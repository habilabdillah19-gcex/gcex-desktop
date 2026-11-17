# -*- coding: utf-8 -*-
"""PDF: Ore Works — Tutorial Membangun Vein Bercabang (pemodelan string gaya Micromine + boolean union).
Gambar dari tangkap_layar_vein_cabang_ow.py (/home/claude/tut/shots/vc*.png). Gaya (CSS) diambil dari bangun_pdf_ow.py.
Hasil: docs/tutorial-ow/Ore_Works_Tutorial_Vein_Bercabang.pdf"""
import asyncio, re, json
from pathlib import Path
from PIL import Image
from playwright.async_api import async_playwright
SRC = Path(__file__).parent; OUTPDF = SRC.parent / 'Ore_Works_Tutorial_Vein_Bercabang.pdf'
SHOTS = Path('/home/claude/tut/shots'); JD = Path('/home/claude/tut/jpg'); J = 'file://' + str(JD) + '/'
CSS = re.search(r"CSS='''(.*?)'''", (SRC / 'bangun_pdf_ow.py').read_text(encoding='utf-8'), re.S).group(1)
CSS += '.svgfig{border:1px solid #b8c4d6;border-radius:3px;background:#fbfcfe}.kbd{font-family:"DejaVu Sans Mono",monospace;font-size:8.5pt;border:1px solid #9aa6b8;border-bottom-width:2px;border-radius:3px;padding:0 4px;background:#fff}'
VER = json.loads((SRC.parents[2] / 'builder-ow.json').read_text(encoding='utf-8'))['extraMetadata']['version']
TGL = '17 November 2026'
for p in sorted(SHOTS.glob('vc*.png')):
    Image.open(p).convert('RGB').save(JD / (p.stem + '.jpg'), quality=86)

class C:
    def __init__(s): s.i = 0
    def next(s): s.i += 1; return s.i
FN = C()
def fig(n, cap, calls=None):
    c = '<div class="cl">' + ''.join(f'<i>{i+1}</i><span>{t}</span>' for i, t in enumerate(calls)) + '</div>' if calls else ''
    return f'<figure><img src="{J}{n}.jpg"><figcaption><b>Gambar {FN.next()}.</b> {cap}</figcaption>{c}</figure>'
def tbl(head, rows):
    return '<table><tr>' + ''.join(f'<th>{h}</th>' for h in head) + '</tr>' + ''.join('<tr>' + ''.join(f'<td>{c}</td>' for c in r) + '</tr>' for r in rows) + '</table>'
K = lambda t: f'<span class="kbd">{t}</span>'

