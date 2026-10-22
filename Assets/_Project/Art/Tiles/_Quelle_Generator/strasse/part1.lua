-------------------------------------------------- Bodenschmutz
local function gum(n) for i = 1, n do local x, y = math.random(1, 29), math.random(1, 30); P(x, y, "c"); P(x + 1, y, "y") end end
local function butt(n) for i = 1, n do local x, y = math.random(2, 27), math.random(2, 29); P(x, y, "W"); P(x + 1, y, "W"); P(x + 2, y, "j") end end
local function leaf(n) for i = 1, n do local x, y = math.random(1, 29), math.random(1, 30); local c = ({"i", "j", "h", "k"})[math.random(1, 4)]; P(x, y, c); P(x + 1, y, c); if math.random() < 0.5 then P(x, y + 1, "h") end end end
local function asphalt(a, b, c3, dirty)
  R(0, 0, 32, 32, "t"); fleck(a or 10, "u"); fleck(b or 10, "a"); fleck(c3 or 3, "y")
  if dirty ~= false then
    for i = 1, math.random(1, 2) do blob(math.random(4, 27), math.random(4, 27), math.random(2, 4), math.random(1, 3), "a", 0.8) end
    if math.random() < 0.3 then butt(1) end
    if math.random() < 0.5 then gum(2) end
    if math.random() < 0.6 then leaf(3) end
  end
end

-------------------------------------------------- Zeile 0: Asphalt
begin(); asphalt(8, 9, 2); put(0, 0)
begin(); asphalt(16, 16, 5); grain(7, "a"); grain(4, "u"); put(1, 0)
begin(); asphalt(9, 9, 2)
do
  local pts = {{6,0},{7,3},{6,6},{9,9},{10,13},{13,16},{12,20},{16,23},{18,27},{17,31}}
  for i = 1, #pts - 1 do L(pts[i][1], pts[i][2], pts[i+1][1], pts[i+1][2], "p") end
  local br = {{10,13},{5,17},{3,20}}
  for i = 1, #br - 1 do L(br[i][1], br[i][2], br[i+1][1], br[i+1][2], "p") end
  for i = 1, #pts do P(pts[i][1] + 1, pts[i][2], "u") end
  P(4, 17, "u"); P(4, 19, "u")
end
put(2, 0)
begin(); asphalt(8, 4, 2)
R(5, 7, 22, 17, "p"); R(6, 8, 20, 15, "a")
for i = 1, 16 do P(math.random(7, 24), math.random(9, 21), "b") end
for i = 1, 6 do P(math.random(7, 24), math.random(9, 21), "p") end
L(6, 8, 25, 8, "b")
put(3, 0)
begin(); asphalt(10, 8, 2)
R(0, 12, 32, 2, "Y"); R(0, 17, 32, 2, "Y")
for i = 1, 9 do local rows = {12,13,17,18}; P(math.random(0,31), rows[math.random(1,4)], i % 2 == 0 and "t" or "u") end
put(4, 0)
begin(); asphalt(10, 8, 2)
R(4, 15, 24, 2, "W")
for i = 1, 8 do P(math.random(4,27), math.random(15,16), i % 2 == 0 and "t" or "y") end
put(5, 0)
begin(); asphalt(8, 6, 1)
R(2, 0, 10, 32, "W"); R(18, 0, 10, 32, "W")
for i = 1, 40 do
  local x = math.random(2, 27)
  if (x <= 11) or (x >= 18) then P(x, math.random(0, 31), i % 2 == 0 and "t" or "y") end
end
put(6, 0)
begin(); asphalt(8, 8, 2)
EL(16, 16, 13, 13, "o"); EL(16, 16, 12, 12, "a"); EL(16, 16, 9, 9, "p")
for y = -8, 8 do for x = -8, 8 do
  if x*x + y*y <= 64 and (x + y) % 4 == 0 then P(16 + x, 16 + y, "b") end
end end
P(24, 9, "c"); P(25, 10, "c"); P(26, 12, "c"); P(23, 8, "c"); P(26, 14, "c"); P(8, 22, "o")
R(10, 12, 2, 2, "i"); P(12, 13, "h"); R(21, 20, 2, 1, "h"); P(20, 19, "i"); P(14, 22, "h"); P(22, 13, "i")
put(7, 0)

-------------------------------------------------- Zeile 1: Pfuetze, Oel, Schlagloch, Bordstein, Gehweg, Gitter
begin(); asphalt(8, 8, 2)
EL(16, 17, 13, 7, "d"); EL(16, 17, 12, 6, "e"); EL(15, 16, 9, 3, "f")
R(20, 14, 3, 1, "m"); P(18, 16, "m"); L(8, 20, 12, 20, "f"); P(24, 19, "f")
P(10, 16, "i"); P(11, 16, "j"); P(12, 17, "h"); R(19, 19, 3, 1, "W"); P(22, 19, "Z"); P(14, 19, "k")
put(0, 1)
begin(); asphalt(8, 8, 2)
EL(15, 16, 11, 7, "p"); EL(17, 17, 8, 5, "a")
P(12, 13, "C"); P(13, 13, "c"); P(18, 18, "B"); P(19, 18, "c"); P(21, 15, "c"); P(15, 20, "B")
put(1, 1)
begin(); asphalt(8, 8, 2)
EL(16, 17, 11, 7, "a")
for i = 0, 15 do
  local ang = i / 16 * math.pi * 2
  P(math.floor(16 + math.cos(ang) * 12 + 0.5), math.floor(17 + math.sin(ang) * 8 + 0.5), i % 2 == 0 and "u" or "y")
