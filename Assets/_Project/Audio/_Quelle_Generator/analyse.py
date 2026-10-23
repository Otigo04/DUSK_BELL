"""Misst, welche Klaenge 'synthetisch/roboterhaft' wirken koennten (ersetzt kein Hoeren!).

  python3 analyse.py [Muster]      Tabelle aller Sounds, sortiert nach Verdacht

Kennzahlen (nur Hinweise):
  tonal   Spitzenwert im Langzeitspektrum gegenueber dem Median in dB. Hoch bei Geraeuschen = Piepston/Brummen.
  mod     Schwankungstiefe der Lautstaerke (Std/Mittel der 20-ms-Huellkurve). Sehr niedrig = statisches Rauschen, sehr hoch = Geknatter.
  rhythm  staerkste Selbstaehnlichkeit der Huellkurve bei Lag 0.15..3 s. Hoch = mechanisches Ticken statt Zufall.
  cv      Variationskoeffizient der Abstaende zwischen Einzelereignissen. Echtes Zufallsgeschehen ~1, Maschine <0.5.
  flat    spektrale Flachheit (0 tonal .. 1 weisses Rauschen) im Mittel.
"""
import glob
import os
import re
import sys
import wave

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

# Klaenge, bei denen Tonhaltigkeit gewollt ist (Glocken, Musik, UI, Stimmen ...) -> nur Geraeusch-Metriken werten
TONAL_OK = re.compile(r'(glocke|mus_|stg_|ui_|quest|vertrauen|wissen|talisman|hinweis|tag_|phase|speichern|titel|lagebericht|schreibmaschine_klingel|'
                      r'tuerglocke|windspiel|kuckuck|standuhr|muenz|glas_|kasse|schluessel|blip_|hupe|nacht_ueberlebt|sanity|wecklevel|tutorial|panel|dialog)')


def load(path):
    w = wave.open(path)
    sr = w.getframerate()
    x = np.frombuffer(w.readframes(w.getnframes()), dtype='<i2').astype(float) / 32768.0
    return x, sr


def metrics(x, sr):
    n = len(x)
    nfft = 2048
    if n < nfft * 2:
        x = np.pad(x, (0, nfft * 2 - n))
        n = len(x)
    hop = nfft // 2
    win = np.hanning(nfft)
    frames = [x[i:i + nfft] * win for i in range(0, max(1, n - nfft), hop)]
    if not frames:
        frames = [np.pad(x, (0, nfft - n)) * win]
    S = np.abs(np.fft.rfft(np.array(frames), axis=1)) ** 2 + 1e-14
    f = np.fft.rfftfreq(nfft, 1.0 / sr)
    band = (f > 150) & (f < min(9000, sr / 2 - 100))
    mean = S[:, band].mean(axis=0)
    # lokaler Median glaettet das Spektrum: Spitzen darueber sind Toene
    k = 21
    pad = np.pad(mean, (k // 2, k // 2), mode='edge')
    loc = np.array([np.median(pad[i:i + k]) for i in range(len(mean))])
    tonal = 10 * np.log10(np.max(mean / loc))
    flat = float(np.mean(np.exp(np.mean(np.log(S[:, band]), axis=1)) / np.mean(S[:, band], axis=1)))
    # Huellkurve (20 ms)
    h = max(1, int(0.02 * sr))
    m = n // h
    env = np.sqrt((x[:m * h].reshape(m, h) ** 2).mean(axis=1)) + 1e-9
    mod = float(np.std(env) / np.mean(env))
    # Rhythmus
    e = env - env.mean()
    ac = np.correlate(e, e, 'full')[len(e) - 1:]
    ac = ac / (ac[0] + 1e-12)
    lo, hi = int(0.15 / 0.02), min(len(ac) - 1, int(3.0 / 0.02))
    rhythm = float(ac[lo:hi].max()) if hi > lo else 0.0
    # Einzelereignisse
    thr = np.mean(env) + 1.5 * np.std(env)
    peaks = [i for i in range(1, len(env) - 1) if env[i] > thr and env[i] >= env[i - 1] and env[i] > env[i + 1]]
    iv = np.diff(peaks) * 0.02
    cv = float(np.std(iv) / np.mean(iv)) if len(iv) > 4 else float('nan')
    return tonal, mod, rhythm, cv, flat, len(peaks)


def main():
    pat = re.compile(sys.argv[1], re.I) if len(sys.argv) > 1 else None
    rows = []
    for p in sorted(glob.glob(ROOT + '/**/*.wav', recursive=True)):
        name = os.path.basename(p)[:-4]
        if pat and not pat.search(name):
            continue
        x, sr = load(p)
        t, mod, rh, cv, fl, npk = metrics(x, sr)
        tonal_ok = bool(TONAL_OK.search(name))
        score = 0.0
        if not tonal_ok:
            score += max(0, t - 14) * 0.5
        if 'Ambience' in p or '_loop' in name:
            score += max(0, rh - 0.35) * 8
            if cv == cv and npk > 8:
                score += max(0, 0.6 - cv) * 6
            score += max(0, 0.12 - mod) * 20
        rows.append((score, name, t, mod, rh, cv, fl, len(x) / sr))
    rows.sort(reverse=True)
    print('%-34s %6s %6s %6s %6s %6s %6s  %s' % ('name', 'tonal', 'mod', 'rhythm', 'cv', 'flat', 'sec', 'verdacht'))
    for sc, n, t, mod, rh, cv, fl, sec in rows:
        print('%-34s %6.1f %6.2f %6.2f %6.2f %6.2f %6.1f  %.1f' % (n, t, mod, rh, cv, fl, sec, sc))


if __name__ == '__main__':
    main()
