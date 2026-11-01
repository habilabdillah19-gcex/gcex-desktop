"""Ambil ulang tangkapan layar tutorial DB-Ex (docs/tutorial-core/gambar/t*.png) dari tampilan DB-Ex (app-core/index.html).

Langkah sama dengan tutorial.html, memakai paket data dummy (buat_data_dummy.py), backend lokal (uvicorn) dan
Ollama tiruan (ollama_tiruan.py, jawaban AI contoh). Jembatan Electron (window.gcexDesktop) diganti tiruan kecil;
folder / file yang "dipilih" di dialog diambil dari window.__q. Path ditampilkan sebagai D:\\Latihan\\... agar sama
dengan teks tutorial.

Pemakaian:  python docs/tutorial-core/tutorial_shots.py [--keep]     (butuh playwright, fastapi, uvicorn, pillow, openpyxl)
Lalu cetak PDF:  python docs/tutorial-core/buat_pdf.py
"""
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

from playwright.sync_api import sync_playwright

T = Path(__file__).resolve().parent
R = T.parents[1]
IMG = T / "gambar"
WORK = Path(tempfile.mkdtemp(prefix="dbex_tut_"))
DATA = WORK / "DB-Ex_Data_Dummy"
WIN = "D:\\Latihan\\DB-Ex_Data_Dummy"  # path yang ditampilkan di tangkapan layar
BE_PORT, OL_PORT = 8765, 11434
W, H = 1500, 900


def free(port: int) -> bool:
    with socket.socket() as s:
        return s.connect_ex(("127.0.0.1", port)) != 0


def wait_url(u: str, t: float = 30) -> None:
    t0 = time.time()
    while time.time() - t0 < t:
        try:
            urllib.request.urlopen(u, timeout=2)
            return
        except Exception:  # noqa: BLE001
            time.sleep(0.3)
    raise RuntimeError("tidak menjawab: " + u)


SHIM = """
window.__q = {folder: null, file: null};
window.gcexDesktop = {isDesktop: true,
  info: async () => ({app: 'DB-Ex', version: '%(ver)s', backendUrl: 'http://127.0.0.1:%(be)d', userData: '', platform: 'win32'}),
  backend: async () => ({ok: true, url: 'http://127.0.0.1:%(be)d', err: ''}),
  openLogs: async () => true, saveFile: async () => ({ok: true, path: 'D:\\\\Latihan\\\\DB-Ex_Core_Log.xlsx'}),
  alert: (m) => console.log('ALERT ' + m), confirm: (m) => { console.log('CONFIRM ' + m); return true; },
  prompt: (m, d) => d || 'Rina W.', openFile: async () => window.__q.file, openFolder: async () => window.__q.folder,
  fullscreen: async () => false, onFullscreen: () => {}, prjPending: async () => null, onPrj: () => {}, showFile: async () => true,
  ollamaStart: async () => ({ok: true, already: true}), pathOf: () => '',
  apiBin: async (path, body) => { const r = await fetch('http://127.0.0.1:%(be)d' + path, {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(body)}); return {buf: await r.arrayBuffer(), headers: {}}; }
};
try { localStorage.setItem('gcexCore.lw', '640'); localStorage.setItem('gcexCore.user', JSON.stringify('Rina W.')); localStorage.setItem('gcexCore.host', JSON.stringify('http://127.0.0.1:%(ol)d')); } catch (e) {}
"""


