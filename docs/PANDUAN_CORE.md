# Panduan DB-Ex

**DB-Ex** (Database Excellence) adalah aplikasi keluarga GC-Ex untuk foto core box; dahulu bernama *Core-Ex* (sampai 0.30.0) dan *GC-Ex Core Interpretation*. Nama **DB-Ex** = *Database Excellence*: ke depan aplikasi ini juga akan membaca formulir lapangan tulisan tangan dengan AI vision menjadi Excel / SQL / CSV.

Repositori dokumentasi core box: foto, interpretasi AI lokal, data lab (Collar, Survey, Assay, Geologi) dan pencarian cepat dalam satu aplikasi. Semua berjalan **di komputer sendiri**; tidak butuh internet, tidak ada foto atau data yang dikirim ke luar.

Pembaruan terakhir: 30 Oktober 2026 (versi 0.23.0: overlay berlapis & interpretasi AI per baris yang bisa diedit di foto; 0.22.0: tanda half core / core loss di foto, Core Recovery otomatis; 0.18.1: DB-Ex menjalankan Ollama otomatis / tombol Jalankan Ollama; 0.18.0: nama baru DB-Ex; 0.16.0: data bor dengan header dinamis, cari cepat, filter kadar, overlay assay di foto).

## 1. Cara kerja singkat

| Bagian | Fungsi | Berjalan di |
|---|---|---|
| Jendela DB-Ex | Tabel log, pratinjau foto, kartu interpretasi, verifikasi, export Excel | komputer ini |
| Backend DB-Ex (FastAPI) | Membaca ribuan foto dari folder, membuat thumbnail, menyimpan hasil di database, mengantre AI, membuat Excel | komputer ini, hanya `127.0.0.1` |
| Ollama + model vision | "Melihat" foto lalu menulis deskripsi (litologi, warna, pelapukan, oksidasi, alterasi, RQD, GSI, RMR, catatan) | komputer ini, `127.0.0.1:11434` |

Backend dan Ollama hanya mendengar di `127.0.0.1`, jadi tidak bisa diakses dari komputer lain di jaringan.

## 2. Memasang

### 2a. DB-Ex

1. Unduh `DB-Ex-Setup-<versi>.exe` dari GitHub (tab **Actions** → run terbaru → **Artifacts** → `DB-Ex-Setup-Windows`).
2. Jalankan installer. Tidak perlu hak admin. Shortcut **DB-Ex** muncul di desktop dan Start menu.
3. Aplikasi bisa dipasang berdampingan dengan GC-Ex Block Model dan GC-Ex Drillhole.

### 2b. Ollama (mesin AI lokal) — sekali per komputer

Di komputer yang **ada internet** (mis. laptop kantor saat di kota):

1. Unduh installer Windows Ollama dari situs resmi Ollama (`OllamaSetup.exe`). Pakai versi **0.12.7 atau lebih baru** (dibutuhkan model Qwen3-VL).
2. Pasang, lalu buka Command Prompt dan unduh model vision, mis.:
   ```
   ollama pull qwen3-vl:8b
   ```
3. Model tersimpan di folder `%USERPROFILE%\.ollama\models`.

Untuk komputer **tanpa internet** di site:

1. Salin `OllamaSetup.exe` dan seluruh folder `%USERPROFILE%\.ollama\models` dari komputer di atas ke flashdisk / hard disk.
2. Di komputer site: pasang `OllamaSetup.exe`, lalu tempel folder `models` ke `%USERPROFILE%\.ollama\models` (buat foldernya bila belum ada).
3. Ollama tidak perlu dibuka manual: saat DB-Ex dibuka dan Ollama belum aktif, DB-Ex menjalankannya otomatis (bisa dimatikan di dialog **Jalankan AI** → *Jalankan Ollama otomatis…*). Bila masih mati, klik tombol **Jalankan Ollama** di dialog AI, atau buka Ollama dari Start menu (ikon llama di system tray). Titik di kanan atas berubah biru: **AI lokal: qwen3-vl:8b**.

Bila folder model ingin disimpan di drive lain (mis. `D:\OllamaModels`), atur variabel lingkungan `OLLAMA_MODELS` ke folder itu lalu jalankan ulang Ollama.

### 2c. Memilih model

| Model | Ukuran unduhan | Cocok untuk |
|---|---|---|
| `qwen3-vl:8b` (disarankan) | ±6,1 GB | PC / laptop dengan kartu grafis NVIDIA ≥ 8 GB VRAM, atau RAM ≥ 16 GB |
| `qwen3-vl:4b` | ±3,3 GB | laptop biasa (RAM 8–16 GB); lebih cepat, sedikit kurang teliti |
| `qwen2.5vl:7b`, `gemma3:12b`, `llama3.2-vision:11b` | 6–8 GB | alternatif bila sudah terpasang |

Perkiraan waktu per foto: GPU 8 GB ±5–20 detik; hanya CPU ±1–3 menit. Antrean berjalan di latar belakang, jadi 500 foto bisa ditinggal semalam. Model yang tidak bisa melihat gambar (mis. `llama3.2:3b`) tampil abu-abu dan tidak bisa dipilih.

## 2d. Prinsip: AI untuk geoteknik, logging geologist untuk geologi

- **AI visual menilai parameter geoteknik**: core recovery, RQD, GSI, RMR, tingkat pelapukan, kondisi (WET / DRY) dan catatan struktur.
- **Isian geologi** (litologi, alterasi, oksidasi, warna) **diambil dari logging geologist** (Data bor › Geologi) bila ada di rentang From–To foto. Isian ini bertanda hitam **logging**, tidak bisa ditimpa AI, dan dipakai di tabel, filter, cari cepat dan Excel.
- AI hanya mengisi isian geologi bila logging untuk foto itu **tidak ada**. Bila ada, logging dikirim ke AI sebagai konteks (mis. QV / silisifikasi umumnya keras) dan AI diminta fokus pada geoteknik.
- Bila satu foto memotong beberapa interval logging, isian diringkas: kode dominan (≥ 80 % panjang), atau campuran mis. `QV (58%) / DAC (42%)`.
- Urutan prioritas: **logging geologist > editan manual di kartu > AI**. Kolom Mineralogy, Vein Type, Interpretasi Alterasi, dll. tampil lengkap di **Data lab** dan bisa ditampilkan sebagai pita di overlay.

## 3. Alur kerja

