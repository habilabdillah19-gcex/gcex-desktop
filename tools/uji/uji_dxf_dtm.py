"""Uji BM 0.24.83 — DXF 3DFACE dipakai sebagai DTM asli + batas blok saat .mdl besar dibaca langsung (data sintetis).
  D1 pembaca garis TIDAK menyederhanakan segitiga 3DFACE (toleransi 0,5 m): semua segitiga utuh.
  D2 TIN.soup mengenali DTM; TIN.rapat tidak merapatkan; TIN.build memakai segitiga asli (jumlah sama dengan file).
  D3 TINZ.of: Z di titik berat tiap segitiga = Z bidang segitiga itu (<= 1 mm), termasuk dinding jenjang curam.
  D4 string biasa (bukan segitiga) tetap lewat jalur lama (soup = null).
  D5 .mdl besar + filter pit: blok lolos filter > batas -> hanya bagian TERATAS yang dimuat (sedikitnya satu pias RL), ada pesan
     rentang berikutnya, dan isinya sama dengan bacaan tanpa batas untuk rentang RL itu.
  D6 (0.24.84) Ringkasan per RL atas SELURUH file dengan batas di dalam pit / di bawah topografi dihitung sambil membaca
     (blok tidak disimpan): sama dengan hitungan langsung dari semua blok; tanpa batas = bsLocal.
Pemakaian: python tools/uji/uji_dxf_dtm.py [app/index.html]   (build 0.24.82 harus GAGAL)
"""
from __future__ import annotations
import json, math, random, shutil, subprocess, sys, tempfile, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HTML = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "app" / "index.html"
PORT = random.randint(8900, 8990)
sys.path.insert(0, str(ROOT / "backend" / "tests"))


def dxf_pit(p: Path) -> int:
    """Pit kerucut berjenjang fiktif: cincin crest/toe tiap 5 m, dinding 70 derajat, 3DFACE antar-cincin."""
    cx, cy, seg, rings, r, z = 1000.0, 2000.0, 36, [], 60.0, 100.0
    for b in range(5):
        rings.append((r, z)); r -= 5 / math.tan(math.radians(70)); z -= 5; rings.append((r, z)); r -= 4
    pt = lambda rr, zz, k: (cx + rr * math.cos(2 * math.pi * k / seg), cy + rr * math.sin(2 * math.pi * k / seg), zz)
    L, n = ["0", "SECTION", "2", "ENTITIES"], 0
    def face(a, b, c):
        nonlocal n; n += 1; L.extend(["0", "3DFACE", "8", "PIT"])
        for i, q in enumerate((a, b, c, c)): L.extend([str(10 + i), "%.3f" % q[0], str(20 + i), "%.3f" % q[1], str(30 + i), "%.3f" % q[2]])
    for (r0, z0), (r1, z1) in zip(rings, rings[1:]):
        for k in range(seg):
            a, b, c, d = pt(r0, z0, k), pt(r0, z0, k + 1), pt(r1, z1, k + 1), pt(r1, z1, k); face(a, b, c); face(a, c, d)
    L.extend(["0", "ENDSEC", "0", "EOF"]); p.write_text("\n".join(L) + "\n"); return n


