#!/usr/bin/env python3
"""Step 0: Pre-registration key distribution analysis.

Downloads MMLU and ARC-Challenge test sets via HF Hub Parquet API
and computes gold key distributions for pre-registered predictions.

Uses parquet endpoint (one call per subject, more efficient) with rate limiting.
Zero eval_audit imports. Stdlib only + urllib for HF Hub API.
"""

from __future__ import annotations

import json
import math
import os
import sys
import time
import urllib.request
from collections import Counter
from pathlib import Path
from typing import Any


HF_TOKEN = os.environ.get("HF_TOKEN", "")
DELAY = 1.5  # seconds between requests to avoid rate limiting


def hf_get(url: str, retries: int = 3) -> Any:
    """GET from HF API with retry and rate limit handling."""
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url)
            if HF_TOKEN:
                req.add_header("Authorization", f"Bearer {HF_TOKEN}")
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < retries - 1:
                wait = (attempt + 1) * 10
                print(f"    Rate limited, waiting {wait}s...", file=sys.stderr)
                time.sleep(wait)
            elif e.code == 422 and attempt < retries - 1:
                time.sleep(DELAY)
            else:
                raise
    return None


def shannon_entropy(counts: dict[str, int]) -> float:
    """Shannon entropy in bits."""
    total = sum(counts.values())
    if total == 0:
        return 0.0
    entropy = 0.0
    for count in counts.values():
        if count > 0:
            p = count / total
            entropy -= p * math.log2(p)
    return entropy


def uniform_entropy(n_options: int) -> float:
    return math.log2(n_options)


def skew_score(counts: dict[str, int], n_options: int = 4) -> float:
    """1 - (actual_entropy / uniform_entropy). Higher = more skewed."""
    h = shannon_entropy(counts)
    h_max = uniform_entropy(n_options)
    if h_max == 0:
        return 0.0
    return 1.0 - (h / h_max)


def gold_oracle_entropy_drop(counts: dict[str, int]) -> float:
    """Compute entropy drop if a gold-oracle answerer perfectly follows gold keys.
    
    Baseline entropy is approximated as uniform (2.0 bits for 4 options).
    Oracle entropy = shannon_entropy(gold_counts).
    Drop = uniform - oracle.
    Positive means oracle entropy is lower (more concentrated).
    """
    h_oracle = shannon_entropy(counts)
    h_uniform = uniform_entropy(len(counts)) if len(counts) > 0 else 2.0
    return h_uniform - h_oracle


# ── MMLU ──

MMLU_SUBJECTS = [
    "abstract_algebra", "anatomy", "astronomy", "business_ethics",
    "clinical_knowledge", "college_biology", "college_chemistry",
    "college_computer_science", "college_mathematics", "college_medicine",
    "college_physics", "computer_security", "conceptual_physics",
    "econometrics", "electrical_engineering", "elementary_mathematics",
    "formal_logic", "global_facts", "high_school_biology",
    "high_school_chemistry", "high_school_computer_science",
    "high_school_european_history", "high_school_geography",
    "high_school_government_and_politics", "high_school_macroeconomics",
    "high_school_mathematics", "high_school_microeconomics",
    "high_school_physics", "high_school_psychology",
    "high_school_statistics", "high_school_us_history",
    "high_school_world_history", "human_aging", "human_sexuality",
    "international_law", "jurisprudence", "logical_fallacies",
    "machine_learning", "management", "marketing", "medical_genetics",
    "miscellahistoricalus", "moral_disputes", "moral_scenarios",
    "nutrition", "philosophy", "prehistory", "professional_accounting",
    "professional_law", "professional_medicine", "professional_psychology",
    "public_relations", "security_studies", "sociology",
    "us_foreign_policy", "virology", "world_religions",
]

ANSWER_MAP = {0: "A", 1: "B", 2: "C", 3: "D"}


def fetch_mmlu_rows(subject: str, split: str = "test") -> list[dict[str, Any]]:
    """Fetch MMLU rows for a subject (first 100 test items)."""
    url = (
        f"https://datasets-server.huggingface.co/rows"
        f"?dataset=cais/mmlu&config={subject}&split={split}&offset=0&length=100"
    )
    data = hf_get(url)
    if data is None:
        return []
    return [row["row"] for row in data.get("rows", [])]