1. **Buka folder foto** → pilih folder berisi foto core box. Subfolder (mis. per lubang bor) ikut dibaca. Format: JPG, PNG, TIFF, BMP, WEBP.
2. Hole ID, nomor box dan kedalaman **dibaca dari nama file** bila polanya jelas (bila tidak, AI membaca papan label di foto, lihat bagian 3a), mis.:
   - `LTH-101_Box11_36.30-40.10.jpg` → LTH-101, box 11, 36,30–40,10 m
   - `DDH-07-15 BX4 10.2m-14.0m.jpg` → DDH-07-15, box 4, 10,2–14,0 m
   - `GCD0123 B05 12,5-15,0m.jpg` → GCD0123, box 5, 12,5–15,0 m

   Isian dari nama file diberi label berarsir **nama file** dan tidak ditimpa AI. Nama seperti `IMG_0001.jpg` dibiarkan kosong: AI mencoba membaca papan label di foto.
3. **Jalankan AI lokal** → pilih model → **Analisis foto yang belum**. Bilah kemajuan di bawah menunjukkan jumlah, sisa waktu, dan tombol **Hentikan**. Hasil tiap foto langsung tersimpan, jadi aplikasi boleh ditutup di tengah jalan; jalankan lagi untuk melanjutkan yang belum.
4. **Periksa & perbaiki.** Klik baris tabel (atau ↑ ↓) untuk melihat foto. Scroll = zoom, tarik = geser, klik ganda = pas layar, tombol ↗ = resolusi penuh untuk membaca label kecil. Ubah isian di kartu kiri atau langsung di tabel.
   - Sel **biru muda** (label biru **AI**) = isian AI yang belum dicek.
   - Label **diedit** (hijau) = sudah diubah geologist. Isian ini **tidak pernah ditimpa AI**, walau AI dijalankan ulang.
5. **Verifikasi**: tombol **Verifikasi & lanjut** atau **Ctrl+Enter** menandai foto sudah diperiksa lalu pindah ke foto berikutnya. Foto terverifikasi tidak disentuh AI lagi. Beberapa foto sekaligus: centang di kolom kiri tabel → **Verifikasi terpilih**.
6. **Export Excel**: semua foto atau hanya yang tampil sesuai filter. Sheet `Core Log` berisi semua kolom + status AI, keyakinan AI, siapa yang memverifikasi; nama file foto bisa diklik untuk membuka fotonya. Sel biru muda di Excel = isian AI yang belum diverifikasi; kolom **Sumber isian geologi** menulis asal tiap isian (logging / manual / AI).

### 3a. Papan label yang dibaca AI

AI diberi tahu tata letak foto core box proyek (contoh fiktif: `docs/referensi/contoh_corebox_fiktif_LTH-101_box11.jpg`):

| Tulisan di papan | Kolom di DB-Ex |
|---|---|
| HOLE ID: LTH-101 | Hole ID |
| START DRILL: 05-03-25 | Start Drill |
| BOX: 11 | Box No |
| DATE POTO: 12-03-25 | Tanggal Foto |
| DEPTH: 36.30 | From (m) |
| M:TO: 40.10 | To (m) |
| M:CONDT: WET | Kondisi Foto |

Kotak berisi 4 baris core (atas = dangkal, kiri → kanan); papan catur di bawah = skala 20 cm per kotak, dipakai AI untuk memperkirakan panjang potongan core (recovery, RQD). Bila format papan di proyek lain berbeda, tulis di **Instruksi tambahan**.

**Filter dua arah:** pilih Hole ID dan isi rentang kedalaman → tabel menyaring dan pratinjau langsung lompat ke foto pertama yang cocok. Klik judul kolom untuk mengurutkan; klik **No** untuk kembali ke urutan nama file.

**Riwayat:** di bawah kartu, **Riwayat perubahan & jawaban asli AI** menunjukkan setiap perubahan (nilai lama → baru, siapa, kapan, manual / AI) dan jawaban mentah AI.

**Instruksi tambahan** di dialog AI: tulis aturan proyek, mis. kode litologi `AND, DAC, QV, BX`, atau "tulis warna dalam bahasa Inggris saja".

## 4. Data bor: Collar, Survey, Assay, Geologi (header dinamis)

Tombol **Data bor** di bilah atas. Pilih tab tabel, lalu **Pilih file CSV / Excel…** (.csv, .txt, .tsv, .xlsx, .xlsm; .xls lama: simpan ulang sebagai .xlsx).

1. **Baris header** dan **sheet** dideteksi otomatis (baris judul laporan lab di atas header dilewati). Bisa diganti bila salah.
2. **Kolom utama**: pilih kolom file untuk tiap isian. Nama header bebas; DB-Ex menebak dari nama umum (Hole_ID / BHID / DHID, From / Depth_From, Easting / X, RL / Z, Dip / Inclination, Azimuth / Bearing, …).

   | Tabel | Wajib | Opsional |
   |---|---|---|
   | Collar | Hole ID, X, Y, Z | Total depth, dip & azimuth collar |
   | Survey | Hole ID, kedalaman, dip, azimuth | – |
   | Assay | Hole ID, From, To | kolom unsur apa pun |
   | Geologi | Hole ID, From, To | kolom apa pun (Lith, Alteration, Mineralogy, Vein, …) |

3. **Kolom lain yang ikut**: centang kolom yang dipakai, beri **nama di DB-Ex** (mis. `Au (ppm)` → `Au`, `Sample No` → `Sample`) dan pilih **angka / teks**. Kolom dengan nama sama di import berikutnya dianggap kolom yang sama.
4. Pratinjau di atas menandai kolom yang dipakai (biru = kolom utama, coret = tidak dipakai).
5. **Cara import**: *Tambah / perbarui per hole* (hole di file diganti seluruhnya, hole lain tetap; untuk data bor baru / sampel ulang) atau *Ganti semua*.
6. Ringkasan hasil: jumlah baris, baris yang dilewati beserta alasannya (Hole ID kosong, From ≥ To, …), nilai di bawah limit deteksi, interval tumpang tindih, hole yang tidak ada di Collar, dan jumlah hole yang cocok dengan foto.

**Logging → isian kartu foto** (tab Geologi): pilih kolom logging untuk Litologi, Alterasi, Oksidasi, Warna, Pelapukan. DB-Ex menebak dari nama kolom (Lith / Lithology / Litologi, Alteration / Alt_Int / Alterasi, Ox / Oxidation, Colour / Warna, Weathering); pilih "— tidak dari logging —" bila isian itu tetap dari AI / manual.

Pemetaan kolom **disimpan di proyek**: file berikutnya dengan susunan header yang sama langsung memakai pemetaan terakhir. Bila format Excel berubah, cukup pilih ulang kolomnya.

Aturan nilai: `<0.01` dibaca 0,005 (setengah limit deteksi); `>10` dibaca 10; `-`, kosong, `NA` = tidak ada nilai; koma desimal (`0,25`) dibaca. Hole ID dicocokkan tanpa membedakan huruf besar, spasi, `-` dan `_` (`LTH 101` = `LTH-101` = `lth101`).

