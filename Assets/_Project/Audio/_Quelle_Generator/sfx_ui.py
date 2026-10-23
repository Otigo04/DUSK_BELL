"""UI, Quests, Lagebericht, Tageszeit-Wechsel, Beziehungs-/Wissens-Feedback.
Bezug: UI-Cheatsheet (Hover nur Farbwechsel -> Hover-Ton minimal), Opening Sequence (Quest-HUD, Tutorial, Titel DUSK BELL),
Regelwerk (Phasen Morgen/Tag/Daemmerung/Nacht, Wecklevel 3/4), Dialogue Bible (Vertrauen -10..+10).
Tonart durchgehend a-Moll / C-Dur-Naehe, damit alles mit der Musik zusammenpasst."""
import numpy as np

import nwaudio as nw
from nwaudio import (sound, white, bp, lp, hp, thump, env_ar, modal, click, layer, sparse, tt, n_, TAU, tv_filter,
                     reverb, colored, sine, tri, midi, note, voice)

U = 'SFX/UI'
Q = 'SFX/Spielfluss'


def ping(f, d=0.5, kind='bell'):
    if kind == 'bell':
        return modal([f, f * 2.0, f * 3.01, f * 4.2], [1, 0.35, 0.18, 0.08], [d, d * 0.6, d * 0.4, d * 0.25], d * 1.4)
    if kind == 'soft':
        return modal([f, f * 2.0], [1, 0.12], [d, d * 0.5], d * 1.4)
    if kind == 'box':   # Spieluhr
        return modal([f, f * 2.02, f * 5.3], [1, 0.4, 0.15], [d, d * 0.5, d * 0.2], d * 1.4)
    if kind == 'pluck':
        return tri(f, d) * np.exp(-tt(d) / (d * 0.3)) * 0.8 + sine(f * 2, d) * np.exp(-tt(d) / (d * 0.15)) * 0.2
    raise ValueError(kind)


def seq(names, gap, d=0.5, kind='bell', gain=1.0):
    parts = [(ping(midi(note(nm)), d, kind), gain, k * gap) for k, nm in enumerate(names)]
    return layer(*parts)


@sound(U, 'ui_klick', n=2, desc='Button gedrueckt (Zustand Gedrueckt): kurzer, dumpfer Holzklick', peak=-12)
def klick(r, i):
    return layer((click(0.03, 700, 3500, 0.006, r), 1.0), (thump(0.06, 260, 150, 0.015), 0.6))


@sound(U, 'ui_hover', n=2, desc='Hover: winziges, helles Ticken (Hover ist laut UI-Cheatsheet nur Farbwechsel - Ton sehr leise halten)', peak=-24)
def hover(r, i):
    return layer((click(0.02, 3000, 8000, 0.003, r), 0.6), (ping(1760 + 80 * i, 0.08, 'soft'), 0.3))


@sound(U, 'ui_bestaetigen', desc='Auswahl bestaetigen: zweistufig aufwaerts', peak=-12)
def bestaetigen(r, i):
    return seq(['A4', 'E5'], 0.07, 0.4, 'pluck')


@sound(U, 'ui_zurueck', desc='Zurueck/Abbrechen: zweistufig abwaerts', peak=-14)
def zurueck(r, i):
    return seq(['E5', 'A4'], 0.07, 0.35, 'pluck')


@sound(U, 'ui_fehler', desc='Aktion nicht moeglich: tiefes, kurzes Brummen', peak=-12)
def fehler(r, i):
    t = tt(0.22)
    return (nw.square(np.full(len(t), 110.0), duty=0.35) * 0.5 + sine(np.full(len(t), 82.0))) * np.sin(np.pi * t / 0.22) ** 0.6


@sound(U, 'panel_auf', desc='Panel / Inventar / Quest-Uebersicht (Q) oeffnen: weiches Aufschwingen', peak=-14)
def panel_auf(r, i):
    return layer((tv_filter(white(0.22, r), lambda u: 800 + 2500 * u, 1.2) * np.sin(np.pi * tt(0.22) / 0.22), 0.5), (ping(midi(note('E5')), 0.3, 'soft'), 0.4, 0.12))


