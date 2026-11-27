# -*- coding: utf-8 -*-
"""Bangun docs/geo-pocket/Tentang_Geo_Pocket.pdf (tangkapan layar dari data latihan fiktif docs/tutorial-ow/data).
Pakai: python web-src-gp/bangun_gp.py && python docs/geo-pocket/buat_tentang_gp.py   (perlu Playwright + Chromium, Node)"""
import asyncio, datetime, html, json, os, subprocess, sys
from pathlib import Path
from playwright.async_api import async_playwright
H = Path(__file__).resolve().parent; R = H.parent.parent; G = H / 'gambar'; G.mkdir(exist_ok=True)
APP = (H / 'Geo_Pocket.html').as_uri(); D = R / 'docs' / 'tutorial-ow' / 'data'
CHROME = os.environ.get('CHROME') or ('/usr/bin/google-chrome' if os.path.exists('/usr/bin/google-chrome') else None)
ARGS = ['--no-sandbox', '--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist']
FMT = json.loads(subprocess.run(['node', '-e', "global.Delaunator=function(){};const G=require('./web-src-gp/core.js');require('./web-src-gp/geo2.js');console.log(JSON.stringify(G.FORMATS))"], cwd=R, capture_output=True, text=True, check=True).stdout)
TGL = datetime.date.today().strftime('%d %B %Y').replace('November', 'November')
KB = round((H / 'Geo_Pocket.html').stat().st_size / 1024)

async def shots(p):
    b = await p.chromium.launch(executable_path=CHROME, headless=True, args=ARGS)
    pg = await b.new_page(viewport={'width': 1360, 'height': 800}, device_scale_factor=1.5)
    await pg.goto(APP)
    await pg.set_input_files('#fin', [str(D / 'LTH_topografi.str'), str(D / 'LTH_pemetaan.dxf')])
    await pg.wait_for_function("__GC.S.geoms.length>5"); await pg.wait_for_timeout(300)
    await pg.evaluate("""(()=>{const S=__GC.S,GC=__GC.GC,M2=__GC.M2,topo=S.geoms.find(g=>/topografi/.test(g.name));
      const tin=GC.buildTIN([topo],{step:2,factor:8}),dem=GC.tinToDEM(tin,0.5),g=GC.mk({name:'DEM topografi',src:'dem'});g.dem=dem;
      const c=document.createElement('canvas');c.width=dem.nx;c.height=dem.ny;c.getContext('2d').putImageData(new ImageData(GC.demRGBA(dem,{}),dem.nx,dem.ny),0,0);dem.cv=c;dem.mode='hyps';g.base='DEM';g.file='(dari LTH_topografi)';
      const k=GC.contours(dem,2,'Kontur 2 m');k.color='#7A5A3A';M2.sty(k).lw=1;M2.sty(k).fill=0;k.base='Kontur';k.file=g.file;
      const d=GC.mk({name:'Batas blok',src:'digit',meta:{cols:['NAMA','KET']}});d.base='Batas blok';d.color='#C2413B';
      GC.addPoly(d,[[10060,20070,150],[10125,20062,152],[10140,20120,155],[10085,20140,154],[10052,20110,151]],true,['Blok A','rencana gali']);
      GC.addPoly(d,[[10140,20120,155],[10125,20062,152],[10175,20070,153],[10180,20125,156]],true,['Blok B','cadangan']);M2.sty(d).label=0;M2.sty(d).fill=0.25;M2.sty(d).lw=2;
      const F=(n,p)=>{const f={id:900+S.folders.length,name:n,parent:p||null,open:true};S.folders.push(f);return f;};
      const f1=F('Topografi'),f2=F('Pemetaan geologi'),f3=F('Desain & batas'),dx=S.folders.find(f=>/dxf/.test(f.name));dx.parent=f2.id;dx.name='Pick-up 26 Nov (DXF)';dx.open=false;
      topo.fold=f1.id;g.fold=f1.id;k.fold=f1.id;d.fold=f3.id;topo.visible=false;
      S.geoms=[d].concat(S.geoms.filter(x=>x.fold===dx.id||S.folders.some(q=>q.id===x.fold&&q.parent===f2.id)),[k,topo,g]);
      __GC.select(d.id);S.selF={g:d,type:'pl',i:0};__GC.select(d.id,true);M2.fit();})()""")
    await pg.wait_for_timeout(600); await pg.screenshot(path=str(G / 'peta.png'))
    await pg.evaluate("__GC.S.view='pl';__GC.showTab('tbl')"); await pg.wait_for_timeout(300); await pg.screenshot(path=str(G / 'tabel.png'), clip={'x': 268 * 1.0, 'y': 28, 'width': 824, 'height': 150})
    await pg.evaluate("__GC.showTab('2d');__GC.LY.paper='A4';__GC.LY.title='PETA RENCANA BLOK GALI';__GC.LY.sub='Data latihan fiktif';__GC.LY.by='Geologi';__GC.LY.no='GP-001';__GC.dlgLayout()")
    await pg.wait_for_timeout(1500); await pg.screenshot(path=str(G / 'layout.png'))
    await pg.click('.modal [data-close]'); await pg.evaluate("__GC.C.soft='Surpac';__GC.C.fmt='dtm';__GC.showTab('conv')"); await pg.wait_for_timeout(300); await pg.screenshot(path=str(G / 'konversi.png'))
    await b.close()

