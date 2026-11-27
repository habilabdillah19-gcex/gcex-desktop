"""Uji mode kerja Dig Block <-> As-Mined & "Nol & simpan" (mode_kerja.js, GC-Ex Block Model; pemilik 27 Nov 2026).
M1 tombol mode & Nol & simpan ada di bilah atas
M2 As-Mined: panel as-mined terbuka (bawaan am.3), folder Dig Block terlipat, poligon as-mined tampil
M3 Dig Block: kembali ke panel dig block TERAKHIR yang dipakai, folder As-Mined terlipat, poligon as-mined disembunyikan
M4 As-Mined lagi: kembali ke panel as-mined terakhir (am.1 yang dibuka sebelumnya)
M5 Nol & simpan: proyek disimpan, display 3D kosong + pesan; gambar ditahan selama kosong
M6 pilih mode / klik panel -> display digambar ulang
M7 pintasan Alt+1 / Alt+2; tanpa galat halaman
Pakai: python tools/uji/uji_mode_kerja.py
"""
import sys
sys.argv = ['x', 'app']
from pathlib import Path
exec(open(Path(__file__).resolve().parent / 'uji_palet.py', encoding='utf-8').read().split('with sync_playwright() as pw:')[0])
gagal = []
def cek(nama, ok, info=''):
    print(('  ok   ' if ok else '  GAGAL ') + nama + ('  ' + str(info)[:250] if info else ''))
    if not ok: gagal.append(nama)
ST = "(()=>({sel:PT.sel,dig:!!PT.open.dig,am:!!PT.open.am,amShow:!!(window.AM&&AM.show),n:(document.getElementById('plotDiv').data||[]).length,nol:MODEKERJA.aktif(),ov:!!document.getElementById('gxNolOv'),on:[].map.call(document.querySelectorAll('#gxMode .seg button.on'),function(b){return b.getAttribute('data-mode')}).join()}))()"
with sync_playwright() as pw:
    b = pw.chromium.launch(args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader"])
    srv, P = server(ROOT / 'app' / 'index.html'); pg = b.new_page(viewport={'width': 1600, 'height': 900}); pg.on('dialog', lambda x: x.accept())
    err = []; pg.on('pageerror', lambda e: err.append(str(e)[:200]))
    muat(pg, P, TUNGGU); pg.wait_for_timeout(1500)
    cek('M1 tombol mode & Nol & simpan di bilah atas', pg.evaluate("!!document.querySelector('#top #gxMode [data-mode=dig]')&&!!document.getElementById('gxNol')"))
    pg.evaluate("PT.select('dig.man');0"); pg.wait_for_timeout(800)
    pg.click('#gxMode [data-mode=am]'); pg.wait_for_timeout(1500); s = pg.evaluate(ST)
    cek('M2 As-Mined: am.3, folder Dig Block terlipat, poligon as-mined tampil', s['sel'] == 'am.3' and s['am'] and not s['dig'] and s['amShow'] and s['on'] == 'am', s)
    pg.evaluate("document.querySelector('#ptree .ptr[data-id=\"am.1\"] .ptl').click();0"); pg.wait_for_timeout(800)
    pg.click('#gxMode [data-mode=dig]'); pg.wait_for_timeout(1500); s = pg.evaluate(ST)
    cek('M3 Dig Block: kembali ke panel terakhir (dig.man), As-Mined terlipat, poligon disembunyikan', s['sel'] == 'dig.man' and s['dig'] and not s['am'] and not s['amShow'] and s['on'] == 'dig', s)
    pg.click('#gxMode [data-mode=am]'); pg.wait_for_timeout(1200); s = pg.evaluate(ST)
    cek('M4 As-Mined lagi: kembali ke am.1', s['sel'] == 'am.1' and s['amShow'], s)
    n0 = s['n']
    pg.evaluate("window._sv=0;var f=SA.saveNow;SA.saveNow=function(){window._sv++;return f.apply(this,arguments);};0")
    pg.click('#gxNol'); pg.wait_for_timeout(2500); s = pg.evaluate(ST)
    pg.evaluate("updatePlot();0"); pg.wait_for_timeout(500); s2 = pg.evaluate(ST)
    cek('M5 Nol & simpan: tersimpan, display kosong + pesan, gambar ditahan', pg.evaluate("window._sv") == 1 and s['n'] == 0 and s['nol'] and s['ov'] and s2['n'] == 0, [s, n0])
    pg.click('#gxNolOv [data-m=dig]'); pg.wait_for_timeout(2500); s = pg.evaluate(ST)
    ok6a = s['n'] > 0 and not s['nol'] and not s['ov'] and s['sel'] == 'dig.man'
    pg.click('#gxNol'); pg.wait_for_timeout(1500)
    pg.evaluate("document.querySelector('#ptree .ptr[data-id=\"bm\"] .ptl').click();0"); pg.wait_for_timeout(2500); s = pg.evaluate(ST)
    cek('M6 pilih mode / klik panel -> display digambar ulang', ok6a and s['n'] > 0 and not s['nol'], s)
    pg.mouse.click(900, 500); pg.keyboard.press('Alt+2'); pg.wait_for_timeout(1200); a = pg.evaluate(ST)
    pg.keyboard.press('Alt+1'); pg.wait_for_timeout(1200); d = pg.evaluate(ST)
    cek('M7 Alt+2 / Alt+1; tanpa galat', a['on'] == 'am' and d['on'] == 'dig' and not err, [a['sel'], d['sel'], err[:2]])
    pg.screenshot(path='/tmp/mode_kerja.png', clip={'x': 0, 'y': 0, 'width': 1600, 'height': 120})
    b.close(); srv.terminate()
print('LULUS' if not gagal else 'GAGAL: %s' % gagal); sys.exit(1 if gagal else 0)
