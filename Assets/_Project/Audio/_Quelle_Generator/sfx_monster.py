"""Monster-Mechanik und Spieler-Koerper. Quellen: Regelwerk (Warnstufen 1-3, Tuerspion, Gegensprech, Sanity),
Monster-Bibel (gleiche Muster lernbar: Gast klopft dreimal, Hausfrau summt ein unbekanntes Lied), Kampfregeln
(Enthuellung: Kamera nah, Ton dumpf, dann das Grinsen; Lebenspunkte nur ueber Atem und Schwaeche im Audio)."""
import numpy as np

import nwaudio as nw
from nwaudio import (sound, white, bp, lp, hp, thump, env_ar, modal, click, layer, sparse, tt, n_, TAU, tv_filter,
                     reverb, colored, curve, voice, Mix, midi, note, sine, tri, saw)
from sfx_doors import creak, wood_hit
from sfx_steps import step_erde, step_kies

M = 'SFX/Monster'
S = 'SFX/Spieler'


def knock(r, f=None, amp=1.0, room=True):
    """Ein Fingerknochen-Klopfen auf eine Holztuer."""
    f = f or r.uniform(165, 215)
    # Fingerknochen auf Holz: dumpfer Koerperschlag, schwach angeregte Moden, kaum Klingeln
    return nw.hit(f, 0.17, r, 0.32, sec=0.35, n=10, ratio_pow=1.4, inharm=0.22, thud=0.85, air=0.35) * amp


# --------------------------------------------------------------------------- Klopfen / Kratzen / Knarren

@sound(M, 'klopfen_gast_dreimal', n=3, desc='Der Gast klopft immer dreimal: ruhig, gleichmaessig, geduldig', peak=-5)
def klopfen_gast(r, i):
    gap = r.uniform(0.62, 0.78)
    f = r.uniform(170, 200)
    parts = [(knock(r, f, 1.0 - 0.05 * k), 1.0, k * gap) for k in range(3)]
    return reverb(layer(*parts), r, 0.35, 0.1, 3500)


@sound(M, 'klopfen_einzeln', n=4, desc='Einzelnes Klopfen an Tuer (Besucher, Gegensprech)', peak=-6)
def klopfen_einzeln(r, i):
    return reverb(knock(r), r, 0.3, 0.1, 3500)


@sound(M, 'klopfen_flehend', n=3, desc='Echte Bewohner flehen um Einlass: hastig, unregelmaessig, wird lauter', peak=-4)
def klopfen_flehend(r, i):
    parts, t = [], 0.0
    k = r.integers(9, 14)
    for j in range(k):
        parts.append((knock(r, r.uniform(150, 230), 0.5 + 0.5 * j / k), 1.0, t))
        t += r.uniform(0.12, 0.4) * (1.0 - 0.4 * j / k)
    return reverb(layer(*parts), r, 0.4, 0.1, 3500)


@sound(M, 'klopfen_starr', n=2, desc='Monster-Klon: Klopfen starr wie ein Metronom, jedes Klopfen identisch', peak=-6)
def klopfen_starr(r, i):
    k1 = knock(r, 185, 1.0)
    return reverb(layer(*[(k1, 1.0, j * 0.9) for j in range(6)]), r, 0.35, 0.1, 3500)


@sound(M, 'fenster_pochen', n=3, desc='Pochen am Fensterglas von aussen', peak=-8)
def fenster_pochen(r, i):
    parts = []
    for j in range(r.integers(1, 4)):
        f = r.uniform(900, 1600)
        g = nw.hit(f, 0.12, r, 0.6, sec=0.25, n=8, ratio_pow=1.3, inharm=0.2, air=0.5)
        parts.append((g, 1.0, j * r.uniform(0.35, 0.6)))
    return reverb(layer(*parts), r, 0.25, 0.08, 5000)


