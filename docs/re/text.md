# Text engine

Dump: `rom.sha1` (8 MiB, header `FANTCHILDREN` / `BFCJ`, EEPROM_V124 save). Offsets are file offsets; ROM bus = `0x08000000 | off`.

## Encoding — verified
- **16-bit little-endian codes**, one per character, even-aligned. No Shift-JIS anywhere (`jp_left.py --sjis` finds 0 runs).
- Glyph codes are `0x000-0x1FF` (the drawer masks `code & 0x1FF`). Order is the font's own charset, not JIS:
  `000` blank (also the space), `001-00A` 0-9, `00B-05C` katakana gojuon + voiced + small (`037`/`038` drawn as Ⅱ/Ⅲ in the ヰ/ヱ slots),
  `05D` ヴ, `05E-077` A-Z, `078-098` symbols, `099-0EA` hiragana (= katakana + 0x8E), `0EB-104` a-z, `105-1FF` kanji
  (`110`/`111` = 『』). Generator: `tools/gen_jp_tbl.py` -> `tbl/jp.tbl`; kanji go in `tbl/kanji.txt` (not read yet).
- Verified by decoding page 0x7F236 = "・・・遠くから なみのおとが聞こえる・・・" exactly as shown on screen in the
  opening cutscene (`work/states/cut1_f3000.mss` + ~400 frames), and by every one of 4133 pages decoding to
  plausible Japanese (`python -X utf8 tools/dec.py --msg 0 1 ... `).
- Symbol cells `078-098` were read off the font by eye; `085`/`086`/`087` (、。．), `089` (；), `08A`/`08B` (’”) and
  `096` (◎) are **guesses** to confirm in the marker build.
- 230 distinct kanji are used by the script (`105-1FF`, 251 cells).

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
- Pages live in `0x7ECB4-0x9C2B0` (4133 distinct pages). That range also holds non-text data (e.g. `0x7EF20`
  has small u16 values ending in `0x8009`), so extract by pointer, never by scanning the range.
- Messages 0-26 include debug/test event names (ヌルイベント, イベントテスト0, カイワテスト0, バトルカイシ,
  トークバトルテスト...): leftover debug event hooks worth following for the Phase 2 warp tool.

## Font — verified (draw path)
- Glyph upload at `0x0802F172-0x0802F1B2`: font `f` (0/1) has glyph base `*(0x082122D4 + 4f)` = `0x080517EC` and a
  per-code pointer table `*(0x082122DC + 4f)` (`0x08210A98` font 0, `0x08211298` font 1). For a code:
  `idx = u16 at ptrtab[code & 0x1FF]`, glyph = 64 bytes at `glyphbase + idx*64`, DMA'd to VRAM as two 4bpp 8×8
  tiles = **one 8×16 cell per character**. Render: `python -X utf8 tools/font_sheet.py ROM out.png --first 0x100`.
- The text box shows 8 px per character (fixed pitch). English will need a VWF or a narrower-pitch hack
  (Phase 5 spike); the per-code index indirection makes it easy to repoint codes to new glyphs.

## Free space — candidates (not yet trap-tested)
- `0x70F96C-0x7FFFFF` (~985 KiB of 0xFF at the ROM end).
- The ROM can grow to 16 MiB (EEPROM games keep working ≤16 MiB; ship BPS). Appending past 8 MiB is the safest home
  for the new script and font.

## Other code addresses seen
- `0x0802ED8A`: page reader (copies a page to a RAM buffer, `ldrh r1,[r7]`). `0x03000158-0x030002D0`: IWRAM
  decompressor reading `0x189BD4-0x1F38E3` (intro/cutscene graphics stream).
- `tools/gbacomp.py scan` finds 170 BIOS-LZ77 blocks (1.7 MB unpacked); none hold text.
