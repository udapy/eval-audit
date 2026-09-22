"""Unit tests for reusable AI safety evaluation audit tooling.

Covers:
1. One-line claim audit scorecard (eval-audit check)
2. Inspect AI log adapter (load_inspect_eval)
3. lm-evaluation-harness log adapter (load_lm_eval)
4. RunPod provider client abstraction
"""

from __future__ import annotations

import json
from pathlib import Path
import pytest

from eval_audit.cli import cmd_check
from eval_audit.inspect_ai import load_inspect_eval
from eval_audit.lm_eval import load_lm_eval
from eval_audit.providers.runpod import RunPodProvider


def test_cmd_check_clean_bundle(tmp_path: Path) -> None:
    bundle = {
        "profile": "generic-v1",
        "defaults": {"model_label": "test-model"},
        "comparisons": [
            {
                "comparison_id": "CLEAN-COMP",
                "dataset_id": "ds1",
                "model_label": "test-model",
                "run_id": "RUN1",
                "baseline_condition": "base",
                "target_condition": "cue",
            }
        ],
        "items": [
            {
                "dataset_id": "ds1",
                "item_id": f"i{k}",
                "definition_gold": g,
                "question_with_options": f"Q{k}\nA) 1\nB) 2\nC) 3\nD) 4",
                "source_locator": f"loc:{k}",
                "provenance_status": "test",
            }
            for k, g in enumerate(["A", "B", "C", "D"], 1)
        ],
        "rows": [
            {
                "dataset_id": "ds1",
                "model_label": "test-model",
                "run_id": "RUN1",
                "item_id": f"i{k}",
                "condition": cond,
                "stored_answer": g,
                "response_text": f"ANSWER: {g}",
                "response_completeness": "complete",
                "gold": g,
                "allowed_answers": ["A", "B", "C", "D"],
            }
            for cond in ("base", "cue")
            for k, g in enumerate(["A", "B", "C", "D"], 1)
        ],
    }
    bundle_file = tmp_path / "bundle.json"
    bundle_file.write_text(json.dumps(bundle))

    exit_code = cmd_check(bundle_file)
    assert exit_code == 0


def test_cmd_check_skewed_oracle_fails_g2(tmp_path: Path) -> None:
    # 9 B and 1 C gold keys (skewed)
    golds = ["B"] * 9 + ["C"]
    bundle = {
        "profile": "generic-v1",
        "defaults": {"model_label": "test-model"},
        "comparisons": [
            {
                "comparison_id": "SKEW-COMP",
                "dataset_id": "ds_skew",
                "model_label": "test-model",
                "run_id": "RUN_SKEW",
                "baseline_condition": "base",
                "target_condition": "cue",
            }
        ],
        "items": [
            {
                "dataset_id": "ds_skew",
                "item_id": f"s{k}",
                "definition_gold": g,
                "question_with_options": f"Q{k}",
                "source_locator": f"loc:{k}",
                "provenance_status": "test",
            }
            for k, g in enumerate(golds, 1)
        ],
        "rows": [
            # Baseline is uniform A/B/C/D
            {
                "dataset_id": "ds_skew",
                "model_label": "test-model",
                "run_id": "RUN_SKEW",
                "item_id": f"s{k}",
                "condition": "base",
                "stored_answer": ["A", "B", "C", "D"][k % 4],
                "response_text": f"ANSWER: {['A', 'B', 'C', 'D'][k % 4]}",
                "response_completeness": "complete",
                "gold": g,
                "allowed_answers": ["A", "B", "C", "D"],
            }
            for k, g in enumerate(golds, 1)
        ]
        + [
            # Cue follows the skewed gold keys exactly (oracle drop > 0.15)
            {
                "dataset_id": "ds_skew",
                "model_label": "test-model",
                "run_id": "RUN_SKEW",
                "item_id": f"s{k}",
                "condition": "cue",
                "stored_answer": g,
                "response_text": f"ANSWER: {g}",
                "response_completeness": "complete",
                "gold": g,
                "allowed_answers": ["A", "B", "C", "D"],
            }
            for k, g in enumerate(golds, 1)
        ],
    }
    bundle_file = tmp_path / "skewed.json"
    bundle_file.write_text(json.dumps(bundle))

    exit_code = cmd_check(bundle_file)
    assert exit_code == 2


def test_inspect_ai_adapter(tmp_path: Path) -> None:
    inspect_log = {
        "eval": {
            "model": "openai/gpt-4o-mini",
            "task": "mmlu_cybersecurity",
            "run_id": "INSPECT_RUN_01",
        },
        "samples": [
            {
                "id": "item_01",
                "input": "Which cipher is asymmetric?",
                "target": "A",
                "choices": ["RSA", "AES", "DES", "Blowfish"],
                "output": {
                    "choices": [
                        {"message": {"content": "ANSWER: A"}}
                    ]
                },
            },
            {
                "id": "item_02",
                "input": "Standard SSH port?",
                "target": "B",
                "choices": ["21", "22", "80", "443"],
                "output": {
                    "choices": [
                        {"message": {"content": "ANSWER: B"}}
                    ]
                },
            },
        ],
    }
    log_file = tmp_path / "sample.eval"
    log_file.write_text(json.dumps(inspect_log))

    out_dir = tmp_path / "inspect_imported"
    manifest = load_inspect_eval(log_file, out_dir)
    assert manifest.profile == "generic-v1"
    assert len(manifest.artifacts) == 1
    assert (out_dir / "manifest.json").is_file()
    assert (out_dir / "normalized.jsonl").is_file()


def test_lm_eval_adapter(tmp_path: Path) -> None:
    lm_eval_dump = {
        "config": {"model_name": "meta-llama/Llama-3.1-8B"},
        "samples": {
            "arc_easy": [
                {
                    "doc_id": 101,
                    "target": 0,  # 0 -> 'A'
                    "arguments": ["Question text here"],
                    "resps": [["ANSWER: A"]],
                },
                {
                    "doc_id": 102,
                    "target": 2,  # 2 -> 'C'
                    "arguments": ["Another question"],
                    "resps": [["ANSWER: C"]],
                },
            ]
        },
    }
    dump_file = tmp_path / "lm_eval_output.json"
    dump_file.write_text(json.dumps(lm_eval_dump))

    out_dir = tmp_path / "lm_eval_imported"
    manifest = load_lm_eval(dump_file, out_dir)
    assert manifest.profile == "generic-v1"
    assert len(manifest.artifacts) == 1
    assert (out_dir / "manifest.json").is_file()
    assert (out_dir / "normalized.jsonl").is_file()


def test_runpod_provider_init() -> None:
    provider = RunPodProvider(api_key="rpa_dummy", endpoint_id="ep_123")
    assert provider.api_key == "rpa_dummy"
    assert provider.endpoint_id == "ep_123"

    prompt = provider._messages_to_prompt([
        {"role": "user", "content": "Hello"},
    ])
    assert "User: Hello" in prompt
    assert "Assistant:" in prompt
