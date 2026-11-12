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

## 79. DB-Ex 0.37.1 — QAQC: input manual & tempel dari Excel

- Tab **Data** di QAQC kini bisa mengedit **CRM_Data, Blank_Data, Duplicate_Data dan Assay_Import** (sebelumnya hanya Master_CRM): klik ganda sel, **+ Baris**, **Hapus baris**, dan **Ctrl+V** blok sel dari Excel (dengan baris judul = kolom dicocokkan menurut judul; tanpa judul = mulai dari sel terpilih).
- Pemeriksaan langsung (sel merah + alasan di tooltip): Sample_ID / Duplicate_ID ganda, kolom wajib kosong, angka tidak valid. **Simpan tabel** menolak menyimpan selama masih ada galat; **Batal** membuang perubahan.
- Impor file tetap **upsert** (tidak menghapus); *Simpan tabel* menyimpan isi tabel di layar apa adanya. Tutorial Latihan 17 langkah 9–10, Panduan DB-Ex bagian 6e.

## 80. DB-Ex 0.37.2 — QAQC: filter Batch_ID & Sample_ID

- Panel kontrol QAQC mendapat **filter Batch_ID** (dari–sampai, atau centang lewat *Pilih batch…*) dan **filter Sample_ID** (dari–sampai, atau daftar yang ditempel dari satu kolom Excel). Rentang memakai urutan nomor (LAB26005 < LAB26012), batas ikut dihitung.
- Semua tab, grafik, ekspor Excel dan laporan PDF hanya memuat sampel dalam filter; filter yang aktif tercantum di bilah atas, dashboard, sheet Control_Panel dan di bawah judul laporan. Data di database tidak berubah; **Hapus filter** kembali ke semua data.
- Kotak isian Panel kontrol kini berbingkai sehingga jelas bisa diketik.

## 82. DB-Ex 0.38.0 — Analisis foto singkapan (Fase 1)

- Tab baru **Analisis** di ruang kerja Singkapan (DB-Ex versi Qt), semua offline:
  - **Segmentasi zona (SAM)** otomatis: SAM membagi foto dari grid titik, zona sewarna yang hanya dipisah jejak kekar digabung. Label dari warna & bentuk (oksida, vein, alterasi pucat, litologi) atau dari AI vision lokal (Ollama) yang melihat foto bernomor zona.
  - **Peta warna terukur**: oksida besi dan vein kuarsa — peta di atas foto, % luas foto & per zona, m² bila foto bergeoreferensi / punya garis skala; area bisa dijadikan poligon usulan.
  - **Struktur & geoteknik**: deteksi jejak kekar / vein → garis usulan, set orientasi & rose diagram, scanline (frekuensi, spasi per set, kelas ISRM), Jv, RQD (Palmström) dan perkiraan GSI (Hoek–Marinos) sebagai bantuan; apparent dip per set bila bergeoreferensi.
- Semua hasil berupa **usulan** (putus-putus) yang baru ikut ekspor setelah diterima geologist.
- SAM kini memakai memori jauh lebih sedikit (puncak ±1,9 GB, sebelumnya bisa >4 GB) — penting untuk PC lapangan 8 GB RAM.
- Data latihan baru `Foto_Singkapan/Dinding_Latihan_W01.jpg` (fiktif), tutorial Latihan 19, Panduan DB-Ex bagian 6c butir 8.

## 83. DB-Ex 0.38.1 — foto dinding pit sungguhan untuk latihan

- Paket data latihan mendapat tiga foto dinding pit sungguhan yang generik (`Foto_Singkapan/Dinding_Pit_A.jpg`, `_B`, `_C`): metadata EXIF / lokasi dibuang dan orang di foto dipotong. Tutorial Latihan 19 langkah 7–9 memakainya, termasuk catatan apa yang andal (peta oksida, batas oksida – segar dari SAM) dan apa yang masih kasar di foto asli (deteksi jejak otomatis, peta vein kuarsa).
- Penyetelan dari uji di foto asli: deteksi jejak memakai peta rekahan gelap / urat terang dan hanya menyimpan garis yang didukung sepanjang panjangnya; zona SAM berupa langit / vegetasi dibuang otomatis; indeks vein kuarsa tidak lagi menangkap langit.

## 84. DB-Ex 0.38.2 — tutorial terkompilasi

- `DB-Ex_Tutorial_Penggunaan.pdf` dibangun ulang: sampul dan daftar isi kini memuat bab 17–19 (QAQC sampel lab, QAQC data bor & laporan PDF, Analisis foto singkapan) dengan data latihan simulasi dan foto dinding pit generik.

## 85. DB-Ex 0.38.3 — bab Singkapan & Analisis foto memakai foto dinding pit sungguhan

- Tutorial bab 12 kini dikerjakan di `Foto_Singkapan/Dinding_Pit_B.jpg`: zona oksida hematit-limonit, vein / dike hematit, kontak, label, strike / dip, channel sampling 4 sampel (`Sampel_Channel_Pit_B.txt`, kadar fiktif) dan infografis.
- Bab 19 dikerjakan di `Dinding_Pit_A.jpg`: peta oksida, usulan jejak otomatis (ditunjukkan apa adanya — masih kasar), jejak yang digambar geologist → set, scanline, Jv, RQD, GSI, lalu zona SAM. `Dinding_Pit_C.jpg` untuk latihan tambahan.
- Foto sintetis (trench & dinding) tidak lagi ada di paket data latihan; hanya dipakai uji otomatis.

## 86. DB-Ex 0.39.0 — lokasi kamera dari GPS HP (Fase 2a)

- **+ Foto** di Singkapan membaca metadata lokasi foto HP (iPhone dsb.): posisi kamera dalam **UTM WGS84** (E, N, RL), ketelitian ±m, arah hadap kamera, kamera & waktu pengambilan (mengisi Tanggal). Tampil di tab Deskripsi.
- **Sistem koordinat…**: zona proyek (mis. UTM 50S) atau otomatis dari bujur. **Peta foto…**: denah posisi & arah kamera semua foto, collar bor, lubang terdekat, tabel lokasi untuk Excel.
- Kompas infografis *otomatis* memakai arah hadap kamera bila foto belum digeoreferensi.
- Metadata lokasi hilang bila foto dikirim lewat aplikasi chat — pindahkan file asli (kabel / AirDrop / Bagikan → Opsi → Lokasi & Semua Data Foto). HEIC belum dibaca: pakai JPG.
- Data latihan: foto Dinding_Pit membawa metadata GPS fiktif; tutorial Latihan 20, Panduan DB-Ex 6c butir 9.

## 87. DB-Ex 0.40.0 — Model 3D (fotogrametri, Fase 2b)

- Tombol **◈ Model 3D…** di ruang kerja Singkapan: 3–10 foto satu dinding → model 3D offline (tanpa internet, tanpa GPU), ±1–1,5 menit untuk 10 foto (termasuk penyesuaian berkas), memori puncak ±0,6 GB.
- **Titik cat RTK**: koordinat ditempel dari Excel / CSV, titik cat diklik di ≥ 2 foto (deteksi bercak cat otomatis membantu) → model berskala & berkoordinat UTM, galat tiap titik dan RMS. Tanpa RTK dipakai GPS HP (kasar).
- **Ukur bidang**: klik titik di sepanjang jejak vein / kekar / sesar yang melintasi permukaan tidak rata → **dip, arah dip, strike sebenarnya**, RMS dan mutu. Ekspor bidang (CSV, STR Surpac) dan awan titik (PLY).
- Data latihan `Model_3D/Dinding_M01` (dinding sintetis fiktif, 10 foto, `Titik_RTK_Dinding_M01.csv`, `KUNCI_JAWABAN.txt`); tutorial Latihan 21; Panduan DB-Ex 6c butir 10.

## 94. DB-Ex 0.42.1 — halaman depan per ruang kerja

- **DB-Ex versi Qt**: halaman depan memuat empat kartu, yaitu **Core box**, **Singkapan & Model 3D**, **Borang lapangan** dan **QAQC Database**. Setiap kartu punya tombol buka folder sendiri (*Buka folder foto core box*, *Buka folder singkapan*, *Buka folder borang*, *Buka folder QAQC*); folder yang dipilih langsung terbuka di ruang kerja itu.
- Tombol **Buka folder** di bilah atas dan *File → Buka folder…* (Ctrl+O) membuka folder untuk ruang kerja yang sedang aktif; *File → Buka folder untuk* memilih ruang kerjanya.
- **Folder terakhir** mencatat ruang kerja terakhir tiap folder, jadi klik folder singkapan langsung kembali ke Singkapan.
- Bilah filter (Hole ID, kedalaman, status) hanya tampil di ruang kerja **Core box**, tidak di halaman depan.
- **DB-Ex versi HTML** (`DB-Ex-Setup`) tetap khusus Core box; halaman depannya kini menyebut bahwa Singkapan, Borang dan QAQC ada di DB-Ex versi Qt (`DB-Ex-Qt-Setup`).
- Perbaikan: membuka folder singkapan untuk kedua kalinya dalam satu sesi tidak lagi memunculkan galat.
- **Installer DB-Ex versi Qt kini ada di Release resmi**: `DB-Ex-Qt-Setup-<versi>.exe` (sebelumnya hanya di pre-release `core-ex-qt-uji`, yang tidak tampil di halaman Release). Pasang installer ini untuk memakai Singkapan & Model 3D, Borang dan QAQC; DB-Ex versi HTML (`DB-Ex-Setup`) otomatis dicopot karena terpasang di folder yang sama. Data di folder proyek (`_GCEx_Core`) tidak tersentuh.

## 89. DB-Ex 0.42.0 — foto drone & Model 3D sampai 100 foto

- **Foto drone DJI** (Mavic 3 / 3E, Phantom 4 RTK, Matrice): arah hadap (yaw gimbal), pitch gimbal, tinggi relatif / absolut dan status RTK dibaca dari metadata XMP. Jenis foto *lantai* / *dinding* terisi otomatis dari sudut gimbal.
- **Skala otomatis foto lantai** dari tinggi terbang dan lensa (drone menunduk tegak): m², spasi kekar, Jv, RQD tanpa garis skala. Klik *ubah tinggi* di info kamera bila lantai tidak setinggi titik lepas landas.
- **Tautkan, bukan salin**: menambah > 20 foto atau > 150 MB menawarkan *Tautkan* — foto tetap di folder aslinya (folder drone 6 GB tidak tersalin ulang). Folder asli jangan dipindah.
- **Model 3D 3–100 foto** (sebelumnya maks. 10): 60 foto drone ±3 menit, memori puncak ±0,75 GB; kemajuan tampil selama pembangunan.
- Panduan DB-Ex 6c butir 9 & 10, tutorial Latihan 21.

## 88. DB-Ex 0.41.0 — Legenda site & penyaring jejak AI

- **Legenda site…** (dialog AI lokal dan tab Analisis Singkapan): isi istilah resmi proyek, yaitu litologi, alterasi, oksida / vein & mineralisasi, struktur, hal yang *bukan geologi* (bekas lubang ledak, pita ukur, cat) dan catatan lain. Tersimpan di folder proyek dan otomatis ikut ke semua prompt AI geologi: analisis core box, deskripsi & delineasi singkapan, label zona SAM, penyaring jejak.
- **Saring jejak dengan AI vision (Ollama)** di tab Analisis → 3 · Struktur & geoteknik: centang sebelum *Deteksi jejak*, atau klik **Saring ulang**. AI melihat foto asli dan foto dengan kandidat jejak bernomor; jejak geologi diberi jenis & nama, jejak semu dibuang. ±1–3 menit dengan `qwen3-vl:8b` di GPU.
- Tidak perlu model baru: tetap `qwen3-vl:8b` (atau `qwen3-vl:4b` bila memori GPU kecil). Tutorial Latihan 19, Panduan DB-Ex bagian 3 dan 6c butir 8.

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

## 75. GC-Ex Drill Hole Ultimate 0.24.26 — set kerja vs referensi, merge, dan export .xlsx

Melengkapi rangka kampanye (bagian 74) dengan alur kerja yang sebenarnya diminta: **saat kampanye grade control jadi set kerja, bor eksplorasi dan infill tetap terlihat sebagai bahan pertimbangan pemodelan — tanpa ikut mencemari angkanya.**

### Tiga peran per kampanye
| Peran | Tampil di 3D / sayatan | Ikut Geostatistik, statistik, flag, estimasi |
|---|---|---|
| **Set kerja** | ya | **ya** |
| **Referensi** | ya | **tidak** |
| **Sembunyi** | tidak | tidak |

Kampanye **AKTIF** selalu ikut set kerja (ia tujuan import / upsert), jadi tidak bisa dijadikan referensi tanpa memindahkan status aktif dulu.

### Pemisahannya nyata, bukan sekadar label
Sebelumnya `visHoles()` dipakai bersama-sama oleh penggambaran **dan** analisis, sehingga menyembunyikan bor dari analisis berarti menghilangkannya dari layar juga. Sekarang:

- `visHoles()` tetap **daftar tampil** — dipakai penggambaran 3D dan sayatan, hanya membuang kampanye *sembunyi*;
- `visHolesK()` adalah **daftar set kerja**, dan **enam titik analisis** dialihkan ke sana: Geostatistik (analisis sayatan dan uji estimasi), flag otomatis dari kadar, komposit & statistik, klik flag di sayatan, serta selubung mineralisasi (*envelope*);
- Model Estimation dan estimasi waste berjalan dari `GM.flags` / `holeData`, bukan `visHoles`, jadi disaring terpisah lewat `meRuns`.

### Merge: menaikkan data referensi ke set kerja
**Gabungkan ke set kerja… (merge)** memilih kampanye mana yang dinaikkan. Sesudahnya:

- data gabungan langsung dipakai pemodelan, Geostatistik dan estimasi;
- **tiap hole tetap memegang label kampanye aslinya** (atribut `Kampanye`), ditambah atribut penanda **`Set kerja`** berisi *set kerja* / *referensi*;
- catatan merge (nama, kampanye yang ikut, waktu) disimpan di proyek supaya asal-usulnya terlacak;
- hasilnya bisa diekspor.

Jadi Anda tetap bisa memilah kembali: warnai per kampanye asal, atau filter hanya bor eksplorasi yang sudah masuk set kerja.

### Export set kerja ke .xlsx
**Export set kerja (.xlsx)…** menulis satu file Excel berisi empat sheet — **Collar, Survey, Assay, Geologi** — hanya untuk hole yang ikut set kerja. **Kolom `Kampanye` ikut ditulis di setiap sheet**, sehingga asal tiap hole tetap terlacak di file keluaran.

Penulis `.xlsx`-nya dibuat sendiri di dalam GC-Ex: zip dengan entri **stored** (tanpa kompresi) dan SpreadsheetML *inline string*. Entri stored dipilih supaya tidak bergantung pada `CompressionStream` dan hasilnya mudah diperiksa; filenya lebih besar, tetapi tetap `.xlsx` sah.

### Diuji
Data tiruan 5 hole (3 eksplorasi/infill + 2 grade control), 68 interval assay dan 68 interval geologi, dengan `gc_2025` sebagai kampanye aktif:

| Uji | Hasil |
|---|---|
| `eksplorasi_2024` dijadikan **referensi** | `visHoles` tetap 5 hole, `visHolesK` tinggal `GC-01, GC-02` |
| Bor eksplorasi terlihat tetapi tidak ikut analisis | **ya** |
| `meRuns` (estimasi) | hanya `GC-01, GC-02` |
| Atribut penanda | `GC-01 → set kerja`, `EX-01 → referensi` |
| **Merge** 2 kampanye | 5 hole masuk set kerja, 1 kampanye dinaikkan dari referensi |
| Label asli sesudah merge | `EX-01` tetap `eksplorasi_2024`, penandanya berubah jadi *set kerja* |
| Export `.xlsx` | 51,5 KB; **dibuka openpyxl**: sheet Collar / Survey / Assay / Geologi, CRC seluruh entri OK |
| Isi sheet Assay | header `HoleID, From, To, SampleID, Au, Jenis, Kampanye`; baris pertama `EX-01, 0, 5, S0, 0,5, RC, eksplorasi_2024` |

### Yang masih belum
Pemilih kampanye di dialog import, pemetaan sheet `.xlsx` per nama saat **import**, penyelesaian bentrok antar kampanye saat upsert, dan penyusun filter AND/OR dengan rentang nilai atas atribut yang sudah diimport.

## 76. GC-Ex Drill Hole Ultimate 0.24.27 — set merge sebagai database baru, satu dataset aktif

Penyesuaian terhadap alur kerja yang sebenarnya, setelah rujukan Surpac diperjelas. Dua hal berubah dari 0.24.26.

### 1. Merge membuat DATABASE BARU, bukan sekadar menaikkan status
Sebelumnya *merge* hanya menandai beberapa kampanye sebagai "set kerja". Sekarang merge membuat **node database tersendiri** di Project Tree, dengan empat tabelnya sendiri: **Collar Merge, Survey Merge, Assay Merge, Geologi Merge**.

Anggotanya gabungan hole kampanye sumber, dihitung **hidup** — hole baru yang masuk ke kampanye sumber otomatis ikut ke set merge, tanpa perlu merge ulang. Tidak ada data yang disalin: set merge adalah **pandangan** atas satu dataset yang sama, jadi tidak ada risiko dua salinan yang berbeda isi.

### 2. Satu dataset AKTIF, dan peran diturunkan darinya
Aturan pokok Anda — *pemodelan dan estimasi/statistik hanya berlaku pada dataset yang aktif* — kini menjadi mekanismenya, bukan sekadar catatan:

| Keadaan database | Peran | Tampil di 3D / sayatan | Ikut Geostatistik, statistik, flag, estimasi |
|---|---|---|---|
| **AKTIF** | **set kerja** | ya | **ya** |
| dicentang, bukan aktif | **referensi** | ya | tidak |
| tidak dicentang | **sembunyi** | tidak | tidak |

Yang aktif boleh berupa kampanye **maupun** set merge. Begitu set merge dijadikan aktif, dialah sumber pemodelan dan estimasi — dan kampanye sumbernya otomatis turun menjadi referensi, tetap terlihat untuk pembanding.

`visHoles()` tetap daftar **tampil**; `visHolesK()` adalah **anggota dataset aktif**, dan enam titik analisis memakainya (Geostatistik analisis sayatan & uji estimasi, flag otomatis dari kadar, komposit & statistik, klik flag di sayatan, selubung mineralisasi), ditambah `meRuns` untuk Model Estimation dan estimasi waste.

### Alur kerjanya
1. Database utama **grade control** dijadikan aktif.
2. Kampanye **eksplorasi** dan **infill** dicentang tampil — berdampingan di jendela 3D untuk memvalidasi bor GC. Keduanya **tidak** memengaruhi angka apa pun.
3. Bila datanya bagus: **Buat set merge…** memilih kampanye yang digabung. GC-Ex langsung menawarkan menjadikannya dataset aktif.
4. Sejak aktif, set merge itulah sumber pemodelan, estimasi dan statistik.
5. **Export database ini (.xlsx)** menulis set merge ke empat sheet untuk pihak luar.

### Label asal tetap utuh
Setiap hole tetap memegang atribut **`Kampanye`** (label asalnya) walaupun sudah masuk set merge, ditambah atribut **`Dataset aktif`** berisi *ikut dataset aktif* / *hanya tampil*. Jadi di dalam set merge pun Anda masih bisa mewarnai dan memfilter per kampanye asal — dan kolom `Kampanye` ikut ditulis di setiap sheet file ekspornya.

### Diuji
Data tiruan 5 hole (3 eksplorasi/infill + 2 grade control), 68 interval assay dan 68 interval geologi:

| Uji | Hasil |
|---|---|
| `gc_2025` dijadikan aktif | perannya **set kerja**; `eksplorasi_2024` otomatis **referensi** |
| Bor eksplorasi terlihat tetapi tidak ikut analisis | `visHoles` 5 hole, `visHolesK` hanya `GC-01, GC-02` |
| `meRuns` (Model Estimation) | hanya `GC-01, GC-02` |
| Atribut penanda | `GC-01 → ikut dataset aktif`, `EX-01 → hanya tampil` |
| **Buat set merge** dari 2 kampanye | node baru `GC+EX_2025` berjenis set merge, 5 hole |
| Set merge dijadikan aktif | perannya **set kerja**; kedua kampanye sumber turun jadi **referensi** |
| `visHolesK` sesudahnya | kelima hole — pemodelan kini memakai data gabungan |
| Label asal | `EX-01` tetap `eksplorasi_2024`, penandanya berubah jadi *ikut dataset aktif* |
| Export `.xlsx` set merge | 51,5 KB, **dibuka openpyxl**: Collar 5, Survey 5, Assay 68, Geologi 68 baris; CRC seluruh entri OK |

Proyek yang disimpan dengan 0.24.25/0.24.26 dimuat ulang dengan penyesuaian otomatis: grup gabungan lama menjadi set merge, dan keadaan tiga nilai menjadi centang tampil.

## 77. GC-Ex Drill Hole Ultimate 0.24.28 — import per kampanye & penyusun filter AND/OR

Menutup empat hal yang masih tertinggal dari rangkaian kampanye.

### 1. Pemilih kampanye tujuan di dialog import
Dialog import dan upsert mendapat **Kampanye tujuan** beserta tombol **+ Kampanye baru…**. Seluruh hole dari import itu diberi label kampanye tersebut. Bawaannya kampanye aktif — atau, bila yang aktif adalah set merge, kampanye sumber pertamanya.

### 2. Satu file .xlsx berisi empat sheet
Tombol **⇧ Satu file .xlsx (4 sheet: Collar / Survey / Assay / Geologi)** memasang satu berkas ke keempat slot sekaligus.

Pemilihan sheet per peran memang **sudah** ditangani GC-Ex sejak lama — tiap slot menilai setiap sheet di dalam berkas dan memilih yang paling cocok, dengan daftar pilihan untuk mengoreksi. Yang kurang hanyalah memasang berkasnya empat kali, dan itulah yang dikerjakan tombol ini.

### 3. Bentrok antar kampanye saat upsert
Daftar prioritas kampanye sebelumnya hanya urutan tampilan. Sekarang ia **menentukan**:

| Keadaan | Hasil |
|---|---|
| Hole belum ada | masuk, diberi label kampanye tujuan |
| Hole sudah ada di kampanye tujuan | diganti seperti biasa |
| Hole ada di kampanye **berprioritas lebih rendah** | kampanye tujuan menang: data diganti, label berpindah |
| Hole ada di kampanye **berprioritas lebih tinggi** | **data ditolak** — tidak menimpa, label tidak berubah |

Hole yang ditolak **dilaporkan di pratinjau upsert** lengkap dengan HoleID-nya, jadi penolakan tidak pernah diam-diam.

### 4. Penyusun filter AND/OR + rentang nilai
Panel **Data & Filter** mendapat penyusun aturan. Pilihan atributnya **dinamis**, dibentuk dari apa yang benar-benar masuk saat import — bukan dari kolom mentah berkas Excel/CSV, sehingga tidak ada kolom yang perlu disimpan ulang dan **tidak ada biaya memori tambahan**:

| Kelompok | Contoh | Operator |
|---|---|---|
| Unsur assay | Au, Ag, Cu | ≥, ≤, >, <, =, ≠, **antara (rentang)** |
| Kategori assay | Jenis, Lab | =, ≠, salah satu (daftar), mengandung |
| Atribut geologi | Lith, Alt, Ox, Texture | sama seperti di atas |
| Kampanye & dataset aktif | — | sama seperti di atas |
| Collar | Easting, Northing, RL, kedalaman, bench | angka / teks |
| Interval | From, To, panjang | angka |

Tiap aturan juga punya **ada isinya** / **kosong** untuk menyaring data yang tidak terisi, dan nilai boleh ditulis dengan koma desimal (`0,5`).

Aturan digabung dengan **AND** atau **OR**, dinilai **per interval**; sebuah hole ikut tampil bila sedikitnya satu intervalnya lolos. Ringkasan di bawah panel menyebutkan berapa interval dan berapa hole yang lolos.

**Sambungannya ke mesin yang sudah ada** sengaja dibuat di satu titik: filter dipasang pada `domOK()` — penjaga interval yang memang sudah dipakai Geostatistik, komposit dan statistik — sehingga hasilnya langsung berlaku di sana **tanpa menyentuh satu pun fungsi analisis**. Pembungkusnya dipasang paling luar dan ber-AND dengan filter domain, populasi WASTE, dan populasi per lapisan yang sudah ada, jadi tidak saling meniadakan.

### Diuji

**Bentrok upsert**, tiga kasus pada dua kampanye (`eksplorasi_2024` prioritas 1, `gc_2025` prioritas 2):

| Kasus | Hasil |
|---|---|
| Tujuan `gc_2025`, data memuat `EX-01` (milik prioritas 1) + `GC-99` baru | hanya `GC-99` masuk; `EX-01` **tidak berubah** dan labelnya tetap; penolakan dilaporkan |
| Tujuan `eksplorasi_2024`, data memuat `GC-01` (milik prioritas 2) | `GC-01` diganti dan labelnya pindah ke pemenang |
| Prioritas `gc_2025` dinaikkan, lalu kasus pertama diulang | kini `EX-01` **diganti** dan labelnya pindah — hasilnya berbalik mengikuti prioritas |

**Penyusun filter**, data tiruan 3 hole / 7 interval:

| Aturan | Hasil |
|---|---|
| `Au ≥ 0,5` | 3 interval, hole `EX-01, GC-01` |
| `Au antara 0,3–1,0` | 3 interval dari tiga hole berbeda |
| `Au ≥ 0,5` **AND** `Lith = QV` | 2 interval — interval `Au 2,5` gugur karena `Lith = AND` |
| `Au ≥ 2` **OR** `Jenis = DD` | 3 interval |
| `RL collar < 290` | hanya `EX-02` |
| `Dataset aktif = ikut` | `EX-01, GC-01` |
| `HoleID salah satu EX-01, GC-01` | `EX-01, GC-01` |
| Sambungan `domOK` | 3 dari 7 interval — **sama persis** dengan hasil filter; begitu filter dimatikan kembali 7 dari 7 |

## 78. CI: Release tidak lagi dihapus sebelum dibuat ulang (tanpa kenaikan versi aplikasi)

Perbaikan CI; isi installer tidak berubah, jadi tidak ada versi aplikasi yang dinaikkan.

### Apa yang terjadi
Karena tag Release memakai versi **tertinggi** di antara ketiga aplikasi, beberapa push berturut-turut bisa memakai tag yang sama. Langkah penerbitan dulu bekerja begini:

1. kalau Release dengan tag itu sudah ada → **hapus** (`gh release delete --cleanup-tag`);
2. buat Release baru berisi berkas hasil build.

Bila run **dibatalkan atau gagal di antara langkah 1 dan 2**, repo ditinggalkan **tanpa rilis sama sekali**.

Itu benar-benar terjadi pada 4 November 2026: beberapa sesi mendorong beruntun, run yang sedang menerbitkan disalip dan dibatalkan tepat sesudah penghapusan, dan **`v0.36.1` lenyap** — padahal di dalamnya ada `GC-Ex-Drillhole-Setup-0.24.24.exe` dan `GC-Ex-Setup-0.24.23.exe`. Untuk sementara rilis terbaru mundur ke `v0.35.3` yang hanya berisi DB-Ex, sehingga installer GC-Ex tidak bisa diunduh siapa pun.

### Perbaikannya
Release **tidak pernah dihapus** lagi:

1. tag dipindahkan ke commit baru dengan `git tag -f` + `git push -f` — Release-nya tidak disentuh, dan arsip kode sumbernya ikut menunjuk commit baru;
2. judul dan catatan rilis diperbarui di tempat (`gh release edit`);
3. berkas ditimpa dengan `gh release upload --clobber`;
4. **sesudah** semua berkas baru dipastikan lengkap, aset lama yang tidak lagi diproduksi run ini — misalnya installer versi sebelumnya — baru dibuang satu per satu.

Pada titik mana pun selama proses ini, Release selalu ada beserta isinya. Run yang dibatalkan paling buruk hanya meninggalkan rilis dengan isi campuran lama-baru, bukan rilis yang hilang.

Kegagalan memindahkan tag tidak lagi menggagalkan penerbitan; ia hanya memunculkan peringatan bahwa arsip kode sumber bisa tertinggal di commit lama.

## 79. GC-Ex Drill Hole Ultimate 0.24.29 — filter posisi, pemotongan di permukaan, export terfilter

Melengkapi penyusun filter (bagian 77) dengan bagian yang masih kurang.

### 1. Tombol cepat topografi
Dua tombol cepat: **Hanya di bawah topografi** dan **Hanya di atas topografi** (sejak 0.24.30 ada di menu node **Filter data bor** di Project Tree dan di dialog *Atur filter…*; sebelumnya di panel **Data & Filter**). Dinilai **per interval dari titik tengahnya** terhadap topografi aktif. Menekan tombol yang berlawanan tidak menumpuk aturan — ia membalik aturan yang sama.

### 2. Aturan posisi di penyusun filter
Selain atribut dan kampanye, aturan kini bisa menilai **posisi** titik tengah interval:

| Jenis | Operator |
|---|---|
| Topografi aktif | di bawah / di atas |
| **DTM mana pun** (versi topografi, desain pit, wireframe sebagai permukaan) | di bawah / di atas |
| **Solid domain** (Geomodeller Vein) | di dalam / di luar |
| **Wireframe** (Data Referensi) | di dalam / di luar |
| **Poligon** (fitur tertutup Map atau string Surpac) | di dalam / di luar |

Semuanya bisa digabung AND/OR dengan aturan atribut — misalnya *Au ≥ 0,5* **DAN** *di dalam solid QV_Lensa2* **DAN** *di bawah topografi*.

Satu jebakan yang perlu disebut karena sempat menimbulkan bug: **ruang koordinatnya berbeda**. Solid domain dan `topoZ` memakai koordinat **lokal** (`x − offX`), sedangkan `rpTinFn`, `rpSurfSrc` dan `rpPoly` memakai koordinat **absolut**. Modul ini mengubahnya di tiap titik uji.

### 3. Export data bor terfilter + pemotongan di permukaan
**Export terfilter (.xlsx)** menulis empat sheet Collar / Survey / Assay / Geologi; **Export terfilter (CSV)** menulis empat berkas terpisah. Keduanya hanya memuat yang lolos filter, dengan kolom `Kampanye` ikut serta.

Yang membuatnya berguna untuk perhitungan tonase: **interval yang memotong permukaan tidak dibuang dan tidak diambil utuh, melainkan dipotong tepat di permukaannya.** Kedalaman potongnya dicari dengan bagi-dua pada lintasan bor (30 langkah — ketelitiannya jauh di bawah satu milimeter untuk interval sepanjang apa pun yang wajar). Tanpa ini, "hanya di bawah topografi" akan melebihkan tonase sebesar separuh interval yang sebenarnya berada di udara.

Jumlah interval yang terpotong dilaporkan sesudah export.

### 4. Perbaikan: batas poligon pada kerangka blok AOI
Ditemukan saat menelusuri ruang koordinat di atas. Pada bagian 64, batas **poligon area** di pembuat kerangka AOI memanggil `rpPoly()` dengan koordinat **lokal**, padahal fungsi itu bekerja dalam koordinat **absolut** — sehingga batas poligonnya menguji tempat yang salah, meleset sejauh offset proyek (ratusan ribu meter). Batas topografi, pit dan RL tidak terpengaruh. Sudah diperbaiki.

### Diuji
Topografi miring `z = 300 − 0,2x`; bor A (collar RL 310 di x = 0, topo 300) dan bor B (collar RL 290 di x = 100, topo 280) — keduanya **menembus permukaan**, jadi ada interval yang benar-benar memotong topografi:

| Uji | Hasil |
|---|---|
| Tombol **di bawah topografi** | interval 0–10 m gugur pada kedua bor (titik tengahnya di udara), sisanya lolos |
| Tombol **di atas topografi** | tepat kebalikannya: hanya interval 0–10 m |
| Interval yang seluruhnya di atas | dibuang |
| Interval yang seluruhnya di bawah | diambil utuh |
| **Interval yang memotong permukaan** (collar digeser agar permukaan jatuh di kedalaman 15 m, interval 10–20 m) | dipotong menjadi **15,0000–20,0000** |
| Baris Assay di hasil export | `A, 15, 20, S10, …` — batasnya benar-benar ikut terpotong |
| Export terfilter | 2 hole, Assay 6 baris, Geologi 6 baris, 1 interval dilaporkan terpotong |
| Filter dimatikan | `domOK` kembali meloloskan 8 dari 8 interval |

### Cara mematikan filter
Tiga cara, semuanya di panel **Data & Filter**: hapus centang **Filter aktif** (aturannya tersimpan untuk dipakai lagi), tekan **Hapus semua & matikan**, atau hapus aturan satu per satu dengan tombol **×** — filter mati sendiri saat aturan terakhir hilang.

## 80. GC-Ex Drill Hole Ultimate 0.24.30 — menu filter pindah ke Project Tree

Penyusun filter (bagian 77 dan 79) dulu berupa kotak tetap di panel **Data & Filter**. Dengan beberapa aturan,
panel itu menjadi panjang sehingga harus digulung naik-turun terus. Isinya sekarang dipindah ke **Project Tree**.

### 1. Node baru: Filter data bor
Di Project Tree, di bawah **Database Bor** (paling bawah, sesudah tabel dan rencana bor):

| Bagian node | Fungsi |
|---|---|
| **Centang** | Menghidupkan / mematikan filter **tanpa menghapus aturan** (muncul setelah ada minimal satu aturan) |
| **Badge** | `AND · 3 aturan · 12 hole` saat aktif, atau `3 aturan (mati)` saat dimatikan |
| **Anak node** | Satu baris per aturan, mis. `Au (assay) ≥ 0.8` atau `Posisi → topografi aktif di bawah`; menunya memuat *Hapus aturan ini* |
| **Menu node** | *Atur filter…*, tombol cepat topografi, *Export data terfilter* (.xlsx / CSV), *Matikan filter*, *Hapus semua aturan* |

### 2. Dialog Atur filter…
Menu **Atur filter…** (atau klik salah satu anak node lalu *Atur filter…*) membuka dialog tersendiri berisi
penyusun aturan yang sama seperti sebelumnya: pilihan mode **AND / OR**, daftar aturan (atribut, operator, nilai
atau rentang `antara`), tombol **+ Aturan**, dan tombol cepat topografi. Kaki dialog menampilkan ringkasan
*"… dari … interval · … dari … hole lolos"* yang ikut berubah setiap kali aturan diubah.

### 3. Cara mematikan filter
Tiga jalan, semuanya setara:

1. **Lepas centang** node *Filter data bor* — aturan tetap tersimpan dan bisa dihidupkan lagi kapan saja.
2. Menu node → **Matikan filter (aturan disimpan)**.
3. Menu node → **Hapus semua aturan** (filter mati dan aturannya hilang).

Saat filter mati, node tampil samar dan `domOK()` kembali meloloskan seluruh data — tampilan, statistik,
komposit, Geostatistik dan estimasi otomatis memakai semua interval lagi.

> Catatan: aturan filter tetap ikut tersimpan di berkas proyek (`.dh3d` / folder proyek), termasuk status
> hidup-matinya, sehingga keadaan filter kembali seperti saat proyek ditutup.

## 81. GC-Ex Drill Hole Ultimate 0.24.31 — perintah kampanye di node & tutorial disusun ulang

### 1. Tambah kampanye dari node Database Bor
Perintah **Tambah kampanye baru…** dan **Buat set merge… (gabungkan kampanye)** dulu hanya ada di menu tiap node
kampanye. Akibatnya, saat belum ada kampanye sama sekali, node itu belum muncul dan perintahnya tidak bisa dicapai.
Sekarang keduanya juga ada di **menu node Database Bor** sendiri, di bagian paling atas:

| Menu node *Database Bor* | |
|---|---|
| **Kampanye pemboran** | *Tambah kampanye baru…* · *Buat set merge…* (mati bila kampanye sumbernya < 2) |
| | *Tambah / perbarui data bor (upsert)…*, Export database (CSV), Hapus hole tertentu…, dst. |

