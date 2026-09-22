# Evidence for review

This page maps each saved slice to the input bytes, the audit output, and the arithmetic a reviewer can recompute. Counts and interpretation notes are in the [research note](RESEARCH-NOTE.md). Assessed model and dataset status is in the [catalog](../data/README.md).

A completed report means the saved rows were processed. It does not establish deception, sandbagging, evaluation awareness, or model intent.

## What is in the repository

Each slice has the same output layout under `audit/artifacts/release/<example>/`:

| File | Role |
| --- | --- |
| `data/raw/bundle.json` | Copy of the saved input inside the audit |
| `data/normalized.jsonl` | Rows after import |
| `report/report.md` and `report/report.json` | Metrics, controls, and gate results |
| `report/evidence/items/` and `report/evidence/findings/` | Per-item and per-finding pages linked from the report |
| `report/inputs/` | Input snapshot stored with the report |
| `independent.json` | Accuracy, entropy, oracle drop, and oracle flag recomputed from the raw rows |
| `sample.json` | Raw rows selected for inspection |
| `triage.jsonl` | Queue for human review |

The comparison table for every slice is [data/comparisons.csv](../data/comparisons.csv). Twenty inspected records, including missing answers and parser disagreements, are in [audit/sample-review.json](../audit/sample-review.json).

| Slice | Response evidence | Saved input | Report |
| --- | --- | --- | --- |
| Synthetic paired fixture | Assigned synthetic answers | [bundle](../examples/transfer-fixture/bundle.json) | [report](../audit/artifacts/release/transfer-fixture/report/report.md) |
| Security/math authored fixture | Assigned synthetic answers. The recorded model label is historical metadata | [bundle](../examples/external-eval/bundle.json) | [report](../audit/artifacts/release/external-eval/report/report.md) |
| Security/math saved responses | Saved text. Collection is claimed; provider execution is unverified | [bundle](../examples/mmlu-balanced/bundle.json) | [report](../audit/artifacts/release/mmlu-balanced/report/report.md) |
| Statistics saved responses | Saved text. Collection is claimed; provider execution is unverified | [bundle](../examples/mmlu-skewed/bundle.json) | [report](../audit/artifacts/release/mmlu-skewed/report/report.md) |
| Science saved responses | Saved text, including missing answers. Collection is claimed; provider execution is unverified | [bundle](../examples/arc-challenge/bundle.json) | [report](../audit/artifacts/release/arc-challenge/report/report.md) |

Figures rendered from these records: [gold-key counts](figures/gold-distributions.png), [entropy comparison](figures/entropy-comparison.png).

## How to check a number

Read the saved bundle and the matching `independent.json` before trusting a summary. Regenerate the reports and the comparison table from those bundles:

```sh
make evidence
```

That command archives the current `audit/artifacts/release/` and `data/comparisons.csv` before writing replacements. Offline replay of the upstream item check, with no network and no inference:

```sh
python scripts/verify_sources.py --verify data/provenance/upstream-20260922
```

The [provenance receipts](../data/provenance/README.md) record that comparison. Statistics items and ARC science items matched the current upstream rows that were checked. The embedded security/math questions matched none of the claimed current subject test splits. The receipts identify the bytes compared at verification time. They do not identify the dataset revision used when the responses were collected.

## What was not retained

Provider envelopes, request ids, returned model snapshots, and finish reasons are absent. The collection helper stored extracted answer text. Its completeness field is inferred from extracted letters. [Collection notes](../scripts/collection/README.md) describe the prompts and the requested model ids. Those scripts are source records. Running them would be a new collection, and the balanced script does not regenerate the saved bundle byte for byte.

Report provenance lines such as a model name or "HF Inference API" are the notes stored with the bundle. They are source claims. The catalog states which of those claims are unauthenticated.

## Scope of these slices

The bundled slices are small and selected. The two security/math bundles share questions. The statistics script keeps the first 25 rows of that subject. The science script keeps the first qualifying four-option items. These files support inspection of the saved rows. They do not estimate a population false-positive rate or representative benchmark performance.

Saved response text and the embedded security/math questions have unresolved redistribution and attribution limits. See [THIRD_PARTY.md](../THIRD_PARTY.md).
