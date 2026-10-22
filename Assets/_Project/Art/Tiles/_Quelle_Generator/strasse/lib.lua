-- Nightward Strasse: gemeinsame Zeichen-Bibliothek (alles global, wird per dofile geladen)
pc = app.pixelColor
hex = { o="1a1526", p="2b2140", a="3d2e4a", b="4f3d5c", c="6b5a7a",
  d="1f2a3d", e="2c3e56", f="3f5570", m="e8e0f0",
  g="3b2a22", h="5c4033", i="7a5a43", j="9c7a5a", k="b89a72",
  l="1e3a2b", n="2f5a3c", q="4a7a4f", r="6e9a5e", s="9ab87a",
  t="4a4550", u="6e6a74", y="9a95a0",
  M="5e3d33", N="8c5f4d", S="d19a7a",
  R="7a2e3a", Q="c4636b", B="3a4a7a", C="6b7fb8",
  Y="ffd27a", Z="ffa550", F="e8733a", W="fff1c9",
  T="6fd3e6", H="a8f0ff", D="2b6b8a", X="f2ead8", E="d64a6a", K="8a1f3d" }
col = {}; rev = {}
for k, h in pairs(hex) do
  col[k] = pc.rgba(tonumber(h:sub(1,2),16), tonumber(h:sub(3,4),16), tonumber(h:sub(5,6),16), 255)
  rev[col[k]] = k
end
allowed = {}
for _, h in pairs(hex) do allowed[h] = true end

img, CW, CH, OX, OY = nil, 32, 32, 0, 0
sheet, spr = nil, nil
GRIME = nil

function newSheet(w, h) spr = Sprite(w, h); sheet = Image(w, h) end
function begin(w, h) img = Image(w or 32, h or 32); CW = w or 32; CH = h or 32; OX = 0; OY = 0 end
function P(x, y, c)
  x = x + OX; y = y + OY
  if c ~= "." and x >= 0 and y >= 0 and x < CW and y < CH then img:drawPixel(x, y, col[c]) end
end
function G(x, y)
  x = x + OX; y = y + OY
  if x < 0 or y < 0 or x >= CW or y >= CH then return nil end
  local px = img:getPixel(x, y)
  if pc.rgbaA(px) == 0 then return nil end
  return rev[px]
end
function R(x, y, w, h, c) for j = y, y + h - 1 do for i = x, x + w - 1 do P(i, j, c) end end end
function RB(x, y, w, h, c) R(x-1, y-1, w+2, h+2, "o"); R(x, y, w, h, c) end
function L(x1, y1, x2, y2, c)
  local dx, dy = math.abs(x2-x1), math.abs(y2-y1)
  local sx = x1 < x2 and 1 or -1
  local sy = y1 < y2 and 1 or -1
  local err = dx - dy
  while true do
    P(x1, y1, c)
    if x1 == x2 and y1 == y2 then break end
    local e2 = 2 * err
    if e2 > -dy then err = err - dy; x1 = x1 + sx end
    if e2 < dx then err = err + dx; y1 = y1 + sy end
  end
end
function EL(cx, cy, rx, ry, c)
  for y = -ry, ry do for x = -rx, rx do
    if (x*x)/(rx*rx) + (y*y)/(ry*ry) <= 1.0 then P(cx+x, cy+y, c) end
  end end
end
function EB(cx, cy, rx, ry, c) EL(cx, cy, rx+1, ry+1, "o"); EL(cx, cy, rx, ry, c) end
function RING(cx, cy, r, c, ry)
  ry = ry or r
  for a = 0, 95 do local an = a / 96 * math.pi * 2
    P(math.floor(cx + math.cos(an) * r + 0.5), math.floor(cy + math.sin(an) * ry + 0.5), c) end
end
function A(x, y, rows, flip)
  local mw = 0
  for _, r in ipairs(rows) do if #r > mw then mw = #r end end
  for j, r in ipairs(rows) do
    for i = 1, #r do
      local ch = r:sub(i, i)
      if ch ~= "." then P(flip and (x + mw - i) or (x + i - 1), y + j - 1, ch) end
    end
  end
end
function lerp(a, b, t) return math.floor(a + (b - a) * t + 0.5) end
function SP(spans, c)
  for _, s in ipairs(spans) do
    for yy = s[1]-1, s[1]+1 do for x = s[2]-1, s[3]+1 do P(x, yy, "o") end end
  end
  for _, s in ipairs(spans) do for x = s[2], s[3] do P(x, s[1], c) end end
