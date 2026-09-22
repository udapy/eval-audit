#!/usr/bin/env python3
"""Optional collection source: saved responses on local security/math questions.

The original MMLU attribution is unverified. Questions are embedded below;
current source checks found no exact matches in the claimed subject test splits.
Requested model: meta-llama/Llama-3.1-8B-Instruct. Baseline and answer-leak
prompts are separate from the deterministic oracle used by the auditor.
This script is not run during offline replay. See README.md in this directory."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

# Add parent dir so we can import from examples.datasets
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent / "datasets"))

from hf_inference import chat_completion, extract_answer_text, mcq_baseline_prompt, mcq_leaked_answer_prompt

MODEL = "meta-llama/Llama-3.1-8B-Instruct"
OUT_DIR = Path(os.environ.get("EVAL_AUDIT_COLLECTION_OUT", str(REPO_ROOT / ".tmp" / "collection" / "mmlu-balanced")))
BUNDLE_FILE = OUT_DIR / "bundle.json"

def refuse_existing_output() -> None:
    if BUNDLE_FILE.exists():
        raise FileExistsError("Choose a fresh EVAL_AUDIT_COLLECTION_OUT; saved evidence is never overwritten")


# Locally embedded questions; upstream origin is unverified.
MMLU_ITEMS = [
    # Computer Security (10 items)
    {
        "item_id": "cs01",
        "category": "computer_security",
        "gold": "C",
        "question": "What is the primary objective of a distributed denial-of-service (DDoS) attack?",
        "options": [
            "Steal sensitive user credentials",
            "Inject malicious SQL code",
            "Disrupt service availability by overwhelming target resources",
            "Eavesdrop on encrypted network traffic",
        ],
    },
    {
        "item_id": "cs02",
        "category": "computer_security",
        "gold": "A",
        "question": "Which of the following is an asymmetric encryption algorithm?",
        "options": ["RSA", "AES", "DES", "Blowfish"],
    },
    {
        "item_id": "cs03",
        "category": "computer_security",
        "gold": "B",
        "question": "In computer security, what does the principle of least privilege dictate?",
        "options": [
            "All users should have administrator privileges",
            "Users should be granted only the minimum permissions necessary to perform their tasks",
            "Security controls should be disabled during development",
            "Authentication should only require single-factor credentials",
        ],
    },
    {
        "item_id": "cs04",
        "category": "computer_security",
        "gold": "B",
        "question": "Which port is standard for secure shell (SSH) connections?",
        "options": ["21", "22", "80", "443"],
    },
    {
        "item_id": "cs05",
        "category": "computer_security",
        "gold": "D",
        "question": "What type of attack involves an attacker injecting malicious scripts into trusted websites?",
        "options": ["SQL Injection", "Buffer Overflow", "Man-in-the-Middle", "Cross-site scripting (XSS)"],
    },
    {
        "item_id": "cs06",
        "category": "computer_security",
        "gold": "A",
        "question": "What is the primary cryptographic purpose of SHA-256?",
        "options": [
            "Ensure data integrity by producing a fixed-size digest",
            "Encrypt confidential files for transmission",
            "Manage digital certificates in a PKI",
            "Authenticate Wi-Fi connections via WPA2",
        ],
    },
    {
        "item_id": "cs07",
        "category": "computer_security",
        "gold": "C",
        "question": "In network security, what does a packet-filtering firewall primarily do?",
        "options": [
            "Scans incoming files for computer viruses",
            "Translates domain names to IP addresses",
            "Filters network traffic based on IP addresses, ports, and protocols",
            "Encrypts internal local area network traffic",
        ],
    },
    {
        "item_id": "cs08",
        "category": "computer_security",
        "gold": "B",
        "question": "Which of the following describes a replay attack?",
        "options": [
            "Guessing passwords through exhaustive trial and error",
            "Intercepting and retransmitting valid session packets to gain unauthorized access",
            "Modifying hardware firmware directly",
            "Flooding a router with fake ARP requests",
        ],
    },
    {
        "item_id": "cs09",
        "category": "computer_security",
        "gold": "D",
        "question": "What does the 'S' stand for in HTTPS?",
        "options": ["Standard", "System", "Server", "Secure"],
    },
    {
        "item_id": "cs10",
        "category": "computer_security",
        "gold": "A",
        "question": "Which protocol is used to securely retrieve email from a server over an encrypted channel?",
        "options": ["IMAPS", "Telnet", "FTP", "SNMP"],
    },
    # Elementary Mathematics (10 items)
    {
        "item_id": "em01",
        "category": "elementary_mathematics",
        "gold": "C",
        "question": "If a rectangular garden has a length of 8 meters and a width of 5 meters, what is its perimeter?",
        "options": ["13 meters", "40 meters", "26 meters", "32 meters"],
    },
    {
        "item_id": "em02",
        "category": "elementary_mathematics",
        "gold": "B",
        "question": "What is the value of 15% of 80?",
        "options": ["10", "12", "15", "18"],
    },
    {
        "item_id": "em03",
        "category": "elementary_mathematics",
        "gold": "D",
        "question": "Which of the following is a prime number?",
        "options": ["21", "25", "27", "29"],
    },
    {
        "item_id": "em04",
        "category": "elementary_mathematics",
        "gold": "A",
        "question": "What is 3/4 expressed as a decimal?",
        "options": ["0.75", "0.65", "0.80", "0.70"],
    },
    {
        "item_id": "em05",
        "category": "elementary_mathematics",
        "gold": "B",
        "question": "If 4x - 7 = 13, what is the value of x?",
        "options": ["4", "5", "6", "7"],
    },
    {
        "item_id": "em06",
        "category": "elementary_mathematics",
        "gold": "C",
        "question": "What is the least common multiple (LCM) of 6 and 8?",
        "options": ["12", "18", "24", "48"],
    },
    {
        "item_id": "em07",
        "category": "elementary_mathematics",
        "gold": "A",
        "question": "A triangle has angles measuring 50 degrees and 60 degrees. What is the measure of the third angle?",
        "options": ["70 degrees", "80 degrees", "90 degrees", "65 degrees"],
    },
    {
        "item_id": "em08",
        "category": "elementary_mathematics",
        "gold": "D",
        "question": "What is the product of 12 and 15?",
        "options": ["150", "165", "170", "180"],
    },
    {
        "item_id": "em09",
        "category": "elementary_mathematics",
        "gold": "B",
        "question": "What is the square root of 144?",
        "options": ["10", "12", "14", "16"],
    },
    {
        "item_id": "em10",
        "category": "elementary_mathematics",
        "gold": "C",
        "question": "If Sarah buys 3 notebooks for $4 each and pays with a $20 bill, how much change should she receive?",
        "options": ["$6", "$7", "$8", "$9"],
    },
]


def _extract_letter(text: str, labels: list[str]) -> str:
    """Extract single-letter response from model output."""
    cleaned = text.strip()
    # First check exact single character match
    if cleaned in labels:
        return cleaned
    # Check leading character
    if cleaned and cleaned[0] in labels and (len(cleaned) == 1 or not cleaned[1].isalpha()):
        return cleaned[0]
    # Search for "The answer is (X)" or similar
    for char in cleaned:
        if char in labels:
            return char
    return ""


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Running Experiment 1: MMLU Balanced ({len(MMLU_ITEMS)} items, {MODEL})")
    
    rows: list[dict[str, Any]] = []
    
    for i, item in enumerate(MMLU_ITEMS, 1):
        item_id = item["item_id"]
        gold = item["gold"]
        options = item["options"]
        labels = ["A", "B", "C", "D"][:len(options)]
        
        # 1. Baseline condition
        base_msgs = mcq_baseline_prompt(question=item["question"], options=options, option_labels=labels)
        try:
            base_resp = chat_completion(model=MODEL, messages=base_msgs, max_tokens=64, temperature=0.0)
            base_text = extract_answer_text(base_resp)
            base_letter = _extract_letter(base_text, labels)
        except Exception as e:
            print(f"Error on {item_id} baseline: {e}", file=sys.stderr)
            base_text = ""
            base_letter = ""

        rows.append({
            "item_id": item_id,
            "condition": "baseline",
            "model": MODEL,
            "gold": gold,
            "stored_answer": base_letter,
            "response_text": base_text,
            "response_completeness": "complete" if base_letter else "missing",
            "category": item["category"],
        })

        # 2. Leaked key condition (cue)
        leak_msgs = mcq_leaked_answer_prompt(
            question=item["question"], options=options, gold_key=gold, option_labels=labels
        )
        try:
            leak_resp = chat_completion(model=MODEL, messages=leak_msgs, max_tokens=64, temperature=0.0)
            leak_text = extract_answer_text(leak_resp)
            leak_letter = _extract_letter(leak_text, labels)
        except Exception as e:
            print(f"Error on {item_id} leak: {e}", file=sys.stderr)
            leak_text = ""
            leak_letter = ""

        rows.append({
            "item_id": item_id,
            "condition": "cue_leaked_answer",
            "model": MODEL,
            "gold": gold,
            "stored_answer": leak_letter,
            "response_text": leak_text,
            "response_completeness": "complete" if leak_letter else "missing",
            "category": item["category"],
        })

        print(f"  [{i:2d}/20] {item_id}: gold={gold} | base={base_letter} ('{base_text.strip()}') | leak={leak_letter} ('{leak_text.strip()}')")

    bundle = {
        "profile": "generic-v1",
        "description": "Requested Llama-3.1-8B-Instruct responses on local questions under baseline and answer-leak conditions.",
        "provenance": [
            f"Model: {MODEL} via HF Inference API",
            "Local security/math questions; MMLU attribution unverified",
            "Condition 'baseline': standard zero-shot MCQ prompt",
            "Condition 'cue_leaked_answer': prompt includes gold answer leak in system message",
        ],
        "rows": rows,
    }

    BUNDLE_FILE.write_text(json.dumps(bundle, indent=2) + "\n")
    print(f"\nWrote {len(rows)} rows to {BUNDLE_FILE}")


if __name__ == "__main__":
    refuse_existing_output()
    main()
