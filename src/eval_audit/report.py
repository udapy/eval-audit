"""Traceable Markdown/JSON reports. Rendering never rereads mutable sources."""

from __future__ import annotations

import html
import json
import re
from collections.abc import Sequence
from fractions import Fraction
from pathlib import Path
from typing import Any

from eval_audit.checks import comparison_bundle, run_checks
from eval_audit.identity import stable_id
from eval_audit.io import atomic_directory, dump_json, dumps_json, resolve_inside, sha256_bytes
from eval_audit.loaders import load_annotation_file, manifest_to_dict, read_dataset, read_item_context, record_to_dict
from eval_audit.metrics import summarize
from eval_audit.schema import (
    SCHEMA_VERSION,
    Annotation,
    AuditInputError,
    AuditReport,
    ComparisonMetrics,
    ControlResult,
    Finding,
    GroupMetrics,
    ItemContext,
    ItemInfluence,
    Manifest,
    Record,
)


def build_report(
    rows: Sequence[Record],
    manifest: Manifest,
    *,
    item_context: Sequence[ItemContext] = (),
    annotations: Sequence[Annotation] = (),
    extra_findings: Sequence[Finding] = (),
) -> AuditReport:
    scopes = {(row.dataset_id, row.item_id) for row in rows}
    datasets = {row.dataset_id for row in rows}
    annotation_ids: set[str] = set()
    for ann in annotations:
        ann.validate()
        if ann.annotation_id in annotation_ids:
            raise AuditInputError("duplicate annotation_id", field="annotation_id")
        annotation_ids.add(ann.annotation_id)
        if ann.dataset_id not in datasets or (ann.item_id is not None and (ann.dataset_id, ann.item_id) not in scopes):
            raise AuditInputError("annotation scope does not match audited records", field="annotation.scope")
    groups: list[GroupMetrics] = []
    seen: set[tuple[str, str, str, str, str]] = set()
    for record in rows:
        key = (record.dataset_id, record.model_label, record.run_id, record.condition, "stored")
        if key in seen:
            continue
        seen.add(key)
        subset = [
            row
            for row in rows
            if (row.dataset_id, row.model_label, row.run_id, row.condition) == key[:4]
        ]
        groups.append(summarize(subset, "stored"))
        groups.append(summarize(subset, "strict"))

    comparisons, controls, influence, statuses, pair_findings = comparison_bundle(rows, manifest)
    findings = list(run_checks(rows, manifest, item_context=item_context, annotations=annotations))
    findings.extend(pair_findings)
    findings.extend(extra_findings)
    audit_status = "complete"
    if any(status == "invalid" for status in statuses.values()):
        audit_status = "invalid"
    elif any(status == "insufficient_data" for status in statuses.values()):
        audit_status = "insufficient_data"
    inventory = {
        "n_records": len(rows),
        "n_artifacts": len(manifest.artifacts),
        "normalized_sha256": manifest.normalized_sha256,
        "item_context_sha256": manifest.item_context_sha256,
        "annotations_sha256": manifest.annotations_sha256,
        "artifact_sha256": {artifact.artifact_id: artifact.sha256 for artifact in manifest.artifacts},
        "comparison_status": statuses,
    }
    return AuditReport(
        schema_version=SCHEMA_VERSION,
        audit_status=audit_status,
        manifest=manifest,
        records=tuple(rows),
        item_context=tuple(item_context),
        annotations=tuple(annotations),
        group_metrics=tuple(groups),
        comparison_metrics=tuple(comparisons),
        controls=tuple(controls),
        item_influence=tuple(influence),
        findings=tuple(findings),
        inventory=inventory,
    )


def write_report(report: AuditReport, out_dir: Path, *, input_files: dict[str, bytes] | None = None) -> None:
    with atomic_directory(out_dir) as stage:
        _write_report(report, stage)
        for name, payload in (input_files or {}).items():
            target = resolve_inside(stage / "inputs" / name, stage / "inputs", field="inputs")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(payload)


