"""vwf.py: variable-width font for the line typer, and the pair encoding of English (docs/re/text.md §VWF).

    from vwf import apply, encode_pairs, text_width
    rom = apply(bytearray(rom))       # hook + tables at VWF_BASE, glyph upload disabled
    codes = encode_pairs("Hello!")    # [u16]: two characters per code (bit 14 set), for dialogue pages
    px = text_width("Hello!")         # rendered width in pixels

The game types a line with `type_line(obj r0, src r1, x r2, y r3, [sp] count, [sp+4] flags)` at 0x0802E7F8: one
8x16 cell per code (tilemap cell x+j -> tiles h-1-2n / h-2n), glyphs uploaded later by 0x0802F108. Each frame it
re-types the revealed part of each line (count = codes revealed), then blank-fills the rest of the row (src = 0,
x = start + count). The hook:
  - src != 0: draws the codes at their own widths into a RAM scratch, then copies the cells to VRAM (cell a = tiles
    t0-2a / t0-2a+1, t0 = h-1-2n; see SCRATCH), maps max(cells, codes) tilemap cells (past the ink: blank tile 0x201, as the game does for spaces),
    adds the cells to n, and records (y, x, x + mapped) for the row in the first 16 bytes of the obj's old glyph
    buffer [obj+4] (4 bytes per y & 3);
  - src == 0 (blank fill): starts the fill after the recorded cells of that row, so it can't wipe them;
  - y outside 0-30 or x < 0: the original code.
The upload routine then only sets its "uploaded" flag (its glyphs are never used).

Codes the hook draws: a game code 0x000-0x1FF (glyph per code), an argument code (skipped), or a **pair code**
0x4000 | i1 << 7 | i2: two characters by 7-bit index into the pair charset (0 = none). The page copy keeps 22 codes
per line, so pairs give up to 44 characters. Indices with (i & 0x1C) == 4 are never used, so no pair code has bits
9-11 = 001 (the copy routine's argument test).

Tables: per game code 128-byte glyph (16 rows x two u32 of 8 4bpp pixels, left and right half) + width byte;
the same per pair index. English glyphs come from fonts/vwf_en.*; game codes keep the game's font-0 glyph at 8 px,
except the codes tbl/en.tbl gives an English glyph.
"""
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from tbl import Table  # noqa: E402

BUS = 0x08000000
VWF_BASE = 0x710000                 # free space (docs/re/text.md §Free space)
WIDTHS_AT = VWF_BASE + 0x400        # 512 bytes, per game code
PW_AT = VWF_BASE + 0x600            # 128 bytes, per pair index
GLYPHS_AT = VWF_BASE + 0x800        # 512 x 128 bytes
PG_AT = GLYPHS_AT + 0x200 * 128     # 128 x 128 bytes
VWF_END = PG_AT + 0x80 * 128        # 0x724800
TYPE_LINE = 0x0802E7F8
UPLOAD_SKIP = 0x0802F12A            # after the upload sets its flag; branch to its epilogue
UPLOAD_EXIT = 0x0802F1B4
UPLOAD_SKIP_ORIG = "0025"            # the original's halfword at UPLOAD_SKIP (movs r5, #0), asserted before patching
FONT0_BASE, FONT0_PTRS = 0x0517EC, 0x210A98
PAIR = 0x4000
# Draw scratch (bug B1): the hook clears and draws a line's cells here, then copies them to VRAM in one pass, so the
# visible tiles go straight from the old to the new pixels (drawing in VRAM showed half-drawn lines whenever the
# redraw ran while the screen scanned the box). Cell a at top - 64a, like the VRAM cells. 0x0203C300-0x0203FFFF is
# never written after boot (tools/lua/ramfree.lua, 9 scenes) and no code literal points past 0x0203C2E0.
# 32 cells (the asm's 32 / 29 constants); glyphs starting past cell 29 are not drawn (off screen anyway).
SCRATCH, SCRATCH_CELLS = 0x0203F000, 32

