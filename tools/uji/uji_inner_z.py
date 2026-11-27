"""Uji string ganda / flagging sejajar dengan string induk (BM 0.24.116; pemilik 27 Nov 2026).
Kasus: di Surpac string flagging tampil DI BAWAH string utama dig block (selisih setengah tebal flitch).
Z1 data lama: induk tanpa s.db di tengah flitch, string ganda di RL bawah -> setelah dimuat, Z string ganda = Z induk
Z2 bentuk string ganda (X, Y) tidak berubah -- tetap shrinkage
Z3 ekspor STR teks: semua titik induk & string ganda ber-Z sama
Z4 string ganda yang dibuat baru oleh dbInner ikut Z induk; induk ber-s.db (RL bawah) tetap di RL bawah; tanpa galat
Pakai: python tools/uji/uji_inner_z.py"""
import sys, re
sys.argv = ['x', 'app']
from pathlib import Path
exec(open(Path(__file__).resolve().parent / 'uji_palet.py', encoding='utf-8').read().split('with sync_playwright() as pw:')[0])
gagal = []
def cek(nama, ok, info=''):
    print(('  ok   ' if ok else '  GAGAL ') + nama + ('  ' + str(info)[:250] if info else ''))
    if not ok: gagal.append(nama)
with sync_playwright() as pw:
    b = pw.chromium.launch(args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader"])
    srv, P = server(ROOT / 'app' / 'index.html'); pg = b.new_page(viewport={'width': 1600, 'height': 900}); pg.on('dialog', lambda x: x.accept())
    err = []; pg.on('pageerror', lambda e: err.append(str(e)[:200]))
    muat(pg, P, TUNGGU); pg.wait_for_timeout(800)
    s = pg.evaluate("""(()=>{if(!dbFlOn())lyApply();var B=lyBench(),mid=(B[0]+B[1])/2,x=BX.m.x[0]-offX,y=BX.m.y[0]-offY;
      DG.S=[{no:17,d:'HG',id:'m1',closed:true,vis:true,col:'#f00',pl:{m:'H',pos:mid,thick:B[0]-B[1]},pts:[[x,y,mid],[x+20,y,mid],[x+20,y+20,mid],[x,y+20,mid]]},
            {no:17,d:'HG',id:'i1',inner:true,parent:'m1',closed:true,vis:true,col:'#000',db:{top:B[0],bot:B[1]},pts:[[x+0.5,y+0.5,B[1]],[x+19.5,y+0.5,B[1]],[x+19.5,y+19.5,B[1]],[x+0.5,y+19.5,B[1]]]}];
      dgList();return {B:B,mid:mid}})()""")
    pg.wait_for_timeout(400)
    z = pg.evaluate("DG.S.map(function(s){return s.pts.map(function(q){return +q[2]})})")
    cek('Z1 data lama: string ganda naik ke Z induk', all(abs(v - s['mid']) < 1e-6 for v in z[1]), z)
    xy = pg.evaluate("DG.S[1].pts.map(function(q){return [q[0]-DG.S[0].pts[0][0],q[1]-DG.S[0].pts[0][1]]})")
    cek('Z2 bentuk shrinkage tetap', xy == [[0.5, 0.5], [19.5, 0.5], [19.5, 19.5], [0.5, 19.5]], xy)
    pg.evaluate("DG.S[1].pts.forEach(function(q){q[2]=lyBench()[1]});window._dl=[];window.dgDl=function(t,f){_dl.push(t)};lyU().sel={};dbExport('strt');0")
    txt = pg.evaluate("(window._dl||[]).join('')")
    zs = set(round(float(m.split(',')[3]), 3) for m in txt.splitlines()[2:] if m and not m.startswith('0,'))
    cek('Z3 ekspor STR: induk & string ganda ber-Z sama', zs == {round(s['mid'], 3)}, [zs, txt[:160]])
    r = pg.evaluate("""(()=>{var B=lyBench(),x=BX.m.x[0]-offX,y=BX.m.y[0]-offY;var U=dbU();U.sfOn=true;
      var _lt=window.lyItems;window.lyItems=lyItems=function(){var L=_lt.apply(this,arguments);L.forEach(function(o){o.ton=o.ton||{};o.ton.sulf=true;});return L;};
      DG.S.push(dbTag({no:5,d:'ORE',id:'m2',closed:true,vis:true,col:'#0f0',pl:{m:'H'},pts:[[x+40,y,0],[x+60,y,0],[x+60,y+20,0],[x+40,y+20,0]]}));
      var n=dbInner(true);window.lyItems=lyItems=_lt;var g=function(id){return DG.S.filter(function(s){return s.inner&&s.parent===id})[0]};
      return {n:n,z1:g('m1')&&g('m1').pts[0][2],z2:g('m2')&&g('m2').pts[0][2],B:B}})()""")
    cek('Z4 dbInner baru ikut Z induk; induk RL bawah tetap; tanpa galat', r['z1'] is not None and abs(r['z1'] - s['mid']) < 1e-6 and abs(r['z2'] - r['B'][1]) < 1e-6 and not err, [r, err[:2]])
    b.close(); srv.terminate()
print('LULUS' if not gagal else 'GAGAL: %s' % gagal); sys.exit(1 if gagal else 0)
