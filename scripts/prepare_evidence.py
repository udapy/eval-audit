"""Replay bundled inputs, verify arithmetic, and build the evidence catalog offline."""
from __future__ import annotations

import argparse
import csv
import io
import json
import math
import subprocess
import sys
from collections import Counter
from pathlib import Path

from release_support import ROOT, preserve, sha256, write_text

EXAMPLES = {
    "transfer-fixture": ("Synthetic paired fixture", "assigned synthetic responses", None),
    "external-eval": ("Security/math authored fixture", "assigned synthetic responses; recorded model label is not execution evidence", None),
    "mmlu-balanced": ("Security/math saved responses", "saved text; collection claimed, provider execution unverified", "meta-llama/Llama-3.1-8B-Instruct"),
    "mmlu-skewed": ("Statistics saved responses", "saved text; collection claimed, provider execution unverified", "meta-llama/Llama-3.1-8B-Instruct"),
    "arc-challenge": ("Science saved responses", "saved text; collection claimed, provider execution unverified", "Qwen/Qwen3-8B"),
}


def entropy(values):
    if not values:
        return None
    counts = Counter(values)
    return -sum(n / len(values) * math.log2(n / len(values)) for n in counts.values())


def close(actual, expected):
    if actual is None or expected is None:
        assert actual is expected, (actual, expected)
    else:
        assert math.isclose(actual, expected, abs_tol=1e-12), (actual, expected)


