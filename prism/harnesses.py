"""Versioned, documented models of how four harnesses assemble instruction context.

CRITICAL HONESTY BOUNDARY
------------------------
These are MODELS of publicly documented loading behaviour, not emulators of
proprietaries runtimes. Vendors do not publish a stable, complete algorithm
and it changes between releases. prism therefore:

  * labels every result "modeled", never "exactly what the agent saw";
  * ships the source URL, model version, and caveat with every resolution;
  * keeps each adapter small and editable so a team can correct it locally;
  * never claims to predict model behaviour, only document composition.

Source for the divergence problem and the three incompatible resolution
models: https://www.augmentcode.com/guides/agents-md-vs-claude-md
AGENTS.md precedence FAQ: https://agents.md/
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from .config import Config
from .directives import _overlap, extract
from .discovery import Discovery
from .model import Directive, Divergence, Excluded, Included, Resolution, Source
from .util import norm_path, sanitize

MODEL_VERSION = "2026-11-01"


@dataclass(frozen=True)
class Harness:
    name: str
    source: str
    summary: str
    caveat: str
    resolver: Callable[..., Resolution]


def _chain(root: Path, target: str) -> list[str]:
    """Directory chain from the scan root down to the target's directory.

    prism deliberately treats the scan root as the model's git root: walking
    above it would require reading files the user did not put in scope.
    """
    t = norm_path(target).lstrip("/")
    parts = [p for p in Path(t).parent.parts if p not in ("", ".")]
    out = [""]
    cur = ""
    for p in parts:
        cur = f"{cur}/{p}" if cur else p
        out.append(cur)
    return out


def _by_dir(sources: list[Source]) -> dict[str, list[Source]]:
    out: dict[str, list[Source]] = {}
    for s in sources:
        out.setdefault(norm_path(s.directory).rstrip("/"), []).append(s)
    return out


def _name(s: Source) -> str:
    return Path(s.path).name.lower()


def _finish(name: str, target: str, inc: list[Included], exc: list[Excluded],
            d: Discovery, notes: list[str]) -> Resolution:
    lookup = {s.path: s for s in d.sources}
    directives: list[Directive] = []
    tokens = 0
    for item in inc:
        s = lookup.get(item.path)
        if s is None or s.error:
            continue
        directives.extend(extract(s.text, s.path, name))
        tokens += s.tokens
    r = Resolution(harness=name, target=norm_path(target), included=inc,
                   excluded=exc, directives=directives, notes=notes, tokens=tokens)
    return r


def _notes(name: str) -> list[str]:
    h = HARNESSES[name]
    return [
        f"model={MODEL_VERSION}; source={h.source}",
        f"strategy: {h.summary}",
        f"caveat: {h.caveat}",
        "This is a modeled resolution, not a trace from a live agent run.",
    ]


# ---------------------------------------------------------------------------
# Codex: root -> cwd concatenation, at most one instruction file per directory.
# ---------------------------------------------------------------------------
def _codex(root: Path, target: str, d: Discovery, cfg: Config) -> Resolution:
    chain = _chain(root, target)
    bydir = _by_dir(d.sources)
    priority = ["agents.override.md", "agents.md", "agent.md"]
    inc: list[Included] = []
    exc: list[Excluded] = []
    for directory in chain:
        candidates = [s for s in bydir.get(directory, [])
                      if s.kind in ("agents_md", "legacy_rule") and _name(s) in priority]
        candidates.sort(key=lambda s: priority.index(_name(s)))
        if candidates:
            inc.append(Included(candidates[0].path, len(inc),
                                f"selected in {directory or '/'}; priority order " + " > ".join(priority)))
            for s in candidates[1:]:
                exc.append(Excluded(s.path, "same directory contributes at most one file"))
        for s in bydir.get(directory, []):
            if s not in candidates and s.kind in ("claude_md", "gemini_md"):
                exc.append(Excluded(s.path, "not part of the Codex instruction chain in this model"))
    for s in d.sources:
        if norm_path(s.directory) not in chain and s.kind in ("agents_md", "claude_md"):
            exc.append(Excluded(s.path, "outside the root-to-working-directory chain; not loaded"))
    return _finish("codex", target, inc, exc, d, _notes("codex"))


# ---------------------------------------------------------------------------
# Claude Code: CLAUDE.md + CLAUDE.local.md per ancestor directory, concatenated.
# ---------------------------------------------------------------------------
def _claude(root: Path, target: str, d: Discovery, cfg: Config) -> Resolution:
    chain = _chain(root, target)
    bydir = _by_dir(d.sources)
    inc: list[Included] = []
    exc: list[Excluded] = []
    for directory in chain:
        group = [s for s in bydir.get(directory, [])
                 if s.kind == "claude_md" and _name(s) in ("claude.md", "claude.local.md")]
        main = [s for s in group if _name(s) == "claude.md"]
        local = [s for s in group if _name(s) == "claude.local.md"]
        for s in main + local:
            inc.append(Included(s.path, len(inc),
                                f"ancestor memory loaded from {directory or '/'}"))
        for s in bydir.get(directory, []):
            # Shadowing is a *local* phenomenon. A nested AGENTS.md with no
            # neighbouring CLAUDE.md is not shadowed by a root-level one.
            if s.kind == "agents_md" and group:
                exc.append(Excluded(s.path, "AGENTS.md is shadowed when CLAUDE.md exists in the same directory"))
    for s in d.sources:
        if norm_path(s.directory) not in chain and s.kind in ("claude_md", "agents_md"):
            exc.append(Excluded(s.path, "below the working directory; loaded lazily on file read"))
    # @import expansion: only refs explicitly resolved by discovery are included.
    seen = {i.path for i in inc}
    for ref in d.imports:
        # "depth" means resolved-and-loaded but not expanded further; its
        # content still belongs in the effective context.
        if ref.status not in ("ok", "depth") or not ref.resolved:
            continue
        if ref.origin in seen and ref.resolved not in seen:
            inc.append(Included(ref.resolved, len(inc),
                                f"@import from {ref.origin}:{ref.line} (depth {ref.depth})"))
            seen.add(ref.resolved)
    return _finish("claude", target, inc, exc, d, _notes("claude"))


# ---------------------------------------------------------------------------
# Zed: first match on a fixed ordered candidate list, no tree traversal.
# ---------------------------------------------------------------------------
_ZED_ORDER = [
    ".rules", ".cursorrules", ".windsurfrules", ".clinerules",
    ".github/copilot-instructions.md", "AGENT.md", "AGENTS.md",
    "CLAUDE.md", "GEMINI.md",
]


def _zed(root: Path, target: str, d: Discovery, cfg: Config) -> Resolution:
    present = {norm_path(s.path): s for s in d.sources}
    inc: list[Included] = []
    exc: list[Excluded] = []
    chosen = ""
    for cand in _ZED_ORDER:
        src = present.get(cand) or present.get(cand.lower())
        if src is not None:
            chosen = src.path
            inc.append(Included(src.path, 0,
                                f"first match in Zed's fixed candidate list (position {_ZED_ORDER.index(cand) + 1})"))
            break
    for s in d.sources:
        if s.path == chosen:
            continue
        if s.directory:
            exc.append(Excluded(s.path, "Zed does not traverse the directory tree in this model"))
        else:
            exc.append(Excluded(s.path, "candidate list stops at the first match" if chosen
                                else "not in Zed's fixed candidate list"))
    notes = _notes("zed") + [
        "Personal instructions (~/.config/zed/AGENTS.md) live outside the repository "
        "and are intentionally never read by prism."
    ]
    return _finish("zed", target, inc, exc, d, notes)


# ---------------------------------------------------------------------------
# Cascade / Devin Desktop: root-level always-on, nested files directory-scoped.
# ---------------------------------------------------------------------------
def _cascade(root: Path, target: str, d: Discovery, cfg: Config) -> Resolution:
    chain = _chain(root, target)
    t = norm_path(target).lstrip("/")
    inc: list[Included] = []
    exc: list[Excluded] = []
    for s in d.sources:
        if s.kind == "agents_md":
            scope = norm_path(s.directory).rstrip("/")
            matches = scope == "" or t.startswith(scope + "/")
            if matches:
                inc.append(Included(s.path, len(inc),
                                    "root-level: always-on" if scope == ""
                                    else f"directory-scoped /** matches {scope}"))
            else:
                exc.append(Excluded(s.path, f"directory-scoped /** ({scope or '/'}) does not match target"))
        elif s.kind in ("devin_rule", "claude_rule", "cursor_rule", "copilot_instruction"):
            globs = s.meta.get("globs") or s.meta.get("applyTo") or []
            if isinstance(globs, str):
                globs = [g.strip() for g in globs.split(",") if g.strip()]
            if not isinstance(globs, list):
                globs = []
            import fnmatch
            matched = [g for g in map(str, globs) if fnmatch.fnmatch(t, g) or fnmatch.fnmatch(t, g + "/**")]
            if matched or not globs:
                inc.append(Included(s.path, len(inc),
                                    f"rule scoped by glob {matched or ['(unscoped)']}"))
            else:
                exc.append(Excluded(s.path, "frontmatter globs do not match target"))
    for s in d.sources:
        if s.kind == "claude_md":
            exc.append(Excluded(s.path, "CLAUDE.md is not a Cascade instruction source in this model"))
    return _finish("cascade", target, inc, exc, d, _notes("cascade"))


HARNESSES: dict[str, Harness] = {
    "codex": Harness(
        "codex", "https://www.augmentcode.com/guides/agents-md-vs-claude-md",
        "concatenate one instruction file per directory, git root down to the working directory",
        "at most one file per directory; exact candidate names vary by Codex version",
        _codex,
    ),
    "claude": Harness(
        "claude", "https://www.augmentcode.com/guides/agents-md-vs-claude-md",
        "concatenate CLAUDE.md then CLAUDE.local.md from the root down to the working directory",
        "Anthropic does not publish the loader; @import depth and shadowing are inferred",
        _claude,
    ),
    "zed": Harness(
        "zed", "https://www.augmentcode.com/guides/agents-md-vs-claude-md",
        "first match on a fixed nine-name candidate list, no directory traversal",
        "verified against Zed 1.18.1 documentation; the ordered list may change",
        _zed,
    ),
    "cascade": Harness(
        "cascade", "https://www.augmentcode.com/guides/agents-md-vs-claude-md",
        "case-insensitive AGENTS.md; root-level always-on, nested files scoped by /** ",
        "Cascade also feeds .devin/rules and legacy .windsurf/rules through the same engine",
        _cascade,
    ),
}


def resolve(name: str, root: Path, target: str, d: Discovery, cfg: Config) -> Resolution:
    if name not in HARNESSES:
        raise KeyError(f"unknown harness: {name}")
    return HARNESSES[name].resolver(root, norm_path(target), d, cfg)


def resolve_all(root: Path, target: str, d: Discovery, cfg: Config) -> list[Resolution]:
    return [resolve(h, root, target, d, cfg) for h in cfg.harnesses]


def _signature(d: Directive) -> str:
    return sanitize(d.text, 200).lower()


def divergence(a: Resolution, b: Resolution, threshold: float = 0.70) -> Divergence:
    sa = {_signature(x) for x in a.directives}
    sb = {_signature(x) for x in b.directives}
    contra: list[str] = []
    for x in a.directives:
        if x.polarity == "neutral":
            continue
        for y in b.directives:
            if y.polarity == "neutral" or x.polarity == y.polarity or x.head != y.head:
                continue
            if _overlap(x.key, y.key) >= threshold:
                msg = (f"{a.harness}: {x.source}:{x.line} {x.text!r}  <->  "
                       f"{b.harness}: {y.source}:{y.line} {y.text!r}")
                if msg not in contra:
                    contra.append(msg)
    return Divergence(
        left=a.harness, right=b.harness,
        only_left=sorted(sa - sb), only_right=sorted(sb - sa),
        contradictory=sorted(contra), shared=len(sa & sb),
    )


def all_divergences(resolutions: list[Resolution], threshold: float = 0.70) -> list[Divergence]:
    out: list[Divergence] = []
    for i, a in enumerate(resolutions):
        for b in resolutions[i + 1:]:
            out.append(divergence(a, b, threshold))
    return out
