"""Snapshot testing for agent context.

A snapshot pins the *composition* of instructions each harness would assemble
for each file, not just the bytes of the instruction files. That is the useful
unit: editing one nested AGENTS.md can silently change what an agent sees for
hundreds of files while leaving the file's own diff tiny.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from . import __version__
from .config import Config
from .discovery import Discovery, collect_targets, discover
from .harnesses import resolve
from .model import Resolution
from .util import safe_write, sha256_text

SNAPSHOT_NAME = ".prism.snapshot.json"
SCHEMA = 1


def fingerprint(res: Resolution, d: Discovery) -> str:
    """Canonical, absolute-path-free digest of an effective context."""
    hashes = {s.path: s.sha256 for s in d.sources}
    parts = [res.harness, res.target]
    for item in res.included:
        parts.append(f"{item.order}:{item.path}:{hashes.get(item.path, '')}")
    for dr in sorted(res.directives, key=lambda x: (x.source, x.line, x.text)):
        parts.append(f"{dr.source}:{dr.line}:{dr.polarity}:{dr.text}")
    return sha256_text("\n".join(parts))


def build_snapshot(root: Path, cfg: Config, d: Discovery | None = None) -> dict[str, Any]:
    root = Path(root).resolve()
    d = d or discover(root, cfg)
    targets: dict[str, dict[str, str]] = {}
    for t in collect_targets(root, cfg):
        targets[t] = {h: fingerprint(resolve(h, root, t, d, cfg), d)
                      for h in cfg.harnesses}
    return {"tool": "prism", "version": __version__, "schema": SCHEMA,
            "harnesses": list(cfg.harnesses), "targets": targets}


def load_snapshot(root: Path) -> dict[str, Any]:
    p = Path(root) / SNAPSHOT_NAME
    with p.open("r", encoding="utf-8") as fh:
        doc = json.load(fh)
    if not isinstance(doc, dict) or not isinstance(doc.get("targets"), dict):
        raise ValueError("snapshot has an invalid structure")
    return doc


def compare(old: dict[str, Any], new: dict[str, Any]) -> list[dict[str, Any]]:
    ot = old.get("targets", {})
    nt = new.get("targets", {})
    changes: list[dict[str, Any]] = []
    for t in sorted(set(ot) | set(nt)):
        if t not in ot:
            changes.append({"kind": "added", "target": t, "harness": "*"})
            continue
        if t not in nt:
            changes.append({"kind": "removed", "target": t, "harness": "*"})
            continue
        for h in sorted(set(ot[t]) | set(nt[t])):
            if ot[t].get(h) != nt[t].get(h):
                changes.append({
                    "kind": "changed", "target": t, "harness": h,
                    "old": ot[t].get(h, ""), "new": nt[t].get(h, ""),
                })
    return changes


def write_snapshot(root: Path, doc: dict[str, Any]) -> Path:
    p = Path(root) / SNAPSHOT_NAME
    return safe_write(p, Path(root),
                      json.dumps(doc, indent=2, sort_keys=True,
                                 ensure_ascii=False) + "\n")
