"""Ambience-Loops (20 s, 22,05 kHz, mono, nahtlos). Bausteine: Wind, Voegel, Grillen, Regen, Feuer, Wasser, Murmeln, Uhr.
Zonen laut Level-Plan: Dorf (Tag/Daemmerung/Nacht), Waldrand/Wald/Tiefwald, Friedhof, Landstrasse, Innenraeume
(Haus, Bar, Revier, Villa, Kapelle), Erdbau (Monster-Schlafplatz), Warnstufen 1-3 der Nachtbelagerung.
Keine Netzbrumm-Geraeusche in Innenraeumen: 1910, Oel/Kerze/Ofen, kein Strom."""
import numpy as np

import nwaudio as nw
from nwaudio import (sound, white, bp, lp, hp, thump, env_ar, modal, click, layer, sparse, tt, n_, TAU, tv_filter,
                     reverb, colored, voice, sine, midi, note, Mix, multi_gust)
import sfx_monster as mon
import sfx_world as wld
import sfx_doors as door
import sfx_items as itm
import voices as vc

A = 'Ambience'
D = 20.0
SRA = 22050


# --------------------------------------------------------------------------- Bausteine

def gusts(d, r, rate=0.25, depth=0.7):
    x = lp(r.standard_normal(n_(d)), rate, 1, circ=True)
    x = x / (np.std(x) + 1e-9)
    return np.clip(1.0 + depth * x, 0.05, 2.6)


def wind(d, r, lo=80, hi=800, level=1.0, rate=0.22, depth=0.8, power=1.0):
    """Wind: rosa-braunes Rauschen, dessen Helligkeit mit der Boe steigt (Boeen sind heller und lauter), mehrere Boen-Skalen."""
    g = multi_gust(d, r, (rate * 0.3, rate, rate * 4.0), (1.0, 0.7, 0.35))
    g = 1.0 + depth * (g - 1.0)
    g = np.clip(g, 0.3, 3.0)
    base = colored(d, r, 1.2 + 0.4 * power)
    fc = lo * 2 + (hi - lo * 2) * np.clip(g / 2.2, 0, 1) ** 1.3
    y = tv_filter(base, fc, 1.0, 'lp', circ=True)
    y = hp(y, lo, 2, circ=True)
    flutter = 1.0 + 0.12 * nw.smooth_rand(d, r, 9.0)
    return y * g ** 1.25 * flutter * level


def whistle(d, r, f=700, level=0.2):
    """Pfeifen an Kanten: zwei schmale, langsam wandernde Baender, nur in Boeen hoerbar."""
    g = multi_gust(d, r, (0.08, 0.3, 1.0), (1.0, 0.8, 0.4))
    out = np.zeros(n_(d))
    for k, ratio in enumerate((1.0, 1.51)):
        drift = nw.smooth_rand(d, r, 0.35)
        fc = f * ratio * (1 + 0.12 * drift)
        out += tv_filter(white(d, r), fc, 14.0, 'bp', circ=True) * (0.7 if k else 1.0)
    return out * np.clip(g - 0.6, 0, None) ** 1.6 * level


def vogel_note(r, f0, f1, d, shape='glide', warble=0.0, harm=(1.0, 0.32, 0.1), noise=0.015):
    t = tt(d)
    u = t / d
    if shape == 'arc':
        f = f0 + (f1 - f0) * np.sin(np.pi * u)
    elif shape == 'fall':
        f = f0 * (1.0 - 0.35 * u ** 0.7)
    else:
        f = f0 + (f1 - f0) * u
    if warble:
        f = f * (1.0 + warble * np.sin(TAU * r.uniform(25, 60) * t))
    ph = np.cumsum(f) / nw.SR
    y = sum(h * np.sin(TAU * (k + 1) * ph) for k, h in enumerate(harm))
    env = np.sin(np.pi * np.clip(u, 0, 1)) ** 0.6 * (1.0 - 0.25 * u)
    return (y + noise * white(d, r)) * env


