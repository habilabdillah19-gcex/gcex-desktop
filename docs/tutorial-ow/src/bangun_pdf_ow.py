import asyncio, html, datetime
from playwright.async_api import async_playwright
J='file:///home/claude/tut/jpg/'
TGL='14 November 2026'
CSS='''
@page{size:A4;margin:16mm 15mm 18mm 15mm}
*{box-sizing:border-box}
body{font-family:"Segoe UI",Inter,"DejaVu Sans",Arial,sans-serif;font-size:10.3pt;color:#2b3445;line-height:1.5;margin:0}
h1{font-size:19pt;color:#1b2a4e;margin:0 0 6px;border-bottom:3px solid #1f6feb;padding-bottom:4px;page-break-before:always}
h2{font-size:13pt;color:#1b2a4e;margin:16px 0 4px}
h3{font-size:11pt;color:#1557c0;margin:12px 0 3px}
p{margin:4px 0 6px}
ol,ul{margin:4px 0 8px;padding-left:20px}li{margin:2px 0}
b{color:#1b2a4e}
code{font-family:"DejaVu Sans Mono",Consolas,monospace;font-size:8.8pt;background:#eef2f7;padding:0 3px;border-radius:2px}
table{border-collapse:collapse;width:100%;margin:6px 0 10px;font-size:9pt;page-break-inside:auto}
th{background:#1b2a4e;color:#fff;text-align:left;padding:4px 6px;font-weight:600}
td{border-bottom:1px solid #d6dde8;padding:3px 6px;vertical-align:top}
tr:nth-child(even) td{background:#f6f8fb}
figure{margin:8px 0 12px;page-break-inside:avoid}
figure img{width:100%;border:1px solid #b8c4d6;border-radius:3px;display:block}
figcaption{font-size:8.8pt;color:#667085;margin-top:3px}
figcaption b{color:#1557c0}
.cl{display:grid;grid-template-columns:auto 1fr;gap:1px 8px;font-size:9pt;margin:4px 0 0;padding:6px 8px;background:#f3f6fa;border-left:3px solid #e53935;border-radius:2px}
.cl i{font-style:normal;background:#e53935;color:#fff;border-radius:50%;width:16px;height:16px;display:inline-flex;align-items:center;justify-content:center;font-size:8pt;font-weight:700;margin-top:2px}
.note{background:#eef4ff;border-left:3px solid #1f6feb;padding:6px 10px;margin:8px 0;font-size:9.5pt}
.warn{background:#fff6e5;border-left:3px solid #f5a623;padding:6px 10px;margin:8px 0;font-size:9.5pt}
.cover{height:262mm;display:flex;flex-direction:column;justify-content:space-between;background:linear-gradient(160deg,#1b2a4e 0%,#24365f 55%,#1f6feb 140%);color:#fff;margin:-16mm -15mm 0;padding:28mm 22mm 20mm}
.cover h1{border:0;color:#fff;font-size:34pt;margin:14px 0 0;page-break-before:avoid}
.cover .st{font-size:15pt;color:#cfe0fb;margin-top:6px}
.cover .meta{font-size:10pt;color:#cfd9ee;line-height:1.7}
.cover img.logo{width:84px}
.cover img.hero{width:100%;border-radius:6px;border:2px solid #ffffff40;margin-top:16px}
.toc{columns:2;font-size:10pt}.toc div{margin:2px 0}
.two{display:grid;grid-template-columns:1fr 1fr;gap:10px}
.small figure img{width:100%}
'''
def fig(n,cap,calls=None,w=None):
    st=f' style="width:{w}"' if w else ''
    c=''
    if calls: c='<div class="cl">'+''.join(f'<i>{i+1}</i><span>{t}</span>' for i,t in enumerate(calls))+'</div>'
    return f'<figure{st}><img src="{J}{n}.jpg"><figcaption><b>Gambar {FN.next()}.</b> {cap}</figcaption>{c}</figure>'
class C:
    def __init__(s): s.i=0
    def next(s): s.i+=1; return s.i
FN=C()
def tbl(head,rows):
    return '<table><tr>'+''.join(f'<th>{h}</th>' for h in head)+'</tr>'+''.join('<tr>'+''.join(f'<td>{c}</td>' for c in r)+'</tr>' for r in rows)+'</table>'
def cover(title,sub,hero):
    return f'''<div class="cover"><div><img class="logo" src="{J}logo.png"><h1>{title}</h1><div class="st">{sub}</div>
<img class="hero" src="{J}{hero}.jpg"></div><div class="meta"><b style="color:#fff">Ore Works 0.2.0</b> · keluarga GC-Ex<br>Versi dokumen: {TGL}<br>Copyright © 2026 Habil Abdillah. Data contoh di dokumen ini fiktif.</div></div>'''

