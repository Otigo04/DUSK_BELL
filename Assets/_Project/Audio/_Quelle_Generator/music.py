"""Musik: eigene Kompositionen, per Code gespielt (Instrumente aus Modal-/Additiv-/Karplus-Strong-Synthese).
Stil laut Style-Bibel: cozy-melancholisch (Stardew Valley / Eastward / Hyper Light Drifter), Nacht = Drones und Luecken.
Tonart-Zentrum a-Moll. Leitmotiv "Dusk Bell": E5 - C5 - D5 - E5 (kehrt in Titel, Nacht-sicher, Morgen, Dorf-Tag wieder).
Loops sind nahtlos (Mix loop=True, Hall zirkulaer). 1910: nur akustische Instrumente. Radio (Opening Step 3): Schlager."""
import numpy as np

import nwaudio as nw
from nwaudio import (sound, white, bp, lp, hp, thump, env_ar, modal, click, layer, sparse, tt, n_, TAU, tv_filter,
                     reverb, colored, voice, sine, tri, midi, note, Mix, chord, parse, additive, pluck, adsr)
import sfx_world as wld

M = 'Music'
SRM = 22050


# --------------------------------------------------------------------------- Instrumente

def env_n(d, a, rel, sus=0.9):
    return adsr(d + rel, a, 0.08, sus, rel)


def pad(f, d, r, a=0.6, rel=1.0, bright=1600, det=0.005, k=3):
    tot = d + rel
    y = np.zeros(n_(tot))
    for j in range(k):
        y += nw.saw(f * (1 + (j - (k - 1) / 2) * det), tot, r.random())
    return lp(y / k, bright, 2) * env_n(d, a, rel)


def strings(f, d, r, a=0.35, rel=0.6, bright=2600, trem=0.0):
    tot = d + rel
    t = tt(tot)
    vib = 1 + 0.004 * np.sin(TAU * 5.2 * t + r.random() * 6)
    y = sum(nw.saw(f * vib * (1 + off), tot, r.random()) for off in (-0.007, -0.002, 0.003, 0.008)) / 4
    y = lp(y, bright, 2) * env_n(d, a, rel)
    if trem:
        y = y * (1 - trem + trem * np.sin(TAU * 7.0 * t + r.random()) ** 2)
    return y


def cello(f, d, r, a=0.12, rel=0.4):
    tot = d + rel
    t = tt(tot)
    vib = 1 + 0.005 * np.sin(TAU * 4.8 * t) * np.clip(t / 0.4, 0, 1)
    y = nw.saw(f * vib, tot) + 0.4 * nw.saw(f * vib * 1.003, tot, 0.3)
    return lp(y, 1100, 2) * env_n(d, a, rel)


def box(f, r=None):
    y = modal([f, f * 2.01, f * 4.17, f * 6.9], [1, 0.35, 0.12, 0.05], [1.7, 0.8, 0.3, 0.15], 2.0)
    return layer((y, 1.0), (click(0.01, 3000, 9000, 0.002, r), 0.1)) if r is not None else y


def glock(f, r=None):
    return modal([f, f * 2.76, f * 5.4, f * 8.93], [1, 0.4, 0.2, 0.1], [1.6, 0.7, 0.3, 0.15], 2.0)


def piano(f, d, r, honky=False):
    dur = max(d, 0.25) + 1.6
    k = max(1.0, np.log2(f / 110.0))
    base = max(0.8, 3.4 - 0.6 * k)
    amps = [1, 0.75, 0.5, 0.4, 0.3, 0.2, 0.14, 0.1]
    t60 = [base / (1 + 0.5 * j) for j in range(8)]
    y = additive(f, dur, amps, t60, inharm=0.0004)
    y = layer((y, 1.0), (click(0.03, min(f * 2, 4000), 5500, 0.005, r), 0.4))[:len(y)]
    if honky:
        y = y + 0.7 * additive(f * 1.006, dur, amps, t60, inharm=0.0007)
        y = lp(y, 6000, 2)
    off = np.exp(-np.maximum(tt(dur) - d, 0) / 0.18)
    return y * off


def organ(f, d, r, a=0.05, rel=0.35):
    tot = d + rel
    y = additive(f, tot, [1, 0.6, 0.45, 0.3, 0.2, 0.12], [tot * 3] * 6) * env_n(d, a, rel)
    return layer((y, 1.0), (bp(white(0.06, r), 1200, 4000) * np.exp(-tt(0.06) / 0.02), 0.05))[:n_(tot)]


def choir(f, d, r, a=0.7, rel=1.0):
    tot = d + rel
    return voice(f, tot, [(720, 9, 1.0), (1150, 9, 0.5), (2700, 9, 0.12)], r, breath=0.04, jit=0.008) * env_n(d, a, rel)


