# 105k-star strategy (ambition, not promise)

**Claim:** no one can guarantee 105,000 GitHub stars. Popularity is also
manipulable. This document is a distribution plan, not a forecast.

## Why this idea has a shot

The 100k+ tier rewards:

> low comprehension cost x broad relevance x immediate usefulness x visible
> demo x distribution channel x active maintenance x sharing loop.

`prism` was chosen to satisfy the first four immediately:

- **One sentence:** see what each coding agent sees.
- **Broad relevance:** 60k+ repositories already use `AGENTS.md`; teams
  increasingly use more than one agent.[^agents]
- **Immediate usefulness:** a five-minute demo on a broken repo produces a
  concrete "oh no" moment.
- **Visible demo:** the `resolve --why` table is a screenshot, not an abstract
  library.

## What stars do not measure

Code quality alone does not predict the top tier. Curated lists, courses, and
roadmaps can out-star frameworks. Fake-star research shows the metric can be
gamed.[^fake] Therefore the project's internal success metrics are:

1. Time saved debugging a rule that never loaded.
2. Number of reproducible divergences caught before merge.
3. CI adoption via `prism check`.
4. Five-minute time-to-first-value for a newcomer.

## Distribution plan

| Phase | Action | Artifact |
|---|---|---|
| Launch | One screenshot + 30-second demo | `README.md`, `examples/demo/` |
| Week 1 | CI recipes for GitHub Actions, GitLab, and pre-commit | `.github/workflows/ci.yml` |
| Week 2 | SARIF upload so findings appear in Code Scanning | `--format sarif` |
| Week 3 | Short write-up explaining the four incompatible loaders | `docs/PRIOR_ART.md` |
| Month 2 | Adapter contributions for more harnesses, each with a source URL | `harnesses.py` |
| Month 3 | Real-world corpus of anonymized divergence cases | Community contributions |
| Ongoing | Honest limitations, pinned loader models, fast issue response | `docs/LIMITATIONS.md` |

## Anti-goals

- No fake stars, no engagement bait, no "AI-powered" rebranding.
- No claim that a clean audit proves agent behavior.
- No runtime network, account, or API key.
- No feature that requires a specific vendor to succeed.

## Revisit trigger

If a vendor ships a universal, open, per-file effective-context resolver with a
CI gate, reposition `prism` as the vendor-neutral audit and snapshot layer, or
retire the overlapping part.

[^agents]: https://agents.md/
[^fake]: https://news.qq.com/rain/a/20250102A05RXD00
