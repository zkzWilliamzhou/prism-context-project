# Demo corpus

`examples/demo/` is a deliberately broken, tiny repository. It is also the
frozen input for `tests/golden/BASELINE.json`: **do not add, remove, or edit
files inside `examples/demo/`** without regenerating and explicitly justifying
the golden hashes.

It contains:

- a root `AGENTS.md` and `CLAUDE.md` with contradictory indentation rules;
- a nested `src/AGENTS.md` that only some harnesses load;
- a `CLAUDE.md` `@import` into `docs/style.md`;
- a `.cursor/rules/base.mdc` with glob frontmatter;
- a `SKILL.md` with a weak description and a wildcard `allowed-tools`;
- a stale `pnpm obsolete-task` command;
- a real `src/app.py` target.

Run:

```bash
python3 -m prism --root examples/demo resolve src/app.py --why
python3 -m prism --root examples/demo audit src/app.py
python3 -m prism --root examples/demo diff src/app.py
```
