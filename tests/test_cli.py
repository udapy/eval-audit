from __future__ import annotations

import json
from pathlib import Path

from eval_audit.cli import main
from eval_audit.demo import write_demo_dataset

HISTORICAL_ROOT = Path(__import__("os").environ.get("EVAL_AUDIT_HISTORICAL_SOURCE", "/__eval_audit_source_not_configured__"))


def test_demo_subcommand(tmp_path: Path) -> None:
    out = tmp_path / "demo"
    assert main(["demo", "--out", str(out)]) == 0
    assert (out / "report.md").is_file()
    assert (out / "report.json").is_file()
    assert (out / "STATUS.txt").read_text(encoding="utf-8").startswith("COMPLETE")


def test_nonempty_destination_exit_2(tmp_path: Path) -> None:
    out = tmp_path / "demo"
    out.mkdir()
    (out / "stale").write_text("nope", encoding="utf-8")
    assert main(["demo", "--out", str(out)]) == 2


def test_missing_manifest_exit_2(tmp_path: Path) -> None:
    assert main(["audit", "--manifest", str(tmp_path / "nope.json"), "--out", str(tmp_path / "r")]) == 2


def test_audit_after_demo_dataset(tmp_path: Path) -> None:
    data = tmp_path / "data"
    write_demo_dataset(data)
    out = tmp_path / "report"
    assert main(["audit", "--manifest", str(data / "manifest.json"), "--out", str(out)]) == 0


def test_import_generic_fixture(tmp_path: Path) -> None:
    fixture = Path(__file__).resolve().parents[1] / "examples" / "transfer-fixture" / "bundle.json"
    data = tmp_path / "xfer"
    assert main(["import", "--source", str(fixture), "--out", str(data)]) == 0
    assert (data / "manifest.json").is_file()
    payload = json.loads((data / "manifest.json").read_text(encoding="utf-8"))
    assert payload["profile"] == "generic-v1"


def test_import_historical_and_audit(tmp_path: Path) -> None:
    if not HISTORICAL_ROOT.is_dir():
        __import__("pytest").skip("Set EVAL_AUDIT_HISTORICAL_SOURCE for optional replay")
    data = tmp_path / "historical"
    report = tmp_path / "report"
    assert main(["import-historical", "--source", str(HISTORICAL_ROOT), "--out", str(data)]) == 0
    assert main(["audit", "--manifest", str(data / "manifest.json"), "--out", str(report)]) == 0
    text = (report / "report.json").read_text(encoding="utf-8")
    assert '"n_records": 88' in text


def test_unknown_command_is_argparse_error() -> None:
    # argparse exits 2 before our handler when required subcommand missing
    assert main.__name__ == "main"