end
EL(16, 17, 10, 6, "p"); EL(15, 20, 6, 2, "e"); P(13, 19, "f"); P(14, 19, "f"); P(19, 21, "m")
put(2, 1)

function sidewalk(ymax)
  R(0, 0, 32, ymax + 1, "u")
  for y = 0, ymax do
    if y == 6 or y == 22 then for x = 0, 31 do P(x, y, "t") end
    elseif y >= 7 and y <= 21 then P(15, y, "t")
    else P(0, y, "t") end
  end
  for _, y in ipairs({0, 7, 23}) do
    if y <= ymax then for x = 1, 31 do if x ~= 15 then P(x, y, "y") end end end
  end
  for i = 1, 14 do
    local y = math.random(0, ymax)
    if y ~= 6 and y ~= 22 then P(math.random(1, 31), y, i % 2 == 0 and "y" or "c") end
  end
  blob(math.random(4, 26), math.random(2, math.max(ymax - 2, 3)), math.random(2, 4), math.random(1, 2), "t", 0.8)
  blob(math.random(4, 26), math.random(2, math.max(ymax - 2, 3)), math.random(1, 3), 1, "c", 0.8)
  if math.random() < 0.7 then gum(2) end
end
begin(); R(0, 0, 32, 32, "t"); sidewalk(12)
R(0, 13, 32, 1, "y"); R(0, 14, 32, 3, "u"); R(0, 17, 32, 2, "c"); R(0, 19, 32, 1, "o"); R(0, 20, 32, 2, "p"); R(0, 22, 32, 1, "a")
for y = 14, 18 do P(15, y, "t") end
for i = 1, 6 do local x = math.random(0, 31); for k = 0, math.random(2, 4) do P(x, 14 + k, "a") end end
for x = 0, 31 do
  if math.random() < 0.35 then P(x, 23, "g") end
  if math.random() < 0.2 then P(x, 24, "h") end
  if math.random() < 0.12 then P(x, 22, "g") end
end
for i = 1, 4 do local x = math.random(0, 30); P(x, 18, "n"); P(x + 1, 18, "q"); P(x, 17, "n") end
for i = 1, 8 do P(math.random(0, 31), math.random(23, 31), i % 2 == 0 and "u" or "a") end
curbH = img
put(3, 1)
begin()
for y = 0, 31 do for x = 0, 31 do img:drawPixel(y, x, curbH:getPixel(x, y)) end end
put(4, 1)
begin(); sidewalk(31); put(5, 1)
begin(); sidewalk(31)
do
  local pts = {{4,0},{6,4},{5,8},{9,12},{11,16},{10,20},{14,24},{15,28},{14,31}}
  for i = 1, #pts - 1 do L(pts[i][1], pts[i][2], pts[i+1][1], pts[i+1][2], "p") end
  P(10, 12, "q"); P(11, 11, "r"); P(12, 11, "s"); P(10, 16, "q"); P(10, 15, "r"); P(14, 24, "n"); P(15, 23, "q"); P(15, 22, "r")
  P(5, 8, "q"); P(4, 7, "r")
end
put(6, 1)
begin(); asphalt(8, 8, 2)
RB(4, 8, 24, 16, "u"); R(6, 10, 20, 12, "p")
for x = 7, 23, 4 do R(x, 10, 2, 12, "u") end
R(4, 8, 24, 1, "y"); P(7, 11, "y"); P(15, 11, "y")
P(9, 16, "i"); P(10, 16, "j"); P(10, 17, "h"); P(18, 14, "W"); P(18, 15, "y"); P(21, 19, "j"); R(5, 9, 2, 1, "i"); P(12, 20, "h")
put(7, 1)

-------------------------------------------------- Zeile 2: Autos, Reifen, Einkaufswagen
GRIME = { soot = 0.14, mud = 4, streaks = 4, rust = 3, specks = 0.04 }
local GCAR = { soot = 0.16, mud = 5, streaks = 5, rust = 4, specks = 0.05 }
function wheel(cx, cy)
  EB(cx, cy, 5, 5, "p"); EL(cx, cy, 2, 2, "u"); P(cx, cy - 1, "y"); P(cx - 4, cy - 3, "b"); P(cx + 3, cy - 3, "b")
end
function carA(wheels, c1, c2, c3)
  EL(32, 30, 29, 1, "p")
  TB(4, 12, 20, 43, 13, 51, c1)
  TF(6, 11, 21, 42, 15, 49, "e")
  L(25, 6, 20, 11, "f"); L(28, 6, 23, 11, "f"); L(39, 6, 44, 11, "f")
  R(31, 6, 2, 6, c1); R(21, 4, 22, 1, c2)
  RB(3, 13, 58, 10, c1); R(4, 14, 56, 1, c2); R(4, 22, 56, 1, c3)
  R(30, 15, 1, 7, c3); R(47, 15, 1, 7, c3); R(27, 16, 3, 1, "y"); R(44, 16, 3, 1, "y")
  RB(1, 19, 4, 3, "u"); R(1, 19, 4, 1, "y"); RB(59, 19, 4, 3, "u"); R(59, 19, 4, 1, "y")
  R(60, 15, 2, 2, "Y"); P(61, 15, "W"); R(2, 15, 2, 2, "Q")
  R(5, 15, 2, 2, "y"); P(5, 15, "W")
  RB(43, 10, 3, 2, "u"); P(43, 10, "y")
  L(35, 15, 40, 18, "u"); L(36, 15, 38, 16, "y"); L(11, 19, 15, 20, "u")
  P(23, 8, "Q"); P(24, 8, "Q"); P(22, 9, "W")
  if wheels then
    for _, cx in ipairs({ 14, 49 }) do
      for y = 17, 22 do for x = cx - 7, cx + 7 do
        if ((x - cx) ^ 2) / 49 + ((y - 24) ^ 2) / 36 <= 1 then P(x, y, "p") end
      end end
    end
    wheel(14, 24); wheel(49, 24)
  end
