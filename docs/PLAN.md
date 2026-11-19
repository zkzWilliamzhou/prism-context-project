# Execution plan

## Phase 0 — Grill the idea

- Owner: Product Griller + Prior-Art Researcher.
- Output: [IDEA.md](IDEA.md), [PRIOR_ART.md](PRIOR_ART.md).
- Gate: at least 10 independent candidates, at least 8 adversarial objections,
  explicit "not located" rather than "does not exist" novelty language.

## Phase 1 — Freeze the spec

- Owner: Boss.
- Output: this plan plus `README.md` pitch.
- Gate: one sentence explains the product; offline/zero-dependency/read-only
  constraints are written down; success criteria exclude star count.

## Phase 2 — Architecture

- Owner: Architect, using the vendored
  `improve-codebase-architecture` methodology.
- Output: `prism/` module map, `docs/ARCHITECTURE.md`.
- Gate: deep modules with small interfaces; detection, resolution, rendering,
  and reporting separated; every extension point documented.

## Phase 3 — Implementation (TDD)

- Owner: Implementer, using the vendored `tdd` discipline.
- Output: CLI, library, demo corpus, unit tests.
- Gate: every rule cites `file:line`; no network/subprocess imports; bounded IO;
  deterministic ordering; redaction at the report boundary.

## Phase 4 — Security and hostile-input review

- Owner: Security Reviewer.
- Output: `SECURITY.md`, `tests/test_hostile.py`.
- Gate: path escape, symlink escape, ANSI/bidi injection, secret leakage,
  malformed UTF-8, empty repo, unbounded reads, and import cycles all covered.

## Phase 5 — Strict review rounds

- Owner: Boss, rejecting work that is vague, faked, or incomplete.
- Output: [REVIEW_LOG.md](REVIEW_LOG.md).
- Gate: more than 8 rounds; each round names the defect, the fix, and the
  regression test. A round without a concrete artifact is rejected.

## Phase 6 — Behavior-preserving architecture refactor

- Owner: Architect + Boss.
- Output: `rules_catalog.py`, `context.py`, `registry.py`, registered rules and
  renderers, memoized parsing.
- Gate: freeze SHA-256 hashes of every CLI command and output format **before**
  touching structure; after the refactor, `tests/test_golden.py` must be byte
  identical. No functional change is allowed.

## Phase 7 — Docs, agents, and skills

- Owner: Docs Agent.
- Output: `docs/`, `agents/`, `skills/`, CI, packaging, notices.
- Gate: every claim has a source or is labeled a decision; upstream skill
  status is honest; limitations ship with the product.

## Phase 8 — Release

- Owner: Boss.
- Output: full test suite, golden gate, demo commands, ZIP.
- Gate: 82/82 tests green, all formats parse, no forbidden imports, no file
  added to the frozen demo corpus, archive contains every deliverable.

## Manager rejection criteria

The boss sends work back when:

- a claim outruns the evidence;
- a "fix" has no regression test;
- a rule fires without `file:line` evidence;
- output changes without an updated golden justification;
- a skill is presented as a verbatim upstream mirror when it is reconstructed;
- a security control is described but not enforced in code;
- an agent reports "done" without listing files changed and tests run.
