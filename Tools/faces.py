"""Gesichts-Bereinigung der Stand-Posen (Style-Bibel: saubere Pixel, keine einzelnen Rauschpixel, Augen klein und klar).

clean_stand(stand, key) -> bereinigte Stand-Pixelmatrix (8 Rahmen a 56 px nebeneinander).
Schritte pro Kopf:
  1. Rauschpixel: einzelne Farbpixel ohne gleichfarbigen Nachbarn nehmen die Nachbarfarbe an (Outline-Farben bleiben)
  2. Augen: isolierte 2x2-Bloecke in Outline dunkel werden zu 1x2 (innere Spalte bleibt), Rest wird Hautfarbe
"""
import numpy as np

OUTLINE = {(0x1a, 0x15, 0x26), (0x2b, 0x21, 0x40)}
# Monsterfarben und Glanzpunkte duerfen als Einzelpixel stehen (Augen, Zaehne)
KEEP = {(0xd6, 0x4a, 0x6a), (0xf2, 0xea, 0xd8), (0xff, 0xf1, 0xc9)}
SKIN = (0xd1, 0x9a, 0x7a)
SKIN_SHADOW = (0x5e, 0x3d, 0x33)
EYE = (0x1a, 0x15, 0x26)
CELL = 56


def _rgb(px):
    return tuple(int(v) for v in px[:3])


def _neighbors4(img, y, x):
    h, w = img.shape[:2]
    for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        ny, nx = y + dy, x + dx
        if 0 <= ny < h and 0 <= nx < w and img[ny, nx, 3] > 0:
            yield img[ny, nx]


def denoise(cell, y0, y1):
    out = cell.copy()
    for y in range(y0, y1):
        for x in range(CELL):
            if cell[y, x, 3] == 0 or _rgb(cell[y, x]) in OUTLINE or _rgb(cell[y, x]) in KEEP:
                continue
            c = _rgb(cell[y, x])
            nb = [_rgb(n) for n in _neighbors4(cell, y, x)]
            if len(nb) < 3 or any(n == c for n in nb):
                continue
            cand = [n for n in nb if n not in OUTLINE]
            if not cand:
                continue
            out[y, x, :3] = max(set(cand), key=cand.count)
    return out


def slim_eyes(cell, y0, y1):
    """Isolierte 2x2-Augenbloecke -> 1x2 (innere Spalte zur Gesichtsmitte)."""
    out = cell.copy()
    xs = np.where(cell[:, :, 3].any(axis=0))[0]
    mid = (xs.min() + xs.max()) / 2.0
    for y in range(y0, y1 - 1):
        for x in range(1, CELL - 2):
            blk = [(y, x), (y, x + 1), (y + 1, x), (y + 1, x + 1)]
            if not all(_rgb(cell[p]) == EYE and cell[p][3] > 0 for p in blk):
                continue
            ring = [(y + dy, x + dx) for dy in range(-1, 3) for dx in range(-1, 3) if (dy, dx) not in ((0, 0), (0, 1), (1, 0), (1, 1))]
            if any(0 <= py < CELL and 0 <= px < CELL and cell[py, px, 3] > 0 and _rgb(cell[py, px]) == EYE for py, px in ring):
                continue  # haengt an der Outline: kein Auge
            inner_right = (x + 0.5) < mid  # linkes Auge: rechte Spalte ist innen
            drop = x if inner_right else x + 1
            skin = cell[y, x - 1] if inner_right else cell[y, x + 2]
            if skin[3] == 0:
                continue
            for yy in (y, y + 1):
                out[yy, drop] = skin
    return out


def _put(cell, row, idx, color):
    cell[row, 14 + idx, :3] = color
    cell[row, 14 + idx, 3] = 255


# Handgesetzte Korrekturen (Zeile, Spalte relativ zu x=14 im Rahmen), nur Vorderansicht S.
def _patch_gast(cell):
    # Die Verkleidung hat in der Frontansicht keine Augen: zwei klare Punkte, schmaler Mund
    _put(cell, 14, 11, EYE)
    _put(cell, 14, 16, EYE)
    _put(cell, 15, 13, SKIN_SHADOW)
    _put(cell, 15, 14, SKIN_SHADOW)


def _patch_hausfrau(cell):
    # Augenschlitze 2x1 -> 1x2
    for idx in (12, 15):
        _put(cell, 16, idx, EYE)
        _put(cell, 17, idx, EYE)
    _put(cell, 17, 11, SKIN)
    _put(cell, 17, 16, SKIN)


PATCHES = {'gast': _patch_gast, 'hausfrau': _patch_hausfrau}


def _head_box(cell):
    ys = np.where(cell[:, :, 3].any(axis=1))[0]
    top, bottom = int(ys.min()), int(ys.max())
    neck = int(top + (bottom - top) * 0.36)
    xs = np.where(cell[top:neck, :, 3].any(axis=0))[0]
    return top, neck, int(xs.min()), int(xs.max())


def _swap_head(body_cell, head_cell):
    """Kopfzone von body_cell durch die von head_cell ersetzen (oben buendig, horizontal an der Kopfmitte ausgerichtet)."""
    out = body_cell.copy()
    bt, bn, bx0, bx1 = _head_box(body_cell)
    ht, hn, hx0, hx1 = _head_box(head_cell)
    out[bt:bn] = 0
    head = head_cell[ht:hn]
    dx = int(round(((bx0 + bx1) - (hx0 + hx1)) / 2.0))
    ys, xs = np.where(head[:, :, 3] > 0)
    for y, x in zip(ys, xs):
        ty, tx = bt + y, x + dx
        if 0 <= tx < CELL and bt <= ty < bn:
            out[ty, tx] = head[y, x]
    return out


def clean_stand(stand, key):
    out = stand.copy()
    for r in range(8):
        cell = out[0:CELL, r * CELL:(r + 1) * CELL]
        ys = np.where(cell[:, :, 3].any(axis=1))[0]
        top, bottom = int(ys.min()), int(ys.max())
        neck = int(top + (bottom - top) * 0.36)
        cell = denoise(cell, top, neck)
        cell = slim_eyes(cell, top, neck)
        if r == 0 and key in PATCHES:
            PATCHES[key](cell)
        out[0:CELL, r * CELL:(r + 1) * CELL] = cell
    # E und SE: Original-Koerper behalten (Haendigkeit: Geschirrtuch, Werkzeug, Tablett bleiben am richtigen Arm),
    # aber den verdeckten Kopf durch den gespiegelten West-Kopf ersetzen. NE (Rueckansicht, kein Gesicht) bleibt Original.
    for east, west in ((6, 2), (7, 1)):
        out[0:CELL, east * CELL:(east + 1) * CELL] = _swap_head(
            out[0:CELL, east * CELL:(east + 1) * CELL], out[0:CELL, west * CELL:(west + 1) * CELL][:, ::-1])
    return out
