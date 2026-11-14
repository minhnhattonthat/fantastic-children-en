-- maprow.lua: log the BG0 tilemap shadow (0x0202D44C, 32 entries a row) for rows ROWS (default "3,5") on frames
-- FROM..TO, after the game's frame work: "MAP f<frame> y=<row> <entry hex>..." (cells 0-27). Box-redraw debugging.
-- Usage: emu.py ROM --out D ... --script tools/lua/maprow.lua --var FROM=2000 --var TO=2020 --var "ROWS='5'"
local SHADOW = 0x0202D44C
L.on_frame(function(n)
  if n < (FROM or 0) or n > (TO or 1e9) then return end
  for y in string.gmatch(ROWS or "3,5", "%d+") do
    local t = {}
    for x = 0, 27 do
      t[#t + 1] = string.format("%04X", emu.read16(SHADOW + (tonumber(y) * 32 + x) * 2, emu.memType.gbaMemory))
    end
    L.log(string.format("MAP f%d y=%s %s", n, y, table.concat(t, " ")))
  end
end)
