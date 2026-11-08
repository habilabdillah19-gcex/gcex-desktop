# -*- coding: utf-8 -*-
"""Menyusun Tutorial GC-Ex Drillhole (HTML -> PDF A4) dari tangkapan layar docs/tutorial/img.
Jalankan: python docs/tutorial/tutorial_shots.py  (membuat img/*.png + notes.json)
          python docs/tutorial/build_tutorial.py  (membuat GCEx_Tutorial_Modelling_Estimasi.pdf)
"""
import os, json, re, html, datetime
from PIL import Image
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
IMG = os.path.join(HERE, 'img')
OUT = os.path.join(HERE, 'build')
os.makedirs(OUT, exist_ok=True)
if not os.path.isdir(IMG) or not os.path.exists(os.path.join(IMG, 'notes.json')):
    raise SystemExit(
        "Tangkapan layar belum ada di %s.\n"
        "Tutorial bergambar ini dibangun dari tangkapan layar aplikasi, jadi jalankan dulu:\n"
        "    python docs/tutorial-gcex/src/tutorial_shots.py\n"
        "Langkah itu membuka GC-Ex di Chromium dan memerlukan browser yang dapat membuka folder\n"
        "proyek (File System Access API). Di lingkungan terbatas (mis. kontainer CI Linux) langkah\n"
        "ini dapat menghentikan renderer; pakai mesin Windows tempat GC-Ex biasa dipakai.\n"
        "Tutorial yang TIDAK memerlukan tangkapan layar: build_tutorial_update.py" % IMG)

N = json.load(open(os.path.join(IMG, 'notes.json'), encoding='utf-8'))
VDH = json.load(open(os.path.join(HERE, '..', '..', '..', 'builder-dh.json'), encoding='utf-8')).get('extraMetadata', {}).get('version', '')
# gambar & angka hasil hitungan langsung dari data latihan (dibuat build_tutorial_update.py -> fig_update/)
FIGU = os.path.join(HERE, 'fig_update')
NU = json.load(open(os.path.join(FIGU, 'notes.json'), encoding='utf-8')) if os.path.exists(os.path.join(FIGU, 'notes.json')) else {}
PDF = os.path.join(HERE, '..', 'GCEx_Tutorial_Modelling_Estimasi.pdf')

def clean(s): return html.unescape(re.sub('<[^>]+>', '', str(s)))

# ---------- gambar: PNG -> JPEG ringan ----------
FIG = {}
for f in sorted(os.listdir(IMG)):
    if not f.endswith('.png'): continue
    im = Image.open(os.path.join(IMG, f)).convert('RGB')
    if im.width > 1700: im = im.resize((1700, round(im.height * 1700 / im.width)), Image.LANCZOS)
    j = f[:-4] + '.jpg'; im.save(os.path.join(OUT, j), quality=82, optimize=True)
    FIG[f[3:-4]] = (j, im.width / im.height)

IMGL = os.path.join(HERE, 'img_lat')
NL = json.load(open(os.path.join(IMGL, 'notes.json'), encoding='utf-8'))
for f in sorted(os.listdir(IMGL)):
    if not f.endswith('.png'): continue
    im = Image.open(os.path.join(IMGL, f)).convert('RGB')
    if im.width > 1700: im = im.resize((1700, round(im.height * 1700 / im.width)), Image.LANCZOS)
    j = 'L' + f[:-4] + '.jpg'; im.save(os.path.join(OUT, j), quality=82, optimize=True)
    FIG[f[3:-4]] = (j, im.width / im.height)

for k, f in (NU.get('F') or {}).items():
    pth = os.path.join(FIGU, f)
    if not os.path.exists(pth): continue
    im = Image.open(pth).convert('RGB')
    if im.width > 1700: im = im.resize((1700, round(im.height * 1700 / im.width)), Image.LANCZOS)
    j = 'U' + f[:-4] + '.jpg'; im.save(os.path.join(OUT, j), quality=86, optimize=True)
    FIG['u_' + k] = (j, im.width / im.height)

fig_no = [0]; FNUM = {}
def fig(key, cap, w=None):
    j, ar = FIG[key]; fig_no[0] += 1; FNUM[key] = fig_no[0]
    narrow = ar < 0.8
    width = w or ('52%' if narrow else '100%')
    return ('<figure class="%s"><img src="%s" style="width:%s"><figcaption><b>Gambar %d.</b> %s</figcaption></figure>'
            % ('nar' if narrow else '', j, width, fig_no[0], cap))

def fig2(k1, c1, k2, c2):
    """dua gambar panel sempit berdampingan"""
    a = fig(k1, c1, '100%'); b = fig(k2, c2, '100%')
    return '<div class="duo"><div>%s</div><div>%s</div></div>' % (a, b)

def steps(*xs): return '<ol class="st">' + ''.join('<li>%s</li>' % x for x in xs) + '</ol>'
def tip(t, k='tip', h='Tips'): return '<div class="box %s"><b>%s</b> %s</div>' % (k, h, t)
def warn(t, h='Perhatian'): return tip(t, 'warn', h)
def why(t): return tip(t, 'why', 'Mengapa?')
def fN(v, d=0):
    # q.v (validasi) bisa null bila domain tidak punya pembanding kadar GC -> jangan menggagalkan PDF
    if v is None: return '&ndash;'
    return ('{:,.%df}' % d).format(v).replace(',', 'X').replace('.', ',').replace('X', '.')

def dta(berkas, isian):
    """Kotak tetap di awal bab: BERKAS data latihan mana yang dipakai dan ANGKA apa yang diisi.
    Dipasang karena menyebut nama tombol saja tidak cukup: pembaca harus tahu data mana yang
    dimuat dan nilai apa yang diketik agar sampai ke gambar dan angka yang sama."""
    b = ''.join('<tr><td>%s</td><td>%s</td></tr>' % r for r in isian)
    return ('<div class="box dta"><b>Data &amp; isian bab ini</b>'
            + ('<div class=dtaf>Berkas: ' + berkas + '</div>' if berkas else '')
            + ('<table class="kv">' + b + '</table>' if isian else '') + '</div>')

def kv(rows): return '<table class="kv">' + ''.join('<tr><td>%s</td><td>%s</td></tr>' % r for r in rows) + '</table>'

st = {r[0]: r for r in (json.loads(N['stat']) if isinstance(N['stat'], str) else N['stat'])}
okm = dict(l.split('\t') for l in N['okMsg'].split('\n') if '\t' in l)
CH = []
def ch(title, body, key=None): CH.append((title, body))

# Urutan bab disusun ulang (0.24.31) per TIPE DEPOSIT dan mengikuti urutan node Project Tree /
# langkah kerja nyata. Bab-bab di bawah tetap ditulis dalam urutan apa saja; daftar BAGIAN inilah
# yang menentukan urutan terbit. Setiap entri = awal judul bab (unik).
BAGIAN = [
 ('Bagian I &middot; Persiapan &amp; database bor',
  'Berlaku untuk <b>semua tipe deposit</b>. Menyiapkan folder proyek, memasukkan data bor, memeriksa '
  'kesehatan datanya, menata kampanye pemboran, dan menyaring data yang akan dipakai.',
  ['Tentang tutorial ini', 'Data simulasi', 'Membuat folder proyek', 'Validasi data bor',
   'Database bor per kampanye', 'Menambah bor infill dengan upsert', 'Filter data bor',
   'Mengenal tampilan', 'Sayatan &amp; penampang 2D', 'Geologi: pita litologi']),
 ('Bagian II &middot; Deposit vein / urat',
  'Endapan <b>vein</b> (epitermal, mesotermal, urat kuarsa) &mdash; benda bijih tipis, miring, dibatasi '
  'hanging wall dan footwall. Urutannya mengikuti node <b>Geomodeller Vein &rarr; Geostatistik &rarr; '
  'Model Estimation</b> di Project Tree: domain &rarr; flag &rarr; string &rarr; solid &rarr; parameter '
  '&rarr; kerangka blok &rarr; estimasi ore &rarr; estimasi waste &rarr; koreksi. Tiga bab di bagian ini '
  '&mdash; <b>kerangka blok AOI</b>, <b>sub-blocking</b> dan <b>estimasi waste</b> &mdash; berlaku untuk '
  '<b>semua tipe deposit</b>; pembaca jalur laterit dirujuk ke sini dari Bagian III.',
  ['Geomodeller Vein: membuat domain vein', 'Flag otomatis dari kadar', 'Koreksi flag secara interaktif',
   'String kontrol hanging wall', 'Membangun solid vein', 'Struktur geologi', 'Sesar 3D',
   'Vein bercabang', 'Memakai wireframe dari Leapfrog', 'Wireframe Leapfrog menjadi domain',
   'Filter domain &amp; statistik',
   'Domain aktif di Geostatistik', 'Variogram, anisotropi', 'Kriging Neighbourhood Analysis',
   'Uji estimasi &amp; simpan parameter', 'Block model dari nol', 'Sub-blocking',
   'Model Estimation: estimasi block model GC', 'Estimasi waste',
   'Koreksi setelah bor baru', 'Autorun: wireframe', 'Autorun Estimasi dari Nol', 'Latihan terpandu']),
 ('Bagian III &middot; Deposit laterit / stratiform berlapis',
  'Endapan <b>laterit</b> (nikel, bauksit) dan <b>stratiform</b> (sedex, seam) &mdash; lapisan tipis '
  'secara vertikal tetapi luas ke samping, mengikuti bentuk permukaan. Jalurnya berbeda dari vein: '
  'node <b>Geomodeller Stratified-Laterite</b>, estimasi per lapisan di koordinat <b>unfold</b>.',
  ['Geomodeller Stratified-Laterite', 'Estimasi waste pada laterit', 'Autorun pada laterit']),
 ('Bagian IV &middot; Pelaporan sumber daya',
  'Berlaku untuk <b>semua tipe deposit</b>, dijalankan sesudah block model terestimasi: mengusulkan kelas '
  '<b>Measured / Indicated / Inferred</b> per blok dari atribut hasil estimasi, lalu melaporkan tonase dan '
  'kadar per kelas dan per cut-off. Blok waste (<code>est_type = 3</code>) sengaja tidak ikut pelaporan '
  'sumber daya &mdash; kadarnya untuk dilusi, ore loss dan perencanaan pit.',
  ['Klasifikasi keyakinan', 'Laporan per desain pit']),
 ('Bagian V &middot; Data pendukung, export &amp; pemeliharaan',
  'Peta 2D, plan bor harian, pergantian topografi / block model per periode, export ke Surpac dan perawatan folder proyek.',
  ['Map: peta geologi 2D', 'Plan bor harian', 'Mengganti topografi', 'Topografi &amp; orthofoto resolusi tinggi',
   'Export database', 'Folder proyek, backup', 'Status pengembangan']),
]

# ================= ISI =================
ch('Tentang tutorial ini', f'''
<p>Tutorial ini mengajarkan alur kerja <b>pemodelan vein dan estimasi block model</b> di <b>GC-Ex Drillhole</b>
(aplikasi desktop <b>GC-Ex Drill Hole Ultimate {VDH}</b>). Setiap langkah dipraktikkan dengan <b>data simulasi</b> yang ikut
dibagikan, dan semua gambar adalah tangkapan layar dari satu kali jalannya latihan tersebut. Jika rekan Anda mengikuti langkah
yang sama, angka yang muncul di layarnya akan sama dengan angka di buku ini.</p>
<h3>Alur kerja (deposit vein)</h3>
<div class="flow">
<div><b>1</b>Folder proyek<br>&amp; import</div><div><b>2</b>Sayatan<br>&amp; geologi</div><div><b>3</b>Domain<br>vein</div>
<div><b>4</b>Flag interval<br>bor</div><div><b>5</b>String HW / FW<br>&amp; solid RBF</div><div><b>6</b>Wireframe<br>Leapfrog</div>
<div><b>7</b>Upsert bor<br>infill</div><div><b>8</b>Statistik<br>&amp; variogram</div><div><b>9</b>KNA &amp; Model<br>Estimation</div><div><b>10</b>Export<br>&amp; backup</div>
</div>
<h3>Susunan buku ini</h3>
<p>Sejak edisi ini, urutan bab mengikuti <b>urutan node Project Tree</b> dan <b>tipe deposit</b>, bukan urutan
penambahan fitur. Bab yang berlaku untuk semua deposit dipisahkan dari bab yang khusus satu tipe:</p>
<table class="t"><tr><th>Bagian</th><th>Untuk</th><th>Isi</th></tr>
<tr><td><b>I</b> Persiapan &amp; database bor</td><td>semua tipe</td><td>folder proyek, import, validasi, kampanye pemboran, filter, sayatan, pita litologi</td></tr>
<tr><td><b>II</b> Deposit vein / urat</td><td>vein, epitermal, mesotermal</td><td>Geomodeller Vein &rarr; flag &rarr; string HW/FW &rarr; solid RBF &rarr; struktur &amp; Sesar 3D &rarr; Geostatistik &rarr; <b>kerangka blok AOI</b> &rarr; <b>sub-blocking</b> &rarr; Model Estimation &rarr; <b>estimasi waste</b> &rarr; koreksi bor baru</td></tr>
<tr><td><b>III</b> Laterit / stratiform</td><td>laterit nikel, bauksit, sedex, seam</td><td>Geomodeller Stratified-Laterite (lapisan dari log geologi, estimasi per lapisan di ruang unfold) &rarr; estimasi waste pada laterit (dua zona unfold)</td></tr>
<tr><td><b>IV</b> Pelaporan sumber daya</td><td>semua tipe</td><td>klasifikasi Measured / Indicated / Inferred, kerapatan bor, grade-tonase per bench / domain / cut-off</td></tr>
<tr><td><b>V</b> Pendukung &amp; pemeliharaan</td><td>semua tipe</td><td>Map 2D, versi topografi &amp; block model, export, folder proyek &amp; backup</td></tr></table>
<p>Jadi bila endapan Anda <b>vein</b>, kerjakan <b>Bagian I &rarr; II &rarr; IV &rarr; V</b>. Bila <b>laterit</b>,
<b>Bagian I &rarr; III &rarr; IV &rarr; V</b> &mdash; dengan satu catatan: tiga bab di Bagian II
(<b>kerangka blok AOI</b>, <b>sub-blocking</b>, <b>estimasi waste</b>) murni geometri dan berlaku untuk semua tipe
deposit, jadi dibaca juga oleh pembaca jalur laterit. Bab <b>Estimasi waste pada laterit</b> di Bagian III merujuk
ke ketiganya dan hanya menjelaskan apa yang berbeda.</p>
<p>Urutan di dalam setiap bagian mengikuti <b>urutan kerja nyata</b>, bukan urutan menu: kerangka blok dibuat
sebelum estimasi (karena estimasi butuh blok untuk diisi), sub-blocking sebelum estimasi (karena mengubah geometri
bloknya), dan estimasi waste sesudah estimasi ore (karena mewarisi variogram domain ore terdekat).</p>
<h3>Yang dibutuhkan</h3>
<ul>
<li>Komputer Windows 10 / 11 64-bit dengan <b>GC-Ex Drill Hole Ultimate</b> terpasang (installer <code>GC-Ex-Drillhole-Setup-{VDH}.exe</code>) dan lisensi aktif.</li>
<li>Aplikasi berjalan sepenuhnya offline; tidak perlu browser atau file Plotly terpisah.</li>
<li>Folder <code>data_simulasi</code> dari paket tutorial ini.</li>
<li>Satu folder kosong untuk proyek latihan, misalnya <code>Proyek_Tutorial_VeinA</code> (boleh di OneDrive / SharePoint / drive jaringan).</li>
</ul>
<h3>Cara membaca</h3>
<p>Langkah bernomor = yang harus diklik / diisi. Kotak <span class="tag tip">Tips</span> berisi jalan pintas,
<span class="tag why">Mengapa?</span> menjelaskan alasan geologinya, dan <span class="tag warn">Perhatian</span> berisi hal yang sering keliru.
Nama tombol dan menu ditulis <b>tebal</b> persis seperti di layar.</p>
''' + warn('Gambar diambil dari GC-Ex Drill Hole Ultimate ' + VDH + ' dengan kartu grafis perangkat lunak; di komputer Anda tampilan 3D lebih halus dan bisa diputar. Posisi, warna dan angka sama.', 'Catatan gambar') + tip('Tur <b>Demo</b> di bilah atas memakai data latihan ini juga: berkasnya dititipkan di folder instalasi, dan tombol <b>&#8681; Muat data latihan simulasi</b> (halaman import) atau <b>&#8681; Muat data latihan &amp; jalankan Demo</b> (menu Demo) mengimpornya sekali klik. Angka yang muncul di bilah bawah demo &mdash; interval hasil usulan flag, jumlah string, volume solid, jumlah komposit, tonase per fase pit &mdash; dihitung saat itu, jadi bisa dicocokkan dengan angka di buku ini.', 'Demo memakai data yang sama'))

ch('Data simulasi', f'''
<p>Data ini <b>sintetis</b> (bukan data perusahaan), dibuat agar meniru kasus vein emas epitermal sempit berbentuk sigmoidal.</p>
<table class="t"><tr><th>File</th><th>Isi</th></tr>
<tr><td>SIM_collar.csv, SIM_survey.csv, SIM_assay.csv, SIM_geologi.csv</td><td>Kampanye resource: <b>{N['nHole']} lubang bor</b>, <b>{fN(N['nAssay'])} baris assay</b> (sampel 1 m) dengan Au, Ag, Cu, Pb, Zn, S, As_ppm, SG; logging Lith, Alt, Ox, Texture, RQD, Recovery.</td></tr>
<tr><td>SIM_kecil_*.csv</td><td>Subset kecil untuk latihan cepat sebelum memakai data penuh.</td></tr>
<tr><td>SIM_gc_*.csv</td><td>Kampanye <b>grade control</b>: bor tegak per bench pola 7 m.</td></tr>
<tr><td>SIM_BM_GC_kadar.csv</td><td>Block model GC <b>berisi kadar</b> untuk tutorial GC-Ex Block Model.</td></tr>
<tr><td>SIM_sesar.csv, SIM_qaqc.csv</td><td>Bidang sesar pasca-mineralisasi (offset 12 m) dan data QAQC (CRM, duplikat, blank).</td></tr>
<tr><td>JAWABAN_MODEL.txt</td><td><b>Kunci jawaban</b>: parameter model yang dipakai membuat data + angka hasil ukur ({{B:Latihan terpandu}}).</td></tr>
<tr><td>SIM_upsert_*.csv</td><td>7 lubang infill (SIM-INF-*) untuk latihan <b>upsert</b>.</td></tr>
<tr><td>SIM_upsert2_*.csv</td><td>7 lubang infill tahap 2 untuk latihan <b>koreksi Model Estimation</b>.</td></tr>
<tr><td>SIM_topo_xyz.csv, SIM_topo_xyz_nov.csv</td><td>Topografi titik XYZ grid 5 m; versi bulan berikutnya untuk latihan Data Spasial.</td></tr>
<tr><td>SIM_BM_GC.csv</td><td>Block model GC kosong 10 &times; 10 &times; 5 m ({fN(N['bx'])} blok) di sekitar array vein.</td></tr>
<tr><td>QV_Lensa2_Leapfrog.obj</td><td>Contoh wireframe lensa 2 hasil Leapfrog (tertutup, 21.596 segitiga).</td></tr>
<tr><td>SIM_struktur.csv</td><td>96 titik struktur (Easting, Northing, RL, Jenis, Dip, Dip_Azimuth, Plunge, Trend, Catatan): kontak vein di singkapan dan bidang sesar.</td></tr>
<tr><td>SIM_pickup_survey.csv</td><td>142 titik pick-up survei (Kode, Easting, Northing, RL, Tebal_m, Keterangan): singkapan vein tiap lensa.</td></tr>
<tr><td>SIM_pit_fase1.dxf, SIM_pit_fase2.dxf</td><td>Dua tahap <b>desain pit</b> (DXF 3DFACE, kerucut lereng 45&deg;, lantai RL 240 dan RL 180); fase 2 memuat fase 1 sehingga bisa dipakai latihan laporan <b>per desain pit</b>.</td></tr>
<tr><td>SIM_topo_akhir_juni.dxf, SIM_topo_akhir_juli.dxf</td><td>Dua <b>survei topografi bulanan</b> pada pit yang sama (lantai RL 260 lalu RL 245): selisihnya = material tergali sebulan, untuk latihan <b>progres topo-ke-topo</b>.</td></tr>
<tr><td>SIM_split_*.csv</td><td>Proyek terpisah vein bercabang (latihan domain induk).</td></tr>
<tr><td>SIM_rusak_collar.csv, SIM_rusak_assay.csv</td><td>Database dengan kesalahan sengaja untuk latihan validasi.</td></tr>
<tr><td>SIM_LAT_collar / survey / assay / geologi.csv</td><td>Proyek terpisah <b>laterit nikel</b>: {NL['nHole']} bor vertikal grid 25 m, sampel 1 m ({fN(NL['nAssay'])} sampel), unsur Ni, Co, Fe, MgO, SiO2 (%), kolom <code>Zona</code>: TS (tanah penutup), LIM, SAP, BRK.</td></tr>
<tr><td>SIM_LAT_topo_xyz.csv, SIM_LAT_BM_GC.csv</td><td>Topografi grid 10 m dan block model GC 12,5 &times; 12,5 &times; 1 m ({fN(NL['nBlok'])} blok) untuk latihan {{B:Geomodeller Stratified}}.</td></tr>
<tr><td>SIM_LAT_sesar.csv</td><td>Jejak sesar F1 (dua titik X, Y) beserta dip 65&deg; ke 100&deg;, normal, offset 12 m, post-mineralisasi, untuk latihan {{B:Sesar 3D}}.</td></tr></table>
<h3>Geometri yang perlu diingat</h3>
<p>Endapannya adalah <b>array 4 lensa vein en-echelon</b> (QV_Lensa1 s/d QV_Lensa4) ditambah satu splay di sisi hanging wall. Tutorial ini menelusuri <b>lensa 2 beserta splay-nya</b>; lensa lain dikerjakan dengan cara yang persis sama. Model geologi lengkapnya ada di {{B:Latihan terpandu}}, kunci jawabannya di <code>data/JAWABAN_MODEL.txt</code>.</p>
''' + (fig('u_peta', 'Jejak permukaan keempat lensa vein, collar bor, dan sesar pasca-mineralisasi. Pola <i>en-echelon</i>: tiap lensa berpindah ke sisi hanging wall, bukan satu vein menerus. (Dihitung dari berkas data latihan.)') if 'u_peta' in FIG else '') + f'''
{kv([('Vein utama (QV_Lensa2)','strike 045&deg;, dip 70&deg; ke 135&deg; (bidang acuan; permukaannya sigmoidal sehingga bidang rata-rata data &plusmn;66&deg;), tebal median 1 m dan membengkak sampai &plusmn;5 m di zona dilatan'),
     ('Ore shoot','pitch 55&deg; dari garis strike di dalam bidang vein &mdash; mengontrol tebal DAN kadar sekaligus'),
     ('Splay hangingwall (QV_Splay_HW)','sejajar, &plusmn;26 m di sisi hanging wall, lebih tipis dan lebih rendah kadar'),
     ('Arah bor','azimuth 315&deg;, dip &minus;55&deg; s/d &minus;65&deg; (dari sisi hanging wall)'),
     ('Koordinat','sekitar E 505.000, N 9.012.000; elevasi 150&ndash;330 m, paleo-muka air tanah RL 250 m (zona bonanza)'),
     ('Dip survey','negatif = ke bawah')])}
''' + why('Karena bor datang dari sisi hanging wall, lubang yang cukup panjang akan menembus <b>QV_Splay_HW dulu</b> (lebih dangkal), baru <b>QV_Lensa2</b>. Ini dipakai pada {{B:Koreksi flag}} untuk latihan koreksi flag.'))

ch('Membuat folder proyek & import data', dta('<code>data/SIM_collar.csv</code>, <code>SIM_survey.csv</code>, <code>SIM_assay.csv</code>, <code>SIM_geologi.csv</code> &middot; topografi <code>SIM_topo_xyz.csv</code> &middot; block model <code>SIM_BM_GC.csv</code>',
     [('Nama project site', 'bebas, mis. <code>Vein A &middot; Latihan</code>'),
      ('Folder proyek', 'folder <b>kosong</b> bernama <code>Proyek_Tutorial_VeinA</code>'),
      ('Nama dataset', '<code>VeinA_Simulasi</code>'),
      ('Hasil yang seharusnya', f"<b>{N['nHole']:,} collar</b>, <b>{fN(N['nAssay'])} interval assay</b>, block model <b>{fN(N['bx'])} blok</b>".replace(',', '.'))]) +  steps(
 'Buka <b>GC-Ex Drill Hole Ultimate</b> dari menu Start. Halaman muka <b>Import data</b> tampil penuh ([[jendela_awal]]); isi <b>Nama project site</b> bila perlu (tampil di bilah atas, disimpan per proyek).',
 'Pada kartu <b>Folder proyek</b>, klik <b>Buka / pilih folder proyek</b> lalu pilih folder kosong <code>Proyek_Tutorial_VeinA</code>. Izinkan akses ketika browser bertanya (<i>Lihat file</i> dan <i>Simpan perubahan</i>).',
 'Pada <b>&#9312; Database drillhole</b>, klik <b>Import Collar</b>, <b>Import Survey</b>, <b>Import Assay</b>, <b>Import Geologi</b> dan pilih empat file SIM_*.csv yang sesuai.',
 'Isi <b>Nama dataset</b>: <code>VeinA_Simulasi</code>. Periksa ringkasan di bawahnya ([[import_database]]): harus tertulis <b>'+f"{N['nHole']:,} collar &middot; {N['nHole']*3:,} survey ({N['nHole']:,} hole) &middot; {fN(N['nAssay'])} interval assay &middot; {fN(N['nAssay'])} interval geologi".replace(",",".")+'</b>, unsur <b>Au, Ag, Cu, Pb, Zn, S, As_ppm, SG</b>.',
 'Gulir ke <b>&#9313; Data spasial &amp; block model</b>: pada <b>Topografi</b> pilih <code>SIM_topo_xyz.csv</code>; pada <b>Block model</b> pilih <code>SIM_BM_GC.csv</code>.',
 'Klik <b>Tampilkan viewer &rarr;</b>. Viewer 3D terbuka ([[viewer_3d]]) dan muncul tawaran menyalin file block model ke folder proyek &mdash; jawab <b>OK</b>.')
 + fig('jendela_awal', 'Jendela awal. Kartu <b>Folder proyek</b> paling atas: proyek disimpan di folder pilihan Anda, GC-Ex hanya membuka &amp; mengolah.')
 + fig('import_database', 'Empat file database sudah dipilih. Ringkasan hijau di bawah memastikan jumlah collar, survey, assay dan geologi terbaca benar.')
 + why('Dengan folder proyek, semua pekerjaan (flag, string, hasil estimasi) tersimpan otomatis ke folder 3 detik setelah ada perubahan, lengkap dengan backup berversi. Rekan lain cukup membuka folder yang sama.')
 + fig('viewer_3d', f"Viewer 3D setelah import: {N['nHole']} lubang bor, {fN(N['nAssay'])} interval assay diwarnai kelas Au. Pesan di bawah: <i>SIM_BM_GC.csv tersalin ke folder proyek sumber/</i>.")
 + tip('Jika ringkasan menulis <i>hole di assay tidak ada di collar</i>, buka <b>Pemetaan kolom &amp; unsur</b> dan cek kolom Hole ID.'))

VL = N.get('valid', []) if isinstance(N.get('valid', []), list) else json.loads(N['valid'])
ch('Validasi data bor', dta('untuk melihat pesan kesalahan: <code>data/SIM_rusak_collar.csv</code> + <code>SIM_rusak_assay.csv</code> (dipilih sebagai Collar / Assay di halaman import, pada proyek coba-coba)',
     [('Yang diisi', 'tidak ada &mdash; validasi berjalan sendiri saat berkas dipilih'),
      ('Yang diklik', 'ringkasan <b>Validasi</b> di bawah ringkasan import, lalu <b>Unduh laporan validasi (CSV)</b>'),
      ('Pada data normal', 'tidak ada baris dibuang; ini sebabnya latihan memakai berkas <code>SIM_rusak_*</code>')]) +  '<p>Saat file database dipilih, GC-Ex memeriksa datanya dan menampilkan ringkasan <b>Validasi</b> di bawah ringkasan import ([[validasi]]). Klik ringkasan itu untuk melihat rinciannya, dan <b>Unduh laporan validasi (CSV)</b> untuk daftar per hole. GC-Ex <b>tidak mengubah data mentah</b>: perbaiki di database sumber, lalu import ulang atau upsert.</p>'
 + '<table class="t"><tr><th>Tingkat</th><th>Kasus</th><th>Yang dilakukan GC-Ex</th></tr>'
 + '<tr><td><b>Dibuang</b></td><td>Collar tanpa koordinat (E / N / RL kosong)</td><td>Hole dan semua intervalnya tidak ditampilkan; nama hole tercantum di laporan</td></tr>'
 + '<tr><td><b>Dibuang</b></td><td>Collar ganda</td><td>Baris pertama dipakai, baris berikutnya diabaikan</td></tr>'
 + '<tr><td><b>Dibuang</b></td><td>Survey tidak valid (dip di luar &plusmn;90&deg;, depth / azimuth kosong)</td><td>Baris survey diabaikan</td></tr>'
 + '<tr><td><b>Dibuang</b></td><td>Interval tanpa From / To, From &ge; To, interval tanpa collar</td><td>Interval tidak dipakai di tampilan, statistik maupun estimasi</td></tr>'
 + '<tr><td>Peringatan</td><td>Interval tumpang tindih</td><td>Tetap dipakai &mdash; panjangnya terhitung dua kali di statistik / komposit, jadi perbaiki dulu</td></tr>'
 + '<tr><td>Peringatan</td><td>Sample ID ganda, interval lewat total depth, survey lebih dalam dari TD, nilai kadar negatif</td><td>Tetap dipakai apa adanya (nilai negatif = kode below detection? ganti di database)</td></tr>'
 + '<tr><td>Info</td><td>Interval kosong (gap), collar tanpa assay</td><td>Gap tampil tanpa warna (tidak diisi nilai); collar tanpa assay tampil sebagai trajectory</td></tr></table>'
 + fig('validasi', 'Data latihan yang bersih: <i>Validasi: tidak ada masalah data</i>.', '78%')
 + '<h3>Latihan: database rusak</h3>' + steps('Di jendela import, ganti file Collar dengan <code>SIM_rusak_collar.csv</code> dan Assay dengan <code>SIM_rusak_assay.csv</code>.',
   'Klik ringkasan <b>Validasi</b> untuk membuka rinciannya ([[validasi_rusak]]), lalu <b>Unduh laporan validasi (CSV)</b> untuk melihat hole mana yang bermasalah.',
   'Kembalikan file ke <code>SIM_collar.csv</code> dan <code>SIM_assay.csv</code> sebelum melanjutkan tutorial.')
 + fig('validasi_rusak', 'Database dengan kesalahan sengaja: 4 dibuang (collar tanpa koordinat, collar ganda, From &ge; To, assay tanpa collar) dan 3 peringatan (Sample ID ganda, tumpang tindih, nilai Au &minus;99).', '78%')
 + warn('Interval tumpang tindih adalah yang paling berbahaya bagi estimasi: panjangnya dihitung dua kali dan kadarnya ikut berbobot ganda. Selesaikan semua peringatan tumpang tindih sebelum Geostatistik / Model Estimation.'))

