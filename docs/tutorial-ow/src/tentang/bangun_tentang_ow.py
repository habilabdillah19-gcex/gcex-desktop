import json, os, runpy, tempfile
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle,
                                PageBreak, KeepTogether, ListFlowable, ListItem)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

FD = "/usr/share/fonts/truetype/dejavu/"
pdfmetrics.registerFont(TTFont("DV", FD + "DejaVuSans.ttf"))
pdfmetrics.registerFont(TTFont("DVB", FD + "DejaVuSans-Bold.ttf"))
from reportlab.pdfbase.pdfmetrics import registerFontFamily
registerFontFamily("DV", normal="DV", bold="DVB", italic="DV", boldItalic="DVB")

ROOT = Path(__file__).resolve().parents[4]
VER = json.load(open(ROOT / "builder-ow.json", encoding="utf-8"))["extraMetadata"]["version"]
OUT = str(ROOT / "docs" / "tutorial-ow" / "Tentang_Ore_Works.pdf")
FIG = os.path.join(tempfile.gettempdir(), "tentang_ow")
runpy.run_path(str(Path(__file__).with_name("gambar_tentang_ow.py")))
BLUE = colors.HexColor("#185FA5"); GREY = colors.HexColor("#5F5E5A"); LIGHT = colors.HexColor("#E6F1FB")

st = {
 "title": ParagraphStyle("t", fontName="DVB", fontSize=26, leading=32, textColor=BLUE, alignment=TA_CENTER, spaceAfter=10),
 "sub": ParagraphStyle("s", fontName="DV", fontSize=13, leading=18, textColor=GREY, alignment=TA_CENTER, spaceAfter=6),
 "h1": ParagraphStyle("h1", fontName="DVB", fontSize=15, leading=20, textColor=BLUE, spaceBefore=10, spaceAfter=6),
 "h2": ParagraphStyle("h2", fontName="DVB", fontSize=10.5, leading=14, spaceBefore=6, spaceAfter=3),
 "b": ParagraphStyle("b", fontName="DV", fontSize=9, leading=13.2, alignment=TA_JUSTIFY, spaceAfter=5),
 "small": ParagraphStyle("sm", fontName="DV", fontSize=7.8, leading=10.5, textColor=GREY, spaceAfter=4),
 "cell": ParagraphStyle("c", fontName="DV", fontSize=8.2, leading=11),
 "cellb": ParagraphStyle("cb", fontName="DVB", fontSize=8.2, leading=11, textColor=colors.white),
}
P = lambda t, s="b": Paragraph(t, st[s])

def bullets(items):
    return ListFlowable([ListItem(P(i), leftIndent=12, value="circle") for i in items],
                        bulletType="bullet", start="•", leftIndent=12, bulletFontName="DV", bulletFontSize=8)

def table(rows, widths):
    data = [[P(c, "cellb") for c in rows[0]]] + [[P(c, "cell") for c in r] for r in rows[1:]]
    t = Table(data, colWidths=widths, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), BLUE), ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("GRID", (0,0), (-1,-1), 0.4, colors.HexColor("#B4B2A9")),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, LIGHT]),
        ("LEFTPADDING", (0,0), (-1,-1), 4), ("RIGHTPADDING", (0,0), (-1,-1), 4),
    ]))
    return t

def fig(path, caption_w=16.5):
    from PIL import Image as PI
    w, h = PI.open(path).size
    width = caption_w * cm
    return Image(path, width=width, height=width * h / w)

def qa(q, a):
    return KeepTogether([P(f"<b>T: {q}</b>", "h2"), P(a)])

def footer(c, d):
    c.saveState(); c.setFont("DV", 7.5); c.setFillColor(GREY)
    c.drawString(2*cm, 1.2*cm, f"Tentang Ore Works · versi aplikasi {VER} · hak cipta Habil Abdillah 2026")
    c.drawRightString(A4[0]-2*cm, 1.2*cm, f"Halaman {d.page}")
    c.restoreState()