def bird(r, kind=None):
    kind = kind or r.choice(['tweet', 'trill', 'whistle', 'finch', 'dove', 'cheep'])
    f = r.uniform(2300, 4600)
    shapes = ['glide', 'arc', 'fall']
    if kind == 'tweet':
        k = int(r.integers(2, 5))
        out = Mix(0.14 * k + 0.1)
        t = 0.0
        for j in range(k):
            d = r.uniform(0.05, 0.11)
            a = f * r.uniform(0.85, 1.2)
            out.add(vogel_note(r, a, a * r.uniform(0.75, 1.35), d, shapes[int(r.integers(0, 3))], warble=r.choice([0, 0.02])), t)
            t += d + r.uniform(0.02, 0.07)
        y = out.buf * 0.5
    elif kind == 'trill':
        k = int(r.integers(10, 20))
        out = Mix(k * 0.035 + 0.1)
        t = 0.0
        for j in range(k):
            fj = f * (1.0 - 0.012 * j)
            out.add(vogel_note(r, fj * 1.05, fj * 0.95, 0.028, 'glide', harm=(1.0, 0.2)), t, 1.0 - 0.015 * j)
            t += 0.032 + 0.0006 * j
        y = out.buf * 0.4
    elif kind == 'whistle':
        a = f * 0.7
        y = np.concatenate([vogel_note(r, a * 1.15, a * 0.9, 0.34, 'fall', 0.006, (1.0, 0.15)), np.zeros(n_(0.06)),
                            vogel_note(r, a * 1.05, a * 0.8, 0.42, 'fall', 0.008, (1.0, 0.12))]) * 0.45
    elif kind == 'finch':
        k = int(r.integers(7, 13))
        out = Mix(k * 0.09 + 0.15)
        t = 0.0
        step = r.uniform(0.07, 0.1)
        for j in range(k):
            a = f * r.uniform(0.8, 1.4)
            d = r.uniform(0.03, 0.075)
            out.add(vogel_note(r, a, a * r.uniform(0.7, 1.4), d, shapes[int(r.integers(0, 3))]), t, r.uniform(0.6, 1.0))
            t += step * (0.97 ** j) + r.uniform(0, 0.02)
        y = out.buf * 0.4
    elif kind == 'cheep':
        k = int(r.integers(2, 6))
        out = Mix(0.16 * k + 0.1)
        for j in range(k):
            a = f * 0.95
            out.add(vogel_note(r, a, a * 1.3, 0.05, 'glide', harm=(1.0, 0.5, 0.25), noise=0.05), j * r.uniform(0.12, 0.2), r.uniform(0.7, 1.0))
        y = out.buf * 0.4
    else:  # dove
        out = Mix(1.5)
        for dd, st in ((0.3, 0.0), (0.5, 0.36), (0.38, 1.0)):
            t = tt(dd)
            f0 = r.uniform(430, 520)
            fr = f0 * (1 + 0.04 * np.sin(TAU * 5.5 * t) - 0.06 * t / dd)
            y0 = (np.sin(TAU * np.cumsum(fr) / nw.SR) + 0.18 * np.sin(TAU * 2 * np.cumsum(fr) / nw.SR)) * np.sin(np.pi * t / dd) ** 1.2
            out.add(y0 + 0.03 * lp(white(dd, r), 900, 1) * np.sin(np.pi * t / dd), st)
        y = out.buf * 0.3
    return nw.resonate(y, f * 1.15, 1.2) * 0.8 + y * 0.4


def birds(d, r, rate, kinds=None, level=1.0, pool=(0.4, 1.0)):
    m = Mix(d, loop=True)
    for _ in range(int(r.poisson(rate * d))):
        s = bird(r, r.choice(kinds) if kinds else None)
        dist = r.uniform(0.0, 1.0)  # Entfernung: nah = hell und laut, fern = dumpf, leiser, mehr Hall
        s = lp(s, 8000 - 4500 * dist, 1) * (pool[0] + (pool[1] - pool[0]) * (1 - dist))
        s = reverb(s, r, 0.5 + 0.8 * dist, 0.1 + 0.3 * dist, 6000)
        m.add(s, r.uniform(0, d), level)
    return m.buf


def crickets(d, r, n=6, level=1.0, active=0.75):
    """Grillen: pro Tier Gruppen aus 3-5 kurzen Pulsen, eigene Tonhoehe/Takt, Phrasen die an- und ausgehen."""
    m = Mix(d, loop=True)
    for _ in range(n):
        f = r.uniform(4000, 5400)
        per = r.uniform(0.35, 0.75)
        npulse = int(r.integers(3, 6))
        gap = r.uniform(0.017, 0.03)
        a = r.uniform(0.3, 1.0)
        t = r.uniform(0, per)
        on = True
        while t < d:
            if r.random() < (1.0 - active) * 0.3:
                on = not on
            if on:
                unit = Mix(per)
                for j in range(npulse):
                    pl = r.uniform(0.007, 0.012)
                    tp = tt(pl)
                    fj = f * (1.0 + 0.012 * j)
                    pulse = np.sin(TAU * fj * tp) + 0.12 * np.sin(TAU * 2 * fj * tp)
                    unit.add(pulse * np.hanning(len(tp)), j * gap, 0.6 + 0.4 * (j + 1) / npulse)
                m.add(unit.buf, t, a * level * r.uniform(0.7, 1.0))
            t += per * r.uniform(0.9, 1.12)
    return lp(m.buf, 6500, 1, circ=True)


def _knister(r):
    """Ein einzelnes Knistern des Feuers: Tick, Snap, Pop oder Raspeln, jeweils mit eigener Farbe."""
    k = r.random()
    if k < 0.55:                                  # Tick
        d = r.uniform(0.0015, 0.004)
        lo = r.uniform(1500, 4500)
        return bp(white(d, r), lo, lo * r.uniform(1.8, 3.0), 1) * np.hanning(n_(d)) * 3.0
    if k < 0.80:                                  # Snap mit kleinem Holzkoerper
        return nw.hit(r.uniform(500, 2400), r.uniform(0.012, 0.045), r, 0.9, sec=0.07, n=5, air=0.6)
    if k < 0.90:                                  # Pop: dumpf
        return layer((nw.thump(0.1, r.uniform(220, 480), 110, 0.02), 0.8), (nw.bp(white(0.01, r), 1200, 5000) * np.hanning(n_(0.01)), 1.0))
    out = np.zeros(n_(0.09))                      # Raspeln: viele Mini-Ticks
    for _ in range(int(r.integers(4, 10))):
        t0 = int(r.uniform(0, 0.07) * nw.SR)
        tick = bp(white(0.0018, r), 2500, 7000, 1) * np.hanning(n_(0.0018)) * r.uniform(0.3, 1.0)
        out[t0:t0 + len(tick)] += tick[:len(out) - t0]
    return out * 3.0


