# Skill gotchas

One line per gotcha: the skill reference it belongs in, then the fact.

- scripts/fetch_emu.py / references/setup.md: `fetch_emu.py gba-bios` 404s: retrobios renamed the file to `bios/Nintendo/Game Boy Advance/GBA_bios.rom` (same SHA-1 300c20df6731a33952ded8c436f7f186d25d3492). Downloaded by hand to tools/mesen/Firmware/gba_bios.bin.
- scripts/tbl.py: `Table.decode` runs until an `{end}`/`{goto}` name; a game whose page-end code carries data in its low bits (here `0x8000|count`, 23 codes) needs its own page splitter (tools/dec.py) or a generic "stop on any code matching a mask" option.
- references/graphics.md §Survey: big "unknown packed" regions may be PCM audio, not custom-compressed graphics: a byte-delta statistic (share of |b[i]-b[i-1]| < 24 as signed bytes; PCM 0.6-1.0, packed data ~0.1-0.5) sorted 1.3 MB here in one step (`tools/rommap.py` + note in docs/re/graphics.md). Also: 1D-mapped sprite banks read as diagonal noise at any fixed tiles-per-row; cover them by VRAM capture, not by static sheets.
- SKILL.md / emulator-qa.md: with the context-mode plugin, reading a >~40-line disassembly or log in one go gets indexed away; read in chunks of <=50 lines with offset/limit.
