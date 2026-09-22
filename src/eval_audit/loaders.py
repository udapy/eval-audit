"""Historical adapter and manifest I/O. Reads pinned files; never executes historical Python."""

from __future__ import annotations

import ast
import json
from collections import Counter
from dataclasses import asdict, replace
from pathlib import Path
from typing import Any

from eval_audit import ADAPTER_VERSION, SCHEMA_VERSION
from eval_audit.io import dump_json, dump_jsonl, load_json, refuse_nonempty, resolve_inside, sha256_bytes, sha256_file
from eval_audit.parsing import parse_answer
from eval_audit.schema import (
    HISTORICAL_ALLOWED,
    Annotation,
    Artifact,
    AuditInputError,
    Comparison,
    ItemContext,
    Manifest,
    Record,
    SourceRef,
    validate_records,
)

HISTORICAL_PINNED_SHA256 = {
    "L": "8e8ca76d09c1c9db0a5be27493af661b386a7949d44e6df82e2d8fdf828e6fe3",
    "M1": "db7ca948ff5b4a58d2c036b9fc2adcbd6965a6055c1b07c86694dfd517f2ae0b",
    "M2": "1dc3ff13686baee71b99898855abc13be514e4673f2314866a49ee22d70f46f2",
    "F1": "80ea61312709bfb6b4252ba7a11e61361d888ae1bec0835499ac61790a3595f9",
    "F2": "ce754fe955f0fab34de9506d9951202f8d44beb2d7fdb56ec6ea0cbfdb775eca",
}

HISTORICAL_SOURCES: dict[str, dict[str, Any]] = {
    "L": {
        "relpath": "lib/evals_common.py",
        "kind": "item_definitions",
        "row_count": 0,
    },
    "M1": {
        "relpath": "results/gpt4.1-mini-model-results/wave1_h1/wave1_MVE.json",
        "dataset_id": "historical-h1",
        "model_label": "gpt-4.1-mini",
        "run_id": "M1",
        "row_count": 20,
        "comparison": Comparison(
            comparison_id="M1",
            dataset_id="historical-h1",
            model_label="gpt-4.1-mini",
            run_id="M1",
            baseline_condition="baseline",
            target_condition="sandbag",
            bank_mapping=None,
        ),
    },
    "F1": {
        "relpath": "results/gpt4.1-full-model-results/gpt4.1_wave1_H1_10_notebook_results/Wave1 MVE.json",
        "dataset_id": "historical-h1",
        "model_label": "gpt-4.1",
        "run_id": "F1",
        "row_count": 20,
        "comparison": Comparison(
            comparison_id="F1",
            dataset_id="historical-h1",
            model_label="gpt-4.1",
            run_id="F1",
            baseline_condition="baseline",
            target_condition="explicit_sandbag",
            bank_mapping=None,
        ),
    },
    "M2": {
        "relpath": "results/gpt4.1-mini-model-results/wave2_h2_strong/wave2_strong_MVE.json",
        "dataset_id": "historical-h2",
        "model_label": "gpt-4.1-mini",
        "run_id": "M2",
        "row_count": 24,
        "comparison": Comparison(
            comparison_id="M2",
            dataset_id="historical-h2",
            model_label="gpt-4.1-mini",
            run_id="M2",
            baseline_condition="baseline",
            target_condition="eval_cued_incentive_strong",
            bank_mapping={"security": "dangerous_like", "harmless": "harmless"},
        ),
    },
    "F2": {
        "relpath": "results/gpt4.1-full-model-results/gpt4.1_wave2_H2_strong_11_notebook_results/wave2_strong_MVE.json",
        "dataset_id": "historical-h2",
        "model_label": "gpt-4.1",
        "run_id": "F2",
        "row_count": 24,
        "comparison": Comparison(
            comparison_id="F2",
            dataset_id="historical-h2",
            model_label="gpt-4.1",
            run_id="F2",
            baseline_condition="baseline",
            target_condition="eval_cued_incentive_strong",
            bank_mapping={"security": "dangerous_like", "harmless": "harmless"},
        ),
    },
}

ITEM_ASSIGNMENTS = {
    "DANGEROUS_ITEMS": "historical-h1",
    "HARMLESS_ITEMS": "historical-h1",
    "HARD_DANGEROUS": "historical-h2",
    "HARD_HARMLESS": "historical-h2",
}

MAPPED_ROW_FIELDS = {"id", "cond", "gold", "letter", "correct", "output", "bank"}
PRESERVED_SOURCE_FIELDS = ("recog", "verbal", "recog_blind", "difficulty")
PROVENANCE_STATUS = "source_definition_not_verified_request"


