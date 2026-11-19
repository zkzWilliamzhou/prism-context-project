"""High-precision, low-recall directive extraction.

We do not attempt NLP. A directive is emitted only for list items or lines
carrying an explicit polarity marker. A contradiction requires the same head
token, opposite polarity, and a Jaccard overlap above a configurable
threshold. Anything ambiguous is left alone and counted as clean, exactly the
precision contract a linter should have: a false alarm costs more than a miss.
"""

from __future__ import annotations

import re
from functools import lru_cache
from typing import Iterable

from .model import Directive, Finding, Source
from .util import redact, sanitize

_POLARITY = re.compile(
    r"\b(always|never|must\s+not|must|do\s+not|don't|don’t|avoid|prefer|"
    r"should\s+not|should|required|forbidden|never\s+use|only\s+use)\b",
    re.IGNORECASE,
)
_BULLET = re.compile(r"^\s*(?:[-*+]\s+|\d+[.)]\s+|>\s+)")
_FENCE = re.compile(r"^\s*(```|~~~)")
_MD_LINK = re.compile(r"\[([^\]]*)\]\(([^)]*)\)")
_INLINE_CODE = re.compile(r"`[^`]*`")
_NONWORD = re.compile(r"[^a-z0-9]+")
_STOP = {
    "the", "and", "for", "with", "that", "this", "from", "are", "not", "you",
    "your", "any", "all", "when", "use", "using", "always", "never", "must",
    "should", "prefer", "avoid", "dont", "don", "only", "into", "before",
    "after", "make", "sure", "instead", "than", "then", "each", "every",
    "file", "files", "code", "repo", "project", "please", "also", "never",
    "do", "does", "is", "in", "of", "to", "a", "an", "it", "be", "as", "on",
    "or", "if", "at", "by", "we", "our", "they", "their",
}
_POS = {"always", "must", "should", "prefer", "required", "only use", "use"}
_NEG = {"never", "must not", "do not", "don't", "don’t", "avoid", "should not",
        "forbidden", "never use"}
_SCOPE_HINT = re.compile(r"\b(in production|on main|in ci|locally|for tests|in tests|"
                         r"at runtime|in staging|only when|except)\b", re.IGNORECASE)
_IMPORT_ONLY = re.compile(r"^@[A-Za-z0-9_./\-]+\s*$")


def _tokens(text: str) -> list[str]:
    t = _MD_LINK.sub(r"\1 \2", text)
    t = _INLINE_CODE.sub(" ", t)
    t = _NONWORD.sub(" ", t.lower())
    return [w for w in t.split() if len(w) >= 3 and w not in _STOP]


@lru_cache(maxsize=512)
def _extract_cached(text: str, source: str, harness: str) -> tuple[Directive, ...]:
    out: list[Directive] = []
    in_fence = False
    for lineno, line in enumerate(text.splitlines(), 1):
        if _FENCE.match(line):
            in_fence = not in_fence
            continue
        if in_fence or not line.strip() or line.lstrip().startswith("#"):
            continue
        bullet = bool(_BULLET.match(line))
        m = _POLARITY.search(line)
        if not bullet and not m:
            continue
        raw = _BULLET.sub("", line).strip() if bullet else line.strip()
        if len(raw) < 4 or _IMPORT_ONLY.match(raw):
            # A bare @import is loader metadata, not an instruction. Counting it
            # as a directive pollutes divergence reports with fake differences.
            continue
        pol = "neutral"
        if m:
            phrase = re.sub(r"\s+", " ", m.group(0).lower())
            pol = "negative" if phrase in _NEG else ("positive" if phrase in _POS else "neutral")
        toks = _tokens(redact(raw))
        if not toks:
            continue
        out.append(Directive(
            text=sanitize(raw, 240), line=lineno, polarity=pol,
            head=toks[0], key=tuple(sorted(set(toks))), source=source,
            harness=harness,
        ))
    return tuple(out)


def extract(text: str, source: str, harness: str = "") -> list[Directive]:
    """Public wrapper. Cached tuples are immutable; callers get a fresh list.

    `snapshot` resolves the same sources for hundreds of targets and four
    harnesses. Without this cache the identical file is re-tokenized thousands
    of times per run.
    """
    return list(_extract_cached(text, source, harness))


def _overlap(a: tuple[str, ...], b: tuple[str, ...]) -> float:
    """Overlap coefficient: intersection / smaller set.

    Jaccard punishes a rule that merely adds a qualifier ("never use tabs.
    always use spaces."), which produced a false negative on the single most
    common contradiction case. Overlap keeps precision via head-token equality
    and the scope-qualifier guard below.
    """
    sa, sb = set(a), set(b)
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / min(len(sa), len(sb))


def _jaccard(a: tuple[str, ...], b: tuple[str, ...]) -> float:
    """Kept for callers that want strict set similarity."""
    sa, sb = set(a), set(b)
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


def contradictions(directives: Iterable[Directive], threshold: float = 0.70) -> list[Finding]:
    items = [d for d in directives if d.polarity in ("positive", "negative")]
    out: list[Finding] = []
    seen: set[tuple[str, str]] = set()
    for i, a in enumerate(items):
        for b in items[i + 1:]:
            if a.polarity == b.polarity or a.head != b.head or a.source == b.source:
                continue
            score = _overlap(a.key, b.key)
            if score < threshold:
                continue
            # A scope qualifier on only one side usually means the two rules
            # are complementary ("never deploy on Fridays" vs "always deploy").
            if bool(_SCOPE_HINT.search(a.text)) != bool(_SCOPE_HINT.search(b.text)):
                continue
            pair = tuple(sorted((f"{a.source}:{a.line}", f"{b.source}:{b.line}")))
            if pair in seen:
                continue
            seen.add(pair)
            out.append(Finding(
                id="PF040", severity="warning", title="Contradictory directives in effective context",
                path=a.source, line=a.line,
                evidence=f"{a.source}:{a.line} {a.text!r}  <->  {b.source}:{b.line} {b.text!r}",
                why=f"Opposite polarity on the same subject (token overlap {score:.2f}). "
                    "Both rules reach the same agent context, so precedence is undefined by prose.",
                fix="Remove one rule, or qualify its scope explicitly (e.g. 'in CI' / 'in production').",
            ))
    return out


def duplicates(directives: Iterable[Directive]) -> list[Finding]:
    buckets: dict[tuple[str, ...], list[Directive]] = {}
    for d in directives:
        if d.polarity == "neutral" or len(d.key) < 2:
            continue
        buckets.setdefault(d.key, []).append(d)
    out: list[Finding] = []
    for key, group in sorted(buckets.items(), key=lambda kv: kv[0]):
        if len(group) < 2:
            continue
        places = ", ".join(f"{g.source}:{g.line}" for g in group[:5])
        out.append(Finding(
            id="PF050", severity="info", title="Duplicated directive costs context tokens",
            path=group[0].source, line=group[0].line,
            evidence=f"{places} — {group[0].text!r}",
            why="The same instruction appears in multiple sources that are loaded together; "
                "the duplicate consumes context budget without adding information.",
            fix="Keep the directive in one source of truth and delete the copies.",
        ))
    return out


def source_directives(sources: Iterable[Source], harness: str = "") -> list[Directive]:
    out: list[Directive] = []
    for s in sources:
        if s.error:
            continue
        out.extend(extract(s.text, s.path, harness))
    return out