JS = r"""async function(nF){var R={},fs=document.getElementById('__f').files,out=[];
  if(!(window.TIN&&TIN.soup))return {lama:1};
  var r=await SA.readLinesInto({f:fs[0],k:'dxf',role:'pit'},out,0.5,null,null),src={x:[],y:[],z:[]},len=0,h4=0,hx=0;
  out.forEach(function(p){if(p===null){if(len===4)h4++;else if(len)hx++;len=0;src.x.push(null);src.y.push(null);src.z.push(null);}else{len++;src.x.push(p[0]);src.y.push(p[1]);src.z.push(p[2]);}});
  R.d1={tri:h4,lain:hx};var sp=TIN.soup(src);R.d2={soup:sp?sp.segitiga:0,rapat:TIN.rapat(src,2)===src,build:(TIN.build(src)||{}).segitiga,flag:(TIN.build(src)||{}).soup};
  var tn=TINZ.of(src,false),bad=0,hit=0,mx=0;for(var q=0;sp&&q<sp.i.length;q++){var a=sp.i[q],b=sp.j[q],c=sp.k[q],x=(sp.x[a]+sp.x[b]+sp.x[c])/3,y=(sp.y[a]+sp.y[b]+sp.y[c])/3,z=(sp.z[a]+sp.z[b]+sp.z[c])/3,v=tn.f(x,y);
    if(v==null){bad++;continue;}hit++;var d=Math.abs(v-z);if(d>mx)mx=d;if(d>0.001)bad++;}R.d3={hit:hit,bad:bad,maks:mx};
  var g=SA.surfGrid(out,'crest');var ga=5*Math.PI/180,gz=g?SA.surfAt(g,1000+59.09*Math.cos(ga),2000+59.09*Math.sin(ga)):NaN;R.d3.gz=gz;R.d3.grid=Math.abs(gz-97.5)<0.8&&isNaN(SA.surfAt(g,1000+200,2000));
  var ln={x:[],y:[],z:[]};for(var s=0;s<40;s++){for(var k=0;k<12;k++){ln.x.push(k*5);ln.y.push(s*3);ln.z.push(100+k);}ln.x.push(null);ln.y.push(null);ln.z.push(null);}R.d4=TIN.soup(ln)===null;
  /* D5 */
  var f=fs[1],H=await SA.mdlHead(f),pit={x0:H.origin[0]-10,y0:H.origin[1]-10,c:200,nx:1,ny:1,z:new Float32Array([H.origin[2]-5])},D0=window.gcexDesktop,B0=SA.MDL_BIG_MB,M0=SA.mdlMaxBlk;
  window.gcexDesktop={api:async function(){throw new Error('stub');},apiBin:async function(){throw new Error('stub');},pathOf:function(){return '';}};SA.MDL_BIG_MB=0.0001;
  try{SA.mdlMaxBlk=function(){return 1e9;};var A=await SA.readMDL(f,null,{head:H,pit:pit});SA.mdlMaxBlk=function(){return 400;};var B=await SA.readMDL(f,null,{head:H,pit:pit});
    var zc=1e9;for(var i=0;i<B.n;i++){var t=B.z[i]+B.sz[i]/2;if(t<zc)zc=t;}var m=/RL ([0-9.]+) /.exec(B.warn||''),cut=m?+m[1]:NaN,nA=0;for(i=0;i<A.n;i++)if(A.z[i]+A.sz[i]/2>cut)nA++;
    R.d5={all:A.n,n:B.n,warn:B.warn||'',cut:cut,minTop:zc,nA:nA,warnA:A.warn||''};}catch(e){R.d5={err:String(e)};}
  window.gcexDesktop=D0;SA.MDL_BIG_MB=B0;SA.mdlMaxBlk=M0;
  /* D6: ringkasan seluruh file dengan batas pit / topografi (streaming) = hitung langsung dari semua blok */
  try{var Afull=await SA.readMDLraw(f,null,{head:H}),m0=BX.m,u0=BX.ui.sgCol,tz0=TP.zf,fl0=SA.mdlFileLast,S={bench:10,ref:0,cut:'',cutA:'au'};
    var zP=function(x,y){return x+offX>H.origin[0]+70?null:100+0.2*(y+offY-H.origin[1]);},zT=function(x,y){return 150+0.1*(x+offX-H.origin[0]);};
    BX.m=Afull;BX.ui.sgCol=null;SA.mdlFileLast=f;TP.zf=function(k){return k==='ov:pit'?zP:zT;};var pF0=OV.pitF,tF0=OV.topoF,dm={x:[0,1,2],y:[0,1,0],z:[0,0,0]};OV.pitF=dm;OV.topoF=dm;
    var L0=bsLocal(S,['au']),S0=await bsStream(S,['au'],{pit:false,topo:false}),S1=await bsStream(S,['au'],{pit:true,topo:true}),S2=await bsStream({bench:10,ref:0,cut:'1',cutA:'au'},['au'],{pit:true,topo:false});
    var eN=0,eV=0,eT=0,eG=0,eW=0,eN2=0;for(i=0;i<Afull.n;i++){var x=Afull.x[i]-offX,y=Afull.y[i]-offY,z=Afull.z[i],zp=zP(x,y),v=Afull.sx[i]*Afull.sy[i]*Afull.sz[i],t=v*bxSGv(undefined),au=Afull.num.au[i];
      if(zp!=null&&z>=zp){if(au>=1)eN2++;if(z<=zT(x,y)){eN++;eV+=v;eT+=t;eG+=au*t;eW+=t;}}}
    R.d6={same0:L0.total.n===S0.total.n&&Math.abs(L0.total.ton-S0.total.ton)<1e-6&&L0.rows.length===S0.rows.length&&Math.abs(L0.total.grade.au-S0.total.grade.au)<1e-9,
      n:[S1.total.n,eN],vol:[S1.total.vol,eV],ton:[S1.total.ton,eT],au:[S1.total.grade.au,eG/eW],cutN:[S2.total.n,eN2],sub:eN>0&&eN<Afull.n,con:S1.con,nModel:S1.n_model};
    BX.m=m0;BX.ui.sgCol=u0;TP.zf=tz0;SA.mdlFileLast=fl0;OV.pitF=pF0;OV.topoF=tF0;}catch(e){R.d6={err:String(e&&e.stack||e)};}
  return R;}"""