# skema penampang (bukan tangkapan layar): induk V1, tiga cabang, zona tumpang tindih, urutan klik
SKEMA = '''<figure><svg class="svgfig" viewBox="0 0 640 300" width="100%" xmlns="http://www.w3.org/2000/svg" font-family="DejaVu Sans,Arial" font-size="11">
<line x1="20" y1="30" x2="620" y2="30" stroke="#8d6e63" stroke-width="2"/><text x="24" y="24" fill="#6d4c41">Permukaan (RL 205)</text>
<polygon points="352,30 368,30 330,150 314,150" fill="#d81b6033" stroke="#d81b60" stroke-width="2"/>
<polygon points="322,128 334,128 214,280 202,280" fill="#1e88e533" stroke="#1e88e5" stroke-width="2"/>
<polygon points="320,128 333,128 304,280 291,280" fill="#43a04733" stroke="#43a047" stroke-width="2"/>
<polygon points="321,128 332,128 410,280 400,280" fill="#fb8c0033" stroke="#fb8c00" stroke-width="2"/>
<rect x="296" y="126" width="56" height="26" fill="none" stroke="#e53935" stroke-dasharray="4 3"/>
<line x1="20" y1="139" x2="290" y2="139" stroke="#999" stroke-dasharray="3 3"/><text x="24" y="134" fill="#555">RL percabangan ±150</text>
<text x="360" y="118" fill="#c62828">tumpang tindih ±4 m</text>
<text x="372" y="70" fill="#d81b60" font-weight="bold">V1 (induk)</text>
<text x="168" y="270" fill="#1e88e5" font-weight="bold">V1A</text><text x="268" y="270" fill="#2e7d32" font-weight="bold">V1B</text><text x="414" y="270" fill="#ef6c00" font-weight="bold">V1C</text>
<g stroke="#37474f" fill="#37474f"><line x1="470" y1="60" x2="470" y2="140" stroke-width="1.5"/><polygon points="465,134 475,134 470,144"/>
<line x1="500" y1="140" x2="500" y2="60" stroke-width="1.5"/><polygon points="495,66 505,66 500,56"/></g>
<text x="440" y="160" fill="#37474f">kontak barat ↓ lalu kontak timur ↑</text>
<text x="20" y="296" fill="#555">W</text><text x="610" y="296" fill="#555">E</text></svg>
<figcaption><b>Gambar ''' + '{n}' + '''.</b> Skema penampang E–W: vein induk V1 bercabang tiga ke bawah. Tiap kode digit sebagai poligon sendiri; induk dan cabang saling menumpang ±4 m di sekitar percabangan supaya union menyatu tanpa celah.</figcaption></figure>'''

T = []
T.append(f'''<div class="cover"><div><img class="logo" src="{J}logo.png"><h1>Membangun Vein Bercabang</h1>
<div class="st">Tutorial Ore Works — digit string per penampang (gaya Micromine) lalu boolean union</div>
<img class="hero" src="{J}vc13b_union_oblik.jpg"></div><div class="meta"><b style="color:#fff">Ore Works {VER}</b> · keluarga GC-Ex<br>Versi dokumen: {TGL}<br>
Copyright © 2026 Habil Abdillah. Seluruh data di dokumen ini fiktif.</div></div>''')
T.append('''<h1>Daftar isi</h1><div class="toc">
<div>1. Pengantar, data latihan &amp; alur kerja</div><div>2. Impor data bor &amp; warna Vein_Type</div><div>3. Menyiapkan penampang 2D</div>
<div>4. Digit string induk V1</div><div>5. Penampang berikutnya &amp; string bayangan</div><div>6. Digit cabang V1A, V1B, V1C</div>
<div>7. Menyatukan cabang (boolean union)</div><div>8. Memeriksa hasil</div><div>9. Potong topografi / bidang, ekspor &amp; simpan</div>
<div>10. Pintasan, kesalahan umum &amp; hasil uji</div></div>
<div class="note">Cara membaca gambar: kotak dan bulatan <b style="color:#e53935">merah bernomor</b> menandai tombol atau isian yang dibahas. Penjelasan tiap nomor ada di bawah gambar.</div>''')

