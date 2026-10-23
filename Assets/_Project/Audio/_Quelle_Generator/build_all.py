"""Rendert alle registrierten Sounds nach Audio/SFX | Ambience | Music (WAV, mono, 16 bit).

  python3 build_all.py                 alles
  python3 build_all.py step door       nur Sounds, deren Name/Pfad eines der Muster (Regex) enthaelt
  python3 build_all.py --list          nur auflisten
  python3 build_all.py --sheet bell    zusaetzlich Vorschaubild (Wellenform + Spektrogramm) nach _Vorschau/
Schreibt Audio/_Liste.txt (Dauer, Pegel, Loop-Naht, Beschreibung) und warnt bei Problemen.
"""
import importlib
import os
import re
import sys
import time

import numpy as np

import nwaudio as nw

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.dirname(HERE)  # .../Audio

MODULES = ['sfx_steps', 'sfx_doors', 'sfx_monster', 'sfx_combat', 'sfx_items', 'sfx_ui', 'sfx_world', 'voices',
           'amb', 'music']


def load_modules():
    for m in MODULES:
        if os.path.exists(os.path.join(HERE, m + '.py')):
            importlib.import_module(m)


def select(pats):
    items = nw.REGISTRY
    if not pats:
        return items
    rx = [re.compile(p, re.I) for p in pats]
    return [s for s in items if any(r.search(s['name']) or r.search(s['path']) for r in rx)]


def render(s, i):
    nw.SR = s['sr']
    name = s['name'] if s['n'] == 1 else '%s_%02d' % (s['name'], i + 1)
    r = nw.rng_for(s['name'], i)
    x = np.asarray(s['fn'](r, i), dtype=float)
    x = np.nan_to_num(x)
    x = nw.dc(x)
    if s['loop']:
        x = nw.hp(x, 32, 2, circ=True)  # Sub-Drift raus, spart Headroom (Loop-sicher, zirkulaer)
    # Transienten zaehmen, damit der Koerper des Klangs nicht im Pegel untergeht (punktweise, also loop-sicher)
    lim = (3.4 if s['loop'] else 2.6) * float(np.sqrt(np.mean(x ** 2))) + 1e-9
    x = np.tanh(x / lim) * lim
    x = nw.normalize(x, s['peak'])
    if s['loop']:
        k = min(96, len(x) // 8)  # Ende laeuft in 4 ms auf den Anfangswert zu: keine Klicks an der Loop-Naht
        w = np.linspace(0.0, 1.0, k)
        x[-k:] = x[-k:] * (1.0 - w) + x[0] * w
    if not s['loop']:
        x = nw.fade(x, 0.002, 0.012)
    return name, x


def sheet(items):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    os.makedirs(os.path.join(OUT, '_Vorschau'), exist_ok=True)
    rows = len(items)
    fig, ax = plt.subplots(rows, 2, figsize=(12, 1.6 * rows), squeeze=False)
    for k, (name, x, sr) in enumerate(items):
        t = np.arange(len(x)) / sr
        ax[k][0].plot(t, x, lw=0.4, color='#3a4a7a')
        ax[k][0].set_ylim(-1, 1)
        ax[k][0].set_ylabel(name, rotation=0, ha='right', fontsize=7)
        ax[k][0].tick_params(labelsize=6)
        ax[k][1].specgram(x, NFFT=1024, Fs=sr, noverlap=768, cmap='magma', vmin=-120, vmax=-20)
        ax[k][1].set_ylim(0, min(sr / 2, 12000))
        ax[k][1].tick_params(labelsize=6)
    fig.tight_layout()
    p = os.path.join(OUT, '_Vorschau', 'sheet_%d.png' % int(time.time()))
    fig.savefig(p, dpi=70)
    return p


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    flags = [a for a in sys.argv[1:] if a.startswith('--')]
    load_modules()
    sel = select(args)
    if '--list' in flags:
        for s in sel:
            print('%-22s %-34s n=%d sr=%d%s' % (s['path'], s['name'], s['n'], s['sr'], ' loop' if s['loop'] else ''))
        print(len(sel), 'Eintraege,', sum(s['n'] for s in sel), 'Dateien')
        return
    rows, shots, warns, t0 = [], [], [], time.time()
    for s in sel:
        d = os.path.join(OUT, s['path'])
        os.makedirs(d, exist_ok=True)
        for i in range(s['n']):
            name, x = render(s, i)
            nw.write_wav(os.path.join(d, name + '.wav'), x, s['sr'])
            sec = len(x) / s['sr']
            seam = nw.seam_ratio(x) if s['loop'] else 0.0
            rows.append((s['path'], name, sec, s['sr'], nw.rms_db(x), s['loop'], seam, s['desc']))
            if s['loop'] and seam > 4.0:
                warns.append('Loop-Naht %s: %.1f' % (name, seam))
            if nw.rms_db(x) < -60:
                warns.append('fast stumm: ' + name)
            if sec > 90:
                warns.append('lang: %s %.0fs' % (name, sec))
            if '--sheet' in flags and i == 0:
                shots.append((name, x, s['sr']))
    if '--sheet' in flags and shots:
        print('Vorschau:', sheet(shots[:12]))
    if not args:
        rows.sort()
        total = 0
        with open(os.path.join(OUT, '_Liste.txt'), 'w', encoding='utf-8') as f:
            f.write('Dusk Bell - Audio-Liste (automatisch von build_all.py erzeugt)\n')
            f.write('Pfad | Datei | Sekunden | Hz | RMS dB | Loop | Naht | Beschreibung\n\n')
            for p, n, sec, sr, rms, loop, seam, desc in rows:
                f.write('%s | %s.wav | %.2f | %d | %.1f | %s | %.1f | %s\n' %
                        (p, n, sec, sr, rms, 'LOOP' if loop else '-', seam, desc))
                total += sec * sr * 2
            f.write('\n%d Dateien, %.1f MB\n' % (len(rows), total / 1e6))
    mb = sum(r[2] * r[3] * 2 for r in rows) / 1e6
    print('%d Dateien, %.1f MB, %.1fs' % (len(rows), mb, time.time() - t0))
    for w in warns:
        print('WARNUNG', w)


if __name__ == '__main__':
    main()
