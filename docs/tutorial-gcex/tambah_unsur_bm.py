"""Tambah kolom fiktif S_PCT (sulfur, %), ZN_PPM, CU_PPM ke data block model latihan GC-Ex Block Model.
Dipakai untuk latihan Additional flagging (aturan S_PCT / ZN_PPM), aturan tujuan material berdasarkan sulfida,
dan rekap dig block multi-unsur. Deterministik (seed tetap); aman dijalankan ulang (kolom lama diganti).
Pola: sulfur naik di bawah zona oksida (RL < 290) dan di dalam domain vein; Zn / Cu ikut kadar Au (lognormal).

DUA berkas diproses, keduanya dipakai tutorial:
  data/SIM_BM_GC.csv        (block model untuk estimasi di GC-Ex Drill Hole)
  data/SIM_BM_GC_kadar.csv  (block model berisi kadar, dipakai Tutorial Block Model)
Sebelum 0.24.25 hanya berkas pertama yang diproses, sehingga bab Additional flagging di Tutorial Block Model
memakai aturan S_PCT / ZN_PPM pada berkas yang TIDAK punya kolom itu: tidak ada satu pun dig block yang ter-flag
(notes.json: db1_flag = 0). Itu sebabnya kedua berkas kini ikut."""
import csv, math, os, random

D = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')


def proses(nama, kol_au='AU_GC'):
    P = os.path.join(D, nama)
    if not os.path.exists(P):
        print('  (lewat) %s tidak ada' % nama)
        return None
    rows = list(csv.reader(open(P, newline='', encoding='utf-8-sig')))
    h = [c for c in rows[0] if c not in ('S_PCT', 'ZN_PPM', 'CU_PPM')]
    keep = [rows[0].index(c) for c in h]
    au_kol = kol_au if kol_au in h else ('AU_GC' if 'AU_GC' in h else 'AU')
    iz, ia, idm = h.index('Z'), h.index(au_kol), h.index('DOMAIN')
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
    S = [float(o[-3]) for o in out[1:]]
    Z = [float(o[-2]) for o in out[1:]]
    nS = sum(1 for v in S if v > 0.8)
    nZ = sum(1 for v in Z if v > 500)
    print('OK %-24s %6d blok  S_PCT > 0,8: %5d (%.1f%%)  ZN_PPM > 500: %5d (%.1f%%)'
          % (nama, len(S), nS, 100.0 * nS / len(S), nZ, 100.0 * nZ / len(S)))
    return out


out = proses('SIM_BM_GC.csv')
proses('SIM_BM_GC_kadar.csv', 'AU_GC')
if out is None:
    raise SystemExit('data/SIM_BM_GC.csv tidak ada. Jalankan make_sim_data.py dulu.')
n = len(out) - 1
S = [float(o[-3]) for o in out[1:]]; Z = [float(o[-2]) for o in out[1:]]
print(n, 'blok; S>0.8 %:', sum(v > 0.8 for v in S), '; Zn>500 ppm:', sum(v > 500 for v in Z))
