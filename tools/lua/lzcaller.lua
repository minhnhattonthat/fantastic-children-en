-- lzcaller.lua: who decompresses an LZ77 block. On the first read of ADDR (--var ADDR=0x0830E21C), logs r0-r3 and
-- every ROM-code-looking word on the SVC stack (0x03007F80-0x03007FFF, the BIOS SWI keeps the caller's lr there)
-- and on the user stack, so the call site and its pointer source can be found.
-- --var HI=0x... widens it to any read in ADDR..HI (first 3 logged).
local ADDR = ADDR or 0x0830E21C
local function reg(s, n) return s["cpu.r" .. n] or s["cpu.r[" .. n .. "]"] or -1 end
local seen = 0
L.on_read(ADDR, HI or ADDR, function(addr)
  if seen < 3 then L.log(string.format("ADDR %08X", addr)) end
  seen = seen + 1
  if seen > 3 then return end
  local s = emu.getState()
  L.log(string.format("READ f%d pc=%08X r0=%08X r1=%08X r2=%08X r3=%08X sp=%08X", L.frame, L.pc(), reg(s, 0),
    reg(s, 1), reg(s, 2), reg(s, 3), reg(s, 13)))
  local out = {}
  for a = 0x03007F80, 0x03007FFC, 4 do
    local v = emu.read32(a, emu.memType.gbaMemory)
    if v >= 0x08000000 and v < 0x08800000 then out[#out + 1] = string.format("%08X:%08X", a, v) end
  end
  local sp = reg(s, 13)
  for a = sp, sp + 0x80, 4 do
    local v = emu.read32(a, emu.memType.gbaMemory)
    if v >= 0x08000000 and v < 0x08800000 then out[#out + 1] = string.format("%08X:%08X", a, v) end
  end
  L.log("STACK " .. table.concat(out, " "))
end)
