# Panduan: mengunduh & memasang GC-Ex Desktop

Panduan ini untuk pengguna, bukan programmer. Tidak perlu memasang Python, Node.js, atau Electron —
semuanya sudah ada di dalam installer.

## 1. Mengunduh installer dari GitHub

1. Buka repositori `gcex-desktop` di github.com.
2. Klik tab **Actions**.
3. Klik baris paling atas yang bertanda centang hijau (**Build GC-Ex (Windows 64-bit)**).
   Bila masih berputar kuning, tunggu ±10 menit. Bila silang merah, kirim tangkapan layarnya ke Claude.
4. Gulir ke bawah ke bagian **Artifacts**. Ada dua installer:
   - **GC-Ex-Setup-Windows** → GC-Ex Block Model (`GC-Ex-Setup-0.17.0.exe`)
   - **GC-Ex-Drillhole-Setup-Windows** → GC-Ex Drillhole (`GC-Ex-Drillhole-Setup-0.17.0.exe`)
5. Ekstrak zip-nya lalu jalankan installer yang dibutuhkan. Keduanya boleh dipasang berdampingan;
   proyek masing-masing aplikasi disimpan terpisah.

## 2. Memasang

1. Klik dua kali `GC-Ex-Setup-0.17.0.exe`.
2. Windows mungkin menampilkan layar biru **"Windows protected your PC"** karena installer belum
   bertanda tangan digital (code signing). Klik **More info → Run anyway**.
   (Peringatan ini hilang setelah installer ditandatangani sertifikat resmi — tahap 4.)
3. Pilih folder instalasi (boleh bawaan), klik **Install**. Tidak perlu hak admin.
4. Buka **GC-Ex** dari ikon di desktop atau menu Start.

## 3. Mengecek semuanya berjalan

- Menu **Bantuan → Tentang GC-Ex**: baris *Backend* harus **aktif**.
- Bila tidak aktif: menu **Bantuan → Buka folder log**, kirim file `gcex-<tanggal>.log` dan
  `backend.log` ke Claude.
- Antivirus kantor kadang memblokir `gcex-backend.exe` karena baru. Bila perlu, minta IT
  menambahkan folder instalasi GC-Ex ke daftar pengecualian.

## 4. MS Access

Fitur Access butuh driver Access 64-bit. Bila **Tentang GC-Ex** / pesan GC-Ex menyebut driver tidak
ditemukan, pasang **Microsoft Access Database Engine 2016 Redistributable** (versi **x64**) dari situs
Microsoft. Catatan: bila Office Anda 32-bit, bicarakan dengan IT dulu — driver 32-bit dan 64-bit
tidak bisa dipasang berdampingan dengan mudah.

## 5. Mengirim register as-mined ke workbook Excel

1. Menu **As-Mined → ⑥ Layout & export → Kirim ke workbook register Excel**.
2. **Pilih workbook…** → pilih workbook akunting (mis. `GC_Ore_Accounting_Emas_v4A_SpotterTruk.xlsx`).
   GC-Ex mencari sendiri sheet yang header-nya cocok (mis. `GC_Polygon`, header baris 4).
3. **Periksa**: GC-Ex menampilkan kolom yang akan diisi, kolom rumus yang tidak disentuh, dan baris tujuan.
   File belum diubah pada langkah ini.
4. **Tutup workbook di Excel**, lalu klik **Kirim**. Hanya kolom input (oranye) di baris kosong pertama yang ditulis;
   kode poligon yang sudah ada dilewati (atau diperbarui bila dipilih). Cadangan dibuat di folder `_backup_gcex`
   di sebelah workbook (30 cadangan terakhir disimpan).
5. Buka workbook di Excel: rumus (Pit, Tanggal, Densitas, Ritase, Cek, …) dihitung ulang otomatis.

Kolom elemen tambahan (mis. `GC CU (%)`) ikut terisi bila header dengan nama yang sama ditambahkan di sheet register.

## 6. Block model .mdl besar (ratusan MB sampai beberapa GB)

- Pilih file .mdl seperti biasa dan atur filter RL. File **150 MB ke atas** otomatis dibaca oleh backend Python.
- **Pembukaan pertama** sebuah file: backend membaca seluruh file sekali dan menyimpan cache di disk
  (`%APPDATA%\GC-Ex\cache`, ukuran ±1,4 x file .mdl; contoh 6 GB -> ±8,4 GB). Uji 2 GB: ±15 detik.
- Pembukaan berikutnya / ganti rentang RL: hanya potongan yang diminta yang dikirim ke tampilan (±1-2 detik).
- Cache otomatis dibuat ulang bila file .mdl berubah. 3 model terakhir disimpan; menu
  **Bantuan -> Hapus cache block model besar** untuk mengosongkan.
- Tombol **Ringkasan seluruh model per RL** (panel Block Model) menghitung tonase & kadar per bench untuk
  seluruh file, bukan hanya potongan yang dimuat.

## 7. Memperbarui

Pasang installer versi baru di atas versi lama (tidak perlu uninstall). Proyek, pengaturan, daftar proyek,
log dan cache tidak terhapus. Cek versi terpasang di **Bantuan → Tentang**.

| Versi | Isi |
|---|---|
| 0.1.0 | Rilis awal GC-Ex Block Model desktop |
| 0.9.0 | Kedua aplikasi: file <b>.prj dibuka dengan klik dua kali</b> (asosiasi file oleh installer; .prj milik aplikasi GC-Ex lain diteruskan otomatis, .prj non-GC-Ex seperti file proyeksi ESRI dibuka di Notepad), tombol <b>layar penuh</b> di bilah atas + F11; GC-Ex Drillhole: RBF vein dengan <b>orientasi bervariasi</b> (pitch lokal dari lineasi plunge / trend struktur), <b>pinch-out di bor tanpa vein</b> (bor yang menembus bidang vein tanpa interval domain), <b>OK dengan orientasi elipsoid dinamis</b> mengikuti HW / FW vein; domain lama tidak berubah sampai opsi diaktifkan |
| 0.10.0 | GC-Ex Drillhole: <b>data struktur & pemetaan permukaan terintegrasi</b> — satu basis data struktur untuk flag GM ⑤ (kini dengan plunge / trend), Data Referensi / CSV, dan titik pick-up Map berkolom Dip / Dip_Azimuth / Plunge / Trend; garis vein / kontak hasil digitasi Map bisa dikaitkan ke domain sebagai <b>jejak singkapan</b> (titik bantu HW / FW permukaan untuk RBF); sumbu antiklin / sinklin / lineasi Map menjadi tren pitch; RBF orientasi bervariasi kini stabil (campuran beberapa TPS anisotropi, tanpa overshoot) |
| 0.11.0 | GC-Ex Drillhole: menu baru <b>Ore Geometry</b> (referensi geologist, tidak dipakai pemodelan / estimasi) — intercept otomatis & GT dijumlah per bor, <b>long section GT</b> (vertikal / bidang vein / manual) dengan RBF spheroidal 2D, <b>ore shoot</b> (gambar sumbu / usulan otomatis → pitch, plunge, trend), <b>grade shell 3D</b> indikator / numerik tanpa batas domain (N baris assay terbawah), export OBJ / DXF / CSV; ukuran installer tidak bertambah |
| 0.11.1 | Kedua aplikasi: perbaikan galat JavaScript saat sakelar <b>Ortho</b> (proyeksi ortografis) diklik ketika Penampang 2D aktif; proyeksi ortografis kini tetap dipakai saat kembali ke 3D |
| 0.12.0 | Kedua aplikasi: tombol Top / Front / Side / Iso / Tegak lurus tidak lagi membuat jendela 3D kosong (kamera dirender ulang & dipertahankan, juga sesudah Penampang 2D), layer tanpa data diberi keterangan <i>(belum ada data)</i>; GC-Ex Drillhole: tombol <b>+ Tambah versi</b> Data Spasial tidak lagi terkunci sesudah menambah versi, menu <b>Sayatan ▾</b> di bilah atas (Penampang (Sayatan) 2D, Sayatan 3D, opsi slab, digitasi string, pengaturan) menggantikan node Sayatan di Project Tree, node baru <b>4 Peta (Mapping)</b> (pick-up, digitasi, titik struktur di peta) sebelum <b>5 Struktur Geologi</b> yang kini mengelompokkan sumber (titik manual, flag GM, Peta, CSV), <b>Layer peta</b> terperinci untuk layout (per sumber struktur, per kelompok fitur, per file / kode pick-up, per domain; legenda / skala / panah utara / grid bisa dimatikan) |
| 0.12.1 | Kedua aplikasi: pemberitahuan lisensi pihak ketiga & penafian merek dagang (folder <code>legal</code> di instalasi, menu Bantuan › Lisensi pihak ketiga & merek dagang) |
| 0.13.0 | GC-Ex Block Model: garis dig block / string di Penampang 2D tidak lagi tampak <b>putus-putus</b> (ruas bersambung digabung), <b>window zoom in / out jauh lebih ringan</b> (blok digambar lewat WebGL + digabung jadi persegi panjang), <b>digitasi manual dig block</b> kini setara dengan otomatis (Enter = tutup poligon & simpan, nomor & warna string mengikuti material, langsung masuk daftar Running grade × tonnage dan bisa diedit bentuk / warna / nama / tujuan), warna poligon as-mined bisa diedit di register |
| 0.14.0 | GC-Ex Block Model: <b>tema earthy</b> (latar abu-abu hangat & putih tulang, teks charcoal, elemen navy redup, aksen oker) dan <b>tipografi UI sistem</b> (Segoe UI / Tahoma / Arial) seragam di menu, tab, dialog, log & teks grafik |
| 0.14.1 | GC-Ex Block Model: <b>blok BM di Penampang 2D digambar sebagai satu gambar</b> di lapisan paling bawah &rarr; zoom / geser tanpa jeda (± 4× lebih cepat) dan garis dig block, string & poligon <b>tidak lagi tertutup blok</b> (diberi tepi gelap agar kontras); <b>digit manual dig block setara otomatis</b>: material dari daftar kelas (nomor & warna string ikut kelas), tujuan (DEST) & warna kelas, tabel aturan kelas / tujuan, ringkasan dig block yang baru disimpan (Edit bentuk / Properti / Hapus) dan daftar running grade × tonnage; <b>Enter</b> menutup poligon & menjadikannya dig block selama flitch aktif (juga dari Digitasi string bebas); string tertutup bisa dijadikan dig block (tombol ⇨DB) |
| 0.14.2 | GC-Ex Block Model: <b>poligon as-mined digit manual</b> &mdash; Enter menutup poligon & grade × tonnage langsung dihitung; <b>warna</b> (kotak warna di tiap baris Register & daftar Poligon) dan <b>bentuk</b> (tombol ⬠, editor titik seperti dig block, hitung ulang otomatis) bisa diedit; <b>Project Tree per flitch</b>: Flitch Aktif › Semua flitch › RL atas–bawah › Dig block / Poligon as-mined (klik = buka flitch & sorot, menu Edit bentuk) dan Register & Laporan As-Mined › Per flitch (jumlah poligon, ton @ kadar) |
| 0.14.3 | GC-Ex Block Model: sampel as-mined (<b>channel & bor</b>) dengan mode import <b>Ganti / Upsert / Append</b> per set &mdash; Upsert: collar per HoleID, assay per interval (interval sama diperbarui, interval lama yang tumpang tindih diganti, lubang lain tetap); Append: baris kembar dilewati; kolom dicocokkan menurut nama; jumlah baris & riwayat import per set |
| 0.14.4 | GC-Ex Block Model: <b>UI sayatan sama dengan GC-Ex Drillhole</b> &mdash; menu <b>Sayatan ▾</b> di bilah atas (Penampang (Sayatan) 2D, <b>Sayatan 3D garis bebas</b>: tarik garis di mana saja di jendela 3D, opsi slab, digitasi, pengaturan), <b>bilah sayatan mengambang</b> (Mundur / posisi / Maju / tebal / 2D-3D, PageUp / PageDown); fitur <b>pilih arah sayatan di tampak atas</b> (gambar garis) tetap ada di menu Sayatan |
| 0.15.1 | GC-Ex Block Model: Register & Laporan As-Mined › <b>Rekap & model as-mined gabungan</b> (rekap per flitch: poligon, sub-blok, ton, kadar; <b>Hitung semua flitch</b>; satu file <b>.mdl gabungan</b> (puzzle semua flitch) atau CSV gabungan) dan <b>3D hasil kerja</b> (prisma dig block rencana, prisma poligon as-mined, sub-blok model as-mined berwarna kelas kadar; block model GC & potong slab disembunyikan sementara, bisa ditampilkan sebagai konteks); juga di Project Tree (Register › 3D hasil kerja, Rekap & model gabungan) |
| 0.16.1 | GC-Ex Drillhole: <b>selubung mineralisasi (envelope / halo) per domain vein</b> &mdash; tombol <b>+ Selubung</b> di kartu vein (Geological Modelling ①): halo ber-COG lebih kecil (bawaan Au &gt; 0,2) diusulkan otomatis dari run yang menyambung ke vein (dilusi, panjang min., perluasan maks. dari vein, opsi bor tanpa vein), disimpan di lapisan terpisah (boleh menumpuk dengan flag vein, koreksi manual Flag / Hapus flag tidak menyentuh vein), solid RBF dari kontak luar vein + halo (pinch-out ke kontak vein di sisi tanpa halo), Model Estimation: blok di dalam vein milik vein, halo = di luar vein, komposit <b>soft boundary</b> (halo + vein) atau hard; kode halo ikut atribut Domain vein untuk Geostatistik. Perbaikan: palet earthy hanya untuk GC-Ex Block Model |
| 0.16.2 | GC-Ex Drillhole: <b>selubung untuk vein bercabang (split / splay)</b> &mdash; selubung dibuat dari domain induk dan memakai interval induk + semua cabang; opsi <b>Satukan induk & cabang dalam satu selubung</b> (bawaan, hanya muncul bila ada cabang): satu bentang per bor dari kontak teratas s/d terbawah, sela waste di antara vein ikut selubung & sampelnya dihitung sebagai sampel halo; blok di dalam induk / cabang tetap milik vein |
| 0.17.0 | Semua aplikasi: <b>lisensi terikat komputer</b> (jendela Aktivasi dengan ID Komputer, kunci <code>GCEX1.…</code> / file .gcexlic, Bantuan › Lisensi GC-Ex, pengingat 14 hari sebelum berakhir; alat penerbit <code>tools/lisensi</code>); <b>tidak ada lagi akses kode sumber</b> dari aplikasi terpasang (Developer tools, F12 / Ctrl+Shift+I / Ctrl+U, view-source, unduh salinan HTML dihapus; menu Tentang disederhanakan; Electron fuses: tidak bisa dijalankan sebagai Node / di-inspect, app hanya dari arsip asar dengan cek integritas); <b>Electron 44.10 (Node 24)</b>, electron-builder 26.18, GitHub Actions v6 (Node 24), paket Python backend diperbarui (FastAPI 0.162, Uvicorn 0.54, Pydantic 2.14, Pillow 13.0, lxml 6.1, NumPy 2.5, pyodbc 5.3, PyInstaller 6.22) + audit keamanan otomatis di build |
| 0.8.0 | GC-Ex Block Model: <b>Reporting grade × tonase dengan constraint</b> (Block Model › Reporting): sisa di bawah topografi / di dalam pit, batas DTM tambahan, domain kategori / wireframe, RL min–maks, poligon (string Surpac, string digitasi / dig block, boundary as-mined), filter atribut, ringkasan per RL (tinggi & RL acuan = flitch aktif), kurva grade-tonase, CSV, tampilkan hanya blok terlapor; kedua aplikasi: <b>file proyek .prj</b> (satu file berisi proyek + file sumber block model, untuk dikirim ke rekan; buka dari jendela awal / menu Proyek); watermark "Copyright Habil Abdillah 2026" di bilah status, jendela awal, Tentang GC-Ex, properti installer dan setiap halaman PDF Block Model |
| 0.7.1 | Perbaikan: GC-Ex Block Model — tombol "Ringkasan seluruh model per RL" tidak lagi error untuk model CSV / .mdl yang dimuat penuh (tampil redup + penjelasan); GC-Ex Drillhole — pesan export .mdl tidak lagi menyebut "dibaca dengan FILTER" dengan daftar atribut kosong bila seluruh model dibaca lewat backend |
| 0.7.0 | Kuning palet diganti emas seimbang #f0c047 (komplementer tepat navy #233a7e, kontras teks navy 7,9:1) di kedua aplikasi & ikon; jarak tulisan ke tepi kotak, antar isian, dialog, tree, bilah atas & margin grafik 2D dirapatkan ±30-40% |
| 0.6.0 | Orthofoto mode "Latar paling bawah (lepas elevasi)" (bawaan, kedua aplikasi): selalu di bawah semua layer di 3D, tampak atas, slab, dan sebagai latar Penampang 2D plan; GC-Ex Block Model: tree 10 langkah kerja dengan status (✓ / berikutnya / belum), panel Properti hanya bagian langkah itu, tombol langkah sebelumnya / berikutnya; as-mined: toleransi tampil pick-up, warna pick-up menurut Z terhadap flitch, import boundary ke flitch menurut elevasi, volume "Ikuti lantai pick-up" untuk lantai tidak rata |
| 0.5.0 | Project Tree di kedua aplikasi (pohon proyek urut alur kerja + panel Properti, centang tampil/sembunyi, klik kanan: ganti, tambah versi, tampilkan sebagai surface/garis, ganti nama, hapus); GC-Ex Drillhole: bilah Sayatan (Maju/Mundur) pindah ke area tampilan dan hanya muncul saat sayatan aktif, hapus tabel survey/assay/geologi atau hole tertentu (bisa dibatalkan) |
| 0.4.0 | File jumbo: topografi / desain pit .str, .dxf, .csv dibaca per potongan 8 MB dan disederhanakan per garis (hasil identik, memori jauh lebih hemat, file > 512 MB kini terbaca); GC-Ex Block Model tampil padat tanpa transparansi/gradasi, logo "GC-Ex" dengan tulisan "Block Model" di bawahnya; huruf kedua aplikasi lebih kecil, ukuran tampilan bawaan 85% |
| 0.3.0 | Tampilan lebih profesional (tombol & pop-up timbul, lebih padat, ukuran tampilan 80–125% diingat, bawaan 90%), panduan langkah (tombol nonaktif menjelaskan alasannya, pesan "belum/dulu" dengan tombol pintas), teks antarmuka tanpa istilah browser |
| 0.2.0 | GC-Ex Drillhole (installer kedua, palet kuning-navy), block model besar lewat backend, kirim register ke Excel, elemen laporan multi-elemen, dialog & menu klik kanan desktop, simpan otomatis saat menutup / muat ulang, GPU berperforma tinggi |

## 8. Ukuran tampilan

Menu **Tampilan → Ukuran tampilan** (75/80/85/90/100/110/125%), atau Ctrl − / Ctrl + / Ctrl 0, atau Ctrl + gulir mouse.
Pilihan disimpan per aplikasi. Bawaan 85% karena layar laptop dengan skala Windows 125–150% terasa sempit.

## 9. Membedakan kedua aplikasi

- **GC-Ex Block Model**: ikon & bilah atas biru navy dengan strip kuning.
- **GC-Ex Drillhole**: ikon & bilah atas kuning emas dengan strip biru navy.

## 10. Project Tree

Panel kiri berisi **Project Tree** (atas) dan **Properti** item terpilih (bawah). Folder tersusun menurut urutan pekerjaan:

- **GC-Ex Drillhole**: Proyek → Data Spasial → Database Bor → Struktur Geologi → Sayatan & Penampang → Geological Modelling →
  Block Model → Model Estimation → Validasi BM → Reporting BM → Geostatistik → Layout & Ekspor (+ Pengaturan tampilan).
- **GC-Ex Block Model** (sejak 0.6.0): Proyek → Data Spasial → Block Model → Data Referensi → Flitch Aktif → Dig Block →
  Laporan Grade × Tonnage → Layout & Ekspor Dig Plan → As-Mined → Register & Laporan As-Mined (+ Pengaturan tampilan).
  Lingkaran nomor menunjukkan status: hijau ✓ selesai, bercincin kuning = langkah berikutnya, abu-abu = belum / opsional.
  Panel Properti hanya menampilkan bagian langkah terpilih; di bawahnya tombol langkah sebelumnya / berikutnya.

Cara pakai:
- **Klik** item: panel Properti menampilkan pengaturannya.
- **Kotak centang**: tampilkan / sembunyikan di layar 3D / 2D.
- **Klik kanan** (atau tombol ⋯): menu item, misalnya *Tambah versi*, *Tampilkan sebagai* (surface / garis / keduanya untuk
  topografi & desain pit), *Jadikan aktif*, *Ganti / perbarui (upsert)*, *Hapus tabel*, *Export*.
- **Klik ganda** atau **F2**: ganti nama (versi data spasial, block model, domain vein).
- Panah keyboard untuk berpindah, Spasi untuk centang. Garis di antara tree dan Properti bisa digeser; tombol « menyembunyikan panel kiri.

Hapus data bor (GC-Ex Drillhole, klik kanan **Database Bor** / tabelnya): hapus tabel survey, assay, geologi, hole tertentu atau
seluruh database. Folder proyek mendapat backup dulu, dan **Batalkan perubahan database terakhir** mengembalikannya.

## 11. Orthofoto sebagai latar

Klik kanan **Orthofoto** di tree (atau menu Overlay) → *Posisi orthofoto*:
- **Latar paling bawah (lepas elevasi)** — bawaan. Orthofoto tidak memakai Z topografi; selalu digambar tepat di bawah data
  terendah yang tampil, sehingga tidak menutupi block model, bor, string, poligon pada tampak atas, Iso maupun saat slab
  dipotong. Di Penampang 2D horizontal (plan) orthofoto menjadi gambar latar.
- **Drape ke topografi**: menempel di permukaan topografi.
- **Bidang datar (di atas data)**: perilaku lama.

## 12. As-mined: pick-up & boundary yang tidak tepat di RL flitch

Di langkah **As-Mined → Poligon, pick-up & lantai**, kotak *Elevasi pick-up & lantai*:
- **Tampilkan pick-up ± m**: titik pick-up dalam jarak ini dari flitch yang ditampilkan (bawaan 3 m). Warna: biru = di bawah
  lantai flitch, hijau = sekitar RL bawah (±0,3 m), oranye = di dalam flitch, merah = di atas flitch. Hover menampilkan Z dan selisihnya.
- **Import boundary masuk ke**: *Flitch aktif (abaikan Z)* seperti sebelumnya, atau *Flitch menurut elevasi string* (flitch yang RL
  bawahnya paling dekat dengan median Z string). Elevasi tiap boundary ditampilkan di daftar poligon.
