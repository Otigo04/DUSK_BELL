DIR = "C:/Users/Otigo/AppData/Local/Temp/claude/F------GAMES-NIGHTWARD-Nightward-Assets--Project-Art-Characters/f812853e-d1a1-4638-94c2-23748d6b83e5/scratchpad/"
local OUT = "F:/!!!_GAMES/NIGHTWARD/Nightward/Assets/_Project/Art/Tiles/Tileset_Strasse_Schrott"
dofile(DIR .. "lib.lua")
newSheet(256, 512)
math.randomseed(11)
local function try(name)
  local ok, err = pcall(dofile, DIR .. name)
  if not ok then print(name .. " Fehler: " .. tostring(err)) end
end
try("part1.lua")
try("part2.lua")
try("part3.lua")
local bad = badPixels(sheet)
local lay = spr.layers[1]
lay.name = "Tiles"
local cel = lay:cel(1)
if cel then cel.image = sheet else spr:newCel(lay, 1, sheet, Point(0, 0)) end
spr:saveAs(OUT .. ".aseprite")
spr:saveCopyAs(OUT .. ".png")
print("Sheet fertig, ungueltige Pixel: " .. bad)
if io.open(DIR .. "anim.lua") then try("anim.lua") end
