"""nwaudio - Synthese-Bibliothek fuer Dusk Bell (nur numpy + Standardbibliothek).

Alle Klaenge entstehen per Code, deterministisch (Seed aus Name + Variante). Keine Samples, keine Fremdrechte.
Jeder Sound ist eine Funktion fn(r, i) -> mono float array (r = numpy Generator, i = Variantennummer),
registriert mit @sound(...). build_all.py rendert alles nach Audio/SFX, Audio/Ambience, Audio/Music.

Das Modul-Global SR ist die aktuelle Abtastrate; build_all setzt sie pro Sound (nw.SR = ...), alle Helfer lesen
sie zur Laufzeit. Loops werden zirkulaer gefiltert (FFT), damit die Naht sauber bleibt.
"""
import math
import os
import re
import wave
import zlib

import numpy as np

SR = 44100
REGISTRY = []
TAU = 2.0 * math.pi


# --------------------------------------------------------------------------- Registrierung

def sound(path, name, n=1, sr=44100, loop=False, desc='', peak=-4.0):
    """Dekorator. path z. B. 'SFX/Schritte'; n = Anzahl Varianten (name_01 ...); peak in dBFS."""
    def deco(fn):
        REGISTRY.append(dict(path=path, name=name, n=n, sr=sr, loop=loop, desc=desc, peak=peak, fn=fn))
        return fn
    return deco


def rng_for(name, i=0):
    return np.random.default_rng(zlib.crc32(('%s:%d' % (name, i)).encode()))


# --------------------------------------------------------------------------- Zeit und Rauschen

def n_(sec):
    return max(1, int(round(sec * SR)))


def tt(sec):
    return np.arange(n_(sec)) / SR


def silence(sec):
    return np.zeros(n_(sec))


def white(sec, r):
    return r.standard_normal(n_(sec))


def colored(sec, r, power=1.0):
    """Rauschen mit 1/f^power Leistungsabfall: 0 weiss, 1 rosa, 2 braun."""
    x = r.standard_normal(n_(sec))
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1.0 / SR)
    f[0] = f[1] if len(f) > 1 else 1.0
    X *= f ** (-power / 2.0)
    y = np.fft.irfft(X, len(x))
    return y / (np.std(y) + 1e-12)


# --------------------------------------------------------------------------- Filter (FFT, nullphasig)

def _shape(x, hfn, circ=False):
    n = len(x)
    pad = 0 if circ else min(n, SR // 4)
    if pad:
        x = np.concatenate([x, np.zeros(pad)])
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1.0 / SR)
    y = np.fft.irfft(X * hfn(f), len(x))
    return y[:n]


def lp(x, fc, order=2, circ=False):
    return _shape(x, lambda f: 1.0 / np.sqrt(1.0 + (f / fc) ** (2 * order)), circ)


def hp(x, fc, order=2, circ=False):
    return _shape(x, lambda f: 1.0 / np.sqrt(1.0 + (fc / np.maximum(f, 1e-9)) ** (2 * order)), circ)


def bp(x, lo, hi, order=2, circ=False):
    return hp(lp(x, hi, order, circ), lo, order, circ)


def resonate(x, fc, q=4.0, circ=False):
    """Formant-/Resonanzfilter (Magnitude-Peak bei fc), Verstaerkung am Peak = 1."""
    return _shape(x, lambda f: 1.0 / np.sqrt(1.0 + (q * (f / fc - fc / np.maximum(f, 1e-9))) ** 2), circ)


def tv_filter(x, fcs, q=2.0, kind='bp', block=1024, circ=False):
    """Zeitvariables Filter per STFT. fcs: Array (len(x)) oder Funktion u in 0..1 -> Hz. kind bp | lp | hp.
    circ=True: Signal wird zyklisch fortgesetzt (Loop-Naht bleibt sauber)."""
    n = len(x)
    hop = block // 2
    win = 0.5 - 0.5 * np.cos(TAU * np.arange(block) / block)
    if circ and n > block:
        xp = np.concatenate([x[-hop:], x, x[:block]])
    else:
        xp = np.concatenate([np.zeros(hop), x, np.zeros(block)])
    out = np.zeros(len(xp))
    f = np.fft.rfftfreq(block, 1.0 / SR)
    fsafe = np.maximum(f, 1e-9)
    for s in range(0, n + hop, hop):
        u = min(s, n - 1) / max(1, n - 1)
        fc = float(fcs(u)) if callable(fcs) else float(fcs[min(s, n - 1)])
        fc = max(20.0, fc)
        if kind == 'bp':
            h = 1.0 / np.sqrt(1.0 + (q * (f / fc - fc / fsafe)) ** 2)
        elif kind == 'lp':
            h = 1.0 / np.sqrt(1.0 + (f / fc) ** (2 * 2))
        else:
            h = 1.0 / np.sqrt(1.0 + (fc / fsafe) ** (2 * 2))
        seg = xp[s:s + block]
        if len(seg) < block:
            seg = np.concatenate([seg, np.zeros(block - len(seg))])
        out[s:s + block] += np.fft.irfft(np.fft.rfft(seg * win) * h, block)
    return out[hop:hop + n]


