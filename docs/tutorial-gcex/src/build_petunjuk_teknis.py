# -*- coding: utf-8 -*-
"""Menyusun 'Petunjuk Teknis GC-Ex' (HTML -> PDF A4) untuk GC-Ex Drill Hole Ultimate & Block Model.

Pendamping 'Tutorial Update GC-Ex': kalau tutorial menjawab *bagaimana memakainya*, dokumen ini
menjawab *bagaimana cara kerjanya* — arsitektur, alur data, format masuk/keluar, algoritme yang
dipakai, batasan yang perlu diketahui, dan masalah umum.

TIDAK memakai tangkapan layar aplikasi, jadi dapat dibangun di mesin mana pun.
Jalankan:  python docs/tutorial-gcex/src/build_petunjuk_teknis.py
Hasil:     docs/GCEx_Petunjuk_Teknis.pdf
"""
import os
import re

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

import doc_gcex as D

FIGD = os.path.join(D.HERE, 'fig_teknis')
os.makedirs(FIGD, exist_ok=True)
PDF = os.path.join(D.DOCS, 'GCEx_Petunjuk_Teknis.pdf')
fig = D.Fig(FIGD)
VBM, VDH = D.versi()

plt.rcParams.update({'font.size': 8, 'figure.facecolor': 'white',
                     'axes.edgecolor': D.INK, 'text.color': D.INK})


def _save(f, nama):
    p = os.path.join(FIGD, nama + '.png')
    f.savefig(p, dpi=190, bbox_inches='tight', pad_inches=0.08)
    plt.close(f)
    return nama + '.png'


# ------------------------------------------------------------------ Gambar 1: susunan aplikasi
def f_arsitektur():
    f, ax = plt.subplots(figsize=(6.4, 3.2))
    ax.axis('off')

    def kotak(x, y, w, h, judul, isi, bg, fg):
        ax.add_patch(plt.Rectangle((x, y), w, h, facecolor=bg, edgecolor=fg, linewidth=1.2, zorder=2))
        ax.text(x + w / 2, y + h - 0.085, judul, ha='center', va='top', fontsize=8.4, color=fg,
                fontweight='bold', zorder=3)
        ax.text(x + w / 2, y + h / 2 - 0.05, isi, ha='center', va='center', fontsize=7, color=D.INK, zorder=3)

    kotak(0.02, 0.60, 0.46, 0.34, 'Jendela aplikasi (Electron)',
          'satu berkas index.html\nPlotly tertanam di dalamnya\ntanpa internet', '#eef2f7', D.ACC)
    kotak(0.52, 0.60, 0.46, 0.34, 'Backend Python (PyInstaller)',
          'hanya untuk block model .mdl besar\nFastAPI di localhost, dimatikan\nsaat aplikasi ditutup', '#f6ebd3', D.ACC2)
    kotak(0.02, 0.17, 0.96, 0.33, 'Folder proyek di komputer Anda',
          'gcex_proyek.db (SQLite: dig block, as-mined, domain, flag, run estimasi, riwayat)  ·  '
          'sumber/ (salinan berkas yang diimpor)  ·  hasil export', '#e9f0e9', '#1b7f4b')
    for x in (0.25, 0.75):
        ax.annotate('', (x, 0.50), (x, 0.60), arrowprops=dict(arrowstyle='<|-|>', color=D.MUT, lw=1.1))
    ax.annotate('', (0.52, 0.77), (0.48, 0.77), arrowprops=dict(arrowstyle='<|-|>', color=D.MUT, lw=1.1))
    ax.text(0.50, 0.805, 'localhost', ha='center', fontsize=6.6, color=D.MUT)
    ax.text(0.5, 0.06, 'Tidak ada data yang keluar dari komputer. Lisensi terikat komputer, diperiksa luring.',
            ha='center', fontsize=7.2, color=D.MUT)
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    return _save(f, 'f1_arsitektur')


# ------------------------------------------------------------------ Gambar 2: alur kerja data
def f_alur():
    f, ax = plt.subplots(figsize=(6.4, 3.8))
    ax.axis('off')
    tahap = [('1  Import', 'Collar, Survey,\nAssay, Geologi\n(CSV / Excel)'),
             ('2  Validasi', 'cek Hole_ID, interval\ntumpang, nilai kosong'),
             ('3  Domain', 'flagging interval\nper domain vein'),
             ('4  Solid', 'string HW / FW\n&rarr; solid RBF'),
             ('5  Geostatistik', 'komposit, top-cut,\nvariogram, KNA'),
             ('6  Estimasi', 'Ordinary Kriging\nblok di dalam solid'),
             ('7  Validasi BM', 'swath, pass, SoR,\ngrade-tonase'),
             ('8  Reporting', 'cut-off, klasifikasi,\nexport .mdl / CSV')]
    y = 0.92
    for i, (j, isi) in enumerate(tahap):
        if i == 4:
            y = 0.46
        x = 0.015 + (i % 4) * 0.247
        ax.add_patch(plt.Rectangle((x, y - 0.20), 0.225, 0.20, facecolor='#eef2f7',
                                   edgecolor=D.ACC, linewidth=1.1))
        ax.text(x + 0.1125, y - 0.035, j.replace('  ', '  '), ha='center', va='top',
                fontsize=8, color=D.ACC, fontweight='bold')
        ax.text(x + 0.1125, y - 0.125, isi.replace('&rarr;', '->'), ha='center', va='center',
                fontsize=6.6, color=D.INK)
        if i % 4 < 3:
            ax.annotate('', (x + 0.243, y - 0.10), (x + 0.228, y - 0.10),
                        arrowprops=dict(arrowstyle='-|>', color=D.MUT, lw=1.1))
    ax.annotate('', (0.128, 0.46), (0.128, 0.60), arrowprops=dict(arrowstyle='-|>', color=D.MUT, lw=1.1))
    ax.annotate('', (0.90, 0.60), (0.90, 0.72), arrowprops=dict(arrowstyle='-', color=D.MUT, lw=1.1))
    ax.plot([0.128, 0.90], [0.60, 0.60], color=D.MUT, lw=1.1)
    ax.text(0.5, 0.10, 'Setiap tahap menyimpan hasilnya ke folder proyek, jadi pekerjaan dapat dilanjutkan\n'
                        'dan run estimasi berikutnya hanya menghitung ulang blok yang terpengaruh.',
            ha='center', fontsize=7.2, color=D.MUT)
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    return _save(f, 'f2_alur')


# ------------------------------------------------------------------ Gambar 3: dua jalur estimasi
def f_dua_jalur():
    f, ax = plt.subplots(figsize=(6.4, 2.7))
    ax.axis('off')
    ax.add_patch(plt.Rectangle((0.02, 0.26), 0.45, 0.68, facecolor='#eef2f7', edgecolor=D.ACC, lw=1.2))
    ax.add_patch(plt.Rectangle((0.53, 0.26), 0.45, 0.68, facecolor='#e9f0e9', edgecolor='#1b7f4b', lw=1.2))
    ax.text(0.245, 0.875, 'Model Estimation', ha='center', fontsize=9, color=D.ACC, fontweight='bold')
    ax.text(0.755, 0.875, 'Geomodeller Stratified-Laterite', ha='center', fontsize=9, color='#1b7f4b',
            fontweight='bold')
    kiri = ['endapan VEIN', 'wadah: solid 3D domain', 'ruang: koordinat asli',
            'variogram per domain (3D)', 'keluaran: au_est / au_final']
    kanan = ['endapan BERLAPIS (laterit, bauksit, sedex)', 'wadah: lapisan atap / lantai',
             'ruang: UNFOLD per lapisan', 'variogram per lapisan, opsi akumulasi 2D',
             'keluaran: sl_lapisan + laporan WMT / DMT']
    for i, (a, b) in enumerate(zip(kiri, kanan)):
        ax.text(0.05, 0.78 - i * 0.105, '• ' + a, fontsize=7, color=D.INK)
        ax.text(0.56, 0.78 - i * 0.105, '• ' + b, fontsize=7, color=D.INK)
    ax.text(0.5, 0.08, 'Dua mesin terpisah. Tipe deposit tidak ditebak aplikasi: Anda yang memilih lewat node mana\n'
                       'pekerjaan dijalankan. Satu proyek boleh memakai keduanya.',
            ha='center', fontsize=7.2, color=D.MUT)
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    return _save(f, 'f3_dua_jalur')


F1, F2, F3 = f_arsitektur(), f_alur(), f_dua_jalur()

# ================================================================== isi dokumen
B = []
# sampul disisipkan di akhir (daftar isi dihitung dari judul <h2> yang benar-benar ada,
# supaya tidak pernah ketinggalan saat bagian baru ditambahkan)
# ---- 1
B.append('<h2>1. Cara kerja singkat</h2>')
B.append('<p>GC-Ex adalah dua aplikasi desktop terpisah yang dipasang sendiri-sendiri: '
         '<b>GC-Ex Drill Hole Ultimate</b> (basis data bor, pemodelan domain vein, geostatistik, estimasi, '
         'reporting) dan <b>GC-Ex Block Model</b> (flitch, dig block, additional flagging, as-mined). '
         'Keduanya berjalan <b>sepenuhnya di komputer Anda</b>: tidak butuh internet, tidak ada data yang '
         'dikirim keluar, dan tidak ada pemeriksaan pembaruan daring.</p>')
B.append(fig(F1, 'Susunan aplikasi. Hampir semua pekerjaan terjadi di dalam jendela aplikasi; backend '
                 'Python hanya dipanggil untuk block model <code>.mdl</code> berukuran besar.'))
B.append('<p>Isi aplikasi ada di <b>satu berkas HTML</b> dengan pustaka grafik Plotly tertanam di dalamnya '
         '(tidak diambil dari internet). Pembungkusnya adalah Electron, yang menyediakan jendela, menu, '
         'akses berkas, dan gerbang lisensi. Untuk block model yang terlalu besar dibaca di dalam jendela, '
         'ada backend Python kecil yang dijalankan aplikasi di <code>localhost</code> dan dimatikan lagi saat '
         'aplikasi ditutup.</p>')

# ---- 2
B.append('<h2>2. Memasang &amp; menjalankan</h2>')
B.append(D.steps(
    'Jalankan <code>GC-Ex-Setup-&lt;versi&gt;.exe</code> (Block Model) atau '
    '<code>GC-Ex-Drillhole-Setup-&lt;versi&gt;.exe</code>. Tidak perlu hak administrator; terpasang ke '
    '<code>%LOCALAPPDATA%\\Programs</code>.',
    'Saat pertama dibuka, setujui Syarat Penggunaan lalu aktifkan lisensi (lihat '
    '<i>Tutorial Aktivasi Lisensi GC-Ex</i>).',
    'Pilih atau buat <b>folder proyek</b>. Seluruh pekerjaan disimpan di folder itu.'))
B.append('<div class=box><b>Kedua aplikasi dipasang terpisah dan boleh berdampingan.</b> Keduanya memakai '
         'folder proyek dengan bentuk yang sama, jadi Block Model dapat membuka folder proyek yang dibuat '
         'Drill Hole Ultimate dan sebaliknya; masing-masing hanya memakai bagian yang relevan baginya.</div>')
B.append('<p>Pembaruan tidak diunduh aplikasi. Versi baru diambil dari GitHub Release dan dipasang menimpa '
         'versi lama — pengaturan, lisensi dan folder proyek tidak tersentuh.</p>')

# ---- 3
B.append('<h2>3. Folder proyek dan apa yang disimpan</h2>')
B.append(D.tabel(['Isi folder proyek', 'Keterangan'], [
    ['<code>gcex_proyek.db</code>', 'basis data SQLite: dig block &amp; as-mined per flitch (Block Model); '
     'database bor, domain, flag, run estimasi (Drill Hole Ultimate); beserta riwayat perubahan dan '
     'view rekap seperti <code>rekap_flitch</code> dan <code>assay_domain</code>'],
    ['<code>sumber/</code>', 'salinan berkas yang Anda impor (block model, topografi, pit, wireframe, '
     'orthofoto). Disalin supaya versi lama tetap bisa diaktifkan lagi dan proyek dapat dibuka orang lain'],
    ['berkas hasil export', 'ditulis ke tempat yang Anda pilih saat export (.mdl, .str, .dxf, .obj, CSV, '
     'Excel, gambar layout)']]))
B.append('<p>Karena seluruh keadaan pekerjaan ada di folder itu, memindahkan proyek antar komputer cukup '
         'dengan menyalin foldernya. Lisensi tetap terikat ke komputer masing-masing.</p>')

# ---- 4
B.append('<h2>4. Alur kerja data</h2>')
B.append(fig(F2, 'Urutan kerja yang diasumsikan aplikasi. Project Tree di sisi kiri mengikuti urutan ini, '
                 'lengkap dengan status tiap langkah.'))
B.append('<p>Tahap 5&ndash;8 dapat diulang berkali-kali tanpa mengulang tahap 1&ndash;4. Saat ada bor baru, '
         '<b>Model Estimation</b> hanya menghitung ulang blok yang lingkungan kriging-nya memuat komposit '
         'baru atau berubah — bukan seluruh block model.</p>')

# ---- 5
B.append('<h2>5. Data bor: format &amp; aturan</h2>')
B.append('<p>Empat tabel dibaca dari CSV atau Excel dengan <b>header bebas</b>: nama kolom dikenali otomatis '
         'dan dapat Anda petakan ulang bila tebakan aplikasi meleset.</p>')
B.append(D.tabel(['Tabel', 'Kolom inti', 'Catatan'], [
    ['Collar', 'Hole_ID, Easting, Northing, RL, Total_depth', 'satu baris per lubang bor'],
    ['Survey', 'Hole_ID, Depth, Dip, Azimuth', 'boleh beberapa baris per bor; <b>dip negatif = ke bawah</b>'],
    ['Assay', 'Hole_ID, From, To, &lt;unsur&gt;…', 'kolom unsur sebanyak yang ada (Au, Ag, Cu, Pb, Zn, S, As, SG…)'],
    ['Geologi', 'Hole_ID, From, To, &lt;atribut&gt;…', 'Lith, Alt, Ox, Texture, RQD, Recovery, dan lainnya']]))
B.append('<p>Menu <b>Validasi data bor</b> memeriksa hal-hal yang biasanya merusak pemodelan: Hole_ID ganda, '
         'Hole_ID di assay yang tidak ada di collar, <code>From = To</code>, interval yang tumpang tindih, '
         'Sample_ID ganda, nilai kosong atau <code>-99</code>, interval melebihi kedalaman bor, dan koordinat '
         'kosong atau jauh di luar area. Data latihan <code>SIM_rusak_*.csv</code> sengaja memuat kesembilan '
         'kesalahan itu untuk mencoba menunya.</p>')
B.append('<div class=box><b>Import ulang bersifat <i>upsert</i>.</b> Lubang bor yang sudah ada akan '
         '<b>diganti</b> isinya, lubang baru ditambahkan, dan pratinjau menunjukkan berapa yang baru, '
         'diperbarui dan sama sebelum Anda menekan tombolnya.</div>')
B.append('<h3>Apa yang terjadi pada data tidak valid</h3>')
B.append('<p>Bawaannya: <b>baris valid tetap masuk</b>, baris tidak valid <b>dibuang per baris</b> dan '
         'dilaporkan. Import hanya diblokir bila <b>tidak ada satu pun collar valid</b>.</p>')
