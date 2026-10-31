# Tutorial DB-Ex — data dummy

`buat_data_dummy.py` membuat paket latihan `DB-Ex_Data_Dummy`. **Seluruh isinya fiktif** (nama perusahaan
PT. CONTOH TAMBANG, lubang LTH-101 / LTH-102, koordinat grid lokal, tanggal, kadar, dan semua foto termasuk
`IMG_0001.jpg` yang bergaya foto HP), sehingga aman dibagikan ke pihak luar:

```
python docs/tutorial-core/buat_data_dummy.py D:\Latihan\DB-Ex_Data_Dummy
```

Butuh Python + Pillow + openpyxl (`pip install pillow openpyxl`). Hasilnya selalu sama (seed tetap), sehingga kunci
jawaban di tutorial berlaku di setiap komputer. Isi paket dijelaskan di `BACA_SAYA.txt` di dalam paket dan di dokumen
tutorial (bagian Pengantar).

## Tutorial PDF bergambar

`docs/DB-Ex_Tutorial_Penggunaan.pdf` (11 latihan, 20 tangkapan layar) dibuat dari `tutorial.html` di folder ini.
Gambar di `gambar/` diambil dari DB-Ex yang menjalankan paket data dummy ini dengan backend lokal dan Ollama tiruan
(jawaban AI contoh), dengan nama pemeriksa fiktif "Rina W.". Cetak ulang: buka `tutorial.html` di Chrome/Edge → Cetak → Simpan sebagai PDF (A4, grafik latar aktif).
