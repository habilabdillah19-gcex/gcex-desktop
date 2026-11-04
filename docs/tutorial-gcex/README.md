# Tutorial GC-Ex Drill Hole Ultimate & Block Model — Modelling & Estimasi

- `GCEx_Tutorial_Modelling_Estimasi.pdf` — tutorial bergambar (domaining, wireframe, estimasi, block model, as-mined).
- `GCEx_Tutorial_Block_Model.pdf` — tutorial GC-Ex Block Model (flitch, dig block, additional flagging, review per flitch, as-mined).
- `data/` — data simulasi **sintetis** (bukan data perusahaan). Penjelasan lengkap di `data/BACA_SAYA.txt`,
  parameter model & angka hasil ukur di `data/JAWABAN_MODEL.txt`.
- `make_sim_data.py` — membuat ulang data simulasi vein (`python make_sim_data.py [folder] [--kecil|--besar]`,
  butuh numpy; hasilnya selalu sama karena benihnya tetap).
- `make_sim_laterit.py` — data simulasi endapan laterit berlapis (untuk Geomodeller Stratified-Laterite).
- `tambah_unsur_bm.py` — menambah kolom fiktif S_PCT / ZN_PPM / CU_PPM ke `data/SIM_BM_GC.csv`.
- `tambah_est_bm.py` — membuat `data/SIM_BM_GC_estimasi.csv`: block model latihan + kolom hasil Model
  Estimation (`est_pass`, `est_nsamp`, `est_sor`, `est_ke`, `est_type`, **`sb_frac`**, `domain_est`).
  Dipakai melatih pembobotan proporsi sub-blok di Reporting GC-Ex Block Model (20,1% blok sebagian).
- `src/` — skrip pembuat gambar & PDF kedua tutorial dari aplikasi di repo.

## Model geologi data simulasi vein

Endapan emas **epitermal low-sulphidation** yang dikontrol zona geser, dibuat supaya setiap kaidah
geologi yang relevan bisa dilatih dan jawabannya selalu diketahui:

| Unsur model | Isi |
|---|---|
| Zona geser | strike 045°, dip 70° ke azimuth 135° (bidang acuan) |
| Array vein | 4 lensa sigmoidal **en-echelon** right-stepping + 1 splay hangingwall |
| Ore shoot | **pitch 55°** dari garis strike di dalam bidang vein, sama untuk semua lensa |
| Zona dilatan | tebal **dan** kadar maksimum dikontrol satu struktur yang sama (jog = ore shoot) |
| Zonasi vertikal | paleo-muka air tanah RL 250 m: zona didih bertekstur colloform (bonanza), Ag/Au naik ke atas, Pb–Zn naik ke bawah, As penanda vein |
| Pelapukan | tudung tercuci 15 m teratas, selimut pengayaan supergen tepat di atas muka air tanah, zona transisi, batuan segar |
| Sesar | pasca-mineralisasi, strike 110°, dip 65°, offset dip-slip 12 m, panjang ±150 m — hanya memotong lensa 2 & 3 |
| Efek nugget | 5% sampel Au dilonjakkan (emas kasar) → variogram Au bernugget tinggi, Ag jauh lebih jinak |

Ukuran bawaan: **610 bor resource + 459 bor grade control**, ±98.000 baris assay 12 unsur/atribut,
topografi 2 versi, block model kosong (untuk estimasi) dan block model berisi kadar (untuk Block Model), QAQC, struktur, pick-up, wireframe, data rusak.
`--kecil` untuk latihan cepat (164 bor), `--besar` untuk uji beban (±300.000 baris assay).

Ikut setiap GitHub Release dalam `GC-Ex-<versi>_1_Dokumen.zip` (PDF) dan `GC-Ex-<versi>_2_Data-Latihan.zip` (data).
