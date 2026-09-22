from __future__ import annotations

import json
from pathlib import Path

import pytest

from eval_audit.checks import run_checks
from eval_audit.cli import main
from eval_audit.demo import write_demo_dataset
from eval_audit.loaders import load_annotation_file, read_dataset, read_item_context
from eval_audit.report import build_report
from eval_audit.schema import AuditInputError
from tests.helpers import make_annotation, pair_set

EXAMPLES = Path(__file__).resolve().parents[1] / "examples" / "annotations-hd1-proposed.jsonl"
REVIEWED = Path(__file__).resolve().parents[1] / "examples" / "annotations-hd1-reviewed.jsonl"
ZERO = "0" * 64


def _score_fingerprint(report) -> object:
    groups = [
        (
            m.dataset_id,
            m.model_label,
            m.run_id,
            m.condition,
            m.answer_basis,
            m.n_correct,
            m.n_total,
            m.n_valid,
            m.entropy_bits,
            tuple(sorted(m.prediction_counts.items())),
        )
        for m in report.group_metrics
    ]
    comparisons = [
        (
            c.comparison_id,
            c.answer_basis,
            c.status,
            str(c.accuracy_drop),
            c.entropy_drop,
            str(c.selectivity),
            c.accuracy_flag,
            c.entropy_flag,
        )
        for c in report.comparison_metrics
    ]
    return groups, comparisons


def test_item_scoped_annotation_requires_verdict_and_rationale() -> None:
    with pytest.raises(AuditInputError, match="gold_uniqueness"):
        make_annotation(gold_uniqueness=None).validate()
    with pytest.raises(AuditInputError, match="nonempty"):
        make_annotation(text="   ").validate()
    with pytest.raises(AuditInputError, match="unknown gold_uniqueness"):
        make_annotation(gold_uniqueness="maybe").validate()
    with pytest.raises(AuditInputError, match="unknown annotation origin"):
        make_annotation(origin="model").validate()
    with pytest.raises(AuditInputError, match="unknown annotation status"):
        make_annotation(status="draft").validate()


def test_dataset_level_note_may_omit_verdict() -> None:
    make_annotation(item_id=None, gold_uniqueness=None).validate()


def test_malformed_annotation_json_fails_usefully(tmp_path: Path) -> None:
    path = tmp_path / "bad.jsonl"
    path.write_text("{not json\n", encoding="utf-8")
    with pytest.raises(AuditInputError, match="malformed annotation JSON"):
        load_annotation_file(path)


