# -*- coding: utf-8 -*-
"""Kerangka dokumen PDF keluarga GC-Ex (gaya sama dengan dokumen DB-Ex).

Dipakai bersama oleh:
  build_tutorial_update.py   -> docs/GCEx_Tutorial_Update.pdf
  build_petunjuk_teknis.py   -> docs/GCEx_Petunjuk_Teknis.pdf

Keduanya TIDAK memakai tangkapan layar aplikasi, jadi dapat dibangun di mesin mana pun
(termasuk runner CI) tanpa menjalankan GC-Ex. Gambar dihitung dari model & data latihan.
"""
import datetime
import html
import os

from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
TUT = os.path.abspath(os.path.join(HERE, '..'))
DOCS = os.path.abspath(os.path.join(TUT, '..'))

INK, ACC, ACC2, MUT = '#1b2a3a', '#1f4e8c', '#c98a16', '#6b7682'
NAVY = '#232f45'

CSS = """
@page { size: A4; margin: 17mm 15mm 15mm 15mm; }
body { font-family: 'Segoe UI', Arial, sans-serif; color: #1b2a3a; font-size: 10pt; line-height: 1.52; }
h1 { font-family: Georgia, 'Times New Roman', serif; font-size: 27pt; margin: 0 0 3mm; font-weight: 700; letter-spacing: -.3pt; }
h1 .x { color: #7fa6d9; font-style: italic; }
h2 { font-size: 13.5pt; color: #1f4e8c; border-bottom: 1.6pt solid #1f4e8c; padding-bottom: 1.2mm;
     margin: 9mm 0 3mm; page-break-after: avoid; }
h3 { font-size: 11pt; margin: 5mm 0 1.5mm; page-break-after: avoid; color: #27405e; }
p { margin: 0 0 2.6mm; text-align: justify; }
ul, ol { margin: 0 0 2.6mm; padding-left: 6mm; }
li { margin: 0 0 1.2mm; }
figure { margin: 4mm 0; page-break-inside: avoid; }
figure img { width: 100%; border: .5pt solid #d6dde6; }
figcaption { font-size: 8pt; color: #6b7682; margin-top: 1.2mm; }
table { border-collapse: collapse; width: 100%; font-size: 8.7pt; margin: 3mm 0; page-break-inside: avoid; }
th, td { border: .5pt solid #d6dde6; padding: 1.5mm 2mm; text-align: left; vertical-align: top; }
th { background: #eef2f7; color: #1f4e8c; font-weight: 600; }
code { background: #f3f6f9; padding: 0 1mm; font-family: Consolas, monospace; font-size: 8.8pt; }
.box  { border-left: 3pt solid #1f4e8c; background: #f7f9fb; padding: 2.6mm 3mm; margin: 3mm 0; }
.warn { border-left: 3pt solid #c98a16; background: #fdf8ee; padding: 2.6mm 3mm; margin: 3mm 0; }
.stop { border-left: 3pt solid #b42318; background: #fdf3f2; padding: 2.6mm 3mm; margin: 3mm 0; }
.page { page-break-after: always; }
small { color: #6b7682; }

/* ---------- sampul ---------- */
.cover { padding-top: 6mm; }
.cv { background: #232f45; color: #fff; border-radius: 3mm; padding: 11mm 11mm 12mm; }
.cv .kic { font-size: 8pt; letter-spacing: 2.2pt; color: #9fb6d4; text-transform: uppercase; margin-bottom: 5mm; }
.cv h1 { color: #fff; }
.cv p { color: #d7e0ec; font-size: 10.5pt; margin: 3mm 0 0; text-align: left; }
.isi { border: .6pt solid #d6dde6; border-radius: 2mm; padding: 5mm 6mm; margin-top: 7mm; font-size: 9.4pt; }
.isi b { display: block; margin-bottom: 2.5mm; color: #1f4e8c; }
.isi .kol { column-count: 2; column-gap: 9mm; }
.isi div.i { break-inside: avoid; margin: 0 0 1.4mm; }
.ftr { margin-top: 9mm; font-size: 8pt; color: #6b7682; line-height: 1.45; }
"""

e = html.escape
num = lambda v: format(int(v), ',d').replace(',', '.')


def cover(kicker, judul, judul_x, ringkas, isi, footer):
    """Sampul bergaya DB-Ex: panel navy + daftar isi dua kolom + catatan kaki."""
    li = ''.join('<div class=i>%s</div>' % x for x in isi)
    return ('<div class="cover page"><div class=cv><div class=kic>%s</div>'
            '<h1>%s<span class=x>%s</span></h1><p>%s</p></div>'
            '<div class=isi><b>Isi</b><div class=kol>%s</div></div>'
            '<div class=ftr>%s</div></div>' % (kicker, judul, judul_x, ringkas, li, footer))


def tabel(head, rows):
    h = '<tr>' + ''.join('<th>%s</th>' % c for c in head) + '</tr>'
    b = ''.join('<tr>' + ''.join('<td>%s</td>' % c for c in r) + '</tr>' for r in rows)
    return '<table>%s%s</table>' % (h, b)


def steps(*items):
    return '<ol>' + ''.join('<li>%s</li>' % i for i in items) + '</ol>'


def bullets(*items):
    return '<ul>' + ''.join('<li>%s</li>' % i for i in items) + '</ul>'


class Fig:
    """Penomoran gambar otomatis."""

    def __init__(self, figdir):
        self.n = 0
        self.dir = os.path.basename(figdir)

    def __call__(self, nama_berkas, caption):
        self.n += 1
        return ('<figure><img src="%s/%s"><figcaption><b>Gambar %d.</b> %s</figcaption></figure>'
                % (self.dir, nama_berkas, self.n, caption))


def render(blocks, pdf_path, footer_text):
    """Susun HTML lalu cetak ke PDF A4 dengan nomor halaman."""
    htm = ('<html><head><meta charset="utf-8"><style>%s</style></head><body>%s</body></html>'
           % (CSS, '\n'.join(blocks)))
    tmp = os.path.join(HERE, '_%s.html' % os.path.basename(pdf_path).replace('.pdf', ''))
    open(tmp, 'w', encoding='utf-8').write(htm)
    with sync_playwright() as pw:
        b = pw.chromium.launch(args=['--disable-dev-shm-usage'])
        pg = b.new_page()
        pg.goto('file://' + tmp)
        pg.wait_for_timeout(700)
        pg.pdf(path=pdf_path, format='A4', print_background=True,
               margin={'top': '0', 'bottom': '0', 'left': '0', 'right': '0'},
               display_header_footer=True, header_template='<div></div>',
               footer_template='<div style="font-size:7pt;color:#6b7682;width:100%;text-align:center;'
                               'font-family:Arial">' + html.escape(footer_text) +
                               ' &middot; halaman <span class="pageNumber"></span> / '
                               '<span class="totalPages"></span></div>')
        b.close()
    os.remove(tmp)
    return os.path.getsize(pdf_path)


def versi():
    """Versi aplikasi dari package.json (Block Model) & builder-dh.json (Drill Hole)."""
    import json
    root = os.path.abspath(os.path.join(DOCS, '..'))
    bm = json.load(open(os.path.join(root, 'package.json'), encoding='utf-8'))['version']
    dh = json.load(open(os.path.join(root, 'builder-dh.json'), encoding='utf-8'))['extraMetadata']['version']
    return bm, dh


def tanggal():
    return datetime.datetime.now().strftime('%d %B %Y')
