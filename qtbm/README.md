# Penampil Qt (tahap 2) — GC-Ex Block Model 3D

Penampil 3D block model memakai **PySide6 + OpenGL** yang berjalan **di samping** aplikasi GC-Ex
yang ada, bukan menggantinya. Dibuat untuk menjawab satu pertanyaan dengan angka: apakah tampilan
3D di luar peramban benar-benar lebih lancar untuk block model besar, dan sepadan dengan biaya
memindahkan seluruh aplikasi?

Sampai itu terbukti pada pekerjaan sehari-hari, **tidak ada yang dipindahkan**. Aplikasi GC-Ex
Block Model dan Drill Hole tetap seperti sekarang dan tetap satu-satunya yang menghasilkan angka
laporan.

## Menjalankan

    python -m qtbm <folder_proyek> <block_model.csv>

Contoh dengan data latihan:

    python -m qtbm docs/tutorial-gcex/data/SIM_BM_GC_kadar.csv

Seret = putar, roda = dekat/jauh, seret kanan = geser. Panel kanan: atribut untuk warna, batas RL,
batas sayatan, dan penghitung fps beserta jumlah blok yang digambar.

## Isi

| Berkas | Isi |
| --- | --- |
| `proyek.py` | pembaca folder proyek GC-Ex (`gcex_data.json`, `gcex_project.json`) + block model CSV, dan penghitung jalur bor dari collar/survey |
| `adegan.py` | penyusun larik siap-GPU: instans blok, warna atribut, jalur bor, permukaan topografi, saringan RL / atribut / sayatan |
| `render.py` | penggambar OpenGL 3.3 (kubus ber-instance) + kamera orbit |
| `tampilan.py` | jendela PySide6 |
| `uji_render.py` | render tanpa layar + pemeriksaan gambar + ukur fps (dipakai CI) |
| `tests/` | uji tanpa grafis: pembaca, adegan, kamera |

## Dua hal yang perlu diketahui sebelum menyentuh kode ini

**1. Block model tidak tersimpan di folder proyek.** Aplikasi menyimpannya di IndexedDB peramban
dan hanya mencatat ASAL berkasnya di `work.src`. Karena itu penampil ini membaca block model dari
berkas sumbernya (CSV; `.mdl` Surpac belum, perlu lewat backend).

**2. Koordinat harus digeser sebelum jadi `float32`.** Di sekitar northing 9.011.700, jarak antar
bilangan `float32` yang berdekatan tepat **1 meter**. Koordinat berkoma akan dibulatkan oleh GPU
dan blok tampak bergeser. Semua koordinat digeser dulu ke titik asal lokal dalam `float64`
(`adegan.titik_asal`), baru diubah ke `float32`. Jangan dibalik urutannya.

## Cara pembuktiannya

Uji tanpa grafis jalan di mana saja (`python -m pytest qtbm/tests`). Render sungguhan diperiksa di
CI pada runner Ubuntu dengan Mesa (`.github/workflows/uji-qt.yml`): gambar harus punya piksel
terisi, warnanya beragam, dan saringan RL harus mengurangi yang tergambar — lalu fps diukur pada
50 ribu / 200 ribu / 1 juta blok. Gambar hasilnya diunggah sebagai artifact agar bisa dilihat.

Penampil ini **tidak** ikut installer dan tidak menaikkan versi aplikasi mana pun.
