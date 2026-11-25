/* a76 · (24 Nov 2026, pemilik)
   1) "Submenu seperti Umum … apakah bisa di-hide salah satu atau keduanya? Berlaku juga untuk submenu lainnya"
      → tiap bar bagian (Umum, tiap objek di tab Data) bisa dilipat (klik bar; ▾/▸; diingat); kepala halaman di Properti
        (Pit Schedule, Desain baru › …, jendela edit) diklik = isi halaman dilipat.
   2) "Ukuran tulisan juga bisa diatur oleh user agar tercipta ruang yang lebih luas"
      → Tampilan → Ukuran tulisan ▸ (85 / 92 / 100 / 110 / 120 %): menu, bilah alat, Project Tree, Properti, status bar ikut
        mengecil/membesar (panel ikut menyempit → ruang 3D lebih luas). Diingat per komputer (psFz). */
(function(){const st=document.createElement('style');st.textContent=`
#pgw .pgs,#pgd .pgs{cursor:pointer;user-select:none}#pgw .pgs::before,#pgd .pgs>span::before{content:"▾";display:inline-block;width:12px;color:#6c757d;font-size:10px}
#pgw .pgs.cl::before,#pgd .pgs.cl>span::before{content:"▸"}#pgw .pgr.pgh0,#pgd .pgr.pgh0{display:none!important}
#pgw #pgh::before{display:none!important}#pgw.cl #pgb{display:block!important}
body.shx #dock>*>:first-child{cursor:pointer}
body.shx #dock>*>:first-child>b:first-of-type::before{content:"▾";display:inline-block;width:12px;color:#6c757d;font-size:10px;font-weight:400}
body.shx #dock>.pgcl>:first-child>b:first-of-type::before{content:"▸"}
body.shx #dock>.pgcl>:not(:first-child){display:none!important}
body.shx[data-fz] #side,body.shx[data-fz] #shL,body.shx[data-fz] #ptb,body.shx[data-fz] #mbar,body.shx[data-fz] #sbar{zoom:var(--ps-fz)}
`;document.head.appendChild(st);})();
/* ---------- 1. bagian bisa dilipat ---------- */
const PGC={set:new Set()};try{PGC.set=new Set(JSON.parse(localStorage.getItem('psPgC')||'[]'));}catch(_){}
function pgcKey(s){return (s.closest('#pgd')?'d:':'p:')+(s.querySelector('span')?s.querySelector('span').textContent:s.textContent).trim();}
function pgcApply(root){if(!root)return;for(const s of root.querySelectorAll('.pgs')){const cl=PGC.set.has(pgcKey(s));s.classList.toggle('cl',cl);for(let n=s.nextElementSibling;n&&n.classList.contains('pgr');n=n.nextElementSibling)n.classList.toggle('pgh0',cl);}}
document.addEventListener('click',e=>{const s=e.target.closest&&e.target.closest('#pgw .pgs,#pgd .pgs');if(s){const k=pgcKey(s);if(PGC.set.has(k))PGC.set.delete(k);else PGC.set.add(k);try{localStorage.setItem('psPgC',JSON.stringify([...PGC.set]));}catch(_){}pgcApply(s.parentElement);try{dispatchEvent(new Event('resize'));}catch(_){}return;}
 /* kepala halaman di Properti */
 const d=$('dock');if(!d||!document.body.classList.contains('shx'))return;const t=e.target;if(!t.closest||!d.contains(t)||t.closest('button,select,input,label,a,summary'))return;
 for(const pg of d.children){const h=pg.firstElementChild;if(h&&h.contains(t)&&pg.children.length>1){pg.classList.toggle('pgcl');h.title=pg.classList.contains('pgcl')?'Klik: buka isi halaman':'Klik: lipat isi halaman';return;}}});
{const _a=pgDraw;pgDraw=function(){const r=_a.apply(this,arguments);try{pgcApply($('pgb'));const h=$('pgh');if(h){h.onclick=null;h.style.cursor='default';h.title='';}const w=$('pgw');if(w)w.classList.remove('cl');}catch(_){}return r;};}
{const _b=pgdDraw;pgdDraw=function(){const r=_b.apply(this,arguments);try{pgcApply($('pgd'));}catch(_){}return r;};}
/* ---------- 2. ukuran tulisan ---------- */
const FZ={v:100,opt:[[85,'Kecil'],[92,'Agak kecil'],[100,'Normal'],[110,'Besar'],[120,'Sangat besar']]};try{FZ.v=+localStorage.getItem('psFz')||100;}catch(_){}
function fzSet(v){FZ.v=FZ.opt.some(o=>o[0]===v)?v:100;try{localStorage.setItem('psFz',String(FZ.v));}catch(_){}const b=document.body;if(FZ.v===100){delete b.dataset.fz;b.style.removeProperty('--ps-fz');}else{b.dataset.fz=FZ.v;b.style.setProperty('--ps-fz',String(FZ.v/100));}
 try{shLayout();}catch(_){}setTimeout(()=>{try{shLayout();tbFit();lgPlace();}catch(_){}},60);}
function fzMenu(){return [{hd:'Ukuran tulisan antarmuka'}].concat(FZ.opt.map(o=>({t:o[1]+' · '+o[0]+'%',on:()=>FZ.v===o[0],fn:()=>fzSet(o[0])})),['-',{hd:'Lebih kecil = ruang 3D lebih luas'}]);}
function fzBtn(){if($('mbfz'))return;const ref=$('mbpal');if(!ref)return;const b=document.createElement('button');b.id='mbfz';b.className='mbb';b.textContent='Ａ Ukuran tulisan';b.title='Perkecil / perbesar tulisan menu, bilah alat, Project Tree dan Properti';b.onclick=()=>cmOpen(b,fzMenu());ref.after(b);try{if(!CASC_ID.includes('mbfz'))CASC_ID.push('mbfz');}catch(_){}}
setInterval(()=>{try{fzBtn();}catch(_){}},1500);setTimeout(()=>{try{fzBtn();if(FZ.v!==100)fzSet(FZ.v);}catch(_){}},200);
try{window.__PS3.fz={set:fzSet,get:()=>FZ.v};window.__PS3.pgc={keys:()=>[...PGC.set]};}catch(_){}
