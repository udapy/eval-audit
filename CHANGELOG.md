# Changes

## 0.3.0

- Optional `eval-audit[mcp]` stdio server for the shared local audit service. The core package remains dependency-free.

## 0.2.0

- Researcher-facing evidence catalog, independently checked comparison data, reproducible static figures, and standalone offline release checks.
- Historical importer/profile names are now `import-historical` and `historical-v1`; old names are not aliases. Reimport original source bytes using the new importer when migrating a historical manifest. Original manifests and reports remain preserved locally.
- Reports now include scoped G0–G4 results. CLI text describes engineering diagnostics rather than claiming behavioral validity. G0/G2 blocking policy is retained; G1/G3 remain advisory.
- Corrected the assigned-response example's description and distinguished ARC target entropy from oracle entropy.
- Application preparation and unused experiment scaffolding are archived locally and excluded from release artifacts.
- Review queue output now refuses existing files and retains each influential item's comparison dataset.
