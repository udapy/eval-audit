"""Scoped engineering diagnostics, never authorization of a behavioral claim.

No scalar hygiene score and no new empirical thresholds are introduced here.
The oracle check reproduces the configured historical entropy heuristic.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Any

from eval_audit.metrics import answer_of, pair_rows
from eval_audit.schema import AuditReport, PairingError


def evaluate_gates(report: AuditReport) -> list[dict[str, Any]]:
    results = []
    artifacts = {a.artifact_id: a for a in report.manifest.artifacts}
    hash_ids: dict[str, list[str]] = defaultdict(list)
    for artifact in report.manifest.artifacts:
        hash_ids[artifact.sha256].append(artifact.artifact_id)
    for comparison in report.manifest.comparisons:
        scope = {"dataset_id": comparison.dataset_id, "model_label": comparison.model_label,
                 "run_id": comparison.run_id, "baseline_condition": comparison.baseline_condition,
                 "target_condition": comparison.target_condition}
        rows = [r for r in report.records
                if (r.dataset_id, r.model_label, r.run_id) ==
                (comparison.dataset_id, comparison.model_label, comparison.run_id)
                and r.condition in {comparison.baseline_condition, comparison.target_condition}]
        codes0 = []
        if not rows or any(r.source.artifact_id not in artifacts or
                          artifacts[r.source.artifact_id].sha256 != r.source.sha256
                          for r in rows):
            codes0.append("PROVENANCE_INCOMPLETE")
        duplicates = {r.source.sha256 for r in rows if
                      len(hash_ids[r.source.sha256]) > 1}
        if duplicates:
            codes0.append("DUPLICATE_ARTIFACT")
        g0 = {"status": "INSUFFICIENT_DATA" if not rows else "FLAGGED" if codes0 else "CLEAR",
              "codes": codes0, "duplicate_artifacts": [
                  {"sha256": sha, "artifact_ids": sorted(hash_ids[sha])} for sha in sorted(duplicates)],
              "limitation": "Manifest/source consistency only; identical bytes do not establish duplicate runs. Loader verifies on-disk hashes."}
        codes1 = []
        if any(answer_of(r, "stored") != answer_of(r, "strict") for r in rows):
            codes1.append("PARSER_SENSITIVE")
        if any(r.response_completeness != "complete" for r in rows):
            codes1.append("TRUNCATION_RISK")
        unavailable = sum(r.option_order is None for r in rows)
        if unavailable:
            codes1.append("OPTION_ORDER_UNAVAILABLE")
        mismatches = [r for r in rows if r.option_order is not None and
                      r.option_order[r.allowed_answers.index(r.gold)] != r.gold_content_id]
        if mismatches:
            codes1.append("OPTION_ORDER_KEY_MISMATCH")
        risk1 = set(codes1) - {"OPTION_ORDER_UNAVAILABLE"}
        g1 = {"status": "INSUFFICIENT_DATA" if not rows else "FLAGGED" if risk1 else
              "NOT_ASSESSED" if unavailable else "CLEAR", "codes": codes1,
              "option_order_unavailable_rows": unavailable,
              "limitation": "Strict parsing covers saved text only; missing option identity is not a passed key-order check."}
        oracle = next((c.metrics for c in report.controls if c.comparison_id == comparison.comparison_id
                       and c.control_id == "gold_oracle" and c.answer_basis == "stored"), None)
        complete_oracle = oracle is not None and oracle.entropy_flag is not None and oracle.n_pairs > 0
        g2 = {"status": "INSUFFICIENT_DATA" if not complete_oracle else
              "FLAGGED" if oracle.entropy_flag else "CLEAR",
              "codes": ["INSUFFICIENT_DATA" if not complete_oracle else
                        "ORACLE_DEGENERATE" if oracle.entropy_flag else "ORACLE_NOT_DEGENERATE"],
              "oracle_entropy_drop": oracle.entropy_drop if oracle is not None else None,
              "limitation": "Relative to this saved baseline and historical entropy threshold only; not a detector validation."}
        try:
            pairs = pair_rows(report.records, comparison)
        except PairingError:
            pairs = []
        metrics = next((m for m in report.comparison_metrics if m.comparison_id == comparison.comparison_id
                        and m.answer_basis == "stored"), None)
        changed = {p.baseline.item_id for p in pairs if
                   (answer_of(p.baseline, "stored") == p.baseline.gold) !=
                   (answer_of(p.target, "stored") == p.target.gold)}
        sufficient = bool(pairs) and metrics is not None and metrics.accuracy_drop is not None
        dominated = sufficient and len(changed) == 1 and metrics.accuracy_drop != 0
        item_id = next(iter(changed)) if dominated else None
        influence = next((i for i in report.item_influence if i.comparison_id == comparison.comparison_id
                          and i.item_id == item_id and i.answer_basis == "stored"), None)
        g3 = {"status": "INSUFFICIENT_DATA" if not sufficient else "FLAGGED" if dominated else "CLEAR",
              "codes": ["INSUFFICIENT_DATA" if not sufficient else "ITEM_DOMINATED" if dominated else
                        "NO_SINGLE_ITEM_ACCURACY_DOMINANCE"],
              "item_id": item_id, "changed_correctness_items": len(changed),
              "accuracy_drop": float(metrics.accuracy_drop) if sufficient else None,
              "without_accuracy_drop": float(influence.without_accuracy_drop)
              if influence is not None and influence.without_accuracy_drop is not None else None,
              "limitation": "Exact single-item correctness-change diagnostic only. Does not rule out other influence, dependence, or small-sample risks."}
        gates = {"G0": g0, "G1": g1, "G2": g2, "G3": g3}
        gates["G4"] = {"status": "NOT_ESTABLISHED", "codes": ["BEHAVIORAL_CLAIM_NOT_ESTABLISHED"],
                       "engineering_only": True,
                       "unresolved_gates": [key for key, value in gates.items() if value["status"] != "CLEAR"],
                       "limitation": "Passing engineering diagnostics cannot establish a behavioral claim. Human interpretation and independent evidence remain required."}
        results.append({"comparison_id": comparison.comparison_id, "scope": scope,
                        "answer_basis": "stored", "gates": gates})
    return results
