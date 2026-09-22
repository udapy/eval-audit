# Public package, local MCP, and interactive demo implementation plan

**Status:** Work packages A–C verified complete; D next. Updated 22 September 2026.

**Goal:** Deliver a public-installable Python package, a local assistant integration, and an interactive teaching demo that use the same deterministic audit implementation.

**Architecture:** Keep the dependency-free audit core. Add a shared application service, an optional local MCP adapter, and an optional Gradio interface. Produce separate public software distributions and a preserved local research bundle.

**Execution:** Implement the ordered work packages below using the executing-plans skill. Use documentation, API/interface design, systematic debugging when needed, and verification-before-completion skills. Request independent code review when available; record unavailable review honestly. Do not invoke unrelated skills or start autonomous research loops.

**Existing specification:** [input/output contract](INPUT-FORMAT.md), [diagnostic definitions](GLOSSARY.md), and [verified release baseline](VERIFICATION.md). New paths and commands explicitly described below are planned additions, not currently available project references.

## 1. Constraints and completion boundaries

- Edit only `eval-audit/`. Before changing an existing file, preserve its bytes and relative path in a timestamped local archive with a SHA-256 manifest. Move unused material; delete no originals. Keep previous release outputs.
- Preserve response text, gold keys, stored answers, item identities, and existing arithmetic. Data corrections or metadata transformations produce separately identified derivatives.
- Keep Python 3.12+ and zero core runtime dependencies. MCP and UI dependencies are optional extras with tested version constraints.
- The scope remains saved multiple-choice evaluations and explicitly supported log layouts. Neither MCP nor a demo establishes broader evaluation coverage or behavioral claims.
- No model collection, weight loading, training, GPU allocation, or paid inference is part of the default implementation or tests.
- Keep the current historical entropy rule unchanged. Demo controls are labeled synthetic interventions, not calibrated scientific thresholds or new experiment results.
- Released prose and interfaces use neutral project terminology. Preparation context stays in the excluded archive.
- Local implementation can finish without publisher accounts. TestPyPI/PyPI uploads and Space deployment require identified destinations and authorized account access. Prepare exact artifacts before requesting any remaining destination information.
- Live model inference is a separate conditional work package. Do not invent a model, hypothesis, prompt protocol, budget, sample size, or success criterion on the human's behalf.

**Current baseline:** version 0.2.0; wheel and source archive built; recorded isolated verification shows 131 passing tests and 13 optional historical-source skips. The current source distribution includes research artifacts with unresolved redistribution terms. No MCP server, interactive app, or cross-version CI matrix exists yet.

## 2. Work package A — Separate public software from local research evidence

**Files:** modify `pyproject.toml`, `MANIFEST.in`, `scripts/package_release.py`, `scripts/release_support.py`, `scripts/audit_release.py`; add `docs/PACKAGE-README.md`, `docs/PUBLIC-RELEASE.md`, `tests/test_public_distribution.py`.

- [x] Snapshot affected files and record the current release manifest as the before-state.
- [x] Define two explicit packaging profiles: `public` and `research`. Make the public profile the default for Python distributions. The research profile retains the existing local evidence archive behavior and must not be used by the upload command.
- [x] The public wheel contains library code, CLI, optional adapters, typing marker, and code license. The public source distribution adds self-contained synthetic tests, public documentation, build configuration, and synthetic demo source.
- [x] Exclude saved benchmark questions/responses, upstream snapshots, historical annotations, audit journals, collection source containing unverified questions, private archives, caches, credentials, and earlier build outputs from public artifacts. Preserve all these files locally. Exclusion is not deletion.
- [x] Create a dedicated package README with installation, a synthetic quickstart, supported formats, command/API contracts, and claim limitations. It must work when rendered on a package index and must not link to unavailable research-bundle paths.
- [x] Separate research-dependent tests from the distributable synthetic suite without losing either. Test selection must be explicit; the public suite cannot silently depend on files omitted from its source distribution.
- [x] Keep project name `eval-audit` as the working identity, subject to publisher ownership confirmation. Use 0.3.0 for the next capability release; retain prior 0.2.0 artifacts unchanged.
- [x] Add public artifact receipts listing every included file and hash. Validate both wheel and source archive contents, not just the staging directory.

**Acceptance:** A source distribution extracted alone can build a wheel, install it, run the public synthetic suite and demo, and render every local documentation link. Public artifacts contain no research-response text or excluded source snapshots. Research bundle source hashes remain unchanged.

