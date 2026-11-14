-- boxlog.lua: log each dialogue box open (0x0802F580, r0 = 0 top box with portrait, else bottom box) and the
-- message fetches after it (msglog-style MSG lines come from warp.lua), so messages can be sorted by box.
-- Used by the width lint's box map: WARP_PROBES=tools/lua/boxlog.lua python tools/debug/warp_all.py ...
local function reg(s, n) return s["cpu.r" .. n] or s["cpu.r[" .. n .. "]"] or -1 end
L.on_exec(0x0802F580, 0x0802F580, function()
  local s = emu.getState()
  L.log(string.format("BOX %d type=%d lr=%08X", L.frame, reg(s, 0) & 0xFF, reg(s, 14)))
end)
