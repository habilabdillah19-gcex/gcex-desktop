# GC-Ex Desktop (Grade Control Excellence)

Satu repositori, tiga aplikasi Windows 64-bit dengan backend Python yang sama:

| Aplikasi | Halaman | Sumber | Installer |
|---|---|---|---|
| GC-Ex Block Model | `app/index.html` | `web-src/` (`python build.py`) | `GC-Ex-Setup-<versi>.exe` |
| GC-Ex Drillhole | `app-dh/index.html` | `web-src-dh/` (`python build_dh.py`) | `GC-Ex-Drillhole-Setup-<versi>.exe` |
| Core-Ex | `app-core/index.html` | langsung `app-core/index.html` (satu file, tanpa build) | `Core-Ex-Setup-<versi>.exe` |

Ketiga aplikasi bisa dipasang berdampingan; masing-masing punya penyimpanan sendiri
(`%APPDATA%\\GC-Ex`, `%APPDATA%\\GC-Ex Drillhole`, `%APPDATA%\\Core-Ex`).

**Core-Ex** (Core Excellence; dahulu GC-Ex Core Interpretation) — interpretasi foto core box 100% offline: folder foto (ribuan foto, bersubfolder)
dibaca backend, Hole / Box / kedalaman dari nama file, deskripsi oleh model vision lokal di **Ollama**
(`core_dh.py`: import Collar/Survey/Assay/Geologi CSV/Excel dengan header dinamis, cari cepat, overlay assay di foto)
(`127.0.0.1:11434`, mis. `qwen3-vl:8b`), verifikasi geologist, export Excel. Hasil disimpan di
`<folder foto>/_GCEx_Core/gcex_core.db` (SQLite) supaya rekan bisa melanjutkan. Panduan: `docs/PANDUAN_CORE.md`.
Pengembangan: `npm run start:core` (Windows) atau `GCEX_APP=core npx electron .`.

Aplikasi desktop Windows 64-bit untuk GC-Ex Block Model: dig block per flitch, layout PDF,
as-mined & register poligon, rekonsiliasi dengan Surpac, serta koneksi ke MS Access dan Excel.

## Susunan

```
gcex-desktop/
├─ app/index.html          Tampilan GC-Ex Block Model (sama dengan versi HTML offline)
├─ app-dh/index.html       Tampilan GC-Ex Drillhole Ultimate + modul desktop
├─ app-core/index.html     Tampilan Core-Ex (offline penuh: tanpa CDN, ikon & font lokal)
├─ builder-core.json       Konfigurasi installer Core-Ex
├─ web-src-dh/             Sumber Drillhole: gcex_dh_base.html + mdlbig_dh.js + deskflush_dh.js + build_dh.py
├─ builder-dh.json         Konfigurasi installer GC-Ex Drillhole
├─ electron/main.js        Jendela aplikasi, menu, log, menjalankan & menghentikan backend
├─ electron/preload.js     Jembatan aman halaman <-> aplikasi (window.gcexDesktop)
├─ backend/                Backend Python (FastAPI), hanya di 127.0.0.1
│  ├─ gcex_backend/excel_io.py   Buat register .xlsx baru, baca sheet
│  ├─ gcex_backend/xlsx_patch.py Tulis register ke workbook yang SUDAH ADA tanpa menyimpan ulang workbook
│  │                             (hanya kolom input; rumus, link, grafik, makro tetap utuh; cadangan dulu)
│  ├─ gcex_backend/access_io.py  Baca tabel / tambah baris ke database MS Access (.accdb/.mdb)
│  ├─ gcex_backend/mdl_io.py     Block model .mdl besar: cache kolom di disk, potongan RL/XY, ringkasan per RL
│  ├─ gcex_backend/core_io.py    Core-Ex: proyek foto (SQLite), thumbnail, antrean AI Ollama, Excel
│  ├─ gcex_backend/server.py     API: /health /info /excel/* (termasuk /excel/register-write) /mdl/* /access/*
│  ├─ run_backend.py             Titik masuk (dipakai Electron & PyInstaller)
│  └─ tests/                     Uji otomatis
├─ web-src/               Sumber tampilan GC-Ex (modul + build.py -> app/index.html)
├─ build/icon.ico          Ikon aplikasi
└─ .github/workflows/build-windows.yml   "Pabrik" .exe otomatis di server Windows GitHub
```

