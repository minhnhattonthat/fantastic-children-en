"""title_gfx.py: the 4 title-screen backgrounds (G1 logo + G2 copyright, docs/re/graphics.md) as editable PNGs.

    python -X utf8 tools/title_gfx.py export [OUTDIR]        # work/gfx/title_<n>.png, 240x160, 8bpp indexed
    python -X utf8 tools/title_gfx.py check PNG..            # each PNG re-packs into its ROM slot?

Each variant is one BIOS-LZ77 block of 601 8bpp tiles: tile 0 blank, tiles 1-600 the 30x20 screen in reading order
(so no map to touch), its 256-colour palette in the next archive record (512 bytes just after the block; checked
against palette RAM at the title, `work/qa/p8/title_ppu`). Import re-tiles the PNG in the
same order (palette indices kept, so draw only with the palette's own colours) and re-compresses. Each block has an
archive record (RECORDS): u32 offset relative to the record itself, u32 packed size (rounded up to 4), u32 flags
0x00420100. Up to that size the block is rewritten in place (padded with 0); bigger, it goes to `alloc(size)` (a free
ROM offset) and the record's offset and size are rewritten.
"""
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import gbacomp  # noqa: E402

BLOCKS = (0x30E21C, 0x36A414, 0x3725F4, 0x378E30)
RECORDS = (0x30D028, 0x30D320, 0x30D334, 0x30D348)
TILES, W, H = 601, 30, 20


def palette(rom, b):
    """The variant's 256 colours: the archive record right after the tile record (size 0x200), just past the block."""
    r = RECORDS[BLOCKS.index(b)] + 12
    off, size = struct.unpack_from("<II", rom, r)
    assert size == 0x200, (hex(r), size)
    pal = struct.unpack_from("<256H", rom, r + off)
    out = []
    for c in pal:
        out += [(c & 31) << 3, (c >> 5 & 31) << 3, (c >> 10 & 31) << 3]
    return out


def to_png(rom, b):
    from PIL import Image
    t, end = gbacomp.decompress(rom, b)
    assert len(t) == TILES * 64
    im = Image.new("P", (W * 8, H * 8))
    im.putpalette(palette(rom, b))
    px = im.load()
    for i in range(W * H):
        for p in range(64):
            px[i % W * 8 + p % 8, i // W * 8 + p // 8] = t[(i + 1) * 64 + p]
    return im, end - b


def tiles_from_png(rom, b, path):
    from PIL import Image
    im = Image.open(path)
    assert im.mode == "P" and im.size == (W * 8, H * 8), (path, im.mode, im.size)
    t, _ = gbacomp.decompress(rom, b)
    out = bytearray(t[:64])
    px = im.load()
    for i in range(W * H):
        out += bytes(px[i % W * 8 + p % 8, i // W * 8 + p // 8] for p in range(64))
    return bytes(out)


def slot(rom, n):
    r = RECORDS[n]
    off, size, flags = struct.unpack_from("<III", rom, r)
    assert r + off == BLOCKS[n] and flags == 0x00420100, (n, hex(off), hex(flags))
    return size


def apply(out, n, path, log=None, alloc=None):
    """Write variant n (0-3) from `path` into `out` (bytearray). alloc(size) -> free ROM offset, for a bigger block."""
    from writelog import put
    b, size = BLOCKS[n], slot(bytes(out), n)
    packed = gbacomp.compress(tiles_from_png(bytes(out), b, path))
    packed += bytes(-len(packed) % 4)
    if len(packed) <= size:
        put(out, b, packed + bytes(size - len(packed)), f"title bg {n}", log)
        return out
    if alloc is None:
        raise ValueError(f"title {n}: packs to {len(packed)} > slot {size}, no alloc")
    at = alloc(len(packed))
    put(out, at, packed, f"title bg {n} (moved)", log)
    put(out, RECORDS[n], struct.pack("<II", at - RECORDS[n], len(packed)), f"title bg {n} record", log)
    return out


def main():
    rom = (ROOT / "rom" / "Fantastic Children (Japan).gba").read_bytes()
    cmd = sys.argv[1] if len(sys.argv) > 1 else "export"
    if cmd == "export":
        od = Path(sys.argv[2] if len(sys.argv) > 2 else ROOT / "work" / "gfx")
        od.mkdir(parents=True, exist_ok=True)
        for n, b in enumerate(BLOCKS):
            im, size = to_png(rom, b)
            im.save(od / f"title_{n}.png")
            print(f"title_{n}.png  block {b:#x}  packed {size}")
    elif cmd == "check":
        bad = 0
        for p in sys.argv[2:]:
            n = int(Path(p).stem.split("_")[-1])
            size = len(gbacomp.compress(tiles_from_png(rom, BLOCKS[n], p)))
            print(f"{p}: {size} / slot {slot(rom, n)} bytes" + ("" if size <= slot(rom, n) else " (moves)"))
            bad += size > slot(rom, n)
        sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