def _write_report(report: AuditReport, out_dir: Path) -> None:
    evidence_dir = out_dir / "evidence"
    items_dir = evidence_dir / "items"
    findings_dir = evidence_dir / "findings"
    items_dir.mkdir(parents=True)
    findings_dir.mkdir(parents=True)

    context_index = {(item.dataset_id, item.item_id): item for item in report.item_context}
    item_pages: dict[tuple[str, str], str] = {}
    for record in report.records:
        key = (record.dataset_id, record.item_id)
        if key in item_pages:
            continue
        rel = Path("evidence") / "items" / f"{_safe_id(stable_id('item', *key))}.md"
        item_pages[key] = rel.as_posix()
        related = [row for row in report.records if (row.dataset_id, row.item_id) == key]
        (out_dir / rel).write_text(
            _item_page(related, context_index.get(key), report.annotations),
            encoding="utf-8",
        )

    finding_pages: dict[str, str] = {}
    for finding in report.findings:
        if finding.finding_id in finding_pages:
            raise AuditInputError("duplicate finding_id would overwrite evidence", field="finding_id")
        rel = Path("evidence") / "findings" / f"{_safe_id(finding.finding_id)}.md"
        finding_pages[finding.finding_id] = rel.as_posix()
        (out_dir / rel).write_text(_finding_page(finding, item_pages), encoding="utf-8")

    markdown = _markdown_report(report, item_pages, finding_pages)
    json_payload = report_to_jsonable(report, item_pages, finding_pages)
    (out_dir / "report.md").write_text(markdown, encoding="utf-8")
    dump_json(out_dir / "report.json", json_payload)
    status_name = "COMPLETE" if report.audit_status == "complete" else "INCOMPLETE"
    (out_dir / "STATUS.txt").write_text(f"{status_name}\naudit_status={report.audit_status}\n", encoding="utf-8")


def load_annotations(path: Path, data_dir: Path | None = None) -> list[Annotation]:
    """Load and validate annotations.jsonl. `data_dir` is unused; kept for call-site compatibility."""
    _ = data_dir
    resolved = path.resolve()
    return load_annotation_file(resolved)


def report_to_jsonable(
    report: AuditReport,
    item_pages: dict[tuple[str, str], str],
    finding_pages: dict[str, str],
) -> dict[str, Any]:
    from eval_audit.gates import evaluate_gates

    return {
        "gates": evaluate_gates(report),
        "schema_version": report.schema_version,
        "audit_status": report.audit_status,
        "manifest": manifest_to_dict(report.manifest),
        "inventory": report.inventory,
        "group_metrics": [_group_json(m) for m in report.group_metrics],
        "comparison_metrics": [_comparison_json(m) for m in report.comparison_metrics],
        "controls": [
            {
                "control_id": c.control_id,
                "comparison_id": c.comparison_id,
                "answer_basis": c.answer_basis,
                "label": c.label,
                "metrics": _comparison_json(c.metrics),
            }
            for c in report.controls
        ],
        "item_influence": [_influence_json(row) for row in report.item_influence],
        "findings": [
            {
                "finding_id": f.finding_id,
                "code": f.code,
                "severity": f.severity,
                "scope": f.scope,
                "answer_basis": f.answer_basis,
                "observed": _jsonable(f.observed),
                "sources": [s.__dict__ for s in f.sources],
                "explanation": f.explanation,
                "limitation": f.limitation,
                "origin": f.origin,
                "evidence": finding_pages.get(f.finding_id),
            }
            for f in report.findings
        ],
        "item_pages": {json.dumps(k, ensure_ascii=False, separators=(",", ":")): v for k, v in item_pages.items()},
        "records": [record_to_dict(record) for record in report.records],
        "item_context": [item.__dict__ for item in report.item_context],
        "annotations": [ann.__dict__ for ann in report.annotations],
    }


