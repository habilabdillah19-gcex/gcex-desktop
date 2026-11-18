# -*- coding: utf-8 -*-
"""BM 0.24.109 / DH 0.24.111: ganti palet warna (web-src/palet.js), 10 palet, seperti Ore Works 0.24.0.
  P1 bawaan = sama persis dengan build sebelum fitur (warna terhitung elemen bingkai, panel, tombol, latar 3D).
  P2 tiap palet (Dasar, Malakit, Azurit, Hitam-putih, ...): bilah atas berganti, tombol bertulisan putih kontras >= 4,5:1,
     warna data 3D (semua trace Plotly) tidak berubah, tanpa galat konsol; tangkapan layar per palet.
  P3 muat ulang -> palet tetap (localStorage per aplikasi); kembali ke bawaan -> sama persis lagi.
  P5 warna tombol utama (aksen digelapkan) >= 4,5:1 terhadap teks putih di ke-10 palet.
  P4 BM Dasar = lapisan Keluarga GC-Ex dimatikan (bilah atas & tombol seperti BM 0.24.107).
Pemakaian: python tools/uji/uji_palet.py [app|app-dh] [html_lama_pembanding]"""
import json, random, subprocess, sys, tempfile, time
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT = Path(__file__).resolve().parents[2]; gagal = []
APP = sys.argv[1] if len(sys.argv) > 1 else 'app'; LAMA = sys.argv[2] if len(sys.argv) > 2 else None
OUT = Path(tempfile.gettempdir()) / ('uji_palet_' + APP); OUT.mkdir(exist_ok=True)
def cek(ok, p):
    print(("  ok   " if ok else "  GAGAL ") + p)
    if not ok: gagal.append(p)
def server(src):
    d = Path(tempfile.mkdtemp()); (d / "index.html").write_bytes(Path(src).read_bytes()); (d / "data-latihan").symlink_to(ROOT / "docs/tutorial-gcex/data")
    P = random.randint(9400, 9799); s = subprocess.Popen([sys.executable, "-m", "http.server", str(P)], cwd=str(d), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1); return s, P
WARNA = """(function(){var g=function(s,p){var e=document.querySelector(s);return e?getComputedStyle(e)[p||'backgroundColor']:null;};
  var bs=[].slice.call(document.querySelectorAll('button')).filter(function(e){var c=getComputedStyle(e);return e.offsetWidth&&c.color==='rgb(255, 255, 255)'&&c.backgroundColor!=='rgba(0, 0, 0, 0)'&&!e.closest('#gxPal');}),b=bs[0];
  return {top:g('#top'),toptx:g('#top','color'),side:g('#side'),pt:g('#ptCol'),status:g('#status'),stage:g('#stage','backgroundImage'),btn:b?getComputedStyle(b).backgroundColor:null,btntx:b?getComputedStyle(b).color:null,btns:bs.map(function(e){return getComputedStyle(e).backgroundColor;}),stat:g('#hint,#status .warn,.err','color'),body:g('body')};})()"""
DATA = "(function(){var d=$('plotDiv').data||[];return JSON.stringify(d.map(function(t){return [t.name,t.type,t.marker&&t.marker.color&&(Array.isArray(t.marker.color)?t.marker.color.slice(0,50):t.marker.color),t.color,t.facecolor&&t.facecolor.slice&&t.facecolor.slice(0,50),t.vertexcolor&&t.vertexcolor.slice&&t.vertexcolor.slice(0,50),t.line&&t.line.color&&(Array.isArray(t.line.color)?t.line.color.slice(0,50):t.line.color),t.colorscale];}));})()"
def rgb(s):
    import re
    m = re.findall(r"[\d.]+", s or ""); return tuple(int(float(x)) for x in m[:3]) if len(m) >= 3 else None
def lum(c):
    v = [x / 255 for x in c]; v = [x / 12.92 if x <= 0.03928 else ((x + 0.055) / 1.055) ** 2.4 for x in v]; return 0.2126 * v[0] + 0.7152 * v[1] + 0.0722 * v[2]
def kontras(a, b):
    x, y = sorted([lum(a), lum(b)]); return (y + 0.05) / (x + 0.05)
def muat(pg, P, tunggu):
    pg.goto("http://127.0.0.1:%d/index.html" % P); pg.wait_for_function("window.DLAT && DLAT.siap", timeout=60000); pg.evaluate("document.getElementById('dlatBtn').click()")
    pg.wait_for_function(tunggu, timeout=600000); pg.wait_for_function("!DLAT.busy", timeout=600000); pg.wait_for_timeout(4000)
    pg.evaluate("(function(){var el=document.querySelector('#ptree .ptr[data-id=\"set.v\"] .ptl');if(el)el.click();else if(window.uiTab)uiTab('View');})()"); pg.wait_for_timeout(800)
