-- textobj.lua: log the dialogue text object (0x0202C790, 0x18 bytes) each time the glyph upload 0x0802F108 runs,
-- and the codes in its buffer. Phase 5 RE of the box layout. Usage: emu.py ROM --out D --state-in S --script this
local seen = 0
local function hex(a, n)
  local t = {}
  for i = 0, n - 1 do t[#t + 1] = string.format("%02X", emu.read(a + i, emu.memType.gbaMemory)) end
  return table.concat(t, " ")
end
L.on_exec(0x0802F108, 0x0802F108, function()
  local o = 0x0202C790
  local n = emu.read16(o + 2, emu.memType.gbaMemory)
  local f = emu.read(o + 0x12, emu.memType.gbaMemory)
  if n == 0 or (f & 1) == 1 then return end
  seen = seen + 1
  if seen > 40 then return end
  local buf = emu.read32(o + 4, emu.memType.gbaMemory)
  L.log(string.format("UP %d obj=%s buf=%08X codes=%s", L.frame, hex(o, 0x18), buf, hex(buf, math.min(2 * n, 64))))
end)