end
begin(64, 32)
carA(true, "R", "Q", "a")
R(8, 16, 3, 2, "i"); R(9, 17, 2, 1, "h"); R(36, 19, 4, 2, "i"); R(51, 15, 3, 2, "h"); P(52, 17, "i"); R(22, 20, 2, 1, "h")
R(24, 13, 1, 1, "i")
put(0, 2, nil, GCAR)

begin(64, 32)
EL(32, 30, 29, 1, "p")
TB(10, 22, 44, 51, 44, 60, "B")
TF(12, 18, 46, 50, 46, 57, "e"); L(48, 12, 46, 18, "f")
RB(3, 5, 42, 17, "B"); R(4, 5, 40, 1, "C"); R(4, 21, 40, 1, "d")
R(4, 11, 40, 2, "k"); R(4, 11, 40, 1, "j")
L(24, 7, 26, 9, "Q"); L(26, 9, 28, 7, "Q"); L(28, 7, 30, 9, "Q"); L(30, 9, 33, 6, "Q"); L(23, 10, 34, 10, "Q"); P(35, 8, "C"); P(36, 7, "C"); P(35, 9, "C")
R(8, 15, 7, 2, "W"); R(17, 15, 5, 2, "W"); R(24, 15, 9, 2, "W"); R(35, 15, 6, 2, "Q")
P(30, 8, "d"); P(31, 8, "d"); P(31, 9, "d"); P(12, 8, "f")
R(58, 20, 5, 3, "u"); R(58, 20, 5, 1, "y"); R(60, 16, 2, 2, "Y"); P(61, 16, "W"); R(2, 16, 2, 3, "Q")
L(8, 4, 8, 2, "u"); R(7, 1, 3, 1, "y")
wheel(14, 24); wheel(52, 24)
put(2, 2, nil, GCAR)

-- Wrack auf Backsteinen, vorne aufgebockt
begin(64, 32); OY = 2
carA(false, "b", "c", "a")
R(24, 8, 8, 1, "o"); L(25, 7, 29, 11, "W"); L(36, 8, 41, 10, "W")
R(6, 16, 5, 2, "i"); R(8, 17, 3, 1, "h"); R(38, 18, 4, 2, "i"); R(52, 16, 3, 2, "h")
OY = 0
put(4, 2, shearY(-0.06, 0), GCAR)
begin(64, 32)
for _, bx in ipairs({ 9, 46 }) do
  local top = 25 - math.floor((bx + 5) * 0.06 + 0.5) + 2
  R(bx - 1, top - 1, 13, 32 - top, "o")
  R(bx, top, 11, 30 - top, "R")
  for y = top, 29 do
    if (y - top) % 3 == 2 then R(bx, y, 11, 1, "a") end
    P(bx + (math.floor((y - top) / 3) % 2 == 0 and 5 or 2), y, "a")
  end
  R(bx, top, 11, 1, "Q"); P(bx + 2, top + 1, "Q")
end
-- Backsteine ohne Mehrfach-Outline: nur Kontur ergaenzen
put(4, 2)

begin()
function tire(cx, cy)
  EL(cx, cy + 3, 11, 4, "o"); EL(cx, cy, 11, 4, "o"); R(cx - 11, cy, 23, 4, "o")
  EL(cx, cy + 3, 10, 3, "p"); R(cx - 10, cy, 21, 4, "p"); EL(cx, cy, 10, 3, "a")
  EL(cx, cy, 5, 1, "o")
  L(cx - 7, cy - 2, cx - 3, cy - 3, "b"); L(cx + 3, cy - 3, cx + 7, cy - 2, "b")
end
tire(16, 22); tire(14, 15); tire(17, 8)
put(6, 2)

begin()
EL(16, 29, 12, 1, "p")
SP(TS(8, 18, 4, 27, 8, 24), "t")
for y = 9, 17 do for x = 6, 27 do if (x + y) % 3 == 0 then P(x, y, "y") end end end
for x = 8, 24, 4 do L(x, 9, x, 18, "u") end
L(4, 8, 2, 4, "u"); L(2, 4, 6, 4, "u")
L(9, 19, 10, 25, "u"); L(23, 19, 22, 25, "u")
EB(10, 26, 2, 2, "p"); EB(22, 26, 2, 2, "p"); P(10, 26, "y"); P(22, 26, "y")
put(7, 2, shearY(0.05, 16))

-------------------------------------------------- Zeilen 3-4: hohe Objekte (32x64)
function pane(px, py, st)
  if st == "lit" then
    R(px, py, 4, 9, "Y"); P(px, py, "W"); R(px + 3, py + 1, 1, 8, "Z"); R(px, py + 8, 3, 1, "Z")
    if math.random() < 0.6 then P(px + math.random(0, 3), py + math.random(3, 6), "Z") end
    if math.random() < 0.35 then P(px + math.random(0, 2), py + math.random(1, 3), "k") end
  elseif st == "dark" then
    R(px, py, 4, 9, "d"); P(px, py, "f"); P(px + 1, py + 1, "f")
  elseif st == "crack" then
    R(px, py, 4, 9, "e"); L(px, py, px + 3, py + 8, "W"); L(px + 3, py + 1, px + 1, py + 4, "f")
  else
    R(px, py, 4, 9, "p"); P(px, py, "X"); P(px + 3, py, "X"); P(px, py + 8, "X"); P(px + 1, py + 7, "X"); P(px + 3, py + 8, "X")
  end