def main() -> None:
    keep = "--keep" in sys.argv
    ver = __import__("json").load(open(R / "builder-core.json"))["extraMetadata"]["version"]
    subprocess.run([sys.executable, str(T / "buat_data_dummy.py"), str(DATA)], check=True)
    procs = []
    env = dict(os.environ, GCEX_CACHE=str(WORK / "cache"), PYTHONPATH=os.pathsep.join([str(R / "backend"), os.environ.get("PYTHONPATH", "")]))
    if not free(BE_PORT) or not free(OL_PORT):
        raise SystemExit(f"port {BE_PORT} / {OL_PORT} sudah dipakai (tutup DB-Ex / Ollama dulu)")
    procs.append(subprocess.Popen([sys.executable, str(T / "ollama_tiruan.py"), str(DATA / "Foto_Core"), str(OL_PORT)],
                                  env=dict(os.environ, OLLAMA_DELAY="0.35")))
    procs.append(subprocess.Popen([sys.executable, "-m", "uvicorn", "gcex_backend.server:app", "--port", str(BE_PORT), "--log-level", "warning"],
                                  cwd=str(R / "backend"), env=env))
    try:
        wait_url(f"http://127.0.0.1:{OL_PORT}/api/version")
        wait_url(f"http://127.0.0.1:{BE_PORT}/health")
        IMG.mkdir(exist_ok=True)
        run(ver)
    finally:
        for p in procs:
            p.terminate()
        if not keep:
            shutil.rmtree(WORK, ignore_errors=True)


def run(ver: str) -> None:
    with sync_playwright() as pw:
        br = pw.chromium.launch()
        ctx = br.new_context(viewport={"width": W, "height": H}, device_scale_factor=1, bypass_csp=True)
        ctx.add_init_script(SHIM % {"ver": ver, "be": BE_PORT, "ol": OL_PORT})
        pg = ctx.new_page()
        errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)[:300]))
        pg.on("console", lambda m: print("  [halaman]", m.text[:160]) if m.text.startswith(("ALERT", "CONFIRM")) else None)

        def ev(js, *a):
            return pg.evaluate(js, *a)

        def wait(ms=600):
            pg.wait_for_timeout(ms)

        def winpath():  # tampilkan path gaya Windows seperti di tutorial
            ev("""(p) => { const w = document.querySelector('#prjName'); if (w && w.textContent.includes(p[0])) w.textContent = w.textContent.split(p[0]).join(p[1]).replace(/\\//g, '\\\\'); }""",
               [str(DATA), WIN])

        def shot(name, sel=None, pad=0, clip=None, within=None):
            wait(500)
            winpath()
            ev("() => { const t = document.getElementById('toast'); if (t) t.style.display = 'none'; }")
            out = IMG / f"{name}.png"
            if sel:
                b = pg.locator(sel).first.bounding_box()
                x0, y0, x1, y1 = b["x"] - pad, b["y"] - pad, b["x"] + b["width"] + pad, b["y"] + b["height"] + pad
                if within:  # potong ke wadah yang terlihat (mis. area kartu yang bisa digulir)
                    c = pg.locator(within).first.bounding_box()
                    x0, y0, x1, y1 = max(x0, c["x"]), max(y0, c["y"]), min(x1, c["x"] + c["width"]), min(y1, c["y"] + c["height"])
                x0, y0 = max(0, x0), max(0, y0)
                clip = {"x": x0, "y": y0, "width": min(W, x1) - x0, "height": min(H, y1) - y0}
            pg.screenshot(path=str(out), clip=clip) if clip else pg.screenshot(path=str(out))
            print("gambar", out.name, flush=True)

        def pick_file(path):
            ev("(p) => { window.__q.file = p; }", str(path))
            pg.click("#dhFile")
            pg.wait_for_function("document.getElementById('dhBody').style.display === 'flex' && !document.getElementById('dhFname').textContent.includes('membaca')")
            wait(400)

        def dh_tab(k):
            pg.click(f"#dhTabs button[data-k='{k}']")
            wait(300)

        def dh_go():
            pg.click("#dhGo")
            pg.wait_for_function("document.getElementById('dhRep').style.display === 'block'")
            wait(400)

        def col(src, name=None, use=None):
            """Atur kolom tambahan di tabel 'Kolom lain yang ikut' menurut nama kolom di file."""
            ev("""([src, name, use]) => { for (const tr of document.querySelectorAll('#dhCols tr')) { const td = tr.children[1]; if (!td || td.textContent !== src) continue;
                 if (name != null) { const i = tr.querySelector('[data-f=name]'); i.value = name; }
                 if (use != null) tr.querySelector('[data-f=use]').checked = use;
                 document.getElementById('dhCols').dispatchEvent(new Event('change')); } }""", [src, name, use])

        pg.goto((R / "app-core" / "index.html").as_uri())
        wait(1500)
        pg.add_style_tag(content=".mask.on{align-items:flex-start!important} .mask .dlg{margin-top:0!important}")
        # ---------------- Latihan 1: halaman awal & buka folder
        shot("t01_awal")
        ev("(p) => { window.__q.folder = p; }", str(DATA / "Foto_Core"))
        pg.click("#bOpen")
        pg.wait_for_function("document.getElementById('sSum').textContent.includes('24 foto')")
        wait(1500)
        shot("t02_folder")
        # ---------------- Latihan 2: data bor
        pg.click("#bDH")
        wait(800)
        dlg = "#mDH .dlg"
        dh_tab("collar")
        pick_file(DATA / "Data_Lab" / "Collar_Latihan.csv")
        dh_go()
        shot("t03_collar", dlg)
        dh_tab("survey")
        pick_file(DATA / "Data_Lab" / "Survey_Latihan.csv")
        dh_go()
        dh_tab("assay")
        pick_file(DATA / "Data_Lab" / "Assay_Latihan.xlsx")
        for src, nm in (("Au (ppm)", "Au"), ("Ag (ppm)", "Ag"), ("Cu (%)", "Cu"), ("Sample No", "Sample")):
            col(src, nm)
        col("Lab_Stat", use=False)
        ev("document.getElementById('dhMode').value = 'upsert'")
        shot("t04_assay", dlg)
        dh_go()
        shot("t05_assay_hasil", dlg)
        dh_tab("geology")
        pick_file(DATA / "Data_Lab" / "Geologi_Latihan.txt")
        dh_go()
        shot("t06_geologi", dlg)
        pg.keyboard.press("Escape")
        wait(400)
        if "--sampai2" in sys.argv:
            return
        part2(pg, ev, wait, shot, pick_file, dh_tab, dh_go)
        if errs:
            print("GALAT HALAMAN:", *errs, sep="\n  ")


