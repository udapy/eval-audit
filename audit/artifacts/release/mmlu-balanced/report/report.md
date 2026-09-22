# Eval Audit report

Deterministic offline report. No timestamps. Synthetic controls are labeled as controls.

## 1. Input and provenance

- audit status: `complete`
- profile: `generic-v1`
- adapter: `1`
- normalized sha256: `2c000e5db765b8648627098b058cf0e0a5736560b7708355ee7e8681d4a7dfc6`
- records: 40

| artifact | sha256 | rows | labels |
| --- | --- | ---: | --- |
| `GENERIC` | `d46477de1aad16e5731fa9b1644eed7a0902204ffc2242588d373fb4f7fc45b0` | 40 | adapter=generic, origin=source_file |

Provenance notes:
- Real model inference: meta-llama/Llama-3.1-8B-Instruct on MMLU balanced items
- Baseline: standard zero-shot prompt
- Target: answer-key leak in system message (gold-oracle control)

## 2. Historical results (stored answers)

| dataset | model | run | condition | n_total | n_valid | n_correct | accuracy_all | entropy_bits | pred counts |
| --- | --- | --- | --- | ---: | ---: | ---: | --- | --- | --- |
| mmlu-math | meta-llama-3.1-8b-instruct | MMLU_BALANCED_RUN | baseline | 10 | 10 | 7 | 7/10 | 1.685475297227335 | A:5 B:3 C:1 D:1 |
| mmlu-math | meta-llama-3.1-8b-instruct | MMLU_BALANCED_RUN | cue | 10 | 10 | 10 | 1/1 | 1.970950594454669 | A:2 B:3 C:3 D:2 |
| mmlu-security | meta-llama-3.1-8b-instruct | MMLU_BALANCED_RUN | baseline | 10 | 10 | 10 | 1/1 | 1.970950594454669 | A:3 B:3 C:2 D:2 |
| mmlu-security | meta-llama-3.1-8b-instruct | MMLU_BALANCED_RUN | cue | 10 | 10 | 10 | 1/1 | 1.970950594454669 | A:3 B:3 C:2 D:2 |

Paired comparisons:

| id | basis | status | n_pairs | acc drop | acc flag | entropy drop | entropy flag | selectivity |
| --- | --- | --- | ---: | --- | --- | --- | --- | --- |
| MMLU-CS-COMP | stored | complete | 10 | 0/1 | false | 0 | false | null |
| MMLU-CS-COMP | strict | complete | 10 | 0/1 | false | null | null | null |
| MMLU-MATH-COMP | stored | complete | 10 | -3/10 | false | -0.285475297227334 | false | null |
| MMLU-MATH-COMP | strict | complete | 10 | 0/1 | false | null | null | null |

## 3. Diagnostic controls

Gold-oracle and constant-letter answerers keep the historical baseline and replace the target answers. They are not model rows.

| comparison | control | n | accuracy_all | entropy | entropy drop | entropy flag |
| --- | --- | ---: | --- | --- | --- | --- |
| MMLU-CS-COMP | gold oracle | 10 | 1/1 | 1.970950594454669 | 0 | false |
| MMLU-CS-COMP | constant A | 10 | 3/10 | 0 | 1.970950594454669 | true |
| MMLU-CS-COMP | constant B | 10 | 3/10 | 0 | 1.970950594454669 | true |
| MMLU-CS-COMP | constant C | 10 | 1/5 | 0 | 1.970950594454669 | true |
| MMLU-CS-COMP | constant D | 10 | 1/5 | 0 | 1.970950594454669 | true |
| MMLU-MATH-COMP | gold oracle | 10 | 1/1 | 1.970950594454669 | -0.285475297227334 | false |
| MMLU-MATH-COMP | constant A | 10 | 1/5 | 0 | 1.685475297227335 | true |
| MMLU-MATH-COMP | constant B | 10 | 3/10 | 0 | 1.685475297227335 | true |
| MMLU-MATH-COMP | constant C | 10 | 3/10 | 0 | 1.685475297227335 | true |
| MMLU-MATH-COMP | constant D | 10 | 1/5 | 0 | 1.685475297227335 | true |

## 4. Item influence

Leave-one-item-out applies to both conditions. Post-hoc exclusion is sensitivity analysis, not a repaired primary result.