def harpsi(f, d, r):
    y = pluck(f, 1.3, r, 0.992, 0.9)
    return layer((y, 1.0), (click(0.01, 2500, 8000, 0.002, r), 0.1))[:len(y)]


def bass_pluck(f, d, r):
    return pluck(f, d + 0.5, r, 0.995, 0.15) * 1.5


def flute(f, d, r, a=0.07, rel=0.25):
    tot = d + rel
    t = tt(tot)
    vib = 1 + 0.006 * np.sin(TAU * 5.0 * t) * np.clip((t - 0.2) / 0.3, 0, 1)
    y = nw.sine(f * vib, tot) + 0.22 * nw.sine(f * 2 * vib, tot) + 0.06 * nw.sine(f * 3 * vib, tot)
    y += 0.05 * bp(white(tot, r), 2000, 5500)
    return y * env_n(d, a, rel)


def accordion(f, d, r, a=0.02, rel=0.1):
    tot = d + rel
    t = tt(tot)
    y = nw.saw(f * 1.004, tot) + nw.saw(f * 0.996, tot, 0.5) + 0.5 * nw.square(f, tot, 0.35)
    y = lp(y, 3400, 2) * (1 - 0.12 + 0.12 * np.sin(TAU * 6.5 * t))
    return y * env_n(d, a, rel, 0.85)


def oompah(f, d=0.3, r=None):
    t = tt(0.3)
    return lp(tri(np.full(len(t), f), 0.3) + 0.5 * nw.square(np.full(len(t), f), 0.3, 0.4), 700, 2) * np.exp(-t / 0.13)


def kick(r):
    return layer((thump(0.35, 130, 46, 0.09), 1.0), (click(0.02, 800, 3000, 0.004, r), 0.2))


def snare(r):
    return bp(white(0.25, r), 1500, 7000) * env_ar(0.25, 0.001, 0.07) + sine(190.0, 0.25) * np.exp(-tt(0.25) / 0.05) * 0.5


def brush(r):
    return bp(white(0.2, r), 3000, 9000) * env_ar(0.2, 0.02, 0.07) * 0.5


def hat(r):
    return hp(white(0.1, r), 7000) * env_ar(0.1, 0.001, 0.02)


def tom(f):
    return thump(0.5, f * 1.6, f, 0.14)


def wblock(f=900.0):
    return modal([f, f * 1.77], [1, 0.4], [0.05, 0.03], 0.1)


# --------------------------------------------------------------------------- Sequencer

class Song:
    def __init__(s, bpm, bars, r, beats=4):
        s.rub = r.uniform(0.05, 0.11)      # Rubato (Beats), periodisch ueber den Loop -> Naht bleibt exakt
        s.rph = r.uniform(0, TAU)
        s.spb = 60.0 / bpm
        s.bpb = beats
        s.bars = bars
        s.sec = bars * beats * s.spb
        s.r = r
        s.tr = {}

    def t(s, name):
        return s.tr.setdefault(name, Mix(s.sec, True))

    def dt(s):
        """Leichte Verstimmung pro Ton (+-3 Cent): echte Instrumente sind nie exakt gleich."""
        return 2.0 ** (s.r.normal(0, 3.0) / 1200.0)

    def put(s, name, sig, beat, gain=1.0, jit=0.009):
        total = s.bars * s.bpb
        b = beat + s.rub * (np.sin(TAU * beat / total + s.rph) + 0.4 * np.sin(2 * TAU * beat / total + 2 * s.rph))
        accent = 1.0 + (0.08 if abs(beat % s.bpb) < 1e-6 else 0.0)
        s.t(name).add(sig, b * s.spb + s.r.normal(0, jit), gain * accent * s.r.uniform(0.85, 1.05))

    def line(s, name, inst, seq, beat0=0.0, gain=1.0, hold=0.96):
        b = beat0
        for m, d in parse(seq):
            if m is not None:
                s.put(name, inst(midi(m) * s.dt(), d * s.spb * hold), b, gain)
            b += d
        return b

    def hold(s, name, inst, chords, octave, gain=1.0, per=1, sel=None, skip=0):
        """Jeder Akkord haelt per Takte; sel waehlt Akkordtoene (Indizes)."""
        for i, c in enumerate(chords):
            if c is None:
                continue
            ns = chord(c, octave)
            for k, m in enumerate(ns):
                if sel is None or k in sel:
                    s.put(name, inst(midi(m) * s.dt(), per * s.bpb * s.spb * 0.98), (i * per + skip) * s.bpb, gain)

    def arp(s, name, inst, chords, octave, pattern, step=0.5, gain=1.0, per=1):
        for i, c in enumerate(chords):
            if c is None:
                continue
            ns = chord(c, octave)
            ns = ns + [ns[0] + 12]
            n = int(per * s.bpb / step)
            for k in range(n):
                m = ns[pattern[k % len(pattern)] % len(ns)]
                s.put(name, inst(midi(m) * s.dt(), step * s.spb * 1.5), i * per * s.bpb + k * step, gain)

    def out(s, gains=None):
        gains = gains or {}
        y = np.zeros(n_(s.sec))
        for k, m in s.tr.items():
            y[:len(m.buf)] += m.buf[:len(y)] * gains.get(k, 1.0)
        return y


