"""Uji block model terotasi (bmrot.js, BM 0.24.112; pemilik 22 Nov 2026).
Model CSV lokal 8 x 6 x 3 blok (5 x 5 x 2,5 m) diimpor lewat dialog Import block model dengan Bearing 120 (Surpac:
azimuth sumbu X model; 90 = tidak diputar).
R1 mode 'lokal': pusat blok = titik putar + dx*ex + dy*ey (ex = (sin b, cos b), ey = (-cos b, sin b)); m.rot tersimpan
R2 volume total & jumlah blok sama dengan model tak terotasi
R3 slab vertikal setebal 1 m tegak lurus sumbu Y model, di tengah satu baris -> tepat 1 baris (8 x 3 blok)
R4 kubus 3D: semua titik sudut, dikembalikan ke kerangka lokal, jatuh di grid 5 m (tidak sejajar sumbu lapangan)
R5 sayatan denah: poligon blok miring searah sumbu X model
R6 alat berbasis grid (dig block otomatis) dicegat dengan pesan, bukan angka salah
R7 mode 'dunia': koordinat file tidak berubah, hanya arah blok; R8 bearing 90 = tanpa rotasi
R9 panel menampilkan keterangan rotasi; tanpa error halaman
Pakai: python tools/uji/uji_bm_rotasi.py
"""
import sys, math
sys.argv = ['x', 'app']
from pathlib import Path
exec(open(Path(__file__).resolve().parent / 'uji_palet.py', encoding='utf-8').read().split('with sync_playwright() as pw:')[0])
gagal = []
def cek(nama, ok, info=''):
    print(('  ok   ' if ok else '  GAGAL ') + nama + ('  ' + str(info) if info else ''))
    if not ok: gagal.append(nama)
NX, NY, NZ, S, SZ, X0, Y0, Z0 = 8, 6, 3, 5.0, 2.5, 504700.0, 9011750.0, 200.0
rows = ['XC,YC,ZC,AU']
for k in range(NZ):
    for j in range(NY):
        for i in range(NX):
            rows.append('%.3f,%.3f,%.3f,%.3f' % (X0 + S / 2 + S * i, Y0 + S / 2 + S * j, Z0 + SZ / 2 + SZ * k, 0.1 * (i + j + k)))
CSV = '\n'.join(rows)
IMPOR = r"""async (a)=>{var csv=a[0],b=a[1],mode=a[2];var f=new File([csv],'rot_uji.csv',{type:'text/csv'});bxDlg();await bxDlgFile(f);
  var set=function(id,v){var e=document.getElementById(id);e.value=v;e.dispatchEvent(new Event('change'));};
  set('bxsx','-1');set('bxsy','-1');set('bxsz','-1');set('bxrb',String(b));set('bxrm',mode);await bxDlgGo();
  var m=BX.m;return {n:m.n,rot:m.rot||null,x:Array.from(m.x),y:Array.from(m.y),z:Array.from(m.z),sx:Array.from(m.sx),sy:Array.from(m.sy),sz:Array.from(m.sz),info:(document.getElementById('bxInfo')||{}).innerText||''};}"""
