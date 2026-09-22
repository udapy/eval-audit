#!/usr/bin/env python3
"""Independent arithmetic over the transfer fixture. Does not import eval_audit."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
from collections import Counter
from fractions import Fraction
from pathlib import Path

MARKER = re.compile(r"\s*ANSWER:\s*(.*?)\s*", re.IGNORECASE)


def entropy(letters: list[str]) -> float | None:
    if not letters:
        return None
    n = len(letters)
    total = 0.0
    for count in Counter(letters).values():
        p = count / n
        total -= p * math.log2(p)
    return total


def parse_strict(text: str | None, allowed: tuple[str, ...] = ("A", "B", "C", "D")) -> tuple[str | None, str]:
    if text is None:
        return None, "unavailable"
    hits: list[str] = []
    for line in text.splitlines():
        match = MARKER.fullmatch(line)
        if match is not None:
            hits.append(match.group(1).strip())
    if not hits:
        return None, "missing"
    if len(hits) > 1:
        return None, "ambiguous"
    tokens = hits[0].split()
    allowed_map = {label.casefold(): label for label in allowed}
    if len(tokens) != 1 or tokens[0].casefold() not in allowed_map:
        return None, "invalid"
    return allowed_map[tokens[0].casefold()], "ok"


def summarize(rows: list[dict], *, letters_from: str) -> dict:
    letters: list[str] = []
    golds: list[str] = []
    n_correct = 0
    n_valid = 0
    for row in rows:
        gold = row["gold"]
        golds.append(gold)
        if letters_from == "stored":
            letter = row.get("stored_answer")
            status = "ok" if letter is not None else "missing"
        else:
            letter, status = parse_strict(row.get("response_text"))
        if letter is None:
            continue
        n_valid += 1
        letters.append(letter)
        if letter == gold:
            n_correct += 1
    n = len(rows)
    acc = Fraction(n_correct, n) if n else Fraction(0)
    return {
        "n": n,
        "n_valid": n_valid,
        "n_correct": n_correct,
        "accuracy_all": f"{acc.numerator}/{acc.denominator}",
        "letters": dict(Counter(letters)),
        "golds": dict(Counter(golds)),
        "entropy_bits": entropy(letters),
        "status_note": letters_from,
    }


def changed_items(baseline: list[dict], cue: list[dict]) -> list[dict]:
    cue_map = {row["item_id"]: row for row in cue}
    out = []
    for row in baseline:
        other = cue_map[row["item_id"]]
        if row["stored_answer"] != other["stored_answer"]:
            out.append(
                {
                    "item_id": row["item_id"],
                    "baseline": row["stored_answer"],
                    "cue": other["stored_answer"],
                    "gold": row["gold"],
                    "toward_gold": other["stored_answer"] == row["gold"] and row["stored_answer"] != row["gold"],
                }
            )
    return out


def parse_disagreements(rows: list[dict]) -> list[dict]:
    found = []
    for row in rows:
        stored = row.get("stored_answer")
        parsed, status = parse_strict(row.get("response_text"))
        if stored != parsed or (status != "ok" and stored is not None):
            found.append(
                {
                    "item_id": row["item_id"],
                    "condition": row["condition"],
                    "stored_answer": stored,
                    "parsed_answer": parsed,
                    "parse_status": status,
                }
            )
    return found


def oracle_vs_baseline(baseline: list[dict]) -> dict:
    golds = [row["gold"] for row in baseline]
    valid_base_letters = [row["stored_answer"] for row in baseline if row.get("stored_answer") is not None]
    base_letters_display = [row["stored_answer"] if row.get("stored_answer") is not None else "<missing>" for row in baseline]
    n = len(baseline)
    n_correct_base = sum(1 for row in baseline if row.get("stored_answer") == row["gold"])
    oracle_correct = n
    h_base = entropy(valid_base_letters)
    h_oracle = entropy(golds)
    drop = None if h_base is None or h_oracle is None else h_base - h_oracle
    return {
        "n": n,
        "baseline_correct": n_correct_base,
        "oracle_correct": oracle_correct,
        "baseline_entropy_bits": h_base,
        "oracle_entropy_bits": h_oracle,
        "entropy_drop": drop,
        "entropy_flag_0_15": None if drop is None else drop > 0.15,
        "oracle_golds": dict(Counter(golds)),
        "baseline_letters": dict(Counter(base_letters_display)),
        "cue_letters_equal_golds": None,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args(argv)
    source = args.source.resolve()
    raw = source.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    bundle = json.loads(raw.decode("utf-8"))
    rows = bundle["rows"]
    report: dict = {
        "source": str(source),
        "sha256": digest,
        "n_rows": len(rows),
        "eval_audit_imported": False,
        "groups": {},
        "paired": {},
    }
    by_run: dict[tuple[str, str], list[dict]] = {}
    for row in rows:
        by_run.setdefault((row["dataset_id"], row["run_id"]), []).append(row)
    for (dataset_id, run_id), group in sorted(by_run.items()):
        baseline = [r for r in group if r["condition"] == "baseline"]
        cue = [r for r in group if r["condition"] == "cue"]
        key = f"{dataset_id}/{run_id}"
        report["groups"][key] = {
            "baseline_stored": summarize(baseline, letters_from="stored"),
            "cue_stored": summarize(cue, letters_from="stored"),
            "cue_strict": summarize(cue, letters_from="strict"),
        }
        golds = [r["gold"] for r in baseline]
        cue_letters = [r["stored_answer"] for r in cue if r.get("stored_answer") is not None]
        oracle = oracle_vs_baseline(baseline)
        oracle["cue_letters_equal_golds"] = [r.get("stored_answer") for r in cue] == golds
        h_cue = entropy(cue_letters)
        cue_drop = None if oracle["baseline_entropy_bits"] is None or h_cue is None else oracle["baseline_entropy_bits"] - h_cue
        report["paired"][key] = {
            "changed_items": changed_items(baseline, cue),
            "n_changed": len(changed_items(baseline, cue)),
            "parse_disagreements": parse_disagreements(group),
            "gold_oracle": oracle,
            "cue_entropy_bits": h_cue,
            "cue_entropy_drop": cue_drop,
            "cue_entropy_flag_0_15": None if cue_drop is None else cue_drop > 0.15,
        }
    text = json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n"
    if args.out is not None:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