ch('Database bor per kampanye (multi-campaign)', dta('kampanye kedua memakai <code>data/SIM_gc_collar / survey / assay / geologi.csv</code> (bor grade control tegak pola 7 m)',
     [('Nama kampanye pertama', 'otomatis dari data yang sudah ada'),
      ('Nama kampanye baru', '<code>gc_2025_11</code>'),
      ('Cara mengisi', 'baris <b>+ Tambah kampanye&hellip;</b> (paling bawah di node <b>Database Bor</b>), lalu <b>upsert</b> keempat berkas <code>SIM_gc_*</code> dengan kampanye tujuan <code>gc_2025_11</code>'),
      ('Set merge', 'nama <code>merge_resource_2025</code>, centang kedua kampanye sumbernya')]) +  '<p>Satu area biasanya dibor berkali-kali: <b>eksplorasi</b>, <b>infill</b>, lalu <b>grade control</b> tiap periode. Ketiganya perlu dilihat bersama untuk memvalidasi bor GC, tetapi <b>tidak boleh</b> tercampur begitu saja saat mengestimasi. Node <b>Database Bor</b> di Project Tree karena itu dipecah per <b>kampanye</b>.</p>'
 + '<h3>Membuat kampanye</h3>'
 + steps('Klik baris <b>+ Tambah kampanye&hellip;</b> paling bawah di node <b>Database Bor</b> (bukan panel), beri nama mis. <code>eksplorasi_2024</code>, <code>infill_2025</code>, <code>gc_2025_11</code>.',
         'Data yang sudah ada otomatis menjadi kampanye pertama. Kampanye baru diisi lewat <b>import / upsert</b>: di dialog import ada <b>pemilih kampanye tujuan</b> (dan tombol <b>Kampanye baru&hellip;</b> langsung di situ).',
         'Untuk memindahkan hole yang salah kampanye: menu node kampanye &rarr; <b>Pindahkan hole ke sini&hellip;</b>, lalu masukkan daftar HoleID.')
 + '<h3>Tiga peran, satu dataset aktif</h3><p>Peran tiap database ditentukan oleh centang dan status aktifnya:</p>'
 + '<table class="t"><tr><th>Keadaan node</th><th>Peran</th><th>Akibatnya</th></tr>'
 + '<tr><td><b>AKTIF</b> (bertanda <i>aktif</i>)</td><td><b>Set kerja</b></td><td>Satu-satunya sumber <b>pemodelan, estimasi, Geostatistik dan statistik</b></td></tr>'
 + '<tr><td>Dicentang, tidak aktif</td><td><b>Referensi</b></td><td><b>Tampil</b> di 3D dan Sayatan 2D sebagai pembanding, <b>tidak</b> ikut analisis</td></tr>'
 + '<tr><td>Tidak dicentang</td><td><b>Sembunyi</b></td><td>Tidak tampil dan tidak ikut analisis; datanya tetap tersimpan</td></tr></table>'
 + why('Inilah cara memvalidasi bor GC: jadikan <code>gc_2025_11</code> sebagai <b>set kerja</b>, biarkan <code>eksplorasi_2024</code> sebagai <b>referensi</b> &mdash; kadar GC bisa dibandingkan langsung di penampang yang sama, tanpa risiko bor eksplorasi ikut masuk ke komposit dan variogram.')
 + '<h3>Menggabungkan kampanye (merge)</h3>'
 + '<p>Bila data GC sudah dinilai bagus, kampanye GC dan eksplorasi/infill digabung menjadi <b>satu set database baru</b> &mdash; node <b>Collar / Survey / Assay / Geologi Merge</b>:</p>'
 + steps('Menu node <b>Database Bor</b> atau node kampanye mana pun &rarr; <b>Buat set merge&hellip;</b>, centang kampanye sumbernya, beri nama mis. <code>merge_resource_2025</code>.',
         'GC-Ex bertanya apakah set merge itu langsung dijadikan <b>dataset aktif</b>. Bila ya, pemodelan dan estimasi berikutnya memakai gabungan tadi.',
         'Set merge bersifat <b>hidup</b>: menambah hole ke salah satu kampanye sumbernya otomatis menambahnya ke set merge &mdash; tidak ada salinan data yang bisa ketinggalan.',
         'Untuk pihak luar: menu node set merge &rarr; <b>Export database ini (.xlsx)</b> &mdash; satu berkas Excel 4 sheet (Collar, Survey, Assay, Geologi), masing-masing berkolom <b>Kampanye</b>.')
 + '<h3>Kampanye sebagai atribut</h3>'
 + '<p>Kampanye juga tersedia sebagai <b>atribut kategori</b> bernama <code>Kampanye</code> (dan <code>Dataset aktif</code>), jadi bisa dipakai untuk <b>pewarnaan</b>, <b>filter</b>, <b>statistik per kampanye</b> dan pemisahan variogram tanpa menambah kolom apa pun di tabel assay.</p>'
 + warn('Bentrok HoleID saat upsert diselesaikan dengan <b>urutan prioritas</b> kampanye (menu node: <b>Naikkan / Turunkan prioritas</b>). Bila satu hole sudah dimiliki kampanye yang lebih tinggi, data baru untuk hole itu <b>ditolak</b> &mdash; tidak menimpa &mdash; dan HoleID yang ditolak dilaporkan sesudah upsert. Jadi pasang urutan prioritas <b>sebelum</b> import, bukan sesudah.'))

ch('Filter data bor (AND / OR)', dta('lanjutan &mdash; tanpa berkas baru',
     [('Mode', '<b>AND</b>'),
      ('Aturan 1', '<code>AU_GPT</code> &mdash; operator <b>antara</b> &mdash; <b>0,3</b> dan <b>1,5</b>'),
      ('Aturan 2', '<code>Lith</code> &mdash; <b>sama dengan</b> &mdash; <code>QV</code>'),
      ('Yang dibaca', 'kaki dialog: berapa interval dan berapa hole yang lolos'),
      ('Sesudah latihan', 'kosongkan aturannya lagi &mdash; filter ini berlaku untuk seluruh aplikasi, termasuk estimasi')]) +  '<p>Node <b>Filter data bor</b> (di bawah <b>Database Bor</b>) menyaring data yang dipakai <b>seluruh aplikasi</b>: tampilan 3D / Sayatan, statistik, komposit, Geostatistik dan estimasi. Dinilai <b>per interval</b>, bukan per hole.</p>'
 + '<h3>Menyusun aturan</h3>'
 + steps('Menu node <b>Filter data bor</b> &rarr; <b>Atur filter&hellip;</b> &mdash; dialog terbuka, panel kerja tidak ikut penuh.',
         'Pilih mode <b>AND</b> (semua aturan harus terpenuhi) atau <b>OR</b> (cukup salah satu).',
         'Tekan <b>+ Aturan</b>, pilih atribut, operator, lalu nilainya. Operator <b>antara</b> dipakai untuk rentang, mis. <code>AU_GPT antara 0,3 dan 1,5</code>.',
         'Kaki dialog menunjukkan hasilnya langsung: <i>&ldquo;&hellip; dari &hellip; interval &middot; &hellip; dari &hellip; hole lolos&rdquo;</i>.')
 + '<h3>Atribut yang bisa difilter</h3><p>Daftarnya <b>dinamis</b> &mdash; mengikuti kolom yang benar-benar ada di proyek:</p>'
 + kv([('Kadar unsur', 'setiap kolom angka di assay (<code>AU_GPT</code>, <code>AG_PPM</code>, &hellip;) &mdash; operator angka dan <b>antara</b>'),
       ('Kategori assay', 'mis. <code>Tekstur</code>, <code>Oksidasi</code> &mdash; sama dengan / bukan / memuat'),
       ('Atribut geologi', 'mis. <code>Lith</code>, <code>Alterasi</code>, <code>Domain</code> dari tabel geologi'),
       ('Kampanye / dataset', 'kampanye pemilik hole, dan apakah hole ikut dataset aktif'),
       ('Data collar', 'Easting, Northing, RL, total depth, bench / grup'),
       ('Interval', 'From, To, panjang interval'),
       ('HoleID', 'sama dengan / memuat / diawali &mdash; untuk memilih sekelompok bor'),
       ('Posisi', 'di atas / bawah <b>topografi</b> atau <b>DTM mana pun</b>; di dalam / luar <b>solid domain</b>, <b>wireframe</b>, atau <b>poligon Map / string</b>')])
 + '<h3>Tombol cepat topografi</h3>'
 + '<p>Menu node menyediakan <b>Hanya di bawah topografi</b> dan <b>Hanya di atas topografi</b> &mdash; dua kebutuhan yang paling sering muncul (membuang interval di udara akibat topografi baru, atau memeriksa material yang sudah tertambang). Menekan tombol yang berlawanan tidak menumpuk aturan, hanya membalik aturan yang sama.</p>'
 + '<h3>Membaca node</h3>'
 + kv([('Badge', '<code>AND &middot; 3 aturan &middot; 12 hole</code> saat aktif, atau <code>3 aturan (mati)</code>'),
       ('Anak node', 'satu baris per aturan, mis. <code>Au (assay) &ge; 0.8</code>; menunya memuat <b>Hapus aturan ini</b>'),
       ('Centang node', 'menghidupkan / mematikan filter <b>tanpa</b> menghapus aturan')])
 + '<h3>Mematikan filter</h3>'
 + steps('<b>Lepas centang</b> node <b>Filter data bor</b> &mdash; cara tercepat, aturan tetap tersimpan.',
         'Atau menu node &rarr; <b>Matikan filter (aturan disimpan)</b>.',
         'Atau menu node &rarr; <b>Hapus semua aturan</b> bila aturannya memang tidak dipakai lagi.')
 + '<h3>Export data terfilter</h3>'
 + '<p>Menu node &rarr; <b>Export data terfilter</b> ke <b>.xlsx</b> (4 sheet) atau <b>CSV</b> (4 berkas). Khusus di export ini, interval yang <b>memotong permukaan</b> tidak dibuang dan tidak diambil utuh melainkan <b>dipotong tepat di permukaannya</b>: interval 10&ndash;20 m dengan topografi di kedalaman 15 m keluar sebagai baris <code>15 &ndash; 20</code>. Tanpa ini, &ldquo;hanya di bawah topografi&rdquo; akan melebihkan panjang bor sebesar separuh interval di batasnya.</p>'
 + warn('Bedakan dua jalur ini. Untuk <b>statistik, komposit, Geostatistik dan estimasi</b>, interval dinilai <b>utuh atau gugur</b> dari <b>titik tengahnya</b> &mdash; tidak dipotong. Pemotongan di permukaan hanya terjadi pada <b>berkas export</b>. Jadi filter memang mempengaruhi hasil estimasi (interval yang tidak lolos tidak dipakai sebagai data masukan), tetapi pengaruhnya per interval penuh.', 'Filter dan estimasi')
 + tip('Aturan filter ikut tersimpan di berkas proyek beserta status hidup-matinya, jadi keadaan filter kembali seperti saat proyek ditutup. Bila hasil estimasi terasa &ldquo;kurang data&rdquo;, periksa dulu node ini &mdash; filter yang tertinggal menyala adalah penyebab yang paling sering terlewat.'))

ch('Mengenal tampilan', dta('lanjutan &mdash; proyek hasil bab sebelumnya',
     [('Batas kelas (menu Warna)', '<code>0.3,0.5,1,3</code> dengan <b>Klasifikasi diskrit</b> aktif'),
      ('Panel Layer', 'preset <b>Bor + domain</b>'),
      ('Lebar panel', 'tarik tepi kanan panel menu; klik ganda = kembali ke bawaan')]) +  '<p>Menu utama ada di <b>Project Tree</b> (kiri), bernomor mengikuti alur kerja nyata: <b>1</b> Proyek &rarr; <b>2</b> Data Spasial &rarr; <b>2b</b> Import Wireframe Geologi &rarr; <b>3</b> Database Bor &rarr; <b>4</b> Peta &rarr; <b>5</b> Struktur Geologi &rarr; <b>5b</b> Ore Geometry &rarr; <b>6</b> Geomodeller Vein / <b>6b</b> Strata-Laterit &rarr; <b>7</b> Geostatistik &rarr; <b>8</b> Block Model &rarr; <b>9</b> Model Estimation &rarr; <b>10</b> Validasi BM &rarr; <b>11</b> Reporting BM &rarr; <b>12</b> Layout &amp; Ekspor. Di bawahnya <b>Pengaturan tampilan</b> (Warna kadar, Overlay, Tampilan &amp; performa). Setiap node membuka satu panel di kanan; tombol <b>&#8943;</b> di ujung baris membuka menunya, dan baris biru <b>+ Tambah &hellip;</b> di bawah anak node menambah isinya (plan, versi, wireframe, domain, struktur &hellip;). Tombol di <b>bar atas</b>: Proyek, arah pandang (Top / Front / Side / Iso / <b>&perp; Tegak lurus</b> sayatan), <b>Sayatan 2D</b>, <b>&#9660; Mundur &middot; posisi &middot; Maju &#9650;</b> (pindah section tanpa membuka menu Sayatan), <b>Layer</b> (ikon tumpukan; juga untuk menyembunyikan drillhole), PNG, dan <b>Geostatistik</b>.</p>'
 + fig('header', 'Bar atas: arah pandang + <b>&perp; Tegak lurus</b>, <b>Sayatan 2D</b>, <b>&#9660; Mundur &middot; posisi &middot; Maju &#9650;</b> untuk berpindah section langsung dari sini, lalu Ortho, Layer, Gelap, PNG dan Geostatistik. Drillhole disembunyikan / ditampilkan lewat panel <b>Layer</b>.')
 + '<h3>Warna kadar</h3>' + steps('Klik <b>Warna</b> di rel kiri.', 'Aktifkan <b>Klasifikasi diskrit (kelas kadar)</b> dan isi <b>Batas kelas</b>: <code>0.3,0.5,1,3</code>.', 'Legenda kanan atas menampilkan jumlah interval per kelas ([[menu_warna]]).')
 + fig('menu_warna', 'Menu Warna: kelas kadar Au &lt;0,3 / 0,3&ndash;0,5 / 0,5&ndash;1 / 1&ndash;3 / &ge;3 g/t. Kotak <b>Ringkasan</b> di kiri bawah memberi statistik data yang sedang tampil.')
 + '<h3>Panel Layer</h3>' + steps('Klik ikon <b>Layer</b> (tumpukan) di bar atas. Panel menempel di sisi kanan area grafik ([[layer_panel]]).',
   'Centang / hapus centang untuk menyembunyikan satu layer; tombol bawah: <b>Semua</b>, <b>Bor + domain</b>, <b>Pemodelan</b>, <b>Kosongkan</b>.',
   'Klik <b>&rsaquo;</b> di kepala panel untuk <b>menciutkan jadi strip tipis</b> di tepi grafik ([[layer_strip]]). Strip menunjukkan jumlah layer yang tampil; klik strip untuk membuka lagi.')
 + fig('layer_panel', 'Panel Layer terbuka (preset <b>Bor + domain</b>). Layer yang tidak punya data tampil abu-abu.')
 + fig('layer_strip', 'Panel Layer diciutkan menjadi strip tipis bertuliskan LAYER di tepi kanan; area grafik kembali lebar.')
 + '<h3>Memperlebar panel menu</h3>' + steps('Arahkan kursor ke <b>tepi kanan panel menu</b> (batas dengan area grafik) sampai kursor berubah menjadi panah kiri-kanan.',
   '<b>Tarik ke kanan</b> untuk memperlebar panel bila ada tulisan atau tabel yang terpotong; tarik ke kiri untuk mempersempit ([[panel_lebar]]). Lebar maksimum 60% layar.',
   'Lebar panel diingat di komputer ini. <b>Klik ganda</b> tepi panel untuk kembali ke lebar bawaan.')
 + fig('panel_lebar', 'Panel menu diperlebar dengan menarik tepinya: tabel solid dan nama string tidak terpotong lagi.')
 + tip('Klik nama di legenda grafik juga menyembunyikan satu trace sementara. Panel Layer lebih cocok untuk menyalakan / mematikan kelompok data.'))

ch('Sayatan & penampang 2D', dta('lanjutan &mdash; proyek yang sama',
     [('Arah potongan', '<b>Garis manual (vertikal / miring)</b>, arah garis <b>135&deg;</b> (tegak lurus strike 045&deg;)'),
      ('Dip bidang', '<b>90</b> (tegak)'),
      ('Tebal slab', '<b>12 m</b>, <b>Potong data (hanya dalam slab)</b> aktif'),
      ('Posisi', '<b>0</b> &mdash; lalu Maju / Mundur per 12 m')]) +  steps(
 'Klik <b>Sayatan</b>. Pilih <b>Arah potongan</b>: <i>Garis manual (vertikal / miring)</i>, lalu <b>Gambar garis sayatan</b> dan klik dua titik di peta, tegak lurus strike vein (garis berarah 135&deg;).',
 '<b>Dip bidang</b> 90 (tegak), <b>Tebal</b> 12 m, aktifkan <b>Potong data (hanya dalam slab)</b>. [[sayatan_3d]] memperlihatkan 3 lubang section tengah.',
 'Klik <b>Sayatan 2D</b> di bar atas (atau biarkan <b>Buka Sayatan 2D setelah menggambar</b> aktif). Lihat [[penampang_2d]].',
 'Pindah section dengan <b>&#9660; Mundur</b> / <b>&#9650; Maju</b> (di menu Sayatan atau di bar atas, angka di tengah = posisi saat ini) atau isi <b>Posisi</b> (offset tegak lurus garis, meter).')
 + fig('sayatan_3d', 'Sayatan tegak tebal 12 m lewat tengah vein: hanya data di dalam slab yang tampil.')
 + fig('penampang_2d', 'Sayatan 2D section yang sama. Label BL 315&deg; / TG 135&deg; menunjukkan arah pandang; sumbu bawah = jarak sepanjang garis, sumbu kiri = elevasi.')
 + why('Flag dan string vein dikerjakan di penampang 2D yang tegak lurus strike, karena di situ ketebalan sebenarnya dan posisi HW / FW terlihat paling jelas.'))

ch('Geologi: pita litologi', dta('lanjutan &mdash; kolom <code>Lith</code> dari <code>SIM_geologi.csv</code>',
     [('Atribut geologi', '<code>Lith</code>'),
      ('Pita hatch (2D)', 'aktif, <b>Lebar 2</b>'),
      ('Yang dilihat', 'kode <b>AND</b> (andesit) dan <b>QV</b> (urat kuarsa) di legenda')]) +  steps(
 'Klik <b>Geologi</b>. <b>Atribut geologi</b>: <code>Lith</code>.',
 'Aktifkan <b>Pita hatch (2D)</b>, <b>Lebar</b> 2. Legenda memperlihatkan AND (andesit) dan QV (urat kuarsa) dengan hatch yang bisa diubah.')
 + fig('geologi_lith', 'Pita litologi di samping trace bor: interval QV (oranye arsir) bertepatan dengan kadar tinggi &mdash; acuan pertama untuk flag domain.')
 + tip('Bagian <b>Domain untuk analisis</b> di menu ini nanti dipakai untuk memilih domain vein sebelum statistik dan estimasi ({{B:Filter domain}}).'))

ch('Geomodeller Vein: membuat domain vein', dta('lanjutan &mdash; tanpa berkas baru',
     [('Domain 1', '<code>QV_Lensa2</code> &mdash; vein utama yang ditelusuri tutorial ini'),
      ('Domain 2', '<code>QV_Splay_HW</code> &mdash; splay di sisi hanging wall'),
      ('Domain aktif', 'klik <code>QV_Lensa2</code> di Project Tree sampai bertanda <i>AKTIF</i>')]) +  steps(
 'Klik <b>Geomodeller Vein</b> di rel kiri.',
 'Di Project Tree, klik <b>+ Tambah domain&hellip;</b> di bawah <b>Geomodeller Vein</b>, ketik <code>QV_Lensa2</code>, OK. Ulangi untuk <code>QV_Splay_HW</code>.',
 'Klik nama domain di Project Tree untuk menjadikannya <b>domain aktif</b> (bertanda <i>AKTIF</i>). Panel Properti hanya menampilkan domain aktif: warna bisa diubah dengan klik kotak warna; centang kanan = tampil / sembunyi. Flag, String, Solid dan Struktur selalu bekerja pada domain aktif.')
 + fig2('gm_domain', 'Dua domain vein dibuat. Di bawah nama: jumlah hole &middot; run &middot; panjang &middot; kadar rata-rata.',
        'gm_usulan_param', 'Bagian <b>Usulan otomatis dari kadar</b> dibuka dengan parameter latihan.')
 + why('Nama domain bebas per proyek. Nama ini dipakai juga untuk string kontrol (<code>QV_Lensa2_HW_01</code>), kolom <code>Ore_Domain</code> saat export, dan filter estimasi &mdash; jadi pilih nama yang baku di tim.'))

ch('Flag otomatis dari kadar', dta('lanjutan &mdash; kadar <code>Au</code> dari <code>SIM_assay.csv</code>',
     [('Unsur', '<b>Au</b>'),
      ('Cut-off', '<b>0,5</b> g/t'),
      ('Panjang min.', '<b>1</b> m'),
      ('Dilusi internal maks.', '<b>1</b> m'),
      ('Lingkup', '<b>Semua hole</b>, <b>Jangan timpa flag lain</b> aktif'),
      ('Hasil yang seharusnya', f"<b>{N['nRunAuto']} interval</b> diusulkan untuk QV_Lensa2")]) +  steps(
 'Pastikan domain aktif = <b>QV_Lensa2</b>.',
 'Buka <b>&#9660; Usulan otomatis dari kadar</b> dan isi: <b>Unsur</b> Au, <b>Cut-off</b> 0.5, <b>Panjang min.</b> 1 m, <b>Dilusi internal maks.</b> 1 m, <b>Lingkup</b> Semua hole, aktifkan <b>Jangan timpa flag lain</b> ([[gm_usulan_param]]).',
 'Klik <b>Usulkan ke domain aktif</b>.',
 f"Hasil ([[gm_usulan_hasil]]): <b>{clean(N['auto']).split('. Periksa')[0]}</b>.")
 + fig('gm_usulan_hasil', 'Interval hasil usulan diberi pita warna domain QV_Lensa2 di penampang 2D. Angka di samping trace = kadar Au.')
 + why('Usulan menggabungkan sampel &ge; cut-off yang dipisah waste &le; dilusi maksimum, dan membuang run lebih pendek dari panjang minimum. Hasilnya <b>hanya usulan</b>: geologist tetap wajib memeriksa tiap section.')
 + warn(f"Usulan memasukkan semua run kadar ke domain aktif. Pada data ini ada <b>{N['holeDuaVein']} hole</b> yang menembus dua vein (contoh <b>{N['contohHole']}</b>), sehingga intercept dangkal (QV_Splay_HW) ikut masuk QV_Lensa2. Ini dikoreksi pada bab berikut."))

ch('Koreksi flag secara interaktif', dta('lanjutan &mdash; hole contoh ' + f"<code>{N['contohHole']}</code>",
     [('Sayatan', f"sepanjang lubang <code>{N['contohHole']}</code>, azimuth <b>315&deg;</b>, dip <b>90</b>, tebal <b>12 m</b>"),
      ('Domain aktif', '<code>QV_Splay_HW</code>'),
      ('Yang dikerjakan', 'tarik mouse sepanjang intercept <b>dangkal</b> &rarr; pindah ke QV_Splay_HW'),
      ('Diulang pada', f"<b>{N['holeDuaVein']} hole</b> yang menembus dua vein")]) +  steps(
 f"Buat sayatan sepanjang lubang <b>{N['contohHole']}</b> (azimuth 315&deg;) dan buka <b>Sayatan 2D</b>.",
 'Di Geomodeller Vein pilih domain aktif <b>QV_Splay_HW</b>, lalu klik <b>&#9998; Flag</b>. Kotak biru <i>Flag aktif: QV_Splay_HW</i> muncul dengan petunjuk mouse.',
 '<b>Klik</b> satu interval = flag / lepas. <b>Tarik sepanjang lubang</b> = flag satu rentang ([[flag_tarik_hw1]]). <b>Shift + tarik</b> = kotak, semua interval di dalam kotak.',
 'Lepas mouse: interval berganti warna domain QV_Splay_HW ([[flag_hasil_hw1]]). Salah? Tekan <b>Ctrl+Z</b> atau klik <b>&#8630; Urungkan</b>.',
 'Untuk menghapus flag, klik <b>&#9003; Hapus flag</b> lalu klik / tarik interval. Tekan <b>Esc</b> atau <b>Selesai</b> untuk keluar dari mode.',
 'Ulangi untuk hole lain yang menembus dua vein, section demi section.')
 + fig('flag_tarik_hw1', 'Menarik mouse sepanjang intercept dangkal pada SIM-S04-2 untuk memindahkannya ke domain QV_Splay_HW.')
 + fig('flag_hasil_hw1', 'Setelah dilepas: intercept dangkal berwarna biru (QV_Splay_HW), intercept dalam tetap oranye (QV_Lensa2). Satu interval hanya boleh punya satu domain.')
 + '<p>Setelah semua hole dikoreksi, statistik di panel domain menjadi:</p>'
 + kv([('QV_Lensa2', f"{st['QV_Lensa2'][1]} hole &middot; {st['QV_Lensa2'][3]} m &middot; Au rata-rata {st['QV_Lensa2'][4]} g/t"),
       ('QV_Splay_HW', f"{st['QV_Splay_HW'][1]} hole &middot; {st['QV_Splay_HW'][3]} m &middot; Au rata-rata {st['QV_Splay_HW'][4]} g/t")])
 + tip('Flag disimpan per <b>kedalaman</b> (from&ndash;to), bukan per nomor baris. Karena itu flag tetap aman ketika data assay hole tersebut diganti lewat upsert ({{B:Menambah bor}}).'))

ch('String kontrol hanging wall / footwall', dta('lanjutan &mdash; flag hasil dua bab sebelumnya',
     [('Sayatan', 'arah <b>135&deg;</b>, dip <b>90</b>, <b>Tebal 20 m</b> (= jarak antar section)'),
      ('Domain aktif', '<code>QV_Lensa2</code>, lalu ulangi untuk <code>QV_Splay_HW</code>'),
      ('Yang diklik', 'tab <b>String</b> &rarr; <b>Semua section</b>'),
      ('Hasil yang seharusnya', f"QV_Lensa2 {clean(N['strUtama'])} QV_Splay_HW: {clean(N['strHW1'])}"),
      ('Periksa di', 'posisi <b>&minus;20</b> m')]) +  '<p>String kontrol adalah garis batas vein per section: <b>HW</b> (hanging wall, garis penuh) dan <b>FW</b> (footwall, garis putus-putus). String ini terpisah dari menu Digitasi dan akan dipakai, diperbaiki dan ditambah setiap ada bor baru.</p>'
 + steps('Atur sayatan tegak lurus strike (135&deg;) dengan <b>Tebal</b> = jarak antar section, di sini <b>20 m</b>.',
   'Domain aktif <b>QV_Lensa2</b>, lalu di tab <b>String</b> klik <b>&#10148;&#10148; Semua section</b>. GC-Ex menarik garis HW dan FW melalui titik kontak flag di tiap section.',
   f"Hasil: <b>{clean(N['strUtama'])}</b> Untuk QV_Splay_HW: <b>{clean(N['strHW1'])}</b>",
   'Periksa per section (Maju / Mundur). Nama string otomatis: <code>QV_Lensa2_HW_05</code>, <code>QV_Lensa2_FW_05</code>, dst.')
 + fig('string_section', 'Section offset &minus;20 m: string HW (penuh) dan FW (putus-putus) QV_Lensa2 (oranye) serta QV_Splay_HW (biru), melalui titik kontak flag.')
 + fig2('string_panel', 'Panel domain sesudah penarikan string. Jumlah hole / run per domain terlihat langsung.',
        'wireframe_panel', 'Panel yang sama setelah wireframe Leapfrog dipakai untuk flag ({{B:Memakai wireframe}}): QV_Lensa2 bertambah jadi 33 hole.')
 + '<h3>Mengedit string langsung di layar</h3>' + steps('Buka <b>Sayatan 2D</b> pada section string yang ingin diperbaiki. Tidak perlu menekan tombol edit.',
   'Arahkan kursor ke string: string tersorot, <b>kotak</b> muncul di setiap titik dan <b>bulatan</b> di tengah setiap segmen, dengan nama string di dekatnya ([[string_hover]]).',
   '<b>Tarik kotak</b> = pindah titik (snap ke kontak bor); <b>tarik bulatan</b> = sisip titik baru; <b>Shift+klik</b> kotak = hapus titik; <b>Ctrl+klik</b> = tambah titik di ujung terdekat.',
   'Selesai: klik area kosong grafik, atau tekan <b>Enter / Esc</b>. Menarik di area kosong tetap menggeser tampilan seperti biasa. Solid RBF dibangun ulang otomatis.',
   'Untuk menggambar string baru pilih HW / FW lalu <b>&#9998; Digit</b>. Edit langsung bisa dimatikan lewat centang <b>Edit string langsung di layar</b>; tombol <b>&#9998;</b> di daftar string tetap ada.')
 + fig('string_hover', 'Kursor di atas string FW QV_Lensa2: titik dan bulatan tengah muncul tanpa membuka mode edit.')
 + fig('string_edit', 'Titik tengah ditarik langsung. String yang sudah diedit tangan diberi tanda dan <b>tidak ditimpa</b> saat Tarik otomatis diulang.')
 + fig('model_3d', 'Tampilan 3D (preset Layer <b>Pemodelan</b>): flag domain dan seluruh string HW / FW tiap section membentuk kerangka vein sigmoidal.')
 + why('String HW dan FW dimodelkan terpisah, seperti pada vein modelling di Leapfrog. Pada tahap berikutnya (RBF) keduanya menjadi permukaan HW dan FW, lalu solid di antaranya dengan tebal minimum 1 m.'))

