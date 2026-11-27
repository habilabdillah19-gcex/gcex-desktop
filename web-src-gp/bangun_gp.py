# -*- coding: utf-8 -*-
"""Rakit Geo Pocket menjadi satu berkas HTML offline: docs/geo-pocket/Geo_Pocket.html
Pakai: python web-src-gp/bangun_gp.py   (pustaka bersama diambil dari web-src/: delaunator.min.js, geotiff.js)"""
from pathlib import Path
H=Path(__file__).resolve().parent;R=H.parent
E=lambda p:p.read_text(encoding='utf-8').replace('</script>','<\\/script>')
t=(H/'template.html').read_text(encoding='utf-8')
for k,p in [('/*CSS*/',H/'style.css'),('/*DEL*/',R/'web-src'/'delaunator.min.js'),('/*GTIFF*/',R/'web-src'/'geotiff.js'),('/*CORE*/',H/'core.js'),('/*GEO2*/',H/'geo2.js'),('/*VIEW*/',H/'view3d.js'),('/*MAP*/',H/'map2d.js'),('/*UI*/',H/'ui.js')]:
    assert k in t,k
    t=t.replace(k,p.read_text(encoding='utf-8') if p.suffix=='.css' else E(p))
out=R/'docs'/'geo-pocket'/'Geo_Pocket.html';out.parent.mkdir(parents=True,exist_ok=True);out.write_text(t,encoding='utf-8')
print(out,len(t))
