# Eval Audit report

Deterministic offline report. No timestamps. Synthetic controls are labeled as controls.

## 1. Input and provenance

- audit status: `complete`
- profile: `generic-v1`
- adapter: `1`
- normalized sha256: `67d5fd6b407c1d4595a5f1e624aab95d8baff4730fcfe2e6bbcbf8b91ea3a5a2`
- records: 50

| artifact | sha256 | rows | labels |
| --- | --- | ---: | --- |
| `GENERIC` | `633f7d95782157bd09ee72a66f9c842673088cc248f38b66c5b0da6107c8c887` | 50 | adapter=generic, origin=source_file |

Provenance notes:
- Model: Qwen/Qwen3-8B via HF Inference API
- Benchmark: ARC-Challenge (allenai/ai2_arc; Clark et al., 2018)
- License: CC-BY-SA 4.0
- Condition &#x27;baseline&#x27;: standard zero-shot MCQ prompt
- Condition &#x27;cue&#x27;: prompt includes gold answer leak in system message

## 2. Historical results (stored answers)

| dataset | model | run | condition | n_total | n_valid | n_correct | accuracy_all | entropy_bits | pred counts |
| --- | --- | --- | --- | ---: | ---: | ---: | --- | --- | --- |
| arc-challenge | qwen-3-8b | ARC_CHALLENGE_RUN | baseline | 25 | 19 | 17 | 17/25 | 1.847420120052174 | A:4 B:5 C:8 D:2 |
| arc-challenge | qwen-3-8b | ARC_CHALLENGE_RUN | cue | 25 | 23 | 22 | 22/25 | 1.687941045236421 | A:4 B:8 C:10 D:1 |

Paired comparisons:

| id | basis | status | n_pairs | acc drop | acc flag | entropy drop | entropy flag | selectivity |
| --- | --- | --- | ---: | --- | --- | --- | --- | --- |
| ARC-CHALLENGE-COMP | stored | complete | 25 | -1/5 | false | 0.1594790748157537 | true | null |
| ARC-CHALLENGE-COMP | strict | complete | 25 | 0/1 | false | null | null | null |

## 3. Diagnostic controls

Gold-oracle and constant-letter answerers keep the historical baseline and replace the target answers. They are not model rows.

| comparison | control | n | accuracy_all | entropy | entropy drop | entropy flag |
| --- | --- | ---: | --- | --- | --- | --- |
| ARC-CHALLENGE-COMP | gold oracle | 25 | 1/1 | 1.810699332842307 | 0.03672078720986738 | false |
| ARC-CHALLENGE-COMP | constant A | 25 | 1/5 | 0 | 1.847420120052174 | true |
| ARC-CHALLENGE-COMP | constant B | 25 | 8/25 | 0 | 1.847420120052174 | true |
| ARC-CHALLENGE-COMP | constant C | 25 | 2/5 | 0 | 1.847420120052174 | true |
| ARC-CHALLENGE-COMP | constant D | 25 | 2/25 | 0 | 1.847420120052174 | true |

## 4. Item influence

Leave-one-item-out applies to both conditions. Post-hoc exclusion is sensitivity analysis, not a repaired primary result.

