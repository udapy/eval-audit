from dataclasses import replace
from pathlib import Path
import json

import pytest

from eval_audit.cli import main
from eval_audit.demo import write_demo_dataset
from eval_audit.loaders import read_dataset
from eval_audit.report import build_report, write_report, _reviewed_key_sensitivity_lines
from eval_audit.schema import AuditInputError
from tests.helpers import make_annotation, make_record


def demo(tmp_path):
    write_demo_dataset(tmp_path / "data")
    return read_dataset(tmp_path / "data/manifest.json")


def test_evidence_names_do_not_collapse_punctuation_or_long_ids(tmp_path):
    manifest, _ = demo(tmp_path)
    ids = ["a/b", "a_b", "x" * 150 + "a", "x" * 150 + "b"]
    records = [make_record(item_id=i, text="unparseable") for i in ids]
    report = build_report(records, replace(manifest, comparisons=()))
    write_report(report, tmp_path / "report")
    payload = json.loads((tmp_path / "report/report.json").read_text())
    assert len(set(payload["item_pages"].values())) == len(ids)
    assert len(list((tmp_path / "report/evidence/items").glob("*.md"))) == len(ids)
    assert len(set(f["evidence"] for f in payload["findings"])) == len(report.findings)


def test_failed_render_never_publishes_partial_report(tmp_path, monkeypatch):
    import eval_audit.report as renderer
    manifest, rows = demo(tmp_path)
    report = build_report(rows, manifest)
    def fail(*args):
        raise RuntimeError("injected render failure")
    monkeypatch.setattr(renderer, "_markdown_report", fail)
    with pytest.raises(RuntimeError, match="injected"):
        write_report(report, tmp_path / "report")
    assert not (tmp_path / "report").exists()


def test_unknown_annotation_scope_rejected(tmp_path):
    manifest, rows = demo(tmp_path)
    with pytest.raises(AuditInputError, match="scope"):
        build_report(rows, manifest, annotations=[make_annotation(dataset_id="missing")])


def test_reviewed_sensitivity_does_not_cross_datasets(tmp_path):
    manifest, rows = demo(tmp_path)
    other = [replace(r, dataset_id="other") for r in rows if r.dataset_id == "demo-skewed"]
    original = next(c for c in manifest.comparisons if c.dataset_id == "demo-skewed")
    manifest = replace(manifest, comparisons=manifest.comparisons + (replace(original, dataset_id="other", comparison_id="other-comparison"),))
    report = build_report(rows + other, manifest, annotations=[make_annotation(dataset_id="demo-skewed", item_id="k1", status="reviewed")])
    lines = "\n".join(_reviewed_key_sensitivity_lines(report, {}))
    assert "D-skewed" in lines
    assert "other-comparison" not in lines


def test_cli_report_contains_replayable_verified_inputs(tmp_path):
    demo(tmp_path)
    assert main(["audit", "--manifest", str(tmp_path / "data/manifest.json"), "--out", str(tmp_path / "report")]) == 0
    manifest, rows = read_dataset(tmp_path / "report/inputs/manifest.json")
    assert len(rows) == 16
    assert main(["audit", "--manifest", str(tmp_path / "report/inputs/manifest.json"), "--out", str(tmp_path / "replay")]) == 0
    assert (tmp_path / "report/report.json").read_bytes() == (tmp_path / "replay/report.json").read_bytes()


def test_option_order_requires_complete_unique_metadata():
    for order, content in [(('one',), 'one'), (('one', 'one', 'two', 'three'), 'one'), (None, 'one')]:
        with pytest.raises(AuditInputError):
            replace(make_record(), option_order=order, gold_content_id=content).validate()
