# Skill gotchas

One line per gotcha: the skill reference it belongs in, then the fact.

- scripts/fetch_emu.py / references/setup.md: `fetch_emu.py gba-bios` 404s: retrobios renamed the file to `bios/Nintendo/Game Boy Advance/GBA_bios.rom` (same SHA-1 300c20df6731a33952ded8c436f7f186d25d3492). Downloaded by hand to tools/mesen/Firmware/gba_bios.bin.