story = []
# Sampul
story += [Spacer(1, 5*cm), P("Tentang Ore Works", "title"),
          P("Ore Works for Desktop: ringkasan produk untuk tim teknis dan investor", "sub"),
          Spacer(1, 1*cm),
          P(f"Versi aplikasi yang dijelaskan: {VER}<br/>Penyusun: Habil Abdillah", "sub"),
          Spacer(1, 1.2*cm),
          P("Dokumen ini meringkas produk. Teks lengkap ketentuan ada di legal/SYARAT_PENGGUNAAN.txt. "
            "Semua contoh dalam dokumen bersifat umum; tidak memuat data proyek nyata.", "small"),
          PageBreak()]

# 1
story += [P("1. Ringkasan", "h1"),
 P("Ore Works for Desktop adalah aplikasi Windows 64-bit untuk pemodelan tubuh bijih (ore body) secara 3D, "
   "analisis struktur, dan visualisasi peta. Seluruh proses berjalan di komputer pengguna. Aplikasi tidak "
   "memerlukan server, koneksi internet, atau unggahan data."),
 P("Produk didistribusikan sebagai installer NSIS x64 melalui GitHub Release. Pembaruan dipasang manual oleh "
   "admin, karena aplikasi tidak memiliki fitur pembaruan otomatis. Akses dikontrol dengan lisensi per mesin "
   "yang diverifikasi memakai tanda tangan Ed25519."),
 P("<b>Intinya:</b> offline, data tetap di mesin pengguna, satu berkas aplikasi yang mudah diaudit, dan "
   "lisensi yang terikat ke perangkat.")]

# 2
story += [P("2. Apa itu Ore Works for Desktop", "h1"),
 P("Ore Works sebelumnya dikenal sebagai Ore Studio. Nama paket instalasinya Ore Works, dengan App ID "
   "com.gcex.oreworks. Produk ini termasuk dalam keluarga aplikasi GC-Ex yang lain, tetapi bekerja sebagai "
   "aplikasi mandiri."),
 bullets([
   "<b>Platform:</b> Windows 64-bit, dibungkus Electron dan dipaketkan dengan electron-builder (NSIS).",
   "<b>Antarmuka:</b> satu berkas HTML (app-ow/index.html) dengan JavaScript murni.",
   "<b>Pustaka pihak ketiga:</b> three.js r128 (3D), geotiff.js 2.1.3 (membaca ortofoto GeoTIFF), sql.js (SQLite di browser). Semuanya berlisensi MIT.",
   "<b>Penyimpanan:</b> file proyek .owproj berbasis SQLite, dipilih dan disimpan pengguna. Format ini ada sejak versi 0.17.0.",
   "<b>Mode pemula:</b> Demo bertahap dan setelan awal, ada sejak versi 0.26.0. Kini tersedia Demo Eksplisit, Implisit, vein bercabang (Y) dan Studio Pemetaan.",
   "<b>Tampilan desktop:</b> dok Project dan Properti, tab dokumen, panel lepas-tempel, tema terang / gelap, pilihan bahasa, antarmuka studio gaya Micromine.",
   "<b>Skala data:</b> diuji sampai 400.000 baris assay, topografi ratusan MB, dan 20.000 titik pick-up di Studio Pemetaan.",
 ])]

# 3
story += [PageBreak(), P("3. Cara kerja", "h1"),
 P("Gambar 1 menunjukkan batas antara komponen. Pembungkus Electron memuat satu berkas HTML. Berkas itu "
   "membaca dan menulis proyek lokal, memverifikasi lisensi, dan memproses data di memori. Tidak ada jalur "
   "keluar ke jaringan dalam alur kerja normal."),
 fig(f"{FIG}/fig1_arsitektur.png", caption_w=12.5), Spacer(1, 6),
 P("Gambar 2 merangkum alur kerja. Data lapangan didigit di Studio Pemetaan (tampilan plan 2D di atas topografi, "
   "atau penampang tegak sejajar muka dinding). Pemodelan eksplisit memakai string penampang dan Studio Pemodelan; "
   "pemodelan implisit memakai interpolasi RBF thin-plate untuk setiap domain. "
   "Batas vein tertutup dibangun dari lajur (lane) yang disatukan. Hasil beberapa domain digabung dengan operasi union. "
   "Analisis struktur menghitung pergeseran batas pada tiap bin di dua sisi dinding (dwLo dan dwHi). Hasilnya "
   "digambar sebagai panah dan garis sebelum dan sesudah di peta 2D, serta sebagai bidang bayangan dan panah di 3D."),
 fig(f"{FIG}/fig2_alur.png"), Spacer(1, 6),
 P("Gambar 3 menunjukkan alur lisensi. Pemeriksaan ini hanya aktif pada build terpaket, sehingga pengembangan "
   "tetap bisa berjalan tanpa lisensi."),
 fig(f"{FIG}/fig3_lisensi.png")]