| comparison | item | orig acc drop | without | Δ acc | orig selectivity | without | Δ sel | evidence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ARC-CHALLENGE-COMP | MCAS_2002_8_11 | -1/5 | -5/24 | 1/120 | null | null | null | [item](evidence/items/item_c8431ec8067e9a791400f43009c4f97048c-447a4c58e66cd6c0fc34cffe79260dde4ce1e8864eb5b1e6309239b223cf87ee.md) |
| ARC-CHALLENGE-COMP | MCAS_2003_8_11 | -1/5 | -5/24 | 1/120 | null | null | null | [item](evidence/items/item_754213a76def7339fa7a10a66e781106628-d544faffea40836e2428575baa0852e34b33199a7e81617c8733cd1416066fb6.md) |
| ARC-CHALLENGE-COMP | MCAS_2006_9_44 | -1/5 | -5/24 | 1/120 | null | null | null | [item](evidence/items/item_0168c8bf42e5b380ba63cf767f4fef2d564-162ea45a1d4eddc7de5dc6bcfc0d352db608a57a6f2334e9c11be5951f1a494f.md) |
| ARC-CHALLENGE-COMP | MCAS_2014_5_7 | -1/5 | -5/24 | 1/120 | null | null | null | [item](evidence/items/item_9f962c24ef849439301b54afe8073c74447-8c6a5bf3e7711d41effb05fb7f84e257ec4e83eff0fc0351704a8b24ef4a3934.md) |
| ARC-CHALLENGE-COMP | MDSA_2007_8_3 | -1/5 | -5/24 | 1/120 | null | null | null | [item](evidence/items/item_5c3c67bdb4495fe0f0d85340f5f06d646e1-cb53a1e81847c3f0d71f2ca31f85c34c00a394a5590832669571cede7072a700.md) |
| ARC-CHALLENGE-COMP | Mercury_402216 | -1/5 | -5/24 | 1/120 | null | null | null | [item](evidence/items/item_74d10674484ac94b6db297497e2e38a7595-157399cfedc1ba8f06c9f84444bdc4f9cd692b58a0bc73fdb33e12ea055694ca.md) |
| ARC-CHALLENGE-COMP | Mercury_404894 | -1/5 | -5/24 | 1/120 | null | null | null | [item](evidence/items/item_526e33888e12d8de07ae91e9f35a5627f39-e026fea3d05498057f49f404e47155b89da5d10e920814b8b09f8614d4dfe7c3.md) |
| ARC-CHALLENGE-COMP | Mercury_407327 | -1/5 | -5/24 | 1/120 | null | null | null | [item](evidence/items/item_2b5752624babc670a477ce5f9557556a357-25f1fcd73f23498dc65cbeab8be0c93d704126fb6ff04b852c924c8202453bad.md) |
| ARC-CHALLENGE-COMP | Mercury_7012740 | -1/5 | -5/24 | 1/120 | null | null | null | [item](evidence/items/item_3829a2b3a1981ad95fb68fcb21a7edb65e3-749ab81f7effe77626a5d8c8174a1c250bffd08a6a89869bd1920f36f0aa5e44.md) |
| ARC-CHALLENGE-COMP | Mercury_7086660 | -1/5 | -5/24 | 1/120 | null | null | null | [item](evidence/items/item_754ffbd37f5e5d4c217b84508c1035edb21-e9964312851f6675ba92b7666217e0ee7a12f2e62e92b920aaac2480efa089ac.md) |
| ARC-CHALLENGE-COMP | Mercury_7094290 | -1/5 | -1/6 | -1/30 | null | null | null | [item](evidence/items/item_e55588bbb88bbfe9cf05ccb8cd88bd7c204-b194fc7580b2b17798361b797f1c7241b0b9a72477ad55e37207f49cf0a2ace1.md) |
| ARC-CHALLENGE-COMP | Mercury_7166425 | -1/5 | -5/24 | 1/120 | null | null | null | [item](evidence/items/item_2bf7d2b4b6997fda47dd16c57bd1c076cb9-60b4da289e05492fd65fd3eea9614f0601fcea5dfa9f78dc5d75e740938b4b7f.md) |
| ARC-CHALLENGE-COMP | Mercury_7168805 | -1/5 | -5/24 | 1/120 | null | null | null | [item](evidence/items/item_a62672cd3a166e840de0cbd425fda63da10-7068e11f5859ac957e08dd33d68bb3d10287df764564a44f7161944fb64834a9.md) |
| ARC-CHALLENGE-COMP | Mercury_7175875 | -1/5 | -5/24 | 1/120 | null | null | null | [item](evidence/items/item_2f7ae3dfdca04f137c131a2fe1e991d16c9-5b5ccbb7925f7eabf4f601377f1c1a248945cef37f28cba34fb766fc89b1688f.md) |
| ARC-CHALLENGE-COMP | Mercury_7186358 | -1/5 | -5/24 | 1/120 | null | null | null | [item](evidence/items/item_af7c7524d009d59dc43b084b6b5c104f29e-8d4ede2838a0bd5db1e204676569f23b141f45d942039bcb5b5a1e4ee56be5e7.md) |
| ARC-CHALLENGE-COMP | Mercury_7186568 | -1/5 | -1/6 | -1/30 | null | null | null | [item](evidence/items/item_b664095951ae4fbef313e7bfb043527659a-bcd29d917c5c72fc3375879fed21d749da401d3b5dfa551f694300d22ff6460d.md) |
| ARC-CHALLENGE-COMP | Mercury_7212993 | -1/5 | -5/24 | 1/120 | null | null | null | [item](evidence/items/item_a6cbaaa2f44e611b5d7c7af064484512858-8ec7f366d2bd5bd593b9fe9bdb919f77424a202e92177a31fd9a08a2a5ffe4f0.md) |
| ARC-CHALLENGE-COMP | Mercury_7250058 | -1/5 | -1/6 | -1/30 | null | null | null | [item](evidence/items/item_97658899c0233b87066fc078a604aec7e09-00b93c09200bf23abe527a8566c4540c5ebfb0c88fa3c2b38362f2efcd07dab0.md) |
| ARC-CHALLENGE-COMP | Mercury_7270393 | -1/5 | -1/6 | -1/30 | null | null | null | [item](evidence/items/item_b62d5b40a5b348ff8202a22759458e8ffe2-a563329ff9ced8480ecdeda085aa72e5fcc5f16c41e4a0fc41aa014ffea0541f.md) |
| ARC-CHALLENGE-COMP | Mercury_LBS10610 | -1/5 | -5/24 | 1/120 | null | null | null | [item](evidence/items/item_45700ca1fb1fefc4ae6f2f657bd1502c4ae-29e9d65773bb10e333d6537636b2fce293a15458b4d88b914f485fa839a872ba.md) |
| ARC-CHALLENGE-COMP | Mercury_SC_405086 | -1/5 | -5/24 | 1/120 | null | null | null | [item](evidence/items/item_fb874a0251bb7243a7f248b5ef0c7384fd0-47041bc84264ad38ca09fd2c2b63a950bc9f36dd9263d0c49cdfd521c65b21e5.md) |
| ARC-CHALLENGE-COMP | Mercury_SC_407400 | -1/5 | -5/24 | 1/120 | null | null | null | [item](evidence/items/item_d89724de4175e793750361d1fa84371a9fd-b63f6e0c3a9f25d7fdc6afc8b623b70f4405e110cb9794844ab324cc0c6a0a01.md) |
| ARC-CHALLENGE-COMP | Mercury_SC_408547 | -1/5 | -1/6 | -1/30 | null | null | null | [item](evidence/items/item_8055b2ff5f8f63c997780547f40cd06bba9-8693dadc5eb63bf691be0d22c84ecc2fda3004c44ca34639b2ed0d74cce44962.md) |
| ARC-CHALLENGE-COMP | Mercury_SC_409171 | -1/5 | -5/24 | 1/120 | null | null | null | [item](evidence/items/item_bffb9f0fe66c9b904eeea0e16b3070e27d9-6003a1cb092347120c31f05200723e55b09341f033749d9022401ebe0718840f.md) |
| ARC-CHALLENGE-COMP | Mercury_SC_413240 | -1/5 | -5/24 | 1/120 | null | null | null | [item](evidence/items/item_06cdc2eda67bbe2898c482b9e8dfb0a2665-d6212ae7a15b25691f68a8aae96a1d672acd9f6662a588a1c5b033feab3172bf.md) |

