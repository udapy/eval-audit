#!/usr/bin/env python3
"""Optional collection source: ARC-Challenge saved science slice.

Selects the first qualifying four-option A-D items and requests baseline and
answer-leak responses from Qwen/Qwen3-8B. An answer-leak response may still be
wrong or missing; it is not the computed gold oracle.
This script is not run during offline replay. See README.md in this directory."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

# Add parent dir so we can import from examples.datasets
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent / "datasets"))

from hf_inference import chat_completion, extract_answer_text, mcq_baseline_prompt, mcq_leaked_answer_prompt
from key_distribution import fetch_arc_rows

MODEL = "Qwen/Qwen3-8B"
MODEL_LABEL = "qwen-3-8b"
DATASET_ID = "arc-challenge"
RUN_ID = "ARC_CHALLENGE_RUN"
OUT_DIR = Path(os.environ.get("EVAL_AUDIT_COLLECTION_OUT", str(REPO_ROOT / ".tmp" / "collection" / "arc-challenge")))
BUNDLE_FILE = OUT_DIR / "bundle.json"

def refuse_existing_output() -> None:
    if BUNDLE_FILE.exists():
        raise FileExistsError("Choose a fresh EVAL_AUDIT_COLLECTION_OUT; saved evidence is never overwritten")



def _extract_letter(text: str, labels: list[str]) -> str:
    cleaned = text.strip()
    if cleaned in labels:
        return cleaned
    if cleaned and cleaned[0] in labels and (len(cleaned) == 1 or not cleaned[1].isalpha()):
        return cleaned[0]
    for char in cleaned:
        if char in labels:
            return char
    return ""


def run_experiment(n_items: int = 25) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Running Experiment 3: ARC-Challenge ({n_items} items, {MODEL})")

    raw_rows = fetch_arc_rows(split="test", max_pages=3)
    if not raw_rows:
        raise RuntimeError("No rows fetched for ARC-Challenge")

    # Filter to 4-option questions with letters A-D
    four_opt_items = []
    for r in raw_rows:
        choices = r.get("choices", {})
        labels = choices.get("label", [])
        texts = choices.get("text", [])
        key = str(r.get("answerKey", ""))
        if len(labels) == 4 and key in ("A", "B", "C", "D") and labels == ["A", "B", "C", "D"]:
            four_opt_items.append({
                "id": r.get("id", f"arc_{len(four_opt_items)+1:02d}"),
                "question": r.get("question", ""),
                "options": texts,
                "gold": key,
            })
        if len(four_opt_items) >= n_items:
            break

    print(f"Selected {len(four_opt_items)} 4-option ARC-Challenge items.")
    rows: list[dict[str, Any]] = []
    items: list[dict[str, Any]] = []

    for i, item in enumerate(four_opt_items, 1):
        item_id = item["id"]
        gold = item["gold"]
        options = item["options"]
        question = item["question"]
        labels = ["A", "B", "C", "D"]
        q_with_opts = f"{question}\n" + "\n".join(f"{lbl}) {opt}" for lbl, opt in zip(labels, options))

        items.append({
            "dataset_id": DATASET_ID,
            "item_id": item_id,
            "definition_gold": gold,
            "question_with_options": q_with_opts,
            "source_locator": f"arc_challenge:{item_id}",
            "provenance_status": "published_eval_arc_clark_2018",
        })

        # Baseline
        base_msgs = mcq_baseline_prompt(question=question, options=options, option_labels=labels)
        try:
            base_resp = chat_completion(model=MODEL, messages=base_msgs, max_tokens=64, temperature=0.0)
            base_text = extract_answer_text(base_resp)
            base_letter = _extract_letter(base_text, labels)
        except Exception as e:
            print(f"Error on {item_id} baseline: {e}", file=sys.stderr)
            base_text = ""
            base_letter = ""

        rows.append({
            "dataset_id": DATASET_ID,
            "model_label": MODEL_LABEL,
            "run_id": RUN_ID,
            "item_id": item_id,
            "condition": "baseline",
            "gold": gold,
            "stored_answer": base_letter,
            "response_text": base_text,
            "response_completeness": "complete" if base_letter else "missing",
            "allowed_answers": labels,
        })

        # Leaked key (cue)
        leak_msgs = mcq_leaked_answer_prompt(
            question=question, options=options, gold_key=gold, option_labels=labels
        )
        try:
            leak_resp = chat_completion(model=MODEL, messages=leak_msgs, max_tokens=64, temperature=0.0)
            leak_text = extract_answer_text(leak_resp)
            leak_letter = _extract_letter(leak_text, labels)
        except Exception as e:
            print(f"Error on {item_id} leak: {e}", file=sys.stderr)
            leak_text = ""
            leak_letter = ""

        rows.append({
            "dataset_id": DATASET_ID,
            "model_label": MODEL_LABEL,
            "run_id": RUN_ID,
            "item_id": item_id,
            "condition": "cue",
            "gold": gold,
            "stored_answer": leak_letter,
            "response_text": leak_text,
            "response_completeness": "complete" if leak_letter else "missing",
            "allowed_answers": labels,
        })

        print(f"  [{i:2d}/{len(four_opt_items)}] {item_id}: gold={gold} | base={base_letter} | leak={leak_letter}")

    comparisons = [
        {
            "comparison_id": "ARC-CHALLENGE-COMP",
            "dataset_id": DATASET_ID,
            "model_label": MODEL_LABEL,
            "run_id": RUN_ID,
            "baseline_condition": "baseline",
            "target_condition": "cue",
        }
    ]

    bundle = {
        "profile": "generic-v1",
        "defaults": {
            "model_label": MODEL_LABEL,
        },
        "provenance_notes": [
            f"Model: {MODEL} via HF Inference API",
            "Benchmark: ARC-Challenge (allenai/ai2_arc; Clark et al., 2018)",
            "License: CC-BY-SA 4.0",
            "Condition 'baseline': standard zero-shot MCQ prompt",
            "Condition 'cue': prompt includes gold answer leak in system message",
        ],
        "comparisons": comparisons,
        "items": items,
        "rows": rows,
    }

    BUNDLE_FILE.write_text(json.dumps(bundle, indent=2) + "\n")
    print(f"\nWrote {len(rows)} rows to {BUNDLE_FILE}")


def main() -> None:
    run_experiment(n_items=25)


if __name__ == "__main__":
    refuse_existing_output()
    main()
