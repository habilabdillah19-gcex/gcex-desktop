# -*- coding: utf-8 -*-
"""PDF: Ore Works — Tutorial Studio Pemetaan (digitasi pemetaan di plan 2D, F8).
Gambar dari tangkap_layar_studio_pemetaan_ow.py (/home/claude/tut/shots/sp*.png). Gaya (CSS) diambil dari bangun_pdf_ow.py.
Hasil: docs/tutorial-ow/Ore_Works_Tutorial_Studio_Pemetaan.pdf"""
import asyncio, re, json
from pathlib import Path
from PIL import Image
from playwright.async_api import async_playwright
SRC = Path(__file__).parent; OUTPDF = SRC.parent / 'Ore_Works_Tutorial_Studio_Pemetaan.pdf'
SHOTS = Path('/home/claude/tut/shots'); JD = Path('/home/claude/tut/jpg'); JD.mkdir(parents=True, exist_ok=True); J = 'file://' + str(JD) + '/'
CSS = re.search(r"CSS='''(.*?)'''", (SRC / 'bangun_pdf_ow.py').read_text(encoding='utf-8'), re.S).group(1)
CSS += '.kbd{font-family:"DejaVu Sans Mono",monospace;font-size:8.5pt;border:1px solid #9aa6b8;border-bottom-width:2px;border-radius:3px;padding:0 4px;background:#fff}'
VER = json.loads((SRC.parents[2] / 'builder-ow.json').read_text(encoding='utf-8'))['extraMetadata']['version']
TGL = '26 November 2026'
for p in sorted(SHOTS.glob('sp*.png')):
    Image.open(p).convert('RGB').save(JD / (p.stem + '.jpg'), quality=86)
logo = SRC.parents[2] / 'build' / 'ow-icon.png'
if not (JD / 'logo.png').exists() and logo.exists():
    Image.open(logo).save(JD / 'logo.png')

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

T = []
T.append(f'''<div class="cover"><div><img class="logo" src="{J}logo.png"><h1>Studio Pemetaan</h1>
<div class="st">Tutorial Ore Works — digitasi pemetaan lapangan di plan 2D (F8)</div>
<img class="hero" src="{J}sp08_hasil_plan.jpg"></div><div class="meta"><b style="color:#fff">Ore Works {VER}</b> · keluarga GC-Ex<br>Versi dokumen: {TGL}<br>
Copyright © 2026 Habil Abdillah. Data contoh di dokumen ini fiktif.</div></div>''')
T.append('''<h1 style="page-break-before:always">Daftar isi</h1><div class="toc">
<div>1. Apa itu Studio Pemetaan</div><div>2. Menyiapkan data &amp; membuka studio</div><div>3. Mengenal layar</div><div>4. Mendigit di plan</div>
<div>5. Strike / dip</div><div>6. Atribut &amp; mengedit</div><div>7. Filter RL (pit bertingkat)</div><div>8. Muka dinding</div>
<div>9. Hasil di 3D, tema &amp; demo</div><div>10. Pintasan &amp; pertanyaan umum</div></div>
<div class="note">Cara membaca gambar: kotak dan bulatan <b style="color:#e53935">merah bernomor</b> menandai tombol atau isian yang dibahas. Penjelasan tiap nomor ada di bawah gambar.</div>''')
T.append('<h1>1. Apa itu Studio Pemetaan</h1>' + '''<p><b>Studio Pemetaan</b> adalah meja gambar 2D tampak atas (plan) untuk mendigit hasil pemetaan lapangan — vein, channel, kontak, jejak struktur, poligon litologi / alterasi, grab sample, strike / dip dan stasiun observasi — seperti mendigit di peta kertas. Tampilannya mengikuti Studio Pemodelan: alat di kiri, peta besar di tengah, daftar fitur dan atribut di kanan.</p>
<ul><li>Tampilan 2D, tetapi tiap titik tetap punya RL: bawaan diambil dari <b>topografi</b> (atau dari titik pick-up bila kursor menempel ke pick-up), jadi hasilnya fitur 3D.</li>
<li>Semua hasil masuk ke data pemetaan yang sama dengan menu <i>Pemetaan › Digitasi</i>: langsung tampil di 3D, panel Data, Layout peta, ekspor (.str, CSV) dan tersimpan di project.</li>
<li>Untuk pit bertingkat ada <b>Filter RL</b> (opsi), untuk dinding ada tampilan <b>Muka dinding</b> (opsi).</li></ul>
<div class="note">Data latihan: folder <code>Ore_Works_Latihan</code> di ZIP data latihan (<code>LTH_collar/survey/assay/geologi.csv</code>, <code>LTH_topografi.str</code>, <code>LTH_pickup.csv</code>). Ortofoto di gambar dibuat dari bayangan topografi (fiktif).</div>''')
T.append('<h1>2. Menyiapkan data &amp; membuka studio</h1>' + '''<ol><li>Muat data bor (<b>Data bor</b>), topografi (<b>Permukaan</b>) dan titik pick-up (<b>Pemetaan › 1 · Titik pick-up</b>). Ortofoto (opsional) lewat menu Permukaan / Ortofoto.</li>
<li>Buka studio dengan salah satu cara: tekan ''' + K('F8') + ''', menu <b>Pemetaan › Studio Pemetaan (F8)</b>, ikon peta di toolbar, atau tombol <b>Studio Pemetaan (2D)</b> di jendela <i>2 · Digitasi</i>.</li>
<li>Tekan ''' + K('F8') + ''' lagi atau <b>✕ Tutup</b> untuk kembali ke 3D.</li></ol>''' +
 fig('sp01_menu', 'Pintu masuk Studio Pemetaan.', ['Menu <b>Pemetaan › Studio Pemetaan (F8)</b>.', 'Ikon peta di toolbar (di sebelah Studio Pemodelan).']))