def finish(song, r, gains=None, rt=1.6, mix_=0.22, damp=4500, tone=None):
    y = song.out(gains)
    y = reverb(y, r, rt, mix_, damp, circ=True)
    if tone:
        y = lp(y, tone, 2, circ=True)
    return y


# --------------------------------------------------------------------------- Stuecke

@sound(M, 'mus_titel', sr=SRM, loop=True, desc='Titelbild / Intro "DUSK BELL": duestere Spieluhr-Melodie in a-Moll, Dronen-Pad, tiefe Glocke alle 4 Takte (Leitmotiv, 45 s)', peak=-10)
def mus_titel(r, i):
    s = Song(64, 12, r)
    ch = ['Am', 'F', 'C', 'G', 'Am', 'F', 'Dm', 'E', 'Am', 'F', 'E', 'Am']
    mel = ['E5:1.5 C5:.5 D5:1 E5:1', 'F5:1.5 A5:.5 G5:1 F5:1', 'E5:1.5 G5:.5 C6:1 G5:1', 'D5:2 B4:1 D5:1',
           'E5:1.5 A5:.5 G5:1 E5:1', 'F5:1.5 C6:.5 A5:1 F5:1', 'D5:1 F5:1 A5:1 F5:1', 'G#5:1.5 B5:.5 E6:2',
           'A5:1.5 E5:.5 C5:1 E5:1', 'C5:2 A4:1 F4:1', 'B4:1.5 G#4:.5 E4:2', 'A4:4']
    for b, m in enumerate(mel):
        s.line('box', lambda f, d: box(f, r), m, b * 4, 0.9)
    s.hold('pad', lambda f, d: pad(f, d, r, 1.2, 1.5, 900), ch, 3, 0.35)
    s.hold('bass', lambda f, d: cello(f, d, r, 0.3, 0.8), ch, 2, 0.5, sel=[0])
    for b in (0, 4, 8):
        s.put('bell', wld.church_bell(110.0, 7.0, r, strike=0.6) * 0.5, b * 4, 0.35)
    return finish(s, r, rt=2.4, mix_=0.3, damp=4000)


@sound(M, 'mus_radio_schlager', sr=SRM, loop=True, desc='Autoradio, Opening Step 3 (Fahrt): froehlicher Akkordeon-Schlager in C-Dur mit Oompah, durch Radio-Filter. Faellt in Step 4 ins Rauschen (in Unity ausblenden)', peak=-10)
def mus_schlager(r, i):
    s = Song(112, 16, r)
    ch = ['C', 'C', 'F', 'C', 'G7', 'G7', 'C', 'C'] * 2
    A = ['E5:1 G5:1 C6:1 G5:1', 'E5:1 G5:.5 E5:.5 D5:2', 'F5:1 A5:1 C6:1 A5:1', 'G5:2 E5:2',
         'D5:1 G5:1 B5:1 G5:1', 'F5:1 D5:1 G5:2', 'E5:1 G5:1 C6:1 E6:1', 'D6:1 C6:1 G5:2']
    B = ['C6:1 G5:1 E5:1 G5:1', 'E5:1 G5:.5 E5:.5 D5:2', 'F5:1 A5:1 C6:1 F6:1', 'E6:2 C6:2',
         'D6:1 B5:1 G5:1 B5:1', 'D6:1 B5:1 G5:2', 'E6:1 C6:1 G5:1 E5:1', 'D5:1 G5:1 C5:2']
    for b, m in enumerate(A + B):
        s.line('acc', lambda f, d: accordion(f, d, r), m, b * 4, 0.8)
    for b, c in enumerate(ch):
        ns = chord(c, 3)
        for k in range(4):
            if k % 2 == 0:
                s.put('bass', oompah(midi(ns[0] - 12)), b * 4 + k, 0.8)
            else:
                for m in ns[1:3] + [ns[0] + 12]:
                    s.put('chord', oompah(midi(m + 12)), b * 4 + k, 0.3)
            s.put('perc', brush(r), b * 4 + k + 0.5, 0.35)
    y = s.out()
    y = reverb(y, r, 0.5, 0.1, 5000, circ=True)
    return nw.lofi(y, r, 280, 4800, 0.01, 0.4, circ=True)


