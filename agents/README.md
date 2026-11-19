# Specialized agent contracts

These are the role contracts used for the build. They are documentation, not
autonomous processes. Each agent owns one artifact type and hands a concrete
file to the strict manager.

| Agent | File | Owns |
|---|---|---|
| Boss / Manager | [00-boss.md](00-boss.md) | Scope, gates, rejection, release verdict |
| Product Griller | [01-product-griller.md](01-product-griller.md) | Deep thinking, self-grilling, decision log |
| Prior-Art Researcher | [02-prior-art-researcher.md](02-prior-art-researcher.md) | Evidence matrix, star dynamics |
| Architect | [03-architect.md](03-architect.md) | Module map, golden gate, extension points |
| Implementer | [04-implementer.md](04-implementer.md) | TDD, CLI, library, demo corpus |
| Security Reviewer | [05-security-reviewer.md](05-security-reviewer.md) | Threat model, hostile regressions |
| QA & Release Manager | [06-qa-release-manager.md](06-qa-release-manager.md) | Test suite, CI, packaging, ZIP |
| Docs & Skills | [07-docs-skills.md](07-docs-skills.md) | README, docs, skills, notices |

The full handoff diagram lives in [../docs/WORKFLOW.md](../docs/WORKFLOW.md).