### 2. Tutorial Modelling & Estimasi disusun ulang
38 bab dikelompokkan menjadi lima **Bagian**, mengikuti urutan node Project Tree dan dipisah per **tipe deposit**:

| Bagian | Untuk | Isi |
|---|---|---|
| **I** Persiapan & database bor | semua tipe | folder proyek, import, validasi, **kampanye pemboran** (bab baru), upsert, **filter data bor** (bab baru), tampilan, sayatan, pita litologi |
| **II** Deposit vein / urat | vein, epitermal, mesotermal | Geomodeller Vein → flag → string HW/FW → solid RBF → struktur & Sesar 3D → vein bercabang → wireframe → Geostatistik → **kerangka blok AOI** → **sub-blocking** → Model Estimation → **estimasi waste** → koreksi bor baru → latihan terpandu |
| **III** Laterit / stratiform berlapis | laterit nikel, bauksit, sedex, seam | Geomodeller Stratified-Laterite (lapisan dari log geologi, estimasi per lapisan di ruang unfold) → **Estimasi waste pada laterit** (bab baru: dua zona unfold, bawah & atas) |
| **IV** Pelaporan sumber daya | semua tipe | klasifikasi Measured / Indicated / Inferred, kerapatan bor, grade-tonase per bench / domain / cut-off |
| **V** Pendukung & pemeliharaan | semua tipe | Map 2D, versi topografi & block model, orthofoto resolusi tinggi, export, folder proyek & backup |

Jadi untuk endapan **vein** dikerjakan Bagian **I → II → IV → V**; untuk **laterit**, **I → III → IV → V**.
Satu catatan: tiga bab di Bagian II — **kerangka blok AOI**, **sub-blocking** dan **estimasi waste** — murni
geometri dan berlaku untuk **semua tipe deposit**, jadi dibaca juga oleh pembaca jalur laterit; bab
*Estimasi waste pada laterit* merujuk ke ketiganya dan hanya menjelaskan apa yang berbeda.

Urutan di dalam setiap bagian mengikuti **urutan kerja nyata**, bukan urutan menu: kerangka blok dibuat sebelum
estimasi (estimasi butuh blok untuk diisi), sub-blocking sebelum estimasi (mengubah geometri bloknya), dan
estimasi waste sesudah estimasi ore (mewarisi variogram domain ore terdekat). Setiap bab mencantumkan nama
Bagiannya di kepala halaman, dan daftar isi dikelompokkan per Bagian. Totalnya 39 bab.

### 3. Petunjuk Teknis & Tutorial Update
- **Petunjuk Teknis** bagian **6 (baru)**: kampanye pemboran, tiga peran database, set merge sebagai pandangan
  hidup, penyelesaian bentrok HoleID, dan filter yang disambungkan pada satu titik (`domOK()`).
- **Petunjuk Teknis** bagian 5 kini merinci **apa yang dibuang vs hanya diperingatkan** saat import / upsert
  (DIBUANG / PERINGATAN / INFO) beserta laporan `Validasi_Data_Bor.csv`.
- **Tutorial Update** bab **10 (baru)**: kampanye, filter, dan export terfilter.

> Catatan penting yang diperjelas di ketiga dokumen: pemotongan interval **tepat di permukaan** hanya terjadi
> pada **berkas export**. Untuk statistik, komposit, Geostatistik dan **estimasi**, interval dinilai **utuh atau
> gugur** dari **titik tengahnya**.

### 4. Mengapa estimasi waste tetap dihitung terpisah dari ore
Pertanyaan yang sering muncul. Di **antarmuka** waste tidak terpisah — ia adalah bagian **③** di dalam menu
**Model Estimation** (dan di dalam **Stratified-Laterite** untuk jalur berlapis): satu run, satu riwayat, satu
block model keluar. Yang terpisah adalah **populasi estimasinya**, dan itu disengaja:

| Alasan | Akibat bila ore dan waste disatukan |
|---|---|
| **Stationaritas / hard boundary** | batas wireframe ore adalah lompatan kadar, bukan gradien. Satu populasi membuat kriging meratakan kadar melintasi batas itu — blok waste di luar vein terangkat oleh komposit vein, blok ore di dalam tertarik turun. Yang terukur bukan dilusi nyata melainkan **dilusi yang disebar interpolator** |
| **Dua populasi statistik** | komposit vein bermean tinggi, CV ~1,2–1,9, nugget tinggi; komposit waste mendekati batas deteksi dengan range jauh lebih panjang. Satu variogram tidak mewakili keduanya |
| **Tujuan pelaporan berbeda** | hasil waste ditandai `domain_est = WASTE`, `est_type = 3` dan **tidak ikut** pelaporan sumber daya; kadarnya untuk dilusi, ore loss dan perencanaan pit |

Integrasinya tetap ada di tempat yang benar: tiap blok waste dikrige memakai **variogram dan elipsoid domain ore
terdekat** selama jaraknya di dalam ambang, jadi kontinuitas lokalnya **diwarisi** dari pemodelan ore. Hanya blok
yang terlalu jauh dari domain mana pun yang jatuh ke IDW (`est_pass = 9`). Penjelasan lengkapnya ada di
**Petunjuk Teknis bagian 9.2**.

## 82. GC-Ex Drill Hole Ultimate 0.24.32 — Autorun & wireframe Leapfrog sebagai domain

Empat node baru di Project Tree. Semuanya perintah, bukan panel — jadi panel kerja tidak bertambah panjang.

### 1. Autorun Wireframe (di bawah Geomodeller Vein)
Centang domain → *Jalankan untuk domain tercentang*. Untuk tiap domain: strike dihitung dari kontak flag →
section dipasang tegak lurus strike → string ditarik di **semua** section → **solid dinyalakan** bila masih mati →
solid rebuild sendiri.

| Keadaan section | Yang dilakukan |
|---|---|
| Belum ada string | dibuat |
| Ada string hasil autorun | diperbarui mengikuti flag terbaru |
| Ada string yang **diedit tangan** | **dilewati**, dihitung di laporan |
| Kontak flag < 2 | dilewati, dihitung di laporan |

Jadi "dari nol" dan "melanjutkan" adalah perintah yang sama — keputusannya per section. Diuji idempoten:
jalan kedua `made 0, rep 44`; dengan satu string diedit tangan `skip 1` dan titiknya tidak berubah.

### 2. Autorun Estimation (update) (di bawah Model Estimation)
Memakai **parameter tersimpan per domain apa adanya** — tidak ada fitting variogram otomatis. Domain tanpa
parameter **dilewati** dengan alasan tertulis (*"di Geostatistik: fitting model, lalu Simpan ke domain"*).
Sesudah domain selesai, lanjut ke estimasi waste lalu menyegarkan Reporting BM. Laporannya membandingkan
kadar rata-rata dan tonase **dengan run sebelumnya**.

### 3. Autorun Lapisan & Estimasi (di bawah Stratified-Laterite)
Usulan lapisan dari kode log menurut **kedalaman tengah rata-rata** (ditimbang panjang interval), lalu permukaan
atap/lantai, lalu estimasi unfold per lapisan + waste laterit. Diuji pada data laterit: TS 0,9 m → LIM 4,2 m →
SAP 11,3 m → BRK 17,6 m — urutan stratigrafi yang benar.

