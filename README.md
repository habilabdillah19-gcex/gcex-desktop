# GC-Ex Desktop (Grade Control Excellence)

Satu repositori, tiga aplikasi Windows 64-bit dengan backend Python yang sama:

| Aplikasi | Halaman | Sumber | Installer |
|---|---|---|---|
| GC-Ex Block Model | `app/index.html` | `web-src/` (`python build.py`) | `GC-Ex-Setup-<versi>.exe` |
| GC-Ex Drillhole | `app-dh/index.html` | `web-src-dh/` (`python build_dh.py`) | `GC-Ex-Drillhole-Setup-<versi>.exe` |
| Core-Ex | `app-core/index.html` | langsung `app-core/index.html` (satu file, tanpa build) | `Core-Ex-Setup-<versi>.exe` |

Ketiga aplikasi bisa dipasang berdampingan; masing-masing punya penyimpanan sendiri
(`%APPDATA%\\GC-Ex`, `%APPDATA%\\GC-Ex Drillhole`, `%APPDATA%\\Core-Ex`).

**Core-Ex** (Core Excellence; dahulu GC-Ex Core Interpretation) — interpretasi foto core box 100% offline: folder foto (ribuan foto, bersubfolder)
dibaca backend, Hole / Box / kedalaman dari nama file, deskripsi oleh model vision lokal di **Ollama**
(`core_dh.py`: import Collar/Survey/Assay/Geologi CSV/Excel dengan header dinamis, cari cepat, overlay assay di foto)
(`127.0.0.1:11434`, mis. `qwen3-vl:8b`), verifikasi geologist, export Excel. Hasil disimpan di
`<folder foto>/_GCEx_Core/gcex_core.db` (SQLite) supaya rekan bisa melanjutkan. Panduan: `docs/PANDUAN_CORE.md`.
Pengembangan: `npm run start:core` (Windows) atau `GCEX_APP=core npx electron .`.

Aplikasi desktop Windows 64-bit untuk GC-Ex Block Model: dig block per flitch, layout PDF,
as-mined & register poligon, rekonsiliasi dengan Surpac, serta koneksi ke MS Access dan Excel.

## Susunan

```
gcex-desktop/
├─ app/index.html          Tampilan GC-Ex Block Model (sama dengan versi HTML offline)
├─ app-dh/index.html       Tampilan GC-Ex Drillhole Ultimate + modul desktop
├─ app-core/index.html     Tampilan Core-Ex (offline penuh: tanpa CDN, ikon & font lokal)
├─ builder-core.json       Konfigurasi installer Core-Ex
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
│  ├─ gcex_backend/core_io.py    Core-Ex: proyek foto (SQLite), thumbnail, antrean AI Ollama, Excel
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
| 3e | Core-Ex: foto core box + AI vision lokal (Ollama), verifikasi, Excel | selesai (0.15.0) |
| 3f | Core-Ex: data bor header dinamis, cari cepat, filter kadar, overlay assay di foto | selesai (0.16.0) |
| 3g | GC-Ex Core Interpretation berganti nama menjadi **Core-Ex** (Core Excellence), tetap keluarga GC-Ex & lisensi bersama | selesai (0.18.0) |
| 3h | Core-Ex menjalankan Ollama otomatis bila belum aktif + tombol **Jalankan Ollama** di dialog AI | selesai (0.18.1) |
| 3i | Data besar: block model .mdl > 6 GB lancar di RAM 8 GB / VRAM 4 GB (indeks RL di luar RAM, batas blok per pemuatan, penampang 2D tanpa jeda); tanpa pembaruan online | selesai (0.18.2) |
| 3j | Grade shell 3D (Ore Geometry) dengan **Surface-Following**: hanya sel di sekitar batas cut-off yang dihitung penuh (hasil sama, 1,3–5 × lebih cepat) | selesai (0.18.3) |
| 3k | Setiap pembaruan terbit di **GitHub Release** v<versi>: 3 installer terpisah + dokumen & tutorial + data latihan + lisensi & tentang + catatan rilis (commit) + SHA-256 + kode sumber | selesai (0.18.4) |
| 3l | Catatan rilis: huruf non-ASCII (—, é) tidak rusak, jam commit ditulis dalam WIB | selesai (0.18.5) |
| 3m | Identitas visual baru (selaras Core-Ex): halaman muka penuh, tema earthy kedua aplikasi, logo GC-Ex / BLOCK MODEL · DRILL HOLE ULTIMATE, nama project site per proyek; Sayatan 2D, garis sayatan di 3D tampak atas, rekap & edit string, legenda string ringkas, Geological Modelling per domain aktif | selesai (0.19.0) |
| 4 | Proyek dapat dipindahkan antar laptop (folder proyek), pembaruan otomatis, code signing | rencana |

## Kebutuhan di laptop pengguna

- Windows 10/11 64-bit.
- Untuk fitur MS Access: driver Access 64-bit (MS Office 64-bit, atau
  *Microsoft Access Database Engine 2016 Redistributable* x64). Menu **Bantuan → Tentang GC-Ex**
  dan endpoint `/info` menunjukkan apakah driver terdeteksi.
- Untuk Core-Ex: Ollama (dipasang terpisah) + satu model vision; lihat `docs/PANDUAN_CORE.md`
  untuk pemasangan tanpa internet. Tanpa Ollama, log tetap bisa diisi & diverifikasi manual.
- Log ada di `%APPDATA%\GC-Ex\logs` (menu **Bantuan → Buka folder log**).
