/* ================= GC-Ex 0.19: identitas visual bersama + nama project site =================
   GCEX_APP ('bm' | 'dh') ditulis oleh skrip build di depan file ini.
   - logo dua baris (GC-Ex / BLOCK MODEL | DRILL HOLE ULTIMATE), lebar kedua baris disamakan
   - halaman muka penuh: judul, 3 langkah, isian NAMA PROJECT SITE (disimpan per proyek: SA.collectWork / SA.applyWork)
   - bilah atas: "Grade Control Excellence" + nama project site */
(function(){
  var APP=window.GCEX_APP||'bm',SUB=APP==='dh'?'Drill Hole Ultimate':'Block Model';
  document.documentElement.classList.add('app-'+APP);
  var $=function(i){return document.getElementById(i);};
  var esc=function(s){return String(s==null?'':s).replace(/[&<>"]/g,function(c){return{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c];});};
  var LOGO='<span class="gcxw" title="GC-Ex '+SUB+'"><span class="gcx">GC-Ex</span><span class="gcxm">'+SUB+'</span></span>';
  /* samakan lebar baris bawah dengan "GC-Ex": jarak huruf baris bawah disetel */
  function fit(w){if(!w)return;var a=w.querySelector('.gcx'),b=w.querySelector('.gcxm');if(!a||!b)return;a.style.removeProperty('font-size');b.style.removeProperty('font-size');b.style.setProperty('letter-spacing','0px','important');
    var wa=a.getBoundingClientRect().width,wb=b.getBoundingClientRect().width,n=Math.max(1,b.textContent.length),cap=w.closest('#top')?23:30;if(!(wa>0&&wb>0))return;
    if(wb>wa){var fs=parseFloat(getComputedStyle(a).fontSize)||20,f2=Math.min(fs*wb/wa,cap);a.style.setProperty('font-size',f2.toFixed(2)+'px','important');wa=a.getBoundingClientRect().width;
      if(wb>wa){var bs=parseFloat(getComputedStyle(b).fontSize)||8;b.style.setProperty('font-size',Math.max(6.5,bs*wa/wb).toFixed(2)+'px','important');wb=b.getBoundingClientRect().width;}}
    b.style.setProperty('letter-spacing',Math.max(0,(wa-wb)/n).toFixed(3)+'px','important');}
  function fitAll(){Array.prototype.forEach.call(document.querySelectorAll('.gcxw'),fit);}
  /* ---------- nama project site ---------- */
  SA.site=SA.site||'';
  function siteTxt(){return SA.site?SA.site:'Nama project site belum diisi';}
  function showSite(){var z=$('zoneLbl');if(z){if(z.textContent!==siteTxt())z.textContent=siteTxt();z.classList.toggle('unset',!SA.site);z.title=SA.site?'Project site: '+SA.site:'Isi nama project site di halaman awal (Proyek > Import / halaman muka)';}
    var i=$('gxSite');if(i&&document.activeElement!==i&&i.value!==SA.site)i.value=SA.site;}
  SA.setSite=function(v){SA.site=String(v||'').trim().slice(0,80);showSite();};
  function hook(name,wrap){var cur=SA[name];Object.defineProperty(SA,name,{configurable:true,get:function(){return cur?wrap(cur):cur;},set:function(f){cur=f;}});}
  hook('collectWork',function(f){return function(){var w=f.apply(this,arguments);try{if(w&&typeof w==='object')w.site=SA.site||'';}catch(e){}return w;};});
  hook('applyWork',function(f){return function(W){try{if(W&&typeof W==='object'&&'site' in W)SA.setSite(W.site);}catch(e){}return f.apply(this,arguments);};});
  /* ---------- bilah atas ---------- */
  function top(){var b=document.querySelector('#top .brand');if(!b)return;
    if(!b.querySelector('.gcxw')||!b.querySelector('.gcxt')){b.innerHTML=LOGO+'<div class="gcxt"><b>Grade Control Excellence</b><small id="zoneLbl"></small></div>';}
    else if(b.querySelector('.gcxw .gcxm').textContent!==SUB){b.querySelector('.gcxw').outerHTML=LOGO;}
    showSite();fit(b.querySelector('.gcxw'));
    var z=$('zoneLbl');if(z&&!z._gxObs){z._gxObs=new MutationObserver(function(){if(z.textContent!==siteTxt())showSite();});z._gxObs.observe(z,{childList:true,characterData:true,subtree:true});}}
  /* ---------- halaman muka ---------- */
  var HERO={bm:{h:'Block model ditambang di komputer ini, <i>bukan di cloud.</i>',
      p:'Buka folder proyek atau import block model (.mdl / CSV), topografi, desain pit dan data bor. GC-Ex Block Model memotong flitch, membuat dig block, mencatat as-mined dan melaporkan grade &times; tonase. Semua diolah offline; tidak ada data yang dikirim ke mana pun.',
      s:[['1 &middot; Import','Folder proyek, block model, permukaan & data bor. Proyek tersimpan otomatis.'],['2 &middot; Flitch & dig block','Sayatan 2D / 3D, dig block otomatis atau manual, string & as-mined.'],['3 &middot; Laporan','Grade &times; tonase dengan constraint, layout dig plan, export.']]},
    dh:{h:'Data bor dimodelkan di komputer ini, <i>bukan di cloud.</i>',
      p:'Buka folder proyek atau import collar, survey, assay dan geologi. GC-Ex Drill Hole Ultimate membuat domain vein, string kontrol, solid RBF, estimasi block model dan grade shell. Semua diolah offline; tidak ada data yang dikirim ke mana pun.',
      s:[['1 &middot; Database bor','Collar, survey, assay, geologi (Excel / CSV), data spasial & block model.'],['2 &middot; Geological modelling','Flag domain, string HW / FW, solid vein, selubung, struktur.'],['3 &middot; Estimasi','Model estimation, validasi, grade shell & ore geometry.']]}}[APP];
  function landing(){var imp=$('imp');if(!imp)return;var hb=imp.querySelector('.impHead .impBrand');
    var body=imp.querySelector('.impBody');if(body&&!$('gxSite')){var h={parentNode:body,nextSibling:body.firstChild};
      var st=document.createElement('section');st.className='gxSite';
      st.innerHTML='<label for="gxSite">Nama project site</label><input type="text" id="gxSite" maxlength="80" placeholder="mis. Site A &middot; Pit Utara" autocomplete="off">'+
        '<span></span><small>Tampil di bilah atas di bawah &ldquo;Grade Control Excellence&rdquo; dan disimpan bersama proyek. Membuka proyek tersimpan memakai nama site proyek itu.</small>';
      h.parentNode.insertBefore(st,h.nextSibling);var inp=st.querySelector('input');inp.value=SA.site;
      inp.addEventListener('input',function(){SA.setSite(inp.value);});inp.addEventListener('change',function(){SA.setSite(inp.value);try{if(SA.saveWork)SA.saveWork();}catch(e){}});}
  }
  function all(){try{top();}catch(e){console.error(e);}try{landing();}catch(e){console.error(e);}}
  all();
  if(document.fonts&&document.fonts.ready)document.fonts.ready.then(fitAll);
  window.addEventListener('load',function(){all();fitAll();});
  /* viewer dibangun ulang saat proyek dibuka -> pasang ulang logo / label bila hilang */
  var t=0;new MutationObserver(function(){if(t)return;t=setTimeout(function(){t=0;var b=document.querySelector('#top .brand');if(b&&(!b.querySelector('.gcxw')||!$('zoneLbl')))top();else showSite();if(!$('gxSite'))landing();},120);})
    .observe(document.body,{childList:true,subtree:true});
})();
