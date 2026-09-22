from __future__ import annotations

import pytest

from eval_audit.schema import AuditInputError, Comparison, Record, validate_records
from tests.helpers import make_record


def test_duplicate_identity_is_fatal() -> None:
    row = make_record()
    with pytest.raises(AuditInputError, match="duplicate"):
        validate_records([row, row])


def test_invalid_gold_is_fatal() -> None:
    with pytest.raises(AuditInputError, match="gold"):
        make_record(gold="Z").validate()


def test_incompatible_alphabets_are_fatal() -> None:
    a = make_record(item_id="i1", allowed=("A", "B"))
    b = make_record(item_id="i2", allowed=("A", "B", "C", "D"), pointer="/rows/1")
    with pytest.raises(AuditInputError, match="incompatible alphabets"):
        validate_records([a, b])


def test_null_repeat_and_permutation_are_allowed() -> None:
    row = make_record(repeat_id=None, permutation_id=None)
    row.validate()
    assert row.repeat_id is None
    assert row.permutation_id is None


def test_unknown_schema_version_is_fatal() -> None:
    with pytest.raises(AuditInputError, match="schema_version"):
        make_record(schema_version=99).validate()


def test_comparison_conditions_must_differ() -> None:
    with pytest.raises(AuditInputError):
        Comparison("c", "d", "m", "r", "baseline", "baseline").validate()


def test_generic_profile_is_known() -> None:
    from eval_audit.schema import GENERIC_PROFILE, profile_by_name

    profile = profile_by_name(GENERIC_PROFILE)
    assert profile.name == "generic-v1"
    assert profile.entropy_drop_threshold == 0.15


def test_unknown_profile_is_fatal() -> None:
    from eval_audit.schema import AuditInputError, profile_by_name

    with pytest.raises(AuditInputError, match="unknown profile"):
        profile_by_name("historical-hd1-special")


def test_record_is_not_historical_hd1() -> None:
    row = make_record(item_id="x9", gold="C", stored="C")
    assert isinstance(row, Record)
    assert row.item_id != "hd1"


def test_annotation_verdict_enum() -> None:
    from eval_audit.schema import Annotation, GOLD_UNIQUENESS_VERDICTS

    assert GOLD_UNIQUENESS_VERDICTS == (
        "unique-correct",
        "contested",
        "invalid-key",
        "insufficient-evidence",
    )
    Annotation(
        "a",
        "d",
        "i",
        "rationale",
        "author",
        "reviewed",
        "human",
        "unique-correct",
    ).validate()
