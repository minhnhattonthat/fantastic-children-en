"""qa_grid.py: labelled grids of warp shots (<dir>/<scene>/warp.png) for reading marker ids or checking for Japanese.

    python -X utf8 tools/qa_grid.py work/qa/marker2 OUT_PREFIX [--scale 0.667] [--cols 6] [--per 48] [--only RE]
    python -X utf8 tools/qa_grid.py work/qa/marker2 OUT_PREFIX --scale 1 --cols 4 --per 20 --names ev_0160b ev_0125

Writes OUT_PREFIX_00.png, _01.png, ... with the scene name above each shot. Scale 1 reads ids and choice columns;
2/3 is enough to spot Japanese left in a box (the Phase 5 marker review read all 649 at 2/3).
"""
import argparse
import re
from pathlib import Path

from PIL import Image, ImageDraw


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("root", type=Path)
    ap.add_argument("out")
    ap.add_argument("--scale", type=float, default=2 / 3)
    ap.add_argument("--cols", type=int, default=6)
    ap.add_argument("--per", type=int, default=48)
    ap.add_argument("--only")
    ap.add_argument("--names", nargs="*")
    a = ap.parse_args()
    names = a.names or sorted(p.parent.name for p in a.root.glob("*/warp.png"))
    if a.only:
        names = [n for n in names if re.search(a.only, n)]
    w, h = round(240 * a.scale), round(160 * a.scale)
    for k in range(0, len(names), a.per):
        chunk = names[k:k + a.per]
        rows = (len(chunk) + a.cols - 1) // a.cols
        g = Image.new("RGB", (a.cols * w, rows * (h + 10)), "white")
        d = ImageDraw.Draw(g)
        for i, n in enumerate(chunk):
            x, y = (i % a.cols) * w, (i // a.cols) * (h + 10)
            p = a.root / n / "warp.png"
            if p.exists():
                g.paste(Image.open(p).convert("RGB").resize((w, h), Image.LANCZOS), (x, y + 10))
            d.text((x + 2, y - 1), n, fill="black")
        g.save(f"{a.out}_{k // a.per:02d}.png")
    print(f"{len(names)} shots -> {(len(names) + a.per - 1) // a.per} grids")


if __name__ == "__main__":
    main()
