# Terminology and diagnostic boundaries

| Term | Meaning in this package |
| --- | --- |
| MCQ | Multiple-choice question |
| Item / row / pair | A question; one saved answer record; baseline and target records matched for a comparison |
| Gold key | Recorded reference answer; its correctness is not independently established by the loader |
| Stored answer | Answer label saved by the original collection process |
| Strict answer basis | Answer parsed from a saved `ANSWER: X` line; unsupported formatting is not automatically model failure |
| Baseline / target | The two conditions named by a comparison; `cue` is a target label in bundled examples |
| Answer-leak cue | Prompt supplies the gold key to a model; response can still be missing or incorrect |
| Gold oracle | Computed control that always returns the recorded gold key; no model invocation |
| Entropy | Shannon entropy of valid predicted letters, in bits; missing answers are excluded |
| Entropy drop | Baseline entropy minus target entropy; positive means more concentrated target letters |
| Oracle entropy drop | Baseline prediction entropy minus gold-key entropy; depends on both distributions |
| Accuracy | Correct answers divided by all rows (`accuracy_all`) or valid answers (`accuracy_valid`); these denominators differ with missingness |
| Leave-one-item-out (LOO) | Recompute a comparison after excluding each paired item in turn; sensitivity only, never silent exclusion from the primary result |
| Selectivity | Historical comparison of accuracy drops between two named banks; absent for generic examples without a bank mapping |
| Provenance | Where bytes came from and what collection claims are actually supported |
| SHA-256 / byte pin | Content checksum used to detect file changes; does not authenticate the originating experiment |
| Triage | A queue for human review. Withheld model/condition fields do not guarantee that content itself is blind |
| Reviewed annotation | A recorded human judgment; does not mutate stored answers or gold keys, nor imply two independent raters |
| Fixture | Constructed regression example, not a model run or held-out benchmark |

## Gates in report.json and the CLI

| Gate | Implemented check | Boundary |
| --- | --- | --- |
| G0 | Manifest/source consistency and duplicate artifact hashes | Identical bytes do not establish independent or duplicate runs |
| G1 | Stored/strict divergence, recorded completeness, available option identity | Missing option identity means not assessed, not a passed order check |
| G2 | Whether a gold oracle exceeds the historical entropy-drop rule against this baseline | The current profiles use strict `> 0.15` bits; this is a reproduced heuristic, not a calibrated universal threshold |
| G3 | Whether exactly one item's correctness change accounts for a nonzero paired accuracy change | Other forms of influence and dependence can remain |
| G4 | Behavioral claim remains unestablished | Human interpretation and independent evidence are required |

`CLEAR`, `FLAGGED`, `INSUFFICIENT_DATA`, and `NOT_ASSESSED` describe scoped engineering checks. `NOT_ESTABLISHED` describes the behavioral-claim boundary. Report completion means processing finished, not that a scientific conclusion is established.

Historical H1/H2 identifiers denote two saved task banks in the optional importer. M1/M2 and F1/F2 are original run IDs, not independent verification of model snapshots. These collections are not bundled. The source scripts and profiles retain these technical IDs solely for explicitly supplied historical replay.
