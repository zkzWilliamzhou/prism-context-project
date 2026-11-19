# Behavior-preserving architecture refactor

## Requirement

> Use the `improve-codebase-architecture` skill, but first make sure you did not
> change any function of the program.

The upstream skill was located in `mattpocock/skills` at
`skills/engineering/improve-codebase-architecture/SKILL.md` and vendored in
[../skills/mattpocock-improve-codebase-architecture/](../skills/mattpocock-improve-codebase-architecture/).
Direct installation into the runtime was unavailable, so its documented
process was applied manually: explore friction, name deepening candidates,
apply the deletion test, design a small interface, and verify at the seam.

## Step 0 — Freeze behavior first

Before any structural edit, nine SHA-256 hashes were captured:

| Command | Format | Exit |
|---|---|---:|
| `audit src/app.py` | json, tty, markdown, sarif | 1 |
| `resolve src/app.py --harness all` | json | 0 |
| `diff src.app.py` | json | 0 |
| `snapshot` | json stdout | 0 |
| `harnesses` | tty | 0 |
| `explain --all` | tty | 0 |

These live in `tests/golden/BASELINE.json`. `tests/test_golden.py` reruns every
command in a subprocess and compares both exit code and exact stdout bytes.

## Friction found

1. `rules.py` mixed rule metadata, detection, sorting, and divergence
   recomputation.
2. `render.py` used a four-branch `if/elif` dispatch.
3. Adding a rule or format required editing an orchestrator.
4. `report.build` recomputed divergences independently of rule evaluation.
5. Identical sources were reparsed thousands of times in `snapshot`.

## Deepening applied

| Before | After | Complexity hidden |
|---|---|---|
| Inline `RULES_CATALOG` | `rules_catalog.py` | Metadata reused by `explain` and SARIF |
| `run_rules(d, resolutions, cfg)` fan-out | `ScanContext` | One dependency carrier |
| Hard-coded sort inside `run_rules` | `RuleRegistry.run` | One ordering contract |
| `if fmt == ...` | `RendererRegistry` | Format lookup and TTY-option special case |
| Repeated `extract(text, source, harness)` | `@lru_cache` on parser core | Snapshot performance |
| Dead imports / dead git-root walk | Removed | Smaller surface |

The public API (`audit`, `resolve`, `build_snapshot`, CLI commands, exit codes,
rule IDs, JSON keys, and output bytes) is unchanged.

## Verification

- `python3 -m unittest discover -s tests`: 82 tests, OK.
- All 9 golden hashes byte-identical after the refactor.
- Unknown output formats still fall back to TTY, preserving pre-refactor
  behavior.
- `tests/test_architecture.py` proves a custom renderer and a custom rule can
  be registered without editing dispatch logic.

## What was deliberately not changed

- The four harness models and their caveats.
- Any rule ID, severity, evidence string, or fix text.
- Snapshot schema and fingerprint algorithm.
- The frozen `examples/demo/` corpus.
- Runtime guarantees: no network, no subprocess, no telemetry, no new
  dependencies.

A later robustness fix made the TTY renderer tolerate a minimal library
`Report()` object. Every CLI-generated report already carries limitations, so
the golden output is unchanged; only an invalid degenerate object stopped
crashing.
