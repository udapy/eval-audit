from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from eval_audit.cli import cmd_audit
from eval_audit.generic import load_generic
from eval_audit.service import AuditService, ServiceError

FIXTURE = Path(__file__).resolve().parents[1] / "examples/transfer-fixture/bundle.json"


@pytest.fixture
def setup(tmp_path):
    source = tmp_path / "bundle.json"
    source.write_bytes(FIXTURE.read_bytes())
    return AuditService(tmp_path, "output"), source


def error_code(code, function, *args, **kwargs):
    with pytest.raises(ServiceError) as caught:
        function(*args, **kwargs)
    assert caught.value.code == code


def test_cli_service_agree_and_preserve(setup):
    service, source = setup
    before = source.read_bytes()
    inspected = service.inspect_bundle("bundle.json")
    assert inspected["record_count"] == 32
    assert not (service.output_root / "audits").exists()
    result = service.run_audit("bundle.json")
    assert source.read_bytes() == before
    assert result["model_runs_executed"] == 0
    load_generic(source, source.parent / "cli-data")
    assert cmd_audit(source.parent / "cli-data/manifest.json", source.parent / "cli-report", None) == 0
    cli = json.loads((source.parent / "cli-report/report.json").read_text())
    exported = service.export_report(result["audit_id"], "json")
    actual = json.loads((service.workspace / exported["path"]).read_text())
    for key in ("group_metrics", "comparison_metrics", "item_influence", "gates", "findings"):
        assert actual[key] == cli[key]
    reopened = AuditService(service.workspace, "output")
    assert reopened.export_report(result["audit_id"], "json") == exported


def test_concurrent_and_replay(setup):
    service, source = setup
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: service.run_audit(str(source)), range(2)))
    assert results[0]["audit_id"] != results[1]["audit_id"]
    assert results[0]["same_source_group"] == results[1]["same_source_group"]
    for result in results:
        service.export_report(result["audit_id"])


@pytest.mark.parametrize("path", ["../bundle.json", "/etc/passwd", "absent.json"])
def test_bad_paths(setup, path):
    service, _ = setup
    error_code("NOT_FOUND" if path == "absent.json" else "INVALID_INPUT", service.run_audit, path)
    assert not list(service.output_root.rglob("completion.json"))


def test_symlinks(setup):
    service, source = setup
    link = source.parent / "linked.json"
    link.symlink_to(source)
    error_code("INVALID_INPUT", service.inspect_bundle, str(link))
    directory = source.parent / "linked-directory"
    directory.symlink_to(source.parent, target_is_directory=True)
    error_code("INVALID_INPUT", service.run_audit, str(directory / "bundle.json"))


@pytest.mark.parametrize("content", ["{", "[]", "PK\u0003\u0004broken", '{"rows": []}'])
def test_malformed(setup, content):
    service, source = setup
    source.write_text(content)
    error_code("INVALID_INPUT", service.run_audit, str(source))
    assert not list(service.output_root.rglob("completion.json"))
    assert list(service.output_root.rglob("failure.json"))


def test_limits_before_parser_and_computation(setup, monkeypatch):
    service, source = setup
    monkeypatch.setattr("eval_audit.service.load_generic", lambda *args: pytest.fail("import should not run"))
    small = AuditService(service.workspace, "small", max_bytes=10)
    error_code("SIZE_LIMIT", small.run_audit, str(source))
    limited = AuditService(service.workspace, "limited", max_records=1)
    error_code("SIZE_LIMIT", limited.run_audit, str(source))


@pytest.mark.parametrize("mutation", ["duplicate", "unknown_comparison", "unpaired"])
def test_invalid_comparison_or_duplicate(setup, mutation):
    service, source = setup
    bundle = json.loads(source.read_text())
    if mutation == "duplicate":
        bundle["rows"].append(bundle["rows"][0])
    elif mutation == "unknown_comparison":
        bundle["comparisons"][0]["dataset_id"] = "unavailable"
    else:
        bundle["rows"].pop()
    source.write_text(json.dumps(bundle))
    error_code("INVALID_INPUT", service.run_audit, str(source))
    assert not list(service.output_root.rglob("completion.json"))


def test_unknown_ids_and_failed_write(setup, monkeypatch):
    service, source = setup
    error_code("NOT_FOUND", service.get_finding, "../x", "x")
    error_code("NOT_FOUND", service.export_report, "0" * 32)
    def fail(*args, **kwargs):
        raise OSError("simulated disk failure")
    monkeypatch.setattr("eval_audit.service.write_report", fail)
    error_code("PROCESSING_FAILURE", service.run_audit, str(source))
    assert not list(service.output_root.rglob("completion.json"))