# ======================= TUTORIAL =======================
T=[cover('Ore Works','Tutorial Penggunaan — dengan tangkapan layar langkah demi langkah','07_3d_bor_topo_wf')]
T.append('''<h1 style="page-break-before:always">Daftar isi</h1><div class="toc">
<div>1. Pengantar &amp; data latihan</div><div>2. Mengenal layar</div><div>3. Latihan 1 — Project, data bor, topografi, wireframe</div>
<div>4. Latihan 2 — Wall mapping</div><div>5. Latihan 3 — Channel sampling &amp; assay</div><div>6. Latihan 4 — Titik struktur &amp; simbol geologi</div>
<div>7. Latihan 5 — Layout peta, slicing, analisis, plan bor</div><div>8. Tips &amp; pertanyaan umum</div></div>
<div class="note">Cara membaca gambar: kotak dan bulatan <b style="color:#e53935">merah bernomor</b> menandai tombol atau isian yang dibahas. Penjelasan tiap nomor ada di bawah gambar.</div>''')
T.append('<h1>1. Pengantar &amp; data latihan</h1>'+'''
<p><b>Ore Works</b> adalah aplikasi satu file HTML untuk melihat data bor, topografi dan wireframe dalam 3D, sekaligus mencatat hasil pemetaan lapangan: wall mapping, channel sampling, grab sample dan pengukuran struktur. Semuanya berjalan offline di browser — tanpa instalasi, internet, atau server. Aplikasi ini dulu bernama kerja <i>Ore Studio</i>.</p>
<h2>Yang dibutuhkan</h2><ul><li>File <code>Ore_Works.html</code> (±1 MB).</li><li>Google Chrome atau Microsoft Edge versi terbaru.</li><li>Laptop biasa sudah cukup; untuk ribuan lubang bor, RAM 8 GB atau lebih lebih nyaman.</li></ul>
<h2>Cara membuka</h2><ol><li>Simpan <code>Ore_Works.html</code> di folder kerja, misalnya <code>Documents\\Ore Works</code>.</li><li>Klik kanan file → <b>Open with</b> → Chrome atau Edge.</li><li>Layar 3D kosong dengan menu di atas akan muncul (Gambar 1).</li></ol>
<div class="warn"><b>Penting.</b> Data yang diimpor hanya ada di memori browser. Selalu simpan pekerjaan lewat <b>File → Simpan project</b> (file <code>.gcv.json</code>) sebelum menutup tab.</div>
<h2>Data latihan</h2><p>Semua latihan memakai data fiktif dalam folder <code>Data_Latihan_Ore_Works</code> (koordinat lokal E 10.000–10.200, N 20.000–20.200):</p>'''+tbl(['File','Isi','Dipakai di'],[
['<code>LTH_collar.csv</code>, <code>LTH_survey.csv</code>, <code>LTH_assay.csv</code>, <code>LTH_geologi.csv</code>','42 lubang GC fiktif, kedalaman 40 m, Au &amp; Ag per meter, litologi/alterasi','Latihan 1'],
['<code>LTH_topografi.str</code>','Topografi string Surpac (grid 5 m)','Latihan 1'],
['<code>LTH_V2001.obj</code>','Wireframe vein V2001 (tebal 2 m)','Latihan 1'],
['<code>LTH_pickup.csv</code>','38 titik pick-up survei: VN (vein), KT (kontak), SL (sesar), CH (channel), GB (grab)','Latihan 2–3'],
['<code>LTH_assay_channel.txt</code>','Hasil assay channel CH01-001 s.d. CH01-008 (Au, Ag, Lith, Alt)','Latihan 3'],
['<code>LTH_titik_struktur.csv</code>','10 pengukuran struktur (sesar, kekar, bedding, foliasi, shear, vein, lineasi)','Latihan 4']]))
T.append('<h1>2. Mengenal layar</h1><p>Layar Ore Works terdiri dari menu, toolbar ikon, tampilan 3D, penunjuk arah dan status bar.</p>'+
 fig('01_awal','Tampilan awal Ore Works.',['<b>Menu atas</b> — klik untuk membuka jendela tiap menu, klik lagi untuk menutup. Jendela bisa digeser dari judulnya.','<b>Toolbar ikon</b> — jalan pintas perintah yang paling sering dipakai.','<b>Penunjuk arah</b> E (merah), N (hijau), RL (biru). Klik = pandangan plan.','<b>Status bar</b> — koordinat kursor, arah pandang, skala, VE, jumlah data, nama project.'])+
 fig('02_toolbar','Toolbar ikon. Nama project bisa diubah dengan mengklik tulisan di sebelah logo.',['Buka / simpan project (.gcv.json).','Zoom ke semua data, perbesar, perkecil.','Pandangan cepat: Plan, WSW, ENE, NNW (sepanjang strike), Oblik.','Eksagerasi vertikal (VE) 1–3×.','Label adaptif, Legenda, panel Data, Slicing, Analisis.','Layout peta siap cetak (PNG/PDF) dan simpan gambar 3D (ikon kamera).','Latar tampilan 3D: Gradasi terang, Gradasi navy, Polos.'])+
 '<h2>Navigasi 3D</h2>'+tbl(['Aksi','Mouse / keyboard'],[['Putar','Seret dengan tombol kiri'],['Geser','Seret dengan tombol kanan, atau dua jari di touchpad'],['Zoom','Roda mouse / cubit touchpad'],['Kembali ke seluruh data','Ikon rumah di toolbar']])+
 fig('32_statusbar','Status bar di bagian bawah layar.',['Koordinat E / N / RL di bawah kursor.','Arah pandang dan plunge kamera.','Perkiraan skala layar.','Eksagerasi vertikal yang sedang aktif.'])+
 fig('33_latar_navy','Pilihan latar Gradasi navy — cocok untuk presentasi.'))
