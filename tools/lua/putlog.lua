-- putlog.lua: log every text_put call (0x0802E79C: r0 src, r1 x, r2 y, r3 cells, lr caller), blank fills (src 0)
-- included, for frames FROM..TO. Box-redraw debugging (which call wipes what, frame by frame).
-- Usage: emu.py ROM --out D ... --script tools/lua/putlog.lua --var FROM=2000 --var TO=2040
local function reg(s, n) return s["cpu.r" .. n] or s["cpu.r[" .. n .. "]"] or -1 end
L.on_exec(0x0802E79C, 0x0802E79C, function()
  if L.frame < (FROM or 0) or L.frame > (TO or 1e9) then return end
  local s = emu.getState()
  L.log(string.format("PUT f%d src=%08X x=%d y=%d n=%d lr=%08X", L.frame, reg(s, 0), reg(s, 1) & 0xFFFF,
    reg(s, 2) & 0xFFFF, reg(s, 3) & 0xFF, reg(s, 14)))
end)
