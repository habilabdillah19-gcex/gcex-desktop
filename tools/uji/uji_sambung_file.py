"""Uji "Sambungkan file" (sambung.js, BM 0.24.114 / DH 0.24.116; pemilik 26 Nov 2026).
Proyek Block Model di folder disk (data latihan) lalu file block model sumber dipindah:
S1 dipindah ke subfolder dalam (arsip/2026/lama/) -> ditemukan otomatis tanpa jendela, block model utuh
S2 dipindah ke LUAR folder proyek -> jendela "Sambungkan file" muncul; pilih file -> block model utuh dan file disalin
   ke sumber/ dengan nama tercatat (isi identik)
S3 "Lewati" -> proyek tetap terbuka tanpa block model (perilaku lama) + peringatan
S4 file pilihan berbeda ukuran -> peringatan konfirmasi muncul sebelum dipakai
S5 tanpa galat halaman; dijalankan dari .html (file://)
Pakai: python tools/uji/uji_sambung_file.py
"""
import sys, os, shutil, tempfile, hashlib
from pathlib import Path
_P = Path(__file__).resolve().parent / 'uji_portabel_html.py'
exec(open(_P, encoding='utf-8').read().split('gagal = []')[0])
gagal = []
def cek(nama, ok, info=''):
    print(('  ok   ' if ok else '  GAGAL ') + nama + ('  ' + str(info)[:300] if info else ''))
    if not ok: gagal.append(nama)
def h(p): return hashlib.sha256(open(p, 'rb').read()).hexdigest()

with sync_playwright() as pw:
    br = pw.chromium.launch(args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader"])
    tmp = Path(tempfile.mkdtemp(prefix='gcex_sambung_')); html = tmp / 'GCEx_BlockModel.html'; html.write_bytes((ROOT / 'app' / 'index.html').read_bytes())
    D0 = tmp / 'asli'; D0.mkdir()
    srv, P = server(ROOT / 'app' / 'index.html')
    ctx = br.new_context(viewport={'width': 1500, 'height': 860}); pg = ctx.new_page(); pg.on('dialog', lambda d: d.accept('Uji') if d.type == 'prompt' else d.accept())
    pasang_fs(pg); muat(pg, P, "window.BX && BX.m"); pg.evaluate(SHIM); pg.evaluate("(d)=>FP.use(DiskDir(d))", str(D0))
    for _ in range(90):
        if list((D0 / 'sumber').glob('*')) if (D0 / 'sumber').exists() else []: break
        pg.wait_for_timeout(1000)
    pg.wait_for_timeout(3000); N0 = pg.evaluate("BX.m.n"); ctx.close(); srv.terminate()
    (D0 / 'gcex.lock').unlink(missing_ok=True)
    SRC = sorted((D0 / 'sumber').glob('*'))[0]; NM = SRC.name; H0 = h(SRC)
    print('    proyek: %d blok, sumber/%s' % (N0, NM))

    def buka(D, pilih=None, lewati=False):
        ctx = br.new_context(viewport={'width': 1500, 'height': 860}); pg = ctx.new_page(); err = []; dlg = []
        pg.on('pageerror', lambda x: err.append(str(x)[:200]))
        pg.on('dialog', lambda d: (dlg.append(d.message), d.accept('Uji') if d.type == 'prompt' else d.accept()))
        pasang_fs(pg); pg.goto(html.as_uri()); pg.wait_for_timeout(7000); pg.evaluate(SHIM)
        if pilih: pg.evaluate("""(p)=>{window.showOpenFilePicker=async function(){return [{getFile:function(){return fsRead(p).then(function(r){var b=atob(r[0]),u=new Uint8Array(b.length);for(var i=0;i<b.length;i++)u[i]=b.charCodeAt(i);return new File([u],p.split('/').pop(),{lastModified:r[1]});});}}];};return 0;}""", str(pilih))
        pg.evaluate("(d)=>{FP.use(DiskDir(d));return 0;}", str(D))
        sb = False
        for _ in range(120):
            if pg.evaluate("!!document.getElementById('gxSambung')"):
                sb = True; pg.wait_for_timeout(300)
                pg.click('#gxSbLewat' if lewati else '#gxSbCari'); break
            if pg.evaluate("!!(window.BX&&BX.m)"): break
            pg.wait_for_timeout(1000)
        try: pg.wait_for_function("window.BX && BX.m", timeout=60000 if not lewati else 8000)
        except Exception: pass
        pg.wait_for_timeout(5000)
        r = pg.evaluate("({n:window.BX&&BX.m?BX.m.n:0,toast:(document.getElementById('fpToast')||{}).innerText||''})")
        ctx.close(); return r, sb, dlg, err

    def salin(nama):
        D = tmp / nama; shutil.copytree(D0, D); return D
    # S1
    D = salin('s1'); dst = D / 'arsip' / '2026' / 'lama'; dst.mkdir(parents=True); shutil.move(str(D / 'sumber' / NM), dst / NM)
    r, sb, dlg, err = buka(D)
    cek('S1 subfolder dalam: ditemukan otomatis tanpa jendela (%d blok)' % r['n'], r['n'] == N0 and not sb and not err, [r['toast'][:120], err[:2]])
    # S2
    D = salin('s2'); luar = tmp / 'luar'; luar.mkdir(); shutil.move(str(D / 'sumber' / NM), luar / NM)
    r, sb, dlg, err = buka(D, pilih=luar / NM)
    kp = D / 'sumber' / NM
    cek('S2 di luar folder: jendela muncul, tersambung (%d blok), disalin ke sumber/ identik' % r['n'], sb and r['n'] == N0 and kp.exists() and h(kp) == H0 and not err, [sb, kp.exists(), r['toast'][:120], err[:2]])
    # S3
    D = salin('s3'); (D / 'sumber' / NM).unlink()
    r, sb, dlg, err = buka(D, lewati=True)
    cek('S3 Lewati: proyek terbuka tanpa block model + peringatan', sb and r['n'] == 0 and 'tidak ditemukan' in r['toast'] and not err, [r, err[:2]])
    # S4
    D = salin('s4'); (D / 'sumber' / NM).unlink(); lain = tmp / 'lain'; lain.mkdir(); (lain / NM).write_bytes(SRC.read_bytes() + b'\n')
    r, sb, dlg, err = buka(D, pilih=lain / NM)
    cek('S4 ukuran beda: peringatan konfirmasi sebelum dipakai', sb and any('berbeda' in m for m in dlg), dlg[:1])
    cek('S5 tanpa galat halaman', not err, err[:2])
    br.close(); shutil.rmtree(tmp, ignore_errors=True)
print('LULUS' if not gagal else 'GAGAL: %s' % gagal); sys.exit(1 if gagal else 0)