T.append('<h1>3. Latihan 1 — Project, data bor, topografi dan wireframe</h1><p>Tujuan: menampilkan data bor, topografi dan wireframe vein dalam satu project lalu menyimpannya.</p>'+
 '<h3>Langkah 1 — Beri nama project</h3><p>Klik tulisan <b>Project baru</b> di sebelah logo, ketik <code>Latihan Zona A</code>, tekan Enter.</p>'+
 '<h3>Langkah 2 — Impor data bor</h3><p>Menu <b>Dataset bor</b> → klik <b>Pilih</b> pada Collar, Survey, Assay dan Geologi → periksa <b>Kolom Au</b> → klik <b>Proses dataset</b>.</p>'+
 fig('03_dataset','Jendela Dataset pemboran tambahan setelah keempat file dipilih.',['Collar: <code>LTH_collar.csv</code> (42 baris).','Survey: <code>LTH_survey.csv</code>.','Assay: <code>LTH_assay.csv</code>; kolom Au terdeteksi otomatis (<code>Au_ppm</code>).','Geologi: <code>LTH_geologi.csv</code>.','<b>Proses dataset</b> — lubang muncul di 3D, berwarna menurut kadar Au.'])+
 '<h3>Langkah 3 — Impor topografi</h3><p>Menu <b>Topografi</b> → <i>Impor sebagai: Topografi</i> → <b>Impor string</b> → pilih <code>LTH_topografi.str</code>. Ore Works membuat DTM (triangulasi) seperti Surpac. Untuk desain pit, pilih <i>Desain pit</i> lalu impor file-nya.</p>'+
 fig('05_topo_menu','Menu Topografi & desain pit.',['Pilih jenis: Topografi atau Desain pit.','Impor file <code>.str</code> (teks/biner) atau <code>.dxf</code>; bisa beberapa file sekaligus.'])+
 '<h3>Langkah 4 — Impor wireframe</h3><p>Menu <b>Wireframe</b> → <b>Impor wireframe</b> → <code>LTH_V2001.obj</code>. Isi kolom <b>Domain</b> dengan <code>V2001</code>.</p>'+
 fig('06_wire_menu','Menu Wireframe geologi.',['Impor <code>.msh</code> Leapfrog, <code>.dtm</code>+<code>.str</code> Surpac (pilih keduanya), <code>.obj</code> atau <code>.dxf</code>.','Daftar wireframe: atur tampil, opasitas dan nama domain.'])+
 '<h3>Langkah 5 — Atur tampilan</h3><p>Klik ikon rumah (zoom ke semua data), lalu coba tombol <b>Plan</b>, <b>WSW</b> dan <b>NNW</b>.</p>'+
 fig('07_3d_bor_topo_wf','Data bor, topografi dan wireframe V2001 dalam satu tampilan 3D.',['Penunjuk arah: putar kamera dan perhatikan arah N/E.','Legenda otomatis menyesuaikan lapisan yang tampil.'])+
 fig('08_plan','Pandangan Plan (dari atas): collar, jejak lubang dan wireframe.')+
 '<h3>Langkah 6 — Filter bila perlu</h3>'+fig('09_filter','Menu Filter data bor: Hole_ID berisi, bench, RL collar, filter kadar, hanya di bawah topografi.',['Contoh: ketik <code>_01</code> untuk menampilkan lubang yang Hole_ID-nya memuat “_01”. Beberapa nilai dipisah titik koma.'])+
 '<h3>Langkah 7 — Simpan project</h3>'+fig('10_file','Menu File kerja project.',['<b>Simpan project</b> → file <code>Project_Latihan_Zona_A_YYYYMMDD_HHMM.gcv.json</code> terunduh.','<b>Buka project</b> → membuka lagi file .gcv.json kapan saja.']))
T.append('<h1>4. Latihan 2 — Wall mapping</h1><p>Tujuan: mengubah titik pick-up survei menjadi vein, kontak dan jejak struktur, lalu melihat vein sebagai lembaran urat 3D.</p>'+
 '<div class="note"><b>Wall mapping vs channel sampling.</b> Wall mapping mencatat <i>geometri dan pengamatan</i> (jejak vein, kontak, struktur, poligon). Channel sampling mencatat <i>interval sampel dan assay</i>, seperti satu lubang bor mendatar. Keduanya boleh di dinding yang sama dan tampil di peta yang sama.</div>'+
 '<h3>Langkah 1 — Impor pick-up</h3><p>Menu <b>Pemetaan</b> → bagian <b>1 · Titik pick-up</b> → <b>Impor pick-up</b> → <code>LTH_pickup.csv</code>. Format: <code>ID, East, North, RL, Code</code>.</p>'+
 fig('11_pickup','Titik pick-up tampil di 3D dengan label ID.',['Tombol impor pick-up (.csv / .txt / .str).'])+
 '<h3>Langkah 2 — Buat vein dari pick-up</h3><p>Bagian <b>2 · Digitasi</b>: pilih kategori <b>Vein pick-up</b>, isi layer <code>V2001</code>, lalu di kotak <b>nomor</b> ketik <code>kode:VN</code> dan klik <b>Buat</b>. Semua titik berkode VN langsung menjadi satu garis vein. Cara lain: rentang ID (<code>P001-P013</code>) atau mendigit manual dengan <b>Digit di 3D</b>.</p>'+
 fig('12_digitasi','Bagian Digitasi.',['Kategori fitur: Vein, Channel, Kontak, Jejak struktur, Poligon, Grab, Observasi.','Menempel ke: titik pick-up dan/atau permukaan topografi.','Layer (nama vein / grup).','<b>Digit di 3D</b> — klik titik di layar; Enter = selesai, Backspace = hapus titik terakhir, Esc = batal.','File pick-up sumber.','Nomor: <code>kode:VN</code>, rentang <code>P001-P013</code>, atau kosong = semua titik.','<b>Buat</b> fitur dari titik pick-up.'])+
 '<h3>Langkah 3 — Isi atribut vein</h3><p>Formulir atribut terbuka otomatis. Isi Jenis <i>Vein</i>, Tebal <code>1.8</code>, Dip <code>70</code>, Dip direction <code>250</code>, Kedalaman ke bawah <code>25</code>, Mineralogi dan Tekstur.</p>'+
 fig('13_atribut_vein','Formulir atribut vein.',['Tebal (m) — ketebalan lembaran urat.','Dip (°).','Dip direction (°, searah jarum jam dari utara).','Kedalaman ke bawah (m) — seberapa jauh vein diteruskan ke arah dip.','<b>Balik arah</b> — membalik sisi miring bila dip direction dikosongkan.'])+
 fig('14_vein3d','Vein V2001 tampil sebagai lembaran urat: tebal, miring 70° ke 250°, menerus 25 m ke bawah, dengan simbol dip di tengah jejak.')+
 '<h3>Langkah 4 — Kontak dan sesar</h3><p>Ulangi dengan kategori <b>Kontak geologi</b> (<code>kode:KT</code>, layer KT-1) dan <b>Jejak struktur</b> (<code>kode:SL</code>, layer F1; atribut Jenis <i>Sesar</i>, Dip 65, Dip direction 20). Grab sample: kategori <b>Grab sample</b>, <code>kode:GB</code>.</p>'+
 fig('18_warna_vein_opsi','Pengaturan Bentuk vein 3D dan Warna kadar channel & grab.',['Bentuk: Lembaran urat atau Tabung (versi lama).','Kedalaman bawaan dan dip bawaan (dipakai bila atribut kosong).','Variasi tebal (pinch & swell) dan simbol dip.','Unsur pewarna (kosong = Au otomatis).','Mode: Kelas kadar atau Gradasi.','Batas kelas (1–6 angka, dipisah titik koma).']))