end
function booth(states)
  EL(16, 61, 13, 2, "p")
  RB(4, 60, 24, 2, "u"); R(4, 60, 24, 1, "y")
  RB(9, 2, 14, 3, "R"); R(10, 2, 12, 1, "Q")
  RB(5, 5, 22, 7, "R"); R(6, 5, 20, 1, "Q")
  R(8, 6, 16, 5, "X")
  for _, p in ipairs({{10,7},{11,7},{12,7},{11,8},{11,9},{14,7},{15,7},{16,7},{14,8},{15,8},{14,9},{15,9},{16,9},{18,7},{18,8},{18,9},{19,9},{20,9}}) do P(p[1], p[2], "p") end
  RB(6, 12, 20, 48, "R"); R(6, 13, 1, 46, "a"); R(25, 13, 1, 46, "Q")
  for k = 0, 3 do for m = 0, 2 do pane(8 + m * 6, 14 + k * 10, states[k + 1][m + 1]) end end
  R(15, 28, 2, 4, "p"); P(14, 28, "p"); P(17, 29, "p")
  R(6, 53, 20, 1, "a"); R(6, 58, 20, 1, "a"); R(24, 36, 1, 5, "y")
  L(10, 56, 14, 56, "Q"); R(9, 54, 3, 3, "W"); P(10, 55, "Q"); R(17, 55, 4, 2, "C"); P(18, 55, "W")
end
local lit = {{"lit","lit","lit"},{"lit","lit","lit"},{"lit","lit","lit"},{"lit","lit","lit"}}
begin(32, 64); booth(lit); put(0, 3)
local brk = {{"lit","crack","lit"},{"gone","lit","crack"},{"dark","lit","gone"},{"crack","lit","lit"}}
begin(32, 64); OX = -3; booth(brk); OX = 0; put(1, 3, shearX(0.13, 62))

-- Telefonmast mit Kabeln, Vogel, Anschlusskasten
begin(32, 64)
EL(16, 61, 8, 2, "p")
RB(14, 12, 4, 50, "i"); R(14, 12, 1, 50, "h"); R(17, 12, 1, 50, "j")
RB(3, 12, 26, 3, "i"); R(3, 12, 26, 1, "j"); RB(7, 22, 18, 3, "i"); R(7, 22, 18, 1, "j")
for _, x in ipairs({6, 11, 20, 25}) do R(x, 9, 2, 3, "y"); P(x, 9, "W"); R(x, 11, 2, 1, "u") end
for _, x in ipairs({9, 22}) do R(x, 19, 2, 3, "y"); R(x, 21, 2, 1, "u") end
L(6, 9, 0, 14, "p"); L(11, 9, 0, 17, "p"); L(20, 9, 31, 17, "p"); L(25, 9, 31, 14, "p")
L(9, 19, 0, 22, "p"); L(22, 19, 31, 22, "p")
RB(10, 32, 7, 10, "t"); R(10, 32, 7, 1, "y"); R(13, 33, 1, 8, "u"); P(15, 37, "Y")
L(13, 42, 12, 47, "p"); L(12, 47, 14, 52, "p")
RB(19, 28, 5, 11, "u"); R(19, 28, 5, 1, "y"); R(19, 33, 5, 1, "t"); R(23, 29, 1, 9, "y")
for _, y in ipairs({44, 48, 52}) do P(13, y, "u"); P(18, y, "u") end
A(13, 6, {"...pp.", "p.pppZ", ".pppp.", "..pp.."}); P(15, 10, "p"); P(17, 10, "p"); P(17, 6, "W")
put(2, 3, shearX(0.05, 62))

-- Laterne, schief
begin(32, 64)
EL(16, 61, 10, 2, "p")
RB(11, 55, 10, 6, "t"); R(12, 55, 8, 1, "y")
RB(14, 8, 4, 48, "u"); R(14, 8, 1, 48, "t"); R(17, 8, 1, 48, "y")
RB(16, 6, 12, 3, "u"); R(16, 6, 12, 1, "y")
RB(21, 9, 10, 4, "t"); R(21, 9, 10, 1, "u")
R(22, 13, 8, 2, "Y"); R(24, 13, 4, 1, "W")
put(3, 3, shearX(-0.1, 62))

-- Ampel
begin(32, 64)
EL(16, 61, 8, 2, "p")
RB(14, 24, 4, 36, "u"); R(14, 24, 1, 36, "t"); R(17, 24, 1, 36, "y")
RB(9, 2, 14, 26, "a"); R(9, 2, 1, 26, "p"); R(22, 3, 1, 24, "b")
RB(18, 36, 4, 6, "t"); P(20, 38, "Y")
for i, cy in ipairs({7, 14, 21}) do
  EB(16, cy, 3, 3, (i == 1) and "R" or (i == 2) and "Y" or "n")
  R(12, cy - 5, 9, 1, "o")
end
P(15, 13, "W"); P(16, 13, "W"); P(15, 6, "Q"); P(16, 20, "q")
put(4, 3, shearX(0.06, 62))

