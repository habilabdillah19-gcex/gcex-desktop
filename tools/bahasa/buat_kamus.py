# -*- coding: utf-8 -*-
"""Bangun web-src/bahasa_kamus.js dari web-src/bahasa/kamus.tsv (pemilih bahasa GC-Ex, BM 0.24.111 / DH 0.24.113).

Kolom TSV: Indonesia, English (UK), Español, Basa Sunda. English (US) diturunkan dari kolom UK dengan ejaan Amerika.
Pakai: python tools/bahasa/buat_kamus.py   (dipanggil juga otomatis oleh web-src/build.py dan web-src-dh/build_dh.py)
"""
import json, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(ROOT, 'web-src', 'bahasa', 'kamus.tsv')
OUT = os.path.join(ROOT, 'web-src', 'bahasa_kamus.js')

US = [('colour', 'color'), ('Colour', 'Color'), ('centre', 'center'), ('Centre', 'Center'), ('metres', 'meters'), ('metre', 'meter'),
      ('ising', 'izing'), ('ised', 'ized'), ('isation', 'ization'), ('ise ', 'ize '), ('ise)', 'ize)'), ('Minimise', 'Minimize'),
      ('odelling', 'odeling'), ('sulphide', 'sulfide'), ('grey', 'gray'), ('Grey', 'Gray'), ('analyse', 'analyze')]
KECUALI = ('Precise', 'precise', 'otherwise', 'Otherwise', 'raised', 'Raised', 'promise', 'exercise', 'surprise', 'advise', 'revise', 'Revise', 'revised')


def ke_us(t):
    if any(k in t for k in KECUALI):
        return t
    for a, b in US:
        t = t.replace(a, b)
    if t.endswith('ise'):
        t = t[:-3] + 'ize'
    return t


def bangun():
    K = {}
    for ln in open(SRC, encoding='utf-8'):
        ln = ln.rstrip('\n')
        if not ln.strip() or (ln.startswith('#') and '\t' not in ln):   # komentar; '# berkas<TAB>…' = pola angka
            continue
        c = ln.split('\t')
        if len(c) != 4 or not all(x.strip() for x in c):
            raise SystemExit('kamus.tsv: baris tidak lengkap: %r' % ln)
        K[c[0]] = [c[1], ke_us(c[1]), c[2], c[3]]
    js = ('/* DIBUAT OTOMATIS oleh tools/bahasa/buat_kamus.py dari web-src/bahasa/kamus.tsv - jangan diedit langsung.\n'
          '   Urutan: [English (UK), English (US), Espanol, Basa Sunda] */\n'
          'window.GXLANG_KAMUS = ' + json.dumps(K, ensure_ascii=False, separators=(',', ':')) + ';\n')
    open(OUT, 'w', encoding='utf-8').write(js)
    return len(K)


if __name__ == '__main__':
    print('kamus:', bangun(), 'entri ->', OUT)