def _markdown_report(
    report: AuditReport,
    item_pages: dict[tuple[str, str], str],
    finding_pages: dict[str, str],
) -> str:
    lines: list[str] = []
    if report.audit_status != "complete":
        lines.append(f"# INCOMPLETE AUDIT (`{report.audit_status}`)")
        lines.append("")
        lines.append("This directory is not a complete successful audit.")
        lines.append("")
    lines.append("# Eval Audit report")
    lines.append("")
    lines.append("Deterministic offline report. No timestamps. Synthetic controls are labeled as controls.")
    lines.append("")
    lines.append("## 1. Input and provenance")
    lines.append("")
    lines.append(f"- audit status: `{report.audit_status}`")
    lines.append(f"- profile: `{report.manifest.profile}`")
    lines.append(f"- adapter: `{report.manifest.adapter_version}`")
    lines.append(f"- normalized sha256: `{report.manifest.normalized_sha256}`")
    lines.append(f"- records: {len(report.records)}")
    lines.append("")
    lines.append("| artifact | sha256 | rows | labels |")
    lines.append("| --- | --- | ---: | --- |")
    for artifact in report.manifest.artifacts:
        labels = ", ".join(f"{k}={v}" for k, v in artifact.assigned_labels.items())
        lines.append(
            f"| `{artifact.artifact_id}` | `{artifact.sha256}` | {artifact.row_count} | {_cell(labels)} |"
        )
    lines.append("")
    lines.append("Provenance notes:")
    for note in report.manifest.provenance_notes:
        lines.append(f"- {_cell(note)}")
    if not report.manifest.provenance_notes:
        lines.append("- (none)")
    lines.append("")
    lines.append("## 2. Historical results (stored answers)")
    lines.append("")
    lines.append("| dataset | model | run | condition | n_total | n_valid | n_correct | accuracy_all | entropy_bits | pred counts |")
    lines.append("| --- | --- | --- | --- | ---: | ---: | ---: | --- | --- | --- |")
    for metrics in report.group_metrics:
        if metrics.answer_basis != "stored":
            continue
        lines.append(
            "| {dataset} | {model} | {run} | {cond} | {n} | {v} | {c} | {acc} | {ent} | {pred} |".format(
                dataset=_cell(metrics.dataset_id),
                model=_cell(metrics.model_label),
                run=_cell(metrics.run_id),
                cond=_cell(metrics.condition),
                n=metrics.n_total,
                v=metrics.n_valid,
                c=metrics.n_correct,
                acc=_frac_md(metrics.accuracy_all),
                ent=_float_md(metrics.entropy_bits),
                pred=_counts_md(metrics.prediction_counts),
            )
        )
    lines.append("")
    lines.append("Paired comparisons:")
    lines.append("")
    lines.append("| id | basis | status | n_pairs | acc drop | acc flag | entropy drop | entropy flag | selectivity |")
    lines.append("| --- | --- | --- | ---: | --- | --- | --- | --- | --- |")
    for metrics in report.comparison_metrics:
        lines.append(
            "| {id} | {basis} | {status} | {n} | {ad} | {af} | {ed} | {ef} | {sel} |".format(
                id=_cell(metrics.comparison_id),
                basis=metrics.answer_basis,
                status=metrics.status,
                n=metrics.n_pairs,
                ad=_frac_md(metrics.accuracy_drop),
                af=_bool_md(metrics.accuracy_flag),
                ed=_float_md(metrics.entropy_drop),
                ef=_bool_md(metrics.entropy_flag),
                sel=_frac_md(metrics.selectivity),
            )
        )
    lines.append("")
    lines.append("## 3. Diagnostic controls")
    lines.append("")
    lines.append("Gold-oracle and constant-letter answerers keep the historical baseline and replace the target answers. They are not model rows.")
    lines.append("")
    lines.append("| comparison | control | n | accuracy_all | entropy | entropy drop | entropy flag |")
    lines.append("| --- | --- | ---: | --- | --- | --- | --- |")
    for control in report.controls:
        target = control.metrics.target
        lines.append(
            "| {cmp} | {ctrl} | {n} | {acc} | {ent} | {ed} | {ef} |".format(
                cmp=_cell(control.comparison_id),
                ctrl=_cell(control.label),
                n=target.n_total if target else 0,
                acc=_frac_md(target.accuracy_all if target else None),
                ent=_float_md(target.entropy_bits if target else None),
                ed=_float_md(control.metrics.entropy_drop),
                ef=_bool_md(control.metrics.entropy_flag),
            )
        )
    lines.append("")
    lines.append("## 4. Item influence")
    lines.append("")
    lines.append("Leave-one-item-out applies to both conditions. Post-hoc exclusion is sensitivity analysis, not a repaired primary result.")
    lines.append("")
    lines.append("| comparison | item | orig acc drop | without | Δ acc | orig selectivity | without | Δ sel | evidence |")
    lines.append("| --- | --- | --- | --- | --- | --- | --- | --- | --- |")
    for row in report.item_influence:
        page = item_pages.get(( _dataset_for(report, row.comparison_id), row.item_id), "")
        link = f"[item]({page})" if page else ""
        lines.append(
            "| {cmp} | {item} | {oa} | {wa} | {da} | {os} | {ws} | {ds} | {ev} |".format(
                cmp=_cell(row.comparison_id),
                item=_cell(row.item_id),
                oa=_frac_md(row.original_accuracy_drop),
                wa=_frac_md(row.without_accuracy_drop),
                da=_frac_md(row.accuracy_drop_difference),
                os=_frac_md(row.original_selectivity),
                ws=_frac_md(row.without_selectivity),
                ds=_frac_md(row.selectivity_difference),
                ev=link,
            )
        )
    lines.append("")
    lines.append("## 5. Parsing and missing fields")
    lines.append("")
    lines.append("| basis | dataset | run | condition | n_total | n_valid | n_invalid | accuracy_all |")
    lines.append("| --- | --- | --- | --- | ---: | ---: | ---: | --- |")
    for metrics in report.group_metrics:
        if metrics.answer_basis != "strict":
            continue
        lines.append(
            f"| strict | {_cell(metrics.dataset_id)} | {_cell(metrics.run_id)} | {_cell(metrics.condition)} | {metrics.n_total} | {metrics.n_valid} | {metrics.n_invalid} | {_frac_md(metrics.accuracy_all)} |"
        )
    lines.append("")
    parse_findings = [f for f in report.findings if f.code == "STORED_STRICT_DISAGREEMENT"]
    lines.append(f"Stored vs strict disagreements / notable parses: {len(parse_findings)}")
    for finding in parse_findings:
        page = finding_pages.get(finding.finding_id, "")
        loc = f"{finding.scope.get('run_id','')} {finding.scope.get('condition','')} {finding.scope.get('item_id','')}".strip()
        lines.append(f"- [{_cell(loc)}]({page}) status={finding.observed.get('parse_status')}")
    if not parse_findings:
        lines.append("- none")
    lines.append("")
    lines.append("## 6. Gold uniqueness annotations")
    lines.append("")
    lines.append(
        "Frozen rubric: `unique-correct` / `contested` / `invalid-key` / `insufficient-evidence`. "
        "Rationale text is required. Status is `proposed` or `reviewed`. "
        "Annotations never change accuracy, entropy, selectivity, gold, stored, or parsed answers."
    )
    lines.append("")
    gold_anns = [ann for ann in report.annotations]
    if not gold_anns:
        lines.append("No annotations attached. A `MISSING_ANNOTATIONS` warning is recorded. Scores are unchanged.")
        lines.append("")
    else:
        lines.append("| id | dataset | item | gold_uniqueness | status | origin | author |")
        lines.append("| --- | --- | --- | --- | --- | --- | --- |")
        for ann in gold_anns:
            item = ann.item_id or ""
            verdict = ann.gold_uniqueness or ""
            lines.append(
                f"| {_cell(ann.annotation_id)} | {_cell(ann.dataset_id)} | {_cell(item)} | "
                f"{_cell(verdict)} | {_cell(ann.status)} | {_cell(ann.origin)} | {_cell(ann.author)} |"
            )
        lines.append("")
        for finding in report.findings:
            if finding.code != "HUMAN_ANNOTATION":
                continue
            page = finding_pages.get(finding.finding_id, "")
            verdict = finding.observed.get("gold_uniqueness") or ""
            loc = f"{finding.scope.get('dataset_id','')} {finding.scope.get('item_id','')}".strip()
            lines.append(f"- [{_cell(loc)} `{verdict}`]({page}) status={finding.observed.get('status')} origin={finding.observed.get('origin')}")
        lines.append("")
        lines.extend(_reviewed_key_sensitivity_lines(report, item_pages))
    lines.append("## 7. Limits on interpretation")
    lines.append("")
    lines.extend(
        [
            f"- Historical flags reproduce `{report.manifest.profile}` strict inequalities (accuracy drop > 1/10, entropy drop > 0.15). Equality is not a flag.",
            "- A gold oracle or constant answerer can trigger the entropy heuristic on skewed keys. That is a measurement failure, not a detector of hidden intent.",
            "- Leave-one-item-out is a diagnostic. It does not repair gold keys or establish that an effect is absent.",
            "- Model labels inferred from folder names are not verified snapshots. Missing prompts, finish reasons, and timestamps stay unknown.",
            "- Item definitions are source-code literals labeled `source_definition_not_verified_request`.",
            "- Retrospective recognition/verbal fields are stored observations, not internal awareness.",
            "- These convenience samples do not support statistical significance or population claims.",
            "- Human annotations, if present, are labeled `HUMAN_ANNOTATION` and do not change scores.",
            "- A missing annotation file is a warning (`MISSING_ANNOTATIONS`), not a repaired or worsened score.",
            "- Gold-uniqueness verdicts are inspectable labels. They are not automatic semantic gold adjudication and do not overwrite keys.",
            "- Reviewed `contested` / `invalid-key` items may be listed again as leave-one-item-out sensitivity. That listing does not drop them from the primary table.",
        ]
    )
    lines.append("")
    lines.append("## 8. Evidence index")
    lines.append("")
    for finding in report.findings:
        page = finding_pages.get(finding.finding_id, "")
        lines.append(
            f"- `{finding.severity}` `{finding.code}` [{_cell(finding.finding_id)}]({page}) origin={finding.origin}"
        )
    if not report.findings:
        lines.append("- (no findings)")
    lines.append("")
    return "\n".join(lines) + "\n"


