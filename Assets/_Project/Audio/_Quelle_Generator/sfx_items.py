"""Items, Handwerk, Bar, Grab, Wald-Aktionen, Talismane. Bezug: Art/Items (Essen, Getraenke, Werkzeug, Talismane ...),
Getraenke-Rezepte (Einschenken, Wachtgroschen), Opening (Zettel am Baumstamm), Friedhof (Grab, Schaufel, Sarg), Can (Gebuesch)."""
import numpy as np

import nwaudio as nw
from nwaudio import (sound, white, bp, lp, hp, thump, env_ar, modal, click, layer, sparse, tt, n_, TAU, tv_filter,
                     reverb, colored, voice, sine, midi, note)
from sfx_doors import wood_hit, creak

I = 'SFX/Items'
B = 'SFX/Bar'
H = 'SFX/Handwerk'
W = 'SFX/Wald'
T = 'SFX/Talisman'


def cloth(d, r, lo=300, hi=3500, a=0.02, tau=0.1):
    return bp(white(d, r), lo, hi) * env_ar(d, a, tau)


# --------------------------------------------------------------------------- Inventar

@sound(I, 'aufheben_klein', n=4, desc='Kleinen Gegenstand aufheben: Stoff, kurzer Klick', peak=-10)
def aufheben_klein(r, i):
    return layer((cloth(0.18, r, 500, 4000, 0.01, 0.05), 1.0), (click(0.02, 1500, 5000, 0.004, r), 0.4, 0.1))


@sound(I, 'aufheben_gross', n=3, desc='Schweren Gegenstand aufheben: Ächzen von Leder, dumpf', peak=-9)
def aufheben_gross(r, i):
    return layer((cloth(0.35, r, 200, 2500, 0.05, 0.15), 1.0), (thump(0.25, 100, 60, 0.05), 0.5, 0.2))


@sound(I, 'fallenlassen', n=4, desc='Gegenstand fallen lassen: dumpfer Aufprall', peak=-9)
def fallenlassen(r, i):
    return layer((thump(0.25, r.uniform(110, 170), 60, 0.05), 1.0), (click(0.03, 600, 3000, 0.006, r), 0.5))


@sound(I, 'inventar_auf', n=2, desc='Rucksack oeffnen: Leder, Schnalle', peak=-10)
def inventar_auf(r, i):
    return layer((cloth(0.35, r, 250, 3000, 0.04, 0.12), 1.0), (modal([2300, 3500], [0.3, 0.2], [0.07, 0.05], 0.15), 0.3), (click(0.02, 2000, 6000, 0.003, r), 0.5, 0.05))


@sound(I, 'inventar_zu', n=2, desc='Rucksack schliessen: Leder, Schnalle rastet', peak=-10)
def inventar_zu(r, i):
    return layer((cloth(0.28, r, 250, 3000, 0.03, 0.09), 1.0), (modal([2100, 3300], [0.4, 0.25], [0.08, 0.05], 0.15), 0.4, 0.2), (click(0.02, 2000, 6000, 0.003, r), 0.6, 0.2))


@sound(I, 'ausruesten', n=3, desc='Werkzeug/Waffe in die Hand nehmen: Leder und Metall', peak=-9)
def ausruesten(r, i):
    return layer((cloth(0.25, r, 400, 3500, 0.02, 0.08), 0.8), (modal([r.uniform(1700, 2300), r.uniform(3000, 4200)], [0.4, 0.25], [0.1, 0.07], 0.2), 0.5, 0.1))


@sound(I, 'wegstecken', n=3, desc='Werkzeug wegstecken', peak=-10)
def wegstecken(r, i):
    return layer((cloth(0.3, r, 300, 3000, 0.04, 0.1), 0.8), (thump(0.15, 120, 70, 0.03), 0.4, 0.22))


# --------------------------------------------------------------------------- Essen, Trinken

