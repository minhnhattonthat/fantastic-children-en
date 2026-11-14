-- spprobe.lua: stack headroom at the line typer 0x0802E7F8 (VWF hook scratch sizing, bug B1).
-- Logs the lowest sp seen there every 300 frames, and how many bytes below that lowest sp are still zero in IWRAM
-- (a zero run under the deepest stack = never used, a rough bound on free stack).
local function reg(s, n) return s["cpu.r" .. n] or s["cpu.r[" .. n .. "]"] or -1 end
local minsp = 0x03008000
L.on_exec(0x0802E7F8, 0x0802E7F8, function()
  local sp = reg(emu.getState(), 13)
  if sp < minsp then minsp = sp end
end)
L.on_frame(function()
  if L.frame % 300 ~= 0 or minsp == 0x03008000 then return end
  local a = minsp - 4
  while a >= 0x03000000 and emu.read32(a, emu.memType.gbaMemory) == 0 do a = a - 4 end
  L.log(string.format("SP f%d min=%08X zero_below=%d lowest_nonzero=%08X", L.frame, minsp, minsp - 4 - a, a))
end)
