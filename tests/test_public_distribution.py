"""Synthetic CLI behavior and the explicit public-distribution boundary."""
import json
from pathlib import Path
import shutil
import sys
import tomllib

import pytest
from eval_audit.cli import main

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from release_support import release_files


def test_public_selection_excludes_research_and_injected_file(tmp_path):
    selected = release_files(ROOT, "public")
    for p in selected:
        dest = tmp_path / p.relative_to(ROOT)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(p, dest)
    secret = tmp_path / "examples/external-eval/bundle.json"
    secret.parent.mkdir(parents=True)
    secret.write_text('{"private_record": true}')
    result = {p.relative_to(tmp_path).as_posix() for p in release_files(tmp_path, "public")}
    assert "examples/external-eval/bundle.json" not in result
    assert "examples/transfer-fixture/bundle.json" in result
    assert not any(p.startswith(("data/", "audit/", ".archive/")) for p in result)


def test_public_selection_fails_when_required_file_missing(tmp_path):
    with pytest.raises(FileNotFoundError, match="Required public file"):
        release_files(tmp_path, "public")


def test_public_metadata_is_core_only():
    config = tomllib.loads((ROOT / "pyproject.toml").read_text())
    assert config["project"]["dependencies"] == []
    assert config["project"]["readme"] == "docs/PACKAGE-README.md"
    for license_file in config["project"]["license-files"]:
        assert (ROOT / license_file).is_file()


def test_public_demo_and_scoped_report(tmp_path):
    assert main(["demo", "--out", str(tmp_path / "demo")]) == 0
    report = json.loads((tmp_path / "demo/report.json").read_text())
    assert report["audit_status"] == "complete"
    assert report["gates"]
    assert all(c["gates"]["G4"]["status"] == "NOT_ESTABLISHED" for c in report["gates"])


def test_public_docs_links_resolve():
    import re
    for name in ("PACKAGE-README.md", "PUBLIC-RELEASE.md"):
        path = ROOT / "docs" / name
        for target in re.findall(r"\]\(([^)]+)\)", path.read_text()):
            if "://" not in target:
                assert (path.parent / target).exists(), target