@sound(I, 'essen_biss', n=4, desc='Abbeissen und Kauen (Brot, Apfel, Fleisch)', peak=-10)
def biss(r, i):
    crunch = hp(sparse(0.25, 700, r), 1800) * np.exp(-tt(0.25) / 0.06)
    chew = lp(white(0.5, r), 900) * (0.5 + 0.5 * np.sin(TAU * 4.5 * tt(0.5))) * 0.25
    return layer((crunch * 1.5, 1.0), (chew, 0.5, 0.2))


@sound(I, 'trinken_schluck', n=3, desc='Schluck trinken: Glucksen', peak=-11)
def schluck(r, i):
    t = tt(0.5)
    f = 280 + 120 * np.sin(TAU * 3 * t)
    g = np.sin(TAU * np.cumsum(f) / nw.SR) * np.exp(-((t - 0.25) / 0.2) ** 2) * 0.3
    return layer((g, 1.0), (bp(white(0.5, r), 300, 1500) * np.exp(-((t - 0.25) / 0.25) ** 2) * 0.3, 1.0))


@sound(B, 'einschenken', n=3, desc='Getraenk ins Glas giessen: Fluessigkeit steigt im Ton, Blasen (Getraenke-Rezepte)', peak=-10)
def einschenken(r, i):
    d = 2.0
    t = tt(d)
    stream = tv_filter(white(d, r), lambda u: 700 + 2200 * u, 1.0) * np.minimum(1, t / 0.1) * np.where(t < d - 0.2, 1, np.exp(-(t - (d - 0.2)) / 0.05))
    bub = np.zeros(len(t))
    for k in range(60):
        t0 = r.uniform(0, d - 0.1)
        f = 500 + 1200 * (t0 / d) + r.uniform(0, 300)
        m = t >= t0
        bub[m] += np.sin(TAU * np.cumsum(f * (1 + 4 * (t[m] - t0))) / nw.SR) * np.exp(-(t[m] - t0) / 0.012) * r.uniform(0.2, 0.6)
    return layer((stream, 0.5), (bub, 0.25))


@sound(B, 'glas_anstossen', n=3, desc='Glaeser stossen an: heller Klang', peak=-8)
def anstossen(r, i):
    f = r.uniform(2400, 3200)
    return reverb(nw.hit(f, 0.6, r, 0.95, sec=0.8, n=9, ratio_pow=1.3, inharm=0.15, tilt=0.75, air=0.35), r, 0.3, 0.08, 7000)


@sound(B, 'glas_abstellen', n=4, desc='Glas auf der Theke abstellen: Klack, kurzes Klingen', peak=-9)
def abstellen(r, i):
    f = r.uniform(1800, 2600)
    return layer((nw.hit(f, 0.22, r, 0.8, sec=0.35, n=7, ratio_pow=1.3, inharm=0.15, air=0.5), 1.0), (thump(0.1, 200, 100, 0.02), 0.4))


@sound(B, 'glas_zerbricht', n=3, desc='Glas zerbricht: Klirren, Scherben rutschen', peak=-4)
def zerbricht(r, i):
    shards = np.zeros(n_(1.1))
    for k in range(r.integers(14, 24)):
        t0 = abs(r.normal(0, 0.28))
        f = r.uniform(2500, 7500)
        s = modal([f, f * 1.37], [1, 0.5], [0.06, 0.04], 0.15) * r.uniform(0.3, 1.0)
        a = int(min(t0, 0.9) * nw.SR)
        shards[a:a + len(s)] += s[:len(shards) - a]
    return reverb(layer((shards, 1.0), (click(0.04, 1500, 9000, 0.006, r), 1.0)), r, 0.4, 0.1, 7000)