T.append('<h1>1. Pengantar, data latihan &amp; alur kerja</h1>' + '''
<p>Vein di lapangan jarang berupa satu bidang lurus: sering satu urat induk di dekat permukaan lalu terpecah menjadi beberapa cabang ke arah bawah. Pemodelan implisit (RBF) cenderung menghaluskan percabangan seperti ini. Ore Works memakai cara <b>eksplisit</b> seperti Micromine / Surpac: geologis menggambar batas vein di tiap penampang, aplikasi menyambung string antar-penampang menjadi solid tertutup, lalu cabang <b>disatukan</b> dengan boolean union menjadi satu tubuh.</p>
<h2>Data latihan</h2><p>Folder <code>Ore_Works_Latihan/Vein_Cabang</code> di ZIP Data-Latihan (dibuat oleh <code>tools/uji/buat_data_vein_cabang_ow.py</code>; koordinat lokal fiktif E 49.870–50.060, N 80.000–80.120):</p>''' +
 tbl(['File', 'Isi'], [['<code>BR_collar.csv</code>', '91 lubang pada 13 penampang E–W (spasi 10 m), 7 lubang per penampang dari barat dan timur'],
  ['<code>BR_survey.csv</code>', 'Arah dan kemiringan lubang (–55° s.d. –85°)'], ['<code>BR_assay.csv</code>', 'Au_ppm dan Ag_ppm per 1 m'],
  ['<code>BR_geologi.csv</code>', 'Lith, Alt, <b>Vein_Type</b> (V1 / V1A / V1B / V1C, "-" = bukan vein) per 1 m'],
  ['<code>geom.json</code>', 'Geometri "sebenarnya" untuk pengujian (tidak perlu diimpor)']]) + '''
<p>Geometri sebenarnya: induk <b>V1</b> (tebal 3 m, dip 75° ke barat) dari permukaan RL 205 sampai RL 150, lalu bercabang tiga sampai RL 50 — <b>V1A</b> ke barat dan landai (60°), <b>V1B</b> hampir tegak (80°), <b>V1C</b> ke timur berlawanan arah (65°).</p>''' +
 SKEMA.replace('{n}', str(FN.next())) + '''
<h2>Alur kerja</h2><ol><li>Impor 4 tabel, warnai lubang menurut <b>Vein_Type</b>.</li><li>Buka penampang 2D tegak lurus jurus (azimut garis 90°, spasi 10 m, slab ±5 m).</li>
<li>Buat solid <b>V1</b>, digit satu poligon per penampang, pindah penampang dengan <span class="kbd">PageDown</span>.</li>
<li>Buat solid <b>V1A</b>, <b>V1B</b>, <b>V1C</b> dengan cara yang sama.</li><li>Tetapkan ketiganya sebagai <b>Cabang dari V1</b> → union otomatis.</li>
<li>Periksa di 3D dan penampang, potong topografi bila perlu, ekspor OBJ / DXF / STR+DTM, simpan project.</li></ol>''')

T.append('<h1>2. Impor data bor &amp; warna Vein_Type</h1>' + '''<h3>Langkah 1 — Impor tabel</h3>
<p>Menu <b>Data bor → Impor tabel (Collar, Survey, Assay, Geologi)</b>. Klik <b>Pilih</b> pada keempat tabel lalu <b>Proses dataset</b>. Kolom dikenali otomatis; bila nama kolom berbeda, pemetaan kolom bisa diubah manual di panel yang sama.</p>''' +
 fig('vc01_impor', 'Panel impor setelah keempat file dipilih.', ['Collar — <code>BR_collar.csv</code>.', 'Survey — <code>BR_survey.csv</code>.', 'Assay — <code>BR_assay.csv</code>.', 'Geologi — <code>BR_geologi.csv</code> (kolom Vein_Type).', '<b>Proses dataset</b>.']) +
 '<h3>Langkah 2 — Warnai lubang menurut kode vein</h3><p>Menu <b>Data bor → Warna lubang</b>, pilih <b>Geologi: Vein_Type</b>. Interval V1 / V1A / V1B / V1C kini berwarna berbeda di 3D dan di penampang.</p>' +
 fig('vc02_warna', 'Warna lubang = Geologi: Vein_Type.', ['Pilihan warna lubang. Legenda kode muncul di bawahnya.']) +
 fig('vc03_3d_bor', 'Lubang bor dari dua arah (barat dan timur) memotong vein induk dan ketiga cabangnya.'))

