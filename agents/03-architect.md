# 03 — Architect

**Mission:** build deep modules with small interfaces, then refactor without
changing one observable byte.

**Inputs:** frozen spec, `docs/PLAN.md`, `improve-codebase-architecture` method.

**Outputs:** `prism/` module map, `docs/ARCHITECTURE.md`,
`docs/ARCHITECTURE_REFACTOR.md`, `tests/golden/BASELINE.json`.

**Done when:**

- Detection, resolution, rendering, and reporting are separated.
- Adding a rule or renderer does not require editing an orchestrator.
- `ScanContext` removes argument fan-out.
- Golden hashes are captured **before** the first structural edit.
- All 9 hashes match after the refactor.

**Reject if:** the deletion test is skipped, or a public API / output format
changes during the refactor.
