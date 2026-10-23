"""Sprech-Blips pro Figur (Opening Sequence: "Keine Stimme: Die NPCs mumbeln, der Text erscheint in der Dialogbox").
Jede Figur hat ein eigenes Stimmprofil, damit man sie am Klang erkennt und Maenner wie Maenner, Frauen wie Frauen klingen:

* Geschlecht: Grundton (Mann ~80-145 Hz, Frau ~170-260 Hz) UND Formanten (Frauen: kuerzerer Stimmtrakt -> F1 +15 %, F2/F3 +15-25 %,
  Werte nach Peterson & Barney 1952). Beides zusammen macht den Unterschied, nicht nur die Tonhoehe.
* Stimmqualitaet pro Figur: Knarren (vocal fry), Rauheit (Jitter/Shimmer), Hauch, Nasalitaet, metallische Schaerfe, Zittern.
* Sprechweise: Silbenlaenge, Tonverlauf (fallend/steigend/flach), Konsonanten-Ansaetze (Verschluss, Zischen, Nasal), Stottern.
Dialogue Bible: Bulut kurz, ruhig, muede; Ilhan wenig Worte, rau; Veronica warm; Elenora hoeflich und eisig; Mara herzlich, frueh auf;
David geduldig; Can zerstreut, zoegernd. Protagonist und Erzaehler haben keine Stimme. Monster-Klone sprechen wie das Original."""
import numpy as np

import nwaudio as nw
from nwaudio import sound, voice, tt, n_, lp, hp, bp, white, layer, reverb, resonate

V = 'SFX/Stimmen'

# Vokal -> (F1, F2, F3) in Hz fuer erwachsene Maenner / Frauen
FORM = {
    'm': {'a': (730, 1090, 2440), 'e': (530, 1840, 2480), 'i': (270, 2290, 3010), 'o': (570, 840, 2410),
          'u': (300, 870, 2240), 'ae': (660, 1720, 2410)},
    'f': {'a': (850, 1220, 2810), 'e': (610, 2330, 2990), 'i': (310, 2790, 3310), 'o': (590, 920, 2710),
          'u': (370, 950, 2670), 'ae': (860, 2050, 2850)},
    'k': {'a': (1000, 1450, 3300), 'e': (700, 2900, 3600), 'i': (400, 3300, 3900), 'o': (700, 1200, 3200),  # Kind ~ +30 %
          'u': (450, 1250, 3100), 'ae': (1000, 2500, 3400)},
}

