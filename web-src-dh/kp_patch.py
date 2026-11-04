# -*- coding: utf-8 -*-
"""Project Tree: sisipkan node kampanye sebagai anak pertama node Database Bor.

fDb() di ptree_dh.js adalah fungsi lokal di dalam IIFE, jadi tidak bisa dibungkus dari modul lain;
satu-satunya titik sisip yang aman adalah larik kids-nya. Kampanye ditaruh PALING ATAS supaya node
Database Bor terbaca seperti daftar database di Surpac (exploration_2024, infill_2023, ...), dengan
tabel gabungan Collar / Survey / Assay / Geologi tetap di bawahnya.
"""


def patch(s: str) -> str:
    a = "      kids:[tb('db.collar',"
    assert s.count(a) == 1, 'awal kids node Database Bor tidak ditemukan tepat satu kali'
    s = s.replace(a, "      kids:(window.kpTree?kpTree():[]).concat([tb('db.collar',")

    b = ("          menu:function(){return[{t:'Export CSV plan bor',fn:A('plExport')},{sep:1},"
         "{t:'Hapus semua titik rencana',danger:1,fn:A('plClear')}];}}]};}")
    assert s.count(b) == 1, 'akhir kids node Database Bor tidak ditemukan tepat satu kali'
    s = s.replace(b, b[:-4] + "])};}")

    # menu node Database Bor: tambah perintah kampanye
    c = "      menu:function(){return[{t:'Tambah / perbarui data bor (upsert)…',fn:ups}"
    assert s.count(c) == 1, 'menu node Database Bor tidak ditemukan tepat satu kali'
    s = s.replace(c, c + ",{sep:1},{t:'Kampanye baru…',fn:function(){if(window.kpTambah)kpTambah();}}"
                      ",{t:'Gabungkan kampanye… (merge)',fn:function(){if(window.kpGabung)kpGabung();}}")
    return s
