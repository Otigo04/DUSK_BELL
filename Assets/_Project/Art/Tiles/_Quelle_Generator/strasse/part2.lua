-- Zeilen 8-11: Waende, Boden, hohe Objekte
dofile(DIR .. "objs.lua")
local SAVE = GRIME
local function asp(a, b, c3) R(0, 0, 32, 32, "t"); fleck(a or 10, "u"); fleck(b or 10, "a"); fleck(c3 or 3, "y") end
local function transpose(src)
  begin()
  for y = 0, 31 do for x = 0, 31 do img:drawPixel(y, x, src:getPixel(x, y)) end end
end

-------------------------------------------------- Zeile 8: Waende, Zaun, Boden-Dreck
GRIME = nil
local function bricks()
  R(0, 0, 32, 32, "g")
  local cols = { "h", "i", "h", "M", "i", "h" }
  for row = 0, 7 do
    local y = row * 4
    local off = (row % 2 == 0) and 0 or 4
    for bx = -1, 4 do
      local x = bx * 8 + off
      local c = cols[math.random(1, #cols)]
      R(x + 1, y + 1, 7, 3, c)
      R(x + 1, y + 1, 7, 1, (c == "h" or c == "M") and "i" or "j")
      if math.random() < 0.3 then P(x + math.random(2, 7), y + 2, "g") end
    end
  end
end
local function wallDirt()
  for i = 1, 6 do
    local x = math.random(0, 31); local y0 = math.random(0, 14)
    for k = 0, math.random(6, 14) do P(x, y0 + k, (k % 3 == 0) and "a" or "g") end
  end
  for x = 0, 31 do for y = 22, 31 do if math.random() < (y - 21) * 0.05 then P(x, y, "g") end end end
  for i = 1, 12 do P(math.random(0, 31), math.random(26, 31), math.random() < 0.5 and "n" or "q") end
  for i = 1, 10 do P(math.random(0, 31), math.random(0, 31), "y") end
end
begin(); bricks(); wallDirt()
do local px, py = math.random(7, 20), math.random(5, 12); blob(px, py, 5, 3, "k", 0.7); blob(px + 1, py + 1, 4, 2, "j", 0.8); P(px - 2, py + 3, "i") end
put(0, 8)

begin(); bricks(); wallDirt()
RING(16, 14, 10, "Q", 5); RING(16, 14, 9, "Q", 4)
EL(16, 14, 3, 3, "Q"); EL(16, 14, 1, 2, "p"); P(15, 13, "W")
L(8, 9, 6, 6, "Q"); L(12, 7, 11, 4, "Q"); L(16, 6, 16, 3, "Q"); L(20, 7, 21, 4, "Q"); L(24, 9, 26, 6, "Q")
for _, d in ipairs({ { 9, 18, 8 }, { 14, 19, 5 }, { 19, 19, 11 }, { 23, 18, 4 } }) do L(d[1], d[2], d[1], d[2] + d[3], "Q") end
P(9, 27, "Q"); P(19, 31, "Q")
put(1, 8)

begin(); bricks(); wallDirt()
R(2, 3, 11, 14, "W"); R(2, 3, 11, 3, "Q"); R(3, 8, 9, 1, "p"); R(3, 10, 7, 1, "y"); R(3, 12, 8, 1, "y"); R(3, 14, 4, 2, "c")
P(2, 3, "g"); P(3, 3, "g"); P(12, 16, "g"); P(12, 15, "g"); R(11, 3, 2, 2, "k")
R(16, 9, 12, 16, "C"); R(17, 10, 10, 5, "W"); R(17, 17, 10, 1, "W"); R(17, 19, 7, 1, "W"); R(17, 21, 9, 1, "d")
for _, p in ipairs({ { 27, 9 }, { 27, 10 }, { 26, 9 }, { 16, 24 }, { 17, 24 }, { 27, 24 }, { 22, 25 } }) do P(p[1], p[2], "g") end
R(14, 2, 4, 5, "k"); L(14, 2, 17, 6, "j"); R(5, 22, 3, 4, "k")
put(2, 8)

begin()
R(0, 0, 32, 32, "u")
R(0, 15, 32, 1, "t"); R(0, 31, 32, 1, "t"); for y = 0, 14 do P(15, y, "t") end; for y = 16, 30 do P(0, y, "t") end
for _, bx in ipairs({ 3, 12, 19, 28 }) do P(bx, 3, "y"); P(bx, 19, "y") end
for _, bx in ipairs({ 3, 28 }) do for k = 0, 9 do P(bx, 4 + k, (k % 3 == 0) and "i" or "h") end end
P(19, 20, "h"); P(19, 21, "h"); P(12, 4, "i")
for i = 1, 22 do P(math.random(0, 31), math.random(0, 31), ({ "y", "c", "t" })[math.random(1, 3)]) end
blob(22, 9, 4, 3, "t", 0.8); blob(8, 24, 3, 2, "c", 0.8)
do local pts = { { 24, 16 }, { 23, 19 }, { 25, 22 }, { 24, 26 }, { 26, 31 } }; for i = 1, #pts - 1 do L(pts[i][1], pts[i][2], pts[i + 1][1], pts[i + 1][2], "a") end end
for x = 0, 31 do if math.random() < 0.4 then P(x, 30, "g") end if math.random() < 0.25 then P(x, 29, "n") end end
put(3, 8)

begin()
for y = 3, 31 do for x = 0, 31 do
  local hole = ((x - 16) / 6) ^ 2 + ((y - 19) / 5) ^ 2 <= 1
  if not hole then
    if (x + y) % 8 == 0 or (x - y + 64) % 8 == 0 then P(x, y, "y")
    elseif (x - y + 64) % 8 == 1 then P(x, y, "u") end
  end
end end
R(0, 1, 32, 2, "u"); R(0, 1, 32, 1, "y")
for a = 0, 15 do
  local an = a / 16 * math.pi * 2
  if math.random() < 0.6 then P(math.floor(16 + math.cos(an) * 7 + 0.5), math.floor(19 + math.sin(an) * 6 + 0.5), "y") end
end
P(6, 10, "i"); P(7, 10, "j"); P(7, 11, "h"); R(23, 24, 4, 3, "W"); P(24, 25, "X"); P(25, 27, "W"); P(22, 26, "W")
for _, x in ipairs({ 3, 12, 27 }) do L(x, 31, x + 1, 25, "n"); P(x + 2, 27, "q"); P(x - 1, 28, "q") end
put(4, 8, nil, SAVE)

begin(); asp(9, 9, 2)
for i = 1, 34 do
  local x, y = math.random(0, 30), math.random(0, 30)
  local c = ({ "i", "j", "h", "k", "g", "M" })[math.random(1, 6)]
  P(x, y, c); P(x + 1, y, c); if math.random() < 0.6 then P(x, y + 1, c) end; if math.random() < 0.3 then P(x + 1, y + 1, "g") end
end
for i = 1, 4 do local x, y = math.random(2, 26), math.random(2, 28); L(x, y, x + 3, y + math.random(-1, 1), "h") end
put(5, 8)

begin(); asp(10, 8, 2)
for t = 0, 31 do
  local y = 14 + math.floor(math.sin(t * math.pi * 2 / 32) * 5 + 0.5)
  for _, off in ipairs({ 0, 7 }) do
    if math.random() > 0.2 then P(t, y + off, "p") end
    if math.random() > 0.45 then P(t, y + off + 1, "a") end
  end
end
for i = 1, 8 do P(math.random(0, 31), math.random(0, 31), "p") end
put(6, 8)

begin(); asp(9, 8, 2)
R(6, 8, 4, 3, "y"); P(6, 8, "W"); P(9, 10, "u"); P(7, 9, "Q")
R(18, 18, 6, 4, "Q"); R(18, 19, 6, 1, "Y"); P(19, 18, "p"); P(22, 21, "p"); P(24, 19, "Q")
for _, p in ipairs({ { 12, 24, "H" }, { 13, 25, "C" }, { 11, 25, "f" }, { 14, 24, "H" }, { 27, 8, "C" }, { 26, 9, "H" } }) do P(p[1], p[2], p[3]) end
R(24, 4, 2, 2, "W"); P(25, 5, "y"); R(3, 20, 2, 2, "W")
for _, p in ipairs({ { 5, 14 }, { 20, 12 }, { 14, 4 } }) do P(p[1], p[2], "W"); P(p[1] + 1, p[2], "W"); P(p[1] + 2, p[2], "j") end
P(10, 28, "Y"); P(21, 27, "Y"); P(22, 27, "k"); P(23, 28, "Y")
put(7, 8)

-------------------------------------------------- Zeile 9: Pflaster, Gleise, Bordstein-Varianten
local function cobble(grassy)
  R(0, 0, 32, 32, "a")
  local cs = { "u", "y", "c", "t", "u", "c" }
  for row = 0, 3 do
    for k = 0, 3 do
      local cx = k * 8 + ((row % 2 == 0) and 4 or 0) + math.random(-1, 1)
      local cy = row * 8 + 4 + math.random(-1, 1)
      local cc = cs[math.random(1, #cs)]
      local ry = (math.random() < 0.6) and 3 or 2
      for _, dx in ipairs({ -32, 0, 32 }) do for _, dy in ipairs({ -32, 0, 32 }) do
        EL(cx + dx, cy + dy, 3, ry, cc)
        P(cx + dx - 1, cy + dy - ry, "y"); P(cx + dx - 2, cy + dy - ry + 1, "y")
        for xx = -2, 2 do P(cx + dx + xx, cy + dy + ry, "b") end
      end end
    end
  end
  fleck(10, "g"); fleck(6, "p")
  if grassy then
    for i = 1, 22 do
      local x, y = math.random(0, 31), math.random(0, 31)
      if G(x, y) == "a" or G(x, y) == "b" then P(x, y, "n"); P(x, y - 1, "q"); if math.random() < 0.5 then P(x + 1, y - 2, "r") end end
    end
  end
end
begin(); cobble(false); put(0, 9)
begin(); cobble(true); put(1, 9)
begin(); cobble(false)
for _, ry in ipairs({ 8, 21 }) do
  R(0, ry - 1, 32, 1, "o"); R(0, ry, 32, 1, "W"); R(0, ry + 1, 32, 1, "y"); R(0, ry + 2, 32, 1, "u"); R(0, ry + 3, 32, 1, "o")
  for i = 1, 10 do P(math.random(0, 31), ry + math.random(0, 2), math.random() < 0.5 and "i" or "h") end
  for x = 3, 31, 8 do P(x, ry + 1, "c") end
end
local railH = img
put(2, 9)
transpose(railH); put(3, 9)

-- Bordstein-Aussenecke (Gehweg oben links)
begin(); sidewalk(31)
local function dd(x, y)
  local d
  if x > 6 and y > 6 then d = math.sqrt((x - 6) ^ 2 + (y - 6) ^ 2) - 6
  elseif x > 12 then d = x - 12
  elseif y > 12 then d = y - 12
  else d = 0 end
  return math.floor(d + 0.5)
end
for y = 0, 31 do for x = 0, 31 do
  local d = dd(x, y)
  if d > 0 then
    local c
    if d == 1 then c = "y" elseif d <= 4 then c = "u" elseif d <= 6 then c = "c" elseif d == 7 then c = "o"
    elseif d <= 9 then c = "p" elseif d == 10 then c = "a" else c = "t" end
    P(x, y, c)
  end
end end
for i = 1, 26 do local x, y = math.random(0, 31), math.random(0, 31); if dd(x, y) > 10 then P(x, y, ({ "u", "a", "y" })[math.random(1, 3)]) end end
for i = 1, 5 do local x, y = math.random(8, 24), math.random(8, 24); if dd(x, y) >= 2 and dd(x, y) <= 6 then P(x, y, "a") end end
for i = 1, 3 do local x, y = math.random(8, 24), math.random(8, 24); if dd(x, y) == 6 then P(x, y, "n") end end
put(4, 9)

-- Bordstein-Absenkung mit Noppenfeld
begin()
for y = 0, 31 do for x = 0, 31 do img:drawPixel(x, y, curbH:getPixel(x, y)) end end
R(8, 13, 16, 11, "t"); fleck(5, "u")
R(10, 13, 12, 8, "y"); R(8, 13, 2, 8, "c"); R(22, 13, 2, 8, "c")
for y = 14, 20, 2 do for x = 11, 21, 2 do P(x, y, "Y") end end
for y = 15, 19, 2 do for x = 12, 20, 4 do P(x, y, "k") end end
R(8, 21, 16, 1, "o"); R(10, 22, 12, 2, "p"); R(11, 24, 10, 1, "a")
fleck(6, "g"); P(10, 17, "j"); P(20, 19, "j")
put(5, 9)

-- Rinnstein mit fliessendem Wasser
function gutter(f)
  begin()
  for y = 0, 31 do for x = 0, 31 do img:drawPixel(x, y, curbH:getPixel(x, y)) end end
  R(0, 20, 32, 1, "o"); R(0, 21, 32, 3, "d"); R(0, 24, 32, 1, "a")
  for x = 0, 31 do
    local ph = (x - f * 2) % 8
    if ph == 0 or ph == 1 then P(x, 22, "f") end
    if ph == 4 then P(x, 23, "e") end
    if ph == 5 then P(x, 21, "e") end
    if ph == 0 and x % 16 == 0 then P(x, 22, "m") end
  end
  P(6, 22, "i"); P(7, 22, "j"); P(7, 23, "h"); P(21, 23, "W"); P(22, 23, "W"); P(23, 23, "j"); P(14, 21, "k")
  return img
end
gutter(0); put(6, 9)

begin(); asp(9, 8, 2)
TF(3, 12, 15, 16, 6, 25, "W"); R(12, 13, 8, 18, "W")
for i = 1, 46 do local x, y = math.random(5, 26), math.random(3, 30); if G(x, y) == "W" then P(x, y, ({ "t", "y", "u" })[math.random(1, 3)]) end end
for i = 1, 6 do P(math.random(11, 20), math.random(13, 30), "k") end
put(7, 9)

-------------------------------------------------- Zeile 10-11: hohe Objekte (32x64)
GRIME = SAVE
drawBushalt(0); put(0, 10)

begin(32, 64)
EL(16, 61, 15, 2, "p")
-- Plane
for x = 5, 26 do
  local h = 8 + ((x * 7) % 5)
  for y = 5, 5 + h do P(x, y, ((x % 5 == 0) and "d") or ((x % 5 == 2) and "C") or "B") end
  P(x, 5 + h + 1, "o")
end
R(5, 4, 22, 1, "o")
for _, p in ipairs({ { 9, 9 }, { 10, 9 }, { 19, 12 }, { 20, 12 }, { 20, 13 } }) do P(p[1], p[2], "p") end
for _, x in ipairs({ 3, 27 }) do RB(x, 4, 2, 56, "u"); R(x, 4, 1, 56, "t"); R(x + 1, 4, 1, 56, "y") end
for _, y in ipairs({ 20, 38, 56 }) do
  RB(1, y, 30, 3, "i"); R(1, y, 30, 1, "j")
  for x = 5, 28, 6 do R(x, y + 1, 1, 2, "g") end
end
L(5, 23, 26, 37, "y"); L(6, 23, 27, 37, "u"); L(26, 41, 5, 55, "y"); L(27, 41, 6, 55, "u")
RB(3, 10, 26, 1, "u"); R(5, 12, 22, 1, "u")
RB(18, 14, 5, 5, "y"); R(18, 14, 5, 1, "W"); L(18, 14, 23, 14, "u"); R(19, 16, 3, 2, "k")
RB(8, 31, 4, 4, "j"); R(9, 31, 2, 1, "k")
put(1, 10)

begin(32, 64)
EL(16, 61, 9, 2, "p")
RB(13, 10, 6, 50, "u"); R(13, 10, 2, 50, "t"); R(18, 10, 1, 50, "y")
for y = 18, 54, 6 do R(13, y, 6, 1, "c") end
RB(4, 8, 24, 3, "t"); R(4, 8, 24, 1, "u")
L(8, 11, 8, 18, "p")
TB(19, 25, 5, 11, 3, 13, "R"); R(5, 19, 7, 1, "Q"); R(7, 26, 2, 2, "Y"); P(7, 26, "W"); P(6, 28, "Z"); P(9, 28, "Z")
RB(19, 26, 6, 8, "y"); EL(22, 29, 2, 2, "W"); P(22, 29, "p"); P(21, 28, "p")
L(26, 11, 31, 22, "p"); L(5, 11, 0, 22, "p"); L(24, 11, 31, 16, "p")
RB(14, 40, 4, 5, "Y"); P(15, 41, "p"); P(16, 42, "p"); P(15, 43, "p")
R(14, 22, 4, 6, "k"); P(15, 23, "g"); P(17, 27, "g")
L(14, 52, 17, 49, "Q"); L(17, 49, 15, 47, "Q")
put(2, 10, shearX(0.04, 62))

begin(32, 64)
EL(16, 61, 12, 2, "p")
RB(7, 6, 18, 54, "R"); R(7, 6, 18, 1, "Q"); R(7, 7, 2, 52, "a"); R(24, 7, 1, 52, "Q")
R(9, 8, 14, 6, "Y"); R(9, 8, 14, 1, "W"); R(11, 10, 3, 2, "p"); R(15, 10, 5, 2, "p")
RB(9, 16, 14, 24, "d")
do
  local pal = { "W", "Q", "C", "Y", "Z" }
  for r, y in ipairs({ 18, 24, 30, 36 }) do
    for k = 0, 3 do
      local x = 10 + k * 3
      local c = pal[(r + k) % 5 + 1]
      R(x, y - 1, 2, 4, c); R(x, y - 1, 2, 1, "W")
    end
  end
end
RB(9, 42, 6, 6, "p"); R(10, 43, 4, 2, "Y"); P(11, 46, "u"); P(13, 46, "u")
R(17, 43, 5, 1, "p"); RB(18, 45, 3, 3, "u")
RB(10, 50, 12, 6, "p"); R(11, 51, 10, 1, "u")
R(8, 56, 5, 2, "W"); P(9, 57, "Q"); R(7, 59, 18, 1, "a")
P(22, 28, "a"); P(21, 29, "a"); R(20, 22, 2, 1, "b")
put(3, 10)

drawFlag(0); put(4, 10)

begin(32, 64)
EL(16, 61, 14, 2, "p")
RB(2, 10, 28, 2, "u"); R(2, 10, 28, 1, "y")
RB(2, 2, 28, 1, "u"); R(2, 6, 28, 1, "t")
for _, x in ipairs({ 2, 29 }) do R(x, 2, 1, 9, "u") end
TL({ { 26, 13 }, { 6, 33 } }, "o", 4)
TL({ { 27, 14 }, { 7, 34 } }, "u", 2)
for k = 0, 8 do local x = 25 - k * 2; local y = 15 + k * 2; R(x - 2, y, 4, 1, "y") end
RB(2, 34, 28, 2, "u"); R(2, 34, 28, 1, "y")
for _, x in ipairs({ 2, 29 }) do R(x, 26, 1, 8, "u") end
R(2, 26, 28, 1, "t")
TL({ { 5, 37 }, { 25, 57 } }, "o", 4)
TL({ { 6, 38 }, { 26, 58 } }, "u", 2)
for k = 0, 8 do local x = 7 + k * 2; local y = 39 + k * 2; R(x - 1, y, 4, 1, "y") end
RB(24, 56, 1, 6, "y"); R(24, 58, 1, 1, "u"); R(24, 60, 1, 1, "u")
R(10, 7, 3, 3, "i"); P(11, 6, "n"); P(20, 12, "W")
put(5, 10)

begin(32, 64)
booth({ { "dark", "dark", "gone" }, { "dark", "crack", "dark" }, { "gone", "dark", "dark" }, { "dark", "lit", "dark" } })
local function vine(x0, y0, steps)
  local x, y = x0, y0
  for i = 1, steps do
    x = math.max(5, math.min(26, x + math.random(-1, 1))); y = y - 1
    P(x, y, "l")
    if i % 2 == 0 then
      local c = ({ "n", "q", "r", "n" })[math.random(1, 4)]
      P(x + 1, y, c); P(x + 2, y, c); P(x - 1, y, c); P(x, y - 1, c); P(x + 1, y + 1, "l")
    end
  end
end
vine(7, 60, 46); vine(24, 60, 38); vine(15, 60, 22)
blob(16, 6, 9, 1, "n", 0.6); blob(10, 5, 3, 1, "q", 0.6)
for _, x in ipairs({ 8, 13, 20, 24 }) do L(x, 12, x, 12 + math.random(3, 7), "l"); P(x, 17, "n") end
put(6, 10, nil, { soot = 0.2, mud = 4, streaks = 6, rust = 3, specks = 0.06, moss = 14 })

begin(32, 64)
EL(16, 61, 14, 2, "p")
RB(2, 50, 16, 8, "i"); R(2, 50, 16, 1, "j"); R(3, 51, 14, 2, "e"); R(4, 51, 5, 1, "f")
L(6, 54, 6, 57, "g"); L(11, 54, 11, 57, "g")
RB(19, 52, 10, 8, "u"); R(19, 52, 10, 1, "y")
RB(21, 16, 6, 36, "t"); R(21, 16, 2, 36, "a"); R(26, 16, 1, 36, "y")
RB(19, 12, 10, 6, "t"); R(19, 12, 10, 1, "y")
RB(8, 30, 12, 3, "t"); R(8, 30, 12, 1, "y"); R(8, 33, 3, 2, "t"); P(9, 37, "f"); P(9, 36, "m")
TL({ { 22, 13 }, { 29, 3 } }, "o", 4)
TL({ { 23, 14 }, { 30, 4 } }, "u", 2)
RB(28, 0, 3, 3, "y")
put(7, 10)