B.append(D.tabel(['Tingkat', 'Contoh', 'Akibat'], [
    ['<b>DIBUANG</b>', 'collar tanpa E / N / RL; collar ganda (HoleID sama); survey dengan |dip| &gt; 90&deg; '
     'atau azimuth di luar &minus;360&hellip;720; assay / geologi tanpa From&ndash;To, <code>From &ge; To</code>, '
     'atau From negatif',
     'baris itu tidak masuk. Collar tanpa koordinat menghilangkan <b>seluruh hole beserta intervalnya</b> &mdash; '
     'ini yang paling berbahaya karena tidak terasa'],
    ['<b>PERINGATAN</b>', 'interval tumpang tindih; interval melewati total depth; survey kedalaman ganda; '
     'Sample_ID ganda di dua tempat; nilai negatif (kode below detection)',
     'data <b>tetap dipakai</b>. Tumpang tindih membuat panjang terhitung dua kali di statistik dan komposit; '
     'nilai negatif dipakai apa adanya &mdash; ganti dengan &frac12; batas deteksi di database sumber'],
    ['<b>INFO</b>', 'celah (gap) antar interval; collar tanpa assay; survey tanpa collar',
     'tidak mengubah apa pun, hanya pemberitahuan']]))
B.append('<p>Di <b>upsert</b> ada satu perbedaan: assay / survey / geologi yang <b>HoleID-nya belum ada di '
         'collar</b> tidak dibuang melainkan <b>disimpan</b> dan tidak ditampilkan sampai collar-nya masuk. '
         'Seluruh daftar temuan dapat diunduh sebagai <b>Validasi_Data_Bor.csv</b> (Tingkat, Kategori, Hole, '
         'Keterangan) untuk dikirim balik ke penyiap data. GC-Ex <b>tidak pernah mengubah berkas sumber</b>.</p>')

# ---- 6 (baru): kampanye & filter
B.append('<div class="page"></div><h2>6. Kampanye pemboran, dataset aktif &amp; filter data</h2>')
B.append('<p>Satu area dibor berkali-kali: eksplorasi, infill, lalu grade control tiap periode. GC-Ex menyimpan '
         'semuanya di <b>satu set tabel</b> (collar / survey / assay / geologi) dan memisahkannya dengan '
         '<b>label kampanye per hole</b>, bukan dengan tabel terpisah per kampanye. Alasannya teknis: seluruh '
         'mesin GC-Ex &mdash; pewarnaan, sayatan, komposit, variogram, estimasi &mdash; membaca satu kumpulan '
         'data yang sama, sehingga memecah tabel berarti menduplikasi semua jalur itu.</p>')
B.append(D.tabel(['Keadaan node database', 'Peran', 'Akibat teknis'], [
    ['<b>AKTIF</b>', 'set kerja', 'satu-satunya sumber pemodelan, estimasi, Geostatistik dan statistik '
     '(titik analisis memakai <code>visHolesK()</code>)'],
    ['dicentang, tidak aktif', 'referensi', 'ikut digambar di 3D / Sayatan 2D (<code>visHoles()</code>) tetapi '
     '<b>tidak</b> masuk analisis &mdash; inilah cara membandingkan kadar GC dengan bor eksplorasi tanpa '
     'mencampurnya ke dalam komposit'],
    ['tidak dicentang', 'sembunyi', 'tidak digambar dan tidak dianalisis; data tetap tersimpan']]))
B.append('<h3>Set merge</h3>')
B.append('<p>Menggabungkan beberapa kampanye membuat <b>node database baru</b> (Collar / Survey / Assay / '
         'Geologi <b>Merge</b>) yang bisa dijadikan dataset aktif. Set merge adalah <b>pandangan hidup</b> atas '
         'kampanye sumbernya, bukan salinan: hole yang ditambahkan ke salah satu sumber otomatis ikut. '
         'Export <b>.xlsx 4 sheet</b> (masing-masing berkolom Kampanye) tersedia per database, termasuk set merge.</p>')
B.append('<div class=box><b>Bentrok HoleID saat upsert</b> diselesaikan dengan <b>urutan prioritas</b> kampanye. '
         'Bila hole itu sudah dimiliki kampanye yang lebih tinggi, data baru untuk hole tersebut <b>ditolak</b> '
         '(tidak menimpa) dan HoleID yang ditolak dilaporkan. Jadi prioritas dipasang <b>sebelum</b> import.</div>')
B.append('<h3>Filter data bor</h3>')
B.append('<p>Filter disambungkan pada <b>satu titik</b> saja, yaitu fungsi penilai domain '
         '(<code>domOK()</code>). Karena setiap mesin analisis memanggil fungsi itu, satu aturan filter langsung '
         'berlaku di tampilan, statistik, komposit, Geostatistik dan estimasi tanpa mengubah satu pun fungsi '
         'analisis. Aturan dinilai <b>per interval</b> dengan mode AND atau OR; daftar atributnya dibangun '
         'dinamis dari kolom yang benar-benar ada (unsur, kategori assay, atribut geologi, kampanye, data collar, '
         'From / To / panjang, HoleID) ditambah aturan <b>posisi</b> terhadap topografi, DTM, solid domain, '
         'wireframe dan poligon.</p>')
B.append(D.tabel(['Jalur', 'Cara interval dinilai'], [
    ['Statistik, komposit, Geostatistik, <b>estimasi</b>',
     '<b>utuh atau gugur</b>, dinilai dari <b>titik tengah</b> interval. Tidak ada pemotongan. Interval yang '
     'tidak lolos tidak dipakai sebagai data masukan &mdash; jadi filter memang mengubah hasil estimasi'],
    ['<b>Export</b> data terfilter (.xlsx / CSV)',
     'interval yang memotong permukaan <b>dipotong tepat di permukaannya</b> (bagi-dua 30 langkah pada lintasan '
     'bor): interval 10&ndash;20 m dengan permukaan di 15 m keluar sebagai 15&ndash;20. Tanpa ini &ldquo;hanya di '
     'bawah topografi&rdquo; melebihkan panjang bor sebesar separuh interval di batasnya']]))
B.append('<p>Status hidup-mati dan seluruh aturan ikut tersimpan di berkas proyek. Mematikan filter tidak '
         'menghapus aturannya &mdash; cukup melepas centang node <b>Filter data bor</b>.</p>')

# ---- 6
B.append('<div class="page"></div><h2>7. Autorun: menjahit langkah, bukan mengambil keputusan</h2>')
B.append('<p>Autorun tidak memuat algoritme baru. Ia <b>memanggil fungsi yang sama</b> dengan yang dipakai manual, '
         'mengulanginya per domain / per lapisan, lalu melaporkan hasilnya. Nilainya ada pada penjahitan langkah dan '
         'pada laporannya &mdash; bukan pada kepintaran baru.</p>')
B.append(D.tabel(['Perintah', 'Yang dipanggil berurutan'], [
    ['<b>Autorun Wireframe</b> (vein)', 'hitung strike dari kontak flag &rarr; pasang section tegak lurus strike &rarr; '
     'tarik string semua section (fungsi yang sama dengan tombol &ldquo;tarik otomatis&rdquo;) &rarr; nyalakan solid '
     'domain bila masih mati &rarr; solid RBF rebuild sendiri'],
    ['<b>Autorun Estimation</b> (vein)', 'pilih domain yang siap &rarr; estimasi inkremental dengan <b>parameter '
     'tersimpan</b> &rarr; estimasi waste &rarr; segarkan Reporting BM'],
    ['<b>Autorun Lapisan</b> (laterit)', 'usulkan lapisan dari kode log menurut kedalaman tengah rata-rata '
     '(hanya bila belum ada) &rarr; bangun permukaan atap / lantai'],
    ['<b>Autorun Estimasi Lapisan</b> (laterit)', 'estimasi unfold per lapisan dengan parameter tiap lapisan &rarr; '
     'estimasi waste laterit (zona bawah & atas)']]))
B.append('<h3>7.1 Empat pengaman</h3>')
B.append(D.tabel(['Pengaman', 'Mekanismenya'], [
    ['Pekerjaan tangan tidak pernah ditimpa', 'string kontrol membawa penanda <code>auto</code>. Yang sudah diedit '
     'tangan dilewati dan <b>dihitung</b>; karena itu &ldquo;dari nol&rdquo; dan &ldquo;melanjutkan&rdquo; adalah '
     'operasi yang sama &mdash; keputusannya per section, bukan per perintah'],
    ['Tidak pernah mengarang parameter', 'autorun estimasi memakai parameter yang sudah disimpan per domain apa '
     'adanya. Domain tanpa parameter <b>dilewati</b> dengan alasan tertulis. Tidak ada fitting variogram otomatis '
     'di jalur produksi'],
    ['Idempoten', 'menjalankan dua kali berturut-turut tidak menambah satu string pun dan tidak mengubah hasil '
     '(diuji: <code>made 0, rep 44</code> pada jalan kedua)'],
    ['Dapat diperiksa', 'laporan memuat <b>sebelum &rarr; sesudah</b>: volume solid dan persen perubahannya; untuk '
     'estimasi, kadar rata-rata dan tonase dibanding run sebelumnya. Bisa diunduh CSV, dan riwayat run tetap bisa '
     'dibatalkan']]))
B.append('<h3>7.2 Autorun Estimasi dari Nol: usulan + gerbang mutu</h3>')
B.append('<p>Autorun update memakai parameter yang sudah disetujui. Untuk domain baru, autorun harus '
         '<b>mengusulkan</b> parameter statistik &mdash; jalur yang berbeda sifatnya, karena usulan bisa salah. '
         'Yang dipanggil: <code>gsrAuto</code> (rekomendasi lag / transform / top-cut) &rarr; <code>gsFitAuto</code> '
         '(fitting model) &rarr; <code>knaRun</code> + <code>knaApply</code> (pindai lingkungan kriging, terapkan '
         'yang terbaik) &rarr; <code>meFromGs</code> (simpan ke domain); <code>AOI.go</code> lebih dulu bila belum '
         'ada block model.</p>')
B.append('<p>Usulan ukuran blok diambil dari data, bukan dari angka hafalan: <b>blok X/Y &asymp; sepertiga spasi '
         'bor</b> (median jarak tiap collar ke collar terdekat), <b>blok Z &asymp; tebal vein median</b> (jarak '
         'pasangan kontak HW&ndash;FW). Sub-blocking disarankan bila tebal vein kurang dari 3&times; tinggi blok. '
         'Semuanya dapat diubah pengguna, dan alasan usulannya ditampilkan.</p>')
B.append(D.tabel(['Gerbang mutu', 'Putusan'], [
    ['Komposit &lt; ambang (bawaan 30); solid belum ada; domain <b>sudah berparameter</b>',
     '<b>dilewati</b> &mdash; tidak ada yang disimpan. Parameter yang sudah disetujui tidak pernah ditimpa'],
    ['Nugget &gt; ambang (bawaan 80%)', '<b>perlu ditinjau</b> &mdash; estimasi akan sangat merata'],
    ['Nugget &lt; 5%', '<b>perlu ditinjau</b> &mdash; pada kadar logam nugget nol praktis tidak pernah terjadi; '
     'biasanya variogram belum terbentuk atau pasangan sampel berjarak pendek terlalu sedikit'],
    ['Range mayor / semi &lt; 1,05', '<b>perlu ditinjau</b> &mdash; anisotropi tidak terselesaikan (elipsoid bulat); '
     'untuk vein hampir selalu keliru'],
    ['Komposit &lt; 50', '<b>perlu ditinjau</b> &mdash; variogram masih rapuh untuk produksi'],
    ['Range mayor &lt; 2&times; panjang komposit, atau &gt; 3&times; bentang data',
     '<b>perlu ditinjau</b> &mdash; model belum terbentuk atau tidak terkekang']]))
B.append('<div class=box>Tiga gerbang terakhir (nugget mendekati nol, elipsoid bulat, komposit &lt; 50) '
         'ditambahkan <b>setelah</b> uji pertama memperlihatkan variogram yang jelas tidak terbentuk &mdash; '
         'nugget 0%, range mayor sama dengan range semi, 31 komposit &mdash; justru lolos sebagai '
         '&ldquo;tersimpan&rdquo;. Memeriksa nugget yang terlalu tinggi saja tidak cukup.</div>')
B.append('<p>Pilihan <b>langsung mengestimasi sesudahnya</b> bawaannya <b>mati</b>: parameter hasil usulan harus '
         'dilihat geologistnya sebelum angka sumber daya keluar darinya.</p>')

B.append('<div class=box>Yang <b>tidak</b> diotomatiskan, dan tidak akan: keputusan domain dan flag (itu geologi), '
         'interpretasi sesar, serta ambang klasifikasi Measured / Indicated / Inferred (itu ranah pelaporan dan '
         'kepatuhan). Autorun mengulang pekerjaan, bukan mengambil keputusan.</div>')

B.append('<div class="page"></div><h2>8. Wireframe geologi (Leapfrog / Surpac): satu node &amp; sebagai domain</h2>')
B.append('<p><b>Satu node saja.</b> Wireframe / solid geologi diimport dan dilihat hanya di node <b>Import Wireframe '
         'Geologi</b> (Drill Hole langkah 2b, Block Model langkah 4b; panel <code>pWf</code>). Anak node = berkas di '
         '<code>MD.models</code> sesuai <b>urutan import</b>. Di Drill Hole seluruh langkah wireframe &rarr; domain '
         '(serap, iris, flag, kunci eksak) dijalankan dari menu klik-kanan berkasnya; Geomodeller Vein hanya memuat '
         'domain dan string hasilnya. Tidak ada pintu import wireframe lain &mdash; panel lain (Reporting &rsaquo; '
         'Batas DTM, Geomodeller &rsaquo; Dari wireframe luar) hanya <i>memilih</i> berkas yang sudah diimport.</p>')
B.append(D.tabel(['Permukaan', 'Drill Hole', 'Block Model'], [
    ['Wireframe geologi', 'node Import Wireframe Geologi (<code>MD.models</code>)', 'node Import Wireframe Geologi (<code>MD.models</code>, <code>jenis: geo</code>)'],
    ['Desain pit / topografi', '<b>Data Spasial</b>, versi pit / topografi; DXF 3DFACE disimpan sebagai TIN seperti .dtm',
     '<b>Data Referensi (DTM, titik, string)</b> (<code>MD.models</code>, <code>jenis: surf</code>; Block Model tidak punya versi Data Spasial)'],
    ['Proyek lama', 'tombol &#8943; berkas &rarr; <i>Pindahkan ke Data Spasial&hellip;</i>: versi non-aktif ber-TIN; rujukan Reporting <code>wf:&lt;i&gt;</code> dialihkan ke <code>sp:&lt;peran&gt;:&lt;id&gt;</code>, indeks sesudahnya digeser',
     'tombol &#8943; berkas &rarr; <i>Pindahkan ke Data Referensi</i> / <i>ke Import Wireframe Geologi</i> (mengubah <code>jenis</code>)']]))
B.append('<p>Model implicit dari Leapfrog dapat dipakai GC-Ex dengan dua cara yang tujuannya berbeda. Perbedaannya '
         'bukan soal mutu, melainkan soal <b>siapa pemegang bentuknya</b>.</p>')
B.append(D.tabel(['', 'Mode B &mdash; diserap', 'Mode A &mdash; eksak'], [
    ['Jalur teknis', 'mesh &rarr; irisan per section &rarr; tiap loop tertutup dibelah jadi string HW / FW '
     '(<code>src = wf:&lt;berkas&gt;</code>) &rarr; solid RBF',
     'domain dikunci ke mesh (<code>d.wfx</code>); uji titik-di-dalam memakai mesh itu sendiri'],
    ['Bentuk', 'rekonstruksi: diresample sesuai spasi section lalu dihaluskan RBF', 'identik dengan mesh'],
    ['Volume', 'volume solid RBF', 'volume mesh (jumlah tetrahedron bertanda)'],
    ['Bisa diedit', 'ya &mdash; sudah menjadi string kontrol GC-Ex', 'tidak'],
    ['Ikut bor baru', 'ya, lewat Autorun Wireframe', 'tidak'],
    ['Dipakai untuk', 'kerja harian: melanjutkan model geologist lain', 'audit: bandingkan tonase batas Leapfrog '
     'vs solid GC-Ex']]))