T.append('<h1>5. Latihan 3 — Channel sampling dan hasil assay</h1><p>Tujuan: membuat channel, membaginya menjadi interval sampel, memasukkan hasil lab, melihat warna kelas kadar, lalu mengekspor.</p>'+
 '<h3>Langkah 1 — Buat channel</h3><p>Kategori <b>Channel sampling</b>, layer <code>CH01</code>, nomor <code>kode:CH</code> → <b>Buat</b>. Isi Tanggal, Geolog, Lebar channel (cm) dan Lokasi.</p>'+
 '<h3>Langkah 2 — Interval dan assay</h3><p>Interval bisa <b>per segmen titik</b> atau tiap panjang tertentu (isi meter lalu <b>Bagi</b>). Buka <b>Tempel dari Excel</b>, salin isi <code>LTH_assay_channel.txt</code> (beserta judul kolom), lalu klik <b>Tempel</b>.</p>'+
 fig('15_channel_paste','Formulir channel: atribut, pembagian interval dan kotak tempel assay.',['Lebar channel (cm).','Interval per segmen titik (atau tiap n meter).','Kotak tempel dari Excel: kolom Sample_ID, Au_ppm, Ag_ppm, Lith, Alt, Deskripsi.','<b>Tempel</b> — baris dicocokkan lewat Sample_ID, atau diisi berurutan.'])+
 fig('16_channel_tabel','Tabel interval setelah assay ditempel: From, To, panjang, Sample_ID, unsur, Lith, Alt.',['Tabel interval bisa diedit langsung.'])+
 fig('17_channel3d','Channel CH01 berwarna per kelas kadar Au; batas interval ditandai titik hitam.',['Legenda kelas kadar channel/grab (unsur & batas sesuai pengaturan).'])+
 '<h3>Langkah 3 — Ekspor</h3>'+fig('23_ekspor','Bagian 4 · Ekspor & layout.',['<b>Channel → CSV bor (4 file)</b>: Collar, Survey, Assay, Geologi untuk Surpac / database.','<b>Channel → Dataset bor</b>: channel menjadi lubang di 3D.','<b>Grab CSV</b>.','<b>Fitur CSV</b>: semua fitur + atribut.','<b>Semua fitur .str</b>: string Surpac.','<b>Layout peta</b> (PNG / PDF).']))
T.append('<h1>6. Latihan 4 — Titik struktur dan simbol geologi</h1><p>Tujuan: memasukkan pengukuran struktur dan menampilkannya sebagai bidang 3D dan simbol peta gaya USGS.</p>'+
 '<ol><li>Menu <b>Struktur</b> → <b>Impor CSV titik struktur</b> → <code>LTH_titik_struktur.csv</code> (pilih <i>Tambah</i>).</li><li>Untuk format kolom, klik <b>Template CSV</b> dan isi di Excel.</li><li>Satu per satu: buka <i>+ Tambah titik struktur</i>, isi Kategori, Jenis, E/N (atau <b>Ambil dari 3D</b>), Dip dan arah.</li></ol>'+
 fig('19_struktur_menu','Menu Struktur.',['Impor CSV titik struktur (Tambah / Ganti semua).','Template CSV.','Ukuran simbol (m).','Tampilan 3D: Bidang + simbol peta, Bidang saja, Simbol peta saja.'])+
 fig('20_struktur3d','Titik struktur sebagai cakram bidang 3D (warna per jenis) dengan simbol peta di atasnya.')+
 fig('21_struktur_plan','Pandangan plan dengan mode “Simbol peta (gaya USGS) saja”.')+
 '<h2>Arti simbol</h2>'+tbl(['Jenis','Bentuk simbol'],[['Bedding / pelapisan','Garis strike + tick pendek ke arah dip; datar = lingkaran bersilang'],['Foliasi','Garis strike + segitiga penuh'],['Shear zone','Garis strike + segitiga kosong'],['Kekar','Garis strike tipis + tick dengan kotak kecil'],['Sesar','Garis strike tebal + tick berpanah; dugaan = putus-putus'],['Vein / veinlet / stockwork','Garis strike tebal + belah ketupat + tick'],['Lineasi / striasi','Panah ke arah plunge + angka plunge']])+
 '<p>Simbol vertikal (dip ≥ 88°) digambar dengan tick ke dua sisi.</p>')
