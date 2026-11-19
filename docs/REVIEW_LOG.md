# Strict review log

**Verdict legend:** `ACCEPT` / `REWORK` / `REJECT`. The manager required more
than 8 rounds; this log records 10. Every round names a concrete defect, a fix,
and a regression test.

| Round | Agent | Finding | Severity | Verdict | Fix | Regression test |
|---:|---|---|---|---|---|---|
| R1 | QA | Contradiction detector used Jaccard similarity and missed "never use tabs. always use spaces."; bare `@import` lines counted as directives; shadowing was reported for nested `AGENTS.md` with no local `CLAUDE.md` | High | REWORK | Switched to overlap coefficient with head-token equality and scope guard; skipped bare imports; made shadowing local to the directory | `test_directives.py`, `test_harnesses.py` |
| R2 | Security | A credential in `AGENTS.md` leaked into `resolutions`, `divergences`, and SARIF evidence; ANSI escapes could reach the terminal | Critical | REJECT → rework | Added `redact()`, `redact_obj()`, redaction at `Report.to_dict()`, directive-token redaction, and sanitization of every rendered path/note | `test_rules.py`, `test_hostile.py` |
| R3 | Security | `@import` hop limits were invisible; target paths could escape the root; `.INSTRUCTIONS.MD` was not classified case-insensitively | High | REWORK | Added `depth` status while still loading the file, `is_within()` target check, lowercased classification | `test_discovery.py`, `test_hostile.py` |
| R4 | QA | `prism check` reported drift immediately after `snapshot --write`; `PF041` used a harness name as a file path; zero line numbers rendered as `:0` | Medium | REWORK | Excluded the generated snapshot from targets; blanked the finding path; dropped zero line numbers | `test_cli.py` |
| R5 | Security | `--config` could point outside the repository; `init`/`snapshot` could write through a symlink | Critical | REJECT → rework | Containment-check config reads; added `safe_write()` that refuses symlinks and out-of-root writes | `test_hostile.py` |
| R6 | Architect | Snapshot reparsed identical sources O(targets x harnesses); dead imports and unused helpers remained | Low | REWORK | Memoized directive extraction with `lru_cache`, removed dead imports, documented the scan-root boundary | `test_hostile.py` performance case |
| R7 | Security | No test enforced the no-network/no-process promise; empty repos, non-UTF-8 files, cwd changes, and `fail-on` thresholds were unverified | High | REWORK | Added hostile regressions for forbidden imports, empty repo, malformed UTF-8, cwd independence, thresholds, and all four output formats | `test_hostile.py`, `test_cli.py` |
| R8 | Architect | Rules, catalog, renderers, and divergence recomputation were tangled; adding a rule or format required editing an orchestrator. First refactor attempt began before freezing behavior | High | REJECT → rework | Stopped, froze `tests/golden/BASELINE.json`, then introduced `rules_catalog.py`, `ScanContext`, `RuleRegistry`, `RendererRegistry`, and registered checks/renderers | `test_golden.py`, `test_architecture.py` |
| R9 | Boss | Architecture refactor had to be proven behavior-neutral, not just "looks equivalent" | Critical | REWORK | Kept unknown-format TTY fallback, preserved every output byte, and reran all 9 frozen SHA-256 hashes | `test_golden.py` |
| R10 | QA | Minimal library `Report()` crashed the TTY renderer; release docs, skills bundle, CI, and archive were missing | Medium | REWORK | Guarded empty limitations; wrote docs, agents, skills, CI, notices, example config; ran the full suite | `test_architecture.py`, final full-suite run |

## Rejected work (explicitly)

- The first skill-install attempt claimed upstream repos could be installed by
  `git clone`; the sandbox returned HTTP 403. The manager rejected the implied
  claim. Final bundle is explicitly labeled **reconstructed from public
  documentation**, with source URLs and license caveats.
- The first prior-art conclusion said "no validator exists". Rejected. The final
  wording is "no widely adopted per-file effective-context + drift gate
  located in a bounded search".
- The first architecture refactor lacked a pre-change behavior freeze. Rejected
  before any structural edit was accepted.

## Final gate

- `python3 -m unittest discover -s tests`: **82 tests, OK**.
- `tests/test_golden.py`: all 9 command/format SHA-256 hashes unchanged.
- All four output formats parse; SARIF is valid 2.1.0.
- No forbidden network/process imports in `prism/`.
- No new file added inside the frozen `examples/demo/` corpus.
- Archive produced as a single ZIP.