T.append('<h1>3. Mengenal layar</h1>' + fig('sp02_layar', 'Layar Studio Pemetaan dengan data latihan.', ['<b>Alat</b> (kiri): Pilih, Vein, Channel, Kontak, Struktur, Poligon, Grab, Strike/dip, Observasi, Ukur, Garis dinding. Angka di bawah ikon = tombol pintas.', '<b>Peta</b>: kontur otomatis dari topografi, ortofoto, pick-up, lubang bor dan fitur. Gulir = zoom, seret = geser.', '<b>Fitur pemetaan</b>: pohon Kategori → Layer → Fitur, centang tampil, cari; di bawahnya <b>Atribut</b> fitur terpilih.', '<b>Bilah atas</b>: layer, kategori, tampilan, sumber RL, filter, snap.', '<b>Intip 3D</b> — Tab = besar / kecil.', '<b>Status bar</b>: koordinat & RL kursor (sumber RL ditulis dalam kurung) dan pesan.']) +
 fig('sp03_bilah', 'Bilah atas.', ['<b>Layer</b> — fitur baru masuk layer ini (mis. nama vein atau bench).', '<b>Kategori</b> — ikut alat yang dipilih.', '<b>Tampilan</b>: Plan / Muka dinding.', '<b>RL titik</b>: Topografi (bawaan), Pick-up (RL titik pick-up terdekat ≤ 8 m), RL tetap.', '<b>Filter RL</b> — bawaan mati; hanya untuk pit bertingkat.', '<b>Snap</b> (menempel ke pick-up & titik fitur), Ortho, Grid, Pas, zoom.', '<b>☰ Latar</b> — lapisan peta.', 'Urungkan / ulangi.']) +
 fig('sp04_latar', 'Panel ☰ Latar: centang lapisan yang ingin dilihat.', ['Kontur topografi (dibuat otomatis dari permukaan, juga untuk topografi berupa grid / titik), ortofoto, string desain pit, pick-up, lubang bor, fitur, titik strike / dip; pilihan "di luar RL / tebal: samar".']))
T.append('<h1>4. Mendigit di plan</h1>' + '''<h3>Langkah 1 — Garis vein</h3><ol><li>Isi <b>Layer</b>, mis. <code>VN_Latihan</code> (Enter).</li><li>Pilih alat <b>Vein</b> (''' + K('1') + ''').</li><li>Klik titik demi titik di sepanjang singkapan. Lingkaran hijau "snap: pick-up …" = titik menempel tepat ke titik survei (E, N dan RL ikut titik itu). Tahan ''' + K('Alt') + ''' untuk klik bebas, ''' + K('Shift') + ''' untuk arah 0 / 45 / 90°.</li>
<li>''' + K('Enter') + ''' atau klik ganda = selesai. Klik kanan = hapus titik terakhir, ''' + K('Esc') + ''' = batal.</li></ol>''' +
 fig('sp05_digit_vein', 'Mendigit vein; garis sementara mengikuti kursor.', ['Alat Vein (tombol 1).', 'Petunjuk alat yang aktif.']) +
 '<h3>Langkah 2 — Kategori lain</h3>' + tbl(['Alat', 'Cara', 'Catatan'], [
  ['Channel ' + K('2'), 'Klik awal & akhir channel, Enter', 'Interval sampel dibuat otomatis; kadar lewat Editor lengkap / tempel dari Excel'],
  ['Kontak ' + K('3'), 'Klik titik-titik, Enter', 'Jenis kontak (tajam, gradasional, sesar, …) di atribut'],
  ['Struktur ' + K('4'), 'Klik titik-titik, Enter', 'Jenis sesar dugaan digambar putus-putus; dip & arah dip tampil sebagai tick'],
  ['Poligon ' + K('5'), 'Klik titik-titik, klik titik pertama / Enter = tutup', 'Kode litologi / alterasi di atribut'],
  ['Grab ' + K('6'), 'Satu klik = satu titik', 'Sample_ID & kadar di atribut / Editor lengkap'],
  ['Observasi ' + K('8'), 'Satu klik = satu titik', 'Foto & catatan lewat Editor lengkap']]) +
 fig('sp08_hasil_plan', 'Hasil digit dengan data latihan: vein, channel, kontak, sesar, poligon alterasi, grab, strike/dip dan observasi.', ['Daftar fitur per kategori dan layer; klik nama = pilih & pusatkan peta.']))
