import unittest

from prism.directives import contradictions, duplicates, extract


class DirectiveTests(unittest.TestCase):
    def test_extracts_bullets_and_polarity(self):
        ds = extract("- Always use tabs.\n- Never use spaces.\n1. Prefer small PRs.\n\nplain text\n", "A.md")
        self.assertEqual(len(ds), 3)
        self.assertEqual(ds[0].polarity, "positive")
        self.assertEqual(ds[1].polarity, "negative")
        self.assertEqual(ds[2].polarity, "positive")

    def test_ignores_fenced_code_and_headings(self):
        text = "# Heading\n\n```\n- Always do bad thing\n```\n\n- Always do good thing\n"
        ds = extract(text, "A.md")
        self.assertEqual(len(ds), 1)
        self.assertIn("good", ds[0].text)

    def test_contradiction_same_subject_opposite_polarity(self):
        ds = (extract("- Always use tabs for indentation.\n", "root/AGENTS.md") +
              extract("- Never use tabs for indentation. Always use spaces.\n", "CLAUDE.md"))
        found = contradictions(ds, 0.70)
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0].id, "PF040")

    def test_scope_qualifier_prevents_false_positive(self):
        ds = (extract("- Always use tabs.\n", "A.md") +
              extract("- Never use tabs in production.\n", "B.md"))
        self.assertEqual(contradictions(ds, 0.60), [])

    def test_same_source_never_contradicts_itself(self):
        ds = extract("- Always use tabs.\n- Never use tabs.\n", "A.md")
        self.assertEqual(contradictions(ds, 0.60), [])

    def test_unrelated_rules_do_not_collide(self):
        ds = (extract("- Always use tabs.\n", "A.md") +
              extract("- Never deploy on Fridays.\n", "B.md"))
        self.assertEqual(contradictions(ds, 0.60), [])

    def test_duplicates_detected_across_sources(self):
        ds = (extract("- Always use tabs for indentation.\n", "A.md") +
              extract("- Always use tabs for indentation.\n", "B.md"))
        self.assertEqual(len(duplicates(ds)), 1)

    def test_inline_code_does_not_pollute_keys(self):
        ds = extract("- Always run `pnpm test` before committing.\n", "A.md")
        self.assertNotIn("pnpm", ds[0].key)

    def test_import_line_is_not_a_directive(self):
        ds = extract("- @docs/style.md\n", "CLAUDE.md")
        self.assertEqual(ds, [], "a bare @import is metadata, not an instruction")


if __name__ == "__main__":
    unittest.main()
