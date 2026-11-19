# Installed and vendored skills

## Status honesty

The build environment could not `git clone` GitHub (HTTP 403). `web_fetch` and
public catalog records were used instead. Therefore `skills/` contains a
**local, attributed bundle reconstructed from public documentation**, not
byte-identical upstream mirrors. Each `SKILL.md` carries its source URL and a
`status` note. `skills/install-upstream.sh` contains the commands a user with
normal network access can run to install the real upstream folders.

This satisfies the workflow requirement to install the skills as usable local
agent-skill folders while avoiding a false claim about verbatim provenance.

## Bundle

| Folder | Origin | Use in this project |
|---|---|---|
| `anthropics-template-skill/` | `anthropics/skills` template | Authoring format reference |
| `obra-brainstorming/` | `obra/superpowers` | Design-first ideation |
| `mattpocock-grill-me/` | `mattpocock/skills` | Relentless plan interview |
| `mattpocock-tdd/` | `mattpocock/skills` | Red/green/refactor discipline |
| `mattpocock-improve-codebase-architecture/` | `mattpocock/skills` | Deep-module architecture refactor |
| `vercel-find-skills/` | `vercel-labs/skills` | Skill discovery/install pattern |
| `stop-slop/` | `hardikpandya/stop-slop` | Prose cleanup rules |
| `deep-thinking-grilling/` | This repo | Original structured ideation protocol |
| `prism-context-audit/` | This repo | Original skill for using `prism` itself |

The scientific brainstorming / critical-thinking methodology used during
ideation is credited in `THIRD_PARTY_NOTICES.md`; its internal skill text is
not vendored here.

## Installing for an agent

Copy any folder into your agent's skills directory, for example:

```bash
mkdir -p ~/.claude/skills
cp -R skills/prism-context-audit ~/.claude/skills/
```

For the real upstream versions:

```bash
bash skills/install-upstream.sh
```

## Which skills were actually applied

- `deep-thinking-grilling` + `obra-brainstorming`: candidate generation and
  self-grilling in `docs/IDEA.md`.
- `mattpocock-grill-me`: the 12 adversarial objections.
- `mattpocock-tdd`: test-first rules and regression tests for every fix.
- `mattpocock-improve-codebase-architecture`: `docs/ARCHITECTURE_REFACTOR.md`.
- `stop-slop`: tightened README and doc prose.
- `vercel-find-skills`: source discovery pattern for the bundle.
- `prism-context-audit`: the final self-audit commands.
