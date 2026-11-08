import re, sys
import os
W = os.path.dirname(os.path.abspath(__file__)) + '/'
OUT = os.path.join(W, '..', 'app', 'index.html')
s = open(W + 'gcex_base.html', encoding='utf-8').read()

def rep(a, b, cnt=1):
    global s
    n = s.count(a)
    assert n == cnt, (n, a[:120])
    s = s.replace(a, b)

# ---------- 0. perbaikan nama file unduhan ----------
rep("filename:'drillhole_3d'", "filename:'GCEx_'+(String(t||'').replace(/[^A-Za-z0-9_-]+/g,'_').replace(/^_+|_+$/g,'').slice(0,60)||'blockmodel')")
rep("l.download='Drillhole3D_Viewer_Offline_lengkap.html'", "l.download='GCEx_BlockModel_Offline_lengkap.html'")

# ---------- 1. CSS seragam (dari GC-Ex Drillhole Ultimate) ----------
CSS = r"""
/* ===== UI seragam GC-Ex (selaras GC-Ex Drillhole Ultimate) ===== */
#rail{overflow-y:auto;scrollbar-width:thin}
#rail .rsep{height:1px;background:var(--bd);margin:5px 6px;flex:0 0 1px}
#hdStep span{display:inline-flex;align-items:center;padding:0 8px;font-size:12px;font-variant-numeric:tabular-nums;color:var(--toptx);opacity:.85;border-left:1px solid rgba(255,255,255,.18);border-right:1px solid rgba(255,255,255,.18);white-space:nowrap}
#top .tb,#top label.tg,#top .dmWrap,#top button{white-space:nowrap;flex-shrink:0}
#top .brand{min-width:0;flex:0 1 auto;overflow:hidden}
#top .brand>div{min-width:0;overflow:hidden}
#top .brand b,#top .brand small{white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
#top{gap:10px}
#lyrBtn{padding:6px 8px}#lyrBtn svg{width:18px;height:18px}
#lyrBtn.on{background:rgba(255,255,255,.22);border-color:#f0c047}
#lyrMenu{flex:0 0 250px;width:250px;flex-direction:column;background:var(--sf,#fff);color:var(--tx,#1c2733);border-left:1px solid var(--bd,#d5dbe3);min-height:0;font-size:13px}
#lyrMenu.mini{flex:0 0 30px;width:30px}
.lyrb{flex:1;overflow-y:auto;padding:0 12px 12px}
.lyrh{display:flex;justify-content:space-between;align-items:center;padding:10px 12px 6px;border-bottom:1px solid var(--bd,#d5dbe3)}
.lyrh .x{margin-left:4px}
.lyrg{font-size:11px;font-weight:700;letter-spacing:.04em;text-transform:uppercase;color:var(--mu,#6b7785);margin:8px 0 2px}
.lyri{display:flex;align-items:center;gap:8px;font-size:13px;padding:3px 0;cursor:pointer}
.lyri.off{opacity:.45;cursor:default}
.lyrp{display:grid;grid-template-columns:1fr 1fr;gap:5px;margin:10px 0 6px}
.lyrp button{font-size:12px;padding:5px 6px}
.lyrstrip{all:unset;box-sizing:border-box;width:100%;height:100%;display:flex;flex-direction:column;align-items:center;gap:8px;padding:10px 0;cursor:pointer;color:var(--mu,#6b7785)}
.lyrstrip:hover{background:rgba(232,89,12,.08);color:var(--tx,#1c2733)}
.lyrsa{font-size:18px;line-height:1}
.lyrsv{writing-mode:vertical-rl;transform:rotate(180deg);font-size:11px;font-weight:700;letter-spacing:.12em}
.lyrsn{font-size:10px}
.uitabs{position:sticky;top:-1px;z-index:5;display:flex;flex-wrap:wrap;gap:3px;margin:10px -2px 6px;padding:6px 2px;background:var(--sf,#fff);border-bottom:2px solid rgba(128,128,128,.25)}
.uitabs button{flex:1 1 auto;padding:5px 6px;font-size:12px;white-space:nowrap}
.uitabs button.on{background:var(--pr,#1f3a5f);color:var(--sf,#fff);border-color:var(--pr,#1f3a5f)}
.uisec.dock{border-left:3px solid var(--pr,#1f3a5f);padding-left:8px;margin-left:-2px}
.uisec.dock>h4:first-child,.uisec.dock>div:first-child>h4:first-child{margin-top:2px}
.uisec .uitabs{position:static;margin:4px 0 6px;padding:0 0 5px;border-bottom:1px dashed rgba(128,128,128,.35)}
.uisec .uitabs button{font-size:11.5px;padding:3px 5px}
.uisec .uisec.dock{border-left:2px solid var(--ac);padding-left:6px}
#side h4.lyhead{margin:14px -2px 6px;font-size:12.5px;text-transform:none;letter-spacing:.3px;color:var(--pr)}
.uisec.dock>h4.lyhead:first-child{margin-top:2px}
#mdList,#ptList,#stList{max-height:220px;overflow-y:auto;overscroll-behavior:contain}
#bxBody .bxcl{max-height:260px;overflow-y:auto;overscroll-behavior:contain}

/* ===== As-Mined v2: register poligon ===== */
#amBody .amflow{font-size:11px;line-height:1.5;color:var(--mu);background:var(--sf2);border:1px solid var(--bd);border-radius:6px;padding:5px 7px}
#amBody .amflow b{color:var(--pr);font-weight:600}
#amBody details.amdet{border:1px solid var(--bd);border-radius:6px;padding:4px 8px;margin-top:6px}
#amBody details.amdet>summary{cursor:pointer;font-weight:600;font-size:12px;color:var(--pr);padding:2px 0}
#amBody table.amcls input,#amBody table.amdst input{width:100%;height:24px!important;padding:1px 3px!important;font-size:11.5px!important;min-width:0}
#amBody table.amcls input[type=color]{padding:0!important;height:22px!important}
#amBody i.amsw{display:inline-flex;align-items:center;justify-content:center;min-width:20px;height:16px;border-radius:3px;font:700 10px/1 Arial;color:#fff;text-shadow:0 0 2px rgba(0,0,0,.6);font-style:normal;margin-right:5px;flex:0 0 auto}
#amBody .ampl code{font-size:11px;word-break:break-all}
#amBody .ampl.new{background:rgba(232,89,12,.08);border-radius:4px}
#amBody input.amblk{width:46px;height:20px!important;padding:0 3px!important;font-size:11px!important;display:inline-block}
#amBody .amflt{margin:8px 0 3px;padding:4px 6px;border-radius:5px;background:var(--sf2);font-size:12px}
#amBody .amflt.on{background:var(--prs)}
#amBody .amflt a{font-size:11px;margin-left:6px}
#amBody .amreg{display:flex;flex-direction:column;gap:3px}
#amBody .amr{border:1px solid var(--bd);border-radius:6px;padding:4px 6px}
#amBody .amr.off{opacity:.5}
#amBody .amr.dup{border-color:var(--dn)}
#amBody .amr.open{border-color:var(--pr);box-shadow:0 0 0 1px var(--pr) inset}
#amBody .amrh{display:flex;align-items:center;gap:4px}
#amBody .amrh code{flex:1;min-width:0;font-size:11px;font-weight:700;cursor:pointer;word-break:break-all;line-height:1.25}
#amBody .amed select,#amBody .amed input{min-width:0;width:100%}
#amBody .amrh button.ed{height:20px;width:22px;padding:0;color:var(--pr)}
#amBody .amrs{font-size:11px;color:var(--mu);margin-left:22px}
#amBody .amed{margin-top:6px;border-top:1px dashed var(--bd);padding-top:5px}
#amBody .amed .g3,#amBody .amed .g2{margin-bottom:3px}
#amBody table.amkv{margin-top:5px}
#amBody table.amkv td:nth-child(odd){color:var(--mu)}
#amBody button.dn{color:var(--dn)}
#amBody .amft{font-size:11.5px;padding:4px 2px;text-align:right}
#bxBody .sgz{margin:6px 0;padding:6px 8px;border:1px solid var(--bd);border-radius:6px;background:var(--sf2)}
#bxBody .sgw{font-size:11.5px;color:#8a5a00;background:#fff4d6;border-left:3px solid #f2a900;padding:4px 6px;border-radius:4px;margin-bottom:5px;line-height:1.4}
#dbBody .calcm{margin:6px 0;padding:6px 8px;border:1px solid var(--bd);border-radius:6px;background:var(--sf2)}
#dbBody .calcm select{width:100%}
#amBody .amcm{margin:4px 0 6px;padding:6px 8px;border:1px solid var(--bd);border-radius:6px;background:var(--sf2)}
#amBody .amcm select{width:100%}
#amBody .amstale{font-size:11.5px;color:#8a5a00;background:#fff4d6;border-left:3px solid #f2a900;padding:4px 6px;border-radius:4px;margin-top:6px}
#amBody .amaud{font-size:11px;color:var(--mu);margin-top:6px}
.elbox{margin:6px 0;padding:6px 8px;border:1px solid var(--bd);border-radius:6px;background:var(--sf2)}
.elbox .elh small{color:var(--mu);font-size:10.5px}
.elbox .elck{display:flex;flex-wrap:wrap;gap:2px 10px;margin-top:4px}
.elbox .elck label{font-size:12px;white-space:nowrap}.elbox .elck label small{color:var(--mu);font-size:10px}
.elbox .elck label.elp{font-weight:700}
.elbox .elbt{display:flex;gap:4px;margin-top:4px}.elbox .elbt button{flex:1;height:24px;font-size:11px;padding:0 4px}
.eltx{color:#5b3fa0}
.elsc{overflow-x:auto;max-width:100%}.elsc table{min-width:100%}.elsc td,.elsc th{white-space:nowrap}
tr.elmet td{font-size:11px;color:var(--mu);font-style:italic}
#amBody .amxf{font-size:12px;padding:4px 6px;margin:4px 0;background:var(--sf);border:1px dashed var(--bd);border-radius:4px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
#amBody .amxm{margin-top:6px;font-size:11.5px}
#amBody .amxm .hint{margin-top:3px}
#amBody .amxr{display:flex;flex-wrap:wrap;gap:3px;margin-top:4px;max-height:120px;overflow:auto}
#amBody .amxr span{font:11px Consolas,monospace;background:var(--sf);border:1px solid var(--bd);border-radius:3px;padding:1px 4px}
.bsdlg{position:fixed;inset:0;z-index:9000;background:rgba(10,20,35,.45);display:none;align-items:center;justify-content:center}
.bsdlg .bsbox{background:var(--sf);color:var(--tx);border-radius:10px;box-shadow:0 10px 40px rgba(0,0,0,.35);width:min(1100px,94vw);max-height:88vh;display:flex;flex-direction:column;padding:12px 14px;overflow:hidden}
.bsdlg .bsh{display:flex;align-items:center;gap:10px}.bsdlg .bsh span{color:var(--mu);font-size:12px;flex:1}.bsdlg .bsh .x{width:30px;height:30px}
.bsdlg .bsp{display:flex;flex-wrap:wrap;gap:8px;align-items:flex-end;margin:8px 0}.bsdlg .bsp label{display:flex;flex-direction:column;font-size:11.5px;gap:2px}.bsdlg .bsp input,.bsdlg .bsp select{width:130px}
.bsdlg .bstb{overflow:auto;margin-top:6px}.bsdlg .bstb td,.bsdlg .bstb th{white-space:nowrap}
#amBody .amxok{color:#1b6e2a;background:#e6f6ea;border-left:3px solid #2f9e44;padding:4px 6px;border-radius:4px}

/* ===== Folder proyek v2 ===== */
#fpBar{position:fixed;top:58px;left:50%;transform:translateX(-50%);z-index:9000;display:none;align-items:center;flex-wrap:wrap;gap:6px 12px;width:min(820px,calc(100vw - 32px));background:#fff4e6;color:#3b2a14;border:1px solid #f2c94c;border-left:5px solid #e8590c;border-radius:8px;padding:9px 12px;box-shadow:0 4px 14px rgba(0,0,0,.18);font-size:12.5px;line-height:1.45}
#fpBar .fpmsg{flex:1 1 380px;min-width:0}
#fpBar .fpbtn{display:flex;gap:6px;flex:0 0 auto}
#fpBar .fpbtn button{margin:0;padding:6px 12px;border-radius:6px;border:1px solid #c98a2b;background:#fff;color:#3b2a14;font-weight:600;cursor:pointer;white-space:nowrap}
#fpBar .fpbtn button.pri{background:#e8590c;border-color:#e8590c;color:#fff}
#fpBar .fptip{flex:1 1 100%;font-size:11.5px;color:#6b4a1a;border-top:1px dashed #e8c48a;padding-top:4px}
.fpbadge{display:inline-block;margin-left:6px;font-size:10.5px;font-weight:600;color:#1f3a5f;background:#e6edf6;border-radius:4px;padding:1px 6px;vertical-align:middle}
"""
i = s.index('</style>')
s = s[:i] + CSS + s[i:]