T.append('<h1>7. Latihan 5 — Layout peta, slicing, analisis dan plan bor</h1>'+
 '<h2>Layout peta siap cetak</h2><ol><li>Klik <b>Layout peta</b> di toolbar.</li><li>Pilih kertas, skala tetap (kosong = pas), judul, subjudul, pembuat, interval kontur.</li><li>Centang lapisan yang dicetak. Gulir = zoom, seret = geser.</li><li>Klik <b>PNG</b> atau <b>PDF</b>.</li></ol>'+
 fig('24_layout_dialog','Jendela Layout peta.',['<b>Pas</b> — kembali ke seluruh data.','Simpan <b>PNG</b>.','Simpan <b>PDF</b>.'])+
 fig('25_layout_hasil','Contoh hasil layout: grid koordinat, panah utara, skala, legenda simbol struktur & kelas kadar, kop.')+
 '<h2>Slicing — penampang 2D</h2><p>Klik <b>Slicing</b>. Pilih arah Vertikal, azimut garis <code>70</code> (searah lubang bor), pusat E/N, tebal irisan ±8 m, centang <b>Tampilkan bidang sayatan di 3D</b>, lalu <b>Buka penampang 2D</b>.</p>'+
 fig('26_slicing','Jendela Slicing 2D / 3D dan bidang sayatan di 3D.',['Arah: Vertikal (penampang) atau Horizontal (level RL).','Azimut garis sayatan.','Pusat E / N (atau <i>Pusat dari tampilan</i>).','Tebal irisan ± dan langkah maju/mundur.','Tampilkan bidang sayatan di 3D.','Buka penampang 2D.'])+
 fig('27_penampang2d','Penampang 2D: lubang bor berwarna kadar, topografi dan struktur; bisa disimpan PNG.',['Jendela penampang: ◀ ▶ geser sayatan, Hole ID, Pas, PNG.'])+
 '<h2>Analisis</h2>'+fig('28_analisis','Jendela Analisis dengan tab Domain, Ringkasan, Long section, Profil strike, Profil vertikal, Pertemuan vein, Envelope, Belum teruji, Interpretasi struktur, Potensi terbuka, Peta level.',['Tab analisis — dihitung ulang otomatis saat data berubah.'])+
 fig('29_peta_level','Tab Peta level: sayatan horizontal di satu RL dengan kelas kadar (interpolasi anomali), wireframe, struktur dan lubang.',['Pengaturan peta level: RL, tebal irisan, mode kadar, kelas, anisotropi, alterasi, kontur, lapisan.'])+
 '<h2>Unsur aktif (multi-elemen)</h2><p>Pilih <b>satu</b> unsur di kotak <b>Unsur</b> pada toolbar (atau di judul jendela Analisis). Pilihan berisi Au (kadar bawaan) dan semua kolom assay dari dataset bor, misalnya <code>Ag_ppm</code>. Unsur aktif dipakai untuk: warna lubang bor &amp; legenda, sampel di atas cut-off, penampang 2D, Peta level, Long section, Profil strike, Profil vertikal dan Envelope.</p><ul><li>Batas kelas tiap unsur disimpan sendiri (kotak <i>Kelas … (4 batas)</i> di Peta level). Untuk unsur baru, batas awal diambil dari persentil data (P50, P75, P90, P97,5).</li><li>Batas ke-1 ÷ 4 = batas bawah warna, batas ke-2 = cut-off sampel, batas ke-4 = batas atas warna.</li><li>Cut-off GT (Long section, Envelope) diisi dalam satuan unsur aktif × meter.</li></ul>'+fig('ue1','Unsur aktif <code>Ag_ppm</code>: warna lubang bor dan legenda berganti ke Ag.',['Kotak <b>Unsur</b> di toolbar.'] if False else None)+fig('ue_ls','Long section dengan unsur aktif Ag_ppm (kotak unsur juga ada di judul jendela Analisis).')+'<h2>Plan bor</h2>'+fig('31_plan_bor','Menu Plan bor: impor CSV rencana bor atau buat titik langsung di 3D (Titik, Garis, Grid area).',['Impor plan bor (.csv): Hole_ID, Easting, Northing, Elevation, Azimuth, Dip, Target Depth.'])+
 '<h2>Panel Data</h2>'+fig('22_panel_data','Panel Data: fitur pemetaan per kategori dan layer. Centang = tampil di 3D, klik nama = buka atribut.',['Panel Data (tombol <b>Data</b> di toolbar).']))
