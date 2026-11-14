"""boxmap.py: measured box budgets from emulator logs -> docs/re/msg_boxes.tsv and docs/re/sys_regions.tsv.

    python -X utf8 tools/boxmap.py LOGDIR [LOGDIR ...]     # merge into the existing files (never drops a row)

Reads every */log.txt under each LOGDIR:
  - `BOX f type=T` (tools/lua/boxlog.lua) then `fN MSG id` (warp.lua): the message is shown in the box last opened:
    type 0 = top box (portrait, 21 cells), else bottom box (24 cells with the VWF hook);
  - `PUT f src=ADDR x= y= n=CELLS lr=` (tools/lua/textput.lua, run on the ORIGINAL ROM): a system string drawn with
    a region of CELLS cells.
A message seen in both boxes is `top` (the smaller budget); a string drawn with several regions keeps the smallest.
The width lint (tools/lint.py) reads both files.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BOXES = ROOT / "docs" / "re" / "msg_boxes.tsv"
REGIONS = ROOT / "docs" / "re" / "sys_regions.tsv"
sys.path.insert(0, str(ROOT / "tools"))


def read(path, cols):
    out = {}
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines()[1:]:
            if line:
                f = line.split("\t")
                out[f[0]] = f[1:]
    return out


def write(path, header, rows):
    lines = ["\t".join(header)] + ["\t".join([k] + v) for k, v in sorted(rows.items())]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def main(dirs):
    from script_tsv import SYS_RANGES
    boxes = read(BOXES, 2)        # msg id -> [box, scene]
    regions = read(REGIONS, 4)    # string id -> [cells, x, y, scene]
    for d in dirs:
        for log in Path(d).glob("*/log.txt"):
            scene = log.parent.name
            box = None
            for line in log.read_text(encoding="utf-8", errors="replace").splitlines():
                m = re.match(r"BOX \d+ type=(\d+)", line)
                if m:
                    box = "top" if m[1] == "0" else "bottom"
                    continue
                m = re.match(r"f\d+ MSG (\d+)", line)
                if m and box:
                    k = m[1]
                    if k not in boxes or (boxes[k][0] == "bottom" and box == "top"):
                        boxes[k] = [box, scene]
                    continue
                m = re.match(r"PUT \d+ src=(\w+) x=(\d+) y=(\d+) n=(\d+)", line)
                if m:
                    off = int(m[1], 16) - 0x08000000
                    if not any(a <= off < b for _, a, b in SYS_RANGES):
                        continue
                    k = f"s{off:06X}"
                    if k not in regions or int(m[4]) < int(regions[k][0]):
                        regions[k] = [m[4], m[2], m[3], scene]
    write(BOXES, ["msg", "box", "scene"], boxes)
    write(REGIONS, ["id", "cells", "x", "y", "scene"], regions)
    print(f"{BOXES.relative_to(ROOT)}: {len(boxes)} messages; {REGIONS.relative_to(ROOT)}: {len(regions)} strings")


if __name__ == "__main__":
    main(sys.argv[1:])
