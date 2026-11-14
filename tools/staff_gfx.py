"""staff_gfx.py: the staff roll (G5, docs/re/graphics.md §Staff roll) as 18 cards, redrawn in English from gfx/staff.tsv.

    python -X utf8 tools/staff_gfx.py export [OUTDIR]    # original cards as PNGs (work/gfx/staff/card_NN.png)
    python -X utf8 tools/staff_gfx.py render FONT        # gfx/staff_NN.png from gfx/staff.tsv + tile/byte budgets
                                                         # (FONT: Oswald[wght].ttf, google/fonts ofl/oswald)

Engine (0x0803D484, card n = 0..17): table 0x0821BB70, 8 bytes per card: u32 map pointer (a full 30x20 BG1 map,
u16 per cell = tile index into the card's block, 0 = the blank tile 0), u8 archive index. Archive records at
0x087060EC + 20*index: the tile block (u32 offset relative to the record, u32 packed size, u32 flags 0x00220100,
BIOS LZ77, 4bpp) then the palette (same layout, 32 bytes: index 0 transparent, 1-15 a grey ramp to white). The whole
block is decompressed into one of two VRAM slots (table 0x0821BC00, by card parity; the next card fades in from the
other slot): even cards at tile 0x201 (to 0x2C8 before the odd slot), odd cards at 0x2C9 (to 0x3BF; BG0's blank is
0x3C0). Cards sharing a block: 10 -> 0,2,4; 11 -> 1,3,5; 12 -> 6,8,10; 13 -> 7,9; 14 -> 12,14; 15 -> 11,13;
16 -> 16; 17 -> 15,17.

English (gfx/staff.tsv: card, tile row, Japanese, English): capitals in an 8x16 cell per character (the original's own
Latin lettering, "INTI ALL STAFF", is set the same way), each line centred on the cell grid, so a block holds two
tiles per distinct character and every card fits its slot. `render FONT` writes the committed gfx/staff_NN.png
(240x160, the card palette's indices); the build (`apply`) cuts them into tiles, deduplicates per block (tile 0
blank), rewrites the maps in place (same size) and the block in place, or in free space (`alloc`) with the record's
offset and size rewritten when it packs bigger.
"""
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import gbacomp  # noqa: E402

TABLE = 0x21BB70
CARDS = 18
ARCH = 0x7060EC
BUS = 0x08000000
W, H = 30, 20
MAP_SIZE = W * H * 2
CAP = {0: 0x2C9 - 0x201, 1: 0x3C0 - 0x2C9}   # tiles per VRAM slot, by card parity
TSV = ROOT / "gfx" / "staff.tsv"
GFX = ROOT / "gfx"
INK_W, CAP_H, BASE = 7, 12, 14                 # glyph ink box in the 8x16 cell; baseline row in the cell
SHADOW = 2                                     # palette index of the 1 px bottom-right shadow (the original's 1-3)


def png_path(n):
    return GFX / f"staff_{n:02d}.png"


def lines():
    """[(card, row, jp, en)] from gfx/staff.tsv."""
    out = []
    for ln in TSV.read_text(encoding="utf-8").splitlines()[1:]:
        if ln.strip() and not ln.startswith("#"):
            c, r, jp, en = ln.split("\t")
            out.append((int(c), int(r), jp, en))
    return out