@sound(B, 'korken_ploppt', n=2, desc='Korken aus der Flasche', peak=-8)
def korken(r, i):
    t = tt(0.3)
    pop = np.sin(TAU * np.cumsum(260 + 400 * np.exp(-t / 0.02)) / nw.SR) * np.exp(-t / 0.045)
    return layer((pop, 1.0), (bp(white(0.15, r), 600, 3000) * env_ar(0.15, 0.001, 0.03), 0.5))


@sound(B, 'muenzen_klimpern', n=3, desc='Wachtgroschen (Silbermuenzen) klimpern in der Hand', peak=-9)
def muenzen(r, i):
    out = []
    for k in range(r.integers(4, 8)):
        f = r.uniform(3000, 5200)
        out.append((nw.hit(f, 0.28, r, 1.0, sec=0.5, n=8, ratio_pow=1.6, inharm=0.2, air=0.6), r.uniform(0.3, 1), r.uniform(0, 0.35)))
    return reverb(layer(*out), r, 0.2, 0.05, 8000)


@sound(B, 'muenze_einzeln', n=4, desc='Eine Muenze auf die Theke gelegt', peak=-9)
def muenze(r, i):
    f = r.uniform(3200, 4800)
    return nw.hit(f, 0.32, r, 1.0, sec=0.6, n=8, ratio_pow=1.6, inharm=0.2, air=0.6)


@sound(B, 'kasse', n=2, desc='Kasse der Bar: Klingel, Schublade springt auf (Ilhan kassiert)', peak=-6)
def kasse(r, i):
    ding = modal([2600, 5200, 7900], [1, 0.4, 0.2], [1.0, 0.6, 0.3], 1.2)
    drawer = layer((click(0.05, 500, 3000, 0.01, r), 0.6), (thump(0.3, 110, 60, 0.07), 0.8), (creak(0.25, 240, 300, r, 0.4, (700, 1400)), 0.2))
    return layer((ding, 0.8), (drawer, 0.9, 0.04), (modal([1800, 2500, 4100], [0.5, 0.3, 0.2], [0.15, 0.1, 0.06], 0.3), 0.5, 0.3))


@sound(B, 'dart_treffer', n=3, desc='Dartpfeil trifft die Scheibe', peak=-9)
def dart(r, i):
    return layer((nw.hit(r.uniform(750, 1000), 0.1, r, 0.6, sec=0.22, n=8, ratio_pow=1.4, inharm=0.2, air=0.5), 1.0), (thump(0.1, 200, 110, 0.02), 0.5))


@sound(B, 'stuhl_ruecken', n=3, desc='Stuhl ueber Dielen ruecken', peak=-9)
def stuhl(r, i):
    d = r.uniform(0.35, 0.6)
    return layer((creak(d, r.uniform(70, 110), r.uniform(80, 130), r, 0.8, (250, 800), 2.5), 0.7),
                 (wood_hit(r.uniform(110, 150), 0.2, r, 0.3, 0.9), 1.0, d * 0.9))


@sound(B, 'hinsetzen', n=3, desc='Auf Stuhl / Bank setzen: Holz knarrt, Stoff', peak=-10)
def hinsetzen(r, i):
    return layer((cloth(0.3, r, 200, 2000, 0.05, 0.1), 0.6), (creak(0.3, 90, 130, r, 0.7, (250, 700), 2.5), 0.5), (wood_hit(r.uniform(110, 160), 0.25, r, 0.35, 0.8), 1.0, 0.15))


@sound(B, 'tasse_abstellen', n=3, desc='Keramiktasse auf Holz (Sheriff, Kaffee)', peak=-10)
def tasse(r, i):
    f = r.uniform(1500, 2100)
    return layer((nw.hit(f, 0.14, r, 0.65, sec=0.25, n=8, ratio_pow=1.4, inharm=0.2, air=0.45), 1.0), (thump(0.1, 180, 100, 0.02), 0.4))


