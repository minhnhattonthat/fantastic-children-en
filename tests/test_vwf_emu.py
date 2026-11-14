"""VWF hook run in Unicorn (bug B1): the cells it draws match a pixel model, and every VRAM write it makes is already
the final value (no cleared or half-drawn state reaches the screen while the game re-types a line each frame)."""
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
    import unicorn as uc
    from unicorn import arm_const as A
    HAVE = True
except ImportError:
    HAVE = False

if HAVE:
    import vwf  # noqa: E402

OBJ, GLYBUF, SHADOW, SRC = 0x0202C790, 0x0202C7A8, 0x0202D44C, 0x02010000
VRAM, H = 0x06008000, 0x37F
SP, STOP = 0x03002A00, 0x02030000


@unittest.skipUnless(HAVE and build.ROM.is_file(), "needs unicorn, keystone-engine, pillow and the ROM")
class HookInUnicorn(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom = bytes(vwf.apply(bytearray(build.ROM.read_bytes())))
        cls.wid, cls.gly, cls.pw, cls.pg = vwf.tables(build.ROM.read_bytes())

    def setUp(self):
        m = uc.Uc(uc.UC_ARCH_ARM, uc.UC_MODE_THUMB)
        m.mem_map(0x08000000, 0x1000000)
        m.mem_write(0x08000000, self.rom)
        m.mem_map(0x02000000, 0x40000)
        m.mem_map(0x03000000, 0x8000)
        m.mem_map(0x06000000, 0x20000)
        self.m, self.writes = m, []
        m.hook_add(uc.UC_HOOK_MEM_WRITE, self._w)

    def _w(self, m, access, addr, size, value, data):
        self.writes.append((addr, size, value & ((1 << 8 * size) - 1)))

    def obj(self, font1=False, reset=True):
        m = self.m
        m.mem_write(OBJ, struct.pack("<HHIIIHBBbb", 0, 0, GLYBUF, VRAM, SHADOW, H, 1 if reset else 0, 0, 0, 0))
        m.mem_write(OBJ + 0x138, bytes([2 if font1 else 0]))

    def put(self, text, x, y, count=None, flags=0):
        codes = vwf.encode_pairs(text)
        m = self.m
        m.mem_write(SRC, struct.pack(f"<{len(codes) + 1}H", *codes, 0x8000 | len(codes)))
        m.mem_write(SP, struct.pack("<II", len(codes) if count is None else count, flags))
        for r, v in ((A.UC_ARM_REG_R0, OBJ), (A.UC_ARM_REG_R1, SRC), (A.UC_ARM_REG_R2, x), (A.UC_ARM_REG_R3, y),
                     (A.UC_ARM_REG_SP, SP), (A.UC_ARM_REG_LR, STOP | 1)):
            m.reg_write(r, v)
        self.writes = []
        m.emu_start(vwf.TYPE_LINE | 1, STOP, count=2_000_000)
        return codes

    def model(self, codes, bg):
        """Expected 4bpp pixels per row (16 rows) of the line, bg OR glyphs at their pens."""
        px = [[bg] * 256 for _ in range(16)]
        pen = 0
        for c in codes:
            if c & vwf.PAIR:
                parts = [(self.pw[i], self.pg[i * 128:i * 128 + 128]) for i in (c >> 7 & 0x7F, c & 0x7F)]
            elif c & 0x0E00 == 0x0200:
                continue
            else:
                parts = [(self.wid[c & 0x1FF], self.gly[(c & 0x1FF) * 128:(c & 0x1FF) * 128 + 128])]
            for w, g in parts:
                for r in range(16):
                    lo, hi = struct.unpack_from("<II", g, r * 8)
                    for i in range(16):
                        v = ((lo if i < 8 else hi) >> (4 * (i & 7))) & 15
                        px[r][pen + i] |= v
                pen += w
        return px, (pen + 6) // 8

    def cells(self, ncells, n0=0):
        """Pixels of the hook's cells 0..ncells-1 read back from VRAM (cell a = tiles h-1-2n0-2a, +1)."""
        t0 = H - 1 - 2 * n0
        px = [[0] * (8 * ncells) for _ in range(16)]
        for a in range(ncells):
            d = self.m.mem_read(VRAM + (t0 - 2 * a) * 32, 64)
            for r in range(16):
                w = struct.unpack_from("<I", d, r * 4)[0]
                for i in range(8):
                    px[r][8 * a + i] = (w >> (4 * i)) & 15
        return px

    def check_line(self, text, font1):
        self.obj(font1)
        self.m.mem_write(VRAM, bytes([0x5A]) * 0x8000)          # garbage under the cells
        codes = self.put(text, 3, 15)
        want, ncells = self.model(codes, 1 if font1 else 0)
        got = self.cells(ncells)
        self.assertEqual([r[:8 * ncells] for r in want], got, text)
        n = struct.unpack("<H", self.m.mem_read(OBJ + 2, 2))[0]
        self.assertEqual(n, ncells)
        return ncells

    def test_cells_match_model(self):
        for text, font1 in (("Hold it down and branches.", False), ("Mmm, we walked the whole w'", True),
                            ("iiii lll WWW ...", False), ("A", True)):
            self.check_line(text, font1)

    def test_retype_writes_only_final_values(self):
        """The game re-types a shown line every frame: with the cells already drawn, a re-type (and a reveal step)
        must not write anything to VRAM that is not the final value of that word."""
        text = "Hold it down and branches."
        for count_before, count_now in ((None, None), (10, 11)):
            self.obj()
            self.m.mem_write(VRAM, bytes(0x8000))
            self.put(text, 3, 15, count_before)
            self.obj()                                            # next frame: n reset by the "uploaded" flag
            self.put(text, 3, 15, count_now)
            vram = [(a, s, v) for a, s, v in self.writes if 0x06000000 <= a < 0x06020000]
            self.assertTrue(vram)
            for a, s, v in vram:
                final = int.from_bytes(self.m.mem_read(a, s), "little")
                self.assertEqual(v, final, f"{a:#x}: wrote {v:#x}, ends as {final:#x}")

    def test_ram_writes_stay_in_known_places(self):
        self.obj()
        self.put("W" * 40, 0, 15)                                 # past the 30-cell draw limit: no stray writes
        lo, hi = vwf.SCRATCH, vwf.SCRATCH + 64 * vwf.SCRATCH_CELLS
        for a, s, v in self.writes:
            ok = (lo <= a < hi or OBJ <= a < OBJ + 0x18 or GLYBUF <= a < GLYBUF + 16 or SHADOW <= a < SHADOW + 0x800
                  or SP - 0x100 <= a < SP or 0x06000000 <= a < 0x06020000)
            self.assertTrue(ok, hex(a))


if __name__ == "__main__":
    unittest.main()
