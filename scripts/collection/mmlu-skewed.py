#!/usr/bin/env python3
"""Optional collection source: MMLU high_school_statistics saved slice.

Selects the first 25 returned test items and requests baseline and answer-leak
responses from meta-llama/Llama-3.1-8B-Instruct. Selection is not random;
the original key-distribution screening examined capped subject slices.
No collection-time dataset revision or serving snapshot is established here.
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
from key_distribution import fetch_mmlu_rows, ANSWER_MAP

MODEL = "meta-llama/Llama-3.1-8B-Instruct"
MODEL_LABEL = "meta-llama-3.1-8b-instruct"
OUT_DIR = Path(os.environ.get("EVAL_AUDIT_COLLECTION_OUT", str(REPO_ROOT / ".tmp" / "collection" / "mmlu-skewed")))
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


def run_experiment(subject: str = "high_school_statistics", n_items: int = 25) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Running Experiment 2: MMLU Skewed ({subject}, {n_items} items, {MODEL})")

    raw_rows = fetch_mmlu_rows(subject)
    if not raw_rows:
        raise RuntimeError(f"No rows found for subject {subject}")

    selected = raw_rows[:n_items]
    rows: list[dict[str, Any]] = []
    items: list[dict[str, Any]] = []

    dataset_id = f"mmlu-{subject.replace('_', '-')}"
    run_id = f"MMLU_{subject.upper()}_RUN"

    for i, item in enumerate(selected, 1):
        item_id = f"stat_{i:02d}"
        raw_ans = item["answer"]
        gold = ANSWER_MAP.get(raw_ans, str(raw_ans)) if isinstance(raw_ans, int) else str(raw_ans)
        options = item["choices"]
        question = item["question"]
        labels = ["A", "B", "C", "D"][:len(options)]
        q_with_opts = f"{question}\n" + "\n".join(f"{lbl}) {opt}" for lbl, opt in zip(labels, options))

        items.append({
            "dataset_id": dataset_id,
            "item_id": item_id,
            "definition_gold": gold,
            "question_with_options": q_with_opts,
            "source_locator": f"mmlu:{subject}:{item_id}",
            "provenance_status": "published_eval_mmlu_hendrycks_2020",
        })

        # Baseline condition
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
            "dataset_id": dataset_id,
            "model_label": MODEL_LABEL,
            "run_id": run_id,
            "item_id": item_id,
            "condition": "baseline",
            "gold": gold,
            "stored_answer": base_letter,
            "response_text": base_text,
            "response_completeness": "complete" if base_letter else "missing",
            "allowed_answers": labels,
        })

        # Leaked key condition (cue)
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
            "dataset_id": dataset_id,
            "model_label": MODEL_LABEL,
            "run_id": run_id,
            "item_id": item_id,
            "condition": "cue",
            "gold": gold,
            "stored_answer": leak_letter,
            "response_text": leak_text,
            "response_completeness": "complete" if leak_letter else "missing",
            "allowed_answers": labels,
        })

        print(f"  [{i:2d}/{n_items}] {item_id}: gold={gold} | base={base_letter} | leak={leak_letter}")

    comparisons = [
        {
            "comparison_id": f"MMLU-{subject.upper()[:4]}-COMP",
            "dataset_id": dataset_id,
            "model_label": MODEL_LABEL,
            "run_id": run_id,
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
            f"Benchmark: MMLU (Hendrycks et al., 2020) subject {subject}",
            "Condition 'baseline': standard zero-shot MCQ prompt",
            "Condition 'cue': prompt includes gold answer leak in system message (answer-leak intervention; distinct from the computed oracle)",
        ],
        "comparisons": comparisons,
        "items": items,
        "rows": rows,
    }

    BUNDLE_FILE.write_text(json.dumps(bundle, indent=2, sort_keys=True) + "\n")
    print(f"\nWrote {len(rows)} rows to {BUNDLE_FILE}")


def main() -> None:
    subject = "high_school_statistics"
    if len(sys.argv) > 1:
        subject = sys.argv[1]
    run_experiment(subject, n_items=25)


if __name__ == "__main__":
    refuse_existing_output()
    main()
