/* ================= GC-Ex Drill Hole Ultimate 0.20: DOMAIN AKTIF di Geostatistik & Model Estimation =================
   - Domain aktif (GM.act) dipakai bersama Geological Modelling, Geostatistik dan Model Estimation; bisa diaktifkan dari
     node domain di bawah Geological Modelling, Geostatistik ATAU Model Estimation (Project Tree) - tidak perlu kembali ke GM.
   - Geostatistik: komposit hanya dari interval bor yang di-flag ke domain aktif (domain + cabangnya; selubung = halo-nya).
     "Semua data (tanpa filter domain)" = perilaku lama. Filter Domain di Data & Filter tetap berlaku di atasnya.
     Hasil fitting disimpan ke domain aktif ("Simpan ke domain" terpilih otomatis).
   - Model Estimation: parameter yang tampil = domain aktif; tombol "Jalankan domain aktif" dan "Jalankan semua domain"
     (domain yang dicentang di Project Tree / tabel). */
(function(){
  if(!window.GM||typeof window.gmDom!=='function')return;
  if(window.GS&&GS.domOnly===undefined)GS.domOnly=true;
  var top=function(id){try{return gmTopId(id);}catch(e){return id;}};
  var name=function(id){var d=id&&gmDom(id);return d?d.name:'';};
  function refresh(){try{if(window.PT&&PT.render)PT.render(true);}catch(e){}try{if(window.ptRender)ptRender();}catch(e){}}
  /* ---------- aktifkan domain dari node mana pun ---------- */
  window.gxDomAct=function(id,where){
    if(id){GM.act=id;if(window.ME)ME.ed=top(id);}
    if(where==='gs'){GS.domOnly=!!id;if(!GS.open)try{gsToggle();}catch(e){}else try{gsRun();}catch(e){}}
    if(where==='me'){try{uiTab('ME');}catch(e){}}
    try{gmPanel();}catch(e){}try{mePanel();}catch(e){}try{gsBar();}catch(e){}try{gmDraw();updatePlot();}catch(e){}refresh();};
  /* ---------- Geostatistik: komposit dari domain aktif ---------- */
  window.gsDomCodes=function(){if(!GS.domOnly||!GM.act||!gmDom(GM.act))return null;var d=gmDom(GM.act),L=[GM.act];
    try{if(!(window.gmIsKid&&gmIsKid(d)))L=gmGroup(GM.act);}catch(e){}var C={};L.forEach(function(x){C[gmIdx(x)]=true;});return C;};
  if(typeof window.gsComps==='function'){var _gc=gsComps;gsComps=function(){var C=gsDomCodes();if(!C)return _gc.apply(this,arguments);var o=window.domOK;
      domOK=function(id,a){return o(id,a)&&C[gmCodeAt(id,(a[1]+a[2])/2)]===true;};try{return _gc.apply(this,arguments);}finally{domOK=o;}};}
  window.gsBar=function(){var p=$('gsPanel');if(!p)return;var w=p.querySelector('.gsWrap'),gh=w&&w.querySelector('.gh');if(!gh)return;var b=$('gsDomBar');
    if(!b){b=document.createElement('div');b.id='gsDomBar';gh.parentNode.insertBefore(b,gh.nextSibling);}
    var on=!!gsDomCodes(),D=window.gmTops?gmTops():GM.doms;
    b.className='gsDomBar'+(on?' on':'');
    b.innerHTML='<span>Domain</span><select onchange="gxDomAct(this.value||null,\'gs\')"><option value=""'+(on?'':' selected')+'>Semua data (tanpa filter domain)</option>'+
      GM.doms.map(function(d){return '<option value="'+d.id+'"'+(on&&d.id===GM.act?' selected':'')+'>'+gmE(d.name)+(d.par?' (cabang)':'')+'</option>';}).join('')+'</select>'+
      (on?'<small>hanya sampel di dalam domain aktif</small>':(GM.doms.length?'<small class=warn>semua sampel tercampur</small>':'<small>belum ada domain (Geological Modelling)</small>'));};
  if(typeof window.gsRun==='function'){var _gr=gsRun;gsRun=function(){try{gsBar();}catch(e){}return _gr.apply(this,arguments);};}
  /* 0.24.65 (uji data nyata Zona 3): bilah domain dulu tetap "belum ada domain" bila panel dibuka sebelum domain dibuat --
     segarkan juga saat panel dibuka / ditutup-buka dan setiap daftar domain berubah */
  /* (gsToggle TIDAK dibungkus: pembungkus di sini membuat tombol Geostatistik tidak membuka panel; lihat nyata_dh.js -- pengamat tampilan panel) */
  if(typeof window.gmDirty==='function'){var _gd=gmDirty;gmDirty=function(){var r=_gd.apply(this,arguments);try{if(window.GS&&GS.open)gsBar();}catch(e){}return r;};}
  if(typeof window.gsTab==='function'){var _gt=gsTab;gsTab=function(t){var r=_gt.apply(this,arguments);try{var s=$('gsDomSel');if(s&&GM.act){var v=top(GM.act);if(s.querySelector('option[value="'+v+'"]'))s.value=v;}}catch(e){}return r;};}
  /* ---------- Model Estimation: jalankan domain aktif / semua ---------- */
  if(typeof window.meDomsReady==='function'){var _mr=meDomsReady;meDomsReady=function(){var L=_mr.apply(this,arguments);if(ME._only)L=L.filter(function(d){return d.id===ME._only;});return L;};}
  window.meRunAct=function(){if(ME.job){ME.job.cancel=true;return;}var id=top(GM.act||'');if(!id||!gmDom(id)){alert('Pilih domain aktif dulu (Project Tree: Model Estimation / Geostatistik / Geological Modelling).');return;}
    var all=(window.gmTops?gmTops():GM.doms).filter(function(d){return d.id===id&&meParOf(d)&&imPar(d).on;});
    if(!all.length){alert('Domain '+name(id)+' belum siap: perlu solid vein (Geological Modelling, Solid) dan parameter estimasi (Geostatistik, Simpan ke domain).');return;}
    var keep=ME.sel[id];ME.sel[id]=true;ME._only=id;
    try{meRun();}catch(e){console.error(e);}
    var t=setInterval(function(){if(!ME.job){clearInterval(t);ME._only=null;if(keep!==undefined)ME.sel[id]=keep;try{mePanel();}catch(e){}}},400);
    if(!ME.job){clearInterval(t);ME._only=null;if(keep!==undefined)ME.sel[id]=keep;}};
  if(typeof window.mePanel==='function'){var _mp=mePanel;mePanel=function(){if(GM.act&&!ME.job)ME.ed=top(GM.act);var r=_mp.apply(this,arguments);
      try{var b=$('meBody'),btn=$('meBtn');if(b&&btn&&!ME.job&&!$('meBtnAct')){var id=top(GM.act||''),ready=_mr?_mr():[];var okA=ready.some(function(d){return d.id===id;});
          btn.innerHTML='&#9654; Jalankan semua domain ('+ready.length+')';btn.title='Semua domain yang dicentang di Project Tree / tabel';
          var a=document.createElement('button');a.id='meBtnAct';a.className='btn-pri';a.style.cssText='width:100%;margin-bottom:6px';a.disabled=!(window.BX&&BX.m&&okA);
          a.innerHTML='&#9654; Jalankan domain aktif'+(id?': '+gmE(name(id)):'');a.title=okA?'Hanya domain aktif':'Domain aktif belum siap (perlu solid + parameter) atau belum dipilih';a.onclick=meRunAct;
          var row=btn.closest('.row')||btn.parentNode;row.parentNode.insertBefore(a,row);
          var sm=b.querySelector('details.gmdet summary');if(sm&&id)sm.innerHTML='Parameter estimasi domain aktif: <b>'+gmE(name(id))+'</b>';}}catch(e){console.error(e);}
      return r;};}
  var st=document.createElement('style');st.textContent='.gsDomBar{display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin:6px 10px 2px;padding:6px 8px;border:1px solid var(--bd);border-left:3px solid var(--mu);border-radius:6px;background:var(--sf2);font-size:12px}'+
    '.gsDomBar.on{border-left-color:var(--pr)}.gsDomBar>span{font-weight:700;color:var(--pr)}.gsDomBar select{flex:1;min-width:140px;height:26px}.gsDomBar small{width:100%;color:var(--mu)}.gsDomBar small.warn{color:var(--dn)}';
  document.head.appendChild(st);
  try{gsBar();}catch(e){}
})();