- **Volume as-mined**: *Tebal flitch penuh* (bawaan, hasil sama dengan versi sebelumnya) atau *Ikuti lantai pick-up*: lantai tiap
  poligon diinterpolasi dari titik pick-up di dalam / sekitar poligon (pita Z & jarak bisa diatur, bisa disaring kode mis. TOE|FLOOR);
  tonase dihitung dari lantai aktual sampai RL atas flitch. Daftar poligon menampilkan lantai median dan tebal rata-rata.

## 13. Palet warna

| Peran | Warna | Dipakai untuk |
|---|---|---|
| Navy utama | `#233a7e` | bilah atas Block Model, tombol utama, teks judul |
| Kuning emas | `#f0c047` | logo, strip, bilah atas Drillhole, tombol aktif |
| Emas tepi | `#d6a12b` | garis tepi elemen kuning |
| Emas gelap | `#a77612` | tepi bawah tombol kuning, garis di latar putih |

Kuning emas dipilih karena hue-nya tepat berseberangan dengan navy di roda warna perseptual (OKLCH 86,5° vs 266,5°)
dan saturasinya sedikit diturunkan dari kuning lemon sebelumnya sehingga tidak "bergetar" di samping navy;
teks navy di atasnya kontras 7,9:1 (WCAG AAA).

## 14. Reporting block model dengan constraint (GC-Ex Block Model)

Project Tree › **Block Model › Reporting (constraint)**:

1. **Atribut & ringkasan per RL** — atribut kadar & satuan, cut-off, pengelompokan **per RL** (tinggi & RL acuan; tombol *= flitch aktif*) atau per atribut kategori. SG mengikuti Block Model › Filter & SG.
2. **Constraint** — domain (atribut kategori / di dalam wireframe), permukaan (*di bawah topografi = sisa / remaining*, atau *di dalam desain pit*), batas DTM tambahan (di atas / di bawah wireframe Data Referensi), RL min–maks, poligon area (string Surpac, string digitasi / dig block, boundary as-mined; di dalam / di luar), filter atribut.
3. **Hasil** — tabel grade × tonase per cut-off, kurva, ringkasan per RL, Export CSV, *Hanya blok terlapor* di tampilan.

Blok dihitung utuh menurut titik pusatnya (seperti Surpac). Untuk .mdl besar yang dibuka lewat backend, hanya rentang RL yang dimuat yang dihitung; ringkasan seluruh file tetap lewat *Ringkasan seluruh model per RL*.

## 15. File proyek .prj (kirim proyek ke rekan)

- **Simpan**: menu Proyek (atau klik kanan node Proyek) › **Simpan sebagai file .prj…**. GC-Ex menanyakan apakah file sumber block model ikut disertakan (wajib untuk block model > 1 juta blok).
- **Buka**: jendela awal › **Buka file proyek (.prj / .dh3d)**, atau menu Proyek › **Buka file .prj…**. File sumber di dalam .prj bisa diekstrak (menu Proyek › Ekstrak file sumber) atau disalin ke folder proyek.
- .prj adalah arsip ZIP standar: `gcex_prj.json` (keterangan), `proyek.dh3d` (seluruh proyek), `sumber/` (file block model). Maksimum 4 GB; proyek .prj Block Model hanya bisa dibuka di GC-Ex Block Model, begitu juga Drillhole.
- Untuk kerja tim harian tetap gunakan **folder proyek** (backup berversi & kunci pemakai); .prj untuk mengirim / mengarsipkan.

## 16. Membuka .prj dengan klik dua kali

- Installer 0.9.0 mendaftarkan ekstensi **.prj** ke GC-Ex. Klik dua kali file .prj di Explorer → aplikasi terbuka dan proyek langsung dimuat.
- Kedua aplikasi mendaftarkan .prj. Bila Windows membuka aplikasi yang salah, GC-Ex membaca isi file dan **meneruskannya ke aplikasi pemiliknya** (Block Model ↔ Drillhole). Syarat: aplikasi tujuan sudah pernah dijalankan sekali setelah dipasang.
- Ekstensi .prj juga dipakai software GIS (file proyeksi ESRI di samping shapefile). File .prj yang bukan proyek GC-Ex dibuka dengan Notepad. Bila ingin .prj GIS tetap dibuka program lain: klik kanan file › *Open with* › *Choose another app* › centang *Always*.

## 17. Layar penuh

Tombol **⛶** di bilah atas (sebelah kanan PNG), tombol **F11**, atau menu Tampilan › Layar penuh. Tekan lagi untuk keluar.

## 18. Geological Modelling v2 (GC-Ex Drillhole)

Di Geological Modelling ④ Solid › Parameter domain aktif:

- **Orientasi bervariasi (tren pitch)** — pitch elipsoid RBF di bidang vein mengikuti **lineasi** (plunge / trend) titik struktur di sekitarnya (radius pengaruh tren). Isi Plunge / Trend di Data Referensi › Struktur (atau kolom `Plunge`, `Trend` di CSV struktur). Tanpa lineasi, pitch tetap.
- **Pinch-out di bor tanpa vein** — bor yang menembus bidang tengah vein pada interval yang ter-assay / ter-log tetapi tidak punya interval domain menjadi titik ketebalan nol; vein menipis ke nol di sekitarnya (radius otomatis = ½ median jarak kontak, dibatasi 0,8 × jarak ke kontak bor terdekat). Titik tembus tampil sebagai tanda × merah di 3D. Domain yang dibuat sebelum 0.9.0 tidak berubah sampai opsi ini dicentang.

Di Model Estimation › Domain & parameter:

- **Orientasi elipsoid: Dinamis — ikuti HW / FW vein** — untuk setiap blok, sumbu variogram & elipsoid pencarian diputar mengikuti strike / dip lokal permukaan HW–FW (dan pitch lokal bila tren aktif). Pada uji vein melengkung sintetis (strike berbelok 25°): RMSE terhadap kadar sebenarnya turun 1,11 → 1,03 g/t, korelasi naik 0,77 → 0,81.


## 19. Data struktur & pemetaan permukaan terintegrasi (GC-Ex Drillhole 0.10.0)

Semua data struktur kini berada di **satu basis data** dan dipakai bersama oleh Geological Modelling (RBF, tren pitch), Model Estimation (OK dinamis), Data Referensi, Map dan tampilan 3D. Ringkasannya tampil di Geological Modelling ⑤ › *Basis data struktur terpadu*.

- **Bidang vs lineasi.** *Dip / dip azimuth* = bidang (mengatur kemiringan HW / FW setempat). *Plunge / trend* = garis di dalam bidang vein (arah shoot, striasi, sumbu lipatan) yang mengatur arah kemenerusan / pitch elipsoid. Satu titik struktur boleh punya keduanya.
- **Flag struktur GM ⑤** — kolom Plunge / Trend baru (nilai menempel untuk klik berikutnya, kosongkan bila tidak ada lineasi); tabel flag bisa diedit langsung.
- **Titik pick-up Map** — CSV `ID, East, North, RL, Code` boleh ditambah kolom `Dip, Dip_Azimuth, Plunge, Trend`. Baris berdip / dip azimuth otomatis masuk basis data struktur sebagai file "(Map pick-up)" (elevasi dari RL, kosong = dari topografi). Baris yang hanya berisi plunge / trend menjadi lineasi tren pitch. Mematikan / menghapus file pick-up di Map ikut mematikan / menghapus strukturnya. Simbol strike-dip dan panah lineasi (angka plunge) tampil di Map, lineasi berupa garis hijau di 3D.
- **Jejak singkapan vein** — di Map › Digitasi pilih garis (tipe *Vein / urat* atau *Kontak*, atau garis dari titik pick-up), lalu di kotak *Integrasi ke Geological Modelling* isi domain, jenis garis (tengah vein / kontak HW / kontak FW), lebar singkapan horizontal, dan (opsional) arah dip. Jejak menjadi titik bantu HW / FW di permukaan untuk solid RBF domain tersebut; sisi HW = ke arah dip (otomatis dari data bor bila kosong). Elevasi dari RL titik pick-up atau topografi. Di Solid ④ ada sakelar *Pakai jejak singkapan vein hasil pemetaan*, dan jejaknya tampil putus-putus di 3D.
- **Sumbu lipatan / lineasi Map** — garis tipe *Sumbu antiklin*, *Sumbu sinklin* atau *Lineasi / shoot* dapat dipakai sebagai tren pitch (semua domain di dekatnya atau domain tertentu), dengan plunge dan arah plunge (searah / berlawanan arah digitasi).
- **Uji sintetis (vein melengkung, singkapan di topografi):** selisih bidang tengah model terhadap jejak singkapan sebenarnya turun dari 1,46 m menjadi 0,03 m setelah jejak singkapan dipakai.
- **RBF orientasi bervariasi lebih stabil:** sekarang memakai campuran beberapa RBF anisotropi (pitch tiap 15°) menurut pitch setempat. Kernel rotasi pasangan di 0.9.0 bisa overshoot (tebal maksimum 36 m pada data uji dengan vein yang sebenarnya hanya setebal 6 m). Cara baru menjaga tebal tetap wajar (maks 6,0 m), dan hasil OK dinamis pada uji 0.9.0 tidak berubah.


## 20. Ore Geometry (GC-Ex Drillhole 0.11.0)

Node paling bawah di Project Tree, bertanda **REFERENSI**. Menu ini untuk melihat geometri deposit secara utuh **sebelum** pemodelan & estimasi. Hasilnya **tidak** ditulis ke basis data struktur, Geological Modelling, maupun Model Estimation (hanya parameter & sumbu shoot yang disimpan di proyek).

- **① Data & intercept** — unsur, cut-off, panjang minimum, dilusi internal maksimum. Intercept dibentuk otomatis per bor; GT = Σ(kadar × panjang) semua intercept **dijumlah per bor**, dikoreksi ke tebal sebenarnya terhadap **bidang acuan** (otomatis dari sebaran intercept berbobot GT, atau manual). Bor tanpa intercept yang menembus bidang acuan (atau berjarak ≤ toleransi) ikut sebagai GT 0 sehingga kontur tertutup. Export CSV intercept.
- **② Long section GT** — bawaan **vertikal** dengan azimuth = strike bidang acuan (bisa diisi), atau proyeksi ke bidang vein miring, atau manual (azimuth + dip). Kontur GT dari RBF spheroidal lokal 2D (range mayor / minor / arah, alpha 3–9, nugget, log(GT+1)); tidak diekstrapolasi di luar range data. Kelas GT bisa diisi sendiri. GT juga tampil sebagai permukaan berwarna di bidang vein di 3D.
- **③ Ore shoot** — **gambar sumbu** di long section (2 klik) atau **usulan otomatis** (fan variogram GT di bidang vein, termasuk bor GT 0). Garis dikembalikan ke bidang vein, lalu dihitung **pitch** (di bidang vein, dari arah strike), **plunge** dan **trend**. Lineasi lapangan di basis data struktur hanya ditampilkan sebagai pembanding. Export CSV (format sama dengan CSV struktur — bila ingin dipakai pemodelan, import sendiri secara sadar).
- **④ Grade shell 3D** — dari seluruh data bor tanpa batas domain. **Indikator** (bawaan, peluang ≥ 0,5) atau **numerik** (log). Elipsoid spheroidal lokal (dip / dip dir / pitch dari bidang acuan atau sumbu shoot, range mayor / semi / minor). Bila tabel assay lebih besar dari **Maks baris assay** (bawaan 100.000), dipakai **baris paling bawah** (data terbaru). Dihitung di latar belakang (Web Worker) tanpa backend tambahan, isosurface dengan marching tetrahedra. Tabel hasil: volume dan persentase sampel ≥ cut-off yang tertangkap shell. Export OBJ / DXF. Tombol **Pratinjau cepat** memakai grid kasar.
- **Uji sintetis** (vein strike 045 / dip 70, shoot pitch 60°): bidang acuan 70,1° → 135,0°; usulan otomatis pitch 60° (plunge 54,5° → 076°, sama dengan kebenaran); uji ulang dengan pitch 25° dan 130° juga tepat. Sumbu yang digambar di long section vertikal dikonversi kembali dengan selisih < 0,1°. Grade shell indikator ≥ 1 g/t menangkap 95 % komposit ≥ 1 g/t. Data 277 ribu baris assay: intercept + long section ± 5 detik, grade shell 100 ribu baris ± 30 detik (pratinjau ± 7 detik).


## 21. Sayatan, Peta (Mapping) & Layout (GC-Ex Drillhole 0.12.0)

- **Menu Sayatan ▾ (bilah atas)** — satu tombol berisi *Penampang (Sayatan) 2D*, *Sayatan 3D*, opsi slab (potong data di dalam slab, bidang potong, profil topo / pit), *Digitasi string di penampang*, dan *Pengaturan Sayatan & Penampang…* (panel Properti tetap). Saat Penampang 2D aktif tombol bertanda **2D**. Node *Sayatan & Penampang* tidak lagi ada di Project Tree.
- **4 Peta (Mapping)** — *Pick-up survei / pemetaan* (per file, bisa dicentang / dihapus), *Digitasi peta* (per fitur), *Titik struktur (klik di peta)*: isi dip / dip az (opsional plunge / trend & keterangan), aktifkan, lalu klik di peta. Elevasi dari topografi. Titik langsung masuk Struktur Geologi.
- **5 Struktur Geologi** — satu basis data dengan sumber dikelompokkan: *Titik manual (3D)*, *Flag struktur (Geological Modelling)*, *Dari Peta (Mapping)* (titik struktur peta, pick-up berkolom struktur, jumlah garis struktur peta), *File CSV struktur*. Centang = dipakai pemodelan & tampil. File pick-up yang sama dengan CSV struktur yang sudah di-import tidak digandakan.
- **12 Layout & Ekspor › Peta (layout cetak)** — *Layer peta (isi peta)*: peta dasar, database bor (per domain), struktur (per sumber; panah lineasi), fitur digitasi (per kelompok), titik pick-up (per file & per kode). Hanya memengaruhi peta & layout. *Layout & cetak*: elemen layout legenda, skala grafis, panah utara, grid koordinat bisa dimatikan.
- **Kamera 3D** — tombol arah pandang dirender ulang (sumbu dihitung ulang) dan kamera / proyeksi Ortho dipertahankan pada setiap render, termasuk setelah Penampang 2D.


## 22. Hak cipta, syarat penggunaan & lisensi open source (0.17.1)

- **Installer** ketiga aplikasi menampilkan halaman **Syarat Penggunaan, Lisensi & Penafian** (Bahasa Indonesia & English) yang harus disetujui sebelum memasang.
- **Saat aplikasi pertama kali dibuka** (sebelum aktivasi lisensi GC-Ex, dan setiap kali versi syarat berubah) muncul ringkasan syarat dengan tombol *Setuju*, *Baca selengkapnya*, *Tidak setuju (keluar)*. Persetujuan dicatat (versi + waktu) di `settings.json` folder data aplikasi.
- Isi pokok syarat: hak cipta Habil Abdillah atas GC-Ex (UU No. 28 Tahun 2014); izin pakai non-eksklusif dan tidak dapat dialihkan; larangan menjual / membagikan ke pihak lain / membongkar / menghapus tanda hak cipta tanpa izin tertulis; tanpa jaminan; batasan tanggung jawab; hasil teknis dan nilai geoteknik AI adalah alat bantu / perkiraan, bukan dasar tunggal keputusan keselamatan; data diproses lokal; Ollama & model AI tunduk lisensinya sendiri; hukum Indonesia.
- **Tanda hak cipta** "Copyright © Habil Abdillah 2026" ada di ujung kanan bilah status bawah ketiga aplikasi. Bila tulisan itu dihapus atau disembunyikan, aplikasi memasang ulang tanda cadangan di sudut kanan bawah (tidak menangkap klik dan tidak menutupi data).
- File **Excel** yang dibuat GC-Ex (register, log core box) memuat tanda hak cipta di footer cetak dan di properti file; data pengguna tidak diubah.
- Menu **Bantuan › Syarat penggunaan & penafian** dan **Bantuan › Lisensi pihak ketiga & merek dagang** (juga tombol di **Bantuan › Tentang GC-Ex**) membuka folder `legal` di instalasi: `SYARAT_PENGGUNAAN.txt`, `LISENSI_PIHAK_KETIGA.txt` (daftar komponen open source), `LISENSI_PYTHON.txt` (dibuat otomatis saat build, sesuai isi installer), `LISENSI_ELECTRON.txt`, `LISENSI_CHROMIUM.html`, `LISENSI_FONT_OFL.txt`, `LISENSI_PLOTLY_BUNDEL.txt`, `PENAFIAN_MEREK.txt`.
- Semua komponen pihak ketiga berlisensi permisif (MIT / BSD / PSF / Apache-2.0 / SIL OFL / zlib; PyInstaller GPL-2.0 dengan pengecualian bootloader) sehingga boleh dipakai & dibagikan, termasuk komersial, asalkan file-file ini ikut disertakan — jangan dihapus dari folder instalasi. Font Playfair Display & Courier Prime dibundel sebagai file asli tanpa diubah.
- Sumber file statis ada di repositori: `legal/`, generator `legal/gen_licenses.py`, watermark `electron/watermark.js`. GitHub Actions memeriksa file-file ini ada di setiap installer.

## 23. Core-Ex (0.15.0)

- Aplikasi ketiga: installer `Core-Ex-Setup-<versi>.exe` (artifact **Core-Ex-Setup-Windows**). Shortcut **Core-Ex**, data di `%APPDATA%\Core-Ex`.
- Interpretasi foto core box dengan AI vision **lokal** (Ollama + mis. `qwen3-vl:8b`), 100% offline. Foto dibaca langsung dari folder oleh backend; hasil di `<folder foto>\_GCEx_Core\gcex_core.db` sehingga rekan bisa melanjutkan.
- 0.16.0: repositori dokumentasi core box — import Collar / Survey / Assay / Geologi (CSV / Excel, **header dinamis**: pengguna memilih kolom sendiri), cari cepat (Ctrl+K, termasuk `Au>=1`), filter kadar, panel data lab per foto, dan **overlay assay & geologi di foto core box**.
- Prinsip: **AI visual untuk parameter geoteknik**; litologi / alterasi / oksidasi / warna dari **logging geologist** diutamakan, AI hanya mengisi bila logging tidak ada.
- Panduan lengkap, termasuk memasang Ollama & model tanpa internet: `docs/PANDUAN_CORE.md` (di aplikasi: **Bantuan › Panduan AI lokal (Ollama)**).



## 24. Lisensi GC-Ex (0.17.0)

- Saat pertama dibuka, GC-Ex menampilkan jendela **Aktivasi** berisi **ID Komputer**. Kirim ID itu ke penerbit lisensi, lalu tempel kunci yang diterima (diawali `GCEX1.`) atau buka file `.gcexlic` → **Aktifkan**.
- Satu lisensi berlaku untuk aplikasi GC-Ex yang tercantum di kunci (Block Model / Drillhole / Core / semua) di komputer itu saja; disimpan di `%APPDATA%\GC-Ex Lisensi\lisensi.json`. Pindah komputer / install ulang Windows = minta kunci baru.
- Info, ganti atau hapus lisensi: **Bantuan → Lisensi GC-Ex…**. Pengingat muncul 14 hari sebelum lisensi berakhir.
- Penerbit: alat `tools/lisensi/GCEx_Pembuat_Lisensi.html` + kunci privat (disimpan offline oleh pemilik GC-Ex). Rincian: `tools/lisensi/BACA_SAYA.md`.
- Tutorial bergambar (pengguna & penerbit, tabel pesan galat, FAQ): `docs/GC-Ex_Tutorial_Aktivasi_Lisensi.pdf`.
- Pemberitahuan lisensi pihak ketiga (MIT / BSD / PSF) disertakan di folder instalasi `resources\legal` dan bisa dibuka lewat **Bantuan → Lisensi pihak ketiga (open source) & merek dagang**.

## 25. Ganti nama: Core-Ex (0.18.0)

- **GC-Ex Core Interpretation** sekarang bernama **Core-Ex** (Core Excellence). Fitur tidak berubah; tetap keluarga GC-Ex.
- Installer: `Core-Ex-Setup-<versi>.exe` (artifact **Core-Ex-Setup-Windows**). Memasang di atas versi lama otomatis menggantikannya (appId sama); shortcut lama diganti shortcut **Core-Ex**.
- Pengaturan, cache dan log dipindahkan sekali dari `%APPDATA%\GC-Ex Core Interpretation` ke `%APPDATA%\Core-Ex` saat Core-Ex pertama dibuka.
- Lisensi yang sudah aktif tetap berlaku (kode aplikasi di kunci tetap `core`); tidak perlu aktivasi ulang. Di alat Pembuat Lisensi, centang **Core-Ex**.
- Proyek foto lama tetap terbaca: folder `_GCEx_Core` dan database `gcex_core.db` di folder foto tidak diubah.
- Syarat penggunaan diperbarui (versi 2026-10-29, memuat nama Core-Ex), jadi diminta disetujui sekali lagi.

## 26. Core-Ex menjalankan Ollama sendiri (0.18.1)

- Ollama tetap dipasang terpisah (sekali per komputer), tetapi tidak perlu dibuka manual: bila belum aktif saat Core-Ex dibuka, Core-Ex menjalankan aplikasi Ollama (`%LOCALAPPDATA%\Programs\Ollama\ollama app.exe`, atau `ollama serve` tersembunyi bila hanya CLI yang ada) lalu menunggu sampai siap (maks. 30 detik).
- Bisa dimatikan: dialog **Jalankan AI** → hilangkan centang *Jalankan Ollama otomatis saat Core-Ex dibuka*. Tombol **Jalankan Ollama** tetap ada di dialog AI dan di halaman awal.
- Hanya untuk alamat Ollama di komputer ini (127.0.0.1 / localhost). Bila Ollama tidak ditemukan, Core-Ex menulis "Ollama belum terpasang".

## 27. Data besar tanpa jeda & pembaruan offline (0.18.2)

