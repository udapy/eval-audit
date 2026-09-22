"""Test import and audit of assigned security/math responses."""

from __future__ import annotations

from pathlib import Path
import pytest

from eval_audit.cli import main
from eval_audit.io import load_json, sha256_file
from eval_audit.loaders import read_dataset


def test_assigned_fixture_import_and_audit(tmp_path: Path) -> None:
    bundle_path = Path("examples/external-eval/bundle.json").resolve()
    assert bundle_path.is_file(), "external benchmark bundle must exist"

    data_dir = tmp_path / "data"
    report_dir = tmp_path / "report"

    # Step 1: Import via generic-v1 profile
    ret_import = main(["import", "--source", str(bundle_path), "--out", str(data_dir)])
    assert ret_import == 0

    manifest, records = read_dataset(data_dir / "manifest.json")
    assert manifest.profile == "generic-v1"
    assert len(records) == 40
    assert len(manifest.comparisons) == 2

    # Step 2: Run audit
    ret_audit = main(["audit", "--manifest", str(data_dir / "manifest.json"), "--out", str(report_dir)])
    assert ret_audit == 0

    report_json_path = report_dir / "report.json"
    assert report_json_path.is_file()
    payload = load_json(report_json_path)

    assert payload["audit_status"] == "complete"
    assert payload["manifest"]["profile"] == "generic-v1"

    # Gate G2: Gold-oracle control must not flag on this constructed key distribution
    controls = payload["controls"]
    oracle_controls = [c for c in controls if c["control_id"] == "gold_oracle"]
    assert len(oracle_controls) == 2
    for oracle in oracle_controls:
        assert oracle["metrics"]["entropy_flag"] is False

    # Gate G1: Parse disagreement on cs09 must be detected
    findings = payload["findings"]
    parse_findings = [f for f in findings if f["code"] == "STORED_STRICT_DISAGREEMENT"]
    assert any(f["scope"].get("item_id") == "cs09" for f in parse_findings)
