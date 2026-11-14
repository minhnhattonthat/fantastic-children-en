# Skill gotchas

One line per gotcha: the skill reference it belongs in, then the fact.

- scripts/fetch_emu.py / references/setup.md: `fetch_emu.py gba-bios` 404s: retrobios renamed the file to `bios/Nintendo/Game Boy Advance/GBA_bios.rom` (same SHA-1 300c20df6731a33952ded8c436f7f186d25d3492). Downloaded by hand to tools/mesen/Firmware/gba_bios.bin.
- scripts/tbl.py: `Table.decode` runs until an `{end}`/`{goto}` name; a game whose page-end code carries data in its low bits (here `0x8000|count`, 23 codes) needs its own page splitter (tools/dec.py) or a generic "stop on any code matching a mask" option.
- SKILL.md / emulator-qa.md: with the context-mode plugin, reading a >~40-line disassembly or log in one go gets indexed away; read in chunks of <=50 lines with offset/limit.