SOL = {r[0]: r for r in (json.loads(N['solid']) if isinstance(N['solid'], str) else N['solid'])}
SOLI = {r[0]: r for r in (json.loads(N['solidInfill']) if isinstance(N['solidInfill'], str) else N['solidInfill'])}
su, sh = SOL['QV_Lensa2'], SOL['QV_Splay_HW']
ch('Membangun solid vein (RBF)', dta('lanjutan &mdash; string kontrol bab sebelumnya',
     [('Radius pengaruh strike', '<b>15 m</b> (bawaan), potong tegas'),
      ('Pinch-out searah dip', '<b>15 m</b>; ujung atas dipotong <b>topografi aktif</b>'),
      ('Tebal minimum', '<b>1 m</b> (= panjang interval sampel)'),
      ('Elipsoid RBF', 'mayor : semi-mayor <b>50 : 50</b> (isotropik); untuk melihat pengaruhnya coba <b>100 : 25</b>, pitch <b>0&deg;</b>'),
      ('Yang diklik', '<b>Semua domain</b> di tab Solid'),
      ('Hasil yang seharusnya', f"QV_Lensa2 <b>{fN(su[1])} m&sup3;</b> (tebal rata-rata {fN(su[2],2)} m), QV_Splay_HW {fN(sh[1])} m&sup3;")]) +  '<p>Dari string kontrol dan titik kontak bor, GC-Ex membangun <b>permukaan hanging wall</b> dan <b>permukaan footwall</b> secara terpisah (interpolasi RBF <i>thin-plate spline</i>, mengikuti bentuk sigmoidal), lalu <b>solid vein</b> di antara keduanya. Model <b>dibangun ulang otomatis</b> setiap string atau flag berubah.</p>'
 + '<h3>Aturan batas model</h3>' + kv([('Searah strike','diperpanjang sejauh <b>radius pengaruh</b> (bawaan 15 m) dari data terluar lalu <b>dipotong tegas</b> (ada dinding penutup). <b>Tidak ada pinch-out</b> searah strike.'),
       ('Celah data searah strike','bila jarak antar data &gt; 2 &times; radius pengaruh (bawaan &gt; 30 m), model <b>diputus</b> menjadi bagian terpisah, tidak disambung paksa.'),
       ('Searah dip, bawah','<b>pinch-out</b> (menipis ke nol) sejauh 15 m di bawah data terdalam.'),
       ('Searah dip, atas','<b>dipotong topografi</b> (bila topografi ada) atau pinch-out 15 m.'),
       ('Tepi model','mengikuti <b>convex hull</b> data di bidang vein: mulus, tanpa &ldquo;gigi sisir&rdquo; walaupun ada lubang bor tunggal di antara section.'),
       ('Tebal','tidak lebih tipis dari <b>tebal minimum</b> 1 m (= interval sampel).')])
 + steps('Di Geomodeller Vein gulir ke tab <b>Solid</b> (Model vein HW / FW &rarr; solid RBF).',
   'Klik <b>&#9654; Bangun solid domain aktif</b>, atau <b>&#9654;&#9654; Semua domain</b>. Kotak centang di daftar domain menyalakan / mematikan solid per domain.',
   'Buka <b>Parameter domain aktif</b> bila perlu mengubah ([[solid_param]]). <b>Batas model</b>: radius pengaruh searah strike, pinch-out searah dip, ujung atas (topografi / pinch-out), tebal minimum. <b>Orientasi vein</b>: otomatis dari data, atau isi <b>Dip</b> dan <b>Dip dir</b> sendiri (klik <i>pakai &amp; ubah</i> untuk mulai dari nilai otomatis). <b>Elipsoid RBF</b>: sumbu mayor, semi-mayor dan pitch. <b>Struktur</b>: pakai titik struktur (lihat {{B:Struktur geologi}}). <b>RBF &amp; mesh</b>: resolusi, <b>Kehalusan permukaan</b>, sumber titik, <b>Anti-spike</b>. Tombol <b>Pakai parameter ini untuk semua domain</b> menyalin ke domain lain; <b>&#8634; Bawaan</b> mengembalikan nilai awal.',
   'Baca kotak ringkasan ([[solid_panel]]): volume, tonase, tebal, jumlah titik, selisih model di kontak bor, dan <b>interval flag di dalam solid</b>.')
 + fig('solid_panel', f"Tab Solid setelah <b>Semua domain</b>: QV_Lensa2 {fN(su[1])} m&sup3; (tebal rata-rata {fN(su[2],2)} m), QV_Splay_HW {fN(sh[1])} m&sup3;. Semua {su[8]} interval flag QV_Lensa2 berada di dalam solid; mesh tertutup rapat.")
 + kv([('Bidang rata-rata QV_Lensa2', f'dip {su[10]}&deg; ke {su[11]}&deg; (vein sigmoidal 70&deg;/135&deg;; bentuk S membuat rata-ratanya lebih landai)'),
       ('Titik model', f'{su[4]} titik HW / {su[5]} titik FW, termasuk {su[6]} pasang kontak bor'),
       ('Volume / luas bidang', f'{fN(su[1])} m&sup3; / {fN(su[12])} m&sup2;'),
       ('Tebal di zona data', f'rata-rata {fN(su[2],2)} m, maksimum {fN(su[3],2)} m, minimum 1,00 m (dipaksa)'),
       ('Waktu hitung', f'{fN(su[13],2)} detik')])
 + fig('solid_param', 'Parameter domain aktif QV_Lensa2: radius pengaruh strike 15 m (potong tegas), pinch-out dip 15 m, atas dipotong topografi, orientasi otomatis, elipsoid isotropik.', '78%')
 + fig('solid_3d', 'Solid QV_Lensa2 (oranye) dan QV_Splay_HW (biru) di 3D bersama lubang bor: tepi bawah mulus mengikuti data, ujung strike dipotong tegas 15 m dari section terluar. Item <b>Solid vein (RBF)</b> di panel Layer menyalakan / menyembunyikannya.')
 + fig('solid_2d', 'Sayatan 2D section tengah: solid terisi warna domain di antara string HW (penuh) dan FW (putus-putus). Di atas dan di bawah kontak terakhir vein menipis (pinch-out) sepanjang 15 m. QV_Splay_HW hanya ditembus satu lubang di section ini, sehingga berbentuk lensa.')
 + why('Tebal minimum 1 m menjaga vein tidak lebih tipis dari interval sampel, sehingga setiap sampel yang di-flag pasti masuk solid. Searah strike data berupa section, sehingga batasnya ditentukan radius pengaruh dan dipotong tegas: tidak ada dasar geologi untuk menipiskan vein di antara section. Searah dip, pinch-out menghindari vein terpotong lurus di bawah bor terdalam.')
 + '<h3>Orientasi & elipsoid RBF</h3>' + steps('<b>Orientasi otomatis</b> dihitung dari sebaran titik HW / FW. Bila vein melengkung kuat atau data sedikit, pilih <b>Diisi manual</b> dan isi dip / dip direction hasil pengukuran (strike = dip dir &minus; 90&deg;, tangan kanan).',
   '<b>Elipsoid RBF</b> mengatur arah kemenerusan permukaan di bidang vein, seperti elipsoid di Leapfrog. Mayor = semi-mayor (bawaan 50 : 50) berarti isotropik. Contoh: mayor 100, semi-mayor 25, pitch 0&deg; membuat permukaan lebih menerus searah strike; pitch 90&deg; = searah dip.',
   'Centang <b>Tampilkan elipsoid di 3D</b> untuk melihat bentuknya di tengah domain ([[solid_ell]]): merah = mayor, hijau = semi-mayor, biru = arah HW.')
 + fig('solid_ell', 'Elipsoid RBF QV_Lensa2 (mayor 100 m searah strike, semi-mayor 25 m) ditampilkan di 3D.')
 + warn('Yang berpengaruh pada RBF adalah <b>rasio</b> mayor : semi-mayor dan pitch, bukan ukuran mutlaknya. Tebal vein tetap dari jarak permukaan HW&ndash;FW.')
 + tip('Hanya string yang <b>tampil</b> (centang di daftar string) yang dipakai model. Untuk menguji interpretasi lain, sembunyikan string tertentu: solid langsung dihitung ulang tanpa string itu.')
 + warn('Tebal diukur tegak lurus <b>bidang rata-rata</b> vein, bukan tegak lurus permukaan lokal. Pada bagian vein yang sangat melengkung tebal sebenarnya sedikit lebih kecil dari angka di panel.')
 + '<h3>Kehalusan permukaan &amp; anti-spike</h3><p>Permukaan HW dan FW harus mulus: tanpa gerigi, runcingan atau spike. Tiga pengaturan di <b>Parameter domain aktif &rarr; RBF &amp; mesh</b> menjaganya:</p>'
 + kv([('Kehalusan permukaan','<b>Tepat di data</b> / <b>Halus</b> (bawaan) / <b>Sangat halus</b> / <b>Maksimum</b>. Penghalusan hanya &ldquo;mengendurkan&rdquo; titik string (interpretasi); kontak bor 100&times; lebih ketat sehingga tetap dihormati. Pada data latihan selisih di kontak bor 0,00 / 0,03 / 0,10 m.'),
       ('Anti-spike: hierarki data','titik string dalam &plusmn;3 m dari kontak bor diganti oleh kontak itu, sehingga tidak ada lekukan &ldquo;mata sapi&rdquo; akibat string yang tidak persis lewat di kontak.'),
       ('Anti-spike: verteks lancip','verteks string bersudut &lt; 60&deg; (garis maju-mundur akibat salah klik) diabaikan; nama string-nya muncul di ringkasan untuk diperbaiki. Spike 6 m tersisa 0,0 m.'),
       ('Otomatis','tebal minimum lembut (tidak patah di 1 m) dan tepi model dihaluskan.')])
 + tip('Bila permukaan masih bergelombang antar section, naikkan <b>Kehalusan permukaan</b> satu tingkat atau beri <b>Elipsoid RBF</b> memanjang searah kemenerusan vein. Ringkasan solid menampilkan &ldquo;selisih di kontak bor&rdquo; untuk memeriksa bahwa data bor tetap dihormati.')
 + '<h3>Export solid</h3>' + steps('Tombol <b>&#8681; OBJ</b> (Leapfrog / umum), <b>&#8681; DXF</b> (3DFACE, layer = nama solid) atau <b>&#8681; STR+DTM</b> (Surpac, ZIP berisi file string dan DTM tertutup dengan tetangga segitiga).',
   'Centang <b>Export juga permukaan HW &amp; FW</b> bila ingin membawa kedua permukaan ke Leapfrog / Surpac sebagai surface terpisah.',
   'Satu domain = satu file; beberapa domain dikemas dalam satu ZIP. File STR+DTM bisa dibaca ulang di node <b>Import Wireframe Geologi</b>.'), 'solid')

ch('Memakai wireframe dari Leapfrog', dta('<code>data/QV_Lensa2_Leapfrog.obj</code> &mdash; wireframe lensa 2 hasil Leapfrog, tertutup, 21.596 segitiga',
     [('Import lewat', 'baris <b>+ Tambah wireframe geologi&hellip;</b> di node <b>Import Wireframe Geologi</b> (data latihan sudah memuatnya)'),
      ('Domain tujuan', '<code>QV_Lensa2</code>'),
      ('Yang diklik', 'tombol &#8943; berkas <code>QV_Lensa2_Leapfrog</code> &rarr; <b>Iris jadi string / flag interval bor (manual)&hellip;</b>, lalu <b>Iris jadi string HW/FW (semua section)</b> dan <b>Flag interval bor di dalam wireframe</b>'),
      ('Hasil yang seharusnya', clean(N['wfFlag']))]) +  steps(
 'Klik baris <b>+ Tambah wireframe geologi&hellip;</b> di node <b>Import Wireframe Geologi</b> (langkah 2b) dan pilih <code>QV_Lensa2_Leapfrog.obj</code> (format lain: Leapfrog .msh, Surpac .dtm/.str, DXF 3DFACE). Setiap berkas muncul sebagai anak node, berurutan sesuai urutan import. Tombol <b>Muat data latihan</b> sudah memuatnya.',
 f"Wireframe tampil di 3D ([[wireframe_import]]): <b>{N['wf']}</b>.",
 'Klik tombol &#8943; berkas <code>QV_Lensa2_Leapfrog</code> &rarr; <b>Iris jadi string / flag interval bor (manual)&hellip;</b>; panel Import Wireframe Geologi menampilkan bagian <b>Iris jadi string / flag interval bor</b>. Pilih wireframe dan domain tujuan, lalu klik <b>&#9986; Iris jadi string HW/FW (section ini)</b> atau <b>&#9986; Semua section</b>. Loop irisan dipecah otomatis menjadi string HW dan FW ([[wireframe_iris]]).',
 f"Klik <b>&#9873; Flag interval bor di dalam wireframe</b>: {clean(N['wfFlag'])}",
 f"Karena flag QV_Lensa2 bertambah, solid QV_Lensa2 ikut <b>dibangun ulang otomatis</b> ({clean(N['solidWf'])}).")
 + fig('wireframe_import', 'Wireframe QV_Lensa2 hasil Leapfrog di atas data bor. Slider di daftar model mengatur transparansi.')
 + fig('wireframe_iris', 'Irisan wireframe pada section &minus;20 m (hijau tua) berdampingan dengan string QV_Lensa2 hasil flag. Keduanya bisa dibandingkan dan diedit.')
 + tip('Setelah selesai, sembunyikan wireframe besar lewat panel <b>Layer</b> (Wireframe / solid) agar tidak menutupi bor.')
 + warn('Pengecekan <i>di dalam wireframe</i> memakai sinar vertikal. Wireframe harus tertutup; jika ada tepi terbuka GC-Ex memberi peringatan dan hasil flag perlu diperiksa.'))

ch('Menambah bor infill dengan upsert', dta('<code>data/SIM_upsert_collar.csv</code>, <code>SIM_upsert_survey.csv</code>, <code>SIM_upsert_assay.csv</code>, <code>SIM_upsert_geologi.csv</code> &mdash; lubang infill <code>SIM-INF-*</code>',
     [('Yang diklik', 'menu <b>Data</b> &rarr; <b>Tambah / perbarui data bor (upsert)</b>, pilih keempat berkas, baca pratinjau, lalu tombol upsert'),
      ('Hasil yang seharusnya', f"<b>{N['upsTambah']} collar baru</b>; {clean(N['upsPrev'])[:120]}"),
      ('Sesudahnya', 'usulan otomatis lagi (parameter sama), koreksi QV_Splay_HW, lalu <b>Semua section</b>'),
      ('String', f"{clean(N['strUpd'])}")]) +  '<p><b>Upsert</b> = tambah atau perbarui. Collar dicocokkan per HoleID (baru ditambah, lama diperbarui). Survey, assay dan geologi <b>diganti per hole</b> untuk hole yang ada di file baru; hole lain tidak disentuh.</p>'
 + steps('Menu <b>Data</b> &rarr; <b>&#8645; Tambah / perbarui data bor (upsert)</b>.',
   'Pilih empat file <code>SIM_upsert_*.csv</code>. Baca pratinjau di atas ([[upsert_pratinjau]]) sebelum melanjutkan.',
   'Klik tombol upsert. Folder proyek otomatis membuat backup <i>sebelum upsert</i>.',
   f"Pesan hasil ([[upsert_hasil]]): <b>{clean(N['upsToast'])}</b>")
 + fig('upsert_pratinjau', f"Pratinjau upsert: {N['upsTambah']} collar baru, {N['upsTambah']} hole diganti untuk survey / assay / geologi, 0 hole lama terpengaruh.")
 + fig('upsert_hasil', f"Sesudah upsert: {N['nHole']+N['upsTambah']:,} lubang.".replace(",",".")+' Tombol <b>&#8630; Batalkan upsert terakhir</b> muncul di menu Data. Block model GC tetap termuat.')
 + '<h3>Memperbarui flag dan string</h3>' + steps(
   f"Domain aktif QV_Lensa2, <b>Lingkup</b> semua hole, <b>Jangan timpa flag lain</b> aktif, lalu <b>Usulkan ke domain aktif</b>: {clean(N['autoInfill']).split('. Periksa')[0]}.",
   'Koreksi intercept QV_Splay_HW pada hole infill seperti {{B:Koreksi flag}}.',
   f"Klik <b>&#10148;&#10148; Semua section</b> lagi: <b>{clean(N['strUpd'])}</b>")
 + fig('upsert_string_baru', f"Section tengah setelah infill: string QV_Lensa2 diperbarui melewati kontak bor baru dan solid ikut diperbarui otomatis ({clean(N['solidInfillMsg'])}): volume QV_Lensa2 {fN(SOLI['QV_Lensa2'][1])} m&sup3;, {SOLI['QV_Lensa2'][8]}/{SOLI['QV_Lensa2'][8]} interval flag di dalam solid.")
 + why('String yang pernah diedit manual dilewati (tidak ditimpa) supaya interpretasi geologist tidak hilang. Hapus tanda edit atau edit lagi secara manual bila memang perlu diubah.'))

ch('Wireframe Leapfrog menjadi domain GC-Ex', dta('<code>data/QV_Lensa2_Leapfrog.obj</code> (atau <code>.msh</code> / <code>.dxf</code> / <code>.dtm</code>+<code>.str</code> milik Anda sendiri)',
     [('Mode B &mdash; isian', 'wireframe: <code>QV_Lensa2_Leapfrog</code> &middot; <b>spasi section</b>: <b>20 m</b> (= spasi bor latihan; untuk vein tipis pakai lebih rapat) &middot; nama domain: kosongkan'),
      ('Yang diklik', '<b>Serap sekarang</b>'),
      ('Yang dibaca', 'selisih <b>volume wireframe &rarr; volume solid</b>; di bawah ~15% wajar'),
      ('Mode A &mdash; isian', 'tidak ada; node anak domain &rarr; <b>Pakai EKSAK: QV_Lensa2_Leapfrog</b>'),
      ('Audit', 'catat tonase Reporting BM sebelum dan sesudah <b>Pakai EKSAK</b>, lalu <b>Lepaskan dari wireframe</b>')]) +  '<p>Pekerjaan yang paling sering terjadi di tambang: model implicit dibuat rekan Anda di <b>Leapfrog Geo</b>, lalu <b>Anda</b> yang melanjutkannya di GC-Ex &mdash; memperbarui bentuknya setiap ada bor grade control baru. GC-Ex menerima wireframe itu dan menjadikannya <b>domain miliknya sendiri</b> yang bisa diedit, bukan benda asing yang sekadar ditumpangkan.</p>'
 + '<h3>Dua mode, dua tujuan berbeda</h3>'
 + '<table class="t"><tr><th></th><th>Mode B &mdash; <b>diserap</b></th><th>Mode A &mdash; <b>eksak</b></th></tr>'
 + '<tr><td>Bentuk solid</td><td>rekonstruksi; kesetiaan diatur spasi section</td><td><b>identik</b> dengan mesh Leapfrog</td></tr>'
 + '<tr><td>Bisa diedit di GC-Ex</td><td><b>ya</b> &mdash; jadi string kontrol HW / FW</td><td>tidak</td></tr>'
 + '<tr><td>Ikut berubah saat ada bor baru</td><td><b>ya</b> (lewat Autorun Wireframe)</td><td>tidak &mdash; harus balik ke Leapfrog</td></tr>'
 + '<tr><td>Untuk apa</td><td><b>kerja harian</b>: melanjutkan model orang lain</td><td><b>audit</b>: membandingkan tonase batas Leapfrog vs solid GC-Ex</td></tr></table>'
 + '<p>Keduanya ada di menu klik-kanan tiap berkas di node <b>Import Wireframe Geologi</b> &mdash; satu-satunya tempat mengimpor dan melihat wireframe geologi.</p>'
 + '<h3>Mode B &mdash; satu perintah</h3>'
 + steps('Node <b>Import Wireframe Geologi</b> &rarr; import wireframe-nya (<code>.msh</code>, <code>.obj</code>, <code>.dxf</code>, atau <code>.dtm</code> + <code>.str</code> Surpac).',
         'Klik tombol &#8943; berkasnya &rarr; <b>Serap jadi domain yang bisa diedit (Mode B)&hellip;</b> (atau tombol &#8943; node &rarr; <b>Serap wireframe &rarr; domain&hellip;</b>)',
         'Isi tiga hal saja: <b>wireframe mana</b>, <b>spasi section</b>, dan <b>nama domain</b> (kosongkan untuk ikut nama berkasnya).',
         'Tekan <b>Serap sekarang</b>.')
 + '<p>Yang dikerjakan GC-Ex, berurutan, dan semuanya dilaporkan:</p>'
 + kv([('0. Wireframe', 'jumlah segitiga, <b>volume mesh</b>, dan apakah <b>tertutup rapat</b>'),
       ('1. Domain', 'dibuat baru, atau dipakai ulang bila namanya sudah ada (= serap ulang)'),
       ('2. Flag interval bor', 'interval yang titik tengahnya <b>di dalam</b> wireframe di-flag ke domain itu'),
       ('3. Section', '<b>strike wireframe</b> dihitung dari verteksnya, section dipasang <b>tegak lurus strike</b>'),
       ('4. String kontrol', 'tiap irisan tertutup dibelah menjadi string <b>HW</b> dan <b>FW</b>, ditandai <code>wf:&lt;nama berkas&gt;</code>; solid domain dinyalakan bila masih mati'),
       ('5. Solid RBF', 'solid dibangun, lalu <b>volumenya dibandingkan dengan volume wireframe</b>')])
 + why('Inilah yang dimaksud &ldquo;diserap&rdquo;: wireframe dibongkar menjadi <b>bahasa asli GC-Ex</b> &mdash; string kontrol HW/FW. Sesudah itu domainnya tidak bisa dibedakan dari domain yang Anda gambar sendiri: titik string bisa ditarik, section bisa ditambah, solid rebuild otomatis, dan <b>Autorun Wireframe</b> ({{B:Autorun: wireframe}}) memperbaruinya setiap ada bor baru.')
 + '<h3>Kontrol mutu: selisih volume</h3>'
 + '<p>Analogi dengan import <code>.mdl</code> tidak sepenuhnya tepat, dan ini perlu dipahami. Block model <code>.mdl</code> masuk <b>persis apa adanya</b>. Wireframe <b>tidak</b>: ia diresample sesuai spasi section, lalu RBF menghaluskannya. Karena itu langkah 5 selalu melaporkan:</p>'
 + kv([('Volume wireframe &rarr; volume solid', 'beserta <b>selisih persennya</b>'),
       ('Selisih di bawah ~15%', 'wajar untuk rekonstruksi'),
       ('Selisih lebih besar', 'GC-Ex <b>menyebut sebabnya</b> dan saran yang sesuai sebab itu &mdash; bukan saran umum')])
 + '<p>Diagnosisnya memakai angka yang terukur, yaitu <b>tebal vein sebenarnya</b>: median jarak antara pasangan titik kontak HW dan FW di setiap intersep bor.</p>'
 + '<table class="t"><tr><th>Sebab terdeteksi</th><th>Saran</th></tr>'
 + '<tr><td>Tebal vein sebenarnya <b>lebih tipis</b> daripada <b>Tebal minimum</b> solid</td><td>turunkan Tebal minimum di Geomodeller Vein &#9315;. <b>Merapatkan spasi section tidak akan menolong sedikit pun</b> untuk sebab ini</td></tr>'
 + '<tr><td>Solid <b>memanjang searah strike</b> di luar ujung irisan wireframe (radius pengaruh)</td><td>kecilkan radius pengaruh strike, atau rapatkan spasi section supaya ujung wireframe terwakili</td></tr>'
 + '<tr><td>Volume solid justru <b>kurang</b> dari volume wireframe</td><td>irisan terlalu jarang, atau ada irisan terbuka / terlalu kecil yang dilewati &mdash; rapatkan spasi section</td></tr></table>'
 + why('Tanpa diagnosis ini, saran yang muncul akan selalu &ldquo;rapatkan spasi section&rdquo; &mdash; dan untuk vein yang lebih tipis daripada tebal minimum solid, saran itu <b>salah</b>: serapat apa pun irisannya, solid tetap dipatok di tebal minimumnya. Saran yang salah lebih berbahaya daripada tidak ada saran, karena waktu terbuang dan sebab sebenarnya tidak tersentuh.')
 + tip('Spasi section adalah pengendali kesetiaan bentuk. Untuk vein tipis, pakai spasi serapat spasi bor atau lebih rapat. Bagian wireframe yang lebih halus daripada spasi irisan memang tidak akan terwakili &mdash; itu bukan kesalahan, itu konsekuensi resampling, dan angka selisih volume membuatnya terukur, bukan tersembunyi.')
 + warn('Bila wireframe <b>tidak tertutup rapat</b> (GC-Ex menghitung sisi terbuka), uji titik-di-dalam tidak bisa dipercaya: flag interval bisa salah dan volumenya tidak bermakna. Rapikan dulu di Leapfrog. GC-Ex tetap memberi tahu dan tetap mau mengerjakannya, tetapi angkanya jangan dipakai.')
 + '<h3>Serap ulang saat rekan Anda memperbarui model di Leapfrog</h3>'
 + '<p>Serap lagi ke <b>nama domain yang sama</b>. Aturannya sama dengan autorun:</p>'
 + '<table class="t"><tr><th>Keadaan string</th><th>Yang dilakukan</th></tr>'
 + '<tr><td>String impor lama di section yang sama</td><td><b>diganti</b> oleh irisan wireframe baru</td></tr>'
 + '<tr><td>String yang <b>Anda edit tangan</b></td><td><b>dilewati</b> &mdash; pekerjaan Anda tidak hilang</td></tr></table>'
 + warn('Konsekuensinya perlu disadari: sejak wireframe diserap, <b>GC-Ex menjadi sumber kebenaran bentuknya</b>, bukan Leapfrog lagi. Bila rekan Anda terus memperbarui di Leapfrog sementara Anda mengedit di GC-Ex, kedua model itu akan berbeda. Laporan penyerapan menyebutkan berapa section yang dilewati karena sudah diedit &mdash; angka itu adalah ukuran seberapa jauh kedua model sudah berpisah. Sepakati di tim siapa yang memegang bentuk resminya.', 'Siapa pemegang bentuk resmi')
 + '<h3>Mode A &mdash; wireframe dipakai eksak</h3>'
 + '<p>Klik tombol &#8943; berkas wireframe di node <b>Import Wireframe Geologi</b> &rarr; <b>Kunci domain &lt;nama domain&gt; ke wireframe ini</b>. Domain itu lalu memakai <b>mesh Leapfrog apa adanya</b> sebagai batas &mdash; uji titik-di-dalam dan volumenya dari mesh itu, tanpa RBF. Badge berkasnya menjadi <code>eksak: &lt;nama domain&gt;</code>; <b>Lepaskan domain &hellip;</b> mengembalikannya ke solid RBF.</p>'
 + '<p>Karena disambungkan pada fungsi pembaca solid domain, mode eksak otomatis berlaku di <b>estimasi</b>, <b>estimasi waste</b>, <b>sub-blocking</b>, <b>filter posisi</b> dan <b>pelaporan</b> &mdash; tidak ada pengaturan lain yang perlu diubah.</p>'
 + steps('Jalankan estimasi dengan <b>solid GC-Ex</b> hasil serap, catat tonase dan kadarnya di Reporting BM.',
         'Node anak domain &rarr; <b>Pakai EKSAK</b>, jalankan estimasi lagi, catat angkanya.',
         'Bandingkan. Selisih tonase menunjukkan seberapa besar pengaruh rekonstruksi terhadap angka yang dilaporkan.',
         'Selesai audit: <b>Lepaskan dari wireframe</b> untuk kembali ke solid yang bisa diedit.')
 + tip('Bila proyek dibuka kembali tetapi wireframe-nya belum diimport ulang di node Import Wireframe Geologi, domain mode eksak <b>otomatis kembali</b> memakai solid RBF-nya dan node itu menampilkannya redup dengan tanda <code>(hilang)</code>. Jadi proyek tidak pernah gagal dibuka karena berkas acuan yang tertinggal.'))