def glyphs(font_path, chars):
    """char -> 8x16 list of palette indices: the font's capital squeezed into INK_W x CAP_H, 16 grey levels."""
    from PIL import Image, ImageDraw, ImageFont
    big = 8
    f = ImageFont.truetype(str(font_path), CAP_H * big * 4 // 3)
    if f.get_variation_names():
        f.set_variation_by_name("Bold")
    cap = f.getbbox("H")
    out = {}
    for ch in chars:
        cell = [[0] * 8 for _ in range(16)]
        if ch != " ":
            bb = f.getbbox(ch)
            im = Image.new("L", (bb[2] - bb[0] + 2, cap[3] - cap[1] + 2 * big * 3), 0)
            ImageDraw.Draw(im).text((-bb[0] + 1, -cap[1] + big * 3), ch, font=f, fill=255)
            w = max(1, min(INK_W, round((bb[2] - bb[0]) / big)))
            sm = im.resize((w, CAP_H + 6), Image.LANCZOS)   # 3 px above/below the cap height (comma, slash)
            x0 = (INK_W - w) // 2
            for y in range(CAP_H + 6):
                cy = BASE - CAP_H + y - 3
                for x in range(w):
                    v = round(sm.getpixel((x, y)) * 15 / 255)
                    if v >= 3 and 0 <= cy < 15:
                        cell[cy][x0 + x] = v
            for y in range(14, -1, -1):          # shadow into the free pixels below/right of the ink
                for x in range(6, -1, -1):
                    if cell[y][x] > SHADOW and not cell[y + 1][x + 1]:
                        cell[y + 1][x + 1] = SHADOW
        out[ch] = cell
    return out


def render(font_path):
    """gfx/staff_NN.png for every card in gfx/staff.tsv."""
    from PIL import Image
    rom = (ROOT / "rom" / "Fantastic Children (Japan).gba").read_bytes()
    ls = lines()
    g = glyphs(font_path, {c for _, _, _, en in ls for c in en})
    for n in range(CARDS):
        im = Image.new("P", (W * 8, H * 8), 0)
        im.putpalette(palette(rom, card(rom, n)[1]) * 16)
        px = im.load()
        for c, r, _, en in ls:
            if c != n:
                continue
            assert en == en.upper() and len(en) <= W and r + 2 <= H, (c, r, en)
            x0 = (W - len(en)) // 2
            for i, ch in enumerate(en):
                for y in range(16):
                    for x in range(8):
                        if g[ch][y][x]:
                            px[(x0 + i) * 8 + x, r * 8 + y] = g[ch][y][x]
        im.save(png_path(n))
    return [png_path(n) for n in range(CARDS)]


def tiles_of(path):
    """30x20 list of 32-byte 4bpp tiles from a card PNG."""
    from PIL import Image
    im = Image.open(path)
    assert im.mode == "P" and im.size == (W * 8, H * 8), (path, im.mode, im.size)
    px = im.load()
    out = []
    for i in range(W * H):
        t = bytearray(32)
        for y in range(8):
            for x in range(8):
                v = px[i % W * 8 + x, i // W * 8 + y]
                assert v < 16, (path, v)
                t[y * 4 + x // 2] |= v << 4 if x & 1 else v
        out.append(bytes(t))
    return out


def pack(rom, a, ns, paths):
    """(tile data, {card: map bytes}) for block a from the cards' PNGs."""
    tiles, index, maps = [bytes(32)], {bytes(32): 0}, {}
    for n in ns:
        cells = []
        for t in tiles_of(paths[n]):
            if t not in index:
                index[t] = len(tiles)
                tiles.append(t)
            cells.append(index[t])
        maps[n] = struct.pack(f"<{W * H}H", *cells)
    cap = min(CAP[n % 2] for n in ns)
    if len(tiles) > cap:
        raise ValueError(f"staff block {a} (cards {ns}): {len(tiles)} tiles > VRAM slot {cap}")
    return b"".join(tiles), maps


def apply(out, log=None, alloc=None, paths=None):
    """Write the English cards (gfx/staff_NN.png) into `out` (bytearray): maps in place, blocks in place or moved."""
    from writelog import put
    paths = paths or {n: png_path(n) for n in range(CARDS)}
    rom = bytes(out)
    for a, ns in sorted(blocks(rom).items()):
        data, maps = pack(rom, a, ns, paths)
        for n, m in maps.items():
            put(out, card(rom, n)[0], m, f"staff card {n} map", log)
        b, size = block(rom, a)
        packed = gbacomp.compress(data)
        packed += bytes(-len(packed) % 4)
        if len(packed) <= size:
            put(out, b, packed + bytes(size - len(packed)), f"staff block {a}", log)
            continue
        if alloc is None:
            raise ValueError(f"staff block {a}: packs to {len(packed)} > slot {size}, no alloc")
        at = alloc(len(packed))
        put(out, at, packed, f"staff block {a} (moved)", log)
        put(out, record(a), struct.pack("<II", at - record(a), len(packed)), f"staff block {a} record", log)
    return out


def card(rom, n):
    """(map offset, archive index) of card n."""
    p, a = struct.unpack_from("<IB", rom, TABLE + 8 * n)
    return p - BUS, a


def record(a):
    return ARCH + 20 * a


def block(rom, a):
    """(block offset, packed size) from archive record a."""
    r = record(a)
    off, size, flags = struct.unpack_from("<III", rom, r)
    assert flags == 0x00220100, (a, hex(flags))
    return r + off, size


def palette(rom, a):
    r = record(a) + 12
    off, size = struct.unpack_from("<II", rom, r)
    assert size == 0x20, (a, size)
    pal = struct.unpack_from("<16H", rom, r + off)
    return [v for c in pal for v in ((c & 31) << 3, (c >> 5 & 31) << 3, (c >> 10 & 31) << 3)]


def blocks(rom):
    """archive index -> [cards] in card order."""
    out = {}
    for n in range(CARDS):
        out.setdefault(card(rom, n)[1], []).append(n)
    return out


def card_png(rom, n):
    from PIL import Image
    m, a = card(rom, n)
    t, _ = gbacomp.decompress(rom, block(rom, a)[0])
    im = Image.new("P", (W * 8, H * 8))
    im.putpalette(palette(rom, a) * 16)
    px = im.load()
    for i in range(W * H):
        e = struct.unpack_from("<H", rom, m + 2 * i)[0]
        ti, hf, vf = e & 0x3FF, e >> 10 & 1, e >> 11 & 1
        for y in range(8):
            for x in range(8):
                sx, sy = (7 - x if hf else x), (7 - y if vf else y)
                v = t[ti * 32 + sy * 4 + sx // 2]
                px[i % W * 8 + x, i // W * 8 + y] = v >> 4 if sx & 1 else v & 15
    return im


def main():
    rom = (ROOT / "rom" / "Fantastic Children (Japan).gba").read_bytes()
    cmd = sys.argv[1] if len(sys.argv) > 1 else "export"
    if cmd == "export":
        od = Path(sys.argv[2] if len(sys.argv) > 2 else ROOT / "work" / "gfx" / "staff")
        od.mkdir(parents=True, exist_ok=True)
        for n in range(CARDS):
            card_png(rom, n).save(od / f"card_{n:02d}.png")
        for a, ns in sorted(blocks(rom).items()):
            b, size = block(rom, a)
            t, _ = gbacomp.decompress(rom, b)
            print(f"block {a}: {b:#x} packed {size:#x}, {len(t) // 32} tiles, cards {ns}")
    elif cmd == "render":
        render(sys.argv[2])
        for a, ns in sorted(blocks(rom).items()):
            data, _ = pack(rom, a, ns, {n: png_path(n) for n in range(CARDS)})
            print(f"block {a} cards {ns}: {len(data) // 32} tiles / slot {min(CAP[n % 2] for n in ns)}, "
                  f"packs {len(gbacomp.compress(data))} / {block(rom, a)[1]} bytes")


if __name__ == "__main__":
    main()
