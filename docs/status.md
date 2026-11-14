# Status

Updated at the end of every session. Keep it to what the next session needs; history is in git.

- **Phase:** 1. Research and recon in progress (text engine done; graphics static sweep left). Last build: none yet (2026-11-14).
- **Done:**
  - Step 0: MesenCE 2.2.1 + GBA BIOS in `tools/mesen/`; smoke boots the original to the title menu (`tools/routes/boot.txt`); start/route input and Lua probe logging verified; guard hook blocks `sed -i`; pre-commit runs `tools/check.py` and rejects a failing test; rulings D1-D7 in `docs/decisions.md`.
  - Text recon (`docs/re/text.md`): 16-bit codes in the font's own charset order; `0x8000|count` page end; message table 0x212B6C (1528) -> page lists -> 4133 pages in 0x7ECB4-0x9C2B0; font draw path and glyph format (8×16 4bpp, per-code index table); `tools/gen_jp_tbl.py` -> `tbl/jp.tbl` (kana, Latin, symbols); `tools/dec.py` decodes pages/messages; `tests/test_text.py` pins the format.
  - Savestates (gitignored, regenerate with the new-game route + `--mash 40 --state-every 1000`): `work/states/fileselect_f2000.mss`, `cut1_f3000.mss` (opening cutscene typing), `stage1_f5000.mss` (stage 1 action).
- **Next:**
  1. Finish Phase 1 graphics survey: static sweep of the 170 LZ77 blocks + IWRAM cutscene stream + raw regions (`tiles.py render`, gba4 and gba8), list every Japanese cell in `docs/re/graphics.md`; locate the title logo/copyright tiles (G1-G3).
  2. Free-space trap test of 0x70F96C-0x7FFFFF (or plan to append past 8 MiB).
  3. Phase 2 debug tool: follow the debug event names in messages 0-26 (イベントテスト, カイワテスト, トークバトルテスト) and the event/scene variables (RAM search) to build `tools/debug/warp.lua` + `scenes.gba.txt`.
  4. Kanji cells 0x105-0x1FF (230 used) into `tbl/kanji.txt` before Phase 4 (template match + careful reading at zoom 6+).
- **Open bugs:** none.
- **Waiting on the user:** nothing.
