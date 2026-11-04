
CH = []
def ch(title, body, key=None): CH.append((title, body))

# Urutan terbit disusun ulang (0.24.33) mengikuti urutan node Project Tree / langkah kerja nyata
# grade control dengan block model. Bab di bawah boleh ditulis dalam urutan apa saja; daftar inilah
# yang menentukan urutannya di PDF. Setiap entri = awal judul bab (unik).
BAGIAN = [
 ('Bagian I &middot; Persiapan &amp; data',
  'Menyiapkan proyek, memasukkan block model hasil estimasi, dan mengenali tampilannya. Dikerjakan '
  'sekali di awal, lalu hanya diulang saat block model periode berikutnya terbit.',
  ['Tentang tutorial ini', 'Data latihan', 'Halaman muka &amp; import block model', 'Mengenal tampilan']),
 ('Bagian II &middot; Flitch &amp; dig block',
  'Inti pekerjaan harian grade control: memilih flitch yang sedang ditambang, membentuk <b>dig block</b>, '
  'merapikannya, lalu menerbitkan dig plan untuk operasi. Urutannya mengikuti node Project Tree.',
  ['Flitch aktif &amp; Sayatan 2D', 'Orthofoto resolusi tinggi di flitch', 'Dig block otomatis',
   'Additional flagging', 'Digit manual &amp; rekap string', 'Pemeriksaan dig block',
   'Preset kelas kadar', 'Review flitch per flitch', 'Layout &amp; ekspor dig plan']),
 ('Bagian III &middot; Pelaporan grade &times; tonase',
  'Melaporkan tonase dan kadar dari block model dengan <i>constraint</i> &mdash; di bawah topografi, di dalam '
  'desain pit, per bench, per kategori, per cut-off.',
  ['Laporan grade', 'Ringkasan harian flitch aktif', 'Rekap dig block: multi-unsur',
   'Pembobotan proporsi sub-blok']),
 ('Bagian IV &middot; As-mined &amp; rekonsiliasi',
  'Membandingkan rencana dengan aktual: permukaan as-mined, register pekerjaan, dan rekonsiliasi flitch per '
  'flitch antara dig plan dan material yang benar-benar tergali.',
  ['As-mined', 'Register, 3D hasil kerja', 'Laporan periode: mingguan']),
 ('Bagian V &middot; Pembaruan',
  'Ringkasan yang baru pada versi terakhir, untuk pembaca yang sudah memakai versi sebelumnya.',
  ['Yang baru di 0.24']),
]
R1, R0 = N['rekap'][1], N['rekap'][0]
AV = N['am_vs'][1]
def fN(v, d=0): return ('{:,.%df}' % d).format(v).replace(',', 'X').replace('.', ',').replace('X', '.')

ch('Tentang tutorial ini', """<p>Tutorial ini mengajarkan alur kerja <b>grade control dengan block model</b> di aplikasi desktop <b>GC-Ex Block Model """ + VBM + """</b>: memotong <b>flitch</b>, membuat <b>dig block</b> otomatis &amp; manual, <b>additional flagging</b> (mis. ore sulfida), meninjau hasil <b>flitch per flitch</b> dari Project Tree, mencatat <b>as-mined</b> dan membandingkan rencana dengan aktual. Semua gambar diambil dari satu kali jalannya latihan dengan data simulasi yang ikut rilis.</p>
<h3>Yang dibutuhkan</h3><ul><li>Windows 10 / 11 64-bit dengan <b>GC-Ex Block Model</b> terpasang (<code>GC-Ex-Setup-""" + VBM + """.exe</code>) dan lisensi aktif.</li>
<li>File <code>SIM_BM_GC_kadar.csv</code> dari <code>GC-Ex-&lt;versi&gt;_2_Data-Latihan.zip</code> (folder <code>GC-Ex_Drillhole_BlockModel_SIM</code>).</li>
<li>Satu folder kosong untuk proyek latihan, misalnya <code>Proyek_Tutorial_BM</code>.</li></ul>
<h3>Alur kerja di Project Tree</h3><table class="t"><tr><th>Langkah</th><th>Node</th><th>Isi</th></tr>
<tr><td>1–3</td><td>Proyek &middot; Data Spasial &middot; Block Model</td><td>folder proyek, permukaan, block model &amp; warna kelas</td></tr>
<tr><td>4–5</td><td>Data Referensi &middot; Flitch Aktif</td><td>string referensi, tinggi flitch &amp; RL, Sayatan 2D</td></tr>
<tr><td>6–8</td><td>Dig Block &middot; Laporan &middot; Layout</td><td>dig block, additional flagging, running grade, dig plan PDF / STR</td></tr>
<tr><td>9–10</td><td>As-Mined &middot; Register</td><td>poligon aktual, rencana vs aktual, register &amp; rekonsiliasi</td></tr></table>""")

