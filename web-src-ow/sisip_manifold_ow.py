# -*- coding: utf-8 -*-
"""Ore Works 0.13.0: sisipkan / perbarui pustaka boolean (web-src/manifold.js + web-src/mfbool.js, manifold-3d Apache-2.0)
ke app-ow/index.html di antara penanda MF-OW-BEGIN / MF-OW-END. Sumber sama dengan GC-Ex Drill Hole & Block Model, jadi
pembaruan pustaka cukup: python tools/vendor/buat_manifold.py ... lalu python web-src-ow/sisip_manifold_ow.py"""
import pathlib, re
R = pathlib.Path(__file__).resolve().parents[1]
H = R / 'app-ow' / 'index.html'
s = H.read_text(encoding='utf-8')
mf = (R / 'web-src' / 'manifold.js').read_text(encoding='utf-8')
mb = (R / 'web-src' / 'mfbool.js').read_text(encoding='utf-8')
for t in (mf, mb):
    assert '</script' not in t.lower()
blok = '<script>/*MF-OW-BEGIN*/\n' + mf + '\n</script>\n<script>\n' + mb + '\n/*MF-OW-END*/</script>\n'
if '/*MF-OW-BEGIN*/' in s:
    a = s.index('<script>/*MF-OW-BEGIN*/'); b = s.index('/*MF-OW-END*/</script>\n') + len('/*MF-OW-END*/</script>\n')
    s = s[:a] + blok + s[b:]
else:
    k = s.index('<script type="text/plain" id="ore-main">')
    s = s[:k] + blok + s[k:]
H.write_text(s, encoding='utf-8')
print('manifold disisipkan:', len(mf) + len(mb), 'byte')