## 5. Parsing and missing fields

| basis | dataset | run | condition | n_total | n_valid | n_invalid | accuracy_all |
| --- | --- | --- | --- | ---: | ---: | ---: | --- |
| strict | arc-challenge | ARC_CHALLENGE_RUN | baseline | 25 | 0 | 25 | 0/1 |
| strict | arc-challenge | ARC_CHALLENGE_RUN | cue | 25 | 0 | 25 | 0/1 |

Stored vs strict disagreements / notable parses: 42
- [ARC_CHALLENGE_RUN baseline MCAS_2002_8_11](evidence/findings/PARSE_894cca88bc8a1ce6e3420a013fc7694334-a0abc7d31cc08027795903f92aa3ff923d19369003a4f63b12e170e451034833.md) status=missing
- [ARC_CHALLENGE_RUN baseline MCAS_2003_8_11](evidence/findings/PARSE_1f2123c5e27f51da6b0fe928596d6bd77b-0bb97bd8a6a49dfe1bc9b1269f0a6c3996a2aa558bce2f48a0b69c61909c8402.md) status=missing
- [ARC_CHALLENGE_RUN baseline MCAS_2006_9_44](evidence/findings/PARSE_2f3a42281878ecac2234f868b485cdba9e-6a11111b78f68ba322ee0ab4d249a8eb2b3d615d5f60d33079b13f01b3130336.md) status=missing
- [ARC_CHALLENGE_RUN baseline MCAS_2014_5_7](evidence/findings/PARSE_faac79e2c0233099d485bd4150f7c5a369-2bc0828d46a039c06fcf60ff154da7207a72885e05637c1626b247ce1acb1f65.md) status=missing
- [ARC_CHALLENGE_RUN baseline MDSA_2007_8_3](evidence/findings/PARSE_8da69b55d805f480ed8d86f8a601e207aa-e96db01409126ef852703f03672e6c8e566b4abbe10c38c63ba6afdcf7be9dd9.md) status=missing
- [ARC_CHALLENGE_RUN baseline Mercury_402216](evidence/findings/PARSE_2beeff1cf8552fc85711af7400647d0e2f-faf0ebc283166db9e9f36cbcbca915cb21d0a856115b434e1d09df1cbcf94bbc.md) status=missing
- [ARC_CHALLENGE_RUN baseline Mercury_407327](evidence/findings/PARSE_41f66d297ee1d51ee213d1a8346be3aaa6-1f733117725a85d6525eb8aa2c360ce0a4e6f7c4029e2f231df94b1449877acf.md) status=missing
- [ARC_CHALLENGE_RUN baseline Mercury_7012740](evidence/findings/PARSE_d6efd1307f9abfe15b0898b2472e9ba246-b80e7623566f72e62a5d8086a8db8af6bc3b7572e28b804484ffb4560b2d07da.md) status=missing
- [ARC_CHALLENGE_RUN baseline Mercury_7086660](evidence/findings/PARSE_fc651d6266b2b4c8526928d22d4da8511d-4c5cdccbb22026c436237f0d42269562ae4ae43c65a131073ae873e26cb1e569.md) status=missing
- [ARC_CHALLENGE_RUN baseline Mercury_7094290](evidence/findings/PARSE_34800bdfc3b63830007d2a8351267ddf40-87e85f0e29e984f93cdb8d6958d7b22de871e78f2f6a05de5bf32aef9ebead5a.md) status=missing
- [ARC_CHALLENGE_RUN baseline Mercury_7166425](evidence/findings/PARSE_d3c90ab3e49a4104286847da12865e7ce3-8c1dd8d90fc395f3b3543e85b1f1437196775691f947b079feaf923e0a7727b3.md) status=missing
- [ARC_CHALLENGE_RUN baseline Mercury_7168805](evidence/findings/PARSE_2c86f1e7bbe3932d9497b7af9c4a72fa15-e3956f69dbd7a11385182b4f6c6c9d39ca12fcc1918b42b9aa40c49ee0866b34.md) status=missing
- [ARC_CHALLENGE_RUN baseline Mercury_7175875](evidence/findings/PARSE_61b694ad566911debb6bcd55a54a56e14e-a4073d03abef5a410a3faba5d9559207702a54551b03914f419549fb6b7b816c.md) status=missing
- [ARC_CHALLENGE_RUN baseline Mercury_7212993](evidence/findings/PARSE_a736c56e033d1d9c0c95a07576cb7fa09c-16b12b5b76bacc21d511e544035173a21b0b6ca22d8350086222c26616b41043.md) status=missing
- [ARC_CHALLENGE_RUN baseline Mercury_LBS10610](evidence/findings/PARSE_1acebff481d8db7006596bcb14fff1cbe1-bf680153b9b200ae94aebfade4e58d40460376f1e018d62bf1f77509b536904d.md) status=missing
- [ARC_CHALLENGE_RUN baseline Mercury_SC_405086](evidence/findings/PARSE_1c4ebd8b4cf90cb91344b9517747af8bc2-cf2948edbe7066c795cba6f428a0a06e3767dd65546f4e2ef349ed0a895d14e5.md) status=missing
- [ARC_CHALLENGE_RUN baseline Mercury_SC_407400](evidence/findings/PARSE_84ce8b7e238a080a20ce0692eabddaf699-88164bf702f6e265c7aa2304eeaf8c2a37f0731cf19eb6a293df0235b5d2a475.md) status=missing
- [ARC_CHALLENGE_RUN baseline Mercury_SC_409171](evidence/findings/PARSE_8f390e37950559cd87eba8e214c99225d1-0a93060d0f0bd6d22958069b61e85e645e93de383aafcebddcdd6d618a7b5977.md) status=missing
- [ARC_CHALLENGE_RUN baseline Mercury_SC_413240](evidence/findings/PARSE_950e8dd8cccfc9d558f276913c3264ff7c-f3655307f32b923289ac6c7fc58fccfbe027b4dff32aa0857a2011973bbf455c.md) status=missing
- [ARC_CHALLENGE_RUN cue MCAS_2002_8_11](evidence/findings/PARSE_6aab19e049796c0974ce2e74872547a364-5ba6d8ccd587a58d17220ee1c702d1a507c885789e3310257d5616777a2d60d1.md) status=missing
- [ARC_CHALLENGE_RUN cue MCAS_2003_8_11](evidence/findings/PARSE_18b4d70006bd9e618d7c20728063725e69-ca7802e63f0d6b004fc1282c346ff37446f14230ba4a11e210bca61093e69b1a.md) status=missing
- [ARC_CHALLENGE_RUN cue MCAS_2006_9_44](evidence/findings/PARSE_8d926bc18400009f112b03088c887e3875-18409ef2cf1099365518fa648b94a7fb16dd529e818b3c7dc74d5911dbbf6d0b.md) status=missing
- [ARC_CHALLENGE_RUN cue MCAS_2014_5_7](evidence/findings/PARSE_efdd2b19c23cef62bb109b659c07a64431-f68290c71acc37985a9472f61319fad3581bd5a640e685d9fb88ba5ebc872a49.md) status=missing
- [ARC_CHALLENGE_RUN cue MDSA_2007_8_3](evidence/findings/PARSE_a19f4c7f496eb03d0ad54d7a7d9c70b3fd-d6748e4ff5359f1ace4a14cc6e8b6ebbf644fd7bc457e6070794f31d25022656.md) status=missing
- [ARC_CHALLENGE_RUN cue Mercury_402216](evidence/findings/PARSE_fefdbe02326bf2a5b0ab3ca626c8fe1d9e-9160e6a4849be7b18d7c26b536b5ab5f5183b9bc24d719130f2986ca4d027fcd.md) status=missing
- [ARC_CHALLENGE_RUN cue Mercury_407327](evidence/findings/PARSE_1e3ffe3144f229520a9da698055fad51fa-4a23ef7e99bb4ac8a91ead84dbba9ea043c02bd1914e60a5ab9c3727c078c6d4.md) status=missing
- [ARC_CHALLENGE_RUN cue Mercury_7012740](evidence/findings/PARSE_e25a3b1976df38a0cbbd98deb444e3144b-addb9266f5c7ba8752442b27fb08f4a6ab36fa6218139abe905769aadc714358.md) status=missing
- [ARC_CHALLENGE_RUN cue Mercury_7086660](evidence/findings/PARSE_aa47f158b670a61ec95e9bbe03cf724c24-ddb44f4d6c3d03b9ff1fc51ba2fd142f2a7c158841a14aa804b64c35a8582903.md) status=missing
- [ARC_CHALLENGE_RUN cue Mercury_7094290](evidence/findings/PARSE_722590f0f4c2a7ea306d4c4fa80a82da14-f7011c4a8cc0db72ff7dde97bb63fa0da3d12a761a03581ad0c99da7ef6f758b.md) status=missing
- [ARC_CHALLENGE_RUN cue Mercury_7166425](evidence/findings/PARSE_14892c5c4f97cff677c9a3291a3f1e3522-563f65c80768f7130903d6645b1bc4e2cff54a4d6acc047614b12082299da2d1.md) status=missing
- [ARC_CHALLENGE_RUN cue Mercury_7168805](evidence/findings/PARSE_1e0a328df3e03c47ca27ecb07bd38717fa-ea63dc1058fd75cbffb85cf1833dd3866a8b29ca037cbeeb65e54f60e3d43ce0.md) status=missing
- [ARC_CHALLENGE_RUN cue Mercury_7175875](evidence/findings/PARSE_a3e9fde0f37e2fa32a4f5338c0fd05df89-b63581e252de4f623205317d2946fc50a7779c717d95e0f420b4064489a4081b.md) status=missing
- [ARC_CHALLENGE_RUN cue Mercury_7186568](evidence/findings/PARSE_ba232e0f47da4c64b50c263dc4de8e6378-fa0caad856eb426351b031feb926941c975586a03608d645b1b425e6056cfdec.md) status=missing
- [ARC_CHALLENGE_RUN cue Mercury_7212993](evidence/findings/PARSE_564ee302ead1868c6cac4c9caea36e2303-43687d1d1e46d369efe02b7e44ac46be58dcda9223b2aa4e76f50571a18a5c94.md) status=missing
- [ARC_CHALLENGE_RUN cue Mercury_7250058](evidence/findings/PARSE_6843dc76749d74880826a0c88662938e9a-8f9bf9a9e9c5c4787fceedb196cb47c55e0e0f678429afc747303dcd73e64ae7.md) status=missing
- [ARC_CHALLENGE_RUN cue Mercury_7270393](evidence/findings/PARSE_7dd4118ff51cf19d481bf10bf627ad3ffe-f20cbda4103ad0f42ad2d8ce62a695a9116cf97110634c8f1cdc5ee69e2a0ef0.md) status=missing
- [ARC_CHALLENGE_RUN cue Mercury_LBS10610](evidence/findings/PARSE_ee766c64bf31e64212bf8c1d862c0462bf-81fe292ffca4b6f5d7d01c6a3d2bf044e3715760334dc826b620225c8315b101.md) status=missing
- [ARC_CHALLENGE_RUN cue Mercury_SC_405086](evidence/findings/PARSE_ddd5497b44db015980ed133d91e6bf053d-dfc49e8db698b70d1d42ec43e7b85cdd6b2da6f2aa02d7e1e27a4517a0e1f965.md) status=missing
- [ARC_CHALLENGE_RUN cue Mercury_SC_407400](evidence/findings/PARSE_8b5137f27e4cd4a569f64a9cb1c0f3dbf4-96d24a94796bac205879257a454ab9a3868c44a00a189f7c531e46b6fabce5f3.md) status=missing
- [ARC_CHALLENGE_RUN cue Mercury_SC_408547](evidence/findings/PARSE_069e0f481cc9cac83e79f0d5c42ce8411b-4672ed9ff3724b3b2b8f526bc1b0f8f3313b7b2958f0d6ab0a97f7d99847c477.md) status=missing
- [ARC_CHALLENGE_RUN cue Mercury_SC_409171](evidence/findings/PARSE_549a3090e7410a9c788c36846b0f9777ae-411c9bb81f08bac381e2c18ca01392c074ed5b6c11d3eedf589ca5212f7c9986.md) status=missing
- [ARC_CHALLENGE_RUN cue Mercury_SC_413240](evidence/findings/PARSE_7bbaaccdf136d123395b8cf30aa5bb464d-b6219cdd040126597d3c65137a215b0576ce03f49c9733105305433f4720ad28.md) status=missing

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

