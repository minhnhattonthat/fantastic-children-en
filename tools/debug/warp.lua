-- warp.lua: cold boot -> any scene of Fantastic Children (GBA) by name. RE notes: docs/re/events.md.
--
--   emu.py ROM --out D --script tools/debug/warp.lua --var "SCENE='area_16'" --frames 2600 --mash 40 --sheet
--   optional: --var "SCENES=[[C:/abs/scenes.gba.txt]]" (default: tools/debug/scenes.gba.txt, found relative to
--             Mesen's working folder tools/mesen), --var "STATE_OUT=[[C:/abs/x.mss]]" (save a state on arrival),
--             --var TRACE=20 (log the game-mode word every N frames), --var STOP_AFTER_SHOT=1,
--             --var PAGES=N [--var PAGE_EVERY=40] (N more shots page_NN.png after warp.png, for QA sheets)
--   emu.py --mash 40 clicks through text (it also presses A during the boot, which is harmless).
--   All scenes, checked: python -X utf8 tools/debug/warp_all.py
--
-- Log lines: "WARP <scene> <how>" on arrival, "MSG <id>" for each message the game fetches, "shot warp.png".
--
-- Scene list lines: `name  key=value ...` (# comments). Keys:
--   boot=title|filesel  stop at the title menu / file select (input only, nothing poked)
--   stg=HH      stage byte (world | area << 4, hex) loaded with game mode 1 once the new-game prologue starts
--   ev=N        event script start record (decimal) run on arrival: in place of the area's entry event when the
--               area has one (so picture-book areas run it full-screen), else as a stage event (mode 2 sub 4)
--   full=1      run ev as a full-screen event (game mode 3, the ending's mode) without loading an area
--   flags=a,b   story flags (hex, 1..0x165) set before loading; -a clears
--   play=N      play-time counter (frames); allitems=1 sets the 75 collectible flags (both pick the ending)
--   sub=N       once the stage is playing, switch mode 2 to sub-state N (3 game over, 5 pause, 11 save prompt)
--   mode=N      once the prologue starts, set game mode N directly (8 staff roll)
--   keys=a,b    buttons pressed after arrival (6 frames each, 50 apart, from arrival + 60)
--   msg=N[,M..] message ids the script can show; the shot waits for the first one fetched (warp_all.py checks it)
--   wait=N      frames from arrival to the shot (default 360)
--   textwait=N  msg= scenes: frames from the message fetch to the shot (default 60; more for a slow fade-in)
local M = emu.memType.gbaMemory
local GS = 0x0202CC40          -- game struct: word 0 = mode | sub << 8 | state << 16 | state2 << 24
local STG_B = GS + 0x1ED8      -- stage byte
local EV_H = GS + 0x1EF4       -- event record to run (u16, 0xFFFF none)
local FLAGP = 0x0202C9E4       -- pointer to the story-flag bit array (flag n: byte n>>3, bit n&7)
local PLAYING = 0x00020102     -- mode 2 sub 1 state 2: stage loaded, no event running
local PLAYTIME = GS + 0x13C4   -- u32 frame counter; the ending is B (fast clear) while it is <= 0x6977F (2 h)
local ITEM_FLAGS, ITEM_FLAGS_N = 0x08219E6C, 75   -- u16 flag ids the ending checks: all set -> ending C

local function rd32(a) return emu.read32(a, M, false) end
local function wr32(a, v) emu.write32(a, v, M) end
local function wr16(a, v) emu.write16(a, v, M) end

-- scene list
local path = SCENES or "../debug/scenes.gba.txt"
local scenes = {}
for line in io.lines(path) do
  line = line:gsub("#.*", "")
  local name, rest = line:match("^%s*(%S+)%s*(.*)$")
  if name then
    local t = {}
    for k, v in rest:gmatch("(%w+)=(%S+)") do t[k] = v end
    scenes[name] = t
  end
end
local sc = scenes[assert(SCENE, "set --var \"SCENE='name'\"")]
if not sc then error("unknown scene " .. SCENE .. " in " .. path) end

local stg = sc.stg and tonumber(sc.stg, 16)
local ev = sc.ev and tonumber(sc.ev)
local sub = sc.sub and tonumber(sc.sub)
local mode = sc.mode and tonumber(sc.mode)
local hold = tonumber(sc.wait or "360")
local textwait = tonumber(sc.textwait or "60")

local phase = "boot"           -- boot -> load -> play -> arrived
local shotAt                   -- frame of warp.png (PAGES shots follow it)
local t0, arrivedAt = 0, nil
local entryHooked = false

local function log(s) L.log(string.format("f%d %s", L.frame, s)) end

-- every message lookup (get_msg at 0x08031020, id in r0): proof of which text the scene reached
-- msg=a,b,c: any of the script's messages (flag-conditional branches pick which one shows first)
local want = nil
if sc.msg then
  want = {}
  for i in tostring(sc.msg):gmatch("%d+") do want[tonumber(i)] = true end
end
local gotMsg = want == nil
L.on_exec(0x08031020, 0x08031020, function()
  local id = emu.getState()["cpu.r0"] & 0xFFFF
  log(string.format("MSG %d", id))
  if want and want[id] and phase ~= "boot" and not gotMsg then gotMsg = L.frame end
end)

local function set_flags()
  local base = rd32(FLAGP)
  if sc.play then wr32(PLAYTIME, tonumber(sc.play)); log("play time " .. sc.play) end
  if sc.allitems then
    for i = 0, ITEM_FLAGS_N - 1 do
      local n = emu.read16(ITEM_FLAGS + 2 * i, M, false)
      local a = base + (n >> 3)
      emu.write(a, emu.read(a, M) | (1 << (n & 7)), M)
    end
    log("all " .. ITEM_FLAGS_N .. " collectible flags set")
  end
  if not sc.flags then return end
  for f in sc.flags:gmatch("[^,]+") do
    local clear = f:sub(1, 1) == "-"
    local n = tonumber(clear and f:sub(2) or f, 16)
    local a = base + (n >> 3)
    local b = emu.read(a, M)
    if clear then b = b & ~(1 << (n & 7)) else b = b | (1 << (n & 7)) end
    emu.write(a, b, M)
  end
  log("flags " .. sc.flags)
end

local function arrive(what)
  phase = "arrived"
  arrivedAt = L.frame
  log("WARP " .. SCENE .. " " .. what)
  if sc.keys then
    L.press("-", 60)
    for k in sc.keys:gmatch("[^,]+") do L.press(k, 6); L.press("-", 44) end
  end
  if STATE_OUT then L.save_state(STATE_OUT, function() log("state saved " .. STATE_OUT) end) end
end

L.on_frame(function(n)
  local w = rd32(GS)
  if TRACE and n % TRACE == 0 then log(string.format("%s word=%08X ev=%04X", phase, w, emu.read16(EV_H, M, false))) end
  if phase == "boot" then
    -- intro (~1500 frames) -> title (START) -> file select (A on NEW GAME) -> prologue event (word 0x01000000)
    -- START skips the intro to PUSH START BUTTON, START again opens the title menu, A on START GAME -> file select
    if sc.boot == "title" then
      if n == 1500 or n == 1900 then L.press("start", 6) end
      if n == 2200 then arrive("title") end
      return
    end
    if sc.boot == "filesel" then
      if n == 1500 or n == 1900 then L.press("start", 6) end
      if n == 2200 then L.press("a", 6) end
      if n == 2500 then arrive("file select") end
      return
    end
    if w == 0x01000000 then
      phase = "load"; t0 = n
      log("prologue running: new game initialised")
      return
    end
    if n >= 1500 and n % 40 == 0 then L.press((n // 40) % 2 == 0 and "start" or "a", 6) end
    return
  end
  if phase == "load" then
    if n == t0 + 10 then
      set_flags()
      if mode then wr32(GS, mode); arrive("mode " .. mode); return end
      if stg then
        emu.write(STG_B, stg, M)
        wr32(GS, 1)
        log(string.format("stage %02X loading", stg))
      elseif ev and sc.full then
        wr16(EV_H, ev); wr32(GS, 3); arrive("full-screen event " .. ev); return
      else
        arrive("prologue"); return
      end
    end
    if n > t0 + 10 and stg then
      -- the area queued its entry event: run ours in its place (same path, so the area's set-up applies)
      local cur = emu.read16(EV_H, M, false)
      if cur ~= 0xFFFF and cur ~= 0 and not entryHooked then
        if ev and cur ~= ev then wr16(EV_H, ev); log(string.format("entry event %d replaced by %d", cur, ev)) end
        entryHooked = cur
      end
      -- entry events run as a stage event (mode 2 sub 4) or, in picture-book areas, full-screen (mode 3)
      if entryHooked and ((w & 0xFFFF) == 0x0402 or (w & 0xFF) == 3) then
        arrive("area event " .. (ev or entryHooked)); return
      end
      if w == PLAYING then phase = "play"; t0 = n end
    end
    return
  end
  if phase == "play" and n == t0 + 5 then
    -- flags again: loading the stage resets some (0x82/0x83 were lost between the first poke and the event)
    if ev then set_flags(); wr16(EV_H, ev); wr32(GS, 0x0402); arrive("stage event " .. ev)
    elseif sub then wr32(GS, 2 | (sub << 8)); arrive("sub " .. sub)
    else arrive(string.format("stage %02X", stg)) end
    return
  end
  -- the shot: from arrival + wait, the first frame that is not one flat colour (fades) and, for a scene with
  -- msg=N, textwait (60) frames after the game fetched message N (text on screen); at most 600 frames later
  -- (a msg= scene shoots at fetch + textwait even inside the hold: with the mash, the box is gone by arrival + hold)
  local early = want and type(gotMsg) == "number" and n >= gotMsg + textwait
  if phase == "arrived" and (n >= arrivedAt + hold or early) and n % 10 == 0 then
    local textUp = gotMsg == true or (gotMsg and n >= gotMsg + textwait)
    if (textUp and not flat()) or n >= arrivedAt + hold + 600 then
      L.shot("warp.png"); log("shot warp.png"); phase = "done"; shotAt = n
      if STOP_AFTER_SHOT and not PAGES then L.finish(0) end
    end
  end
  -- --var PAGES=N: N more shots, one every PAGE_EVERY (40) frames, as the mash pages through the dialogue (QA sheets)
  -- (the frame just before each mash press; emu.py --mash N presses when n % N < 6. A press on a page still typing
  -- completes it, the next one turns the page, so every page is shot complete at least once; tools/qa_sheets.py
  -- drops the partly typed shots. Typing a 2-line page takes longer than 90 frames, so a slower mash doesn't help.)
  local every = PAGE_EVERY or MASH or 40
  if phase == "done" and PAGES and shotAt and n > shotAt + 3 and n % every == every - 3 then
    pagesShot = (pagesShot or 0) + 1
    L.shot(string.format("page_%02d.png", pagesShot)); log(string.format("shot page_%02d.png", pagesShot))
    if pagesShot >= PAGES and STOP_AFTER_SHOT then L.finish(0) end
  end
end)

-- true when the screen is (almost) one colour: sample a 16 x 12 grid of the frame buffer
function flat()
  local buf = emu.getScreenBuffer()
  local first, other = buf[1], 0
  for y = 0, 11 do
    for x = 0, 15 do
      local p = buf[(y * 13 + 6) * 240 + x * 15 + 8]
      if p ~= first then other = other + 1 end
    end
  end
  return other < 8
end
