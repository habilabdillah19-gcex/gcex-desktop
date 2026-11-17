# -*- coding: utf-8 -*-
"""Menanam sql.js (SQLite di WebAssembly, MIT) ke app-ow/index.html -- dipakai Ore Works untuk file proyek .owproj
(SQLite: tabel bor bisa dibaca DB Browser / Python / Access-ODBC; bagian besar disimpan biner + deflate).

Aplikasi offline: pustaka + WASM DITANAM (tanpa unduhan saat dipakai). Paket npm hanya dibutuhkan saat menanam ulang:
    npm install --prefix /tmp/sq sql.js@1.13.0
    python tools/vendor/buat_sqljs.py /tmp/sq/node_modules/sql.js
Isi pustaka tidak diubah. Blok di index.html dibatasi /*SQ-OW-BEGIN*/ ... /*SQ-OW-END*/ dan diganti utuh bila sudah ada;
bila belum ada, disisipkan tepat sebelum <script type="text/plain" id="ore-main">.
WASM disimpan base64 di window.__SQ_WASM_B64 dan didekode saat pertama kali proyek .owproj disimpan / dibuka."""
import base64, json, pathlib, sys

src = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "/tmp/sq/node_modules/sql.js")
ver = json.loads((src / "package.json").read_text(encoding="utf-8"))["version"]
js = (src / "dist" / "sql-wasm.js").read_text(encoding="utf-8")
assert "</script" not in js.lower() and "import.meta" not in js
b64 = base64.b64encode((src / "dist" / "sql-wasm.wasm").read_bytes()).decode("ascii")
lic = (src / "LICENSE").read_text(encoding="utf-8").replace("*/", "* /")
blok = ("<script>/*SQ-OW-BEGIN*/ /* sql.js %s (MIT, https://github.com/sql-js/sql.js) -- SQLite (WebAssembly) untuk file proyek\n"
        "   Ore Works .owproj. DIBUAT OTOMATIS oleh tools/vendor/buat_sqljs.py; jangan disunting. Isi pustaka & WASM tidak diubah.\n\n%s*/\n"
        "window.__SQ_VER=%s;window.__SQ_WASM_B64=%s;\n%s\n/*SQ-OW-END*/</script>\n" % (ver, lic, json.dumps(ver), json.dumps(b64), js))
P = pathlib.Path(__file__).resolve().parents[2] / "app-ow" / "index.html"
t = P.read_text(encoding="utf-8")
if "/*SQ-OW-BEGIN*/" in t:
    a = t.index("<script>/*SQ-OW-BEGIN*/"); b = t.index("/*SQ-OW-END*/</script>\n", a) + len("/*SQ-OW-END*/</script>\n")
    t = t[:a] + blok + t[b:]
else:
    m = '<script type="text/plain" id="ore-main">'
    assert t.count(m) == 1
    t = t.replace(m, blok + m)
P.write_text(t, encoding="utf-8")
print("OK", P, "sql.js", ver, len(blok), "byte")
