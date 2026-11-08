"""Gambar bab 'Plan bor harian' (set plan bor, Drillhole 0.24.44). Jalankan sesudah tutorial_shots.py.
Memakai data latihan simulasi (tombol "Muat data latihan simulasi") dan membuat tiga plan:
  1. Plan hari 1  : 5 titik sepanjang garis, bench RL240
  2. Plan hari 2  : grid 3 x 2 di sebelah timur laut, bench RL235
  3. extend plan 1: 2 titik tambahan (plan 1 diaktifkan lagi)
Hasil: img/88_plan_set.png (Project Tree + panel), img/89_plan_peta.png (peta plan) + catatan di img/notes.json."""
from playwright.sync_api import sync_playwright
import os, sys, json, time, random, subprocess, tempfile, urllib.request
T = os.path.dirname(os.path.abspath(__file__)) + '/'; R = os.path.abspath(T + '../../../') + '/'; DATA = os.path.abspath(T + '../data'); IMG = T + 'img/'
PORT = random.randint(9100, 9899); P = 'http://localhost:%d/index.html' % PORT
d = tempfile.mkdtemp(prefix='gcex_plan_'); open(d + '/index.html', 'wb').write(open(R + 'app-dh/index.html', 'rb').read()); os.symlink(DATA, d + '/data-latihan')
subprocess.Popen([sys.executable, '-m', 'http.server', str(PORT)], cwd=d, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
for _ in range(40):
    try: urllib.request.urlopen(P, timeout=1); break
    except Exception: time.sleep(0.4)
with sync_playwright() as pw:
    ctx = pw.chromium.launch_persistent_context(tempfile.mkdtemp(), args=['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'],
                                                viewport={'width': 1600, 'height': 940}, device_scale_factor=1.25)
    ctx.add_init_script("window.showDirectoryPicker=async function(){throw new Error('batal');};")
    pg = ctx.new_page(); pg.on('dialog', lambda x: x.accept(x.default_value) if x.type == 'prompt' else x.accept())
    pg.goto(P); pg.wait_for_timeout(1500); pg.wait_for_function('window.DLAT && DLAT.siap', timeout=90000)
    pg.evaluate("document.getElementById('dlatBtn').click()")
    pg.wait_for_function('window.collars && collars.length>0', timeout=900000); pg.wait_for_function('!DLAT.busy', timeout=900000); pg.wait_for_timeout(3000)
    r = pg.evaluate("""(async function(){var W=function(ms){return new Promise(function(r){setTimeout(r,ms);});};
      try{localStorage.removeItem(plKey()+'_sets');}catch(e){}PL.sets=null;PL.h=[];PL.act=null;PL._hDari=null;
      $('plBench').value='RL240';$('plSeq').value=1;plRefresh(true);
      PL.sets[0].name='Plan '+PL.sets[0].name.split(' ')[1]+' \\u00b7 RL240';
      var c=collars.filter(function(q){return q[0]&&q[3]>0;})[200]||collars[0],x0=c[1]-offX,y0=c[2]-offY,s1=PL.act;
      plLine({x:x0,y:y0},{x:x0+40,y:y0});
      $('plBench').value='RL235';$('plSeq').value=1;PLS.baru();await W(200);
      for(var j=0;j<2;j++)for(var i=0;i<3;i++)plNew(x0+60+i*10,y0+40+j*10);plRefresh(true);
      $('plBench').value='RL240';$('plSeq').value=6;PLS.aktif(s1);plNew(x0+50,y0);plNew(x0+60,y0);plRefresh(true);
      if(VIEW2D)toggle2D();PT.open['db']=1;PT.open['db.plan']=1;PT.render(true);PT.select('db.plan.'+s1);await W(900);
      var r=document.querySelector('.ptr[data-id="db.plan"]');if(r)r.scrollIntoView({block:'center'});
      return PL.sets.map(function(s){return [s.name,s.h.length,s.h.map(function(h){return h.n;}).join(' ')];});})()""")
    pg.wait_for_timeout(1200)
    pg.screenshot(path=IMG + '88_plan_set.png', clip={'x': 0, 'y': 0, 'width': 480, 'height': 940}); print('shot 88_plan_set.png')
    # peta plan (2D): plan aktif magenta tegas, plan lain pudar; diperbesar ke area plan
    pg.evaluate("""(function(){drawOpen('plan');var A=[];PL.sets.forEach(function(s){s.h.forEach(function(h){A.push(h);});});
      var x0=1e18,x1=-1e18,y0=1e18,y1=-1e18;A.forEach(function(h){x0=Math.min(x0,h.x);x1=Math.max(x1,h.x);y0=Math.min(y0,h.y);y1=Math.max(y1,h.y);});
      var c=document.getElementById('drawCv');DRW.cx=(x0+x1)/2;DRW.cy=(y0+y1)/2;DRW.s=Math.min(c.clientWidth/(x1-x0+160),(c.clientHeight-50)/(y1-y0+160));drawRender();})()""")
    pg.wait_for_timeout(1500)
    pg.screenshot(path=IMG + '89_plan_peta.png', clip={'x': 480, 'y': 50, 'width': 1120, 'height': 860}); print('shot 89_plan_peta.png')
    ctx.close()
nf = IMG + 'notes.json'; N = json.load(open(nf, encoding='utf-8')); N['planSet'] = r
json.dump(N, open(nf, 'w', encoding='utf-8'), ensure_ascii=False, indent=1); print(r)
