"""Membangun 'Tentang Pit Studio for Desktop' (PDF) — panduan menjawab pertanyaan ahli IT & investor.
Pemakaian: python buat_tentang_ps.py <folder gambar> <berkas PDF keluaran>
Gambar dibuat oleh gambar.py; tangkapan layar memakai data latihan FIKTIF. Tanpa internet."""
import sys, os
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, Image, Table, TableStyle,
                                PageBreak, KeepTogether, NextPageTemplate, CondPageBreak)

IMG, OUT = sys.argv[1], sys.argv[2]
FD = "/usr/share/fonts/truetype/dejavu/"
pdfmetrics.registerFont(TTFont("DV", FD + "DejaVuSans.ttf"))
pdfmetrics.registerFont(TTFont("DVB", FD + "DejaVuSans-Bold.ttf"))
pdfmetrics.registerFont(TTFont("DVI", FD + "DejaVuSans-Oblique.ttf"))
pdfmetrics.registerFont(TTFont("DVBI", FD + "DejaVuSans-BoldOblique.ttf"))
from reportlab.lib.fonts import addMapping
addMapping("DV", 0, 0, "DV"); addMapping("DV", 1, 0, "DVB"); addMapping("DV", 0, 1, "DVI"); addMapping("DV", 1, 1, "DVBI")

NV, GD, AC, PN, LN, MU = (colors.HexColor(c) for c in ("#1C2733", "#B5893E", "#2B5F9E", "#F7F5F0", "#D3CDC1", "#6b7280"))
GR, KU, MR = colors.HexColor("#2f9e44"), colors.HexColor("#e8a33d"), colors.HexColor("#c92a2a")
VER, TGL = "0.1.8", "28 November 2026"

S = {}
S["b"] = ParagraphStyle("b", fontName="DV", fontSize=9.6, leading=14, textColor=NV, spaceAfter=5)
S["s"] = ParagraphStyle("s", parent=S["b"], fontSize=8.4, leading=11.6, textColor=MU)
S["h1"] = ParagraphStyle("h1", fontName="DVB", fontSize=17, leading=21, textColor=NV, spaceBefore=2, spaceAfter=4)
S["h2"] = ParagraphStyle("h2", fontName="DVB", fontSize=11.5, leading=15, textColor=AC, spaceBefore=9, spaceAfter=4)
S["kk"] = ParagraphStyle("kk", fontName="DVB", fontSize=8, leading=10, textColor=GD, spaceAfter=1)
S["li"] = ParagraphStyle("li", parent=S["b"], leftIndent=12, bulletIndent=2, spaceAfter=2.5)
S["td"] = ParagraphStyle("td", fontName="DV", fontSize=8.4, leading=11.2, textColor=NV)
S["th"] = ParagraphStyle("th", fontName="DVB", fontSize=8.4, leading=11.2, textColor=colors.white)
S["q"] = ParagraphStyle("q", fontName="DVB", fontSize=9.6, leading=13, textColor=NV, spaceBefore=6, spaceAfter=2)
S["a"] = ParagraphStyle("a", parent=S["b"], leftIndent=10, borderPadding=(5, 6, 5, 8), backColor=PN, borderColor=GD,
                        borderWidth=0, spaceAfter=7)
S["cap"] = ParagraphStyle("cap", parent=S["s"], fontSize=7.8, leading=10, alignment=TA_CENTER, spaceBefore=2, spaceAfter=8)
S["pitch"] = ParagraphStyle("pitch", parent=S["b"], fontSize=11, leading=16.5, textColor=NV)

W = A4[0] - 36 * mm


def P(t, st="b"):
    return Paragraph(t, S[st])


def L(items, st="li"):
    return [Paragraph(t, S[st], bulletText="•") for t in items]


def fig(n, w=W, cap=None):
    from PIL import Image as PI
    p = os.path.join(IMG, n); iw, ih = PI.open(p).size
    out = [Image(p, width=w, height=w * ih / iw)]
    if cap: out.append(P(cap, "cap"))
    return out


def tbl(rows, cw, head=True, zebra=True, fs=None):
    data = [[c if not isinstance(c, str) else Paragraph(c, S["th"] if (head and i == 0) else S["td"]) for c in r] for i, r in enumerate(rows)]
    t = Table(data, colWidths=cw, repeatRows=1 if head else 0)
    st = [("VALIGN", (0, 0), (-1, -1), "TOP"), ("LINEBELOW", (0, 0), (-1, -1), 0.4, LN),
          ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4), ("LEFTPADDING", (0, 0), (-1, -1), 5)]
    if head: st += [("BACKGROUND", (0, 0), (-1, 0), NV)]
    if zebra:
        for i in range(1 if head else 0, len(rows)):
            if i % 2 == 0: st.append(("BACKGROUND", (0, i), (-1, i), colors.HexColor("#fbfaf7")))
    t.setStyle(TableStyle(st)); return t


def QA(q, a, tip=None):
    out = [P(q, "q"), P(a, "a")]
    if tip: out.insert(2, P("<i>Catatan untuk Anda: " + tip + "</i>", "s"))
    return KeepTogether(out)


def kartu(items, cols=3):
    cells, row = [], []
    for k, v in items:
        row.append([P(k, "kk"), Paragraph(v, ParagraphStyle("kv", fontName="DVB", fontSize=11, leading=14, textColor=NV))])
        if len(row) == cols: cells.append(row); row = []
    if row: cells.append(row + [""] * (cols - len(row)))
    t = Table(cells, colWidths=[W / cols] * cols)
    t.setStyle(TableStyle([("BOX", (0, 0), (-1, -1), 0.6, LN), ("INNERGRID", (0, 0), (-1, -1), 0.6, LN),
                           ("BACKGROUND", (0, 0), (-1, -1), PN), ("VALIGN", (0, 0), (-1, -1), "TOP"),
                           ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 7)]))
    return t


