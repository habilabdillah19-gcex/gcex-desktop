# Keputusan GC-Ex yang berlaku sekarang

Dokumen ini hanya memuat **keputusan yang masih berlaku**. Kebijakan yang sudah ditimpa
kebijakan baru tidak dicatat di sini — jejak lengkapnya ada di `README.md` (baris 5a…) dan
`docs/PANDUAN_INSTALL.md` (bagian bernomor).

Tanggal: 7 November 2026.

## 0. Keadaan terkini

| Aplikasi | Versi | Sumber versi |
|---|---|---|
| GC-Ex Block Model | 0.24.36 | `package.json` |
| GC-Ex Drillhole | 0.24.38 | `builder-dh.json` → `extraMetadata.version` |
| DB-Ex | 0.42.8 | `builder-core.json` → `extraMetadata.version` |

Commit terakhir: `25e44b0`. Release aktif: `v0.42.8`, memuat installer ketiga aplikasi pada
versinya masing-masing.

## 1. Cara kerja (berlaku untuk setiap sesi)

- Pemilik adalah **geolog, bukan programmer**. Jawab dalam **Bahasa Indonesia**, dan jelaskan
  sebab-akibatnya, bukan nama fungsinya saja.
- **Fokus ke versi HTML.** Pekerjaan Qt ditunda sampai pemilik menyatakan sebaliknya.
- **DB-Ex tidak disentuh** dari sesi ini — sumbernya tidak ada di pohon kerja ini dan sesi lain
  memegangnya.
- Perubahan dikirim **bertahap / patch**, bukan menulis ulang berkas besar.

## 2. Aturan rilis & versi

- Setiap push ke `main` harus muncul di GitHub Release; CI menerbitkannya otomatis.
- **Hanya naikkan versi aplikasi yang isi installernya benar-benar berubah.** Push yang hanya
  mengubah dokumen, data latihan, atau CI **tidak** menaikkan versi apa pun.
- Urutannya **wajib**: naikkan `package.json` **lebih dulu**, baru jalankan `python web-src/build.py`.
  Membangun sebelum menaikkan versi membuat aplikasi mencap dirinya versi lama, dan CI menolaknya
  di penjaga cap versi. (Ini pernah terjadi pada 0.24.33.)
- Sebelum push: `git fetch` + `git pull --rebase` (ada sesi paralel), lalu
  `python tools/rilis/kemas_rilis.py --cek` dan `python tools/rilis/cek_cap_versi.py`.
- **Jangan pernah** memakai `[skip ci]`.
- Kunci privat lisensi tidak pernah masuk repo/Release. Data contoh harus fiktif.
- Bila beberapa versi menumpuk: **batalkan build lama, langsung terbitkan versi tertinggi**
  (permintaan pemilik, 7 Nov 2026).

## 3. Kontrak UI: satu node, satu fungsi

Ini aturan induk yang melahirkan sebagian besar perbaikan UI sesi ini.

- Isi panel **Properti** selalu milik node yang sedang dipilih. Judul, sorotan di Project Tree,
  dan isi panel berasal dari satu sumber.
- Tiap node menyatakan apa yang muncul: panel sungguhan (`tab` + `sub` + `foc`), kartu aksi
  (`card`/`go`, tanpa `tab`), atau kartu folder (`card:{kids:1}`).
- Perintah yang **memindahkan tab sendiri** (mis. `lyApply`, `lyFlOff`) wajib memilih node pemilik
  panel hasilnya. Melepas fokus tanpa memindah node membuat panel menampilkan beberapa fungsi
  sekaligus — justru kebalikan aturan ini.
- Satu fitur hanya boleh ada di **satu** node. Fitur grade & tonnage hanya di panelnya sendiri;
  pembuatan dig block tidak muncul di panel flitch; ekspor hanya di satu node.

## 4. Ekspor

- **Setiap ekspor, berkas apa pun dan bentuk apa pun, harus memunculkan jendela simpan** yang
  menanyakan lokasi dan nama berkas. Tidak ada unduhan diam-diam.
- Pintunya satu: `gxJenis()` + `gxSimpan()`. Semua jalur unduh (`dgDl`, `gsDl`, `gxDl`, CSV, PNG,
  `.html`, `.dh3d`, dll.) menyalurkan ke situ.
- Berlaku di **Block Model dan Drill Hole**. Belum diterapkan di DB-Ex.
- Ekspor berlaku pada **flitch yang sedang aktif**.

## 5. Flitch: apa yang dipotong, apa yang dibiarkan utuh

- **Blok model di 3D dipotong tepat di RL flitch aktif** (atas dan bawah), bukan sekadar dipilih
  utuh. Hasilnya tampil seperti pulau-pulau berbatas RL, mirip Surpac.
- **Permukaan referensi (topografi, desain pit, DTM) dibiarkan utuh**, tidak ikut dipotong
  — keputusan pemilik, 7 Nov 2026.
- **Uji pilih string hanya mengenai flitch aktif.** Ore line dari elevasi lain tetap ditampilkan
  sebagai rujukan arah bijih, tetapi tidak boleh terklik. Saringannya sama persis dengan
  `lyPolys()`.