T.append('<h1>3. Menyiapkan penampang 2D</h1>' + '''<p>String digambar di penampang yang <b>tegak lurus jurus</b> vein. Jurus vein latihan N–S, jadi garis penampang berarah E–W (azimut 90°).</p>
<h3>Langkah 3 — Atur Slicing</h3><p>Klik <b>Slicing</b> di menu atas. Isi Arah = Vertikal (penampang), Azimut garis = <code>90</code>, Pusat E/N = <code>50000</code> / <code>80000</code>, Tebal ± = <code>5</code>, langkah = <code>10</code>, lalu <b>Buka penampang 2D</b>.</p>''' +
 fig('vc04_slicing', 'Panel Slicing.', ['Azimut garis penampang (90° = barat–timur).', 'Pusat penampang — penampang pertama di N 80.000.', 'Tebal slab ±5 m: lubang di dalam slab ikut tampil.', 'Langkah 10 m = spasi penampang (sama dengan spasi lubang).', '<b>Buka penampang 2D</b>.']) +
 '''<h3>Langkah 4 — Tampilkan log geologi</h3><p>Di jendela penampang, baris <b>Log geologi</b> mengatur pita warna di kiri dan kanan jejak lubang. Pilih <b>kiri = Vein_Type</b> dan <b>kanan = Alt</b> supaya kontak vein mudah dibaca. Gulir = zoom, seret = geser, klik ganda = pas.</p>''' +
 fig('vc05_pen2d', 'Penampang N+0 dengan log Vein_Type dan alterasi.', ['Bilah pemodelan: ✎ Digit string, solid aktif, + Solid, Snap, Hapus string ini, Urungkan.', 'Log kiri = Vein_Type.', 'Log kanan = Alt.']) +
 '<div class="note">Jendela penampang bisa diperbesar dengan menyeret sudut kanan bawahnya. Tombol ◀ ▶ di judul sama dengan <span class="kbd">PageUp</span> / <span class="kbd">PageDown</span>.</div>')

T.append('<h1>4. Digit string induk V1</h1>' + '''<h3>Langkah 5 — Buat solid V1</h3><p>Klik <b>+ Solid</b>, beri nama <code>V1</code>. Mode digit langsung aktif (tombol menjadi <b>■ Selesai digit</b>, kursor silang). Tombol <span class="kbd">D</span> juga menyalakan / mematikan mode digit.</p>
<h3>Langkah 6 — Klik batas vein</h3><p>Aturan Micromine yang dipakai: <b>satu poligon tertutup per kode vein per penampang</b>, digambar berurutan mengelilingi vein:</p>
<ol><li>Mulai di <b>atas</b> (permukaan / ujung atas interpretasi) di sisi barat.</li><li>Klik semua <b>kontak sisi barat dari atas ke bawah</b>. Dengan <b>Snap</b> menyala, titik menempel tepat di kontak interval bor.</li>
<li>Klik ujung bawah (barat lalu timur), kemudian semua <b>kontak sisi timur dari bawah ke atas</b>.</li><li>Tekan <span class="kbd">Enter</span>, klik ganda, atau klik titik awal untuk menutup.</li></ol>''' +
 fig('vc06_digit_hw', 'Sedang mendigit V1: kontak sisi barat sudah diklik, garis putus-putus mengikuti kursor.', ['<b>■ Selesai digit</b> — mode digit aktif.', '<b>Snap</b> menyala: titik menempel ke kontak interval, sampel dan string lain.']) +
 '''<div class="warn"><b>Penting — sisi, bukan From/To.</b> Lubang dari timur bertemu sisi timur vein lebih dulu, jadi kontak "From"-nya ada di sisi timur. Selalu ikuti <b>sisi</b> vein (barat ke bawah, timur ke atas), bukan urutan From/To lubang. Bila dicampur, poligon menyilang seperti angka 8 dan solid menipis atau terpuntir.</div>
<p>Titik di luar data bor (ujung atas di permukaan, ujung bawah di bawah intercept terdalam) tidak punya kontak untuk ditempeli: tahan <span class="kbd">Alt</span> saat mengklik agar titik bebas. Teruskan ujung bawah kira-kira ½ spasi bor di bawah intercept terdalam, searah kemiringan vein.</p>''' +
 fig('vc07_string1', 'String V1 di penampang pertama sudah tertutup.', ['Status solid aktif: jumlah string, volume sementara, dan "ada di penampang ini".']) +
 tbl(['Saat menggambar', 'Tombol'], [['Batalkan titik terakhir', K('Backspace') + ' atau klik kanan'], ['Batalkan string yang sedang digambar', K('Esc')],
  ['Tutup string', K('Enter') + ', klik ganda, atau klik titik awal'], ['Titik bebas (tanpa snap)', 'tahan ' + K('Alt')]]))

