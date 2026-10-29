"""Gambar 'validasi_rusak' (database dengan kesalahan sengaja, SIM_rusak_*). Jalankan sesudah tutorial_shots.py."""
from playwright.sync_api import sync_playwright
import os,subprocess,sys,time,urllib.request
T=os.path.dirname(os.path.abspath(__file__))+'/';R=os.path.abspath(T+'../../../')+'/';DATA=T+'../data/';IMG=T+'img/';PORT=8777;P='http://localhost:%d/index.html'%PORT
try:urllib.request.urlopen(P,timeout=2)
except Exception:subprocess.Popen([sys.executable,'-m','http.server',str(PORT)],cwd=R+'app-dh/',stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
with sync_playwright() as pw:
    br=pw.chromium.launch();pg=br.new_page(viewport={'width':1600,'height':940},device_scale_factor=1.25);pg.on('dialog',lambda d:d.accept())
    pg.goto(P);pg.wait_for_timeout(1500)
    for role,f in [('collar','SIM_rusak_collar.csv'),('survey','SIM_survey.csv'),('assay','SIM_rusak_assay.csv'),('geo','SIM_geologi.csv')]:
        pg.set_input_files("input[onchange*=\"slotFile('%s'\"]"%role,DATA+f);pg.wait_for_timeout(600)
    pg.evaluate("SA.preview&&SA.preview();var d=document.querySelector('#dbSum details');if(d)d.open=true;document.getElementById('dbSum').scrollIntoView({block:'center'})");pg.wait_for_timeout(600)
    b=pg.locator('#dbSum').bounding_box();x=max(0,b['x']-12);y=max(0,b['y']-12)
    pg.screenshot(path=IMG+'71_validasi_rusak.png',clip={'x':x,'y':y,'width':min(1600-x,b['width']+24),'height':min(940-y,b['height']+24)});br.close()
print('ok')
