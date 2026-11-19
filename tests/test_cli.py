import json
import unittest
from pathlib import Path

from tests.helpers import cli, make_repo

REPO = {
    "AGENTS.md": "- Always use tabs.\n- Run `pnpm test` first.\n",
    "CLAUDE.md": "- Never use tabs.\n",
    "src/AGENTS.md": "- Prefer functional patterns.\n",
    "src/app.py": "x = 1\n",
    "package.json": '{"scripts":{"test":"echo ok"}}\n',
}


class CliTests(unittest.TestCase):
    def test_version_and_harnesses(self):
        code, out, _ = cli("--version")
        self.assertEqual(code, 0)
        self.assertIn("prism 1.0.0", out)
        code, out, _ = cli("harnesses")
        self.assertEqual(code, 0)
        for h in ("codex", "claude", "zed", "cascade"):
            self.assertIn(h, out)

    def test_audit_json_is_valid_and_deterministic(self):
        root, tmp = make_repo(REPO)
        try:
            a = cli("--root", str(root), "audit", "src/app.py", "--format", "json", "--no-color")
            b = cli("--root", str(root), "audit", "src/app.py", "--format", "json", "--no-color")
            self.assertEqual(a[0], b[0])
            self.assertEqual(a[1], b[1])
            doc = json.loads(a[1])
            self.assertEqual(doc["tool"], "prism")
            self.assertEqual(len(doc["resolutions"]), 4)
            self.assertIn("limitations", doc)
        finally:
            tmp.cleanup()

    def test_exit_codes_and_fail_on(self):
        root, tmp = make_repo(REPO)
        try:
            args = ["--root", str(root), "audit", "src/app.py", "--format", "json", "--no-color"]
            self.assertEqual(cli(*args)[0], 1)
            self.assertEqual(cli(*args, "--fail-on", "never")[0], 0)
        finally:
            tmp.cleanup()

    def test_all_formats_are_parseable(self):
        root, tmp = make_repo(REPO)
        try:
            for fmt in ("tty", "json", "markdown", "sarif"):
                code, out, err = cli("--root", str(root), "audit", "src/app.py",
                                     "--format", fmt, "--no-color")
                self.assertEqual(code, 1, (fmt, err))
                self.assertTrue(out.strip())
                if fmt == "sarif":
                    self.assertEqual(json.loads(out)["version"], "2.1.0")
                if fmt == "markdown":
                    self.assertTrue(out.startswith("# prism"))
        finally:
            tmp.cleanup()

    def test_bad_config_returns_usage_error(self):
        root, tmp = make_repo({**REPO, "prism.json": '{"max_tokens": "not-a-number"}'})
        try:
            code, _, err = cli("--root", str(root), "audit", "src/app.py")
            self.assertEqual(code, 2)
            self.assertIn("wrong type", err)
        finally:
            tmp.cleanup()

    def test_unknown_harness_returns_usage_error(self):
        root, tmp = make_repo(REPO)
        try:
            code, _, err = cli("--root", str(root), "resolve", "src/app.py",
                               "--harness", "nope")
            self.assertEqual(code, 2)
            self.assertIn("unknown harness", err)
        finally:
            tmp.cleanup()

    def test_init_is_read_only_by_default(self):
        root, tmp = make_repo(REPO)
        try:
            code, out, _ = cli("--root", str(root), "init")
            self.assertEqual(code, 0)
            self.assertFalse((root / "prism.json").exists())
            self.assertIn("harnesses", out)
            code, _, _ = cli("--root", str(root), "init", "--write")
            self.assertEqual(code, 0)
            self.assertTrue((root / "prism.json").exists())
            code, _, err = cli("--root", str(root), "init", "--write")
            self.assertEqual(code, 2)
            self.assertIn("already exists", err)
        finally:
            tmp.cleanup()

    def test_snapshot_check_detects_context_drift(self):
        root, tmp = make_repo(REPO)
        try:
            self.assertEqual(cli("--root", str(root), "snapshot", "--write")[0], 0)
            self.assertTrue((root / ".prism.snapshot.json").exists())
            self.assertEqual(cli("--root", str(root), "check")[0], 0)
            (root / "src/AGENTS.md").write_text("- Prefer classes.\n", encoding="utf-8")
            code, out, _ = cli("--root", str(root), "check")
            self.assertEqual(code, 1)
            self.assertIn("change", out.lower())
        finally:
            tmp.cleanup()

    def test_same_edit_changes_only_matching_targets(self):
        root, tmp = make_repo(REPO)
        try:
            cli("--root", str(root), "snapshot", "--write")
            (root / "src/AGENTS.md").write_text("- Prefer classes.\n", encoding="utf-8")
            code, out, _ = cli("--root", str(root), "check", "--format", "json")
            self.assertEqual(code, 1)
            doc = json.loads(out)
            self.assertTrue(any(c["target"] == "src/app.py" for c in doc["changes"]))
        finally:
            tmp.cleanup()

    def test_source_tree_has_no_network_or_process_imports(self):
        forbidden = ("import socket", "import subprocess", "import requests",
                     "from urllib", "import urllib", "import http.client",
                     "os.system", "eval(", "exec(", "pickle.loads")
        base = Path(__file__).resolve().parent.parent / "prism"
        for p in sorted(base.rglob("*.py")):
            text = p.read_text(encoding="utf-8")
            for token in forbidden:
                self.assertNotIn(token, text, f"{p.name} contains {token}")

    def test_explain_all_lists_every_rule(self):
        code, out, _ = cli("explain", "--all")
        self.assertEqual(code, 0)
        self.assertIn("PF041", out)
        self.assertIn("PF073", out)


if __name__ == "__main__":
    unittest.main()