@sound(M, 'mus_dorf_tag', sr=SRM, loop=True, desc='Dorf am Tag: warme Gitarren-Arpeggien, Glockenspiel-Melodie, melancholisch aber gemuetlich (48 s)', peak=-10)
def mus_dorf_tag(r, i):
    s = Song(80, 16, r)
    ch = ['Am7', 'Fmaj7', 'C', 'G', 'Am7', 'Dm7', 'E7', 'Am'] * 2
    s.arp('pluck', lambda f, d: pluck(f, 1.2, r, 0.994, 0.45), ch, 3, [0, 2, 1, 3, 2, 1, 3, 2], 0.5, 0.55)
    s.hold('pad', lambda f, d: pad(f, d, r, 0.8, 1.0, 1100), ch, 3, 0.18, sel=[1, 2])
    s.hold('bass', lambda f, d: bass_pluck(f, d, r), ch, 2, 0.45, sel=[0])
    m = ['E5:2 C5:1 D5:1', 'F5:2 D5:1 A4:1', 'G#5:1 B5:1 E5:2', 'A5:3 R:1']
    m2 = ['C5:1.5 E5:.5 G5:1 E5:1', 'D5:1.5 F5:.5 A5:1 F5:1', 'B4:1 G#4:1 B4:1 E5:1', 'A4:4']
    for b, line in enumerate(m):
        s.line('lead', lambda f, d: glock(f, r), line, (4 + b) * 4, 0.55)
    for b, line in enumerate(m2):
        s.line('lead', lambda f, d: glock(f, r), line, (12 + b) * 4, 0.5)
    return finish(s, r, rt=1.4, mix_=0.2)


@sound(M, 'mus_dorf_abend', sr=SRM, loop=True, desc='Daemmerung (Sheriff laeutet gleich, Verriegeln): Spannung baut sich auf, Cello-Drone, ferne Glockentoene, ungeloeste Dominante (44 s)', peak=-10)
def mus_dorf_abend(r, i):
    s = Song(66, 12, r)
    ch = ['Dm', 'Dm', 'Bb', 'Bb', 'Gm', 'Gm', 'A', 'A', 'Dm', 'Bb', 'Gm', 'A']
    s.hold('str', lambda f, d: strings(f, d, r, 0.9, 1.0, 1800), ch, 3, 0.45)
    s.hold('cello', lambda f, d: cello(f, d, r, 0.4, 0.8), ch, 2, 0.5, sel=[0])
    for b in (0, 4, 8):
        s.line('bell', lambda f, d: glock(f, r), 'E5:1 R:.5 A4:2.5', b * 4 + 2, 0.5)
    for k in range(12 * 4):
        s.put('tick', wblock(1100.0 if k % 2 == 0 else 880.0), k, 0.12)
    s.put('rise', strings(midi(note('A5')), 8.0, r, 5.0, 2.0, 3000, 0.4), 11 * 4 - 8, 0.15)
    return finish(s, r, rt=2.0, mix_=0.28, damp=4200)


@sound(M, 'mus_nacht_belagerung', sr=SRM, loop=True, desc='Nachtbelagerung: keine Melodie. Tiefe Dissonanz (A/B-Flat), schwebende Streicher, einzelne Glasobertoene, dumpfer Puls, viel Stille (48 s)', peak=-11)
def mus_nacht(r, i):
    s = Song(50, 10, r)
    L = s.sec
    for f, g in ((55.0, 0.6), (58.27, 0.5), (82.4, 0.25), (110.0, 0.15)):
        s.put('drone', lp(nw.saw(np.full(n_(L), f), L), 260, 2, circ=True) * (0.7 + 0.3 * np.sin(TAU * tt(L) / L * (1 + int(f) % 3))), 0, g)
    for _ in range(7):
        f = midi(note(r.choice(['E6', 'F6', 'A#5', 'B5', 'C#6'])))
        s.put('glass', sine(f, 3.0) * np.sin(np.pi * tt(3.0) / 3.0) ** 2 * 0.3, r.uniform(0, 38), 0.5)
    for k in range(int(L / 1.2)):
        if r.random() < 0.5:
            s.put('pulse', thump(0.6, 65, 35, 0.15), k * 1.2 / s.spb, 0.4)
    for _ in range(2):
        f = midi(note(r.choice(['A3', 'E3'])))
        s.put('bow', strings(f, 6.0, r, 3.0, 3.0, 1500, 0.5), r.uniform(0, 38), 0.3)
    return finish(s, r, rt=3.2, mix_=0.35, damp=3000)


