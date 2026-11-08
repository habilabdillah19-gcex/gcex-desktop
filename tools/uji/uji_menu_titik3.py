# -*- coding: utf-8 -*-
"""Project Tree: satu pintu menu = tombol ⋯, perintah tambah = baris "+ Tambah …" (BM 0.24.41, DH 0.24.45).

A/B: build lama (git <dasar>:app*/index.html) vs build baru, data latihan simulasi sama.
Yang diukur (akibat, bukan keberadaan kode):
  1. Klik kanan sungguhan pada baris node: build lama membuka #ptMenu, build baru TIDAK.
  2. ⋯ baris yang tidak dipilih & tidak di-hover: build baru opacity > 0 dan visible.
  3. Baris "+ Tambah …" yang diharapkan ada di tiap aplikasi; menu ⋯ induknya tidak lagi memuat perintah itu.
  4. Mengklik baris tambah benar-benar menambah (DH: jumlah plan +1; BM: jumlah preset +1; DH: item pilihan
     struktur muncul sebagai menu).
Pemakaian: python tools/uji/uji_menu_titik3.py [--dasar=<ref git>]
"""
import json, os, random, subprocess, sys, tempfile, time, urllib.request
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT = Path(__file__).resolve().parents[2]; DATA = ROOT / "docs" / "tutorial-gcex" / "data"
DASAR = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--dasar=")), "HEAD")
HARAP = {"app/index.html": ["ref", "wf"],
         "app-dh/index.html": ["sp.ref", "wf", "db", "db.plan", "st", "st.flt", "gm"]}
# keputusan pemilik 8 Nov 2026 (BM 0.24.42 / DH 0.24.46); 21:19: menu ⋯ Data Spasial BOLEH memuat import file langsung (bukan baris + Tambah): versi topo / pit / ortho / BM dan preset TETAP di panel,
# TANPA baris + Tambah; import wireframe, data referensi dan "+ Kampanye baru" DIHAPUS dari panel.
TANPA = {"app/index.html": ["dig.pst"], "app-dh/index.html": ["sp.topo", "sp.pit", "sp.ortho", "bm", "mp.pf"]}  # pick-up CSV tetap di panel Peta (DH 0.24.47)
JS_INFO = r"""(function(){PT.render(true);var L=PT.flatAll(PT.nodes||[]);
  var add=L.filter(function(n){return n.addRow;}).map(function(n){return n.id.replace(/\.\+$/,'');});
  var menuTambah=[];L.forEach(function(n){if(!n.menu||n.addRow)return;var M=[];try{M=n.menu()||[];}catch(e){}
    M.forEach(function(o){if(o&&o.t&&/^(\+ |Tambah (kampanye|wireframe)|Plan baru|Kampanye baru|Import wireframe geologi|Import CSV struktur|Import CSV titik|Simpan pengaturan sekarang sebagai preset)/.test(o.t))menuTambah.push(n.id+': '+o.t);});});
  var x=[].slice.call(document.querySelectorAll('#ptree .ptr:not(.sel) .ptx'))[0],cs=x&&getComputedStyle(x);
  var pin=[];[].forEach.call(document.querySelectorAll('input[type=file]'),function(i){var o=i.getAttribute('onchange')||'';if(/mdImport|mdPts|mdStr|stImport/.test(o)){var q=i.closest('section');pin.push(q?q.id:'(luar)');}});
  return {add:add,menuTambah:menuTambah,ptx:cs?[+cs.opacity,cs.visibility]:null,panelImport:pin,kpBaru:document.documentElement.outerHTML.indexOf('kpImpBaru()">')>=0};})()"""