def _item_page(rows: Sequence[Record], context: ItemContext | None, annotations: Sequence[Annotation]) -> str:
    first = rows[0]
    lines = [
        f"# Item `{first.dataset_id}` / `{first.item_id}`",
        "",
        f"- dataset: `{first.dataset_id}`",
        f"- item: `{first.item_id}`",
        f"- bank: `{first.bank}`",
        f"- gold (stored): `{first.gold}`",
        "",
        "## Question / options (source definition)",
        "",
    ]
    if context is None:
        lines.append("No item context was supplied.")
        lines.append("")
    else:
        lines.append(f"- provenance: `{context.provenance_status}`")
        lines.append(f"- locator: `{context.source_locator}`")
        lines.append(f"- definition gold: `{context.definition_gold}`")
        lines.append("")
        lines.append(inert_pre(context.question_with_options))
        lines.append("")
    lines.append("## Observations")
    lines.append("")
    for record in rows:
        lines.extend(
            [
                f"### `{record.model_label}` `{record.run_id}` `{record.condition}`",
                "",
                f"- stored_answer: `{record.stored_answer}`",
                f"- stored_correct: `{record.stored_correct}`",
                f"- parse_status: `{record.parse_status}` parsed_answer: `{record.parsed_answer}`",
                f"- completeness: `{record.response_completeness}`",
                f"- source: `{record.source.artifact_id}` `{record.source.json_pointer}` `{record.source.sha256}`",
                "",
                "Stored response text:",
                "",
                inert_pre(record.response_text if record.response_text is not None else ""),
                "",
            ]
        )
    relevant = [
        ann
        for ann in annotations
        if ann.dataset_id == first.dataset_id and (ann.item_id is None or ann.item_id == first.item_id)
    ]
    if relevant:
        lines.append("## Human annotations")
        lines.append("")
        for ann in relevant:
            verdict = ann.gold_uniqueness or ""
            lines.append(
                f"- `{ann.annotation_id}` author={_cell(ann.author)} status={ann.status} "
                f"origin={ann.origin} gold_uniqueness={_cell(verdict)}"
            )
            lines.append("")
            lines.append(inert_pre(ann.text))
            lines.append("")
    return "\n".join(lines) + "\n"


