# -*- coding: utf-8 -*-
"""Project Tree: sisipkan node kampanye sebagai anak pertama node Database Bor.

fDb() di ptree_dh.js adalah fungsi lokal di dalam IIFE, jadi tidak bisa dibungkus dari modul lain;
satu-satunya titik sisip yang aman adalah larik kids-nya. Kampanye ditaruh PALING ATAS supaya node
Database Bor terbaca seperti daftar database di Surpac (exploration_2024, infill_2023, ...), dengan
tabel gabungan Collar / Survey / Assay / Geologi tetap di bawahnya.
"""


def patch(s: str) -> str:
    """Patch ptree_dh.js: node kampanye + perintah menu."""
    return _menu_db(patch_tree(s))


def _menu_db(s: str) -> str:
    """Menu node "Database Bor" diawali perintah kampanye (kpMenuDb)."""
    a = ("      menu:function(){return[{h:'Import file (langsung)'},")
    assert s.count(a) == 1, 'awal menu node Database Bor tidak ditemukan tepat satu kali'
    s = s.replace(a, "      menu:function(){return(window.kpMenuDb?kpMenuDb():[]).concat(["
                     "{h:'Import file (langsung)'},")
    b = "fn:function(){PTD.drop('all');}}];},"
    assert s.count(b) == 1, 'akhir menu node Database Bor tidak ditemukan tepat satu kali'
    s = s.replace(b, "fn:function(){PTD.drop('all');}}]);},")
    return s


def _tree_body(s: str) -> str:
    a = "      kids:[tb('db.collar',"
    assert s.count(a) == 1, 'awal kids node Database Bor tidak ditemukan tepat satu kali'
    s = s.replace(a, "      kids:(window.kpTree?kpTree():[]).concat([tb('db.collar',")

    # 0.24.44: menu node Plan bor berubah (set plan bor); jangkarnya akhir menu itu
    b = ("{sep:1},{t:'Hapus semua titik di plan aktif…',danger:1,fn:A('plClear')}];}}]};}")
    assert s.count(b) == 1, 'akhir kids node Database Bor tidak ditemukan tepat satu kali'
    # 0.24.30: node "Filter data bor" (fq_dh.js) ikut masuk ke kids, di urutan paling bawah.
    s = s.replace(b, b[:-4] + "]).concat(window.fqTree?fqTree():[])};}")

    # ---- titik ANALISIS dialihkan dari visHoles() ke visHolesK() (set kerja saja).
    # visHoles() tetap daftar TAMPIL supaya bor referensi masih tergambar di 3D / sayatan.
    return s


ANALISIS = [
    # (berkas, potongan unik, keterangan)
    ('base', "function okData(){var ids=visHoles()", 'Geostatistik: uji estimasi'),
    ('base', "var S=secK(),ids=visHoles(),el=$('elementFilter').value,ei=elements.indexOf(el);", 'Geostatistik: analisis sayatan'),
    ('base', "var ids=visHoles();if(o.scope==='slab')", 'Flag otomatis dari kadar'),
    ('base', "var ids=visHoles(),el=$('elementFilter').value,ei=elements.indexOf(el),cl=", 'Komposit & statistik'),
    ('base', "function gmHits(A){var S=secK(),F=p2fn(S.g),out=[];visHoles()", 'Klik flag di sayatan'),
    ('env', "var ids=visHoles();if(GM.opt.scope==='slab')", 'Selubung mineralisasi (envelope)'),
]


def patch_analisis(s: str, tanda: str) -> str:
    """Ganti visHoles() -> visHolesK() hanya di titik analisis; tiap potongan wajib unik."""
    n = 0
    for berkas, frag, _ket in ANALISIS:
        if berkas != tanda:
            continue
        assert s.count(frag) == 1, 'potongan analisis tidak unik / tidak ada: ' + frag[:60]
        s = s.replace(frag, frag.replace('visHoles()', '(window.visHolesK?visHolesK():visHoles())'))
        n += 1
    assert n, 'tidak ada titik analisis untuk ' + tanda
    return s


def patch_tree(s: str) -> str:
    s = _tree_body(s)
    c = "      menu:function(){return[{h:'Import file (langsung)'}"
    assert s.count(c) == 1, 'menu node Database Bor tidak ditemukan tepat satu kali'
    # Dulu di sini ditambahkan "Kampanye baru…" & "Gabungkan kampanye… (merge)". Keduanya kembar dengan
    # "Tambah kampanye baru…" & "Buat set merge…" dari kpMenuDb() yang sudah tampil di menu yang sama
    # (permintaan pemilik 8 Nov 2026: satu perintah satu tempat), jadi tidak ditambahkan lagi.
    return s
