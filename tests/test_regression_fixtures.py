"""Constructed regression cases for measurement and ingestion faults."""

from __future__ import annotations

from fractions import Fraction
from pathlib import Path

import pytest

from eval_audit.checks import comparison_bundle
from eval_audit.cli import main
from eval_audit.io import dump_json, dump_jsonl, sha256_file
from eval_audit.loaders import manifest_to_dict, record_to_dict
from eval_audit.schema import (
    SCHEMA_VERSION,
    Artifact,
    AuditInputError,
    Comparison,
    Manifest,
    PairingError,
    SourceRef,
    validate_records,
)
from tests.helpers import make_record, pair_set

ZERO = "c" * 64


def _manifest(comparison: Comparison, sha: str = ZERO) -> Manifest:
    return Manifest(
        schema_version=SCHEMA_VERSION,
        adapter_version="1",
        profile="historical-v1",
        artifacts=(Artifact("U", "raw.jsonl", "raw.jsonl", sha, 1, {"origin": "unseen"}),),
        normalized_file="normalized.jsonl",
        normalized_sha256=sha,
        comparisons=(comparison,),
        provenance_notes=("unseen fixture",),
    )


def test_unseen_clean_balanced_has_no_entropy_flag() -> None:
    golds = {"u1": "A", "u2": "B", "u3": "C", "u4": "D"}
    rows = pair_set(golds, golds, golds, dataset_id="unseen-clean", run_id="U1")
    comparison = Comparison("U1", "unseen-clean", "synthetic", "U1", "baseline", "cue")
    metrics, controls, influence, status, findings = comparison_bundle(rows, _manifest(comparison))
    stored = next(m for m in metrics if m.answer_basis == "stored")
    assert stored.entropy_flag is False
    assert stored.accuracy_flag is False
    oracle = next(c for c in controls if c.control_id == "gold_oracle")
    assert oracle.metrics.entropy_flag is False
    assert status["U1"] == "complete"
    assert {row.item_id for row in influence} == {"u1", "u2", "u3", "u4"}
    assert not any(f.code == "CONTROL_ORACLE_ENTROPY_FLAG" for f in findings)


def test_unseen_skewed_oracle_flags() -> None:
    golds = {"s1": "B", "s2": "B", "s3": "B", "s4": "C"}
    baseline = {"s1": "A", "s2": "B", "s3": "C", "s4": "D"}
    rows = pair_set(golds, baseline, golds, dataset_id="unseen-skew", run_id="U2")
    comparison = Comparison("U2", "unseen-skew", "synthetic", "U2", "baseline", "cue")
    _metrics, controls, _inf, _status, findings = comparison_bundle(rows, _manifest(comparison))
    oracle = next(c for c in controls if c.control_id == "gold_oracle")
    assert oracle.metrics.target is not None
    assert oracle.metrics.target.accuracy_all == Fraction(1, 1)
    assert oracle.metrics.entropy_flag is True
    assert any(f.code == "CONTROL_ORACLE_ENTROPY_FLAG" for f in findings)


def test_unseen_missing_pairs_exit_2(tmp_path: Path) -> None:
    golds = {"p1": "A", "p2": "B"}
    rows = pair_set(golds, golds, golds, dataset_id="unseen-miss", run_id="U3")
    rows = [row for row in rows if not (row.condition == "cue" and row.item_id == "p2")]
    comparison = Comparison("U3", "unseen-miss", "synthetic", "U3", "baseline", "cue")
    from eval_audit.metrics import pair_rows

    with pytest.raises(PairingError):
        pair_rows(rows, comparison)
    data = tmp_path / "data"
    data.mkdir()
    raw_file = data / "raw.json"
    raw_file.write_text("raw", encoding="utf-8")
    raw_sha = sha256_file(raw_file)
    from dataclasses import replace
    rows = [replace(row, source=SourceRef("U", raw_sha, row.source.json_pointer)) for row in rows]
    payload = [record_to_dict(row) for row in rows]
    dump_jsonl(data / "normalized.jsonl", payload)
    manifest = Manifest(
        schema_version=SCHEMA_VERSION,
        adapter_version="1",
        profile="historical-v1",
        artifacts=(
            Artifact(
                "U",
                "raw.json",
                "raw.json",
                raw_sha,
                len(rows),
                {"origin": "unseen"},
            ),
        ),
        normalized_file="normalized.jsonl",
        normalized_sha256=sha256_file(data / "normalized.jsonl"),
        comparisons=(comparison,),
        provenance_notes=("unseen missing pair",),
    )
    dump_json(data / "manifest.json", manifest_to_dict(manifest))
    assert main(["audit", "--manifest", str(data / "manifest.json"), "--out", str(tmp_path / "out")]) == 2
    status = (tmp_path / "out" / "STATUS.txt").read_text(encoding="utf-8")
    assert "INCOMPLETE" in status


def test_unseen_duplicate_identity() -> None:
    row = make_record(dataset_id="unseen-dup", item_id="d1")
    with pytest.raises(AuditInputError, match="duplicate"):
        validate_records([row, row])


