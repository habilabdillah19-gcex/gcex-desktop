# -*- coding: utf-8 -*-
"""Bukti bahwa SETIAP ekspor menanyakan lokasi & nama berkas.

Caranya tidak membaca kode, melainkan memalsukan jembatan aplikasi terpasang
(gcexDesktop.api.saveFile) lalu memanggil tiap fungsi ekspor sungguhan dan mencatat apakah dialog
Simpan itu benar-benar dipanggil, dengan nama berkas apa. Satu pun ekspor yang lolos tanpa bertanya
akan terlihat sebagai <a download> yang ikut tercatat terpisah."""
import os, random, shutil, subprocess, sys, tempfile, time, urllib.request
from pathlib import Path
ROOT=Path("/home/claude/gcex-desktop"); PORT=str(random.randint(9100,9899))
APP=sys.argv[1] if len(sys.argv)>1 else "app-dh"
DATA=ROOT/"docs"/"tutorial-gcex"/"data"
d=Path(tempfile.mkdtemp(prefix="gcex_exp_")); shutil.copyfile(ROOT/APP/"index.html",d/"index.html")
os.symlink(DATA,d/"data-latihan")
subprocess.Popen([sys.executable,"-m","http.server",PORT],cwd=str(d),stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
for _ in range(40):
    try: urllib.request.urlopen("http://localhost:%s/index.html"%PORT,timeout=1); break
    except Exception: time.sleep(0.4)
print("aplikasi:",APP)

JS_SADAP=r"""
(function(){
  window.__SAVE=[]; window.__DL=[];
  /* palsukan jembatan aplikasi terpasang: inilah jalur yang dipakai di Windows */
  window.gcexDesktop={api:{saveFile:function(nama,data,filters){
     __SAVE.push({nama:nama,byte:(data&&data.length)||0,filters:(filters||[]).map(function(f){return f.name;})});
     return Promise.resolve('C:\\Uji\\'+nama);}}};
  /* catat juga kalau ada yang masih mengunduh diam-diam lewat <a download> */
  var klik=HTMLAnchorElement.prototype.click;
  HTMLAnchorElement.prototype.click=function(){ if(this.download)__DL.push(this.download); return klik.apply(this,arguments); };
  return true;})
"""
JS_HASIL=r"(function(){return{simpan:window.__SAVE,unduh:window.__DL};})"
from playwright.sync_api import sync_playwright
with sync_playwright() as pw:
    ctx=pw.chromium.launch_persistent_context(tempfile.mkdtemp(prefix="gcex_expc_"),
        args=["--use-angle=swiftshader","--enable-unsafe-swiftshader"],viewport={"width":1500,"height":950})
    ctx.add_init_script("window.showDirectoryPicker=async function(){throw new Error('batal');};")
    pg=ctx.new_page(); pg.on("dialog",lambda x:x.accept())
    er=[]; pg.on("pageerror",lambda e:er.append(str(e)[:140]))
    pg.goto("http://localhost:%s/index.html"%PORT); pg.wait_for_timeout(1500)
    pg.wait_for_function("window.DLAT && DLAT.siap",timeout=90000)
    pg.evaluate("document.getElementById('dlatBtn').click()")
    # tunggu datanya masuk (bukan menunggu gxSimpan: sumber viewer baru dieval sesudah proyek dibuka)
    pg.wait_for_function("(window.collars && collars.length>0) || (window.BX && BX.m && BX.m.n>0)",timeout=600000)
    pg.wait_for_function("!DLAT.busy",timeout=600000); pg.wait_for_timeout(5000)
    print("gxSimpan tersedia:",pg.evaluate("typeof window.gxSimpan"))
    pg.evaluate(JS_SADAP)
    FUNGSI = sys.argv[2].split(",") if len(sys.argv)>2 else []
    for nm in FUNGSI:
        try:
            # dukung nama bertitik (mis. SA.valCsv) dan argumen (mis. dgExport:str)
            fn,_,arg = nm.partition(":")
            jalan = "(function(){var f=window;%s;return typeof f==='function';})()" % \
                    ";".join(["f=f&&f[%r]"%k for k in fn.split(".")])
            if not pg.evaluate(jalan): print("  - %-20s (tidak tersedia)"%nm); continue
            panggil = "(function(){var f=window;%s;try{f(%s);}catch(e){window.__ERR=(window.__ERR||[]).concat(%r+': '+String(e&&e.message||e));}})()" % (
                ";".join(["f=f[%r]"%k for k in fn.split(".")]), repr(arg) if arg else "", nm)
            pg.evaluate(panggil)
            pg.wait_for_timeout(900)
        except Exception as e: print("  ! %-16s galat harness: %s"%(nm,str(e)[:70]))
    R=pg.evaluate(JS_HASIL)
    print("\n%d ekspor memunculkan dialog Simpan:"%len(R["simpan"]))
    for s in R["simpan"]: print("   %-44s %7d byte   jenis: %s"%(s["nama"],s["byte"],", ".join(s["filters"][:2])))
    if R["unduh"]:
        print("\n%d MASIH mengunduh diam-diam tanpa bertanya:"%len(R["unduh"]))
        for u in R["unduh"]: print("   %s"%u)
    else:
        print("\nTidak ada yang mengunduh diam-diam.")
    e2=pg.evaluate("window.__ERR||[]")
    if e2: print("galat fungsi:",e2[:6])
    if er: print("galat halaman:",er[:4])
    ctx.close()
