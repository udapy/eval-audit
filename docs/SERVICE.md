# Local audit service

`AuditService` runs deterministic saved multiple-choice audits. It shares report orchestration and scoring with the CLI. It performs no inference and requires no credentials.

```python
from eval_audit.service import AuditService
service = AuditService(workspace="/absolute/research/workspace", output_root="audit-output")
inspection = service.inspect_bundle("bundle.json")
result = service.run_audit("bundle.json")
page = service.findings_page(result["audit_id"], offset=0)
if page["findings"]:
    finding = service.get_finding(result["audit_id"], page["findings"][0]["finding_id"])
report = service.export_report(result["audit_id"], format="markdown")
```

The operator must supply an existing workspace and a dedicated output directory inside it. Relative paths are resolved against the workspace. Traversal, symlinks below the workspace, external paths, binary archives and unsupported inputs are rejected. This protects the interface boundary; it is not a sandbox against another local process with the same permissions.

The default input limits are 10 MiB (including annotations), 2,000 records, 20 entries per findings page, and 4,096 total response characters per explicit finding excerpt request. These limits constrain software resources, not research sample sizes. Summaries cap metric lists; the full JSON report preserves rational accuracy values, denominators and nulls. Use `findings_page` with its returned offset for further findings. Full reports may contain sensitive source text. Routine finding responses omit annotations and raw observed values. `include_raw=True` explicitly requests bounded matching response excerpts.

Each request captures source bytes before conversion. Inspections retain staging under `inspections/` and never publish an audit ID. Audits use exclusive random IDs under `audits/`; incomplete attempts retain diagnostics and cannot be retrieved as completed audits. The completion receipt records source hashes and hashes of report artifacts. Export returns an existing workspace-relative path and URI, never overwrites a destination. Existing receipts work after restarting the service. Artifact hash mismatches fail retrieval. These hashes detect accidental changes; they do not authenticate against a malicious local owner.

`same_source_group` identifies identical captured files, including filenames and annotations. Repeating an audit creates another artifact, not an independent model run. Concurrent requests have separate directories. No request deletes an earlier source or output.

Errors raise `ServiceError`, an `AuditInputError` subclass with `code` and `as_dict()`. Codes are `INVALID_INPUT`, `NOT_FOUND`, `SIZE_LIMIT`, `UNSUPPORTED_LAYOUT`, and `PROCESSING_FAILURE`. A scientifically flagged but structurally complete audit is a completed artifact, not behavioral approval. Invalid or insufficient comparisons remain failed attempts with retained reports.

## Supported log envelopes

`generic` accepts the existing JSON bundle or a directory containing `bundle.json`, or `rows.jsonl` plus `comparisons.json` and optional `meta.json`/`items.jsonl`. Annotations use a separate JSONL path.

`inspect` and `lm-eval` accept a JSON object with **two explicit logs**:

```json
{"baseline": {"eval": {"model": "synthetic", "task": "demo"}, "samples": [{"id": "i1", "target": "A", "input": "Synthetic item", "output": {"completion": "ANSWER: B"}}]}, "target": {"eval": {"model": "synthetic", "task": "demo"}, "samples": [{"id": "i1", "target": "A", "input": "Synthetic item", "output": {"completion": "ANSWER: A"}}]}}
```

Inspect support is limited to text inputs, one text completion or message choice, explicit IDs, a single letter target, and optional 2–10 text choices. It does not read zipped `.eval` archives. For lm-eval, each log needs `config.model_name` and one task under `samples`; each sample needs `doc_id`, a letter target or zero-based integer for A–D, and `resps` containing exactly one text generation (optionally nested once). Likelihood tuples, multiple tasks or generations, and mismatched model/task/item definitions are rejected. Other layouts require an explicit generic conversion.

The imported derivative uses strict parser results as its stored-answer field; it does not claim the provider stored those answers. It retains the original envelope and records that distinction in report provenance. Completeness stays `unknown` unless explicitly supplied. Single logs cannot establish paired comparisons and are rejected by this service.

The older direct `load_inspect_eval` / `load_lm_eval` functions still mirror a single log and use gold-conditioned extraction. They are retained for compatibility, are unsuitable for paired scientific comparisons, and are **not used by this service or CLI**. Use a paired envelope through the service or `eval-audit check --format inspect` / `--format lm-eval`, or convert actual paired observations to the generic CLI format. Correcting that compatibility API is separately tracked; no saved research responses were changed.