# ---------- 2. Bar atas: susunan sama dengan GC-Ex Drillhole ----------
old_seg = "<button onclick='setCam(1.5,-1.5,1)' title='Isometrik'>Iso</button></div>"
rep(old_seg, "<button onclick='setCam(1.5,-1.5,1)' title='Isometrik'>Iso</button><button onclick='viewSection()' title='Kamera tegak lurus bidang sayatan'>&#8869; Tegak lurus</button></div>")
m = re.search(r"<button class='tb' onclick='viewSection\(\)'.*?Tegak lurus sayatan</button>\n", s)
assert m; s = s[:m.start()] + s[m.end():]
# langkah slab setelah tombol Penampang 2D
m = re.search(r"(<button class='tb' id='btn2d'.*?Penampang 2D</button>\n)", s)
assert m
s = s[:m.end()] + "<div class='seg' id='hdStep' title='Geser sayatan sejauh tebal slab (sama dengan Maju / Mundur di menu Sayatan)'><button onclick='stepPos(-1)'>&#9660; Mundur</button><span id='hdPos'>0.0 m</span><button onclick='stepPos(1)'>Maju &#9650;</button></div>\n" + s[m.end():]
rep("<input type='checkbox' id='showDH' hidden><label class='tg sw'><input type='checkbox' id='darkMode'",
    "<button class='tb' id='lyrBtn' onclick='lyrToggle()' title='Layer: tampil / sembunyikan semua elemen 3D &amp; Penampang 2D' aria-label='Layer'><svg viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='1.8' stroke-linejoin='round'><path d='M12 3l9 5-9 5-9-5z'/><path d='M3 13l9 5 9-5'/><path d='M3 17.5l9 5 9-5' opacity='.6'/></svg></button>\n<input type='checkbox' id='showDH' hidden><label class='tg sw'><input type='checkbox' id='darkMode'")

