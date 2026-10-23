"""Kampf: kurz, selten, bedrohlich (Kampfregeln). Werkzeuge: Axt, Dreschflegel, Machete, Laterne, Faust; Pistole/Flinte (Ilhan).
Kein Lebensbalken - Treffer und Atem tragen die Information."""
import numpy as np

import nwaudio as nw
from nwaudio import (sound, white, bp, lp, hp, thump, env_ar, modal, click, layer, sparse, tt, n_, TAU, tv_filter,
                     reverb, colored, voice, sine)
from sfx_doors import wood_hit, creak

K = 'SFX/Kampf'


def whoosh(d, lo, hi, r, tone=1.6, peak_at=0.45):
    t = tt(d)
    u = t / d
    sweep = lo + (hi - lo) * np.sin(np.pi * np.clip(u, 0, 1)) ** 1.0
    e = np.where(u < peak_at, np.sin(0.5 * np.pi * u / peak_at) ** 2, np.cos(0.5 * np.pi * (u - peak_at) / (1 - peak_at)) ** 2)
    return tv_filter(white(d, r), sweep, tone) * e


@sound(K, 'schlag_faust', n=3, desc='Schlag mit der Faust durch die Luft', peak=-10)
def schlag_faust(r, i):
    return whoosh(0.18, 600, 2200, r, 1.4)


@sound(K, 'schlag_messer', n=3, desc='Messer / Gartenschere: schnelles helles Zischen', peak=-9)
def schlag_messer(r, i):
    return whoosh(0.2, 1800, 6500, r, 1.8, 0.4)


@sound(K, 'schlag_axt', n=3, desc='Axt: langsamer, schwerer Schwung (verbraucht Ausdauer)', peak=-7)
def schlag_axt(r, i):
    return layer((whoosh(0.4, 250, 1400, r, 1.2, 0.55), 1.0), (lp(white(0.4, r), 200) * 0.2, 1.0))


@sound(K, 'schlag_flegel', n=3, desc='Dreschflegel: schwer, langsames Ausholen, Kettenklirren', peak=-7)
def schlag_flegel(r, i):
    chain = modal([2100, 3200, 4700], [0.3, 0.25, 0.15], [0.08, 0.06, 0.04], 0.2)
    return layer((whoosh(0.5, 220, 1100, r, 1.1, 0.6), 1.0), (chain, 0.4, 0.05), (chain, 0.3, 0.2))


@sound(K, 'schlag_machete', n=3, desc='Machete: schnell, durch Dickicht', peak=-8)
def schlag_machete(r, i):
    return layer((whoosh(0.25, 900, 4200, r, 1.5, 0.4), 1.0), (bp(sparse(0.2, 300, r), 2500, 8000) * np.exp(-tt(0.2) / 0.08), 0.3, 0.1))


@sound(K, 'treffer_stumpf', n=4, desc='Dumpfer Treffer auf Koerper (Faust, Flegel)', peak=-5)
def treffer_stumpf(r, i):
    return layer((thump(0.3, 110, 50, 0.07), 1.0), (bp(white(0.15, r), 200, 2200) * env_ar(0.15, 0.002, 0.03), 0.8),
                 (click(0.02, 800, 3000, 0.005, r), 0.5))


@sound(K, 'treffer_axt', n=3, desc='Axt trifft: Knacken, schwerer Schlag, Nachklingen', peak=-4)
def treffer_axt(r, i):
    return reverb(layer((click(0.1, 400, 4500, 0.02, r), 1.0), (thump(0.5, 95, 40, 0.12), 1.2),
                        (modal([r.uniform(180, 240), r.uniform(500, 700)], [0.6, 0.3], [0.25, 0.15], 0.5), 0.5)), r, 0.3, 0.08, 3000)


@sound(K, 'treffer_klinge', n=3, desc='Klinge trifft: kurzes, nasses Schneiden, ohne Blutorgie', peak=-7)
def treffer_klinge(r, i):
    return layer((tv_filter(white(0.14, r), lambda u: 4500 - 3000 * u, 1.4) * env_ar(0.14, 0.004, 0.04), 1.0),
                 (thump(0.2, 130, 70, 0.04), 0.6), (bp(white(0.2, r), 200, 900) * env_ar(0.2, 0.01, 0.05), 0.5))


@sound(K, 'treffer_monster', n=4, desc='Treffer auf ein Monster: schwerer als Mensch, mit tiefem, falschem Unterton', peak=-4)
def treffer_monster(r, i):
    under = voice(48, 0.5, [(180, 5, 1.0), (500, 4, 0.4)], r, breath=0.2, jit=0.05) * env_ar(0.5, 0.01, 0.2)
    return reverb(layer((treffer_stumpf(r, i), 1.0), (under, 0.7, 0.02), (hp(sparse(0.3, 400, r), 3000) * np.exp(-tt(0.3) / 0.07), 0.3)), r, 0.4, 0.1, 3000)


