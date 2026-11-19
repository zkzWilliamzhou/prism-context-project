---
name: find-skills
description: This skill helps you discover and install skills from the open agent skills ecosystem. Use when the user asks for a capability you do not have, wants to find a skill, or is setting up a new machine or repository.
source_repo: vercel-labs/skills
source_path: skills/find-skills/SKILL.md
source_url: https://github.com/vercel-labs/skills/blob/main/skills/find-skills/SKILL.md
metadata:
  license: not verified
  status: condensed-reconstruction-from-public-catalog
---

# Find Skills

The Skills CLI (`npx skills`) is the package manager for the open Agent Skills
ecosystem. It lets an agent extend itself mid-task instead of stopping while a
human browses a directory.

## When to use

- The user asks "how do I do X" where X may have an existing skill.
- The user says "find a skill for X" or "is there a skill for X".
- The user wants tools, templates, or workflows for a specific domain.
- You are setting up a new machine or repo and want the skills it needs.
- You want to keep installed skills current.

## When not to use

- You already know the exact skill; use its catalog install command directly.
- You are authoring a skill rather than finding one.
- You need a security or maintenance review; the leaderboard ranks by
  popularity, not review.
- The environment has no Node.js; install manually from the raw `SKILL.md`.

## Commands

```bash
npx skills find [query]     # search by keyword
npx skills add <owner/repo> # install from GitHub
npx skills check            # check for updates
npx skills update           # update installed skills
```

Browse the ecosystem at https://skills.sh/. Before running a search, check the
leaderboard: a well-known skill may already exist for the domain.

## Step 1: understand the need

Identify the domain, the specific task, and whether it is common enough that a
skill likely exists. Then search. Always read the `SKILL.md` before installing;
skills are instructions that run with your permissions.

## Source note

Condensed from the public AgenticSkills catalog page for `find-skills` on
2026-11-13. Not a byte-identical upstream mirror.