def dc(x):
    return x - np.mean(x)


# --------------------------------------------------------------------------- Huellkurven

def curve(sec, pts, power=1.0):
    """Stueckweise lineare Kurve durch [(t, v), ...] (t in Sekunden); power biegt jedes Segment."""
    t = tt(sec)
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    y = np.interp(t, xs, ys)
    return y


def expdecay(sec, tau):
    return np.exp(-tt(sec) / max(tau, 1e-6))


def env_ar(sec, a, tau):
    """Schneller Anstieg (a) und exponentielles Abklingen (tau) - Grundform fast aller Geraeusche."""
    t = tt(sec)
    return (1.0 - np.exp(-t / max(a, 1e-6))) * np.exp(-t / max(tau, 1e-6))


def layer(*parts):
    """Addiert (signal, gain) oder (signal, gain, start_sekunden); Laenge = laengster Teil."""
    items = []
    for p in parts:
        sig, g = p[0], p[1]
        st = int(round(p[2] * SR)) if len(p) > 2 else 0
        items.append((sig, g, st))
    n = max(len(s) + st for s, _, st in items)
    out = np.zeros(n)
    for s, g, st in items:
        out[st:st + len(s)] += g * s
    return out


def sparse(sec, density, r, lo=0.3, hi=1.0):
    """Zufaellige Einzelimpulse (Knistern, Kies)."""
    n = n_(sec)
    x = np.zeros(n)
    k = r.poisson(density * sec)
    idx = r.integers(0, n, k)
    x[idx] = r.uniform(lo, hi, k) * r.choice([-1.0, 1.0], k)
    return x


def adsr(sec, a=0.01, d=0.1, s=0.7, r=0.2):
    n = n_(sec)
    ia, idc, ir = n_(a), n_(d), n_(r)
    e = np.ones(n) * s
    ia = min(ia, n)
    e[:ia] = np.linspace(0, 1, ia, endpoint=False)
    j = min(n, ia + idc)
    e[ia:j] = np.linspace(1, s, j - ia, endpoint=False) if j > ia else e[ia:j]
    if ir > 0:
        k = max(0, n - ir)
        e[k:] *= np.linspace(1, 0, n - k)
    return e


def fade(x, fin=0.003, fout=0.006):
    x = x.copy()
    a, b = min(n_(fin), len(x)), min(n_(fout), len(x))
    if a > 1:
        x[:a] *= np.linspace(0, 1, a)
    if b > 1:
        x[-b:] *= np.linspace(1, 0, b)
    return x


def pulse_env(sec, centers, widths, heights=None, r=None):
    """Summe glatter Glockenimpulse (fuer Ruckeln, Atem, Kratzen)."""
    t = tt(sec)
    e = np.zeros(len(t))
    for k, c in enumerate(centers):
        w = widths[k] if hasattr(widths, '__len__') else widths
        h = heights[k] if heights is not None else 1.0
        e += h * np.exp(-0.5 * ((t - c) / w) ** 2)
    return e


# --------------------------------------------------------------------------- Oszillatoren

def _phase(freq, sec=None):
    f = np.asarray(freq, dtype=float)
    if f.ndim == 0:
        f = np.full(n_(sec), float(f))
    return np.cumsum(f) / SR, f


def sine(freq, sec=None, ph0=0.0):
    p, _ = _phase(freq, sec)
    return np.sin(TAU * (p + ph0))


def _blep(t, dt):
    y = np.zeros_like(t)
    m = t < dt
    x = t[m] / dt[m]
    y[m] = x + x - x * x - 1.0
    m = t > 1.0 - dt
    x = (t[m] - 1.0) / dt[m]
    y[m] = x * x + x + x + 1.0
    return y


