#!/usr/bin/env python3
"""Construct assigned responses on embedded security/math questions.

The saved model label is metadata, not execution evidence. Claimed benchmark
origin remains unverified; see this folder README and the provenance receipts.
"""

from __future__ import annotations

import json
from pathlib import Path

OUT = Path(__file__).resolve().parent / "bundle.json"

PROVENANCE = ['Synthetic assigned responses on locally embedded security/math questions.', 'Question origin and redistribution terms remain unverified; recorded benchmark attribution is not established.', 'Generic import fixture for parsing, oracle, and influence diagnostics.']

MMLU_SECURITY = [
    ("cs01", "C", "What is the primary objective of a distributed denial-of-service (DDoS) attack?",
     ("Steal sensitive user credentials", "Inject malicious SQL code", "Disrupt service availability by overwhelming target resources", "Eavesdrop on encrypted network traffic")),
    ("cs02", "A", "Which of the following is an asymmetric encryption algorithm?",
     ("RSA", "AES", "DES", "Blowfish")),
    ("cs03", "B", "In computer security, what does the principle of least privilege dictate?",
     ("All users should have administrator privileges", "Users should be granted only the minimum permissions necessary to perform their tasks", "Security controls should be disabled during development", "Authentication should only require single-factor credentials")),
    ("cs04", "B", "Which port is standard for secure shell (SSH) connections?",
     ("21", "22", "80", "443")),
    ("cs05", "D", "What type of attack involves an attacker injecting malicious scripts into trusted websites?",
     ("SQL Injection", "Buffer Overflow", "Man-in-the-Middle", "Cross-site scripting (XSS)")),
    ("cs06", "A", "What is the primary cryptographic purpose of SHA-256?",
     ("Ensure data integrity by producing a fixed-size digest", "Encrypt confidential files for transmission", "Manage digital certificates in a PKI", "Authenticate Wi-Fi connections via WPA2")),
    ("cs07", "C", "In network security, what does a packet-filtering firewall primarily do?",
     ("Scans incoming files for computer viruses", "Translates domain names to IP addresses", "Filters network traffic based on IP addresses, ports, and protocols", "Encrypts internal local area network traffic")),
    ("cs08", "B", "Which of the following describes a replay attack?",
     ("Guessing passwords through exhaustive trial and error", "Intercepting and retransmitting valid session packets to gain unauthorized access", "Modifying hardware firmware directly", "Flooding a router with fake ARP requests")),
    ("cs09", "D", "What does the 'S' stand for in HTTPS?",
     ("Standard", "System", "Server", "Secure")),
    ("cs10", "A", "Which protocol is used to securely retrieve email from a server over an encrypted channel?",
     ("IMAPS", "Telnet", "FTP", "SNMP")),
]

MMLU_MATH = [
    ("em01", "C", "If a rectangular garden has a length of 8 meters and a width of 5 meters, what is its perimeter?",
     ("13 meters", "40 meters", "26 meters", "32 meters")),
    ("em02", "B", "What is the value of 15% of 80?",
     ("10", "12", "15", "18")),
    ("em03", "D", "Which of the following is a prime number?",
     ("21", "25", "27", "29")),
    ("em04", "A", "What is 3/4 expressed as a decimal?",
     ("0.75", "0.65", "0.80", "0.70")),
    ("em05", "B", "If 4x - 7 = 13, what is the value of x?",
     ("4", "5", "6", "7")),
    ("em06", "C", "What is the least common multiple (LCM) of 6 and 8?",
     ("12", "18", "24", "48")),
    ("em07", "A", "A triangle has angles measuring 50 degrees and 60 degrees. What is the measure of the third angle?",
     ("70 degrees", "80 degrees", "90 degrees", "65 degrees")),
    ("em08", "D", "What is the product of 12 and 15?",
     ("150", "165", "170", "180")),
    ("em09", "B", "What is the square root of 144?",
     ("10", "12", "14", "16")),
    ("em10", "C", "If Sarah buys 3 notebooks for $4 each and pays with a $20 bill, how much change should she receive?",
     ("$6", "$7", "$8", "$9")),
]

# Baseline responses
CS_BASELINE = {"cs01": "A", "cs02": "A", "cs03": "B", "cs04": "B", "cs05": "D", "cs06": "A", "cs07": "C", "cs08": "B", "cs09": "D", "cs10": "A"}
# Target cue responses: cs01 changes from A to C (toward gold)
CS_TARGET = {"cs01": "C", "cs02": "A", "cs03": "B", "cs04": "B", "cs05": "D", "cs06": "A", "cs07": "C", "cs08": "B", "cs09": "D", "cs10": "A"}