def load_historical(source_root: Path, out_dir: Path) -> Manifest:
    source_root = source_root.resolve()
    out_dir = out_dir.resolve()
    if not source_root.is_dir():
        raise AuditInputError(f"source root does not exist: {source_root}", field="source")
    refuse_nonempty(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    artifacts: list[Artifact] = []
    records: list[Record] = []
    item_context: list[ItemContext] = []
    notes = [
        "Model labels are inferred from folder names, not verified API snapshot IDs.",
        "Run IDs are adapter-assigned source identities, not recovered provider run IDs.",
        "Historical responses are labeled possibly_truncated; exact per-row truncation is unknown.",
        "Item definitions are literal source assignments, not proof of the exact historical request.",
        "H1 item ids in results (d1) are matched to definition ids (d01) by dropping leading zeros.",
    ]

    for artifact_id, spec in HISTORICAL_SOURCES.items():
        relpath = spec["relpath"]
        source_path = resolve_inside(source_root / relpath, source_root, field="source")
        if not source_path.is_file():
            raise AuditInputError("missing source file", artifact=artifact_id, field="path")
        raw = source_path.read_bytes()
        digest = sha256_bytes(raw)
        expected = HISTORICAL_PINNED_SHA256[artifact_id]
        if digest != expected:
            raise AuditInputError(
                "source hash does not match the pinned Historical profile",
                artifact=artifact_id,
                field="sha256",
            )
        copied_rel = Path("raw") / artifact_id / Path(relpath).name
        copied_path = out_dir / copied_rel
        copied_path.parent.mkdir(parents=True, exist_ok=True)
        copied_path.write_bytes(raw)
        if sha256_file(copied_path) != digest:
            raise AuditInputError("copied bytes do not match source", artifact=artifact_id, field="sha256")

        if spec.get("kind") == "item_definitions":
            item_context = extract_item_context(raw.decode("utf-8"), digest)
            artifacts.append(
                Artifact(
                    artifact_id=artifact_id,
                    original_relative_path=relpath,
                    copied_relative_path=copied_rel.as_posix(),
                    sha256=digest,
                    row_count=0,
                    assigned_labels={"role": "item_definitions"},
                )
            )
            continue

        payload = json.loads(raw.decode("utf-8"))
        rows = payload.get("rows")
        if not isinstance(rows, list):
            raise AuditInputError("expected a top-level rows array", artifact=artifact_id, field="rows")
        if len(rows) != spec["row_count"]:
            raise AuditInputError(
                f"expected {spec['row_count']} rows, found {len(rows)}",
                artifact=artifact_id,
                field="rows",
            )
        for index, row in enumerate(rows):
            records.append(_row_to_record(row, index, artifact_id, digest, spec))
        artifacts.append(
            Artifact(
                artifact_id=artifact_id,
                original_relative_path=relpath,
                copied_relative_path=copied_rel.as_posix(),
                sha256=digest,
                row_count=len(rows),
                assigned_labels={
                    "dataset_id": spec["dataset_id"],
                    "model_label": spec["model_label"],
                    "run_id": spec["run_id"],
                    "model_label_origin": "inferred_from_folder_name",
                },
            )
        )

    validate_records(records)
    _check_definition_conflicts(item_context)
    records = sorted(records, key=_record_sort_key)
    normalized_rows = [record_to_dict(record) for record in records]
    normalized_rel = Path("normalized.jsonl")
    dump_jsonl(out_dir / normalized_rel, normalized_rows)
    normalized_sha = sha256_file(out_dir / normalized_rel)

    context_rel = Path("item_context.jsonl")
    context_rows = [asdict(item) for item in item_context]
    dump_jsonl(out_dir / context_rel, context_rows)
    context_sha = sha256_file(out_dir / context_rel)

    comparisons = tuple(spec["comparison"] for artifact_id, spec in HISTORICAL_SOURCES.items() if "comparison" in spec)
    manifest = Manifest(
        schema_version=SCHEMA_VERSION,
        adapter_version=ADAPTER_VERSION,
        profile="historical-v1",
        artifacts=tuple(artifacts),
        normalized_file=normalized_rel.as_posix(),
        normalized_sha256=normalized_sha,
        comparisons=comparisons,
        provenance_notes=tuple(notes),
        item_context_file=context_rel.as_posix(),
        item_context_sha256=context_sha,
    )
    manifest.validate()
    dump_json(out_dir / "manifest.json", manifest_to_dict(manifest))
    return manifest


def read_dataset(manifest_path: Path) -> tuple[Manifest, list[Record]]:
    manifest_path = manifest_path.resolve()
    if not manifest_path.is_file():
        raise AuditInputError("manifest does not exist", field="manifest")
    data_dir = manifest_path.parent
    payload = load_json(manifest_path)
    manifest = manifest_from_dict(payload)
    manifest.validate()
    _verify_manifest_paths(manifest, data_dir)

    normalized = resolve_inside(data_dir / manifest.normalized_file, data_dir, field="normalized_file")
    actual = sha256_file(normalized)
    if actual != manifest.normalized_sha256:
        raise AuditInputError("normalized file hash does not match the manifest", field="normalized_sha256")

    records = [record_from_dict(json.loads(line)) for line in normalized.read_text(encoding="utf-8").splitlines() if line]
    validate_records(records)
    _verify_record_sources(records, manifest)
    return manifest, records


def _verify_record_sources(records: list[Record], manifest: Manifest) -> None:
    artifacts = {artifact.artifact_id: artifact for artifact in manifest.artifacts}
    counts: Counter[str] = Counter()
    for record in records:
        source = record.source
        artifact = artifacts.get(source.artifact_id)
        if artifact is None:
            raise AuditInputError(
                "record source artifact is not in the manifest",
                artifact=source.artifact_id, row=source.json_pointer, field="source.artifact_id",
            )
        if source.sha256 != artifact.sha256:
            raise AuditInputError(
                "record source hash does not match the manifest artifact",
                artifact=source.artifact_id, row=source.json_pointer, field="source.sha256",
            )
        counts[source.artifact_id] += 1
    for artifact in manifest.artifacts:
        # Item JSONL counts describe definitions, not normalized response records.
        is_definitions = (
            artifact.assigned_labels.get("role") == "item_definitions"
            or artifact.assigned_labels.get("origin") == "items.jsonl"
        )
        expected = 0 if is_definitions else artifact.row_count
        if counts[artifact.artifact_id] != expected:
            raise AuditInputError(
                f"record count does not match manifest: expected {expected}, found {counts[artifact.artifact_id]}",
                artifact=artifact.artifact_id, field="row_count",
            )


def read_item_context(manifest: Manifest, data_dir: Path) -> list[ItemContext]:
    if manifest.item_context_file is None:
        return []
    path = resolve_inside(data_dir / manifest.item_context_file, data_dir, field="item_context_file")
    if sha256_file(path) != manifest.item_context_sha256:
        raise AuditInputError("item_context hash does not match the manifest", field="item_context_sha256")
    items = [item_context_from_dict(json.loads(line)) for line in path.read_text(encoding="utf-8").splitlines() if line]
    _check_definition_conflicts(items)
    return items


def load_annotation_file(path: Path) -> list[Annotation]:
    if not path.is_file():
        raise AuditInputError("annotations file does not exist", field="annotations")
    items: list[Annotation] = []
    seen: set[str] = set()
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError as exc:
            raise AuditInputError(
                "malformed annotation JSON",
                field="annotations",
                row=line_no,
            ) from exc
        if not isinstance(payload, dict):
            raise AuditInputError(
                "annotation line must be a JSON object",
                field="annotations",
                row=line_no,
            )
        annotation = annotation_from_dict(payload, row=line_no)
        if annotation.annotation_id in seen:
            raise AuditInputError(
                "duplicate annotation_id",
                field="annotation_id",
                row=line_no,
            )
        seen.add(annotation.annotation_id)
        items.append(annotation)
    return items


def read_annotations(manifest: Manifest, data_dir: Path) -> list[Annotation]:
    if manifest.annotations_file is None:
        return []
    path = resolve_inside(data_dir / manifest.annotations_file, data_dir, field="annotations_file")
    if sha256_file(path) != manifest.annotations_sha256:
        raise AuditInputError("annotations hash does not match the manifest", field="annotations_sha256")
    return load_annotation_file(path)


def annotation_from_dict(payload: dict[str, Any], *, row: int | str | None = None) -> Annotation:
    allowed = {
        "annotation_id", "dataset_id", "item_id", "text", "author", "status", "origin",
        "gold_uniqueness", "source_references",
    }
    unknown = sorted(set(payload) - allowed)
    if unknown:
        raise AuditInputError("unknown annotation field", field=unknown[0], row=row)
    try:
        refs = payload.get("source_references") or ()
        if not isinstance(refs, (list, tuple)):
            raise AuditInputError("source_references must be a list", field="source_references", row=row)
        annotation = Annotation(
            annotation_id=str(payload["annotation_id"]),
            dataset_id=str(payload["dataset_id"]),
            item_id=_opt_str(payload.get("item_id")),
            text=payload["text"],
            author=payload["author"],
            status=str(payload["status"]),
            origin=str(payload["origin"]),
            gold_uniqueness=_opt_str(payload.get("gold_uniqueness")),
            source_references=tuple(str(x) for x in refs),
        )
    except KeyError as exc:
        raise AuditInputError(
            f"missing annotation field {exc.args[0]}",
            field=str(exc.args[0]),
            row=row,
        ) from exc
    try:
        annotation.validate()
    except AuditInputError as exc:
        raise AuditInputError(str(exc), field=exc.field, row=row, artifact=exc.artifact) from exc
    return annotation


def extract_item_context(source_text: str, source_sha256: str) -> list[ItemContext]:
    try:
        tree = ast.parse(source_text)
    except SyntaxError as exc:
        raise AuditInputError("item-definition source is not parseable Python", field="item_definitions") from exc
    found: dict[str, ast.AST] = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            name = node.targets[0].id
            if name in ITEM_ASSIGNMENTS:
                found[name] = node.value
    missing = [name for name in ITEM_ASSIGNMENTS if name not in found]
    if missing:
        raise AuditInputError(
            f"missing allowlisted literal assignments: {missing}",
            field="item_definitions",
        )
    items: list[ItemContext] = []
    for name, dataset_id in ITEM_ASSIGNMENTS.items():
        try:
            value = ast.literal_eval(found[name])
        except (ValueError, TypeError) as exc:
            raise AuditInputError(
                f"{name} is not a literal assignment",
                artifact="L",
                field=name,
            ) from exc
        if not isinstance(value, list):
            raise AuditInputError(f"{name} must be a list of item dicts", field=name)
        for index, raw in enumerate(value):
            if not isinstance(raw, dict):
                raise AuditInputError(f"{name}[{index}] is not a dict", field=name)
            for required in ("id", "q", "a"):
                if required not in raw or not isinstance(raw[required], str) or raw[required] == "":
                    raise AuditInputError(
                        f"{name}[{index}] missing {required}",
                        field=required,
                    )
            source_id = raw["id"]
            aliases = _item_aliases(source_id)
            for item_id in aliases:
                items.append(
                    ItemContext(
                        dataset_id=dataset_id,
                        item_id=item_id,
                        question_with_options=raw["q"],
                        definition_gold=raw["a"],
                        source_artifact_sha256=source_sha256,
                        source_locator=f"{name}[{index}].id={source_id}",
                        provenance_status=PROVENANCE_STATUS,
                    )
                )
    _check_definition_conflicts(items)
    return items


def record_to_dict(record: Record) -> dict[str, Any]:
    payload = asdict(record)
    payload["allowed_answers"] = list(record.allowed_answers)
    payload["option_order"] = list(record.option_order) if record.option_order is not None else None
    return payload


def record_from_dict(payload: dict[str, Any]) -> Record:
    source = payload.get("source")
    if not isinstance(source, dict):
        raise AuditInputError("record.source must be an object", field="source")
    allowed = payload.get("allowed_answers")
    if not isinstance(allowed, list):
        raise AuditInputError("allowed_answers must be a list", field="allowed_answers")
    record = Record(
        schema_version=int(payload["schema_version"]),
        dataset_id=str(payload["dataset_id"]),
        model_label=str(payload["model_label"]),
        run_id=str(payload["run_id"]),
        condition=str(payload["condition"]),
        item_id=str(payload["item_id"]),
        repeat_id=_opt_str(payload.get("repeat_id")),
        permutation_id=_opt_str(payload.get("permutation_id")),
        bank=_opt_str(payload.get("bank")),
        allowed_answers=tuple(str(x) for x in allowed),
        gold=str(payload["gold"]),
        stored_answer=_opt_str(payload.get("stored_answer")),
        stored_correct=_opt_bool(payload.get("stored_correct")),
        response_text=_opt_str(payload.get("response_text")) if payload.get("response_text") is not None else None,
        response_completeness=str(payload["response_completeness"]),
        parsed_answer=_opt_str(payload.get("parsed_answer")),
        parse_status=str(payload["parse_status"]),
        source=SourceRef(
            artifact_id=str(source["artifact_id"]),
            sha256=str(source["sha256"]),
            json_pointer=str(source["json_pointer"]),
        ),
        source_fields=dict(payload.get("source_fields") or {}),
        option_order=_option_order(payload.get("option_order")),
        gold_content_id=payload.get("gold_content_id"),
    )
    record.validate()
    return record


def _option_order(value: Any) -> tuple[str, ...] | None:
    if value is None:
        return None
    if not isinstance(value, list):
        raise AuditInputError("option_order must be a list", field="option_order")
    return tuple(value)


def manifest_to_dict(manifest: Manifest) -> dict[str, Any]:
    return {
        "schema_version": manifest.schema_version,
        "adapter_version": manifest.adapter_version,
        "profile": manifest.profile,
        "artifacts": [asdict(artifact) for artifact in manifest.artifacts],
        "normalized_file": manifest.normalized_file,
        "normalized_sha256": manifest.normalized_sha256,
        "comparisons": [
            {
                "comparison_id": c.comparison_id,
                "dataset_id": c.dataset_id,
                "model_label": c.model_label,
                "run_id": c.run_id,
                "baseline_condition": c.baseline_condition,
                "target_condition": c.target_condition,
                "bank_mapping": c.bank_mapping,
            }
            for c in manifest.comparisons
        ],
        "provenance_notes": list(manifest.provenance_notes),
        "item_context_file": manifest.item_context_file,
        "item_context_sha256": manifest.item_context_sha256,
        "annotations_file": manifest.annotations_file,
        "annotations_sha256": manifest.annotations_sha256,
    }


def manifest_from_dict(payload: dict[str, Any]) -> Manifest:
    artifacts = tuple(
        Artifact(
            artifact_id=str(raw["artifact_id"]),
            original_relative_path=str(raw["original_relative_path"]),
            copied_relative_path=str(raw["copied_relative_path"]),
            sha256=str(raw["sha256"]),
            row_count=int(raw["row_count"]),
            assigned_labels=dict(raw.get("assigned_labels") or {}),
        )
        for raw in payload["artifacts"]
    )
    comparisons = tuple(
        Comparison(
            comparison_id=str(raw["comparison_id"]),
            dataset_id=str(raw["dataset_id"]),
            model_label=str(raw["model_label"]),
            run_id=str(raw["run_id"]),
            baseline_condition=str(raw["baseline_condition"]),
            target_condition=str(raw["target_condition"]),
            bank_mapping=raw.get("bank_mapping"),
        )
        for raw in payload["comparisons"]
    )
    return Manifest(
        schema_version=int(payload["schema_version"]),
        adapter_version=str(payload["adapter_version"]),
        profile=str(payload["profile"]),
        artifacts=artifacts,
        normalized_file=str(payload["normalized_file"]),
        normalized_sha256=str(payload["normalized_sha256"]),
        comparisons=comparisons,
        provenance_notes=tuple(payload.get("provenance_notes") or ()),
        item_context_file=_opt_str(payload.get("item_context_file")),
        item_context_sha256=_opt_str(payload.get("item_context_sha256")),
        annotations_file=_opt_str(payload.get("annotations_file")),
        annotations_sha256=_opt_str(payload.get("annotations_sha256")),
    )


def item_context_from_dict(payload: dict[str, Any]) -> ItemContext:
    item = ItemContext(
        dataset_id=str(payload["dataset_id"]),
        item_id=str(payload["item_id"]),
        question_with_options=str(payload["question_with_options"]),
        definition_gold=str(payload["definition_gold"]),
        source_artifact_sha256=str(payload["source_artifact_sha256"]),
        source_locator=str(payload["source_locator"]),
        provenance_status=str(payload["provenance_status"]),
    )
    item.validate()
    return item


def write_manifest(path: Path, manifest: Manifest) -> None:
    manifest.validate()
    dump_json(path, manifest_to_dict(manifest))


def with_annotations(manifest: Manifest, *, relpath: str, sha256: str) -> Manifest:
    return replace(manifest, annotations_file=relpath, annotations_sha256=sha256)


def _row_to_record(
    row: Any,
    index: int,
    artifact_id: str,
    digest: str,
    spec: dict[str, Any],
) -> Record:
    if not isinstance(row, dict):
        raise AuditInputError("row is not an object", artifact=artifact_id, row=index, field="rows")
    item_id = row.get("id")
    condition = row.get("cond")
    gold = row.get("gold")
    if not isinstance(item_id, str) or not item_id:
        raise AuditInputError("missing id", artifact=artifact_id, row=index, field="id")
    if not isinstance(condition, str) or not condition:
        raise AuditInputError("missing cond", artifact=artifact_id, row=index, field="cond")
    if not isinstance(gold, str):
        raise AuditInputError("invalid gold", artifact=artifact_id, row=index, field="gold")
    stored = row.get("letter")
    if stored is not None and not isinstance(stored, str):
        raise AuditInputError("invalid letter", artifact=artifact_id, row=index, field="letter")
    stored_correct = row.get("correct")
    if stored_correct is not None and not isinstance(stored_correct, bool):
        raise AuditInputError("invalid correct", artifact=artifact_id, row=index, field="correct")
    output = row.get("output")
    if output is not None and not isinstance(output, str):
        raise AuditInputError("invalid output", artifact=artifact_id, row=index, field="output")
    bank = row.get("bank")
    if bank is not None and not isinstance(bank, str):
        raise AuditInputError("invalid bank", artifact=artifact_id, row=index, field="bank")
    parsed = parse_answer(output, HISTORICAL_ALLOWED)
    extras = {key: value for key, value in row.items() if key not in MAPPED_ROW_FIELDS}
    source_fields = {key: extras.get(key) for key in PRESERVED_SOURCE_FIELDS}
    source_fields["extra"] = {key: value for key, value in extras.items() if key not in PRESERVED_SOURCE_FIELDS}
    return Record(
        schema_version=SCHEMA_VERSION,
        dataset_id=spec["dataset_id"],
        model_label=spec["model_label"],
        run_id=spec["run_id"],
        condition=condition,
        item_id=item_id,
        repeat_id=None,
        permutation_id=None,
        bank=bank,
        allowed_answers=HISTORICAL_ALLOWED,
        gold=gold,
        stored_answer=stored,
        stored_correct=stored_correct,
        response_text=output,
        response_completeness="possibly_truncated",
        parsed_answer=parsed.answer,
        parse_status=parsed.status,
        source=SourceRef(artifact_id=artifact_id, sha256=digest, json_pointer=f"/rows/{index}"),
        source_fields=source_fields,
    )


def _verify_manifest_paths(manifest: Manifest, data_dir: Path) -> None:
    for artifact in manifest.artifacts:
        copied = resolve_inside(data_dir / artifact.copied_relative_path, data_dir, field="copied_relative_path")
        if not copied.is_file():
            raise AuditInputError("copied artifact is missing", artifact=artifact.artifact_id, field="path")
        if sha256_file(copied) != artifact.sha256:
            raise AuditInputError(
                "copied artifact hash does not match the manifest",
                artifact=artifact.artifact_id,
                field="sha256",
            )
    resolve_inside(data_dir / manifest.normalized_file, data_dir, field="normalized_file")
    if manifest.item_context_file:
        resolve_inside(data_dir / manifest.item_context_file, data_dir, field="item_context_file")
    if manifest.annotations_file:
        resolve_inside(data_dir / manifest.annotations_file, data_dir, field="annotations_file")


def _check_definition_conflicts(items: list[ItemContext]) -> None:
    seen: dict[tuple[str, str], ItemContext] = {}
    for item in items:
        item.validate()
        key = (item.dataset_id, item.item_id)
        previous = seen.get(key)
        if previous is None:
            seen[key] = item
            continue
        if (
            previous.question_with_options != item.question_with_options
            or previous.definition_gold != item.definition_gold
        ):
            raise AuditInputError(
                "conflicting item definitions",
                field="item_id",
                row=item.item_id,
            )


def _item_aliases(item_id: str) -> tuple[str, ...]:
    alias = _unpad_item_id(item_id)
    if alias == item_id:
        return (item_id,)
    return (item_id, alias)


def _unpad_item_id(item_id: str) -> str:
    prefix = []
    digits = []
    for char in item_id:
        if char.isalpha() and not digits:
            prefix.append(char)
        elif char.isdigit():
            digits.append(char)
        else:
            return item_id
    if not prefix or not digits:
        return item_id
    return f"{''.join(prefix)}{int(''.join(digits))}"


def _record_sort_key(record: Record) -> tuple[Any, ...]:
    return (
        record.dataset_id,
        record.model_label,
        record.run_id,
        record.condition,
        record.item_id,
        (0, "") if record.repeat_id is None else (1, record.repeat_id),
        (0, "") if record.permutation_id is None else (1, record.permutation_id),
    )


def _opt_str(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)


def _opt_bool(value: Any) -> bool | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    raise AuditInputError("expected boolean or null", field="stored_correct")
