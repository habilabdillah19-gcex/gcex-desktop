# Pit Studio — sumber

Pit Studio adalah satu berkas HTML offline (`app-ps/index.html`) hasil rakitan `bangun_ps.py` dari berkas `a*.js`,
`app.css`, `body.html` dan pustaka di `lib/` (three.js r128, OrbitControls, Clipper 6.4.2; tanpa CDN).

- Bangun: `python web-src-ps/bangun_ps.py` → `app-ps/index.html`. CI menjalankan `--cek` dan menolak bila
  sumber dan hasil selisih, jadi **setiap** perubahan `a*.js` harus diikuti bangun ulang sebelum commit.
- Versi: `builder-ps.json` → `extraMetadata.version`, dicap sebagai `window.GCEX_VER` saat bangun
  (diperiksa `tools/rilis/cek_cap_versi.py`).
- Pembaca block model Surpac `.mdl` **tidak** disalin ke sini: dirakit dari sumber GC-Ex Block Model
  (`web-src/mdlattr.js` + `web-src/gcex_base.html`) setiap kali bangun, supaya hasil bacanya selalu sama.
- Backend: installer membawa backend Python GC-Ex (`resources/backend`). `a36_gt.js` memakainya untuk berkas
  `.mdl` ≥ 150 MB (`/mdl/open` membangun cache kolom di disk, `/mdl/subset` mengirim jendela area kerja saja);
  berkas kecil, atau bila backend gagal, dibaca langsung di halaman. Ambang bisa diubah lewat
  `localStorage.psMdlBigMB`.
- `a37_desktop.js` hanya aktif di dalam Electron (`window.gcexDesktop`): dialog prompt/alert/confirm, cap versi.
- Installer: `npx electron-builder --config builder-ps.json --win nsis --x64 --publish never` (sesudah backend
  dibangun) → `dist/Pit-Studio-Setup-<versi>.exe`. Lisensi memakai kunci GC-Ex dengan aplikasi `ps` (atau `*`).
- Mencoba tanpa installer: buka `app-ps/index.html` di Edge / Chrome (tanpa backend; .mdl dibaca langsung).
- Data latihan **fiktif**: `docs/tutorial-ps/data/` (dibuat `docs/tutorial-ps/src/buat_data_latihan_ps.py`).
  Data perusahaan (topografi, desain pit, as-built) TIDAK BOLEH masuk repo ini.
- Lisensi pihak ketiga khusus Pit Studio ada di `legal-ps/`.
