"""Tueren, Riegel, Barrikaden, Fensterlaeden, Tore, Luken. Regelwerk: Barrikade = Holzbalken + zwei Fensterlaeden mit Eisengriffen."""
import numpy as np

import nwaudio as nw
from nwaudio import (sound, white, bp, lp, hp, thump, env_ar, modal, click, layer, sparse, tt, n_, TAU, tv_filter,
                     reverb, colored, curve)

P = 'SFX/Tueren'


def creak(sec, f0, f1, r, harsh=0.5, res=(500, 1300), q=3.0):
    """Holz-/Scharniergeknarze: Saegezahn mit zittriger Tonhoehe (Haft-Gleit-Effekt), durch gleitendes Resonanzfilter."""
    # Stick-Slip: unregelmaessiger Impulszug (Abstand ~1/f mit Zufall), durch gleitendes Resonanzfilter gefaerbt
    n = n_(sec)
    t = tt(sec)
    times, tc = [], 0.0
    while tc < sec:
        f = f0 + (f1 - f0) * tc / sec
        tc += (1.0 / f) * (1.0 + harsh * r.uniform(-0.55, 0.9))
        times.append(tc)
    idx = (np.array(times) * nw.SR).astype(int)
    idx = idx[idx < n]
    imp = np.zeros(n)
    amp = r.uniform(0.35, 1.0, len(idx))
    amp *= (r.random(len(idx)) > 0.12 * harsh)  # gelegentliches Haengenbleiben
    imp[idx] = amp
    grip = np.clip(0.6 + 0.9 * lp(r.standard_normal(n), 9, 1) / 0.25, 0.1, 1.6)
    y = tv_filter(imp * grip, lambda u: res[0] + (res[1] - res[0]) * u, q)
    return y * np.sin(np.pi * np.clip(t / sec, 0, 1)) ** 0.6 * 4.0


def latch(r, lo=1800, hi=6500):
    return layer((click(0.03, lo, hi, 0.004, r), 0.8),
                 (nw.hit(r.uniform(1700, 2600), 0.07, r, 0.95, sec=0.15, n=8, ratio_pow=1.7, inharm=0.25, air=0.4), 1.0))


def wood_hit(f, sec, r, amp=1.0, soft=0.0):
    """Holz-Aufprall: viele unregelmaessige Moden, Anschlagsgeraeusch, dumpfer Koerperschlag (soft 0..1 = weicher/dumpfer)."""
    y = nw.hit(f, 0.24, r, 0.7 - 0.55 * soft, sec=sec, n=12, ratio_pow=1.45, inharm=0.2, thud=0.55, air=0.3)
    return y * amp


@sound(P, 'tuer_oeffnen', n=3, desc='Holztuer oeffnen: Klinke, Knarzen', peak=-8)
def tuer_oeffnen(r, i):
    c = creak(0.8, r.uniform(150, 200), r.uniform(220, 300), r, 0.6)
    return layer((latch(r), 0.7), (c, 0.6, 0.06), (wood_hit(r.uniform(90, 120), 0.4, r, 0.25, 0.8), 1.0, 0.7))


@sound(P, 'tuer_schliessen', n=3, desc='Holztuer schliessen: kurzes Knarzen, Schlag, Falle', peak=-6)
def tuer_schliessen(r, i):
    c = creak(0.45, r.uniform(240, 300), r.uniform(150, 190), r, 0.4)
    body = wood_hit(r.uniform(75, 105), 0.6, r, 1.0, 0.6)
    return reverb(layer((c, 0.35), (body, 1.0, 0.4), (latch(r), 0.55, 0.43)), r, 0.35, 0.08, 3000)


@sound(P, 'tuer_zuschlagen', n=2, desc='Tuer wird zugeschlagen / vom Wind zugeschlagen', peak=-3)
def tuer_zuschlagen(r, i):
    body = wood_hit(r.uniform(70, 95), 0.8, r, 1.0)
    rattle = modal([2300, 3400, 5100], [0.3, 0.2, 0.1], [0.12, 0.09, 0.06], 0.4)
    return reverb(layer((body, 1.0), (rattle, 0.4, 0.02), (latch(r), 0.5, 0.01)), r, 0.6, 0.15, 3500)


@sound(P, 'tuer_klinke_rattern', n=3, desc='Jemand rüttelt an der verschlossenen Tuer (Warnstufe/Tuerspion)', peak=-9)
def klinke(r, i):
    out = []
    t = 0.0
    for k in range(r.integers(3, 6)):
        f = r.uniform(1900, 2500)
        hit = nw.hit(f, 0.08, r, 0.95, sec=0.18, n=8, ratio_pow=1.7, inharm=0.25, air=0.5)
        out.append((hit * r.uniform(0.5, 1), 1.0, t))
        out.append((wood_hit(r.uniform(90, 130), 0.25, r, 0.35, 0.9), 1.0, t))
        t += r.uniform(0.07, 0.16) if k % 2 == 0 else r.uniform(0.25, 0.45)
    return layer(*out)


