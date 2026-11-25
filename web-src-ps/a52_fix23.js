/* a52: perbaikan pemakaian 23 Nov 2026 (pemilik):
   1. Panel Properti (kanan) dan Project Tree (kiri) bisa DIGESER lebarnya — tarik garis tepinya; lebar diingat.
   2. "Rekomendasi sistem" tidak lagi muncul sendiri setiap kali tampilan berganti: hanya sekali untuk tiap hasil desain baru.
   3. Masuk tab Edit tanpa pit → halaman "Pilih pit untuk diedit": Pit final (Desain baru), Staging, Pit final impor, atau impor file.
   4. Impor DXF permukaan (3DFACE) — mis. "…_permukaan_akhir.dxf" hasil ekspor Pit Studio / Surpac — sebagai topografi.
   5. Perdalam / sump pada pit final yang diedit tidak dibatasi "Pit final impor" (batas itu hanya untuk staging). */
/* ---- 1. lebar panel ---- */
(function(){const st=document.createElement('style');st.textContent='.shrz{position:absolute;top:0;bottom:0;width:7px;cursor:col-resize;z-index:30;background:transparent}.shrz:hover,.shrz.on{background:rgba(43,95,158,.35)}';document.head.appendChild(st);
 {const s2=document.createElement('style');s2.textContent='body.shx #dock>.flw.docked{width:auto!important;max-width:none!important;min-width:0!important;left:auto!important;right:auto!important;align-self:stretch!important;box-sizing:border-box}body.shx #dock>.flw.docked .flb{max-width:none!important}';document.head.appendChild(s2);}
 const mk=(id,side,key,min,max)=>{const el=$(id);if(!el)return;if(getComputedStyle(el).position==='static')el.style.position='relative';const h=document.createElement('div');h.className='shrz';h.style[side==='L'?'left':'right']='0';h.title='Tarik untuk mengubah lebar panel (klik ganda = lebar bawaan)';el.appendChild(h);
  const set=w=>{w=Math.max(min,Math.min(max,Math.round(w)));el.style.setProperty('width',w+'px','important');el.style.setProperty('flex','0 0 '+w+'px','important');try{localStorage.setItem(key,w);}catch(_){}try{window.dispatchEvent(new Event('resize'));}catch(_){}};
  try{const w=+localStorage.getItem(key);if(w>0)set(w);}catch(_){}
  h.addEventListener('pointerdown',e=>{e.preventDefault();h.classList.add('on');h.setPointerCapture(e.pointerId);const r=el.getBoundingClientRect();const mv=ev=>set(side==='L'?r.right-ev.clientX:ev.clientX-r.left);const up=()=>{h.classList.remove('on');h.removeEventListener('pointermove',mv);h.removeEventListener('pointerup',up);};h.addEventListener('pointermove',mv);h.addEventListener('pointerup',up);});
  h.addEventListener('dblclick',()=>{el.style.removeProperty('width');el.style.removeProperty('flex');try{localStorage.removeItem(key);}catch(_){}window.dispatchEvent(new Event('resize'));});};
 mk('side','L','psSideW',300,Math.max(420,innerWidth*0.6));mk('shL','R','psTreeW',180,520);})();
/* ---- 2. rekomendasi sekali per hasil ---- */
{const SEEN=new WeakSet(),_w=winShow;winShow=function(w,on){try{if(w&&w.id==='tdw'&&on===true&&!(typeof DMO!=='undefined'&&DMO.on)&&!window.__TDWFORCE){let R=null;try{R=curR();}catch(_){}if(R){if(SEEN.has(R))return;SEEN.add(R);}}}catch(_){}return _w.apply(this,arguments);};
 document.addEventListener('click',e=>{if(e.target&&e.target.id==='tdwo'){window.__TDWFORCE=1;setTimeout(()=>{window.__TDWFORCE=0;},50);}},true);}
