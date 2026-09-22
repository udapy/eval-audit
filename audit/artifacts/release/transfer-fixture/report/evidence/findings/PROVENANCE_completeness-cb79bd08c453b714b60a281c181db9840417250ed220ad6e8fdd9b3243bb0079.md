# Finding `PROVENANCE:completeness`

- code: `PROVENANCE_TRUNCATION`
- severity: `info`
- origin: `computed`
- answer_basis: `None`
- scope: `{}`

## Explanation

<pre>Saved outputs are not labeled complete. Strict parse metrics describe available text only.</pre>

## Limitation

<pre>Missing request text, finish reasons, and snapshots cannot be inferred from a parse failure.</pre>

## Observed values

<pre>{
  &quot;n_rows&quot;: 32,
  &quot;response_completeness_values&quot;: [
    &quot;complete&quot;,
    &quot;possibly_truncated&quot;
  ]
}</pre>

