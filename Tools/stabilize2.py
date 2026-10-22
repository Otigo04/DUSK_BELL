"""Kopf-Anker: Nur der Kopf kommt aus der Stand-Pose (stabiles Gesicht), Koerper/Arme/Beine bleiben aus dem animierten Frame."""
import sys
import numpy as np
from PIL import Image
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from stabilize import drop_orphans, figure_rows

def head_anchor(anchor, head_frac):
    top, bottom = figure_rows(anchor)
    neck = int(top + (bottom - top) * head_frac)
    return top, neck

def align(frame, anchor, top, neck, pad_y=(-1, 4), pad_x=(-2, 2)):
    """Beste (dx, dy), mit der der Anker-Kopf zum Kopf des Frames passt."""
    ref = anchor[top:neck]
    h = neck - top
    best = (10**9, 0, 0)
    for dy in range(pad_y[0], pad_y[1] + 1):
        for dx in range(pad_x[0], pad_x[1] + 1):
            y0 = top + dy
            if y0 < 0 or y0 + h > frame.shape[0]: continue
            shifted = np.roll(frame[y0:y0 + h], -dx, axis=1)
            # nur Silhouetten-Abweichung zaehlt, damit Gesichtsdetails die Lage nicht verfaelschen
            d = int(((shifted[:, :, 3] > 0) != (ref[:, :, 3] > 0)).sum())
            if d < best[0]: best = (d, dx, dy)
    return best[0], best[1], best[2]

def stabilize(stand_path, sheet_path, out_path, cell=56, head_frac=0.36, max_err=30):
    stand = np.array(Image.open(stand_path).convert('RGBA'))
    sheet = np.array(Image.open(sheet_path).convert('RGBA'))
    cols = sheet.shape[1] // cell
    out = np.zeros_like(sheet)
    big = cell > 56
    stats = [0, 0]
    for r in range(8):
        a56 = stand[0:56, r * 56:(r + 1) * 56]
        # Anker in die Zellgroesse setzen (groessere Zellen: zentriert)
        anchor = np.zeros((cell, cell, 4), dtype=np.uint8)
        pad = (cell - 56) // 2
        anchor[pad:pad + 56, pad:pad + 56] = a56
        top, neck = head_anchor(anchor, head_frac)
        for c in range(cols):
            frame = sheet[r * cell:(r + 1) * cell, c * cell:(c + 1) * cell].copy()
            if frame[:, :, 3].max() == 0: continue
            err, dx, dy = align(frame, anchor, top, neck, (-12, 12) if big else (-1, 4), (-12, 12) if big else (-2, 2))
            if err > max_err:  # Kopf in anderer Pose (Ausholen, Sprung): Original behalten
                out[r * cell:(r + 1) * cell, c * cell:(c + 1) * cell] = frame
                stats[1] += 1
                continue
            stats[0] += 1
            comp = frame.copy()
            comp[:neck + dy] = 0  # alter Kopf raus
            head = anchor[top:neck]
            ys = slice(top + dy, neck + dy)
            region = comp[ys]
            h = np.roll(head, dx, axis=1)
            comp[ys] = np.where(h[:, :, 3:4] > 0, h, region)
            out[r * cell:(r + 1) * cell, c * cell:(c + 1) * cell] = drop_orphans(comp)
    Image.fromarray(out).save(out_path)
    return stats
