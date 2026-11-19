---
name: brainstorming
description: "You MUST use this before any creative work - creating features, building components, adding functionality, or modifying behavior. Explores user intent, requirements and design before implementation."
category: productivity-and-workflow
source_repo: obra/superpowers
source_path: skills/brainstorming/SKILL.md
source_url: https://github.com/obra/superpowers/blob/main/skills/brainstorming/SKILL.md
metadata:
  license: MIT (reported by catalogs)
  status: condensed-reconstruction
---

# Brainstorming Ideas Into Designs

Help turn ideas into fully formed designs and specs through natural
collaborative dialogue. Start by understanding the current project context,
then ask questions one at a time to refine the idea. Once you understand what
you are building, present the design and get user approval.

Do NOT invoke any implementation skill, write code, scaffold a project, or take
any implementation action until you have presented a design and the user has
approved it. This applies to EVERY project regardless of perceived simplicity.

## Anti-pattern: "This is too simple to need a design"

Every project goes through this process. A todo list, a single-function utility,
a config change: all of them. "Simple" projects are where unexamined
assumptions cause the most wasted work. The design can be short, but you MUST
present it and get approval.

## Checklist

1. Explore project context: check files, docs, recent commits.
2. Offer a visual companion just in time, not upfront, only when a question
   would genuinely be clearer shown than described.
3. Ask clarifying questions one at a time: purpose, constraints, success
   criteria.
4. Propose 2-3 approaches with trade-offs and a recommendation.
5. Present the design in sections scaled to complexity; get approval after
   each section.
6. Write a design doc (upstream suggests
   `docs/superpowers/specs/YYYY-MM-DD--design.md`) and commit it.
7. Spec self-review: placeholders, contradictions, ambiguity, scope.
8. Ask the user to review the written spec.
9. Transition to implementation via a writing-plans skill.

## Source note

Condensed from public documentation and catalog previews of
`obra/superpowers` on 2026-11-13. Not a byte-identical upstream mirror.
