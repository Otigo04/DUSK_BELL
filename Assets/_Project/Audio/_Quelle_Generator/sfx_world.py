"""Welt: Glocke (Titel des Spiels), Tiere, Fahrzeug und Radio (Opening), Wetter-Einzelklaenge, Dorf-Objekte.
Glockenregel: Sheriff laeutet in der Daemmerung (Regelwerk), in Opening Step 12b schlaegt sie zweimal (Opening Sequence),
Spieler muss vor dem Laeuten im Haus sein (Bulut: "Be inside before the bell rings")."""
import numpy as np

import nwaudio as nw
from nwaudio import (sound, white, bp, lp, hp, thump, env_ar, modal, click, layer, sparse, tt, n_, TAU, tv_filter,
                     reverb, colored, voice, sine, midi, note, Mix)
from sfx_doors import creak, wood_hit

G = 'SFX/Glocke'
A = 'SFX/Tiere'
F = 'SFX/Fahrzeug'
O = 'SFX/Welt'


def church_bell(f, d, r, hum=1.0, strike=1.0, bright=1.0):
    """Kirchenglocke nach klassischer Teilton-Folge (Unterton, Prim, Mollterz, Quinte, Oktave ...), leichte Schwebungen."""
    ratios = [0.5, 1.0, 1.183, 1.506, 2.0, 2.514, 2.662, 3.011, 4.166, 5.433]
    amps = [0.55 * hum, 1.0, 0.8, 0.55, 0.65, 0.35 * bright, 0.3 * bright, 0.22 * bright, 0.14 * bright, 0.08 * bright]
    t60 = [d * 1.0, d * 0.85, d * 0.6, d * 0.5, d * 0.4, d * 0.3, d * 0.3, d * 0.22, d * 0.16, d * 0.1]
    fr = [f * q for q in ratios]
    body = modal(fr, amps, t60, d)
    beat = modal([x * 1.0035 for x in fr[:4]], [a * 0.5 for a in amps[:4]], t60[:4], d)  # Schwebung, "lebendiger" Klang
    hit = layer((click(0.05, 500, 6000, 0.008, r), 0.6 * strike), (thump(0.4, f * 0.8, f * 0.4, 0.1), 0.5 * strike))
    return layer((body, 1.0), (beat, 0.6), (hit, 1.0))


@sound(G, 'glocke_gross', sr=32000, n=3, desc='Grosse Dorfglocke, ein Schlag (D3, langer Nachklang ~9 s). Die "Dusk Bell"', peak=-3)
def glocke_gross(r, i):
    return reverb(church_bell(146.8 * (1 + 0.004 * (i - 1)), 9.0, r), r, 2.6, 0.3, 4500)


@sound(G, 'glocke_zweimal', sr=32000, desc='Opening Step 12b: Abenddaemmerung, die Glocke schlaegt zweimal (Abstand 2,2 s)', peak=-3)
def glocke_zweimal(r, i):
    a = church_bell(146.8, 8.0, r)
    return reverb(layer((a, 1.0), (church_bell(146.8, 8.0, r) * 0.95, 1.0, 2.2)), r, 2.6, 0.3, 4500)


@sound(G, 'glocke_laeuten', sr=32000, desc='Sheriff laeutet die Abendglocke: 8 Schlaege, gleichmaessig, Nachklaenge ueberlagern sich (ca. 19 s)', peak=-3)
def glocke_laeuten(r, i):
    parts = [(church_bell(146.8 * (1 + 0.002 * (k % 2)), 7.0, r), 0.85 + 0.15 * (k % 2), k * 2.0) for k in range(8)]
    return reverb(layer(*parts), r, 2.6, 0.3, 4500)


@sound(G, 'glocke_gedaempft_fern', sr=32000, n=2, desc='Glocke aus der Ferne / durch Waende (Nacht, im Haus gehoert): dumpf, kein Anschlag', peak=-10)
def glocke_fern(r, i):
    return lp(reverb(church_bell(146.8, 9.0, r, strike=0.1), r, 2.0, 0.5, 2500), 700, 2)


@sound(G, 'glocke_kapelle', sr=32000, n=2, desc='Kleine Kapellenglocke (hell, G4): Kapelle am Friedhof, Beerdigung', peak=-4)
def glocke_kapelle(r, i):
    return reverb(church_bell(392.0, 5.5, r, bright=1.2), r, 1.8, 0.3, 6000)