B.append('<h3>8.1 Satu titik sambungan</h3>')
B.append('<p>Mode eksak disambungkan pada <b>satu</b> fungsi: pembaca solid domain (<code>meGrpR</code>). Seluruh '
         'mesin GC-Ex &mdash; estimasi domain, estimasi waste, sub-blocking, filter posisi, pelaporan &mdash; membaca '
         'solid lewat fungsi itu, sehingga satu sambungan membuat mode eksak berlaku di semuanya <b>tanpa menyentuh '
         'satu pun fungsi analisis</b>. Bila wireframe belum diimport ulang saat proyek dibuka, fungsi itu otomatis '
         'kembali memakai solid RBF dan node-nya menandai <i>(hilang)</i>, jadi proyek tidak pernah gagal dibuka '
         'karena berkas acuan yang tertinggal.</p>')
B.append('<h3>8.2 Kontrol mutu penyerapan</h3>')
B.append('<p>Berbeda dengan impor <code>.mdl</code> yang masuk persis apa adanya, wireframe <b>diresample</b>. '
         'Karena itu laporan penyerapan selalu menyebut <b>volume wireframe vs volume solid hasil serap beserta '
         'selisih persennya</b>; selisih di atas ~10% memunculkan peringatan untuk merapatkan spasi section dan '
         'menyerap ulang ke domain yang sama. Mesh yang <b>tidak tertutup rapat</b> juga dilaporkan (jumlah sisi '
         'terbuka): pada mesh bocor, uji titik-di-dalam tidak bisa dipercaya sehingga flag interval maupun volumenya '
         'tidak bermakna.</p>')
B.append('<div class=box><b>Konsekuensi yang perlu disepakati di tim.</b> Sejak diserap, GC-Ex menjadi sumber '
         'kebenaran bentuknya. Serap ulang mengganti string impor lama tetapi <b>melewati</b> string yang sudah '
         'diedit tangan &mdash; jumlah section yang dilewati itulah ukuran seberapa jauh model GC-Ex dan model '
         'Leapfrog sudah berpisah.</div>')

B.append('<h3>8.3 Vein system: banyak vein dari satu kolom kode (Drill Hole 0.24.71)</h3>')
B.append('<p>Diadopsi dari review mesh <i>Vein System</i> Leapfrog. Algoritma solid RBF per domain tetap sama; yang ditambahkan adalah '
         'cara mengelola banyak domain sekaligus (<code>web-src-dh/vsys_dh.js</code>) dan resolusi adaptif di <code>imBuild</code>.</p>')
B.append(D.tabel(['Bagian', 'Cara kerja'], [
    ['Flag dari kolom kode', 'baris kolom terpilih (atribut geologi <code>geoRows</code> atau kategori assay) dikelompokkan per <b>domain tujuan</b>; '
     'interval sekode di lubang yang sama digabung bila selanya &le; nilai <i>Gabung run</i>; ditulis dengan <code>gmSetRange</code> '
     '(satu flag per kedalaman, flag domain lain di interval itu tertimpa). Mode <i>Diganti seluruhnya</i> menghapus dulu flag lama '
     'domain tujuan di semua lubang. Domain baru memakai parameter domain aktif dan solidnya dinyalakan. Diurungkan dengan <i>Urungkan</i>.'],
    ['Prioritas', 'urutan domain induk di <code>GM.doms</code>. Model Estimation mengklaim blok per domain menurut urutan ini '
     '(<code>claimed</code>): blok di dalam dua solid menjadi milik domain yang lebih atas. Cabang ikut induknya.'],
    ['Volume gabungan', 'jumlah volume solid dikurangi tumpang tindih. Tumpang tindih tiap pasangan dihitung dengan titik grid '
     '(0,5&ndash;2 m, &le; &plusmn;200 rb titik) di irisan kotak batas kedua solid; titik yang berada di &ge; 3 solid dihitung '
     'hanya sekali per solid tambahan. Hasil disimpan dengan kunci solid; berubah = &ldquo;usang&rdquo;, hitung ulang.'],
    ['Ekspor gabungan', 'mesh semua solid tampil disambung (<code>imMerge</code>) lalu ditulis dengan penulis OBJ / DXF / STR+DTM yang '
     'sama dengan ekspor per domain. Solid tidak di-boolean-kan: bagian yang bertumpang tetap ada di kedua solid.'],
    ['Solid usang', 'saat solid dibangun dicatat dua sidik: <b>data</b> (titik HW/FW dari kontak bor, flag dan string) dan '
     '<b>parameter</b> (kunci <code>imKey</code> tanpa titik). Bila <i>Jalankan ulang otomatis</i> mati dan kunci berubah, '
     'domain ditandai usang; sebabnya dari sidik mana yang berbeda.'],
    ['Resolusi adaptif', 'simpul mesh searah strike dan searah dip tidak lagi seragam. Jarak simpul pada posisi <i>x</i> = '
     'resolusi &times; min(K, 1 + d/(3 &times; resolusi)), d = jarak ke koordinat data terdekat di arah itu, K = <i>Jarang maks.</i> '
     '(bawaan 4). Luas &amp; volume ekstrapolasi memakai lebar simpul setempat. Mati = rumus lama persis (A/B identik).']]))

B.append('<h3>8.4 Jalur proyek: mulai dari nol / lanjutkan (Drill Hole 0.24.73)</h3>')
B.append('<p>Jalur adalah status proyek, bukan algoritma: tidak ada perhitungan yang berubah. Kode: <code>web-src-dh/jalur_imp_dh.js</code> '
         '(halaman Import) dan <code>web-src-dh/jalur_dh.js</code> (viewer, disambung sesudah <code>vsys_dh.js</code>). Disimpan di pekerjaan '
         'proyek sebagai <code>jalur = {mode, acuan:{wf,bm,par}, log, tebak}</code>.</p>')
B.append(D.tabel(['Bagian', 'Cara kerja'], [
    ['Penentu', '<code>mode</code> = <i>nol</i> / <i>lanjut</i>. Objek acuan: wireframe dari file (<code>MD.models</code>, domain <code>d.wfx</code> atau string '
     '<code>src: wf:</code>), versi block model dengan <code>src.kind</code> <i>mdl</i> / <i>csv</i> (atau AOI / sub-blok yang <code>base</code>-nya acuan), '
     'parameter dari log. Data mentah tidak dihitung.'],
    ['Pintu', '<code>JLR.boleh(k)</code> = jalur lanjut dan acuan <i>k</i> dicentang. Dipakai oleh pengaman <code>bxDlg</code>, <code>bmAdd</code> '
     '(di jalur tanpa acuan block model dialihkan ke <code>AOI.dlg</code>), <code>mdImport</code> (wireframe geologi; permukaan / '
     '<i>surf</i> selalu boleh), <code>uiTab(\'Wf\')</code>, dan penyaring node Project Tree (<code>PT.def.nodes</code>).'],
    ['Sinkron', '<code>JLR.sinkron()</code> sesudah proyek dibuka: jalur kosong &rarr; ditebak dari isi (<code>tebak</code>); jalur nol tetapi ada objek '
     'acuan &rarr; lanjut + <code>tebak</code>; jalur lanjut &rarr; acuan yang objeknya ada dinyalakan. Selama <code>tebak</code> tidak ada pintu ditutup.'],
    ['Otomasi', '<code>arWfDoms</code> mengeluarkan domain <code>d.wfx</code> (eksak). <code>meFromGs</code> pada domain berparameter dengan acuan parameter '
     '&rarr; <code>confirm</code> + jejak. <code>ar3</code>, <code>arEst</code>, <code>gsFitAuto</code>, <code>knaRun</code> tidak diubah (sudah tidak menimpa). <code>ar3</code> (0.24.75, opsi <code>AR3.o.bidang</code>, bawaan nyala): sebelum <code>gsRun</code> tiap domain dipanggil <code>NY.planeSec()</code> (alert dibungkam, gagal &rarr; sayatan aktif); nilai sayatan pemakai (<code>sMode, p1e..p2n, dipS, dipN, pos, thick, limSeg</code>) disimpan di awal dan dipulihkan di <code>tutup()</code>. <code>AOI.go</code> di dalam autorun (<code>AR3.busy</code> / <code>AR.busy</code>) tidak memanggil <code>alert</code> langkah berikutnya; teksnya masuk <code>AOI.msg</code> dan laporan autorun.'],
    ['Jejak', '<code>log</code>: [ket, waktu, pengguna], dari pemilihan di halaman Import, konfirmasi tebakan, ubah acuan, '
     '<i>Jadikan jalur Lanjutan</i> (didahului <code>FP.flush</code>).'],
    ['Halaman Import', 'proyek baru wajib memilih jalur sebelum <b>Tampilkan viewer</b>; import ulang membaca jalur dari pekerjaan tersimpan (baca saja). '
     '<code>SA.go()</code> dari skrip tanpa pilihan: demo &rarr; lanjut (wf, bm); ada berkas block model &rarr; lanjut (bm) + tebak; selain itu nol.'],
    ['Data latihan', '0.24.76: tombol <code>#dlatNolBtn</code> di samping <code>#dlatBtn</code> (dipasang dari <code>jalur_imp_dh.js</code>; <code>demodata.js</code> bersama tidak diubah). '
     '<code>JLR.dlat(nol)</code> menyetel jalur, lalu <code>DLAT.muat</code>; selama <code>JLR.dlatNol</code>, <code>DLAT.ada</code> menolak <code>*_BM_GC*</code> dan <code>*Leapfrog.obj</code>. '
     'Saat data latihan dimuat, jalur di <code>SA.go</code> mengikuti tombol (bukan kartu).']]))

B.append('<h3>8.5 Parameter estimasi dari log Surpac (Drill Hole 0.24.79)</h3>')
B.append(D.tabel(['Bagian', 'Cara kerja'], [
    ['Kode', '<code>web-src-dh/slog_dh.js</code> (<code>SLOG</code>), disambung sesudah <code>sumber_dh.js</code>. Pintu: <code>meParHtml</code> dibungkus (tombol per domain) dan menu node <code>me</code>; '
     'hanya bila <code>JLR.boleh(\'par\')</code>, proyek tanpa jalur, atau jalur masih tebakan.'],
    ['Pembaca', '<code>SLOG.parse</code>: blok perintah <code>BM FILL OK / ORDINARY KRIGING / INVERSE DISTANCE / NEAREST NEIGHBOUR</code> sampai perintah berikutnya; '
     '<code>frm20030.attname</code>, <code>frm20040</code> (location &rarr; <code>compositeXX.str</code> &rarr; unsur; constrain), <code>frm20080</code> (majordist, semimajfact, minorfact, min/max, max_samp_per_id, axis_1..3), '
     '<code>frm20101</code> (co, c1..c5, a1..a5, azimuth/plunge/dip, semi_ratio, minor_ratio), constraint <code>INSIDE/OUTSIDE CONSTRAINT nama</code>.'],
    ['Orientasi', '<code>SLOG.vek(b,p,d)</code>: ZXY LRL &mdash; bearing searah jarum jam; plunge tangan kanan (positif mengangkat mayor); dip tangan kiri (positif mengangkat semi). '
     'Dipilih secara empiris pada BMGC Zona 3 (korelasi 0,871 vs 0,733&ndash;0,819 untuk tafsiran lain).'],
    ['Salin', '<code>SLOG.est</code>: <code>m</code> = {vM,vS,vN,c0,cs,A,B=a/semi_ratio,Cn=a/minor_ratio}; <code>sr</code> = [majordist, majordist/semimajfact, majordist/minorfact]; '
     '<code>P</code> = [{mult 1, min, max, mph (0 bila &ge; max)}]; <code>hard</code> = constrain Y; <code>nd</code> dari dialog (bawaan 1&times;1&times;1); <code>surpac</code> = sudut asli & waktu run.'],
    ['Uji kecocokan', '<code>SLOG.ujiJalan</code>: run beratribut = kolom acuan (<code>SLOG.kolomAcuan</code>) dikelompokkan per set parameter; tiap set &rarr; <code>meRun</code> penuh (<code>ME.opt.force</code> sementara) pada domain terpilih (ME.sel sementara); '
     'salinan <code>&lt;unsur&gt;_est</code> disimpan; korelasi dihitung pada blok yang diisi semua set (<code>rS</code>), cakupan = blok terisi / maks. Sesudahnya: <code>d.est</code> & <code>ME.sel</code> dipulihkan, '
     '<code>ME.store.runs</code> dipotong ke panjang awal, rekomendasi = rS tertinggi (seri &rarr; run terbaru), jejak jalur.']]))

B.append('<h3>8.6 Reporting BM: cara Surpac sebagai bawaan, proporsi volume terhadap permukaan (BM 0.24.68 / DH 0.24.81)</h3>')
B.append(D.tabel(['Bagian', 'Cara kerja'], [
    ['Aturan', 'Semua pilihan yang punya padanan Surpac memakai cara Surpac sebagai bawaan (angka diaudit terhadap report Surpac); cara GC-Ex tetap tersedia sebagai pilihan. '
     'Bawaan <code>rpDef</code>: <code>sfrac:false</code>, <code>sfN:4</code>; Block Model <code>frac:false</code> (dulu <code>true</code>).'],
    ['Jangkauan permukaan', '<code>rpSurf</code> = TIN saja (<code>TINZ.of</code>, sama dengan tampilan); di luar segitiga = <code>null</code>. <code>rpRun</code> memaksa '
     '<code>tzT = pzT = true</code>: blok di luar jangkauan topografi / pit / DTM masuk <code>nOut.ext</code>, apa pun sumbernya (termasuk <code>RP.ovr</code> dari '
     '<code>rppit.js</code>). Dulu IDW mengisi &plusmn;30 m di luar selubung TIN dan blok yang lebih jauh lolos tanpa diuji. Padanan Python <code>gcex_backend/laporan.py</code> ikut.'],
    ['Proporsi permukaan', '<code>web-src/rpsfrac.js</code> (<code>RPSF.make</code>): telapak blok dibagi n&times;n kolom; tiap kolom: selang Z = [maks(pit, DTM <i>di atas</i>), '
     'min(topografi, DTM <i>di bawah</i>)], kolom di luar jangkauan = 0; proporsi = rata-rata panjang irisan selang dengan [dasar, atap] blok / tinggi blok. Cache per kolom (0,05 m). '
     'Dikalikan dengan <code>sb_frac</code> bila keduanya aktif. Bila <code>o.sfrac</code>, uji titik pusat permukaan dilewati (blok yang pusatnya di luar tetap bisa terhitung sebagian).'],
    ['Metode tonase', '<code>rpmetode.js</code>: cara GC-Ex = <code>frac</code> + <code>sfrac</code> sekaligus; tab aktif bila ada <code>sb_frac</code> atau batas permukaan.'],
    ['Uji', '<code>tools/uji/uji_rp_permukaan.py</code>: bidang miring sebagian, kedua aplikasi; cara Surpac = 750 blok (build lama 1.460), cara GC-Ex = 744.000 m&sup3; analitis.'],
]))

B.append('<h2>9. Dua jalur estimasi: vein dan berlapis</h2>')
B.append(fig(F3, 'Vein dan endapan berlapis dikerjakan mesin yang berbeda, dengan wadah domain dan ruang '
                 'hitung yang berbeda pula.'))
B.append('<p>Pertanyaan yang sering muncul: <i>bagaimana aplikasi tahu tipe deposit saat estimasi?</i> '
         'Jawabannya: tidak perlu tahu. Pembedanya struktural, bukan deteksi otomatis. Domain vein adalah '
         '<b>solid 3D</b> dan diestimasi pada koordinat asli; lapisan laterit adalah <b>permukaan atap dan '
         'lantai</b> yang diratakan dulu (unfold) sebelum variogram dihitung, supaya arah vertikal pelapukan '
         'tidak tercampur ke arah mendatar. Yang tidak mungkin dilakukan adalah mengestimasi vein memakai '
         'mesin laterit atau sebaliknya — dan itu memang disengaja.</p>')