@sound(M, 'kratzen_holz', sr=22050, n=4, desc='Warnstufe 1: Krallen kratzen langsam ueber Holz (Tuer, Laden)', peak=-8)
def kratzen_holz(r, i):
    parts, t = [], 0.0
    for j in range(r.integers(2, 5)):
        d = r.uniform(0.45, 0.9)
        n = n_(d)
        grain = np.clip(1.0 + 0.9 * lp(r.standard_normal(n), 90, 1) / 0.4, 0, 2.2)
        src = white(d, r) * grain * np.sin(np.pi * tt(d) / d) ** 0.8
        y = tv_filter(src, lambda u: r.uniform(1200, 1400) + 1800 * u, 1.4)
        parts.append((y, 1.0, t))
        parts.append((click(0.02, 400, 2000, 0.005, r), 0.4, t + r.uniform(0, d)))
        t += d + r.uniform(0.2, 0.7)
    return reverb(layer(*parts), r, 0.3, 0.08, 4000)


@sound(M, 'kratzen_glas', n=2, desc='Krallen quietschen ueber Fensterglas', peak=-9)
def kratzen_glas(r, i):
    d = 1.1
    t = tt(d)
    f = 2800 + 1400 * np.sin(TAU * 3.0 * t) * (t / d) + 600 * lp(r.standard_normal(len(t)), 20, 1)
    y = nw.square(f, duty=0.15) * np.sin(np.pi * t / d) ** 1.5
    return reverb(tv_filter(y, lambda u: 3000 + 800 * u, 3), r, 0.3, 0.1, 6000)


@sound(M, 'knarren_dielen', n=4, desc='Dielen knarren (jemand im Haus / auf der Veranda)', peak=-9)
def knarren_dielen(r, i):
    c = creak(r.uniform(0.5, 0.9), r.uniform(60, 90), r.uniform(100, 150), r, 0.7, (180, 480), 3.0)
    return reverb(layer((c, 0.7), (wood_hit(r.uniform(90, 130), 0.3, r, 0.35, 0.8), 1.0, 0.0)), r, 0.4, 0.1, 2500)


@sound(M, 'knarren_gebaelk', sr=22050, n=3, desc='Dachbalken knacken und knarren, langsam (Nachtbelagerung)', peak=-10)
def knarren_gebaelk(r, i):
    c = creak(r.uniform(1.4, 2.4), r.uniform(35, 55), r.uniform(60, 90), r, 0.9, (120, 360), 3.0)
    snap = modal([r.uniform(140, 200), r.uniform(430, 600)], [0.6, 0.3], [0.06, 0.04], 0.12)
    return reverb(layer((c, 0.7), (snap, 0.7, r.uniform(0.2, 1.0))), r, 0.6, 0.15, 2500)


@sound(M, 'kerze_flackert', sr=22050, n=3, desc='Warnstufe 1: Kerze flackert, kleines Zischen und Pusten', peak=-12)
def kerze_flackert(r, i):
    d = 1.6
    n = n_(d)
    flutter = np.clip(0.4 + lp(r.standard_normal(n), 22, 1) / 0.5, 0, 1.5)
    air = hp(white(d, r), 2500) * flutter * (0.5 + 0.5 * np.sin(np.pi * tt(d) / d))
    pops = hp(sparse(d, 12, r), 3500) * 2
    return layer((air, 0.35), (pops, 0.5), (lp(white(d, r), 300) * flutter * 0.05, 1.0))


@sound(M, 'kerze_erlischt', n=2, desc='Kerze wird ausgeblasen: Puff, Docht zischt', peak=-10)
def kerze_aus(r, i):
    puff = bp(white(0.25, r), 300, 4000) * env_ar(0.25, 0.01, 0.06)
    sizz = hp(white(0.8, r), 3500) * env_ar(0.8, 0.05, 0.25)
    return layer((puff, 1.0), (sizz, 0.3, 0.1))


@sound(M, 'tatze_im_spalt', n=3, desc='Warnstufe 3: Holz splittert, eine Tatze schiebt sich durch den Spalt, Schleifen, tiefes Atmen', peak=-3)
def tatze(r, i):
    crack = layer((click(0.15, 400, 5000, 0.03, r), 1.0), (modal([r.uniform(120, 160), r.uniform(300, 420)], [1, 0.5], [0.25, 0.15], 0.5), 0.9),
                  (hp(sparse(0.3, 600, r), 2500) * np.exp(-tt(0.3) / 0.07), 0.5))
    drag = tv_filter(colored(1.3, r, 1.0) * np.sin(np.pi * tt(1.3) / 1.3) ** 0.7, lambda u: 220 + 380 * u, 1.5)
    br = lp(white(2.0, r), 160, 2) * (0.5 + 0.5 * np.sin(TAU * 0.45 * tt(2.0) - 1.0)) * np.sin(np.pi * tt(2.0) / 2.0)
    return reverb(layer((crack, 1.0), (drag, 0.5, 0.35), (br, 2.0, 0.2)), r, 0.45, 0.12, 2500)


