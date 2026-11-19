"""Assemble a deterministic, machine-readable report."""

from __future__ import annotations

from pathlib import Path

from .config import Config
from .discovery import Discovery
from .harnesses import all_divergences
from .model import Report, Resolution
from .rules import run_rules
from .util import norm_path

LIMITATIONS = [
    "Harness loaders are MODELS of documented behaviour, not traces from a live agent. "
    "Vendors do not publish stable algorithms and they change between releases.",
    "prism resolves instruction composition only. It does not predict what an LLM will do, "
    "does not measure skill invocation, and cannot see host system prompts, user history, or tool availability.",
    "Directive extraction is high-precision / low-recall. A clean result means no mechanically "
    "provable defect was found, not that the instructions are good.",
    "Token counts are a deterministic bytes/4 proxy, not tokenizer output.",
    "Secret and injection rules are pattern heuristics. They are not a security scan and can miss novel variants.",
    "Personal/global instruction files outside the repository are intentionally never read.",
    "No network access, no subprocess execution, no telemetry. Runs are reproducible offline.",
]


def build(root: Path, target: str, command: str, d: Discovery,
          resolutions: list[Resolution], cfg: Config) -> Report:
    findings = [f.to_dict() for f in run_rules(d, resolutions, cfg)]
    divs = all_divergences(resolutions, cfg.contradiction_threshold)
    counts = {"error": 0, "warning": 0, "info": 0}
    for f in findings:
        sev = f.get("severity", "info")
        counts[sev] = counts.get(sev, 0) + 1
    return Report(
        root=".", target=norm_path(target), command=command,
        sources=[s.to_dict() for s in d.sources],
        resolutions=[r.to_dict() for r in resolutions],
        findings=findings,
        divergences=[x.to_dict() for x in divs],
        counts=counts,
        limitations=list(LIMITATIONS),
    )
