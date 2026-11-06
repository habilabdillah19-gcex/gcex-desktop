# -*- coding: utf-8 -*-
"""Peta node Project Tree -> isi panel Properti yang BENAR-BENAR terlihat.
Dijalankan di aplikasi sungguhan dengan data latihan."""
import os, shutil, subprocess, sys, tempfile, time, urllib.request
from pathlib import Path
ROOT = Path("/home/claude/gcex-desktop")
DATA = ROOT / "docs" / "tutorial-gcex" / "data"
PORT = sys.argv[1] if len(sys.argv) > 1 else "8801"

d = Path(tempfile.mkdtemp(prefix="gcex_ui_"))
shutil.copyfile(ROOT / "app" / "index.html", d / "index.html")
os.symlink(DATA, d / "data-latihan")
subprocess.Popen([sys.executable, "-m", "http.server", PORT], cwd=str(d),
                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
for _ in range(40):
    try:
        urllib.request.urlopen("http://localhost:%s/index.html" % PORT, timeout=1); break
    except Exception: time.sleep(0.4)

JS_LIST = r"""
(function(){ return (PT.flat||[]).map(function(n){return {id:n.id,t:n.t,tab:n.tab||'',foc:n.foc||''};}); })
"""
# teks yang KELIHATAN di #side (panel Properti), dipotong per judul
JS_SEE = r"""
(function(){
  var sd=document.getElementById('side'); if(!sd) return {err:'no side'};
  var out=[], seen={};
  var vis=function(e){ if(!e.offsetParent && e.tagName!=='BODY') return false;
    var s=getComputedStyle(e); return s.display!=='none' && s.visibility!=='hidden'; };
  sd.querySelectorAll('h3,h4,.amh,.dbsub,.uisec>.uish,label>b,button.btn-pri,.rptabs button.on,.lab,.ptcd>button,.ptck button,.lyhead')
    .forEach(function(e){ if(!vis(e))return; var t=(e.textContent||'').trim().slice(0,60);
      if(!t||seen[t])return; seen[t]=1; out.push(t); });
  return {n:out.length, t:out.slice(0,25)};
})
"""
from playwright.sync_api import sync_playwright
with sync_playwright() as pw:
    ctx = pw.chromium.launch_persistent_context(tempfile.mkdtemp(prefix="gcex_uictx_"),
        args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader"],
        viewport={"width": 1600, "height": 1000})
    ctx.add_init_script("window.showDirectoryPicker=async function(){throw new Error('batal');};")
    pg = ctx.new_page(); pg.on("dialog", lambda x: x.accept())
    err = []; pg.on("pageerror", lambda e: err.append(str(e)[:160]))
    pg.goto("http://localhost:%s/index.html" % PORT); pg.wait_for_timeout(1500)
    pg.wait_for_function("window.DLAT && DLAT.siap", timeout=60000)
    pg.evaluate("document.getElementById('dlatBtn').click()")
    pg.wait_for_function("window.BX && BX.m && BX.m.n>0", timeout=600000)
    pg.wait_for_function("!DLAT.busy", timeout=600000); pg.wait_for_timeout(2500)
    # buka semua folder
    pg.evaluate("(function(){(PT.flat||[]).forEach(function(n){PT.open[n.id]=1;});PT.render(true);})()")
    pg.wait_for_timeout(600)
    nodes = pg.evaluate(JS_LIST)
    print("%d node" % len(nodes)); print("=" * 100)
    for n in nodes:
        try:
            pg.evaluate("PT.select(%r)" % n["id"]); pg.wait_for_timeout(260)
            s = pg.evaluate(JS_SEE)
        except Exception as e:
            s = {"err": str(e)[:80]}
        print("\n### %-28s %-34s tab=%-6s foc=%s" % (n["id"], n["t"][:34], n["tab"], n["foc"]))
        print("    " + " | ".join(s.get("t", [])) if s.get("t") else "    " + str(s))
    if err: print("\nGALAT:", err[:5])
    ctx.close()
