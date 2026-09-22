"""Tests for blinded adjudication triage workflow."""

from __future__ import annotations

import json
from pathlib import Path
import pytest

from eval_audit.cli import main
from eval_audit.triage import generate_triage_queue, write_triage_queue


def test_triage_queue_generation(tmp_path: Path) -> None:
    bundle_path = Path("examples/external-eval/bundle.json").resolve()
    data_dir = tmp_path / "data"
    queue_file = tmp_path / "queue.jsonl"

    ret_import = main(["import", "--source", str(bundle_path), "--out", str(data_dir)])
    assert ret_import == 0

    # Test Python API
    queue = generate_triage_queue(data_dir / "manifest.json")
    assert len(queue) >= 2
    item_ids = {entry["item_id"] for entry in queue}
    assert "cs01" in item_ids  # High LOO influence
    assert "cs09" in item_ids  # Parse disagreement

    # Test CLI command
    ret_cli = main(["triage", "--manifest", str(data_dir / "manifest.json"), "--out", str(queue_file)])
    assert ret_cli == 0
    assert queue_file.is_file()

    entries = [json.loads(line) for line in queue_file.read_text(encoding="utf-8").splitlines() if line]
    assert len(entries) == len(queue)
    for entry in entries:
        assert "declared_gold" in entry
        assert "question_with_options" in entry
        assert len(entry["blinded_raters"]) == 2
        # Blinding: model_label, condition, and run_id must not be exposed to raters
        assert "model_label" not in entry
        assert "condition" not in entry
        assert "historical_score" not in entry