def sampul(c, d):
    w, h = A4
    c.saveState(); c.setFillColor(NV); c.rect(0, 0, w, h, fill=1, stroke=0)
    c.setFillColor(GD); c.rect(18 * mm, h - 92 * mm, 26 * mm, 2.2 * mm, fill=1, stroke=0)
    c.setFillColor(colors.white); c.setFont("DVB", 12); c.drawString(18 * mm, h - 70 * mm, "TENTANG")
    c.setFont("DVB", 34); c.drawString(18 * mm, h - 85 * mm, "Pit Studio for Desktop")
    c.setFont("DV", 13); c.setFillColor(colors.HexColor("#d9dee5"))
    c.drawString(18 * mm, h - 104 * mm, "Apa itu, bagaimana bekerja, apa yang ditawarkan,")
    c.drawString(18 * mm, h - 111 * mm, "kelebihan, status legal — dan cara menjawab pertanyaan")
    c.drawString(18 * mm, h - 118 * mm, "ahli IT / programmer dan investor teknologi.")
    y = 70 * mm
    c.setFillColor(GD); c.setFont("DVB", 9); c.drawString(18 * mm, y + 16 * mm, "VERSI DOKUMEN")
    c.setFillColor(colors.white); c.setFont("DV", 10)
    c.drawString(18 * mm, y + 10 * mm, f"Pit Studio {VER} (Windows 64-bit) · {TGL}")
    c.drawString(18 * mm, y + 4 * mm, "Keluarga GC-Ex · Copyright © 2026 Habil Abdillah")
    c.setFillColor(colors.HexColor("#9aa5b1")); c.setFont("DV", 8)
    c.drawString(18 * mm, 22 * mm, "Tangkapan layar memakai data latihan fiktif. Bagian legal adalah ringkasan fakta, bukan nasihat hukum.")
    c.drawString(18 * mm, 17 * mm, "Angka teknis diambil dari kode sumber dan hasil uji pada tanggal dokumen ini.")
    c.restoreState()


def hal(c, d):
    w, h = A4
    c.saveState(); c.setStrokeColor(LN); c.setLineWidth(0.5); c.line(18 * mm, h - 13 * mm, w - 18 * mm, h - 13 * mm)
    c.setFont("DV", 7.5); c.setFillColor(MU)
    c.drawString(18 * mm, h - 11 * mm, "Tentang Pit Studio for Desktop")
    c.drawRightString(w - 18 * mm, h - 11 * mm, f"versi {VER} · {TGL}")
    c.line(18 * mm, 13 * mm, w - 18 * mm, 13 * mm)
    c.drawString(18 * mm, 9 * mm, "© 2026 Habil Abdillah · keluarga GC-Ex")
    c.drawRightString(w - 18 * mm, 9 * mm, str(d.page))
    c.setFillColor(GD); c.rect(18 * mm, h - 13.4 * mm, 14 * mm, 0.9 * mm, fill=1, stroke=0)
    c.restoreState()


doc = BaseDocTemplate(OUT, pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm, topMargin=18 * mm, bottomMargin=18 * mm,
                      title="Tentang Pit Studio for Desktop", author="Habil Abdillah", subject="Pit Studio — tentang produk, cara kerja, legal")
fr = Frame(18 * mm, 18 * mm, W, A4[1] - 36 * mm, id="f")
doc.addPageTemplates([PageTemplate("cover", frames=[fr], onPage=sampul), PageTemplate("isi", frames=[fr], onPage=hal)])
E = [NextPageTemplate("isi"), PageBreak()]

# ---------------- 1. Cara memakai + jawaban 30 detik
E += [P("Cara memakai dokumen ini", "h1"),
      P("Dokumen ini disusun sebagai <b>bahan jawaban</b>. Tiap bagian dibuka dengan jawaban singkat yang bisa Anda ucapkan, "
        "lalu rincian untuk pertanyaan lanjutan. Bagian 8 dan 9 berisi bank pertanyaan dengan saran jawaban — terpisah untuk "
        "<b>ahli IT / programmer</b> (yang akan menguji cara kerja dan keamanan) dan <b>investor</b> (yang akan menguji pasar, "
        "kepemilikan dan risiko). Bagian 6 dan 7 sengaja jujur tentang hal yang belum beres: penanya yang berpengalaman "
        "akan menemukannya sendiri, dan jauh lebih baik bila Anda yang menyebutkannya lebih dulu."),
      P("Jawaban 30 detik", "h2"),
      P("“<b>Pit Studio</b> adalah aplikasi desktop Windows untuk <b>mendesain pit tambang terbuka</b> — pit final, staging, "
        "jalan tambang — lalu <b>menjadwalkan penggaliannya</b> dan langsung melihat <b>tonase, kadar dan stripping ratio</b> dari "
        "block model. Semuanya berjalan <b>offline</b> di laptop, tanpa server dan tanpa internet, dan membaca format yang "
        "sudah dipakai tim tambang: string Surpac, DXF dan block model .mdl. Ini aplikasi kelima di keluarga GC-Ex yang saya "
        "kembangkan; posisinya alat kerja harian yang ringan untuk geolog dan mine planner, bukan pengganti paket perencanaan "
        "tambang yang besar.”", "pitch"), Spacer(1, 6),
      kartu([("VERSI", f"{VER} · 28 Nov 2026"), ("PLATFORM", "Windows 64-bit"), ("INSTALLER", "±152 MB, tanpa hak admin"),
             ("JARINGAN", "100% offline"), ("KODE SUMBER", "89 modul · ±1,6 MB"), ("BAHASA", "ID · EN · ES · SU"),
             ("FORMAT MASUK", ".str · .dxf · .mdl"), ("FORMAT KELUAR", ".str · .dxf · .csv · .png"), ("LISENSI", "per komputer, Ed25519")]),
      Spacer(1, 8)]
E += fig("s_pit3d.jpg", w=W * 0.74, cap="Desain pit final hasil Rancang Otomatis di atas topografi latihan (data fiktif). Kiri: Project Tree; kanan: halaman Properti.")

