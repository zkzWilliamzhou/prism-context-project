# 05 — Security Reviewer

**Mission:** treat every instruction file as hostile input.

**Inputs:** implementation, demo corpus.

**Outputs:** `SECURITY.md`, `tests/test_hostile.py`, redaction fixes.

**Done when:**

- Path escape, symlink escape, ANSI/bidi injection, secret leakage, malformed
  UTF-8, empty repo, import cycles, and bounded reads are tested.
- A credential never appears in TTY, JSON, Markdown, or SARIF.
- The threat model states what the tool is **not**.
- No network or subprocess import exists in the package.

**Reject if:** a secret reaches any report, or a control exists only in prose.
