"""Reject unsupported edits and keep copied source provenance reproducible."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from eval_audit.generic import load_generic
from eval_audit.io import sha256_file
from eval_audit.loaders import load_annotation_file, read_dataset, read_item_context, record_from_dict, record_to_dict
from eval_audit.schema import AuditInputError


def bundle() -> dict:
    return {
        "defaults": {"dataset_id": "fixture", "model_label": "synthetic", "run_id": "R"},
        "comparisons": [{"comparison_id": "C", "dataset_id": "fixture", "model_label": "synthetic",
                         "run_id": "R", "baseline_condition": "baseline", "target_condition": "cue"}],
        "rows": [{"item_id": "i", "condition": condition, "gold": "A", "stored_answer": "B",
                  "response_text": "ANSWER: B"} for condition in ("baseline", "cue")],
        "items": [{"dataset_id": "fixture", "item_id": "i", "question_with_options": "A: one; B: two",
                   "definition_gold": "A"}],
    }


def import_bundle(tmp_path: Path, payload: dict | None = None) -> Path:
    source = tmp_path / "bundle.json"
    source.write_text(json.dumps(bundle() if payload is None else payload), encoding="utf-8")
    dest = tmp_path / "data"
    load_generic(source, dest)
    return dest


@pytest.mark.parametrize("field", ["gold", "stored_answer", "unexpected"])
def test_annotation_rejects_unknown_fields(tmp_path: Path, field: str) -> None:
    payload = {"annotation_id": "a", "dataset_id": "fixture", "text": "Review rationale",
               "author": "Reviewer", "status": "proposed", "origin": "human", field: "B"}
    path = tmp_path / "annotations.jsonl"
    path.write_text(json.dumps(payload) + "\n", encoding="utf-8")
    with pytest.raises(AuditInputError, match="unknown annotation field") as error:
        load_annotation_file(path)
    assert error.value.field == field
    assert error.value.row == 1


@pytest.mark.parametrize("field", ["author", "text"])
@pytest.mark.parametrize("value", [None, 17, False])
def test_annotation_does_not_coerce_required_text(tmp_path: Path, field: str, value: object) -> None:
    payload = {"annotation_id": "a", "dataset_id": "fixture", "text": "Review rationale",
               "author": "Reviewer", "status": "proposed", "origin": "human"}
    payload[field] = value
    path = tmp_path / "annotations.jsonl"
    path.write_text(json.dumps(payload) + "\n", encoding="utf-8")
    with pytest.raises(AuditInputError) as error:
        load_annotation_file(path)
    assert error.value.field == field


@pytest.mark.parametrize("field,value", [("artifact_id", "UNKNOWN"), ("sha256", "f" * 64)])
def test_read_dataset_rejects_unbound_source(tmp_path: Path, field: str, value: str) -> None:
    dest = import_bundle(tmp_path)
    path = dest / "normalized.jsonl"
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    rows[0]["source"][field] = value
    path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")
    manifest_path = dest / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["normalized_sha256"] = sha256_file(path)
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(AuditInputError) as error:
        read_dataset(manifest_path)
    assert error.value.field == f"source.{field}"


def test_read_dataset_rejects_wrong_record_count(tmp_path: Path) -> None:
    dest = import_bundle(tmp_path)
    manifest_path = dest / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["artifacts"][0]["row_count"] += 1
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(AuditInputError, match="record count"):
        read_dataset(manifest_path)


@pytest.mark.parametrize("item_location,expected_id", [("items", "ITEMS"), ("meta", "META"),
                                                       ("comparisons", "COMPARISONS")])
def test_jsonl_provenance_uses_actual_artifact_and_line(tmp_path: Path, item_location: str, expected_id: str) -> None:
    payload = bundle()
    source = tmp_path / "source"
    source.mkdir()
    rows = [{**payload["defaults"], **row} for row in payload["rows"]]
    (source / "rows.jsonl").write_text("\n" + json.dumps(rows[0]) + "\n\n" + json.dumps(rows[1]) + "\n")
    comparisons = payload["comparisons"]
    if item_location == "comparisons":
        comparisons = {"comparisons": comparisons, "items": payload["items"]}
    (source / "comparisons.json").write_text(json.dumps(comparisons))
    if item_location == "meta":
        (source / "meta.json").write_text(json.dumps({"items": payload["items"]}))
    if item_location == "items":
        (source / "items.jsonl").write_text("\n" + json.dumps(payload["items"][0]) + "\n")
    dest = tmp_path / "data"
    manifest = load_generic(source, dest)
    _, records = read_dataset(dest / "manifest.json")
    context = read_item_context(manifest, dest)
    artifact = next(a for a in manifest.artifacts if a.artifact_id == expected_id)
    assert context[0].source_artifact_sha256 == artifact.sha256
    assert {r.source.json_pointer for r in records} == {"line:2", "line:4"}
    if item_location == "items":
        assert context[0].source_locator == "line:2"


def test_option_identity_roundtrip_preserves_stored_gold_even_when_mismatched(tmp_path: Path) -> None:
    payload = bundle()
    for row in payload["rows"]:
        row.update(option_order=["wrong", "correct", "third", "fourth"], gold_content_id="correct")
    dest = import_bundle(tmp_path, payload)
    _, records = read_dataset(dest / "manifest.json")
    for record in records:
        assert record.option_order == ("wrong", "correct", "third", "fourth")
        assert record.gold_content_id == "correct"
        assert record.gold == "A"
        assert record.stored_answer == "B"
        assert "option_order" not in record.source_fields
        serialized = record_to_dict(record)
        assert serialized["option_order"] == ["wrong", "correct", "third", "fourth"]
        assert record_from_dict(serialized) == record


@pytest.mark.parametrize("option_order", ["abcd", {"A": "one"}, [None, "two", "three", "four"]])
def test_generic_rejects_malformed_option_order(tmp_path: Path, option_order: object) -> None:
    payload = bundle()
    payload["rows"][0].update(option_order=option_order, gold_content_id="two")
    with pytest.raises(AuditInputError):
        import_bundle(tmp_path, payload)


def test_read_dataset_detects_removed_record_even_with_updated_normalized_hash(tmp_path: Path) -> None:
    dest = import_bundle(tmp_path)
    path = dest / "normalized.jsonl"
    path.write_text(path.read_text().splitlines()[0] + "\n", encoding="utf-8")
    manifest_path = dest / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["normalized_sha256"] = sha256_file(path)
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(AuditInputError, match="record count"):
        read_dataset(manifest_path)


def test_optional_option_identity_can_be_defaulted_or_absent(tmp_path: Path) -> None:
    payload = bundle()
    payload["defaults"].update(option_order=["one", "two", "three", "four"], gold_content_id="one")
    dest = import_bundle(tmp_path, payload)
    _, records = read_dataset(dest / "manifest.json")
    for record in records:
        assert record.option_order == ("one", "two", "three", "four")
        assert record.gold_content_id == "one"
        legacy_payload = record_to_dict(record)
        del legacy_payload["option_order"]
        del legacy_payload["gold_content_id"]
        legacy = record_from_dict(legacy_payload)
        assert legacy.option_order is None
        assert legacy.gold_content_id is None
