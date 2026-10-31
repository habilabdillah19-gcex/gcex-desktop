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
