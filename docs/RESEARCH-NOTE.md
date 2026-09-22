# Reading the saved evaluation evidence

This project audits whether recorded multiple-choice measurements support the way they are described. It preserves stored labels, parses response text separately, and shows simple controls before a researcher interprets differences as model behavior.

![Gold-key counts](figures/gold-distributions.png)

## Data and model attribution

The [catalog](../data/README.md) covers a 16-item synthetic transfer fixture, a 20-item example with assigned security/math responses, a 20-item saved security/math response set, 25 statistics items, and 25 science items. Each item has baseline and target rows. The two security/math examples share questions; these are not independent item banks.

The assigned-response example carries a historical Llama model label, but its authoring script constructs the responses. It is a synthetic demonstration. The other three bundles contain saved response text attributed locally to Llama-3.1-8B-Instruct or Qwen3-8B. Full provider envelopes, request IDs, returned model snapshots, and finish reasons were not retained. We can replay these files; we cannot authenticate execution from their model labels.

The locally embedded security/math questions were described as MMLU in the old metadata. Their benchmark origin is unverified. A release-time comparison found no exact matches in the claimed current subject test splits. Statistics and ARC items matched the current upstream rows checked. This verifies current item content, not the revision used during collection. See [provenance receipts](../data/provenance/README.md).

## Verified observations

![Entropy comparison](figures/entropy-comparison.png)

Values below use stored answers and come from the independently checked [comparison table](../data/comparisons.csv). Accuracy includes missing responses in its denominator; entropy uses valid letters only.

| Saved slice | Baseline correct | Target correct | Baseline minus oracle entropy (bits) | Oracle flag at >0.15 |
| --- | ---: | ---: | ---: | --- |
| Local security questions | 10/10 | 10/10 | 0.000000 | false |
| Local math questions | 7/10 | 10/10 | -0.285475 | false |
| MMLU statistics slice | 10/25 | 25/25 | 0.367097 | true |
| ARC science slice | 17/25 | 22/25 | 0.036721 | false |

The ARC saved target entropy drop is approximately **0.159479** bits, while its computed oracle drop is approximately **0.036721** bits. These are different quantities. The earlier narrative conflated the target flag with the oracle diagnostic. ARC has six missing baseline answers and two missing target answers, which also changes the entropy denominators.

The synthetic transfer fixture illustrates how an oracle can trigger this heuristic even while answering every item correctly. This demonstrates a limitation of interpreting this metric as evidence of concealed capability. It does not prove that all entropy drops have the same cause. Oracle flags depend on the saved baseline as well as gold-key skew.

## Reproduce and interpret

Run `make evidence` to regenerate reports and independently compare counts, accuracy, entropy, and oracle flags against raw bundle rows. Run `make figures` to render the charts. Existing generated files are archived before replacement.

Inspect response samples and linked evidence pages before interpreting aggregate values. In particular, the strict parser expects an `ANSWER:` marker, whereas collection prompts sometimes requested a bare letter. Their disagreement can be a format mismatch. The stored labels are themselves outputs of collection parsers and are not an independently adjudicated answer basis.

The bundled slices are small and selected, no population false-positive rate is estimated, and this work establishes no model intent. Human annotations and blinded queues support review; they do not complete that review automatically.