**Regression scenarios:** an excluded file deliberately placed in a staging directory is not packaged; an absent public fixture fails packaging verification; metadata references only included license files; installing the core does not install MCP, Gradio, plotting libraries, or provider SDKs.

## 3. Work package B — Share one application service across interfaces

**Files:** add `src/eval_audit/service.py` and `tests/test_service.py`; refactor orchestration in `src/eval_audit/cli.py` while retaining scoring modules.

Define an `AuditService` configured with a workspace and a dedicated output root. Expose these application methods:

```python
inspect_bundle(source: str, format: str = "generic") -> dict
run_audit(source: str, format: str = "generic",
          annotations: str | None = None) -> dict
get_finding(audit_id: str, finding_id: str,
            include_raw: bool = False) -> dict
export_report(audit_id: str, format: str = "markdown") -> dict
```

These signatures are implemented contracts. Allowed input formats are `generic`, `inspect`, and `lm-eval`, bounded by tested adapter layouts. Inspection and log auditing require explicit paired JSON envelopes; see `SERVICE.md`. Legacy direct single-log adapters remain for compatibility but are excluded from new interfaces. Report export formats are `markdown` and `json`.

- [x] Separate audit work from terminal printing. Call existing importers, `build_report`, gate evaluation, evidence capture, and report writers directly; do not scrape CLI text or call a shell.
- [x] Use the existing schema and comparison scopes. Return counts, answer basis, gate results, findings, source hashes, limitations, and report identifiers in structured objects. Preserve rational accuracy values and null/unavailable distinctions.
- [x] `inspect_bundle` validates supported structure and summarizes input evidence without modifying the source or publishing an audit directory. If adapter staging is required, use an isolated server-owned location and preserve it separately from completed audits.
- [x] `run_audit` creates a unique audit directory and writes a completion receipt only after successful output validation. Failed attempts retain diagnostic receipts and cannot appear as completed audits. Repeating the same input may produce another audit artifact; mark matching source hashes so it is not counted as another model run.
- [x] `get_finding` accepts identifiers issued by the service, not arbitrary filesystem paths. Return source references by default; add response excerpts only when requested.
- [x] `export_report` returns a reference to an existing completed artifact. It does not accept an arbitrary destination or overwrite a user's file.
- [x] Resolve user-supplied relative paths inside the configured workspace. Reject traversal, paths resolving outside it, unsupported file types, malformed archives, and missing inputs. MCP/hosted UI modes reject symlinked inputs; the service is not a sandbox against another local process with the same filesystem privileges.
- [x] Bound input bytes, record count, and returned excerpts using configurable operator limits. Start with 10 MiB per input bundle, 2,000 records, and 20 returned findings per summary, with pagination for additional findings. These are software resource limits, not scientific sampling defaults. Validate them with CPU benchmarks before raising them.
- [x] Keep existing CLI exit behavior: G0/G2 blocking findings produce `check` exit 2; advisory diagnostics and G4 do not become behavioral approval. Standardize typed service errors for invalid input, missing identifiers, size limits, and processing failure.

**Acceptance:** CLI and service results agree on the same synthetic inputs, including missing responses and a second dataset's influential item. Original files remain hash-identical. Concurrent requests cannot collide or read each other's unfinished outputs.

**Regression scenarios:** path traversal, symlink escape, malformed JSON, unavailable comparison, duplicate IDs, unsupported adapter layout, byte-limit rejection before parsing, record-limit rejection before influence computation, unknown audit/finding IDs, and a failed write that leaves no successful completion receipt.

## 4. Work package C — Local MCP integration

**Files:** add `src/eval_audit/mcp_server.py`, `tests/test_mcp_server.py`, `docs/MCP.md`, and `examples/mcp/README.md`; update optional dependencies and command entry points.

