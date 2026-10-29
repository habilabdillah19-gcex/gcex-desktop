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
