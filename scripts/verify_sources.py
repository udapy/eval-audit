#!/usr/bin/env python3
"""Capture public source receipts, or verify captured item matches offline.

Capture: python scripts/verify_sources.py --fetch --out data/provenance/NEW_DIR
Replay:  python scripts/verify_sources.py --verify data/provenance/NEW_DIR

Only anonymous HTTPS GETs to Hugging Face are used. No inference is performed.
Capture refuses an existing destination, including an empty directory. Offline
replay checks snapshots and receipts without network access or file writes.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[1]
SPLITS = (
    ("cais/mmlu", "computer_security"),
    ("cais/mmlu", "elementary_mathematics"),
    ("cais/mmlu", "high_school_statistics"),
    ("allenai/ai2_arc", "ARC-Challenge"),
)
BUNDLES = ("external-eval", "mmlu-balanced", "mmlu-skewed", "arc-challenge")
SUBJECTS = {
    "mmlu-security": "computer_security",
    "mmlu-math": "elementary_mathematics",
    "mmlu-high-school-statistics": "high_school_statistics",
    "arc-challenge": "ARC-Challenge",
}


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_json(path: Path):
    return json.loads(path.read_bytes())


def write_json(path: Path, value) -> None:
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, sort_keys=True, ensure_ascii=False)
        stream.write("\n")


def split_key(dataset: str, config: str) -> str:
    return dataset.replace("/", "--") + "--" + config + "--test"


def local_tuple(item: dict) -> tuple:
    """Parse only structural formatting; retain exact question/option content."""
    text = item["question_with_options"]
    if text.startswith("Question: "):
        text = text[len("Question: "):]
    elif text.startswith("Q: "):
        text = text[len("Q: "):]
    matches = list(re.finditer(r"(?m)^([A-D])\) ", text))
    if not matches or [m[1] for m in matches] != list("ABCD"):
        raise ValueError(f"Unsupported option structure for {item['item_id']}")
    question = text[:matches[0].start()].removesuffix("\n")
    choices = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() - 1 if index + 1 < len(matches) else len(text)
        choices.append(text[match.end():end])
    return question, tuple(zip("ABCD", choices)), str(item["definition_gold"])


def upstream_tuple(row: dict, dataset: str) -> tuple:
    if dataset == "cais/mmlu":
        answer = row["answer"]
        gold = "ABCD"[answer] if isinstance(answer, int) else str(answer)
        return row["question"], tuple(zip("ABCD", row["choices"])), gold
    choices = row["choices"]
    return row["question"], tuple(zip(choices["label"], choices["text"])), str(row["answerKey"])


def calculate_receipts(root: Path, manifest: dict) -> dict:
    upstream = {}
    coverage = []
    for entry in manifest["splits"]:
        rows = []
        for page in entry["snapshots"]:
            data = read_json(root / page)
            rows.extend(data["rows"])
        indices = [row["row_idx"] for row in rows]
        if indices != list(range(entry["num_rows_total"])):
            raise ValueError(f"Incomplete or duplicated split: {entry['config']}")
        dataset = entry["dataset"]
        upstream[entry["config"]] = (dataset, rows)
        coverage.append({"dataset": dataset, "config": entry["config"],
                         "split": "test", "rows_checked": len(rows), "full_split": True})

    item_receipts = []
    summary = []
    inputs = {}
    for entry in manifest["local_inputs"]:
        name = entry["bundle"]
        bundle = read_json(root / entry["snapshot"])
        inputs[name] = bundle
        count = 0
        for item in bundle["items"]:
            config = SUBJECTS[item["dataset_id"]]
            dataset, rows = upstream[config]
            expected = local_tuple(item)
            matches = []
            for candidate in rows:
                row = candidate["row"]
                if expected != upstream_tuple(row, dataset):
                    continue
                if dataset == "allenai/ai2_arc" and item["item_id"] != row["id"]:
                    continue
                matches.append({"row_idx": candidate["row_idx"],
                                "upstream_item_id": row.get("id")})
            count += bool(matches)
            item_receipts.append({
                "bundle": name, "local_item_id": item["item_id"],
                "local_dataset_id": item["dataset_id"], "dataset": dataset,
                "config": config, "split": "test", "exact_match": bool(matches),
                "matched_rows": matches,
                "comparison": "question, ordered option labels and text, gold" +
                              (", upstream item ID" if dataset == "allenai/ai2_arc" else ""),
                "collection_revision": None,
            })
        summary.append({"bundle": name, "items": len(bundle["items"]), "exact_matches": count})
    shared = all(
        local_tuple(a) == local_tuple(b)
        for a, b in zip(inputs["external-eval"]["items"], inputs["mmlu-balanced"]["items"], strict=True)
    )
    return {
        "schema_version": 1, "coverage": coverage, "summary": summary,
        "external_and_balanced_items_equal_after_prompt_prefix_removal": shared,
        "format_normalization": "Remove only an initial 'Question: ' or 'Q: '; split A) through D) lines. No content, case, whitespace, option order, or gold normalization.",
        "limitations": [
            "Matches concern saved item content, not model-response authenticity.",
            "Current upstream heads are recorded separately; original collection revisions remain unknown.",
            "Dataset-server responses do not pin a repository revision; current heads are observations, not guaranteed snapshot revisions.",
            "An unmatched tuple does not establish authorship or prove absence from other dataset versions or splits.",
        ],
        "items": item_receipts,
    }


def capture(out: Path) -> None:
    if out.exists():
        raise ValueError("Destination already exists; choose a new directory.")
    out.mkdir(parents=True, exist_ok=False)
    (out / "upstream").mkdir()
    (out / "local_inputs").mkdir()
    manifest = {"schema_version": 1, "started_at_utc": datetime.now(timezone.utc).isoformat(),
                "requests": [], "splits": [], "local_inputs": [], "current_heads": []}

    def fetch(url: str, filename: str):
        request = urllib.request.Request(url, headers={"Accept": "application/json"}, method="GET")
        with urllib.request.urlopen(request, timeout=60) as response:
            payload = response.read()
            selected_headers = {name: response.headers[name] for name in
                                ("Content-Type", "ETag", "X-Repo-Commit", "Date")
                                if response.headers.get(name)}
            status = response.status
        value = json.loads(payload)
        relative = "upstream/" + filename
        with (out / relative).open("xb") as stream:
            stream.write(payload)
        manifest["requests"].append({"method": "GET", "url": url, "status": status,
                                     "fetched_at_utc": datetime.now(timezone.utc).isoformat(),
                                     "snapshot": relative, "sha256": digest(payload),
                                     "headers": selected_headers, "authenticated": False})
        print(f"GET {url} -> {relative}", flush=True)
        return value, relative

    for name in BUNDLES:
        source = Path("examples") / name / "bundle.json"
        payload = (PROJECT / source).read_bytes()
        snapshot = "local_inputs/" + name + ".json"
        with (out / snapshot).open("xb") as stream:
            stream.write(payload)
        manifest["local_inputs"].append({"bundle": name, "source": source.as_posix(),
                                         "snapshot": snapshot, "sha256": digest(payload)})

    for dataset in dict.fromkeys(dataset for dataset, _ in SPLITS):
        data, path = fetch("https://huggingface.co/api/datasets/" + dataset,
                           dataset.replace("/", "--") + "--metadata.json")
        manifest["current_heads"].append({
            "dataset": dataset, "current_head_observed": data.get("sha"),
            "collection_revision": None, "metadata_snapshot": path,
            "upstream_license_recorded": data.get("cardData", {}).get("license"),
            "dataset_card_url": "https://huggingface.co/datasets/" + dataset,
        })

    for dataset, config in SPLITS:
        entry = {"dataset": dataset, "config": config, "split": "test", "snapshots": []}
        offset = 0
        while True:
            query = urllib.parse.urlencode({"dataset": dataset, "config": config,
                                            "split": "test", "offset": offset, "length": 100})
            data, path = fetch("https://datasets-server.huggingface.co/rows?" + query,
                               split_key(dataset, config) + f"--offset-{offset:04d}.json")
            if data.get("partial"):
                raise ValueError("Upstream reported a partial split response.")
            entry["snapshots"].append(path)
            if "num_rows_total" in entry and entry["num_rows_total"] != data["num_rows_total"]:
                raise ValueError("Upstream split size changed during capture.")
            entry["num_rows_total"] = data["num_rows_total"]
            offset += len(data["rows"])
            if offset >= data["num_rows_total"]:
                break
            if not data["rows"]:
                raise ValueError("Upstream returned an empty page before split end.")
        manifest["splits"].append(entry)

    manifest["completed_at_utc"] = datetime.now(timezone.utc).isoformat()
    write_json(out / "requests.json", manifest)
    receipts = calculate_receipts(out, manifest)
    write_json(out / "item_matches.json", receipts)
    checksums = {path.relative_to(out).as_posix(): digest(path.read_bytes())
                 for path in sorted(out.rglob("*.json"))}
    write_json(out / "checksums.json", {"algorithm": "sha256", "files": checksums,
                                        "excludes": ["checksums.json"]})
    print(json.dumps(receipts["summary"], indent=2))


def verify(root: Path) -> None:
    checksums = read_json(root / "checksums.json")["files"]
    for relative, expected in checksums.items():
        path = Path(relative)
        if path.is_absolute() or ".." in path.parts:
            raise ValueError("Checksum path must be relative and contained in snapshot directory.")
        if digest((root / path).read_bytes()) != expected:
            raise ValueError(f"Checksum mismatch: {relative}")
    manifest = read_json(root / "requests.json")
    calculated = calculate_receipts(root, manifest)
    if calculated != read_json(root / "item_matches.json"):
        raise ValueError("Item receipt recomputation did not match saved results.")
    print(json.dumps({"offline_verification": "passed", "files_verified": len(checksums),
                      "summary": calculated["summary"]}, indent=2))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--fetch", action="store_true", help="Explicitly permit public anonymous GET requests.")
    mode.add_argument("--verify", type=Path, help="Verify a captured directory offline without writing files.")
    parser.add_argument("--out", type=Path, help="New capture directory; must not already exist.")
    args = parser.parse_args()
    if args.fetch and args.out is None:
        parser.error("--fetch requires --out NEW_DIR")
    if args.verify is not None and args.out is not None:
        parser.error("--out is only accepted with --fetch")
    try:
        if args.fetch:
            capture(args.out)
        else:
            verify(args.verify)
    except (OSError, ValueError, KeyError) as exc:
        print(f"Source verification failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
