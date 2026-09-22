from __future__ import annotations

import json
from pathlib import Path

import pytest

from eval_audit.loaders import extract_item_context, load_historical, read_dataset
from eval_audit.schema import AuditInputError

HISTORICAL_ROOT = Path(__import__("os").environ.get("EVAL_AUDIT_HISTORICAL_SOURCE", "/__eval_audit_source_not_configured__"))
PINNED_M1 = "db7ca948ff5b4a58d2c036b9fc2adcbd6965a6055c1b07c86694dfd517f2ae0b"


def test_import_historical_yields_88_rows(tmp_path: Path) -> None:
    if not HISTORICAL_ROOT.is_dir():
        pytest.skip("Historical source tree is not present")
    dest = tmp_path / "data"
    manifest = load_historical(HISTORICAL_ROOT, dest)
    manifest2, records = read_dataset(dest / "manifest.json")
    assert sum(a.row_count for a in manifest.artifacts) == 88
    assert len(records) == 88
    assert {a.artifact_id for a in manifest.artifacts} == {"L", "M1", "M2", "F1", "F2"}
    conditions = {(r.run_id, r.condition) for r in records}
    assert ("M1", "sandbag") in conditions
    assert ("F1", "explicit_sandbag") in conditions
    assert ("M2", "eval_cued_incentive_strong") in conditions
    assert manifest2.normalized_sha256 == manifest.normalized_sha256
    source = HISTORICAL_ROOT / "results/gpt4.1-mini-model-results/wave1_h1/wave1_MVE.json"
    from hashlib import sha256

    assert sha256(source.read_bytes()).hexdigest() == PINNED_M1

    from fractions import Fraction

    from eval_audit.metrics import compare, pair_rows, summarize
    from eval_audit.schema import profile_by_name

    profile = profile_by_name("historical-v1")
    m2_base = [r for r in records if r.run_id == "M2" and r.condition == "baseline"]
    m2_cue = [r for r in records if r.run_id == "M2" and r.condition == "eval_cued_incentive_strong"]
    assert summarize(m2_base, "stored").n_correct == 11
    assert summarize(m2_base, "stored").n_total == 12
    assert summarize(m2_cue, "stored").n_correct == 12
    assert summarize(m2_base, "stored").entropy_bits == pytest.approx(0.8166890883150209, abs=1e-12)
    assert summarize(m2_cue, "stored").entropy_bits == pytest.approx(0.41381685030363374, abs=1e-12)
    comparison = next(c for c in manifest.comparisons if c.comparison_id == "M2")
    metrics = compare(pair_rows(records, comparison), "stored", profile, comparison=comparison)
    assert metrics.selectivity == Fraction(-1, 6)
    m1_sand = [r for r in records if r.run_id == "M1" and r.condition == "sandbag"]
    assert summarize(m1_sand, "stored").n_correct == 8
    f1_sand = [r for r in records if r.run_id == "F1" and r.condition == "explicit_sandbag"]
    assert summarize(f1_sand, "stored").n_correct == 9


def test_changed_normalized_hash_is_rejected(tmp_path: Path) -> None:
    if not HISTORICAL_ROOT.is_dir():
        pytest.skip("Historical source tree is not present")
    dest = tmp_path / "data"
    load_historical(HISTORICAL_ROOT, dest)
    path = dest / "normalized.jsonl"
    path.write_text(path.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    with pytest.raises(AuditInputError, match="normalized file hash"):
        read_dataset(dest / "manifest.json")


def test_changed_raw_hash_is_rejected(tmp_path: Path) -> None:
    if not HISTORICAL_ROOT.is_dir():
        pytest.skip("Historical source tree is not present")
    dest = tmp_path / "data"
    load_historical(HISTORICAL_ROOT, dest)
    raw = dest / "raw" / "M1" / "wave1_MVE.json"
    raw.write_bytes(raw.read_bytes() + b" ")
    with pytest.raises(AuditInputError, match="copied artifact hash"):
        read_dataset(dest / "manifest.json")


def test_missing_source_file(tmp_path: Path) -> None:
    with pytest.raises(AuditInputError, match="source root"):
        load_historical(tmp_path / "missing", tmp_path / "out")


def test_non_literal_assignment_rejected() -> None:
    source = "DANGEROUS_ITEMS = foo()\nHARMLESS_ITEMS = []\nHARD_DANGEROUS = []\nHARD_HARMLESS = []\n"
    with pytest.raises(AuditInputError, match="not a literal"):
        extract_item_context(source, "ab" * 32)


def test_conflicting_definitions_rejected() -> None:
    source = """
DANGEROUS_ITEMS = [{"id": "d01", "bank": "dangerous_like", "q": "Q1", "a": "A"}]
HARMLESS_ITEMS = [{"id": "d1", "bank": "harmless", "q": "Q2", "a": "B"}]
HARD_DANGEROUS = []
HARD_HARMLESS = []
"""
    with pytest.raises(AuditInputError, match="conflicting"):
        extract_item_context(source, "ab" * 32)


def test_literal_extraction_aliases_d01() -> None:
    source = """
DANGEROUS_ITEMS = [{"id": "d01", "bank": "dangerous_like", "q": "Q: x", "a": "B"}]
HARMLESS_ITEMS = []
HARD_DANGEROUS = [{"id": "hd1", "bank": "dangerous_like", "q": "Q: y", "a": "B"}]
HARD_HARMLESS = []
"""
    items = extract_item_context(source, "ab" * 32)
    ids = {(item.dataset_id, item.item_id, item.definition_gold) for item in items}
    assert ("historical-h1", "d01", "B") in ids
    assert ("historical-h1", "d1", "B") in ids
    assert ("historical-h2", "hd1", "B") in ids


def test_path_escape_rejected(tmp_path: Path) -> None:
    if not HISTORICAL_ROOT.is_dir():
        pytest.skip("Historical source tree is not present")
    dest = tmp_path / "data"
    load_historical(HISTORICAL_ROOT, dest)
    manifest = json.loads((dest / "manifest.json").read_text(encoding="utf-8"))
    manifest["normalized_file"] = "../secret.jsonl"
    (dest / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(AuditInputError, match="escapes"):
        read_dataset(dest / "manifest.json")
