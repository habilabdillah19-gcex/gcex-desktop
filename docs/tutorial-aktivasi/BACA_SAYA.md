# Sumber tutorial aktivasi

`docs/GC-Ex_Tutorial_Aktivasi_Lisensi.pdf` dibuat dari `aktivasi.html` di folder ini.

- `shots.js` mengambil tangkapan layar jendela Aktivasi (dengan `window.gcexLic` tiruan) dan alat Pembuat Lisensi (dengan kunci Ed25519 demo sementara, bukan kunci penerbit).
- `pdf.js` mencetak `aktivasi.html` ke PDF A4 (Playwright/Chromium).
- Semua nama, ID Komputer dan kunci di gambar adalah contoh fiktif.

Sebelum `shots.js` dijalankan, siapkan di folder ini (jangan di-commit):
`demo_priv.json` (kunci Ed25519 demo, `{"jwk":{...}}`), `gen_demo.html` (salinan alat pembuat lisensi dengan `EXPECT_X` diganti `x` kunci demo) dan `gen_real.html` (salinan alat asli).