- `info` `STORED_STRICT_DISAGREEMENT` [PARSE:894cca88bc8a1ce6e3420a013fc7694334b94250743f980f8fcc10730a2a6630](evidence/findings/PARSE_894cca88bc8a1ce6e3420a013fc7694334-a0abc7d31cc08027795903f92aa3ff923d19369003a4f63b12e170e451034833.md) origin=computed
- `info` `STORED_STRICT_DISAGREEMENT` [PARSE:1f2123c5e27f51da6b0fe928596d6bd77bfb17a9aed28c68a40d2ad916c0defd](evidence/findings/PARSE_1f2123c5e27f51da6b0fe928596d6bd77b-0bb97bd8a6a49dfe1bc9b1269f0a6c3996a2aa558bce2f48a0b69c61909c8402.md) origin=computed
- `info` `STORED_STRICT_DISAGREEMENT` [PARSE:2f3a42281878ecac2234f868b485cdba9e54bf683af642dfeaebc899b33903cc](evidence/findings/PARSE_2f3a42281878ecac2234f868b485cdba9e-6a11111b78f68ba322ee0ab4d249a8eb2b3d615d5f60d33079b13f01b3130336.md) origin=computed
- `info` `STORED_STRICT_DISAGREEMENT` [PARSE:faac79e2c0233099d485bd4150f7c5a369e06ebc6b7d41788c8f68624b8451b2](evidence/findings/PARSE_faac79e2c0233099d485bd4150f7c5a369-2bc0828d46a039c06fcf60ff154da7207a72885e05637c1626b247ce1acb1f65.md) origin=computed
- `info` `STORED_STRICT_DISAGREEMENT` [PARSE:8da69b55d805f480ed8d86f8a601e207aa55326a2d5cdc5874cb9529537b0d75](evidence/findings/PARSE_8da69b55d805f480ed8d86f8a601e207aa-e96db01409126ef852703f03672e6c8e566b4abbe10c38c63ba6afdcf7be9dd9.md) origin=computed
- `info` `STORED_STRICT_DISAGREEMENT` [PARSE:2beeff1cf8552fc85711af7400647d0e2f7a4083296d5ff9bff925743fe5aebf](evidence/findings/PARSE_2beeff1cf8552fc85711af7400647d0e2f-faf0ebc283166db9e9f36cbcbca915cb21d0a856115b434e1d09df1cbcf94bbc.md) origin=computed
- `info` `STORED_STRICT_DISAGREEMENT` [PARSE:41f66d297ee1d51ee213d1a8346be3aaa6e71960686ba798fa09e7503a8877ae](evidence/findings/PARSE_41f66d297ee1d51ee213d1a8346be3aaa6-1f733117725a85d6525eb8aa2c360ce0a4e6f7c4029e2f231df94b1449877acf.md) origin=computed
- `info` `STORED_STRICT_DISAGREEMENT` [PARSE:d6efd1307f9abfe15b0898b2472e9ba2468d97abb496a656b5f59fa3f300da2e](evidence/findings/PARSE_d6efd1307f9abfe15b0898b2472e9ba246-b80e7623566f72e62a5d8086a8db8af6bc3b7572e28b804484ffb4560b2d07da.md) origin=computed
- `info` `STORED_STRICT_DISAGREEMENT` [PARSE:fc651d6266b2b4c8526928d22d4da8511d077fdd6f7a5217cbe52484e6f4b2ac](evidence/findings/PARSE_fc651d6266b2b4c8526928d22d4da8511d-4c5cdccbb22026c436237f0d42269562ae4ae43c65a131073ae873e26cb1e569.md) origin=computed
- `info` `STORED_STRICT_DISAGREEMENT` [PARSE:34800bdfc3b63830007d2a8351267ddf40cd4b1190cc4287a2cd006663b55239](evidence/findings/PARSE_34800bdfc3b63830007d2a8351267ddf40-87e85f0e29e984f93cdb8d6958d7b22de871e78f2f6a05de5bf32aef9ebead5a.md) origin=computed
- `info` `STORED_STRICT_DISAGREEMENT` [PARSE:d3c90ab3e49a4104286847da12865e7ce3d0182734b6d85e8351346dc908202d](evidence/findings/PARSE_d3c90ab3e49a4104286847da12865e7ce3-8c1dd8d90fc395f3b3543e85b1f1437196775691f947b079feaf923e0a7727b3.md) origin=computed
- `info` `STORED_STRICT_DISAGREEMENT` [PARSE:2c86f1e7bbe3932d9497b7af9c4a72fa152c4edf148eb2d14e0a8e8c59f189c9](evidence/findings/PARSE_2c86f1e7bbe3932d9497b7af9c4a72fa15-e3956f69dbd7a11385182b4f6c6c9d39ca12fcc1918b42b9aa40c49ee0866b34.md) origin=computed
- `info` `STORED_STRICT_DISAGREEMENT` [PARSE:61b694ad566911debb6bcd55a54a56e14e5b0f56f69c94ff678d112feec4f547](evidence/findings/PARSE_61b694ad566911debb6bcd55a54a56e14e-a4073d03abef5a410a3faba5d9559207702a54551b03914f419549fb6b7b816c.md) origin=computed
- `info` `STORED_STRICT_DISAGREEMENT` [PARSE:a736c56e033d1d9c0c95a07576cb7fa09c78d29c0d5aa20de035514fd52e5971](evidence/findings/PARSE_a736c56e033d1d9c0c95a07576cb7fa09c-16b12b5b76bacc21d511e544035173a21b0b6ca22d8350086222c26616b41043.md) origin=computed
- `info` `STORED_STRICT_DISAGREEMENT` [PARSE:1acebff481d8db7006596bcb14fff1cbe11c10743e5b7af7685fc5eaaf53abf4](evidence/findings/PARSE_1acebff481d8db7006596bcb14fff1cbe1-bf680153b9b200ae94aebfade4e58d40460376f1e018d62bf1f77509b536904d.md) origin=computed
- `info` `STORED_STRICT_DISAGREEMENT` [PARSE:1c4ebd8b4cf90cb91344b9517747af8bc2e4d2ecd077c8b70c7c8dc6c9c0776b](evidence/findings/PARSE_1c4ebd8b4cf90cb91344b9517747af8bc2-cf2948edbe7066c795cba6f428a0a06e3767dd65546f4e2ef349ed0a895d14e5.md) origin=computed
- `info` `STORED_STRICT_DISAGREEMENT` [PARSE:84ce8b7e238a080a20ce0692eabddaf699575c54815699a3c99a45b2b70ad7bb](evidence/findings/PARSE_84ce8b7e238a080a20ce0692eabddaf699-88164bf702f6e265c7aa2304eeaf8c2a37f0731cf19eb6a293df0235b5d2a475.md) origin=computed
- `info` `STORED_STRICT_DISAGREEMENT` [PARSE:8f390e37950559cd87eba8e214c99225d1fae868fffd90e5cd20afa6dacba468](evidence/findings/PARSE_8f390e37950559cd87eba8e214c99225d1-0a93060d0f0bd6d22958069b61e85e645e93de383aafcebddcdd6d618a7b5977.md) origin=computed
- `info` `STORED_STRICT_DISAGREEMENT` [PARSE:950e8dd8cccfc9d558f276913c3264ff7cb5b024223543ece87e7cb7b367e8ae](evidence/findings/PARSE_950e8dd8cccfc9d558f276913c3264ff7c-f3655307f32b923289ac6c7fc58fccfbe027b4dff32aa0857a2011973bbf455c.md) origin=computed
- `info` `STORED_STRICT_DISAGREEMENT` [PARSE:6aab19e049796c0974ce2e74872547a3647a78343b0d3c0765adb0c75149250e](evidence/findings/PARSE_6aab19e049796c0974ce2e74872547a364-5ba6d8ccd587a58d17220ee1c702d1a507c885789e3310257d5616777a2d60d1.md) origin=computed
- `info` `STORED_STRICT_DISAGREEMENT` [PARSE:18b4d70006bd9e618d7c20728063725e6947bed07299ec86825ee8d4ec93d0ea](evidence/findings/PARSE_18b4d70006bd9e618d7c20728063725e69-ca7802e63f0d6b004fc1282c346ff37446f14230ba4a11e210bca61093e69b1a.md) origin=computed
- `info` `STORED_STRICT_DISAGREEMENT` [PARSE:8d926bc18400009f112b03088c887e38756511c3054cc6b46b42a8a496ce5221](evidence/findings/PARSE_8d926bc18400009f112b03088c887e3875-18409ef2cf1099365518fa648b94a7fb16dd529e818b3c7dc74d5911dbbf6d0b.md) origin=computed
- `info` `STORED_STRICT_DISAGREEMENT` [PARSE:efdd2b19c23cef62bb109b659c07a64431f4122737bc3ca932f4820d97bd4a65](evidence/findings/PARSE_efdd2b19c23cef62bb109b659c07a64431-f68290c71acc37985a9472f61319fad3581bd5a640e685d9fb88ba5ebc872a49.md) origin=computed
- `info` `STORED_STRICT_DISAGREEMENT` [PARSE:a19f4c7f496eb03d0ad54d7a7d9c70b3fd714671a58e3111454c2365356a4565](evidence/findings/PARSE_a19f4c7f496eb03d0ad54d7a7d9c70b3fd-d6748e4ff5359f1ace4a14cc6e8b6ebbf644fd7bc457e6070794f31d25022656.md) origin=computed
- `info` `STORED_STRICT_DISAGREEMENT` [PARSE:fefdbe02326bf2a5b0ab3ca626c8fe1d9e7339cb8540417ae6239112b50e5277](evidence/findings/PARSE_fefdbe02326bf2a5b0ab3ca626c8fe1d9e-9160e6a4849be7b18d7c26b536b5ab5f5183b9bc24d719130f2986ca4d027fcd.md) origin=computed
- `info` `STORED_STRICT_DISAGREEMENT` [PARSE:1e3ffe3144f229520a9da698055fad51fa8286ccb2d344f55b2a0aa2988c0c14](evidence/findings/PARSE_1e3ffe3144f229520a9da698055fad51fa-4a23ef7e99bb4ac8a91ead84dbba9ea043c02bd1914e60a5ab9c3727c078c6d4.md) origin=computed
- `info` `STORED_STRICT_DISAGREEMENT` [PARSE:e25a3b1976df38a0cbbd98deb444e3144b591453e1ce714b3b2f7b8220348ef0](evidence/findings/PARSE_e25a3b1976df38a0cbbd98deb444e3144b-addb9266f5c7ba8752442b27fb08f4a6ab36fa6218139abe905769aadc714358.md) origin=computed
- `info` `STORED_STRICT_DISAGREEMENT` [PARSE:aa47f158b670a61ec95e9bbe03cf724c240d5e79c7f2394b7aee9fbdb6043c15](evidence/findings/PARSE_aa47f158b670a61ec95e9bbe03cf724c24-ddb44f4d6c3d03b9ff1fc51ba2fd142f2a7c158841a14aa804b64c35a8582903.md) origin=computed
- `info` `STORED_STRICT_DISAGREEMENT` [PARSE:722590f0f4c2a7ea306d4c4fa80a82da1481c826362c628cccbb53fba5f35053](evidence/findings/PARSE_722590f0f4c2a7ea306d4c4fa80a82da14-f7011c4a8cc0db72ff7dde97bb63fa0da3d12a761a03581ad0c99da7ef6f758b.md) origin=computed
- `info` `STORED_STRICT_DISAGREEMENT` [PARSE:14892c5c4f97cff677c9a3291a3f1e352219c2a93e0d00b3ef445c20bbe303ba](evidence/findings/PARSE_14892c5c4f97cff677c9a3291a3f1e3522-563f65c80768f7130903d6645b1bc4e2cff54a4d6acc047614b12082299da2d1.md) origin=computed
- `info` `STORED_STRICT_DISAGREEMENT` [PARSE:1e0a328df3e03c47ca27ecb07bd38717fa811f72c26a85b63520ec0c6aed991b](evidence/findings/PARSE_1e0a328df3e03c47ca27ecb07bd38717fa-ea63dc1058fd75cbffb85cf1833dd3866a8b29ca037cbeeb65e54f60e3d43ce0.md) origin=computed
- `info` `STORED_STRICT_DISAGREEMENT` [PARSE:a3e9fde0f37e2fa32a4f5338c0fd05df8905f886b05393b65df8d0a224673d2a](evidence/findings/PARSE_a3e9fde0f37e2fa32a4f5338c0fd05df89-b63581e252de4f623205317d2946fc50a7779c717d95e0f420b4064489a4081b.md) origin=computed
- `info` `STORED_STRICT_DISAGREEMENT` [PARSE:ba232e0f47da4c64b50c263dc4de8e63786128eb409e005572980b2ddd5e4a66](evidence/findings/PARSE_ba232e0f47da4c64b50c263dc4de8e6378-fa0caad856eb426351b031feb926941c975586a03608d645b1b425e6056cfdec.md) origin=computed
- `info` `STORED_STRICT_DISAGREEMENT` [PARSE:564ee302ead1868c6cac4c9caea36e2303466211b1424c896080e8b10facdc19](evidence/findings/PARSE_564ee302ead1868c6cac4c9caea36e2303-43687d1d1e46d369efe02b7e44ac46be58dcda9223b2aa4e76f50571a18a5c94.md) origin=computed
- `info` `STORED_STRICT_DISAGREEMENT` [PARSE:6843dc76749d74880826a0c88662938e9a743ea7474dad058432a1f1cdca2c64](evidence/findings/PARSE_6843dc76749d74880826a0c88662938e9a-8f9bf9a9e9c5c4787fceedb196cb47c55e0e0f678429afc747303dcd73e64ae7.md) origin=computed
- `info` `STORED_STRICT_DISAGREEMENT` [PARSE:7dd4118ff51cf19d481bf10bf627ad3ffe8e77de690ecc15be13a84065368fa9](evidence/findings/PARSE_7dd4118ff51cf19d481bf10bf627ad3ffe-f20cbda4103ad0f42ad2d8ce62a695a9116cf97110634c8f1cdc5ee69e2a0ef0.md) origin=computed
- `info` `STORED_STRICT_DISAGREEMENT` [PARSE:ee766c64bf31e64212bf8c1d862c0462bf3a9e19a1e5f5cecf8243b560854807](evidence/findings/PARSE_ee766c64bf31e64212bf8c1d862c0462bf-81fe292ffca4b6f5d7d01c6a3d2bf044e3715760334dc826b620225c8315b101.md) origin=computed
- `info` `STORED_STRICT_DISAGREEMENT` [PARSE:ddd5497b44db015980ed133d91e6bf053d8ed86da17b8c5681ebbbb34f467de3](evidence/findings/PARSE_ddd5497b44db015980ed133d91e6bf053d-dfc49e8db698b70d1d42ec43e7b85cdd6b2da6f2aa02d7e1e27a4517a0e1f965.md) origin=computed
- `info` `STORED_STRICT_DISAGREEMENT` [PARSE:8b5137f27e4cd4a569f64a9cb1c0f3dbf421b6cd637a898b302eaf733da78e71](evidence/findings/PARSE_8b5137f27e4cd4a569f64a9cb1c0f3dbf4-96d24a94796bac205879257a454ab9a3868c44a00a189f7c531e46b6fabce5f3.md) origin=computed
- `info` `STORED_STRICT_DISAGREEMENT` [PARSE:069e0f481cc9cac83e79f0d5c42ce8411bea209a77300fc6c0401de6e869218a](evidence/findings/PARSE_069e0f481cc9cac83e79f0d5c42ce8411b-4672ed9ff3724b3b2b8f526bc1b0f8f3313b7b2958f0d6ab0a97f7d99847c477.md) origin=computed
- `info` `STORED_STRICT_DISAGREEMENT` [PARSE:549a3090e7410a9c788c36846b0f9777aec681ff865a7f27e9d9e30a8d33d9c6](evidence/findings/PARSE_549a3090e7410a9c788c36846b0f9777ae-411c9bb81f08bac381e2c18ca01392c074ed5b6c11d3eedf589ca5212f7c9986.md) origin=computed
- `info` `STORED_STRICT_DISAGREEMENT` [PARSE:7bbaaccdf136d123395b8cf30aa5bb464d23f4a1637922fb1957c5ad92b6a525](evidence/findings/PARSE_7bbaaccdf136d123395b8cf30aa5bb464d-b6219cdd040126597d3c65137a215b0576ce03f49c9733105305433f4720ad28.md) origin=computed
- `info` `GOLD_DISTRIBUTION` [GOLD:381a5c8ead8fbbee01f907d1952bd7f657ba2321fdc9f1e81f832bfca38d97de](evidence/findings/GOLD_381a5c8ead8fbbee01f907d1952bd7f657b-46c55713895764d663ea0cf03e4118d5dd15bb24279a7cfaa2fccb792f0f7937.md) origin=computed
- `info` `PROVENANCE_TRUNCATION` [PROVENANCE:completeness](evidence/findings/PROVENANCE_completeness-cb79bd08c453b714b60a281c181db9840417250ed220ad6e8fdd9b3243bb0079.md) origin=computed
- `warning` `MISSING_ANNOTATIONS` [ANN:missing](evidence/findings/ANN_missing-1ba0c371a574060179db5eee4aa624aa1579b2d5ea03cb3c9f231d6286a92e1e.md) origin=computed
- `warning` `HISTORICAL_ENTROPY_FLAG` [ENTFLAG:ARC-CHALLENGE-COMP:stored](evidence/findings/ENTFLAG_ARC-CHALLENGE-COMP_stored-2e5e996b0b341b72048dea799111cc9803c36b7ee18b8cd129293c5d64808a10.md) origin=computed
- `warning` `INSUFFICIENT_DATA` [INSUFFICIENT:ARC-CHALLENGE-COMP:strict](evidence/findings/INSUFFICIENT_ARC-CHALLENGE-COMP_strict-222cb59d59aa560f45e95a12d9268f16006f2b91df7d871645c531d718fddb3b.md) origin=computed
- `warning` `CONTROL_CONSTANT_ENTROPY_FLAG` [CTRL:ARC-CHALLENGE-COMP:constant_A](evidence/findings/CTRL_ARC-CHALLENGE-COMP_constant_A-4633c6d43f28ca50b8155538e9f8e8b0e4c479034bc0f1087901f74fdda63075.md) origin=computed
- `warning` `CONTROL_CONSTANT_ENTROPY_FLAG` [CTRL:ARC-CHALLENGE-COMP:constant_B](evidence/findings/CTRL_ARC-CHALLENGE-COMP_constant_B-8a6252644d02949889285c830319d74157dd3c4e55fd281700f674b492dfb414.md) origin=computed
- `warning` `CONTROL_CONSTANT_ENTROPY_FLAG` [CTRL:ARC-CHALLENGE-COMP:constant_C](evidence/findings/CTRL_ARC-CHALLENGE-COMP_constant_C-4d1586ca6b8e62171e1be7349924ac8f94ff88fedf680aa217e8662955623757.md) origin=computed
- `warning` `CONTROL_CONSTANT_ENTROPY_FLAG` [CTRL:ARC-CHALLENGE-COMP:constant_D](evidence/findings/CTRL_ARC-CHALLENGE-COMP_constant_D-2594c2c842c66d69a4a31cb9f33e7f311a50163c087170ea6f54c1d930f74a23.md) origin=computed

