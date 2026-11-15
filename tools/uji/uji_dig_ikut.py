"""Uji BM 0.24.89 (data latihan + poligon sintetis).
  K1 garis yang sedang didigit (kanvas oranye) ikut digambar ulang SELAMA plan 2D digeser (tombol mouse masih ditekan) dan
     posisinya cocok dengan gambar blok; dulu baru disegarkan sesudah geser selesai.
  K2 warna garis ganda (flag): garis ganda = warna aturan flag, garis asli tetap warna kadar; ganti warna aturan -> garis ganda
     ikut; mode "Sama dengan garis asli" = cara lama; dbApplySN tidak menimpa warna flag; layout PDF memakai warna flag.
  K3 DXF ekspor lengkap: ada TABLES > LAYER untuk tiap layer, $EXTMIN / $EXTMAX, BLOCKS, entitas tidak berubah.
Pemakaian: python tools/uji/uji_dig_ikut.py [app/index.html]   (build 0.24.88 harus GAGAL)"""
from __future__ import annotations
import json, random, shutil, subprocess, sys, tempfile, time
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
HTML = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "app" / "index.html"
PORT = random.randint(8900, 8990)
SET = r"""async function(){var w=function(t){return new Promise(function(r){setTimeout(r,t);});},m=BX.m,zc=m.z[Math.floor(m.n/2)],R={};
  if(!window.afWarna||!window.dxfLengkap)return {lama:1};
  lySet('fh',1.5);lyU().bot='';lySet('top',zc+0.75);lyApply();await w(2500);
  var ix=[];for(var i=0;i<m.n&&ix.length<400;i++){if(Math.abs(m.z[i]-zc)<1e-6)ix.push(i);}var i0=ix[Math.floor(ix.length/2)],x0=m.x[i0]-m.sx[i0]/2-offX,y0=m.y[i0]-m.sy[i0]/2-offY,s=m.sx[i0],B=lyBench();
  DG.S.length=0;DG.S.push(dbTag({no:17,d:'HG',id:'p1',closed:true,vis:true,col:'#ff0000',pts:[[x0,y0,zc],[x0+s*6,y0,zc],[x0+s*6,y0+s*4,zc],[x0,y0+s*4,zc]]}));
  /* K2 */
  var U=dbU(),A=Object.keys(m.num)[0];U.af=[{n:'Uji Flag',k:'num',a:A,op:'>=',c:-1e9,on:true,col:'#0000ff'}];U.sfOn=true;U.sfOff=0.5;U.sfCol='flag';LY.cache=null;
  var r1=dbInner(true),inn=function(){return DG.S.filter(function(q){return q.inner;})[0];},par=function(){return DG.S.filter(function(q){return q.id==='p1';})[0];},a=inn();
  R.k2={made:r1.n,inner:a&&a.col,fl:a&&a.fl,parent:par().col};
  afSet(0,'col','#00aa00');R.k2.ganti=inn().col;dbApplySN();R.k2.sn=inn().col;R.k2.parentSN=par().col;
  var pg=lyBuild(),ln=[];(pg||[]).forEach(function(p){p.ops.forEach(function(o){if(o.t==='line'&&o.dash&&o.col==='#00aa00')ln.push(1);});});R.k2.pdf=ln.length;
  U.sfCol='kadar';afWarnaSemua();R.k2.kadar=inn().col===par().col&&!inn().fcol;U.sfCol='flag';afWarnaSemua();R.k2.balik=inn().col;
  dbPanel&&0;
  /* K3 */
  var r=['0','SECTION','2','HEADER','9','$ACADVER','1','AC1009','0','ENDSEC','0','SECTION','2','ENTITIES','0','POLYLINE','8','17','62','1','66','1','70','9','10','0.0','20','0.0','30','0.0','0','VERTEX','8','17','10','500.5','20','900.25','30','228.0','70','32','0','VERTEX','8','17','10','510.5','20','910.25','30','229.0','70','32','0','SEQEND','8','17','0','POLYLINE','8','14','62','90','66','1','70','9','10','0.0','20','0.0','30','0.0','0','VERTEX','8','14','10','490','20','880','30','228.0','70','32','0','SEQEND','8','14','0','ENDSEC','0','EOF'],o=dxfLengkap(r),t=o.join('\n');
  R.k3={tables:/\nTABLES\n0\nTABLE\n2\nLTYPE/.test(t),l17:/\nLAYER\n2\n17\n70\n0\n62\n1\n6\nCONTINUOUS/.test(t),l14:/\nLAYER\n2\n14\n70\n0\n62\n90\n/.test(t),ext:/\$EXTMIN\n10\n490\.000\n20\n880\.000\n30\n228\.000\n9\n\$EXTMAX\n10\n510\.500\n20\n910\.250\n30\n229\.000/.test(t),blocks:/\nBLOCKS\n0\nENDSEC\n0\nSECTION\n2\nENTITIES\n/.test(t),ent:o.slice(o.indexOf('ENTITIES')+1).join('|')===r.slice(r.indexOf('ENTITIES')+1).join('|'),eof:o[o.length-1]==='EOF'};
  /* K1: mulai mendigit, dua titik */
  DG.S=DG.S.filter(function(q){return !q.inner;});updatePlot();await w(1500);dgStart();await w(1500);DG.c2=[[x0+offX+s,y0+offY+s],[x0+offX+s*5,y0+offY+s*3]];DG.cur=[[x0+s,y0+s,zc],[x0+s*5,y0+s*3,zc]];dgDraw();
  var gd=document.getElementById('plotDiv'),r0=gd.getBoundingClientRect(),fl=gd._fullLayout;window.__n=0;var d0=window.dgDraw;window.dgDraw=function(){window.__n++;return d0.apply(this,arguments);};
  R.pt=[fl.xaxis.d2p(x0+offX+s*9)+fl.xaxis._offset+r0.left,fl.yaxis.d2p(y0+offY+s*7)+fl.yaxis._offset+r0.top];R.on=DG.on;R.v2d=VIEW2D;return R;}"""
