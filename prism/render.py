"""Deterministic renderers. Untrusted text is sanitized before any decoration."""

from __future__ import annotations

import json
from typing import Any

from .model import Report
from .registry import Renderer, RendererRegistry
from .rules_catalog import RULES_CATALOG
from .util import sanitize

_BAR = "─" * 68
_LEVEL = {"error": "error", "warning": "warning", "info": "note"}
_BADGE = {"error": "ERROR  ", "warning": "WARN   ", "info": "INFO   "}
_COLOR = {"error": "\x1b[31m", "warning": "\x1b[33m", "info": "\x1b[36m",
          "dim": "\x1b[2m", "bold": "\x1b[1m", "reset": "\x1b[0m"}


def _c(text: str, key: str, color: bool) -> str:
    if not color:
        return text
    return f"{_COLOR[key]}{text}{_COLOR['reset']}"


def _tty(r: Report, color: bool, why: bool = False) -> str:
    lines: list[str] = []
    head = f"prism {r.version} · {r.command} · target {sanitize(r.target)}"
    lines.append(_c("┌" + _BAR, "dim", color))
    lines.append("│ " + _c(head, "bold", color))
    c = r.counts
    lines.append(f"│ sources {len(r.sources)} · contexts {len(r.resolutions)} · "
                 f"findings {c.get('error', 0)} error / {c.get('warning', 0)} warning / "
                 f"{c.get('info', 0)} info")
    lines.append(_c("└" + _BAR, "dim", color))

    if r.resolutions:
        lines.append("")
        lines.append(_c("EFFECTIVE CONTEXT (modeled)", "bold", color))
        for res in r.resolutions:
            lines.append(f"  {res['harness']:<8} {res['tokens']:>6} tok  "
                         f"{len(res['directives'])} directives")
            for item in res["included"]:
                lines.append(f"    [{item['order']}] + {sanitize(item['path'], 200)}")
                if why:
                    lines.append(f"        {_c(sanitize(item['reason'], 120), 'dim', color)}")
            if why:
                for item in res["excluded"][:12]:
                    lines.append(f"        - {sanitize(item['path'], 200)}  "
                                 f"{_c(sanitize(item['reason'], 100), 'dim', color)}")
                if len(res["excluded"]) > 12:
                    lines.append(f"        … {len(res['excluded']) - 12} more excluded (use JSON for full)")
            note = res["notes"][0] if res.get("notes") else "modeled resolution"
            lines.append(f"    {_c(sanitize(note, 160), 'dim', color)}")

    if r.divergences:
        lines.append("")
        lines.append(_c("WHERE THE AGENTS DISAGREE", "bold", color))
        for dv in r.divergences:
            n = len(dv["only_left"]) + len(dv["only_right"])
            lines.append(f"  {dv['left']} vs {dv['right']}: {n} differing directives, "
                         f"{len(dv['contradictory'])} contradictory, {dv['shared']} shared")
            for x in (dv["only_left"][:2] + dv["only_right"][:2]):
                lines.append(f"    · {sanitize(x, 100)}")
            for x in dv["contradictory"][:2]:
                lines.append(f"    {_c('! ', 'error', color)}{sanitize(x, 140)}")

    if r.findings:
        lines.append("")
        lines.append(_c("FINDINGS", "bold", color))
        for f in r.findings:
            path = sanitize(f["path"], 200)
            loc = f"{path}:{f['line']}" if path and f["line"] else (path or "-")
            badge = _c(_BADGE[f["severity"]], f["severity"], color)
            lines.append(f"  {badge} {f['id']}  {f['title']}  {loc}")
            if f["evidence"]:
                lines.append(f"      {sanitize(f['evidence'], 200)}")
            if f["fix"]:
                lines.append(f"      fix: {_c(sanitize(f['fix'], 160), 'dim', color)}")
    else:
        lines.append("")
        lines.append(_c("  No mechanically provable findings.", "dim", color))

    if r.limitations:
        lines.append("")
        lines.append(_c("Limits: " + r.limitations[0], "dim", color))
    return "\n".join(lines) + "\n"