@sound(M, 'mus_nacht_sicher', sr=SRM, loop=True, desc='Nacht im Schutzraum (Kamin, Talisman, Lichtinsel): zarte Spieluhr, weiches Pad, Leitmotiv ganz leise - Sicherheit, aber nicht Frieden (48 s)', peak=-11)
def mus_nacht_sicher(r, i):
    s = Song(60, 12, r)
    ch = ['Am', 'F', 'C', 'G', 'Am', 'F', 'Dm', 'E', 'Am', 'F', 'C', 'Am']
    s.arp('box', lambda f, d: box(f, r), ch, 4, [0, 2, 1, 3], 1.0, 0.35)
    s.hold('pad', lambda f, d: pad(f, d, r, 1.5, 1.5, 800), ch, 3, 0.3)
    s.hold('bass', lambda f, d: cello(f, d, r, 0.3, 0.8), ch, 2, 0.3, sel=[0])
    s.line('motif', lambda f, d: box(f, r), 'E5:2 C5:1 D5:1 E5:4', 4 * 4, 0.35)
    s.line('motif', lambda f, d: box(f, r), 'E5:2 C5:1 D5:1 E5:4', 8 * 4, 0.3)
    return finish(s, r, rt=2.2, mix_=0.3, damp=3500)


@sound(M, 'mus_bar', sr=SRM, loop=True, desc='Ilhans Bar: verstimmtes Honky-Tonk-Klavier, a-Moll-Walzer, Kontrabass-Zupfen. Leicht schief, leicht traurig (43 s)', peak=-10)
def mus_bar(r, i):
    s = Song(100, 24, r, beats=3)
    A = ['Am', 'Am', 'Dm', 'Dm', 'E7', 'E7', 'Am', 'Am']
    B = ['C', 'C', 'G', 'G', 'F', 'F', 'E7', 'E7']
    ch = A + B + A
    pi = lambda f, d: piano(f, d, r, honky=True)
    mA = ['E5:1 A5:1 C6:1', 'B5:2 A5:1', 'F5:1 A5:1 D6:1', 'C6:2 A5:1', 'G#5:1 B5:1 D6:1', 'C6:2 B5:1', 'A5:1 E5:1 C5:1', 'A4:3']
    mB = ['G5:1 E5:1 C5:1', 'E5:2 G5:1', 'D5:1 G5:1 B5:1', 'A5:2 G5:1', 'A5:1 F5:1 C5:1', 'F5:2 A5:1', 'G#5:1 B5:1 E5:1', 'E5:3']
    mA2 = ['E5:1 A5:1 C6:1', 'D6:2 C6:1', 'F5:1 A5:1 D6:1', 'E6:2 C6:1', 'G#5:1 B5:1 D6:1', 'E6:2 D6:1', 'C6:1 A5:1 E5:1', 'A5:3']
    for b, m in enumerate(mA + mB + mA2):
        s.line('rh', pi, m, b * 3, 0.65)
    for b, c in enumerate(ch):
        ns = chord(c, 3)
        s.put('lh', pi(midi(ns[0] - 12), 0.9), b * 3, 0.55)
        for k in (1, 2):
            for m in ns[1:]:
                s.put('lh', pi(midi(m), 0.4), b * 3 + k, 0.28)
        s.put('bass', bass_pluck(midi(ns[0] - 12), 0.5, r), b * 3, 0.5)
    return finish(s, r, rt=0.9, mix_=0.15, damp=5000)


@sound(M, 'mus_revier', sr=SRM, loop=True, desc='Sheriff-Stube (Bulut erste Begegnung): einzelne Klaviertoene, Cello-Drone, tickende Uhr - mueder, nicht boese (44 s)', peak=-11)
def mus_revier(r, i):
    s = Song(54, 10, r)
    ch = ['Am', 'F', 'Dm', 'E', 'Am', 'F', 'C', 'E', 'Am', 'Am']
    s.hold('cello', lambda f, d: cello(f, d, r, 0.5, 1.0), ch, 2, 0.55, sel=[0])
    s.hold('pad', lambda f, d: pad(f, d, r, 1.2, 1.5, 700), ch, 3, 0.18, sel=[1, 2])
    pm = ['E4:2 A4:2', 'C5:2 A4:2', 'D5:3 F4:1', 'G#4:2 B4:2', 'E5:2 C5:2', 'A4:2 F4:2', 'G4:2 E4:2', 'B4:3 G#4:1', 'A4:4', 'R:4']
    for b, m in enumerate(pm):
        s.line('piano', lambda f, d: piano(f, d, r), m, b * 4, 0.6)
    for k in range(10 * 4):
        s.put('tick', wblock(1250.0 if k % 2 == 0 else 1000.0), k, 0.07)
    return finish(s, r, rt=2.0, mix_=0.28, damp=4000)


