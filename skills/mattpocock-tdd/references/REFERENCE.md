# TDD reference (project original)

## Good test

```python
def test_shadowing_is_local_to_the_directory():
    # Known-good expectation: a nested AGENTS.md with no neighbouring
    # CLAUDE.md is not shadowed by a root-level CLAUDE.md.
    ...
```

It names a public behavior, uses an independent expectation, and survives an
internal rename.

## Bad test

```python
def test_internal_helper():
    assert _jaccard(a, b) == _jaccard(a, b)  # tautological
```

It recomputes the same value and can never disagree with the code.

## Mocking guidance

- Mock at a confirmed seam, never inside the module under test.
- Prefer a local fake over a network client.
- If a test needs `eval`, a socket, or a temp file outside the repo, the seam is
  wrong.

## Refactoring gate

Before changing structure, freeze observable output. In this project that is
`tests/golden/BASELINE.json`. After the refactor, every hash must still match.
