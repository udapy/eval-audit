# Eval Audit report

Deterministic offline report. No timestamps. Synthetic controls are labeled as controls.

## 1. Input and provenance

- audit status: `complete`
- profile: `generic-v1`
- adapter: `1`
- normalized sha256: `8324cc866bd6b15b7659b202e6d693d718dd96ee97a3807e36e7bb420ae35b96`
- records: 32

| artifact | sha256 | rows | labels |
| --- | --- | ---: | --- |
| `GENERIC` | `792616e543c76cae2f67b8c5f6c4059d32c77092013b9ed27589edec0bcc06c4` | 32 | adapter=generic, origin=source_file |

Provenance notes:
- Original synthetic paired fixture for testing generic import and measurement diagnostics.
- License: CC0 1.0. Authored 2026-09-18. Stored letters are assigned, not model outputs.
- This fixture is not a published benchmark or an independent model evaluation.
- xfer-balanced golds are 2 each of A/B/C/D. xfer-mild-skew golds are 3A+3B+1C+1D.
- Paired changes are multi-item by construction. Gold keys are not rewritten at import.

## 2. Historical results (stored answers)

| dataset | model | run | condition | n_total | n_valid | n_correct | accuracy_all | entropy_bits | pred counts |
| --- | --- | --- | --- | ---: | ---: | ---: | --- | --- | --- |
| xfer-balanced | fixture-synthetic | X1 | baseline | 8 | 8 | 6 | 3/4 | 1.811278124459133 | A:3 B:1 C:1 D:3 |
| xfer-balanced | fixture-synthetic | X1 | cue | 8 | 8 | 8 | 1/1 | 2 | A:2 B:2 C:2 D:2 |
| xfer-mild-skew | fixture-synthetic | X2 | baseline | 8 | 8 | 4 | 1/2 | 2 | A:2 B:2 C:2 D:2 |
| xfer-mild-skew | fixture-synthetic | X2 | cue | 8 | 8 | 7 | 7/8 | 1.75 | A:4 B:2 C:1 D:1 |

Paired comparisons:

| id | basis | status | n_pairs | acc drop | acc flag | entropy drop | entropy flag | selectivity |
| --- | --- | --- | ---: | --- | --- | --- | --- | --- |
| XFER-BAL | stored | complete | 8 | -1/4 | false | -0.1887218755408671 | false | null |
| XFER-BAL | strict | complete | 8 | 0/1 | false | -0.1070177095953564 | false | null |
| XFER-SKEW | stored | complete | 8 | -3/8 | false | 0.25 | true | null |
| XFER-SKEW | strict | complete | 8 | -3/8 | false | 0.25 | true | null |

## 3. Diagnostic controls

Gold-oracle and constant-letter answerers keep the historical baseline and replace the target answers. They are not model rows.

| comparison | control | n | accuracy_all | entropy | entropy drop | entropy flag |
| --- | --- | ---: | --- | --- | --- | --- |
| XFER-BAL | gold oracle | 8 | 1/1 | 2 | -0.1887218755408671 | false |
| XFER-BAL | constant A | 8 | 1/4 | 0 | 1.811278124459133 | true |
| XFER-BAL | constant B | 8 | 1/4 | 0 | 1.811278124459133 | true |
| XFER-BAL | constant C | 8 | 1/4 | 0 | 1.811278124459133 | true |
| XFER-BAL | constant D | 8 | 1/4 | 0 | 1.811278124459133 | true |
| XFER-SKEW | gold oracle | 8 | 1/1 | 1.811278124459133 | 0.1887218755408671 | true |
| XFER-SKEW | constant A | 8 | 3/8 | 0 | 2 | true |
| XFER-SKEW | constant B | 8 | 3/8 | 0 | 2 | true |
| XFER-SKEW | constant C | 8 | 1/8 | 0 | 2 | true |
| XFER-SKEW | constant D | 8 | 1/8 | 0 | 2 | true |

## 4. Item influence

Leave-one-item-out applies to both conditions. Post-hoc exclusion is sensitivity analysis, not a repaired primary result.

