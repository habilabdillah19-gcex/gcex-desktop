"""Sambungkan pembaca garis jumbo (bigline.js) ke layar Mulai GC-Ex Block Model & GC-Ex Drillhole.
Bagian SA.go yang membaca topografi / desain pit diganti dengan SA.readLinesInto (baca per potongan + sederhanakan per segmen),
hasil (titik, jumlah titik, batas area) identik dengan pembaca asli."""
import re

GO = re.compile(r"var segs=await readLines\(s\),out=s\.role==='topo'\?D\.topoData:D\.pitData,nn=segsOut\(segs,out,s\.k==='xyz'\?0:tol\);(\s*)"
                r"var x0=1e18,x1=-1e18,y0=1e18,y1=-1e18;segs\.forEach\(function\(P\)\{P\.forEach\(function\(p\)\{if\(p\[0\]<x0\)x0=p\[0\];if\(p\[0\]>x1\)x1=p\[0\];if\(p\[1\]<y0\)y0=p\[1\];if\(p\[1\]>y1\)y1=p\[1\];\}\);\}\);\s*"
                r"segs\.forEach\(function\(P\)\{P\.forEach\(function\(p\)\{ab\(p\[0\],p\[1\],p\[2\]\);\}\);\}\);")
GO_NEW = ("var out=s.role==='topo'?D.topoData:D.pitData,_R=await SA.readLinesInto(s,out,s.k==='xyz'?0:tol,ab,function(f){msg('Membaca '+esc(s.f.name)+': '+Math.round(f*100)+'%');}),nn=_R.nn,segs={buang:_R.buang,recLen:_R.recLen};\\1"
          "var x0=_R.x0,x1=_R.x1,y0=_R.y0,y1=_R.y1;")
VER_OLD = "var segs=await readLines(s2),nn=segsOut(segs,out,s2.k==='xyz'?0:tol);"
VER_NEW = "var nn=(await SA.readLinesInto(s2,out,s2.k==='xyz'?0:tol)).nn;"


ANCHOR = "SA.readLines=function(s){return readLines(s);};"


def patch(s, js):
    # modul harus berada DI DALAM closure tempat readStr/readDxf/readXyz/dpKeep didefinisikan (bukan variabel global)
    assert s.count(ANCHOR) == 1, 'titik sisip SA.readLines tidak ditemukan tepat satu kali'
    s = s.replace(ANCHOR, ANCHOR + '\n' + js + '\n')
    s, n = GO.subn(GO_NEW, s)
    assert n == 1, 'pola pembacaan topografi di SA.go tidak ditemukan tepat satu kali: %d' % n
    m = s.count(VER_OLD)
    assert m <= 1, m
    s = s.replace(VER_OLD, VER_NEW)
    return s, n + m
