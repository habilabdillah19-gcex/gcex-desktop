
CH = []
def ch(title, body, key=None): CH.append((title, body))
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

