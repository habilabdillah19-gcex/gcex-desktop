# -*- coding: utf-8 -*-
"""Profil jeda saat berpindah panel / node Project Tree (BM & DH), data latihan.
Untuk tiap node: klik baris -> ukur JS sinkron (ms), long task 1,5 s sesudahnya, panggilan Plotly (react/newPlot/
relayout/restyle/resize + durasinya), PT.render, updatePlot. Keluaran: tabel terurut dari yang paling lambat.
Pemakaian: python tools/uji/profil_panel.py app/index.html  |  app-dh/index.html"""
import json, os, random, subprocess, sys, tempfile, time, urllib.request
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT = Path(__file__).resolve().parents[2]; DATA = ROOT / "docs" / "tutorial-gcex" / "data"; APP = sys.argv[1]
port = str(random.randint(9100, 9899)); d = Path(tempfile.mkdtemp()); (d / "index.html").write_bytes((ROOT / APP).read_bytes()); os.symlink(DATA, d / "data-latihan")
srv = subprocess.Popen([sys.executable, "-m", "http.server", port], cwd=str(d), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
P = "http://localhost:%s/index.html" % port
for _ in range(50):
    try: urllib.request.urlopen(P, timeout=1); break
    except Exception: time.sleep(.4)
HOOK = r"""(function(){window.__PR={lt:0,pl:[],render:0,up:0};
  new PerformanceObserver(function(l){l.getEntries().forEach(function(e){__PR.lt+=e.duration;});}).observe({entryTypes:['longtask']});
  ['react','newPlot','relayout','restyle','redraw','update','addTraces','deleteTraces'].forEach(function(k){var f=Plotly[k];if(typeof f!=='function')return;Plotly[k]=function(){var t=performance.now();var r=f.apply(this,arguments);var fin=function(){__PR.pl.push([k,Math.round(performance.now()-t)]);};if(r&&r.then)r.then(fin,fin);else fin();return r;};});
  var rs=Plotly.Plots.resize;Plotly.Plots.resize=function(){var t=performance.now();var r=rs.apply(this,arguments);var fin=function(){__PR.pl.push(['resize',Math.round(performance.now()-t)]);};if(r&&r.then)r.then(fin,fin);else fin();return r;};
  var pr=PT.render;PT.render=function(){__PR.render++;return pr.apply(this,arguments);};
  if(window.updatePlot){var up=updatePlot;window.updatePlot=function(){__PR.up++;return up.apply(this,arguments);};}
  window.__reset=function(){__PR.lt=0;__PR.pl=[];__PR.render=0;__PR.up=0;};})()"""
with sync_playwright() as pw:
    ctx = pw.chromium.launch_persistent_context(tempfile.mkdtemp(), args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"], viewport={"width": 1600, "height": 940})
    ctx.add_init_script("window.showDirectoryPicker=undefined;")
    pg = ctx.new_page(); pg.on("dialog", lambda x: x.accept(x.default_value) if x.type == "prompt" else x.accept())
    pg.goto(P); pg.wait_for_timeout(1500); pg.wait_for_function("window.DLAT && DLAT.siap", timeout=90000)
    pg.evaluate("document.getElementById('dlatBtn').click()"); pg.wait_for_timeout(3000); pg.wait_for_function("!DLAT.busy", timeout=900000); pg.wait_for_timeout(3000)
    pg.evaluate(HOOK)
    ids = pg.evaluate("(function(){for(var k=0;k<3;k++){PT.render(true);PT.flatAll(PT.nodes).forEach(function(n){if(n.kids&&n.kids.length)PT.open[n.id]=1;});}PT.render(true);return PT.flatAll(PT.nodes).filter(function(n){return !n.addRow;}).map(function(n){return [n.id,n.t,n.tab||''];});})()")
    rows = []
    for nid, t, tab in ids:
        pg.evaluate("__reset()")
        r = pg.evaluate("""(function(id){var el=document.querySelector('#ptree .ptr[data-id=\"'+CSS.escape(id)+'\"] .ptl');if(!el)return null;var t0=performance.now();el.click();return Math.round(performance.now()-t0);})(%s)""" % json.dumps(nid))
        if r is None: continue
        pg.wait_for_timeout(1500)
        m = pg.evaluate("__PR")
        rows.append({"id": nid, "t": t, "tab": tab, "sync": r, "lt": round(m["lt"]), "pl": m["pl"], "render": m["render"], "up": m["up"]})
    # pindah tab lewat rail (rb*) juga
    rails = pg.evaluate("[].map.call(document.querySelectorAll('.rb[id^=rb]'),function(b){return b.id;})")
    for rb in rails:
        pg.evaluate("__reset()")
        r = pg.evaluate("(function(id){var el=document.getElementById(id);if(!el||el.offsetParent===null)return null;var t0=performance.now();el.click();return Math.round(performance.now()-t0);})(%s)" % json.dumps(rb))
        if r is None: continue
        pg.wait_for_timeout(1500); m = pg.evaluate("__PR")
        rows.append({"id": rb, "t": "(rail)", "tab": "", "sync": r, "lt": round(m["lt"]), "pl": m["pl"], "render": m["render"], "up": m["up"]})
    ctx.close()
srv.terminate()
rows.sort(key=lambda x: -(x["lt"] + x["sync"]))
print(APP, "| node:", len(rows), "| total longtask ms:", sum(x["lt"] for x in rows), "| total plotly ms:", sum(sum(p[1] for p in x["pl"]) for x in rows))
print("%-28s %-30s %6s %6s %4s %3s  plotly" % ("id", "node", "sync", "ltask", "rend", "up"))
for x in rows[:45]:
    print("%-28s %-30s %6d %6d %4d %3d  %s" % (x["id"][:28], x["t"][:30], x["sync"], x["lt"], x["render"], x["up"], ",".join("%s:%d" % (p[0], p[1]) for p in x["pl"])[:70]))
json.dump(rows, open("/tmp/profil_%s.json" % ("dh" if "dh" in APP else "bm"), "w"))
