# Graphics text survey

Two passes: a tour of the original ROM (boot, intro, title, file select, opening cutscene, stage 1) and a static
sweep of the whole ROM (2026-11-14). Pinned by `tests/test_graphics.py`.

## Japanese elements

| # | Screen | Element | Kind | Source | State | Plan |
|---|---|---|---|---|---|---|
| G1 | Title | Logo ファンタジックチルドレン (small "FANTASTIC CHILDREN" above) | 8bpp BG | inside the 4 title backgrounds, LZ77 blocks `0x30E21C`, `0x36A414`, `0x3725F4`, `0x378E30` (38464 B each, one per title variant) | verified (sweep sheet, gba8) | **Done** (English logo in all 4, in-game shots; §Title backgrounds) |
| G2 | Title | Copyright "© なかむらたかし／日本アニメーション・FC製作委員会 2004 / © BANDAI 2005" | 8bpp BG | same 4 blocks, bottom rows | verified (sweep sheet) | **Done**: "©T.NAKAMURA/NIPPON ANIMATION / FC PRODUCTION COMMITTEE 2004 / © BANDAI 2005" in the G6 font, all 4 |
| G3 | Boot | Developer logo インディ・クリエイツ | 4bpp tiles, raw | `~0x30CC00-0x30D000`, next to the BANDAI logo tiles (`0x30C800-0x30E200`); stride not pinned yet | verified: BG1 of the 3rd boot screen (f600), raw tiles 3-0x30 at `0x30D3BC`, map rows 8-10 cols 6-23 | **Done**: "INTI CREATES" (`tools/devlogo_gfx.py`, `gfx/devlogo.png`; shot `work/qa/p8/g3_en`) |
| G5 | Staff roll | Credits pages: roles and names in kana/kanji (プロデューサー, サウンド, 日本アニメーション...) mixed with "INTI ALL STAFF" | 4bpp tiles, 8×16 glyphs as tile pairs | 8 LZ77 blocks `0x709094`, `0x70A4D4`, `0x70AF18`, `0x70C5B0`, `0x70D32C`, `0x70E2EC`, `0x70EC24`, `0x70F174` (end at `0x70F96C`) | verified (sweep sheet; engine 0x0803D484, §Staff roll) | **Done**: 18 English cards (`tools/staff_gfx.py`, `gfx/staff.tsv`, `gfx/staff_NN.png`; D13), shots `work/qa/p8/g5_en`, `g5_en2` |
| G6 | Debug only? | 8×8 font: ASCII + half-width katakana (JIS X 0201 order) | 4bpp tiles, raw | `0x40000-0x40C00` | verified (sweep sheet) | Probably the debug/test menu print font; translate only if a player-visible screen uses it |
| G4 | Intro / cutscenes | Book pages with pseudo-handwriting, stage map backgrounds with English place names | 4bpp LZ77 (`0x3279A4-0x33EE80`) | — | not Japanese; no change |

Already English in the original: BANDAI and GAME BOY logos, PUSH START BUTTON, START GAME / DELETE GAME, NEW GAME
slots, HUD name plate (TOMA), HUD counters, map place names, talk-battle command sprites (`0x6A7000-0x6A9800`).

Font-drawn (text work, not graphics): intro and cutscene captions, the file-select help line
"ゲームを 最初からはじめます。 / A:決定 B:もどる" (8×16 dialogue font; source string not yet matched to the message
table — check in the marker build).

## Static sweep: what was covered

Tools: `tools/rommap.py` (coarse class per 2 KiB), `tools/gfx_sweep.py lz|raw` (labelled sheets with offsets; prints
and indexes every skipped region). Sheets in `work/sweep/` (regenerate; gitignored).

| Region | Content | How checked |
|---|---|---|
| all 170 BIOS-LZ77 blocks (`gbacomp.py scan`) | stage tilesets, cutscene stills (5 KB blocks, `0x391740-0x3E5908`), tilemaps (`0x3F2904-0x3FDE38`, noise as tiles), title BGs (8bpp), credits | every block rendered gba4 (zoom 1), title blocks gba8, credits zoom 3; 1 block under 512 B skipped (`0x39170C`, palette/map) |
| `0x000000-0x040000` | ARM/Thumb code | raw sheet (noise) |
| `0x040000-0x040C00` | 8×8 half-width font (G6) | zoom 3 |
| `0x050000-0x062000` | 8×16 dialogue font (`0x517EC`, see text.md) | raw sheet |
| `0x07ECB4-0x09C2B0` | script pages | text.md |
| `0x0A8000-0x1F0000` | **signed 8-bit PCM samples**, not graphics (bytes small and smooth: 60-100% of byte-to-byte deltas under 24; raw sheets are noise). Includes `0x189BD4-0x1F38E3`, which the IWRAM routine at `0x03000158` streams during the intro: audio, not the cutscene graphics as first guessed | rommap + delta statistic (guess, strong); confirm if sound work is ever needed |
| `0x1F0000-0x21C000` | sequence/pointer data, message table, page lists | raw sheet, text.md |
| `0x21C000-0x300000` | 0xFF fill | skipped: fill |
| `0x300000-0x30E000` | BANDAI + developer logo tiles (G3), small UI bits | zoom 3 |
| gaps between LZ blocks `0x3E7000-0x4B2800` | tilemaps / level data (u16 stripes) | raw sheets |
| `0x4D0000-0x560000` | tilemaps (u16 stripes) | raw sheet |
| `0x560000-0x6F0000` | sprites (1D-mapped, so no fixed stride reads cleanly), 8bpp portraits `0x657000-0x695000`, effects `0x69E000-0x6A1000`, command sprites `0x6A7000-0x6A9800` (English) | raw sheets at 128/32/8 tiles per row; **no Japanese seen, but sprite text could hide at a wrong stride** |
| `0x6F0000-0x70F96C` | credits LZ blocks (G5) and small data | sweep |
| `0x70F96C-0x800000` | 0xFF fill, free (text.md) | skipped: fill |

