/* a58: penurunan TERKENDALI (pemilik, 23 Nov): area yang sudah dipilih / ditarik tidak bisa dipilih / ditarik lagi sebelum
   ▶ Jalankan ditekan — berlaku untuk Klik blok (a54) DAN Tarik jalur alat / Area gali (Pit Schedule lama).
   Jalur / area baru yang menimpa jalur / area yang BELUM dijalankan ditolak dengan pesan; sesudah Jalankan boleh ditarik lagi
   (lintasan berikutnya = bench di bawahnya). Tugas otomatis (Turun per bench, paralel, impor proyek) tidak dibatasi. */
const KDL={ran:new Set(),user:false};
function kdlBw(){return Math.min(+$('schbx').value||5,+$('schby').value||5);}
function kdlIn(t,x,y,pad){if(t.type==='poly')return schPip(t.pts,x,y)||schSeg(t.pts,x,y,true)[0]<=pad;const w=Math.max(1,t.nb|0)*kdlBw();return schSeg(t.pts,x,y,false)[0]<=w/2+pad;}
function kdlSamp(type,P,nb){const o=[],st=2;const n=P.length,cl=type==='poly';for(let i=0;i<n-(cl?0:1);i++){const a=P[i],b=P[(i+1)%n],L=Math.hypot(b[0]-a[0],b[1]-a[1]),k=Math.max(1,Math.ceil(L/st));for(let j=0;j<=k;j++)o.push([a[0]+(b[0]-a[0])*j/k,a[1]+(b[1]-a[1])*j/k]);}
 if(cl){let x0=1e18,x1=-1e18,y0=1e18,y1=-1e18;for(const p of P){x0=Math.min(x0,p[0]);x1=Math.max(x1,p[0]);y0=Math.min(y0,p[1]);y1=Math.max(y1,p[1]);}const s=Math.max(3,Math.sqrt((x1-x0)*(y1-y0)/4000));for(let x=x0;x<=x1;x+=s)for(let y=y0;y<=y1;y+=s)if(schPip(P,x,y))o.push([x,y]);}return o;}
/* tugas yang belum dijalankan dan bertumpuk dengan jalur / area baru */
function kdlClash(type,P,o){const pend=SCH.tasks.filter(t=>t.on&&!t._elev&&(t.type==='line'||t.type==='poly')&&!KDL.ran.has(t));if(!pend.length)return null;
 const nb=(o&&o.nb)||(typeof mbNs==='function'?mbNs():1),pad=type==='line'?Math.max(1,nb)*kdlBw()/2-0.5:-0.5;const S=kdlSamp(type,P,nb);
 for(const t of pend){let hit=0;for(const p of S)if(kdlIn(t,p[0],p[1],pad)){if(++hit>=2)return t;}}return null;}
{const _e=schDigEnd;schDigEnd=function(ok){const d=SCH.dig;KDL.user=!!(ok&&d&&(d.type==='line'||d.type==='poly'));try{return _e.apply(this,arguments);}finally{KDL.user=false;}};}
{const _a=schAdd;schAdd=function(type,P,o){if(KDL.user&&(type==='line'||type==='poly')&&!(typeof DMO!=='undefined'&&DMO.on)){KDL.user=false;const t=kdlClash(type,P,o);
  if(t){schMsg('&#9888; '+(type==='line'?'Jalur':'Area')+' ini menimpa <b>'+esc(t.nm)+'</b> yang belum dijalankan. Tekan <b>▶ Jalankan</b> dulu, baru area itu bisa ditarik / dipilih lagi (bench berikutnya).',1);try{schDrawStatic();}catch(_){}return null;}}
 return _a.apply(this,arguments);};}
/* klik blok lama (tugas sel; hanya tampil saat demo): blok yang sudah dipilih tapi belum dijalankan tidak bisa dipilih lagi */
/* Jalankan berhasil → semua tugas aktif tercatat sudah dijalankan */
{const _r=schRun;schRun=function(){const T=SCH.tasks.filter(t=>t.on);const r=_r.apply(this,arguments);const mark=()=>{try{if(SCH.sim)for(const t of T)KDL.ran.add(t);uxSync(true);}catch(_){}};if(r&&typeof r.then==='function')r.then(mark,()=>{});else mark();return r;};}
{const _x=schReset;schReset=function(){KDL.ran=new Set();return _x.apply(this,arguments);};}
try{window.__PS3.kdl={clash:(type,P,o)=>{const t=kdlClash(type,P,o);return t?t.nm:null;},ran:()=>KDL.ran.size,pend:()=>SCH.tasks.filter(t=>t.on&&!KDL.ran.has(t)).length};}catch(_){}
{const _u=schUnpack;schUnpack=function(){const r=_u.apply(this,arguments);try{for(const f of SCH.phs)if(f.sim)for(const t of (f.tasks||[]))if(t.on)KDL.ran.add(t);}catch(_){}return r;};}
