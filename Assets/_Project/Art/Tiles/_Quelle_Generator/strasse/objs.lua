-- Objekte, die statisch UND animiert gebraucht werden: Parameter f = Frame (0-basiert)

function TL(pts, c, w)   -- dicke Linie durch Punkte
  w = w or 2
  for i = 1, #pts - 1 do
    local x1, y1, x2, y2 = pts[i][1], pts[i][2], pts[i+1][1], pts[i+1][2]
    local dx, dy = math.abs(x2-x1), math.abs(y2-y1)
    local sx = x1 < x2 and 1 or -1
    local sy = y1 < y2 and 1 or -1
    local err = dx - dy
    while true do
      R(x1, y1, w, w, c)
      if x1 == x2 and y1 == y2 then break end
      local e2 = 2 * err
      if e2 > -dy then err = err - dy; x1 = x1 + sx end
      if e2 < dx then err = err + dx; y1 = y1 + sy end
    end
  end
end
function TLB(pts, c, w)  -- mit Outline
  w = w or 2
  for _, p in ipairs(pts) do end
  local o = {}
  TL(pts, "o", w + 2)
  -- Outline-Pass hat um 1 versetzt gezeichnet: Mitte zurueckholen
  local sh = {}
  for i, p in ipairs(pts) do sh[i] = { p[1] + 1, p[2] + 1 } end
  TL(sh, c, w)
end

