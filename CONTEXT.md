# CONTEXT.md — domain glossary

Use these terms exactly in architecture discussions.

| Term | Meaning in this project |
|---|---|
| **Effective context** | The ordered set of instruction sources a modeled harness would load for one target file |
| **Harness** | A coding agent whose loader behavior is modeled: `codex`, `claude`, `zed`, `cascade` |
| **Resolution** | One harness's included/excluded sources, directives, token estimate, and caveats for one target |
| **Directive** | A high-precision extracted instruction with polarity, head token, and source line |
| **Divergence** | A difference in directives between two harness resolutions for the same target |
| **Finding** | A mechanically provable defect with a rule ID, severity, `file:line`, evidence, and fix |
| **Snapshot** | Per-target, per-harness fingerprints of effective context, used by `prism check` |
| **Seam** | A public boundary where behavior can be observed without reaching inside a module |
| **Deep module** | A small interface hiding a large implementation |
| **Deletion test** | Would removing this module concentrate complexity, or just move it? |
| **Golden gate** | SHA-256 hashes of CLI output frozen before a refactor, replayed after it |
| **Redaction** | Recursive replacement of credential-shaped strings before serialization |
| **Containment** | Every path resolves inside the scan root before it is read or written |
| **Modeled, not traced** | The loader is a documented approximation, not a live-agent trace |