@sound(P, 'riegel_zu', n=2, desc='Eisenriegel / Schloss einrasten', peak=-7)
def riegel_zu(r, i):
    slide = tv_filter(white(0.28, r) * np.sin(np.pi * tt(0.28) / 0.28), lambda u: 900 + 2600 * u, 3)
    clack = layer((nw.hit(r.uniform(800, 1000), 0.2, r, 0.95, sec=0.3, n=10, ratio_pow=1.7, inharm=0.25, air=0.5), 1.0),
                  (thump(0.3, 160, 70, 0.04), 0.6), (click(0.02, 2000, 7000, 0.003, r), 0.5))
    return layer((slide, 0.35), (clack, 1.0, 0.27))


@sound(P, 'riegel_auf', n=2, desc='Riegel zurueckschieben / aufschliessen', peak=-8)
def riegel_auf(r, i):
    clack = layer((modal([850, 2100, 3600], [0.6, 0.4, 0.2], [0.12, 0.08, 0.05], 0.25), 1.0),
                  (click(0.02, 2000, 6500, 0.003, r), 0.6))
    slide = tv_filter(white(0.3, r) * np.sin(np.pi * tt(0.3) / 0.3), lambda u: 3200 - 2400 * u, 3)
    return layer((clack, 1.0), (slide, 0.35, 0.05))


@sound(P, 'schluessel_drehen', n=2, desc='Schluessel im Schloss drehen (Veronicas Praxis, Haustuer)', peak=-10)
def schluessel(r, i):
    parts = [(click(0.02, 2500, 8000, 0.003, r), 0.8, 0.0), (click(0.02, 2500, 8000, 0.003, r), 0.6, 0.12)]
    parts.append((layer((modal([1100, 2500, 4300], [0.6, 0.4, 0.2], [0.1, 0.07, 0.04], 0.2), 1.0), (thump(0.2, 180, 80, 0.03), 0.5)), 1.0, 0.3))
    return layer(*parts)


@sound(P, 'barrikade_balken', n=3, desc='Schwerer Holzbalken wird vor die Tuer gelegt (Barrikade)', peak=-3)
def barrikade_balken(r, i):
    scrape = tv_filter(colored(0.5, r, 1.0) * np.sin(np.pi * tt(0.5) / 0.5) ** 0.7, lambda u: 250 + 500 * u, 1.5)
    hit = layer((thump(0.9, 90, 38, 0.2), 1.0), (modal([110, 190, 310, 520], [1, 0.6, 0.4, 0.2], [0.6, 0.4, 0.25, 0.15], 0.9), 0.7),
                (hp(sparse(0.5, 400, r), 2500) * np.exp(-tt(0.5) / 0.1), 0.3))
    return reverb(layer((scrape, 0.5), (hit, 1.0, 0.45)), r, 0.5, 0.12, 2500)


@sound(P, 'barrikade_entfernen', n=2, desc='Balken wird angehoben / zur Seite gelegt', peak=-6)
def barrikade_weg(r, i):
    lift = tv_filter(colored(0.45, r, 1.0) * np.sin(np.pi * tt(0.45) / 0.45) ** 0.7, lambda u: 700 - 400 * u, 1.5)
    put = layer((thump(0.6, 85, 40, 0.15), 0.9), (modal([120, 200, 340], [1, 0.6, 0.3], [0.4, 0.25, 0.15], 0.6), 0.6))
    return layer((lift, 0.6), (put, 0.8, 0.5))


@sound(P, 'fensterladen_zu', n=3, desc='Fensterladen zuklappen, Eisengriff rastet ein', peak=-6)
def laden_zu(r, i):
    a = wood_hit(r.uniform(250, 320), 0.35, r, 0.9, 0.2)
    b = wood_hit(r.uniform(230, 290), 0.35, r, 0.7, 0.2)
    metal = modal([1400, 2900, 4500], [0.6, 0.4, 0.25], [0.2, 0.14, 0.08], 0.35)
    return layer((a, 1.0), (b, 0.8, 0.11), (metal, 0.5, 0.2), (creak(0.25, 380, 500, r, 0.3, (900, 1700)), 0.2, 0.0))


@sound(P, 'fensterladen_auf', n=3, desc='Fensterladen aufstossen', peak=-7)
def laden_auf(r, i):
    metal = layer((modal([1500, 3000, 4800], [0.6, 0.4, 0.25], [0.15, 0.1, 0.06], 0.25), 1.0), (click(0.02, 2500, 7000, 0.003, r), 0.5))
    c = creak(0.4, 450, 300, r, 0.5, (900, 1800))
    return layer((metal, 0.7), (c, 0.4, 0.06), (wood_hit(r.uniform(260, 320), 0.3, r, 0.6, 0.3), 1.0, 0.38))


