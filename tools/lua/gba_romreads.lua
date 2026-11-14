-- gba_romreads.lua: per PC, the lowest/highest ROM address it reads and the read count, in a frame window.
-- --var FROM=N --var TO=M [--var LO=0x08000000 --var HI=0x09FFFFFF]. Logs at frame TO.
local FROM = FROM or 0
local TO = TO or 600
local LO = LO or 0x08000000
local HI = HI or 0x09FFFFFF
local stats = {}
local active = false
L.on_read(LO, HI, function(addr, value)
  if not active then return end
  local pc = L.pc()
  local s = stats[pc]
  if not s then
    stats[pc] = {lo = addr, hi = addr, n = 1, first = L.frame}
  else
    if addr < s.lo then s.lo = addr end
    if addr > s.hi then s.hi = addr end
    s.n = s.n + 1
  end
end)
L.on_frame(function(n)
  if n == FROM then active = true end
  if n == TO then
    active = false
    local keys = {}
    for pc in pairs(stats) do keys[#keys + 1] = pc end
    table.sort(keys)
    for _, pc in ipairs(keys) do
      local s = stats[pc]
      L.log(string.format("pc=%08X lo=%08X hi=%08X n=%d first=%d", pc, s.lo, s.hi, s.n, s.first))
    end
  end
end)