**Yang didapat setelah import:**
- Kartu foto → **Data lab**: koordinat collar, koordinat X, Y, Z di From dan To foto (dihitung dari survey), tabel assay dan geologi di rentang foto. Kadar diberi warna kelas.
- Tabel → kolom **<unsur> rata2** (rata-rata tertimbang panjang di rentang foto) untuk unsur yang dipilih di filter **Kadar**.
- Excel → kolom `<unsur> rata-rata` dan `<unsur> maks` untuk semua unsur angka.

## 5. Cari cepat & filter

- **Cari cepat** (kotak di bilah atas, **Ctrl+K**) mencari di nama file, Hole ID, isian log, dan semua kolom teks data geologi / assay. Contoh: `LTH-101`, `pyrite`, `QV`, `silisifikasi`, nomor sampel `S0034`. Hasil menunjukkan interval dan foto core box-nya; ↑ ↓ lalu Enter (atau klik) untuk membuka foto.
- **Kueri kadar**: `Au>=1`, `Cu>0.3`, `Ag<5` → semua interval assay yang memenuhi, diurutkan dari nilai tertinggi, lengkap dengan fotonya. Overlay assay otomatis menyala saat membuka hasil assay.
- **Filter** (bilah kedua, menyaring tabel): Hole ID, rentang kedalaman (pratinjau lompat ke foto pertama yang cocok), status AI / verifikasi, **Kadar** (unsur, rata2 / maks, ≥ nilai — mis. tampilkan hanya box dengan Au maks ≥ 1 g/t), dan **Saring** teks.

## 6. Overlay hasil assay di foto core box

Tombol **lapisan** (ikon tumpukan) di pojok kanan atas pratinjau menyalakan overlay:
- **Pita assay** di atas tiap baris core, warna sesuai kelas kadar (biru muda → navy) dan nilai kadarnya. Garis tegak = batas interval sampel.
- **Pita geologi** di bawah tiap baris (mis. Lith: AND, DAC, QV).
- **Kedalaman** di awal dan akhir setiap baris.
- Strip pengaturan di bawah foto: pilih unsur, ubah **kelas** (mis. `0.1, 0.5, 1, 3`), tampilkan / sembunyikan nilai, pilih kolom geologi, dan legenda.

**Atur area core**: kotak biru menandai area baris core di foto (bawaan: cocok dengan foto standar proyek, papan label di atas, 4 baris). Tarik sudut untuk mengubah ukuran, tengah untuk menggeser, isi jumlah baris, lalu simpan untuk **foto ini**, **semua foto lubang ini**, atau **bawaan proyek**.

Cara posisi dihitung: interval box (From–To foto) dibagi rata ke jumlah baris; baris 1 = paling dangkal, kiri → kanan. Ini **perkiraan**: bila core hilang (recovery rendah) atau panjang tiap baris tidak sama, posisi pita bisa bergeser dari penanda kedalaman di core block. Pakai penanda di core block sebagai acuan akhir.

## 6a. Overlay berlapis & interpretasi per baris

**Lapisan overlay.** Panel Overlay berisi daftar lapisan; tiap lapisan menjadi satu pita tipis di setiap baris core, ditumpuk berurutan.

| Sumber | Isi | Penempatan |
|---|---|---|
| Assay | kolom unsur (Au, Ag, Cu, …) | per interval sampel |
| Logging | kolom apa pun dari data Geologi (Lith, Alterasi, Mineralogy, Vein, RQD / Weathering bila ada) | per interval logging |
| Interpretasi per baris | Litologi, Alterasi, Warna, Pelapukan, Oksidasi, RQD, Recovery, Rekahan/m, GSI, RMR, Catatan dari AI atau geologist | per segmen (batas geologi aktual) |
| Kartu foto | isian kartu (satu nilai per box) | sepanjang box |

- **+ Lapisan** menambah, **↑ ↓ ×** mengurutkan / menghapus, centang menyalakan / mematikan. **Preset**: *Assay + logging*, *Geologi: AI vs logging*, *Geoteknik* (RQD, Recovery, Rekahan/m, Pelapukan), *Kartu foto*.
- Warna: angka = kelas (RQD 25/50/75/90, Recovery 50/75/90/95, RMR 21/41/61/81, Rekahan/m terbalik); batas kelas bisa diketik. Pelapukan W1–W6, Oksidasi dan GSI = palet berurutan (segar → lapuk). Kode teks (Lith, Alterasi) = warna per kode, klik kotak warna di legenda untuk mengganti.
- Pita **putus-putus** = nilai AI yang belum diedit; garis penuh = logging / editan geologist.
- Susunan lapisan, kelas dan warna disimpan di proyek (`gcex_core.db`), jadi sama untuk semua rekan.

**Interpretasi per baris (AI).** Saat AI dijalankan, selain nilai per box, AI membagi tiap baris core menjadi segmen di setiap perubahan nyata litologi, warna, pelapukan, oksidasi, alterasi, vein atau zona rekahan, maksimal ±1 m per segmen, lalu menilai geologi dan geoteknik tiap segmen. Kedalaman segmen = From foto + posisi di box, jadi ikut benar bila From/To dikoreksi.

**Mengedit segmen di foto** (Overlay → **Edit segmen**):
- **Klik segmen** → formulir semua nilai (Litologi … RMR, Catatan) + From/To; **Simpan** (Enter).
- **Tarik garis batas kuning** untuk menggeser batas; segmen tetangga ikut sehingga tidak ada celah / tumpang tindih. Dibulatkan 0,05 m.
- **Tarik di area kosong** untuk segmen baru (manual); segmen lain yang tertimpa dipotong.
- **Belah di …** (di titik yang diklik), **Gabung dengan berikutnya**, **Hapus**. Esc = selesai.
- Kartu foto bagian *Interpretasi per baris* menampilkan tabel segmen; klik baris untuk mengedit.

Aturan: segmen yang diedit / ditambah geologist **tidak pernah ditimpa AI**; analisis ulang hanya mengganti segmen AI yang belum diedit dan memotongnya di sekitar segmen editan. Foto terverifikasi tidak disentuh. Setiap perubahan tercatat di riwayat. Excel mendapat sheet **Segmen**; cari cepat juga menelusuri isi segmen.

## 6b. Tanda interval: half core & core loss

Tombol **tanda** (ikon pita bergaris, di sebelah tombol overlay) membuka panel *Tanda interval*.