end
function TS(y0, y1, xl0, xr0, xl1, xr1)
  local sp = {}
  for y = y0, y1 do
    local t = (y1 == y0) and 0 or (y - y0) / (y1 - y0)
    sp[#sp+1] = { y, lerp(xl0, xl1, t), lerp(xr0, xr1, t) }
  end
  return sp
end
function TB(y0, y1, xl0, xr0, xl1, xr1, c) SP(TS(y0, y1, xl0, xr0, xl1, xr1), c) end
function TF(y0, y1, xl0, xr0, xl1, xr1, c)
  for _, s in ipairs(TS(y0, y1, xl0, xr0, xl1, xr1)) do for x = s[2], s[3] do P(x, s[1], c) end end
end
function TR(x, y, w, h, k, c)
  for i = 0, w - 1 do
    local yo = math.floor(i * k + 0.5)
    for j = -1, h do
      local cc = (j == -1 or j == h or i == 0 or i == w - 1) and "o" or c
      P(x + i, y + yo + j, cc)
    end
  end
end
function stamp(w, h, fn, tf, dx, dy)
  local si, sw, sh, sox, soy = img, CW, CH, OX, OY
  img = Image(w, h); CW = w; CH = h; OX = 0; OY = 0
  fn()
  local t = img
  img, CW, CH, OX, OY = si, sw, sh, sox, soy
  for y = 0, h - 1 do for x = 0, w - 1 do
    local px = t:getPixel(x, y)
    if pc.rgbaA(px) > 0 then
      local X, Y = x, y
      if tf then X, Y = tf(x, y) end
      X = dx + X + OX; Y = dy + Y + OY
      if X >= 0 and Y >= 0 and X < CW and Y < CH then img:drawPixel(X, Y, px) end
    end
  end end
end
function shearX(k, y0) return function(x, y) return x + math.floor((y0 - y) * k + 0.5), y end end
function shearY(k, x0) return function(x, y) return x, y + math.floor((x - x0) * k + 0.5) end end
function fleck(n, c) for i = 1, n do P(math.random(0,CW-1), math.random(0,CH-1), c) end end
function grain(n, c) for i = 1, n do local x, y = math.random(0,CW-2), math.random(0,CH-1); P(x, y, c); P(x+1, y, c) end end
function blob(cx, cy, rx, ry, c, jit)
  for y = -ry - 1, ry + 1 do for x = -rx - 1, rx + 1 do
    local d = (x*x)/((rx+0.5)*(rx+0.5)) + (y*y)/((ry+0.5)*(ry+0.5))
    if d + (math.random() - 0.5) * (jit or 0.5) <= 1.0 then P(cx + x, cy + y, c) end
  end end
end

-------------------------------------------------- Schmutz-Pass
local dkmap = { R="M", Q="R", B="d", C="B", y="u", u="t", t="a", W="y", X="y", i="h", j="i", k="j", h="g",
  e="d", f="e", b="a", c="b", q="n", n="l", r="q", s="r", S="N", N="M", m="y", l="p", g="p" }
local prot = { o=1, p=1, Y=1, Z=1, F=1, E=1, T=1, H=1, D=1, K=1 }
local mudc = { "g", "h", "g", "M", "a", "g" }
local metal = { u=1, t=1, y=1, c=1 }
function grime(o)
  if not o then return end
  local w, h = CW, CH
  local minY, maxY, minX, maxX = h, -1, w, -1
  for y = 0, h - 1 do for x = 0, w - 1 do
    if pc.rgbaA(img:getPixel(x, y)) > 0 then
      if y < minY then minY = y end; if y > maxY then maxY = y end
      if x < minX then minX = x end; if x > maxX then maxX = x end
    end
  end end
  if maxY < 0 then return end
  local function get(x, y)
    if x < 0 or y < 0 or x >= w or y >= h then return nil end
    local px = img:getPixel(x, y)
    if pc.rgbaA(px) == 0 then return nil end
    return rev[px]
  end
  local function set(x, y, c) img:drawPixel(x, y, col[c]) end
  local span = math.max(maxY - minY, 1)
  -- Russ / Alterung, unten staerker
  for y = minY, maxY do for x = minX, maxX do
    local c = get(x, y)
    if c and not prot[c] and dkmap[c] then
      local t = (y - minY) / span
      if math.random() < (o.soot or 0.10) * (0.3 + t * 1.7) then set(x, y, dkmap[c]) end
    end
  end end
  -- Matsch am Boden
  local mud = o.mud or 4
  local pr = { 0.85, 0.6, 0.4, 0.2, 0.1 }
  for d = 0, mud - 1 do
    local y = maxY - d
    for x = minX, maxX do
      local c = get(x, y)
      if c and c ~= "o" and c ~= "p" and not prot[c] and math.random() < (pr[d + 1] or 0.1) then
        set(x, y, mudc[math.random(1, #mudc)])
      end
    end
  end
  -- Regenschlieren von oben
  for i = 1, (o.streaks or 3) do
    local x = math.random(minX + 1, math.max(maxX - 1, minX + 1))
    local y = minY
    while y <= maxY do
      local c = get(x, y)
      if c and c ~= "o" and c ~= "p" and not prot[c] and (get(x, y - 1) == nil or get(x, y - 1) == "o" or get(x, y - 1) == "p") then break end
      y = y + 1
    end
    local len = math.random(3, 9)
    for k = 0, len do
      local c = get(x, y + k)
      if not c or c == "o" or c == "p" or prot[c] then break end
      set(x, y + k, o.streakc or dkmap[c] or c)
    end
  end
  -- Rost auf Metall
  for i = 1, (o.rust or 2) do
    for tries = 1, 12 do
      local x, y = math.random(minX, maxX), math.random(minY, maxY)
      local c = get(x, y)
      if c and metal[c] then
        set(x, y, "i")
        if get(x + 1, y) and metal[get(x + 1, y)] then set(x + 1, y, "h") end
        if get(x, y + 1) and metal[get(x, y + 1)] then set(x, y + 1, "h") end
        if math.random() < 0.5 and get(x - 1, y) and metal[get(x - 1, y)] then set(x - 1, y, "j") end
        break
      end
    end
  end
  -- Moos in den unteren Ecken
  for i = 1, (o.moss or 0) do
    local x = math.random(minX, maxX)
    local y = maxY - math.random(1, 6)
    local c = get(x, y)
    if c and c ~= "o" and c ~= "p" and not prot[c] then set(x, y, math.random() < 0.5 and "n" or "q") end
  end
  -- Dreckspritzer
  local sp = o.specks or 0.03
  for y = minY, maxY do for x = minX, maxX do
    local c = get(x, y)
    if c and c ~= "o" and c ~= "p" and not prot[c] and math.random() < sp then
      set(x, y, math.random() < 0.6 and "g" or "a")
    end
  end end
end

function put(cx, cy, tf, gr)
  if gr ~= false then grime(gr or GRIME) end
  for y = 0, CH - 1 do for x = 0, CW - 1 do
    local px = img:getPixel(x, y)
    if pc.rgbaA(px) > 0 then
      local X, Y = x, y
      if tf then X, Y = tf(x, y) end
      if X >= 0 and Y >= 0 and X < CW and Y < CH then sheet:drawPixel(cx*32 + X, cy*32 + Y, px) end
    end
  end end
end

-- Einzelbild fuer Animationen: Schmutz (feste Saat) + Transformation, liefert neues Image
function bake(tf, gr, seed)
  if gr then math.randomseed(seed or 5); grime(gr) end
  local out = Image(CW, CH)
  for y = 0, CH - 1 do for x = 0, CW - 1 do
    local px = img:getPixel(x, y)
    if pc.rgbaA(px) > 0 then
      local X, Y = x, y
      if tf then X, Y = tf(x, y) end
      if X >= 0 and Y >= 0 and X < CW and Y < CH then out:drawPixel(X, Y, px) end
    end
  end end
  return out
end

function badPixels(im)
  local bad = 0
  for y = 0, im.height - 1 do for x = 0, im.width - 1 do
    local px = im:getPixel(x, y)
    local a = pc.rgbaA(px)
    if a ~= 0 then
      local hx = string.format("%02x%02x%02x", pc.rgbaR(px), pc.rgbaG(px), pc.rgbaB(px))
      if a ~= 255 or not allowed[hx] then bad = bad + 1 end
    end
  end end
  return bad
end

ANIM_DIR = "F:/!!!_GAMES/NIGHTWARD/Nightward/Assets/_Project/Art/Tiles/Animiert/"
ANIM_LOG = {}
function saveAnim(name, frames, w, h, ms)
  local n = #frames
  local s = Sprite(w, h)
  local lay = s.layers[1]
  lay.name = "Anim"
  local strip = Image(w * n, h)
  for i = 1, n do
    if i > 1 then s:newFrame() end
    local cel = lay:cel(i)
    if cel then cel.image = frames[i] else s:newCel(lay, i, frames[i], Point(0, 0)) end
    s.frames[i].duration = ms / 1000
    strip:drawImage(frames[i], Point((i - 1) * w, 0))
  end
  local tag = s:newTag(1, n); tag.name = "Loop"
  local bad = 0
  for i = 1, n do bad = bad + badPixels(frames[i]) end
  s:saveAs(ANIM_DIR .. name .. ".aseprite")
  local out = Sprite(w * n, h)
  out.layers[1].name = "Strip"
  local oc = out.layers[1]:cel(1)
  if oc then oc.image = strip else out:newCel(out.layers[1], 1, strip, Point(0, 0)) end
  out:saveAs(ANIM_DIR .. name .. ".png")
  out:close(); s:close()
  ANIM_LOG[#ANIM_LOG + 1] = string.format("%s | %d | %dx%d | %d", name, n, w, h, ms)
  if bad > 0 then print("UNGUELTIG " .. name .. ": " .. bad) end
end
