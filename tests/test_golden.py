"""Behavior-preservation gate for the architecture refactor.

These hashes were frozen BEFORE any structural refactor. They cover every CLI
command and every output format. If a refactor changes any byte of observable
output, this test fails - that is the whole point.
"""

import hashlib
import json
import subprocess
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
BASELINE = json.loads((Path(__file__).parent / "golden" / "BASELINE.json").read_text(
    encoding="utf-8"))["commands"]


class GoldenTests(unittest.TestCase):
    def test_observable_behavior_is_byte_identical(self):
        for name, spec in BASELINE.items():
            with self.subTest(command=name):
                p = subprocess.run(
                    [sys.executable, "-m", "prism", *spec["args"]],
                    cwd=str(REPO), capture_output=True, text=True,
                )
                digest = hashlib.sha256(p.stdout.encode("utf-8")).hexdigest()
                self.assertEqual(p.returncode, spec["exit"], f"{name}: exit code changed")
                self.assertEqual(digest, spec["sha256"],
                                 f"{name}: output changed - the refactor altered behavior")

    def test_snapshot_check_still_passes_on_its_own_baseline(self):
        p = subprocess.run(
            [sys.executable, "-m", "prism", "--root", "examples/demo", "snapshot"],
            cwd=str(REPO), capture_output=True, text=True,
        )
        doc = json.loads(p.stdout)
        self.assertEqual(doc["tool"], "prism")
        self.assertEqual(doc["schema"], 1)
        self.assertEqual(set(doc["harnesses"]), {"codex", "claude", "zed", "cascade"})


if __name__ == "__main__":
    unittest.main()