def main() -> int:
    from playwright.sync_api import sync_playwright
    from test_mdl_io import make_mdl
    d = Path(tempfile.mkdtemp()); shutil.copy(HTML, d / "index.html"); (d / "data-latihan").symlink_to(ROOT / "docs" / "tutorial-gcex" / "data")
    nF = dxf_pit(d / "pit_uji.dxf"); make_mdl(d / "uji.mdl", n=3000)
    srv = subprocess.Popen([sys.executable, "-m", "http.server", str(PORT)], cwd=str(d), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(1.2); gagal = []; err = []
    def cek(ok, msg):
        print(("  ok   " if ok else "  GAGAL ") + msg)
        if not ok: gagal.append(msg)
    try:
        with sync_playwright() as pw:
            b = pw.chromium.launch(args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader"])
            pg = b.new_page(viewport={"width": 1440, "height": 900}); pg.on("dialog", lambda x: x.accept()); pg.on("pageerror", lambda e: err.append(str(e)))
            pg.goto("http://127.0.0.1:%d/index.html" % PORT)
            pg.wait_for_function("window.DLAT && DLAT.siap", timeout=60000); pg.evaluate("document.getElementById('dlatBtn').click()")
            pg.wait_for_function("window.BX && BX.m && BX.m.n>0", timeout=600000); pg.wait_for_function("!DLAT.busy", timeout=600000); pg.wait_for_timeout(3000)
            pg.evaluate("var i=document.createElement('input');i.type='file';i.multiple=true;i.id='__f';document.body.appendChild(i)")
            pg.set_input_files("#__f", [str(d / "pit_uji.dxf"), str(d / "uji.mdl")])
            r = pg.evaluate("(%s)(%d)" % (JS, nF)); b.close()
    finally:
        srv.terminate()
    print(json.dumps(r, ensure_ascii=False)[:1200])
    if r.get("lama"):
        print("GAGAL: TIN.soup tidak ada (build lama)"); return 1
    cek(r["d1"]["tri"] == nF and r["d1"]["lain"] == 0, "D1 %d segitiga 3DFACE utuh sesudah penyederhanaan 0,5 m %s" % (nF, r["d1"]))
    cek(r["d2"]["soup"] == nF and r["d2"]["rapat"] and r["d2"]["build"] == nF and r["d2"]["flag"] == 1, "D2 DTM dikenali, tidak dirapatkan, tampilan memakai segitiga asli %s" % r["d2"])
    cek(r["d3"]["hit"] == nF and r["d3"]["bad"] == 0 and r["d3"]["grid"], "D3 Z hitungan = bidang segitiga asli (maks %.2e m); grid filter import benar" % r["d3"]["maks"])
    cek(r["d4"], "D4 string biasa tidak dianggap DTM")
    d5 = r["d5"]
    cek("err" not in d5 and d5["all"] == 3000 and not d5["warnA"], "D5 tanpa kelebihan: semua blok dimuat, tanpa pesan %s" % {k: v for k, v in d5.items() if k != "warn"})
    cek("err" not in d5 and 0 < d5["n"] == d5["nA"] and d5["minTop"] > d5["cut"] and "Rentang berikutnya" in d5["warn"] and "3,000" in d5["warn"].replace(".", ","),
        "D5 batas 400 blok: dimuat %s blok teratas (RL > %s), sama dengan bacaan penuh; pesan: %s" % (d5.get("n"), d5.get("cut"), d5.get("warn", "")[:160]))
    d6 = r["d6"]
    cek("err" not in d6 and d6["same0"], "D6 tanpa batas: hasil streaming = hitungan dari model yang dimuat %s" % d6.get("err", ""))
    cek("err" not in d6 and d6["sub"] and d6["n"][0] == d6["n"][1] and abs(d6["vol"][0] - d6["vol"][1]) < 1e-6 and abs(d6["ton"][0] - d6["ton"][1]) < 1e-6
        and abs(d6["au"][0] - d6["au"][1]) < 1e-9 and d6["nModel"] == 3000, "D6 di dalam pit + di bawah topografi (titik tengah): blok %s, ton %s, kadar %s" % (d6.get("n"), d6.get("ton"), d6.get("au")))
    cek("err" not in d6 and d6["cutN"][0] == d6["cutN"][1] and "cara Surpac" in d6["con"], "D6 cut-off + di dalam pit: %s blok; keterangan: %s" % (d6.get("cutN"), d6.get("con")))
    cek(not err, "tanpa error halaman %s" % err[:3])
    print("GAGAL (%d)" % len(gagal) if gagal else "LULUS")
    return 1 if gagal else 0


if __name__ == "__main__":
    sys.exit(main())
