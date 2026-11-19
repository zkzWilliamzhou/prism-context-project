import unittest

from prism.frontmatter import parse_frontmatter


class FrontmatterTests(unittest.TestCase):
    def test_no_frontmatter(self):
        meta, body, warns, has = parse_frontmatter("# hello\n\ntext\n")
        self.assertFalse(has)
        self.assertEqual(meta, {})
        self.assertEqual(warns, [])
        self.assertTrue(body.startswith("# hello"))

    def test_unterminated(self):
        meta, body, warns, has = parse_frontmatter("---\nname: x\n")
        self.assertFalse(has)
        self.assertTrue(any("no closing" in w for w in warns))
        self.assertIn("name: x", body)

    def test_scalars_and_types(self):
        doc = ('---\nname: pdf-tools\ndescription: "Use when handling PDFs"\n'
               'count: 3\nenabled: true\ndisabled: false\nempty: null\n---\n# body\n')
        meta, body, warns, has = parse_frontmatter(doc)
        self.assertTrue(has)
        self.assertEqual(meta["name"], "pdf-tools")
        self.assertEqual(meta["description"], "Use when handling PDFs")
        self.assertEqual(meta["count"], 3)
        self.assertIs(meta["enabled"], True)
        self.assertIs(meta["disabled"], False)
        self.assertIsNone(meta["empty"])
        self.assertEqual(warns, [])
        self.assertEqual(body.strip(), "# body")

    def test_inline_list_with_quoted_commas(self):
        doc = '---\nglobs: ["src/a,b.ts", \'src/**/*.tsx\', plain.md]\n---\nx\n'
        meta, _, warns, _ = parse_frontmatter(doc)
        self.assertEqual(meta["globs"], ["src/a,b.ts", "src/**/*.tsx", "plain.md"])
        self.assertEqual(warns, [])

    def test_nested_map_and_list(self):
        doc = ('---\nmetadata:\n  author: Ada\n  trigger: writing prose\n'
               'tags:\n  - one\n  - two\n---\nbody\n')
        meta, _, warns, _ = parse_frontmatter(doc)
        self.assertEqual(meta["metadata"], {"author": "Ada", "trigger": "writing prose"})
        self.assertEqual(meta["tags"], ["one", "two"])
        self.assertEqual(warns, [])

    def test_block_scalar(self):
        doc = "---\nnotes: |\n  first line\n  second line\n---\nbody\n"
        meta, _, _, _ = parse_frontmatter(doc)
        self.assertEqual(meta["notes"], "first line\nsecond line")

    def test_folded_scalar(self):
        doc = "---\nnotes: >\n  first line\n  second line\n---\nbody\n"
        meta, _, _, _ = parse_frontmatter(doc)
        self.assertEqual(meta["notes"], "first line second line")

    def test_comments_and_duplicates(self):
        doc = "---\nname: a # inline\nname: b\n---\nbody\n"
        meta, _, warns, _ = parse_frontmatter(doc)
        self.assertEqual(meta["name"], "b")
        self.assertTrue(any("duplicate" in w for w in warns))

    def test_unsupported_syntax_warns_but_does_not_raise(self):
        doc = "---\nname: a\n: bad\n  nested: value\n---\nbody\n"
        meta, _, warns, _ = parse_frontmatter(doc)
        self.assertEqual(meta["name"], "a")
        self.assertTrue(any("unsupported" in w for w in warns))
        self.assertTrue(any("indentation" in w for w in warns))

    def test_crlf_and_bom_are_tolerated(self):
        doc = "\ufeff---\r\nname: a\r\n---\r\nbody\r\n"
        # A UTF-8 BOM before the delimiter is not valid frontmatter; we must
        # degrade gracefully rather than crash or misparse.
        meta, body, _, has = parse_frontmatter(doc)
        self.assertFalse(has)
        self.assertIn("name: a", body)


if __name__ == "__main__":
    unittest.main()