@sound(G, 'handglocke', desc='Handglocke wird geschuettelt (Sheriff, Warnung): helles Scheppern, ca. 3 s', peak=-5)
def handglocke(r, i):
    d = 3.2
    out = Mix(d)
    t = 0.0
    while t < 2.6:
        out.add(modal([1568, 2349, 3322, 4700], [1, 0.6, 0.4, 0.25], [0.9, 0.6, 0.4, 0.25], 1.0) * r.uniform(0.5, 1.0), t)
        t += r.uniform(0.07, 0.12)
    return reverb(out.buf, r, 0.6, 0.15, 8000)


@sound(G, 'standuhr_schlag', sr=32000, n=2, desc='Standuhr / Wanduhr: einzelner Schlag (Villa, Revier)', peak=-8)
def standuhr(r, i):
    return reverb(modal([392, 784, 1175, 1570, 2350], [1, 0.5, 0.35, 0.2, 0.12], [2.5, 1.8, 1.2, 0.8, 0.5], 3.0), r, 0.8, 0.15, 6000)


@sound(G, 'kuckucksuhr', sr=22050, desc='Kuckucksuhr: zwei Rufe (Villa-/Haus-Interieur)', peak=-12)
def kuckuck(r, i):
    d = 1.6
    out = Mix(d)
    for k, f in enumerate((660, 520)):
        t = tt(0.28)
        y = sine(f * (1 + 0.02 * np.sin(TAU * 6 * t)), 0.28) * np.sin(np.pi * t / 0.28) ** 0.5
        out.add(y, 0.1 + k * 0.5)
    return reverb(out.buf, r, 0.4, 0.1, 5000)


# --------------------------------------------------------------------------- Tiere

def caw(r, f=620.0, d=0.45):
    t = tt(d)
    fr = f * (1.0 + 0.35 * np.exp(-t / 0.05) - 0.3 * t / d) * (1 + 0.03 * np.sin(TAU * 60 * t))
    y = voice(fr, d, [(900, 4, 1.0), (1800, 4, 0.7), (3200, 4, 0.3)], r, breath=0.35, jit=0.04, kind='square')
    return y * (np.minimum(1, t / 0.02)) * np.exp(-t / (d * 0.7))


@sound(A, 'rabe_kraechzen', sr=22050, n=5, desc='Rabe kraechzt (Rabe_Sitzt am Friedhof, Opening)', peak=-9)
def rabe(r, i):
    k = r.integers(1, 4)
    out = Mix(0.4 + 0.55 * k)
    for j in range(k):
        out.add(caw(r, r.uniform(520, 720), r.uniform(0.3, 0.5)), j * r.uniform(0.45, 0.6))
    return reverb(out.buf, r, 0.7, 0.2, 5000)


@sound(A, 'rabe_abflug', sr=22050, n=3, desc='Rabe fliegt auf: Fluegelschlaege und Ruf (Rabe_Flug)', peak=-8)
def rabe_flug(r, i):
    d = 1.4
    out = Mix(d)
    for k in range(9):
        t = k * (0.1 + 0.015 * k)
        out.add(bp(white(0.09, r), 150, 1800) * env_ar(0.09, 0.005, 0.025) * (1.0 if k < 5 else 0.6), t)
    out.add(caw(r, 600, 0.35), 0.15, 0.7)
    return reverb(out.buf, r, 0.7, 0.2, 5000)


@sound(A, 'eule', sr=22050, n=3, desc='Eule ruft in der Nacht: zwei Rufe, weich, weit weg', peak=-12)
def eule(r, i):
    d = 2.4
    out = Mix(d)
    for k, (f, t0, dd) in enumerate(((410, 0.1, 0.35), (350, 0.62, 0.65))):
        t = tt(dd)
        fr = f * (1 - 0.06 * t / dd) * (1 + 0.006 * nw.smooth_rand(dd, r, 8.0, False))
        env = np.sin(np.pi * t / dd) ** 0.8
        y = (sine(fr, dd) + 0.25 * sine(2 * fr, dd) + 0.06 * sine(3 * fr, dd)) * env + 0.12 * lp(white(dd, r), 1100, 1) * env
        out.add(y, t0 + 0.7 * k * (i % 2))
    return reverb(out.buf, r, 1.6, 0.4, 3000)


@sound(A, 'katze_miauen', sr=22050, n=4, desc='Katze miaut (Katze.png/_Idle, _Alert)', peak=-11)
def miau(r, i):
    d = r.uniform(0.5, 0.9)
    t = tt(d)
    f = 480 + 330 * np.sin(np.pi * np.clip(t / d, 0, 1)) ** 0.8 + r.uniform(-30, 30)
    y = voice(f, d, [((900, 1700), 7, 1.0), ((2400, 2000), 6, 0.5)], r, breath=0.05, jit=0.015)
    return y * np.sin(np.pi * t / d) ** 0.6


