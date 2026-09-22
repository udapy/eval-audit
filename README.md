# Eval Audit

Offline diagnostics for saved multiple-choice evaluation results. Import saved answer records, compare stored labels with parsed text, compute simple controls and item influence, and produce inspectable reports. Python 3.12+; no runtime dependencies, credentials, or model downloads.

**Start here:** [research note](docs/RESEARCH-NOTE.md) · [data and models](data/README.md) · [input format](docs/INPUT-FORMAT.md) · [terminology](docs/GLOSSARY.md) · [release verification](docs/VERIFICATION.md).

![Offline audit workflow](docs/figures/workflow.png)

## Install and try it

From this project's directory:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[dev,plots]'
.venv/bin/eval-audit demo --out .tmp/my-first-demo
.venv/bin/eval-audit import --source examples/transfer-fixture/bundle.json --out .tmp/my-first-input
.venv/bin/eval-audit audit --manifest .tmp/my-first-input/manifest.json --out .tmp/my-first-report
```

Use a new output directory for each run. The CLI refuses nonempty destinations. Open the generated `report.md`; its evidence pages link records to saved source bytes. Source bundles and code licenses are described separately in [THIRD_PARTY.md](THIRD_PARTY.md).

## Commands

| Command | Purpose |
| --- | --- |
| `eval-audit demo --out DIR` | Generate and audit a small synthetic example |
| `eval-audit import --source BUNDLE --out DIR` | Import a generic JSON or JSONL bundle |
| `eval-audit audit --manifest FILE --out DIR` | Generate metrics, findings, gate results, and evidence pages |
| `eval-audit triage --manifest FILE --out FILE` | Export a queue for human review |
| `eval-audit check BUNDLE` | Print scoped engineering diagnostics |
| `eval-audit check LOG --format inspect` | Import supported Inspect log fields and audit them |
| `eval-audit check LOG --format lm-eval` | Import supported lm-evaluation-harness sample fields |
| `eval-audit import-historical --source DIR --out DIR` | Optional importer for an explicitly supplied, byte-pinned historical collection |

`check` exits 0 when G0/G2 have no blocking finding, 2 for blocked/invalid input, and 1 for an unexpected audit error. G1/G3 diagnostics remain advisory and G4 remains unestablished. Exit 0 is **not validation of a behavioral claim**. `audit` reports input-processing status; review its findings even when it exits 0. See [gate definitions](docs/GLOSSARY.md).

Adapters support particular saved-field layouts; they are not claims of compatibility with every upstream log version. The provider client and collection scripts are optional, separate from offline replay.

## Reproduce this release

```sh
make check
make evidence
make figures
make release-audit
make release
```

`make check` uses bundled offline inputs and keeps its outputs in a fresh `.tmp/` directory. Evidence and figure regeneration archives existing outputs before replacement. `make release` creates a timestamped public package. Examples, evidence, and the research note are in this repository. A wheel installs the library and CLI.

Historical source data is not bundled and is not needed for normal use. To run optional historical integration tests, set `EVAL_AUDIT_HISTORICAL_SOURCE` to a separately supplied authorized collection. Model collection is outside this workflow; see [collection notes](scripts/collection/README.md).

## What the evidence supports

The [catalog](data/catalog.json) indexes five bundles and distinguishes assigned responses from saved text with locally recorded model attribution. The named balanced subset has unverified benchmark origin. Statistics and science items have separate upstream verification receipts; model execution is not independently authenticated by those receipts.

A computed gold oracle is a perfect answerer by construction. A model prompted with the answer key can still emit a wrong or missing answer. The oracle diagnostic depends on both gold keys and the saved baseline. It cannot establish deception, sandbagging, or evaluation awareness.

## Project map

- `src/`: library and CLI; `tests/`: offline regression cases.
- `examples/`: frozen source bundles and example-specific notes.
- `data/`: evidence catalog, comparison tables, upstream verification receipts.
- `audit/`: regenerated reports, independent arithmetic, and release records.
- `docs/`: research note, format reference, glossary, and static figures. Install notes are in `docs/PACKAGE-README.md`. Local assistant setup is in `docs/MCP.md`.
- `scripts/`: reproduction, source verification, packaging, and optional collection.

Original preparation material and pre-edit files are preserved in an excluded local archive. No archived preparation files are required to use the release.
