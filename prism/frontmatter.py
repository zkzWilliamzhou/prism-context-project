"""A deliberately small YAML-subset parser for SKILL.md / .mdc frontmatter.

Why not PyYAML: prism has a zero-dependency runtime promise. Why not `eval`
or a generic loader: these files are untrusted.

Supported syntax (and ONLY this):
    key: plain scalar | "quoted" | 'quoted' | [a, b] | true/false/int/null
    key:                      followed by an indented map or a `- item` list
    key: | / > / |- / >-      block scalar with a dedented indented body
    # comments outside quotes

Anything else produces a WARNING and is skipped. It never raises and never
guesses, because a silent misparse is worse than a visible limitation.
"""

from __future__ import annotations

import re
from typing import Any

_KEY = re.compile(r"^([A-Za-z0-9_.\-]+)\s*:\s*(.*)$")
_LIST_ITEM = re.compile(r"^-\s+(.*)$")
_BLOCK = {"|", "|-", "|+", ">", ">-", ">+"}


def _strip_comment(s: str) -> str:
    quote = ""
    for i, ch in enumerate(s):
        if quote:
            if ch == quote and (i == 0 or s[i - 1] != "\\"):
                quote = ""
        elif ch in "\"'":
            quote = ch
        elif ch == "#" and (i == 0 or s[i - 1].isspace()):
            return s[:i].rstrip()
    return s.rstrip()


def _unquote(s: str) -> str:
    if len(s) >= 2 and s[0] == s[-1] and s[0] in "\"'":
        inner = s[1:-1]
        if s[0] == '"':
            inner = inner.replace('\\"', '"').replace("\\n", "\n").replace("\\\\", "\\")
        else:
            inner = inner.replace("''", "'")
        return inner
    return s


def _scalar(s: str) -> Any:
    s = _strip_comment(s).strip()
    if s.startswith("[") and s.endswith("]"):
        inner = s[1:-1].strip()
        if not inner:
            return []
        parts, buf, quote = [], "", ""
        for ch in inner:
            if quote:
                buf += ch
                if ch == quote:
                    quote = ""
            elif ch in "\"'":
                quote = ch
                buf += ch
            elif ch == ",":
                parts.append(_unquote(buf.strip()))
                buf = ""
            else:
                buf += ch
        if buf.strip():
            parts.append(_unquote(buf.strip()))
        return parts
    if len(s) >= 2 and s[0] == s[-1] and s[0] in "\"'":
        return _unquote(s)
    low = s.lower()
    if low in ("true", "yes", "on"):
        return True
    if low in ("false", "no", "off"):
        return False
    if low in ("null", "none", "~", ""):
        return None
    if re.fullmatch(r"-?\d+", s):
        return int(s)
    return s


def _indent(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def _parse_block(lines: list[str], base: int, warnings: list[str]) -> dict[str, Any]:
    data: dict[str, Any] = {}
    i, n = 0, len(lines)
    while i < n:
        raw = lines[i].rstrip("\r")
        if not raw.strip() or raw.lstrip().startswith("#"):
            i += 1
            continue
        if _indent(raw) != 0:
            warnings.append(f"frontmatter line {base + i + 1}: unexpected indentation; skipped")
            i += 1
            continue
        m = _KEY.match(raw)
        if not m:
            warnings.append(f"frontmatter line {base + i + 1}: unsupported syntax; skipped")
            i += 1
            continue
        key, rest = m.group(1), _strip_comment(m.group(2)).strip()
        if key in data:
            warnings.append(f"frontmatter line {base + i + 1}: duplicate key '{key}'; last value wins")

        if rest in _BLOCK:
            j, collected = i + 1, []
            while j < n and (not lines[j].strip() or _indent(lines[j]) > 0):
                collected.append(lines[j])
                j += 1
            indents = [_indent(x) for x in collected if x.strip()]
            cut = min(indents) if indents else 1
            body = [x[cut:] if len(x) >= cut else "" for x in collected]
            data[key] = "\n".join(body) if rest.startswith("|") else " ".join(
                x.strip() for x in body if x.strip()
            )
            i = j
            continue

        if rest == "":
            j = i + 1
            collected = []
            while j < n and (not lines[j].strip() or _indent(lines[j]) > 0):
                collected.append(lines[j])
                j += 1
            if not collected:
                data[key] = None
                i = j
                continue
            indents = [_indent(x) for x in collected if x.strip()]
            cut = min(indents) if indents else 1
            sub = [x[cut:] if len(x) >= cut else "" for x in collected]
            nonblank = [x for x in sub if x.strip() and not x.lstrip().startswith("#")]
            if nonblank and all(_LIST_ITEM.match(x.strip()) for x in nonblank):
                data[key] = [_scalar(_LIST_ITEM.match(x.strip()).group(1)) for x in nonblank]
            else:
                data[key] = _parse_block(sub, base + i + 1, warnings)
            i = j
            continue

        data[key] = _scalar(rest)
        i += 1
    return data


def parse_frontmatter(text: str) -> tuple[dict[str, Any], str, list[str], bool]:
    """Return (metadata, body, warnings, has_frontmatter)."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, text, [], False
    end = None
    for idx in range(1, len(lines)):
        if lines[idx].strip() in ("---", "..."):
            end = idx
            break
    if end is None:
        return {}, text, ["frontmatter: opening '---' has no closing delimiter"], False
    fmlines = lines[1:end]
    body = "\n".join(lines[end + 1:])
    warnings: list[str] = []
    data = _parse_block(fmlines, 1, warnings)
    return data, body, warnings, True