ch('Data latihan', f"""<p><code>SIM_BM_GC_kadar.csv</code> adalah block model GC <b>sintetis</b> (bukan data perusahaan): {fN(N['nBlok'])} blok 2,5 &times; 2,5 &times; 2,5 m di sekitar vein simulasi, atribut <b>{N['atribut']}</b>, dan <code>DOMAIN</code>.</p>
<table class="t"><tr><th>Kolom</th><th>Isi</th></tr><tr><td>AU</td><td>kadar emas (g/t)</td></tr><tr><td>SG</td><td>berat jenis</td></tr>
<tr><td>S_PCT</td><td><b>baru</b>: sulfur (%) fiktif; naik di bawah zona oksida (RL &lt; 290) dan di dalam vein</td></tr>
<tr><td>ZN_PPM, CU_PPM</td><td><b>baru</b>: seng &amp; tembaga (ppm) fiktif, mengikuti kadar Au</td></tr><tr><td>DOMAIN</td><td>QV_Utama / QV_HW1 / WASTE</td></tr></table>"""
 + tip('Kolom S_PCT, ZN_PPM dan CU_PPM ditambahkan untuk latihan <b>additional flagging</b>. Dibuat ulang dengan <code>python tambah_unsur_bm.py</code> (hasil selalu sama).'))

ch('Halaman muka & import block model', steps(
 'Buka <b>GC-Ex Block Model</b> dari menu Start. Halaman muka <b>Import data</b> tampil penuh ([[halaman_muka]]).',
 'Isi <b>Nama project site</b> (di sini <i>Site Latihan &middot; Pit Simulasi</i>). Nama ini tampil di bilah atas di bawah <b>Grade Control Excellence</b> dan disimpan per proyek.',
 'Klik <b>Buka / pilih folder proyek</b> lalu pilih folder kosong <code>Proyek_Tutorial_BM</code>.',
 'Pada <b>Block model</b> pilih <code>SIM_BM_GC_kadar.csv</code> ([[import]]), lalu <b>Buka block model &rarr;</b>.')
 + fig('halaman_muka', 'Halaman muka GC-Ex Block Model: nama project site, folder proyek, proyek tersimpan dan impor data.')
 + fig('import', 'Block model dipilih; file sumber disalin ke folder proyek <code>sumber/</code>.'))

ch('Mengenal tampilan', '<p>Di kiri ada <b>Project Tree</b> (urut langkah kerja, angka 1–10) dan <b>Properti</b> (isi node yang dipilih). Bilah atas: logo <b>GC-Ex / BLOCK MODEL</b>, <b>Grade Control Excellence</b> + nama project site, Proyek, arah pandang, menu <b>Sayatan</b> (Sayatan 2D / 3D), Ortho, Layer, Gelap, PNG.</p>'
 + fig('header', 'Bilah atas GC-Ex Block Model.')
 + fig('bm_3d', 'Block model dengan filter AU &ge; 0,19 (Block Model &rarr; Filter &amp; SG): ore shoot kadar tinggi (merah) di tengah vein.')
 + steps('Project Tree &rarr; <b>Block Model &rarr; Warna &amp; kelas kadar</b>: kelas diskrit dan warnanya ([[warna_kelas]]).')
 + fig('warna_kelas', 'Warna &amp; kelas kadar AU.'))

ch('Flitch aktif & Sayatan 2D', steps(
 f"Project Tree &rarr; <b>Flitch Aktif</b>: isi <b>Tinggi flitch</b> 2,5 dan <b>RL atas</b> {N['flitch1'][0]} ([[flitch]]).",
 'Klik <b>Terapkan flitch</b>: GC-Ex membuka <b>Sayatan 2D</b> tampak atas pada RL tengah flitch; blok dilukis sebagai gambar sehingga zoom &amp; geser ringan.')
 + fig('flitch', f"Flitch RL {N['flitch1'][0]} – {N['flitch1'][1]} di Sayatan 2D.")
 + tip('Menu <b>Sayatan &rarr; Pilih arah sayatan di tampak atas</b> membuka jendela 3D tampak atas; tarik garis P1 &rarr; P2 langsung di atas data untuk sayatan vertikal.'))

