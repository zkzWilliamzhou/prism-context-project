"""Plain data structures. No behaviour lives here, so JSON stays stable."""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any

from .util import redact_obj


@dataclass
class Source:
    path: str                 # repo-relative, posix
    kind: str                 # agents_md | claude_md | skill | cursor_rule | ...
    text: str = ""
    meta: dict[str, Any] = field(default_factory=dict)
    parse_warnings: list[str] = field(default_factory=list)
    sha256: str = ""
    tokens: int = 0
    error: str = ""
    directory: str = ""       # repo-relative parent directory, "" for root

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d.pop("text", None)   # never leak whole file bodies into reports
        return redact_obj(d)


@dataclass
class Directive:
    text: str
    line: int
    polarity: str             # positive | negative | neutral
    head: str                 # first content token after polarity words
    key: tuple[str, ...]      # sorted normalized content tokens
    source: str
    harness: str = ""


@dataclass
class Included:
    path: str
    order: int
    reason: str


@dataclass
class Excluded:
    path: str
    reason: str


@dataclass
class Resolution:
    harness: str
    target: str
    included: list[Included] = field(default_factory=list)
    excluded: list[Excluded] = field(default_factory=list)
    directives: list[Directive] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    tokens: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "harness": self.harness,
            "target": self.target,
            "included": [asdict(x) for x in self.included],
            "excluded": [asdict(x) for x in self.excluded],
            "directives": [asdict(x) for x in self.directives],
            "notes": list(self.notes),
            "tokens": self.tokens,
        }


@dataclass
class Finding:
    id: str
    severity: str             # error | warning | info
    title: str
    path: str = ""
    line: int = 0
    evidence: str = ""
    why: str = ""
    fix: str = ""
    harness: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Divergence:
    left: str
    right: str
    only_left: list[str] = field(default_factory=list)
    only_right: list[str] = field(default_factory=list)
    contradictory: list[str] = field(default_factory=list)
    shared: int = 0

    def to_dict(self) -> dict[str, Any]:
        return redact_obj(asdict(self))


@dataclass
class Report:
    tool: str = "prism"
    version: str = "1.0.0"
    root: str = ""
    target: str = ""
    command: str = ""
    sources: list[dict[str, Any]] = field(default_factory=list)
    resolutions: list[dict[str, Any]] = field(default_factory=list)
    findings: list[dict[str, Any]] = field(default_factory=list)
    divergences: list[dict[str, Any]] = field(default_factory=list)
    counts: dict[str, int] = field(default_factory=dict)
    limitations: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return redact_obj(asdict(self))
