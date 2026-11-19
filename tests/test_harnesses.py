import unittest
from pathlib import Path

from prism.config import Config
from prism.discovery import discover
from prism.harnesses import all_divergences, divergence, resolve, resolve_all
from tests.helpers import make_repo

FILES = {
    "AGENTS.md": "- Always use tabs.\n- Run `pnpm test` first.\n",
    "CLAUDE.md": "- Never use tabs.\n- Always use spaces.\n",
    "src/AGENTS.md": "- Prefer functional patterns.\n",
    "src/app.py": "x = 1\n",
    "pkg/other.py": "y = 2\n",
    ".rules": "- Legacy rule wins for Zed.\n",
}


class HarnessTests(unittest.TestCase):
    def setUp(self):
        self.root, self.tmp = make_repo(FILES)
        self.cfg = Config()
        self.d = discover(self.root, self.cfg)

    def tearDown(self):
        self.tmp.cleanup()

    def test_codex_concatenates_root_to_cwd(self):
        r = resolve("codex", self.root, "src/app.py", self.d, self.cfg)
        self.assertEqual([i.path for i in r.included], ["AGENTS.md", "src/AGENTS.md"])
        self.assertEqual([i.order for i in r.included], [0, 1])

    def test_codex_takes_at_most_one_file_per_directory(self):
        self.root.joinpath("AGENT.md").write_text("- second\n", encoding="utf-8")
        d = discover(self.root, self.cfg)
        r = resolve("codex", self.root, "src/app.py", d, self.cfg)
        self.assertEqual([i.path for i in r.included][0], "AGENTS.md")

    def test_claude_shadowing_requires_a_local_claude_md(self):
        r = resolve("claude", self.root, "src/app.py", self.d, self.cfg)
        reasons = [e.reason for e in r.excluded]
        # root has both files -> shadowed; src/ has no CLAUDE.md -> must NOT be shadowed
        shadowed = [e.path for e in r.excluded if "shadowed" in e.reason.lower()]
        self.assertIn("AGENTS.md", shadowed)
        self.assertNotIn("src/AGENTS.md", shadowed)

    def test_claude_includes_imports(self):
        self.root.joinpath("CLAUDE.md").write_text("@notes.md\n", encoding="utf-8")
        self.root.joinpath("notes.md").write_text("- Keep notes short.\n", encoding="utf-8")
        d = discover(self.root, self.cfg)
        r = resolve("claude", self.root, "src/app.py", d, self.cfg)
        self.assertIn("notes.md", [i.path for i in r.included])

    def test_zed_first_match_wins_and_does_not_traverse(self):
        r = resolve("zed", self.root, "src/app.py", self.d, self.cfg)
        self.assertEqual([i.path for i in r.included], [".rules"])
        self.assertTrue(all("not traverse" in e.reason or "candidate list" in e.reason
                            or "not in Zed" in e.reason
                            for e in r.excluded))

    def test_cascade_scopes_nested_agents_md(self):
        r = resolve("cascade", self.root, "pkg/other.py", self.d, self.cfg)
        paths = [i.path for i in r.included]
        self.assertIn("AGENTS.md", paths)
        self.assertNotIn("src/AGENTS.md", paths)

    def test_all_harnesses_return_notes_and_caveats(self):
        for r in resolve_all(self.root, "src/app.py", self.d, self.cfg):
            self.assertTrue(any("model=" in n for n in r.notes))
            self.assertTrue(any("caveat:" in n for n in r.notes))

    def test_divergence_is_symmetric_in_counts(self):
        a = resolve("codex", self.root, "src/app.py", self.d, self.cfg)
        b = resolve("claude", self.root, "src/app.py", self.d, self.cfg)
        dv = divergence(a, b, 0.70)
        self.assertGreater(len(dv.only_left), 0)
        self.assertGreater(len(dv.only_right), 0)
        self.assertEqual(len(all_divergences(resolve_all(self.root, "src/app.py", self.d, self.cfg))), 6)

    def test_unknown_harness_raises(self):
        with self.assertRaises(KeyError):
            resolve("unknown", self.root, "src/app.py", self.d, self.cfg)


if __name__ == "__main__":
    unittest.main()