@sound(U, 'panel_zu', desc='Panel schliessen (Esc): weiches Zuschwingen', peak=-14)
def panel_zu(r, i):
    return layer((tv_filter(white(0.2, r), lambda u: 3000 - 2200 * u, 1.2) * np.sin(np.pi * tt(0.2) / 0.2), 0.5), (ping(midi(note('A4')), 0.25, 'soft'), 0.4, 0.1))


@sound(U, 'dialog_oeffnen', desc='Dialogbox geht auf: leises Papier-/Holzgeraeusch mit tiefem Ton', peak=-14)
def dialog_auf(r, i):
    return layer((bp(white(0.15, r), 300, 3000) * env_ar(0.15, 0.02, 0.05), 0.5), (ping(midi(note('A3')), 0.35, 'soft'), 0.5))


@sound(U, 'dialog_weiter', n=3, desc='Weiter-Pfeil: ganz leises Ticken beim Weiterschalten einer Zeile', peak=-20)
def dialog_weiter(r, i):
    return layer((click(0.02, 1500, 5000, 0.004, r), 0.7), (ping(880 + 110 * i, 0.12, 'soft'), 0.4))


@sound(U, 'dialog_auswahl_hover', desc='Antwortoption unter der Maus: minimal', peak=-22)
def auswahl_hover(r, i):
    return ping(1319, 0.1, 'soft')


@sound(U, 'dialog_antwort_gewaehlt', desc='Antwort angeklickt: runder Holzton', peak=-14)
def antwort(r, i):
    return layer((thump(0.18, 380, 190, 0.05), 0.8), (ping(midi(note('E5')), 0.25, 'pluck'), 0.6))


@sound(U, 'schreibmaschine_tick', n=4, desc='Intro-Text (Step 2) / Erzaehlerzeilen: leiser Tastenanschlag', peak=-24)
def tick(r, i):
    return layer((click(0.03, 1800 + 150 * i, 6000, 0.005, r), 1.0), (thump(0.04, 600, 300, 0.01), 0.4))


@sound(U, 'schreibmaschine_klingel', desc='Schreibmaschine: Zeilenende-Glocke', peak=-14)
def type_bell(r, i):
    return reverb(modal([3520, 7040, 9800], [1, 0.4, 0.2], [0.9, 0.5, 0.3], 1.2), r, 0.4, 0.08, 9000)


# --------------------------------------------------------------------------- Spielfluss

@sound(Q, 'quest_neu', desc='Neue Quest im HUD (Main Quest "Investigate the log"): ruhig aufsteigende Terz-Quinte', peak=-10)
def quest_neu(r, i):
    return reverb(seq(['A4', 'C5', 'E5'], 0.16, 0.9, 'box'), r, 0.8, 0.2, 7000)


@sound(Q, 'quest_aktualisiert', desc='Quest-Fortschritt: zwei Toene', peak=-12)
def quest_update(r, i):
    return reverb(seq(['E5', 'G5'], 0.14, 0.6, 'box'), r, 0.6, 0.15, 7000)


@sound(Q, 'quest_erledigt', desc='Quest abgeschlossen: kleines Aufwaerts-Arpeggio mit Glockenklang', peak=-9)
def quest_done(r, i):
    return reverb(seq(['A4', 'C5', 'E5', 'A5'], 0.13, 1.3, 'bell'), r, 1.2, 0.25, 8000)


@sound(Q, 'hinweis_gefunden', desc='Fund / Wissen: geheimnisvoller Doppelton (z. B. "You found: a torn list of names")', peak=-10)
def fund(r, i):
    return reverb(layer((seq(['E5', 'B5'], 0.2, 1.4, 'bell'), 0.8), (sine(np.full(n_(2.0), 164.8), 2.0) * np.exp(-tt(2.0) / 0.8), 0.2)), r, 1.6, 0.3, 7000)


@sound(Q, 'tutorial_hinweis', desc='Tutorial-Einblendung (F - Interact / E - Talk): weiches Poppen', peak=-16)
def tutorial(r, i):
    return layer((thump(0.1, 600, 300, 0.02), 0.5), (ping(midi(note('C6')), 0.3, 'soft'), 0.6))


@sound(Q, 'vertrauen_plus', desc='Beziehung +1 (Rosé #c4636b): warme, runde Doppelnote', peak=-12)
def vertrauen_plus(r, i):
    return reverb(seq(['C5', 'G5'], 0.1, 0.8, 'box'), r, 0.7, 0.15, 6500)