def fire(d, r, level=1.0, density=26, big=3.5):
    """Feuer: Grundrauschen (Roar) + Flammenhauch + Zischen, alle ueber dieselbe Flacker-Huellkurve, dazu Knister-Ereignisse
    in Schueben (Kettenreaktionen), Staerke log-normal verteilt (viele leise, wenige laute)."""
    g = np.clip(multi_gust(d, r, (0.15, 0.6, 2.5), (1.0, 0.8, 0.6)), 0.6, 2.2)
    roar = bp(colored(d, r, 1.7), 45, 450, 2, circ=True) * g ** 0.9
    whoosh = bp(colored(d, r, 1.0), 450, 2400, 2, circ=True) * g ** 1.4 * 0.32
    hiss = nw.grain_noise(d, r, 3500, 9500, 150.0, 2.0) * g ** 1.8 * 0.09
    m = Mix(d, loop=True)
    base = r.uniform(0, d, int(r.poisson((density * 0.55 + big) * d)))
    times = list(base)
    for t0 in base:
        if r.random() < 0.4:
            for _ in range(int(r.integers(1, 4))):
                times.append(t0 + r.uniform(0.004, 0.07))
    for t0 in times:
        a = float(np.clip(r.lognormal(-0.8, 0.9), 0.05, 2.5))
        m.add(_knister(r), t0 % d, a)
    return (roar * 0.6 + whoosh + hiss + m.buf * 0.75) * level


def rain(d, r, level=1.0, roof=False):
    """Regen: gekoernte Rauschbaender (viele kleine Tropfen) + einzelne groessere Tropfen mit Plink + tiefes Grundrauschen."""
    bed = (nw.grain_noise(d, r, 700, 2600, 450.0, 1.5) * 0.45 + nw.grain_noise(d, r, 2600, 6000, 700.0, 2.0) * 0.5
           + nw.grain_noise(d, r, 6000, 10000, 1000.0, 2.5) * 0.3)
    m = Mix(d, loop=True)
    for _ in range(int(40 * d * level)):
        f = float(np.exp(r.uniform(np.log(700), np.log(2800))))
        m.add(nw.bubble(f), r.uniform(0, d), float(np.clip(r.lognormal(-1.2, 0.6), 0.05, 0.8)))
    for _ in range(int(160 * d * level)):
        dd = r.uniform(0.002, 0.006)
        lo = r.uniform(1500, 5000)
        m.add(bp(white(dd, r), lo, lo * 2.2, 1) * np.hanning(n_(dd)), r.uniform(0, d), float(np.clip(r.lognormal(-0.6, 0.7), 0.05, 2.0)) * 2.5)
    out = bed * 0.5 + m.buf * 0.35 + lp(colored(d, r, 1.5), 300, 2, circ=True) * 0.2
    if roof:
        out = lp(out, 3200, 2, circ=True) * 0.6
        t = Mix(d, loop=True)
        for _ in range(int(80 * d * level)):
            t.add(nw.hit(r.uniform(150, 420), 0.07, r, 0.6, sec=0.12, n=6), r.uniform(0, d), float(np.clip(r.lognormal(-1.5, 0.7), 0.05, 0.7)))
        out = out + t.buf * 0.7 + lp(colored(d, r, 2.0), 200, 2, circ=True) * 0.25
    return out * level


def water(d, r, level=1.0, dense=160):
    """Wasser: Fluss-Rauschen + dichter Teppich aus Minnaert-Blasen (Tonhoehe ~ 1/Groesse, steigt waehrend des Abklingens)."""
    flow = bp(colored(d, r, 0.8), 300, 5000, 2, circ=True) * multi_gust(d, r, (0.3, 1.5, 6.0), (1.0, 0.7, 0.5)) * 0.12
    m = Mix(d, loop=True)
    for _ in range(int(dense * d)):
        f = float(np.exp(r.uniform(np.log(450), np.log(3600))))
        m.add(nw.bubble(f), r.uniform(0, d), float(np.clip(r.lognormal(-1.3, 0.7), 0.03, 0.9)))
    return (flow + m.buf * 0.55) * level


def murmur(d, r, level=1.0, rate=7.0, near=False):
    m = Mix(d, loop=True)
    who = ['dorfbewohner_m', 'dorfbewohner_w', 'mara', 'david', 'ilhan', 'veronica', 'can']
    for _ in range(int(rate * d)):
        b = vc.blip(who[int(r.integers(0, len(who)))], int(r.integers(0, 6)), r)
        m.add(b, r.uniform(0, d), r.uniform(0.2, 1.0))
    y = m.buf
    return lp(y, 2500 if near else 1400, 2, circ=True) * level