1. Pilih **Jenis**: *Half core*, *Core loss*, atau **+ Jenis lain…** (mis. *Rusak pengangkutan*, *Sampel geotek*).
2. Klik **Mulai menandai**, lalu **tarik di sepanjang baris core** dari awal sampai akhir interval. Tanda boleh menyambung ke baris berikutnya. Kedalaman From–To dihitung dari posisi di foto (interval box dibagi rata ke baris core, sama seperti overlay) dan dibulatkan 0,05 m; angka bisa diketik ulang.
3. Isi formulir lalu **Simpan** (Enter):
   - **Half core** wajib **No. sampel**. Bila data assay punya kolom *Sample* / *Sampel* / *Sample_No*, nomor sampel yang paling banyak beririsan terisi otomatis (pilihan lain ada di daftar).
   - **Catatan** bebas untuk semua jenis.
4. Klik tanda yang sudah ada (saat mode menandai) untuk mengedit; tombol **Edit** / **Hapus** juga ada di kartu foto bagian *Tanda interval*. **Esc** = berhenti menandai.

**Core Recovery otomatis.** Bila foto punya tanda, Core Recovery (%) = (interval foto − total core loss) / interval foto. Isian ini berlabel merah **tanda**, tidak ditimpa AI, dan dihitung ulang setiap tanda atau From/To foto berubah. Mengetik Recovery sendiri mengalahkan hitungan ini sampai tanda foto itu diubah lagi. Bagian core loss di luar rentang foto tidak dihitung.

**Hasil.** Tabel mendapat kolom *Loss m* dan *Half m*; cari cepat menemukan tanda (mis. `core loss`, `half core`, nomor sampel); Excel mendapat sheet **Interval** (Hole, From, To, Panjang, Jenis, No. sampel, Catatan, Foto, oleh, waktu) serta kolom *Core loss (m)*, *Half core (m)*, *Sampel half core*; tombol **CSV** di panel mengekspor semua tanda proyek. Setiap perubahan tercatat di riwayat foto.

Bila pita tanda tidak tepat di atas core, atur dulu **Atur area core** (bagian 6).

## 6b2. Infografis foto core box

**File › Ekspor infografis foto (PNG / PDF)** (Ctrl+E) di ruang kerja Core box menyimpan foto yang dipilih sebagai *plate* bergaya editorial: foto utuh (papan judul core box tetap terbaca) dengan overlay lapisan yang sedang aktif persis seperti di layar, pita atas berisi kicker (Foto core box · Box n) dan judul serif *Hole · dari – ke m*, pita bawah berisi caption logging (litologi, alterasi, pelapukan, recovery, RQD, catatan) dan kredit (nama folder proyek), serta legenda warna lapisan overlay. Di ruang kerja Singkapan perintah yang sama mengekspor infografis singkapan.

## 6c. Singkapan: foto mapping & trenching (DB-Ex versi Qt)

Ruang kerja **Singkapan** (tombol di bilah atas, di samping **Core box**) untuk foto singkapan, dinding / lantai pit dan trenching hasil mapping lapangan. Memakai folder proyek yang sama dengan Core box.

1. **+ Foto** — pilih foto satu atau beberapa. Foto **disalin** ke `_GCEx_Core/singkapan/foto` di folder proyek (foto asli tidak diubah), jadi rekan yang membuka folder yang sama melihat hasil yang sama.
2. **Deskripsi** — isi Judul, Lokasi, Tanggal, lalu **Deskripsikan dengan AI** (Ollama, model vision yang sama dengan Core box). AI mengisi jenis foto (wall / floor), litologi, alterasi, pelapukan ISRM W1–W6, oksidasi / gossan, vein, struktur, GSI, spasi kekar, pembagian zona dan catatan. Isian biru muda = isian AI yang belum dicek; isian yang Anda edit tidak ditimpa saat AI dijalankan ulang. Riwayat perubahan & jawaban asli AI ada di bawah tab.
3. **Digitasi (tab Fitur)** — pilih jenis di bilah atas (kontak litologi / alterasi, zona litologi / alterasi / oksida, sesar, kekar, vein, zona vein, breksi / diatrema, channel sampel, garis skala, label), klik **✎ Gambar**, klik titik demi titik di foto, klik ganda / Enter untuk selesai (Backspace = hapus titik terakhir, Esc = batal).
   - **Edit**: klik fitur, tarik kotak putih untuk menggeser titik, klik ganda di garis untuk menyisipkan titik, Delete untuk menghapus titik / fitur, **Belah di titik** dan **Gabung** untuk garis.
   - **Snap** (aktif bawaan) menempelkan titik ke titik / garis fitur lain, sehingga kontak antar-poligon tidak bercelah.
   - **Garis skala**: tarik di sepanjang benda yang panjangnya diketahui (pita ukur, tongkat) dan isi *Panjang m*. Skala ini dipakai bar skala infografis dan perkiraan spasi kekar oleh AI. Bila tidak ada garis skala, bar skala memakai skala dari georeferensi (langkah 5).
   - **✦ SAM (Segment Anything)** di bilah atas: pilih jenis zona (poligon), klik **✦ SAM**, lalu klik di dalam zona di foto — batas zona digambar otomatis mengikuti tepi batuan (pratinjau putus-putus). **Shift+klik** = titik "bukan zona" untuk memotong bagian yang ikut; **Tab** = ganti ukuran (kecil / sedang / besar — mis. pita gossan saja, zona alterasi di sekitarnya, atau seluruh dinding); **Backspace** = hapus titik terakhir; **Enter** = simpan sebagai fitur lalu lanjut ke zona berikutnya; **Esc** = selesai. Klik pertama di tiap foto butuh beberapa detik (SAM membaca foto sekali), klik berikutnya cepat. Model berjalan offline di komputer ini.
   - **Usulan otomatis** (kotak di atas daftar fitur) — biar komputer membuat draf lebih dulu, lalu Anda periksa:
     - *Zona warna (cepat, tanpa AI)*: foto dibagi menjadi beberapa zona menurut warna (atur *zona*: 2 = oksida vs segar, 3–4 bila ada beberapa zona). Zona merah / coklat / kuning diberi jenis *Zona oksida / gossan*, lainnya *Zona litologi*. Langit, vegetasi, orang dan bayangan bisa ikut menjadi zona: hapus saja.
     - *AI vision (Ollama)*: model vision mengusulkan kontak, sesar, kekar, vein dan zona beserta jenis & namanya (20–120 detik). Hasil bergantung model; model yang mendukung *grounding* (mis. keluarga Qwen-VL) paling baik. Catatan tambahan di panel AI ikut dikirim.
     - Usulan tampil **titik-titik** dan bertanda *◌ usulan* di daftar. Usulan **tidak ikut** legenda, ekspor PNG / PDF, maupun STR / DXF sampai diterima. Edit seperti fitur biasa (geser / sisip / hapus titik, ganti jenis & nama), lalu **✓ Terima usulan** atau **Simpan** (Simpan juga menerima). **Terima semua** / **Buang semua** untuk seluruh usulan di foto. Menjalankan ulang satu cara mengganti usulan lama dari cara itu saja.
   - **Sampel / kadar** (tabel di form fitur) — kadar diisi manual atau ditempel dari Excel:
     - **Garis channel / trenching** dibagi menjadi beberapa **interval**: tiap baris = *Sample ID, Dari m, Ke m* lalu kadar per unsur. Jarak *dari–ke* diukur dari **ujung kiri** garis (collar) ke kanan (EOH); garis yang digambar dari kanan ke kiri otomatis dibalik. **+ Interval** menambah baris yang melanjutkan *ke* terakhir dan menaikkan nomor sampel. Panjang garis diambil dari georef (3D) atau garis skala; tanpa keduanya garis dianggap sepanjang interval terjauh. Bila interval lebih panjang dari garis, muncul peringatan merah.
     - **Zona / poligon** dan garis tanpa interval memakai satu baris sampel tanpa dari–ke.
     - **Tempel dari Excel**: salin baris dengan kolom *Sample ID, Dari, Ke*, lalu kadar. Bila baris judul kolom ikut disalin (mis. `Au (ppm)`, `Ag_ppm`, `SxS %`), kolom dicocokkan menurut nama unsur; tanpa judul, urutannya mengikuti tabel.
     - Nilai di bawah batas deteksi ditulis `<0.01` (dihitung setengah batas deteksi di komposit); desimal boleh koma. Interval tidak boleh tumpang-tindih, Sample ID tidak boleh kembar.
   - *Teks lain* menambah baris bebas di kotak kadar fitur zona / satu sampel.
   - **Strike / dip terukur** (jenis titik): klik posisinya lalu isi mis. `N100/80` atau `100/80`. Digambar sebagai simbol T dengan panah dip dan teks N100/80; nilainya bisa diubah di form (Strike °, Dip °) dan ikut ekspor STR.
   - **Label zona (rentang)** (jenis garis): tarik dari batas kiri ke batas kanan zona (mis. di bawah garis trenching), lalu isi nama zona. Digambar sebagai kurung putih dengan garis penunjuk ke kotak putih; tarik kotaknya untuk memindahkan. Tidak ikut ekspor STR / DXF.
   - **Label kotak** (centang di bilah atas, aktif bawaan): label baru memakai kotak putih; bisa diubah per label di form (*Kotak putih*).
   - **Atur jenis fitur & nomor string…** — ubah nama, warna dan nomor string Surpac per jenis, atau tambah jenis sendiri (mis. dike). Satu nomor string untuk satu jenis.
