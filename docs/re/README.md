# Reverse-engineering notes

One file per subsystem (text engine, pointers, compression, font, graphics). Mark every finding with how far it is
proven, so a later session doesn't build on a guess:

- **verified** - and how: a decoded known string, a corrupt-and-boot test, a breakpoint hit on the drawing path, a
  passing roundtrip test. Name the test or savestate.
- **guess** - and why it seems likely (byte pattern, another game, an earlier patch's notes). Promote it to verified
  before code depends on it.

Addresses are for the dump in `rom.sha1` unless a note says otherwise.

| File | Covers | State |
|---|---|---|
| `text.md` | 16-bit encoding, font charset order, page-end/length code, message table 0x212B6C, page lists, font draw path, free space | verified (kanji cells unread, a few symbols guessed) |
| `graphics.md` | tile-drawn Japanese: title logo, copyright, developer logo; static sweep pending | partial |

Prior work: no earlier fan translation of this game was found (web search, 2026-11-14).