def clock(d, r, period=1.0, level=1.0):
    m = Mix(d, loop=True)
    k = int(d / period)
    for j in range(k):
        f = 1750 if j % 2 == 0 else 1520
        tk = layer((nw.hit(f * r.uniform(0.97, 1.03), 0.045, r, 0.95, sec=0.08, n=6, air=0.5), 1.0))
        m.add(tk, j * period + r.normal(0, 0.002), level * r.uniform(0.85, 1.0))
    return m.buf


def room(d, r, level=1.0, tone=250):
    return lp(colored(d, r, 2.0), tone, 2, circ=True) * gusts(d, r, 0.1, 0.2) * level


def scatter(m, r, fn, count, gain=(0.5, 1.0), post=None, margin=0.0):
    d = m.n / nw.SR
    for _ in range(int(count)):
        s = fn(r)
        if post:
            s = post(s)
        m.add(s, r.uniform(0, d - margin), r.uniform(*gain))
    return m


def far(x, fc=1100):
    """Entfernung: Hoehen weg, leiser."""
    return lp(x, fc, 2) * 0.6


def mix(*parts):
    return sum(p * g for p, g in parts)


# --------------------------------------------------------------------------- Dorf

@sound(A, 'amb_dorf_tag', sr=SRA, loop=True, desc='Dorf am Tag: leichter Wind, einzelne Voegel, fernes Hammern (Schmiede), Insekten', peak=-14)
def dorf_tag(r, i):
    m = Mix(D, loop=True)
    scatter(m, r, lambda r: lp(layer(*[(modal([2200, 3900], [0.5, 0.3], [0.5, 0.3], 0.7), 1.0, k * 0.28) for k in range(3)]), 4500, 2), 2, (0.1, 0.2))
    scatter(m, r, lambda r: far(door.wood_hit(r.uniform(140, 200), 0.3, r, 0.5, 0.5), 900), 3, (0.2, 0.4))
    return mix((wind(D, r, 80, 700, 1.0), 0.6), (birds(D, r, 1.1), 0.8), (m.buf, 1.0), (room(D, r, 1.0, 150), 0.2))


@sound(A, 'amb_dorf_daemmerung', sr=SRA, loop=True, desc='Dorf in der Daemmerung: Wind frischt auf, letzte Voegel, entfernt klappen Laeden und Riegel, Grillen beginnen', peak=-14)
def dorf_daem(r, i):
    m = Mix(D, loop=True)
    scatter(m, r, lambda r: far(door.tuer_schliessen(r, 0), 900), 3, (0.2, 0.4))
    scatter(m, r, lambda r: far(door.laden_zu(r, 0), 1000), 3, (0.2, 0.4))
    scatter(m, r, lambda r: far(door.riegel_zu(r, 0), 1000), 2, (0.2, 0.35))
    return mix((wind(D, r, 80, 900, 1.0, 0.25, 0.9), 0.75), (birds(D, r, 0.25), 0.5), (crickets(D, r, 3, 0.4), 0.5), (m.buf, 1.0))


@sound(A, 'amb_dorf_nacht', sr=SRA, loop=True, desc='Dorf bei Nacht: Wind pfeift duenn, Grillen, Eule, fernes Knarren. Nichts bewegt sich - dieser Eindruck ist das Ziel', peak=-14)
def dorf_nacht(r, i):
    m = Mix(D, loop=True)
    scatter(m, r, lambda r: far(wld.eule(r, int(r.integers(0, 3))), 1800), 1, (0.2, 0.3))
    scatter(m, r, lambda r: far(mon.knarren_gebaelk(r, 0), 700), 2, (0.15, 0.3))
    return mix((wind(D, r, 60, 500, 0.8, 0.18, 0.9), 0.4), (whistle(D, r, 520, 1.0), 0.25), (crickets(D, r, 4, 0.5, 0.6), 0.5), (m.buf, 1.0),
               (lp(colored(D, r, 2.0), 70, 2, circ=True), 0.5))


@sound(A, 'amb_morgen', sr=SRA, loop=True, desc='Morgen (Lagebericht-Phase): Morgenchor der Voegel, sanfter Wind, ein ferner Karren', peak=-14)
def morgen(r, i):
    return mix((wind(D, r, 80, 600, 0.8), 0.55), (birds(D, r, 2.6, ['tweet', 'trill', 'finch', 'whistle'], 1.0), 0.9))


@sound(A, 'amb_beerdigung', sr=SRA, loop=True, desc='Dorfplatz bei der Beerdigung (Opening Step 9): gedaempftes Murmeln, Wind, ein Rabe, fernes Schluchzen als Atem', peak=-14)
def beerdigung(r, i):
    m = Mix(D, loop=True)
    scatter(m, r, lambda r: far(wld.rabe(r, int(r.integers(0, 5))), 2500), 1, (0.2, 0.35))
    scatter(m, r, lambda r: lp(mon.seufzen(r, int(r.integers(0, 2))), 1500, 2), 2, (0.15, 0.3))
    return mix((wind(D, r, 70, 600, 1.0, 0.2, 0.8), 0.5), (murmur(D, r, 1.0, 3.0), 0.5), (m.buf, 1.0))


