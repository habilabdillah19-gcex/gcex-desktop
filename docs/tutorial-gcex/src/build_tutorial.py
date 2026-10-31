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
        "Tutorial yang TIDAK memerlukan tangkapan layar: build_tutorial_024.py" % IMG)

N = json.load(open(os.path.join(IMG, 'notes.json'), encoding='utf-8'))
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
def kv(rows): return '<table class="kv">' + ''.join('<tr><td>%s</td><td>%s</td></tr>' % r for r in rows) + '</table>'

st = {r[0]: r for r in (json.loads(N['stat']) if isinstance(N['stat'], str) else N['stat'])}
okm = dict(l.split('\t') for l in N['okMsg'].split('\n') if '\t' in l)
CH = []
def ch(title, body, key=None): CH.append((title, body))

# ================= ISI =================
ch('Tentang tutorial ini', f'''
<p>Tutorial ini mengajarkan alur kerja <b>pemodelan vein dan estimasi block model</b> di <b>GC-Ex Drillhole</b>
(aplikasi desktop <b>GC-Ex Drill Hole Ultimate 0.23.1</b>). Setiap langkah dipraktikkan dengan <b>data simulasi</b> yang ikut
dibagikan, dan semua gambar adalah tangkapan layar dari satu kali jalannya latihan tersebut. Jika rekan Anda mengikuti langkah
yang sama, angka yang muncul di layarnya akan sama dengan angka di buku ini.</p>
<h3>Alur kerja</h3>
<div class="flow">
<div><b>1</b>Folder proyek<br>&amp; import</div><div><b>2</b>Sayatan<br>&amp; geologi</div><div><b>3</b>Domain<br>vein</div>
<div><b>4</b>Flag interval<br>bor</div><div><b>5</b>String HW / FW<br>&amp; solid RBF</div><div><b>6</b>Wireframe<br>Leapfrog</div>
<div><b>7</b>Upsert bor<br>infill</div><div><b>8</b>Statistik<br>&amp; variogram</div><div><b>9</b>KNA &amp; Model<br>Estimation</div><div><b>10</b>Export<br>&amp; backup</div>
</div>
<h3>Yang dibutuhkan</h3>
<ul>
<li>Komputer Windows 10 / 11 64-bit dengan <b>GC-Ex Drill Hole Ultimate</b> terpasang (installer <code>GC-Ex-Drillhole-Setup-0.23.1.exe</code>) dan lisensi aktif.</li>
<li>Aplikasi berjalan sepenuhnya offline; tidak perlu browser atau file Plotly terpisah.</li>
<li>Folder <code>data_simulasi</code> dari paket tutorial ini.</li>
<li>Satu folder kosong untuk proyek latihan, misalnya <code>Proyek_Tutorial_VeinA</code> (boleh di OneDrive / SharePoint / drive jaringan).</li>
</ul>
<h3>Cara membaca</h3>
<p>Langkah bernomor = yang harus diklik / diisi. Kotak <span class="tag tip">Tips</span> berisi jalan pintas,
<span class="tag why">Mengapa?</span> menjelaskan alasan geologinya, dan <span class="tag warn">Perhatian</span> berisi hal yang sering keliru.
Nama tombol dan menu ditulis <b>tebal</b> persis seperti di layar.</p>
''' + warn('Gambar diambil dari GC-Ex Drill Hole Ultimate 0.23.1 dengan kartu grafis perangkat lunak; di komputer Anda tampilan 3D lebih halus dan bisa diputar. Posisi, warna dan angka sama.', 'Catatan gambar'))