4. **Infografis** — pilih template:
   - *Trenching / channel (dengan kadar)*: pita judul kuning, kotak kadar per fitur (tarik kotaknya untuk memindahkan), kotak komposit, legenda, bar skala.
   - *Mapping dinding (tanpa kadar)*: pita judul navy, legenda, bar skala, strip deskripsi ringkas (litologi, alterasi, pelapukan, vein, struktur, GSI).
   - *Overlay saja*: garis & poligon tanpa judul.

   **Kadar di template Trenching**:
   - garis berinterval mendapat tanda batas interval dan **satu kotak kadar per sampel** (Sample ID, dari–ke, unsur yang dicentang), ditempatkan di atas garis dengan dua ketinggian bergantian (sisi bawah dibiarkan untuk label zona); tarik kotaknya untuk memindahkan;
   - **Warnai interval menurut** satu unsur: segmen garis & bingkai kotak diberi warna kelas kadar, kelasnya masuk legenda;
   - **Komposit otomatis**: rata-rata tertimbang panjang per unsur untuk tiap garis berinterval, ditambahkan ke kotak komposit (teks bebas tetap bisa diisi);
   - **Atur unsur & kelas warna…**: daftar unsur (bawaan Au, Ag, Cu, Pb, Zn, As, S, SxS, C), satuan (ppm, ppb, %, g/t, oz/t), desimal, *Tampil* di kotak kadar, batas kelas (mis. `0.2; 0.5; 1`). Kadar semua unsur tetap tersimpan & ikut ekspor walau tidak ditampilkan;
   - **⇩ Tabel sampel (CSV)**: semua sampel di semua foto (Sample ID, dari, ke, panjang, koordinat E/N/RL awal & akhir bila foto digeoreferensi, kadar, baris KOMPOSIT per garis) untuk Excel / database assay.

   **Gaya** (tab Infografis): *Editorial dokumenter alam* (bawaan) — kicker kapital oker & judul serif di atas gradasi gelap, panel data gelap transparan dengan batang warna kelas kadar, garis penunjuk putih tipis bertitik di ujung fitur, *Caption* serif miring (kosong = ringkasan deskripsi untuk template dinding) dan *Kredit foto* di kaki (kosong = tanggal · lokasi); atau *Klasik* (pita judul kuning / navy, kotak kuning).

   **Kompas** (tab Infografis): *otomatis dari georef* — foto dinding menampilkan huruf arah kamera menghadap (mis. W) di atas mawar angin, foto lantai menampilkan panah utara yang diputar sesuai foto; tanpa georef pilih arah pandang manual (N, NE, … NW). Posisi kompas bisa dipilih; bila bertabrakan dengan legenda, kompas digeser ke sampingnya.

   **Ekspor PNG / PDF** memakai foto resolusi penuh (maks. 6000 px) dan sama persis dengan tampilan di layar.

5. **Georef (titik survey)** — sebelum memotret, beri tanda **Pylox / pita** di singkapan dan minta survey mengukurnya (total station / GNSS).
   - Tab **Georef** → **⊕ Titik di foto**, klik tiap tanda di foto (titik bernama G1, G2, …; tarik penanda untuk menggeser, Esc = selesai). Isi **E, N, RL** di tabel, atau salin dari Excel (kolom *Nama, E, N, RL* atau *E, N, RL*, judul kolom boleh ikut) lalu **Tempel dari Excel**: baris dicocokkan menurut nama; koordinat tanpa nama mengisi titik yang belum berkoordinat. Titik yang koordinatnya ditempel lebih dulu ditandai *klik di foto* dan terisi pada klik berikutnya.
   - **Bidang foto**: *otomatis* mengikuti jenis foto di Deskripsi (wall / floor), atau pilih *dinding* / *lantai*.
   - Jumlah titik menentukan cara hitung: **2 titik** = skala & arah saja (dinding dianggap tegak, lantai datar; hanya teliti bila foto tegak lurus bidang), **3 titik** = bidang boleh miring, tanpa koreksi perspektif, **≥4 titik** = bidang terbaik + **koreksi perspektif**. Dengan **5 titik atau lebih** galat tiap titik dan **RMS** dapat diperiksa — titik dengan galat besar biasanya salah klik atau salah ketik koordinat.
   - Hasil: metode, RMS (m), orientasi bidang (dip → arah dip), skala di tengah foto, dan peringatan (titik segaris, titik menyimpang dari bidang, jenis bidang tidak cocok).
   - **Ukuran 3D** tampil di form fitur (tab Fitur): panjang 3D dan *apparent dip* (ujung ke ujung) untuk garis, luas & keliling untuk poligon.