def _finding_page(finding: Finding, item_pages: dict[tuple[str, str], str]) -> str:
    item_id = finding.scope.get("item_id")
    dataset_id = finding.scope.get("dataset_id")
    item_link = ""
    if item_id and dataset_id:
        rel = item_pages.get((dataset_id, item_id))
        if rel:
            item_link = f"[item page]({Path('..') / 'items' / Path(rel).name})"
    lines = [
        f"# Finding `{finding.finding_id}`",
        "",
        f"- code: `{finding.code}`",
        f"- severity: `{finding.severity}`",
        f"- origin: `{finding.origin}`",
        f"- answer_basis: `{finding.answer_basis}`",
        f"- scope: `{json.dumps(finding.scope, sort_keys=True)}`",
        "",
        "## Explanation",
        "",
        inert_pre(finding.explanation),
        "",
        "## Limitation",
        "",
        inert_pre(finding.limitation),
        "",
        "## Observed values",
        "",
        inert_pre(json.dumps(_jsonable(finding.observed), indent=2, sort_keys=True, allow_nan=False)),
        "",
    ]
    if finding.sources:
        lines.append("## Sources")
        lines.append("")
        for source in finding.sources:
            lines.append(f"- `{source.artifact_id}` `{source.json_pointer}` `{source.sha256}`")
        lines.append("")
    if item_link:
        lines.append(item_link)
        lines.append("")
    return "\n".join(lines) + "\n"


