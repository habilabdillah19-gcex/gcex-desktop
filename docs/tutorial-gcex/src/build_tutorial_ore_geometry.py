# -*- coding: utf-8 -*-
"""Menyusun 'Tutorial Ore Geometry Studio' (HTML -> PDF A4) untuk GC-Ex Drill Hole Ultimate 0.24.77.

Berbeda dengan build_tutorial_update.py, tutorial ini MEMAKAI tangkapan layar aplikasi: GC-Ex Drill Hole
(app-dh/index.html hasil build_dh.py) dijalankan di Chromium tanpa layar, data latihan simulasi dimuat
(tombol Demo), lalu setiap langkah Ore Geometry Studio dijalankan dan difoto. Semua angka di teks diambil
dari hasil hitungan aplikasi pada data latihan, jadi selalu cocok dengan yang dilihat pengguna.

Jalankan:  python web-src-dh/build_dh.py && python docs/tutorial-gcex/src/build_tutorial_ore_geometry.py
Hasil:     docs/tutorial-gcex/GCEx_Tutorial_Ore_Geometry_Studio.pdf
"""
import json
import os
import random
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

from playwright.sync_api import sync_playwright

import doc_gcex as D

HERE = Path(__file__).resolve().parent
TUT = HERE.parent
ROOT = TUT.parent.parent
DATA = TUT / 'data'
FIGD = HERE / 'fig_ogs'
PDF = TUT / 'GCEx_Tutorial_Ore_Geometry_Studio.pdf'
FIGD.mkdir(exist_ok=True)

W8 = "var W=function(ms){return new Promise(function(r){setTimeout(r,ms);});};"
LANGKAH = [
    # (nama berkas, JS sebelum foto, target foto, tunggu ms)
    ('01_panel', "uiTab('OG');", '#pOG', 800),
    ('02_data_lanjut', "ogsOpen('data');ogsFlag();ogsRender();", '#ogsWin', 1500),
    ('03_data_nol', "var col=VS.kolom().filter(function(c){return c.n==='Vein'&&c.src==='g';})[0];gmOpt('vsCol',col.key);gmOpt('vsGap',0);VS.terapkan(true);await W(600);imSync(true);await W(900);"
                    "ogsSrc().forEach(function(s){OGS.p.mesh[s.k]=s.k[0]==='i';});ogsOpen('data');ogsFlag();ogsRender();", '#ogsWin', 1800),
    ('04_geo', "ogsGo('geo');", '#ogsWin', 1500),
    ('05_kadar', "ogsGo('kadar');", '#ogsWin', 1200),
    ('06_ls', "ogsGo('ls');", '#ogsWin', 1800),
    ('07_env', "OGS.p.envDom=OGS.F.ref;ogsGo('env');", '#ogsWin', 4000),
    ('08_zon', "ogsGo('zon');", '#ogsWin', 1800),
    ('09_prof', "OGS.p.pfDom=String(OGS.F.ref);ogsGo('prof');", '#ogsWin', 1800),
    ('10_sec', "ogsGo('sec');await W(800);ogsSecUsul();", '#ogsWin', 2200),
    ('11_lama', "ogsGo('lama');await W(500);ogRunIc();", '#ogsWin', 1200),
    ('12_struk', "ogsGo('struk');await W(1500);var L=ogsIgL('struk');var u=L.filter(function(g){return g.usul;})[0];if(u){u.usul=false;u.nm='Pergeseran bidang (diterima)';u.col='#7048e8';u.dash='dash';}"
                 "L.push({id:'gT',nm:'Batas bawah GC (interpretasi)',typ:'line',pts:[[-300,215],[-100,205],[100,205],[300,200],[500,210]],col:'#e8590c',dash:'solid',leg:true,ket:'contoh'});"
                 "L.push({id:'gX',nm:'Cek dengan PDH',typ:'text',pts:[[150,140]],col:'#1971c2',dash:'solid',leg:false,ket:''});ogsRender();", '#ogsWin', 2200),
    ('13_par', "ogsGo('par');", '#ogsWin', 4500),
    ('14_jun', "ogsGo('jun');", '#ogsWin', 4500),
    ('15_tgt', "ogsGo('tgt');await W(800);ogsTgtUsul();", '#ogsWin', 2200),
    ('16_luar', "ogsGo('luar');", '#ogsWin', 2000),
    ('18_peta_ctrl', "ogsGo('peta');", '#ogsWin', 6000),
    ('18_peta', "var L=ogsIgL('peta');L.push({id:'pS',nm:'Struktur (contoh interpretasi)',typ:'line',pts:[[OGS.F.fr.c[0]+offX-150,OGS.F.fr.c[1]+offY+40],[OGS.F.fr.c[0]+offX+150,OGS.F.fr.c[1]+offY+190]],col:'#111111',dash:'solid',leg:true,ket:'contoh'});ogsRender();", '#ogsPT', 6000),
    ('17_lap', "ogsGo('lap');await W(600);OGS.p.lap.s.data.h='Lima lensa kuarsa sejajar, satu sistem vein';OGS.p.lap.s.rek={on:true,h:'Tiga tindakan untuk tim',t:'Revisi wireframe di sekitar pertemuan vein\\nUji target T1 dan T2 dari arah SE\\nLogging tekstur vein pada lubang baru'};ogsGo('lap');", '#ogsWin', 1200),
]
ANGKA = r"""(function(){var F=OGS.F,au=ogsEi(ogsAu()),V=ogsIn(F),T=F.I.map(function(c){return c.T;}),J=ogsJun(),L=ogsLuar(),d=F.dom[F.ref];
  return {dom:F.dom.map(function(x){return [x.nm,x.nI,ogsIn(F,F.dom.indexOf(x)).length];}),nI:F.I.length,nV:V.length,nHole:Object.keys(holeData).length,nA:F.n,
    ref:[d.nm,Math.round(d.pl.strike),Math.round(d.pl.dip),ogsArah(d.pl.ddir)],Tm:ogsMed(T),T10:ogsQ(T,0.1),T90:ogsQ(T,0.9),au:ogsWmean(F,au,V),
    kon:ogsMed(ogsVals(F,au,V))/ogsMed(ogsVals(F,au,ogsOut(F))),env:F.dom.map(function(x,q){var E=ogsEnv(q);return E?[x.nm,Math.round(E.vol),Math.round(E.ton)]:null;}).filter(Boolean),
    jun:[J.ss.n,J.sm.n,J.ss.gt,J.sm.gt,J.ss.au,J.sm.au],luar:L.map(function(r){return [r.nm,r.L.length];}),tgt:OGS.p.tgt.map(function(t){return t.nm;}),sec:OGS.p.sec.map(function(s){return [s.nm,s.ls];})};})()"""