@sound(A, 'katze_fauchen', sr=22050, n=2, desc='Katze faucht (wittert Monster)', peak=-8)
def katze_faucht(r, i):
    d = 0.8
    return layer((tv_filter(white(d, r), lambda u: 6000, 1.0) * env_ar(d, 0.03, 0.25), 0.7),
                 (voice(260, d, [(1200, 5, 1.0)], r, breath=0.5, jit=0.08) * env_ar(d, 0.03, 0.3), 0.4))


@sound(A, 'katze_schnurren_loop', sr=22050, loop=True, desc='Katze schnurrt (Loop, 4 s, 26 Hz Grundrauschen)', peak=-18)
def schnurren(r, i):
    d = 4.0
    t = tt(d)
    pulses = 0.5 + 0.5 * np.sin(TAU * 26 * t)
    return lp(white(d, r), 500, 2, circ=True) * pulses * (0.8 + 0.2 * np.sin(TAU * 0.5 * t))


@sound(A, 'ratte_quieken', sr=22050, n=3, desc='Ratte quiekt, huscht (Strasse/Keller)', peak=-14)
def ratte(r, i):
    d = 0.3
    t = tt(d)
    f = (2800 + 1200 * np.sin(TAU * 11 * t)) * (1.0 + 0.03 * nw.smooth_rand(d, r, 30.0, False))
    y = voice(f, d, [(3500, 6, 1.0), (5500, 6, 0.4)], r, breath=0.25, jit=0.03, shimmer=0.15)
    return y * np.sin(np.pi * t / d) ** 1.2


# --------------------------------------------------------------------------- Fahrzeug / Radio (Opening)

def _engine_pulses(times, amps, d, r, circ=False):
    """Zuendimpulse (Zeit, Staerke) -> Motorklang: jeder Impuls ist ein kurzer dumpfer Knall, der Auspuff und Block zum Schwingen bringt."""
    m = Mix(d, loop=circ)
    shot = layer((thump(0.06, 190, 70, 0.014), 1.0), (lp(white(0.03, r), 900, 1) * np.hanning(n_(0.03)), 0.6))
    for t, a in zip(times, amps):
        m.add(shot, t, a)
    y = m.buf
    body = nw.resonate(y, 140, 3, circ) + 0.7 * nw.resonate(y, 330, 3, circ) + 0.25 * lp(y, 1500, 1, circ)
    mech = bp(white(d, r), 1400, 5000, 2, circ=circ) * 0.015 * (0.6 + 0.4 * nw.smooth_rand(d, r, 6.0, circ))
    return body + mech


def _engine_loop(r, d, f, rough):
    N = int(round(f * d))
    per = d / N
    times = [k * per + r.normal(0, per * rough) for k in range(N)]
    amps = [r.uniform(0.75, 1.0) * (0.6 if k % 4 == 2 else 1.0) for k in range(N)]
    return _engine_pulses(times, amps, d, r, circ=True)


@sound(F, 'auto_motor_leerlauf', sr=22050, loop=True, desc='Auto-Motor im Leerlauf, alter Vierzylinder: unregelmaessige Zuendfolge, Auspuff-Resonanz (Loop 3 s)', peak=-18)
def motor_idle(r, i):
    return _engine_loop(r, 3.0, 25.0, 0.06)


@sound(F, 'auto_motor_fahrt', sr=22050, loop=True, desc='Motor bei Fahrt (Loop 3 s): hoeher; Unity: Pitch mit Tempo skalieren', peak=-18)
def motor_drive(r, i):
    return _engine_loop(r, 3.0, 48.0, 0.035)


@sound(F, 'auto_starten', sr=22050, desc='Motor anlassen: Anlasser orgelt (stockend), Zuendung faengt, faellt in Leerlauf', peak=-9)
def auto_start(r, i):
    d = 3.8
    times, amps = [], []
    t = 0.0
    while t < 1.3:                                   # Anlasser: langsame, schwere Kompressionsschlaege
        times.append(t)
        amps.append(r.uniform(0.6, 0.9))
        t += 0.11 + 0.01 * r.random()
    rate = 7.0
    while t < d:                                     # Zuendung faengt: Rate steigt, haengt kurz, pendelt sich ein
        times.append(t)
        amps.append(r.uniform(0.7, 1.0) * (0.5 if r.random() < 0.15 else 1.0))
        rate = min(25.0, rate + 0.9 + 0.6 * r.random())
        t += (1.0 / rate) * r.uniform(0.9, 1.1)
    eng = _engine_pulses(times, amps, d, r)
    whine = nw.sine(np.full(n_(d), 310.0), d) * 0.05 * (tt(d) < 1.3) * np.minimum(1, tt(d) / 0.1)
    return reverb(layer((eng, 1.0), (whine, 1.0)), r, 0.3, 0.1, 3000)


