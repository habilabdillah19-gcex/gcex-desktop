# -*- coding: utf-8 -*-
"""DH 0.24.99: kategori kolom impor diingat + pemeriksaan tambahan + Validasi & edit tabel (grid gaya MS Access).
Data uji fiktif dibuat di folder sementara (nama kolom Indonesia / tak dikenal, kesalahan disengaja).
  V1 alias nama Indonesia: Timur/Utara/Elevasi/Kedalaman_Total, Jarak/Kemiringan/Arah terpetakan otomatis.
  V2 nama kolom tak dikenal (BH, A, B): Hole_ID & From/To ditebak dari isi.
  V3 kategori geologi: Batuan -> Litologi, Ubahan -> Alterasi, Tekstur -> Kode lain; kotak kategori per kolom.
  V4 laporan validasi import memuat pemeriksaan baru (huruf besar/kecil, koordinat jauh, bukan angka, Emas > 500, litologi kosong, azimuth).
  V5 pilihan diingat: ubah Tekstur -> Struktur & buang unsur Perak, muat ulang halaman, import file yang sama -> pilihan kembali.
  V6 jendela Validasi & edit tabel (sebelum diproses): sel galat disorot, edit lewat keyboard, Ctrl+Z, Terapkan -> pratinjau ikut.
  V7 ekspor CSV memakai pemisah asli (;).
  V8 sesudah Buka: kategori geologi ikut ke 3D (gkCi('lith')).
  V9 sesudah diproses: Database Bor › Validasi & edit tabel -> edit koordinat -> Bangun ulang dataset -> collar berubah.
Pemakaian: python tools/uji/uji_dh_vgrid.py"""
import random, subprocess, sys, tempfile, time, urllib.request
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT = Path(__file__).resolve().parents[2]; TMP = Path(tempfile.mkdtemp())
port = str(random.randint(9100, 9899)); d = Path(tempfile.mkdtemp()); (d / "index.html").write_bytes((ROOT / "app-dh/index.html").read_bytes())
srv = subprocess.Popen([sys.executable, "-m", "http.server", port], cwd=str(d), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
P = "http://localhost:%s/index.html" % port
for _ in range(50):
    try: urllib.request.urlopen(P, timeout=1); break
    except Exception: time.sleep(.4)
# ---------- data fiktif ----------
H = ["DH-%02d" % i for i in range(1, 11)]
col = ["Kode,Timur,Utara,Elevasi,Kedalaman_Total"] + ["%s,%.1f,%.1f,300,6" % (h, 500000 + 20 * i, 9000000 + 15 * i) for i, h in enumerate(H)]
col[-1] = "DH-10,5500180.0,9000135.0,300,6"   # salah ketik koordinat
sv = ["Kode,Jarak,Kemiringan,Arah"] + ["%s,0,-60,90" % h for h in H]; sv[3] = "DH-03,0,-60,400"
asy = ["BH;A;B;Emas;Perak"]
for h in H:
    for f in range(3): asy.append("%s;%d;%d;%.2f;%.1f" % (h, f, f + 1, 0.5 + f, 2.0))
asy[4] = "DH-02;0;1;abc;2.0"; asy[5] = "dh-02;1;2;0.8;2.0"; asy[7] = "DH-03;0;1;900;2.0"; asy[9] = "DH-03;2;1;0.6;2.0"  # bukan angka, beda huruf, Emas > 500, To < From
geo = ["Hole_ID,From,To,Batuan,Ubahan,Tekstur"] + ["%s,0,3,AND,ARG,MASSIVE" % h for h in H]; geo[2] = "DH-02,0,3,,ARG,MASSIVE"
for n, L in (("uji_collar.csv", col), ("uji_survey.csv", sv), ("uji_assay.csv", asy), ("uji_geologi.csv", geo)): (TMP / n).write_text("\n".join(L) + "\n", encoding="utf-8")
gagal = []
def cek(ok, pesan):
    print(("  ok   " if ok else "  GAGAL ") + pesan)
    if not ok: gagal.append(pesan)
inp = lambda pg, k: pg.locator('input[onchange*="%s"]' % k).first
def isi(pg):
    for role, f in (("collar", "uji_collar.csv"), ("survey", "uji_survey.csv"), ("assay", "uji_assay.csv"), ("geo", "uji_geologi.csv")):
        inp(pg, "slotFile('%s'" % role).set_input_files(str(TMP / f)); pg.wait_for_timeout(700)
    pg.wait_for_timeout(800)
MAP = """()=>{var M=SA.map,T=function(r){return SA.T[M[r].t];},h=function(r,k){var c=M[r][k];return c>=0?T(r).h[c]:null;};
 return {c:[h('collar','hole'),h('collar','e'),h('collar','n'),h('collar','rl'),h('collar','td')],s:[h('survey','hole'),h('survey','dep'),h('survey','dip'),h('survey','azi')],
  a:[h('assay','hole'),h('assay','fr'),h('assay','to')],els:M.assay.els.map(function(c){return T('assay').h[c];}),
  kat:(function(){var o={};Object.keys(M.geo.kat||{}).forEach(function(c){o[T('geo').h[c]]=M.geo.kat[c];});return o;})(),sel:document.querySelectorAll('#gcBox select[data-gc]').length};}"""
with sync_playwright() as pw:
    ud = tempfile.mkdtemp()
    ctx = pw.chromium.launch_persistent_context(ud, args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader"], viewport={"width": 1400, "height": 850})
    ctx.add_init_script("window.showDirectoryPicker=undefined;window.showSaveFilePicker=undefined;")
    pg = ctx.new_page(); DLG = []; ERR = []
    pg.on("dialog", lambda x: (DLG.append(x.message[:300]), x.accept())); pg.on("pageerror", lambda e: ERR.append(str(e)[:300]))
    pg.goto(P); pg.wait_for_timeout(1500)
    if pg.query_selector('#fpCard button.sb'): pg.click('#fpCard button.sb'); pg.wait_for_timeout(400)
    isi(pg); m = pg.evaluate(MAP)
    cek(m["c"] == ["Kode", "Timur", "Utara", "Elevasi", "Kedalaman_Total"] and m["s"] == ["Kode", "Jarak", "Kemiringan", "Arah"], "V1 alias Indonesia: collar %s, survey %s" % (m["c"], m["s"]))
    cek(m["a"] == ["BH", "A", "B"], "V2 tebak dari isi: Hole_ID/From/To = %s" % m["a"])
    cek(m["kat"].get("Batuan") == "lith" and m["kat"].get("Ubahan") == "alt" and m["kat"].get("Tekstur") == "code" and m["sel"] == 3, "V3 kategori geologi %s, %s kotak pilihan" % (m["kat"], m["sel"]))
    vi = pg.evaluate("SA.VI.map(function(r){return r[0]+'|'+r[1]+'|'+r[2];})")
    need = ["Hole ID beda huruf besar/kecil", "Koordinat jauh dari lubang lain", "Nilai bukan angka Emas", "Emas > 500", "Litologi kosong", "Azimuth di luar 0–360"]
    cek(all(any(("|" + n) in v for v in vi) for n in need), "V4 pemeriksaan baru di laporan validasi: %s" % [n for n in need if not any(("|" + n) in v for v in vi)])
    cek(pg.evaluate("!!document.querySelector('#dbSum .vgOpenB') && /galat/.test(document.querySelector('#sfassay .vgsl').textContent)"), "V4 tombol Validasi & edit tabel + jumlah galat di slot Assay")
    # V5 diingat
    pg.evaluate("(function(){var M=SA.map,c=SA.T[M.geo.t].h.indexOf('Tekstur');VG.gk(c,'str');var p=SA.T[M.assay.t].h.indexOf('Perak');SA.tog('assay.els',p,false);})()")
    pg.reload(); pg.wait_for_timeout(1500)
    if pg.query_selector('#fpCard button.sb'): pg.click('#fpCard button.sb'); pg.wait_for_timeout(400)
    isi(pg); m2 = pg.evaluate(MAP)
    cek(m2["kat"].get("Tekstur") == "str" and "Perak" not in m2["els"] and "Emas" in m2["els"], "V5 pilihan diingat sesudah muat ulang: Tekstur=%s, unsur %s" % (m2["kat"].get("Tekstur"), m2["els"]))
    # V6 grid sebelum diproses
    pg.evaluate("VG.openSlot('assay')"); pg.wait_for_timeout(500)
    g = pg.evaluate("""()=>({on:document.getElementById('vgw').classList.contains('on'),E:document.querySelectorAll('#vggrid td.E').length,W:document.querySelectorAll('#vggrid td.W').length,
      rules:[].map.call(document.querySelectorAll('#vgrules div[data-r]'),function(d){return d.textContent;}),tabs:document.querySelectorAll('#vgtabs button').length})""")
    cek(g["on"] and g["E"] > 0 and g["W"] > 0 and any("To ≤ From" in r for r in g["rules"]) and g["tabs"] == 4, "V6 jendela terbuka: %s sel galat, %s peringatan, 4 tab, aturan %s" % (g["E"], g["W"], g["rules"][:4]))
    pg.evaluate("[].filter.call(document.querySelectorAll('#vgrules div[data-r]'),function(d){return /To ≤ From/.test(d.textContent);})[0].click()"); pg.wait_for_timeout(200)
    pg.click("#vgiss div[data-j='0']"); pg.wait_for_timeout(200)
    pg.keyboard.type("3"); pg.keyboard.press("Enter"); pg.wait_for_timeout(600)
    v1 = pg.evaluate("(function(){var M=SA.map,T=SA.T[M.assay.t];var r=T.r.filter(function(r){return r[0]==='DH-03'&&String(r[1])==='2';})[0];return String(r[2]);})()")
    pg.keyboard.press("Control+z"); pg.wait_for_timeout(500)
    v2 = pg.evaluate("(function(){var M=SA.map,T=SA.T[M.assay.t];var r=T.r.filter(function(r){return r[0]==='DH-03'&&String(r[1])==='2';})[0];return String(r[2]);})()")
    cek(v1 == "3" and v2 == "1", "V6 edit lewat keyboard: To 1 -> %s; Ctrl+Z -> %s" % (v1, v2))
    pg.evaluate("VG.state().sel.r=0"); pg.click("#vgiss div[data-j='0']"); pg.keyboard.press("F2"); pg.keyboard.press("Control+a"); pg.keyboard.type("3"); pg.keyboard.press("Enter"); pg.wait_for_timeout(600)
    # V7 ekspor
    pg.evaluate("window.__csv=null;window.dgDl=function(t,f){window.__csv=[f,t];}"); pg.click("#vgexp"); pg.wait_for_timeout(200)
    ex = pg.evaluate("window.__csv")
    cek(ex and ex[1].split("\r\n")[0] == "BH;A;B;Emas;Perak" and "DH-03;2;3;" in ex[1], "V7 ekspor CSV pemisah asli: %s / %s" % (ex and ex[0], ex and ex[1].split("\r\n")[0]))
    if len(sys.argv) > 2: pg.click("#vggo"); pg.wait_for_timeout(500); pg.evaluate("VG.kolom()"); pg.wait_for_timeout(800); pg.screenshot(path=sys.argv[2]); pg.evaluate("VG.openSlot('assay')")
    pg.click("#vggo"); pg.wait_for_timeout(800)
    ab = pg.evaluate("(SA.V.aBad||[]).length")
    cek(ab == 0 and not pg.evaluate("document.getElementById('vgw').classList.contains('on')"), "V6 Terapkan & tutup: pratinjau memakai tabel hasil edit (assay To <= From tersisa %s)" % ab)
    # V8 buka -> kategori ke 3D
    pg.evaluate("document.getElementById('dsName').value='UjiVG';SA.go()")
    pg.wait_for_function("document.getElementById('imp').classList.contains('off') && window.collars && collars.length>0", timeout=300000); pg.wait_for_timeout(3000)
    k8 = pg.evaluate("[window.gkCi?gkCi('lith'):-9, window.gkCi?gkCi('str'):-9, (SA.D.geoCat||[]).map(function(c){return c.n+':'+c.kat;})]")
    cek(k8[0] >= 0 and k8[1] >= 0, "V8 kategori geologi ikut ke proyek & 3D: %s" % k8[2])
    # V9 sesudah diproses
    pg.evaluate("PT.render(true)"); pg.wait_for_timeout(300)
    cek(pg.evaluate("!!document.querySelector(\"#ptree .ptr[data-id='db.vg']\")"), "V9 node Database Bor › Validasi & edit tabel ada")
    pg.evaluate("VG.openDs('collar')"); pg.wait_for_timeout(500)
    o9 = pg.evaluate("""()=>{var V=VG.state(),t=V.T.collar,i=t.tb.rows.findIndex(function(r){return r[0]==='DH-10';});return {i:i,hd:t.tb.hd0,w:[].some.call(document.querySelectorAll('#vgrules div'),function(d){return /Koordinat jauh/.test(d.textContent);})};}""")
    pg.evaluate("(function(){var V=VG.state();var vi=V.view.indexOf(%d);V.sel={r:vi,c:1};})()" % o9["i"]); pg.evaluate("document.getElementById('vggrid').focus()")
    pg.keyboard.press("F2"); pg.keyboard.press("Control+a"); pg.keyboard.type("500180"); pg.keyboard.press("Enter"); pg.wait_for_timeout(600)
    w9 = pg.evaluate("[].some.call(document.querySelectorAll('#vgrules div'),function(d){return /Koordinat jauh/.test(d.textContent);})")
    cek(o9["w"] and not w9, "V9 koordinat DH-10 jauh -> diperbaiki di grid, peringatan hilang")
    pg.click("#vggo")
    pg.wait_for_function("window.collars && collars.length>0 && document.getElementById('imp').classList.contains('off')", timeout=300000); pg.wait_for_timeout(2500)
    x9 = pg.evaluate("(function(){var c=SA.D.collars.filter(function(c){return c[0]==='DH-10';})[0];return c?c[1]:null;})()")
    cek(x9 == 500180, "V9 Bangun ulang dataset: Easting DH-10 di proyek = %s (harap 500180); dialog: %s" % (x9, [x[:60] for x in DLG][-2:]))
    if len(sys.argv) > 1: pg.evaluate("VG.openDs('assay')"); pg.wait_for_timeout(600); pg.screenshot(path=sys.argv[1])
    cek(not ERR, "tanpa galat halaman: %s" % ERR[:3])
    ctx.close()
srv.terminate()
print("LULUS" if not gagal else "GAGAL: %s" % gagal)
sys.exit(1 if gagal else 0)
