# GC-Ex Desktop (Grade Control Excellence)

Satu repositori, dua aplikasi Windows 64-bit dengan backend Python yang sama:

| Aplikasi | Halaman | Sumber | Installer |
|---|---|---|---|
| GC-Ex Block Model | `app/index.html` | `web-src/` (`python build.py`) | `GC-Ex-Setup-<versi>.exe` |
| GC-Ex Drillhole | `app-dh/index.html` | `web-src-dh/` (`python build_dh.py`) | `GC-Ex-Drillhole-Setup-<versi>.exe` |

Kedua aplikasi bisa dipasang berdampingan; masing-masing punya penyimpanan proyek sendiri
(`%APPDATA%\\GC-Ex` dan `%APPDATA%\\GC-Ex Drillhole`).

Aplikasi desktop Windows 64-bit untuk GC-Ex Block Model: dig block per flitch, layout PDF,
as-mined & register poligon, rekonsiliasi dengan Surpac, serta koneksi ke MS Access dan Excel.

## Susunan

```
gcex-desktop/
├─ app/index.html          Tampilan GC-Ex Block Model (sama dengan versi HTML offline)
├─ app-dh/index.html       Tampilan GC-Ex Drillhole Ultimate + modul desktop
├─ web-src-dh/             Sumber Drillhole: gcex_dh_base.html + mdlbig_dh.js + deskflush_dh.js + build_dh.py
├─ builder-dh.json         Konfigurasi installer GC-Ex Drillhole
├─ electron/main.js        Jendela aplikasi, menu, log, menjalankan & menghentikan backend
├─ electron/preload.js     Jembatan aman halaman <-> aplikasi (window.gcexDesktop)
├─ backend/                Backend Python (FastAPI), hanya di 127.0.0.1
│  ├─ gcex_backend/excel_io.py   Buat register .xlsx baru, baca sheet
│  ├─ gcex_backend/xlsx_patch.py Tulis register ke workbook yang SUDAH ADA tanpa menyimpan ulang workbook
│  │                             (hanya kolom input; rumus, link, grafik, makro tetap utuh; cadangan dulu)
│  ├─ gcex_backend/access_io.py  Baca tabel / tambah baris ke database MS Access (.accdb/.mdb)
│  ├─ gcex_backend/mdl_io.py     Block model .mdl besar: cache kolom di disk, potongan RL/XY, ringkasan per RL
│  ├─ gcex_backend/server.py     API: /health /info /excel/* (termasuk /excel/register-write) /mdl/* /access/*
│  ├─ run_backend.py             Titik masuk (dipakai Electron & PyInstaller)
│  └─ tests/                     Uji otomatis
├─ web-src/               Sumber tampilan GC-Ex (modul + build.py -> app/index.html)
├─ build/icon.ico          Ikon aplikasi
└─ .github/workflows/build-windows.yml   "Pabrik" .exe otomatis di server Windows GitHub
```

Cara kerja: saat GC-Ex dibuka, Electron menyalakan `gcex-backend.exe` di port acak di komputer
itu sendiri (tidak terbuka ke jaringan), menunggu sampai siap, lalu halaman GC-Ex memakainya lewat
`window.gcexDesktop.backend()`. Saat GC-Ex ditutup, backend ikut dimatikan.

## Membuat installer (.exe)

Otomatis: setiap perubahan yang diunggah ke cabang `main` memicu GitHub Actions
(tab **Actions** di GitHub) untuk menguji backend, membangun `gcex-backend.exe`, mengecek
backend benar-benar menyala, lalu membuat installer `GC-Ex-Setup-<versi>.exe`.
Unduh dari halaman run tersebut, bagian **Artifacts**.

## Peta jalan

| Tahap | Isi | Status |
|---|---|---|
| 1 | Electron + GC-Ex + backend dasar (Excel, Access), installer otomatis | dikerjakan |
| 2 | Tombol di GC-Ex: register as-mined langsung ke Excel (selesai) / Access (menunggu contoh database), buka/simpan proyek tanpa dialog izin | dikerjakan |
| 3 | Pembaca block model .mdl besar di Python (cache disk, potongan RL/area, ringkasan seluruh model per RL) | dikerjakan |
| 3b | File jumbo: topografi / desain pit .str, .dxf, .csv ±500-700 MB dibaca per potongan (hasil identik), assay 200.000 baris, orthofoto 1 GB | selesai (0.4.0) |
| 3c | Project Tree (pohon proyek urut alur kerja + Properti) di kedua aplikasi; bilah Sayatan mengambang di Drillhole | selesai (0.5.0) |
| 3d | Orthofoto latar lepas elevasi; UI Block Model 10 langkah dengan status; as-mined lantai pick-up tidak rata | selesai (0.6.0) |
| 4 | Proyek dapat dipindahkan antar laptop (folder proyek), pembaruan otomatis, code signing | rencana |

## Kebutuhan di laptop pengguna

- Windows 10/11 64-bit.
- Untuk fitur MS Access: driver Access 64-bit (MS Office 64-bit, atau
  *Microsoft Access Database Engine 2016 Redistributable* x64). Menu **Bantuan → Tentang GC-Ex**
  dan endpoint `/info` menunjukkan apakah driver terdeteksi.
- Log ada di `%APPDATA%\GC-Ex\logs` (menu **Bantuan → Buka folder log**).