ch('Filter domain & statistik', dta('lanjutan &mdash; komposit dari interval ber-flag',
     [('Domain untuk analisis', '<b>Domain vein (Geomodeller Vein)</b>, centang <b>QV_Lensa2</b> saja'),
      ('Sayatan', 'sejajar bidang vein: strike <b>45&deg;</b>, dip <b>70&deg;</b>, tebal slab <b>40 m</b>, posisi <b>0</b>'),
      ('Yang diklik', '<b>Geostatistik</b> di bar atas &rarr; <b>Hitung</b>'),
      ('Hasil yang seharusnya', f"n = <b>{N['gsN']}</b> komposit 1 m, rata-rata <b>{N['gsMean']}</b> g/t"),
      ('Tab Profil', 'sumbu <b>RL</b>, lebar pita <b>10 m</b>, garis acuan <b>250</b> (paleo-muka air tanah)')]) +  steps(
 'Menu <b>Geologi</b> &rarr; <b>Domain untuk analisis</b>: pilih <b>Domain vein (Geomodeller Vein)</b>, lalu centang <b>QV_Lensa2</b> saja ([[domain_filter]]).',
 'Atur sayatan <b>sejajar bidang vein</b>: strike 45&deg;, dip 70&deg;, tebal slab 40 m (&plusmn;20 m), posisi 0.',
 'Klik <b>Geostatistik</b> di bar atas lalu <b>&#8635; Hitung</b>. Tab <b>Statistik</b> ([[geostat_statistik]]).')
 + fig2('domain_filter', 'Filter <b>Domain vein</b>. Filter berlaku untuk tampilan assay, ringkasan, geostatistik, KNA dan estimasi OK.',
        'export_database', 'Menu Data setelah <b>Export database (CSV)</b> ({{B:Export}}).')
 + fig('geostat_statistik', f"Statistik komposit 1 m domain QV_Lensa2: n = {N['gsN']}, rata-rata {N['gsMean']} g/t" + (f", declustered {fN((N.get('gsSt') or {}).get('dec'),3)} g/t, CV {fN((N.get('gsSt') or {}).get('cv'),2)}, maksimum {fN((N.get('gsSt') or {}).get('max'),2)} g/t." if N.get('gsSt') else '.'))
 + ('<h3>Kurva pemusatan logam (0.24.24)</h3>' + steps('Masih di tab <b>Statistik</b>, gulir ke grafik <b>Pemusatan logam</b>: % sampel teratas terhadap % logam terkumpul ([[geostat_logam]]).',
     'Tabel di bawahnya memberi <b>ambang kadar</b> untuk 1 / 2,5 / 5 / 10% sampel teratas; tombol <b>Pakai sebagai top-cut</b> mengisi top-cut dan menghitung ulang.')
    + fig('geostat_logam', 'Pemusatan logam domain QV_Lensa2: ' + '; '.join('%s%% sampel teratas (&ge; %s g/t) = %s%% logam' % (str(q[0]).replace('.', ','), fN(q[1], 2), str(q[2]).replace('.', ',')) for q in (N.get('mc') or [])[:3]) + '.')
    + tip('Bila 1% sampel teratas memuat lebih dari &plusmn;10% logam, kadar ekstrem terlalu berpengaruh pada rata-rata: pertimbangkan top-cut, lalu cocokkan dengan titik patah kurva log-probability dan tabel top-cut.') if ('geostat_logam' in FIG) else '')
 + ('<h3>Profil vertikal: zonasi kadar (0.24.24)</h3>' + steps('Tab <b>Profil</b> di panel Geostatistik. Sumbu <b>RL</b>, lebar pita 10 m. Panel bawaan: Au, rasio Ag/Au, jumlah Pb+Zn, dan % kode tekstur colloform / crustiform (bila ada kolom tekstur).',
     'Isi <b>Garis acuan</b> (mis. paleo-muka air tanah RL 250) dan labelnya. Panel bisa ditambah / diganti: unsur, rasio, jumlah, atau % kode geologi apa pun.',
     'Filter domain aktif, hole, dan (opsional) slab sayatan ikut berlaku. <b>CSV</b> dan <b>PNG</b> untuk laporan ([[geostat_profil]]).')
    + fig('geostat_profil', ('Profil vertikal domain QV_Lensa2 per pita RL 10 m dari %s interval: %s.' % (fN(N['pf']['n']), ', '.join(N['pf']['lbl']))) if isinstance(N.get('pf'), dict) and N['pf'].get('lbl') else 'Profil vertikal domain QV_Lensa2 per pita RL 10 m: Au, rasio Ag/Au, Pb+Zn dan % tekstur terhadap RL, dengan garis acuan paleo-muka air tanah.')
    + why('Profil vertikal menunjukkan <b>batas zona</b> (zona didih, base-metal, tudung tercuci) sebelum domain estimasi dibuat. Interval di kedua sisi batas zona sebaiknya menjadi domain berbeda.') if ('geostat_profil' in FIG) else '')
 + why('Rata-rata <i>declustered</i> lebih rendah dari rata-rata biasa karena sampel kadar tinggi di ore shoot dibor lebih rapat. Gunakan histogram skala log dan persentil P95&ndash;P99 untuk memutuskan perlu tidaknya top-cut.'))

ch('Domain aktif di Geostatistik & Model Estimation (versi 0.20)', '<p>Mulai GC-Ex Drill Hole Ultimate <b>0.20</b>, satu <b>domain aktif</b> dipakai bersama oleh Geomodeller Vein, Geostatistik dan Model Estimation. Domain bisa diaktifkan dari node domain di bawah <b>Geomodeller Vein</b>, <b>Geostatistik</b> atau <b>Model Estimation</b> di Project Tree, sehingga tidak perlu kembali ke Geomodeller Vein.</p>'
 + steps('Project Tree &rarr; <b>Geostatistik</b> &rarr; klik <b>QV_Lensa2</b>. Panel Geostatistik terbuka dengan bilah <b>Domain: QV_Lensa2</b> &mdash; komposit hanya dari interval bor yang di-flag ke QV_Lensa2 (beserta cabangnya; untuk selubung: interval halo) ([[dom20_gs]]).',
   'Untuk melihat semua sampel (perilaku lama), pilih <b>Semua data (tanpa filter domain)</b> di node Geostatistik atau di bilah Domain.',
   'Setelah fitting, <b>Simpan ke domain</b> otomatis memilih domain aktif.',
   'Project Tree &rarr; <b>Model Estimation</b> &rarr; klik domain: domain itu menjadi aktif dan parameternya tampil di Properti ([[dom20_me]]). Centang di node domain = ikut <b>Jalankan semua domain</b>.',
   'Bagian Jalankan: <b>&#9654; Jalankan domain aktif</b> hanya mengestimasi domain aktif; <b>&#9654; Jalankan semua domain</b> mengestimasi semua domain yang dicentang. Keduanya juga ada di menu &hellip; node Model Estimation.')
 + fig2('dom20_gs', 'Geostatistik dengan <b>domain aktif</b> QV_Lensa2: hanya sampel di dalam domain.', 'dom20_me', 'Model Estimation: Properti menampilkan domain aktif yang dipilih dari Project Tree.')
 + tip('Filter <b>Domain untuk analisis</b> di menu Geologi ({{B:Filter domain}}) tetap berlaku di atas domain aktif. Bila filter itu tidak dipakai, domain aktif sudah cukup untuk memisahkan sampel per domain.'))

ch('Variogram, anisotropi & model', dta('lanjutan &mdash; komposit domain QV_Lensa2 dari bab sebelumnya',
     [('Yang diisi', 'tidak ada angka wajib &mdash; klik <b>Auto-fit ulang</b> di tab <b>Model</b>'),
      ('Bila perlu disetel', 'lag dan toleransi di <b>Parameter analisis</b>'),
      ('Hasil yang seharusnya', 'nugget <b>0,648</b>, satu struktur sferis C1 <b>0,349</b>, range mayor <b>108,5 m</b>, semi <b>43 m</b>, downhole <b>6 m</b>')]) +  steps(
 'Tab <b>Variogram</b>: variogram eksperimental arah major, semi-major dan downhole beserta model ([[geostat_variogram]]). Tabel di bawah memberi jumlah pasangan per lag.',
 'Tab <b>Anisotropi</b>: range per arah (pitch) di bidang sayatan; elips menunjukkan arah major / semi-major ([[geostat_anisotropi]]).',
 'Klik <b>Auto-fit ulang</b> di tab <b>Model</b>, lalu koreksi bila perlu. Parameter langsung dipakai estimasi ([[geostat_model]]).')
 + fig('geostat_variogram', 'Variogram eksperimental (titik) dan model (garis). Label pasangan bisa dimatikan; data bisa diunduh ke CSV.')
 + fig('geostat_anisotropi', 'Rose range per pitch: range terpanjang sekitar pitch 85&deg; (searah dip / ore shoot).')
 + fig('geostat_model', 'Tab Model dan ringkasan parameter OK: nugget 0,648, satu struktur sferis C1 0,349, range major 108,5 m, semi 43 m, downhole 6 m.')
 + warn('Nugget 65% tergolong tinggi tetapi wajar untuk emas vein sempit. Periksa ulang dengan mengubah lag atau toleransi di <b>Parameter analisis</b> sebelum menerima model.'))

def okp(i):
    for k,v in okm.items():
        if k.startswith('Pass %d (' % i): return k.split('(')[1].rstrip(')'), v
    return ('', '')
ME1 = json.loads(N['me1']); ME2 = json.loads(N['me2']); MEB = N['meBM']
m1 = {r[0]: r for r in ME1}; m2 = {r[0]: r for r in ME2}
u1, h1, u2 = m1['QV_Lensa2'], m1['QV_Splay_HW'], m2['QV_Lensa2']
kp = N.get('knaPass1', '1,4,24,4').split(',')
ch('Kriging Neighbourhood Analysis (KNA)', dta('lanjutan &mdash; model variogram bab sebelumnya',
     [('Ukuran blok', '<b>5 &times; 5 &times; 2,5 m</b> (diisi di tab Uji estimasi)'),
      ('Jumlah blok uji', '<b>10</b>'),
      ('Maks sampel diuji', '<b>6, 8, 12, 16, 20, 24, 32</b>'),
      ('Faktor radius', '<b>0,75 / 1 / 1,5 / 2</b>'),
      ('Hasil yang seharusnya', f"Pass 1 = radius &times;{kp[0]}, {kp[1]}&ndash;{kp[2]} sampel, maks {kp[3]} per hole &mdash; klik <b>Terapkan ke Pass 1</b>")]) +  steps(
 'Tab <b>KNA</b>. Isi ukuran blok pada tab Uji estimasi dulu: 5 &times; 5 &times; 2,5 m.',
 'Biarkan <b>Jumlah blok uji</b> 10, <b>Maks sampel diuji</b> 6, 8, 12, 16, 20, 24, 32, <b>Faktor radius</b> 0,75 / 1 / 1,5 / 2. Klik <b>Jalankan KNA</b>.',
 f'Baca rekomendasi ([[geostat_kna]]) lalu klik <b>Terapkan ke Pass 1</b>. Pada latihan ini Pass 1 menjadi radius &times;{kp[0]}, {kp[1]}&ndash;{kp[2]} sampel, maks {kp[3]} per hole.')
 + fig('geostat_kna', 'Hasil KNA: grafik Slope of Regression dan Kriging Efficiency terhadap jumlah sampel untuk tiap faktor radius.')
 + kv([('Rekomendasi', clean(N['kna']).split('Patokan')[0]), ('Patokan umum', 'SoR &ge; 0,9 dan KE &ge; 0,5 untuk blok <i>measured</i>; menambah sampel setelah SoR mendatar hanya menambah smoothing.')]))

ch('Uji estimasi & simpan parameter ke domain', dta('lanjutan &mdash; parameter hasil KNA',
     [('Ukuran blok', '<b>5 &times; 5 &times; 2,5 m</b>'),
      ('Diskretisasi', '<b>3, 3, 2</b>'),
      ('Batas atas', '<b>di bawah topografi</b>'),
      ('Domain pada Simpan', '<code>QV_Lensa2</code>, lalu ulangi untuk <code>QV_Splay_HW</code>'),
      ('Hasil yang seharusnya', f"{fN(N['ok'])} blok terestimasi; pesan simpan: {clean(N['gsDomMsg'])}")]) +  '<p>Tab <b>Uji estimasi</b> di Geostatistik adalah estimasi cepat pada grid blok sendiri untuk <b>menilai parameter</b> (bukan block model produksi). Bila parameter sudah dirasa tepat, parameter itu <b>disimpan ke domain</b> dan dipakai menu <b>Model Estimation</b> ({{B:Model Estimation}}).</p>'
 + steps('Tab <b>Uji estimasi</b>: blok 5 &times; 5 &times; 2,5 m, <b>Diskretisasi</b> 3,3,2, <b>Batas atas</b> di bawah topo.',
   f'Pass: radius &times;1 ({okp(1)[0]}), &times;1,5 ({okp(2)[0]}), &times;2,5 ({okp(3)[0]}).',
   'Klik <b>Jalankan estimasi OK</b> dan tunggu bilah kemajuan penuh ([[estimasi_ok_hasil]]). Tampilkan hasil lewat <b>Tampilan block model</b> ([[estimasi_ok_3d]], [[estimasi_ok_2d]]).',
   'Gulir ke bawah: kotak <b>Simpan parameter ke domain</b>. Pilih <b>QV_Lensa2</b> (otomatis terpilih karena filter domain) lalu klik <b>&#8681; Simpan ke domain</b> ([[simpan_ke_domain]]). Ulangi untuk QV_Splay_HW (latihan ini memakai parameter yang sama karena data QV_Splay_HW sedikit).')
 + fig('estimasi_ok_hasil', 'Ringkasan uji estimasi di panel kanan dan blok hasil di 3D.')
 + kv([('Blok terestimasi / kandidat', okm.get('Blok terestimasi / kandidat','')), ('Pass 1 / 2 / 3', '%s / %s / %s blok' % (okp(1)[1], okp(2)[1], okp(3)[1])),
       ('Mean blok vs komposit', '%s vs %s g/t' % (okm.get('Mean estimasi blok'), okm.get('Mean komposit (top-cut)'))),
       ('Rata-rata SoR / KE', '%s / %s' % (okm.get('Rata-rata Slope of Regression'), okm.get('Rata-rata Kriging Efficiency')))])
 + fig('estimasi_ok_3d', 'Hasil uji estimasi di 3D, diwarnai Grade OK.')
 + fig('estimasi_ok_2d', 'Sayatan 2D section tengah: blok uji dengan bor dan string QV_Lensa2.')
 + fig('simpan_ke_domain', f"Kotak <b>Simpan parameter ke domain</b> di bawah tab Uji estimasi: {clean(N['gsDomMsg'])}")
 + why('Uji estimasi mengisi seluruh kotak grid, termasuk blok jauh dari data, sehingga SoR / KE rata-rata rendah. Itu wajar untuk uji. Estimasi produksi di Model Estimation hanya mengisi blok di dalam solid vein.')
 + tip('Yang disimpan ke domain: model variogram dan arah elipsoid (tab Model), pass &amp; diskretisasi, top-cut, panjang komposit, unsur, dan label sayatan sumbernya. Semua bisa diedit lagi di Model Estimation.'))

ch('Model Estimation: estimasi block model GC', dta('block model <code>SIM_BM_GC.csv</code> (sudah di folder proyek) + parameter yang tersimpan di domain',
     [('Kadar GC asli', '<code>AU</code> &mdash; pembanding dan nilai akhir di luar blok estimasi'),
      ('SG', 'kolom SG block model, untuk tonase'),
      ('Domain yang dicentang', '<code>QV_Lensa2</code> dan <code>QV_Splay_HW</code> &mdash; <code>QV_Lensa2_Leapfrog</code> <b>tidak</b> dicentang'),
      ('Bagian &#9314;', '<b>Tambah blok baru di bagian solid tanpa blok GC</b> menyala'),
      ('Hasil yang seharusnya', f"QV_Lensa2 {fN(u1[3])} blok diestimasi ulang + {u1[6]} blok tambahan; block model menjadi {fN(MEB[1])} blok")]) +  '<p>Menu <b>Model Estimation</b> (rel kiri, di bawah Geomodeller Vein) mengestimasi <b>block model GC</b> per domain vein. Aturannya:</p><ul>'
 '<li><b>Sampel</b> = komposit dari interval yang di-flag domain itu saja (batas keras).</li>'
 '<li><b>Blok</b> = blok GC yang titik pusatnya di dalam solid domain ({{B:Membangun solid}}).</li>'
 '<li><b>Koreksi</b>: blok di dalam solid diestimasi ulang. <b>Penambahan</b>: bagian solid tanpa blok GC diisi blok baru seukuran blok dominan.</li>'
 '<li>Hasil ditulis ke <b>atribut baru</b>; atribut GC asli tidak diubah. Blok di luar solid tidak disentuh.</li></ul>'
 + steps('Pastikan block model GC sudah diimport (menu <b>Block Model</b>; di latihan ini <code>SIM_BM_GC.csv</code> dari folder proyek).',
   'Klik <b>Model Estimation</b>. Bagian &#9312;: pilih <b>Kadar GC asli</b> (di sini <code>AU</code>) sebagai pembanding dan nilai akhir di luar estimasi, dan <b>SG</b> untuk tonase.',
   'Bagian &#9313;: tiap domain menunjukkan status solid dan parameter. Centang domain yang ikut run (QV_Lensa2_Leapfrog tidak dicentang). Buka <b>Parameter estimasi</b> untuk melihat / mengedit nugget, sill, range, pass, top-cut dan panjang komposit ([[me_panel]]).',
   'Bagian &#9314;: biarkan <b>Tambah blok baru di bagian solid tanpa blok GC</b> menyala. Kotak status menulis <b>run pertama</b>. Klik <b>&#9654; Jalankan estimasi</b>.',
   'Bagian &#9315; menampilkan validasi per domain ([[me_hasil]]). Klik <b>Tampilkan di Block Model</b> untuk melihat hasil ([[me_bm3d]], [[me_bm2d]]).')
 + fig('me_panel', 'Menu Model Estimation sebelum run: block model GC, domain dengan solid &amp; parameter, dan editor parameter QV_Lensa2 (asal: sayatan Geostatistik).')
 + fig('me_hasil', f"Validasi run pertama. QV_Lensa2: {u1[3]:,} blok di solid diestimasi ulang + {u1[6]} blok tambahan; rata-rata komposit {fN(u1[10],3)} vs estimasi {fN(u1[11],3)} (GC lama {fN(u1[12],3)}). Grafik swath: komposit (titik oranye), estimasi baru (biru), GC lama (abu-abu) per 10 m sepanjang strike.".replace(',', '.'))
 + kv([('QV_Lensa2', f"{u1[5]:,} blok terestimasi (pass 1/2/3: {u1[9][0]}/{u1[9][1]}/{u1[9][2]}), {fN(u1[13])} m&sup3;, {fN(u1[14])} t, logam {fN(u1[15])} g (GC lama {fN(u1[16])} g)".replace(',', '.')),
       ('QV_Splay_HW', (f"tidak ada blok GC di dalam solid &rarr; {h1[6]} blok tambahan, rata-rata estimasi {fN(h1[11],3)} g/t"
                        if h1[11] is not None else
                        f"tidak ada blok GC di dalam solid &rarr; {h1[6]} blok tambahan; {h1[5]} blok terestimasi")),
       ('Block model', f"{MEB[0]:,} blok GC + {MEB[1]-MEB[0]} blok tambahan = {MEB[1]:,} blok".replace(',', '.')),
       ('Waktu', f"{fN(u1[17]/1000,1)} detik")])
 + fig('me_bm3d', 'Menu Block Model setelah <b>Tampilkan di Block Model</b>: diwarnai <code>au_final</code>, hanya blok terestimasi (filter <code>est_type &ge; 1</code>).')
 + fig('me_bm2d', 'Sayatan 2D tebal 2,5 m: blok terestimasi mengikuti solid QV_Lensa2 dan QV_Splay_HW di antara string HW / FW.')
 + '<h3>Atribut baru di block model</h3>' + kv([('au_est','kadar hasil estimasi (&minus;99 bila tidak diestimasi)'),('au_final','au_est bila ada, selain itu kadar GC asli &mdash; dipakai untuk perencanaan'),('domain_est','nama domain vein'),('est_pass / est_nsamp','pass yang berhasil, jumlah sampel'),('est_sor / est_ke / est_kv','slope of regression, kriging efficiency, kriging variance'),('est_type','1 = koreksi blok GC, 2 = blok tambahan'),('est_date / est_run','tanggal (yyyymmdd) dan nomor run terakhir yang mengestimasi blok itu')])
 + why('Atribut GC asli dibiarkan utuh supaya perubahan bisa diaudit dan dibandingkan (rekonsiliasi). Keputusan memakai nilai baru ada di atribut <code>au_final</code>.')
 + warn('Rata-rata estimasi bisa berbeda cukup jauh dari GC lama di zona vein (di sini GC lama jauh lebih rendah karena blok GC 2,5 m mencampur vein dengan waste). Periksa swath plot dan penampang sebelum memakai hasil.'), 'me')

ch('Autorun Estimasi dari Nol: domain baru', dta('lanjutan &mdash; dipakai pada domain yang <b>belum</b> punya parameter (mis. QV_Splay_HW bila Anda belum menyimpan parameter ke sana)',
     [('Blok X / Y', 'usulan <b>5 m</b> (&asymp; sepertiga spasi bor 14,5 m) &mdash; boleh diubah'),
      ('Blok Z', 'usulan <b>3 m</b> (&asymp; tebal vein median)'),
      ('Sub-blocking', 'disarankan <b>nyala</b> karena tebal vein kurang dari 3&times; tinggi blok'),
      ('Minimal komposit', '<b>30</b> &mdash; di bawah ini domain dilewati'),
      ('Nugget maksimal', '<b>80%</b> &mdash; di atas ini ditandai perlu ditinjau'),
      ('Yang dibaca', 'putusan per domain: <b>tersimpan</b> / <b>tinjau</b> / <b>dilewati</b> beserta alasannya')]) +  '<p>Autorun Estimation (update) memakai parameter yang <b>sudah Anda setujui</b>. Untuk domain yang belum punya parameter sama sekali, itu tidak bisa dipakai. Node <b>Autorun Estimasi dari Nol</b> (di bawah Model Estimation) mengisi kekosongan itu &mdash; dan perlu dibaca dengan kesadaran bahwa ia <b>mengusulkan</b>, bukan memutuskan.</p>'
 + '<h3>Yang dikerjakannya</h3>'
 + kv([('Kerangka blok', 'memakai block model aktif, atau membuat <b>kerangka AOI baru</b> bila belum ada'),
       ('Variogram', 'rekomendasi otomatis (lag, transform, top-cut) lalu <b>fitting model</b> &mdash; fungsi yang sama dengan tombol di Geostatistik'),
       ('Lingkungan kriging', '<b>KNA</b> dipindai, lalu kombinasi terbaik (radius &times; faktor, jumlah sampel maksimal) diterapkan'),
       ('Parameter', 'disimpan ke domain, seperti <b>Simpan ke domain</b> yang Anda lakukan manual')])
 + '<h3>Pilihan yang diberikan &mdash; dengan usulan dari data Anda</h3>'
 + '<table class="t"><tr><th>Pilihan</th><th>Usulan dan dari mana</th></tr>'
 + '<tr><td><b>Blok X / Y</b></td><td>&asymp; <b>sepertiga spasi bor</b> (median jarak tiap collar ke collar terdekat). Pada data latihan: spasi 14,5 m &rarr; blok 5 m</td></tr>'
 + '<tr><td><b>Blok Z</b></td><td>&asymp; <b>tebal vein median</b> (jarak pasangan kontak HW&ndash;FW). Pada data latihan: 3 m</td></tr>'
 + '<tr><td><b>Sub-blocking + N</b></td><td>disarankan otomatis bila tebal vein kurang dari <b>3&times;</b> tinggi blok &mdash; batas solid akan kasar tanpa itu</td></tr>'
 + '<tr><td><b>Minimal komposit</b></td><td>bawaan 30; di bawah ini domain <b>dilewati</b></td></tr>'
 + '<tr><td><b>Nugget maksimal</b></td><td>bawaan 80%; di atas ini ditandai perlu ditinjau</td></tr></table>'
 + tip('Angka blok itu <b>usulan dari data</b>, bukan keharusan. Kalau tinggi bench atau selektivitas alat gali Anda menentukan lain, ganti saja &mdash; alasan usulannya ditampilkan supaya Anda bisa menilai mana yang lebih masuk akal untuk tambang Anda.')
 + '<h3>Tiga putusan per domain</h3>'
 + '<p>Karena usulan boleh salah, tiap domain diberi putusan yang tegas:</p>'
 + '<table class="t"><tr><th>Putusan</th><th>Artinya</th></tr>'
 + '<tr><td><b>&#10003; tersimpan</b></td><td>lolos semua gerbang mutu</td></tr>'
 + '<tr><td><b>&#9888; perlu ditinjau</b></td><td>parameter <b>tersimpan tetapi belum layak produksi</b>. Alasannya ditulis</td></tr>'
 + '<tr><td><b>&#10006; dilewati</b></td><td>tidak ada yang disimpan sama sekali</td></tr></table>'
 + '<h3>Gerbang mutunya</h3>'
 + '<table class="t"><tr><th>Pemeriksaan</th><th>Putusan dan alasannya</th></tr>'
 + '<tr><td>Komposit kurang dari ambang</td><td><b>dilewati</b> &mdash; variogram dari sampel sesedikit itu tidak bermakna</td></tr>'
 + '<tr><td>Solid belum terbentuk</td><td><b>dilewati</b> &mdash; jalankan Autorun Wireframe dulu</td></tr>'
 + '<tr><td>Domain <b>sudah punya parameter</b></td><td><b>dilewati</b> &mdash; autorun dari nol tidak pernah menimpa yang sudah Anda setujui</td></tr>'
 + '<tr><td>Nugget di atas ambang</td><td><b>perlu ditinjau</b> &mdash; estimasi akan sangat merata (efek nugget tinggi khas emas kasar)</td></tr>'
 + '<tr><td>Nugget <b>di bawah 5%</b></td><td><b>perlu ditinjau</b> &mdash; pada kadar logam nugget nol praktis tidak pernah terjadi; biasanya berarti variogram belum terbentuk atau pasangan sampel berjarak pendek terlalu sedikit</td></tr>'
 + '<tr><td>Range mayor &asymp; range semi</td><td><b>perlu ditinjau</b> &mdash; <b>anisotropi tidak terselesaikan</b>, elipsoidnya bulat. Untuk vein hampir selalu keliru</td></tr>'
 + '<tr><td>Komposit kurang dari 50</td><td><b>perlu ditinjau</b> &mdash; variogram masih rapuh untuk dipakai produksi</td></tr>'
 + '<tr><td>Range mayor &lt; 2&times; panjang komposit, atau &gt; 3&times; bentang data</td><td><b>perlu ditinjau</b> &mdash; model kemungkinan belum terbentuk atau tidak terkekang</td></tr></table>'
 + why('Dua gerbang terakhir yang disebut di atas &mdash; nugget mendekati nol dan elipsoid bulat &mdash; ditambahkan sesudah uji pertama memperlihatkan variogram yang jelas <b>tidak terbentuk</b> (nugget 0%, range mayor sama dengan range semi, 31 komposit) justru lolos sebagai &ldquo;tersimpan&rdquo;. Memeriksa nugget yang terlalu <i>tinggi</i> saja tidak cukup: nugget nol sama mencurigakannya, dan kesalahan seperti itu tidak terlihat lagi di angka tonase akhir.')
 + '<h3>Bawaannya tidak langsung mengestimasi</h3>'
 + '<p>Pilihan <b>Langsung lanjut mengestimasi</b> ada, tetapi bawaannya <b>mati</b>. Alur yang disarankan:</p>'
 + steps('Jalankan <b>Autorun Estimasi dari Nol</b>, lihat laporannya.',
         'Buka tiap domain bertanda <b>perlu ditinjau</b> di <b>Geostatistik</b>, periksa variogramnya, perbaiki (mis. pasang orientasi manual bila anisotropinya tidak terselesaikan), lalu <b>Simpan ke domain</b> lagi.',
         'Setelah semua domain bersih, jalankan <b>Autorun Estimation (update)</b> ({{B:Autorun: wireframe}}).')
 + warn('Angka sumber daya tidak boleh dilaporkan dari parameter yang belum pernah Anda lihat sendiri. Autorun dari nol memangkas waktu mengetik dan mencoba-coba, <b>bukan</b> tanggung jawab geologistnya.', 'Batas tanggung jawab'))

ch('Koreksi setelah bor baru', dta('<code>data/SIM_upsert2_collar.csv</code>, <code>SIM_upsert2_survey.csv</code>, <code>SIM_upsert2_assay.csv</code>, <code>SIM_upsert2_geologi.csv</code> &mdash; infill tahap 2',
     [('Langkah', 'upsert keempat berkas &rarr; usulan otomatis (<b>Dilusi internal maks. 2 m</b>) &rarr; <b>Semua section</b> &rarr; <b>Jalankan estimasi</b> lagi'),
      ('Yang dibaca', f"kotak status: {clean(N['mePending'])[:140]}"),
      ('Hasil yang seharusnya', f"hanya {m2['QV_Lensa2'][2]} hole baru / berubah yang memicu koreksi, bukan seluruh block model")]) +  '<p>Inilah pemakaian sehari-hari: setiap ada bor baru, GC-Ex hanya mengestimasi ulang blok yang <b>lingkungan kriging-nya</b> berubah, yaitu blok yang memakai komposit dari hole baru / berubah, ditambah blok yang baru masuk solid. Blok lain tetap nilai run sebelumnya.</p>'
 + steps('Menu <b>Data</b> &rarr; <b>Tambah / perbarui data bor (upsert)</b>: pilih <code>SIM_upsert2_*.csv</code> (2 bor infill SIM-INF-05 dan 06 di ujung timur).',
   f"Geomodeller Vein: <b>Usulkan ke domain aktif</b> dengan <b>Jangan timpa flag lain</b> (dilusi 2 m): {clean(N['autoInfill2']).split('. Periksa')[0]}. Lalu <b>&#10148;&#10148; Semua section</b>; solid QV_Lensa2 diperbarui otomatis.",
   'Buka <b>Model Estimation</b>. Kotak status di bagian &#9314; menyebut hole yang berubah ([[me_tertunda]]): ' + clean(N['mePending']).replace('\n','; ') + '.',
   'Klik <b>&#9654; Jalankan estimasi</b>. Validasi menunjukkan berapa blok yang dikoreksi ([[me_koreksi]]).',
   'Untuk melihat blok mana yang diperbarui, warnai block model dengan <code>est_run</code> ([[me_run]]).')
 + fig('me_tertunda', 'Sebelum run kedua: GC-Ex mendeteksi 2 hole baru untuk QV_Lensa2; QV_Splay_HW tidak berubah sehingga tidak ada blok yang dihitung ulang.')
 + fig('me_koreksi', f"Run kedua: QV_Lensa2 hanya {u2[4]:,} dari {u2[3]:,} blok di solid diestimasi ulang, {u2[6]} blok tambahan, {u2[7]} blok kembali ke GC karena solid berubah bentuk. QV_Splay_HW: 0 blok.".replace(',', '.'))
 + fig('me_run', 'Block model diwarnai <code>est_run</code>: biru = run 1, oranye = run 2 (blok di sekitar bor infill baru).')
 + kv([('Hole berubah', u2[18]), ('Blok di solid / dikoreksi', f"{u2[3]:,} / {u2[4]:,}".replace(',', '.')), ('Kembali ke GC (keluar solid)', str(u2[7])), ('Rata-rata komposit / estimasi', f"{fN(u2[10],3)} / {fN(u2[11],3)}")])
 + tip('Setelah mengubah parameter (variogram, pass, top-cut), centang <b>Estimasi ulang semua blok di dalam solid</b>: perubahan parameter mempengaruhi semua blok, bukan hanya sekitar bor baru. GC-Ex memberi peringatan bila parameter berubah sejak run terakhir.')
 + tip('<b>Batalkan run terakhir</b> mengembalikan hasil sebelum run. Riwayat semua run (tanggal, pengguna, hole yang berubah, jumlah blok) ada di <b>Riwayat run</b> dan bisa diunduh sebagai CSV.'))

SP = N['split'] if isinstance(N.get('split'), dict) else json.loads(N['split'])
SPM = N['splitMe'] if isinstance(N.get('splitMe'), list) else json.loads(N['splitMe'])

def g(k, d=None):
    v = N.get(k, d)
    return d if v is None else v
def hv(k): return k in FIG
def figs(*pairs):
    """gambar hanya bila tangkapan layarnya ada (tahap tangkapan layar boleh gagal tanpa menggagalkan PDF)"""
    return ''.join(fig(k, c) if hv(k) else '' for k, c in pairs)