def jalankan():
    port = str(random.randint(9100, 9899)); d = Path(tempfile.mkdtemp())
    (d / 'index.html').write_bytes((ROOT / 'app-dh' / 'index.html').read_bytes()); os.symlink(DATA, d / 'data-latihan')
    srv = subprocess.Popen([sys.executable, '-m', 'http.server', port], cwd=str(d), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    url = 'http://localhost:%s/index.html' % port
    for _ in range(50):
        try: urllib.request.urlopen(url, timeout=1); break
        except Exception: time.sleep(.4)
    err = []
    with sync_playwright() as pw:
        ctx = pw.chromium.launch_persistent_context(tempfile.mkdtemp(), args=['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'], viewport={'width': 1600, 'height': 950})
        ctx.add_init_script("window.showDirectoryPicker=async function(){throw new Error('batal');};")
        pg = ctx.new_page(); pg.on('dialog', lambda x: x.accept(x.default_value) if x.type == 'prompt' else x.accept())
        pg.on('pageerror', lambda e: err.append(str(e)[:300]))
        pg.goto(url); pg.wait_for_timeout(1500); pg.wait_for_function('window.DLAT && DLAT.siap', timeout=90000)
        pg.evaluate("document.getElementById('dlatBtn').click()"); pg.wait_for_timeout(3000)
        pg.wait_for_function('!DLAT.busy', timeout=900000); pg.wait_for_timeout(2500)
        pg.evaluate('OGS.noPrint=true')
        for nm, js, sel, ms in LANGKAH:
            pg.evaluate('(async function(){' + W8 + js + '})()'); pg.wait_for_timeout(ms)
            pg.evaluate("var c=document.getElementById('ogsC');if(c)c.scrollTop=0;")
            pg.locator(sel).screenshot(path=str(FIGD / (nm + '.png')))
        angka = pg.evaluate(ANGKA)
        n = pg.evaluate('(async function(){return await ogsLapBuat("pdf");})()'); pg.wait_for_timeout(1500)
        lap = pg.evaluate('OGS._lapHtml')
        ctx.close()
    srv.terminate()
    (FIGD / 'laporan.html').write_text(lap, encoding='utf-8')
    with sync_playwright() as pw:
        b = pw.chromium.launch(); p2 = b.new_page(viewport={'width': 1280, 'height': 720}); p2.goto('file://' + str(FIGD / 'laporan.html')); p2.wait_for_timeout(1500)
        for k, i in [('lap_sampul', 0), ('lap_struktur', None), ('lap_penampang', None)]:
            idx = i
            if k == 'lap_struktur': idx = p2.evaluate("[...document.querySelectorAll('section')].findIndex(s=>/Struktur bawah/i.test((s.querySelector('h2')||{}).textContent||''))")
            if k == 'lap_penampang': idx = p2.evaluate("[...document.querySelectorAll('section')].findIndex(s=>/Penampang/i.test((s.querySelector('h2')||{}).textContent||''))")
            p2.locator('section').nth(max(0, idx)).screenshot(path=str(FIGD / (k + '.png')))
        b.close()
    angka['nLap'] = n; angka['galat'] = err
    json.dump(angka, open(FIGD / 'angka.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    return angka


A = jalankan()
if A['galat']: print('PERINGATAN galat halaman:', A['galat'][:3])
VBM, VDH = D.versi()
F = D.Fig(str(FIGD))
n = D.num
dk = lambda v, d=1: ('%.*f' % (d, v)).replace('.', ',')
B = []
B.append('<h2>1. Apa itu Ore Geometry Studio</h2>')
B.append('<p><b>Ore Geometry Studio</b> adalah satu jendela di GC-Ex Drill Hole yang mengumpulkan semua alat untuk memahami '
         '<b>bentuk, ketebalan, kadar, zonasi dan struktur</b> sebuah sistem vein, sampai ke usulan target bor dan laporan '
         'presentasi siap cetak. Isinya mengikuti deck <i>Ore Geometry</i> yang dipakai Geology Team: dari tabel domain sampai '
         'penampang multi-elemen, pertemuan vein dan target lanjutan.</p>')
B.append('<div class=box><b>Referensi geologist.</b> Studio membaca data bor dan wireframe, tetapi <b>tidak menulis</b> flag ke '
         'Geomodeller dan <b>tidak dipakai</b> Model Estimation. Volume / tonase di Studio adalah gambaran geometri, bukan estimasi '
         'sumber daya. Pembersihan data juga tidak dilakukan otomatis: Studio hanya menampilkan temuan.</div>')
B.append(F('01_panel.png', 'Node Ore Geometry di panel samping: ringkasan hasil terakhir, tombol <b>Buka Ore Geometry Studio</b> '
           'dan tautan langsung ke setiap halaman.'))
B.append('<p>Jendela Studio bisa digeser (tarik judulnya), diperkecil (&ndash;) dan ditutup (&times;). Menu di kiri dibagi tiga: '
         'halaman 1&ndash;8 (geometri, kadar, zonasi, penampang), <b>Struktur &amp; target</b> (9&ndash;13) dan <b>Laporan</b> (14). '
         'Bagian <i>Alat lain</i> berisi alat Ore Geometry sebelumnya dan pintasan ke Geostatistik &rsaquo; Profil dan Slicer.</p>')
B.append(D.tabel(['Halaman', 'Isi', 'Hasil yang bisa diambil'], [
    ['1 Data &amp; domain', 'Sumber wireframe, prioritas, flag otomatis, pemeriksaan data', 'peta intercept, tabel domain (CSV)'],
    ['2 Geometri &amp; tebal', 'strike, dip, panjang, tinggi, RL, tebal sebenarnya per domain', 'tabel, histogram, sebaran tebal'],
    ['3 Kadar &amp; multi-elemen', 'statistik vein vs luar vein, kontras, Spearman, geologi di vein', 'tabel unsur &amp; domain'],
    ['4 Long section', 'GT dan unsur pilihan, sampai 6 panel', 'grafik PNG'],
    ['5 Envelope RBF &amp; 3D', 'RBF GT per domain, envelope cut-off, volume / tonase, 3D', 'grafik, tabel volume'],
    ['6 Zonasi vertikal', 'median per pita RL: vein vs halo', 'grafik'],
    ['7 Profil per domain', 'format Geostatistik &rsaquo; Profil, dibatasi ke domain', 'grafik'],
    ['8 Penampang', 'sayatan Studio sendiri, panel unsur + geologi, potongan wireframe', 'grafik, tabel'],
    ['9 Struktur bawah permukaan', 'collar, dasar GC, puncak ore, zona belum teruji, garis interpretasi', 'grafik, tabel, CSV / STR garis'],
    ['10 Struktur paralel &amp; tekukan', 'posisi tegak lurus vs strike, deviasi strike lokal', 'grafik, tabel, uji statistik'],
    ['11 Pertemuan vein', 'GT / tebal / kadar zona 2 vein atau lebih vs 1 vein', 'grafik, tabel, uji per lokasi'],
    ['12 Target bor', 'usulan otomatis + klik di long section', 'tabel E/N/RL, collar, azimuth, panjang (CSV)'],
    ['13 Di luar wireframe', 'sampel &ge; cut-off di luar wireframe per kategori', 'tabel, peta'],
    ['14 Laporan PDF', 'deck bertemplate navy / emas, judul ditulis geologist', 'PDF / HTML'],
    ['15 Peta level', 'sayatan horizontal jadi peta: kadar, arsir alterasi, wireframe, lubang, kontur, legenda di dalam peta', 'peta PNG, slide laporan, garis .str di RL']]))

B.append('<div class="page"></div><h2>2. Menyiapkan data: dua jalur proyek</h2>')
B.append('<p>Studio hanya butuh tiga hal: <b>data bor dengan assay</b>, <b>wireframe domain</b>, dan (opsional) <b>kolom geologi</b>. '
         'Wireframe domain bisa datang dari dua jalur proyek:</p>')
B.append(D.tabel(['Jalur', 'Sumber wireframe domain', 'Di Studio tampil sebagai'], [
    ['Lanjutkan dari Surpac / Leapfrog', 'Import Wireframe Geologi (.dxf, .obj, .str/.dtm)', '<i>wireframe impor</i>'],
    ['Mulai dari Nol', 'Solid yang dibangun di Geological Modelling (mis. Vein System dari kolom kode)', '<i>solid GC-Ex</i>']]))
B.append(D.steps(
    'Muat data bor (atau tombol <b>Demo</b> untuk data latihan: %s lubang, %s interval assay).' % (n(A['nHole']), n(A['nA'])),
    'Jalur <b>Lanjutkan</b>: import wireframe di node Import Wireframe Geologi. Jalur <b>Mulai dari Nol</b>: bangun solid di Geological Modelling.',
    'Buka node <b>Ore Geometry</b> &rsaquo; <b>Buka Ore Geometry Studio</b> &rsaquo; halaman <b>1 &middot; Data &amp; domain</b>.',
    'Centang wireframe yang dipakai, atur <b>prioritas</b> dengan &#9650; &#9660; (bila wireframe bertumpang, yang lebih atas menang).',
    'Tekan <b>Hitung flag domain &amp; intercept</b>. Hitung ulang setiap kali data atau wireframe berubah (Studio memberi tanda).'))
B.append(F('02_data_lanjut.png', 'Jalur Lanjutkan: satu wireframe Leapfrog (QV_Lensa2_Leapfrog) dari data latihan.'))
B.append(F('03_data_nol.png', 'Jalur Mulai dari Nol: lima solid GC-Ex dari kolom geologi <i>Vein</i> (Vein System). Wireframe impor dimatikan '
           'supaya tidak bertumpang dengan solid QV_Lensa2.'))
B.append('<p>Pada data latihan (jalur Mulai dari Nol) hasilnya <b>%s domain, %s sampel vein, %s intercept</b>:</p>' % (len(A['dom']), n(A['nV']), n(A['nI'])))
B.append(D.tabel(['Domain', 'Intercept', 'Sampel di dalam wireframe'], [[x[0], n(x[1]), n(x[2])] for x in A['dom']]))
B.append(D.tabel(['Isian', 'Arti'], [
    ['Sela gabung intercept', 'interval sedomain dalam satu lubang yang berjarak &le; nilai ini digabung menjadi satu intercept (bawaan 1 m)'],
    ['Unsur utama (GT)', 'unsur untuk GT (kadar &times; tebal sebenarnya), bawaan Au'],
    ['Unsur Ag', 'untuk rasio Ag/Au; kosongkan bila tidak ada'],
    ['SG', 'densitas untuk tonase envelope (bawaan 2,42)']]))
B.append('<div class=warn><b>Pemeriksaan data</b> di halaman 1 hanya mendaftar temuan (nilai negatif, banyak nol, nilai ekstrem yang '
         'mencurigakan satuan). Perbaikan dilakukan di database bor, bukan di Studio.</div>')

B.append('<div class="page"></div><h2>3. Geometri, tebal dan kadar</h2>')
B.append('<p>Setiap domain diberi bidang dari PCA titik tengah intercept (bobot panjang). <b>Tebal sebenarnya</b> = panjang intercept &times; '
         '|arah lubang &middot; normal bidang|. Bidang <b>acuan</b> (bawaan: domain dengan intercept terbanyak) dipakai long section, '
         'penampang dan struktur; bisa diganti di halaman 2.</p>')
B.append(F('04_geo.png', 'Halaman 2. Data latihan: bidang acuan %s strike %s&deg;, dip %s&deg; ke %s; tebal sebenarnya median %s m (P10&ndash;P90 %s&ndash;%s m).'
           % (A['ref'][0], A['ref'][1], A['ref'][2], A['ref'][3], dk(A['Tm']), dk(A['T10']), dk(A['T90']))))
B.append(F('05_kadar.png', 'Halaman 3. Kontras Au %s&times; (median di vein vs di luar wireframe), korelasi Spearman antar unsur, kadar per domain '
           'dan geologi di dalam vein (pilih kolom geologi dengan sakelar).' % n(round(A['kon']))))
B.append(D.bullets('Baris kuning = domain acuan.', 'Tanda * = unsur dengan kurang dari 20 sampel di domain itu.',
                   'Setiap tabel punya tombol <b>CSV</b>, setiap grafik tombol <b>PNG</b>.'))

B.append('<div class="page"></div><h2>4. Long section, envelope dan zonasi</h2>')
B.append(F('06_ls.png', 'Halaman 4. Long section multi-panel: GT intercept dan unsur di sampel vein, diproyeksikan ke bidang acuan. '
           'Panel dipilih dengan daftar di atas grafik (maks 6).'))
B.append(F('07_env.png', 'Halaman 5. Envelope RBF: peta GT di bidang domain, garis hitam = envelope cut-off, arsir abu = lebih dari 25 m dari intercept, '
           'tabel volume / tonase semua domain dan envelope 3D.'))
B.append(D.tabel(['Parameter envelope', 'Bawaan', 'Arti'], [
    ['Cut-off GT', '0,6', 'batas envelope (g/t&middot;m)'], ['Resolusi', '2 m', 'ukuran sel grid di bidang'],
    ['Jarak maks', '30 m', 'sel lebih jauh dari intercept tidak dihitung'], ['Batas arsir', '25 m', 'sel lebih jauh diberi arsir'],
    ['Smoothing', '0,5', 'RBF linear dengan polinom derajat 1; 0 = tepat melewati data']]))
B.append('<p>Volume data latihan: ' + '; '.join('%s %s m&sup3; (%s t)' % (x[0], n(x[1]), n(x[2])) for x in A['env']) + '.</p>')
B.append(F('08_zon.png', 'Halaman 6. Zonasi vertikal: median per pita RL di dalam vein (merah) dan halo &le; 45 m dari bidang (biru). '
           'Ag/Au hanya dihitung bila Au &ge; 0,1.'))
B.append(F('09_prof.png', 'Halaman 7. Profil per domain dengan format Geostatistik &rsaquo; Profil: unsur, rasio, jumlah dan % kode geologi.'))

B.append('<div class="page"></div><h2>5. Penampang (sayatan Studio)</h2>')
B.append('<p>Sayatan Studio <b>berdiri sendiri</b>: tidak menggerakkan Slicer di bilah atas. Bawaannya tegak lurus strike bidang acuan.</p>')
B.append(D.steps('Tekan <b>Usulkan sayatan</b> (tiga posisi dengan intercept terbanyak / GT tertinggi, berjarak &ge; 60 m), atau <b>+ Sayatan</b>.',
                 'Ubah <b>posisi sepanjang strike</b>, <b>azimuth</b> (kosong = tegak lurus) dan <b>lebar jendela &plusmn;</b>.',
                 '<b>Maju / Mundur</b> menggeser sayatan sejauh 2 &times; lebar jendela.',
                 '<b>Gambar di peta</b>: klik dua titik di peta kecil; arah garis menjadi azimuth sayatan.',
                 'Pilih panel unsur dan kolom geologi. Garis hitam = potongan wireframe; lingkaran berwarna = sampel vein per domain.'))
B.append(F('10_sec.png', 'Halaman 8. Sayatan usulan %s. Di bawah grafik: sampel Au tertinggi dan sampel &ge; 0,5 di luar wireframe.'
           % ', '.join('%s (%s m)' % (s[0], n(s[1])) for s in A['sec'])))
B.append(F('11_lama.png', 'Alat Ore Geometry sebelumnya (Intercept &amp; GT, Long section GT, Ore shoot, Grade shell) kini di bagian <i>Alat lain</i>.'))

B.append('<div class="page"></div><h2>6. Struktur bawah permukaan dan garis interpretasi</h2>')
B.append('<p>Halaman 9 menjawab pertanyaan <i>"apakah ore berhenti di dasar GC?"</i>. Garis berikut dihitung otomatis dari data: '
         '<b>collar tertinggi</b> (&asymp; topografi / pit), <b>dasar lubang GC</b>, <b>puncak ore</b> (sampel &ge; cut-off), dan '
         '<b>zona belum teruji GC</b> (dasar GC sampai RL batas). Lubang eksplorasi dikenali dari <b>pola nama</b> (regex, bawaan '
         '<code>^(PDH|MDH|DDH|EXP|EX|RC)</code>).</p>')
B.append('<div class=box><b>Garis interpretasi dibuat geologist.</b> Tekukan, ujung ore, sesar atau batas zona bukan hasil hitungan. '
         'Studio hanya memberi <b>usulan</b> (abu-abu, putus-putus, bertanda <i>usulan</i>) yang baru menjadi garis resmi setelah '
         'Anda menekan <b>Terima</b>. Usulan yang dihapus tidak muncul lagi.</div>')
B.append(D.steps('Pilih jenis: <b>Penanda posisi</b> (1 klik, garis tegak), <b>Polyline</b> (beberapa klik, lalu <b>Selesai</b>), '
                 '<b>Pita / zona</b> (2 klik: awal &amp; akhir), <b>Poligon</b> (&ge; 3 klik, lalu Selesai), <b>Teks</b> (1 klik).',
                 'Klik di grafik. Titik yang sedang digambar tampil merah putus-putus; <b>Batal</b> membatalkan.',
                 'Beri nama: nama itu masuk legenda. Atur warna, gaya (garis / putus-putus / titik), centang legenda dan keterangan di tabel.',
                 'Ekspor: <b>Garis (CSV E/N/RL)</b> atau <b>String Surpac (.str)</b>. Koordinat dikembalikan ke 3D di bidang acuan (long section) '
                 'atau di bidang sayatan (penampang).'))
B.append(F('12_struk.png', 'Halaman 9 dengan satu usulan yang sudah diterima (pergeseran bidang), satu polyline interpretasi dan satu teks. '
           'Tabel per segmen strike: lubang GC, % kena &ge; cut-off, collar, dasar GC, puncak ore, ore eksplorasi terdalam.'))
B.append('<p>Garis interpretasi juga tersedia di <b>Penampang</b> (garis tampil di semua panel) dan di grafik posisi tegak lurus '
         'pada halaman 10. Semua garis tersimpan di proyek dan ikut ke laporan PDF bila sudah diterima.</p>')

B.append('<div class="page"></div><h2>7. Struktur paralel, tekukan dan pertemuan vein</h2>')
B.append(F('13_par.png', 'Halaman 10. Kiri: peta sampel &ge; cut-off berwarna RL dengan jejak bidang tiap domain. Kanan: jarak tegak lurus bidang '
           'acuan vs jarak sepanjang strike. Bawah: tabel per sepertiga panjang strike dan peta tekukan strike bidang acuan.'))
B.append('<p><b>Tekukan</b> = sudut lokal bidang (dari RBF posisi tegak lurus) terhadap strike rata-rata. Tabel membandingkan GT intercept '
         'per kelas tekukan; uji Mann-Whitney menilai apakah bagian yang menekuk &gt; 10&deg; berbeda dari bagian lurus.</p>')
B.append('<p><b>Pertemuan vein</b> (halaman 11): intercept vein bernama di satu lubang yang berjarak &le; sela (bawaan 3 m) dihitung '
         'sebagai satu <b>zona</b>. GT zona = jumlah GT vein di zona itu, jadi selalu naik bila dua vein bergabung; ukuran yang adil '
         'adalah <b>Au zona</b> (rata-rata tertimbang tebal). Uji <b>per sel lokasi</b> (50 m strike &times; 25 m RL, Wilcoxon) '
         'membandingkan zona pertemuan dan zona 1 vein di tempat yang sama.</p>')
B.append(F('14_jun.png', 'Halaman 11 pada data latihan: %s zona 1 vein, %s zona pertemuan. Lensa simulasi hampir sejajar sehingga '
           'pertemuannya sedikit; pada data nyata Zona 2 pertemuan mencapai 27%% zona.' % (n(A['jun'][0]), n(A['jun'][1]))))

B.append('<div class="page"></div><h2>8. Target bor dan sampel di luar wireframe</h2>')
B.append(D.steps('Tekan <b>Usulkan target</b>: di bawah intercept eksplorasi GT tertinggi yang berada di bawah dasar GC; bila tidak ada lubang '
                 'eksplorasi, di bawah intercept terdalam yang GT-nya &ge; median; ditambah celah data terbesar.',
                 'Atau tekan <b>Klik target di long section</b> lalu klik posisinya.',
                 'Studio menghitung E / N / RL target di bidang acuan, collar (collar tertinggi &plusmn;25 m), azimuth (dari sisi arah dip, '
                 'menembus vein) dan panjang lubang untuk dip lubang yang Anda isi.',
                 'Ubah nama dan keterangan di tabel; ekspor CSV.'))
B.append(F('15_tgt.png', 'Halaman 12: target usulan %s. Garis titik merah = proyeksi lubang usulan.' % ', '.join(A['tgt'])))
B.append(F('16_luar.png', 'Halaman 13: sampel &ge; cut-off di luar wireframe per kategori. Data latihan: ' +
           '; '.join('%s %s' % (x[0], n(x[1])) for x in A['luar']) + '.'))
B.append(D.tabel(['Kategori', 'Aturan'], [
    ['Dekat wireframe', '&le; 10 m dari verteks wireframe terdekat: kandidat revisi batas wireframe'],
    ['Di bawah dasar wireframe', 'lebih dalam dari verteks terendah di segmen strike yang sama (&le; 40 m dari bidang)'],
    ['Lanjutan strike', 'di luar rentang strike intercept'],
    ['Koridor vein', '&le; 60 m dari bidang, &gt; 10 m dari wireframe'], ['Struktur lain', '&gt; 60 m dari bidang acuan']]))

B.append('<div class="page"></div><h2>9. Laporan PDF</h2>')
B.append('<p>Halaman 14 menyusun deck presentasi dengan template yang sama dengan deck <i>Ore Geometry</i> (navy / emas, 13,333 &times; 7,5 in): '
         'sampul, ringkasan, setiap halaman Studio, profil per domain, setiap sayatan, struktur, target dan rekomendasi.</p>')
B.append(D.steps('Isi label sampul, judul, subjudul (sumber data) dan kaki halaman.',
                 'Untuk setiap slide: centang <b>Cetak</b>, tulis <b>judul kalimat</b> (pesan utama slide) dan <b>catatan</b> (satu poin per baris). '
                 'Teks abu-abu hanyalah usulan angka dan dipakai bila kolom dibiarkan kosong.',
                 'Tekan <b>Buat laporan &amp; cetak ke PDF</b>. Di dialog cetak pilih <b>Simpan sebagai PDF</b> / <b>Microsoft Print to PDF</b>; '
                 'ukuran halaman sudah diatur, margin 0, centang <b>Grafik latar belakang</b>.',
                 'Atau <b>Simpan laporan (HTML)</b> untuk dibuka dan dicetak di browser.'))
B.append(F('17_lap.png', 'Halaman 14: isian sampul dan daftar slide dengan judul kalimat yang ditulis geologist.'))
B.append(F('lap_sampul.png', 'Contoh sampul laporan (%s slide pada data latihan).' % A['nLap']))
B.append(F('lap_struktur.png', 'Contoh slide struktur dengan garis interpretasi yang sudah diterima.'))
B.append(F('lap_penampang.png', 'Contoh slide penampang.'))
B.append('<div class=warn>Laporan memakai parameter dan garis interpretasi saat tombol ditekan. Garis yang masih berstatus <i>usulan</i> '
         'tetap tercetak abu-abu bertanda usulan; terima atau hapus dulu sebelum laporan dibagikan.</div>')

B.append('<div class="page"></div><h2>10. Peta level (sayatan horizontal)</h2>')
B.append('<p>Halaman 15 mengubah irisan horizontal di satu RL menjadi <b>peta</b> bergaya peta eksplorasi: warna kelas kadar, arsir alterasi, '
         'garis wireframe domain, lubang yang menembus RL, kontur, garis interpretasi, judul, panah utara, skala dan legenda <b>di dalam peta</b>.</p>')
B.append(D.steps('Pilih <b>RL</b> (tombol &#9650; &#9660; menggeser sebesar <i>langkah</i>, bawaan 5 m) dan <b>tebal irisan</b> (bawaan &plusmn;5 m).',
                 '<b>Mode kadar</b>: <i>Anomali</i> (bawaan) = interpolasi IDW anisotropi searah strike bidang acuan (bawaan 4:1, jangkauan 40 m, '
                 'tidak diwarnai bila &gt; 25 m dari sampel). <i>Di dalam domain saja</i> = warna hanya di dalam wireframe; lebih jujur untuk vein tipis.',
                 '<b>Kelas</b>: 4 batas, bawaan 0,4; 0,5; 1; 3 g/t (5 warna: biru, kuning, oranye, merah, magenta).',
                 '<b>Alterasi</b>: pilih kolom geologi; setiap sel diberi alterasi yang menguasai &ge; 50% sampel di sekitarnya, digambar sebagai <b>arsir</b> di atas warna kadar.',
                 '<b>Wireframe</b>: <i>garis tengah</i> (bawaan) atau <i>dinding</i>; tebal garis bisa diatur; tiap domain bisa dimatikan.',
                 '<b>Kontur</b>: <b>Impor string kontur (.str / .dxf)</b>. Tanpa string, kontur dibuat dari collar sebagai cadangan; '
                 'collar ada di lantai pit saat pemboran, jadi itu bukan topografi asli.',
                 '<b>Geser label</b> domain dan Hole ID dengan mouse (tarik kotak label). Posisi tersimpan per RL di proyek.',
                 'Tarik <b>garis interpretasi</b> (struktur, lode baru); namanya tampil sejajar garis. Ekspor .str memberi koordinat 3D pada RL peta.'))
B.append(F('18_peta_ctrl.png', 'Halaman 15: kontrol peta level di atas, peta di bawah.'))
B.append(F('18_peta.png', 'Peta level pada data latihan (jalur Mulai dari Nol): kelas Au, arsir alterasi, garis tengah wireframe tiap lensa dengan label, '
           'kontur cadangan dari collar dan satu contoh garis struktur. Legenda, judul, panah utara dan skala ada di dalam peta.'))
B.append(D.tabel(['Lubang yang ditampilkan', 'Aturan'], [
    ['Titik tembus', 'semua lubang yang <b>menembus RL</b> di dalam batas peta (titik abu kecil)'],
    ['Berakhir di irisan', 'lubang yang tidak sampai RL tetapi ujungnya di dalam &plusmn;tebal irisan (lingkaran kosong)'],
    ['Lubang eksplorasi', 'dikenali dari pola nama (halaman 9); digambar besar dengan jejak lubang dan Hole ID. '
                          'Hole ID yang terlalu rapat dilewati supaya tidak bertumpuk; label bisa digeser']]))
B.append('<p>Untuk laporan, isi <b>RL peta yang dicetak</b> (mis. <code>280; 300; 320</code>): setiap RL menjadi satu slide peta di Laporan PDF.</p>')
B.append('<div class="page"></div><h2>11. Batasan dan catatan</h2>')
B.append(D.bullets(
    'Studio adalah referensi: tidak menulis flag Geomodeller dan tidak dipakai Model Estimation.',
    'Envelope RBF dan volume / tonase adalah gambaran geometri, bukan estimasi sumber daya. Bagian berarsir didukung sedikit data.',
    'Flag memakai titik tengah interval assay. Wireframe yang tidak tertutup diberi peringatan; hasil di dekat bagian terbuka bisa tidak akurat.',
    'Tebal intercept lubang yang menembus vein dengan sudut kecil sangat peka terhadap orientasi bidang domain.',
    'Uji statistik (Mann-Whitney, Wilcoxon) memakai pendekatan normal; dengan sedikit sel / sampel, nilai p kurang andal.',
    'Pembersihan data tidak otomatis. Perbaiki satuan, batas deteksi atau batch lab di database bor, lalu hitung ulang.',
    'Lubang eksplorasi dikenali dari pola nama; sesuaikan regex dengan penamaan proyek Anda.',
    'Peta level adalah interpolasi visual dari sampel di irisan; di elevasi dengan sedikit lubang, warnanya hanya mengikuti beberapa titik.'))

import re
ISI = [re.sub('<[^>]+>', '', q) for x in B for q in re.findall(r'<h2>(.*?)</h2>', x)]
B.insert(0, D.cover('GRADE CONTROL EXCELLENCE &middot; GC-EX DRILL HOLE ULTIMATE', 'Tutorial Ore Geometry ', 'Studio',
                    'Satu jendela untuk geometri, ketebalan, kadar, zonasi, penampang, struktur, pertemuan vein, target bor dan laporan '
                    'presentasi sistem vein. Berlaku untuk jalur proyek <b>Mulai dari Nol</b> maupun <b>Lanjutkan dari Surpac / Leapfrog</b>.',
                    ISI, 'GC-Ex Drill Hole Ultimate %s &middot; disusun otomatis %s dari tangkapan layar aplikasi pada data latihan simulasi.<br>'
                    'Data latihan sepenuhnya sintetis: tidak ada nama perusahaan, Hole ID atau koordinat proyek nyata.<br>'
                    'Copyright &copy; Habil Abdillah 2026. Seluruh hak dilindungi.' % (VDH, D.tanggal())))
sz = D.render(B, str(PDF), 'Tutorial Ore Geometry Studio · GC-Ex Drill Hole %s' % VDH)
print('OK', PDF, sz, 'byte'); print(json.dumps({k: v for k, v in A.items() if k != 'galat'}, ensure_ascii=False)[:1500])