# ---------------- 2. Apa itu
E += [PageBreak(), P("1 · Apa itu Pit Studio for Desktop?", "h1"),
      P("<b>Jawaban singkat:</b> aplikasi perencanaan tambang terbuka yang mencakup desain pit, jalan, staging, penjadwalan "
        "gali dan laporan grade × tonnage — dalam satu installer yang berjalan sepenuhnya di komputer pengguna."),
      P("Masalah yang dipecahkan", "h2"),
      *L(["Mendesain pit dan menghitung ulang cadangannya biasanya berpindah-pindah antara beberapa perangkat lunak dan "
          "spreadsheet; setiap perubahan desain berarti ekspor–impor–hitung ulang.",
          "Paket perencanaan tambang komersial lengkap, tetapi berat dan memerlukan pelatihan khusus. Untuk pekerjaan harian "
          "(cek staging, perdalam bench, jadwal mingguan) tim sering butuh alat yang lebih ringan.",
          "Banyak lokasi tambang bekerja dengan jaringan terbatas; data desain dan block model termasuk data rahasia perusahaan "
          "yang tidak boleh keluar dari laptop."]),
      P("Untuk siapa", "h2"),
      *L(["<b>Mine planner / engineer perencanaan</b> — desain pit final & staging, jalan, jadwal per fleet.",
          "<b>Geolog grade control</b> — melihat dampak desain terhadap ore, kadar dan SR; sayatan dengan block model.",
          "<b>Pengawas / manajemen tambang</b> — laporan grade × tonnage per periode dan per fleet, layout peta siap cetak."]),
      P("Posisi dalam keluarga GC-Ex", "h2"),
      P("Pit Studio adalah aplikasi kelima keluarga GC-Ex. Kelimanya dipasang terpisah, masing-masing punya versi sendiri, "
        "tetapi berbagi backend lokal dan satu file lisensi per komputer."), *fig("d1_keluarga.png", cap="Gambar 1 — Keluarga GC-Ex dan komponen bersama.")]

# ---------------- 3. Cara kerja
E += [PageBreak(), P("2 · Bagaimana cara kerjanya?", "h1"),
      P("<b>Jawaban singkat untuk orang IT:</b> “Ini aplikasi Electron. Antarmuka dan seluruh mesin geometri berjalan sebagai "
        "satu halaman HTML/JavaScript dengan three.js untuk 3D. Untuk block model yang besar, ada backend Python (FastAPI) yang "
        "dijalankan aplikasi sendiri dan hanya mendengar di 127.0.0.1 pada port acak. Tidak ada server luar, tidak ada "
        "akun, tidak ada pembaruan otomatis.”"),
      *fig("d2_arsitektur.png", cap="Gambar 2 — Arsitektur Pit Studio for Desktop. Semua komponen berada di komputer pengguna."),
      P("Komponen utama", "h2"),
      tbl([["Komponen", "Teknologi", "Tugas"],
           ["Kerangka aplikasi", "Electron (Chromium + Node.js), installer NSIS", "Jendela, menu, dialog file, lisensi; memuat halaman aplikasi dari arsip ASAR"],
           ["Halaman aplikasi", "JavaScript (89 modul) digabung menjadi satu app-ps/index.html", "Seluruh desain, edit, jadwal, laporan, sayatan, ukur, terjemahan"],
           ["Grafik 3D", "three.js (MIT)", "Tampilan topografi, pit, jalan, blok, jejak jadwal"],
           ["Geometri poligon", "Clipper (Boost 1.0)", "Offset dan operasi boolean bench / crest / toe / batas"],
           ["Permukaan presisi", "Delaunator (ISC) + TIN GC-Ex", "Triangulasi topografi & desain; blok dihitung di dalam segitiga (cara DTM Surpac)"],
           ["Backend lokal", "Python, FastAPI, Uvicorn, NumPy (dibundel PyInstaller)", "Membaca block model Surpac .mdl besar secara bertahap; hanya 127.0.0.1"]],
          [32 * mm, 55 * mm, W - 87 * mm]),
      CondPageBreak(75 * mm), P("Alur kerja pengguna", "h2"), *fig("d3_alur.png", cap="Gambar 3 — Alur kerja dari data sampai keluaran.")]
E += [P("Yang terjadi di balik layar saat desain diubah", "h2"),
      *L(["Setiap perubahan desain menghasilkan permukaan baru. Pit Studio membuat <b>TIN</b> (jaring segitiga) dari string "
          "topografi dan desain: string dirapatkan 2 m, dibuat triangulasi Delaunay, lalu tinggi permukaan di setiap titik "
          "diinterpolasi linear di dalam segitiganya.",
          "Blok model dihitung masuk bila titik pusatnya berada di antara topografi dan permukaan desain — sama dengan resep "
          "GC-Ex Block Model dan cara kerja DTM di Surpac.",
          "Sekitar satu detik setelah perubahan terakhir, hitungan diulang otomatis; hasil dan <b>selisihnya</b> (ore, kadar, "
          "waste, SR) muncul di pojok 3D.",
          "Pit Schedule memecah area ke blok tambang bench × strip × blok, lalu menggali per fleet sesuai kapasitas alat dan "
          "periode (shift / hari / minggu / bulan); laporan grade × tonnage dihitung per periode dan per fleet."])]