@sound(M, 'tuer_wucht', n=3, desc='Monster wirft sich gegen die Tuer: schwerer Einschlag, Staub, Balken ächzt', peak=-2)
def tuer_wucht(r, i):
    hit = layer((thump(0.9, 70, 32, 0.22), 1.2), (modal([95, 160, 270, 450], [1, 0.7, 0.5, 0.3], [0.5, 0.35, 0.2, 0.12], 0.9), 0.8),
                (click(0.2, 300, 3500, 0.04, r), 0.9), (hp(sparse(0.6, 500, r), 2500) * np.exp(-tt(0.6) / 0.12), 0.35))
    return reverb(layer((hit, 1.0), (creak(0.6, 45, 70, r, 0.9, (150, 400), 3), 0.3, 0.1)), r, 0.7, 0.18, 2500)


@sound(M, 'aussen_schritte_nachts', sr=22050, n=3, desc='Dumpfe Schritte vor dem Haus, durch die Wand gehoert, langsam', peak=-12)
def aussen_schritte(r, i):
    parts, t = [], 0.0
    for j in range(r.integers(4, 8)):
        s = step_kies(r, j) if r.random() < 0.5 else step_erde(r, j)
        parts.append((lp(s, 700, 2), 1.0, t))
        t += r.uniform(0.7, 1.15)
    return layer(*parts)


@sound(M, 'fluestern', sr=22050, n=4, desc='Fluestern ohne Worte (Sanity sinkt): Sibilanten mit Silbenrhythmus', peak=-12)
def fluestern(r, i):
    d = r.uniform(2.0, 3.2)
    n = n_(d)
    out = np.zeros(n)
    t = 0.0
    while t < d - 0.3:
        L = r.uniform(0.09, 0.28)
        w = white(L, r)
        f1, f2 = r.uniform(400, 900), r.uniform(1400, 2600)
        syl = resonate_pair(w, f1, f2)
        sib = hp(white(L, r), 4500) * (r.random() < 0.5) * 0.7
        seg = (syl + sib) * np.sin(np.pi * tt(L) / L) ** 1.5
        k = int(t * nw.SR)
        out[k:k + len(seg)] += seg[:n - k]
        t += L + r.uniform(0.02, 0.18)
    return reverb(out, r, 0.6, 0.35, 5000)


def resonate_pair(x, f1, f2):
    return nw.resonate(x, f1, 5) + 0.7 * nw.resonate(x, f2, 6)


@sound(M, 'knurren', sr=22050, n=3, desc='Tiefes Knurren (Gast/Hausfrau enthuellt, kurz vor dem Angriff)', peak=-4)
def knurren(r, i):
    d = r.uniform(1.2, 1.8)
    t = tt(d)
    f0 = 55 + 12 * np.sin(TAU * 1.5 * t) + 20 * (t / d)
    y = voice(f0, d, [(260, 5, 1.0), ((700, 520), 4, 0.6), (1500, 4, 0.2)], r, breath=0.2, jit=0.06, kind='square')
    wob = 0.65 + 0.35 * np.sin(TAU * 18 * t)
    return reverb(y * wob * np.sin(np.pi * t / d) ** 0.6, r, 0.4, 0.1, 2500)


@sound(M, 'fauchen', n=2, desc='Zischendes Fauchen mit rauem Kern (Enthuellung)', peak=-5)
def fauchen(r, i):
    d = 0.9
    y = tv_filter(white(d, r), lambda u: 5500 - 2500 * u, 1.2) * env_ar(d, 0.05, 0.3)
    core = voice(110, d, [(900, 4, 1.0), (2200, 4, 0.5)], r, breath=0.3, jit=0.08) * env_ar(d, 0.05, 0.35)
    return reverb(layer((y, 0.8), (core, 0.5)), r, 0.4, 0.1, 5000)


