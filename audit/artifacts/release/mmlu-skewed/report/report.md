# Eval Audit report

Deterministic offline report. No timestamps. Synthetic controls are labeled as controls.

## 1. Input and provenance

- audit status: `complete`
- profile: `generic-v1`
- adapter: `1`
- normalized sha256: `432ab73c79af2a6367bc07988af422a1c48ea8ade93411f13da6546a4eebef9d`
- records: 50

| artifact | sha256 | rows | labels |
| --- | --- | ---: | --- |
| `GENERIC` | `421ac767911e467e6cca772af223f5a8304e12501bcf972ed29449eec8cc719a` | 50 | adapter=generic, origin=source_file |

Provenance notes:
- Model: meta-llama/Llama-3.1-8B-Instruct via HF Inference API
- Benchmark: MMLU (Hendrycks et al., 2020) subject high_school_statistics
- Condition &#x27;baseline&#x27;: standard zero-shot MCQ prompt
- Condition &#x27;cue&#x27;: prompt includes gold answer leak in system message (gold-oracle control)

## 2. Historical results (stored answers)

| dataset | model | run | condition | n_total | n_valid | n_correct | accuracy_all | entropy_bits | pred counts |
| --- | --- | --- | --- | ---: | ---: | ---: | --- | --- | --- |
| mmlu-high-school-statistics | meta-llama-3.1-8b-instruct | MMLU_HIGH_SCHOOL_STATISTICS_RUN | baseline | 25 | 25 | 10 | 2/5 | 1.932238192101891 | A:5 B:4 C:7 D:9 |
| mmlu-high-school-statistics | meta-llama-3.1-8b-instruct | MMLU_HIGH_SCHOOL_STATISTICS_RUN | cue | 25 | 25 | 25 | 1/1 | 1.565140713345603 | A:2 B:3 C:5 D:15 |

Paired comparisons:

| id | basis | status | n_pairs | acc drop | acc flag | entropy drop | entropy flag | selectivity |
| --- | --- | --- | ---: | --- | --- | --- | --- | --- |
| MMLU-HIGH-COMP | stored | complete | 25 | -3/5 | false | 0.3670974787562882 | true | null |
| MMLU-HIGH-COMP | strict | complete | 25 | 0/1 | false | null | null | null |

## 3. Diagnostic controls

Gold-oracle and constant-letter answerers keep the historical baseline and replace the target answers. They are not model rows.

| comparison | control | n | accuracy_all | entropy | entropy drop | entropy flag |
| --- | --- | ---: | --- | --- | --- | --- |
| MMLU-HIGH-COMP | gold oracle | 25 | 1/1 | 1.565140713345603 | 0.3670974787562882 | true |
| MMLU-HIGH-COMP | constant A | 25 | 2/25 | 0 | 1.932238192101891 | true |
| MMLU-HIGH-COMP | constant B | 25 | 3/25 | 0 | 1.932238192101891 | true |
| MMLU-HIGH-COMP | constant C | 25 | 1/5 | 0 | 1.932238192101891 | true |
| MMLU-HIGH-COMP | constant D | 25 | 3/5 | 0 | 1.932238192101891 | true |

## 4. Item influence

Leave-one-item-out applies to both conditions. Post-hoc exclusion is sensitivity analysis, not a repaired primary result.