# ---------------- 4. Fitur
E += [PageBreak(), P("3 · Apa yang ditawarkan?", "h1"),
      P("<b>Jawaban singkat:</b> “Satu alur lengkap: data → pit final → jalan → staging & edit → grade × tonnage → jadwal → "
        "laporan dan peta. Semua hasil bisa diekspor kembali ke Surpac atau AutoCAD.”"),
      tbl([["Kelompok", "Yang bisa dilakukan"],
           ["Data", "Impor topografi & string (.str / .dxf), trim topografi, block model Surpac .mdl (Version 4.0) termasuk model besar lewat backend"],
           ["Desain pit final", "Rancang Otomatis (atas → bawah), Desain Terpandu, Edit Manual; domain geoteknik per zona (tinggi bench, sudut, berm); lantai bertingkat; <b>sayat horizontal di RL</b> saat mendigit dasar pit — block model terlihat sebagai irisan di elevasi dasar*"],
           ["Jalan tambang", "Spiral & switchback, jalan luar (hauling road) dengan potong / timbun dan titik belok, jalan penghubung dua lantai, sampai tiga jalan per area*; kemiringan & lebar terjaga"],
           ["Staging & edit", "Fase / front galian bulanan dibatasi pit final; pindah titik, Play-Doh (kuas sapuan), trim, overcut, perdalam pit & sump; riwayat dan simpan otomatis"],
           ["Grade × Tonnage", "Dihitung otomatis setiap desain berubah, dengan pemberitahuan selisih ore / kadar / waste / SR; kelas kadar & tujuan (ROM, stockpile, waste); preset GC-Ex; multi-unsur. <b>Laporan dibatasi poligon</b> seperti constraint Surpac — didigit, dipilih dari string di 3D, atau blok mining dari .str; di dalam / di luar*. <b>Kategori ore</b> (mis. Oxide / Sulfide) dari atribut block model apa pun*. Tabel laporan: tiap kelas ore, <b>Total ore</b> (ton @ kadar), waste dalam BCM, SR*"],
           ["Pit Schedule", "4 langkah: data & area → blok tambang (bench × strip × blok) → alat & cara gali (turun per bench, klik blok, jalur gali) → laporan per periode & per fleet; hauling; fase"],
           ["Blok tambang", "Cadangan per blok; simpan / impor blok (.str) agar prospek yang sama memakai blok yang sama di proyek atau laptop lain; poligon batas dari Surpac"],
           ["Keluaran", "Sayatan (penampang) dengan block model dan posisinya di 3D — semua desain termasuk pit final impor ikut tersayat*, alat Ukur jarak-sudut-arah (3D & 2D), Layout peta, ekspor .str / .dxf / .csv / .png, file proyek"],
           ["Kualitas desain", "Tolok ukur kerapian string otomatis: menggantung, silang, tidak dipatuhi, bergelombang — target 0 / 0 / 0 / 0"],
           ["Antarmuka", "Kerangka seperti aplikasi desktop (menu & bilah alat cascade, Project Tree, Properti, panel lepas-tempel), 10 palet warna, ukuran tulisan, isian adaptif per mode, <b>menu klik kanan</b> di 3D, sayatan 2D dan Lapisan*, daftar pintasan di menu Bantuan*, layar penuh, 4 bahasa, tombol Demo yang memutar tutorial (bab A–P)"]],
          [32 * mm, W - 32 * mm]),
      P("* Baru di versi 0.1.8 (pembaruan 26–27 November 2026): diuji otomatis pada data latihan fiktif; uji pada data kerja masih berjalan.", "s")]
E += [Spacer(1, 6)] + fig("s_edit_gt.jpg", cap="Edit pit (perdalam / sump). Pojok kiri atas: Grade × Tonnage tiap desain dihitung otomatis; baris ↳ menunjukkan selisih terhadap hitungan sebelumnya.")
E += [CondPageBreak(110 * mm)] + fig("s_sayatan.jpg", cap="Sayatan A–B dengan block model per kelas kadar; garis bidik membaca RL, tebal galian dan kadar blok; tombol Ukur di pojok kanan atas.")
E += fig("s_laporan.jpg", cap="Pit Schedule: laporan Grade × Tonnage per periode & per fleet (grafik ton dan kadar ore, tabel kumulatif).")
E += [CondPageBreak(110 * mm)] + fig("s_batas.jpg", cap="Baru di 0.1.8 — laporan block model dibatasi blok mining dari berkas .str: blok 2 dan 3 dipilih dengan klik di 3D (data fiktif).")
E += [CondPageBreak(110 * mm)] + fig("s_kategori.jpg", cap="Baru di 0.1.8 — kategori ore (Oxide / Sulfide) dari atribut block model; laporan dan CSV dipecah per kategori.")
E += [CondPageBreak(110 * mm)] + fig("s_klikkanan.jpg", w=W * 0.8, cap="Baru di 0.1.8 — menu klik kanan di atas string: jadikan batas laporan, salin info, ekspor string, sayatan lewat titik, ukur.")
E += [CondPageBreak(110 * mm)] + fig("s_sayatrl.jpg", cap="Baru di 0.1.8 — sayat horizontal di RL saat mendigit dasar pit: block model tampil sebagai irisan di elevasi dasar.")

# ---------------- 5. Kelebihan
E += [PageBreak(), P("4 · Apa kelebihannya?", "h1"),
      P("<b>Jawaban singkat:</b> “Ringan, offline, langsung bicara dalam format Surpac, dan setiap perubahan desain langsung "
        "terlihat dampaknya pada ton, kadar dan SR. Hitungannya sudah dicocokkan dengan perhitungan independen.”"),
      tbl([["Kelebihan", "Bukti yang bisa ditunjukkan"],
           ["<b>Offline penuh, data tetap di laptop</b>", "Tidak ada alamat internet di kode Pit Studio; backend hanya 127.0.0.1; tidak ada pembaruan otomatis (publish: null)"],
           ["<b>Umpan balik instan</b>", "Grade × Tonnage dihitung ulang otomatis tiap desain berubah, lengkap dengan selisihnya — tanpa ekspor-impor"],
           ["<b>Hitungan presisi & terverifikasi</b>", "Resep TIN sama dengan GC-Ex Block Model; hasil uji sama persis dengan hitungan Python terpisah (Gambar 5)"],
           ["<b>Cocok dengan alat yang sudah ada</b>", "Membaca dan menulis string Surpac (.str), DXF, block model .mdl; blok tambang disimpan sebagai .str yang juga terbuka di Surpac"],
           ["<b>Satu alur desain → jadwal</b>", "Desain, jadwal per fleet dan laporan ada di satu aplikasi; jadwal bisa memakai desain acuan yang diimpor"],
           ["<b>Kerapian desain diukur</b>", "Empat indikator kerapian string dihitung otomatis; uji regresi demo menargetkan 0 / 0 / 0 / 0"],
           ["<b>Mudah dipasang</b>", "Satu installer ±152 MB per aplikasi, per pengguna (tanpa hak administrator), Windows 64-bit"],
           ["<b>Bahasa lokal</b>", "Antarmuka asli Bahasa Indonesia; terjemahan English, Español, Basa Sunda"],
           ["<b>Cepat berkembang</b>", "Sembilan versi desktop (0.1.0 → 0.1.8) terbit 22–28 November 2026; tiap push dibangun ulang otomatis oleh CI"]],
          [52 * mm, W - 52 * mm]),
      Spacer(1, 6), *fig("c2_presisi.png", w=W * 0.92, cap="Gambar 5 — Verifikasi hitungan bijih pada desain uji (data fiktif). Cara raster lama kurang ±30 %; TIN presisi sama persis dengan acuan Python."),
      *fig("c1_kode.png", w=W * 0.92, cap="Gambar 6 — Komposisi kode sumber Pit Studio per kelompok fungsi (total ±1,6 MB di 89 modul, termasuk pembaruan 26–27 November).")]

