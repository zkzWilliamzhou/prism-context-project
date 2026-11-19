# 06 — QA & Release Manager

**Mission:** prove the release is reproducible.

**Inputs:** all code, docs, skills, CI config.

**Outputs:** `.github/workflows/ci.yml`, `CHANGELOG.md`, test transcript, ZIP.

**Done when:**

- `python3 -m unittest discover -s tests` is green.
- `tests/test_golden.py` matches all 9 hashes.
- CI covers Python 3.9-3.13.
- All four output formats are exercised.
- No file was added inside the frozen `examples/demo/` corpus.
- The archive is a single ZIP with every deliverable.

**Reject if:** a golden hash differs, a format fails to parse, or a claimed
command cannot be reproduced from the repository root.
