from __future__ import annotations

from eval_audit.parsing import parse_answer
from eval_audit.schema import Annotation, HISTORICAL_ALLOWED, SCHEMA_VERSION, Record, SourceRef

ZERO_SHA = "0" * 64


def make_record(
    *,
    dataset_id: str = "syn",
    model_label: str = "synthetic",
    run_id: str = "R",
    condition: str = "baseline",
    item_id: str = "i1",
    gold: str = "A",
    stored: str | None = "A",
    text: str | None = "ANSWER: A",
    bank: str | None = None,
    stored_correct: bool | None = None,
    completeness: str = "complete",
    allowed: tuple[str, ...] = HISTORICAL_ALLOWED,
    pointer: str = "/rows/0",
    repeat_id: str | None = None,
    permutation_id: str | None = None,
    option_order: tuple[str, ...] | None = None,
    gold_content_id: str | None = None,
    artifact_id: str = "U",
    schema_version: int = SCHEMA_VERSION,
) -> Record:
    parsed = parse_answer(text, allowed)
    if stored_correct is None and stored is not None:
        stored_correct = stored == gold
    return Record(
        schema_version=schema_version,
        dataset_id=dataset_id,
        model_label=model_label,
        run_id=run_id,
        condition=condition,
        item_id=item_id,
        repeat_id=repeat_id,
        permutation_id=permutation_id,
        bank=bank,
        allowed_answers=allowed,
        gold=gold,
        stored_answer=stored,
        stored_correct=stored_correct,
        response_text=text,
        response_completeness=completeness,
        parsed_answer=parsed.answer,
        parse_status=parsed.status,
        source=SourceRef(artifact_id, ZERO_SHA, pointer),
        source_fields={},
        option_order=option_order,
        gold_content_id=gold_content_id,
    )


def make_annotation(
    *,
    annotation_id: str = "a1",
    dataset_id: str = "syn",
    item_id: str | None = "i1",
    text: str = "rationale",
    author: str = "reviewer",
    status: str = "proposed",
    origin: str = "human",
    gold_uniqueness: str | None = "contested",
    source_references: tuple[str, ...] = (),
) -> Annotation:
    return Annotation(
        annotation_id=annotation_id,
        dataset_id=dataset_id,
        item_id=item_id,
        text=text,
        author=author,
        status=status,
        origin=origin,
        gold_uniqueness=gold_uniqueness,
        source_references=source_references,
    )


def pair_set(
    golds: dict[str, str],
    baseline: dict[str, str],
    target: dict[str, str],
    *,
    banks: dict[str, str] | None = None,
    dataset_id: str = "syn",
    run_id: str = "R",
    target_condition: str = "cue",
    artifact_id: str = "U",
) -> list[Record]:
    rows: list[Record] = []
    for item_id, gold in golds.items():
        bank = None if banks is None else banks[item_id]
        rows.append(
            make_record(
                dataset_id=dataset_id,
                run_id=run_id,
                condition="baseline",
                item_id=item_id,
                gold=gold,
                stored=baseline[item_id],
                text=f"ANSWER: {baseline[item_id]}",
                bank=bank,
                pointer=f"/b/{item_id}",
                artifact_id=artifact_id,
            )
        )
        rows.append(
            make_record(
                dataset_id=dataset_id,
                run_id=run_id,
                condition=target_condition,
                item_id=item_id,
                gold=gold,
                stored=target[item_id],
                text=f"ANSWER: {target[item_id]}",
                bank=bank,
                pointer=f"/t/{item_id}",
                artifact_id=artifact_id,
            )
        )
    return rows
