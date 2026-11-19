"""Discover agent-instruction files and expand @imports safely.

Discovery is bounded (file count, depth, bytes) and read-only. Every candidate
path is containment-checked before it is opened; a symlink or `../` that
resolves outside the repository is recorded as a finding and never followed.
"""

from __future__ import annotations

import fnmatch
import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path

from .config import Config
from .frontmatter import parse_frontmatter
from .model import Source
from .util import (
    MAX_DEPTH, MAX_FILES, MAX_TOTAL_BYTES, is_within, norm_path,
    rel, safe_read, sanitize, sha256_text, token_estimate,
)

PRUNE_DIRS = {
    ".git", ".hg", ".svn", "node_modules", ".venv", "venv", "__pycache__",
    ".pytest_cache", ".mypy_cache", ".ruff_cache", ".cache", ".next", ".nuxt",
    "dist", "build", "target", "site-packages", ".tox", "coverage",
}
MAX_TEXT_EXT = (".py", ".js", ".ts", ".tsx", ".jsx", ".go", ".rs", ".java",
               ".rb", ".sh", ".c", ".h", ".cpp", ".cs", ".php", ".swift",
               ".kt", ".md", ".mdc", ".json", ".yaml", ".yml", ".toml", ".txt", ".sql")
_AT_REF = re.compile(r"(?<![\w@`])@([A-Za-z0-9_./\-]+)")
_FENCE = re.compile(r"^\s*(```|~~~)")


def classify(relpath: str, name: str) -> str | None:
    """Return a stable source kind, or None if the file is not an instruction file."""
    p = norm_path(relpath)
    low = p.lower()
    n = name.lower()
    if n == "skill.md":
        return "skill"
    if n in ("agents.md", "agent.md"):
        return "agents_md"
    if n in ("claude.md", "claude.local.md"):
        return "claude_md"
    if n == "gemini.md":
        return "gemini_md"
    if n in (".rules", ".cursorrules", ".windsurfrules", ".clinerules"):
        return "legacy_rule"
    if low == ".github/copilot-instructions.md" or low.endswith(".instructions.md"):
        return "copilot_instruction"
    if low.startswith(".cursor/rules/") and n.endswith(".mdc"):
        return "cursor_rule"
    if low.startswith(".claude/rules/"):
        return "claude_rule"
    if low.startswith(".devin/rules/") or low.startswith(".windsurf/rules/"):
        return "devin_rule"
    if low.startswith(".kiro/steering/"):
        return "kiro_rule"
    if low.startswith(".junie/"):
        return "junie_rule"
    return None


def git_root(root: Path) -> Path:
    """Walk upward for a .git directory; fall back to the given root."""
    cur = Path(root).resolve()
    for parent in [cur, *cur.parents]:
        if (parent / ".git").exists():
            return parent
    return cur


def is_ignored(relpath: str, cfg: Config) -> bool:
    return any(fnmatch.fnmatch(relpath, pat) or fnmatch.fnmatch(relpath, pat + "/**")
               for pat in cfg.ignore)


def _walk(root: Path, cfg: Config) -> tuple[list[tuple[Path, str]], bool]:
    items: list[tuple[Path, str]] = []
    count, total, truncated = 0, 0, False
    for dirpath, dirnames, filenames in os.walk(str(root)):
        d = Path(dirpath)
        depth = len(d.relative_to(root).parts)
        if depth >= MAX_DEPTH:
            dirnames[:] = []
        dirnames[:] = sorted(x for x in dirnames
                             if x not in PRUNE_DIRS and not x.startswith(".git")
                             and not is_ignored(rel(d / x, root), cfg))
        for fname in sorted(filenames):
            if count >= MAX_FILES or total >= MAX_TOTAL_BYTES:
                truncated = True
                return items, truncated
            p = d / fname
            r = rel(p, root)
            if is_ignored(r, cfg):
                continue
            try:
                total += min(p.stat().st_size, MAX_TOTAL_BYTES)
            except OSError:
                continue
            count += 1
            items.append((p, r))
    return items, truncated


@dataclass
class ImportRef:
    origin: str
    line: int
    raw: str
    resolved: str = ""
    status: str = ""
    depth: int = 0


@dataclass
class Discovery:
    root: Path
    sources: list[Source] = field(default_factory=list)
    imports: list[ImportRef] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    truncated: bool = False
    package_scripts: dict[str, str] = field(default_factory=dict)


