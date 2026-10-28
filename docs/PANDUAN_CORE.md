# Panduan GC-Ex Core Interpretation

Interpretasi foto core box dengan AI yang berjalan **di komputer sendiri**. Tidak butuh internet, tidak ada foto atau data yang dikirim ke luar.

Pembaruan terakhir: 28 Oktober 2026 (versi 0.15.0).

## 1. Cara kerja singkat

| Bagian | Fungsi | Berjalan di |
|---|---|---|
| Jendela GC-Ex Core Interpretation | Tabel log, pratinjau foto, kartu interpretasi, verifikasi, export Excel | komputer ini |
| Backend GC-Ex (FastAPI) | Membaca ribuan foto dari folder, membuat thumbnail, menyimpan hasil di database, mengantre AI, membuat Excel | komputer ini, hanya `127.0.0.1` |
| Ollama + model vision | "Melihat" foto lalu menulis deskripsi (litologi, warna, pelapukan, oksidasi, alterasi, RQD, GSI, RMR, catatan) | komputer ini, `127.0.0.1:11434` |

Backend dan Ollama hanya mendengar di `127.0.0.1`, jadi tidak bisa diakses dari komputer lain di jaringan.

## 2. Memasang

### 2a. GC-Ex Core Interpretation

1. Unduh `GC-Ex-Core-Setup-<versi>.exe` dari GitHub (tab **Actions** → run terbaru → **Artifacts** → `GC-Ex-Core-Setup-Windows`).
2. Jalankan installer. Tidak perlu hak admin. Shortcut **GC-Ex Core Interpretation** muncul di desktop dan Start menu.
3. Aplikasi bisa dipasang berdampingan dengan GC-Ex Block Model dan GC-Ex Drillhole.

### 2b. Ollama (mesin AI lokal) — sekali per komputer

Di komputer yang **ada internet** (mis. laptop kantor saat di kota):

1. Unduh installer Windows Ollama dari situs resmi Ollama (`OllamaSetup.exe`). Pakai versi **0.12.7 atau lebih baru** (dibutuhkan model Qwen3-VL).
2. Pasang, lalu buka Command Prompt dan unduh model vision, mis.:
   ```
   ollama pull qwen3-vl:8b
   ```
3. Model tersimpan di folder `%USERPROFILE%\.ollama\models`.

Untuk komputer **tanpa internet** di site:

1. Salin `OllamaSetup.exe` dan seluruh folder `%USERPROFILE%\.ollama\models` dari komputer di atas ke flashdisk / hard disk.
2. Di komputer site: pasang `OllamaSetup.exe`, lalu tempel folder `models` ke `%USERPROFILE%\.ollama\models` (buat foldernya bila belum ada).
3. Jalankan Ollama dari Start menu (ikon llama di system tray). Di GC-Ex, titik di kanan atas berubah hijau: **AI lokal: qwen3-vl:8b**.

Bila folder model ingin disimpan di drive lain (mis. `D:\OllamaModels`), atur variabel lingkungan `OLLAMA_MODELS` ke folder itu lalu jalankan ulang Ollama.

### 2c. Memilih model

| Model | Ukuran unduhan | Cocok untuk |
|---|---|---|
| `qwen3-vl:8b` (disarankan) | ±6,1 GB | PC / laptop dengan kartu grafis NVIDIA ≥ 8 GB VRAM, atau RAM ≥ 16 GB |
| `qwen3-vl:4b` | ±3,3 GB | laptop biasa (RAM 8–16 GB); lebih cepat, sedikit kurang teliti |
| `qwen2.5vl:7b`, `gemma3:12b`, `llama3.2-vision:11b` | 6–8 GB | alternatif bila sudah terpasang |

Perkiraan waktu per foto: GPU 8 GB ±5–20 detik; hanya CPU ±1–3 menit. Antrean berjalan di latar belakang, jadi 500 foto bisa ditinggal semalam. Model yang tidak bisa melihat gambar (mis. `llama3.2:3b`) tampil abu-abu dan tidak bisa dipilih.

## 3. Alur kerja

1. **Buka folder foto** → pilih folder berisi foto core box. Subfolder (mis. per lubang bor) ikut dibaca. Format: JPG, PNG, TIFF, BMP, WEBP.
2. Hole ID, nomor box dan kedalaman **dibaca dari nama file** bila polanya jelas (bila tidak, AI membaca papan label di foto, lihat bagian 3a), mis.:
   - `LTH-101_Box11_36.30-40.10.jpg` → LTH-101, box 11, 36,30–40,10 m
   - `Z3-280-63 BX4 10.2m-14.0m.jpg` → Z3-280-63, box 4, 10,2–14,0 m
   - `GCD0123 B05 12,5-15,0m.jpg` → GCD0123, box 5, 12,5–15,0 m

   Isian dari nama file diberi label berarsir **nama file** dan tidak ditimpa AI. Nama seperti `IMG_0001.jpg` dibiarkan kosong: AI mencoba membaca papan label di foto.
3. **Jalankan AI lokal** → pilih model → **Analisis foto yang belum**. Bilah kemajuan di bawah menunjukkan jumlah, sisa waktu, dan tombol **Hentikan**. Hasil tiap foto langsung tersimpan, jadi aplikasi boleh ditutup di tengah jalan; jalankan lagi untuk melanjutkan yang belum.
4. **Periksa & perbaiki.** Klik baris tabel (atau ↑ ↓) untuk melihat foto. Scroll = zoom, tarik = geser, klik ganda = pas layar, tombol ↗ = resolusi penuh untuk membaca label kecil. Ubah isian di kartu kiri atau langsung di tabel.
   - Sel **biru muda** (label biru **AI**) = isian AI yang belum dicek.
   - Label **diedit** (hijau) = sudah diubah geologist. Isian ini **tidak pernah ditimpa AI**, walau AI dijalankan ulang.