@sound(M, 'enthuellung_dumpf', n=1, desc='Enthuellung Teil 1: Ton wird dumpf, Herzschlag, Druck (Kamera geht nah)', peak=-5)
def enthuellung_dumpf(r, i):
    d = 2.6
    t = tt(d)
    sw = lp(colored(d, r, 2.0), 140, 2) * np.minimum(1, t / 1.6)
    hb = layer((thump(0.3, 70, 42, 0.07), 1.0), (thump(0.3, 60, 38, 0.06), 0.7, 0.26))
    parts = [(hb, 0.9 + 0.3 * k / 4.0, 0.2 + k * (0.62 - 0.07 * k)) for k in range(4)]
    air = lp(white(d, r), 220, 2) * 0.3 * np.minimum(1, t / 2.0)
    return layer((sw, 1.4), (air, 1.0), *parts)


@sound(M, 'enthuellung_grinsen', n=2, desc='Enthuellung Teil 2: das Grinsen. Schriller Dissonanzakkord, Schlag, Stille danach', peak=-4)
def enthuellung_grinsen(r, i):
    d = 2.4
    t = tt(d)
    notes = [midi(note('E6')), midi(note('F6')), midi(note('A#5')), midi(note('B5'))]
    ch = sum(sine(f, d) * np.exp(-t / 0.9) for f in notes) * (0.1 + 0.9 * np.minimum(1, t / 0.02))
    shriek = nw.square(np.linspace(2100, 1500, len(t)) * (1 + 0.02 * np.sin(TAU * 40 * t)), duty=0.2) * np.exp(-t / 0.18)
    boom = thump(d, 85, 30, 0.35)
    return reverb(layer((ch, 0.5), (shriek, 0.35), (boom, 1.3), (click(0.05, 800, 7000, 0.01, r), 0.8)), r, 1.4, 0.25, 6000)


@sound(M, 'enthuellung_komplett', n=1, desc='Enthuellung komplett: dumpf -> Grinsen (ca. 5 s), fertig zum Abspielen', peak=-3)
def enthuellung_komplett(r, i):
    a = enthuellung_dumpf(r, 0)
    b = enthuellung_grinsen(r, 0)
    return layer((a / (np.max(np.abs(a)) + 1e-9), 0.8), (b / (np.max(np.abs(b)) + 1e-9), 1.0, 2.5))


@sound(M, 'grinsen_tuerspion', n=2, desc='Tuerspion: Silhouette, das 2-3 Pixel breite Grinsen - kurzer kalter Schimmer, kein Schlag', peak=-9)
def grinsen_tuerspion(r, i):
    d = 2.2
    t = tt(d)
    y = (sine(2349, d) + 0.8 * sine(2489 + 12 * i, d) + 0.4 * sine(3136, d))
    e = np.sin(np.pi * np.clip(t / d, 0, 1)) ** 2
    return reverb(y * e * (1 + 0.3 * np.sin(TAU * 5.5 * t)), r, 1.0, 0.3, 7000)


@sound(M, 'hausfrau_summt', sr=22050, n=2, desc='Die Hausfrau summt ein Lied, das niemand im Dorf kennt: Wiegenlied, leicht verstimmt', peak=-8)
def hausfrau_summt(r, i):
    # a-Moll-Wiegenlied; jede zweite Note ein Viertelton zu tief
    mel = 'E5:1 D5:.5 C5:.5 D5:1 A4:1.5 R:.5 E5:1 F5:.5 E5:.5 D5:1 B4:1.5 R:.5 C5:1 D5:.5 E5:.5 A5:1.5 G5:.5 E5:2'
    bpm = 58 + 6 * i
    spb = 60.0 / bpm
    line = nw.parse(mel)
    total = sum(b for _, b in line) * spb + 1.0
    out = np.zeros(n_(total))
    t = 0.0
    for k, (m, b) in enumerate(line):
        if m is not None:
            f = midi(m) * (2 ** (-0.5 / 12) if k % 2 == 1 else 1.0)
            d = b * spb * 0.95
            y = voice(vibrato_f(f, d, r), d, [(480, 6, 1.0), (1050, 6, 0.5), (2500, 6, 0.1)], r, breath=0.04, jit=0.012)
            y = y * nw.adsr(d, 0.08, 0.1, 0.8, 0.12)
            kk = int(t * nw.SR)
            out[kk:kk + len(y)] += y[:len(out) - kk]
        t += b * spb
    return reverb(out, r, 1.2, 0.3, 4500)


