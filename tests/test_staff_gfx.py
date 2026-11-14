"""G5 staff roll: the English cards written by staff_gfx.apply read back through the game's own table, records and
maps as the committed PNGs, and every block fits its VRAM slot."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import gbacomp  # noqa: E402
import staff_gfx as s  # noqa: E402

ROM = ROOT / "rom" / "Fantastic Children (Japan).gba"


@unittest.skipUnless(ROM.exists() and s.png_path(0).exists(), "needs the dump and gfx/staff_NN.png")
class StaffGfx(unittest.TestCase):
    def test_roundtrip(self):
        from PIL import Image
        rom = ROM.read_bytes()
        out = bytearray(rom) + bytearray(0x10000)
        free = [len(rom)]

        def alloc(size):
            at = free[0]
            free[0] += (size + 3) & ~3
            return at
        s.apply(out, alloc=alloc)
        out = bytes(out)
        for n in range(s.CARDS):
            self.assertEqual(s.card(out, n), s.card(rom, n))       # table untouched
            got = s.card_png(out, n)
            want = Image.open(s.png_path(n))
            self.assertEqual(list(got.getdata()), list(want.getdata()), f"card {n}")
        for a, ns in s.blocks(out).items():
            t, _ = gbacomp.decompress(out, s.block(out, a)[0])
            self.assertLessEqual(len(t) // 32, min(s.CAP[n % 2] for n in ns), f"block {a}")
            self.assertEqual(t[:32], bytes(32), f"block {a}: tile 0 must be blank")

    def test_tsv_rows(self):
        rows = s.lines()
        self.assertEqual({c for c, *_ in rows}, set(range(s.CARDS)))
        for c, r, jp, en in rows:
            self.assertTrue(en and en == en.upper() and len(en) <= s.W and r + 2 <= s.H, (c, r, en))


if __name__ == "__main__":
    unittest.main()
