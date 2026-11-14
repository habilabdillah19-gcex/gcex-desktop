"""Uji BM 0.24.87 — pengayaan lembar Layout & Plot PDF (layx_bm.js), data latihan + dig block sintetis.
  L1 panel: kotak "Pengayaan lembar" ada, sakelar induk + sakelar tiap bagian; tidak ada menu baru di luar panel Layout.
  L2 halaman gabungan: inset lokasi (kotak merah area lembar), kop lengkap (Dibuat / Diperiksa / Disetujui / Revisi /
     Koordinat / Sumber data), label di dalam dig block, elemen bertanda (north, bar, legend, inset).
  L3 halaman satu dig block: tabel koordinat patok memuat koordinat titik sudut yang benar.
  L4 gaya grid "Tanda +" / "Tepi saja": garis grid penuh hilang, diganti tanda.
  L5 catatan + panah: tampil di pratinjau & PDF; pegangan ujung panah hanya di pratinjau (tidak masuk PDF).
  L6 geser elemen: LX.move menggeser panah utara sejauh yang diminta; klik dua kali (LX.home) = posisi bawaan;
     seret sungguhan di pratinjau menggeser inset.
  L7 sakelar induk mati: lembar persis seperti tanpa modul (jumlah & isi operasi sama dengan lyPage asli, kop 34 mm).
  L8 PDF tetap terbentuk (%PDF, halaman sama banyak) dengan semua pengayaan.
Pemakaian: python tools/uji/uji_layx.py [app/index.html]   (build 0.24.86 harus GAGAL)
"""
from __future__ import annotations
import json, random, shutil, subprocess, sys, tempfile, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HTML = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "app" / "index.html"
PORT = random.randint(8900, 8990)