AH = g('aoiHasil', {}) or {}; SBH = g('sbHasil', {}) or {}; WL0 = g('wsLast', {}) or {}
def asal(nm):
    for r in (AH.get('asal') or []):
        if r[0] == nm: return r[1]
    return None
def fz(v, d=0): return fN(v, d) if isinstance(v, (int, float)) else '&ndash;'

ch('Block model dari nol: kerangka AOI', dta('lanjutan &mdash; block model aktif ' + f"<code>SIM_BM_GC.csv</code> ({fN(N['aoiBase'][0])} blok)",
     [('Perlakuan', '<b>Pertahankan &amp; isi kekosongan</b>'),
      ('Extent', 'E <b>504.800 &ndash; 505.200</b>, N <b>9.011.800 &ndash; 9.012.200</b>'),
      ('Ukuran blok', '<b>10 &times; 10 &times; 5 m</b> (sama dengan model impor)'),
      ('Batas', 'centang <b>Potong topografi aktif</b>; desain pit tidak dipakai'),
      ('Hasil yang seharusnya', f"{fN(AH.get('n'))} blok &mdash; {fN(asal('impor'))} impor dipertahankan + {fN(asal('kerangka'))} blok kerangka baru")]) +  '<p>Sampai versi 0.24.15, GC-Ex Drill Hole <b>selalu memerlukan block model dari luar</b>: estimasi hanya mengoreksi blok yang pusatnya di dalam solid domain, sehingga material <b>waste</b> di sekitar wireframe hanya ada bila model impornya memang memuatnya. Tombol <b>&#8862; Buat kerangka blok (AOI)</b> di menu <b>Block Model</b> membuat grid persegi seluruh <i>area of interest</i> &mdash; ore <b>dan</b> waste &mdash; dari extent, ukuran blok dan RL yang Anda tentukan. Kerangkanya murni geometri, jadi berlaku untuk semua tipe deposit.</p>'
 + kv([('Belum ada block model','mode <b>Ganti</b>: seluruh AOI dibuat dari nol'),
       ('Sudah ada .mdl, cakupannya lebih sempit','mode <b>Pertahankan &amp; isi kekosongan</b>: model impor dipertahankan <b>utuh</b> (termasuk kadar dan sub-bloknya), blok baru hanya di sel AOI yang belum tercakup'),
       ('Batas','potong topografi aktif (hanya blok di bawah permukaan), di dalam desain pit, rentang RL, poligon area dari Map / string Surpac')])
 + steps('Menu <b>Block Model</b> &rarr; <b>&#8862; Buat kerangka blok (AOI)</b>. Extent bawaan = seluruh data bor + block model aktif.',
   'Latihan: perlakuan <b>Pertahankan &amp; isi kekosongan</b>, extent E 504.800&ndash;505.200, N 9.011.800&ndash;9.012.200, ukuran blok <b>10 &times; 10 &times; 5 m</b> (sama dengan model impor), centang <b>Potong topografi aktif</b>.',
   'Klik <b>Hitung jumlah blok</b> &mdash; ukuran grid, blok baru, blok impor yang dipertahankan, dan yang dibuang per sebab muncul sebelum apa pun dibangun ([[aoi_dialog]]).',
   'Klik <b>Buat kerangka &rarr;</b>. Atribut kategori <code>AOI_ASAL</code> membedakan <b>impor</b> dan <b>kerangka</b> ([[aoi_2d]]).')
 + figs(('aoi_dialog', 'Dialog kerangka AOI. ' + clean(g('aoiPrev', ''))[:260]),
        ('aoi_2d', f"Sayatan 2D berwarna AOI_ASAL: blok impor {fz(asal('impor'))} dipertahankan, {fz(asal('kerangka'))} blok kerangka baru mengisi area di luar cakupan model impor (total {fz(AH.get('n'))} blok)."))
 + (fig('u_aoi', 'Kerangka blok AOI pada satu sayatan, dihitung langsung dari data latihan: %s blok di bawah topografi, %s di antaranya di dalam desain pit. Permukaan yang dipakai sama dengan Reporting BM.' % (NU.get('aoi_blok', '-'), NU.get('aoi_pit', '-'))) if hv('u_aoi') else '')
 + warn('Blok kerangka <b>belum punya kadar</b> (atribut numerik NaN). Kadarnya diisi Model Estimation: domain vein untuk ore ({{B:Model Estimation}}), domain WASTE untuk sisanya ({{B:Estimasi waste}}). Versi block model berjenis <code>aoi</code> menyimpan <b>parameter</b> saja, jadi file proyek tetap ringan.'))

ch('Sub-blocking & proporsi volume (sb_frac)', dta('lanjutan &mdash; kerangka AOI bab sebelumnya',
     [('Tingkat pecah', '<b>1 tingkat</b>'),
      ('Yang diklik', '<b>Hitung jumlah blok</b> lalu <b>Pecah blok &rarr;</b>'),
      ('Hasil yang seharusnya', f"{fN(SBH.get('n'))} blok; {fN(SBH.get('part'))} blok di perbatasan ber-<code>sb_frac</code> 0&ndash;1"),
      ('Sesudahnya', 'jalankan ulang <b>Model Estimation</b> (posisi blok berubah), lalu pilih <code>sb_frac</code> di Reporting BM')]) +  '<p>Blok dihitung utuh berdasarkan <b>titik pusatnya</b>: blok yang separuh di dalam vein dan separuh di luar tetap dihitung 100% ore atau 100% waste. Pada vein setebal 1&ndash;4 m dengan blok 5 m, kesalahan batas itu sendiri sebesar dilusi yang mau diukur.</p>'
 + kv([('&#9707; Pecah blok di batas solid','blok yang <b>menyeberangi</b> batas solid dipecah <b>2 &times; 2 &times; 2</b>, 1&ndash;3 tingkat (uji 27 titik per blok). Sub-blok yang sudah ada dihormati; hasilnya tetap bisa ditulis ke .mdl Surpac (octree).'),
       ('&#9634; Hitung proporsi volume ore per blok','tanpa memecah: proporsi volume tiap blok yang di dalam solid, atribut <code>sb_frac</code> (0&ndash;1)')])
 + steps('Menu <b>Block Model</b> &rarr; <b>Pecah blok di batas solid</b>. Pilih <b>1 tingkat</b>, klik <b>Hitung jumlah blok</b> ([[sb_dialog]]).',
   'Klik <b>Pecah blok &rarr;</b>. <code>sb_frac</code> ikut dihitung otomatis ([[sb_frac_2d]]).',
   'Jalankan ulang <b>Model Estimation</b> (posisi blok berubah, hasil lama tidak cocok lagi).',
   'Di <b>Reporting BM</b> pilih <code>sb_frac</code> pada <b>Timbang volume &amp; tonase dengan proporsi</b>: blok perbatasan dilaporkan sebagian, bukan dibulatkan ({{B:Klasifikasi}}).')
 + figs(('sb_dialog', 'Dialog sub-blocking. ' + clean(g('sbPrev', ''))[:240]),
        ('sb_frac_2d', f"Sayatan 2D berwarna sb_frac sesudah dipecah 1 tingkat: {fz(SBH.get('n'))} blok, {fz(SBH.get('full'))} seluruhnya di dalam solid dan {fz(SBH.get('part'))} di perbatasan (proporsi 0&ndash;1)."))
 + (fig('u_frac', 'Jejak satu lensa pada sayatan dengan grid blok 5 m (dihitung dari data latihan): dari %s sel yang bersinggungan dengan solid, <b>%s hanya sebagian</b> di dalamnya &mdash; angka di tiap sel adalah <code>sb_frac</code>.' % (NU.get('fr_part', 0) + NU.get('fr_full', 0), NU.get('fr_part', '-'))) if hv('u_frac') else '')
 + '<h3>Mana yang sebenarnya menyelesaikan masalah volume</h3><p>Vein mendatar tebal 4 m, blok 5 m yang pusatnya tepat di luar vein (volume sebenarnya 400 m&sup3;):</p>'
 + '<table class="t"><tr><th>Tingkat pecah</th><th>Blok</th><th>Dihitung titik pusat</th><th>Ditimbang sb_frac</th></tr><tr><td>utuh</td><td>80</td><td><b>0 m&sup3; (&minus;100%)</b></td><td>400,0 m&sup3; (0,00%)</td></tr><tr><td>1</td><td>136</td><td>500 m&sup3; (+25%)</td><td>400,0 m&sup3;</td></tr><tr><td>2</td><td>360</td><td>500 m&sup3; (+25%)</td><td>400,0 m&sup3;</td></tr><tr><td>3</td><td>1.256</td><td>375 m&sup3; (&minus;6,3%)</td><td>400,0 m&sup3;</td></tr></table>'
 + why('Kolom titik pusat membaik tetapi <b>berayun</b>; pembulatan tidak hilang hanya dengan memperkecil blok. Untuk <b>volume &amp; tonase</b>, <code>sb_frac</code>-lah yang menyelesaikan masalah, bahkan tanpa memecah blok. Sub-blocking tetap berguna untuk resolusi <b>kadar</b> di dekat kontak dan geometri dig block.')
 + warn('Urutan yang disarankan: impor / kerangka AOI &rarr; sub-blocking &rarr; <code>sb_frac</code> &rarr; estimasi domain vein &rarr; estimasi waste. Kadar <b>tidak</b> dikalikan proporsi.'))

ch('Estimasi waste: kadar di luar wireframe ore', dta('lanjutan &mdash; sampel = interval yang <b>tidak di-flag domain apa pun</b>',
     [('Populasi Geostatistik', 'bilah <b>Domain</b> &rarr; <b>WASTE (di luar semua domain)</b>'),
      ('Hasil populasi waste', f"{(g('wsGs') or ['','?','?','?'])[1]} komposit, rata-rata Au {fN((g('wsGs') or [0,0,0,0])[2],3)} g/t, CV {fN((g('wsGs') or [0,0,0,0])[3],2)}"),
      ('Yang disimpan', 'tab <b>Uji estimasi</b> &rarr; <b>Simpan ke WASTE</b>'),
      ('Pilihan saat menjalankan', 'Variogram <b>Otomatis</b>, centang <b>hanya di bawah topografi</b>'),
      ('Hasil yang seharusnya', clean(g('wsHasil', ''))[:160])]) +  '<p>Model Estimation adalah <i>hard boundary</i> per domain: blok di luar solid tidak disentuh. Padahal kadar di sekitar wireframe-lah yang menentukan <b>dilusi</b>, <b>ore loss</b>, dan tonase total di dalam pit. Bagian <b>&#9317; Estimasi waste</b> di Model Estimation mengisinya sebagai domain semu <b>WASTE</b>.</p>'
 + (fig('u_waste', 'Dari %s sampel data latihan di <b>luar</b> solid vein: kadar Au terhadap jarak ke vein terdekat (kiri) dan logam per pita jarak (kanan). Median Au %s g/t pada &lt; 1,5 m, %s g/t pada 1,5&ndash;5 m, %s g/t pada 5&ndash;12 m; <b>%s%%</b> logam Au sampel berada di luar solid.' % (fN(NU.get('w_n', 0)), str(NU.get('w_med15', '-')).replace('.', ','), str(NU.get('w_med5', '-')).replace('.', ','), str(NU.get('w_med12', '-')).replace('.', ','), str(NU.get('w_share', '-')).replace('.', ','))) if hv('u_waste') else '')
 + kv([('Blok','blok yang pusatnya di luar <b>semua</b> solid domain (opsional: hanya di bawah topografi / di dalam pit). Blok harus sudah ada &mdash; lengkapi dulu dengan kerangka AOI.'),
       ('Sampel','komposit dari interval yang <b>tidak di-flag domain apa pun</b> (hard boundary waste), top-cut tersendiri'),
       ('Variogram','variogram WASTE sendiri bila sudah difit; kalau belum, variogram <b>domain terdekat</b>, dan <b>IDW</b> bila jauh dari semua domain'),
       ('Penanda hasil','<code>domain_est = WASTE</code>, <code>est_type = 3</code>; blok IDW <code>est_pass = 9</code> dengan SoR / KE / KV = &minus;99')])
 + '<h3>Memfit variogram waste sendiri</h3>' + steps('Panel <b>Geostatistik</b>, bilah <b>Domain</b> &rarr; <b>WASTE (di luar semua domain)</b>. Komposit = interval tanpa flag domain, populasi yang sama dengan sampel estimasi waste ([[ws_geostat]]).',
   'Statistik, variogram, fan, fitting model, KNA seperti biasa.',
   'Tab <b>Uji estimasi</b> &rarr; <b>&#8681; Simpan ke WASTE</b> ([[ws_simpan]]).')
 + figs(('ws_geostat', 'Geostatistik populasi WASTE: ' + ' · '.join(str(x) for x in (g('wsGs') or [])[:1]) + (f" — {g('wsGs')[1]} komposit, rata-rata Au {fN(g('wsGs')[2],3)} g/t, CV {fN(g('wsGs')[3],2)}" if g('wsGs') else '') + '.'),
        ('ws_simpan', 'Simpan ke WASTE: model variogram, elipsoid, pass, diskretisasi, top-cut dan panjang komposit tersimpan ke parameter waste.'))
 + '<h3>Menjalankan estimasi waste</h3>' + steps('Menu <b>Model Estimation</b> &rarr; <b>&#9317; Estimasi waste</b>. Variogram: <b>Otomatis</b> (memakai variogram WASTE bila ada). Centang <b>hanya di bawah topografi</b>.',
   'Klik <b>Periksa dulu</b>: jumlah blok waste, komposit waste, dan perkiraan pembagian kriging vs IDW ([[ws_panel]]).',
   'Klik <b>Jalankan estimasi waste</b> ([[ws_hasil]], [[ws_2d]]).')
 + figs(('ws_panel', 'Bagian &#9317; Estimasi waste sesudah Periksa dulu.'),
        ('ws_hasil', clean(g('wsHasil', 'Hasil estimasi waste.'))[:300]),
        ('ws_2d', 'Sayatan 2D kadar akhir: blok ore di dalam solid (domain vein) dan halo waste di sekitarnya (domain WASTE) dalam satu block model.'))
 + why('Variogram sebuah domain hanya berlaku di sekitar domain itu. Kriging pada blok yang jauh tetap menghasilkan angka &mdash; lengkap dengan SoR dan KE yang <b>menyesatkan</b>. IDW tidak berpura-pura, karena itu ukuran keyakinannya diisi &minus;99.')
 + tip('Blok waste <b>tidak diberi kelas keyakinan</b> (kelas tersendiri <i>Waste (di luar solid)</i>) dan tidak ikut kurva grade-tonase per kelas, tetapi volume &amp; tonasenya tetap dilaporkan bersama ore di Reporting BM.'))

KL = g('kls') or []
def kls(nm):
    for r in KL:
        if r[0] == nm: return r[1]
    return None
SPS = g('spasi') or {}
ch('Klasifikasi keyakinan & kerapatan bor', dta('lanjutan &mdash; atribut hasil Model Estimation dan estimasi waste',
     [('Ukuran keyakinan', '<b>SoR</b> dengan ambang bawaan (Measured SoR &ge; 0,75; Indicated &ge; 0,45)'),
      ('Timbang proporsi', 'pilih <code>sb_frac</code> pada <b>Timbang volume &amp; tonase dengan proporsi</b>'),
      ('Yang diklik', '<b>Hitung klasifikasi</b>, lalu <b>Hitung reporting</b>'),
      ('Hasil yang seharusnya', ', '.join('%s %s blok' % (r[0], fN(r[1])) for r in KL if r[1])),
      ('Kerapatan bor', f"warnai <code>est_spasi</code> dengan batas kelas <code>15,25,40,60</code> &mdash; median spasi data latihan {str(SPS.get('med','-')).replace('.',',')} m")]) +  '<p><b>Reporting BM</b> dapat mengusulkan kelas <b>Measured / Indicated / Inferred</b> per blok dari atribut hasil Model Estimation, lalu melaporkan tonase dan kadar per kelas.</p>'
 + '<table class="t"><tr><th>Atribut</th><th>Arti</th></tr><tr><td><code>est_pass</code></td><td>pass pencarian (1 = radius penuh)</td></tr><tr><td><code>est_nsamp</code></td><td>jumlah komposit yang dipakai</td></tr><tr><td><code>est_sor</code> / <code>est_ke</code></td><td>slope of regression / kriging efficiency</td></tr><tr><td><code>est_nhole</code></td><td>jumlah <b>lubang bor berbeda</b> yang komposit-nya dipakai</td></tr><tr><td><code>est_spasi</code></td><td>perkiraan <b>spasi bor setempat</b> (m)</td></tr><tr><td><code>est_dmin</code></td><td>jarak ke komposit terdekat yang dipakai</td></tr></table>'
 + (fig('u_klas', 'Alur penentuan kelas: blok diuji berurutan dari syarat terketat; yang tidak memenuhi turun ke kelas berikutnya.') if hv('u_klas') else '')
 + '<table class="t"><tr><th>Kelas</th><th>Syarat bawaan (dapat diubah di panel)</th></tr><tr><td><b>Measured</b></td><td>pass &le; 1, komposit &ge; 12, SoR &ge; 0,75, lubang bor berbeda &ge; 3, spasi bor &le; 25 m</td></tr><tr><td><b>Indicated</b></td><td>pass &le; 2, komposit &ge; 7, SoR &ge; 0,45, lubang bor berbeda &ge; 2, spasi bor &le; 50 m</td></tr><tr><td><b>Inferred</b></td><td>blok terestimasi lainnya</td></tr></table>'
 + steps('Jalankan <b>Model Estimation</b> (dan estimasi waste bila perlu).',
   'Buka <b>Reporting BM</b> &rarr; <b>&#9312; Atribut</b>; kotak <b>Klasifikasi keyakinan</b> ada di bawahnya ([[kls_panel]]). Pilih ukuran (SoR / KE) dan ambangnya.',
   'Klik <b>&#9654; Hitung klasifikasi</b> &rarr; atribut kategori <code>klasifikasi</code> ([[kls_hasil_panel]]).',
   'Pilih <code>sb_frac</code> pada <b>Timbang volume &amp; tonase dengan proporsi</b>, lalu <b>&#9654; Hitung reporting</b>: tabel per kelas dan <b>kurva grade &times; tonase bertumpuk per kelas</b> ([[kls_gt]]).')
 + figs(('kls_panel', 'Kotak Klasifikasi keyakinan di Reporting BM &#9312;.'),
        ('kls_hasil_panel', 'Hasil klasifikasi: ' + ', '.join('%s %s blok' % (r[0], fN(r[1])) for r in KL if r[1]) + '.'),
        ('kls_gt', 'Grade &times; tonase bertumpuk per kelas keyakinan (volume &amp; tonase ditimbang sb_frac).'),
        ('kls_3d', 'Atribut klasifikasi di 3D.'))
 + '<h3>Kerapatan bor per blok</h3><p>Jumlah komposit saja bukan ukuran kerapatan: dua puluh komposit dari <b>satu</b> lubang tidak sama dengan dua puluh komposit dari enam lubang. Karena itu syarat Measured / Indicated memakai <code>est_nhole</code> dan <code>est_spasi</code>.</p>'
 + figs(('kerapatan_3d', f"Block model berwarna est_spasi (batas kelas 15 / 25 / 40 / 60 m): median spasi bor setempat {fz(SPS.get('med'),1)} m (p10 {fz(SPS.get('p10'),1)} m, p90 {fz(SPS.get('p90'),1)} m), median {fz(SPS.get('nholeMed'))} lubang bor per blok. Bagian dalam endapan yang hanya terbor tiap sayatan ke-3 tampak jelas lebih renggang."),)
 + warn('Ambang ini usulan geostatistik, <b>bukan</b> keputusan klasifikasi. Penetapan Measured / Indicated / Inferred tetap wewenang <b>Competent Person</b> sesuai KCMI / JORC.'))

ch('Laporan per desain pit & progres topo-ke-topo', dta('<code>data/SIM_pit_fase1.dxf</code>, <code>SIM_pit_fase2.dxf</code>, <code>SIM_topo_akhir_juni.dxf</code>, <code>SIM_topo_akhir_juli.dxf</code> &mdash; DXF 3DFACE, diimport ke <b>Data Spasial</b> sebagai versi desain pit / topografi (disimpan sebagai DTM segitiga; tombol <b>Muat data latihan</b> sudah memuatnya). Block model: <code>SIM_BM_GC_kadar.csv</code> (sudah berisi kadar), supaya angkanya bisa dicocokkan tanpa menjalankan estimasi dulu',
     [('Block model', '<code>SIM_BM_GC_kadar.csv</code> &mdash; dengan <code>SIM_BM_GC.csv</code> yang masih kosong, blok tanpa kadar tidak masuk laporan; jalankan Model Estimation dulu'),
      ('Atribut &amp; cut-off', 'diatur seperti biasa di tab &#9312; (latihan: <code>AU_GC</code>, cut-off <b>0</b>, pengelompokan per RL 5 m)'),
      ('Mode 1 &mdash; per pit', 'topografi <code>SIM_topo_akhir_juni</code>; centang <b>SIM_pit_fase1</b> lalu <b>SIM_pit_fase2</b>'),
      ('Mode 2 &mdash; progres', 'atas <code>SIM_topo_akhir_juni</code>, bawah <code>SIM_topo_akhir_juli</code>'),
      ('Hasil yang seharusnya', 'fase 1 <b>3.384 blok</b> / 549.900 t &middot; fase 2 <b>16.103 blok</b> / 2.616.738 t &middot; progres sebulan <b>2.439 blok</b> / 396.338 t (SG 2,6, tanpa batas domain)')])
 + '<p>Reporting BM biasa memakai <b>satu</b> permukaan topografi dan <b>satu</b> desain pit: yang sedang aktif. Dua pekerjaan rutin karena itu jadi berulang &mdash; membandingkan fase pit, dan menghitung material yang benar-benar tergali bulan ini. Tab <b>&#9315; Pit &amp; progres</b> (node <b>Per desain pit &amp; progres topo-ke-topo</b> di bawah Reporting BM) mengerjakan keduanya tanpa mengganti versi aktif.</p>'
 + warn('Tab ini <b>tidak</b> punya pengaturan sendiri untuk atribut, cut-off, domain, poligon, RL, SG atau <code>sb_frac</code>. Semuanya diambil dari tab &#9312; dan &#9313;, dan hanya <b>permukaan atas &amp; bawah</b> yang diganti &mdash; supaya angkanya pasti sebanding dengan laporan biasa.', 'Yang diganti hanya permukaan')
 + '<h3>1. Beberapa desain pit sekaligus, topografi sama</h3>'
 + steps('Import kedua desain pit: baris <b>+ Tambah versi desain pit&hellip;</b> di <b>Data Spasial &rarr; Desain pit</b> &rarr; <code>SIM_pit_fase1.dxf</code>, lalu ulangi untuk <code>SIM_pit_fase2.dxf</code>. Versi lama tetap tersimpan. (Wireframe geologi tidak diimport di sini, melainkan di node Import Wireframe Geologi.)',
   'Reporting BM &rarr; tab <b>&#9312;</b>: pilih atribut dan cut-off seperti biasa. Lalu tab <b>&#9315; Pit &amp; progres</b>, mode <b>Per desain pit</b>.',
   'Pilih <b>topografi</b> &mdash; satu untuk semua pit, supaya perbedaan angka benar-benar berasal dari desain pitnya.',
   'Centang desain pit <b>dari yang terkecil ke terbesar</b>, lalu <b>Hitung per pit</b>.')
 + '<p>Hasilnya satu baris per pit: blok, volume, tonase, kadar tiap atribut dan logamnya. Di bawah tiap baris (mulai baris kedua) ada baris <b>tambahan</b>: selisih terhadap pit di atasnya.</p>'
 + kv([('Tonase &amp; logam tambahan', 'dikurangkan langsung (fase 2 &minus; fase 1)'),
       ('Kadar tambahan', 'logam tambahan &divide; tonase tambahan &mdash; bukan rata-rata dua kadar'),
       ('Syaratnya', 'pit <b>bersarang</b> (fase berikutnya memuat fase sebelumnya). Untuk pit yang saling terpisah, baca baris per pit saja dan abaikan baris tambahan')])
 + why('Angka yang dicari short term planner adalah <i>berapa tambahan ore bila pit diperdalam ke fase berikutnya</i>. Menghitungnya dari dua laporan terpisah berarti dua kali ganti versi aktif, dua kali catat, dan satu kesempatan salah catat.')
 + '<h3>2. Progres topo-ke-topo (ore reconcile)</h3>'
 + '<p>Material yang tergali antara dua survei adalah blok yang berada <b>di bawah topografi lama</b> dan <b>di atas topografi baru</b>. Dengan begitu seluruh atribut block model bisa dilaporkan untuk periode itu: tonase, kadar tiap unsur, logam, dan rinciannya per RL.</p>'
 + steps('Import kedua survei sebagai versi topografi: baris <b>+ Tambah versi topografi&hellip;</b> di <b>Data Spasial &rarr; Topografi</b> &rarr; <code>SIM_topo_akhir_juni.dxf</code> dan <code>SIM_topo_akhir_juli.dxf</code>. Versi aktif tetap <code>SIM_topo_xyz</code> bila Anda mengaktifkannya kembali.',
   'Tab <b>&#9315; Pit &amp; progres</b> &rarr; mode <b>Progres topo-ke-topo</b>.',
   'Isi <b>topografi atas</b> = survei yang lebih <b>awal</b> (akhir Juni), <b>topografi bawah</b> = survei yang lebih <b>baru</b> (akhir Juli).',
   'Biarkan <b>Laporkan semua atribut kadar</b> menyala bila ingin seluruh unsur ikut, bukan hanya yang dicentang di tab &#9312;.',
   'Klik <b>Hitung progres</b>, lalu <b>Export CSV</b> untuk laporan bulanan.')
 + kv([('Yang dilaporkan', 'blok, volume, tonase, kadar &amp; logam tiap atribut, dan rincian per RL / kategori sesuai pengelompokan di tab &#9312;'),
       ('Permukaan DTM', 'bila berupa DTM segitiga (.dtm / .dxf), blok di <b>luar jangkauan</b> DTM tidak dihitung dan dilaporkan sebagai <i>di luar DTM</i> &mdash; sama seperti Surpac'),
       ('Permukaan titik XYZ', 'diinterpolasi IDW seperti Reporting biasa'),
       ('Arah yang benar', 'bila atas dan bawah tertukar, hasilnya 0 blok &mdash; itu tandanya, bukan galat')])
 + warn('Hasil ini adalah <b>block model di antara dua permukaan</b>, bukan timbangan. Rekonsiliasi sebenarnya tetap membandingkannya dengan tonase ROM / pabrik: survei punya ketidakpastiannya sendiri, dan blok dihitung utuh menurut titik pusatnya (pakai <code>sb_frac</code> bila block model sudah dipecah di batas solid).')
 + tip('Untuk laporan bulanan rutin: simpan tiap survei sebagai <b>versi</b> di Data Spasial dengan catatan tanggalnya (mis. &ldquo;survei drone 30 Juni&rdquo;), supaya pasangan topografi tiap bulan tinggal dipilih dan tidak tertukar.'))

ch('Vein bercabang: domain induk', dta('<b>proyek terpisah</b>: <code>data/SIM_split_collar / survey / assay / geologi.csv</code> + block model <code>SIM_split_BM_GC.csv</code>, topografi <code>SIM_topo_xyz.csv</code>',
     [('Folder proyek', 'folder kosong baru, mis. <code>Proyek_Tutorial_Split</code>'),
      ('Nama dataset', '<code>VeinSplit_Simulasi</code>'),
      ('Domain', '<code>QVS_Utama</code> dan <code>QVS_Cabang</code>'),
      ('Usulan otomatis', 'Au, cut-off <b>0,5</b>, panjang min <b>1 m</b>, dilusi <b>1 m</b>, semua hole'),
      ('Koreksi', 'intercept <b>terjauh</b> pada hole yang punya dua intercept &rarr; <code>QVS_Cabang</code>'),
      ('Yang menjadikannya cabang', 'menu domain <code>QVS_Cabang</code> &rarr; <b>Domain induk</b> = <code>QVS_Utama</code>')]) +  '<p>Vein yang <b>bercabang</b> (split / splay) tidak bisa digambarkan dengan satu permukaan HW dan satu FW. Di GC-Ex tiap cabang dibuat sebagai <b>domain sendiri</b> dengan string HW / FW sendiri, lalu dijadikan <b>cabang dari domain induk</b>. Solidnya digabung, dan Model Estimation memperlakukan induk + cabang sebagai <b>satu domain</b> &mdash; mirip seam split pada batubara.</p>'
 + '<p>Latihan ini memakai proyek terpisah dengan data <code>SIM_split_*</code>: vein <b>QVS_Utama</b> dan <b>QVS_Cabang</b> yang lepas dari sisi footwall pada &plusmn;66 m searah dip, makin menjauh ke atas. Bor dangkal menembus dua vein, bor dalam hanya satu (vein sudah menyatu).</p>'
 + steps('Buat proyek baru, import <code>SIM_split_collar/survey/assay/geologi.csv</code>, topografi dan <code>SIM_split_BM_GC.csv</code>.',
   'Geomodeller Vein: buat domain <b>QVS_Utama</b> dan <b>QVS_Cabang</b>. Usulan otomatis Au &ge; 0,5 untuk QVS_Utama (lingkup semua hole).',
   f"Di Sayatan 2D, flag run <b>bawah</b> pada lubang yang menembus dua vein ke <b>QVS_Cabang</b> ([[split_flag]]). Di data latihan ada {N['splitFlag']} lubang seperti itu.",
   'Di kartu domain QVS_Cabang pilih <b>&#8627; cabang dari QVS_Utama</b> ([[split_domain]]). Kartu QVS_Utama berubah menjadi <b>induk dari 1 cabang</b>, dan kartu cabang bergeser ke kanan.',
   '<b>&#10148;&#10148; Semua section</b> untuk masing-masing domain, lalu <b>&#9654;&#9654; Semua domain</b> di tab Solid.')
 + fig('split_flag', 'Section tengah: lubang dangkal menembus QVS_Utama (oranye) lalu QVS_Cabang (biru) di bawahnya; lubang dalam hanya satu vein.')
 + fig('split_domain', 'Kartu domain: QVS_Cabang dijadikan cabang dari QVS_Utama.', '78%')
 + '<h3>Sambung ke induk</h3><p>Data cabang berhenti di bor terakhir yang masih menembus dua vein, padahal cabang sebenarnya menyambung ke induk lebih jauh. Karena itu kontak induk pada lubang yang <b>tidak</b> menembus cabang (vein sudah menyatu), dalam <b>jarak sambung</b> (bawaan 30 m) dari data cabang, dipakai juga sebagai titik cabang. Ujung cabang di sisi itu dipotong tegas di dalam induk, bukan pinch-out. Opsi <b>Sambung ke induk</b> dan <b>Jarak sambung</b> ada di Parameter domain aktif bila domain aktif adalah cabang.</p>'
 + fig('split_2d', 'Sayatan 2D: solid QVS_Cabang lepas dari QVS_Utama di titik percabangan dan menjauh ke atas sampai topografi &mdash; bentuk Y.')
 + kv([('Solid QVS_Utama', f"{fN(SP['vU'])} m&sup3;, flag di dalam {SP['inU']}"),
       ('Solid QVS_Cabang', f"{fN(SP['vC'])} m&sup3;, flag di dalam {SP['inC']}, {SP['nj']} titik sambung ke induk"),
       ('Solid gabungan', f"<b>{fN(SP['vol'])} m&sup3;</b> (tumpang tindih di percabangan {fN(SP['ov'])} m&sup3; tidak dihitung dua kali)")])
 + fig('split_panel', 'Tab Solid: kotak <b>Solid gabungan per domain induk</b> menampilkan volume gabungan tanpa tumpang tindih.')
 + fig('split_3d', 'Tampilan 3D: solid induk (oranye) dan cabang (biru).')
 + '<h3>Geostatistik & Model Estimation</h3>' + steps('Di menu Geologi pilih atribut filter <b>Domain induk (Geomodeller Vein)</b> dan centang QVS_Utama: sampel induk + cabang ikut ' + f"({N['splitGs']} komposit). Atribut <b>Domain vein</b> tetap ada bila ingin melihat cabang terpisah.",
   'Jalankan Geostatistik seperti biasa, lalu <b>Simpan ke domain</b>. Hanya domain induk yang ditawarkan, karena cabang memakai parameter induknya.',
   'Menu Model Estimation menampilkan satu baris <b>QVS_Utama + 1 cabang</b> dengan solid gabungan ([[split_me]]). Run memakai sampel kedua vein dan mengestimasi blok di kedua solid; atribut <code>domain_est</code> berisi QVS_Utama.')
 + fig('split_me', f"Model Estimation untuk kelompok QVS_Utama: {SPM[0]['nIn']:,} blok di dalam solid gabungan, {SPM[0]['nAdd']} blok tambahan, {SPM[0]['nComp']} komposit.".replace(',', '.'), '78%')
 + tip('Export solid: centang <b>Export cabang digabung ke file domain induk</b> untuk satu file berisi solid induk + cabang (permukaan HW / FW tidak ikut). Tanpa centang, tiap domain diexport sendiri.')
 + warn('Cabang hanya satu tingkat: domain induk tidak bisa menjadi cabang domain lain. Untuk melepas, pilih <b>Domain mandiri</b> di kartu cabang.'))