B.append('<p><b>Sesar 3D.</b> Bidang sesar dapat dicatat beserta dip, offset dan urutan umurnya '
         '(<i>pre</i>, <i>syn</i>, <i>post</i>). Sesar <i>post</i>-mineralisasi dengan offset membuat data '
         'dipulihkan dulu sebelum pemodelan, lalu model dan hasil estimasi digeser kembali. Sesar juga dapat '
         'dijadikan <b>batas keras</b>: sampel tidak dipakai menyeberang bidangnya.</p>')

# ---- 7
B.append('<div class="page"></div><h2>10. Algoritme yang dipakai</h2>')
B.append('<p>Seluruhnya diimplementasikan sendiri berdasarkan literatur ilmiah terbuka; tidak ada kode dari '
         'perangkat lunak komersial yang disalin.</p>')
B.append(D.tabel(['Keperluan', 'Metode', 'Rujukan'], [
    ['Permukaan vein dari titik HW / FW', 'thin-plate spline / radial basis function, dengan pilihan '
     'interpolan <i>spheroidal</i>', 'Duchon 1976; Carr dkk. 2001'],
    ['Estimasi kadar', 'Ordinary Kriging, diskretisasi blok, pencarian elipsoid bertingkat (pass)',
     'Matheron 1963; Journel &amp; Huijbregts 1978'],
    ['Variografi', 'variogram eksperimental berarah, kipas arah, model nugget + struktur', 'idem'],
    ['Permukaan isosurface', 'marching tetrahedra', 'Doi &amp; Koide 1991'],
    ['Endapan berlapis', 'unfold proporsional atau dari atap; opsi akumulasi 2D (tebal &times; kadar)',
     'praktik umum pemodelan laterit'],
    ['Geometri ore shoot', 'GT (kadar &times; tebal) per bor, kipas variogram di bidang vein, pitch / plunge / trend',
     'praktik umum vein geser']]))
B.append('<p>Mutu estimasi tiap blok dicatat sebagai atribut, bukan hanya kadarnya: <code>est_pass</code> '
         '(pass pencarian yang berhasil), <code>est_nsamp</code> (jumlah komposit), <code>est_sor</code> '
         '(slope of regression), <code>est_ke</code> (kriging efficiency), <code>est_kv</code> (kriging '
         'variance), serta <code>est_nhole</code>, <code>est_dmin</code> dan <code>est_spasi</code> yang '
         'menggambarkan kerapatan bor di sekitar blok.</p>')

# ---- 8
B.append('<div class="page"></div><h2>11. Kerangka blok AOI, estimasi waste &amp; proporsi volume</h2>')
B.append('<h3>11.1 Kerangka blok AOI</h3>')
B.append('<p>Block model dapat dibuat <b>tanpa acuan model lama</b>: grid persegi seluruh <i>area of interest</i> '
         '(ore dan waste), dipotong topografi aktif, dasar desain pit, rentang RL, dan poligon area. Permukaan yang '
         'dipakai sama dengan Reporting BM &mdash; permukaan segitiga (TIN) versi aktif bila ada, kalau tidak titik '
         'topografi / pit &mdash; sehingga volume yang dilaporkan konsisten dengan kerangka yang dibangun.</p>')
B.append('<p>Mode <i>isi kekosongan</i> mempertahankan block model aktif <b>utuh</b> beserta seluruh atributnya dan '
         'hanya membuat blok baru pada sel yang belum tercakup. Cakupan diuji per sel: setiap blok impor menandai '
         'semua sel AOI yang ditimpa kotaknya, jadi sub-blok maupun blok induk terbaca benar. Atribut kategori '
         '<code>AOI_ASAL</code> membedakan <code>impor</code> dan <code>kerangka</code>; blok kerangka berisi NaN '
         'pada atribut numerik dan kosong pada atribut kategori.</p>')
B.append('<p>Versi block model berjenis <code>aoi</code> menyimpan <b>parameter saja</b>, bukan bloknya; kerangka '
         'dibangun ulang saat versi itu diaktifkan. Batas aman 4 juta blok baru per pembangunan.</p>')
B.append('<h3>11.2 Mengapa waste dihitung terpisah dari ore</h3>')
B.append('<p>Di antarmuka, estimasi waste <b>tidak</b> terpisah: ia adalah bagian <b>&#9317;</b> di dalam menu '
         '<b>Model Estimation</b> (dan di dalam menu <b>Stratified-Laterite</b> untuk jalur berlapis), satu run, '
         'satu riwayat, satu block model keluar. Yang terpisah adalah <b>populasi estimasinya</b>, dan itu '
         'disengaja:</p>')
B.append(D.tabel(['Alasan', 'Akibat bila ore dan waste disatukan'], [
    ['<b>Stationaritas / hard boundary</b>', 'batas wireframe ore adalah lompatan kadar, bukan gradien. Satu '
     'populasi membuat kriging meratakan kadar melintasi batas itu: blok waste di luar vein terangkat oleh '
     'komposit vein, blok ore di dalam tertarik turun. Yang terukur bukan dilusi nyata melainkan <b>dilusi '
     'yang disebar interpolator</b> &mdash; justru hal yang dicegah oleh domaining'],
    ['<b>Dua populasi statistik</b>', 'komposit di dalam vein bermean tinggi, CV ~1,2&ndash;1,9, nugget tinggi; '
     'komposit waste mendekati batas deteksi dengan range jauh lebih panjang. Satu variogram tidak mewakili '
     'keduanya &mdash; karena itu ada pilihan <b>variogram WASTE sendiri</b> selain mewarisi variogram domain '
     'terdekat'],
    ['<b>Tujuan pelaporan berbeda</b>', 'hasil waste ditandai <code>domain_est = WASTE</code>, '
     '<code>est_type = 3</code> dan <b>tidak ikut</b> pelaporan sumber daya; kadarnya untuk dilusi, ore loss '
     'dan perencanaan pit. Angka yang dicampur menghilangkan pemisahan ini']]))
B.append('<p>Integrasinya tetap ada di tempat yang benar: tiap blok waste dikrige memakai <b>variogram dan '
         'elipsoid domain ore terdekat</b> selama jaraknya di dalam ambang, sehingga kontinuitas lokalnya '
         '<b>diwarisi</b> dari pemodelan ore, bukan ditentukan sendiri. Hanya blok yang terlalu jauh dari domain '
         'mana pun yang jatuh ke IDW (<code>est_pass = 9</code>).</p>')

B.append('<h3>11.3 Estimasi waste &mdash; jalur solid domain</h3>')
B.append(D.tabel(['Unsur', 'Aturan'], [
    ['Blok', 'blok block model aktif yang pusatnya <b>di luar semua</b> solid domain; opsional hanya di bawah '
     'topografi aktif dan/atau di dalam desain pit'],
    ['Sampel', 'komposit dari interval bor yang <b>tidak di-flag domain apa pun</b> (<i>hard boundary waste</i>), '
     'dengan panjang komposit dan top-cut tersendiri'],
    ['Variogram', '(a) variogram waste yang difit sendiri &mdash; dipakai untuk seluruh blok waste; atau '
     '(b) variogram <b>domain terdekat</b>, dicari dari komposit ber-flag tiap domain, bila jaraknya &le; ambang'],
    ['IDW', 'untuk blok yang jaraknya melebihi ambang, dan untuk blok yang sampelnya tidak cukup untuk kriging. '
     'Bobot 1 / jarak<sup>p</sup>, radius dan jumlah titik dapat diatur'],
    ['Penanda', '<code>domain_est = WASTE</code>, <code>est_type = 3</code>. Blok IDW: <code>est_pass = 9</code> dan '
     '<code>est_sor</code> / <code>est_ke</code> / <code>est_kv</code> = &minus;99']]))
B.append('<div class=box>Ketiga ukuran keyakinan dibiarkan &minus;99 untuk blok IDW dengan sengaja: <i>slope of '
         'regression</i> dan <i>kriging efficiency</i> dihitung dari model variogram, dan model itu tidak berlaku di '
         'tempat yang jauh dari domain. Angka yang dihitung dari model yang tidak berlaku lebih berbahaya daripada '
         'kolom kosong.</div>')
B.append('<p><b>Variogram waste sendiri.</b> Menu Geostatistik menerima populasi <b>WASTE (di luar semua domain)</b> '
         'pada bilah Domain, sehingga seluruh alat yang ada &mdash; statistik, variogram arah &amp; fan, fitting, '
         'KNA, uji estimasi &mdash; berlaku untuk populasi yang sama dengan sampel estimasi waste. Hasil fitting '
         'disimpan lewat <b>Simpan ke WASTE</b> (model variogram, elipsoid, pass, diskretisasi, top-cut, panjang '
         'komposit) dan ikut tersimpan di proyek.</p>')
B.append('<h3>11.4 Estimasi waste &mdash; jalur berlapis (laterit)</h3>')
B.append('<p>Jalur Stratified-Laterite punya penyimpanan (<code>SL.S</code>) dan mesin estimasinya sendiri, jadi '
         'waste-nya dikerjakan terpisah &mdash; dan di <b>ruang unfold</b>, karena pada endapan berlapis kadar '
         'berubah mengikuti kelengkungan permukaan, bukan jarak lurus 3D.</p>')
B.append(D.tabel(['Zona', 'Blok', 'Sumbu ketiga <i>unfold</i>'], [
    ['bawah', 'di bawah permukaan terbawah model', '<code>z_dasar(x,y) &minus; z_blok</code>'],
    ['atas', 'di atas kontak teratas, masih di bawah topografi aktif', '<code>z_blok &minus; z_atap(x,y)</code>'],
    ['(luar)', 'di luar cakupan grid permukaan', 'tanpa kerangka unfold &rarr; elevasi apa adanya (opsional)']]))
B.append('<p>Sampel: komposit dari interval yang <b>kodenya tidak dipetakan ke lapisan mana pun</b>; tiap komposit '
         'ditempatkan ke zona sesuai posisinya sendiri dan hanya dipakai untuk blok di zona yang sama. Metodenya IDW '
         'anisotropis (elipsoid r1/r2 horizontal searah azimut, r3 pada sumbu unfold) &mdash; bukan kriging, karena '
         'variogram sebuah lapisan berlaku di dalam lapisan itu dan di luar seluruh lapisan tidak ada domain yang '
         'variogramnya pantas diwarisi. Hasil: <code>sl_pass = 9</code>, <code>sl_ns</code>, dan kategori '
         '<code>sl_lapisan = WASTE (di luar lapisan)</code>. Blok di atas topografi adalah udara dan tidak ikut.</p>')
B.append('<div class=warn>Estimasi lapisan yang dijalankan ulang membentuk <code>SL.S</code> baru, sehingga estimasi '
         'waste laterit ikut terhapus dan harus dijalankan ulang sesudahnya.</div>')
B.append('<h3>11.5 Sub-blocking di batas solid &amp; atribut <code>sb_frac</code></h3>')
B.append('<p>Blok yang menyeberangi batas solid dapat dipecah <b>2 &times; 2 &times; 2</b>, berulang 1&ndash;3 '
         'tingkat. Pemecahan di ketiga sumbu bersamaan disengaja: <code>.mdl</code> Surpac adalah octree dengan '
         'tingkat yang sama di ketiga sumbu, sehingga blok anak tetap jatuh di kisi octree dan model masih bisa '
         'ditulis balik. Uji menyeberang memakai kisi 3 &times; 3 &times; 3 (27 titik) di dalam kotak blok. Batas '
         'ukuran minimum dihitung dari ukuran blok <b>dominan</b> dibagi 2<sup>tingkat</sup> per sumbu, sehingga '
         'sub-blok yang sudah ada tidak dipecah ulang. Atribut blok anak diwarisi dari induknya.</p>')
B.append('<p>Atribut <code>sb_frac</code> (0&ndash;1) menyimpan <b>proporsi volume</b> blok yang berada di dalam '
         'solid, dihitung dengan integrasi titik-tengah 10&sup3; = 1.000 titik per blok perbatasan. Reporting BM '
         'dapat menimbang volume &amp; tonase dengan atribut itu; blok berproporsi 0 tidak dilaporkan. Kadar tidak '
         'dikalikan proporsi &mdash; kadar rata-rata ditimbang tonase, yang sudah berproporsi.</p>')
B.append(D.tabel(['Pengujian', 'Titik pusat', 'Ditimbang <code>sb_frac</code>'], [
    ['Vein mendatar tebal 4 m, blok 5 m, tanpa pemecahan', '&minus;100%', '0,00%'],
    ['Sama, 1 tingkat pecah', '+25%', '0,00%'],
    ['Sama, 3 tingkat pecah', '&minus;6,3%', '0,00%'],
    ['Bola radius 30 m, blok 5 m, tanpa pemecahan', '+0,80%', '+0,02%']]))
B.append('<div class=box>Untuk <b>volume</b>, <code>sb_frac</code> yang menyelesaikan masalah; sub-blocking membaik '
         'tetapi berayun, karena pembulatan titik pusat tidak hilang hanya dengan memperkecil blok. Sub-blocking '
         'tetap berguna untuk resolusi <b>kadar</b> di dekat kontak dan geometri <b>dig block</b>. Sub-blocking '
         'mengubah posisi blok, jadi jalankan sebelum estimasi.</div>')

B.append('<div class="page"></div><h2>12. Klasifikasi keyakinan sumber daya</h2>')
B.append('<p>Di <b>Reporting BM</b>, GC-Ex dapat mengusulkan kelas Measured / Indicated / Inferred per blok '
         'dari atribut di atas, lalu melaporkan tonase dan kadar per kelas beserta kurva grade &times; tonase '
         'bertumpuk. Aturan bawaannya:</p>')
B.append(D.tabel(['Kelas', 'Syarat bawaan (semuanya dapat diubah)'], [
    ['Measured', 'pass &le; 1, komposit &ge; 12, SoR &ge; 0,75, <b>lubang bor berbeda &ge; 3</b>, '
     '<b>spasi bor &le; 25 m</b>'],
    ['Indicated', 'pass &le; 2, komposit &ge; 7, SoR &ge; 0,45, <b>lubang bor berbeda &ge; 2</b>, '
     '<b>spasi bor &le; 50 m</b>'],
    ['Inferred', 'blok terestimasi lainnya'],
    ['Belum terklasifikasi', 'blok tanpa estimasi']]))
B.append('<p>Dua syarat terakhir penting: jumlah komposit saja bukan ukuran kerapatan bor. Dua puluh komposit '
         'dari <b>satu</b> lubang bor tidak sama artinya dengan dua puluh komposit dari enam lubang — dan '
         'dengan aturan ini blok seperti itu jatuh ke Inferred, bukan Measured.</p>')
B.append('<div class=warn>&#9888; Ambang di panel adalah <b>usulan geostatistik yang dapat diulang, bukan '
         'keputusan klasifikasi</b>. Penetapan kelas tetap wewenang <b>Competent Person</b> sesuai KCMI / JORC, '
         'yang juga menimbang hal-hal yang tidak terbaca dari angka: kemenerusan geologi antar bor, keyakinan '
         'pada model domain, kualitas QAQC, ketersediaan data densitas, dan kelayakan penambangan.</div>')

# ---- 9
B.append('<div class="page"></div><h2>13. Laporan beberapa desain pit &amp; progres topo-ke-topo</h2>')
B.append('<p>Reporting BM memakai <b>satu</b> topografi dan <b>satu</b> desain pit: yang sedang aktif. Dua '
         'pekerjaan rutin karena itu tidak pernah menghasilkan angka berdampingan &mdash; membandingkan fase '
         'pit, dan menghitung material yang benar-benar tergali antara dua survei. Tab <b>&#9315; Pit &amp; '
         'progres</b> (ada di Drill Hole maupun Block Model) mengerjakan keduanya.</p>')
B.append(D.tabel(['Mode', 'Yang dihitung'], [
    ['Per desain pit', 'untuk tiap desain pit yang dicentang: blok di bawah <b>satu</b> topografi yang sama dan '
     'di atas desain pit itu. Satu baris per pit, plus baris <b>tambahan</b> = selisih terhadap pit sebelumnya'],
    ['Progres topo-ke-topo', 'blok di bawah topografi <b>lama</b> dan di atas topografi <b>baru</b> = material '
     'tergali antara dua survei; seluruh atribut kadar dapat dilaporkan sekaligus']]))