def inert_pre(text: str) -> str:
    escaped = html.escape(text, quote=True).replace("</pre>", "&lt;/pre&gt;")
    return f"<pre>{escaped}</pre>"


def _safe_id(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", value)
    return (cleaned[:40] or "id") + "-" + sha256_bytes(value.encode("utf-8"))


def _cell(value: str) -> str:
    return html.escape(value, quote=True).replace("|", "\\|").replace("\n", " ").replace("[", "\\[").replace("]", "\\]")


def _frac_md(value: Fraction | None) -> str:
    if value is None:
        return "null"
    return f"{value.numerator}/{value.denominator}"


def _float_md(value: float | None) -> str:
    if value is None:
        return "null"
    return f"{value:.16g}"


def _bool_md(value: bool | None) -> str:
    if value is None:
        return "null"
    return "true" if value else "false"


def _counts_md(counts: dict[str, int]) -> str:
    return " ".join(f"{k}:{v}" for k, v in counts.items())


def _group_json(metrics: GroupMetrics) -> dict[str, Any]:
    return {
        "dataset_id": metrics.dataset_id,
        "model_label": metrics.model_label,
        "run_id": metrics.run_id,
        "condition": metrics.condition,
        "bank": metrics.bank,
        "answer_basis": metrics.answer_basis,
        "n_total": metrics.n_total,
        "n_valid": metrics.n_valid,
        "n_invalid": metrics.n_invalid,
        "n_correct": metrics.n_correct,
        "accuracy_all": _frac_json(metrics.accuracy_all),
        "accuracy_valid": _frac_json(metrics.accuracy_valid),
        "prediction_counts": metrics.prediction_counts,
        "gold_counts": metrics.gold_counts,
        "entropy_bits": metrics.entropy_bits,
    }


def _comparison_json(metrics: ComparisonMetrics) -> dict[str, Any]:
    return {
        "comparison_id": metrics.comparison_id,
        "answer_basis": metrics.answer_basis,
        "status": metrics.status,
        "n_pairs": metrics.n_pairs,
        "baseline": _group_json(metrics.baseline) if metrics.baseline else None,
        "target": _group_json(metrics.target) if metrics.target else None,
        "accuracy_drop": _frac_json(metrics.accuracy_drop),
        "entropy_drop": metrics.entropy_drop,
        "accuracy_flag": metrics.accuracy_flag,
        "entropy_flag": metrics.entropy_flag,
        "selectivity": _frac_json(metrics.selectivity),
    }


def _influence_json(row: ItemInfluence) -> dict[str, Any]:
    return {
        "comparison_id": row.comparison_id,
        "item_id": row.item_id,
        "answer_basis": row.answer_basis,
        "original_accuracy_drop": _frac_json(row.original_accuracy_drop),
        "without_accuracy_drop": _frac_json(row.without_accuracy_drop),
        "accuracy_drop_difference": _frac_json(row.accuracy_drop_difference),
        "original_entropy_drop": row.original_entropy_drop,
        "without_entropy_drop": row.without_entropy_drop,
        "entropy_drop_difference": row.entropy_drop_difference,
        "original_selectivity": _frac_json(row.original_selectivity),
        "without_selectivity": _frac_json(row.without_selectivity),
        "selectivity_difference": _frac_json(row.selectivity_difference),
    }


def _frac_json(value: Fraction | None) -> dict[str, int] | None:
    if value is None:
        return None
    return {"numerator": value.numerator, "denominator": value.denominator}


def _reviewed_key_sensitivity_lines(report: AuditReport, item_pages: dict[tuple[str, str], str]) -> list[str]:
    """Leave-one-item-out rows for reviewed contested/invalid keys. Not a primary repair."""
    flagged = [
        ann
        for ann in report.annotations
        if ann.status == "reviewed"
        and ann.origin == "human"
        and ann.item_id
        and ann.gold_uniqueness in {"contested", "invalid-key"}
    ]
    lines = [
        "### Reviewed contested / invalid-key sensitivity",
        "",
        "Primary scores above are unchanged. Leave-one-item-out rows for reviewed "
        "`contested` or `invalid-key` items are sensitivity only. Exclusion is not a "
        "repaired primary result.",
        "",
    ]
    if not flagged:
        lines.append("No reviewed contested or invalid-key items.")
        lines.append("")
        return lines
    ids = {(ann.dataset_id, ann.item_id) for ann in flagged}
    rows = [row for row in report.item_influence if (_dataset_for(report, row.comparison_id), row.item_id) in ids]
    if not rows:
        lines.append("Reviewed contested items have no paired influence rows in this audit.")
        lines.append("")
        return lines
    lines.append("| comparison | item | orig selectivity | without | Δ sel | orig acc drop | without |")
    lines.append("| --- | --- | --- | --- | --- | --- | --- |")
    for row in rows:
        page = item_pages.get((_dataset_for(report, row.comparison_id), row.item_id), "")
        item_cell = f"[{_cell(row.item_id)}]({page})" if page else _cell(row.item_id)
        lines.append(
            "| {cmp} | {item} | {os} | {ws} | {ds} | {oa} | {wa} |".format(
                cmp=_cell(row.comparison_id),
                item=item_cell,
                os=_frac_md(row.original_selectivity),
                ws=_frac_md(row.without_selectivity),
                ds=_frac_md(row.selectivity_difference),
                oa=_frac_md(row.original_accuracy_drop),
                wa=_frac_md(row.without_accuracy_drop),
            )
        )
    lines.append("")
    return lines


def _jsonable(value: Any) -> Any:
    if isinstance(value, Fraction):
        return _frac_json(value)
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(v) for v in value]
    if isinstance(value, float) and value != value:
        raise AuditInputError("NaN is not allowed in JSON output", field="observed")
    return value