# 4
story += [PageBreak(), P("4. Yang ditawarkan", "h1"),
 table([
   ["Kemampuan", "Keterangan"],
   ["Impor data", "Data bor (collar, survey, assay, litologi), kanal / trench, DXF, topografi, ortofoto GeoTIFF, gambar geofisika ber-georef, Arsip GIS MapInfo dan Shapefile. Kategori kolom dipilih pengguna; tabel bisa divalidasi dan diedit."],
   ["Studio Pemetaan (F8)", "Digitasi pemetaan di plan 2D: vein, channel, kontak, struktur, poligon litologi / alterasi, grab sample, strike / dip, observasi. Snap ke pick-up, RL dari topografi / pick-up / RL tetap, filter RL opsional, tampilan muka dinding, urungkan / ulangi, atribut per fitur."],
   ["Pemodelan eksplisit", "String penampang (HW / FW, titik ikat, boolean), Studio Pemodelan untuk digitasi wireframe gaya CAD, vein bercabang dan string tertutup."],
   ["Pemodelan implisit", "Studio Implisit: interpolasi RBF per domain, snap ke kontak log geologi, splay vein (Y / Triple Y), mode stratified / laterit."],
   ["Analisis", "Dashboard geokimia; analisis struktur dengan pergeseran batas dua sisi, uji signifikansi (Mann-Whitney dan ambang 2 σ), panah dan bidang bayangan di peta 2D dan 3D."],
   ["Penampang", "Penampang 2D dengan log geologi dan kadar, seri penampang sekali klik, penanda lokasi A–A' di 3D, peta level dan Layout peta."],
   ["Layout peta", "Kop peta, grid, legenda, inset lokasi dan inset detail (2x sampai 10x), simpan PNG / PDF."],
   ["Demo dan tutorial", "Demo bertahap di dalam aplikasi dan tutorial PDF bergambar (penggunaan, vein bercabang, Studio Pemetaan)."],
   ["Proyek", "File .owproj (SQLite) untuk menyimpan dan membuka pekerjaan."],
 ], [4.4*cm, 12.1*cm]),
 Spacer(1, 6),
 P(f"<i>Catatan: daftar ini mengikuti kemampuan pada versi {VER}. Fitur yang belum diuji pada data proyek penuh "
   "ditandai pada bagian 6.</i>", "small"),
 P("Pembaruan sejak versi 0.32.6", "h2"),
 table([
   ["Versi", "Perubahan utama"],
   ["0.32.7 – 0.32.9", "Usulan struktur lebih selektif dengan uji signifikansi per lubang; ganti pandangan mempertahankan zoom dan fokus; perbaikan hasil review."],
   ["0.33.0 – 0.33.1", "Penanda lokasi penampang di 3D, peta level dan Layout peta; seri penampang sejajar sekali klik."],
   ["0.33.2", "Kerapian antarmuka: tanpa garis aksen, ikon satu warna, fokus keyboard."],
   ["0.34.0", "Studio Pemetaan (F8): seluruh fitur pemetaan didigit di plan 2D atau muka dinding."],
   ["0.34.1", "Demo Studio Pemetaan di dalam aplikasi dan tutorial PDF Studio Pemetaan."],
 ], [3.2*cm, 13.3*cm])]

