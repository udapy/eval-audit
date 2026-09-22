# Assigned security/math responses

This 20-item, 40-row example is synthetic: `authoring.py` assigns answer letters and constructs response prose. The saved model label does not establish that a model ran. The questions' claimed MMLU origin is unverified; the local source metadata is retained as an original claim.

Use it to exercise parsing, oracle controls, and item influence. It is not independent real-model benchmark validation. See the [catalog](../../data/README.md) and [source checks](../../data/provenance/README.md).

The authoring script refuses to overwrite its saved bundle. For offline reproduction, use `make evidence` or `python scripts/independent_generic_replay.py --source examples/external-eval/bundle.json`.