Cara kerja: saat GC-Ex dibuka, Electron menyalakan `gcex-backend.exe` di port acak di komputer
itu sendiri (tidak terbuka ke jaringan), menunggu sampai siap, lalu halaman GC-Ex memakainya lewat
`window.gcexDesktop.backend()`. Saat GC-Ex ditutup, backend ikut dimatikan.

## Membuat installer (.exe)

Otomatis: setiap perubahan yang diunggah ke cabang `main` memicu GitHub Actions
(tab **Actions** di GitHub) untuk menguji backend, membangun `gcex-backend.exe`, mengecek
backend benar-benar menyala, lalu membuat installer `GC-Ex-Setup-<versi>.exe`.
Unduh dari halaman run tersebut, bagian **Artifacts**.

## Peta jalan

| Tahap | Isi | Status |
|---|---|---|
| 1 | Electron + GC-Ex + backend dasar (Excel, Access), installer otomatis | dikerjakan |
| 2 | Tombol di GC-Ex: register as-mined langsung ke Excel (selesai) / Access (menunggu contoh database), buka/simpan proyek tanpa dialog izin | dikerjakan |
| 3 | Pembaca block model .mdl besar di Python (cache disk, potongan RL/area, ringkasan seluruh model per RL) | dikerjakan |
| 3b | File jumbo: topografi / desain pit .str, .dxf, .csv ±500-700 MB dibaca per potongan (hasil identik), assay 200.000 baris, orthofoto 1 GB | selesai (0.4.0) |
| 3c | Project Tree (pohon proyek urut alur kerja + Properti) di kedua aplikasi; bilah Sayatan mengambang di Drillhole | selesai (0.5.0) |
| 3d | Orthofoto latar lepas elevasi; UI Block Model 10 langkah dengan status; as-mined lantai pick-up tidak rata | selesai (0.6.0) |
| 3e | Core-Ex: foto core box + AI vision lokal (Ollama), verifikasi, Excel | selesai (0.15.0) |
| 3f | Core-Ex: data bor header dinamis, cari cepat, filter kadar, overlay assay di foto | selesai (0.16.0) |
| 3g | GC-Ex Core Interpretation berganti nama menjadi **Core-Ex** (Core Excellence), tetap keluarga GC-Ex & lisensi bersama | selesai (0.18.0) |
| 3h | Core-Ex menjalankan Ollama otomatis bila belum aktif + tombol **Jalankan Ollama** di dialog AI | selesai (0.18.1) |
| 3i | Data besar: block model .mdl > 6 GB lancar di RAM 8 GB / VRAM 4 GB (indeks RL di luar RAM, batas blok per pemuatan, penampang 2D tanpa jeda); tanpa pembaruan online | selesai (0.18.2) |
| 3j | Grade shell 3D (Ore Geometry) dengan **Surface-Following**: hanya sel di sekitar batas cut-off yang dihitung penuh (hasil sama, 1,3–5 × lebih cepat) | selesai (0.18.3) |
| 3k | Setiap pembaruan terbit di **GitHub Release** v<versi>: 3 installer terpisah + dokumen & tutorial + data latihan + lisensi & tentang + catatan rilis (commit) + SHA-256 + kode sumber | selesai (0.18.4) |
| 3l | Catatan rilis: huruf non-ASCII (—, é) tidak rusak, jam commit ditulis dalam WIB | selesai (0.18.5) |
| 3m | Identitas visual baru (selaras Core-Ex): halaman muka penuh, tema earthy kedua aplikasi, logo GC-Ex / BLOCK MODEL · DRILL HOLE ULTIMATE, nama project site per proyek; Sayatan 2D, garis sayatan di 3D tampak atas, rekap & edit string, legenda string ringkas, Geological Modelling per domain aktif | selesai (0.19.0) |
| 3n | GC-Ex Drill Hole Ultimate: **domain aktif** dipakai bersama Geological Modelling, Geostatistik (komposit hanya dari domain aktif) dan Model Estimation (Jalankan domain aktif / semua domain); domain bisa diaktifkan dari node Geostatistik & Model Estimation di Project Tree | selesai (Drillhole 0.20.0) |
| 3o | GC-Ex Block Model: **Additional flagging** (flag seluruh poligon dig block bila komposit unsur > COG, garis ganda; menggantikan material SxS) dan **review per flitch** di Project Tree (Dig Block, Laporan, As-Mined rencana vs aktual), legenda string ringkas | selesai (Block Model 0.20.1) |
| 3p | Tutorial PDF: GC-Ex Drill Hole Ultimate diperbarui ke antarmuka 0.20 (gambar diambil ulang); **tutorial baru GC-Ex Block Model** (flitch, dig block, additional flagging, review per flitch, as-mined); data latihan BM + kolom S_PCT / ZN_PPM / CU_PPM; As-Mined per flitch: rencana & aktual sebagai subnode | selesai (Block Model 0.20.2) |
| 3q | **Database proyek SQLite** (`gcex_proyek.db` di folder proyek): Block Model = dig block & as-mined per flitch (+ view rekap_flitch); Drill Hole Ultimate = collar, survey, assay, geologi, domain, flag, run estimasi (+ view assay_domain); tabel `riwayat` mencatat setiap perubahan | selesai (Block Model & Drillhole 0.20.3) |
| 3r | GC-Ex Drill Hole Ultimate: **Sesar 3D** (bidang sesar dari jejak Peta / koordinat + dip / dip direction, vektor gerak trend / plunge, offset, pre / syn / post mineralisasi, urutan umur & relasi memotong; post + offset dipulihkan sebelum pemodelan & estimasi, batas keras, syn = kontrol orientasi vein) dan menu baru **Geomodeller Stratified-Laterite Deposit** (laterit Ni / bauksit / sedex: lapisan dari log geologi, permukaan atap / isopach, estimasi unfold per lapisan OK / IDW / akumulasi 2D, laporan WMT / DMT & rasio); menu Geological Modelling menjadi **Geomodeller Vein System Deposit**; tutorial + data latihan laterit | selesai (Drill Hole Ultimate 0.21.0) |
| 3s | Core-Ex: folder foto besar (uji 4.501 foto / 45 GB nominal: scan 0,4 s, buka ulang 0,2 s, UI tetap lancar); thumbnail JPEG 2× lebih cepat & memori backend 470 → 100 MB (decode skala kecil); foto panorama > 178 MP tidak lagi ditolak | selesai (Core-Ex 0.21.1) |
| 3t | Core-Ex: **tanda interval di foto** — half core (wajib nomor sampel, saran dari assay), core loss (Core Recovery dihitung otomatis), jenis lain; kolom Loss/Half di tabel, cari cepat, sheet Excel *Interval*, CSV, riwayat | selesai (Core-Ex 0.22.0) |
| 3u | Core-Ex: **overlay berlapis** (assay, logging, interpretasi per baris, kartu foto; preset, warna & kelas per lapisan disimpan di proyek) dan **interpretasi AI per baris core** mengikuti batas geologi, bisa diedit di foto (nilai, geser batas, belah, gabung, tambah, hapus), tidak ditimpa AI; sheet Excel *Segmen* | selesai (Core-Ex 0.23.0) |
| 3v | Core-Ex: identitas visual baru — palet editorial (kertas #F2F2F0, navy #232F45, biru baja #4A7499, judul #1F4E8C), font Inter + JetBrains Mono (OFL, dibundel); rencana pindah ke PySide6 (Core-Ex 1.0.0) | selesai (Core-Ex 0.23.2) |
| 3w | Core-Ex Qt (PySide6) tahap 1: kerangka native di `app_core_qt/` — lisensi Ed25519 (kunci & file lisensi sama), syarat penggunaan, tabel virtual bisa diedit, pratinjau zoom/geser/putar, kartu, AI lokal + Ollama otomatis, Data bor, cari Ctrl+K, Excel/JSON; uji pytest-qt | sumber (Core-Ex 0.23.3; installer masih Electron) |
| 3x | Core-Ex Qt tahap 2–3: overlay berlapis, tanda half core / core loss, editor segmen (geser batas, belah, gabung), kalibrasi area core, Data lab di kartu; build PyInstaller + installer NSIS (copot versi Electron otomatis), uji mandiri exe di CI; lisensi Qt/PySide6 (LGPL-3.0) | sumber + artefak CI (Core-Ex 0.23.4; installer rilis masih Electron) |
| 3y | Core-Ex Qt: perbaikan tata letak panel (form tanda/segmen muat di panel sempit), cek Ollama tidak tertukar; CI menampilkan ringkasan galat uji Qt & kemas rilis sebagai anotasi | sumber (Core-Ex 0.23.5; installer rilis masih Electron) |
| 3z | Core-Ex Qt: sisa fitur versi Electron/HTML dipindahkan — **satu jendela** (membuka Core-Ex lagi menampilkan jendela yang sudah terbuka, folder diteruskan), jendela dibuka penuh, menu **Tampilan › Ukuran tampilan** 80–150% (Ctrl+= / Ctrl+- / Ctrl+0) & **Layar penuh** (F11), daftar pilihan Pelapukan / Oksidasi di sel tabel, Bantuan › Panduan AI lokal; pintasan Ctrl+O yang bentrok diperbaiki | sumber (Core-Ex 0.23.6; installer rilis masih Electron) |
| 4a | **CI: Release bisa terbit lagi** — kegagalan uji Core-Ex Qt tidak lagi membatalkan job (penyebab Release 0.23.4 & 0.23.5 tidak terbit), unggah Release dicoba sampai 3× + dilengkapi `gh release upload --clobber` dan kelengkapan file diperiksa (penyebab Release 0.23.3 gagal tanpa pesan); Core-Ex Qt: timer awal milik jendela & status AI dijaga agar tidak menyentuh widget yang sudah dihapus | sumber (Core-Ex 0.23.7; installer rilis masih Electron) |
| 4b | Core-Ex Qt: uji Windows stabil lagi — tata letak panel, cek Ollama & fokus isian yang tertunda tidak lagi menyentuh jendela yang sudah ditutup (sisa penyebab galat uji Windows: relayout panel, hasil cek Ollama, fokus form), uji satu jendela memakai thread pengirim | sumber (Core-Ex 0.23.8; installer rilis masih Electron) |
| 4c | CI: pesan jelas bila `GITHUB_TOKEN` tidak boleh membuat Release (HTTP 403 — sebab sebenarnya Release 0.23.3–0.23.7 tidak terbit; perlu Settings › Actions › General › Workflow permissions = *Read and write*), tidak dicoba ulang sia-sia; Core-Ex Qt: perbaikan balapan **satu jendela** (pesan folder bisa terlewat bila data & pemutusan soket tiba bersamaan) | sumber (Core-Ex 0.23.9; installer rilis masih Electron) |
| 4d | CI: langkah uji Core-Ex Qt bisa dijalankan lagi — tanda kutip di pola ringkasan galat (0.23.8) membuat skrip PowerShell gagal dibaca sehingga langkah itu selalu gagal sebelum pytest berjalan | sumber (Core-Ex 0.23.10; installer rilis masih Electron) |
| 4e | Uji Core-Ex Qt satu jendela mengirim dari proses terpisah (seperti Core-Ex kedua sungguhan); di Windows thread pengirim dalam proses yang sama tidak andal | sumber (Core-Ex 0.23.11; installer rilis masih Electron) |
| 4f | Installer uji **Core-Ex Qt** diterbitkan ke pre-release privat `core-ex-qt-uji` (selalu versi terbaru), tidak lagi hanya artifact Actions yang tertolak bila kuota penyimpanan penuh | sumber (Core-Ex 0.24.3; installer rilis masih Electron) |
| 3s | GC-Ex Drill Hole Ultimate: **Geostatistik per lapisan** di ruang unfold (sumber *Lapisan* di panel Geostatistik: statistik, variogram, anisotropi, model, KNA; akumulasi 2D = tebal × kadar), **Simpan ke lapisan** (model variogram, pass, diskretisasi, top-cut; range vertikal dari variogram downhole) dan **validasi lapisan** (swath Easting / Northing / Z unfold, grade-tonase DMT) | selesai (Drill Hole Ultimate 0.23.1) |
| 3t | GC-Ex Drill Hole Ultimate: **klasifikasi keyakinan sumber daya** di Reporting BM — kelas Measured / Indicated / Inferred diusulkan dari hasil estimasi (pass pencarian, jumlah komposit, slope of regression atau kriging efficiency; ambang bisa diubah), menjadi atribut kategori `klasifikasi` (grup laporan, pewarnaan 3D, export CSV) + **kurva grade × tonase bertumpuk per kelas**. Penetapan kelas tetap wewenang Competent Person | selesai (Drill Hole Ultimate 0.24.0) |
| 3u | **Kedua aplikasi**: topografi & orthofoto resolusi sangat tinggi tanpa korban performa — piramida LOD ortho (warna rata-rata area, anti-alias), resolusi **dan** luas mesh mengikuti luas tampilan (zoom 10 m: 0,1 m/titik, 13.700 titik, 3 ms — sebelumnya 1 m/titik, 160.000 titik, 592 ms), gambar ortho Peta 2D dipotong sesuai tampilan pada resolusi asli (220 x 220 px / 6 ms / 9 KB, sebelumnya 2.666 x 2.666 px / 255 ms / 3,1 MB), desimasi topografi per sel di dalam tampilan (11x lebih banyak titik pada anggaran sama), grid elevasi tampilan (200.000 pembacaan: 14 ms vs 512 ms). Perhitungan reporting tetap memakai topoZ asli | selesai (Block Model & Drill Hole Ultimate 0.24.1) |
| 3v | **Data latihan simulasi baru** (jauh lebih besar & taat kaidah geologi): endapan epitermal low-sulphidation terkontrol zona geser — array **4 lensa en-echelon** + splay, **ore shoot ber-pitch 55°** yang mengontrol tebal *dan* kadar sekaligus, zonasi vertikal terhadap paleo-muka air tanah (Ag/Au naik ke atas, Pb–Zn ke bawah, tekstur colloform di zona didih), profil pelapukan + selimut supergen, sesar pasca-mineralisasi terbatas, efek nugget Au. 610 bor resource + 459 bor grade control, ±98.000 baris assay 12 atribut, QAQC, 2 versi topografi, data rusak, kunci jawaban. Plus **Tutorial Tambahan 0.24** (PDF, gambar dihitung dari model & data — bukan tangkapan layar) | selesai (Block Model & Drill Hole Ultimate 0.24.2) |
| 3w | Drill Hole Ultimate: Model Estimation merekam **kerapatan bor per blok** — `est_nhole` (jumlah lubang bor berbeda), `est_dmin` (jarak ke komposit terdekat), `est_spasi` (perkiraan spasi bor setempat); ketiganya ikut ke block model & export `.mdl`. **Klasifikasi keyakinan kini memakai spasi bor dan jumlah bor**, bukan hanya jumlah komposit — blok dengan 20 komposit dari 1 lubang bor tidak lagi bisa menjadi Measured. CI: tutorial PDF dibangun otomatis di runner Windows tiap rilis | selesai (Block Model & Drill Hole Ultimate 0.24.4) |
| 3x | CI: pembuatan tutorial bergambar di runner Windows dipaksa UTF-8 dan pencatatan angka hasil tidak lagi menggagalkan seluruh tahap bila konsol tidak dapat mencetaknya (konsol Windows bawaannya cp1252, teks panel GC-Ex memuat karakter di luar itu) | selesai (Block Model & Drill Hole Ultimate 0.24.5) |
| 3y | Tutorial bergambar disesuaikan dengan data latihan baru: wireframe contoh `QV_Lensa2_Leapfrog.obj` (dulu `QV_Utama_Leapfrog.obj`), domain yang ditelusuri `QV_Lensa2` + `QV_Splay_HW` (vein utama & splay hangingwall-nya), dan penjelasan geometri diperbarui (array 4 lensa, pitch ore shoot 55°, paleo-muka air tanah RL 250 m) | selesai (Block Model & Drill Hole Ultimate 0.24.6) |
| 3z | CI: **kegagalan Core-Ex Qt tidak lagi menahan Release GC-Ex** (installer Qt masih tahap percobaan), dan pengambilan teks lisensi GNU dari gnu.org dicoba 3× lalu jatuh ke salinan dari rilis sebelumnya — satu gangguan jaringan dulu menggagalkan seluruh rilis | selesai (Block Model & Drill Hole Ultimate 0.24.7) |
| 4a | Skrip tangkapan layar tutorial tidak lagi mematok jumlah bor (`collars.length===37`) yang berasal dari data latihan lama — penantian upsert kini relatif (menunggu jumlah bor bertambah), dan keterangan berkas di narasi memakai hitungan data yang berlaku | selesai (Block Model & Drill Hole Ultimate 0.24.8) |
| 4g | **Core-Ex Qt: ruang kerja Singkapan** — foto singkapan / trenching (disalin ke proyek), deskripsi AI lokal (ISRM, JSON), digitasi garis / poligon / label dengan snap, belah & gabung, kadar manual, garis skala, pustaka jenis fitur & nomor string Surpac, infografis 3 template (trenching dengan kadar, mapping dinding, overlay) ekspor PNG / PDF | sumber + installer uji (Core-Ex 0.25.0; installer rilis masih Electron) |
| 4h | **Core-Ex Qt: Singkapan tahap B** — georeferensi foto dari titik survey Pylox / pita (klik di foto + E, N, RL, tempel dari Excel): 2 titik similaritas, 3 titik bidang + affine, ≥4 titik bidang terbaik + koreksi perspektif, galat per titik & RMS, orientasi bidang; ukuran 3D per fitur (panjang, apparent dip, luas); bar skala dari georef; ekspor STR Surpac & DXF R12 (E, N, RL) per foto atau semua foto | sumber + installer uji (Core-Ex 0.26.0; installer rilis masih Electron) |
| 4 | Proyek dapat dipindahkan antar laptop (folder proyek), pembaruan otomatis, code signing | rencana |

## Kebutuhan di laptop pengguna

- Windows 10/11 64-bit.
- Untuk fitur MS Access: driver Access 64-bit (MS Office 64-bit, atau
  *Microsoft Access Database Engine 2016 Redistributable* x64). Menu **Bantuan → Tentang GC-Ex**
  dan endpoint `/info` menunjukkan apakah driver terdeteksi.
- Untuk Core-Ex: Ollama (dipasang terpisah) + satu model vision; lihat `docs/PANDUAN_CORE.md`
  untuk pemasangan tanpa internet. Tanpa Ollama, log tetap bisa diisi & diverifikasi manual.
- Log ada di `%APPDATA%\GC-Ex\logs` (menu **Bantuan → Buka folder log**).
