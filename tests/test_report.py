from __future__ import annotations

from pathlib import Path

from eval_audit.demo import write_demo_dataset
from eval_audit.loaders import read_dataset, read_item_context
from eval_audit.report import build_report, inert_pre, write_report
from eval_audit.schema import Annotation


def test_report_links_and_stable_json(tmp_path: Path) -> None:
    data = tmp_path / "data"
    write_demo_dataset(data)
    manifest, records = read_dataset(data / "manifest.json")
    context = read_item_context(manifest, data)
    report = build_report(records, manifest, item_context=context)
    out = tmp_path / "report1"
    write_report(report, out)
    md = (out / "report.md").read_text(encoding="utf-8")
    js = (out / "report.json").read_text(encoding="utf-8")
    assert "NaN" not in js
    assert "Infinity" not in js
    assert "[item](evidence/items/" in md or "evidence/items/" in md
    assert (out / "evidence" / "items").is_dir()
    # portable relative links
    for line in md.splitlines():
        if "](" in line:
            assert "http://" not in line
            assert "/Users/" not in line
    out2 = tmp_path / "report2"
    write_report(report, out2)
    assert (out / "report.md").read_text(encoding="utf-8") == (out2 / "report.md").read_text(encoding="utf-8")
    assert (out / "report.json").read_text(encoding="utf-8") == (out2 / "report.json").read_text(encoding="utf-8")


def test_malicious_text_is_inert() -> None:
    payload = 'hello <script>alert(1)</script> [click](https://evil.example) ```\ncode\n```'
    rendered = inert_pre(payload)
    assert "<script>" not in rendered
    assert "&lt;script&gt;" in rendered
    assert rendered.startswith("<pre>")
    assert rendered.endswith("</pre>")


def test_annotations_do_not_change_scores(tmp_path: Path) -> None:
    data = tmp_path / "data"
    write_demo_dataset(data)
    manifest, records = read_dataset(data / "manifest.json")
    context = read_item_context(manifest, data)
    clean = build_report(records, manifest, item_context=context)
    annotated = build_report(
        records,
        manifest,
        item_context=context,
        annotations=(
            Annotation(
                annotation_id="a1",
                dataset_id="demo-skewed",
                item_id="k1",
                text="human note",
                author="reviewer",
                status="proposed",
                origin="human",
                gold_uniqueness="contested",
            ),
        ),
    )
    assert [m.n_correct for m in clean.group_metrics] == [m.n_correct for m in annotated.group_metrics]
    assert any(f.origin == "human_annotation" for f in annotated.findings)


def test_reviewed_contested_lists_sensitivity_without_changing_scores(tmp_path: Path) -> None:
    data = tmp_path / "data"
    write_demo_dataset(data)
    manifest, records = read_dataset(data / "manifest.json")
    context = read_item_context(manifest, data)
    out = tmp_path / "report"
    annotated = build_report(
        records,
        manifest,
        item_context=context,
        annotations=(
            Annotation(
                annotation_id="rev1",
                dataset_id="demo-skewed",
                item_id="k1",
                text="reviewed contested",
                author="reviewer",
                status="reviewed",
                origin="human",
                gold_uniqueness="contested",
            ),
        ),
    )
    clean = build_report(records, manifest, item_context=context)
    assert [m.n_correct for m in clean.group_metrics] == [m.n_correct for m in annotated.group_metrics]
    write_report(annotated, out)
    md = (out / "report.md").read_text(encoding="utf-8")
    assert "Reviewed contested / invalid-key sensitivity" in md
    assert "| D-skewed | [k1]" in md or "| D-skewed | k1 |" in md
    proposed = build_report(
        records,
        manifest,
        item_context=context,
        annotations=(
            Annotation(
                annotation_id="p1",
                dataset_id="demo-skewed",
                item_id="k1",
                text="still proposed",
                author="reviewer",
                status="proposed",
                origin="human",
                gold_uniqueness="contested",
            ),
        ),
    )
    write_report(proposed, tmp_path / "proposed")
    proposed_md = (tmp_path / "proposed" / "report.md").read_text(encoding="utf-8")
    assert "No reviewed contested or invalid-key items." in proposed_md