def saw(freq, sec=None, ph0=0.0):
    p, f = _phase(freq, sec)
    t = (p + ph0) % 1.0
    dt = np.clip(f / SR, 1e-6, 0.5)
    return 2.0 * t - 1.0 - _blep(t, dt)


def square(freq, sec=None, duty=0.5, ph0=0.0):
    p, f = _phase(freq, sec)
    t = (p + ph0) % 1.0
    dt = np.clip(f / SR, 1e-6, 0.5)
    y = np.where(t < duty, 1.0, -1.0)
    y = y + _blep(t, dt) - _blep((t + 1.0 - duty) % 1.0, dt)
    return y


def tri(freq, sec=None, ph0=0.0):
    p, _ = _phase(freq, sec)
    t = (p + ph0) % 1.0
    return 4.0 * np.abs(t - 0.5) - 1.0


def vibrato(base, sec, rate=5.0, depth=0.01, r=None, delay=0.0):
    """Frequenzkurve base*(1+LFO)."""
    t = tt(sec)
    ph = r.random() * TAU if r is not None else 0.0
    d = np.clip((t - delay) / 0.3, 0, 1) if delay else 1.0
    return base * (1.0 + depth * d * np.sin(TAU * rate * t + ph))


def midi(n):
    return 440.0 * 2.0 ** ((n - 69) / 12.0)


# --------------------------------------------------------------------------- Modal- und Saitensynthese

def modal(freqs, amps, t60s, sec, phases=None):
    """Summe exponentiell abklingender Sinus-Moden. t60 = Zeit bis -60 dB."""
    t = tt(sec)[None, :]
    f = np.asarray(freqs, dtype=float)[:, None]
    a = np.asarray(amps, dtype=float)[:, None]
    tau = (np.asarray(t60s, dtype=float) / 6.91)[:, None]
    ph = np.zeros_like(f) if phases is None else np.asarray(phases, dtype=float)[:, None]
    ok = f < SR / 2.2
    y = (a * ok * np.sin(TAU * f * t + ph) * np.exp(-t / tau)).sum(axis=0)
    return y


def click(sec, lo, hi, tau, r, order=2):
    """Gefilterter Rauschimpuls mit exponentiellem Abklingen (Transiente)."""
    x = white(sec, r) * expdecay(sec, tau)
    return bp(x, lo, hi, order)


def thump(sec, f0, f1, tau, r=None):
    """Tiefer Schlag: Sinus mit fallender Frequenz."""
    t = tt(sec)
    f = f1 + (f0 - f1) * np.exp(-t / (tau * 0.5))
    return np.sin(TAU * np.cumsum(f) / SR) * np.exp(-t / tau)


def pluck(freq, sec, r, decay=0.996, bright=0.5):
    """Karplus-Strong, nachgestimmt per Interpolation (exakte Tonhoehe)."""
    N = max(2, int(round(SR / freq)))
    f_actual = SR / N
    L = int(sec * SR * (f_actual / freq)) + N + 4
    out = np.zeros(L)
    init = r.uniform(-1, 1, N)
    k = int(round((1.0 - bright) * 6))
    for _ in range(k):
        init = 0.5 * (init + np.roll(init, 1))
    out[:N] = init - np.mean(init)
    for s in range(N, L, N):
        e = min(s + N, L)
        prev = out[s - N:e - N]
        prev1 = np.concatenate([[out[s - N - 1] if s - N - 1 >= 0 else 0.0], out[s - N:e - N - 1]])[:len(prev)]
        out[s:e] = decay * 0.5 * (prev + prev1)
    ratio = freq / f_actual
    idx = np.arange(n_(sec)) * ratio
    idx = np.clip(idx, 0, L - 1)
    return np.interp(idx, np.arange(L), out)


def additive(freq, sec, amps, t60s=None, inharm=0.0, ph=None):
    """Teiltonreihe mit Amplituden und Abklingzeiten."""
    k = np.arange(1, len(amps) + 1)
    fr = freq * k * np.sqrt(1.0 + inharm * k * k)
    t60 = t60s if t60s is not None else [sec * 2.0] * len(amps)
    return modal(fr, amps, t60, sec, ph)


