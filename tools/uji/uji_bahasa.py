"""Uji pemilih bahasa GC-Ex (bahasa.js, pemilik 19 Nov 2026).
B1 pemilih ada di panel Tampilan (#gxLang) dengan 5 bahasa, bawaan Bahasa Indonesia
B2 tiap bahasa menerjemahkan teks menu/tombol/judul (>= 60% teks yang ada di kamus ikut berganti), tanpa error halaman
B3 kembali ke Indonesia memulihkan seluruh teks halaman persis seperti semula
B4 pilihan tersimpan (localStorage) dan dipakai lagi setelah muat ulang
B5 isi data tidak tersentuh: nilai <option value> sama sebelum/sesudah
B6 en-US memakai ejaan Amerika (Color), en-GB ejaan Inggris (Colour)
Pakai: python tools/uji/uji_bahasa.py app|app-dh
"""
import sys
app = sys.argv[1] if len(sys.argv) > 1 else 'app'; sys.argv = ['x', app]
from pathlib import Path
exec(open(Path(__file__).resolve().parent / 'uji_palet.py', encoding='utf-8').read().split('with sync_playwright() as pw:')[0])
gagal = []
def cek(nama, ok, info=''):
    print(('  ok   ' if ok else '  GAGAL ') + nama + ('  ' + str(info) if info else ''))
    if not ok: gagal.append(nama)
TEKS = "(()=>document.body.innerText)()"
H4 = "(()=>{var h=document.querySelector('#gxPal h4');return h?h.textContent:'';})()"
VAL = "(()=>[...document.querySelectorAll('option')].map(o=>o.value).join('|'))()"
CAKUP = r"""(()=>{var K=window.GXLANG_KAMUS,n=0,t=0;document.querySelectorAll('button,label,option,h3,h4,summary,th').forEach(function(e){var s=GXLANG.asli(e).replace(/^[^0-9A-Za-zÀ-ɏ(\[]*/,'').replace(/[\s:….▾→]*$/,'');if(!s||!K[s])return;t++;var now='';e.childNodes.forEach(function(c){if(c.nodeType===3)now+=c.nodeValue;});if(now.indexOf(s)<0)n++;});return [n,t];})()"""
with sync_playwright() as pw:
    b = pw.chromium.launch(args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader"])
    srv, P = server(ROOT / app / 'index.html'); pg = b.new_page(viewport={'width': 1500, 'height': 860}); pg.on('dialog', lambda x: x.accept())
    err = []; pg.on('pageerror', lambda e: err.append(str(e)))
    muat(pg, P, TUNGGU)
    d = pg.evaluate("GXLANG.daftar().map(function(x){return x.k})")
    cek('B1 pemilih 5 bahasa, bawaan id', d == ['id', 'en-GB', 'en-US', 'es', 'su'] and pg.evaluate("GXLANG.aktif()") == 'id' and pg.evaluate("!!document.getElementById('gxLangSel')"), d)
    t0, v0 = pg.evaluate(TEKS), pg.evaluate(VAL)
    for k in ['en-GB', 'en-US', 'es', 'su']:
        pg.evaluate("(k)=>GXLANG.pakai(k)", k); pg.wait_for_timeout(500)
        n, t = pg.evaluate(CAKUP)
        cek('B2 %s menerjemahkan %d/%d teks berkamus' % (k, n, t), t > 50 and n >= 0.6 * t)
        if k == 'en-GB': cek('B6 en-GB "Colour palette"', 'Colour palette' in pg.evaluate(H4))
        if k == 'en-US': cek('B6 en-US "Color palette"', 'Color palette' in pg.evaluate(H4))
        pg.screenshot(path='/tmp/bahasa_%s_%s.png' % (app, k))
    cek('B5 nilai option tidak berubah', pg.evaluate(VAL) == v0)
    pg.evaluate("GXLANG.pakai('id')"); pg.wait_for_timeout(500)
    t1 = pg.evaluate(TEKS)
    cek('B3 kembali ke Indonesia = teks semula', t1 == t0, '' if t1 == t0 else [l for l in t1.split('\n') if l not in t0.split('\n')][:5])
    pg.evaluate("GXLANG.pakai('su')"); muat(pg, P, TUNGGU); pg.wait_for_timeout(800)
    cek('B4 tersimpan setelah muat ulang', pg.evaluate("GXLANG.aktif()") == 'su' and 'Palét warna' in pg.evaluate(H4), [pg.evaluate("GXLANG.aktif()"), pg.evaluate(H4)])
    pg.evaluate("GXLANG.pakai('id')")
    cek('B2 tanpa error halaman', not err, err[:3])
    b.close(); srv.terminate()
print('LULUS' if not gagal else 'GAGAL: %s' % gagal); sys.exit(1 if gagal else 0)
