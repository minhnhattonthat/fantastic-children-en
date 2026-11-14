# Status

Updated at the end of every session. Keep it to what the next session needs; history is in git.

- **Phase:** 2. Debug tool next (Phase 1 research and recon done 2026-11-14). Last build: none yet.
- **Done:**
  - Step 0: MesenCE 2.2.1 + GBA BIOS in `tools/mesen/`; smoke boots the original to the title menu (`tools/routes/boot.txt`); start/route input and Lua probe logging verified; guard hook blocks `sed -i`; pre-commit runs `tools/check.py` and rejects a failing test; rulings D1-D7 in `docs/decisions.md`.
  - Phase 1 text recon (`docs/re/text.md`): 16-bit codes in the font's own charset order; `0x8000|count` page end; message table 0x212B6C (1528) -> page lists -> 4133 pages in 0x7ECB4-0x9C2B0; font draw path and glyph format (8×16 4bpp, per-code index table); `tools/gen_jp_tbl.py` -> `tbl/jp.tbl`; `tools/dec.py`; `tests/test_text.py`.
  - Phase 1 graphics survey (`docs/re/graphics.md`, `tests/test_graphics.py`): static sweep of all 170 LZ77 blocks and the raw ROM (`tools/rommap.py`, `tools/gfx_sweep.py`). Found: title logo + copyright in 4 LZ 8bpp title BGs (G1/G2), developer logo tiles ~0x30CC00 (G3), staff roll in 8 LZ blocks 0x709094-0x70F96C (G5), 8×8 half-width debug font 0x40000 (G6). 0xA8000-0x1F0000 is PCM audio, not graphics.
  - Free space verified: 0x70F96C-0x7FFFFF unread from boot to stage 1 (trap test with positive control) and unreferenced; ROM may grow to 16 MiB.
  - Savestates (gitignored, regenerate with the new-game route + `--mash 40 --state-every 1000`): `work/states/fileselect_f2000.mss`, `cut1_f3000.mss` (opening cutscene typing), `stage1_f5000.mss` (stage 1 action).
- **Next:**
  1. Phase 2 debug tool: follow the debug event names in messages 0-26 (イベントテスト, カイワテスト, トークバトルテスト) and the event/scene variables (RAM search) to build `tools/debug/warp.lua` + `tools/debug/scenes.gba.txt` (one entry per stage/chapter, talk battle, menus, game over, ending, staff roll), each reached from a cold boot with a shot.
  2. While warping: VRAM/OAM capture of every screen for sprite text (sprites 0x560000-0x6F0000 only partly proven text-free) and pin G3's tile range; add finds to `docs/re/graphics.md`. Check whether any player-visible screen uses the G6 8×8 font.
  3. Kanji cells 0x105-0x1FF (230 used) into `tbl/kanji.txt` before Phase 4 (template match + careful reading at zoom 6+).
- **Open bugs:** none.
- **Waiting on the user:** nothing.
