"""flicker.py: find one-frame text glitches in a --shot-every run (bug B1 check).

    python -X utf8 tools/flicker.py DIR [DIR2 ..] [--from 1990 --to 2300] [--box x0,y0,x1,y1 ..]

Per box (default: the text cells of both boxes, ▼ excluded: top box x 8-176, y 24-56; bottom box x 24-216,
y 120-152), reports "flickers": a shot whose crop differs from the shot before while the shot after is identical to
the one before (A, B, A). Typing only moves forward (A, B, C) and a page change does not come back, so A-B-A in the
text cells is a line shown half drawn (or otherwise wrong) for a frame. Exit 1 if any dir has one.
"""
import argparse
import sys
from pathlib import Path

from PIL import Image


def flickers(d, lo, hi, box):
    shots = sorted(p for p in Path(d).glob("f[0-9]*.png") if lo <= int(p.stem[1:]) <= hi)
    seq = [(int(p.stem[1:]), Image.open(p).convert("RGB").crop(box).tobytes()) for p in shots]
    return len(seq), [seq[i][0] for i in range(1, len(seq) - 1)
                      if seq[i][1] != seq[i - 1][1] and seq[i + 1][1] == seq[i - 1][1]]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dirs", nargs="+")
    ap.add_argument("--from", dest="lo", type=int, default=0)
    ap.add_argument("--to", dest="hi", type=int, default=10 ** 7)
    ap.add_argument("--box", nargs="*", default=["8,24,176,56", "24,120,216,152"])
    a = ap.parse_args()
    bad = 0
    for d in a.dirs:
        for b in a.box:
            n, fs = flickers(d, a.lo, a.hi, tuple(int(v) for v in b.split(",")))
            print(f"{d} box {b}: {n} shots, {len(fs)} flickers {fs[:12]}")
            bad += bool(fs)
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
