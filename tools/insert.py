"""insert.py: put the script/ text into the ROM (docs/re/text.md §Insert).

    from insert import build_rom
    rom = build_rom(orig, mode="en")       # rows with `en` get it, the rest keep the Japanese
    rom = build_rom(orig, mode="marker")   # every row gets `[id] marker text` (Phase 5 marker build)

A page's English may hold LINE_SEP (" / "): each part becomes its own page, the extras following it in every page
list (msgs.Script.repack). Pages (dialogue) are pair-encoded (vwf.encode_pairs: two characters per code, at most PAGE_CODES codes, the page
copy's limit) and, with the page lists, relocated to TEXT_BASE. System strings with English are pair-encoded too
(sys_bytes), written after the pages, and every holder in their `ref` is repointed.
The VWF hook and its tables go to vwf.VWF_BASE.
"""
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import vwf  # noqa: E402
from msgs import BUS, END, Script  # noqa: E402
from script_tsv import ENDFLAG, load, rom_rows  # noqa: E402

TEXT_BASE = 0x730000          # after vwf.VWF_END (0x724800); free to 0x7FFFFF, the ROM may grow past 8 MiB
PAGE_CODES = 21               # the page copy keeps 22 codes per line (0x0802FBCE), the box shows at most 21 (0x0802F78C)
MARKER_PX = vwf.TOP_PX        # marker pages fit both boxes; build.py --marker-px 192 stresses the bottom box
UI_ONLY = set("▼▶：＄ 　")    # strings made only of these (cursors, separators, blanks, empty) are UI, not text
LINE_SEP = " / "              # in a page's English: start an extra page (line) right after it, in every list


def is_text(jp):
    return any(ch not in UI_ONLY for ch in jp)
FILLER = "The quick brown fox jumps over the lazy dog. Pack my box with five dozen liquor jugs."


def page_bytes(text):
    codes = vwf.encode_pairs(text)
    if len(codes) > PAGE_CODES:
        raise ValueError(f"{len(codes)} codes > {PAGE_CODES} for {text!r}")
    return struct.pack(f"<{len(codes)}H", *codes) + struct.pack("<H", END | len(codes))


def sys_bytes(text):
    """System string: pair-encoded like pages (every one seen is drawn by the VWF typer, through text_put with a
    cell count or through the page copy as a battle line), {argN} kept, trailing {endflag} -> end-code bit 14."""
    flag = 0x4000 if text.endswith(ENDFLAG) else 0
    codes = vwf.encode_pairs(text[:-len(ENDFLAG)] if flag else text)
    if len(codes) > 0xFF:
        raise ValueError(f"too long: {text!r}")
    return struct.pack(f"<{len(codes)}H", *codes) + struct.pack("<H", END | flag | len(codes))


def marker_page(rid, limit_px=MARKER_PX):
    text = rid
    for ch in " " + FILLER:
        if vwf.ink_width(text + ch) > limit_px or len(vwf.encode_pairs(text + ch)) > PAGE_CODES:
            break
        text += ch
    return text.rstrip()


def marker_sys(rid, jp):
    """The id plus filler, about as wide as the Japanese (8 px per glyph); argument codes and {endflag} kept."""
    toks = list(vwf._tokens(jp))
    keep = [t for t in toks if t.startswith("{arg")]
    tail = ENDFLAG if jp.endswith(ENDFLAG) else ""
    glyphs = len([t for t in toks if not t.startswith("{")])
    text = rid
    for ch in " " + FILLER:
        if (vwf.ink_width(text + ch) > min(vwf.BOTTOM_PX, max(glyphs * 8, vwf.ink_width(rid)))
                or len(vwf.encode_pairs(text + ch)) + len(keep) > PAGE_CODES):
            break
        text += ch
    return text.rstrip() + "".join(keep) + tail


def texts(d, mode, marker_px=MARKER_PX):
    """{row id: English text or None} for every row."""
    rows = rom_rows(d)
    if mode == "marker":
        from lint import CHOICE_CELLS, CHOICES
        choice = {r.id for r in rows if r.id[0] == "p"
                  and any(m.split(".")[0][1:] in CHOICES for m in r.ref.split(","))}
        return {r.id: (None if not is_text(r.jp) else marker_page(r.id, CHOICE_CELLS * 8) if r.id in choice
                       else marker_page(r.id, marker_px) if r.id[0] == "p"
                       else marker_sys(r.id, r.jp))
                for r in rows}
    tsv = load()
    return {r.id: (tsv.get(r.id, {}).get("en") or None) for r in rows}


def build_rom(d, mode="en", marker_px=MARKER_PX, qa=None):
    en = texts(d, mode, marker_px)
    en.update(qa or {})   # --qa ID=text: single-line overrides for width and glyph stress tests
    out = vwf.apply(bytearray(d))
    s = Script.unpack(d)
    for off in s.pages:
        t = en.get(f"p{off:06X}")
        if t:
            parts = t.split(LINE_SEP)
            s.pages[off] = page_bytes(t) if len(parts) == 1 else [page_bytes(p) for p in parts]
    out = bytearray(s.repack(bytes(out), base=TEXT_BASE))
    o = (s.end + 3) & ~3
    rows = [r for r in rom_rows(d) if r.id[0] == "s" and en.get(r.id)]
    for r in rows:
        b = sys_bytes(en[r.id])
        if len(out) < o + len(b):
            out += b"\xFF" * (o + len(b) - len(out))
        out[o:o + len(b)] = b
        for h in r.ref.split(","):
            h = int(h, 16)
            assert struct.unpack_from("<I", out, h)[0] == BUS + r.off, (r.id, hex(h))
            struct.pack_into("<I", out, h, BUS + o)
        o = (o + len(b) + 3) & ~3
    if len(out) % 0x10000:   # keep the size a round number
        out += b"\xFF" * (0x10000 - len(out) % 0x10000)
    return bytes(out)
