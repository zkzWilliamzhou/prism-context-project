# Contributing

## Non-negotiable gates

1. **Zero runtime dependencies.** Standard library only, Python 3.9+.
2. **No network, no subprocess, no telemetry** anywhere in `prism/`. The test
   suite greps for the forbidden imports.
3. **Read-only by default.** Only `init --write` and `snapshot --write` may
   write, and both go through `safe_write()`.
4. **Behavior freeze.** `tests/golden/BASELINE.json` holds SHA-256 hashes of
   every CLI command and output format from before the architecture refactor.
   If a change alters a byte, either the change is wrong or the baseline must
   be updated in a separate, explicitly justified commit.
5. **Tests before merge.** `python3 -m unittest discover -s tests -v` must be
   green.
6. **High precision, low recall.** A new rule must be justifiable from source
   text in two lines and must cite `file:line`. Do not ship a score or a vague
   heuristic.

## Workflow

```bash
python3 -m unittest discover -s tests
python3 -m prism --root examples/demo audit src/app.py --why
python3 -m prism --root examples/demo snapshot
```

Add a test for every bug fix. Add a `PF###` entry to
`prism/rules_catalog.py` for every new rule, and register the check in
`prism/rules.py` rather than editing an orchestrator.

## Adding a harness

Add a resolver to `prism/harnesses.py`, document its source URL and caveat in
`HARNESSES`, add it to `ALL_HARNESSES` in `prism/config.py`, and add a
`tests/test_harnesses.py` case. Never claim it is an exact emulator.

## Adding an output format

Register a `Renderer` in `prism/render.py`. Do not add another `if` branch to
`render()`.

## Style

- Deterministic ordering everywhere.
- Sanitize anything derived from an instruction file before it reaches a
  terminal or a report.
- Prefer deep modules with small interfaces. The interface is the test surface.
