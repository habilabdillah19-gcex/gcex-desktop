"""Build GC-Ex Drillhole untuk aplikasi desktop: gcex_dh_base.html + modul desktop -> ../app-dh/index.html

Modul desktop yang disisipkan (sebelum FP.startUI, setelah semua fungsi proyek & pembaca .mdl terdefinisi):
- ../web-src/mdlbig.js : prompt/alert/confirm lewat dialog aplikasi, cegah drop file di luar kotak unggah,
                          block model .mdl besar lewat backend Python (sama dengan GC-Ex Block Model)
- mdlbig_dh.js         : jalur block model besar khusus Drillhole (filter titik tengah E/N/RL, SA.mdlRun)
- ../web-src/guide.js  : panduan langkah (tombol nonaktif & pesan 'belum/dulu')
- ../web-src/desk_skin.css : kulit desktop (3D halus, lebih padat), sesudah tema
- theme_dh.css         : palet terbalik (kuning mayor, biru navy minor)
- ../web-src/bigline.js : pembaca topografi / desain pit jumbo (.str/.dxf/.csv) per potongan, hasil identik
- slabbar_dh.js        : bilah Maju / Mundur mengambang, hanya muncul saat sayatan / Penampang 2D aktif
- ../web-src/ptree.js + ptree_dh.js : Project Tree (pohon proyek urut alur kerja + panel properti)
- deskflush_dh.js      : simpan ke komputer + folder proyek dan lepas kunci sebelum jendela ditutup
- ../web-src/hires.js  : LOD topografi & orthofoto (piramida, resolusi mengikuti zoom, gambar asli di Peta 2D)
- cls_dh.js            : klasifikasi sumber daya (Measured / Indicated / Inferred) di Reporting BM
- env_dh.js            : selubung mineralisasi (envelope / halo) per domain vein, soft boundary di Model Estimation
- aoi_dh.js            : kerangka blok AOI (block model dibuat dari nol / melengkapi cakupan .mdl impor)
- waste_dh.js          : estimasi waste (domain semu WASTE, est_type 3) untuk material di luar seluruh solid
Di browser biasa (tanpa GC-Ex Desktop) modul ini tidak mengubah apa pun.
"""
import os
import shutil
import subprocess
import sys

W = os.path.dirname(os.path.abspath(__file__)) + os.sep
OUT = os.path.join(W, '..', 'app-dh', 'index.html')
SHARED = os.path.join(W, '..', 'web-src') + os.sep

s = open(W + 'gcex_dh_base.html', encoding='utf-8').read()
mods = [SHARED + 'mdlbig.js', SHARED + 'guide.js', SHARED + 'desk_text.js', W + 'mdlbig_dh.js', W + 'deskflush_dh.js', SHARED + 'prj.js', SHARED + 'wm.js']
if shutil.which('node'):
    for m in mods + [SHARED + 'bigline.js', W + 'slabbar_dh.js', SHARED + 'ptree.js', W + 'og_dh.js', W + 'ui4_dh.js', W + 'ptree_dh.js', W + 'env_dh.js', W + 'flt_dh.js', W + 'sl_dh.js', W + 'cls_dh.js', W + 'aoi_dh.js', W + 'waste_dh.js']:
        r = subprocess.run(['node', '--check', m], capture_output=True, text=True)
        assert r.returncode == 0, 'Galat sintaks di ' + m + ':\n' + r.stderr[:800]
    print('Cek sintaks modul: OK')