T.append('<h1>5. Strike / dip</h1>' + '''<ol><li>Pilih alat <b>Strike/dip</b> (''' + K('7') + ''').</li><li>Pilih <b>Jenis</b> dan isi <b>Dip</b> di bilah atas.</li><li>Klik lokasi lalu <b>seret</b> ke arah strike. Aturan tangan kanan: dip ke kanan arah seret (dip direction = strike + 90°). Klik tanpa seret memakai kolom <b>strike</b>.</li></ol><p>Hasilnya masuk ke <b>Titik struktur</b> (menu Struktur), jadi tampil sebagai bidang + simbol di 3D dan di Layout peta.</p>''' +
 fig('sp07_strike_dip', 'Menyeret arah strike.', ['Alat Strike/dip (7).', 'Jenis struktur.', 'Dip (°).', 'Strike (°) bila tidak diseret.']))
T.append('<h1>6. Atribut &amp; mengedit</h1>' + '''<p>Fitur yang baru dibuat langsung terpilih; atributnya tampil di panel kanan. Ubah nilai lalu pindah kolom / Enter — tersimpan seketika.</p>''' +
 fig('sp06_atribut', 'Fitur terpilih di daftar dan panel atributnya.', ['Fitur terpilih di daftar.', 'Atribut: nama, layer, jenis, tebal, dip, dip direction, kedalaman, dll. Tombol <b>Balik arah</b>, <b>Ikuti topografi</b> (sisip titik tiap ±1 m menempel ke topografi), <b>Editor lengkap</b> (interval channel, kadar, warna, foto), <b>Lihat di 3D</b>, <b>Hapus</b>.']) +
 tbl(['Aksi (alat Pilih ' + K('V') + ')', 'Cara'], [['Pilih fitur', 'Klik garis / titik / dalam poligon, atau klik nama di daftar'], ['Pindah titik', 'Seret kotak titik (snap tetap berlaku)'], ['Sisip titik', K('Ctrl') + '+klik pada garis'], ['Hapus satu titik', 'Klik kanan pada kotak titik'], ['Hapus fitur', K('Delete')], ['Urungkan / ulangi', K('Ctrl') + '+' + K('Z') + ' / ' + K('Ctrl') + '+' + K('Y')]]) +
 fig('sp09_edit', 'Menyeret titik vein.', ['Alat Pilih (V).', 'Urungkan bila salah.']))
T.append('<h1>7. Filter RL (pit bertingkat)</h1>' + '''<p>Pemetaan permukaan tidak memerlukan bench. Di pit yang sudah tergali, titik pick-up dari beberapa bench bertumpuk di XY yang hampir sama, sehingga snap bisa menempel ke bench yang salah. Untuk kasus itu nyalakan <b>Filter RL</b>: hanya titik dan fitur di dalam RL ± tebal yang terang dan bisa di-snap; ''' + K('PgUp') + ' / ' + K('PgDn') + ''' naik / turun satu langkah.</p>''' +
 fig('sp10_filter_rl', 'Filter RL menyala.', ['Centang Filter RL.', 'RL pusat (◀ ▶).', 'Tebal ± (m).']))
T.append('<h1>8. Muka dinding</h1>' + '''<ol><li>Pilih alat <b>Garis dinding</b> (''' + K('W') + ''') lalu klik dua titik di plan sejajar dinding yang dipetakan.</li><li>Tampilan berganti ke <b>Muka dinding</b>: sumbu datar = jarak sepanjang dinding, sumbu tegak = RL. Profil topografi / desain pit, pick-up dan lubang bor dalam tebal ± ditampilkan.</li><li>Digit seperti biasa; titik jatuh di bidang dinding (atau tepat di pick-up bila menempel).</li><li>Kembali dengan tombol <b>Plan</b>.</li></ol>''' +
 fig('sp11_dinding', 'Tampilan Muka dinding dengan kontak yang baru didigit.', ['Tombol Muka dinding (dan Plan).', 'Tebal ± dinding.', 'Alat Garis dinding (W).']))