# ---------------- 6. Keamanan
E += [PageBreak(), P("5 · Keamanan, data dan cara distribusi", "h1"),
      P("<b>Jawaban singkat:</b> “Data tidak pernah meninggalkan laptop. Aplikasi tidak memanggil internet, backend hanya "
        "mendengar di localhost, dan lisensinya diverifikasi secara kriptografis di komputer itu sendiri.”"),
      tbl([["Aspek", "Penerapan", "Cara memeriksa"],
           ["Jaringan", "Tidak ada URL internet di kode Pit Studio; link luar dibuka di browser, bukan di aplikasi", "Cari 'http' di web-src-ps; uji dengan jaringan dimatikan"],
           ["Backend", "Hanya 127.0.0.1, port acak tiap kali dijalankan", "electron/main.js (freePort, 127.0.0.1)"],
           ["Isolasi halaman", "contextIsolation, sandbox, nodeIntegration = false pada semua jendela", "webPreferences di electron/main.js"],
           ["Integritas paket", "Electron fuses: runAsNode mati, NODE_OPTIONS mati, ASAR integrity, hanya muat dari ASAR", "builder-ps.json → electronFuses"],
           ["Pembaruan", "Tanpa auto-update; versi baru dibagikan admin dari GitHub Release", "builder-ps.json → publish: null"],
           ["Lisensi", "Kunci = data JSON + tanda tangan Ed25519; terikat ID komputer (hash MachineGuid); aplikasi hanya memegang kunci publik", "electron/license.js"],
           ["Kunci privat", "Disimpan pemilik; tidak pernah masuk repositori atau Release", "Aturan repo (CLAUDE.md); alat admin terpisah"],
           ["Data contoh", "Data latihan & demo fiktif (bukit sintetis, koordinat rekaan)", "docs/tutorial-ps/data, a24_data.js"]],
          [26 * mm, 80 * mm, W - 106 * mm]),
      P("Proses rilis", "h2"),
      *L(["Setiap push ke cabang utama dibangun ulang oleh GitHub Actions menjadi installer Windows dan diterbitkan sebagai "
          "GitHub Release beserta SHA256SUMS dan catatan rilis.",
          "Sebelum push, skrip memeriksa bahwa halaman aplikasi sama persis dengan sumbernya dan bahwa hanya aplikasi yang "
          "berkasnya berubah yang naik versi.",
          "Belum ada: penandatanganan kode (code signing) Windows — Windows SmartScreen dapat menampilkan peringatan saat "
          "installer pertama kali dijalankan."])]

# ---------------- 7. Legal
E += [PageBreak(), P("6 · Status legal", "h1"),
      P("<b>Jawaban singkat:</b> “Hak cipta programnya milik saya pribadi dan dilindungi otomatis oleh UU Hak Cipta. Komponen "
        "open source yang dipakai berlisensi permisif dan teks lisensinya ikut di installer. Merek ‘Pit Studio’ belum "
        "didaftarkan, dan pencatatan ciptaan di DJKI sedang/akan saya urus.”"),
      P("<i>Sesuaikan kalimat terakhir dengan langkah yang benar-benar sudah Anda ambil. Bagian ini adalah ringkasan fakta dari "
        "berkas repo dan undang-undang, bukan nasihat hukum; untuk pembicaraan investasi, mintalah konsultan kekayaan "
        "intelektual memeriksanya.</i>", "s"),
      *fig("d4_legal.png", cap="Gambar 7 — Matriks status legal Pit Studio pada tanggal dokumen ini."),
      P("Hak cipta", "h2"),
      *L(["UU No. 28 Tahun 2014 mendefinisikan hak cipta sebagai hak eksklusif yang timbul <b>otomatis</b> berdasarkan prinsip "
          "deklaratif setelah ciptaan diwujudkan dalam bentuk nyata (Pasal 1 angka 1). Program komputer termasuk ciptaan "
          "yang dilindungi.",
          "Perlindungan program komputer berlaku <b>50 tahun sejak pertama kali diumumkan</b> (Pasal 59).",
          "Pencatatan ciptaan di DJKI <b>tidak wajib</b>, tetapi menjadi bukti tertulis kepemilikan yang kuat bila terjadi "
          "sengketa — sangat dianjurkan sebelum bicara dengan investor.",
          "Pemegang hak tercatat di aplikasi dan installer: <b>Habil Abdillah</b> (perorangan). Tidak ada badan usaha "
          "yang disebut di berkas legal."]),
      P("Lisensi kepada pengguna", "h2"),
      *L(["Perangkat lunak <b>dilisensikan, bukan dijual</b>: izin non-eksklusif, tidak dapat dialihkan, dapat dicabut "
          "(legal/SYARAT_PENGGUNAAN.txt, tunduk pada hukum Republik Indonesia, disediakan ‘AS IS’).",
          "Dilarang tanpa izin tertulis: menjual / membagikan installer, reverse engineering, menghapus tanda hak cipta, "
          "memakai nama GC-Ex untuk produk lain.",
          "Teknis: kunci lisensi per komputer, bisa diberi tanggal kedaluwarsa — mendukung model langganan maupun lisensi abadi."]),
      P("Merek", "h2"),
      *L(["Indonesia menganut <b>first to file</b>: hak atas merek baru diperoleh setelah merek terdaftar (UU No. 20 Tahun "
          "2016, Pasal 3). Memakai nama ‘Pit Studio’ lebih dulu tidak memberi hak eksklusif.",
          "‘Pit Studio’ adalah gabungan kata umum; lakukan penelusuran di pangkalan data merek DJKI (PDKI) sebelum "
          "mendaftar, dan siapkan nama cadangan.",
          "Nama produk pihak lain (Surpac, GEOVIA, Minex, AutoCAD, dll.) disebut hanya untuk menjelaskan kecocokan format; "
          "ada penafian merek di legal/PENAFIAN_MEREK.txt."])]