rep("<span class='gcx' title='GC-Ex'>GC-Ex</span><div><b>Grade Control Excellence &middot; Block Model</b>",
    "<span class='gcxw' title='GC-Ex Block Model: pemanfaatan block model dalam penambangan'><span class='gcx'>GC-Ex</span><span class='gcxm'>Block Model</span></span><div><b>Grade Control Excellence</b>")
s = s.replace("#top{gap:10px}", "#top{gap:10px}\n#top .modb{flex:0 0 auto;font:700 9px/1.05 Arial,sans-serif;letter-spacing:.08em;color:#1b1408;background:#f0c047;border-radius:4px;padding:3px 5px;text-align:center}", 1)

# ---------- 3. Rail: urutan & pengelompokan seperti GC-Ex Drillhole ----------
m = re.search(r"<nav id='rail'>\n(.*?)\n</nav>", s, re.S)
lines = m.group(1).split('\n')
B = {}
for ln in lines:
    k = re.search(r"id='(rb\w+)'", ln)
    if k: B[k.group(1)] = ln
B['rbModel'] = B['rbModel'].replace(">Model</button>", ">Data Referensi</button>").replace("<button class='rb' id='rbModel'", "<button class='rb' id='rbModel' title='Data referensi eksternal: permukaan pit / topografi (DTM), titik survey, string Surpac / DXF'")
B['rbAM'] = B['rbAM'].replace("title='Model as-mined (rekonsiliasi)'", "title='As-Mined: model as-mined &amp; rekonsiliasi per flitch'")
order = ['rbData', 'rbGeo', 'rbSlice', 'rbBM', 'rbAM', '|', 'rbModel', 'rbWf', 'rbDig', 'rbPlan', 'rbWarna', 'rbOverlay', 'rbView']
out = []
for k in order:
    out.append("<div class=rsep title='Menu pendukung'></div>" if k == '|' else B.pop(k))