def voice(f0, sec, forms, r, breath=0.06, jit=0.01, kind='saw', shimmer=0.08, wander=0.012):
    """Stimm-aehnlicher Klang: Glottis-Quelle durch Formantfilter. forms = [(fc oder (fc_start, fc_ende), q, gain), ...].
    Natuerlicher als ein blanker Saegezahn: Quelle fallend (-12 dB/Okt), Periodenjitter, Amplitudenschwankung pro Periode (shimmer),
    langsam wandernde Tonhoehe, Hauch pulsiert mit der Stimmritze."""
    n = n_(sec)
    f0 = np.asarray(f0, dtype=float)
    if f0.ndim == 0:
        f0 = np.full(n, float(f0))
    fast = smooth_rand(sec, r, 40.0, circ=False)    # Periodenjitter
    slow = smooth_rand(sec, r, 1.5, circ=False)     # Wandern der Tonhoehe
    f = f0 * (1.0 + jit * fast + wander * slow)
    src = saw(f) if kind == 'saw' else square(f, duty=0.3)
    src = lp(src, float(np.mean(f0)) * 4.0 + 300.0, 1)  # ~ -12 dB/Okt oberhalb der Eckfrequenz
    ph = (np.cumsum(f) / SR) % 1.0
    cyc = np.cumsum(np.diff(np.concatenate([[1.0], ph])) < 0)
    amp = 1.0 + shimmer * r.standard_normal(int(cyc[-1]) + 2)[cyc]
    pulse = 0.35 + 0.65 * (1.0 - ph)  # Hauch staerker kurz nach dem Stimmritzenschluss
    src = src * amp + breath * white(sec, r) * pulse
    y = np.zeros(n)
    for fc, q, g in forms:
        a, b = (fc, fc) if np.isscalar(fc) else fc
        y += g * tv_filter(src, lambda u, a=a, b=b: a + (b - a) * u, q)
    return y


# --------------------------------------------------------------------------- Natuerlichkeit: Koerper, Blasen, Koernung

def smooth_rand(sec, r, rate, circ=True):
    """Langsames Zufallssignal (Mittel 0, Std 1) mit Grenzfrequenz rate Hz."""
    x = lp(r.standard_normal(n_(sec)), rate, 1, circ=circ)
    return x / (np.std(x) + 1e-9)


def multi_gust(sec, r, rates=(0.07, 0.25, 0.9), weights=(1.0, 0.7, 0.4), circ=True):
    """Boeen/Flackern auf mehreren Zeitskalen, immer positiv, Mittel ~1."""
    g = sum(w * smooth_rand(sec, r, f, circ) for f, w in zip(rates, weights))
    g = g / (np.std(g) + 1e-9)
    return np.clip(1.0 + 0.55 * g, 0.03, 3.0)


def grain_noise(sec, r, lo, hi, rate=200.0, power=2.0, circ=True):
    """Gekoernts Band-Rauschen: Rauschen mal positiver, schiefer Zufallshuellkurve - klingt nach vielen kleinen Einzelereignissen."""
    base = bp(white(sec, r), lo, hi, 2, circ)
    g = np.clip(smooth_rand(sec, r, rate, circ) + 0.6, 0, None) ** power
    return base * g / (np.mean(g) + 1e-9)


def body(f0, t60, r, sec, n=14, ratio_pow=1.5, inharm=0.18, tilt=0.72, hard=0.5):
    """Schwingender Koerper (Holz, Keramik, Blech ...): viele unregelmaessige Moden, hoehere klingen schneller ab.
    hard 0..1 steuert, wie viele hohe Moden angeregt werden (harter Schlag = hell)."""
    k = np.arange(1, n + 1)
    ratios = k ** ratio_pow * (1.0 + inharm * r.uniform(-1, 1, n))
    ratios[0] = 1.0
    amps = (tilt ** (k - 1)) * r.uniform(0.5, 1.0, n)
    amps *= 1.0 / (1.0 + (ratios * f0 / (700.0 + 9000.0 * hard)) ** 2)
    t60s = t60 / (1.0 + 0.55 * (k - 1)) * r.uniform(0.7, 1.3, n)
    return modal(f0 * ratios, amps, t60s, sec, r.uniform(0, TAU, n))


def strike_noise(r, hard=0.5):
    """Kurzer Anschlagsimpuls: je haerter, desto kuerzer und heller."""
    d = 0.002 + 0.012 * (1.0 - hard)
    x = white(d, r) * np.hanning(n_(d))
    return lp(x, 500.0 + 9000.0 * hard, 1)