@sound(B, 'schublade', n=3, desc='Schublade (Schreibtisch, Revier) aufziehen', peak=-10)
def schublade(r, i):
    d = 0.5
    rumble = tv_filter(colored(d, r, 1.0), lambda u: 200 + 300 * u, 1.5) * np.sin(np.pi * tt(d) / d) ** 0.7
    return layer((rumble, 0.6), (wood_hit(r.uniform(120, 160), 0.25, r, 0.35, 0.8), 1.0, 0.45), (click(0.02, 1500, 5000, 0.003, r), 0.4, 0.03))


# --------------------------------------------------------------------------- Papier, Schreiben, Licht

@sound(I, 'papier_rascheln', n=4, desc='Papier rascheln (zerrissener Zettel am Baumstamm: Liste von Namen)', peak=-10)
def papier(r, i):
    d = r.uniform(0.7, 1.2)
    x = hp(white(d, r), 1500) * (0.4 + 0.6 * np.clip(lp(r.standard_normal(n_(d)), 18, 1) / 0.3, 0, 1)) * np.sin(np.pi * tt(d) / d) ** 0.5
    return x + hp(sparse(d, 160, r), 3000) * 0.5


@sound(I, 'papier_zerreissen', n=2, desc='Papier zerreissen', peak=-8)
def zerreissen(r, i):
    d = 0.7
    return layer((tv_filter(white(d, r), lambda u: 2500 + 3000 * u, 1.0) * np.clip(lp(r.standard_normal(n_(d)), 40, 1) / 0.4 + 0.6, 0, 1.5) * np.sin(np.pi * tt(d) / d) ** 0.6, 1.0),
                 (hp(sparse(d, 250, r), 3000) * 0.5, 1.0))


@sound(I, 'seite_umblaettern', n=3, desc='Seite im Tagebuch umblaettern', peak=-11)
def seite(r, i):
    return layer((tv_filter(white(0.3, r), lambda u: 1500 + 4000 * u, 1.0) * np.sin(np.pi * tt(0.3) / 0.3) ** 1.5, 1.0), (click(0.02, 1000, 5000, 0.004, r), 0.3, 0.26))


@sound(I, 'tagebuch_schreiben', n=2, desc='Bleistift kratzt ueber Papier (Tagebuch, Veronicas Totenbuch)', peak=-12)
def schreiben(r, i):
    d = 3.0
    n = n_(d)
    strokes = np.zeros(n)
    t = 0.1
    while t < d - 0.3:
        L = r.uniform(0.06, 0.22)
        s = bp(white(L, r), 1800, 7500) * np.sin(np.pi * tt(L) / L)
        a = int(t * nw.SR)
        strokes[a:a + len(s)] += s[:n - a] * r.uniform(0.4, 1)
        t += L + r.uniform(0.02, 0.2)
    return strokes


@sound(I, 'streichholz', n=3, desc='Streichholz anreissen und aufflammen', peak=-8)
def streichholz(r, i):
    rasp = tv_filter(white(0.25, r), lambda u: 2500 + 3500 * u, 1.3) * np.sin(np.pi * tt(0.25) / 0.25)
    flare = hp(white(0.5, r), 800) * env_ar(0.5, 0.02, 0.15) * 0.4
    return layer((rasp, 0.8), (flare, 0.8, 0.22), (click(0.02, 3000, 9000, 0.003, r), 0.5, 0.22))


@sound(I, 'kerze_anzuenden', n=2, desc='Kerze anzuenden: Streichholz, Docht fasst', peak=-10)
def kerze_an(r, i):
    return layer((streichholz(r, 0), 1.0), (hp(white(0.6, r), 1800) * env_ar(0.6, 0.1, 0.2) * 0.1, 1.0, 0.45))


@sound(I, 'laterne_anzuenden', n=2, desc='Laterne anzuenden: Glas klappt auf, Docht, Flamme faucht, Klappe zu', peak=-9)
def laterne_an(r, i):
    glass = modal([2500, 3800, 5300], [0.4, 0.3, 0.2], [0.2, 0.14, 0.08], 0.4)
    return layer((glass, 0.5), (streichholz(r, 0), 0.8, 0.35), (glass, 0.4, 1.1), (click(0.02, 2000, 6000, 0.003, r), 0.5, 1.1))


