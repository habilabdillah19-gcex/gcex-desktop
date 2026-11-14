# -*- coding: utf-8 -*-
"""Block Model 0.24.78: shell ala Ore Works tahap 1 + 2 (web-src/shell_bm.js, kompas 3D di gcex_base.html).

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
  S6 menu teks bilah atas = node teratas Project Tree (tanpa Proyek); memilih item -> node terpilih di Project Tree.
  S7 cari di Project Tree: hanya baris yang cocok + induknya; dikosongkan -> folder kembali seperti semula.
  S8 kompas 3D: piringan miring (elips) & panah Z saat pandangan samping; dari atas: elips = lingkaran, Z = titik.
Pemakaian: python tools/uji/uji_shell_bm.py [app/index.html]   (build 0.24.77 harus GAGAL)
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
  /* S6 */
  var top=PT.nodes.filter(function(n){return !n.addRow&&!/^Proyek/i.test(n.t);}).map(function(n){return n.id;});
  var mb=[].slice.call(document.querySelectorAll('#bmMenu>button[data-i]'));R.s6={top:top.length,menu:mb.length};
  var bmB=mb.filter(function(b){return b.textContent==='Block Model';})[0];
  if(bmB){bmB.click();await w(200);var it=[].filter.call(document.querySelectorAll('#bmMenuDd button[data-id]'),function(b){return b.textContent==='Statistik';})[0];R.s6.item=!!it;if(it){it.click();await w(500);}}
  R.s6.sel=PT.sel;
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
    s6 = r["s6"]; cek(s6["menu"] == s6["top"] and s6["menu"] >= 8, "S6 menu teks = node teratas Project Tree (%s/%s)" % (s6["menu"], s6["top"]))
    cek(s6.get("item") and s6["sel"] == "bm.stat" or (s6.get("item") and str(s6["sel"]).startswith("bm.")), "S6 memilih 'Statistik' dari menu -> node terpilih %s" % s6["sel"])
    s7 = r["s7"]; v = s7["vis"]
    cek(len(v) >= 2 and any("Statistik" in x for x in v) and any("Block Model" in x for x in v) and len(v) <= 4, "S7 cari 'statistik' -> hanya hasil + induk: %s" % v)
    cek(s7["restored"] and s7["after"] > len(v), "S7 kosongkan cari -> folder kembali seperti semula")
    s8 = r["s8"]
    cek(s8["side"][0] > 3 * s8["side"][1] and "a4" not in (s8["zSide"] or ""), "S8 pandangan samping: piringan pipih %s, panah Z %s" % (s8["side"], s8["zSide"]))
    cek(abs(s8["top"][0] - s8["top"][1]) < 1.5 and "a4" in (s8["zTop"] or ""), "S8 dari atas: lingkaran %s, Z = titik" % s8["top"])
    cek(not err, "tanpa error halaman %s" % err[:3])
    print("GAGAL (%d)" % len(gagal) if gagal else "LULUS")
    return 1 if gagal else 0


if __name__ == "__main__":
    sys.exit(main())
