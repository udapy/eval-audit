"""Conformance suite: Formal verification of Claim-Integrity Gates G0-G4.

Tests C01 through C08 verify that audit gates reliably catch failure classes
and do not silently pass invalid or degenerate evaluation artifacts.
"""

from __future__ import annotations

from fractions import Fraction
from pathlib import Path
import pytest

from eval_audit.checks import comparison_bundle, run_checks
from eval_audit.io import dump_json, sha256_bytes
from eval_audit.schema import (
    SCHEMA_VERSION,
    Artifact,
    Comparison,
    ItemContext,
    Manifest,
    PairingError,
    Record,
    SourceRef,
)
from tests.helpers import make_annotation, make_record, pair_set

DUMMY_SHA = "a" * 64
DUMMY_SHA_2 = "b" * 64


def _build_manifest(
    comparison: Comparison,
    artifacts: tuple[Artifact, ...] | None = None,
    profile: str = "generic-v1",
) -> Manifest:
    if artifacts is None:
        artifacts = (Artifact("art_1", "raw.json", "raw.json", DUMMY_SHA, 100, {"origin": "test"}),)
    return Manifest(
        schema_version=SCHEMA_VERSION,
        adapter_version="1",
        profile=profile,
        artifacts=artifacts,
        normalized_file="norm.jsonl",
        normalized_sha256=DUMMY_SHA,
        comparisons=(comparison,),
        provenance_notes=("conformance test",),
    )


def test_c01_clean_balanced_all_gates_pass() -> None:
    """C01: Uniform keys, clean parsing, balanced responses pass all gates cleanly."""
    golds = {"i1": "A", "i2": "B", "i3": "C", "i4": "D"}
    rows = pair_set(golds, golds, golds, dataset_id="c01-clean", run_id="RUN_C01")
    comparison = Comparison("C01", "c01-clean", "synthetic", "RUN_C01", "baseline", "cue")
    manifest = _build_manifest(comparison)

    comp_metrics, controls, influence, statuses, comp_findings = comparison_bundle(rows, manifest)
    run_findings = run_checks(rows, manifest)

    assert statuses["C01"] == "complete"
    # Gate G2: Oracle does not flag on balanced keys
    oracle = next(c for c in controls if c.control_id == "gold_oracle")
    assert oracle.metrics.entropy_flag is False
    assert not any(f.code == "CONTROL_ORACLE_ENTROPY_FLAG" for f in comp_findings)

    # Gate G1: No parse disagreements or truncation notes
    assert not any(f.code == "STORED_STRICT_DISAGREEMENT" for f in run_findings)
    assert not any(f.code == "PROVENANCE_TRUNCATION" for f in run_findings)

    # Gate G0: No duplicate artifacts
    assert not any(f.code == "DUPLICATE_ARTIFACT" for f in run_findings)


def test_c02_skewed_keys_oracle_trips_gate_g2() -> None:
    """C02: Heavily skewed gold distribution causes gold oracle to trip entropy heuristic."""
    # Golds are skewed (9 B, 1 C)
    golds = {f"k{i}": "B" for i in range(1, 10)}
    golds["k10"] = "C"
    # Baseline responses are uniform/varied across choices (A/B/C/D)
    letters = ["A", "B", "C", "D"]
    baseline = {f"k{i}": letters[i % 4] for i in range(1, 11)}
    # Cue target condition
    target = {f"k{i}": "B" for i in range(1, 10)}
    target["k10"] = "C"

    rows = pair_set(golds, baseline, target, dataset_id="c02-skew", run_id="RUN_C02")
    comparison = Comparison("C02", "c02-skew", "synthetic", "RUN_C02", "baseline", "cue")
    manifest = _build_manifest(comparison)

    _, controls, _, _, comp_findings = comparison_bundle(rows, manifest)
    run_findings = run_checks(rows, manifest)

    # Gate G2 trips: oracle drop from varied baseline to concentrated gold key exceeds 0.15
    oracle = next(c for c in controls if c.control_id == "gold_oracle")
    assert any(f.code == "CONTROL_ORACLE_ENTROPY_FLAG" for f in comp_findings)
    gold_dist = next(f for f in run_findings if f.code == "GOLD_DISTRIBUTION")
    assert gold_dist.observed["gold_counts"]["B"] == 9


def test_c03_single_item_collapse_gate_g3() -> None:
    """C03: Single item drives 100% of paired accuracy change; LOO reveals zero residual."""
    golds = {f"item_{i}": "A" for i in range(1, 11)}
    # Baseline has item_1 wrong (B instead of A), all others correct
    baseline = {f"item_{i}": "A" for i in range(1, 11)}
    baseline["item_1"] = "B"
    # Target condition has all items correct
    target = {f"item_{i}": "A" for i in range(1, 11)}

    rows = pair_set(golds, baseline, target, dataset_id="c03-influence", run_id="RUN_C03")
    comparison = Comparison("C03", "c03-influence", "synthetic", "RUN_C03", "baseline", "cue")
    manifest = _build_manifest(comparison)

    comp_metrics, _, influence, _, _ = comparison_bundle(rows, manifest)
    stored_metric = next(m for m in comp_metrics if m.answer_basis == "stored")

    # Overall paired accuracy difference is -1/10 (improved by 1/10)
    assert stored_metric.accuracy_drop == Fraction(-1, 10)

    # Gate G3: Leave-one-out for item_1 must drop the delta to 0.0
    item1_loo = next(inf for inf in influence if inf.item_id == "item_1")
    assert item1_loo.without_accuracy_drop == Fraction(0, 1)

    # Any other item left out still preserves the -1/9 delta
    item2_loo = next(inf for inf in influence if inf.item_id == "item_2")
    assert item2_loo.without_accuracy_drop == Fraction(-1, 9)