T.append('<h1>9. Hasil di 3D, tema &amp; demo</h1>' + fig('sp13_hasil_3d', 'Setelah studio ditutup: semua fitur sudah ada di 3D.') +
 fig('sp12_gelap', 'Tema gelap (◐ Tema); pilihan tema, snap, grid dan lapisan diingat per komputer.', ['Tombol Tema.']) +
 '<div class="note"><b>▶ Demo</b> di kepala jendela Studio Pemetaan (atau dialog Demo › <i>Demo Pemetaan</i>) memutar peragaan otomatis dengan data simulasi: memuat data, mendigit tiap kategori, mengedit, muka dinding sampai hasil di 3D. Kendali: ' + K('Spasi') + ' jeda, ' + K('→') + ' lompat, ' + K('Esc') + ' stop, kecepatan 0,5× / 1× / 2×.</div>')
T.append('<h1>10. Pintasan &amp; pertanyaan umum</h1>' + tbl(['Tombol', 'Fungsi'], [
 [K('F8'), 'Buka / tutup Studio Pemetaan'], [K('V') + ' ' + K('1') + '–' + K('8') + ' ' + K('M') + ' ' + K('W'), 'Pilih · Vein · Channel · Kontak · Struktur · Poligon · Grab · Strike/dip · Observasi · Ukur · Garis dinding'],
 [K('Enter') + ' / klik ganda', 'Selesaikan garis / poligon'], ['Klik kanan', 'Hapus titik terakhir (saat digit) / hapus titik (alat Pilih)'], [K('Esc'), 'Batalkan digit / lepas pilihan'],
 [K('Alt') + ' / ' + K('Shift'), 'Tanpa snap / ortho'], [K('Ctrl') + '+' + K('Z') + ' / ' + K('Y'), 'Urungkan / ulangi'], [K('PgUp') + ' / ' + K('PgDn'), 'RL naik / turun (Filter RL)'], [K('F') + ' / ' + K('+') + ' ' + K('−'), 'Pas / zoom'], [K('Tab'), 'Intip 3D besar / kecil'], [K('F11'), 'Layar penuh']]) +
 tbl(['Pertanyaan', 'Jawaban'], [
 ['Titik saya RL-nya 0 / aneh.', 'Belum ada topografi di bawah titik itu. Muat topografi, pakai RL titik "Pick-up", atau "RL tetap".'],
 ['Kursor menempel ke titik yang salah.', 'Tahan Alt saat klik, matikan Snap, atau nyalakan Filter RL di pit bertingkat.'],
 ['Pintasan angka tidak jalan.', 'Fokus masih di kolom isian; tekan Enter atau klik peta dulu.'],
 ['Kontur tidak muncul.', 'Centang Kontur topografi di ☰ Latar, dan pastikan permukaan topografi tercentang tampil.'],
 ['Bagaimana mengisi kadar channel?', 'Pilih channel → Editor lengkap → tempel dari Excel (Sample_ID + kolom unsur).']]))

FOOT = '<div style="width:100%;font-size:7.5pt;color:#8a92a3;padding:0 15mm;display:flex;justify-content:space-between;font-family:Segoe UI,DejaVu Sans,Arial"><span>{t}</span><span>Halaman <span class="pageNumber"></span> / <span class="totalPages"></span></span></div>'
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path='/usr/bin/google-chrome'); t = 'Ore Works — Tutorial Studio Pemetaan'
        h = f'<!DOCTYPE html><html lang="id"><head><meta charset="utf-8"><title>{t}</title><style>{CSS}</style></head><body>' + '\n'.join(T) + '</body></html>'
        hp = Path('/home/claude/tut/Ore_Works_Tutorial_Studio_Pemetaan.html'); hp.write_text(h, encoding='utf-8')
        pg = await b.new_page(); await pg.goto('file://' + str(hp)); await pg.wait_for_timeout(1500)
        await pg.pdf(path=str(OUTPDF), format='A4', print_background=True, display_header_footer=True, header_template='<div></div>', footer_template=FOOT.format(t=t), margin={'top': '16mm', 'bottom': '18mm', 'left': '15mm', 'right': '15mm'})
        await b.close(); print('ok', OUTPDF)
asyncio.run(main())
