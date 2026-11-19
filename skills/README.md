# Skill bundle

This directory contains a local, attributed set of Agent Skills folders. Copy
any folder into your agent's skills directory (for example
`~/.claude/skills/<name>/`) to use it.

## Honest provenance

Direct `git clone` from GitHub returned HTTP 403 in the build environment.
These folders were reconstructed from public documentation, catalog previews,
and search records on 2026-11-13. They are **not byte-identical upstream
mirrors**. `install-upstream.sh` contains the commands to fetch the real repos
when network access is available, and `manifest.json` records every source.

| Folder | Upstream | Status |
|---|---|---|
| `anthropics-template-skill/` | `anthropics/skills` template | Reconstructed scaffold |
| `obra-brainstorming/` | `obra/superpowers` | Condensed reconstruction |
| `mattpocock-grill-me/` | `mattpocock/skills` | Frontmatter verbatim, body condensed |
| `mattpocock-tdd/` | `mattpocock/skills` | Condensed reconstruction |
| `mattpocock-improve-codebase-architecture/` | `mattpocock/skills` | Condensed reconstruction + project overlay |
| `vercel-find-skills/` | `vercel-labs/skills` | Condensed reconstruction |
| `stop-slop/` | `hardikpandya/stop-slop` | Condensed reconstruction |
| `deep-thinking-grilling/` | This repository | Original |
| `prism-context-audit/` | This repository | Original |

See `../THIRD_PARTY_NOTICES.md` and `../docs/SKILLS.md`.