ch('Dig block otomatis', steps(
 'Project Tree &rarr; <b>Dig Block &rarr; Otomatis (kelas &amp; tujuan)</b>. Aturan kelas (string number, warna, material) dan <b>Tujuan (DEST)</b> per material diatur di sini.',
 'Klik <b>Buat dig block otomatis</b> ([[digblock_auto]]).')
 + fig('digblock_auto', f"{N['db1']} dig block otomatis di flitch RL {N['flitch1'][0]} – {N['flitch1'][1]}: HG &rarr; R418, LG &rarr; S340.")
 + why('Dig block mengikuti batas sudut blok GC, lalu dihaluskan dan celah kecil disatukan sesuai lebar alat gali.'))

ch('Additional flagging (garis ganda)', """<p><b>Additional flagging</b> menggantikan aturan &ldquo;sulfida / material SxS&rdquo;. Satu aturan = <b>nama flag + unsur + operator + COG</b>. Bila <b>komposit</b> unsur di dalam poligon (rata-rata tertimbang tonase) melewati COG, <b>seluruh poligon</b> diberi flag dan digambar dengan <b>garis ganda</b>.</p>"""
 + steps('Dig Block &rarr; Otomatis &rarr; buka <b>Additional flagging (garis ganda)</b> ([[flagging_aturan]]).',
   'Aturan 1: nama <b>Ore Sulfide</b>, unsur <code>S_PCT</code>, <b>&gt;</b>, COG <b>0,8</b> (%).',
   'Klik <b>+ Aturan flag</b>. Aturan 2: <b>Zn tinggi</b>, <code>ZN_PPM</code>, <b>&gt;</b>, COG <b>500</b> (ppm). Satuan COG = satuan kolom block model.',
   'Klik <b>Perbarui garis ganda</b>. Poligon ber-flag mendapat garis kedua di sebelah dalam ([[flagging_2d]]).')
 + fig('flagging_aturan', 'Tabel aturan additional flagging.')
 + fig('flagging_2d', f"Dari {N['db1']} dig block, {N['db1_flag']} ber-flag <b>Ore Sulfide</b> (komposit S &gt; 0,8 %) dan bergaris ganda.")
 + tip('Kolom <b>Flag?</b> di aturan Tujuan (DEST) memakai flag ini, mis. LG + flag &rarr; stockpile sulfida. Nama flag ikut di label dig plan, PDF, daftar dig block (&#9873;) dan Project Tree. Proyek lama: pengaturan sxs &amp; batas otomatis menjadi aturan <i>Ore Sulfide</i>.'))

ch('Digit manual & rekap string', steps(
 'Dig Block &rarr; <b>Digit manual (snap sudut blok)</b>: klik <b>Mulai</b>, klik sudut-sudut blok di Sayatan 2D, klik titik pertama <b>atau tekan Enter</b> untuk menutup. Poligonnya mendapat menu yang sama dengan dig block otomatis (edit bentuk, warna, grade &times; tonase).',
 'Dig Block &rarr; <b>Rekap &amp; edit string</b> ([[rekap_string]]): tabel semua string (tampil, nomor, keterangan, titik, panjang, bidang) dengan &#9998; <b>edit bentuk</b> dan &times; hapus. String baru dibuat di bagian bawah panel.')
 + fig('rekap_string', 'Rekap &amp; edit string.'))