@sound(I, 'feuer_entfachen', n=2, desc='Kamin/Feuer entfachen: Zunder, Flamme wuchtet auf, Knistern', peak=-8)
def feuer_an(r, i):
    d = 2.5
    whump = lp(white(d, r), 700) * env_ar(d, 0.15, 0.7)
    crackle = hp(sparse(d, 60, r), 2500) * np.minimum(1, tt(d) / 0.8) * 2.0
    return layer((whump, 0.6), (crackle, 0.7), (streichholz(r, 0), 0.7))


@sound(I, 'holz_nachlegen', n=3, desc='Holzscheit ins Feuer legen: Rumpeln, Funken', peak=-8)
def holz_nach(r, i):
    return layer((wood_hit(r.uniform(90, 120), 0.4, r, 0.7, 0.6), 1.0), (hp(sparse(0.8, 90, r), 2500) * np.exp(-tt(0.8) / 0.3) * 2.0, 0.5, 0.1))


@sound(I, 'schluessel_klimpern', n=3, desc='Veronicas Schluesselbund: Metallklingeln', peak=-9)
def klimpern(r, i):
    out = []
    for k in range(r.integers(5, 9)):
        f = r.uniform(1800, 4200)
        out.append((nw.hit(f, 0.2, r, 1.0, sec=0.35, n=7, ratio_pow=1.6, inharm=0.25, air=0.6), r.uniform(0.3, 1), r.uniform(0, 0.4)))
    return layer(*out)


@sound(I, 'truhe_auf', n=2, desc='Truhe oeffnen: Scharnier knarrt, Deckel schlaegt zurueck', peak=-8)
def truhe_auf(r, i):
    return layer((creak(0.7, 190, 260, r, 0.6, (500, 1100)), 0.5), (wood_hit(r.uniform(110, 150), 0.35, r, 0.6, 0.4), 1.0, 0.65))


@sound(I, 'truhe_zu', n=2, desc='Truhe zuklappen', peak=-7)
def truhe_zu(r, i):
    return layer((creak(0.3, 260, 200, r, 0.4, (500, 1000)), 0.3), (wood_hit(r.uniform(100, 140), 0.5, r, 1.0, 0.3), 1.0, 0.25), (click(0.02, 1500, 5000, 0.004, r), 0.5, 0.3))


@sound(I, 'verband', n=2, desc='Verband abreissen und wickeln (Veronica heilt)', peak=-11)
def verband(r, i):
    tear = tv_filter(white(0.4, r), lambda u: 3500 + 2000 * u, 1.0) * np.sin(np.pi * tt(0.4) / 0.4) ** 0.5
    wrap = cloth(1.0, r, 500, 4000, 0.1, 0.4) * (0.6 + 0.4 * np.sin(TAU * 3 * tt(1.0)))
    return layer((tear, 0.8), (wrap, 0.5, 0.4))


@sound(I, 'tabletten', n=2, desc='Tablettenflasche schuetteln', peak=-10)
def tabletten(r, i):
    d = 0.8
    return layer((hp(sparse(d, 90, r), 2000) * np.minimum(1, np.sin(np.pi * tt(d) / d) * 2), 1.0), (modal([1900, 3100], [0.2, 0.1], [0.05, 0.04], 0.1), 0.0))


# --------------------------------------------------------------------------- Handwerk, Grab, Wald

