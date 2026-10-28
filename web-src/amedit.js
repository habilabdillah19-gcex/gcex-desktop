/* ================= GC-Ex Block Model 0.14: poligon as-mined bisa diedit langsung =================
   - Warna: kotak warna langsung di tiap baris Register poligon & daftar Poligon (tanpa membuka editor).
   - Bentuk: tombol ⬠ memakai editor titik dig block (tarik / sisip / hapus titik, snap sudut blok & pick-up);
     selesai edit -> titik disalin balik ke poligon as-mined, grade × tonnage dihitung ulang otomatis.
   - Enter menutup poligon as-mined saat mendigit (lihat digman.js). */
function amEdShape(id){var x=amBndAll().filter(function(q){return q.id===id;})[0];if(!x)return;if(!(window.dbFlOn&&dbFlOn()))lyApply();
  var I=amInfoById(id)||{},B=lyBench(),zs=lyZs(),tid='amtmp_'+id;DG.S=DG.S.filter(function(q){return q.id!==tid;});
  var s={no:+I.sid||1,d:'AS-MINED',closed:true,pts:x.pts.map(function(p){return[+p[0]-offX,+p[1]-offY,zs];}),pl:{m:'H',pos:zs,thick:B[0]-B[1]},col:I.col||'#2b8a3e',vis:true,id:tid,amTmp:id,db:{top:B[0],bot:B[1],zs:zs}};
  DG.S.push(s);if(!VIEW2D)toggle2D();setTimeout(function(){dbEdStart(DG.S.indexOf(s));AM.bmsg='&#9998; Edit bentuk poligon <b>'+amE(I.code||id)+'</b>: tarik titik (snap sudut blok), tarik titik tengah garis = tambah titik, Shift+klik titik = hapus. <b>Enter / Esc / Selesai</b> = simpan.';try{amPanel();}catch(e){}},60);}
(function(){var _e=dbEdEnd;dbEdEnd=function(){var s=null;try{s=dbEdS();}catch(e){}var r=_e.apply(this,arguments);
    try{if(s&&s.amTmp){var x=amBndAll().filter(function(q){return q.id===s.amTmp;})[0];if(x&&s.pts.length>=3){x.pts=s.pts.map(function(q){return[Math.round((q[0]+offX)*1000)/1000,Math.round((q[1]+offY)*1000)/1000];});}
      DG.S=DG.S.filter(function(q){return q!==s&&!(q.inner&&q.parent===s.id);});dgSave();dgList();AM.bmsg='Bentuk poligon diperbarui; grade &times; tonnage dihitung ulang.';
      if(amR().auto!==false)amRun(true);amPanel();updatePlot();amDirty();}}catch(e){console.error(e);}return r;};
  /* sisa poligon sementara (mis. aplikasi ditutup saat edit) dibersihkan */
  try{var n=DG.S.length;DG.S=DG.S.filter(function(q){return !q.amTmp;});if(DG.S.length!==n)dgSave();}catch(e){}})();
function amColSet(id,v){amPSet(id,'col',v);}
(function(){var _p=amPanel;amPanel=function(){var r=_p.apply(this,arguments);try{var el=$('amBody');if(!el)return r;var info={};amAllInfo().forEach(function(I){info[I.x.id]=I;});
    var mk=function(id,cls){var I=info[id];if(!I)return null;var w=document.createElement('span');w.className='amedx '+(cls||'');
      w.innerHTML='<input type=color value="'+amE(I.col)+'" title="Warna poligon (peta, layout &amp; register)" onchange="amColSet(\''+id+'\',this.value)"><button class=ed title="Edit bentuk poligon (geser / sisip / hapus titik)" onclick="amEdShape(\''+id+'\')">&#11040;</button>';return w;};
    el.querySelectorAll('.amr .amrh').forEach(function(h){var c=h.querySelector('code[onclick]');if(!c)return;var m=/amPOpen\('([^']+)'\)/.exec(c.getAttribute('onclick')||'');if(!m)return;var w=mk(m[1]);if(w){var b=h.querySelector('button.ed');h.insertBefore(w,b||null);}});
    el.querySelectorAll('.amrow.ampl').forEach(function(rw){var d=rw.querySelector('button.x[onclick*="amBndDel"]');if(!d)return;var m=/amBndDel\('([^']+)'\)/.exec(d.getAttribute('onclick')||'');if(!m)return;var w=mk(m[1],'pl');if(w)rw.insertBefore(w,d);});
  }catch(e){console.error(e);}return r;};})();
(function(){var st=document.createElement('style');st.textContent=
  '#amBody .amedx{display:inline-flex;gap:2px;align-items:center;flex:0 0 auto}#amBody .amedx input[type=color]{width:24px!important;height:20px!important;padding:0!important;border:1px solid var(--bd);border-radius:3px;cursor:pointer}'+
  '#amBody .amedx button.ed{height:20px;width:22px;padding:0;color:var(--pr);font-size:12px;min-height:20px}#amBody .amrow.ampl{align-items:center}';document.head.appendChild(st);})();