6. **Topografi / DTM as-built (opsional)** (tab Georef, bagian *Topografi*):
   - Koordinat yang benar tetap **georef**. Topografi survey biasanya diperbarui sekitar seminggu sekali, jadi foto bisa lebih baru dari DTM; menempel ke DTM hanya dilakukan bila dipilih saat ekspor.
   - **+ Impor DTM…**: pilih file Surpac **.dtm beserta .str pasangannya** (teks maupun biner, nama file jangan diubah), isi nama versi dan **tanggal survey**. Beberapa versi topografi bisa disimpan.
   - **Cek terhadap foto ini**: cakupan DTM di foto, **jarak titik survey (Pylox) ke DTM** (besar = topografi belum memuat galian terbaru), porsi titik fitur yang kena DTM, dan peringatan bila **tanggal foto lebih baru dari tanggal survey**.
   - **Tempel**: foto lantai diproyeksikan tegak lurus (vertikal) ke DTM; foto dinding sepanjang normal bidang georef (maks. 10 m). Garis dirapatkan ±0,5 m agar mengikuti bentuk permukaan.
   - **Depth Anything** (centang *Isi area di luar DTM…*): kedalaman relatif dari satu foto (AI lokal) diubah ke meter memakai titik yang kena DTM dan / atau titik georef (≥ 4 titik yang tidak sebidang), lalu dipakai untuk bagian foto di luar DTM. Hasil kalibrasi (RMS) ditampilkan; tanpa kalibrasi yang sah, bagian itu tetap di bidang georef.
7. **Ekspor digitasi 3D** (tab Georef) — **STR** Surpac atau **DXF** R12, untuk foto ini atau semua foto (foto yang belum digeoreferensi dilewati dan disebutkan).
   - STR: kolom Y = northing, X = easting, Z = RL; nomor string per jenis fitur (Atur jenis fitur & nomor string…); D1 jenis, D2 Sample ID (atau nama fitur), D3 judul foto, lalu dari–ke dan kadar (`Au=1.03`, `Ag=4`, …). Garis berinterval diekspor **satu segmen per interval sampel**. Poligon ditutup; label menjadi titik tunggal; garis skala tidak ikut.
   - DXF: satu layer per jenis fitur (warna mengikuti pustaka), 3D polyline, nama fitur sebagai TEXT.
   - Setiap ekspor (STR, DXF, tabel sampel, database channel) menanyakan **sumber koordinat**: **Georef — bidang foto (bawaan, disarankan)** atau *Tempel ke topografi* (pilih versi DTM, opsional Depth Anything). Pilihan bawaan selalu georef; Collar memuat kolom COORD_SRC.
   - **⇩ Database channel: Collar · Survey · Assay · Geologi (CSV)** — semua garis *Channel sampel* di semua foto yang sudah digeoreferensi direkap seperti data bor (4 file `<nama>_collar.csv`, `_survey.csv`, `_assay.csv`, `_geology.csv`):
     - satu garis channel = satu lubang; HOLE_ID = nama fitur (kosong → `<judul foto>_CH<n>`);
     - **Collar** = ujung kiri garis (E, N, RL dari georef), MAX_DEPTH = panjang garis 3D (atau *ke* terjauh bila lebih panjang), **DIP = 0** mutlak, AZIMUTH = arah garis dari kiri ke kanan; juga TYPE (CHANNEL), foto, tanggal, lokasi;
     - **Survey**: satu baris di kedalaman 0 dan satu baris di tiap titik belok garis bila azimuth berubah (dip tetap 0);
     - **Assay**: FROM, TO, SAMPLE_ID dan semua unsur (kolom `Au_ppm`, `SxS_pct`, …). Nilai di bawah batas deteksi dipilih saat ekspor: setengah DL, negatif DL, atau teks asli;
     - **Geologi**: garis dipotong oleh batas zona litologi / alterasi / oksida / vein / breksi dan ujung *Label zona*; tiap interval berisi nama zona yang dilewati (kolom LITHOLOGY, ALTERATION, OXIDATION, VEIN, BRECCIA, ZONE), STRUCTURE = sesar / kekar / vein / kontak yang memotong interval itu, WEATHERING dari deskripsi foto. Kolom yang tidak punya zona sama sekali diisi deskripsi foto (mis. litologi) untuk seluruh lubang.
   - Koordinat berada **di bidang foto**: tonjolan / cekungan singkapan tidak terukur, jadi hasilnya sebaik kerataan dinding dan sebaran titik kontrol.

Penting: deskripsi AI dan garis yang digambar di foto adalah alat bantu; kemiringan yang terlihat di satu dinding hanyalah *apparent dip*.

## 6d. Borang: borang lapangan tulisan tangan → Excel / CSV / SQLite / MS Access (DB-Ex versi Qt)

Tombol **Borang** di bilah atas (di samping *Core box* dan *Singkapan*) membuka ruang kerja borang untuk folder proyek yang sama. Foto / scan / PDF borang disalin ke `_GCEx_Core/borang/scan` di dalam folder proyek; data tersimpan di `_GCEx_Core/borang/borang.db`. Empat jenis borang:

