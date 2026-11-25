/* a79 · sisa kerapian (24 Nov 2026, pemilik: "Bereskan!")
   - Ukuran tulisan berlaku juga untuk jendela mengambang, Legenda, menu anak (isi jendela diperkecil; ukuran jendela tetap).
   - Baris padat (≥ 2 kotak angka) tidak turun baris: kotak angka menyusut (min 34 px), kolom label dipersempit.
   - Mode Edit pit: baris isian jendela edit (.mwr / .row / label+input) ikut kisi. */
(function(){const st=document.createElement('style');st.textContent=`
body.shx[data-fz] .flw:not(.docked):not(.dkd)>*,body.shx[data-fz] #schw:not(.dkd)>*,body.shx[data-fz] body>.cmenu>*,body.shx[data-fz] .cmenu>*{zoom:var(--ps-fz)}
body.shx #dock .r.pgx:has(>.pgv.pgm)>.pgl{flex:0 0 24%!important}
body.shx #dock .r.pgx>.pgv.pgm{flex-wrap:nowrap!important;white-space:nowrap;font-size:11.5px}
body.shx #dock .r.pgx>.pgv.pgm>input[type=number]{flex:1 1 34px!important;width:34px!important;min-width:30px;max-width:62px;padding-left:3px!important;padding-right:1px!important}
body.shx #dock .r.pgx>.pgv.pgm>button{padding-left:5px!important;padding-right:5px!important}
body.shx #dock .r.pgx>.pgv.pgm.pgw2{flex-wrap:wrap!important;white-space:normal}
`;document.head.appendChild(st);})();
/* baris yang tetap terlalu panjang (catatan panjang di dalam nilai) boleh turun baris */
{const _w=pgxWrap;pgxWrap=function(root){const r=_w.apply(this,arguments);try{for(const v of root.querySelectorAll('.r.pgx>.pgv.pgm:not(.pgq)')){v.classList.add('pgq');let n=0;for(const c of v.childNodes)if(c.nodeType===3)n+=c.nodeValue.trim().length;else if(c.tagName==='SPAN'||c.tagName==='LABEL')n+=c.textContent.trim().length;if(n>34)v.classList.add('pgw2');}}catch(_){}return r;};}
/* baris .fl dengan ≥ 2 kotak angka (mis. Edit Otomatis 6: "Muka bench … izin … – …", "Berm … m tiap … bench") → label 50 % | nilai */
(function(){const st=document.createElement('style');st.textContent=`
body.shx #dock .fl.pgf>.pgl{flex:0 0 calc(50% - 6px);color:#495057}
body.shx #dock .fl.pgf>.pgv{flex:1 1 auto;min-width:0;display:flex;align-items:center;gap:4px;white-space:nowrap}
body.shx #dock .fl.pgf>.pgv>input[type=number]{flex:1 1 34px!important;width:34px!important;min-width:30px;max-width:60px;margin:0!important}
`;document.head.appendChild(st);})();
{const _w=pgxWrap;pgxWrap=function(root){try{for(const r of root.querySelectorAll('.fl:not(.pgf):not(.pgfn)')){const f=r.firstChild;if(!f||f.nodeType!==3||r.querySelectorAll(':scope > input[type=number]').length<2){r.classList.add('pgfn');continue;}const t=f.nodeValue.replace(/\s+/g,' ').trim();if(t.length<2||t.length>30){r.classList.add('pgfn');continue;}
   const l=document.createElement('span');l.className='pgl';const v=document.createElement('span');v.className='pgv';l.appendChild(f);while(r.firstChild)v.appendChild(r.firstChild);r.appendChild(l);r.appendChild(v);r.classList.add('pgf');}}catch(e){console.warn('flwrap',e);}return _w.apply(this,arguments);};}