@sound(P, 'fenster_oeffnen', n=2, desc='Schiebefenster hochziehen (Flucht durchs Fenster): Holz quietscht, Glas klirrt leise', peak=-8)
def fenster_auf(r, i):
    slide = creak(0.55, 700, 1100, r, 0.8, (1100, 2400), 5.0)
    glass = modal([2900, 4200, 5800], [0.25, 0.2, 0.12], [0.3, 0.2, 0.15], 0.5) * np.exp(-tt(0.5) / 0.15)
    return layer((slide, 0.7), (glass, 0.3, 0.1), (wood_hit(r.uniform(180, 230), 0.3, r, 0.5, 0.5), 1.0, 0.55))


@sound(P, 'fenster_schliessen', n=2, desc='Fenster zuschieben und einrasten', peak=-8)
def fenster_zu(r, i):
    slide = creak(0.4, 1000, 700, r, 0.7, (2200, 1100), 5.0)
    return layer((slide, 0.6), (wood_hit(r.uniform(190, 240), 0.35, r, 0.9, 0.5), 1.0, 0.38), (latch(r, 2500, 8000), 0.4, 0.4))


@sound(P, 'fenster_klettern', n=3, desc='Ueber die Fensterbank klettern: Stoff, Holz, dumpfer Aufprall draussen', peak=-9)
def fenster_klettern(r, i):
    cloth = bp(white(0.5, r), 300, 2500) * env_ar(0.5, 0.05, 0.12)
    sill = wood_hit(r.uniform(160, 210), 0.3, r, 0.5, 0.8)
    land = layer((thump(0.4, 120, 55, 0.08), 0.9), (bp(white(0.3, r), 300, 3000) * env_ar(0.3, 0.005, 0.07), 0.5))
    return layer((cloth, 0.6), (sill, 0.8, 0.25), (land, 1.0, 0.55))


@sound(P, 'pendeltuer', n=3, desc='Pendeltuer der Bar: quietscht, schwingt dreimal nach (Ilhans Bar)', peak=-8)
def pendeltuer(r, i):
    parts = []
    t = 0.0
    for k, amp in enumerate((1.0, 0.65, 0.4, 0.22)):
        d = 0.32 + 0.05 * k
        parts.append((creak(d, 480 if k % 2 == 0 else 360, 380 if k % 2 == 0 else 520, r, 0.4, (700, 1500)), 0.35 * amp, t))
        parts.append((wood_hit(r.uniform(150, 200), 0.18, r, 0.5 * amp, 0.9), 1.0, t + d * 0.8))
        t += d
    return layer(*parts)


@sound(P, 'tuerglocke', n=2, desc='Tuerglockchen (Baeckerei, Laden): helles Klingeln', peak=-8)
def tuerglocke(r, i):
    f = r.uniform(2000, 2500)
    return reverb(modal([f, f * 1.51, f * 2.76, f * 4.2], [1, 0.7, 0.4, 0.25], [1.1, 0.8, 0.5, 0.3], 1.3), r, 0.6, 0.15, 7000)


@sound(P, 'tor_quietscht_auf', n=2, desc='Eisentor oeffnen (Friedhofstor): langes metallisches Quietschen', peak=-8)
def tor_auf(r, i):
    c = creak(1.3, 520, 380, r, 0.9, (1500, 2600), 7.0)
    ring = modal([820, 1630, 2480], [0.4, 0.3, 0.2], [1.2, 0.8, 0.5], 1.4) * np.sin(np.pi * tt(1.4) / 1.4)
    return reverb(layer((c, 0.8), (ring, 0.25), (click(0.03, 2000, 7000, 0.004, r), 0.5)), r, 1.0, 0.15, 4000)


@sound(P, 'tor_zu', n=2, desc='Eisentor faellt zu: Klang und Nachhall', peak=-6)
def tor_zu(r, i):
    clang = nw.hit(r.uniform(380, 440), 1.4, r, 0.9, sec=1.6, n=16, ratio_pow=1.75, inharm=0.25, tilt=0.8, air=0.3)
    return reverb(layer((clang, 0.8), (thump(0.5, 120, 60, 0.08), 0.8)), r, 1.0, 0.2, 4000)


@sound(P, 'falltuer_hoch', n=2, desc='Falltuer / Kellerluke wird angehoben und fallen gelassen', peak=-5)
def falltuer(r, i):
    c = creak(0.6, 200, 260, r, 0.5, (350, 800))
    return reverb(layer((c, 0.5), (wood_hit(r.uniform(85, 110), 0.7, r, 1.0, 0.2), 1.0, 0.65), (hp(sparse(0.5, 300, r), 3000) * np.exp(-tt(0.5) / 0.1), 0.3, 0.65)), r, 0.5, 0.12, 2500)
