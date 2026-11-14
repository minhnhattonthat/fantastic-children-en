# Game modes, areas and event scripts (Phase 2, for the warp tool)

Addresses are bus addresses; ROM file offset = `addr & 0x1FFFFFF`. All verified in MesenCE by poking RAM and
shooting the screen (`tools/debug/warp.lua`, `python -X utf8 tools/debug/warp_all.py`).

## Game struct `0x0202CC40`
- **Word 0** = `mode | sub << 8 | state << 16 | state2 << 24`. Main loop `0x0803283C` calls
  `*(0x08219E28 + 4*mode)`; `set_mode(struct, word)` = `0x08032888` (writes the whole word).
  | mode | handler | what |
  |---|---|---|
  | 0 | 0x08032E99 | boot / title / file select (word 0) and the new-game prologue: word `0x01000000` = prologue event (record 43) running, set right after NEW GAME, with the new game initialised |
  | 1 | 0x08033035 | load the area in the stage byte, then mode 2 |
  | 2 | 0x080331A5 | stage; sub (byte 1) jump table at `0x080331D8`: 1 play (`0x00020102` = loaded, idle), 3 fall -> game over, 4 run event `+0x1EF4` (`0x08033A38`), 5 pause, 7 -> mode 3, 11 save prompt |
  | 3 | 0x08033CAD | full-screen ("picture book") event `+0x1EF4`; the ending runs here |
  | 4 | 0x08038519 | (talk-battle screen internals; reached through events, not by poking) |
  | 5 | 0x0803506D | save prompt (セーブしますか？) |
  | 6 | 0x08035431 | pause menu: BATTLE EDIT / SUPPORT EDIT / ITEM INFO (L/R switch pages) |
  | 7 | 0x08037955 | returns to the stage |
  | 8 | 0x0803CDD1 | staff roll |
  | 9 | 0x080375F5 | GAME OVER screen |
- `+0x13C4` u32 play-time frame counter (incremented by the main loop in modes 0-7 except 5).
- `+0x1ED8` **stage byte** = `world | area << 4`. `+0x1EF4` u16 event record to run (0xFFFF none).
  `+0x1EFC` s16 talk-battle id queued by the running event (record byte `+0x19`).

## Areas
- `0x0820D0FC`: 7 world pointers -> 20-byte entries; worlds have 1, 9, 14, 10, 13, 8, 5 areas (60). Entry: `+0` area
  data pointer (0x80-byte block: behaviour table, maps), `+4/+8` start x/y (<<12), `+0xE` u16 **entry event** record
  (0xFFFF none; checked by `0x080389C8` dry run, stored to `+0x1EF4` at `0x08034B4E`), `+0x10` music/flags.
- World 0 area 0 (`00`) is an empty test room. The new game starts in `16` (beach). Picture-book areas (e.g. `01`, the
  house) run their entry event in mode 3.

## Event records `0x08066F30` (2713 × 36 bytes, up to the page area `0x0807ECB4`)
`get_event(i)` = `0x08030FF4` (count `0xA99` at `0x08030FEC`). Runner state at `0x0203B3F0` (`+0` current record
pointer). `start_event(rec, arg)` = `0x08038B74`; `resolve(rec)` = `0x08038904` follows conditional jumps first.

| offset | field |
|---|---|
| +0x00 s16, +0x02 u16 | condition: `f0 > 0`: jump to record `+2` if flag `f0` set; `f0 < 0`: jump if flag `-f0` clear; `0x7FFF` none |
| +0x0C u16 | message id shown (`get_msg` `0x08031020`; 0xFFFF none) |
| +0x0E u16 | choice-list message id (0xFFFF none) |
| +0x10, +0x12, +0x14 u16 | with a choice list: the record each answer jumps to (e.g. record 66 -> 67 / 68 / 80) |
| +0x19 u8 | talk-battle id to start after the event (0xFF none) -> `+0x1EFC`; battle table `0x0821AEE0` (90 × 16 bytes) |
| +0x1A u8 | runner byte `+0x13` |
| +0x20 u16 | next: 0xFFFF next record, 0xFFFE end of script, else jump to that record |

A **script** starts at record 0 or after an end (0xFFFE): 960 scripts, 470 with text, 88 battle ids used (82 and 89
never). Records 0-36 are leftover test events (イベントテスト, カイワテスト, トークバトルテスト); 2311-2493 is a
debug "viewer test" (character viewer, event-BG viewer). `python -X utf8 tools/events.py` lists every script
(range, messages, battles, jumps, entry-of-area, first text). Messages reached by records: 1481 of 1528 through `+0xC`;
the rest are the choice lists in `+0x0E..`.

Static script ranges (split at 0xFFFE) are not what runs: conditions, `next` jumps and choice answers cross
them (record 82's text 54/55 is reached from record 80; 1678 falls to 1679 while flag 0x88 is clear).
`events.flow(recs, start, first)` walks the real flow, both ways at each condition (`first` forces the start
record's); `gen_scenes.py` uses it for each scene's `msg=` list and adds `flags=` so a conditional first record
takes the branch with the script's own text (a `b` scene takes the other branch when it has text too); later
conditions where one way ends the script silently get their flag too (`chain()`: ev_0082b needs 0x12A then 0x12D).
`+0x1C`/`+0x1E` look like flags the record sets when it runs (s16, < 0 clears: record 84 sets 0x12A that record 82
tests; 1862/1863 toggle 0x82/0x83) — **guess**, from the data only. The warp pokes `flags=` again just before the
stage event starts: flags set before the stage load did not hold for 0x82/0x83. Every
+0x0C message of records 37+ lies on some scene's flow (`tests/test_events.py`).

Talk battles are started by short scripts ("見つけたぞ！" + battle id) attached to stage NPCs. The battle screen's
backdrop is whatever the current area's BG layer holds: area `16` garbles it, `62` (indoor) is clean, so the warp
runs battle and object scripts in `62`. Which area an NPC stands in is in the area object data (not decoded; the
warp does not need it).

## Story flags
`get_flag(n)` `0x08031098`, `set_flag(n, v)` `0x080310D4`: n = 1..0x165, bit array at `*(0x0202C9E4)`, byte `n>>3`,
bit `n&7`.

## Endings
Script 1986-2259 in mode 3. Before it runs, `0x08032B60` ranks the clear: the 75 collectible flags listed at
`0x08219E6C` (all set -> rank 2) and play time (`<= 0x6977F` frames = 2 h -> rank 4, which wins), then
rank 4 -> flag 0x85 set -> **ending B** (records 2067-2184); rank 2 -> flag 0x87 -> **ending C** (2185-2255);
otherwise flag 0x86 -> **ending A** (1988-2066). All three end in 2256-2259, then the staff roll (mode 8).
