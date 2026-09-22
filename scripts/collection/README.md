# Optional collection source records

These scripts record how responses were requested. They are separate from the offline package and are never invoked by `make check`, `make evidence`, or release packaging. Do not run them to reproduce existing results: use saved bundles instead.

They reference Hugging Face Inference and dataset-server endpoints. Running them requires an explicit new collection decision and credentials. No collection was run for this release.

The three collection scripts write under a fresh `EVAL_AUDIT_COLLECTION_OUT` directory (default `.tmp/collection/<example>`), refusing an existing bundle. Helpers are in `datasets/`. The balanced collection script's original output shape differs from the normalized saved bundle; it is a source record, not a byte-stable regeneration command.

`mmlu-balanced.py` embeds local security/math questions with an unverified MMLU attribution. `mmlu-skewed.py` selects the first 25 statistics rows. `arc-challenge.py` selects the first qualifying four-option A–D science rows. These are not random representative samples. `datasets/key_distribution.py` inspects capped subject slices, not entire benchmark distributions.

The helper saves extracted content (or reasoning content), not full provider envelopes. Its completeness field is inferred from extracted letters, not provider finish reasons. Answer-leak prompts are interventions; they are distinct from the deterministic gold-oracle control.