ch('Data simulasi', f'''
<p>Data ini <b>sintetis</b> (bukan data perusahaan), dibuat agar meniru kasus vein emas epitermal sempit berbentuk sigmoidal.</p>
<table class="t"><tr><th>File</th><th>Isi</th></tr>
<tr><td>SIM_collar.csv, SIM_survey.csv, SIM_assay.csv, SIM_geologi.csv</td><td>33 lubang bor di 11 section (jarak 20 m) tegak lurus strike, 3 lubang per section, sampel 1 m. Unsur Au, Ag, SxS; geologi Lith / Alt / Ox.</td></tr>
<tr><td>SIM_upsert_*.csv</td><td>7 lubang infill (SIM-INF-*) untuk latihan <b>upsert</b>.</td></tr>
<tr><td>SIM_upsert2_*.csv</td><td>7 lubang infill tahap 2 untuk latihan <b>koreksi Model Estimation</b>.</td></tr>
<tr><td>SIM_topo_xyz.csv, SIM_topo_xyz_nov.csv</td><td>Topografi titik XYZ grid 5 m; versi bulan berikutnya untuk latihan Data Spasial.</td></tr>
<tr><td>SIM_BM_GC.csv</td><td>Block model GC kosong 10 &times; 10 &times; 5 m ({N['bx']:,} blok) di sekitar array vein.</td></tr>
<tr><td>QV_Lensa2_Leapfrog.obj</td><td>Contoh wireframe lensa 2 hasil Leapfrog (tertutup, 21.596 segitiga).</td></tr>
<tr><td>SIM_struktur.csv</td><td>96 titik struktur (Easting, Northing, RL, Jenis, Dip, Dip_Azimuth, Plunge, Trend, Catatan): kontak vein di singkapan dan bidang sesar.</td></tr>
<tr><td>SIM_pickup_survey.csv</td><td>142 titik pick-up survei (Kode, Easting, Northing, RL, Tebal_m, Keterangan): singkapan vein tiap lensa.</td></tr>
<tr><td>SIM_split_*.csv</td><td>Proyek terpisah vein bercabang (latihan domain induk).</td></tr>
<tr><td>SIM_rusak_collar.csv, SIM_rusak_assay.csv</td><td>Database dengan kesalahan sengaja untuk latihan validasi.</td></tr>
<tr><td>SIM_LAT_collar / survey / assay / geologi.csv</td><td>Proyek terpisah <b>laterit nikel</b>: {NL['nHole']} bor vertikal grid 25 m, sampel 1 m ({NL['nAssay']:,} sampel), unsur Ni, Co, Fe, MgO, SiO2 (%), kolom <code>Zona</code>: TS (tanah penutup), LIM, SAP, BRK.</td></tr>
<tr><td>SIM_LAT_topo_xyz.csv, SIM_LAT_BM_GC.csv</td><td>Topografi grid 10 m dan block model GC 12,5 &times; 12,5 &times; 1 m ({NL['nBlok']:,} blok) untuk latihan {{B:Geomodeller Stratified}}.</td></tr>
<tr><td>SIM_LAT_sesar.csv</td><td>Jejak sesar F1 (dua titik X, Y) beserta dip 65&deg; ke 100&deg;, normal, offset 12 m, post-mineralisasi, untuk latihan {{B:Sesar 3D}}.</td></tr></table>
<h3>Geometri yang perlu diingat</h3>
<p>Endapannya adalah <b>array 4 lensa vein en-echelon</b> (QV_Lensa1 s/d QV_Lensa4) ditambah satu splay di sisi hanging wall. Tutorial ini menelusuri <b>lensa 2 beserta splay-nya</b>; lensa lain dikerjakan dengan cara yang persis sama. Model geologi lengkapnya, beserta kunci jawabannya, ada di <i>Tutorial Tambahan GC-Ex 0.24</i> dan <code>data/JAWABAN_MODEL.txt</code>.</p>
{kv([('Vein utama (QV_Lensa2)','strike 045&deg;, dip 70&deg; ke 135&deg; (bidang acuan; permukaannya sigmoidal sehingga bidang rata-rata data &plusmn;66&deg;), tebal median 1 m dan membengkak sampai &plusmn;5 m di zona dilatan'),
     ('Ore shoot','pitch 55&deg; dari garis strike di dalam bidang vein &mdash; mengontrol tebal DAN kadar sekaligus'),
     ('Splay hangingwall (QV_Splay_HW)','sejajar, &plusmn;26 m di sisi hanging wall, lebih tipis dan lebih rendah kadar'),
     ('Arah bor','azimuth 315&deg;, dip &minus;55&deg; s/d &minus;65&deg; (dari sisi hanging wall)'),
     ('Koordinat','sekitar E 505.000, N 9.012.000; elevasi 150&ndash;330 m, paleo-muka air tanah RL 250 m (zona bonanza)'),
     ('Dip survey','negatif = ke bawah')])}
''' + why('Karena bor datang dari sisi hanging wall, lubang yang cukup panjang akan menembus <b>QV_Splay_HW dulu</b> (lebih dangkal), baru <b>QV_Lensa2</b>. Ini dipakai pada {{B:Koreksi flag}} untuk latihan koreksi flag.'))

ch('Membuat folder proyek & import data', steps(
 'Buka <b>GC-Ex Drill Hole Ultimate</b> dari menu Start. Halaman muka <b>Import data</b> tampil penuh ([[jendela_awal]]); isi <b>Nama project site</b> bila perlu (tampil di bilah atas, disimpan per proyek).',
 'Pada kartu <b>Folder proyek</b>, klik <b>Buka / pilih folder proyek</b> lalu pilih folder kosong <code>Proyek_Tutorial_VeinA</code>. Izinkan akses ketika browser bertanya (<i>Lihat file</i> dan <i>Simpan perubahan</i>).',
 'Pada <b>&#9312; Database drillhole</b>, klik <b>Import Collar</b>, <b>Import Survey</b>, <b>Import Assay</b>, <b>Import Geologi</b> dan pilih empat file SIM_*.csv yang sesuai.',
 'Isi <b>Nama dataset</b>: <code>VeinA_Simulasi</code>. Periksa ringkasan di bawahnya ([[import_database]]): harus tertulis <b>33 collar &middot; 66 survey (33 hole) &middot; 2863 interval assay &middot; 2863 interval geologi</b>, unsur <b>Au, Ag, SxS</b>.',
 'Gulir ke <b>&#9313; Data spasial &amp; block model</b>: pada <b>Topografi</b> pilih <code>SIM_topo_xyz.csv</code>; pada <b>Block model</b> pilih <code>SIM_BM_GC.csv</code>.',
 'Klik <b>Tampilkan viewer &rarr;</b>. Viewer 3D terbuka ([[viewer_3d]]) dan muncul tawaran menyalin file block model ke folder proyek &mdash; jawab <b>OK</b>.')
 + fig('jendela_awal', 'Jendela awal. Kartu <b>Folder proyek</b> paling atas: proyek disimpan di folder pilihan Anda, GC-Ex hanya membuka &amp; mengolah.')
 + fig('import_database', 'Empat file database sudah dipilih. Ringkasan hijau di bawah memastikan jumlah collar, survey, assay dan geologi terbaca benar.')
 + why('Dengan folder proyek, semua pekerjaan (flag, string, hasil estimasi) tersimpan otomatis ke folder 3 detik setelah ada perubahan, lengkap dengan backup berversi. Rekan lain cukup membuka folder yang sama.')
 + fig('viewer_3d', f"Viewer 3D setelah import: {N['nHole']} lubang bor, {N['nAssay']:,} interval assay diwarnai kelas Au. Pesan di bawah: <i>SIM_BM_GC.csv tersalin ke folder proyek sumber/</i>.")
 + tip('Jika ringkasan menulis <i>hole di assay tidak ada di collar</i>, buka <b>Pemetaan kolom &amp; unsur</b> dan cek kolom Hole ID.'))