E += [P("Komponen open source yang dikemas", "h2"),
      tbl([["Komponen", "Lisensi", "Kewajiban utama"],
           ["three.js (3D)", "MIT", "Sertakan teks lisensi — sudah (legal/LISENSI_THREEJS.txt)"],
           ["Clipper / js-clipper (poligon)", "Boost Software License 1.0", "Sertakan teks lisensi — sudah"],
           ["Delaunator (triangulasi)", "ISC", "Sertakan teks lisensi — sudah"],
           ["Electron / Chromium / Node.js", "MIT, BSD, dan lainnya", "Sertakan pemberitahuan — sudah (LISENSI_PIHAK_KETIGA)"],
           ["Python, FastAPI, Uvicorn, NumPy, Pydantic", "PSF, MIT, BSD", "Sertakan pemberitahuan — sudah"],
           ["PyInstaller (pembungkus backend)", "GPL-2.0 dengan pengecualian bootloader", "Pengecualian mengizinkan distribusi program tertutup"]],
          [55 * mm, 45 * mm, W - 100 * mm]),
      P("Semua lisensi di atas permisif terhadap distribusi tertutup (closed source) asalkan pemberitahuan hak ciptanya "
        "disertakan. Tidak ada komponen berlisensi copyleft kuat (GPL penuh / AGPL) di dalam aplikasi.", "s"),
      P("Yang perlu dibereskan (urut prioritas)", "h2"),
      tbl([["#", "Tindakan", "Alasan"],
           ["1", "Jadikan repositori GitHub <b>privat</b> (atau pisahkan kode Pit Studio ke repo privat)", "Saat ini repo publik: siapa pun bisa membaca dan menyalin kode sumber serta mengunduh kode dari tiap Release. Larangan di EULA tidak mencegah orang melihatnya."],
           ["2", "Periksa kontrak kerja / peraturan perusahaan tentang kekayaan intelektual", "Bila aplikasi dibuat dalam hubungan kerja, kepemilikan dapat ditentukan oleh perjanjian kerja (UU Hak Cipta mengatur ciptaan dalam hubungan kerja). Investor pasti menanyakannya."],
           ["3", "Catatkan ciptaan ‘Pit Studio’ (dan keluarga GC-Ex) di DJKI", "Bukti tertulis kepemilikan dan tanggal ciptaan."],
           ["4", "Telusuri & daftarkan merek di DJKI (kelas perangkat lunak)", "Hak merek hanya lahir dari pendaftaran."],
           ["5", "Tinjau syarat penggunaan & penafian merek khusus Pit Studio (ada sejak 0.1.8) bersama penasihat hukum", "Berkasnya sudah dibuat (legal/SYARAT_PENGGUNAAN.txt, PENAFIAN_MEREK.txt, LISENSI_PIHAK_KETIGA.txt versi Pit Studio) tetapi belum ditinjau ahli hukum."],
           ["6", "Pertimbangkan badan usaha (PT / CV) sebagai pemegang lisensi distribusi", "Memudahkan kontrak, faktur, dan masuknya investor."],
           ["7", "Code signing Windows", "Menghilangkan peringatan SmartScreen; kesan profesional di perusahaan klien."]],
          [8 * mm, 70 * mm, W - 78 * mm])]

# ---------------- 8. Batasan
E += [PageBreak(), P("7 · Batasan saat ini — katakan dengan jujur", "h1"),
      P("Penanya yang ahli akan menghargai Anda yang mengetahui batas produknya sendiri. Yang berikut benar pada versi "
        f"{VER}:"),
      tbl([["Batasan", "Cara menyampaikan"],
           ["Belum ada optimasi pit (Lerchs-Grossmann / pseudoflow) seperti Whittle", "“Pit Studio mendesain dan menjadwalkan; optimasi ekonomi pit masih dilakukan di perangkat lunak khusus. Itu kandidat pengembangan.”"],
           ["Penjadwalan berbasis aturan dan urutan pengguna, bukan optimasi matematis (LP/MIP)", "“Jadwalnya simulasi yang dapat diatur — cepat dan transparan — bukan penjadwal optimasi.”"],
           ["Satu pengguna per file; belum ada kerja bersama / server", "“Sengaja offline untuk keamanan data; kolaborasi lewat file proyek dan .str.”"],
           ["Block model yang diputar (rotasi) belum digambar miring di sayatan", "“Hitungan tonase sudah benar; tampilannya di penampang menyusul.”"],
           ["Baru diuji otomatis di lingkungan pengembangan; uji manual di banyak konfigurasi Windows masih terbatas", "“Kami butuh pilot di lokasi untuk mematangkan.”"],
           ["Satu pengembang (pemilik) dengan bantuan asisten AI", "Lihat bank pertanyaan: risiko ketergantungan orang & rencana mitigasi."],
           ["Belum ada code signing; installer ±152 MB per aplikasi", "“Standar aplikasi Electron + Python; code signing ada di rencana.”"],
           ["Tutorial PDF masih memakai tampilan 0.1.2", "Video demo lengkap (24 Nov) tersedia; tombol Demo di aplikasi sudah sampai bab P (pembaruan 26 Nov)."],
           ["Fitur baru 0.1.8 baru diuji otomatis pada data latihan fiktif", "“Hitungannya sudah dicocokkan pada data latihan; uji pada data kerja sedang berjalan.”"]],
          [68 * mm, W - 68 * mm])]