# 5
story += [P("5. Kelebihan", "h1"),
 bullets([
   "<b>Offline penuh.</b> Tidak ada server, cloud, atau unggahan. Cocok untuk lokasi dengan jaringan terbatas.",
   "<b>Data tetap di pengguna.</b> Proyek disimpan sebagai berkas lokal; tidak ada pengumpulan data penggunaan.",
   "<b>Mudah diaudit.</b> Logika utama berada dalam satu berkas HTML, sehingga pemeriksaan kode relatif sederhana.",
   "<b>Visualisasi terhubung.</b> Hasil pemetaan, pemodelan dan analisis tampil konsisten di peta 2D, penampang dan 3D dari satu data.",
   "<b>Ramah pemula.</b> Demo di dalam aplikasi dan tutorial PDF bergambar untuk setiap alur utama.",
   "<b>Distribusi terkendali.</b> Installer, lisensi per mesin, dan pengujian CI (fuses, asar, gerbang lisensi) berjalan otomatis.",
 ])]

# 6
story += [PageBreak(), P("6. Keterbatasan dan risiko", "h1"),
 P("Bagian ini penting untuk investor dan tim teknis. Hal-hal berikut belum terbukti dan perlu diuji lebih lanjut:"),
 bullets([
   "Fitur analisis struktur, pemodelan dan Studio Pemetaan belum diverifikasi pada data proyek nyata yang lengkap.",
   "Ketepatan model bergantung pada kualitas dan kerapatan data bor atau kanal.",
   "Hanya Windows 64-bit. Tidak ada versi macOS atau Linux.",
   "Rendering 3D bergantung pada WebGL dan GPU. Pada perangkat lemah, tampilan bisa lambat.",
   "Pengembangan saat ini bergantung pada satu pengembang utama.",
 ]),
 Spacer(1, 6), fig(f"{FIG}/fig4_risiko.png", caption_w=14),
 P("Penilaian dalam gambar 4 bersifat kualitatif dan disusun dari kondisi produk, bukan dari data pasar.", "small")]

# 7
story += [PageBreak(), P("7. Status legal", "h1"),
 P("Bagian ini merangkum <i>legal/SYARAT_PENGGUNAAN.txt</i> dan bukan nasihat hukum. Rujuk teks lengkapnya bila "
   "diperlukan keputusan hukum."),
 table([
   ["Aspek", "Ringkasan ketentuan"],
   ["Kepemilikan", "Hak cipta dan kepemilikan kode ada pada penyusun (Habil Abdillah, 2026)."],
   ["Hak pengguna", "Lisensi non-eksklusif, tidak dapat dialihkan, dan dapat dicabut."],
   ["Batasan", "Dilarang menjual, menyalin, mengubah, atau melakukan rekayasa balik. Pemberitahuan hak cipta wajib dipertahankan. Nama produk tidak boleh dipakai tanpa izin."],
   ["Komponen pihak ketiga", "three.js, geotiff.js, dan sql.js berlisensi MIT. Teks lisensinya ada di legal-ow/."],
   ["Hasil teknis", "Hasil model dan analisis hanya pendukung keputusan. Pengguna yang kompeten wajib memverifikasinya."],
   ["Jaminan dan tanggung jawab", "Perangkat lunak tanpa jaminan. Batas tanggung jawab diatur dalam ketentuan."],
   ["Data dan privasi", "Data diproses lokal. Tidak ada data yang dikirim keluar. Pencadangan data adalah tanggung jawab pengguna."],
   ["Lisensi kunci", "Kunci dibuat dengan kunci privat yang disimpan offline oleh pemilik."],
 ], [4.2*cm, 12.3*cm])]

