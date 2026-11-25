/* a72 · Properti: isi langkah sebagai KISI label | nilai + tab DATA (24 Nov 2026, pemilik: "Ya, lanjutkan keduanya")
   - Formulir desain (.pg label, .fl) dan baris jadwal (.r) tampil sebagai baris kisi: label kiri, nilai kanan, garis tipis.
   - Baris .r yang diawali teks pendek dibungkus (teks → .pgl, sisanya → .pgv); elemen dipindah, bukan disalin (handler tetap).
   - Tab DATA di sebelah PROPERTI: ringkasan data yang dimuat (topografi, block model, pit final impor, desain). */
(function(){const st=document.createElement('style');st.textContent=`
body.shx #dock .pg{display:block!important;margin:4px 0!important;border-top:1px solid #E7E3DA}
body.shx #dock .pg>label{display:flex!important;flex-direction:row!important;align-items:center;gap:6px;min-height:25px;padding:1px 0 1px 2px;border-bottom:1px solid #E7E3DA;font-size:12px!important;color:#495057}
body.shx #dock .pg>label>span{margin-left:auto;flex:0 0 50%;display:flex;align-items:center;gap:4px;color:#1C2733}
body.shx #dock .pg>label>span>input,body.shx #dock .pg>label>span>select{flex:1 1 auto;min-width:0;width:auto!important}
body.shx #dock .fl{min-height:25px;margin:0!important;padding:1px 0 1px 2px;border-bottom:1px solid #E7E3DA;font-size:12px}
body.shx #dock .fl>input[type=number]:first-of-type,body.shx #dock .fl>select:first-of-type{margin-left:auto}
body.shx #dock .r.pgx{flex-wrap:nowrap!important;align-items:center;gap:6px;min-height:25px;margin:0!important;padding:1px 0 1px 2px;border-bottom:1px solid #E7E3DA}
body.shx #dock .r.pgx>.pgl{flex:0 0 31%;color:#495057;font-size:12px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
body.shx #dock .r.pgx>.pgv{flex:1 1 auto;min-width:0;display:flex;flex-wrap:wrap;align-items:center;gap:3px 6px;color:#1C2733}
body.shx #side>.shph>span.tabx{background:transparent;border-top:2px solid transparent;font-weight:600;color:#5C6672;cursor:pointer}
body.shx #side>.shph>span{cursor:pointer}
body.shx.pg-data #side>.shph>span.tab0{background:transparent;border-top-color:transparent;font-weight:600;color:#5C6672}
body.shx.pg-data #side>.shph>span.tabx{background:#F7F5F0;border-top:2px solid #2B5F9E;font-weight:700;color:#1C2733}
body.shx #side>#pgd:not(#dock):not(#shpe):not(.shph):not(.x1){display:none!important}
body.shx.pg-data #side>#pgd:not(#dock):not(#shpe):not(.shph):not(.x1){display:block!important;flex:1 1 auto;overflow:auto;min-height:0;background:#F7F5F0;font-size:12px}
body.shx.pg-data #side>#pgw:not(#dock):not(#shpe):not(.shph):not(.x1),body.shx.pg-data #side>#dock,body.shx.pg-data #side>#shpe{display:none!important}
#pgd .pgt{display:flex;align-items:baseline;gap:8px;padding:6px 10px 5px}#pgd .pgt b{font-size:13px;color:#1C2733;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}#pgd .pgt span{margin-left:auto;color:#6c757d;font-size:11px;white-space:nowrap}
#pgd .pgs{background:#EDEBE6;border-top:1px solid #D3CDC1;border-bottom:1px solid #D3CDC1;padding:3px 10px;font-weight:700;font-size:11px;color:#1C2733;display:flex;gap:6px}#pgd .pgs i{margin-left:auto;font-style:normal;font-weight:400;color:#6c757d}
#pgd .pgr{display:flex;border-bottom:1px solid #E7E3DA;min-height:22px;align-items:center}
#pgd .pgr>span{flex:0 0 42%;padding:2px 6px 2px 10px;color:#495057;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}#pgd .pgr>b{flex:1;font-weight:400;color:#1C2733;padding:2px 8px 2px 4px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
#pgd .pga{display:flex;gap:6px;padding:8px 10px;flex-wrap:wrap}#pgd .pge{padding:8px 10px;color:#6c757d}
`;document.head.appendChild(st);})();

/* ---------- baris .r → kisi ---------- */
function pgxWrap(root){for(const r of root.querySelectorAll('.r:not(.pgx):not(.pgn)')){const f=r.firstChild;
  if(!f||f.nodeType!==3||r.children.length===0||!r.querySelector('input,select')){r.classList.add('pgn');continue;}
  const t=f.nodeValue.replace(/\s+/g,' ').trim();if(t.length<2||t.length>24||r.closest('details#schadv2,.plnote')){r.classList.add('pgn');continue;}
  const l=document.createElement('span');l.className='pgl';l.title=t;const v=document.createElement('span');v.className='pgv';l.appendChild(f);while(r.firstChild)v.appendChild(r.firstChild);r.appendChild(l);r.appendChild(v);r.classList.add('pgx');}}
let PGXT=0;function pgxSoon(){if(PGXT)return;PGXT=requestAnimationFrame(()=>{PGXT=0;try{if(document.body.classList.contains('shx')){const d=$('dock');if(d)pgxWrap(d);}}catch(e){console.warn('pgx',e);}});}
try{const d=$('dock');if(d)new MutationObserver(pgxSoon).observe(d,{childList:true,subtree:true});}catch(_){}
setInterval(pgxSoon,1500);

