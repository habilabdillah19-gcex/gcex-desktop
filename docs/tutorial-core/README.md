# Tutorial GC-Ex Core Interpretation — data dummy

`buat_data_dummy.py` membuat paket latihan `GCEx_Core_Data_Dummy`. **Seluruh isinya fiktif** (nama perusahaan
PT. CONTOH TAMBANG, lubang LTH-101 / LTH-102, koordinat grid lokal, tanggal, kadar, dan semua foto termasuk
`IMG_0001.jpg` yang bergaya foto HP), sehingga aman dibagikan ke pihak luar:

```
python docs/tutorial-core/buat_data_dummy.py D:\Latihan\GCEx_Core_Data_Dummy
```

Butuh Python + Pillow + openpyxl (`pip install pillow openpyxl`). Hasilnya selalu sama (seed tetap), sehingga kunci
jawaban di tutorial berlaku di setiap komputer. Isi paket dijelaskan di `BACA_SAYA.txt` di dalam paket dan di dokumen
tutorial (bagian Pengantar).