SV = N['strVol'] if isinstance(N.get('strVol'), list) else json.loads(N['strVol'])
ch('Struktur geologi (dip / dip azimuth)', dta('<code>data/SIM_struktur.csv</code> &mdash; ' + f"{N['strN']} titik struktur (kolom <code>No, X, Y, Z, Dip, Dip_Azimuth, Keterangan</code>)",
     [('Import lewat', 'baris <b>+ Tambah struktur&hellip;</b> &rarr; <b>Import CSV struktur&hellip;</b> di node <b>Struktur Geologi</b> (langkah 5)'),
      ('Flag struktur di Sayatan 2D', '<b>Dip 65</b>, <b>Dip az 135</b>, keterangan <code>kontak HW</code> &mdash; lalu klik dua kali di penampang'),
      ('Radius pemakaian', '<b>25 m</b> (bawaan) dari data vein'),
      ('Hasil yang seharusnya', f"volume QV_Lensa2 {fN(SV[0])} m&sup3; &rarr; {fN(SV[1])} m&sup3; setelah {SV[2]} struktur dipakai")]) +  '<p>Arah dip vein bisa berubah: misalnya ke timur di elevasi 300 dan ke barat di elevasi 100. Titik struktur (dip / dip azimuth) memberi tahu RBF arah kemiringan setempat. Ada tiga sumber: <b>flag struktur</b> di Sayatan 2D per domain, <b>file CSV</b>, dan <b>titik manual</b> di 3D.</p>'
 + '<h3>Import file struktur</h3>' + steps('Node <b>Struktur Geologi</b> &rarr; <b>&#8679; Import CSV struktur</b>, pilih <code>SIM_struktur.csv</code> ([[struktur_panel]]).',
   'Format kolom: <code>No, X, Y, Z, Dip, Dip_Azimuth, Keterangan</code> (pemisah koma / titik koma / tab; header fleksibel; Z kosong = diambil dari topografi).',
   'Daftar sumber menampilkan file beserta jumlah titik. Centang untuk menampilkan / menyembunyikan, <b>&times;</b> untuk menghapus file.',
   'Klik baris titik untuk memilihnya; nilai X, Y, Z, Dip, Dip az, No dan Keterangan bisa diubah langsung.')
 + fig('struktur_panel', f"Panel Struktur geologi: {N['strN']} titik dari SIM_struktur.csv; titik pertama terpilih dan bisa diedit.", '78%')
 + fig('struktur_3d', 'Tampilan 3D: tiap struktur berupa cakram berorientasi (hijau = dari file) dengan garis strike (hitam) dan tanda arah dip: deretan di singkapan, dua di kedalaman (core oriented), dan kekar. Item Layer <b>Struktur geologi</b> menyalakan / menyembunyikannya.')
 + '<h3>Flag struktur di Sayatan 2D</h3>' + steps('Geomodeller Vein &rarr; bagian <b>&#9316; Flag struktur</b>. Isi <b>Dip</b> 65, <b>Dip az</b> 135 dan keterangan.',
   'Klik <b>&#9998; Flag struktur</b>, lalu klik di Sayatan 2D pada posisi pengukuran ([[struktur_flag]]). Titik ditaruh di bidang sayatan untuk <b>domain aktif</b>.',
   'Klik berikutnya <b>memakai nilai yang sama</b> sampai Anda mengubahnya; nomor bertambah otomatis. Garis pendek di penampang = dip semu (perpotongan bidang struktur dengan bidang sayatan). <b>Esc</b> = selesai.')
 + fig('struktur_flag', 'Flag struktur di Sayatan 2D: dua titik 65/135 untuk QV_Lensa2 (oranye) dan dua struktur dari file di dekat sayatan (hijau), masing-masing tampil sebagai garis dip semu berlabel dip/az.')
 + '<h3>Titik manual di 3D</h3>' + steps('Klik baris <b>+ Tambah struktur&hellip;</b> di node <b>Struktur Geologi</b> &rarr; <b>Titik (klik di 3D)</b>. Arahkan kursor ke bor, solid atau topografi sampai info muncul, lalu klik. Atau <b>+ Titik di tengah area</b>.',
   'Geser titik terpilih dengan tombol <b>Maju / Mundur, Kiri / Kanan</b> (relatif arah pandang 3D; di Sayatan 2D relatif bidang sayatan) dan <b>Z + / Z &minus;</b>, dengan langkah yang diatur ([[struktur_manual]]).')
 + fig('struktur_manual', 'Editor titik terpilih: koordinat, dip / dip az, keterangan, dan tombol geser.', '78%')
 + '<h3>Pengaruh pada solid RBF</h3>'
 + kv([('Struktur flag domain','selalu dipakai untuk domain itu'),('Struktur file / manual',f"dipakai bila dalam radius (bawaan 25 m) dari data vein; opsi global di node Struktur Geologi, opsi per domain di Parameter solid &rarr; Struktur"),
       ('Cara kerja','tiap struktur menjadi titik bantu kemiringan lunak di permukaan HW dan FW, sehingga permukaan mengikuti dip setempat; struktur yang hampir tegak lurus bidang vein diabaikan dan dilaporkan'),
       ('Data latihan',f"volume QV_Lensa2 {fN(SV[0])} m&sup3; &rarr; {fN(SV[1])} m&sup3; setelah {SV[2]} struktur file dipakai")])
 + warn('Struktur hanya mengarahkan kemiringan, bukan posisi. Struktur dari singkapan yang salah ukur bisa menarik permukaan; periksa daftar &ldquo;Struktur dipakai&rdquo; di ringkasan solid.'))

MF = N['mapF'] if isinstance(N.get('mapF'), list) else json.loads(N['mapF'])
L0 = NL['srf0']; L1 = NL['srf1']; LP = NL['lap0']; LC = NL['lap15']; TRF = NL['jejakF1']
def nf(v, d=0): return ('{:,.%df}' % d).format(v).replace(',', 'X').replace('.', ',').replace('X', '.')
ch('Sesar 3D: bidang, offset & urutan umur', dta('<code>data/SIM_LAT_sesar.csv</code> &mdash; jejak sesar F1 (dua titik X, Y), dipakai pada proyek laterit',
     [('Nama', '<code>F1</code>'),
      ('Jejak (koordinat manual)', f"<code>{TRF[0][0]},{TRF[0][1]};{TRF[1][0]},{TRF[1][1]}</code>"),
      ('Waktu / urutan umur', '<b>Post-mineralisasi</b>, urutan <b>1</b>'),
      ('Dip / dip direction', '<b>65&deg;</b> / <b>100&deg;</b>'),
      ('Jangkauan', 'atas jejak <b>20 m</b>, bawah <b>120 m</b>'),
      ('Gerak', '<b>Normal</b>, offset <b>12 m</b>'),
      ('Elevasi jejak', '<b>Tetap</b>, Z <b>190</b>')]) +  '<p>Menu <b>Sesar 3D</b> (rel kiri, sesudah Sayatan) mengubah garis sesar menjadi <b>bidang 3D</b> yang ikut dipakai pemodelan dan estimasi. Panjang bidang searah strike = panjang jejak yang Anda digitasi; jangkauan searah dip diatur dengan <b>Atas jejak</b> dan <b>Bawah</b>.</p>'
 + kv([('Bidang','jejak (garis struktur di Peta atau koordinat) + <b>dip</b> dan <b>dip direction</b>; elevasi jejak dari topografi aktif atau Z tetap'),
       ('Gerak','jenis normal / naik / mendatar dekstral / sinistral (otomatis) atau <b>oblik</b>: trend &amp; plunge garis gores; <b>offset</b> = net slip hanging wall (m)'),
       ('Waktu','<b>pre</b>-mineralisasi (referensi), <b>syn</b>-mineralisasi (mengontrol bentuk ore body), <b>post</b>-mineralisasi (memotong &amp; menggeser ore body)'),
       ('Urutan umur','angka 1 = tertua; centang <b>Memotong</b> untuk sesar yang lebih tua. Tombol <b>Urutkan umur otomatis</b> menyusun pre &lt; syn &lt; post lalu relasi memotong; urutan melingkar / tidak logis diberi peringatan')])
 + '<h3>Membuat sesar F1 (data laterit)</h3>' + steps('Buka proyek laterit (import <code>SIM_LAT_*</code>, lihat {{B:Geomodeller Stratified}}). Klik <b>Sesar 3D</b> di rel kiri ([[flt_kosong]]).',
   'Cara biasa: digitasi garis struktur jenis <i>Sesar normal</i> di menu <b>Map</b>, lalu di Sesar 3D pilih garisnya dan klik <b>+ Dari garis Peta</b>. Untuk latihan, klik <b>+ Koordinat manual</b> dan isi <code>%s,%s;%s,%s</code> (dari SIM_LAT_sesar.csv).' % (TRF[0][0], TRF[0][1], TRF[1][0], TRF[1][1]),
   'Di <b>Atribut sesar</b> isi: waktu <b>Post-mineralisasi</b>, urutan umur 1, dip <b>65</b>, dip direction <b>100</b>, atas 20 m, bawah 120 m, jenis <b>Normal</b>, offset <b>12</b> m, elevasi jejak <b>Tetap</b> Z <b>190</b> ([[flt_atribut]]).',
   'Bagian <b>Pengaruh ke pemodelan</b> merangkum sesar yang dipulihkan, batas keras dan sesar syn ([[flt_pengaruh]]).')
 + fig2('flt_kosong', 'Menu Sesar 3D sebelum ada sesar.', 'flt_atribut', 'Atribut sesar F1: post, dip 65/100, normal, offset 12 m.')
 + fig('flt_pengaruh', 'Ringkasan pengaruh: 1 sesar post dengan offset dipulihkan; tidak ada peringatan urutan umur.', '52%')
 + fig('flt_3d', 'Bidang F1 di 3D dengan permukaan lapisan yang terpotong dan tergeser (hanging wall timur turun).')
 + fig('flt_map', 'Jejak F1 di Map dengan tanda arah dip dan label waktu / offset.')
 + '<h3>Apa yang dilakukan GC-Ex dengan sesar</h3>'
 + kv([('Post + offset &gt; 0','kontak / sampel di hanging wall <b>dipulihkan</b> (digeser balik searah vektor gerak), mulai sesar <b>termuda</b>. Model vein / lapisan dan estimasi dikerjakan di ruang pulih, lalu hasilnya <b>digeser kembali</b>. Mesh terpotong rapi di bidang sesar.'),
       ('Batas keras','bawaan untuk post <b>tanpa</b> offset (offset belum diketahui); bisa dinyalakan untuk syn / post lain. Sampel tidak dipakai menyeberang bidang sesar (Model Estimation, estimasi lapisan, interpolasi ketebalan).'),
       ('Syn-mineralisasi','titik-semu orientasi di bidang sesar dalam <b>jarak pengaruh</b> data domain: solid RBF vein mengikuti bidang sesar (vein yang mengisi sesar). Di Geomodeller Stratified-Laterite, centang Batas keras untuk <i>growth fault</i> (ketebalan berbeda di kedua sisi).'),
       ('Pre-mineralisasi','hanya referensi tampilan; ikut tergeser oleh sesar post yang lebih muda'),
       ('Sesar memotong sesar','bidang sesar tua digeser oleh sesar muda (tampilan 3D / Sayatan) dan dipulihkan lebih dulu')])
 + why('Ore body yang terpotong sesar post bila diinterpolasi langsung akan &ldquo;dijembatani&rdquo; melintasi bidang sesar (lapisan melandai palsu, kadar tercampur). Dengan pemulihan, data dari kedua sisi bersambung lagi seperti sebelum tersesarkan.')
 + warn('Pemulihan memakai translasi kaku (tanpa rotasi / lipatan). Offset di ujung jejak bisa dikecilkan bertahap dengan <b>Taper ujung</b>. Simpan &amp; export: CSV sesar dan DXF bidang (3DFACE), tabel <code>sesar</code> di gcex_proyek.db.'))


if NU:
    ch('Latihan terpandu: menemukan kembali geometri endapan', '<p>Data latihan dibuat dari geometri yang sudah ditentukan (<code>make_sim_data.py</code>), jadi setiap latihan punya <b>jawaban yang diketahui</b>: Anda bisa memeriksa apakah cara kerja Anda benar-benar mengembalikan geometri itu. Kunci jawabannya ada di <code>JAWABAN_MODEL.txt</code>. Semua gambar di bab ini dihitung langsung dari berkas data latihan.</p>'
     + (fig('u_bidang', 'Bidang vein lensa 2 dibentangkan. Kiri: tebal vein. Kanan: GT model (tebal &times; kadar relatif). Keduanya memanjang searah sumbu ore shoot ber-pitch %.0f&deg;.' % NU['PITCH']) if hv('u_bidang') else '')
     + '<h3>2a &mdash; orientasi bidang vein</h3><p>Setelah flagging domain, pasang bidang terbaik pada seluruh intersep vein. Hasil yang seharusnya: <b>dip &asymp; %.0f&deg;, dip-azimuth &asymp; %.0f&deg;</b>. Bidang acuan model %.0f&deg;/%.0f&deg;, tetapi permukaan vein sigmoidal sehingga bidang rata-rata bagian yang terbor lebih landai &mdash; keduanya benar.</p>' % (NU['dip_ukur'], NU['daz_ukur'], NU['DIP'], NU['DIPAZ'])
     + '<h3>2b &mdash; pitch ore shoot</h3>' + steps('Hitung <b>GT = kadar &times; tebal</b> dijumlah <b>per bor</b> (node <b>Ore Geometry</b>, langkah 5b, melakukannya sendiri setelah tombol <b>Hitung intercept &amp; GT</b> ditekan).', 'Proyeksikan GT ke bidang vein, cari arah kemenerusan terbaik (kipas variogram).', '<b>Gabungkan keempat lensa</b>: kontrol strukturnya satu; satu lensa saja datanya terlalu sedikit untuk menembus efek nugget Au.')
     + (fig('u_gt', 'GT per bor di bidang vein. Kiri (lensa utuh): pemusatan GT memanjang searah sumbu ore shoot. Kanan (lensa yang dipotong sesar): polanya pecah karena blok yang turun menggeser vein %.0f m.' % NU['FA_OFF']) if hv('u_gt') else '')
     + (fig('og_kipas', 'Di aplikasi: Ore Geometry &rarr; &#9314; Ore shoot menggambar kipas variogram GT dan tebal intersep dari data proyek. ' + clean(N.get('ogFan', '')).split(' Bila GT')[0]) if ('og_kipas' in FIG) else '')
 + (fig('u_kipas', 'Kipas variogram: lembah terdalam = arah paling menerus. GT di %s&deg;, tebal intersep di %s&deg;, berbanding pitch model %.0f&deg;.' % (NU.get('fan_gt', '-'), NU.get('fan_tb', '-'), NU['PITCH'])) if hv('u_kipas') else '')
     + '<p>Pakai hasil itu untuk <b>elipsoid pencarian</b> estimasi: major searah pitch &asymp; %.0f&deg; di bidang vein, semi searah strike, minor tegak lurus bidang vein; nisbah &plusmn;3 : 2 : 1 ({{B:Variogram}}).</p>' % NU['PITCH']
     + '<h3>2c &mdash; pemulihan sesar lebih dulu</h3><p>Di <b>Sesar 3D</b> masukkan bidang dari <code>SIM_sesar.csv</code> (strike 110&deg;, dip 65&deg;, offset %.0f m, post-mineralisasi) dan jalankan pemulihan sebelum pemodelan ({{B:Sesar 3D}}). Tanpa pemulihan, domain lensa 2 &amp; 3 pecah dan arah ore shoot-nya kacau; lensa 1 &amp; 4 tidak terpengaruh.</p>' % NU['FA_OFF']
     + '<h3>2d &mdash; zonasi vertikal</h3>'
     + (fig('u_zonasi', 'Zonasi vertikal terhadap paleo-muka air tanah RL %.0f m: Au memuncak di sekitar RL %s m bersama tekstur colloform; Ag/Au naik dari &asymp;%s di bawah menjadi &asymp;%s di atas; Pb+Zn naik ke bawah.' % (NU['WT_RL'], NU.get('zon_puncak', '-'), str(NU.get('zon_agau_bawah', '-')).replace('.', ','), str(NU.get('zon_agau_atas', '-')).replace('.', ','))) if hv('u_zonasi') else '')
     + warn('<b>Jangan menginterpolasi menembus batas zona.</b> Zona didih, zona base-metal dan tudung tercuci adalah populasi kadar yang berbeda; dicampur dalam satu domain, variogram dan estimasinya ikut salah.')
     + '<h3>2e &mdash; top-cut</h3>'
     + ('<p>Di aplikasi: Geostatistik &rarr; tab <b>Profil</b> membuat grafik zonasi seperti ini dari data proyek ([[geostat_profil]]), dan tab <b>Statistik</b> memuat kurva pemusatan logam ([[geostat_logam]]).</p>' if ('geostat_profil' in FIG) and ('geostat_logam' in FIG) else '')
 + (fig('u_topcut', 'Sebaran Au di dalam vein: rata-rata %s g/t, median %s g/t, CV %s, maksimum %s g/t. 1%% sampel teratas memuat %s%% logam &mdash; itulah alasan top-cut.' % tuple(str(NU.get(k, '-')).replace('.', ',') for k in ('au_mean', 'au_med', 'au_cv', 'au_max', 'tc_1'))) if hv('u_topcut') else '')
     + tip('Top-cut ditentukan <b>per unsur</b>: Ag tidak perlu top-cut seagresif Au karena efek nugget-nya jauh lebih kecil.'))

ch('Geomodeller Stratified-Laterite: laterit nikel', dta('<b>proyek terpisah</b>: <code>data/SIM_LAT_collar / survey / assay / geologi.csv</code> + topografi <code>SIM_LAT_topo_xyz.csv</code> + block model <code>SIM_LAT_BM_GC.csv</code> &mdash; ' + f"{NL['nHole']} bor vertikal grid 25 m, {fN(NL['nAssay'])} sampel 1 m, unsur Ni, Co, Fe, MgO, SiO2".replace(',', '.'),
     [('Nama dataset', '<code>Laterit_Simulasi</code>'),
      ('Kolom geologi', '<code>Zona</code> (kode <b>TS, LIM, SAP, BRK</b>)'),
      ('Preset lapisan', '<b>Laterit nikel</b> &rarr; Limonit, Saprolit, Bedrock'),
      ('Unsur estimasi', '<b>Ni, Co, Fe, MgO, SiO2</b>; rasio <b>SiO2 / MgO</b>'),
      ('Cut-off laporan', '<b>0</b> lalu ulangi dengan <b>1,5</b> % Ni untuk melihat bedanya')]) +  '<p>Endapan <b>laterit</b> (nikel, bauksit) dan <b>stratiform</b> (sedex) berlapis mengikuti permukaan: lapisan tipis secara vertikal tetapi luas ke samping. Menu <b>Geomodeller Stratified-Laterite</b> (rel kiri, di bawah Geomodeller Vein) memodelkan lapisan dari log geologi, lalu mengestimasi per lapisan di koordinat <b>unfold</b>. Menu vein yang lama sekarang bernama <b>Geomodeller Vein</b> (Geomodeller Vein System Deposit).</p>'
 + '<h3>Import data laterit</h3>' + steps('Buat folder proyek baru, import <code>SIM_LAT_collar / survey / assay / geologi.csv</code>, topografi <code>SIM_LAT_topo_xyz.csv</code> dan block model <code>SIM_LAT_BM_GC.csv</code> seperti {{B:Membuat folder}}.',
   'Di menu Geologi pilih atribut <b>Zona</b> untuk melihat profil TS / LIM / SAP / BRK ([[lat_geologi]]).')
 + fig('lat_geologi', f"Data laterit: {NL['nHole']} bor vertikal, pita geologi Zona.")
 + '<h3>&#9312; Lapisan</h3>' + steps('Klik <b>Geomodeller Strata-Laterit</b> di rel kiri. Pilih <b>Kolom geologi</b> = Zona.',
   'Pilih <b>Preset</b> = <i>Laterit nikel</i>: lapisan Limonit, Saprolit, Bedrock dibuat dan kode log dicocokkan otomatis ([[sl_lapisan]]). Periksa / ubah kode lewat daftar centang tiap lapisan ([[sl_kode]]).',
   'Isi <b>densitas basah</b> (t/m&sup3;) dan <b>kadar air</b> (%) per lapisan. Lapisan terakhir = <b>dasar</b> (bedrock): hanya atapnya yang dimodelkan.')
 + fig2('sl_lapisan', 'Preset laterit nikel: urutan lapisan, densitas, kadar air.', 'sl_kode', 'Kode log per lapisan (centang).')
 + '<h3>&#9313; Permukaan lapisan</h3>' + steps('Bagian <b>Permukaan</b> dibangun otomatis: atap lapisan pertama dari <b>topografi &minus; kedalaman kontak</b> (atau elevasi kontak bor), lalu <b>ketebalan (isopach)</b> tiap lapisan ditumpuk ke bawah sehingga permukaan tidak pernah bersilangan ([[sl_permukaan]]).',
   'Atur <b>sel grid</b> (5 m), <b>ekstrapolasi maksimum</b> dari bor terdekat (30 m), pangkat IDW dan jumlah tetangga. Hole yang berhenti di dalam lapisan tidak dipakai untuk ketebalan (tebal minimum).',
   'Tampilan 3D: permukaan atap tiap lapisan dan titik kontak bor ([[sl_permukaan_3d]]). Export: <b>Grid CSV</b> (atap &amp; tebal) dan <b>DXF permukaan</b>.')
 + fig('sl_permukaan', f"Ringkasan permukaan: {L0['nh']} hole, grid {L0['nx']} &times; {L0['ny']} @ {L0['cell']} m; tebal rata-rata limonit {nf(L0['st'][0][2],2)} m, saprolit {nf(L0['st'][1][2],2)} m.", '52%')
 + fig('sl_permukaan_3d', 'Permukaan atap Limonit, Saprolit dan Bedrock di 3D.')
 + '<h3>Sesar memotong lapisan</h3>' + steps('Pada Sayatan 2D arah 100&deg; lewat E 412.150 N 9.620.150, tanpa sesar permukaan &ldquo;melandai&rdquo; melewati zona sesar ([[sl_sayatan_tanpa_sesar]]).',
   'Setelah F1 dibuat ({{B:Sesar 3D}}), permukaan dibangun ulang otomatis: kontak dipulihkan, digrid, lalu digeser kembali, sehingga lapisan <b>terpotong tegas</b> di bidang sesar ([[sl_sayatan_sesar]], [[sl_permukaan_sesar]]).')
 + fig('sl_sayatan_tanpa_sesar', 'Tanpa sesar: permukaan menjembatani zona sesar.')
 + fig('sl_sayatan_sesar', 'Dengan F1 (post, offset 12 m): hanging wall timur turun &plusmn;11 m; lapisan terpotong di bidang sesar.')
 + fig('sl_permukaan_sesar', f"Ringkasan setelah F1: 1 sesar post dipulihkan; {L1['st'][1][1]} hole saprolit ditandai &ldquo;berhenti / terpotong sesar&rdquo; (atap dan lantai di blok sesar berbeda: kontaknya dipakai, ketebalannya tidak).", '52%')
 + '<h3>&#9314; Estimasi per lapisan</h3>' + steps('Pilih <b>unsur</b> (Ni, Co, Fe, MgO, SiO2), panjang <b>komposit</b> 1 m, dan <b>rasio</b> SiO2 / MgO ([[sl_estimasi]]).',
   'Per lapisan: <b>Mode</b> Blok 3D (OK atau IDW) atau <b>Akumulasi 2D</b>; <b>Unfold</b> proporsional atau dari atap; azimuth &amp; range mayor / minor / vertikal (vertikal di ruang unfold, mis. 3 m); nugget; jumlah sampel.',
   'Isi parameter dari <b>Geostatistik per lapisan</b> (di bawah) dengan <b>Simpan ke lapisan</b>, atau ketik manual (mengetik manual menonaktifkan model variogram tersimpan).',
   'Klik <b>&#9654; Jalankan estimasi lapisan</b>. Hasil masuk ke block model GC sebagai atribut <code>sl_lapisan</code>, <code>sl_ni</code>, <code>sl_co</code>, &hellip;, <code>sl_pass</code>, <code>sl_ns</code>, <code>sl_rasio</code> ([[sl_estimasi_hasil]], [[sl_bm_2d]], [[sl_bm_lapisan_3d]]).')
 + fig2('sl_estimasi', 'Parameter estimasi per lapisan.', 'sl_estimasi_hasil', 'Hasil run: ' + clean(NL['slMsg']).replace('&#10003; ', ''))
 + fig('sl_bm_2d', 'Block model GC berwarna sl_ni di Sayatan 2D: blok hanging wall ikut turun di timur sesar F1.')
 + fig('sl_bm_lapisan_3d', 'Atribut sl_lapisan di 3D.')
 + '<h3>Geostatistik per lapisan (ruang unfold)</h3>' + steps('Buka panel <b>Geostatistik</b> (tombol kanan atas), unsur <b>Ni</b>. Di bilah atas panel pilih <b>Lapisan</b> = <i>Saprolit (unfold)</i>. Komposit diambil per lapisan: koordinat X, Y (dipulihkan bila ada sesar post) dan Z = posisi unfold; lapisan akumulasi 2D memakai nilai tebal &times; kadar.',
     'Tab <b>Variogram / Anisotropi</b>: arah di bidang datar (0&deg; = timur). Variogram <b>downhole</b> = arah vertikal di ruang unfold ([[gs_lapisan]]).',
     'Tab <b>Model</b> &rarr; fitting otomatis ([[gs_lapisan_model]]); tab <b>KNA</b> untuk jumlah sampel / radius. Uji estimasi grid tidak dipakai untuk sumber lapisan.',
     'Tab <b>Uji estimasi</b> &rarr; <b>Simpan ke lapisan Saprolit</b> ([[gs_simpan_lapisan]]): model variogram, pass, diskretisasi dan top-cut tersimpan; azimuth, range mayor / minor / <b>vertikal (dari variogram downhole)</b> dan nugget di tabel &#9314; terisi, bertanda <i>variogram: Geostatistik</i> ([[sl_estimasi_vario]]).')
 + fig('gs_lapisan', f"Geostatistik sumber Lapisan Saprolit (unfold): {NL['gsLap'][1]} komposit, rata-rata Ni {nf(NL['gsLap'][2],3)}%, CV {nf(NL['gsLap'][3],2)}.")
 + fig('gs_lapisan_model', 'Model variogram lapisan Saprolit (fitting otomatis).')
 + fig2('gs_simpan_lapisan', clean(NL['gsSimpan']).split('. Lanjut')[0] + '.', 'sl_estimasi_vario', 'Tabel estimasi: Saprolit memakai model dari Geostatistik.')
 + '<h3>&#9316; Validasi lapisan</h3>' + steps('Bagian <b>Validasi</b>: pilih lapisan, unsur dan arah <b>swath</b> (Easting, Northing atau <b>Z unfold</b>) dengan lebar bin.',
     'Bandingkan rata-rata <b>komposit</b> (oranye) dan <b>blok</b> (biru) per bin, serta selisih global. Tabel <b>grade-tonase</b> (DMT &amp; kadar per cut-off) di bawahnya ([[sl_validasi]], [[sl_validasi_e]]).')
 + fig2('sl_validasi', f"Swath Z unfold Saprolit (bin 1 m): komposit {nf(NL['valZ']['cm'],3)}% vs blok {nf(NL['valZ']['em'],3)}%; profil vertikal Ni terbawa ke blok.", 'sl_validasi_e', 'Swath Easting (bin 25 m) dan grade-tonase DMT per cut-off.')
 + why('Pada laterit, kadar Ni berubah tajam secara vertikal (puncak di saprolit atas) tetapi pelan secara lateral. Variogram di ruang unfold menangkap kontras ini: range vertikal beberapa meter, lateral ratusan meter. Tanpa unfold, profil vertikal tercampur variasi elevasi topografi.')
 + why('<b>Unfold proporsional</b>: setiap sampel / blok diberi posisi relatif antara atap dan lantai lapisannya (0 = atap, 1 = lantai), jadi sampel di puncak bukit dan di lembah yang sama-sama &ldquo;bagian atas saprolit&rdquo; dianggap berdekatan. Tanpa unfold, pencarian sampel memakai elevasi absolut dan bisa mengambil sampel dari lapisan lain di topografi yang miring.')
 + '<h3>&#9315; Laporan</h3>' + steps('Bagian <b>Laporan</b>: volume, <b>WMT</b> (volume &times; densitas basah), <b>DMT</b> (WMT &times; (1 &minus; kadar air)), kadar rata-rata (ditimbang DMT) dan rasio ([[sl_laporan]]).',
   'Isi <b>cut-off</b> Ni &ge; 1,5 untuk tonase bijih ([[sl_laporan_cut]]). <b>&#8681; Laporan CSV</b> (menu node: <b>Export laporan WMT / DMT (CSV)</b>) untuk Excel.')
 + fig2('sl_laporan', f"Tanpa cut-off: Limonit {nf(LP[0][4])} DMT @ Ni {nf(LP[0][5][0],3)}%; Saprolit {nf(LP[1][4])} DMT @ Ni {nf(LP[1][5][0],3)}%.", 'sl_laporan_cut', f"Cut-off Ni &ge; 1,5: Limonit {nf(LC[0][2])} DMT @ {nf(LC[0][3][0],3)}%; Saprolit {nf(LC[1][2])} DMT @ {nf(LC[1][3][0],3)}%.")
 + ('<h3>&#9316;b Estimasi waste laterit</h3><p>Blok yang <b>tidak jatuh di lapisan mana pun</b> (mis. tanah penutup di atas kontak teratas, bedrock di bawah permukaan terbawah bila bedrock bukan lapisan dasar) tidak pernah diestimasi oleh &#9314;. Bagian <b>&#9316;b</b> mengisinya dengan IDW anisotropis di <b>ruang unfold</b>: zona <i>atas</i> memakai tinggi di atas kontak teratas, zona <i>bawah</i> kedalaman di bawah permukaan terbawah; blok di atas topografi adalah udara dan tidak pernah ikut. Sampelnya interval yang kodenya tidak dipetakan ke lapisan mana pun.</p>'
   + steps('Sesudah &#9314; Estimasi, buka bagian <b>&#9316;b Estimasi waste</b> &rarr; <b>Periksa dulu</b> ([[wl_panel]]).', 'Klik <b>Jalankan</b>. Hasil: <code>sl_pass = 9</code>, kategori <code>sl_lapisan = WASTE (di luar lapisan)</code> ([[wl_hasil]], [[wl_2d]]).')
   + ''.join(fig(k, c) for k, c in (('wl_panel', 'Bagian &#9316;b sesudah Periksa dulu.'), ('wl_hasil', clean(NL.get('wlHasil', 'Hasil estimasi waste laterit.'))), ('wl_2d', 'Sayatan 2D sl_lapisan: tanah penutup di atas atap limonit kini berkadar (WASTE).')) if k in FIG)
   + warn('Setiap kali estimasi lapisan &#9314; dijalankan ulang, estimasi waste laterit ikut terhapus &mdash; jalankan ulang sesudahnya.') if 'wl_panel' in FIG else '')
 + '<h3>Bauksit &amp; stratiform (sedex)</h3>'
 + kv([('Preset Bauksit','Overburden, Bauksit, Kaolin / lempung, Batuan dasar; pakai unsur Al2O3, SiO2 reaktif, Fe2O3 dan rasio Al2O3 / SiO2'),
       ('Preset Stratiform (sedex)','Hanging wall, Lapisan bijih (Akumulasi 2D), Footwall; lapisan tidak harus mengikuti topografi; sesar post dipulihkan, growth fault = syn + batas keras'),
       ('Akumulasi 2D','per bor: tebal lapisan T dan kadar rata-rata g; kadar blok = &Sigma;(w &middot; T &middot; g) / &Sigma;(w &middot; T): cocok untuk lapisan tipis yang tebalnya berubah')])
 + fig('tree', 'Project Tree: Struktur Geologi &rsaquo; Sesar (bidang 3D) dan Geomodeller Stratified-Laterite Deposit dengan node lapisan &amp; tahap &#9312;&ndash;&#9315;.', '40%')
 + tip('Semua pengaturan lapisan, sesar dan hasil estimasi tersimpan per proyek; tabel <code>sesar</code> dan <code>lapisan</code> ikut ke database proyek SQLite (gcex_proyek.db).'))

