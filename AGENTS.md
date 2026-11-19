# prism agent instructions

- Run `python3 -m unittest discover -s tests` before finishing any change.
- Run `python3 -m prism --root examples/demo audit src/app.py` after touching
  resolution, rules, or rendering.
- Run `python3 -m prism --root examples/demo snapshot` to confirm the frozen
  demo still resolves deterministically.
- Never add, remove, or edit files inside `examples/demo/` unless you also
  update `tests/golden/BASELINE.json` with an explicit justification.
- Never add a runtime dependency, network call, subprocess, eval, or pickle to
  `prism/`.
- Use `prism check` after editing any instruction file in this repository.
- Read `CONTEXT.md` before proposing an architecture change.
- Keep `SKILL.md` frontmatter descriptions specific: state what the skill does
  and when to use it.
- Prefer a regression test over a prose assurance.