Pengaman: maksimal **12 lapisan** diusulkan (lebih dari itu dilaporkan sebagai "kemungkinan kolom litologi biasa,
bukan kode lapisan"); bila lapisan × grid melebihi 4 juta sel muncul **konfirmasi** yang menyebut ukuran grid dan
memperingatkan tampilan akan berhenti merespons; perhitungan beratnya ditunda supaya dialog laporan tergambar
lebih dulu. Bila lapisan sudah ada, **pemetaan kode tidak diubah** — hanya permukaannya dibangun ulang.

### 4. Wireframe luar (Leapfrog / Surpac) (di bawah Geomodeller Vein)
Dua mode untuk dua tujuan berbeda:

| | **Mode B — diserap** | **Mode A — eksak** |
|---|---|---|
| Jalur | mesh → irisan per section → string HW/FW → solid RBF | domain dikunci ke mesh; uji titik-di-dalam memakai mesh itu |
| Bentuk | rekonstruksi (diresample + dihaluskan RBF) | **identik** dengan mesh Leapfrog |
| Bisa diedit | **ya** — sudah jadi string kontrol GC-Ex | tidak |
| Ikut bor baru | **ya**, lewat Autorun Wireframe | tidak |
| Untuk | kerja harian: melanjutkan model geologist lain | audit: bandingkan tonase batas Leapfrog vs solid GC-Ex |

Mode B satu perintah dengan tiga isian (wireframe, spasi section, nama domain). Mode A dipilih per domain di
anak node. Mode A disambungkan pada **satu** fungsi pembaca solid domain (`meGrpR`), sehingga otomatis berlaku di
estimasi, estimasi waste, sub-blocking, filter posisi dan pelaporan. Bila wireframe belum diimport ulang saat
proyek dibuka, domain itu **otomatis kembali** memakai solid RBF dan node-nya menandai `(hilang)`.

### 5. Kontrol mutu penyerapan — dengan diagnosis sebab
Laporan penyerapan membandingkan **volume wireframe vs volume solid hasil serap** beserta selisih persennya, lalu
**menyebut sebab yang paling mungkin** dan saran yang sesuai sebab itu:

| Sebab terdeteksi | Saran |
|---|---|
| Tebal vein sebenarnya (median kontak HW–FW) < tebal minimum solid | turunkan **Tebal minimum**; *merapatkan spasi section tidak akan menolong* |
| Solid memanjang di luar ujung irisan | kecilkan **radius pengaruh strike**, atau rapatkan spasi section |
| Volume solid justru **kurang** | irisan terlalu jarang / ada irisan terbuka yang dilewati — rapatkan spasi |

Mesh yang **tidak tertutup rapat** juga dilaporkan (jumlah sisi terbuka): pada mesh bocor uji titik-di-dalam tidak
bisa dipercaya, sehingga flag interval maupun volumenya tidak bermakna.

> Diuji di aplikasi sungguhan dengan data latihan dan berkas `QV_Lensa2_Leapfrog.obj`: **45 + 31 + 23 pemeriksaan
> lulus, tanpa galat JavaScript.** Tiga cacat ditemukan dan diperbaiki sebelum rilis: autorun membuat string tanpa
> menyalakan solid domainnya; *Autorun Lapisan* pada kolom litologi bisa membekukan aplikasi tanpa penjelasan; dan
> langkah waste melaporkan "selesai" padahal tidak ada yang dijalankan.

## 83. GC-Ex Drill Hole Ultimate 0.24.33 — Autorun Estimasi dari Nol (Tahap 3)

Melengkapi autorun 0.24.32. Yang sebelumnya hanya bisa **memperbarui** domain yang sudah berparameter; node baru
**Autorun Estimasi dari Nol** (di bawah Model Estimation) menangani domain yang **belum punya parameter sama sekali**.

### 1. Yang dikerjakan
Rekomendasi otomatis (lag / transform / top-cut) → **fitting model variogram** → **KNA** dipindai lalu kombinasi
terbaik diterapkan → parameter **disimpan ke domain**. Bila belum ada block model, **kerangka AOI** dibuat lebih dulu.

### 2. Pilihan, dengan usulan dari data Anda

| Pilihan | Usulan dan dari mana |
|---|---|
| **Blok X / Y** | ≈ **⅓ spasi bor** (median jarak tiap collar ke collar terdekat). Data latihan: spasi 14,5 m → blok 5 m |
| **Blok Z** | ≈ **tebal vein median** (jarak pasangan kontak HW–FW). Data latihan: 3 m |
| **Sub-blocking + N** | disarankan bila tebal vein < **3×** tinggi blok |
| **Minimal komposit** | bawaan 30 — di bawah ini domain dilewati |
| **Nugget maksimal** | bawaan 80% — di atas ini ditandai perlu ditinjau |
| **Simpan ke domain** | bawaan nyala |
| **Langsung estimasi** | bawaan **mati** |

### 3. Tiga putusan per domain

| Putusan | Artinya |
|---|---|
| **✓ tersimpan** | lolos semua gerbang mutu |
| **⚠ perlu ditinjau** | parameter **tersimpan tetapi belum layak produksi** — alasannya ditulis |
| **✖ dilewati** | tidak ada yang disimpan sama sekali |

### 4. Gerbang mutu

| Pemeriksaan | Putusan |
|---|---|
| Komposit < ambang; solid belum ada; domain **sudah berparameter** | **dilewati** — parameter yang sudah disetujui tidak pernah ditimpa |
| Nugget > ambang (80%) | perlu ditinjau — estimasi akan sangat merata |
| **Nugget < 5%** | perlu ditinjau — pada kadar logam nugget nol praktis tidak pernah terjadi |
| **Range mayor ≈ range semi** (< 1,05×) | perlu ditinjau — anisotropi tidak terselesaikan, elipsoid bulat |
| Komposit < 50 | perlu ditinjau — variogram masih rapuh untuk produksi |
| Range mayor < 2× panjang komposit, atau > 3× bentang data | perlu ditinjau — model belum terbentuk / tidak terkekang |

> Tiga gerbang yang dicetak tebal ditambahkan **setelah** uji pertama memperlihatkan variogram yang jelas tidak
> terbentuk — nugget 0%, range mayor sama dengan range semi, 31 komposit — justru lolos sebagai "tersimpan".
> Memeriksa nugget yang terlalu *tinggi* saja tidak cukup, dan kesalahan seperti itu tidak terlihat lagi di angka
> tonase akhir.

### 5. Alur yang disarankan
1. Jalankan **Autorun Estimasi dari Nol**, lihat laporannya (bisa diunduh CSV).
2. Buka tiap domain bertanda **perlu ditinjau** di **Geostatistik**, periksa variogramnya, perbaiki (mis. pasang
   orientasi manual bila anisotropinya tidak terselesaikan), lalu **Simpan ke domain** lagi.
3. Setelah bersih, jalankan **Autorun Estimation (update)**.

Angka sumber daya tidak boleh dilaporkan dari parameter yang belum pernah dilihat sendiri. Autorun ini memangkas
waktu mengetik dan mencoba-coba, bukan tanggung jawab geologistnya.

> Diuji di aplikasi sungguhan: **38 pemeriksaan lulus**, tanpa galat JavaScript — termasuk ambang komposit
> ekstrem (harus dilewati tanpa menyimpan apa pun), jalan normal, dan jaminan tidak menimpa parameter yang ada.

## 84. GC-Ex Block Model 0.24.24 — alat harian grade control & laporan periode

Pemakai GC-Ex Block Model adalah **Junior Grade Control** dan **Short Term / Junior Mine Planner**, jadi seluruh
tambahan ini ditujukan pada *Daily Ore Mining & Grade Control*. Reporting Block Model **tidak** memuat klasifikasi
sumber daya (Measured / Indicated / Inferred) maupun pengelompokan per domain estimasi — keduanya tetap di GC-Ex
Drill Hole, karena itu ranah pemodelan & estimasi.

### 1. Pemeriksaan dig block (node baru, di bawah Dig Block)
Dijalankan **sebelum dig plan terbit**, dua tingkat:

| Temuan | Tingkat |
|---|---|
| Lebar minimum di bawah batas selektivitas alat | **CEGAH** |
| Tonase nol (poligon tidak memuat blok) | **CEGAH** |
| Garis saling memotong (poligon menyilang) | **CEGAH** |
| Poligon tidak tertutup | **CEGAH** |
| Tanpa tujuan material | **CEGAH** |
| Luas di bawah ambang | PERIKSA |
| Kadar kosong (blok −99 / atribut belum dipilih) | PERIKSA |
| Nama dipakai lebih dari sekali | PERIKSA |

Lebar minimum dihitung **rotating calipers pada convex hull** — jarak terkecil antara dua garis sejajar yang
mengapit poligon, bukan perkiraan luas÷keliling. Diuji: persegi 10 × 2 m → tepat **2,00 m**; segitiga tipis →
tepat **0,50 m**. Flitch aktif atau semua flitch, dengan export CSV.

> Dua pemeriksaan jarang berbunyi pada pengaturan bawaan, dan itu wajar: *tanpa tujuan material* hanya mungkin bila
> materialnya tidak cocok aturan tujuan mana pun **dan** tujuan cadangan kosong; *nama ganda* hanya mungkin bila
> template nama tidak memuat `{NO}`. Keduanya tetap diperiksa untuk menjaga keadaan yang tidak biasa.

### 2. Ringkasan harian flitch aktif (node baru, di bawah Laporan Grade × Tonnage)
Satu halaman: ton & kadar **semua unsur terpilih** per material dan per tujuan, jumlah dig block, lalu **rencana
(dig block) vs aktual (as-mined)** bila as-mined flitch itu sudah dihitung. Export CSV.

### 3. Preset kelas kadar & tujuan (node baru, di bawah Dig Block)
Batas kelas kadar, aturan tujuan material, **lebar minimum alat** dan ambang sulfida disimpan sebagai preset
bernama di berkas proyek — supaya shift siang dan malam, dan antar orang, memakai batas yang sama persis. Memakai
preset menghitung ulang material & tujuan dig block yang ada, selalu dengan konfirmasi.

### 4. Laporan periode mingguan / bulanan (node baru, di bawah Register & Laporan As-Mined)
Menjumlahkan apa yang **benar-benar tergali** dari register as-mined.

| | |
|---|---|
| **Periode** | Minggu ini · Minggu lalu · Bulan ini · Bulan lalu · Kustom (minggu Senin–Minggu, ISO) |
| **Kelompokkan** | per tanggal, minggu, **shift (DS / NS)**, flitch, tujuan material, kode ore, pit |
| **Isi** | jumlah poligon, ton, BCM, kadar semua unsur — kadar **ditimbang tonase** |
| **Target** | isi target ton (dan kadar) → pencapaian %, hijau ≥ 100%, jingga ≥ 90%, merah di bawahnya |
| **Tren** | per hari untuk mingguan, per minggu untuk bulanan |
| **Pembanding** | periode sebelumnya, panjang sama, beserta selisih ton & persen |
| **Export** | CSV: tabel, total, target & pencapaian, tren, periode pembanding |

Kadar dijumlahkan dengan mesin yang sama dengan register dan PDF rekonsiliasi, jadi **angkanya tidak pernah
berbeda dari register**.

> **Batasan yang disebut terang-terangan.** As-mined dihitung per flitch aktif, jadi poligon dari flitch yang belum
> pernah dihitung belum punya tonase. Laporan **tidak** menjumlahkannya diam-diam: jumlahnya ditampilkan beserta
> tombol **Hitung semua flitch** (jalur yang sama dengan tombol di panel As-Mined). Bereskan angka itu menjadi nol
> sebelum laporan dikirim.

### 5. Orthofoto resolusi tinggi di plan / flitch
Latar orthofoto pada penampang horizontal dulu satu JPEG seukuran ortho penuh, dibuat sekali lalu dipakai terus;
ortho dibatasi 2,5 juta piksel saat import, sehingga di flitch sempit buram dan zoom tidak menolong. Piramida LOD
(sampai 4096 px, dipotong sesuai tampilan) **sudah ada** tetapi tidak pernah dipanggil dari jalur 2D, dan bentang
dunia tampilan tidak pernah terisi karena pemantau zoom hanya dipasang untuk Peta — yang tidak ada di Block Model.
Keduanya diperbaiki: **zoom masuk sekarang makin tajam**. Node **Orthofoto (latar plan / flitch)** di bawah Flitch
Aktif: nyala/mati, opasitas 100/75/50/25%, dan badge resolusi yang sedang dipakai.

### 6. Rekap dig block: multi-unsur, Metal, centroid
Rekap semua flitch (CSV) dulu hanya satu kolom kadar. Sekarang memuat **semua unsur** yang dicentang di *Elemen
laporan*, **Metal** tiap unsur yang satuannya memungkinkan, serta **Centroid_X / Centroid_Y** (titik berat poligon)
untuk dispatch / fleet system.

### 7. Pembobotan proporsi sub-blok (`sb_frac`)
Bila block model berasal dari Model Estimation GC-Ex Drill Hole dan pernah dipecah di batas solid, tonase dan
volume di Reporting **ditimbang proporsi volume blok**. Tanpa ini block model yang **sama** memberi tonase
**berbeda** antara laporan Drill Hole dan Block Model. Pada data latihan `SIM_BM_GC_estimasi.csv` (20,1% blok
sebagian): **8,05 juta ton** dengan pembobotan vs **10,75 juta ton** tanpa. Pilihannya hanya muncul bila atributnya
ada dan bisa dimatikan (blok dihitung utuh, cara Surpac).

### 8. Data latihan baru
`data/SIM_BM_GC_estimasi.csv` — block model latihan + kolom hasil Model Estimation (`est_pass`, `est_nsamp`,
`est_sor`, `est_ke`, `est_type`, **`sb_frac`**, `domain_est`), dibuat ulang dengan
`python docs/tutorial-gcex/tambah_est_bm.py` (hasilnya selalu sama). `data/BACA_SAYA.txt` juga memuat langkah
melatih laporan periode, karena poligon as-mined harus didigitasi sendiri dan tidak bisa disiapkan sebagai berkas.

> Diuji di aplikasi sungguhan: **60 + 14 pemeriksaan lulus**, tanpa galat JavaScript. Tes pertama sempat lulus
> dengan `nDb: 0` — pemeriksaan dig block belum pernah dijalankan pada dig block sungguhan; tes kedua menyuntikkan
> empat dig block yang sengaja dibuat cacat dan membuktikan ketujuh aturannya memicu.

## 85. Reporting: beberapa desain pit sekaligus & progres topo-ke-topo (kedua aplikasi, versi tetap)

Berlaku untuk **GC-Ex Drill Hole 0.24.33** dan **GC-Ex Block Model 0.24.24** — **nomor versinya tidak dinaikkan**
(permintaan pemilik): Release pada tag yang sama diterbitkan ulang dengan installer baru.

Reporting BM hanya memakai topografi dan desain pit yang **sedang aktif**, satu-satu. Dua pekerjaan rutin karena
itu tidak pernah menghasilkan angka berdampingan. Tab baru **④ Pit & progres** di Reporting (juga node
**Per desain pit & progres topo-ke-topo** di Project Tree, di bawah Reporting BM / Laporan) mengerjakan keduanya.

### 1. Per desain pit, topografi sama
1. Import desain pitnya: **Data Referensi → Import model / solid** (`.dxf`, `.dtm`+`.str`, `.obj`, `.msh`), atau di
   Drill Hole lewat **Data Spasial → + Tambah versi desain pit** (versi lama tetap tersimpan).
2. Atur atribut & cut-off seperti biasa di tab **①**, lalu buka tab **④ Pit & progres** → mode **Per desain pit**.
3. Pilih **satu** topografi untuk semua pit, centang desain pit **dari yang terkecil ke terbesar**, lalu
   **Hitung per pit**.

Hasilnya satu baris per pit (blok, volume, tonase, kadar & logam tiap atribut) dan di bawahnya baris **tambahan** =
selisih terhadap pit sebelumnya. Kadar tambahan dihitung sebagai *logam tambahan ÷ tonase tambahan*, bukan
rata-rata dua kadar. Baris tambahan hanya bermakna untuk pit **bersarang**; untuk pit yang saling terpisah, baca
baris per pit saja.

### 2. Progres topo-ke-topo (ore reconcile)
Mode **Progres topo-ke-topo**: isi **topografi atas** = survei yang lebih **awal** (mis. akhir Juni) dan
**topografi bawah** = survei yang lebih **baru** (akhir Juli). Yang dilaporkan adalah blok yang titik pusatnya
**di bawah** permukaan atas dan **di atas** permukaan bawah — material yang tergali antara dua survei, dengan
seluruh atribut kadar block model (centang *Laporkan semua atribut kadar*), rincian per RL, dan export CSV.

Bila atas dan bawah tertukar, hasilnya **0 blok** — itu petunjuknya, bukan galat.

> ⚠ Hasil ini adalah **block model di antara dua permukaan**, bukan timbangan. Rekonsiliasi sebenarnya tetap
> membandingkannya dengan tonase ROM / pabrik: survei topografi punya ketidakpastian sendiri dan kadar blok adalah
> hasil estimasi. Blok dihitung utuh menurut titik pusatnya, kecuali `sb_frac` dinyalakan di tab ①.

Semua batasan lain (domain, poligon, rentang RL, filter atribut, SG, `sb_frac`, daftar cut-off) tetap diambil dari
tab ① dan ②: yang diganti **hanya permukaan atas & bawah**, sehingga angkanya sebanding dengan laporan biasa.
Secara teknis modul ini mengisi `RP.ovr` lalu memanggil `rpRun()` milik aplikasi sekali untuk tiap target — tidak
ada mesin perhitungan kedua yang bisa berbeda hasilnya.

### 3. Data latihan baru
`python docs/tutorial-gcex/tambah_pit_topo.py` membuat empat permukaan DXF 3DFACE (hasilnya selalu sama):

| Berkas | Isi |
| --- | --- |
| `SIM_pit_fase1.dxf`, `SIM_pit_fase2.dxf` | dua tahap desain pit, lantai RL 240 dan RL 180, lereng 45° (bersarang) |
| `SIM_topo_akhir_juni.dxf`, `SIM_topo_akhir_juli.dxf` | dua survei topografi bulanan pit yang sama (lantai RL 260 lalu RL 245) |

Pada data latihan: fase 1 **3.384 blok / 549.900 t**, fase 2 **16.103 blok / 2.616.738 t**, progres sebulan
**2.439 blok / 396.338 t** (SG 2,6, tanpa batas domain).

### 4. Tombol Demo disusun ulang (kedua aplikasi)
- Urutan langkah mengikuti **buku tutorial**, bukan urutan menu.
- Keterangan tiap langkah dipendekkan menjadi **satu kalimat** (sebagian tadinya 300 huruf dan tidak terbaca
  selesai sebelum langkahnya berganti).
- Tempo bawaan **0,55×** durasi lama dan kursor diperbarui **20 fps**; pilihan kecepatan menjadi
  **Pelan / Sedang / Cepat / Kilat**.
- Langkah pertama menyebutkan **data yang sedang terbuka** dan mengingatkan bila bukan data latihan simulasi
  `SIM_*` — demo berjalan di atas data yang dimuat, bukan data bawaan di dalam installer.
- Langkah baru untuk menu yang belum pernah masuk demo: serap wireframe Leapfrog, kerangka AOI & sub-blocking,
  estimasi waste, autorun, pemeriksaan dig block, preset kelas, ringkasan harian, laporan periode, dan laporan per
  desain pit / progres topo-ke-topo.

> Diuji di aplikasi sungguhan: **16 pemeriksaan lulus di kedua aplikasi**, dibandingkan dengan hitungan **bebas**
> (jumlah blok dihitung ulang dari rumus kerucut pit, tanpa melewati jalur DTM): selisih 0,4–0,5 % karena
> pembulatan segitiga DTM, dan Drill Hole maupun Block Model memberi angka yang **sama persis**. Seluruh tur Demo
> juga dijalankan sampai habis di kedua aplikasi tanpa galat JavaScript.

## 86. Demo berjalan di atas data latihan bawaan (kedua aplikasi, versi tetap)

Sebelumnya tur **Demo** memakai data apa pun yang sedang terbuka — kalau belum ada data, demo tidak bisa
memperlihatkan apa pun, dan kalau datanya data proyek sungguhan, angka yang muncul tidak sama dengan angka di
buku tutorial. Sekarang berkas data latihan yang dipakai tutorial **dititipkan di dalam installer** dan bisa
dimuat satu tombol.

### 1. Dua tombol
| Tempat | Tombol | Yang dikerjakan |
| --- | --- | --- |
| Halaman import (sebelum ada data) | **⇩ Muat data latihan simulasi** | impor seluruh berkas latihan lalu buka viewer |
| Menu **Demo** (sesudah viewer terbuka) | **⇩ Muat data latihan & jalankan Demo** | sama, lalu tur Demo langsung jalan |

Kalau sudah ada data terbuka, GC-Ex bertanya dulu (halaman dimuat ulang, pekerjaan yang belum tersimpan ke folder
proyek akan hilang). Impornya memakai **jalur import yang sama** dengan yang dipakai pengguna
(`SA.slotFile` / `SA.addSp` / `SA.bmPick` / `SA.go`) — tidak ada jalur baca kedua yang bisa berbeda hasilnya.

### 2. Berkas yang dititipkan
| Aplikasi | Berkas | Dari tutorial |
| --- | --- | --- |
| Drill Hole | `SIM_collar/survey/assay/geologi.csv`, `SIM_topo_xyz.csv`, `SIM_BM_GC_kadar.csv`, `QV_Lensa2_Leapfrog.obj`, `SIM_pit_fase1/2.dxf`, `SIM_topo_akhir_juni/juli.dxf` | bab *Membuat folder proyek & import data* sampai *Laporan per desain pit* |
| Block Model | `SIM_BM_GC_kadar.csv`, `SIM_pit_fase1/2.dxf`, `SIM_topo_akhir_juni/juli.dxf` | bab *Halaman muka & import block model* sampai *Laporan per desain pit* |

Untuk Drill Hole yang dititipkan adalah block model **berisi kadar** (`SIM_BM_GC_kadar.csv`), bukan model kosong `SIM_BM_GC.csv` yang dipakai bab estimasi: demo tidak menjalankan Model Estimation (butuh menit), jadi dengan model kosong laporan apa pun akan menunjukkan 0 blok. Model kosongnya tetap ada di ZIP Data-Latihan untuk latihan estimasi.

Tambahan ukuran installer: **Drill Hole ±3,3 MB** (21,1 MB CSV/DXF mentah) dan **Block Model ±1,3 MB** (9,9 MB mentah).

Letaknya `resources/data-latihan` di folder instalasi; dibaca lewat protokol internal
`gcexfile://latihan/<nama berkas>`. Data latihan **lengkap** (laterit, vein bercabang, upsert, database rusak,
QAQC) tetap diambil dari `GC-Ex-<versi>_2_Data-Latihan.zip` pada Release — yang dititipkan hanya yang dipakai tur
Demo, supaya installer tidak membesar tanpa guna.

### 3. Angka di demo = angka di tutorial
Langkah-langkah ini **benar-benar menjalankan** perintahnya dan menampilkan hasil sungguhan di bilah bawah, bukan
angka yang ditulis tangan di dalam program:

| Langkah | Yang ditampilkan |
| --- | --- |
| Domain vein, flag interval & string kontrol | jumlah interval yang diusulkan + jumlah string (tutorial: 524 interval, 98 string) |
| Model vein HW / FW → solid (RBF) | volume solid, tebal rata-rata, interval flag di dalam solid |
| Analisis geostatistik slab | jumlah komposit, rata-rata, CV (tutorial: 657 komposit, 3,150 g/t) |
| Kriging Neighbourhood Analysis | rekomendasi pass 1 |
| Dig block otomatis / Running grade & tonnage | jumlah dig block, ton @ kadar, RL flitch |
| Beberapa pit & progres topo-ke-topo | tonase per fase pit dan progres sebulan (3.384 / 16.103 / 2.439 blok) |

Langkah lain (upsert, Model Estimation, kerangka AOI, sub-blocking, estimasi waste, klasifikasi) **dijelaskan
tanpa dijalankan**: perhitungannya memakan waktu menit, bukan detik, jadi tidak pantas dijalankan di tengah tur.
Angkanya ada di buku tutorial.

## 87. GC-Ex Drill Hole Ultimate 0.24.34 — perhitungan berat punya versi Python, dengan bukti angka

Perhitungan paling berat di GC-Ex sekarang punya **dua versi**: versi JavaScript yang dipakai aplikasi sejak
awal, dan versi Python (NumPy) di backend. Yang dipindahkan: variogram eksperimental & fitting model, Ordinary
Kriging, sub-blocking beserta proporsi volume ore `sb_frac`, dan agregasi laporan tonase × kadar lengkap dengan
constraint-nya (rentang RL, poligon, filter atribut, permukaan atas/bawah, batas DTM tambahan, domain, SG,
pembobotan `sb_frac`).

### 1. Yang berubah di aplikasi: satu tombol, dan angka laporan tidak tersentuh

Di panel **Block Model**, di bawah tombol *Hitung proporsi volume ore per blok (sb_frac)*, ada tombol baru:

> **⏱ Bandingkan sb_frac: JavaScript vs backend Python**

Tombol itu menjalankan **kedua** versi pada mesh solid dan daftar blok yang sama, lalu melaporkan:

| Yang dilaporkan | Gunanya |
| --- | --- |
| beda angka terbesar antara kedua versi | memastikan hasilnya memang sama (beda ~1e-7 adalah pembulatan penyimpanan `Float32`, bukan selisih hitungan) |
| total waktu yang ditunggu, JavaScript vs backend | angka yang benar-benar dirasakan pemakai |
| rincian: waktu hitung murni, jumlah inti CPU, dan waktu kirim data | memperlihatkan di mana ongkosnya berada |

**Atribut `sb_frac` yang tersimpan tetap hasil versi JavaScript**, apa pun hasil pembandingan. Jadi tombol ini
tidak bisa mengubah satu angka pun di laporan tonase — ia hanya mengukur. Kalau backend tidak aktif, tombolnya
mengatakan begitu dan tidak terjadi apa-apa.

Kenapa pengukurannya diserahkan ke pemakai: kecepatan backend bergantung pada **jumlah inti CPU** komputer yang
dipakai, karena perhitungan kriging dan `sb_frac` dibagi ke beberapa proses (hasil satu blok tidak bergantung
pada blok lain). Angka dari komputer pengembang tidak mewakili komputer kantor atau laptop lapangan.

### 2. Bukti bahwa angkanya sama

Bukan "mestinya sama", tetapi diuji: fungsi JS yang dipakai produksi dijalankan di aplikasi sungguhan atas data
latihan simulasi, masukan dan keluarannya **dibekukan** menjadi berkas uji, lalu masukan yang sama dihitung versi
Python dan dibandingkan satu per satu.

| Yang diuji | Cakupan pembandingan | Hasil |
| --- | --- | --- |
| Variogram & fitting | γ per lag/arah, nugget, sill, range | sama |
| Ordinary Kriging | pass, jumlah sampel, kadar, kriging variance, SoR, KE, bobot negatif — 1.000 blok, ketiga pass terpakai | sama |
| `sb_frac` | proporsi tiap blok, jumlah blok utuh / perbatasan / di luar, volume ore berbobot — 66.147 blok terhadap solid 70.780 segitiga | sama (beda maks 3e-08 = batas `Float32`) |
| Agregasi laporan | jumlah blok, volume, tonase, kadar berbobot tonase, dan jumlah blok terbuang di tiap tahap — lima susunan constraint, termasuk progres topo juni→juli (2.439 blok, sama dengan buku tutorial) | sama |

Seluruhnya **44 uji otomatis** (`backend/tests/`), dengan berkas keluaran JS yang dibekukan di
`backend/tests/data/*_js.json`. Kalau suatu saat versi Python bergeser walau sedikit, ujinya gagal. Harness yang
mengambil angka dari aplikasi sungguhan ada di `tools/uji/paritas_*.py`.

### 3. Kecepatan: diukur, bukan diperkirakan

Pada 2 inti CPU, data latihan:

| Bagian | JavaScript | Python |
| --- | --- | --- |
| Variogram & fitting | 623 ms | 441 ms |
| Ordinary Kriging | 0,871 ms/blok | 0,756 ms/blok |
| `sb_frac`, 66 ribu blok | 3.404 ms | 2.373 ms |
| Agregasi laporan | 28–58 ms | 29–80 ms (tidak membaik) |

Dua catatan yang jujur. **Pertama**, agregasi laporan tidak mendapat apa-apa: JavaScript sudah menyelesaikannya
dalam satu lintasan atas blok, jadi tidak ada yang bisa dihemat. **Kedua**, pada `sb_frac` penghematan terbesar
bukan dari NumPy melainkan dari sifat ujinya — uji "titik di dalam mesh" memakai sinar vertikal, sehingga hanya
bergantung pada (x,y). Artinya 1.000 titik cuplikan per blok sebenarnya 100 kolom × 10 ketinggian, dan segitiga
cukup diperiksa **sekali per kolom**: 35,5 detik menjadi 3,9 detik, sebelum dibagi ke inti CPU.

Pada komputer berinti banyak selisihnya akan lebih lebar, dan itulah yang diukur tombol di atas.

### 4. Apa yang belum dilakukan

Aplikasi **belum** memakai backend untuk perhitungan ini. Alasannya terlihat dari pengukuran: mengirim mesh dan
daftar blok ke backend memakan waktu yang tidak kecil, jadi pemindahan yang benar harus mengirim data **sekali**
lalu menyimpannya di backend — bukan mengirim ulang setiap kali hitung. Selama itu belum dikerjakan, jalur
JavaScript tetap satu-satunya yang dipakai, sehingga tidak ada risiko angka berubah.

## 88. Metode tonase: cara Surpac vs cara presisi GC-Ex — dibuat bisa dibandingkan

Pernah ada sengketa angka: volume dan tonase block model **yang sama** berbeda antara hitungan
Surpac dan hitungan GC-Ex. Penyebabnya bukan salah hitung, melainkan dua aturan yang berbeda untuk
blok di perbatasan, ditambah satu pilihan di GC-Ex yang mudah terlewat. Bagian ini menerangkan
keduanya dan di mana angkanya bisa diperiksa.

### 1. Dua aturan yang sama-sama sah

| Cara | Aturan | Dipakai untuk |
| --- | --- | --- |
| **Seperti Surpac** | blok dihitung **utuh** bila titik pusatnya di dalam batas (string / solid / flitch) — sama dengan Surpac *Keep partial = False* | rekonsiliasi dengan report Surpac |
| **Presisi GC-Ex** | blok perbatasan ditimbang **proporsi volumenya** yang benar-benar di dalam batas | dig plan, perhitungan dilusi & ore loss |

Pada vein tebal 2–4 m dengan blok 5 × 5 × 2,5 m, kesalahan batas itu sendiri sebesar dilusi yang
mau diukur — itulah sebabnya cara presisi ada.

### 2. Di tab Dig block: pilihan metode + Audit CSV

Di bawah pilihan *Sayatan BM* ada **Metode tonase** dengan dua pilihan di atas, lalu tombol
**🔍 Audit blok per poligon (CSV)**. Ekspor itu memuat **setiap blok** dengan kedua perhitungan
bersebelahan: luas terpotong, tebal di flitch, volume/ton/metal presisi, lalu kolom *Titik tengah
masuk (Surpac)* beserta volume/ton/metal Surpac.

**Yang diperbaiki pada 0.24.25 / 0.24.35:** ringkasan Audit CSV kini juga memuat **waste pengisi** —
yaitu area poligon yang **tidak tertutup blok BM**, yang dihitung sebagai waste bila pilihan *"Area
polygon tanpa blok BM dihitung sebagai waste default"* menyala (**bawaannya menyala**). Pilihan itu
hanya dipakai metode Presisi GC-Ex; metode Seperti Surpac mengabaikannya.

Sebelum perbaikan ini, ekspor Audit hanya menjumlahkan blok, sedangkan panel Dig block memuat blok
**ditambah** waste pengisi — jadi kedua angka itu tidak pernah cocok dan selisihnya tidak bisa
dijelaskan oleh orang yang hanya memegang ekspornya. Contoh nyata dari data latihan (poligon
4.019,6 m², flitch 2,5 m):

| Angka | Nilai |
| --- | --- |
| Blok (presisi, dipotong) | 8.510,32 t |
| Waste pengisi (area tanpa blok BM) | 17.616,82 t |
| **Ton presisi + waste** (= angka di panel) | **26.127,14 t** |
| Ton Surpac (titik pusat masuk) | 9.100,00 t |

Kolom baru **Ton presisi + waste** itulah yang cocok dengan tonase di panel. Keterangan di bawah
ringkasan menyebutkan SG dan kadar waste yang dipakai, serta menegaskan bahwa metode Surpac tidak
memuatnya. Hint di pilihan metode juga memberi peringatan selama pilihan waste itu menyala.

### 3. Di Reporting BM: tab ⑤ Metode tonase (kedua aplikasi)

Tab baru di Reporting BM — **ada di GC-Ex Block Model maupun GC-Ex Drill Hole** — menghitung
**kedua** metode sekali jalan dan menaruh selisihnya berdampingan per cut-off: blok, volume,
tonase, kadar tiap atribut, lalu baris **Selisih** dalam ton dan persen. Ada tombol Export CSV.

Tab itu memakai atribut, cut-off, pengelompokan, domain, poligon, permukaan dan SG yang sudah
diatur di tab ① dan ②; yang diganti hanya aturan blok perbatasan. Mesin hitungnya `rpRun()` yang
sama seperti laporan biasa, dijalankan dua kali — jadi angkanya pasti konsisten dengan laporan
biasa, bukan hasil rumus salinan. Itu diuji otomatis di `tools/uji/uji_metode_tonase.py`.

**Dua hal yang perlu dibaca sebelum menyimpulkan:**

- Metode presisi memakai atribut proporsi (`sb_frac`). Bila block model belum punya atribut itu,
  kedua metode **identik** dan tab ini mengatakannya terang-terangan. Hitung dulu di GC-Ex Drill
  Hole › Block Model › *Hitung proporsi volume ore per blok (sb_frac)*.
- **Blok berproporsi 0 tidak dilaporkan sama sekali** pada metode presisi. Jadi bila `sb_frac`
  hanya mencakup solid vein, baris *Presisi GC-Ex* melaporkan material **di dalam solid saja**,
  sedangkan baris *Seperti Surpac* melaporkan semua blok yang lolos constraint — termasuk waste di
  luar solid. Selisih bisa tampak −98% dan itu **wajar**, bukan tanda salah hitung. Perbandingan
  yang berarti: samakan dulu constraint domainnya di tab ②, lalu lihat selisihnya — yang tersisa
  barulah pengaruh aturan blok perbatasan. Panel menampilkan rincian berapa blok berproporsi 1,
  berapa di perbatasan, dan berapa berproporsi 0, supaya asal selisihnya terlihat.

## 89. Penampil 3D Qt tahap 2A — tampilan block model yang sama persis dengan aplikasi HTML

Penampil 3D Qt (ZIP ke-4 di Release, berdiri sendiri, tidak menggantikan apa pun) kini punya
**panel "Tampilan block model"** dengan kendali yang sama dengan panel di aplikasi HTML:

| Kendali | Perilaku |
| --- | --- |
| **Warnai berdasarkan** | atribut angka atau atribut kategori |
| **Kelas diskrit** | batas bawah ≤ nilai < batas atas; warna, batas, tambah/hapus kelas |
| **Kuantil** | batas bawaan dari kuantil 50 / 75 / 90 / 97 persen |
| **Pakai cut-off** | batas kelas ditulis manual, mis. `0.3, 0.5, 1, 2` |
| **Kategori** | centang = tampil, warna per nilai, jumlah blok per nilai |
| **Tampilkan bila (cut-off)** | atribut + `≥` / `<` + nilai |
| **Opasitas kubus**, **SG tetap**, **Kolom SG** | sama dengan panel HTML |

### Mengapa "sama persis" itu diuji, bukan dianggap

Kedua aplikasi akan dipakai **berdampingan** oleh orang yang sama. Kalau jumlah blok yang tampil
atau warnanya berbeda sedikit saja, yang terjadi bukan selisih selera tampilan melainkan dua
jawaban berbeda untuk pertanyaan yang sama. Karena itu aturannya tidak ditulis ulang dari ingatan:

- `qtbm/tampil_bm.py` menirukan `bxCls`, `bxClassOf`, `bxPass`, `bxLab` dan `bxDefUI` apa adanya —
  termasuk hal-hal yang kelihatan aneh: batas kelas dihitung dari data **tercuplik** (maksimum
  ±20.000 nilai), kuantilnya bukan interpolasi, dan batas yang sama setelah dibulatkan ke 2 angka
  berarti **dibuang**, sehingga jumlah kelas bisa kurang dari 5.
- `python tools/uji/paritas_tampil_bm.py` membuka **aplikasi HTML sungguhan** dengan data latihan,
  menjalankan `bxCls()` / `bxClassOf()` / `bxSel()` asli di dalamnya untuk 9 susunan panel, lalu
  membandingkan hasilnya blok demi blok dengan versi Python. Hasil terakhir: **semua sama persis**
  (4.135 blok cuplikan; termasuk kasus cut-off `≥` / `<`, batas kelas manual, dan kategori yang
  dilepas centangnya).
- Hasil JS itu dibekukan ke `qtbm/tests/data/tampil_bm_js.json` sehingga CI memeriksanya **tanpa
  peramban** setiap kali `qtbm/**` berubah.

Satu beda yang **disengaja**: pembulatan batas kelas memakai aturan JavaScript (nilai tepat setengah
dibulatkan **ke atas**: 1,25 → 1,3). Kalau ditulis dengan `'%.1e'` bawaan Python, hasilnya 1,2 —
dan batas kelas kedua aplikasi akan berbeda tanpa ada yang menyadarinya.

### Import block model Surpac `.mdl` langsung

Penampil tidak lagi meminta `.mdl` diekspor ke CSV dulu. Berkas `.mdl` dibaca lewat
`gcex_backend.mdl_io` — **modul yang sama** yang dipakai aplikasi, jadi tidak ada pembaca format
kedua yang bisa menyimpang. Yang perlu diketahui:

- Ukuran blok tidak ada di berkas per blok; `.mdl` menyimpan **octree**, jadi ukuran dihitung dari
  kotak akar dibagi 2^level — sama seperti di aplikasi.
- Pembacaan pertama sebuah berkas **membangun cache kolom** (sekali per berkas, bisa beberapa menit
  untuk model besar). Kemajuannya ditulis di panel. Berkas yang sudah pernah dibuka aplikasi
  langsung terbaca dari cache yang sama.
- Atribut **kalkulasi** (rumus `IIF(...)`) tidak tersimpan di berkas, jadi tidak muncul di penampil.

### Yang belum ada di tahap ini

Panel Sayatan/Slicing, Reporting Block Model, dan Dig block + digitasi string **belum** ada di
penampil Qt — semuanya masih dikerjakan di aplikasi HTML seperti biasa. Urutan pengerjaannya:
Reporting Block Model lebih dulu (mesin hitungnya sudah ada di
`backend/gcex_backend/laporan.py`), lalu Dig block + ekspor DXF/STR.

## 90. Penampil 3D Qt tahap 2B — tab Laporan Block Model

Penampil Qt kini punya dua tab di panel kanan: **Tampilan** (bagian 89) dan **Laporan**. Tab
Laporan menghitung tonase × kadar seperti Reporting Block Model di aplikasi HTML.

| Pilihan | Keterangan |
| --- | --- |
| **Atribut kadar (cut-off)** | atribut yang dipakai menyaring cut-off |
| **Cut-off** | daftar dipisah koma; tiap nilai dilaporkan sebagai **≥ nilai** |
| **Kelompokkan** | Total saja / **Per RL (bench / flitch)** / **Per atribut kategori** |
| **Tinggi bench + RL acuan** | bench dihitung dari RL acuan; label jadi `RL <atas> – <bawah>` |
| **Atribut yang dilaporkan kadarnya** | dicentang; tiap atribut dapat kolom kadar **dan kolom logam** |
| **Batasi ke saringan tampilan** | memakai batas RL + sayatan yang sedang tampil di layar |
| **Bandingkan metode tonase** | presisi GC-Ex vs seperti Surpac, berdampingan + baris Selisih |

Tabelnya bisa diekspor ke CSV, lengkap dengan keterangan metode di bawahnya.

### Angkanya dibuktikan sama dengan laporan aplikasi HTML

Mesin hitungnya **bukan** ditulis ulang: yang dipakai `gcex_backend.laporan.run()`, modul Python
yang sudah dibuktikan sama dengan `rpRun()` (bagian 87). Tetapi mesin yang benar masih bisa
dipanggil dengan **pilihan yang salah**, jadi lapisan Qt-nya diuji sendiri:
`python tools/uji/paritas_laporan_bm.py` membuka **aplikasi Block Model sungguhan**, menjalankan
`rpRun()` asli untuk **7 susunan pilihan** (SG tetap, kolom SG, beberapa atribut, per RL 5 m, per
RL 10 m dengan RL acuan 300, metode seperti Surpac, per kategori), lalu membandingkan jumlah blok,
volume, tonase dan kadar berbobot **per grup**. Hasil terakhir: **ketujuhnya sama persis** (3.007
blok cuplikan). Hasil JS dibekukan ke `qtbm/tests/data/laporan_bm_js.json` supaya CI memeriksanya
tanpa peramban.

### Dua hal yang ditemukan uji itu, dan sudah diperbaiki

**1. SG hanya punya satu sumber: panel Tampilan.** Di aplikasi HTML, Reporting BM mengambil SG dari
panel tampilan block model (`BX.ui.sg` / `BX.ui.sgCol`), bukan dari panel laporan. Rancangan awal
tab Laporan Qt punya kotak SG sendiri — artinya ada dua tempat mengisi SG dan tidak ada yang tahu
mana yang terhitung. Sekarang kotak SG di tab Laporan hanya **menampilkan** SG yang berlaku dan
dimatikan, dengan tulisan *"SG (dari panel Tampilan)"*.

**2. Kolom SG tidak dipilih otomatis.** Walaupun block model punya atribut bernama `SG`, bawaannya
tetap **SG tetap 2,6** — sama dengan aplikasi HTML (`bxDefUI` menyetel `sgCol` kosong). Memilih
kolom SG otomatis hanya di Qt akan membuat tonase bawaan kedua aplikasi berbeda untuk model yang
sama: selisih yang tidak akan dicari siapa pun, karena tidak ada yang merasa mengubah apa-apa.

### Peringatan yang harus dibaca bersama angkanya

- Bila block model **tidak punya atribut `sb_frac`**, metode presisi tidak punya apa pun untuk
  ditimbang, sehingga kedua metode menghasilkan angka **sama**. Panel mengatakannya terus-terang:
  selisih 0% di situ **bukan** bukti kedua cara cocok — modelnya belum pernah di-sub-blocking.
- Blok **berproporsi nol** tidak dilaporkan sama sekali oleh metode presisi, sedangkan metode
  Surpac tetap melaporkannya. Panel menyebutkan berapa blok yang begitu, karena itulah penyebab
  utama selisih yang tampak besar.
- Panel juga menulis **berapa blok terbuang di tiap tahap penyaringan** (di luar rentang RL, kadar
  tidak sah, SG tidak sah, proporsi nol), supaya pertanyaan "kenapa tonasenya sekian" ada
  jawabannya tanpa menebak.
- **Waste pengisi tidak termasuk** di laporan ini; itu hanya ada di perhitungan dig block per
  poligon (bagian 88). Keterangan ini ikut tercetak di CSV.

### RALAT: "kejanggalan satuan logam" yang pernah ditulis di sini TIDAK BENAR

Bagian ini sebelumnya menyatakan bahwa satuan kolom logam ditentukan dari awalan nama atribut
sehingga `CU_PPM` dianggap `%`, dan bahwa itu adalah perilaku aplikasi HTML yang sengaja ditiru
di Qt. **Keduanya salah.**

Diperiksa langsung di aplikasi yang berjalan: `rpUnitDef('CU_PPM')` mengembalikan **`'ppm'`**.
`rpUnitDef` memanggil `elUnit()` lebih dulu dan hanya jatuh ke regex cadangannya bila `elUnit`
mengembalikan string kosong — dan `elUnit` memeriksa `ppm` / `ppb` **sebelum** aturan awalan
unsur. **Aplikasi HTML benar sejak awal.**

Yang keliru adalah tiruan di penampil Qt (`qtbm/laporan_bm.satuan()`): ia menyalin regex
cadangannya saja, tanpa `elUnit`. Akibatnya nyata — untuk 1.000 t @ 50 ppm:

| | CU_PPM | Hasil |
| --- | --- | --- |
| Aplikasi HTML | `ppm` | 50.000 gram (50 kg) — benar |
| Penampil Qt (sebelum ralat) | `%` | 500 "t logam" — salah **10.000 kali** dan salah satuan |

Pada data latihan, dua dari lima atribut terkena (`CU_PPM`, `ZN_PPM`).

**Mengapa tidak tertangkap:** uji di `qtbm/tests/test_laporan_bm.py` menuliskan `("CU_PPM", "%")`
sebagai nilai yang diharapkan — nilai itu diambil dari bacaan saya atas kodenya, bukan dari
aplikasi. Ujinya lulus sambil **melindungi** bug-nya. Uji yang memuat keyakinan keliru lebih buruk
daripada tidak ada uji, sebab ia memberi rasa aman.

**Sudah diperbaiki:** `satuan()` kini meniru rantai lengkapnya (elUnit dulu, baru regex cadangan),
dan `tools/uji/paritas_laporan_bm.py` membandingkan satuan **43 nama atribut** terhadap `elUnit()`
asli di aplikasi — banyak nama, supaya URUTAN aturannya ikut teruji, bukan satu-dua contoh. Ada
penjaga agar daftarnya selalu memuat atribut ppm: tanpa itu, aturan yang pernah salah tidak
teruji sama sekali.

### Yang belum ada

Panel Sayatan/Slicing belum ada di penampil Qt. Dig block sudah ada — lihat bagian 91.


## 91. Penampil 3D Qt tahap 2C — tab Dig block, digitasi plan 2D, dan ekspor DXF/STR

Penampil Qt kini punya tab ketiga: **Dig block**. Di tab ini poligon galian digambar langsung di
atas block model, tonasenya dihitung, dan hasilnya diekspor ke DXF atau Surpac `.str`.

### Mengapa digitasinya di plan 2D, bukan di tampilan 3D

Dig block adalah poligon pada **satu bidang datar** (flitch). Mengklik titik di tampilan 3D yang
bisa diputar berarti menebak kedalaman di balik piksel: satu derajat kemiringan kamera menggeser
titiknya beberapa meter dan tidak ada yang akan tahu. Karena itu tab Dig block mengganti viewport
menjadi **plan 2D dengan RL terkunci** pada flitch yang aktif, satu piksel selalu berarti jarak
yang sama di lapangan, dan RL flitch selalu tertulis di sudut kanvas. Aplikasi HTML pun begitu —
`dgStart()` memaksa pindah ke Sayatan 2D sebelum digitasi dimulai.

### Kendali

| Kendali | Perilaku |
| --- | --- |
| **RL atas / RL bawah** | Batas flitch. Tombol *Flitch berikut ke bawah* menggeser keduanya satu tebal flitch. |
| **Cara ambil blok** | *Tumpang tindih sebenarnya* (composite) atau *hanya blok di bidang tengah* — yang kedua menghitung blok setebal flitch penuh walau bloknya lebih tipis. |
| **Atribut kadar** | Kadar yang dirata-rata berbobot tonase, dan dasar kolom logam. |
| **Metode tonase** | *Presisi GC-Ex* (blok dipotong di garis poligon dan bidang flitch) atau *Seperti Surpac* (blok ikut **utuh** bila titik tengahnya di dalam poligon dan flitch). |
| **Bandingkan kedua metode** | Dua kolom tonase berdampingan + kolom Selisih %. |
| **Hanya blok yang lolos cut-off tampilan** | Ikut cut-off panel Tampilan (`lyU().onlyPass`). |
| **Waste pengisi** | Dilusi untuk luas poligon yang tidak tertutup blok. **Bawaannya menyala**, sama dengan aplikasi HTML. |
| **Tempel ke sudut blok** | Titik klik menempel ke sudut / titik tengah blok terdekat, supaya garis galian jatuh di batas blok. |
| Papan ketik saat mendigit | **Enter** tutup poligon · **Backspace** urung titik · **Esc** batal. Klik titik pertama juga menutup poligon. |

Tetikus di kanvas 2D: **klik kiri** menaruh titik, **klik kanan / tengah + geser** memindahkan
pandangan, **roda** memperbesar berpusat di kursor. Ada batang skala di kiri bawah — tanpa itu
tidak ada cara menilai ukuran poligon dari gambarnya saja.

### Angkanya dibuktikan, bukan diklaim

Mesin dig block **tidak ada** di `gcex_backend`: ia tiruan `lyTon()` (presisi) dan `lyTonS()`
(Surpac) di aplikasi HTML, ditulis ulang di Python (`qtbm/galian.py`). Karena itu seluruh
perilakunya harus dibuktikan, bukan dipercaya. `tools/uji/paritas_galian_bm.py` membuka
**aplikasi Block Model sungguhan** dengan data latihan dan menjalankan `lyTon()` **asli** untuk
**21 susunan**: poligon dengan garis di batas blok dan di tengah blok, poligon segi lima, flitch
setebal 1 / 3 / setengah blok, mode bidang tengah, poligon lubang (*exclusion*), kolom SG, cut-off
tampilan, dan waste pengisi. Semua **sama persis**. Isi berkas `.str` dan `.dxf` juga dibandingkan
**baris per baris** dengan keluaran `dgExport()` asli. Hasil JS dibekukan ke
`qtbm/tests/data/galian_bm_js.json` supaya CI memeriksanya tanpa peramban.

### Tiga hal yang bisa membuat kedua aplikasi diam-diam berbeda — sudah ditutup

**1. Waste pengisi bawaannya MENYALA.** `dbU()` di aplikasi HTML menyetel `U.wOn = true` bila
belum pernah disentuh. Kalau di Qt dibuat mati, tonase dig block bawaan akan lebih kecil untuk
poligon yang sama, dan tidak ada yang merasa mengubah apa pun.

**2. Perlakuan blok yang kolom SG-nya kosong / nol** (`sgZero` / `sgRep`) belum diteruskan panel
Laporan ke mesin hitungnya, walau mesinnya sudah mendukung. Sekarang ikut, dan sumbernya tetap
satu: panel Tampilan. Tab Dig block **tidak punya kotak SG sendiri** — hanya menampilkan SG yang
berlaku.

**3. Dua ruang koordinat.** Aplikasi HTML menyimpan koordinat block model secara **penuh**
(`BX.m.x`) tetapi titik hasil digitasi **relatif offset** (`DG.S[].pts`), sehingga `lyItems()`
harus menambahkan offset sebelum menghitung dan `dgExport()` menambahkannya lagi saat menulis
berkas. Tertukar satu kali saja, berkasnya tetap terbaca Surpac dan tidak memunculkan galat apa
pun — poligonnya saja yang berada ratusan kilometer dari tempatnya. Penampil Qt **tidak menyalin
pembagian itu**: satu ruang koordinat saja, sehingga kelas kesalahan itu tidak ada.

### Asimetri yang ditiru apa adanya

**Waste pengisi hanya ditambahkan pada metode presisi.** Di aplikasi HTML, `lyTonS()` memang tidak
pernah menambahkannya, jadi baris waste hilang begitu metode diganti ke Surpac. Itu perilaku
aplikasi resmi dan sengaja dipertahankan; panel mengatakannya di bawah pilihan waste dan dalam
catatan di bawah tabel, supaya selisih antara dua kolom tidak disalahartikan sebagai perbedaan
cara memotong blok saja.

### Peringatan yang ikut ditampilkan bersama angkanya

- **Berapa persen luas poligon yang tertutup blok.** Sisanya tidak punya blok sama sekali dan
  tonasenya tidak terhitung kecuali waste pengisi dinyalakan.
- Bila mode **bidang tengah** dipakai: volume bisa lebih besar daripada volume blok sebenarnya.
- Berapa persen tonase yang **tidak punya kadar sah** dan karena itu tidak ikut rata-rata kadar —
  tonasenya tetap dilaporkan.
- Bila kedua metode memberi angka **sama persis** pada satu poligon, panel menyatakan itu bisa
  terjadi karena poligonnya jatuh tepat di garis blok, dan **bukan** bukti umum bahwa kedua cara
  selalu cocok.

### Uji otomatis

`qtbm/tests` naik dari 96 ke **178 uji**. Termasuk dua penjaga agar ujinya tidak lulus palsu: bila
ketiga kasus kolom SG memberi angka identik, atau tidak satu pun kasus membedakan kedua metode,
ujinya **gagal**. Penjaga itu sudah terpakai sekali — kolom SG data latihan tidak punya satu pun
nilai tidak sah, sehingga cabang `sgZero` / `sgRep` semula tidak teruji sama sekali dan ujinya
lulus tanpa menguji apa pun.

Uji mandiri `.exe` di CI kini ikut menjalankan dig block **dan ekspornya**, sebab mesinnya harus
benar-benar **terkemas**: kalau yang gagal adalah ekspornya, yang dibawa ke lapangan adalah berkas
kosong, dan itu baru ketahuan di lapangan.

### Yang belum ada di tab Dig block

Aturan material otomatis (`dbRule` / HG-LG / tujuan dump), *minimum mining width*, dig block
otomatis dari badan bijih, poligon lubang dari antarmuka (mesinnya sudah mendukung, panelnya
belum), penyimpanan string ke folder proyek, dan cetak peta oreblock PDF. Semua itu masih hanya
ada di aplikasi HTML.


## 92. Penampil Qt — dua perbaikan kecil di tab Dig block

### Keputusan: selisih metode tonase TIDAK ditampilkan secara bawaan

Pemilik menyatakan selisih luasan / tonase / kadar sangat berdampak pada kepercayaan karena
perangkat lunak yang diakui adalah Surpac, dan bahwa block model kerjanya **tidak punya**
atribut proporsi `sb_frac`. Sempat dibuat agar angka kedua metode selalu tampil berdampingan;
pemilik kemudian meralat: **tetap presisi, selisihnya tidak perlu ditampilkan.** Perubahan itu
dibatalkan seluruhnya — aplikasi HTML kembali ke keadaan sebelumnya (modul `digband.js` dicabut,
versi Block Model kembali ke 0.24.25 karena isi installernya tidak berubah), dan di penampil Qt
pilihan *"Tampilkan juga angka metode satunya"* tetap ada tetapi **mati** secara bawaan.

Catatan yang perlu diingat kalau topik ini dibuka lagi: tanpa `sb_frac`, Reporting BM memang
memberi angka identik untuk kedua metode sehingga pilihan metode di laporan tidak berdampak —
tetapi di **dig block** selisihnya bersifat **geometris** (blok dipotong di garis poligon versus
blok ikut utuh bila titik tengahnya di dalam), jadi ia **tetap ada walau model tanpa `sb_frac`**.
Pada uji paritas: −9,6% bila garis poligon tepat di batas blok, −0,1% bila di tengah blok, −0,9%
pada poligon segi lima, −17,9% bila ada poligon lubang, dan kadarnya ikut bergeser (0,2763 vs
0,2629). Angka itu dicatat di sini supaya tersedia bila nanti dibutuhkan, bukan untuk menyalakan
kembali tampilannya tanpa diminta.

### Dua cacat yang diperbaiki

- Tombol **"Tutup & simpan"** diganti menjadi **"Tutup poligon"**, dan judul daftarnya menjadi
  *"String di sesi ini (belum tersimpan ke berkas)"*. Label lama menyesatkan: yang terjadi
  hanyalah poligon masuk daftar di panel — belum ada apa pun yang tersimpan ke berkas.
- Menutup jendela saat masih ada string yang belum diekspor sekarang **memunculkan peringatan**.
  Penyimpanan ke folder proyek belum ada, sehingga menutup jendela benar-benar menghilangkan
  string; selama penyimpanan itu belum dibuat, setidaknya pekerjaannya tidak hilang tanpa
  pemakai diberi tahu.


## 93. Penampil Qt — string dig block tersimpan di folder proyek

### Cacat yang ditutup

Sebelum ini, string dig block di penampil Qt hanya ada selama jendela terbuka. Menutup aplikasi
menghilangkan semuanya, tanpa peringatan apa pun. Seorang junior yang mendigit 20 dig block lalu
menutup penampil kehilangan satu shift pekerjaan.

### Keputusan: Qt TIDAK menulis ke `gcex_project.json`

`gcex_project.json` dijaga protokol yang cukup rumit di aplikasi HTML: berkas kunci
(`gcex.lock`) yang menyatakan siapa sedang membuka proyek, nomor revisi `rev` untuk mendeteksi
konflik antar pemakai, cadangan otomatis ke `backup/` dan `backup/harian/`, serta hash isi. Kalau
penampil Qt — yang masih berstatus percobaan — menulis ke situ dan satu bagian protokol itu
terlewat, yang rusak adalah berkas proyek yang sedang dipakai orang lain. Harga kesalahan itu
jauh lebih besar daripada manfaat menulis langsung.

Karena itu pembagiannya:

| Berkas | Perlakuan penampil Qt |
| --- | --- |
| `gcex_project.json` | **hanya dibaca** — untuk mengambil string yang dibuat aplikasi HTML. Tidak pernah ditulis, tidak pernah dikunci. |
| `gcex_dig_qt.json` | **berkas Qt sendiri**, di folder proyek yang sama. Di sinilah string Qt disimpan. |

**Akibat yang harus diketahui:** string yang dibuat di Qt **belum** otomatis muncul di aplikasi
HTML. Untuk itu aplikasi HTML perlu diajari membaca berkas pendamping ini, dan itu perubahan pada
aplikasi produksi yang menunggu keputusan pemilik.

### Yang bisa dilakukan di panel

- **Simpan ke folder proyek** — menulis `gcex_dig_qt.json`. Simpan juga berjalan **otomatis**
  setiap kali daftar string berubah dan saat jendela ditutup.
- **Ambil string dari aplikasi HTML** — menambahkan string dari `gcex_project.json`. Sengaja
  **menambah, bukan mengganti**: mengganti berarti membuang pekerjaan yang mungkin belum
  tersimpan. Nomor string yang sudah dipakai dilewati supaya tidak ada dua string bernomor sama.
- Peringatan di panel hanya muncul bila memang ada yang bisa hilang: tanpa folder proyek, atau
  ada perubahan yang belum tersimpan.

### Dua hal yang bisa salah TANPA memunculkan galat — dan cara keduanya dijaga

**1. Offset koordinat.** Aplikasi HTML memakai dua ruang koordinat: block model memakai koordinat
penuh, tetapi titik hasil digitasi (`DG.S[].pts`) tersimpan **relatif** terhadap `offX`/`offY`.
Offset itu dihitung dari **koordinat collar** — minimum easting / northing, dibulatkan ke bawah
ke ribuan; bila tidak ada collar dipakai `anch` dari berkas data; bila itu pun tidak ada, nol.
Salah hitung satu kali saja memindahkan poligon ratusan kilometer: berkasnya tetap sah, gambarnya
saja kosong. `Proyek.offset()` menyalin rumus itu, dan diuji terhadap `offX`/`offY` aplikasi
sungguhan (data latihan: 504000 / 9011000 dari 610 collar), termasuk kasus tanpa collar, kasus
`anch` dikalahkan collar, dan pembulatan **ke bawah** untuk koordinat negatif (−1234 → −2000,
bukan −1000). Offset yang dipakai saat membaca adalah yang **tersimpan di berkas**, bukan yang
dihitung ulang — sehingga bila data bor proyek berubah dan offsetnya ikut berubah, string lama
tetap kembali ke tempat yang benar.

**2. Hash isi berkas.** Berkas proyek GC-Ex memakai hash `FP.hash` untuk memeriksa keutuhan isi.
Salinan Python-nya harus sama persis, kalau tidak berkas yang ditulis Qt dianggap rusak oleh
pihak mana pun yang memeriksanya. Hal yang mudah terlewat: JavaScript bekerja pada **satuan kode
UTF-16** (`charCodeAt`, `s.length`), jadi satu emoji di keterangan string menjadi **dua** satuan
kode. Salinan Python menghitungnya sama, dan diuji terhadap `FP.hash` asli untuk delapan teks
termasuk emoji, tab, baris baru dan tanda kutip — semuanya cocok.

### Yang diuji

`tools/uji/paritas_simpan_galian.py` membuka aplikasi Block Model sungguhan dan membandingkan:
`FP.hash` (8 teks), `offX`/`offY`, serta pembacaan berkas `gcex_project.json` **asli** yang dibuat
`FP.pack` + `SA.collectWork` di dalam aplikasi — bukan berkas tiruan, sebab berkas tiruan hanya
membuktikan Python cocok dengan dugaan Python. Ditambah uji bolak-balik berkas Qt, dan satu
pemeriksaan tegas bahwa `gcex_project.json` **tidak berubah satu byte pun** setelah Qt menulis.
Hasil JS dibekukan ke `qtbm/tests/data/simpan_galian_js.json` (2 KB) untuk CI.

Perilaku saat berkas rusak juga diuji dan sengaja dipilih: berkas string Qt yang rusak
**tidak dihapus dan tidak ditimpa** — pemakai mungkin masih bisa menyelamatkan isinya sendiri;
yang terjadi hanya tidak dimuat, dan itu dikatakan. Sebaliknya, `gcex_project.json` yang rusak
tidak melempar galat sama sekali: gagal membaca pekerjaan orang lain tidak boleh menghalangi
pemakai memakai penampilnya.

Penulisan memakai berkas sementara lalu ganti nama. Itu bukan kehati-hatian berlebihan: kalau
aplikasi mati di tengah penulisan langsung, yang tertinggal adalah berkas separuh jadi — dan
string yang hilang justru pekerjaan yang hendak diselamatkan berkas ini.

Uji mandiri `.exe` di CI ikut menulis lalu membaca string dan memeriksa koordinatnya kembali
**tepat**, serta memeriksa hash-nya cocok dengan `FP.hash`. **216 uji otomatis** di `qtbm/tests`.


## 94. Block Model 0.24.26 — string dig block Qt terbaca di aplikasi HTML, dan cap versi dijaga CI

### String dig block jadi dua arah

Sebelum ini alirannya satu arah: string yang dibuat di aplikasi HTML terlihat di penampil Qt,
tetapi string yang dibuat di Qt tidak terlihat di aplikasi HTML. Pemakai yang mendigit di Qt lalu
ingin mencetak peta oreblock, memakai aturan material HG/LG, atau as-mined akan menemui daftar
kosong tanpa penjelasan — sebab hal-hal itu hanya ada di aplikasi HTML.

Panel **Dig block** aplikasi HTML sekarang punya tombol **⇩ Ambil string dari penampil 3D Qt**,
yang membaca `gcex_dig_qt.json` di folder proyek. Pembagian berkasnya tetap seperti sebelumnya
dan sengaja tidak diubah:

| Berkas | Ditulis oleh | Dibaca oleh |
| --- | --- | --- |
| `gcex_project.json` | aplikasi HTML | aplikasi HTML + penampil Qt |
| `gcex_dig_qt.json` | penampil Qt | penampil Qt + **aplikasi HTML (baru)** |

Penampil Qt tetap **tidak** menulis ke `gcex_project.json`, karena berkas itu dijaga berkas kunci,
nomor revisi dan cadangan otomatis (lihat bagian 93).

**Menambah, bukan mengganti.** Daftar string yang sudah ada tidak pernah ditimpa: menimpa berarti
membuang pekerjaan yang mungkin belum tersimpan. String yang isinya sudah ada dilewati, dan nomor
yang sudah terpakai diganti nomor berikutnya supaya tidak ada dua string bernomor sama. Menekan
tombolnya dua kali tidak melipatgandakan apa pun — ini diuji.

### Hal yang paling mudah salah: offset

Titik digitasi tersimpan **relatif** terhadap `offX`/`offY`, dan offset itu dihitung dari
koordinat collar proyek. Berkas Qt mencatat offset yang dipakainya saat menulis. Kalau kemudian
ada collar baru di barat atau selatan yang menggeser nilai minimum, offset aplikasi **berbeda**
dari yang tercatat di berkas. Karena itu titiknya digeser sebesar selisih kedua offset, bukan
dipakai apa adanya. Tanpa penggeseran itu poligon pindah ribuan meter dan **tidak ada galat apa
pun yang muncul** — hanya poligon kosong di tempat yang salah.

Penggeserannya **dikatakan** kepada pemakai ("koordinat digeser −3000 / +2000 m karena offset
proyek berbeda dari saat berkas Qt ditulis"), sebab tanpa itu tidak ada cara mengetahui bahwa
koordinatnya disesuaikan, dan tidak ada cara menilai apakah penyesuaian itu wajar.

Diuji di aplikasi sungguhan: berkas `gcex_dig_qt.json` yang **ditulis oleh Python** dibaca oleh
`dgQtImport()` **asli** di dalam aplikasi, untuk dua kasus — offset sama dan offset berbeda. Pada
kasus kedua berkas menyimpan titik (3100,5; −1799,75) sementara aplikasi memulihkannya menjadi
(100,5; 200,25), yaitu tempat nyata yang sama. Penjaga ujinya memeriksa bahwa titik **di dalam
berkas** benar-benar berbeda antara kedua kasus — kalau sama, penggeseran tidak pernah diperlukan
sehingga tidak teruji.

Satu bug ditemukan oleh uji ini dan sudah diperbaiki: `esc()` milik aplikasi tidak terjangkau dari
lingkup modul, sehingga `dgQtImport` melempar galat **setelah** string tergabung — pemakai akan
melihat pesan galat padahal pekerjaannya sudah masuk. Pelolosan karakternya tidak dibuang,
melainkan diganti pelolos sendiri di dalam modul: keterangan string dan waktu simpan datang dari
berkas, yaitu masukan dari luar.

### Cap versi sekarang dijaga CI

CI **tidak** menjalankan `web-src/build.py` — berkas `app*/index.html` yang ada di repo itulah
yang dikemas. Jadi menaikkan versi tanpa membangun ulang berkas HTML-nya membuat aplikasi
melaporkan versi **lama**, dan tidak ada apa pun yang menolak.

Itu sudah pernah terjadi: pada commit `d717474` Block Model dinaikkan ke 0.24.25 dan Drill Hole ke
0.24.35 tanpa dibangun ulang, sehingga aplikasi yang beredar mencap dirinya **0.24.24** dan
**0.24.34** selama beberapa rilis. Tidak ada fitur yang rusak — nomor itu hanya dipakai untuk
tampilan dan untuk kolom `versi` di tabel `sinkron` basis data proyek — tetapi tabel itulah jejak
resmi siapa mengerjakan apa dengan versi apa, dan baris riwayat tidak pernah diperbaiki lagi.

Dua hal dikerjakan:

1. **Cap keduanya dibetulkan.** Block Model dibangun ulang bersama perubahan ini dan naik ke
   **0.24.26**, jadi tidak ada nomor versi yang terbuang hanya untuk membenarkan cap. Drill Hole
   dibangun ulang dan capnya menjadi **0.24.35** — versinya **tidak** dinaikkan, karena yang
   berubah hanyalah cap yang menyusul nomor yang memang sudah diumumkan di rilis sebelumnya,
   bukan perubahan isi aplikasi. Pengaman `kemas_rilis.py --cek` tetap lulus.
2. **Pemeriksaan CI baru** `tools/rilis/cek_cap_versi.py` membandingkan `window.GCEX_VER` di dalam
   tiap berkas HTML dengan versi yang dinyatakan di `package.json` / `builder-dh.json` /
   `builder-core.json`, dan **menggagalkan build** bila tidak cocok. Berjalan di awal, sebelum
   apa pun dibangun. Aplikasi yang tidak menanamkan cap dilaporkan sebagai "tidak bisa diperiksa",
   bukan didiamkan seolah lulus.

Pemeriksaan itu sendiri diuji dengan sengaja merusak cap satu aplikasi: ia memang gagal dengan
kode keluar 1 dan menyebut berkas serta nomor yang bersangkutan. Pemeriksaan yang belum pernah
terbukti bisa gagal tidak membuktikan apa pun.

**218 uji otomatis** di `qtbm/tests`.


## 95. Penampil Qt — tab Sayatan

Penampil Qt kini punya tab keempat: **Sayatan**. Kendali sayatan ad-hoc yang dulu ada di bilah
sisi (slab tegak berazimut) **dicabut**, karena ia memakai uji titik tengah blok dan azimut saja
sehingga memilih blok yang berbeda dari aplikasi HTML pada pengaturan yang sama — dan karena ada
dua tempat yang bisa membatasi sayatan. Sekarang definisinya **satu**, dipakai bersama oleh panel
Tampilan, Laporan dan Dig block.

### Hanya dua mode, sengaja

| Mode | Posisi diukur sebagai |
| --- | --- |
| **Horizontal (plan per elevasi)** | RL |
| **Garis manual (vertikal / miring)** | jarak dari titik 1, dengan dip dan pilihan batas ruas |

Fungsi `secGeom` di aplikasi HTML juga memuat mode X, Y dan A, tetapi pilihan *Arah potongan* di
aplikasi **Block Model** hanya menawarkan `H` dan `P` — ketiga mode lain **tidak bisa dicapai dari
antarmukanya**. Menawarkannya di penampil Qt berarti memberi angka yang tidak bisa diperiksa
terhadap apa pun. Ada uji yang menjaga daftar mode panel tetap H dan P, sehingga menambah mode
baru memaksa keputusan paritas lebih dulu, bukan diam-diam.

### Kendali

Arah potongan, **Potong data** (hanya blok di dalam slab), posisi (slider + kotak angka), tebal
slab, dan untuk garis manual: dip, titik 1 dan titik 2 (easting/northing penuh), batas sepanjang
ruas, serta perpanjangan ujung. Tombol *Pas ke tengah model* dan — pada mode horizontal — *Geser
satu tebal ke bawah* untuk menyusuri bench satu per satu. Panel menulis keterangan sayatan yang
aktif beserta **jumlah blok di dalam slab**, dan mengatakan terus-terang bila nol.

Catatan kecil yang disengaja: slider **tidak menjepit** kotak angkanya. Di aplikasi HTML `pos`
adalah slider yang menjepit nilainya, dan itu sempat membuat uji paritas menyetel 0 lalu mendapat
127 tanpa tanda apa pun.

### Tiga hal yang bisa salah TANPA galat — dan cara ketiganya dijaga

**1. Uji kotak, bukan uji titik tengah.** Aplikasi HTML (`bxSlabHit`) menguji blok sebagai
**kotak**: setengah rentang blok diproyeksikan ke normal bidang (`r = (sx·|nx| + sy·|ny| +
sz·|nz|)/2`), lalu blok ikut bila rentang `[d−r, d+r]` bersinggungan dengan slab. Memakai titik
tengah membuat slab yang lebih tipis daripada satu blok hampir tidak memilih apa pun. Bedanya
besar: pada data latihan, slab setebal satu blok memilih **164 blok** dengan uji kotak dan hanya
**63** dengan uji titik tengah. Kedua jalur disediakan dan diuji terpisah (`dalam_slab` dan
`dalam_slab_titik`), sebab aplikasi HTML sendiri memakai titik tengah di tempat lain — metode
tonase "seperti Surpac".

**2. RL pusat bidang pada sayatan miring.** `secGeom` memakai `(G.z0 + G.z1)/2`, yaitu tengah
kotak **data bor** (collar dan ujung lubang), **bukan** tengah block model. Pada dip 90 ini tidak
berpengaruh karena normal bidang tidak punya komponen z — tetapi pada dip lain bidangnya bergeser
dan blok yang terpilih berbeda. Itulah sebabnya kasus dip 90 lulus sejak awal sementara dip 70 dan
45 tidak, sampai sumbernya ditemukan. `Proyek.rl_data()` menyalin perhitungan itu, panel
**menyebutkan nilai yang sedang dipakai**, dan bila proyek tidak punya data bor panel mengatakan
bahwa keduanya bisa berbeda sehingga sayatan miring akan bergeser.

**3. Ruang koordinat.** Aplikasi HTML menaruh pusat bidang mode X di `c = [-offX, 0, 0]` supaya
`pos` tetap berupa easting penuh pada koordinat internalnya. Penampil Qt memakai koordinat penuh
sejak awal, jadi pusatnya `[0, 0, 0]` dan `pos` langsung easting penuh — hasilnya sama. Menyalin
`[-offX, 0, 0]` ke sini akan menggeser bidangnya dua kali.

### Yang diuji

`tools/uji/paritas_sayatan_bm.py` membuka aplikasi Block Model sungguhan dan menjalankan `secK()`
+ `bxSlabHit()` **asli** untuk **12 susunan** (horizontal dengan tebal 10 m, setebal satu blok,
0,2 m, tepat di batas blok, dan di luar model; garis manual dengan dip 90 / 70 / 45, offset 30,
dibatasi ruas, dengan perpanjangan 40 m, dan ruas pendek). Yang dibandingkan adalah **blok mana
yang terpilih** — bukan parameter bidangnya — sebab itulah yang dilihat pemakai dan itu kebal
terhadap perbedaan cara menuliskan pusat bidang. Keduabelasnya **sama persis**, pada kedua jalur
(uji kotak dan uji titik tengah).

Tiga bug ditemukan dan diperbaiki dalam prosesnya, dua di antaranya milik harness ujinya sendiri:
panjang ruas dihitung lalu **tidak diteruskan** ke hasil bidang (bug kode); `pos` disetel 0 tetapi
dijepit slider menjadi 127 (bug harness); dan mode `X` disetel ke pilihan yang tidak memilikinya
sehingga `secGeom` jatuh ke cabang miring dengan azimut 0 (bug harness, dan inilah yang menyingkap
bahwa mode X / Y / A tidak bisa dicapai dari antarmuka).

Penjaga agar ujinya tidak lulus palsu: bila tidak ada satu pun kasus di mana uji kotak dan uji
titik tengah berbeda, ujinya **gagal**; dan bila daftar mode di aplikasi berubah, ujinya juga
gagal dengan menyebut daftar barunya.

Uji mandiri `.exe` di CI ikut memeriksa bahwa uji kotak memilih lebih banyak blok daripada uji
titik tengah — kalau sama, uji kotak hilang dari kemasan. **252 uji otomatis** di `qtbm/tests`.


## 96. Block Model 0.24.27 — atap (roof) as-mined dari pick-up survey

### Masalah yang ditutup

Dalam satu flitch (mis. RL240–RL238,5), elevasi atap dan lantai penggalian **tidak pernah tepat**
di RL nominalnya. Lantainya sudah ditangani sejak sebelumnya: pilihan *Ikuti lantai pick-up*
menginterpolasi lantai tiap poligon dari titik pick-up. **Atapnya belum** — `amRun` memakai
`B[0]`, yaitu RL atas flitch nominal, ditulis mati di kodenya.

Akibatnya **sistematis dan selalu berlebih**, jadi tidak saling menghapus antar flitch melainkan
menumpuk. Kalau atap sebenarnya ada di 239,78 sementara nominalnya 240,00, setiap poligon
kelebihan 0,22 m setebal seluruh luasnya: pada poligon 2.000 m² itu 440 m³ ≈ 1.100 t ore yang
tidak pernah digali.

### Alurnya sekarang

1. **Impor titik pick-up ATAP** — pick-up dig block / poligon ore actual yang dipasang **hari
   sebelumnya**. CSV XYZ format Surpac, atau `.str` / `.dxf`.
2. **Impor titik pick-up LANTAI** — pick-up lantai penggalian satu shift (seperti sebelumnya).
3. Digitasi boundary, lalu hitung as-mined. Batas atas sub-blok mengikuti atap, batas bawahnya
   mengikuti lantai.

### Titik atap dan titik lantai disimpan TERPISAH

`amD().ptsR` untuk atap, `amD().pts` untuk lantai, dengan tombol impor masing-masing. Keduanya
**tidak** dipisahkan dari elevasinya — memisahkan dari elevasi justru mustahil diandalkan, sebab
seluruh sebab fitur ini ada adalah karena elevasinya tidak pasti. Kalau keduanya tercampur dalam
satu awan titik, atap dan lantai akan diinterpolasi dari titik yang sama dan volumenya salah
**tanpa tanda apa pun**.

Pengurai kolom CSV-nya **satu**, bukan dua: `amPtsFile(files, slot)` diberi parameter slot alih-alih
disalin menjadi fungsi kedua — kalau disalin, perbaikan pengenalan kolom pada salah satunya tidak
akan ikut ke yang lain.

### Dua bentuk atap

| Pilihan | Perilaku |
| --- | --- |
| **RL atas flitch (nominal)** | rumus lama, **tetap bawaan** |
| **Atap rata dari pick-up** | satu elevasi per poligon, dari titik atap di dalam / dekat poligon itu |
| **Atap ikut permukaan pick-up** | IDW pangkat 2, sama dengan lantai — untuk atap yang memang tidak rata |

### Median, bukan rata-rata — tetapi keduanya ditampilkan

Satu titik salah tembak (di berm, atau dari flitch sebelahnya) menggeser rata-rata; median tidak.
Jadi bawaannya **median**, dengan rata-rata sebagai pilihan. Yang lebih penting: **keduanya
ditampilkan berdampingan**, dan bila berbeda lebih dari 5 cm panel memperingatkan bahwa awan
titiknya kemungkinan berisi outlier atau atapnya sebenarnya tidak rata — dan menyarankan mode
*ikut permukaan*. Selisih itu adalah **tanda**, bukan hiasan; menyembunyikannya berarti
menyembunyikan mutu datanya.

### Kalau lantai menembus atap

Dengan atap rata dan lantai bergelombang, ini **akan** terjadi — entah karena underdig nyata atau
karena titik dari hari / flitch yang salah. Tebalnya dihitung **nol** di situ, **dan luas yang
terjepit itu dilaporkan di panel** dengan peringatan. Menjepit tanpa memberi tahu akan
menyembunyikan masalah survei sebagai angka yang kelihatan wajar.

### Poligon tanpa titik atap

Kurang dari 3 titik atap di dalam / dekat poligon → poligon itu memakai **RL atas flitch nominal**,
dan itu **disebutkan**. Flitch pertama yang digali memang tidak punya pick-up hari sebelumnya;
tanpa disebutkan, tidak ada cara membedakan atap hasil survei dari atap asumsi.

### Yang diuji — dan mana yang lebih penting

`tools/uji/uji_atap_asmined.py` menjalankan **dua versi aplikasi berdampingan**: versi pembanding
diambil dari git (`--dasar`, bawaan `HEAD`) sehingga ujinya bisa diulang siapa pun, bukan hanya di
mesin yang menyimpan salinannya.

**1. Tidak ada angka lama yang berubah** — ini yang lebih penting. Dengan bawaan
(`roof = 'flitch'`), hasil as-mined versi baru harus sama persis dengan versi sebelum perubahan.
Delapan ukuran dibandingkan (volume, tonase, jumlah sub-blok, terestimasi, warisan, sel, luas,
volume poligon) dan semuanya **identik sampai digit terakhir** — 7.159,455128214322 m³ di kedua
versi. Perubahan yang menggeser angka produksi tanpa ada yang meminta adalah kerusakan, bukan
peningkatan.

**2. Mode atap mengubah angka ke arah yang benar** — atap 0,22 m di bawah RL nominal pada flitch
2,50 m memberi volume **−8,80%**, tepat sesuai 0,22 / 2,50. Mode rata dan mode permukaan memberi
angka identik ketika semua titiknya memang rata, seperti seharusnya.


### Sel pecahan: kolom FRAKSI / VOLUME dan selisih yang ditampilkan

Di dalam GC-Ex, sel yang hanya terisi sebagian dihitung dengan fraksinya: `v = dx·dy·dz × f`.
Volume dan tonasenya benar. **Tetapi saat diekspor, sel itu ditulis sebagai blok PENUH** — octree
`.mdl` tidak punya konsep sel pecahan, dan CSV menulis `DX,DY,DZ` ukuran grid penuh.

Akibatnya siapa pun yang menghitung ulang volume dari dimensi blok — di Surpac, misalnya, saat
rekonsiliasi — akan mendapat angka **lebih besar** daripada yang dilaporkan GC-Ex. Pada data
latihan (grid 5×5×2,5 m, 125 sel):

| | Volume GC-Ex | Dihitung ulang dari dimensi blok | Selisih |
| --- | --- | --- | --- |
| Atap nominal | 7.159,46 m³ | 7.812,50 m³ | +9,1% |
| Atap rata dari pick-up | 6.529,42 m³ | 7.812,50 m³ | +19,7% |

Sebelum fitur atap, sel pecahan hanya ada di **tepi poligon**. Sekarang atap dan lantai juga
menghasilkannya, dan itu mengenai **seluruh luas poligon** — jadi fitur atap ini sendiri yang
memperbesar selisihnya dari 9% ke 20%.

Dua hal dikerjakan supaya selisih itu **terlihat**, bukan ditemukan orang lain saat rekonsiliasi:

1. **Kolom `FRAKSI` dan `VOLUME`** ditambahkan ke ekspor *Sub-blok CSV* (`amCells`) dan ke ekspor
   model gabungan (`am3Csv`). `FRAKSI` = bagian sel yang benar-benar terisi; `VOLUME` = volume
   sebenarnya sel itu. Jumlah kolom `VOLUME` sama persis dengan volume yang dilaporkan panel,
   sementara jumlah `DX×DY×DZ` sama dengan volume blok penuh — kedua angka itu kini ada di dalam
   berkas yang sama sehingga selisihnya bisa diterangkan tanpa menebak.
2. **Panel menyebutkan selisihnya** setiap kali as-mined dihitung: volume terhitung, volume bila
   semua sel dihitung penuh, dan persentasenya, beserta keterangan bahwa ekspor menulis blok
   berukuran penuh dan kolom `FRAKSI` / `VOLUME` memuat angka sebenarnya.

Keduanya **tidak mengubah satu angka pun** yang sudah ada — hanya membuat yang tersembunyi jadi
terlihat. Uji `tools/uji/uji_atap_asmined.py` memeriksanya: jumlah kolom `VOLUME` harus sama
dengan volume yang dilaporkan (6.529,4231 = 6.529,4231), jumlah `DX×DY×DZ` harus sama dengan
volume blok penuh (7.812,5000 = 7.812,5000), harus ada sel pecahan (kalau tidak ada, kolom
`FRAKSI` tidak teruji), dan panel harus benar-benar menyebutkan selisihnya.

`amVolTxt` dipanggil dari `am2.js` lewat `window.amVolTxt ? ... : ''`, bukan langsung: kalau
modul atapnya tidak termuat, seluruh perhitungan as-mined akan melempar galat — ketergantungan
keras dari modul inti ke modul tambahan.

### Yang masih belum ada untuk model compiled

Ekspor `.mdl` masih menulis sel pecahan sebagai blok penuh. Memperbaikinya berarti memecah sel
itu ke level octree yang lebih halus supaya bentuknya mendekati atap / lantai sebenarnya — paling
benar secara geometri, tetapi paling berat dan dibatasi level maksimum octree model sumber.

Perlu diingat juga: resolusi vertikal model as-mined = **tinggi blok terkecil di model sumber**
(`amGrid`). Pada model yang tidak di-sub-block (mis. dz = 2,5 m), atap yang 0,22 m lebih rendah
**tidak akan terlihat** pada bentuk 3D-nya sama sekali — bentuknya persis sama, yang berubah
hanya angkanya. Ketidakrataan baru tampak sebagai teras bila modelnya sub-blocked.

### Yang belum ada

Atap belum bisa dibaca dari DTM / permukaan yang sudah jadi (mis. `.dtm` Surpac) — baru dari awan
titik. Atribut tujuan dumping dan ore characteristic sudah ada di as-mined lewat aturan material
(`R.cls` dan `R.dst`); yang ditambahkan di sini hanya batas atas volumenya.


## 97. CI: build Windows dibuat hemat tanpa mengurangi Release

### Masalahnya

Sejak 1 November tercatat **86 build Windows dalam enam hari**, masing-masing **38–87 menit**
dengan **pengali 2×** untuk runner Windows. Jatah 3.000 menit GitHub Pro habis sekitar hari
ketiga, dan sejak itu **setiap build ditolak** dengan pesan *"The job was not started because
recent account payments have failed or your spending limit needs to be increased."* Akibatnya
tidak ada installer baru yang terbit sejak pukul 03:12 tanggal 6 November, walau pekerjaannya
sudah ada di `main`.

### Yang TIDAK dilakukan

Build Windows **tidak** dipindahkan ke pemicu manual atau tag saja. Itu sempat dipertimbangkan,
tetapi melanggar aturan repo ini sendiri: *"SETIAP pembaruan yang di-push ke `main` … harus
muncul di GitHub Release."* Kalau build hanya jalan saat tag, push biasa tidak akan pernah
terbit, dan jejak resmi tiap pembaruan hilang.

Repo juga **tidak** dijadikan publik. Sistem lisensinya memang tidak bisa dipalsukan walau
sumbernya terbuka — Ed25519, aplikasi hanya memegang kunci publik di `electron/license.js`,
kunci privat tidak ada di repo — tetapi dengan sumber terbuka siapa pun bisa **menghapus**
pemeriksaan lisensinya dan membangun ulang aplikasinya sendiri. Gerbang lisensi menahan
penyalinan biasa, bukan orang yang memegang sumbernya.

### Yang dilakukan

**1. `cancel-in-progress: true` pada build Windows.** Sebelumnya `false`, sehingga enam push
beruntun dari beberapa sesi membangun installer yang sama enam kali — padahal hanya hasil
terakhir yang pernah dipakai. Ini **tidak** melanggar aturan Release: build selalu mengambil
keadaan `main` terakhir, dan catatan rilis memuat **semua** commit sejak rilis sebelumnya, jadi
commit yang build-nya dibatalkan tetap terbit — hanya ikut pada build berikutnya.

Dihitung dari riwayat nyata: dari 86 run, **68 disusul push baru dalam 50 menit** (lebih cepat
daripada build selesai) sehingga akan dibatalkan. Sisa **18 build** yang benar-benar perlu
berjalan — pemangkasan sekitar 79%. Angka ini perkiraan: ia mengandaikan push berikutnya datang
sebelum build sebelumnya selesai, yang benar untuk rentetan push tetapi tidak selalu.

**2. Cache.** Alur ini sebelumnya **tidak punya satu pun** `actions/cache`, sehingga pip, npm dan
binary Electron diunduh ulang dari nol setiap build — kemungkinan besar sebab build 87 menit.
Ditambahkan:

| Cache | Kunci | Catatan |
| --- | --- | --- |
| pip (lewat `setup-python`) | isi `backend/requirements*.txt` | batal sendiri bila daftar paket berubah |
| unduhan npm | isi `package.json` | **bukan** `cache: npm` bawaan `setup-node` — lihat di bawah |
| binary Electron & electron-builder | isi `package.json` | batal sendiri bila versi Electron naik |

`cache: npm` bawaan `setup-node` **sengaja tidak dipakai**: repo ini tidak punya
`package-lock.json`, dan `setup-node` menggagalkan build bila berkas kunci itu tidak ada. Cache
unduhan npm dipasang manual sebagai gantinya, karena ia **tidak** mengubah cara npm memilih versi
paket — menambahkan lock file akan mengubah versi yang terkemas ke installer, dan itu keputusan
tersendiri yang perlu diputuskan pemilik, bukan efek samping perbaikan CI.

**3. `concurrency` pada alur uji penampil Qt.** Alur ini murah (Ubuntu, ~1,5 menit, pengali 1×)
dan bukan sumber masalah tagihan, tetapi tidak ada gunanya menjalankan uji yang sama berkali-kali
untuk commit yang langsung saling menimpa.

### Yang masih perlu tindakan pemilik

Perubahan ini **tidak menghidupkan kembali** build yang sedang diblokir. Jatah menit yang sudah
habis tetap habis: *spending limit* perlu dinaikkan di **GitHub → Settings → Billing & plans**,
atau ditunggu sampai jatah bulanan berganti. Setelah itu `gh run rerun <id>` akan membangun
commit teratas dan menerbitkan seluruh pekerjaan yang tertahan dalam satu Release.

### Catatan terpisah: tidak ada `package-lock.json`

Repo ini tidak punya lock file, sehingga `npm install` bebas memilih versi paket yang berbeda
antar build. Untuk aplikasi yang diedarkan sebagai installer berlisensi, itu berarti dua build
dari commit yang sama bisa mengemas versi dependensi yang berbeda. Belum diubah di sini karena
menambahkannya mengubah versi yang terkemas, dan itu keputusan pemilik.


## 98. Drill Hole 0.24.36 — cap versi, dan ralat atas keputusan sebelumnya

Pada bagian 94, cap versi di `app-dh/index.html` dibetulkan dari 0.24.34 menjadi 0.24.35 **tanpa**
menaikkan versi Drill Hole, dengan alasan yang berubah hanya cap yang menyusul nomor yang sudah
diumumkan di rilis sebelumnya — bukan isi aplikasi.

**Alasan itu keliru**, dan akibatnya tepat jenis masalah yang pembetulan cap itu sendiri hendak
hilangkan:

| | Nama berkas installer | Aplikasi melaporkan dirinya |
| --- | --- | --- |
| Release sebelum pembetulan | `GC-Ex-Drillhole-Setup-0.24.35.exe` | 0.24.34 |
| Build setelah pembetulan | `GC-Ex-Drillhole-Setup-0.24.35.exe` | 0.24.35 |

Dua installer yang **isinya berbeda** dengan **nama berkas dan nomor versi yang sama persis**, dan
yang kedua menimpa yang pertama di Release. Kalau nanti ada yang melapor "saya pakai 0.24.35",
tetap tidak bisa dipastikan ia memakai yang mana — persis kerancuan yang hendak dihilangkan.

Aturan repo juga lebih tegas daripada penalaran itu: *"Naikkan versi aplikasi yang **isi
installernya** berubah."* `app-dh/index.html` adalah isi installer Drill Hole, dan ia berubah.
Tidak ada pengecualian untuk "hanya cap versi".

**Diperbaiki:** Drill Hole naik ke **0.24.36**, `app-dh/index.html` dibangun ulang sehingga capnya
ikut 0.24.36, dan `tools/rilis/cek_cap_versi.py` memastikan keduanya cocok. Perubahan ini
sengaja di-push **sebelum** build yang sedang berjalan selesai, supaya `0.24.35` yang kedua tidak
pernah sempat terbit — membiarkannya terbit dulu justru mewujudkan masalahnya.

## 99. DB-Ex 0.42.2 — keluarkan foto dari daftar Core box; folder Borang tidak lagi terdaftar otomatis

- **Keluarkan dari daftar**: tombol baru di bilah atas tabel Core box (juga tombol **Delete** saat tabel aktif). Berlaku untuk foto yang dicentang, atau foto yang sedang dibuka bila tidak ada yang dicentang.
  File foto di folder **tidak dihapus dan tidak dipindah**; foto hanya dikeluarkan dari daftar Core box (isian, segmen dan tandanya ikut terhapus dari database) dan tidak masuk lagi saat dipindai ulang (↻ / F5). Bilah status menampilkan jumlahnya (*N dikeluarkan*).
- **Kembalikan**: *File → Kembalikan foto yang dikeluarkan dari daftar…* memasukkan lagi semua foto tersebut sebagai foto baru.
- **Folder Borang / Singkapan / QAQC tidak lagi otomatis masuk Core box.** Dulu setiap folder yang dibuka langsung dipindai dan semua gambarnya didaftarkan sebagai foto core box (mis. foto borang ikut tampil di tabel Core box). Sekarang foto hanya didaftarkan dari ruang kerja Core box. Bila folder dibuka untuk ruang kerja lain lalu Anda pindah ke Core box, DB-Ex bertanya dulu apakah foto di folder itu memang foto core box.
- Folder yang sudah telanjur terisi foto borang di Core box: centang semua (*Pilih semua yang tampil*) lalu **Keluarkan dari daftar**. Data Borang tidak terpengaruh.


## 100. CI: build terjadwal sebagai jaring pengaman

### Kegagalan yang ditimbulkan perbaikan sebelumnya

Bagian 97 mengubah `cancel-in-progress` menjadi `true` supaya rentetan push hanya menghasilkan
satu build. Itu memang memangkas build sia-sia, tetapi punya kegagalan sendiri yang **tidak
terlihat saat perubahannya dibuat**: bila beberapa sesi mem-push **lebih cepat daripada build
selesai** (~40 menit), tidak ada satu pun build yang pernah tuntas dan **Release tidak pernah
diperbarui sama sekali**.

Itu bukan kemungkinan teoretis — ia langsung terjadi pada 6 November: tiga build berturut-turut
dibatalkan (06:22, 06:28, dan satu lagi), dua di antaranya oleh push dari sesi yang berbeda, satu
oleh push saya sendiri. Sebelum perubahan itu, build mengantre dan semuanya akhirnya jalan: boros,
tetapi Release selalu terbit.

### Jaring pengamannya

Ditambahkan pemicu terjadwal harian:

```yaml
schedule:
  - cron: "44 18 * * *"      # 18:44 UTC = 02:44 WITA
```

Jam sepi, sehingga kecil kemungkinan ia sendiri dibatalkan push. Menitnya sengaja **bukan** `:00`
— GitHub menunda jadwal yang menumpuk di awal jam.

Dan `cancel-in-progress` dibuat bergantung pada jenis pemicunya:

```yaml
cancel-in-progress: ${{ github.event_name != 'schedule' }}
```

- **Push** membatalkan build yang sedang jalan — peredam tetap bekerja.
- **Build terjadwal** tidak membatalkan apa pun; ia mengantre. Jaring pengaman tidak boleh justru
  membunuh build yang hampir selesai.

Grup `concurrency`-nya tetap sama untuk keduanya, sehingga tidak pernah ada dua build menulis
Release yang sama pada saat bersamaan — bahaya yang sudah diperingatkan komentar aslinya.

### Yang diterima sebagai konsekuensi

Build terjadwal tetap jalan walau `main` tidak berubah sejak Release terakhir, dan akan
menerbitkan ulang isi yang sama. Itu dibiarkan: repo sudah publik sehingga menitnya gratis, dan
menambah pemeriksaan "apakah ada yang berubah" menambah kerumitan pada bagian yang justru harus
bisa diandalkan tanpa syarat. Yang dibelinya adalah jaminan sederhana — **Release selalu cocok
dengan `main` paling lambat keesokan dini hari**, apa pun yang terjadi dengan push hari itu.

## 101. DB-Ex 0.42.3 — Borang dibaca AI lebih cepat

- **AI tidak lagi "berpikir panjang" untuk Borang.** Model seperti `qwen3-vl` menulis penalaran panjang sebelum menjawab; di komputer tanpa GPU itu bisa memakan sebagian besar dari ±10 menit per lembar. DB-Ex kini mematikan mode itu (*think = false*) khusus untuk membaca borang, bila model mendukungnya. Ollama versi lama yang belum mengenal parameter ini otomatis dibaca ulang tanpa parameter itu.
- **Pilihan kecepatan** di sebelah tombol *✦ Baca dengan AI*: **Cepat** (gambar 1280 px), **Seimbang** (1600 px, bawaan), **Teliti** (2000 px, untuk tulisan kecil / scan buram). Makin kecil gambar, makin cepat AI membaca. Pilihan diingat.
- **Baca semua yang belum**: semua borang yang belum dibaca (atau gagal) diantrekan dan dibaca satu per satu di latar belakang. Daftar borang menampilkan *AI membaca…* / *antre AI #n*, dan di bawah scan tampil jam berjalan. Selama itu Anda bisa membuka, memeriksa, dan memverifikasi borang lain. Borang yang gagal dilewati dan antrean berlanjut.
- Lama baca per borang tercatat di bawah scan (*Dibaca AI … · N dtk*), jadi Anda bisa membandingkan sebelum dan sesudah.


## 102. RALAT: `cancel-in-progress: true` dikembalikan ke `false`

Bagian 97 mengubah `cancel-in-progress` menjadi `true` dengan alasan dari 86 run Windows dalam
enam hari, "68 di antaranya akan dibatalkan" sehingga hemat ~79%. **Perhitungan itu salah.**

Ia mengandaikan bahwa dengan `false` ke-86 run berjalan penuh. Tidak demikian: **GitHub sudah
membatalkan run yang masih mengantre** dalam satu grup `concurrency` walaupun setelannya `false`.
Itu terlihat jelas di riwayat 5–6 November — banyak run berstatus *cancelled* di bawah setelan
lama. Yang sebenarnya ditambahkan oleh `true` hanyalah satu hal: **membunuh build yang sudah
berjalan**.

Di repo dengan beberapa sesi bekerja bersamaan, itu fatal. Push datang tiap 5–15 menit sedangkan
build perlu 38–87 menit, sehingga tidak ada satu pun build yang pernah selesai.

Buktinya langsung terbaca dari riwayat hari yang sama:

| Setelan | Rentang | Hasil |
| --- | --- | --- |
| `false` (lama) | 6 Nov 20:42–03:12 | **7 build sukses** (diselingi 7 pembatalan run yang mengantre) |
| `true` (perubahan 05:53) | 6 Nov 05:53–07:05 | **0 sukses, 4 pembatalan beruntun** |

Alasan awal perubahan itu — jatah 3.000 menit GitHub Pro habis — juga sudah **lenyap satu jam
kemudian** ketika repo dijadikan publik: Actions pada runner standar gratis tanpa batas untuk
repo publik. Premisnya hilang, tetapi perubahannya tidak ditinjau ulang.

**Dikembalikan ke `false`.** Yang tetap dipertahankan:

- **Cache** (pip, unduhan npm, binary Electron) — murni untung, memangkas waktu build.
- **Build terjadwal 02:44 WITA** — tetap berguna: run yang mengantre masih bisa dibatalkan push
  berikutnya, jadi pada hari yang sangat sibuk masih mungkin ada rentang panjang tanpa Release
  baru.

Pelajarannya dicatat di sini karena sempat merugikan: perubahan dibuat atas perkiraan tentang
perilaku GitHub, bukan atas riwayat yang sudah tersedia di repo ini sendiri. Riwayat itu sudah
berisi jawabannya sejak awal.

## 103. As-mined: atap dari permukaan / DTM yang sudah dimuat

Bagian 95 memberi atap as-mined dari **awan titik pick-up** (median per poligon, atau interpolasi
IDW). Itu cocok bila geologist memegang CSV pick-up mentah. Tetapi alur yang lebih umum di
tambang adalah sebaliknya: titik pick-up sudah dijadikan **DTM di Surpac** lebih dulu — ditutup,
dibersihkan, dipotong di batas desain — dan DTM itulah yang dianggap sah. Memaksa pemakai kembali
ke awan titik mentah berarti memakai permukaan yang **berbeda** dari yang dipakai survei untuk
menghitung volume, dan selisihnya tidak akan pernah bisa dijelaskan saat rekonsiliasi.

Karena itu ada mode atap keempat: **Atap dari permukaan / DTM yang sudah dimuat (menu Model)**.

### Dari mana permukaannya diambil

Tidak ada pengimpor baru. Permukaan diambil dari daftar yang **sudah ada**, `MD.models`, yang
diisi oleh pembaca yang sudah lama terpasang:

| Berkas | Catatan |
| --- | --- |
| Surpac `.dtm` | **harus** disertai `.str` pasangannya — `.dtm` hanya memuat segitiga, titiknya ada di `.str` |
| Leapfrog `.msh` | |
| `.obj` | |
| DXF mesh (`POLYFACE` / `3DFACE`) | |

Jadi urutannya: muat permukaannya lewat menu **Model** seperti biasa, lalu pilih namanya di panel
as-mined. Satu permukaan bisa dipakai sekaligus untuk gambar 3D dan untuk perhitungan; tidak ada
salinan kedua yang bisa menyimpang.

Koordinatnya **tidak** dikonversi. `MD.models[].v` menyimpan koordinat **penuh** (fungsi gambar
`mdLocal()` lah yang mengurangi `offX/offY`, hanya untuk tampilan), dan as-mined juga bekerja di
koordinat penuh. Menambahkan konversi "untuk aman" justru akan menggeser permukaannya 1 km.

### Cara elevasinya dibaca

`amRoofZ` menembakkan garis vertikal dari setiap pusat sel ke permukaan dan mengambil elevasi
perpotongannya (barisentrik, dari segitiga yang benar-benar menaungi titik itu). Supaya tidak
menelusuri seluruh segitiga untuk setiap sel, segitiga diindeks lebih dulu ke **kisi ember 2D**
(`_rfIx`, disimpan pada objek modelnya dan dipakai ulang selama modelnya tidak berganti).

Dua keadaan dilaporkan, bukan didiamkan:

1. **Di luar jangkauan permukaan.** Kalau garis vertikal sebuah sel tidak mengenai satu segitiga
   pun — DTM-nya tidak menjangkau seluruh poligon — sel itu memakai **RL atas flitch nominal**,
   yaitu atap **asumsi**, sama seperti sebelum fitur ini ada. Luas total yang mengalaminya
   ditampilkan di panel dengan peringatan. Diam-diam memakai RL nominal di separuh poligon akan
   memberi angka yang kelihatan wajar dan salah.
2. **Satu titik mengenai lebih dari satu segitiga.** Itu tanda yang dipilih kemungkinan **solid
   tertutup** (punya atap *dan* lantai), bukan permukaan. Yang diambil adalah perpotongan
   **terdekat ke RL atas flitch**, tetapi jumlah titiknya tetap dilaporkan: pada solid tertutup
   pilihan itu bisa benar untuk sebagian sel dan salah untuk sebagian lain, dan tanpa angka ini
   tidak ada cara pemakai mengetahuinya.

### Yang diuji

`tools/uji/uji_atap_asmined.py` ditambah dua kasus, keduanya dengan permukaan sintetis yang
dimasukkan langsung ke `MD.models` dalam bentuk yang sama dengan hasil `readDtm` / `readMsh`:

- **DTM rata yang menutupi seluruh poligon** pada RL atas &minus; 0,22 m → volumenya **wajib
  sama persis** dengan mode *atap rata* pada elevasi yang sama, dan luas "di luar jangkauan"
  wajib **nol**. Ini yang mengikat mode baru ke mode yang sudah terbukti.
- **DTM yang hanya menutupi separuh poligon** → luas "di luar jangkauan" wajib **lebih dari nol**,
  dan volumenya wajib berada **di antara** DTM penuh dan atap flitch nominal (separuh yang tidak
  terjangkau kembali ke RL nominal).

Uji bawaan (bagian 95) tetap berjalan: dengan `roof = 'flitch'`, delapan ukuran as-mined masih
identik sampai digit terakhir dengan versi sebelum perubahan. Mode atap baru tidak boleh menggeser
satu angka pun bagi pemakai yang tidak memilihnya.

### Yang belum

Ekspor `.mdl` masih menulis sel pecahan sebagai blok penuh (bagian 95). Dengan atap dari DTM
selisihnya **bertambah besar**, sebab sel pecahan tidak lagi hanya di tepi poligon melainkan di
seluruh luasnya. Kolom `FRAKSI` / `VOLUME` dan catatan di panel membuat selisihnya terlihat;
memperbaikinya berarti memecah sel ke level octree yang lebih halus, dan itu pekerjaan berikutnya.

## 104. DB-Ex 0.42.4 — jawaban AI Borang ringkas; RC Drill Logging mengikuti borang lapangan

- **Jawaban AI ringkas.** AI tidak lagi menulis JSON; tiap baris tabel dijawab sebagai satu baris teks dengan nilai dipisah `|`. Jawaban jadi kira-kira 3-4x lebih pendek, dan di komputer tanpa GPU panjang jawaban itulah yang paling menentukan waktu baca. Panjang jawaban juga dibatasi, sehingga model yang mengulang baris tanpa henti berhenti sendiri dan tidak lagi berakhir *gagal* setelah menunggu lama.
- **RC Drill Logging / Chiptray Log** kini berkolom Hole ID, Tanggal, Sample ID, From, To, **Lith, Int_Alt, Min1, Vein_Type, Qt_pct**, Remark (QAQC). Satu lembar boleh memuat banyak lubang:
  - Hole ID & tanggal cukup ditulis di baris pertama lubang; baris di bawahnya diisi otomatis sampai Hole ID berikutnya (ditandai kuning).
  - Garis bergelombang / kurung kurawal / tanda ulang di kolom Lith, Int_Alt, Min1 diisi dari baris atas (kuning).
  - Baris sisipan BLANK / STD tanpa From-To tidak memutus pemeriksaan urutan interval.
  - Ekspor `RC_INTERVAL` / sheet *Interval_Geodatabase* membawa kolom LITH, INT_ALT, MIN1, VEIN_TYPE, QT_PCT.
- **Putaran scan diingat.** Foto borang baru otomatis memakai putaran (↻) borang terakhir sejenis dengan bentuk foto yang sama, jadi foto yang diambil rebah tidak perlu diputar satu per satu sebelum dibaca AI. Putar scan dulu sebelum membaca: AI membaca tulisan yang tegak jauh lebih cepat dan tepat.

## 105. DB-Ex 0.42.5 — Borang: konteks AI secukupnya, porsi GPU ditampilkan

- **Penyebab lambat yang paling sering: model tidak seluruhnya di GPU.** Konteks AI sebelumnya ditetapkan 16384 token (lalu 8192). Memori konteks (KV cache) sebesar itu bisa membuat model tidak muat di VRAM, sehingga sebagian dijalankan CPU dan pembacaan satu lembar bisa memakan 5-10 menit. Sekarang konteks dihitung secukupnya dari ukuran gambar + perintah + jawaban (±5-6 ribu token).
- **Panel di bawah scan** setelah AI membaca kini menampilkan: jumlah token jawaban, token/detik, ukuran gambar, konteks, dan **porsi model di GPU** (dari Ollama). Bila kurang dari 100 %, muncul peringatan merah dengan saran:
  - tutup aplikasi lain yang memakai GPU (browser dengan banyak tab, Leapfrog, Surpac 3D);
  - pilih kecepatan **Cepat** (gambar 1280 px);
  - pakai model yang lebih kecil, mis. `qwen3-vl:2b` (`ollama pull qwen3-vl:2b`, lalu pilih di dialog AI).
- Cek manual di Command Prompt saat AI sedang membaca: `ollama ps` — kolom **PROCESSOR** harus `100% GPU`.

## 106. DB-Ex 0.42.6 — Borang di laptop tanpa GPU NVIDIA

Ollama hanya memakai kartu grafis NVIDIA (atau AMD tertentu). Pada laptop dengan **Intel Iris Xe**, AI seluruhnya berjalan di CPU, dan membaca satu lembar tulisan tangan bisa memakan beberapa menit. Panel di bawah scan kini menyebut hal itu dan menyarankan, dari yang paling berpengaruh:

1. **Pakai komputer lain yang punya GPU NVIDIA sebagai "server" AI.** Di komputer itu pasang Ollama, set variabel lingkungan `OLLAMA_HOST=0.0.0.0`, lalu `ollama pull qwen3-vl:4b`. Di DB-Ex laptop: dialog AI → alamat Ollama diisi `http://<IP komputer itu>:11434`. Foto tetap di laptop; hanya gambar borang yang dikirim lewat jaringan kantor (tidak ke internet).
2. **Model kecil** `qwen3-vl:2b` (`ollama pull qwen3-vl:2b`, pilih di dialog AI): kira-kira 2x lebih cepat, sedikit lebih sering keliru membaca tulisan jelek — periksa sel kuning.
3. Kecepatan **Cepat** (gambar 1280 px) dan tutup aplikasi lain supaya RAM 8 GB tidak penuh.

## 107. Perapian UI/UX: satu fungsi satu tempat, judul yang nyambung dengan isinya

Permintaan pemilik, dengan enam tangkapan layar: banyak fungsi yang sama muncul di beberapa menu,
ada panel yang isinya tidak nyambung dengan judulnya, dan tombol-tombol bernomor dalam lingkaran
masih tersisa.

### Satu sebab, bukan enam

Lima dari enam keluhan itu berasal dari **satu** kelemahan yang sama, bukan dari lima tempat berbeda.

Panel Properti di bawah Project Tree diisi dengan cara memilih **tab** dan **sub-bagian** panel yang
sudah ada. Node yang hanya menjalankan perintah — membuka dialog, mengunduh berkas — tidak punya
tab, jadi ia **tidak mengganti isi panel sama sekali**: panel milik node SEBELUMNYA tetap terpampang
di bawah judul node yang baru. Dan node yang punya tab tetapi tidak menyebut segmen mana yang
dimaksud akan menampilkan **seluruh** panel Dig block, termasuk bagian milik node lain.

Akibatnya persis seperti yang dilaporkan: tombol *Import BM* muncul di bawah judul *Sayatan 2D*,
panel *Dig block otomatis* muncul di mana-mana, dan folder *Dig Block* memperlihatkan isi yang sama
persis dengan sub-node *Otomatis*.

### Yang dikerjakan

Sekarang setiap node menyatakan apa yang muncul di Properti. Ada tiga bentuk, dan tidak ada bentuk
keempat yang "membiarkan saja apa adanya":

1. **Panel** — node yang memang punya panel sendiri (tab + sub-bagian + segmen).
2. **Kartu aksi** — node yang menjalankan perintah: keterangan singkat + tombolnya, tanpa panel.
   Ini bawaan untuk setiap node tanpa tab, jadi kelemahan yang sama tidak bisa muncul lagi pada
   node yang ditambahkan nanti.
3. **Kartu folder** — daftar sub-menu sebagai tombol, bukan salinan panel sub-node pertamanya.

Pemetaan yang berubah, diperiksa dengan menekan ke-66 node satu per satu lalu merekam isi panelnya
(`peta_panel`, lihat "Cara memeriksanya" di bawah):

| Node | Sebelum | Sesudah |
| --- | --- | --- |
| `dig` (folder Dig Block) | sama persis dengan `dig.auto` | kartu folder |
| `dig.auto` Otomatis | kelas kadar **dan** tujuan | kelas kadar saja |
| `dig.dest` Tujuan (DEST) | tidak ada | node sendiri, tujuan saja |
| `fl.2d` di bawah Flitch Aktif | panel Block Model + tombol Import BM | **Buat Flitch Aktif** (kartu, 3 tombol) |
| `rep.unit`, `rep.csv`, `out.png`, `reg.xl`, `reg.pdf`, `reg.mdl` | panel node sebelumnya | kartu aksi |
| `dig.qc`, `dig.pst`, `rep.day`, `reg.prd`, `reg.3d`, `reg.puz` | panel Dig block / Register | kartu aksi |
| `rep.x` Per desain pit & progres | di Laporan Grade × Tonnage | pindah ke Block Model › Reporting |
| `rep.rl` Ringkasan per RL | ada di DUA cabang | satu, di Block Model |
| `rep`, `out`, `am`, `reg`, `sp`, `set` (folder) | menduplikasi sub-node pertamanya | kartu folder |

Judul besar di dalam panel (`.lyhead`, `h3`) juga disembunyikan selama Project Tree aktif: ia hanya
mengulang nama node yang sudah tertulis di kepala Properti, dan justru membuat isi panel terbaca
sebagai milik judul yang salah.

Node *Sayatan 2D* di bawah *Flitch Aktif* diganti menjadi **Buat Flitch Aktif**, sesuai permintaan:
yang dikerjakan di situ memang menerapkan flitch, bukan mengatur sayatan.

### Angka dalam lingkaran

Dihapus seluruhnya, 51 tempat di enam berkas: tab ①–⑥ pada Reporting, Metode tonase, Pit & progres,
alur As-Mined dan tab panel, serta badge bernomor di Project Tree. Badge itu kini titik status saja —
statusnya (selesai / berikutnya / belum / opsional) tetap terbaca lewat warna dan tooltip, sedangkan
nomornya tidak menambah apa pun di atas urutan node yang memang sudah terlihat dari atas ke bawah.
Kalimat yang dulu merujuk "tab ②" diganti menjadi nama tabnya, supaya tidak menunjuk sesuatu yang
sudah tidak ada.

### Cara memeriksanya

`peta_panel` menjalankan aplikasi sungguhan dengan data latihan, menekan setiap node Project Tree,
lalu merekam judul-judul yang BENAR-BENAR terlihat di panel Properti. Itu yang memunculkan peta
redundansi di atas, dan itu pula yang dipakai untuk memastikan perbaikannya bekerja — bukan dengan
membaca kode dan berharap.

## 108. Lag di laptop: 45,8 detik layar membeku, menjadi 1,0 detik

Laporan pemilik: aplikasi sering tersendat di laptop HP 14s. Yang dikerjakan di sini bukan menebak
lalu menyetel apa saja yang kelihatan berat, melainkan **mengukur lebih dulu**.

### Cara mengukurnya

Yang diukur adalah apa yang dirasakan: **berapa lama layar membeku**. Caranya memantau jeda antar
frame (`requestAnimationFrame`); frame normal ~16 ms, dan setiap jeda di atas 50 ms adalah waktu
ketika aplikasi tidak menanggapi apa pun. Diuji di atas block model sintetis **586.775 blok** dengan
ukuran campuran 6×6×3 / 3×3×3 / 1,5×1,5×0,75 m — sengaja dibuat sebesar `bmgczone3` milik pemilik,
sebab data latihan hanya 66 rb blok dan tidak pernah memperlihatkan masalahnya.

Dua pengukuran pertama saya **salah dan dibuang**, dan itu dicatat di sini supaya tidak diulang:

1. Mengukur waktu dinding sesudah `wait_for_timeout(6000)` — yang terbaca ya 6 detik itu, bukan
   lamanya aplikasi sibuk.
2. Menggeser slider lewat event buatan pada `#secPos` — **id itu tidak ada**; slider sayatan ber-id
   `#pos`. Jadi selama dua putaran pengukuran, tidak ada slider yang benar-benar digeser, dan
   angkanya (173 ms vs 212 ms) tidak berarti apa-apa. Baru setelah gagang slider yang benar diseret
   dengan gerakan mouse sungguhan, masalahnya muncul.

### Apa yang ditemukan

Pada profil Seimbang, grafik berisi **8 trace `mesh3d` dengan 3.389.028 titik**. Setiap langkah
geseran slider sayatan membangun ulang seluruh titik itu dan mengirimnya lagi ke kartu grafis.

Menyeret slider sayatan 24 langkah:

| | Layar membeku | Total membeku | Jeda terlama |
| --- | --- | --- | --- |
| Sebelum | **47 ×** | **45.847 ms** | **4.779 ms** |
| Sesudah | 3 × | **1.025 ms** | 773 ms |

Hampir 46 detik tidak menanggapi apa pun, dengan satu jeda hampir 5 detik. Di laptop dengan grafis
bawaan, itulah yang terasa sebagai "lag".

### Yang diubah

1. **Pengaman model besar.** Setelan *Update saat slider dilepas* sudah lama ada dan memang
   jawabannya, tetapi bawaannya mati pada profil Seimbang — jadi pengguna harus tahu dulu bahwa
   setelan itu ada. Sekarang, saat block model ≥ 250.000 blok dimuat, setelan itu dinyalakan
   **sekali** dan **alasannya ditulis** di panel Block Model. Ia tidak menimpa keputusan pengguna:
   begitu pengguna menyentuh setelan itu sendiri, pilihannya diingat dan tidak diubah lagi. Yang
   berubah hanya KAPAN gambar diperbarui, bukan isinya.
2. **Penyegaran Project Tree.** Dulu `setInterval` 1,5 detik tanpa syarat, dan tiap denyut membangun
   ulang seluruh pohon. Di dalamnya ada `lyItems()`, yang **menghitung tonase presisi setiap
   poligon** — padahal yang dipakai hanya JUMLAH poligonnya. Diganti `lyPolys()`, yang memberi
   daftar sama tanpa satu pun perhitungan tonase. Penyegarannya kini menunggu saat peramban luang
   (`requestIdleCallback`), dilewati saat tampilan sedang diputar/digeser, dan mundur bertahap
   1,5 → 8 detik selama tidak ada yang berubah, lalu cepat lagi begitu pengguna menyentuh apa pun.
   Diukur pada data latihan dengan 68 dig block: 6,6 → 4,9 ms per bangun-ulang. Kecil, tetapi
   denyut berkalanya yang hilang.

Perubahan nomor 2 saja tidak akan terasa; yang menyelesaikan masalahnya adalah nomor 1.

## 109. Fitur Demo disesuaikan dengan Project Tree

Setelah panel Properti ditentukan oleh node Project Tree, Demo perlu ikut disesuaikan: ia berpindah
panel dengan `uiTab()`, padahal tab-nya memang berganti tetapi bagian panel yang dituju tetap
tersembunyi karena node yang terpilih bukan pemiliknya.

### Yang diperiksa, dan apa yang ternyata sudah rusak

`tools/uji/uji_demo.py` menjalankan demo **sungguhan** dari langkah pertama sampai habis, dan tiap
250 ms mencatat apakah elemen yang ditunjuk langkah itu BENAR-BENAR terlihat di layar. Hasil awal:
**5 dari 37 langkah menunjuk elemen yang tidak pernah tampak.** Pemeriksaan yang sama dijalankan
pada versi SEBELUM perapian UI (`git show HEAD:app/index.html`) dan memberi **5 kegagalan yang sama
persis** — jadi kelimanya sudah rusak sejak sebelumnya, bukan akibat perapian ini, dan sekarang
ikut diperbaiki.

### Tiga percobaan, dua di antaranya salah

Dicatat karena sempat memperburuk keadaan:

1. Memetakan node Project Tree ke **17 langkah** sekaligus: kerusakan NAIK dari 5 ke 7. Sebabnya
   memilih node ikut mengganti panel, dan pilihan itu **terbawa ke langkah berikutnya** yang
   mengandaikan panel lain.
2. Dipersempit ke 4 langkah: tersisa 4 — perbaikan lama hilang, kerusakan baru muncul.
3. Yang benar: bukan menambal tiap langkah, melainkan **satu** perubahan — selama demo berjalan
   (`body.dm-tur`), penyembunyian per-node dimatikan. Demo adalah tur yang menyusuri banyak bagian
   panel berturut-turut; Project Tree sebaliknya sengaja menyembunyikan yang bukan milik node
   terpilih. Dua maksud itu memang bertabrakan, dan tempat menyelesaikannya satu, bukan 37.

Ditambah dua hal kecil: dua langkah Layout PDF tetap perlu memilih node-nya (bagian panel itu hanya
terbuka lewat pemilih bagian, bukan lewat penyembunyian), dan tiga elemen target diarahkan ulang —
`.dbtot` yang baru ada setelah dig block dibuat, serta `btn2d` dan `rbAM` yang merupakan tombol
bilah atas yang kini digantikan Project Tree (yang ditunjuk sekarang baris node-nya).

Satu kesalahan saya sendiri juga dicatat: perbaikan elemen target sempat **tidak pernah dijalankan**
karena fungsi pemasangnya keluar lebih awal untuk langkah yang tidak ada di daftar node. Ujinya
melaporkan kegagalan yang sama seolah perbaikannya tidak bekerja — padahal kodenya memang tidak
pernah dieksekusi.

**Hasil akhir: 0 dari 37 langkah menunjuk elemen yang tidak terlihat.**

## 110. GC-Ex Drill Hole: lag yang sama, 44,1 detik menjadi 1,1 detik

Permintaan pemilik: lakukan untuk Drill Hole apa yang sudah dilakukan untuk Block Model (bagian
108), supaya ringan di laptop HP 14s.

Dikerjakan dengan urutan yang sama — **ukur dulu, baru ubah** — dan memakai alat ukur yang sama
(`tools/uji/ukur_lag_dh.py`): lamanya **layar membeku**, yaitu jumlah jeda antar-frame di atas
50 ms, selama gagang slider sayatan diseret dengan gerakan mouse sungguhan.

### Yang ditemukan

Diukur di atas **data latihan SIM_*** saja — 610 lubang bor, 76.069 sampel assay. Tidak perlu data
sintetis yang besar seperti di Block Model, sebab masalahnya sudah muncul pada data latihan itu
sendiri: grafiknya berisi **15 trace, 1.190.825 titik**, dan setiap langkah geseran slider
membangun ulang seluruh geometri lubang bor lalu mengirimnya lagi ke kartu grafis.

Menyeret slider sayatan 24 langkah:

| | Layar membeku | Total membeku | Jeda terlama |
| --- | --- | --- | --- |
| Sebelum | **61 ×** | **44.138 ms** | 2.324 ms |
| Sesudah | 2 × | **1.078 ms** | 769 ms |

### Yang diubah

Satu hal, sama persis dengan Block Model: setelan *Update saat slider dilepas* dinyalakan **sekali**
ketika datanya besar, dengan **alasan tertulis** di panel Sayatan. Ambangnya disesuaikan dengan
bentuk data Drill Hole — bukan jumlah blok, melainkan **≥ 20.000 sampel assay, atau ≥ 200 lubang,
atau block model estimasi ≥ 250.000 blok** — sebab di aplikasi ini yang berat adalah geometri
lubang bornya, dan block model estimasi sering belum ada sama sekali.

Ia tidak menimpa keputusan pengguna: begitu pengguna menyentuh setelan itu sendiri, pilihannya
diingat (`localStorage`) dan tidak diubah lagi. Yang berubah hanya **kapan** gambar diperbarui,
bukan isinya — tidak ada satu angka pun yang bergeser, dan tidak ada data yang disembunyikan.

Pemeriksaannya dipanggil **sesudah** data pemboran dimuat (`SA.boot`), bukan saat halaman dibuka:
jumlah lubang dan sampel baru diketahui di titik itu.

### Catatan untuk pengukuran berikutnya

Dua hal yang sempat menghabiskan waktu dan dicatat supaya tidak diulang: node Sayatan di Drill Hole
ber-id `sec` (di Block Model `set.s`), dan `uiTab` / `PT.select` tidak terjangkau dari luar karena
sumber viewer dievaluasi ke dalam lingkupnya sendiri — yang bekerja adalah menekan tombolnya
langsung (`#rbSlice`). Selama slider `#pos` belum terlihat di layar, ia tidak bisa diseret, dan
pengukurannya menghasilkan angka yang tidak berarti apa-apa.

## 111. DB-Ex 0.42.7 — perbaikan galat "jawaban AI tidak berformat H| / R|"

- Di 0.42.4–0.42.6 AI diminta menjawab ringkas (`H|...`, `R|...`). Sebagian model kecil menjawab dengan bentuk lain (tabel markdown, `R:`, JSON di tengah penjelasan) atau menulis jawabannya di bagian *thinking*, sehingga borang gagal dengan pesan di atas. Bentuk-bentuk itu kini dikenali.
- Bila jawaban tetap tidak terbaca, DB-Ex otomatis **mengulang sekali dengan format JSON berskema** (cara sebelum 0.42.4): lebih lambat, tetapi bentuk jawabannya dipaksa oleh Ollama.
- Jawaban mentah AI terakhir untuk tiap borang disimpan di `_GCEx_Core/borang/ai_mentah/<id>.txt`; pesan galat juga memuat potongan awal jawaban. Bila masih gagal, kirim file itu ke admin.

## 112. DB-Ex 0.42.8 — jawaban AI Borang dipaksa rapi; folder _GCEx_Core bersarang dicegah

- Di 0.42.7 model kecil (`qwen3-vl:2b`) kadang menulis penjelasan atau menyalin judul kolom, dan teks itu masuk ke tabel sebagai baris ("The user says…", "TIME", "From"). Sekarang Ollama **memaksa** bentuk jawaban: daftar nilai per baris tanpa nama kolom (tetap ringkas), dan baris yang isinya judul kolom, kalimat penjelasan, atau kosong dibuang otomatis.
- **Jangan membuka folder `_GCEx_Core` sebagai folder proyek** — buka folder foto / borang di atasnya. Bila terlanjur terpilih, DB-Ex kini otomatis memakai folder induknya (tidak lagi membuat `_GCEx_Core\_GCEx_Core\borang\_GCEx_Core`). Borang yang terlanjur masuk ke folder bersarang perlu ditambahkan ulang dari folder yang benar.
- Ketepatan tetap bergantung pada model: `qwen3-vl:2b` di CPU cepat-lambatnya ±5 menit per lembar dan lebih sering salah membaca kolom waktu; hasil terbaik dengan `qwen3-vl:4b` di komputer ber-GPU NVIDIA (lihat bagian sebelumnya).


## 113. Perapian UI/UX lanjutan, ekspor selalu bertanya, dan 3D dibatasi flitch aktif

Sebelas temuan pemilik dengan tangkapan layar. Lima di antaranya berakar pada satu hal yang sama
dengan bagian 107 — node yang tidak punya panel sendiri membiarkan panel node SEBELUMNYA terpampang
di bawah judul yang berbeda — dan sisanya cacat tersendiri.

### Ekspor: selalu bertanya mau disimpan di mana dan dengan nama apa

Permintaannya jelas: apa pun yang diekspor, dalam bentuk apa pun, harus memunculkan jendela simpan.

Yang ditemukan lebih buruk dari dugaan: **tidak satu pun** ekspor melakukannya. Semuanya memakai
`<a download>`, yang di aplikasi terpasang berarti berkas jatuh diam-diam ke folder Download dengan
nama yang sudah dipatok. Padahal jembatan Electron **sudah menyediakan** dialog Simpan
(`gcex:saveFile`, lengkap dengan penyaring jenis berkas) sejak awal — ia hanya tidak pernah dipanggil
dari halaman sama sekali.

Sekarang semua ekspor lewat satu pintu, `gxSimpan()`, dengan tiga jalur berurutan: dialog Simpan
milik Windows di aplikasi terpasang, `showSaveFilePicker` di peramban yang mendukungnya, dan — kalau
keduanya tidak ada — setidaknya **menanyakan nama berkas** lebih dulu, bukan memakai nama patokan.
Dipasang di satu tempat supaya ekspor yang ditambahkan nanti ikut menurut tanpa perlu diingatkan.
Yang ikut dialihkan: string STR/DXF, ringkasan tonase CSV, pemeriksaan dig block, ringkasan harian,
laporan periode, rencana bor CSV, berkas proyek `.dh3d` dan `.prj`, serta ekstraksi berkas sumber.

### Tampilan 3D dibatasi RL flitch aktif

Permintaan: setelah flitch dibuat, 3D harus memperlihatkan block model sebagai **pulau-pulau** yang
atas dan bawahnya dibatasi RL flitch aktif, seperti Surpac.

Terukur sebelum perbaikan: flitch 238,75–241,25 m, tetapi block model yang digambar **148,75–331,25 m**
— seluruh model, dari dasar sampai puncak. Dilihat dari samping, urat setinggi 180 m itu tampak
seperti tirai tegak, bukan pulau-pulau.

Sebabnya bukan cara memotongnya: `bxSel()` sudah lama tahu cara memotong tepat di RL flitch
(`BX.ui.fl`), tetapi hanya diminta memotong kalau kotak *Potong data (hanya dalam slab)* dicentang
atau sedang di Penampang 2D. Di 3D biasa, tidak ada yang memintanya. Jadi yang diubah hanya **siapa
yang meminta**: selama ada flitch aktif dan sayatannya horizontal, block model selalu dipotong di RL
flitch. Terukur sesudahnya: **238,75–241,25 m**, tepat flitch.

Yang TIDAK ikut berubah, dan itu disengaja: angka tonase dan laporan sama sekali tidak tersentuh —
ini murni soal apa yang digambar. Permukaan referensi (topografi, solid pit, solid urat Leapfrog)
juga tetap digambar utuh dan tetap mengikuti kotak *Potong data*; pada tangkapan layar, benda tinggi
yang masih terlihat setelah perbaikan adalah solid urat, bukan block model.

**Keputusan pemilik (7 Nov 2026): permukaan referensi dibiarkan UTUH, tidak ikut dipotong di RL
flitch.** Alasannya topografi dan desain pit berguna sebagai konteks — di mana flitch ini berada
relatif terhadap permukaan dan desain — dan keduanya jarang memotong flitch yang sama, sehingga
memotongnya hanya akan menghilangkannya dari layar. Yang terganggu bisa mematikan centangnya per
objek di Data Referensi. Jadi ini bukan hal yang belum diputuskan: jangan diubah tanpa permintaan
baru. Elevasi yang digambar tiap objek saat flitch 238,75–241,25 m, sebagai acuan bila nanti
dipertanyakan lagi:

| Objek | Elevasi tergambar |
| --- | --- |
| Block model (5 kelas kadar) | **238,75 – 241,25** (ikut flitch) |
| `QV_Lensa2_Leapfrog` (solid urat) | 132,09 – 322,93 |
| `SIM_topo_akhir_juni` | 260 – 348,12 |
| `SIM_topo_akhir_juli` | 245 – 348,12 |
| `SIM_pit_fase1` | 240 – 348,12 |
| `SIM_pit_fase2` | 180 – 348,12 |

### Dua cacat lain yang ditemukan

1. **Tombol "Simpan preset" mati justru ketika belum ada preset.** Kartu aksi mematikan SELURUH
   tombolnya ketika node ber-`dim`. Tetapi `dim` menandai *daftar yang masih kosong*, bukan aksi yang
   mustahil — sehingga satu-satunya jalan membuat preset pertama adalah lewat menu titik-tiga.
   Sekarang yang memutuskan hanya aksi itu sendiri. Preset yang disimpan juga **langsung dipakai di
   flitch aktif**, sesuai permintaan.
2. **Tab "Pit & progres" muncul dua kali.** Pemasang tab melewatkan pekerjaannya kalau sudah ada
   tombol bertanda `.rpxtab`, tetapi panel yang menggambar bilah tabnya sendiri membuat tombol
   "Pit & progres" **tanpa** tanda itu — jadi tombol kedua dengan nama sama persis ditambahkan.
   Sekarang panel-panel itu menandai tombolnya, dan pemeriksaannya juga melihat teksnya.

### Satu fungsi satu tempat (lanjutan bagian 107)

- Panel Block Model kini disembunyikan **total** untuk node yang panelnya ada di tab lain, jadi panel
  *Sayatan* tidak lagi memuat menu digitasi dig block.
- *Buat Flitch Aktif* kini **berisi** isian tinggi & RL flitch; folder *Flitch Aktif* jadi kartu daftar.
- Node *RL …*, *Semua flitch* dan *Dig block (n)* jadi kartu ringkas, bukan salinan panel orang lain.
- Tabel running grade & tonase dikeluarkan dari node *Otomatis* dan *Digit manual*: angka grade &
  tonase hanya di **Laporan Grade × Tonnage › Running grade & tonnage**.
- Tombol Export DXF/STR di panel *Rekap & edit string* dihapus. Ekspor string tinggal di satu node dan
  berlaku untuk flitch yang sedang aktif. Dua panel dengan tombol export berpenampilan sama tetapi
  cakupan berbeda (semua string yang tampil vs dig block flitch aktif) adalah sumber salah ekspor yang
  tidak kelihatan sampai berkasnya dibuka di Surpac.

### Mengganti nama string

Bisa langsung, dan memang sudah bisa sejak dulu: kotak teks berisi nama string di panel *Running grade
& tonnage* dapat diketik, dan namanya tersimpan ke proyek (`lyNm`) serta terpakai saat ekspor. Yang
kurang hanyalah petunjuk bahwa kotak itu bisa diketik.

### Catatan: dua kesalahan alat ukur, bukan aplikasinya

Dicatat supaya tidak diulang. **Pertama**, harness uji memakai nomor port tetap; peladen dari
pengujian sebelumnya masih menyajikan berkas lama, sehingga uji diam-diam memeriksa versi yang salah
— saya sempat menyimpulkan 0.24.29 rusak total karena ini, dan itu **keliru**; versi rilisnya sehat.
Semua harness kini memakai port acak. **Kedua**, probe 3D awalnya mengukur rentang elevasi SEMUA
lapisan sekaligus, termasuk topografi dan solid pit yang memang setinggi 348 m, sehingga perbaikan
yang sudah bekerja terbaca seolah tidak berubah. Pengukuran harus per lapisan.

## 114. Ekspor As-Mined disatukan: satu berkas, satu tempat membuatnya

Lanjutan bagian 113, atas prinsip yang sama (satu fungsi satu tempat).

Yang ditemukan: **`amMdl()` bisa dipanggil dari TIGA tempat dengan tiga nama berbeda**, padahal berkas
yang dihasilkan sama persis:

| Tempat | Nama tombolnya |
| --- | --- |
| Panel Register (`am3d.js`) | ⇩ .mdl gabungan |
| Node *Rekap & model gabungan (.mdl)* | Export .mdl gabungan |
| Node *Block model as-mined (.mdl)* | Block model as-mined (.mdl) |

Tiga nama untuk satu berkas membuat pemakai wajar mengira ketiganya berbeda — dan perbedaan yang
disangka itu baru ketahuan tidak ada setelah ketiga berkasnya dibuka.

Sekarang ada satu node **Ekspor As-Mined** yang memuat seluruh keluaran As-Mined: report
rekonsiliasi (PDF), block model as-mined (.mdl), rekap gabungan (CSV), dan kirim register ke Excel.
Node *Rekap & model gabungan* berganti nama menjadi **Rekap semua flitch** dan tinggal mengerjakan
satu hal — menghitung — sesuai namanya. Tombol export di panel Register diganti petunjuk ke tempat
yang satu itu.

Tombol *Kirim register ke Excel* dinonaktifkan sendiri bila Excel tidak terpasang, dengan alasannya
di tooltip — bukan dimatikan diam-diam.

Diperiksa dengan menekan ke-66 node lalu merekam isi panelnya: ekspor `.mdl` / PDF / CSV kini
muncul di **satu** node saja.

## 115. GC-Ex Drill Hole: semua ekspor menanyakan lokasi & nama berkas

Permintaan pemilik: pola ekspor di bagian 113 diterapkan juga ke modul Drill Hole.

Keadaan sebelumnya sama persis dengan Block Model: **17 titik unduh di 8 berkas**, semuanya memakai
`<a download>`, sehingga di aplikasi terpasang berkas jatuh diam-diam ke folder Download dengan nama
yang sudah dipatok — padahal jembatan Electron sudah menyediakan dialog Simpan dan tidak pernah
dipanggil dari halaman ini juga.

Sekarang semua lewat satu pintu `gxSimpan()` yang identik: dialog Simpan Windows di aplikasi
terpasang, `showSaveFilePicker` di peramban, dan minimal **menanyakan nama berkas** bila keduanya
tidak ada.

| Berkas | Yang dialihkan |
| --- | --- |
| `gcex_dh_base.html` | tiga pembantu unduh (`gsDl`, `dgDl`, `gxDl`), rencana bor CSV, PNG peta, validasi data bor, viewer `.html` lengkap, proyek `.dh3d` |
| `flt_dh.js` | sesar CSV + DXF |
| `sl_dh.js` | laporan lapisan & grid CSV |
| `prof_dh.js` | profil kadar CSV |
| `kp_dh.js`, `fq_dh.js` | keluaran panel masing-masing |
| `arun_dh.js`, `ar3_dh.js` | laporan Autorun CSV |

Berkas `.prj` sudah ikut sejak Block Model, sebab Drill Hole memakai `prj.js` yang sama.

### Cara membuktikannya: perilaku, bukan rupa kode

`tools/uji/uji_ekspor.py` **memalsukan jembatan aplikasi terpasang** (`gcexDesktop.api.saveFile`),
lalu memanggil fungsi ekspor yang sungguhan dan mencatat dua hal: apakah dialog Simpan benar-benar
dipanggil (dengan nama berkas dan penyaring jenis apa), dan apakah masih ada yang lolos mengunduh
diam-diam lewat `<a download>` — yang dicatat terpisah dengan membungkus `HTMLAnchorElement.click`.
Jadi yang diperiksa perilakunya, bukan tampak luar kodenya.

### Regresi yang nyaris lolos, dan mengapa pemeriksaan biasa tidak menangkapnya

Pengganti untuk ekspor PNG peta membuang `}};im.src=url;});}` di ujung baris aslinya. Akibatnya
**seluruh sumber viewer gagal diurai**, `SA` tidak pernah terbentuk, dan Drill Hole memuat lubang bor
tetapi **nol blok**.

Yang berbahaya: tidak ada pesan galat di layar, aplikasi terbuka normal, data bor masuk — hanya block
model yang diam-diam kosong. Dan `node --check` pada tiap berkas sumber **lolos semua**, sebab tiap
berkas memang seimbang; yang tidak seimbang adalah hasil gabungannya di dalam
`<script type="text/plain" id="vsrc">`.

Ditemukan dengan membandingkan **keseimbangan kurung per potongan perubahan** terhadap versi
sebelumnya: dari 17 perubahan, 16 seimbang dan satu menyimpang +4 kurawal — langsung menunjuk baris
yang salah tanpa menebak. Terbukti pulih: 610 lubang **dan** 66.147 blok, tanpa galat.

Dua hal yang diubah pada cara kerja setelah ini: perubahan massal seperti ini diperiksa keseimbangan
kurungnya **sebelum** dibangun, dan pemeriksaan "aplikasi masih hidup dan datanya masuk" dijadikan
langkah wajib sebelum apa pun dinyatakan selesai — karena pemeriksaan sintaks per berkas lolos untuk
bug semacam ini.

### Yang tidak disentuh

**DB-Ex sengaja tidak diubah.** Sumbernya tidak ada di pohon ini (dikerjakan sesi lain), jadi
mengubahnya dari sini berisiko bentrok.

## 116. Block model di 3D dipotong di RL flitch, bukan hanya dipilih

Laporan pemilik, dengan tangkapan layar versi **0.24.31** yang sudah memuat perbaikan bagian 113:
tampilan 3D masih berbentuk "pagar" tegak, bukan pulau-pulau berbatas rata seperti Surpac.

### Perbaikan sebelumnya baru setengah jalan

Bagian 113 membuat block model **dipilih** berdasarkan flitch aktif. Tetapi blok yang terpilih tetap
digambar **utuh setinggi aslinya** — tidak dipotong di RL flitch.

Direproduksi dengan setelan yang terlihat di layar pemilik (`flMode` = *Komposit seluruh tebal
flitch*, metode tonase *Seperti Surpac*, tinggi flitch **1,5 m**):

| Flitch 1,5 m (239,25 – 240,75) | Yang digambar |
| --- | --- |
| Sebelum | 238,75 – 241,25 = **2,5 m** (tinggi penuh blok) |
| Sesudah | **239,25 – 240,75** (tepat flitch) |

Pada model pemilik efeknya lebih parah daripada sekadar "kelebihan 1 m": `bmgczone3` memakai
sub-blok bertinggi **campur 0,75 / 1,5 / 3 m**. Setiap blok 3 m yang menyentuh flitch 1,5 m digambar
penuh 3 m, blok 0,75 m digambar 0,75 m — jadi tebalnya melebihi flitch **dan** ujung atas-bawahnya
bergerigi. Itulah bentuk pagar yang dilaporkan.

Sekarang tinggi tiap kubus **dijepit** ke [bawah, atas] flitch. Yang berubah hanya **geometri yang
digambar**; pemilihan blok, tonase dan laporan tidak tersentuh sama sekali. Kunci penghapusan muka
tersembunyi ikut memakai tinggi efektif, supaya penggabungan muka antar-blok bertetangga tetap benar
dan jumlah segitiga tidak membengkak.

### Mengapa uji sebelumnya lolos padahal cacatnya masih ada

Ini bagian yang paling penting untuk tidak diulang. Uji bagian 113 memakai flitch **2,5 m**, yaitu
**sama persis dengan tinggi blok** data latihan. Dengan flitch sebesar itu, "blok dipilih lalu
digambar utuh" dan "blok dipotong di RL flitch" menghasilkan angka yang **identik** — 238,75 – 241,25
pada keduanya. Ujinya lolos, laporannya meyakinkan, dan cacatnya tetap hidup sampai pemilik
melihatnya sendiri di lapangan.

`tools/uji/uji_tebal_flitch_3d.py` karena itu sengaja memakai flitch **1,5 m, lebih KECIL dari tinggi
blok**, pada dua mode komposit (`comp` dan `mid`, yang menempuh cabang berbeda di `bxSel()`), dan
**gagal** bila tebal yang digambar tidak sama persis dengan tebal flitch. Pelajarannya umum: sebuah
uji yang parameternya kebetulan membuat dua perilaku berbeda memberi angka sama bukanlah uji — ia
hanya pengesah.

## 117. Judul Properti mengikuti panelnya, dan tiga dialog yang tidak pernah terlihat

**Versi:** GC-Ex Block Model 0.24.33.

Tiga laporan pemilik yang tampak terpisah, satu akar yang sama: sesuatu di layar tidak
dipertanggungjawabkan oleh node yang sedang dipilih.

### 117.1 Tombol *Per desain pit & progres topo-ke-topo* tidak bereaksi

Node `rep.x` didaftarkan sebagai **kartu aksi** padahal yang ingin ditampilkan adalah sebuah
**panel**. Tombolnya memanggil panel itu, lalu sistem kartu menggambar kartu node berikutnya di
atasnya, sehingga yang terlihat pemilik: ditekan, lalu kembali ke *Reporting (constraint)*.
Perbaikannya satu baris &mdash; node itu diberi `tab: 'Rep'` sehingga menjadi node panel biasa.

### 117.2 Judul Properti tertinggal di node lama

Beberapa perintah memindahkan tab **sendiri**: `lyApply()` menerapkan flitch lalu berpindah ke tab
Block Model. Pembungkus `uiTab` menanggapinya dengan **melepas fokus panel** dan membiarkan sorotan
di node sebelumnya. Akibatnya dua hal sekaligus: judulnya berbunyi **Sayatan** di atas panel **Dig
block**, dan karena fokus dilepas, isian **otomatis dan manual tampil bersamaan** &mdash; persis
kebalikan dari aturan satu node satu fungsi.

Sekarang perintah yang memindahkan tab sendiri **memilih node pemilik panelnya**
(`PT.select('fl.2d')`), sehingga judul, sorotan dan isi berasal dari satu sumber.

Diukur A/B pada aplikasi sungguhan, dengan memilih node *Sayatan* lalu menjalankan `lyApply()`:

| Build | Judul sesudah `lyApply` | Segmen `#dbBody` yang tampak |
|---|---|---|
| lama | `Sayatan` | &mdash; |
| baru | `Buat Flitch Aktif` | `fl` saja |

### 117.3 Pemeriksaan dig block, Rekap harian dan Laporan periode tidak muncul

Ketiganya membuat dialognya dengan `class="bxdlg"`. Kelas itu **tidak punya satu pun aturan CSS**
di seluruh sumber. Dialognya terbuat dengan benar dan `display:flex` dipasang, tetapi tanpa
`position:fixed` ia ikut aliran halaman biasa dan berhenti di `top=950` pada jendela setinggi 950
piksel &mdash; tepat di bawah tepi layar. Tombolnya terasa mati padahal fungsinya berjalan penuh.

Aturan yang ditambahkan (berdampingan dengan `.bsdlg` yang sudah ada):

```css
.bxdlg{position:fixed;inset:0;z-index:9000;background:rgba(10,20,35,.45);
       display:none;align-items:center;justify-content:center;padding:18px}
.bxdlg .impBody{overflow:auto}
```

### 117.4 Mengapa pemeriksaan sebelumnya lolos

Harness pemeriksaan node hanya memastikan elemen dialognya **ada di DOM** &mdash; dan ketiganya
memang ada, hanya tidak terlihat. `tools/uji/uji_dialog.py` kini mengukur **letak kotaknya terhadap
jendela**: terhadap build lama ketiganya `DI LUAR LAYAR (top=950)`, terhadap build baru ketiganya
`TERLIHAT`. Sama seperti pelajaran bagian 116: memeriksa keberadaan, bukan akibat, bukanlah uji.

## 118. Klik string di Sayatan 2D hanya mengenai flitch aktif

**Versi:** GC-Ex Block Model 0.24.34.

Pada Sayatan 2D, ore line dari elevasi lain memang sengaja ikut ditampilkan sebagai rujukan arah
bijih. Yang salah bukan ia terlihat, melainkan ia **boleh diklik**.

`dbPick()` menelusuri seluruh `DG.S` dengan saringan `vis && closed && !inner` saja — tanpa satu
pun pemeriksaan elevasi — lalu memilih garis terdekat ke kursor **dalam piksel**. Di bidang datar,
garis dari RL lain diproyeksikan ke tempat yang sama, sehingga ia bersaing setara dengan garis yang
benar. Akibatnya: hendak memilih ore line hijau pada flitch aktif, yang terpilih garis coklat muda
dari elevasi lain.

Sekarang `dbPick()` memakai saringan bench yang **sama persis** dengan `lyPolys()`:

- bila string punya `s.db`, atap dan lantainya harus cocok dengan flitch aktif;
- string pada bidang non-horizontal dikecualikan;
- selain itu, `z` titik pertamanya harus berada di dalam rentang flitch.

Satu sumber kebenaran untuk pertanyaan "string ini milik flitch mana".

### 118.1 Dua tes cacat yang dibuang lebih dulu

| Percobaan | Apa yang terjadi |
|---|---|
| 1 | Data latihan tidak memuat satu pun string di elevasi lain (`stringLuarFlitch: 0`), tetapi tesnya tetap berbunyi "BENAR" — tidak menguji apa pun |
| 2 | Dua poligon dibuat **berbagi tepi persis sama**; klik di tepi yang satu berjarak **nol** dari tepi yang lain, dan `d<best` yang ketat selalu memenangkan yang terdaftar lebih dulu — build lama ikut lolos |
| 3 | Keduanya dipisah 150 m: build lama memilih `String 17 (LG elevasi lain)`, build baru tidak memilih apa pun |

Pelajarannya sama dengan bagian 116 dan 117, kali ini dua kali dalam satu perbaikan: tes yang
parameternya membuat perilaku benar dan perilaku salah memberi hasil sama bukanlah tes.

## 119. Import lantai As-Mined diberi nama sesuai isinya

**Versi:** GC-Ex Block Model 0.24.35.

Pertanyaan pemilik ada dua — mengapa masih ada tombol *Import pick-up* padahal sudah ada import
boundary dan import pick-up atap, dan di mana CSV **lantai** di-import — tetapi jawabannya satu:
**tombol yang disangka berlebih itu justru import lantai**, dan satu-satunya yang ada.

Di dalam aplikasi keduanya memang terpisah dan keduanya dipakai:

| Simpanan | Isi | Dipakai oleh |
|---|---|---|
| `D.pts` | titik pick-up **lantai** | `amFloorFn()` — interpolasi lantai IDW per poligon |
| `D.ptsR` | titik pick-up **atap** | `amRoofPts()` — batas atas volume as-mined |

Yang salah hanya penamaannya. Judul kotaknya berbunyi "Titik pick-up survey", tombolnya "Import
pick-up", petunjuknya "CSV: ID, X/East, Y/North, Z/RL, Kode." — tidak satu kata pun menyebut
**lantai**, sementara kotak tepat di bawahnya menyebut dirinya "Titik pick-up ATAP" dengan jelas.
Satu kotak bernama spesifik berdampingan dengan kotak bernama umum membuat yang umum terbaca
sebagai duplikat, sekaligus membuat fungsi yang sedang dicari terlihat seolah tidak ada.

Tidak ada kode perhitungan yang diubah. Yang diubah namanya:

- judul: **Titik pick-up LANTAI (floor) penggalian**
- tombol: **⇧ Import pick-up lantai (.csv / .txt / .str / .dxf)**
- petunjuk: menyatakan titik lantai disimpan **terpisah** dari titik atap
- hitungan titik: "… titik **lantai**"
- kotak atap menunjuk balik ke kotak lantai di atasnya

sehingga dari mana pun pemakai masuk, pasangannya ketemu.

### 119.1 Cara mengujinya

`tools/uji/uji_label_amined.py` membaca **teks panel yang benar-benar tergambar**, bukan kode
sumbernya: build lama `menyebut import LANTAI: False`, build baru `True`, dengan import atap tetap
`True` di keduanya.

## 120. CSV pick-up ID,X,Y,Z,Kode terbaca benar, dan panel atap/lantai dirampingkan

**Versi:** GC-Ex Block Model 0.24.36.

### 120.1 Kolom tergeser satu

Untuk berkas **tanpa baris judul**, `amPtsFile()` dahulu hanya memeriksa apakah kolom pertama
berupa angka; bila ya, ia menetapkan X = kolom 1, Y = kolom 2, Z = kolom 3. Berkas survey pick-up
lazimnya berbentuk **ID, Easting, Northing, RL, Kode** dengan ID berupa angka, sehingga seluruh
kolom tergeser satu:

| Seharusnya | Terbaca sebagai |
|---|---|
| ID (1, 2, 3 …) | Easting |
| Easting (558993) | Northing |
| Northing (9010227) | **Z / elevasi** |
| RL (271,63) | Kode |

Itulah yang terlihat di layar: sumbu Easting berisi 60–160 (nomor titik) dan label elevasi berbunyi
9010238. Karena Z berisi angka ratusan ribu, **tidak satu titik pun** jatuh di pita elevasi flitch
("10 titik atap, 0 di dalam pita RL 271,60–274,50"), jadi atap dan lantai tidak pernah terbentuk —
tanpa satu pun pesan galat, karena setiap angkanya sah sebagai angka.

Kini kolom koordinat dikenali dari **besaran nilainya**, bukan posisinya: dua kolom berdampingan
yang median mutlaknya sama-sama ≥ 1.000 adalah Easting & Northing, di posisi mana pun; Z dan Kode
mengikut sesudahnya; kolom sebelum keduanya diperlakukan sebagai ID. Aturan lama tetap dipakai
sebagai cadangan untuk koordinat grid lokal yang nilainya kecil.

Diuji dengan berkas tiruan berbentuk sama persis dengan berkas pemilik
(`tools/uji/uji_csv_pickup.py`):

| Build | x | y | z |
|---|---|---|---|
| lama | 1 – 60 (nomor ID) | 558990 – 559001 | 9010220 – 9010234 |
| baru | 558990 – 559001 | 9010220 – 9010234 | 270,6 – 272,32 |

### 120.2 Perampingan panel atap & lantai

Setelan halus — pita ke atas / ke bawah RL, buffer dari poligon, pola kode titik, ringkasan
elevasi — dipindah ke balik satu baris **Setelan lanjutan**. Yang tersisa langsung terlihat hanya
pilihan yang dipakai harian. Terukur dari panel yang tergambar: kendali yang langsung terlihat di
kedua kotak turun dari **12 menjadi 3**.

## 121. DB-Ex 0.42.9 — perbaikan galat Borang "Jawaban model bukan JSON"

- Penyebab: dengan bentuk JSON yang dipaksa (0.42.8), sebagian model / versi Ollama mengembalikan jawaban **kosong**, atau model tetap "berpikir" sampai batas token habis sebelum sempat menjawab.
- Sekarang DB-Ex selalu meminta model tidak berpikir (`think: false`), dan bila jawaban kosong / tak terbaca, otomatis **mengulang sekali tanpa format paksa** (baris teks `H|` / `R|`).
- Bila tetap gagal, pesan galat menyebut penyebabnya, mis. *jawaban kosong (selesai: length, 2500 token, berpikir 9000 karakter)* — artinya model kehabisan token karena berpikir — beserta lokasi jawaban mentah `_GCEx_Core\borang\ai_mentah\<nomor>.txt`. Kirim pesan / file itu ke admin.
- Disarankan memperbarui Ollama ke versi terbaru (unduh ulang installer Ollama) supaya `think: false` dan format JSON berjalan benar untuk `qwen3-vl`.

## 122. DB-Ex 0.42.10 — pakai qwen3-vl versi `-instruct` untuk Borang

- Tag polos `qwen3-vl:2b` / `qwen3-vl:4b` di Ollama adalah versi **thinking**: sebelum menjawab, model menulis penalaran panjang — pada borang tulisan tangan sering berputar-putar sampai batas token habis, sehingga jawabannya kosong (galat "Jawaban model bukan JSON" / "jawaban kosong").
- Pasang versi **instruct** (langsung menjawab, jauh lebih cepat):
  ```
  ollama pull qwen3-vl:2b-instruct
  ollama pull qwen3-vl:4b-instruct
  ```
  lalu pilih di dialog AI (tombol **AI lokal** di kanan atas). Laptop tanpa GPU NVIDIA: `2b-instruct`; laptop dengan GPU NVIDIA: `4b-instruct` (atau `8b-instruct` bila memori GPU ≥ 8 GB).
- Dialog AI kini menandai model qwen3-vl tanpa `-instruct`; pesan galat Borang menyebut model pengganti yang tepat.

## 123. DB-Ex 0.42.11 — kolom aktivitas Daily Drilling Report tidak bergeser lagi

- Pada model kecil (`qwen3-vl:2b-instruct`) tabel aktivitas sempat bergeser: rentang jam masuk ke kolom uraian / kategori, uraian hilang.
- AI kini hanya diminta dua nilai per kegiatan: **rentang jam** dan **uraian**. Program memecah jam menjadi Mulai / Selesai, mengisi kategori dari kata kunci uraian, dan menggabungkan baris lanjutan (tanpa jam) ke kegiatan di atasnya.
- Borang yang sudah dibaca dengan versi lama: klik **✦ Baca dengan AI** lagi.

## 124. DB-Ex 0.42.12 — Borang lebih cepat, kolom tidak bergeser (RC, Loading Ore, ROM)

- **Lebih cepat**: AI menulis tiap baris tabel sebagai satu teks `nilai|nilai|…` (jawaban ±separuh lebih pendek) dan foto dipotong otomatis ke lembar kertas sebelum dibaca (papan klip / meja tidak ikut dikirim).
- **RC Drill Logging**: urutan isian mengikuti kolom borang (No, Hole_ID, Tanggal, From, To, Lith, Int_Alt, Min1, Vein_Type, Qt_pct, Remark2). Sample_ID tercetak dihitung program dari No (ditandai kuning — cocokkan dengan scan).
- **Loading Ore** dan **ROM / Crusher**: AI menyalin sel menurut urutan kolom borang; program yang menentukan kelas material, tumpukan rehandling dan status Baru / Lama dari posisi sel. Bila AI salah menghitung kolom kosong, kelas ditandai kuning. Di borang ROM, isi nama ketiga tumpukan rehandling di header (dibaca AI bila tertulis).
- Borang yang sudah dibaca dengan versi lama: klik **✦ Baca dengan AI** lagi.
- Batas kemampuan: model 2b di CPU membaca tulisan tangan kecil (kode litologi / alterasi) kurang andal. Untuk ketelitian pakai mode **Seimbang**, atau `qwen3-vl:4b-instruct` di laptop dengan GPU NVIDIA (jauh lebih cepat dan teliti).

## 125. DB-Ex 0.43.0 (Qt) — tata letak Borang baru

- **Kiri**: pilih jenis borang → **Tambah File** atau **Tambah Folder** (semua foto / PDF dalam satu folder), atau seret file dari Explorer ke halaman Borang. **Daftar File** menampilkan status tiap borang (Belum dibaca, Dalam antrean, Memproses + progres, Perlu verifikasi, Selesai, AI gagal) dan bisa diurutkan. Klik kanan = baca AI / hapus.
- **Tengah**: bilah zoom (− % +), putar ↻, pas layar ⤢, **⛶ fokus scan** (panel samping disembunyikan).
- **Kanan**: tab **Data** (status ekstraksi + *Keyakinan AI*, header dua kolom, tabel, ringkasan kartu angka), tab **Validasi** (daftar galat; klik = lompat ke sel), **Pivot**, **Ekspor**.
- **Bawah**: antrean AI dengan **Baca Semua dengan AI** dan **Batal**.
- Data proyek lama tetap terbaca; hanya tampilan yang berubah.

## 126. DB-Ex 0.44.0 (Qt) — Riwayat, Template, Auto Detect, jenis borang baru

- **Navigasi** di bilah atas (mode Borang): **Borang · Riwayat · Template · Pengaturan · Bantuan**.
- **Riwayat**: semua perubahan di proyek (siapa, kapan, nilai lama / baru); cari, filter jenis, simpan CSV; klik ganda = buka borangnya.
- **Template**: lihat / duplikat jenis bawaan, buat **template kustom** untuk borang lain di site (header, kolom, tipe, petunjuk AI, tabel database). Disimpan di folder proyek (`_GCEx_Core/borang/template.json`).
- **Auto Detect (Rekomendasi)** di daftar jenis: jenis ditebak dari nama file; bila tidak bisa, AI menentukannya sebelum membaca. Klik kanan file → *Ubah jenis borang* / *Deteksi jenis dengan AI*.
- **Jenis baru**: Geological Mapping, Channel Sampling, Drill Progress Report (validasi, pivot, ringkasan, ekspor Excel / CSV / SQLite / Access).
- Kolom bawaan jenis baru masih umum. Bila borang site Anda berbeda: Template → pilih jenisnya → **Duplikat** → ubah kolom → Simpan.

## 127. DB-Ex 0.44.1 — kamus site & aturan baca AI

- AI diminta langsung menulis bacaan terbaik tiap sel dan menandai yang ragu dengan **?** (disorot kuning) — tidak berlama-lama "berpikir".
- **Kamus site** (lihat di **Template**): nilai yang sudah Anda verifikasi ≥ 2 kali (mis. asal material, tujuan, keterangan) dipakai AI sebagai ejaan acuan; bacaan yang mirip dirapikan otomatis dan ditandai kuning. Makin banyak baris diverifikasi, makin tepat.
- **ROM / Crusher & Loading Ore**: versi borang dengan urutan kolom kelas berbeda (mis. SCAT paling kanan) kini dipetakan benar — periksa isian **Urutan kolom kelas** di header.

## 128. Block Model 0.24.37 — laporan titik lantai As-Mined & nama menu

- **Panel Lantai** (As-Mined › Flitch, poligon, lantai & atap, mode *Ikuti lantai pick-up*) kini menyebut berapa titik lantai yang dipakai dan berapa yang dibuang karena di luar pita elevasi. Bila tidak satu pun titik jatuh di pita, atau ada poligon dengan < 3 titik lantai, muncul peringatan kuning: poligon itu memakai RL bawah nominal.
- Peringatan **atap menembus lantai** (luas yang tebalnya dihitung nol) kini juga muncul di panel Lantai.
- Beberapa menu diganti namanya supaya sesuai isinya, mis. **Buka daftar poligon as-mined flitch ini** (dulu *Register as-mined flitch ini*: menu ini hanya membuka daftar, tidak mengubah dig block menjadi as-mined) dan **Simpan salinan proyek (.dh3d)…** (dulu *Unduh file proyek*).
- Angka tonase tidak berubah.

## 129. Drillhole 0.24.39 — node "Import Wireframe Geologi"

- Semua wireframe / solid geologi (Leapfrog `.msh` / `.obj`, Surpac `.dtm` + `.str`, DXF) diimport di **satu** tempat: node **Import Wireframe Geologi** di Project Tree (di bawah Data Spasial). Klik kanan node › *Import wireframe geologi…*, atau pilih node lalu pakai tombol di panelnya.
- Setiap berkas muncul sebagai anak node, **berurutan sesuai urutan import**. Centang = tampil di 3D.
- Menjadikan wireframe domain: klik kanan berkasnya —
  - *Serap jadi domain yang bisa diedit (Mode B)…* — jadi string HW/FW + solid RBF, ikut diperbarui saat ada bor baru;
  - *Iris jadi string / flag interval bor* — membuka Geomodeller Vein dengan wireframe ini terpilih;
  - *Kunci domain … ke wireframe ini* (Mode A) — batas EKSAK untuk audit; *Lepaskan …* untuk kembali ke solid RBF.
- Tombol / menu import wireframe di tempat lain sudah dihapus (Data referensi, Reporting BM, Geomodeller Vein). Reporting BM tetap bisa memakai wireframe yang sudah diimport sebagai *Batas DTM tambahan*.

## 130. Block Model 0.24.38 — node "Import Wireframe Geologi"

- Wireframe / solid geologi diimport dan dilihat hanya di node **Import Wireframe Geologi** (di bawah Data Referensi), berurutan sesuai urutan import.
- **Data Referensi (DTM, titik, string)** kini untuk permukaan pit / topografi (DTM) yang dipakai Reporting › *Pit & progres* dan batas DTM, serta titik survey & string.
- Proyek lama: semua model tampil di node wireframe. Untuk desain pit / topografi, klik kanan › *Pindahkan ke Data Referensi (permukaan pit / topo)*.
- Tombol *+ Import DTM* di Reporting › Batas DTM dihapus; import DTM-nya di Data Referensi.

## 131. Drillhole 0.24.40 — semua alat wireframe di satu panel

- *Iris jadi string HW/FW* dan *Flag interval bor di dalam wireframe* kini ada di panel **Import Wireframe Geologi** (klik kanan berkas › *Iris jadi string / flag interval bor (manual)…*), tidak lagi di Geomodeller Vein.
- Data latihan: desain pit dan survei topografi bulanan masuk **Data Spasial** sebagai versi pit / topografi.
- DXF 3DFACE yang diimport ke Data Spasial disimpan sebagai DTM segitiga (seperti Surpac .dtm).

## 132. Drillhole 0.24.41 — merapikan proyek lama: pit / topo ke Data Spasial

Proyek yang dibuat sebelum 0.24.39 bisa menyimpan desain pit dan survei topografi di daftar wireframe. Untuk memindahkannya:

- Semua sekaligus: klik kanan **Import Wireframe Geologi** › *Pindahkan permukaan pit / topo ke Data Spasial…*. Berkas dikenali dari namanya (pit / topo / DTM / survei). Periksa daftar di jendela konfirmasi; bila ada yang salah, batalkan dan pindahkan satu per satu.
- Satu berkas: klik kanan berkasnya › *Pindahkan ke Data Spasial sebagai versi topografi…* atau *…sebagai versi desain pit…*.
- Hasilnya versi **non-aktif** di Data Spasial; topografi / pit yang aktif tidak berubah. Aktifkan di Data Spasial bila ingin dipakai.
- Batas DTM di Reporting yang memakai berkas itu ikut dialihkan, jadi angkanya tetap sama.

## 128. DB-Ex 0.44.2 — Auto Detect lewat judul tercetak, ganti jenis & baca ulang

- **Auto Detect** kini menyalin judul formulir yang tercetak (mis. DAILY DRILLING REPORT) dan menentukan jenis dari judul itu — tidak lagi tertukar antara Daily Drilling Report dan Drill Progress Report.
- Bila jenis tetap salah (tanda: banyak sel merah): klik **Jenis salah? Ganti & baca ulang** di kartu status, atau klik kanan file → **Ubah jenis borang & baca ulang**. Baris lama dibuang (dengan konfirmasi) lalu borang dibaca ulang AI.

## 133. Drillhole 0.24.42 — 3D lebih ringan, urutan tree sesuai alur kerja

- Geser sayatan, Maju / Mundur, dan ganti centang lapisan kini jauh lebih ringan: lapisan 3D yang tidak berubah (mis. block model) tidak dikirim ulang ke kartu grafis.
- **Ore Geometry** tidak lagi menghitung otomatis saat dibuka; tekan **Hitung intercept & GT** di panelnya.
- Urutan Project Tree: … Struktur Geologi (5) › **Ore Geometry (5b)** › Geomodeller (6 / 6b) › **Geostatistik (7)** › Block Model (8) › Model Estimation (9) › Validasi BM (10) › Reporting BM (11) › Layout & Ekspor (12).
- Export database ada di menu **Database Bor**; export block model .mdl di menu **Block Model** (tidak lagi di Layout & Ekspor).

## 129. DB-Ex 0.44.3 — ROM / Crusher & Loading Ore dibaca utuh

- AI kini menulis satu nilai per kolom besar: **Rehandling** dan **Kelas** ditulis sebagai nama judul kolom tempat centang / tonase berada — tidak lagi 21 sel per baris yang membuat baris bergeser.
- Semua jenis borang: sel kosong ditulis `-` oleh AI; bila jumlah sel satu baris tetap meleset, seluruh isian baris itu disorot kuning untuk dicek.
- Seluruh tabel tidak bisa lagi tertumpuk dalam satu baris (penyebab "hanya 1 baris" di ROM, "0 baris" di Daily Drilling Report, dan waktu baca sangat lama).
- Borang ROM / Loading Ore yang sudah dibaca versi lama: klik **✦ Baca dengan AI** lagi.

## 130. DB-Ex 0.44.4 — potong area borang

- Di bilah atas scan: **✂ Potong** → tarik kotak mengelilingi **tabel** (judul kolom ikut) → lepas mouse. AI hanya membaca area itu: lebih teliti dan lebih cepat.
- **✕** menghapus potongan. **⧉** memakai potongan yang sama untuk semua halaman dari PDF yang sama, atau semua borang sejenis yang belum dipotong (periksa tiap borang — posisi tabel di foto bisa berbeda).
- Setelah memotong, klik **✦ Baca dengan AI** lagi.
- Foto yang hanya memuat sebagian kolom borang (mis. kolom No / Hole ID terpotong) kini tetap terbaca ke kolom yang benar; isi kolom yang tidak tampak (mis. Hole ID) di header / tabel.

## 134. Block Model 0.24.39 & Drillhole 0.24.43 — demo dan tutorial mengikuti tampilan baru

- **Tombol Demo** menunjuk node **Import Wireframe Geologi** untuk langkah wireframe, dan menghitung laporan per pit / progres topo dari versi Data Spasial (Drill Hole) atau permukaan DTM di Data Referensi (Block Model).
- **Tutorial bergambar** (Modelling & Estimasi, Block Model), **Tutorial Update** dan **Petunjuk Teknis** dibangun ulang dengan tangkapan layar versi ini.
- Block Model › As-Mined: tombol **Import pick-up atap** kini sama dengan tombol **Import pick-up lantai** (biru, tulisan putih).

## 135. Drillhole 0.24.44 (Block Model 0.24.40) — plan bor per hari / per bench

- Node **Database Bor › Plan bor (rencana)**: klik kanan → **Plan baru…** membuat plan baru (nama bawaan *Plan tanggal · bench*). Setiap plan tampil **berurutan** sebagai sub-node bernomor (1., 2., …) dengan jumlah titiknya.
- Hanya satu plan **aktif**. Titik baru, Hapus semua, Nomori ulang dan Export CSV di panel bekerja pada plan aktif. Untuk extend di lokasi lama: klik kanan sub-node → **Jadikan plan aktif**, lalu tambah titik.
- Plan aktif digambar magenta tegas, plan lain ungu pudar (3D dan peta plan). Centang sub-node untuk tampil / sembunyi.
- Export: per plan (**Export CSV plan ini…**) atau **Export CSV semua plan…** (satu file, kolom Plan).
- Proyek yang dibuat sebelum versi ini dibuka dengan satu plan bernama **Plan lama**.
- Tutorial Modelling & Estimasi: bab baru **Plan bor harian**. Tombol Demo langkah *Plan bor* membuat **Plan demo**.

## 131. DB-Ex 0.44.5 — AI membaca lebih sedikit

- **Bagian bawah tabel yang kosong** (baris belum diisi) otomatis tidak dikirim ke AI: lebih cepat dan tulisan tampak lebih besar. Tanda tangan di bawah tabel tidak menghalangi.
- **PDF berhalaman banyak**: header (tanggal, shift, crew, lokasi) disalin dari halaman yang sudah terisi (kuning — cocokkan); AI hanya membaca tabel. Baca halaman pertama dulu, lalu **Baca Semua dengan AI**.
- Keduanya bisa dimatikan di **Pengaturan → Meringankan kerja AI**.
- Di bawah hasil baca kini tampil kecepatan, pemakaian GPU, porsi gambar yang dibuang, dan apakah header disalin.

## 136. Drillhole 0.24.45 & Block Model 0.24.41 — menu ⋯ dan baris "+ Tambah …" di Project Tree

- **Satu pintu menu: tombol ⋯** di ujung baris node, sekarang **selalu tampak** (abu-abu tipis). **Klik kanan di Project Tree tidak lagi membuka menu.**
- **Perintah yang menambah isi** tidak lagi di menu ⋯, tetapi baris biru **+ Tambah …** paling bawah di bawah node tersebut. Baris dengan beberapa pilihan (mis. *+ Tambah struktur…*) membuka daftar pilihannya.
  - Drill Hole: + Tambah versi topografi / desain pit / orthofoto, + Tambah titik survey / string, + Tambah wireframe geologi, + Tambah kampanye, + Tambah plan bor, + Tambah titik pick-up (CSV), + Tambah struktur, + Tambah sesar (dari koordinat), + Tambah domain, + Tambah versi block model.
  - Block Model: + Tambah data referensi, + Tambah wireframe geologi, + Tambah preset (dari pengaturan sekarang).
- Menu ⋯ berisi perintah untuk isi yang sudah ada (tampilkan sebagai, jadikan aktif, ganti nama, export, pindahkan, hapus). Node yang menunya kosong tidak menampilkan ⋯.
- Panel Plan Bor tidak lagi punya tombol *+ Plan baru*; plan hari lain dibuat lewat **+ Tambah plan bor…** di Project Tree.
- Tutorial, Tutorial Update, Petunjuk Teknis dan teks Demo menyebut ⋯ / + Tambah, bukan klik kanan.

## 137. Drillhole 0.24.46 & Block Model 0.24.42 — satu pintu import

- **Dihapus dari panel** (import hanya lewat baris **+ Tambah …** di Project Tree):
  - Tombol *Import wireframe geologi* di panel **Import Wireframe Geologi** (kedua aplikasi) → **+ Tambah wireframe geologi…**.
  - Tombol import di panel **Data Referensi** (Block Model: DTM, titik survey, string; Drill Hole: titik survey, string) → **+ Tambah data referensi…** / **+ Tambah titik survey / string…**.
  - Tombol *+ Kampanye baru…* di dialog import / upsert → **+ Tambah kampanye…** di node Database Bor (pilihan kampanye tujuan tetap ada di dialog).
- **Tetap di panel, tanpa baris + Tambah**: *+ Tambah versi topografi / desain pit / orthofoto / block model* di panel **Data Spasial** (Drill Hole) dan tombol *Simpan pengaturan sekarang sebagai preset* di kartu **Preset kelas kadar & tujuan** (Block Model).
- Tutorial, Petunjuk Teknis dan gambar tutorial mengikuti.
- **Daily Drilling Report**: AI kini hanya membaca isian header di bagian atas borang (tanggal, shift, rig, driller, client, DHP ID). WH, DL, HM engine dan bit diisi sendiri bila perlu — sebelumnya AI menyalin nama isian ("DHP_ID", "WH") dan membaca sangat lama.

## 138. Drillhole 0.24.47 — import CSV struktur satu pintu; pick-up tetap di panel Peta

- Tombol **Import CSV struktur** dihapus dari panel Struktur Geologi. Import lewat baris **+ Tambah struktur… › Import CSV struktur…** di Project Tree.
- **Import titik pick-up (CSV)** tetap di panel **Peta (Mapping)**; baris *+ Tambah titik pick-up* di Project Tree dihapus.
- Block Model tidak berubah (tetap 0.24.42).

## 139. Drillhole 0.24.48 — panel Struktur Geologi dan Data referensi dipisah

- Klik node **Struktur Geologi** (atau anaknya) → panel hanya berisi struktur (tabel titik, sumber, titik manual). Judul, tab Titik survey / String dan isinya tidak lagi ikut tampil.
- Klik node **Data referensi (titik survey, string)** → panel hanya titik survey & string; tab **Struktur** tidak muncul.
- Data tidak berubah, hanya tampilan panel yang mengikuti node. Gambar tutorial bab Struktur Geologi diambil ulang.
- Integrasi data tetap: struktur yang dicentang (per sumber) tetap dipakai solid vein RBF, dan saklar **Pakai struktur** per domain tetap berlaku — dibuktikan uji pembanding dengan build sebelum perubahan UI (angka volume identik).

## 132. DB-Ex 0.44.6 — galat "HTTP Error 500" dari Ollama

- **"AI gagal: HTTP Error 500"** = mesin AI Ollama berhenti (biasanya memori penuh setelah banyak borang / mode Seimbang). DB-Ex kini mengulang sekali otomatis dengan gambar lebih kecil; bila tetap gagal, tampil pesan Ollama dan sarannya: tutup aplikasi lain, pilih **Cepat**, atau tutup Ollama dari ikon taskbar lalu buka lagi.

## 140. Drillhole 0.24.49 — nomor titik struktur

- Import CSV struktur **tanpa kolom ID** (mis. `SIM_struktur.csv`: Easting, Northing, RL, …) kini diberi nomor urut **1, 2, 3, …** di kolom **No** tabel titik struktur. Dulu kolom *Northing* terbaca sebagai kolom nomor sehingga No berisi angka Northing.
- Berkas yang punya kolom nomor (No, ID, Point, Kode, Titik, Nama, …) tetap memakai nilai kolom itu. Koordinat, dip dan dip azimuth tidak berubah, jadi model vein tidak terpengaruh.

## 141. Block Model 0.24.43 & Drillhole 0.24.50 — layar kosong karena koordinat liar (STR biner ber-deskripsi)

- **Gejala**: setelah import, 3D hanya menampilkan kotak abu-abu dan sumbu bertuliskan *Easting (+-2.5e+307)* / *Northing (+-3.1e+307)*.
- **Sebab**: file **STR biner Surpac yang punya kolom deskripsi** (D1, D2, …) dibaca dengan panjang rekaman tetap 29 byte, sehingga pembacaan bergeser dan koordinat menjadi angka liar (±1e+250…1e+307). Satu titik liar saja sudah menggeser seluruh proyek sehingga data lain jatuh jauh di luar layar.
- **Perbaikan**: panjang rekaman STR biner dideteksi otomatis (29 byte + 8 byte per kolom deskripsi). Titik berkoordinat tidak masuk akal (> 100.000 km, NaN, 0,0) dibuang per titik dan dilaporkan di daftar file (*⚠ N titik berkoordinat rusak dibuang*). File yang lebih dari separuh titiknya rusak ditolak dengan saran menyimpan ulang sebagai STR teks / DXF. Orthofoto dan batas block model yang tidak masuk akal juga dilaporkan.
- Proyek yang sudah terlanjur tersimpan dengan koordinat liar: titik rusak dibuang dan area proyek dihitung ulang saat dibuka. Bila tampilan masih kosong, import ulang file-nya.

## 142. Block Model 0.24.44 & Drillhole 0.24.51 — Data Spasial langsung dari tombol ⋯

- Permintaan pemilik: tombol ⋯ pada **Data Spasial** dan sub-node **Topografi / Desain pit / Orthofoto** harus langsung menanyakan *file apa* lalu membuka jendela pilih file, bukan kembali ke layar Mulai.
- **Block Model**: ⋯ Data Spasial → *Topografi… / Desain pit… / Orthofoto…*; ⋯ Topografi / Desain pit → *Tambah file …* (digabung) atau *Ganti … dengan file…*; ⋯ Orthofoto → *Import / Ganti orthofoto…*. File dibaca dengan pembaca yang sama dengan layar Mulai, overlay dibangun ulang di tempat, proyek tersimpan (browser / folder proyek). Menu lama *Ganti / tambah lewat Import ulang…* dihapus. Topografi hasil import langsung juga dipakai untuk dig block (Z dari topografi) dan filter .mdl berikutnya.
- **Drill Hole**: ⋯ Data Spasial / Topografi / Desain pit / Orthofoto → *Tambah versi … dari file…* (versi baru, seperti tombol di panel). Tombol di panel tetap ada.
- Uji: `tools/uji/uji_spasial_langsung_bm.py` (SIM_BM_GC_kadar.csv → topo juni → pit fase 1 → ganti topo juli; data tersimpan), `tools/uji/uji_spasial_langsung_dh.py` (versi +1).

## 143. Block Model 0.24.45 & Drillhole 0.24.52 — import block model & data bor langsung dari tombol ⋯

- **⋯ Block Model → Import block model dari file (.mdl / CSV)…** (kedua aplikasi): jendela pilih file terbuka lebih dulu; dialog pemetaan kolom / filter RL-pit-topo lalu tampil dengan file itu sudah terisi, tinggal klik *Muat*.
- **Drill Hole, ⋯ Database Bor**: *Import collar / survey / assay / geologi dari file (tambah / perbarui)…* — jendela pilih file → jendela upsert terbuka dengan file terpasang di slotnya (pemetaan kolom + pratinjau), lalu **Gabungkan**. Sub-node Collar / Survey / Assay / Geologi punya menu yang sama untuk tabelnya. *Tambah / perbarui beberapa tabel sekaligus (upsert)…* tetap ada untuk banyak file.
- Aturan upsert tidak berubah: collar per Hole ID, survey / assay / geologi diganti per hole yang ada di file baru.
- Uji: `tools/uji/uji_import_langsung.py` (BM & DH: dialog terisi; DH: +32 collar SIM_split_collar.csv).

## 144. Block Model 0.24.46 & Drillhole 0.24.53 — Demo & tutorial menunjuk menu ⋯ import

- **Tombol Demo**: langkah *Import block model* (Block Model) kini menunjuk tombol ⋯ node Block Model dan membuka menunya; langkah baru *Data Spasial lewat ⋯* (Block Model) dan *Import data lewat tombol ⋯* (Drill Hole, node Database Bor) memperlihatkan pintu import langsung dari Project Tree.
- **Tutorial bergambar**: gambar baru menu ⋯ Block Model & Data Spasial (Tutorial Block Model) dan menu ⋯ Database Bor & Data Spasial (Tutorial Modelling & Estimasi), dibuat dari data latihan simulasi.
- **Perbaikan Drill Hole**: di 0.24.52 tombol ⋯ pada node **Database Bor** tidak membuka menu (menu sub-node tetap bekerja). Sudah diperbaiki.

## 145. Block Model 0.24.47 & Drillhole 0.24.54 — Jeda berganti panel / atribut dikurangi, kotak Kinerja & grafis

- **Apa yang diukur**: berpindah panel sendiri murah (< 35 ms). Yang terasa adalah **ganti atribut warna** (geometri kubus / segmen bor dibangun ulang 1–3 detik lalu digambar ±1 detik; di Drill Hole sempat digambar dua kali per klik), **centang overlay** (rentang sumbu otomatis berubah sehingga semua lapisan 3D diunggah ulang ke kartu grafis), dan **ubah ukuran jendela** (digambar ulang berkali-kali).
- **Perbaikan**: kembali ke atribut yang pernah ditampilkan kini seketika (beberapa atribut terakhir disimpan); centang overlay / collar / label tidak lagi mengunggah ulang semua lapisan 3D (setiap lapisan diberi tanda pengenal tetap dan dibandingkan isinya, bukan posisinya di daftar); rentang sumbu 3D dibuat tetap selama filter hole / bench / sayatan sama (kotak 3D juga tidak melompat; ganti filter tetap menyesuaikan rentang); ubah ukuran jendela digambar ulang sekali; klik atribut di Drill Hole digambar sekali; dialog Satuan elemen tidak menyegarkan bila tidak ada yang diubah. Hubungan antar data tidak berubah: diuji dengan membandingkan hasil dari cache vs hitung ulang (identik) dan gambar 3D dengan / tanpa pelewatan lapisan (identik).
- **Kotak Kinerja & grafis** (Pengaturan tampilan › Tampilan & performa): menyebut apakah **kartu grafis dipakai**. Bila tertulis *render perangkat lunak*, 3D digambar oleh prosesor — inilah penyebab paling mungkin bila jeda masih terasa; kotak memberi langkah di Windows (driver, Settings › Display › Graphics › *High performance*, mode daya). Kotak juga mencatat jeda 12 aksi terakhir; tombol **Salin laporan kinerja** menyalin teksnya untuk dikirim saat melapor.
- Dokumen: tutorial bergambar kedua aplikasi (sub-bab *Kinerja & grafis*), Petunjuk Teknis, Tutorial Update bab 12.

## 146. DB-Ex 0.44.7 — Daily Drilling Report: tabel lubang & kegiatan disusun ulang

- **Gejala**: tabel *Meterage / lubang* berisi puluhan baris yang masing-masing hanya satu nilai (From = 0, 15, kode Hole ID, nomor lubang, Az, Dip, jam kegiatan, uraian), Meterage 0 m, atau header berisi `? | ? | ?`.
- **Sebab**: model AI kecil menulis tabel satu sel per elemen (bukan satu teks `from|to|hole|az|dip` per lubang), atau "macet" mengulang tanda tanya.
- **Perbaikan**: DB-Ex mengelompokkan kembali sel itu per lubang (Hole ID yang terpecah dua, mis. kode + nomor, digabung), jam + uraian yang tersasar menjadi baris kegiatan, isian tanpa huruf / angka diabaikan, kegiatan kembar berturut-turut dibuang, dan contoh di petunjuk AI tidak lagi berisi kegiatan nyata (dulu disalin model menjadi baris palsu). Borang yang sudah terbaca dengan gejala ini: klik **Baca dengan AI** sekali lagi.
- Tulisan sangat padat (± 40 kegiatan dengan jam kecil) tetap sulit bagi model 2b: **✂ Potong** ke tabel kegiatan saja agar tulisan tampak lebih besar bagi AI.

## 147. DB-Ex 0.44.8 — Daily Drilling Report: baris yang melintasi tabel lubang & kegiatan

- **Gejala** (setelah ✂ Potong yang memuat tabel lubang dan kolom kegiatan sekaligus): kolom *Dip* berisi `65|60|06:30-06:45|travel to opp`, Hole ID 24_265 dan nomor lubang terpisah, kegiatan hanya sebagian.
- **Sebab**: model AI membaca satu baris cetak dari kiri ke kanan melintasi kedua tabel.
- **Perbaikan**: bagian yang diawali rentang jam dipindah menjadi baris kegiatan (digabung dengan yang sudah ada, urut jam), sisanya disusun sebagai lubang. Klik **Baca dengan AI** lagi pada borang yang terdampak.

## 148. DB-Ex 0.45.0 — Mode Transkrip: AI menyalin, pengguna menentukan kolom

- Tab baru **✎ Transkrip** di panel kanan Borang (atau klik kanan file → *Salin teks dengan AI*). AI hanya menyalin tulisan menjadi teks; tabel Data tidak berubah sampai Anda menekan **Terapkan ke tabel ▶**.
- Panel 1 teks (rapikan: `Label: nilai` untuk kop, sel dipisah `|` untuk tabel; pemisah bisa diganti), panel 2 isian kop → header, panel 3 kisi dengan dropdown tujuan kolom di baris pertama (klik nomor baris = lewati). Usulan pemetaan otomatis; pemetaan tersimpan per jenis borang dan dipakai lagi.
- Cocok untuk borang padat (Daily Drilling Report 30–40 kegiatan) yang salah kolom bila dibaca langsung: kesalahan AI terlihat dan diputuskan manusia, bukan ditebak program. Pembacaan langsung (**✦ Baca dengan AI**) tetap ada untuk borang yang rapi.
- Teknis: kolom `teks` di tabel `docs`, berkas `transkrip_map.json` dan `ai_mentah\<id>_teks.txt` di `_GCEx_Core\borang`; modul backend `core_transkrip.py`, Qt `forms_transkrip.py`. Uji: `backend/tests/test_core_transkrip.py`, `app_core_qt/tests/test_qt_m11.py`.

## 149. Block Model 0.24.48 & Drillhole 0.24.55 — Tampilan 3D kosong pada proyek tanpa data bor (perbaikan 0.24.47 / 0.24.54)

- **Gejala**: setelah 0.24.47 / 0.24.54, proyek yang hanya berisi block model dan string (tanpa lubang bor) menampilkan kotak 3D
  dengan sumbu −1…2 dan hanya string dig block yang tampak; block model ada di legenda tetapi di luar kotak.
- **Sebab**: rentang sumbu tetap yang baru dihitung dari daftar koordinat lubang bor + overlay saja; tanpa lubang bor daftar itu
  kosong (diisi 0…1). Dulu tidak terasa karena rentang otomatis mengikuti semua lapisan.
- **Perbaikan**: rentang tetap kini digabung dari batas **semua lapisan 3D** (block model, string, wireframe, overlay, bor).
  Diuji pada kedua aplikasi: rentang selalu memuat seluruh data pada awal, saat lubang bor / topo / pit dicentang-lepas, dan pada
  flitch aktif.
- **Juga diperbaiki**: berganti flitch (Maju / Mundur) pada 0.24.47 bisa menampilkan kubus flitch *sebelumnya* dari cache — kini
  batas RL flitch ikut diperhitungkan; dan langkah Demo *Topografi, desain pit & orthofoto* yang panelnya tertimpa panel flitch.
- **Catatan tampilan**: bila block model terlihat hanya sepotong, periksa dua pemotong yang memang disengaja — **Flitch Aktif**
  (kubus digambar setebal flitch) dan **Sayatan › Opsi slab › Potong data di dalam slab (3D)** (hanya blok di dalam slab di
  sekitar Elevasi sayatan). Lepaskan keduanya untuk melihat model utuh.

## 149. DB-Ex 0.45.1 — Transkrip: baris dropdown menempel

- Baris pertama kisi (dropdown tujuan kolom) tidak lagi ikut tergulir; nomor baris kisi kini = nomor baris teks tabel.

## 150. DB-Ex 0.45.2 — Transkrip: scan kolom satu per satu; jendela muat di layar

- **Scan kolom kiri → kanan** (mis. DDR: Meterage, Hole ID, Azimuth, Dip, Drilling details): pilih **+ kolom di kanan** di sebelah tombol *Salin teks dengan AI*, lalu ulangi untuk tiap kolom: ✂ Potong kolom → Salin. Tiap salinan ditempel sebagai kolom baru di kanan teks (baris ke-1 ke baris ke-1, dst.). Setelah kolom terakhir, atur dropdown tujuan bila perlu lalu **Terapkan** sekali.
- Pastikan setiap potongan kolom mencakup **baris yang sama** (dari baris judul sampai baris terakhir); sel kosong di kertas sebaiknya ditulis `-` di teks agar baris tetap sejajar — periksa di kisi sebelum Terapkan.
- **+ di bawah**: potongan atau lembar lanjutan tabel yang sama. **Ganti teks**: teks lama diganti (meminta konfirmasi).
- Satu tombol **Terapkan ke tabel ▶**, di bawah kisi.
- Jendela DB-Ex tidak lagi melebar melewati layar (tombol kanan terpotong): halaman bisa digulir mendatar bila jendela sangat sempit.

## 151. DB-Ex 0.46.0 — AI menyalin, Anda memutuskan (Baca dengan AI cara Transkrip)

- **Cara baca bawaan berubah**: Pengaturan → *Cara AI membaca borang* = **Transkrip + pemetaan Anda** (disarankan). *Langsung ke tabel* (cara lama) tetap bisa dipilih.
- **✦ Baca dengan AI / Baca Semua**: AI menyalin teks borang. Tabel langsung disusun bila DB-Ex **yakin** — judul kolom di teks dikenali dari pilihan Anda sebelumnya, atau Anda pernah memutuskan pemetaan untuk jumlah kolom yang sama. Bila belum: borang berstatus ungu **Perlu pemetaan kolom**, tab ✎ Transkrip terbuka, Anda tentukan kolomnya lalu **Terapkan**. Keputusan itu dipakai untuk borang berikutnya (jenis sama), dan **Terapkan juga ke n borang lain ▶▶** menerapkannya ke borang yang sudah tersalin & menunggu.
- **Alat di kisi** (panel 3): klik ganda sel = sunting · klik kanan sel = sisipkan / hapus sel (sel kanan bergeser), gabung / pecah sel, gabung ke baris atas, jadikan isian kop, lewati, sisipkan / hapus baris · klik kanan judul kolom = gabungkan baris-baris yang kolom ini kosong ke atas (uraian dua baris), pecah kolom (spasi / rentang jam │ sisanya), gabung, tukar, sisipkan, hapus kolom. Tujuan kolom **Kop · Tanggal / Shift / …** untuk nilai kop yang ditulis di tiap baris. Semua suntingan tertulis kembali di teks (panel 1).
- Keputusan tersimpan di `_GCEx_Core\borang\transkrip_map.json` (per jenis: per jumlah kolom, judul kolom → tujuan, label kop → isian header). Hapus berkas itu untuk mulai dari nol.

## 152. Drillhole 0.24.56 & Block Model 0.24.49 — Slicer satu tombol, panel Assay, permukaan topo/pit, STR berdeskripsi teks

- **Permukaan topografi & desain pit kini tampil di 3D Drill Hole.** Sebelumnya pengaman gambar membuang semua permukaan hasil
  Delaunay (tanpa indeks segitiga), sehingga hanya garis kontur yang terlihat walau node aktif. Warna permukaan bawaan **seragam**;
  pilihan gradasi elevasi + pemilih warna ada di panel Overlay (kedua aplikasi).
- **Tombol bernomor lingkaran** (① Topografi, ② Pit, …) dihapus di seluruh aplikasi.
- **Node Assay** membuka panel *Assay — tampilan kadar*: unsur yang ditampilkan, cutoff, klasifikasi diskrit / gradasi, colorscale.
  Sub-node unsur hanya daftar (tidak bisa diklik; yang bertanda warna = sedang tampil). Fitur upsert / export / filter bench & hole
  tetap di node Database Bor dan Collar.
- **Slicer** (Drill Hole): satu tombol di bilah atas menggantikan menu Sayatan ▾. Popup: Dip, Dip azimuth, preset Plan / Tegak E–W /
  Tegak N–S / Garis di peta, Lebar slab, Langkah (terpisah), Posisi, Pusat bidang (E, N, RL; Pusat data / Pusat pandangan),
  Mundur / Maju, Potong data / Tampilkan bidang / Profil topo, Sayatan 2D, Sayatan 3D, Digitasi, Pengaturan lanjutan. Panel Sayatan
  di Properti tetap ada (mode Slicer = pilihan pertama).
- **Plan bor** digambar garis utuh (tidak putus-putus) di 3D dan peta.
- **STR biner Surpac berdeskripsi teks** (mis. berkas desain pit dengan kolom D1 = "2"): deskripsi disimpan sebagai teks berpanjang
  bebas di belakang tiap titik, bukan angka biner tetap — pembaca lama membaca bergeser sehingga koordinat liar / kosong. Kini
  dibaca benar; format lama tetap didukung lewat jalur cadangan. Uji: `tools/uji/uji_str_desc_teks.py`.
- **Block model besar tampil utuh (LOD).** Bila jumlah blok terpilih melebihi batas profil Kinerja, dulu hanya kelas tertinggi yang
  digambar (model terlihat "sepotong-sepotong"). Kini blok digabung ke sel yang lebih besar (kelipatan ukuran blok induk) dan tiap sel
  digambar dengan warna kelas dominannya — seluruh model dan semua kelas tetap terlihat; angka legenda tetap jumlah blok asli;
  statistik, tonase & laporan tidak berubah. Naikkan profil Kinerja (Seimbang / Penuh) untuk sel yang lebih halus atau blok asli.
- **Acuan koordinat proyek yang terlanjur salah** (sumbu bertuliskan *Easting (+−52882000)*; sisa STR pit yang dulu salah terbaca):
  saat block model dimuat dan acuannya > 100 km dari model, acuan dihitung ulang dari batas block model, titik topografi / pit yang jauh
  dibuang, proyek disimpan dan halaman dimuat ulang (ada pemberitahuan). File spasial yang tidak overlap dengan collar / block model kini
  tidak dipakai sama sekali (ditandai merah di daftar).
- **Reporting Block Model › Pit & progres**: Block Model hanya menyimpan satu topografi dan satu desain pit aktif, sehingga pilihan
  *Topografi atas / bawah* dulu hanya "Topografi aktif" / "Desain pit aktif". Kini ada tombol **Pilih file topografi (STR / DXF / CSV /
  DTM)…** di bawah tiap pilihan (dan **Pilih file desain pit…** di mode Per desain pit): file survei dibaca langsung dan dipakai untuk
  laporan itu (tidak mengubah topografi tampilan). Untuk menyimpannya di proyek, import sebagai Permukaan DTM di Data Referensi.

## 153. Block Model 0.24.50 & Drillhole 0.24.57 — Permukaan & ortho resolusi tinggi, penyamaan kedua aplikasi

- **Permukaan topografi & desain pit** kini dibangun dari **seluruh titik survei** (TIN penuh), bukan 15 ribu titik contoh: lekuk
  kecil tetap tampak dan tidak berubah saat zoom. Berlaku di kedua aplikasi.
- **Orthofoto**: pilihan Resolusi bawaan **Otomatis** — setajam anggaran profil Kinerja (Hemat 300 rb · Seimbang 800 rb · Penuh 1,5 juta
  titik; tidak lebih halus dari piksel ortho) dan makin halus saat kamera 3D di-zoom masuk. Dulu bawaan 2 m. Bila terasa berat, pilih
  profil Hemat atau resolusi tetap (4 / 2 / 1 / 0,5 / 0,25 m).
- **Penyamaan Block Model ↔ Drill Hole**: Block Model mendapat tombol **Slicer** (sama dengan Drill Hole 0.24.56); Drill Hole mendapat
  tampilan block model besar utuh (LOD sel, dulu sampel titik), perbaikan acuan koordinat otomatis, dan pengabaian file spasial yang tidak
  overlap. Reporting Block Model di Block Model diperiksa terhadap Drill Hole: engine, bagian dan constraint-nya sama (port langsung).

## 154. Block Model 0.24.51 — Solid Vein Aktual (trial): tubuh vein tergali sebagai solid 3D

- **Node baru** paling bawah di Project Tree Block Model: **Solid Vein Aktual (trial)**. Terpisah dari As-Mined; isinya dikelompokkan per
  **Periode** (+ Tambah periode…).
- **Titik atap**: import pick-up survey atap galian (CSV / STR / DXF), pilih file yang dipakai, saring **RL min – RL maks**.
- **Poligon per flitch**: **Digit poligon** di plan flitch aktif (kursor snap ke titik atap), atau **Ambil as-mined** / **Ambil dig block**.
- **Bangun solid**: poligon flitch berurutan disambung dengan cara kerja Surpac (semua titik dipakai; metode luas permukaan minimum,
  equi-angular atau proporsional). **Jarak sambung maks** menentukan kapan dua poligon dianggap satu tubuh — lebih jauh dari itu menjadi
  pulau tertutup sendiri. Flitch tanpa poligon memutus solid; poligon bercabang dibelah otomatis.
- **Tampil di 3D**: garis poligon dan tubuh solid selalu digambar di jendela 3D selama centang node menyala; tombol
  **Lihat di 3D (zoom ke vein)** mendekatkan kamera ke sana. Tiap pulau punya centang tampil sendiri.
- **Hasil**: volume & tonase (× SG) per pulau, tanda tertutup, ekspor **DTM + STR Surpac**, **DXF 3DFACE**, **CSV**. Solid bisa dipakai
  sebagai batas domain di Reporting Block Model.
- Masih **trial**: bandingkan volumenya dengan Surpac sebelum dipakai untuk laporan resmi. GC-Ex Drillhole tidak berubah (0.24.57).

## 155. Block Model 0.24.52 — Solid Vein Aktual: perbaikan sesudah diuji dengan pick-up nyata

- **File pick-up tetap terpisah.** Tabel *Titik atap* kini satu baris per **file** (dulu file CSV melebur menurut kolom kode survey).
- **RL flitch dibaca dari nama file** (mis. `ACT_SO261108OB_235-5_234_Z4.csv` = RL 235,5–234) dan bisa dikoreksi di tabel. Titik
  dipakai untuk flitch file-nya, bukan dipilah dari elevasinya — atap galian nyata naik-turun melewati batas flitch. Tombol **Buka**
  menjadikan flitch file itu flitch aktif.
- **Z sudut poligon** yang tepat di titik pick-up memakai elevasi titik itu apa adanya.
- **Garis luar otomatis (semua file)**: usulan poligon dari gugus titik tiap file, dengan parameter *Sisi terpanjang (m)*. Ini usulan:
  periksa di plan tiap flitch; poligon yang tidak cocok dihapus lalu didigit.
- **Jarak sambung maks** bawaan kini 3 m (dulu 10 m), supaya dua flitch yang hanya bersebelahan tidak ikut tersambung.

## 156. Block Model 0.24.53 — Solid Vein Aktual berdiri sendiri, edit titik poligon, data susulan

- **Berdiri sendiri.** Titik atap menu ini disimpan terpisah (tidak lagi berbagi dengan As-Mined); tombol *Ambil as-mined* dan
  *Ambil dig block* dihapus. **Titik atap yang diimport pada 0.24.51 / 0.24.52 perlu diimport ulang di menu ini.**
- **Poligon**: digit manual dengan snap ke titik atap, atau usulan **Garis luar otomatis**.
- **Edit titik poligon** (tombol ✎ di baris poligon): seret titik untuk menggeser (menempel ke titik atap), seret kotak kecil di tengah
  sisi untuk menyisip titik, klik ganda / klik kanan titik untuk menghapus, lalu **Selesai**.
- **Data susulan**: import ulang file bernama sama mengganti titik file itu; file baru menambah baris. Sesudah poligon baru didigit,
  **Bangun solid** membangun ulang seluruh solid periode. Panel menandai bila solid belum diperbarui. Opsi **Kumulatif** mengikutkan
  poligon periode-periode sebelumnya.
- **Poligon bertampalan di flitch yang sama** (dig block dipasang dua kali): diperingatkan dengan luas tampalan dan perkiraan volume
  yang terhitung dua kali. Penggabungan otomatisnya belum ada.

## 157. Block Model 0.24.54 — As-Mined sesudah diuji data nyata; Solid Vein menggabung poligon bertampalan

**As-Mined**

- **Import boundary dari CSV pick-up OB.** Tombol *Import boundary* kini menerima `.csv` / `.txt` (ID, X, Y, Z, kode): titik berurutan
  menjadi satu poligon. **RL flitch, tanggal dan pit dibaca dari nama file** (mis. `ACT_SO261106OB_272-5_271_Z3.csv` = RL 272,5–271,
  6 Nov 2026, pit Z3) — tidak lagi memakai flitch aktif dan tanggal hari ini. Titik OB sekaligus disimpan sebagai titik atap.
  Bila urutan titik membuat poligon memotong dirinya (file berisi lebih dari satu dig block), panel memperingatkan.
- **Kelas kadar mengikuti block model.** Batas kelas As-Mined diambil dari aturan kolom material di block model `.mdl`
  (tombol *Ambil dari block model* di panel; otomatis bila kelas masih bawaan aplikasi).
- **SG dari kolom block model.** Bila block model `.mdl` punya kolom SG / densitas yang masuk akal, kolom itu dipakai otomatis untuk model yang
  baru dibuka (dulu selalu SG tetap 2,6). **Tonase proyek baru bisa berbeda dari versi sebelumnya karena hal ini** — periksa di
  Block Model › Filter & SG. Proyek lama tidak berubah sampai Anda memilih kolomnya.
- **3D hasil kerja menampilkan solid as-mined**: poligon OB di antara permukaan atap dan lantai yang dipakai hitungan. Kubus
  sub-blok ukuran penuh (yang tampak lebih besar dari volume terhitung) kini pilihan.
- **Zoom ke poligon**: tombol *Zoom ke poligon flitch ini* / *Zoom semua poligon* (3D dan plan 2D); otomatis saat 3D hasil kerja dibuka.
- Material di luar poligon OB tidak dihitung; dilusi hanya yang berada di dalam poligon OB.

**Solid Vein Aktual**

- Poligon yang **bertampalan di flitch yang sama** (dig block dipasang ulang karena lantai belum tuntas) kini **digabung otomatis**
  jadi satu tubuh; atap memakai permukaan tertinggi, sehingga tampalan tidak terhitung dua kali. Bisa dimatikan di *Parameter solid*.

## 158. Block Model 0.24.55 & Drillhole 0.24.58 — tombol "Muat data latihan simulasi" di aplikasi terpasang

- Di aplikasi yang **terpasang**, tombol *Muat data latihan simulasi* (dan Demo yang memakainya) gagal dengan pesan
  "Gagal membaca data latihan SIM_collar.csv (HTTP 404)". Berkas latihannya ada di folder instalasi, tetapi alamat yang diminta
  aplikasi salah bentuk sehingga tidak pernah sampai ke sana. Sudah diperbaiki di kedua aplikasi.
- Tidak ada perubahan lain pada Drillhole.

## 159. Drillhole 0.24.59 — topografi & desain pit tetap tampil sesudah database bor dihapus

- Sesudah **Database Bor › ⋯ › Hapus seluruh database bor**, topografi dan desain pit tidak bisa ditampilkan (jendela 3D kosong,
  sumbu "Easting (+0)"). Sebabnya acuan koordinat proyek ikut hilang bersama lubang bor. Kini acuan dihitung dari topografi dan
  desain pit yang ada. Proyek yang sudah terlanjur kosong pulih begitu dibuka dengan versi ini — tidak perlu import ulang.
- Cara menghapus data bor: **⋯** di node Database Bor → *Hapus seluruh database bor…* atau *Hapus hole tertentu…*; **⋯** di node
  Survey / Assay / Geologi → *Hapus tabel ini…*. Bisa dibatalkan lewat *Batalkan perubahan database terakhir*.

## 160. DB-Ex 0.46.1 — Windows Defender menandai DB-Ex.exe (salah deteksi)

- **Gejala** (DB-Ex 0.46.0): Windows Security → *Threats found* `Trojan:Win32/Bearfoos.A!ml`; pintasan DB-Ex memberi pesan *"The item 'DB-Ex.exe' … has been changed or moved"* karena exe sudah dikarantina.
- **Arti `!ml`**: deteksi heuristik pembelajaran mesin (kemiripan pola), bukan tanda tangan virus yang dikenal. Exe buatan PyInstaller tanpa tanda tangan digital sering kena.
- **Sebelum mengizinkan, periksa**: (1) Windows Security → *See details* → berkas yang ditandai harus `%LOCALAPPDATA%\Programs\DB-Ex\DB-Ex.exe` atau installer DB-Ex yang Anda unduh dari Release; (2) PowerShell `Get-FileHash <installer>` harus sama persis dengan baris installer itu di `SHA256SUMS.txt` Release. Bila keduanya cocok: pilih **Allow on device** → *Start actions* (atau *Protection history* → *Restore*), lalu laporkan sebagai salah deteksi di https://www.microsoft.com/en-us/wdsi/filesubmission. Bila tidak cocok: biarkan dikarantina dan laporkan ke admin.
- **Catatan rilis**: dua build 0.46.1 pertama gagal menerbitkan Release (HTTP 403) karena commit-nya mengubah berkas workflow CI; Release terbit dari commit dokumen sesudahnya (aturan ini dicatat di `CLAUDE.md`). Sejak 0.46.1 CI juga tidak lagi membangun tutorial PDF di setiap push — Release memakai PDF yang ada di repo.
- **Perbaikan 0.46.1**: bootloader PyInstaller dikompilasi sendiri, exe membawa identitas (VERSIONINFO) lengkap, tanpa UPX, dan CI memindai DB-Ex.exe & installer dengan Microsoft Defender sebelum rilis. Ini mengurangi, tetapi tidak menjamin hilangnya, salah deteksi; obat tuntas adalah tanda tangan kode (sertifikat berbayar).

## 160. Drillhole 0.24.60 — popup Slicer dirapikan, menu kembar dibuang, galat saat kursor di atas model

- **Popup Slicer**: tombol *Garis di peta…* menjadi **Sayatan Garis Bebas** dan membuka kotak *Sayatan garis bebas* (tarik garis di
  jendela 3D). *Sayatan 2D* / *Sayatan 3D* menjadi **Tampilan 2D** / **Tampilan 3D** — hanya mengganti cara melihat sayatan yang aktif.
- **Pengaturan sayatan terpusat di popup Slicer.** Baris *Pengaturan lanjutan (panel Sayatan)* dihapus; panel Sayatan tidak lagi
  muncul di Properti.
- **Panel Tampilan & performa** tidak lagi memuat Label hole / Collar / Trajectory / No-data; semuanya diatur dari panel **Layer**.
- **Galat** "Cannot read properties of undefined (reading 'length') … k.pick" saat kursor melewati block model / permukaan: tidak
  lagi muncul (titik itu hanya tidak menampilkan hover).
- **Hover bor**: bila keterangan saat kursor di atas lubang bor tidak muncul, periksa tombol **Hover detail** di Database Bor ›
  panel Data & Filter — hover mati bila tombol itu mati atau *Mode ringan* menyala.

## 161. DB-Ex 0.46.2 — kelompok tulisan; tab Transkrip: daftar tujuan terlihat, jendela muat di layar

- **Kelompok tulisan** (DDR uji lapangan: tabel lubang dan tabel kegiatan berdampingan): teks dibagi per tabel — baris kosong, baris judul kolom baru, atau penanda `# Kelompok n` di teks. Di kisi, setiap kelompok punya **baris biru ▸ K1, ▸ K2 …** berisi dropdown tujuan kolom kelompok itu sendiri (mis. K1 = Meterage / lubang · From, To, Hole ID, Az, Dip; K2 = Rentang jam, Uraian kegiatan). Klik kanan nomor baris → *Mulai KELOMPOK baru di baris ini* / *Gabungkan kelompok ke kelompok di atasnya*. Alat kolom (mis. *Gabungkan baris yang kolom ini kosong ke atas*) hanya bekerja di kelompoknya.
- AI kini diminta menyalin **satu tabel sampai selesai**, lalu baris kosong, lalu tabel berikutnya — tidak lagi menyejajarkan tabel lubang dengan tabel kegiatan (dulu menghasilkan lubang karangan dan satu baris kegiatan raksasa). Menit yang ditulis kecil di atas (`06'30''`) terbaca sebagai 06:30.

- Tab **✎ Transkrip** sebelum ada teks tidak lagi menampilkan *"Pratinjau gagal: 'cols'"*. Area kisi kini memperlihatkan **semua tujuan yang bisa Anda pilih** untuk jenis borang yang terbuka (tabel utama, tabel tambahan seperti Meterage / lubang di DDR, dan isian Kop), alat-alat kisi, dan cara scan kolom satu per satu. Begitu teks ada, tiap kolom teks mendapat dropdown tujuan di baris biru atas kisi.
- Judul kolom umum di teks (*Jam*, *Truck*, *Uraian*, *From* …) hanya diusulkan ke tujuan yang memang ada di jenis borang itu (Ore Spotter: *Jam* → *Start loading*).
- Jendela DB-Ex kini muat di layar 1.280 px logis (mis. 1920 px dengan skala 150 %): tombol kanan (Terapkan, status AI) tidak lagi terpotong.

## 162. Block Model 0.24.56 & Drillhole 0.24.61 — block model .mdl yang gagal dibuka, titik atap, menu As-Mined, Slicer

- **Block model .mdl** yang menampilkan "Tipe atribut "" (…) belum didukung" kini terbaca: daftar atributnya dibaca dengan
  pemeriksaan silang (berlaku di Block Model dan Drillhole). Bila tetap gagal, pesan menyebut atribut terakhir yang terbaca —
  kirim file .mdl itu ke admin.
- **As-Mined**: titik pick-up **atap** (OB) tampil di plan sebagai × ungu bersama titik lantai, dan kursor digit menempel ke
  keduanya. Tombol **Tampil di jendela: Titik lantai / Titik atap** (di atas tombol *Digit poligon*) mematikan salah satu
  lapisan agar digitasi lebih jelas; titik yang disembunyikan tidak ditempeli kursor, hitungan tidak berubah. **Per flitch** membuka panel As-Mined flitch itu (tidak lagi kembali ke *Buat Flitch Aktif*). **Register untuk database**
  (Salin ke Excel, Register CSV, Kirim ke workbook) kini node tersendiri di *Register & Laporan As-Mined*.
- **Slicer (Block Model)**: *Sayatan Garis Bebas* (dulu *Garis di peta…*), *Tampilan 2D / Tampilan 3D* (hanya mengganti cara
  melihat), tanpa *Pengaturan lanjutan*; node *Pengaturan tampilan › Sayatan* dihapus. Galat *k.pick* saat kursor di atas model
  ditambal seperti di Drillhole.
- **Laporan kinerja** (kedua aplikasi) tidak lagi menghitung waktu selama kotak dialog terbuka.

## 163. DB-Ex 0.46.3 — Transkrip untuk Ore Spotter & Ore to Crusher (borang lama & DBX)

- **Borang lama dengan kolom per kelas** (angka Truck / Tonnage atau Ton ditulis di bawah kolom kelas OX-LG, SF-LG, …): di dropdown tujuan kolom tersedia *Kolom kelas OX-LG · Truck*, *Kolom kelas OX-LG · Tonnage* … (Ore Spotter) dan *Kolom kelas OX-LG · Ton* …, *Rehandling · tumpukan 1–3*, *Status · Baru / Lama* (ROM / Crusher). Pilih sekali per kolom; DB-Ex mengisi Kelas + Truck + Tonnage (atau Kelas + Ton + Rehandling + Status) seperti cara baca langsung. Pilihan ini diingat untuk borang berikutnya dengan jumlah kolom yang sama.
- **Ore Spotter**: kolom baru **Block**, **Dig-block ID** dan **Catatan** (borang DBX-ORE). Sel kosong / tanda ulang mengikuti baris atas seperti Pit dan Elevasi.
- Judul kolom borang DBX (*Jam (JJMM)*, *No. Truk*, *Tonase (t)*, *Kelas (kode)*, *Dig-block ID*, …) dikenali otomatis.

## 164. DB-Ex 0.46.4 — Transkrip: pisahkan kolom dengan spasi atau garis pemisah (seperti Excel)

- Teks salinan AI yang **rata kolom dengan spasi** kini terbaca otomatis sebagai **Spasi lebar** (dulu sering terbaca *titik koma* sehingga hanya 2 kolom).
- Pilihan *Pemisah* di tab ✎ Transkrip: **Spasi lebar (≥2 / tab)** · **Setiap spasi** · **Garis pemisah (lebar tetap)…**.
- **Garis pemisah**: jendela penggaris seperti *Text Import* Excel — garis biru diusulkan otomatis; **klik** untuk membuat garis, **seret** untuk memindahkan, **klik ganda** untuk menghapus; pratinjau kolom di bawahnya ikut berubah. Tekan **Pakai garis ini**, lalu petakan kolom dan **Terapkan** seperti biasa. Tombol **┆ Atur garis…** membuka penggaris lagi.
- Baris yang menjorok (kolom pertama kosong) atau diawali `-` tidak lagi menggeser kolom.
- Setelah sel kisi disunting, teks ditulis ulang dengan pemisah `|`.

## 165. Block Model 0.24.57 — Solid Vein Aktual tidak lagi terikat flitch aktif

- Menu **Solid Vein Aktual (trial)** kini punya **flitch kerja sendiri**. Mencentang file titik atap (mis. RL 275,5–274),
  menekan **Buka**, atau mengisi *Tinggi flitch / RL atas / RL bawah* di bagian *Poligon per flitch* langsung membuka plan
  di RL itu dan menampilkan titiknya — tidak perlu kembali ke menu Dig Block atau As-Mined.
- **Selesai import** CSV titik atap, plan flitch file itu (RL dari nama file) langsung terbuka dan titiknya tampil — bisa
  langsung didigit dengan *Digit poligon*.
- Flitch Dig Block / As-Mined **tidak diubah**; tampilan flitch-nya hanya dimatikan selama plan Solid Vein dibuka.
- CSV titik tanpa baris judul yang kolom kodenya berupa teks (mis. `OB`) tidak lagi kehilangan titik pertama.

## 166. Block Model 0.24.58 — As-Mined: kunci tanggal-shift & Report As-Mined per tanggal

- **Report As-Mined per tanggal** (Project Tree › *Register & Laporan As-Mined* › *Report As-Mined per tanggal*, atau tombol di
  bagian *Register untuk database*): pilih **tanggal** dan **shift** (DS / NS / semua) → tonase, BCM, dan kadar tiap unsur per
  poligon, subtotal per shift, total tertimbang tonase. Bisa **Salin ke Excel** atau **CSV**. Jendelanya pop-up: bisa digeser,
  diperkecil, dan ditutup tanpa kehilangan data.
- **Kunci tanggal-shift** (satu tombol per shift): semua poligon hari & shift itu dibekukan. Tombol *Hitung* berikutnya — mis. dua
  minggu kemudian di flitch yang sama — **tidak mengubah** angka poligon terkunci walau sampel, titik lantai/atap, SG, atau
  parameter berubah; rekap flitch memakai angka beku. Poligon terkunci tidak bisa dihapus, dimatikan, atau diedit. **Buka kunci**
  perlu konfirmasi dan dicatat.
- Poligon yang ditambahkan **setelah** dikunci dengan tanggal-shift sama ditandai *ditambah setelah dikunci*; tombol *Kunci yang baru*
  ikut mengunci.
- **Tampalan**: poligon baru yang bertampalan dengan poligon terkunci di flitch yang sama memunculkan peringatan; **OK** mengurangi
  area tampalan dari poligon baru (material itu sudah dilaporkan), **Batal** membiarkannya dan menandainya ⚠ di report.

## 167. Block Model 0.24.59 — atap As-Mined & Solid Vein dari titik pick-up memakai triangulasi (seperti Surpac)

- **Atap As-Mined** pada pilihan *Atap ikut permukaan pick-up*: titik pick-up atap kini **ditriangulasi** (TIN) dan elevasi atap di
  setiap titik = interpolasi linear di dalam segitiga — sama dengan DTM Surpac. Elevasi titik pick-up dipakai persis; tidak ada
  penghalusan yang menurunkan puncak atau menaikkan cekungan. Bagian tepi poligon yang di luar jangkauan titik memakai IDW sebagai cadangan.
- **Solid Vein Aktual**: Z atap tiap sudut poligon juga dari triangulasi titik atap (pilihan *Triangulasi (TIN) titik atap*,
  bawaan; *IDW radius* tetap ada sebagai cara lama). Permukaan gabungan poligon bertampalan juga dari triangulasi.
- Bangun ulang solid / Hitung ulang flitch untuk memakai cara baru (poligon yang tanggal-shift-nya **terkunci** tidak berubah).

## 168. Block Model 0.24.60 & Drillhole 0.24.62 — topografi, pit & lantai dihitung dengan triangulasi; panel pop-up

- **Topografi & desain pit** kini dihitung dari **triangulasi (TIN) yang sama dengan yang tampil di 3D** — interpolasi linear di
  dalam segitiga seperti DTM Surpac. Berlaku untuk: estimasi (blok di atas topografi dilewati), Reporting di bawah topografi / di
  dalam pit, laporan per fase pit & topo-ke-topo, potong block model saat import, orthofoto di atas topografi, dan di Drillhole
  kedalaman dari topografi, sesar, dan kontur. Crest dan toe bench tidak lagi dihaluskan. Di luar jangkauan data (tepi, celah
  kontur lebar) dipakai cara lama sebagai cadangan.
- **Lantai As-Mined** dari pick-up juga triangulasi, sama dengan atap — tebal galian konsisten.
- Angka Reporting / As-Mined lama di dekat tepi bench bisa sedikit bergeser setelah dihitung ulang; poligon yang tanggal-shift-nya
  **terkunci** tidak berubah.
- **Pop-up panel**: tombol **⧉ Pop-up** di judul *Register poligon* (daftar poligon per flitch), *Layout & export* As-Mined, dan
  *Titik atap* Solid Vein memindah bagian itu ke jendela mengambang — geser, perkecil (–), tutup (×, kembali ke panel). Pilihan diingat.

## 169. Block Model 0.24.61 — Report As-Mined harian di panel Register untuk database

- *Report As-Mined per tanggal* kini **di dalam panel *Register untuk database*** (Project Tree › *Register & Laporan As-Mined* ›
  *Register untuk database (report harian & kunci)*), tidak lagi jendela pop-up. Urutannya satu alur: pilih **tanggal & shift** →
  periksa tabel ton & kadar → **Salin ke Excel / Register CSV / Kirim ke workbook** di bawahnya (hanya poligon tanggal-shift
  itu). Begitu laporan itu **keluar** (tersalin, CSV tersimpan, atau terkirim ke workbook), poligonnya **terkunci otomatis** 🔒.
  *Buka kunci* tetap tersedia (dengan konfirmasi). Pilih *Semua tanggal* untuk menyalin seluruh register seperti dulu.
- **Daftar poligon per flitch** (*Register poligon*) tampil sebagai **jendela pop-up** secara bawaan saat node-nya dipilih — tidak
  perlu scroll panjang ketika flitch banyak. Tombol *↩ Panel* mengembalikannya ke panel.

## 170. Block Model 0.24.62 — isian Report As-Mined harian sejajar

- Isian *Tanggal* dan *Shift* kini sejajar dalam satu baris; pilihan *tanggal yang punya poligon* dipindah ke baris sendiri.

## 171. Block Model 0.24.63 — Report As-Mined mingguan / bulanan; Register untuk database jadi jendela pop-up

- Report As-Mined diikat **tanggal & shift poligon**, bukan elevasi flitch: semua flitch pada tanggal itu ikut (kolom RL
  menunjukkan flitch tiap poligon).
- Pilihan **Periode**: *Harian*, *Mingguan* (Senin–Minggu dari tanggal yang dipilih), *Bulanan*, atau *Rentang tanggal*
  (Dari–Sampai). Tabel diberi subtotal per tanggal; Salin ke Excel / Register CSV / Kirim ke workbook memakai periode itu.
- Kunci otomatis hanya terjadi pada **report harian**. Report mingguan / bulanan tidak mengunci, dan memberi tahu berapa poligon
  di periode itu yang belum dilaporkan harian.
- Bagian **Register untuk database** kini tampil sebagai **jendela pop-up** (bisa digeser, diperkecil, ditutup; *↩ Panel* untuk
  mengembalikan ke panel).

## 172. Block Model 0.24.64 & Drillhole 0.24.63 — pop-up tahap 2, Report block model dalam Solid Vein, Data per lubang

**Block Model**
- Tombol **⧉ Pop-up** kini juga ada pada: daftar **dig block** flitch aktif (bagian *Running grade & tonnage*), **hasil Reporting**
  (tab *Hasil*; jendela tetap memperlihatkan hasil terakhir saat Anda pindah ke tab *Constraint* untuk mengubah batas), dan
  **Solid Vein › Poligon per flitch**. Jendela pop-up bisa diubah ukurannya dari pojok kanan bawah.
- **Solid Vein › [periode] › Report block model dalam solid**: grade × tonase **block model resmi** di dalam solid periode itu —
  per cut-off, per pulau, per flitch — dengan *Salin ke Excel* dan *CSV*. Blok dihitung utuh bila titik pusatnya di dalam solid
  (cara Surpac). Periode (cut-off date) mengikuti tanggal periode Solid Vein; pilihan *Kumulatif* ikut. Bangun solid dulu.

**Drillhole**
- **Data per lubang (pop-up)**: tombol di bawah *Hole ID* (panel Data & Filter) atau node *Database Bor › Data per lubang*.
  Jendela berisi collar, survey, assay (dengan rata-rata tertimbang panjang) dan geologi satu lubang; mengikuti pilihan Hole ID dan
  klik lubang di 3D; kolom unsur yang sedang ditampilkan disorot; *Salin assay ke Excel*.
- **Hasil Reporting BM** dan **panel Geostatistik** (statistik & variogram) bisa dilepas jadi jendela lewat tombol **⧉ Pop-up**.

**Kedua aplikasi**: *Laporan kinerja* (Tampilan & performa) tetap mencatat setiap klik — termasuk di dalam jendela pop-up — untuk
dikirim bila ada galat, jeda, atau lag.

## 173. Drillhole 0.24.65 — perbaikan dari uji data nyata Zona 3; area pengaruh & radius pencarian

Pembaruan ini hanya untuk **GC-Ex Drillhole** (Block Model tetap 0.24.64). Isinya hasil uji pemodelan & estimasi vein
dari nol dengan data GC nyata; seluruh 18 temuan diperbaiki.

**Model Estimation**
- Bagian baru **Area pengaruh & radius pencarian** di parameter tiap domain:
  - *Elipsoid pass 1 (m)* mayor / semi / minor — kosong = range variogram. Pass 2–3 = faktor radius × elipsoid ini.
  - *Jarak pengaruh maks sampel (m)* — sampel yang lebih jauh dari pusat blok tidak dipakai, sehingga blok jauh dari bor tetap
    kosong (-99). Berlaku untuk **semua lubang**; isi *Hanya untuk lubang berawalan* (mis. `PDH, SDH`) bila ingin membatasi
    sebagian lubang saja.
  - Parameter domain diubah → domain itu diestimasi ulang otomatis pada run berikutnya.
- Atribut baru **au_id2** (ID² pembanding dari sampel yang sama dengan kriging) ikut di block model, Reporting, dan export.
- Export **.mdl Surpac** kini juga untuk block model yang dibuat dari nol (Kerangka AOI): header disusun baru, ukuran sel & origin
  grid mengikuti kerangka.

**Geomodeller Vein**
- Solid: baris *flag di atas topografi (sudah tertambang)*, *% volume jauh dari kontak bor* (peringatan bila > 25% berjarak > 15 m),
  tebal dibatasi 1,5 × tebal kontak terbesar.
- Vein bercabang: titik *sambung ke induk* dibatasi sebanyak kontak cabang dan menyatu di sumbu induk (cabang tidak menggembung).
- Selubung (halo): jumlah lubang, panjang, dan validasi solid kini terisi; soft boundary hanya memakai sampel vein di zona transisi
  (bawaan 2 m, bisa diubah).
- Import flag CSV menawarkan menghapus flag lama domain yang sama di lubang yang tidak ada di file.
- String HW/FW otomatis lebih halus di zona bor GC rapat.
- Tombol **☑ Status alur pemodelan**: daftar langkah data → domain → string → solid → parameter → block model → estimasi →
  reporting → export beserta statusnya.

**Geostatistik**: tombol **▦ Sayatan di bidang domain** (statistik & variogram memakai seluruh data domain aktif); fitting otomatis
memakai nugget dari variogram downhole dan selalu mayor ≥ semi-mayor; isian *Range downhole / minor* per struktur dipakai bila diubah.

**Impor & tampilan**: CSV yang bukan UTF-8 (mis. karakter ±) dibaca benar dengan peringatan; validasi menyebut Hole ID per butir;
Kerangka AOI punya *Origin grid* (blok sejajar model Surpac); label hole dimatikan otomatis bila > 150 lubang; topografi yang baru
diimpor langsung tampil; nama lengkap node Project Tree muncul saat kursor diarahkan.

## 174. Block Model 0.24.65 — Display 3D As-Mined menampilkan block model di dalam solid as-mined

**Register & Laporan As-Mined › 3D hasil kerja** (*Lihat 3D hasil kerja*) kini menampilkan **blok-blok block model yang
masuk hitungan as-mined**, bukan bentuk solid as-mined-nya:
- Mode *Presisi*: tiap blok dipotong garis poligon OB (XY) serta permukaan atap & lantai di titik tengah blok (Z), persis
  seperti hitungan, sehingga volume blok yang tampak = volume hitungan. Mode *Seperti Surpac*: blok utuh.
- Warna = kelas kadar As-Mined (MO / LG / HG / … / waste) dari kadar hasil as-mined blok itu; legenda menyebut jumlah blok,
  tonase dan kadar tiap kelas; garis tepi blok digambar tipis.
- **Solid as-mined** tetap ada sebagai pilihan *selubung* (kotak centang, mati secara bawaan). *Sub-blok model as-mined*
  (ukuran penuh) dan *Block model GC (konteks)* tidak berubah.
- Bila blok belum muncul, klik **Hitung semua flitch** dulu (blok berasal dari hasil running as-mined).

## 175. Drillhole 0.24.66 — Sampel yang dipakai (seperti Surpac) & domain wireframe langsung siap estimasi

Dari simulasi wireframe BMGC Zona 3 (11 Nov 2026). Log Surpac BMGC menjalankan *BM FILL OK* dengan data source
`constrain = N`: blok dibatasi wireframe, tetapi sampel tidak. GC-Ex selama ini selalu memakai sampel di dalam domain saja
(hard boundary), sehingga kadarnya lebih tinggi walau wireframenya sama.

**Model Estimation › parameter domain › Sampel yang dipakai**
- *Hanya sampel di dalam domain* (bawaan): interval yang di-flag domain itu.
- *Semua sampel database (seperti Surpac)*: semua assay ikut menimbang kadar blok; blok tetap hanya di dalam solid / wireframe.
  Pakai bila hasil harus sebanding dengan block model Surpac yang dibuat dengan data tidak dibatasi constraint.
- Mengubah pilihan = domain itu diestimasi ulang pada run berikutnya.

**Kunci domain ke wireframe** (Project Tree › Import Wireframe Geologi › wireframe › *Kunci domain … ke wireframe ini*):
interval bor di dalam wireframe kini di-flag otomatis bila domain belum punya flag, dan domain langsung siap di Model Estimation.

## 176. Block Model 0.24.66 & Drillhole 0.24.67 — mesh Leapfrog dengan kolom nilai per titik

Mesh Leapfrog (.msh) yang membawa nilai per titik tanpa jumlah komponen di bagian `[index]` (mis. `Thickness_Value Double 1407;`,
dari ekspor wireframe vein beserta ketebalannya) dulu ditolak dengan pesan *indeks segitiga di luar jumlah titik*. Kini kolom
seperti itu dibaca sebagai satu komponen dan dilewati, sehingga Location dan Tri terbaca benar. Berlaku di Import Wireframe
Geologi (Drillhole) dan Wireframe geologi (Block Model).

## 177. Drillhole 0.24.68 — Model Estimation selalu memakai semua sampel, seperti Surpac

Keputusan pemilik (11 Nov 2026): estimasi harus sama persis dengan Surpac. Pilihan *Sampel yang dipakai* (0.24.66) dihapus.
Model Estimation kini SELALU memakai semua sampel database untuk menaksir blok, seperti *BM FILL* Surpac dengan data source
`constrain = N`; blok tetap hanya di dalam solid atau wireframe domain. Lubang eksplorasi digabung ke database GC lewat
Project Tree › Database › **Tambah / perbarui beberapa tabel sekaligus (upsert)**. Validasi dan statistik domain tetap
memakai komposit domain.

## 178. Drillhole 0.24.69 — pilihan Soft / Hard boundary kembali (bawaan: seperti Surpac)

Permintaan pemilik (11 Nov 2026): pilihan hard boundary dan soft boundary jangan dihilangkan. Model Estimation › parameter
domain › **Batas sampel**:
- **Soft boundary** (bawaan): semua sampel database menimbang kadar blok, sama dengan Surpac *BM FILL* data `constrain = N`.
- **Hard boundary**: hanya interval yang di-flag domain itu.
Blok selalu hanya di dalam solid atau wireframe domain. Mengubah pilihan = domain itu diestimasi ulang. Pilihan *zona transisi*
di selubung (halo) tetap seperti sebelumnya.

## 179. Drillhole 0.24.70 — Import Block Model .mdl di layar Import kembali berfungsi

Sejak 0.24.61, memilih file `.mdl` di layar Import (slot *Block model*, sebelum **Mulai**) gagal dengan pesan
*mdlAttrs is not defined*. Pembaca daftar atribut .mdl kini juga dimuat di layar Import. Import .mdl lewat Project Tree /
panel Block Model (sesudah proyek terbuka) tidak terpengaruh.

## 180. Drillhole 0.24.71 — Vein System: banyak vein sekaligus, opsi per vein, solid usang, resolusi adaptif

Diadopsi dari review mesh *Vein System* Leapfrog Zona 2. Algoritma solid RBF GC-Ex tidak berubah: dengan pengaturan bawaan
solid yang terbangun identik dengan versi 0.24.70.

- **Flag dari kolom kode** (Geomodeller Vein › tab *Flag*, di bawah *Usulan otomatis dari kadar*): pilih kolom kode di database
  bor (atribut geologi atau kategori assay, mis. *Orebody*, *Vein*, *Lith*). Setiap kode menjadi satu domain; kolom *Domain
  tujuan* bisa diisi nama yang sama untuk menggabungkan beberapa kode (mis. `2001V` dan `2001_V`). Kode kosong atau `-` tidak
  dicentang. *Flag lama domain tujuan*: **Diganti seluruhnya** (kolom = interpretasi lengkap) atau **Dipertahankan**. Bisa diurungkan.
- **Opsi semua vein (tabel) & prioritas** (tab *Solid*): satu baris per domain untuk snap ke bor (*Tepat*) / kehalusan, pinch-out
  di bor kosong, pinch-out searah dip, tebal minimum, radius strike, ujung atas, resolusi, dan resolusi adaptif. Tombol ▲▼ mengubah
  **prioritas**: bila solid bertumpang, blok diklaim domain yang lebih atas saat Model Estimation.
- **Vein system (gabungan semua solid)** (tab *Solid*): jumlah volume, **volume gabungan** (tumpang tindih dihitung sekali) dan
  ekspor **Gabungan OBJ / DXF / STR+DTM** — semua solid dalam satu berkas, tiap solid tetap tertutup.
- **Solid usang**: bila *Jalankan ulang otomatis* dimatikan, domain yang masukannya berubah (data bor / flag / string, atau parameter)
  ditandai **usang** di panel Solid dan di Project Tree; tombol / menu ⋯ **Bangun ulang solid usang** membangun semuanya sekaligus.
- **Resolusi adaptif** (Parameter domain aktif › RBF & mesh, atau tabel opsi): segitiga rapat di dekat data dan menjarang sampai
  *Jarang maks.* × resolusi. Pada data latihan QV_Lensa2: verteks berkurang ±34 %, volume bergeser ±0,7 %. Bawaan: mati.
- Data latihan: `SIM_geologi.csv` dan `SIM_kecil_geologi.csv` kini punya kolom **Vein** (QV_Lensa1–4, QV_Splay_HW) untuk melatih
  *Flag dari kolom kode*. Kolom lama tidak berubah.

## 181. Drillhole 0.24.72 — Ore Geometry Studio: semua menu Ore Geometry dalam satu jendela

Node **Ore Geometry** › tombol **Buka Ore Geometry Studio**. Panel samping kini hanya ringkasan; semua menu ada di jendela lebar
(bisa digeser, diperkecil, ditutup). Studio adalah **referensi geologist**: hasilnya tidak menulis flag Geomodeller dan tidak dipakai
Model Estimation. Berlaku untuk kedua jalur proyek.

1. **Data & domain** — pilih wireframe domain (solid GC-Ex dari Geological Modelling dan / atau wireframe impor Surpac / Leapfrog),
   atur prioritas ▲▼, lalu **Hitung flag domain & intercept**. Interval assay yang titik tengahnya di dalam wireframe di-flag otomatis;
   interval sedomain berurutan di satu lubang digabung menjadi satu intercept. *Pemeriksaan data* hanya menampilkan temuan
   (nilai negatif, banyak nol, nilai ekstrem yang mencurigakan satuan); tidak ada data yang diubah.
2. **Geometri & tebal** — strike, dip, panjang, tinggi, RL dan tebal sebenarnya (median, P10–P90) per domain; pilih bidang acuan.
3. **Kadar & multi-elemen** — statistik unsur di vein vs luar vein, kontras, korelasi Spearman, kadar per domain, geologi di vein.
4. **Long section** — sampai 6 panel (GT dan unsur), proyeksi ke bidang acuan.
5. **Envelope RBF & 3D** — RBF linear di bidang tiap domain; garis envelope GT, arsir bagian jauh dari intercept, volume / tonase
   (SG bisa diubah) dan tampilan 3D. Gambaran geometri, bukan estimasi sumber daya.
6. **Zonasi vertikal** — median per pita RL di dalam vein vs halo.
7. **Profil per domain** — format sama dengan Geostatistik › Profil (unsur, rasio, jumlah, % kode geologi).
8. **Penampang** — sayatan Studio sendiri (tidak menggerakkan Slicer): **Usulkan sayatan**, tambah, Maju / Mundur, ubah azimuth dan
   lebar jendela, atau **Gambar di peta** (klik dua titik). Panel unsur + kolom geologi, potongan wireframe, tabel sampel tertinggi dan
   sampel ≥ 0,5 di luar wireframe.

Alat lama (Intercept & GT, Long section GT, Ore shoot, Grade shell) dan pintasan Geostatistik › Profil / Slicer ada di bagian *Alat lain*.
Setiap grafik punya tombol **PNG**, setiap tabel **CSV**. Tahap 2 (berikutnya): struktur, garis interpretasi, pertemuan vein, target
bor, laporan PDF.

## 182. Drillhole 0.24.73 — Jalur proyek: Mulai dari nol / Lanjutkan dari Surpac / Leapfrog

Setiap proyek GC-Ex Drill Hole kini berada di salah satu dari dua **jalur**, dipilih di halaman pembuka (kartu *Jalur proyek*).
Penentunya: apakah proyek memakai **model dari software lain** (wireframe / domain, block model `.mdl` / CSV, parameter estimasi).
Data mentah (collar, survey, assay, geologi, topografi) tidak dihitung. Tidak ada algoritma yang berubah.

- **Mulai dari nol**: domain, solid, kerangka blok (AOI) dan parameter dibuat di GC-Ex. Fitur adaptasi tidak tampil: node
  *Import Wireframe Geologi*, *Import block model dari file*, Serap / Eksak. Pintasan "Import BM…" membuka *Buat kerangka blok (AOI)*.
- **Lanjutkan dari Surpac / Leapfrog**: centang acuan yang Anda punya. Tahap beracuan bisa *Pakai acuan* atau *Buat baru*; tahap tanpa
  acuan dibuat di GC-Ex. Tidak ada alat yang disembunyikan. Contoh: wireframe Leapfrog + estimasi dari awal = Lanjutkan, acuan *Wireframe* saja.
- **Project Tree › Proyek › Jalur**: label jalur, acuan, dialog *detail & jejak*. *Jadikan jalur Lanjutan…* satu arah dan tercatat.
- **Otomasi**: Autorun Wireframe tidak membangun ulang domain *acuan eksak*; menyimpan parameter Geostatistik ke domain yang parameternya
  acuan meminta konfirmasi. Autorun Estimasi dari Nol, auto-fit variogram dan KNA berjalan sama di kedua jalur (hanya mengisi domain tanpa parameter).
  Kerangka blok (AOI) yang dibuat oleh autorun tidak lagi memunculkan jendela "langkah berikutnya" di tengah proses; hasilnya tercatat di laporan autorun.
- **Proyek lama** (sebelum 0.24.73): jalur ditebak dari isi proyek dan ditandai *perlu konfirmasi*; sebelum dikonfirmasi tidak ada menu yang
  disembunyikan. **Muat data latihan** selalu masuk jalur Lanjutkan (wireframe Leapfrog + block model GC).
- Dokumen: Tutorial Modelling & Estimasi (bab *Jalur proyek: mulai dari nol atau lanjutkan*), Tutorial Update bab 15, Petunjuk Teknis 8.4.

## 183. Drillhole 0.24.74 — Ore Geometry Studio tahap 2: struktur, garis interpretasi, pertemuan vein, target, laporan PDF

Tutorial lengkap bergambar: **docs/tutorial-gcex/GCEx_Tutorial_Ore_Geometry_Studio.pdf** (juga di `_1_Dokumen.zip` › Tutorial).

- **9 Struktur bawah permukaan** — long section dengan garis otomatis dari data (collar tertinggi, dasar lubang GC, puncak ore, zona
  belum teruji GC) dan tabel per segmen strike. Lubang eksplorasi dikenali dari pola nama (regex, bisa diubah).
- **Garis interpretasi** (dibuat geologist) di long section struktur, penampang dan grafik posisi tegak lurus: penanda posisi, polyline,
  pita / zona, poligon, teks. Beri nama (masuk legenda), warna, gaya, keterangan. Usulan otomatis tampil abu-abu bertanda *usulan* sampai
  ditekan **Terima**. Ekspor **CSV E/N/RL** atau **string Surpac .str**.
- **10 Struktur paralel & tekukan**, **11 Pertemuan vein** (zona ≥ 2 vein vs 1 vein, uji per sel lokasi), **12 Target bor**
  (usulan + klik; E/N/RL, collar, azimuth, panjang), **13 Di luar wireframe** (sampel ≥ cut-off per kategori).
- **14 Laporan PDF** — template deck (navy / emas, 13,333 × 7,5 in). Tulis judul kalimat & catatan per slide, lalu **Buat laporan & cetak
  ke PDF** (dialog cetak → *Simpan sebagai PDF* / *Microsoft Print to PDF*, margin 0, centang *Grafik latar belakang*) atau simpan HTML.

## 184. Drillhole 0.24.75 — Autorun Estimasi dari Nol: sayatan di bidang tiap domain

Variogram di Geostatistik dihitung dari komposit di dalam **sayatan aktif**. Autorun Estimasi dari Nol dulu memakai sayatan apa pun
yang sedang terpasang; pada data nyata sayatan horizontal bawaan bisa hanya memuat sebagian kecil komposit sebuah vein (Zona 3: 13 dari
489), sehingga domain dilewati karena di bawah ambang komposit.

- Sekarang tiap domain dipasangi **sayatan di bidang domain** sebelum variogram dihitung — sama dengan tombol *Sayatan di bidang domain*
  di Geostatistik (strike & dip dari kontak bor, tebal = sebaran kontak). Semua komposit domain ikut.
- Laporan autorun menyebut sayatan yang dipakai per domain. Sayatan Anda dikembalikan sesudah autorun selesai.
- Pilihan **Variogram dari sayatan di bidang tiap domain** di dialog Autorun Estimasi dari Nol (bawaan nyala). Dimatikan = perilaku lama.

## 185. Drillhole 0.24.76 — Data latihan untuk jalur Mulai dari nol

Halaman import kini punya dua tombol data latihan:

- **Data latihan — Lanjutkan**: seperti sebelumnya (bor, topografi, block model GC, wireframe Leapfrog). Angka sama dengan buku tutorial.
- **Data latihan — Mulai dari nol**: data bor dan topografi simulasi yang sama, tanpa block model GC dan wireframe Leapfrog. Buat domain dengan
  *Flag dari kolom kode* (kolom *Vein*), lalu *Autorun Wireframe* dan *Autorun Estimasi dari Nol*.

Jalur proyek mengikuti tombol yang ditekan, bukan kartu jalur. Tombol Demo tetap memakai jalur Lanjutkan.

## 186. Drillhole 0.24.77 — Ore Geometry Studio: 15 · Peta level

Ore Geometry Studio › **15 · Peta level** mengubah irisan horizontal di satu RL menjadi peta: kelas kadar (Anomali / Di dalam domain),
arsir alterasi, garis tengah wireframe domain, lubang yang menembus RL, kontur, garis interpretasi, dengan judul, panah utara, skala dan
legenda di dalam peta. Kontur: **Impor string kontur (.str / .dxf)**; tanpa string dipakai kontur dari collar (bukan topografi asli).
Label domain dan Hole ID bisa digeser dengan mouse. Isi *RL peta yang dicetak* (mis. 280; 300; 320) untuk slide peta di Laporan PDF.
Panduan bergambar: Tutorial Ore Geometry Studio bab 10.

## 187. Drillhole 0.24.78 — Peta level: posisi bebas, kadar halus, sakelar lapisan

Di Ore Geometry Studio › 15 · Peta level: tarik **judul**, **panah utara & skala** (tarik huruf N) dan **legenda** ke tempat kosong; tombol *posisi otomatis* mengembalikannya. Warna kadar kini halus (tidak kotak-kotak). Setiap lapisan bisa dinyalakan / dimatikan dengan sakelar **Lapisan** di atas peta.

## 188. Drillhole 0.24.79 — Parameter estimasi dari log Surpac

Untuk proyek jalur **Lanjutkan** dengan acuan *Parameter estimasi*: Model Estimation › **⋯ › Isi parameter dari log Surpac…**
(atau tombol **Isi dari log Surpac…** di panel parameter domain).

- Pilih berkas log Surpac. GC-Ex menampilkan semua run *BM FILL* (terbaru di atas) dengan variogram, orientasi (bearing / plunge / dip),
  elipsoid pencarian, jumlah sampel dan constraint; run kriging Au terakhir terpilih otomatis.
- **Memilih run**: run yang benar adalah run yang menghasilkan nilai di block model yang diserahkan — atributnya sama dengan kolom kadar
  block model, biasanya run terakhir atribut itu. Tombol **Uji kecocokan dengan block model acuan** mengestimasi domain terpilih dengan tiap
  set parameter berbeda dan membandingkannya dengan kolom kadar block model Surpac yang aktif; run paling cocok ditandai ★ dan dipilih.
  Run uji tidak masuk riwayat Model Estimation dan parameter domain tidak berubah sampai Anda menekan **Salin parameter ke domain terpilih**.
- Orientasi Surpac ZXY LRL diterjemahkan ke sumbu GC-Ex; sumber sampel `constrain = N` = soft boundary (semua sampel), `Y` = hard.
  Log tidak mencatat diskretisasi blok: atur di dialog (bawaan 1×1×1).
- **Tanpa log**: parameter tidak tersimpan di .mdl. Buat dari data bor dengan *Autorun Estimasi dari Nol* (hilangkan centang acuan
  *Parameter estimasi* di Proyek › Jalur), lalu bandingkan dengan block model pendahulu pada blok yang sama.

## 189. Block Model 0.24.67 + Drillhole 0.24.80 — Block model .mdl dengan deskripsi atribut

Block model Surpac yang atributnya diberi *Description* (mis. `sg3` berdeskripsi "density") kini terbaca di import
kedua aplikasi. Sebelumnya muncul galat *Atribut ke-… sesudah "…" tidak terbaca (tipe …)*. Tidak ada langkah tambahan:
pilih ulang berkas .mdl di layar import. Deskripsi atribut ikut tersimpan apa adanya saat block model diekspor kembali ke .mdl.

## 190. Block Model 0.24.68 + Drillhole 0.24.81 — Reporting BM: cara Surpac sebagai bawaan

(DB-Ex 0.46.5 hanya ikut naik karena mesin laporan Python di backend bersama; tidak ada perubahan yang terlihat di DB-Ex.)

- **Hanya di bawah topografi.** Blok di luar jangkauan topografi, desain pit atau batas DTM tidak lagi dilaporkan, sama seperti
  Surpac. Bila block model lebih luas dari pick-up topografi, tonase *sisa* bisa turun dibanding versi sebelumnya — angka baru
  inilah yang setara dengan report Surpac.
- **Blok di batas permukaan** (Reporting BM › Constraint): *Cara Surpac — titik pusat blok* (bawaan) atau *Cara GC-Ex — proporsi
  volume blok* (kolom 2×2 sampai 8×8, bawaan 4×4). Tab **Metode tonase** menampilkan keduanya berdampingan.
- Block Model: centang *timbang dengan proporsi sub-blok (`sb_frac`)* kini **mati** secara bawaan (cara Surpac).

## 191. Block Model 0.24.69 + Drillhole 0.24.82 — Topografi & desain pit ber-hillshade

Permukaan topografi, desain pit dan DTM kini digambar dengan **hillshade** (cahaya dari barat laut, 45°): lereng, jenjang pit dan
punggungan terlihat jelas dari sudut pandang mana pun. Atur di panel **Overlay › Bayangan (shading) topo & pit**: *Hillshade jelas*
(bawaan), *Hillshade lembut*, atau *Lampu 3D Plotly (lama)*. Warna bawaan topo hijau zaitun dan pit biru keabuan; keduanya tetap bisa
diganti di **Topo / pit**.