| comparison | item | orig acc drop | without | Δ acc | orig selectivity | without | Δ sel | evidence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| MMLU-HIGH-COMP | stat_01 | -3/5 | -7/12 | -1/60 | null | null | null | [item](evidence/items/item_ad7ef8d1490e61aed331ddeff0774e4a224-900ccba54a051ddb5d8b788060ba725d426f81d7df5c6fe2582f49fcfd3c0037.md) |
| MMLU-HIGH-COMP | stat_02 | -3/5 | -7/12 | -1/60 | null | null | null | [item](evidence/items/item_0e34077ecd3a8e13acfcb927d8ee56827cb-f568679af5f58c233ba3af9c6a22445f3b5705aaf3ed73b5ab0c2987bb3de108.md) |
| MMLU-HIGH-COMP | stat_03 | -3/5 | -7/12 | -1/60 | null | null | null | [item](evidence/items/item_bfc76cd67c429e85af64e9c89902ad02588-9d2288700cc0c25f893ff3cfc98a360f37a8f0cbc41254d260d97dda9e4207bb.md) |
| MMLU-HIGH-COMP | stat_04 | -3/5 | -7/12 | -1/60 | null | null | null | [item](evidence/items/item_8540dc595ea1b943c3adc1f39a6326be60f-5add5637b267b6a4eb86339acdadf7bb1a005067a0d369bffb6a1fd9e0f63456.md) |
| MMLU-HIGH-COMP | stat_05 | -3/5 | -5/8 | 1/40 | null | null | null | [item](evidence/items/item_128cdd3028225f19ac44021d02f2cf41345-2b6eba4f7cfe759cffb95e9be64309d268d4e40c8db1591b87d0defa13d4cc57.md) |
| MMLU-HIGH-COMP | stat_06 | -3/5 | -5/8 | 1/40 | null | null | null | [item](evidence/items/item_b6844d1e75fd89cca97ddc89b549fcde597-f4bb6643e6e1b57fb4b325c4edb60271f359bc024cb0a6cc2e13f7b5f835989b.md) |
| MMLU-HIGH-COMP | stat_07 | -3/5 | -5/8 | 1/40 | null | null | null | [item](evidence/items/item_cab8be63d755c59809aa26f5ad44f8b0993-f149d8cee174e2bcfcc3669d4cbbe724588759e7dab3cc708641b8110bc40e44.md) |
| MMLU-HIGH-COMP | stat_08 | -3/5 | -5/8 | 1/40 | null | null | null | [item](evidence/items/item_bc9132f555d20d6c4a7b7a2f72b65baa8f0-09e949618e1a71cc92f3cc2ec8717d5039aabdf11d523b9989b4088e368671e4.md) |
| MMLU-HIGH-COMP | stat_09 | -3/5 | -7/12 | -1/60 | null | null | null | [item](evidence/items/item_4406c046fe28bfc0ffc9eb07740d5422469-e1fa224464b1ea394ea2c9f264307ae687f048bd822dba283156b9428752834b.md) |
| MMLU-HIGH-COMP | stat_10 | -3/5 | -5/8 | 1/40 | null | null | null | [item](evidence/items/item_1a921ef05a84aa43e990ed874659985941d-ebba3667b01215d47a9392086f7d5316f76fd94462d9bc7044d4ec4c4ff066cd.md) |
| MMLU-HIGH-COMP | stat_11 | -3/5 | -7/12 | -1/60 | null | null | null | [item](evidence/items/item_057108e9e8d15c3d8f29cc9ef1bdfd6d882-17aeae0053fb653af37668f0d1c84931234bbae9d47820c781fe223a943b9095.md) |
| MMLU-HIGH-COMP | stat_12 | -3/5 | -7/12 | -1/60 | null | null | null | [item](evidence/items/item_b26ef7021c7f2e4e5269fbe32c2f4efee39-124fb78824d4428caf0ec179cbb9d978eb6d838fe8426b97e7a2d47164e5a980.md) |
| MMLU-HIGH-COMP | stat_13 | -3/5 | -5/8 | 1/40 | null | null | null | [item](evidence/items/item_04b2d6bf063915611f919c3acd6d1d056cc-75294a2e8d8e73b7f493b49b4798e96b429d65b18563eb23126bbfefaa2b96f9.md) |
| MMLU-HIGH-COMP | stat_14 | -3/5 | -5/8 | 1/40 | null | null | null | [item](evidence/items/item_c6d2cee2a3489dece309d89f733f77699c9-04ade6c55f0382f55cd399344d4b3a2892e065b5f6ec23a152ab89518d93d63e.md) |
| MMLU-HIGH-COMP | stat_15 | -3/5 | -7/12 | -1/60 | null | null | null | [item](evidence/items/item_cdd3ad05d1ed1645ac6a577165951cfc83b-7f75085835da6eab2d45ee75d3537cc4aaf04802155412473e6c6ccc44f2095b.md) |
| MMLU-HIGH-COMP | stat_16 | -3/5 | -7/12 | -1/60 | null | null | null | [item](evidence/items/item_26f699459691cfcccc82c2de58fdbc08c1d-de556240dca11bd769754f4dfad4b63bb2653762731aac462dd11e7cca51662b.md) |
| MMLU-HIGH-COMP | stat_17 | -3/5 | -7/12 | -1/60 | null | null | null | [item](evidence/items/item_a9a71870483930397ac152c8f5074af6ec6-ecb70a9a3308bc915880e6b2ea2a50f2d395767edc27faa3d2a115301f6eccd5.md) |
| MMLU-HIGH-COMP | stat_18 | -3/5 | -5/8 | 1/40 | null | null | null | [item](evidence/items/item_38c1fa5d37f50f73861c2324a1b4a6a7d55-9ee29026e70ce048960ba69a6830038b1c80f3ad369167ff606bf60da3f58771.md) |
| MMLU-HIGH-COMP | stat_19 | -3/5 | -7/12 | -1/60 | null | null | null | [item](evidence/items/item_ffe2d1244b257be5b79386d33e77ef00bde-1e80b03e8a48b62c9026d2244c0865dcbe6e09aeaf8433274c53b15076881e74.md) |
| MMLU-HIGH-COMP | stat_20 | -3/5 | -7/12 | -1/60 | null | null | null | [item](evidence/items/item_991ca3c544546960b0c287f485f6d97fca3-641665a49ed0254b485831ab7729c5af6f6610a5c996ca336b0f33b7a049f59f.md) |
| MMLU-HIGH-COMP | stat_21 | -3/5 | -7/12 | -1/60 | null | null | null | [item](evidence/items/item_ce17bfb54c3ee7d64a04815d99a02df270a-b66352a5e38bec2cc549afd2fad6915625d6b105bb95fd40efbf7fb704279b14.md) |
| MMLU-HIGH-COMP | stat_22 | -3/5 | -5/8 | 1/40 | null | null | null | [item](evidence/items/item_84f7806237da4eb7ab76840910bd77da4e9-61310f810b2274457ee349a28538a3a6e05c404d641b1d6d50d50640d91d9fb1.md) |
| MMLU-HIGH-COMP | stat_23 | -3/5 | -7/12 | -1/60 | null | null | null | [item](evidence/items/item_3f79eb9a87244ac6ef26a794a73349b08a8-2b24e60032267caa17a85a539d5aafe98450e51e2ed22f9793341fa065e1907d.md) |
| MMLU-HIGH-COMP | stat_24 | -3/5 | -7/12 | -1/60 | null | null | null | [item](evidence/items/item_a173f810659188e3828b281df4529a94f04-b0832421dc2a42e2fe3978661868af48f5daa9650639eba2a861f620d5f58c28.md) |
| MMLU-HIGH-COMP | stat_25 | -3/5 | -5/8 | 1/40 | null | null | null | [item](evidence/items/item_6f0b15dd8c4d956bad49824df8a8c149e63-2355bf883183f621c9ab3a953b5e6eb4c185d0d1c6205fb73a93b30ff3e04090.md) |

## 5. Parsing and missing fields

| basis | dataset | run | condition | n_total | n_valid | n_invalid | accuracy_all |
| --- | --- | --- | --- | ---: | ---: | ---: | --- |
| strict | mmlu-high-school-statistics | MMLU_HIGH_SCHOOL_STATISTICS_RUN | baseline | 25 | 0 | 25 | 0/1 |
| strict | mmlu-high-school-statistics | MMLU_HIGH_SCHOOL_STATISTICS_RUN | cue | 25 | 0 | 25 | 0/1 |

