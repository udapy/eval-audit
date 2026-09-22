"""SDK client coverage for the optional local MCP server."""
from __future__ import annotations

import asyncio
import importlib.metadata
import json
import platform
import shutil
import sys
import tomllib
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from release_support import release_files

FIXTURE = ROOT / "examples/transfer-fixture/bundle.json"
TOOLS = {"inspect_bundle", "run_audit", "get_finding", "export_report"}


def test_metadata_and_public_files():
    config = tomllib.loads((ROOT / "pyproject.toml").read_text())
    assert config["project"]["dependencies"] == []
    assert config["project"]["optional-dependencies"]["mcp"] == ["mcp>=2,<3"]
    assert config["project"]["scripts"]["eval-audit-mcp"] == "eval_audit.mcp_server:main"
    selected = {path.relative_to(ROOT).as_posix() for path in release_files(ROOT, "public")}
    for name in (
        "src/eval_audit/mcp_server.py",
        "tests/test_mcp_server.py",
        "docs/MCP.md",
        "docs/mcp-reproducibility.json",
        "examples/mcp/README.md",
    ):
        assert name in selected
    assert "data/" not in {name.split("/")[0] + "/" for name in selected if name.startswith("data/")}


def test_core_import_does_not_load_mcp():
    script = "import eval_audit, eval_audit.cli, eval_audit.service, eval_audit.mcp_server, sys; assert 'mcp' not in sys.modules"
    completed = __import__("subprocess").run([sys.executable, "-c", script], cwd=ROOT, capture_output=True, text=True)
    assert completed.returncode == 0, completed.stderr


def test_pin_matches_installed_mcp():
    pytest.importorskip("mcp")
    record = json.loads((ROOT / "docs/mcp-reproducibility.json").read_text())
    assert record["constraint"] == "mcp>=2,<3"
    assert importlib.metadata.version("mcp") == record["distributions"]["mcp"]
    if (platform.python_version(), sys.platform, platform.machine()) == (record["python"], record["os"], record["machine"]):
        for name, version in record["distributions"].items():
            assert importlib.metadata.version(name) == version


def test_startup_errors_use_stderr(tmp_path, capsys):
    pytest.importorskip("mcp")
    from eval_audit.mcp_server import main
    with pytest.raises(SystemExit) as usage:
        main([])
    assert usage.value.code == 2
    assert capsys.readouterr().out == ""
    with pytest.raises(SystemExit) as missing:
        main(["--workspace", str(tmp_path / "absent"), "--output-root", "audit-output"])
    assert missing.value.code == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "INVALID_INPUT" in captured.err


def test_stdio_protocol_audit_restart_and_malformed_arguments(tmp_path):
    pytest.importorskip("mcp")
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    shutil.copy(FIXTURE, workspace / "bundle.json")
    asyncio.run(_protocol(workspace))


def test_output_root_is_closed(tmp_path):
    pytest.importorskip("mcp")
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    shutil.copy(FIXTURE, workspace / "bundle.json")
    asyncio.run(_isolation(workspace))


def _text(result) -> str:
    return "\n".join(getattr(block, "text", "") for block in result.content)


def _has_key(value, key: str) -> bool:
    if isinstance(value, dict):
        return key in value or any(_has_key(item, key) for item in value.values())
    if isinstance(value, list):
        return any(_has_key(item, key) for item in value)
    return False


def _params(workspace: Path):
    from mcp import StdioServerParameters
    return StdioServerParameters(
        command=sys.executable,
        args=["-m", "eval_audit.mcp_server", "--workspace", str(workspace), "--output-root", "audit-output"],
        cwd=str(workspace),
    )


async def _connect(workspace: Path):
    from mcp import Client
    from mcp.client.stdio import stdio_client
    return Client(stdio_client(_params(workspace)))