| comparison | item | orig acc drop | without | Δ acc | orig selectivity | without | Δ sel | evidence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| XFER-BAL | xb01 | -1/4 | -2/7 | 1/28 | null | null | null | [item](evidence/items/item_9e54ff2b8076152cb1072e05c7367417ee7-224f374a045c7005494ac9e7697035978dbdd9f6dacb3cfad16d0ef8d7674995.md) |
| XFER-BAL | xb02 | -1/4 | -2/7 | 1/28 | null | null | null | [item](evidence/items/item_86e24bf4cac04ce462801c3efcf42d033ea-39c4fa77e7ecae48004faae84beca31cb0f44c35bf3e15ee5245ff462969e4b4.md) |
| XFER-BAL | xb03 | -1/4 | -1/7 | -3/28 | null | null | null | [item](evidence/items/item_418a802708cb74fbf163a0a70b6e0b8214f-63a64de5e0b5909c2d5bde5f90c09543533a87e8100948bfe6f16528b64f3b4a.md) |
| XFER-BAL | xb04 | -1/4 | -2/7 | 1/28 | null | null | null | [item](evidence/items/item_673bb52d643d3d8f6574c6f377ee1c06904-134a0180c5b957753ea8383836e003f93dbcaccab3abfcc3939250ae8c491223.md) |
| XFER-BAL | xb05 | -1/4 | -2/7 | 1/28 | null | null | null | [item](evidence/items/item_1d00708bf8603529c9ac324273f1b292fab-49ad11571e15ee43132f861fca34e46e4f1ccb89815588a4b64ed1c33371ba88.md) |
| XFER-BAL | xb06 | -1/4 | -1/7 | -3/28 | null | null | null | [item](evidence/items/item_a02f14fdc89d6d3deb8859a15046440ade9-d9157b6c9e62f24ea3b32a98929a27df62d7911a1d0d362ae77d64fd4e903583.md) |
| XFER-BAL | xb07 | -1/4 | -2/7 | 1/28 | null | null | null | [item](evidence/items/item_befd09dbff864b6ed000530f59c83460e4d-6a4fd9603e7c91c35b4b590b22c9e30cf624384cf41c5db4823b889d54ae73ce.md) |
| XFER-BAL | xb08 | -1/4 | -2/7 | 1/28 | null | null | null | [item](evidence/items/item_ad851a8ff6b90e03cb7a4068de2151c9912-ba60b9f848b35f0b251c1ea20959e57d570dcea6433031e8dabf52ffc00994f7.md) |
| XFER-SKEW | xs01 | -3/8 | -3/7 | 3/56 | null | null | null | [item](evidence/items/item_3388354c36245dc8bfec99c5e427da12678-f011ba1da902d5bb5aa82eb99733883457767f6486f1dc651aace80c8525f6c5.md) |
| XFER-SKEW | xs02 | -3/8 | -2/7 | -5/56 | null | null | null | [item](evidence/items/item_1ac21522a6ec5ebfe3aa9465f025b902e43-8749a3f75d673c7a4a74d49c54729961fbeadabd3d945d6341a98ff2c70d385d.md) |
| XFER-SKEW | xs03 | -3/8 | -2/7 | -5/56 | null | null | null | [item](evidence/items/item_fea5a63f58ec8102d40cc3949eae4eff4ff-e9840b21ddf5dd61d1e8396dcb60898601293baff46d1324cc92e4543d1b51bd.md) |
| XFER-SKEW | xs04 | -3/8 | -2/7 | -5/56 | null | null | null | [item](evidence/items/item_3668e98a64184f997dc1ef1a4d15fb8eea3-21669e6e8606097c5ba9e1e0848ce66e20a6873c955dd271eba78a132d55d9ae.md) |
| XFER-SKEW | xs05 | -3/8 | -3/7 | 3/56 | null | null | null | [item](evidence/items/item_bacaec64c03d7a706dd1d6deeef1b849f81-8a75387c61593d82009e49de6ccd23264d23b33e45017af75207f3a95ce4ae63.md) |
| XFER-SKEW | xs06 | -3/8 | -3/7 | 3/56 | null | null | null | [item](evidence/items/item_396809296c83e1d0329e616d8108979c187-70156274863fa1c4be3d1ea5c6fda306afb115bbcaa1d90309dab7e0e07338ee.md) |
| XFER-SKEW | xs07 | -3/8 | -3/7 | 3/56 | null | null | null | [item](evidence/items/item_be5046a2c24b0863f536c2f8e95a2c936e7-8fb54ee8ae9dfeaac257450080b48b570b93f0f6c5b9d8301beaca5fc9d8553a.md) |
| XFER-SKEW | xs08 | -3/8 | -3/7 | 3/56 | null | null | null | [item](evidence/items/item_38beb192b2f1252ad8c8488886d325d770b-5a3a61c4e272204b5693680edce4d5ac99db5e8f7695aef955dfc9690ad24973.md) |