def run(output: Path) -> dict:
    """Use the CLI as a separate process; independently calculate from raw rows."""
    preserve(output)
    output.mkdir(parents=True)
    catalog = {"schema_version": 1, "answer_basis": "stored", "examples": [], "comparisons": []}
    for slug, (title, kind, requested_model) in EXAMPLES.items():
        source = ROOT / "examples" / slug / "bundle.json"
        bundle = json.loads(source.read_text())
        destination = output / slug
        def invoke(*args):
            subprocess.run([sys.executable, "-m", "eval_audit", *map(str, args)], cwd=ROOT, check=True)
        invoke("import", "--source", source, "--out", destination / "data")
        invoke("audit", "--manifest", destination / "data/manifest.json", "--out", destination / "report")
        invoke("triage", "--manifest", destination / "data/manifest.json", "--out", destination / "triage.jsonl")
        report = json.loads((destination / "report/report.json").read_text())
        rows = bundle["rows"]
        example = {
            "id": slug, "title": title, "source": source.relative_to(ROOT).as_posix(),
            "sha256": sha256(source), "bytes": source.stat().st_size,
            "n_rows": len(rows), "n_items": len({(r["dataset_id"], r["item_id"]) for r in rows}),
            "recorded_model_labels": sorted({r.get("model_label", bundle.get("defaults", {}).get("model_label")) for r in rows}),
            "requested_model_from_script": requested_model, "model_revision": None,
            "response_evidence": kind, "report": (destination / "report/report.md").relative_to(ROOT).as_posix(),
            "dataset_revision": None,
            "dataset_provenance": "original authored fixture" if slug == "transfer-fixture" else
                "manually embedded questions; upstream item matching unverified" if slug in {"external-eval", "mmlu-balanced"} else
                "all bundled items match captured current upstream rows; collection revision remains unknown",
            "upstream_verification": None if slug == "transfer-fixture" else "data/provenance/upstream-20260922/item_matches.json",
            "license_status": "original fixture declares CC0-1.0" if slug == "transfer-fixture" else "see THIRD_PARTY.md; upstream licensing does not establish local provenance",
            "missing_evidence": [] if slug == "transfer-fixture" else
                (["upstream question origin", "collection revision"] if slug in {"external-eval", "mmlu-balanced"} else ["collection revision"]) +
                ([] if slug == "external-eval" else ["full provider responses", "request IDs", "returned model snapshot", "finish reasons"]),
        }
        catalog["examples"].append(example)
        independent = []
        for comparison in bundle["comparisons"]:
            matched = [r for r in rows if (r["dataset_id"], r.get("model_label", bundle.get("defaults", {}).get("model_label")), r["run_id"]) ==
                       (comparison["dataset_id"], comparison["model_label"], comparison["run_id"])]
            baseline = [r for r in matched if r["condition"] == comparison["baseline_condition"]]
            target = [r for r in matched if r["condition"] == comparison["target_condition"]]
            assert len(baseline) == len(target) > 0
            assert {r["item_id"] for r in baseline} == {r["item_id"] for r in target}
            valid = lambda group: [r["stored_answer"] for r in group if r.get("stored_answer") in r.get("allowed_answers", ["A", "B", "C", "D"])]
            hbase, htarget, horacle = entropy(valid(baseline)), entropy(valid(target)), entropy([r["gold"] for r in baseline])
            metrics = next(m for m in report["comparison_metrics"] if m["comparison_id"] == comparison["comparison_id"] and m["answer_basis"] == "stored")
            oracle = next(c["metrics"] for c in report["controls"] if c["comparison_id"] == comparison["comparison_id"] and c["answer_basis"] == "stored" and c["control_id"] == "gold_oracle")
            for actual, expected in [(metrics["baseline"]["entropy_bits"], hbase), (metrics["target"]["entropy_bits"], htarget),
                                     (oracle["target"]["entropy_bits"], horacle)]:
                close(actual, expected)
            for group, side in [(baseline, "baseline"), (target, "target")]:
                assert metrics[side]["n_correct"] == sum(r.get("stored_answer") == r["gold"] for r in group)
                assert metrics[side]["n_valid"] == len(valid(group))
            drop = None if hbase is None else hbase - horacle
            close(oracle["entropy_drop"], drop)
            assert oracle["entropy_flag"] == (None if drop is None else drop > 0.15)
            row = {"example": slug, "comparison_id": comparison["comparison_id"], "dataset_id": comparison["dataset_id"],
                   "model_label": comparison["model_label"], "n_pairs": len(baseline),
                   "baseline_valid": len(valid(baseline)), "target_valid": len(valid(target)),
                   "baseline_correct": metrics["baseline"]["n_correct"], "target_correct": metrics["target"]["n_correct"],
                   "baseline_entropy_bits": hbase, "target_entropy_bits": htarget, "oracle_entropy_bits": horacle,
                   "oracle_entropy_drop": drop, "oracle_flag": oracle["entropy_flag"],
                   "gold_counts": dict(sorted(Counter(r["gold"] for r in baseline).items())), "source_sha256": sha256(source)}
            independent.append(row)
            catalog["comparisons"].append(row)
        (destination / "independent.json").write_text(json.dumps(independent, indent=2, sort_keys=True) + "\n")
        # Include representative complete raw rows for manual review without inventing provider metadata.
        samples = rows[:2] + [r for r in rows if not r.get("response_text")][:2]
        (destination / "sample.json").write_text(json.dumps(samples, indent=2, ensure_ascii=False) + "\n")
    return catalog


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=ROOT / "audit/artifacts/release")
    args = parser.parse_args()
    catalog = run(args.out.resolve())
    write_text(ROOT / "data/catalog.json", json.dumps(catalog, indent=2, sort_keys=True) + "\n")
    csv_data = io.StringIO()
    writer = csv.DictWriter(csv_data, fieldnames=list(catalog["comparisons"][0]))
    writer.writeheader()
    for row in catalog["comparisons"]:
        writer.writerow({**row, "gold_counts": json.dumps(row["gold_counts"], sort_keys=True)})
    write_text(ROOT / "data/comparisons.csv", csv_data.getvalue())
    lines = ["# Evidence catalog", "", "Generated by `python scripts/prepare_evidence.py`. Counts describe bundled slices, not entire benchmarks.", "",
             "| Example | Items / rows | Response evidence | Saved input | Report |", "| --- | ---: | --- | --- | --- |"]
    for e in catalog["examples"]:
        lines.append(f"| {e['title']} | {e['n_items']} / {e['n_rows']} | {e['response_evidence']} | [bundle](../{e['source']}) | [audit](../{e['report']}) |")
    lines += ["", "Machine-readable [catalog](catalog.json) contains model labels, requested model IDs, missing evidence, byte hashes, and dataset provenance.",
              "[Comparison data](comparisons.csv) records independently verified arithmetic. [Source and license notes](../THIRD_PARTY.md) explain attribution limits.",
              "", "The external-eval model label is historical metadata on assigned responses. It is not evidence that this model ran.",
              "The other three saved-response bundles retain their original provenance claims, which are not independently authenticated.",
              "", "## Recorded models", "",
              "| Example | Recorded label | Requested model in collection script | Execution evidence |",
              "| --- | --- | --- | --- |"]
    for e in catalog["examples"]:
        lines.append(f"| {e['id']} | {', '.join(e['recorded_model_labels'])} | {e['requested_model_from_script'] or 'No model collection'} | {e['response_evidence']} |")
    lines += ["", "No model weights are bundled. Returned model snapshots, provider envelopes, request IDs, and finish reasons are unavailable for the saved model text.", "", "[Optional historical source inventory](HISTORICAL.md) records the two additional model labels and their unbundled raw-source requirements."]
    write_text(ROOT / "data/README.md", "\n".join(lines) + "\n")
    print(f"Verified {len(catalog['examples'])} bundles and {len(catalog['comparisons'])} comparisons")


if __name__ == "__main__":
    main()