A = "setTimeout(function(){try{FP.startUI();}catch(e){}},50);\n"
assert s.count(A) == 1, 'titik sisip FP.startUI tidak ditemukan tepat satu kali'
# pembungkus SA.readMDL milik Block Model (format opsi berbeda) dimatikan; Drillhole memakai mdlbig_dh.js
ins = 'SA._mdlBigOn=1;\n' + '\n'.join(open(m, encoding='utf-8').read() for m in mods)
s = s.replace(A, ins + '\n' + A)
# topografi / desain pit jumbo: baca per potongan & sederhanakan per segmen (hasil identik)
sys.path.insert(0, SHARED)
import bigline_patch
s, nb = bigline_patch.patch(s, open(SHARED + 'bigline.js', encoding='utf-8').read())
import ortho_patch
s = ortho_patch.patch(s)
print('Orthofoto latar: OK')
import hires_patch
s = hires_patch.patch(s)
print('LOD topografi & orthofoto (resolusi tinggi): OK')
print('Pembaca garis jumbo tersambung:', nb, 'tempat')
# Geological Modelling v2: tren pitch, pinch-out bor kosong, OK orientasi dinamis
sys.path.insert(0, W)
import gm2_patch
s = gm2_patch.patch(s)
print('GM v2 (tren / pinch-out / OK dinamis): OK')
# integrasi data struktur & pemetaan permukaan (Map) ke pemodelan
import gm3_patch
s = gm3_patch.patch(s)
print('GM v3 (basis data struktur terpadu + Map): OK')
# Peta (Mapping) & Layout terpisah, layer peta terperinci, titik struktur di peta
import ui4_patch
s = ui4_patch.patch(s)
print('UI 0.12 (Mapping / Layout / Sayatan): OK')
# Model Estimation merekam spasi bor & jumlah bor per blok (dipakai klasifikasi sumber daya)
import mecls_patch
s = mecls_patch.patch(s)
print('Spasi bor & jumlah bor per blok di Model Estimation: OK')
# bilah sayatan mengambang (Maju / Mundur): di akhir sumber viewer (dijalankan sesudah viewer terbentuk)
VS = '<script type="text/plain" id="vsrc">'
assert s.count(VS) == 1
vi = s.index(VS); vj = s.index('</script>', vi)
s = s[:vj] + '\n' + '\n'.join(open(f, encoding='utf-8').read() for f in [W + 'slabbar_dh.js', W + 'og_dh.js', W + 'ui4_dh.js', SHARED + 'ptree.js', W + 'ptree_dh.js']) + '\n' + gm2_patch.TAIL + '\n' + gm3_patch.TAIL + '\n' + open(W + 'env_dh.js', encoding='utf-8').read() + '\n' + open(SHARED + 'ui19.js', encoding='utf-8').read() + '\n' + open(W + 'dom20_dh.js', encoding='utf-8').read() + '\n' + open(W + 'flt_dh.js', encoding='utf-8').read() + '\n' + open(W + 'sl_dh.js', encoding='utf-8').read() + '\n' + open(W + 'cls_dh.js', encoding='utf-8').read() + '\n' + open(W + 'aoi_dh.js', encoding='utf-8').read() + '\n' + open(W + 'waste_dh.js', encoding='utf-8').read() + '\n' + s[vj:]
s = s.replace("  if(!DOM.on)b+='<p class=gg-why>&#9432; Belum ada filter dom", "  if(!DOM.on&&!(window.gsDomCodes&&gsDomCodes()))b+='<p class=gg-why>&#9432; Belum ada filter dom")
s = s.replace("Geser posisi dengan tombol <b>Maju / Mundur</b> di bilah atas untuk", "Geser posisi dengan tombol <b>Maju / Mundur</b> di bilah Sayatan (atas tampilan) untuk")
# tema Drillhole (palet terbalik): dipasang sebagai <style> terakhir supaya menimpa gaya bawaan
css = open(W + 'theme_dh.css', encoding='utf-8').read()
assert s.count('</body>') >= 1
k = s.rindex('</body>')
s = s[:k] + '<style id="dhTheme">\n' + css + '\n</style>\n<style id="deskSkin">\n' + open(SHARED + 'desk_skin.css', encoding='utf-8').read() + '\n</style>\n<style id="deskDense">\n' + open(SHARED + 'desk_dense.css', encoding='utf-8').read() + '\n</style>\n' + s[k:]
assert '<script id="plotlyInline">' in s and len(s) > 3_000_000, 'Plotly tertanam tidak ditemukan'
os.makedirs(os.path.dirname(OUT), exist_ok=True)
import nosrc_patch
s = nosrc_patch.patch(s)
print('Tanpa akses kode sumber: OK')
import palette_patch
s, npal = palette_patch.patch(s, earthy=True)
s = palette_patch.layout(s)
print('Palet earthy:', npal, 'tempat')
# 0.21: Sesar 3D (filter batas keras di pencarian sampel, blok di ruang pulih) & ganti nama menu Geological Modelling
for a, b in [('if(d<=1)cand.push([d,L[t]]);', 'if(d<=1&&(!window.OKF||OKF(c)))cand.push([d,L[t]]);'),
             ('var x=it.x-offX,y=it.y-offY,z=it.z,res=null,cbb=dc.cbb;', 'var x=it.x-offX,y=it.y-offY,z=it.z,res=null,cbb=dc.cbb;if(window.fltQ){var _fq=fltQ(x,y,z);x=_fq[0];y=_fq[1];z=_fq[2];}'),
             ('var near=function(x,y,z){', 'var near=function(x,y,z){if(window.fltQ){var _fq=fltQ(x,y,z);x=_fq[0];y=_fq[1];z=_fq[2];}')]:
    assert s.count(a) == 1, 'titik patch sesar: ' + a
    s = s.replace(a, b)
s = s.replace("<h3>Geological Modelling</h3>", "<h3>Geomodeller Vein System Deposit</h3>")
s = s.replace("title='Geological Modelling: domain vein", "title='Geomodeller Vein System Deposit: domain vein")
s = s.replace("Geological<br>Modelling</button>", "Geomodeller<br>Vein</button>")
n_gm = s.count('Geological Modelling')
s = s.replace('Geological Modelling', 'Geomodeller Vein')
print('Menu Geomodeller Vein / Stratified-Laterite / Sesar 3D: OK (' + str(n_gm) + ' teks)')
import brand_build
s = brand_build.apply(s, 'dh', OUT, open(SHARED + 'theme_earthy.css', encoding='utf-8').read() + '\n')
print('Identitas GC-Ex 0.19: OK')
open(OUT, 'w', encoding='utf-8').write(s)
print('OK', OUT, len(s))