-- Schildermast, verdreht
begin(32, 64)
EL(16, 61, 7, 2, "p")
RB(15, 4, 2, 57, "u"); R(15, 4, 1, 57, "t"); R(16, 4, 1, 57, "y")
EB(16, 12, 7, 7, "B"); EL(16, 12, 6, 6, "W"); EL(16, 12, 5, 5, "B")
R(15, 9, 2, 7, "W"); P(14, 10, "W"); P(17, 10, "W"); P(13, 11, "W"); P(18, 11, "W")
SP({{24,13,18},{25,11,20},{26,10,21},{27,10,21},{28,10,21},{29,10,21},{30,10,21},{31,10,21},{32,10,21},{33,10,21},{34,11,20},{35,13,18}}, "R")
R(12, 28, 8, 1, "W"); R(12, 30, 8, 1, "W"); R(12, 32, 8, 1, "W")
stamp(24, 14, function()
  RB(2, 2, 19, 8, "e"); R(3, 3, 17, 1, "f"); R(5, 5, 12, 1, "W"); R(5, 7, 8, 1, "W")
end, shearY(0.22, 12), 4, 42)
P(14, 41, "y"); P(16, 41, "y")
put(5, 3, shearX(0.07, 62))

-- Getraenkeautomat
begin(32, 64)
EL(16, 61, 13, 2, "p")
RB(6, 5, 20, 54, "B"); R(7, 5, 18, 1, "C"); R(6, 6, 1, 52, "d"); R(25, 6, 1, 52, "C")
R(8, 7, 16, 6, "Y"); R(10, 9, 3, 2, "p"); R(14, 9, 5, 2, "p"); R(20, 9, 2, 2, "p"); R(8, 7, 16, 1, "W")
R(8, 15, 12, 26, "Y")
do
  local cc = {"Q", "C", "s", "Z", "W"}
  for _, y in ipairs({19, 25, 31, 37}) do
    for i = 0, 4 do R(9 + i * 2, y - 4, 2, 4, cc[(i + y) % 5 + 1]) end
    R(8, y, 12, 1, "p")
  end
end
RB(8, 15, 12, 26, "Y"); R(8, 15, 12, 26, "Y")
do
  local cc = {"Q", "C", "s", "Z", "W"}
  for _, y in ipairs({19, 25, 31, 37}) do
    for i = 0, 4 do R(9 + i * 2, y - 4, 2, 4, cc[(i + y) % 5 + 1]) end
    R(8, y, 12, 1, "p")
  end
end
R(8, 15, 1, 26, "Z")
R(21, 16, 3, 2, "Z"); R(21, 20, 3, 2, "Z"); R(21, 26, 3, 1, "p")
for y = 29, 35, 3 do for x = 21, 23, 2 do P(x, y, "u") end end
RB(10, 46, 12, 8, "p"); R(11, 47, 10, 1, "u")
R(6, 57, 20, 2, "d"); P(9, 43, "d"); P(10, 44, "d"); TR(21, 38, 3, 3, 0.3, "W")
put(6, 3)

-- Litfasssaeule mit zerrissenen Plakaten
begin(32, 64)
EL(16, 61, 13, 2, "p")
RB(7, 14, 18, 46, "k")
R(8, 16, 16, 8, "Q"); R(8, 26, 16, 10, "e"); R(8, 38, 16, 8, "Y"); R(8, 48, 16, 10, "B")
R(10, 18, 8, 2, "W"); R(10, 21, 5, 1, "W"); R(10, 29, 9, 1, "f"); R(10, 32, 6, 3, "m")
R(10, 40, 12, 2, "Z"); R(12, 50, 8, 4, "C")
for _, p in ipairs({{8,24},{9,25},{12,25},{20,25},{22,24},{23,36},{16,37},{9,36},{18,46},{23,47},{10,47}}) do P(p[1], p[2], "k") end
R(8, 14, 1, 46, "a"); R(24, 15, 1, 44, "W")
EB(16, 12, 11, 3, "u"); EL(16, 11, 8, 2, "y")
RB(6, 58, 20, 3, "t"); R(6, 58, 20, 1, "u")
put(7, 3)

-------------------------------------------------- Zeile 5: kleine Props
local cone = {
 "......oooo......",
 ".....oZZZFo.....",
 ".....oZZZFo.....",
 "....oZZZZFFo....",
 "....oWWWWXXo....",
 "...oWWWWWXXXo...",
 "...oZZZZZFFFo...",
 "..oZZZZZZFFFFo..",
 "..oZZZZZZFFFFo..",
 ".oWWWWWWWXXXXXo.",
 ".oWWWWWWWXXXXXo.",
 ".oZZZZZZZZFFFFFo",
 "oooooooooooooooo",
 "oaccccccccaaaaao",
 "oaaaaaaaaaaaaaao",
 "oooooooooooooooo" }
begin(); EL(16, 29, 10, 1, "p"); A(8, 14, cone, true); put(0, 5)
begin(); A(8, 14, cone, true)
put(1, 5, function(x, y) return 31 - y, x + 6 end)
begin(); R(3, 30, 17, 1, "p"); put(1, 5)

local hydrant = {
 "......oooo......",
 ".....oRRQQo.....",
 "....oRRRQQQo....",
 "....oRRRRQQo....",
 "...oooooooooo...",
 "..oyyyyyyyyyyo..",
 "...oooooooooo...",
 "...oRRRRRRQQo...",
 "ooooRRRRRRQQoooo",
 "oyyoRRRRRRQQoyyo",
 "oyyoRRRRRRQQoyyo",
 "ooooRRRRRRQQoooo",
 "...oRRRRRRQQo...",
 "...oRRRRRRQQo...",
 "..ooooooooooo...",
 ".oRRRRRRRRQQQQo.",
 ".oooooooooooooo." }
begin(); EL(16, 29, 10, 1, "p"); A(8, 13, hydrant); put(2, 5)

local function bin()
  R(8, 9, 5, 3, "B"); P(9, 8, "C"); P(11, 8, "W")
  TB(14, 28, 8, 25, 9, 23, "u")
  for _, x in ipairs({12, 16, 20}) do R(x, 15, 1, 12, "t") end
  L(24, 15, 23, 27, "y"); R(9, 28, 15, 1, "t")
  TR(7, 12, 20, 3, -0.2, "y")