JS = r"""async function(){var R={},w=function(ms){return new Promise(function(r){setTimeout(r,ms);});};
  if(!window.LX)return {lama:1};
  var m=BX.m,e=m.ext,L=lyU(),zc=Math.round((e[4]+e[5])/2),cx=(e[0]+e[1])/2-offX,cy=(e[2]+e[3])/2-offY;
  L.top=String(zc+0.75);L.bot=String(zc-0.75);L.fh=1.5;L.mode='auto';L.gap=3;L.paper='A3';L.orient='L';L.sum=false;L.ortho=false;
  var sq=function(x,y,s,d,no){return {no:no,d:d,closed:true,vis:true,col:no===1?'#d93a2b':'#3fa64a',pts:[[x,y,zc],[x+s,y,zc],[x+s,y+s,zc],[x,y+s,zc]]};};
  var S0=DG.S.slice();DG.S.length=0;DG.S.push(sq(cx-14,cy-6,12,'HG',1));DG.S.push(sq(cx-1,cy-6,12,'LG',2));DG.S.push(sq(cx+60,cy+40,10,'HG',3));
  if(!OV.pitF||!OV.pitF.x||!OV.pitF.x.length){var px=[],py=[],pz=[];for(var a=0;a<=40;a++){px.push((e[0]+e[1])/2-offX+90*Math.cos(a/40*6.2832));py.push((e[2]+e[3])/2-offY+70*Math.sin(a/40*6.2832));pz.push(zc);}OV.pitF={x:px,y:py,z:pz};R.pitBuatan=1;}
  L.lx=true;L.inset=true;L.kopX=true;L.lblIn=true;L.tKoord=true;L.drag=true;L.gridStyle='line';L.pos={};L.notes=[];L.by='Geolog A';L.chk='Geolog B';L.apr='Supt C';L.rev='2';L.crs='UTM uji';L.src='';
  /* L1 */
  uiTab&&0;lyPanel();var bx=$('lxBox');R.l1={box:!!bx,keys:bx?[].map.call(bx.querySelectorAll('[data-lx]'),function(x){return x.getAttribute('data-lx');}):[],add:!!$('lxNoteAdd'),dalamLy:!!(bx&&bx.closest('#lyBody'))};
  var txt=function(pg){return pg.ops.filter(function(p){return p.t==='text';}).map(function(p){return p.txt;});},els=function(pg){var o={};pg.ops.forEach(function(p){if(p.el)o[p.el]=(o[p.el]||0)+1;});return o;};
  /* L2/L3 */
  var P=lyBuild();R.nPage=P.length;var pg=P.filter(function(p){return p.ctx.grp;})[0],p1=P.filter(function(p){return !p.ctx.grp;})[0];
  var T=txt(pg);R.l2={grp:!!pg,tbh:pg.ctx.tbh,inset:T.some(function(t){return /^Lokasi lembar\s+1 : \d+/.test(t);}),merah:pg.ops.some(function(p){return p.el==='inset'&&p.t==='rect'&&p.stroke==='#c22a1c';}),
    kop:['Dibuat','Diperiksa','Disetujui','Geolog A','Geolog B','Supt C'].every(function(k){return T.indexOf(k)>=0;})&&T.some(function(t){return t==='Revisi  2';})&&T.some(function(t){return t==='Koordinat  UTM uji';})&&T.some(function(t){return /^Sumber data: BM /.test(t);}),
    lbl:T.filter(function(t){return /^(HG|LG) - /.test(t);}).length,ton:T.filter(function(t){return / t @ /.test(t);}).length,els:els(pg)};
  var T1=txt(p1),r=p1.ctx.items[0].r;R.l3={ada:T1.some(function(t){return /^Koordinat patok/.test(t);}),baris:r.every(function(q,i){return T1.some(function(t){return t.indexOf(q[0].toFixed(2))>=0&&t.indexOf(q[1].toFixed(2))>=0&&new RegExp('^\\s*'+(i+1)+'\\s').test(t);});}),el:els(p1).koord||0,grpTanpa:!txt(pg).some(function(t){return /^Koordinat patok/.test(t);})};
  /* L4 */
  var ng=function(pg){return pg.ops.filter(function(p){return p.g;}).length;},g0=ng(pg),n0=pg.ops.length;L.gridStyle='plus';var pgP=lyBuild().filter(function(p){return p.ctx.grp;})[0];L.gridStyle='edge';var pgE=lyBuild().filter(function(p){return p.ctx.grp;})[0];L.gridStyle='line';
  R.l4={garis:g0,plus:ng(pgP),edge:ng(pgE),nPlus:pgP.ops.length-n0+g0,nEdge:pgE.ops.length-n0+g0};
  /* L5 */
  LX.noteAdd();L.notes[0].txt='Awas batas waste';var P5=lyBuild(),pn=P5.filter(function(p){return txt(p).indexOf('Awas batas waste')>=0;})[0];
  R.l5={ada:!!pn,panah:pn?pn.ops.some(function(p){return p.t==='poly'&&p.el==='tip:0';}):false,pv:pn?pn.ops.filter(function(p){return p.pv;}).length:0,svg:pn?lySvg(pn).indexOf('data-el="note:0"')>0:false,baris:$('lxBox')?$('lxBox').querySelectorAll('[data-lxn]').length:0};
  var pdf5=lyPdf(P5),t5=await pdf5.text();R.l8={pdf:t5.slice(0,5),hal:(t5.match(/\/Type \/Page[^s]/g)||[]).length,nPage:P5.length,catatan:t5.indexOf('(Awas batas waste)')>0,size:pdf5.size};
  L.notes=[];
  /* L6 */
  lyPreview();await w(300);LY.pi=LY.pages.indexOf(LY.pages.filter(function(p){return p.ctx.grp;})[0]);lyShow();await w(200);
  var nx=function(){var o=LY.pages[LY.pi].ops.filter(function(p){return p.el==='north'&&p.t==='poly';})[0];return o.pts[0];},a0=nx();LX.move('north',-20,-15);await w(150);var a1=nx();LX.home('north');await w(150);var a2=nx();
  var svg=document.querySelector('#lyDlg .lyPg svg'),gi=svg.querySelector('[data-el="inset"]'),rb=gi.getBoundingClientRect(),ix0=LY.pages[LY.pi].ops.filter(function(p){return p.el==='inset';})[0].x;
  R.l6={geser:[+(a1[0]-a0[0]).toFixed(2),+(a1[1]-a0[1]).toFixed(2)],balik:Math.abs(a2[0]-a0[0])<1e-6&&Math.abs(a2[1]-a0[1])<1e-6,hint:!!document.querySelector('#lyDlg .lxh'),cur:gi.style.cursor,pt:[rb.left+rb.width/2,rb.top+6],ix0:ix0,mm:LY.pages[LY.pi].W/svg.getBoundingClientRect().width};
  R._drag=1;window.__lx={S0:S0};return R;}"""

