# -*- coding: utf-8 -*-
"""Membuat web-src-dh/vendor/manifold_dh.js dari paket npm manifold-3d (Apache-2.0) untuk GC-Ex Drill Hole.

Aplikasi offline: pustaka + WASM DITANAM di index.html (tanpa unduhan saat dipakai). Paket npm hanya dibutuhkan saat
membuat ulang berkas ini (sekali per versi pustaka):
    npm install --prefix /tmp/mf manifold-3d@3.5.4
    python tools/vendor/buat_manifold.py /tmp/mf/node_modules/manifold-3d
manifold.js adalah modul ES (import.meta, export default); diubah menjadi skrip biasa:
  - import.meta.url  -> document.baseURI (hanya dipakai mencari manifold.wasm; WASM diberikan lewat wasmBinary)
  - export default Module -> window.__MF_MODULE = Module
WASM disimpan base64 di window.__MF_WASM_B64 dan didekode saat pertama kali dipakai (web-src-dh/vunion_dh.js)."""
import base64, json, pathlib, sys

src = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "/tmp/mf/node_modules/manifold-3d")
ver = json.loads((src / "package.json").read_text(encoding="utf-8"))["version"]
js = (src / "manifold.js").read_text(encoding="utf-8")
assert js.count("export default Module") == 1, "struktur manifold.js berubah"
js = js.replace("import.meta.url", "(typeof document!=='undefined'?document.baseURI:'')").replace("export default Module", "window.__MF_MODULE=Module;")
assert "import.meta" not in js and "export " not in js.split("window.__MF_MODULE")[-1]
b64 = base64.b64encode((src / "manifold.wasm").read_bytes()).decode("ascii")
out = pathlib.Path(__file__).resolve().parents[2] / "web-src-dh" / "vendor" / "manifold_dh.js"
lic = (src / "LICENSE").read_text(encoding="utf-8").replace("*/", "* /")
out.write_text("/* manifold-3d %s (Apache License 2.0, https://github.com/elalish/manifold) -- boolean mesh untuk menyatukan solid vein\n"
               "   induk + cabang (GC-Ex Drill Hole). DIBUAT OTOMATIS oleh tools/vendor/buat_manifold.py; jangan disunting.\n"
               "   Isi pustaka & WASM tidak diubah; hanya pembungkus modul ES diubah menjadi skrip biasa.\n\n%s*/\n"
               "window.__MF_VER=%s;window.__MF_WASM_B64=%s;\n%s\n" % (ver, lic, json.dumps(ver), json.dumps(b64), js), encoding="utf-8")
print("OK", out, out.stat().st_size, "byte, manifold-3d", ver)
