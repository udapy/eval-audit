# Upstream item verification

[Receipts](upstream-20260922/item_matches.json), [request/source inventory](upstream-20260922/requests.json), and [checksums](upstream-20260922/checksums.json) preserve a read-only source check performed for this release. The capture includes full current subject test splits and the local bundles compared against them.

| Saved bundle | Exact item matches | Current upstream rows checked |
| --- | ---: | ---: |
| Assigned security/math example | 0/20 | 100 security + 378 mathematics |
| Saved security/math responses | 0/20 | Same complete splits |
| MMLU statistics | 25/25 | 216 statistics |
| ARC science | 25/25 | 1,172 science |

Comparison checks question text, option labels/order/text, and gold answers. ARC item IDs are checked too. Only a structural `Question: ` or `Q: ` prefix is removed; question content is not rewritten. A nonmatch establishes no exact match in these splits, not who authored the question.

Observed current dataset heads are recorded separately from the unknown collection revisions. Source-server pages were requested at the current head, not a historical pinned revision. These receipts establish what bytes were compared at verification time. They do not authenticate model execution or historical collection timing.

Recheck all saved checksums and item comparisons without network:

```sh
python scripts/verify_sources.py --verify data/provenance/upstream-20260922
```

The script requires explicit `--fetch --out NEW_DIR` for a new anonymous upstream capture and refuses an existing destination. No inference is involved. [Third-party notes](../../THIRD_PARTY.md) link primary license sources.
