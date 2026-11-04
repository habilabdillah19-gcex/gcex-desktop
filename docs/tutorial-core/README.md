# Tutorial DB-Ex — data dummy

`buat_data_dummy.py` membuat paket latihan `DB-Ex_Data_Dummy`. **Seluruh isinya fiktif** (nama perusahaan
PT. CONTOH TAMBANG, lubang LTH-101 / LTH-102, koordinat grid lokal, tanggal, kadar, dan semua foto termasuk
`IMG_0001.jpg` yang bergaya foto HP), sehingga aman dibagikan ke pihak luar:

```
python docs/tutorial-core/buat_data_dummy.py D:\Latihan\DB-Ex_Data_Dummy
```

Butuh Python + Pillow + openpyxl + numpy (`pip install pillow openpyxl numpy`). Hasilnya selalu sama (seed tetap), sehingga kunci
jawaban di tutorial berlaku di setiap komputer. Isi paket dijelaskan di `BACA_SAYA.txt` di dalam paket dan di dokumen
tutorial (bagian Pengantar).

## Tutorial PDF bergambar

`docs/DB-Ex_Tutorial_Penggunaan.pdf` (latihan 0–16, 37 tangkapan layar) dibuat dari `tutorial.html` di folder ini.
Gambar di `gambar/` diambil dari DB-Ex yang menjalankan paket data dummy ini dengan backend lokal dan Ollama tiruan
(jawaban AI contoh), dengan nama pemeriksa fiktif "Rina W.". Cetak ulang: buka `tutorial.html` di Chrome/Edge → Cetak → Simpan sebagai PDF (A4, grafik latar aktif).

Bab 12–18 (DB-Ex versi Qt: Singkapan, Borang Ore Spotter loading pit & ROM / crusher, RC Daily Drilling Report, ekspor ke
database & dashboard drilling, QAQC Database dengan `QAQC/QAQC_Latihan.xlsx`) memakai gambar `gambar/q*.png` dari `tutorial_shots_qt.py`: foto trench sintetis, scan borang
yang digambar ulang komputer (tulisan miring biru meniru tulisan tangan) dan jawaban AI tiruan — semuanya fiktif.

```
QT_QPA_PLATFORM=offscreen python docs/tutorial-core/tutorial_shots_qt.py   # gambar q*.png
python docs/tutorial-core/buat_pdf.py                                     # tutorial + Penjelasan Teknis PDF
```

`buat_pdf.py` juga mencetak `docs/DB-Ex_Panduan_Teknis.pdf` (penjelasan teknis) dari `docs/PANDUAN_CORE.html`
(`python docs/md2html.py docs/PANDUAN_CORE.md docs/PANDUAN_CORE.html`), dengan sampul, daftar isi dan nomor halaman.