B.append('<p><b>Cara pemasangannya penting untuk dipercaya.</b> Modul ini tidak menyalin mesin perhitungan '
         'Reporting. Ia mengisi <code>RP.ovr</code> (permukaan atas / bawah), memanggil <code>rpRun()</code> '
         'milik aplikasi sekali untuk tiap target, lalu mengumpulkan hasilnya. Akibatnya semua batasan lain '
         '&mdash; domain, poligon, rentang RL, filter atribut, SG, <code>sb_frac</code>, daftar cut-off &mdash; '
         'berlaku apa adanya, dan angkanya pasti sebanding dengan laporan biasa. Satu-satunya yang diganti '
         'adalah permukaan.</p>')
B.append(D.tabel(['Hal', 'Perilaku'], [
    ['Sumber permukaan', 'Drill Hole: versi topografi / desain pit di <b>Data Spasial</b> (DXF 3DFACE / .dtm = TIN) '
     'dan wireframe di node Import Wireframe Geologi. Block Model: permukaan DTM di <b>Data Referensi</b> dan wireframe '
     'geologi. DTM segitiga dipakai persis seperti Surpac; titik / kontur diinterpolasi IDW'],
    ['Di luar jangkauan DTM', 'blok tidak dihitung dan dilaporkan terpisah sebagai <i>di luar DTM</i>'],
    ['Kadar tambahan antar pit', 'logam tambahan &divide; tonase tambahan &mdash; bukan rata-rata dua kadar. '
     'Hanya benar untuk pit <b>bersarang</b>; untuk pit terpisah baca baris per pit saja'],
    ['Atas &amp; bawah tertukar', 'hasilnya 0 blok (bukan angka negatif) &mdash; itu petunjuk, bukan galat'],
    ['Blok dihitung', 'utuh menurut titik pusatnya, kecuali block model sudah dipecah dan <code>sb_frac</code> '
     'dinyalakan di tab &#9312;']]))
B.append('<p>Uji yang dijalankan sebelum rilis membandingkan hasil kedua mode dengan hitungan <b>bebas</b>: '
         'jumlah blok dihitung ulang langsung dari rumus kerucut pit data latihan, tanpa melewati jalur DTM. '
         'Pada data latihan selisihnya 0,4&ndash;0,5% (3.384 vs 3.398 blok; 16.103 vs 16.112; 2.439 vs 2.452) '
         '&mdash; berasal dari pembulatan segitiga DTM terhadap kerucut matematisnya, dan kedua aplikasi '
         'memberi angka yang sama persis.</p>')
B.append('<div class=warn>&#9888; Hasil progres topo-ke-topo adalah <b>block model di antara dua permukaan</b>, '
         'bukan timbangan. Rekonsiliasi sebenarnya tetap membandingkannya dengan tonase ROM / pabrik: survei '
         'topografi punya ketidakpastian sendiri, dan kadar blok adalah hasil estimasi.</div>')
B.append('<h3>Data latihan bawaan untuk Demo</h3>')
B.append('<p>Berkas data simulasi yang dipakai buku tutorial dititipkan <b>di dalam installer</b> '
         '(<code>resources/data-latihan</code>) dan dibaca lewat protokol internal '
         '<code>gcexfile://latihan/&lt;nama berkas&gt;</code>. Dua tombol memuatnya: <b>&#8681; Muat data '
         'latihan simulasi</b> di halaman import, dan <b>&#8681; Muat data latihan &amp; jalankan Demo</b> di '
         'menu Demo. Impornya memakai jalur yang sama dengan yang dipakai pengguna '
         '(<code>SA.slotFile</code> / <code>SA.addSp</code> / <code>SA.bmPick</code> / <code>SA.go</code>), '
         'lalu permukaan desain pit &amp; survei bulanan masuk lewat jalur pengguna juga: Drill Hole '
         '<code>spAdd</code> (versi Data Spasial; topografi aktif &amp; centang overlay dipulihkan sesudahnya), '
         'Block Model <code>mdImport(&hellip;, \'surf\')</code> ke Data Referensi; wireframe Leapfrog '
         '<code>mdImport(&hellip;, \'geo\')</code> &mdash; jadi tidak ada jalur baca kedua yang bisa berbeda hasilnya.</p>')
B.append(D.tabel(['Aplikasi', 'Berkas yang dititipkan'], [
    ['Drill Hole', '<code>SIM_collar / survey / assay / geologi.csv</code>, <code>SIM_topo_xyz.csv</code>, '
     '<code>SIM_BM_GC_kadar.csv</code> (model <b>berisi kadar</b>: demo tidak menjalankan estimasi), '
     '<code>QV_Lensa2_Leapfrog.obj</code>, <code>SIM_pit_fase1/2.dxf</code>, '
     '<code>SIM_topo_akhir_juni/juli.dxf</code>'],
    ['Block Model', '<code>SIM_BM_GC_kadar.csv</code>, <code>SIM_pit_fase1/2.dxf</code>, '
     '<code>SIM_topo_akhir_juni/juli.dxf</code>'],
    ['Tidak dititipkan', 'data laterit, vein bercabang, upsert, database rusak, QAQC &mdash; tetap dari '
     '<code>GC-Ex-&lt;versi&gt;_2_Data-Latihan.zip</code> pada Release, supaya installer tidak membesar '
     'tanpa guna']]))
B.append('<p>Langkah demo yang memang menjalankan perintahnya menampilkan <b>hasil sungguhan</b> di bilah '
         'bawah &mdash; jumlah interval yang diusulkan, jumlah string, volume solid, jumlah komposit &amp; CV, '
         'rekomendasi KNA, jumlah dig block beserta ton @ kadar, dan tonase per fase pit serta progres '
         'topo-ke-topo. Angkanya dibaca dari hasil perhitungan saat itu, bukan ditulis tangan di dalam '
         'program, sehingga bisa dicocokkan dengan buku tutorial. Langkah yang perhitungannya memakan waktu '
         'menit (upsert, Model Estimation, kerangka AOI, sub-blocking, estimasi waste, klasifikasi) '
         '<b>dijelaskan tanpa dijalankan</b>; angkanya ada di buku tutorial.</p>')
B.append('<h3>Tombol Demo</h3>')
B.append('<p>Tur otomatis di bilah atas kedua aplikasi disusun ulang mengikuti urutan <b>buku tutorial</b> '
         '(bukan urutan menu), keterangan tiap langkah dipendekkan menjadi satu kalimat, tempo bawaan '
         '0,55&times; durasi lama dengan pembaruan kursor 20 fps, dan pilihan kecepatan menjadi Pelan / Sedang '
         '/ Cepat / Kilat. Demo dijalankan di atas <b>data yang sedang terbuka</b>; langkah pertamanya '
         'menyebutkan dataset itu dan mengingatkan bila yang terbuka bukan data latihan simulasi. Langkah baru '
         'ditambahkan untuk menu yang belum pernah masuk demo: serap wireframe Leapfrog, kerangka AOI &amp; '
         'sub-blocking, estimasi waste, autorun, pemeriksaan dig block, preset kelas, ringkasan harian, laporan '
         'periode, dan laporan per desain pit / progres topo-ke-topo.</p>')

B.append('<h3>Kinerja 3D: lapisan yang tidak berubah tidak dikirim ulang (Drill Hole 0.24.42)</h3>')
B.append('<p>Plotly gl3d meng-update <b>setiap</b> lapisan setiap kali satu lapisan saja berubah. Block model latihan '
         '(66.147 blok, &plusmn;940 ribu titik sudut setelah sisi dalam dibuang) membuat setiap geser sayatan atau ganti '
         'centang &plusmn;1,3 s kerja JavaScript. <code>glskip_dh.js</code> melewati <code>update()</code> bila objek '
         'lapisan masukan sama persis dengan panggilan sebelumnya (properti tingkat atas identik per referensi, objek '
         'kecil per isi JSON, visibilitas dan <code>dataScale</code> adegan sama). Hasil ukur data latihan: gambar ulang '
         '1.290 &rarr; 158 ms, 3&times; klik Maju sayatan 3.690 &rarr; 494 ms. Maju / Mundur memakai jalur ringan '
         'slider (gambar penuh sekali setelah 350 ms); Ore Geometry tidak menghitung otomatis saat dibuka; '
         'Geostatistik memakai ulang hasil bila sayatan, data &amp; setelannya sama.</p>')
B.append('<h3>Jeda saat berganti panel / atribut &amp; kotak Kinerja (BM 0.24.47 / DH 0.24.54)</h3>')
B.append('<p>Hasil profil per node (<code>tools/uji/profil_panel.py</code>): berpindah panel sendiri murah (&lt; 35 ms). Yang mahal: '
         '(1) <b>ganti atribut warna</b> &mdash; Block Model membangun ulang geometri kubus per kelas (1&ndash;2 dtk pada 66 ribu blok), Drill Hole '
         'membangun ulang semua segmen + teks hover (1&ndash;3 dtk pada 1.600 hole) lalu <code>Plotly.react</code> &plusmn;1 dtk; di Drill Hole '
         'klik atribut sempat memanggil <code>updatePlot</code> dua kali (mode lintasan + nilai) &mdash; kini sekali (<code>trajModeDiam</code>); '
         '(2) <b>centang overlay</b> &mdash; dengan autorange rentang sumbu berubah &rarr; <code>dataScale</code> adegan berubah &rarr; semua lapisan '
         'diunggah ulang; (3) <b>resize</b> jendela / panel memicu <code>Plotly.Plots.resize</code> berulang; (4) dialog Satuan elemen memanggil '
         '<code>elRefresh</code> walau tidak ada yang diubah.</p>')
B.append('<p>Perbaikan: <code>glskip.js</code> kini dipakai kedua aplikasi dan membandingkan larik per <b>nilai</b> (panjang + checksum seluruh isi untuk larik angka, '
         '16 contoh untuk larik teks; <code>GLSKIP.debug=true</code> mencatat alasan tiap update di <code>GLSKIP.alasan</code>), bukan per referensi; setiap lapisan '
         'diberi <b>uid tetap</b> (hash nama + urutan ke-n; lapisan bor <code>dhTraj / dhNoData / dhCollar / dhLblAssay / dhLblHole</code>) karena tanpa uid Plotly '
         'mencocokkan lapisan lama-baru menurut posisi dalam daftar &mdash; menyisipkan satu overlay menggeser semua lapisan di belakangnya dan semuanya diunggah ulang; '
         '<code>dataScale</code> gl3d ternyata dihitung dari <b>batas data</b> semua lapisan (bukan rentang sumbu), maka ditambah lapisan dua titik tak kasatmata '
         '<code>_rentang</code> di pojok rentang tetap sehingga overlay di dalam kotak tidak mengubah skala (hasil: centang topo / collar di Drill Hole = 0 lapisan '
         'di-update; Block Model 10 dilewati, 1 di-update); '
         'rentang sumbu 3D <b>tetap</b> (<code>rngTetap</code>: gabungan rentang untuk filter hole / bench / sayatan yang sama; filter berganti = '
         'dihitung ulang seperti autorange; rasio aspek dari rentang tetap itu juga) sehingga centang overlay tidak memaksa unggah ulang; '
         'cache 6 pemilihan blok (<code>BX.scL</code>) + 6 geometri kubus (<code>BX.mcL</code>) dan 4 hasil <code>buildDH</code> (<code>DHCL</code>) '
         '&mdash; kembali ke atribut yang pernah tampil tidak dihitung ulang; reset &ldquo;polos&rdquo; <code>BX.sc={}</code> dari modul lain '
         '(unit, SG, laporan) tetap membuang semua cache; <code>uiResize</code> ditunda 40 ms dan dilewati bila ukuran tidak berubah; '
         '<code>elUnitDlg</code> hanya menyegarkan bila ada perubahan. Uji <code>tools/uji/uji_cache.py</code>: tanda tangan lapisan (nama, jumlah titik / '
         'segitiga, jumlah koordinat) + teks statistik dari cache harus identik dengan hitung ulang tanpa cache; <code>uji_glskip_gambar.py</code>: PNG adegan '
         'dengan dan tanpa glskip identik.</p>')
B.append('<p><b>Kotak Kinerja &amp; grafis</b> (<code>kinerja.js</code>, panel Tampilan &amp; performa) membaca <code>WEBGL_debug_renderer_info</code>: bila '
         'renderer SwiftShader / llvmpipe / Microsoft Basic Render / WARP, 3D digambar prosesor &mdash; ini penyebab paling mungkin bila jeda terasa di '
         'laptop walau pengukuran di atas sudah kecil. Kotak mencatat 12 aksi terakhir (sinkron, long task, panggilan Plotly) dan tombol <b>Salin laporan '
         'kinerja</b> menyalin teksnya. Catatan ukur: pada lingkungan uji tanpa GPU, waktu render (<code>(program)</code>) tidak mewakili; bandingkan '
         'waktu sinkron JavaScript.</p>')
B.append('<h3>Slicer, panel Assay, permukaan overlay, STR deskripsi teks (DH 0.24.56 / BM 0.24.49)</h3>')
B.append('<p><b>Permukaan topo &amp; pit tidak pernah tampil di 3D Drill Hole</b>: pengaman <code>Plotly.react</code> (<code>_gcexSafe</code>) membuang setiap '
         'mesh3d tanpa <code>i/j/k</code> &mdash; padahal permukaan topo / pit adalah mesh Delaunay (tanpa indeks). Kini mesh tanpa indeks sah bila &ge; 3 titik. '
         'Ditambah <code>ovWarna</code> (seragam / gradasi) + <code>ovTopoCol</code> / <code>ovPitCol</code> di panel Overlay kedua aplikasi; kunci <code>ovCache</code> memuatnya. '
         'Sekalian: uid lapisan hasil hitungan dihitung ulang tiap gambar (objek dari cache membawa uid lama &rarr; dua lapisan ber-uid sama &rarr; Plotly membuang satu).</p>')
B.append('<p><b>Slicer</b> (<code>ui4_dh.js</code>, menggantikan menu Sayatan &#9662;): mode baru <code>sMode=S</code> di <code>secGeom()</code> &mdash; bidang dari '
         '<code>slDip</code> / <code>slAz</code> (dip azimuth; strike = azimuth &minus; 90&deg;) melalui pusat <code>slX/slY/slZ</code> (koordinat asli); dip &lt; 0,5&deg; '
         'dikembalikan sebagai geometri H (plan, pos = elevasi) sehingga semua jalur lama (2D, slab bar, geostatistik) tetap berlaku; <code>slStep</code> = langkah '
         '<code>stepPos</code> terpisah dari <code>thick</code>. <code>window.SLICER</code> = {open, close, set(dip,az), pusat(x,y,z)} untuk Demo / uji. Pusat pandangan '
         'dihitung dari <code>scene.camera.center</code> (koordinat ternormalisasi &rarr; data). Riwayat geostatistik (<code>gsgGeo</code>) menyimpan nilai Slicer.</p>')
B.append('<p><b>Node Assay</b> &rarr; tab <code>Warna</code> (panel &ldquo;Assay &mdash; tampilan kadar&rdquo;: <code>elementFilter</code> &amp; <code>cutoff</code> pindah dari pData); '
         'sub-node unsur <code>info:1</code> (<code>ptree.js</code>: klik diabaikan, kelas <code>.info</code>); node <code>set.w</code> dihapus. Nomor lingkaran (&#9312;&hellip;) dihapus dari semua label; '
         'pengelompokan bagian Geomodeller (<code>key()</code>) kini mengenali judul h4, bukan nomornya; <code>uiSecTabs</code> membuang nomor dari label tab.</p>')
