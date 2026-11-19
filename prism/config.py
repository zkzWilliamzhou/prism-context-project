"""Configuration loading with accumulated, explicit validation errors.

Unknown keys and wrong types are reported rather than silently ignored: a
misspelled threshold that quietly disables a check is a real CI hazard.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .util import is_within, safe_read

CONFIG_NAME = "prism.json"
ALL_HARNESSES = ("codex", "claude", "zed", "cascade")


class ConfigError(Exception):
    pass


@dataclass
class Config:
    harnesses: list[str] = field(default_factory=lambda: list(ALL_HARNESSES))
    ignore: list[str] = field(default_factory=list)
    max_tokens: int = 8000
    import_hops: int = 4
    contradiction_threshold: float = 0.70
    fail_on: str = "error"
    max_targets: int = 2000
    enabled_rules: list[str] = field(default_factory=list)  # empty == all
    disabled_rules: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


_KNOWN = {
    "harnesses": list,
    "ignore": list,
    "max_tokens": int,
    "import_hops": int,
    "contradiction_threshold": (int, float),
    "fail_on": str,
    "max_targets": int,
    "enabled_rules": list,
    "disabled_rules": list,
}
_BOUNDS = {
    "max_tokens": (1, 10_000_000),
    "import_hops": (0, 8),
    "contradiction_threshold": (0.0, 1.0),
    "max_targets": (1, 50_000),
}


def load_config(root: Path, explicit: str | None = None) -> Config:
    path = Path(explicit) if explicit else root / CONFIG_NAME
    if not path.is_absolute():
        path = root / path
    if not is_within(path, root):
        raise ConfigError("config path escapes the repository root")
    if not path.exists():
        return Config()
    try:
        raw = json.loads(safe_read(path, root))
    except (OSError, json.JSONDecodeError) as exc:
        raise ConfigError(f"cannot read config {path}: {exc}") from exc
    if not isinstance(raw, dict):
        raise ConfigError("config must be a JSON object")
    errors: list[str] = []
    for key in raw:
        if key not in _KNOWN:
            errors.append(f"unknown config key '{key}'")
    cfg = Config()
    for key, expected in _KNOWN.items():
        if key not in raw:
            continue
        val = raw[key]
        if not isinstance(val, expected) or (expected is int and isinstance(val, bool)):
            errors.append(f"config '{key}' has wrong type (expected {expected})")
            continue
        if key in _BOUNDS:
            lo, hi = _BOUNDS[key]
            if not (lo <= val <= hi):
                errors.append(f"config '{key}' must be within [{lo}, {hi}]")
                continue
        if key == "harnesses":
            bad = [x for x in val if x not in ALL_HARNESSES]
            if bad:
                errors.append(f"unknown harness(es): {', '.join(map(str, bad))}")
                continue
            if not val:
                errors.append("'harnesses' must not be empty")
                continue
        if key in ("ignore", "enabled_rules", "disabled_rules"):
            if any(not isinstance(x, str) for x in val):
                errors.append(f"config '{key}' must contain only strings")
                continue
        if key == "fail_on" and val not in ("error", "warning", "info", "never"):
            errors.append("'fail_on' must be error|warning|info|never")
            continue
        setattr(cfg, key, val)
    if errors:
        raise ConfigError("; ".join(errors))
    return cfg
