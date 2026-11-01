"""Cetak tutorial DB-Ex (tutorial.html + gambar/t*.png) menjadi docs/DB-Ex_Tutorial_Penggunaan.pdf.

Sama dengan Chrome/Edge -> Cetak -> Simpan sebagai PDF (A4 dari @page, grafik latar aktif), memakai Chromium Playwright.
Pemakaian:  python docs/tutorial-core/tutorial_shots.py   (ambil ulang tangkapan layar)
            python docs/tutorial-core/buat_pdf.py         (cetak PDF)
"""
from pathlib import Path

from playwright.sync_api import sync_playwright

T = Path(__file__).resolve().parent
OUT = T.parents[0] / "DB-Ex_Tutorial_Penggunaan.pdf"


def main() -> None:
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        pg = b.new_page()
        pg.goto((T / "tutorial.html").as_uri(), wait_until="networkidle")
        pg.wait_for_timeout(800)  # font & gambar selesai dimuat
        pg.pdf(path=str(OUT), format="A4", print_background=True, prefer_css_page_size=True)
        b.close()
    print("OK", OUT, f"{OUT.stat().st_size / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
