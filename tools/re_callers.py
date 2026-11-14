"""re_callers.py: list every BL to a function with the few instructions before it (argument set-up).

    python -X utf8 tools/re_callers.py TARGET [--before N]

TARGET is a bus address (hex). Uses capstone like the skill's disasm.py. Recon helper for the warp tool.
"""
import argparse
import struct
from pathlib import Path

from capstone import CS_ARCH_ARM, CS_MODE_THUMB, Cs

ROM = Path(__file__).resolve().parents[1] / "rom" / "Fantastic Children (Japan).gba"


def bl_target(d, o):
    h, l = struct.unpack_from("<HH", d, o)
    if (h & 0xF800) != 0xF000 or (l & 0xF800) != 0xF800:
        return None
    off = ((h & 0x7FF) << 12) | ((l & 0x7FF) << 1)
    if off & 0x400000:
        off -= 0x800000
    return 0x08000000 + o + 4 + off


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("target")
    ap.add_argument("--before", type=int, default=4)
    a = ap.parse_args()
    t = int(a.target, 16) & ~1
    d = ROM.read_bytes()
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
    for o in range(0, 0x200000, 2):
        if bl_target(d, o) != t:
            continue
        start = o - 2 * a.before
        ins = [f"{i.mnemonic} {i.op_str}" for i in md.disasm(d[start:o], 0x08000000 + start)]
        print(f"{0x08000000 + o:08X}  " + " ; ".join(ins))


if __name__ == "__main__":
    main()