def test_finding_pagination_raw_and_integrity(setup):
    original, source = setup
    service = AuditService(original.workspace, "paged", page_size=1, max_excerpt_chars=3)
    result = service.run_audit(str(source))
    audit_id = result["audit_id"]
    first = service.findings_page(audit_id)
    assert len(first["findings"]) == 1
    finding_id = first["findings"][0]["finding_id"]
    assert "observed" not in first["findings"][0]
    assert "excerpts" not in service.get_finding(audit_id, finding_id)
    for offset in range(first["total"]):
        f = service.findings_page(audit_id, offset)["findings"][0]
        raw = service.get_finding(audit_id, f["finding_id"], True)
        assert sum(len(e["response_text"] or "") for e in raw["excerpts"]) <= 3
    error_code("NOT_FOUND", service.get_finding, audit_id, "../report.json")
    error_code("INVALID_INPUT", service.findings_page, audit_id, -1)
    exported = service.export_report(audit_id, "json")
    (service.workspace / exported["path"]).write_text("{}")
    error_code("PROCESSING_FAILURE", service.export_report, audit_id, "json")


def test_missing_answers_and_second_dataset_agree(setup):
    service, source = setup
    bundle = json.loads(source.read_text())
    first = bundle["rows"][0]
    first["stored_answer"] = None
    first["response_text"] = None
    first["response_completeness"] = "unknown"
    extra = json.loads(json.dumps(bundle))
    for section in ("rows", "items", "comparisons"):
        for entry in extra[section]:
            entry["dataset_id"] += "-second"
            if "comparison_id" in entry:
                entry["comparison_id"] += "-second"
        bundle[section].extend(extra[section])
    source.write_text(json.dumps(bundle))
    result = service.run_audit(str(source))
    report = json.loads((service.workspace / service.export_report(result["audit_id"], "json")["path"]).read_text())
    load_generic(source, source.parent / "cli-data")
    cmd_audit(source.parent / "cli-data/manifest.json", source.parent / "cli-report", None)
    cli = json.loads((source.parent / "cli-report/report.json").read_text())
    assert report["item_influence"] == cli["item_influence"]
    assert report["group_metrics"] == cli["group_metrics"]
    assert len({m["dataset_id"] for m in report["group_metrics"]}) == 4


@pytest.mark.parametrize("format", ["inspect", "lm-eval"])
def test_paired_adapters_gold_independent(setup, format):
    service, source = setup
    def log(answer):
        if format == "inspect":
            return {"eval": {"model": "synthetic", "task": "demo"}, "samples": [
                {"id": "i1", "target": "A", "input": "Q", "output": {"completion": f"ANSWER: {answer}"}}]}
        return {"config": {"model_name": "synthetic"}, "samples": {"demo": [
            {"doc_id": "i1", "target": 0, "resps": [[f"ANSWER: {answer}"]]}]}}
    source.write_text(json.dumps(log("B")))
    error_code("UNSUPPORTED_LAYOUT", service.run_audit, str(source), format)
    source.write_text(json.dumps({"baseline": log("B"), "target": log("A")}))
    result = service.run_audit(str(source), format)
    report = json.loads((service.workspace / service.export_report(result["audit_id"], "json")["path"]).read_text())
    answers = {r["condition"]: r["stored_answer"] for r in report["records"]}
    assert answers == {"baseline": "B", "target": "A"}
    from eval_audit.cli import cmd_check
    assert cmd_check(source, format_name=format) in (0, 2)
    assert all(r["response_completeness"] == "unknown" for r in report["records"])


def test_unsupported_likelihood_layout(setup):
    service, source = setup
    log = {"config": {"model_name": "synthetic"}, "samples": {"demo": [
        {"doc_id": "i1", "target": 0, "resps": [[-0.1, True]]}]}}
    source.write_text(json.dumps({"baseline": log, "target": log}))
    error_code("UNSUPPORTED_LAYOUT", service.run_audit, str(source), "lm-eval")


def test_annotation_capture_is_in_receipt(setup):
    service, source = setup
    annotation = source.parent / "review.jsonl"
    annotation.write_text("")
    result = service.run_audit(str(source), annotations=str(annotation))
    assert "annotations.jsonl" in result["source_hashes"]
    assert annotation.read_bytes() == b""


def test_bundle_directory_layout(setup):
    service, source = setup
    payload = json.loads(source.read_text())
    directory = source.parent / "jsonl-bundle"
    directory.mkdir()
    (directory / "rows.jsonl").write_text("\n".join(json.dumps(r) for r in payload["rows"]))
    (directory / "comparisons.json").write_text(json.dumps(payload["comparisons"]))
    (directory / "items.jsonl").write_text("\n".join(json.dumps(r) for r in payload["items"]))
    assert service.inspect_bundle(str(directory))["record_count"] == 32
    assert service.run_audit(str(directory))["status"] == "complete"