T.append('<h1>8. Tips &amp; pertanyaan umum</h1>'+tbl(['Pertanyaan','Jawaban'],[
['Data hilang setelah tab ditutup.','Data hanya ada di memori browser. Selalu <b>Simpan project</b> (.gcv.json) dan buka lagi lewat <b>Buka project</b>.'],
['Layar 3D kosong setelah impor.','Klik ikon rumah (zoom ke semua data). Periksa menu Filter dan centang lapisan.'],
['Topografi dan bor tidak bertemu.','Semua file harus satu sistem koordinat (E/N/RL yang sama).'],
['Vein miring ke arah salah.','Isi Dip &amp; Dip direction di atribut vein, atau klik <b>Balik arah</b>.'],
['Label saling menumpuk.','Aktifkan <b>Label</b> di toolbar (label adaptif) atau kecilkan Ukuran label di menu Tampilan.'],
['Angka desimal tidak terbaca.','Titik dan koma desimal sama-sama diterima; pemisah kolom CSV boleh koma, titik koma atau tab.'],
['Gambar untuk laporan.','Ikon kamera = gambar 3D; Layout peta = peta resmi berskala.'],
['Ekspor channel hanya 1 file terunduh.','Izinkan <i>multiple downloads</i> di browser — ekspor channel mengunduh 4 file.']])+
 '<p>Format kolom lengkap, cara kerja tiap fitur dan pemecahan masalah ada di <b>Ore Works — Petunjuk Teknis</b>.</p>')

# ======================= PETUNJUK TEKNIS =======================
FN.i=0
P=[cover('Ore Works','Petunjuk Teknis — format data, cara kerja fitur, pemecahan masalah','25_layout_hasil')]
P.append('<h1 style="page-break-before:always">1. Ringkasan teknis</h1><p>Ore Works adalah aplikasi web satu berkas (<code>Ore_Works.html</code>, ±1 MB) yang berjalan sepenuhnya di browser tanpa internet dan tanpa server.</p>'+tbl(['Komponen','Keterangan'],[
['Mesin 3D','three.js r128 + OrbitControls, tertanam di berkas (lisensi MIT)'],['Bahasa','HTML, CSS, JavaScript murni; tanpa CDN dan pustaka luar'],['Browser','Chrome / Edge terbaru (WebGL 2); Firefox belum diuji penuh'],['Data','Diproses di memori browser; tidak ada data yang dikirim ke mana pun'],['Penyimpanan','File project <code>.gcv.json</code>; nama project &amp; pilihan latar di penyimpanan lokal browser'],['Versi desktop','Installer Ore Works 0.2.0 (Windows, keluarga GC-Ex) memakai halaman yang sama, dengan lisensi per komputer']])+
 '<h1>2. Koordinat, satuan dan tampilan</h1><p>Semua data dibaca dalam satu sistem koordinat proyek: Easting (E), Northing (N), RL dalam meter. Tidak ada transformasi datum/proyeksi.</p><ul><li><b>Titik acuan</b> diambil dari data pertama yang diimpor; koordinat tetap ditampilkan dan diekspor dalam nilai asli.</li><li><b>Arah</b>: azimut dan dip direction diukur searah jarum jam dari utara (0–360°). Dip 0° = datar, 90° = tegak.</li><li><b>VE</b> 1–3× hanya untuk tampilan; ekspor dan hitungan memakai RL asli.</li><li><b>Skala layar</b> di status bar = perkiraan pada titik fokus kamera (96 dpi). Untuk skala pasti gunakan Layout peta dengan skala tetap.</li><li><b>Desimal</b>: titik dan koma diterima saat impor; ekspor memakai titik.</li></ul>'+
 fig('32_statusbar','Status bar: koordinat kursor, arah pandang, skala layar, VE.'))
P.append('<h1>3. Format impor</h1><p>Nama kolom dikenali otomatis (huruf besar/kecil tidak berpengaruh). Pemisah CSV boleh koma, titik koma atau tab.</p>'+tbl(['Data','Menu','Format','Kolom wajib (nama yang dikenali)'],[
['Collar','Dataset bor','CSV','Hole_ID (HoleID, BHID, DHID, Hole), X (East, Easting, E), Y (North, Northing, N), Z (RL, Elev, Elevation); opsional Max depth (EOH, TD, Depth, Length)'],
['Survey','Dataset bor','CSV','Hole_ID, Depth (At, Distance), Dip, Azimuth (Azi, Brg, Bearing)'],
['Assay','Dataset bor','CSV','Hole_ID, From, To + kolom unsur (Au, Au_ppm, …)'],
['Geologi','Dataset bor','CSV','Hole_ID, From, To + kolom litologi/alterasi'],
['Topografi / desain pit','Topografi','<code>.str</code> Surpac (teks/biner), <code>.dxf</code>','String dibuat DTM seperti Surpac'],
['Wireframe','Wireframe','<code>.msh</code>, <code>.dtm</code>+<code>.str</code>, <code>.obj</code>, <code>.dxf</code> 3DFACE','Satu file = satu domain'],
['Ortofoto','Topografi → Ortofoto','<code>.jpg/.png</code> + <code>.jgw/.pgw/.tfw</code>','Tanpa world file: isi E/N min–max'],
['Pick-up survei','Pemetaan','CSV atau <code>.str</code>','ID, East, North, RL, Code (judul boleh ada/tidak)'],
['Titik struktur','Struktur','CSV (Template CSV)','ID, Kategori, Jenis, X/E, Y/N, Z/RL (kosong = topografi), Dip, DipDirection / Azimuth / Trend atau Strike, Tebal, Keterangan'],
['Plan bor','Plan bor','CSV','Drillhole Name/Hole_ID, Easting, Northing, Elevation, Azimuth, Dip, Target Depth; opsional Lift/Drift rate, Distance, Extension, Comment'],
['Project','File','<code>.gcv.json</code>','Hasil Simpan project / paket zona GC-Ex']])+
 '<p>Mode dataset bor: <b>Upsert</b> (Hole_ID sama diganti) atau <b>Append</b> (hanya Hole_ID baru). Lubang berawalan PDH/MDH/DDH otomatis eksplorasi, lainnya GC.</p><p><b>Pemilihan titik pick-up</b> di kotak nomor: <code>kode:VN</code> (semua titik ber-Code VN), rentang ID <code>P001-P013</code>, daftar ID dipisah koma, atau kosong = semua.</p>')