def hit(f0, t60, r, hard=0.5, sec=None, n=14, ratio_pow=1.5, inharm=0.18, tilt=0.72, thud=0.0, air=0.25):
    """Natuerlicher Aufprall: Koerper-Moden + Anschlagsgeraeusch + optional dumpfer Schlag (thud) und Luftrauschen."""
    sec = sec or min(2.5, t60 * 1.3 + 0.05)
    b = body(f0, t60, r, sec, n, ratio_pow, inharm, tilt, hard)
    s = strike_noise(r, hard)
    out = layer((b, 1.0), (s, air * 3.0))
    if thud:
        out = layer((out, 1.0), (thump(min(sec, 0.35), f0 * 0.9, f0 * 0.35, 0.06), thud))
    return out[:n_(sec)]


def bubble(f0, r=None):
    """Minnaert-Blase: Sinus, der waehrend des Abklingens leicht ansteigt (Wasser: Tropfen, Giessen, Brunnen)."""
    tau = 12.0 / f0
    d = min(0.25, 5 * tau)
    t = tt(d)
    f = f0 * (1.0 + 0.6 * t / (t + tau * 1.5))
    return np.sin(TAU * np.cumsum(f) / SR) * np.exp(-t / tau)


# --------------------------------------------------------------------------- Raum, Echo, Farbe

def _next_pow2(n):
    return 1 << (int(n) - 1).bit_length()


def fftconv(x, ir):
    n = len(x) + len(ir) - 1
    m = _next_pow2(n)
    y = np.fft.irfft(np.fft.rfft(x, m) * np.fft.rfft(ir, m), m)
    return y[:n]


def reverb(x, r, rt60=1.5, mix=0.25, damp=4500.0, pre=0.012, circ=False, lowcut=120.0):
    """Hall aus abklingendem Rauschen. circ=True: Schwanz laeuft um (fuer Loops), Laenge bleibt."""
    L = int(rt60 * 1.1 * SR)
    n = np.arange(L)
    ir = r.standard_normal(L) * np.exp(-6.91 * n / (rt60 * SR))
    ir = hp(lp(ir, damp, 1), lowcut, 1)
    p = int(pre * SR)
    ir = np.concatenate([np.zeros(p), ir])
    ir /= math.sqrt(float(np.sum(ir ** 2))) + 1e-12
    if circ:
        N = len(x)
        f = np.zeros(N)
        for k in range(0, len(ir), N):
            seg = ir[k:k + N]
            f[:len(seg)] += seg
        wet = np.fft.irfft(np.fft.rfft(x) * np.fft.rfft(f), N)
        return (1.0 - mix) * x + mix * wet
    wet = fftconv(x, ir)
    dry = np.concatenate([x, np.zeros(len(wet) - len(x))])
    return (1.0 - mix) * dry + mix * wet


def echo(x, delay, fb=0.35, taps=4, tone=3000.0, circ=False):
    d = int(delay * SR)
    out = x.copy()
    cur = x
    for k in range(taps):
        cur = lp(np.roll(cur, d) if circ else np.concatenate([np.zeros(d), cur])[:len(x)], tone, 1, circ) * fb
        out = out + cur
    return out


def soft(x, drive=1.5):
    return np.tanh(x * drive) / np.tanh(drive)


def crush(x, bits=8, hold=1):
    q = 2.0 ** (bits - 1)
    y = np.round(x * q) / q
    if hold > 1:
        y = np.repeat(y[::hold], hold)[:len(x)]
    return y


def lofi(x, r, lo=250.0, hi=5500.0, hiss=0.01, wow=0.0, circ=False):
    """Altes Radio / Tonband: Bandbegrenzung, Rauschen, Tonhoehenschwankung."""
    y = bp(x, lo, hi, 2, circ)
    if wow > 0:
        n = len(y)
        t = np.arange(n) / SR
        shift = wow * SR * 0.01 * (np.sin(TAU * 0.4 * t) + 0.5 * np.sin(TAU * 1.1 * t + 1.0))
        y = np.interp(np.arange(n) + shift, np.arange(n), y)
    return y + hiss * hp(white(len(y) / SR, r)[:len(y)], 1500, 1, circ)


