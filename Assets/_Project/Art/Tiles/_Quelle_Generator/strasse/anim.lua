-- Animierte Streifen (horizontal), je Frame-Groesse w x h
local GD = { soot = 0.14, mud = 4, streaks = 4, rust = 3, specks = 0.04 }
local function anim(name, n, w, h, ms, fn, tfm, gr)
  local fr = {}
  for f = 0, n - 1 do
    math.randomseed(100 + f * 0 + #name)
    begin(w, h)
    fn(f)
    local tf = tfm and tfm(f) or nil
    if gr == false then fr[#fr + 1] = bake(tf, nil)
    else fr[#fr + 1] = bake(tf, gr or GD, 77 + #name) end
  end
  saveAnim(name, fr, w, h, ms)
end
local function asp(a, b, c3) R(0, 0, 32, 32, "t"); fleck(a or 10, "u"); fleck(b or 10, "a"); fleck(c3 or 3, "y") end

-------------------------------------------------- einfache Wrapper fuer objs.lua
anim("Strasse_Katze_Anim", 8, 32, 32, 160, drawCat)
anim("Strasse_Ratte_Anim", 4, 32, 32, 110, drawRat)
anim("Strasse_Taube_Anim", 4, 32, 32, 220, drawPigeon)
anim("Strasse_Boombox_Anim", 4, 32, 32, 160, drawBoombox)
anim("Strasse_Grablicht_Anim", 4, 32, 32, 130, drawGrablicht, nil, false)
anim("Strasse_Kaugummiautomat_Anim", 4, 32, 32, 200, drawKaugummi)
anim("Strasse_Neon_Bar_Anim", 8, 32, 32, 90, drawNeon)
anim("Strasse_Fahne_Anim", 6, 32, 64, 160, drawFlag)
anim("Strasse_Bushaltestelle_Anim", 4, 32, 64, 280, drawBushalt)
anim("Strasse_Zwerg_Anim", 6, 32, 32, 220, drawZwerg)

-------------------------------------------------- Feuertonne
anim("Strasse_Feuertonne_Anim", 6, 32, 32, 100, function(f)
  EL(16, 30, 11, 1, "p")
  RB(9, 15, 14, 14, "u"); R(9, 15, 3, 14, "t"); R(22, 15, 1, 14, "y"); R(9, 20, 14, 1, "t"); R(9, 26, 14, 1, "t")
  local v = (f % 2 == 0) and "Z" or "Y"
  R(12, 21, 2, 2, v); R(18, 22, 2, 2, v); P(12, 22, "Y"); P(18, 23, "Y")
  R(15, 17, 3, 1, "h"); R(11, 27, 3, 1, "i")
  EB(16, 15, 7, 2, "t"); EL(16, 15, 5, 1, (f % 2 == 0) and "F" or "Z")
  local layers = { { 6, 11, "F" }, { 4, 9, "Z" }, { 2.6, 6, "Y" }, { 1.4, 3, "W" } }
  for li, l in ipairs(layers) do
    local hw, hh, c = l[1], l[2], l[3]
    hh = hh + ({ 0, 1, 0, -1, 1, 0 })[f + 1] * ((li < 4) and 1 or 0)
    for r = 0, hh - 1 do
      local t = r / hh
      local w = hw * (1 - t ^ 1.6)
      local sway = math.floor(math.sin(f / 6 * math.pi * 2 + t * 3 + li) * 1.6 * t + 0.5)
      local y = 14 - r
      for x = math.floor(16 - w + sway + 0.5), math.floor(16 + w + sway + 0.5) do P(x, y, c) end
    end
  end
  for k = 0, 2 do
    local t = ((f / 6) + k / 3) % 1
    local x = 16 + math.floor(math.sin(t * 5 + k * 2) * 6)
    local y = 6 - math.floor(t * 6)
    P(x, y, (t < 0.5) and "Y" or "Z")
  end
end)

-------------------------------------------------- Telefonzelle flackert (+ Motte)
local pane0 = pane
function pane(px, py, st)
  if st == "dim" then R(px, py, 4, 9, "Z"); P(px, py, "Y"); R(px + 3, py + 1, 1, 8, "j")
  else pane0(px, py, st) end
end
local LIT = { { "lit", "lit", "lit" }, { "lit", "lit", "lit" }, { "lit", "lit", "lit" }, { "lit", "lit", "lit" } }
local DIM = { { "dim", "dim", "dim" }, { "dim", "dim", "dim" }, { "dim", "dim", "dim" }, { "dim", "dim", "dim" } }
local FLK = { { "lit", "lit", "lit" }, { "lit", "dark", "lit" }, { "lit", "lit", "dark" }, { "lit", "lit", "lit" } }
local stt = { LIT, DIM, FLK, LIT }
local moth = { { 27, 8 }, { 28, 6 }, { 29, 9 }, { 28, 7 } }
anim("Strasse_Telefonzelle_Anim", 4, 32, 64, 140, function(f)
  math.randomseed(21)
  booth(stt[f + 1])
  local m = moth[f + 1]
  P(m[1], m[2], "W"); P(m[1] + 1, m[2] - 1, "y"); P(m[1] - 1, m[2] - 1, "y")
end)

-------------------------------------------------- Laterne flackert, Insekten kreisen
anim("Strasse_Laterne_Anim", 6, 32, 64, 120, function(f)
  local lens = ({ "Y", "W", "Y", "Z", "Y", "W" })[f + 1]
  local reach = ({ 10, 12, 9, 6, 10, 12 })[f + 1]
  for y = 15, 15 + reach do
    local sp = (y - 15) // 2
    for x = 22 - sp, 29 + sp do
      if (y - 15) < reach * 0.45 then
        if (x + y) % 2 == 0 then P(x, y, "Y") end
      elseif (x + y) % 4 == 0 then P(x, y, "Z") end
    end
  end
  EL(16, 61, 10, 2, "p")
  RB(11, 55, 10, 6, "t"); R(12, 55, 8, 1, "y")
  RB(14, 8, 4, 48, "u"); R(14, 8, 1, 48, "t"); R(17, 8, 1, 48, "y")
  RB(16, 6, 12, 3, "u"); R(16, 6, 12, 1, "y")
  RB(21, 9, 10, 4, "t"); R(21, 9, 10, 1, "u")
  R(22, 13, 8, 2, lens); if lens == "Y" then R(24, 13, 4, 1, "W") end
  for k = 0, 1 do
    local a = f / 6 * math.pi * 2 + k * math.pi
    local mx, my = 26 + math.floor(math.cos(a) * 5 + 0.5), 17 + math.floor(math.sin(a) * 3 + 0.5)
    P(mx, my, "p"); P(mx + 1, my - 1, "W")
  end
end, function() return shearX(-0.1, 62) end)

-------------------------------------------------- Ampel blinkt
anim("Strasse_Ampel_Anim", 4, 32, 64, 350, function(f)
  EL(16, 61, 8, 2, "p")
  RB(14, 24, 4, 36, "u"); R(14, 24, 1, 36, "t"); R(17, 24, 1, 36, "y")
  RB(9, 2, 14, 26, "a"); R(9, 2, 1, 26, "p"); R(22, 3, 1, 24, "b")
  RB(18, 36, 4, 6, "t"); P(20, 38, "Y")
  local cols = {
    { "R", "Y", "n" }, { "R", "Y", "n" }, { "R", "j", "n" }, { "R", "j", "r" } }
  local c = cols[f + 1]
  for i, cy in ipairs({ 7, 14, 21 }) do
    EB(16, cy, 3, 3, c[i]); R(12, cy - 5, 9, 1, "o")
  end
  if f == 0 then RING(16, 14, 5, "Z", 5); P(15, 13, "W"); P(16, 13, "W") end
  if f == 1 then P(15, 13, "W") end
  if f == 3 then P(15, 20, "s"); P(16, 20, "W") end
end, function() return shearX(0.06, 62) end)

-------------------------------------------------- Absperrung mit Blinklicht
anim("Strasse_Blinklicht_Anim", 4, 32, 32, 250, function(f)
  EL(16, 29, 14, 1, "p")
  RB(5, 18, 2, 10, "u"); RB(25, 18, 2, 10, "u")
  RB(3, 12, 26, 5, "W")
  for x = 4, 24, 6 do R(x, 13, 3, 3, "R"); R(x + 1, 12, 2, 1, "R"); R(x + 2, 16, 2, 1, "R") end
  R(3, 16, 26, 1, "y")
  RB(14, 6, 5, 5, "t")
  if f == 0 then
    R(15, 7, 3, 3, "Y"); P(16, 8, "W")
    for _, p in ipairs({ { 12, 8 }, { 20, 8 }, { 16, 4 }, { 13, 5 }, { 19, 5 }, { 11, 8 }, { 21, 8 } }) do P(p[1], p[2], "Z") end
  elseif f == 1 then
    R(15, 7, 3, 3, "Z"); P(12, 8, "j"); P(20, 8, "j")
  else
    R(15, 7, 3, 3, "a"); P(15, 7, "b")
  end
end, function() return shearY(0.05, 16) end)

-------------------------------------------------- Gully mit Dampf
anim("Strasse_Gully_Dampf_Anim", 6, 32, 32, 150, function(f)
  EL(15, 25, 11, 5, "o"); EL(15, 25, 10, 4, "u"); EL(15, 25, 9, 3, "p"); EL(15, 26, 6, 1, "a")
  EB(26, 18, 4, 6, "u"); EL(26, 18, 2, 4, "y"); R(26, 15, 1, 6, "t"); L(24, 18, 28, 18, "t")
  for k = 0, 2 do
    local t = ((f / 6) + k / 3) % 1
    local y = 22 - math.floor(t * 19)
    local x = 15 + math.floor(math.sin(t * 6 + k * 2) * 3)
    if t < 0.3 then P(x, y, "m"); P(x + 1, y, "m")
    elseif t < 0.7 then R(x - 1, y, 3, 2, "m"); P(x - 2, y + 1, "y"); P(x + 2, y, "y")
    else P(x - 1, y, "y"); P(x + 1, y + 1, "y"); P(x + 2, y - 1, "c"); P(x - 2, y + 1, "c") end
  end
end)

-------------------------------------------------- Fernseher rauscht
anim("Strasse_Fernseher_Anim", 4, 32, 32, 90, function(f)
  stamp(32, 32, function()
    math.randomseed(300 + f)
    L(14, 8, 10, 2, "u"); L(18, 8, 22, 3, "u"); P(10, 2, "y"); P(22, 3, "y")
    RB(6, 9, 20, 15, "i"); R(7, 9, 18, 1, "j")
    RB(8, 11, 12, 11, (f == 2) and "f" or "e")
    for i = 1, 30 do local ch = { "f", "m", "d", "e", "f" }; P(math.random(8, 19), math.random(11, 21), ch[math.random(1, 5)]) end
    R(8, 11 + (f * 3) % 10, 12, 1, "m")
    P(9, 12, "m"); P(10, 12, "f"); P(9, 13, "f")
    P(22, 13, "Y"); P(22, 17, "y"); L(21, 19, 23, 19, "h"); L(21, 21, 23, 21, "h")
  end, shearY(-0.1, 6), 0, 0)
  RB(4, 24, 24, 6, "j"); R(4, 24, 24, 1, "k"); L(5, 25, 27, 29, "i"); L(27, 25, 5, 29, "i")
  EL(16, 31, 12, 1, "p")
end)

-------------------------------------------------- Getraenkeautomat flackert
anim("Strasse_Automat_Anim", 4, 32, 64, 220, function(f)
  EL(16, 61, 13, 2, "p")
  RB(6, 5, 20, 54, "B"); R(7, 5, 18, 1, "C"); R(6, 6, 1, 52, "d"); R(25, 6, 1, 52, "C")
  local hd = ({ "Y", "Z", "Y", "Y" })[f + 1]
  R(8, 7, 16, 6, hd); R(10, 9, 3, 2, "p"); R(14, 9, 5, 2, "p"); R(20, 9, 2, 2, "p"); if hd == "Y" then R(8, 7, 16, 1, "W") end
  RB(8, 15, 12, 26, (f == 3) and "Z" or "Y"); R(8, 15, 12, 26, (f == 3) and "Z" or "Y")
  local cc = { "Q", "C", "s", "Z", "W" }
  for _, y in ipairs({ 19, 25, 31, 37 }) do
    for i = 0, 4 do R(9 + i * 2, y - 4, 2, 4, cc[(i + y) % 5 + 1]) end
    R(8, y, 12, 1, "p")
  end
  R(8, 15, 1, 26, "Z")
  R(21, 16, 3, 2, "Z"); R(21, 20, 3, 2, "Z"); R(21, 26, 3, 1, "p")
  for y = 29, 35, 3 do for x = 21, 23, 2 do P(x, y, "u") end end
  RB(10, 46, 12, 8, "p"); R(11, 47, 10, 1, "u")
  if f == 3 then R(13, 49, 2, 4, "Q") end
  R(6, 57, 20, 2, "d"); P(9, 43, "d"); P(10, 44, "d")
  local gx = 9 + f * 3
  L(gx, 16, gx - 3, 22, "W"); P(gx + 1, 16, "m")
end)

-------------------------------------------------- Muenztelefon, Hoerer pendelt
anim("Strasse_Muenztelefon_Anim", 4, 32, 32, 200, function(f)
  EL(16, 29, 10, 1, "p")
  RB(14, 23, 4, 6, "u"); R(14, 23, 1, 6, "t")
  RB(9, 4, 14, 19, "B"); R(9, 4, 14, 1, "C"); R(22, 5, 1, 17, "C"); R(9, 5, 2, 17, "d")
  R(12, 7, 8, 3, "Y"); R(12, 7, 8, 1, "W"); P(14, 8, "p"); P(16, 8, "p"); P(18, 8, "p")
  for _, y in ipairs({ 13, 16, 19 }) do for _, x in ipairs({ 13, 16, 19 }) do P(x, y, "W") end end
  local dx = ({ 0, 1, 0, -1 })[f + 1]
  L(10, 18, 7 + dx, 20, "p"); L(7 + dx, 20, 6 + dx, 24, "p")
  RB(3 + dx, 24, 5, 4, "p"); P(4 + dx, 24, "b"); P(6 + dx, 24, "b")
end, function() return shearX(-0.04, 29) end)

-------------------------------------------------- Pfuetze mit Regenringen, Oel, Rinnstein
anim("Strasse_Pfuetze_Regen_Anim", 6, 32, 32, 120, function(f)
  math.randomseed(41)
  asp(8, 8, 2)
  EL(16, 17, 13, 7, "d"); EL(16, 17, 12, 6, "e"); EL(15, 16, 9, 3, "f")
  R(20, 14, 3, 1, "m"); P(18, 16, "m"); L(8, 20, 12, 20, "f"); P(24, 19, "f")
  P(10, 16, "i"); P(11, 16, "j"); P(12, 17, "h")
  for _, rp in ipairs({ { 11, 17, 0 }, { 21, 19, 3 }, { 16, 15, 5 } }) do
    local r = ((f + rp[3]) % 6) + 1
    if r <= 5 then
      for a = 0, 47 do
        local an = a / 48 * math.pi * 2
        local x = math.floor(rp[1] + math.cos(an) * r * 1.6 + 0.5)
        local y = math.floor(rp[2] + math.sin(an) * r * 0.8 + 0.5)
        local g = G(x, y)
        if g == "e" or g == "f" or g == "m" then P(x, y, (r < 3) and "m" or "f") end
      end
    end
    if r == 1 then P(rp[1], rp[2] - 4, "f"); P(rp[1], rp[2] - 3, "m") end
  end
end, nil, false)

anim("Strasse_Oelfleck_Anim", 4, 32, 32, 300, function(f)
  math.randomseed(42)
  asp(8, 8, 2)
  EL(15, 16, 11, 7, "p"); EL(17, 17, 8, 5, "a")
  local cs = { "C", "Q", "s", "Y", "B" }
  for k = 0, 9 do
    local a = k * 0.62 + f * 0.5
    local x = 16 + math.floor(math.cos(a) * 8 + 0.5)
    local y = 16 + math.floor(math.sin(a) * 4 + 0.5)
    local g = G(x, y)
    if g == "p" or g == "a" then P(x, y, cs[(k + f) % 5 + 1]) end
  end
end, nil, false)

anim("Strasse_Rinnstein_Anim", 4, 32, 32, 180, function(f) gutter(f) end, nil, false)

-------------------------------------------------- Telefonmast im Wind (Kabel, Vogel)
anim("Strasse_Telefonmast_Anim", 4, 32, 64, 250, function(f)
  EL(16, 61, 8, 2, "p")
  local e1 = ({ 0, 1, 2, 1 })[f + 1]
  local e2 = ({ 2, 1, 0, 1 })[f + 1]
  L(6, 9, 0, 14 + e1, "p"); L(11, 9, 0, 17 + e1, "p"); L(20, 9, 31, 17 + e2, "p"); L(25, 9, 31, 14 + e2, "p")
  L(9, 19, 0, 22 + e1, "p"); L(22, 19, 31, 22 + e2, "p")
  RB(14, 12, 4, 50, "i"); R(14, 12, 1, 50, "h"); R(17, 12, 1, 50, "j")
  RB(3, 12, 26, 3, "i"); R(3, 12, 26, 1, "j"); RB(7, 22, 18, 3, "i"); R(7, 22, 18, 1, "j")
  for _, x in ipairs({ 6, 11, 20, 25 }) do R(x, 9, 2, 3, "y"); P(x, 9, "W"); R(x, 11, 2, 1, "u") end
  for _, x in ipairs({ 9, 22 }) do R(x, 19, 2, 3, "y"); R(x, 21, 2, 1, "u") end
  RB(10, 32, 7, 10, "t"); R(10, 32, 7, 1, "y"); R(13, 33, 1, 8, "u"); P(15, 37, "Y")
  L(13, 42, 12, 47, "p"); L(12, 47, 14, 52, "p")
  RB(19, 28, 5, 11, "u"); R(19, 28, 5, 1, "y"); R(19, 33, 5, 1, "t"); R(23, 29, 1, 9, "y")
  for _, y in ipairs({ 44, 48, 52 }) do P(13, y, "u"); P(18, y, "u") end
  if f == 2 then
    A(13, 7, { "...pp.", "p.pppZ", ".pppp." }); P(15, 10, "p"); P(17, 10, "p")
  else
    A(13, 6, { "...pp.", "p.pppZ", ".pppp.", "..pp.." }); P(15, 10, "p"); P(17, 10, "p")
    if f == 1 then P(12, 6, "p") end
  end
end, function() return shearX(0.05, 62) end)

-------------------------------------------------- Litfasssaeule, Plakat flattert
anim("Strasse_Litfasssaeule_Anim", 4, 32, 64, 200, function(f)
  EL(16, 61, 13, 2, "p")
  RB(7, 14, 18, 46, "k")
  R(8, 16, 16, 8, "Q"); R(8, 26, 16, 10, "e"); R(8, 38, 16, 8, "Y"); R(8, 48, 16, 10, "B")
  R(10, 18, 8, 2, "W"); R(10, 21, 5, 1, "W"); R(10, 29, 9, 1, "f"); R(10, 32, 6, 3, "m")
  R(10, 40, 12, 2, "Z"); R(12, 50, 4, 4, "C")
  for _, p in ipairs({ { 8, 24 }, { 9, 25 }, { 12, 25 }, { 20, 25 }, { 22, 24 }, { 23, 36 }, { 16, 37 }, { 9, 36 }, { 18, 46 }, { 23, 47 }, { 10, 47 } }) do P(p[1], p[2], "k") end
  R(8, 14, 1, 46, "a"); R(24, 15, 1, 44, "W")
  EB(16, 12, 11, 3, "u"); EL(16, 11, 8, 2, "y")
  RB(6, 58, 20, 3, "t"); R(6, 58, 20, 1, "u")
  local len = ({ 2, 4, 5, 3 })[f + 1]
  for i = 1, len do
    local up = (f % 2 == 0) and -(i // 2) or (i // 2)
    R(24 + i, 36 + up, 1, 9 - i // 2, (i % 2 == 0) and "W" or "m")
    P(24 + i, 36 + up - 1, "o"); P(24 + i, 36 + up + 9 - i // 2, "o")
  end
  P(28 + (f % 3), 30 - f, "W"); P(27, 50 + f, "y")
end)

-------------------------------------------------- Parkuhr abgelaufen
anim("Strasse_Parkuhr_Anim", 4, 32, 32, 400, function(f)
  EL(16, 29, 8, 1, "p")
  RB(15, 12, 3, 17, "u"); R(15, 12, 1, 17, "t"); R(17, 12, 1, 17, "y")
  RB(11, 3, 11, 10, "y"); R(11, 3, 11, 1, "W"); R(11, 4, 2, 9, "u")
  R(14, 5, 6, 4, "e"); P(14, 5, "f")
  if f < 2 then P(15, 7, "Y"); P(17, 7, "Y"); P(18, 7, "Y") end
  R(14, 10, 6, 1, (f % 2 == 0) and "Q" or "R"); R(16, 11, 2, 1, "p")
  RB(13, 28, 7, 2, "t")
end, function() return shearX(-0.1, 29) end)

-------------------------------------------------- Hydrant tropft
anim("Strasse_Hydrant_Anim", 6, 32, 32, 130, function(f)
  EL(16, 29, 10, 1, "p")
  A(8, 13, {
   "......oooo......", ".....oRRQQo.....", "....oRRRQQQo....", "....oRRRRQQo....",
   "...oooooooooo...", "..oyyyyyyyyyyo..", "...oooooooooo...", "...oRRRRRRQQo...",
   "ooooRRRRRRQQoooo", "oyyoRRRRRRQQoyyo", "oyyoRRRRRRQQoyyo", "ooooRRRRRRQQoooo",
   "...oRRRRRRQQo...", "...oRRRRRRQQo...", "..ooooooooooo...", ".oRRRRRRRRQQQQo.",
   ".oooooooooooooo." })
  R(5, 29, 7, 1, "e")
  if f == 0 then P(9, 25, "f"); P(9, 26, "f")
  elseif f == 1 then P(9, 27, "f"); P(9, 28, "m")
  elseif f == 2 then P(8, 29, "m"); P(10, 29, "m"); P(9, 28, "f")
  elseif f == 3 then RING(9, 29, 3, "f", 1)
  elseif f == 4 then RING(9, 29, 4, "e", 1) end
end)

-------------------------------------------------- Muelltonne mit Fliegen
anim("Strasse_Muelltonne_Fliegen_Anim", 6, 32, 32, 100, function(f)
  EL(16, 30, 11, 1, "p")
  R(8, 9, 5, 3, "B"); P(9, 8, "C"); P(11, 8, "W")
  TB(14, 28, 8, 25, 9, 23, "u")
  for _, x in ipairs({ 12, 16, 20 }) do R(x, 15, 1, 12, "t") end
  L(24, 15, 23, 27, "y"); R(9, 28, 15, 1, "t")
  TR(7, 12, 20, 3, -0.2, "y")
  R(21, 7, 3, 2, "X")
  for k = 0, 2 do
    local a = f / 6 * math.pi * 2 + k * 2.1
    local x = 17 + math.floor(math.cos(a) * (3 + k * 2) + 0.5)
    local y = 6 + math.floor(math.sin(a * 2) * 3 + 0.5)
    P(x, y, "p"); if f % 2 == 0 then P(x + 1, y - 1, "W") else P(x - 1, y - 1, "W") end
  end
end)

-------------------------------------------------- Schildermast, Platte quietscht
anim("Strasse_Schildermast_Anim", 6, 32, 64, 150, function(f)
  EL(16, 61, 7, 2, "p")
  RB(15, 4, 2, 57, "u"); R(15, 4, 1, 57, "t"); R(16, 4, 1, 57, "y")
  EB(16, 12, 7, 7, "B"); EL(16, 12, 6, 6, "W"); EL(16, 12, 5, 5, "B")
  R(15, 9, 2, 7, "W"); P(14, 10, "W"); P(17, 10, "W"); P(13, 11, "W"); P(18, 11, "W")
  SP({ { 24, 13, 18 }, { 25, 11, 20 }, { 26, 10, 21 }, { 27, 10, 21 }, { 28, 10, 21 }, { 29, 10, 21 }, { 30, 10, 21 }, { 31, 10, 21 }, { 32, 10, 21 }, { 33, 10, 21 }, { 34, 11, 20 }, { 35, 13, 18 } }, "R")
  R(12, 28, 8, 1, "W"); R(12, 30, 8, 1, "W"); R(12, 32, 8, 1, "W")
  local k = ({ 0.30, 0.18, 0.06, -0.06, 0.06, 0.18 })[f + 1]
  stamp(24, 14, function()
    RB(2, 2, 19, 8, "e"); R(3, 3, 17, 1, "f"); R(5, 5, 12, 1, "W"); R(5, 7, 8, 1, "W")
  end, shearY(k, 12), 4, 42)
  P(14, 41, "y"); P(16, 41, "y")
  if f == 0 or f == 3 then P(3, 41, "W"); P(2, 40, "W") end
end, function() return shearX(0.07, 62) end)

-------------------------------------------------- Zeitung weht ueber die Strasse
anim("Strasse_Zeitung_Anim", 8, 32, 32, 100, function(f)
  local k = ({ 0.4, -0.3, 0.2, -0.5, 0.3, -0.2, 0.4, -0.3 })[f + 1]
  local x = -6 + f * 5
  local y = 21 + math.floor(math.sin(f * 0.9) * 3 + 0.5)
  stamp(10, 8, function()
    R(0, 0, 8, 5, "W"); R(1, 1, 6, 1, "y"); R(1, 3, 4, 1, "y"); R(0, 0, 8, 1, "X")
    R(0, 0, 8, 1, "o"); R(0, 5, 8, 1, "o"); R(0, 0, 1, 6, "o"); R(7, 0, 1, 6, "o")
    R(1, 1, 6, 4, "W"); R(1, 1, 6, 1, "y"); R(1, 3, 4, 1, "y"); P(5, 3, "u"); P(6, 3, "u")
  end, shearY(k, 4), x, y)
end, nil, false)

-------------------------------------------------- Zigarettenkippe glimmt
anim("Strasse_Kippe_Anim", 4, 32, 32, 220, function(f)
  R(13, 27, 4, 1, "W"); R(17, 27, 1, 1, "j"); R(12, 27, 1, 1, (f % 2 == 0) and "F" or "Z")
  P(12, 28, "p"); P(13, 28, "p")
  for k = 0, 2 do
    local y = 26 - ((f * 2 + k * 4) % 12)
    local x = 12 + math.floor(math.sin((f + k) * 1.1) * 1.5 + 0.5)
    P(x, y, (k == 0) and "y" or "c")
  end
end, nil, false)

-------------------------------------------------- Handpumpe tropft
anim("Strasse_Pumpe_Anim", 6, 32, 64, 140, function(f)
  EL(16, 61, 14, 2, "p")
  RB(2, 50, 16, 8, "i"); R(2, 50, 16, 1, "j"); R(3, 51, 14, 2, "e"); R(4, 51, 5, 1, "f")
  L(6, 54, 6, 57, "g"); L(11, 54, 11, 57, "g")
  RB(19, 52, 10, 8, "u"); R(19, 52, 10, 1, "y")
  RB(21, 16, 6, 36, "t"); R(21, 16, 2, 36, "a"); R(26, 16, 1, 36, "y")
  RB(19, 12, 10, 6, "t"); R(19, 12, 10, 1, "y")
  RB(8, 30, 12, 3, "t"); R(8, 30, 12, 1, "y"); R(8, 33, 3, 2, "t")
  local hl = ({ 0, 0, 0, 1, 1, 0 })[f + 1]
  TL({ { 22, 13 }, { 29, 3 + hl } }, "o", 4)
  TL({ { 23, 14 }, { 30, 4 + hl } }, "u", 2)
  RB(28, 0 + hl, 3, 3, "y")
  if f == 0 then P(9, 36, "f")
  elseif f == 1 then P(9, 41, "f"); P(9, 40, "m")
  elseif f == 2 then P(9, 47, "f"); P(9, 46, "m")
  elseif f == 3 then RING(9, 51, 2, "m", 1)
  elseif f == 4 then RING(9, 51, 3, "f", 1) end
end)

-------------------------------------------------- Autos: Leerlauf mit Auspuff, Warnblinker, rauchendes Wrack
anim("Strasse_Auto_Leerlauf_Anim", 6, 80, 32, 110, function(f)
  OX = 14; OY = (f % 2 == 0) and 0 or 1
  carA(false, "R", "Q", "a")
  OY = 0
  for _, cx in ipairs({ 14, 49 }) do
    for y = 17, 22 do for x = cx - 7, cx + 7 do
      if ((x - cx) ^ 2) / 49 + ((y - 24) ^ 2) / 36 <= 1 then P(x, y, "p") end
    end end
  end
  wheel(14, 24); wheel(49, 24)
  R(8, 16, 3, 2, "i"); R(9, 17, 2, 1, "h"); R(36, 19, 4, 2, "i"); R(51, 15, 3, 2, "h")
  OX = 0
  R(12, 24, 4, 1, "p"); R(11, 25, 1, 1, "y")
  for k = 0, 2 do
    local t = ((f / 6) + k / 3) % 1
    local x = 12 - math.floor(t * 11) + math.floor(math.sin(t * 6 + k) * 1.5 + 0.5)
    local y = 24 - math.floor(t * 9)
    if t < 0.5 then R(x, y, 2, 2, "y") else R(x, y, 2, 1, "c"); P(x - 1, y + 1, "c") end
  end
  if f % 3 == 0 then P(14 + 60, 17, "W") end
end, nil, { soot = 0.16, mud = 5, streaks = 5, rust = 4, specks = 0.05 })

anim("Strasse_Lieferwagen_Blinker_Anim", 4, 64, 32, 250, function(f)
  EL(32, 30, 29, 1, "p")
  TB(10, 22, 44, 51, 44, 60, "B")
  TF(12, 18, 46, 50, 46, 57, "e"); L(48, 12, 46, 18, "f")
  RB(3, 5, 42, 17, "B"); R(4, 5, 40, 1, "C"); R(4, 21, 40, 1, "d")
  R(4, 11, 40, 2, "k"); R(4, 11, 40, 1, "j")
  L(24, 7, 26, 9, "Q"); L(26, 9, 28, 7, "Q"); L(28, 7, 30, 9, "Q"); L(30, 9, 33, 6, "Q"); L(23, 10, 34, 10, "Q"); P(35, 8, "C"); P(36, 7, "C"); P(35, 9, "C")
  R(8, 15, 7, 2, "W"); R(17, 15, 5, 2, "W"); R(24, 15, 9, 2, "W"); R(35, 15, 6, 2, "Q")
  P(30, 8, "d"); P(31, 8, "d"); P(31, 9, "d"); P(12, 8, "f")
  R(58, 20, 5, 3, "u"); R(58, 20, 5, 1, "y")
  L(8, 4, 8, 2, "u"); R(7, 1, 3, 1, "y")
  wheel(14, 24); wheel(52, 24)
  if f % 2 == 0 then
    R(60, 16, 3, 3, "Z"); P(61, 17, "Y")
    R(1, 16, 3, 3, "Z"); P(2, 17, "Y")
    for _, p in ipairs({ { 62, 14 }, { 63, 17 }, { 62, 20 }, { 0, 14 }, { 0, 20 } }) do P(p[1], p[2], "Z") end
    R(7, 2, 3, 1, "Z"); P(8, 0, "Y")
  else
    R(60, 16, 3, 3, "j"); R(1, 16, 3, 3, "j")
  end
end, nil, { soot = 0.16, mud = 5, streaks = 5, rust = 4, specks = 0.05 })

anim("Strasse_Wrack_Rauch_Anim", 6, 80, 32, 140, function(f)
  stamp(64, 32, function()
    OY = 2
    carA(false, "b", "c", "a")
    R(24, 8, 8, 1, "o"); L(25, 7, 29, 11, "W"); L(36, 8, 41, 10, "W")
    R(6, 16, 5, 2, "i"); R(8, 17, 3, 1, "h"); R(38, 18, 4, 2, "i"); R(52, 16, 3, 2, "h")
    OY = 0
  end, shearY(-0.06, 0), 0, 0)
  for _, bx in ipairs({ 9, 46 }) do
    local top = 25 - math.floor((bx + 5) * 0.06 + 0.5) + 2
    R(bx - 1, top - 1, 13, 32 - top, "o"); R(bx, top, 11, 30 - top, "R")
    for y = top, 29 do
      if (y - top) % 3 == 2 then R(bx, y, 11, 1, "a") end
      P(bx + (math.floor((y - top) / 3) % 2 == 0 and 5 or 2), y, "a")
    end
    R(bx, top, 11, 1, "Q"); P(bx + 2, top + 1, "Q")
  end
  for k = 0, 2 do
    local t = ((f / 6) + k / 3) % 1
    local x = 50 + math.floor(t * 12) + math.floor(math.sin(t * 5 + k * 2) * 2 + 0.5)
    local y = 13 - math.floor(t * 12)
    if t < 0.35 then R(x, y, 3, 2, "t"); P(x + 1, y - 1, "u")
    elseif t < 0.7 then R(x, y, 3, 3, "u"); P(x - 1, y + 1, "t"); P(x + 3, y, "c")
    else R(x, y, 2, 2, "c"); P(x + 3, y - 1, "c"); P(x - 2, y + 1, "b") end
  end
  if f == 2 then P(47, 11, "Y"); P(49, 10, "Z"); P(46, 12, "W") end
  if f == 3 then P(50, 11, "Z") end
end, nil, { soot = 0.16, mud = 5, streaks = 5, rust = 4, specks = 0.05 })

-------------------------------------------------- Liste fuer Unity
local lf = io.open(ANIM_DIR .. "_Liste_Strasse.txt", "w")
if lf then
  lf:write("Nightward Strasse & Schrott: animierte Streifen (horizontal, Frame = Breite/Frames)\n")
  lf:write("Name | Frames | Frame-Groesse | ms pro Frame\n\n")
  for _, l in ipairs(ANIM_LOG) do lf:write(l .. "\n") end
  lf:write("\n.aseprite je Streifen: 1 Layer, Tag Loop, Frame-Dauer wie oben. Quelle: _Quelle_Generator/strasse/*.lua\n")
  lf:close()
end
print("Animationen: " .. #ANIM_LOG)
