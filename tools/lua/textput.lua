-- textput.lua: log each distinct text_put call (0x0802E79C: r0 src, r1 x, r2 y, r3 cells, lr caller) so every
-- string gets the cell region its caller gives it (width gate, docs/re/text.md §Box widths).
-- Usage: emu.py ROM --out D ... --script tools/lua/textput.lua   (run on the ORIGINAL ROM: src = original offsets)
local function reg(s, n) return s["cpu.r" .. n] or s["cpu.r[" .. n .. "]"] or -1 end
local seen = {}
L.on_exec(0x0802E79C, 0x0802E79C, function()
  local s = emu.getState()
  local src, x, y, n, lr = reg(s, 0), reg(s, 1) & 0xFFFF, reg(s, 2) & 0xFFFF, reg(s, 3) & 0xFF, reg(s, 14)
  if src == 0 then return end
  local k = string.format("%08X %d %d %d %08X", src, x, y, n, lr)
  if seen[k] then return end
  seen[k] = true
  L.log("PUT " .. L.frame .. " src=" .. string.format("%08X", src) .. string.format(" x=%d y=%d n=%d lr=%08X", x, y, n, lr))
end)
