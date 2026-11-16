# -*- coding: utf-8 -*-
"""BM 0.24.91 / DH 0.25.0: tombol material popup string dari tabel kelas kadar + skala di setiap jendela 2D & 3D.
  K1 pengaturan proyek LAMA tetap terbaca: aturan LG 0.5-1 -> 14 (hijau tua), HG >= 1 -> 17, warna digit manual WS -> 1 (U.sn)
     menjadi tombol LG·14, HG·17, WS·1 di popup string (tanpa HG·17 / LG·14 bawaan yang tertanam).
  K2 klik tombol kelas: string number, warna DAN material terisi (string dalam ikut nomor & warna).
  K3 "＋ Kelas…" membuka Dig Block › Otomatis, tabel kelas kadar tersorot.
  K4 tambah kelas SG·18 -> tombol baru; hapus kelas LG -> tombol LG hilang.
  K5 Simpan sebagai standar -> ubah -> Pakai standar = kembali.
  K6 nomor string impor -> material dari tabel kelas (dbKelasN).
  S1 3D: kotak skala tampil ("Skala ≈ 1 : N", di pusat pandangan); px/m cocok dengan proyeksi anotasi Plotly (≤ 3 %).
  S2 2D denah: skala tampil, 1 : N sesuai rentang sumbu x / lebar plot.
  S3 penampang dengan eksagerasi vertikal: keterangan "VE n×".
  S4 grafik non-spasial (histogram Reporting) tanpa skala; sakelar SKL.set(false) menyembunyikan.
  S5 Drillhole: 3D & peta 2D ber-skala.
Pemakaian: python tools/uji/uji_kelas_skala.py [png_popup] [png_2d]"""
import random, subprocess, sys, tempfile, time, json
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT = Path(__file__).resolve().parents[2]
gagal = []
def cek(ok, pesan):
    print(("  ok   " if ok else "  GAGAL ") + pesan)
    if not ok: gagal.append(pesan)
def serve(app):
    d = Path(tempfile.mkdtemp()); (d / "index.html").write_bytes((ROOT / app / "index.html").read_bytes()); (d / "data-latihan").symlink_to(ROOT / "docs/tutorial-gcex/data")
    p = random.randint(9400, 9899); s = subprocess.Popen([sys.executable, "-m", "http.server", str(p)], cwd=str(d), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1.2)
    return s, "http://127.0.0.1:%d/index.html" % p