| comparison | item | orig acc drop | without | Δ acc | orig selectivity | without | Δ sel | evidence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| MMLU-CS-COMP | cs01 | 0/1 | 0/1 | 0/1 | null | null | null | [item](evidence/items/item_cebea26c15053cf6762f3ee8b59f103ed9e-97d05e4e3ccc3e9ced205237e4fe6b1d94b469ca471703a7a08a1b9d8d5d4393.md) |
| MMLU-CS-COMP | cs02 | 0/1 | 0/1 | 0/1 | null | null | null | [item](evidence/items/item_0a3ac9394f22b0e5a4487c0b6aa2bf13669-8cc255bb622d274702164003c9cfac12474f090f6753230b947fa2c42bb60ddd.md) |
| MMLU-CS-COMP | cs03 | 0/1 | 0/1 | 0/1 | null | null | null | [item](evidence/items/item_7a5a70513387effe9845a7f3598cd0f27ca-ce38868df71bef428e0b6c0016eebaa9217a7787768d0d42460ded1ea2ad2578.md) |
| MMLU-CS-COMP | cs04 | 0/1 | 0/1 | 0/1 | null | null | null | [item](evidence/items/item_2d06db66e2f30a25e3c6830283f548ad9a7-4a951b827254cbf712a08f468a94aef279b3e60a82cfdddcb7e09f42c42dc26d.md) |
| MMLU-CS-COMP | cs05 | 0/1 | 0/1 | 0/1 | null | null | null | [item](evidence/items/item_556c0422539022ccaf1bd53f2a15eba59e0-35e6baa87ec686c341649aa4a4ffc7376102b139133da771c3ff700d8e188659.md) |
| MMLU-CS-COMP | cs06 | 0/1 | 0/1 | 0/1 | null | null | null | [item](evidence/items/item_01351c82b542ae628bfb3e970db92df65c9-b85bd6bf6cd81007dc1e18da711c7f3cbad2a41bbc3f51a264fa8b57fd392f85.md) |
| MMLU-CS-COMP | cs07 | 0/1 | 0/1 | 0/1 | null | null | null | [item](evidence/items/item_1862b4a371977f628b10c4225720a341205-8a2be46e634de71b715fbdf46992cb64e872e0623108acd2b011619435884266.md) |
| MMLU-CS-COMP | cs08 | 0/1 | 0/1 | 0/1 | null | null | null | [item](evidence/items/item_7e9b765faddb83edb1c4cf7fd06c418b7e9-8308a26bb16716d17ab49f20e618b28ba8f7511fc1f02c5da22ae5677e2a086e.md) |
| MMLU-CS-COMP | cs09 | 0/1 | 0/1 | 0/1 | null | null | null | [item](evidence/items/item_eeeeea300831827afc2c3e0816a80c40219-307dcfd23aac31088f37de1440bb7ef9d01dd62f98661d41b4f27ed1ae23b741.md) |
| MMLU-CS-COMP | cs10 | 0/1 | 0/1 | 0/1 | null | null | null | [item](evidence/items/item_302875f4de3513be618596be55dc459edfe-2d4d94bc811e383f54ae4c9a7017075b1fe51fa80bac3d2b551a898882e3e515.md) |
| MMLU-MATH-COMP | em01 | -3/10 | -1/3 | 1/30 | null | null | null | [item](evidence/items/item_a084414d8403aa885bc36dbbbfd19034405-f696ae72e42e0c2adf063cea868aa45a6ca66c722ada2f4cb8f9d8d23aea066e.md) |
| MMLU-MATH-COMP | em02 | -3/10 | -1/3 | 1/30 | null | null | null | [item](evidence/items/item_3e446b75ec407b6cc320c5076fcbde8509b-be60eb6fe55f2546f487cf785a1f35634299b89c8257b9499864e5dc30a54c17.md) |
| MMLU-MATH-COMP | em03 | -3/10 | -1/3 | 1/30 | null | null | null | [item](evidence/items/item_c3b1e03f3cd26cc1d439e15d9c718b85b18-130e5c146de1912db61ec34af51e1ebb0c8b313cd9bdab3271cb685649af8396.md) |
| MMLU-MATH-COMP | em04 | -3/10 | -1/3 | 1/30 | null | null | null | [item](evidence/items/item_aafc7d177169cf34650559dc1f3e4caf971-d8e11f7bdba7aaf6d5db2a6e7bfecfcede07ee955855a917eb13348d67483a42.md) |
| MMLU-MATH-COMP | em05 | -3/10 | -1/3 | 1/30 | null | null | null | [item](evidence/items/item_a986f1f0a3b3cddc338be9978b024ebd2df-b619a5683c1b0599c4274c8451e9696c1a9247905632c61889b7ea18315c2aac.md) |
| MMLU-MATH-COMP | em06 | -3/10 | -2/9 | -7/90 | null | null | null | [item](evidence/items/item_ee18bc95fd385f2f84763fd958168714418-cf28040973b1530fd8f84cada1e602fa725e4a0b169eb0f18391a39631fe8556.md) |
| MMLU-MATH-COMP | em07 | -3/10 | -1/3 | 1/30 | null | null | null | [item](evidence/items/item_4fb2f9d9dbbdc9f927ee97fe2aa758063db-1f5367358a1195a32c9c9593ab8a538a0868294a168c02e9cf94a2654ea5dc9f.md) |
| MMLU-MATH-COMP | em08 | -3/10 | -2/9 | -7/90 | null | null | null | [item](evidence/items/item_aa00c3f20bd3adbdc4ce3af687ab7b97b75-7c476d0d849e70ae21a9fcf25ce3fba70084347a2011d2c729d7e8df786036c3.md) |
| MMLU-MATH-COMP | em09 | -3/10 | -1/3 | 1/30 | null | null | null | [item](evidence/items/item_7e190afab995b0b80bdc9296d637208c2b9-e8b687a79c9af4113a5cf5ebcc1971cdda556de34ab84e5ea01ef611145f2a35.md) |
| MMLU-MATH-COMP | em10 | -3/10 | -2/9 | -7/90 | null | null | null | [item](evidence/items/item_2f30e853efd5f86eb2857fe158243cf0958-0c07adcbf80af9a09ebab92321ccac5b23fb785344b4c0804f6e4ea72377dcfc.md) |

