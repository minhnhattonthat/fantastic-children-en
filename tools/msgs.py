"""msgs.py: unpack and repack the message text (table -> page lists -> pages), see docs/re/text.md.

    from msgs import Script
    s = Script.unpack(rom)            # s.pages {page_off: text}, s.lists (page-list area as words), s.table
    rom2 = s.repack(rom)              # in place: every page back at its own offset (identity build)
    rom3 = s.repack(rom, base=0x710000)  # relocate: pages + page lists to free space, table repointed

Page text is the glyph codes only, decoded through tbl/jp.tbl (unknown codes as `[XX]` bytes, so it roundtrips);
the end code `0x8000 | glyph count` is written by repack, never stored in the text.
"""
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from tbl import Table  # noqa: E402

BUS = 0x08000000
MSG_TABLE, MSG_COUNT = 0x212B6C, 1528
LISTS, LISTS_END = 0x21434C, 0x219BC0  # page-list area: NULL-terminated u32 page pointers, lists overlap
PAGES, PAGES_END = 0x7ECB4, 0x9C140    # pages tile this range exactly (tests/test_script.py); data follows
END = 0x8000
MAX_GLYPHS = 0xFF                      # the end code's count field (test_text: c & 0xFF == count)


def u32(d, o):
    return struct.unpack_from("<I", d, o)[0]


def page_codes(d, off):
    """The page's glyph codes (bytes, no end code) and its total length in bytes including the end code."""
    o = off
    while not struct.unpack_from("<H", d, o)[0] & END:
        o += 2
    return bytes(d[off:o]), o + 2 - off


class Script:
    def __init__(self, table, lists, pages, sizes, tbl):
        self.table = table    # [offset into lists area, in words] per message id
        self.lists = lists    # page-list area as words: page file offset, or 0 = end of list
        self.pages = pages    # {page file offset: text}
        self.sizes = sizes    # {page file offset: original byte length incl. end code}
        self.tbl = tbl

    @classmethod
    def unpack(cls, d, tbl=None):
        tbl = tbl or Table.load(ROOT / "tbl" / "jp.tbl")
        nwords = (LISTS_END - LISTS) // 4
        lists = []
        for i in range(nwords):
            w = u32(d, LISTS + 4 * i)
            if w and not (BUS + PAGES <= w < BUS + PAGES_END):
                raise ValueError(f"page-list word {LISTS + 4 * i:#x} = {w:#x} is not a page pointer")
            lists.append(w - BUS if w else 0)
        if lists[-1] != 0:
            raise ValueError("page-list area does not end with a terminator")
        table = []
        for n in range(MSG_COUNT):
            p = u32(d, MSG_TABLE + 4 * n) - BUS
            if not LISTS <= p < LISTS_END or (p - LISTS) % 4:
                raise ValueError(f"message {n} points outside the page-list area: {p:#x}")
            table.append((p - LISTS) // 4)
        pages, sizes = {}, {}
        for off in sorted({w for w in lists if w}):
            codes, size = page_codes(d, off)
            text, used = tbl.decode(codes, 0, len(codes))
            assert used == len(codes)
            pages[off], sizes[off] = text, size
        return cls(table, lists, pages, sizes, tbl)

    def encode_page(self, text):
        codes = self.tbl.encode(text)
        if len(codes) % 2:
            raise ValueError(f"odd byte count in {text!r}")
        n = len(codes) // 2
        if n > MAX_GLYPHS:
            raise ValueError(f"{n} glyphs > {MAX_GLYPHS} in {text!r}")
        return codes + struct.pack("<H", END | n)

    def messages(self):
        """[(message id, [page offsets])]."""
        out = []
        for n, w in enumerate(self.table):
            offs = []
            while self.lists[w]:
                offs.append(self.lists[w])
                w += 1
            out.append((n, offs))
        return out

    def repack(self, d, base=None, log=None):
        """New ROM bytes. base=None: pages in place (each must fit its original size); else pages, then the
        page-list area, are written from file offset `base` (free space) and the message table repointed.
        log: a writelog.WriteLog that records the relocated build's writes (pages, page lists, message table)."""
        from writelog import put
        out = bytearray(d)
        where = {}
        if base is None:
            for off, text in self.pages.items():
                b = self.encode_page(text)
                if len(b) > self.sizes[off]:
                    raise ValueError(f"page {off:#x} grew {self.sizes[off]} -> {len(b)} bytes; relocate instead")
                out[off:off + len(b)] = b
                where[off] = off
            lists_at = LISTS
        else:
            o = base
            for off in sorted(self.pages):
                t = self.pages[off]
                # bytes = already encoded, end code included; a list of bytes = the page plus extra pages that
                # follow it in every page list holding it (English that needs more lines than the Japanese)
                parts = t if isinstance(t, list) else [t]
                where[off] = []
                for p in parts:
                    b = p if isinstance(p, bytes) else self.encode_page(p)
                    where[off].append(o)
                    put(out, o, b, f"page {off:X}", log)
                    o += len(b)
            words, index = [], []
            for w in self.lists:
                index.append(len(words))
                words.extend(where[w] if w else [None])
            lists_at = (o + 3) & ~3
            self.end = lists_at + 4 * len(words)   # first free byte after the relocated pages and lists
            self.where = where                     # page offset -> [file offsets of its relocated page(s)]
            put(out, lists_at, struct.pack(f"<{len(words)}I", *(BUS + a if a is not None else 0 for a in words)),
                "page lists", log)
            put(out, MSG_TABLE, struct.pack(f"<{len(self.table)}I", *(BUS + lists_at + 4 * index[w] for w in self.table)),
                "message table", log)
            return bytes(out)
        for i, w in enumerate(self.lists):
            struct.pack_into("<I", out, lists_at + 4 * i, BUS + where[w] if w else 0)
        for n, w in enumerate(self.table):
            struct.pack_into("<I", out, MSG_TABLE + 4 * n, BUS + lists_at + 4 * w)
        return bytes(out)