out.append("<div class='grow'></div>")
out.append(B.pop('rbHide'))
assert not B, B
s = s[:m.start(1)] + '\n'.join(out) + s[m.end(1):]

# ---------- 4. Panel Block Model: judul bagian jadi H4 (untuk tab) ----------
rep("<div id='bxBody'></div>\n<div class='lyhead'>&#9935; Dig block per flitch</div>",
    "<h4>Tampilan block model</h4>\n<div id='bxBody'></div>\n<h4 class='lyhead'>&#9935; Dig block per flitch</h4>")
rep("<div class='lyhead'>&#128438; Layout &amp; Plot PDF</div>", "<h4 class='lyhead'>&#128438; Layout &amp; Plot PDF</h4>")

# ---------- 5. Data Referensi ----------
# panel Data Referensi (permukaan DTM, titik, string) & panel Import Wireframe Geologi ditulis langsung di gcex_base.html
# sejak 0.24.42 import keduanya hanya lewat baris "+ Tambah …" di Project Tree (tombol panel dihapus)
assert "<section id='pWf' hidden>" in s and "<section id='pModel' hidden>" in s

# ---------- 6. Teks tur demo ----------
rep("d:'Menu Model: solid vein (Leapfrog, Surpac DTM, DXF, OBJ), titik survey", "d:'Wireframe geologi (Leapfrog, Surpac DTM, DXF, OBJ) diimport di node Import Wireframe Geologi; Menu Data Referensi: permukaan pit / topografi (DTM), titik survey")
rep("'Model & Overlay'", "'Referensi & Overlay'", s.count("'Model & Overlay'"))
s = s.replace("t:'Model vein & string Surpac'", "t:'Wireframe & data referensi'")

