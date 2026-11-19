# Prior art and star dynamics

**Search status:** bounded, public-documentation search conducted 2026-11-13.
Not exhaustive. "No direct evidence located" is not "never built".

## Adjacent tools

| Tool | Source | What it does | What it does not do |
|---|---|---|---|
| `agenteval-cli` | https://npmjs.com/package/agenteval-cli | Lints `CLAUDE.md`, `AGENTS.md`, Cursor rules; dead refs, bloat, contradictions, stale commands | Resolve a per-file effective context per harness |
| SkillMD | https://skillmd.com/ | Registry, parser, lint rules, security scanner, quality score, SARIF | Model host-specific composition |
| `skill-check` | https://www.npmjs.com/package/skill-check | Spec validation, HTML/JSON/SARIF reports, duplicate detection, security scan | Cross-harness divergence or drift gate |
| `rules-doctor` | https://wpnews.pro/news/your-claude-md-might-not-be-loading-i-built-a-check-up-for-that | Heuristic Claude Code import/shadowing/size check-up | Multiple harnesses, per-file snapshot |
| Microsoft APM | https://menuagentic.com/blogs/the-lockfile-arrived-for-the-prompt | Manifest, lockfile, content hashes, drift detection, CycloneDX/SPDX SBOM | Describe composition of prose + model + tools + permissions |
| `vacutest` | https://github.com/ (catalog record) | Detects vacuous/tautological tests without AST or execution | Agent instruction context |
| `testrot` | https://www.jxxy.net/ai/articles/testrot | Python AST detector for always-passing tests | Instruction files |
| `slopguard` | https://github.com/Chris-biu/slopguard | Catches hallucinated/typosquatted packages before install | Offline-only; needs registry data |
| `AGENTS.md` | https://agents.md/ | Open format, 60k+ repos, nested-file precedence FAQ | Tooling for cross-harness equality |

## The divergence evidence

The strongest single source is Augment Code's comparison of
`AGENTS.md` vs `CLAUDE.md` loading:

- Codex concatenates one file per directory from git root down.
- Claude Code concatenates `CLAUDE.md` / `CLAUDE.local.md` from root down.
- Zed takes the first match on a fixed nine-name candidate list and does not
  traverse the tree.
- Cascade scopes root-level `AGENTS.md` as always-on and nested files as `/**`
  glob rules.

Source: https://www.augmentcode.com/guides/agents-md-vs-claude-md

`prism` encodes these as *versioned models*, not emulators, and prints the
source URL and caveat with every resolution.

## Claim boundary

The defensible novelty claim is:

> No widely adopted, offline, vendor-neutral tool was located that computes the
> effective instruction context for a specific file across multiple harnesses,
> compares directives, and gates drift in CI.

It is **not** a claim that no linter, no lockfile, no security scanner, and no
live-agent evaluator exists.

## Star dynamics

Repositories above ~100k stars are dominated by low-comprehension-cost,
broad-relevance, immediately useful, demoable artifacts. Approximate,
time-dependent examples:

| Repository | Approx. stars | Category |
|---|---:|---|
| `freeCodeCamp/freeCodeCamp` | ~427k | Free coding education |
| `kamranahmedse/developer-roadmap` | ~351k | Career roadmap |
| `EbookFoundation/free-programming-books` | >300k | Curated resource list |
| `public-apis/public-apis` | >300k | Reference list |
| `awesome-selfhosted/awesome-selfhosted` | >220k | Curated list |
| `tensorflow/tensorflow` | >180k | ML framework |
| `microsoft/vscode` | >170k | Developer platform |
| `ohmyzsh/ohmyzsh` | >170k | Productivity tool |
| `jwasham/coding-interview-university` | ~117k | Study plan |

The plausible causal bundle is:

> low comprehension cost x broad relevance x immediate usefulness x visible demo
> x distribution channel x active maintenance x sharing loop.

Code quality alone is not a sufficient predictor. GitHub stars are also
manipulable; CMU-led work identified millions of suspected fake stars, so
popularity is a discovery signal, not a quality certificate.[^fakestars]

## Implication for `prism`

- One-sentence pitch and one-screenshot demo are first-class features.
- The README, CI snippet, and demo corpus matter as much as the resolver.
- The tool must be useful in five minutes without a model or an account.
- Success is measured in saved debugging time and reproducible regressions,
  not in a star counter.

[^fakestars]: Reported in https://news.qq.com/rain/a/20250102A05RXD00
