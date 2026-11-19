"""Test helpers: deterministic temp repos and in-process CLI capture."""

from __future__ import annotations

import io
import tempfile
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from prism.cli import main


def make_repo(files: dict[str, str]) -> tuple[Path, object]:
    tmp = tempfile.TemporaryDirectory(prefix="prism-test-")
    root = Path(tmp.name)
    for rel, content in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
    return root, tmp


def cli(*args: str) -> tuple[int, str, str]:
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        try:
            code = main(list(args))
        except SystemExit as exc:  # argparse --version/--help
            code = int(exc.code or 0)
    return code, out.getvalue(), err.getvalue()


BASE = {
    "AGENTS.md": "- Always use tabs for indentation.\n- Run `pnpm test` before commits.\n",
    "src/app.py": "def main():\n    return 1\n",
    "package.json": '{"scripts": {"test": "vitest run"}}\n',
}