@sound(H, 'schaufel_graben', n=4, desc='Schaufel sticht in Erde und hebt aus (Grab am Dorfeingang)', peak=-8)
def graben(r, i):
    scr = tv_filter(white(0.3, r), lambda u: 600 + 1200 * u, 1.2) * env_ar(0.3, 0.03, 0.1)
    return layer((scr, 0.7), (click(0.05, 2000, 7000, 0.01, r), 0.6, 0.0), (thump(0.3, 100, 55, 0.07), 0.8, 0.28),
                 (hp(sparse(0.3, 500, r), 2500) * np.exp(-tt(0.3) / 0.1), 0.4, 0.3))


@sound(H, 'erde_werfen', n=4, desc='Erde auf den Haufen / auf den Sarg werfen', peak=-9)
def erde(r, i):
    return layer((thump(0.4, 110, 50, 0.1), 1.0), (lp(white(0.4, r), 1500) * env_ar(0.4, 0.01, 0.1), 0.8), (hp(sparse(0.3, 400, r), 2500) * np.exp(-tt(0.3) / 0.08), 0.4, 0.05))


@sound(H, 'sarg_absenken', desc='Sarg an Seilen ins Grab: Seil knarrt, Holz schabt, dumpfer Aufsetzer', peak=-8)
def sarg(r, i):
    d = 3.2
    rope = creak(2.4, 55, 75, r, 1.0, (400, 900), 3.0) * 0.5
    scrape = tv_filter(colored(2.0, r, 1.0), lambda u: 300 + 200 * u, 1.5) * 0.15 * np.sin(np.pi * tt(2.0) / 2.0)
    return reverb(layer((rope, 1.0), (scrape, 1.0, 0.2), (thump(0.8, 85, 38, 0.2), 1.2, 2.6), (wood_hit(110, 0.6, r, 0.6, 0.5), 1.0, 2.6)), r, 0.6, 0.15, 2500)


@sound(H, 'holz_hacken', n=3, desc='Holz hacken: Axt spaltet Scheit, zwei Haelften fallen', peak=-4)
def hacken(r, i):
    return reverb(layer((click(0.1, 500, 5000, 0.02, r), 1.0), (wood_hit(r.uniform(140, 200), 0.5, r, 1.0, 0.2), 1.0),
                        (wood_hit(r.uniform(120, 170), 0.3, r, 0.5, 0.5), 1.0, 0.18), (wood_hit(r.uniform(150, 210), 0.3, r, 0.4, 0.5), 1.0, 0.28)), r, 0.4, 0.1, 3500)


@sound(H, 'eimer_brunnen', n=2, desc='Eimer am Brunnen hochziehen: Rolle quietscht, Wasser tropft, Eimer klappert', peak=-9)
def brunnen_eimer(r, i):
    pulley = creak(1.8, 380, 440, r, 0.6, (900, 1700), 4.0) * 0.4
    drip = np.zeros(n_(2.8))
    for k in range(r.integers(10, 18)):
        t0 = r.uniform(0.2, 2.6)
        f = r.uniform(900, 1800)
        s = sine(f * (1 + 0.8 * np.exp(-tt(0.12) / 0.03)), 0.12) * np.exp(-tt(0.12) / 0.03)
        a = int(t0 * nw.SR)
        drip[a:a + len(s)] += s[:len(drip) - a] * r.uniform(0.1, 0.4)
    clack = wood_hit(r.uniform(150, 200), 0.3, r, 0.6, 0.2)
    return reverb(layer((pulley, 1.0), (drip, 0.6), (clack, 0.6, 2.0)), r, 0.6, 0.15, 5000)


@sound(H, 'wasser_plaetschern', n=3, desc='Wasser plaetschert (Hand im Brunnen, Trog)', peak=-12)
def plaetschern(r, i):
    d = 1.6
    t = tt(d)
    out = bp(white(d, r), 400, 5000) * np.clip(0.3 + lp(r.standard_normal(len(t)), 14, 1) / 0.4, 0, 1.2) * 0.3
    for k in range(40):
        t0 = r.uniform(0, d - 0.1)
        f = r.uniform(600, 2000)
        m = t >= t0
        out[m] += np.sin(TAU * np.cumsum(f * (1 + 3 * (t[m] - t0))) / nw.SR) * np.exp(-(t[m] - t0) / 0.015) * r.uniform(0.1, 0.4)
    return out * np.sin(np.pi * t / d) ** 0.5