POP = """()=>{var b=[].map.call(document.querySelectorAll('#dbPop .dpb button.dpk'),function(x){return x.textContent.replace(/\\s+/g,' ').trim();});return b;}"""
with sync_playwright() as pw:
    br = pw.chromium.launch(args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader"])
    srv, U = serve("app"); pg = br.new_page(viewport={"width": 1500, "height": 950}); ERR = []
    pg.on("dialog", lambda x: x.accept()); pg.on("pageerror", lambda e: ERR.append(str(e)[:300]))
    pg.goto(U); pg.wait_for_function("window.DLAT && DLAT.siap", timeout=60000); pg.evaluate("document.getElementById('dlatBtn').click()")
    pg.wait_for_function("window.BX && BX.m && window.SKL", timeout=600000); pg.wait_for_timeout(5000)
    # ---------- K1 pengaturan lama ----------
    pg.evaluate("""()=>{var u=dbU();u.rules=[{lo:0.5,hi:1,n:14,c:'#2b8a3e',m:'LG'},{lo:1,hi:'',n:17,c:'#ff1a1a',m:'HG'}];u.sn={HG:{n:17,c:'#ff1a1a'},LG:{n:14,c:'#7ee04a'},WS:{n:1,c:'#9aa3ad'}};
      var p=[[0,0,0],[20,0,0],[20,20,0],[0,20,0]];var o={id:'tK',pts:p,closed:true,vis:true,no:5,col:'#ffd400',d:'X',name:'uji'};DG.S.push(o);DG.S.push({id:'tKi',pts:p,closed:true,vis:true,no:5,col:'#ffd400',inner:true,parent:'tK'});window.__ki=DG.S.length-2;dbPop(__ki,300,300);}""")
    b1 = pg.evaluate(POP)
    cek(b1 == ["LG · 14", "HG · 17", "WS · 1"], "K1 pengaturan lama terbaca -> tombol %s" % b1)
    if len(sys.argv) > 1: pg.screenshot(path=sys.argv[1], clip={"x": 290, "y": 290, "width": 290, "height": 330})
    # ---------- K2 ----------
    pg.evaluate("dbStrKelas(__ki,0)"); k2 = pg.evaluate("[DG.S[__ki].no,DG.S[__ki].col,DG.S[__ki].d,DG.S[__ki+1].no,DG.S[__ki+1].col]")
    cek(k2 == [14, "#2b8a3e", "LG", 14, "#2b8a3e"], "K2 klik LG·14: nomor, warna, material + string dalam %s" % k2)
    cek(pg.evaluate("document.querySelector('#dbPop .dpk.on')&&document.querySelector('#dbPop .dpk.on').textContent.indexOf('LG')>=0"), "K2 tombol kelas aktif disorot")
    # ---------- K3 ----------
    pg.evaluate("dbKelasBuka()"); pg.wait_for_timeout(1200)
    cek(pg.evaluate("!!document.querySelector('#dbBody .dbrt') && document.querySelector('#dbBody .dbrt').offsetParent!==null && document.getElementById('dbPop').style.display==='none'"), "K3 ＋ Kelas… membuka tabel kelas kadar")
    # ---------- K4 ----------
    pg.evaluate("dbRAdd();var R=dbU().rules,k=R.length-1;dbRSet(k,'m','SG');dbRSet(k,'c','#c2185b');dbRSet(k,'n','18');dbPop(__ki,300,300)")
    b4 = pg.evaluate(POP)
    pg.evaluate("dbRDel(0);dbPop(__ki,300,300)"); b4b = pg.evaluate(POP)
    cek("SG · 18" in b4 and "LG · 14" not in b4b and "SG · 18" in b4b and "WS · 1" in b4b, "K4 tambah SG·18 %s; hapus LG -> %s" % (b4, b4b))
    # ---------- K5 ----------
    pg.evaluate("dbStdSave();var u=dbU();u.rules=[{lo:2,hi:'',n:9,c:'#000000',m:'ZZ'}];u.sn={};dbStdUse();dbPop(__ki,300,300)"); b5 = pg.evaluate(POP)
    cek(b5 == b4b, "K5 standar disimpan & dipakai lagi: %s" % b5)
    k6 = pg.evaluate("[dbKelasN(18)&&dbKelasN(18).m, dbKelasN(1)&&dbKelasN(1).m, dbKelasN(77)]")
    cek(k6 == ["SG", "WS", None], "K6 nomor -> material: %s" % k6)
    pg.evaluate("dbPopClose();DG.S=DG.S.filter(function(s){return s.id!=='tK'&&s.id!=='tKi';});dgSave&&dgSave();")
    # ---------- S1 3D ----------
    if pg.evaluate("typeof VIEW2D!=='undefined'&&VIEW2D"): pg.evaluate("toggle2D()"); pg.wait_for_timeout(2500)
    pg.evaluate("Plotly.relayout('plotDiv',{'scene.camera':{eye:{x:0,y:0,z:1.8},up:{x:0,y:1,z:0},center:{x:0,y:0,z:0}}})"); pg.wait_for_timeout(1500)
    s1 = pg.evaluate("""()=>{var gd=document.getElementById('plotDiv'),b=gd.querySelector('.gxSkala'),I=SKL.info(gd);return {t:b&&b.offsetParent!==null?b.innerText.replace(/\\n/g,' | '):null,ppm:I&&1/I.mpp};}""")
    # pembanding: proyeksi anotasi Plotly di pusat rentang
    ref = pg.evaluate("""async()=>{var gd=document.getElementById('plotDiv'),fl=gd._fullLayout.scene,r=[fl.xaxis.range,fl.yaxis.range,fl.zaxis.range],m=r.map(function(a){return (a[0]+a[1])/2;}),L=(r[0][1]-r[0][0])*0.1;
      await Plotly.relayout(gd,{'scene.annotations':[{x:m[0]-L/2,y:m[1],z:m[2],text:'A',showarrow:false},{x:m[0]+L/2,y:m[1],z:m[2],text:'B',showarrow:false}]});await new Promise(function(r){setTimeout(r,700);});
      var t=[].map.call(gd.querySelectorAll('.annotation-text-g'),function(g){var q=g.getBoundingClientRect();return q.x+q.width/2;});var v=Math.abs(t[1]-t[0])/L;await Plotly.relayout(gd,{'scene.annotations':[]});return v;}""")
    cek(s1["t"] and "Skala" in s1["t"] and s1["ppm"] and abs(s1["ppm"] / ref - 1) < 0.03, "S1 3D: '%s'; px/m %.4f vs proyeksi Plotly %.4f" % (s1["t"], s1["ppm"] or 0, ref))
    # ---------- S2 2D denah ----------
    pg.evaluate("document.getElementById('sMode').value='H';modeChanged()"); pg.wait_for_timeout(800)
    pg.evaluate("toggle2D()"); pg.wait_for_timeout(3000)
    s2 = pg.evaluate("""()=>{var gd=document.getElementById('plotDiv'),b=gd.querySelector('.gxSkala'),xa=gd._fullLayout.xaxis,mpp=Math.abs(xa.range[1]-xa.range[0])/xa._length;return {t:b&&b.offsetParent!==null?b.innerText.replace(/\\n/g,' | '):null,r:Math.round(mpp*1000/(25.4/96)),bw:b?b.querySelector('.bar').offsetWidth:0,mpp:mpp};}""")
    import re
    n2 = int(re.sub(r"\D", "", ((s2["t"] or "").split("|")[0].split(":") + ["0"])[1]) or 0)
    m2 = re.search(r"\|\s*([\d.,]+) m", s2["t"] or ""); lm = float(m2.group(1).replace(".", "").replace(",", ".")) if m2 else 0
    cek(s2["t"] and abs(n2 / s2["r"] - 1) < 0.06 and abs(s2["bw"] * s2["mpp"] / lm - 1) < 0.05, "S2 2D denah: '%s'; rasio harap ~1:%s; batang %d px = %.1f m" % (s2["t"], s2["r"], s2["bw"], s2["bw"] * s2["mpp"]))
    if len(sys.argv) > 2: pg.screenshot(path=sys.argv[2])
    # ---------- S3 penampang ----------
    opts = pg.evaluate("[].map.call(document.getElementById('sMode').options,function(o){return o.value;})")
    vm = 'S'; pg.evaluate("document.getElementById('sMode').value='S';document.getElementById('slDip').value=90;document.getElementById('slAz').value=0;modeChanged()")
    pg.evaluate("var z=document.getElementById('zex');z.value=2;z.dispatchEvent(new Event('change',{bubbles:true}));z.dispatchEvent(new Event('input',{bubbles:true}));if(!VIEW2D)toggle2D();else updatePlot()"); pg.wait_for_timeout(3000)
    s3 = pg.evaluate("""()=>{var gd=document.getElementById('plotDiv'),b=gd.querySelector('.gxSkala');return {t:b&&b.offsetParent!==null?b.innerText.replace(/\\n/g,' | '):null,ve:gd.layout.yaxis?gd.layout.yaxis.scaleratio:null};}""")
    cek(s3["t"] and abs((s3["ve"] or 1) - 1) > 1e-6 and "VE" in s3["t"], "S3 penampang (%s, scaleratio %s): '%s'" % (vm, s3["ve"], s3["t"]))
    # ---------- S4 ----------
    s4 = pg.evaluate("""()=>{var n=0,sp=0;document.querySelectorAll('.js-plotly-plot').forEach(function(gd){if(gd.id==='plotDiv')return;n++;if(gd.querySelector('.gxSkala')&&gd.querySelector('.gxSkala').style.display!=='none')sp++;});SKL.set(false);var h=document.querySelector('#plotDiv .gxSkala').style.display;SKL.set(true);return [n,sp,h];}""")
    cek(s4[1] == 0 and s4[2] == "none", "S4 grafik lain (%d) tanpa skala; sakelar mati menyembunyikan" % s4[0])
    cek(not ERR, "BM tanpa galat halaman: %s" % ERR[:3])
    pg.close(); srv.terminate()
    # ---------- S5 Drillhole ----------
    srv, U = serve("app-dh"); pg = br.new_page(viewport={"width": 1500, "height": 950}); ERR = []
    pg.on("dialog", lambda x: x.accept()); pg.on("pageerror", lambda e: ERR.append(str(e)[:300]))
    pg.goto(U); pg.wait_for_function("window.DLAT && DLAT.siap", timeout=60000); pg.evaluate("document.getElementById('dlatBtn').click()")
    pg.wait_for_function("window.collars && collars.length>0 && window.SKL", timeout=600000); pg.wait_for_timeout(6000)
    d1 = pg.evaluate("(function(){var b=document.querySelector('#plotDiv .gxSkala');return b&&b.offsetParent!==null?b.innerText.replace(/\\n/g,' | '):null;})()")
    pg.evaluate("document.getElementById('sMode').value='H';modeChanged();toggle2D&&toggle2D()"); pg.wait_for_timeout(3000)
    d2 = pg.evaluate("(function(){var b=document.querySelector('#plotDiv .gxSkala');return b&&b.offsetParent!==null?b.innerText.replace(/\\n/g,' | '):null;})()")
    cek(d1 and "Skala" in d1 and d2 and "Skala" in d2, "S5 Drillhole 3D '%s' · 2D '%s'" % (d1, d2))
    cek(not ERR, "DH tanpa galat halaman: %s" % ERR[:3])
    srv.terminate(); br.close()
print("LULUS" if not gagal else "GAGAL: %s" % gagal)
sys.exit(1 if gagal else 0)
