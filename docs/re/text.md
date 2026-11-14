# Text engine

Dump: `rom.sha1` (8 MiB, header `FANTCHILDREN` / `BFCJ`, EEPROM_V124 save). Offsets are file offsets; ROM bus = `0x08000000 | off`.

## Encoding — verified
- **16-bit little-endian codes**, one per character, even-aligned. No Shift-JIS anywhere (`jp_left.py --sjis` finds 0 runs).
- Glyph codes are `0x000-0x1FF` (the drawer masks `code & 0x1FF`). Order is the font's own charset, not JIS:
  `000` blank (also the space), `001-00A` 0-9, `00B-05C` katakana gojuon + voiced + small (`037`/`038` drawn as Ⅱ/Ⅲ in the ヰ/ヱ slots),
  `05D` ヴ, `05E-077` A-Z, `078-098` symbols, `099-0EA` hiragana (= katakana + 0x8E), `0EB-104` a-z, `105-1FF` kanji
  (`110`/`111` = 『』). Generator: `tools/gen_jp_tbl.py` -> `tbl/jp.tbl`; kanji in `tbl/kanji.txt`: all 249 cells
  read off the font (8 px wide, so many are squeezed) and each used one checked against its words in the script
  (e.g. `10F` 宝物庫, `1ED` ティナ様, `1E5` 二億光年). `18E`/`18F` (宿命, one use) and `1DC` (霊道) are guesses;
  19 cells no page uses are marked `# unused`. Every one of the 4133 pages now decodes with no hex left.
- Verified by decoding page 0x7F236 = "・・・遠くから なみのおとが聞こえる・・・" exactly as shown on screen in the
  opening cutscene (`work/states/cut1_f3000.mss` + ~400 frames), and by every one of 4133 pages decoding to
  plausible Japanese (`python -X utf8 tools/dec.py --msg 0 1 ... `).
- Symbol cells `078-098` were read off the font by eye; `085`/`086`/`087` (、。．), `089` (；), `08A`/`08B` (’”) and
  `096` (◎) were guesses; re-read at 4x zoom in Phase 5 (`tools/font_sheet.py --first 0x84 --count 20 --zoom 4`): the
  shapes match, and `089`/`096` are used by no string, so nothing depends on them.
- 230 distinct kanji cells are used by the script (`105-1FF`: 251 cells incl. 『』).

## Control codes — verified (by the copy routine at 0x0802ED8A and a whole-script check)
- `0x8000 | n`: **end of page**, where `n` = the page's character count. Every one of the 4133 pages has
  `n` equal to its glyph count (test: `tests/test_text.py`). The insert step must write the new count.
  Bit 14 (`0x4000`) is preserved by the copy routine; no page uses it.