T.append('<h1>5. Penampang berikutnya &amp; string bayangan</h1>' + '''<h3>Langkah 7 — Pindah penampang</h3><p>Tekan <span class="kbd">PageDown</span> (maju 10 m) atau <span class="kbd">PageUp</span> (mundur). String penampang sebelumnya dan sesudahnya tampil sebagai <b>bayangan</b> putus-putus; pakai sebagai panduan agar bentuk antar-penampang konsisten. Ulangi langkah 6 sampai semua penampang yang memotong V1 terisi (13 penampang pada data latihan).</p>''' +
 fig('vc08_bayangan', 'Penampang N+10: string V1 dari penampang N+0 tampil sebagai bayangan.', ['Status: string belum ada di penampang ini.']) +
 '''<div class="note"><b>Konsistensi itu kunci.</b> Aplikasi menyambung titik ujung atas/bawah dan sisi barat/timur antar-penampang secara otomatis. Hasilnya paling rapi bila tiap string digambar dengan pola yang sama: mulai di atas-barat, berputar searah, jumlah titik kurang lebih setara. Bila sambungan di satu bagian tetap aneh, pasang <b>titik ikat</b>: <span class="kbd">Shift</span>+klik sebuah titik — sambungan ke penampang tetangga dimulai dari titik itu.</div>''' +
 tbl(['Mengedit string yang sudah ada (mode digit aktif)', 'Cara'], [['Geser titik', 'seret titiknya'], ['Sisip titik', K('Ctrl') + '+klik pada garis'],
  ['Hapus titik', 'klik kanan titik, atau arahkan kursor lalu ' + K('Delete')], ['Titik ikat / lepas', K('Shift') + '+klik titik'],
  ['Hapus seluruh string di penampang ini', 'tombol <b>Hapus string ini</b>'], ['Urungkan perubahan', K('Ctrl') + '+' + K('Z') + ' atau tombol ↶']]))

T.append('<h1>6. Digit cabang V1A, V1B, V1C</h1>' + '''<h3>Langkah 8 — Satu solid per cabang</h3><p>Klik <b>+ Solid</b> tiga kali: <code>V1A</code>, <code>V1B</code>, <code>V1C</code>. Pilih solid aktif di daftar bilah penampang, lalu digit seperti langkah 6–7 — hanya interval kode cabang itu.</p>
<h3>Langkah 9 — Daerah percabangan</h3><p>Tentukan RL percabangan dari data: di antara intercept V1 terdalam dan intercept cabang tertinggi (data latihan: ±RL 150). Agar union menyatu tanpa celah:</p>
<ul><li>Ujung bawah <b>V1</b> diteruskan ±4 m <b>di bawah</b> RL percabangan.</li><li>Ujung atas tiap <b>cabang</b> dimulai ±4 m <b>di atas</b> RL percabangan, di dalam badan V1.</li>
<li>Ujung bawah cabang: ½ spasi bor di bawah intercept terdalamnya (lihat juga penampang tetangga).</li></ul>''' +
 fig('vc09_cabang_pen', 'Penampang N+60: string V1 (merah muda) dan ketiga cabang saling menumpang di sekitar RL 150.', ['Solid aktif — ganti di sini sebelum mendigit cabang lain.']) +
 fig('vc10_sendiri_3d', 'Di 3D, empat solid masih terpisah dan saling menembus di daerah percabangan.'))