def part2(pg, ev, wait, shot, pick_file, dh_tab, dh_go):
    LEFT = "#left"

    def sel_name(name):
        i = ev("(n) => S.view.findIndex(r => r.name === n)", name)
        ev("(i) => select(i)", i)
        pg.wait_for_function("() => S.det && S.view[S.cur] && S.det.tray !== undefined", timeout=15000)
        wait(900)

    def card_to(text, before=0):
        """Gulir kartu foto (#card) sampai judul bagian `text` di atas (dikurangi `before` piksel)."""
        ev("""([t, before]) => { const c = document.getElementById('card'); const h = [...c.querySelectorAll('h4, .sect, h3')].find(x => x.textContent.includes(t));
                       if (h) c.scrollTop += h.getBoundingClientRect().top - c.getBoundingClientRect().top - 6 - before; }""", [text, before])
        wait(300)

    def card_top():
        ev("() => { document.getElementById('card').scrollTop = 0; }")

    def pt(row, u):
        """Koordinat layar titik di baris core `row` (0 = atas) pada posisi u (0..1) sepanjang baris."""
        return ev("""([row, u]) => { const tr = S.det.tray, b = vw.getBoundingClientRect();
            const X0 = tr.x0 * V.iw, Y0 = tr.y0 * V.ih, BW = (tr.x1 - tr.x0) * V.iw, RH = (tr.y1 - tr.y0) * V.ih / tr.rows;
            return [b.left + V.x + (X0 + u * BW) * V.s, b.top + V.y + (Y0 + (row + 0.5) * RH) * V.s]; }""", [row, u])

    def drag(a, b):
        pg.mouse.move(*a)
        pg.mouse.down()
        for k in range(1, 9):
            pg.mouse.move(a[0] + (b[0] - a[0]) * k / 8, a[1] + (b[1] - a[1]) * k / 8)
            pg.wait_for_timeout(30)
        pg.mouse.up()
        wait(500)

    # ---------------- Latihan 3: AI lokal
    pg.click("#bAI")
    pg.wait_for_function("() => document.querySelector('input[name=aiM]')", timeout=15000)
    ev("() => { const m = document.querySelector('input[name=aiM][value=\"qwen3-vl:8b\"]'); if (m) { m.checked = true; m.dispatchEvent(new Event('change', {bubbles: true})); } document.getElementById('aiPx').value = '1600'; }")
    wait(500)
    shot("t07_ai_dialog", "#mAI .dlg")
    pg.click("#aiRun")
    pg.wait_for_function("() => { const t = document.getElementById('pTxt').textContent; const m = t.match(/AI (\\d+)\\//); return m && +m[1] >= 9; }", timeout=60000)
    shot("t08_ai_jalan")
    pg.wait_for_function("() => document.getElementById('sSum').textContent.includes('AI selesai 24')", timeout=120000)
    wait(2500)
    # ---------------- Latihan 4: kartu foto
    sel_name("IMG_0001.jpg")
    shot("t09_kartu_asli")
    card_to("Geologi", 150)
    shot("t10_kartu_geologi", LEFT)
    sel_name("LTH-102_Box6_19.00-22.80.jpg")
    card_to("Geologi", 150)
    shot("t11_kartu_543", LEFT)
    # ---------------- Latihan 5: edit & verifikasi
    ev("() => { const s = document.getElementById('fHole'); s.value = 'LTH-101'; s.dispatchEvent(new Event('change', {bubbles: true})); }")
    wait(800)
    sel_name("LTH-101_Box1_0.00-3.63.jpg")
    inp = pg.locator("#card [data-cf='rqd_pct']")
    inp.fill("62")
    inp.press("Tab")
    wait(700)
    pg.keyboard.press("Control+Enter")
    wait(1200)
    ev("() => select(S.view.findIndex(r => r.name.startsWith('LTH-101_Box1_')))")
    wait(1200)
    shot("t12_verifikasi")
    # ---------------- Latihan 6: overlay & area core
    pg.click("#fClr")
    wait(600)
    sel_name("IMG_0001.jpg")
    if not ev("() => OV.on"):
        pg.click("#vOv")
    wait(900)
    shot("t13_overlay")
    pg.click("#ovCal")
    wait(800)
    shot("t14_area_core", LEFT)
    ev("() => calEnd()")
    wait(400)
    # ---------------- Latihan 6b: tanda half core & core loss
    if ev("() => OV.on"):
        pg.click("#vOv")
    pg.click("#vMk")
    wait(400)
    ev("() => { const s = document.getElementById('mkKind'); s.value = 'halfcore'; s.dispatchEvent(new Event('change', {bubbles: true})); }")
    pg.click("#mkMode")
    wait(300)
    drag(pt(1, 0.0), pt(1, 0.506))
    pg.fill("#mkN", "sampel duplikat")
    wait(300)
    shot("t21_tanda_form", LEFT)
    pg.click("#mkSave")
    wait(900)
    ev("() => { const s = document.getElementById('mkKind'); s.value = 'coreloss'; s.dispatchEvent(new Event('change', {bubbles: true})); }")
    drag(pt(2, 0.70), pt(2, 0.95))
    pg.fill("#mkN", "core hilang saat pemboran")
    pg.click("#mkSave")
    wait(900)
    pg.click("#mkMode")
    wait(400)
    shot("t22_tanda_foto", LEFT)
    card_to("Tanda")
    shot("t23_tanda_kartu", "#cMk", pad=4, within="#card")
    ev("() => mkOpen(false)")
    wait(300)
    # ---------------- Latihan 6c: overlay berlapis & edit segmen
    if not ev("() => OV.on"):
        pg.click("#vOv")
    wait(700)
    card_top()
    shot("t24_overlay_lapisan", LEFT)
    ev("() => { const s = document.getElementById('ovPre'); s.value = 'Geoteknik'; s.dispatchEvent(new Event('change', {bubbles: true})); }")
    wait(800)
    shot("t25_overlay_geoteknik", LEFT)
    pg.click("#sgMode")
    wait(500)
    first = ev("() => { const s = SG.list.filter(x => x.f0 < 0.25).sort((a, b) => a.f0 - b.f0)[0]; return [s.id, s.f0, s.f1]; }")
    rows = ev("() => S.det.tray.rows")
    u_mid = ((first[1] + first[2]) / 2) * rows
    pg.mouse.click(*pt(int(u_mid), u_mid - int(u_mid)))
    wait(600)
    ev("""() => { const f = document.getElementById('sgForm'); const set = (k, v) => { const i = f.querySelector('[data-sgf="' + k + '"]'); if (i) { i.value = v; i.dispatchEvent(new Event('input', {bubbles: true})); i.dispatchEvent(new Event('change', {bubbles: true})); } };
               set('rqd_pct', '12'); set('weathering', 'W4 (Highly Weathered)'); set('notes', 'zona hancur'); }""")
    pg.click("#sgSave")
    wait(900)
    # geser garis batas akhir segmen itu ke kanan
    s1 = ev("(id) => { const s = SG.list.find(x => x.id === id); return s ? s.f1 : null; }", first[0])
    if s1 is not None and s1 * rows < 1:
        drag(pt(0, s1 * rows), pt(0, s1 * rows + 0.08))
    pg.mouse.click(*pt(int(u_mid), u_mid - int(u_mid)))
    wait(700)
    shot("t26_edit_segmen", LEFT)
    ev("() => { sgFormClose(); sgSetMode(false); }")
    wait(400)
    card_to("Interpretasi")
    shot("t27_daftar_segmen", "#cSeg", pad=4, within="#card")
    card_top()
    if ev("() => OV.on"):
        pg.click("#vOv")
    wait(400)
    # ---------------- Latihan 7: cari cepat & kueri kadar
    pg.keyboard.press("Control+K")
    pg.fill("#qq", "chalcopyrite")
    pg.wait_for_function("() => document.getElementById('qres').style.display === 'block'", timeout=10000)
    wait(800)
    shot("t15_cari")
    pg.fill("#qq", "Au>=3")
    wait(1200)
    shot("t16_cari_au")
    pg.keyboard.press("Enter")
    wait(1000)
    # ---------------- Latihan 8: filter kadar
    ev("""() => { const set = (id, v) => { const e = document.getElementById(id); e.value = v; e.dispatchEvent(new Event('change', {bubbles: true})); e.dispatchEvent(new Event('input', {bubbles: true})); };
               set('fEl', 'Au'); set('fAgg', 'gmax'); set('fMin', '1'); }""")
    wait(1200)
    shot("t17_filter")
    pg.click("#fClr")
    wait(600)
    # ---------------- Latihan 9: assay ulang per hole
    pg.click("#bDH")
    wait(600)
    dh_tab("assay")
    pick_file(DATA / "Data_Lab" / "Assay_Latihan_LTH-102_ulang.csv")
    shot("t18_upsert_map", "#mDH .dlg")
    dh_go()
    shot("t19_upsert_hasil", "#mDH .dlg")
    pg.keyboard.press("Escape")
    wait(500)
    # ---------------- Latihan 10: impor JSON lama, kondisi akhir
    pg.set_input_files("#jsonIn", str(DATA / "Dashboard_lama" / "Geotech_Dashboard_LTH-102.json"))
    wait(1500)
    ev("() => { const q = document.getElementById('qq'); q.value = ''; document.getElementById('qres').style.display = 'none'; }")
    sel_name("IMG_0001.jpg")
    card_top()
    shot("t20_akhir")


if __name__ == "__main__":
    main()
