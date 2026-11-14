"""Phase 7 ROM-level checks on a fresh English build (built here, not read from build/).

- romdiff: no byte changes outside tools/allowed.py's ranges (free space, message table, pointer holders, 2 patches);
- the code patches swallow no branch target (+-4 KB of the original's Thumb code);
- every English row reads back from the built ROM through the game's own pointers (message table -> page lists ->
  pages; system-string holders), and rows without English keep their original bytes;
- no Japanese left in any English cell.
"""
import re
import struct
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))
import allowed  # noqa: E402
import build  # noqa: E402
import insert  # noqa: E402
import msgs  # noqa: E402
import vwf  # noqa: E402
from script_tsv import load  # noqa: E402

BUS = vwf.BUS


def u32(d, o):
    return struct.unpack_from("<I", d, o)[0]


def codes_at(d, off):
    codes, _ = msgs.page_codes(d, off)
    return list(struct.unpack(f"<{len(codes) // 2}H", codes)), struct.unpack_from("<H", d, off + len(codes))[0]


def message_pages(d):
    """{message id: [page file offsets]} through the table and page lists of ROM `d`."""
    out = {}
    for n in range(msgs.MSG_COUNT):
        p, offs = u32(d, msgs.MSG_TABLE + 4 * n) - BUS, []
        while u32(d, p):
            offs.append(u32(d, p) - BUS)
            p += 4
        out[n] = offs
    return out


@unittest.skipUnless(build.ROM.is_file(), "no ROM dump in rom/")
class EnglishRom(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from writelog import WriteLog
        cls.d = build.ROM.read_bytes()
        cls.log = WriteLog(cls.d)
        cls.out = insert.build_rom(cls.d, "en", log=cls.log)
        cls.rows = load()

    def test_no_change_outside_allowed_ranges(self):
        with tempfile.TemporaryDirectory() as t:
            p = Path(t) / "en.gba"
            p.write_bytes(self.out)
            rc, out = allowed.romdiff(build.ROM, p)
            self.assertEqual(rc, 0, out)
            # with the write log: every changed byte is a logged write inside the ranges, with the original's
            # bytes where it expects them, not overlapped or overwritten by another write
            rc, out = allowed.romdiff(build.ROM, p, self.log.save(Path(t) / "writes.txt"))
            self.assertEqual(rc, 0, out)

    def test_patches_swallow_no_branch_target(self):
        from capstone import CS_ARCH_ARM, CS_MODE_THUMB, Cs
        md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
        for start, n in ((vwf.TYPE_LINE + 2, 10), (vwf.UPLOAD_SKIP, 2)):
            o, pos, hits = start - BUS, start - BUS - 0x1000, []
            while pos < o + 0x1000:
                ins = list(md.disasm(self.d[pos:pos + 4], BUS + pos, count=1))
                if not ins:
                    pos += 2
                    continue
                i = ins[0]
                if i.mnemonic.startswith("b") and i.op_str.startswith("#") and start < int(i.op_str[1:], 16) < start + n:
                    hits.append(f"{i.address:#x} {i.mnemonic} {i.op_str}")
                pos += i.size
            self.assertEqual(hits, [], f"branch into the patch at {start:#x}")

    def test_every_page_reads_back(self):
        orig, new = message_pages(self.d), message_pages(self.out)
        checked = 0
        for n, offs in orig.items():
            want = []   # (English text, None) or (None, original bytes)
            for off in offs:
                en = self.rows.get(f"p{off:06X}", {}).get("en")
                if en:
                    want += [(t, None) for t in en.split(insert.LINE_SEP)]
                else:
                    want.append((None, self.d[off:off + msgs.page_codes(self.d, off)[1]]))
            self.assertEqual(len(new[n]), len(want), f"message {n}: page count")
            for off, (text, raw) in zip(new[n], want):
                if text is None:
                    self.assertEqual(self.out[off:off + len(raw)], raw, f"message {n} page {off:#x}")
                else:
                    codes, end = codes_at(self.out, off)
                    self.assertEqual(vwf.decode_pairs(codes), text, f"message {n} page {off:#x}")
                    self.assertEqual(end & 0xFF, len(codes))
                    checked += 1
        self.assertGreater(checked, 4000)

    def test_every_system_string_reads_back(self):
        n = 0
        for r in self.rows.values():
            if r["id"][0] != "s" or not r.get("en"):
                continue
            for h in r["ref"].split(","):
                codes, end = codes_at(self.out, u32(self.out, int(h, 16)) - BUS)
                text = vwf.decode_pairs(codes) + ("{endflag}" if end & 0x4000 else "")
                self.assertEqual(text, r["en"], r["id"])
                n += 1
        self.assertGreater(n, 300)

    def test_no_japanese_in_english(self):
        bad = [r["id"] for r in self.rows.values() if re.search(r"[぀-ヿ一-鿿]", r.get("en") or "")]
        self.assertEqual(bad, [])


if __name__ == "__main__":
    unittest.main()
