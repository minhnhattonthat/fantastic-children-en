"""Pin the event, area and mode tables the warp tool relies on (docs/re/events.md)."""
import struct
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from dec import ROM  # noqa: E402
from events import REC_BASE, REC_COUNT, REC_SIZE, areas, flow, flow_msgs, records, scripts  # noqa: E402


@unittest.skipUnless(ROM.exists(), "ROM not present")
class Events(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = ROM.read_bytes()
        cls.recs = records(cls.d)

    def test_record_table_ends_at_pages(self):
        self.assertEqual(REC_BASE + REC_SIZE * REC_COUNT, 0x7ECB4)  # first text page
        self.assertEqual(struct.unpack_from("<H", self.d, 0x30FEC + 0)[0] & 0xFF00, 0x4800)  # ldr r0,=0xA99
        self.assertEqual(struct.unpack_from("<I", self.d, 0x30FF0)[0], 0xA99)

    def test_flow_follows_choices_and_conditions(self):
        r = self.recs
        # record 66 asks choice 41 (+0x0E); answers jump to records 67 / 68 (+0x10 / +0x12), text 42 / 43
        self.assertTrue({67, 68} <= set(flow(r, 48)))
        self.assertIn(41, flow_msgs(r, 48))
        # record 82: jump to 48 if flag 0x12A is clear (the warp saw 32-34); set, it runs 82 -> 85 -> (86 ..)
        self.assertNotIn(32, flow_msgs(r, 82, False))
        self.assertEqual(flow_msgs(r, 82, True)[:3], [32, 33, 34])
        # record 1678 jumps to 1679 when flag 0x88 is clear (the new-game default): the warp saw 847, not 846
        self.assertEqual(flow_msgs(r, 1678, True), [847])
        self.assertEqual(flow_msgs(r, 1678, False), [846])

    def test_scene_list_covers_every_record_message(self):
        import re
        scenes = (ROOT / "tools" / "debug" / "scenes.gba.txt").read_text(encoding="utf-8")
        listed = {int(m) for ms in re.findall(r"\bmsg=([\d,]+)", scenes) for m in ms.split(",")}
        hand = {m for s in (43, 1986, 2311) for m in flow_msgs(self.recs, s)}
        shown = {x[6] for x in self.recs[37:] if x[6] != 0xFFFF}
        self.assertEqual(shown - listed - hand, set())

    def test_mode_table(self):
        want = [0x8032E99, 0x8033035, 0x80331A5, 0x8033CAD, 0x8038519, 0x803506D, 0x8035431, 0x8037955,
                0x803CDD1, 0x80375F5]
        self.assertEqual(list(struct.unpack_from("<10I", self.d, 0x219E28)), want)

    def test_areas(self):
        a = areas(self.d)
        self.assertEqual(len(a), 60)
        ent = dict(a)
        self.assertEqual(ent[0x16], 2262)   # new game's first area: "こ・・・ ここは・・・？"
        self.assertEqual(ent[0x01], 81)     # the house: tutorial

    def test_scripts(self):
        sc = scripts(self.recs)
        self.assertEqual(len(sc), 960)
        self.assertEqual(sum(1 for s in sc if s[2]), 470)
        battles = {b for s in sc for b in s[3]}
        self.assertEqual(len(battles), 88)
        start = {s[0]: s for s in sc}
        self.assertIn(1986, start)                      # ending
        self.assertEqual(self.recs[1986][0], 0x85)     # ending B branch
        self.assertEqual(self.recs[1986][1], 2067)
        self.assertEqual(self.recs[1987][0], 0x87)     # ending C branch
        self.assertEqual(self.recs[1987][1], 2185)

    def test_every_message_record_in_range(self):
        for r in self.recs:
            self.assertTrue(r[6] == 0xFFFF or r[6] < 1528)

    def test_scene_list_fresh(self):
        """tools/debug/scenes.gba.txt must be what gen_scenes.py writes now."""
        import subprocess
        txt = (ROOT / "tools" / "debug" / "scenes.gba.txt").read_text(encoding="utf-8")
        subprocess.run([sys.executable, "-X", "utf8", str(ROOT / "tools" / "debug" / "gen_scenes.py")],
                       check=True, capture_output=True)
        self.assertEqual((ROOT / "tools" / "debug" / "scenes.gba.txt").read_text(encoding="utf-8"), txt)


if __name__ == "__main__":
    unittest.main()
