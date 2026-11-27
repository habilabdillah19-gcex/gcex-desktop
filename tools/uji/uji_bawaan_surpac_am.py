"""Uji setelan BAWAAN panel 'Flitch, poligon, lantai & atap' = cara Surpac (BM 0.24.116; pemilik 27 Nov 2026).
S1 proyek baru (belum ada poligon as-mined): Volume = lantai pick-up (TIN), Atap = permukaan pick-up (TIN), boundary = menurut elevasi string
S2 proyek lama (sudah ada poligon, pilihan belum pernah disimpan): tetap rumus lama (tebal flitch penuh, RL atas nominal, flitch aktif)
S3 pilihan yang sudah disimpan tidak ditimpa
S4 string 2D (semua Z = 0) dengan bawaan 'menurut elevasi' tetap masuk flitch aktif, tidak terlempar ke RL 0
S5 opsi Surpac tampil paling atas & terpilih di panel; tanpa galat
Pakai: python tools/uji/uji_bawaan_surpac_am.py"""
import sys
sys.argv = ['x', 'app']
from pathlib import Path
exec(open(Path(__file__).resolve().parent / 'uji_palet.py', encoding='utf-8').read().split('with sync_playwright() as pw:')[0])
gagal = []
def cek(nama, ok, info=''):
    print(('  ok   ' if ok else '  GAGAL ') + nama + ('  ' + str(info)[:250] if info else ''))
    if not ok: gagal.append(nama)
RESET = "(function(bnd,simpan){var U=BX.ui;U.amData={sets:{},bnd:bnd?[{id:'x',name:'X',pts:[[0,0],[1,0],[1,1]],top:1,bot:0,on:true}]:[]};AM.D=null;var r=(U.am=U.am||{});r.reg=simpan||{};var R=amR();return{f:R.floor,r:R.roof,z:R.bndZ,s:R.sdef,m:amRoofMode()}})"
with sync_playwright() as pw:
    b = pw.chromium.launch(args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader"])
    srv, P = server(ROOT / 'app' / 'index.html'); pg = b.new_page(viewport={'width': 1600, 'height': 900}); pg.on('dialog', lambda x: x.accept())
    err = []; pg.on('pageerror', lambda e: err.append(str(e)[:200]))
    muat(pg, P, TUNGGU); pg.wait_for_timeout(1000)
    s = pg.evaluate(RESET + "(false,null)")
    cek('S1 proyek baru = cara Surpac', s['f'] == 'pickup' and s['r'] == 'pickup' and s['z'] == 'auto' and s['m'] == 'pickup', s)
    s = pg.evaluate(RESET + "(true,null)")
    cek('S2 proyek lama tetap rumus lama', s['f'] == 'flitch' and s['r'] == 'flitch' and s['z'] == 'active', s)
    s = pg.evaluate(RESET + "(false,{floor:'flitch',roof:'flat',bndZ:'active'})")
    cek('S3 pilihan tersimpan tidak ditimpa', s['f'] == 'flitch' and s['r'] == 'flat' and s['z'] == 'active', s)
    s4 = pg.evaluate("""(()=>{var r=BX.ui.am.reg={};amR();var B=lyBench(),D=amD();var n0=D.bnd.length;
      amBndAdd([[BX.m.x[0],BX.m.y[0],0],[BX.m.x[0]+20,BX.m.y[0],0],[BX.m.x[0]+20,BX.m.y[0]+20,0]],'DUA_D');var o=D.bnd[D.bnd.length-1];
      return{z:amR().bndZ,top:o.top,bot:o.bot,B:B,n:D.bnd.length-n0}})()""")
    cek('S4 string 2D (Z=0) masuk flitch aktif', s4['z'] == 'auto' and s4['n'] == 1 and abs(s4['top'] - s4['B'][0]) < 1e-6 and abs(s4['bot'] - s4['B'][1]) < 1e-6, s4)
    pg.evaluate(RESET + "(false,null)"); pg.evaluate("PT.select('am.3');amPanel();0"); pg.wait_for_timeout(800)
    s5 = pg.evaluate("""(()=>{var S=[].slice.call(document.querySelectorAll('#amBody select'));var g=function(re){var e=S.filter(function(x){return [].some.call(x.options,function(o){return re.test(o.text)})})[0];return e?{v:e.value,f:e.options[0].text}:null};
      return{roof:g(/RL atas flitch \\(nominal/),vol:g(/Tebal flitch penuh/),bnd:g(/Flitch aktif \\(abaikan/)}})()""")
    cek('S5 opsi Surpac di atas & terpilih; tanpa galat', s5['roof'] and s5['roof']['v'] == 'pickup' and 'Surpac' in s5['roof']['f'] and s5['vol']['v'] == 'pickup' and 'Surpac' in s5['vol']['f'] and s5['bnd']['v'] == 'auto' and 'Surpac' in s5['bnd']['f'] and not err, [s5, err[:2]])
    b.close(); srv.terminate()
print('LULUS' if not gagal else 'GAGAL: %s' % gagal); sys.exit(1 if gagal else 0)
