-- ramfree.lua: which 256-byte blocks of EWRAM 0x02030000-0x0203FFFF and IWRAM the game writes (free-RAM search for
-- the VWF scratch, bug B1). Logs "FREE <lo>-<hi> <bytes>" for every run of never-written blocks, every 600 frames
-- and at frame FRAMES-1 (pass --var FRAMES=N, the run length). Combine runs over several scenes: only blocks free in
-- all of them are candidates.
-- Writes before frame START (default 600: the boot clears all RAM) are ignored.
local hit = {}
local function mark(addr) if L.frame >= (START or 600) then hit[addr >> 8] = true end end
L.on_write(0x02030000, 0x0203FFFF, mark)
L.on_write(0x03000000, 0x03007FFF, mark)
local function report()
  for _, r in ipairs({ { 0x02030000, 0x02040000 }, { 0x03000000, 0x03008000 } }) do
    local lo = nil
    for b = r[1] >> 8, (r[2] >> 8) do
      local free = b < (r[2] >> 8) and not hit[b]
      if free and not lo then lo = b end
      if not free and lo then
        if (b - lo) >= 4 then L.log(string.format("FREE f%d %08X-%08X %d", L.frame, lo << 8, b << 8, (b - lo) << 8)) end
        lo = nil
      end
    end
  end
end
L.on_frame(function()
  if L.frame % 600 == 0 or L.frame == (FRAMES or 0) - 1 then report() end
end)