MID = r"""function(){var gd=document.getElementById('plotDiv'),A=dgAx(),q=DG.c2[0],p=dgPx(A,q[0],q[1]),I=(gd.layout.images||[]).filter(function(i){return i.name==='bmimg';})[0],el=gd.querySelector('image'),b=el.getBoundingClientRect(),g=gd.getBoundingClientRect();
  return {n:window.__n,px:p[0],py:p[1],ex:b.left-g.left+(q[0]-I.x)/I.sizex*b.width,ey:b.top-g.top+(I.y-q[1])/I.sizey*b.height,xr:A.x.range[0]};}"""
def main() -> int:
    from playwright.sync_api import sync_playwright
    d = Path(tempfile.mkdtemp()); shutil.copy(HTML, d / "index.html"); (d / "data-latihan").symlink_to(ROOT / "docs" / "tutorial-gcex" / "data")
    srv = subprocess.Popen([sys.executable, "-m", "http.server", str(PORT)], cwd=str(d), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1.2); gagal = []; err = []
    def cek(ok, msg):
        print(("  ok   " if ok else "  GAGAL ") + msg)
        if not ok: gagal.append(msg)
    try:
        with sync_playwright() as pw:
            b = pw.chromium.launch(args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader"]); pg = b.new_page(viewport={"width": 1500, "height": 950})
            pg.on("dialog", lambda x: x.accept()); pg.on("pageerror", lambda e: err.append(str(e)))
            pg.goto("http://127.0.0.1:%d/index.html" % PORT)
            pg.wait_for_function("window.DLAT && DLAT.siap", timeout=60000); pg.evaluate("document.getElementById('dlatBtn').click()")
            pg.wait_for_function("window.BX && BX.m && BX.m.n>0", timeout=600000); pg.wait_for_function("!DLAT.busy", timeout=600000); pg.wait_for_timeout(3000)
            r = pg.evaluate("(%s)()" % SET)
            if not r.get("lama"):
                x, y = r["pt"]; m0 = pg.evaluate("(%s)()" % MID)
                pg.mouse.move(x, y); pg.mouse.down(); pg.mouse.move(x + 60, y + 30, steps=4); pg.mouse.move(x + 150, y + 80, steps=5); pg.wait_for_timeout(300)
                m1 = pg.evaluate("(%s)()" % MID); pg.mouse.up(); pg.wait_for_timeout(300)
            b.close()
    finally:
        srv.terminate()
    if r.get("lama"):
        print("GAGAL: build lama (afWarna / dxfLengkap tidak ada)"); return 1
    print(json.dumps(r)[:900]); print(json.dumps(m0), json.dumps(m1))
    geser = abs(m1["xr"] - m0["xr"])
    cek(r["on"] and r["v2d"] and geser > 1, "K1 plan benar-benar bergeser selama tombol ditekan (%.1f m)" % geser)
    cek(m1["n"] > m0["n"], "K1 kanvas digit digambar ulang selama geser (%s kali)" % (m1["n"] - m0["n"]))
    cek(abs(m1["px"] - m1["ex"]) < 1.5 and abs(m1["py"] - m1["ey"]) < 1.5, "K1 posisi titik digit = posisi di gambar blok saat geser (selisih %.2f, %.2f px)" % (m1["px"] - m1["ex"], m1["py"] - m1["ey"]))
    k2 = r["k2"]
    cek(k2["made"] == 1 and k2["inner"] == "#0000ff" and k2["fl"] == "Uji Flag" and k2["parent"] == "#ff0000", "K2 garis ganda berwarna flag, garis asli tetap warna kadar %s" % k2)
    cek(k2["ganti"] == "#00aa00" and k2["sn"] == "#00aa00" and k2["pdf"] >= 1 and k2["kadar"] and k2["balik"] == "#00aa00", "K2 ganti warna aturan / dbApplySN / PDF / mode kadar")
    k3 = r["k3"]
    cek(all(k3.values()), "K3 DXF lengkap: TABLES + LAYER 17 & 14 + EXTMIN/EXTMAX + BLOCKS, entitas sama %s" % k3)
    cek(not err, "tanpa error halaman %s" % err[:3])
    print("GAGAL (%d)" % len(gagal) if gagal else "LULUS"); return 1 if gagal else 0
if __name__ == "__main__":
    sys.exit(main())
