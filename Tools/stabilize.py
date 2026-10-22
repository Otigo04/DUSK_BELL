"""Stabilisiert 8-Richtungs-Sheets: Kopf/Oberkoerper aus der Stand-Pose (Anker), Bewegung aus dem Sheet.
Rahmen 56x56, Zeilen = 8 Richtungen. Nicht-destruktiv: schreibt <name>_fixed.png neben die Originale."""
import sys
import numpy as np
from PIL import Image

CELL = 56

def figure_rows(stand_cell):
    a = stand_cell[:, :, 3] > 0
    ys = np.where(a.any(axis=1))[0]
    return ys.min(), ys.max()

def best_dy(frame, anchor, top, split, maxdy=3):
    """Vertikale Verschiebung des Rahmens gegenueber dem Anker, gemessen an der Kopfzone (ohne Arme: mittlere Spalten)."""
    head = anchor[top:top + 12, 14:42]
    best = (10**9, 0)
    for dy in range(0, maxdy + 1):
        seg = frame[top + dy:top + dy + 12, 14:42]
        d = int((seg != head).any(axis=2).sum())
        if d < best[0]: best = (d, dy)
    return best[1]

def drop_orphans(rgba, min_area=8):
    """Entfernt kleine abgetrennte Pixelreste (z. B. Haendchen-Spitzen aus dem Original-Frame)."""
    a = rgba[:, :, 3] > 0
    seen = np.zeros_like(a)
    h, w = a.shape
    for y in range(h):
        for x in range(w):
            if not a[y, x] or seen[y, x]: continue
            stack, comp = [(y, x)], []
            seen[y, x] = True
            while stack:
                cy, cx = stack.pop(); comp.append((cy, cx))
                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1):
                        ny, nx = cy + dy, cx + dx
                        if 0 <= ny < h and 0 <= nx < w and a[ny, nx] and not seen[ny, nx]:
                            seen[ny, nx] = True; stack.append((ny, nx))
            if len(comp) < min_area:
                for cy, cx in comp: rgba[cy, cx] = 0
    return rgba

def stabilize(stand_path, sheet_path, out_path, split_frac=0.72):
    stand = np.array(Image.open(stand_path).convert('RGBA'))
    sheet = np.array(Image.open(sheet_path).convert('RGBA'))
    cols = sheet.shape[1] // CELL
    out = np.zeros_like(sheet)
    for r in range(8):
        anchor = stand[0:CELL, r * CELL:(r + 1) * CELL]
        top, bottom = figure_rows(anchor)
        split = int(top + (bottom - top) * split_frac)
        for c in range(cols):
            frame = sheet[r * CELL:(r + 1) * CELL, c * CELL:(c + 1) * CELL]
            dy = best_dy(frame, anchor, top, split)
            comp = np.zeros_like(frame)
            # unten: Beine/Saum aus dem animierten Rahmen
            comp[split + dy:, :] = frame[split + dy:, :]
            # oben: Anker (Kopf + Oberkoerper), um dy abgesenkt
            up = anchor[top:split]
            comp[top + dy:split + dy, :] = np.where(up[:, :, 3:4] > 0, up, comp[top + dy:split + dy, :])
            out[r * CELL:(r + 1) * CELL, c * CELL:(c + 1) * CELL] = drop_orphans(comp)
    Image.fromarray(out).save(out_path)

if __name__ == '__main__' and len(sys.argv) == 4:
    stabilize(*sys.argv[1:4])


SETS = {
    # Idle und Walk entstehen in build_cycles.py. Hier nur die Sheets mit eigener Pose (Angriff, Schuss).
    'BULUT SHERIFF/ANIMATIONS_8DIR/bulut': [('shoot', 72)],
    'DER GAST/ANIMATIONS_8DIR/der_gast_revealed': [('attack', 72)],
    'DIE HAUSFRAU/ANIMATIONS_8DIR/die_hausfrau_revealed': [('attack', 72)],
}

def run_all(root='Assets/_Project/Art/Characters/'):
    """Aufruf aus dem Projektordner nach build_cycles.py: python Tools/stabilize.py --all
    Setzt den bereinigten Kopf aus der Stand-Pose (*_stand_clean.png) auf Frames, deren Kopfpose passt."""
    from stabilize2 import stabilize as head_anchor
    for base, kinds in SETS.items():
        for kind, cell in kinds:
            stats = head_anchor(root + base + '_stand_clean.png', f'{root}{base}_{kind}_sheet.png', f'{root}{base}_{kind}_fixed.png', cell=cell)
            print('ok', base, kind, 'verankert/behalten', stats)

if __name__ == '__main__' and len(sys.argv) == 2 and sys.argv[1] == '--all':
    run_all()
elif __name__ == '__main__' and len(sys.argv) == 4:
    stabilize(*sys.argv[1:4])
