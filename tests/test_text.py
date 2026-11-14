import struct
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import dec  # noqa: E402


@unittest.skipUnless(dec.ROM.is_file(), "no ROM dump in rom/")
class PageFormat(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = dec.ROM.read_bytes()

    def test_every_page_end_code_holds_its_char_count(self):
        pages = {off for n in range(dec.MSG_COUNT) for off in dec.message(self.d, n)}
        self.assertEqual(len(pages), 4133)
        for off in pages:
            o, n = off, 0
            while True:
                c = struct.unpack_from("<H", self.d, o)[0]
                o += 2
                if c & 0x8000:
                    self.assertEqual(c & 0xFF, n, hex(off))
                    break
                self.assertLess(c, 0x200, hex(off))
                n += 1

    def test_known_page_decodes(self):
        from tbl import Table
        t = Table.load(ROOT / "tbl" / "jp.tbl")
        text, _ = dec.page(t, self.d, 0x7F236)
        self.assertTrue(text.startswith("・"))
        self.assertIn("くから なみのおとが", text)
        self.assertTrue(text.endswith("{end15}"))


if __name__ == "__main__":
    unittest.main()
