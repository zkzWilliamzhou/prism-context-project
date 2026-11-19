"""prism command line interface.

Exit codes: 0 clean / below threshold, 1 findings or snapshot drift, 2 usage or IO error.
No command writes to the repository unless it carries an explicit write flag.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from . import __version__
from .config import ALL_HARNESSES, Config, ConfigError, load_config
from .discovery import discover
from .harnesses import HARNESSES, all_divergences, resolve_all
from .model import Report
from .render import render, render_snapshot_diff
from .report import LIMITATIONS, build
from .rules_catalog import RULES_CATALOG
from .snapshot import (SNAPSHOT_NAME, build_snapshot, compare, load_snapshot,
                       write_snapshot)
from .util import is_within, norm_path, safe_write, sanitize

FORMATS = ("tty", "json", "markdown", "sarif")
_SEV_ORDER = {"error": 0, "warning": 1, "info": 2}

INIT_TEMPLATE = {
    "harnesses": list(ALL_HARNESSES),
    "ignore": ["docs/generated/**"],
    "max_tokens": 8000,
    "import_hops": 4,
    "contradiction_threshold": 0.7,
    "fail_on": "error",
    "max_targets": 2000,
    "enabled_rules": [],
    "disabled_rules": [],
}


class UsageError(Exception):
    pass


def _common(p: argparse.ArgumentParser, suppress: bool) -> None:
    sup = argparse.SUPPRESS if suppress else None
    p.add_argument("--format", choices=FORMATS, default=sup or "tty")
    p.add_argument("--no-color", action="store_true", default=sup or False)
    p.add_argument("--fail-on", choices=("error", "warning", "info", "never"), default=sup)
    p.add_argument("--why", action="store_true", default=sup or False)


def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="prism",
        description="See exactly what each coding agent sees - and where they disagree.",
        epilog="Modeled resolution, not a live-agent trace. Offline and read-only by default.",
    )
    p.add_argument("--version", action="version", version=f"prism {__version__}")
    p.add_argument("--root", default=".", help="repository root (default: cwd)")
    p.add_argument("--config", default=None, help="path to prism.json")
    _common(p, suppress=False)

    sub = p.add_subparsers(dest="command", required=True)

    r = sub.add_parser("resolve", help="show modeled effective context for a target file")
    r.add_argument("target", nargs="?", default=".")
    r.add_argument("--harness", default=None, help="comma-separated subset or 'all'")
    _common(r, suppress=True)

    df = sub.add_parser("diff", help="show where harnesses disagree for a target file")
    df.add_argument("target", nargs="?", default=".")
    df.add_argument("--harness", default=None)
    _common(df, suppress=True)

    a = sub.add_parser("audit", help="full structural, security and divergence audit")
    a.add_argument("target", nargs="?", default=".")
    a.add_argument("--harness", default=None)
    _common(a, suppress=True)

    s = sub.add_parser("snapshot", help="compute a deterministic context snapshot")
    s.add_argument("--write", action="store_true", help=f"write {SNAPSHOT_NAME}")
    _common(s, suppress=True)

    c = sub.add_parser("check", help="fail CI when effective contexts drifted")
    _common(c, suppress=True)

    i = sub.add_parser("init", help="print or write a starter prism.json")
    i.add_argument("--write", action="store_true")
    i.add_argument("--force", action="store_true")

    e = sub.add_parser("explain", help="explain a rule id")
    e.add_argument("rule", nargs="?", default=None)
    e.add_argument("--all", action="store_true")

    sub.add_parser("harnesses", help="list the modeled harness loaders")
    return p


def _cfg(root: Path, args: argparse.Namespace) -> Config:
    cfg = load_config(root, args.config)
    if getattr(args, "fail_on", None):
        cfg.fail_on = args.fail_on
    harness = getattr(args, "harness", None)
    if harness and harness != "all":
        wanted = [x.strip() for x in harness.split(",") if x.strip()]
        bad = [x for x in wanted if x not in ALL_HARNESSES]
        if bad:
            raise UsageError(f"unknown harness(es): {', '.join(bad)}")
        cfg.harnesses = wanted
    return cfg


def _color(args: argparse.Namespace, fmt: str) -> bool:
    return (fmt == "tty" and not getattr(args, "no_color", False)
            and sys.stdout.isatty() and os.environ.get("NO_COLOR") is None)


def _exit_for(report: Report, cfg: Config) -> int:
    if cfg.fail_on == "never":
        return 0
    threshold = _SEV_ORDER[cfg.fail_on]
    for f in report.findings:
        if _SEV_ORDER.get(f.get("severity", "info"), 2) <= threshold:
            return 1
    return 0


def _light_report(command: str, target: str, d, res, cfg: Config) -> Report:
    return Report(
        root=".", target=norm_path(target), command=command,
        sources=[s.to_dict() for s in d.sources],
        resolutions=[x.to_dict() for x in res],
        divergences=[x.to_dict() for x in all_divergences(res, cfg.contradiction_threshold)]
        if len(res) > 1 else [],
        limitations=list(LIMITATIONS),
    )


def _dispatch(args: argparse.Namespace, root: Path, cfg: Config) -> int:
    fmt = args.format
    color = _color(args, fmt)
    why = bool(getattr(args, "why", False))

    if args.command == "version":
        print(f"prism {__version__}")
        return 0

    if args.command == "harnesses":
        for name, h in HARNESSES.items():
            print(f"{name:<9} {h.summary}")
            print(f"{'':<9} source: {h.source}")
            print(f"{'':<9} caveat: {h.caveat}")
        return 0

    if args.command == "explain":
        if args.all or not args.rule:
            for rid, (title, why_txt, fix) in sorted(RULES_CATALOG.items()):
                print(f"{rid}  {title}\n    why: {why_txt}\n    fix: {fix}")
        else:
            rid = args.rule.upper()
            if rid not in RULES_CATALOG:
                raise UsageError(f"unknown rule {rid}")
            title, why_txt, fix = RULES_CATALOG[rid]
            print(f"{rid}  {title}\n\nwhy: {why_txt}\nfix: {fix}")
        return 0

    if args.command == "init":
        text = json.dumps(INIT_TEMPLATE, indent=2) + "\n"
        if args.write:
            path = root / "prism.json"
            if path.exists() and not args.force:
                raise UsageError(f"{path.name} already exists (use --force)")
            safe_write(path, root, text)
            print(f"wrote {sanitize(str(path))}")
        else:
            sys.stdout.write(text)
        return 0

    if args.command == "snapshot":
        doc = build_snapshot(root, cfg)
        if args.write:
            p = write_snapshot(root, doc)
            print(f"wrote {p.name}: {len(doc['targets'])} targets x {len(doc['harnesses'])} harnesses")
        else:
            sys.stdout.write(json.dumps(doc, indent=2, sort_keys=True) + "\n")
        return 0

    if args.command == "check":
        try:
            old = load_snapshot(root)
        except (OSError, ValueError) as exc:
            raise UsageError(f"cannot read {SNAPSHOT_NAME}: {exc}") from exc
        changes = compare(old, build_snapshot(root, cfg))
        sys.stdout.write(render_snapshot_diff(changes, "json" if fmt == "json" else "tty"))
        return 1 if changes else 0

    target = norm_path(getattr(args, "target", "."))
    if not is_within(root / target, root):
        raise UsageError("target path escapes the repository root")
    d = discover(root, cfg)
    res = resolve_all(root, target, d, cfg)

    if args.command in ("resolve", "diff"):
        rpt = _light_report(args.command, target, d, res, cfg)
        if args.command == "diff" and len(res) < 2:
            raise UsageError("diff needs at least two harnesses")
        sys.stdout.write(render(rpt, fmt, color, why))
        return 0

    if args.command == "audit":
        rpt = build(root, target, "audit", d, res, cfg)
        sys.stdout.write(render(rpt, fmt, color, why))
        return _exit_for(rpt, cfg)

    raise UsageError(f"unhandled command {args.command}")


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    root = Path(args.root).resolve()
    if not root.is_dir():
        print(f"prism: root is not a directory: {sanitize(str(root))}", file=sys.stderr)
        return 2
    try:
        cfg = _cfg(root, args)
        return _dispatch(args, root, cfg)
    except (ConfigError, UsageError, ValueError, OSError) as exc:
        print(f"prism: {sanitize(str(exc), 500)}", file=sys.stderr)
        return 2
