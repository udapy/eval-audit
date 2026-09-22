# Eval Audit

Deterministic, offline diagnostics for saved multiple-choice evaluation results. Python 3.12+; no runtime dependencies, credentials, model downloads, or GPU required.

## Install and run

```sh
python -m pip install eval-audit
python -m eval_audit demo --out my-new-demo
```

The demo uses constructed arithmetic questions and assigned answers. Open `my-new-demo/report.md` to inspect metrics, controls, and linked evidence. Choose a fresh output directory for every run; existing evidence is not overwritten.

For your own saved bundle:

```sh
eval-audit import --source bundle.json --out imported-inputs
eval-audit audit --manifest imported-inputs/manifest.json --out audit-report
eval-audit check bundle.json
```

A generic JSON bundle contains `rows` and explicit paired `comparisons`, with optional item text and provenance notes. Rows identify dataset, model label, run, item, condition, gold key, stored answer, response text, and allowed answer labels. Missing answers stay missing. The source distribution includes an original CC0 synthetic bundle under `examples/transfer-fixture/`.

## Read diagnostics carefully

G0 checks source/manifest integrity; G1 checks saved-answer parsing and available option identities; G2 tests a computed gold oracle against a historical entropy heuristic; G3 diagnoses single-item accuracy influence. G4 always records that behavioral claims require additional evidence and human interpretation.

`check` exits 0 when no G0/G2 finding blocks the check, 2 for blocking/invalid inputs, and 1 for unexpected errors. Advisory diagnostics may remain at exit 0. A completed audit does not establish deception, evaluation awareness, or the validity of a behavioral claim.

Accuracy includes missing rows in its all-row denominator; entropy uses valid letters only. Stored labels, parsed answers, and gold keys remain separate. Source hashes detect changed bytes but do not authenticate a recorded model label.

## Other interfaces

The CLI also exports human review queues with `triage`, accepts supported saved Inspect and lm-evaluation-harness layouts through `check --format`, and provides `import-historical` for an explicitly supplied optional pinned collection. Log adapter support is limited to tested layouts, not every upstream log version.

## Local assistant

```sh
python -m pip install 'eval-audit[mcp]'
eval-audit-mcp --workspace /absolute/workspace --output-root audit-output
```

That command starts a local stdio server for the same audit service as the CLI. The core install omits this extra. Setup, the tool contract, and a synthetic example are in [MCP.md](MCP.md). Text returned to the assistant can leave the machine when the assistant host is a cloud service.

The code is MIT licensed. The original synthetic transfer fixture declares CC0-1.0. Model weights, saved research responses, upstream benchmark snapshots, and historical annotations are excluded from public distributions. No claim is made about third-party redistribution rights for user-supplied data.
