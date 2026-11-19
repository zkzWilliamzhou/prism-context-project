"""One immutable-ish carrier for everything a rule or renderer needs.

Before the refactor, rule functions took 3-4 loosely related positional
arguments and `report.build` recomputed divergences independently. This context
makes the dependency graph explicit and gives new checks a stable surface.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .config import Config
from .discovery import Discovery
from .harnesses import all_divergences
from .model import Divergence, Resolution


@dataclass
class ScanContext:
    root: Path
    target: str
    discovery: Discovery
    resolutions: list[Resolution]
    cfg: Config

    @property
    def divergences(self) -> list[Divergence]:
        return all_divergences(self.resolutions, self.cfg.contradiction_threshold)