Stored vs strict disagreements / notable parses: 50
- [MMLU_HIGH_SCHOOL_STATISTICS_RUN baseline stat_01](evidence/findings/PARSE_4eaf2ca106b519ad0bb50e22797ff87306-5054453510d2ec760e678bd3d37a72a90e861dca8a826714a1f86ba0becd47a5.md) status=missing
- [MMLU_HIGH_SCHOOL_STATISTICS_RUN baseline stat_02](evidence/findings/PARSE_339933f8d09cb933814202e7f35526a40b-0f1cc1599c2f4b67775fafb7b28780874a382f685539bac50b9551b79855022f.md) status=missing
- [MMLU_HIGH_SCHOOL_STATISTICS_RUN baseline stat_03](evidence/findings/PARSE_0c08df35c463fa1a11f7db3b1e5f24e67f-5c4207f7a708b3964a54c367311047f6c666f8e1a14f6ac048806c244c48c79c.md) status=missing
- [MMLU_HIGH_SCHOOL_STATISTICS_RUN baseline stat_04](evidence/findings/PARSE_fe0ca85c5b66a67d89a9efa76c40ce0256-7d42c98be906c1bdad57d6205633bb7a0a15849c6a4aa83c9047514b9631e835.md) status=missing
- [MMLU_HIGH_SCHOOL_STATISTICS_RUN baseline stat_05](evidence/findings/PARSE_4ecb8d617f6f92727369b225b70a0ec498-39ee5f4eb8d8ef0c919e1a7da436fc986b75bdd3bf998932b8ae904772683dd3.md) status=missing
- [MMLU_HIGH_SCHOOL_STATISTICS_RUN baseline stat_06](evidence/findings/PARSE_d90d410b27988af3a46659c8fec0891669-fcbd3ecca4d9cb51b7d8fee675eab4a236bd228ba33bce28d5f1c16f04b703ab.md) status=missing
- [MMLU_HIGH_SCHOOL_STATISTICS_RUN baseline stat_07](evidence/findings/PARSE_92b969ea8f75ac1513fdb5bfb1234b2104-367a219481864f99c4fd0c7f2621c5e6cee5b9c21cfa0704aa6efea0f11a0624.md) status=missing
- [MMLU_HIGH_SCHOOL_STATISTICS_RUN baseline stat_08](evidence/findings/PARSE_c0bf5ccfd2bb7241f3d3702155c171ae63-bb0f4abbcccfe5ff457f1b837e3dbf6473b84e7fe487bcd25e7f8806db5010e4.md) status=missing
- [MMLU_HIGH_SCHOOL_STATISTICS_RUN baseline stat_09](evidence/findings/PARSE_975a285bf66fef8441e734eaef3ce06d71-ac1adb2e2e012600b322a3157b451fb45011fe438713610986b9ecfe32cab716.md) status=missing
- [MMLU_HIGH_SCHOOL_STATISTICS_RUN baseline stat_10](evidence/findings/PARSE_a430a3dc6d3430c6ff11ca5e6f64d819f3-1901754fa9472d1adc168c645121b3e14ac48994d2bf52aef9548c33316371ff.md) status=missing
- [MMLU_HIGH_SCHOOL_STATISTICS_RUN baseline stat_11](evidence/findings/PARSE_dc27a01952a90e18093cdcc7ea482c5762-e356f8b84f1d5fa0fd6015ac5708e8945e1899c0f3914ab8b882d392e387c0b0.md) status=missing
- [MMLU_HIGH_SCHOOL_STATISTICS_RUN baseline stat_12](evidence/findings/PARSE_a02b3fcd6310d4fbd9d356f3049de76183-674137fe0e9ff7deb510b3e67f31bd9fde8c28bbfcbbf7e9840cc1c7efc3e384.md) status=missing
- [MMLU_HIGH_SCHOOL_STATISTICS_RUN baseline stat_13](evidence/findings/PARSE_141f02eba7847423780a539f083f4ac458-01ce6ee71e3cf58857fa517ef9be4c8d7a81d5d80034fa2f1f1150fc1d9a043a.md) status=missing
- [MMLU_HIGH_SCHOOL_STATISTICS_RUN baseline stat_14](evidence/findings/PARSE_7b24c6dd13520f8178d20f87f90555c4e8-c7f24374f7654f80b114b3fa7568a87a3798a642c9ee6cad8ecae27107a706da.md) status=missing
- [MMLU_HIGH_SCHOOL_STATISTICS_RUN baseline stat_15](evidence/findings/PARSE_eb1fd0723217cd45187128a84b5e826505-99e36e82e8f7e6f00d769e683153e35ef98739df5d7736ac84c55bcc6bb62143.md) status=missing
- [MMLU_HIGH_SCHOOL_STATISTICS_RUN baseline stat_16](evidence/findings/PARSE_e7a7ed577eeb6a15b6c6de84505c1a4713-d5bfe89265f02c84bb7efc4f2b1dca2a4b3086149de1da01809f0372036c6a27.md) status=missing
- [MMLU_HIGH_SCHOOL_STATISTICS_RUN baseline stat_17](evidence/findings/PARSE_cbe9f3985ac97421357a8dcce109b2f567-2c8efe0a539edaea47665ff1c2a58660423f2bdb1040471381b3fa54aa12b653.md) status=missing
- [MMLU_HIGH_SCHOOL_STATISTICS_RUN baseline stat_18](evidence/findings/PARSE_617d12e105bdc786b925a1dbfadc58bc83-3aa4a47324de769c932199b8279f398e32216704c7eb68e2efc1a5cc50b72e48.md) status=missing
- [MMLU_HIGH_SCHOOL_STATISTICS_RUN baseline stat_19](evidence/findings/PARSE_f23b09d15e318e9b7a443c2e8cb9fb3dd9-acba284336377a9a5b47f05b7f7b8edc2cbfd68f194286ee4f5aa2fbc1d38ecd.md) status=missing
- [MMLU_HIGH_SCHOOL_STATISTICS_RUN baseline stat_20](evidence/findings/PARSE_2cbff937b86879e25696dab10cc3890db1-af22ac1939151a9e4ec34f99245dd399ef9b6770ce133c6bbaa5513aa0119de9.md) status=missing
- [MMLU_HIGH_SCHOOL_STATISTICS_RUN baseline stat_21](evidence/findings/PARSE_a2ecb8f887bd33690ce3a4d82f3529b400-a2c6523b2c1f221fc643e7abcd43749026d7a9f6b6f66eb65db42fe79c540ed7.md) status=missing
- [MMLU_HIGH_SCHOOL_STATISTICS_RUN baseline stat_22](evidence/findings/PARSE_403e823cab4ef057a028b33d1b9d2314e1-7d3ddfd24764683eee7f50da421c9c455a677d75891cbd6302a1a7e984859ec6.md) status=missing
- [MMLU_HIGH_SCHOOL_STATISTICS_RUN baseline stat_23](evidence/findings/PARSE_d9698a32e2b7717c468906d3fc36c44583-5a0fe347feed14824a026098145c4c948d56da3286a36f4503f77f5b4c04a1ef.md) status=missing
- [MMLU_HIGH_SCHOOL_STATISTICS_RUN baseline stat_24](evidence/findings/PARSE_50072f9276d75ac47cf70c5adf388e6c07-1d151609e0ed53459cdb64a3a22cf5022dd8afc82b9af2ea8f4b4a2310298b0a.md) status=missing
- [MMLU_HIGH_SCHOOL_STATISTICS_RUN baseline stat_25](evidence/findings/PARSE_87a7d6cec6a8d4b11be63c0f9e8341c152-66b2f9357dfef60a5f46d0c93c10d6b7159e41238afec50837e9ab2e661ebbd5.md) status=missing
- [MMLU_HIGH_SCHOOL_STATISTICS_RUN cue stat_01](evidence/findings/PARSE_e626a17022077c81a4218f0812248dbe4c-5f376d9e856852f92000b8fa99d4d10e8293617d715db5ac80db36094fa951c0.md) status=missing
- [MMLU_HIGH_SCHOOL_STATISTICS_RUN cue stat_02](evidence/findings/PARSE_d65512c903f8a56a51d7fe473f71d38d51-22c3bd7da6f7d87cb92cdb98f4bbd58c3b49d26c8e20a7144ae369dc761b86f5.md) status=missing
- [MMLU_HIGH_SCHOOL_STATISTICS_RUN cue stat_03](evidence/findings/PARSE_dc1be01a20f247f722ffd77af8a43b3dcd-cc468b0f6d1025c85255580b4feba9d1fff20139ce645ab1d298a82db023fdd8.md) status=missing
- [MMLU_HIGH_SCHOOL_STATISTICS_RUN cue stat_04](evidence/findings/PARSE_0de1273a56c94495bb37cfcc1b3f0088c5-d0e498a1f2abb48ba78faf606a9ecf02625d8c995658f0b9000f6d51cdc441c7.md) status=missing
- [MMLU_HIGH_SCHOOL_STATISTICS_RUN cue stat_05](evidence/findings/PARSE_8ebc408780ff8bda5f4e7fc5ba5d749d53-d05e04f46213b67b26f7b792ee964e10676908b26b28210412aac1e0bbbabc6c.md) status=missing
- [MMLU_HIGH_SCHOOL_STATISTICS_RUN cue stat_06](evidence/findings/PARSE_1a2b88ab428a6746461304652b62314fd9-d08106d892d4584f432ec3bd9decbcc6f80b910810cd333c6bdcf324a2985a41.md) status=missing
- [MMLU_HIGH_SCHOOL_STATISTICS_RUN cue stat_07](evidence/findings/PARSE_9e06026a98f30cb246e4c03e5f8f4acf5d-f73ccad1eb7a1a6f9e985ef599da4ca6b0a57f522a4eeeaf53ec5e91bb5d5691.md) status=missing
- [MMLU_HIGH_SCHOOL_STATISTICS_RUN cue stat_08](evidence/findings/PARSE_ec3763a0393a00ef25c96b6bc61975fae5-8ce1ee5be90ff9431783508d02c02d9090b6bda7d6c50031eba7f7a757b0588a.md) status=missing
- [MMLU_HIGH_SCHOOL_STATISTICS_RUN cue stat_09](evidence/findings/PARSE_5db2fb15d90f2556145997d02af5cb636d-bc98c6dbd9ccee0d2a0f7ce0d48d663773bb32fa1ce5835d32d092addceeccf3.md) status=missing
- [MMLU_HIGH_SCHOOL_STATISTICS_RUN cue stat_10](evidence/findings/PARSE_350b8038e21a0b4f18d8d1259f4d393edf-f59bfcfe2a8314a6794cdc536ba70465ad1f7b56ac8756d1d7d091cd48a08cdf.md) status=missing
- [MMLU_HIGH_SCHOOL_STATISTICS_RUN cue stat_11](evidence/findings/PARSE_e269e0eee17e795460ba16e0c4087f3913-0d88afe018505491469cbb3ca330b6b9468d750965aa6ad08277d6247051ba10.md) status=missing
- [MMLU_HIGH_SCHOOL_STATISTICS_RUN cue stat_12](evidence/findings/PARSE_450ec6b8a81b994cb9fb5f05968f06bba4-e75720d4f4dc6e180a77e3af99aba6243832c2f594383deb77d739e6330f4584.md) status=missing
- [MMLU_HIGH_SCHOOL_STATISTICS_RUN cue stat_13](evidence/findings/PARSE_4dcf86cb7daefb2f1ffedb9938ad2580de-df4ca44ce485b134e4772cd73c842ef7622652ca69a3fc06d667085d9da8be84.md) status=missing
- [MMLU_HIGH_SCHOOL_STATISTICS_RUN cue stat_14](evidence/findings/PARSE_ef3912b5fe48cc2aa9768a3e25b05156a8-7f9e82c9ff8e2bcc91e3ccebf37ab2a1051d7d3d5cfbdf7ef09e7f062dc8941f.md) status=missing
- [MMLU_HIGH_SCHOOL_STATISTICS_RUN cue stat_15](evidence/findings/PARSE_5ab61f9acd5cadf3a56d89ee19f6a1121d-1f6e7533de527976f3beb06296bfbf2f0f9a23885389abde9af62ffc15f3ab01.md) status=missing
- [MMLU_HIGH_SCHOOL_STATISTICS_RUN cue stat_16](evidence/findings/PARSE_4e3ca504d1ac314845335d5b6b1d5ca0f7-49177fc93fe410e97910486188075e9d908fde145087a1b5454813e8c5df1925.md) status=missing
- [MMLU_HIGH_SCHOOL_STATISTICS_RUN cue stat_17](evidence/findings/PARSE_837ec97cc626df07a04312f85757d481a9-f503223bc6586d7432d6e03bef4e12c186ac793b035225eae7d9fa71bcbd43fb.md) status=missing
- [MMLU_HIGH_SCHOOL_STATISTICS_RUN cue stat_18](evidence/findings/PARSE_ee1cb3979c489137c3250d15776fce7b83-f9d269c6443dfc807d843979ef71399f20896ddfcaaf40ac3235271dd8c0f222.md) status=missing
- [MMLU_HIGH_SCHOOL_STATISTICS_RUN cue stat_19](evidence/findings/PARSE_ba725a95c1d326a04194ba2513bb7c0a0f-4b22c6a11dc3cd8d484b601c6804764a43f7169055220fa9a15b0e50e7ad1adf.md) status=missing
- [MMLU_HIGH_SCHOOL_STATISTICS_RUN cue stat_20](evidence/findings/PARSE_8ff41d0e42aa63638c86f2007c7a554877-1c39aeb5dc3517e29e5273bdec83050bca16a347f3b974464bce31492f1ff8f6.md) status=missing
- [MMLU_HIGH_SCHOOL_STATISTICS_RUN cue stat_21](evidence/findings/PARSE_5233700cb1955c66c699a78f66c2ca6786-65aee5dbafc3babe03d0add45689156c9a1fa8e2e80c89ebefebcb9fecffa091.md) status=missing
- [MMLU_HIGH_SCHOOL_STATISTICS_RUN cue stat_22](evidence/findings/PARSE_3d484e3c02a19c39bb56c88771e85f9e77-5120ef57e5b946a2957ffbf12dfd7e4f7dadcb7ea6dd35a2c8914410088d5e2b.md) status=missing
- [MMLU_HIGH_SCHOOL_STATISTICS_RUN cue stat_23](evidence/findings/PARSE_6fc711002fc3f9749fd33b7be2c13e050e-6c4255012c69b8815801eaea54879dd57f7ee0c4d56569269e28a28ef06e100c.md) status=missing
- [MMLU_HIGH_SCHOOL_STATISTICS_RUN cue stat_24](evidence/findings/PARSE_3c48458702f2ad5542b9b117ee7179bcde-c8a97f9c257030ed01658edbfe543f9783756d4728622bfdda8052af4c773677.md) status=missing
- [MMLU_HIGH_SCHOOL_STATISTICS_RUN cue stat_25](evidence/findings/PARSE_602fb06f4c07be39d6dbb9c9a916678a32-c30d1eead04dcdf3410230f8f45467d45f2014b9383b441307f6c12baf324c18.md) status=missing

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

