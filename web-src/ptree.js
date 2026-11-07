/* ================= GC-Ex: PROJECT TREE (dipakai GC-Ex Block Model & GC-Ex Drillhole) =================
   Konsep seperti Leapfrog: kiri atas = pohon proyek tersusun menurut urutan pekerjaan, kiri bawah = PROPERTI item terpilih
   (isi panel menu yang sudah ada), kanan = tampilan 3D/2D. Rail ikon kiri disembunyikan; semua menu tetap ada.
   Tiap item: centang tampil/sembunyi (bila relevan), klik = buka propertinya, klik kanan / tombol ⋯ = menu
   (ganti, tambah versi, tampilkan sebagai, ganti nama, hapus, export ...). Ganda-klik / F2 = ganti nama (bila bisa).
   Definisi pohon tiap aplikasi: PT.install({app:'dh'|'bm', nodes:function(){return [...]}}).
   Node: {id,t,ic,b(badge),mark,hint,tab,sub(regex teks sub-tab),go(),chk(true/false),onChk(v),menu()->[{t,fn,danger,dis,sep,on}],
          kids:[...],rename(nama),del(),dim} */
(function(){if(window.PT)return;
  var $=function(i){return document.getElementById(i);},LS=function(k,v){try{if(v===undefined)return localStorage.getItem(k);localStorage.setItem(k,v);}catch(e){return null;}};
  var esc=function(s){return String(s==null?'':s).replace(/[&<>"']/g,function(c){return{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c];});};
  var P='<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round">',Z='</svg>';
  var IC={
    folder:P+'<path d="M1.5 4.5v8h13v-7H7.5L6 4H2z" fill="var(--ptfold)" stroke="var(--ptfoldln)"/>'+Z,
    proj:P+'<rect x="2" y="2.5" width="12" height="11" rx="1"/><path d="M2 5.5h12M5 8.5h6M5 11h4"/>'+Z,
    topo:P+'<path d="M1.5 12.5c2-3 3.5-4 5.5-3s3.5-2.5 7.5-4"/><path d="M1.5 9.5c2-2.5 3.5-3 5-2.2S10 5 13 3" opacity=".55"/>'+Z,
    pit:P+'<path d="M1 4h3l1.5 3h5L12 4h3"/><path d="M3 7.5l1.6 3h6.8L13 7.5" opacity=".6"/>'+Z,
    ortho:P+'<rect x="2" y="3" width="12" height="10" rx="1"/><path d="M2 11l3.5-3.5 3 3 2-2L14 12"/><circle cx="11" cy="6" r="1.1"/>'+Z,
    db:P+'<ellipse cx="8" cy="3.8" rx="5.5" ry="1.8"/><path d="M2.5 3.8v8.4c0 1 2.5 1.8 5.5 1.8s5.5-.8 5.5-1.8V3.8M2.5 8c0 1 2.5 1.8 5.5 1.8s5.5-.8 5.5-1.8"/>'+Z,
    table:P+'<rect x="2" y="3" width="12" height="10" rx=".8"/><path d="M2 6.3h12M2 9.6h12M6.5 3v10"/>'+Z,
    collar:P+'<path d="M8 2v9"/><path d="M5 11h6l-3 3z" fill="currentColor"/>'+Z,
    hole:P+'<path d="M4 2.5l8 11"/><circle cx="4" cy="2.5" r="1.3" fill="currentColor"/>'+Z,
    el:P+'<rect x="2.5" y="2.5" width="11" height="11" rx="2"/><path d="M6 10.5V5.5h4M6 8h3"/>'+Z,
    geo:P+'<path d="M2 5c3-1.5 6 1.5 12-.5M2 9c3-1.5 6 1.5 12-.5M2 13c3-1.5 6 1.5 12-.5"/>'+Z,
    plan:P+'<circle cx="8" cy="8" r="5.5" stroke-dasharray="2 1.6"/><path d="M8 5.5v5M5.5 8h5"/>'+Z,
    struct:P+'<path d="M3 13L13 3"/><path d="M8 8l2.6 2.6" stroke-width="1.6"/>'+Z,
    section:P+'<path d="M2 5.5l6-3 6 3-6 3z"/><path d="M2 10.5l6 3 6-3" stroke-dasharray="1.6 1.4"/>'+Z,
    s2d:P+'<rect x="2" y="3" width="12" height="10" rx="1"/><path d="M2 10l3.5-3 3 2 2.5-3L14 8"/>'+Z,
    string:P+'<path d="M2 12l3-6 3.5 4L12 3l2 3"/><circle cx="2" cy="12" r="1"/><circle cx="14" cy="6" r="1"/>'+Z,
    solid:P+'<path d="M8 1.8l5.5 3.1v6.2L8 14.2l-5.5-3.1V4.9z"/><path d="M8 8l5.5-3.1M8 8v6.2M8 8L2.5 4.9" opacity=".6"/>'+Z,
    dom:P+'<path d="M3 3.5c4 1 6 1 10-.5v4c-4 1.5-6 1.5-10 .5zM3 9.5c4 1 6 1 10-.5"/>'+Z,
    block:P+'<path d="M2 5.5l3-1.7 3 1.7v3.4l-3 1.7-3-1.7zM8 5.5l3-1.7 3 1.7v3.4l-3 1.7-3-1.7zM5 10.6l3 1.7 3-1.7"/>'+Z,
    attr:P+'<path d="M3 4h10M3 8h10M3 12h6"/>'+Z,
    est:P+'<circle cx="5" cy="5" r="1.5"/><circle cx="11" cy="4" r="1.5"/><circle cx="7" cy="11" r="1.5"/><path d="M6.4 5.6l3.2-1M6 9.6l-.6-3M8.3 10.2l2.2-4.6" opacity=".6"/>'+Z,
    check:P+'<path d="M2 13h12"/><path d="M3 10l3-4 3 2 4-5"/><path d="M10.5 2.5l1.5 1.5 2.5-2.5" stroke-width="1.5"/>'+Z,
    report:P+'<rect x="3" y="1.8" width="10" height="12.4" rx="1"/><path d="M5.5 5h5M5.5 8h5M5.5 11h3"/>'+Z,
    chart:P+'<path d="M2 14h12M4 12V8M7.3 12V4.5M10.6 12V7M13.5 12V3" stroke-width="1.6"/>'+Z,
    map:P+'<path d="M1.8 3.5l4-1.5 4.4 1.5 4-1.5v10.5l-4 1.5-4.4-1.5-4 1.5z"/><path d="M5.8 2v10.5M10.2 3.5V14"/>'+Z,
    export:P+'<path d="M8 2v8M5 7l3 3 3-3M2.5 11v2.5h11V11"/>'+Z,
    image:P+'<rect x="2" y="3" width="12" height="10" rx="1"/><circle cx="6" cy="6.5" r="1.2"/><path d="M2.5 12l4-3.5 3 2.5 2-1.5 2.5 2"/>'+Z,
    gear:P+'<circle cx="8" cy="8" r="2.2"/><path d="M8 1.8v2M8 12.2v2M1.8 8h2M12.2 8h2M3.6 3.6l1.4 1.4M11 11l1.4 1.4M3.6 12.4L5 11M11 5l1.4-1.4"/>'+Z,
    color:P+'<circle cx="8" cy="8" r="5.8"/><path d="M8 2.2v11.6" /><path d="M8 2.2a5.8 5.8 0 010 11.6z" fill="currentColor" opacity=".35"/>'+Z,
    eye:P+'<path d="M1.5 8s2.4-4.2 6.5-4.2S14.5 8 14.5 8s-2.4 4.2-6.5 4.2S1.5 8 1.5 8z"/><circle cx="8" cy="8" r="1.8"/>'+Z,
    digit:P+'<path d="M2.5 13.5l2.2-.6 7.6-7.6-1.6-1.6-7.6 7.6z"/><path d="M9.6 4.8l1.6 1.6"/>'+Z,
    flitch:P+'<rect x="2" y="5" width="12" height="2.6" rx=".5"/><rect x="2" y="9" width="12" height="2.6" rx=".5" opacity=".55"/>'+Z,
    poly:P+'<path d="M3 4.5l6-2 4.5 4-2 6.5-7 .5z"/>'+Z,
    asmined:P+'<path d="M2 12.5h12"/><path d="M3.5 12.5L6 6l3 3 2-4 1.5 7.5"/><path d="M10.5 2.5l1.5 1.5 2.5-2.5" stroke-width="1.5"/>'+Z,
    ver:P+'<circle cx="8" cy="8" r="2.2" fill="currentColor"/>'+Z,
    ref:P+'<path d="M8 1.8l5.5 3.1v6.2L8 14.2l-5.5-3.1V4.9z" stroke-dasharray="2 1.4"/>'+Z,
    pts:P+'<circle cx="4" cy="5" r="1.2" fill="currentColor"/><circle cx="11" cy="4" r="1.2" fill="currentColor"/><circle cx="7" cy="10" r="1.2" fill="currentColor"/><circle cx="12" cy="11.5" r="1.2" fill="currentColor"/>'+Z,
    gs:P+'<path d="M2 13c2-8 4-9 6-9s3 5 6 6"/><path d="M2 14h12" opacity=".6"/>'+Z,
    more:'<svg viewBox="0 0 16 16" fill="currentColor"><circle cx="3.5" cy="8" r="1.3"/><circle cx="8" cy="8" r="1.3"/><circle cx="12.5" cy="8" r="1.3"/></svg>'};
  var T=window.PT={def:null,sel:null,open:{},sig:'',flat:[],nodes:[],ic:IC,esc:esc};
  var ok=function(f){try{return f();}catch(e){return undefined;}};
  /* ---------- tata letak: kolom kiri = tree + properti ---------- */
  function layout(){var body=$('body'),side=$('side');if(!body||!side||$('ptCol'))return false;
    var col=document.createElement('div');col.id='ptCol';body.insertBefore(col,side);
    col.innerHTML='<div id="ptWrap"><div class="pth"><span class="ptt">Project Tree</span><span class="ptb"><button type="button" id="ptExp" title="Buka semua folder">&#8862;</button><button type="button" id="ptCol1" title="Tutup semua folder">&#8863;</button><button type="button" id="ptHide" title="Sembunyikan panel kiri (buka lagi lewat tombol di tepi kiri tampilan)">&#171;</button></span></div><div id="ptree" tabindex="0" role="tree" aria-label="Project tree"></div></div><div id="ptSplit" title="Geser untuk mengatur tinggi tree / properti"></div>';
    col.appendChild(side);var ph=document.createElement('div');ph.id='ptPH';side.insertBefore(ph,side.firstChild);
    /* Kartu aksi. Node yang hanya menjalankan perintah (buka dialog, unduh berkas) dulu tidak mengganti
       isi panel sama sekali, sehingga panel milik node SEBELUMNYA tetap terpampang di bawah judul node
       yang baru -- isi tidak nyambung dengan judulnya, dan fungsi yang sama terlihat seolah ada di
       banyak menu. Sekarang node seperti itu memunculkan kartu ringkas berisi keterangan + tombolnya. */
    var cd=document.createElement('div');cd.id='ptCard';cd.style.display='none';side.insertBefore(cd,ph.nextSibling);
    var ob=document.createElement('button');ob.type='button';ob.id='ptOpen';ob.title='Tampilkan Project Tree';ob.innerHTML='&#187;';ob.onclick=function(){if(side.classList.contains('hide'))uiSide();};
    var st=$('stage');if(st)st.appendChild(ob);
    $('ptHide').onclick=function(){if(!side.classList.contains('hide'))uiSide();};
    $('ptExp').onclick=function(){T.flatAll(T.nodes).forEach(function(n){if(n.kids&&n.kids.length)T.open[n.id]=1;});saveOpen();render(true);};
    $('ptCol1').onclick=function(){T.open={};saveOpen();render(true);};
    var sync=function(){col.classList.toggle('hide',side.classList.contains('hide'));ob.style.display=side.classList.contains('hide')?'block':'none';};
    new MutationObserver(sync).observe(side,{attributes:true,attributeFilter:['class']});sync();
    /* tinggi tree (diingat) */
    var wrap=$('ptWrap'),sp=$('ptSplit'),h0=+LS('gcex_ptH')||0,setH=function(h){var H=col.getBoundingClientRect().height||600;h=Math.round(Math.max(120,Math.min(H-140,h)));wrap.style.height=h+'px';return h;};
    setTimeout(function(){setH(h0>0?h0:Math.round((col.getBoundingClientRect().height||600)*0.46));},0);
    sp.addEventListener('mousedown',function(e){if(e.button!==0)return;var y0=e.clientY,s0=wrap.getBoundingClientRect().height;document.body.classList.add('ptdrag');
      var mv=function(ev){setH(s0+ev.clientY-y0);},up=function(){document.removeEventListener('mousemove',mv);document.removeEventListener('mouseup',up);document.body.classList.remove('ptdrag');LS('gcex_ptH',String(wrap.getBoundingClientRect().height|0));};
      document.addEventListener('mousemove',mv);document.addEventListener('mouseup',up);e.preventDefault();});
    sp.addEventListener('dblclick',function(){LS('gcex_ptH','0');setH((col.getBoundingClientRect().height||600)*0.46);});
    window.addEventListener('resize',function(){var h=wrap.getBoundingClientRect().height;setH(h);});
    /* lebar bawaan kolom sedikit lebih lebar untuk tree */
    try{if(!(+LS('gcex_sideW')>0)&&window.uiSideW&&uiSideW()<310)uiSideW(310);}catch(e){}
    return true;}
  /* ---------- data ---------- */
  T.flatAll=function(L,out){out=out||[];(L||[]).forEach(function(n){out.push(n);if(n.kids)T.flatAll(n.kids,out);});return out;};
  function saveOpen(){LS('gcex_pt_open_'+(T.def&&T.def.app),JSON.stringify(T.open));}
  function find(id){var r=null;T.flatAll(T.nodes).some(function(n){if(n.id===id){r=n;return true;}return false;});return r;}
  T.find=find;
  function build(){var L=ok(function(){return T.def.nodes();})||[];T.nodes=L;return L;}
  function sigOf(L){return JSON.stringify(T.flatAll(L).map(function(n){return [n.id,n.t,n.b,n.mark,n.chk,n.dim,n.st,n.kids?n.kids.length:-1,T.open[n.id]?1:0];}));}
  /* ---------- gambar ---------- */
  function rowHtml(n,d){var has=n.kids&&n.kids.length,op=has&&T.open[n.id],ck=n.chk===true||n.chk===false;
    return '<div class="ptr'+(T.sel===n.id?' sel':'')+(n.dim?' dim':'')+(n.fold?' fold':'')+'" role="treeitem" aria-level="'+(d+1)+'"'+(has?' aria-expanded="'+(op?'true':'false')+'"':'')+' data-id="'+esc(n.id)+'" style="--d:'+d+'" title="'+esc(n.hint||n.t)+'">'+
      '<span class="ptc'+(has?'':' no')+'">'+(has?(op?'&#9662;':'&#9656;'):'')+'</span>'+
      (ck?'<span class="ptk'+(n.chk?' on':'')+'" role="checkbox" aria-checked="'+(n.chk?'true':'false')+'" title="'+(n.chk?'Sembunyikan':'Tampilkan')+'"></span>':'<span class="ptk no"></span>')+
      (n.step?'<span class="pts'+(n.st?' '+n.st:'')+'" title="'+({done:'Selesai',next:'Langkah berikutnya',todo:'Belum dikerjakan',opt:'Opsional',part:'Sebagian'}[n.st]||'')+'"></span>':'')+'<span class="pti">'+(IC[n.ic]||IC.folder)+'</span><span class="ptl">'+esc(n.t)+'</span>'+(n.mark?'<span class="ptm">'+esc(n.mark)+'</span>':'')+(n.b!=null&&n.b!==''?'<span class="ptn">'+esc(n.b)+'</span>':'')+
      (n.menu?'<button type="button" class="ptx" tabindex="-1" title="Menu (klik kanan)">'+IC.more+'</button>':'')+'</div>';}
  function render(force){var el=$('ptree');if(!el||!T.def||T.editing)return;var L=build(),s=sigOf(L);if(!force&&s===T.sig)return;T.sig=s;var h='',flat=[];
    var walk=function(A,d){A.forEach(function(n){h+=rowHtml(n,d);flat.push(n);if(n.kids&&n.kids.length&&T.open[n.id])walk(n.kids,d+1);});};walk(L,0);
    var st=el.scrollTop;el.innerHTML=h||'<div class="hint" style="padding:10px">Buka atau buat proyek dulu.</div>';el.scrollTop=st;T.flat=flat;head();try{nav();}catch(e){}}
  T.render=render;
  function markSel(){var el=$('ptree');if(!el)return;el.querySelectorAll('.ptr.sel').forEach(function(r){r.classList.remove('sel');});var r=T.sel&&el.querySelector('.ptr[data-id="'+CSS.escape(T.sel)+'"]');if(r)r.classList.add('sel');head();}
  T.markSel=markSel;
  /* Kartu aksi: node tanpa `tab` (tidak punya panel sendiri) atau yang menyetel `card`. */
  function card(n){var el=$('ptCard');if(!el)return;
    var C=n&&(n.card||(!n.tab&&n.go?{}:null));
    if(!C){el.style.display='none';el.innerHTML='';document.body.classList.remove('pt-card');return;}
    var acts=C.acts||(n.go?[{t:C.run||('Jalankan: '+n.t.replace(/[.\u2026]+$/,'')),fn:n.go,pri:1}]:[]);
    var h='<div class=ptcd>'+(C.hint||n.hint?'<p>'+esc(C.hint||n.hint)+'</p>':'');
    /* `dim` menandai node yang DAFTARNYA masih kosong, bukan aksi yang tidak bisa dijalankan.
       Dulu seluruh tombol di kartu ikut dimatikan karenanya -- akibatnya tombol "Simpan preset"
       justru mati persis ketika belum ada preset sama sekali, yaitu saat tombol itu paling
       dibutuhkan, dan satu-satunya jalan keluarnya lewat menu titik-tiga. Sekarang yang memutuskan
       hanya aksi itu sendiri (`dis`). */
    var mati=acts.every(function(a){return a.dis;});
    if(n.dim&&mati)h+='<p class=ptcw>'+esc(C.why||'Belum bisa dijalankan: datanya belum ada.')+'</p>';
    h+=acts.map(function(a,i){return '<button type="button" class="'+(a.pri?'btn-pri':'')+'" data-i="'+i+'"'+(a.dis?' disabled':'')+(a.title?' title="'+esc(a.title)+'"':'')+'>'+esc(a.t)+'</button>';}).join('');
    if(C.kids&&n.kids&&n.kids.length)h+='<div class=ptck>'+n.kids.map(function(k){return '<button type="button" data-go="'+esc(k.id)+'">'+esc(k.t)+'</button>';}).join('')+'</div>';
    el.innerHTML=h+'</div>';el.style.display='';document.body.classList.add('pt-card');
    el.onclick=function(e){var b=e.target.closest('button');if(!b)return;
      if(b.dataset.go){T.select(b.dataset.go);return;}
      var a=acts[+b.dataset.i];if(a&&a.fn)try{a.fn();}catch(x){console.error(x);}};}
  T.card=card;
  /* Memindahkan sorotan & judul ke node lain tanpa menjalankan aksinya. Dipakai ketika panel
     berpindah bukan karena pemilihan node: menjalankan select() di situ akan memanggil go() lagi
     dan bisa berputar. */
  T.mark=function(id){var n=find(id);if(!n)return;T.sel=id;
    try{head();}catch(e){}
    try{card(n);}catch(e){}
    try{var sd=$('ptBody');if(sd){[].forEach.call(sd.querySelectorAll('.ptr.on'),function(r){r.classList.remove('on');});
      var r=sd.querySelector('.ptr[data-id="'+id+'"]');if(r)r.classList.add('on');}}catch(e){}};
  function head(){var ph=$('ptPH');if(!ph)return;var n=T.sel&&find(T.sel);if(!n){ph.innerHTML='<span class="pp">Properti</span>';return;}
    ph.innerHTML='<span class="pp">Properti</span><span class="pi2">'+(IC[n.ic]||IC.folder)+'</span><b>'+esc(n.t)+'</b>'+(n.menu?'<button type="button" class="ptx" title="Menu item ini">'+IC.more+'</button>':'');
    var b=ph.querySelector('.ptx');if(b)b.onclick=function(e){var r=b.getBoundingClientRect();menu(n,r.left,r.bottom+2);e.stopPropagation();};}
  /* ---------- aksi ---------- */
  T.goSub=function(tab,re,tries){if(!re)return;if(Array.isArray(re)){var okk=true;re.forEach(function(r){okk=T.goSub(tab,r,-1)&&okk;});if(!okk&&(tries||0)<8&&tries!==-1)setTimeout(function(){T.goSub(tab,re,(tries||0)+1);},90);return okk;}
    var p=$('p'+tab);if(!p)return false;var rx=re instanceof RegExp?re:new RegExp(re,'i');
    var B=[].slice.call(p.querySelectorAll('.uitabs button,.rptabs button')),hit=null;
    B.some(function(b){if(rx.test(b.textContent||'')){hit=b;return true;}return false;})||B.some(function(b){if(rx.test(b.title||'')){hit=b;return true;}return false;});
    if(hit){if(!hit.classList.contains('on'))hit.click();return true;}
    if(tries!==-1&&(tries||0)<8)setTimeout(function(){T.goSub(tab,re,(tries||0)+1);},90);return false;};
  function select(n,noAct){if(!n)return;T.sel=n.id;T._qt=Date.now();if(!noAct){T._quiet=1;try{if(n.tab&&window.uiTab){uiTab(n.tab);}}catch(e){console.error(e);}T._quiet=0;
      var go=function(){try{if(n.sub)T.goSub(n.tab,n.sub);}catch(e){}try{if(n.go)n.go();}catch(e){console.error(e);}};if(n.sub)setTimeout(go,30);else go();
      var sd=$('side');if(sd&&n.tab)sd.scrollTop=0;try{card(n);}catch(e){console.error(e);}try{if(T.def.onSelect)T.def.onSelect(n);}catch(e){console.error(e);}}
    render();markSel();scrollSel();nav();}
  function topOf(n){var r=null;T.nodes.some(function(t){if(t===n||T.flatAll(t.kids||[]).indexOf(n)>=0){r=t;return true;}return false;});return r;}
  function nav(){var sd=$('side');if(!sd||!T.def||!T.def.nav)return;var el=$('ptNav');if(!el){el=document.createElement('div');el.id='ptNav';sd.appendChild(el);}else if(el.parentNode!==sd||el!==sd.lastElementChild)sd.appendChild(el);
    var n=T.sel&&find(T.sel),t=n&&topOf(n),S=T.nodes.filter(function(x){return x.step;}),i=t?S.indexOf(t):-1;if(i<0){el.style.display='none';return;}el.style.display='';
    var pv=S[i-1],nx=S[i+1],lab=function(x){return esc(x.t.replace(/^Proyek:.*/,'Proyek'));};
    el.innerHTML='<span class="pnl">Langkah '+(i+1)+' / '+S.length+(t.st?' &middot; '+({done:'selesai',next:'berikutnya',todo:'belum',opt:'opsional',part:'sebagian'}[t.st]||''):'')+'</span><div class="pnb">'+(pv?'<button type="button" data-id="'+esc(pv.id)+'" title="'+lab(pv)+'">&#9664; '+lab(pv)+'</button>':'<span></span>')+(nx?'<button type="button" class="nx" data-id="'+esc(nx.id)+'" title="'+lab(nx)+'">'+lab(nx)+' &#9654;</button>':'')+'</div>';
    el.onclick=function(e){var b=e.target.closest('button[data-id]');if(!b)return;var m=find(b.dataset.id);if(m){T.open[m.id]=1;saveOpen();select(m);render(true);markSel();scrollSel();}};}
  T.nav=nav;
  T.select=function(id){var n=find(id);if(n)select(n);};
  function toggle(n){if(!n.kids||!n.kids.length)return;if(T.open[n.id])delete T.open[n.id];else T.open[n.id]=1;saveOpen();render(true);}
  function check(n){if(!n.onChk)return;try{n.onChk(!n.chk);}catch(e){console.error(e);}setTimeout(function(){render(true);},60);}
  function rename(n){if(!n.rename)return;var row=$('ptree').querySelector('.ptr[data-id="'+CSS.escape(n.id)+'"] .ptl');if(!row)return;
    var inp=document.createElement('input');inp.type='text';inp.className='ptin';inp.value=n.t;row.replaceWith(inp);T.editing=1;inp.focus();inp.select();var done=false;
    var fin=function(okk){if(done)return;done=true;T.editing=0;var v=inp.value.trim();if(okk&&v&&v!==n.t){try{n.rename(v);}catch(e){console.error(e);}}setTimeout(function(){render(true);},40);};
    inp.addEventListener('keydown',function(e){e.stopPropagation();if(e.key==='Enter')fin(true);else if(e.key==='Escape')fin(false);});inp.addEventListener('blur',function(){fin(true);});}
  T.pick=function(accept,multi,cb){var i=document.createElement('input');i.type='file';i.accept=accept||'';i.multiple=!!multi;i.style.display='none';document.body.appendChild(i);
    i.onchange=function(){try{cb(i);}finally{setTimeout(function(){i.remove();},60000);}};i.click();};
  /* ---------- menu konteks ---------- */
  function menu(n,x,y){close();var L=ok(function(){return n.menu();})||[];if(n.rename)L.push({sep:1},{t:'Ganti nama  (F2)',fn:function(){rename(n);}});
    if(!L.length)return;var m=document.createElement('div');m.id='ptMenu';m.setAttribute('role','menu');
    m.innerHTML='<div class="pmh">'+esc(n.t)+'</div>'+L.map(function(o,i){if(o.sep)return '<div class="pms"></div>';if(o.h)return '<div class="pmg">'+esc(o.h)+'</div>';
      return '<button type="button" role="menuitem" data-i="'+i+'" class="'+(o.danger?'dg ':'')+(o.on?'on ':'')+'"'+(o.dis?' disabled':'')+'>'+(o.on!=null?'<span class="rd">'+(o.on?'&#9679;':'')+'</span>':'')+esc(o.t)+'</button>';}).join('');
    document.body.appendChild(m);var r=m.getBoundingClientRect(),W=window.innerWidth,H=window.innerHeight;m.style.left=Math.max(4,Math.min(x,W-r.width-6))+'px';m.style.top=Math.max(4,Math.min(y,H-r.height-6))+'px';
    m.addEventListener('click',function(e){var b=e.target.closest('button');if(!b)return;var o=L[+b.dataset.i];close();if(o&&o.fn)setTimeout(function(){try{o.fn();}catch(er){console.error(er);}setTimeout(function(){render(true);},80);},0);});
    var f=m.querySelector('button:not([disabled])');if(f)f.focus();}
  function close(){var m=$('ptMenu');if(m)m.remove();}
  T.menuFor=function(id,x,y){var n=find(id);if(n)menu(n,x,y);};
  /* ---------- event ---------- */
  function bind(){var el=$('ptree');
    el.addEventListener('click',function(e){var r=e.target.closest('.ptr');if(!r)return;var n=find(r.dataset.id);if(!n)return;
      if(e.target.closest('.ptc')){toggle(n);return;}if(e.target.closest('.ptk')&&!e.target.closest('.ptk.no')){check(n);return;}
      if(e.target.closest('.ptx')){var b=e.target.closest('.ptx').getBoundingClientRect();menu(n,b.left,b.bottom+2);return;}
      var now=Date.now();if(T._lc&&T._lc.id===n.id&&now-T._lc.t<450){T._lc=null;dbl(n);return;}T._lc={id:n.id,t:now};
      select(n);if(n.kids&&n.kids.length&&!T.open[n.id]&&n.fold){T.open[n.id]=1;saveOpen();render(true);}});
    var dbl=function(n){if(n.rename)rename(n);else if(n.dbl)n.dbl();else if(n.kids&&n.kids.length)toggle(n);};
    el.addEventListener('contextmenu',function(e){var r=e.target.closest('.ptr');if(!r)return;e.preventDefault();e.stopPropagation();var n=find(r.dataset.id);if(!n)return;if(T.sel!==n.id)select(n);menu(n,e.clientX,e.clientY);});
    el.addEventListener('keydown',function(e){if(e.target.tagName==='INPUT')return;var i=-1;T.flat.forEach(function(n,k){if(n.id===T.sel)i=k;});var n=T.flat[i];
      if(e.key==='ArrowDown'||e.key==='ArrowUp'){e.preventDefault();var j=Math.max(0,Math.min(T.flat.length-1,i+(e.key==='ArrowDown'?1:-1)));if(T.flat[j])select(T.flat[j]);scrollSel();}
      else if(e.key==='ArrowRight'&&n&&n.kids&&n.kids.length&&!T.open[n.id]){e.preventDefault();toggle(n);}
      else if(e.key==='ArrowLeft'&&n&&T.open[n.id]){e.preventDefault();toggle(n);}
      else if(e.key===' '&&n&&n.onChk){e.preventDefault();check(n);}
      else if(e.key==='F2'&&n){e.preventDefault();rename(n);}
      else if((e.key==='ContextMenu'||(e.shiftKey&&e.key==='F10'))&&n){e.preventDefault();var r=el.querySelector('.ptr.sel');var b=r?r.getBoundingClientRect():{left:40,bottom:80};menu(n,b.left+30,b.bottom);}});
    document.addEventListener('mousedown',function(e){if(!e.target.closest('#ptMenu'))close();},true);
    document.addEventListener('keydown',function(e){if(e.key==='Escape')close();});
    window.addEventListener('blur',close);}
  function scrollSel(){var r=$('ptree').querySelector('.ptr.sel');if(r)r.scrollIntoView({block:'nearest'});}
  /* ---------- sinkron dengan menu lama (uiTab dipanggil dari tempat lain) ---------- */
  function hook(){var u=window.uiTab;if(typeof u==='function'&&!u._pt){window.uiTab=function(n){var r=u.apply(this,arguments);try{if(!T._quiet&&Date.now()-(T._qt||0)>1500){var cur=T.sel&&find(T.sel);if(!cur||cur.tab!==n){var m=null;T.flatAll(T.nodes).some(function(x){if(x.tab===n&&!x.sub){m=x;return true;}return false;});
          if(m){T.sel=m.id;T.flatAll(T.nodes).forEach(function(p){if(p.kids&&p.kids.indexOf(m)>=0)T.open[p.id]=1;});}}render();markSel();nav();}}catch(e){}return r;};window.uiTab._pt=1;}
    var de=window.dmEl;if(typeof de==='function'&&!de._pt){window.dmEl=function(x){var e=de(x);try{if(e&&/^rb[A-Z]/.test(e.id||'')&&e.getBoundingClientRect().width===0){var k=e.id.slice(2),m=null;
        T.flatAll(T.nodes).some(function(z){if(z.tab===k&&!z.sub){m=z;return true;}return false;});if(m){T.flatAll(T.nodes).forEach(function(p){if(p.kids&&p.kids.indexOf(m)>=0)T.open[p.id]=1;});render(true);
          var r=$('ptree').querySelector('.ptr[data-id="'+CSS.escape(m.id)+'"]');if(r){r.scrollIntoView({block:'nearest'});return r;}}}}catch(er){}return e;};window.dmEl._pt=1;}
    var up=window.updatePlot;if(typeof up==='function'&&!up._pt){var tm=0;window.updatePlot=function(){var r=up.apply(this,arguments);clearTimeout(tm);tm=setTimeout(function(){render();},150);return r;};window.updatePlot._pt=1;}}
  T.install=function(def){T.def=def;if(def.css){var dc=document.createElement('style');dc.id='ptDefCss';dc.textContent=def.css;document.head.appendChild(dc);}try{T.open=JSON.parse(LS('gcex_pt_open_'+def.app)||'null')||null;}catch(e){T.open=null;}
    if(!layout())return;bind();hook();var first=!T.open;if(first)T.open={};build();if(first){(def.openDef||[]).forEach(function(id){T.open[id]=1;});}
    var cur=null;try{var t=LS('dh3d_tab');if(t)T.flatAll(T.nodes).some(function(x){if(x.tab===t&&!x.sub){cur=x;return true;}return false;});}catch(e){}
    if(cur)T.sel=cur.id;render(true);poll();document.body.classList.add('pt-on');};
  /* Penyegaran berkala.
     Dulu: setInterval 1,5 detik tanpa syarat. Tiap denyut membangun ULANG seluruh pohon, dan itu
     bukan pekerjaan ringan -- ia memindai dig block, menghitung luas tiap poligon, mengelompokkan
     flitch dan membaca register as-mined. Pada model besar, denyut itu muncul sebagai tersendat
     berkala, persis saat pengguna sedang memutar atau menggeser tampilan.
     Sekarang: (1) dijalankan saat peramban sedang luang (requestIdleCallback), bukan menyela;
     (2) dilewati ketika tampilan sedang diputar / digeser atau ada perhitungan berjalan, sebab
     hasilnya toh akan dibuang; (3) mundur bertahap 1,5 -> 8 detik selama tidak ada yang berubah,
     dan kembali cepat begitu pengguna menyentuh apa pun. Yang berubah hanya KAPAN pohon dibangun
     ulang, bukan isinya. */
  var PI=1500,PMAX=8000,ptimer=null;
  T.soon=function(){PI=1500;if(ptimer){clearTimeout(ptimer);ptimer=null;poll();}};
  function busy(){return document.body.classList.contains('ptdrag')||document.body.classList.contains('busy')||
    !!(window.BX&&BX.busy)||!!(window.DLAT&&DLAT.busy)||!!(window.PLOTBUSY);}
  function tick(){if(document.hidden||T.editing||busy()){PI=Math.min(PMAX,PI*1.5);return;}
    var before=T.sig;render();PI=(T.sig===before)?Math.min(PMAX,Math.round(PI*1.4)):1500;}
  function poll(){ptimer=setTimeout(function(){ptimer=null;
    var run=function(){try{tick();}catch(e){}poll();};
    if(window.requestIdleCallback)requestIdleCallback(run,{timeout:1200});else run();},PI);}
  /* sentuhan pengguna -> segarkan cepat lagi */
  ['pointerdown','keydown','change'].forEach(function(ev){document.addEventListener(ev,function(){PI=1500;},true);});
  /* ---------- pembantu untuk definisi pohon ---------- */
  T.u={cb:function(id){var e=$(id);return e?!!e.checked:undefined;},
    setCb:function(id,v){var e=$(id);if(!e)return;if(e.checked!==!!v){e.checked=!!v;e.dispatchEvent(new Event('change',{bubbles:true}));}},
    val:function(id){var e=$(id);return e?e.value:'';},
    setVal:function(id,v){var e=$(id);if(!e)return;e.value=v;e.dispatchEvent(new Event('change',{bubbles:true}));},
    opts:function(id){var e=$(id);return e?[].map.call(e.options,function(o){return[o.value,o.textContent];}):[];},
    num:function(x){return x==null||x===''?'':(+x).toLocaleString('id-ID');},
    ask:function(m,d){var r=window.prompt(m,d==null?'':d);return r==null?null:String(r).trim();}};
  /* ---------- gaya ---------- */
  var css=document.createElement('style');css.id='ptreeCss';css.textContent=[
    ':root{--ptfold:#f2d675;--ptfoldln:#b8962a;--ptsel:#dbe6f6;--ptselln:#8fb0dc;--pthov:#eef2f7}',
    'body.dark{--ptfold:#8a7430;--ptfoldln:#c7a648;--ptsel:#24364f;--ptselln:#4b6d99;--pthov:#1c2836}',
    'body.pt-on #rail{display:none!important}',
    '#ptCol{display:flex;flex-direction:column;flex:0 0 auto;min-height:0;background:var(--sf,#fff);border-right:1px solid var(--bd,#d5dbe3)}',
    '#ptCol.hide{display:none}#ptCol.hide+#sideGrip{display:none}',
    '#ptCol>#side{flex:1 1 auto!important;min-height:0;border-right:0!important;padding-top:0!important}',
    '#ptWrap{display:flex;flex-direction:column;min-height:120px;width:0;min-width:100%;flex:0 0 auto}',
    '#ptWrap .pth{display:flex;align-items:center;justify-content:space-between;height:28px;padding:0 6px 0 10px;border-bottom:1px solid var(--bd,#d5dbe3);background:var(--bg,#f4f6f9)}',
    '#ptWrap .ptt,#ptPH .pp{font:700 10.5px/1 Arial,sans-serif;letter-spacing:.07em;text-transform:uppercase;color:var(--mu,#6b7785)}',
    '#ptWrap .ptb{display:flex;gap:2px}#ptWrap .ptb button{all:unset;cursor:pointer;width:22px;height:20px;text-align:center;border-radius:4px;color:var(--mu,#6b7785);font-size:13px;line-height:20px}#ptWrap .ptb button:hover{background:var(--pthov);color:var(--tx,#1c2733)}',
    '#ptree{flex:1;overflow:auto;padding:3px 0 8px;outline:none;font-size:12px;user-select:none}',
    '.ptr{display:flex;align-items:center;gap:3px;height:22px;padding:0 4px 0 calc(4px + var(--d)*14px);cursor:default;white-space:nowrap;color:var(--tx,#1c2733);border:1px solid transparent;border-left:0;border-right:0}',
    '.ptr:hover{background:var(--pthov)}.ptr.sel{background:var(--ptsel);border-color:var(--ptselln)}#ptree:focus .ptr.sel{box-shadow:inset 3px 0 0 var(--pr,#1f3a5f)}',
    '.ptr.dim .ptl{color:var(--mu,#8a95a3)}.ptr.fold>.ptl{font-weight:600}',
    '.ptc{flex:0 0 12px;text-align:center;font-size:10px;color:var(--mu,#6b7785);cursor:pointer}.ptc.no{cursor:default}',
    '.ptk{flex:0 0 13px;height:13px;border:1px solid #8996a6;border-radius:3px;background:var(--sf,#fff);cursor:pointer;position:relative}.ptk.no{border-color:transparent;background:none;cursor:default}',
    '.ptk.on{background:var(--pr,#1f3a5f);border-color:var(--pr,#1f3a5f)}.ptk.on::after{content:"";position:absolute;left:3.5px;top:0.5px;width:3.5px;height:7px;border:solid #fff;border-width:0 2px 2px 0;transform:rotate(45deg)}',
    '#ptCard{padding:8px 10px 10px}',
    'body.pt-card #side>:not(#ptPH):not(#ptCard):not(#ptNav){display:none!important}',
    '.ptcd p{margin:0 0 8px;font:12.5px/1.5 Arial,sans-serif;color:var(--mu,#6b7785)}.ptcd p.ptcw{color:#b05000}',
    '.ptcd>button{display:block;width:100%;margin:0 0 6px;padding:7px 10px;font:600 12.5px Arial,sans-serif;cursor:pointer;border-radius:5px;border:1px solid var(--bd,#c9d2dc);background:var(--bg2,#fff)}',
    '.ptcd>button:disabled{opacity:.5;cursor:not-allowed}.ptcd .ptck{margin-top:8px;border-top:1px solid var(--bd,#e3e8ee);padding-top:8px}',
    '.ptcd .ptck button{display:block;width:100%;margin:0 0 4px;padding:6px 9px;text-align:left;font:12.5px Arial,sans-serif;cursor:pointer;border:0;background:none;color:var(--pr,#1f3a5f);border-radius:4px}',
    '.ptcd .ptck button:hover{background:var(--hv,#eef2f7)}',
    '.pti{flex:0 0 16px;width:16px;height:16px;color:var(--pr,#1f3a5f);display:inline-flex}.pti svg,#ptPH .pi2 svg{width:16px;height:16px}',
    /* Dulu lingkaran berangka (1..10). Pemilik meminta angka dalam lingkaran dihilangkan: nomor langkah
   tidak menambah informasi apa pun di atas urutan node yang memang sudah terlihat dari atas ke bawah,
   sedangkan statusnya tetap berguna. Jadi tinggal titik status, keterangannya di tooltip. */
    '.pts{flex:0 0 7px;height:7px;border-radius:50%;background:var(--pr,#1f3a5f);margin:0 5px 0 1px}',
    '.pts.done{background:#2f9e44}.pts.todo{background:transparent;box-shadow:inset 0 0 0 1.5px #9aa5b1}.pts.opt{background:#adb5bd}.pts.part{background:#f08c00}.pts.next{background:var(--pr,#1f3a5f);box-shadow:0 0 0 2px #f0c047}',
    '#ptNav{position:sticky;bottom:-14px;z-index:3;margin:14px -14px -14px;padding:6px 10px 8px;background:var(--bg,#f4f6f9);border-top:1px solid var(--bd,#d5dbe3)}',
    '#ptNav .pnl{display:block;font:700 10px/1.2 Arial,sans-serif;letter-spacing:.06em;text-transform:uppercase;color:var(--mu,#6b7785);margin-bottom:4px}',
    '#ptNav .pnb{display:flex;gap:6px;justify-content:space-between}#ptNav button{flex:1 1 0;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-size:11.5px}',
    '#ptNav button.nx{background:var(--pr,#1f3a5f)!important;color:#fff!important;border-color:var(--pr,#1f3a5f)!important}',
    '.ptl{flex:0 1 auto;min-width:0;overflow:hidden;text-overflow:ellipsis}',
    '.ptm{flex:0 0 auto;font-size:9.5px;font-weight:700;padding:0 5px;border-radius:8px;background:var(--pr,#1f3a5f);color:#fff;line-height:15px;text-transform:uppercase;letter-spacing:.03em}',
    '.ptn{flex:0 0 auto;margin-left:auto;font-size:10.5px;color:var(--mu,#6b7785);font-variant-numeric:tabular-nums;padding-left:6px}',
    '.ptx{all:unset;flex:0 0 18px;height:18px;border-radius:4px;color:var(--mu,#6b7785);display:inline-flex;align-items:center;justify-content:center;cursor:pointer;visibility:hidden}.ptx svg{width:14px;height:14px}',
    '.ptn+.ptx{margin-left:2px}.ptr .ptl+.ptx,.ptr .ptm+.ptx{margin-left:auto}.ptr:hover .ptx,.ptr.sel .ptx{visibility:visible}.ptx:hover{background:var(--bd,#d5dbe3);color:var(--tx,#1c2733)}',
    '.ptin{flex:1;min-width:60px;height:18px;font:inherit;padding:0 4px;border:1px solid var(--pr,#1f3a5f);border-radius:3px}',
    '#ptSplit{flex:0 0 5px;cursor:row-resize;background:var(--bg,#f4f6f9);border-top:1px solid var(--bd,#d5dbe3);border-bottom:1px solid var(--bd,#d5dbe3)}#ptSplit:hover,body.ptdrag #ptSplit{background:var(--pr,#1f3a5f)}',
    'body.ptdrag{cursor:row-resize!important;user-select:none}',
    '#ptPH{position:sticky;top:0;z-index:3;display:flex;align-items:center;gap:6px;height:28px;margin:0 -14px 8px;padding:0 8px 0 10px;background:var(--bg,#f4f6f9);border-bottom:1px solid var(--bd,#d5dbe3);white-space:nowrap}',
    '#ptPH .pp{flex:0 0 auto}#ptPH .pi2{display:inline-flex;color:var(--pr,#1f3a5f);margin-left:4px}#ptPH b{font-size:12px;overflow:hidden;text-overflow:ellipsis;min-width:0}#ptPH .ptx{visibility:visible;margin-left:auto}',
    '#ptOpen{position:absolute;left:0;top:50%;transform:translateY(-50%);z-index:7;width:16px;height:56px;padding:0;border:1px solid var(--bd,#c9d3de);border-left:0;border-radius:0 6px 6px 0;background:var(--sf,#fff);color:var(--pr,#1f3a5f);cursor:pointer;font-size:12px;display:none;pointer-events:auto}',
    '#ptMenu{position:fixed;z-index:9999;min-width:200px;max-width:320px;padding:4px 0;background:var(--sf,#fff);color:var(--tx,#1c2733);border:1px solid var(--bd,#9fb0c6);border-radius:6px;box-shadow:0 4px 0 rgba(16,24,40,.14);font-size:12px}',
    '#ptMenu .pmh{padding:4px 12px 5px;font-weight:700;font-size:11px;color:var(--mu,#6b7785);border-bottom:1px solid var(--bd,#d5dbe3);margin-bottom:3px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}',
    '#ptMenu .pmg{padding:5px 12px 2px;font-size:10px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;color:var(--mu,#6b7785)}',
    '#ptMenu button{all:unset;box-sizing:border-box;display:flex;align-items:center;gap:6px;width:100%;padding:4px 14px;cursor:pointer;white-space:nowrap}',
    '#ptMenu button:hover,#ptMenu button:focus{background:var(--ptsel)}#ptMenu button[disabled]{opacity:.45;cursor:default;background:none}',
    '#ptMenu button.dg{color:#c92a2a}#ptMenu .rd{width:10px;font-size:9px;color:var(--pr,#1f3a5f)}#ptMenu .pms{height:1px;margin:3px 0;background:var(--bd,#d5dbe3)}'].join('\n');
  (document.head||document.documentElement).appendChild(css);
})();