def _imports_from(text: str, origin: str) -> list[ImportRef]:
    out: list[ImportRef] = []
    in_fence = False
    for lineno, line in enumerate(text.splitlines(), 1):
        if _FENCE.match(line):
            in_fence = not in_fence
            continue
        for m in _AT_REF.finditer(line):
            raw = m.group(1)
            if raw.startswith("http"):
                continue  # remote refs are outside scope and never fetched
            out.append(ImportRef(origin=origin, line=lineno, raw=raw,
                                 status="in_code_fence" if in_fence else ""))
    return out


def _resolve_one(ref: ImportRef, root: Path) -> None:
    if ref.status == "in_code_fence":
        return
    cand = Path(ref.raw)
    if not cand.is_absolute():
        cand = root / Path(ref.origin).parent / cand
    if not is_within(cand, root):
        ref.status = "escape"
        return
    r = norm_path(rel(cand, root))
    if not cand.exists() or not cand.is_file():
        ref.status = "missing"
        return
    ref.resolved = r
    ref.status = "ok"


def _make_source(path: str, text: str, kind: str) -> Source:
    meta, _body, warns, _has = parse_frontmatter(text)
    s = Source(
        path=path, kind=kind, text=text, meta=meta, parse_warnings=warns,
        sha256=sha256_text(text), tokens=token_estimate(text),
        directory=str(Path(path).parent.as_posix()),
    )
    if s.directory == ".":
        s.directory = ""
    return s


def _expand_imports(d: Discovery, cfg: Config, root: Path) -> None:
    """Bounded BFS: expand @imports and load their contents as sources.

    A file already discovered is referenced but not duplicated. An origin we
    have already expanded is treated as a cycle rather than followed again.
    """
    known = {s.path for s in d.sources}
    visited: set[str] = set()
    frontier = [s for s in d.sources if s.kind in ("claude_md", "claude_rule")]
    for hop in range(cfg.import_hops):
        next_frontier: list[Source] = []
        for src in frontier:
            if src.path in visited:
                continue
            visited.add(src.path)
            for ref in _imports_from(src.text, src.path):
                ref.depth = hop + 1
                _resolve_one(ref, root)
                d.imports.append(ref)
                if ref.status != "ok":
                    continue
                if ref.resolved in visited:
                    ref.status = "circular"
                    continue
                if ref.resolved in known:
                    continue  # already a source; no content duplication
                p = root / ref.resolved
                try:
                    text = safe_read(p, root)
                except OSError as exc:
                    ref.status = "missing"
                    d.warnings.append(f"import {ref.resolved}: {sanitize(str(exc))}")
                    continue
                ns = _make_source(ref.resolved, text, "imported")
                d.sources.append(ns)
                known.add(ns.path)
                next_frontier.append(ns)
        if not next_frontier:
            break
        frontier = next_frontier
    # Anything resolved on the last allowed hop was loaded, but its own
    # @imports were deliberately not expanded. Report that boundary instead of
    # silently pretending the graph ended there.
    for ref in d.imports:
        if ref.status == "ok" and ref.depth >= cfg.import_hops:
            ref.status = "depth"
        elif ref.status == "ok" and ref.resolved not in known:
            ref.status = "missing"


def discover(root: Path, cfg: Config) -> Discovery:
    root = Path(root).resolve()
    d = Discovery(root=root)
    items, d.truncated = _walk(root, cfg)
    for p, r in items:
        kind = classify(r, p.name)
        if kind is None:
            continue
        if not is_within(p, root):
            d.warnings.append(f"skipped out-of-root path: {r}")
            continue
        try:
            text = safe_read(p, root)
        except OSError as exc:
            d.sources.append(Source(path=r, kind=kind, error=sanitize(str(exc)),
                                    directory=str(Path(r).parent.as_posix())))
            continue
        d.sources.append(_make_source(r, text, kind))
    _expand_imports(d, cfg, root)
    pkg = root / "package.json"
    if pkg.is_file():
        try:
            data = json.loads(safe_read(pkg, root))
            scripts = data.get("scripts", {}) if isinstance(data, dict) else {}
            if isinstance(scripts, dict):
                d.package_scripts = {str(k): str(v) for k, v in scripts.items()}
        except (OSError, ValueError):
            d.warnings.append("package.json could not be parsed; stale-command check skipped")
    return d


# The snapshot is a generated artefact *about* targets. Including it as a
# target makes `prism check` report drift on the very first run after writing.
GENERATED_TARGETS = {".prism.snapshot.json"}


def collect_targets(root: Path, cfg: Config) -> list[str]:
    """Bounded, deterministic list of source files to compute contexts for."""
    items, _ = _walk(root, cfg)
    out = [r for p, r in items
           if p.suffix.lower() in MAX_TEXT_EXT and r not in GENERATED_TARGETS
           ][: cfg.max_targets]
    return sorted(out)
