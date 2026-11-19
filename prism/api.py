"""Small public Python API. Import-safe: no side effects, no IO at import time."""

from __future__ import annotations

from pathlib import Path

from .config import Config, load_config
from .discovery import discover
from .harnesses import resolve_all
from .model import Report
from .report import build
from .snapshot import build_snapshot as _build_snapshot
from .util import norm_path


def audit(root: str | Path = ".", cfg: Config | None = None,
          target: str = ".") -> Report:
    root = Path(root).resolve()
    cfg = cfg or load_config(root)
    d = discover(root, cfg)
    res = resolve_all(root, norm_path(target), d, cfg)
    return build(root, norm_path(target), "audit", d, res, cfg)


def resolve(root: str | Path, target: str, cfg: Config | None = None):
    root = Path(root).resolve()
    cfg = cfg or load_config(root)
    d = discover(root, cfg)
    return resolve_all(root, norm_path(target), d, cfg)


def build_snapshot(root: str | Path = ".", cfg: Config | None = None) -> dict:
    root = Path(root).resolve()
    cfg = cfg or load_config(root)
    return _build_snapshot(root, cfg)
