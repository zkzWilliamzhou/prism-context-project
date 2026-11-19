# prism

**See exactly what each coding agent sees — and where they disagree.**

`prism` is a zero-dependency, offline, read-only Python CLI that resolves the
*effective instruction context* for a file across AI coding agents, shows the
difference, and turns the result into a CI gate.

Most repositories now carry `AGENTS.md`, `CLAUDE.md`, `.cursor/rules/`, skills,
and nested overrides at the same time. Those files are not loaded the same way
by every harness. Codex concatenates root-down, Claude Code concatenates its own
memory files, Zed stops at the first match in a fixed candidate list, and
Cascade scopes nested files by directory. One checkout can hand four different
instruction sets to four agents, and none of them reports that it did.[^divergence]

Linters can tell you a file is valid. They cannot tell you which rules actually
reached the agent for `src/app.py`, which ones were silently shadowed, or that a
one-line edit to a nested `AGENTS.md` changed the context of 300 files. `prism`
answers those questions deterministically, without a model, a network call, or
an API key.

> **Star ambition:** this project is deliberately shaped for the 100k+ tier:
> one-sentence comprehension, a five-minute demo, immediate usefulness, and a
> low-friction CI story. Stars are not a quality metric and nobody can guarantee
> them. See [docs/STAR_STRATEGY.md](docs/STAR_STRATEGY.md) for the honest plan.

---

## 30-second demo

```bash
git clone https://github.com/zkzWilliamzhou/prism-context-project.git
cd prism
python3 -m prism --root examples/demo resolve src/app.py --why
```

```text
EFFECTIVE CONTEXT (modeled)
  codex        86 tok  7 directives
    [0] + AGENTS.md
    [1] + src/AGENTS.md
  claude       68 tok  6 directives
    [0] + CLAUDE.md
    [1] + docs/style.md
  zed          51 tok  4 directives
    [0] + AGENTS.md
  cascade      86 tok  7 directives
    [0] + AGENTS.md
    [1] + src/AGENTS.md

WHERE THE AGENTS DISAGREE
  codex vs claude: 12 differing directives, 0 contradictory, 0 shared
  claude vs zed:   10 differing directives, 0 contradictory, 0 shared
```

Then:

```bash
python3 -m prism audit src/app.py --format sarif
python3 -m prism snapshot --write     # commit .prism.snapshot.json
python3 -m prism check                # fails CI when effective context drifts
```

---

## Why this is different

Adjacent tools already exist, and they are good at what they do:

| Tool | What it does | What it does not do |
|---|---|---|
| `agenteval` | Lints `CLAUDE.md` / `AGENTS.md` for dead refs, bloat, contradictions | Resolve a per-file effective context across harnesses[^agenteval] |
| SkillMD / `skill-check` | Parse, lint, score and security-scan `SKILL.md` | Model host-specific instruction composition[^skillmd][^skillcheck] |
| `rules-doctor` | Diagnose Claude-specific imports and shadowing heuristically | Compare harnesses or gate drift for every file[^rulesdoctor] |
| Microsoft APM | Pin, hash and export agent context as an SBOM | Describe the *composition* of prose, model, tools and permissions[^apm] |

`prism` occupies the gap between **file validity** and **live-agent behavior**:
it computes a reproducible, per-file, per-harness instruction composition, then
uses that composition as a reviewable CI artifact. It does not pretend to
predict what an LLM will do.

## Features

- **Four documented harness models:** `codex`, `claude`, `zed`, `cascade`, each
  with a source URL, model version, and explicit caveat.
- **Effective context:** included/excluded files, ordering, reason, directives,
  and a deterministic token estimate for any target file.
- **Divergence report:** which directives are unique to a harness, which are
  shared, and which are contradictory.
- **16 audit rules:** frontmatter, imports, dead links, shadowing, secrets,
  prompt-injection phrasing, risky commands, stale package scripts, wildcard
  tool permissions, token budgets, contradictions, duplicates, and divergence.
- **Snapshot drift gate:** `snapshot` + `check` catch silent context changes in
  pull requests.