@sound(A, 'amb_brunnen', sr=SRA, loop=True, desc='Dorfbrunnen / Wassertrog (Brunnen_Anim): Plaetschern und Tropfen', peak=-16)
def brunnen(r, i):
    return mix((water(D, r, 1.0, 140), 1.0), (wind(D, r, 80, 500, 0.5), 0.15))


@sound(A, 'amb_nebel_dumpf', sr=SRA, loop=True, desc='Nebel (VFX/Nebel): alles gedaempft, tiefe Stille mit weichem Wind', peak=-18)
def nebel(r, i):
    return mix((lp(colored(D, r, 1.5), 300, 2, circ=True), 0.7), (lp(wind(D, r, 50, 400, 1.0), 400, 2), 0.4), (lp(colored(D, r, 2.0), 60, 2, circ=True), 0.5))


# --------------------------------------------------------------------------- Wald

@sound(A, 'amb_wald_tag', sr=SRA, loop=True, desc='Waldrand am Tag: dichter Vogelgesang, Blaetterrauschen, ferner Astknacks', peak=-14)
def wald_tag(r, i):
    m = Mix(D, loop=True)
    scatter(m, r, lambda r: far(itm.ast(r, int(r.integers(0, 4))), 1500), 1, (0.15, 0.3))
    leaves = hp(wind(D, r, 600, 4000, 1.0, 0.3, 0.9, 0.5), 600, circ=True)
    return mix((wind(D, r, 80, 500, 0.8), 0.4), (leaves, 0.45), (birds(D, r, 2.0, None, 1.0), 0.9), (m.buf, 1.0))


@sound(A, 'amb_wald_nacht', sr=SRA, loop=True, desc='Waldrand bei Nacht: Wind in den Wipfeln, Grillen, Eule, vereinzeltes Knacken, Stille dazwischen', peak=-14)
def wald_nacht(r, i):
    m = Mix(D, loop=True)
    scatter(m, r, lambda r: far(wld.eule(r, int(r.integers(0, 3))), 2200), 1, (0.25, 0.4))
    scatter(m, r, lambda r: far(itm.ast(r, int(r.integers(0, 4))), 1200), 2, (0.2, 0.35))
    leaves = hp(wind(D, r, 500, 3000, 1.0, 0.2, 0.9, 0.5), 500, circ=True)
    return mix((wind(D, r, 60, 400, 1.0, 0.15, 0.9), 0.5), (leaves, 0.35), (crickets(D, r, 5, 0.6, 0.5), 0.5), (m.buf, 1.0))


@sound(A, 'amb_wald_tief', sr=SRA, loop=True, desc='Tiefer Wald (Zone 2+): keine Voegel, drueckende Stille, Holz knarrt, irgendwo atmet etwas Tiefes', peak=-15)
def wald_tief(r, i):
    m = Mix(D, loop=True)
    scatter(m, r, lambda r: far(mon.knarren_gebaelk(r, int(r.integers(0, 3))), 600), 2, (0.2, 0.4))
    scatter(m, r, lambda r: far(itm.ast(r, int(r.integers(0, 4))), 800), 1, (0.2, 0.3))
    scatter(m, r, lambda r: far(mon.fluestern(r, int(r.integers(0, 4))), 2500), 1, (0.08, 0.16))
    return mix((lp(colored(D, r, 2.0), 90, 2, circ=True), 0.9), (wind(D, r, 60, 350, 0.8, 0.12, 0.9), 0.3), (whistle(D, r, 380, 1.0), 0.18), (m.buf, 1.0))


@sound(A, 'amb_erdbau', sr=SRA, loop=True, desc='Erdbau am Waldrand (Schlafplatz des Gastes, unter der verkruepelten Birke): Tropfen im Hall, Wurzeln knarren, tiefer langsamer Atem', peak=-15)
def erdbau(r, i):
    m = Mix(D, loop=True)
    for _ in range(int(r.poisson(0.5 * D))):
        f = r.uniform(900, 1700)
        dd = 0.08
        m.add(sine(f * (1 + 1.5 * np.exp(-tt(dd) / 0.02)), dd) * np.exp(-tt(dd) / 0.02), r.uniform(0, D), r.uniform(0.3, 1.0))
    drips = reverb(m.buf, r, 2.0, 0.5, 4000, circ=True)
    breath = np.zeros(n_(D))
    for k in range(int(D / 6.0)):
        c = lp(white(6.0, r), 200, 2) * np.sin(np.pi * np.clip(tt(6.0) / 6.0, 0, 1)) ** 2 * 0.8
        a = int(k * 6.0 * nw.SR)
        breath[a:a + len(c)] += c[:len(breath) - a]
    mm = Mix(D, loop=True)
    scatter(mm, r, lambda r: far(door.creak(r.uniform(1.0, 2.0), 40, 70, r, 0.9, (100, 300), 3.0), 400), 2, (0.2, 0.4))
    return mix((drips, 0.6), (breath, 1.2), (mm.buf, 1.0), (lp(colored(D, r, 2.0), 60, 2, circ=True), 0.8))