end
begin(); EL(16, 30, 11, 1, "p"); bin(); R(21, 7, 3, 2, "X"); put(3, 5)
begin(); bin(); put(4, 5, function(x, y) return 31 - y, x + 2 end)
begin()
R(22, 22, 3, 5, "y"); R(22, 22, 3, 1, "W")
RB(26, 26, 4, 3, "B"); P(27, 26, "C")
R(23, 28, 5, 1, "X"); P(24, 29, "X"); P(25, 29, "X")
EL(21, 18, 2, 6, "p"); R(21, 12, 1, 12, "p"); P(22, 13, "y"); P(22, 23, "y")
R(27, 22, 2, 2, "Q"); R(21, 29, 2, 1, "s")
EL(16, 30, 12, 1, "p")
put(4, 5)

begin()
L(14, 8, 10, 2, "u"); L(18, 8, 22, 3, "u"); P(10, 2, "y"); P(22, 3, "y")
RB(6, 9, 20, 15, "i"); R(7, 9, 18, 1, "j")
RB(8, 11, 12, 11, "e")
for i = 1, 26 do local ch = {"f", "m", "d", "e", "f"}; P(math.random(8, 19), math.random(11, 21), ch[math.random(1, 5)]) end
P(9, 12, "m"); P(10, 12, "f"); P(9, 13, "f")
P(22, 13, "Y"); P(22, 17, "y"); L(21, 19, 23, 19, "h"); L(21, 21, 23, 21, "h")
put(5, 5, shearY(-0.1, 6))
begin()
RB(4, 24, 24, 6, "j"); R(4, 24, 24, 1, "k"); L(5, 25, 27, 29, "i"); L(27, 25, 5, 29, "i")
EL(16, 31, 12, 1, "p")
put(5, 5)

begin()
EL(16, 29, 10, 1, "p")
RB(8, 10, 16, 19, "u"); R(8, 10, 16, 1, "y"); R(16, 11, 1, 17, "t"); R(8, 11, 1, 17, "t"); R(23, 11, 1, 17, "y")
RB(10, 13, 5, 7, "W"); R(11, 15, 3, 1, "p"); P(11, 16, "p"); P(13, 16, "p"); P(11, 17, "p"); P(13, 17, "p")
R(18, 14, 4, 1, "t"); R(18, 16, 4, 1, "t"); R(18, 18, 4, 1, "t"); R(18, 22, 4, 1, "b")
L(16, 10, 16, 5, "p"); L(16, 5, 20, 3, "p")
L(23, 15, 27, 16, "p"); L(27, 16, 25, 19, "p"); L(25, 19, 28, 21, "p")
RB(26, 22, 3, 5, "p"); P(27, 22, "b")
put(6, 5)

begin()
EL(16, 29, 14, 1, "p")
TB(15, 25, 3, 28, 6, 25, "X"); R(5, 16, 3, 9, "u"); R(4, 15, 2, 1, "u")
RB(7, 26, 3, 3, "j"); RB(22, 26, 3, 3, "j")
EB(16, 14, 13, 3, "W"); EL(16, 14, 11, 2, "f"); R(10, 14, 4, 1, "m"); P(20, 13, "m")
R(14, 9, 4, 3, "Y"); P(17, 9, "Z"); P(18, 10, "Z"); P(14, 10, "W")
RB(27, 6, 2, 8, "y"); L(26, 5, 30, 5, "u")
put(7, 5, shearY(0.06, 16))

-------------------------------------------------- Zeilen 6-7: schraeger Mix
-- Sofa mit gebrochenem Bein
begin()
EL(16, 29, 14, 1, "p")
RB(5, 8, 22, 10, "R"); R(6, 8, 20, 1, "Q"); P(10, 12, "a"); P(16, 12, "a"); P(22, 12, "a"); P(13, 14, "a"); P(19, 14, "a")
RB(7, 17, 18, 7, "Q"); R(15, 17, 1, 7, "R"); R(7, 23, 18, 1, "R")
RB(2, 12, 5, 13, "R"); R(3, 12, 3, 1, "Q"); RB(25, 12, 5, 13, "R"); R(26, 12, 3, 1, "Q")
RB(4, 25, 2, 3, "i")
P(19, 19, "W"); P(20, 18, "W"); P(21, 19, "W"); P(20, 20, "Y")
put(0, 6, function(x, y) return x, y + math.floor((x - 16) * 0.12 + 0.5) + 2 end)

-- alter Kuehlschrank, Tuer einen Spalt offen
begin()
EL(16, 29, 10, 1, "p")
RB(8, 3, 16, 26, "y"); R(8, 3, 3, 26, "u"); R(23, 3, 1, 26, "W"); R(9, 3, 14, 1, "W")
R(8, 12, 16, 1, "t"); R(21, 6, 1, 4, "t"); R(21, 14, 1, 8, "t")
R(9, 16, 3, 2, "i"); R(10, 17, 2, 2, "h"); R(14, 24, 4, 2, "h"); P(18, 7, "Q"); R(12, 5, 4, 2, "Y"); P(13, 5, "W")
R(22, 13, 2, 15, "p"); R(23, 14, 1, 13, "Y")
R(9, 28, 3, 1, "t"); R(20, 28, 3, 1, "t")
put(1, 6, shearX(0.06, 29))