# ---------- 7. Kartu Plotly disembunyikan bila Plotly sudah tertanam ----------
rep("E('plSave').style.display=(how.indexOf('tertanam')>=0)?'none':'block';",
    "E('plSave').style.display=(how.indexOf('tertanam')>=0)?'none':'block';if(how.indexOf('tertanam')>=0&&E('plCard'))E('plCard').style.display='none';")

# ---------- 7b. Folder proyek v2 (di dalam closure FP) ----------
fp2 = open(W + 'fp2.js', encoding='utf-8').read()
fp2 = fp2 + '\n' + open(W + 'prj.js', encoding='utf-8').read() + '\n' + open(W + 'wm.js', encoding='utf-8').read()
rep("setTimeout(function(){try{FP.startUI();}catch(e){}},50);\n", fp2 + "\nsetTimeout(function(){try{FP.startUI();}catch(e){}},50);\n")

# ---------- 7b2. Block model besar lewat backend (skrip luar, sebelum fungsi permukaan grid) ----------
rep("/* ================= permukaan grid dari string (topografi / desain pit) =================",
    open(W + 'mdlbig.js', encoding='utf-8').read() + '\n' + open(W + 'guide.js', encoding='utf-8').read() + '\n' + open(W + 'desk_text.js', encoding='utf-8').read() + "\n/* ================= permukaan grid dari string (topografi / desain pit) =================")