T.append('<h1>7. Menyatukan cabang (boolean union)</h1>' + '''<h3>Langkah 10 — Cabang dari V1</h3><p>Menu <b>Wireframe</b> → bagian <b>Pemodelan string (penampang)</b>. Pilih <b>V1A</b> di daftar solid, lalu pada <b>Cabang dari</b> pilih <b>V1</b>. Ulangi untuk V1B dan V1C.</p>''' +
 fig('vc11_cabang_dari', 'V1A ditetapkan sebagai cabang dari V1.', ['Daftar solid — pilih cabang yang akan disatukan.', '<b>Cabang dari</b> = V1. Induk tidak boleh berupa cabang lain.', 'Keterangan: solid ini disatukan ke induknya (volume dibaca di induk).']) +
 '''<p>Setiap kali cabang ditetapkan, induk dibangun ulang: solid V1 dan semua cabangnya di-<i>union</i> (setara Solid → Boolean → Union di Micromine). Wireframe cabang yang terpisah dihapus, sehingga hanya tersisa <b>satu wireframe V1</b> sebagai domain.</p>''' +
 fig('vc12_union_info', 'Pilih V1: status union, volume, tonase dan opsi pemotongan.', ['Status: union 4 solid · 1 bagian, volume dan tonase total (densitas 2,6 t/m³ bisa diubah).', 'Potong dengan topografi aktif (opsional).', 'Potong dengan bidang struktur, sisi atas atau bawah (opsional).']) +
 '<div class="warn">Bila status menyebut <b>2 bagian</b> atau lebih, ada cabang yang tidak menyentuh induk. Periksa daerah percabangan: perpanjang ujung atas cabang atau ujung bawah induk sampai saling menumpang. Serpihan sangat kecil dibuang otomatis dan disebut di status.</div>')

T.append('<h1>8. Memeriksa hasil</h1>' + fig('vc13_union_3d', 'Solid V1 hasil union dilihat sepanjang jurus: satu tubuh induk dengan tiga cabang ke bawah.') +
 fig('vc13b_union_oblik', 'Pandangan oblik.') + fig('vc14_union_pen', 'Penampang N+60 setelah union: garis potong solid mengikuti interval V1, V1A, V1B dan V1C.') +
 '''<h2>Daftar periksa</h2><ul><li>Status <b>tertutup</b> dan <b>1 bagian</b>.</li><li>Semua interval kode vein ada di dalam solid; interval "-" (bukan vein) di luar. Telusuri dengan PageDown di penampang.</li>
<li>Tidak ada "pinggang" (bagian menyempit tiba-tiba) antar-penampang — biasanya tanda urutan titik berbeda; perbaiki dengan titik ikat.</li>
<li>Ujung bawah tidak jauh melewati data bor.</li></ul>''')

T.append('<h1>9. Potong topografi / bidang, ekspor &amp; simpan</h1>' + '''<h3>Langkah 11 (opsional) — Pemotongan</h3><p>Pada induk V1 centang <b>Potong topografi</b> agar bagian di atas permukaan terbuang (perlu topografi aktif). <b>Potong bidang</b> memotong solid dengan bidang struktur dari menu Struktur — misalnya sesar yang memotong vein — dan menyisakan sisi atas atau bawah.</p>
<h3>Langkah 12 — Ekspor</h3>''' + fig('vc15_ekspor', 'Tombol ekspor solid.', ['<b>OBJ</b> — mesh untuk Leapfrog, Blender, dll.', '<b>DXF</b> — 3DFACE untuk Micromine, Datamine, AutoCAD.', '<b>STR+DTM</b> — pasangan Surpac (.str + .dtm).', '<b>String DXF</b> — string penampang sebagai polyline 3D.']) +
 '<h3>Langkah 13 — Simpan project</h3><p><b>File → Simpan project</b> (<code>.gcv.json</code>). Semua string, cabang, pengaturan union dan pemotongan ikut tersimpan dan dibangun ulang saat project dibuka.</p>')

