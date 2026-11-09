"""Orthofoto: mode 'Latar paling bawah (lepas elevasi)' untuk GC-Ex Block Model & GC-Ex Drillhole.
3D: orthofoto digambar datar tepat di bawah semua data yang tampil (tidak ikut Z topografi), sehingga tidak menutupi layer lain
di tampak atas, Iso maupun saat slab/sayatan dipotong. Penampang 2D horizontal (plan): orthofoto menjadi gambar latar
(layer paling bawah). Mode lama (Drape ke topo, Bidang datar) tetap ada."""


def patch(s):
    def R(a, b):
        nonlocal s
        assert s.count(a) == 1, (s.count(a), a[:80])
        s = s.replace(a, b)
    R("<select id='orMode' onchange='updatePlot()'><option value='drape'>Drape ke topo</option><option value='flat'>Bidang datar</option></select>",
      "<select id='orMode' onchange='updatePlot()'><option value='base' selected>Latar paling bawah (lepas elevasi)</option><option value='drape'>Drape ke topo</option><option value='flat'>Bidang datar (di atas data)</option></select>")
    R("var mode=$('orMode').value,hasT=OV.topoF.x.length>0;if(!hasT)mode='flat';",
      "var mode=$('orMode').value||'base',hasT=OV.topoF.x.length>0;if(!hasT&&mode==='drape')mode='flat';")
    R("z=(mode==='flat')?flatZ:topoZ(x,y)", "z=(mode==='flat')?flatZ:(mode==='base')?0:topoZ(x,y)")
    R("b:{x0:x0,x1:x1,y0:y0,y1:y1,z0:zmin,z1:zmax},res:res,n:n};", "b:{x0:x0,x1:x1,y0:y0,y1:y1,z0:zmin,z1:zmax},res:res,n:n,base:mode==='base'};")
    R("' | drape '+(mode==='flat'?'bidang datar':'ke topografi')+", "' | '+(mode==='base'?'latar paling bawah (lepas elevasi)':mode==='flat'?'bidang datar':'drape ke topografi')+")
    R("var od=(VIEW2D||draft)?null:orthoTrace(crop,light);if(od)addB(od.b);",
      "var od=(VIEW2D||draft)?null:orthoTrace(crop,light);if(od&&!od.base)addB(od.b);")
    # z latar = sedikit di bawah SEMUA data yang tampil (dihitung dari semua trace final, termasuk block model & model referensi)
    R("  /* rasio aspek juga dari rentang TETAP (bukan rentang data saat ini) supaya skala adegan tidak berubah saat overlay dicentang */",
      "  if(od&&od.base){var _zl=Infinity,_zh=-Infinity,_sc=function(v){if(v!=null&&isFinite(v)){if(v<_zl)_zl=v;if(v>_zh)_zh=v;}};traces.forEach(function(t){if(t===od.tr||!t.z)return;var a=t.z;for(var _i=0;_i<a.length;_i++){var _r=a[_i];if(_r!=null&&typeof _r==='object'&&_r.length!==undefined){for(var _j=0;_j<_r.length;_j++)_sc(_r[_j]);}else _sc(_r);}});"
      "if(!isFinite(_zl)){_zl=rz[0];_zh=rz[1];}var _zb=_zl-Math.max(0.5,(_zh-_zl)*0.02);if(od.zb!==_zb){od.zb=_zb;var _z=new Array(od.tr.x.length);for(var _k=0;_k<_z.length;_k++)_z[_k]=_zb;od.tr.z=_z;}if(_zb<rz[0])rz[0]=_zb;}\n"
      "  /* rasio aspek juga dari rentang TETAP (bukan rentang data saat ini) supaya skala adegan tidak berubah saat overlay dicentang */")
    # penampang 2D horizontal: orthofoto sebagai gambar latar
    R("L.yaxis.scaleanchor='x';L.yaxis.scaleratio=(g.m==='H')?1:o.zex;",
      "L.yaxis.scaleanchor='x';L.yaxis.scaleratio=(g.m==='H')?1:o.zex;try{if(g.m==='H'&&window.ORT&&$('ovOrtho')&&$('ovOrtho').checked){var _oi=orthoImg2D();if(_oi)L.images=[_oi];}}catch(_e){console.warn(_e);}")
    fn = ("function orthoImg2D(){if(!window.ORT)return null;var m=ORT.m;if(!ORT.url){var cv=document.createElement('canvas');cv.width=m.w;cv.height=m.h;var ctx=cv.getContext('2d'),im=ctx.createImageData(m.w,m.h),p=ORT.px,d=im.data;"
          "for(var i=0,j=0;i<p.length;i+=3,j+=4){d[j]=p[i];d[j+1]=p[i+1];d[j+2]=p[i+2];d[j+3]=255;}ctx.putImageData(im,0,0);ORT.url=cv.toDataURL('image/jpeg',0.88);}"
          "return{source:ORT.url,xref:'x',yref:'y',x:m.e0-m.dx/2,y:m.n0+m.dy/2,sizex:m.w*m.dx,sizey:m.h*m.dy,xanchor:'left',yanchor:'top',sizing:'stretch',layer:'below',opacity:+(($('orOp')||{}).value||1)};}\n")
    R("function orthoTrace(crop,light){", fn + "function orthoTrace(crop,light){")
    return s
