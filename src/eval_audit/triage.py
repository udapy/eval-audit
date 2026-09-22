"""Blinded adjudication triage: Extract high-influence and parse-divergent items.

Extracts items requiring human review into a blinded adjudication queue without
exposing model condition, historical accuracy, or research hypothesis to raters.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from eval_audit.checks import comparison_bundle, run_checks
from eval_audit.identity import stable_id
from eval_audit.loaders import read_dataset, read_item_context
from eval_audit.schema import AuditInputError, ItemContext, Manifest, Record

VERDICTS = ("unique-correct", "contested", "invalid-key", "insufficient-evidence")


def generate_triage_queue(
    manifest_path: Path,
    *,
    influence_threshold: float = 0.05,
) -> list[dict[str, Any]]:
    manifest_path = manifest_path.resolve()
    manifest, records = read_dataset(manifest_path)
    data_dir = manifest_path.parent
    item_context = read_item_context(manifest, data_dir)
    context_map = {(c.dataset_id, c.item_id): c for c in item_context}

    _, _, influence_list, _, _ = comparison_bundle(records, manifest)
    findings = run_checks(records, manifest, item_context=item_context)

    # 1. Flag items with high LOO influence
    high_influence_items: dict[tuple[str, str], list[str]] = {}
    datasets = {c.comparison_id: c.dataset_id for c in manifest.comparisons}
    for inf in influence_list:
        if inf.accuracy_drop_difference is not None and abs(float(inf.accuracy_drop_difference)) >= influence_threshold:
            key = (datasets[inf.comparison_id], inf.item_id)
            high_influence_items.setdefault(key, []).append(
                f"HIGH_INFLUENCE: delta_acc={float(inf.accuracy_drop_difference):.3f}"
            )
        if inf.selectivity_difference is not None and abs(float(inf.selectivity_difference)) >= influence_threshold:
            key = (datasets[inf.comparison_id], inf.item_id)
            high_influence_items.setdefault(key, []).append(
                f"HIGH_INFLUENCE: delta_sel={float(inf.selectivity_difference):.3f}"
            )

    # 2. Flag items with parse disagreements
    parse_disagreements: dict[tuple[str, str], list[str]] = {}
    for f in findings:
        if f.code == "STORED_STRICT_DISAGREEMENT" and "item_id" in f.scope:
            key = (f.scope.get("dataset_id", ""), f.scope["item_id"])
            parse_disagreements.setdefault(key, []).append(
                f"PARSE_DISAGREEMENT: stored={f.observed.get('stored_answer')} parsed={f.observed.get('parsed_answer')}"
            )

    # Combine candidates
    all_keys = sorted(set(high_influence_items.keys()) | set(parse_disagreements.keys()))
    queue: list[dict[str, Any]] = []

    # Map records to extract question text and declared gold
    record_map: dict[tuple[str, str], Record] = {(r.dataset_id, r.item_id): r for r in records}

    for dataset_id, item_id in all_keys:
        rec = record_map.get((dataset_id, item_id))
        if rec is None:
            continue
        ctx = context_map.get((dataset_id, item_id))
        q_text = ctx.question_with_options if ctx else "(Question text unavailable in item context sidecar)"

        reasons = high_influence_items.get((dataset_id, item_id), []) + parse_disagreements.get((dataset_id, item_id), [])

        queue.append({
            "triage_id": stable_id("TRIAGE", dataset_id, item_id),
            "dataset_id": dataset_id,
            "item_id": item_id,
            "declared_gold": rec.gold,
            "question_with_options": q_text,
            "triage_reasons": reasons,
            "allowed_verdicts": list(VERDICTS),
            "blinded_raters": [
                {"slot": 1, "rater_id": None, "verdict": None, "rationale": None, "source_reference": None},
                {"slot": 2, "rater_id": None, "verdict": None, "rationale": None, "source_reference": None},
            ],
            "blinding_guarantee": "Model names and condition labels are omitted. Review reasons may reveal diagnostic values; content can still disclose context.",
        })

    return queue


def write_triage_queue(manifest_path: Path, out_file: Path) -> int:
    out_file = out_file.resolve()
    if out_file.exists():
        raise AuditInputError("triage output already exists", field="out")
    queue = generate_triage_queue(manifest_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with out_file.open("x", encoding="utf-8") as f:
        for entry in queue:
            f.write(json.dumps(entry, sort_keys=True) + "\n")
    return len(queue)