-- Briefkasten
begin()
EL(16, 29, 9, 1, "p")
RB(14, 20, 4, 9, "t"); R(14, 20, 1, 9, "u")
RB(8, 5, 16, 15, "Y"); R(9, 5, 14, 1, "W"); R(8, 7, 3, 12, "Z"); R(23, 6, 1, 13, "W")
R(11, 9, 10, 1, "p"); RB(11, 14, 10, 4, "Z"); R(12, 15, 8, 1, "Y")
P(20, 7, "p"); R(14, 11, 4, 2, "B"); P(15, 11, "C")
put(2, 6, shearX(0.08, 29))

-- Parkuhr
begin()
EL(16, 29, 8, 1, "p")
RB(15, 12, 3, 17, "u"); R(15, 12, 1, 17, "t"); R(17, 12, 1, 17, "y")
RB(11, 3, 11, 10, "y"); R(11, 3, 11, 1, "W"); R(11, 4, 2, 9, "u")
R(14, 5, 6, 4, "e"); P(14, 5, "f"); R(14, 10, 6, 1, "R"); R(16, 11, 2, 1, "p")
RB(13, 28, 7, 2, "t")
put(3, 6, shearX(-0.1, 29))

-- offener Gully mit Dampf
begin()
EL(15, 25, 11, 5, "o"); EL(15, 25, 10, 4, "u"); EL(15, 25, 9, 3, "p"); EL(15, 26, 6, 1, "a")
EB(26, 18, 4, 6, "u"); EL(26, 18, 2, 4, "y"); R(26, 15, 1, 6, "t"); L(24, 18, 28, 18, "t")
for _, p in ipairs({{14,21},{15,20},{15,19},{16,18},{17,17},{16,16},{15,15},{15,14},{16,13},{17,12},{16,11},{14,10},{15,9},{18,8},{17,7},{20,6},{19,5}}) do P(p[1], p[2], "m") end
for _, p in ipairs({{13,19},{18,14},{14,13},{17,10},{19,9},{16,6},{15,12}}) do P(p[1], p[2], "y") end
put(4, 6)

-- Fahrrad
begin()
local function ring(cx, cy, r, c)
  for a = 0, 63 do local an = a / 64 * math.pi * 2; P(math.floor(cx + math.cos(an) * r + 0.5), math.floor(cy + math.sin(an) * r + 0.5), c) end
end
EL(16, 29, 14, 1, "p")
ring(8, 22, 6, "p"); ring(8, 22, 5, "u"); ring(24, 22, 6, "p"); ring(24, 22, 5, "u")
for _, cx in ipairs({8, 24}) do L(cx - 4, 22, cx + 4, 22, "t"); L(cx, 18, cx, 26, "t"); P(cx, 22, "y") end
L(8, 22, 13, 13, "Q"); L(13, 13, 22, 13, "Q"); L(13, 13, 15, 22, "Q"); L(15, 22, 22, 13, "Q"); L(8, 22, 15, 22, "Q"); L(22, 13, 24, 22, "u")
R(11, 12, 5, 1, "p"); P(10, 12, "p"); L(21, 11, 25, 11, "p"); P(22, 12, "p"); P(15, 23, "y"); P(15, 24, "y")
put(5, 6)

-- Sperrmuell
begin()
EL(16, 29, 14, 1, "p")
RB(18, 9, 11, 9, "j"); R(19, 9, 9, 1, "k"); R(22, 9, 2, 9, "k"); R(19, 13, 9, 1, "j"); P(26, 11, "i"); P(27, 15, "i")
RB(3, 21, 12, 7, "k"); R(4, 21, 10, 1, "W"); R(4, 25, 10, 1, "j"); R(8, 22, 1, 5, "i")
EB(11, 17, 5, 5, "b"); R(8, 14, 3, 2, "c"); P(8, 16, "c"); R(13, 19, 2, 2, "a"); P(11, 11, "Y"); P(12, 12, "Y")
EB(23, 24, 6, 4, "b"); R(20, 22, 4, 1, "c"); P(20, 23, "c"); R(26, 26, 3, 1, "a"); P(23, 19, "Y")
L(4, 28, 8, 15, "i"); L(5, 28, 9, 15, "h")
R(14, 26, 4, 2, "g"); R(15, 25, 2, 1, "g"); R(16, 27, 3, 1, "Q")
put(6, 6)

-- Koffer und Regenschirm
begin()
EL(16, 29, 14, 1, "p")
RB(6, 16, 18, 12, "i"); R(6, 16, 18, 1, "j"); R(6, 20, 18, 1, "h"); R(6, 25, 18, 1, "h")
RB(12, 13, 6, 3, "u"); R(13, 14, 4, 1, "y")
R(7, 17, 2, 3, "j"); R(21, 17, 2, 3, "j"); R(7, 25, 2, 3, "j"); R(21, 25, 2, 3, "j")
R(9, 22, 2, 2, "Y"); R(19, 22, 2, 2, "Y"); R(13, 22, 4, 3, "C"); R(14, 23, 2, 1, "W"); P(21, 18, "Q")
L(28, 9, 26, 21, "B"); L(29, 9, 27, 21, "B"); L(27, 10, 25, 21, "B"); L(28, 10, 26, 22, "b")
L(25, 22, 24, 28, "u"); P(23, 28, "u"); P(24, 29, "u")
put(7, 6)

-- Muenztelefon mit haengendem Hoerer
begin()
EL(16, 29, 10, 1, "p")
RB(14, 23, 4, 6, "u"); R(14, 23, 1, 6, "t")
RB(9, 4, 14, 19, "B"); R(9, 4, 14, 1, "C"); R(22, 5, 1, 17, "C"); R(9, 5, 2, 17, "d")
R(12, 7, 8, 3, "Y"); R(12, 7, 8, 1, "W"); P(14, 8, "p"); P(16, 8, "p"); P(18, 8, "p")
for _, y in ipairs({13, 16, 19}) do for _, x in ipairs({13, 16, 19}) do P(x, y, "W") end end
L(10, 18, 7, 20, "p"); L(7, 20, 6, 24, "p")
RB(3, 24, 5, 4, "p"); P(4, 24, "b"); P(6, 24, "b")
put(0, 7, shearX(-0.04, 29))