@sound(W, 'ast_bricht', n=4, desc='Ast bricht: Knacken (Schleichen im Wald, Warnung)', peak=-6)
def ast(r, i):
    return layer((click(0.1, 800, 6000, 0.02, r), 1.0), (modal([r.uniform(300, 500), r.uniform(900, 1300)], [0.5, 0.3], [0.12, 0.08], 0.25), 0.6),
                 (hp(sparse(0.2, 400, r), 3000) * np.exp(-tt(0.2) / 0.05), 0.4))


@sound(W, 'busch_raschelt', n=5, desc='Etwas bewegt sich im Gebuesch (Can fuettert am Waldrand; der Spieler sieht nur Bewegung)', peak=-9)
def busch(r, i):
    d = r.uniform(0.9, 1.8)
    n = n_(d)
    mod = np.clip(0.4 + lp(r.standard_normal(n), 12, 1) / 0.3, 0, 1.4)
    x = bp(white(d, r), 1500, 7500) * mod * np.sin(np.pi * tt(d) / d) ** 0.7
    return x + hp(sparse(d, 100, r), 3500) * 0.4 * np.sin(np.pi * tt(d) / d)


@sound(W, 'blaetter_rascheln', n=3, desc='Laub / Gebuesch beim Hindurchgehen (Dickicht, Machete)', peak=-11)
def blaetter(r, i):
    d = 0.9
    return layer((hp(white(d, r), 2000) * env_ar(d, 0.05, 0.2), 0.5), (hp(sparse(d, 350, r), 3000) * np.exp(-tt(d) / 0.3), 1.0))


@sound(W, 'kraeuter_pfluecken', n=4, desc='Kraut / Beere pfluecken: Rupfen, kleines Knacken', peak=-11)
def pfluecken(r, i):
    return layer((cloth(0.15, r, 1500, 6000, 0.01, 0.04), 0.8), (click(0.02, 1500, 5000, 0.005, r), 0.7, 0.1))


@sound(W, 'untersuchen_loop', sr=22050, loop=True, desc='Baumstamm untersuchen (Fortschrittsbalken 7 s): leises Rascheln, Tasten - Opening Step 7 verlangt Stille sonst', peak=-18)
def untersuchen(r, i):
    d = 8.0
    n = n_(d)
    mod = np.clip(0.3 + lp(r.standard_normal(n), 4, 1, circ=True) / 0.4, 0, 1.2)
    x = bp(white(d, r), 800, 5000, 2, circ=True) * mod
    return x + hp(sparse(d, 20, r), 2500) * 0.4


# --------------------------------------------------------------------------- Talismane (Palette: kuehles Blau, #6fd3e6)

def shimmer(freqs, d, r, rate=5.0, tail=0.4):
    t = tt(d)
    y = sum(sine(f * (1 + 0.002 * np.sin(TAU * rate * t + k)), d) for k, f in enumerate(freqs)) / len(freqs)
    return y


@sound(T, 'talisman_aufhaengen', n=2, desc='Talisman an den Haken neben die Tuer haengen: Schnur, Holzklick, klares Klingen', peak=-9)
def tal_haengen(r, i):
    cord = cloth(0.25, r, 1000, 6000, 0.03, 0.06)
    tap = wood_hit(r.uniform(230, 300), 0.2, r, 0.4, 0.8)
    ring = modal([1568, 2349, 3136, 4699], [1, 0.6, 0.45, 0.25], [1.4, 1.0, 0.8, 0.5], 1.6)
    return reverb(layer((cord, 0.5), (tap, 0.7, 0.2), (ring, 0.45, 0.22)), r, 1.0, 0.25, 8000)


