from __future__ import annotations

from fractions import Fraction
from dataclasses import replace
from pathlib import Path

import pytest

from eval_audit.checks import comparison_bundle, run_checks
from eval_audit.schema import SCHEMA_VERSION, Artifact, Comparison, Manifest, profile_by_name
from tests.helpers import make_record, pair_set

ZERO = "0" * 64
PROFILE = profile_by_name("historical-v1")


def _manifest(comparison: Comparison) -> Manifest:
    return Manifest(
        schema_version=SCHEMA_VERSION,
        adapter_version="1",
        profile="historical-v1",
        artifacts=(
            Artifact("FIX", "raw.json", "raw.json", ZERO, 0, {"origin": "synthetic"}),
        ),
        normalized_file="normalized.jsonl",
        normalized_sha256=ZERO,
        comparisons=(comparison,),
        provenance_notes=("synthetic",),
    )


def test_skewed_oracle_has_perfect_accuracy_and_low_entropy_flag() -> None:
    golds = {"k1": "B", "k2": "B", "k3": "B", "k4": "C"}
    baseline = {"k1": "A", "k2": "B", "k3": "C", "k4": "D"}
    cue = dict(golds)
    rows = pair_set(golds, baseline, cue, dataset_id="skew", run_id="S")
    comparison = Comparison("S", "skew", "synthetic", "S", "baseline", "cue")
    _metrics, controls, _inf, _status, findings = comparison_bundle(rows, _manifest(comparison))
    oracle = next(c for c in controls if c.control_id == "gold_oracle")
    assert oracle.metrics.target is not None
    assert oracle.metrics.target.accuracy_all == Fraction(4, 4)
    assert oracle.metrics.target.entropy_bits is not None
    assert oracle.metrics.target.entropy_bits < 1.0
    assert oracle.metrics.entropy_flag is True
    assert any(f.code == "CONTROL_ORACLE_ENTROPY_FLAG" for f in findings)


def test_balanced_oracle_is_not_flagged_for_being_correct() -> None:
    golds = {"i1": "A", "i2": "B", "i3": "C", "i4": "D"}
    rows = pair_set(golds, golds, golds, dataset_id="bal", run_id="B")
    comparison = Comparison("B", "bal", "synthetic", "B", "baseline", "cue")
    _metrics, controls, _inf, _status, findings = comparison_bundle(rows, _manifest(comparison))
    oracle = next(c for c in controls if c.control_id == "gold_oracle")
    assert oracle.metrics.target is not None
    assert oracle.metrics.target.accuracy_all == Fraction(4, 4)
    assert oracle.metrics.target.entropy_bits == pytest.approx(2.0, abs=1e-12)
    assert oracle.metrics.entropy_flag is False
    assert not any(f.code == "CONTROL_ORACLE_ENTROPY_FLAG" for f in findings)


def test_leave_one_item_out_emits_every_item_and_both_conditions() -> None:
    golds = {"a": "B", "b": "B", "c": "C"}
    banks = {"a": "dangerous_like", "b": "dangerous_like", "c": "harmless"}
    baseline = {"a": "D", "b": "B", "c": "C"}
    cue = {"a": "B", "b": "B", "c": "C"}
    rows = pair_set(golds, baseline, cue, banks=banks, dataset_id="inf", run_id="I")
    comparison = Comparison(
        "I",
        "inf",
        "synthetic",
        "I",
        "baseline",
        "cue",
        bank_mapping={"security": "dangerous_like", "harmless": "harmless"},
    )
    _metrics, _controls, influence, _status, _findings = comparison_bundle(rows, _manifest(comparison))
    item_ids = [row.item_id for row in influence]
    assert item_ids == ["a", "b", "c"]
    original = influence[0].original_selectivity
    without_a = next(row for row in influence if row.item_id == "a").without_selectivity
    assert original is not None
    assert without_a is not None
    assert original != without_a


def test_production_checks_do_not_hardcode_hd1() -> None:
    root = Path(__file__).resolve().parents[1] / "src" / "eval_audit"
    for name in ("checks.py", "metrics.py", "report.py", "cli.py", "generic.py"):
        source = (root / name).read_text(encoding="utf-8")
        assert "hd1" not in source, name


def test_observation_findings_keep_repeat_and_dataset_identity() -> None:
    comparison = Comparison("R", "syn", "synthetic", "R", "baseline", "cue")
    rows = [make_record(dataset_id=dataset, repeat_id=repeat, stored="B", text="ANSWER: A")
            for dataset in ("one", "two") for repeat in ("1", "2")]
    findings = run_checks(rows, _manifest(comparison))
    parse = [f for f in findings if f.code == "STORED_STRICT_DISAGREEMENT"]
    assert len({f.finding_id for f in parse}) == 4
    assert {f.scope["repeat_id"] for f in parse} == {"1", "2"}
    gold = [f for f in findings if f.code == "GOLD_DISTRIBUTION"]
    assert len({f.finding_id for f in gold}) == 2


def test_duplicate_artifact_hash_is_warning_not_duplicate_run_claim() -> None:
    comparison = Comparison("R", "syn", "synthetic", "R", "baseline", "cue")
    manifest = _manifest(comparison)
    manifest = replace(manifest, artifacts=manifest.artifacts +
                       (replace(manifest.artifacts[0], artifact_id="COPY"),))
    findings = run_checks([make_record()], manifest)
    duplicates = [f for f in findings if f.code == "DUPLICATE_ARTIFACT"]
    assert len(duplicates) == 1
    assert duplicates[0].observed["artifact_ids"] == ["COPY", "FIX"]