/* ---- 3. pilih pit untuk diedit ---- */
function epwFill(){const b=$('epwb');if(!b)return;const it=[];if(RES)it.push(['res','▲ Pit final (Desain baru)',RES]);if(STG)it.push(['stg','▤ Staging',STG]);if(FIN&&FIN.S&&FIN.S.length)it.push(['fin','⬚ Pit final impor — '+String(FIN.nm||'').replace(/^[0-9a-f]{8}-/,''),null]);
 b.innerHTML='<div class="hint" style="margin-bottom:6px">Pilih desain yang mau diubah (perdalam / sump, push back, Play-Doh, edit manual). Desain aslinya tidak berubah sampai hasil edit disimpan.</div>'+(it.length?it.map(q=>'<button class="pri" data-ep="'+q[0]+'" style="display:block;width:100%;margin:3px 0;text-align:left">'+esc(q[1])+'</button>').join(''):'<div class="info">Belum ada desain di proyek ini.</div>')+'<button data-ep="file" style="display:block;width:100%;margin:6px 0 0">&#8679; Impor pit jadi dari file (.str / .dxf)</button>';
 b.querySelectorAll('[data-ep]').forEach(x=>x.onclick=()=>{const k=x.dataset.ep;try{if(k==='file'){$('epf').click();}else{const R0=k==='res'?RES:k==='stg'?STG:null,src=k==='fin'?FIN.S:R0.S,L=src.map(s=>s.pts.map(p=>p.slice()));edLoad(L,k==='res'?'Hasil pit final ('+$('pjn').textContent+')':k==='stg'?'Hasil staging ('+$('pjn').textContent+')':'Pit final impor ('+String(FIN.nm||'').replace(/^[0-9a-f]{8}-/,'')+')',R0);if(ED)ED.fromRes=k==='stg'?'stage':k==='res'?'new':'fin';}winShow($('epw'),false);try{edSum();}catch(_){}}catch(e){alert(e.message);}});}
{const _c=clickMode;clickMode=function(m){const r=_c.apply(this,arguments);try{if(m==='edit')setTimeout(epwMaybe,60);}catch(_){}return r;};}
function epwMaybe(){if(MODE!=='edit'||ED||(typeof DMO!=='undefined'&&DMO.on))return;if(!(RES||STG||(FIN&&FIN.S&&FIN.S.length)))return;epwFill();winShow($('epw'),true);}
document.querySelectorAll('#mode button[data-m="edit"]').forEach(b=>b.addEventListener('click',()=>setTimeout(epwMaybe,80)));
/* tombol lama "Pakai hasil Desain baru" juga membuka pilihan bila lebih dari satu sumber */
try{const ef=$('efrom');if(ef){const old=ef.onclick;ef.onclick=e=>{const n=(RES?1:0)+(STG?1:0)+(FIN&&FIN.S&&FIN.S.length?1:0);if(n>1){epwFill();winShow($('epw'),true);}else old&&old(e);};}}catch(_){}
/* ---- 4. DXF 3DFACE ---- */
{const _tp=topoParse;topoParse=function(txt,nm){const L=_tp(txt,nm);try{if((/\.dxf$/i.test(nm)||/^\s*0\s*[\r\n]+\s*SECTION/i.test(txt))&&/\n\s*3DFACE\s*\r?\n/.test(txt)){const t=txt.split(/\r?\n/);let f=null,n=0;
  const put=()=>{if(!f)return;const P=[];for(let k=0;k<4;k++){const q=f[k];if(q&&q.every(isFinite))P.push(q);}if(P.length>=3){if(P.length===4&&Math.hypot(P[3][0]-P[2][0],P[3][1]-P[2][1],P[3][2]-P[2][2])<1e-6)P.pop();P.push(P[0].slice());L.push(P);n++;}f=null;};
  for(let i=0;i+1<t.length;i+=2){const c=t[i].trim(),v=t[i+1].trim();if(c==='0'){put();if(v==='3DFACE')f=[[NaN,NaN,NaN],[NaN,NaN,NaN],[NaN,NaN,NaN],null];continue;}if(!f)continue;const cc=+c;if(cc>=10&&cc<=13){const k=cc-10;f[k]=f[k]||[NaN,NaN,NaN];f[k][0]=+v;}else if(cc>=20&&cc<=23){const k=cc-20;f[k]=f[k]||[NaN,NaN,NaN];f[k][1]=+v;}else if(cc>=30&&cc<=33){const k=cc-30;f[k]=f[k]||[NaN,NaN,NaN];f[k][2]=+v;}}put();}}catch(e){console.warn('3DFACE',e);}return L;};}
/* ---- 5. perdalam / sump dengan kedalaman bukan kelipatan tinggi bench (mis. lantai 240 → 230 pada bench 15 m) ----
   Dulu: satu bench penuh 15 m tidak muat di atas RL target → "RL bawah tidak tercapai". Sekarang tinggi bench di bawah lantai lama
   dibagi rata supaya tepat sampai RL target (10 m → 1 bench 10 m; 25 m pada bench 15 m → 2 bench 12,5 m). Bench di atas lantai lama tetap. */
{const _rd=runDeepen;runDeepen=function(f,zt){let H2=NaN;try{const p=prmAt(f.z-0.01),d=f.z-zt,n=Math.max(1,Math.ceil(d/p.H-1e-6));H2=d/n;if(Math.abs(H2-p.H)<0.01)H2=NaN;}catch(_){}
 if(!isFinite(H2))return _rd.apply(this,arguments);const _p=prmAt;prmAt=function(z){const q=_p.apply(this,arguments);if(z<f.z+0.01){const r=Object.assign({},q);r.H=H2;r.a=H2/Math.tan(Math.min(r.A,88.9)*Math.PI/180);return r;}return q;};
 try{const r=_rd.apply(this,arguments);try{const e=$('edres');if(e&&!/Gagal/.test(e.textContent))e.insertAdjacentHTML('beforeend','<div class="hint">Tinggi bench di bawah lantai lama disesuaikan '+f1(H2)+' m agar tepat sampai RL '+f1(zt)+'.</div>');}catch(_){}return r;}finally{prmAt=_p;}};}
/* pesan gagal di tab Edit: batas pit final impor tidak berlaku di sini */
{const _rd=runDeepen;runDeepen=function(){try{return _rd.apply(this,arguments);}catch(e){if(MODE==='edit'&&e&&e.message)e.message=e.message.replace(' atau sudah di luar batas pit final','')+' Saran: perlebar poligon sump, kecilkan "lantai min", atau pilih RL lantai baru yang lebih dangkal.';throw e;}};}
