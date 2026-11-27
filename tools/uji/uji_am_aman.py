"""Uji digitasi as-mined yang aman + menu titik tiga hapus (BM 0.24.116; pemilik 27 Nov 2026).
Kasus: poligon as-mined yang didigit berubah menjadi dig block (flitch belum punya dig block).
A1 tombol Digit poligon as-mined: Project Tree TETAP di panel As-Mined (dulu pindah ke panel dig block fl.2d)
A2 tutup dengan klik titik pertama -> poligon as-mined, BUKAN dig block
A3 tutup dengan Enter -> poligon as-mined tertutup (dulu dibuang diam-diam)
A4 panel dig block yang terbuka saat mendigit as-mined menampilkan pita peringatan
A5 Mulai dig block dari panel Dig Block tetap menghasilkan dig block (tanpa regresi)
A6 menu titik tiga: 'Pindahkan ke As-Mined' memindah dig block menjadi poligon as-mined
A7 menu titik tiga poligon as-mined: 'Hapus poligon as-mined' menghapusnya
A8 menu titik tiga 'Aktual': hapus semua as-mined satu flitch; tanpa galat
A9 laporan harian: poligon bertanggal sama di DUA flitch berbeda ikut terlapor; tanggal lain tidak
Pakai: python tools/uji/uji_am_aman.py"""
import sys
sys.argv = ['x', 'app']
from pathlib import Path
exec(open(Path(__file__).resolve().parent / 'uji_palet.py', encoding='utf-8').read().split('with sync_playwright() as pw:')[0])
gagal = []
def cek(nama, ok, info=''):
    print(('  ok   ' if ok else '  GAGAL ') + nama + ('  ' + str(info)[:250] if info else ''))
    if not ok: gagal.append(nama)
ST = "(()=>({db:DG.S.filter(s=>s.db).length,am:amD().bnd.length,on:DG.on,digOn:AM.digOn,sel:PT.sel,pita:!!document.getElementById('amaPita')}))()"
NODE = "((re)=>{var o=null;(function w(L){(L||[]).forEach(function(n){if(!o&&new RegExp(re).test(n.id))o=n;if(n.kids)w(typeof n.kids==='function'?n.kids():n.kids);});})(PT.nodes);return o})"
def menu(pg, pre, teks):
    return pg.evaluate("""((pre,t)=>{var hit=null;(function w(L){(L||[]).forEach(function(n){if(hit)return;if(n.id&&n.id.indexOf(pre)===0&&typeof n.menu==='function'){var m=n.menu().filter(function(x){return x&&x.t&&x.t.indexOf(t)===0})[0];if(m)hit=m;}if(n.kids)w(typeof n.kids==='function'?n.kids():n.kids);});})(PT.nodes);if(!hit)return 'tanpa item';hit.fn();return 'ok'})(%r,%r)""" % (pre, teks))
def poligon(pg, dx0, tutup='klik'):
    pts = pg.evaluate("""((d)=>{var A=dgAx(),g=document.getElementById('plotDiv').getBoundingClientRect();var xr=A.x.range,yr=A.y.range;
      var cx=(xr[0]+xr[1])/2+d,cy=(yr[0]+yr[1])/2,s=(xr[1]-xr[0])/14;
      return [[cx,cy],[cx+s,cy],[cx+s,cy+s],[cx,cy+s]].map(p=>[g.left+A.x._offset+A.x.d2p(p[0]),g.top+A.y._offset+A.y.d2p(p[1])])})(%s)""" % dx0)
    for x, y in pts: pg.mouse.click(x, y); pg.wait_for_timeout(200)
    if tutup == 'klik': pg.mouse.click(*pts[0])
    else: pg.keyboard.press('Enter')
    pg.wait_for_timeout(900)
