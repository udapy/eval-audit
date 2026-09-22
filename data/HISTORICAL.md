# Optional historical source inventory

The original work also referenced four historical response files: two task banks under each of the folder labels `gpt-4.1-mini` and `gpt-4.1`. These labels do not verify serving snapshots. H1 denotes the explicit-underperformance task bank; H2 denotes the evaluation-cue task bank.

The [machine-readable source contract](historical-sources.json) lists expected relative paths, byte pins, and row counts from the importer. It expects 88 response rows across four files plus a literal item-definition source. These are adapter expectations, not newly replayed results in this release.

Original raw files were not available inside the released project and have not been copied from the surrounding workspace. Their old derived reports and preparation notes remain in the excluded local archive. Default examples and tests are self-contained. Optional historical integration tests are explicitly skipped unless `EVAL_AUDIT_HISTORICAL_SOURCE` is supplied.

Run `eval-audit import-historical --source AUTHORIZED_SOURCE_DIR --out NEW_DIR` only with that separately supplied source. This is an intentional optional input requirement, not a broken local link. No archived preparation context is required by the default package.