# ---------- 7b3. Topografi / desain pit jumbo: baca per potongan & sederhanakan per segmen ----------
sys.path.insert(0, W)
import bigline_patch as _blp
s, _nb = _blp.patch(s, open(W + 'bigline.js', encoding='utf-8').read())
import ortho_patch as _orp
s = _orp.patch(s)
print('Orthofoto latar: OK')
import hires_patch as _hrp
s = _hrp.patch(s)
print('LOD topografi & orthofoto (resolusi tinggi): OK')
print('Pembaca garis jumbo tersambung:', _nb, 'tempat')

# ---------- 7c. Multi-elemen: akumulasi kadar tiap elemen laporan di perhitungan & tampilan dig block ----------
def rep1(a, b):
    global s
    n = s.count(a)
    assert n == 1, (n, a[:80])
    s = s.replace(a, b)
# lyTon (metode Presisi): inisialisasi, tambah per blok, finalisasi
rep1("sfT:0,sx:0,sxT:0},DU=window.dbU?dbU():{},SC=DU.sfAttr",
     "sfT:0,sx:0,sxT:0,E:window.elInit?elInit(ga):null},DU=window.dbU?dbU():{},SC=DU.sfAttr")
rep1("var v=ar*ovi,sg=sgA&&isFinite(sgA[i])&&sgA[i]>0?sgA[i]:U.sg,t=v*sg;r.n++;r.a+=ar*ovi/fh;r.v+=v;r.t+=t;",
     "var v=ar*ovi,sg=sgA&&isFinite(sgA[i])&&sgA[i]>0?sgA[i]:U.sg,t=v*sg;r.n++;r.a+=ar*ovi/fh;r.v+=v;r.t+=t;if(r.E)elAdd(r,i,t);")
rep1("r.cov=r.a/Math.max(1e-9,lyArea(P)-ea);return r;}",
     "r.cov=r.a/Math.max(1e-9,lyArea(P)-ea);if(r.E)elFin(r);return r;}")
# komposit flitch: ringkasan kelas per elemen
rep1("GV=gA?lyFcNum(fc,gA):null,ca=s*s;", "GV=gA?lyFcNum(fc,gA):null,ca=s*s,EV=window.elFcVals?elFcVals(fc):[];")
rep1("S.g+=GV[q]*fc.CW[q]*ca;S.gt+=fc.CW[q]*ca;}}", "S.g+=GV[q]*fc.CW[q]*ca;S.gt+=fc.CW[q]*ca;}if(EV.length)elStAdd(S,EV,q,fc.CW[q]*ca);}")
# tampilan: daftar dig block, popup, editor, running grade, label peta layout
rep1("(t.t?lyFmt(t.t)+' t @ '+(isFinite(t.grade)?t.grade.toFixed(2):'-'):'-')+'</b>'+(t.wA",
     "(t.t?lyFmt(t.t)+' t @ '+(isFinite(t.grade)?t.grade.toFixed(2):'-'):'-')+'</b>'+elTxtH(t)+(t.wA")
