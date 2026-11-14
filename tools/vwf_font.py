"""vwf_font.py: the English VWF font (see docs/re/text.md §VWF and docs/fonts.md).

    python -X utf8 tools/vwf_font.py render TTF [--size 13]   # TTF -> fonts/vwf_en.png + fonts/vwf_en.tsv
    python -X utf8 tools/vwf_font.py sheet OUT.png             # zoomed preview of fonts/vwf_en.png

    from vwf_font import load
    glyphs = load()   # {char: (width, rows)}; rows = 16 lists of 16 pixel levels 0-15

The game's font is 16-level antialiased (pixel value = intensity, 4bpp), 8x16 per cell. English glyphs are stored up
to 16 px wide (two cells) so W/M fit; `width` is the advance in pixels. fonts/vwf_en.png is the source of truth
the build reads (cells of 16x16 in a 16-column grid, grey level 17*v), fonts/vwf_en.tsv lists char and width per cell
in the same order. Hand-edit the PNG to touch up a glyph; `render` overwrites both files.
"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FONTS = ROOT / "fonts"
PNG, TSV = FONTS / "vwf_en.png", FONTS / "vwf_en.tsv"
CELL = 16
COLS = 16
# every character the English table can encode, in sheet order; space first
CHARS = (" " + "".join(chr(c) for c in range(0x21, 0x7F) if chr(c) not in "\\`{}[]|^_<>@#")
         + "…—‘’“”é")   # ♪ × ▼ ▶ and the rest keep the game's own glyph at width 8
BASELINE = 12          # row of the baseline (cap height ~10 px at size 13)
SPACE_W = 3
GAP = 1                # extra pixel after each glyph's ink


def render(ttf, size):
    from PIL import Image, ImageDraw, ImageFont
    font = ImageFont.truetype(str(ttf), size)
    asc, _ = font.getmetrics()
    sheet = Image.new("L", (COLS * CELL, (len(CHARS) + COLS - 1) // COLS * CELL), 0)
    rows = []
    for i, ch in enumerate(CHARS):
        cell = Image.new("L", (CELL * 2, CELL), 0)
        if ch != " ":
            ImageDraw.Draw(cell).text((1, BASELINE - asc), ch, font=font, fill=255)
        px = cell.load()
        cols = [x for x in range(CELL * 2) if any(px[x, y] > 40 for y in range(CELL))]
        if cols:
            left = min(cols)
            ink = max(cols) - left + 1
        else:
            left, ink = 0, 0
        if ink > CELL - GAP:
            raise SystemExit(f"{ch!r} is {ink} px wide, > {CELL - GAP}")
        width = SPACE_W if ch == " " else ink + GAP
        out = Image.new("L", (CELL, CELL), 0)
        out.paste(cell.crop((left, 0, left + CELL, CELL)), (0, 0))
        # 0-255 -> 0-15 with a mild boost so thin strokes stay bright on the dark box
        out = out.point(lambda v: min(15, round((v / 255) ** 0.8 * 15)) * 17)
        sheet.paste(out, (i % COLS * CELL, i // COLS * CELL))
        rows.append((ch, width))
    FONTS.mkdir(exist_ok=True)
    sheet.save(PNG)
    lines = ["char\twidth"] + [f"{'U+%04X' % ord(c)}\t{w}" for c, w in rows]
    TSV.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    print(f"{PNG.relative_to(ROOT)}: {len(rows)} glyphs")


def load():
    from PIL import Image
    im = Image.open(PNG).convert("L")
    px = im.load()
    lines = TSV.read_text(encoding="utf-8").split("\n")[1:]
    out = {}
    for i, line in enumerate(l for l in lines if l):
        code, w = line.split("\t")
        ch = chr(int(code[2:], 16))
        x0, y0 = i % COLS * CELL, i // COLS * CELL
        rows = [[round(px[x0 + x, y0 + y] / 17) for x in range(CELL)] for y in range(CELL)]
        if any(v for r in rows for v in r[int(w):]) and ch != " ":
            raise ValueError(f"glyph {ch!r} has ink past its width {w}")
        out[ch] = (int(w), rows)
    return out


def sheet(out):
    from PIL import Image
    im = Image.open(PNG)
    im.resize((im.width * 4, im.height * 4), Image.NEAREST).save(out)
    print(out)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("render")
    r.add_argument("ttf")
    r.add_argument("--size", type=int, default=13)
    s = sub.add_parser("sheet")
    s.add_argument("out")
    a = ap.parse_args()
    if a.cmd == "render":
        render(a.ttf, a.size)
    else:
        sheet(a.out)


if __name__ == "__main__":
    sys.exit(main())