## 5. Parsing and missing fields

| basis | dataset | run | condition | n_total | n_valid | n_invalid | accuracy_all |
| --- | --- | --- | --- | ---: | ---: | ---: | --- |
| strict | mmlu-math | MMLU_BALANCED_RUN | baseline | 10 | 0 | 10 | 0/1 |
| strict | mmlu-math | MMLU_BALANCED_RUN | cue | 10 | 0 | 10 | 0/1 |
| strict | mmlu-security | MMLU_BALANCED_RUN | baseline | 10 | 0 | 10 | 0/1 |
| strict | mmlu-security | MMLU_BALANCED_RUN | cue | 10 | 0 | 10 | 0/1 |

Stored vs strict disagreements / notable parses: 40
- [MMLU_BALANCED_RUN baseline em01](evidence/findings/PARSE_50d78b99f6b9e1dfb445962a85e81b2387-ef9d3abb8159c1f00b2616ba9b1c74fbc795b5e821b018a9edf377279938f2ad.md) status=missing
- [MMLU_BALANCED_RUN baseline em02](evidence/findings/PARSE_ab19fb64d7000a4035533b14eed5a724d2-3df714f47a700039fefa33ad40c70035a62fd7e0f74a07bc39139399a211484c.md) status=missing
- [MMLU_BALANCED_RUN baseline em03](evidence/findings/PARSE_08c51ba7e6f5088414454bc18f15da08d2-4cc37aa7101cb4bff2158d007d98fea533befb0f88a27f7ee7d9863af11369d9.md) status=missing
- [MMLU_BALANCED_RUN baseline em04](evidence/findings/PARSE_6694e769123448d47ffbffb1beb6ad86fb-9c6d5d9a87a83a4c33a46bca5e7f11b121c87075a7e020c7be0b0c6dd5eb7271.md) status=missing
- [MMLU_BALANCED_RUN baseline em05](evidence/findings/PARSE_4e032a585ef32c34bc31a9c3d4ec208b4d-6a8327087e40657f3e2e32f609409d4a7f122469fca1248f6216b7605fca94da.md) status=missing
- [MMLU_BALANCED_RUN baseline em06](evidence/findings/PARSE_ea7d719a177e03c89262657d27ea100518-49d9328857c88440ad724cb72b890555dc1e63a77bc0e41d9d9d1d862aa188b8.md) status=missing
- [MMLU_BALANCED_RUN baseline em07](evidence/findings/PARSE_2dee335a403bef7bbe9694ea37ef74ad4b-f54e4d211e5b007dbf7c5e291cd22ef456055c984986a162fa95a29c4f01dbe9.md) status=missing
- [MMLU_BALANCED_RUN baseline em08](evidence/findings/PARSE_37c9d57e7062b10aab1ed8e0d994cdf50e-18acfd931c22cd3ce3cf080617a5a465b1b2417131f235f63c27f6c475509ed9.md) status=missing
- [MMLU_BALANCED_RUN baseline em09](evidence/findings/PARSE_ed5637d4858d86c5a5b116f87b2dde301c-bc171ffc1d300b1a2989a2b335fa4500c4cec97e6913fc9c7485ea28ff6b64e0.md) status=missing
- [MMLU_BALANCED_RUN baseline em10](evidence/findings/PARSE_d24b64185ea6a32a965409264a4b50bf19-f8a5a8a1119969c20c641c6fd60b23b58060334d3c7e26a9778ed1241afdd3ad.md) status=missing
- [MMLU_BALANCED_RUN cue em01](evidence/findings/PARSE_ac7579a4a09de764f9270d2f73cb624714-3850b7e14c8ea47f28e1491da57876942c49ceec4e0281fa01e46182c23d8538.md) status=missing
- [MMLU_BALANCED_RUN cue em02](evidence/findings/PARSE_b21870db980c600e6130505f354f74bff4-bead5076f1e5390c37627482376f7b97ca91d5da1f0875386090df77b159e056.md) status=missing
- [MMLU_BALANCED_RUN cue em03](evidence/findings/PARSE_355df18e4e6304fc9ea9b2bd6e0543ce10-25c0cf050002eb93a183c9ae0b45c28955ec32b1edab8104dbef1f178ba401b2.md) status=missing
- [MMLU_BALANCED_RUN cue em04](evidence/findings/PARSE_14f0e50f599e65041c882451bdb9c3ec96-e1f0442315f1ab5e3bbde771987e973439360fd149590cc8341011784859c697.md) status=missing
- [MMLU_BALANCED_RUN cue em05](evidence/findings/PARSE_c612d751efd5bab328aed4cc38269faf19-5b45ae0543d99ab46d69fbf24145dd67db5029c6533ae85062ebed8511cc8444.md) status=missing
- [MMLU_BALANCED_RUN cue em06](evidence/findings/PARSE_b711790362d8ac15b8e8dd269ca45413b9-cb902edd60976411be6badb5e7151453aa11d93745ad86f4981ac7e3ac1994af.md) status=missing
- [MMLU_BALANCED_RUN cue em07](evidence/findings/PARSE_b401f8811931598a66f604428109a4af8c-d98a1c42afa1deb26401d3d2d6ae2b3b51a3425bd084b87052d850b49f565f97.md) status=missing
- [MMLU_BALANCED_RUN cue em08](evidence/findings/PARSE_6fc98ace6e4f75f8114697839f98852cab-b12c0d303771f582a2a21ae7b276cde60e7f293029d00f9f264db833dbd39a49.md) status=missing
- [MMLU_BALANCED_RUN cue em09](evidence/findings/PARSE_573f6c97b05638648596fb4c6e1753328e-ae02c262371190da0d0340009ec9d9575847ef6e0b0a0dd79d750c30257cbba5.md) status=missing
- [MMLU_BALANCED_RUN cue em10](evidence/findings/PARSE_812c12336821c147a122140fa2cc16106c-efef9d6688edce67c906e53b10aecabec90dba7ffc3d6ce7a6ace9525d0f3cf8.md) status=missing
- [MMLU_BALANCED_RUN baseline cs01](evidence/findings/PARSE_d439cf39b04bea032ebcdf8da46a202442-cdd17daa2d1e4eb45756a336ffcb11e839a408a2c16736f02bbd75fda0c7c7b3.md) status=missing
- [MMLU_BALANCED_RUN baseline cs02](evidence/findings/PARSE_4309167e3b195c2bdee2ff68971a5638f5-75e1657aa82f4730a079d37d6ecd6b16a1dc2a284daaec1e8fa0f9423798b6fd.md) status=missing
- [MMLU_BALANCED_RUN baseline cs03](evidence/findings/PARSE_e7d8ba2a26676e2c29f28b418f4698156e-4fd21134c09034f945e1aac79e0f7dca0b547f8baebc79e1cd0a0507f8dae58a.md) status=missing
- [MMLU_BALANCED_RUN baseline cs04](evidence/findings/PARSE_442f57281f056dd3c08fc1ec0c34e37914-9fb7703c3bf7c9508e0c3f0a6e49302c5ab2ff56223ff61b3e5e0afb6ec8ca9a.md) status=missing
- [MMLU_BALANCED_RUN baseline cs05](evidence/findings/PARSE_c8c9239febe89874f34d3001ec8af91cc9-3b91f1439f9cd1f7f932f179b67014415d9a9c94cc65de9d48e9394b368d651e.md) status=missing
- [MMLU_BALANCED_RUN baseline cs06](evidence/findings/PARSE_e924413e04b099a240434dcbdf66c5cda6-945faf225c923101c40f54f51cc5af0a33d62d749c0e3baec98a2e30f8b957b9.md) status=missing
- [MMLU_BALANCED_RUN baseline cs07](evidence/findings/PARSE_561f4e40c8fd24ada1135032cfa0f0caba-7badc0ff3c61a3e562ea43c9d0cdd5c46f1d025eed071b466c088928f98d2123.md) status=missing
- [MMLU_BALANCED_RUN baseline cs08](evidence/findings/PARSE_abd9e881d4cc6ff4ac3e05e7794cd9d08a-51942cf6101c5797f0f04481a9ed227ec1c83c307c48f0e24b61f2ad081b6724.md) status=missing
- [MMLU_BALANCED_RUN baseline cs09](evidence/findings/PARSE_11bdd86fb5f32e4004985da52ac01d314d-27b6c9433c579b819c98188744e7e0126301a3b12a78b6e3aaa0e6ecedfb6142.md) status=missing
- [MMLU_BALANCED_RUN baseline cs10](evidence/findings/PARSE_572adf6e50fedac06605369f248eb0b0a4-2756db50feb12bb9312d1193587262f12dfb13d0f9e4cad8113642accfe52ebc.md) status=missing
- [MMLU_BALANCED_RUN cue cs01](evidence/findings/PARSE_880a02b0e8938396420d7e3357fd7fcdaa-e7932bde69dded423d152ba21867e14d64dfb456d363b7135ccd3f6c77f3d55c.md) status=missing
- [MMLU_BALANCED_RUN cue cs02](evidence/findings/PARSE_4dea6e6209b9a586f09e74ee2215993279-5039890a4cbd72a218e8f201c789850183461246d5dee1ee29798ca27c25e3e6.md) status=missing
- [MMLU_BALANCED_RUN cue cs03](evidence/findings/PARSE_99d031a7d420cae89101c7510542c865ce-080fe447504bef96054ff6e25e1e54249a45b8a8fc9aaef1b2cd46614cf9fd7d.md) status=missing
- [MMLU_BALANCED_RUN cue cs04](evidence/findings/PARSE_5e6f8be1c3318516a48eeedc5b9641bcc0-e341592b5c38354b923e8de4008a3c83359af259026aa356bd80fad2204ad2da.md) status=missing
- [MMLU_BALANCED_RUN cue cs05](evidence/findings/PARSE_eb1ffd1fb615a8150c3e883386fbe70362-a2cc56fbb0cfac3af47dde77d00a8f673406e0bdb52e3f2a1c8f7f94d3f004f3.md) status=missing
- [MMLU_BALANCED_RUN cue cs06](evidence/findings/PARSE_c04b1bd2fda2f58fc1567290628230fbe5-0522045b602298f88c561b736c07a8b852d8114c82b95eef5048d4e61692305f.md) status=missing
- [MMLU_BALANCED_RUN cue cs07](evidence/findings/PARSE_29b1133a21293d56173506e69904d45904-21ae287878d88f65c69a76937dc9bb20c349d20178bdffbb9cbc327f96877ed0.md) status=missing
- [MMLU_BALANCED_RUN cue cs08](evidence/findings/PARSE_a27db15af3fac2b95c02fe7d0d868d939e-e9467289d2292c8b0201d2a175cdcee0ab64666128f36c048836f3316d71f8d0.md) status=missing
- [MMLU_BALANCED_RUN cue cs09](evidence/findings/PARSE_3e242ea4e005ab42d709f547a8b84f4437-f130ac78a4dee342a6999a02fb5e819fa66407d30c63be1e4b0832d89a73c853.md) status=missing
- [MMLU_BALANCED_RUN cue cs10](evidence/findings/PARSE_609d2b06780891da14b775d08ceeaae90d-d580c85fbb8155582275c363b33be9f380db3ecf154445cac0c763a56b7df80f.md) status=missing

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

