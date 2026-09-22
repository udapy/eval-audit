# Release verification

## 0.3.0 implementation checkpoint

Work packages A–C are locally verified. Public software excludes research logs and snapshots; isolated source-build verification passed 109 tests at A. The shared service passes 22 targeted tests. At B the public suite passed 131 tests. After the MCP adapter, the public suite passed 137 tests and `make check` passed 164 tests with 13 optional historical skips. Full offline replay at B passed all five research bundles. See [step A](../audit/step-a.json), [step B](../audit/step-b.json), and [step C](../audit/step-c.json). The interactive demo and publication are still pending. The verification below records the preserved 0.2.0 baseline.


Verified on 22 September 2026 with Python 3.14.7. The package declares Python 3.12+; other supported interpreter versions were not tested in this session.

## Evidence preservation

[Preservation receipt](../audit/preservation.json): all 428 pre-edit files (2,491,433 bytes) were recovered from checksum-verified backups. Four saved example bundles remain byte-identical. The transfer fixture's release copy changes only provenance notes; all other fields are unchanged. Unused preparation files and experiment scaffolding were moved into the local archive. No originals were deleted. Renamed annotation metadata and historical interfaces have archived originals.

## Offline behavior

`make check`: **131 passed, 13 skipped**. The skips are optional integrations requiring a separately supplied historical collection; default release checks need no sibling directories. The old experimental scaffold tests remain archived with that unused scaffold. Five source bundles and eight comparisons pass independent count, accuracy, entropy, and oracle-flag verification. All five import/audit/triage flows and expected scorecard exit codes pass.

Targeted regressions verify that scorecards do not validate behavioral claims, ARC oracle and target values stay distinct, triage refuses existing output files, and influential items from a second dataset retain the correct scope.

[Source receipts](../data/provenance/README.md) were independently replayed offline: 28 captured files verified, 90 item comparisons reproduced. The capture uses read-only upstream GETs, not inference. Statistics and science items match; the two local security/math sets do not match their claimed current subject test splits.

## Distribution checks

Built the researcher archive, source distribution, and wheel. Installed the wheel into a fresh virtual environment and confirmed imports resolve to its installed site-packages. Ran all tests there with source-path injection disabled: **131 passed, 13 optional skips**. All five bundled CLI flows, expected scorecard codes, and the source-receipt replay passed from the standalone researcher directory. The isolated release audit also passed.

Inspected 20 representative saved records, including changed answers, parenthetical formatting, literal backslash-n sequences, and missing ARC text. The selected rows and observations are in the [sample review](../audit/sample-review.json). Figures were rendered and visually inspected.

## Corrections from the audit

- Assigned example responses are labeled synthetic despite an original model label.
- Unverified benchmark origins and unavailable provider envelopes are explicit.
- ARC target entropy drop and computed oracle drop are distinguished; G2 does not flag this ARC slice.
- The CLI uses implemented scoped gates and no longer prints that a behavioral claim is valid.
- Triage correctly scopes influence by comparison dataset and refuses to overwrite existing review files.
- Missing response denominators, parser-format disagreements, and review limitations are documented.
- Preparation context is excluded from release files, and historical interfaces use neutral names.

The [automated release audit](../audit/release-audit.json) checks included filenames/content, local links/anchors, catalog hashes, and machine-specific paths. Original raw provenance strings remain source claims; their assessed status is documented alongside them.

## Remaining evidence limitations

Recorded model labels do not authenticate provider execution. Historical collection revisions are unknown. Embedded question attribution and saved-text redistribution terms remain unresolved. Small selected slices and synthetic fixtures do not establish representative benchmark performance, population false-positive rates, or model intent. These limitations are evidence gaps, not broken project dependencies.

Independent source verification completed. An additional code-review agent could not run because its usage limit was reached; the final code and packaging review was completed locally, with regression and isolated-install checks recorded above.