ch('Autorun: wireframe & estimasi sekali jalan (vein)', dta('lanjutan &mdash; proyek vein beserta flag terbarunya (jalankan sesudah upsert bor baru)',
     [('Domain yang dicentang', '<code>QV_Lensa2</code>, <code>QV_Splay_HW</code>'),
      ('Spasi section', '<b>20 m</b> (seperempat sampai separuh spasi bor; data latihan berjarak 20 m)'),
      ('Bangun ulang string yang sudah diedit tangan', '<b>mati</b> &mdash; biarkan begitu'),
      ('Yang diklik', 'menu node &rarr; <b>Jalankan untuk domain tercentang</b>'),
      ('Yang dibaca', 'laporan per section: <b>dibuat</b> / <b>diperbarui</b> / <b>dilewati (diedit tangan)</b> / <b>kontak &lt; 2</b>')]) +  '<p>Sesudah beberapa periode grade control, pekerjaannya jadi berulang: bor baru masuk lewat upsert, Anda flagging, lalu <b>langkah-langkah yang sama</b> dikerjakan lagi &mdash; tarik string tiap section, bangun solid, estimasi ulang, estimasi waste, segarkan laporan. Dua node <b>Autorun</b> menjahit langkah itu menjadi satu perintah. Tidak ada algoritme baru di dalamnya: yang dipanggil adalah fungsi yang sama dengan yang Anda pakai manual.</p>'
 + '<h3>1. Autorun Wireframe (node di bawah Geomodeller Vein)</h3>'
 + steps('Centang domain yang ikut &mdash; tiap domain muncul sebagai <b>anak node</b> dengan centangnya sendiri.',
         'Menu node &rarr; <b>Pengaturan autorun&hellip;</b> untuk menentukan <b>spasi section</b> (lazimnya seperempat sampai separuh spasi bor). Hanya ini yang perlu diputuskan.',
         'Menu node &rarr; <b>Jalankan untuk domain tercentang</b>.')
 + '<p>Untuk setiap domain, GC-Ex menghitung <b>strike</b>-nya dari titik tengah kontak flag, memasang garis section <b>tegak lurus strike</b> melewati pusat data, lalu menarik string di <b>semua section</b> dengan spasi yang Anda tentukan. Solid terbangun ulang sendiri sesudahnya.</p>'
 + '<h3>&ldquo;Dari nol&rdquo; dan &ldquo;melanjutkan&rdquo; adalah perintah yang sama</h3>'
 + '<p>Ini yang paling perlu dipahami: keputusannya diambil <b>per section</b>, bukan per perintah.</p>'
 + '<table class="t"><tr><th>Keadaan section</th><th>Yang dilakukan autorun</th></tr>'
 + '<tr><td>Belum ada string</td><td><b>dibuat</b></td></tr>'
 + '<tr><td>Ada string hasil autorun</td><td><b>diperbarui</b> mengikuti flag terbaru</td></tr>'
 + '<tr><td>Ada string yang <b>Anda edit tangan</b></td><td><b>dilewati</b> &mdash; tidak pernah ditimpa &mdash; dan dihitung di laporan</td></tr>'
 + '<tr><td>Kontak flag kurang dari 2</td><td>dilewati dan dihitung di laporan</td></tr></table>'
 + why('Karena itu autorun aman dijalankan berulang kali. Sesudah upsert bor baru, perintah yang sama otomatis bersifat melanjutkan: section yang sudah Anda rapikan tangan tetap utuh, section baru dan section otomatis ikut terbarui. Menjalankannya dua kali berturut-turut tidak menambah satu string pun.')
 + warn('Pilihan <b>Bangun ulang semua, termasuk string yang sudah diedit tangan</b> ada di Pengaturan, bawaannya <b>mati</b>, dan selalu meminta konfirmasi. Nyalakan hanya bila interpretasi lama memang mau dibuang.')
 + '<h3>2. Autorun Estimation (node di bawah Model Estimation)</h3>'
 + '<p>Perintah ini <b>tidak</b> melakukan fitting variogram. Ia memakai <b>parameter yang sudah Anda simpan per domain</b> ({{B:Uji estimasi}}) apa adanya, menjalankan estimasi inkremental, lanjut ke estimasi waste, lalu menyegarkan Reporting BM.</p>'
 + '<table class="t"><tr><th>Keadaan domain</th><th>Yang dilakukan</th></tr>'
 + '<tr><td>Solid ada + parameter tersimpan ada</td><td><b>diestimasi</b> &mdash; hanya blok yang lingkungan kriging-nya berubah ({{B:Koreksi setelah bor baru}})</td></tr>'
 + '<tr><td>Belum ada parameter tersimpan</td><td><b>dilewati</b>, dengan alasan tertulis: <i>&ldquo;di Geostatistik: fitting model, lalu Simpan ke domain&rdquo;</i></td></tr>'
 + '<tr><td>Solid belum dinyalakan / gagal</td><td><b>dilewati</b>, dengan sebabnya</td></tr>'
 + '<tr><td>Tidak ada bor baru yang mempengaruhinya</td><td>dilewati &mdash; tidak ada blok yang perlu dikoreksi</td></tr></table>'
 + why('Mengganti variogram yang sudah disetujui dengan hasil fit otomatis diam-diam adalah hal terakhir yang kita inginkan di model produksi. Jadi autorun lebih memilih <b>tidak mengerjakan</b> sebuah domain daripada mengarang parameternya. Domain baru tetap melewati Geostatistik dengan mata Anda sendiri.')
 + '<h3>3. Laporan autorun &mdash; bagian yang membuatnya bisa dipertanggungjawabkan</h3>'
 + '<p>Setiap autorun membuka satu halaman laporan, dan bisa diunduh sebagai CSV:</p>'
 + kv([('Hasil', 'per domain: string baru / diperbarui / dilewati, atau blok diestimasi / ditambah'),
       ('Sebelum &rarr; sesudah', 'volume solid (m&sup3;) dan persen perubahannya; untuk estimasi: kadar rata-rata dan tonase <b>dibanding run sebelumnya</b>'),
       ('Catatan', 'strike dan spasi section yang dipakai, asal parameter, atau <b>alasan dilewati</b>')])
 + tip('Kolom <b>Sebelum &rarr; sesudah</b> adalah tempat pertama yang dilihat. Volume solid yang melonjak padahal bor barunya sedikit biasanya berarti string otomatis di section bertepi data perlu dirapikan tangan. Kadar rata-rata yang berubah jauh tanpa penambahan bor yang sepadan berarti ada yang perlu ditelusuri di riwayat run &mdash; dan riwayat run bisa dibatalkan.')
 + '<h3>Alur kerja harian sesudah ada autorun</h3>'
 + steps('<b>Upsert</b> data bor baru ke kampanye yang sesuai ({{B:Database bor per kampanye}}).',
         '<b>Flagging</b> interval bor baru &mdash; ini tetap pekerjaan Anda, tidak diotomatiskan.',
         'Node <b>Autorun Wireframe</b> &rarr; jalankan. Periksa laporannya.',
         'Node <b>Autorun Estimation</b> &rarr; jalankan. Periksa kolom sebelum &rarr; sesudah.',
         'Bila ada domain <b>baru</b>, ia akan dilewati &mdash; kerjakan Geostatistik untuk domain itu sekali ({{B:Variogram, anisotropi}}, {{B:Uji estimasi}}), simpan parameternya, sesudah itu ia ikut autorun selamanya.')
 + warn('Yang <b>tidak pernah</b> diotomatiskan: keputusan domain dan flag (itu geologi), interpretasi sesar, dan ambang klasifikasi Measured / Indicated / Inferred (itu ranah pelaporan). Autorun mengulang pekerjaan, bukan mengambil keputusan.'))

ch('Estimasi waste pada laterit', dta('lanjutan &mdash; proyek laterit sesudah lapisan dan estimasi per lapisan selesai',
     [('Prasyarat', 'kerangka blok AOI yang mencakup <b>seluruh</b> AOI, bukan hanya zona laterit'),
      ('Zona yang dinyalakan', '<b>bawah</b> (saprock / bedrock) &mdash; untuk latihan nyalakan juga <b>atas</b>'),
      ('Sumber variogram', '<b>variogram lapisan terdekat</b>, atau simpan variogram waste sendiri dari Geostatistik'),
      ('Hasil yang seharusnya', 'blok bertanda <code>domain_est = WASTE</code>, <code>est_type = 3</code>')]) +  '<p>Jalur <b>Stratified-Laterite</b> punya mesin estimasinya sendiri: setiap blok dicari lapisannya, dan blok yang <b>tidak jatuh di lapisan mana pun</b> (<code>sl_lapisan</code> kosong) tidak pernah diestimasi. Padahal untuk melaporkan volume <b>ore dan waste</b> di bawah topografi atau di dalam desain pit, blok itu justru harus punya kadar. Bagian <b>&#9317; Estimasi waste</b> di menu <b>Stratified-Laterite</b> mengisinya.</p>'
 + warn('Tiga bab yang mendahuluinya ada di <b>Bagian II</b> karena murni geometri dan berlaku untuk semua tipe deposit &mdash; bacalah dulu {{B:Block model dari nol}} (kerangka blok AOI), {{B:Sub-blocking}} (proporsi volume di batas lapisan) dan {{B:Estimasi waste}} (prinsip umum, jalur vein). Bab ini hanya menjelaskan <b>apa yang berbeda</b> pada laterit.', 'Dibaca sesudah Bagian II')
 + '<h3>Dua zona waste, masing-masing dengan ruang unfold sendiri</h3>'
 + '<p>Pada laterit, jarak lurus tidak mewakili kedekatan geologi: sampel harus dicari <b>mengikuti kelengkungan permukaan lapisan</b>. Karena itu tiap zona waste diberi ruang <b>unfold</b>-nya sendiri, sama seperti estimasi ore per lapisan.</p>'
 + '<table class="t"><tr><th>Zona</th><th>Blok yang masuk</th><th>Koordinat unfold</th></tr>'
 + '<tr><td><b>Bawah</b></td><td>di bawah permukaan terbawah model &mdash; bedrock / saprock di bawah zona laterit</td><td><code>z = z_dasar(x,y) &minus; z_blok</code> (kedalaman di bawah permukaan itu)</td></tr>'
 + '<tr><td><b>Atas</b></td><td>di atas kontak teratas model tetapi <b>masih di bawah topografi aktif</b> &mdash; mis. limonit penutup yang tidak dimodelkan sebagai lapisan</td><td><code>z = z_blok &minus; z_atap(x,y)</code> (tinggi di atas kontak teratas)</td></tr>'
 + '<tr><td><i>(Luar grid)</i></td><td>di luar cakupan grid permukaan (permukaan tidak terdefinisi)</td><td>tidak ada kerangka unfold &rarr; elevasi apa adanya (3D biasa). <b>Opsional, bawaan mati</b></td></tr></table>'
 + why('Blok di <b>atas topografi</b> adalah <b>udara</b>, bukan waste, jadi tidak pernah ikut diestimasi. Inilah bedanya dengan jalur vein, yang batas atasnya adalah permukaan solid; pada laterit batas atasnya adalah topografi itu sendiri.')
 + '<h3>Sampelnya dari mana</h3>'
 + '<p>Komposit diambil dari interval geologi yang kodenya <b>tidak dipetakan ke lapisan mana pun</b> &mdash; <i>hard boundary</i> waste, sama semangatnya dengan jalur vein ({{B:Estimasi waste}}): material di luar model tidak boleh diestimasi dari sampel di dalam model, dan sebaliknya. Tiap komposit ditempatkan ke zona (bawah / atas) yang sesuai dengan posisinya, lalu dikrige di ruang unfold zona itu.</p>'
 + steps('Selesaikan dulu pemodelan lapisan dan estimasi per lapisan ({{B:Geomodeller Stratified-Laterite}}).',
         'Pastikan ada <b>kerangka blok</b> yang mencakup seluruh AOI, bukan hanya zona laterit ({{B:Block model dari nol}}) &mdash; blok waste tidak akan ada bila kerangkanya hanya sebesar lapisan.',
         'Buka <b>Stratified-Laterite &rarr; &#9317; Estimasi waste</b>, nyalakan zona <b>bawah</b> dan / atau <b>atas</b> sesuai keadaan endapan Anda.',
         'Pilih sumber variogramnya: <b>variogram waste sendiri</b> (di Geostatistik pilih populasi waste, fitting, lalu <b>Simpan</b>) atau <b>variogram lapisan terdekat</b>; blok yang terlalu jauh dari sampel mana pun diisi <b>IDW</b>.',
         'Jalankan. Hasilnya ditandai sebagai domain semu <b>WASTE</b> dengan <code>est_type = 3</code>, jadi <b>tidak ikut</b> pelaporan sumber daya ({{B:Klasifikasi keyakinan}}).')
 + tip('Untuk laterit nikel, zona <b>bawah</b> biasanya yang paling berguna: kadar Ni di saprock/bedrock di bawah batas lapisan menentukan sampai mana alat gali boleh turun sebelum material menjadi waste. Zona <b>atas</b> dipakai bila ada penutup (overburden limonitik) yang tidak dimodelkan sebagai lapisan tetapi tetap harus dihitung tonasenya.'))

ch('Autorun pada laterit: lapisan & estimasi', dta('lanjutan &mdash; proyek laterit; kolom geologi <code>Zona</code>',
     [('Minimal hole per kode', '<b>3</b> (bawaan) &mdash; kode yang lebih jarang dilewati'),
      ('Batas jumlah lapisan', '<b>12</b>'),
      ('Ukuran sel permukaan', 'bila GC-Ex meminta konfirmasi karena gridnya besar: <b>Batal</b>, perbesar ukuran sel di &#9313; Permukaan, jalankan lagi'),
      ('Hasil yang seharusnya', 'urutan <b>TS</b> 0,9 m &rarr; <b>LIM</b> 4,2 m &rarr; <b>SAP</b> 11,3 m &rarr; <b>BRK</b> 17,6 m')]) +  '<p>Jalur berlapis punya autorun-nya sendiri: node <b>Autorun Lapisan &amp; Estimasi</b> di bawah <b>Geomodeller Stratified-Laterite</b>. Prinsipnya sama dengan jalur vein ({{B:Autorun: wireframe}}) &mdash; mengulang langkah yang sudah ada, tidak mengambil keputusan geologi &mdash; hanya langkahnya berbeda.</p>'
 + '<h3>1. Usulan lapisan dari log geologi</h3>'
 + '<p>Bila <b>belum ada</b> lapisan berkode, menu node &rarr; <b>Usulkan lapisan dari log geologi&hellip;</b> membaca kolom geologi yang dipilih, lalu untuk tiap kode menghitung <b>kedalaman tengah rata-rata</b> (ditimbang panjang interval) dan membuat satu lapisan per kode, <b>diurutkan dari yang paling atas</b>.</p>'
 + kv([('Yang dilewati', 'kode yang ditembus lebih sedikit dari ambang <b>Minimal hole per kode</b> (bawaan 3) &mdash; dilaporkan, tidak dijadikan lapisan'),
       ('Urutan lapisan', 'mengikuti kedalaman tengah rata-rata, sehingga limonit di atas, saprolit di bawahnya, dan seterusnya'),
       ('Batas jumlah', 'maksimal <b>12 lapisan</b>. Lebih dari itu dilaporkan: kolom tersebut kemungkinan <b>litologi biasa</b>, bukan kode lapisan &mdash; pilih kolom lain'),
       ('Bila lapisan sudah ada', 'pemetaan kode <b>tidak diubah</b> &mdash; autorun hanya membangun ulang permukaannya')])
 + '<p>Pada data latihan laterit, hasilnya persis urutan stratigrafinya: <b>TS</b> 0,9 m &rarr; <b>LIM</b> 4,2 m &rarr; <b>SAP</b> 11,3 m &rarr; <b>BRK</b> 17,6 m.</p>'
 + warn('Membangun permukaan adalah perhitungan <b>berat</b>: jumlah lapisan dikali jumlah sel grid. Bila hasilnya melebihi beberapa juta sel, GC-Ex <b>meminta konfirmasi</b> lebih dulu, menyebut ukuran gridnya, dan memperingatkan bahwa tampilan akan berhenti merespons beberapa menit. Jalan keluarnya: <b>Batal</b>, perbesar <b>Ukuran sel</b> di &#9313; Permukaan, lalu jalankan lagi.', 'Perhitungan berat')
 + warn('Usulan ini berdasarkan <b>kedalaman</b>, bukan pengertian geologi. Kode yang hadir di dua posisi stratigrafi, atau kode campuran, akan salah tempat. Karena itu laporannya selalu mengingatkan: <b>periksa dan perbaiki pemetaan kodenya</b> di &#9312; Lapisan &amp; kode log sebelum mengestimasi. Yang diotomatiskan adalah pekerjaan mengetiknya, bukan penafsirannya.')
 + '<h3>2. Permukaan atap / lantai</h3>'
 + '<p>Sesudah lapisan ada, autorun langsung membangun permukaannya dan melaporkan ukuran gridnya. Ini langkah yang di jalur vein setara dengan solid RBF.</p>'
 + '<h3>3. Estimasi lapisan + waste laterit</h3>'
 + steps('Menu node &rarr; <b>Jalankan estimasi lapisan + waste</b>.',
         'Tiap lapisan memakai <b>parameter tersimpannya sendiri</b> (metode, ruang unfold, radius) &mdash; autorun tidak mengubahnya.',
         'Lapisan tanpa kode, atau yang estimasinya dimatikan di &#9314;, <b>dilewati</b> dengan alasannya.',
         'Sesudah semua lapisan selesai, autorun lanjut ke <b>estimasi waste laterit</b> ({{B:Estimasi waste pada laterit}}) &mdash; zona bawah dan atas dengan ruang unfold masing-masing.')
 + '<p>Laporannya sama bentuknya dengan jalur vein: hasil per lapisan, perbandingan, dan daftar yang dilewati beserta sebabnya, dengan tombol unduh CSV.</p>'
 + tip('Untuk endapan laterit yang dibor rapat per periode, inilah urutan harian yang masuk akal: upsert data bor &rarr; periksa pemetaan kode bila ada kode log baru &rarr; <b>Bangun ulang permukaan lapisan</b> &rarr; <b>Jalankan estimasi lapisan + waste</b> &rarr; periksa &#9315; Laporan WMT / DMT.'))

ch('Map: peta geologi 2D', dta('<code>data/SIM_pickup_survey.csv</code> &mdash; ' + f"{N['pickN']} titik pick-up survei (kolom <code>Kode, Easting, Northing, RL, Tebal_m, Keterangan</code>)",
     [('Import lewat', 'menu <b>Map</b> &rarr; import titik'),
      ('Garis struktur', 'jenis <b>Vein / urat</b> &mdash; klik titik kode <code>VEIN_HW</code> berurutan, <b>Enter</b> untuk menutup'),
      ('Poligon alterasi', 'nama <code>SIL</code>'),
      ('Layout', 'judul <code>Peta Geologi Vein A (latihan)</code>, subjudul <code>Data simulasi GC-Ex</code>')]) +  '<p>Menu <b>Map</b> di rel kiri mengganti area grafik dengan peta 2D (Easting / Northing; Z tidak dipakai), seperti Global Mapper. Scroll = zoom, tarik = geser; koordinat kursor tampil di kiri bawah.</p>'
 + '<h3>Layer peta</h3>' + steps('Klik <b>Map</b> di rel kiri ([[map_layer]]).', 'Centang layer: orthofoto, kontur topografi (interval diatur), desain pit, collar, jejak bor, domain vein, struktur (simbol USGS), fitur digitasi, titik pick-up, label.')
 + fig('map_layer', 'Map dengan kontur topografi 5 m, collar dan jejak bor, titik tengah domain QV_Lensa2 dan simbol struktur USGS (strike + tick arah dip + angka dip).')
 + kv([('Simbol struktur USGS','miring: garis strike + tick ke arah dip + angka dip; tegak (&ge; 85&deg;): garis strike + tick dua sisi; datar (&le; 5&deg;): lingkaran bersilang')])
 + '<h3>Import titik pick-up survei</h3>' + steps('Bagian <b>Titik pick-up survei / pemetaan</b> &rarr; <b>&#8679; Import CSV titik</b>, pilih <code>SIM_pickup_survey.csv</code> (kolom <code>ID, East, North, RL, Code</code>; header fleksibel).',
   'Titik diwarnai per Code. Centang <b>garis per Code</b> untuk menyambung titik ber-Code sama (VEIN_HW, VEIN_FW, TOE, CREST) ([[map_pickup]]). Label: ID / Code / RL / tanpa label.',
   'Tombol per file: <b>&#8981;</b> zoom ke file, <b>&#8631;</b> jadikan fitur digitasi (bisa diedit &amp; export DXF), <b>&times;</b> hapus file.')
 + fig('map_pickup', f"{N['pickN']} titik pick-up: batas HW dan FW singkapan vein, serta TOE dan CREST pit kecil, disambung per Code.")
 + '<h3>Digitasi vein, alterasi &amp; litologi</h3>' + steps('Bagian <b>Digitasi</b>: pilih <b>Jenis</b> &mdash; Boundary alterasi, Boundary litologi, Garis struktur, atau Garis lain.',
   'Vein sebagai garis: Jenis <b>Garis struktur</b>, Tipe <b>Vein / urat</b>. Vein bersinggungan dengan lebar: Jenis <b>Boundary litologi</b>, nama <code>QV</code>.',
   'Klik <b>&#9998; Mulai digitasi</b>, lalu klik titik-titik di peta. Titik <b>menempel (snap)</b> ke titik pick-up dan titik fitur lain (lingkaran oranye).',
   'Klik ganda / <b>Enter</b> = simpan fitur, Backspace = hapus titik terakhir, Esc = batal. Mode digitasi tetap aktif untuk fitur berikutnya.',
   'Edit fitur: klik namanya di daftar &rarr; tarik kotak = geser titik, tarik bulatan tengah = sisip, Shift+klik = hapus titik, Delete = hapus fitur. Export <b>DXF</b> / <b>CSV</b>.')
 + fig('map_digit', 'Vein didigit di atas titik pick-up VEIN_HW (snap) dan boundary alterasi SIL di sekitarnya: ' + ', '.join(MF) + '.')
 + '<h3>Layout peta</h3>' + steps('Isi <b>Judul</b>, <b>Sub judul</b>, <b>Dibuat oleh</b>, pilih <b>Kertas</b> (A4 / A3, lanskap / potret).',
   'Atur zoom peta sesuai area yang ingin dicetak.', '<b>&#8681; Layout PNG</b> menyimpan gambar; <b>&#128438; Cetak / PDF</b> membuka dialog cetak browser &rarr; Simpan sebagai PDF.')
 + fig('map_layout', 'Contoh layout A4 lanskap: peta, legenda dari layer yang tampil, panah utara, skala grafis dan perkiraan skala numerik, serta kotak judul.')
 + tip('Fitur peta, titik pick-up, pengaturan layer dan layout tersimpan di proyek. Skala grafis akurat; skala numerik adalah perkiraan dari lebar tampilan.'))

PS = N.get('planSet') or []
if PS:
  ch('Plan bor harian: satu plan per hari / per bench', dta('lanjutan &mdash; tidak ada berkas masuk; titik dibuat di peta plan dari data latihan',
     [('Yang diklik', 'baris <b>+ Tambah plan bor&hellip;</b> (paling bawah di <b>Database Bor &rarr; Plan bor (rencana)</b>)'),
      ('Plan 1', f"<b>{PS[0][0]}</b>: alat <b>Garis</b>, 5 titik; lalu extend 2 titik &rarr; <b>{PS[0][1]} titik</b> ({PS[0][2]})"),
      ('Plan 2', f"<b>{PS[1][0]}</b>: alat <b>Grid area</b> 3 &times; 2 di timur laut &rarr; <b>{PS[1][1]} titik</b> ({PS[1][2]})" if len(PS) > 1 else '-'),
      ('Hasil yang seharusnya', 'dua sub-node bernomor 1. dan 2. di bawah <b>Plan bor (rencana)</b>, badge <b>' + f"{len(PS)} plan &middot; {sum(x[1] for x in PS)} titik" + '</b>')])
   + '<p>Rencana bor dibuat bertahap: hari ini satu baris di bench RL240, besok grid di bench lain, lusa tambahan di lokasi kemarin. Mulai Drillhole 0.24.44 setiap rencana disimpan sebagai <b>plan tersendiri</b> dan tampil <b>berurutan</b> sebagai sub-node <b>Plan bor (rencana)</b>. Hanya satu plan yang <b>aktif</b>: titik baru, Hapus semua, Nomori ulang dan Export CSV di panel bekerja pada plan aktif saja.</p>'
   + steps('Buka node <b>Plan bor (rencana)</b> dan klik baris <b>+ Tambah plan bor&hellip;</b> di paling bawah ([[plan_set]]). Nama bawaan <i>Plan tanggal &middot; bench</i>; ganti bila perlu, misalnya <code>' + PS[0][0] + '</code>.',
     'Di panel Plan Bor isi <b>Bench</b> <code>RL240</code>, pilih alat <b>Garis</b> lalu tarik garis di peta plan: 5 titik dengan spasi sesuai isian <b>Spasi (m)</b>.',
     'Hari berikutnya: <b>+ Tambah plan bor&hellip;</b> lagi, Bench <code>RL235</code>, alat <b>Grid area</b>: klik sudut-sudut area, klik ganda untuk selesai &rarr; ' + (f"{PS[1][1]} titik." if len(PS) > 1 else 'grid titik.'),
     'Extend di lokasi plan pertama: tombol &#8943; sub-node <b>1.</b> &rarr; <b>Jadikan plan aktif</b> (atau pilih di kotak plan di atas panel), lalu tambah titik. Nomor melanjutkan urutan plan itu: ' + PS[0][2] + '.',
     'Centang / hapus centang sub-node untuk menampilkan atau menyembunyikan plan di 3D dan di peta. Plan aktif digambar <b>magenta tegas</b>, plan lain <b>ungu pudar</b> ([[plan_peta]]).',
     'Export: tombol &#8943; sub-node &rarr; <b>Export CSV plan ini&hellip;</b> (nama file dari nama plan), atau node induk &rarr; <b>Export CSV semua plan&hellip;</b> (satu file, kolom Plan).')
   + fig('plan_set', 'Project Tree: <b>Plan bor (rencana)</b> berisi ' + ', '.join(f"{i+1}. {x[0]} ({x[1]} titik)" for i, x in enumerate(PS)) + '. Plan 1 bertanda <i>aktif</i>; panel Plan Bor di kanan memakai plan aktif.', '62%')
   + fig('plan_peta', f"Peta plan: plan aktif ({PS[0][0]}, {PS[0][1]} titik) magenta tegas di antara collar lama; plan RL235 ({PS[1][1] if len(PS)>1 else 0} titik) ungu pudar di timur laut.")
   + tip('Plan tersimpan di proyek bersama sesi kerja. Proyek lama yang dibuat sebelum 0.24.44 dibuka dengan satu plan bernama <b>Plan lama</b> berisi semua titik sebelumnya.')
   + warn('<b>Hapus semua</b> di panel dan menu <b>Hapus semua titik di plan aktif&hellip;</b> hanya mengosongkan plan aktif. Untuk membuang satu plan utuh pakai <b>Hapus plan ini&hellip;</b> di sub-node-nya.'))