## Title backgrounds (G1/G2) — verified 2026-11-15
- Each of the 4 variants is one LZ77 block of 601 8bpp tiles: tile 0 blank, tiles 1-600 = the 30x20 screen in
  reading order (no map edits needed); 256-colour palette in the next archive record (512 B just after the block;
  matches palette RAM at the title, `work/qa/p8/title_ppu`. The earlier "512 B before" guess was wrong).
- Which variant shows: `0x080316D0` counts the endings seen (bits 0-2 of `0x0202DC56`, from the save) and loads
  archive record `0x0830D000 + 20 * table[0x08219C1C + count]` (42, 2, 40, 41): none -> variant 3 (dark, the
  normal title), one -> 0, two -> 1, three -> 2. Warp scenes `title`, `title_1`..`title_3` (`clears=N`).
- **Done 2026-11-15:** `tools/title_logo.py FONT` writes `gfx/title_<n>.png`: the old logo and copyright are the
  pixels whose colour agrees across all 4 variants (the backgrounds differ), inpainted per variant; the new logo is
  "FANTASTIC CHILDREN" in Bebas Neue (OFL, `docs/fonts.md`), cap 22 px, 3 px tracking, the original's blue-to-cyan
  fill, silver outline, navy extrusion; copyright in the game's own G6 8×8 font (R redrawn, © hand-drawn):
  "©T.NAKAMURA/NIPPON ANIMATION", "FC PRODUCTION COMMITTEE 2004", "© BANDAI 2005". All 4 pack smaller than their
  slots (in place). `insert.build_rom` applies every `gfx/title_<n>.png`. Shots: `work/qa/p8/title_en*`.
- Archive records (12 B: u32 offset relative to the record, u32 packed size rounded up to 4, u32 flags `0x00420100`)
  at `0x30D028`, `0x30D320`, `0x30D334`, `0x30D348`. Found by `tools/lua/lzcaller.lua` (BIOS copy of the palette at
  f284, caller `0x08002F41`) and a self-relative offset scan. `tools/gbacomp.py compress` re-packs all 4 unedited
  blocks to exactly the record sizes; bigger art is moved (`tools/title_gfx.py apply(alloc=...)`, test in
  `tests/test_title_gfx.py`).

## Staff roll (G5) — verified 2026-11-15

Game mode 8 (warp scene `staff`), BG1 over the art. Routine 0x0803D484 shows card r0+1 of 18: table 0x0821BB70
(8 bytes per card: u32 pointer to a full 30x20 u16 map in ROM at 0x0A0634-0x0A5B73, u8 archive index 10-17). Archive
records 0x087060EC + 20*index: tile block (self-relative u32 offset, packed size, flags 0x00220100, BIOS LZ77 4bpp)
then a 32-byte palette (0 transparent, 1-15 grey ramp). The whole block goes to VRAM slot by card parity (table
0x0821BC00): even cards tile 0x201 (200 tiles before the odd slot), odd cards 0x2C9 (247 before BG0's blank 0x3C0);
map cells are block-relative (0 = blank). 8 blocks are shared by 1-3 cards (`staff_gfx.py export` prints which).
English: `tools/staff_gfx.py render Oswald[wght].ttf` writes `gfx/staff_NN.png` from `gfx/staff.tsv`; the build
dedups tiles per block (39-55 tiles each), rewrites maps and blocks in place (`tests/test_staff_gfx.py`). Cards
change about every 300 frames from the `staff` state; the epilogue ("10 years later.") follows card 17.

## Still to survey
- 2026-11-15: OBJ VRAM dumped on pause / pause_support / pause_items / battle_01 / gameover (`work/qa/p8/obj/`,
  original ROM): no Japanese. The pause action-bar card faces are English in the original (Punch, Kick, Chop, Guard;
  raw 4bpp at `0x69BDF0`, `0x69C590`, ...); GAME OVER / "Press START to continue" are English. The remaining
  screens are covered by the Phase 8 tour sheets.
- Sprites (`0x560000-0x6F0000`) are only proven text-free where a stride read cleanly. Cover them by VRAM/OAM capture
  on every screen the Phase 2 debug tool reaches (pause/menu/status, talk battle, stage title cards, boss banners,
  game over, ending, staff roll) and add any Japanese found here.
- Pin G3's exact tile range and stride when redrawing it (runtime VRAM dump of the boot logo).