@sound(M, 'mus_beerdigung', sr=SRM, loop=True, desc='Beerdigung / Friedhof (Opening Step 9, Zeitlupenfahrt): Orgel und Chor-Pad in d-Moll, kleine Glocke, Tuch am Mund (46 s)', peak=-10)
def mus_beerdigung(r, i):
    s = Song(52, 10, r)
    ch = ['Dm', 'Bb', 'Gm', 'Dm', 'Bb', 'A', 'Dm', 'Gm', 'A', 'Dm']
    s.hold('organ', lambda f, d: organ(f, d, r), ch, 3, 0.4)
    s.hold('organ', lambda f, d: organ(f, d, r), ch, 2, 0.35, sel=[0])
    s.hold('choir', lambda f, d: choir(f, d, r), ch, 4, 0.25, sel=[1, 2])
    mel = ['D5:2 F5:2', 'D5:2 Bb4:2', 'D5:2 G5:2', 'F5:4', 'D5:2 F5:2', 'E5:2 C#5:2', 'D5:3 R:1', 'Bb4:2 D5:2', 'C#5:2 E5:2', 'D5:4']
    for b, m in enumerate(mel):
        s.line('lead', lambda f, d: choir(f, d, r, 0.5, 0.9), m, b * 4, 0.35)
    for b in (0, 4, 8):
        s.put('bell', wld.church_bell(midi(note('D4')), 5.0, r) * 0.5, b * 4, 0.3)
    return finish(s, r, rt=2.8, mix_=0.35, damp=3800)


@sound(M, 'mus_villa', sr=SRM, loop=True, desc='Villa der Madame Elenora: kalter, praeziser Walzer auf dem Cembalo in e-Moll, Glasharmonika. Hoeflich wie ein Vertrag (39 s)', peak=-10)
def mus_villa(r, i):
    s = Song(92, 16, r, beats=3)
    ch = ['Em', 'B7', 'Em', 'Am', 'C', 'B7', 'Em', 'Em', 'Em', 'B7', 'Em', 'Am', 'C', 'B7', 'Em', 'Em']
    runs = {'Em': 'B4:.5 E5:.5 G5:.5 B5:.5 G5:.5 E5:.5', 'B7': 'D#5:.5 F#5:.5 A5:.5 B5:.5 A5:.5 F#5:.5',
            'Am': 'A4:.5 C5:.5 E5:.5 A5:.5 E5:.5 C5:.5', 'C': 'G4:.5 C5:.5 E5:.5 G5:.5 E5:.5 C5:.5'}
    for b, c in enumerate(ch):
        seq = runs[c]
        if b >= 8:
            seq = ' '.join('%s%d:%s' % (n.split(':')[0][:-1], int(n.split(':')[0][-1]) + (1 if k % 2 == 0 else 0), n.split(':')[1])
                           for k, n in enumerate(seq.split()))
        s.line('rh', lambda f, d: harpsi(f, d, r), seq, b * 3, 0.6, 1.0)
        ns = chord(c, 3)
        s.put('lh', harpsi(midi(ns[0] - 12), 0.6, r), b * 3, 0.6)
        for k in (1, 2):
            for m in ns[1:]:
                s.put('lh', harpsi(midi(m), 0.3, r), b * 3 + k, 0.22)
    s.hold('glass', lambda f, d: sine(f, d + 1.0) * adsr(d + 1.0, 0.6, 0.1, 0.8, 1.0), ch[::2], 5, 0.07, per=2, sel=[0, 1])
    return finish(s, r, rt=1.6, mix_=0.22, damp=6500)