def test_unseen_invalid_parse_is_separate_from_stored() -> None:
    row = make_record(
        dataset_id="unseen-parse",
        item_id="z1",
        stored="B",
        text="I think the answer is B without a marker",
        stored_correct=True,
        gold="B",
    )
    assert row.stored_answer == "B"
    assert row.parse_status == "missing"
    assert row.parsed_answer is None


def test_unseen_changed_hash(tmp_path: Path) -> None:
    golds = {"h1": "A"}
    rows = pair_set(golds, golds, golds, dataset_id="unseen-hash", run_id="U6")
    data = tmp_path / "data"
    data.mkdir()
    dump_jsonl(data / "normalized.jsonl", [record_to_dict(r) for r in rows])
    dump_jsonl(data / "raw.jsonl", [record_to_dict(r) for r in rows])
    comparison = Comparison("U6", "unseen-hash", "synthetic", "U6", "baseline", "cue")
    manifest = Manifest(
        schema_version=SCHEMA_VERSION,
        adapter_version="1",
        profile="historical-v1",
        artifacts=(
            Artifact("U", "raw.jsonl", "raw.jsonl", sha256_file(data / "raw.jsonl"), 2, {"origin": "unseen"}),
        ),
        normalized_file="normalized.jsonl",
        normalized_sha256=sha256_file(data / "normalized.jsonl"),
        comparisons=(comparison,),
        provenance_notes=("unseen hash",),
    )
    dump_json(data / "manifest.json", manifest_to_dict(manifest))
    (data / "normalized.jsonl").write_text(
        (data / "normalized.jsonl").read_text(encoding="utf-8") + " ",
        encoding="utf-8",
    )
    assert main(["audit", "--manifest", str(data / "manifest.json"), "--out", str(tmp_path / "out")]) == 2


def test_unseen_annotation_does_not_mutate_scores(tmp_path: Path) -> None:
    """Regression case: annotations are non-scoring. Same-session fixture, not held-out."""
    golds = {"u1": "A", "u2": "B", "u3": "C", "u4": "D"}
    rows = pair_set(golds, golds, golds, dataset_id="unseen-ann", run_id="U7")
    data = tmp_path / "data"
    data.mkdir()
    raw_file = data / "raw.json"
    raw_file.write_text("raw", encoding="utf-8")
    raw_sha = sha256_file(raw_file)
    from dataclasses import replace
    rows = [replace(r, source=SourceRef("U", raw_sha, r.source.json_pointer)) for r in rows]
    dump_jsonl(data / "normalized.jsonl", [record_to_dict(r) for r in rows])
    comparison = Comparison("U7", "unseen-ann", "synthetic", "U7", "baseline", "cue")
    manifest = Manifest(
        schema_version=SCHEMA_VERSION,
        adapter_version="1",
        profile="historical-v1",
        artifacts=(
            Artifact("U", "raw.json", "raw.json", raw_sha, 8, {"origin": "unseen"}),
        ),
        normalized_file="normalized.jsonl",
        normalized_sha256=sha256_file(data / "normalized.jsonl"),
        comparisons=(comparison,),
        provenance_notes=("unseen annotation non-mutation",),
    )
    dump_json(data / "manifest.json", manifest_to_dict(manifest))
    ann = tmp_path / "ann.jsonl"
    dump_jsonl(
        ann,
        [
            {
                "annotation_id": "u-u1",
                "dataset_id": "unseen-ann",
                "item_id": "u1",
                "text": "rationale: unique-correct on a balanced fixture",
                "author": "fixture-author",
                "status": "proposed",
                "origin": "human",
                "gold_uniqueness": "unique-correct",
                "source_references": ["unseen"],
            }
        ],
    )
    clean = tmp_path / "clean"
    annotated = tmp_path / "ann-out"
    assert main(["audit", "--manifest", str(data / "manifest.json"), "--out", str(clean)]) == 0
    assert (
        main(
            [
                "audit",
                "--manifest",
                str(data / "manifest.json"),
                "--out",
                str(annotated),
                "--annotations",
                str(ann),
            ]
        )
        == 0
    )
    import json

    clean_js = json.loads((clean / "report.json").read_text(encoding="utf-8"))
    ann_js = json.loads((annotated / "report.json").read_text(encoding="utf-8"))
    assert clean_js["group_metrics"] == ann_js["group_metrics"]
    assert clean_js["comparison_metrics"] == ann_js["comparison_metrics"]
    for rec in clean_js["records"]:
        match = next(
            r for r in ann_js["records"] if r["item_id"] == rec["item_id"] and r["condition"] == rec["condition"]
        )
        assert rec["gold"] == match["gold"]
        assert rec["stored_answer"] == match["stored_answer"]
        assert rec["parsed_answer"] == match["parsed_answer"]
    assert any(f["code"] == "MISSING_ANNOTATIONS" for f in clean_js["findings"])
    assert any(f["code"] == "HUMAN_ANNOTATION" for f in ann_js["findings"])
