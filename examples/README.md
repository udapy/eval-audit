# Bundled examples

Use the [catalog](../data/README.md) for counts, models, source hashes, evidence limitations, and generated reports. Each folder contains `bundle.json`, the saved source consumed by the generic importer.

| Folder | Purpose |
| --- | --- |
| `transfer-fixture` | Original synthetic paired answers with balanced and mildly skewed keys |
| `external-eval` | Assigned responses on locally embedded security/math questions; synthetic despite its old model label |
| `mmlu-balanced` | Saved responses on local security/math questions; claimed benchmark origin unverified |
| `mmlu-skewed` | Saved responses on a selected MMLU statistics slice |
| `arc-challenge` | Saved responses on a selected ARC science slice, including missing responses |

The `eval-audit demo` command creates a separate small synthetic demonstration. No example requires a model call to audit it.

The proposed and reviewed annotation files are renamed derivatives of optional historical annotations. They preserve the recorded human/agent distinction and do not change scores. Their historical dataset is not bundled; they are not annotations for the five examples above. See the [annotation rubric](../docs/GOLD-UNIQUENESS.md).
