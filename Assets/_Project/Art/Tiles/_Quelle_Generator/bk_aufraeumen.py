"""Nach python bk_build.py: setzt alle PNGs, deren PIXEL unveraendert sind (nur anders kodiert), per git checkout zurueck.
Danach zeigt git status nur wirklich neue/geaenderte Teile.   Aufruf:  python3 bk_aufraeumen.py"""
import io
import os
import subprocess

from PIL import Image, ImageChops

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = subprocess.check_output(['git', 'rev-parse', '--show-toplevel'], cwd=HERE, text=True).strip()
ART = os.path.normpath(os.path.join(HERE, '..', '..'))
rel = os.path.relpath(ART, ROOT)

lines = subprocess.check_output(['git', 'status', '--porcelain', rel], cwd=ROOT, text=True).splitlines()
restored, kept = 0, []
for l in lines:
    if not l.startswith(' M'):
        continue
    p = l[3:].strip().strip('"')
    if p.lower().endswith('.png'):
        try:
            old = Image.open(io.BytesIO(subprocess.check_output(['git', 'show', 'HEAD:' + p], cwd=ROOT))).convert('RGBA')
            new = Image.open(os.path.join(ROOT, p)).convert('RGBA')
            if old.size == new.size and ImageChops.difference(old, new).getbbox() is None:
                subprocess.check_call(['git', 'checkout', '--', p], cwd=ROOT)
                restored += 1
                continue
        except Exception:
            pass
    kept.append(p)
print('zurueckgesetzt (nur Kodierung):', restored)
for k in kept:
    print('geaendert:', k)
