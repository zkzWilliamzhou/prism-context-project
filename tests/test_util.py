import os
import unittest
from pathlib import Path

from prism.util import is_within, safe_read, sanitize, sha256_text, token_estimate
from tests.helpers import make_repo


class UtilTests(unittest.TestCase):
    def test_sanitize_strips_ansi_and_controls(self):
        raw = "\x1b[31mRED\x1b[0m\n\x00\x07 tab\there\u202eRLO\u200b"
        out = sanitize(raw)
        self.assertNotIn("\x1b", out)
        self.assertNotIn("\x00", out)
        self.assertNotIn("\u202e", out)
        self.assertNotIn("\u200b", out)
        self.assertNotIn("\n", out)

    def test_sanitize_bounds_length(self):
        self.assertTrue(sanitize("a" * 10000, 20).endswith("…"))
        self.assertLessEqual(len(sanitize("a" * 10000, 20)), 21)

    def test_containment_blocks_parent_traversal(self):
        root, tmp = make_repo({"AGENTS.md": "x"})
        try:
            self.assertTrue(is_within(root / "AGENTS.md", root))
            self.assertFalse(is_within(root / "../outside.md", root))
            with self.assertRaises(OSError):
                safe_read(root / "../outside.md", root)
        finally:
            tmp.cleanup()

    def test_containment_blocks_symlink_escape(self):
        root, tmp = make_repo({"AGENTS.md": "x"})
        try:
            outside = Path(tmp.name).parent / "prism-outside-secret.txt"
            outside.write_text("SECRET", encoding="utf-8")
            link = root / "link.md"
            try:
                link.symlink_to(outside)
            except (OSError, NotImplementedError):
                self.skipTest("symlinks unavailable")
            self.assertFalse(is_within(link, root))
            with self.assertRaises(OSError):
                safe_read(link, root)
        finally:
            outside.unlink(missing_ok=True)
            tmp.cleanup()

    def test_safe_read_bounds_size(self):
        root, tmp = make_repo({"big.md": "a" * 100})
        try:
            from prism.util import MAX_FILE_BYTES
            # Patch the cap to a small value to exercise the guard cheaply.
            import prism.util as util
            old = util.MAX_FILE_BYTES
            util.MAX_FILE_BYTES = 10
            try:
                with self.assertRaises(OSError):
                    safe_read(root / "big.md", root)
            finally:
                util.MAX_FILE_BYTES = old
        finally:
            tmp.cleanup()

    def test_deterministic_hashing_and_token_proxy(self):
        self.assertEqual(sha256_text("abc"), sha256_text("abc"))
        self.assertEqual(token_estimate(""), 0)
        self.assertEqual(token_estimate("abcd"), 1)
        self.assertEqual(token_estimate("abcde"), 2)
        self.assertEqual(token_estimate("éééé"), 2)  # byte-based, stable


if __name__ == "__main__":
    unittest.main()