def _markdown(r: Report) -> str:
    out = [f"# prism {r.command} report", "", f"- target: `{r.target}`",
           f"- sources: {len(r.sources)}", f"- modeled contexts: {len(r.resolutions)}",
           f"- findings: {r.counts.get('error', 0)} error, "
           f"{r.counts.get('warning', 0)} warning, {r.counts.get('info', 0)} info", ""]
    if r.divergences:
        out += ["## Where the agents disagree", ""]
        for dv in r.divergences:
            out.append(f"**{dv['left']} vs {dv['right']}** — "
                       f"{len(dv['only_left']) + len(dv['only_right'])} differing, "
                       f"{len(dv['contradictory'])} contradictory, {dv['shared']} shared")
            for x in dv["only_left"][:3]:
                out.append(f"- only {dv['left']}: {sanitize(x, 160)}")
            for x in dv["only_right"][:3]:
                out.append(f"- only {dv['right']}: {sanitize(x, 160)}")
            for x in dv["contradictory"][:3]:
                out.append(f"- conflict: {sanitize(x, 200)}")
        out.append("")
    if r.findings:
        out += ["## Findings", "", "| ID | Severity | Location | Title | Evidence |",
                "|---|---|---|---|---|"]
        for f in r.findings:
            path = sanitize(f["path"], 200)
            loc = f"{path}:{f['line']}" if path and f["line"] else (path or "-")
            out.append(f"| {f['id']} | {f['severity']} | `{loc}` | {f['title']} | "
                       f"{sanitize(f['evidence'], 160).replace('|', '/')} |")
        out.append("")
    out += ["## Limitations", ""] + [f"- {x}" for x in r.limitations]
    return "\n".join(out) + "\n"


def _sarif(r: Report) -> str:
    rules = [{"id": rid, "name": rid, "shortDescription": {"text": title},
              "helpUri": "https://github.com/prism-context/prism#rules"}
             for rid, (title, _why, _fix) in sorted(RULES_CATALOG.items())]
    results = []
    for f in r.findings:
        loc: dict[str, Any] = {"artifactLocation": {"uri": sanitize(f["path"], 200) or "."}}
        if f["line"]:
            loc["region"] = {"startLine": max(1, f["line"])}
        results.append({
            "ruleId": f["id"],
            "level": _LEVEL.get(f["severity"], "note"),
            "message": {"text": sanitize(f"{f['title']}: {f['evidence']}", 500)},
            "locations": [{"physicalLocation": loc}],
        })
    doc = {
        "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
        "version": "2.1.0",
        "runs": [{"tool": {"driver": {"name": "prism", "version": r.version,
                                      "informationUri": "https://github.com/prism-context/prism",
                                      "rules": rules}},
                  "results": results}],
    }
    return json.dumps(doc, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def _json(r: Report) -> str:
    return json.dumps(r.to_dict(), indent=2, sort_keys=True,
                      ensure_ascii=False) + "\n"


RENDERERS = RendererRegistry([
    Renderer("tty", _tty),
    Renderer("json", _json),
    Renderer("markdown", _markdown),
    Renderer("sarif", _sarif),
])


def render(report: Report, fmt: str = "tty", color: bool = False,
           why: bool = False) -> str:
    try:
        return RENDERERS.render(report, fmt, color, why)
    except KeyError:
        # Preserved pre-refactor behaviour: unknown formats fall back to TTY.
        return _tty(report, color, why)


def render_snapshot_diff(changes: list[dict[str, Any]], fmt: str = "tty") -> str:
    if fmt == "json":
        return json.dumps({"changes": changes, "count": len(changes)},
                          indent=2, sort_keys=True) + "\n"
    if not changes:
        return "prism check: effective contexts unchanged.\n"
    out = [f"prism check: {len(changes)} effective-context change(s)", ""]
    for c in changes[:40]:
        out.append(f"  {sanitize(c['kind'], 12):<8} {sanitize(c['target'], 200)}  "
                   f"[{sanitize(c.get('harness', '-'), 20)}]")
    if len(changes) > 40:
        out.append(f"  … {len(changes) - 40} more")
    return "\n".join(out) + "\n"
