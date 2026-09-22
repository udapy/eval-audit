"""Generic import + transfer fixture. Production path must not need hd1."""

from __future__ import annotations

import json
from fractions import Fraction
from pathlib import Path

import pytest

from eval_audit.cli import main
from eval_audit.generic import load_generic
from eval_audit.loaders import read_dataset
from eval_audit.schema import AuditInputError, profile_by_name

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "examples" / "transfer-fixture" / "bundle.json"
SRC = ROOT / "src" / "eval_audit"
FIXTURE_SHA256 = "792616e543c76cae2f67b8c5f6c4059d32c77092013b9ed27589edec0bcc06c4"


def test_generic_source_files_do_not_mention_hd1() -> None:
    from hashlib import sha256

    assert sha256(FIXTURE.read_bytes()).hexdigest() == FIXTURE_SHA256
    for name in ("generic.py", "cli.py", "checks.py", "metrics.py"):
        text = (SRC / name).read_text(encoding="utf-8")
        assert "hd1" not in text, name
    bundle = FIXTURE.read_text(encoding="utf-8")
    assert "hd1" not in bundle
    assert "historical-h2" not in bundle


def test_generic_profile_does_not_require_historical_name() -> None:
    profile = profile_by_name("generic-v1")
    assert profile.name == "generic-v1"
    with pytest.raises(AuditInputError, match="unknown profile"):
        profile_by_name("hd1-v1")


def test_import_transfer_fixture(tmp_path: Path) -> None:
    dest = tmp_path / "data"
    manifest = load_generic(FIXTURE, dest)
    assert manifest.profile == "generic-v1"
    _, records = read_dataset(dest / "manifest.json")
    assert len(records) == 32
    assert {r.dataset_id for r in records} == {"xfer-balanced", "xfer-mild-skew"}
    assert {r.item_id for r in records if r.dataset_id == "xfer-balanced"} == {
        "xb01",
        "xb02",
        "xb03",
        "xb04",
        "xb05",
        "xb06",
        "xb07",
        "xb08",
    }
    assert all(r.item_id != "hd1" for r in records)
    golds_before = {(r.dataset_id, r.item_id, r.condition): r.gold for r in records}
    # Re-read: golds unchanged
    _, again = read_dataset(dest / "manifest.json")
    golds_after = {(r.dataset_id, r.item_id, r.condition): r.gold for r in again}
    assert golds_before == golds_after


