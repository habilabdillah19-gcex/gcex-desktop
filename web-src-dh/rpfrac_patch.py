# -*- coding: utf-8 -*-
"""Reporting BM: timbang volume & tonase dengan atribut proporsi (mis. sb_frac dari sub-blocking).

Blok dihitung utuh berdasarkan titik pusatnya, jadi blok perbatasan selalu 100% ore atau 100% waste.
Dengan atribut proporsi (0..1) volume & tonase blok dikalikan proporsinya, sehingga blok perbatasan ikut
seadanya. Atribut kadar TIDAK dikalikan: kadarnya memang kadar bagian yang di dalam solid; pembobotan
kadar rata-rata memakai tonase, yang sudah berproporsi.
"""


def patch(s: str) -> str:
    # 1) bawaan: tanpa pembobotan
    a = "cuts:'0, 0.3, 0.5, 1, 2',grp:'bench',bh:5,show:false,sx:[],polyOut:false};}"
    assert s.count(a) == 1, 'rpDef tidak ditemukan tepat satu kali'
    s = s.replace(a, "cuts:'0, 0.3, 0.5, 1, 2',grp:'bench',bh:5,show:false,sx:[],polyOut:false,frac:''};}")

    # 2) fungsi proporsi per blok, disiapkan sekali di awal rpRun
    a = ("    var z0=parseFloat(o.z0),z1=parseFloat(o.z1),PL=o.poly?rpPoly(o.poly):null,"
         "FA=o.fA&&m.num[o.fA]?m.num[o.fA]:null,fv=parseFloat(o.fV),"
         "SGA=o.sgMode==='a'&&m.num[o.sgAttr]?m.num[o.sgAttr]:null,sg0=+o.sg||2.6;")
    assert s.count(a) == 1, 'awal rpRun tidak ditemukan tepat satu kali'
    s = s.replace(a, a + (
        "\n    /* proporsi volume blok di dalam solid (0..1): blok perbatasan ikut seadanya, tidak dibulatkan */"
        "\n    var FRQ=o.frac&&m.num[o.frac]?m.num[o.frac]:null,"
        "FRC=function(i){if(!FRQ)return 1;var v=FRQ[i];return isFinite(v)&&v>=0?Math.min(1,v):0;},nOutFr=0;"))

    # 3) tonase per blok
    a = "mask[i]=1;T.push(m.sx[i]*m.sy[i]*m.sz[i]*sg);I.push(i);"
    assert s.count(a) == 1, 'baris tonase tidak ditemukan tepat satu kali'
    s = s.replace(a, ("var fr=FRC(i);if(FRQ&&!(fr>0)){nOutFr++;continue;}"
                      "mask[i]=1;T.push(m.sx[i]*m.sy[i]*m.sz[i]*sg*fr);I.push(i);FR.push(fr);"))

    # 4) volume per blok di agregasi
    a = "r.n++;r.t+=t;r.v+=m.sx[i2]*m.sy[i2]*m.sz[i2];"
    assert s.count(a) == 1, 'baris volume tidak ditemukan tepat satu kali'
    s = s.replace(a, "r.n++;r.t+=t;r.v+=m.sx[i2]*m.sy[i2]*m.sz[i2]*FR[j];")

    # 5) daftar proporsi sejajar T / I
    a = "var n=m.n,mask=new Uint8Array(n),T=[],I=[],Kg=[],nb=0,"
    assert s.count(a) == 1, 'deklarasi T/I tidak ditemukan tepat satu kali'
    s = s.replace(a, "var n=m.n,mask=new Uint8Array(n),T=[],I=[],FR=[],Kg=[],nb=0,")

    # 6) pilihan di panel, di bawah poligon area
    a = ("  h+='<label>Poligon area (string Surpac / fitur tertutup Map)</label>"
         "<div class=\"g3 f\"><div style=\"grid-column:span 2\">'+sel('',[['','Tanpa poligon']].concat(PLs),o.poly,\"RP.o.poly=this.value\")+'</div><div>'")
    assert s.count(a) == 1, 'panel poligon tidak ditemukan tepat satu kali'
    FR = (
        "  (function(){var nums=Object.keys(m.num).filter(function(k){return /frac|prop/i.test(k);});"
        "if(!nums.length&&!o.frac)return;"
        "h+='<label title=\"Volume &amp; tonase tiap blok dikalikan proporsi ini (0&ndash;1), sehingga blok di perbatasan solid ikut seadanya alih-alih dibulatkan ke ore atau waste. "
        "Atribut sb_frac dihitung di menu Block Model: Pecah blok di batas solid / Hitung proporsi volume ore per blok.\">"
        "Timbang volume &amp; tonase dengan proporsi</label><div class=f>'"
        "+sel('',[['','(tanpa pembobotan — blok dihitung utuh)']].concat(nums.map(function(k){return[k,k];})),o.frac,\"RP.o.frac=this.value\")+'</div>';"
        "if(o.frac)h+='<div class=hint style=\"margin:-4px 0 6px\">Blok dengan proporsi 0 tidak dilaporkan; blok perbatasan dilaporkan sebagian. "
        "Kadar tidak dikalikan proporsi — kadar rata-rata ditimbang tonase, yang sudah berproporsi.</div>';})();\n"
    )
    s = s.replace(a, FR + a)

    # 7) sebutkan di ringkasan hasil bahwa laporan berproporsi
    a = "RP.res={rows:rows,cuts:cuts,atts:atts,unit:Object.assign({},o.unit),nb:nb,nOut:nOut,lab:D.lab,"
    assert s.count(a) == 1, 'RP.res tidak ditemukan tepat satu kali'
    s = s.replace(a, a + "frac:o.frac||'',nOutFr:nOutFr,")
    return s
