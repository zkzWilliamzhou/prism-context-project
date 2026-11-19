# Deep thinking, grilling, and the product decision

**Focal question:** What zero-dependency, offline, genuinely useful developer
tool solves an unowned pain and has a credible path to the 100k+ GitHub-star
tier?

**Decision owner:** the strict manager agent. **Horizon:** one build session,
with a maintainable 1.0 release. **Audience:** teams using more than one AI
coding agent on one repository.

## Constraints

| Kind | Constraint |
|---|---|
| Real | No runtime network, no API key, no external service, Python stdlib only |
| Real | Must work in CI and be deterministic across machines and cwd |
| Real | Must be useful without a live LLM |
| Assumed | Python 3.9+ is available |
| Negotiable | Number of harness models; output formats |
| Unknown | Exact proprietary loader behavior of each vendor |
| Prohibited | Claiming to predict model behavior; claiming novelty without a bounded prior-art check |

## Independent candidate generation

Generated before reading prior-art results. Labels follow the brainstorming
method: **idea**, **assumption**, **prediction**, **disconfirming evidence**.

| ID | Idea | Assumption | Prediction | What would kill it |
|---|---|---|---|---|
| I1 | Skill trigger test harness | Descriptions drive routing | Authors will write positive/negative cases | Existing eval tool already owns it |
| I2 | Instruction-debt linter | Duplication across config files is common | Teams want a consolidated report | Becomes "yet another style checker" |
| I3 | Local skill provenance/policy checker | Teams need hashes and allowlists | SBOM export is enough | APM already does this |
| I4 | Config migration normalizer | Formats are mappable | One canonical file is desirable | Mapping rules are contested |
| I5 | Vacuous-test detector | Agents write tests that cannot fail | CI wants a 2-second pre-gate | `vacutest` / `testrot` already exist |
| I6 | Hallucinated-package detector | Slopsquatting is real | Offline typo detection helps | `slopguard` already exists and needs a registry |
| I7 | Documentation drift checker | README commands go stale | Static command validation is enough | Generic link checkers cover it |
| I8 | Effective agent-context resolver | Harnesses load different files | A per-file diff is immediately useful | A vendor publishes a universal resolver |
| I9 | Cross-harness CI drift gate | Composition changes silently | Snapshot testing applies to prompts | Nobody has more than one agent |
| I10 | Agent-instruction visualizer | A picture explains divergence | Demo-ability drives adoption | It is a demo, not a daily tool |

**Preserved minority view:** I2 and I4 remained attractive to a docs-minded
reviewer even after rejection; they are recorded here rather than averaged away.

## Evidence check (after the independent round)

The bounded search found strong adjacent work:

- `agenteval-cli`, SkillMD, and `skill-check` lint instruction files and skill
  metadata.[^prior]
- `rules-doctor` statically simulates one vendor's rule-loading pipeline.[^prior]
- Microsoft APM pins agent context with hashes, lockfiles, and SBOM export.[^prior]
- `vacutest` / `testrot` detect tautological tests; `slopguard` catches
  hallucinated packages.[^prior]
- Public documentation establishes that Codex, Claude Code, Zed, and Cascade
  resolve the *same* repository differently.[^divergence]
- `AGENTS.md` alone is used by 60k+ open-source projects.[^agentsmd]

**Status:** `support-located` for the pain, `challenge-located` for I1-I7,
`search-incomplete` for the whole ecosystem. Absence from a bounded search is
not proof of novelty. A niche integrated resolver may exist; the credible claim
is **"no widely adopted per-file effective-context + drift gate located"**, not
"never built".

## Adversarial grilling

A reviewer who did not originate I8/I9 asked these questions. The manager
required an answer before implementation.

| # | Objection | Response / mitigation | Residual uncertainty |
|---|---|---|---|
| 1 | You cannot test an LLM without an LLM | Correct. `prism` reports modeled instruction composition, never invocation | Live behavior remains unmeasured |
| 2 | Simple keyword overlap is useless | Contradiction checks require equal head token, opposite polarity, overlap coefficient, and scope guard | Still high-precision/low-recall |
| 3 | This is another YAML linter | The product is the effective context and the drift gate; lint is the foundation | Adjacent tools may add this |
| 4 | Descriptions are only one routing signal | Resolvers model file loading only and say so in every report | Other signals are out of scope |
| 5 | Trigger tests are subjective | Not shipped. Snapshots pin composition, not judgments | Test cases remain a future option |
| 6 | The ecosystem is too immature | Core is generic: Markdown instruction files + JSON manifests | Early-market risk |
| 7 | No central schema | Unknown frontmatter keys warn, never hard-fail; user-defined config supported | Portability is best-effort |
| 8 | Vendors will absorb this | A vendor-neutral, offline CI gate still has a role | Platform risk remains |
| 9 | Stars do not prove pain | Success is defined as saved debugging time and reproducible regressions, not stars | Distribution risk |
| 10 | A green audit creates false confidence | Seven limitations ship with every report | Users may still over-trust |
| 11 | Four harness models will rot | Each model carries a version, source URL, and caveat; adapters are small and editable | Maintenance burden is real |
| 12 | Reading untrusted Markdown is dangerous | Bounded reads, containment, sanitization, redaction, no execution | Not a security scanner |

## Decision

**Build I8 + I9 as one product: `prism`.**

The combination is novel in the bounded search, fits the offline constraint,
and turns an invisible, embarrassing failure into a five-minute demo:

> "Here is what Codex saw for this file. Here is what Claude saw. They disagree.
> Here is the CI check that stops it from happening again."

Rejected: I1 (eval needs a model), I2/I4 (style/mapping disputes), I3 (APM),
I5/I6 (existing tools), I7 (too shallow), I10 (demo without a daily workflow).

## Success criteria (not stars)

1. A changed nested `AGENTS.md` fails `prism check` for the affected targets.
2. A reviewer can see which file, order, and reason produced a divergence.
3. A credential in an instruction file never appears in any output format.
4. Every CLI command and output format is byte-identical across the
   architecture refactor.
5. A newcomer understands the value from one screenshot and runs it in five
   minutes.

## Revisit triggers

- A vendor publishes a stable, complete loader specification.
- A widely adopted cross-harness resolver appears.
- Fewer than two harnesses matter to the target audience.
- Users treat a clean audit as proof of agent behavior.

## Method citation

> Kassis, T., Agarwal, V., He, Y., Patel, D., & Brueckner, A. M. (2026).
> *Scientific Agent Skills: A Library of Procedural Knowledge for Research
> Agents*. arXiv:2609.00065. https://doi.org/10.48550/arXiv:2609.00065

[^prior]: See [PRIOR_ART.md](PRIOR_ART.md).
[^divergence]: https://www.augmentcode.com/guides/agents-md-vs-claude-md
[^agentsmd]: https://agents.md/