@sound(F, 'auto_abstellen', sr=22050, desc='Motor aus: Zuendaussetzer, Auslaufen, Metall tickt beim Abkuehlen', peak=-11)
def auto_aus(r, i):
    d = 3.0
    times, amps = [], []
    t, rate = 0.0, 25.0
    while t < 1.8:
        times.append(t)
        amps.append(r.uniform(0.5, 1.0) * max(0.2, 1.0 - t / 1.8))
        rate = max(3.0, rate * 0.93)
        t += (1.0 / rate) * r.uniform(0.85, 1.25)
    eng = _engine_pulses(times, amps, d, r)
    tick = nw.hit(r.uniform(1700, 2100), 0.08, r, 1.0, sec=0.15, n=7, ratio_pow=1.7, inharm=0.25, air=0.5)
    return layer((eng, 1.0), (tick, 0.15, 2.0), (tick, 0.1, 2.5))


@sound(F, 'auto_tuer_auf', sr=32000, n=2, desc='Autotuer oeffnen: Griff, Scharnier', peak=-9)
def auto_tuer_auf(r, i):
    return layer((click(0.04, 1500, 6000, 0.006, r), 0.8), (creak(0.35, 300, 380, r, 0.4, (900, 1600)), 0.3, 0.05), (thump(0.2, 140, 80, 0.04), 0.4, 0.4))


@sound(F, 'auto_tuer_zu', sr=32000, n=2, desc='Autotuer zuschlagen: dumpfer Blechschlag, Klack', peak=-5)
def auto_tuer_zu(r, i):
    return reverb(layer((thump(0.4, 110, 55, 0.08), 1.0), (modal([180, 360, 720, 1450], [1, 0.6, 0.4, 0.2], [0.2, 0.14, 0.1, 0.06], 0.4), 0.7), (click(0.03, 1500, 7000, 0.005, r), 0.7)), r, 0.3, 0.08, 4000)


@sound(F, 'auto_bremsen', sr=22050, desc='Auto bremst auf Schotter vor dem Baumstamm (Opening Step 4): Kies knirscht, Quietschen kurz', peak=-8)
def auto_bremse(r, i):
    d = 2.2
    t = tt(d)
    gravel = bp(white(d, r), 1500, 8000) * np.clip(1 - t / d, 0, 1) ** 1.5 * (0.6 + 0.4 * np.clip(lp(r.standard_normal(len(t)), 30, 1) / 0.5, 0, 1))
    squeal = sine(1800 + 400 * (1 - t / d), d) * np.clip(1 - t / 0.9, 0, 1) * 0.04
    return layer((gravel, 0.7), (squeal, 1.0), (lp(white(d, r), 300), 0.1))


@sound(F, 'auto_hupe', sr=22050, desc='Hupe (kurz, schnarrend, 1910er-Stil)', peak=-8)
def hupe(r, i):
    d = 0.6
    t = tt(d)
    return (nw.square(np.full(len(t), 372.0), duty=0.4) + nw.square(np.full(len(t), 466.0), duty=0.4)) * 0.5 * adsr_(d)


def adsr_(d):
    return nw.adsr(d, 0.02, 0.05, 0.9, 0.08)


@sound(F, 'radio_rauschen_loop', sr=22050, loop=True, desc='Autoradio ohne Sender (Opening Step 4: Schlager geht in Rauschen ueber): Hiss, 50-Hz-Brummen, leises Knistern (Loop 6 s)', peak=-20)
def radio_noise(r, i):
    d = 6.0
    t = tt(d)
    hiss = bp(white(d, r), 300, 6000, 2, circ=True) * (0.7 + 0.3 * lp(r.standard_normal(len(t)), 3, 1, circ=True) / 0.4)
    crack = hp(sparse(d, 14, r), 2000, circ=True) * 1.5
    return hiss + crack + 0.02 * sine(np.full(len(t), 100.0), d)


