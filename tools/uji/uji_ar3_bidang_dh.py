"""Autorun Estimasi dari Nol memasang sayatan di bidang tiap domain (Drill Hole 0.24.75).
A/B: build lama (git, --dasar=HEAD) vs build baru (app-dh/index.html), data latihan (Demo), parameter domain dikosongkan,
tanpa simpan & tanpa estimasi. Dicek: jumlah komposit per domain baru >= lama, minimal satu domain bertambah,
sayatan pemakai dikembalikan sesudah autorun, opsi mati = perilaku lama persis, tanpa pageerror."""
import json, random, subprocess, sys, tempfile, time, urllib.request
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT = Path(__file__).resolve().parents[2]
DASAR = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--dasar=")), "HEAD")
DATA = ROOT / "docs" / "tutorial-gcex" / "data"

JS = r"""
(async function (bidang) {
  var tunggu = function (f, ms) { return new Promise(function (res) { var t0 = Date.now(); (function p() { if (f() || Date.now() - t0 > ms) return res(); setTimeout(p, 300); })(); }); };
  /* domain latihan dari kolom geologi Vein (satu domain per kode) + solid */
  var col = VS.kolom().filter(function (c) { return c.n === 'Vein' && c.src === 'g'; })[0]; gmOpt('vsCol', col.key); gmOpt('vsGap', 0);
  VS.terapkan(true); await new Promise(function (r) { setTimeout(r, 500); }); imSync(true); await new Promise(function (r) { setTimeout(r, 500); });
  GM.doms.forEach(function (d) { d.est = null; });
  try { gmDirty(true); } catch (e) {}
  var SEC = ['sMode', 'p1e', 'p1n', 'p2e', 'p2n', 'dipS', 'pos', 'thick'], a0 = SEC.map(function (k) { var e = document.getElementById(k); return e ? e.value : null; });
  AR3.o.aoi = 'pakai'; AR3.o.simpan = false; AR3.o.lanjut = false; AR3.o.sb = false;
  if (bidang !== null) AR3.o.bidang = bidang;
  AR3.pil = {};
  var info = { arBusy: !!(window.AR && AR.busy), ar3Busy: !!AR3.busy, doms: ar3Doms().map(function (x) { return [x.d.name, x.adaPar, x.solid]; }) };
  var al = window.alert, psn = []; window.alert = function (m) { psn.push(String(m)); };
  try { ar3Run(); } finally { window.alert = al; }
  if (!AR3.log) return { kom: {}, pulih: true, info: info, pesan: psn };
  await tunggu(function () { return AR3.log && AR3.log.selesai; }, 600000);
  var a1 = SEC.map(function (k) { var e = document.getElementById(k); return e ? e.value : null; });
  var o = {};
  AR3.log.baris.forEach(function (b) { var m = String(b.hasil || '').replace(/<[^>]+>/g, ' ').match(/([\d.]+)\s+komposit/); if (m) o[b.nama] = [+m[1].replace(/\./g, ''), b.verdikt, /Sayatan di bidang domain/.test(b.ket || '')]; });
  try { ar3Close(); } catch (e) {}
  return { kom: o, pulih: JSON.stringify(a0) === JSON.stringify(a1), a0: a0, a1: a1 };
})
"""

def jalan(html, bidang):
    port = str(random.randint(9100, 9899)); d = Path(tempfile.mkdtemp()); (d / "index.html").write_bytes(html)
    (d / "data-latihan").symlink_to(DATA)
    srv = subprocess.Popen([sys.executable, "-m", "http.server", port], cwd=str(d), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    P = "http://localhost:%s/index.html" % port
    for _ in range(50):
        try: urllib.request.urlopen(P, timeout=1); break
        except Exception: time.sleep(.4)
    err = []
    with sync_playwright() as pw:
        ctx = pw.chromium.launch_persistent_context(tempfile.mkdtemp(), args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader"], viewport={"width": 1600, "height": 950})
        ctx.add_init_script("window.showDirectoryPicker=async function(){throw new Error('batal');};")
        pg = ctx.new_page(); pg.on("dialog", lambda x: x.accept(x.default_value) if x.type == "prompt" else x.accept())
        pg.on("pageerror", lambda e: err.append(str(e)[:300]))
        pg.goto(P); pg.wait_for_timeout(1500); pg.wait_for_function("window.DLAT && DLAT.siap", timeout=90000)
        pg.evaluate("document.getElementById('dlatBtn').click()"); pg.wait_for_timeout(3000)
        pg.wait_for_function("!DLAT.busy", timeout=900000); pg.wait_for_timeout(2500)
        pg.wait_for_function("!(window.AR&&AR.busy)", timeout=600000); pg.wait_for_timeout(1000)
        r = pg.evaluate(JS, bidang); print({k: r.get(k) for k in ('info', 'pesan')}, flush=True)
        ctx.close()
    srv.terminate(); r["pageerror"] = err; return r


lama = jalan(subprocess.check_output(["git", "-C", str(ROOT), "show", DASAR + ":app-dh/index.html"]), None)
baru = jalan((ROOT / "app-dh/index.html").read_bytes(), True)
mati = jalan((ROOT / "app-dh/index.html").read_bytes(), False)
print("lama :", json.dumps(lama["kom"], ensure_ascii=False))
print("baru :", json.dumps(baru["kom"], ensure_ascii=False))
print("mati :", json.dumps(mati["kom"], ensure_ascii=False))
salah = []
if not lama["kom"]: salah.append("build lama tidak menghasilkan baris komposit -> uji tidak membuktikan")
naik = 0
for k, v in lama["kom"].items():
    b = baru["kom"].get(k)
    if not b: salah.append("domain %s hilang di build baru" % k); continue
    if b[0] < v[0]: salah.append("%s: komposit turun %s -> %s" % (k, v[0], b[0]))
    if b[0] > v[0]: naik += 1
    if not b[2]: salah.append("%s: laporan tidak menyebut sayatan di bidang domain" % k)
    m = mati["kom"].get(k)
    if not m or m[0] != v[0] or m[1] != v[1]: salah.append("%s: opsi mati tidak sama dengan perilaku lama (%s vs %s)" % (k, m, v))
if not naik: salah.append("tidak ada domain yang komposit-nya bertambah -> uji tidak membuktikan")
if not baru["pulih"]: salah.append("sayatan pemakai tidak dikembalikan: %s -> %s" % (baru["a0"], baru["a1"]))
for n, r in (("lama", lama), ("baru", baru), ("mati", mati)):
    if r["pageerror"]: salah.append("galat halaman %s: %s" % (n, r["pageerror"][:2]))
print("\nGAGAL:\n  " + "\n  ".join(salah) if salah else "\nLULUS")
sys.exit(1 if salah else 0)
