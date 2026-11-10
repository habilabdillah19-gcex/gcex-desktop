# Aturan repo GC-Ex (untuk setiap sesi Claude / kontributor)

## Rilis = jejak resmi setiap pembaruan (permintaan pemilik, wajib)
- SETIAP pembaruan yang di-push ke `main` — installer/kode aplikasi, kode sumber, tutorial, data dummy, panduan teknis,
  tentang / lisensi — harus muncul di **GitHub Release**. CI (`.github/workflows/build-windows.yml`) menerbitkan
  Release `v<versi package.json>` otomatis lewat `tools/rilis/kemas_rilis.py`.
- Karena itu:
  - **Naikkan versi** aplikasi yang **isi installernya** berubah (patch / minor) pada setiap push.
    Push yang hanya mengubah dokumen, data latihan, atau CI **TIDAK** menaikkan versi aplikasi mana pun: installernya
    identik, dan Release tetap terbit ulang pada tag yang sama sehingga ZIP dokumen / data latihannya ikut diperbarui.
    (Dulu aturan ini berbunyi "termasuk perubahan dokumen / data latihan saja"; itu membuat versi Block Model naik tujuh
    kali tanpa satu pun perubahan pada aplikasinya — lihat README 0.24.23.) Versi per aplikasi: Block Model = `package.json`; Drillhole = `builder-dh.json` `extraMetadata.version`;
    DB-Ex = `builder-core.json` `extraMetadata.version` (bila kosong ikut package.json). **Tag** Release memakai versi
    tertinggi, tetapi isinya memuat installer KETIGA aplikasi pada versinya masing-masing (CI membangun ketiganya tiap run;
    versi tiap aplikasi disebut di catatan rilis). Tambahkan baris versi di `README.md` + bagian di `docs/PANDUAN_INSTALL.md`.
  - **Jangan memakai `[skip ci]`** di pesan commit (commit itu tidak akan masuk Release).
  - **`[lompat]`** di pesan commit membatalkan build yang sedang berjalan dan langsung membangun commit itu (pemilik,
    10 Nov 2026: revisi di tengah proses langsung melompat ke versi baru). Pakai bila pemilik meminta revisi sementara build
    push sesi ini masih berjalan; push biasa TIDAK memakainya (sesi paralel jangan saling membatalkan build).
  - Sebelum push: `git fetch` + `git pull --rebase` (beberapa sesi push paralel); bila versi sudah dipakai sesi lain, naikkan lagi.
  - **Hanya naikkan versi aplikasi yang berkasnya benar-benar berubah** (Block Model tidak ikut naik karena perubahan Drill Hole saja).
    Periksa dengan `python tools/rilis/kemas_rilis.py --cek` sebelum push; CI menolak commit yang melanggar.
- **CI tidak membangun tutorial PDF di setiap push** (pemilik, 10 Nov 2026: "tidak usah membuat pdf"; langkah bergambar ±16 menit).
  Release memakai PDF yang ada di repo: sesi yang mengubah tutorial membangunnya di kontainer lalu meng-commit PDF-nya.
  Minta CI membangun ulang hanya bila perlu: tulis `[pdf]` di pesan commit, atau jalankan workflow secara manual.
- **Commit yang mengubah `.github/workflows/*` tidak bisa menjadi titik tag Release BARU**: GITHUB_TOKEN ditolak
  membuat tag / Release di commit itu (HTTP 403 "Resource not accessible by integration"; DB-Ex 0.46.1, 10 Nov 2026 —
  dua run gagal di langkah *Kemas & terbitkan*). Memperbarui Release yang tag-nya sudah ada tetap jalan. Jadi bila
  versi naik bersamaan dengan perubahan workflow, susulkan satu commit lain (mis. dokumen) yang tidak menyentuh workflow.
- Isi Release: 3 installer terpisah (GC-Ex Block Model, GC-Ex Drillhole, DB-Ex — tidak dibundel, masing-masing pada versinya sendiri) + `DB-Ex-Qt-Setup` (DB-Ex versi Qt, versi = builder-core.json; satu-satunya yang memuat Singkapan / Borang / QAQC), `_1_Dokumen.zip`,
  `_2_Data-Latihan.zip`, `_3_Lisensi-dan-Tentang.zip`, `_CATATAN_RILIS.md` (commit sejak rilis sebelumnya), `SHA256SUMS.txt`,
  plus kode sumber otomatis dari tag. File baru yang perlu ikut rilis didaftarkan di `tools/rilis/kemas_rilis.py`.
- Lokasi: tutorial & data simulasi GC-Ex di `docs/tutorial-gcex/`, DB-Ex di `docs/tutorial-core/`, panduan di `docs/`,
  lisensi & syarat di `legal/`, alat lisensi admin di `tools/lisensi/`.

## Lain-lain
- Aplikasi offline: tanpa auto-update / pemeriksaan pembaruan online (`publish: null`); pembaruan didistribusikan admin dari Release.
- Kunci privat lisensi TIDAK PERNAH masuk repo / Release.
- Data contoh harus fiktif (tanpa nama perusahaan, Hole ID, koordinat proyek nyata).
