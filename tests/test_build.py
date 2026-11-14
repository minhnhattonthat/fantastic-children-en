"""Phase 3 identity build: unpack -> repack with no edits gives the dump back, byte for byte."""
import struct
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))
import build  # noqa: E402
import gbacomp  # noqa: E402
import msgs  # noqa: E402


@unittest.skipUnless(build.ROM.is_file(), "no ROM dump in rom/")
class Identity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = build.ROM.read_bytes()
        cls.s = msgs.Script.unpack(cls.d)

    def test_identity_build_is_byte_identical(self):
        self.assertEqual(build.repack(self.d), self.d)

    def test_every_page_roundtrips(self):
        for off, text in self.s.pages.items():
            self.assertEqual(self.s.encode_page(text), self.d[off:off + self.s.sizes[off]], hex(off))

    def test_shape(self):
        self.assertEqual(len(self.s.pages), 4133)
        self.assertEqual(len(self.s.table), msgs.MSG_COUNT)

    def test_relocated_build_reads_back_the_same_script(self):
        out = self.s.repack(self.d, base=0x710000)
        self.assertEqual(len(out), len(self.d))
        self.assertEqual(struct.unpack_from("<I", out, msgs.MSG_TABLE)[0] >> 24, 0x08)
        # read the relocated ROM the way the game does: table -> list -> page
        for n in range(msgs.MSG_COUNT):
            p = struct.unpack_from("<I", out, msgs.MSG_TABLE + 4 * n)[0] - msgs.BUS
            self.assertGreaterEqual(p, 0x710000)
            want = [self.s.pages[o] for o in self.s.messages()[n][1]]
            got = []
            while (w := struct.unpack_from("<I", out, p)[0]):
                codes, _ = msgs.page_codes(out, w - msgs.BUS)
                got.append(self.s.tbl.decode(codes, 0, len(codes))[0])
                p += 4
            self.assertEqual(got, want, n)
        # nothing outside the table and the free tail changed
        self.assertEqual(out[:msgs.MSG_TABLE], self.d[:msgs.MSG_TABLE])
        self.assertEqual(out[msgs.MSG_TABLE + 4 * msgs.MSG_COUNT:0x710000],
                         self.d[msgs.MSG_TABLE + 4 * msgs.MSG_COUNT:0x710000])

    def test_lz_codec_roundtrips(self):
        # graphics pass through untouched until redrawn; edited blocks get recompressed. The pure-Python
        # compressor runs ~10 KB/s, so the check samples every 17th block (10 of 170, ~15 s) to fit pre-commit.
        blocks = list(gbacomp.scan(self.d))
        self.assertEqual(len(blocks), 170)
        for off, *_ in blocks[::17]:
            raw, _ = gbacomp.decompress(self.d, off)
            self.assertEqual(gbacomp.decompress(gbacomp.compress(raw))[0], raw, hex(off))


if __name__ == "__main__":
    unittest.main()