JS2 = r"""async function(a){var R={},L=lyU(),w=function(ms){return new Promise(function(r){setTimeout(r,ms);});};await w(200);
  var ix1=LY.pages[LY.pi].ops.filter(function(p){return p.el==='inset';})[0].x;R.dx=+(ix1-a.ix0).toFixed(2);R.pos=L.pos.inset||null;
  /* L7: sakelar induk mati = lyPage asli */
  $('lyDlg').style.display='none';L.pos={};L.lx=false;var P=lyBuild(),pg=P.filter(function(p){return p.ctx.grp;})[0],T=pg.ops.filter(function(p){return p.t==='text';}).map(function(p){return p.txt;});
  R.l7={tbh:pg.ctx.tbh,inset:pg.ops.some(function(p){return p.el==='inset';}),kop:T.indexOf('Dibuat')>=0,lbl:T.some(function(t){return /^(HG|LG) - /.test(t);}),grid:pg.ops.filter(function(p){return p.g;}).length,koord:P.some(function(p){return p.ops.some(function(q){return q.el==='koord';});}),n:pg.ops.length};
  L.lx=true;L.inset=false;L.kopX=false;L.lblIn=false;L.tKoord=false;var P2=lyBuild(),pg2=P2.filter(function(p){return p.ctx.grp;})[0];R.l7.sama=pg2.ops.length===pg.ops.length&&pg2.ctx.tbh===34;
  lyPanel();R.l7.dis=!!$('lxBox');L.lx=false;LX.open=1;lyPanel();R.l7.dis=[].every.call($('lxBox').querySelectorAll('[data-lx]:not([data-lx="lx"])'),function(x){return x.disabled;});
  DG.S.length=0;window.__lx.S0.forEach(function(s){DG.S.push(s);});return R;}"""