@sound(Q, 'vertrauen_minus', desc='Beziehung -1: dumpfer, fallender Doppelton', peak=-12)
def vertrauen_minus(r, i):
    return layer((seq(['A3', 'E3'], 0.14, 0.7, 'soft'), 1.0), (thump(0.2, 100, 55, 0.05), 0.6))


@sound(Q, 'wissen_plus', desc='Wissen +1 (blau #6b7fb8): hoher, kuehler Ton', peak=-12)
def wissen_plus(r, i):
    return reverb(ping(midi(note('B5')), 1.0, 'bell'), r, 1.0, 0.2, 8000)


@sound(Q, 'talisman_zaehler', desc='Talismanzaehler im HUD aendert sich (#6fd3e6): kristalliner Ping', peak=-14)
def tal_zaehler(r, i):
    return reverb(ping(midi(note('E6')), 0.8, 'bell'), r, 0.8, 0.2, 9000)


@sound(Q, 'talisman_leer', desc='Keine Talismane mehr (Zaehler rot #8a1f3d): hohler, tiefer Schlag', peak=-10)
def tal_leer(r, i):
    return layer((thump(0.6, 140, 55, 0.15), 1.0), (ping(midi(note('E4')), 0.8, 'soft'), 0.4))


@sound(Q, 'wecklevel_stufe3', desc='Wecklevel 3 (orange): leise Unruhe, tiefer Puls', peak=-10)
def weck3(r, i):
    d = 2.4
    t = tt(d)
    y = sine(np.full(len(t), 55.0), d) * (0.5 + 0.5 * np.sin(TAU * 1.2 * t)) ** 2 * np.sin(np.pi * t / d)
    return reverb(layer((y, 1.0), (modal([196, 207.7], [0.4, 0.4], [1.8, 1.8], 2.4), 0.3)), r, 1.0, 0.2, 2500)


@sound(Q, 'wecklevel_stufe4', desc='Wecklevel 4 (rot #d64a6a): Tagesjagd beginnt, hartes Dissonanz-Signal', peak=-6)
def weck4(r, i):
    d = 3.0
    t = tt(d)
    chord = sum(sine(midi(note(nm)), d) for nm in ('A2', 'Bb2', 'E3', 'F3')) * np.exp(-t / 1.4)
    hit = thump(1.0, 80, 35, 0.2)
    return reverb(layer((chord, 0.3), (hit, 1.2), (click(0.05, 600, 5000, 0.01, r), 0.6)), r, 1.5, 0.25, 3500)


@sound(Q, 'sanity_warnung', desc='Sanity unter 40 % (Schlafsperre): duenner, hoher Ton mit Zittern', peak=-14)
def sanity(r, i):
    d = 2.2
    t = tt(d)
    y = (sine(3520.0 * (1 + 0.004 * np.sin(TAU * 7 * t)), d) + 0.5 * sine(3730.0, d)) * np.sin(np.pi * t / d) ** 2
    return reverb(y, r, 1.2, 0.3, 8000)


@sound(Q, 'lagebericht_zeile', n=3, desc='Lagebericht: jede Zeile erscheint (0,3 s): weiches Ticken', peak=-18)
def lage_zeile(r, i):
    return layer((click(0.02, 1200, 4500, 0.005, r), 0.6), (ping(midi(note(('A4', 'C5', 'E5')[i])), 0.2, 'soft'), 0.5))


@sound(Q, 'lagebericht_verlust', desc='Lagebericht nennt einen Toten (Warnsymbol, #d64a6a): tiefer Glockenschlag, kein Jingle', peak=-8)
def lage_verlust(r, i):
    f = midi(note('A2'))
    return reverb(modal([f, f * 2.4, f * 3.7, f * 5.1], [1, 0.5, 0.3, 0.2], [3.0, 2.0, 1.4, 0.9], 3.2), r, 1.6, 0.3, 3500)


@sound(Q, 'lagebericht_gewinn', desc='Lagebericht: Talisman/Wissen gewonnen: kleiner heller Doppelklang', peak=-11)
def lage_gewinn(r, i):
    return reverb(seq(['G5', 'D6'], 0.1, 1.0, 'bell'), r, 1.0, 0.2, 8000)


