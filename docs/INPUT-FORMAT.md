# Inputs and outputs

## Generic bundle

Pass a JSON object with a nonempty `rows` array and explicit `comparisons`. The [transfer fixture](../examples/transfer-fixture/bundle.json) is a complete runnable example.

```json
{
  "profile": "generic-v1",
  "defaults": {"model_label": "my-recorded-model"},
  "comparisons": [{
    "comparison_id": "example-pair", "dataset_id": "example",
    "model_label": "my-recorded-model", "run_id": "run-1",
    "baseline_condition": "baseline", "target_condition": "cue"
  }],
  "rows": [
    {"dataset_id": "example", "run_id": "run-1", "item_id": "q1",
     "condition": "baseline", "gold": "A", "stored_answer": "B",
     "allowed_answers": ["A", "B", "C", "D"],
     "response_text": "ANSWER: B", "response_completeness": "complete"},
    {"dataset_id": "example", "run_id": "run-1", "item_id": "q1",
     "condition": "cue", "gold": "A", "stored_answer": "A",
     "allowed_answers": ["A", "B", "C", "D"],
     "response_text": "ANSWER: A", "response_completeness": "complete"}
  ]
}
```

This one-item example illustrates the contract; it cannot establish a population result. Use null for unavailable answers/text. Completeness may be `complete`, `possibly_truncated`, or `unknown`; describe the collection evidence accurately. See schema validation for accepted values; do not infer completeness from answer correctness.

Optional `items` provide `dataset_id`, `item_id`, `question_with_options`, `definition_gold`, `source_locator`, and `provenance_status`. Optional `provenance_notes` record source claims. Neither field authenticates origin automatically.

Alternatively pass a directory containing `rows.jsonl`, `comparisons.json`, and optional `meta.json`. A standalone JSONL file is not the generic bundle contract. The metadata file can supply defaults, item context, and provenance notes.

Records pair by dataset, model, run, item, repeat, and permutation scope. Duplicate identities and broken pairings are invalid. Stored answers, parsed answers, and gold keys remain separate. The importer copies raw bytes and writes hash-pinned normalized rows and a manifest.

## Reports

`audit` writes `report.md`, `report.json`, `STATUS.txt`, captured `inputs/`, and linked evidence pages. JSON includes comparison/group metrics, controls, item influence, findings, annotations, and scoped `gates`. Rational accuracy values are represented with numerator and denominator. Entropy values are in bits.

Gates are additive report fields in version 0.2.0. Existing metric meanings are unchanged. Historical profile and importer names changed; use original source files to reimport rather than editing byte-pinned manifests in place.

Annotations are supplied separately with `--annotations FILE.jsonl`; see the [rubric](GOLD-UNIQUENESS.md). They never overwrite scores. `triage` exports review records but does not record completed human adjudication by itself.
