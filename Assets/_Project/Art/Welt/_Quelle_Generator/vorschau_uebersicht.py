"""Gesamtuebersicht aller Zonen in einem Bild: _Vorschau/Welt_Uebersicht.png (aus den Einzel-Vorschauen, die die Generatoren schreiben).
Aufruf: python vorschau_uebersicht.py"""
import os
from PIL import Image, ImageDraw
import welt_lib as W

V = W.WELT + '/_Vorschau/'
PANELS = [('03 Fluss (Strom S, Gras-Ufer)', 'Fluss_S_Gras_f0.png'), ('03 Fluss (Kies-Ufer, Strom O)', 'Fluss_O_Kies_f0.png'),
          ('02 Tiefwald: Uebergang Gras -> Wald', 'Tiefwald_Uebergang_f0.png'), ('02 Tiefwald: Dickicht', 'Tiefwald_Dickicht_f0.png'),
          ('04 Sumpf: Moorwasser', 'Sumpf_Moorwasser_f0.png'), ('04 Sumpf: Bohlenweg', 'Sumpf_Bohlenweg.png'),
          ('05 Felsland: Plateau mit Felswand', 'Felsland_PlateauMoos_f0.png'), ('06 Ruinen: Mauer', 'Ruinen_Mauer_f0.png')]
PW, PH = 480, 300


def main():
    sheet = Image.new('RGBA', (2 * PW + 30, 4 * (PH + 26) + 10), (24, 22, 34, 255))
    d = ImageDraw.Draw(sheet)
    for i, (title, f) in enumerate(PANELS):
        p = V + f
        if not os.path.exists(p):
            continue
        im = Image.open(p).convert('RGBA')
        w, h = im.size
        crop = im.crop((0, 0, min(w, PW), min(h, PH)))
        x, y = 10 + (i % 2) * (PW + 10), 10 + (i // 2) * (PH + 26)
        d.text((x, y), title, fill=(230, 226, 240, 255))
        sheet.paste(crop, (x, y + 14))
    sheet.save(V + 'Welt_Uebersicht.png')
    print('ok', V + 'Welt_Uebersicht.png')


if __name__ == '__main__':
    main()
