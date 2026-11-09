/* ================= GC-Ex: panduan langkah (GC-Ex Block Model & GC-Ex Drillhole) =================
   1) Tombol NONAKTIF yang diklik -> kartu kecil di dekat tombol: kenapa belum aktif + tombol pintas ke langkah
      yang harus dikerjakan dulu.
   2) Pesan "belum ... / ... dulu" (alert) -> kotak panduan bergaya aplikasi dengan tombol pintas ke menu terkait.
      Pesan lain (galat, konfirmasi hasil) tetap memakai kotak pesan biasa.
   Tidak mengubah logika fungsi mana pun; hanya cara pemberitahuannya. */
(function(){if(window.GCG)return;var G=window.GCG={};
  var esc=function(s){return String(s==null?'':s).replace(/[&<>"]/g,function(c){return{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c];});};
  var css='.gcg-pop{position:fixed;z-index:100000;max-width:330px;background:var(--sf,#fff);color:var(--tx,#1c2733);border:1px solid var(--bd,#d9dee5);border-radius:9px;'+
    'box-shadow:0 14px 34px rgba(16,24,40,.26),0 3px 8px rgba(16,24,40,.14);padding:10px 12px 10px 12px;font:12px/1.45 "Segoe UI",Arial,sans-serif;animation:gcgIn .14s ease-out}'+
    '.gcg-pop:before{content:"";position:absolute;left:var(--ax,20px);width:10px;height:10px;background:inherit;border-left:1px solid var(--bd,#d9dee5);border-top:1px solid var(--bd,#d9dee5);transform:rotate(45deg)}'+
    '.gcg-pop.dn:before{top:-6px}.gcg-pop.up:before{bottom:-6px;transform:rotate(225deg)}'+
    '.gcg-h{display:flex;align-items:center;gap:7px;font-weight:700;color:var(--pr,#233a7e);margin-bottom:4px}.gcg-h svg{flex:none}'+
    '.gcg-b{color:var(--tx,#1c2733)}.gcg-a{display:flex;flex-wrap:wrap;gap:6px;margin-top:8px}'+
    '.gcg-a button{height:26px;padding:0 10px;border-radius:6px;border:1px solid var(--bd,#d9dee5);background:var(--sf2,#f5f7fa);color:var(--tx,#1c2733);font:600 11.5px "Segoe UI",Arial,sans-serif;cursor:pointer;'+
    'background-image:linear-gradient(180deg,rgba(255,255,255,.55),rgba(255,255,255,0) 55%,rgba(16,24,40,.06));box-shadow:0 1px 2px rgba(16,24,40,.12)}'+
    '.gcg-a button.go{background-color:var(--mj,var(--pr,#233a7e));color:var(--mjtx,#fff);border-color:transparent;background-image:linear-gradient(180deg,rgba(255,255,255,.26),rgba(255,255,255,.04) 48%,rgba(0,0,0,.10))}'+
    '.gcg-a button:active{transform:translateY(1px);box-shadow:inset 0 2px 4px rgba(0,0,0,.2)}'+
    '.gcg-bg{position:fixed;inset:0;z-index:99999;background:rgba(16,24,40,.28);display:flex;align-items:center;justify-content:center;animation:gcgFade .12s ease-out}'+
    '.gcg-dlg{width:min(460px,92vw);background:var(--sf,#fff);color:var(--tx,#1c2733);border-radius:11px;overflow:hidden;box-shadow:0 18px 44px rgba(16,24,40,.35),0 4px 10px rgba(16,24,40,.18);font:12.5px/1.5 "Segoe UI",Arial,sans-serif;animation:gcgIn .16s ease-out}'+
    '.gcg-dh{display:flex;align-items:center;gap:9px;padding:11px 14px;background:var(--top,#233a7e);color:var(--toptx,#fff);font-weight:700;font-size:13px;'+
    'background-image:linear-gradient(180deg,rgba(255,255,255,.12),rgba(0,0,0,.08));border-bottom:3px solid var(--ac,#f0c047)}'+
    '.gcg-db{padding:13px 16px 6px}.gcg-dlg .gcg-a{padding:6px 16px 14px;justify-content:flex-end}.gcg-dlg .gcg-a button{height:30px;padding:0 14px;font-size:12px}'+
    '@keyframes gcgIn{from{opacity:0;transform:translateY(4px)}to{opacity:1;transform:none}}@keyframes gcgFade{from{opacity:0}to{opacity:1}}'+
    'body.dark .gcg-a button{background-image:linear-gradient(180deg,rgba(255,255,255,.07),rgba(0,0,0,.15))}'+
    'body.dark .gcg-a button.go{color:var(--mjtx,#0e1621)}';
  var st=document.createElement('style');st.id='gcgCss';st.textContent=css;(document.head||document.documentElement).appendChild(st);
  var ICO='<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M12 16v-4M12 8h.01"/></svg>';
  /* ---------- navigasi (dipanggil hanya bila fungsinya ada di aplikasi ini) ---------- */
  var fn=function(n){return typeof window[n]==='function';};
  var go=function(tab,sec){return function(){try{if(fn('uiTab'))uiTab(tab);if(sec&&fn('uiSecSel'))setTimeout(function(){uiSecSel(sec[0],sec[1]);},60);}catch(e){console.warn(e);}};};
  var click=function(id){return function(){var e=document.getElementById(id);if(e)e.click();};};
  var has=function(id){return!!document.getElementById(id);};
  /* tombol pintas yang dikenali dari isi pesan */
  var ACT=[
    {re:/import block model|block model gc dulu|belum ada block model|buka block model/i,a:[['Import BM…',function(){if(fn('bxDlg'))bxDlg();else go('BM')();},function(){return fn('bxDlg')||fn('uiTab');}],['Buka Block Model',go('BM'),function(){return fn('uiTab');}]]},
    {re:/as-mined/i,a:[['Buka As-Mined',go('AM',['am','3']),function(){return fn('amPanel');}]]},
    {re:/dig block/i,a:[['Buka Dig block',go('BM',['bmp','2']),function(){return fn('dbPanel');}]]},
    {re:/horizontal|menu sayatan|sayatan aktif/i,a:[['Buka Sayatan',go('Slice'),function(){return fn('uiTab');}]]},
    {re:/folder proyek/i,a:[['Hubungkan folder proyek',function(){try{FP.pick();}catch(e){}},function(){return!!(window.FP&&FP.pick);}]]},
    {re:/wireframe|data referensi/i,a:[['Buka Data Referensi',go('Model'),function(){return fn('uiTab');}]]},
    {re:/geostatistik/i,a:[['Buka Geostatistik',click('gsBtn'),function(){return has('gsBtn');}]]},
    {re:/geological modelling|domain|solid vein/i,a:[['Buka Geological Modelling',go('GM'),function(){return has('rbGM');}]]},
    {re:/hasil estimasi|parameter estimasi/i,a:[['Buka Model Estimation',go('ME'),function(){return has('rbME');}]]},
    {re:/data drillhole|collar|assay|buka proyek dulu/i,a:[['Import data…',click('btnImp'),function(){return has('btnImp');}]]},
    {re:/titik rencana/i,a:[['Buka Plan Bor',go('Plan'),function(){return has('rbPlan');}]]},
    {re:/fitur digitasi|string kontrol|string yang ditampilkan/i,a:[['Buka Digitasi',go('Dig'),function(){return has('rbDig');}]]}];
  var acts=function(t){var out=[],seen={};ACT.forEach(function(x){if(x.re.test(t))x.a.forEach(function(a){if(!seen[a[0]]&&(!a[2]||a[2]())){seen[a[0]]=1;out.push(a);}});});return out.slice(0,2);};
  /* ---------- kotak panduan (pengganti alert bernada "belum / dulu") ---------- */
  G.close=function(){var d=document.getElementById('gcgDlg');if(d)d.remove();};
  G.dialog=function(msg,title,list){G.close();var A=list||acts(msg),d=document.createElement('div');d.id='gcgDlg';d.className='gcg-bg';
    d.innerHTML='<div class="gcg-dlg" role="dialog" aria-modal="true"><div class="gcg-dh">'+ICO+'<span>'+esc(title||'Langkah yang perlu dikerjakan dulu')+'</span></div><div class="gcg-db">'+esc(msg).replace(/\n/g,'<br>')+'</div>'+
      '<div class="gcg-a">'+A.map(function(a,i){return '<button type="button" data-i="'+i+'">'+esc(a[0])+'</button>';}).join('')+'<button type="button" class="go" data-ok="1">Mengerti</button></div></div>';
    d.addEventListener('click',function(e){var b=e.target.closest('button');if(e.target===d){G.close();return;}if(!b)return;G.close();if(b.getAttribute('data-i')!=null){try{A[+b.getAttribute('data-i')][1]();}catch(x){console.warn(x);}}});
    document.body.appendChild(d);setTimeout(function(){var b=d.querySelector('button.go');if(b)b.focus();},0);};
  G.isGuide=function(m){m=String(m||'');if(/gagal|galat|error|rusak|tidak dikenali|tidak didukung/i.test(m))return false;
    return /\b(belum|dulu|terlebih dahulu|butuh)\b/i.test(m)||/^\s*pilih\b/i.test(m);};
  var _alert=window.alert;
  window.alert=function(m){if(G.isGuide(m)&&document.body){try{G.dialog(String(m));return;}catch(e){}}return _alert.apply(window,arguments);};
  /* ---------- kartu kecil di dekat tombol nonaktif ---------- */
  G.popClose=function(){var p=document.getElementById('gcgPop');if(p)p.remove();};
  G.pop=function(el,title,msg,list){G.popClose();var r=el.getBoundingClientRect(),p=document.createElement('div');p.id='gcgPop';p.className='gcg-pop';
    p.innerHTML='<div class="gcg-h">'+ICO+'<span>'+esc(title)+'</span></div><div class="gcg-b">'+esc(msg)+'</div>'+(list&&list.length?'<div class="gcg-a">'+list.map(function(a,i){return '<button type="button" class="'+(i?'':'go')+'" data-i="'+i+'">'+esc(a[0])+'</button>';}).join('')+'</div>':'');
    document.body.appendChild(p);var W=window.innerWidth,H=window.innerHeight,pw=p.offsetWidth,ph=p.offsetHeight,x=Math.max(8,Math.min(W-pw-8,r.left+r.width/2-30)),below=r.bottom+ph+14<H;
    p.style.left=x+'px';p.style.top=(below?r.bottom+9:r.top-ph-9)+'px';p.classList.add(below?'dn':'up');p.style.setProperty('--ax',Math.max(10,Math.min(pw-20,r.left+r.width/2-x-5))+'px');
    p.addEventListener('click',function(e){var b=e.target.closest('button');if(!b)return;G.popClose();try{list[+b.getAttribute('data-i')][1]();}catch(x){console.warn(x);}});};
  /* alasan khusus per fungsi tombol (GC-Ex Block Model); selain itu dipakai keterangan tombol / pesan umum */
  var AMP=['Buka Poligon',go('AM',['am','3'])],AMH=['Buka Parameter',go('AM',['am','4'])];
  var WHY={
    amLyPreview:['Belum ada poligon as-mined yang dicentang dan sudah dihitung. Digit atau import boundary di Poligon, lalu klik Hitung.',[AMP,AMH]],
    amLyPdf:'amLyPreview',amRegCopy:'amLyPreview',amRegCsv:'amLyPreview',amStr:'amLyPreview',amAuditCsv:'amLyPreview',
    amPdf:['Belum ada hasil hitung as-mined. Buka Parameter lalu klik Hitung di flitch yang ingin dilaporkan.',[AMH]],amCsv:'amPdf',amCells:'amPdf',
    amMdl:['Export .mdl butuh block model resmi yang dibuka dari file Surpac .mdl dan hasil hitung as-mined.',[['Import BM…',function(){if(fn('bxDlg'))bxDlg();}],AMH]],
    amXlPlan:['Pilih workbook register dulu (tombol Pilih workbook…) dan pastikan ada poligon yang sudah dihitung.',[]],
    amXlSend:['Klik Periksa dulu: GC-Ex menunjukkan kolom yang diisi dan baris tujuan sebelum menulis ke workbook.',[]],
    dbDelSel:['Belum ada dig block yang dipilih. Centang kolom pertama di daftar, Ctrl+klik string di Penampang 2D, atau Shift+tarik kotak.',[]],
    dbPickAll:'dbDelSel',
    bxDlgGo:['Pilih file block model (.mdl / .csv) dulu, lalu atur filter.',[]]};
  var reason=function(b){var oc=b.getAttribute('onclick')||'',m=/^\s*([A-Za-z_$][\w$.]*)\s*\(/.exec(oc),k=m&&m[1].split('.').pop(),w=k&&WHY[k];if(typeof w==='string')w=WHY[w];
    if(!w&&b.id==='bxGo')w=WHY.bxDlgGo;
    if(!w&&b.id==='btnGo')w=['Import minimal satu data dulu (database drillhole atau block model / data spasial), lalu klik Tampilkan viewer.',[]];
    if(w)return{t:w[0],a:w[1]||[]};
    var t=(b.getAttribute('title')||'').trim();
    var wf=has('rail')&&/alur kerja/i.test((document.getElementById('rail')||{}).textContent||'');
    return{t:t||('Tombol ini aktif setelah langkah sebelumnya selesai.'+(wf?' Ikuti urutan Alur Kerja bernomor di rail kiri.':' Lengkapi isian / data di atasnya dulu.')),a:acts(t)};};
  document.addEventListener('pointerdown',function(e){var p=document.getElementById('gcgPop');if(p&&!p.contains(e.target))G.popClose();
    var b=e.target&&e.target.closest&&e.target.closest('button:disabled');if(!b||b.closest('.gcg-pop,.gcg-dlg'))return;var R=reason(b);
    G.pop(b,'Belum bisa dipakai',R.t,R.a);},true);
  document.addEventListener('keydown',function(e){if(e.key==='Escape'){if(document.getElementById('gcgDlg')){G.close();e.stopPropagation();}G.popClose();}},true);
  window.addEventListener('resize',G.popClose);document.addEventListener('scroll',G.popClose,true);
})();