def normalize(x, peak_db=-3.0):
    m = float(np.max(np.abs(x))) + 1e-12
    return x * (10.0 ** (peak_db / 20.0) / m)


def rms_db(x):
    return 20.0 * math.log10(float(np.sqrt(np.mean(x ** 2))) + 1e-12)


# --------------------------------------------------------------------------- Mischen und Loops

class Mix:
    """Mono-Puffer, in den Signale an Zeitpunkten eingemischt werden. loop=True: ueberlaufende Teile wickeln um."""

    def __init__(self, sec, loop=False):
        self.n = n_(sec)
        self.buf = np.zeros(self.n)
        self.loop = loop

    def add(self, sig, t, gain=1.0):
        i = int(round(t * SR))
        if self.loop:
            i %= self.n
            k = 0
            L = len(sig)
            while k < L:
                m = min(L - k, self.n - i)
                self.buf[i:i + m] += gain * sig[k:k + m]
                k += m
                i = (i + m) % self.n
        else:
            if i >= self.n:
                return
            m = min(len(sig), self.n - i)
            if m > 0:
                self.buf[i:i + m] += gain * sig[:m]
        return self


def crossfade_loop(x, xf):
    """x hat Laenge N + xf; Ergebnis Laenge N, Ende blendet nahtlos in den Anfang."""
    N = len(x) - xf
    out = x[:N].copy()
    w = np.linspace(0, 1, xf)
    a = np.sin(w * math.pi / 2)
    b = np.cos(w * math.pi / 2)
    out[:xf] = out[:xf] * a + x[N:N + xf] * b
    return out


def seam_ratio(x):
    """Sprung an der Loop-Naht relativ zur typischen Sample-Differenz (1 = unauffaellig)."""
    d = np.abs(np.diff(x))
    typ = float(np.percentile(d, 95)) + 1e-9
    return abs(x[0] - x[-1]) / typ


# --------------------------------------------------------------------------- Datei-Ausgabe

def write_wav(path, x, sr):
    x = np.clip(x, -1.0, 1.0)
    pcm = (x * 32767.0).astype('<i2')
    with wave.open(path, 'wb') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(pcm.tobytes())


# --------------------------------------------------------------------------- Musiktheorie / Sequencer

NOTE_BASE = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11}


def note(name):
    """'A4' 'C#5' 'Bb3' -> MIDI. 'R' = Pause (None)."""
    if name in ('R', 'r', '-'):
        return None
    m = re.match(r'^([A-Ga-g])([#b]?)(-?\d)$', name)
    if not m:
        raise ValueError(name)
    n = NOTE_BASE[m.group(1).upper()] + {'#': 1, 'b': -1, '': 0}[m.group(2)]
    return 12 * (int(m.group(3)) + 1) + n


def parse(seq):
    """'A4:1 C5:.5 R:.5' -> [(midi|None, beats), ...]"""
    out = []
    for tok in seq.split():
        nm, _, d = tok.partition(':')
        out.append((note(nm), float(d) if d else 1.0))
    return out


QUAL = {'': (0, 4, 7), 'm': (0, 3, 7), 'dim': (0, 3, 6), '7': (0, 4, 7, 10), 'm7': (0, 3, 7, 10), 'maj7': (0, 4, 7, 11),
        'sus2': (0, 2, 7), 'sus4': (0, 5, 7), 'aug': (0, 4, 8), '5': (0, 7), 'm6': (0, 3, 7, 9), '6': (0, 4, 7, 9)}


def chord(sym, octave=3):
    """'Am' 'F#m7' 'Bb' 'E7' -> Liste MIDI-Noten (Grundton in octave)."""
    m = re.match(r'^([A-G])([#b]?)(.*)$', sym)
    root = 12 * (octave + 1) + NOTE_BASE[m.group(1)] + {'#': 1, 'b': -1, '': 0}[m.group(2)]
    return [root + i for i in QUAL[m.group(3)]]


def play_line(mix, line, bpm, inst, t0=0.0, gain=1.0, **kw):
    """line = [(midi|None, beats)]; inst(freq, sec, r?) -> signal. Gibt Endzeit zurueck."""
    spb = 60.0 / bpm
    t = t0
    for m, b in line:
        if m is not None:
            mix.add(inst(midi(m), b * spb * kw.get('hold', 1.0) + kw.get('rel', 0.0)), t, gain)
        t += b * spb
    return t
