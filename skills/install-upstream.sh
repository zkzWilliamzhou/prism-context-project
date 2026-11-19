#!/usr/bin/env bash
# Install the real upstream skills when Node 18+ and network access are available.
# This script is documentation for the user; it is NOT executed by prism.
set -euo pipefail

echo "Review each upstream LICENSE before installing."
echo "Requires: Node.js 18+, npx, network access."

npx skills add https://github.com/anthropics/skills --skill template-skill
npx skills add https://github.com/obra/superpowers --skill brainstorming
npx skills add https://github.com/mattpocock/skills --skill grill-me
npx skills add https://github.com/mattpocock/skills --skill tdd
npx skills add https://github.com/mattpocock/skills --skill improve-codebase-architecture
npx skills add https://github.com/vercel-labs/skills --skill find-skills
npx skills add https://github.com/hardikpandya/stop-slop

echo "Done. Copy the installed folders into your agent's skills directory if needed."
