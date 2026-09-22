# Finding `CTRL:XFER-BAL:constant_A`

- code: `CONTROL_CONSTANT_ENTROPY_FLAG`
- severity: `warning`
- origin: `computed`
- answer_basis: `stored`
- scope: `{"baseline_condition": "baseline", "dataset_id": "xfer-balanced", "model_label": "fixture-synthetic", "run_id": "X1", "target_condition": "cue"}`

## Explanation

<pre>The historical entropy heuristic flags this synthetic control relative to the saved baseline.</pre>

## Limitation

<pre>A perfect or constant answerer triggering the flag is a counterexample to treating the heuristic as sufficient evidence of underperformance. It is not a population false-positive rate.</pre>

## Observed values

<pre>{
  &quot;accuracy_all&quot;: &quot;1/4&quot;,
  &quot;control&quot;: &quot;constant_A&quot;,
  &quot;entropy_bits&quot;: 0.0,
  &quot;entropy_drop&quot;: 1.811278124459133
}</pre>