# 8
story += [PageBreak(), P("8. Pertanyaan untuk ahli IT dan programmer", "h1"),
 qa("Apa stack-nya?",
    "Electron sebagai pembungkus, satu berkas HTML dengan JavaScript, three.js r128 untuk 3D, dan sql.js untuk SQLite. "
    "Tidak ada backend atau server lokal. Paket dibuat dengan electron-builder."),
 qa("Bagaimana data disimpan?",
    "Di file .owproj berbasis SQLite yang dipilih pengguna. Tidak ada database terpusat."),
 qa("Apakah aplikasi memeriksa pembaruan atau mengirim data?",
    "Tidak. Konfigurasi publish bernilai null, sehingga tidak ada pemeriksaan pembaruan online. Pembaruan diberikan lewat installer baru."),
 qa("Bagaimana lisensi diverifikasi?",
    "Kunci berformat GCEX1 ditandatangani dengan Ed25519. Aplikasi memakai kunci publik untuk memverifikasi tanda tangan, "
    "lalu mencocokkan ID mesin (SHA-256 dari MachineGuid). Lisensi disimpan di lisensi.json pada folder data aplikasi pengguna."),
 qa("Bagaimana kualitas build diperiksa?",
    "CI membangun installer Windows x64 dan menjalankan pemeriksaan fuses, asar, serta gerbang lisensi. Setiap rilis menerbitkan installer beserta SHA256SUMS."),
 qa("Bisakah dikembangkan lebih lanjut?",
    "Bisa. Perubahan pada app-ow/index.html memerlukan kenaikan versi Ore Works, dan sinkronisasi cap versi lewat web-src-ow/cap_versi_ow.py."),
]

# 9
story += [PageBreak(), P("9. Pertanyaan untuk investor teknologi", "h1"),
 qa("Masalah apa yang diselesaikan?",
    "Pemodelan dan analisis tubuh bijih yang tetap berjalan tanpa koneksi, dengan data yang tidak meninggalkan perangkat. "
    "Ini relevan untuk lokasi tambang dengan jaringan terbatas atau kebijakan data yang ketat."),
 qa("Siapa penggunanya?",
    "Tim geologi, grade control, dan perencanaan tambang yang bekerja dengan data bor, kanal, dan peta."),
 qa("Bagaimana model bisnisnya?",
    "Dokumen ini tidak memuat harga atau model lisensi komersial. Keputusan tersebut ada pada pemilik produk."),
 qa("Bagaimana posisi kompetitifnya?",
    "Dokumen ini tidak memuat analisis pasar atau pesaing. Perlu riset terpisah sebelum dipakai untuk keputusan investasi."),
 qa("Seberapa siap produknya?",
    f"Versi {VER} sudah memiliki fitur inti yang berjalan dan terdistribusi. Validasi menyeluruh pada data proyek nyata "
    "belum dilaporkan. Ini adalah langkah utama yang perlu dibuktikan."),
 qa("Apa risiko utamanya?",
    "Ketergantungan pada satu pengembang, belum adanya validasi lapangan yang luas, dan distribusi hanya untuk Windows. Lihat bagian 6."),
 qa("Apa langkah berikutnya yang logis?",
    "Validasi pada beberapa data proyek, dokumentasi pengguna yang lebih lengkap, uji kinerja pada perangkat kelas kantor, "
    "dan kajian pasar."),
]

# 10
story += [P("10. Sumber dan catatan", "h1"),
 bullets([
   "app-ow/index.html: logika aplikasi.",
   "builder-ow.json: versi dan konfigurasi paket.",
   "legal/SYARAT_PENGGUNAAN.txt dan legal-ow/: ketentuan dan lisensi pihak ketiga.",
   "tools/lisensi/BACA_SAYA.md: skema kunci lisensi.",
   "docs/PANDUAN_INSTALL.md: riwayat fitur per versi.",
 ]),
 Spacer(1, 4),
 P("Semua contoh pada dokumen ini bersifat umum. Tidak ada nama perusahaan, Hole ID, atau koordinat proyek nyata.", "small")]

doc = SimpleDocTemplate(OUT, pagesize=A4, leftMargin=2*cm, rightMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm,
                        title="Tentang Ore Works", author="Habil Abdillah", subject="Ringkasan produk Ore Works for Desktop")
doc.build(story, onFirstPage=footer, onLaterPages=footer)
print("built", OUT)
