"""Phase 5 engine: VWF hook, pair encoding of dialogue, marker build (docs/re/text.md §VWF)."""
import struct
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))
import build  # noqa: E402

try:
    import keystone  # noqa: F401
    import PIL  # noqa: F401
    HAVE = True
except ImportError:
    HAVE = False

if HAVE:
    import insert  # noqa: E402
    import msgs  # noqa: E402
    import vwf  # noqa: E402
    import vwf_font  # noqa: E402


@unittest.skipUnless(HAVE, "needs keystone-engine and pillow")
class Pairs(unittest.TestCase):
    def test_every_glyph_roundtrips_and_no_code_looks_like_control(self):
        chars = "".join(vwf_font.load())
        for i in range(len(chars)):
            for j in range(len(chars)):
                s = chars[i] + chars[j]
                codes = vwf.encode_pairs(s)
                self.assertEqual(vwf.decode_pairs(codes), s)
                for c in codes:
                    self.assertFalse(c & 0x8000, s)                  # end code
                    self.assertNotEqual(c & 0x0E00, 0x0200, s)       # the copy routine's argument test

    def test_mixed_text(self):
        s = "Hi, ×3 ♪ “Toma”… é!"
        self.assertEqual(vwf.decode_pairs(vwf.encode_pairs(s)), s)

    def test_glyphs_fit_their_storage(self):
        for ch, (w, rows) in vwf_font.load().items():
            self.assertLessEqual(w, 16, ch)
            self.assertEqual(len(rows), 16)

    def test_ink_width(self):
        self.assertEqual(vwf.ink_width(""), 0)
        self.assertEqual(vwf.ink_width("A"), vwf.text_width("A") - 1)


@unittest.skipUnless(HAVE and build.ROM.is_file(), "needs keystone-engine, pillow and the ROM")
class Engine(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = build.ROM.read_bytes()

    def test_hook_fits_and_patches(self):
        code = vwf.hook_code()
        self.assertLess(len(code), vwf.WIDTHS_AT - vwf.VWF_BASE)
        out = vwf.apply(bytearray(self.d))
        o = vwf.TYPE_LINE - vwf.BUS
        self.assertEqual(out[o:o + 2], self.d[o:o + 2])                      # push {r4-r7,lr} kept
        self.assertEqual(struct.unpack_from("<I", out, o + 8)[0], vwf.BUS + vwf.VWF_BASE + 1)
        changed = [i for i in range(len(self.d)) if out[i] != self.d[i] and i < vwf.VWF_BASE]
        self.assertTrue(all(o + 2 <= i < o + 12 or vwf.UPLOAD_SKIP - vwf.BUS <= i < vwf.UPLOAD_SKIP - vwf.BUS + 2
                            for i in changed), [hex(i) for i in changed[:5]])

    def test_japanese_glyphs_kept_at_8px(self):
        w, gly, pw, pg = vwf.tables(self.d)
        self.assertEqual(w[0x105], 8)                    # a kanji
        self.assertEqual(w[0x05E], vwf_font.load()["A"][0])

    def test_marker_build(self):
        out = insert.build_rom(self.d, "marker")
        self.assertEqual(len(out), len(self.d))
        tab = msgs.MSG_TABLE   # pages are pair codes now: read each message's first page back by hand
        rows = {r.id: r for r in insert.rom_rows(self.d)}
        seen = 0
        for n in range(msgs.MSG_COUNT):
            lst = struct.unpack_from("<I", out, tab + 4 * n)[0] - msgs.BUS
            p = struct.unpack_from("<I", out, lst)[0] - msgs.BUS
            if p < 0:
                continue
            codes = []
            while True:
                c = struct.unpack_from("<H", out, p + 2 * len(codes))[0]
                if c & 0x8000:
                    self.assertEqual(c & 0xFF, len(codes))
                    break
                codes.append(c)
            self.assertLessEqual(len(codes), insert.PAGE_CODES)
            text = vwf.decode_pairs(codes)
            self.assertLessEqual(vwf.ink_width(text), vwf.TOP_PX, text)
            self.assertIn(text.split(" ")[0], rows)
            seen += 1
        self.assertGreater(seen, 1500)
        # every system string with text is repointed to its marker
        for r in rows.values():
            if r.id[0] != "s" or not insert.is_text(r.jp):
                continue
            for h in r.ref.split(","):
                p = struct.unpack_from("<I", out, int(h, 16))[0] - msgs.BUS
                self.assertGreaterEqual(p, insert.TEXT_BASE, r.id)


@unittest.skipUnless(HAVE, "needs keystone-engine and pillow")
class Lint(unittest.TestCase):
    def setUp(self):
        import lint
        from tbl import Table
        self.lint = lint
        self.tbl = Table.load(ROOT / "tbl" / "en.tbl")

    def row(self, en, jp="テスト", rid="p07ECB4", ref="m0.0", file="msg_0000.tsv"):
        return {"id": rid, "ref": ref, "jp": jp, "en": en, "notes": "", "file": file}

    def test_page_budgets(self):
        ok = "Mmm, we walked the whol"                  # 167 px ink
        self.assertEqual(self.lint.lint_row(self.row(ok), self.tbl), ([], []))
        errs, _ = self.lint.lint_row(self.row(ok + "e way"), self.tbl)
        self.assertTrue(any("px" in e for e in errs))

    def test_format_checks(self):
        errs, _ = self.lint.lint_row(self.row("Hi {arg0}", jp="テスト"), self.tbl)
        self.assertIn("argument tokens differ from the Japanese", errs)
        errs, _ = self.lint.lint_row(self.row("Hi\\", jp="テスト"), self.tbl)
        self.assertTrue(any("encode" in e for e in errs))
        errs, _ = self.lint.lint_row(self.row("Hi", jp="　テスト"), self.tbl)
        self.assertIn("leading/trailing blank differs from the Japanese", errs)

    def test_battle_line_counts_names(self):
        r = self.row("{arg0} hits {arg1}!", jp="{arg0}が{arg1}に", rid="s09F6C4", ref="21B4EC", file="sys_battle.tsv")
        self.assertEqual(self.lint.lint_row(r, self.tbl), ([], []))