b = 120.0; r = math.radians(b); ex = (math.sin(r), math.cos(r)); ey = (-math.cos(r), math.sin(r))
with sync_playwright() as pw:
    br = pw.chromium.launch(args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader"])
    srv, P = server(ROOT / 'app' / 'index.html'); pg = br.new_page(viewport={'width': 1500, 'height': 860})
    pesan = []; pg.on('dialog', lambda d: (pesan.append(d.message), d.accept()))
    err = []; pg.on('pageerror', lambda e: err.append(str(e)))
    muat(pg, P, TUNGGU)
    M = pg.evaluate(IMPOR, [CSV, b, 'lokal'])
    n = NX * NY * NZ; e = 0.0
    for q in range(n):
        i, j = q % NX, (q // NX) % NY
        dx, dy = S / 2 + S * i, S / 2 + S * j
        wx, wy = X0 + dx * ex[0] + dy * ey[0], Y0 + dx * ex[1] + dy * ey[1]
        e = max(e, abs(M['x'][q] - wx), abs(M['y'][q] - wy))
    cek('R1 pusat blok diputar benar (galat maks %.2e m), m.rot.b=%s' % (e, M['rot'] and M['rot']['b']), M['n'] == n and e < 1e-6 and M['rot'] and abs(M['rot']['b'] - 120) < 1e-9)
    vol = sum(M['sx'][q] * M['sy'][q] * M['sz'][q] for q in range(n))
    cek('R2 volume total %.1f m3 = %d x 5 x 5 x 2,5' % (vol, n), abs(vol - n * S * S * SZ) < 1e-6)
    # R3: slab tegak lurus ey melalui pusat baris j=2, tebal 1 m
    j = 2; cx, cy = X0 + (S / 2) * ex[0] + (S / 2 + S * j) * ey[0], Y0 + (S / 2) * ex[1] + (S / 2 + S * j) * ey[1]
    nsel = pg.evaluate("""(a)=>{var K=[{n:[a[2],a[3],0],c:[a[0]-offX,a[1]-offY,0],lo:-0.5,hi:0.5}],c=0;for(var i=0;i<BX.m.n;i++)if(bxSlabHit(i,K))c++;return c;}""", [cx, cy, ey[0], ey[1]])
    cek('R3 slab 1 m tegak lurus sumbu Y model memilih %d blok (harus %d = 1 baris)' % (nsel, NX * NZ), nsel == NX * NZ)
    V = pg.evaluate("""()=>{var T=[];bxTraces(T,{});var o=[];T.forEach(function(t){if(t.type==='mesh3d')for(var i=0;i<t.x.length;i++)o.push([t.x[i]+offX,t.y[i]+offY]);});return o;}""")
    def lok(p): dx, dy = p[0] - X0, p[1] - Y0; return dx * ex[0] + dy * ex[1], dx * ey[0] + dy * ey[1]
    eg = max((min(abs(c / S - round(c / S)) for _ in [0]) for p in V for c in lok(p)), default=1) * S if V else 1
    cek('R4 %d titik sudut kubus 3D di grid lokal 5 m (galat maks %.2e m)' % (len(V), eg), len(V) > 0 and eg < 1e-4)
    P2 = pg.evaluate("""()=>{var T=bxTraces2D({K:[{n:[0,0,1],c:[0,0,0],lo:201,hi:201}],g:{m:'H',u:[1,0,0]}},function(x,y,z){return[x,y];});var t=T.filter(function(t){return t.fill==='toself';})[0];return t?[Array.from(t.x).slice(0,6),Array.from(t.y).slice(0,6)]:null;}""")
    ok5 = False
    if P2:
        ux, uy = P2[0][1] - P2[0][0], P2[1][1] - P2[1][0]; L = math.hypot(ux, uy); ok5 = abs(L - S) < 1e-6 and abs(ux / L - ex[0]) < 1e-6 and abs(uy / L - ex[1]) < 1e-6
    cek('R5 denah 2D: sisi blok searah sumbu X model', ok5, P2 and [round(v, 3) for v in P2[0][:3]])
    pesan.clear(); pg.evaluate("dbAuto();0"); pg.wait_for_timeout(300)
    dlg = pg.evaluate("(document.getElementById('gcgDlg')||{}).innerText||''"); pg.evaluate("window.GCG&&GCG.close?GCG.close():(document.getElementById('gcgDlg')&&document.getElementById('gcgDlg').remove());0")
    cek('R6 dig block otomatis dicegat dengan pesan', any('terotasi' in s for s in pesan) or 'terotasi' in dlg, (pesan or [dlg])[:1])
    cek('R9 panel menampilkan keterangan rotasi', 'bearing 120' in M['info'], M['info'][-120:])
    M2 = pg.evaluate(IMPOR, [CSV, b, 'dunia'])
    cek('R7 mode dunia: koordinat tidak berubah, rotasi tercatat', abs(M2['x'][0] - (X0 + S / 2)) < 1e-9 and abs(M2['y'][7] - (Y0 + S / 2)) < 1e-9 and M2['rot'] and M2['rot']['mode'] == 'dunia')
    M3 = pg.evaluate(IMPOR, [CSV, 90, 'lokal'])
    cek('R8 bearing 90 = tanpa rotasi', M3['rot'] is None and abs(M3['x'][0] - (X0 + S / 2)) < 1e-9)
    cek('R9 tanpa error halaman', not err, err[:3])
    import os
    if os.environ.get('GAMBAR'):
        pg.evaluate(IMPOR, [CSV, b, 'lokal']); pg.evaluate("(()=>{var a=document.getElementById('bxAttr');if(a){a.value='AU';a.dispatchEvent(new Event('change'));}if(window.setView)setView('top');updatePlot();})()"); pg.wait_for_timeout(2500)
        pg.screenshot(path='/tmp/bm_rotasi.png')
    br.close(); srv.terminate()
print('LULUS' if not gagal else 'GAGAL: %s' % gagal); sys.exit(1 if gagal else 0)