# who: dict(sex, f0, tract, vowels, dur, contour, wander, breath, jit, shim, fry, nasal, metal, warm, onset, tremor, desc)
CAST = {
    'bulut': dict(sex='m', f0=104, tract=0.97, vowels=['o', 'a', 'u', 'e'], dur=(0.09, 0.115), contour=-0.07, wander=0.012, breath=0.04,
                  jit=0.008, shim=0.07, fry=0.35, onset=('nasal', 0.35), desc='Sheriff Bulut: tief, ruhig, muede, Stimme knarrt am Satzende'),
    'ilhan': dict(sex='m', f0=84, tract=0.92, vowels=['a', 'o', 'ae'], dur=(0.06, 0.08), contour=-0.03, wander=0.01, breath=0.1,
                  jit=0.03, shim=0.2, fry=0.6, onset=('burst', 0.6), desc='Bartender Ilhan: sehr tief, rau, kurz angebunden, harte Ansaetze'),
    'david': dict(sex='m', f0=128, tract=1.0, vowels=['e', 'o', 'i', 'a'], dur=(0.1, 0.13), contour=0.04, wander=0.014, breath=0.13,
                  jit=0.01, shim=0.09, nasal=0.45, onset=('nasal', 0.5), desc='Pastor David: weich, langsam, leicht nasal, freundlich steigend'),
    'can': dict(sex='m', f0=122, tract=1.04, vowels=['e', 'i', 'ae', 'a'], dur=(0.05, 0.1), contour=0.08, wander=0.03, breath=0.09,
                jit=0.035, shim=0.15, onset=('burst', 0.3), desc='Can: hoeher, zittrig, zoegernd, Aussagen klingen wie Fragen, stottert'),
    'dorfbewohner_m': dict(sex='m', f0=116, tract=0.98, vowels=['a', 'e', 'o', 'u'], dur=(0.07, 0.1), contour=-0.02, wander=0.015, breath=0.07,
                           jit=0.015, shim=0.1, fry=0.1, onset=('burst', 0.4), desc='Generischer Dorfbewohner, mittleres Alter'),
    'dorfbewohner_m_alt': dict(sex='m', f0=96, tract=0.95, vowels=['o', 'u', 'a'], dur=(0.095, 0.13), contour=-0.05, wander=0.02, breath=0.14,
                               jit=0.025, shim=0.16, fry=0.3, tremor=0.025, onset=('nasal', 0.4), desc='Alter Mann: tief, bruechig, zittrig, langsam'),
    'veronica': dict(sex='f', f0=176, tract=1.0, vowels=['a', 'o', 'e', 'u'], dur=(0.095, 0.125), contour=-0.04, wander=0.018, breath=0.1,
                     jit=0.009, shim=0.07, warm=0.55, onset=('nasal', 0.3), desc='Doctor Veronica: aeltere Frau, warm, ruhig, weich'),
    'mara': dict(sex='f', f0=232, tract=1.04, vowels=['a', 'i', 'e', 'ae'], dur=(0.06, 0.08), contour=0.09, wander=0.03, breath=0.07,
                 jit=0.014, shim=0.07, onset=('fric', 0.35), desc='Baker Mara: jung, hell, herzlich, schnell, Satzenden gehen hoch'),
    'elenora': dict(sex='f', f0=205, tract=1.0, vowels=['i', 'e', 'ae'], dur=(0.055, 0.075), contour=0.0, wander=0.006, breath=0.02,
                    jit=0.004, shim=0.03, metal=0.45, onset=('burst', 0.7), desc='Madame Elenora: gleichmaessig, praezise, scharf, eisig, kein Hauch'),
    'dorfbewohner_w': dict(sex='f', f0=190, tract=1.0, vowels=['a', 'e', 'o', 'i'], dur=(0.07, 0.1), contour=0.01, wander=0.025, breath=0.08,
                           jit=0.014, shim=0.09, onset=('nasal', 0.3), desc='Generische Dorfbewohnerin, mittleres Alter'),
    'dorfbewohner_w_alt': dict(sex='f', f0=160, tract=0.98, vowels=['a', 'o', 'u', 'e'], dur=(0.09, 0.12), contour=-0.03, wander=0.025, breath=0.12,
                               jit=0.022, shim=0.14, tremor=0.022, onset=('nasal', 0.35), desc='Alte Frau: bruechig, zittrig, langsam'),
    'kind': dict(sex='k', f0=300, tract=1.0, vowels=['a', 'i', 'e', 'o'], dur=(0.05, 0.075), contour=0.1, wander=0.05, breath=0.05,
                 jit=0.02, shim=0.1, onset=('fric', 0.3), desc='Kind / Junge (Beerdigung): sehr hell, kurz, steigend'),
}

# Vokal-Reihenfolge pro Silbennummer (Varianten _01.._06): jede Figur nutzt ihre Vorlieben in anderer Reihenfolge,
# Varianten tragen unterschiedliche Konturen, damit gemischte Blips wie Sprechen wirken
CONTOUR_MOD = [0.0, -0.5, 1.8, 0.4, -1.2, 0.9]


def onset_noise(kind, r, sex):
    """Konsonanten-Ansatz vor dem Vokal."""
    if kind == 'burst':                       # p / t / k: Verschlusslaut
        d = r.uniform(0.012, 0.022)
        lo = r.uniform(900, 2500)
        x = bp(white(d, r), lo, lo * 2.5, 1) * np.exp(-tt(d) / (d * 0.35)) * 1.6
        return x
    if kind == 'fric':                        # s / f / sch: Reibelaut
        d = r.uniform(0.03, 0.055)
        lo = r.uniform(3500, 5500) * (1.15 if sex != 'm' else 1.0)
        return hp(white(d, r), lo, 2) * np.sin(np.pi * tt(d) / d) ** 0.7 * 0.5
    if kind == 'nasal':                       # m / n: tiefes Brummen mit Formant bei ~ 250 Hz
        d = r.uniform(0.03, 0.05)
        f = r.uniform(110, 140) if sex == 'm' else r.uniform(190, 230)
        y = voice(f, d, [(250, 8, 1.0), (1000, 5, 0.1)], r, breath=0.02, jit=0.01)
        return y * np.sin(np.pi * tt(d) / d) ** 0.8 * 0.5
    return np.zeros(1)