def main() -> int:
    from playwright.sync_api import sync_playwright
    d = Path(tempfile.mkdtemp()); shutil.copy(HTML, d / "index.html"); (d / "data-latihan").symlink_to(ROOT / "docs" / "tutorial-gcex" / "data")
    srv = subprocess.Popen([sys.executable, "-m", "http.server", str(PORT)], cwd=str(d), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(1.2); gagal = []; err = []
    def cek(ok, msg):
        print(("  ok   " if ok else "  GAGAL ") + msg)
        if not ok: gagal.append(msg)
    try:
        with sync_playwright() as pw:
            b = pw.chromium.launch(args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader"])
            pg = b.new_page(viewport={"width": 1500, "height": 950}); pg.on("dialog", lambda x: x.accept()); pg.on("pageerror", lambda e: err.append(str(e)))
            pg.goto("http://127.0.0.1:%d/index.html" % PORT)
            pg.wait_for_function("window.DLAT && DLAT.siap", timeout=60000); pg.evaluate("document.getElementById('dlatBtn').click()")
            pg.wait_for_function("window.BX && BX.m && BX.m.n>0", timeout=600000); pg.wait_for_function("!DLAT.busy", timeout=600000); pg.wait_for_timeout(3000)
            r = pg.evaluate("(%s)()" % JS)
            if not r.get("lama"):
                x, y = r["l6"]["pt"]; pg.mouse.move(x, y); pg.mouse.down(); pg.mouse.move(x + 60, y + 40, steps=6); pg.mouse.up(); pg.wait_for_timeout(400)
                r2 = pg.evaluate("(%s)(%s)" % (JS2, json.dumps({"ix0": r["l6"]["ix0"]})))
            b.close()
    finally:
        srv.terminate()
    if r.get("lama"):
        print("GAGAL: modul LX tidak ada (build lama)"); return 1
    print(json.dumps(r, ensure_ascii=False)[:1500]); print(json.dumps(r2, ensure_ascii=False))
    l1 = r["l1"]
    cek(l1["box"] and l1["dalamLy"] and l1["add"] and all(k in l1["keys"] for k in ["lx", "inset", "kopX", "lblIn", "tKoord", "drag", "gridStyle", "insetSrc", "by", "chk", "apr", "rev", "crs", "src"]), "L1 kotak Pengayaan lembar di panel Layout, sakelar induk + per bagian")
    l2 = r["l2"]
    cek(l2["grp"] and l2["tbh"] == 54 and l2["inset"] and l2["merah"] and l2["kop"], "L2 halaman gabungan: inset lokasi + kotak merah, kop lengkap (54 mm) %s" % {k: l2[k] for k in ("tbh", "inset", "merah", "kop")})
    cek(l2["lbl"] == 2 and l2["ton"] >= 1 and all(l2["els"].get(k) for k in ("north", "bar", "inset")), "L2 label di dalam 2 dig block; elemen bertanda %s" % l2["els"])
    l3 = r["l3"]
    cek(l3["ada"] and l3["baris"] and l3["el"] > 4 and l3["grpTanpa"], "L3 tabel koordinat patok di halaman satu dig block, koordinat benar %s" % l3)
    l4 = r["l4"]
    cek(l4["garis"] > 4 and l4["plus"] == 0 and l4["edge"] == 0 and l4["nPlus"] > l4["nEdge"] > 0, "L4 gaya grid: garis %s -> tanda + (%s op) / tepi saja (%s op)" % (l4["garis"], l4["nPlus"], l4["nEdge"]))
    l5 = r["l5"]; l8 = r["l8"]
    cek(l5["ada"] and l5["panah"] and l5["pv"] == 1 and l5["svg"] and l5["baris"] == 1, "L5 catatan + panah di pratinjau; pegangan ujung panah khusus pratinjau %s" % l5)
    l6 = r["l6"]
    cek(l6["geser"] == [-20, -15] and l6["balik"] and l6["hint"] and l6["cur"] == "move", "L6 LX.move menggeser panah utara %s mm, klik dua kali kembali" % l6["geser"])
    ex = 60 * l6["mm"]
    cek(abs(r2["dx"] - ex) < 1.5 and r2["pos"], "L6 seret sungguhan di pratinjau: inset bergeser %.1f mm (harap %.1f)" % (r2["dx"], ex))
    l7 = r2["l7"]
    cek(l7["tbh"] == 34 and not l7["inset"] and not l7["kop"] and not l7["lbl"] and l7["grid"] > 4 and not l7["koord"] and l7["sama"] and l7["dis"], "L7 sakelar induk mati: lembar seperti semula (kop 34 mm, tanpa pengayaan) %s" % l7)
    cek(l8["pdf"] == "%PDF-" and l8["hal"] == l8["nPage"] and l8["catatan"], "L8 PDF terbentuk: %s halaman, %s KB, catatan ikut" % (l8["hal"], l8["size"] // 1024))
    cek(not err, "tanpa error halaman %s" % err[:3])
    print("GAGAL (%d)" % len(gagal) if gagal else "LULUS")
    return 1 if gagal else 0


if __name__ == "__main__":
    sys.exit(main())