def mmlu_gold_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    """Extract gold key distribution from MMLU rows."""
    counts: Counter[str] = Counter()
    for row in rows:
        answer = row.get("answer")
        if isinstance(answer, int):
            answer = ANSWER_MAP.get(answer, str(answer))
        elif isinstance(answer, str) and len(answer) == 1 and answer.isdigit():
            answer = ANSWER_MAP.get(int(answer), answer)
        counts[str(answer)] += 1
    return dict(sorted(counts.items()))


# ── ARC-Challenge ──

def fetch_arc_rows(split: str = "test", max_pages: int = 5) -> list[dict[str, Any]]:
    all_rows = []
    for page in range(max_pages):
        offset = page * 100
        url = (
            f"https://datasets-server.huggingface.co/rows"
            f"?dataset=allenai/ai2_arc&config=ARC-Challenge&split={split}&offset={offset}&length=100"
        )
        data = hf_get(url)
        if not data or not data.get("rows"):
            break
        rows = [row["row"] for row in data["rows"]]
        all_rows.extend(rows)
        if len(rows) < 100:
            break
        time.sleep(0.5)
    return all_rows


def arc_gold_counts(rows: list[dict[str, Any]]) -> tuple[dict[str, int], int, int]:
    """Extract gold key distribution from ARC-Challenge, filtering to 4-option items."""
    counts: Counter[str] = Counter()
    n_four = 0
    for row in rows:
        choices = row.get("choices", {})
        labels = choices.get("label", [])
        if len(labels) != 4:
            continue
        n_four += 1
        answer = row.get("answerKey", "")
        counts[str(answer)] += 1
    return dict(sorted(counts.items())), n_four, len(rows)