ch('Orthofoto resolusi tinggi di flitch', """<p>Saat menggambar dig block di flitch, yang paling membantu adalah melihat <b>foto lapangannya</b> di bawah poligon: batas material yang terlihat di muka galian, jalan angkut, batas pekerjaan shift sebelumnya. Orthofoto tampil sebagai <b>gambar latar</b> pada Penampang 2D horizontal &mdash; dan flitch adalah penampang horizontal.</p>
<p>Sejak 0.24.24 latar itu dipotong sesuai tampilan dari <b>piramida resolusi tinggi</b>, bukan satu gambar beresolusi tetap. Artinya <b>zoom masuk membuatnya makin tajam</b>; sebelumnya gambar dibuat sekali seukuran ortho penuh lalu dipakai terus, sehingga di flitch sempit (misal 50 &times; 50 m dari ortho 1,5 km) tampak buram dan zoom tidak menolong.</p>""" +
 kv([('Node', '<b>Orthofoto (latar plan / flitch)</b> di bawah <b>Flitch Aktif</b>'),
     ('Centang', 'nyala / mati tanpa pergi ke menu Overlay'),
     ('Menu', 'opasitas 100 / 75 / 50 / 25%'),
     ('Badge', 'resolusi yang sedang dipakai, mis. <code>LOD 2048 px @ 0,12 m/px</code>')])
 + tip('Opasitas 50&ndash;75% biasanya paling enak: foto masih terbaca, warna kelas kadar blok tetap jelas di atasnya.')
 + warn('Latar ini hanya digambar pada penampang <b>horizontal</b> (plan / flitch). Pada penampang vertikal tidak ada orthofoto &mdash; badge node akan menyebut <i>hanya di plan 2D</i>.'))

ch('Pemeriksaan dig block sebelum dig plan terbit', """<p>Dig plan yang cacat baru ketahuan di pit, saat alat sudah di muka galian. Node <b>Pemeriksaan dig block</b> memeriksanya lebih dulu, dan membagi temuan menjadi dua tingkat.</p>""" +
 '<table class="t"><tr><th>Tingkat</th><th>Artinya</th></tr>' +
 '<tr><td><b>CEGAH</b></td><td>jangan diterbitkan sebelum dibereskan</td></tr>' +
 '<tr><td><b>PERIKSA</b></td><td>perlu dilihat, belum tentu salah</td></tr></table>' +
 '<h3>Yang diperiksa</h3>' +
 '<table class="t"><tr><th>Temuan</th><th>Tingkat</th><th>Mengapa</th></tr>' +
 '<tr><td><b>Lebar minimum</b> di bawah batas selektivitas alat</td><td>CEGAH</td><td>tidak praktis digali; alat akan mengambil material sebelahnya juga</td></tr>' +
 '<tr><td><b>Tonase nol</b></td><td>CEGAH</td><td>poligon tidak memuat blok model: salah posisi, salah flitch, atau tersaring filter atribut</td></tr>' +
 '<tr><td><b>Garis saling memotong</b> (poligon menyilang)</td><td>CEGAH</td><td>luas dan tonase tidak bisa dipercaya</td></tr>' +
 '<tr><td><b>Poligon tidak tertutup</b></td><td>CEGAH</td><td>bukan area; tonase tidak terhitung</td></tr>' +
 '<tr><td><b>Tanpa tujuan material</b></td><td>CEGAH</td><td>truk tidak tahu harus ke mana</td></tr>' +
 '<tr><td><b>Luas</b> di bawah ambang</td><td>PERIKSA</td><td>blok sangat kecil; pertimbangkan digabung</td></tr>' +
 '<tr><td><b>Kadar kosong</b></td><td>PERIKSA</td><td>blok di dalamnya berkadar &minus;99, atau atribut kadar belum dipilih</td></tr>' +
 '<tr><td><b>Nama dipakai lebih dari sekali</b></td><td>PERIKSA</td><td>bisa tertukar di dispatch dan register</td></tr></table>' +
 why('<b>Lebar minimum</b> dihitung dengan <i>rotating calipers</i> pada <i>convex hull</i> poligon &mdash; jarak terkecil antara dua garis sejajar yang mengapitnya. Bukan perkiraan luas dibagi keliling. Pada uji, persegi 10 &times; 2 m menghasilkan tepat <b>2,00 m</b> dan segitiga tipis tepat <b>0,50 m</b>, jadi angka yang Anda sampaikan ke operasi bisa dipertanggungjawabkan.')
 + steps('Node <b>Pemeriksaan dig block</b> &rarr; <b>Periksa flitch aktif</b> (atau <b>semua flitch</b> sebelum rekap mingguan).',
         'Bereskan semua yang bertanda <b>CEGAH</b>.',
         'Unduh CSV-nya bila perlu lampiran, lalu terbitkan dig plan.')
 + tip('Dua pemeriksaan ini jarang berbunyi pada pengaturan bawaan, dan itu wajar: <b>tanpa tujuan material</b> hanya mungkin bila materialnya tidak cocok aturan tujuan mana pun <i>dan</i> tujuan cadangan kosong; <b>nama ganda</b> hanya mungkin bila template nama tidak memuat <code>{NO}</code>. Keduanya tetap diperiksa untuk menjaga keadaan yang tidak biasa.'))

