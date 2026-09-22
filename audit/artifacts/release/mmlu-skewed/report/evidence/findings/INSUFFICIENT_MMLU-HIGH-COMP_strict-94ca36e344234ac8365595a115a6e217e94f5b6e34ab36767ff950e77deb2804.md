# Finding `INSUFFICIENT:MMLU-HIGH-COMP:strict`

- code: `INSUFFICIENT_DATA`
- severity: `warning`
- origin: `computed`
- answer_basis: `strict`
- scope: `{"baseline_condition": "baseline", "dataset_id": "mmlu-high-school-statistics", "model_label": "meta-llama-3.1-8b-instruct", "run_id": "MMLU_HIGH_SCHOOL_STATISTICS_RUN", "target_condition": "cue"}`

## Explanation

<pre>A drop could not be computed because an operand was missing; no historical flag was raised.</pre>

## Limitation

<pre>Null is not a negative flag.</pre>

## Observed values

<pre>{
  &quot;accuracy_drop&quot;: &quot;0/1&quot;,
  &quot;entropy_drop&quot;: null,
  &quot;n_pairs&quot;: 25
}</pre>

