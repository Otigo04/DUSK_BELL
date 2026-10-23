"""Schritte pro Untergrund (je 4 Varianten) plus Landen/Ausweichen. Passend zu den Tiles: Erdweg, Gras, Dielen, Stein, Kies, Pflaster."""
import numpy as np

import nwaudio as nw
from nwaudio import (sound, white, bp, lp, hp, thump, env_ar, modal, click, layer, sparse, tt, n_, TAU)

P = 'SFX/Schritte'


@sound(P, 'step_erde', n=4, desc='Schritt auf Erdweg (Dorfstrasse, Pfade)', peak=-14)
def step_erde(r, i):
    n = 0.24
    scuff = bp(white(n, r), r.uniform(220, 320), r.uniform(1800, 2600)) * env_ar(n, 0.003, 0.04)
    heel = thump(n, r.uniform(110, 150), 52, 0.05)
    grit = bp(sparse(n, 140, r), 1500, 6500) * np.exp(-tt(n) / 0.05)
    return layer((scuff, 1.0), (heel, 0.55), (grit, 0.6))


@sound(P, 'step_gras', n=4, desc='Schritt auf Gras / Wiese', peak=-16)
def step_gras(r, i):
    n = 0.3
    sw = bp(white(n, r), r.uniform(500, 800), r.uniform(4200, 5600)) * env_ar(n, 0.014, 0.075)
    body = thump(n, 95, 60, 0.05) * 0.25
    return layer((sw, 1.0), (body, 0.5))


@sound(P, 'step_holz', n=4, desc='Schritt auf Holzdielen / Veranda / Steg', peak=-12)
def step_holz(r, i):
    n = 0.4
    f = r.uniform(150, 230)
    return layer((nw.hit(f, 0.25, r, 0.4, sec=n, n=12, ratio_pow=1.45, inharm=0.2, thud=0.6, air=0.3), 1.0),
                 (bp(white(0.12, r), 400, 3000) * env_ar(0.12, 0.004, 0.025), 0.35))


@sound(P, 'step_stein', n=4, desc='Schritt auf Steinplatten / Keller / Revier-Boden', peak=-13)
def step_stein(r, i):
    n = 0.45
    tick = click(0.05, 1300, 6500, 0.008, r)
    ring = nw.hit(r.uniform(480, 720), 0.14, r, 0.8, sec=n, n=9, ratio_pow=1.35, inharm=0.2, air=0.2)
    tail = bp(white(n, r), 400, 2500) * np.exp(-tt(n) / 0.12) * 0.12
    heel = thump(n, 130, 70, 0.035) * 0.6
    return layer((tick, 0.8), (ring, 0.7), (tail, 1.0), (heel, 0.5))


@sound(P, 'step_pflaster', n=4, desc='Schritt auf Pflaster / Kopfsteinpflaster', peak=-13)
def step_pflaster(r, i):
    n = 0.35
    tick = click(0.04, 1800, 7500, 0.006, r)
    clack = nw.hit(r.uniform(900, 1300), 0.07, r, 0.9, sec=n, n=8, ratio_pow=1.4, inharm=0.2, air=0.3)
    heel = thump(n, 150, 75, 0.03) * 0.5
    return layer((tick, 0.7), (clack, 0.9), (heel, 0.6))


@sound(P, 'step_kies', n=4, desc='Schritt auf Kies / Schotter', peak=-15)
def step_kies(r, i):
    n = 0.34
    t = tt(n)
    crunch = bp(sparse(n, 520, r), 1800, 9000) * np.exp(-t / 0.09)
    crunch = lp(crunch, 7000, 1)
    body = bp(white(n, r), 300, 1600) * env_ar(n, 0.006, 0.06) * 0.3
    heel = thump(n, 110, 60, 0.04) * 0.4
    return layer((crunch * 2.2, 1.0), (body, 1.0), (heel, 0.5))


@sound(P, 'step_matsch', n=4, desc='Schritt im Matsch / nasser Erde', peak=-14)
def step_matsch(r, i):
    n = 0.4
    t = tt(n)
    sq = bp(white(n, r), 150, 900) * env_ar(n, 0.01, 0.09)
    pop = np.sin(TAU * np.cumsum(300 + 900 * (t / n)) / nw.SR) * np.exp(-t / 0.03) * (t > 0.08)
    heel = thump(n, 90, 50, 0.07) * 0.6
    return layer((sq, 1.0), (pop, 0.18), (heel, 0.6))


@sound(P, 'step_wasser', n=4, desc='Schritt in Pfuetze / flachem Wasser', peak=-13)
def step_wasser(r, i):
    n = 0.5
    t = tt(n)
    sp = bp(white(n, r), 500, 6500) * env_ar(n, 0.006, 0.11)
    bub = np.zeros(len(t))
    for k in range(3):
        t0 = r.uniform(0.03, 0.25)
        f = r.uniform(500, 1100)
        m = t >= t0
        bub[m] += np.sin(TAU * np.cumsum(f * (1 + 2.5 * (t[m] - t0))) / nw.SR) * np.exp(-(t[m] - t0) / 0.03)
    return layer((sp, 1.0), (bub, 0.25), (thump(n, 100, 55, 0.05), 0.35))


@sound(P, 'step_laub', n=4, desc='Schritt auf Laub / trockenem Unterholz (Wald)', peak=-15)
def step_laub(r, i):
    n = 0.4
    t = tt(n)
    rus = hp(white(n, r), 2200) * env_ar(n, 0.01, 0.1)
    cr = bp(sparse(n, 220, r), 2500, 9000) * np.exp(-t / 0.12)
    snap = click(0.02, 1500, 4000, 0.004, r) * (r.random() < 0.4)
    return layer((rus, 0.5), (cr * 2.0, 1.0), (snap, 0.5, r.uniform(0.02, 0.15)), (thump(n, 100, 60, 0.04), 0.2))


@sound(P, 'step_teppich', n=4, desc='Schritt auf Teppich / Stoff (Villa, Innenraeume)', peak=-20)
def step_teppich(r, i):
    n = 0.25
    soft = lp(white(n, r), 700) * env_ar(n, 0.012, 0.05)
    return layer((soft, 1.0), (thump(n, 90, 55, 0.04), 0.5))


@sound(P, 'step_schwer', n=3, desc='Schwerer Schritt (Monster, Tatze auf Dielen)', peak=-8)
def step_schwer(r, i):
    n = 0.7
    body = modal([r.uniform(70, 95), r.uniform(150, 210), r.uniform(300, 420)], [1, 0.6, 0.3], [0.35, 0.2, 0.12], n)
    lo = thump(n, 80, 38, 0.15)
    creak = nw.tv_filter(white(0.4, r) * env_ar(0.4, 0.02, 0.12), lambda u: 500 + 700 * u, 4)
    return layer((body, 0.8), (lo, 0.9), (creak, 0.25, 0.04))


@sound(P, 'sprung_landen', n=3, desc='Landen / Ausweichrolle: Stoff und Staub', peak=-11)
def landen(r, i):
    n = 0.4
    cloth = bp(white(n, r), 300, 3000) * env_ar(n, 0.006, 0.08)
    return layer((cloth, 1.0), (thump(n, 130, 55, 0.06), 0.8), (hp(sparse(n, 200, r), 3000) * np.exp(-tt(n) / 0.08), 0.5))
