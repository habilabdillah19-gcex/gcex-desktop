"""Tambah kolom fiktif S_PCT (sulfur, %), ZN_PPM, CU_PPM ke data/SIM_BM_GC.csv untuk latihan Additional flagging
GC-Ex Block Model 0.20.1. Deterministik (seed tetap); aman dijalankan ulang (kolom lama diganti).
Pola: sulfur naik di bawah zona oksida (RL < 290) dan di dalam domain vein; Zn / Cu ikut kadar Au dengan sebaran lognormal."""
import csv, math, os, random
P = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'SIM_BM_GC.csv')
rows = list(csv.reader(open(P, newline='', encoding='utf-8')))
h = [c for c in rows[0] if c not in ('S_PCT', 'ZN_PPM', 'CU_PPM')]
keep = [rows[0].index(c) for c in h]
iz, ia, idm = h.index('Z'), h.index('AU'), h.index('DOMAIN')
rnd = random.Random(20261029)
out = [h + ['S_PCT', 'ZN_PPM', 'CU_PPM']]
for r in rows[1:]:
    r = [r[k] for k in keep]
    z, au, vein = float(r[iz]), float(r[ia]), r[idm] != 'WASTE'
    fresh = 1 / (1 + math.exp((z - 290) / 4))  # 0 di atas 290 (oksida), 1 jauh di bawah (segar)
    s = (0.05 + 0.55 * fresh + (0.55 * fresh if vein else 0)) * math.exp(rnd.gauss(0, 0.35))
    zn = 60 * math.exp(rnd.gauss(0, 0.6)) * (1 + 3.5 * min(au, 4) / 4) * (1 + fresh)
    cu = 40 * math.exp(rnd.gauss(0, 0.6)) * (1 + 4 * min(au, 4) / 4)
    out.append(r + ['%.3f' % s, '%.0f' % zn, '%.0f' % cu])
csv.writer(open(P, 'w', newline='', encoding='utf-8'), lineterminator='\n').writerows(out)
n = len(out) - 1
S = [float(o[-3]) for o in out[1:]]; Z = [float(o[-2]) for o in out[1:]]
print(n, 'blok; S>0.8 %:', sum(v > 0.8 for v in S), '; Zn>500 ppm:', sum(v > 500 for v in Z))
