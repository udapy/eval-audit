#!/usr/bin/env python3
"""HF Inference API helper — stdlib only (urllib).

Sends chat completion requests to https://router.huggingface.co/v1/chat/completions
for generating real model responses on benchmark items.

No eval_audit imports. No external dependencies.
"""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.request
import urllib.error
from typing import Any


HF_TOKEN = os.environ.get("HF_TOKEN", "")
HF_INFERENCE_URL = "https://router.huggingface.co/v1/chat/completions"
DEFAULT_DELAY = 1.0  # seconds between requests


def chat_completion(
    *,
    model: str,
    messages: list[dict[str, str]],
    max_tokens: int = 256,
    temperature: float = 0.0,
    retries: int = 3,
) -> dict[str, Any]:
    """Send a chat completion request to HF Inference API.
    
    Returns the full API response dict.
    Raises on persistent failure.
    """
    payload = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    body = json.dumps(payload).encode("utf-8")

    for attempt in range(retries):
        try:
            req = urllib.request.Request(
                HF_INFERENCE_URL,
                data=body,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {HF_TOKEN}",
                },
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=60) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < retries - 1:
                wait = (attempt + 1) * 15
                print(f"  [rate limited, waiting {wait}s...]", file=sys.stderr)
                time.sleep(wait)
            elif e.code in (500, 502, 503) and attempt < retries - 1:
                wait = (attempt + 1) * 5
                print(f"  [server error {e.code}, retrying in {wait}s...]", file=sys.stderr)
                time.sleep(wait)
            else:
                raise
        except (urllib.error.URLError, TimeoutError) as e:
            if attempt < retries - 1:
                wait = (attempt + 1) * 5
                print(f"  [connection error, retrying in {wait}s...]", file=sys.stderr)
                time.sleep(wait)
            else:
                raise

    raise RuntimeError("all retries exhausted")


def extract_answer_text(response: dict[str, Any]) -> str:
    """Extract the assistant's message content from a chat completion response."""
    choices = response.get("choices", [])
    if not choices:
        return ""
    msg = choices[0].get("message", {})
    content = msg.get("content")
    if content:
        return content
    reasoning = msg.get("reasoning_content")
    if reasoning:
        return reasoning
    return ""


def mcq_baseline_prompt(
    *,
    question: str,
    options: list[str],
    option_labels: list[str] | None = None,
) -> list[dict[str, str]]:
    """Build a standard MCQ baseline prompt (no hints, no leaks).
    
    Returns messages list for chat completion.
    """
    if option_labels is None:
        option_labels = ["A", "B", "C", "D"][:len(options)]
    
    options_text = "\n".join(
        f"{label}) {text}" for label, text in zip(option_labels, options)
    )

    return [
        {
            "role": "system",
            "content": (
                "You are answering a multiple-choice question. "
                "Reply with ONLY the letter of the correct answer (e.g., 'A', 'B', 'C', or 'D'). "
                "Do not explain your reasoning."
            ),
        },
        {
            "role": "user",
            "content": f"{question}\n\n{options_text}",
        },
    ]


def mcq_leaked_answer_prompt(
    *,
    question: str,
    options: list[str],
    gold_key: str,
    option_labels: list[str] | None = None,
) -> list[dict[str, str]]:
    """Build an answer-key leak prompt (gold answer leaked in system message).
    
    This creates the gold-oracle condition: the model should reproduce the gold key.
    Used to test Gate G2 (oracle degeneracy) on controlled data.
    """
    if option_labels is None:
        option_labels = ["A", "B", "C", "D"][:len(options)]
    
    options_text = "\n".join(
        f"{label}) {text}" for label, text in zip(option_labels, options)
    )

    return [
        {
            "role": "system",
            "content": (
                "You are answering a multiple-choice question. "
                f"The correct answer to this question is {gold_key}. "
                "Reply with ONLY the letter of the correct answer. "
                "Do not explain your reasoning."
            ),
        },
        {
            "role": "user",
            "content": f"{question}\n\n{options_text}",
        },
    ]


