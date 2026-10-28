# -*- coding: utf-8 -*-
"""Aplikasi desktop (terpasang): tidak ada fungsi untuk mengambil kode sumber halaman.
- Tautan "unduh salinan HTML dengan Plotly tertanam" dihapus; SA.saveStandalone tidak lagi menyimpan HTML.
- Salinan kode sumber halaman (SA.src0 = document.documentElement.outerHTML) tidak dibuat.
Dipakai oleh web-src/build.py (Block Model) dan web-src-dh/build_dh.py (Drillhole)."""


def patch(s):
    def rep(a, b):
        nonlocal s
        c = s.count(a)
        assert c == 1, 'nosrc_patch: pola ditemukan %d kali: %s' % (c, a[:80])
        s = s.replace(a, b)
    rep("""<div id="plSave" style="display:none" class="hint2">Agar file ini benar-benar mandiri untuk dibagikan, <a href="#" onclick="SA.saveStandalone();return false">unduh salinan HTML dengan Plotly tertanam</a>.</div>""",
        """<div id="plSave" style="display:none"></div>""")
    rep("SA.src0='<!DOCTYPE html>\\n'+document.documentElement.outerHTML;", "SA.src0='';")
    rep("saveStandalone=async function(){", "saveStandalone=async function(){return;")
    return s
