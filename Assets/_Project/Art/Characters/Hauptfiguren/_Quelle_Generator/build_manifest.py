"""Schreibt die Frame-Dauern der Kampf-Animationen als Lua-Tabelle (fuer das Aseprite-Zusammenbauen)."""
import os as _o, sys as _s; _s.path.insert(0, _o.path.normpath(_o.path.join(_o.path.dirname(_o.path.abspath(__file__)), '../../../__STYLEBIBLE/tools'))); import pixel_guard  # noqa: E402,F401  (Pixel Law, siehe __STYLEBIBLE/ART_STYLE.md)
import sys
import gen_hauptfiguren_combat as C

out = sys.argv[1]
lines = ['return {']
for an, fn in C.ANIMS.items():
    seq = fn()
    lines.append('  {name="%s", durs={%s}},' % (an, ','.join('%.3f' % p['dur'] for p in seq)))
lines.append('}')
open(out, 'w', encoding='utf-8').write('\n'.join(lines) + '\n')
print('\n'.join(lines))

import json
import os
from gen_hauptfiguren import SPECS, ORDER

# Muendungsposition (Pixel in der 56x56-Zelle, Ursprung oben links) im Feuer-Frame der Pistole je Figur/Richtung
if len(sys.argv) > 2:
    res = {}
    seq = C.ANIMS['shoot']()
    fire = 2
    for n, spec in SPECS.items():
        res[n] = {}
        for v in ORDER:
            C.render_pose(spec, v, seq[fire])
            res[n][v] = list(C.render_pose.muzzle)
    json.dump({'zelle': 56, 'feuer_frame_index': fire, 'muendung_px': res}, open(sys.argv[2], 'w'), indent=1)
    print(json.dumps(res))
