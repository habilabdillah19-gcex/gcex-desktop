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
B.append(D.cover(
    'GRADE CONTROL EXCELLENCE · KELUARGA GC-EX',
    'Petunjuk Teknis GC-', 'Ex',
    'Cara kerja, alur data, format impor / ekspor, algoritme yang dipakai, kerangka blok AOI, '
    'estimasi waste (vein &amp; berlapis), sub-blocking di batas solid, batasan dan masalah umum. '
    'Pendamping <i>Tutorial Update GC-Ex</i>. Berlaku untuk GC-Ex Drill Hole Ultimate dan GC-Ex Block Model.',
    ['1. Cara kerja singkat', '2. Memasang & menjalankan', '3. Folder proyek dan apa yang disimpan',
     '4. Alur kerja data', '5. Data bor: format & aturan', '6. Dua jalur estimasi: vein dan berlapis',
     '7. Algoritme yang dipakai', '8. Kerangka blok AOI, estimasi waste & proporsi volume',
     '9. Klasifikasi keyakinan sumber daya',
     '10. Topografi & orthofoto resolusi tinggi', '11. Format impor / ekspor',
     '12. GC-Ex Block Model: flitch, dig block, as-mined', '13. Dikerjakan bersama beberapa geologist',
     '14. Batasan yang perlu diketahui', '15. Masalah umum', '16. Hak cipta & syarat penggunaan'],
    'GC-Ex Block Model %s &middot; GC-Ex Drill Hole Ultimate %s &middot; disusun otomatis %s.<br>'
    'Semua nama perusahaan, lubang bor, koordinat dan kadar pada contoh di dokumen ini fiktif.<br>'
    'Copyright &copy; Habil Abdillah 2026. Seluruh hak dilindungi.' % (VBM, VDH, D.tanggal())))

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
B.append('<h2>7. Dua jalur estimasi: vein dan berlapis</h2>')
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
B.append('<div class="page"></div><h2>8. Algoritme yang dipakai</h2>')
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
B.append('<div class="page"></div><h2>9. Kerangka blok AOI, estimasi waste &amp; proporsi volume</h2>')
B.append('<h3>8.1 Kerangka blok AOI</h3>')
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
B.append('<h3>8.2 Estimasi waste &mdash; jalur solid domain</h3>')
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
B.append('<h3>8.3 Estimasi waste &mdash; jalur berlapis (laterit)</h3>')
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
B.append('<h3>8.4 Sub-blocking di batas solid &amp; atribut <code>sb_frac</code></h3>')
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

B.append('<div class="page"></div><h2>10. Klasifikasi keyakinan sumber daya</h2>')
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
B.append('<h2>11. Topografi &amp; orthofoto resolusi tinggi</h2>')
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
B.append('<h2>12. Format impor / ekspor</h2>')
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
B.append('<h2>13. GC-Ex Block Model: flitch, dig block, as-mined</h2>')
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
B.append('<h2>14. Dikerjakan bersama beberapa geologist</h2>')
B.append('<p>Folder proyek dirancang agar dapat dibuka orang lain: berkas sumber disalin ke dalamnya, dan '
         'basis data proyek menyimpan riwayat perubahan. Yang perlu disepakati di tim:</p>')
B.append(D.bullets(
    'Satu folder proyek <b>dikerjakan satu orang pada satu waktu</b>. Aplikasi mengunci berkas saat dipakai, '
    'tetapi folder bersama di jaringan tetap berisiko bila dibuka bersamaan.',
    'Nama domain dipakai juga untuk nama string, kolom <code>Ore_Domain</code> saat export dan filter '
    'estimasi — jadi sepakati penamaan baku sejak awal.',
    'Parameter variogram dan pass disimpan <b>ke domain</b>, sehingga ikut berpindah bersama proyek.'))

# ---- 13
B.append('<h2>15. Batasan yang perlu diketahui</h2>')
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
B.append('<h2>16. Masalah umum</h2>')
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
B.append('<h2>17. Hak cipta &amp; syarat penggunaan</h2>')
B.append('<p>GC-Ex adalah perangkat lunak independen dan <b>tidak</b> berafiliasi dengan, disponsori, atau '
         'didukung oleh pemilik merek perangkat lunak pertambangan mana pun. Nama-nama produk pihak lain '
         'dipakai semata-mata untuk menjelaskan kecocokan format berkas dan alur kerja.</p>')
B.append('<p>Daftar komponen open-source beserta teks lisensinya ada di folder <code>legal</code> pada folder '
         'instalasi, dan ikut di setiap Release dalam '
         '<code>GC-Ex-&lt;versi&gt;_3_Lisensi-dan-Tentang.zip</code>: pemberitahuan lisensi pihak ketiga, '
         'penafian merek dagang, syarat penggunaan, serta teks lisensi Python, Electron / Chromium, dan font.</p>')
B.append('<p>Perangkat lunak disediakan &ldquo;apa adanya&rdquo; tanpa jaminan apa pun. '
         'Copyright &copy; Habil Abdillah 2026. Seluruh hak dilindungi.</p>')

sz = D.render(B, PDF, 'Petunjuk Teknis GC-Ex %s / %s' % (VBM, VDH))
print('OK', PDF, sz, 'byte')