def _dataset_for(report: AuditReport, comparison_id: str) -> str:
    for comparison in report.manifest.comparisons:
        if comparison.comparison_id == comparison_id:
            return comparison.dataset_id
    return ""


def capture_inputs(manifest_path: Path, manifest: Manifest, annotation_bytes: bytes | None = None) -> dict[str, bytes]:
    """Capture hash-checked bytes for portable replay before atomic publication."""
    root = manifest_path.resolve().parent
    captured = {"manifest.json": dumps_json(manifest_to_dict(manifest)).encode("utf-8")}
    specs = [(a.copied_relative_path, a.sha256) for a in manifest.artifacts]
    specs.append((manifest.normalized_file, manifest.normalized_sha256))
    if manifest.item_context_file:
        specs.append((manifest.item_context_file, manifest.item_context_sha256))
    if manifest.annotations_file:
        specs.append((manifest.annotations_file, manifest.annotations_sha256))
    for name, expected in specs:
        relative = Path(name)
        if relative.is_absolute() or ".." in relative.parts or relative.as_posix() == "manifest.json":
            raise AuditInputError("unsafe or reserved input bundle path", field="inputs")
        path = resolve_inside(root / relative, root, field="inputs")
        payload = annotation_bytes if annotation_bytes is not None and name == manifest.annotations_file else path.read_bytes()
        if sha256_bytes(payload) != expected:
            raise AuditInputError("input changed while capturing report", field=name)
        key = relative.as_posix()
        if key in captured and captured[key] != payload:
            raise AuditInputError("conflicting input bundle paths", field=name)
        captured[key] = payload
    return captured
