# -*- coding: utf-8 -*-
"""Membuat SIM_BM_GC_estimasi.csv: block model latihan + atribut hasil Model Estimation GC-Ex Drill Hole.

Gunanya melatih dua hal di GC-Ex Block Model yang hanya muncul bila atributnya ada:
  - Reporting BM: pembobotan proporsi volume sub-blok (kolom sb_frac), sehingga blok di batas solid
    dihitung SEBAGIAN. Tanpa pembobotan itu, block model yang sama memberi tonase berbeda antara
    laporan di Drill Hole dan di Block Model.
  - membaca atribut hasil estimasi (est_pass, est_nsamp, est_sor, est_ke, est_type, domain_est) pada
    block model yang berasal dari Drill Hole.

Jalankan: python docs/tutorial-gcex/tambah_est_bm.py [folder data]
Hasilnya SELALU sama (benih tetap), jadi angka di tutorial bisa dicocokkan.

Catatan: angka est_* di sini TIRUAN, dibuat agar bentuk datanya menyerupai keluaran Model Estimation.
Untuk latihan estimasi yang sebenarnya, pakai GC-Ex Drill Hole dengan data bor simulasinya.
"""
import csv, os, random, sys

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, 'data')
SRC = os.path.join(DATA, 'SIM_BM_GC_kadar.csv')
OUT = os.path.join(DATA, 'SIM_BM_GC_estimasi.csv')

if not os.path.exists(SRC):
    raise SystemExit('Tidak ada %s. Jalankan make_sim_data.py dulu.' % SRC)

random.seed(20261105)
TAMBAH = ['est_pass', 'est_nsamp', 'est_sor', 'est_ke', 'est_nhole', 'est_spasi', 'est_type', 'sb_frac', 'domain_est']

with open(SRC, encoding='utf-8-sig', newline='') as f:
    rd = csv.reader(f)
    head = next(rd)
    rows = list(rd)

ix = {k.strip().upper(): i for i, k in enumerate(head)}
kol_au = ix.get('AU_GC', ix.get('AU', None))

n_part = 0
with open(OUT, 'w', encoding='utf-8', newline='') as f:
    w = csv.writer(f)
    w.writerow(head + TAMBAH)
    for r in rows:
        try:
            au = float(r[kol_au]) if kol_au is not None and r[kol_au] not in ('', None) else -99.0
        except ValueError:
            au = -99.0
        ore = au > 0.3

        # pass pencarian: blok berkadar (data rapat) lebih sering pass 1
        p = random.choices([1, 2, 3], [0.6, 0.3, 0.1])[0] if ore else random.choices([1, 2, 3], [0.2, 0.4, 0.4])[0]
        ns = max(2, int(random.gauss(16 if p == 1 else 9, 4)))
        sor = round(min(0.98, max(0.05, random.gauss(0.80 if p == 1 else 0.45, 0.12))), 3)
        ke = round(min(0.95, max(0.02, sor - random.uniform(0.05, 0.3))), 3)
        nh = max(1, int(random.gauss(4 if p == 1 else 2, 1.2)))
        spasi = round(max(8.0, random.gauss(18 if p == 1 else 38, 7)), 1)
        # est_type: 1 = koreksi blok GC, 2 = blok tambahan, 3 = waste (di luar solid)
        ty = 1 if ore else random.choices([1, 2, 3], [0.1, 0.1, 0.8])[0]
        # sb_frac: blok di dalam solid utuh = 1; sekitar seperlima blok berada di batas -> sebagian
        if random.random() < 0.2:
            fr = round(random.uniform(0.1, 0.9), 3)
            n_part += 1
        else:
            fr = 1
        dom = 'WASTE' if ty == 3 else random.choice(['QV_Lensa2', 'QV_Lensa2', 'QV_Splay_HW'])
        w.writerow(r + [p, ns, sor, ke, nh, spasi, ty, fr, dom])

print('OK %s' % OUT)
print('   %d blok, %d di antaranya sebagian (sb_frac < 1) = %.1f%%' % (len(rows), n_part, 100.0 * n_part / max(1, len(rows))))
print('   kolom tambahan: %s' % ', '.join(TAMBAH))
