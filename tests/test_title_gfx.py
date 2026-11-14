"""title_gfx.py (G1/G2 title backgrounds): export -> import is lossless and the records point at the blocks."""
import struct
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))
import build  # noqa: E402

try:
    import PIL  # noqa: F401
    HAVE = True
except ImportError:
    HAVE = False


@unittest.skipUnless(HAVE and build.ROM.is_file(), "needs pillow and the ROM")
class TitleGfx(unittest.TestCase):
    def test_roundtrip_and_moved_record(self):
        import gbacomp
        import title_gfx
        rom = build.ROM.read_bytes()
        with tempfile.TemporaryDirectory() as td:
            for n, b in enumerate(title_gfx.BLOCKS):
                self.assertEqual(title_gfx.slot(rom, n) % 4, 0)
                im, _ = title_gfx.to_png(rom, b)
                p = Path(td) / f"title_{n}.png"
                im.save(p)
                self.assertEqual(title_gfx.tiles_from_png(rom, b, p), gbacomp.decompress(rom, b)[0])
            out = bytearray(rom)
            big = title_gfx.slot(rom, 3) - 4                      # force a move: pretend the slot is smaller
            struct.pack_into("<I", out, title_gfx.RECORDS[3] + 4, big)
            title_gfx.apply(out, 3, Path(td) / "title_3.png", alloc=lambda size: 0x7F0000)
            off, size = struct.unpack_from("<II", out, title_gfx.RECORDS[3])
            self.assertEqual(title_gfx.RECORDS[3] + off, 0x7F0000)
            self.assertEqual(gbacomp.decompress(bytes(out), 0x7F0000)[0], gbacomp.decompress(rom, title_gfx.BLOCKS[3])[0])


if __name__ == "__main__":
    unittest.main()
