---
name: prism-context-audit
description: Use when auditing AI coding-agent instruction files (AGENTS.md, CLAUDE.md, skills, Cursor rules), resolving effective context for a file, comparing harnesses, or gating instruction drift in CI.
metadata:
  source: local
  license: MIT
  status: original
---

# prism Context Audit

`prism` is offline, read-only, and zero-dependency. It models what four
harnesses (`codex`, `claude`, `zed`, `cascade`) would load for a file.

## Commands

```bash
prism resolve src/app.py --why        # effective context, with reasons
prism diff src/app.py                 # where harnesses disagree
prism audit src/app.py                # full audit, CI exit codes
prism audit src/app.py --format sarif # GitHub Code Scanning
prism snapshot --write                # commit .prism.snapshot.json
prism check                           # fail on context drift
prism explain --all                   # every rule and remedy
prism harnesses                       # loader models and caveats
```

## Interpretation

- `included` files reach the modeled context; `excluded` files do not, with a
  reason.
- A divergence is a difference in directives, not proof of what an LLM will do.
- A finding is a mechanically provable defect with `file:line` evidence.
- A clean run means no provable defect was found, not that the instructions are
  good.
- Token counts are a bytes/4 proxy.
- Every report carries limitations. Read them.

## Before editing instruction files

1. Run `prism snapshot --write` and commit the snapshot.
2. Make the edit.
3. Run `prism check`. Investigate every changed target.
4. Run `prism audit` with `--fail-on error`.
5. Never claim loader models are exact vendor traces.

## Safety

`prism` never opens a socket, spawns a process, reads outside the repository,
or writes without `--write`. It redacts credential-shaped strings and strips
terminal control sequences from untrusted Markdown.
