"""dec.py: decode strings from the ROM with tbl/jp.tbl, for recon and spot checks.

    python -X utf8 tools/dec.py OFF [OFF..]        # file offsets in hex (0x08 prefix ok)
    python -X utf8 tools/dec.py --msg N [N..]      # message N of the table at 0x212B6C: every page
"""
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from tbl import Table  # noqa: E402

ROM = ROOT / "rom" / "Fantastic Children (Japan).gba"
MSG_TABLE, MSG_COUNT = 0x212B6C, 1528  # table ends at 0x21434C, where the page lists begin


def page(t, d, off):
    """Decode one page: stops after the first 0x80xx code."""
    out, o = [], off
    while True:
        key = d[o:o + 2]
        c = struct.unpack_from("<H", key)[0]
        if key in t.dec:
            out.append(t.dec[key])
        elif key in t.ctrl:
            out.append("{%s}" % t.ctrl[key][0])
        else:
            out.append("[%04X]" % c)
        o += 2
        if c & 0x8000:
            return "".join(out), o - off


def message(d, n):
    p = struct.unpack_from("<I", d, MSG_TABLE + 4 * n)[0] - 0x08000000
    pages = []
    while True:
        s = struct.unpack_from("<I", d, p)[0]
        if s == 0:
            return pages
        pages.append(s - 0x08000000)
        p += 4


def main():
    t = Table.load(ROOT / "tbl" / "jp.tbl")
    d = ROM.read_bytes()
    args = sys.argv[1:]
    if args and args[0] == "--msg":
        for n in args[1:]:
            for off in message(d, int(n, 0)):
                print(f"{n}\t{off:06X}\t{page(t, d, off)[0]}")
    else:
        for a in args:
            off = int(a, 16) & 0x1FFFFFF
            print(f"{off:06X}\t{page(t, d, off)[0]}")


if __name__ == "__main__":
    main()
