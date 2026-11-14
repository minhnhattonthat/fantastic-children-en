"""Phase 8 layout rules: reflow keeps every group's text, pages and indents, and the ▼ cursor rule in lint."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import batches  # noqa: E402
import lint  # noqa: E402
import reflow  # noqa: E402


def row(i, jp, en, ref):
    return {"id": f"p{i:06X}", "ref": ref, "jp": jp, "en": en, "file": "msg_0000.tsv"}


class Reflow(unittest.TestCase):
    def test_solve_keeps_words_pages_and_indents(self):
        g = [row(1, "あ", "Since the 15th century, / children", "m0.0"),
             row(2, "い", "have vanished in groups... / every 11 years. These", "m0.1"),
             row(3, "　う", " white-haired ones were called / the Children.", "m0.2")]
        new = reflow.solve(g, parity_fixed=True, terms=[])
        self.assertIsNotNone(new)
        self.assertEqual(len(new), 3)
        words = lambda pages: " ".join(p.replace(lint.LINE_SEP, " ") for p in pages).split()
        self.assertEqual(words(new), words([r["en"] for r in g]))
        self.assertTrue(new[2].startswith(" ") and not new[0].startswith(" "))
        lines = [ln for p in new for ln in p.split(lint.LINE_SEP)]
        self.assertEqual((len(lines) - 3) % 2, 0, "parity before a blank page")
        self.assertLessEqual(reflow.mid_ends([ln.strip() for ln in lines]),
                             reflow.mid_ends(reflow.lines_of(g)))

    def test_glued_units(self):
        words = 'Battle Item SP "Old Paints" obtained! Deals 10 damage with the +Control Pad'.split()
        glue = reflow.glued(words, batches.glossary())
        self.assertIn(words.index('Paints"'), glue)
        self.assertIn(words.index("damage"), glue)
        self.assertIn(words.index("Pad"), glue)


class Cursor(unittest.TestCase):
    def test_full_width_last_line_touches_cursor(self):
        b = (168, 21, "box top")
        self.assertTrue(lint.cursor_follows(row(1, "あ", "x", "m9999.0"), b))
        self.assertFalse(lint.cursor_follows(row(1, "あ", "x", "m9999.0"), (72, 9, "choice answer, 9 cells")))

    def test_script_clears_cursor(self):
        from tbl import Table
        en_tbl = Table.load(ROOT / "tbl" / "en.tbl")
        bad = [r["id"] for r in lint.load().values() if r["en"] and r["id"][0] == "p"
               and any("▼" in e for e in lint.lint_row(r, en_tbl)[0])]
        self.assertEqual(bad, [])


if __name__ == "__main__":
    unittest.main()
