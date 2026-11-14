"""devlogo_gfx.py: the boot developer logo (G3, インディ・クリエイツ -> "INTI CREATES"), docs/re/graphics.md.

    python -X utf8 tools/devlogo_gfx.py render FONT.ttf [PNG]   # -> gfx/devlogo.png (144x24, 4bpp indices 0-15)
    python -X utf8 tools/devlogo_gfx.py export PNG              # the original logo cells as the same kind of PNG

The logo is BG1 (4bpp, palette bank 0) on the third boot screen: map rows 8-10, columns 6-23, raw tiles 3-0x30 at
ROM 0x30D3BC (tile t at TILES + (t - 3) * 32, VRAM 0x4060 <- 0x30D3BC, found by vramfind.py on
work/qa/p8/g3/ppu_000600.*). Every cell in rows 9-10 has its own tile; row 8 holds the tops of the tall kana and
shares tiles 3 and 6 between cells, so the new logo leaves row 8 blank (index 14, the background) and fits in the
144x16 px of rows 9-10. Palette: 1-13 a white-to-blue ramp, 14 the background, 15 the drop shadow.
"""
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

TILES = 0x30D3BC
FIRST, LAST = 3, 0x30
MAP = [[0x001] * 2 + [3, 4, 5, 6, 1, 1, 7, 6, 8, 9, 0xA, 0xB, 1, 0xC, 6, 3],      # row 8, cols 6-23 (from VRAM)
       list(range(0x0D, 0x1F)), list(range(0x1F, 0x31))]                          # rows 9, 10
W, H = 18 * 8, 3 * 8
BG, SHADOW = 14, 15
TEXT, CAP, SHEAR = "INTI CREATES", 12, 0.22    # Lato Black, sheared to match the original's italic
PNG = ROOT / "gfx" / "devlogo.png"


def tile_off(t):
    assert FIRST <= t <= LAST, hex(t)
    return TILES + (t - FIRST) * 32


def export(rom, path):
    from PIL import Image
    im = Image.new("P", (W, H))
    im.putpalette([v for i in range(16) for v in (255 - i * 16,) * 3])
    px = im.load()
    for r, row in enumerate(MAP):
        for c, t in enumerate(row):
            for p in range(64):
                px[c * 8 + p % 8, r * 8 + p // 8] = BG if t == 1 else rom[tile_off(t) + p // 2] >> 4 * (p & 1) & 15
    im.save(path)


def render(font_path, path):
    import numpy as np
    from PIL import Image, ImageDraw, ImageFont
    big = 8
    f = ImageFont.truetype(str(font_path), 100 * big)
    x0, y0, x1, y1 = f.getbbox("H")
    capb = y1 - y0
    bx0, _, bx1, _ = f.getbbox(TEXT)
    im = Image.new("L", (bx1 - bx0 + 40 * big, capb + 4 * big))
    ImageDraw.Draw(im).text((20 * big - bx0, 2 * big - y0), TEXT, font=f, fill=255)
    im = im.transform(im.size, Image.AFFINE, (1, SHEAR, -SHEAR * im.size[1], 0, 1, 0), Image.BICUBIC)   # italic
    a = np.array(im)
    cols = np.nonzero(a.max(0) > 0)[0]
    a = a[:, cols[0]:cols[-1] + 1]
    s = CAP / capb
    w = round(a.shape[1] * s)
    h = round(a.shape[0] * s)
    assert w + 1 <= W, f"logo {w} px wide > {W - 1}: lower CAP"
    g = np.array(Image.fromarray(a).resize((w, h), Image.LANCZOS)) / 255.0
    canvas = np.zeros((H, W))
    ox, oy = (W - 1 - w) // 2, 8 + (16 - 1 - CAP) // 2 - (h - CAP) // 2
    canvas[oy:oy + h, ox:ox + w] = g
    assert not canvas[:8].any() or canvas[:8].max() < 0.1, "logo reaches into row 8 (shared tiles)"
    canvas[:8] = 0
    shadow = np.roll(np.roll(canvas, 1, 0), 1, 1)
    idx = np.full((H, W), BG, np.uint8)
    idx[shadow > 0.5] = SHADOW
    ink = canvas > 1 / 26
    idx[ink] = np.clip(np.round(14 - canvas[ink] * 13), 1, 13).astype(np.uint8)
    out = Image.fromarray(idx, "P")
    out.putpalette([v for i in range(16) for v in (255 - i * 16,) * 3])
    out.save(path)


def apply(out, path=PNG, log=None):
    """Write the logo PNG's rows 9-10 into tiles 0x0D-0x30 and blank row 8's tiles (3-0xC) to the background."""
    from PIL import Image
    from writelog import put
    im = Image.open(path)
    assert im.mode == "P" and im.size == (W, H), (path, im.mode, im.size)
    px = im.load()
    done = {}
    for r, row in enumerate(MAP):
        for c, t in enumerate(row):
            if t == 1:
                continue
            pix = [px[c * 8 + p % 8, r * 8 + p // 8] for p in range(64)]
            assert done.setdefault(t, pix) == pix, f"tile {t:#x} shared by cells that now differ"
    for t, pix in sorted(done.items()):
        put(out, tile_off(t), bytes(pix[i] | pix[i + 1] << 4 for i in range(0, 64, 2)), f"dev logo tile {t:#x}", log)
    return out


def main():
    rom = (ROOT / "rom" / "Fantastic Children (Japan).gba").read_bytes()
    cmd = sys.argv[1]
    if cmd == "export":
        export(rom, sys.argv[2])
    elif cmd == "render":
        p = Path(sys.argv[3]) if len(sys.argv) > 3 else PNG
        p.parent.mkdir(exist_ok=True)
        render(sys.argv[2], p)
        print(p)


if __name__ == "__main__":
    main()
