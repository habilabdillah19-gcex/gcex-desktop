# -*- coding: utf-8 -*-
"""Membuat permukaan latihan DXF 3DFACE: dua tahap desain pit + dua survei topografi bulanan.

Dipakai oleh dua fitur Reporting yang baru (GC-Ex Drill Hole dan GC-Ex Block Model):
  - laporan BEBERAPA DESAIN PIT sekaligus dengan topografi yang sama (fase 1 vs fase 2),
  - laporan PROGRES TOPO-KE-TOPO: material tergali antara dua survei (akhir Juni -> akhir Juli).
Tanpa berkas ini, data latihan hanya punya satu topografi titik XYZ dan tidak punya desain pit
sama sekali, sehingga kedua fitur itu tidak bisa dilatih.

DXF 3DFACE dipilih karena dibaca oleh KEDUA aplikasi: di Drill Hole lewat Data Spasial (versi
topografi / desain pit) maupun Data Referensi, di Block Model lewat Data Referensi. Formatnya
sama dengan DXF yang diexport GC-Ex sendiri, jadi jalur bacanya sudah teruji.

Permukaannya SINTETIS tetapi menumpang topografi latihan yang sudah ada (SIM_topo_xyz.csv),
jadi elevasinya menyambung dengan data lain. Pit berbentuk kerucut terbalik, lereng 45 derajat,
dan BERSARANG (fase 2 memuat fase 1) supaya kolom "tambahan" di laporan per pit bermakna.

Jalankan: python docs/tutorial-gcex/tambah_pit_topo.py [folder data]
Hasilnya selalu sama (tanpa unsur acak).
"""
import csv
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, 'data')
SRC = os.path.join(DATA, 'SIM_topo_xyz.csv')

# pusat pit = pusat array vein data latihan; petak grid 10 m (sama dengan blok model impor)
CX, CY, SEL = 505050.0, 9012000.0, 10.0
X0, X1, Y0, Y1 = 504700.0, 505400.0, 9011750.0, 9012250.0

if not os.path.exists(SRC):
    raise SystemExit('Tidak ada %s. Jalankan make_sim_data.py dulu.' % SRC)

# ---------- topografi dasar: titik XYZ latihan -> grid 10 m (rata-rata per sel, isi celah dari tetangga)
sum_z, cnt = {}, {}
with open(SRC, encoding='utf-8-sig', newline='') as f:
    rd = csv.reader(f)
    next(rd)
    for r in rd:
        try:
            x, y, z = float(r[0]), float(r[1]), float(r[2])
        except (ValueError, IndexError):
            continue
        k = (round(x / SEL), round(y / SEL))
        sum_z[k] = sum_z.get(k, 0.0) + z
        cnt[k] = cnt.get(k, 0) + 1
base = {k: sum_z[k] / cnt[k] for k in sum_z}
if not base:
    raise SystemExit('Topografi latihan kosong.')
rata = sum(base.values()) / len(base)


def topo(x, y):
    """Elevasi topografi asli di (x, y): sel terdekat, melebar sampai ketemu."""
    i, j = round(x / SEL), round(y / SEL)
    for r in range(0, 6):
        best, bd = None, 1e18
        for a in range(i - r, i + r + 1):
            for b in range(j - r, j + r + 1):
                if max(abs(a - i), abs(b - j)) != r:
                    continue
                v = base.get((a, b))
                if v is None:
                    continue
                d = (a - i) ** 2 + (b - j) ** 2
                if d < bd:
                    bd, best = d, v
        if best is not None:
            return best
    return rata


def kerucut(x, y, lantai, r_lantai):
    """Permukaan pit: kerucut terbalik lereng 45 derajat, dipotong di topografi."""
    r = math.hypot(x - CX, y - CY)
    z = lantai if r <= r_lantai else lantai + (r - r_lantai)
    return min(z, topo(x, y))


def tulis_dxf(path, zfn, layer):
    """DXF 3DFACE per petak grid (dua segitiga), format sama dengan export DXF GC-Ex."""
    nx = int(round((X1 - X0) / SEL))
    ny = int(round((Y1 - Y0) / SEL))
    r = ['0', 'SECTION', '2', 'HEADER', '9', '$ACADVER', '1', 'AC1009', '0', 'ENDSEC',
         '0', 'SECTION', '2', 'ENTITIES']
    f3 = lambda v: '%.3f' % v
    nt = 0
    for a in range(nx):
        for b in range(ny):
            xs, ys = X0 + a * SEL, Y0 + b * SEL
            P = [(xs, ys), (xs + SEL, ys), (xs + SEL, ys + SEL), (xs, ys + SEL)]
            Z = [zfn(p[0], p[1]) for p in P]
            for t in ((0, 1, 2), (0, 2, 3)):
                q = [(P[k][0], P[k][1], Z[k]) for k in t]
                r += ['0', '3DFACE', '8', layer,
                      '10', f3(q[0][0]), '20', f3(q[0][1]), '30', f3(q[0][2]),
                      '11', f3(q[1][0]), '21', f3(q[1][1]), '31', f3(q[1][2]),
                      '12', f3(q[2][0]), '22', f3(q[2][1]), '32', f3(q[2][2]),
                      '13', f3(q[2][0]), '23', f3(q[2][1]), '33', f3(q[2][2])]
                nt += 1
    r += ['0', 'ENDSEC', '0', 'EOF']
    with open(path, 'w', encoding='utf-8', newline='') as f:
        f.write('\r\n'.join(r) + '\r\n')
    return nt


def lapor(nama, zfn, layer):
    p = os.path.join(DATA, nama)
    nt = tulis_dxf(p, zfn, layer)
    zs = [zfn(X0 + i * 25.0, Y0 + j * 25.0) for i in range(int((X1 - X0) / 25)) for j in range(int((Y1 - Y0) / 25))]
    print('OK %-26s %6d segitiga  RL %.1f - %.1f' % (nama, nt, min(zs), max(zs)))


# Dua survei bulanan: pit yang sama, makin dalam & makin lebar sebulan kemudian.
lapor('SIM_topo_akhir_juni.dxf', lambda x, y: kerucut(x, y, 260.0, 40.0), 'TOPO_JUNI')
lapor('SIM_topo_akhir_juli.dxf', lambda x, y: kerucut(x, y, 245.0, 55.0), 'TOPO_JULI')
# Dua tahap desain pit (bersarang): fase 1 di dalam fase 2.
lapor('SIM_pit_fase1.dxf', lambda x, y: kerucut(x, y, 240.0, 60.0), 'PIT_FASE1')
lapor('SIM_pit_fase2.dxf', lambda x, y: kerucut(x, y, 180.0, 90.0), 'PIT_FASE2')
print('Pakai: Drill Hole -> Data Spasial (versi topografi / desain pit) atau Data Referensi;'
      ' Block Model -> Data Referensi. Laporan: Reporting -> tab "Pit & progres".')