---------------------------------------------------------------- Katze
function drawCat(f)
  begin()
  EL(16, 30, 11, 1, "p")
  local tx = ({0, 1, 2, 2, 1, 0, -1, -1})[(f % 8) + 1]
  local ty = ({0, 0, -1, -2, -1, 0, 0, 0})[(f % 8) + 1]
  local tail = { {21, 27}, {25, 28}, {27 + tx // 2, 25}, {27 + tx, 21 + ty} }
  TL(tail, "o", 4)
  for i = 1, #tail do tail[i] = { tail[i][1] + 1, tail[i][2] + 1 } end
  TL(tail, "a", 2)
  EB(16, 25, 6, 5, "a")
  EB(16, 20, 4, 5, "a")
  R(12, 28, 3, 2, "b"); R(17, 28, 3, 2, "b"); P(12, 29, "o"); P(19, 29, "o")
  EB(16, 12, 6, 5, "a")
  local ear = (f % 8 == 3) and 1 or 0
  SP({ { 5 + ear, 11, 11 }, { 6 + ear, 10, 12 }, { 7 + ear, 10, 13 } }, "a")
  SP({ { 5, 20, 20 }, { 6, 19, 21 }, { 7, 18, 21 } }, "a")
  P(11, 6 + ear, "Q"); P(20, 6, "Q")
  if f % 8 == 5 or f % 8 == 6 then
    R(13, 12, 3, 1, "o"); R(17, 12, 3, 1, "o")
  else
    R(13, 11, 3, 2, "Y"); R(17, 11, 3, 2, "Y"); P(14, 11, "p"); P(14, 12, "p"); P(18, 11, "p"); P(18, 12, "p")
  end
  P(16, 14, "Q"); L(8, 14, 11, 13, "c"); L(8, 15, 11, 15, "c"); L(21, 13, 24, 14, "c"); L(21, 15, 24, 15, "c")
  P(19, 8, "b"); P(20, 9, "b"); P(21, 12, "b"); P(20, 22, "b"); P(21, 25, "b"); P(20, 28, "b")
  P(14, 17, "Q"); P(15, 17, "Q"); P(16, 17, "Q"); P(17, 17, "Q")   -- Halsband
  P(16, 18, "Y")
end

---------------------------------------------------------------- Ratte
function drawRat(f)
  begin()
  EL(15, 29, 11, 1, "p")
  local k = f % 4
  local tw = ({0, 1, 0, -1})[k + 1]
  -- Schwanz
  L(9, 26, 6, 26 + tw, "Q"); L(6, 26 + tw, 3, 25 - tw, "Q"); P(2, 25 - tw, "Q")
  -- Beine
  local a = (k % 2 == 0) and 0 or 1
  R(11 + a, 27, 2, 2, "t"); R(15 - a, 27, 2, 2, "t"); R(19 + a, 27, 2, 2, "t"); R(8 - a, 27, 2, 2, "t")
  EB(14, 25, 6, 3, "u")
  EB(21, 24, 3, 2, "u"); P(24, 25, "Q"); P(25, 25, "o")
  P(21, 21, "u"); P(22, 21, "u"); P(21, 22, "Q"); P(23, 23, "W")
  R(10, 22, 8, 1, "y"); P(19, 23, "y"); P(12, 27, "g")
  L(23, 26, 26, 27, "c"); L(23, 27, 26, 28, "c")
end

---------------------------------------------------------------- Taube
function drawPigeon(f)
  begin()
  EL(15, 30, 9, 1, "p")
  local k = f % 4
  local hx = ({22, 23, 24, 23})[k + 1]
  local hy = ({15, 19, 24, 19})[k + 1]
  -- Beine
  L(14, 27, 13, 29, "Q"); L(17, 27, 18, 29, "Q"); R(12, 29, 3, 1, "Q"); R(17, 29, 3, 1, "Q")
  -- Schwanz
  TB(24, 29, 5, 8, 2, 6, "c")
  EB(15, 22, 7, 5, "u")
  R(9, 20, 8, 3, "y"); R(10, 24, 6, 1, "t"); L(9, 22, 14, 25, "c"); L(10, 21, 14, 23, "t")
  -- Hals + Kopf
  TL({ { 19, 19 }, { hx - 1, hy + 2 } }, "o", 5)
  TL({ { 20, 20 }, { hx, hy + 2 } }, "u", 3)
  P(21, 19, "C"); P(22, 19, "C"); P(21, 20, "C"); P(20, 21, "B")
  EB(hx, hy, 3, 3, "u")
  P(hx + 1, hy - 1, "Z"); P(hx + 1, hy - 2, "Z")
  L(hx + 3, hy, hx + 5, hy + 1, "k"); P(hx + 6, hy + 1, "j")
  P(hx - 1, hy - 2, "y"); P(hx, hy - 2, "y")
end

---------------------------------------------------------------- Boombox
function drawBoombox(f)
  begin()
  EL(16, 30, 14, 1, "p")
  L(25, 12, 29, 3, "y"); P(29, 2, "Y")
  R(9, 8, 14, 1, "u"); R(9, 8, 1, 5, "u"); R(22, 8, 1, 5, "u")
  RB(3, 12, 26, 14, "t"); R(3, 12, 26, 1, "y"); R(3, 13, 1, 12, "u"); R(28, 13, 1, 12, "c")
  local big = (f % 2 == 0) and 3 or 2
  for _, cx in ipairs({ 8, 23 }) do
    EL(cx, 19, 4, 4, "p"); EL(cx, 19, big, big, "u"); EL(cx, 19, 1, 1, "y")
    if big == 3 then RING(cx, 19, 4, "c") end
  end
  RB(12, 14, 8, 5, "e"); R(12, 14, 8, 1, "f")
  local r = (f % 4 < 2) and 0 or 1
  P(14 + r, 17, "W"); P(17 - r, 17, "W"); P(15, 16, "y"); P(16, 16, "y")
  R(12, 21, 8, 1, "y"); P(13, 21, "Q"); P(18, 22, "Y"); P(14, 23, "Q"); P(16, 23, "Z"); P(18, 23, "Q")
  R(5, 12, 2, 1, "Q")
  -- Noten
  local n = f % 4
  local nx = ({ 6, 8, 11, 13 })[n + 1]
  local ny = ({ 8, 6, 4, 2 })[n + 1]
  P(nx, ny, "Y"); P(nx, ny - 1, "Y"); P(nx, ny - 2, "Y"); P(nx + 1, ny - 2, "Y"); P(nx - 1, ny, "Y")
  local mx = ({ 26, 24, 22, 20 })[n + 1]
  local my = ({ 6, 4, 3, 1 })[n + 1]
  P(mx, my, "W"); P(mx, my - 1, "W"); P(mx + 1, my - 1, "W")
end

---------------------------------------------------------------- Grablicht
function drawGrablicht(f)
  begin()
  EL(16, 30, 12, 1, "p")
  RB(5, 25, 22, 4, "u"); R(5, 25, 22, 1, "y"); R(5, 28, 22, 1, "t")
  -- verwelkte Blumen
  L(8, 24, 7, 17, "n"); L(11, 24, 12, 15, "n"); L(14, 24, 10, 19, "l")
  RB(5, 14, 3, 3, "M"); P(6, 15, "g"); RB(11, 12, 3, 3, "Q"); P(12, 13, "R"); RB(8, 17, 2, 2, "k")
  P(9, 22, "M"); P(6, 23, "M"); P(13, 23, "k")
  -- Glas mit Kerze
  RB(16, 15, 7, 10, "R"); R(17, 16, 1, 8, "Q"); R(22, 16, 1, 8, "K")
  R(18, 18, 3, 6, "Y"); R(18, 18, 3, 1, "W")
  R(18, 24, 3, 1, "Z")
  RB(24, 20, 3, 5, "W"); R(24, 20, 3, 1, "X"); P(25, 22, "j")   -- abgebrannte Kerze
  local fl = f % 4
  P(19, 14, "Z")
  if fl == 0 then P(19, 13, "Y"); P(19, 12, "W")
  elseif fl == 1 then P(19, 13, "Y"); P(20, 12, "Y"); P(19, 12, "W")
  elseif fl == 2 then P(19, 13, "Y"); P(19, 12, "Y"); P(19, 11, "W"); P(18, 12, "Z")
  else P(19, 13, "Y"); P(18, 12, "Y"); P(19, 12, "W") end
  P(14, 11, "Z"); P(24, 13, "Z")
end

---------------------------------------------------------------- Kaugummiautomat
function drawKaugummi(f)
  begin()
  EL(16, 30, 9, 1, "p")
  RB(11, 27, 10, 2, "u"); RB(14, 22, 4, 6, "t"); R(14, 22, 1, 6, "y")
  RB(10, 15, 12, 8, "R"); R(10, 15, 12, 1, "Q"); R(10, 16, 2, 6, "a"); R(21, 16, 1, 6, "Q")
  RB(14, 17, 4, 4, "u"); R(15, 18, 2, 2, "y"); R(15, 18, 2, 1, "t")
  R(13, 22, 6, 1, "p"); P(11, 17, "Y"); P(11, 19, "Y")
  EB(16, 8, 7, 7, "e")
  EL(16, 8, 6, 6, "d")
  local balls = { {13,5,"Q"}, {17,4,"Y"}, {15,8,"C"}, {19,7,"s"}, {12,9,"Z"}, {17,11,"Q"}, {14,12,"Y"}, {20,10,"C"}, {16,6,"s"}, {18,13,"Z"} }
  for _, b in ipairs(balls) do R(b[1], b[2], 2, 2, b[3]); P(b[1], b[2], "W") end
  RING(16, 8, 6, "f")
  local g = f % 4
  local gx = ({ 12, 14, 18, 20 })[g + 1]
  local gy = ({ 4, 2, 2, 4 })[g + 1]
  P(gx, gy, "W"); P(gx + 1, gy + 1, "W"); P(gx, gy + 1, "m")
  RB(13, 0, 6, 2, "t")
end

---------------------------------------------------------------- Neonschild "BAR"
local NL = {
  B = { "####.", "#...#", "#...#", "####.", "#...#", "#...#", "####." },
  A = { ".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#" },
  R = { "####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#" } }
local NF = { {1,1,1}, {1,1,1}, {1,0,1}, {1,1,1}, {0,1,0}, {1,1,1}, {1,1,1}, {0,1,1} }
function drawNeon(f)
  begin()
  local fl = NF[(f % 8) + 1]
  L(0, 6, 7, 6, "u"); L(0, 7, 7, 7, "t"); P(2, 8, "y"); P(5, 8, "y")
  RB(6, 8, 24, 16, "p"); R(6, 8, 24, 1, "a"); R(6, 23, 24, 1, "a")
  L(8, 8, 8, 3, "u"); L(28, 8, 28, 3, "u"); R(7, 2, 3, 1, "y"); R(27, 2, 3, 1, "y")
  for i, ch in ipairs({ "B", "A", "R" }) do
    local x0 = 8 + (i - 1) * 7
    for j, row in ipairs(NL[ch]) do
      for k = 1, #row do
        if row:sub(k, k) == "#" then
          if fl[i] == 1 then
            P(x0 + k - 1, 11 + j - 1, "Q")
            if (j == 4) then P(x0 + k - 1, 11 + j - 1, "W") end
          else
            P(x0 + k - 1, 11 + j - 1, "b")
          end
        end
      end
    end
    if fl[i] == 1 then P(x0 - 1, 10, "R"); P(x0 + 5, 18, "R") end
  end
  if f % 8 == 4 then P(11, 20, "W"); P(12, 21, "Y") end
  P(31 - 1, 25, "g"); P(29, 26, "g"); P(8, 25, "g")
end

---------------------------------------------------------------- Fahne
function drawFlag(f)
  begin(32, 64)
  EL(8, 61, 8, 2, "p")
  RB(6, 6, 2, 54, "y"); R(6, 6, 1, 54, "u"); R(7, 6, 1, 54, "W")
  EB(7, 3, 2, 2, "Y")
  RB(4, 59, 6, 2, "t")
  for i = 0, 19 do
    local yo = math.floor(math.sin(i * 0.45 - f * 1.05) * (0.8 + i * 0.1) + 0.5) + math.floor(i * 0.15)
    for j = 0, 13 do
      local gone = (i >= 15 and ((i * 7 + j * 3) % 5 == 0)) or (i >= 17 and j > 9 and (i + j) % 2 == 0)
      if not gone then
        local c = (j >= 5 and j <= 8) and "Q" or "R"
        if (i * 3 + j * 5) % 11 == 0 then c = "a" end
        if (i + j * 2) % 13 == 0 then c = "M" end
        P(8 + i, 8 + yo + j, c)
      end
    end
    P(8 + i, 7 + yo, "o"); P(8 + i, 22 + yo, "o")
  end
  P(8, 8, "o")
  L(5, 62, 5, 62, "o")
end

---------------------------------------------------------------- Bushaltestelle
function drawBushalt(f)
  begin(32, 64)
  EL(14, 61, 15, 2, "p")
  RB(27, 10, 2, 50, "u"); R(27, 10, 1, 50, "t"); R(28, 10, 1, 50, "y")
  EB(28, 5, 4, 4, "Y"); R(26, 3, 1, 5, "n"); R(30, 3, 1, 5, "n"); R(26, 5, 5, 1, "n"); P(26, 8, "k"); P(30, 2, "k")
  RB(1, 10, 24, 4, "t"); R(1, 10, 24, 1, "u"); P(6, 9, "i"); P(7, 9, "j"); P(7, 8, "i"); P(18, 9, "i")
  R(4, 14, 17, 34, "e")
  L(7, 14, 4, 22, "f"); L(10, 14, 4, 26, "f"); L(17, 14, 12, 22, "f")
  L(14, 33, 17, 40, "W"); L(17, 40, 13, 46, "W"); L(16, 36, 19, 37, "W")
  local pal = { "Q", "C", "Z", "W" }
  RB(8, 17, 10, 24, "Y")
  R(9, 18, 8, 6, pal[(f % 4) + 1]); R(9, 25, 8, 8, pal[((f + 1) % 4) + 1]); R(9, 34, 8, 5, pal[((f + 2) % 4) + 1])
  R(10, 20, 4, 1, "W"); R(10, 27, 6, 1, "p"); R(10, 29, 5, 1, "p"); R(10, 36, 3, 1, "W")
  RB(2, 14, 2, 46, "u"); RB(21, 14, 2, 46, "u")
  RB(5, 46, 16, 3, "i"); R(5, 46, 16, 1, "j"); R(9, 47, 1, 2, "g")
  RB(6, 49, 2, 10, "u"); RB(18, 49, 2, 10, "u")
  L(5, 40, 9, 42, "Q"); L(9, 42, 7, 44, "Q"); P(5, 44, "Q")
  R(11, 58, 2, 1, "X"); P(14, 59, "k"); R(21, 58, 2, 2, "n")
end

---------------------------------------------------------------- Gartenzwerg
function drawZwerg(f)
  begin()
  EL(16, 30, 7, 1, "p")
  A(9, 6, {
   "......oo......", ".....oQQo.....", "....oQQQQo....", "....oQQQQRo...",
   "...oQQQQQRRo..", "..oQQQQQQRRRo.", "..oRRRRRRRRRo.", "..oWWSSSSWWo..",
   "..oWSSSSSSSWo.", "..oWWSNNSWWo..", "..oWWWWWWWWo..", "...oWWWWWWo...",
   "...oBBBBBBo...", "..oBBCCBBBBo..", "..oBBBBBBBBo..", ".oNoBBBBBBoNo.",
   "..oBBBBBBBBo..", "..oggoooogo...", "..ogo....ogo.." })
  local k = f % 6
  local dx = ({ 0, -1, -1, 0, 1, 0 })[k + 1]
  if k == 5 then
    P(14, 14, "N"); P(17, 14, "N"); P(13, 14, "M"); P(14, 14, "M"); P(16, 14, "M"); P(17, 14, "M")
  else
    P(14 + dx, 14, "p"); P(17 + dx, 14, "p")
  end
  P(21, 14, "W"); P(22, 15, "W")
  if k == 2 or k == 3 then P(10, 8, "Q") end
end