@sound(A, 'amb_friedhof', sr=SRA, loop=True, desc='Friedhof am Dorfeingang (Sued): duenner Wind, Raben, ferne Kapellenglocke, Holzkreuze knarren', peak=-14)
def friedhof(r, i):
    m = Mix(D, loop=True)
    scatter(m, r, lambda r: far(wld.rabe(r, int(r.integers(0, 5))), 3000), 2, (0.15, 0.3))
    scatter(m, r, lambda r: far(door.creak(1.2, 90, 120, r, 0.8, (300, 900), 3.0), 900), 1, (0.2, 0.3))
    return mix((wind(D, r, 100, 900, 1.0, 0.2, 0.9), 0.4), (whistle(D, r, 640, 1.0), 0.2), (m.buf, 1.0), (birds(D, r, 0.2, ['dove'], 1.0), 0.5))


# --------------------------------------------------------------------------- Strasse (Opening)

@sound(A, 'amb_strasse_fahrt', sr=SRA, loop=True, desc='Opening Step 3, Landstrasse bei Fahrt: Fahrtwind, Reifen auf Asphalt, froehliche Voegel (Motor extra)', peak=-16)
def strasse_fahrt(r, i):
    tyre = bp(white(D, r), 150, 1200, 2, circ=True) * 0.25
    return mix((wind(D, r, 100, 1800, 1.0, 0.12, 0.3), 0.5), (tyre, 1.0), (birds(D, r, 0.8, ['tweet', 'finch'], 1.0), 0.3))


@sound(A, 'amb_strasse_still', sr=SRA, loop=True, desc='Opening Step 4, vor dem Baumstamm: Voegel verstummen, nur dumpfer Wind und eine unnatuerliche Stille', peak=-18)
def strasse_still(r, i):
    return mix((lp(wind(D, r, 60, 500, 1.0, 0.1, 0.6), 500, 2), 0.35), (lp(colored(D, r, 2.0), 70, 2, circ=True), 0.7), (whistle(D, r, 450, 1.0), 0.06))


# --------------------------------------------------------------------------- Innenraeume

@sound(A, 'amb_haus_tag', sr=SRA, loop=True, desc='Wohnhaus am Tag: Raumton, Uhr tickt, Holz knackt leise, Wind von aussen gedaempft', peak=-18)
def haus_tag(r, i):
    m = Mix(D, loop=True)
    scatter(m, r, lambda r: far(mon.knarren_dielen(r, int(r.integers(0, 4))), 800), 1, (0.1, 0.2))
    return mix((room(D, r, 1.0, 300), 0.5), (clock(D, r, 1.0, 1.0), 0.1), (lp(wind(D, r, 80, 500, 1.0), 450, 2), 0.15), (m.buf, 1.0))


@sound(A, 'amb_haus_nacht_schutz', sr=SRA, loop=True, desc='Im Schutzraum bei Nacht (Barrikade zu, Kerze): gedaempfter Wind, Uhr, Holz, Kerzenflattern, drueckende Ruhe', peak=-18)
def haus_nacht(r, i):
    m = Mix(D, loop=True)
    scatter(m, r, lambda r: mon.kerze_flackert(r, int(r.integers(0, 3))), 2, (0.15, 0.3))
    scatter(m, r, lambda r: far(mon.knarren_gebaelk(r, int(r.integers(0, 3))), 700), 2, (0.15, 0.3))
    return mix((room(D, r, 1.0, 220), 0.5), (clock(D, r, 1.0, 1.0), 0.1), (lp(wind(D, r, 60, 400, 1.0, 0.15, 0.9), 350, 2), 0.3), (m.buf, 1.0))


@sound(A, 'amb_kamin', sr=SRA, loop=True, desc='Kamin im Raum: Knistern, Rauschen der Glut, Holz setzt sich (Sanity-Regeneration, Lichtinsel)', peak=-16)
def kamin(r, i):
    return mix((fire(D, r, 1.0), 1.0), (room(D, r, 1.0, 250), 0.3))


@sound(A, 'amb_lagerfeuer', sr=SRA, loop=True, desc='Lagerfeuer im Freien: Knistern, Roar, Nachtwind (Lagerfeuer_Gross)', peak=-14)
def lagerfeuer(r, i):
    return mix((fire(D, r, 1.1, 30, 4.0), 1.0), (wind(D, r, 80, 600, 1.0), 0.2), (crickets(D, r, 2, 0.4), 0.2))


