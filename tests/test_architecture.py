"""Regression tests for the behavior-preserving architecture refactor."""

import unittest

from prism.config import Config
from prism.context import ScanContext
from prism.discovery import discover
from prism.harnesses import all_divergences, resolve_all
from prism.model import Finding, Report
from prism.registry import Renderer, RendererRegistry, Rule, RuleRegistry
from prism.render import RENDERERS, render
from prism.rules import RULES
from prism.rules_catalog import RULES_CATALOG
from tests.helpers import make_repo


class ArchitectureTests(unittest.TestCase):
    def test_registries_expose_stable_extension_points(self):
        self.assertEqual(RULES.names(),
                         ["source-integrity", "import-graph", "effective-context"])
        self.assertEqual(RENDERERS.formats(), ["json", "markdown", "sarif", "tty"])
        self.assertEqual(set(RENDERERS.formats()),
                         {"tty", "json", "markdown", "sarif"})

    def test_custom_renderer_needs_no_dispatch_edit(self):
        reg = RendererRegistry([Renderer("upper", lambda r: "CUSTOM")])
        self.assertEqual(reg.render(Report(), "upper", False, False), "CUSTOM")
        with self.assertRaises(KeyError):
            reg.render(Report(), "missing", False, False)

    def test_rule_registry_orders_findings_in_one_place(self):
        reg = RuleRegistry([
            Rule("second", lambda ctx: [Finding(id="PF999", severity="info", title="later")]),
            Rule("first", lambda ctx: [Finding(id="PF001", severity="error", title="first")]),
        ])
        self.assertEqual([f.id for f in reg.run(None)], ["PF001", "PF999"])

    def test_scan_context_matches_direct_divergence_calculation(self):
        root, tmp = make_repo({
            "AGENTS.md": "- Always use tabs.\n",
            "CLAUDE.md": "- Never use tabs.\n",
            "src/app.py": "x = 1\n",
        })
        try:
            cfg = Config()
            d = discover(root, cfg)
            res = resolve_all(root, "src/app.py", d, cfg)
            ctx = ScanContext(root=root, target="src/app.py", discovery=d,
                              resolutions=res, cfg=cfg)
            self.assertEqual([x.to_dict() for x in ctx.divergences],
                             [x.to_dict() for x in all_divergences(res, cfg.contradiction_threshold)])
        finally:
            tmp.cleanup()

    def test_unknown_format_still_falls_back_to_tty(self):
        out = render(Report(), "not-a-real-format", False, False)
        self.assertTrue(out.startswith("┌"))
        self.assertIn("prism", out)

    def test_catalog_is_declarative_and_complete(self):
        self.assertEqual(len(RULES_CATALOG), 16)
        self.assertTrue(all(rid.startswith("PF") for rid in RULES_CATALOG))
        self.assertEqual(len({title for title, _, _ in RULES_CATALOG.values()}),
                         len(RULES_CATALOG))


if __name__ == "__main__":
    unittest.main()
