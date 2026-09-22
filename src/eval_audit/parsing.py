"""Strict v1 answer parser. Conservative on purpose; stored labels stay separate."""

from __future__ import annotations

import re

from eval_audit.schema import ParseResult

_MARKER = re.compile(r"\s*ANSWER:\s*(.*?)\s*", re.IGNORECASE)


def parse_answer(text: str | None, allowed: tuple[str, ...]) -> ParseResult:
    """Parse exactly one standalone ``ANSWER: X`` line.

    - ``None`` text → ``unavailable``
    - no marker line → ``missing``
    - two or more marker lines → ``ambiguous`` even if the answers match
    - one marker whose payload is not exactly one allowed label → ``invalid``
    """
    if text is None:
        return ParseResult(answer=None, status="unavailable")
    if not allowed:
        return ParseResult(answer=None, status="invalid")

    allowed_map = {label.casefold(): label for label in allowed}
    hits: list[str] = []
    for line in text.splitlines():
        match = _MARKER.fullmatch(line)
        if match is not None:
            hits.append(match.group(1).strip())

    if not hits:
        return ParseResult(answer=None, status="missing")
    if len(hits) > 1:
        return ParseResult(answer=None, status="ambiguous")

    tokens = hits[0].split()
    if len(tokens) != 1:
        return ParseResult(answer=None, status="invalid")
    label = allowed_map.get(tokens[0].casefold())
    if label is None:
        return ParseResult(answer=None, status="invalid")
    return ParseResult(answer=label, status="ok")