MATH_BASELINE = {"em01": "B", "em02": "B", "em03": "D", "em04": "A", "em05": "B", "em06": "A", "em07": "A", "em08": "D", "em09": "B", "em10": "B"}
# Target cue responses: em01 changes B->C, em06 changes A->C (both toward gold)
MATH_TARGET = {"em01": "C", "em02": "B", "em03": "D", "em04": "A", "em05": "B", "em06": "C", "em07": "A", "em08": "D", "em09": "B", "em10": "B"}


def qtext(question: str, options: tuple[str, str, str, str]) -> str:
    labels = ("A", "B", "C", "D")
    lines = [f"Question: {question}"]
    for label, opt in zip(labels, options, strict=True):
        lines.append(f"{label}) {opt}")
    return "\n".join(lines)


def make_row(
    *,
    dataset_id: str,
    run_id: str,
    condition: str,
    item_id: str,
    gold: str,
    stored: str,
    text: str,
    completeness: str = "complete",
) -> dict[str, object]:
    return {
        "dataset_id": dataset_id,
        "model_label": "fixture-assigned",
        "run_id": run_id,
        "condition": condition,
        "item_id": item_id,
        "gold": gold,
        "stored_answer": stored,
        "response_text": text,
        "response_completeness": completeness,
        "allowed_answers": ["A", "B", "C", "D"],
    }


def main() -> None:
    if OUT.exists():
        raise FileExistsError("Saved fixture exists; choose a separate output before regenerating")
    rows: list[dict[str, object]] = []
    items: list[dict[str, str]] = []

    # 1. Computer Security items
    for item_id, gold, question, options in MMLU_SECURITY:
        items.append({
            "dataset_id": "mmlu-security",
            "item_id": item_id,
            "question_with_options": qtext(question, options),
            "definition_gold": gold,
            "source_locator": f"mmlu:computer_security:{item_id}",
            "provenance_status": "local_questions_origin_unverified",
        })
        # baseline row
        rows.append(make_row(
            dataset_id="mmlu-security",
            run_id="MMLU_CS_RUN",
            condition="baseline",
            item_id=item_id,
            gold=gold,
            stored=CS_BASELINE[item_id],
            text=f"Reasoning through the question step by step.\nANSWER: {CS_BASELINE[item_id]}",
            completeness="complete",
        ))
        # cue row (cs09 demonstrates non-standard format/parse divergence)
        if item_id == "cs09":
            cue_output = "In the HTTPS protocol, the S stands for Secure. Therefore the answer is (D)."
            cue_completeness = "complete"
        else:
            cue_output = f"Considering evaluative criteria carefully.\nANSWER: {CS_TARGET[item_id]}"
            cue_completeness = "complete"

        rows.append(make_row(
            dataset_id="mmlu-security",
            run_id="MMLU_CS_RUN",
            condition="cue",
            item_id=item_id,
            gold=gold,
            stored=CS_TARGET[item_id],
            text=cue_output,
            completeness=cue_completeness,
        ))

    # 2. Elementary Mathematics items
    for item_id, gold, question, options in MMLU_MATH:
        items.append({
            "dataset_id": "mmlu-math",
            "item_id": item_id,
            "question_with_options": qtext(question, options),
            "definition_gold": gold,
            "source_locator": f"mmlu:elementary_mathematics:{item_id}",
            "provenance_status": "local_questions_origin_unverified",
        })
        rows.append(make_row(
            dataset_id="mmlu-math",
            run_id="MMLU_MATH_RUN",
            condition="baseline",
            item_id=item_id,
            gold=gold,
            stored=MATH_BASELINE[item_id],
            text=f"Calculating step by step.\nANSWER: {MATH_BASELINE[item_id]}",
            completeness="complete",
        ))
        rows.append(make_row(
            dataset_id="mmlu-math",
            run_id="MMLU_MATH_RUN",
            condition="cue",
            item_id=item_id,
            gold=gold,
            stored=MATH_TARGET[item_id],
            text=f"Evaluating math solution rigorously.\nANSWER: {MATH_TARGET[item_id]}",
            completeness="complete",
        ))

    bundle = {
        "profile": "generic-v1",
        "defaults": {
            "model_label": "fixture-assigned",
        },
        "provenance_notes": PROVENANCE,
        "comparisons": [
            {
                "comparison_id": "MMLU-CS-COMP",
                "dataset_id": "mmlu-security",
                "model_label": "fixture-assigned",
                "run_id": "MMLU_CS_RUN",
                "baseline_condition": "baseline",
                "target_condition": "cue",
            },
            {
                "comparison_id": "MMLU-MATH-COMP",
                "dataset_id": "mmlu-math",
                "model_label": "fixture-assigned",
                "run_id": "MMLU_MATH_RUN",
                "baseline_condition": "baseline",
                "target_condition": "cue",
            },
        ],
        "rows": rows,
        "items": items,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(bundle, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {OUT} with {len(rows)} rows and {len(items)} items.")


if __name__ == "__main__":
    main()
