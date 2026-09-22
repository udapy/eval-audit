"""CLI: import, import-historical, audit, demo. Offline; no credentials; no network."""

from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path

from eval_audit import __version__
from eval_audit.io import refuse_nonempty
from eval_audit.generic import load_generic
from eval_audit.loaders import load_historical
from eval_audit.schema import AuditError, AuditInputError, PairingError


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="eval-audit", description="Offline evaluation-validity audit")
    parser.add_argument("--version", action="version", version=__version__)
    sub = parser.add_subparsers(dest="command", required=True)

    generic_p = sub.add_parser("import", help="Import a generic JSON/JSONL MCQ bundle (Historical-agnostic)")
    generic_p.add_argument("--source", required=True, type=Path)
    generic_p.add_argument("--out", required=True, type=Path)

    import_p = sub.add_parser("import-historical", help="Import the four pinned Historical result files plus item definitions")
    import_p.add_argument("--source", required=True, type=Path)
    import_p.add_argument("--out", required=True, type=Path)

    audit_p = sub.add_parser("audit", help="Audit a previously imported (or synthetic) dataset")
    audit_p.add_argument("--manifest", required=True, type=Path)
    audit_p.add_argument("--out", required=True, type=Path)
    audit_p.add_argument("--annotations", type=Path, default=None)

    demo_p = sub.add_parser("demo", help="Run the bundled synthetic demo (no Historical data required)")
    demo_p.add_argument("--out", required=True, type=Path)

    triage_p = sub.add_parser("triage", help="Generate a blinded human adjudication queue for influential/divergent items")
    triage_p.add_argument("--manifest", required=True, type=Path)
    triage_p.add_argument("--out", required=True, type=Path)

    check_p = sub.add_parser("check", help="Engineering audit scorecard (exit 0=no blocking G0/G2 finding, 2=blocked)")
    check_p.add_argument("source", type=Path, help="Path to evaluation bundle or log file")
    check_p.add_argument("--format", choices=["generic", "inspect", "lm-eval"], default="generic", help="Input format (default: generic)")
    check_p.add_argument("--annotations", type=Path, default=None, help="Optional human annotations file")

    args = parser.parse_args(argv)
    try:
        if args.command == "import":
            return cmd_import_generic(args.source, args.out)
        if args.command == "import-historical":
            return cmd_import_historical(args.source, args.out)
        if args.command == "audit":
            return cmd_audit(args.manifest, args.out, args.annotations)
        if args.command == "demo":
            return cmd_demo(args.out)
        if args.command == "triage":
            return cmd_triage(args.manifest, args.out)
        if args.command == "check":
            return cmd_check(args.source, format_name=args.format, annotations_path=args.annotations)
        raise AuditInputError(f"unknown command {args.command}", field="command")
    except PairingError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    except AuditInputError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    except AuditError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except Exception as exc:  # noqa: BLE001 — CLI boundary
        print(f"unexpected failure: {type(exc).__name__}", file=sys.stderr)
        return 1


def cmd_import_generic(source: Path, out: Path) -> int:
    manifest = load_generic(source, out)
    n_rows = sum(artifact.row_count for artifact in manifest.artifacts)
    print(f"imported {n_rows} rows into {out} profile={manifest.profile}")
    return 0


def cmd_import_historical(source: Path, out: Path) -> int:
    manifest = load_historical(source, out)
    n_rows = sum(artifact.row_count for artifact in manifest.artifacts)
    print(f"imported {n_rows} rows into {out}")
    return 0


def cmd_audit(manifest_path: Path, out: Path, annotations_path: Path | None) -> int:
    from eval_audit.service import audit_manifest

    report = audit_manifest(manifest_path, out, annotations_path)
    print(f"wrote {out / 'report.md'} status={report.audit_status}")
    if report.audit_status == "invalid":
        return 2
    return 0


def cmd_demo(out: Path) -> int:
    from eval_audit.demo import write_demo_dataset

    refuse_nonempty(out)
    with tempfile.TemporaryDirectory(prefix="eval-audit-demo-") as tmp:
        staging = Path(tmp)
        write_demo_dataset(staging)
        code = cmd_audit(staging / "manifest.json", out, None)
        return code


def cmd_triage(manifest_path: Path, out_file: Path) -> int:
    from eval_audit.triage import write_triage_queue

    n = write_triage_queue(manifest_path, out_file)
    print(f"queued {n} items for blinded adjudication into {out_file}")
    return 0


def cmd_check(source: Path, format_name: str = "generic", annotations_path: Path | None = None) -> int:
    import json

    resolved_source = source.resolve()
    if not resolved_source.exists():
        raise AuditInputError(f"source file does not exist: {resolved_source}", field="source")

    with tempfile.TemporaryDirectory(prefix="eval-audit-check-data-") as tmp_data, \
         tempfile.TemporaryDirectory(prefix="eval-audit-check-out-") as tmp_out:
        data_dir = Path(tmp_data)
        out_dir = Path(tmp_out)

        if format_name in {"inspect", "lm-eval"}:
            from eval_audit.paired_logs import paired_bundle
            if resolved_source.stat().st_size > 10 * 1024 * 1024:
                raise AuditInputError("Log byte limit exceeded", field="source")
            payload = json.loads(resolved_source.read_text(encoding="utf-8"))
            if not isinstance(payload, dict):
                raise AuditInputError("Paired log must be a JSON object", field="source")
            paired = paired_bundle(payload, format_name, 2000)
            derived = data_dir / "paired-bundle.json"
            derived.write_text(json.dumps(paired), encoding="utf-8")
            manifest = load_generic(derived, data_dir / "normalized")
            data_dir = data_dir / "normalized"
        elif format_name == "generic":
            manifest = load_generic(resolved_source, data_dir)
        else:
            raise AuditInputError("Unsupported input format", field="format")

        manifest_path = data_dir / "manifest.json"
        cmd_audit(manifest_path, out_dir, annotations_path)

        report_json_path = out_dir / "report.json"
        if not report_json_path.is_file():
            print("Failed to produce audit report.", file=sys.stderr)
            return 1

        report = json.loads(report_json_path.read_text(encoding="utf-8"))
        records = report.get("records", [])
        gate_sets = report.get("gates", [])

        print()
        print("=" * 72)
        print(f"EVAL-AUDIT SCORECARD: {resolved_source.name}")
        print("=" * 72)
        print(f"Profile: {manifest.profile} | Comparisons: {len(gate_sets)} | Rows: {len(records)}")

        blocked = report.get("audit_status") != "complete" or not gate_sets
        for entry in gate_sets:
            print(f"Comparison: {entry['comparison_id']} (stored answer basis)")
            for name, gate in entry["gates"].items():
                print(f"  {name}: {gate['status']} ({', '.join(gate['codes'])})")
            if any(entry["gates"][g]["status"] in {"FLAGGED", "INSUFFICIENT_DATA"}
                   for g in ("G0", "G2")):
                blocked = True
        print("=" * 72)
        print("G1/G3 diagnostics are advisory; G4 requires human interpretation.")
        if blocked:
            print("AUDIT CHECK: BLOCKED (exit code 2). Review diagnostics and evidence.")
            return 2
        print("AUDIT CHECK: no blocking G0/G2 finding (exit code 0). Behavioral claims remain unestablished.")
        return 0


def entrypoint() -> None:
    raise SystemExit(main())