## 5. Parsing and missing fields

| basis | dataset | run | condition | n_total | n_valid | n_invalid | accuracy_all |
| --- | --- | --- | --- | ---: | ---: | ---: | --- |
| strict | xfer-balanced | X1 | baseline | 8 | 8 | 0 | 3/4 |
| strict | xfer-balanced | X1 | cue | 8 | 6 | 2 | 3/4 |
| strict | xfer-mild-skew | X2 | baseline | 8 | 8 | 0 | 1/2 |
| strict | xfer-mild-skew | X2 | cue | 8 | 8 | 0 | 7/8 |

Stored vs strict disagreements / notable parses: 2
- [X1 cue xb07](evidence/findings/PARSE_8f519864c4c36df772d3af0b2207ca6a9c-27ee6cedfeb4d6b7baee66c906665dc3710ab983877c0f3253f03854205fb996.md) status=missing
- [X1 cue xb08](evidence/findings/PARSE_2e85518c3ffe49cfb546017fdcf2672f01-c96880cfd428f89ff0722767bbd4371a4fc8e9fda036b6da0e06d3759d5422e5.md) status=invalid

## 6. Gold uniqueness annotations

Frozen rubric: `unique-correct` / `contested` / `invalid-key` / `insufficient-evidence`. Rationale text is required. Status is `proposed` or `reviewed`. Annotations never change accuracy, entropy, selectivity, gold, stored, or parsed answers.

No annotations attached. A `MISSING_ANNOTATIONS` warning is recorded. Scores are unchanged.

## 7. Limits on interpretation

- Historical flags reproduce `generic-v1` strict inequalities (accuracy drop > 1/10, entropy drop > 0.15). Equality is not a flag.
- A gold oracle or constant answerer can trigger the entropy heuristic on skewed keys. That is a measurement failure, not a detector of hidden intent.
- Leave-one-item-out is a diagnostic. It does not repair gold keys or establish that an effect is absent.
- Model labels inferred from folder names are not verified snapshots. Missing prompts, finish reasons, and timestamps stay unknown.
- Item definitions are source-code literals labeled `source_definition_not_verified_request`.
- Retrospective recognition/verbal fields are stored observations, not internal awareness.
- These convenience samples do not support statistical significance or population claims.
- Human annotations, if present, are labeled `HUMAN_ANNOTATION` and do not change scores.
- A missing annotation file is a warning (`MISSING_ANNOTATIONS`), not a repaired or worsened score.
- Gold-uniqueness verdicts are inspectable labels. They are not automatic semantic gold adjudication and do not overwrite keys.
- Reviewed `contested` / `invalid-key` items may be listed again as leave-one-item-out sensitivity. That listing does not drop them from the primary table.

## 8. Evidence index