def test_transfer_fixture_oracle_and_influence(tmp_path: Path) -> None:
    dest = tmp_path / "data"
    load_generic(FIXTURE, dest)
    report_dir = tmp_path / "report"
    assert main(["audit", "--manifest", str(dest / "manifest.json"), "--out", str(report_dir)]) == 0
    payload = json.loads((report_dir / "report.json").read_text(encoding="utf-8"))
    assert payload["manifest"]["profile"] == "generic-v1"
    assert "hd1" not in json.dumps(payload)

    from eval_audit.checks import comparison_bundle, run_checks
    from eval_audit.loaders import read_dataset, read_item_context

    manifest, records = read_dataset(dest / "manifest.json")
    item_context = read_item_context(manifest, dest)
    metrics, controls, influence, status, _pair_findings = comparison_bundle(records, manifest)
    findings = run_checks(records, manifest, item_context=item_context)
    assert status["XFER-BAL"] == "complete"
    assert status["XFER-SKEW"] == "complete"

    bal_stored = next(m for m in metrics if m.comparison_id == "XFER-BAL" and m.answer_basis == "stored")
    assert bal_stored.baseline is not None and bal_stored.target is not None
    assert bal_stored.baseline.accuracy_all == Fraction(6, 8)
    assert bal_stored.target.accuracy_all == Fraction(8, 8)
    assert bal_stored.entropy_flag is False

    bal_oracle = next(c for c in controls if c.comparison_id == "XFER-BAL" and c.control_id == "gold_oracle")
    assert bal_oracle.metrics.target is not None
    assert bal_oracle.metrics.target.accuracy_all == Fraction(8, 8)
    assert bal_oracle.metrics.entropy_flag is False

    skew_oracle = next(c for c in controls if c.comparison_id == "XFER-SKEW" and c.control_id == "gold_oracle")
    assert skew_oracle.metrics.target is not None
    assert skew_oracle.metrics.target.accuracy_all == Fraction(8, 8)
    assert skew_oracle.metrics.entropy_flag is True

    skew_stored = next(m for m in metrics if m.comparison_id == "XFER-SKEW" and m.answer_basis == "stored")
    assert skew_stored.baseline is not None and skew_stored.target is not None
    assert skew_stored.baseline.accuracy_all == Fraction(4, 8)
    assert skew_stored.target.accuracy_all == Fraction(7, 8)
    assert skew_stored.entropy_flag is True

    bal_changed = []
    for rec_b in records:
        if rec_b.run_id != "X1" or rec_b.condition != "baseline":
            continue
        rec_t = next(
            r
            for r in records
            if r.run_id == "X1" and r.condition == "cue" and r.item_id == rec_b.item_id
        )
        if rec_b.stored_answer != rec_t.stored_answer:
            bal_changed.append(rec_b.item_id)
    assert sorted(bal_changed) == ["xb03", "xb06"]

    skew_changed = []
    for rec_b in records:
        if rec_b.run_id != "X2" or rec_b.condition != "baseline":
            continue
        rec_t = next(
            r
            for r in records
            if r.run_id == "X2" and r.condition == "cue" and r.item_id == rec_b.item_id
        )
        if rec_b.stored_answer != rec_t.stored_answer:
            skew_changed.append(rec_b.item_id)
    assert sorted(skew_changed) == ["xs02", "xs03", "xs04"]
    assert len({row.item_id for row in influence if row.comparison_id == "XFER-BAL"}) == 8
    assert any(f.code == "STORED_STRICT_DISAGREEMENT" for f in findings)


def test_jsonl_directory_import(tmp_path: Path) -> None:
    src = tmp_path / "src"
    src.mkdir()
    rows = [
        {
            "dataset_id": "jsonl-bank",
            "model_label": "fixture-synthetic",
            "run_id": "J1",
            "condition": "baseline",
            "item_id": "j1",
            "gold": "A",
            "stored_answer": "B",
            "response_text": "ANSWER: B",
        },
        {
            "dataset_id": "jsonl-bank",
            "model_label": "fixture-synthetic",
            "run_id": "J1",
            "condition": "cue",
            "item_id": "j1",
            "gold": "A",
            "stored_answer": "A",
            "response_text": "ANSWER: A",
        },
    ]
    (src / "rows.jsonl").write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    (src / "comparisons.json").write_text(
        json.dumps(
            [
                {
                    "comparison_id": "J",
                    "dataset_id": "jsonl-bank",
                    "model_label": "fixture-synthetic",
                    "run_id": "J1",
                    "baseline_condition": "baseline",
                    "target_condition": "cue",
                }
            ]
        ),
        encoding="utf-8",
    )
    dest = tmp_path / "out"
    manifest = load_generic(src, dest)
    assert manifest.profile == "generic-v1"
    _, records = read_dataset(dest / "manifest.json")
    assert len(records) == 2
    assert {r.gold for r in records} == {"A"}


def test_missing_comparisons_exit_2(tmp_path: Path) -> None:
    src = tmp_path / "bad.json"
    src.write_text(json.dumps({"rows": [{"item_id": "x", "gold": "A"}]}), encoding="utf-8")
    assert main(["import", "--source", str(src), "--out", str(tmp_path / "o")]) == 2


def test_cli_import_and_audit_fixture(tmp_path: Path) -> None:
    data = tmp_path / "data"
    report = tmp_path / "report"
    assert main(["import", "--source", str(FIXTURE), "--out", str(data)]) == 0
    assert main(["audit", "--manifest", str(data / "manifest.json"), "--out", str(report)]) == 0
    text = (report / "report.md").read_text(encoding="utf-8")
    assert "generic-v1" in text
    assert "hd1" not in text