- `info` `STORED_STRICT_DISAGREEMENT` [PARSE:50d78b99f6b9e1dfb445962a85e81b2387bc9677a6a5aff9bcc71f70ee783bca](evidence/findings/PARSE_50d78b99f6b9e1dfb445962a85e81b2387-ef9d3abb8159c1f00b2616ba9b1c74fbc795b5e821b018a9edf377279938f2ad.md) origin=computed
- `info` `STORED_STRICT_DISAGREEMENT` [PARSE:ab19fb64d7000a4035533b14eed5a724d213f1a3a0dac3657b14bccfd1671f28](evidence/findings/PARSE_ab19fb64d7000a4035533b14eed5a724d2-3df714f47a700039fefa33ad40c70035a62fd7e0f74a07bc39139399a211484c.md) origin=computed
- `info` `STORED_STRICT_DISAGREEMENT` [PARSE:08c51ba7e6f5088414454bc18f15da08d20654155dfdd40679804d5e315e539f](evidence/findings/PARSE_08c51ba7e6f5088414454bc18f15da08d2-4cc37aa7101cb4bff2158d007d98fea533befb0f88a27f7ee7d9863af11369d9.md) origin=computed
- `info` `STORED_STRICT_DISAGREEMENT` [PARSE:6694e769123448d47ffbffb1beb6ad86fbe98d66ec10410b54f7131218b967e1](evidence/findings/PARSE_6694e769123448d47ffbffb1beb6ad86fb-9c6d5d9a87a83a4c33a46bca5e7f11b121c87075a7e020c7be0b0c6dd5eb7271.md) origin=computed
- `info` `STORED_STRICT_DISAGREEMENT` [PARSE:4e032a585ef32c34bc31a9c3d4ec208b4dfa78f80da1a3800d7b4e49b304d848](evidence/findings/PARSE_4e032a585ef32c34bc31a9c3d4ec208b4d-6a8327087e40657f3e2e32f609409d4a7f122469fca1248f6216b7605fca94da.md) origin=computed
- `info` `STORED_STRICT_DISAGREEMENT` [PARSE:ea7d719a177e03c89262657d27ea100518cbae5c4eddb2bedf74c32a555959e7](evidence/findings/PARSE_ea7d719a177e03c89262657d27ea100518-49d9328857c88440ad724cb72b890555dc1e63a77bc0e41d9d9d1d862aa188b8.md) origin=computed
- `info` `STORED_STRICT_DISAGREEMENT` [PARSE:2dee335a403bef7bbe9694ea37ef74ad4b34df0a9880dc07812682afe5c9ee38](evidence/findings/PARSE_2dee335a403bef7bbe9694ea37ef74ad4b-f54e4d211e5b007dbf7c5e291cd22ef456055c984986a162fa95a29c4f01dbe9.md) origin=computed
- `info` `STORED_STRICT_DISAGREEMENT` [PARSE:37c9d57e7062b10aab1ed8e0d994cdf50e18b65ed9fba006c717f4ac4e5cf2cf](evidence/findings/PARSE_37c9d57e7062b10aab1ed8e0d994cdf50e-18acfd931c22cd3ce3cf080617a5a465b1b2417131f235f63c27f6c475509ed9.md) origin=computed
- `info` `STORED_STRICT_DISAGREEMENT` [PARSE:ed5637d4858d86c5a5b116f87b2dde301cb9a8038a91646f7d92897913ce8adf](evidence/findings/PARSE_ed5637d4858d86c5a5b116f87b2dde301c-bc171ffc1d300b1a2989a2b335fa4500c4cec97e6913fc9c7485ea28ff6b64e0.md) origin=computed
- `info` `STORED_STRICT_DISAGREEMENT` [PARSE:d24b64185ea6a32a965409264a4b50bf19a69837af039d4bc012072a43713bfe](evidence/findings/PARSE_d24b64185ea6a32a965409264a4b50bf19-f8a5a8a1119969c20c641c6fd60b23b58060334d3c7e26a9778ed1241afdd3ad.md) origin=computed
- `info` `STORED_STRICT_DISAGREEMENT` [PARSE:ac7579a4a09de764f9270d2f73cb624714ac335910ea16b54c4d0bbf15f8307a](evidence/findings/PARSE_ac7579a4a09de764f9270d2f73cb624714-3850b7e14c8ea47f28e1491da57876942c49ceec4e0281fa01e46182c23d8538.md) origin=computed
- `info` `STORED_STRICT_DISAGREEMENT` [PARSE:b21870db980c600e6130505f354f74bff47d079e4a35765e28400112a5fe3219](evidence/findings/PARSE_b21870db980c600e6130505f354f74bff4-bead5076f1e5390c37627482376f7b97ca91d5da1f0875386090df77b159e056.md) origin=computed
- `info` `STORED_STRICT_DISAGREEMENT` [PARSE:355df18e4e6304fc9ea9b2bd6e0543ce1068041dead2c489c7cb3b9aa5958bef](evidence/findings/PARSE_355df18e4e6304fc9ea9b2bd6e0543ce10-25c0cf050002eb93a183c9ae0b45c28955ec32b1edab8104dbef1f178ba401b2.md) origin=computed
- `info` `STORED_STRICT_DISAGREEMENT` [PARSE:14f0e50f599e65041c882451bdb9c3ec962dfb62d99cb53c83009ca182aa0205](evidence/findings/PARSE_14f0e50f599e65041c882451bdb9c3ec96-e1f0442315f1ab5e3bbde771987e973439360fd149590cc8341011784859c697.md) origin=computed
- `info` `STORED_STRICT_DISAGREEMENT` [PARSE:c612d751efd5bab328aed4cc38269faf198c39b586fe374e830d89245b998466](evidence/findings/PARSE_c612d751efd5bab328aed4cc38269faf19-5b45ae0543d99ab46d69fbf24145dd67db5029c6533ae85062ebed8511cc8444.md) origin=computed
- `info` `STORED_STRICT_DISAGREEMENT` [PARSE:b711790362d8ac15b8e8dd269ca45413b9f1f6c4165e9faa7305cb5f3609732d](evidence/findings/PARSE_b711790362d8ac15b8e8dd269ca45413b9-cb902edd60976411be6badb5e7151453aa11d93745ad86f4981ac7e3ac1994af.md) origin=computed
- `info` `STORED_STRICT_DISAGREEMENT` [PARSE:b401f8811931598a66f604428109a4af8cffdcabfbff67a96e0f2ed4e1316ea4](evidence/findings/PARSE_b401f8811931598a66f604428109a4af8c-d98a1c42afa1deb26401d3d2d6ae2b3b51a3425bd084b87052d850b49f565f97.md) origin=computed
- `info` `STORED_STRICT_DISAGREEMENT` [PARSE:6fc98ace6e4f75f8114697839f98852cabd5dd426b921a4a3c20b7987a461809](evidence/findings/PARSE_6fc98ace6e4f75f8114697839f98852cab-b12c0d303771f582a2a21ae7b276cde60e7f293029d00f9f264db833dbd39a49.md) origin=computed
- `info` `STORED_STRICT_DISAGREEMENT` [PARSE:573f6c97b05638648596fb4c6e1753328e52ffbf4e97bb4f518e7e1555b04bfc](evidence/findings/PARSE_573f6c97b05638648596fb4c6e1753328e-ae02c262371190da0d0340009ec9d9575847ef6e0b0a0dd79d750c30257cbba5.md) origin=computed
- `info` `STORED_STRICT_DISAGREEMENT` [PARSE:812c12336821c147a122140fa2cc16106c11c1aee12d32c923ccde7356c12f7b](evidence/findings/PARSE_812c12336821c147a122140fa2cc16106c-efef9d6688edce67c906e53b10aecabec90dba7ffc3d6ce7a6ace9525d0f3cf8.md) origin=computed
- `info` `STORED_STRICT_DISAGREEMENT` [PARSE:d439cf39b04bea032ebcdf8da46a202442e02aba217b08de3e34c9b842680963](evidence/findings/PARSE_d439cf39b04bea032ebcdf8da46a202442-cdd17daa2d1e4eb45756a336ffcb11e839a408a2c16736f02bbd75fda0c7c7b3.md) origin=computed
- `info` `STORED_STRICT_DISAGREEMENT` [PARSE:4309167e3b195c2bdee2ff68971a5638f5039151dfd4d798a8bdfd807271c84d](evidence/findings/PARSE_4309167e3b195c2bdee2ff68971a5638f5-75e1657aa82f4730a079d37d6ecd6b16a1dc2a284daaec1e8fa0f9423798b6fd.md) origin=computed
- `info` `STORED_STRICT_DISAGREEMENT` [PARSE:e7d8ba2a26676e2c29f28b418f4698156ebea0030b3a41b8a3c62558518b0541](evidence/findings/PARSE_e7d8ba2a26676e2c29f28b418f4698156e-4fd21134c09034f945e1aac79e0f7dca0b547f8baebc79e1cd0a0507f8dae58a.md) origin=computed
- `info` `STORED_STRICT_DISAGREEMENT` [PARSE:442f57281f056dd3c08fc1ec0c34e37914d9761df1365da2c568294dafcc6eb1](evidence/findings/PARSE_442f57281f056dd3c08fc1ec0c34e37914-9fb7703c3bf7c9508e0c3f0a6e49302c5ab2ff56223ff61b3e5e0afb6ec8ca9a.md) origin=computed
- `info` `STORED_STRICT_DISAGREEMENT` [PARSE:c8c9239febe89874f34d3001ec8af91cc9b94cdee0e7756b4f5160a9fa26d386](evidence/findings/PARSE_c8c9239febe89874f34d3001ec8af91cc9-3b91f1439f9cd1f7f932f179b67014415d9a9c94cc65de9d48e9394b368d651e.md) origin=computed
- `info` `STORED_STRICT_DISAGREEMENT` [PARSE:e924413e04b099a240434dcbdf66c5cda6cfe1d73dee9275c03ddad6ba2a212e](evidence/findings/PARSE_e924413e04b099a240434dcbdf66c5cda6-945faf225c923101c40f54f51cc5af0a33d62d749c0e3baec98a2e30f8b957b9.md) origin=computed
- `info` `STORED_STRICT_DISAGREEMENT` [PARSE:561f4e40c8fd24ada1135032cfa0f0caba3bbf487214104f616e8cadb26b017c](evidence/findings/PARSE_561f4e40c8fd24ada1135032cfa0f0caba-7badc0ff3c61a3e562ea43c9d0cdd5c46f1d025eed071b466c088928f98d2123.md) origin=computed
- `info` `STORED_STRICT_DISAGREEMENT` [PARSE:abd9e881d4cc6ff4ac3e05e7794cd9d08a15d8fd588897b53c3e74842c7ddb0b](evidence/findings/PARSE_abd9e881d4cc6ff4ac3e05e7794cd9d08a-51942cf6101c5797f0f04481a9ed227ec1c83c307c48f0e24b61f2ad081b6724.md) origin=computed
- `info` `STORED_STRICT_DISAGREEMENT` [PARSE:11bdd86fb5f32e4004985da52ac01d314dd2719a7687b156c09de0f55a397b3b](evidence/findings/PARSE_11bdd86fb5f32e4004985da52ac01d314d-27b6c9433c579b819c98188744e7e0126301a3b12a78b6e3aaa0e6ecedfb6142.md) origin=computed
- `info` `STORED_STRICT_DISAGREEMENT` [PARSE:572adf6e50fedac06605369f248eb0b0a4820d72d429fff5c4cba23a8825338f](evidence/findings/PARSE_572adf6e50fedac06605369f248eb0b0a4-2756db50feb12bb9312d1193587262f12dfb13d0f9e4cad8113642accfe52ebc.md) origin=computed
- `info` `STORED_STRICT_DISAGREEMENT` [PARSE:880a02b0e8938396420d7e3357fd7fcdaa475ab9a8c1ce598ef46039a2bdb295](evidence/findings/PARSE_880a02b0e8938396420d7e3357fd7fcdaa-e7932bde69dded423d152ba21867e14d64dfb456d363b7135ccd3f6c77f3d55c.md) origin=computed
- `info` `STORED_STRICT_DISAGREEMENT` [PARSE:4dea6e6209b9a586f09e74ee221599327983eb20dc2273bfd78854cb1e5831d2](evidence/findings/PARSE_4dea6e6209b9a586f09e74ee2215993279-5039890a4cbd72a218e8f201c789850183461246d5dee1ee29798ca27c25e3e6.md) origin=computed
- `info` `STORED_STRICT_DISAGREEMENT` [PARSE:99d031a7d420cae89101c7510542c865ce503ba338227259e83e882cabc9f26e](evidence/findings/PARSE_99d031a7d420cae89101c7510542c865ce-080fe447504bef96054ff6e25e1e54249a45b8a8fc9aaef1b2cd46614cf9fd7d.md) origin=computed
- `info` `STORED_STRICT_DISAGREEMENT` [PARSE:5e6f8be1c3318516a48eeedc5b9641bcc0d44daf9af3b7be3982199fc12f1fcc](evidence/findings/PARSE_5e6f8be1c3318516a48eeedc5b9641bcc0-e341592b5c38354b923e8de4008a3c83359af259026aa356bd80fad2204ad2da.md) origin=computed
- `info` `STORED_STRICT_DISAGREEMENT` [PARSE:eb1ffd1fb615a8150c3e883386fbe7036277efdef3741f97fde2232f22ea3821](evidence/findings/PARSE_eb1ffd1fb615a8150c3e883386fbe70362-a2cc56fbb0cfac3af47dde77d00a8f673406e0bdb52e3f2a1c8f7f94d3f004f3.md) origin=computed
- `info` `STORED_STRICT_DISAGREEMENT` [PARSE:c04b1bd2fda2f58fc1567290628230fbe56a019c93b77e287fa1b7cfd4147dad](evidence/findings/PARSE_c04b1bd2fda2f58fc1567290628230fbe5-0522045b602298f88c561b736c07a8b852d8114c82b95eef5048d4e61692305f.md) origin=computed
- `info` `STORED_STRICT_DISAGREEMENT` [PARSE:29b1133a21293d56173506e69904d45904a4de7f25f3c45108b5bca348e866a7](evidence/findings/PARSE_29b1133a21293d56173506e69904d45904-21ae287878d88f65c69a76937dc9bb20c349d20178bdffbb9cbc327f96877ed0.md) origin=computed
- `info` `STORED_STRICT_DISAGREEMENT` [PARSE:a27db15af3fac2b95c02fe7d0d868d939e6b84c3d5668a16b715428735e4e1a0](evidence/findings/PARSE_a27db15af3fac2b95c02fe7d0d868d939e-e9467289d2292c8b0201d2a175cdcee0ab64666128f36c048836f3316d71f8d0.md) origin=computed
- `info` `STORED_STRICT_DISAGREEMENT` [PARSE:3e242ea4e005ab42d709f547a8b84f4437e76bd0877f0e3d1bdb83c1c04887a4](evidence/findings/PARSE_3e242ea4e005ab42d709f547a8b84f4437-f130ac78a4dee342a6999a02fb5e819fa66407d30c63be1e4b0832d89a73c853.md) origin=computed
- `info` `STORED_STRICT_DISAGREEMENT` [PARSE:609d2b06780891da14b775d08ceeaae90d776f699cff1e7d2fe8b8c2f4e4378b](evidence/findings/PARSE_609d2b06780891da14b775d08ceeaae90d-d580c85fbb8155582275c363b33be9f380db3ecf154445cac0c763a56b7df80f.md) origin=computed
- `info` `GOLD_DISTRIBUTION` [GOLD:3e52d30eafa019a33cd8020d52226b591f0961e4c9583f7ac1340658cc4760f3](evidence/findings/GOLD_3e52d30eafa019a33cd8020d52226b591f0-063c464f6952f5d6c9f71496ae8affdf5551554a98b06d54bdc37a375d28c5c9.md) origin=computed
- `info` `GOLD_DISTRIBUTION` [GOLD:a864702a3fab39ede000d40fe9bcaf861b3a5bbbf284612b8f5b2ac3ace68f17](evidence/findings/GOLD_a864702a3fab39ede000d40fe9bcaf861b3-e9f572919b0a8d5f38e79ed468f3a94082b49f709bf12c82c596420728f37df3.md) origin=computed
- `warning` `MISSING_ANNOTATIONS` [ANN:missing](evidence/findings/ANN_missing-1ba0c371a574060179db5eee4aa624aa1579b2d5ea03cb3c9f231d6286a92e1e.md) origin=computed
- `warning` `INSUFFICIENT_DATA` [INSUFFICIENT:MMLU-CS-COMP:strict](evidence/findings/INSUFFICIENT_MMLU-CS-COMP_strict-b599e722560a3451b28ab1922c0081285b01b0751e4b67e52cfd9fa3d762dc7e.md) origin=computed
- `warning` `CONTROL_CONSTANT_ENTROPY_FLAG` [CTRL:MMLU-CS-COMP:constant_A](evidence/findings/CTRL_MMLU-CS-COMP_constant_A-d905492d4a882f480b9b7599f564ea6afc4a987904d032ba6fdbd0fb84202468.md) origin=computed
- `warning` `CONTROL_CONSTANT_ENTROPY_FLAG` [CTRL:MMLU-CS-COMP:constant_B](evidence/findings/CTRL_MMLU-CS-COMP_constant_B-a46489ef6449bd0757c086c27adf9ceea99d259714694524e3c9fd0cbfe15bb8.md) origin=computed
- `warning` `CONTROL_CONSTANT_ENTROPY_FLAG` [CTRL:MMLU-CS-COMP:constant_C](evidence/findings/CTRL_MMLU-CS-COMP_constant_C-0efa31e9f776e6a550151397d43290d577d7e0a344ad9d89900990e597a6663d.md) origin=computed
- `warning` `CONTROL_CONSTANT_ENTROPY_FLAG` [CTRL:MMLU-CS-COMP:constant_D](evidence/findings/CTRL_MMLU-CS-COMP_constant_D-0d83d202bc3929734f771e9ea9cc6b081547d41089bf4cad0537f18b69a89a99.md) origin=computed
- `warning` `INSUFFICIENT_DATA` [INSUFFICIENT:MMLU-MATH-COMP:strict](evidence/findings/INSUFFICIENT_MMLU-MATH-COMP_strict-4377a28b21dd64e522eeba00a98efaa2443bb6230e48526f9b06570706627d3b.md) origin=computed
- `warning` `CONTROL_CONSTANT_ENTROPY_FLAG` [CTRL:MMLU-MATH-COMP:constant_A](evidence/findings/CTRL_MMLU-MATH-COMP_constant_A-fa5701b6e394f45f343c8784fd86f495128385e6f6149f21fbe60d9793259b49.md) origin=computed
- `warning` `CONTROL_CONSTANT_ENTROPY_FLAG` [CTRL:MMLU-MATH-COMP:constant_B](evidence/findings/CTRL_MMLU-MATH-COMP_constant_B-98a7ea121e29599df091e27155c7d9ec8fcd43e7ee612c7d78578556da60ca0e.md) origin=computed
- `warning` `CONTROL_CONSTANT_ENTROPY_FLAG` [CTRL:MMLU-MATH-COMP:constant_C](evidence/findings/CTRL_MMLU-MATH-COMP_constant_C-140d185731c7b29aa1d84484d1c2c376ef189e8a5f4b3b59fd5a385e5ddf2538.md) origin=computed
- `warning` `CONTROL_CONSTANT_ENTROPY_FLAG` [CTRL:MMLU-MATH-COMP:constant_D](evidence/findings/CTRL_MMLU-MATH-COMP_constant_D-0e6d2ccd7def1def4d4678fd10bef09abfb15bb1a8252dc2b40f3b41824dd9ef.md) origin=computed