/* ---------- tab DATA ---------- */
const PGD={on:false,sig:''};
function pgdExt(s){if(s._pgx&&s._pgx.L===s.L)return s._pgx;let n=0,x0=1e18,x1=-1e18,y0=1e18,y1=-1e18,z0=1e18,z1=-1e18;for(const l of s.L||[])for(const p of l){n++;if(p[0]<x0)x0=p[0];if(p[0]>x1)x1=p[0];if(p[1]<y0)y0=p[1];if(p[1]>y1)y1=p[1];if(p[2]<z0)z0=p[2];if(p[2]>z1)z1=p[2];}
 return s._pgx={L:s.L,n,x0,x1,y0,y1,z0,z1};}
function pgdData(){const S=[];const nm=s=>String(s||'').replace(/^[0-9a-f]{8}-/,'');
 TP.forEach(s=>{const e=pgdExt(s),R=[['Status',s.on?'aktif':'mati']];if((s.L||[]).length!==e.n)R.push(['String',(s.L||[]).length.toLocaleString('id-ID')]);R.push(['Titik',e.n.toLocaleString('id-ID')]);
  if(e.n){R.push(['Easting',nf(e.x0)+' – '+nf(e.x1)],['Northing',nf(e.y0)+' – '+nf(e.y1)],['RL',f1(e.z0)+' – '+f1(e.z1)],['Luas bentang',nf((e.x1-e.x0)*(e.y1-e.y0)/1e4,1)+' ha']);}
  S.push({h:nm(s.nm),t:'Topografi',R});});
 try{if(GT.file){const R=[['Berkas',GT.file.name],['Atribut kadar',GT.attr||'—'],['Atribut SG',GT.sg||('tetap '+GT.sgc)]];try{const m=GT.m;const n=m&&(m.n||(m.z&&m.z.length));if(n)R.push(['Jumlah blok',Number(n).toLocaleString('id-ID')]);}catch(_){}
   try{R.push(['Kelas kadar',GT.rules.map(r=>r.m+' '+r.lo+(r.hi!==''?'–'+r.hi:'+')).join(' · ')]);}catch(_){}S.push({h:GT.file.name,t:'Block model',R});}}catch(_){}
 try{if(FIN)S.push({h:nm(FIN.nm)||'Pit final impor',t:'Batas final',R:[['String',(FIN.S||FIN.L||[]).length||'—'],['RL puncak',isFinite(FIN.zmax)?f1(FIN.zmax):'—']]});}catch(_){}
 const vol=R=>{try{return R&&R.vol&&R.vol.tot?nf(R.vol.tot)+' m³':'—';}catch(_){return '—';}};
 try{if(RES)S.push({h:'Pit final',t:'Desain',R:[['Bench',RES.B?RES.B.length:'—'],['Volume',vol(RES)],['String',RES.S?RES.S.length:'—']]});}catch(_){}
 try{if(STG)S.push({h:'Staging',t:'Desain',R:[['Bench',STG.B?STG.B.length:'—'],['Volume',vol(STG)],['String',STG.S?STG.S.length:'—']]});}catch(_){}
 return S;}
function pgdDraw(force){const el=$('pgd');if(!el||!PGD.on)return;let S;try{S=pgdData();}catch(e){return;}const sg=JSON.stringify(S);if(!force&&sg===PGD.sig)return;PGD.sig=sg;
 el.innerHTML='<div class="pgt"><b>Data project</b><span>'+S.length+' objek</span></div>'+(S.length?S.map(s=>'<div class="pgs"><span>'+esc(s.h)+'</span><i>'+esc(s.t)+'</i></div>'+s.R.map(r=>'<div class="pgr"><span>'+esc(r[0])+'</span><b title="'+esc(String(r[1]))+'">'+esc(String(r[1]))+'</b></div>').join('')).join(''):'<div class="pge">Belum ada data. Impor topografi (.str / .dxf) atau muat block model (.mdl).</div>')+
  '<div class="pga"><button data-d="imp">&#8679; Impor topografi…</button><button data-d="bm">&#9638; Block model (.mdl)…</button></div>';}
function pgdSet(on){PGD.on=!!on;document.body.classList.toggle('pg-data',PGD.on);if(PGD.on)pgdDraw(true);}
function pgdInit(){const side=$('side');if(!side||$('pgd'))return;const ph=side.querySelector(':scope > .shph');if(!ph)return;const a=ph.querySelector('span');if(!a)return;a.classList.add('tab0');
 const b=document.createElement('span');b.className='tabx';b.textContent='Data';a.after(b);a.onclick=()=>pgdSet(false);b.onclick=()=>pgdSet(true);
 const d=document.createElement('div');d.id='pgd';side.appendChild(d);d.addEventListener('click',e=>{const x=e.target.closest('button[data-d]');if(!x)return;pgdSet(false);try{shAct(x.dataset.d);}catch(_){}});}
/* membuka halaman apa pun (pohon, menu) → kembali ke tab Properti */
{const _w=winShow;winShow=function(w,on){if(on!==false&&PGD.on&&w&&w.id!=='tdw')pgdSet(false);return _w.apply(this,arguments);};}
{const _o=schOpen;schOpen=function(on){if(on&&PGD.on)pgdSet(false);return _o.apply(this,arguments);};}
setInterval(()=>{try{pgdInit();pgdDraw();}catch(_){}},900);try{pgdInit();}catch(_){}
try{window.__PS3.pgd={set:pgdSet,data:()=>pgdData(),wrapped:()=>document.querySelectorAll('#dock .r.pgx').length};}catch(_){}
