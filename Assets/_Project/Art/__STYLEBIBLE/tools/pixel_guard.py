"""Pixel-Law-Waechter: faengt JEDES PIL-Image.save() auf PNGs im Art-Ordner ab.

Einbindung (steht in jedem Generator ganz oben):  import pixel_guard
Regel:
  * Zieldatei steht in style_baseline.txt (bekannte Altlast)  -> darf schreiben, wird nur gezaehlt.
  * Sonst (neue oder bisher konforme Datei)                   -> muss E_-fehlerfrei sein, sonst PixelLawError
    und die Datei wird NICHT geschrieben.
  * Vorschau-/Uebersichtsbilder und Dateien ausserhalb Art/ werden ignoriert.
Notbremse nur fuer Migrationsarbeit: Umgebungsvariable PIXEL_GUARD=warn (Fehler nur melden). Nie dauerhaft setzen.
"""
import atexit
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import style_lib as S  # noqa: E402

ART = os.path.dirname(os.path.dirname(HERE))          # .../Art
BASELINE_FILE = os.path.join(os.path.dirname(HERE), "style_baseline.txt")


class PixelLawError(Exception):
    pass


def load_baseline(path=BASELINE_FILE):
    try:
        return {l.strip() for l in open(path, encoding="utf-8") if l.strip() and not l.startswith("#")}
    except OSError:
        return set()


def rel_art(path):
    """Pfad relativ zu Art/ (mit /), oder None wenn ausserhalb / ausgenommen."""
    p = os.path.abspath(str(path))
    if not p.startswith(ART + os.sep):
        return None
    rel = p[len(ART) + 1:].replace(os.sep, "/")
    parts = rel.split("/")
    if any(d in S.SKIP_DIRS or d.startswith("_Backup") for d in parts[:-1]):
        return None
    if any(k in parts[-1] for k in S.SKIP_NAMES):
        return None
    return rel


_BASE = load_baseline()
_stat = {"ok": 0, "legacy": 0, "fail": 0}
_orig_save = Image.Image.save


def _guarded_save(self, fp, format=None, **params):
    is_png = isinstance(fp, (str, os.PathLike)) and str(fp).lower().endswith(".png")
    rel = rel_art(fp) if is_png else None
    if rel is not None:
        if rel in _BASE:
            _stat["legacy"] += 1
        else:
            kind = S.guess_kind(rel)
            err, warn = S.check_image(self, kind, path=rel)
            for m in warn:
                print(f"[pixel_guard] warn {rel}: {m}")
            if err:
                _stat["fail"] += 1
                msg = f"Pixel Law verletzt: {rel} ({kind})\n  " + "\n  ".join(err) + \
                      "\n  Regeln: Art/__STYLEBIBLE/ART_STYLE.md, Farben nur aus style_lib.P"
                if os.environ.get("PIXEL_GUARD") == "warn":
                    print("[pixel_guard] " + msg)
                else:
                    raise PixelLawError(msg)
            else:
                _stat["ok"] += 1
    return _orig_save(self, fp, format, **params)


if Image.Image.save is not _guarded_save:
    Image.Image.save = _guarded_save


@atexit.register
def _summary():
    if any(_stat.values()):
        print(f"[pixel_guard] konform geschrieben: {_stat['ok']}, Altlast (Baseline): {_stat['legacy']}, verletzt: {_stat['fail']}")
