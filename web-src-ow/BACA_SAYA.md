# Ore Works — sumber

Ore Works (dahulu bernama kerja *Ore Studio*) adalah satu berkas HTML offline: `app-ow/index.html`
(three.js r128 tertanam, tanpa CDN, tanpa backend Python). Berkas itu sendiri adalah sumbernya —
diedit langsung, tidak ada langkah build seperti `web-src/` atau `web-src-dh/`.

- Versi: `builder-ow.json` → `extraMetadata.version`. Cap di HTML (`window.GCEX_VER`) wajib sama;
  setelah menaikkan versi jalankan `python web-src-ow/cap_versi_ow.py` (diperiksa CI lewat
  `tools/rilis/cek_cap_versi.py`).
- Installer: `npx electron-builder --config builder-ow.json --win nsis --x64 --publish never`
  → `dist/Ore-Works-Setup-<versi>.exe`. Lisensi memakai kunci GC-Ex dengan aplikasi `ow` (atau `*`).
- Mencoba tanpa installer: buka `app-ow/index.html` di Edge / Chrome.
- Lisensi pihak ketiga khusus Ore Works ada di `legal-ow/` (ikut ke folder `legal` installer Ore Works saja).
- Paket **Demo Studio** (0.26.0): `python web-src-ow/sisip_demo_ow.py` menyisipkan data bor simulasi 3 sistem vein + string
  interpretasi + vein aktual kasar ke `<script type="text/plain" id="ow-demo">` (gzip + base64). Jalankan ulang bila data
  `docs/tutorial-ow/data/Vein_*` atau `*_string_interpretasi.json` berubah. Rekam demo: buka `index.html?demo=sigmoid&rekam=1`.
