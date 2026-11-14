-- typecall.lua: log every call of the line typer 0x0802E7F8 (r0 obj, r1 src, r2 x, r3 y, [sp] count, [sp+4] flags)
-- and of the glyph upload 0x0802F108. Phase 5 RE of the dialogue box.
local function reg(s, n) return s["cpu.r" .. n] or s["cpu.r[" .. n .. "]"] or -1 end
local count = 0
L.on_exec(0x0802E7F8, 0x0802E7F8, function()
  count = count + 1
  if count > (MAXLOG or 60) then return end
  local s = emu.getState()
  local sp = reg(s, 13)
  local src = reg(s, 1)
  L.log(string.format("TYPE %d obj=%08X src=%08X x=%d y=%d cnt=%d fl=%X lr=%08X first=%04X n=%d",
    L.frame, reg(s, 0), src, reg(s, 2) & 0xFFFF, reg(s, 3) & 0xFFFF,
    emu.read32(sp, emu.memType.gbaMemory), emu.read32(sp + 4, emu.memType.gbaMemory), reg(s, 14),
    emu.read16(src, emu.memType.gbaMemory), emu.read16(reg(s, 0) + 2, emu.memType.gbaMemory)))
end)