def test_malformed_annotation_missing_origin_fails_usefully(tmp_path: Path) -> None:
    path = tmp_path / "bad.jsonl"
    path.write_text(
        json.dumps(
            {
                "annotation_id": "x",
                "dataset_id": "syn",
                "item_id": "i1",
                "text": "rationale",
                "author": "a",
                "status": "proposed",
                "gold_uniqueness": "contested",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    with pytest.raises(AuditInputError, match="origin"):
        load_annotation_file(path)


def test_missing_annotation_is_warning_not_score_change(tmp_path: Path) -> None:
    data = tmp_path / "data"
    write_demo_dataset(data)
    manifest, records = read_dataset(data / "manifest.json")
    context = read_item_context(manifest, data)
    golds = [row.gold for row in records]
    stored = [row.stored_answer for row in records]
    parsed = [row.parsed_answer for row in records]
    report = build_report(records, manifest, item_context=context, annotations=())
    assert [row.gold for row in report.records] == golds
    assert [row.stored_answer for row in report.records] == stored
    assert [row.parsed_answer for row in report.records] == parsed
    missing = [f for f in report.findings if f.code == "MISSING_ANNOTATIONS"]
    assert len(missing) == 1
    assert missing[0].severity == "warning"
    assert not any(f.code == "HUMAN_ANNOTATION" for f in report.findings)


def test_annotations_cannot_change_accuracy_entropy_selectivity(tmp_path: Path) -> None:
    data = tmp_path / "data"
    write_demo_dataset(data)
    manifest, records = read_dataset(data / "manifest.json")
    context = read_item_context(manifest, data)
    clean = build_report(records, manifest, item_context=context)
    annotated = build_report(
        records,
        manifest,
        item_context=context,
        annotations=(
            make_annotation(
                annotation_id="demo-k1",
                dataset_id="demo-skewed",
                item_id="k1",
                gold_uniqueness="contested",
                origin="agent",
                text="proposed contested; not a gold rewrite",
            ),
        ),
    )
    assert _score_fingerprint(clean) == _score_fingerprint(annotated)
    assert [row.gold for row in clean.records] == [row.gold for row in annotated.records]
    assert [row.stored_answer for row in clean.records] == [row.stored_answer for row in annotated.records]
    assert [row.parsed_answer for row in clean.records] == [row.parsed_answer for row in annotated.records]
    human = [f for f in annotated.findings if f.code == "HUMAN_ANNOTATION"]
    assert len(human) == 1
    assert human[0].origin == "human_annotation"
    assert human[0].observed["gold_uniqueness"] == "contested"
    assert human[0].observed["origin"] == "agent"
    assert not any(f.code == "MISSING_ANNOTATIONS" for f in annotated.findings)


def test_cli_malformed_annotations_exit_2(tmp_path: Path) -> None:
    data = tmp_path / "data"
    write_demo_dataset(data)
    bad = tmp_path / "bad.jsonl"
    bad.write_text('{"annotation_id": "x"}\n', encoding="utf-8")
    assert (
        main(
            [
                "audit",
                "--manifest",
                str(data / "manifest.json"),
                "--out",
                str(tmp_path / "out"),
                "--annotations",
                str(bad),
            ]
        )
        == 2
    )


def test_cli_annotations_do_not_change_demo_scores(tmp_path: Path) -> None:
    data = tmp_path / "data"
    write_demo_dataset(data)
    clean_out = tmp_path / "clean"
    ann_out = tmp_path / "ann"
    ann = tmp_path / "ann.jsonl"
    ann.write_text(
        json.dumps(
            {
                "annotation_id": "demo-k1",
                "dataset_id": "demo-skewed",
                "item_id": "k1",
                "text": "rationale for contested key",
                "author": "tester",
                "status": "proposed",
                "origin": "human",
                "gold_uniqueness": "contested",
                "source_references": ["demo"],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    assert main(["audit", "--manifest", str(data / "manifest.json"), "--out", str(clean_out)]) == 0
    assert main(
        [
            "audit",
            "--manifest",
            str(data / "manifest.json"),
            "--out",
            str(ann_out),
            "--annotations",
            str(ann),
        ]
    ) == 0
    clean = json.loads((clean_out / "report.json").read_text(encoding="utf-8"))
    annotated = json.loads((ann_out / "report.json").read_text(encoding="utf-8"))
    assert clean["group_metrics"] == annotated["group_metrics"]
    assert clean["comparison_metrics"] == annotated["comparison_metrics"]
    assert any(f["code"] == "MISSING_ANNOTATIONS" for f in clean["findings"])
    assert any(f["code"] == "HUMAN_ANNOTATION" for f in annotated["findings"])
    md = (ann_out / "report.md").read_text(encoding="utf-8")
    assert "## 6. Gold uniqueness annotations" in md
    assert "contested" in md


def test_proposed_example_loads_as_agent_contested() -> None:
    items = load_annotation_file(EXAMPLES)
    assert len(items) == 1
    ann = items[0]
    assert ann.status == "proposed"
    assert ann.origin == "agent"
    assert ann.gold_uniqueness == "contested"
    assert ann.item_id == "hd1"
    assert "NOT human-reviewed" in ann.text
    assert ann.dataset_id == "historical-h2"


def test_reviewed_example_loads_as_human_contested() -> None:
    items = load_annotation_file(REVIEWED)
    assert len(items) == 1
    ann = items[0]
    assert ann.status == "reviewed"
    assert ann.origin == "human"
    assert ann.gold_uniqueness == "contested"
    assert ann.item_id == "hd1"
    assert ann.author == "Uday"
    assert "Gold is not rewritten" in ann.text
    assert ann.dataset_id == "historical-h2"


def test_run_checks_annotations_do_not_touch_rows() -> None:
    golds = {"i1": "A", "i2": "B"}
    rows = pair_set(golds, golds, golds, dataset_id="syn", run_id="R")
    from eval_audit.schema import SCHEMA_VERSION, Artifact, Comparison, Manifest

    manifest = Manifest(
        schema_version=SCHEMA_VERSION,
        adapter_version="1",
        profile="historical-v1",
        artifacts=(Artifact("FIX", "raw.json", "raw.json", ZERO, 0, {"origin": "synthetic"}),),
        normalized_file="normalized.jsonl",
        normalized_sha256=ZERO,
        comparisons=(Comparison("R", "syn", "synthetic", "R", "baseline", "cue"),),
        provenance_notes=("synthetic",),
    )
    before = [(r.gold, r.stored_answer, r.parsed_answer) for r in rows]
    findings = run_checks(
        rows,
        manifest,
        annotations=(make_annotation(dataset_id="syn", item_id="i1", gold_uniqueness="invalid-key"),),
    )
    after = [(r.gold, r.stored_answer, r.parsed_answer) for r in rows]
    assert before == after
    assert any(f.code == "HUMAN_ANNOTATION" and f.severity == "warning" for f in findings)


def test_historical_proposed_annotation_does_not_change_h2_headlines(tmp_path: Path) -> None:
    historical = Path(__import__("os").environ.get("EVAL_AUDIT_HISTORICAL_SOURCE", "/__eval_audit_source_not_configured__"))
    if not historical.is_dir():
        pytest.skip("Historical source tree is not present")
    from fractions import Fraction

    from eval_audit.loaders import load_historical
    from eval_audit.metrics import compare, pair_rows, summarize
    from eval_audit.schema import profile_by_name

    dest = tmp_path / "data"
    load_historical(historical, dest)
    manifest, records = read_dataset(dest / "manifest.json")
    context = read_item_context(manifest, dest)
    annotations = tuple(load_annotation_file(EXAMPLES))
    clean = build_report(records, manifest, item_context=context)
    annotated = build_report(records, manifest, item_context=context, annotations=annotations)
    assert _score_fingerprint(clean) == _score_fingerprint(annotated)
    profile = profile_by_name("historical-v1")
    m2_base = [r for r in annotated.records if r.run_id == "M2" and r.condition == "baseline"]
    m2_cue = [r for r in annotated.records if r.run_id == "M2" and r.condition == "eval_cued_incentive_strong"]
    assert summarize(m2_base, "stored").n_correct == 11
    assert summarize(m2_base, "stored").n_total == 12
    assert summarize(m2_cue, "stored").n_correct == 12
    comparison = next(c for c in manifest.comparisons if c.comparison_id == "M2")
    metrics = compare(pair_rows(annotated.records, comparison), "stored", profile, comparison=comparison)
    assert metrics.selectivity == Fraction(-1, 6)
    hd1_golds = {r.gold for r in annotated.records if r.item_id == "hd1"}
    assert hd1_golds == {"B"}
    assert any(f.code == "HUMAN_ANNOTATION" and f.observed.get("gold_uniqueness") == "contested" for f in annotated.findings)


def test_historical_reviewed_annotation_does_not_change_h2_headlines(tmp_path: Path) -> None:
    historical = Path(__import__("os").environ.get("EVAL_AUDIT_HISTORICAL_SOURCE", "/__eval_audit_source_not_configured__"))
    if not historical.is_dir():
        pytest.skip("Historical source tree is not present")
    from fractions import Fraction

    from eval_audit.loaders import load_historical
    from eval_audit.metrics import compare, pair_rows, summarize
    from eval_audit.schema import profile_by_name

    dest = tmp_path / "data"
    load_historical(historical, dest)
    manifest, records = read_dataset(dest / "manifest.json")
    context = read_item_context(manifest, dest)
    annotations = tuple(load_annotation_file(REVIEWED))
    clean = build_report(records, manifest, item_context=context)
    annotated = build_report(records, manifest, item_context=context, annotations=annotations)
    assert _score_fingerprint(clean) == _score_fingerprint(annotated)
    profile = profile_by_name("historical-v1")
    m2_base = [r for r in annotated.records if r.run_id == "M2" and r.condition == "baseline"]
    m2_cue = [r for r in annotated.records if r.run_id == "M2" and r.condition == "eval_cued_incentive_strong"]
    assert summarize(m2_base, "stored").n_correct == 11
    assert summarize(m2_base, "stored").n_total == 12
    assert summarize(m2_cue, "stored").n_correct == 12
    comparison = next(c for c in manifest.comparisons if c.comparison_id == "M2")
    metrics = compare(pair_rows(annotated.records, comparison), "stored", profile, comparison=comparison)
    assert metrics.selectivity == Fraction(-1, 6)
    without = next(
        row
        for row in annotated.item_influence
        if row.item_id == "hd1" and row.answer_basis == "stored" and row.comparison_id == "M2"
    )
    assert without.without_selectivity == Fraction(0, 1)
    md_dir = tmp_path / "out"
    from eval_audit.report import write_report

    write_report(annotated, md_dir)
    md = (md_dir / "report.md").read_text(encoding="utf-8")
    assert "Reviewed contested / invalid-key sensitivity" in md
    assert "M2" in md
    assert annotated.findings
    assert any(
        f.code == "HUMAN_ANNOTATION"
        and f.observed.get("status") == "reviewed"
        and f.observed.get("origin") == "human"
        for f in annotated.findings
    )
