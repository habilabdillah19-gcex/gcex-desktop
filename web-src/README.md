# web-src: sumber tampilan GC-Ex

`app/index.html` adalah HASIL BUILD — jangan disunting langsung. Ubah file di sini, lalu jalankan:

    python web-src/build.py

| File | Isi |
|---|---|
| gcex_base.html | GC-Ex Block Model asli (dasar) |
| am2.js | As-Mined v2: register poligon, layout, ekspor |
| sgfix.js | SG terpusat (blok SG <= 0), metode tonase "Seperti Surpac", audit blok |
| ui_layer.js | UI seragam (tab panel, panel Layer, posisi slab) |
| fp2.js | Folder proyek v2, pemulihan 3D |
| plotly.js | Library grafik Plotly 2.27.0 (ditanam ke index.html) |
| build.py | Menggabungkan semuanya menjadi app/index.html |