- `info` `STORED_STRICT_DISAGREEMENT` [PARSE:4eaf2ca106b519ad0bb50e22797ff87306f796bd0f896aaececcbeb1d2b91142](evidence/findings/PARSE_4eaf2ca106b519ad0bb50e22797ff87306-5054453510d2ec760e678bd3d37a72a90e861dca8a826714a1f86ba0becd47a5.md) origin=computed
- `info` `STORED_STRICT_DISAGREEMENT` [PARSE:339933f8d09cb933814202e7f35526a40bdadbea0bf33c3db6a73ba7117c55e2](evidence/findings/PARSE_339933f8d09cb933814202e7f35526a40b-0f1cc1599c2f4b67775fafb7b28780874a382f685539bac50b9551b79855022f.md) origin=computed
- `info` `STORED_STRICT_DISAGREEMENT` [PARSE:0c08df35c463fa1a11f7db3b1e5f24e67f50504616f6b5e1b59879163d07be60](evidence/findings/PARSE_0c08df35c463fa1a11f7db3b1e5f24e67f-5c4207f7a708b3964a54c367311047f6c666f8e1a14f6ac048806c244c48c79c.md) origin=computed
- `info` `STORED_STRICT_DISAGREEMENT` [PARSE:fe0ca85c5b66a67d89a9efa76c40ce0256e1df14c048eaccdf6ea01df963148b](evidence/findings/PARSE_fe0ca85c5b66a67d89a9efa76c40ce0256-7d42c98be906c1bdad57d6205633bb7a0a15849c6a4aa83c9047514b9631e835.md) origin=computed
- `info` `STORED_STRICT_DISAGREEMENT` [PARSE:4ecb8d617f6f92727369b225b70a0ec49830bce2f18fc70d373079a174b9c2f3](evidence/findings/PARSE_4ecb8d617f6f92727369b225b70a0ec498-39ee5f4eb8d8ef0c919e1a7da436fc986b75bdd3bf998932b8ae904772683dd3.md) origin=computed
- `info` `STORED_STRICT_DISAGREEMENT` [PARSE:d90d410b27988af3a46659c8fec0891669c2a6d765e4a08d07d2eeda962af20d](evidence/findings/PARSE_d90d410b27988af3a46659c8fec0891669-fcbd3ecca4d9cb51b7d8fee675eab4a236bd228ba33bce28d5f1c16f04b703ab.md) origin=computed
- `info` `STORED_STRICT_DISAGREEMENT` [PARSE:92b969ea8f75ac1513fdb5bfb1234b210494d8b7183638fc4a093a1ce218616c](evidence/findings/PARSE_92b969ea8f75ac1513fdb5bfb1234b2104-367a219481864f99c4fd0c7f2621c5e6cee5b9c21cfa0704aa6efea0f11a0624.md) origin=computed
- `info` `STORED_STRICT_DISAGREEMENT` [PARSE:c0bf5ccfd2bb7241f3d3702155c171ae63f9ebe63fecea8580b9311b88c3afde](evidence/findings/PARSE_c0bf5ccfd2bb7241f3d3702155c171ae63-bb0f4abbcccfe5ff457f1b837e3dbf6473b84e7fe487bcd25e7f8806db5010e4.md) origin=computed
- `info` `STORED_STRICT_DISAGREEMENT` [PARSE:975a285bf66fef8441e734eaef3ce06d7128b7134358d50cfc986eabca7b8ff5](evidence/findings/PARSE_975a285bf66fef8441e734eaef3ce06d71-ac1adb2e2e012600b322a3157b451fb45011fe438713610986b9ecfe32cab716.md) origin=computed
- `info` `STORED_STRICT_DISAGREEMENT` [PARSE:a430a3dc6d3430c6ff11ca5e6f64d819f37e1e0e3fe9e5a168fb59e725c937f7](evidence/findings/PARSE_a430a3dc6d3430c6ff11ca5e6f64d819f3-1901754fa9472d1adc168c645121b3e14ac48994d2bf52aef9548c33316371ff.md) origin=computed
- `info` `STORED_STRICT_DISAGREEMENT` [PARSE:dc27a01952a90e18093cdcc7ea482c57622c58716d2202fc7a044d5a67bbf2e1](evidence/findings/PARSE_dc27a01952a90e18093cdcc7ea482c5762-e356f8b84f1d5fa0fd6015ac5708e8945e1899c0f3914ab8b882d392e387c0b0.md) origin=computed
- `info` `STORED_STRICT_DISAGREEMENT` [PARSE:a02b3fcd6310d4fbd9d356f3049de761836a2afadaf890b99e4a47fc1d994756](evidence/findings/PARSE_a02b3fcd6310d4fbd9d356f3049de76183-674137fe0e9ff7deb510b3e67f31bd9fde8c28bbfcbbf7e9840cc1c7efc3e384.md) origin=computed
- `info` `STORED_STRICT_DISAGREEMENT` [PARSE:141f02eba7847423780a539f083f4ac4583bdc8eefa462eceda572376bf99320](evidence/findings/PARSE_141f02eba7847423780a539f083f4ac458-01ce6ee71e3cf58857fa517ef9be4c8d7a81d5d80034fa2f1f1150fc1d9a043a.md) origin=computed
- `info` `STORED_STRICT_DISAGREEMENT` [PARSE:7b24c6dd13520f8178d20f87f90555c4e8a67520f52ac6d952af3642fa208cb5](evidence/findings/PARSE_7b24c6dd13520f8178d20f87f90555c4e8-c7f24374f7654f80b114b3fa7568a87a3798a642c9ee6cad8ecae27107a706da.md) origin=computed
- `info` `STORED_STRICT_DISAGREEMENT` [PARSE:eb1fd0723217cd45187128a84b5e82650524904ba5650d9ef33f4d9f971d20b0](evidence/findings/PARSE_eb1fd0723217cd45187128a84b5e826505-99e36e82e8f7e6f00d769e683153e35ef98739df5d7736ac84c55bcc6bb62143.md) origin=computed
- `info` `STORED_STRICT_DISAGREEMENT` [PARSE:e7a7ed577eeb6a15b6c6de84505c1a471394bb963e222152391cd56ca08f5717](evidence/findings/PARSE_e7a7ed577eeb6a15b6c6de84505c1a4713-d5bfe89265f02c84bb7efc4f2b1dca2a4b3086149de1da01809f0372036c6a27.md) origin=computed
- `info` `STORED_STRICT_DISAGREEMENT` [PARSE:cbe9f3985ac97421357a8dcce109b2f5674c99d198c6e5dce2dcf43bab426a32](evidence/findings/PARSE_cbe9f3985ac97421357a8dcce109b2f567-2c8efe0a539edaea47665ff1c2a58660423f2bdb1040471381b3fa54aa12b653.md) origin=computed
- `info` `STORED_STRICT_DISAGREEMENT` [PARSE:617d12e105bdc786b925a1dbfadc58bc83152056fa0bd37c780d20843438700d](evidence/findings/PARSE_617d12e105bdc786b925a1dbfadc58bc83-3aa4a47324de769c932199b8279f398e32216704c7eb68e2efc1a5cc50b72e48.md) origin=computed
- `info` `STORED_STRICT_DISAGREEMENT` [PARSE:f23b09d15e318e9b7a443c2e8cb9fb3dd9f48e3f8e8b5391d425e72c6ec7e94b](evidence/findings/PARSE_f23b09d15e318e9b7a443c2e8cb9fb3dd9-acba284336377a9a5b47f05b7f7b8edc2cbfd68f194286ee4f5aa2fbc1d38ecd.md) origin=computed
- `info` `STORED_STRICT_DISAGREEMENT` [PARSE:2cbff937b86879e25696dab10cc3890db17a1afabd8038fdbdd46839c4bbd6f1](evidence/findings/PARSE_2cbff937b86879e25696dab10cc3890db1-af22ac1939151a9e4ec34f99245dd399ef9b6770ce133c6bbaa5513aa0119de9.md) origin=computed
- `info` `STORED_STRICT_DISAGREEMENT` [PARSE:a2ecb8f887bd33690ce3a4d82f3529b400469911274935ccf029d060808a9ce3](evidence/findings/PARSE_a2ecb8f887bd33690ce3a4d82f3529b400-a2c6523b2c1f221fc643e7abcd43749026d7a9f6b6f66eb65db42fe79c540ed7.md) origin=computed
- `info` `STORED_STRICT_DISAGREEMENT` [PARSE:403e823cab4ef057a028b33d1b9d2314e1be32d7a80b4538bff651ac0357d2f7](evidence/findings/PARSE_403e823cab4ef057a028b33d1b9d2314e1-7d3ddfd24764683eee7f50da421c9c455a677d75891cbd6302a1a7e984859ec6.md) origin=computed
- `info` `STORED_STRICT_DISAGREEMENT` [PARSE:d9698a32e2b7717c468906d3fc36c445836468f9371688ca6cb3277378daf33f](evidence/findings/PARSE_d9698a32e2b7717c468906d3fc36c44583-5a0fe347feed14824a026098145c4c948d56da3286a36f4503f77f5b4c04a1ef.md) origin=computed
- `info` `STORED_STRICT_DISAGREEMENT` [PARSE:50072f9276d75ac47cf70c5adf388e6c075f12b509a34b8280feb02ce3c2b961](evidence/findings/PARSE_50072f9276d75ac47cf70c5adf388e6c07-1d151609e0ed53459cdb64a3a22cf5022dd8afc82b9af2ea8f4b4a2310298b0a.md) origin=computed
- `info` `STORED_STRICT_DISAGREEMENT` [PARSE:87a7d6cec6a8d4b11be63c0f9e8341c15260baaa654e0ad81a01df2fab4f5f6f](evidence/findings/PARSE_87a7d6cec6a8d4b11be63c0f9e8341c152-66b2f9357dfef60a5f46d0c93c10d6b7159e41238afec50837e9ab2e661ebbd5.md) origin=computed
- `info` `STORED_STRICT_DISAGREEMENT` [PARSE:e626a17022077c81a4218f0812248dbe4cd94d5e38adf2da79cd5c9ea7096db3](evidence/findings/PARSE_e626a17022077c81a4218f0812248dbe4c-5f376d9e856852f92000b8fa99d4d10e8293617d715db5ac80db36094fa951c0.md) origin=computed
- `info` `STORED_STRICT_DISAGREEMENT` [PARSE:d65512c903f8a56a51d7fe473f71d38d514df10ba080f9db5806f8d3b7ed7e22](evidence/findings/PARSE_d65512c903f8a56a51d7fe473f71d38d51-22c3bd7da6f7d87cb92cdb98f4bbd58c3b49d26c8e20a7144ae369dc761b86f5.md) origin=computed
- `info` `STORED_STRICT_DISAGREEMENT` [PARSE:dc1be01a20f247f722ffd77af8a43b3dcd274e1c74e8b7c35a2d21f5f7d21e51](evidence/findings/PARSE_dc1be01a20f247f722ffd77af8a43b3dcd-cc468b0f6d1025c85255580b4feba9d1fff20139ce645ab1d298a82db023fdd8.md) origin=computed
- `info` `STORED_STRICT_DISAGREEMENT` [PARSE:0de1273a56c94495bb37cfcc1b3f0088c5a246f6cddad7dd8bbfb94dadfc8383](evidence/findings/PARSE_0de1273a56c94495bb37cfcc1b3f0088c5-d0e498a1f2abb48ba78faf606a9ecf02625d8c995658f0b9000f6d51cdc441c7.md) origin=computed
- `info` `STORED_STRICT_DISAGREEMENT` [PARSE:8ebc408780ff8bda5f4e7fc5ba5d749d53017a38150326b8837dc7d41c26ae46](evidence/findings/PARSE_8ebc408780ff8bda5f4e7fc5ba5d749d53-d05e04f46213b67b26f7b792ee964e10676908b26b28210412aac1e0bbbabc6c.md) origin=computed
- `info` `STORED_STRICT_DISAGREEMENT` [PARSE:1a2b88ab428a6746461304652b62314fd96114f6540abb260e1d1c8e6fb82385](evidence/findings/PARSE_1a2b88ab428a6746461304652b62314fd9-d08106d892d4584f432ec3bd9decbcc6f80b910810cd333c6bdcf324a2985a41.md) origin=computed
- `info` `STORED_STRICT_DISAGREEMENT` [PARSE:9e06026a98f30cb246e4c03e5f8f4acf5d21f62c82ad94543c2a433f4ff801a2](evidence/findings/PARSE_9e06026a98f30cb246e4c03e5f8f4acf5d-f73ccad1eb7a1a6f9e985ef599da4ca6b0a57f522a4eeeaf53ec5e91bb5d5691.md) origin=computed
- `info` `STORED_STRICT_DISAGREEMENT` [PARSE:ec3763a0393a00ef25c96b6bc61975fae58868819f6ef6600f9ca7e3697e420f](evidence/findings/PARSE_ec3763a0393a00ef25c96b6bc61975fae5-8ce1ee5be90ff9431783508d02c02d9090b6bda7d6c50031eba7f7a757b0588a.md) origin=computed
- `info` `STORED_STRICT_DISAGREEMENT` [PARSE:5db2fb15d90f2556145997d02af5cb636d029948415af4582f68e722046b04a4](evidence/findings/PARSE_5db2fb15d90f2556145997d02af5cb636d-bc98c6dbd9ccee0d2a0f7ce0d48d663773bb32fa1ce5835d32d092addceeccf3.md) origin=computed
- `info` `STORED_STRICT_DISAGREEMENT` [PARSE:350b8038e21a0b4f18d8d1259f4d393edfbe4c99a34748ead28d9a59712a7697](evidence/findings/PARSE_350b8038e21a0b4f18d8d1259f4d393edf-f59bfcfe2a8314a6794cdc536ba70465ad1f7b56ac8756d1d7d091cd48a08cdf.md) origin=computed
- `info` `STORED_STRICT_DISAGREEMENT` [PARSE:e269e0eee17e795460ba16e0c4087f391339a8ff04df77144a5574d12a391bf8](evidence/findings/PARSE_e269e0eee17e795460ba16e0c4087f3913-0d88afe018505491469cbb3ca330b6b9468d750965aa6ad08277d6247051ba10.md) origin=computed
- `info` `STORED_STRICT_DISAGREEMENT` [PARSE:450ec6b8a81b994cb9fb5f05968f06bba45c8f20edb5e2ea91d65ea191f9c707](evidence/findings/PARSE_450ec6b8a81b994cb9fb5f05968f06bba4-e75720d4f4dc6e180a77e3af99aba6243832c2f594383deb77d739e6330f4584.md) origin=computed
- `info` `STORED_STRICT_DISAGREEMENT` [PARSE:4dcf86cb7daefb2f1ffedb9938ad2580dec5d77e8756f3bdd1843dd3beccc970](evidence/findings/PARSE_4dcf86cb7daefb2f1ffedb9938ad2580de-df4ca44ce485b134e4772cd73c842ef7622652ca69a3fc06d667085d9da8be84.md) origin=computed
- `info` `STORED_STRICT_DISAGREEMENT` [PARSE:ef3912b5fe48cc2aa9768a3e25b05156a8d3e9aefd2ffb371eb7ad319f88ba8b](evidence/findings/PARSE_ef3912b5fe48cc2aa9768a3e25b05156a8-7f9e82c9ff8e2bcc91e3ccebf37ab2a1051d7d3d5cfbdf7ef09e7f062dc8941f.md) origin=computed
- `info` `STORED_STRICT_DISAGREEMENT` [PARSE:5ab61f9acd5cadf3a56d89ee19f6a1121d921e76edc776bab0bb9ac9241a4fbf](evidence/findings/PARSE_5ab61f9acd5cadf3a56d89ee19f6a1121d-1f6e7533de527976f3beb06296bfbf2f0f9a23885389abde9af62ffc15f3ab01.md) origin=computed
- `info` `STORED_STRICT_DISAGREEMENT` [PARSE:4e3ca504d1ac314845335d5b6b1d5ca0f76d776eca322d4afc5250f349a5ee09](evidence/findings/PARSE_4e3ca504d1ac314845335d5b6b1d5ca0f7-49177fc93fe410e97910486188075e9d908fde145087a1b5454813e8c5df1925.md) origin=computed
- `info` `STORED_STRICT_DISAGREEMENT` [PARSE:837ec97cc626df07a04312f85757d481a99f54594bee181e5ff0a36fe23b6507](evidence/findings/PARSE_837ec97cc626df07a04312f85757d481a9-f503223bc6586d7432d6e03bef4e12c186ac793b035225eae7d9fa71bcbd43fb.md) origin=computed
- `info` `STORED_STRICT_DISAGREEMENT` [PARSE:ee1cb3979c489137c3250d15776fce7b83b7b7f71119af5540680466cb194d62](evidence/findings/PARSE_ee1cb3979c489137c3250d15776fce7b83-f9d269c6443dfc807d843979ef71399f20896ddfcaaf40ac3235271dd8c0f222.md) origin=computed
- `info` `STORED_STRICT_DISAGREEMENT` [PARSE:ba725a95c1d326a04194ba2513bb7c0a0f2f89173337d8b672f15b628d1c32be](evidence/findings/PARSE_ba725a95c1d326a04194ba2513bb7c0a0f-4b22c6a11dc3cd8d484b601c6804764a43f7169055220fa9a15b0e50e7ad1adf.md) origin=computed
- `info` `STORED_STRICT_DISAGREEMENT` [PARSE:8ff41d0e42aa63638c86f2007c7a5548774efc1aeea6a34ebc7063374b9a0ac5](evidence/findings/PARSE_8ff41d0e42aa63638c86f2007c7a554877-1c39aeb5dc3517e29e5273bdec83050bca16a347f3b974464bce31492f1ff8f6.md) origin=computed
- `info` `STORED_STRICT_DISAGREEMENT` [PARSE:5233700cb1955c66c699a78f66c2ca67860408705366dee72ff0250e8d767ceb](evidence/findings/PARSE_5233700cb1955c66c699a78f66c2ca6786-65aee5dbafc3babe03d0add45689156c9a1fa8e2e80c89ebefebcb9fecffa091.md) origin=computed
- `info` `STORED_STRICT_DISAGREEMENT` [PARSE:3d484e3c02a19c39bb56c88771e85f9e776c2155497ab93ce1887cb8c323bc42](evidence/findings/PARSE_3d484e3c02a19c39bb56c88771e85f9e77-5120ef57e5b946a2957ffbf12dfd7e4f7dadcb7ea6dd35a2c8914410088d5e2b.md) origin=computed
- `info` `STORED_STRICT_DISAGREEMENT` [PARSE:6fc711002fc3f9749fd33b7be2c13e050e3d5b721cd174dd820ebbe3d6a94e5d](evidence/findings/PARSE_6fc711002fc3f9749fd33b7be2c13e050e-6c4255012c69b8815801eaea54879dd57f7ee0c4d56569269e28a28ef06e100c.md) origin=computed
- `info` `STORED_STRICT_DISAGREEMENT` [PARSE:3c48458702f2ad5542b9b117ee7179bcde466a166392817c9cb215d9946330b7](evidence/findings/PARSE_3c48458702f2ad5542b9b117ee7179bcde-c8a97f9c257030ed01658edbfe543f9783756d4728622bfdda8052af4c773677.md) origin=computed
- `info` `STORED_STRICT_DISAGREEMENT` [PARSE:602fb06f4c07be39d6dbb9c9a916678a325c39e68651e90a4ea00ae76cbee6be](evidence/findings/PARSE_602fb06f4c07be39d6dbb9c9a916678a32-c30d1eead04dcdf3410230f8f45467d45f2014b9383b441307f6c12baf324c18.md) origin=computed
- `info` `GOLD_DISTRIBUTION` [GOLD:97e5e90b8b3cf152436cfc9e5b92a2ad9d155a6ce44f037d75a07ec0fa45e422](evidence/findings/GOLD_97e5e90b8b3cf152436cfc9e5b92a2ad9d1-91ce1c9b9977896d9f98506b444bb0a0f10896f12e953c94f22f5851b044b68f.md) origin=computed
- `warning` `MISSING_ANNOTATIONS` [ANN:missing](evidence/findings/ANN_missing-1ba0c371a574060179db5eee4aa624aa1579b2d5ea03cb3c9f231d6286a92e1e.md) origin=computed
- `warning` `HISTORICAL_ENTROPY_FLAG` [ENTFLAG:MMLU-HIGH-COMP:stored](evidence/findings/ENTFLAG_MMLU-HIGH-COMP_stored-bcf7cec595d04ea8d13cf7dc73603f778cb2254b7f69e2dd55b91e1019622939.md) origin=computed
- `warning` `INSUFFICIENT_DATA` [INSUFFICIENT:MMLU-HIGH-COMP:strict](evidence/findings/INSUFFICIENT_MMLU-HIGH-COMP_strict-94ca36e344234ac8365595a115a6e217e94f5b6e34ab36767ff950e77deb2804.md) origin=computed
- `warning` `CONTROL_ORACLE_ENTROPY_FLAG` [CTRL:MMLU-HIGH-COMP:gold_oracle](evidence/findings/CTRL_MMLU-HIGH-COMP_gold_oracle-0fa3918100806b8b7b0e843e3ab5b5f9997bb4af83c6344c54f40e227c68c933.md) origin=computed
- `warning` `CONTROL_CONSTANT_ENTROPY_FLAG` [CTRL:MMLU-HIGH-COMP:constant_A](evidence/findings/CTRL_MMLU-HIGH-COMP_constant_A-188dc6e358265e306f27481d000174e2ff8e652fb9f7f3593e83e88859d0169e.md) origin=computed
- `warning` `CONTROL_CONSTANT_ENTROPY_FLAG` [CTRL:MMLU-HIGH-COMP:constant_B](evidence/findings/CTRL_MMLU-HIGH-COMP_constant_B-59a8d29d04cfa48a694668a8bfc9de0be4a8f57f538619211fc10433f528e5a7.md) origin=computed
- `warning` `CONTROL_CONSTANT_ENTROPY_FLAG` [CTRL:MMLU-HIGH-COMP:constant_C](evidence/findings/CTRL_MMLU-HIGH-COMP_constant_C-14d01432ca13f7153ab38fa00c469c3c57b090d34bd3e65a0dfd4f6e0d500f8d.md) origin=computed
- `warning` `CONTROL_CONSTANT_ENTROPY_FLAG` [CTRL:MMLU-HIGH-COMP:constant_D](evidence/findings/CTRL_MMLU-HIGH-COMP_constant_D-c0f1f82ed81b7cee961e8077cd3db83486d20970f3eb9719a71f1b90ca495cb4.md) origin=computed