def main() -> None:
    print("=" * 72)
    print("STEP 0: PRE-REGISTRATION KEY DISTRIBUTION ANALYSIS")
    print("=" * 72)
    print()

    results: list[dict[str, Any]] = []

    # ── MMLU subjects (with rate limiting) ──
    print("Fetching MMLU subjects (with 1.5s delay between requests)...")
    for i, subject in enumerate(MMLU_SUBJECTS):
        if i > 0:
            time.sleep(DELAY)
        try:
            rows = fetch_mmlu_rows(subject)
            counts = mmlu_gold_counts(rows)
            n = len(rows)
            h = shannon_entropy(counts)
            s = skew_score(counts)
            oracle_drop = gold_oracle_entropy_drop(counts)
            results.append({
                "subject": subject,
                "counts": counts,
                "n": n,
                "entropy": round(h, 6),
                "skew": round(s, 6),
                "oracle_drop": round(oracle_drop, 6),
            })
            max_key = max(counts, key=counts.get) if counts else "?"
            max_pct = counts.get(max_key, 0) / n * 100 if n else 0
            print(f"  [{i+1:2d}/57] {subject:45s}  n={n:3d}  {counts}  H={h:.4f}  skew={s:.4f}  oracle_drop={oracle_drop:.4f}")
        except Exception as e:
            print(f"  [{i+1:2d}/57] {subject:45s}  ERROR: {e}", file=sys.stderr)

    # Sort by skew
    results.sort(key=lambda x: x["skew"], reverse=True)

    print()
    print("=" * 72)
    print("TOP 10 MOST SKEWED MMLU SUBJECTS (best candidates for Exp 2)")
    print("=" * 72)
    for r in results[:10]:
        max_key = max(r["counts"], key=r["counts"].get) if r["counts"] else "?"
        max_pct = r["counts"].get(max_key, 0) / r["n"] * 100 if r["n"] else 0
        flag = "YES" if r["oracle_drop"] > 0.15 else "no"
        print(f"  {r['subject']:45s}  n={r['n']:3d}  skew={r['skew']:.4f}  dominant={max_key}({max_pct:.1f}%)  oracle_flag={flag}  drop={r['oracle_drop']:.4f}")

    print()
    print("MOST BALANCED (for reference):")
    for r in results[-5:]:
        print(f"  {r['subject']:45s}  n={r['n']:3d}  skew={r['skew']:.4f}  drop={r['oracle_drop']:.4f}")

    # ── ARC-Challenge ──
    print()
    print("=" * 72)
    print("ARC-CHALLENGE TEST SET")
    print("=" * 72)
    time.sleep(DELAY)
    arc_counts: dict[str, int] = {}
    arc_n_four = 0
    arc_n_total = 0
    arc_h = 0.0
    arc_s = 0.0
    arc_oracle_drop = 0.0
    try:
        arc_rows = fetch_arc_rows()
        arc_counts, arc_n_four, arc_n_total = arc_gold_counts(arc_rows)
        arc_h = shannon_entropy(arc_counts)
        arc_s = skew_score(arc_counts)
        arc_oracle_drop = gold_oracle_entropy_drop(arc_counts)
        print(f"  Total items: {arc_n_total}")
        print(f"  4-option items: {arc_n_four}")
        print(f"  Gold key counts: {arc_counts}")
        print(f"  Shannon entropy: {arc_h:.4f} bits (uniform = {uniform_entropy(4):.4f})")
        print(f"  Skew score: {arc_s:.4f}")
        print(f"  Gold-oracle entropy drop: {arc_oracle_drop:.4f} (flag threshold = 0.15)")
    except Exception as e:
        print(f"  ERROR: {e}", file=sys.stderr)

    # ── Pre-registration summary ──
    print()
    print("=" * 72)
    print("PRE-REGISTRATION PREDICTIONS")
    print("=" * 72)

    if results:
        # Find our existing balanced subjects
        balanced_subjects = [r for r in results if r["subject"] in ("computer_security", "elementary_mathematics")]
        skewed = results[0]

        if balanced_subjects:
            for b in balanced_subjects:
                flag = "YES" if b["oracle_drop"] > 0.15 else "NO"
                print(f"\n  Exp 1 candidate: {b['subject']}")
                print(f"    n={b['n']}, keys={b['counts']}, H={b['entropy']:.4f}")
                print(f"    Oracle entropy drop = {b['oracle_drop']:.4f}")
                print(f"    Would G2 flag fire? {flag}")

        print(f"\n  Exp 2 (SKEWED): {skewed['subject']}")
        print(f"    n={skewed['n']}, keys={skewed['counts']}, H={skewed['entropy']:.4f}")
        print(f"    Oracle entropy drop = {skewed['oracle_drop']:.4f}")
        flag = "YES" if skewed["oracle_drop"] > 0.15 else "NO"
        print(f"    Would G2 flag fire? {flag}")
        print(f"    >>> PREDICTION: entropy_flag = true under answer-key leak")

    if arc_n_four > 0:
        flag = "YES" if arc_oracle_drop > 0.15 else "NO"
        print(f"\n  Exp 3 (ARC-Challenge): {arc_n_four} 4-option items")
        print(f"    keys={arc_counts}, H={arc_h:.4f}, skew={arc_s:.4f}")
        print(f"    Oracle entropy drop = {arc_oracle_drop:.4f}")
        print(f"    Would G2 flag fire? {flag}")
        if arc_oracle_drop > 0.15:
            print(f"    >>> PREDICTION: entropy_flag = true under answer-key leak")
        else:
            print(f"    >>> PREDICTION: entropy_flag = false under answer-key leak")

    # ── Save JSON ──
    output = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "mmlu_subjects": results,
        "recommended_skewed": results[0]["subject"] if results else None,
        "arc_challenge": {
            "counts": arc_counts,
            "n_four_option": arc_n_four,
            "n_total": arc_n_total,
            "entropy": round(arc_h, 6),
            "skew": round(arc_s, 6),
            "oracle_drop": round(arc_oracle_drop, 6),
        },
    }

    out_path = Path(__file__).resolve().parent.parent.parent / "audit" / "artifacts" / "key_distributions.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n")
    print(f"\n  Saved distributions to {out_path}")


if __name__ == "__main__":
    main()