@sound(K, 'treffer_holz', n=3, desc='Schlag auf Holz (Tuer, Fass, Balken)', peak=-6)
def treffer_holz(r, i):
    return wood_hit(r.uniform(110, 190), 0.5, r, 1.0, 0.1)


@sound(K, 'schaden_spieler', n=3, desc='Spieler wird getroffen: dumpfer Schlag, Luft weg, kurzes Pfeifen im Ohr', peak=-4)
def schaden(r, i):
    d = 1.4
    t = tt(d)
    hit = layer((thump(0.4, 120, 45, 0.09), 1.2), (click(0.05, 600, 3500, 0.01, r), 0.7))
    air = tv_filter(white(0.4, r), lambda u: 1500 - 900 * u, 1.2) * np.sin(np.pi * tt(0.4) / 0.4) ** 1.5
    ring = sine(3700, d) * np.exp(-t / 0.5) * 0.12
    return layer((hit, 1.0), (air, 0.4, 0.05), (ring, 1.0, 0.04))


@sound(K, 'pistole_schuss', n=3, desc='Pistolenschuss (Revolver, 1910): scharfer Knall, Hall', peak=-2)
def pistole(r, i):
    crack = layer((click(0.12, 700, 9000, 0.012, r), 1.2), (thump(0.5, 160, 55, 0.08), 1.0), (lp(white(0.4, r), 900) * np.exp(-tt(0.4) / 0.1), 0.6))
    return reverb(crack, r, 1.1, 0.35, 5000)


@sound(K, 'flinte_schuss', n=2, desc='Flinte (Ilhan): tiefer, breiter Knall mit langem Hall', peak=-1)
def flinte(r, i):
    boom = layer((click(0.2, 200, 6000, 0.03, r), 1.2), (thump(0.9, 120, 35, 0.2), 1.4), (lp(white(0.8, r), 500) * np.exp(-tt(0.8) / 0.2), 0.8))
    return reverb(boom, r, 1.8, 0.4, 3500)


@sound(K, 'pistole_nachladen', n=2, desc='Revolver spannen und Trommel drehen', peak=-9)
def nachladen(r, i):
    parts = [(layer((click(0.02, 2000, 7000, 0.003, r), 1.0), (modal([1300, 2800], [0.4, 0.2], [0.06, 0.04], 0.15), 0.5)), 1.0, k * 0.09) for k in range(4)]
    parts.append((layer((modal([900, 2100, 3400], [0.7, 0.4, 0.2], [0.14, 0.1, 0.06], 0.3), 1.0), (thump(0.2, 180, 90, 0.03), 0.5)), 1.0, 0.45))
    return layer(*parts)


@sound(K, 'pistole_leer', desc='Abzug ohne Munition: trockenes Klicken', peak=-10)
def leer(r, i):
    return layer((click(0.03, 1500, 6000, 0.004, r), 1.0), (modal([1900, 3200], [0.4, 0.2], [0.05, 0.03], 0.1), 0.5))


@sound(K, 'waffe_bricht', n=3, desc='Waffe/Werkzeug bricht: Knacken, Splittern, Metallping (Haltbarkeit = 0)', peak=-4)
def waffe_bricht(r, i):
    crack = layer((click(0.15, 300, 6000, 0.03, r), 1.0), (hp(sparse(0.5, 700, r), 2500) * np.exp(-tt(0.5) / 0.1), 0.6),
                  (modal([r.uniform(2400, 3200), r.uniform(4100, 5200)], [0.5, 0.3], [0.5, 0.3], 0.7), 0.5), (thump(0.4, 140, 60, 0.07), 0.7))
    return reverb(crack, r, 0.5, 0.12, 4500)


@sound(K, 'ausweichen', n=4, desc='Ausweichsprung zur Seite (Fenster 0,3 s): Stoff, Staub, Landung', peak=-8)
def ausweichen(r, i):
    return layer((whoosh(0.22, 400, 2200, r, 1.2, 0.4), 0.8), (bp(white(0.3, r), 300, 3000) * env_ar(0.3, 0.01, 0.08), 0.5, 0.12),
                 (thump(0.25, 120, 55, 0.05), 0.7, 0.2), (hp(sparse(0.25, 250, r), 3000) * np.exp(-tt(0.25) / 0.07), 0.4, 0.2))