@sound(Q, 'tag_beginnt', desc='Morgen: neuer Tag (Lagebericht erscheint). Sonnenaufgang-Arpeggio, Vogel-Pizzicato', peak=-9)
def tag_beginnt(r, i):
    return reverb(layer((seq(['A3', 'E4', 'A4', 'C5', 'E5'], 0.28, 1.6, 'box'), 1.0), (seq(['A2'], 0, 3.0, 'soft'), 0.4)), r, 1.8, 0.3, 6500)


@sound(Q, 'phase_tag', desc='Uebergang zur Tagphase: offen, ruhig, zwei Toene', peak=-12)
def phase_tag(r, i):
    return reverb(seq(['D5', 'A5'], 0.3, 1.2, 'box'), r, 1.4, 0.3, 7000)


@sound(Q, 'phase_daemmerung', desc='Daemmerung beginnt (Sheriff laeutet gleich): absteigende Quarte, Glocken-Hauch', peak=-9)
def phase_daem(r, i):
    return reverb(layer((seq(['E5', 'B4', 'E4'], 0.45, 2.0, 'bell'), 0.8), (sine(np.full(n_(4.0), 110.0), 4.0) * np.sin(np.pi * tt(4.0) / 4.0), 0.3)), r, 2.2, 0.35, 5000)


@sound(Q, 'phase_nacht', desc='Nacht faellt: tiefer Drone schwillt an, hohler Schlag, Stille danach', peak=-6)
def phase_nacht(r, i):
    d = 5.0
    t = tt(d)
    dr = (sine(np.full(len(t), 55.0), d) + 0.7 * sine(np.full(len(t), 58.3), d) + 0.4 * sine(np.full(len(t), 82.4), d)) * np.sin(np.pi * np.clip(t / d, 0, 1)) ** 1.5
    return reverb(layer((dr, 0.8), (thump(1.2, 70, 32, 0.3), 1.3, 1.6)), r, 2.0, 0.3, 2500)


@sound(Q, 'nacht_ueberlebt', desc='Morgen nach einer Nacht ohne Verluste: erleichternde Aufloesung (Moll -> Dur)', peak=-10)
def nacht_ueberlebt(r, i):
    return reverb(layer((seq(['A3', 'C4', 'E4'], 0.01, 3.0, 'soft'), 0.5), (seq(['A3', 'C#4', 'E4', 'A4'], 0.01, 3.5, 'soft'), 0.6, 1.4)), r, 2.0, 0.3, 6000)


@sound(Q, 'speichern', desc='Spielstand gespeichert: kurzer ruhiger Doppelton', peak=-16)
def speichern(r, i):
    return reverb(seq(['A4', 'A5'], 0.12, 0.5, 'soft'), r, 0.5, 0.1, 6000)


@sound(Q, 'titel_dusk_bell', desc='Titel "DUSK BELL" (#ffd27a) nach dem Intro-Text: ferne Glocke, tiefer Schlag, langer Hall (ca. 8 s)', peak=-5)
def titel(r, i):
    d = 8.0
    f = 146.8
    bell = modal([f * 0.5, f, f * 1.2, f * 1.5, f * 2.0, f * 2.5, f * 3.0, f * 4.2], [0.6, 1, 0.7, 0.6, 0.5, 0.35, 0.25, 0.15],
                 [9, 7, 5, 4.5, 3.5, 3, 2.2, 1.5], d)
    shim = sum(sine(midi(note(nm)), d) for nm in ('E5', 'B5', 'E6')) * np.minimum(1, tt(d) / 2.0) * np.exp(-tt(d) / 3.0) * 0.1
    return reverb(layer((bell, 0.9), (thump(1.5, 80, 34, 0.35), 1.2), (shim, 1.0, 0.3), (click(0.03, 800, 5000, 0.006, r), 0.5)), r, 3.0, 0.35, 4500)


@sound(Q, 'uebergang_whoosh', n=2, desc='Szenenuebergang (Ausblenden ueber Schwarz 0,5 s): leiser Luftzug', peak=-18)
def uebergang(r, i):
    return tv_filter(white(0.8, r), lambda u: 600 + 1800 * (1 - u) if i else 600 + 1800 * u, 1.0) * np.sin(np.pi * tt(0.8) / 0.8) ** 1.5