def tabel_format():
    r = ''.join('<tr><td><b>%s</b></td><td>%s</td><td class="c">%s</td><td class="c">%s</td><td>%s</td></tr>' % (html.escape(f['label']), html.escape(f['soft']), '✓' if f['r'] else '–', '✓' if f['w'] else '–', html.escape(f['note'])) for f in FMT)
    r += '<tr><td><b>GeoTIFF ortofoto (.tif)</b></td><td>Global Mapper · drone</td><td class="c">✓</td><td class="c">–</td><td>RGB/RGBA; LZW, Deflate, JPEG; overview; detail dibaca sesuai zoom</td></tr>'
    r += '<tr><td><b>JPG / PNG + world file</b></td><td>Umum</td><td class="c">✓</td><td class="c">–</td><td>.jgw / .pgw / .wld</td></tr>'
    return '<table class="t"><tr><th>Format</th><th>Software</th><th>Baca</th><th>Tulis</th><th>Catatan</th></tr>' + r + '</table>'

CSS = """@page{size:A4;margin:16mm 15mm 16mm}*{box-sizing:border-box}body{font:10pt/1.5 Inter,"Segoe UI",Arial,sans-serif;color:#1F2430;margin:0}
h1{font-size:26pt;margin:0;letter-spacing:.01em}h2{font-size:13pt;margin:16pt 0 5pt;color:#1C2733;border-bottom:1.5pt solid #17806B;padding-bottom:2pt;break-after:avoid}h3{font-size:10.5pt;margin:9pt 0 2pt;break-after:avoid}
p{margin:0 0 6pt}ul{margin:0 0 6pt;padding-left:14pt}li{margin-bottom:2pt}.cov{background:#1C2733;color:#ECE9E1;padding:18pt 18pt 14pt;border-radius:2pt}.cov .tag{display:inline-block;background:#17806B;color:#fff;font-weight:700;padding:1pt 6pt;border-radius:2pt;font-size:9pt;margin-bottom:6pt}
.cov p{color:#C9CED6;margin-top:6pt}.meta{display:flex;gap:18pt;margin-top:10pt;font-size:8.5pt;color:#C9CED6}.meta b{color:#fff;display:block;font-size:10pt}
img{width:100%;border:.6pt solid #D3CDC1;border-radius:2pt}figure{margin:8pt 0;break-inside:avoid}figcaption{font-size:8.5pt;color:#5C6672;margin-top:2pt}
.g2{display:grid;grid-template-columns:1fr 1fr;gap:10pt}.k{background:#F7F5F0;border:.6pt solid #D3CDC1;border-radius:2pt;padding:7pt 9pt;break-inside:avoid}.k b{color:#17806B}
table.t{border-collapse:collapse;width:100%;font-size:8.3pt}table.t th{background:#EDEBE6;text-align:left;padding:3pt 5pt;border-bottom:.8pt solid #D3CDC1}table.t td{padding:2.5pt 5pt;border-bottom:.5pt solid #E6E2D8;vertical-align:top}table.t .c{text-align:center}tr{break-inside:avoid}
.note{font-size:8.5pt;color:#5C6672}.w{border-left:2.5pt solid #B5893E;background:#FBF7EC;padding:5pt 9pt;margin:6pt 0;break-inside:avoid}"""
def halaman():
    im = lambda n, c: '<figure><img src="%s"><figcaption>%s</figcaption></figure>' % ((G / n).as_uri(), c)
    return f"""<!DOCTYPE html><html lang="id"><head><meta charset="utf-8"><style>{CSS}</style></head><body>
<div class="cov"><span class="tag">GP</span><h1>Geo Pocket</h1><p>Peta 2D, digitasi, luas, layout peta, dan konverter data geologi &amp; tambang dalam satu berkas HTML yang berjalan tanpa internet.</p>
<div class="meta"><div><b>Tentang aplikasi</b>{TGL}</div><div><b>Bentuk</b>satu berkas HTML, ±{KB} KB</div><div><b>Keluarga</b>GC-Ex · Ore Works · Pit Studio</div><div><b>Nama lama</b>GeoConv</div></div></div>
<h2>Apa itu Geo Pocket</h2>
<p>Geo Pocket adalah alat kerja harian untuk geolog dan surveyor tambang: membuka pick-up dan poligon dari berbagai software pada satu peta, mendigit batas, menghitung luas, menyusun layout peta, dan mengubah format file antar-software. Cukup buka <b>Geo_Pocket.html</b> di browser (Chrome / Edge); tidak ada instalasi, tidak ada data yang dikirim ke server.</p>
<p>Tata letaknya mengikuti Ore Works: bar menu, <b>Project Tree</b> di kiri, tab dokumen di tengah (Peta 2D, 3D, Tabel atribut, Konversi), panel <b>Properti</b> di kanan, dan status bar berisi koordinat.</p>
{im('peta.png', 'Peta 2D: Project Tree berfolder dan subfolder, DEM hasil triangulasi string topografi, kontur 2 m, dan dua poligon digitasi beserta luasnya di panel Properti. Data latihan fiktif.')}
<h2>Kemampuan utama</h2>
<div class="g2">
<div class="k"><b>Peta 2D bertumpuk</b><br>DXF, SHP, TAB MapInfo, MIF/MID, KML/KMZ, GeoJSON, STR, DTM, MSH, CSV, dan GeoTIFF ditampilkan bersama. Urutan gambar = urutan pohon; seret untuk mengubah.</div>
<div class="k"><b>Project Tree berfolder</b><br>Lapisan dikelompokkan ke folder dan subfolder. File berlapis banyak (mis. DXF) otomatis masuk satu folder. Centang folder = tampil/sembunyi semua isinya; isi folder bisa diekspor sekaligus.</div>
<div class="k"><b>Digitasi &amp; edit</b><br>Poligon, garis, titik; snap ke vertex terdekat; elevasi diambil dari DEM; seret, sisip, hapus vertex; urungkan (Ctrl+Z).</div>
<div class="k"><b>Luas</b><br>Luas dan keliling tampil saat mendigit, per fitur (m² dan ha), total per lapisan, dan tabel luas yang bisa diunduh CSV. Ikut tertulis ke SHP dan MIF.</div>
<div class="k"><b>GeoTIFF &amp; DEM</b><br>Ortofoto dibaca bertingkat sesuai zoom. Topografi dari string atau DXF dijadikan TIN lalu DEM, lengkap dengan kontur.</div>
<div class="k"><b>Georeferensi gambar</b><br>Peta pindaian, tangkapan layar, atau foto tanpa koordinat diberi titik kontrol (2 titik atau afin 3+ titik dengan residu dan RMS), tampil di peta, dan diunduh sebagai GeoTIFF atau world file.</div>
<div class="k"><b>Layout peta</b><br>A4 sampai A1, skala otomatis atau pilihan, grid koordinat berlabel, arah utara, batang skala, legenda, blok judul. Unduh PDF atau PNG.</div>
<div class="k"><b>Konversi format</b><br>Pilih software tujuan (Leapfrog, Surpac, MapInfo, Global Mapper, Google Earth) dan format yang disarankan muncul. Banyak file dikemas ZIP.</div>
<div class="k"><b>Sistem koordinat</b><br>UTM WGS84 zona 1–60 U/S (bawaan 50S). Data lintang/bujur diproyeksikan otomatis; status bar menampilkan E/N dan lintang/bujur.</div>
</div>
{im('tabel.png', 'Tabel atribut: panjang dan luas tiap poligon, dengan total luas.')}
{im('layout.png', 'Layout peta: pratinjau halaman dengan grid, skala, legenda, dan blok informasi.')}
{im('konversi.png', 'Tab Konversi: sumber, tujuan (di sini Surpac DTM + STR), dan opsi.')}
<h2>Format yang didukung</h2>{tabel_format()}
<p class="note">Berkas berpasangan dipilih bersamaan: SHP + DBF, MIF + MID, TAB + DAT + MAP + ID, DTM + STR, gambar + world file.</p>
<h2>Cara kerja</h2>
<ul><li><b>Satu berkas HTML</b> dirakit dari modul sumber di <code>web-src-gp/</code> oleh <code>bangun_gp.py</code>: <code>core.js</code> (pembaca/penulis format), <code>geo2.js</code> (UTM, KML/GeoJSON, TIN, DEM, kontur, GeoTIFF, PDF), <code>map2d.js</code> (peta kanvas, digitasi), <code>view3d.js</code> (WebGL), <code>ui.js</code>.</li>
<li><b>Tanpa server dan tanpa internet.</b> File dibaca langsung oleh browser di komputer pengguna; hasil diunduh sebagai file biasa.</li>
<li><b>Memakai ulang kode keluarga GC-Ex:</b> pembaca MSH, STR/DTM Surpac (teks dan biner), DXF BLOCK/INSERT, aturan TIN (string dirapatkan 2 m, titik &lt; 1 mm disatukan, segitiga tepi lebih panjang dari 8 × median dibuang), dan palet antarmuka.</li>
<li><b>Pustaka pihak ketiga</b> (sudah ada di repo): geotiff.js 2.1.3 (lisensi MIT) dan Delaunator (lisensi ISC).</li></ul>
<h2>Pengujian</h2>
<ul><li>Hasil tulis diperiksa dengan pembaca independen: ezdxf (DXF), GDAL (SHP, MIF, TAB, KML, KMZ, GeoJSON), trimesh (OBJ, STL, PLY), rasterio (GeoTIFF DEM dan citra hasil georeferensi, ASC), pyproj (UTM), pdfinfo (PDF).</li>
<li>MSH yang ditulis ulang sama persis byte demi byte dengan aslinya; koordinat DXF, OBJ, STL ASCII, PLY, DTM identik sampai 3 desimal.</li>
<li>Konversi UTM ↔ lintang/bujur selisih di bawah 0,001 mm terhadap pyproj. Luas poligon digitasi sama dengan luas yang dihitung GDAL dari hasil ekspor.</li>
<li>Uji otomatis di repo: <code>node web-src-gp/uji/uji_inti.js</code>, <code>uji_geo.js</code>, <code>uji_tab.js</code>, <code>uji_georef.js</code>; uji antarmuka di Chrome tanpa galat JavaScript.</li></ul>
<div class="w"><b>Belum diuji:</b> membuka hasil ekspor langsung di Leapfrog, Surpac, MapInfo, Global Mapper, dan Google Earth, serta data lapangan asli (ortofoto dan pick-up nyata). Semua uji memakai data latihan fiktif.</div>
<h2>Batas yang perlu diketahui</h2>
<ul><li>ECW dan MrSID tidak dibuka (format tertutup); konversi dulu ke GeoTIFF.</li><li>MapInfo TAB dibaca (titik, garis, poligon, multipoint, atribut), tetapi belum ditulis; untuk mengirim ke MapInfo pakai MIF/MID atau SHP. Objek teks, busur, dan elips dilewati. TAB yang menaut ke Excel (Type XLS) hanya dimuat geometrinya.</li>
<li>Proyek belum bisa disimpan: lapisan, folder, dan digitasi hilang saat browser ditutup. Ekspor hasil digitasi sebelum menutup.</li>
<li>STL biner memakai float32, presisi koordinat UTM turun sampai ±1 m; pakai STL ASCII.</li><li>DEM dari GeoTIFF di atas 3.000 piksel dicuplik; GeoTIFF lintang/bujur tidak diproyeksikan ulang.</li><li>Luas adalah luas planimetrik (tampak atas) pada bidang proyeksi.</li></ul>
<h2>Riwayat</h2>
<table class="t"><tr><th style="width:22%">Tanggal</th><th>Perubahan</th></tr>
<tr><td>26 Nov 2026</td><td><b>GeoConv</b>: konverter MSH, OBJ, STL, PLY, DXF, STR, DTM, SHP, MIF/MID, CSV dengan pratinjau 3D.</td></tr>
<tr><td>26 Nov 2026</td><td>Peta 2D ala Global Mapper: digitasi, luas, GeoTIFF, topo → DEM, kontur, layout peta, KML/KMZ/GeoJSON, sistem koordinat UTM.</td></tr>
<tr><td>27 Nov 2026</td><td>Berganti nama menjadi <b>Geo Pocket</b>. Project Tree berfolder dan subfolder. Sumber masuk repo (<code>web-src-gp/</code>).</td></tr>
<tr><td>27 Nov 2026</td><td>MapInfo TAB native dibaca langsung: geometri dari .MAP/.ID, atribut dari .DAT (Float, Integer, tanggal biner sesuai definisi .TAB), proyeksi UTM dari header. Kolom koordinat <code>UTM_mE</code> / <code>UTM_mN</code> dikenali. Zoom semua mengabaikan titik nyasar di (0, 0).</td></tr>
<tr><td>27 Nov 2026</td><td>Georeferensi gambar ala Ore Works: titik kontrol di gambar, koordinat diketik atau diambil dari peta, hasil sebagai lapisan citra, GeoTIFF (RGB/RGBA, Deflate), atau world file.</td></tr></table>
<p class="note" style="margin-top:14pt">© Copyright Habil Abdillah 2026. Leapfrog, Surpac, MapInfo, Global Mapper, dan Google Earth adalah merek pemiliknya masing-masing; Geo Pocket tidak berafiliasi dengan mereka. Tangkapan layar memakai data latihan fiktif.</p>
</body></html>"""

async def main():
    async with async_playwright() as p:
        await shots(p)
        b = await p.chromium.launch(executable_path=CHROME, headless=True, args=['--no-sandbox'])
        pg = await b.new_page(); tmp = H / '_tentang.html'; tmp.write_text(halaman(), encoding='utf-8'); await pg.goto(tmp.as_uri()); await pg.wait_for_timeout(500)
        out = H / 'Tentang_Geo_Pocket.pdf'
        await pg.pdf(path=str(out), format='A4', print_background=True, prefer_css_page_size=True, display_header_footer=True, header_template='<span></span>',
                     footer_template='<div style="font:7pt sans-serif;color:#888;width:100%;text-align:center">Tentang Geo Pocket · halaman <span class="pageNumber"></span> / <span class="totalPages"></span></div>')
        await b.close(); tmp.unlink(); print(out, out.stat().st_size)
asyncio.run(main())