_a = "(t&&t.t?lyFmt(t.t)+' t @ '+(isFinite(t.grade)?t.grade.toFixed(2):'-')+' g/t':'-')+'</b>"
assert s.count(_a) == 2, s.count(_a)
s = s.replace(_a, _a + "'+elTxtH(t)+'")
rep1("' g/t</b>'+(t.cov<0.98?", "' g/t</b>'+elTxtH(t)+(t.cov<0.98?")
rep1("+(o.ton.sulf?'  (sulfida)':''),col:'#000000',font:'TB',anchor:'m',halo:1});",
     "+(o.ton.sulf?'  (sulfida)':''),col:'#000000',font:'TB',anchor:'m',halo:1});if(o.ton&&o.ton.t>0&&L.lblEl!==false&&window.elLbl){var _et=elLbl(o.ton);if(_et)ops.push({t:'text',x:ax,y:Math.min.apply(null,p.map(function(q){return q[1];}))-11,s:3.4,txt:_et,col:'#000000',font:'T',anchor:'m',halo:1});}")

# as-mined report (rekonsiliasi per flitch): elemen tambahan di CSV & halaman kedua PDF
rep1("names:r.polys};});}", "names:r.polys,el:s.el||null,elw:s.elw||null};});}")
rep1("Metal_resmi_g,Metal_asmined_g'];", "Metal_resmi_g,Metal_asmined_g'+(window.elAmCsvH?elAmCsvH():'')];")
rep1("x.mO.toFixed(2),x.mA.toFixed(2)].join(','));});", "x.mO.toFixed(2),x.mA.toFixed(2)].concat(window.elAmCsvV?elAmCsvV(x):[]).join(','));});")
rep1("T.mO.toFixed(2),T.mA.toFixed(2)].join(','));", "T.mO.toFixed(2),T.mA.toFixed(2)].concat(window.elAmCsvT?elAmCsvT(R):[]).join(','));")
rep1("var pg={W:W,H:H,ops:ops,scale:0},b=lyPdf([pg]);", "var pg={W:W,H:H,ops:ops,scale:0},PG=[pg];try{var _p2=window.elAmPage?elAmPage(R):null;if(_p2)PG.push(_p2);}catch(e){console.error(e);}var b=lyPdf(PG);")

# ---------- 7z. Cek sintaks semua modul JS (bila Node.js tersedia) supaya galat ketahuan saat build ----------
import shutil as _sh, subprocess as _sp
# modul tambahan 0.14.0+ (dipasang di akhir lapisan UI, berurutan)
EXTRA = ['theme_ui.js', 'bm2dimg.js', 'digman.js', 'amedit.js', 'amups.js', 'sec_bm.js', 'am3d.js', 'ui19.js', 'flrev_bm.js', 'ortho2d_bm.js', 'period_bm.js', 'gcops_bm.js', 'rppit.js', 'rpmetode.js', 'digqt.js', 'amroof.js', 'demox.js']
if _sh.which('node'):
    for _m in EXTRA + ['am2.js', 'sgfix.js', 'multiel.js', 'mdlsum.js', 'rpbm.js', 'prj.js', 'wm.js', 'ui_layer.js', 'fp2.js', 'mdlbig.js', 'guide.js', 'desk_text.js', 'bigline.js', 'ptree.js', 'ptree_bm.js', 'amfloor.js']:
        _r = _sp.run(['node', '--check', W + _m], capture_output=True, text=True)
        assert _r.returncode == 0, 'Galat sintaks di ' + _m + ':\n' + _r.stderr[:800]
    print('Cek sintaks modul: OK')