- **Ore Spotter: Loading Pit → ROM / Stockpile** (borang loading / rehandling ore di front): header nama crew, lokasi (pit), excavator (EX-…), tanggal, shift I / II; baris: No, Start / Finish Loading, Pit, Elevation, kelas material (OX-LG, SF-LG, OX-HG, SF-HG, OX-SG, SF-SG, OX-MO, SF-MO — kelompok kolom tempat Truck & Tonnage ditulis), Truck, Tonnage, Tujuan Dumping.
- **Ore ke Stockpile / Crusher (Rehandling / Direct)** (borang spotter di ROM / crusher): header crew, lokasi, tanggal, shift; baris: No, Eq. No. Unit, Start / Finish Loading, Asal Material, Tujuan, Rehandling Tumpukan (sub-kolom yang dicentang), kelas material + ton (termasuk SCAT), Status Baru / Lama, Keterangan (Direct / Rehandling / OPP).
- **RC Drilling: Daily Drilling Report**: header Date, Shift, Drill rig, Driller, Client, DHP ID, jam **WH / DL / MNTC / BD / RAIN / STD**, HM engine (start, finish, running), bit / reamer, catatan, geologist approval. Satu borang berisi **dua tabel** — pilih di *Tabel:* di atas tabel data:
  - **Aktivitas** (drilling details): Mulai, Selesai, uraian, **Kategori** (diisi otomatis dari kata kunci, bisa dipilih dari daftar), kolom turunan Jam (durasi) dan Kelompok jam. Kelompok jam sesuai aturan site: **WH** = DRILLING, TRAVELING ANTAR TITIK BOR, PERSIAPAN, P2H, P5M; **DL** = ISTIRAHAT, STANDBY, WAIT BLASTING, TRAVELING KE LOKASI (dan LAIN-LAIN); **MNTC / BD / RAIN** = MAINTENANCE / BREAKDOWN / HUJAN; **STD** = STANDBY TIDAK ADA OPERATOR, STANDBY TIDAK ADA LOKASI. Kata kunci: *traveling* + *titik / lubang / hole / antar* → antar titik bor, *traveling* lainnya (ke ROM, pit, dll.) → ke lokasi; *blasting* → wait blasting; *standby / waiting* + *tidak ada operator* atau *tidak ada lokasi / titik* → STD, standby lain (mis. area longsor) → STANDBY (DL). Bila tebakan salah, ganti kategorinya — kelompok jam ikut berubah.
  - **Meterage / lubang**: From, To, Hole ID, Az, Dip (kolom turunan Meter).
  - Kotak ringkasan membandingkan jam di borang dengan jumlah durasi aktivitas per kelompok (merah bila selisih > 0,5 jam), total meter, jumlah lubang, meter per jam drilling dan HM running. Validasi: jam kosong / tidak valid, kegiatan tidak menyambung, di luar shift (lembur), To ≤ From, azimuth / dip di luar rentang.
- **RC Drill / Chiptray Log**: header Hole ID, tanggal pengeboran; baris Sample ID, From, To, Remark QAQC (STD / BLANK / DUP).

**Penulisan baku di seluruh Borang** (hasil AI, ketikan manual, tabel dan semua ekspor): **Hole ID memakai garis bawah**, huruf besar (Z2-265-S-05 → Z2_265_S_05, z4 270.56 → Z4_270_56); **Drill rig** dirapikan ke *Merek 00N* bila mereknya dikenal (Hanjin, Hanwa): tulisan tangan *hansin SDR-07* atau ketikan *Hanjin 7* → **Hanjin 007** — nilai ini yang masuk kolom **EqType** dashboard. Isian yang dirapikan dari hasil AI ditandai kuning.

Cara tulis cepat di lapangan dipahami program (sel yang diisi program ditandai **kuning** agar dicek):

