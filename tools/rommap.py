"""rommap.py: coarse ROM map, one line per run of same-class chunks.

    python -X utf8 tools/rommap.py ROM [--chunk 0x800]

Classes per chunk: ff (fill), zero, lz (inside a BIOS-LZ77 block from gbacomp.scan), text (inside the page range),
gfx4 (looks like 4bpp tiles: many 0 nibbles, few distinct nibble values per tile), other (code / data / packed).
A guide for where to render graphics sheets; not proof of anything.
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gbacomp  # noqa: E402

TEXT = (0x7ECB4, 0x9C2B0)


def classify(c):
    if c.count(0xFF) > len(c) * 0.95:
        return "ff"
    if c.count(0) > len(c) * 0.95:
        return "zero"
    # 4bpp tile heuristic: per 32-byte tile, distinct nibble count small and zero nibble common
    good = 0
    tiles = len(c) // 32
    for t in range(tiles):
        b = c[t * 32:(t + 1) * 32]
        nib = [x & 15 for x in b] + [x >> 4 for x in b]
        if len(set(nib)) <= 6 and nib.count(0) >= 8:
            good += 1
    if good > tiles * 0.6:
        return "gfx4"
    return "other"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("rom")
    ap.add_argument("--chunk", type=lambda s: int(s, 0), default=0x800)
    a = ap.parse_args()
    rom = open(a.rom, "rb").read()
    lz = [(o, o + p) for o, p, _ in gbacomp.scan(rom)]
    li = 0
    runs = []
    for off in range(0, len(rom), a.chunk):
        while li < len(lz) and lz[li][1] <= off:
            li += 1
        if li < len(lz) and lz[li][0] < off + a.chunk and lz[li][1] > off and lz[li][0] <= off:
            k = "lz"
        elif TEXT[0] <= off < TEXT[1]:
            k = "text"
        else:
            k = classify(rom[off:off + a.chunk])
        if runs and runs[-1][2] == k:
            runs[-1][1] = off + a.chunk
        else:
            runs.append([off, off + a.chunk, k])
    for s, e, k in runs:
        print(f"{s:07X}-{e:07X}\t{(e - s) // 1024:5d}K\t{k}")


if __name__ == "__main__":
    main()