ch('Preset kelas kadar & tujuan material', """<p>Batas kelas kadar dan aturan tujuan material diisi manual tiap kali. Akibatnya shift siang dan shift malam, atau dua orang yang berbeda, bisa memakai batas yang berbeda tanpa ada yang sadar &mdash; dan itu muncul sebagai selisih yang tidak bisa dijelaskan di rekonsiliasi.</p>
<p>Node <b>Preset kelas kadar &amp; tujuan</b> menyimpannya sebagai preset bernama di berkas proyek.</p>""" +
 kv([('Yang disimpan', 'batas kelas kadar (LG / HG / &hellip;), aturan tujuan material, <b>lebar minimum alat</b>, ambang sulfida, material bawaan, ambang luas'),
     ('Menyimpan', 'menu node &rarr; <i>Simpan pengaturan sekarang sebagai preset&hellip;</i>, beri nama mis. <code>Pit A &mdash; Nov 2026</code>'),
     ('Memakai', 'klik nama preset di menu node, atau di anak node-nya &rarr; <i>Pakai preset ini</i>'),
     ('Tiap preset tampil', 'jumlah kelas, jumlah aturan tujuan, lebar minimum, dan tanggal disimpan')])
 + warn('Memakai preset <b>tidak menghapus</b> dig block yang sudah ada, tetapi material dan tujuannya dihitung ulang dengan aturan baru. Karena itu selalu ada konfirmasi lebih dulu. Untuk rekonsiliasi yang rapi, ganti preset di <b>awal</b> periode, bukan di tengah.'))

ch('Ringkasan harian flitch aktif', """<p>Laporan pagi biasanya dirakit sendiri dari beberapa tabel. Node <b>Ringkasan harian (flitch aktif)</b> menyusunnya sekaligus, dalam satu halaman.</p>""" +
 kv([('Per material', 'jumlah dig block, ton, dan kadar <b>semua unsur</b> yang dicentang di <i>Elemen laporan</i>'),
     ('Per tujuan material', 'tabel yang sama, dikelompokkan menurut tujuan'),
     ('Rencana vs aktual', 'bila as-mined flitch itu sudah dihitung: ton rencana (dig block) vs aktual (as-mined), beserta selisih dan persennya'),
     ('Export', 'CSV satu berkas berisi ketiga bagian di atas')])
 + tip('Kalau as-mined flitch itu belum dihitung, bagian rencana vs aktual akan mengatakannya terang-terangan, bukan menampilkan nol. Untuk rekap beberapa hari sekaligus, pakai <b>Laporan periode</b>.'))

ch('Rekap dig block: multi-unsur & centroid', """<p>Rekap dig block semua flitch (CSV) dulu hanya memuat <b>satu</b> kolom kadar. Untuk endapan ber-multi unsur, kolom lainnya harus diambil dari tempat lain.</p>
<p>Sekarang rekap itu memuat <b>semua unsur</b> yang dicentang di <i>Elemen laporan</i>, <b>Metal</b> tiap unsur yang satuannya memungkinkan, serta <b>Centroid_X</b> dan <b>Centroid_Y</b> tiap dig block.</p>""" +
 kv([('Kolom', 'RL_atas, RL_bawah, Nama, Material, Tujuan, Luas_m2, Ton, &lt;tiap unsur&gt;, Metal_&lt;unsur&gt;, Centroid_X, Centroid_Y, Flag'),
     ('Centroid', 'titik berat poligon (bukan titik tengah kotak pembatas), dipakai dispatch / fleet system untuk menandai lokasi blok')]))