@sound(M, 'mus_wald_tag', sr=SRM, loop=True, desc='Wald am Tag (Erkundung, Waldrand bis Zone 2): Floete, Zupf-Arpeggio, weiche Handtrommel in d-Dorisch - neugierig, wachsam (46 s)', peak=-10)
def mus_wald(r, i):
    s = Song(84, 16, r)
    ch = ['Dm7', 'C', 'Dm7', 'G', 'Dm7', 'C', 'Bb', 'A'] * 2
    s.arp('pluck', lambda f, d: pluck(f, 1.0, r, 0.992, 0.5), ch, 3, [0, 1, 2, 3, 2, 1], 0.5, 0.4)
    s.hold('pad', lambda f, d: pad(f, d, r, 0.8, 1.0, 1000), ch, 3, 0.15, sel=[1, 2])
    s.hold('bass', lambda f, d: bass_pluck(f, d, r), ch, 2, 0.35, sel=[0])
    mel = ['D5:1 F5:1 A5:2', 'G5:1 E5:1 C5:2', 'D5:1 F5:1 A5:1 C6:1', 'B5:2 G5:2', 'A5:1 F5:1 D5:2', 'G5:1 E5:1 C5:2', 'D5:2 F5:2', 'E5:3 R:1']
    for b, m in enumerate(mel):
        s.line('flute', lambda f, d: flute(f, d, r), m, (b + (0 if b < 8 else 8)) * 4 if b < 8 else b * 4, 0.45)
    for b in range(0, 16, 2):
        s.put('drum', tom(110.0) * 0.5, b * 4, 0.4)
        s.put('drum', wblock(700.0), b * 4 + 2.5, 0.2)
    return finish(s, r, rt=1.5, mix_=0.22)


@sound(M, 'mus_flucht', sr=SRM, loop=True, desc='Flucht / Verfolgung (Tagesjagd, Wecklevel 4+): treibender Bass-Ostinato, Kick, Streicher-Stabs mit kleiner Sekunde (36 s)', peak=-9)
def mus_flucht(r, i):
    s = Song(132, 20, r)
    ch = ['Am', 'Am', 'Bb', 'Am', 'Am', 'Am', 'F', 'E', 'Am', 'Am', 'Bb', 'Am', 'Dm', 'Dm', 'F', 'E', 'Am', 'Bb', 'Am', 'E']
    for b, c in enumerate(ch):
        root = chord(c, 2)[0]
        for k in range(8):
            s.put('bass', lp(nw.saw(np.full(n_(0.25), midi(root + (12 if k % 4 == 3 else 0))), 0.25), 700, 2) * np.exp(-tt(0.25) / 0.2), b * 4 + k * 0.5, 0.55, 0.002)
        for k in (0, 1, 2, 3):
            s.put('kick', kick(r), b * 4 + k, 0.7, 0.002)
        for k in (1, 3):
            s.put('snare', snare(r), b * 4 + k, 0.45, 0.002)
        for k in (0.5, 1.5, 2.5, 3.5):
            s.put('stab', strings(midi(chord(c, 4)[1]), 0.18, r, 0.01, 0.1, 2200), b * 4 + k, 0.3)
            s.put('stab', strings(midi(chord(c, 4)[2] + (1 if c == 'Am' else 0)), 0.18, r, 0.01, 0.1, 2200), b * 4 + k, 0.2)
        s.put('hat', hat(r), b * 4 + 0.5, 0.2)
    return finish(s, r, rt=0.6, mix_=0.12, damp=4000)


@sound(M, 'mus_kampf', sr=SRM, loop=True, desc='Kampf (10-30 s, selten): Toms, scharfer Saegezahn-Ostinato, dissonante Treffer. Kurz und bedrohlich (26 s)', peak=-9)
def mus_kampf(r, i):
    s = Song(150, 16, r)
    for b in range(16):
        note_ = 'A1' if b % 4 != 3 else 'Bb1'
        for k in range(8):
            s.put('bass', lp(nw.saw(np.full(n_(0.2), midi(note(note_))), 0.2), 900, 2) * np.exp(-tt(0.2) / 0.15), b * 4 + k * 0.5, 0.5, 0.002)
        s.put('tom', tom(80.0), b * 4, 0.7, 0.002)
        s.put('tom', tom(95.0), b * 4 + 1.5, 0.5, 0.002)
        s.put('tom', tom(70.0), b * 4 + 2.5, 0.6, 0.002)
        s.put('snare', snare(r), b * 4 + 3, 0.5, 0.002)
        if b % 2 == 0:
            s.put('hit', strings(midi(note('E4')), 0.5, r, 0.02, 0.2, 2500) + strings(midi(note('F4')), 0.5, r, 0.02, 0.2, 2500), b * 4 + 2, 0.25)
    return finish(s, r, rt=0.7, mix_=0.15, damp=3500)


@sound(M, 'mus_morgen', sr=SRM, loop=True, desc='Morgen / Lagebericht: zerbrechliche Hoffnung, Spieluhr-Arpeggio in C-Dur mit Leitmotiv, Pad (27 s)', peak=-11)
def mus_morgen(r, i):
    s = Song(72, 8, r)
    ch = ['C', 'G', 'Am', 'F', 'C', 'G', 'F', 'C']
    s.arp('box', lambda f, d: box(f, r), ch, 4, [0, 1, 2, 3, 2, 1], 0.5, 0.45)
    s.hold('pad', lambda f, d: pad(f, d, r, 1.0, 1.2, 1100), ch, 3, 0.25)
    s.hold('bass', lambda f, d: cello(f, d, r, 0.3, 0.6), ch, 2, 0.3, sel=[0])
    s.line('motif', lambda f, d: glock(f, r), 'E5:1.5 C5:.5 D5:1 E5:1 G5:2 E5:1 D5:1 C5:4', 8, 0.4)
    return finish(s, r, rt=1.6, mix_=0.25)


