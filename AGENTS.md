# Project maintenance

- Work only inside this project unless the user explicitly expands scope.
- Preserve files before modifying or moving them. Archive unused material; do not delete it. Use timestamped destinations and checksums.
- Default workflows are offline. Do not run model collection, load weights, or allocate compute as part of release verification.
- Preserve raw response text, gold labels, and stored answers. A metadata rename produces a derived version; retain the original and record its checksum.
- Distinguish authored responses, saved response text, provider records, and computed controls.
- The human owns scientific interpretation. Report verified arithmetic and limitations; do not write an application executive summary.
- Record release verification in docs/VERIFICATION.md and audit/STATUS.md. Do not depend on files outside this project.
- Run make check, independently verify reported numbers, inspect raw examples, and audit the isolated release before claiming completion.