ch('Pembobotan proporsi sub-blok (sb_frac)', """<p>Bila block model yang Anda pakai berasal dari <b>Model Estimation GC-Ex Drill Hole</b> dan pernah dipecah di batas solid (sub-blocking), setiap blok membawa kolom <code>sb_frac</code>: proporsi volume blok yang benar-benar berada di dalam solid.</p>
<p>Reporting Block Model kini <b>menimbang</b> tonase dan volume dengan angka itu, jadi blok di perbatasan dihitung <b>sebagian</b>. Pilihannya hanya muncul bila atribut itu ada, dan bisa dimatikan (blok dihitung utuh, cara Surpac).</p>""" +
 why('Tanpa pembobotan ini, block model yang <b>sama</b> memberi tonase yang <b>berbeda</b> antara laporan di Drill Hole dan di Block Model &mdash; justru dilusi batas yang sudah diukur dengan susah payah menjadi hilang. Pada data latihan <code>SIM_BM_GC_estimasi.csv</code> (20,1% blok sebagian), selisihnya sekitar <b>25%</b>: 8,05 juta ton dengan pembobotan vs 10,75 juta ton tanpa pembobotan.')
 + tip('Latihannya: import <code>data/SIM_BM_GC_estimasi.csv</code>, buka Reporting, jalankan sekali dengan centang <b>Timbang volume &amp; tonase dengan proporsi sub-blok</b> dan sekali tanpa centang, lalu bandingkan.'))

ch('Laporan grade × tonase', steps(
 'Project Tree &rarr; <b>Laporan Grade × Tonnage &rarr; Running grade &amp; tonnage</b> ([[laporan_flitch]]): ton, kadar dan metal per dig block flitch aktif, dikelompokkan per tujuan.',
 '<b>Elemen laporan &amp; kadar tonase</b>: centang unsur tambahan (S_PCT, ZN_PPM, CU_PPM) agar ikut tabel, CSV, PDF dan register.')
 + fig('laporan_flitch', 'Running grade &amp; tonnage flitch aktif.'))

ch('Review flitch per flitch di Project Tree', f"""<p>Setiap menu punya node <b>Per flitch</b> yang dihitung dari poligon tersimpan; flitch aktif tidak berubah saat menghitung. Kerjakan flitch kedua (RL atas {R0[0]}) dengan langkah yang sama, lalu tinjau keduanya.</p>"""
 + steps('<b>Dig Block &rarr; Per flitch</b> ([[pertree_digblock]]): tiap flitch menampilkan jumlah DB dan ton @ kadar. Buka satu flitch: daftar poligon dengan ton @ kadar dan &#9873; flag ([[pertree_digblock_flitch]]).',
   'Klik poligon: flitch-nya dibuka di Sayatan 2D dan poligon disorot ([[pertree_digblock_2d]]). Menu &hellip;: <b>Edit bentuk</b>, <b>Hapus</b>.',
   '<b>Laporan Grade × Tonnage &rarr; Per flitch</b> ([[pertree_laporan]]): ton @ kadar per flitch dan per material &rarr; tujuan. <b>Rekap semua flitch (CSV)</b>: satu baris per dig block di semua flitch.')
 + fig('pertree_digblock', 'Dig Block &rarr; Per flitch.') + fig('pertree_digblock_flitch', 'Isi satu flitch: poligon dengan ton @ kadar dan flag.')
 + fig('pertree_digblock_2d', 'Klik poligon di Project Tree: flitch dibuka dan poligon disorot.')
 + fig('pertree_laporan', 'Laporan &rarr; Per flitch dan Rekap semua flitch (CSV).')
 + f"""<table class="t"><tr><th>Flitch</th><th>Dig block</th><th>Ton</th><th>AU (g/t)</th><th>Ber-flag</th></tr>
<tr><td>{R0[0]} – {R0[1]}</td><td>{R0[2]}</td><td>{fN(R0[3])}</td><td>{fN(R0[4],2)}</td><td>{R0[5]}</td></tr>
<tr><td>{R1[0]} – {R1[1]}</td><td>{R1[2]}</td><td>{fN(R1[3])}</td><td>{fN(R1[4],2)}</td><td>{R1[5]}</td></tr></table>
<p>CSV rekap berisi {N['csv_baris']} baris (satu per dig block).</p>""")

ch('Layout & ekspor dig plan', steps('Project Tree &rarr; <b>Layout &amp; Ekspor Dig Plan &rarr; Layout &amp; plot PDF</b> ([[layout]]): judul, skala, elemen laporan, tabel tonase; PDF siap cetak.',
 '<b>Export STR / DXF (Surpac)</b> untuk string dig block; <b>Simpan gambar PNG</b> untuk tampilan saat ini.') + fig('layout', 'Layout &amp; plot PDF.'))

