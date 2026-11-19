import unittest

from prism.config import Config
from prism.discovery import classify, collect_targets, discover, git_root
from tests.helpers import make_repo


class DiscoveryTests(unittest.TestCase):
    def test_classify_all_kinds(self):
        cases = {
            "SKILL.md": "skill", "AGENTS.md": "agents_md", "AGENT.md": "agents_md",
            "CLAUDE.md": "claude_md", "CLAUDE.local.md": "claude_md",
            "GEMINI.md": "gemini_md", ".rules": "legacy_rule",
            ".cursorrules": "legacy_rule",
            ".github/copilot-instructions.md": "copilot_instruction",
            ".cursor/rules/a.mdc": "cursor_rule",
            ".claude/rules/a.md": "claude_rule",
            ".devin/rules/a.md": "devin_rule",
            ".kiro/steering/a.md": "kiro_rule",
            ".junie/guide.md": "junie_rule",
            "src/main.py": None, "README.md": None,
        }
        for path, expected in cases.items():
            self.assertEqual(classify(path, path.rsplit("/", 1)[-1]), expected, path)

    def test_prunes_dependency_dirs(self):
        root, tmp = make_repo({
            "AGENTS.md": "- rule\n",
            "node_modules/pkg/AGENTS.md": "- ignore me\n",
            ".git/hooks/AGENTS.md": "- ignore me\n",
        })
        try:
            d = discover(root, Config())
            paths = [s.path for s in d.sources]
            self.assertIn("AGENTS.md", paths)
            self.assertFalse(any("node_modules" in p for p in paths))
            self.assertFalse(any(p.startswith(".git/") for p in paths))
        finally:
            tmp.cleanup()

    def test_ignore_patterns(self):
        root, tmp = make_repo({"AGENTS.md": "- a\n", "generated/AGENTS.md": "- b\n"})
        try:
            cfg = Config(ignore=["generated/**"])
            paths = [s.path for s in discover(root, cfg).sources]
            self.assertEqual(paths, ["AGENTS.md"])
        finally:
            tmp.cleanup()

    def test_import_expansion_and_fence_detection(self):
        root, tmp = make_repo({
            "CLAUDE.md": "# c\n@docs/style.md\n\n```\n@docs/fenced.md\n```\n",
            "docs/style.md": "- Follow the guide.\n",
        })
        try:
            d = discover(root, Config())
            statuses = {r.raw: r.status for r in d.imports}
            self.assertEqual(statuses.get("docs/style.md"), "ok")
            self.assertEqual(statuses.get("docs/fenced.md"), "in_code_fence")
            self.assertIn("docs/style.md", [s.path for s in d.sources])
        finally:
            tmp.cleanup()

    def test_import_escape_and_missing(self):
        root, tmp = make_repo({
            "CLAUDE.md": "@../outside.md\n@missing.md\n",
        })
        try:
            d = discover(root, Config())
            statuses = {r.raw: r.status for r in d.imports}
            self.assertEqual(statuses["../outside.md"], "escape")
            self.assertEqual(statuses["missing.md"], "missing")
        finally:
            tmp.cleanup()

    def test_import_cycle_is_bounded(self):
        root, tmp = make_repo({
            "CLAUDE.md": "@a.md\n",
            "a.md": "@b.md\n",
            "b.md": "@a.md\n",
        })
        try:
            d = discover(root, Config(import_hops=4))
            self.assertTrue(any(r.status == "circular" for r in d.imports))
            self.assertLessEqual(len(d.imports), 12)
        finally:
            tmp.cleanup()

    def test_hop_limit_reports_depth(self):
        root, tmp = make_repo({
            "CLAUDE.md": "@a.md\n", "a.md": "@b.md\n", "b.md": "@c.md\n",
            "c.md": "@d.md\n", "d.md": "- end\n",
        })
        try:
            d = discover(root, Config(import_hops=2))
            self.assertTrue(any(r.status == "depth" for r in d.imports))
        finally:
            tmp.cleanup()

    def test_package_scripts_and_targets(self):
        root, tmp = make_repo({"src/a.py": "x", "AGENTS.md": "- a\n",
                              "package.json": '{"scripts":{"test":"echo ok"}}'})
        try:
            d = discover(root, Config())
            self.assertEqual(d.package_scripts.get("test"), "echo ok")
            self.assertIn("src/a.py", collect_targets(root, Config()))
        finally:
            tmp.cleanup()


if __name__ == "__main__":
    unittest.main()