def jalan(html, nama):
    port = str(random.randint(9100, 9899)); d = Path(tempfile.mkdtemp())
    (d / "index.html").write_bytes(html); os.symlink(DATA, d / "data-latihan")
    srv = subprocess.Popen([sys.executable, "-m", "http.server", port], cwd=str(d), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    P = "http://localhost:%s/index.html" % port
    for _ in range(50):
        try: urllib.request.urlopen(P, timeout=1); break
        except Exception: time.sleep(.4)
    H = {}
    with sync_playwright() as pw:
        ctx = pw.chromium.launch_persistent_context(tempfile.mkdtemp(), args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"], viewport={"width": 1500, "height": 900})
        ctx.add_init_script("window.showDirectoryPicker=async function(){throw new Error('batal');};")
        pg = ctx.new_page(); pg.on("dialog", lambda x: x.accept(x.default_value or "UJI") if x.type == "prompt" else x.accept())
        pg.goto(P); pg.wait_for_timeout(1500); pg.wait_for_function("window.DLAT && DLAT.siap", timeout=90000)
        pg.evaluate("document.getElementById('dlatBtn').click()"); pg.wait_for_timeout(3000)
        pg.wait_for_function("!DLAT.busy", timeout=900000); pg.wait_for_timeout(2500)
        pg.evaluate("PT.render(true)"); pg.locator("#ptree .ptr[data-id='proj']").click(button="right"); pg.wait_for_timeout(300)
        H["klikKanan"] = pg.evaluate("!!document.getElementById('ptMenu')"); pg.keyboard.press("Escape"); pg.mouse.move(900, 500)
        pg.evaluate("PT.select('proj')"); pg.wait_for_timeout(300)
        H.update(pg.evaluate(JS_INFO))
        if "app-dh" in nama and H["add"]:
            n0 = pg.evaluate("PL.sets.length"); pg.evaluate("PT.open['db']=1;PT.open['db.plan']=1;PT.render(true)")
            pg.locator("#ptree .ptr[data-id='db.plan.+']").click(); pg.wait_for_timeout(600)
            H["plan"] = [n0, pg.evaluate("PL.sets.length")]
            pg.evaluate("PT.open['st']=1;PT.render(true)"); pg.locator("#ptree .ptr[data-id='st.+']").click(); pg.wait_for_timeout(300)
            H["stMenu"] = pg.evaluate("(document.getElementById('ptMenu')||{}).innerText||''"); pg.keyboard.press("Escape")
        if "app-dh" in nama:
            pg.evaluate("PT.select('sp.topo')"); pg.wait_for_timeout(700)
            H["spPanel"] = pg.evaluate("document.querySelectorAll('input[onchange*=spAdd]').length")
        else:
            pg.evaluate("PT.select('dig.pst')"); pg.wait_for_timeout(500)
            H["presetKartu"] = pg.evaluate("((document.getElementById('ptCard')||{}).innerText||'').indexOf('Simpan pengaturan sekarang sebagai preset')>=0")
        ctx.close()
    srv.terminate(); return H

salah = []
for app, harap in HARAP.items():
    lama = subprocess.run(["git", "show", "%s:%s" % (DASAR, app)], cwd=ROOT, capture_output=True).stdout
    A = jalan(lama, app + " lama"); B = jalan((ROOT / app).read_bytes(), app)
    print(app, "\n  lama:", json.dumps(A, ensure_ascii=False), "\n  baru:", json.dumps(B, ensure_ascii=False))
    if not A["klikKanan"]: salah.append(app + ": build lama klik kanan tidak membuka menu -> uji tidak membuktikan")
    if B["klikKanan"]: salah.append(app + ": klik kanan masih membuka menu")
    if not B["ptx"] or B["ptx"][0] <= 0 or B["ptx"][1] != "visible": salah.append(app + ": ⋯ tidak selalu tampak %s" % B["ptx"])
    kurang = [h for h in harap if h not in B["add"]]
    if kurang: salah.append(app + ": baris + Tambah tidak ada untuk %s" % kurang)
    if B["menuTambah"]: salah.append(app + ": menu ⋯ masih memuat perintah tambah %s" % B["menuTambah"])
    if "plan" in B and B["plan"][1] != B["plan"][0] + 1: salah.append("DH: + Tambah plan bor tidak menambah plan %s" % B["plan"])
    if "stMenu" in B and "Import CSV struktur" not in B["stMenu"]: salah.append("DH: + Tambah struktur tidak membuka pilihan")
    ada = [t for t in TANPA[app] if t in B["add"]]
    if ada: salah.append(app + ": baris + Tambah mestinya tidak ada untuk %s" % ada)
    if B.get("panelImport"): salah.append(app + ": tombol import wireframe / data referensi masih di panel %s" % B["panelImport"])
    if not A.get("panelImport"): salah.append(app + ": build lama tanpa tombol import di panel -> uji tidak membuktikan")
    if "app-dh" in app and B.get("kpBaru"): salah.append("DH: tombol + Kampanye baru masih di dialog import")
    if "app-dh" in app and not B.get("spPanel"): salah.append("DH: tombol + Tambah versi topografi hilang dari panel Data Spasial")
    if "app-dh" not in app and not B.get("presetKartu"): salah.append("BM: tombol simpan preset hilang dari kartu")
print("\nGAGAL:\n  " + "\n  ".join(salah) if salah else "\nLULUS")
