"""Bundled synthetic demo data. Not Historical results."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from eval_audit import ADAPTER_VERSION, SCHEMA_VERSION
from eval_audit.io import dump_json, dump_jsonl, sha256_file
from eval_audit.loaders import manifest_to_dict, record_to_dict
from eval_audit.parsing import parse_answer
from eval_audit.schema import (
    HISTORICAL_ALLOWED,
    Artifact,
    Comparison,
    ItemContext,
    Manifest,
    Record,
    SourceRef,
    validate_records,
)

DEMO_SHA = "a" * 64


def write_demo_dataset(out_dir: Path) -> Manifest:
    out_dir.mkdir(parents=True, exist_ok=True)
    records = _balanced_records() + _skewed_records()
    validate_records(records)
    raw_path = out_dir / "raw" / "demo.jsonl"
    dump_jsonl(raw_path, [record_to_dict(record) for record in records])
    raw_sha = sha256_file(raw_path)
    records = [
        replace(
            record,
            source=SourceRef(artifact_id="DEMO", sha256=raw_sha, json_pointer=record.source.json_pointer),
        )
        for record in records
    ]
    dump_jsonl(out_dir / "normalized.jsonl", [record_to_dict(record) for record in records])
    context = _context(raw_sha)
    dump_jsonl(
        out_dir / "item_context.jsonl",
        [
            {
                "dataset_id": item.dataset_id,
                "item_id": item.item_id,
                "question_with_options": item.question_with_options,
                "definition_gold": item.definition_gold,
                "source_artifact_sha256": item.source_artifact_sha256,
                "source_locator": item.source_locator,
                "provenance_status": item.provenance_status,
            }
            for item in context
        ],
    )
    manifest = Manifest(
        schema_version=SCHEMA_VERSION,
        adapter_version=ADAPTER_VERSION,
        profile="historical-v1",
        artifacts=(
            Artifact(
                artifact_id="DEMO",
                original_relative_path="raw/demo.jsonl",
                copied_relative_path="raw/demo.jsonl",
                sha256=raw_sha,
                row_count=len(records),
                assigned_labels={"origin": "synthetic_demo", "not": "historical_results"},
            ),
        ),
        normalized_file="normalized.jsonl",
        normalized_sha256=sha256_file(out_dir / "normalized.jsonl"),
        comparisons=(
            Comparison(
                comparison_id="D-balanced",
                dataset_id="demo-balanced",
                model_label="synthetic",
                run_id="D1",
                baseline_condition="baseline",
                target_condition="cue",
            ),
            Comparison(
                comparison_id="D-skewed",
                dataset_id="demo-skewed",
                model_label="synthetic",
                run_id="D2",
                baseline_condition="baseline",
                target_condition="cue",
            ),
        ),
        provenance_notes=(
            "Synthetic demo. These rows are not Historical results.",
            "demo-balanced is a clean negative control with uniform golds A/B/C/D.",
            "demo-skewed has golds B,B,B,C; the gold oracle is a counterexample to the entropy heuristic.",
        ),
        item_context_file="item_context.jsonl",
        item_context_sha256=sha256_file(out_dir / "item_context.jsonl"),
    )
    dump_json(out_dir / "manifest.json", manifest_to_dict(manifest))
    return manifest


def _record(
    *,
    dataset_id: str,
    run_id: str,
    condition: str,
    item_id: str,
    gold: str,
    stored: str,
    pointer: str,
    bank: str | None = None,
) -> Record:
    text = f"ANSWER: {stored}"
    parsed = parse_answer(text, HISTORICAL_ALLOWED)
    return Record(
        schema_version=SCHEMA_VERSION,
        dataset_id=dataset_id,
        model_label="synthetic",
        run_id=run_id,
        condition=condition,
        item_id=item_id,
        repeat_id=None,
        permutation_id=None,
        bank=bank,
        allowed_answers=HISTORICAL_ALLOWED,
        gold=gold,
        stored_answer=stored,
        stored_correct=stored == gold,
        response_text=text,
        response_completeness="complete",
        parsed_answer=parsed.answer,
        parse_status=parsed.status,
        source=SourceRef(artifact_id="DEMO", sha256=DEMO_SHA, json_pointer=pointer),
        source_fields={},
    )


def _balanced_records() -> list[Record]:
    golds = {"i1": "A", "i2": "B", "i3": "C", "i4": "D"}
    rows: list[Record] = []
    index = 0
    for condition in ("baseline", "cue"):
        for item_id, gold in golds.items():
            rows.append(
                _record(
                    dataset_id="demo-balanced",
                    run_id="D1",
                    condition=condition,
                    item_id=item_id,
                    gold=gold,
                    stored=gold,
                    pointer=f"/balanced/{index}",
                )
            )
            index += 1
    return rows


def _skewed_records() -> list[Record]:
    golds = {"k1": "B", "k2": "B", "k3": "B", "k4": "C"}
    baseline_answers = {"k1": "A", "k2": "B", "k3": "C", "k4": "D"}
    cue_answers = {"k1": "B", "k2": "B", "k3": "B", "k4": "B"}
    rows: list[Record] = []
    index = 0
    for condition, answers in (("baseline", baseline_answers), ("cue", cue_answers)):
        for item_id, gold in golds.items():
            rows.append(
                _record(
                    dataset_id="demo-skewed",
                    run_id="D2",
                    condition=condition,
                    item_id=item_id,
                    gold=gold,
                    stored=answers[item_id],
                    pointer=f"/skewed/{index}",
                )
            )
            index += 1
    return rows


def _context(source_sha256: str) -> list[ItemContext]:
    items = []
    questions = {
        ("demo-balanced", "i1", "A"): "Q: one?\nA) one\nB) two\nC) three\nD) four",
        ("demo-balanced", "i2", "B"): "Q: two?\nA) one\nB) two\nC) three\nD) four",
        ("demo-balanced", "i3", "C"): "Q: three?\nA) one\nB) two\nC) three\nD) four",
        ("demo-balanced", "i4", "D"): "Q: four?\nA) one\nB) two\nC) three\nD) four",
        ("demo-skewed", "k1", "B"): "Q: skewed-1?\nA) a\nB) b\nC) c\nD) d",
        ("demo-skewed", "k2", "B"): "Q: skewed-2?\nA) a\nB) b\nC) c\nD) d",
        ("demo-skewed", "k3", "B"): "Q: skewed-3?\nA) a\nB) b\nC) c\nD) d",
        ("demo-skewed", "k4", "C"): "Q: skewed-4?\nA) a\nB) b\nC) c\nD) d",
    }
    for (dataset_id, item_id, gold), question in questions.items():
        items.append(
            ItemContext(
                dataset_id=dataset_id,
                item_id=item_id,
                question_with_options=question,
                definition_gold=gold,
                source_artifact_sha256=source_sha256,
                source_locator=f"demo:{dataset_id}:{item_id}",
                provenance_status="synthetic_demo",
            )
        )
    return items