ch('As-mined: rencana vs aktual', """<p>Sesudah penambangan, batas aktual dicatat sebagai <b>poligon as-mined</b> (pick-up survey, file STR / DXF / CSV, atau digit manual) lalu dihitung dengan model GC + koreksi sampel. Di latihan ini poligon aktual dibuat dari dig block yang bergeser 0,6 m (simulasi penggalian).</p>"""
 + steps('Project Tree &rarr; <b>As-Mined &rarr; Poligon, pick-up &amp; lantai</b>: import pick-up / boundary atau digit manual ([[asmined_poligon]]).',
   f"<b>As-Mined &rarr; Per flitch</b> ([[pertree_asmined]]): tiap flitch menampilkan selisih <b>&Delta;</b>; di dalamnya <b>Rencana (dig block)</b> dan <b>Aktual (as-mined)</b> beserta poligon. Flitch RL {AV[0]} – {AV[1]}: rencana {fN(AV[2])} t @ {fN(AV[3],2)}, aktual {fN(AV[5])} t @ {fN(AV[6],2)}.",
   'Klik flitch: dibuka di Sayatan 2D dengan dig block (rencana) dan poligon as-mined (aktual) bertumpuk ([[asmined_review_2d]]).')
 + fig('asmined_poligon', 'Poligon as-mined di flitch aktif.') + fig('pertree_asmined', 'As-Mined &rarr; Per flitch: selisih, rencana dan aktual.')
 + fig('asmined_review_2d', 'Rencana (dig block) dan aktual (as-mined) bertumpuk.')
 + why('Kadar aktual lebih rendah karena poligon aktual bergeser keluar dari vein sempit: dilusi. Inilah yang ingin dilihat rekonsiliasi flitch per flitch.'))

ch('Laporan periode: mingguan & bulanan', """<p>Node <b>Laporan periode (mingguan / bulanan)</b> di bawah <b>Register &amp; Laporan As-Mined</b> menjumlahkan apa yang <b>benar-benar tergali</b> dalam satu rentang tanggal, dari register as-mined.</p>""" +
 kv([('Periode cepat', 'Minggu ini &middot; Minggu lalu &middot; Bulan ini &middot; Bulan lalu &middot; Kustom (dari&ndash;sampai)'),
     ('Kelompokkan', 'per tanggal, per minggu, per <b>shift (DS / NS)</b>, per flitch, per tujuan material, per kode ore, atau per pit'),
     ('Isi tabel', 'jumlah poligon, ton, BCM, dan kadar semua unsur terpilih &mdash; kadar <b>ditimbang tonase</b>'),
     ('Target', 'isi target ton (dan kadar) periode ini &rarr; pencapaian dalam persen, diberi warna: hijau &ge; 100%, jingga &ge; 90%, merah di bawahnya'),
     ('Tren', 'grafik batang: per <b>hari</b> untuk laporan mingguan, per <b>minggu</b> untuk bulanan'),
     ('Pembanding', 'periode sebelumnya dengan panjang yang sama, beserta selisih ton dan persennya'),
     ('Export', 'CSV memuat tabel, total, target & pencapaian, tren, dan periode pembanding')])
 + why('Kadar dijumlahkan dengan mesin yang sama dengan register dan PDF rekonsiliasi (<i>ditimbang tonase</i>), jadi angka di laporan periode tidak pernah berbeda dari angka di register. Itu syarat supaya laporan mingguan dan bulanan bisa dipertanggungjawabkan.')
 + warn('As-mined dihitung <b>per flitch aktif</b>. Poligon dari flitch yang belum pernah dihitung belum punya tonase, dan laporan <b>tidak</b> menjumlahkannya diam-diam: jumlahnya disebut terang-terangan beserta tombol <b>Hitung semua flitch</b> (memakai jalur yang sama dengan tombol di panel As-Mined, jadi hasilnya identik). Selalu bereskan angka itu menjadi nol sebelum laporan dikirim.', 'Poligon yang belum dihitung')
 + steps('Pastikan poligon as-mined sudah diisi <b>tanggal</b> dan <b>shift</b>-nya (panel As-Mined &rarr; <i>Terapkan ke flitch ini</i> mengisinya sekaligus).',
         'Buka node <b>Laporan periode</b>, pilih periodenya.',
         'Bila ada peringatan poligon belum dihitung, tekan <b>Hitung semua flitch</b>.',
         'Isi target ton bila ada, pilih pengelompokan, lalu <b>Hitung</b>.',
         'Unduh CSV untuk lampiran laporan mingguan / bulanan.'))