- Saat menguji potongan flitch, **tinggi flitch harus lebih kecil dari tinggi blok** — kalau sama,
  "pilih utuh" dan "potong di flitch" memberi angka identik dan ujinya tidak membuktikan apa pun.

## 6. As-Mined

- **Titik lantai dan titik atap disimpan terpisah** (`D.pts` dan `D.ptsR`) dan keduanya dipakai:
  lantai untuk interpolasi IDW per poligon, atap untuk batas atas volume as-mined.
- Keduanya **dinamai eksplisit** di panel ("Titik pick-up LANTAI (floor)…" dan "Titik pick-up
  ATAP…"), dan masing-masing menunjuk ke pasangannya. Satu kotak bernama spesifik di sebelah
  kotak bernama umum membuat yang umum terbaca sebagai duplikat.
- **Setelan halus disembunyikan** di balik baris *Setelan lanjutan* (pita, buffer, pola kode,
  ringkasan elevasi). Kendali yang langsung terlihat: 3, bukan 12.
- Luas yang atapnya menembus lantai **wajib dilaporkan**, bukan dijepit diam-diam — itu underdig
  nyata atau titik dari hari/flitch yang salah.

## 7. Pembacaan berkas koordinat

- Untuk CSV **tanpa baris judul**, kolom **tidak boleh ditebak dari urutannya**. Kolom koordinat
  dikenali dari **besaran nilainya**: dua kolom berdampingan yang median mutlaknya ≥ 1.000 adalah
  Easting & Northing, di posisi mana pun; Z dan Kode mengikut sesudahnya; kolom sebelumnya adalah
  ID.
- Alasannya: berkas survey pick-up lazim berbentuk `ID,Easting,Northing,RL,Kode` dengan ID berupa
  angka. Aturan lama menggeser seluruh kolom satu langkah sehingga Northing terbaca sebagai Z,
  tidak satu titik pun jatuh di pita elevasi, dan atap/lantai tidak pernah terbentuk — tanpa satu
  pun pesan galat, karena setiap angkanya sah sebagai angka.
- Aturan lama tetap dipakai sebagai cadangan untuk koordinat grid lokal yang nilainya kecil.

## 8. Keringanan untuk laptop HP 14s

- Block Model: `bxBesarAuto()` menyalakan "Update saat slider dilepas" otomatis pada ≥ 250.000 blok;
  `bxLim3D()` membatasi blok 3D (hemat 60k / seimbang 150k / penuh 400k).
- Drill Hole: `dhBesarAuto()` dengan ambang ≥ 20.000 sampel, ≥ 200 lubang, atau ≥ 250.000 blok,
  dipanggil dari `SA.boot`.
- Lag diukur dari **jeda `requestAnimationFrame` > 50 ms selama drag tetikus sungguhan** pada
  `#pos`. Jangan mengukur `wait_for_timeout` sendiri — itu mengukur tidurnya harness, bukan lag.

## 9. Cara menguji (wajib, hasil pelajaran mahal sesi ini)

1. **Selalu A/B terhadap build lama.** `git show HEAD:app/index.html` sebagai pembanding. Uji yang
   lulus di build lama **dan** build baru tidak membuktikan apa pun.
2. **Ukur akibat, bukan keberadaan.** "Elemen dialog ada di DOM" lolos padahal dialognya berhenti
   satu piksel di bawah layar. Ukur posisi kotaknya terhadap jendela, teks yang benar-benar
   tergambar, jumlah kendali yang terlihat.
3. **Periksa parameter ujinya sendiri.** Dua poligon yang berbagi tepi persis sama membuat jarak
   klik nol ke keduanya — build benar dan build salah memberi hasil sama.
4. **Pastikan kasusnya tereproduksi** sebelum menyatakan lulus. `stringLuarFlitch: 0` artinya tidak
   ada yang diuji.
5. **Port acak** di setiap harness (`random.randint(9100, 9899)`). Port tetap pernah membuat
   `http.server` lama menyajikan berkas basi dan menghasilkan kesimpulan yang salah total.
6. **Periksa keseimbangan kurung per hunk sebelum build.** `node --check` per berkas bisa lolos
   padahal `vsrc` yang digabung rusak — aplikasi memuat tanpa galat tetapi 0 blok.
7. **Jalankan boot check** (aplikasi hidup + data termuat) sebelum menyatakan apa pun selesai.
8. Harness disimpan di `tools/uji/`.

## 10. Yang belum selesai

- Pola jendela simpan belum diterapkan ke **DB-Ex** (sengaja — sesi lain memegang sumbernya).
- Pekerjaan **Qt ditunda**.
- Laporan poligon bertumpang-tindih saat proyek dibuka kembali **belum tuntas**: jalur
  `SA.collectWork` → `SA.applyWork` terbukti tidak menggandakan (68 → 68 string, nol kembar), dan
  geometrinya cocok dengan fitur **string ganda (sulfida)** yang menyala secara bawaan
  (offset 0,5 m ke dalam, kolom `sxs` > 0,8). Bila mematikan centang *Buat string ganda untuk ore
  sulfida* **tidak** menghilangkan garis keduanya, berarti ada penggandaan nyata di jalur buka
  proyek dari folder (`FP.openFolder`) yang belum tereproduksi dengan data latihan.