TUNGGU = "window.collars && collars.length > 0" if APP == 'app-dh' else "window.BX && BX.m"
with sync_playwright() as pw:
    b = pw.chromium.launch(args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader"])
    if LAMA:
        srv, P = server(LAMA); ctx0 = b.new_context(viewport={"width": 1500, "height": 860}); pg = ctx0.new_page(); pg.on("dialog", lambda x: x.accept())
        muat(pg, P, TUNGGU); W0 = pg.evaluate(WARNA); ctx0.close(); srv.terminate()
    srv, P = server(ROOT / APP / "index.html")
    ctx = b.new_context(viewport={"width": 1500, "height": 860}); pg = ctx.new_page(); E = []
    pg.on("pageerror", lambda e: E.append(str(e)[:200])); pg.on("console", lambda m: E.append(m.text[:200]) if m.type == "error" and "favicon" not in m.text else None); pg.on("dialog", lambda x: x.accept())
    muat(pg, P, TUNGGU)
    W1 = pg.evaluate(WARNA); D1 = pg.evaluate(DATA)
    if LAMA: cek(W1 == W0, "P1 bawaan = build sebelum fitur %s" % ("" if W1 == W0 else {k: (W0[k], W1[k]) for k in W1 if W0.get(k) != W1[k]}))
    ui = pg.evaluate("document.querySelectorAll('#gxPal .pr').length")
    cek(ui == 10, "UI Palet warna di Tampilan & performa: %d pilihan" % ui)
    pg.screenshot(path=str(OUT / "09_bawaan.png"))
    daftar = pg.evaluate("GXPAL.daftar().map(function(p){return [p.k,p.nm];})")
    kb = pg.evaluate("GXPAL.daftar().map(function(p){return [p.k,p.c.btn,+GXPAL.kontras(p.c.btn,'#FFFFFF').toFixed(2)];})")
    cek(all(x[2] >= 4.5 for x in kb), "P5 tombol utama (aksen) bertulisan putih >= 4,5:1 di semua palet: %s" % [(x[0], x[1], x[2]) for x in kb])
    for i, (k, nm) in enumerate(daftar):
        pg.evaluate("(k)=>{document.querySelector('#gxPal .pr[data-k=\"'+k+'\"]').click();}", k); pg.wait_for_timeout(900)
        W = pg.evaluate(WARNA); D = pg.evaluate(DATA)
        kt = min([kontras(rgb(x), (255, 255, 255)) for x in W["btns"] if rgb(x)] or [0])
        aktif = pg.evaluate("[GXPAL.aktif(),document.querySelector('#gxPal .pr.on').getAttribute('data-k')]")
        beda = (W["top"] != W1["top"]) or k in ("bawaan", "gcex")
        cek(D == D1 and kt >= 4.5 and len(W["btns"]) > 0 and aktif == [k, k] and beda, "P2 %-9s bilah %s, tombol %s (kontras min %.1f dari %d tombol putih), data 3D %s" % (k, W["top"], W["btn"], kt, len(W["btns"]), "sama" if D == D1 else "BERUBAH"))
        pg.screenshot(path=str(OUT / ("%02d_%s.png" % (i + 1, k))))
    if APP == 'app':
        pg.evaluate("document.querySelector('#gxPal .pr[data-k=\"dasar\"]').click()"); pg.wait_for_timeout(600)
        kb = pg.evaluate("document.getElementById('keluargaBm').media")
        cek(kb == "not all", "P4 BM Dasar: lapisan Keluarga GC-Ex dimatikan (%s)" % kb)
    pg.evaluate("document.querySelector('#gxPal .pr[data-k=\"azurit\"]').click()"); pg.wait_for_timeout(600); Wa = pg.evaluate(WARNA)
    muat(pg, P, TUNGGU); Wb = pg.evaluate(WARNA); ak = pg.evaluate("GXPAL.aktif()")
    cek(ak == "azurit" and Wb["top"] == Wa["top"] and Wb["btn"] == Wa["btn"], "P3 muat ulang: palet tetap %s (%s)" % (ak, Wb["top"]))
    pg.evaluate("document.querySelector('#gxPal .pr[data-k=\"bawaan\"]').click()"); pg.wait_for_timeout(900)
    W2 = pg.evaluate(WARNA)
    cek(W2 == W1, "P3 kembali ke bawaan = sama persis %s" % ("" if W2 == W1 else {k: (W1[k], W2[k]) for k in W1 if W1[k] != W2[k]}))
    cek(not E, "tanpa galat konsol %s" % E[:3])
    b.close(); srv.terminate()
print("Tangkapan layar:", OUT)
print("LULUS" if not gagal else "GAGAL: %s" % gagal); sys.exit(1 if gagal else 0)
