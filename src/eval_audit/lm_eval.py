"""EleutherAI lm-evaluation-harness adapter.

Ingests evaluation outputs from lm-evaluation-harness (https://github.com/EleutherAI/lm-evaluation-harness).
Converts sample dumps (generated via --log_samples) into eval-audit generic bundle format.
Zero runtime dependencies; stdlib only.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any

from eval_audit.generic import load_generic
from eval_audit.schema import AuditInputError, Manifest

DEFAULT_ALLOWED = ["A", "B", "C", "D"]


def load_lm_eval(source: Path, out_dir: Path) -> Manifest:
    """Load an lm-evaluation-harness sample output JSON and convert to eval-audit manifest."""
    source = source.resolve()
    if not source.exists():
        raise AuditInputError(f"lm-eval source does not exist: {source}", field="source")

    try:
        data = json.loads(source.read_text(encoding="utf-8"))
    except Exception as exc:
        raise AuditInputError("source is not valid JSON", field="source") from exc

    model_name = data.get("config", {}).get("model_name", "unknown-model")
    if not model_name or model_name == "unknown-model":
        model_name = data.get("model_name", "unknown-model")

    samples_by_task = data.get("samples", {})
    if not samples_by_task:
        raise AuditInputError(
            "no samples dictionary found in lm-eval output (did you run with --log_samples?)",
            field="samples",
        )

    task_name = next(iter(samples_by_task.keys()))
    samples = samples_by_task[task_name]
    run_id = f"LM_EVAL_{task_name.upper()}"

    rows: list[dict[str, Any]] = []
    items: list[dict[str, Any]] = []

    for index, sample in enumerate(samples):
        item_id = str(sample.get("doc_id", f"item_{index+1:04d}"))
        target = sample.get("target", "")
        if isinstance(target, int) and 0 <= target < 4:
            gold = DEFAULT_ALLOWED[target]
        else:
            gold = str(target).strip()

        resps = sample.get("resps", [])
        if resps and isinstance(resps, list):
            first_resp = resps[0]
            if isinstance(first_resp, list) and first_resp:
                response_text = str(first_resp[0])
            else:
                response_text = str(first_resp)
        else:
            response_text = str(sample.get("filtered_resps", [""])[0] if sample.get("filtered_resps") else "")

        arguments = sample.get("arguments", {})
        prompt = ""
        if isinstance(arguments, dict):
            prompt = arguments.get("gen_args_0", {}).get("arg_0", "")
        elif isinstance(arguments, list) and arguments:
            prompt = str(arguments[0])

        items.append({
            "dataset_id": task_name,
            "item_id": item_id,
            "definition_gold": gold,
            "question_with_options": prompt or f"Item {item_id}",
            "source_locator": f"lm_eval:{task_name}:{item_id}",
            "provenance_status": "lm_eval_sample",
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
            "allowed_answers": DEFAULT_ALLOWED,
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
            "allowed_answers": DEFAULT_ALLOWED,
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
            f"Imported from lm-evaluation-harness log: {source.name}",
            f"Model: {model_name}, Task: {task_name}",
        ],
        "comparisons": comparisons,
        "items": items,
        "rows": rows,
    }

    with tempfile.NamedTemporaryFile(suffix=".json", mode="w", encoding="utf-8", delete=False) as f:
        json.dump(bundle, f, indent=2)
        temp_bundle_path = Path(f.name)

    try:
        manifest = load_generic(temp_bundle_path, out_dir)
    finally:
        temp_bundle_path.unlink(missing_ok=True)

    return manifest
