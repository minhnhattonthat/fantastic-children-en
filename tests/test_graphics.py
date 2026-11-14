"""Pins the graphics-text sources found by the Phase 1 static sweep (docs/re/graphics.md)."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import dec  # noqa: E402
import gbacomp  # noqa: E402

TITLE_BG = (0x30E21C, 0x36A414, 0x3725F4, 0x378E30)  # G1+G2, 8bpp title backgrounds
CREDITS = (0x709094, 0x70A4D4, 0x70AF18, 0x70C5B0, 0x70D32C, 0x70E2EC, 0x70EC24, 0x70F174)  # G5
CREDITS_SIZES = (6272, 3200, 6784, 4160, 4992, 2560, 1600, 2368)
TAIL_FREE = 0x70F96C  # 0xFF from here to the 8 MiB end


@unittest.skipUnless(dec.ROM.is_file(), "no ROM dump in rom/")
class GraphicsSources(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = dec.ROM.read_bytes()

    def test_lz_scan_finds_170_blocks(self):
        self.assertEqual(sum(1 for _ in gbacomp.scan(self.d)), 170)

    def test_title_backgrounds_are_lz_8bpp(self):
        for off in TITLE_BG:
            out, _ = gbacomp.decompress(self.d, off)
            self.assertEqual(len(out), 38464, hex(off))

    def test_credits_blocks(self):
        for off, size in zip(CREDITS, CREDITS_SIZES):
            out, end = gbacomp.decompress(self.d, off)
            self.assertEqual(len(out), size, hex(off))
        self.assertLessEqual(end, TAIL_FREE)

    def test_tail_is_free(self):
        self.assertNotEqual(self.d[TAIL_FREE - 1], 0xFF)
        self.assertTrue(all(b == 0xFF for b in self.d[TAIL_FREE:]))
        self.assertEqual(len(self.d), 0x800000)


if __name__ == "__main__":
    unittest.main()
