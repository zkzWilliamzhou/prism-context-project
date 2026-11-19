---
name: improve-codebase-architecture
description: Scan a codebase for deepening opportunities, present them as a visual HTML report, then grill through whichever one you pick.
disable-model-invocation: true
category: engineering-core
source_repo: mattpocock/skills
source_path: skills/engineering/improve-codebase-architecture/SKILL.md
source_url: https://github.com/mattpocock/skills/blob/main/skills/engineering/improve-codebase-architecture/SKILL.md
metadata:
  license: MIT (reported by catalogs)
  status: condensed-reconstruction-with-project-overlay
---

# Improve Codebase Architecture

Surface architectural friction and propose **deepening opportunities**:
refactors that turn shallow modules into deep ones. The aim is testability and
AI-navigability.

Use the shared vocabulary exactly: **module**, **interface**, **depth**,
**seam**, **adapter**, **leverage**, **locality**. Do not drift into
"component", "service", "API", or "boundary". The deletion test asks: would
removing this module concentrate complexity, or just move it?

## Process

1. **Scope before you scan — YAGNI.** Weight recently changed areas. If the
   user named a direction, take it. Otherwise inspect recent history for hot
   spots, then widen only if changes are scattered.
2. **Read the domain glossary and ADRs first.** `CONTEXT.md` names good seams;
   ADRs record decisions not to re-litigate.
3. **Explore organically.** Note where understanding one concept requires
   bouncing between many small modules, where modules are shallow, where pure
   functions were extracted only for testability while real bugs hide in how
   they are called, where coupled modules leak across seams, and what is hard to
   test through the current interface.
4. **Present candidates.** For each: cluster, why coupled, dependency
   category, and test impact. Do not propose interfaces yet.
5. **Design multiple interfaces.** At least three radically different options:
   minimal interface, maximum flexibility, optimized for the common caller,
   and ports-and-adapters where relevant. Compare them and recommend one.
6. **Create an RFC.** Use the template in
   [references/REFERENCE.md](references/REFERENCE.md).

## Project overlay: behavior freeze first

This project adds one non-negotiable gate. Before any structural edit:

1. Capture SHA-256 hashes of every CLI command and output format.
2. Store them in `tests/golden/BASELINE.json`.
3. Refactor behind registries and a shared `ScanContext`.
4. Rerun every hash. Any byte change means the refactor altered behavior.

Architecture work is not complete until the golden gate is green.
