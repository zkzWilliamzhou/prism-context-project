# Changelog

All notable changes to this project are documented here. The format is based on
Keep a Changelog, and this project adheres to Semantic Versioning.

## [1.0.0] - 2026-11-13

### Added

- Offline, zero-dependency Python 3.9+ CLI and library.
- Four documented harness models: `codex`, `claude`, `zed`, `cascade`.
- `resolve`, `diff`, `audit`, `snapshot`, `check`, `init`, `explain`, and
  `harnesses` commands.
- TTY, JSON, Markdown, and SARIF 2.1.0 output.
- 16 deterministic audit rules with `prism explain`.
- Snapshot drift gate for effective contexts per target file.
- Bounded, containment-checked discovery and `@import` expansion.
- Recursive credential redaction and terminal-control sanitization.
- 82 tests, including hostile-input regressions and a byte-level golden gate.
- A behavior-preserving architecture refactor: declarative rule catalog,
  `ScanContext`, rule/ renderer registries, and memoized directive parsing.
- Vendored/reconstructed GitHub skill bundle, agent contracts, workflow,
  ideation log, prior-art matrix, and 10-round review log.

### Fixed

- Contradiction false negatives caused by strict Jaccard similarity.
- Bare `@import` lines counted as directives.
- Shadowing over-reported for nested `AGENTS.md` without a local `CLAUDE.md`.
- Credential leakage through resolutions, divergences, and SARIF evidence.
- `@import` hop limits not surfaced in reports.
- Snapshot self-drift on first `check` after `snapshot --write`.
- Config and target path escapes; symlink write escapes.
- ANSI/bidi control sequences reaching terminal output.
- O(targets x harnesses x sources) directive re-parsing.
- Minimal library `Report()` objects crashing the TTY renderer.

### Known limitations

See [docs/LIMITATIONS.md](docs/LIMITATIONS.md). Loader models are documented
approximations, not live-agent traces; token counts are a bytes/4 proxy; a
clean audit is not proof of instruction quality.
