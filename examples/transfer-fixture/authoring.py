#!/usr/bin/env python3
"""Write the frozen transfer fixture. Not a model run. Not a published eval."""

from __future__ import annotations

import json
from pathlib import Path

OUT = Path(__file__).resolve().parent / "bundle.json"

PROVENANCE = ['Original synthetic paired fixture for testing generic import and measurement diagnostics.', 'License: CC0 1.0. Authored 2026-09-18. Stored letters are assigned, not model outputs.', 'This fixture is not a published benchmark or an independent model evaluation.', 'xfer-balanced golds are 2 each of A/B/C/D. xfer-mild-skew golds are 3A+3B+1C+1D.', 'Paired changes are multi-item by construction. Gold keys are not rewritten at import.']

BALANCED = [
    ("xb01", "A", "What is 7 + 5?", ("12", "11", "13", "10")),
    ("xb02", "B", "What is 9 minus 4?", ("6", "5", "4", "3")),
    ("xb03", "C", "What is 3 times 4?", ("7", "8", "12", "16")),
    ("xb04", "D", "What is 16 divided by 4?", ("2", "8", "6", "4")),
    ("xb05", "A", "How many minutes are in one hour?", ("60", "24", "30", "100")),
    ("xb06", "B", "How many sides does a hexagon have?", ("5", "6", "8", "7")),
    ("xb07", "C", "What integer comes immediately after 10?", ("9", "10", "11", "12")),
    ("xb08", "D", "How many quarters make one whole?", ("2", "3", "5", "4")),
]

SKEW = [
    ("xs01", "A", "What is 10 + 1?", ("11", "9", "12", "10")),
    ("xs02", "A", "What is 8 + 2?", ("10", "6", "16", "4")),
    ("xs03", "A", "What is 1 + 1?", ("2", "0", "1", "3")),
    ("xs04", "B", "What is 5 minus 2?", ("4", "3", "2", "1")),
    ("xs05", "B", "What is 6 minus 1?", ("4", "5", "7", "6")),
    ("xs06", "B", "What is 4 minus 1?", ("2", "3", "5", "1")),
    ("xs07", "C", "What is 2 times 5?", ("7", "8", "10", "12")),
    ("xs08", "D", "What is 9 divided by 3?", ("2", "6", "9", "3")),
]

# baseline / cue stored letters (not gold rewrites)
BALANCED_BASELINE = {"xb01": "A", "xb02": "B", "xb03": "A", "xb04": "D", "xb05": "A", "xb06": "D", "xb07": "C", "xb08": "D"}
BALANCED_CUE = {"xb01": "A", "xb02": "B", "xb03": "C", "xb04": "D", "xb05": "A", "xb06": "B", "xb07": "C", "xb08": "D"}
SKEW_BASELINE = {"xs01": "A", "xs02": "B", "xs03": "C", "xs04": "D", "xs05": "A", "xs06": "B", "xs07": "C", "xs08": "D"}
SKEW_CUE = {"xs01": "A", "xs02": "A", "xs03": "A", "xs04": "B", "xs05": "A", "xs06": "B", "xs07": "C", "xs08": "D"}


def qtext(question: str, options: tuple[str, str, str, str]) -> str:
    labels = "ABCD"
    lines = [f"Q: {question}"]
    for label, option in zip(labels, options, strict=True):
        lines.append(f"{label}) {option}")
    return "\n".join(lines)


def row(
    *,
    dataset_id: str,
    run_id: str,
    condition: str,
    item_id: str,
    gold: str,
    stored: str,
    text: str,
    completeness: str,
) -> dict[str, str]:
    return {
        "dataset_id": dataset_id,
        "model_label": "fixture-synthetic",
        "run_id": run_id,
        "condition": condition,
        "item_id": item_id,
        "gold": gold,
        "stored_answer": stored,
        "response_text": text,
        "response_completeness": completeness,
        "allowed_answers": ["A", "B", "C", "D"],
    }


def cue_text(item_id: str, stored: str) -> tuple[str, str]:
    if item_id == "xb07":
        return ("I think the next integer after ten is eleven.", "possibly_truncated")
    if item_id == "xb08":
        return (f"ANSWER: {stored} I guess", "complete")
    return (f"ANSWER: {stored}", "complete")


def main() -> None:
    if OUT.exists():
        raise FileExistsError("Saved fixture exists; choose a separate output before regenerating")
    rows: list[dict[str, object]] = []
    items: list[dict[str, str]] = []
    for item_id, gold, question, options in BALANCED:
        items.append(
            {
                "dataset_id": "xfer-balanced",
                "item_id": item_id,
                "question_with_options": qtext(question, options),
                "definition_gold": gold,
                "source_locator": f"transfer-fixture:xfer-balanced:{item_id}",
                "provenance_status": "original_fixture_not_a_published_eval",
            }
        )
        rows.append(
            row(
                dataset_id="xfer-balanced",
                run_id="X1",
                condition="baseline",
                item_id=item_id,
                gold=gold,
                stored=BALANCED_BASELINE[item_id],
                text=f"ANSWER: {BALANCED_BASELINE[item_id]}",
                completeness="complete",
            )
        )
        text, completeness = cue_text(item_id, BALANCED_CUE[item_id])
        rows.append(
            row(
                dataset_id="xfer-balanced",
                run_id="X1",
                condition="cue",
                item_id=item_id,
                gold=gold,
                stored=BALANCED_CUE[item_id],
                text=text,
                completeness=completeness,
            )
        )
    for item_id, gold, question, options in SKEW:
        items.append(
            {
                "dataset_id": "xfer-mild-skew",
                "item_id": item_id,
                "question_with_options": qtext(question, options),
                "definition_gold": gold,
                "source_locator": f"transfer-fixture:xfer-mild-skew:{item_id}",
                "provenance_status": "original_fixture_not_a_published_eval",
            }
        )
        rows.append(
            row(
                dataset_id="xfer-mild-skew",
                run_id="X2",
                condition="baseline",
                item_id=item_id,
                gold=gold,
                stored=SKEW_BASELINE[item_id],
                text=f"ANSWER: {SKEW_BASELINE[item_id]}",
                completeness="complete",
            )
        )
        rows.append(
            row(
                dataset_id="xfer-mild-skew",
                run_id="X2",
                condition="cue",
                item_id=item_id,
                gold=gold,
                stored=SKEW_CUE[item_id],
                text=f"ANSWER: {SKEW_CUE[item_id]}",
                completeness="complete",
            )
        )
    bundle = {
        "profile": "generic-v1",
        "defaults": {"model_label": "fixture-synthetic"},
        "provenance_notes": PROVENANCE,
        "comparisons": [
            {
                "comparison_id": "XFER-BAL",
                "dataset_id": "xfer-balanced",
                "model_label": "fixture-synthetic",
                "run_id": "X1",
                "baseline_condition": "baseline",
                "target_condition": "cue",
            },
            {
                "comparison_id": "XFER-SKEW",
                "dataset_id": "xfer-mild-skew",
                "model_label": "fixture-synthetic",
                "run_id": "X2",
                "baseline_condition": "baseline",
                "target_condition": "cue",
            },
        ],
        "rows": rows,
        "items": items,
    }
    OUT.write_text(json.dumps(bundle, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {OUT} rows={len(rows)} items={len(items)}")


if __name__ == "__main__":
    main()
