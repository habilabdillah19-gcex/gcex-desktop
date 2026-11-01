# Aturan repo GC-Ex (untuk setiap sesi Claude / kontributor)

## Rilis = jejak resmi setiap pembaruan (permintaan pemilik, wajib)
- SETIAP pembaruan yang di-push ke `main` — installer/kode aplikasi, kode sumber, tutorial, data dummy, panduan teknis,
  tentang / lisensi — harus muncul di **GitHub Release**. CI (`.github/workflows/build-windows.yml`) menerbitkan
  Release `v<versi package.json>` otomatis lewat `tools/rilis/kemas_rilis.py`.
- Karena itu:
  - **Naikkan versi** aplikasi yang berubah (patch / minor) pada setiap push yang mengubah isi, termasuk perubahan dokumen /
    data latihan saja. Versi per aplikasi: Block Model = `package.json`; Drillhole = `builder-dh.json` `extraMetadata.version`;
    DB-Ex = `builder-core.json` `extraMetadata.version` (bila kosong ikut package.json). **Tag** Release memakai versi
    tertinggi, tetapi isinya memuat installer KETIGA aplikasi pada versinya masing-masing (CI membangun ketiganya tiap run;
    versi tiap aplikasi disebut di catatan rilis). Tambahkan baris versi di `README.md` + bagian di `docs/PANDUAN_INSTALL.md`.
  - **Jangan memakai `[skip ci]`** di pesan commit (commit itu tidak akan masuk Release).
  - Sebelum push: `git fetch` + `git pull --rebase` (beberapa sesi push paralel); bila versi sudah dipakai sesi lain, naikkan lagi.
- Isi Release: 3 installer terpisah (GC-Ex Block Model, GC-Ex Drillhole, DB-Ex — tidak dibundel, masing-masing pada versinya sendiri), `_1_Dokumen.zip`,
  `_2_Data-Latihan.zip`, `_3_Lisensi-dan-Tentang.zip`, `_CATATAN_RILIS.md` (commit sejak rilis sebelumnya), `SHA256SUMS.txt`,
  plus kode sumber otomatis dari tag. File baru yang perlu ikut rilis didaftarkan di `tools/rilis/kemas_rilis.py`.
- Lokasi: tutorial & data simulasi GC-Ex di `docs/tutorial-gcex/`, DB-Ex di `docs/tutorial-core/`, panduan di `docs/`,
  lisensi & syarat di `legal/`, alat lisensi admin di `tools/lisensi/`.

## Lain-lain
- Aplikasi offline: tanpa auto-update / pemeriksaan pembaruan online (`publish: null`); pembaruan didistribusikan admin dari Release.
- Kunci privat lisensi TIDAK PERNAH masuk repo / Release.
- Data contoh harus fiktif (tanpa nama perusahaan, Hole ID, koordinat proyek nyata).
