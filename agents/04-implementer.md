# 04 — Implementer / TDD

**Mission:** turn the spec into a deterministic, offline, zero-dependency CLI
and library.

**Inputs:** architecture contract, rule catalog, demo corpus requirements.

**Outputs:** `prism/*.py`, `examples/demo/`, `tests/`.

**Done when:**

- Every rule cites `file:line` and has a regression test.
- No `socket`, `subprocess`, `requests`, `urllib`, `eval`, `exec`, or `pickle`
  in `prism/`.
- Reads are bounded; writes require an explicit flag and `safe_write()`.
- Output ordering is deterministic across runs and cwd.
- Four output formats parse correctly.

**Reject if:** a rule ships without evidence, an IO path is unbounded, or a test
passes for the wrong reason.