@sound(T, 'talisman_aktiv', n=2, desc='Talisman-Feld schliesst sich ums Haus: aufsteigendes kuehles Summen, dann ruhiger Ton', peak=-8)
def tal_aktiv(r, i):
    d = 3.0
    t = tt(d)
    y = shimmer([523, 784, 1047, 1568, 2093], d, r) * np.minimum(1, (t / 1.8) ** 2) * np.where(t < 2.0, 1, np.exp(-(t - 2.0) / 0.6))
    air = hp(white(d, r), 3500) * np.minimum(1, t / 2.0) ** 2 * 0.08
    return reverb(layer((y, 0.8), (air, 1.0), (modal([1047, 1568, 2093], [0.5, 0.4, 0.3], [1.5, 1.2, 1.0], 2.0), 0.4, 1.9)), r, 1.5, 0.3, 9000)


@sound(T, 'talisman_summen_loop', sr=22050, loop=True, desc='Talisman-Feld (Schutzraum): leises kuehles Summen, schwebende Terz-Quinte (Loop)', peak=-22)
def tal_loop(r, i):
    d = 6.0
    t = tt(d)
    y = (sine(392.0, d) + sine(392.0 * 1.5 + 0.7, d) + 0.6 * sine(784.0 - 0.9, d) + 0.4 * sine(1174.7, d))
    y *= 1 + 0.25 * np.sin(TAU * (1 / 6.0) * t * 2) + 0.1 * np.sin(TAU * (1 / 6.0) * t * 5 + 1)
    return y


@sound(T, 'talisman_fund', n=2, desc='Talisman im Wald gefunden: reiner, kristallener Akkord (selten, kostbar)', peak=-7)
def tal_fund(r, i):
    notes = ['E5', 'B5', 'E6', 'G#6'] if i == 0 else ['D5', 'A5', 'D6', 'F#6']
    out = []
    for k, nm in enumerate(notes):
        f = midi(note(nm))
        out.append((modal([f, f * 2.0, f * 3.01, f * 4.2], [1, 0.4, 0.25, 0.12], [2.4, 1.4, 0.9, 0.5], 3.0), 0.7, k * 0.11))
    return reverb(layer(*out), r, 1.8, 0.35, 9000)


@sound(T, 'talisman_bricht', n=2, desc='Talisman zerbricht (Barrikade/Feld faellt): Glasriss, absteigendes Schimmern, dumpfer Nachhall', peak=-5)
def tal_bricht(r, i):
    d = 3.0
    t = tt(d)
    crack = layer((click(0.1, 1500, 9000, 0.015, r), 1.0), (modal([r.uniform(2800, 3500), r.uniform(4200, 5200), 6100], [0.7, 0.5, 0.3], [0.4, 0.3, 0.2], 0.8), 0.6))
    fall = sum(sine(f * np.exp(-t / 1.5 * 0.6), d) for f in (1568, 1175, 784)) * np.exp(-t / 0.9) * 0.2
    return reverb(layer((crack, 1.0), (fall, 1.0, 0.05), (thump(0.8, 90, 40, 0.15), 0.8, 0.02)), r, 1.4, 0.3, 6000)


@sound(T, 'talisman_schrein_oeffnen', n=2, desc='Talisman-Schrein im Haus oeffnen: Holzklappe, leises Klingeln der gelagerten Talismane', peak=-10)
def tal_schrein(r, i):
    return layer((creak(0.35, 260, 320, r, 0.4, (600, 1200)), 0.3), (wood_hit(r.uniform(200, 260), 0.2, r, 0.5, 0.7), 1.0, 0.3),
                 (reverb(modal([2093, 3136, 4186], [0.4, 0.3, 0.2], [0.8, 0.6, 0.4], 1.0), r, 0.6, 0.2, 9000), 0.3, 0.35))