- `(c & 0x0E00) == 0x0200`: insert argument string `c & 0xFF` (from the caller's arg list). Not used by any page
  in the message table.
- No newline code: a page is one line; a message is a list of pages (the box shows lines one after another).

## Pointers — verified
- **Message table** at `0x212B6C`: 1528 × u32 bus pointers (message ids 0-1527), referenced from code at
  `0x3102C` (literal pool). Each points into the page-list area `0x21434C-0x219BC0`.
- **Page lists**: NULL-terminated u32 arrays of page pointers. Lists overlap (a message id may point into the
  middle of another's list), so lists must be rebuilt as a whole, not per message.
- Pages live in `0x7ECB4-0x9C140` (4133 distinct pages, tiling the range exactly; pages of digits such as
  `0x7EF20` look like data but are text). `0x9C140` on is data, then the system strings (§Text inventory).
- Messages 0-26 include debug/test event names (ヌルイベント, イベントテスト0, カイワテスト0, バトルカイシ,
  トークバトルテスト...): leftover debug event hooks worth following for the Phase 2 warp tool.

## Unpack / repack — verified (Phase 3, `tests/test_build.py`)
- `tools/msgs.py` `Script.unpack` reads table -> page-list area (5661 words, every non-zero word a page pointer) ->
  4133 pages; `repack` writes them back in place (identity: `build.py --identity` prints `identical`) or, with
  `base=`, writes pages + the whole page-list area to free space and repoints the 1528 table entries.
- Relocation is safe for text: a 2-aligned scan of the ROM finds no u32 pointing at a page outside the list area
  (26 matches, all inside packed graphics/PCM, none 4-aligned in code) and only 2 matches for a list address outside
  the table (`0xF71C4`, `0x394330`: both inside sample data). Longest page: 22 glyphs (176 px at the fixed 8 px pitch).

## Text inventory — verified (Phase 4, `tests/test_script.py`)
`tools/script_tsv.py extract` writes `script/*.tsv` (columns `id ref jp en notes`; id = ROM offset). 4663 rows:
- **4133 pages** (`pXXXXXX`, `script/msg_NNNN.tsv` by first message, 100 messages per file; `ref` = `m<msg>.<page>`).
  They tile `0x7ECB4-0x9C140` exactly (no gaps, no overlaps); every message 0-1527 has at least one page.
- **530 system strings** (`sXXXXXX`), same encoding, stored back to back and reached only by u32 pointers
  (`ref` = holder offsets; every string has one, none lands mid-string). Holders: code pools (`0x3112C`, `0x373DC`,
  `0x2E6E8-0x2E768`) and the tables at `0x219C20-0x21BB70` (right after the page lists).
  - `0x9C610-0x9D030` `sys_menu`: file menu (ＲＥＣＯＲＤ1, ＮＥＷ ＧＡＭＥ, the help line "ゲームを 最初からはじめます。"),
    delete/save prompts, 60-odd area names (パパン寺院 ほんでん ...), save messages.
  - `0x9D510-0x9F6B4` `sys_items`: equip menus, battle card / support friend / item descriptions.
  - `0x9F6C4-0xA0632` `sys_battle`: battle and talk-battle lines, item pickups.
  - `0x669F4-0x66A04` (in `sys_menu`): cursor strings ▼, blank, ▶, blank.
- Data inside those ranges (not text): `0x9C140-0x9C610` records (ptr `0x3112C`), `0x9CFB2` 2-byte pad,
  `0x9D030-0x9D510` u16 lists (ptrs `0x219F90-0x21A09C`), `0x9F6B4-0x9F6C4` u16 0..7 (ptr `0x373DC`); palettes
  start at `0xA0632`.
- **Argument codes** `0x0200-0x0203` = `{arg0}`-`{arg3}` (names, numbers inserted by the battle code), counted in
  the end code's word count like glyphs. 50 system strings use them; no page does.
- **End code bit 14** (`0xC0nn`): 11 battle lines (ワンダァーーーッ！！, 相打ち！ ...). Meaning unknown (wait for input?);
  kept as a trailing `{endflag}` token that `script_tsv.encode` turns back into the bit. Keep it in `en`.
- Search for text elsewhere: an even-aligned scan for `n` codes + `0x8000|n` outside these areas found only noise
  (1-2 glyph hits in graphics/PCM), and every u32 in code / `0x1F0000-0x21C000` / `0x300000-0x30E000` pointing at a
  valid string lands in the areas above. Pointers from `0xA8000-0x1F0000` (PCM) into the system area are chance
  matches and are ignored.

## Font — verified (draw path)
- Glyph upload at `0x0802F172-0x0802F1B2`: font `f` (0/1) has glyph base `*(0x082122D4 + 4f)` = `0x080517EC` and a
  per-code pointer table `*(0x082122DC + 4f)` (`0x08210A98` font 0, `0x08211298` font 1). For a code:
  `idx = u16 at ptrtab[code & 0x1FF]`, glyph = 64 bytes at `glyphbase + idx*64`, DMA'd to VRAM as two 4bpp 8×8
  tiles = **one 8×16 cell per character**. Render: `python -X utf8 tools/font_sheet.py ROM out.png --first 0x100`.
- The text box shows 8 px per character (fixed pitch); English uses the VWF hook (§VWF and pair encoding).

## Free space — verified
- `0x70F96C-0x7FFFFF` (~961 KiB of 0xFF at the ROM end; the last data is the credits LZ block ending at `0x70F96B`).
  **Trap test:** `tools/lua/gba_romreads.lua` watching `0x0870F96C-0x087FFFFF` over cold boot -> new game ->
  opening cutscene -> stage 1 (`tools/routes/newgame.txt --mash 40 --frames 6000`) logged no reads; the same run
  watching the page range logged the page reader `0x0802ED8A` (positive control). No 4-aligned u32 in code or
  tables points into the tail (665 hits, all inside packed/PCM data). Pinned by `tests/test_graphics.py`.
- The ROM can grow to 16 MiB (EEPROM games keep working ≤16 MiB; ship BPS). Plan: new script and font go at
  `0x710000` first, then past 8 MiB if needed.
- `0x21C000-0x2FFFFF` (912 KiB of 0xFF) is a second candidate; not trap-tested.

## Other code addresses seen
- `0x0802ED8A`: page reader (copies a page to a RAM buffer, `ldrh r1,[r7]`). `0x03000158-0x030002D0`: IWRAM
  routine reading `0x189BD4-0x1F38E3` during the intro: that range is PCM sample data (see graphics.md), so this is
  most likely the sound mixer, not a graphics decompressor.
- `tools/gbacomp.py scan` finds 170 BIOS-LZ77 blocks (1.7 MB unpacked); none hold text.

## Box drawing — verified (Phase 5, probes `tools/lua/textobj.lua`, `typecall.lua`, `textput.lua`)
- One text object at `0x0202C790` (0x18 bytes): `+2` n = cells used this frame, `+4` glyph buffer (66 codes,
  `0x0202C7A8`), `+8` VRAM base `0x06008000`, `+0xC` tilemap shadow (`0x0202D44C`, BG0, 32 entries per row),
  `+0x10` h = `0x37F`, `+0x12` bit 0 "uploaded", `+0x14/+0x15` s8 x/y offsets. Byte `0x0202C790+0x138` == 2 selects
  font 1 (glyph background value 1 = opaque black: the top box); else font 0 (background 0, transparent).
- `text_put(src, x, y, cells, flags)` `0x0802E79C` -> `type_line(obj, src, x, y, [sp] cells, [sp+4] flags)`
  `0x0802E7F8`: one 8x16 cell per code; cell j -> tiles `h-1-2n` / `h-2n` (n counts glyphs, spaces get the blank
  tile `0x201`); when the string ends before `cells`, the rest is blank-mapped; `src = 0` blank-maps `cells`.
  The glyph upload `0x0802F108` (called per frame by `0x0802DE00`) DMAs each buffered glyph to its tiles.
- Dialogue box (state `0x0202C8D0`): two line buffers at `+0xA4` / `+0xD0` (0x2C bytes); the page copy
  `0x0802ED3C` (called at `0x0802FBD4`) keeps **22 codes** per line and expands argument codes; the reveal
  (`[+6]` line, `[+7]` codes shown) caps a line at 21 codes. Each frame `0x0802F740-0x0802F804` re-types the shown
  lines: completed line `text_put(buf, x, y, 21)`, current line `text_put(buf, x, y, k)` then blank fill from
  `x+k`, 21-k cells; empty line blank 21 cells. Line 2 is at y+2. Cursor ▼ via `text_put` at col 27 (bottom) /
  col 22 (top).
- Box choice: `0x0802F580(r0)`: r0 = 0 **top box** (x=1, y=3/5, portrait on the right, font 1), else **bottom box**
  (x=3, y=15/17). Events pass the runner byte `0x0203B3F0+0x12` (`0x08039394`); talk battles open the top box
  (`0x080379E8`); battle lines show in the bottom box (`0x08039B3B`). `tools/lua/boxlog.lua` logs each open.

## VWF and pair encoding — verified (Phase 5, `tools/vwf.py`, `tests/test_vwf.py`, shots in work/qa/p5)
- Hook at `type_line` (`push {r4-r7,lr}` kept, then a jump to `0x08710000`). For a string it draws every code at
  its own width straight into the cells (OR of 4bpp rows, glyphs up to 16 px wide), clears the cells first (to
  `0x11111111` under font 1), maps max(cells, region) tilemap cells (past the ink: `0x201`), adds the cells to n and
  records (y, x, end) for the row at `[obj+4] + 4*(y&3)`; the blank fill that follows starts after the recorded
  end. Bottom-box rows (y 15/17, region ending at col 24) are widened to col 27: **24 cells**. The upload routine
  now only sets its flag (`0x0802F12A: b 0x0802F1B4`). Cells = (advance + 6) / 8 (the last pixel is the gap).
- The hook clears and draws into a RAM scratch (`0x0203F000`, 32 cells x 64 B) and then copies the cells to VRAM,
  so a re-typed line never shows a cleared or half-drawn state (bug B1: drawing straight into VRAM tore lines whenever
  the per-frame re-type ran while the screen scanned the box). Free RAM: nothing writes `0x0203C300-0x0203FFFF`
  after boot in 9 scenes (`tools/lua/ramfree.lua`) and no code literal points past `0x0203C2E0`. The text task's
  stack is small and low (sp `0x030029C4` at `type_line`, `tools/lua/spprobe.lua`; boot sp_usr `0x03007DA0`), so no
  stack buffers in the hook. Tests: `tests/test_vwf_emu.py` (Unicorn); in-game: `tools/flicker.py` on a
  `--shot-every 2` run.
- **Pair codes**: `0x4000 | i1 << 7 | i2`, two characters by index into the English glyph set (index 0 = none;
  indices with `(i & 0x1C) == 4` unused, so no code has bits 9-11 = 001, the copy's argument test). A 22-code line
  holds 44 characters. Every English string (pages and system strings) is pair-encoded; game codes still work
  (Japanese keeps its own glyphs at 8 px, so untranslated rows show as before).
- Font: `fonts/vwf_en.png` + `.tsv` (Lato Bold 13 px rendered to 16 levels, `tools/vwf_font.py`), 89 glyphs.

## Box widths — the width gate (measured, Phase 5)
| Variant | Where | Budget (ink px / codes) | Measured |
|---|---|---|---|
| Dialogue, bottom box | events, battle lines | 192 / 21, 2 lines per box | `p07F28E` = "Mmm, we walked the whole w'" (192 px) ends at col 26, clear of ▼ (work/qa/p5/stress) |
| Dialogue, top box | portrait events, talk battles | 168 / 21 | `p0974EA` 167 px stops before the portrait (work/qa/p5/top2) |
| Choice answer | pages of the 47 choice-list messages (`docs/re/choices.tsv`) | 72 / 9 cells | 2-column grid: top box cursor col 2 / 12, text col 3 / 13 (original `work/qa/warps/ev_0160b`); bottom box the same +2 cols. A 168 px marker in column 1 ran under column 2, and column 2 past the box (`work/qa/marker2/ev_0160b`, `debug_viewer`) |
| File menu | RECORD n / NEW GAME / area in slot / help | 15 / 30 / 15 / 26 cells (x 8 px) | `textput.lua` regions |
| Pause info box | item, card, support descriptions | 28 cells (224 px), 3 lines | `textput.lua` regions |
| Name fields (args) | talk-battle names | 8 cells | `textput.lua`, RAM `0x0202C934..` |
Per-message box: `docs/re/msg_boxes.tsv` (from boxlog runs; unseen messages take the top box, 168 px). Per-string
regions: `docs/re/sys_regions.tsv`. Both written by `tools/boxmap.py`; `tools/lint.py` applies them.
Glyph torture line (all ASCII, … — ‘ ’ “ ” é, double spaces, × ♪ ▼) renders correctly (work/qa/p5/stress).
