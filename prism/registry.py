"""Small, dependency-free plug-in registries.

The point of the refactor is a boundary: adding a rule or an output format must
not require editing the orchestrator. Ordering is defined once here so every
renderer and every CI consumer sees findings in the same sequence.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable

from .context import ScanContext
from .model import Finding, Report

_SEV_ORDER = {"error": 0, "warning": 1, "info": 2}


@dataclass(frozen=True)
class Rule:
    name: str
    check: Callable[[ScanContext], list[Finding]]


class RuleRegistry:
    def __init__(self, rules: Iterable[Rule] = ()) -> None:
        self._rules: list[Rule] = list(rules)

    def register(self, rule: Rule) -> None:
        self._rules.append(rule)

    def __iter__(self):
        return iter(self._rules)

    def names(self) -> list[str]:
        return [r.name for r in self._rules]

    def run(self, ctx: ScanContext) -> list[Finding]:
        found: list[Finding] = []
        for rule in self._rules:
            found.extend(rule.check(ctx))
        return sorted(found, key=lambda x: (
            _SEV_ORDER.get(x.severity, 3), x.id, x.path, x.line, x.evidence,
        ))


@dataclass(frozen=True)
class Renderer:
    fmt: str
    render: Callable[..., str]


class RendererRegistry:
    def __init__(self, renderers: Iterable[Renderer] = ()) -> None:
        self._by_fmt = {r.fmt: r for r in renderers}

    def register(self, renderer: Renderer) -> None:
        self._by_fmt[renderer.fmt] = renderer

    def formats(self) -> list[str]:
        return sorted(self._by_fmt)

    def render(self, report: Report, fmt: str, color: bool, why: bool) -> str:
        entry = self._by_fmt.get(fmt)
        if entry is None:
            raise KeyError(f"unknown output format: {fmt}")
        # TTY is the only renderer with presentation options.
        if fmt == "tty":
            return entry.render(report, color, why)
        return entry.render(report)
