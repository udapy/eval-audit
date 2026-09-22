# Release status

## 0.3.0 implementation checkpoint

Work packages A–C are locally verified. Public software excludes research logs and snapshots; isolated source-build verification passed 109 tests at A. The shared service passes 22 targeted tests. At B the public suite passed 131 tests. After the MCP adapter, the public suite passed 137 tests and `make check` passed 164 tests with 13 optional historical skips. Full offline replay at B passed all five research bundles. See [step A](step-a.json), [step B](step-b.json), and [step C](step-c.json). The interactive demo and publication are still pending. The verification below records the preserved 0.2.0 baseline.


Researcher package organized; original files preserved in the excluded local archive. No model inference, weight loading, GPU allocation, or paid API calls were performed during release preparation. Read-only public dataset requests were used to verify item provenance.

Offline tests on 22 September 2026: 164 passed, 13 optional historical-source tests skipped. The public suite passed 137. Five bundles and eight comparisons independently replayed before this MCP step. Static figures and research note generated from checked values.

See [verification](../docs/VERIFICATION.md), [preservation](preservation.json), [release audit](release-audit.json), and [catalog](../data/README.md). Public redistribution rights for some saved content remain unresolved; no upload or publication has been performed.
