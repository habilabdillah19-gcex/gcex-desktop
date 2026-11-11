# -*- coding: utf-8 -*-
"""Tambah kolom kode vein per lensa ("Vein") ke geologi data latihan.

Dipakai untuk melatih Geomodeller Vein > Flag > "Flag dari kolom kode" (satu domain per kode, gaya vein system):
interval yang ter-log sebagai vein (Lith QV / QVB / BX / QV_AND) diberi kode lensa tempat interval itu berada
(QV_Lensa1 ... QV_Lensa4, dari geometri model sintetis di make_sim_data.py); interval lain diberi "-".

Kolom ditambahkan di AKHIR berkas, jadi kolom lama, angka, dan urutan baris tidak berubah. Hasil selalu sama.
Pemakaian: python docs/tutorial-gcex/tambah_kode_vein.py
"""
import csv
import math
import os

import numpy as np

W = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(W, 'data')
VEIN = {'QV', 'QVB', 'BX', 'QV_AND'}

# definisi geometri lensa = bagian awal make_sim_data.py (sebelum lubang bor dibuat; tidak menulis berkas)
src = open(os.path.join(W, 'make_sim_data.py'), encoding='utf-8').read()
src = src[:src.index('\nholes = []')]
src = src.replace("os.makedirs(OUTD, exist_ok=True)", "")
G = {'__name__': 'sim_geom', '__file__': os.path.join(W, 'make_sim_data.py')}
import sys
_argv = sys.argv; sys.argv = [_argv[0]]
exec(compile(src, 'make_sim_data.py', 'exec'), G)
sys.argv = _argv
inside_all, LENSA = G['inside_all'], G['LENSA']


def lensa(P):
    """Lensa untuk sekumpulan titik: mayoritas titik di dalam vein; bila tidak ada, lensa terdekat."""
    ins, best, which, a, b = inside_all(P)
    w = which[which >= 0]
    if len(w):
        return int(np.bincount(w).argmax())
    q = G['unfault'](P)
    a2, b2, w2 = G['frame'](q)
    dd = []
    for V in LENSA[:4]:
        T = G['thick'](a2, b2, V)
        d = np.abs(w2 - G['wmid'](a2, b2, V)) - T / 2
        dd.append(float(np.min(np.where(T > 0.05, d, 1e9))))
    return int(np.argmin(dd))


def tambah(pre):
    fc, fs, fg = (os.path.join(D, pre + n) for n in ('collar.csv', 'survey.csv', 'geologi.csv'))
    if not os.path.exists(fg):
        return
    C = {r[0]: [float(r[1]), float(r[2]), float(r[3])] for r in list(csv.reader(open(fc)))[1:]}
    S = {}
    for r in list(csv.reader(open(fs)))[1:]:
        if float(r[1]) == 0.0:
            S[r[0]] = (abs(float(r[2])), float(r[3]))  # dip tersimpan negatif (ke bawah)
    rows = list(csv.reader(open(fg, newline='')))
    head, body = rows[0], rows[1:]
    if 'Vein' in head:
        k = head.index('Vein'); head = head[:k]; body = [x[:k] for x in body]
    out, n = [], {}
    for x in body:
        kode = '-'
        if x[3] in VEIN and x[0] in C and x[0] in S:
            dip, az = S[x[0]]
            v = np.array([math.sin(math.radians(az)) * math.cos(math.radians(dip)),
                          math.cos(math.radians(az)) * math.cos(math.radians(dip)), -math.sin(math.radians(dip))])
            f, t = float(x[1]), float(x[2])
            dq = f + (t - f) * (np.arange(5) + 0.5) / 5
            P = np.array(C[x[0]]) + np.outer(dq, v)
            kode = LENSA[lensa(P)]['nama']
        n[kode] = n.get(kode, 0) + 1
        out.append(x + [kode])
    with open(fg, 'w', newline='') as fh:
        w = csv.writer(fh, lineterminator='\n'); w.writerow(head + ['Vein']); w.writerows(out)
    print(pre + 'geologi.csv:', dict(sorted(n.items())))


for p in ('SIM_', 'SIM_kecil_'):
    tambah(p)
