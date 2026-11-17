# -*- coding: utf-8 -*-
"""Ore Works 0.13.1: sisipkan / perbarui pembaca GeoTIFF (web-src/geotiff.js, geotiff.js MIT) ke app-ow/index.html
di antara penanda GT-OW-BEGIN / GT-OW-END. Memperbarui pustaka: npm install --prefix /tmp/gt geotiff@<versi>, salin
dist-browser/geotiff.js (+ kepala lisensi) ke web-src/geotiff.js, lalu jalankan skrip ini."""
import pathlib
R = pathlib.Path(__file__).resolve().parents[1]
H = R / 'app-ow' / 'index.html'
s = H.read_text(encoding='utf-8')
g = (R / 'web-src' / 'geotiff.js').read_text(encoding='utf-8')
assert '</script' not in g.lower()
blok = '<script>/*GT-OW-BEGIN*/\n' + g + '\n/*GT-OW-END*/</script>\n'
if '/*GT-OW-BEGIN*/' in s:
    a = s.index('<script>/*GT-OW-BEGIN*/'); b = s.index('/*GT-OW-END*/</script>\n') + len('/*GT-OW-END*/</script>\n')
    s = s[:a] + blok + s[b:]
else:
    k = s.index('<script type="text/plain" id="ore-main">')
    s = s[:k] + blok + s[k:]
H.write_text(s, encoding='utf-8')
print('geotiff disisipkan:', len(g), 'byte')
