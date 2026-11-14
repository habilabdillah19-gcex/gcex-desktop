# -*- coding: utf-8 -*-
"""Block Model 0.24.78 / 0.24.79: shell ala Ore Works tahap 1 + 2 + tempel Properti (web-src/shell_bm.js, kompas 3D di gcex_base.html).

Keputusan pemilik 14 Nov 2026 (mockup disetujui): tidak boleh ada menu kembar; logo & huruf bilah atas tetap.
Memakai data latihan (fiktif).
  S1 toolbar #bmTb: alat tampilan DIPINDAH dari bilah atas (bilah atas tanpa .tools); tiap alat tepat satu kali di dokumen
     (Top/Front/Side/Iso, Tegak lurus, Slicer, Ortho, Lapisan, Gelap, PNG, Layar penuh); tombol tersembunyi tetap tersembunyi;
     logo .gcx tetap Arial Black.
  S2 "Semua data": kamera menjauh/mendekat -> kembali ke jarak bawaan dengan arah pandang yang sama.
  S3 Latar 3D: bawaan Polos (latar Plotly tidak transparan); Gradasi navy -> latar Plotly transparan + kelas #stage,
     label sumbu terang; kembali ke Polos.
  S4 status bar: koordinat kursor (E/N + offset proyek) dari plotly_hover, VE; info lama tetap (#secInfo, #rtime, #wmark);
     arah pandang TIDAK diulang (hanya di kompas).
  S5 kepala jendela pop-up & legenda navy.
  S6 (0.24.79) menu teks bilah atas dihapus; Properti tempel kiri / kanan / lepas (jendela), posisi diingat; tombol « hanya
     menyembunyikan Project Tree (Properti kiri tetap tampil), » memunculkannya.
  S7 cari di Project Tree: hanya baris yang cocok + induknya; dikosongkan -> folder kembali seperti semula.
  S8 kompas 3D: piringan miring (elips) & panah Z saat pandangan samping; dari atas: elips = lingkaran, Z = titik.
  S9 (0.24.81) .mdl >= 150 MB dengan filter pit/topografi dibaca langsung (tanpa backend); hanya filter RL -> backend.
  S10 (0.24.81) sayatan horizontal di luar RL block model yang baru dimuat dipindah ke tengah rentangnya.
  S11 (0.24.82) model .mdl besar yang dibaca langsung (filter pit/topografi) -> Ringkasan per RL tetap lewat backend atas
      seluruh file: cache dibangun dulu dengan progres, lalu /mdl/benches; gagal (disk penuh) -> kotak folder cache tampil.
  S13 (0.24.86) kamera 3D digerakkan: gambar ulang penuh hanya bila orthofoto tampil (dulu selalu -> jeda pada model besar).
  S12 (0.24.82) kotak folder cache: folder, terpakai, ruang bebas, tombol Ganti folder; hapus cache tetap satu pintu (Bantuan).
Pemakaian: python tools/uji/uji_shell_bm.py [app/index.html]   (build 0.24.78 harus GAGAL di S6)
"""
from __future__ import annotations
import random, shutil, subprocess, sys, tempfile, time, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HTML = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "app" / "index.html"
PORT = random.randint(8800, 8899)