def syllable(who, k, r):
    p = CAST[who]
    sex = p['sex']
    vow = p['vowels'][(k + int(r.integers(0, len(p['vowels'])))) % len(p['vowels'])]
    F = np.array(FORM[sex][vow], dtype=float) * p['tract']
    d = r.uniform(*p['dur']) * (0.7 if k == 3 else 1.0)
    t = tt(d)
    u = t / d
    contour = p['contour'] + 0.05 * CONTOUR_MOD[k % 6] * (1 if p['contour'] >= 0 else -1)
    f0 = p['f0'] * r.uniform(0.94, 1.07)
    f = f0 * (1.0 + contour * u + 0.035 * np.sin(np.pi * u))
    if p.get('tremor'):
        f = f * (1.0 + p['tremor'] * np.sin(nw.TAU * 5.3 * t + r.uniform(0, 6.28)))
    y = voice(f, d, [(F[0], 8, 1.0), (F[1], 9, 0.5 if sex == 'm' else 0.42), (F[2], 10, 0.2)], r,
              breath=p['breath'], jit=p['jit'], shimmer=p['shim'], wander=p['wander'])
    if p.get('fry'):                          # Knarren: jede zweite Stimmritzen-Periode schwaecher
        half = np.sign(np.sin(nw.TAU * np.cumsum(f * 0.5) / nw.SR))
        y = y * (1.0 - p['fry'] * (0.5 + 0.5 * half) * np.clip(1.4 - u * 0.6, 0, 1))
    if p.get('nasal'):
        y = y + p['nasal'] * (resonate(y, 270, 6) * 0.6 + resonate(y, 2400, 5) * 0.3)
    if p.get('metal'):
        y = y + p['metal'] * resonate(y, 3300, 3)
    if p.get('warm'):
        y = lp(y, 3300 - 800 * p['warm'], 1) * (1.0 + 0.2 * p['warm'])
    env = np.sin(np.pi * np.clip(u, 0, 1)) ** 0.7 * np.clip(u * 12, 0, 1)
    y = y * env
    on, prob = p['onset']
    if r.random() < prob:
        c = onset_noise(on, r, sex)
        gap = np.zeros(int(0.004 * nw.SR))
        y = np.concatenate([c, gap, y])
    return y


def blip(who, k, r):
    """Eine Sprech-Silbe fuer die Figur 'who' (k = Variantennummer 0..5)."""
    if who == 'can' and k % 6 == 5:           # Stottern: zwei kurze Ansaetze hintereinander
        a, b = syllable('can', 0, r), syllable('can', 2, r)
        return np.concatenate([a[:int(len(a) * 0.55)], np.zeros(int(0.045 * nw.SR)), b])
    return syllable(who, k, r)


def _register(who):
    desc = CAST[who]['desc']

    @sound(V, 'blip_' + who, n=6, sr=22050, desc='Sprech-Silbe: ' + desc, peak=-12)
    def _fn(r, i, who=who):
        return blip(who, i, r)
    return _fn


for _who in CAST:
    _register(_who)


@sound(V, 'menge_murmeln_kurz', n=3, sr=22050, desc='Dorfplatz-Murmeln (Beerdigung, Bar): kurzer Satz aus Silben verschiedener Stimmen, mit Hall', peak=-16)
def murmel_kurz(r, i):
    out = np.zeros(n_(2.6))
    t = 0.1
    mix = ['dorfbewohner_m', 'dorfbewohner_w', 'dorfbewohner_m_alt', 'dorfbewohner_w_alt', 'dorfbewohner_m', 'dorfbewohner_w']
    spk = mix[int(r.integers(0, len(mix)))]
    while t < 2.2:
        if r.random() < 0.15:                 # zweite Stimme faellt kurz ein
            spk = mix[int(r.integers(0, len(mix)))]
        b = blip(spk, int(r.integers(0, 6)), r) * r.uniform(0.5, 1.0)
        a = int(t * nw.SR)
        out[a:a + len(b)] += b[:len(out) - a]
        t += r.uniform(0.1, 0.2)
    return reverb(lp(out, 2000, 2), r, 0.6, 0.3, 3000)