# frame: [0] cells C, [4] codes k, [8] i, [12] obj, [16] src, [20] cols left, [24] tmp, [28] raw x, [32] raw y,
# [36] region (count when the string ended early, as the game blank-fills up to count; else k)
# Box regions (cells): the game gives each dialogue line 21 cells from x (0x0802F774/F7C8/F802/F932). Bottom box
# (x=3, y=15/17, ▼ at col 27): the hook widens any call on those rows whose region ends at col 24 to col 27 (24
# cells, 192 px). Top box (x=1, y=3/5, talk battles and the prologue, portrait on the right, ▼ at col 22): 21 cells.
BOTTOM_PX, TOP_PX = 192, 168
ASM = r"""
hook:
    cmp r3, #15
    beq wide
    cmp r3, #17
    bne nowide
wide:
    cmp r2, #3
    blt nowide
    ldr r4, [sp, #20]
    lsls r4, r4, #24
    lsrs r4, r4, #24
    adds r5, r2, r4
    cmp r5, #24
    bne nowide
    adds r4, #3
    str r4, [sp, #20]
nowide:
    cmp r1, #0
    bne typed
    ldr r4, [r0, #4]
    lsrs r5, r4, #18
    cmp r5, #0x80
    bne orig
    movs r5, #3
    ands r5, r3
    lsls r5, r5, #2
    adds r4, r4, r5
    ldrb r5, [r4]
    cmp r5, r3
    bne orig
    ldrb r5, [r4, #1]
    cmp r2, r5
    blt orig
    ldrb r5, [r4, #2]
    cmp r2, r5
    bge orig
    movs r6, #0
    strb r6, [r4, #1]
    strb r6, [r4, #2]
    ldr r6, [sp, #20]
    lsls r6, r6, #24
    lsrs r6, r6, #24
    subs r7, r5, r2
    subs r6, r6, r7
    ble done0
    str r6, [sp, #20]
    mov r2, r5
    b orig
done0:
    pop {r4, r5, r6, r7}
    pop {r0}
    bx r0
typed:
    movs r4, #0x15
    ldrsb r4, [r0, r4]
    adds r4, r3, r4
    bmi orig
    cmp r4, #30
    bgt orig
    movs r5, #0x14
    ldrsb r5, [r0, r5]
    adds r5, r2, r5
    bmi orig
    b vwf
orig:
    mov r7, r10
    mov r6, r9
    mov r5, r8
    push {r5, r6, r7}
    sub sp, #0xc
    ldr r4, lit_back
    bx r4
vwf:
    mov r6, r8
    mov r7, r9
    push {r6, r7}
    mov r6, r10
    mov r7, r11
    push {r6, r7}
    sub sp, #40
    str r0, [sp, #12]
    str r1, [sp, #16]
    str r2, [sp, #28]
    str r3, [sp, #32]
    ldr r0, lit_map
    ldr r0, [r0, #12]
    lsls r4, r4, #6
    adds r0, r0, r4
    lsls r1, r5, #1
    adds r0, r0, r1
    mov r8, r0
    movs r0, #32
    subs r0, r0, r5
    str r0, [sp, #20]
    ldr r6, [sp, #12]
    ldrb r0, [r6, #0x12]
    movs r1, #1
    tst r0, r1
    beq noreset
    bics r0, r1
    strb r0, [r6, #0x12]
    movs r0, #0
    strh r0, [r6, #2]
noreset:
    ldrh r0, [r6, #0x10]
    ldrh r1, [r6, #2]
    lsls r1, r1, #1
    subs r0, r0, r1
    subs r0, r0, #1
    mov r10, r0
    lsls r0, r0, #5
    ldr r1, [r6, #8]
    adds r0, r0, r1
    mov r11, r0
    ldr r0, [sp, #76]
    lsls r0, r0, #24
    lsrs r0, r0, #24
    ldr r7, [sp, #16]
    movs r4, #0
    movs r5, #0
p1:
    cmp r5, r0
    bge p1end
    lsls r1, r5, #1
    ldrh r1, [r7, r1]
    lsls r2, r1, #16
    bmi p1endhit
    adds r5, #1
    bl ewidth
    adds r4, r4, r2
    b p1
p1endhit:
    str r0, [sp, #36]
    b p1fin
p1end:
    str r5, [sp, #36]
p1fin:
    adds r4, #6
    lsrs r4, r4, #3
    str r4, [sp]
    str r5, [sp, #4]
    cmp r4, #32
    ble c32
    movs r4, #32
c32:
    ldr r1, lit_scr
    movs r2, #0
    ldr r3, lit_map
    adds r3, #0xff
    adds r3, #0x39
    ldrb r3, [r3]
    cmp r3, #2
    bne clr
    ldr r2, lit_ones
clr:
    cmp r4, #0
    beq clrend
    movs r3, #16
clr2:
    stmia r1!, {r2}
    subs r3, #1
    bne clr2
    subs r1, #128
    subs r4, #1
    b clr
clrend:
    movs r0, #0
    mov r9, r0
    str r0, [sp, #8]
chr:
    ldr r0, [sp, #8]
    ldr r1, [sp, #4]
    cmp r0, r1
    bge chrend
    adds r1, r0, #1
    str r1, [sp, #8]
    ldr r7, [sp, #16]
    lsls r0, r0, #1
    ldrh r0, [r7, r0]
    lsls r2, r0, #17
    bmi chrpair
    lsls r2, r0, #20
    lsrs r2, r2, #29
    cmp r2, #1
    beq chr
    lsls r0, r0, #23
    lsrs r0, r0, #23
    ldr r3, lit_widths
    ldrb r3, [r3, r0]
    lsls r0, r0, #7
    ldr r1, lit_glyphs
    adds r0, r0, r1
    bl put
    b chr
chrpair:
    str r0, [sp, #24]
    lsls r0, r0, #18
    lsrs r0, r0, #25
    ldr r3, lit_pw
    ldrb r3, [r3, r0]
    lsls r0, r0, #7
    ldr r1, lit_pg
    adds r0, r0, r1
    bl put
    ldr r0, [sp, #24]
    lsls r0, r0, #25
    lsrs r0, r0, #25
    ldr r3, lit_pw
    ldrb r3, [r3, r0]
    lsls r0, r0, #7
    ldr r1, lit_pg
    adds r0, r0, r1
    bl put
    b chr
chrend:
    ldr r2, [sp]
    cmp r2, #32
    ble cp0
    movs r2, #32
cp0:
    ldr r4, lit_scr
    mov r5, r11
cp1:
    cmp r2, #0
    ble cpend
    ldmia r4!, {r0, r1, r3, r6}
    stmia r5!, {r0, r1, r3, r6}
    ldmia r4!, {r0, r1, r3, r6}
    stmia r5!, {r0, r1, r3, r6}
    ldmia r4!, {r0, r1, r3, r6}
    stmia r5!, {r0, r1, r3, r6}
    ldmia r4!, {r0, r1, r3, r6}
    stmia r5!, {r0, r1, r3, r6}
    subs r4, #128
    subs r5, #128
    subs r2, #1
    b cp1
cpend:
    ldr r0, [sp]
    ldr r1, [sp, #36]
    cmp r1, r0
    ble m1
    mov r0, r1
m1:
    ldr r1, [sp, #20]
    cmp r0, r1
    ble m2
    mov r0, r1
m2:
    ldr r6, [sp, #12]
    ldr r4, [r6, #4]
    lsrs r5, r4, #18
    cmp r5, #0x80
    bne norec
    ldr r3, [sp, #32]
    movs r5, #3
    ands r5, r3
    lsls r5, r5, #2
    adds r4, r4, r5
    strb r3, [r4]
    ldr r3, [sp, #28]
    strb r3, [r4, #1]
    adds r3, r3, r0
    strb r3, [r4, #2]
norec:
    ldr r5, [sp, #80]
    mov r1, r8
    mov r2, r10
    movs r3, #0
map:
    cmp r3, r0
    bge mapend
    ldr r4, [sp]
    cmp r3, r4
    blt tile
    ldr r6, lit_blank
    mov r7, r6
    b putm
tile:
    mov r6, r2
    adds r7, r6, #1
putm:
    movs r4, #1
    tst r5, r4
    bne notop
    strh r6, [r1]
notop:
    movs r4, #2
    tst r5, r4
    bne nobot
    mov r4, r1
    adds r4, #64
    strh r7, [r4]
nobot:
    adds r1, #2
    subs r2, #2
    adds r3, #1
    b map
mapend:
    ldr r6, [sp, #12]
    ldrh r0, [r6, #2]
    ldr r1, [sp]
    adds r0, r0, r1
    strh r0, [r6, #2]
    add sp, #40
    pop {r6, r7}
    mov r10, r6
    mov r11, r7
    pop {r6, r7}
    mov r8, r6
    mov r9, r7
    pop {r4, r5, r6, r7}
    pop {r0}
    bx r0

ewidth:
    lsls r2, r1, #17
    bmi ewpair
    lsls r2, r1, #20
    lsrs r2, r2, #29
    cmp r2, #1
    beq ewzero
    lsls r2, r1, #23
    lsrs r2, r2, #23
    ldr r6, lit_widths
    ldrb r2, [r6, r2]
    bx lr
ewzero:
    movs r2, #0
    bx lr
ewpair:
    ldr r6, lit_pw
    lsls r2, r1, #18
    lsrs r2, r2, #25
    ldrb r2, [r6, r2]
    lsls r3, r1, #25
    lsrs r3, r3, #25
    ldrb r3, [r6, r3]
    adds r2, r2, r3
    bx lr

put:
    mov r6, r9
    adds r3, r6, r3
    mov r9, r3
    lsrs r1, r6, #3
    cmp r1, #29
    bgt putskip
    lsls r1, r1, #6
    ldr r3, lit_scr
    subs r1, r3, r1
    movs r2, #7
    ands r2, r6
    lsls r2, r2, #2
    movs r3, #32
    subs r3, r3, r2
    movs r4, #16
row:
    ldr r5, [r0]
    ldr r6, [r1]
    mov r7, r5
    lsls r7, r2
    orrs r6, r7
    str r6, [r1]
    subs r1, #64
    ldr r6, [r1]
    lsrs r5, r3
    orrs r6, r5
    ldr r5, [r0, #4]
    mov r7, r5
    lsls r7, r2
    orrs r6, r7
    str r6, [r1]
    subs r1, #64
    ldr r6, [r1]
    lsrs r5, r3
    orrs r6, r5
    str r6, [r1]
    adds r1, #132
    adds r0, #8
    subs r4, #1
    bne row
putskip:
    bx lr

.align 2
lit_back:   .word 0x0802E805
lit_map:    .word 0x0202C790
lit_widths: .word {widths}
lit_glyphs: .word {glyphs}
lit_pw:     .word {pw}
lit_pg:     .word {pg}
lit_blank:  .word 0x201
lit_ones:   .word 0x11111111
lit_scr:    .word {scr_top}
"""


