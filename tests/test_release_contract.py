"""Release regressions: scoped diagnostics and evidence-preserving interfaces."""
import json
from pathlib import Path

import pytest

from eval_audit.cli import main
from eval_audit.generic import load_generic
from eval_audit.schema import AuditInputError
from eval_audit.triage import write_triage_queue

ROOT = Path(__file__).resolve().parents[1]


def test_scorecard_reports_scoped_diagnostics_without_claim_validation(capsys):
    assert main(["check", str(ROOT / "examples/arc-challenge/bundle.json")]) == 0
    output = capsys.readouterr().out
    assert "ORACLE_NOT_DEGENERATE" in output
    assert "PARSER_SENSITIVE" in output
    assert "G4: NOT_ESTABLISHED" in output
    assert "CLAIM VALID" not in output


def test_report_serializes_oracle_and_target_as_different_quantities(tmp_path):
    load_generic(ROOT / "examples/arc-challenge/bundle.json", tmp_path / "data")
    assert main(["audit", "--manifest", str(tmp_path / "data/manifest.json"), "--out", str(tmp_path / "report")]) == 0
    report = json.loads((tmp_path / "report/report.json").read_text())
    oracle = report["gates"][0]["gates"]["G2"]
    assert oracle["status"] == "CLEAR"
    assert oracle["oracle_entropy_drop"] == pytest.approx(0.03672078720986738)
    target = next(m for m in report["comparison_metrics"] if m["answer_basis"] == "stored")
    assert target["entropy_drop"] == pytest.approx(0.15947907481575374)


def test_triage_refuses_to_overwrite_existing_evidence(tmp_path):
    out = tmp_path / "review.jsonl"
    out.write_bytes(b"existing human review\n")
    with pytest.raises(AuditInputError, match="exists"):
        write_triage_queue(tmp_path / "unused-manifest.json", out)
    assert out.read_bytes() == b"existing human review\n"


def test_triage_keeps_second_dataset_influence(tmp_path):
    source = ROOT / "examples/external-eval/bundle.json"
    load_generic(source, tmp_path / "data")
    out = tmp_path / "review.jsonl"
    write_triage_queue(tmp_path / "data/manifest.json", out)
    rows = [json.loads(line) for line in out.read_text().splitlines()]
    # Math corrections must not be incorrectly scoped to the security dataset.
    assert any(row.get("item_id") == "em01" for row in rows), rows