**Block model .mdl sangat besar (contoh uji: 6,2 GB, 141 juta blok, laptop RAM 7 GB, 2 inti CPU)**
- File .mdl ≥ 150 MB dibaca sekali oleh backend menjadi cache di disk (uji 6,2 GB: ±85 detik, sekali saja). Indeks RL sekarang dibuat di disk, bukan di RAM: memori backend saat membangun cache turun dari ±2,8 GB menjadi ±0,6 GB.
- Siapkan ruang disk kosong ±1,5–2 × ukuran file .mdl untuk cache (GC-Ex memberi tahu bila kurang). Tiga cache terakhir disimpan; yang lama dihapus otomatis.
- **Batas blok per pemuatan** supaya RAM / VRAM 4 GB tidak penuh: ±1,5 juta blok (RAM ≤ 4 GB), ±2,5 juta (RAM < 8 GB), ±3,5 juta (RAM ≥ 8 GB). Bila rentang RL yang diminta berisi lebih banyak blok, GC-Ex memuat **rentang RL teratas yang muat** dan menampilkan pesan berisi RL yang dimuat. Untuk bench lain, import ulang dengan isian **RL bawah / RL atas** (atau centang *Hanya di dalam desain pit*). Mengambil potongan 2,5 juta blok dari model 6,2 GB: ±3,5 detik.
- **Penampang 2D**: blok dilukis langsung ke gambar (bukan jutaan kotak), PNG penuh dikodekan di latar sehingga layar tidak membeku. Uji 2,5 juta blok: pindah ke 2D ±2 detik (sebelumnya ±42 detik), menggambar ulang / zoom / digitasi ±0,01 detik (sebelumnya ±3,3 detik).
- **3D**: jumlah kubus tetap dibatasi profil Kinerja (Hemat 60 rb · Seimbang 150 rb · Penuh 400 rb) dan hanya sisi luar yang digambar, sehingga VRAM 4 GB cukup. Untuk melihat semua blok gunakan cut-off, Potong data atau Penampang 2D.
- Batas heap JavaScript jendela GC-Ex dinaikkan ke 4 GB.

**Data bor besar (GC-Ex Drillhole), uji 2.500 lubang / 250.000 baris assay + 250.000 baris geologi**
- Impor + desurvey + gambar pertama ±5 detik (sekali, sebagian besar menggambar 3D); geser sayatan 2D ±0,2–0,6 detik; domain otomatis ±0,3 detik; memori ±0,5 GB. Tidak perlu pengaturan khusus.

**Pembaruan (offline)**
- GC-Ex tidak pernah memeriksa pembaruan lewat internet dan tidak memasang pembaruan sendiri (installer tidak berisi data publish / auto-update).
- Setiap versi dibangun dari kode di repositori GitHub milik admin (GitHub Actions → *Build GC-Ex (Windows 64-bit)*). Ketiga installer diterbitkan ke **GitHub Releases** repo (privat), tag `v<versi>` — buka repo → *Releases* → unduh `GC-Ex-Setup-…`, `GC-Ex-Drillhole-Setup-…`, `Core-Ex-Setup-…`. Releases tidak memakan kuota artifact Actions; artifact Actions tetap dibuat sebagai cadangan 7 hari bila kuota cukup.
- Pelanggan yang ingin memperbarui meminta installer versi terbaru ke admin; admin mengunduh dari Releases lalu mengirimkannya.
- Ketiga aplikasi tetap dipasang terpisah (satu installer per aplikasi). Memasang versi baru di atas versi lama: pengaturan, proyek dan lisensi tetap.

## 28. Grade shell dengan Surface-Following (GC-Ex Drillhole 0.18.3)

- Menu **Ore Geometry → ④ Grade shell 3D**: opsi baru **Surface-Following (cepat)**, aktif bawaan. Ide dari metode Surface-Following pada pemodelan implisit RBF: RBF tidak dihitung di seluruh kotak, tetapi hanya di sekitar permukaan cut-off.
- Cara kerja: RBF dihitung dulu di grid kasar (tiap 4 sel), lalu hanya blok yang dilintasi batas cut-off, tepi jangkauan data, dan blok berisi sampel ≥ cut-off (beserta tetangganya) yang dihitung penuh. Sisanya (jauh di dalam / jauh di luar shell) diisi interpolasi; mesh marching tetrahedra dan volume tetap di grid halus. Berlaku otomatis bila grid ≥ 150 ribu titik.
- Uji 250.000 baris assay (grid 2,6 juta titik): indikator 3 cut-off 104 → 20 detik, numerik 35 → 8 detik; jumlah segitiga, volume dan validasi sampel **identik** dengan perhitungan penuh. Uji data tutorial (grid 2,5 juta titik): 1,3–1,5 × lebih cepat, selisih volume ≤ 0,2 %.
- Hilangkan centang untuk menghitung seluruh grid (perilaku lama), mis. untuk pembanding.

## 29. GitHub Release lengkap untuk ketertelusuran (0.18.4)

Setiap build di `main` menerbitkan **Release `v<versi>`** (repo → *Releases*; privat) berisi:

| File | Isi |
|---|---|
| `GC-Ex-Setup-<v>.exe`, `GC-Ex-Drillhole-Setup-<v>.exe`, `Core-Ex-Setup-<v>.exe` | installer, dipasang satu per satu |
| `GC-Ex-<v>_1_Dokumen.zip` | README, panduan teknis (PANDUAN_INSTALL, PANDUAN_CORE), tutorial PDF: GC-Ex Modelling & Estimasi, Core-Ex, Aktivasi Lisensi |
| `GC-Ex-<v>_2_Data-Latihan.zip` | data simulasi GC-Ex Drillhole & Block Model (SIM_*), paket dummy Core-Ex (foto core box & data lab fiktif), generator datanya |
| `GC-Ex-<v>_3_Lisensi-dan-Tentang.zip` | TENTANG.txt (versi, commit, tanggal build), syarat penggunaan, lisensi open source, penafian merek, alat pembuat lisensi admin (tanpa kunci privat) |
| `GC-Ex-<v>_CATATAN_RILIS.md` | isi rilis + daftar perubahan (commit) sejak rilis sebelumnya + SHA-256 |
| `SHA256SUMS.txt` | sidik jari semua file (cek keaslian file yang dikirim ke pelanggan) |
| Source code (zip / tar.gz) | kode sumber persis commit rilis (otomatis dari tag) |

- Versi dinaikkan pada setiap pembaruan (termasuk perubahan dokumen / data latihan saja), sehingga tiap pembaruan punya Release sendiri. Build ulang versi yang sama mengganti Release versi itu dengan isi terbaru.
- Tutorial & data simulasi GC-Ex kini disimpan di repo: `docs/tutorial-gcex/`.
- 0.18.5: daftar perubahan di catatan rilis kini UTF-8 (tanda — dll. tidak rusak) dan jam commit dalam WIB.

## 30. Tampilan baru GC-Ex Block Model & Drill Hole Ultimate (0.19.0)