def _asm(src, addr):
    from keystone import KS_ARCH_ARM, KS_MODE_THUMB, Ks
    enc, _ = Ks(KS_ARCH_ARM, KS_MODE_THUMB).asm(src, addr)
    return bytes(enc)


def hook_code():
    src = ASM
    for k, v in (("widths", WIDTHS_AT), ("glyphs", GLYPHS_AT), ("pw", PW_AT), ("pg", PG_AT)):
        src = src.replace("{" + k + "}", hex(BUS + v))
    src = src.replace("{scr_top}", hex(SCRATCH + (SCRATCH_CELLS - 1) * 64))
    return _asm(src, BUS + VWF_BASE)


def _pack_rows(rows):
    """16 rows of up to 16 pixel levels -> 128 bytes (per row: u32 left 8 px, u32 right 8 px; pixel x at bits 4x)."""
    out = bytearray()
    for r in rows:
        for half in (r[:8], r[8:16]):
            out += struct.pack("<I", sum((v & 15) << (4 * i) for i, v in enumerate(half)))
    return bytes(out)


_cache = {}


def pair_index():
    """{char: 7-bit pair index} for every English glyph; indices with (i & 0x1C) == 4 are skipped."""
    if "pi" not in _cache:
        import vwf_font
        free = (i for i in range(1, 0x80) if i & 0x1C != 4)
        _cache["font"] = vwf_font.load()
        _cache["pi"] = {ch: next(free) for ch in _cache["font"]}
    return _cache["pi"]