P.append('<h1>4. Kategori fitur pemetaan</h1>'+tbl(['Kategori','ID','Geometri','String .str','Atribut'],[
['Vein pick-up','VN','Garis','1','Layer, Jenis (Vein, Veinlet, Stockwork, Breksi hidrotermal, Vein zone), Tebal (m), Dip, Dip direction, Kedalaman ke bawah (m), Tinggi ke atas (m), Mineralogi, Tekstur, Keterangan'],
['Channel sampling','CH','Garis','2','Layer, Tanggal, Geolog/sampler, Lebar channel (cm), Lokasi/bench, Keterangan + tabel interval (From, To, Sample_ID, unsur, Lith, Alt, Deskripsi)'],
['Kontak geologi','KT','Garis','3','Layer, Unit sisi satu/lain, Jenis kontak (Tajam, Gradasional, Sesar, Intrusif, Tidak pasti)'],
['Jejak struktur','SL','Garis','4','Layer, Jenis (Sesar, Sesar dugaan, Kekar, Shear zone, Breksi sesar, Lainnya), Dip, Dip direction'],
['Poligon litologi/alterasi','PG','Poligon','5','Tipe (Litologi, Alterasi, Mineralisasi, Oksidasi, Lainnya), Kode/layer, Deskripsi'],
['Grab sample','GB','Titik','6','Layer, Sample_ID, Tanggal, Litologi, Alterasi, Deskripsi + nilai unsur'],
['Stasiun observasi/foto','OB','Titik','7','Layer, Stasiun, Tanggal, No. foto, Catatan']])+
 '<p>Daftar unsur assay (mis. <code>Au_ppm, Ag_ppm, Cu_ppm</code>) diatur sekali di formulir channel/grab dan berlaku untuk semua channel dan grab.</p>'+fig('16_channel_tabel','Contoh tabel interval channel dengan unsur, Lith dan Alt.'))
P.append('<h1>5. Cara kerja fitur visual</h1><h2>Vein 3D (lembaran urat)</h2><p>Garis digitasi vein dirapatkan tiap ±0,5 m, lalu diteruskan ke arah dip sejauh <i>Kedalaman ke bawah</i> (dan ke atas sejauh <i>Tinggi ke atas</i>). Ketebalan dipasang tegak lurus bidang vein.</p><ul><li>Orientasi dari Dip &amp; Dip direction. Bila kosong: dip bawaan (80°) dan dip direction = strike garis + 90° (miring ke kanan arah digitasi).</li><li>Ketebalan = Tebal (m) × perbesar tampilan; bila kosong memakai ukuran vein bawaan.</li><li>Ujung strike dan dasar vein menipis (lensa); variasi tebal 0–80 % (bawaan 30 %) memberi pinch &amp; swell yang tetap sama setiap dibuka.</li><li>Vein zone / Stockwork transparan; Breksi hidrotermal sedikit transparan.</li><li>Ini visualisasi interpretasi, bukan wireframe estimasi; volume tidak dihitung dari lembaran ini.</li></ul>'+
 fig('14_vein3d','Vein sebagai lembaran urat 3D.')+
 '<h2>Simbol struktur</h2><p>Mengikuti gaya simbol FGDC/USGS (disederhanakan) per Jenis; diputar sesuai dip direction dan diberi angka dip. Di 3D, simbol direbahkan horizontal di titik pengukuran. Bila <i>Label dip/arah</i> aktif, angka di dalam simbol 3D dihilangkan agar tidak dobel.</p>'+fig('21_struktur_plan','Simbol struktur dalam pandangan plan.')+
 '<h2>Kelas kadar</h2><p>Batas kelas 1–6 angka (bawaan 0,4; 0,5; 1; 3 untuk Au) membentuk 2–7 kelas. Nilai yang sama dengan batas masuk kelas di atasnya (0,5 → kelas 0,5–1). Mode Gradasi memakai skala warna kontinu dari seperempat batas terendah sampai batas tertinggi.</p>'+
 '<h2>Label adaptif</h2><p>Setiap kamera bergerak, label diukur di layar: ukuran mengecil otomatis bila label banyak (×1 sampai ×0,62); label yang bertabrakan digeser ke sisi lain titiknya, dan bila tetap bertabrakan disembunyikan sementara. Prioritas: label besar (nama fitur), lalu yang paling dekat kamera.</p>')
