"""BUILD-ALLES fuer Art/Welt: fuehrt alle Zonen-Generatoren aus, pruefft (qa_welt) und schreibt _Liste.txt + _Assets.json.
Aufruf: python build_welt.py            (komplett, ca. 1 Minute)
        python build_welt.py fluss     nur eine Zone: gemeinsam | fluss | tiefwald | sumpf | felsland | ruinen
Hinweis: Die Generatoren schreiben die PNGs jedes Mal neu (deterministisch, gleiche Eingabe -> gleiche Pixel)."""
import os as _o, sys as _s; _s.path.insert(0, _o.path.normpath(_o.path.join(_o.path.dirname(_o.path.abspath(__file__)), '../../__STYLEBIBLE/tools'))); import pixel_guard  # noqa: E402,F401  (Pixel Law, siehe __STYLEBIBLE/ART_STYLE.md)
import json
import os
import subprocess
import sys
import time

import qa_welt
import welt_lib as W

HERE = os.path.dirname(os.path.abspath(__file__))
STEPS = {
    'gemeinsam': ['gen_gemeinsam.py'],
    'fluss': ['gen_fluss.py', 'gen_fische.py', 'gen_fluss_objekte.py'],
    'tiefwald': ['gen_tiefwald.py'],
    'sumpf': ['gen_sumpf.py'],
    'felsland': ['gen_felsland.py'],
    'ruinen': ['gen_ruinen.py'],
}
ORDER = ['gemeinsam', 'fluss', 'tiefwald', 'sumpf', 'felsland', 'ruinen']


def run(script):
    t0 = time.time()
    r = subprocess.run([sys.executable, os.path.join(HERE, script)], cwd=HERE, capture_output=True, text=True)
    tail = (r.stdout.strip().splitlines() or [''])[-1]
    print('%-22s %-5s %5.1fs  %s' % (script, 'ok' if r.returncode == 0 else 'FEHLER', time.time() - t0, tail))
    if r.returncode:
        print(r.stdout[-2000:], r.stderr[-2000:])
    return r.returncode == 0


def write_liste(entries):
    lines = ['WELT JENSEITS ZONE 1 - Asset-Liste (automatisch von build_welt.py erzeugt, nicht von Hand aendern)',
             'Format: Datei | Groesse | Art | Zelle | Frames', '']
    zone = None
    for e in sorted(entries, key=lambda e: e['datei']):
        if e['zone'] != zone:
            zone = e['zone']
            lines += ['', '== %s ==' % zone]
        lines.append('%-46s %9s  %-16s %-8s %s' % (e['datei'].split('/', 1)[1], '%dx%d' % tuple(e['groesse']), e.get('art', '?'),
                                                   ('%dx%d' % tuple(e['zellen'])) if e.get('zellen') else '-', e.get('frames', '-')))
    open(W.WELT + '/_Liste.txt', 'w', encoding='utf-8', newline='\n').write('\n'.join(lines) + '\n')
    W.dump_json(W.WELT + '/_Assets.json', {'ppu': 32, 'filter': 'Point', 'kompression': 'keine', 'sprites': entries})


def main(argv):
    zones = argv or ORDER
    for z in zones:
        if z not in STEPS:
            print('unbekannte Zone', z)
            return 2
    ok = True
    for z in zones:
        for s in STEPS[z]:
            ok = run(s) and ok
    run('vorschau_uebersicht.py')
    entries, errs = qa_welt.main(verbose=True)
    write_liste(entries)
    print('_Liste.txt und _Assets.json geschrieben (%d Eintraege)' % len(entries))
    return 0 if ok and not errs else 1


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