B.append('<p><b>STR biner Surpac</b> (<code>bigline.js readStrS</code>): rekaman = <code>[0x00][int32 string][Y][X][Z]</code> 29 byte lalu <b>deskripsi teks berpanjang bebas</b> '
         '(&ldquo;,2&rdquo;, &ldquo;,Lensa A&rdquo;) sampai byte 0x00 berikutnya; 4 byte awalan sesudah header; 29 byte nol = pemisah string; bantalan nol + END. '
         'Pembaca lama (deskripsi 8 byte biner per kolom, rekaman tetap) tetap sebagai cadangan <code>strTetap</code> bila &gt; 50 % rekaman tidak sah. '
         'Uji <code>uji_str_desc_teks.py</code>: biner-teks = teks = biner-lama, kedua aplikasi. Garis plan bor utuh (tanpa putus-putus) di 3D dan peta.</p>')
B.append('<p><b>Block Model besar</b>: <code>bxTraces</code> memakai <b>LOD</b> bila blok terpilih &gt; <code>bxLim3D()</code> &mdash; sel = ukuran blok induk terbesar &times; faktor '
         '2<sup>k</sup> (dinaikkan sampai jumlah sel &le; batas), kelas per sel = dominan menurut bobot volume, model tiruan <code>mm</code> dialirkan ke pembangun kubus yang sama '
         '(culling sisi bersama, potongan flitch) sehingga seluruh model &amp; semua kelas tampak; <code>BX.lim3d={shown,tot,lod,f,nAsli}</code>, legenda memakai <code>nAsli</code>. '
         'Dulu kelas yang tidak muat disembunyikan. Drill Hole masih memakai sampel titik (<code>BXCAP</code>) untuk kasus yang sama. '
         '<b>Jangkar area</b>: <code>SA.go</code> hanya memanggil <code>ab()</code> untuk file spasial yang overlap dengan collar atau (tanpa collar) block model; titik file yang tidak '
         'overlap dibuang (<code>out.length=_ob</code>); <code>SA.readLinesInto</code> tidak lagi memanggil <code>ab</code> per titik (mengembalikan x0..z1; <code>bigline_patch</code> memberi '
         '<code>segs.forEach</code> tiruan dua pojok). <code>SA.reAnchor(m)</code> (BM): jangkar proyek tersimpan &gt; 100 km dari batas block model dan tanpa collar &rarr; '
         '<code>D.anch</code> = batas model, titik topo / pit &gt; 50 km dibuang, simpan proyek + work, <code>location.reload()</code>.</p>')
B.append('<h3>Resolusi permukaan &amp; ortho, penyamaan BM &harr; DH (BM 0.24.50 / DH 0.24.57)</h3>')
B.append('<p><b>TIN penuh</b> (<code>web-src/tinhr.js</code> + <code>delaunator.min.js</code>, ISC): permukaan topo &amp; pit dibangun SEKALI per sumber titik dari seluruh titik '
         '(cap 400 rb; lebih dari itu satu titik per sel), segitiga sliver di tepi (sisi &gt; 8&times; median) dibuang, lalu trace memakai <code>i/j/k</code> tetap &mdash; Plotly '
         'tidak men-triangulasi lagi per zoom, glskip bisa melewatinya. Dulu: mesh tanpa indeks dari 15 rb titik terdesimasi (survei 33 rb titik tampil separuh). '
         'Cadangan otomatis ke cara lama bila Delaunator tidak ada. <code>TIN.info()</code> untuk diagnosis.</p>')
B.append('<p><b>Ortho</b>: Resolusi bawaan <b>Otomatis</b> (nilai 0) = <code>HR.resFor</code> dengan anggaran menurut profil Kinerja (<code>HR.anggaran()</code>: Hemat 300 rb, '
         'Seimbang 800 rb, Penuh 1,5 jt titik; batas <code>nx*ny</code> di <code>orthoTrace</code> ikut), tidak lebih halus dari piksel ortho; dulu bawaan 2 m. '
         '<b>Zoom kamera 3D</b> kini dipakai untuk memperkirakan extent tampilan (<code>HR.fromCamera</code>: pusat kamera &rarr; koordinat data, lebar &prop; jarak mata / 2,165, margin 1,8&times;) '
         'karena rentang sumbu tetap tidak lagi berubah saat zoom; <code>HR.attach</code> memasang pada <code>#plotDiv</code>. Zoom masuk = area kecil = resolusi lebih halus pada anggaran sama.</p>')
B.append('<p><b>Penyamaan BM &harr; DH</b>: Drill Hole kini memakai LOD sel untuk block model &gt; 120 rb blok (dulu sampel titik), <code>SA.reAnchor</code> dan pengecualian file spasial '
         'tidak-overlap juga ada di DH; Block Model mendapat <b>Slicer</b> (<code>sec_bm.js</code>, mode <code>sMode=S</code> di <code>secGeom</code>, langkah Demo <i>Slicer</i>). '
         'Reporting Block Model BM (<code>rpbm.js</code>) adalah port langsung dari Reporting BM Drill Hole: bagian, filter, constraint dan hasilnya sama; perbedaan hanya label '
         '(BM: tinggi / RL acuan flitch &amp; tombol = flitch aktif; DH: Densitas, Unsur divalidasi).</p>')
B.append('<h3>Solid Vein Aktual (trial) &mdash; Block Model 0.24.51</h3>')
B.append('<p>Modul <code>web-src/svein_bm.js</code> (hanya Block Model; terdaftar di <code>EXTRA</code> <code>build.py</code>), panel <code>#pSV</code> / tab <code>SV</code>, '
         'node Project Tree <code>sv</code> dari <code>svTree()</code> (dipanggil <code>ptree_bm.js</code>). Data di <code>BX.ui.sv = {per:[{id,name,from,to,polys:[{top,bot,pts,src,on}],par,res}],cur,filt}</code> '
         '&mdash; ikut proyek seperti <code>amData</code>; geometri hasil tidak disimpan, dibangun ulang (<code>SV.build</code>) saat diperlukan. Titik atap = <code>amD().ptsR</code> (satu sumber dengan As-Mined).</p>')
B.append('<p><b>Algoritma (mengikuti Surpac).</b> (1) Ring tiap poligon dibuat berlawanan jarum jam, Z sudut = IDW titik atap dalam radius &amp; pita RL flitch (atau RL atas flitch). '
         '(2) Poligon dua flitch <i>berurutan</i> dipasangkan bila <code>dPoly</code> (jarak datar tepi-ke-tepi, 0 bila bertumpuk) &le; jarak sambung maks; flitch kosong memutus. '
         '(3) Komponen 1&ndash;1 langsung di-loft; 1&ndash;n / n&ndash;1: ring pemilik dibelah garis bagi tegak lurus sumbu centroid anak (<code>splitRing</code>, titik potong disisipkan ke semua ring yang memuat sisi itu supaya tidak ada T-junction). '
         '(4) <code>loft</code> = <i>triangulate between segments</i>: tanpa resample, dynamic programming di kisi (m+1)&times;(n+1) dengan biaya luas segitiga (minimum surface area), + kuadrat diagonal (equi-angular) atau + selisih posisi keliling (proporsional); semua titik awal dicoba. '
         '(5) Tutup atas = ear clipping (<code>ears</code>), opsional disisipi titik pick-up di dalam poligon + Lawson flip sisi dalam (<code>refine</code>); pulau terbawah: dinding tegak ke RL bawah flitch + tutup bawah. '
         '(6) Validasi per pulau (<code>edges</code>): tiap sisi berarah harus punya pasangan berlawanan tepat satu; volume = jumlah tetrahedron bertanda (<code>volume</code>), orientasi dibalik bila negatif.</p>')
B.append('<p><b>Tampilan.</b> Garis poligon digambar lewat pembungkus <code>dgTraces</code> (3D &amp; plan 2D) selama centang node menyala; titik atap hanya saat node <code>sv</code> aktif / mendigit. '
         'Solid: bila <i>Daftarkan ke Wireframe geologi</i> menyala masuk <code>MD.models</code> (<code>jenis:geo</code>, tanda <code>sv</code>/<code>svn</code>, ikut <code>SA.mdPack</code>) sehingga tampil di 3D, sayatan 2D dan daftar domain Reporting; bila mati tetap digambar langsung sebagai <code>mesh3d</code>. '
         '<code>SV.lihat()</code> mengubah kotak batas vein ke koordinat kubus adegan Plotly (rentang sumbu &times; rasio aspek) lalu menyetel <code>scene.camera</code> center / eye. '
         'Digitasi memakai mesin <code>DG</code> dengan penanda <code>DG.svm</code>: <code>dgSnapHook</code> snap ke titik atap, <code>dgFinish</code> dibelokkan ke periode (tidak masuk daftar string / dig block). '
         'Ekspor: DTM (OBJECT / TRISOLATION per pulau, indeks tetangga) + STR, DXF 3DFACE, CSV. Uji: <code>tools/uji/uji_solid_vein.py</code> (prisma volume eksak, pulau terpisah, flitch kosong, cabang, cekung 3 metode, atap pick-up, tampil 3D, baca-ulang DTM, digit &amp; simpan).</p>')
B.append('<p><b>0.24.52 &mdash; sesudah uji pick-up nyata.</b> Titik atap membawa nama file (<code>q.f</code> dari <code>amPtsFile</code>; dulu CSV dikelompokkan menurut kolom kode). '
         '<code>SV.flParse(nama)</code> membaca RL flitch dari pola <code>_&lt;atas&gt;_&lt;bawah&gt;_</code> (tanda hubung = koma desimal), isian tabel menimpanya (<code>filt.fl</code>); <code>ptsLv(top)</code> = titik file ber-flitch itu (file tanpa flitch: pita Z lama). '
         '<code>zRoof</code>: titik berimpit &le; 2 cm memberi Z persis. <code>SV.outline(Q, L)</code> = alpha shape: Delaunay (<code>Delaunator</code>), buang segitiga bersisi &gt; L, sisi yang dipakai satu segitiga dirangkai jadi loop (belokan paling kiri di titik jepit), lubang &amp; serpihan &lt; 1 m&sup2; dibuang. '
         'Catatan: <code>sArea()</code> modul ini negatif untuk loop berlawanan jarum jam. Bawaan <code>dmax</code> 3 m.</p>')
B.append('<p><b>0.24.53 &mdash; berdiri sendiri.</b> Titik atap pindah ke <code>BX.ui.sv.pts</code> (tidak lagi <code>amD().ptsR</code>); pembaca <code>SV.bacaCsv</code> / <code>SV.importFiles</code> (upsert per nama file); <code>fromAM</code> / <code>fromDB</code> dihapus. '
         'Penyunting titik sendiri: <code>SV.edit(id)</code> / <code>SV.edDone(batal)</code>, kanvas <code>#svCv</code>, peristiwa mouse ditangkap di <code>#plotDiv</code> (capture) hanya saat mengenai titik / pegangan tengah sisi. '
         '<code>p.stale</code> menandai solid usang. <code>polysOf(p)</code> + <code>par.kum</code> = bangun kumulatif lintas periode. '
         'Tampalan poligon satu flitch: luas diukur dengan kisi di irisan kotak batas, volume ganda = luas &times; (atap rata-rata terendah &minus; RL bawah), masuk <code>res.ovl</code> dan peringatan; geometri belum digabung.</p>')
B.append('<h3>As-Mined sesudah uji data nyata &mdash; Block Model 0.24.54</h3>')
B.append('<p>Modul <code>web-src/amnyata.js</code> (BM saja, sesudah <code>amroof.js</code> di <code>EXTRA</code>) membungkus fungsi As-Mined yang ada: '
         '<code>amBndFile</code> (CSV / TXT ditangani di sini: <code>AMN.csvPts</code> &rarr; satu poligon, <code>AMN.nama(nama)</code> &rarr; <code>{top,bot,date,pit}</code>, '
         'diteruskan sebagai argumen ketiga <code>amBndAdd(pts,name,opt)</code>; titik juga masuk <code>amD().ptsR</code> dengan upsert per nama file), '
         '<code>amR</code> (sekali per proyek: bila <code>R.cls</code> masih persis bawaan, <code>AMN.pakaiKelas</code> mengisi dari <code>AMN.kelasModel()</code> &mdash; '
         'rumus IIF di <code>BX.m.mdl.expr</code> yang kini disimpan pembaca .mdl, cadangan: kadar terendah tiap kategori kolom material), '
         '<code>am3Traces</code> (<code>AMN.solid(I)</code>: ring poligon dirapatkan + kisi dalam, Delaunay, segitiga bertitik berat di luar poligon dibuang, '
         'Z atas = <code>amRoofFn</code>, Z bawah = <code>amFloorFn</code> / RL bawah; <code>AM3.sol</code> bawaan menyala, <code>AM3.sb</code> bawaan mati), '
         '<code>am3Toggle</code> (zoom otomatis) dan <code>am3Box</code> / <code>amPanel</code> (tombol &amp; keterangan). <code>AMN.zoom(semua)</code>: 3D = <code>scene.camera</code>, plan = rentang sumbu. '
         '<code>bxDefUI</code> memilih <code>sgCol</code> otomatis (nama sg / sg&lt;n&gt; / density / dens / bd, nilai tengah 1,2&ndash;5). Uji: <code>tools/uji/uji_asmined_nyata.py</code>.</p>')
B.append('<p><b>Solid Vein &mdash; gabung tampalan.</b> <code>SV.polyUnion(A,B)</code>: kedua poligon disearahkan, sisi dipecah di titik potong dan di titik lawan yang menempel, '
         'potongan di luar poligon lawan dirangkai (sisi berimpit searah dipakai sekali, berlawanan dibuang; belokan paling kanan di simpang), loop terluar dipakai. '
         'Di <code>SV.build</code> langkah 1c: kelompok tampalan (&ge; 0,5 m&sup2;) digabung, Z ring = maksimum permukaan anggota yang memuat titik itu (IDW sudut-sudut anggota); '
         'gagal menggabung &rarr; tetap terpisah + peringatan. <code>par.gab=false</code> mematikan.</p>')
B.append('<p><b>Data latihan di aplikasi terpasang (BM 0.24.55 / DH 0.24.58).</b> Skema <code>gcexfile</code> terdaftar <i>standard</i>: bagian pertama sesudah <code>//</code> adalah host dan tidak masuk <code>pathname</code>. '
         'Penangan di <code>electron/main.js</code> memeriksa <code>pathname.startsWith(\'latihan/\')</code>, jadi alamat yang benar adalah <code>gcexfile://open/latihan/&lt;nama&gt;</code> (<code>DLAT.url</code> di <code>demodata.js</code>), bukan <code>gcexfile://latihan/&lt;nama&gt;</code> yang selalu 404. '
         'Uji peramban tidak melewati jalur ini; <code>tools/uji/uji_url_latihan.js</code> meniru penangan untuk menjaganya.</p>')
B.append('<p><b>Jangkar tanpa bor (DH 0.24.59).</b> <code>SA.boot</code>: <code>ANCH = D.anch || (tanpa collar ? SA.anchSpasial(D) : null)</code> &mdash; batas topografi + desain pit (titik lolos <code>SA.koordOk</code>). '
         'Tanpa ini proyek yang database bornya dihapus (<code>PTD.drop(\'all\')</code>) memakai <code>offX/offY</code> = 0 dan <code>G</code> = 0&ndash;100 m, sehingga <code>OV.topoC</code> / <code>OV.pitC</code> (overlay dipotong area kerja) kosong. Uji: <code>uji_hapus_bor_overlay.py</code>.</p>')