def vibrato_f(f, d, r):
    return nw.vibrato(f, d, 5.0, 0.012, r, delay=0.15)


@sound(M, 'gast_zaehlt', sr=22050, n=2, desc='Der Gast zaehlt laut vor sich hin: rhythmisches, tonloses Murmeln, sieben Silben', peak=-9)
def gast_zaehlt(r, i):
    out = np.zeros(n_(6.0))
    t = 0.2
    for k in range(7):
        L = r.uniform(0.18, 0.3)
        f = 108 + 4 * k
        y = voice(f * (1 + 0.04 * np.sin(TAU * 6 * tt(L))), L, [((400 + 40 * k, 600), 6, 1.0), (1200, 6, 0.4)], r, breath=0.5, jit=0.02)
        y *= np.sin(np.pi * tt(L) / L)
        kk = int(t * nw.SR)
        out[kk:kk + len(y)] += y
        t += 0.78 + r.uniform(-0.03, 0.03)
    return reverb(out, r, 0.7, 0.3, 4000)


# --------------------------------------------------------------------------- Spieler: Koerper

def _breath_cycle(period, r, depth=1.0, rough=0.0, tone=(350, 2500)):
    """Ein Atemzug (ein + aus) als Noise-Huellkurve."""
    n = n_(period)
    t = np.arange(n) / n
    ein = np.where(t < 0.42, np.clip(np.sin(np.pi * t / 0.42), 0, 1) ** 1.4, 0)
    aus = np.where((t >= 0.5) & (t < 0.95), np.clip(np.sin(np.pi * (t - 0.5) / 0.45), 0, 1) ** 1.2, 0) * 0.8
    e = (ein + aus) * depth
    w = white(period, r)
    y = bp(w, tone[0], tone[1], 2) * e
    if rough:
        y *= 1.0 + rough * np.sin(TAU * 38 * np.arange(n) / nw.SR + 1)
    return y


def _breath_loop(r, period, count, depth, rough, tone):
    n = n_(period * count)
    out = np.zeros(n)
    for k in range(count):
        c = _breath_cycle(period * (1 + 0.04 * r.uniform(-1, 1)), r, depth * r.uniform(0.9, 1.0), rough, tone)
        a = int(k * period * nw.SR)
        out[a:a + len(c)] += c[:n - a]
    return out


@sound(S, 'atem_stufe3_ruhig', sr=22050, loop=True, n=1, desc='Atem bei 3/3 Leben: ruhig, kaum hoerbar (Loop, 4 Zuege)', peak=-24)
def atem3(r, i):
    return _breath_loop(r, 4.4, 4, 0.5, 0.0, (300, 1800))


@sound(S, 'atem_stufe2_unruhig', sr=22050, loop=True, n=1, desc='Atem bei 2/3 Leben: schneller, hoerbar, leicht zittrig (Loop)', peak=-18)
def atem2(r, i):
    return _breath_loop(r, 2.4, 6, 0.8, 0.25, (350, 2800))


@sound(S, 'atem_stufe1_keuchend', sr=22050, loop=True, n=1, desc='Atem bei 1/3 Leben: keuchend, pfeifend, mit Herzschlag - die Schwaeche, die das Audio zeigt (Loop)', peak=-12)
def atem1(r, i):
    b = _breath_loop(r, 1.6, 9, 1.0, 0.4, (400, 3500))
    wheeze = sine(1650 + 120 * np.sin(TAU * 0.6 * tt(14.4)), 14.4) * 0.03 * (np.abs(b) > 0.05)
    hb = _heart(14.4, 112, r, 0.7)
    return layer((b, 1.0), (wheeze, 1.0), (hb, 0.5))


