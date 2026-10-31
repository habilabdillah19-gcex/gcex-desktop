"""Sambungkan web-src/hires.js (LOD topografi & orthofoto) ke halaman GC-Ex.

Dipakai build GC-Ex Drill Hole Ultimate dan GC-Ex Block Model. Dijalankan SETELAH ortho_patch,
karena salah satu titik sambungnya adalah baris yang sudah diubah ortho_patch.

Titik sambung (semuanya diperiksa harus muncul tepat satu kali):
 1. orthoRGB(xl,yl)      -> terima argumen res, ambil warna rata-rata area dari piramida (anti-alias)
 2. resolusi mesh ortho  -> mengikuti luas tampilan (zoom masuk = makin detail, jumlah titik tetap)
 3. drape ortho          -> elevasi dari grid tampilan (O(1)); topoZ asli tetap dipakai reporting
 4. topografi di 3D      -> desimasi per sel dari SELURUH data di dalam tampilan, bukan "tiap ke-n"
 5. kunci cache trace    -> ikut berubah saat tampilan berubah
 6. mapOrtho() (Drillhole) -> gambar ortho dipotong sesuai tampilan sampai 4096 px (resolusi asli saat
                              zoom dekat), bukan satu JPEG 3000 px untuk seluruh area
"""
import os

W = os.path.dirname(os.path.abspath(__file__)) + os.sep


def patch(s: str) -> str:
    n = [0]

    def R(a, b, wajib=True):
        nonlocal s
        c = s.count(a)
        if wajib:
            assert c == 1, 'titik sambung hires (%d x): %s' % (c, a[:90])
        elif c != 1:
            return False
        s = s.replace(a, b)
        n[0] += 1
        return True

    # 1. warna ortho: rata-rata area pada resolusi yang dipakai mesh
    R("function orthoRGB(xl,yl){var m=ORT.m",
      "function orthoRGB(xl,yl,res){if(res&&window.HR&&HR.on){var _q=HR.rgb(xl,yl,res);if(_q)return _q;}var m=ORT.m")

    # 2. resolusi mesh ortho mengikuti luas tampilan (kotak "Resolusi (m)" jadi batas paling halus)
    R("var res=+$('orRes').value;if(light)res=Math.max(res,4);",
      "var res=+$('orRes').value;if(light)res=Math.max(res,4);"
      "if(window.HR&&HR.on&&HR.ext){var _b=HR.box({x0:HR.ext.x0,x1:HR.ext.x1,y0:HR.ext.y0,y1:HR.ext.y1}),"
      "_r=HR.resFor(_b.x0,_b.x1,_b.y0,_b.y1,light?60000:HR.budget);res=Math.max(Math.min(res,_r),_r*0.5);}")

    # 2b. LUAS mesh ortho juga dipotong sesuai tampilan. Tanpa ini resolusi halus tidak ada gunanya:
    #     pembatas "nx*ny > 300000" akan menaikkan kembali res karena mesh masih menutupi seluruh area.
    R("if(crop){x0=Math.max(x0,G.x0-mg);x1=Math.min(x1,G.x1+mg);y0=Math.max(y0,G.y0-mg);y1=Math.min(y1,G.y1+mg);}",
      "if(crop){x0=Math.max(x0,G.x0-mg);x1=Math.min(x1,G.x1+mg);y0=Math.max(y0,G.y0-mg);y1=Math.min(y1,G.y1+mg);}"
      "if(window.HR&&HR.on&&HR.ext){var _q=HR.box({x0:x0,x1:x1,y0:y0,y1:y1});x0=_q.x0;x1=_q.x1;y0=_q.y0;y1=_q.y1;}")

    # 2c. cache mesh ortho ikut berganti saat tampilan berubah
    R("var key=res+'|'+crop+'|'+mode;", "var key=res+'|'+crop+'|'+mode+'|'+((window.HR&&HR.ver)||0);")

    # 3. drape & warna di dalam orthoTrace (baris sesudah ortho_patch; cadangan: sebelum ortho_patch)
    if not R("z=(mode==='flat')?flatZ:(mode==='base')?0:topoZ(x,y),c=(z===null)?null:orthoRGB(x,y);",
             "z=(mode==='flat')?flatZ:(mode==='base')?0:HRZ(x,y),c=(z===null)?null:orthoRGB(x,y,res);", False):
        R("z=(mode==='flat')?flatZ:topoZ(x,y),c=(z===null)?null:orthoRGB(x,y);",
          "z=(mode==='flat')?flatZ:HRZ(x,y),c=(z===null)?null:orthoRGB(x,y,res);")
    # HRZ: grid tampilan bila ada, kalau tidak topoZ asli
    R("function orthoTrace(crop,light){",
      "function HRZ(x,y){if(window.HR&&HR.on){var q=HR.zFast(x,y);if(q!==null)return q;}return topoZ(x,y);}\n"
      "function orthoTrace(crop,light){")

    # 4. topografi 3D: desimasi per sel dari seluruh data di dalam tampilan
    R("pmode=($('ovPitMode')||{}).value||'surf';",
      "pmode=($('ovPitMode')||{}).value||'surf';"
      "if(window.HR&&HR.on&&HR.ext){try{ms=HR.topoMesh(crop?OV.topoC:OV.topoF,light?4900:15000);tp=HR.topoLines(tp);}catch(_e){}}")

    # 5. kunci cache trace topografi ikut tampilan
    R("ovCache('ts|'+crop+'|'+light+'|'+op", "ovCache('ts|'+crop+'|'+light+'+'+op+'|'+((window.HR&&HR.ver)||0)")
    R("ovCache('tl|'+crop", "ovCache('tl|'+crop+'|'+((window.HR&&HR.ver)||0)")

    # 6. Peta 2D (hanya GC-Ex Drill Hole): gambar ortho sesuai tampilan, sampai 4096 px
    R("function mapOrtho(){var m=window.ORT&&ORT.m;if(!m||!ORT.px)return null;",
      "function mapOrtho(){var m=window.ORT&&ORT.m;if(!m||!ORT.px)return null;"
      "if(window.HR&&HR.on){try{var _i=HR.mapImage();if(_i)return _i;}catch(_e){}}", False)

    # kode modul disisipkan sebelum orthoInit supaya HR sudah ada saat ortho dimuat
    js = open(W + 'hires.js', encoding='utf-8').read()
    R("function orthoInit(){", js + "\nfunction orthoInit(){")
    # info resolusi di panel overlay ikut menyebut LOD
    R("$('orInfo').textContent=orthoImg.src+' | '+orthoImg.w+' x '+orthoImg.h+' px @ '+orthoImg.dx+' m';",
      "$('orInfo').textContent=orthoImg.src+' | '+orthoImg.w+' x '+orthoImg.h+' px @ '+orthoImg.dx+' m"
      " (LOD aktif: detail mengikuti zoom)';")
    return s