JS = r"""async function(){
  var R={},$=function(i){return document.getElementById(i);},w=function(ms){return new Promise(function(r){setTimeout(r,ms);});};
  var tb=$('bmTb');R.s1={tb:!!tb,topTools:!!document.querySelector('#top .tools'),inTb:!!(tb&&tb.querySelector('.tools'))};
  var txt=function(re){return [].filter.call(document.querySelectorAll('button'),function(b){return re.test(b.textContent.trim());}).length;};
  R.s1.n={Top:txt(/^Top$/),Front:txt(/^Front$/),Side:txt(/^Side$/),Iso:txt(/^Iso$/),PNG:txt(/^PNG$/),tegak:txt(/Tegak lurus/),
    slicer:document.querySelectorAll('#btnSecM').length,ortho:document.querySelectorAll('#ortho').length,lyr:document.querySelectorAll('#lyrBtn').length,
    gelap:document.querySelectorAll('#darkMode').length,fs:document.querySelectorAll('#fsBtn').length,semua:document.querySelectorAll('#tbAll').length,latar:document.querySelectorAll('#tbBg').length};
  R.s1.inside=['btnSecM','ortho','lyrBtn','darkMode','fsBtn','tbAll','tbBg'].every(function(i){return $(i)&&tb.contains($(i));});
  var gs=$('gsBtn');R.s1.gsHidden=!gs||!gs.hidden||getComputedStyle(gs).display==='none';
  R.s1.logo=getComputedStyle(document.querySelector('#top .gcx')).fontFamily;
  /* S2 */
  var gd=$('plotDiv');setCam(0.5,-0.5,0.33);await w(700);var e0=gd._fullLayout.scene.camera.eye;$('tbAll').click();await w(900);var e1=gd._fullLayout.scene.camera.eye;
  var n=function(e){return Math.sqrt(e.x*e.x+e.y*e.y+e.z*e.z);};R.s2={d0:n(e0),d1:n(e1),dir:(e0.x*e1.x+e0.y*e1.y+e0.z*e1.z)/(n(e0)*n(e1))};
  /* S3 */
  var s=$('tbBg');R.s3={def:s.value,bg0:gd._fullLayout.paper_bgcolor};s.value='navy';s.onchange();await w(2500);
  R.s3.bgN=gd._fullLayout.paper_bgcolor;R.s3.cls=$('stage').classList.contains('bglat-navy');R.s3.tick=gd._fullLayout.scene.xaxis.tickfont.color;
  s.value='polos';s.onchange();await w(2500);R.s3.bgP=gd._fullLayout.paper_bgcolor;R.s3.cls2=$('stage').classList.contains('bglat-navy');
  /* S4 */
  gd.emit('plotly_hover',{points:[{x:10,y:20,z:250}]});await w(100);
  R.s4={xy:$('sbXY').textContent,ve:$('sbVE').textContent,old:!!($('secInfo')&&$('rtime')&&$('wmark')),offX:offX,offY:offY,
    pandang:/Pandang/.test($('status').textContent),bg:getComputedStyle($('status')).backgroundColor};
  /* S5 */
  var lg=document.querySelector('.tplg-t'),tmp=document.createElement('div');tmp.style.background='#233a7e';document.body.appendChild(tmp);var pr=getComputedStyle(tmp).backgroundColor;tmp.remove();R.s5={leg:lg?getComputedStyle(lg).backgroundColor:null,navy:pr,pal:[].some.call(document.styleSheets,function(ss){try{return [].some.call(ss.cssRules,function(r){return /\.tplg-t/.test(r.selectorText||'')&&/border-bottom: 2px solid/.test(r.cssText);});}catch(e){return false;}})};
  if(window.GXP&&GXP.buka){try{GXP.buka('ujiShell','Uji','<p>isi</p>');}catch(x){}}
  var pp=document.querySelector('.gxpop .gxph');R.s5.pop=pp?getComputedStyle(pp).backgroundColor:null;
  /* S6 (0.24.79): menu teks bilah atas dihapus; Properti tempel kiri / kanan / lepas; Project Tree disembunyikan sendiri */
  R.s6={menu:!!$('bmMenu')};var par=function(){var p=$('side').parentNode;return p&&p.id;},vis=function(id){var e=$(id);return !!e&&e.getBoundingClientRect().width>0&&getComputedStyle(e).display!=='none';};
  R.s6.p0=par();R.s6.btn=document.querySelectorAll('#ptPH .pdk button[data-p]').length;
  document.querySelector('#ptPH .pdk button[data-p=kanan]').click();await w(700);
  var sr=$('side').getBoundingClientRect(),gr=$('plotDiv').getBoundingClientRect();R.s6.kanan={p:par(),kanan:sr.left>=gr.right-2,ls:localStorage.getItem('gcex_bm_prop'),tree:vis('ptWrap')};
  document.querySelector('#ptPH .pdk button[data-p=lepas]').click();await w(700);
  R.s6.lepas={p:par(),fixed:getComputedStyle($('propF')).position,kanan:vis('propR'),btnOn:!!document.querySelector('#ptPH .pdk button[data-p=lepas].on')};
  $('ptHide').click();await w(500);R.s6.lepasNoTree={col:vis('ptCol'),prop:vis('side'),ob:vis('ptOpen')};$('ptOpen').click();await w(400);
  document.querySelector('#ptPH .pdk button[data-p=kiri]').click();await w(700);R.s6.kiri={p:par(),f:vis('propF')};
  $('ptHide').click();await w(500);R.s6.kiriNoTree={tree:vis('ptWrap'),prop:vis('side'),ob:vis('ptOpen')};$('ptOpen').click();await w(500);R.s6.kembali={tree:vis('ptWrap'),prop:vis('side')};
  /* S7 */
  var open0=JSON.stringify(PT.open);SHELL.cari('statistik');await w(400);
  var vis=[].filter.call(document.querySelectorAll('#ptree .ptr'),function(r){return getComputedStyle(r).display!=='none';}).map(function(r){return r.textContent.trim().slice(0,30);});
  R.s7={vis:vis};SHELL.cari('');await w(400);R.s7.restored=JSON.stringify(PT.open)===open0;
  R.s7.after=[].filter.call(document.querySelectorAll('#ptree .ptr'),function(r){return getComputedStyle(r).display!=='none';}).length;
  /* S8 */
  var ell=function(){var d=$('cpEll').getAttribute('d'),P=d.replace(/[MLZ]/g,' ').trim().split(/\s+/).map(function(p){return p.split(',').map(Number);}),
    xs=P.map(function(p){return p[0];}),ys=P.map(function(p){return p[1];});return [Math.max.apply(0,xs)-Math.min.apply(0,xs),Math.max.apply(0,ys)-Math.min.apply(0,ys)];};
  setCam(2.4,0.3,0.2);await w(900);R.s8={side:ell(),zSide:$('cpZ').getAttribute('d'),zh:$('cpZh').getAttribute('points'),txt:$('cpTxt').textContent};
  setCam(0,-0.01,2.5);await w(900);R.s8.top=ell();R.s8.zTop=$('cpZ').getAttribute('d');
  /* S9 (0.24.81): .mdl besar + filter pit/topografi -> dibaca langsung (tanpa backend); tanpa filter area -> backend */
  var calls=[],D0=window.gcexDesktop;window.gcexDesktop={api:async function(u){calls.push(u);throw new Error('stub');},apiBin:async function(u){calls.push(u);throw new Error('stub');},pathOf:function(){return 'C:/x/besar.mdl';}};
  var fake={name:'besar.mdl',size:200*1048576,lastModified:0,slice:function(){return new Blob([new Uint8Array(64)]);}};
  try{await SA.readMDL(fake,null,{pit:{x0:0,y0:0,c:1,nx:1,ny:1,z:new Float32Array(1)}});}catch(x){}var cPit=calls.slice();calls.length=0;
  try{await SA.readMDL(fake,null,{zMin:210,zMax:270});}catch(x){}var cRl=calls.slice();window.gcexDesktop=D0;
  R.s9={pit:cPit,rl:cRl};
  /* S10 (0.24.81): sayatan di luar RL block model baru -> dipindah ke tengah rentang */
  var cb=$('showPlane');if(cb&&!cb.checked){cb.checked=true;cb.dispatchEvent(new Event('change',{bubbles:true}));}if(typeof VIEW2D!=='undefined'&&VIEW2D&&window.toggle2D)toggle2D();
  if($('sMode').value!=='H'){$('sMode').value='H';$('sMode').dispatchEvent(new Event('change',{bubbles:true}));}await w(600);
  var p=$('pos');p.max=Math.max(+p.max,9999);p.value=9000;var e=BX.m.ext;BX.m=Object.assign({},BX.m);SHELL.rlCek();await w(1500);
  R.s10={pos:+p.value,z0:e&&e[4],z1:e&&e[5]};
  /* S11 */
  var M0=BX.m.mdl,c11=[],k=0,ms=[];BX.m.mdl=Object.assign({},M0||{},{via:'js',bigPath:1,path:'C:/x/besar.mdl',nRead:88280388,st:[{name:BX.ui.attr,type:1}]});
  window.gcexDesktop={api:async function(u,b){c11.push(u);if(u==='/mdl/open'){k++;if(k<3){setTimeout(function(){var d=$('bsDlg');ms.push(d?d.textContent:'');},50);return {state:'building',pct:k*40,n:k*1000};}return {state:'ready'};}
    if(u==='/mdl/benches')return {rows:[],tot:{}};throw new Error('?');}};
  try{bsOpen();await bsRun();}catch(x){R.e11=String(x);}var okRun=c11.slice();
  c11.length=0;window.gcexDesktop.api=async function(u){c11.push(u);if(u==='/mdl/cache')return {root:'D:/GC-Ex_cache_mdl',used:0,free:5e11,items:[],custom:true};throw new Error('No space left on device');};
  await bsRun();await w(300);var dl=$('bsDlg');
  R.s11={calls:okRun,prog:ms.some(function(t){return /Membangun cache seluruh model/.test(t);}),back:bsBack(),errCard:!!(dl&&dl.querySelector('#mdlCache')),errTxt:dl?/No space/.test(dl.textContent):false};
  /* S12 */
  var cc=$('mdlCache');R.s12={txt:cc?cc.textContent:'',btn:cc?[].map.call(cc.querySelectorAll('button'),function(b){return b.textContent;}):[],hapusBtn:document.querySelectorAll('button').length&&[].filter.call(document.querySelectorAll('button'),function(b){return /Hapus cache/i.test(b.textContent);}).length};
  window.gcexDesktop=D0;BX.m.mdl=M0;if(dl)dl.style.display='none';
  /* S13 (0.24.86): kamera digerakkan (zoom masuk) -> TIDAK ada gambar ulang penuh bila orthofoto tidak tampil */
  if(typeof VIEW2D!=='undefined'&&VIEW2D&&window.toggle2D){toggle2D();await w(1500);}
  var gd2=$('plotDiv'),nU=0,u0=window.updatePlot;window.updatePlot=function(){nU++;return u0.apply(this,arguments);};
  var cam=function(k){return Plotly.relayout(gd2,{'scene.camera':{eye:{x:0.25*k,y:-0.3*k,z:0.2*k},center:{x:0.05*k,y:0,z:0},up:{x:0,y:0,z:1}}});};
  await cam(1);await w(900);var nOff=nU,hp=window.HR_perlu;window.HR_perlu=function(){return true;};await cam(1.3);await w(900);var nOn=nU-nOff;window.HR_perlu=hp;window.updatePlot=u0;
  R.s13={ada:typeof hp==='function',off:nOff,on:nOn,perlu:hp?hp():null};
  return R;}"""


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
            pg = b.new_page(viewport={"width": 1440, "height": 900}); pg.on("dialog", lambda x: x.accept()); pg.on("pageerror", lambda e: err.append(str(e)))
            pg.goto("http://127.0.0.1:%d/index.html" % PORT)
            pg.wait_for_function("window.DLAT && DLAT.siap", timeout=60000); pg.evaluate("document.getElementById('dlatBtn').click()")
            pg.wait_for_function("window.BX && BX.m && BX.m.n>0", timeout=600000); pg.wait_for_function("!DLAT.busy", timeout=600000); pg.wait_for_timeout(5000)
            ada = pg.evaluate("!!window.SHELL")
            if not ada:
                print("GAGAL: shell_bm.js tidak terpasang (build lama)"); b.close(); return 1
            r = pg.evaluate(JS); b.close()
    finally:
        srv.terminate()
    print(json.dumps(r, ensure_ascii=False)[:1500])
    s1 = r["s1"]
    cek(s1["tb"] and s1["inTb"] and not s1["topTools"], "S1 alat tampilan pindah ke toolbar, bilah atas tanpa .tools")
    cek(all(v == 1 for v in s1["n"].values()), "S1 tiap alat tepat satu kali: %s" % s1["n"])
    cek(s1["inside"] and s1["gsHidden"], "S1 alat di dalam toolbar; tombol tersembunyi tetap tersembunyi")
    cek("Arial Black" in s1["logo"], "S1 huruf logo GC-Ex tetap Arial Black (%s)" % s1["logo"])
    s2 = r["s2"]; cek(abs(s2["d1"] - (1.5 * 1.5 * 2 + 1) ** 0.5) < 0.05 and s2["dir"] > 0.999 and abs(s2["d0"] - s2["d1"]) > 0.5, "S2 Semua data: jarak kamera bawaan, arah tetap %s" % s2)
    s3 = r["s3"]
    cek(s3["def"] == "polos" and "0, 0, 0, 0" not in s3["bg0"].replace("rgba(0,0,0,0)", "rgba(0, 0, 0, 0)"), "S3 bawaan Polos (latar tidak transparan: %s)" % s3["bg0"])
    cek("0, 0, 0, 0" in s3["bgN"] and s3["cls"] and s3["tick"] == "#c9d2e3", "S3 Gradasi navy: latar transparan, kelas stage, label terang")
    cek("0, 0, 0, 0" not in s3["bgP"] and not s3["cls2"], "S3 kembali Polos")
    s4 = r["s4"]
    e_exp = "E " + format(10 + s4["offX"], ",.1f").replace(",", "X").replace(".", ",").replace("X", ".")
    cek(s4["xy"].startswith(e_exp) and "RL 250,0" in s4["xy"], "S4 koordinat kursor + offset proyek: %s (harap %s…)" % (s4["xy"], e_exp))
    cek(s4["ve"].startswith("VE ") and s4["old"] and not s4["pandang"], "S4 VE, info lama tetap, arah pandang tidak diulang")
    cek(s4["bg"] == "rgb(27, 35, 51)", "S4 status bar navy (%s)" % s4["bg"])
    s5 = r["s5"]; NAVY = ("rgb(35, 58, 126)", "rgb(44, 59, 87)")  # #233a7e; palet build (palette_patch.py) memetakannya ke #2c3b57
    cek(s5["leg"] in NAVY and s5["pal"], "S5 kepala legenda navy + garis emas (%s)" % s5["leg"])
    if s5.get("pop") is not None: cek(s5["pop"] in NAVY, "S5 kepala jendela pop-up navy (%s)" % s5["pop"])
    s6 = r["s6"]
    cek(not s6["menu"], "S6 menu teks bilah atas sudah dihapus (0.24.79)")
    cek(s6["p0"] == "ptCol" and s6["btn"] == 4, "S6 Properti bawaan di kiri, 3 tombol posisi + perkecil")
    cek(s6["kanan"]["p"] == "propR" and s6["kanan"]["kanan"] and s6["kanan"]["ls"] == "kanan" and s6["kanan"]["tree"], "S6 tempel kanan: kolom kanan 3D, posisi diingat, Project Tree tetap %s" % s6["kanan"])
    cek(s6["lepas"]["p"] == "propF" and s6["lepas"]["fixed"] == "fixed" and not s6["lepas"]["kanan"] and s6["lepas"]["btnOn"], "S6 lepas: jendela mengambang %s" % s6["lepas"])
    cek(not s6["lepasNoTree"]["col"] and s6["lepasNoTree"]["prop"] and s6["lepasNoTree"]["ob"], "S6 lepas + Project Tree disembunyikan: kolom kiri hilang, Properti tetap %s" % s6["lepasNoTree"])
    cek(s6["kiri"]["p"] == "ptCol" and not s6["kiri"]["f"], "S6 kembali ke kiri")
    cek(not s6["kiriNoTree"]["tree"] and s6["kiriNoTree"]["prop"] and s6["kiriNoTree"]["ob"], "S6 kiri + sembunyikan Project Tree: hanya Project Tree yang hilang %s" % s6["kiriNoTree"])
    cek(s6["kembali"]["tree"] and s6["kembali"]["prop"], "S6 tampilkan Project Tree lagi")
    s7 = r["s7"]; v = s7["vis"]
    cek(len(v) >= 2 and any("Statistik" in x for x in v) and any("Block Model" in x for x in v) and len(v) <= 4, "S7 cari 'statistik' -> hanya hasil + induk: %s" % v)
    cek(s7["restored"] and s7["after"] > len(v), "S7 kosongkan cari -> folder kembali seperti semula")
    s8 = r["s8"]
    cek(s8["side"][0] > 3 * s8["side"][1] and "a4" not in (s8["zSide"] or ""), "S8 pandangan samping: piringan pipih %s, panah Z %s" % (s8["side"], s8["zSide"]))
    cek(abs(s8["top"][0] - s8["top"][1]) < 1.5 and "a4" in (s8["zTop"] or ""), "S8 dari atas: lingkaran %s, Z = titik" % s8["top"])
    s9 = r["s9"]
    cek(not s9["pit"] and any("/mdl/" in u for u in s9["rl"]), "S9 .mdl besar: filter pit -> baca langsung %s; hanya RL -> backend %s" % (s9["pit"], s9["rl"]))
    s10 = r["s10"]
    cek(s10["z0"] is not None and s10["z0"] - 1e-6 <= s10["pos"] <= s10["z1"] + 1e-6, "S10 sayatan RL 9000 dipindah ke dalam rentang block model %s" % s10)
    s11 = r["s11"]
    cek(s11["back"] and s11["calls"][:3] == ["/mdl/open"] * 3 and s11["calls"][-1] == "/mdl/benches" and s11["prog"],
        "S11 dibaca langsung + filter pit -> Ringkasan per RL lewat backend, cache dibangun dengan progres %s" % s11)
    cek(s11["errCard"] and s11["errTxt"], "S11 cache gagal (disk penuh) -> pesan + kotak folder cache")
    s12 = r["s12"]
    cek("D:/GC-Ex_cache_mdl" in s12["txt"] and "ruang bebas" in s12["txt"] and any("Ganti folder" in b for b in s12["btn"])
        and any("Kembalikan" in b for b in s12["btn"]) and "Bantuan" in s12["txt"] and not s12["hapusBtn"],
        "S12 kotak folder cache; hapus cache tetap satu pintu di menu Bantuan %s" % s12)
    s13 = r["s13"]
    cek(s13["ada"] and s13["off"] == 0 and s13["on"] >= 1 and s13["perlu"] is False, "S13 kamera digerakkan: tanpa orthofoto tidak digambar ulang (%s), dengan orthofoto digambar ulang (%s)" % (s13["off"], s13["on"]))
    cek(not err, "tanpa error halaman %s" % err[:3])
    print("GAGAL (%d)" % len(gagal) if gagal else "LULUS")
    return 1 if gagal else 0


if __name__ == "__main__":
    sys.exit(main())
