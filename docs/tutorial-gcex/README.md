# Tutorial GC-Ex Drillhole & Block Model — Modelling & Estimasi

- `GCEx_Tutorial_Modelling_Estimasi.pdf` — tutorial bergambar (domaining, wireframe, estimasi, block model, as-mined).
- `data/` — data simulasi **sintetis** (bukan data perusahaan): collar, survey, assay, geologi, pick-up, topografi,
  block model GC, wireframe contoh, data upsert, data rusak (latihan validasi), vein bercabang. Penjelasan di `data/BACA_SAYA.txt`.
- `GCEx_Tutorial_Block_Model.pdf` — tutorial GC-Ex Block Model 0.20 (flitch, dig block, additional flagging, review per flitch, as-mined).
- `tambah_unsur_bm.py` — menambah kolom fiktif S_PCT / ZN_PPM / CU_PPM ke `data/SIM_BM_GC.csv`.
- `src/` — skrip pembuat gambar & PDF kedua tutorial dari aplikasi di repo.
- `make_sim_data.py` — membuat ulang data simulasi (`python make_sim_data.py [folder]`, butuh numpy; hasil selalu sama).

Ikut setiap GitHub Release dalam `GC-Ex-<versi>_1_Dokumen.zip` (PDF) dan `GC-Ex-<versi>_2_Data-Latihan.zip` (data).
