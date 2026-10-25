
/* ================= UI SERAGAM GC-Ex (diselaraskan dengan GC-Ex Drillhole Ultimate) =================
   - Panel ringkas: bagian panel tampil sebagai tab menempel (satu bagian terbuka, "Semua" = tampilan lama)
   - Panel Layer di sisi kanan grafik (tombol lapis di bar atas)
   - Posisi slab di bar atas (Mundur / Maju)
   Modul ini khusus pemanfaatan block model untuk penambangan: tanpa Geological Modelling / Model Estimation. */
var UISEC={};
function uiSecSel(key,k){try{localStorage.setItem('gcex_sec_'+key,k);}catch(e){}var c=UISEC[key];if(!c)return;
  c.querySelectorAll(':scope>.uitabs button').forEach(function(b){b.classList.toggle('on',b.dataset.k===k);});
  c.querySelectorAll(':scope>.uisec').forEach(function(d){var on=k==='all'||d.dataset.k===k;d.style.display=on?'':'none';d.classList.toggle('dock',on&&k!=='all');});
  var t=c.querySelector(':scope>.uitabs');if(t&&t.getBoundingClientRect().top<0)t.scrollIntoView({block:'start'});}
function uiSecTabs(c,key,labels,opt){if(!c)return;opt=opt||{};UISEC[key]=c;
  c.querySelectorAll(':scope>.uitabs').forEach(function(t){t.remove();});
  c.querySelectorAll(':scope>.uisec').forEach(function(d){while(d.firstChild)c.insertBefore(d.firstChild,d);d.remove();});
  var G=[{n:[]}],AL=[];
  Array.prototype.slice.call(c.childNodes).forEach(function(n){
    if(n.nodeType===1&&opt.always&&n.matches(opt.always)){AL.push(n);return;}
    var hd=n.nodeType===1&&((opt.hd&&n.matches(opt.hd))||n.tagName==='H4'||(n.firstElementChild&&n.firstElementChild.tagName==='H4'&&n.tagName==='DIV'));
    if(hd){var h=(n.tagName==='H4'||(opt.hd&&n.matches(opt.hd)))?n:n.firstElementChild;G.push({n:[],t:(h.textContent||'').trim()});}
    G[G.length-1].n.push(n);});
  if(G.length<3)return;
  var sel=null;try{sel=localStorage.getItem('gcex_sec_'+key);}catch(e){}if(!(sel==='all'||(+sel>=1&&+sel<G.length)))sel=opt.def||'1';
  var bar=document.createElement('div');bar.className='uitabs';
  bar.innerHTML=G.slice(1).map(function(g,i){var l=labels&&labels[i]||g.t.replace(/\s*\(.*$/,'').slice(0,18);return '<button data-k="'+(i+1)+'" title="'+g.t.replace(/"/g,'&quot;')+'">'+l+'</button>';}).join('')+'<button data-k="all" title="Tampilkan semua bagian">&#9776; Semua</button>';
  bar.addEventListener('click',function(e){var b=e.target.closest('button');if(b)uiSecSel(key,b.dataset.k);});
  G[0].n.forEach(function(n){c.appendChild(n);});c.appendChild(bar);
  G.slice(1).forEach(function(g,i){var d=document.createElement('div');d.className='uisec';d.dataset.k=String(i+1);g.n.forEach(function(n){d.appendChild(n);});c.appendChild(d);});
  AL.forEach(function(n){c.appendChild(n);});uiSecSel(key,sel);}
function uiSecOpen(key,k){if(UISEC[key])uiSecSel(key,String(k));}
/* buka tab yang memuat elemen (dipakai tur demo & aksi otomatis) */
function uiReveal(el){if(!el||!el.parentElement)return;var ch=[],a=el;while(a&&a!==document.body){if(a.classList&&a.classList.contains('uisec'))ch.unshift(a);a=a.parentElement;}
  ch.forEach(function(d){if(d.style.display!=='none')return;var c=d.parentElement;for(var k in UISEC)if(UISEC[k]===c){uiSecSel(k,d.dataset.k);break;}});}

/* ---------- posisi slab di bar atas ---------- */
(function(){var up=updatePlot,show=function(){var e=$('hdPos'),p=$('pos');if(e&&p)e.textContent=(+p.value||0).toFixed(1)+' m';};updatePlot=function(){show();return up.apply(this,arguments);};var p=$('pos');if(p)p.addEventListener('input',show);show();})();

/* ---------- panel Layer ---------- */
var LYR={items:null};
function lyrCk(id){return{get:function(){var e=$(id);return !!(e&&e.checked);},set:function(v){var e=$(id);if(e&&!e.disabled)e.checked=v;},ok:function(){var e=$(id);return !!e&&!e.disabled;}};}
function lyrArr(get,ver){return{get:function(){var L=get();return L.length>0&&L.some(function(o){return o.vis;});},set:function(v){get().forEach(function(o){o.vis=v;});ver();},ok:function(){return get().length>0;}};}
function lyrDef(){var md=function(){MD.ver++;MD.sc={};try{mdList();}catch(e){}if(SA.dirty)SA.dirty();},L=[
  {g:'Block model'},{k:'bx',t:'Block model GC',c:lyrCk('bxShow')},
  {k:'am',t:'As-mined, boundary & sampel (2D)',c:{get:function(){return !!AM.show;},set:function(v){AM.show=v;try{amPanel();}catch(e){}},ok:function(){return !!(window.BX&&BX.m);}}},
  {g:'String & data referensi'},
  {k:'dg',t:'String digitasi / dig block',c:lyrArr(function(){return DG.S;},function(){dgSave();dgList();})},
  {k:'wf',t:'Wireframe / solid',c:lyrArr(function(){return MD.models;},md)},{k:'pt',t:'Titik survey',c:lyrArr(function(){return MD.pts;},md)},{k:'st',t:'String Surpac / DXF',c:lyrArr(function(){return MD.str||[];},md)},
  {g:'Overlay'},{k:'ts',t:'Topografi (surface)',c:lyrCk('ovTopoS')},{k:'tl',t:'Topografi (kontur)',c:lyrCk('ovTopoL')},{k:'pi',t:'Desain pit',c:lyrCk('ovPit')},{k:'or',t:'Orthofoto',c:lyrCk('ovOrtho')},
  {k:'sp',t:'Bidang sayatan (3D)',c:lyrCk('showPlane')},{k:'pf',t:'Profil topo / pit di sayatan',c:lyrCk('showProf')}];
  if(window.collars&&collars.length)L=L.concat([{g:'Drillhole'},{k:'dh',t:'Drillhole',c:lyrCk('showDH')},{k:'co',t:'Collar',c:lyrCk('showCollar')},{k:'lb',t:'Label hole',c:lyrCk('showLabel')}]);
  return L;}
function lyrApply(fn){var mm=$('lyrMenu');var up=window.updatePlot,n=0;window.updatePlot=function(){n++;};try{fn();}finally{window.updatePlot=up;}
  DHC=null;updatePlot();if(mm&&mm.getAttribute('data-st')==='mini')lyrMini();else lyrRender();}
function lyrSet(k,v){LYR.items=LYR.items||lyrDef();var it=LYR.items.filter(function(x){return x.k===k;})[0];if(!it)return;lyrApply(function(){it.c.set(v);});}
function lyrPreset(p){LYR.items=LYR.items||lyrDef();lyrApply(function(){LYR.items.forEach(function(it){if(!it.k||!it.c.ok())return;
  if(p==='all')it.c.set(it.k!=='lb'&&it.k!=='sp'?true:it.c.get());
  else if(p==='mine')it.c.set(['bx','am','dg','ts','pi','pf'].indexOf(it.k)>=0);
  else if(p==='ref')it.c.set(['bx','dg','wf','pt','st'].indexOf(it.k)>=0);
  else if(p==='none')it.c.set(false);});});}
function lyrRender(){var m=$('lyrMenu');if(!m||m.getAttribute('data-st')!=='open')return;LYR.items=LYR.items||lyrDef();var h='<div class=lyrh><b>Layer</b><span><button class=x onclick="lyrState(\'mini\')" title="Ciutkan jadi strip tipis">&#8250;</button><button class=x onclick="lyrState(\'off\')" title="Tutup panel Layer">&times;</button></span></div><div class=lyrb>';
  LYR.items.forEach(function(it){if(it.g){h+='<div class=lyrg>'+it.g+'</div>';return;}var ok=it.c.ok();h+='<label class="lyri'+(ok?'':' off')+'"><input type=checkbox '+(it.c.get()&&ok?'checked':'')+(ok?'':' disabled')+' onchange="lyrSet(\''+it.k+'\',this.checked)">'+it.t+'</label>';});
  h+='<div class=lyrp><button onclick="lyrPreset(\'all\')">Semua</button><button onclick="lyrPreset(\'mine\')" title="Block model, dig block, as-mined, topografi & pit">Tambang</button><button onclick="lyrPreset(\'ref\')" title="Block model, string & data referensi">Referensi</button><button onclick="lyrPreset(\'none\')">Kosongkan</button></div>'+
    '<div class=hint>Klik nama di legenda grafik juga menyembunyikan satu trace sementara.</div></div>';m.innerHTML=h;}
function lyrState(st){var m=$('lyrMenu');if(!m)return;var old=m.getAttribute('data-st')||'off';if(st===old&&st!=='open')return;m.setAttribute('data-st',st);m.style.display=st==='off'?'none':'flex';m.classList.toggle('mini',st==='mini');
  var b=$('lyrBtn');if(b)b.classList.toggle('on',st!=='off');try{localStorage.setItem('gcex_lyr',st==='open'?'1':st==='mini'?'mini':'0');}catch(e){}
  if(st==='open'){LYR.items=lyrDef();lyrRender();}else if(st==='mini')lyrMini();if(st!==old)setTimeout(function(){uiResize();if(window.dgDraw)try{dgDraw();}catch(e){}},40);}
function lyrToggle(show){var m=$('lyrMenu');if(!m)return;var st=m.getAttribute('data-st')||'off';if(show===undefined)show=st!=='open';lyrState(show?'open':'off');}
function lyrMini(){var m=$('lyrMenu');if(!m)return;var L=lyrDef(),on=0,ok=0;L.forEach(function(it){if(it.k&&it.c.ok()){ok++;if(it.c.get())on++;}});
  m.innerHTML='<button class=lyrstrip onclick="lyrState(\'open\')" title="Buka panel Layer ('+on+' dari '+ok+' layer tampil)"><span class=lyrsa>&#8249;</span><svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"><path d="M12 3l9 5-9 5-9-5z"/><path d="M3 13l9 5 9-5"/></svg><span class=lyrsv>LAYER</span><span class=lyrsn>'+on+'/'+ok+'</span></button>';}
(function(){if($('lyrMenu'))return;var m=document.createElement('aside');m.id='lyrMenu';m.style.display='none';var st=$('stage');if(st&&st.parentNode)st.parentNode.insertBefore(m,st.nextSibling);else document.body.appendChild(m);
  document.addEventListener('change',function(e){if(m.contains(e.target))return;var s=m.getAttribute('data-st');if(s==='open'||s==='mini')setTimeout(s==='mini'?lyrMini:lyrRender,0);},true);
  try{var v=localStorage.getItem('gcex_lyr');if(v==='1'||v==='mini')setTimeout(function(){lyrState(v==='1'?'open':'mini');},0);}catch(e){}})();

/* ---------- panel ringkas: Block Model, As-Mined, Data Referensi ---------- */
(function(){
  var wrap=function(fn,after,before){var f=window[fn];if(typeof f!=='function')return;window[fn]=function(){if(before)try{before.apply(this,arguments);}catch(e){console.error(e);}var r=f.apply(this,arguments);if(after)try{after.apply(this,arguments);}catch(e){console.error(e);}return r;};};
  /* Block Model: tab utama (Block model / Dig block / Layout PDF) */
  uiSecTabs($('pBM'),'bmp',['&#9312; Block model','&#9313; Dig block','&#9314; Layout PDF']);
  /* isi Block model: sub-bagian seperti GC-Ex Drillhole */
  wrap('bxPanel',function(){var b=$('bxBody');if(!b||!BX.m)return;var mk=function(t,before){if(!before)return;var h=document.createElement('h4');h.textContent=t;b.insertBefore(h,before);};
    var kids=Array.prototype.slice.call(b.children),fl=kids.filter(function(n){return n.classList.contains('lab')&&/cut-off/i.test(n.textContent);})[0];
    mk('Warna & kelas',kids[0]);mk('Filter & tampilan',fl);mk('Statistik & tonase',$('bxStat'));
    uiSecTabs(b,'bm',['Warna &amp; kelas','Filter &amp; SG','Statistik']);});
  /* As-Mined: alur bernomor jadi tab */
  var amTabs=function(){var b=$('amBody');if(!b||!BX.m)return;uiSecTabs(b,'am',['&#9312; Setup','&#9313; Sampel','&#9314; Poligon','&#9315; Parameter','&#9316; Register','&#9317; Layout'],{hd:'.amh',def:'3'});};
  wrap('amPanel',amTabs);
  wrap('amFile',null,function(){uiSecOpen('am',2);});
  ['amPtsFile','amBndFile','amBndFromDig','amDig'].forEach(function(fn){wrap(fn,null,function(){uiSecOpen('am',3);});});
  wrap('amRun',function(silent){if(silent===true)return;uiSecOpen('am',5);});
  /* Data Referensi */
  uiSecTabs($('pModel'),'ref',['Wireframe','Titik survey','String'],{always:'#mdMsg'});
  ['mdImport','mdPts','mdStr'].forEach(function(fn,i){wrap(fn,null,function(){uiSecOpen('ref',i+1);});});
  /* tur demo: elemen yang ditunjuk otomatis dibuka tab-nya */
  wrap('dmPoint',null,function(x){uiReveal(dmEl(x));});
  try{if(BX.m)bxPanel();}catch(e){}try{amPanel();}catch(e){}
})();
