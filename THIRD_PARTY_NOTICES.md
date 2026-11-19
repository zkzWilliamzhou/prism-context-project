# Third-party notices

`prism` itself is MIT-licensed. The `skills/` directory contains a local,
attributed bundle of agent skills plus two project-native skills. Direct
`git clone` was unavailable in the build environment, so upstream files were
**reconstructed from public documentation and catalog records**, not mirrored
byte-for-byte. Each skill folder states its source URL and status. Before
redistributing a verbatim upstream copy, review the upstream LICENSE and pin a
commit.

| Skill | Upstream | Upstream license / status | Local status |
|---|---|---|---|
| Template Skill | `anthropics/skills` → `template/SKILL.md` | Repository skills are commonly Apache-2.0; document skills are source-available. Verify per skill. | Reconstructed scaffold |
| Brainstorming | `obra/superpowers` → `skills/brainstorming/SKILL.md` | MIT (reported by catalogs) | Condensed reconstruction |
| `grill-me`, `tdd`, `improve-codebase-architecture` | `mattpocock/skills` → `skills/...` | MIT (reported by catalogs) | Condensed reconstruction; `grill-me` frontmatter captured verbatim |
| `find-skills` | `vercel-labs/skills` → `skills/find-skills/SKILL.md` | Not verified | Condensed reconstruction from public catalog text |
| `stop-slop` | `hardikpandya/stop-slop` → `SKILL.md` | MIT | Condensed reconstruction; frontmatter and rules captured from public GitHub preview |
| `deep-thinking-grilling`, `prism-context-audit` | This repository | MIT | Original project skills |

## Method citation

Structured ideation and adversarial evidence review in this project used the
Scientific Agent Skills methodology:

> Kassis, T., Agarwal, V., He, Y., Patel, D., & Brueckner, A. M. (2026).
> *Scientific Agent Skills: A Library of Procedural Knowledge for Research
> Agents*. arXiv:2609.00065. https://doi.org/10.48550/arXiv:2609.00065

## Documentation sources

- Agent Skills format and progressive disclosure: https://agentskills.io/ and https://skill.md/
- `AGENTS.md`: https://agents.md/
- Cross-harness loading divergence: https://www.augmentcode.com/guides/agents-md-vs-claude-md
- Prior-art tools: `agenteval-cli`, SkillMD, `skill-check`, `rules-doctor`,
  `vacutest`, `slopguard`, Microsoft APM. URLs are listed in
  [docs/PRIOR_ART.md](docs/PRIOR_ART.md).

No source code from those projects was copied into `prism/`.