@sound(F, 'radio_senderwechsel', sr=22050, n=2, desc='Radio durch die Sender drehen: Pfeifen gleitet, Bruchstuecke Musik, Rauschen', peak=-14)
def radio_dreh(r, i):
    d = 2.4
    t = tt(d)
    whistle = sine(300 + 2500 * np.abs(np.sin(TAU * 0.6 * t)) ** 2, d) * 0.1
    hiss = bp(white(d, r), 400, 6000) * 0.5
    snips = np.zeros(len(t))
    for k in range(3):
        a = int(r.uniform(0.2, 1.9) * nw.SR)
        L = int(r.uniform(0.1, 0.25) * nw.SR)
        f = midi(r.integers(57, 76))
        snips[a:a + L] += sine(f, L / nw.SR)[:L] * 0.3
    return bp(whistle + hiss + snips, 250, 4000)


@sound(F, 'radio_aus', sr=22050, desc='Radio ausgeschaltet: Knack, kurzer Abfall', peak=-14)
def radio_aus(r, i):
    return layer((thump(0.08, 300, 100, 0.01), 0.7), (click(0.02, 1000, 4000, 0.003, r), 0.6), (bp(white(0.2, r), 400, 3000) * np.exp(-tt(0.2) / 0.03), 0.3))


# --------------------------------------------------------------------------- Welt-Einzelklaenge

@sound(O, 'donner_fern', sr=22050, n=3, desc='Ferner Donner: tiefes Grollen (Wetter, Nacht)', peak=-8)
def donner(r, i):
    d = r.uniform(4.0, 6.0)
    t = tt(d)
    rumble = lp(colored(d, r, 2.0), 140, 2) * (np.minimum(1, t / 0.4) * np.exp(-t / (d * 0.35)))
    rolls = lp(colored(d, r, 1.5), 300, 2) * np.exp(-((t - d * 0.4) / (d * 0.18)) ** 2) * 0.6
    return reverb(rumble + rolls, r, 1.5, 0.3, 1200)


@sound(O, 'windspiel', sr=32000, n=2, desc='Windspiel (Talisman-Haus, Veranda): vereinzelte helle Toene im Wind', peak=-14)
def windspiel(r, i):
    d = 5.0
    out = Mix(d)
    scale = [midi(note(n)) for n in ('E6', 'G6', 'A6', 'B6', 'D7')]
    for k in range(r.integers(6, 11)):
        f = scale[r.integers(0, len(scale))]
        out.add(modal([f, f * 2.76, f * 5.4], [1, 0.3, 0.1], [2.5, 1.2, 0.5], 2.8), r.uniform(0, d - 1), r.uniform(0.3, 1.0))
    return reverb(out.buf, r, 1.2, 0.25, 9000)


@sound(O, 'fenster_klappern', sr=22050, n=2, desc='Laden/Fenster klappern im Wind', peak=-12)
def klappern(r, i):
    d = 3.0
    out = Mix(d)
    t = 0.0
    while t < d - 0.3:
        out.add(wood_hit(r.uniform(240, 340), 0.2, r, r.uniform(0.3, 1.0), 0.4), t)
        t += r.uniform(0.1, 0.5)
    return out.buf


@sound(O, 'wegweiser_quietscht', sr=22050, n=2, desc='Wegweiser / Schild an rostiger Kette quietscht im Wind', peak=-14)
def schild(r, i):
    return creak(2.2, 600, 700, r, 0.8, (1500, 2400), 6.0) * 0.4


@sound(O, 'fahne_flattern_loop', sr=22050, loop=True, desc='Fahne flattert (Fahne_Rot/Blau): Loop 4 s', peak=-20)
def fahne(r, i):
    d = 4.0
    t = tt(d)
    flap = np.clip(lp(r.standard_normal(len(t)), 14, 1, circ=True) / 0.3, 0, 1.0) ** 2
    return hp(white(d, r), 600, circ=True) * lp(white(d, r), 3000, circ=True) * flap * 0.4 + lp(white(d, r), 250, 2, circ=True) * flap * 0.5


@sound(O, 'karren_quietschen_loop', sr=22050, loop=True, desc='Handkarren / Schubkarre rollt (Loop 3 s): rhythmisches Quietschen, Kies', peak=-20)
def karren(r, i):
    d = 3.0
    t = tt(d)
    rot = 0.5 + 0.5 * np.sin(TAU * (1 / 1.0) * t)
    sq = sine(900 + 250 * rot, d) * rot ** 3 * 0.1
    gr = bp(white(d, r), 600, 5000, 2, circ=True) * (0.4 + 0.2 * rot)
    return sq + gr * 0.4