5. **Verifikasi**: tombol **Verifikasi & lanjut** atau **Ctrl+Enter** menandai foto sudah diperiksa lalu pindah ke foto berikutnya. Foto terverifikasi tidak disentuh AI lagi. Beberapa foto sekaligus: centang di kolom kiri tabel → **Verifikasi terpilih**.
6. **Export Excel**: semua foto atau hanya yang tampil sesuai filter. Sheet `Core Log` berisi semua kolom + status AI, keyakinan AI, siapa yang memverifikasi; nama file foto bisa diklik untuk membuka fotonya. Sel biru muda di Excel = isian AI yang belum diverifikasi.

### 3a. Papan label yang dibaca AI

AI diberi tahu tata letak foto core box proyek (contoh asli: `docs/referensi/contoh_corebox_LTH-101_box11.jpg`):

| Tulisan di papan | Kolom di GC-Ex |
|---|---|
| HOLE ID: LTH-101 | Hole ID |
| START DRILL: 05-03-25 | Start Drill |
| BOX: 11 | Box No |
| DATE POTO: 12-03-25 | Tanggal Foto |
| DEPTH: 36.30 | From (m) |
| M:TO: 40.10 | To (m) |
| M:CONDT: WET | Kondisi Foto |

Kotak berisi 4 baris core (atas = dangkal, kiri → kanan); papan catur di bawah = skala 20 cm per kotak, dipakai AI untuk memperkirakan panjang potongan core (recovery, RQD). Bila format papan di proyek lain berbeda, tulis di **Instruksi tambahan**.

**Filter dua arah:** pilih Hole ID dan isi rentang kedalaman → tabel menyaring dan pratinjau langsung lompat ke foto pertama yang cocok. Klik judul kolom untuk mengurutkan; klik **No** untuk kembali ke urutan nama file.

**Riwayat:** di bawah kartu, **Riwayat perubahan & jawaban asli AI** menunjukkan setiap perubahan (nilai lama → baru, siapa, kapan, manual / AI) dan jawaban mentah AI.

**Instruksi tambahan** di dialog AI: tulis aturan proyek, mis. kode litologi `AND, DAC, QV, BX`, atau "tulis warna dalam bahasa Inggris saja".

## 4. Dikerjakan bersama (beberapa geologist)

- Hasil kerja disimpan di subfolder `_GCEx_Core` **di dalam folder foto** (`gcex_core.db`). Geologist lain yang membuka folder yang sama (mis. di drive jaringan) melihat dan melanjutkan pekerjaan yang sama. Nama Anda dicatat pada setiap editan dan verifikasi.
- Foto asli tidak pernah diubah, dipindah, atau diganti namanya.
- Folder boleh dipindah ke drive lain asalkan subfolder `_GCEx_Core` ikut tersalin.
- Bila folder tidak bisa ditulisi (hanya-baca), GC-Ex memberi tahu dan menyimpan hasil di komputer ini saja.
- **Pindai ulang** mendaftarkan foto baru yang ditambahkan ke folder; foto yang dihapus ditandai **File hilang** (hasilnya tetap tersimpan).
- Sebaiknya satu folder dikerjakan satu orang pada satu waktu; dua orang mengedit foto yang sama bersamaan = editan terakhir yang berlaku.

## 5. Dari dashboard lama (Gemini)

**Impor JSON lama** membaca file proyek `.json` dari dashboard versi Gemini dan mencocokkannya per nama file foto. Hasil berstatus "Done" masuk sebagai isian AI (biru muda, belum diverifikasi); sisanya sebagai isian manual. Foto yang tidak ada di folder dilaporkan.

## 6. Batasan yang perlu diketahui

- **RQD, GSI, RMR dan core recovery dari AI adalah perkiraan visual dari foto**, bukan pengukuran di core shed (panjang potongan, kondisi rekahan, kekuatan batuan tidak bisa diukur dari foto). Pakai sebagai bantuan awal; nilai resmi tetap dari logging geoteknik.
- Pembacaan papan label tergantung ketajaman foto. Bila AI salah membaca Hole ID / kedalaman, perbaiki manual; lebih baik lagi beri nama file dengan pola di bagian 3.
- Keyakinan AI (rendah / sedang / tinggi) adalah penilaian model itu sendiri, bukan jaminan.

## 7. Masalah umum

| Gejala | Penyebab / solusi |
|---|---|
| Titik merah "Ollama tidak aktif" | Ollama belum dipasang / belum dijalankan. Buka Ollama dari Start menu, lalu klik **Periksa** di dialog AI. |
| "Belum ada model vision" | Model belum diunduh / disalin. Lihat bagian 2b. |
| AI sangat lambat | Model berjalan di CPU. Pakai `qwen3-vl:4b`, ukuran foto 1024 px, atau komputer dengan kartu grafis NVIDIA. |
| Banyak foto berstatus "AI gagal" | Arahkan kursor ke label "AI gagal" untuk melihat penyebab. Biasanya Ollama tertutup di tengah antrean atau memori habis; jalankan Ollama lagi lalu **Jalankan AI lokal** (yang gagal diulang otomatis). |
| "Folder ini tidak bisa ditulisi" | Folder hanya-baca. Hasil disimpan di komputer ini saja; salin folder foto ke lokasi yang bisa ditulisi untuk kerja bersama. |
| Foto tidak muncul di tabel | Ekstensi bukan JPG/PNG/TIFF/BMP/WEBP, atau foto ditambahkan setelah folder dibuka: klik **Pindai ulang**. |
| Bar "Backend tidak aktif" | Menu **Bantuan → Buka folder log**, kirim `backend.log` dan file log terbaru. |