def run_mcq_inference(
    *,
    model: str,
    items: list[dict[str, Any]],
    delay: float = DEFAULT_DELAY,
    verbose: bool = True,
) -> list[dict[str, Any]]:
    """Run baseline + leaked-answer inference on a list of MCQ items.
    
    Each item must have:
      - item_id: str
      - question: str
      - options: list[str]
      - gold: str (e.g., "A", "B", "C", "D")
      - option_labels: list[str] (optional, defaults to A/B/C/D)
    
    Returns a list of result dicts with fields:
      - item_id, gold, condition, stored_answer, response_text, response_completeness
    """
    results: list[dict[str, Any]] = []
    n = len(items)

    for i, item in enumerate(items):
        item_id = item["item_id"]
        question = item["question"]
        options = item["options"]
        gold = item["gold"]
        labels = item.get("option_labels", ["A", "B", "C", "D"][:len(options)])

        # ── Baseline ──
        if verbose:
            print(f"  [{i+1}/{n}] {item_id} baseline...", end=" ", flush=True)
        
        baseline_msgs = mcq_baseline_prompt(question=question, options=options, option_labels=labels)
        baseline_resp = chat_completion(model=model, messages=baseline_msgs, max_tokens=64, temperature=0.0)
        baseline_text = extract_answer_text(baseline_resp)
        
        # Extract single letter from response
        baseline_letter = _extract_letter(baseline_text, labels)

        if verbose:
            print(f"→ {baseline_letter}", end="  ", flush=True)

        time.sleep(delay)

        # ── Leaked answer (cue) ──
        if verbose:
            print(f"cue...", end=" ", flush=True)
        
        cue_msgs = mcq_leaked_answer_prompt(
            question=question, options=options, gold_key=gold, option_labels=labels,
        )
        cue_resp = chat_completion(model=model, messages=cue_msgs, max_tokens=64, temperature=0.0)
        cue_text = extract_answer_text(cue_resp)
        cue_letter = _extract_letter(cue_text, labels)

        if verbose:
            correct = "✓" if cue_letter == gold else "✗"
            print(f"→ {cue_letter} (gold={gold}) {correct}")

        time.sleep(delay)

        results.append({
            "item_id": item_id,
            "gold": gold,
            "baseline_text": baseline_text,
            "baseline_letter": baseline_letter,
            "cue_text": cue_text,
            "cue_letter": cue_letter,
        })

    return results


def _extract_letter(text: str, valid_labels: list[str]) -> str | None:
    """Extract a single answer letter from model response text."""
    text = text.strip()
    
    # Direct single letter
    if len(text) == 1 and text.upper() in valid_labels:
        return text.upper()
    
    # "A)" or "A." or "(A)" patterns
    for label in valid_labels:
        if text.upper().startswith(label):
            return label
    
    # Search for standalone letter
    import re
    for label in valid_labels:
        if re.search(rf'\b{label}\b', text.upper()):
            return label
    
    # Last resort: first character
    if text and text[0].upper() in valid_labels:
        return text[0].upper()
    
    return None


if __name__ == "__main__":
    # Quick smoke test
    if not HF_TOKEN:
        print("ERROR: HF_TOKEN not set", file=sys.stderr)
        sys.exit(1)
    
    print("Smoke test: single MCQ inference...")
    items = [{
        "item_id": "test_01",
        "question": "What is 2 + 2?",
        "options": ["3", "4", "5", "6"],
        "gold": "B",
    }]
    results = run_mcq_inference(
        model="meta-llama/Llama-3.1-8B-Instruct",
        items=items,
        delay=0.5,
    )
    print(f"\nResult: {json.dumps(results[0], indent=2)}")
    print(f"\nBaseline letter: {results[0]['baseline_letter']}")
    print(f"Cue letter: {results[0]['cue_letter']} (gold: {results[0]['gold']})")
    print("Smoke test passed!" if results[0]["cue_letter"] == "B" else "WARNING: Cue did not follow leaked answer")
