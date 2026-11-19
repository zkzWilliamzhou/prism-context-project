"""Adversarial regressions from review rounds 3-7.

Each test here corresponds to a defect or unsafe behaviour found during a
strict review round; they stay in the suite permanently so it cannot return.
"""

import json
import os
import time
import unittest
from pathlib import Path

from prism.api import build_snapshot
from prism.config import Config
from prism.directives import _extract_cached
from prism.discovery import classify, discover
from prism.render import render
from prism.report import build
from prism.harnesses import resolve_all
from tests.helpers import cli, make_repo

BASE = {"AGENTS.md": "- Always use tabs.\n", "src/app.py": "x = 1\n"}


class HostileTests(unittest.TestCase):
    def test_config_cannot_read_outside_root(self):
        root, tmp = make_repo(BASE)
        try:
            outside = Path(tmp.name).parent / "prism-outside-config.json"
            outside.write_text('{"fail_on":"never"}', encoding="utf-8")
            code, _, err = cli("--root", str(root), "--config", str(outside), "audit")
            self.assertEqual(code, 2)
            self.assertIn("escapes", err)
        finally:
            outside.unlink(missing_ok=True)
            tmp.cleanup()

    def test_init_refuses_to_write_through_symlink(self):
        root, tmp = make_repo(BASE)
        try:
            inner = root / "shared-config.json"
            inner.write_text('{"fail_on":"never"}', encoding="utf-8")
            link = root / "prism.json"
            try:
                link.symlink_to(inner)
            except (OSError, NotImplementedError):
                self.skipTest("symlinks unavailable")
            code, _, err = cli("--root", str(root), "init", "--write", "--force")
            self.assertEqual(code, 2)
            self.assertEqual(inner.read_text(encoding="utf-8"), '{"fail_on":"never"}')
            self.assertIn("symlink", err)
        finally:
            tmp.cleanup()

    def test_snapshot_refuses_to_write_through_symlink(self):
        root, tmp = make_repo(BASE)
        try:
            outside = Path(tmp.name).parent / "prism-outside-snap.txt"
            outside.write_text("UNTOUCHED", encoding="utf-8")
            link = root / ".prism.snapshot.json"
            try:
                link.symlink_to(outside)
            except (OSError, NotImplementedError):
                self.skipTest("symlinks unavailable")
            code, _, err = cli("--root", str(root), "snapshot", "--write")
            self.assertEqual(code, 2)
            self.assertEqual(outside.read_text(encoding="utf-8"), "UNTOUCHED")
        finally:
            outside.unlink(missing_ok=True)
            tmp.cleanup()

    def test_target_outside_root_rejected(self):
        root, tmp = make_repo(BASE)
        try:
            code, _, err = cli("--root", str(root), "resolve", "../../etc/passwd")
            self.assertEqual(code, 2)
            self.assertIn("escapes", err)
        finally:
            tmp.cleanup()

    def test_non_utf8_instruction_file_is_tolerated(self):
        root, tmp = make_repo({})
        try:
            (root / "AGENTS.md").write_bytes(b"- Always use tabs.\n\xff\xfe\x80 broken\n")
            (root / "src").mkdir()
            (root / "src/app.py").write_text("x = 1\n", encoding="utf-8")
            code, out, err = cli("--root", str(root), "audit", "src/app.py", "--format", "json")
            self.assertIn(code, (0, 1))
            self.assertEqual(err, "")
            self.assertEqual(json.loads(out)["tool"], "prism")
        finally:
            tmp.cleanup()

    def test_empty_repository_is_clean(self):
        root, tmp = make_repo({})
        try:
            code, out, err = cli("--root", str(root), "audit", "--format", "json")
            self.assertEqual(code, 0)
            self.assertEqual(err, "")
            doc = json.loads(out)
            self.assertEqual(doc["sources"], [])
            self.assertEqual(doc["counts"], {"error": 0, "warning": 0, "info": 0})
        finally:
            tmp.cleanup()

    def test_no_format_leaks_a_credential(self):
        secret = "ghp_" + "B" * 40
        root, tmp = make_repo({
            "AGENTS.md": f"- token = \"{secret}\"\n",
            "src/app.py": "x = 1\n",
        })
        try:
            for fmt in ("tty", "json", "markdown", "sarif"):
                code, out, err = cli("--root", str(root), "audit", "src/app.py",
                                     "--format", fmt, "--no-color")
                self.assertIn(code, (0, 1), fmt)
                self.assertNotIn(secret, out, fmt)
                self.assertNotIn(secret, err, fmt)
        finally:
            tmp.cleanup()

    def test_json_report_is_independent_of_cwd(self):
        root, tmp = make_repo(BASE)
        old = os.getcwd()
        try:
            os.chdir(root)
            a = cli("--root", str(root), "audit", "src/app.py", "--format", "json", "--no-color")
            os.chdir(Path(root).parent)
            b = cli("--root", str(root), "audit", "src/app.py", "--format", "json", "--no-color")
            self.assertEqual(a[1], b[1])
        finally:
            os.chdir(old)
            tmp.cleanup()

    def test_case_insensitive_instruction_classification(self):
        self.assertEqual(classify("foo.INSTRUCTIONS.MD", "foo.INSTRUCTIONS.MD"),
                         "copilot_instruction")

    def test_fail_on_warning_and_info_thresholds(self):
        root, tmp = make_repo({
            "AGENTS.md": "- Always use tabs for indentation.\n",
            "src/AGENTS.md": "- Always use tabs for indentation.\n",
            "src/app.py": "x = 1\n",
        })
        try:
            base = ["--root", str(root), "audit", "src/app.py", "--format", "json", "--no-color"]
            self.assertEqual(cli(*base, "--fail-on", "info")[0], 1)
            self.assertEqual(cli(*base, "--fail-on", "error")[0], 0)
        finally:
            tmp.cleanup()

    def test_snapshot_is_byte_stable_across_runs(self):
        root, tmp = make_repo(BASE)
        try:
            self.assertEqual(build_snapshot(root, Config()),
                             build_snapshot(root, Config()))
        finally:
            tmp.cleanup()

    def test_directive_parsing_is_memoized(self):
        files = {f"pkg{i}/AGENTS.md": "- Always use tabs.\n- Prefer small PRs.\n"
                 for i in range(12)}
        files.update({f"pkg{i}/mod{j}.py": "x = 1\n"
                      for i in range(12) for j in range(4)})
        root, tmp = make_repo(files)
        try:
            _extract_cached.cache_clear()
            t0 = time.perf_counter()
            doc = build_snapshot(root, Config(max_targets=100))
            elapsed = time.perf_counter() - t0
            info = _extract_cached.cache_info()
            self.assertGreaterEqual(len(doc["targets"]), 48)
            self.assertGreater(info.hits, 0, "identical sources must be parsed once")
            self.assertLess(elapsed, 5.0, "snapshot must stay fast on a modest repo")
        finally:
            tmp.cleanup()

    def test_report_from_library_api_is_redacted(self):
        secret = "sk-" + "C" * 40
        root, tmp = make_repo({"AGENTS.md": f'- key = "{secret}"\n',
                               "src/app.py": "x = 1\n"})
        try:
            from prism.api import audit
            text = json.dumps(audit(root, target="src/app.py").to_dict())
            self.assertNotIn(secret, text)
            self.assertNotIn(secret, render(audit(root, target="src/app.py"), "tty"))
        finally:
            tmp.cleanup()


if __name__ == "__main__":
    unittest.main()