P.append('<h1>6. Format ekspor</h1><p>CSV memakai UTF-8 (dengan BOM agar terbaca Excel), pemisah koma, titik desimal, koordinat 3 desimal. <code>YYYYMMDD</code> = tanggal ekspor.</p>'+tbl(['Tombol','Nama file','Kolom / isi'],[
['Channel → CSV bor','<code>Channel_Collar_YYYYMMDD.csv</code>','Holeid, X, Y, Z, Maxdepth, Type (CH), Tanggal, Geolog, Lebar_cm, Lokasi'],
['','<code>Channel_Survey_YYYYMMDD.csv</code>','Holeid, Depth, Dip, Azimuth — satu baris per segmen; dip positif = turun'],
['','<code>Channel_Assay_YYYYMMDD.csv</code>','Holeid, From, To, Sample_ID, kolom unsur'],
['','<code>Channel_Geologi_YYYYMMDD.csv</code>','Holeid, From, To, Lith, Alt, Deskripsi'],
['Channel → Dataset bor','(di aplikasi)','Channel menjadi lubang di 3D, filter dan analisis'],
['Grab CSV','<code>Grab_sample_YYYYMMDD.csv</code>','Sample_ID, X, Y, Z, unsur, Tanggal, Litologi, Alterasi, Deskripsi'],
['Fitur CSV','<code>Fitur_pemetaan_YYYYMMDD.csv</code>','Kategori, ID, Urut, X, Y, Z, semua atribut (di titik pertama tiap fitur)'],
['Semua fitur .str','<code>Pemetaan_YYYYMMDD.str</code>','String Surpac: nomor string = kategori (bagian 4), urutan Y, X, Z, D1 = ID fitur, D2 = Sample_ID / kode / jenis'],
['Titik struktur → Ekspor CSV','CSV','ID, Kategori, Jenis, X, Y, Z, Dip, DipDirection, Strike, Polarity, Tebal, Keterangan (bisa diimpor kembali)'],
['Layout peta','PNG / PDF','Peta dengan kop, grid, skala, panah utara, legenda'],
['Ikon kamera','<code>&lt;project&gt;_3D.png</code>','Gambar tampilan 3D saat ini'],
['Simpan project','<code>Project_&lt;nama&gt;_YYYYMMDD_HHMM.gcv.json</code>','Seluruh data, fitur, struktur, plan bor dan pengaturan']])+
 '<p>Panjang channel (From/To, Maxdepth) diukur miring sepanjang garis 3D, sehingga desurvey di Surpac menghasilkan posisi yang sama.</p>'+fig('25_layout_hasil','Contoh hasil Layout peta (PNG).'))
P.append('<h1>7. Penyimpanan, keterbatasan dan pemecahan masalah</h1><p><b>Penyimpanan.</b> Data impor, fitur dan struktur hanya ada di memori tab browser. Menutup atau memuat ulang tab menghapusnya kecuali sudah disimpan sebagai <code>.gcv.json</code>.</p><h2>Keterbatasan versi HTML</h2><ul><li>Tidak ada transformasi koordinat.</li><li>Vein 3D adalah visual interpretasi, bukan wireframe estimasi.</li><li>File sangat besar (topografi/pit ratusan MB, ortofoto &gt; 200 MB) dapat membuat browser lambat; potong area kerja dulu.</li><li>Analisis Pertemuan vein, Belum teruji, Potensi terbuka dan Filter kadar tetap memakai Au; Unsur aktif berlaku untuk warna lubang, penampang, peta level, long section, profil strike, profil vertikal dan envelope.</li><li>Simbol struktur mengikuti gaya FGDC/USGS yang disederhanakan.</li></ul>'+tbl(['Gejala','Penyebab umum','Solusi'],[
['Layar 3D hitam / kosong','WebGL nonaktif atau driver lama','Chrome/Edge terbaru; aktifkan <i>Use hardware acceleration</i>'],
['Kolom CSV tidak dikenali','Nama kolom berbeda','Ganti judul kolom sesuai bagian 3, atau pilih kolom Au manual'],
['Data tidak muncul','Koordinat jauh dari data lain','Periksa sistem koordinat; klik zoom ke semua data'],
['Ekspor tidak terunduh','Browser memblokir unduhan berganda','Izinkan <i>multiple downloads</i>'],
['Browser macet saat impor','File terlalu besar','Tunggu; bila tetap macet, perkecil file atau pakai versi desktop']])+
 '<p>Versi desktop Windows (installer Ore Works, keluarga GC-Ex) memakai halaman yang sama dengan lisensi per komputer; dapatkan dari admin GC-Ex.</p>')

FOOT='<div style="width:100%;font-size:7.5pt;color:#8a92a3;padding:0 15mm;display:flex;justify-content:space-between;font-family:Segoe UI,DejaVu Sans,Arial"><span>{t}</span><span>Halaman <span class="pageNumber"></span> / <span class="totalPages"></span></span></div>'
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(executable_path='/usr/bin/google-chrome')
        for nm,parts,t in [('Ore_Works_Tutorial_Penggunaan',T,'Ore Works — Tutorial Penggunaan'),('Ore_Works_Petunjuk_Teknis',P,'Ore Works — Petunjuk Teknis')]:
            h=f'<!DOCTYPE html><html lang="id"><head><meta charset="utf-8"><title>{t}</title><style>{CSS}</style></head><body>'+'\n'.join(parts)+'</body></html>'
            open(f'/home/claude/tut/{nm}.html','w',encoding='utf-8').write(h)
            pg=await b.new_page();await pg.goto(f'file:///home/claude/tut/{nm}.html');await pg.wait_for_timeout(1500)
            await pg.pdf(path=f'/home/claude/tut/{nm}.pdf',format='A4',print_background=True,display_header_footer=True,header_template='<div></div>',footer_template=FOOT.format(t=t),margin={'top':'16mm','bottom':'18mm','left':'15mm','right':'15mm'})
            print('ok',nm)
        await b.close()
asyncio.run(main())
