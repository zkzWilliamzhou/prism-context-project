# Limitations

These limitations are also embedded in every JSON report. Read them before
treating a green run as a guarantee.

1. **Modeled, not traced.** Harness loaders are models of public documentation,
   not traces from a live agent. Vendors do not publish stable algorithms and
   they change between releases. Every resolution carries a model version,
   source URL, and caveat.
2. **Composition, not behavior.** `prism` resolves which instruction files
   reach a context. It does not predict what an LLM will do, does not measure
   skill invocation, and cannot see host system prompts, user history, or tool
   availability.
3. **High precision, low recall.** Directive extraction fires only on explicit
   list items or polarity markers. A clean result means no mechanically
   provable defect was found, not that the instructions are good.
4. **Token proxy.** Counts are deterministic `bytes/4` estimates, not
   tokenizer output. They are useful for CI budgets, not billing.
5. **Heuristic security.** Secret, injection, and risky-command rules are
   pattern checks. They can miss novel variants and are not a security scan.
6. **No global context.** Personal/global instruction files outside the
   repository are intentionally never read.
7. **Four harnesses only.** `codex`, `claude`, `zed`, and `cascade` are modeled.
   Other agents are discovered as sources but not resolved.
8. **Bounded discovery.** 2 MB per file, 32 MB total, 5,000 files, depth 12,
   plus `max_targets`. `PF090` reports when a limit was hit.
9. **YAML subset.** The frontmatter parser supports scalars, simple lists/maps,
   and block scalars. Unsupported syntax produces `PF001` warnings rather than
   a guess.
10. **Snapshot scope.** Snapshots pin modeled composition, not model behavior.
    They fail on instruction changes, not on vendor loader updates.
11. **Stars are not quality.** The 100k-star ambition is a distribution and
    comprehension goal, not an engineering metric or a promise.

## When to escalate

- Need real invocation evidence: run a separate live-agent evaluation with a
  pinned model, host, and prompt protocol.
- Need a security certification: use a dedicated scanner and human review.
- Need exact vendor behavior: consult the vendor's documentation and verify
  with `--debug`-style tooling where available.
