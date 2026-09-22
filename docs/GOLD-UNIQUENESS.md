# Gold uniqueness rubric (frozen)

Use this rubric for item-scoped annotations. It does **not** change scores. It does **not** overwrite gold, stored, or parsed answers. Product scope excludes automatic semantic gold adjudication.

## Verdicts

| Verdict | Use when |
| --- | --- |
| `unique-correct` | The stored/definition gold is the only defensible keyed answer given the stem and options. |
| `contested` | At least one other allowed letter is also a defensible keyed answer. Record the competing letter(s) in the rationale. |
| `invalid-key` | The stored/definition gold is not a defensible keyed answer. |
| `insufficient-evidence` | Stem, options, or provenance are too weak to decide uniqueness. |

Rationale text is required. Status is `proposed` or `reviewed`. Origin is `human` or `agent`. An agent `proposed` label is **not** a human review.

## Status

- `proposed`: attached for inspection; not a gold rewrite.
- `reviewed`: a named human has accepted or rejected the verdict; gold still is not overwritten by the package.

## Missing annotations

If no annotation file is supplied, the audit emits `MISSING_ANNOTATIONS` (warning). Scores stay the same.

## Example

[proposed example](../examples/annotations-hd1-proposed.jsonl) is an agent-proposed `contested` worksheet for historical-h2 `hd1`. Keep it as the historical proposed record. Human-reviewed copy: [reviewed example](../examples/annotations-hd1-reviewed.jsonl) (`status=reviewed`, `origin=human`). Neither overwrites gold.

These are historical annotation examples for an optional, unbundled collection. Source-definition and original run identifiers are provenance labels, not project file dependencies. The released copies rename dataset metadata; originals remain archived. They are not evidence of independent two-rater review.
