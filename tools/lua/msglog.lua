-- msglog.lua: log every message lookup get_msg(id) at 0x08031020 with the caller (lr), for the warp tool's RE.
-- Usage: emu.py ROM --out D --route R --script tools/lua/msglog.lua [--var KEYS=1 to print the state keys once]
local keysDone = false
local function reg(s, n)
  return s["cpu.r" .. n] or s["cpu.r[" .. n .. "]"] or -1
end
L.on_exec(0x08031020, 0x08031020, function()
  local s = emu.getState()
  if KEYS and not keysDone then
    keysDone = true
    local ks = {}
    for k, _ in pairs(s) do if k:sub(1, 4) == "cpu." then ks[#ks + 1] = k end end
    table.sort(ks)
    L.log("KEYS " .. table.concat(ks, " "))
  end
  L.log(string.format("MSG %d id=%d lr=%08X", L.frame, reg(s, 0) & 0xFFFF, reg(s, 14)))
end)
-- the event-text command: r5 = event runner, [r5] = event record (u16 msg id at +0xC)
L.on_exec(0x0803913C, 0x0803913C, function()
  local s = emu.getState()
  L.log(string.format("EVT %d runner=%08X rec=%08X", L.frame, reg(s, 5), reg(s, 0)))
end)