# --------------------------------------------------------------------------- Stinger (einmalig)

STG = 'Music/Stinger'


@sound(STG, 'stg_grinsen', sr=SRM, desc='Das Grinsen wird sichtbar: gleitende Violinen, Cluster, harter Schlag, danach Stille (3 s)', peak=-5)
def stg_grinsen(r, i):
    d = 3.0
    t = tt(d)
    glide = nw.saw(np.linspace(900, 2200, len(t)), d) * np.minimum(1, t / 1.2) * np.exp(-np.maximum(t - 1.3, 0) / 0.1)
    cluster = sum(strings(midi(note(n)), 1.5, r, 0.05, 0.4, 3500) for n in ('E5', 'F5', 'F#5', 'B5'))
    hit = thump(1.2, 90, 32, 0.25)
    return reverb(layer((lp(glide, 4000, 2), 0.3), (cluster, 0.25, 1.3), (hit, 1.2, 1.3)), r, 1.8, 0.3, 4500)


@sound(STG, 'stg_tod', sr=SRM, desc='Spieler stirbt: tiefer Orgelakkord, Glocke, Verklingen (8 s)', peak=-6)
def stg_tod(r, i):
    d = 8.0
    ch = sum(organ(midi(m), 5.0, r, 0.3, 3.0) for m in chord('Am', 2) + [57])
    bell = wld.church_bell(110.0, 7.0, r)
    return reverb(layer((ch, 0.4), (bell, 0.6, 0.1)), r, 3.0, 0.4, 3000)


@sound(STG, 'stg_nacht_ueberlebt', sr=SRM, desc='Nacht ueberlebt: Moll loest sich nach Dur auf, Klavier und Streicher (7 s)', peak=-8)
def stg_ueberlebt(r, i):
    a = sum(strings(midi(m), 3.0, r, 0.6, 1.5, 1800) for m in chord('Am', 3))
    b = sum(strings(midi(m), 3.5, r, 0.8, 2.0, 2200) for m in chord('A', 3))
    return reverb(layer((a, 0.25), (b, 0.3, 3.0), (piano(midi(note('E5')), 1.2, r), 0.6, 2.9), (piano(midi(note('A5')), 2.0, r), 0.5, 3.5)), r, 2.6, 0.35, 5000)


@sound(STG, 'stg_entdeckung', sr=SRM, desc='Hinweis entdeckt (Zettel, Totenbuch): Spieluhr-Arpeggio E-H-Gis-E, dunkler Swell darunter (4 s)', peak=-8)
def stg_entdeckung(r, i):
    out = [(box(midi(note(n)), r), 0.7, k * 0.22) for k, n in enumerate(['E5', 'B5', 'G#5', 'E6'])]
    sw = lp(nw.saw(np.full(n_(3.5), 82.4), 3.5), 300, 2) * np.sin(np.pi * tt(3.5) / 3.5) ** 2
    return reverb(layer(*out, (sw, 0.5)), r, 2.0, 0.35, 6000)


@sound(STG, 'stg_loop_neustart', sr=SRM, desc='Der Tag beginnt von vorn (Loop): umgekehrte Glocke schwillt an, weicher Akkord (6 s)', peak=-7)
def stg_loop(r, i):
    b = wld.church_bell(146.8, 5.0, r)[::-1] * np.linspace(0.2, 1.0, n_(5.0) + 0)[:n_(5.0)]
    ch = sum(pad(midi(m), 1.5, r, 0.2, 2.0, 1500) for m in chord('Am', 3))
    return reverb(layer((b, 0.8), (ch, 0.4, 4.6)), r, 2.4, 0.35, 4500)


@sound(STG, 'stg_gefahr_naht', sr=SRM, desc='Gefahr naht (Monster in Sicht, Tagesjagd): tiefes Tremolo schwillt an, Dissonanz, Schlag (3,5 s)', peak=-7)
def stg_gefahr(r, i):
    a = sum(strings(midi(note(n)), 3.0, r, 2.0, 0.3, 2000, 0.7) for n in ('A3', 'Bb3', 'E4'))
    return reverb(layer((a, 0.35), (thump(1.0, 85, 34, 0.22), 1.2, 3.0)), r, 1.6, 0.25, 3500)
