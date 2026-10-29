"""GC-Ex 0.19: pasang identitas visual bersama (brand.css + brand.js) dan font (Playfair Display, Courier Prime; OFL)
ke hasil build GC-Ex Block Model / Drillhole. Dipanggil PALING AKHIR (sesudah palette_patch) supaya tidak ikut diganti."""
import os
import shutil

W = os.path.dirname(os.path.abspath(__file__)) + '/'
FONTS = ['PlayfairDisplay-wght.ttf', 'PlayfairDisplay-Italic-wght.ttf', 'CourierPrime-Regular.ttf', 'CourierPrime-Bold.ttf',
         'OFL_PlayfairDisplay.txt', 'OFL_CourierPrime.txt']


def apply(s, app, out_html, extra_css=''):
    # 'Penampang (Sayatan) 2D' / 'Penampang 2D' -> 'Sayatan 2D' (menu, tree, petunjuk)
    s = s.replace('Penampang (Sayatan) 2D', 'Sayatan 2D').replace('Penampang 2D', 'Sayatan 2D')
    k = s.rindex('</body>')
    css = extra_css + open(W + 'brand.css', encoding='utf-8').read()
    js = "window.GCEX_APP='%s';\n" % app + open(W + 'brand.js', encoding='utf-8').read()
    s = s[:k] + '<style id="gxBrand">\n' + css + '\n</style>\n<script id="gxBrandJs">\n' + js + '\n</script>\n' + s[k:]
    src = os.path.join(W, '..', 'app-core', 'fonts')
    dst = os.path.join(os.path.dirname(os.path.abspath(out_html)), 'fonts')
    os.makedirs(dst, exist_ok=True)
    for f in FONTS:
        shutil.copy2(os.path.join(src, f), os.path.join(dst, f))
    return s