def encode_pairs(text):
    """Dialogue text -> codes: runs of English glyphs two per pair code, anything else one game code (tbl/en.tbl)."""
    pi = pair_index()
    en = Table.load(ROOT / "tbl" / "en.tbl")
    out, pend = [], None
    for tok in _tokens(text):
        if tok in pi:
            if pend is None:
                pend = pi[tok]
            else:
                out.append(PAIR | pend << 7 | pi[tok])
                pend = None
            continue
        if pend is not None:
            out.append(PAIR | pend << 7)
            pend = None
        b = en.encode(tok)
        out += struct.unpack(f"<{len(b) // 2}H", b)
    if pend is not None:
        out.append(PAIR | pend << 7)
    for c in out:
        assert c & 0x8000 == 0 and (c & 0x4000 or c < 0x400) and (c & 0x4E00) != 0x4200, hex(c)
    return out


def decode_pairs(codes):
    """Inverse of encode_pairs (tests and tools)."""
    pi = {v: k for k, v in pair_index().items()}
    en = Table.load(ROOT / "tbl" / "en.tbl")
    out = ""
    for c in codes:
        if c & PAIR:
            out += pi[c >> 7 & 0x7F] + (pi[c & 0x7F] if c & 0x7F else "")
        else:
            out += en.decode(struct.pack("<H", c), 0, 2)[0]
    return out