T.append('<h1>10. Pintasan, kesalahan umum &amp; hasil uji</h1>' + tbl(['Gejala', 'Penyebab', 'Perbaikan'], [
 ['Solid terpuntir / menipis di tengah', 'Kontak dicampur menurut From/To lubang, bukan sisi vein', 'Gambar ulang: sisi barat ke bawah, sisi timur ke atas'],
 ['Union "2 bagian"', 'Cabang tidak menumpang induk', 'Perpanjang ujung V1 dan ujung atas cabang ±4 m saling melewati'],
 ['Solid "belum tertutup"', 'String tunggal di satu penampang dengan ujung datar, atau string rusak', 'Cek daftar string; ganti Ujung ke Runcing ke titik'],
 ['Sambungan melompat ke titik lain', 'Bentuk string antar-penampang sangat berbeda', 'Pasang titik ikat (Shift+klik)'],
 ['Klik tidak menempel ke kontak', 'Snap mati, atau sedang menahan Alt', 'Centang Snap'],
 ['PageDown tidak berpindah', 'Masih ada string yang sedang digambar', 'Enter untuk menutup atau Esc untuk membatalkan']]) +
 '<h2>Hasil uji data latihan</h2><p>Langkah tutorial ini diuji otomatis dengan <code>tools/uji/uji_pemodelan_cabang_ow.py</code> (data yang sama, string mengikuti aturan di atas):</p>' +
 tbl(['Uji', 'Hasil'], [['Solid terpisah', 'V1 22.515 · V1A 17.500 · V1B 27.144 · V1C 15.225 m³'],
  ['Union', '1 tubuh tertutup, 0 sisi tak-manifold, 77.784 m³ (tumpang tindih 4.600 m³ terhapus)'],
  ['Intercept di dalam solid', 'V1 26/26 · V1A 39/39 · V1B 65/65 · V1C 52/52'], ['Sampel bukan vein di dalam solid', '0 dari 10.809'],
  ['Puntiran sisi barat ↔ timur', '0 di keempat solid'], ['Presisi vs geometri sebenarnya', '96–98 %'],
  ['Kelengkapan (recall)', '96–98 % di atas percabangan · 90–92 % RL 100–150 · ±57 % di bawah RL 100 (sengaja tidak dimodelkan jauh di bawah data bor)']]) +
 '<div class="note">Recall di bawah RL 100 rendah karena vein sebenarnya menerus sampai RL 50 sedangkan intercept terdalam ±RL 85–100. Itu keputusan interpretasi yang wajar: solid tidak diteruskan jauh melewati data.</div>')

FOOT = '<div style="width:100%;font-size:7.5pt;color:#8a92a3;padding:0 15mm;display:flex;justify-content:space-between;font-family:Segoe UI,DejaVu Sans,Arial"><span>{t}</span><span>Halaman <span class="pageNumber"></span> / <span class="totalPages"></span></span></div>'
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path='/usr/bin/google-chrome'); t = 'Ore Works — Tutorial Vein Bercabang'
        h = f'<!DOCTYPE html><html lang="id"><head><meta charset="utf-8"><title>{t}</title><style>{CSS}</style></head><body>' + '\n'.join(T) + '</body></html>'
        hp = Path('/home/claude/tut/Ore_Works_Tutorial_Vein_Bercabang.html'); hp.write_text(h, encoding='utf-8')
        pg = await b.new_page(); await pg.goto('file://' + str(hp)); await pg.wait_for_timeout(1500)
        await pg.pdf(path=str(OUTPDF), format='A4', print_background=True, display_header_footer=True, header_template='<div></div>', footer_template=FOOT.format(t=t), margin={'top': '16mm', 'bottom': '18mm', 'left': '15mm', 'right': '15mm'})
        await b.close(); print('ok', OUTPDF)
asyncio.run(main())
