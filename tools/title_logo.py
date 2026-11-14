"""title_logo.py: draw the English title logo (G1) and copyright lines (G2) into the 4 title backgrounds.

    python -X utf8 tools/title_logo.py FONT.ttf [OUTDIR]     # -> gfx/title_<n>.png (8bpp, each variant's own palette)
    python -X utf8 tools/title_logo.py FONT.ttf --preview P  # RGB sheet of the 4 results (2x) to look at

How (docs/re/graphics.md §Title backgrounds):
- The logo and copyright are the same art in all 4 variants, the backgrounds differ, so the old text is every pixel of
  the logo band / copyright band whose colour agrees across the 4 (dilated 1 px). Those pixels are inpainted per
  variant by diffusion from the surrounding background.
- The new logo ("FANTASTIC CHILDREN", one line) is drawn hard-edged in the old logo's colours: cyan-to-blue gradient
  fill, light rim, navy outline and drop shadow (colours sampled from the original art, constants below).
- The copyright lines use the game's own 8x8 ASCII font (G6, ROM 0x40000, tile = ASCII - 0x19), proportional,
  white with a dark outline, like the original lines.
- Only changed pixels are re-quantized, to the nearest colour among palette indices 64-255 (0-63 are loaded at run
  time for the other layers), so the rest of each picture keeps its exact indices.
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import title_gfx  # noqa: E402

ROM = ROOT / "rom" / "Fantastic Children (Japan).gba"
LOGO_BAND = (18, 74)          # rows holding the old logo (small Latin wordmark + katakana)
COPY_BAND = (128, 160)        # rows holding the old copyright lines
AGREE = 40                    # max channel spread across the 4 variants for "old text" pixels
LOGO_GROW = 4                 # extra dilation in the logo band (translucent shadow)
TEXT = "FANTASTIC CHILDREN"
LOGO_BOX = (4, 28, 236, 72)   # x0, y0, x1, y1 the logo is centred in (outlines and extrusion included)
CAP, TRACK, SPACE, BOLDEN = 22, 3, 7, False   # cap height, px between letters, word space, thicken stems 1 px
TOP, BOTTOM = (24, 72, 232), (150, 240, 255)   # fill gradient (original logo: blue top, light cyan bottom)
RIM, SILVER, EDGE, SHADOW = (248, 248, 248), (176, 176, 200), (8, 8, 48), (16, 24, 96)
COPY = ["\x7fT.NAKAMURA/NIPPON ANIMATION", "FC PRODUCTION COMMITTEE 2004", "\x7f BANDAI 2005"]
COPY_Y = (128, 138, 149)      # top row of each copyright line
WHITE, INK = (248, 248, 248), (16, 16, 32)


def originals(rom):
    out = []
    for b in title_gfx.BLOCKS:
        im, _ = title_gfx.to_png(rom, b)
        out.append(im)
    return out


def old_text_mask(rgbs):
    a = np.stack(rgbs).astype(int)                    # 4,H,W,3
    spread = (a.max(0) - a.min(0)).max(-1)            # H,W
    m = spread <= AGREE
    band = np.zeros_like(m)
    band[LOGO_BAND[0]:LOGO_BAND[1]] = True
    band[COPY_BAND[0]:COPY_BAND[1]] = True
    m &= band
    d = m.copy()          # dilate 1 px; the logo's drop shadow is translucent (differs per variant): 4 px there
    for r, rows in ((1, slice(None)), (LOGO_GROW, slice(*LOGO_BAND))):
        for dy in range(-r, r + 1):
            for dx in range(-r, r + 1):
                d[rows] |= np.roll(np.roll(m, dy, 0), dx, 1)[rows]
    return d & band


def inpaint(rgb, mask, iters=600):
    img = rgb.astype(float)
    known = ~mask
    img[mask] = 0
    for _ in range(iters):
        acc = np.zeros_like(img)
        n = np.zeros(mask.shape)
        for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            k = np.roll(np.roll(known, dy, 0), dx, 1)
            acc += np.roll(np.roll(img, dy, 0), dx, 1) * k[..., None]
            n += k
        fill = mask & (n > 0)
        img[fill] = acc[fill] / n[fill][:, None]
        known = known | fill
    return img


def logo_layer(font_path):
    """RGBA 240x160: the English logo, hard-edged, fitted into LOGO_BOX."""
    big = 8                                    # render 8x, one glyph at a time, then scale down (no squash)
    f = ImageFont.truetype(str(font_path), 100 * big)
    cx0, cy0, cx1, cy1 = f.getbbox("H")
    scale = CAP / (cy1 - cy0)                  # final px per big px
    cols, x = [], 0
    for ch in TEXT:
        if ch == " ":
            x += SPACE
            continue
        gx0, _, gx1, _ = f.getbbox(ch)
        gw = round((gx1 - gx0) * scale)
        im = Image.new("L", (gx1 - gx0 + 2 * big, cy1 - cy0))
        ImageDraw.Draw(im).text((big - gx0, -cy0), ch, font=f, fill=255)
        g = np.array(im.resize((gw + round(2 * big * scale), CAP), Image.LANCZOS)) >= 128
        g = g[:, g.any(0)]
        g = g | np.roll(g, 1, 1) if BOLDEN else g          # 1 px heavier stems
        cols.append((x, g))
        x += g.shape[1] + TRACK
    w, h = x - TRACK, CAP
    assert w + 8 <= LOGO_BOX[2] - LOGO_BOX[0], f"logo {w} px wide: lower CAP or TRACK"
    core = np.zeros((h, w), bool)
    for gx, g in cols:
        core[:, gx:gx + g.shape[1]] |= g

    def grow(m, r=1):
        o = m.copy()
        for dy in range(-r, r + 1):
            for dx in range(-r, r + 1):
                o |= np.roll(np.roll(m, dy, 0), dx, 1)
        return o

    pad = np.zeros((h + 8, w + 8), bool)      # 2 px outlines + 3 px extrusion
    pad[2:2 + h, 2:2 + w] = core
    core = pad
    silver = grow(core)                       # the original: silver outline, dark rim, navy extrusion down-right
    dark = grow(silver)
    shadow = np.zeros_like(dark)
    for k in range(1, 4):
        shadow |= np.roll(np.roll(dark, k, 0), k, 1)
    hi = silver & ~np.roll(silver, 1, 0)      # top edge of the outline catches the light
    H, W = core.shape
    rgba = np.zeros((H, W, 4), np.uint8)
    rgba[shadow] = (*SHADOW, 255)
    rgba[dark] = (*EDGE, 255)
    rgba[silver] = (*SILVER, 255)
    rgba[hi] = (*RIM, 255)
    ys = np.nonzero(core.any(1))[0]
    for y in range(H):
        t = 0 if len(ys) < 2 else min(1, max(0, (y - ys[0]) / (ys[-1] - ys[0])))
        c = tuple(int(TOP[i] + (BOTTOM[i] - TOP[i]) * t) for i in range(3))
        rgba[y][core[y]] = (*c, 255)
    out = Image.new("RGBA", (240, 160))
    ox = LOGO_BOX[0] + (LOGO_BOX[2] - LOGO_BOX[0] - W) // 2
    oy = LOGO_BOX[1] + (LOGO_BOX[3] - LOGO_BOX[1] - H) // 2
    out.paste(Image.fromarray(rgba, "RGBA"), (ox, oy))
    return out


HAND = {   # copyright sign (not in G6); R redrawn: G6's own R has a closed foot and reads as B
    "\x7f": ["..####..", ".#....#.", "#..##..#", "#.#....#", "#.#....#", "#..##..#", ".#....#.", "..####.."],
    "R": ["######..", "#######.", ".##..##.", ".######.", ".#####..", ".##.###.", "###..###", "###..###"],
}


def g6_glyph(rom, ch):
    """8x8 bool array of the game's G6 font; '\x7f' = the copyright sign drawn by hand."""
    if ch in HAND:
        return np.array([[c == "#" for c in r] for r in HAND[ch]])
    t = ord(ch) - 0x19
    d = rom[0x40000 + t * 32:0x40000 + t * 32 + 32]
    return np.array([[(d[(y * 8 + x) // 2] >> (4 * (x & 1))) & 15 != 0 for x in range(8)] for y in range(8)])


def copy_layer(rom):
    out = np.zeros((160, 240, 4), np.uint8)
    for line, y in zip(COPY, COPY_Y):
        glyphs = []
        for ch in line:
            if ch == " ":
                glyphs.append(np.zeros((8, 3), bool))
                continue
            g = g6_glyph(rom, ch)
            cols = np.nonzero(g.any(0))[0]
            glyphs.append(g[:, cols[0]:cols[-1] + 1])
        width = sum(g.shape[1] + 1 for g in glyphs) - 1
        assert width <= 236, (line, width)
        ink = np.zeros((160, 240), bool)
        x = (240 - width) // 2
        for g in glyphs:
            ink[y:y + 8, x:x + g.shape[1]] |= g
            x += g.shape[1] + 1
        edge = ink.copy()
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                edge |= np.roll(np.roll(ink, dy, 0), dx, 1)
        out[edge & ~ink] = (*INK, 255)
        out[ink] = (*WHITE, 255)
    return Image.fromarray(out, "RGBA")


def build(font_path, rom):
    ims = originals(rom)
    rgbs = [np.array(im.convert("RGB")) for im in ims]
    mask = old_text_mask(rgbs)
    logo = np.array(logo_layer(font_path))
    cpy = np.array(copy_layer(rom))
    over = np.zeros((160, 240, 4), np.uint8)
    for layer in (logo, cpy):
        a = layer[..., 3] > 0
        over[a] = layer[a]
    drawn = over[..., 3] > 0
    results = []
    for im, rgb in zip(ims, rgbs):
        pal = np.array(im.getpalette()[:768]).reshape(256, 3)[64:].astype(int)
        filled = inpaint(rgb, mask)        # all of it: old pixels under the new letters must not seed the fill
        filled[drawn] = over[drawn][:, :3]
        change = mask | drawn
        idx = np.array(im).copy()
        pts = filled[change]
        d = ((pts[:, None, :] - pal[None, :, :]) ** 2).sum(-1)
        idx[change] = d.argmin(1) + 64
        out = Image.fromarray(idx.astype(np.uint8), "P")
        out.putpalette(im.getpalette())
        results.append(out)
    return results


def main():
    args = sys.argv[1:]
    font = Path(args[0])
    rom = ROM.read_bytes()
    res = build(font, rom)
    if "--preview" in args:
        p = Path(args[args.index("--preview") + 1])
        s = Image.new("RGB", (480, 320))
        for n, im in enumerate(res):
            s.paste(im.convert("RGB"), (n % 2 * 240, n // 2 * 160))
        s.resize((960, 640), Image.NEAREST).save(p)
        print(p)
        return
    od = Path(args[1]) if len(args) > 1 else ROOT / "gfx"
    od.mkdir(parents=True, exist_ok=True)
    for n, im in enumerate(res):
        im.save(od / f"title_{n}.png")
        print(od / f"title_{n}.png")


if __name__ == "__main__":
    main()
