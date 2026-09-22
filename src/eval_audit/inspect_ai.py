"""Inspect AI log adapter.

Ingests evaluation outputs from UK AISI / Inspect AI (https://github.com/UKGovernmentBEIS/inspect_ai).
Converts Inspect sample logs into eval-audit generic bundle format for claim-integrity auditing.
Zero runtime dependencies; stdlib only.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from eval_audit.generic import load_generic
from eval_audit.schema import AuditInputError, Manifest

DEFAULT_ALLOWED = ["A", "B", "C", "D"]


def load_inspect_eval(source: Path, out_dir: Path) -> Manifest:
    """Load an Inspect AI .eval or .json log file and convert to eval-audit manifest."""
    source = source.resolve()
    if not source.exists():
        raise AuditInputError(f"inspect source does not exist: {source}", field="source")

    try:
        data = json.loads(source.read_text(encoding="utf-8"))
    except Exception as exc:
        raise AuditInputError("source is not valid JSON", field="source") from exc

    eval_meta = data.get("eval", {})
    model_name = eval_meta.get("model", "unknown-model")
    task_name = eval_meta.get("task", "unknown-task")
    run_id = eval_meta.get("run_id", f"INSPECT_{task_name.upper()}")

    samples = data.get("samples", [])
    if not samples:
        raise AuditInputError("no samples found in inspect eval log", field="samples")

    rows: list[dict[str, Any]] = []
    items: list[dict[str, Any]] = []

    for index, sample in enumerate(samples):
        item_id = str(sample.get("id", f"sample_{index+1:04d}"))
        target = sample.get("target")
        if isinstance(target, list):
            target = target[0] if target else ""
        gold = str(target).strip()

        # Extract options if present
        choices = sample.get("choices")
        allowed = DEFAULT_ALLOWED
        if choices and isinstance(choices, list) and len(choices) <= 10:
            allowed = ["ABCDEFGHIJKLMNOPQRSTUVWXYZ"[i] for i in range(len(choices))]

        # Output / completion
        output_obj = sample.get("output", {})
        if isinstance(output_obj, dict):
            choices_list = output_obj.get("choices", [])
            if choices_list and isinstance(choices_list[0], dict):
                msg = choices_list[0].get("message", {})
                response_text = msg.get("content") or ""
            else:
                response_text = str(output_obj.get("completion", ""))
        else:
            response_text = str(output_obj)

        input_content = sample.get("input", "")
        if isinstance(input_content, list):
            input_str = "\n".join(str(m.get("content", "")) for m in input_content)
        else:
            input_str = str(input_content)

        items.append({
            "dataset_id": task_name,
            "item_id": item_id,
            "definition_gold": gold,
            "question_with_options": input_str or f"Item {item_id}",
            "source_locator": f"inspect:{task_name}:{item_id}",
            "provenance_status": "inspect_ai_log",
        })

        rows.append({
            "dataset_id": task_name,
            "model_label": model_name,
            "run_id": run_id,
            "condition": "baseline",
            "item_id": item_id,
            "gold": gold,
            "stored_answer": gold if response_text.endswith(gold) else None,
            "response_text": response_text,
            "response_completeness": "complete" if response_text else "unknown",
            "allowed_answers": allowed,
        })
        rows.append({
            "dataset_id": task_name,
            "model_label": model_name,
            "run_id": run_id,
            "condition": "evaluated",
            "item_id": item_id,
            "gold": gold,
            "stored_answer": gold if response_text.endswith(gold) else None,
            "response_text": response_text,
            "response_completeness": "complete" if response_text else "unknown",
            "allowed_answers": allowed,
        })

    comparisons = [
        {
            "comparison_id": f"{task_name.upper()}-AUDIT",
            "dataset_id": task_name,
            "model_label": model_name,
            "run_id": run_id,
            "baseline_condition": "baseline",
            "target_condition": "evaluated",
        }
    ]

    bundle = {
        "profile": "generic-v1",
        "defaults": {"model_label": model_name},
        "provenance_notes": [
            f"Imported from Inspect AI log: {source.name}",
            f"Model: {model_name}, Task: {task_name}",
        ],
        "comparisons": comparisons,
        "items": items,
        "rows": rows,
    }

    import tempfile

    with tempfile.NamedTemporaryFile(suffix=".json", mode="w", encoding="utf-8", delete=False) as f:
        json.dump(bundle, f, indent=2)
        temp_bundle_path = Path(f.name)

    try:
        manifest = load_generic(temp_bundle_path, out_dir)
    finally:
        temp_bundle_path.unlink(missing_ok=True)

    return manifest