B.append('<p><b>Slicer DH 0.24.60.</b> <code>ui4_dh.js</code>: <code>data-pre=line</code> &rarr; <code>s3Open()</code> (kotak <code>#s3Box</code>); <code>#btn2d</code> / <code>#btnSec3</code> dilabel ulang "Tampilan 2D / 3D" dan kliknya ditangkap di fase capture pada <code>#secMenu</code> '
         '(<code>if(in2&amp;&amp;!VIEW2D)toggle2D(); if(in3&amp;&amp;VIEW2D)toggle2D()</code>) sehingga <code>onclick</code> lama tidak jalan; butir <code>data-a=set</code> dihapus. '
         'Baris <code>showLabel / showCollar / showTraj / showNoData</code> di panel View diberi <code>display:none</code> (tetap dibaca <code>updatePlot</code> &amp; preset). '
         'Plotly tersemat: <code>k.pick</code> (gl-mesh3d) kini <code>if(!r)return null</code> bila <code>this.cells[e]</code> tidak ada. Uji: <code>uji_slicer_tombol_dh.py</code>.</p>')
B.append('<p><b>DH 0.24.65.</b> <code>nyata_dh.js</code>: <code>NY.mdlSynth(m)</code> (header .mdl Version 4.0 sintetis, origin = origin grid AOI bila sejajar / pojok blok, root = sel &times; 2<sup>L</sup>, L &le; 19) dipakai <code>bxMdlExport</code> bila <code>m.mdl.hraw</code> tidak ada; <code>NY.planeSec()</code>; <code>NY.status()</code> (POP.win). <code>nyata_patch.py</code> (sesudah gm2 &amp; mecls): kolom ME <code>idw</code> &rarr; atribut <code>&lt;el&gt;_id2</code> (<code>meIdw</code>, jarak anisotropik elipsoid). Parameter domain <code>P.sr</code> (elipsoid pass 1, m) &amp; <code>P.lim={d,pre}</code> (<code>meLimOf/meLimSel</code>), <code>parChg</code> memaksa estimasi ulang domain. <code>imBuild</code>: <code>st.nab</code> (flag di atas topografi), <code>st.far15/far30</code>, <code>tCapV</code> = 1,5 &times; tebal kontak (P.tCap), titik sambung = titik tengah kontak induk, maks <code>max(3,nc)</code>. <code>imFlagList(d)</code> (selubung &rarr; GM.envF). <code>meComps</code> selubung soft: zona transisi <code>softD</code>, top-cut vein. <code>gsNugDH</code>, mayor &ge; semi; <code>M.dSet</code> &rarr; Cn = mD. AOI <code>ox/oy/oz</code>. <code>SA.textAuto</code> (UTF-8 ketat &rarr; Windows-1252, <code>SA.encNote</code>). <code>gmMergeKey</code> (kontak &lt; 2 m dirata-rata). Uji: <code>uji_nyata_dh.py</code>.</p>')
B.append('<p><b>BM 0.24.64 / DH 0.24.63.</b> <code>popout.js</code> bersama: <code>POP.win(id,judul,html)</code>; DEF dengan <code>hd(host)</code>/<code>grab(hd)</code>, alias gaya <code>css</code>; bagian <code>db.list</code> (<code>#dbBody .dbsub</code> Running grade), <code>rp.res</code> (<code>.rptabs</code> saat <code>RP.sec===\'2\'</code>), <code>sv.poly</code>; <code>#gsPanel.gxfloat</code>. <code>SV.repHitung(p)</code>: per pulau indeks grid segitiga, uji paritas sinar +Z, blok utuh titik pusat; pengelompokan cut-off / pulau / <code>levels(p)</code>. DH <code>holedata_dh.js</code> (<code>HD.buka/render/tsv</code>; <code>plotly_click</code> mencari id collar terpanjang di nama trace / hover). Uji: <code>uji_popout_bm.py</code>, <code>uji_popout_dh.py</code>.</p>')
B.append('<p><b>BM 0.24.63.</b> <code>AMK.f.mode</code> (hari / minggu / bulan / rentang, <code>f.date2</code>) &rarr; <code>AMK.range()</code>; <code>AMK.rows()</code> menyaring <code>x.date</code> dalam rentang; <code>AMK.lockRows</code> hanya bila <code>AMK.harian()</code>. <code>popout.js</code>: def <code>am.db</code> bawaan menyala; <code>salinCss()</code> menyalin aturan <code>#amBody</code>/<code>#svBody</code> ke <code>.gxpb.h-amBody</code>/<code>.gxpb.h-svBody</code> (style <code>#gxpoCss</code>).</p>')
B.append('<p><b>BM 0.24.61.</b> <code>AMK.inline()</code> disisipkan di bagian <i>Register untuk database</i> (<code>am2.js</code>); <code>amRegRows</code> dibungkus: <code>AMK.f.date</code> terisi &rarr; hanya baris <code>AMK.rows()</code>; <code>AMK.keXl()</code> menggulir ke <code>#amXlWrap</code>. Kunci otomatis: <code>AMK.lockRows(rows,via)</code> dari pembungkus <code>amRegCopy</code> / <code>amRegCsv</code> (lewat <code>gxSimpan</code> sekali, hanya bila tidak dibatalkan) / <code>amXlSend</code> (<code>AM.xl.res</code>); hanya bila <code>AMK.f.date</code> terisi. Pop-up <code>amkPop</code> &amp; node <code>reg.tgl</code> dihapus. <code>popout.js</code>: <code>am.reg</code> bawaan menyala; jendela muncul saat judul bagian mulai terlihat (<code>offsetParent</code>) atau tombol ditekan; observer juga memantau atribut <code>data-f</code>/<code>hidden</code>/<code>class</code>/<code>style</code>.</p>')
B.append('<p><b>BM 0.24.60 / DH 0.24.62.</b> <code>tinz.js</code>: indeks CSR (<code>Int32Array</code>), <code>opt.faktor</code> (buang sliver = <code>TIN.faktor</code>), <code>TINZ.of(o)</code> (WeakMap + panjang). <code>topoZ</code> dibungkus (TIN, cadangan <code>topoZ._idw</code>); <code>rpSurf</code> &rarr; <code>TINZ.of</code> + <code>rpSurfIdw</code> (BM <code>rpbm.js</code>, DH base); <code>SA.surfGrid</code> menimpa sel dengan TIN vertex string; <code>amFloorFn</code> TIN (<code>amFloorKey</code> + <i>tin</i>). <code>popout.js</code> (<code>POP.set(k,on)</code>, <code>POP.def</code>): MutationObserver pada <code>#amBody</code> / <code>#svBody</code>, simpul bagian dipindah ke <code>.gxpop</code>; <code>localStorage gcex_popout</code>. Uji: <code>uji_tinz.py</code>.</p>')
B.append('<p><b>BM 0.24.59.</b> <code>web-src/tinz.js</code>: <code>TINZ(P,{luar})</code> &rarr; <code>{f(x,y),nt,n}</code> (Delaunator; titik &lt; 1 mm disatukan; koordinat dikurangi titik pertama; indeks grid kotak segitiga; barycentric linear; di luar selubung <code>luar(x,y)</code>). Dipakai <code>amRoofFn</code> mode <i>pickup</i> (IDW lama = cadangan; <code>amRoofKey</code> + <i>tin</i>) dan Solid Vein <code>zRoof</code> (<code>zMode</code> <i>idw</i> = TIN, <i>idwr</i> = IDW radius) + permukaan gabungan. Uji: <code>uji_tinz.py</code>.</p>')
B.append('<p><b>BM 0.24.58.</b> <code>web-src/amkunci.js</code> (<code>AMK</code>): <code>amD().lock[\'tanggal|shift\']={t,ids,n,ton}</code>; pembungkus <code>amRun</code> menghitung semua poligon lalu mengembalikan <code>x.st</code> poligon terkunci (nilai beku), mengoreksi <code>AM.res[flitch].sum</code> (vol, t, gA, gO, ne, nf, el/elw) dan mempertahankan sel sesi sebelumnya; <code>amInfo</code> diberi <code>lk</code> / <code>lkBaru</code>, <code>stale=false</code> untuk yang terkunci. Penjaga <code>amBndDel</code> / <code>amBndOn</code> / <code>amEdShape</code> / <code>amPSet</code> (kecuali col, print, sid). <code>amBndAdd</code> &rarr; <code>AMK.cekTampal</code> &rarr; <code>AMK.diff</code> (pecah sisi di titik potong, sisi A di luar B + sisi B di dalam A dibalik, dirangkai; diverifikasi luas = luas A &minus; irisan sampel 160&times;160; lubang ditolak). Pop-up umum <code>AMK.pop(id,judul,html)</code> (<code>.gxpop</code>). Uji: <code>uji_am_kunci.py</code>.</p>')
B.append('<p><b>BM 0.24.57.</b> Solid Vein: flitch kerja <code>D().lv</code> milik menu sendiri &mdash; <code>lvB()</code>, <code>lvOn()</code>, <code>SV.view(top,bot)</code> (sayatan plan seperti <code>lyApply</code> tanpa <code>lySet</code>; <code>BX.ui.fl</code> dimatikan). <code>importFiles</code> / <code>fileOn</code> / <code>goLv</code> / <code>flSet</code> memakai level ini. CSV tanpa judul: baris pertama dibuang hanya bila kolom E/N-nya bukan angka. Uji: <code>uji_sv_flitch.py</code>.</p>')
B.append('<p><b>BM 0.24.56 / DH 0.24.61.</b> <code>web-src/mdlattr.js</code> &mdash; <code>mdlAttrs(u,p,na)</code>: runut-balik atas kandidat lebar nilai bawaan per tipe (integer 5/9/4/8/13, real 9/8/13/5/17, karakter teks+1/+0/+5/+9, tipe lain semuanya), sah bila seluruh sisa daftar terbaca dan kunci blok pertama (<code>key&amp;31 &le; 24</code>) masuk akal; byte ekor sesudah nilai tidak boleh huruf. '
         '<b>BM 0.24.67 / DH 0.24.80:</b> kandidat <code>d4</code>/<code>d8</code> (nilai lalu teks deskripsi berakhiran 0), <code>ds</code> (teks bawaan lalu deskripsi) dan deskripsi sesudah ekspresi kalkulasi &mdash; kolom <i>Description</i> Surpac yang terisi. '
         'Di BM disisipkan ke bagian import lewat penanda <code>/* @@MDLATTR@@ */</code> di <code>build.py</code> (EXTRA hanya jalan di viewer); di DH lewat daftar SHARED. '
         'As-Mined: <code>AMN.roofNear(B)</code> + pembungkus <code>amTraces2D</code> / <code>dgSnapHook</code> / <code>amRoofPts</code> (<code>amnyata.js</code>); tombol tampil lapisan <code>AMN.vis(\'vF\'|\'vR\')</code> &rarr; <code>amD().vF/vR</code>, disaring di pembungkus terluar <code>amTraces2D</code> + <code>dgSnapHook</code> (dipasang <code>setTimeout 0</code> setelah <code>amfloor.js</code>; kait titik as-mined dilewati dengan <code>AM.digOn=false</code> sementara); node <code>am.fl.*</code> diberi <code>tab:\'AM\'</code>, <code>flOpen</code> memanggil <code>PT.mau(null)</code> (pembungkus <code>lyApply</code> di <code>ptree_bm.js</code>: id kosong = pilihan tetap). Node <code>reg.db</code> &rarr; bagian <code>amh</code> "Register untuk database" di <code>am2.js</code>. '
         '<code>kinerja.js</code> membungkus <code>prompt/confirm/alert</code>; durasinya dikurangkan dari kolom sinkron &amp; long task. Uji: <code>uji_mdl_header.js</code>, <code>uji_bm_revisi_1011.py</code>.</p>')
B.append('<h3>Urutan Project Tree Drill Hole</h3>')
B.append('<p>1 Proyek &middot; 2 Data Spasial &middot; 2b Import Wireframe Geologi &middot; 3 Database Bor &middot; 4 Peta '
         '&middot; 5 Struktur Geologi &middot; <b>5b Ore Geometry</b> (referensi, sebelum pemodelan) &middot; 6 Geomodeller '
         'Vein / 6b Strata-Laterit &middot; <b>7 Geostatistik</b> (variogram sebelum estimasi) &middot; 8 Block Model &middot; '
         '9 Model Estimation &middot; 10 Validasi BM &middot; 11 Reporting BM &middot; 12 Layout &amp; Ekspor. Export database '
         'hanya di menu Database Bor; export .mdl hanya di menu Block Model.</p>')
B.append('<h3>Menu &#8943; dan baris + Tambah (kedua aplikasi, BM 0.24.42 / DH 0.24.47)</h3>')
B.append(D.bullets(
    '<b>Satu pintu menu: tombol &#8943;</b> di ujung baris node, selalu tampak (abu-abu tipis). Klik kanan pada Project Tree '
    'sengaja tidak membuka apa pun. Keyboard: tombol Menu / Shift+F10 pada node terpilih.',
    '<b>Perintah yang menambah isi node</b> tidak ada di menu &#8943;, melainkan baris biru <b>+ Tambah &hellip;</b> paling bawah '
    'di anak node (properti node <code>add:{t,fn}</code> atau <code>add:{t,items}</code> di <code>ptree.js</code>). Drill Hole: titik '
    'survey &amp; string, wireframe geologi, kampanye, plan bor, struktur, sesar, domain. Block Model: data referensi, '
    'wireframe geologi. Untuk wireframe, data referensi, kampanye dan CSV struktur tombol import di panel dihapus (satu pintu).',
    '<b>Pengecualian (tetap di panel, tanpa baris + Tambah)</b>: versi topografi / desain pit / orthofoto / block model di panel '
    '<b>Data Spasial</b> (Drill Hole), import titik pick-up CSV di panel <b>Peta (Mapping)</b> (Drill Hole) dan tombol simpan preset di kartu <b>Preset kelas kadar &amp; tujuan</b> (Block Model).',
    '<b>Data Spasial lewat &#8943; (BM 0.24.44 / DH 0.24.51)</b>: menu &#8943; node Data Spasial, Topografi, Desain pit dan Orthofoto membuka '
    'jendela pilih file dan memasukkan datanya <i>di tempat</i> (Drill Hole: versi baru; Block Model: tambah / ganti data), tanpa kembali ke layar Mulai. '
    'Block Model: <code>SA.spMasuk(role, mode, files)</code> memakai pembaca yang sama dengan layar Mulai lalu membangun ulang overlay.',
    '<b>Block model &amp; data bor lewat &#8943; (BM 0.24.45 / DH 0.24.52)</b>: &#8943; Block Model &rarr; <i>Import block model dari file&hellip;</i> '
    '(jendela pilih file &rarr; dialog pemetaan terisi). Drill Hole &#8943; Database Bor / Collar / Survey / Assay / Geologi &rarr; '
    '<i>Import &hellip; dari file (tambah / perbarui)&hellip;</i> (jendela pilih file &rarr; jendela upsert dengan file terpasang, '
    '<code>UP.openDengan(role, f)</code>). Tidak ada menu yang mengembalikan pemakai ke layar Mulai, kecuali <i>Import ulang</i> di menu Proyek.',
    '<b>Panel mengikuti node</b> (DH 0.24.48): node <b>Struktur Geologi</b> hanya menampilkan bagian struktur; node '
    '<b>Data referensi</b> hanya titik survey &amp; string (keduanya berbagi panel <code>#pModel</code>, dipisah oleh kelas '
    '<code>ref-st</code> / <code>ref-ref</code> di <code>ptree_dh.js</code>).',
    'Menu &#8943; berisi perintah atas isi yang sudah ada: tampilkan sebagai, jadikan aktif, ganti nama, export, pindahkan, hapus. '
    'Node yang menunya kosong tidak menampilkan &#8943;.'))

B.append('<h2>14. Topografi &amp; orthofoto resolusi tinggi</h2>')
B.append('<p>Orthofoto disusun menjadi <b>piramida LOD</b>: level 0 piksel asli, tiap level berikutnya '
         'merata-ratakan 2 &times; 2. Warna diambil dari level yang texel-nya sepadan dengan kerapatan '
         'tampilan, sehingga rata-rata area (anti-alias) dan tidak berkerlip. Resolusi <b>dan</b> luas mesh '
         'mengikuti area yang sedang terlihat, jadi zoom masuk makin detail dengan jumlah titik yang tetap. '
         'Di menu Peta, orthofoto dipotong sesuai tampilan dan dikirim setajam layar.</p>')