- **Four output formats:** human TTY, JSON, Markdown, SARIF 2.1.0.
- **Safe by construction:** no network, no subprocess, no telemetry, bounded
  reads, path containment, symlink refusal on writes, control-sequence
  sanitization, and recursive credential redaction.
- **Zero runtime dependencies:** Python 3.9+ standard library only.

## Install

```bash
pip install .
# or, without installing:
python3 -m prism --help
```

## Commands

| Command | Purpose |
|---|---|
| `prism resolve <file>` | Modeled effective context for one file |
| `prism diff <file>` | Where harnesses disagree |
| `prism audit [file]` | Full audit; exit 1 on findings at/above `--fail-on` |
| `prism snapshot --write` | Write `.prism.snapshot.json` |
| `prism check` | Fail if any effective context changed |
| `prism explain --all` | Show every rule and its remedy |
| `prism harnesses` | Show loader models and caveats |
| `prism init --write` | Write a starter `prism.json` |

Useful flags: `--format tty|json|markdown|sarif`, `--harness codex,claude`,
`--why`, `--no-color`, `--fail-on error|warning|info|never`, `--config`,
`--root`.

Exit codes: `0` clean / below threshold, `1` findings or drift, `2` usage/IO
error.

## CI

```yaml
- uses: actions/setup-python@v5
  with: { python-version: "3.11" }
- run: pip install .
- run: prism audit src/app.py --format sarif > prism.sarif
- run: prism check
```

See [.github/workflows/ci.yml](.github/workflows/ci.yml) for the full matrix.

## Configuration

Copy [prism.example.json](prism.example.json) to `prism.json`. Unknown keys and
wrong types are hard errors, not silent no-ops.

```json
{
  "harnesses": ["codex", "claude", "zed", "cascade"],
  "ignore": ["docs/generated/**"],
  "max_tokens": 8000,
  "import_hops": 4,
  "contradiction_threshold": 0.7,
  "fail_on": "error",
  "max_targets": 2000,
  "enabled_rules": [],
  "disabled_rules": []
}
```

## Honest limitations

Read [docs/LIMITATIONS.md](docs/LIMITATIONS.md) before trusting a green run.
The short version:

- Loader models reflect public documentation, not proprietary runtime traces.
  Vendors do not publish stable algorithms and they change between releases.
- A clean audit means no mechanically provable defect was found, not that the
  instructions are good.
- Token counts are a stable `bytes/4` proxy, not tokenizer output.
- Secret and injection checks are high-precision heuristics, not a security
  scanner.
- `prism` never reads personal/global instruction files outside the repository.

## Project map

| Path | Contents |
|---|---|
| `prism/` | The CLI and library |
| `tests/` | 82 unit, hostile-input, golden-gate and architecture tests |
| `tests/golden/BASELINE.json` | Byte-level behavior freeze from before the architecture refactor |
| `examples/demo/` | A tiny broken repo that reproduces four disagreeing agents |
| `docs/` | Ideation, prior art, plan, workflow, 10 review rounds, architecture, star strategy |
| `agents/` | Specialized agent contracts and the strict manager gate |
| `skills/` | Vendored/reconstructed GitHub skills plus two project-native skills |

## Credits

Ideation used a structured scientific brainstorming and critical-thinking
method; the method paper is cited in
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md). The vendored skill bundle is
documented in [skills/README.md](skills/README.md) and
[docs/SKILLS.md](docs/SKILLS.md).

## License

MIT. See [LICENSE](LICENSE).

---

[^divergence]: "AGENTS.md vs CLAUDE.md: Which Files Your Coding Agents Actually Read", Augment Code. https://www.augmentcode.com/guides/agents-md-vs-claude-md
[^agenteval]: `agenteval-cli`. https://npmjs.com/package/agenteval-cli
[^skillmd]: SkillMD. https://skillmd.com/
[^skillcheck]: `skill-check`. https://www.npmjs.com/package/skill-check
[^rulesdoctor]: "Your CLAUDE.md Might Not Be Loading — I Built a Check-Up for That". https://wpnews.pro/news/your-claude-md-might-not-be-loading-i-built-a-check-up-for-that
[^apm]: "The lockfile arrived for the prompt", Agentic AI Wiki. https://menuagentic.com/blogs/the-lockfile-arrived-for-the-prompt