with sync_playwright() as pw:
    b = pw.chromium.launch(args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader"])
    srv, P = server(ROOT / 'app' / 'index.html'); pg = b.new_page(viewport={'width': 1600, 'height': 900}); pg.on('dialog', lambda x: x.accept())
    err = []; pg.on('pageerror', lambda e: err.append(str(e)[:200]))
    muat(pg, P, TUNGGU); pg.wait_for_timeout(1000)
    pg.evaluate("PT.select('am.3');0"); pg.wait_for_timeout(800)
    pg.click("#amBody button:has-text('Digit poligon as-mined')"); pg.wait_for_timeout(1500); s = pg.evaluate(ST)
    cek('A1 panel tetap As-Mined saat mendigit', s['on'] and s['digOn'] and s['sel'] == 'am.3', s)
    poligon(pg, 0); s = pg.evaluate(ST)
    cek('A2 klik titik pertama -> as-mined, bukan dig block', s['am'] == 1 and s['db'] == 0 and s['sel'] == 'am.3', s)
    pg.click("#amBody button:has-text('Digit poligon as-mined')"); pg.wait_for_timeout(1200)
    poligon(pg, -40, 'enter'); s = pg.evaluate(ST)
    cek('A3 Enter -> poligon as-mined tertutup', s['am'] == 2 and s['db'] == 0, s)
    pg.click("#amBody button:has-text('Digit poligon as-mined')"); pg.wait_for_timeout(1000)
    pg.evaluate("PT.select('dig.man');0"); pg.wait_for_timeout(1000); s = pg.evaluate(ST)
    cek('A4 panel dig block menampilkan pita "Sedang mendigit poligon AS-MINED"', s['pita'], s)
    pg.keyboard.press('Escape'); pg.wait_for_timeout(500)
    pg.evaluate("PT.select('dig.man');0"); pg.wait_for_timeout(900)
    pg.evaluate("dbDig();0"); pg.wait_for_timeout(1200)
    poligon(pg, 40); s = pg.evaluate(ST)
    cek('A5 Mulai dig block -> dig block (tanpa regresi)', s['db'] == 1 and s['am'] == 2 and not s['pita'], s)
    pg.evaluate("PT.render(true);0"); pg.wait_for_timeout(600)
    r = ''
    r6 = menu(pg, 'dig.fl.', 'Pindahkan ke As-Mined'); pg.wait_for_timeout(1500); s = pg.evaluate(ST)
    cek('A6 Pindahkan ke As-Mined: dig block -> poligon as-mined', r6 == 'ok' and s['db'] == 0 and s['am'] == 3, [r, r6, s])
    pg.evaluate("PT.render(true);0"); pg.wait_for_timeout(600)
    r7 = menu(pg, 'am.fl.', 'Hapus poligon as-mined'); pg.wait_for_timeout(800); s = pg.evaluate(ST)
    cek('A7 titik tiga: Hapus poligon as-mined', r7 == 'ok' and s['am'] == 2, [r7, s])
    pg.evaluate("PT.render(true);0"); pg.wait_for_timeout(600)
    r8 = menu(pg, 'am.fl.', 'Hapus semua poligon as-mined'); pg.wait_for_timeout(800); s = pg.evaluate(ST)
    cek('A8 titik tiga Aktual: hapus semua as-mined di flitch; tanpa galat', r8 == 'ok' and s['am'] == 0 and not err, [r8, s, err[:2]])
    a9 = pg.evaluate("""(()=>{var D=amD(),B=lyBench(),h=B[0]-B[1],x=BX.m.x[0],y=BX.m.y[0];
      var mk=function(id,dt,k){return{id:id,name:id,top:B[0]-k*h,bot:B[1]-k*h,pts:[[x,y],[x+10,y],[x+10,y+10]],key:id,on:true,date:dt,shift:'DS',st:{n:1,t:100,v:40,gA:1}}};
      D.bnd=[mk('p1','2026-11-26',0),mk('p2','2026-11-26',2),mk('p3','2026-11-25',0)];
      AMK.f.mode='hari';AMK.f.date='2026-11-26';AMK.f.shift='';var R=AMK.rows().map(function(I){return I.x.id}).sort();return R})()""")
    cek('A9 laporan harian 26-Nov: poligon tanggal itu dari semua flitch, tanggal lain tidak', a9 == ['p1', 'p2'], a9)
    b.close(); srv.terminate()
print('LULUS' if not gagal else 'GAGAL: %s' % gagal); sys.exit(1 if gagal else 0)