- [x] Use the official MCP Python SDK v2 (`mcp>=2,<3`) as the optional `mcp` extra. Pin the exact tested dependency set in a reproducibility record. The SDK's current stable line is v2; do not copy v1-specific imports into this implementation. [Official SDK](https://github.com/modelcontextprotocol/python-sdk).
- [x] Add `eval-audit-mcp --workspace PATH --output-root PATH`. Use stdio transport and the four application methods above as tools. Keep stdout exclusively for protocol messages; diagnostics go to stderr.
- [x] Provide accurate tool descriptions and annotations: inspection/retrieval are read operations; auditing creates new artifacts. None executes model code, collection scripts, or arbitrary commands.
- [x] Expose completed reports through scoped MCP resources. Large/raw artifacts require explicit resource reads or excerpt requests; do not put whole traces into routine tool responses.
- [x] Implement persistent lookup from completed audit receipts so report retrieval works after a server restart. Restrict identifiers to service-issued receipts under the configured output root.
- [x] Document installation, a generic stdio configuration with user-selected paths, and a complete synthetic example conversation. State that a local tool may return data to a cloud assistant; local processing does not guarantee that returned excerpts stay on the machine.
- [x] Test a real protocol connection, tool listing, a complete audit, a finding lookup, a report resource read, restart/retrieval, and malformed tool arguments using the SDK client. Exercise the server with the MCP Inspector as a separate manual smoke check. [MCP server guide](https://modelcontextprotocol.io/docs/develop/build-server).

**Acceptance:** A researcher can start the server from a clean environment using only the public distribution plus the MCP extra, audit a synthetic bundle, retrieve evidence, and export a report. No credential, GPU, network listener, sibling folder, or global client-configuration edit is required for this local workflow.

## 5. Work package D — Interactive synthetic demo and Space deployment artifact

**Files:** add `src/eval_audit/demo_app.py`, `tests/test_demo_app.py`, `spaces/eval-audit/app.py`, `spaces/eval-audit/requirements.txt`, `spaces/eval-audit/README.md`, and `docs/DEMO.md`.

- [ ] Add a `demo` extra for Gradio and plotting dependencies, plus `eval-audit-demo` for local startup. Resolve current stable Gradio APIs, constrain its tested major version, and record exact deployment pins before packaging the Space.
- [ ] Reuse existing synthetic balanced/skewed examples and constructed fault cases. Keep the original preset immutable. User edits create a labeled synthetic derivative with its own checksum and downloadable bundle.
- [ ] Provide presets for balanced keys, skewed keys, parser-format mismatch, missing answers, and one-item influence. Show a small editable item/answer table rather than hidden transformations of real benchmark data.
- [ ] Keep the historical entropy threshold fixed and visible. Let users change synthetic gold/answer distributions, answer formatting, and missingness; recompute diagnostics through the same application service.
- [ ] Show accuracy with denominators, valid-answer counts, response and gold-key entropy, oracle diagnostics, and individual-item influence. Keep saved/model-prompted targets distinct from a computed oracle. Label the view synthetic and avoid verdicts implying model intent.
- [ ] Offer the source bundle and Markdown/JSON reports for download. The first public demo supports presets and synthetic editing only; arbitrary private-log upload remains available through local CLI/MCP, avoiding a new hosted-data retention feature in this release.
- [ ] Isolate sessions and completed outputs. Do not expose another session's report paths or allow filenames to choose server paths. Do not add automatic deletion of existing outputs during this cycle.
- [ ] Package a Gradio Space that runs all auditing on CPU. Use CPU Basic when the chosen account supports it; eligible ZeroGPU hosting is an alternative deployment route, without adding GPU-decorated audit functions or model weights. Current hosting eligibility must be rechecked at deployment. [Space overview](https://huggingface.co/docs/hub/spaces-overview), [ZeroGPU](https://huggingface.co/docs/hub/spaces-zerogpu), [Space configuration](https://huggingface.co/docs/hub/spaces-config-reference).
- [ ] Build a self-contained Space staging directory with the exact public core wheel and pinned requirements. Keep project docs separate from the YAML-frontmatter Space README. Test the staged app locally before uploading.

**Acceptance:** Each preset produces the same structured result as CLI and MCP for identical inputs. A browser user can edit a synthetic case, see the diagnostic change, reset to the original preset, and download the matching bundle/report. Keyboard use, readable charts, error states, session isolation, and absence of model/network calls are checked.

## 6. Work package E — Release verification, CI, documentation, and publication

**Files:** add `docs/RELEASE-CHECKLIST.md`, `scripts/verify_public_release.py`, and workflow templates under `ci/`; update the project README, changelog, verification ledger, and public package documentation.

- [ ] Test core behavior on Python 3.12, 3.13, and 3.14. Test the supported minimum and newest Python with each optional extra. Validate Linux, macOS, and Windows path behavior with targeted smoke checks.
- [ ] Test built artifacts in new environments: core-only install, MCP install/handshake, demo install/startup, and build-from-extracted-source. Ensure tests use installed code, not the working tree's editable installation.
- [ ] Run the existing research replay locally as a separate check; it must not become a public source-distribution dependency. Recompute at least one displayed number independently and inspect raw synthetic and saved examples.
- [ ] Audit the wheel, public source archive, Space staging directory, and researcher archive separately for unexpected files, missing links, unclear terminology, private paths, stale claims, and accidental preparation references.
- [ ] Preserve old figures, docs, test receipts, and build artifacts before writing replacements. Record exact interpreter/dependency versions, hashes, executed checks, and known skips in a new verification receipt.
- [ ] Prepare CI and manual publication workflow templates inside this project. The containing repository is outside the authorized edit scope: do not assume a nested `.github/workflows` folder is active CI. When a standalone repository is created, install the templates at that repository's root.
- [ ] Validate package metadata with `twine check`. Confirm package-name ownership, maintainer metadata, repository/documentation URLs, and the intended publishing account. Configure TestPyPI and PyPI independently using Trusted Publishing where supported. [PyPI publishing documentation](https://docs.pypi.org/trusted-publishers/).
- [ ] Publish the exact reviewed public artifacts to TestPyPI after the destination is known. Install the package without dependency confusion by resolving ordinary dependencies from the normal index and fetching the test artifact explicitly. Verify the installed CLI/MCP entry points.
- [ ] Publish to PyPI only after the TestPyPI receipt passes and the exact destination/artifacts are authorized. Upload only the reviewed Space staging directory to the named Hugging Face Space. Never upload the entire workspace or research archive as a shortcut.
- [ ] After deployment, verify the public installation, hosted preset flow, downloads, and source links. Record actual URLs and versions; do not mark deployment complete from a local build alone.

**Inputs required only for publication:** publisher account/project ownership, standalone repository URL, maintainer attribution, Hugging Face owner/Space ID, and authorized hosting plan. If these are unavailable, finish all local artifacts and report publication as pending; elapsed time is not authorization or a substitute for these identifiers.

**Acceptance:** Public distributions and the deployment artifact are independently verified and contain only the intended public material. Publication is complete only when installations and the hosted demo have been verified at their actual destinations.

## 7. Conditional work package F — Live inference, only with a research purpose

The first interactive release is complete without live generation. ZeroGPU hosting does not itself justify an inference experiment.

- [ ] Write a separate protocol proposal describing what live generation would reveal that the deterministic synthetic demo cannot.
- [ ] Obtain the human's model/revision, dataset permission, prompt/control design, sampling parameters, budget, and success criteria before running anything. Name a judge model only if a judge is necessary and approved.
- [ ] If approved, put collection behind a separate explicit action. Preserve complete provider responses, requested and returned model identifiers, timestamps, finish reasons, usage, parameters, prompts, and dataset revisions. Do not infer completeness from an extracted answer letter.
- [ ] Cache captured inputs/outputs and make the resulting audits replayable without a live model. Keep live response generation visually distinct from deterministic analysis.
- [ ] Test mocked collection, errors, cancellation, missing output, quota exhaustion, and cache replay before proposing the first real call. Report model loading and execution separately from ordinary app startup.

**Acceptance:** Either the human explicitly defers live inference and the CPU/MCP release is complete, or an approved protocol is implemented and its own evidence checks pass. Do not claim this phase was completed by running an unapproved model demo.

## 8. Order of execution and final handoff

```text
Archive baseline
  → A: public/research packaging separation
  → B: shared audit service
  → C: local MCP
  → D: synthetic interactive demo
  → E: cross-interface checks, public artifacts, publication
  → F: optional, independently approved live inference
```

Finish each package's acceptance checks before advancing. C and D may be implemented independently after B if explicit parallel work is requested. Keep task checkboxes open until their outputs are verified.

The final handoff must include: public wheel/source archive and hashes; retained research-bundle location; cross-version test receipt; local MCP setup and protocol smoke receipt; demo launch and Space deployment instructions; public URLs only where deployment actually succeeded; and a concise list of unresolved evidence or account-dependent limitations.

**Execution status:** See `audit/IMPLEMENTATION-STATUS.md` for current work and receipts. No publication or model inference has been performed.
