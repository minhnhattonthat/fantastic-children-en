# Graphics text survey

Two passes: a tour of the original ROM (boot, intro, title, file select, opening cutscene, stage 1) and a static
sweep of the whole ROM (2026-11-14). Pinned by `tests/test_graphics.py`.

## Japanese elements

| # | Screen | Element | Kind | Source | State | Plan |
|---|---|---|---|---|---|---|
| G1 | Title | Logo ファンタジックチルドレン (small "FANTASTIC CHILDREN" above) | 8bpp BG | inside the 4 title backgrounds, LZ77 blocks `0x30E21C`, `0x36A414`, `0x3725F4`, `0x378E30` (38464 B each, one per title variant) | verified (sweep sheet, gba8) | Redraw as an English logo in all 4 (D5) |
| G2 | Title | Copyright "© なかむらたかし／日本アニメーション・FC製作委員会 2004 / © BANDAI 2005" | 8bpp BG | same 4 blocks, bottom rows | verified (sweep sheet) | Redraw in English: "© Takashi Nakamura / Nippon Animation, FC Production Committee 2004" |
| G3 | Boot | Developer logo インディ・クリエイツ | 4bpp tiles, raw | `~0x30CC00-0x30D000`, next to the BANDAI logo tiles (`0x30C800-0x30E200`); stride not pinned yet | guess (sweep sheet, stride off) | Romanized name (check the company's own: "Inti Creates"; the credits already say "INTI ALL STAFF") |
| G5 | Staff roll | Credits pages: roles and names in kana/kanji (プロデューサー, サウンド, 日本アニメーション...) mixed with "INTI ALL STAFF" | 4bpp tiles, 8×16 glyphs as tile pairs | 8 LZ77 blocks `0x709094`, `0x70A4D4`, `0x70AF18`, `0x70C5B0`, `0x70D32C`, `0x70E2EC`, `0x70EC24`, `0x70F174` (end at `0x70F96C`) | verified (sweep sheet) | English credits (D3): redraw, or replace with font-drawn text if the credits engine allows; reach via debug tool |
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

## Still to survey
- Sprites (`0x560000-0x6F0000`) are only proven text-free where a stride read cleanly. Cover them by VRAM/OAM capture
  on every screen the Phase 2 debug tool reaches (pause/menu/status, talk battle, stage title cards, boss banners,
  game over, ending, staff roll) and add any Japanese found here.
- Pin G3's exact tile range and stride when redrawing it (runtime VRAM dump of the boot logo).