# ---------------- 9. Bank pertanyaan
E += [PageBreak(), P("8 · Bank pertanyaan — ahli IT / programmer", "h1"),
      QA("“Dibangun dengan apa? Kenapa Electron, bukan aplikasi native?”",
         "“Electron dengan halaman JavaScript dan three.js untuk 3D, plus backend Python untuk membaca block model besar. "
         "Alasannya: satu basis kode bisa diuji di browser dan dikemas sebagai desktop, grafik 3D lewat WebGL sudah matang, "
         "dan backend Python berbagi pembaca .mdl dengan aplikasi GC-Ex lainnya. Konsekuensinya ukuran installer ±152 MB.”"),
      QA("“Bagaimana block model yang sangat besar ditangani?”",
         "“Backend Python membaca file .mdl dan hanya mengirim subset blok di area kerja (dan di bawah topografi) ke tampilan. "
         "Untuk desain, laporan dihitung dari subset itu dengan TIN presisi.”"),
      QA("“Seberapa akurat hitungan tonasenya? Sudah divalidasi?”",
         "“Metodenya sama dengan GC-Ex Block Model: TIN dari string topografi dan desain, aturan titik pusat blok. Pada desain "
         "uji, jumlah blok dan tonase bijih sama persis dengan hitungan Python yang ditulis terpisah — 21.740 blok, "
         "6.548.307 t. Cara raster lama kurang sekitar 30 % dan sudah diganti.”",
         "tunjukkan Gambar 5. Bila ditanya perbandingan dengan Surpac, katakan metode sama (DTM + pusat blok), tetapi uji "
         "silang langsung dengan Surpac pada data nyata belum didokumentasikan — tawarkan melakukannya."),
      QA("“Apakah ada data yang dikirim ke internet? Telemetri?”",
         "“Tidak ada. Kode Pit Studio tidak memuat alamat internet, backend hanya mendengar di localhost, dan tidak ada "
         "pembaruan otomatis. Silakan uji dengan kabel jaringan dicabut atau dengan pemantau lalu lintas.”"),
      QA("“Bagaimana sistem lisensinya? Bisa dibobol?”",
         "“Kunci lisensi berisi data pemegang, aplikasi, ID komputer dan tanggal kedaluwarsa, ditandatangani Ed25519. "
         "Aplikasi hanya memegang kunci publik, jadi kunci palsu tidak bisa dibuat tanpa kunci privat. Seperti semua "
         "aplikasi desktop, pemeriksaan di sisi klien pada akhirnya bisa dimodifikasi oleh orang yang sangat niat — "
         "perlindungan utamanya tetap lisensi hukum dan hubungan dengan klien.”"),
      QA("“Siapa yang menulis kodenya? Bagaimana kualitasnya dijaga?”",
         "“Saya merancang alur, aturan teknis tambang dan memeriksa hasilnya; penulisan kode dibantu asisten AI. Kualitas "
         "dijaga dengan tolok ukur kerapian desain otomatis, uji regresi lewat demo otomatis yang menjalankan seluruh "
         "bab tutorial, verifikasi angka terhadap hitungan independen, dan build otomatis di setiap perubahan.”",
         "jawab jujur. Status hak cipta karya yang dibuat dengan bantuan AI masih berkembang di banyak negara; sebut ini ke "
         "konsultan HKI Anda."),
      QA("“Bagaimana kalau perlu integrasi dengan sistem kami?”",
         "“Pertukaran data lewat format terbuka: .str, .dxf, .csv, .png dan file proyek .json. Karena ada backend HTTP lokal, "
         "integrasi lebih dalam (mis. membaca basis data internal) secara teknis mungkin, tetapi belum ada API publik.”"),
      QA("“Bagaimana proses rilis dan pembaruannya?”",
         "“Setiap perubahan dibangun ulang oleh CI menjadi installer dan diterbitkan sebagai Release dengan checksum SHA-256. "
         "Pembaruan dibagikan admin, bukan otomatis, supaya lokasi tanpa internet tetap aman dan versi terkendali.”"),
      QA("“Apa yang terjadi kalau Anda tidak lagi memelihara aplikasi ini?”",
         "“Aplikasi tetap berjalan offline tanpa server, dan data tersimpan dalam format standar industri, jadi pengguna tidak "
         "terkunci. Untuk keberlanjutan, kode sumber dan proses build terdokumentasi dan otomatis.”"),
      PageBreak(), P("9 · Bank pertanyaan — investor teknologi", "h1"),
      QA("“Masalah apa yang Anda selesaikan, dan untuk siapa?”",
         "“Perencana tambang dan geolog grade control butuh melihat dampak setiap perubahan desain pada tonase, kadar dan "
         "SR — cepat, di laptop, tanpa internet, dan tetap memakai format Surpac. Pit Studio menyatukan desain, jadwal dan "
         "laporan itu.”"),
      QA("“Siapa pesaingnya, dan apa bedanya?”",
         "“Paket perencanaan tambang komersial (seperti Surpac, Minex, Deswik, Whittle) jauh lebih lengkap, dan kami tidak "
         "bersaing langsung di sana. Pit Studio adalah alat kerja harian yang ringan, offline, berbahasa Indonesia, dan "
         "cocok dengan file dari perangkat lunak tersebut.”",
         "jangan merendahkan pesaing dan jangan mengklaim ‘lebih baik dari Surpac’. Siapkan perbandingan harga lisensi dari "
         "sumber resmi bila investor menanyakan."),
      QA("“Siapa pemilik IP-nya?”",
         "“Hak cipta atas nama saya pribadi, dilindungi otomatis menurut UU No. 28/2014. Langkah berikutnya: pencatatan di "
         "DJKI, pendaftaran merek, dan — bila investasi berjalan — pengalihan ke badan usaha.”",
         "jawab ini hanya setelah Anda memeriksa kontrak kerja (tindakan #2 di Bagian 6). Bila aplikasi dibuat dengan "
         "fasilitas, waktu kerja, atau data perusahaan tempat Anda bekerja, bicarakan dengan konsultan sebelum bertemu investor."),
      QA("“Model bisnisnya?”",
         "“Lisensi per komputer — teknisnya sudah mendukung lisensi abadi maupun berjangka (langganan). Saluran awal: "
         "lisensi ke tim tambang dan kontraktor, ditambah jasa pelatihan dan kustomisasi.”",
         "isi dengan harga dan rencana Anda sendiri. Dokumen ini sengaja tidak memuat angka pasar atau harga karena belum ada "
         "datanya."),
      QA("“Sudah ada pengguna atau pendapatan?”",
         "“[Isi dengan fakta: jumlah pengguna uji / pilot, umpan balik, pendapatan bila ada.]”",
         "jangan melebih-lebihkan. ‘Belum ada pendapatan, sedang mencari pilot’ adalah jawaban yang dapat diterima pada tahap awal."),
      QA("“Kenapa Anda yang tepat membangun ini?”",
         "“Saya geolog yang bekerja langsung dengan data bor, block model dan Surpac. Aturan teknis di aplikasi — geoteknik, "
         "jalan, kelas kadar, cara kerja blok tambang — berasal dari praktik lapangan, bukan dari asumsi programmer.”"),
      QA("“Apa risiko terbesarnya?”",
         "“Tiga: (1) ketergantungan pada satu pengembang, (2) status IP yang perlu dirapikan (pencatatan, merek, kerahasiaan "
         "repo), (3) pasar perangkat lunak tambang yang konservatif. Mitigasinya: dokumentasi dan build otomatis, langkah "
         "legal di Bagian 6, dan pilot di lokasi untuk membangun referensi.”"),
      QA("“Dana akan dipakai untuk apa?”",
         "“[Isi: misalnya code signing & legal, uji lapangan, pengembang kedua, optimasi pit, dukungan pelanggan.]”"),
      QA("“Apa peta jalannya?”",
         "“Yang sudah dekat: tutorial baru, uji di Windows lapangan, code signing. Kandidat berikutnya: optimasi pit "
         "ekonomi, penjadwalan berbasis optimasi, block model terotasi di sayatan, integrasi lebih erat dengan aplikasi GC-Ex lain.”",
         "sebut sebagai kandidat, bukan janji tanggal.")]