def _heart(sec, bpm, r, amp=1.0):
    m = Mix(sec, loop=True)
    spb = 60.0 / bpm
    lub = thump(0.3, 72, 42, 0.07)
    dub = thump(0.25, 62, 38, 0.06) * 0.7
    for k in range(int(sec / spb + 0.5)):
        m.add(lub, k * spb, amp)
        m.add(dub, k * spb + 0.27 * spb, amp)
    return lp(m.buf, 160, 2, circ=True)


@sound(S, 'herzschlag_ruhig', sr=22050, loop=True, desc='Herzschlag 62 bpm (Loop, 6 Schlaege)', peak=-14)
def hb_slow(r, i):
    return _heart(60.0 / 62 * 6, 62, r)


@sound(S, 'herzschlag_schnell', sr=22050, loop=True, desc='Herzschlag 118 bpm bei Gefahr/Kampf (Loop)', peak=-10)
def hb_fast(r, i):
    return _heart(60.0 / 118 * 12, 118, r)


@sound(S, 'luftholen_schreck', n=3, desc='Erschrecktes Einatmen (Fund, Grinsen, Klopfen)', peak=-8)
def gasp(r, i):
    d = 0.45
    y = tv_filter(white(d, r), lambda u: 900 + 2400 * u, 1.2) * np.sin(np.pi * tt(d) / d) ** 0.8
    return y


@sound(S, 'seufzen', n=2, desc='Erschoepftes Ausatmen / Seufzen (Rast, Bank, Bett)', peak=-12)
def seufzen(r, i):
    d = 1.3
    return tv_filter(white(d, r), lambda u: 1800 - 1000 * u, 1.0) * np.sin(np.pi * tt(d) / d) ** 1.3


@sound(S, 'tod_dumpf', sr=22050, desc='Spieler stirbt: Schlag, Pfeifen, alles sinkt ins Dumpfe (ca. 6 s)', peak=-4)
def tod(r, i):
    d = 6.0
    t = tt(d)
    hit = layer((thump(0.8, 90, 36, 0.2), 1.3), (click(0.2, 300, 5000, 0.05, r), 0.8))
    ring = sine(3900, d) * np.exp(-t / 1.6) * 0.15 * np.minimum(1, t / 0.2)
    sink = lp(colored(d, r, 2.0), 110, 2) * np.minimum(1, t / 1.5) * np.exp(-t / 3.0)
    hb = _heart(d, 54, r, 0.8) * np.exp(-t / 1.5)
    return layer((hit, 1.0), (ring, 1.0), (sink, 1.5), (hb, 0.5, 0.3))


@sound(S, 'aufwachen_morgen', sr=22050, desc='Aufwachen im Bett nach dem Tod: Einatmen, Pfeifen blendet aus, Stoff, ferner Vogel (ca. 5 s)', peak=-8)
def aufwachen(r, i):
    d = 5.0
    t = tt(d)
    ring = sine(3300, d) * 0.12 * np.exp(-t / 1.4) * np.minimum(1, t / 0.3)
    breath = tv_filter(white(1.0, r), lambda u: 800 + 2000 * u, 1.2) * np.sin(np.pi * tt(1.0)) ** 1.2
    cloth = bp(white(1.2, r), 300, 3000) * env_ar(1.2, 0.2, 0.3)
    return layer((ring, 1.0), (breath, 0.6, 0.2), (cloth, 0.5, 1.2), (lp(white(d, r), 400, 2) * 0.01 * t / d, 1.0))


@sound(S, 'einschlafen', sr=22050, desc='Einschlafen: Stoff, tiefes Ausatmen, Klang sinkt (ca. 5 s)', peak=-12)
def einschlafen(r, i):
    d = 5.0
    cloth = bp(white(1.5, r), 250, 2500) * env_ar(1.5, 0.15, 0.4)
    br = _breath_loop(r, 3.2, 2, 0.6, 0.0, (250, 1400))[:n_(5.0)]
    br = np.concatenate([br, np.zeros(n_(5.0) - len(br))]) * np.exp(-tt(5.0) / 3.0)
    return layer((cloth, 0.6), (br, 1.0, 0.0))