@sound(A, 'amb_bar_tag', sr=SRA, loop=True, desc='Ilhans Bar am Tag: gedaempftes Gemurmel, Glaeser, Stuehle, Ofenknistern', peak=-14)
def bar_tag(r, i):
    m = Mix(D, loop=True)
    scatter(m, r, lambda r: itm.abstellen(r, int(r.integers(0, 4))), 5, (0.15, 0.35))
    scatter(m, r, lambda r: itm.anstossen(r, int(r.integers(0, 3))), 1, (0.1, 0.2))
    scatter(m, r, lambda r: itm.stuhl(r, int(r.integers(0, 3))), 1, (0.1, 0.2))
    scatter(m, r, lambda r: itm.dart(r, int(r.integers(0, 3))), 2, (0.1, 0.25))
    return mix((murmur(D, r, 1.0, 6.0, True), 0.5), (m.buf, 1.0), (fire(D, r, 0.5), 0.3), (room(D, r, 1.0, 300), 0.3))


@sound(A, 'amb_bar_leer', sr=SRA, loop=True, desc='Bar fast leer (spaetes Licht): Ofen, Uhr, ein Glas klirrt leise, Wind ums Haus', peak=-18)
def bar_leer(r, i):
    m = Mix(D, loop=True)
    scatter(m, r, lambda r: itm.abstellen(r, int(r.integers(0, 4))), 1, (0.1, 0.2))
    return mix((fire(D, r, 0.5), 0.5), (clock(D, r, 1.0, 1.0), 0.1), (room(D, r, 1.0, 250), 0.4), (lp(wind(D, r, 60, 400, 1.0), 350, 2), 0.2), (m.buf, 1.0))


@sound(A, 'amb_revier', sr=SRA, loop=True, desc='Sheriff-Stube (Revier): Uhr, Kanonenofen, Papier, Talisman-Summen am Haken ("faint blue light")', peak=-17)
def revier(r, i):
    m = Mix(D, loop=True)
    scatter(m, r, lambda r: itm.papier(r, int(r.integers(0, 4))), 1, (0.1, 0.2))
    scatter(m, r, lambda r: itm.tasse(r, int(r.integers(0, 3))), 1, (0.1, 0.2))
    hum = (sine(np.full(n_(D), 392.0), D) + 0.6 * sine(np.full(n_(D), 588.7), D) + 0.3 * sine(np.full(n_(D), 784.0), D)) * 0.02
    return mix((room(D, r, 1.0, 260), 0.5), (clock(D, r, 1.0, 1.0), 0.14), (fire(D, r, 0.35), 0.3), (hum, 1.0), (m.buf, 1.0))


@sound(A, 'amb_villa', sr=SRA, loop=True, desc='Villa der Madame Elenora: grosse Halle, Standuhr tickt langsam, Kristall klirrt von selbst, kalter Zug', peak=-18)
def villa(r, i):
    m = Mix(D, loop=True)
    scatter(m, r, lambda r: modal([2637, 3951, 5274], [0.5, 0.3, 0.2], [1.5, 1.0, 0.7], 1.8), 2, (0.04, 0.09))
    tick = clock(D, r, 1.4, 1.0)
    return mix((reverb(room(D, r, 1.0, 200), r, 1.4, 0.3, 3500, circ=True), 0.8), (reverb(tick, r, 1.2, 0.2, 5000, circ=True), 0.12), (lp(wind(D, r, 60, 500, 1.0), 400, 2), 0.2), (m.buf, 1.0))


@sound(A, 'amb_kapelle', sr=SRA, loop=True, desc='Kapelle: leerer Steinraum, tiefer Nachhall, Kerzenflattern, ein ferner Orgelton', peak=-18)
def kapelle(r, i):
    m = Mix(D, loop=True)
    scatter(m, r, lambda r: mon.kerze_flackert(r, int(r.integers(0, 3))), 1, (0.1, 0.2))
    organ = (sine(np.full(n_(D), 110.0), D) + 0.5 * sine(np.full(n_(D), 164.8), D) + 0.3 * sine(np.full(n_(D), 220.0), D)) * (0.6 + 0.4 * np.sin(TAU * tt(D) / D)) * 0.04
    return mix((reverb(room(D, r, 1.0, 300), r, 2.5, 0.4, 3000, circ=True), 0.8), (organ, 1.0), (m.buf, 1.0))


# --------------------------------------------------------------------------- Wetter

@sound(A, 'amb_regen_leicht', sr=SRA, loop=True, desc='Leichter Regen im Freien', peak=-16)
def regen_l(r, i):
    return mix((rain(D, r, 0.5), 1.0), (wind(D, r, 80, 500, 0.6), 0.15))


@sound(A, 'amb_regen_stark', sr=SRA, loop=True, desc='Starker Regen im Freien mit Wind', peak=-14)
def regen_s(r, i):
    return mix((rain(D, r, 1.2), 1.0), (wind(D, r, 80, 900, 1.0, 0.25, 0.9), 0.35))


@sound(A, 'amb_regen_dach', sr=SRA, loop=True, desc='Regen aufs Dach, von innen gehoert', peak=-16)
def regen_dach(r, i):
    return mix((rain(D, r, 0.9, roof=True), 1.0), (room(D, r, 1.0, 250), 0.3))


