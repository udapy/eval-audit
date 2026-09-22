from __future__ import annotations

from eval_audit.parsing import parse_answer


def test_single_marker() -> None:
    assert parse_answer("ANSWER: B", ("A", "B")).answer == "B"
    assert parse_answer("ANSWER: B", ("A", "B")).status == "ok"


def test_two_markers_ambiguous_even_if_identical() -> None:
    assert parse_answer("ANSWER: A\nANSWER: B", ("A", "B")).status == "ambiguous"
    assert parse_answer("ANSWER: B\nANSWER: B", ("A", "B")).status == "ambiguous"
    assert parse_answer("ANSWER: A\nANSWER: B", ("A", "B")).answer is None


def test_unknown_label_invalid() -> None:
    assert parse_answer("ANSWER: Z", ("A", "B")).status == "invalid"


def test_absent_text_unavailable() -> None:
    assert parse_answer(None, ("A", "B")).status == "unavailable"


def test_whitespace_and_case() -> None:
    result = parse_answer("  answer: b  ", ("A", "B"))
    assert result.status == "ok"
    assert result.answer == "B"


def test_extra_answer_text_invalid() -> None:
    assert parse_answer("ANSWER: B extra", ("A", "B")).status == "invalid"


def test_truncated_fragment_missing() -> None:
    assert parse_answer("A) Disk encryption ", ("A", "B", "C", "D")).status == "missing"


def test_empty_string_missing() -> None:
    assert parse_answer("", ("A", "B")).status == "missing"


def test_inline_marker_is_not_standalone() -> None:
    assert parse_answer("therefore ANSWER: B is right", ("A", "B")).status == "missing"