-- wackeliger Plastikstuhl
begin()
EL(16, 29, 10, 1, "p")
RB(13, 17, 2, 9, "t"); RB(17, 17, 2, 9, "t")
RB(9, 17, 2, 11, "u"); RB(21, 17, 2, 11, "u")
RB(8, 13, 16, 4, "C"); R(8, 13, 16, 1, "W"); R(8, 16, 16, 1, "B")
RB(9, 3, 14, 9, "C"); R(9, 3, 14, 1, "W"); R(11, 6, 10, 1, "B"); R(11, 9, 10, 1, "B"); R(22, 4, 1, 7, "B")
put(1, 7, shearX(0.12, 29))

-- Verkehrsspiegel
begin()
EL(16, 29, 8, 1, "p")
RB(15, 14, 3, 15, "u"); R(15, 14, 1, 15, "t"); R(17, 14, 1, 15, "y")
EB(16, 8, 8, 8, "Z"); EL(16, 8, 6, 6, "f"); EL(16, 8, 5, 5, "e")
L(12, 5, 14, 3, "m"); P(11, 7, "f"); P(19, 11, "f"); L(13, 11, 19, 11, "d"); P(16, 6, "Y"); P(17, 7, "Z")
R(14, 27, 5, 2, "t")
put(2, 7, shearX(0.08, 29))

-- Feuertonne (Lichtquelle)
begin()
EL(16, 29, 10, 1, "p")
RB(9, 15, 14, 14, "u"); R(9, 15, 3, 14, "t"); R(22, 15, 1, 14, "y"); R(9, 20, 14, 1, "t"); R(9, 26, 14, 1, "t")
R(12, 21, 2, 2, "Z"); R(18, 22, 2, 2, "Z"); P(12, 22, "Y"); P(18, 23, "Y"); R(15, 17, 3, 1, "h"); R(11, 27, 3, 1, "i")
EB(16, 15, 7, 2, "t"); EL(16, 15, 5, 1, "p")
A(9, 3, {
 "......F......", ".....FZ..F...", ".....FZF.FZ..", "....FZZFFZF..",
 "...FZZYZZZZF.", "...FZYYYZZZF.", "..FZYYWYYZZZF", "..FZYYWWYYZZF",
 "..FZZYYYYYZZF", "...FFZZZZZFF." })
P(8, 5, "Z"); P(23, 7, "Y"); P(20, 3, "Z"); P(12, 2, "F")
put(3, 7)

-- Absperrung mit Blinklicht
begin()
EL(16, 29, 14, 1, "p")
RB(5, 18, 2, 10, "u"); RB(25, 18, 2, 10, "u")
RB(3, 12, 26, 5, "W")
for x = 4, 24, 6 do R(x, 13, 3, 3, "R"); R(x + 1, 12, 2, 1, "R"); R(x + 2, 16, 2, 1, "R") end
R(3, 16, 26, 1, "y")
RB(14, 6, 5, 5, "t"); R(15, 7, 3, 3, "Z"); P(16, 8, "Y"); P(15, 7, "W")
put(4, 7, shearY(0.05, 16))

-- Kartonstapel
begin()
EL(16, 29, 14, 1, "p")
RB(3, 19, 14, 9, "j"); R(4, 19, 12, 1, "k"); R(9, 19, 2, 9, "k"); R(5, 22, 3, 3, "W"); R(6, 23, 1, 1, "Q"); R(12, 25, 3, 1, "h")
RB(18, 21, 10, 7, "i"); R(19, 21, 8, 1, "j"); R(22, 21, 2, 7, "k"); R(24, 23, 3, 2, "W")
RB(7, 10, 12, 9, "k"); R(8, 10, 10, 1, "W"); R(12, 10, 2, 9, "j"); R(8, 13, 3, 3, "W"); P(9, 14, "Q"); R(15, 16, 2, 1, "h")
L(18, 9, 24, 7, "k"); L(18, 10, 24, 8, "j")
put(5, 7)

-- Satellitenschuessel
begin()
EL(16, 29, 11, 1, "p")
RB(10, 26, 12, 3, "t"); R(10, 26, 12, 1, "u"); RB(15, 22, 2, 4, "u")
EB(14, 14, 10, 8, "y"); EL(14, 14, 8, 6, "u"); EL(13, 13, 6, 4, "y"); EL(12, 12, 2, 1, "W")
L(14, 14, 23, 7, "t"); L(14, 15, 23, 8, "t"); RB(22, 5, 3, 3, "p")
put(6, 7, shearY(0.1, 16))

-- Gartenzwerg
begin()
EL(16, 30, 7, 1, "p")
A(9, 6, {
 "......oo......", ".....oQQo.....", "....oQQQQo....", "....oQQQQRo...",
 "...oQQQQQRRo..", "..oQQQQQQRRRo.", "..oRRRRRRRRRo.", "..oWWSSSSWWo..",
 "..oWSpSSpSWo..", "..oWWSNNSWWo..", "..oWWWWWWWWo..", "...oWWWWWWo...",
 "...oBBBBBBo...", "..oBBCCBBBBo..", "..oBBBBBBBBo..", ".oNoBBBBBBoNo.",
 "..oBBBBBBBBo..", "..oggoooogo...", "..ogo....ogo.." })
P(21, 14, "W"); P(22, 15, "W")
put(7, 7)