def _tokens(text):
    i = 0
    while i < len(text):
        if text[i] in "{[":
            j = text.index("}" if text[i] == "{" else "]", i) + 1
            yield text[i:j]
            i = j
        else:
            yield text[i]
            i += 1


def text_width(text):
    """Pixels the hook draws for `text` (English glyph widths; other characters 8 px)."""
    pi = pair_index()
    font = _cache["font"]
    return sum(font[t][0] if t in pi else (0 if t.startswith("{") else 8) for t in _tokens(text))


def ink_width(text):
    """Pixels up to the last drawn column: the advance minus the 1-px gap after the last glyph (the hook's cell
    count is (advance + 6) / 8). Budgets (BOTTOM_PX, TOP_PX, region cells x 8) apply to this."""
    return max(0, text_width(text) - 1)


def tables(d):
    """(game-code widths 512 B, game-code glyphs 512*128 B, pair widths 128 B, pair glyphs 128*128 B)."""
    pi = pair_index()
    font = _cache["font"]
    en = Table.load(ROOT / "tbl" / "en.tbl")
    wid, gly = bytearray(0x200), bytearray(0x200 * 128)
    pw, pg = bytearray(0x80), bytearray(0x80 * 128)
    for code in range(0x200):
        p = struct.unpack_from("<I", d, FONT0_PTRS + 4 * code)[0] - BUS
        idx = struct.unpack_from("<H", d, p)[0]
        g = d[FONT0_BASE + idx * 64:FONT0_BASE + idx * 64 + 64]
        for r in range(16):
            gly[code * 128 + r * 8:code * 128 + r * 8 + 4] = g[r * 4:r * 4 + 4]
        wid[code] = 8
    for ch, (w, rows) in font.items():
        g = _pack_rows(rows)
        code = struct.unpack("<H", en.encode(ch))[0]
        wid[code], gly[code * 128:code * 128 + 128] = w, g
        i = pi[ch]
        pw[i], pg[i * 128:i * 128 + 128] = w, g
    return bytes(wid), bytes(gly), bytes(pw), bytes(pg)


def apply(out, log=None):
    """Write the hook, tables and the two patches into `out` (bytearray of the ROM, grown as needed).
    log: a writelog.WriteLog recording each write."""
    from writelog import put
    code = hook_code()
    if len(code) > WIDTHS_AT - VWF_BASE:
        raise ValueError(f"hook is {len(code)} bytes")
    wid, gly, pw, pg = tables(bytes(out))
    for at, b, by in ((VWF_BASE, code, "vwf hook"), (WIDTHS_AT, wid, "vwf widths"), (PW_AT, pw, "vwf pair widths"),
                      (GLYPHS_AT, gly, "vwf glyphs"), (PG_AT, pg, "vwf pair glyphs")):
        put(out, at, b, by, log)
    if len(out) < VWF_END:
        out += b"\xFF" * (VWF_END - len(out))
    # type_line: keep `push {r4-r7,lr}`, then ldr r4,[pc,#4]; bx r4; nop; .word hook|1
    patch = _asm("ldr r4, [pc, #4]\nbx r4\nnop", TYPE_LINE + 2) + struct.pack("<I", BUS + VWF_BASE + 1)
    o = TYPE_LINE + 2 - BUS
    assert out[o:o + 10] == bytes.fromhex("57464e464546e0b483b0"), out[o:o + 10].hex()
    put(out, o, patch, "type_line hook", log)
    o = UPLOAD_SKIP - BUS
    assert out[o:o + 2] == bytes.fromhex(UPLOAD_SKIP_ORIG), out[o:o + 2].hex()
    put(out, o, _asm(f"b {UPLOAD_EXIT:#x}", UPLOAD_SKIP), "glyph upload skip", log)
    return out