# ---------- 8. Lapisan UI di akhir sumber viewer ----------
ui = open(W + 'am2.js', encoding='utf-8').read() + '\n' + open(W + 'amfloor.js', encoding='utf-8').read() + '\n' + open(W + 'sgfix.js', encoding='utf-8').read() + '\n' + open(W + 'multiel.js', encoding='utf-8').read() + '\n' + open(W + 'mdlsum.js', encoding='utf-8').read() + '\n' + open(W + 'rpbm.js', encoding='utf-8').read() + '\n' + open(W + 'ui_layer.js', encoding='utf-8').read() + '\n' + open(W + 'ptree.js', encoding='utf-8').read() + '\n' + open(W + 'ptree_bm.js', encoding='utf-8').read()
ui += ''.join('\n' + open(W + _m, encoding='utf-8').read() for _m in EXTRA)
# data latihan bawaan: modul shell (di luar sumber viewer, karena tombolnya ada di halaman import)
_dl = open(W + 'demodata.js', encoding='utf-8').read()
assert '</scr' + 'ipt>' not in _dl
s = s.replace('</body>', '<script>\n' + _dl + '\n</script>\n</body>', 1)

i = s.index('<script type="text/plain" id="vsrc">')
j = s.index('</script>', i)
s = s[:j] + ui + '\n' + s[j:]

# ---------- 8c. SG per blok terpusat ----------
import re as _re
_pat=_re.compile(r"sgA&&isFinite\(sgA\[([a-z.]+)\]\)&&sgA\[\1\]>0\?sgA\[\1\]:(?:U|BX\.ui)\.sg")
_n=len(_pat.findall(s));s=_pat.sub(lambda mm:'bxSGv(sgA?sgA['+mm.group(1)+']:NaN)',s);print('SG terpusat:',_n,'tempat')
assert _n>=6

# ---------- 0.20: "sulfida / SxS" -> Additional flagging (aturan komposit unsur, lihat flrev_bm.js) ----------
s = s.replace("(o.ton.sulf?'  (sulfida)':'')", "(window.afTxt?afTxt(o.ton):'')")
s = s.replace("(t.sulf?' &middot; <b style=\"color:#b8860b\">sulfida &rarr; string ganda</b>':'')", "(t.sulf?' &middot; <b style=\"color:#b8860b\">&#9873; '+((t.af||[]).join(', ')||'flag')+' &rarr; garis ganda</b>':'')")
s = s.replace("<span>Sulfida?</span>", "<span>Flag?</span>")
s = s.replace("' string ganda</b> (sulfida / sxs &gt; '+U.sxsThr+')'", "' garis ganda</b> (additional flagging)'")
# ---------- 8d. Kulit desktop (3D halus + lebih padat), dipasang sebagai <style> terakhir ----------
_k = s.rindex('</body>')
s = s[:_k] + '<style id="deskSkin">\n' + open(W + 'desk_skin.css', encoding='utf-8').read() + '\n</style>\n' + '<style id="bmSolid">\n' + open(W + 'skin_bm_solid.css', encoding='utf-8').read() + '\n</style>\n' + '<style id="deskDense">\n' + open(W + 'desk_dense.css', encoding='utf-8').read() + '\n</style>\n' + '<style id="themeEarthy">\n' + open(W + 'theme_earthy.css', encoding='utf-8').read() + '\n</style>\n' + s[_k:]

# ---------- 9. Tanam Plotly ----------
if '--noplotly' not in sys.argv:
    p = open(W + 'plotly.js', encoding='utf-8').read()
    rep('<script id="plotlyInline"></script>', '<script id="plotlyInline">' + p.replace('</script', '<\\/script') + '</script>')

import bmfix_patch
s = bmfix_patch.patch(s)
print('BM fix (garis 2D, zoom, dig block manual): OK')

import nosrc_patch as _nosrc
s = _nosrc.patch(s)
print('Tanpa akses kode sumber: OK')
import palette_patch as _pal
s, _np = _pal.patch(s, earthy=True)
s = _pal.layout(s)
print('Palet kuning baru:', _np, 'tempat')
import brand_build as _brand
s = _brand.apply(s, 'bm', OUT)
print('Identitas GC-Ex 0.19: OK')
open(OUT, 'w', encoding='utf-8').write(s)
print('OK', len(s))