ch('Mengganti topografi & block model (Data Spasial)', dta('<code>data/SIM_topo_xyz_nov.csv</code> &mdash; topografi bulan berikutnya (area pit turun sampai 6 m)',
     [('Yang diklik', '<b>Data Spasial</b> &rarr; &#9312; Topografi &rarr; <b>+ Tambah versi topografi</b>'),
      ('Berkas', '<code>SIM_topo_xyz_nov.csv</code>'),
      ('Sesudahnya', 'centang <b>Banding</b> pada versi lama; tombol <b>Aktif</b> untuk berganti versi'),
      ('Hasil yang seharusnya', clean(N.get('spMsg', ''))[:170])]) +  '<p>Topografi pick-up, orthofoto, desain pit dan block model GC berganti tiap periode. Data baru ditambahkan di menu <b>Data Spasial</b> sebagai <b>versi</b>: satu versi aktif dipakai, versi lama tetap tersimpan dan bisa diaktifkan lagi.</p>'
 + steps('Klik <b>Data Spasial</b> di rel kiri.',
   'Di bagian <b>&#9312; Topografi</b> klik <b>+ Tambah versi topografi</b> dan pilih <code>SIM_topo_xyz_nov.csv</code> (topografi bulan berikutnya: area pit turun hingga 6 m).',
   f"Versi baru langsung aktif. {clean(N.get('spMsg',''))}",
   'Centang <b>Banding</b> pada versi lama untuk menampilkannya sebagai titik / garis putus-putus ([[data_spasial]]). Klik tombol bulat <b>Aktif</b> untuk kembali ke versi lama kapan saja.',
   'Block model GC baru: <b>+ Tambah versi block model</b> (jendela Import BM). Di proyek folder jawab <b>OK</b> saat ditawari menyalin file ke folder proyek.')
 + fig('data_spasial', 'Menu Data Spasial: dua versi topografi; versi lama ditampilkan sebagai pembanding di 3D.')
 + tip('Hasil kerja mencatat versi yang dipakai: solid vein yang dipotong topografi dibangun ulang otomatis; uji estimasi dan Model Estimation memberi tanda bila topografi / block model aktif berbeda dari saat dijalankan.')
 + warn('Jangan mengganti data lewat import ulang di proyek folder. Pakai menu Data Spasial agar versi lama tetap ada dan hasil kerja ikut diperbarui.'))

ch('Topografi & orthofoto resolusi tinggi', '<p>Mulai 0.24, orthofoto dan topografi resolusi tinggi ditampilkan tanpa membuat tampilan tersendat. Orthofoto disusun menjadi <b>piramida LOD</b>; warna diambil dari tingkat yang sepadan dengan kerapatan tampilan, dan resolusi mesh mengikuti luas area yang sedang terlihat &mdash; zoom masuk otomatis makin detail. Di <b>Peta (Mapping)</b> orthofoto dipotong sesuai tampilan, setajam layar.</p>'
 + '<table class="t"><tr><th></th><th>Sebelum</th><th>Sesudah</th></tr><tr><td>Mesh ortho, zoom 40 m</td><td>1 m/titik &middot; 592 ms</td><td><b>0,1 m/titik</b> &middot; 136 ms</td></tr><tr><td>Mesh ortho, zoom 10 m</td><td>1 m/titik &middot; 592 ms</td><td><b>0,1 m/titik</b> &middot; <b>3 ms</b></td></tr><tr><td>Gambar ortho Peta, zoom 10 m</td><td>2.666 &times; 2.666 px &middot; 255 ms</td><td>220 &times; 220 px @ 0,05 m &middot; 6 ms</td></tr><tr><td>200.000 pembacaan elevasi</td><td>512 ms</td><td><b>14 ms</b></td></tr></table>'
 + kv([('Resolusi (m) di panel orthofoto','sekarang <b>batas paling halus</b>, bukan resolusi tetap'),('Penyegaran','&plusmn;0,3 detik setelah zoom / geser berhenti; klik ganda / autoscale kembali ke seluruh area'),('Hasil laporan','tidak berubah: grid elevasi cepat hanya untuk tampilan; Reporting BM, estimasi dan validasi memakai fungsi elevasi aslinya (selisih rata-rata 4 mm pada uji 300 titik)')])
 + tip('Latihan: di {{B:Mengganti topografi}} Anda sudah memasang <code>SIM_topo_xyz_nov.csv</code> sebagai versi kedua. Hitung volume sisa di Reporting BM dengan batas <b>di bawah topografi aktif</b> untuk kedua versi &mdash; bedanya adalah material yang sudah tergali.'))

ch('Export database & block model', dta('lanjutan &mdash; tidak ada berkas masuk; bab ini menghasilkan berkas',
     [('Dip di survey', '<b>negatif = ke bawah</b> (Surpac / Leapfrog)'),
      ('Hasil yang seharusnya', clean(N['exportDb'])),
      ('Isi ZIP', '<code>' + ', '.join(N['zipIsi']) + '</code>'),
      ('Block model', '<b>Export .mdl (Surpac)</b> bila dibuka dari .mdl; dari CSV: <b>CSV blok domain</b> &mdash; ' + clean(N['meCsv']))]) +  steps(
 'Tombol &#8943; node <b>Database Bor</b> &rarr; <b>Export database (CSV)</b> (atau tombol yang sama di panel Data). Pilih <b>Dip di survey</b>: negatif = ke bawah (Surpac / Leapfrog umumnya negatif).',
 f"Hasil: {clean(N['exportDb'])} File ZIP berisi: <code>{', '.join(N['zipIsi'])}</code>.",
 'Kolom <code>Ore_Domain</code> di assay &amp; geologi berisi domain dari flag, siap dipakai sebagai interval selection di Leapfrog atau Surpac.',
 'Block model hasil Model Estimation: tombol &#8943; node <b>Block Model</b> &rarr; <b>Export block model GC (.mdl)</b>, atau <b>&#8681; Export .mdl (Surpac)</b> di Model Estimation (bila block model dibuka dari file .mdl). Header &amp; atribut asli tetap, atribut baru ditambahkan di akhir, blok tambahan disisipkan sesuai urutan octree Surpac. Block model dari CSV: <b>&#8681; CSV blok domain</b> ' + f"({clean(N['meCsv'])}).",
 'String kontrol: <b>&#8681; Export STR</b> / <b>&#8681; Export DXF</b>; flag: <b>&#8681; Export flag (CSV)</b>; solid: <b>OBJ / DXF / STR+DTM</b> di Geomodeller Vein.')
 + tip('Jika menu <b>Proyek &rarr; Salin setiap export ke folder proyek/export</b> aktif, salinan export juga tersimpan di folder proyek, misalnya <code>export/2026-10-22/GCEx_Database_VeinA_Simulasi_20261022.zip</code>.')
 + warn('Export .mdl dengan atribut &amp; blok tambahan sudah diuji dibaca ulang oleh GC-Ex dan dibandingkan per record dengan file asli (model Z3, 590.478 blok). Uji buka di Surpac tetap disarankan sebelum dipakai produksi.'))

ch('Folder proyek, backup & pemulihan', dta('folder <code>Proyek_Tutorial_VeinA</code> hasil seluruh latihan',
     [('Yang dilihat', f"nama folder, <b>revisi {N['rev']}</b>, waktu simpan, pengguna"),
      ('Yang diisi', 'tidak ada &mdash; simpan otomatis 3 detik sesudah tiap perubahan'),
      ('Latihan pemulihan', '<b>Pulihkan dari backup&hellip;</b> &rarr; pilih versi beralasan <i>sebelum upsert</i> &rarr; <b>Pulihkan</b>')]) +  steps(
 'Klik <b>Proyek</b> di bar atas ([[proyek_menu]]). Terlihat nama folder, nomor revisi, waktu simpan dan pengguna.',
 '<b>Simpan sekarang</b> memaksa simpan + backup. Biasanya tidak perlu: simpan otomatis berjalan 3 detik setelah perubahan. Bila simpan otomatis sedang berjalan, tombol ini menunggu sampai selesai.',
 '<b>Pulihkan dari backup&hellip;</b> menampilkan daftar versi beserta alasannya (proyek baru, data berubah, sebelum upsert, estimasi berubah, &hellip;). Klik <b>Pulihkan</b> pada versi yang diinginkan ([[proyek_pulihkan]]). Versi saat ini dicadangkan dulu sebelum dipulihkan.')
 + fig('proyek_menu', f"Menu Proyek: folder Proyek_Tutorial_VeinA pada revisi {N['rev']}, block model sumber <code>sumber/SIM_BM_GC.csv</code> tercentang (ada di folder).", '78%')
 + fig('proyek_pulihkan', 'Dialog pemulihan berisi versi-versi backup dengan alasan perubahan.')
 + '<h3>Isi folder proyek</h3>' + kv([('gcex_data.json','database bor + data spasial'),('gcex_model.json','domain, flag, string, wireframe referensi'),('gcex_estimasi.json','hasil estimasi OK'),('gcex_project.json','pengaturan tampilan & daftar bagian'),('sumber/','file block model sumber (dibaca ulang saat proyek dibuka)'),('backup/','versi berkala + salinan bagian yang berubah'),('export/','salinan semua export (bila diaktifkan)')])
 + warn('Satu folder proyek dipakai satu orang pada satu waktu. Jika rekan membuka folder yang sedang dipakai, GC-Ex membukanya <b>hanya-baca</b> dan menyebut siapa yang sedang memakai.'))

ch('Status pengembangan', '<p>Status pengembangan. Langkah di buku ini tetap berlaku; tahap baru menambah menu, tidak mengubah yang sudah ada.</p>'
 + '<table class="t"><tr><th>Tahap</th><th>Isi</th></tr>'
 + '<tr><td><b>Tahap 2</b><br>Solid vein RBF</td><td><b>Sudah tersedia</b> ({{B:Membangun solid}}): permukaan HW dan FW per domain dimodelkan terpisah (RBF), solid dengan tebal minimum 1 m, potong tegas searah strike (radius pengaruh 15 m), pinch-out / potong topografi searah dip, orientasi & elipsoid per domain, dibangun ulang otomatis, export OBJ / DXF / Surpac STR+DTM.</td></tr>'
 + '<tr><td><b>Tahap 3</b><br>Model Estimation</td><td><b>Sudah tersedia</b> ({{B:Model Estimation}}, {{B:Koreksi setelah}}): parameter per domain dari Geostatistik, Ordinary Kriging blok GC di dalam solid, koreksi hanya sekitar bor baru, blok tambahan, atribut baru, riwayat run, export .mdl / CSV.</td></tr>'
 + '<tr><td><b>Pembaruan 23 Okt</b></td><td><b>Sudah tersedia</b>: validasi data ({{B:Validasi data}}), RBF halus &amp; anti-spike, vein bercabang ({{B:Vein bercabang}}), struktur geologi ({{B:Struktur geologi}}), menu Map ({{B:Map:}}).</td></tr>'
 + '<tr><td><b>Versi 0.21</b></td><td><b>Sudah tersedia</b>: Sesar 3D ({{B:Sesar 3D}}) dan Geomodeller Stratified-Laterite ({{B:Geomodeller Stratified}}); menu Geological Modelling berganti nama menjadi Geomodeller Vein. <b>0.23.1</b>: Geostatistik per lapisan (ruang unfold), Simpan ke lapisan, validasi swath &amp; grade-tonase per lapisan.</td></tr>'
 + '<tr><td><b>Versi 0.24</b></td><td><b>Sudah tersedia</b>: data latihan baru &amp; {{B:Latihan terpandu}}, {{B:Klasifikasi}}, kerapatan bor per blok, {{B:Topografi &}}, {{B:Block model dari nol}}, {{B:Estimasi waste}} (vein &amp; laterit), {{B:Sub-blocking}}.</td></tr>'
 + '<tr><td><b>Tabel grade-tonnage</b><br>per domain &amp; per bench</td><td><b>Sudah tersedia</b> di <b>Reporting BM</b> ({{B:Klasifikasi}}): grup laporan dapat dipilih <b>Per bench (elevasi)</b> dengan tinggi bench bebas, <b>Per domain estimasi</b>, <b>Per domain vein</b>, atau <b>Per atribut kategori</b> (mis. <code>klasifikasi</code>), masing-masing per cut-off, lengkap dengan kurva grade-tonase dan ekspor CSV. Baris ini dulu tercantum sebagai usulan yang belum dikerjakan; itu keliru &mdash; fiturnya sudah ada sejak menu Reporting BM dibuat.</td></tr>'
 + '<tr><td><b>Usulan berikutnya</b><br>(belum disepakati)</td><td>Rekonsiliasi <b>kadar GC lama vs hasil estimasi baru per periode</b> di GC-Ex Drill Hole. Rekonsiliasi <i>as-mined</i> flitch per flitch sudah ada di GC-Ex Block Model; yang belum ada adalah perbandingan periodik (mis. per bulan / per kampanye bor) antara kadar GC yang dipakai saat penambangan dan model yang diestimasi ulang sesudahnya.</td></tr></table>'
 + '<h3>Ringkasan angka latihan (untuk mengecek hasil peserta)</h3>'
 + kv([('Import awal', f"{N['nHole']} hole, {fN(N['nAssay'])} assay, block model GC {fN(N['bx'])} blok"),
       ('Usulan otomatis', clean(N['auto']).split('. Periksa')[0]),
       ('Setelah koreksi', f"QV_Lensa2 {st['QV_Lensa2'][1]} hole / {st['QV_Lensa2'][3]} m / {st['QV_Lensa2'][4]} g/t; QV_Splay_HW {st['QV_Splay_HW'][1]} hole / {st['QV_Splay_HW'][3]} m / {st['QV_Splay_HW'][4]} g/t"),
       ('String', 'QV_Lensa2 22 string (11 section), QV_Splay_HW 4 string (2 section)'),
       ('Solid RBF', f"QV_Lensa2 {fN(su[1])} m&sup3; ({su[8]}/{su[8]} flag di dalam), QV_Splay_HW {fN(sh[1])} m&sup3;; setelah infill QV_Lensa2 {fN(SOLI['QV_Lensa2'][1])} m&sup3;"),
       ('Upsert', '4 hole baru, 359 interval; total 37 hole (+2 hole di latihan koreksi = 39)'),
       ('Statistik QV_Lensa2', f"{N['gsN']} komposit, mean {N['gsMean']} g/t, CV 1,24"),
       ('Variogram', 'nugget 65%, range major 108,5 m / semi 43 m / downhole 6 m'),
       ('Uji estimasi', f"{N['ok']:,} blok, mean {okm.get('Mean estimasi blok')} g/t"),
       ('Model Estimation run 1', f"QV_Lensa2 {u1[5]:,} blok (+{u1[6]} tambahan), mean {fN(u1[11],3)}; QV_Splay_HW {h1[6]} blok tambahan".replace(',', '.')),
       ('Model Estimation run 2', f"2 bor infill &rarr; QV_Lensa2 {u2[4]:,} dari {u2[3]:,} blok dikoreksi".replace(',', '.')),
       ('Export', clean(N['exportDb']))])
 + '<h3>Masalah yang sering muncul</h3><table class="t"><tr><th>Gejala</th><th>Penyebab / solusi</th></tr>'
 + '<tr><td>Tombol folder proyek tidak ada / gagal</td><td>Pilih folder di drive lokal / jaringan yang bisa ditulis; buka ulang GC-Ex bila izin folder ditolak.</td></tr>'
 + '<tr><td>Sayatan 2D kosong</td><td>Slab terlalu tipis atau posisi di luar data; tambah <b>Tebal</b> atau atur <b>Posisi</b> 0.</td></tr>'
 + '<tr><td>Klik flag tidak berpengaruh</td><td>Mode flag belum aktif (<b>&#9998; Flag</b>) atau domain aktif belum dipilih.</td></tr>'
 + '<tr><td>Tarik otomatis tidak membuat string</td><td>Section butuh &ge; 2 kontak flag dari domain aktif di dalam slab.</td></tr>'
 + '<tr><td>Solid gagal: &ldquo;titik HW / FW kurang&rdquo;</td><td>Butuh minimal 3 titik HW dan 3 titik FW (string tampil + kontak bor). Tarik string dulu atau tambah flag.</td></tr>'
 + '<tr><td>Solid tidak berubah setelah edit</td><td>Cek <b>Jalankan ulang otomatis</b> menyala, dan string yang diedit tidak disembunyikan.</td></tr>'
 + '<tr><td>&ldquo;Gagal menyimpan ke folder: file sedang dikunci program lain&rdquo;</td><td>File proyek sedang dipegang OneDrive (sinkronisasi), antivirus, Excel atau GC-Ex di jendela lain. GC-Ex sudah mencoba ulang 4 kali. Tunggu sinkronisasi OneDrive selesai / tutup program itu, lalu <b>Simpan sekarang</b> lagi. Pekerjaan tetap aman di browser.</td></tr>'
 + '<tr><td>Bar merah &ldquo;Galat JavaScript (di dalam Plotly)&rdquo;</td><td>Klik <b>Gambar ulang</b>. Bila berulang, kirim tangkapan layar bar (memuat jejak galat) dan langkah terakhir yang dilakukan.</td></tr>'
 + '<tr><td>Ringkasan solid: &ldquo;struktur diabaikan&rdquo;</td><td>Bidang struktur hampir tegak lurus bidang vein (bukan struktur sejajar vein); periksa dip / dip az atau sembunyikan file-nya.</td></tr>'
 + '<tr><td>Titik pick-up &ldquo;jauh dari data proyek&rdquo;</td><td>Sistem koordinat file berbeda dengan collar (mis. lokal vs UTM); samakan di software survei.</td></tr>'
 + '<tr><td>Klik di Sayatan 2D tidak tercatat</td><td>Kartu <b>Ringkasan</b> di kiri bawah menutupi area itu; ciutkan kartunya.</td></tr>'
 + '<tr><td>Solid cabang tidak menyambung ke induk</td><td>Pastikan <b>Sambung ke induk</b> menyala dan perbesar <b>Jarak sambung</b> sampai mencapai lubang yang sudah menembus vein gabungan.</td></tr>'
 + '<tr><td>Solid berupa beberapa bagian terpisah</td><td>Celah data searah strike lebih dari 2 &times; radius pengaruh. Perbesar radius pengaruh bila memang satu vein menerus.</td></tr>'
 + '<tr><td>Block model hilang setelah membuka proyek</td><td>File di <code>sumber/</code> dipindah / diganti; salin ulang lewat menu Proyek.</td></tr>'
 + '<tr><td>Model Estimation: domain tidak siap</td><td>Perlu solid (Geomodeller Vein &#9315;) dan parameter (Geostatistik &rarr; Uji estimasi &rarr; Simpan ke domain).</td></tr>'
 + '<tr><td>&ldquo;blok hasil tersimpan tidak ditemukan&rdquo;</td><td>Block model GC yang dibuka berbeda dari saat run (file sumber diganti). Jalankan ulang dengan opsi semua blok.</td></tr></table>')

# ================= URUTAN TERBIT =================
# Setiap bab harus muncul tepat satu kali di BAGIAN; sisanya ditempelkan di bagian terakhir agar
# bab baru tidak pernah hilang dari PDF, dengan peringatan di layar.
_sisa = dict(CH)
URUT = []          # [(nomor bab atau None, judul bagian, judul bab, isi)]
_no = [0]
def _ambil(awal):
    for t in list(_sisa):
        if t.startswith(awal.replace('&amp;', '&')) or t.startswith(awal):
            return t, _sisa.pop(t)
    return None, None   # bab opsional (mis. 'Latihan terpandu' yang butuh fig_update/)
for jt, ji, daftar in BAGIAN:
    URUT.append((None, jt, ji, None))
    for awal in daftar:
        t, b = _ambil(awal)
        if t is None: continue
        _no[0] += 1
        URUT.append((_no[0], jt, t, b))
if _sisa:
    print('PERINGATAN: bab belum masuk daftar BAGIAN, ditempel di bagian terakhir:', ', '.join(_sisa))
    for t in list(_sisa):
        _no[0] += 1
        URUT.append((_no[0], BAGIAN[-1][0], t, _sisa.pop(t)))
NOMOR = {t: n for n, _, t, b in URUT if b is not None}

# ================= HTML =================
toc = ''
for n, jt, t, b in URUT:
    if b is None:
        toc += '<li class="pt">%s</li>' % jt
    else:
        toc += '<li><span>%d. %s</span></li>' % (n, t)
body = ''
for n, jt, t, b in URUT:
    if b is None:
        body += '<section class="part"><div><div class="lbl">%s</div><p>%s</p></div></section>' % (jt, t)
    else:
        body += '<section class="ch"><div class="bag">%s</div><h2><span>%d</span>%s</h2>%s</section>' % (jt, n, t, b)
today = datetime.date.today()
bulan = ['Januari','Februari','Maret','April','Mei','Juni','Juli','Agustus','September','Oktober','November','Desember'][today.month-1]
HTML = f'''<!doctype html><html lang="id"><head><meta charset="utf-8"><title>Tutorial GC-Ex: Pemodelan Vein & Estimasi Block Model</title>
<style>
@page{{size:A4;margin:16mm 15mm 16mm 15mm}}
:root{{--nv:#1f2d6b;--ac:#f2c200;--mu:#5b6478;--ln:#d9dde6}}
*{{box-sizing:border-box}}
body{{font-family:Inter,'DejaVu Sans',sans-serif;font-size:10pt;line-height:1.5;color:#1b2033;margin:0}}
code{{font-family:'DejaVu Sans Mono',monospace;font-size:8.6pt;background:#f1f3f8;padding:0 3px;border-radius:3px}}
.cover{{height:265mm;display:flex;flex-direction:column;justify-content:space-between;page-break-after:always}}
.cover .top{{background:var(--nv);color:#fff;padding:22mm 14mm 16mm;border-bottom:4mm solid var(--ac)}}
.cover .logo{{font-size:30pt;font-weight:800;color:var(--ac);letter-spacing:.5px}}
.cover h1{{font-size:24pt;line-height:1.2;margin:8mm 0 3mm;font-weight:700}}
.cover .sub{{font-size:12pt;opacity:.85}}
.cover .img{{padding:0 6mm}}.cover .img img{{width:100%;border:1px solid var(--ln);border-radius:4px}}
.cover .meta{{color:var(--mu);font-size:9.5pt;padding:0 6mm}}
.toc{{page-break-after:always}}.toc h2{{font-size:16pt;color:var(--nv);border-bottom:2px solid var(--ac);padding-bottom:2mm}}
.toc ol{{list-style:none;padding:0;columns:1}}.toc li{{padding:1.6mm 0;border-bottom:1px dotted var(--ln);font-size:10.5pt}}
.ch{{page-break-before:always}}
.toc li.pt{{border:0;padding:4mm 0 1mm;font-size:11pt;font-weight:700;color:var(--nv);border-bottom:2px solid var(--ac)}}
.part{{page-break-before:always;height:200mm;display:flex;align-items:center;justify-content:center;text-align:center}}
.part .lbl{{font-size:20pt;font-weight:700;color:var(--nv);border-bottom:3mm solid var(--ac);display:inline-block;padding-bottom:3mm;margin-bottom:6mm}}
.part p{{max-width:120mm;margin:0 auto;color:var(--mu);font-size:10.5pt;line-height:1.6;text-align:left}}
.ch .bag{{font-size:8.2pt;letter-spacing:.6px;text-transform:uppercase;color:var(--mu);margin:0 0 1.5mm}}
h2{{font-size:16pt;color:var(--nv);margin:0 0 4mm;display:flex;align-items:center;gap:3mm;border-bottom:2px solid var(--ac);padding-bottom:2mm}}
h2 span{{background:var(--nv);color:var(--ac);font-size:13pt;min-width:9mm;height:9mm;border-radius:2mm;display:inline-flex;align-items:center;justify-content:center}}
h3{{font-size:11.5pt;color:var(--nv);margin:5mm 0 2mm}}
p{{margin:0 0 2.5mm}}
ol.st{{counter-reset:s;list-style:none;padding:0;margin:2mm 0 3mm}}
ol.st li{{counter-increment:s;position:relative;padding:1.2mm 0 1.2mm 9mm;break-inside:avoid}}
ol.st li:before{{content:counter(s);position:absolute;left:0;top:1.2mm;width:6mm;height:6mm;border-radius:50%;background:var(--ac);color:var(--nv);font-weight:700;font-size:9pt;display:flex;align-items:center;justify-content:center}}
figure{{margin:3mm 0 4mm;break-inside:avoid;text-align:center}}
figure img{{border:1px solid var(--ln);border-radius:3px;display:block;margin:0 auto}}
figcaption{{font-size:8.8pt;color:var(--mu);margin-top:1.5mm;text-align:left}}
figure.nar figcaption{{max-width:52%;margin-left:auto;margin-right:auto}}
.duo{{display:flex;gap:6mm;break-inside:avoid}}.duo>div{{flex:1}}.duo figure.nar figcaption{{max-width:none}}
.box{{border-left:1.2mm solid;padding:2mm 3mm;margin:3mm 0;border-radius:0 2mm 2mm 0;break-inside:avoid;font-size:9.4pt}}
.box b:first-child{{display:block;font-size:8.6pt;text-transform:uppercase;letter-spacing:.4px}}
.tip{{border-color:#2f9e44;background:#ebfbee}}.tip b:first-child{{color:#2b8a3e}}
.why{{border-color:#1c7ed6;background:#e7f5ff}}.why b:first-child{{color:#1864ab}}
.warn{{border-color:#e8590c;background:#fff4e6}}.warn b:first-child{{color:#d9480f}}
.dta{{border-color:#5f3dc4;background:#f3f0ff}}.dta b:first-child{{color:#5f3dc4}}
.dta .dtaf{{font-size:9pt;margin:1mm 0 0}}.dta table.kv{{margin:1.5mm 0 0}}.dta table.kv td:first-child{{width:30%}}
.tag{{font-size:8pt;font-weight:700;padding:0 2mm;border-radius:1mm;border:0}}
table{{border-collapse:collapse;width:100%;margin:2mm 0 3mm;font-size:9pt;break-inside:avoid}}
table.t th{{background:var(--nv);color:#fff;text-align:left;padding:1.5mm 2mm}}table.t td{{border-bottom:1px solid var(--ln);padding:1.5mm 2mm;vertical-align:top}}
table.kv td{{border-bottom:1px solid var(--ln);padding:1.3mm 2mm;vertical-align:top}}table.kv td:first-child{{width:34%;font-weight:600;color:var(--nv)}}
.flow{{display:grid;grid-template-columns:repeat(5,1fr);gap:2.5mm;margin:2mm 0 4mm}}
.flow div{{background:#f1f3f8;border:1px solid var(--ln);border-radius:2mm;padding:2mm;text-align:center;font-size:8.8pt;line-height:1.3}}
.flow b{{display:block;color:var(--nv);font-size:12pt}}
ul{{margin:1mm 0 3mm;padding-left:5mm}}li{{margin:.6mm 0}}
</style></head><body>
<div class="cover"><div class="top"><div class="logo">GC-Ex</div><h1>Tutorial Pemodelan Vein &amp;<br>Estimasi Block Model</h1>
<div class="sub">GC-Ex Drill Hole Ultimate {VDH} &middot; langkah demi langkah dengan data simulasi VeinA &amp; laterit nikel (Sesar 3D, Geomodeller Stratified-Laterite)</div></div>
<div class="img"><img src="{FIG['model_3d'][0]}"></div>
<div class="meta">Edisi {today.day} {bulan} {today.year} &middot; untuk pelatihan internal geologist grade control<br>
Data latihan sintetis &middot; semua gambar diambil dari satu kali jalannya latihan</div></div>
<div class="toc"><h2>Daftar isi</h2><ol>{toc}</ol></div>
{body}
</body></html>'''
def _bab(m):
    for t, n in NOMOR.items():
        if t.startswith(m.group(1)): return 'Bab %d' % n
    raise KeyError(m.group(1))
HTML = re.sub(r'\{\{?B:([^}]+)\}\}?', _bab, HTML)   # di dalam f-string {{B:..}} menjadi {B:..}
HTML = re.sub(r'\[\[(\w+)\]\]', lambda m: 'Gambar %d' % FNUM[m.group(1)], HTML)
hp = os.path.join(OUT, 'tutorial.html'); open(hp, 'w', encoding='utf-8').write(HTML)
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(); pg.goto('file://' + hp); pg.wait_for_timeout(800)
    pg.pdf(path=PDF, format='A4', print_background=True, display_header_footer=True,
           header_template='<div></div>',
           footer_template='<div style="font-size:7.5pt;color:#8a90a2;width:100%;padding:0 15mm;display:flex;justify-content:space-between;font-family:Inter,sans-serif"><span>GC-Ex &middot; Tutorial Pemodelan Vein &amp; Estimasi Block Model</span><span><span class="pageNumber"></span> / <span class="totalPages"></span></span></div>',
           margin={'top': '14mm', 'bottom': '16mm', 'left': '15mm', 'right': '15mm'})
    b.close()
print('PDF', PDF, os.path.getsize(PDF) // 1024, 'KB', 'gambar', fig_no[0])