async def _protocol(workspace: Path):
    from eval_audit.service import AuditService
    async with await _connect(workspace) as client:
        listed = await client.list_tools()
        by_name = {tool.name: tool for tool in listed.tools}
        assert set(by_name) == TOOLS
        for name in ("inspect_bundle", "get_finding", "export_report"):
            assert by_name[name].annotations.read_only_hint is True
            assert by_name[name].annotations.open_world_hint is False
            assert "shell command" in by_name[name].description
        audit_tool = by_name["run_audit"]
        assert audit_tool.annotations.read_only_hint is False
        assert audit_tool.annotations.destructive_hint is False
        assert audit_tool.annotations.idempotent_hint is False
        assert audit_tool.annotations.open_world_hint is False
        templates = await client.list_resource_templates()
        uris = {item.uri_template for item in templates.resource_templates}
        assert uris == {
            "audit://{audit_id}/report/markdown",
            "audit://{audit_id}/report/json",
        }

        inspected = await client.call_tool("inspect_bundle", {"source": "bundle.json"})
        assert inspected.is_error is False
        assert inspected.structured_content["record_count"] == 32
        assert "audit_id" not in inspected.structured_content
        assert not list((workspace / "audit-output").rglob("completion.json"))

        audited = await client.call_tool("run_audit", {"source": "bundle.json"})
        assert audited.is_error is False
        payload = audited.structured_content
        assert payload["model_runs_executed"] == 0
        assert payload["status"] == "complete"
        assert _has_key(payload, "response_text") is False
        assert str(workspace) not in json.dumps(payload)
        direct = AuditService(workspace, "service-output").run_audit("bundle.json")
        assert payload["finding_count"] == direct["finding_count"]
        assert payload["gates"] == direct["gates"]
        assert payload["group_metrics"] == direct["group_metrics"]
        assert payload["same_source_group"] == direct["same_source_group"]
        audit_id = payload["audit_id"]
        finding_id = payload["findings"][0]["finding_id"]

        finding = await client.call_tool("get_finding", {"audit_id": audit_id, "finding_id": finding_id})
        assert finding.is_error is False
        assert _has_key(finding.structured_content, "response_text") is False
        raw = await client.call_tool(
            "get_finding", {"audit_id": audit_id, "finding_id": finding_id, "include_raw": True})
        assert raw.is_error is False
        assert "excerpts" in raw.structured_content

        exported = await client.call_tool("export_report", {"audit_id": audit_id, "format": "markdown"})
        assert exported.is_error is False
        reference = exported.structured_content
        assert reference["uri"] == f"audit://{audit_id}/report/markdown"
        report_path = workspace / reference["path"]
        markdown = await client.read_resource(reference["uri"])
        assert markdown.contents[0].text == report_path.read_text(encoding="utf-8")
        json_report = await client.read_resource(f"audit://{audit_id}/report/json")
        assert json.loads(json_report.contents[0].text)["audit_status"] == "complete"

        malformed = await client.call_tool("inspect_bundle", {"source": "bundle.json", "format": "zip"})
        assert malformed.is_error is True
        assert "zip" in _text(malformed).lower() or "literal" in _text(malformed).lower()
        traversal = await client.call_tool("run_audit", {"source": "../bundle.json"})
        assert traversal.is_error is True
        assert "INVALID_INPUT" in _text(traversal)
        unknown = await client.call_tool("get_finding", {"audit_id": "0" * 32, "finding_id": "missing"})
        assert unknown.is_error is True
        assert "NOT_FOUND" in _text(unknown)

    async with await _connect(workspace) as restarted:
        again = await restarted.call_tool("export_report", {"audit_id": audit_id, "format": "json"})
        assert again.is_error is False
        assert again.structured_content["uri"] == f"audit://{audit_id}/report/json"
        reread = await restarted.read_resource(f"audit://{audit_id}/report/markdown")
        assert reread.contents[0].text == report_path.read_text(encoding="utf-8")
        from mcp import MCPError
        with pytest.raises(MCPError):
            await restarted.read_resource("audit://" + ("ab" * 16) + "/report/markdown")


async def _isolation(workspace: Path):
    from mcp import Client
    async with await _connect(workspace) as client:
        audited = await client.call_tool("run_audit", {"source": "bundle.json"})
        audit_id = audited.structured_content["audit_id"]
    from eval_audit.mcp_server import build_server
    other = build_server(str(workspace), "other-output")
    async with Client(other) as client:
        hidden = await client.call_tool("export_report", {"audit_id": audit_id})
        assert hidden.is_error is True
        assert "NOT_FOUND" in _text(hidden)