# ---------------- 10. Do & don't + lampiran
E += [PageBreak(), P("10 · Saat presentasi: lakukan dan hindari", "h1"),
      tbl([["Lakukan", "Hindari"],
           ["Demo dengan <b>data latihan fiktif</b> bawaan installer, atau tombol Demo", "Menampilkan topografi, pit, block model atau koordinat milik perusahaan tempat Anda bekerja"],
           ["Tunjukkan Gambar 5 (verifikasi) dan uji ‘cabut kabel jaringan’", "Mengklaim ‘setara Surpac’ atau ‘menggantikan Whittle / Minex’"],
           ["Sebut batasan (Bagian 7) sebelum ditanya", "Menjanjikan fitur dengan tanggal pasti"],
           ["Bawa dokumen ini, video demo, dan berkas legal/ dari Release", "Mengirim installer atau kode sumber sebelum ada perjanjian kerahasiaan (NDA)"],
           ["Minta NDA sebelum diskusi teknis mendalam", "Membagikan kunci privat lisensi atau alat pembuat lisensi"]],
          [W / 2, W / 2]),
      P("Lampiran A — Riwayat versi desktop", "h2"),
      tbl([["Versi", "Tanggal", "Isi utama"],
           ["0.1.0", "22 Nov 2026", "Installer desktop pertama; backend GC-Ex untuk block model besar"],
           ["0.1.1", "22 Nov 2026", "Turun per elevasi (G × T × SR tiap penurunan), jendela laporan & grafik"],
           ["0.1.2", "22 Nov 2026", "Blok tambang bench × strip × blok; kotak hitung otomatis"],
           ["0.1.3", "22 Nov 2026", "Kerangka seperti Ore Works, Pit Schedule 4 langkah, hitungan presisi GC-Ex, simpan / impor blok"],
           ["0.1.4", "22 Nov 2026", "Grade × Tonnage otomatis + pemberitahuan, sayatan dengan block model, tombol Ukur, terjemahan"],
           ["0.1.5", "22 Nov 2026", "Perbaikan kecil tombol Demo"],
           ["0.1.6", "24 Nov 2026", "Antarmuka cascade & Properti gaya Ore Works, palet, lapisan jadwal, jadwal otomatis, posisi sayatan di 3D; tanpa garis aksen"],
           ["0.1.7", "25 Nov 2026", "Grade × Tonnage multi-unsur (unsur lain dipilih pengguna)"],
           ["0.1.8", "28 Nov 2026", "Batas laporan block model (poligon / string 3D / blok mining, dalam / luar), kategori ore, kolom laporan baru (Total ore, waste BCM), sayat di RL, menu klik kanan, sayatan 2D sinkron dengan pit final impor, Bantuan → Pintasan, hauling road v3, tiga jalan per area, filter per unsur, berkas legal Pit Studio, demo bab P"]],
          [20 * mm, 26 * mm, W - 46 * mm]),
      P("Prototipe HTML Pit Studio dikembangkan sejak setidaknya pertengahan November 2026 sebelum dikemas sebagai desktop.", "s"),
      P("Lampiran B — Istilah", "h2"),
      tbl([["Istilah", "Arti singkat"],
           ["Pit final / staging", "Batas akhir galian / tahapan galian menuju pit final"],
           ["Crest / toe / berm", "Puncak lereng / kaki lereng / teras datar di antara bench"],
           ["Block model (.mdl)", "Model 3D kotak-kotak berisi kadar dan berat jenis, format Surpac"],
           ["Grade × Tonnage (G × T)", "Tonase dan kadar bijih per kelas di dalam desain atau periode"],
           ["SR (stripping ratio)", "Ton waste dibagi ton bijih"],
           ["TIN / DTM", "Permukaan dari jaring segitiga; cara Surpac menghitung volume"],
           ["Bench × strip × blok", "Pembagian area tambang untuk penjadwalan (seperti di Minex)"],
           ["Electron / backend", "Kerangka aplikasi desktop berbasis web / program Python pendukung di komputer yang sama"],
           ["Ed25519", "Algoritma tanda tangan digital untuk memverifikasi kunci lisensi"],
           ["DJKI", "Direktorat Jenderal Kekayaan Intelektual — pencatatan ciptaan & pendaftaran merek"]],
          [42 * mm, W - 42 * mm]),
      Spacer(1, 8),
      P("Dasar hukum yang dirujuk: UU No. 28 Tahun 2014 tentang Hak Cipta (Pasal 1 angka 1; Pasal 59); UU No. 20 Tahun 2016 "
        "tentang Merek dan Indikasi Geografis (Pasal 3). Berkas repo: legal/SYARAT_PENGGUNAAN.txt, legal/PENAFIAN_MEREK.txt, "
        "legal/LISENSI_PIHAK_KETIGA.txt, legal-ps/, electron/license.js, electron/main.js, builder-ps.json.", "s")]

doc.build(E)
print("PDF:", OUT)
