"""Generic JSON/JSONL adapter. Historical-agnostic; does not special-case item ids or overwrite gold."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from eval_audit import ADAPTER_VERSION, SCHEMA_VERSION
from eval_audit.io import dump_json, dump_jsonl, refuse_nonempty, sha256_bytes, sha256_file
from eval_audit.loaders import (
    _record_sort_key,
    _option_order,
    manifest_to_dict,
    record_to_dict,
)
from eval_audit.parsing import parse_answer
from eval_audit.schema import (
    GENERIC_PROFILE,
    Artifact,
    AuditInputError,
    Comparison,
    ItemContext,
    Manifest,
    Record,
    SourceRef,
    profile_by_name,
    validate_records,
)

DEFAULT_ALLOWED = ("A", "B", "C", "D")
ROW_ALIASES = {
    "condition": ("condition", "cond"),
    "stored_answer": ("stored_answer", "letter"),
    "response_text": ("response_text", "output"),
    "stored_correct": ("stored_correct", "correct"),
}


@dataclass
class _SourceBundle:
    payload: dict[str, Any]
    artifacts: list[Artifact]
    row_locators: list[str] | None = None
    item_artifact_id: str = "GENERIC"
    item_locators: list[str] | None = None


def load_generic(source: Path, out_dir: Path) -> Manifest:
    source = source.resolve()
    out_dir = out_dir.resolve()
    if not source.exists():
        raise AuditInputError(f"generic source does not exist: {source}", field="source")
    refuse_nonempty(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    imported = _read_source(source, out_dir)
    bundle, raw_copies = imported.payload, imported.artifacts
    profile_name = str(bundle.get("profile") or GENERIC_PROFILE)
    profile_by_name(profile_name)

    defaults = bundle.get("defaults") or {}
    if defaults is None:
        defaults = {}
    if not isinstance(defaults, dict):
        raise AuditInputError("defaults must be an object", field="defaults")

    comparisons = _comparisons(bundle.get("comparisons"))
    raw_rows = bundle.get("rows")
    if not isinstance(raw_rows, list) or not raw_rows:
        raise AuditInputError("expected a nonempty rows array", field="rows")

    artifacts = tuple(raw_copies)
    primary = artifacts[0]
    records: list[Record] = []
    for index, row in enumerate(raw_rows):
        locator = imported.row_locators[index] if imported.row_locators is not None else f"/rows/{index}"
        records.append(_row_to_record(row, index, defaults, primary, locator))

    validate_records(records)
    records = sorted(records, key=_record_sort_key)
    _check_comparisons_cover_records(records, comparisons)

    dump_jsonl(out_dir / "normalized.jsonl", [record_to_dict(record) for record in records])
    item_artifact = next(a for a in artifacts if a.artifact_id == imported.item_artifact_id)
    context = _items(bundle.get("items"), item_artifact.sha256, imported.item_locators)
    item_context_file = None
    item_context_sha = None
    if context:
        dump_jsonl(out_dir / "item_context.jsonl", [asdict(item) for item in context])
        item_context_file = "item_context.jsonl"
        item_context_sha = sha256_file(out_dir / "item_context.jsonl")

    notes = tuple(str(n) for n in (bundle.get("provenance_notes") or ()))
    if not notes:
        notes = ("Generic import. Provenance notes were not supplied in the source bundle.",)

    manifest = Manifest(
        schema_version=SCHEMA_VERSION,
        adapter_version=ADAPTER_VERSION,
        profile=profile_name,
        artifacts=artifacts,
        normalized_file="normalized.jsonl",
        normalized_sha256=sha256_file(out_dir / "normalized.jsonl"),
        comparisons=comparisons,
        provenance_notes=notes,
        item_context_file=item_context_file,
        item_context_sha256=item_context_sha,
    )
    manifest.validate()
    dump_json(out_dir / "manifest.json", manifest_to_dict(manifest))
    return manifest


def _read_source(source: Path, out_dir: Path) -> _SourceBundle:
    raw_root = out_dir / "raw"
    raw_root.mkdir(parents=True, exist_ok=True)
    if source.is_file():
        raw = source.read_bytes()
        digest = sha256_bytes(raw)
        dest = raw_root / source.name
        dest.write_bytes(raw)
        payload = _parse_json_bytes(raw, field="source")
        if not isinstance(payload, dict):
            raise AuditInputError("bundle JSON must be an object", field="source")
        artifact = Artifact(
            artifact_id="GENERIC",
            original_relative_path=source.name,
            copied_relative_path=dest.relative_to(out_dir).as_posix(),
            sha256=digest,
            row_count=_row_count(payload),
            assigned_labels={"adapter": "generic", "origin": "source_file"},
        )
        return _SourceBundle(payload, [artifact])

    bundle_path = source / "bundle.json"
    rows_path = source / "rows.jsonl"
    comparisons_path = source / "comparisons.json"
    if bundle_path.is_file():
        raw = bundle_path.read_bytes()
        dest = raw_root / "bundle.json"
        dest.write_bytes(raw)
        payload = _parse_json_bytes(raw, field="bundle")
        if not isinstance(payload, dict):
            raise AuditInputError("bundle.json must be an object", field="bundle")
        artifact = Artifact(
            artifact_id="GENERIC",
            original_relative_path="bundle.json",
            copied_relative_path=dest.relative_to(out_dir).as_posix(),
            sha256=sha256_bytes(raw),
            row_count=_row_count(payload),
            assigned_labels={"adapter": "generic", "origin": "bundle.json"},
        )
        return _SourceBundle(payload, [artifact])
    if rows_path.is_file() and comparisons_path.is_file():
        rows_raw = rows_path.read_bytes()
        cmp_raw = comparisons_path.read_bytes()
        (raw_root / "rows.jsonl").write_bytes(rows_raw)
        (raw_root / "comparisons.json").write_bytes(cmp_raw)
        rows = _parse_jsonl_bytes(rows_raw)
        comparisons_payload = _parse_json_bytes(cmp_raw, field="comparisons")
        meta: dict[str, Any] = {}
        item_artifact_id = "COMPARISONS"
        item_locators = None
        meta_path = source / "meta.json"
        artifacts = [
            Artifact(
                artifact_id="ROWS",
                original_relative_path="rows.jsonl",
                copied_relative_path="raw/rows.jsonl",
                sha256=sha256_bytes(rows_raw),
                row_count=len(rows),
                assigned_labels={"adapter": "generic", "origin": "rows.jsonl"},
            ),
            Artifact(
                artifact_id="COMPARISONS",
                original_relative_path="comparisons.json",
                copied_relative_path="raw/comparisons.json",
                sha256=sha256_bytes(cmp_raw),
                row_count=0,
                assigned_labels={"adapter": "generic", "origin": "comparisons.json"},
            ),
        ]
        if meta_path.is_file():
            meta_raw = meta_path.read_bytes()
            (raw_root / "meta.json").write_bytes(meta_raw)
            parsed_meta = _parse_json_bytes(meta_raw, field="meta")
            if not isinstance(parsed_meta, dict):
                raise AuditInputError("meta.json must be an object", field="meta")
            meta = parsed_meta
            if "items" in meta:
                item_artifact_id = "META"
            artifacts.append(
                Artifact(
                    artifact_id="META",
                    original_relative_path="meta.json",
                    copied_relative_path="raw/meta.json",
                    sha256=sha256_bytes(meta_raw),
                    row_count=0,
                    assigned_labels={"adapter": "generic", "origin": "meta.json"},
                )
            )
        items_path = source / "items.jsonl"
        items: list[Any] = []
        if items_path.is_file():
            items_raw = items_path.read_bytes()
            (raw_root / "items.jsonl").write_bytes(items_raw)
            items = _parse_jsonl_bytes(items_raw)
            if items:
                item_artifact_id = "ITEMS"
                item_locators = _jsonl_locators(items_raw)
            artifacts.append(
                Artifact(
                    artifact_id="ITEMS",
                    original_relative_path="items.jsonl",
                    copied_relative_path="raw/items.jsonl",
                    sha256=sha256_bytes(items_raw),
                    row_count=len(items),
                    assigned_labels={"adapter": "generic", "origin": "items.jsonl"},
                )
            )
        if isinstance(comparisons_payload, dict) and "comparisons" in comparisons_payload:
            comparisons = comparisons_payload["comparisons"]
            extra = {k: v for k, v in comparisons_payload.items() if k != "comparisons"}
            meta = {**extra, **meta}
        else:
            comparisons = comparisons_payload
        payload = {
            **meta,
            "comparisons": comparisons,
            "rows": rows,
            "items": items or meta.get("items"),
        }
        return _SourceBundle(payload, artifacts, _jsonl_locators(rows_raw), item_artifact_id, item_locators)
    raise AuditInputError(
        "generic source must be a bundle JSON file, a directory with bundle.json, "
        "or a directory with rows.jsonl and comparisons.json",
        field="source",
    )


def _parse_json_bytes(raw: bytes, *, field: str) -> Any:
    try:
        return json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise AuditInputError("source is not valid JSON", field=field) from exc


def _parse_jsonl_bytes(raw: bytes) -> list[Any]:
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise AuditInputError("rows.jsonl is not UTF-8", field="rows") from exc
    rows: list[Any] = []
    for line_no, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise AuditInputError("malformed JSONL row", field="rows", row=line_no) from exc
    return rows


def _jsonl_locators(raw: bytes) -> list[str]:
    return [f"line:{number}" for number, line in enumerate(raw.decode("utf-8").splitlines(), start=1)
            if line.strip()]


def _row_count(payload: dict[str, Any]) -> int:
    rows = payload.get("rows")
    if isinstance(rows, list):
        return len(rows)
    return 0


def _comparisons(raw: Any) -> tuple[Comparison, ...]:
    if not isinstance(raw, list) or not raw:
        raise AuditInputError("expected a nonempty comparisons array", field="comparisons")
    items: list[Comparison] = []
    for index, spec in enumerate(raw):
        if not isinstance(spec, dict):
            raise AuditInputError("comparison must be an object", field="comparisons", row=index)
        try:
            comparison = Comparison(
                comparison_id=str(spec["comparison_id"]),
                dataset_id=str(spec["dataset_id"]),
                model_label=str(spec["model_label"]),
                run_id=str(spec["run_id"]),
                baseline_condition=str(spec["baseline_condition"]),
                target_condition=str(spec["target_condition"]),
                bank_mapping=spec.get("bank_mapping"),
            )
        except KeyError as exc:
            raise AuditInputError(
                f"missing comparison field {exc.args[0]}",
                field=str(exc.args[0]),
                row=index,
            ) from exc
        comparison.validate()
        items.append(comparison)
    return tuple(items)


def _row_to_record(
    row: Any, index: int, defaults: dict[str, Any], artifact: Artifact, locator: str,
) -> Record:
    if not isinstance(row, dict):
        raise AuditInputError("row is not an object", artifact=artifact.artifact_id, row=index, field="rows")
    merged = {**defaults, **row}
    item_id = _require_str(merged, "item_id", index, artifact.artifact_id)
    condition = _first_str(merged, ROW_ALIASES["condition"], "condition", index, artifact.artifact_id)
    gold = _require_str(merged, "gold", index, artifact.artifact_id)
    dataset_id = _require_str(merged, "dataset_id", index, artifact.artifact_id)
    model_label = _require_str(merged, "model_label", index, artifact.artifact_id)
    run_id = _require_str(merged, "run_id", index, artifact.artifact_id)
    stored = _optional_str(merged, ROW_ALIASES["stored_answer"])
    stored_correct = _optional_bool(merged, ROW_ALIASES["stored_correct"], index, artifact.artifact_id)
    response_text = _optional_str(merged, ROW_ALIASES["response_text"])
    if "response_text" in merged and merged["response_text"] is None:
        response_text = None
    allowed_raw = merged.get("allowed_answers") or list(DEFAULT_ALLOWED)
    if not isinstance(allowed_raw, list) or not allowed_raw:
        raise AuditInputError(
            "allowed_answers must be a nonempty list",
            artifact=artifact.artifact_id,
            row=index,
            field="allowed_answers",
        )
    allowed = tuple(str(x) for x in allowed_raw)
    completeness = str(merged.get("response_completeness") or "unknown")
    parsed = parse_answer(response_text, allowed)
    return Record(
        schema_version=SCHEMA_VERSION,
        dataset_id=dataset_id,
        model_label=model_label,
        run_id=run_id,
        condition=condition,
        item_id=item_id,
        repeat_id=_opt(merged.get("repeat_id")),
        permutation_id=_opt(merged.get("permutation_id")),
        bank=_opt(merged.get("bank")),
        allowed_answers=allowed,
        gold=gold,
        stored_answer=stored,
        stored_correct=stored_correct,
        response_text=response_text,
        response_completeness=completeness,
        parsed_answer=parsed.answer,
        parse_status=parsed.status,
        source=SourceRef(
            artifact_id=artifact.artifact_id,
            sha256=artifact.sha256,
            json_pointer=locator,
        ),
        source_fields={
            key: value
            for key, value in row.items()
            if key
            not in {
                "dataset_id",
                "model_label",
                "run_id",
                "condition",
                "cond",
                "item_id",
                "gold",
                "stored_answer",
                "letter",
                "stored_correct",
                "correct",
                "response_text",
                "output",
                "allowed_answers",
                "response_completeness",
                "bank",
                "repeat_id",
                "permutation_id",
                "option_order",
                "gold_content_id",
            }
        },
        option_order=_option_order(merged.get("option_order")),
        gold_content_id=merged.get("gold_content_id"),
    )


def _items(raw: Any, source_sha256: str, locators: list[str] | None = None) -> list[ItemContext]:
    if raw is None:
        return []
    if not isinstance(raw, list):
        raise AuditInputError("items must be a list", field="items")
    items: list[ItemContext] = []
    for index, spec in enumerate(raw):
        if not isinstance(spec, dict):
            raise AuditInputError("item context must be an object", field="items", row=index)
        try:
            item = ItemContext(
                dataset_id=str(spec["dataset_id"]),
                item_id=str(spec["item_id"]),
                question_with_options=str(spec["question_with_options"]),
                definition_gold=str(spec["definition_gold"]),
                source_artifact_sha256=str(spec.get("source_artifact_sha256") or source_sha256),
                source_locator=str(spec.get("source_locator") or (locators[index] if locators else f"/items/{index}")),
                provenance_status=str(spec.get("provenance_status") or "generic_source"),
            )
        except KeyError as exc:
            raise AuditInputError(
                f"missing item field {exc.args[0]}",
                field=str(exc.args[0]),
                row=index,
            ) from exc
        item.validate()
        items.append(item)
    return items


def _check_comparisons_cover_records(records: list[Record], comparisons: tuple[Comparison, ...]) -> None:
    keys = {(r.dataset_id, r.model_label, r.run_id) for r in records}
    for comparison in comparisons:
        key = (comparison.dataset_id, comparison.model_label, comparison.run_id)
        if key not in keys:
            raise AuditInputError(
                "comparison does not match any record dataset/model/run",
                field="comparisons",
                row=comparison.comparison_id,
            )


def _require_str(payload: dict[str, Any], field: str, index: int, artifact: str) -> str:
    value = payload.get(field)
    if not isinstance(value, str) or value == "":
        raise AuditInputError(f"missing {field}", artifact=artifact, row=index, field=field)
    return value


def _first_str(
    payload: dict[str, Any],
    names: tuple[str, ...],
    field: str,
    index: int,
    artifact: str,
) -> str:
    for name in names:
        value = payload.get(name)
        if isinstance(value, str) and value:
            return value
    raise AuditInputError(f"missing {field}", artifact=artifact, row=index, field=field)


def _optional_str(payload: dict[str, Any], names: tuple[str, ...]) -> str | None:
    for name in names:
        if name in payload:
            value = payload[name]
            if value is None:
                return None
            if not isinstance(value, str):
                raise AuditInputError(f"invalid {names[0]}", field=names[0])
            return value
    return None


def _optional_bool(
    payload: dict[str, Any],
    names: tuple[str, ...],
    index: int,
    artifact: str,
) -> bool | None:
    for name in names:
        if name not in payload:
            continue
        value = payload[name]
        if value is None:
            return None
        if isinstance(value, bool):
            return value
        raise AuditInputError(
            f"invalid {names[0]}",
            artifact=artifact,
            row=index,
            field=names[0],
        )
    return None


def _opt(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value)
    return text if text else None
