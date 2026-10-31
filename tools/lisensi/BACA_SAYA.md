# Lisensi GC-Ex (kunci terikat komputer)

Sejak 0.17.0, GC-Ex Block Model, Drillhole dan DB-Ex yang terpasang hanya bisa dibuka dengan **kunci lisensi**.

## Untuk pemakai
1. Buka GC-Ex. Jendela **Aktivasi** menampilkan **ID Komputer** (XXXX-XXXX-XXXX-XXXX). Klik **Salin** dan kirim ke penerbit lisensi.
2. Tempel kunci yang diterima (teks diawali `GCEX1.`) atau **Buka file .gcexlic**, lalu **Aktifkan**.
3. Satu lisensi dipakai bersama semua aplikasi GC-Ex di komputer itu (sesuai aplikasi yang tercantum di kunci); file: `%APPDATA%\GC-Ex Lisensi\lisensi.json`.
4. Info / ganti kunci (mis. perpanjangan): menu **Bantuan → Lisensi GC-Ex…**. 14 hari sebelum berakhir muncul pengingat.

## Untuk penerbit (pemilik GC-Ex)
- Alat: `tools/lisensi/GCEx_Pembuat_Lisensi.html` (buka di Edge / Chrome terbaru, offline).
- Muat **kunci privat** `GCEx_KUNCI_PRIVAT_LISENSI.json` → isi ID Komputer, nama pemegang, organisasi, aplikasi (Block Model / Drillhole / Core / Semua), berlaku sampai (atau tanpa batas) → **Buat kunci lisensi** → salin / simpan `.gcexlic`.
- Kunci privat **tidak** ada di repositori. Simpan di flashdisk + cadangan offline. Bila hilang, lisensi baru tidak bisa dibuat untuk versi ini (perlu rilis baru dengan pasangan kunci baru). Bila bocor, siapa pun bisa membuat lisensi.
- Daftar lisensi yang dibuat tersimpan di browser alat; unduh CSV sebagai arsip.

## Cara kerja
- ID Komputer = hash SHA-256 dari MachineGuid Windows (cadangan: nama komputer + CPU + MAC).
- Kunci = `GCEX1.<data>.<tanda tangan Ed25519>`; data berisi no. lisensi, ID komputer, aplikasi, pemegang, tanggal terbit & kedaluwarsa. Aplikasi hanya memegang kunci publik (`electron/license.js`), jadi kunci tidak bisa dipalsukan atau diubah (mis. tanggal) tanpa kunci privat.
- Tanggal terbesar yang pernah terlihat dicatat, sehingga memundurkan jam komputer tidak menghidupkan lisensi kedaluwarsa.
- Saat pengembangan (`npm start`) lisensi tidak diwajibkan; set `GCEX_LIC=1` untuk mengujinya.