- `info` `STORED_STRICT_DISAGREEMENT` [PARSE:8f519864c4c36df772d3af0b2207ca6a9cdeb1e330a087e55bf5fa8ba874ded5](evidence/findings/PARSE_8f519864c4c36df772d3af0b2207ca6a9c-27ee6cedfeb4d6b7baee66c906665dc3710ab983877c0f3253f03854205fb996.md) origin=computed
- `info` `STORED_STRICT_DISAGREEMENT` [PARSE:2e85518c3ffe49cfb546017fdcf2672f01ca65b0e45be7493642d9c3443131bb](evidence/findings/PARSE_2e85518c3ffe49cfb546017fdcf2672f01-c96880cfd428f89ff0722767bbd4371a4fc8e9fda036b6da0e06d3759d5422e5.md) origin=computed
- `info` `GOLD_DISTRIBUTION` [GOLD:08a1c21824a4684bbe96c277ccf17b4d78bf0bbe7434fbb1dcc6e275d995f252](evidence/findings/GOLD_08a1c21824a4684bbe96c277ccf17b4d78b-bc3422c0397657a9d5608f32e9b5fa93029d2f91e2ab421858e76e41d11fc50d.md) origin=computed
- `info` `GOLD_DISTRIBUTION` [GOLD:86684e3c0c5c8b9097a7ea592ebef592bfb0abeb2ef4db673ba48de5e91048ea](evidence/findings/GOLD_86684e3c0c5c8b9097a7ea592ebef592bfb-9c091ea6df93ea174a360ba7f1d6c4e9cc005a02b5a512637cbeea7ea3121c07.md) origin=computed
- `info` `PROVENANCE_TRUNCATION` [PROVENANCE:completeness](evidence/findings/PROVENANCE_completeness-cb79bd08c453b714b60a281c181db9840417250ed220ad6e8fdd9b3243bb0079.md) origin=computed
- `warning` `MISSING_ANNOTATIONS` [ANN:missing](evidence/findings/ANN_missing-1ba0c371a574060179db5eee4aa624aa1579b2d5ea03cb3c9f231d6286a92e1e.md) origin=computed
- `warning` `CONTROL_CONSTANT_ENTROPY_FLAG` [CTRL:XFER-BAL:constant_A](evidence/findings/CTRL_XFER-BAL_constant_A-98cfd1cf55e247dc1e71b292bc7d03329b2655f5f9d384d65f5ab52f1c3c6b21.md) origin=computed
- `warning` `CONTROL_CONSTANT_ENTROPY_FLAG` [CTRL:XFER-BAL:constant_B](evidence/findings/CTRL_XFER-BAL_constant_B-5ef9d12a53db51b79af055a02c0d38fcb929424474f50d1941b656ee4f028575.md) origin=computed
- `warning` `CONTROL_CONSTANT_ENTROPY_FLAG` [CTRL:XFER-BAL:constant_C](evidence/findings/CTRL_XFER-BAL_constant_C-d172686bfb2547ed88f39dec11f889e5d87141060fe427bff385e214e4aa9cd5.md) origin=computed
- `warning` `CONTROL_CONSTANT_ENTROPY_FLAG` [CTRL:XFER-BAL:constant_D](evidence/findings/CTRL_XFER-BAL_constant_D-7ad419af68d92bd7bb51c871e1d4a532cc9269c2805d277b95305e187b18991b.md) origin=computed
- `warning` `HISTORICAL_ENTROPY_FLAG` [ENTFLAG:XFER-SKEW:stored](evidence/findings/ENTFLAG_XFER-SKEW_stored-99062f7ec590b24da343a55d934b4dd4d6b81ce215172b5140553251c7ab5014.md) origin=computed
- `warning` `CONTROL_ORACLE_ENTROPY_FLAG` [CTRL:XFER-SKEW:gold_oracle](evidence/findings/CTRL_XFER-SKEW_gold_oracle-732e6ba61edec3f6a6d6881bd4c930ec5d9ebc327608fb4f73d85194c78d196e.md) origin=computed
- `warning` `CONTROL_CONSTANT_ENTROPY_FLAG` [CTRL:XFER-SKEW:constant_A](evidence/findings/CTRL_XFER-SKEW_constant_A-533b7d7e5a208bccef975ef4f8b25c855d00073b292f434e592fde8ff40d71bd.md) origin=computed
- `warning` `CONTROL_CONSTANT_ENTROPY_FLAG` [CTRL:XFER-SKEW:constant_B](evidence/findings/CTRL_XFER-SKEW_constant_B-257f8ac2eaae7ead1845252bb78c8fcc65f379d80b6dbab5b9d8fdaafca4ba55.md) origin=computed
- `warning` `CONTROL_CONSTANT_ENTROPY_FLAG` [CTRL:XFER-SKEW:constant_C](evidence/findings/CTRL_XFER-SKEW_constant_C-9de2e71b87c1da0608611f8c4ff5cb90a05b002e1a8874a21497ee0426040024.md) origin=computed
- `warning` `CONTROL_CONSTANT_ENTROPY_FLAG` [CTRL:XFER-SKEW:constant_D](evidence/findings/CTRL_XFER-SKEW_constant_D-b4a277d484b39e72aba8e351ccb8122f0d109de767e6fec4da755023447ab73f.md) origin=computed

