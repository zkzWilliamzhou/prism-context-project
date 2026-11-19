"""Hardened, dependency-free helpers shared by every prism module.

Design rules (deliberate, load-bearing):
  * every read is bounded in bytes and in total volume;
  * every path is resolved and checked for containment before use;
  * every string that can reach a terminal is sanitized of control sequences;
  * no function here imports a network, subprocess, or eval facility.
"""

from __future__ import annotations

import hashlib
import os
import re
from pathlib import Path
from typing import Iterable

MAX_FILE_BYTES = 2_000_000
MAX_TOTAL_BYTES = 32_000_000
MAX_DEPTH = 12
MAX_FILES = 5_000
MAX_OUTPUT_CHARS = 400

# C0/C1 controls, DEL, and ANSI escape sequences. Untrusted Markdown is rendered
# to a terminal, so this is a real injection boundary, not cosmetic cleanup.
_ANSI = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]|\x1b\][^\x07\x1b]*(?:\x07|\x1b\\)")
_CONTROLS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]")
_BIDI = re.compile(r"[\u202a-\u202e\u2066-\u2069\u200b-\u200f\ufeff]")

# Defense in depth: instruction files are untrusted and are echoed into four
# different report formats. Redact before any string leaves the parser layer.
_SECRETISH = re.compile(
    r"(?:sk-|gh[pousr]_|xox[baprs]-|AKIA)[A-Za-z0-9_\-]{16,}"
    r"|-----BEGIN [A-Z ]*PRIVATE KEY-----"
    r"|(?:api[_-]?key|secret|password|token)\s*[:=]\s*[\"'][A-Za-z0-9_\-]{16,}[\"']",
    re.IGNORECASE,
)


def redact(text: object) -> str:
    """Replace credential-shaped substrings before they can reach a report."""
    return _SECRETISH.sub("[REDACTED]", "" if text is None else str(text))


def redact_obj(obj: object) -> object:
    """Recursively redact every string in a JSON-serialisable structure."""
    if isinstance(obj, str):
        return redact(obj)
    if isinstance(obj, dict):
        return {k: redact_obj(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [redact_obj(v) for v in obj]
    return obj


def sanitize(text: object, limit: int = MAX_OUTPUT_CHARS) -> str:
    """Return terminal-safe, single-line-ish text derived from untrusted input."""
    s = redact(text)
    s = _ANSI.sub("", s)
    s = _BIDI.sub("", s)
    s = _CONTROLS.sub(" ", s)
    s = s.replace("\r", " ").replace("\n", " ").replace("\t", " ")
    s = re.sub(r" {3,}", "  ", s).strip()
    if len(s) > limit:
        s = s[:limit] + "…"
    return s


def is_within(path: Path, root: Path) -> bool:
    """True iff `path` resolves to something inside `root` (symlinks included)."""
    try:
        rp = Path(os.path.realpath(str(path)))
        rr = Path(os.path.realpath(str(root)))
        return rp == rr or rr in rp.parents
    except (OSError, ValueError):
        return False


def safe_read(path: Path, root: Path | None = None) -> str:
    """Read a bounded text file, never following a path outside `root`.

    Raises OSError for unreadable / escaping / oversized files. Callers decide
    whether to turn that into a finding. Errors are never silently swallowed.
    """
    if root is not None and not is_within(path, root):
        raise OSError("path escapes repository root")
    p = Path(path)
    if p.is_symlink() and root is not None and not is_within(p, root):
        raise OSError("symlink escapes repository root")
    size = p.stat().st_size
    if size > MAX_FILE_BYTES:
        raise OSError("file exceeds size limit")
    with p.open("rb") as fh:
        raw = fh.read(MAX_FILE_BYTES + 1)
    if len(raw) > MAX_FILE_BYTES:
        raise OSError("file exceeds size limit")
    # `replace` is intentional: a single bad byte must not abort an entire audit.
    return raw.decode("utf-8", errors="replace")


def safe_write(path: Path, root: Path, text: str) -> Path:
    """Write only inside `root`, and never through a symlink.

    The two commands with write flags (`init`, `snapshot`) must not be able to
    clobber an arbitrary file via a crafted repository layout.
    """
    p = Path(path)
    if not is_within(p, root):
        raise OSError("write target escapes repository root")
    if p.is_symlink():
        raise OSError("refusing to write through a symlink")
    p.write_text(text, encoding="utf-8")
    return p


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()


def sha256_paths(paths: Iterable[Path], root: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    for p in sorted(paths, key=lambda x: rel(x, root)):
        try:
            out[rel(p, root)] = sha256_text(safe_read(p, root))
        except OSError:
            continue
    return out


def rel(path: Path, root: Path) -> str:
    try:
        return Path(path).resolve().relative_to(Path(root).resolve()).as_posix()
    except (ValueError, OSError):
        try:
            return Path(os.path.relpath(str(path), str(root))).as_posix()
        except (ValueError, OSError):
            return sanitize(str(path))


def token_estimate(text: str) -> int:
    """Documented, deterministic proxy for tokens: ceil(bytes/4).

    This is NOT a tokenizer. It is stable across runs and machines, which is what
    a CI budget check needs. The README states the limitation explicitly.
    """
    b = len(text.encode("utf-8", errors="replace"))
    return (b + 3) // 4


def norm_path(s: str) -> str:
    return s.replace("\\", "/").strip()