def test_c04_truncation_divergence_gate_g1() -> None:
    """C04: Truncated response text causes strict parse divergence and flags truncation risk."""
    rows = [
        make_record(item_id="t1", gold="A", stored="A", text="Model began thinking but cut off...", completeness="possibly_truncated"),
        make_record(item_id="t1", condition="cue", gold="A", stored="A", text="ANSWER: A", completeness="complete"),
        make_record(item_id="t2", gold="B", stored="B", text="ANSWER: B", completeness="complete"),
        make_record(item_id="t2", condition="cue", gold="B", stored="B", text="ANSWER: B", completeness="complete"),
    ]
    comparison = Comparison("C04", "syn", "synthetic", "R", "baseline", "cue")
    manifest = _build_manifest(comparison)

    run_findings = run_checks(rows, manifest)
    codes = {f.code for f in run_findings}
    assert "STORED_STRICT_DISAGREEMENT" in codes
    assert "PROVENANCE_TRUNCATION" in codes


def test_c05_score_mutation_attack_prevented() -> None:
    """C05: Non-scoring human annotation cannot alter recorded answers or scores."""
    golds = {"m1": "A", "m2": "B"}
    rows = pair_set(golds, golds, golds, dataset_id="c05-mutation", run_id="RUN_C05")
    comparison = Comparison("C05", "c05-mutation", "synthetic", "RUN_C05", "baseline", "cue")
    manifest = _build_manifest(comparison)

    metrics_before, _, _, _, _ = comparison_bundle(rows, manifest)

    # Attack annotation attempting to label m1 as invalid-key
    ann = make_annotation(annotation_id="ann_attack", dataset_id="c05-mutation", item_id="m1", gold_uniqueness="invalid-key")
    findings = run_checks(rows, manifest, annotations=[ann])

    metrics_after, _, _, _, _ = comparison_bundle(rows, manifest)

    # Scores and stored values are strictly invariant
    assert metrics_before == metrics_after
    assert any(f.code == "HUMAN_ANNOTATION" and f.severity == "warning" for f in findings)
    assert rows[0].gold == "A"
    assert rows[0].stored_answer == "A"


def test_c06_broken_pairing_gate_g0_g3() -> None:
    """C06: Missing target row raises PairingError and marks comparison invalid."""
    golds = {"p1": "A", "p2": "B"}
    # p2 is missing in cue condition
    rows = [
        make_record(item_id="p1", condition="baseline", gold="A", stored="A"),
        make_record(item_id="p1", condition="cue", gold="A", stored="A"),
        make_record(item_id="p2", condition="baseline", gold="B", stored="B"),
    ]
    comparison = Comparison("C06", "syn", "synthetic", "R", "baseline", "cue")
    manifest = _build_manifest(comparison)

    _, _, _, statuses, comp_findings = comparison_bundle(rows, manifest)
    assert statuses["C06"] == "invalid"
    assert any(f.code == "PAIRING_INVALID" for f in comp_findings)


def test_c07_duplicate_artifact_gate_g0() -> None:
    """C07: Duplicate byte hashes across distinct artifact IDs trigger DUPLICATE_ARTIFACT."""
    comparison = Comparison("C07", "syn", "synthetic", "R", "baseline", "cue")
    art1 = Artifact("artifact_primary", "runs/run1.json", "runs/run1.json", DUMMY_SHA, 1234, {})
    art2 = Artifact("artifact_alias", "copies/run1_copy.json", "copies/run1_copy.json", DUMMY_SHA, 1234, {})
    manifest = _build_manifest(comparison, artifacts=(art1, art2))

    golds = {"d1": "A"}
    rows = pair_set(golds, golds, golds, dataset_id="syn", run_id="R")

    findings = run_checks(rows, manifest)
    dup_finding = next((f for f in findings if f.code == "DUPLICATE_ARTIFACT"), None)
    assert dup_finding is not None
    assert dup_finding.observed["sha256"] == DUMMY_SHA
    assert dup_finding.observed["artifact_ids"] == ["artifact_alias", "artifact_primary"]


def test_c08_option_order_mismatch_gate_g1() -> None:
    """C08: Shuffled option order with unupdated gold index triggers OPTION_ORDER_KEY_MISMATCH."""
    comparison = Comparison("C08", "syn", "synthetic", "R", "baseline", "cue")
    manifest = _build_manifest(comparison)

    # Gold letter is 'A' (index 0). Option order says index 0 is content 'opt_2',
    # but declared gold_content_id is 'opt_1'.
    record = make_record(
        item_id="o1",
        gold="A",
        stored="A",
        option_order=("opt_2", "opt_1", "opt_3", "opt_4"),
        gold_content_id="opt_1",
    )

    findings = run_checks([record], manifest)
    mismatch = next((f for f in findings if f.code == "OPTION_ORDER_KEY_MISMATCH"), None)
    assert mismatch is not None
    assert mismatch.observed["stored_gold"] == "A"
    assert mismatch.observed["content_at_gold"] == "opt_2"
    assert mismatch.observed["gold_content_id"] == "opt_1"
