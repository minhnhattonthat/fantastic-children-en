"""font_sheet.py: render the dialogue font by text code, for building tbl/jp.tbl.

    python -X utf8 tools/font_sheet.py ROM OUT.png [--font 0|1] [--mode 4bpp8x16|2bpp16x16|4bpp16x16] [--first 0] [--count 512]

Glyph lookup (docs/re/text.md): idx = u16 at *(PTRTAB[font] + (code & 0x1FF)*4); glyph = GLYPHS[font] + idx*64.
Each cell is labelled with its code in hex (row label = high part, 16 codes per row).
"""
import argparse
import struct
from PIL import Image, ImageDraw

ROM_BASE = 0x08000000
FONT_TABLE_GLYPHS = 0x2122D4  # u32 per font: glyph data base
FONT_TABLE_PTRS = 0x2122DC    # u32 per font: per-code pointer table


def u32(d, o):
    return struct.unpack_from("<I", d, o)[0]


def glyph_index(d, font, code):
    ptrtab = u32(d, FONT_TABLE_PTRS + font * 4) - ROM_BASE
    p = u32(d, ptrtab + (code & 0x1FF) * 4) - ROM_BASE
    return struct.unpack_from("<H", d, p)[0]


def glyph_pixels(d, font, code, mode):
    base = u32(d, FONT_TABLE_GLYPHS + font * 4) - ROM_BASE
    g = d[base + glyph_index(d, font, code) * 64:][:64]
    if mode == "4bpp8x16":  # two 8x8 4bpp tiles stacked
        w, h = 8, 16
        px = [[0] * w for _ in range(h)]
        for t in range(2):
            for y in range(8):
                for x in range(8):
                    b = g[t * 32 + y * 4 + x // 2]
                    px[t * 8 + y][x] = (b >> 4) if x & 1 else (b & 15)
        return px
    if mode == "4bpp16x16":  # 2x2 tiles, but only 64 bytes: show the first two tiles side by side
        w, h = 16, 8
        px = [[0] * w for _ in range(h)]
        for t in range(2):
            for y in range(8):
                for x in range(8):
                    b = g[t * 32 + y * 4 + x // 2]
                    px[y][t * 8 + x] = (b >> 4) if x & 1 else (b & 15)
        return px
    if mode == "2bpp16x16":  # linear 16x16, 2 bits per pixel, low bits first
        w, h = 16, 16
        px = [[0] * w for _ in range(h)]
        for y in range(16):
            for x in range(16):
                i = y * 16 + x
                px[y][x] = (g[i // 4] >> ((i % 4) * 2)) & 3
        return px
    raise SystemExit("unknown mode")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("rom")
    ap.add_argument("out")
    ap.add_argument("--font", type=int, default=0)
    ap.add_argument("--mode", default="4bpp8x16")
    ap.add_argument("--first", type=lambda s: int(s, 0), default=0)
    ap.add_argument("--count", type=lambda s: int(s, 0), default=512)
    ap.add_argument("--zoom", type=int, default=3)
    a = ap.parse_args()
    d = open(a.rom, "rb").read()
    sample = glyph_pixels(d, a.font, a.first, a.mode)
    gh, gw = len(sample), len(sample[0])
    cw, ch = gw * a.zoom + 4, gh * a.zoom + 14
    cols = 16
    rows = (a.count + cols - 1) // cols
    img = Image.new("RGB", (cols * cw + 40, rows * ch), (40, 40, 60))
    dr = ImageDraw.Draw(img)
    for i in range(a.count):
        code = a.first + i
        px = glyph_pixels(d, a.font, code, a.mode)
        mx = max(max(r) for r in px) or 1
        ox, oy = 40 + (i % cols) * cw, (i // cols) * ch
        dr.text((ox, oy), f"{code:03X}", fill=(255, 200, 80))
        for y in range(gh):
            for x in range(gw):
                v = px[y][x] * 255 // mx
                if v:
                    dr.rectangle([ox + x * a.zoom, oy + 12 + y * a.zoom, ox + x * a.zoom + a.zoom - 1,
                                  oy + 12 + y * a.zoom + a.zoom - 1], fill=(v, v, v))
        if i % cols == 0:
            dr.text((2, oy + 14), f"{code:03X}", fill=(120, 200, 255))
    img.save(a.out)
    print(a.out, img.size)


if __name__ == "__main__":
    main()