VL = N.get('valid', []) if isinstance(N.get('valid', []), list) else json.loads(N['valid'])
ch('Validasi data bor', '<p>Saat file database dipilih, GC-Ex memeriksa datanya dan menampilkan ringkasan <b>Validasi</b> di bawah ringkasan import ([[validasi]]). Klik ringkasan itu untuk melihat rinciannya, dan <b>Unduh laporan validasi (CSV)</b> untuk daftar per hole. GC-Ex <b>tidak mengubah data mentah</b>: perbaiki di database sumber, lalu import ulang atau upsert.</p>'
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

ch('Mengenal tampilan', '<p>Menu utama ada di <b>rel kiri</b>, diurutkan mengikuti alur kerja: <b>Data &rarr; Geologi &rarr; Sayatan &rarr; Geomodeller Vein &rarr; Block Model &rarr; Model Estimation</b>. Di bawah garis pemisah ada menu pendukung: Data Spasial, Data Referensi, Digitasi, Plan Bor, Warna, Overlay, Tampilan. Tombol di <b>bar atas</b>: Proyek, arah pandang (Top / Front / Side / Iso / <b>&perp; Tegak lurus</b> sayatan), <b>Sayatan 2D</b>, <b>&#9660; Mundur &middot; posisi &middot; Maju &#9650;</b> (pindah section tanpa membuka menu Sayatan), <b>Layer</b> (ikon tumpukan; juga untuk menyembunyikan drillhole), PNG, dan <b>Geostatistik</b>.</p>'
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

ch('Sayatan & penampang 2D', steps(
 'Klik <b>Sayatan</b>. Pilih <b>Arah potongan</b>: <i>Garis manual (vertikal / miring)</i>, lalu <b>Gambar garis sayatan</b> dan klik dua titik di peta, tegak lurus strike vein (garis berarah 135&deg;).',
 '<b>Dip bidang</b> 90 (tegak), <b>Tebal</b> 12 m, aktifkan <b>Potong data (hanya dalam slab)</b>. [[sayatan_3d]] memperlihatkan 3 lubang section tengah.',
 'Klik <b>Sayatan 2D</b> di bar atas (atau biarkan <b>Buka Sayatan 2D setelah menggambar</b> aktif). Lihat [[penampang_2d]].',
 'Pindah section dengan <b>&#9660; Mundur</b> / <b>&#9650; Maju</b> (di menu Sayatan atau di bar atas, angka di tengah = posisi saat ini) atau isi <b>Posisi</b> (offset tegak lurus garis, meter).')
 + fig('sayatan_3d', 'Sayatan tegak tebal 12 m lewat tengah vein: hanya data di dalam slab yang tampil.')
 + fig('penampang_2d', 'Sayatan 2D section yang sama. Label BL 315&deg; / TG 135&deg; menunjukkan arah pandang; sumbu bawah = jarak sepanjang garis, sumbu kiri = elevasi.')
 + why('Flag dan string vein dikerjakan di penampang 2D yang tegak lurus strike, karena di situ ketebalan sebenarnya dan posisi HW / FW terlihat paling jelas.'))

ch('Geologi: pita litologi', steps(
 'Klik <b>Geologi</b>. <b>Atribut geologi</b>: <code>Lith</code>.',
 'Aktifkan <b>Pita hatch (2D)</b>, <b>Lebar</b> 2. Legenda memperlihatkan AND (andesit) dan QV (urat kuarsa) dengan hatch yang bisa diubah.')
 + fig('geologi_lith', 'Pita litologi di samping trace bor: interval QV (oranye arsir) bertepatan dengan kadar tinggi &mdash; acuan pertama untuk flag domain.')
 + tip('Bagian <b>Domain untuk analisis</b> di menu ini nanti dipakai untuk memilih domain vein sebelum statistik dan estimasi ({{B:Filter domain}}).'))

ch('Geomodeller Vein: membuat domain vein', steps(
 'Klik <b>Geomodeller Vein</b> di rel kiri.',
 'Di Project Tree, klik <b>+ Tambah domain&hellip;</b> di bawah <b>Geomodeller Vein</b>, ketik <code>QV_Lensa2</code>, OK. Ulangi untuk <code>QV_Splay_HW</code>.',
 'Klik nama domain di Project Tree untuk menjadikannya <b>domain aktif</b> (bertanda <i>AKTIF</i>). Panel Properti hanya menampilkan domain aktif: warna bisa diubah dengan klik kotak warna; centang kanan = tampil / sembunyi. Flag, String, Solid dan Struktur selalu bekerja pada domain aktif.')
 + fig2('gm_domain', 'Dua domain vein dibuat. Di bawah nama: jumlah hole &middot; run &middot; panjang &middot; kadar rata-rata.',
        'gm_usulan_param', 'Bagian <b>Usulan otomatis dari kadar</b> dibuka dengan parameter latihan.')
 + why('Nama domain bebas per proyek. Nama ini dipakai juga untuk string kontrol (<code>QV_Lensa2_HW_01</code>), kolom <code>Ore_Domain</code> saat export, dan filter estimasi &mdash; jadi pilih nama yang baku di tim.'))

ch('Flag otomatis dari kadar', steps(
 'Pastikan domain aktif = <b>QV_Lensa2</b>.',
 'Buka <b>&#9660; Usulan otomatis dari kadar</b> dan isi: <b>Unsur</b> Au, <b>Cut-off</b> 0.5, <b>Panjang min.</b> 1 m, <b>Dilusi internal maks.</b> 1 m, <b>Lingkup</b> Semua hole, aktifkan <b>Jangan timpa flag lain</b> ([[gm_usulan_param]]).',
 'Klik <b>Usulkan ke domain aktif</b>.',
 f"Hasil ([[gm_usulan_hasil]]): <b>{clean(N['auto']).split('. Periksa')[0]}</b>.")
 + fig('gm_usulan_hasil', 'Interval hasil usulan diberi pita warna domain QV_Lensa2 di penampang 2D. Angka di samping trace = kadar Au.')
 + why('Usulan menggabungkan sampel &ge; cut-off yang dipisah waste &le; dilusi maksimum, dan membuang run lebih pendek dari panjang minimum. Hasilnya <b>hanya usulan</b>: geologist tetap wajib memeriksa tiap section.')
 + warn(f"Usulan memasukkan semua run kadar ke domain aktif. Pada data ini ada <b>{N['holeDuaVein']} hole</b> yang menembus dua vein (contoh <b>{N['contohHole']}</b>), sehingga intercept dangkal (QV_Splay_HW) ikut masuk QV_Lensa2. Ini dikoreksi pada bab berikut."))

ch('Koreksi flag secara interaktif', steps(
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

ch('String kontrol hanging wall / footwall', '<p>String kontrol adalah garis batas vein per section: <b>HW</b> (hanging wall, garis penuh) dan <b>FW</b> (footwall, garis putus-putus). String ini terpisah dari menu Digitasi dan akan dipakai, diperbaiki dan ditambah setiap ada bor baru.</p>'
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
def fN(v, d=0): return ('{:,.%df}' % d).format(v).replace(',', 'X').replace('.', ',').replace('X', '.')
su, sh = SOL['QV_Lensa2'], SOL['QV_Splay_HW']
ch('Membangun solid vein (RBF)', '<p>Dari string kontrol dan titik kontak bor, GC-Ex membangun <b>permukaan hanging wall</b> dan <b>permukaan footwall</b> secara terpisah (interpolasi RBF <i>thin-plate spline</i>, mengikuti bentuk sigmoidal), lalu <b>solid vein</b> di antara keduanya. Model <b>dibangun ulang otomatis</b> setiap string atau flag berubah.</p>'
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
   'Satu domain = satu file; beberapa domain dikemas dalam satu ZIP. File STR+DTM bisa dibaca ulang di menu <b>Data Referensi</b>.'), 'solid')

ch('Memakai wireframe dari Leapfrog', steps(
 'Klik <b>Data Referensi</b> &rarr; <b>Import model vein / solid</b> dan pilih <code>QV_Lensa2_Leapfrog.obj</code> (format lain: Leapfrog .msh, Surpac .dtm/.str, DXF 3DFACE).',
 f"Wireframe tampil di 3D ([[wireframe_import]]): <b>{N['wf']}</b>.",
 'Kembali ke <b>Geomodeller Vein</b>, buka bagian <b>Wireframe luar</b>. Pilih wireframe dan domain tujuan, lalu klik <b>&#9986; Iris jadi string HW/FW (section ini)</b> atau <b>&#9986; Semua section</b>. Loop irisan dipecah otomatis menjadi string HW dan FW ([[wireframe_iris]]).',
 f"Klik <b>&#9873; Flag interval bor di dalam wireframe</b>: {clean(N['wfFlag'])}",
 f"Karena flag QV_Lensa2 bertambah, solid QV_Lensa2 ikut <b>dibangun ulang otomatis</b> ({clean(N['solidWf'])}).")
 + fig('wireframe_import', 'Wireframe QV_Lensa2 hasil Leapfrog di atas data bor. Slider di daftar model mengatur transparansi.')
 + fig('wireframe_iris', 'Irisan wireframe pada section &minus;20 m (hijau tua) berdampingan dengan string QV_Lensa2 hasil flag. Keduanya bisa dibandingkan dan diedit.')
 + tip('Setelah selesai, sembunyikan wireframe besar lewat panel <b>Layer</b> (Wireframe / solid) agar tidak menutupi bor.')
 + warn('Pengecekan <i>di dalam wireframe</i> memakai sinar vertikal. Wireframe harus tertutup; jika ada tepi terbuka GC-Ex memberi peringatan dan hasil flag perlu diperiksa.'))

ch('Menambah bor infill dengan upsert', '<p><b>Upsert</b> = tambah atau perbarui. Collar dicocokkan per HoleID (baru ditambah, lama diperbarui). Survey, assay dan geologi <b>diganti per hole</b> untuk hole yang ada di file baru; hole lain tidak disentuh.</p>'
 + steps('Menu <b>Data</b> &rarr; <b>&#8645; Tambah / perbarui data bor (upsert)</b>.',
   'Pilih empat file <code>SIM_upsert_*.csv</code>. Baca pratinjau di atas ([[upsert_pratinjau]]) sebelum melanjutkan.',
   'Klik tombol upsert. Folder proyek otomatis membuat backup <i>sebelum upsert</i>.',
   f"Pesan hasil ([[upsert_hasil]]): <b>{clean(N['upsToast'])}</b>")
 + fig('upsert_pratinjau', 'Pratinjau upsert: 4 collar baru, 4 hole diganti untuk survey/assay/geologi, 0 hole lama terpengaruh.')
 + fig('upsert_hasil', 'Sesudah upsert: 37 lubang. Tombol <b>&#8630; Batalkan upsert terakhir</b> muncul di menu Data. Block model GC tetap termuat.')
 + '<h3>Memperbarui flag dan string</h3>' + steps(
   f"Domain aktif QV_Lensa2, <b>Lingkup</b> semua hole, <b>Jangan timpa flag lain</b> aktif, lalu <b>Usulkan ke domain aktif</b>: {clean(N['autoInfill']).split('. Periksa')[0]}.",
   'Koreksi intercept QV_Splay_HW pada hole infill seperti {{B:Koreksi flag}}.',
   f"Klik <b>&#10148;&#10148; Semua section</b> lagi: <b>{clean(N['strUpd'])}</b>")
 + fig('upsert_string_baru', f"Section tengah setelah infill: string QV_Lensa2 diperbarui melewati kontak bor baru dan solid ikut diperbarui otomatis ({clean(N['solidInfillMsg'])}): volume QV_Lensa2 {fN(SOLI['QV_Lensa2'][1])} m&sup3;, {SOLI['QV_Lensa2'][8]}/{SOLI['QV_Lensa2'][8]} interval flag di dalam solid.")
 + why('String yang pernah diedit manual dilewati (tidak ditimpa) supaya interpretasi geologist tidak hilang. Hapus tanda edit atau edit lagi secara manual bila memang perlu diubah.'))

ch('Filter domain & statistik', steps(
 'Menu <b>Geologi</b> &rarr; <b>Domain untuk analisis</b>: pilih <b>Domain vein (Geomodeller Vein)</b>, lalu centang <b>QV_Lensa2</b> saja ([[domain_filter]]).',
 'Atur sayatan <b>sejajar bidang vein</b>: strike 45&deg;, dip 70&deg;, tebal slab 40 m (&plusmn;20 m), posisi 0.',
 'Klik <b>Geostatistik</b> di bar atas lalu <b>&#8635; Hitung</b>. Tab <b>Statistik</b> ([[geostat_statistik]]).')
 + fig2('domain_filter', 'Filter <b>Domain vein</b>. Filter berlaku untuk tampilan assay, ringkasan, geostatistik, KNA dan estimasi OK.',
        'export_database', 'Menu Data setelah <b>Export database (CSV)</b> ({{B:Export}}).')
 + fig('geostat_statistik', f"Statistik komposit 1 m domain QV_Lensa2: n = {N['gsN']}, rata-rata {N['gsMean']} g/t, declustered 2,075 g/t, CV 1,24, maksimum 17,47 g/t.")
 + why('Rata-rata <i>declustered</i> lebih rendah dari rata-rata biasa karena sampel kadar tinggi di ore shoot dibor lebih rapat. Gunakan histogram skala log dan persentil P95&ndash;P99 untuk memutuskan perlu tidaknya top-cut.'))

ch('Domain aktif di Geostatistik & Model Estimation (versi 0.20)', '<p>Mulai GC-Ex Drill Hole Ultimate <b>0.20</b>, satu <b>domain aktif</b> dipakai bersama oleh Geomodeller Vein, Geostatistik dan Model Estimation. Domain bisa diaktifkan dari node domain di bawah <b>Geomodeller Vein</b>, <b>Geostatistik</b> atau <b>Model Estimation</b> di Project Tree, sehingga tidak perlu kembali ke Geomodeller Vein.</p>'
 + steps('Project Tree &rarr; <b>Geostatistik</b> &rarr; klik <b>QV_Lensa2</b>. Panel Geostatistik terbuka dengan bilah <b>Domain: QV_Lensa2</b> &mdash; komposit hanya dari interval bor yang di-flag ke QV_Lensa2 (beserta cabangnya; untuk selubung: interval halo) ([[dom20_gs]]).',
   'Untuk melihat semua sampel (perilaku lama), pilih <b>Semua data (tanpa filter domain)</b> di node Geostatistik atau di bilah Domain.',
   'Setelah fitting, <b>Simpan ke domain</b> otomatis memilih domain aktif.',
   'Project Tree &rarr; <b>Model Estimation</b> &rarr; klik domain: domain itu menjadi aktif dan parameternya tampil di Properti ([[dom20_me]]). Centang di node domain = ikut <b>Jalankan semua domain</b>.',
   'Bagian Jalankan: <b>&#9654; Jalankan domain aktif</b> hanya mengestimasi domain aktif; <b>&#9654; Jalankan semua domain</b> mengestimasi semua domain yang dicentang. Keduanya juga ada di menu &hellip; node Model Estimation.')
 + fig2('dom20_gs', 'Geostatistik dengan <b>domain aktif</b> QV_Lensa2: hanya sampel di dalam domain.', 'dom20_me', 'Model Estimation: Properti menampilkan domain aktif yang dipilih dari Project Tree.')
 + tip('Filter <b>Domain untuk analisis</b> di menu Geologi ({{B:Filter domain}}) tetap berlaku di atas domain aktif. Bila filter itu tidak dipakai, domain aktif sudah cukup untuk memisahkan sampel per domain.'))

ch('Variogram, anisotropi & model', steps(
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
ch('Kriging Neighbourhood Analysis (KNA)', steps(
 'Tab <b>KNA</b>. Isi ukuran blok pada tab Uji estimasi dulu: 5 &times; 5 &times; 2,5 m.',
 'Biarkan <b>Jumlah blok uji</b> 10, <b>Maks sampel diuji</b> 6, 8, 12, 16, 20, 24, 32, <b>Faktor radius</b> 0,75 / 1 / 1,5 / 2. Klik <b>Jalankan KNA</b>.',
 f'Baca rekomendasi ([[geostat_kna]]) lalu klik <b>Terapkan ke Pass 1</b>. Pada latihan ini Pass 1 menjadi radius &times;{kp[0]}, {kp[1]}&ndash;{kp[2]} sampel, maks {kp[3]} per hole.')
 + fig('geostat_kna', 'Hasil KNA: grafik Slope of Regression dan Kriging Efficiency terhadap jumlah sampel untuk tiap faktor radius.')
 + kv([('Rekomendasi', clean(N['kna']).split('Patokan')[0]), ('Patokan umum', 'SoR &ge; 0,9 dan KE &ge; 0,5 untuk blok <i>measured</i>; menambah sampel setelah SoR mendatar hanya menambah smoothing.')]))

ch('Uji estimasi & simpan parameter ke domain', '<p>Tab <b>Uji estimasi</b> di Geostatistik adalah estimasi cepat pada grid blok sendiri untuk <b>menilai parameter</b> (bukan block model produksi). Bila parameter sudah dirasa tepat, parameter itu <b>disimpan ke domain</b> dan dipakai menu <b>Model Estimation</b> ({{B:Model Estimation}}).</p>'
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

ch('Model Estimation: estimasi block model GC', '<p>Menu <b>Model Estimation</b> (rel kiri, di bawah Geomodeller Vein) mengestimasi <b>block model GC</b> per domain vein. Aturannya:</p><ul>'
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
       ('QV_Splay_HW', f"tidak ada blok GC di dalam solid &rarr; {h1[6]} blok tambahan, rata-rata estimasi {fN(h1[11],3)} g/t"),
       ('Block model', f"{MEB[0]:,} blok GC + {MEB[1]-MEB[0]} blok tambahan = {MEB[1]:,} blok".replace(',', '.')),
       ('Waktu', f"{fN(u1[17]/1000,1)} detik")])
 + fig('me_bm3d', 'Menu Block Model setelah <b>Tampilkan di Block Model</b>: diwarnai <code>au_final</code>, hanya blok terestimasi (filter <code>est_type &ge; 1</code>).')
 + fig('me_bm2d', 'Sayatan 2D tebal 2,5 m: blok terestimasi mengikuti solid QV_Lensa2 dan QV_Splay_HW di antara string HW / FW.')
 + '<h3>Atribut baru di block model</h3>' + kv([('au_est','kadar hasil estimasi (&minus;99 bila tidak diestimasi)'),('au_final','au_est bila ada, selain itu kadar GC asli &mdash; dipakai untuk perencanaan'),('domain_est','nama domain vein'),('est_pass / est_nsamp','pass yang berhasil, jumlah sampel'),('est_sor / est_ke / est_kv','slope of regression, kriging efficiency, kriging variance'),('est_type','1 = koreksi blok GC, 2 = blok tambahan'),('est_date / est_run','tanggal (yyyymmdd) dan nomor run terakhir yang mengestimasi blok itu')])
 + why('Atribut GC asli dibiarkan utuh supaya perubahan bisa diaudit dan dibandingkan (rekonsiliasi). Keputusan memakai nilai baru ada di atribut <code>au_final</code>.')
 + warn('Rata-rata estimasi bisa berbeda cukup jauh dari GC lama di zona vein (di sini GC lama jauh lebih rendah karena blok GC 2,5 m mencampur vein dengan waste). Periksa swath plot dan penampang sebelum memakai hasil.'), 'me')

ch('Koreksi setelah bor baru', '<p>Inilah pemakaian sehari-hari: setiap ada bor baru, GC-Ex hanya mengestimasi ulang blok yang <b>lingkungan kriging-nya</b> berubah, yaitu blok yang memakai komposit dari hole baru / berubah, ditambah blok yang baru masuk solid. Blok lain tetap nilai run sebelumnya.</p>'
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
ch('Vein bercabang: domain induk', '<p>Vein yang <b>bercabang</b> (split / splay) tidak bisa digambarkan dengan satu permukaan HW dan satu FW. Di GC-Ex tiap cabang dibuat sebagai <b>domain sendiri</b> dengan string HW / FW sendiri, lalu dijadikan <b>cabang dari domain induk</b>. Solidnya digabung, dan Model Estimation memperlakukan induk + cabang sebagai <b>satu domain</b> &mdash; mirip seam split pada batubara.</p>'
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
ch('Struktur geologi (dip / dip azimuth)', '<p>Arah dip vein bisa berubah: misalnya ke timur di elevasi 300 dan ke barat di elevasi 100. Titik struktur (dip / dip azimuth) memberi tahu RBF arah kemiringan setempat. Ada tiga sumber: <b>flag struktur</b> di Sayatan 2D per domain, <b>file CSV</b>, dan <b>titik manual</b> di 3D.</p>'
 + '<h3>Import file struktur</h3>' + steps('Menu <b>Data Referensi</b> &rarr; bagian <b>Struktur geologi</b> &rarr; <b>&#8679; Import CSV struktur</b>, pilih <code>SIM_struktur.csv</code> ([[struktur_panel]]).',
   'Format kolom: <code>No, X, Y, Z, Dip, Dip_Azimuth, Keterangan</code> (pemisah koma / titik koma / tab; header fleksibel; Z kosong = diambil dari topografi).',
   'Daftar sumber menampilkan file beserta jumlah titik. Centang untuk menampilkan / menyembunyikan, <b>&times;</b> untuk menghapus file.',
   'Klik baris titik untuk memilihnya; nilai X, Y, Z, Dip, Dip az, No dan Keterangan bisa diubah langsung.')
 + fig('struktur_panel', f"Panel Struktur geologi: {N['strN']} titik dari SIM_struktur.csv; titik pertama terpilih dan bisa diedit.", '78%')
 + fig('struktur_3d', 'Tampilan 3D: tiap struktur berupa cakram berorientasi (hijau = dari file) dengan garis strike (hitam) dan tanda arah dip: deretan di singkapan, dua di kedalaman (core oriented), dan kekar. Item Layer <b>Struktur geologi</b> menyalakan / menyembunyikannya.')
 + '<h3>Flag struktur di Sayatan 2D</h3>' + steps('Geomodeller Vein &rarr; bagian <b>&#9316; Flag struktur</b>. Isi <b>Dip</b> 65, <b>Dip az</b> 135 dan keterangan.',
   'Klik <b>&#9998; Flag struktur</b>, lalu klik di Sayatan 2D pada posisi pengukuran ([[struktur_flag]]). Titik ditaruh di bidang sayatan untuk <b>domain aktif</b>.',
   'Klik berikutnya <b>memakai nilai yang sama</b> sampai Anda mengubahnya; nomor bertambah otomatis. Garis pendek di penampang = dip semu (perpotongan bidang struktur dengan bidang sayatan). <b>Esc</b> = selesai.')
 + fig('struktur_flag', 'Flag struktur di Sayatan 2D: dua titik 65/135 untuk QV_Lensa2 (oranye) dan dua struktur dari file di dekat sayatan (hijau), masing-masing tampil sebagai garis dip semu berlabel dip/az.')
 + '<h3>Titik manual di 3D</h3>' + steps('Data Referensi &rarr; Struktur geologi &rarr; <b>+ Titik (klik di 3D)</b>. Arahkan kursor ke bor, solid atau topografi sampai info muncul, lalu klik. Atau <b>+ Titik di tengah area</b>.',
   'Geser titik terpilih dengan tombol <b>Maju / Mundur, Kiri / Kanan</b> (relatif arah pandang 3D; di Sayatan 2D relatif bidang sayatan) dan <b>Z + / Z &minus;</b>, dengan langkah yang diatur ([[struktur_manual]]).')
 + fig('struktur_manual', 'Editor titik terpilih: koordinat, dip / dip az, keterangan, dan tombol geser.', '78%')
 + '<h3>Pengaruh pada solid RBF</h3>'
 + kv([('Struktur flag domain','selalu dipakai untuk domain itu'),('Struktur file / manual',f"dipakai bila dalam radius (bawaan 25 m) dari data vein; opsi global di Data Referensi, opsi per domain di Parameter solid &rarr; Struktur"),
       ('Cara kerja','tiap struktur menjadi titik bantu kemiringan lunak di permukaan HW dan FW, sehingga permukaan mengikuti dip setempat; struktur yang hampir tegak lurus bidang vein diabaikan dan dilaporkan'),
       ('Data latihan',f"volume QV_Lensa2 {fN(SV[0])} m&sup3; &rarr; {fN(SV[1])} m&sup3; setelah {SV[2]} struktur file dipakai")])
 + warn('Struktur hanya mengarahkan kemiringan, bukan posisi. Struktur dari singkapan yang salah ukur bisa menarik permukaan; periksa daftar &ldquo;Struktur dipakai&rdquo; di ringkasan solid.'))

MF = N['mapF'] if isinstance(N.get('mapF'), list) else json.loads(N['mapF'])
L0 = NL['srf0']; L1 = NL['srf1']; LP = NL['lap0']; LC = NL['lap15']; TRF = NL['jejakF1']
def nf(v, d=0): return ('{:,.%df}' % d).format(v).replace(',', 'X').replace('.', ',').replace('X', '.')
ch('Sesar 3D: bidang, offset & urutan umur', '<p>Menu <b>Sesar 3D</b> (rel kiri, sesudah Sayatan) mengubah garis sesar menjadi <b>bidang 3D</b> yang ikut dipakai pemodelan dan estimasi. Panjang bidang searah strike = panjang jejak yang Anda digitasi; jangkauan searah dip diatur dengan <b>Atas jejak</b> dan <b>Bawah</b>.</p>'
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

ch('Geomodeller Stratified-Laterite: laterit nikel', '<p>Endapan <b>laterit</b> (nikel, bauksit) dan <b>stratiform</b> (sedex) berlapis mengikuti permukaan: lapisan tipis secara vertikal tetapi luas ke samping. Menu <b>Geomodeller Stratified-Laterite</b> (rel kiri, di bawah Geomodeller Vein) memodelkan lapisan dari log geologi, lalu mengestimasi per lapisan di koordinat <b>unfold</b>. Menu vein yang lama sekarang bernama <b>Geomodeller Vein</b> (Geomodeller Vein System Deposit).</p>'
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
   'Isi <b>cut-off</b> Ni &ge; 1,5 untuk tonase bijih ([[sl_laporan_cut]]). <b>&#8681; Laporan CSV</b> untuk Excel.')
 + fig2('sl_laporan', f"Tanpa cut-off: Limonit {nf(LP[0][4])} DMT @ Ni {nf(LP[0][5][0],3)}%; Saprolit {nf(LP[1][4])} DMT @ Ni {nf(LP[1][5][0],3)}%.", 'sl_laporan_cut', f"Cut-off Ni &ge; 1,5: Limonit {nf(LC[0][2])} DMT @ {nf(LC[0][3][0],3)}%; Saprolit {nf(LC[1][2])} DMT @ {nf(LC[1][3][0],3)}%.")
 + '<h3>Bauksit &amp; stratiform (sedex)</h3>'
 + kv([('Preset Bauksit','Overburden, Bauksit, Kaolin / lempung, Batuan dasar; pakai unsur Al2O3, SiO2 reaktif, Fe2O3 dan rasio Al2O3 / SiO2'),
       ('Preset Stratiform (sedex)','Hanging wall, Lapisan bijih (Akumulasi 2D), Footwall; lapisan tidak harus mengikuti topografi; sesar post dipulihkan, growth fault = syn + batas keras'),
       ('Akumulasi 2D','per bor: tebal lapisan T dan kadar rata-rata g; kadar blok = &Sigma;(w &middot; T &middot; g) / &Sigma;(w &middot; T): cocok untuk lapisan tipis yang tebalnya berubah')])
 + fig('tree', 'Project Tree: Struktur Geologi &rsaquo; Sesar (bidang 3D) dan Geomodeller Stratified-Laterite Deposit dengan node lapisan &amp; tahap &#9312;&ndash;&#9315;.', '40%')
 + tip('Semua pengaturan lapisan, sesar dan hasil estimasi tersimpan per proyek; tabel <code>sesar</code> dan <code>lapisan</code> ikut ke database proyek SQLite (gcex_proyek.db).'))

ch('Map: peta geologi 2D', '<p>Menu <b>Map</b> di rel kiri mengganti area grafik dengan peta 2D (Easting / Northing; Z tidak dipakai), seperti Global Mapper. Scroll = zoom, tarik = geser; koordinat kursor tampil di kiri bawah.</p>'
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

ch('Mengganti topografi & block model (Data Spasial)', '<p>Topografi pick-up, orthofoto, desain pit dan block model GC berganti tiap periode. Data baru ditambahkan di menu <b>Data Spasial</b> sebagai <b>versi</b>: satu versi aktif dipakai, versi lama tetap tersimpan dan bisa diaktifkan lagi.</p>'
 + steps('Klik <b>Data Spasial</b> di rel kiri.',
   'Di bagian <b>&#9312; Topografi</b> klik <b>+ Tambah versi topografi</b> dan pilih <code>SIM_topo_xyz_nov.csv</code> (topografi bulan berikutnya: area pit turun hingga 6 m).',
   f"Versi baru langsung aktif. {clean(N.get('spMsg',''))}",
   'Centang <b>Banding</b> pada versi lama untuk menampilkannya sebagai titik / garis putus-putus ([[data_spasial]]). Klik tombol bulat <b>Aktif</b> untuk kembali ke versi lama kapan saja.',
   'Block model GC baru: <b>+ Tambah versi block model</b> (jendela Import BM). Di proyek folder jawab <b>OK</b> saat ditawari menyalin file ke folder proyek.')
 + fig('data_spasial', 'Menu Data Spasial: dua versi topografi; versi lama ditampilkan sebagai pembanding di 3D.')
 + tip('Hasil kerja mencatat versi yang dipakai: solid vein yang dipotong topografi dibangun ulang otomatis; uji estimasi dan Model Estimation memberi tanda bila topografi / block model aktif berbeda dari saat dijalankan.')
 + warn('Jangan mengganti data lewat import ulang di proyek folder. Pakai menu Data Spasial agar versi lama tetap ada dan hasil kerja ikut diperbarui.'))

ch('Export database & block model', steps(
 'Menu <b>Data</b> &rarr; <b>&#8681; Export database (CSV)</b>. Pilih <b>Dip di survey</b>: negatif = ke bawah (Surpac / Leapfrog umumnya negatif).',
 f"Hasil: {clean(N['exportDb'])} File ZIP berisi: <code>{', '.join(N['zipIsi'])}</code>.",
 'Kolom <code>Ore_Domain</code> di assay &amp; geologi berisi domain dari flag, siap dipakai sebagai interval selection di Leapfrog atau Surpac.',
 'Block model hasil Model Estimation: <b>&#8681; Export .mdl (Surpac)</b> di Model Estimation (bila block model dibuka dari file .mdl). Header &amp; atribut asli tetap, atribut baru ditambahkan di akhir, blok tambahan disisipkan sesuai urutan octree Surpac. Block model dari CSV: <b>&#8681; CSV blok domain</b> ' + f"({clean(N['meCsv'])}).",
 'String kontrol: <b>&#8681; Export STR</b> / <b>&#8681; Export DXF</b>; flag: <b>&#8681; Export flag (CSV)</b>; solid: <b>OBJ / DXF / STR+DTM</b> di Geomodeller Vein.')
 + tip('Jika menu <b>Proyek &rarr; Salin setiap export ke folder proyek/export</b> aktif, salinan export juga tersimpan di folder proyek, misalnya <code>export/2026-10-22/GCEx_Database_VeinA_Simulasi_20261022.zip</code>.')
 + warn('Export .mdl dengan atribut &amp; blok tambahan sudah diuji dibaca ulang oleh GC-Ex dan dibandingkan per record dengan file asli (model Z3, 590.478 blok). Uji buka di Surpac tetap disarankan sebelum dipakai produksi.'))

ch('Folder proyek, backup & pemulihan', steps(
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
 + '<tr><td><b>Usulan berikutnya</b><br>(belum disepakati)</td><td>Klasifikasi blok (measured / indicated) dari pass, SoR dan jarak sampel; tabel grade-tonnage per domain dan per bench; rekonsiliasi GC lama vs model baru per periode.</td></tr></table>'
 + '<h3>Ringkasan angka latihan (untuk mengecek hasil peserta)</h3>'
 + kv([('Import awal', f"{N['nHole']} hole, {N['nAssay']:,} assay, block model GC {N['bx']:,} blok"),
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

# ================= HTML =================
toc = ''.join('<li><span>%d. %s</span></li>' % (i, t) for i, (t, _) in enumerate(CH))
body = ''.join('<section class="ch"><h2><span>%d</span>%s</h2>%s</section>' % (i, t, b) for i, (t, b) in enumerate(CH))
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
<div class="sub">GC-Ex Drill Hole Ultimate 0.23.1 &middot; langkah demi langkah dengan data simulasi VeinA &amp; laterit nikel (Sesar 3D, Geomodeller Stratified-Laterite)</div></div>
<div class="img"><img src="{FIG['model_3d'][0]}"></div>
<div class="meta">Edisi {today.day} {bulan} {today.year} &middot; untuk pelatihan internal geologist grade control<br>
Data latihan sintetis &middot; semua gambar diambil dari satu kali jalannya latihan</div></div>
<div class="toc"><h2>Daftar isi</h2><ol>{toc}</ol></div>
{body}
</body></html>'''
def _bab(m):
    for i,(t,_) in enumerate(CH):
        if t.startswith(m.group(1)):return 'Bab %d'%i
    raise KeyError(m.group(1))
HTML = re.sub(r'\{\{B:([^}]+)\}\}', _bab, HTML)
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
