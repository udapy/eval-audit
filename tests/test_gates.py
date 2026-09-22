"""Synthetic conformance cases; these are engineering tests, not held-out evidence."""
from dataclasses import replace

import pytest

from eval_audit.gates import evaluate_gates
from eval_audit.metrics import pair_rows
from eval_audit.report import build_report
from eval_audit.schema import Comparison, PairingError
from tests.helpers import pair_set
from tests.test_checks import _manifest


def fixture(kind):
    golds = {str(i): label for i, label in enumerate("ABCD")}
    baseline = dict(golds)
    target = dict(golds)
    if kind == "skewed":
        golds = dict(zip(golds, "BBBC"))
        target = dict(golds)
    if kind == "single":
        target["0"] = "B"
    rows = pair_set(golds, baseline, target)
    comparison = Comparison("R", "syn", "synthetic", "R", "baseline", "cue")
    manifest = _manifest(comparison)
    if kind == "truncated":
        rows[0] = replace(rows[0], response_completeness="truncated", parsed_answer=None,
                          parse_status="missing", response_text="reasoning cut off")
    if kind == "duplicate":
        manifest = replace(manifest, artifacts=manifest.artifacts +
                           (replace(manifest.artifacts[0], artifact_id="COPY"),))
    if kind == "key_mismatch":
        rows = [replace(r, option_order=("b", "a", "c", "d"),
                        gold_content_id=r.gold.lower()) for r in rows]
    return rows, manifest


@pytest.mark.parametrize(("kind", "gate", "code"), [
    ("balanced", "G2", "ORACLE_NOT_DEGENERATE"),
    ("skewed", "G2", "ORACLE_DEGENERATE"),
    ("single", "G3", "ITEM_DOMINATED"),
    ("truncated", "G1", "PARSER_SENSITIVE"),
    ("duplicate", "G0", "DUPLICATE_ARTIFACT"),
    ("key_mismatch", "G1", "OPTION_ORDER_KEY_MISMATCH"),
])
def test_engineering_gate_cases(kind, gate, code):
    rows, manifest = fixture(kind)
    gates = evaluate_gates(build_report(rows, manifest))[0]["gates"]
    assert code in gates[gate]["codes"]
    assert gates["G4"]["status"] == "NOT_ESTABLISHED"
    if kind == "single":
        assert gates["G3"]["item_id"] == "0"
        assert gates["G3"]["accuracy_drop"] == pytest.approx(0.25, abs=1e-12)
        assert gates["G3"]["without_accuracy_drop"] == pytest.approx(0, abs=1e-12)


def test_missing_pair_cannot_pass_gates():
    rows, manifest = fixture("balanced")
    gates = evaluate_gates(build_report(rows[:-1], manifest))[0]["gates"]
    assert gates["G2"]["status"] == "INSUFFICIENT_DATA"
    assert gates["G3"]["status"] == "INSUFFICIENT_DATA"


def test_empty_comparison_cannot_pass_gates():
    _, manifest = fixture("balanced")
    gates = evaluate_gates(build_report([], manifest))[0]["gates"]
    assert all(gates[g]["status"] == "INSUFFICIENT_DATA" for g in ("G0", "G1", "G2", "G3"))


def test_option_order_absence_is_explicitly_unassessed():
    rows, manifest = fixture("balanced")
    gate = evaluate_gates(build_report(rows, manifest))[0]["gates"]["G1"]
    assert "OPTION_ORDER_UNAVAILABLE" in gate["codes"]
    assert gate["status"] == "NOT_ASSESSED"


def test_paired_options_must_match_even_when_gold_letters_match():
    rows, manifest = fixture("balanced")
    rows[0] = replace(rows[0], option_order=("a", "b", "c", "d"), gold_content_id="a")
    with pytest.raises(PairingError, match="option_order mismatch"):
        pair_rows(rows, manifest.comparisons[0])
