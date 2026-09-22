"""Bounded, local audit application service. No network or model execution.

Paths are confined to one operator-owned workspace. This is not a sandbox
against another process running with the same filesystem privileges.
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from eval_audit.generic import load_generic
from eval_audit.io import refuse_nonempty, sha256_bytes
from eval_audit.loaders import (load_annotation_file, read_annotations, read_dataset,
                               read_item_context, with_annotations)
from eval_audit.report import build_report, capture_inputs, write_report
from eval_audit.schema import AuditInputError


class ServiceError(AuditInputError):
    """Stable code plus human-readable message; never a successful result."""
    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(message)

    def as_dict(self) -> dict:
        return {"code": self.code, "message": str(self)}


def audit_manifest(manifest_path: Path, out: Path, annotations_path: Path | None = None):
    """Shared orchestration for CLI and service; retain core report arithmetic."""
    refuse_nonempty(out)
    manifest, records = read_dataset(manifest_path)
    data_dir = manifest_path.resolve().parent
    context = read_item_context(manifest, data_dir)
    annotation_bytes = None
    if annotations_path is not None:
        if not annotations_path.is_file():
            raise AuditInputError("annotations file does not exist", field="annotations")
        annotation_bytes = annotations_path.read_bytes()
        annotations = load_annotation_file(annotations_path)
        manifest = with_annotations(manifest, relpath="annotations.jsonl",
                                    sha256=sha256_bytes(annotation_bytes))
    else:
        annotations = read_annotations(manifest, data_dir)
    report = build_report(records, manifest, item_context=context, annotations=annotations)
    write_report(report, out, input_files=capture_inputs(manifest_path, manifest, annotation_bytes))
    return report


class AuditService:
    """One workspace, append-only attempts, completion receipts and bounded reads."""
    def __init__(self, workspace: str | Path, output_root: str | Path, *,
                 max_bytes: int = 10 * 1024 * 1024, max_records: int = 2000,
                 page_size: int = 20, max_excerpt_chars: int = 4096):
        for value in (max_bytes, max_records, page_size, max_excerpt_chars):
            if type(value) is not int or value <= 0:
                raise ServiceError("INVALID_INPUT", "Resource limits must be positive integers.")
        try:
            self.workspace = Path(workspace).resolve(strict=True)
        except (OSError, ValueError) as exc:
            raise ServiceError("INVALID_INPUT", "Workspace must be an existing directory.") from exc
        if not self.workspace.is_dir():
            raise ServiceError("INVALID_INPUT", "Workspace must be a directory.")
        self.output_root = self._path(str(output_root), must_exist=False)
        if self.output_root == self.workspace:
            raise ServiceError("INVALID_INPUT", "Use a dedicated output directory within the workspace.")
        self.max_bytes, self.max_records = max_bytes, max_records
        self.page_size, self.max_excerpt_chars = page_size, max_excerpt_chars
        self.output_root.mkdir(parents=True, exist_ok=True)

    def _path(self, value: str, *, must_exist: bool = True) -> Path:
        if not isinstance(value, str) or not value or "\0" in value:
            raise ServiceError("INVALID_INPUT", "Expected a nonempty workspace path.")
        path = Path(value)
        if ".." in path.parts:
            raise ServiceError("INVALID_INPUT", "Parent traversal is not allowed.")
        path = path if path.is_absolute() else self.workspace / path
        # Check every component below the workspace, including internal symlinks.
        try:
            relative = path.relative_to(self.workspace)
        except ValueError as exc:
            raise ServiceError("INVALID_INPUT", "Path is outside the configured workspace.") from exc
        cursor = self.workspace
        for part in relative.parts:
            cursor = cursor / part
            if cursor.is_symlink():
                raise ServiceError("INVALID_INPUT", "Symlinked paths are not supported.")
        resolved = path.resolve()
        if not resolved.is_relative_to(self.workspace):
            raise ServiceError("INVALID_INPUT", "Path escapes the workspace.")
        if must_exist and not resolved.exists():
            raise ServiceError("NOT_FOUND", "Workspace input does not exist.")
        return resolved

    def _new_attempt(self, inspection: bool) -> Path:
        root = self._path(str(self.output_root), must_exist=True)
        parent = root / ("inspections" if inspection else "audits")
        self._path(str(parent), must_exist=False).mkdir(exist_ok=True)
        attempt = parent / uuid4().hex
        attempt.mkdir()  # exclusive; requests never share an unfinished directory
        return attempt

    @staticmethod
    def _json(path: Path) -> dict:
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(value, dict):
                raise ValueError("object required")
            return value
        except (ValueError, UnicodeError, RecursionError) as exc:
            raise ServiceError("INVALID_INPUT", "Expected a supported JSON object; archives are unsupported.") from exc

    def _copy_inputs(self, source: str, annotations: str | None, attempt: Path):
        path = self._path(source)
        if path.is_dir():
            names = ("bundle.json",) if (path / "bundle.json").exists() else (
                "rows.jsonl", "comparisons.json", "meta.json", "items.jsonl")
            files = [self._path(str(path / name)) for name in names if (path / name).exists() or (path / name).is_symlink()]
            if not files:
                raise ServiceError("INVALID_INPUT", "Directory has no supported bundle files.")
        elif path.is_file() and path.suffix.lower() in {".json", ".eval"}:
            files = [path]
        else:
            raise ServiceError("INVALID_INPUT", "Expected a JSON bundle or supported bundle directory.")
        ann = self._path(annotations) if annotations is not None else None
        if ann is not None and (not ann.is_file() or ann.suffix != ".jsonl"):
            raise ServiceError("INVALID_INPUT", "Annotations must be a JSONL file.")
        all_files = files + ([ann] if ann else [])
        if sum(f.stat().st_size for f in all_files) > self.max_bytes:
            raise ServiceError("SIZE_LIMIT", "Input byte limit exceeded before parsing.")
        copies = attempt / "source"
        copies.mkdir()
        hashes, total = {}, 0
        for index, original in enumerate(all_files):
            # Also cap the read itself in case a file grows after stat().
            with original.open("rb") as stream:
                payload = stream.read(self.max_bytes - total + 1)
            total += len(payload)
            if total > self.max_bytes:
                raise ServiceError("SIZE_LIMIT", "Input byte limit exceeded during capture.")
            name = "annotations.jsonl" if ann is not None and index == len(files) else original.name
            if name == "annotations.jsonl" and index < len(files):
                raise ServiceError("INVALID_INPUT", "Reserved input filename.")
            (copies / name).write_bytes(payload)
            hashes[name] = sha256_bytes(payload)
        copied_source = copies if path.is_dir() else copies / path.name
        return copied_source, copies / "annotations.jsonl" if ann else None, hashes

    def _import(self, source: Path, format: str, attempt: Path):
        if format not in {"generic", "inspect", "lm-eval"}:
            raise ServiceError("INVALID_INPUT", "Format must be generic, inspect, or lm-eval.")
        if source.is_dir() and not (source / "bundle.json").exists():
            rows_path = source / "rows.jsonl"
            if not rows_path.is_file() or not (source / "comparisons.json").is_file():
                raise ServiceError("INVALID_INPUT", "Directory requires rows.jsonl and comparisons.json.")
            count = sum(bool(line.strip()) for line in rows_path.read_text().splitlines())
            comparisons = json.loads((source / "comparisons.json").read_text(encoding="utf-8"))
            comparisons = comparisons.get("comparisons", []) if isinstance(comparisons, dict) else comparisons
            if format != "generic":
                raise ServiceError("INVALID_INPUT", "Log adapters require paired JSON files.")
        else:
            payload = self._json(source / "bundle.json" if source.is_dir() else source)
            if format != "generic":
                from eval_audit.paired_logs import paired_bundle
                payload = paired_bundle(payload, format, self.max_records)
                source = attempt / "derived-bundle.json"
                source.write_text(json.dumps(payload), encoding="utf-8")
            rows = payload.get("rows")
            if not isinstance(rows, list):
                raise ServiceError("INVALID_INPUT", "Expected rows array.")
            count, comparisons = len(rows), payload.get("comparisons", [])
        if count > self.max_records:
            raise ServiceError("SIZE_LIMIT", "Record limit exceeded before audit computation.")
        if not isinstance(comparisons, list) or len(comparisons) > self.max_records:
            raise ServiceError("SIZE_LIMIT", "Comparison limit exceeded or invalid comparison list.")
        manifest = load_generic(source, attempt / "dataset")
        return manifest

    def _prepare(self, source: str, format: str, annotations: str | None, attempt: Path):
        copied, annotation, hashes = self._copy_inputs(source, annotations, attempt)
        manifest = self._import(copied, format, attempt)
        return manifest, annotation, hashes

    @staticmethod
    def _write_json(path: Path, payload: dict):
        with path.open("x", encoding="utf-8") as stream:
            json.dump(payload, stream, indent=2, allow_nan=False)
            stream.write("\n")

    def _failure(self, attempt: Path, exc: Exception):
        error = exc if isinstance(exc, ServiceError) else ServiceError(
            "INVALID_INPUT" if isinstance(exc, (AuditInputError, ValueError, TypeError, KeyError, UnicodeError))
            else "PROCESSING_FAILURE", "Input validation failed." if isinstance(exc, AuditInputError)
            else f"Audit did not complete ({type(exc).__name__}).")
        try:
            self._write_json(attempt / "failure.json", {"status": "failed", "error": error.as_dict()})
        except OSError:
            pass  # Failure to persist diagnostics must never create a completion receipt.
        return error

    def inspect_bundle(self, source: str, format: str = "generic") -> dict:
        attempt = self._new_attempt(True)
        try:
            manifest, _, hashes = self._prepare(source, format, None, attempt)
            _, records = read_dataset(attempt / "dataset/manifest.json")
            return {"status": "inspected", "record_count": len(records),
                    "comparison_count": len(manifest.comparisons), "source_hashes": hashes,
                    "answer_bases": ["stored", "strict"],
                    "limitations": ["Inspection validates structure; no audit or behavioral verdict was produced."]}
        except Exception as exc:
            raise self._failure(attempt, exc) from exc

    def run_audit(self, source: str, format: str = "generic", annotations: str | None = None) -> dict:
        attempt = self._new_attempt(False)
        try:
            _, annotation, hashes = self._prepare(source, format, annotations, attempt)
            report = audit_manifest(attempt / "dataset/manifest.json", attempt / "report", annotation)
            if report.audit_status != "complete":
                raise ServiceError("INVALID_INPUT", "Comparison could not be audited completely; diagnostic output retained.")
            payload = self._json(attempt / "report/report.json")
            if payload.get("audit_status") != "complete":
                raise ServiceError("PROCESSING_FAILURE", "Output validation failed.")
            artifacts = {str(p.relative_to(attempt)): sha256_bytes(p.read_bytes())
                         for p in (attempt / "report").rglob("*") if p.is_file()}
            # Stable across retries/concurrent requests. An artifact is not a new model run.
            fingerprint = sha256_bytes(json.dumps(hashes, sort_keys=True).encode())
            receipt = {"receipt_version": 1, "status": "complete", "audit_id": attempt.name,
                       "created_utc": datetime.now(timezone.utc).isoformat(), "format": format,
                       "source_hashes": hashes, "same_source_group": fingerprint,
                       "artifacts": artifacts}
            summary = self._summary(receipt, payload)
            # Publish receipt atomically. Readers ignore a partial receipt on process failure.
            pending = attempt / "completion.pending.json"
            self._write_json(pending, receipt)
            pending.rename(attempt / "completion.json")
            return summary
        except Exception as exc:
            raise self._failure(attempt, exc) from exc

    def _finding(self, finding: dict) -> dict:
        # Human annotations / observed values may contain response text. Full content
        # remains in explicitly requested reports, never in routine summaries.
        keys = ("finding_id", "code", "severity", "scope", "answer_basis", "origin")
        result = {key: finding[key] for key in keys}
        result["sources"] = finding["sources"][:self.page_size]
        result["source_count"] = len(finding["sources"])
        if finding["origin"] == "computed":
            for key in ("explanation", "limitation"):
                result[key] = finding[key][:self.max_excerpt_chars]
        return result

    def _summary(self, receipt: dict, report: dict) -> dict:
        return {"audit_id": receipt["audit_id"], "status": "complete",
                "source_hashes": receipt["source_hashes"], "same_source_group": receipt["same_source_group"],
                "model_runs_executed": 0, "input_format": receipt["format"],
                "provenance_notes": [note[:self.max_excerpt_chars] for note in report["manifest"]["provenance_notes"][:self.page_size]],
                "inventory": report["inventory"],
                "answer_bases": ["stored", "strict"], "gates": report["gates"][:self.page_size],
                "group_metrics": report["group_metrics"][:self.page_size],
                "comparison_metrics": report["comparison_metrics"][:self.page_size],
                "finding_count": len(report["findings"]),
                "findings": [self._finding(f) for f in report["findings"][:self.page_size]],
                "next_findings_offset": self.page_size if len(report["findings"]) > self.page_size else None,
                "limitations": ["Saved MCQ diagnostics only; behavioral claims remain unestablished.",
                                 "Matching same_source_group means replayed source evidence, not independent model runs.",
                                 "Summary metric lists are bounded; read the JSON report for all scopes."],
                "reports": {fmt: f"audit://{receipt['audit_id']}/report/{fmt}" for fmt in ("json", "markdown")}}

    def _completed(self, audit_id: str):
        if not isinstance(audit_id, str) or re.fullmatch(r"[0-9a-f]{32}", audit_id) is None:
            raise ServiceError("NOT_FOUND", "Unknown audit identifier.")
        attempt = self._path(str(self.output_root / "audits" / audit_id))
        receipt_path = self._path(str(attempt / "completion.json"))
        try:
            receipt = self._json(receipt_path)
            if receipt.get("status") != "complete" or receipt.get("audit_id") != audit_id or receipt.get("receipt_version") != 1:
                raise ValueError("receipt mismatch")
            path = self._artifact(attempt, receipt, "report/report.json")
            return attempt, receipt, self._json(path)
        except (KeyError, ValueError) as exc:
            raise ServiceError("PROCESSING_FAILURE", "Invalid completion receipt.") from exc

    def _artifact(self, attempt: Path, receipt: dict, name: str):
        path = self._path(str(attempt / name))
        expected = receipt.get("artifacts", {}).get(name)
        if not path.is_file() or expected != sha256_bytes(path.read_bytes()):
            raise ServiceError("PROCESSING_FAILURE", "Completed artifact failed integrity verification.")
        return path

    def findings_page(self, audit_id: str, offset: int = 0) -> dict:
        if type(offset) is not int or offset < 0:
            raise ServiceError("INVALID_INPUT", "Offset must be a nonnegative integer.")
        _, _, report = self._completed(audit_id)
        entries = report["findings"]
        end = offset + self.page_size
        return {"audit_id": audit_id, "offset": offset, "total": len(entries),
                "findings": [self._finding(f) for f in entries[offset:end]],
                "next_offset": end if end < len(entries) else None}

    def get_finding(self, audit_id: str, finding_id: str, include_raw: bool = False) -> dict:
        if type(include_raw) is not bool:
            raise ServiceError("INVALID_INPUT", "include_raw must be boolean.")
        _, _, report = self._completed(audit_id)
        finding = next((f for f in report["findings"] if f["finding_id"] == finding_id), None)
        if finding is None:
            raise ServiceError("NOT_FOUND", "Unknown finding identifier.")
        result = self._finding(finding)
        if include_raw:
            sources = finding["sources"]
            rows = [row for row in report["records"] if row["source"] in sources]
            remaining, excerpts = self.max_excerpt_chars, []
            for row in rows[:self.page_size]:
                raw = row.get("response_text")
                text = raw[:remaining] if isinstance(raw, str) else None
                remaining -= len(text or "")
                excerpts.append({"source": row["source"], "response_text": text,
                                 "truncated": isinstance(raw, str) and len(raw) > len(text or "")})
            result["excerpts"] = excerpts
            result["excerpt_record_count"] = len(rows)
        return result

    def export_report(self, audit_id: str, format: str = "markdown") -> dict:
        if format not in {"markdown", "json"}:
            raise ServiceError("INVALID_INPUT", "Report format must be markdown or json.")
        attempt, receipt, _ = self._completed(audit_id)
        name = "report/report." + ("md" if format == "markdown" else "json")
        path = self._artifact(attempt, receipt, name)
        return {"audit_id": audit_id, "format": format, "path": str(path.relative_to(self.workspace)),
                "uri": f"audit://{audit_id}/report/{format}", "sha256": receipt["artifacts"][name],
                "bytes": path.stat().st_size}
