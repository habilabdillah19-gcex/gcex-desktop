# -*- coding: utf-8 -*-
"""Sisipan untuk AUTORUN (arun_dh.js).

1. gmDraft() mencatat jumlah string yang dibuat / diperbarui / dilewati ke GM.lastDraft, supaya
   laporan autorun memakai ANGKA yang sama dengan yang dipakai panel — bukan hasil parsing teks.
2. Node Project Tree: Autorun Wireframe di bawah Geomodeller Vein, Autorun Estimation di bawah
   Model Estimation, Autorun Lapisan di bawah Stratified-Laterite.
"""


def patch_base(s: str) -> str:
    """gmDraft(): simpan hitungan ke GM.lastDraft sebelum GM.lastStr dirangkai."""
    a = "  GM.lastStr=(made||rep)?made+' string baru, '"
    assert s.count(a) == 1, 'rangkaian GM.lastStr di gmDraft tidak ditemukan tepat satu kali'
    return s.replace(a, "  GM.lastDraft={made:made,rep:rep,skip:skip,secN:secN};\n" + a)


def patch_tree(s: str) -> str:
    # --- Geomodeller Vein: kids diakhiri node autorun
    a = (".concat(D.filter(function(d){return !d.par;}).map(kid))};}")
    assert s.count(a) == 1, 'akhir kids node Geomodeller Vein tidak ditemukan tepat satu kali'
    s = s.replace(a, ".concat(D.filter(function(d){return !d.par;}).map(kid))"
                     ".concat(window.arWfTree?arWfTree():[])};}")

    # --- Stratified-Laterite
    b = ("so('sl.4','④ Laporan WMT / DMT','report',4)])};}")
    assert s.count(b) == 1, 'akhir kids node Stratified-Laterite tidak ditemukan tepat satu kali'
    s = s.replace(b, "so('sl.4','④ Laporan WMT / DMT','report',4)])"
                     ".concat(window.arLatTree?arLatTree():[])};}")

    # --- Model Estimation
    c = ("sub('me.4','Hasil','report','ME','Hasil')])});")
    assert s.count(c) == 1, 'akhir kids node Model Estimation tidak ditemukan tepat satu kali'
    s = s.replace(c, "sub('me.4','Hasil','report','ME','Hasil')])"
                     ".concat(window.arEstTree?arEstTree():[])});")
    return s