@sound(A, 'amb_sturm', sr=SRA, loop=True, desc='Sturm: Heulen, Regen, klappernde Laeden, Baeume ächzen', peak=-12)
def sturm(r, i):
    m = Mix(D, loop=True)
    scatter(m, r, lambda r: far(door.creak(r.uniform(1.0, 2.0), 50, 90, r, 0.9, (150, 500), 3.0), 900), 3, (0.2, 0.4))
    scatter(m, r, lambda r: lp(wld.klappern(r, 0), 3000, 2), 2, (0.15, 0.3))
    return mix((wind(D, r, 80, 1400, 1.4, 0.35, 0.9), 0.8), (whistle(D, r, 600, 1.0), 0.3), (rain(D, r, 1.0), 0.6), (m.buf, 1.0))


# --------------------------------------------------------------------------- Nachtbelagerung (Warnstufen)

def _scratch_events(m, r, count, gain, lpf=None):
    for _ in range(count):
        s = mon.kratzen_holz(r, int(r.integers(0, 4)))
        if lpf:
            s = lp(s, lpf, 2)
        m.add(s, r.uniform(0, D - 4), r.uniform(*gain))


@sound(A, 'amb_warnstufe1', sr=SRA, loop=True, desc='Warnstufe 1 (Knarren, Krallen am Holz, flackernde Kerze): leise Bedrohung, nichts passiert', peak=-16)
def warn1(r, i):
    m = Mix(D, loop=True)
    _scratch_events(m, r, 1, (0.2, 0.3), 2500)
    scatter(m, r, lambda r: mon.knarren_gebaelk(r, int(r.integers(0, 3))), 2, (0.2, 0.4))
    scatter(m, r, lambda r: mon.kerze_flackert(r, int(r.integers(0, 3))), 2, (0.2, 0.3))
    drone = (sine(np.full(n_(D), 55.0), D) + 0.7 * sine(np.full(n_(D), 58.0), D)) * 0.08
    return mix((room(D, r, 1.0, 200), 0.4), (drone, 1.0), (lp(wind(D, r, 60, 400, 1.0), 350, 2), 0.25), (m.buf, 1.0))


@sound(A, 'amb_warnstufe2', sr=SRA, loop=True, desc='Warnstufe 2 (5-10 s Reaktionsfenster): dichter Kratzen, unregelmaessiges Klopfen, Herzschlag hoerbar, Drone beginnt zu schweben', peak=-14)
def warn2(r, i):
    m = Mix(D, loop=True)
    _scratch_events(m, r, 3, (0.3, 0.5), 3500)
    scatter(m, r, lambda r: mon.klopfen_einzeln(r, int(r.integers(0, 4))), 4, (0.2, 0.45))
    scatter(m, r, lambda r: mon.knarren_gebaelk(r, int(r.integers(0, 3))), 3, (0.25, 0.5))
    scatter(m, r, lambda r: mon.fluestern(r, int(r.integers(0, 4))), 1, (0.1, 0.2))
    t = tt(D)
    drone = (sine(np.full(len(t), 55.0), D) + 0.8 * sine(np.full(len(t), 59.0), D) + 0.5 * sine(np.full(len(t), 110.0), D)) * 0.1
    return mix((room(D, r, 1.0, 200), 0.35), (drone, 1.0), (mon._heart(D, 78, r, 0.6) * 0.5, 1.0), (m.buf, 1.0))


@sound(A, 'amb_warnstufe3', sr=SRA, loop=True, desc='Warnstufe 3 (Tatze/Fratze im Spalt): lautes Kratzen, Schlaege, Knurren, schneller Herzschlag - Kampf oder Flucht', peak=-10)
def warn3(r, i):
    m = Mix(D, loop=True)
    _scratch_events(m, r, 4, (0.5, 0.8))
    scatter(m, r, lambda r: mon.tuer_wucht(r, int(r.integers(0, 3))), 2, (0.5, 0.8))
    scatter(m, r, lambda r: mon.knurren(r, int(r.integers(0, 3))), 2, (0.4, 0.7))
    t = tt(D)
    drone = (sine(np.full(len(t), 55.0), D) + 0.9 * sine(np.full(len(t), 58.5), D) + 0.6 * sine(np.full(len(t), 116.0), D)) * 0.14
    return mix((drone, 1.0), (mon._heart(D, 118, r, 0.9) * 0.7, 1.0), (m.buf, 1.0), (wind(D, r, 80, 900, 1.0), 0.2))


@sound(A, 'amb_sanity_niedrig', sr=SRA, loop=True, desc='Sanity niedrig: Pfeifen im Ohr, Fluestern ohne Worte, Kratzen aus den Waenden', peak=-16)
def sanity_low(r, i):
    m = Mix(D, loop=True)
    scatter(m, r, lambda r: mon.fluestern(r, int(r.integers(0, 4))), 5, (0.2, 0.5))
    _scratch_events(m, r, 1, (0.1, 0.2), 2000)
    ring = sine(np.full(n_(D), 3900.0), D) * 0.02 * (0.5 + 0.5 * gusts(D, r, 0.2, 0.3) / 1.3)
    return mix((m.buf, 1.0), (ring, 1.0), (room(D, r, 1.0, 200), 0.3))
