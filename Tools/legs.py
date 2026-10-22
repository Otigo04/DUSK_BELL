"""Gegliederte Beine fuer die Gehzyklen: Oberschenkel, Knie, Wade, Fuss.

Seitenansicht: Zwei-Knochen-Bein. Der Oberschenkel schwingt um die Huefte, beim Vorschwingen beugt sich das Knie
und hebt den Fuss. Die Huefte sinkt so weit, dass der tiefste Fuss genau am Boden steht (daraus ergibt sich das Gehwippen).
Vorderansicht: zwei senkrechte, nach unten schmaler werdende Beine, das Schwungbein hebt den Fuss.
Alles pixelgenau: Maske pro Gliedmasse, Outline = Rand um die Maske, eine Schattenspalte auf der Rueckseite.
"""
import math

import numpy as np

OUTLINE = (0x1a, 0x15, 0x26)


def _limb_mask(shape, p0, p1, w0, w1):
    """Maske eines sich verjuengenden Segments von p0 nach p1 (x, y als float)."""
    h, w = shape
    m = np.zeros(shape, dtype=bool)
    x0, y0 = p0
    x1, y1 = p1
    dx, dy = x1 - x0, y1 - y0
    ln2 = dx * dx + dy * dy
    ys, xs = np.mgrid[0:h, 0:w]
    px, py = xs + 0.5, ys + 0.5
    if ln2 < 1e-6:
        t = np.zeros_like(px)
    else:
        t = np.clip(((px - x0) * dx + (py - y0) * dy) / ln2, 0, 1)
    cx, cy = x0 + t * dx, y0 + t * dy
    dist = np.hypot(px - cx, py - cy)
    half = (w0 + (w1 - w0) * t) / 2.0
    m = dist <= half
    return m


def _dilate(m):
    d = m.copy()
    d[1:] |= m[:-1]
    d[:-1] |= m[1:]
    d[:, 1:] |= m[:, :-1]
    d[:, :-1] |= m[:, 1:]
    return d


def _paint(img, mask, style, shin_mask, foot_mask, knee_y, ankle_y, boot_h, light, dark, shade, outline_img=None):
    """Malt ein Bein mit Detail: Lichtkante / Mittelton / dunkle Innenkante, Knie-Falten, Stoffglanz, Saum, Stiefel mit Glanzpunkt.
    light: -1 = Licht links, +1 = Licht rechts."""
    p_dark, p_mid, p_light = style['pants']
    cuff = style.get('cuff')                  # (Saum, Saumkante) oder None
    boot, boot_hi, boot_dark = style['boot']

    out = _dilate(mask) & ~mask
    for y, x in zip(*np.where(out)):
        img[y, x, :3] = OUTLINE
        img[y, x, 3] = 255

    boot_top = ankle_y - max(0, boot_h - 3)   # erste Stiefelzeile an der Wade
    rows = [y for y in range(mask.shape[0]) if mask[y].any()]
    first_row = rows[0]
    for y in rows:
        xs = np.where(mask[y])[0]
        x0, x1 = int(xs.min()), int(xs.max())
        width = x1 - x0 + 1
        light_x = x0 if light < 0 else x1
        dark_x = x1 if light < 0 else x0
        for x in xs:
            on_foot = bool(foot_mask[y, x])
            in_boot = on_foot or (shin_mask[y, x] and y >= boot_top)
            if in_boot:
                col = boot
                if x == light_x and not on_foot:
                    col = boot_hi                      # Glanzkante am Schaft
                if on_foot and y == int(np.where(foot_mask.any(axis=1))[0].min()):
                    col = boot_hi if x == light_x or x == dark_x else boot
                if on_foot and y == int(np.where(foot_mask.any(axis=1))[0].max()):
                    col = boot_dark                    # Sohle
            elif cuff and y >= boot_top - 3:
                col = cuff[1] if y == boot_top - 1 else cuff[0]   # grauer Saum, helle Kante direkt ueber dem Stiefel
            else:
                if width >= 3 and x == light_x:
                    col = p_light
                elif width >= 3 and x == dark_x:
                    col = p_dark
                else:
                    col = p_mid
                # Knie-Falte: zwei dunkle Pixel quer
                if abs(y - knee_y) < 0.6 and width >= 4 and x not in (x0, x1) and (x - x0) % 2 == 0:
                    col = p_dark
                # Stoffglanz am Oberschenkel: einzelne helle Pixel neben der Lichtkante
                if (y - first_row) % 3 == 1 and width >= 5 and x == (light_x - light):
                    col = p_light
                # Falten an der Wade
                if (y - first_row) % 4 == 2 and width >= 5 and x == (dark_x + light) and y > knee_y:
                    col = p_dark
            if dark:
                col = shade(col, 0.75)
            img[y, x, :3] = col
            img[y, x, 3] = 255


