"""Phase 4 extraction: script/*.tsv holds every string, re-encodes to the original bytes, and covers the text ranges."""
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import msgs  # noqa: E402
import script_tsv as st  # noqa: E402
from tbl import Table  # noqa: E402

# Data blocks inside or between the text ranges, each checked by hand (docs/re/text.md §Text inventory)
DATA_GAPS = {
    (0x9C140, 0x9C610),  # records (u16 pairs), pointer from code at 0x3112C
    (0x9CFB2, 0x9CFB4),  # 2-byte pad (0x0000) before a 4-aligned string
    (0x9D030, 0x9D510),  # u16 lists, pointers from the table at 0x219F90
    (0x9F6B4, 0x9F6C4),  # u16 0..7, pointer from code at 0x373DC
}


@unittest.skipUnless(st.ROM.is_file(), "no ROM dump in rom/")
class Extract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = st.ROM.read_bytes()
        cls.tbl = Table.load(ROOT / "tbl" / "jp.tbl")
        cls.rows = st.rom_rows(cls.d, cls.tbl)
        cls.tsv = st.load()

    def test_roundtrip(self):
        """Re-encoding every jp in script/ (+ the end code) gives the ROM bytes at its id."""
        for rid, r in self.tsv.items():
            off = int(rid[1:], 16)
            b = st.encode(self.tbl, r["jp"])
            self.assertEqual(b, self.d[off:off + len(b)], rid)

    def test_tsv_matches_rom(self):
        """script/ has exactly the ROM's strings with the ROM's jp and ref (catches table edits not re-extracted)."""
        self.assertEqual(set(self.tsv), {r.id for r in self.rows})
        for r in self.rows:
            t = self.tsv[r.id]
            self.assertEqual((t["jp"], t["ref"], t["file"]), (r.jp, r.ref, r.file), r.id)

    def test_no_unknown_codes(self):
        bad = [r.id for r in self.rows if "[" in r.jp]
        self.assertEqual(bad, [])

    def test_coverage(self):
        """Strings + listed data blocks tile each text area with no gap and no overlap."""
        spans = sorted([(r.off, r.off + r.size) for r in self.rows] + list(DATA_GAPS))
        areas = [(msgs.PAGES, 0xA0632), (0x669F4, 0x66A04)]
        for lo, hi in areas:
            cur = lo
            for a, b in spans:
                if lo <= a < hi:
                    self.assertEqual(a, cur, f"gap or overlap at {cur:#x}")
                    cur = b
            self.assertEqual(cur, hi)

    def test_every_page_and_message(self):
        s = msgs.Script.unpack(self.d, self.tbl)
        pages = {r.off for r in self.rows if r.id[0] == "p"}
        self.assertEqual(pages, set(s.pages))
        shown = {ref.split(".")[0] for r in self.rows if r.id[0] == "p" for ref in r.ref.split(",")}
        self.assertEqual(shown, {f"m{n}" for n in range(msgs.MSG_COUNT)})

    def test_system_strings_have_pointers(self):
        """Every system string is reached by a pointer from code or the tables, so relocating it can repoint."""
        orphans = {r.id for r in self.rows if r.id[0] == "s" and not r.ref}
        self.assertEqual(orphans, set())
        holders = st.sys_holders(self.d)
        starts = {r.off for r in self.rows if r.id[0] == "s"}
        self.assertEqual(set(holders) - starts, set(), "a pointer lands inside a system string")

    def test_reextract_keeps_english(self):
        with tempfile.TemporaryDirectory() as tmp:
            wrote, _ = st.extract(self.d, folder=tmp)
            path = Path(tmp) / "msg_0100.tsv"
            rows = st.read_tsv(path)
            rows[0]["en"], rows[0]["notes"] = " Let's go!", "kept"
            st.write_tsv(path, rows)
            self.assertEqual(st.extract(self.d, folder=tmp), ([], wrote))  # no --force: nothing rewritten
            st.extract(self.d, force=True, folder=tmp)
            r = st.load(tmp)[rows[0]["id"]]
            self.assertEqual((r["en"], r["notes"]), (" Let's go!", "kept"))

    def test_counts(self):
        self.assertEqual(sum(r.id[0] == "p" for r in self.rows), 4133)
        self.assertEqual(sum(r.id[0] == "s" for r in self.rows), 530)


if __name__ == "__main__":
    unittest.main()
