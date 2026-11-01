"""Cetak tutorial DB-Ex (tutorial.html + gambar/t*.png, q*.png) menjadi docs/DB-Ex_Tutorial_Penggunaan.pdf, dan penjelasan
teknis (docs/PANDUAN_CORE.html, dibuat dari PANDUAN_CORE.md oleh docs/md2html.py) menjadi docs/DB-Ex_Panduan_Teknis.pdf.

Sama dengan Chrome/Edge -> Cetak -> Simpan sebagai PDF (A4 dari @page, grafik latar aktif), memakai Chromium Playwright.
Pemakaian:  python docs/tutorial-core/tutorial_shots.py   (ambil ulang tangkapan layar t*.png, DB-Ex Electron)
            python docs/tutorial-core/tutorial_shots_qt.py (ambil ulang tangkapan layar q*.png, DB-Ex versi Qt)
            python docs/tutorial-core/buat_pdf.py         (cetak PDF)
"""
from pathlib import Path

from playwright.sync_api import sync_playwright

T = Path(__file__).resolve().parent
OUT = T.parents[0] / "DB-Ex_Tutorial_Penggunaan.pdf"
TEK = T.parents[0] / "DB-Ex_Panduan_Teknis.pdf"
PRINT_CSS = """
@page{size:A4;margin:16mm 15mm 18mm}
body{background:#fff;font-size:10pt}
main{max-width:none;padding:0;background:#fff;min-height:0}
h1{display:none}
h2{break-after:avoid;font-size:16pt;margin-top:8mm;padding-bottom:1.5mm;border-bottom:1.5px solid #2a5ea8}
h3{break-after:avoid;font-size:12pt}
table,pre,li{break-inside:avoid}
th,td{padding:4px 6px;font-size:9pt}code{font-size:8.6pt}
.cover{height:255mm;display:flex;flex-direction:column;justify-content:space-between;break-after:page}
.band{background:#141a26;color:#f6f5f1;border-radius:3mm;padding:18mm 12mm 16mm}
.band .k{letter-spacing:.18em;text-transform:uppercase;font-size:9pt;opacity:.8}
.band .t{font:700 34pt Georgia,serif;margin:4mm 0 3mm}.band .t em{color:#9cc0ea;font-style:normal}
.band .l{font-size:11.5pt;opacity:.92;max-width:150mm}
.toc{border:1px solid #c6c4bd;border-radius:3mm;padding:5mm 7mm;columns:2;column-gap:10mm;font-size:9.5pt}
.toc div{break-inside:avoid;margin:.5mm 0}
.meta{font-size:8.5pt;color:#5d6773}
"""


def main() -> None:
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        pg = b.new_page()
        pg.goto((T / "tutorial.html").as_uri(), wait_until="networkidle")
        pg.wait_for_timeout(800)  # font & gambar selesai dimuat
        pg.pdf(path=str(OUT), format="A4", print_background=True, prefer_css_page_size=True)
        print("OK", OUT, f"{OUT.stat().st_size / 1e6:.1f} MB")
        # ---- penjelasan teknis: Panduan DB-Ex + sampul, daftar isi dan nomor halaman
        import json
        ver = json.loads((T.parents[1] / "builder-core.json").read_text(encoding="utf-8"))["extraMetadata"]["version"]
        pg = b.new_page()
        pg.goto((T.parents[0] / "PANDUAN_CORE.html").as_uri(), wait_until="networkidle")
        pg.add_style_tag(content=PRINT_CSS)
        pg.evaluate("""(ver) => {
          const m = document.querySelector('main');
          const toc = [...m.querySelectorAll('h2')].map(h => '<div>' + h.textContent + '</div>').join('');
          const c = document.createElement('section'); c.className = 'cover';
          c.innerHTML = '<div><div class="band"><div class="k">Database Excellence · keluarga GC-Ex</div>' +
            '<div class="t">Penjelasan Teknis DB<em>-Ex</em></div><div class="l">Cara kerja, alur data, format impor / ekspor, ' +
            'AI lokal, ruang kerja Core box, Singkapan dan Borang, batasan dan masalah umum. Pendamping Tutorial DB-Ex.</div></div></div>' +
            '<div class="toc"><b style="display:block;column-span:all;margin-bottom:1.5mm">Isi</b>' + toc + '</div>' +
            '<div class="meta">DB-Ex ' + ver + ' · Contoh data di dokumen ini fiktif.<br>Copyright © Habil Abdillah 2026. Seluruh hak dilindungi.</div>';
          m.prepend(c);
        }""", ver)
        pg.wait_for_timeout(300)
        foot = ('<div style="font:8px Segoe UI,Arial,sans-serif;color:#5d6773;width:100%;padding:0 15mm;display:flex;'
                'justify-content:space-between"><span>Penjelasan Teknis DB-Ex ' + ver + '</span>'
                '<span><span class="pageNumber"></span> / <span class="totalPages"></span></span></div>')
        pg.pdf(path=str(TEK), format="A4", print_background=True, prefer_css_page_size=True, display_header_footer=True,
               header_template="<div></div>", footer_template=foot)
        print("OK", TEK, f"{TEK.stat().st_size / 1e6:.1f} MB")
        b.close()


if __name__ == "__main__":
    main()