def render_side(shape, hip_x, hip_y, ground_y, fwd, phase, amp, widths, style, boot_h, shade, idle):
    """Gibt (Beinbild, Huefte-Absenkung in px) zurueck."""
    h, w = shape
    shoe_h = 2
    L = ground_y - shoe_h - hip_y            # Huefte bis Knoechel (gerade)
    Lt = int(round(L * 0.52))
    Ls = L - Lt
    legs = []
    for k in (0, 1):
        phi = 0.0 if idle else (phase + 0.5 * k)
        theta = amp * math.sin(2 * math.pi * phi) if not idle else 0.0
        flex = 0.0 if idle else 1.0 * max(0.0, math.cos(2 * math.pi * phi))
        legs.append((theta, flex))

    def joints(theta, flex, hy):
        kx = hip_x + fwd * Lt * math.sin(theta)
        ky = hy + Lt * math.cos(theta)
        beta = theta - flex
        ax = kx + fwd * Ls * math.sin(beta)
        ay = ky + Ls * math.cos(beta)
        return (kx, ky), (ax, ay)

    reach = [(joints(t, f, hip_y)[1][1] - hip_y) for t, f in legs]
    drop = max(0.0, L - max(reach)) if not idle else 0.0
    hy = hip_y + drop

    out = np.zeros((h, w, 4), dtype=np.uint8)
    order = sorted(range(2), key=lambda i: legs[i][0])  # hinteres Bein (kleinerer Winkel) zuerst
    wt, wk, wc, wa = widths
    for rank, i in enumerate(order):
        theta, flex = legs[i]
        (kx, ky), (ax, ay) = joints(theta, flex, hy)
        thigh = _limb_mask((h, w), (hip_x, hy), (kx, ky), wt, wk)
        calf = _limb_mask((h, w), (kx, ky), (ax, ay), wc, wa)
        # Fuss: Ferse 2 px hinter, Spitze 4 px vor dem Knoechel
        fx0, fx1 = (ax - 2.0, ax + 4.0) if fwd > 0 else (ax - 4.0, ax + 2.0)
        foot = np.zeros((h, w), dtype=bool)
        ys, xs = np.mgrid[0:h, 0:w]
        foot = (xs + 0.5 >= fx0) & (xs + 0.5 <= fx1) & (ys + 0.5 >= ay - 0.5) & (ys + 0.5 <= ay + shoe_h - 0.5)
        ys_, _ = np.mgrid[0:h, 0:w]
        calf = calf & (ys_ + 0.5 <= ay + shoe_h - 0.5)  # runde Enden nicht unter die Sohle ragen lassen
        mask = thigh | calf | foot
        _paint(out, mask, style, calf & ~foot, foot, ky, int(round(ay)), boot_h, fwd, dark=(rank == 0 and not idle), shade=shade)
    return out, drop


def render_front(shape, cx, hip_y, ground_y, phase, widths, style, boot_h, shade, idle):
    h, w = shape
    shoe_h = 2
    L = ground_y - shoe_h - hip_y
    Lt = int(round(L * 0.52))
    wt, wk, wc, wa = widths
    out = np.zeros((h, w, 4), dtype=np.uint8)
    s = 0.0 if idle else math.sin(2 * math.pi * phase)
    gap = 2
    lifts = []
    for sgn in (-1, 1):
        lift = max(0.0, s * -sgn) * 3.0
        lifts.append(lift)
    for sgn, lift in zip((-1, 1), lifts):
        hx = cx + sgn * (wt + gap) / 2.0
        ay = hip_y + L - lift
        ky = hip_y + Lt - lift * 0.5
        # Knie leicht nach aussen, wenn das Bein angehoben wird (perspektivische Verkuerzung)
        kx = hx + sgn * 0.4 * lift / 3.0
        thigh = _limb_mask((h, w), (hx, hip_y), (kx, ky), wt, wk)
        calf = _limb_mask((h, w), (kx, ky), (hx, ay), wc, wa)
        ys, xs = np.mgrid[0:h, 0:w]
        foot = (xs + 0.5 >= hx - (wa + 2) / 2.0) & (xs + 0.5 <= hx + (wa + 2) / 2.0) & (ys + 0.5 >= ay - 0.5) & (ys + 0.5 <= ay + shoe_h - 0.5)
        calf = calf & (ys + 0.5 <= ay + shoe_h - 0.5)
        mask = thigh | calf | foot
        _paint(out, mask, style, calf & ~foot, foot, ky, int(round(ay)), boot_h, sgn, dark=False, shade=shade)
    drop = 0.0 if idle else (1.0 if max(lifts) < 1.5 else 0.0)
    return out, drop