B.append(D.bullets(
    'Kotak <b>Resolusi (m)</b> di panel orthofoto kini berfungsi sebagai <b>batas paling halus</b>, bukan '
    'resolusi tetap.',
    'Tampilan disegarkan sekitar 0,3 detik setelah gerakan zoom / geser berhenti, bukan tiap frame.',
    'Mesh dibuat sedikit lebih luas dari layar supaya geseran kecil tidak menyisakan tepi kosong.',
    'Klik ganda / autoscale mengembalikan tampilan ke seluruh area.',
    'Tambahan memori untuk piramida kira-kira sepertiga dari piksel dasar.'))
B.append('<div class=box><b>Hasil laporan tidak berubah.</b> Grid elevasi cepat itu dipakai hanya untuk '
         'tampilan (menempelkan warna orthofoto ke topografi). Perhitungan Reporting BM, estimasi dan validasi '
         'tetap memakai fungsi elevasi aslinya.</div>')

# ---- 10
B.append('<h2>15. Format impor / ekspor</h2>')
B.append(D.tabel(['Keperluan', 'Masuk', 'Keluar'], [
    ['Data bor', 'CSV, Excel (header bebas)', 'CSV, Excel'],
    ['Block model', '.mdl (Surpac), CSV', '.mdl, CSV'],
    ['String / poligon', '.str (Surpac), .dxf', '.str, .dxf'],
    ['Permukaan / solid', '.dtm + .str, .dxf, .obj, .msh (Leapfrog)', '.obj, .dtm'],
    ['Topografi / desain pit', '.dtm, .str, .dxf, CSV / TXT / XYZ', '&mdash;'],
    ['Orthofoto', 'GeoTIFF, JPG / PNG + world file', '&mdash;'],
    ['Laporan', '&mdash;', 'CSV, Excel, gambar layout']]))
B.append('<p>Nama produk dan format pihak lain disebut semata-mata untuk menjelaskan kecocokan pertukaran '
         'data. Kecocokan diupayakan tetapi tidak dijamin, dan dapat berubah bila format mereka berubah.</p>')

# ---- 11
B.append('<h2>16. GC-Ex Block Model: flitch, dig block, as-mined</h2>')
B.append(D.bullets(
    '<b>Flitch</b> — block model dipotong per ketinggian kerja; Project Tree memberi subnode tiap flitch '
    'sehingga audit atau review dapat langsung memilih flitch yang dimaksud.',
    '<b>Dig block otomatis</b> — poligon dibentuk dari blok di atas cut-off, lengkap dengan hitungan '
    'kadar &times; tonase.',
    '<b>Digitasi manual</b> — menekan <b>Enter</b> menutup string secara otomatis, lalu poligonnya mendapat '
    'menu yang sama dengan hasil otomatis: edit bentuk, ubah warna, dan hitungan grade-tonase.',
    '<b>Additional flagging</b> — seluruh poligon dig block ikut di-flag bila komposit unsurnya melewati COG.',
    '<b>As-mined</b> — poligon hasil penambangan sebenarnya, dapat diedit bentuk maupun warnanya, dan '
    'hasil running-nya dapat digabung menjadi satu berkas <code>.mdl</code>.',
    '<b>Register poligon</b> — daftar seluruh poligon dengan String ID dan warna yang dapat diubah.'))

# ---- 12
B.append('<h3>15.1 Alat harian grade control (0.24.24)</h3>')
B.append('<p>Pemakai GC-Ex Block Model adalah <b>Junior Grade Control</b> dan <b>Short Term / Junior Mine '
         'Planner</b>, jadi alatnya ditujukan pada <i>Daily Ore Mining &amp; Grade Control</i> &mdash; bukan '
         'eksplorasi atau pemodelan. Karena itu Reporting Block Model <b>tidak</b> memuat klasifikasi sumber daya '
         '(Measured / Indicated / Inferred) maupun pengelompokan per domain estimasi; keduanya tetap di GC-Ex '
         'Drill Hole. Menaruhnya di alat harian hanya mengundang angka sumber daya terbit dari tempat yang bukan '
         'tempatnya.</p>')
B.append(D.tabel(['Alat', 'Cara kerjanya'], [
    ['<b>Pemeriksaan dig block</b>', 'Dijalankan sebelum dig plan terbit, dua tingkat: <b>CEGAH</b> (lebar minimum '
     'di bawah batas selektivitas alat, tonase nol, garis saling memotong, poligon tidak tertutup, tanpa tujuan '
     'material) dan <b>PERIKSA</b> (luas di bawah ambang, kadar kosong, nama ganda). Lebar minimum dihitung '
     '<i>rotating calipers</i> pada <i>convex hull</i> &mdash; jarak terkecil antara dua garis sejajar yang '
     'mengapit poligon, bukan perkiraan luas/keliling. Diuji: persegi 10&times;2 m &rarr; tepat 2,00 m; segitiga '
     'tipis &rarr; tepat 0,50 m'],
    ['<b>Ringkasan harian</b>', 'Satu halaman untuk flitch aktif: ton dan kadar semua unsur terpilih per material '
     'dan per tujuan, ditambah rencana (dig block) vs aktual (as-mined flitch itu) bila sudah dihitung'],
    ['<b>Preset kelas kadar &amp; tujuan</b>', 'Batas kelas, aturan tujuan material, lebar minimum alat dan ambang '
     'sulfida disimpan sebagai preset bernama di berkas proyek, supaya DS dan NS memakai batas yang sama persis. '
     'Memakai preset menghitung ulang material &amp; tujuan dig block yang ada (selalu dengan konfirmasi)'],
    ['<b>Rekap dig block</b>', 'CSV semua flitch kini memuat <b>semua unsur</b> terpilih + Metal tiap unsur + '
     '<b>centroid</b> poligon (titik berat, bukan titik tengah kotak pembatas) untuk dispatch / fleet system'],
    ['<b>Pembobotan <code>sb_frac</code></b>', 'Bila block model berasal dari Model Estimation Drill Hole dan pernah '
     'dipecah di batas solid, tonase &amp; volume ditimbang proporsi volume blok. Tanpa ini block model yang SAMA '
     'memberi tonase berbeda antara laporan Drill Hole dan Block Model. Pada data latihan (20,1% blok sebagian): '
     '8,05 juta ton dengan pembobotan vs 10,75 juta ton tanpa']]))
B.append('<h3>15.2 Laporan periode (mingguan / bulanan)</h3>')
B.append('<p>Menjumlahkan apa yang benar-benar tergali dari <b>register as-mined</b>: tiap poligon menyimpan '
         'tanggal, shift (DS / NS), pit, blok, RL flitch, kode ore dan tujuan material; tonase, volume dan kadarnya '
         'dihitung mesin as-mined dan tersimpan pada poligon itu. Agregasi kadar memakai penimbang tonase yang sama '
         'dengan register dan PDF rekonsiliasi, sehingga <b>angka laporan periode tidak pernah berbeda dari '
         'register</b>.</p>')
B.append(D.bullets(
    'Periode: minggu ini / minggu lalu / bulan ini / bulan lalu / kustom. Minggu dihitung Senin&ndash;Minggu (ISO).',
    'Pengelompokan: per tanggal, per minggu, per <b>shift</b>, per flitch, per tujuan material, per kode ore, per pit.',
    '<b>Target</b> ton (dan kadar) periode &rarr; pencapaian persen, berwarna: hijau &ge; 100%, jingga &ge; 90%, merah di bawahnya.',
    '<b>Tren</b>: per hari untuk laporan mingguan, per minggu untuk bulanan.',
    '<b>Pembanding</b> periode sebelumnya dengan panjang yang sama.',
    'Export CSV memuat tabel, total, target &amp; pencapaian, tren, dan periode pembanding.'))
B.append('<div class=box><b>Batasan yang disebut terang-terangan di antarmuka.</b> As-mined dihitung per flitch '
         'aktif, jadi poligon dari flitch yang belum pernah dihitung belum punya tonase. Laporan periode '
         '<b>tidak</b> menjumlahkannya diam-diam: jumlah poligon seperti itu ditampilkan beserta tombol '
         '<i>Hitung semua flitch</i>, yang memakai jalur yang sama dengan tombol di panel As-Mined sehingga '
         'hasilnya identik.</div>')
B.append('<h3>15.3 Orthofoto resolusi tinggi di plan / flitch</h3>')
B.append('<p>Latar orthofoto pada Penampang 2D horizontal (termasuk tampilan flitch) dulu dibuat sebagai satu '
         'JPEG seukuran ortho penuh, dibuat sekali lalu di-cache selamanya. Ortho dibatasi 2,5 juta piksel saat '
         'import, sehingga pada flitch sempit gambarnya buram dan zoom tidak menolong. Piramida LOD '
         '(<code>HR.mapImage</code>, sampai 4096 px, dipotong sesuai tampilan) sudah ada tetapi tidak pernah '
         'dipanggil dari jalur 2D, dan <code>HR.extW</code> tidak pernah terisi karena pemantau zoom hanya '
         'dipasang untuk Peta &mdash; yang tidak ada di Block Model. Keduanya diperbaiki: latar 2D memakai LOD, '
         'pemantau zoom sendiri mengisi bentang dunia saat tampilan 2D plan, dan gambar disusun ulang tertunda '
         'sehingga <b>zoom masuk makin tajam</b>. Node <b>Orthofoto (latar plan / flitch)</b> di bawah Flitch '
         'Aktif menyediakan nyala/mati, opasitas, dan badge resolusi yang sedang dipakai.</p>')

B.append('<h2>17. Dikerjakan bersama beberapa geologist</h2>')
B.append('<p>Folder proyek dirancang agar dapat dibuka orang lain: berkas sumber disalin ke dalamnya, dan '
         'basis data proyek menyimpan riwayat perubahan. Yang perlu disepakati di tim:</p>')
B.append(D.bullets(
    'Satu folder proyek <b>dikerjakan satu orang pada satu waktu</b>. Aplikasi mengunci berkas saat dipakai, '
    'tetapi folder bersama di jaringan tetap berisiko bila dibuka bersamaan.',
    'Nama domain dipakai juga untuk nama string, kolom <code>Ore_Domain</code> saat export dan filter '
    'estimasi — jadi sepakati penamaan baku sejak awal.',
    'Parameter variogram dan pass disimpan <b>ke domain</b>, sehingga ikut berpindah bersama proyek.'))

# ---- 13
B.append('<h2>18. Batasan yang perlu diketahui</h2>')
B.append(D.bullets(
    'Aplikasi <b>luring sepenuhnya</b>: tidak ada sinkronisasi antar komputer, tidak ada pembaruan otomatis.',
    'Lisensi <b>terikat komputer</b>. Ganti komputer berarti minta lisensi baru ke admin.',
    'Block model sangat besar dibaca lewat backend Python per potongan; yang ditampilkan di layar tetap '
    'dibatasi agar tampilan tidak tersendat.',
    'Menu <b>Ore Geometry</b> adalah alat bantu pandang bagi geologist dan <b>tidak</b> dipakai oleh '
    'Geomodeller Vein, basis data struktur, maupun Model Estimation.',
    'Klasifikasi keyakinan adalah usulan, bukan keputusan (lihat bagian 8).',
    'Hasil pemodelan, estimasi dan reporting <b>harus diperiksa</b> dan menjadi tanggung jawab pengguna / '
    'Competent Person yang berwenang sebelum dipakai untuk keputusan teknis, pelaporan sumber daya '
    '(mis. KCMI, JORC) atau keperluan komersial.'))

# ---- 14
B.append('<h2>19. Masalah umum</h2>')
B.append(D.tabel(['Gejala', 'Sebab yang biasa', 'Yang dilakukan'], [
    ['Menu atau centang layer tidak bisa diklik', 'datanya memang belum ada',
     'panel memberi keterangan <i>(belum ada data)</i>; import datanya dulu'],
    ['Estimasi menghasilkan sedikit sekali blok', 'solid domain belum dibangun, atau blok tidak berada '
     'di dalam solid', 'periksa tab Solid pada domain, lalu jalankan ulang'],
    ['Banyak blok di pass 2&ndash;3 dengan SoR rendah', 'data bor kurang rapat di daerah itu',
     'wajar; pakai pass &amp; SoR untuk klasifikasi, jangan rata-ratakan seluruh blok'],
    ['Dip bidang vein hasil pengukuran tidak sama dengan dip acuan', 'permukaan vein melengkung (sigmoidal)',
     'bidang rata-rata data memang lebih landai; keduanya benar'],
    ['Arah ore shoot kacau pada sebagian domain', 'ada sesar pasca-mineralisasi yang belum dipulihkan',
     'masukkan bidang sesar di Sesar 3D lalu pulihkan sebelum pemodelan'],
    ['Kadar rata-rata domain terasa terlalu tinggi', 'belum ada top-cut pada unsur ber-efek nugget tinggi',
     'periksa CV dan pemusatan logam, lalu tentukan top-cut per unsur'],
    ['Orthofoto tampak buram saat zoom dekat', 'versi lama memakai resolusi tetap',
     'sejak 0.24.1 detail mengikuti zoom; tunggu ±0,3 detik setelah berhenti menggeser'],
    ['Atribut <code>est_nhole</code> / <code>est_spasi</code> tidak ada', 'block model diestimasi sebelum '
     '0.24.4', 'jalankan ulang Model Estimation agar kerapatan bor ikut terekam']]))

# ---- 15
B.append('<h2>20. Hak cipta &amp; syarat penggunaan</h2>')
B.append('<p>GC-Ex adalah perangkat lunak independen dan <b>tidak</b> berafiliasi dengan, disponsori, atau '
         'didukung oleh pemilik merek perangkat lunak pertambangan mana pun. Nama-nama produk pihak lain '
         'dipakai semata-mata untuk menjelaskan kecocokan format berkas dan alur kerja.</p>')
B.append('<p>Daftar komponen open-source beserta teks lisensinya ada di folder <code>legal</code> pada folder '
         'instalasi, dan ikut di setiap Release dalam '
         '<code>GC-Ex-&lt;versi&gt;_3_Lisensi-dan-Tentang.zip</code>: pemberitahuan lisensi pihak ketiga, '
         'penafian merek dagang, syarat penggunaan, serta teks lisensi Python, Electron / Chromium, dan font.</p>')
B.append('<p>Perangkat lunak disediakan &ldquo;apa adanya&rdquo; tanpa jaminan apa pun. '
         'Copyright &copy; Habil Abdillah 2026. Seluruh hak dilindungi.</p>')

_ISI = [re.sub('<[^>]+>', '', m) for x in B for m in re.findall(r'<h2>(.*?)</h2>', x)]
assert len(_ISI) >= 16, 'daftar isi kosong?'
B.insert(0, D.cover(
    'GRADE CONTROL EXCELLENCE · KELUARGA GC-EX',
    'Petunjuk Teknis GC-', 'Ex',
    'Cara kerja, alur data, format impor / ekspor, algoritme yang dipakai, kerangka blok AOI, '
    'estimasi waste (vein &amp; berlapis), sub-blocking di batas solid, batasan dan masalah umum. '
    'Pendamping <i>Tutorial Update GC-Ex</i>. Berlaku untuk GC-Ex Drill Hole Ultimate dan GC-Ex Block Model.',
    _ISI,
    'GC-Ex Block Model %s &middot; GC-Ex Drill Hole Ultimate %s &middot; disusun otomatis %s.<br>'
    'Semua nama perusahaan, lubang bor, koordinat dan kadar pada contoh di dokumen ini fiktif.<br>'
    'Copyright &copy; Habil Abdillah 2026. Seluruh hak dilindungi.' % (VBM, VDH, D.tanggal())))

sz = D.render(B, PDF, 'Petunjuk Teknis GC-Ex %s / %s' % (VBM, VDH))
print('OK', PDF, sz, 'byte')