- **Tanda ulang** (〃, ", =, ,, garis tegak / garis miring panjang) → nilai baris di atasnya; *〃 370* di Tujuan → *ROM 370*; Tujuan yang hanya angka → awalan baris atas (mis. *ROM*).
- **Jam menit saja**: *19.02* lalu *05* → 19:05; menit lebih kecil dari baris atas → jam berikutnya (*19.55* lalu *03* → 20:03).
- **Nomor truk singkat** (borang loading pit): *4026* lalu *26* → 4026; *4026* lalu *45* → 4045.
- Baris yang hanya mengganti Pit / Elevation tanpa truk tidak dijadikan baris; nilainya dibawa ke baris berikutnya. Sel Pit, Elevation, Tujuan, Asal, Status dan Keterangan yang kosong diisi dari baris atas.
- **Shift II melewati tengah malam**: kolom *Tanggal muat* = tanggal borang + 1 untuk jam sebelum 12:00. Validasi menandai jam di luar shift (shift I / DS 06:00–18:00, shift II / NS 18:00–06:00) dan jam yang mundur.

Langkah:

1. Pilih jenis borang di kiri, klik **+ Borang** lalu pilih foto / scan / PDF (PDF: satu borang per halaman).
2. Bila scan miring, putar dengan **↻** di pojok scan (putaran juga dipakai saat AI membaca).
3. Klik **✦ Baca dengan AI**. Ollama di komputer ini membaca header dan tabel (model vision yang sama dengan dialog AI; tulisan tangan biasanya 30–180 detik). Bila AI gagal, tabel **tidak diisi apa pun**: tidak ada data contoh / tiruan. Tabel juga boleh diisi manual (**+ Baris**, **Sisipkan**, **Hapus baris**; di RC, baris baru melanjutkan From / To dan nomor Sample ID).
4. **Periksa berdampingan**: scan di tengah, data di kanan. Sel **kuning** = AI ragu membaca atau diisi program (tanda ulang, jam menit saja, nomor truk singkat); sel **merah** = galat validasi (arahkan kursor untuk alasannya). Contoh validasi: jam / ton bukan angka, ton di luar 0–400, jam mundur atau di luar shift, kelas material tidak dikenal, nomor baris tidak urut, shift bukan I / II; RC: To ≤ From, celah / tumpang tindih interval, Sample ID ganda atau loncat (juga terhadap borang lain di proyek), remark QAQC tidak dikenal.
5. Perbaiki sel langsung di tabel (tersimpan otomatis; sel yang diedit tidak lagi ditandai ragu). Centang **✓** tiap baris yang sudah dicocokkan dengan scan — **Ctrl+Enter** = verifikasi baris terpilih & lanjut ke baris berikutnya; **✓ Verifikasi semua** untuk sekaligus.
6. Tab **Pivot** (borang ore): ritase & tonase per shift, per front (pit · elevasi · excavator) atau per asal → tujuan, dan per tujuan × kelas material.
7. Tab **Ekspor**: *borang ini* atau *semua borang jenis ini di proyek*. Bawaan **hanya baris terverifikasi** (centang *Sertakan baris yang belum diverifikasi* bila perlu; kolom VERIFIED = 0).
   - **Excel (.xlsx)**: sheet data (`Data_Loading_Pit`, `Data_ROM_Crusher`, `Interval_Geodatabase`, atau untuk Daily Drilling Report `DDR_Aktivitas` + `DDR_Meterage` + `DDR_Ringkasan_Shift`), pivot (ritase & tonase; DDR: jam per kelompok, jam per kategori, meter per rig & shift, meter per lubang), dan sheet Audit.
   - **CSV** (Daily Drilling Report: file ZIP berisi DDR_DASHBOARD.csv, DDR_AKTIVITAS.csv, DDR_METERAGE.csv, DDR_SHIFT.csv).
   - **Daily Drilling Report → dashboard drilling**: sheet Excel pertama `Data_Dashboard` (tabel `DDR_DASHBOARD`) memakai kolom yang sama dengan sheet *Data* dashboard drilling: Date (dd-mmm-yyyy), EqType (drill rig), Location (isian header *Location*), Shift (S01 = shift I, S02 = shift II), Prospect (awalan Hole ID, mis. Z4 dari Z4_295_49), BHID, Interval_m (To − From), WH, Maint, BD, Delay, Standby, Rain, Remarks (catatan), lalu **Azimuth** dan **Dip** di dua kolom paling kanan. Satu baris per lubang; jam shift (dari borang, bila kosong dari jumlah aktivitas) hanya ditulis di baris pertama shift agar total jam di dashboard tidak berlipat. Shift tanpa lubang tetap ditulis satu baris berisi jam saja. Salin baris-barisnya lalu tempel di bawah data terakhir sheet *Data*.
   - **SQLite (.db)**: tabel `ORE_LOADING_PIT`, `ORE_ROM_CRUSHER`, `RC_INTERVAL` atau `DDR_AKTIVITAS` / `DDR_METERAGE` / `DDR_SHIFT` (+ view pivot, mis. `ORE_LOADING_PIT_PIVOT_PER_SHIFT`, `DDR_METERAGE_PIVOT_METER_RIG`). Ekspor ulang memperbarui baris yang sama.
   - **MS Access (.accdb)**: database & tabel dibuat otomatis bila belum ada; baris yang sudah ada (kolom SRC_KEY = borang:baris) dilewati. Butuh driver Access 64-bit (MS Office 64-bit / Microsoft Access Database Engine).

Semua perubahan (tambah, AI, edit, verifikasi, ekspor) tercatat di riwayat borang dengan nama pengguna.

## 7. Dikerjakan bersama (beberapa geologist)

- Hasil kerja disimpan di subfolder `_GCEx_Core` **di dalam folder foto** (`gcex_core.db`). Geologist lain yang membuka folder yang sama (mis. di drive jaringan) melihat dan melanjutkan pekerjaan yang sama. Nama Anda dicatat pada setiap editan dan verifikasi.
- Foto asli tidak pernah diubah, dipindah, atau diganti namanya.
- Folder boleh dipindah ke drive lain asalkan subfolder `_GCEx_Core` ikut tersalin.
- Bila folder tidak bisa ditulisi (hanya-baca), DB-Ex memberi tahu dan menyimpan hasil di komputer ini saja.
- **Pindai ulang** mendaftarkan foto baru yang ditambahkan ke folder; foto yang dihapus ditandai **File hilang** (hasilnya tetap tersimpan).
- Sebaiknya satu folder dikerjakan satu orang pada satu waktu; dua orang mengedit foto yang sama bersamaan = editan terakhir yang berlaku.

## 8. Dari dashboard lama (Gemini)

**Impor JSON lama** membaca file proyek `.json` dari dashboard versi Gemini dan mencocokkannya per nama file foto. Hasil berstatus "Done" masuk sebagai isian AI (biru muda, belum diverifikasi); sisanya sebagai isian manual. Foto yang tidak ada di folder dilaporkan.

## 9. Batasan yang perlu diketahui

- **RQD, GSI, RMR dan core recovery dari AI adalah perkiraan visual dari foto**, bukan pengukuran di core shed (panjang potongan, kondisi rekahan, kekuatan batuan tidak bisa diukur dari foto). Pakai sebagai bantuan awal; nilai resmi tetap dari logging geoteknik.
- Posisi pita overlay di foto adalah perkiraan (interval box dibagi rata ke baris core), bukan hasil pembacaan penanda kedalaman.
- Pembacaan papan label tergantung ketajaman foto. Bila AI salah membaca Hole ID / kedalaman, perbaiki manual; lebih baik lagi beri nama file dengan pola di bagian 3.
- Keyakinan AI (rendah / sedang / tinggi) adalah penilaian model itu sendiri, bukan jaminan.

## 10. Masalah umum

| Gejala | Penyebab / solusi |
|---|---|
| Titik merah "Ollama tidak aktif" | Klik **Jalankan AI** → **Jalankan Ollama**. Bila muncul "Ollama belum terpasang", pasang `OllamaSetup.exe` dulu (bagian 2b). |
| "Belum ada model vision" | Cek `ollama list` di Command Prompt. Model qwen3-vl tercantum → perbarui Ollama ke 0.12.7+ (model tidak terhapus). Tidak tercantum → `ollama pull qwen3-vl:8b` atau salin folder model (bagian 2b). Model di drive lain → atur `OLLAMA_MODELS`. |
| AI sangat lambat | Model berjalan di CPU. Pakai `qwen3-vl:4b`, ukuran foto 1024 px, atau komputer dengan kartu grafis NVIDIA. |
| Banyak foto berstatus "AI gagal" | Arahkan kursor ke label "AI gagal" untuk melihat penyebab. Biasanya Ollama tertutup di tengah antrean atau memori habis; jalankan Ollama lagi lalu **Jalankan AI lokal** (yang gagal diulang otomatis). |
| "Folder ini tidak bisa ditulisi" | Folder hanya-baca. Hasil disimpan di komputer ini saja; salin folder foto ke lokasi yang bisa ditulisi untuk kerja bersama. |
| Foto tidak muncul di tabel | Ekstensi bukan JPG/PNG/TIFF/BMP/WEBP, atau foto ditambahkan setelah folder dibuka: klik **Pindai ulang**. |
| Data lab kosong di kartu foto | Hole ID / From / To foto belum diisi, atau Hole ID di foto berbeda dengan di file lab (mis. `LTH-101A`). Perbaiki Hole ID di kartu; data lab langsung dicocokkan ulang. |
| "Tidak ada baris yang bisa diimport" | Baris header salah (isi nomor baris yang berisi nama kolom) atau kolom From / To bukan angka. Lihat alasan di pesan. |
| Pita overlay tidak pas dengan core | Klik **Atur area core**, sesuaikan kotak & jumlah baris, simpan untuk semua foto lubang ini. |
| "Interval half core wajib diisi nomor sampel" | Isi No. sampel; bila assay punya kolom Sample, pilih dari daftar. |
| `Au>=1` → "Unsur tidak ada" | Nama unsur mengikuti **nama di DB-Ex** saat import (mis. `Au`, bukan `Au_ppm`). |
| Bar "Backend tidak aktif" | Menu **Bantuan → Buka folder log**, kirim `backend.log` dan file log terbaru. |

## 11. Hak cipta & syarat penggunaan

DB-Ex adalah ciptaan Habil Abdillah (Copyright © Habil Abdillah 2026). Saat memasang dan saat pertama kali membuka aplikasi, pengguna harus menyetujui **Syarat Penggunaan, Lisensi & Penafian**. Teks lengkap dan daftar komponen open source ada di menu **Bantuan › Syarat penggunaan & penafian** dan **Bantuan › Lisensi pihak ketiga & merek dagang**. Nilai geoteknik dari AI adalah perkiraan visual dan tidak boleh menjadi satu-satunya dasar keputusan keselamatan.

