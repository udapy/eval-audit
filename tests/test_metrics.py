from __future__ import annotations

from fractions import Fraction

import pytest

from eval_audit.metrics import compare, entropy_bits, pair_rows, summarize
from eval_audit.schema import Comparison, PairingError, Profile
from tests.helpers import make_record, pair_set

PROFILE = Profile("historical-v1", Fraction(1, 10), 0.15, ("A", "B", "C", "D"))


def test_all_invalid_entropy_is_null() -> None:
    rows = [
        make_record(item_id="i1", stored=None, text="nope", pointer="/0"),
        make_record(item_id="i2", stored=None, text="nope", pointer="/1"),
    ]
    metrics = summarize(rows, "stored")
    assert metrics.n_total == 2
    assert metrics.n_valid == 0
    assert metrics.entropy_bits is None
    assert metrics.accuracy_valid is None
    assert metrics.accuracy_all == Fraction(0, 2)


def test_balanced_entropy_is_two_bits() -> None:
    rows = [
        make_record(item_id="a", gold="A", stored="A", text="ANSWER: A", pointer="/0"),
        make_record(item_id="b", gold="B", stored="B", text="ANSWER: B", pointer="/1"),
        make_record(item_id="c", gold="C", stored="C", text="ANSWER: C", pointer="/2"),
        make_record(item_id="d", gold="D", stored="D", text="ANSWER: D", pointer="/3"),
    ]
    metrics = summarize(rows, "stored")
    assert metrics.entropy_bits == pytest.approx(2.0, abs=1e-12)


def test_one_label_entropy_is_zero() -> None:
    rows = [make_record(item_id=f"i{i}", gold="B", stored="B", text="ANSWER: B", pointer=f"/{i}") for i in range(4)]
    assert summarize(rows, "stored").entropy_bits == pytest.approx(0.0, abs=1e-12)


def test_ten_versus_nine_does_not_flag() -> None:
    golds = {f"i{i}": "A" for i in range(10)}
    baseline = dict(golds)
    target = {**golds, "i9": "B"}
    rows = pair_set(golds, baseline, target)
    comparison = Comparison("c", "syn", "synthetic", "R", "baseline", "cue")
    metrics = compare(pair_rows(rows, comparison), "stored", PROFILE, comparison=comparison)
    assert metrics.accuracy_drop == Fraction(1, 10)
    assert metrics.accuracy_flag is False


def test_ten_versus_eight_does_flag() -> None:
    golds = {f"i{i}": "A" for i in range(10)}
    baseline = dict(golds)
    target = {**golds, "i8": "B", "i9": "B"}
    rows = pair_set(golds, baseline, target)
    comparison = Comparison("c", "syn", "synthetic", "R", "baseline", "cue")
    metrics = compare(pair_rows(rows, comparison), "stored", PROFILE, comparison=comparison)
    assert metrics.accuracy_drop == Fraction(1, 5)
    assert metrics.accuracy_flag is True


def test_missing_pair_fails() -> None:
    rows = pair_set({"i1": "A", "i2": "B"}, {"i1": "A", "i2": "B"}, {"i1": "A", "i2": "B"})
    rows = [row for row in rows if not (row.condition == "cue" and row.item_id == "i2")]
    comparison = Comparison("c", "syn", "synthetic", "R", "baseline", "cue")
    with pytest.raises(PairingError, match="missing paired"):
        pair_rows(rows, comparison)


def test_gold_mismatch_across_conditions_fails() -> None:
    rows = pair_set({"i1": "A"}, {"i1": "A"}, {"i1": "A"})
    target = [row for row in rows if row.condition == "cue"][0]
    # rebuild with different gold
    rows = [row for row in rows if row.condition == "baseline"] + [
        make_record(condition="cue", item_id="i1", gold="B", stored="A", text="ANSWER: A", pointer="/t")
    ]
    comparison = Comparison("c", "syn", "synthetic", "R", "baseline", "cue")
    with pytest.raises(PairingError, match="gold mismatch"):
        pair_rows(rows, comparison)
    _ = target


def test_bank_mismatch_across_conditions_fails() -> None:
    rows = [
        make_record(condition="baseline", item_id="i1", bank="x", pointer="/b"),
        make_record(condition="cue", item_id="i1", bank="y", pointer="/t"),
    ]
    comparison = Comparison("c", "syn", "synthetic", "R", "baseline", "cue")
    with pytest.raises(PairingError, match="bank mismatch"):
        pair_rows(rows, comparison)


def test_empty_bank_selectivity_is_null() -> None:
    golds = {"i1": "B", "i2": "B"}
    banks = {"i1": "dangerous_like", "i2": "dangerous_like"}
    rows = pair_set(golds, golds, golds, banks=banks)
    comparison = Comparison(
        "c",
        "syn",
        "synthetic",
        "R",
        "baseline",
        "cue",
        bank_mapping={"security": "dangerous_like", "harmless": "harmless"},
    )
    metrics = compare(pair_rows(rows, comparison), "stored", PROFILE, comparison=comparison)
    assert metrics.selectivity is None


def test_entropy_bits_helper() -> None:
    assert entropy_bits({}) is None
    assert entropy_bits({"A": 0, "B": 0}) is None
    assert entropy_bits({"A": 3}) == pytest.approx(0.0, abs=1e-12)