@sound(K, 'laterne_schwenken', n=3, desc='Laterne schwenken: Kette knarrt, Glas klingt, Flamme faucht (Monster weicht 2 s zurueck)', peak=-8)
def laterne_schwenken(r, i):
    chain = modal([2400, 3600, 5100, 6800], [0.3, 0.25, 0.2, 0.15], [0.09, 0.07, 0.05, 0.04], 0.3)
    flame = hp(white(0.5, r), 600) * env_ar(0.5, 0.08, 0.2) * 0.3
    return layer((whoosh(0.45, 300, 1500, r, 1.2, 0.5), 0.5), (chain, 0.4, 0.05), (chain, 0.25, 0.2), (flame, 0.6),
                 (creak(0.35, 300, 360, r, 0.5, (900, 1500)), 0.15))


@sound(K, 'laterne_abwehr', n=2, desc='Licht trifft das Monster: Zischen, es weicht zurueck', peak=-6)
def laterne_abwehr(r, i):
    hiss = tv_filter(white(1.0, r), lambda u: 5000 - 3000 * u, 1.2) * env_ar(1.0, 0.03, 0.3)
    core = voice(np.linspace(180, 90, n_(1.0)), 1.0, [(700, 5, 1.0), (1800, 5, 0.3)], r, breath=0.4, jit=0.06) * env_ar(1.0, 0.03, 0.4)
    return reverb(layer((hiss, 0.7), (core, 0.5)), r, 0.5, 0.15, 5000)


@sound(K, 'tablett_treffer', n=3, desc='Hausfrau schlaegt mit dem Tablett zu: Blech scheppert, schwerer Schlag', peak=-3)
def tablett(r, i):
    f = r.uniform(380, 460)
    clang = nw.hit(f, 0.9, r, 0.95, sec=1.1, n=14, ratio_pow=1.7, inharm=0.25, tilt=0.8, air=0.4)
    return reverb(layer((clang, 0.9), (thump(0.4, 130, 60, 0.07), 1.0)), r, 0.6, 0.15, 6000)


@sound(K, 'brot_wirft', n=3, desc='Brot geworfen / gereicht: weicher Aufprall (Hausfrau-Schwaeche)', peak=-10)
def brot_wirft(r, i):
    return layer((thump(0.25, 100, 60, 0.05), 0.8), (bp(white(0.15, r), 300, 2500) * env_ar(0.15, 0.004, 0.04), 0.6),
                 (hp(sparse(0.12, 500, r), 3000) * np.exp(-tt(0.12) / 0.04), 0.3))


@sound(K, 'hausfrau_betaeubt', desc='Hausfrau wehrlos (5 s): Ton sackt ab, Atem entweicht, Tablett kullert', peak=-6)
def betaeubt(r, i):
    d = 5.0
    t = tt(d)
    drone = voice(np.linspace(130, 60, len(t)), d, [(450, 5, 1.0), (1100, 5, 0.4)], r, breath=0.1, jit=0.03) * np.exp(-t / 2.5) * np.minimum(1, t / 0.1)
    roll = modal([420, 800, 1700], [0.3, 0.2, 0.1], [0.5, 0.3, 0.2], 1.0) * np.sin(TAU * 11 * tt(1.0)) ** 2
    return reverb(layer((drone, 0.8), (roll, 0.5, 0.6), (thump(0.4, 100, 50, 0.1), 0.6)), r, 0.8, 0.2, 4000)


@sound(K, 'name_enthuellt', desc='Der Gast hoert seinen Namen: Verkleidung wird 3 s durchsichtig. Anschwellender Glasschimmer, dann Riss', peak=-4)
def name_enthuellt(r, i):
    d = 3.4
    t = tt(d)
    sw = sum(sine(f, d) * np.minimum(1, (t / 2.6) ** 2) for f in (880, 1175, 1568, 2093)) * 0.25
    sw *= 1 + 0.3 * np.sin(TAU * 6 * t)
    air = tv_filter(white(d, r), lambda u: 800 + 5000 * u, 1.5) * np.minimum(1, t / 2.6) ** 2 * 0.3
    crack = layer((click(0.2, 800, 9000, 0.03, r), 1.0), (thump(0.8, 90, 40, 0.2), 1.0))
    sw = sw * np.where(t < 2.7, 1.0, np.exp(-(t - 2.7) / 0.2))
    return reverb(layer((sw, 0.6), (air, 0.7), (crack, 1.2, 2.7)), r, 1.2, 0.3, 6000)


@sound(K, 'monster_weicht', n=2, desc='Monster zieht sich zurueck: absinkendes Knurren, Rascheln, es verliert Interesse', peak=-8)
def weicht(r, i):
    d = 2.4
    t = tt(d)
    g = voice(np.linspace(95, 50, len(t)), d, [(350, 5, 1.0), (900, 4, 0.4)], r, breath=0.25, jit=0.06, kind='square') * np.exp(-t / 1.1)
    rus = hp(white(d, r), 1500) * env_ar(d, 0.5, 0.5) * 0.12
    return reverb(layer((g, 0.8), (rus, 0.7)), r, 0.8, 0.2, 3500)