ch('Register, 3D hasil kerja & rekonsiliasi', steps(
 'Project Tree &rarr; <b>Register &amp; Laporan As-Mined &rarr; Register poligon</b> ([[register]]): kode poligon, BCM, ton, kadar, ritase; <b>Kirim register ke Excel</b>, CSV, <b>Report rekonsiliasi (PDF)</b>.',
 '<b>3D hasil kerja</b>: prisma dig block, poligon as-mined dan sub-blok model as-mined per flitch ([[hasil_kerja_3d]]). <b>Rekap &amp; model gabungan (.mdl)</b> menggabungkan semua flitch ke satu block model Surpac.')
 + fig('register', 'Register poligon as-mined.') + fig('hasil_kerja_3d', '3D hasil kerja: dig block (rencana) dan as-mined (aktual).'))

ch('Yang baru di 0.24', """<p>Perbaikan GC-Ex Block Model 0.24 berpusat pada satu keluhan: digitasi manual dulu terasa kalah dari dig block otomatis. Sekarang keduanya setara, dan seluruh hasil kerja &mdash; dari dig block sampai as-mined &mdash; bisa ditinjau dan diedit dari satu tempat.</p>"""
 + '<table class="t"><tr><th>Yang berubah</th><th>Di tutorial ini</th></tr>'
 + '<tr><td><b>Digitasi manual setara otomatis</b>: <b>Enter</b> menutup string, poligon mendapat menu edit bentuk, warna, grade &times; tonase</td><td>{{B:Digit manual}}</td></tr>'
 + '<tr><td><b>Poligon as-mined dapat diedit</b> (bentuk &amp; warna), <b>register poligon</b> dapat diubah warnanya</td><td>{{B:As-mined}}, {{B:Register}}</td></tr>'
 + '<tr><td><b>Subnode per flitch di Project Tree</b> untuk audit / review langsung ke flitch yang dimaksud</td><td>{{B:Review flitch}}</td></tr>'
 + '<tr><td><b>3D hasil kerja dig block &rarr; as-mined</b> dan <b>rekap as-mined satu berkas .mdl</b></td><td>{{B:Register}}</td></tr>'
 + '<tr><td><b>Penampang Sayatan seragam</b> dengan GC-Ex Drill Hole Ultimate; <b>tanpa jeda saat zoom</b> (segmen garis digabung, kotak blok 2D dirapatkan; garis putus-putus merah pada dig block tidak muncul lagi)</td><td>{{B:Flitch aktif}}</td></tr>'
 + '<tr><td><b>Topografi &amp; orthofoto resolusi tinggi</b>: piramida LOD, resolusi mengikuti zoom, Peta setajam layar</td><td>di bawah</td></tr></table>'
 + '<h3>Topografi &amp; orthofoto resolusi tinggi</h3><p>Orthofoto disusun menjadi <b>piramida LOD</b>; warna diambil dari tingkat yang sepadan dengan kerapatan tampilan dan resolusi mesh mengikuti luas area yang terlihat, jadi zoom masuk otomatis makin detail tanpa menambah beban. Kotak <b>Resolusi (m)</b> di panel orthofoto kini berarti <b>batas paling halus</b>. Tampilan disegarkan &plusmn;0,3 detik setelah zoom / geser berhenti. Perhitungan laporan tidak berubah: grid elevasi cepat hanya dipakai untuk tampilan.</p>'
 + '<table class="t"><tr><th></th><th>Sebelum</th><th>Sesudah</th></tr><tr><td>Mesh ortho, zoom 10 m</td><td>1 m/titik &middot; 592 ms</td><td><b>0,1 m/titik</b> &middot; <b>3 ms</b></td></tr><tr><td>200.000 pembacaan elevasi</td><td>512 ms</td><td><b>14 ms</b></td></tr></table>'
 + tip('Klasifikasi keyakinan, kerangka blok AOI, estimasi waste dan sub-blocking ada di <b>GC-Ex Drill Hole Ultimate</b> (Tutorial Modelling &amp; Estimasi). Block model hasilnya (.mdl) dibuka di sini untuk flitch, dig block dan as-mined.'))

