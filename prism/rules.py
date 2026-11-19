"""Deterministic audit rules, registered as independent checks.

Precision contract: every rule must be justifiable from the source text in two
lines, must cite file:line, and must never echo a secret. Anything we cannot
classify is counted as clean. Rules are heuristics, not security guarantees.

The executable checks live here; their metadata lives in `rules_catalog.py`;
their shared inputs live in `ScanContext`; their ordering lives in
`RuleRegistry`. Adding a rule is a registration, not an edit to an orchestrator.
"""

from __future__ import annotations

import fnmatch
import re
from pathlib import Path

from .config import Config
from .context import ScanContext
from .directives import contradictions, duplicates
from .discovery import Discovery
from .model import Finding, Resolution
from .registry import Rule, RuleRegistry
from .rules_catalog import RULES_CATALOG  # re-exported for render/cli compatibility
from .util import is_within, sanitize

__all__ = ["RULES_CATALOG", "RULES", "run_rules", "rule_sources",
           "rule_imports", "rule_contexts"]

_SECRET_PATTERNS = [
    ("private_key", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |PGP )?PRIVATE KEY-----")),
    ("aws_access_key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("github_token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{36,}\b")),
    ("openai_key", re.compile(r"\bsk-[A-Za-z0-9]{32,}\b")),
    ("slack_token", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{20,}\b")),
    ("generic_api_key", re.compile(r"(?:api[_-]?key|secret|password|token)\s*[:=]\s*[\"'][A-Za-z0-9_\-]{20,}[\"']", re.IGNORECASE)),
]
_PLACEHOLDER = re.compile(r"(example|placeholder|your[_-]?|xxxx|dummy|redacted|fake|sample|<[^>]+>)", re.IGNORECASE)
_RISKY_CMD = [
    ("pipe-to-shell", re.compile(r"\b(curl|wget)\b[^\n|]*\|\s*(sudo\s+)?(ba)?sh\b", re.IGNORECASE)),
    ("recursive-root-delete", re.compile(r"\brm\s+-[rRfF]+\s+/(\s|$)")),
    ("no-verify", re.compile(r"\b--no-verify\b")),
    ("world-writable", re.compile(r"\bchmod\s+(777|-R\s+777)\b")),
    ("force-push", re.compile(r"\bgit\s+push\s+.*--force\b", re.IGNORECASE)),
]
_INJECTION = [
    re.compile(r"ignore (?:all |any )?(?:previous|prior|above) instructions", re.IGNORECASE),
    re.compile(r"do not (?:tell|inform|mention to) the (?:user|human)", re.IGNORECASE),
    re.compile(r"disregard (?:the )?(?:system|safety|previous)", re.IGNORECASE),
    re.compile(r"exfiltrat|send .* (?:to|at) https?://", re.IGNORECASE),
]
_MD_LINK = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
_RUN_CMD = re.compile(r"\b(?:npm run|pnpm|yarn)\s+([A-Za-z0-9_:.\-]+)")
_TRIGGER = re.compile(r"\b(use when|when the user|whenever|trigger|use for|only when)\b", re.IGNORECASE)
_KEBAB = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def _mk(cfg: Config, rid: str, severity: str, path: str = "", line: int = 0,
        evidence: str = "", fix: str = "") -> Finding | None:
    if not _enabled(cfg, rid):
        return None
    title, why, default_fix = RULES_CATALOG[rid]
    return Finding(id=rid, severity=severity, title=title, path=path, line=line,
                   evidence=sanitize(evidence, 300), why=why, fix=fix or default_fix)


def _enabled(cfg: Config, rid: str) -> bool:
    if cfg.enabled_rules and rid not in cfg.enabled_rules:
        return False
    return rid not in cfg.disabled_rules and not any(
        fnmatch.fnmatch(rid, pat) for pat in cfg.disabled_rules
    )


def _scan_lines(text: str) -> list[tuple[int, str]]:
    out, in_fence = [], False
    for n, line in enumerate(text.splitlines(), 1):
        if line.lstrip().startswith("```") or line.lstrip().startswith("~~~"):
            in_fence = not in_fence
            continue
        if not in_fence:
            out.append((n, line))
    return out


# --- Check 1: everything provable from a single instruction file ------------
def rule_sources(ctx: ScanContext) -> list[Finding]:
    d, cfg = ctx.discovery, ctx.cfg
    out: list[Finding] = []
    for s in d.sources:
        if s.error:
            f = _mk(cfg, "PF002", "error", s.path, evidence=s.error)
            if f:
                out.append(f)
            continue
        for w in s.parse_warnings:
            f = _mk(cfg, "PF001", "warning", s.path, evidence=w)
            if f:
                out.append(f)
        if s.kind == "skill":
            meta = s.meta
            name = meta.get("name")
            desc = meta.get("description")
            if not isinstance(name, str) or not name.strip():
                f = _mk(cfg, "PF010", "error", s.path, 1, "missing 'name' in frontmatter")
                if f:
                    out.append(f)
            elif not _KEBAB.match(name.strip()):
                f = _mk(cfg, "PF010", "warning", s.path, 1,
                        f"name {name!r} is not kebab-case")
                if f:
                    out.append(f)
            if not isinstance(desc, str) or len(desc.strip()) < 20:
                f = _mk(cfg, "PF010", "error", s.path, 1,
                        "missing or very short 'description' (the routing signal)")
                if f:
                    out.append(f)
            elif not _TRIGGER.search(desc):
                f = _mk(cfg, "PF010", "warning", s.path, 1,
                        "description does not state when to use the skill")
                if f:
                    out.append(f)
            tools = meta.get("allowed-tools") or meta.get("allowed_tools")
            if isinstance(tools, str) and ("*" in tools or "Bash(*)" in tools):
                f = _mk(cfg, "PF073", "warning", s.path, 1,
                        "allowed-tools contains a wildcard (value not echoed)")
                if f:
                    out.append(f)
        for n, line in _scan_lines(s.text):
            for kind, pat in _SECRET_PATTERNS:
                m = pat.search(line)
                if m and not _PLACEHOLDER.search(line):
                    f = _mk(cfg, "PF070", "error", s.path, n,
                            f"{kind} matched at line {n}; value redacted")
                    if f:
                        out.append(f)
                    break
            for kind, pat in _RISKY_CMD:
                if pat.search(line):
                    f = _mk(cfg, "PF071", "warning", s.path, n,
                            f"{kind}: {sanitize(line.strip(), 160)}")
                    if f:
                        out.append(f)
                    break
            for pat in _INJECTION:
                if pat.search(line):
                    f = _mk(cfg, "PF072", "error", s.path, n,
                            f"injection-like phrasing: {sanitize(line.strip(), 160)}")
                    if f:
                        out.append(f)
                    break
            for m in _MD_LINK.finditer(line):
                target = m.group(1).split("#")[0].strip()
                if not target or "://" in target or target.startswith(("mailto:", "data:")):
                    continue
                cand = (d.root / Path(s.path).parent / target).resolve()
                if not is_within(cand, d.root):
                    f = _mk(cfg, "PF021", "error", s.path, n,
                            f"link target escapes repository: {sanitize(target)}")
                    if f:
                        out.append(f)
                elif not cand.exists():
                    f = _mk(cfg, "PF021", "warning", s.path, n,
                            f"missing local link target: {sanitize(target)}")
                    if f:
                        out.append(f)
            if d.package_scripts:
                for m in _RUN_CMD.finditer(line):
                    script = m.group(1)
                    if script in ("install", "add", "run", "test", "start", "ci"):
                        continue
                    if script not in d.package_scripts:
                        f = _mk(cfg, "PF080", "info", s.path, n,
                                f"package script {script!r} not declared in package.json")
                        if f:
                            out.append(f)
        if s.tokens > cfg.max_tokens:
            f = _mk(cfg, "PF060", "warning", s.path, 1,
                    f"file alone is ~{s.tokens} tokens (limit {cfg.max_tokens})")
            if f:
                out.append(f)
    return out


# --- Check 2: @import graph integrity --------------------------------------
def rule_imports(ctx: ScanContext) -> list[Finding]:
    d, cfg = ctx.discovery, ctx.cfg
    sev = {
        "escape": ("PF020", "error"), "in_code_fence": ("PF020", "warning"),
        "missing": ("PF020", "warning"), "circular": ("PF020", "warning"),
        "depth": ("PF020", "info"),
    }
    out: list[Finding] = []
    for ref in d.imports:
        if ref.status not in sev:
            continue
        rid, severity = sev[ref.status]
        reason = {
            "escape": "resolves outside the repository root (refused)",
            "in_code_fence": "sits inside a fenced code block, so it is rendered literally and never expanded",
            "missing": "target file does not exist",
            "circular": "part of an import cycle",
            "depth": "beyond the configured @import hop limit",
        }[ref.status]
        f = _mk(cfg, rid, severity, ref.origin, ref.line,
                f"@{sanitize(ref.raw)} — {reason}")
        if f:
            out.append(f)
    return out


# --- Check 3: properties of the *effective* context ------------------------
def rule_contexts(ctx: ScanContext) -> list[Finding]:
    resolutions, cfg, divs = ctx.resolutions, ctx.cfg, ctx.divergences
    out: list[Finding] = []
    seen_contra: set[str] = set()
    seen_dup: set[str] = set()
    for r in resolutions:
        for f in contradictions(r.directives, cfg.contradiction_threshold):
            key = f"{f.path}:{f.line}:{f.evidence[:80]}"
            if key in seen_contra:
                continue
            seen_contra.add(key)
            f.harness = r.harness
            out.append(f)
        for f in duplicates(r.directives):
            key = f"{f.path}:{f.line}:{f.evidence[:80]}"
            if key in seen_dup:
                continue
            seen_dup.add(key)
            f.harness = r.harness
            out.append(f)
        if r.tokens > cfg.max_tokens:
            f = _mk(cfg, "PF060", "warning", r.target,
                    evidence=f"{r.harness} effective context ~{r.tokens} tokens "
                             f"(limit {cfg.max_tokens})", fix="")
            if f:
                f.harness = r.harness
                out.append(f)
        for ex in r.excluded:
            if "shadowed" in ex.reason.lower():
                f = _mk(cfg, "PF030", "error", ex.path, evidence=ex.reason)
                if f:
                    f.harness = r.harness
                    out.append(f)
    for dv in divs:
        n = len(dv.only_left) + len(dv.only_right)
        if not n and not dv.contradictory:
            continue
        sev = "error" if dv.contradictory else "warning"
        examples = (dv.only_left[:2] + dv.only_right[:2])
        f = _mk(cfg, "PF041", sev, "",
                evidence=f"{dv.left} vs {dv.right}: {n} directives differ, "
                         f"{len(dv.contradictory)} contradictory, {dv.shared} shared; "
                         f"e.g. {'; '.join(sanitize(x, 90) for x in examples)}")
        if f:
            out.append(f)
    return out


RULES = RuleRegistry([
    Rule("source-integrity", rule_sources),
    Rule("import-graph", rule_imports),
    Rule("effective-context", rule_contexts),
])


def run_rules(d: Discovery, resolutions: list[Resolution], cfg: Config) -> list[Finding]:
    """Compatibility entry point used by `report.build`."""
    ctx = ScanContext(root=d.root, target="", discovery=d,
                      resolutions=resolutions, cfg=cfg)
    found = list(RULES.run(ctx))
    for w in d.warnings:
        f = _mk(cfg, "PF090", "info", evidence=w)
        if f:
            found.append(f)
    if d.truncated:
        f = _mk(cfg, "PF090", "warning", evidence="discovery bounded by max file/byte limits")
        if f:
            found.append(f)
    order = {"error": 0, "warning": 1, "info": 2}
    return sorted(found, key=lambda x: (
        order.get(x.severity, 3), x.id, x.path, x.line, x.evidence,
    ))