- **Halaman muka penuh** (gaya Core-Ex): judul, tiga langkah kerja, lalu kartu Folder proyek / Proyek tersimpan / impor data. Tidak lagi berupa pop-up di atas tampilan.
- **Nama project site**: isian di halaman muka. Tampil di bilah atas di bawah *Grade Control Excellence* dan **disimpan per proyek** (membuka proyek tersimpan / file .prj memakai nama site proyek itu).
- **Logo** dua baris rata kiri-kanan: *GC-Ex* di atas, *BLOCK MODEL* atau *DRILL HOLE ULTIMATE* di bawah.
- **Warna**: kedua aplikasi earthy & muted; biru dari Core-Ex (#1d4785 / #2a5ea8), aksen oker tanah (#b5893e), latar kertas. Drill Hole Ultimate tidak lagi kuning terang.
- **Sayatan 2D**: nama baru untuk *Penampang (Sayatan) 2D* di semua menu, tree dan petunjuk.
- **Gambar garis sayatan**: membuka jendela 3D **tampak atas** dengan data tetap tampil; tarik garis P1 → P2 langsung di atasnya (bidang tegak, dip bisa diubah di Properti).
- **Block Model → Dig Block → Rekap & edit string** (dulu *Digitasi string bebas*): tabel string (tampil, nomor, keterangan, titik, panjang, bidang) dengan tombol ✎ edit bentuk dan × hapus; pembuatan string baru di bawahnya.
- **Bilah "Langkah x / 10 · Berikutnya" dihapus**: urutan kerja dan flitch tersedia langsung di Project Tree.
- **Drill Hole Ultimate → Geological Modelling**: *+ Tambah domain…* di Project Tree; Properti hanya menampilkan **domain aktif** yang dipilih di tree (Flag, String, Solid, Struktur bekerja pada domain itu); nomor bagian (② ③ ④ ⑤) dihapus.
- **Legenda**: string kontrol bernomor digabung per domain & sisi (mis. *QV_Utama_HW*, *QV_Utama_FW*).

## 31. Domain aktif di Geostatistik & Model Estimation (GC-Ex Drill Hole Ultimate 0.20.0)

Versi ini hanya untuk **GC-Ex Drill Hole Ultimate** (`GC-Ex-Drillhole-Setup-0.20.0.exe`, Release v0.20.0). GC-Ex Block Model dan Core-Ex tetap versi 0.19.0 (Release v0.19.0).

- **Satu domain aktif** dipakai bersama Geological Modelling, Geostatistik dan Model Estimation.
- Mengaktifkan domain dari Project Tree, di mana saja: node domain di bawah **Geological Modelling**, **Geostatistik** atau **Model Estimation** (tanda *aktif*). Tidak perlu kembali ke Geological Modelling.
- **Geostatistik**: komposit hanya dari interval bor yang di-flag ke domain aktif (domain + cabangnya; selubung = interval halo). Bilah **Domain** di atas panel Geostatistik menunjukkan domain yang dipakai dan bisa diganti di situ. **Semua data (tanpa filter domain)** = perilaku lama. *Simpan ke domain* otomatis memilih domain aktif. Filter *Domain untuk analisis* di menu Geologi tetap berlaku di atasnya.
- **Model Estimation**: Properti menampilkan parameter domain aktif. **▶ Jalankan domain aktif** hanya mengestimasi domain aktif; **▶ Jalankan semua domain** mengestimasi semua domain yang dicentang (centang di node domain Model Estimation atau di tabel). Keduanya juga ada di menu … node Model Estimation.
- Tutorial *GC-Ex Modelling & Estimasi* diperbarui: bab **Domain aktif di Geostatistik & Model Estimation (versi 0.20)**.

## 32. Additional flagging & review per flitch (GC-Ex Block Model 0.20.1)

Versi ini hanya untuk **GC-Ex Block Model** (`GC-Ex-Setup-0.20.1.exe`, Release v0.20.1). Nomor 0.20.1 dipakai karena Release v0.20.0 sudah milik GC-Ex Drill Hole Ultimate. Drill Hole Ultimate tetap 0.20.0 dan Core-Ex tetap 0.19.0.

**Additional flagging** (menggantikan *Aturan sulfida / material SxS*; Dig Block → Otomatis → *Additional flagging (garis ganda)*)
- Daftar aturan: *Nama flag*, *Unsur* (kolom block model), *> / ≥*, *COG*. Flag diberikan ke **seluruh poligon** dig block bila **komposit** unsur di dalam poligon (rata-rata tertimbang tonase) melewati COG. Contoh: *Ore Sulfide* = S > 0,8 %; *Zn tinggi* = Zn > 500 ppm; *Cu tinggi* = Cu > 500 ppm. Satuan COG = satuan kolom block model.
- Aturan kode kategori tetap ada (flag bila ≥ 50 % tonase berkode tertentu).
- Poligon ber-flag: **garis ganda** (jarak ke dalam diatur di *Garis ganda ke dalam (m)*), nama flag di label dig plan & PDF, daftar dig block (⚑) dan Project Tree. Aturan *Tujuan (DEST)* kolom **Flag?** (Ya / Tidak / semua) memakai flag ini.
- Proyek lama: kolom sxs & batas serta kode sulfida otomatis menjadi aturan *Ore Sulfide*.

**Review flitch per flitch di Project Tree** (dihitung dari poligon tersimpan; flitch aktif tidak berubah)
- **Dig Block → Per flitch**: tiap flitch (RL atas – bawah, tanda *aktif*) berisi poligon: nama · material → tujuan, ton @ kadar, ⚑ flag. Klik = buka flitch di Sayatan 2D & sorot poligon; menu: *Edit bentuk*, *Hapus*.
- **Laporan Grade × Tonnage → Per flitch**: ton @ kadar per flitch dan per material → tujuan. **Rekap semua flitch (CSV)**: satu baris per dig block di semua flitch (RL, material, tujuan, luas, ton, kadar, metal, flag).
- **As-Mined → Per flitch**: *Rencana* (dig block) vs *Aktual* (as-mined) ton @ kadar dan selisih (Δ %). Klik = buka flitch dengan poligon dig block dan as-mined bertumpuk di Sayatan 2D.
- *Flitch Aktif → Semua flitch* dan *Register & Laporan As-Mined → Per flitch* tetap ada.
- Legenda: string dig block bernama sama (mis. *String 17 HG*) tampil sekali.

## 33. Tutorial baru & data latihan (GC-Ex Block Model 0.20.2)

- **Tutorial GC-Ex Block Model** (`GC-Ex_Tutorial_Block_Model.pdf`, di `GC-Ex-<versi>_1_Dokumen.zip` → *Tutorial*): halaman muka & nama project site, flitch & Sayatan 2D, dig block otomatis, **additional flagging**, digit manual & rekap string, laporan grade × tonase, **review per flitch** di Project Tree, layout dig plan, **as-mined rencana vs aktual**, register & 3D hasil kerja.
- **Tutorial GC-Ex Drill Hole Ultimate** (`GC-Ex_Tutorial_Modelling_Estimasi.pdf`): semua gambar diambil ulang dari aplikasi 0.20 (halaman muka penuh, Project Tree, Sayatan 2D, domain aktif), langkah tambah domain lewat Project Tree, bab domain aktif di Geostatistik & Model Estimation.
- **Data latihan**: `SIM_BM_GC.csv` mendapat kolom fiktif **S_PCT** (%), **ZN_PPM**, **CU_PPM** untuk latihan additional flagging (generator `tambah_unsur_bm.py`).
- **As-Mined → Per flitch**: setiap flitch menampilkan selisih Δ; di dalamnya subnode **Rencana (dig block)** dan **Aktual (as-mined)** beserta poligon (label tidak lagi terpotong).
- Skrip pembuat tutorial ada di `docs/tutorial-gcex/src` (gambar dibuat ulang dari aplikasi di repo: `tutorial_shots.py`, `shot_rusak.py`, `tutorial_bm_shots.py`; PDF: `build_tutorial.py`, `build_tutorial_bm.py`).

## 34. Database proyek SQLite (GC-Ex Block Model & Drill Hole Ultimate 0.20.3)

Release v0.20.3 berisi installer **GC-Ex Block Model 0.20.3** dan **GC-Ex Drill Hole Ultimate 0.20.3**. Core-Ex tetap 0.19.0.

- Setiap kali proyek tersimpan ke **folder proyek**, GC-Ex memperbarui file **`gcex_proyek.db`** (SQLite) di folder itu. Proyek lama tanpa .db: dibuat otomatis pada penyimpanan pertama. Saat folder dibuka, .db yang ada dipakai sebagai dasar sehingga riwayat lama tetap.
- **Block Model**: tabel `digblock` (id, RL atas / bawah, nama, material, tujuan, luas, ton, kadar, flag, titik), `asmined` (id, RL, kode, aktif, dihitung, BCM, ton, kadar, titik) dan view **`rekap_flitch`** (rencana vs aktual per flitch).
- **Drill Hole Ultimate**: `collar`, `survey`, `assay` (satu kolom per unsur), `geologi`, `domain`, `flag_domain`, `estimasi_run` dan view **`assay_domain`** (setiap interval assay beserta domain flag-nya).
- **Jejak perubahan**: tabel `riwayat` mencatat setiap baris yang ditambah / diubah / dihapus (waktu, pengguna, aplikasi, data lama & baru); tabel `sinkron` mencatat setiap penyimpanan dan versi aplikasinya. Impor pertama sebuah tabel dicatat satu baris ringkas.
- Project Tree → **Proyek → Database proyek (SQLite)**: jumlah baris; klik = isi tabel & riwayat perubahan terakhir, tombol *Sinkronkan sekarang*.
- File .db bisa dibuka dengan **DB Browser for SQLite**, Excel (ODBC), QGIS, Python, dll. Contoh: `SELECT * FROM rekap_flitch;` atau `SELECT domain, COUNT(*), AVG(Au) FROM assay_domain GROUP BY domain;`.
- Hanya di aplikasi desktop (memakai backend GC-Ex); file proyek `.prj` tetap dipakai untuk mengirim proyek ke rekan.

## 35. Sesar 3D & Geomodeller Stratified-Laterite (GC-Ex Drill Hole Ultimate 0.21.0)

Release v0.21.0 berisi installer **GC-Ex Drill Hole Ultimate 0.21.0**. GC-Ex Block Model tetap 0.20.3 dan Core-Ex tetap 0.19.0 (installer ada di rilis sebelumnya).

- Menu **Geological Modelling** berganti nama menjadi **Geomodeller Vein System Deposit** (rel kiri: *Geomodeller Vein*); isi & cara kerja sama.
- **Sesar 3D** (rel kiri, sesudah Sayatan; Project Tree → Struktur Geologi → Sesar (bidang 3D)): sesar dari garis struktur di Peta atau koordinat manual + dip / dip direction → bidang 3D (panjang searah strike = panjang jejak). Atribut: jenis (normal / naik / mendatar dekstral / sinistral / oblik trend-plunge), offset (net slip), waktu **pre / syn / post** mineralisasi, urutan umur (1 = tertua), relasi *memotong* (divalidasi; tombol urutkan otomatis), batas keras, taper ujung. Export CSV & DXF.
  - Post + offset: kontak & sampel dipulihkan (sesar termuda dulu) → solid vein / permukaan lapisan & estimasi dikerjakan di ruang pulih → hasil digeser kembali, terpotong di bidang sesar.
  - Batas keras: sampel tidak dipakai menyeberang sesar. Syn: bidang sesar mengarahkan orientasi solid vein (jarak pengaruh).
- **Geomodeller Stratified-Laterite Deposit** (rel kiri: *Geomodeller Strata-Laterit*): preset laterit nikel / bauksit / sedex; lapisan dari kolom log geologi + densitas & kadar air; permukaan atap (topografi − kedalaman kontak) & ketebalan isopach (grid, ekstrapolasi terbatas); estimasi per lapisan di koordinat **unfold** (OK / IDW blok 3D atau akumulasi 2D), multi-unsur & rasio (mis. SiO2/MgO) ke atribut block model `sl_*`; laporan volume / WMT / DMT / kadar dengan cut-off; export grid CSV & DXF permukaan.
- Database proyek SQLite: tabel baru `sesar` dan `lapisan`.
- Tutorial `GC-Ex_Tutorial_Modelling_Estimasi.pdf` diperbarui (bab Sesar 3D & Geomodeller Stratified-Laterite); data latihan baru `SIM_LAT_*` (laterit nikel fiktif dengan sesar F1) + generator `make_sim_laterit.py`.

## 36. Folder foto besar (Core-Ex 0.21.1)

- Ukuran folder (GB) tidak dimuat ke memori: Core-Ex hanya mendaftar nama & ukuran file, lalu membuka foto satu per satu saat dilihat / dianalisis AI. Uji 30 Okt 2026: 4.501 foto (24 MP + satu panorama 117 MP), 45,6 GB nominal → scan 0,4 s, buka ulang 0,2 s, buka folder di UI 0,9 s, tabel tetap lancar digulir.
- Thumbnail & pratinjau JPEG kini didecode langsung di skala kecil: ±2× lebih cepat, memori backend ±100 MB (sebelumnya ±470 MB setelah 60 thumbnail 24 MP).
- Foto panorama / gabungan di atas 178 MP tidak lagi ditolak (batas dinaikkan ke 1,5 miliar piksel).
- Cache thumbnail & pratinjau ada di `%APPDATA%\Core-Ex\cache` (±10 KB per thumbnail, ±100–300 KB per pratinjau). Untuk puluhan ribu foto, sisakan beberapa GB di drive C:.
- Database `_GCEx_Core\gcex_core.db` hanya berisi teks & angka (ribuan foto = beberapa MB), aman di drive jaringan.

## 37. Tanda half core & core loss (Core-Ex 0.22.0)

- Tombol **tanda** di pratinjau foto → pilih jenis (Half core / Core loss / jenis lain) → **Mulai menandai** → tarik di sepanjang baris core. Kedalaman dihitung dari posisi di foto (dibulatkan 0,05 m) dan bisa diketik ulang.
- Half core wajib nomor sampel (terisi otomatis dari kolom Sample di assay bila ada). Core loss menghitung **Core Recovery** foto otomatis: (interval − core loss) / interval; berlabel *tanda*, tidak ditimpa AI.
- Disimpan di `_GCEx_Core/gcex_core.db` (tabel `marks`) bersama riwayat perubahan; ikut sheet Excel **Interval** dan export CSV dari panel.
- Proyek lama terbuka seperti biasa; tabel dan kolom baru dibuat otomatis.

## 38. Overlay berlapis & interpretasi per baris (Core-Ex 0.23.0)

- Overlay foto kini berupa **lapisan**: kolom assay, kolom logging geologi apa pun, interpretasi per baris (Litologi, Alterasi, Pelapukan, Oksidasi, RQD, Recovery, Rekahan/m, GSI, RMR) dan isian kartu foto. Preset, urutan, warna & kelas disimpan di proyek.
- AI menilai **tiap baris core** dan membaginya mengikuti batas geologi aktual (±1 m per segmen). Nilai lama per box tetap ada di kartu.
- Semua hasil AI bisa diedit: di kartu / tabel segmen, atau langsung di foto (**Edit segmen**: klik segmen, tarik batas, belah, gabung, tambah, hapus). Editan tidak ditimpa AI.
- Foto yang dianalisis versi sebelumnya belum punya segmen: jalankan **Analisis ulang** (isian yang sudah diedit tetap aman). Jawaban AI lebih panjang, jadi waktu per foto sedikit bertambah.

## 36. Geostatistik & validasi per lapisan (GC-Ex Drill Hole Ultimate 0.23.1)

Release v0.23.1 berisi installer **GC-Ex Drill Hole Ultimate 0.23.1** (nomor versi dinaikkan ke 0.23.1 karena 0.21.1–0.23.0 sudah dipakai Core-Ex; Block Model 0.20.3 dan Core-Ex tetap di rilisnya masing-masing).

- Panel **Geostatistik** → pilihan **Lapisan** (mis. *Saprolit (unfold)*): komposit lapisan dengan X, Y dipulihkan dari sesar post dan Z = posisi unfold (lapisan akumulasi 2D: nilai = tebal × kadar, Z = 0). Statistik, variogram (bidang datar, 0° = timur; downhole = vertikal), model dan KNA berlaku; uji estimasi grid dinonaktifkan.
- Tab Uji estimasi → **Simpan ke lapisan**: model variogram, pass, diskretisasi dan top-cut disimpan ke lapisan; tabel ③ Estimasi terisi (azimuth, range mayor / minor / vertikal dari variogram downhole, nugget) dan bertanda *variogram: Geostatistik*. Mengetik parameter manual menonaktifkan model tersimpan.
- Geomodeller Stratified-Laterite → **⑤ Validasi**: swath komposit vs blok (Easting, Northing, Z unfold), selisih rata-rata global, tabel grade-tonase DMT per cut-off.
- Tutorial diperbarui (bab Geomodeller Stratified-Laterite: Geostatistik per lapisan & Validasi).

## 39. Tampilan baru Core-Ex (0.23.2)

- Palet editorial: latar kertas abu muda, pita navy pada judul dialog, kotak biru baja, judul bagian biru tua, blok kode navy. Tema gelap ikut disesuaikan.
- Font: **Inter** (judul & teks) dan **JetBrains Mono** (angka, kode, label di foto), keduanya SIL OFL dan dibundel (tetap offline). Playfair Display & Courier Prime tidak lagi dipakai aplikasi (masih dipakai dokumen tutorial).
- Fungsi tidak berubah. Langkah berikutnya: antarmuka Core-Ex native PySide6 (Core-Ex 1.0.0).

## 40. Core-Ex Qt — tahap 1 (Core-Ex 0.23.3, kode sumber)

- Installer Core-Ex 0.23.3 **masih versi Electron** (isi sama dengan 0.23.2). Yang baru adalah kode sumber antarmuka native PySide6 di `app_core_qt/` (pratinjau pengembang, belum dipasang installer).
- Sudah ada: syarat penggunaan & aktivasi lisensi (kunci `GCEX1.` dan file `%APPDATA%\GC-Ex Lisensi\lisensi.json` sama, jadi lisensi lama tetap berlaku), tabel foto virtual yang bisa diedit, pratinjau foto (zoom, geser, putar, resolusi penuh), kartu interpretasi, AI lokal (Ollama dijalankan otomatis), Data bor, cari cepat Ctrl+K, export Excel, impor JSON.
- Tahap berikutnya: overlay berlapis, tanda half core / core loss, editor segmen, kalibrasi area core; lalu installer Core-Ex 1.0.0 berbasis PySide6.
- Menjalankan dari sumber (pengembang): `pip install PySide6-Essentials==6.8.1.1` lalu `python app_core_qt/main.py` (Python 3.11+).

## 41. Core-Ex Qt — tahap 2 & 3 (Core-Ex 0.23.4, kode sumber + uji build)

- Installer di Release masih Core-Ex versi Electron. Antarmuka Qt kini lengkap setara 0.23.x: overlay berlapis (assay, logging, segmen, kartu foto; warna & kelas bisa diubah), tanda half core / core loss (tarik di foto, recovery otomatis), editor segmen per baris (klik, geser batas kuning, belah, gabung, hapus, segmen baru), atur area core box, Data lab di kartu.
- CI membangun `Core-Ex-Qt-Setup-<versi>.exe` (PyInstaller + NSIS) sebagai artefak uji: exe diuji mandiri (backend, Pillow, Excel, font), gerbang lisensi, pasang & copot diam-diam.
- Installer Qt memasang ke folder yang sama (`%LOCALAPPDATA%\Programs\Core-Ex`) dan mencopot Core-Ex versi Electron lebih dulu. Lisensi, pengaturan dan folder `_GCEx_Core` tidak tersentuh.
- Qt for Python / Qt 6 berlisensi LGPL-3.0 (dinamis, file Qt bisa diganti); teks lisensinya ikut di folder `legal`.

## 42. Core-Ex 0.23.5

- Installer Core-Ex masih versi Electron (isi sama). Kode Core-Ex Qt: formulir tanda & segmen dipecah beberapa baris agar muat di panel sempit, daftar lapisan & pemetaan kolom tidak lagi bertumpuk saat diganti, pemeriksaan Ollama yang lama diabaikan.
- CI: ringkasan galat uji Core-Ex Qt dan galat pengemasan rilis ditulis sebagai anotasi run (mudah dibaca tanpa membuka log).

## 43. Core-Ex 0.23.6

- Installer Core-Ex di Release masih versi Electron (isi sama). Kode Core-Ex Qt kini memuat sisa perilaku versi Electron / HTML yang belum dipindahkan:
  - **Satu jendela**: membuka Core-Ex lagi (atau `Core-Ex.exe --folder D:\Foto_Core`) menampilkan jendela yang sudah terbuka dan membuka folder yang diminta di sana, bukan jendela kedua.
  - Jendela dibuka penuh (maximized) seperti versi Electron.
  - **Tampilan › Ukuran tampilan** 80 / 90 / 100 / 110 / 125 / 150 % (Ctrl+= perbesar, Ctrl+- perkecil, Ctrl+0 bawaan). Skala dipakai setelah Core-Ex dibuka ulang; Core-Ex menawarkan buka ulang langsung dan membuka lagi folder yang sedang dikerjakan.
  - **Tampilan › Layar penuh** (F11).
  - Sel Pelapukan dan Oksidasi di tabel memakai daftar pilihan (W1–W6, Unoxidized–Completely Oxidized) seperti kartu foto.
  - **Bantuan › Panduan AI lokal (Ollama)** (dirujuk pesan di dialog AI).
  - Perbaikan: pintasan Ctrl+O (Buka folder) terdaftar dua kali sehingga tidak berfungsi.
  - Perbaikan: hasil pemeriksaan latar (mis. cek Ollama) yang datang setelah jendela / dialog ditutup tidak lagi menimbulkan galat.
- CI: uji pytest-qt baru (satu jendela, ukuran tampilan, layar penuh, pintasan tidak bentrok, daftar pilihan di sel) dan uji exe: Core-Ex kedua diteruskan ke jendela pertama (peringatan bila gagal, tidak menghentikan rilis).

## 44. Core-Ex 0.23.7

Perbaikan rantai rilis (CI) — Release v0.23.3, v0.23.4 dan v0.23.5 tidak pernah terbit, padahal ketiga installer sudah berhasil dibangun:

- **Uji Core-Ex Qt tidak lagi membatalkan Release.** Langkah uji `pytest-qt` sudah dirancang untuk hanya memberi peringatan bila uji gagal, tetapi GitHub menambahkan `exit $LASTEXITCODE` di akhir setiap skrip PowerShell. Karena kode keluar pytest masih bukan 0, langkah itu tetap dianggap gagal, job berhenti, dan langkah **Kemas & terbitkan GitHub Release** dilewati. Sekarang langkah tersebut ditutup dengan `exit 0`; hasil uji tetap terlihat sebagai anotasi `::warning::`. (Penyebab v0.23.4 & v0.23.5.)
- **Unggah Release lebih tahan gangguan.** `gh release create` kini dicoba sampai 3×; bila release sudah terbentuk tetapi sebagian file gagal terunggah, file dilengkapi dengan `gh release upload --clobber`. Setelah selesai, daftar file di Release dibandingkan dengan folder `rilis/` dan kekurangannya dilaporkan sebagai galat. Dulu satu kegagalan unggah langsung menghentikan langkah ini tanpa pesan apa pun. (Penyebab v0.23.3.)

Perbaikan Core-Ex Qt:

- Timer awal (cek Ollama & status AI) kini milik jendela, sehingga ikut berhenti saat jendela ditutup — dulu `QTimer.singleShot` lepas masih menyala setelah jendela hilang.
- Status AI lokal dan jajak pendapat progres AI memeriksa dulu apakah widgetnya masih ada, sehingga galat `Internal C++ object (QPushButton) already deleted` tidak muncul lagi di event loop Qt.
- Uji `pytest-qt`: setiap uji ditutup dengan menguras tugas latar, jadi hasil tugas uji sebelumnya tidak lagi menggagalkan tahap persiapan uji berikutnya (dulu uji editor segmen & tanda interval error di tahap setup).

## 45. Core-Ex 0.23.8

- Installer Core-Ex di Release masih versi Electron. Perbaikan Core-Ex Qt (melengkapi 0.23.7): penjadwalan tata letak panel, hasil cek Ollama di dialog AI, fokus formulir tanda, pesan sementara dan menu cari kini terikat ke jendelanya, sehingga tidak lagi menimbulkan galat `Internal C++ object (QWidget) already deleted` bila jendela sudah ditutup lebih dulu (mis. saat buka ulang Core-Ex). Hasil tugas latar yang datang setelah jendela ditutup diabaikan dan dicatat di log.
- CI: uji satu jendela mengirim pesan dari thread lain (named pipe Windows menunggu event loop), ringkasan galat uji Core-Ex Qt kini menyertakan lokasi file.

## 46. Core-Ex 0.23.9

**Penyebab sebenarnya Release v0.23.3–v0.23.7 tidak terbit: izin, bukan kode.** Setelah perbaikan 0.23.7, build berhasil sampai langkah Release, dan pesan galatnya akhirnya terlihat:

```
gh HTTP 403: Resource not accessible by integration
    https://api.github.com/repos/.../releases
```

Artinya `GITHUB_TOKEN` yang dipakai CI tidak diberi izin menulis, sehingga `gh release create` ditolak. Workflow sendiri sudah meminta `permissions: contents: write`, jadi batasnya ada di **pengaturan repo**:

> GitHub → repo ini → **Settings › Actions › General › Workflow permissions** → pilih **Read and write permissions** → Save.

Setelah itu jalankan ulang build terakhir (tab **Actions** → run terakhir → **Re-run all jobs**) — Release akan terbit tanpa perlu push baru. Repo baru di GitHub secara bawaan memakai izin *read-only*, dan itulah yang terjadi sejak v0.23.3.

Perubahan di versi ini:

- CI: galat 403 dikenali dan dilaporkan dengan petunjuk pengaturan di atas, serta tidak dicoba ulang 3× (percuma, hanya memperlambat).
- Core-Ex Qt (satu jendela): bila data dan pemutusan soket tiba bersamaan, `readyRead` bisa terlewat sehingga folder dari Core-Ex kedua tidak diteruskan. Sekarang sisa buffer juga dibaca saat soket terputus, pengiriman memproses event loop lebih dulu, dan pesan dijaga agar tidak dikirim dua kali. (Penyebab uji `test_single_instance_forwards_folder` gagal di Windows.)
- Catatan: kuota penyimpanan artefak GitHub Actions penuh, jadi installer cadangan di tab Actions sementara tidak terunggah. Kuota dihitung ulang tiap 6–12 jam; setelah Release bisa terbit lagi, installer tetap tersedia dari Release.

## 47. Core-Ex 0.23.10

- CI: perbaikan langkah **Core-Ex Qt - pasang PySide6 & uji pytest-qt**. Pola ringkasan galat yang ditambahkan di 0.23.8 memakai `\"` di dalam string PowerShell berkutip ganda; PowerShell tidak mengenal `\"` sebagai escape, sehingga skrip langkah itu gagal dibaca dan langkah selalu gagal (exit 1) sebelum pytest berjalan. Pola kini memakai kutip tunggal. Isi aplikasi sama dengan 0.23.9.

## 48. Core-Ex 0.23.11

- Uji Core-Ex Qt: uji satu jendela kini mengirim pesan dari proses Python terpisah, persis seperti Core-Ex kedua yang dibuka pengguna. Di build Windows 0.23.10 uji ini gagal karena pengirim berupa thread di proses yang sama, padahal uji exe sungguhan (Core-Ex kedua diteruskan ke jendela pertama) sudah lulus. Isi aplikasi sama dengan 0.23.10.
## 49. GC-Ex Drill Hole Ultimate 0.24.0

**Klasifikasi keyakinan sumber daya di Reporting BM.** Di bagian ① Atribut menu *Reporting BM* ada kotak baru **Klasifikasi keyakinan (Measured / Indicated / Inferred)**. Kelas diusulkan dari atribut hasil *Model Estimation* yang sudah ada:

| Masukan | Arti |
|---|---|
| `est_pass` | pass pencarian sampel (1 = radius penuh / data rapat, 2–3 = radius diperbesar) |
| `est_nsamp` | jumlah komposit yang dipakai blok itu |
| `est_sor` / `est_ke` | slope of regression atau kriging efficiency (bisa dipilih) |

Aturan bawaan, semuanya bisa diubah di panel:

- **Measured** — pass ≤ 1, komposit ≥ 12, SoR ≥ 0,75
- **Indicated** — pass ≤ 2, komposit ≥ 7, SoR ≥ 0,45
- **Inferred** — blok terestimasi lainnya
- **Belum terklasifikasi** — blok tanpa estimasi

Hasilnya ditulis sebagai atribut **kategori** `klasifikasi`, jadi seluruh mesin Reporting yang sudah ada langsung bisa dipakai: pilih grup **Per atribut kategori → klasifikasi** untuk tabel tonase & kadar per kelas, export CSV ikut, dan atribut ini juga bisa diwarnai di tampilan 3D. Di bagian ③ Hasil muncul **kurva grade × tonase per kelas keyakinan** (batang bertumpuk = tonase kelas, garis putus-putus = kadar rata-rata kelas). Bila estimasi dijalankan ulang, klasifikasi ikut dihitung ulang.

Bila atribut `est_nsamp` atau `est_sor` tidak ada (block model dari luar GC-Ex), syaratnya diabaikan dan panel memberi tahu.

> ⚠ Ambang di panel adalah **usulan geostatistik yang dapat diulang, bukan keputusan klasifikasi**. Penetapan Measured / Indicated / Inferred tetap wewenang **Competent Person** sesuai KCMI / JORC, yang juga menimbang spasi bor, kemenerusan geologi, QAQC dan kelayakan penambangan. Spasi bor dan jumlah bor berbeda per blok belum direkam estimasi, jadi belum bisa dipakai sebagai syarat otomatis.

## 50. GC-Ex Block Model & Drill Hole Ultimate 0.24.1

**Topografi & orthofoto resolusi sangat tinggi tanpa mengorbankan performa.** Berlaku di kedua aplikasi.

Yang membatasi sebelumnya:

- Orthofoto digambar sebagai mesh 3D berwarna per-titik dengan resolusi **tetap** dari kotak *Resolusi (m)*, dan dibatasi 300.000 titik untuk **seluruh area**. Zoom masuk tidak menambah detail, zoom keluar menghitung titik yang tidak terlihat. Warna diambil satu piksel (point sample) sehingga berkerlip saat gambar dikecilkan.
- Peta (Mapping) memakai satu JPEG seluruh ortho yang dipaksa maksimum 3.000 px sisi panjang — ortho 8.000 px pun hanya tampil 2.666 px, jadi zoom dekat tampak buram.
- Topografi digambar dari desimasi *ambil tiap titik ke-n* ke 15.000 titik, dihitung **sekali** saat proyek dibuka: zoom masuk tetap kasar.
- `topoZ()` menghitung IDW ulang setiap dipanggil — dan dipanggil ~300.000 kali setiap kali ortho di-drape ke topografi.

Yang berubah:

1. **Piramida LOD orthofoto.** Level 0 = piksel asli, tiap level berikutnya rata-rata 2 × 2. Warna diambil dari level yang texel-nya sepadan dengan resolusi mesh, jadi rata-rata area (anti-alias) dan pembacaannya lebih murah. Tambahan memori = ⅓ dari piksel dasar (ortho 8.000 × 8.000: 183 MB → +61 MB, dibangun sekali ±0,3 detik).
2. **Resolusi *dan* luas mesh mengikuti tampilan.** Zoom masuk otomatis makin detail sampai batas piksel asli, dengan jumlah titik tetap di bawah anggaran. Kotak *Resolusi (m)* kini menjadi batas paling halus, bukan resolusi tetap.
3. **Peta 2D memakai gambar asli.** Ortho dipotong sesuai tampilan dan dikirim setajam layar (maksimum 4.096 px).
4. **Desimasi topografi per sel**, dihitung dari seluruh data **di dalam tampilan** — sebaran merata dan detail penuh saat zoom masuk.
5. **Grid elevasi untuk tampilan**, dibaca bilinear O(1).

Hasil ukur (ortho sintetis 8.000 × 8.000 px @ 5 cm, topografi 200.000 titik, Chromium headless):

| | Sebelum | Sesudah |
|---|---|---|
| Mesh ortho, tampilan 400 m | 1 m/titik · 160.000 titik · 592 ms | 0,91 m/titik · 193.000 titik · 525 ms |
| Mesh ortho, zoom 40 m | 1 m/titik · 160.000 titik · 592 ms | **0,1 m/titik** · 215.000 titik · 136 ms |
| Mesh ortho, zoom 10 m | 1 m/titik · 160.000 titik · 592 ms | **0,1 m/titik** · 13.700 titik · **3 ms** |
| Gambar ortho Peta 2D, zoom 10 m | 2.666 × 2.666 px @ 0,15 m · 255 ms · 3,1 MB | **220 × 220 px @ 0,05 m** · 6 ms · 9 KB |
| Gambar ortho Peta 2D, zoom keluar | 2.666 × 2.666 px · 255 ms | 1.454 × 1.454 px · 89 ms |
| Titik topografi di jendela 10 m (anggaran 15.000) | 15 | **172** |
| 200.000 pembacaan elevasi | 512 ms | **14 ms** |
| Warna ortho pada mesh kasar | titik tunggal (berkerlip) | rata-rata area (anti-alias) |

> **Hasil laporan tidak berubah.** Grid elevasi dipakai **hanya untuk tampilan** (menempelkan warna ortho ke topografi). Semua perhitungan *Reporting BM*, estimasi dan validasi tetap memanggil `topoZ()` asli. Grid itu pun dibangun dengan memanggil `topoZ()` asli pada simpul-simpulnya: pada uji 300 titik acak, selisihnya rata-rata **4 mm** dan maksimum **3,8 cm** pada permukaan dengan relief 30 m.

Catatan pemakaian: saat zoom/geser, tampilan disegarkan ±0,3 detik setelah gerakan berhenti (bukan tiap frame), dan mesh dibuat sedikit lebih luas dari layar supaya geseran kecil tidak menyisakan tepi kosong. Klik ganda / autoscale mengembalikan tampilan ke seluruh area.

## 51. GC-Ex Block Model & Drill Hole Ultimate 0.24.2

**Data latihan simulasi diganti, dan tutorial tambahan 0.24 ditambahkan.**

Data latihan lama (±33 bor, ±2.500 baris assay, 2 vein) diganti endapan emas **epitermal low-sulphidation** terkontrol zona geser yang jauh lebih besar dan dibuat taat kaidah geologi, supaya setiap latihan punya jawaban yang diketahui:

| Unsur model | Isi |
|---|---|
| Array vein | **4 lensa sigmoidal en-echelon** (right-stepping) + 1 splay hangingwall |
| Ore shoot | **pitch 55°** dari garis strike di dalam bidang vein, sama untuk semua lensa |
| Zona dilatan | tebal **dan** kadar maksimum dikontrol satu struktur yang sama (jog dilatan = ore shoot) |
| Zonasi vertikal | paleo-muka air tanah RL 250 m: zona didih bertekstur colloform, Ag/Au naik ke atas (4,3 → 19), Pb–Zn naik ke bawah, As penanda vein |
| Pelapukan | tudung tercuci 15 m teratas, selimut supergen tepat di atas muka air tanah, transisi, batuan segar |
| Sesar | pasca-mineralisasi strike 110°/dip 65°, offset 12 m, panjang ±150 m — hanya memotong lensa 2 & 3 |
| Efek nugget | 5% sampel Au dilonjakkan → CV Au 1,9 (perlu top-cut), Ag jauh lebih jinak |

Ukuran: **610 bor resource + 459 bor grade control**, ±98.000 baris assay dengan Au, Ag, Cu, Pb, Zn, S, As, SG; logging Lith, Alt, Ox, Texture, RQD, Recovery. Ditambah subset latihan cepat, dua tahap data upsert, vein bercabang + block model 2,5 m, database dengan 9 kesalahan sengaja, QAQC (CRM/duplikat/blank), struktur & pick-up, dua versi topografi, block model kosong, wireframe, dan `JAWABAN_MODEL.txt` sebagai kunci jawaban. `make_sim_data.py --besar` menghasilkan ±300.000 baris assay untuk uji beban.

Verifikasi (dari data yang dihasilkan, bukan dari model): kipas variogram GT per bor menemukan kembali **pitch 55°**; bidang terbaik seluruh intersep memberi **dip ~66°, dip-azimuth ~139°** (bidang acuan 70°/135° — bedanya karena vein sigmoidal, dan ini dijelaskan di tutorial); kadar Au memuncak di **RL 250 m** bersamaan tekstur colloform; CRM bias ~0% (sd 3,7–5,6%), duplikat HARD rata ~8%, blank < 0,02 g/t.

**Tutorial Tambahan GC-Ex 0.24** (`GCEx_Tutorial_0.24_Tambahan.pdf`, 12 halaman) ikut di `_1_Dokumen.zip`: model data latihan & daftar berkas, latihan terpandu menemukan kembali geometri endapan (orientasi, pitch, pemulihan sesar, zonasi vertikal, top-cut), klasifikasi keyakinan sumber daya, topografi & orthofoto resolusi tinggi, serta daftar bagian tutorial lama yang perlu disesuaikan. Semua gambarnya **dihitung dari model dan berkas data**, bukan tangkapan layar, sehingga dapat dibangun ulang di mesin mana pun: `python docs/tutorial-gcex/src/build_tutorial_024.py`.

> Catatan: dua tutorial bergambar yang lama (*Modelling & Estimasi*, *Block Model*) dibangun dari tangkapan layar aplikasi dan **belum** diperbarui ke data baru — langkah kerjanya tetap berlaku, yang berubah hanya nama domain dan angka di layar (daftarnya ada di bab 5 tutorial tambahan). Membangun ulang keduanya memerlukan mesin tempat GC-Ex dapat membuka folder proyek; skripnya kini memberi pesan jelas bila tangkapan layar belum tersedia.

## 52. Core-Ex 0.24.3

- Installer uji **Core-Ex versi Qt** (`Core-Ex-Qt-Setup-<versi>.exe`) kini diterbitkan setiap build `main` ke pre-release privat **core-ex-qt-uji** di halaman Releases (hanya versi terbaru yang disimpan). Sebelumnya installer ini hanya tersedia sebagai artifact Actions, yang tertolak saat kuota penyimpanan Actions akun penuh ("Artifact storage quota has been hit").
- Pre-release ini **bukan rilis resmi**: Release `v<versi>` tetap memuat Core-Ex versi Electron sampai Core-Ex 1.0.0. Versi Core-Ex dinaikkan ke 0.24.3 agar menjadi versi tertinggi dan Release ini terbit; isi aplikasi Core-Ex sama dengan 0.23.11.

## 52. GC-Ex Block Model & Drill Hole Ultimate 0.24.4

### Kerapatan bor direkam saat estimasi

Klasifikasi 0.24.2 hanya bisa memakai **jumlah komposit** (`est_nsamp`). Itu bukan ukuran kerapatan bor: 20 komposit dari **satu** lubang bor sangat berbeda artinya dengan 20 komposit dari enam lubang. Sekarang *Model Estimation* merekam tiga atribut baru per blok, dihitung dari komposit yang benar-benar dipakai kriging:

| Atribut | Arti |
|---|---|
| `est_nhole` | jumlah **lubang bor berbeda** yang komposit-nya dipakai blok itu |
| `est_dmin` | jarak (m) dari pusat blok ke komposit terdekat yang dipakai |
| `est_spasi` | perkiraan **spasi bor setempat** (m): tiap lubang diwakili komposit terdekatnya ke blok, lalu dirata-ratakan jarak mendatar tiap lubang ke lubang terdekat lainnya. Bernilai −99 bila lubang yang dipakai kurang dari dua |

Ketiganya ikut ke block model, tampilan 3D, reporting dan export `.mdl` seperti atribut estimasi lainnya.

### Klasifikasi memakai kerapatan bor

Aturan bawaan di *Reporting BM › Klasifikasi keyakinan* sekarang:

- **Measured** — pass ≤ 1, komposit ≥ 12, SoR ≥ 0,75, **bor berbeda ≥ 3**, **spasi bor ≤ 25 m**
- **Indicated** — pass ≤ 2, komposit ≥ 7, SoR ≥ 0,45, **bor berbeda ≥ 2**, **spasi bor ≤ 50 m**
- **Inferred** — blok terestimasi lainnya
- **Belum terklasifikasi** — blok tanpa estimasi

Semua ambang tetap bisa diubah di panel. Contoh uji: blok dengan 20 komposit tetapi hanya dari **satu** lubang bor dulu jatuh ke Measured, sekarang menjadi **Inferred**. Begitu pula blok dengan tiga lubang bor tetapi spasi 80 m.

> Block model yang diestimasi dengan versi sebelum 0.24.4 belum punya `est_nhole` / `est_spasi`. Panel memberi tahu hal ini, kedua syarat itu diabaikan, dan hasilnya sama seperti 0.24.2. Jalankan ulang *Model Estimation* agar kerapatan bor ikut terekam.

Penetapan kelas tetap wewenang **Competent Person** (KCMI / JORC), yang juga menimbang hal-hal yang tidak terbaca dari angka: kemenerusan geologi antar bor, keyakinan pada model domain, kualitas QAQC, ketersediaan data densitas, dan kelayakan penambangan.

### Tutorial PDF dibangun otomatis di CI

Build Windows sekarang membangun ulang tutorial tiap rilis, sehingga isinya selalu mengikuti aplikasi dan data latihan terbaru:

1. **Data latihan** dibuat ulang (`make_sim_data.py`, `make_sim_laterit.py`).
2. **Tutorial Tambahan 0.24** dibangun (`build_tutorial_024.py`). Tidak memerlukan tangkapan layar, jadi kegagalannya **menggagalkan** build — ini harus selalu berhasil.
3. **Dua tutorial bergambar** dibangun dari tangkapan layar aplikasi (`tutorial_shots.py` → `build_tutorial.py`, `tutorial_bm_shots.py` → `build_tutorial_bm.py`). Langkah ini memerlukan Chromium yang dapat membuka folder proyek lewat File System Access API — itulah sebabnya hanya bisa di runner Windows, bukan kontainer Linux. Bila gagal, build **tetap lanjut** dengan peringatan dan PDF lama di repo yang dipakai, supaya rilis tidak tertahan.
4. Daftar PDF beserta ukuran dan waktu buatnya ditulis sebagai `::notice::` di ringkasan run, jadi Anda bisa melihat mana yang benar-benar diperbarui.

## 53. GC-Ex Block Model & Drill Hole Ultimate 0.24.5

Perbaikan pembuatan tutorial bergambar di CI, dari hasil run pertama 0.24.4.

Kabar baiknya: **tangkapan layar aplikasi memang berhasil di runner Windows** (tiga gambar pertama jadi), sehingga dugaan bahwa kegagalan sebelumnya adalah batasan kontainer Linux terbukti benar.

Kegagalannya ada di tempat yang tidak terduga: skrip berhenti di dalam `print()`, bukan di aplikasinya. Konsol Windows bawaannya memakai cp1252, sedangkan teks panel GC-Ex yang dicatat sebagai angka hasil memuat karakter di luar cp1252 (misalnya `≥` dan titik tengah) — sehingga `UnicodeEncodeError` menghentikan seluruh tahap tangkapan layar.

Dua lapis perbaikan:

1. Ketiga langkah tutorial di CI dijalankan dengan `PYTHONIOENCODING=utf-8` dan `PYTHONUTF8=1`.
2. Fungsi `note()` di ketiga skrip tangkapan layar kini menangkap kegagalan pencetakan: angkanya **tetap tercatat** ke `notes.json`, hanya barisnya di log yang diganti keterangan singkat. Pembuatan tutorial tidak boleh gagal hanya karena konsol tidak sanggup mencetak satu karakter.

Ringkasan galat di CI juga diperpanjang dari 14 menjadi 30 baris terakhir, supaya traceback berikutnya terbaca utuh tanpa membuka log.

## 54. GC-Ex Block Model & Drill Hole Ultimate 0.24.6

Run 0.24.5 membuktikan perbaikan UTF-8 berhasil (galat `UnicodeEncodeError` hilang), tetapi tahap tangkapan layar berhenti di tempat berikutnya — dan kali ini penyebabnya memang kekeliruan saat data latihan diganti di 0.24.2:

- Skrip tangkapan layar masih memuat `QV_Utama_Leapfrog.obj`, padahal berkas itu sudah berganti nama menjadi `QV_Lensa2_Leapfrog.obj`.
- Domain yang dibuat skrip tidak lagi cocok dengan nama domain yang dipakai narasi PDF (104 acuan).

Keduanya diselaraskan. Tutorial bergambar sekarang menelusuri **lensa 2 beserta splay hangingwall-nya** (`QV_Lensa2` + `QV_Splay_HW`) — pasangan yang menceritakan hal yang sama seperti versi lama (bor dari sisi hanging wall menembus splay dulu, baru vein utama), tetapi memakai domain yang benar-benar ada di data baru. Bagian "Geometri yang perlu diingat" diperbarui: endapan berupa array 4 lensa en-echelon, ore shoot ber-pitch 55° yang mengontrol tebal dan kadar sekaligus, bidang rata-rata data ±66° (bukan 70° karena permukaan vein sigmoidal), paleo-muka air tanah RL 250 m, dan rujukan ke kunci jawaban.

Lensa lain dikerjakan dengan cara yang persis sama, jadi langkah-langkah tutorial tidak berubah.

## 55. GC-Ex Block Model & Drill Hole Ultimate 0.24.7

Run 0.24.6 gagal **sebelum** sampai ke langkah tutorial: langkah *Core-Ex Qt — bangun (PyInstaller)* berhenti, sehingga sembilan langkah sesudahnya termasuk Release ikut dilewati dan v0.24.6 tidak terbit.

Penyebabnya bukan kode: di tengah langkah itu ada pengambilan teks lisensi GNU (LGPL-3.0 dan GPL-3.0) langsung dari `gnu.org` — **setiap build**, tanpa salinan di repo. Satu gangguan jaringan menggagalkan seluruh rilis.

Dua perbaikan, keduanya mengikuti prinsip yang sama dengan perbaikan 0.23.7: langkah yang tidak menentukan isi rilis tidak boleh menahan rilis.

1. **Pengambilan teks lisensi tahan gangguan.** Dicoba sampai 3× dengan jeda; bila tetap gagal, salinannya diambil dari `_3_Lisensi-dan-Tentang.zip` rilis terakhir (GitHub selalu terjangkau dari runner); baru setelah keduanya gagal langkah itu menyerah. Teksnya hanya disalin, tidak pernah diubah.
2. **Kegagalan Core-Ex Qt tidak menahan Release GC-Ex.** Core-Ex Qt masih tahap percobaan — installer yang terbit masih versi Electron — jadi kegagalan build Qt kini ditandai sebagai peringatan, langkah Qt berikutnya melewati diri, dan rilis GC-Ex tetap berjalan.

Karena run 0.24.6 berhenti di langkah 22, perbaikan tutorial di versi itu (`QV_Lensa2` + `QV_Splay_HW`, wireframe `QV_Lensa2_Leapfrog.obj`) **belum pernah diuji**; pengujiannya ikut di rilis ini.

## 56. GC-Ex Block Model & Drill Hole Ultimate 0.24.8

Dengan rilis 0.24.7 rantai rilis sudah tahan gangguan, dan tangkapan layar tutorial berhasil sampai **gambar ke-29** (sebelumnya berhenti di ke-3): import wireframe, flagging dari wireframe, dan pembangunan solid semuanya berjalan dengan domain `QV_Lensa2` + `QV_Splay_HW`.

Berhentinya di bab *upsert*, karena skrip mematok jumlah bor dari data latihan lama:

```js
collars.length===37     // 33 bor + 4 infill — data lama
```

Data sekarang 610 bor, jadi penantian itu tidak pernah terpenuhi dan berhenti setelah 3 menit. Dua tempat diperbaiki (upsert tahap 1 dan 2): jumlah bor dicatat sebelum upsert, lalu ditunggu **bertambah** — tidak lagi bergantung pada angka tetap, sehingga ukuran data latihan boleh berubah kapan saja tanpa merusak tutorial.

Keterangan berkas di narasi juga disesuaikan dengan isi data yang berlaku (jumlah lubang infill, titik struktur, dan titik pick-up dihitung dari berkasnya).

Penangkapan galat di CI diperbaiki: GitHub hanya menampilkan 10 anotasi peringatan per langkah, dan jatah itu sebelumnya habis oleh jejak Playwright sehingga penyebab sebenarnya terpotong. Sekarang yang ditampilkan adalah baris pengecualian terakhir beserta lokasi berkas/barisnya, dan 60 baris log terakhir ditulis ke ringkasan run yang tidak dibatasi.

## 57. Core-Ex 0.25.0 — ruang kerja Singkapan (Core-Ex versi Qt)

- Fitur baru hanya di **Core-Ex versi Qt** (installer uji di pre-release `core-ex-qt-uji`); Core-Ex Electron di Release tidak berubah.
- **Singkapan** (tombol di bilah atas, di samping Core box): foto singkapan / trenching dimasukkan satu per satu dan disalin ke `_GCEx_Core/singkapan`; deskripsi AI lokal (jenis foto wall / floor, litologi, alterasi, pelapukan ISRM, oksidasi / gossan, vein, struktur, GSI, spasi kekar, zona) dengan isian yang diedit tidak ditimpa AI; digitasi garis / poligon / label dengan snap, geser / sisip / hapus titik, belah & gabung garis; kadar Au / Ag / SxS manual; garis skala (panjang m); pustaka jenis fitur dengan warna & nomor string Surpac yang bisa diubah per proyek.
- **Infografis** 3 template (Trenching dengan kadar, Mapping dinding tanpa kadar, Overlay saja), kotak kadar & komposit bisa ditarik, posisi legenda, bar skala, ekspor PNG / PDF resolusi penuh.
- Panduan: PANDUAN_CORE bagian 6c. Tahap berikutnya: georeferensi dari titik survey (2, 3, ≥4 titik), alat ukur dan ekspor STR / DXF.

## 58. Core-Ex 0.26.0 — Singkapan: georeferensi, ukuran 3D, ekspor STR / DXF (Core-Ex versi Qt)

- Fitur baru hanya di **Core-Ex versi Qt** (installer uji di pre-release `core-ex-qt-uji`); Core-Ex Electron di Release tidak berubah.
- Tab **Georef** di ruang kerja Singkapan: klik tanda Pylox / pita di foto lalu isi E, N, RL hasil pick-up survey (atau tempel dari Excel). 2 titik = similaritas, 3 titik = bidang + affine, ≥4 titik = bidang terbaik + koreksi perspektif; galat per titik & RMS (5+ titik), orientasi bidang, peringatan susunan titik.
- Ukuran 3D per fitur (panjang, apparent dip, luas / keliling) di form fitur; bar skala infografis memakai skala georef bila tidak ada garis skala.
- Ekspor **STR Surpac** (Y, X, Z; nomor string per jenis; D1 jenis, D2 nama, D3 foto, kadar) dan **DXF R12** (layer per jenis, 3D polyline) dalam E, N, RL, per foto atau semua foto.
- Panduan: PANDUAN_CORE bagian 6c langkah 5–6.

## 59. Core-Ex 0.26.1 — perbaikan CI rilis

- Langkah pembuatan tutorial bergambar di CI gagal di-parse PowerShell sejak 0.24.8, sehingga Release v0.24.8 dan v0.25.0 tidak terbit. Sudah diperbaiki; isi aplikasi sama dengan 0.26.0.

## 60. Core-Ex 0.27.0 — Singkapan: delineasi otomatis (Core-Ex versi Qt)

- Fitur baru hanya di **Core-Ex versi Qt** (installer uji di pre-release `core-ex-qt-uji`); Core-Ex Electron di Release tidak berubah.
- Tab Fitur › **Usulan otomatis**: *Zona warna* (tanpa AI, beberapa detik) membagi foto menjadi zona oksida / gossan vs batuan segar; *AI vision* (Ollama) mengusulkan kontak, sesar, kekar, vein dan zona beserta jenisnya.
- Usulan berupa draf titik-titik yang tidak ikut legenda / ekspor sampai diterima: edit, lalu **✓ Terima usulan** / Simpan, atau **Terima semua** / **Buang semua**.
- Panduan: PANDUAN_CORE bagian 6c langkah 3.

## 61. Core-Ex 0.28.0 — Singkapan: kadar multi-unsur per interval (Core-Ex versi Qt)

- Fitur baru hanya di **Core-Ex versi Qt** (installer uji di pre-release `core-ex-qt-uji`); Core-Ex Electron di Release tidak berubah.
- Tabel **Sampel / kadar** di form fitur menggantikan kolom tetap Au / Ag / SxS: garis channel / trenching dibagi interval *dari–ke* (m), zona memakai satu sampel; isi manual atau tempel dari Excel (judul kolom dicocokkan menurut unsur), nilai `<0.01` diterima. Data lama Au / Ag / SxS terbaca otomatis.
- Infografis Trenching: kotak kadar per interval (bisa ditarik), tanda batas interval, warna segmen menurut kelas kadar satu unsur + legenda kelas, komposit otomatis tertimbang panjang.
- **Atur unsur & kelas warna** (satuan, desimal, tampil, batas kelas) dan **⇩ Tabel sampel (CSV)**. Ekspor STR / DXF: satu segmen per interval dengan Sample ID & kadar semua unsur.
- Panduan: PANDUAN_CORE bagian 6c langkah 3–4.

## 62. Core-Ex 0.29.0 — Singkapan: simbol & label gaya peta (Core-Ex versi Qt)

- Fitur baru hanya di **Core-Ex versi Qt** (installer uji di pre-release `core-ex-qt-uji`).
- Jenis fitur baru: **Strike / dip terukur** (simbol T + N100/80, ikut STR) dan **Label zona (rentang)** (kurung + garis penunjuk + kotak putih). Label biasa bisa memakai kotak putih.
- **Kompas** di infografis: otomatis dari georef (dinding = arah kamera menghadap, lantai = panah utara) atau manual.
- Kotak kadar interval ditempatkan di atas garis dengan dua ketinggian bergantian.

## 63. Core-Ex 0.30.0 — Singkapan: channel / trenching ke database bor (Core-Ex versi Qt)

- Fitur baru hanya di **Core-Ex versi Qt** (installer uji di pre-release `core-ex-qt-uji`).
- Tab Georef › **⇩ Database channel**: 4 CSV Collar · Survey · Assay · Geologi dari semua garis Channel sampel yang tergeoreferensi. Collar di ujung kiri foto, EOH di kanan, **dip 0**, azimuth dari georef; geologi dari zona yang dipotong garis, label zona & struktur; pilihan nilai di bawah batas deteksi.
- Garis channel (dan garis berinterval) kini selalu disimpan kiri → kanan; *dari–ke* diukur dari ujung kiri.
- Panduan: PANDUAN_CORE bagian 6c langkah 6.

## 64. DB-Ex 0.31.0 — Core-Ex berganti nama menjadi DB-Ex; gaya infografis editorial

- **Core-Ex sekarang bernama DB-Ex** (*Database Excellence*). Arah ke depan: selain foto core box & singkapan, DB-Ex akan membaca formulir lapangan tulisan tangan dengan AI vision dan mengubahnya ke Excel / SQL / CSV. GC-Ex (Block Model & Drillhole) tidak berubah.
- Installer Release: `DB-Ex-Setup-<versi>.exe` (Electron); installer uji Qt: `DB-Ex-Qt-Setup-<versi>.exe` di pre-release `core-ex-qt-uji` (nama tag tetap).
- Pengaturan, log & cache dipindah otomatis sekali dari `%APPDATA%\Core-Ex` ke `%APPDATA%\DB-Ex` saat DB-Ex pertama dibuka. Lisensi (`%APPDATA%\GC-Ex Lisensi`) dan kunci lisensi tidak berubah. Installer DB-Ex Qt mencopot Core-Ex lama (Electron maupun Qt) beserta pintasannya; data proyek (`_GCEx_Core` di folder foto) tidak tersentuh.
- **Gaya infografis "Editorial dokumenter alam"** (bawaan): kicker kapital oker + judul serif di atas gradasi gelap, panel data gelap transparan dengan batang warna kelas, garis penunjuk putih tipis bertitik, caption serif miring & kredit foto di kaki, legenda / bar skala / kompas minimalis. Gaya *Klasik* (pita judul kuning / navy, kotak kuning) tetap bisa dipilih di tab Infografis. Kolom baru: Kicker, Caption, Kredit foto.
- **Infografis foto core box** (baru): File › Ekspor infografis foto (PNG / PDF), Ctrl+E — plate editorial: foto utuh + overlay lapisan yang aktif, judul Hole · dari–ke, caption logging (litologi, alterasi, pelapukan, recovery, RQD, catatan), legenda lapisan.
- Tutorial PDF DB-Ex masih memuat tangkapan layar bernama lama sampai dibuat ulang.

## 65. DB-Ex 0.31.1 — tutorial PDF DB-Ex dibuat ulang

- `DB-Ex_Tutorial_Penggunaan.pdf` (di `_1_Dokumen.zip`) dibuat ulang: semua tangkapan layar memakai nama DB-Ex, judul sampul "Tutorial DB-Ex". Isi latihan tidak berubah.

## 66. DB-Ex 0.31.2 — persiapan pustaka visi (pengembang)

- Tidak ada perubahan aplikasi. Workflow manual untuk pengembang: *Dev models* (memeriksa lisensi & isi model ONNX Segment Anything dan Depth Anything V2 Small) dan *Dev wheels* (OpenCV, Shapely, ONNX Runtime) sebagai persiapan fitur SAM, Depth Anything dan tempel ke topografi.

## 67. DB-Ex 0.32.0 — SAM, Depth Anything & topografi opsional (DB-Ex versi Qt)

- Fitur baru hanya di **DB-Ex versi Qt** (installer uji `DB-Ex-Qt-Setup-<versi>.exe` di pre-release `core-ex-qt-uji`). Tidak perlu memasang apa pun: **OpenCV, Shapely, ONNX Runtime** serta model **SlimSAM-77** (Segment Anything) dan **Depth Anything V2 Small** (keduanya Apache-2.0) sudah di dalam installer; semuanya berjalan offline di CPU. Installer menjadi lebih besar (± 150–250 MB).
- **✦ SAM** di bilah atas Singkapan: klik di dalam zona → batas zona otomatis; Shift+klik = bukan zona; Tab = ukuran (kecil / sedang / besar); Enter = simpan; Esc = selesai.
- **Topografi / DTM as-built (opsional)** di tab Georef: impor Surpac .dtm + .str beserta tanggal survey; *Cek terhadap foto ini* melaporkan cakupan DTM, jarak titik survey ke DTM dan peringatan bila foto lebih baru dari topografi.
- **Ekspor** STR / DXF / tabel sampel / database channel menanyakan sumber koordinat; **bawaan: georef** (bidang foto dari titik survey). *Tempel ke topografi* hanya bila dipilih; area di luar DTM opsional diisi Depth Anything yang dikalibrasi ke meter. Collar memuat kolom COORD_SRC (GEOREF / TOPO:<nama>).

## 68. DB-Ex 0.33.0 — Borang: borang lapangan tulisan tangan (DB-Ex versi Qt)

- Fitur baru hanya di **DB-Ex versi Qt** (installer uji `DB-Ex-Qt-Setup-<versi>.exe` di pre-release `core-ex-qt-uji`). Pembaca PDF (**pypdfium2 / PDFium**, Apache-2.0 / BSD-3) ikut installer; AI memakai Ollama lokal yang sama (tanpa internet).
- Tombol **Borang** di bilah atas: tambah foto / scan / PDF borang **Ore Spotter / Truck Count** atau **RC Drill / Chiptray Log**, **✦ Baca dengan AI**, periksa berdampingan (kuning = AI ragu, merah = galat validasi), centang ✓ per baris (Ctrl+Enter), pivot, lalu ekspor ke **Excel, CSV, SQLite (.db) atau MS Access (.accdb)**. Langkah lengkap: *Panduan DB-Ex* bagian 6d.
- MS Access butuh driver Access 64-bit (MS Office 64-bit atau Microsoft Access Database Engine 2016 x64). Database & tabel dibuat otomatis.

## 69. DB-Ex 0.33.1 — rilis ruang kerja Borang

- Isi sama dengan 0.33.0 (Borang: Ore Spotter / Truck Count & RC Drill / Chiptray Log). Build 0.33.0 terhenti di uji otomatis sebelum installer dibuat; 0.33.1 memperbaikinya. Pasang `DB-Ex-Qt-Setup-0.33.1.exe`.

## 70. DB-Ex 0.34.0 — Borang mengikuti borang ore spotter lapangan

- Jenis borang ore kini mengikuti borang lapangan: **Ore Spotter: Loading Pit → ROM / Stockpile** dan **Ore ke Stockpile / Crusher (Rehandling / Direct)**, di samping **RC Drill / Chiptray Log**. Borang ore yang ditambahkan di 0.33.x memakai kolom lama: hapus lalu tambahkan ulang scan-nya.
- Tanda ulang (〃, ", =, garis), jam yang ditulis menitnya saja dan nomor truk singkat diisi otomatis lalu ditandai kuning untuk dicek. Langkah lengkap: *Panduan DB-Ex* bagian 6d.
- Tabel database ekspor: `ORE_LOADING_PIT`, `ORE_ROM_CRUSHER`, `RC_INTERVAL`.

## 71. DB-Ex 0.34.1 — jam shift Borang

- Validasi jam borang ore memakai jam shift site: **shift I / DS 06:00–18:00**, **shift II / NS 18:00–06:00**. Jam di luar shift ditandai merah untuk dicek.

## 72. DB-Ex 0.35.0 — Borang RC Drilling: Daily Drilling Report

- Jenis borang baru **RC Drilling: Daily Drilling Report** di ruang kerja Borang (DB-Ex versi Qt): AI membaca header (rig, driller, shift, jam WH / DL / MNTC / BD / RAIN / STD, HM engine, bit, catatan), tabel aktivitas dan tabel meterage dalam satu borang.
- Kategori aktivitas diisi otomatis dari kata kunci (bisa diganti dari daftar); ringkasan membandingkan jam di borang dengan jumlah durasi aktivitas.
- Ekspor ke tabel **DDR_AKTIVITAS**, **DDR_METERAGE**, **DDR_SHIFT** (Excel, CSV dalam ZIP, SQLite, MS Access) beserta pivot jam per kelompok / kategori dan meter per rig / lubang. Langkah lengkap: *Panduan DB-Ex* bagian 6d.

## 73. DB-Ex 0.35.1 — kelompok jam Daily Drilling Report

- Kategori & kelompok jam aktivitas mengikuti aturan site: **WH** = drilling, traveling antar titik bor, persiapan, P2H, P5M; **DL** = istirahat, standby, wait blasting, traveling ke lokasi; **MNTC / BD / RAIN** = maintenance, breakdown, hujan; **STD** = standby tidak ada operator, standby tidak ada lokasi.

## 74. DB-Ex 0.35.2 — Daily Drilling Report ke dashboard drilling

- Ekspor Daily Drilling Report kini juga menghasilkan sheet **Data_Dashboard** (tabel `DDR_DASHBOARD`) dengan kolom sama seperti sheet *Data* dashboard drilling: Date, EqType, Location, Shift, Prospect, BHID, Interval_m, WH, Maint, BD, Delay, Standby, Rain, Remarks, lalu **Azimuth** dan **Dip**. Satu baris per lubang; jam shift ditulis di baris pertama shift.
- Header Daily Drilling Report mendapat isian **Location** (nama area / prospek), karena tidak tertulis di borang.

## 75. DB-Ex 0.35.3 — Hole ID garis bawah & nama drill rig baku

- Hole ID di Borang (Daily Drilling Report, RC Drill / Chiptray) selalu ditulis dengan **garis bawah** dan huruf besar: Z2-265-S-05 → Z2_265_S_05.
- Drill rig dirapikan ke format **Hanjin 007** (merek + nomor 3 digit) untuk kolom **EqType** dashboard drilling; isian yang dirapikan dari hasil AI ditandai kuning.

## 76. DB-Ex 0.36.0 — tutorial & penjelasan teknis PDF

- **Tutorial DB-Ex** (`Tutorial/DB-Ex_Tutorial_Penggunaan.pdf` di `_1_Dokumen.zip`) mendapat bab 12–16 untuk DB-Ex versi Qt: Singkapan, Borang Ore Spotter (Loading Pit, ROM / Crusher), RC Daily Drilling Report, ekspor ke database & dashboard drilling.
- **Penjelasan Teknis DB-Ex** (`Panduan_Teknis/DB-Ex_Panduan_Teknis.pdf`): Panduan DB-Ex dalam bentuk PDF dengan sampul, daftar isi dan nomor halaman.
- Cara membuat ulang (pengembang): `python docs/tutorial-core/tutorial_shots_qt.py` lalu `python docs/tutorial-core/buat_pdf.py`.

## 77. DB-Ex 0.36.1 — data simulasi Singkapan & Borang

- Paket **DB-Ex_Data_Dummy** di `_2_Data-Latihan.zip` kini juga berisi data latihan bab 12–16 tutorial: `Foto_Singkapan/` (foto dinding trench sintetis, `Sampel_Trench_TR01.txt`) dan `Borang/` (scan borang fiktif `Borang_Loading_Pit_30Okt.jpg`, `Borang_ROM_31Okt.jpg`, `DDR_31Okt.jpg`, dan ketiganya dalam `Borang_Latihan_3_halaman.pdf`). Semua isi fiktif.
## 78. DB-Ex 0.37.0 — QAQC Database (sampel lab & data bor)

- Tombol **QAQC** baru di bilah atas DB-Ex versi Qt. Data QAQC tersimpan sendiri di `_GCEx_Core/qaqc/qaqc.db` dalam folder proyek.
- **QAQC sampel lab** dengan rumus workbook QAQC kantor apa adanya: CRM Z = (Lab − Mean)/SD (PASS ≤ 2, WARNING 2–3, FAIL > 3), blank gagal di atas cut-off (0,01), duplikat HARD = |O−D|/(O+D) lolos ≤ 10 % plus RPD, ARD dan R². Dashboard per zona (Memuaskan / Marginal / Tidak memuaskan), ringkasan per batch lab, Lampiran A/B/C; semua batas bisa diatur di Panel kontrol.
- **Impor**: workbook QAQC (.xlsx / .xlsm; semua sheet dikenali) atau satu tabel / CSV. Upsert per Sample_ID; ID ganda di file dilaporkan.
- **QAQC data bor**: memeriksa Collar, Survey, Assay, Geologi yang sudah diimpor (koordinat nol, EOH kosong, dip terbalik, survey / interval melewati EOH, tumpang-tindih, celah, Sample ID ganda, nilai negatif).
- **Ekspor**: Excel (QAQC_Dashboard, CRM_Data, CRM_Summary, Duplicate_Data, Duplicate Summary, Blank_Data, Report_Appendix, dll.) + folder grafik PNG, dan **laporan QAQC PDF** (ringkasan eksekutif, integritas data bor, CRM, blank, duplikat, batch, lampiran).
- Installer DB-Ex Qt kini membawa **matplotlib 3.9.2** (lisensi di `LISENSI_PIHAK_KETIGA.txt`); selftest installer menguji rute QAQC dan penggambaran grafik.
- Tutorial bab 17–18 (QAQC) + data latihan fiktif `QAQC/QAQC_Latihan.xlsx` di `_2_Data-Latihan.zip`; Panduan DB-Ex bagian 6e.

## 57. GC-Ex Block Model & Drill Hole Ultimate 0.24.9

**Dua dokumen PDF baru untuk keluarga GC-Ex**, mengikuti pola dokumen DB-Ex (tutorial + penjelasan teknis):

| Berkas | Isi | Tempat di Release |
|---|---|---|
| `GCEx_Tutorial_Update.pdf` | Apa yang baru dan bagaimana memakainya: data latihan simulasi baru, latihan terpandu menemukan kembali geometri endapan, klasifikasi keyakinan sumber daya, kerapatan bor per blok, topografi & orthofoto resolusi tinggi, dan yang baru di GC-Ex Block Model | `_1_Dokumen.zip` → `Tutorial/` |
| `GCEx_Petunjuk_Teknis.pdf` | Cara kerja: arsitektur, folder proyek, alur kerja data, format data bor, dua jalur estimasi (vein vs berlapis), algoritme yang dipakai, klasifikasi, LOD topografi/ortho, format impor-ekspor, Block Model, kerja bersama, batasan, masalah umum, hak cipta | `_1_Dokumen.zip` → `Panduan_Teknis/` |

Keduanya **tidak memakai tangkapan layar aplikasi** — gambarnya diagram yang digambar sendiri dan grafik yang dihitung dari model & berkas data latihan. Akibatnya keduanya dapat dibangun di mesin mana pun, ikut dibangun ulang otomatis tiap rilis, dan angkanya selalu cocok dengan data yang dikirim. Membangun manual:

```
python docs/tutorial-gcex/src/build_tutorial_update.py
python docs/tutorial-gcex/src/build_petunjuk_teknis.py
```

Berkas `GCEx_Tutorial_0.24_Tambahan.pdf` digantikan oleh `GCEx_Tutorial_Update.pdf` (isinya diteruskan dan ditambah bab kerapatan bor serta bab GC-Ex Block Model). Gaya kedua dokumen ditaruh di modul bersama `docs/tutorial-gcex/src/doc_gcex.py`.

Perbaikan CI menyertai: pagar kode markdown pada penulisan ringkasan galat ditulis dengan kutip tunggal — di string PowerShell berkutip ganda, backtick adalah karakter escape sehingga tiga backtick membuat kutipnya tidak pernah tertutup dan seluruh langkah gagal diurai (penyebab run 0.24.8 gagal).

## 58. GC-Ex Block Model & Drill Hole Ultimate 0.24.10

**Setiap Release kini memuat installer ketiga aplikasi pada versinya masing-masing.**

Sebelumnya pengemas rilis hanya menyertakan installer yang nomor versinya **sama persis** dengan tag Release (yaitu versi tertinggi di antara ketiga aplikasi). Akibatnya, selama DB-Ex terus naik versi lebih cepat, installer GC-Ex tidak pernah ikut terbit:

| Rilis | Installer di dalamnya |
|---|---|
| v0.33.1 | DB-Ex-Setup-0.33.1.exe saja |
| v0.35.0 | DB-Ex-Setup-0.35.0.exe saja |
| v0.35.3 | DB-Ex-Setup-0.35.3.exe saja |

Padahal CI **membangun ketiga installer di setiap run** — pengemas yang membuangnya. Jadi perbaikan GC-Ex sejak v0.24.7 (klasifikasi keyakinan dengan kerapatan bor, LOD topografi & orthofoto, perbaikan digitasi manual dan as-mined di Block Model) tidak pernah sampai ke pengguna.

Sekarang: bila installer dengan versi tag ada, itu yang dipakai; bila tidak, dipakai installer terbaru aplikasi itu yang ada di folder `dist`. Versi tiap aplikasi disebut di catatan rilis, misalnya:

> Versi tiap aplikasi di rilis ini: GC-Ex Block Model 0.24.10, GC-Ex Drillhole 0.24.10, DB-Ex 0.36.1.

Tag Release tetap memakai versi tertinggi seperti sebelumnya, dan aturan di `CLAUDE.md` disesuaikan agar tidak lagi bertentangan dengan perilaku pengemas.

Diuji dengan installer tiruan pada versi yang berbeda-beda (GC-Ex 0.24.9, DB-Ex 0.36.1): ketiganya masuk ke folder rilis, tabel isi rilis menyebut versi masing-masing, dan `SHA256SUMS.txt` mencakup semuanya.

## 59. GC-Ex Block Model & Drill Hole Ultimate 0.24.11

Rilis v0.36.1 berhasil memuat ketiga installer, dan kedua dokumen PDF baru dibangun ulang di CI. Yang masih tertinggal: dua tutorial bergambar lama. Perbaikan lanjutan dari telaah run terakhir:

1. **Skrip tangkapan layar tahan nilai yang belum terisi.** Ada 13 tempat yang membaca pesan terakhir sebuah menu lalu membersihkan tag HTML-nya, misalnya `GM.lastAuto.replace(…)`. Bila menunya belum pernah menghasilkan pesan, nilainya `undefined` dan seluruh tahap tangkapan layar berhenti. Semua pembacaan itu kini diberi nilai cadangan `(tidak ada)`.
2. **Bor infill data latihan diarahkan ke lensa yang ditelusuri tutorial.** Sebelumnya 14 bor `SIM-INF-*` tersebar ke lensa 2 dan 3; padahal tutorial hanya memakai domain `QV_Lensa2` + `QV_Splay_HW`. Akibatnya langkah *usulkan ke domain aktif* pada bab upsert bisa tidak menemukan apa pun. Kini semuanya diarahkan ke lensa 2.
3. **Penangkapan galat di CI diperbaiki lagi.** Pengecualian Playwright berbentuk `playwright._impl._errors.Error: …`, sedangkan pola sebelumnya mengharuskan baris **dimulai** kata ber-akhiran *Error*, sehingga baris penyebabnya justru terlewat dan yang tertampil hanya jejak berkas. Sekarang pola mencari di mana pun dalam baris, ditambah baris `Call log` / `waiting for` yang biasanya menjelaskan apa yang ditunggu Playwright.
4. Pesan penjaga pada `build_tutorial.py` dan `build_tutorial_bm.py` menyebut nama berkas yang benar (`build_tutorial_update.py`).

## 60. GC-Ex Block Model & Drill Hole Ultimate 0.24.12

Dengan perbaikan pola penangkap galat di 0.24.11, penyebab kegagalan tahap tangkapan layar akhirnya terbaca:

```
playwright._impl._errors.Error: Page.evaluate:
TypeError: Cannot read properties of undefined (reading 'id')
```

Artinya ada perintah yang membaca `.id` dari sesuatu yang belum ada — hampir pasti `GM.doms[0]` atau `GM.doms[1]` pada saat daftar domain belum terisi sebanyak itu. Yang belum diketahui: **di langkah mana**. Pesan Playwright tidak menyebutkan konteksnya, dan log CI hanya memperlihatkan jejak berkas pustaka.

Karena itu ketiga skrip tangkapan layar kini mencetak **penanda jejak** bila berhenti karena galat:

```
GAGAL setelah gambar: 29_upsert_pratinjau.png
catatan terakhir     : upsPrev = Pratinjau: Collar: 7 baru, ...
```

Penanda itu diisi otomatis oleh fungsi `shot()` dan `note()` yang sudah ada, dan dicetak lewat `sys.excepthook` sehingga tidak perlu mengubah susunan skrip. CI ikut menampilkan kedua baris itu sebagai anotasi, jadi langkah penyebabnya langsung terlihat tanpa membuka log.

## 61. GC-Ex Block Model & Drill Hole Ultimate 0.24.13

Penanda jejak 0.24.12 langsung menjawab pertanyaannya:

```
GAGAL setelah gambar: 42_me_panel.png
catatan terakhir     : gsDomMsg = ✓ Tersimpan ke QV_Lensa2. Lanjut di menu Model Estimation.
```

Dua baris sesudah gambar ke-42 masih mencari domain bernama `QV_Utama`:

```js
var d = GM.doms.find(x => x.name === 'QV_Utama');  PT.select('gs.d.' + d.id)
```

Domain itu sudah tidak ada sejak data latihan diganti — skrip kini membuat `QV_Lensa2` dan `QV_Splay_HW`. Saat itu saya hanya mengganti baris `gmAddDom` dan nama berkas `.obj`, tidak menyisir seluruh skripnya; empat acuan nama lama tertinggal, dan dua di antaranya membaca `.id` dari hasil pencarian yang kosong.

Diperbaiki: keempat acuan diganti ke nama domain yang benar-benar dibuat, dan setiap pencarian domain diberi **cadangan** (`|| GM.doms[0]`, atau dijaga `if (d)`) sehingga nama yang tidak ketemu tidak lagi menghentikan seluruh tahap tangkapan layar. Sisa skrip juga disisir: tidak ada lagi Hole ID atau jumlah bor yang dipatok dari data lama.

Kemajuan tahap tangkapan layar sejauh ini: gambar ke-3 → ke-29 → **ke-42** dari sekitar 60.

## 62. GC-Ex Block Model & Drill Hole Ultimate 0.24.14

**Tangkapan layar tutorial Drill Hole akhirnya selesai seluruhnya** — tidak ada lagi penanda jejak dari `tutorial_shots.py`. Kegagalan yang tersisa pindah ke dua tempat lain yang lebih sederhana, dan keduanya akibat penggantian data latihan di 0.24.2:

**1. Block model latihan tidak berisi kadar.** `SIM_BM_GC.csv` yang baru sengaja dibuat **kosong** (`AU_GC = -99` di semua blok) karena dipakai GC-Ex Drill Hole untuk latihan *Model Estimation*. Tetapi GC-Ex Block Model memerlukan model yang **sudah berisi kadar** — tanpa itu tidak ada blok di atas cut-off, tidak ada dig block, dan tidak ada flitch sama sekali:

```
GAGAL setelah gambar: (belum ada)
catatan terakhir     : flitches = []
IndexError: list index out of range
```

Data latihan kini menyediakan **dua** block model:

| Berkas | Isi | Dipakai |
|---|---|---|
| `SIM_BM_GC.csv` | kosong, 10 × 10 × 5 m | GC-Ex Drill Hole — latihan Model Estimation |
| `SIM_BM_GC_kadar.csv` | **berisi kadar**, 5 × 5 × 2,5 m, 66.147 blok, kolom AU_GC / SG / DOMAIN | GC-Ex Block Model — flitch, dig block, additional flagging, as-mined |

Model berisi kadar itu dihitung dari model geologi yang sama (zona didih, ore shoot, halo), dengan 6,3% blok di atas 0,5 g/t dan 73 tingkat flitch 2,5 m — cukup untuk seluruh latihan Block Model.

**2. RL flitch dipatok dari topografi lama.** Skrip mencari flitch pada `RL 292,5` — nilai yang berasal dari data lama. Sekarang RL diambil dari block model yang benar-benar dimuat (bench dengan blok terbanyak), jadi ukuran dan posisi data latihan boleh berubah tanpa merusak tutorial.

**3. `shot_rusak.py` tidak pernah dijalankan CI.** Gambar `validasi_rusak` (database dengan kesalahan sengaja) dipakai narasi `build_tutorial.py`, tetapi skrip pembuatnya tidak ada di urutan langkah CI — sehingga penyusunan PDF berhenti dengan `KeyError: 'validasi_rusak'`. Kini ikut dijalankan sesudah `tutorial_shots.py`.

## 63. GC-Ex Block Model & Drill Hole Ultimate 0.24.15

Setelah 0.24.14, **seluruh tangkapan layar GC-Ex lolos** dan `GCEx_Tutorial_Block_Model.pdf` terbangun segar di CI. Tinggal satu galat pada penyusunan `GCEx_Tutorial_Modelling_Estimasi.pdf`:

```
build_tutorial.py, line 233, in fN
TypeError: unsupported format string passed to NoneType.__format__
```

**Sebabnya.** Skrip tangkapan layar menyimpan hasil Model Estimation per domain, termasuk objek validasi `q.v` (rata-rata komposit, rata-rata estimasi, kadar GC lama, volume, tonase, logam). Objek itu **bisa kosong** bila domain tersebut tidak punya pembanding kadar GC di dalam solid — dan pada data latihan baru, `QV_Splay_HW` memang demikian. Narasi tetap memformat nilainya sebagai angka, jadi penyusunan PDF berhenti.

**Perbaikannya.** Pemformat angka `fN()` kini menulis `–` untuk nilai kosong, bukan melemparkan galat; dan baris ringkasan `QV_Splay_HW` punya kalimat cadangan yang hanya menyebut jumlah blok bila rata-rata estimasi tidak tersedia. Artinya **narasi tutorial tidak lagi mengandaikan setiap domain punya pembanding kadar GC** — data latihan boleh berubah bentuk tanpa mematahkan penyusunan PDF.

## 64. GC-Ex Drill Hole Ultimate 0.24.16 — kerangka blok AOI

Sampai 0.24.15, GC-Ex Drill Hole **selalu memerlukan block model dari luar**: estimasi hanya mengoreksi blok yang pusatnya di dalam solid domain, dan hanya bisa *menambah* blok pada bagian solid yang belum punya blok GC. Tidak ada cara membuat kerangka blok sendiri. Akibatnya pemodelan selalu dituntun model lama, dan material **waste** di sekitar wireframe ore hanya ada bila model impornya memang memuatnya.

Menu **Block Model** sekarang punya tombol **⊞ Buat kerangka blok (AOI)**.

### Apa yang dibuat
Grid persegi seluruh *area of interest* — **ore dan waste** — dari extent, ukuran blok, dan RL yang Anda tentukan. Extent awal diambil dari sebaran lubang bor (+ margin 50 m) dan diperluas bila ada block model aktif. Origin disnap ke kelipatan ukuran blok supaya bench-nya rata.

### Batas yang dipakai
| Batas | Perilaku |
|---|---|
| Potong topografi aktif | hanya blok yang pusatnya **di bawah** permukaan (sisa / in-situ) |
| Di dalam desain pit | blok dipertahankan hanya **antara dasar pit dan topografi** (volume di dalam pit) |
| Rentang RL | batas atas / bawah manual |
| Poligon area | fitur tertutup menu **Map** atau string Surpac — sama persis dengan poligon di Reporting BM |

Permukaan yang dipakai sama dengan Reporting BM: permukaan segitiga (TIN) versi aktif bila ada, kalau tidak titik topografi / desain pit. Jadi volume yang dilaporkan konsisten dengan kerangka yang dibangun.

### Dua mode
| Mode | Perilaku |
|---|---|
| **Pertahankan & isi kekosongan** | block model aktif dipertahankan **utuh** — seluruh blok, ukuran sub-bloknya, dan semua atributnya termasuk **kadar waste dari `.mdl`** — dan blok baru hanya dibuat pada sel AOI yang **belum tercakup** model itu |
| **Ganti** | kerangka baru seluruh AOI, model aktif diabaikan |

Mode *isi kekosongan* itulah jalur untuk melengkapi `.mdl` impor yang cakupannya lebih sempit dari AOI. Cakupan diuji per sel: setiap blok impor menandai semua sel AOI yang **ditimpa kotaknya**, jadi sub-blok Surpac yang lebih kecil maupun blok induk yang lebih besar sama-sama terbaca benar.

Atribut kategori **`AOI_ASAL`** membedakan asal setiap blok: `impor` atau `kerangka`. Blok kerangka **belum punya kadar** — atribut numerik model lama diisi NaN, atribut kategori dibiarkan kosong. Pengisian kadarnya pekerjaan Model Estimation, bukan modul ini.

### Sebelum menekan tombol
Tombol **Hitung jumlah blok** menampilkan ukuran grid, jumlah blok baru, jumlah blok impor yang dipertahankan, perincian yang dibuang (di atas topografi / di luar pit / di luar poligon / sudah tercakup), dan perkiraan volume. Batas aman 4 juta blok baru; di atas itu permintaannya ditolak dengan pesan yang menyarankan memperbesar ukuran blok.

### Penyimpanan proyek
Versi block model berjenis `aoi` menyimpan **parameter saja, bukan bloknya**, sehingga file proyek tetap ringan; kerangka dibangun ulang saat versi itu diaktifkan. Untuk mode *isi kekosongan*, file `.mdl` / CSV dasarnya harus masih ada di folder `sumber/` proyek.

### Diuji
Logika pemotongan diuji terhadap hitungan tangan pada topografi sintetis (bidang miring `z = 300 − 0,1·x`) dan dasar pit RL 240, grid 10 × 10 × 5 m:

| Uji | Hasil modul | Hitungan tangan |
|---|---|---|
| Kerangka penuh + potong topografi | 1.910 blok (90 dibuang) | 1.910 |
| + batas desain pit | 1.110 blok (800 dibuang) | 1.110 |
| Isi kekosongan terhadap model impor separuh AOI | 930 blok baru + 1.000 impor | 930 |

Model gabungan juga diperiksa: kadar blok impor tetap (`AU = 0,2`), blok kerangka `NaN`, kategori lama kosong untuk blok baru, dan `AOI_ASAL` berisi 1.000 `impor` + 930 `kerangka`.

## 65. GC-Ex Drill Hole Ultimate 0.24.17 — estimasi waste

Pelengkap kerangka blok AOI (bagian 64). Setelah kerangka terbentuk, blok di luar wireframe ore masih **tanpa kadar**, karena Model Estimation adalah *hard boundary* per domain: hanya blok yang pusatnya di dalam solid vein yang diestimasi.

Menu **Model Estimation** sekarang punya bagian **⑤ Estimasi waste (material di luar seluruh solid)**.

### Aturannya
| Unsur | Aturan |
|---|---|
| Blok | blok block model aktif yang pusatnya **di luar semua** solid domain |
| Sampel | komposit dari interval bor yang **tidak di-flag domain apa pun** — *hard boundary waste* |
| Parameter | salinan variogram & elipsoid sebuah domain pilihan, dengan **pengali radius**, **panjang komposit**, dan **top-cut** sendiri |
| Penanda hasil | `domain_est = WASTE`, `est_type = 3` |
| Batas opsional | hanya blok di bawah topografi aktif, dan/atau hanya di dalam desain pit |

Hard boundary waste itu penting: interval ore **tidak** ikut jadi sampel, sehingga kadar halo tidak tertarik naik oleh kadar vein. Top-cut waste tersedia terpisah supaya satu assay tinggi di luar solid tidak mencemari seluruh halo.

Parameter waste memakai salinan parameter domain karena variogram waste jarang difit sendiri; pengali radius disediakan karena halo biasanya **lebih menerus** daripada vein, jadi radius > 1× wajar.

### Arti `est_type = 3`
`est_type` sudah membedakan `1` (koreksi blok di dalam solid) dan `2` (blok tambahan di dalam solid). Nilai `3` membuat blok waste:

- **tidak pernah** ikut pelaporan sumber daya per domain vein;
- **tidak diberi kelas keyakinan** — kelas baru *Waste (di luar solid)* pada atribut `klasifikasi`, dan blok ini juga dikeluarkan dari kurva grade-tonase per kelas, karena waste bukan sumber daya;
- tetap terbawa ke **Reporting BM** sebagai material, jadi volume & tonase waste di bawah topografi atau di dalam desain pit bisa dilaporkan bersama ore.

Dengan itu lengkap jalur yang Anda perlukan: **volume ore dan waste di bawah topografi dan di dalam desain pit, beserta klasifikasi sumber dayanya** — klasifikasi hanya pada ore, waste dihitung sebagai material.

### Prasyarat
Blok waste harus **sudah ada** di block model aktif; modul ini tidak membuat blok baru. Bila cakupan `.mdl` impor lebih sempit dari area of interest, lengkapi dulu dengan **Buat kerangka blok (AOI)** mode *isi kekosongan* (bagian 64). Tombol **Periksa dulu** menampilkan jumlah blok waste, jumlah komposit waste, dan berapa blok dilewati per sebab sebelum estimasi dijalankan.

### Diuji
Model tiruan: dua lubang bor vertikal 100 m berjarak 25 m, assay 1 m; flag domain hole A 40–50 m dan hole B 45–55 m (kadar 5 g/t di zona flag, 0,1 g/t di luar); solid domain RL 245–260; topografi RL 290; block model 2 × 20 blok 5 m.

| Uji | Hasil | Harapan |
|---|---|---|
| Komposit di luar flag (2 m) | 91 | 91 (tiap lubang 90 m di luar flag) |
| Komposit berkadar > 1 g/t | 0 | 0 — interval ore tidak ikut |
| Rata-rata kadar komposit waste | 0,100 | 0,100 |
| Blok waste / di dalam solid / di atas topografi | 30 / 6 / 4 | 30 / 6 / 4 |
| `est_type` & `domain_est` hasil | 3 & WASTE | 3 & WASTE |
| Rentang kadar estimasi waste | 0,100 – 0,100 | ~0,100 — tidak tercemar kadar vein |
| Blok `est_type 3` di klasifikasi | *Waste (di luar solid)* | bukan Measured / Indicated / Inferred |

## 66. GC-Ex Drill Hole Ultimate 0.24.18 — waste: variogram domain terdekat, IDW bila jauh

Pada 0.24.17 parameter waste adalah salinan variogram **satu** domain yang dipilih tangan. Itu tidak masuk akal bila ada beberapa domain yang terpisah jauh: halo di sekitar lensa utara seharusnya mewarisi kontinuitas lensa utara, bukan lensa selatan. Sesuai permintaan pemilik, pemilihannya kini **per blok**:

| Jarak blok ke komposit domain terdekat | Metode |
|---|---|
| ≤ ambang (**Jarak maks. ke domain**, bawaan 50 m) | **Kriging** dengan variogram & elipsoid **domain terdekat itu** |
| > ambang | **IDW** pada komposit waste — ditandai `est_pass = 9` |

Domain terdekat dicari dari **komposit ber-flag** tiap domain, bukan dari jarak ke permukaan solid. Itu disengaja: kontinuitas dibawa oleh data, dan blok yang dekat ke dinding solid tetapi jauh dari semua sampel domain itu memang tidak punya dasar untuk memakai variogramnya.

### Mengapa IDW untuk yang jauh
Variogram sebuah domain hanya berlaku di sekitar domain itu. Memakainya pada blok yang jauh berarti mengaku tahu kontinuitas di tempat yang tidak punya data domain — kriging akan tetap menghasilkan angka, lengkap dengan *slope of regression* dan *kriging efficiency* yang **menyesatkan** karena dihitung dari model yang tidak berlaku di situ. IDW tidak berpura-pura: ia hanya pembobotan jarak. Karena itu `est_sor`, `est_ke`, dan `est_kv` diisi **-99** (tidak berlaku) untuk blok IDW, dan `est_pass = 9` membuatnya mudah disaring di Reporting BM maupun tampilan 3D.

Parameter IDW: **pangkat jarak** (bawaan 2 — *inverse distance squared*), **maks titik** (12), dan **radius** (60 m). Blok tanpa satu pun komposit waste dalam radius dibiarkan **tanpa kadar**, bukan dipaksa diisi.

Ada satu jalur jatuh lagi: blok yang **dekat** domain tetapi komposit waste di sekitarnya tidak cukup untuk kriging (tidak memenuhi jumlah sampel minimum pass mana pun) juga diisi IDW, bukan dibiarkan kosong.

Tombol **Periksa dulu** sekarang menampilkan perkiraan pembagian kriging vs IDW dari cuplikan 2.000 blok, dan daftar domain yang variogramnya akan dipakai. Setelah run, panel melaporkan jumlah blok per variogram yang dipakai (mis. `QV_Lensa2 1.240 · QV_Splay_HW 310 · (IDW) 4.880`).

### Diuji
Model tiruan: dua bor vertikal 100 m berjarak 25 m; flag domain A 40–50 m dan B 45–55 m (5 g/t); waste 0,1 g/t kecuali **zona anomali 1,0 g/t** pada A 90–100 m (RL 200–210); solid RL 250–260; ambang 20 m; block model 20 bench 5 m.

| Uji | Hasil | Harapan |
|---|---|---|
| Komposit waste berkadar ore | 0 dari 91 | 0 — hard boundary waste |
| Blok dalam 25 m dari solid | semua kriging (pass 1, sor 0,8) | kriging dengan variogram QV |
| Blok RL < 215 (jauh dari domain) | semua IDW (pass 9), `sor = -99` | IDW |
| Pembagian keseluruhan | 8 kriging + 10 IDW dari 18 blok | 2 blok sisanya di dalam solid, dilewati |
| Blok terbawah (dekat anomali) | 0,992 | mendekati 1,0 — IDW menangkap anomali waste setempat, bukan merata 0,1 |

Baris terakhir itu yang membuktikan gunanya: tanpa IDW setempat, anomali kadar di luar solid akan hilang ditelan rata-rata.

### Lingkup: tipe deposit
| Jalur | Kerangka blok AOI | Estimasi waste |
|---|---|---|
| **Geomodeller Vein** (solid domain — vein, lensa, breksi, stockwork, skarn, massive sulphide) | ya | **ya** |
| **Stratified-Laterite** (lapisan, ruang *unfold*) | ya — kerangkanya geometri murni, tidak mengenal tipe deposit | **belum** |
| **Sesar 3D** | ya | tidak berlaku (bukan domain kadar) |

Estimasi waste bekerja pada jalur **solid domain**: ia mencari blok di luar seluruh solid dan menulis hasilnya ke penyimpanan Model Estimation (`ME.store`). Menu **Stratified-Laterite** punya penyimpanan (`SL.S`) dan mesin estimasinya sendiri — termasuk IDW-nya sendiri di ruang *unfold* — dan tidak memakai modul ini. Untuk laterit, material di luar lapisan yang dimodelkan (overburden di atas, bedrock di bawah lapisan dasar) belum diestimasi.

## 67. GC-Ex Drill Hole Ultimate 0.24.19 — estimasi waste jalur laterit

Bagian 66 menyebut keterbatasannya terang-terangan: estimasi waste baru berlaku pada jalur **solid domain** (Geomodeller Vein). Jalur **Stratified-Laterite** punya penyimpanan (`SL.S`) dan mesin estimasinya sendiri — setiap blok dicari lapisannya lewat `slLayerAt()`, dan blok yang **tidak jatuh di lapisan mana pun** tidak pernah diestimasi. Bagian ini menutup kekurangan itu.

Menu **Stratified-Laterite** sekarang punya bagian **④b Estimasi waste (di luar permukaan lapisan)**.

### Dua zona, masing-masing dengan ruang *unfold* sendiri
Inilah inti perbedaannya dengan jalur vein. Pada laterit, kadar berubah mengikuti **kelengkungan permukaan lapisan**, bukan menurut jarak lurus 3D — dua titik yang berjarak sama bisa sangat berbeda bila satu sejajar permukaan dan satu memotongnya. Karena itu pencariannya dilakukan di ruang *unfold*:

| Zona | Blok | Koordinat *unfold* sumbu ketiga |
|---|---|---|
| **bawah** | di bawah permukaan terbawah model (mis. bedrock, bila lapisan dasar tidak dipakai) | kedalaman di bawah permukaan itu: `z_dasar(x,y) − z_blok` |
| **atas** | di atas kontak teratas model **tetapi masih di bawah topografi aktif** | tinggi di atas kontak teratas: `z_blok − z_atap(x,y)` |
| *(luar)* | di luar cakupan grid permukaan (permukaan NaN) | tidak ada kerangka *unfold* — memakai elevasi apa adanya (3D biasa). Opsional, bawaan **mati** |

**Blok di atas topografi adalah udara, bukan waste**, jadi tidak pernah ikut. Bila topografi belum ada, zona *atas* tidak bisa dipisahkan dari udara sehingga dilewati seluruhnya — panel mengatakannya, bukan menebak.

### Sampel
Komposit dari interval geologi yang **kodenya tidak dipetakan ke lapisan mana pun** — *hard boundary waste*, sama semangatnya dengan jalur vein. Setiap komposit ditempatkan ke zona yang sesuai dengan posisinya **sendiri** terhadap permukaan, lalu dipakai hanya untuk blok di zona yang sama: sampel bedrock tidak pernah mengisi blok di atas kontak teratas, dan sebaliknya.

Bila **semua** kode geologi sudah dipetakan ke lapisan, tidak ada sampel waste — dan pesannya mengatakan itu beserta dua jalan keluarnya (lepaskan kode yang memang bukan lapisan dari pemetaan, atau nyalakan saja estimasi untuk lapisan itu sendiri), bukan mengisi blok dengan angka tanpa dasar.

### Metode: IDW, bukan kriging
Di jalur vein, blok waste dekat domain memakai **variogram domain terdekat** (bagian 66). Di jalur laterit itu tidak dilakukan, dan ini keputusan sadar: variogram sebuah lapisan berlaku **di dalam** lapisan itu, di ruang *unfold*-nya sendiri; di luar seluruh lapisan tidak ada "domain terdekat" yang variogramnya pantas diwarisi. Jadi dipakai IDW dengan jarak anisotropis (elipsoid `r1`/`r2` horizontal searah azimut, `r3` pada sumbu *unfold*) — persis cara `slStep` menghitung jarak saat kriging tidak terpakai. `r3` sengaja kecil secara bawaan (3 m), karena kadar berubah cepat tegak lurus lapisan.

Blok yang tetangganya kurang dari **Min titik** dibiarkan **tanpa kadar**, bukan dipaksa diisi.

### Hasil
Ditulis ke `SL.S` yang sedang aktif: `sl_<unsur>` terisi, `sl_pass = 9` (penanda IDW), `sl_ns`, dan `sl_lapisan` mendapat kategori baru **`WASTE (di luar lapisan)`**. Dengan begitu laporan volume/WMT/DMT dan tampilan 3D langsung mengenalinya sebagai material tersendiri.

**Perhatian:** setiap kali estimasi lapisan (bagian ③) dijalankan ulang, `SL.S` dibentuk baru sehingga estimasi waste ini ikut terhapus — jalankan ulang sesudahnya. Peringatan itu tercetak di panelnya sendiri.

### Diuji
Model laterit tiruan dengan permukaan **miring** (atap `z = 300 − 0,2x`, dasar model 12 m di bawahnya) supaya ruang *unfold* benar-benar diuji, bukan grid datar. Lima bor 30 m berjarak 25 m; Limonit 0–5 m (Ni 1,8%), Saprolit 5–12 m (1,2%), kode `BED` di bawah 12 m **tidak dipetakan** ke lapisan dengan kadar bergradien `Ni = 0,25 + 0,002x` %; block model 20 kolom × 25 bench 2 m.

| Uji | Hasil | Harapan |
|---|---|---|
| Blok zona bawah / udara / sudah punya lapisan | 280 / 100 / 120 | 280 / 100 / 120 |
| Blok terisi | 224 dari 280 | 56 sisanya lebih dalam dari jangkauan sampel → dibiarkan kosong |
| `sl_pass` blok waste | 9 | 9 |
| Kategori `sl_lapisan` baru | WASTE (di luar lapisan) | — |
| Blok limonit yang berubah | 0 | 0 — hasil lapisan tidak tersentuh |
| **Galat kadar bedrock** terhadap gradien sebenarnya | rata-rata **0,0035%**, maks **0,0060%** | mendekati nol |

Baris terakhir itu buktinya: meski permukaannya miring, IDW di ruang *unfold* memulihkan gradien kadar bedrock hampir tepat (mis. pada x = 97,5 m estimasi 0,448% vs sebenarnya 0,445%). Pada percobaan pertama galatnya 10× lebih besar di tepi timur — ternyata itu cacat **tiruan ujinya**, bukan modulnya: `slAt` yang asli menjepit koordinat di tepi grid, sedangkan tiruan pertama menolaknya sehingga komposit bor terakhir terbuang ke zona *luar*. Setelah tiruan disamakan dengan perilaku asli, galatnya turun ke angka di tabel.

### Lingkup sesudah bagian ini
| Jalur | Kerangka blok AOI | Estimasi waste |
|---|---|---|
| **Geomodeller Vein** (solid domain: vein, lensa, breksi, stockwork, skarn, massive sulphide) | ya | ya — variogram domain terdekat, IDW bila jauh |
| **Stratified-Laterite** (laterit Ni, bauksit, stratiform / sedex) | ya | **ya — IDW di ruang *unfold*** |
| **Sesar 3D** | ya | tidak berlaku (bukan domain kadar) |

## 68. GC-Ex Drill Hole Ultimate 0.24.20 — sub-blocking di batas solid & proporsi volume `sb_frac`

Blok dihitung utuh berdasarkan **titik pusatnya**: blok yang separuh di dalam vein dan separuh di luar tetap dihitung 100% ore atau 100% waste. Pada vein tebal 2–4 m dengan blok 5 × 5 × 2,5 m, kesalahan batas itu sendiri sebesar dilusi yang mau diukur — jadi angka dilusi & ore loss tidak bisa dipercaya sebelum ini dibereskan.

Menu **Block Model** mendapat dua tombol baru, dan Reporting BM satu pilihan baru.

### 1. ◗ Pecah blok di batas solid (sub-blocking)
Blok yang **menyeberangi** batas solid dipecah **2 × 2 × 2** menjadi 8 anak, berulang sampai 1–3 tingkat.

Pemecahan 2 × 2 × 2 (bukan 2 × 2 × 1) disengaja: block model Surpac `.mdl` adalah **octree** yang membelah ketiga sumbu bersamaan dengan tingkat yang sama, sehingga blok anak tetap jatuh tepat di kisi octree dan modelnya masih bisa ditulis balik ke `.mdl`.

Uji "menyeberang" memakai **27 titik** (kisi 3 × 3 × 3 di dalam kotak blok): bila semuanya di dalam solid atau semuanya di luar, blok dibiarkan utuh. Kisi 27 titik dipilih supaya vein tipis yang melintas tengah blok **tanpa menyentuh sudut** tetap terdeteksi.

**Sub-blok yang sudah ada dihormati.** Batas ukuran minimum dihitung dari ukuran blok **dominan** dibagi 2^tingkat, per sumbu; blok yang sudah lebih halus dari batas itu dibiarkan utuh. Jadi model Surpac yang memang sudah ber-sub-blok di sekitar wireframe **tidak dipecah ulang**.

Atribut blok anak diwarisi dari induknya, termasuk atribut kategori. Jalankan **sebelum** estimasi: posisi blok berubah sehingga hasil estimasi lama tidak lagi cocok — panelnya memperingatkan bila sudah ada hasil.

### 2. ▢ Hitung proporsi volume ore per blok (`sb_frac`)
Sub-blocking memperkecil kesalahan batas, **tetapi tidak menghilangkannya**: blok terkecil di perbatasan masih dihitung utuh. Pengujian di bawah memperlihatkan galatnya **berayun**, bukan menuju nol dengan rapi.

Jalan keluarnya: simpan **proporsi volume** tiap blok yang berada di dalam solid sebagai atribut **`sb_frac` (0–1)**. Blok di perbatasan lalu dilaporkan seadanya — 0,35 blok ore dan 0,65 blok waste — bukan dibulatkan ke salah satu. Proporsinya dihitung dengan integrasi titik-tengah: 0 bila seluruh 27 titik di luar, 1 bila seluruhnya di dalam, dan bila bercampur dicuplik **10³ = 1.000 titik** per blok.

### 3. Reporting BM: "Timbang volume & tonase dengan proporsi"
Pilihan baru di bagian constraint. Volume & tonase tiap blok dikalikan proporsinya; blok dengan proporsi 0 tidak dilaporkan. **Kadar tidak dikalikan proporsi** — kadarnya memang kadar bagian yang di dalam solid, dan kadar rata-rata ditimbang tonase yang sudah berproporsi.

### Diuji — dan ini mengubah urutan prioritasnya
**Kasus terburuk: vein mendatar tipis.** Vein tebal 4 m (RL 248–252), blok 5 × 5 × 5 m dengan bench berpusat di RL 247,5 dan 252,5 — **tidak satu pun titik pusat blok jatuh di dalam vein**. Volume sebenarnya 400 m³:

| Tingkat pecah | Blok | Titik pusat | Ditimbang `sb_frac` |
|---|---|---|---|
| utuh | 80 | **0 m³ (−100%)** | 400,0 m³ (0,00%) |
| 1 | 136 | 500 m³ (+25%) | 400,0 m³ (0,00%) |
| 2 | 360 | 500 m³ (+25%) | 400,0 m³ (0,00%) |
| 3 | 1.256 | 375 m³ (−6,3%) | 400,0 m³ (0,00%) |

Perhatikan kolom tengah: sub-blocking memperbaiki bencana −100% menjadi ±25%, lalu −6% — **membaik, tetapi berayun**, karena pembulatan titik pusat tidak hilang hanya dengan memperkecil blok.

**Batas melengkung: bola radius 30 m**, volume analitik 113.097 m³:

| Tingkat | Blok | Titik pusat | Ditimbang `sb_frac` | Blok perbatasan | Waktu |
|---|---|---|---|---|---|
| utuh | 4.096 | 114.000 m³ (+0,80%) | **113.120 m³ (+0,02%)** | 632 | 77 ms |
| 1 | 8.520 | 112.625 m³ (−0,42%) | 113.103 m³ (+0,01%) | 2.504 | 0,5 s |
| 2 | 26.720 | 113.000 m³ (−0,09%) | 113.096 m³ (−0,00%) | 9.896 | 2,7 s |

Pada bentuk simetris, galat titik pusat sebagian saling menghapus sehingga tampak kecil (+0,80%) — itulah sebabnya kasus vein tipis di atas jauh lebih penting sebagai penguji.

**Kesimpulan yang jujur dari angka-angka ini:** untuk **volume** ore/waste, `sb_frac` yang menyelesaikan masalah — bahkan **tanpa** memecah blok, galatnya sudah +0,02%. Sub-blocking tetap berguna untuk hal lain: resolusi **kadar** di dekat kontak (blok lebih kecil diestimasi dari komposit yang lebih relevan), dan geometri **dig block** yang mengikuti batas ore lebih rapat. Jadi kalau yang Anda perlukan hanya volume & tonase yang benar, jalankan tombol kedua saja — lebih cepat dan tidak melipatgandakan jumlah blok.

### Penyimpanan proyek
Versi block model berjenis `sub` menyimpan **parameter dan rujukan model dasarnya**, bukan bloknya; hasil pemecahan dibangun ulang saat versi itu diaktifkan. Model dasarnya boleh berjenis `.mdl`, CSV, maupun kerangka `aoi`.

## 69. GC-Ex Drill Hole Ultimate 0.24.21 — variogram waste difit sendiri

Sampai 0.24.20, blok waste memakai **salinan** variogram domain terdekat. Itu pinjaman, dan secara geostatistik tidak ideal: kontinuitas halo di luar solid tidak harus sama dengan kontinuitas bijih di dalamnya. Biasanya pada halo **nugget lebih besar**, **sill lebih kecil**, dan **range lebih panjang** — kadarnya rendah dan meratanya lebih luas.

Modul ini membuka seluruh mesin Geostatistik yang sudah ada untuk populasi waste, bukan membuat mesin baru.

### 1. Populasi WASTE di menu Geostatistik
Bilah **Domain** mendapat pilihan **WASTE (di luar semua domain)**. Komposit yang dipakai hanya interval yang **tidak di-flag domain apa pun** — populasi yang **sama** dengan sampel estimasi waste, jadi variogram yang difit memang variogram populasi yang diestimasi, bukan populasi lain.

Seluruh alat ikut berlaku apa adanya: statistik & histogram, variogram arah & **fan**, fitting model, **KNA**, dan uji estimasi. Tidak ada yang perlu dipelajari ulang.

### 2. "Simpan ke WASTE" di tab Uji estimasi
Menyimpan model variogram + elipsoid + pass + diskretisasi + top-cut + panjang komposit ke parameter waste, ikut tersimpan di proyek. Kotaknya juga menampilkan apa yang sedang tersimpan (unsur, asal populasi, tanggal) dan tombol menghapusnya.

Bila populasi yang sedang dianalisis **bukan** waste, tombolnya bertanya dulu — variogram tetap bisa disimpan, tetapi Anda diberi tahu bahwa asalnya populasi lain.

### 3. Estimasi waste memakainya untuk seluruh blok
Pilihan baru **"Variogram yang dipakai"** di bagian ⑤ Estimasi waste:

| Mode | Perilaku |
|---|---|
| **Otomatis** (bawaan) | variogram waste sendiri bila ada; kalau tidak, variogram domain terdekat |
| **Variogram domain terdekat** | perilaku 0.24.18–0.24.20, walaupun variogram waste tersimpan |

Dengan variogram waste sendiri, **tidak ada lagi uji jarak ke domain**: variogram itu berlaku untuk seluruh blok waste, dan IDW hanya dipakai bila sampel di sekitar blok tidak cukup untuk kriging. Kolom "Jarak maks. ke domain" ikut dinonaktifkan supaya tidak menyesatkan.

### Diuji
Model tiruan: dua bor vertikal 100 m jarak 25 m, flag domain A 40–50 m dan B 45–55 m (5 g/t), waste 0,1 g/t dengan anomali 1,0 g/t di A 90–100 m; solid RL 250–260; ambang jarak domain 20 m.

| Uji | Hasil | Harapan |
|---|---|---|
| Mode sebelum ada variogram waste | `dom` | perilaku lama terjaga |
| Komposit Geostatistik: semua → populasi WASTE | 200 → 180 | 20 interval ber-flag dibuang |
| Kadar yang lolos filter WASTE | 0,1 dan 1,0 g/t | **tidak ada 5 g/t** — ore tidak bocor |
| "Simpan ke WASTE" | nugget 0,35, range 90, asal `populasi WASTE, n=91` | tersimpan dengan jejak asalnya |
| Mode sesudah tersimpan | `own` | otomatis beralih |
| Estimasi waste dengan variogram sendiri | **18 blok kriging, 0 IDW** | seluruh blok, tanpa uji jarak |
| Mode dipaksa "domain terdekat" | 8 kriging + 10 IDW | perilaku 0.24.18 tetap bisa dipakai |

Baris keempat dari bawah itu intinya: dengan variogram waste sendiri, blok yang sebelumnya terpaksa IDW karena jauh dari domain **kini punya model kontinuitas yang sah** dan bisa dikrige.

## 70. GC-Ex Drill Hole Ultimate 0.24.22 — tutorial & petunjuk teknis untuk fitur baru

Tiga fitur terakhir (bagian 64–69) baru tercatat di `README.md` dan panduan ini. Sekarang masuk ke dokumen yang dibaca pengguna.

### `GCEx_Tutorial_Update.pdf` — 21 halaman (dari 14)
Tiga bab baru, dan bab lama "Bagian tutorial lama yang perlu disesuaikan" bergeser ke nomor 10:

| Bab | Isi |
|---|---|
| **7. Block model dari nol: kerangka AOI** | tiga keadaan → tiga mode, tabel batas (topografi / pit / RL / poligon), uji cakupan per sel, `AOI_ASAL` |
| **8. Estimasi waste: kadar di luar wireframe ore** | mengapa waste bukan kadar nol, langkah pemakaian, aturan sampel & variogram, memfit variogram waste sendiri di Geostatistik, jalur laterit dengan ruang *unfold* |
| **9. Sub-blocking di batas solid & proporsi volume** | dua tombol, mengapa 2 × 2 × 2, sub-blok yang sudah ada dihormati, dan tabel pengukuran yang menunjukkan mana yang sebenarnya menyelesaikan masalah volume |

**Tiga gambar baru, semuanya dihitung dari model & data latihan** — bukan tangkapan layar, bukan ilustrasi:

1. **Kerangka blok AOI pada sayatan** — 584 blok terbentuk di bawah topografi, 233 di antaranya di dalam desain pit, dengan jejak solid vein di atasnya.
2. **Kadar waste terhadap jarak ke vein** — dari **32.029 sampel data latihan yang berada di luar solid**: median Au **0,258 g/t** pada jarak < 1,5 m, **0,121 g/t** pada 1,5–5 m, **0,034 g/t** pada 5–12 m, berikut logam yang dikandungnya per pita jarak.
3. **Proporsi volume per blok 5 m pada batas solid** — batas solid sebagai garis kontur dengan angka `sb_frac` di tiap sel.

Dua angka dari gambar itu yang paling penting bagi pembaca, dan keduanya dihitung dari data latihan, bukan dikarang:

- **37,8% dari seluruh logam Au dalam sampel berada pada interval di luar solid vein.** Halo di sekitar vein epitermal bukan kadar nol — justru halo 0,1–0,3 g/t itu yang menentukan apakah dilusi masih ekonomis.
- Pada gambar proporsi volume, **tidak satu pun blok 5 m yang seluruhnya di dalam vein** (22 sel bersinggungan, semuanya hanya sebagian). Dengan vein setipis ini, perhitungan berbasis titik pusat bukan kurang teliti — ia salah secara sistematis.

### `GCEx_Petunjuk_Teknis.pdf` — 10 halaman (dari 8)
Bagian **8. Kerangka blok AOI, estimasi waste & proporsi volume** dengan empat sub-bagian (8.1 kerangka AOI, 8.2 waste jalur solid domain, 8.3 waste jalur berlapis, 8.4 sub-blocking & `sb_frac`); bagian 8–15 yang lama bergeser menjadi 9–16.

### Dibangun di CI
Kedua dokumen ini tidak memakai tangkapan layar aplikasi, jadi ikut dibangun otomatis setiap rilis di langkah **Tutorial PDF — Update & Petunjuk Teknis** (langkah yang wajib berhasil). Gambar-gambarnya dihitung ulang dari data latihan pada setiap build, sehingga angkanya selalu cocok dengan data yang dikirim dalam rilis yang sama.

## 71. GC-Ex Block Model & Drill Hole Ultimate 0.24.23 — tutorial bergambar terkompilasi, koreksi versi, pengaman versi

### Koreksi: Block Model 0.24.16–0.24.22 identik dengan 0.24.15
Rilis 0.24.16 sampai 0.24.22 hanya mengubah GC-Ex Drill Hole Ultimate (kerangka AOI, estimasi waste, sub-blocking, variogram waste) dan dokumen bersama. Nomor versi GC-Ex Block Model ikut dinaikkan di setiap commit itu, padahal **tidak ada satu pun berkas Block Model yang berubah** (`git diff 5007a23 0601b26 -- app/ web-src/ electron/ backend/` kosong; hanya baris versi di `package.json`). Pengguna Block Model 0.24.15 tidak perlu memasang 0.24.16–0.24.22. Block Model **0.24.23** berisi perubahan dokumen saja (bab *Yang baru di 0.24* di tutorial Block Model).

### Pengaman versi
`tools/rilis/kemas_rilis.py` kini menolak rilis bila nomor versi sebuah aplikasi naik tanpa ada berkas milik aplikasi itu yang berubah sejak tag rilis sebelumnya:

| Aplikasi | Berkas miliknya |
|---|---|
| GC-Ex Block Model | `app/`, `web-src/`, `electron/`, `backend/`, `build/`, `legal/`, tutorial Block Model (`GCEx_Tutorial_Block_Model.pdf`, `build_tutorial_bm.py`, `bm_bab.py`, `tutorial_bm_shots.py`), `SIM_BM_GC_kadar.csv` |
| GC-Ex Drill Hole Ultimate | `app-dh/`, `web-src-dh/`, `web-src/`, `electron/`, `backend/`, `build/`, `legal/`, `docs/tutorial-gcex/` (kecuali berkas Block Model di atas) |
| DB-Ex | `app-core/`, `app_core_qt/`, `electron/`, `backend/`, `build/`, `legal/`, `docs/tutorial-core/`, `docs/referensi/`, `docs/PANDUAN_CORE*`, `docs/DB-Ex_*` |

Berkas bersama keluarga (README, panduan ini, `CLAUDE.md`, alat rilis, workflow CI) tidak dihitung milik aplikasi mana pun. Bila sebuah push **hanya** mengubah berkas bersama, **satu** aplikasi boleh naik versi supaya perubahannya tetap terbit di Release.

- Sebelum push: `python tools/rilis/kemas_rilis.py --cek` (keluar 1 + daftar pelanggaran bila ditolak).
- CI menjalankan pemeriksaan yang sama sebagai langkah pertama (gagal cepat, sebelum installer dibangun) dan sekali lagi saat mengemas Release.
- Diuji pada riwayat: rentang `5007a23..0601b26` ditolak dengan pesan *"GC-Ex Block Model 0.24.15 -> 0.24.22: tidak ada berkas GC-Ex Block Model yang berubah"*.

### Tutorial bergambar terkompilasi
Isi *Tutorial Update GC-Ex* kini juga ada di dua tutorial bergambar, dengan tangkapan layar aplikasi dari satu kali jalannya latihan:

| Tutorial | Bab baru / diperbarui |
|---|---|
| `GCEx_Tutorial_Modelling_Estimasi.pdf` | Data simulasi (data penuh 610 bor + peta lensa), **Block model dari nol: kerangka AOI**, **Sub-blocking & proporsi volume (sb_frac)**, **Estimasi waste** (variogram WASTE di Geostatistik, Periksa dulu, hasil di sayatan), **Klasifikasi keyakinan & kerapatan bor** (Reporting BM ditimbang `sb_frac`, kurva grade-tonase per kelas, `est_spasi` di 3D), **Latihan terpandu** (orientasi vein, pitch ore shoot, pemulihan sesar, zonasi vertikal, top-cut; gambar dihitung dari data), **Topografi & orthofoto resolusi tinggi**, estimasi waste laterit (&#9316;b) di bab Stratified-Laterite |
| `GCEx_Tutorial_Block_Model.pdf` | **Yang baru di 0.24** (digitasi manual setara otomatis — Enter menutup string, as-mined & register dapat diedit, subnode per flitch, 3D hasil kerja, rekap .mdl, sayatan seragam, topografi & orthofoto resolusi tinggi) |

`GCEx_Tutorial_Update.pdf` tetap terbit sebagai ringkasan "apa yang baru"; bab 10-nya kini memetakan tiap bab ke bab tutorial bergambar. Nomor versi di sampul kedua tutorial bergambar dibaca otomatis dari `package.json` / `builder-dh.json`. Rujukan bab di dalam f-string (`{B:...}`) yang sebelumnya tercetak mentah kini terselesaikan.

Skrip: `tutorial_shots.py` bagian 16d (AOI → sub-blocking → estimasi ulang → waste → klasifikasi; gagal tidak menghentikan tangkapan layar lain), `tutorial_lat_shots.py` bagian 5c (waste laterit), `build_tutorial_update.py` menulis `fig_update/notes.json` untuk dipakai `build_tutorial.py`.

### Perbaikan kecil (Drill Hole Ultimate 0.24.23)
- Pesan hasil **Estimasi waste** selalu menulis *kriging (variogram domain terdekat)* walaupun yang dipakai variogram WASTE hasil fitting sendiri. Pesan kini menyebut sumber yang benar-benar dipakai; perhitungannya tidak berubah.
- Dialog **Buat kerangka blok (AOI)** dan **Pecah blok di batas solid** (0.24.16 / 0.24.20) tidak punya gaya tampilan sehingga muncul di bawah batas layar dan tidak terlihat. Kini tampil sebagai jendela di tengah layar seperti dialog Import block model.
- Skrip tangkapan layar tutorial: sayatan Geostatistik diambil dari bidang solid QV_Lensa2 (sebelumnya koordinat data latihan lama, 0 komposit), dan dialog peringatan yang tertinggal ditutup sebelum mengambil gambar.

## 72. GC-Ex Drill Hole Ultimate 0.24.24 — profil kadar, pemusatan logam, kipas variogram GT

Tiga grafik yang sebelumnya hanya ada di *Tutorial Update* (dihitung skrip dokumen dari data latihan) kini bisa dibuat langsung di aplikasi dari data proyek sendiri.

| Grafik | Tempat | Isi |
|---|---|---|
| **Profil kadar (zonasi)** | Geostatistik → tab **Profil** | Rata-rata tertimbang panjang per pita RL / Easting / Northing (lebar pita diatur). Hingga 6 panel: unsur, rasio dua unsur (rasio rata-rata, mis. Ag/Au), jumlah dua unsur (mis. Pb+Zn), % panjang kode geologi (mis. tekstur colloform). Garis acuan + label (mis. paleo-muka air tanah). Filter hole, filter domain Geologi, domain aktif Geostatistik, dan opsional hanya slab sayatan. Ekspor CSV & PNG. |
| **Pemusatan logam** | Geostatistik → tab **Statistik** (di atas tabel top-cut) | Kurva % sampel teratas terhadap % logam terkumpul dari komposit yang sedang dianalisis; titik 1 / 5 / 10 %; tabel ambang kadar 1 / 2,5 / 5 / 10 % dengan tombol **Pakai sebagai top-cut**. |
| **Kipas variogram GT & tebal** | Ore Geometry → **③ Ore shoot** | Variogram ternormalisasi (nilai log) GT per bor dan tebal intersep di bidang vein, 36 arah dari garis strike (toleransi ±12,5°, perataan 3 arah); lembah terdalam = arah paling menerus, ditandai otomatis; sumbu shoot yang digambar ikut tampil sebagai garis. |

Tutorial *Modelling & Estimasi*: bab *Filter domain & statistik* mendapat sub-bab Kurva pemusatan logam dan Profil vertikal; Latihan terpandu 2b / 2d / 2e menampilkan versi aplikasi di samping gambar hitungan dokumen. Keterangan gambar statistik kini dari hasil hitung (sebelumnya angka tetap dari data latihan lama).

## 73. Koreksi dokumen & retensi artefak CI (tanpa kenaikan versi aplikasi)

Pembaruan ini **tidak menaikkan versi aplikasi mana pun**: isinya hanya dokumen dan CI, sehingga installer Block Model 0.24.23 dan Drill Hole Ultimate 0.24.24 tidak berubah. Release tetap terbit ulang pada tag yang sama, jadi ZIP dokumen ikut diperbarui.

### 1. Baris *Status pengembangan* yang basi di tutorial
Bab terakhir `GCEx_Tutorial_Modelling_Estimasi.pdf` mencantumkan **"tabel grade-tonnage per domain dan per bench"** sebagai usulan yang *belum disepakati / belum dikerjakan*. Itu keliru dan bisa membuat pembaca mencari fitur yang sebenarnya sudah ada.

Reporting BM **sudah** bisa mengelompokkan laporan grade-tonase:

| Grup laporan | Keterangan |
|---|---|
| Per bench (elevasi) | tinggi bench bebas |
| Per domain estimasi | dari atribut `domain_est` |
| Per domain vein | solid Geomodeller Vein |
| Per atribut kategori | mis. `klasifikasi` (Measured / Indicated / Inferred) |

Semuanya per cut-off, lengkap dengan kurva grade-tonase dan ekspor CSV. Barisnya kini dipindahkan ke daftar **"Sudah tersedia"**, dengan catatan terbuka bahwa baris itu dulu salah.

**Usulan yang benar-benar masih terbuka** tinggal satu: **rekonsiliasi kadar GC lama vs hasil estimasi baru per periode** di GC-Ex Drill Hole. Rekonsiliasi *as-mined* flitch per flitch sudah ada di GC-Ex Block Model; yang belum ada adalah perbandingan periodik (mis. per bulan atau per kampanye bor) antara kadar GC yang dipakai saat penambangan dan model yang diestimasi ulang sesudahnya.

### 2. Retensi artefak CI: 7 → 2 hari
Run terakhir memunculkan galat `Failed to CreateArtifact: Artifact storage quota has been hit`. Itu **tidak menahan rilis** — langkahnya memang `continue-on-error`, dan sumber resmi installer adalah GitHub Release, bukan artefak Actions.

Penyebabnya bukan cacat: setiap push mengunggah tiga installer berukuran 144–200 MB sebagai cadangan, dan dengan beberapa push per hari kuota penyimpanan (dihitung GB-hari) penuh — tercatat 65 artefak, 9,79 GB belum kedaluwarsa.

Retensi ketiga installer di blok rilis diturunkan dari 7 menjadi **2 hari**: cukup untuk mengambil installer sebuah run yang baru selesai, dan memangkas pemakaian kuota sekitar 70%. Artefak uji DB-Ex Qt dibiarkan 7 hari karena ukurannya satu berkas dan dipakai untuk diagnosis lebih lama.

### 3. `CLAUDE.md`: aturan versi yang saling bertentangan
Dua butir aturan saling berlawanan — satu menyuruh menaikkan versi pada setiap push yang mengubah isi *"termasuk perubahan dokumen / data latihan saja"*, satu lagi (ditambahkan 0.24.23) hanya untuk aplikasi yang berkasnya benar-benar berubah. Butir pertama itulah yang membuat versi Block Model naik tujuh kali tanpa satu pun perubahan pada aplikasinya.

Butir pertama kini disamakan: **push yang hanya mengubah dokumen, data latihan, atau CI tidak menaikkan versi aplikasi mana pun**, karena installernya identik dan Release tetap terbit ulang pada tag yang sama. Pembaruan ini sendiri mengikuti aturan barunya.

## 74. GC-Ex Drill Hole Ultimate 0.24.25 — database bor per kampanye (rangka)

Menirukan modul *Geological Database* GEOVIA Surpac: beberapa database bor tersambung sekaligus (`exploration_2024`, `infill_2023`, `grade_control_2025`), satu di antaranya **ACTIVE**, masing-masing berwarna sendiri di tampilan 3D.

### Keputusan rancangan: satu dataset, label asal per hole
Seluruh fitur GC-Ex — 3D, sayatan, Geostatistik, Geomodeller, Model Estimation, Reporting — membaca tabel global `collars` / `surveys` / `assays` / `geoRows`. Memecahnya menjadi beberapa penyimpanan terpisah berarti menyentuh semuanya sekaligus, dengan risiko regresi besar dan **tanpa manfaat tambahan**.

Jadi datanya tetap **satu**, dan setiap hole membawa **label kampanye** asalnya. Ini juga yang tersirat dari permintaan *"kampanye sebagai atribut geologi virtual"*: begitu labelnya ada, pemisahan per kampanye datang gratis di semua mesin yang sudah ada.

### Yang sudah jalan

| Bagian | Isi |
|---|---|
| **Project Tree** | node *Database Bor* dipecah per kampanye; tiap kampanye memuat Collar / Survey / Assay / Geologi beserta jumlah barisnya |
| **Penanda AKTIF** | kampanye aktif = tujuan import / upsert berikutnya; hole tanpa label otomatis masuk ke sana |
| **Tampil / sembunyi** | centang per kampanye, menyaring `visHoles()` sehingga berlaku serentak di 3D, sayatan 2D, statistik, Geostatistik dan komposit |
| **Warna per kampanye** | warnanya ditulis ke gaya kategori, jadi pewarnaan trajectory memakai warna yang sama |
| **Prioritas** | daftar berurutan, bisa digeser naik / turun |
| **Atribut virtual** | kategori **Kampanye** (dan **Gabungan kampanye** bila ada grup) berperilaku seperti atribut geologi biasa |
| **Gabungan (merge)** | beberapa kampanye disatukan sebagai grup bernama; **tiap hole tetap memegang label aslinya**, jadi masih bisa difilter satu per satu |
| **Pindah hole** | hole yang salah label bisa dipindahkan antar kampanye |
| **Tersimpan di proyek** | daftar kampanye, prioritas, kampanye aktif dan label tiap hole ikut disimpan dan dimuat ulang |

Node *Database Bor* juga mendapat perintah **Kampanye baru…** dan **Gabungkan kampanye… (merge)**.

### Diuji
Data tiruan 5 hole (3 eksplorasi + 2 grade control), 68 interval assay dan 68 interval geologi:

| Uji | Hasil |
|---|---|
| Kampanye pertama dibuat otomatis dari nama dataset, seluruh hole berlabel | 5 dari 5 |
| Jumlah baris per kampanye | 3 hole / 56 assay dan 2 hole / 12 assay — **total 68 = 68, cocok** |
| Atribut virtual | `EX-01 → [[0, 100, 0]]` = `eksplorasi_2024`; `GC-01 → [[0, 30, 1]]` = `gc_2025` |
| Atribut geologi lain | tetap diteruskan ke penangan aslinya, tidak terganggu |
| Warna kategori | mengikuti warna kampanye |
| Sembunyikan `gc_2025` | `visHoles` menyusut dari 5 menjadi 3 hole |
| Geser prioritas | urutan berubah benar |
| Gabungan 2 kampanye | grup terbentuk, atribut *Gabungan kampanye* muncul, dan `EX-01` tetap berlabel `eksplorasi_2024` |
| Simpan & muat ulang proyek | 2 kampanye, 1 gabungan, 5 label hole — utuh |

### Yang belum — jangan dianggap selesai
| Belum ada | Keterangan |
|---|---|
| Pemilih kampanye di dialog import | label kampanye sekarang ditentukan oleh kampanye **AKTIF**, belum bisa dipilih saat import berlangsung |
| Pemilihan sheet `.xlsx` berdasarkan nama | pembaca `.xlsx` sudah ada di GC-Ex, tetapi pemetaan otomatis sheet Collar / Survey / Assay / Geologi belum dibuat |
| Penyelesaian bentrok antar kampanye | daftar prioritas sudah ada dan bisa digeser, tetapi aturan "hole yang sama di dua kampanye, yang lebih tinggi menang" **belum** dipakai saat upsert |
| Filter kolom dinamis + rentang nilai | memerlukan penyimpanan kolom mentah hasil import, yang sekarang dibuang setelah dipetakan — pekerjaan tersendiri |
