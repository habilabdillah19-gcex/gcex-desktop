/* a68: PENJADWALAN OTOMATIS — logika teknik tambang (pilihan pemilik 24 Nov, butir 1·2·3·4 + SR 90%):
   1) TARGET SEBAGAI RENTANG per periode: ore min–maks (kapasitas pabrik), kadar min–maks (blending), SR maks yang wajib
      tercapai di ≥ N % periode (bawaan 90 %), SR diratakan antar-periode (opsional), BCM maks.
   2) PENGUPASAN LEBIH DULU: stok ore terbuka (ore pada blok yang sudah boleh digali) dijaga ≥ n periode kebutuhan ore;
      bila kurang, waste yang menutup ore didahulukan.
   3) BEBERAPA FLEET: tiap fleet punya peran (semua / ore / waste) dan kapasitas sendiri; dua fleet tidak bekerja berdekatan
      dalam periode yang sama (jarak aman dalam jumlah blok).
   4) URUTAN FISIK: blok baru boleh digali bila blok di atasnya habis; beda bench antar kolom tetangga ≤ n (lereng kerja).
   Titik muat DINAMIS: blok berikutnya dipilih dari semua blok yang boleh digali menurut kebutuhan periode (bukan menyisir
   berurutan); perpindahan jauh diberi penalti kecil. Bila SR maks tidak lagi bisa dicapai (melebihi jatah meleset), sistem
   BERHENTI dan memberi tahu: periode berapa, SR sisa cadangan, dan sarannya.
   Mode manual (Klik blok) tidak berubah. */
function apDef(c){const t=c.tg,s=c.sq;if(t.oremax===undefined)t.oremax=0;if(t.gmax===undefined)t.gmax=0;if(t.srpct===undefined)t.srpct=90;if(t.lvl===undefined)t.lvl=true;
 if(s.maxd===undefined)s.maxd=2;if(s.expo===undefined)s.expo=2;if(s.sep===undefined)s.sep=2;if(s.smart===undefined)s.smart=true;return c;}
{const _c=plCfg;plCfg=function(){return apDef(_c.apply(this,arguments));};}
function apRun(){const X=plBlocks();if(!X)throw new Error('Belum ada blok tambang — buka Pit Schedule, gambar Batas fase, lalu hitung Blok tambang.');
 const c=plCfg(),sq=c.sq,tg=c.tg,F=plFleets(),cal=plCal(c.cal.t==='shift'?5000:c.cal.t==='hari'?3000:c.cal.t==='minggu'?600:150);
 const caps=F.map(plFcap);if(!caps.some(v=>v>0))throw new Error('Kapasitas fleet 0 — atur unit di Pengaturan unit.');
 const B=X.B,M=X.byKey,done=new Map(),rem=new Map(),part=new Map(),fleetOf=new Map();
 /* kolom (s|b) → daftar blok urut bench atas → bawah */
 const COL=new Map();for(const o of B){const k=o.s+'|'+o.b;(COL.get(k)||COL.set(k,[]).get(k)).push(o);}for(const a of COL.values())a.sort((p,q)=>q.k-p.k);
 const top=new Map();/* indeks blok teratas yang belum habis per kolom */for(const k of COL.keys())top.set(k,0);
 const topK=k=>{const a=COL.get(k);if(!a)return null;const i=top.get(k);return i<a.length?a[i].k:-1e9;};
 const maxd=Math.max(1,sq.maxd|0),sep=Math.max(0,sq.sep|0);
 /* boleh digali: blok teratas kolomnya + sesudah digali beda bench dengan kolom tetangga ≤ maxd */
 const avail=o=>{const ck=o.s+'|'+o.b,a=COL.get(ck),i=top.get(ck);if(!a||a[i]!==o)return false;for(const [ds,db] of [[1,0],[-1,0],[0,1],[0,-1]]){const t=topK((o.s+ds)+'|'+(o.b+db));if(t===null)continue;if(t-(o.k-1)>maxd)return false;}return true;};
 const oreBelow=(o,D)=>{const a=COL.get(o.s+'|'+o.b),i=a.indexOf(o);let t=0;for(let j=i+1;j<a.length&&j<=i+D;j++)t+=a[j].ore||0;return t;};
 const P=cal.map((q,p)=>({p,lab:q.lab,shifts:q.shifts,d0:q.d0,d1:q.d1,cap:caps.reduce((a,v)=>a+v,0)*q.shifts,fc:caps.map(v=>v*q.shifts),fu:caps.map(()=>0),blocks:[],vol:0,ore:0,met:0,wv:0,wt:0,viol:0,pos:caps.map(()=>[])}));
 let totV=0,totO=0,totW=0;for(const o of B){totV+=o.vol;totO+=o.ore||0;totW+=(o.wv!=null?o.wv:o.vol);}
 const perCap=P.length?P[0].cap||1:1,estN=Math.max(1,Math.ceil(totV/Math.max(1,perCap))),pct=Math.max(0,Math.min(100,tg.srpct||0)),allow=tg.srmax>0?Math.floor(estN*(100-pct)/100+1e-9):1e9;
 const role=i=>F[i].role||'any',last=caps.map(()=>null);
 const fleetFor=(o,P0,isOre)=>{let bi=-1,bs=-1e18;for(let i=0;i<caps.length;i++){const room=P0.fc[i]-P0.fu[i];if(room<=1e-3)continue;const r=role(i);if(r==='ore'&&!isOre)continue;if(r==='waste'&&isOre)continue;
   /* jarak aman: fleet lain yang bekerja periode ini */let near=false;if(sep>0)for(let g=0;g<caps.length&&!near;g++){if(g===i)continue;for(const q of P0.pos[g])if(Math.abs(q.s-o.s)<sep&&Math.abs(q.b-o.b)<sep){near=true;break;}}if(near)continue;
   const L=last[i],d=L?Math.abs(L.s-o.s)+Math.abs(L.b-o.b)+Math.abs(L.k-o.k):0,sc=room/Math.max(1,P0.fc[i])-0.03*d+(r!=='any'?0.5:0);if(sc>bs){bs=sc;bi=i;}}return bi;};
 const take=(o,P0,f,fi)=>{const key=o.key;let r=rem.has(key)?rem.get(key).r:1;f=Math.min(f,r);if(!(f>1e-6))return 0;r-=f;rem.set(key,{r,fi});
  if(!P0.blocks.includes(key))P0.blocks.push(key);P0.vol+=o.vol*f;P0.ore+=(o.ore||0)*f;P0.met+=(o.met||0)*f;P0.wv+=(o.wv!=null?o.wv:o.vol)*f;P0.wt+=(o.waste||0)*f;P0.fu[fi]+=o.vol*f;P0.pos[fi].push(o);last[fi]=o;
  if(!fleetOf.has(key))fleetOf.set(key,fi);(part.get(key)||part.set(key,[]).get(key)).push({p:P0.p,f,fi});
  if(r<=1e-6){done.set(key,P0.p);rem.delete(key);const ck=o.s+'|'+o.b;top.set(ck,top.get(ck)+1);}return f;};
 const isOreB=o=>(o.ore||0)>0&&(!(tg.gmin>0)||!(o.g<tg.gmin*0.5));
 let miss=0,stop=null,idle=0;
 for(const P0 of P){if(done.size>=B.length&&!rem.size)break;const lim=tg.bcm>0?Math.min(P0.cap,tg.bcm):P0.cap;let forced=false;
  /* kebutuhan ore per periode untuk hitung stok terbuka */const oreNeed=tg.ore>0?tg.ore:(totO/estN);
  /* SR sasaran: diratakan = SR sisa cadangan, dibatasi SR maks */let rO=0,rW=0;for(const o of B){if(done.has(o.key))continue;const f=rem.has(o.key)?rem.get(o.key).r:1;rO+=(o.ore||0)*f;rW+=(o.wv!=null?o.wv:o.vol)*f;}
  const srRem=rO>0?rW/rO:Infinity,srT=tg.srmax>0?(tg.lvl?Math.min(tg.srmax,srRem):tg.srmax):(tg.lvl&&isFinite(srRem)?srRem:Infinity);
  for(let guard=0;guard<20000&&lim-P0.vol>1e-3;guard++){
   /* blok sebagian dilanjutkan oleh fleet yang sama */let o=null,fi=-1;const oreFull0=tg.oremax>0&&P0.ore>=tg.oremax*0.999;for(const [key,v] of rem){if(P0.fc[v.fi]-P0.fu[v.fi]>1e-3){const q=M.get(key);if(oreFull0&&(q.ore||0)>0)continue;o=q;fi=v.fi;break;}}
   if(!o){const E=[];for(const [ck,a] of COL){const i=top.get(ck);if(i>=a.length)continue;const q=a[i];if(!rem.has(q.key)&&!PL.lock.has(q.key)&&avail(q))E.push(q);}if(!E.length)break;
    const EO=E.filter(isOreB),EW=E.filter(q=>!isOreB(q)),sr=P0.ore>0?P0.wv/P0.ore:Infinity,g=P0.ore>0?P0.met/P0.ore:null;
    let expo=0;for(const q of EO)expo+=q.ore;const needStrip=sq.expo>0&&expo<sq.expo*oreNeed&&EW.length>0;
    const oreFull=tg.oremax>0&&P0.ore>=tg.oremax*0.999;
    /* keputusan: ore atau waste? */let wantOre;if(oreFull||!EO.length)wantOre=false;else if(!EW.length)wantOre=true;else if(needStrip&&sr<=srT)wantOre=false;else if(sr>srT)wantOre=true;else wantOre=!isFinite(srT);
    let C=wantOre?EO:EW;if(!C.length)C=wantOre?EW:(oreFull?[]:EO);if(!C.length)break;if(wantOre&&!EO.length)forced=true;
    /* nilai tiap calon (titik muat dinamis) */let best=null,bs=-1e18,bf=-1;for(const q of C){const f2=fleetFor(q,P0,isOreB(q));if(f2<0)continue;let sc=0;
     if(isOreB(q)){const bsr=(q.wv!=null?q.wv:q.vol)/Math.max(1,q.ore);sc-=Math.min(bsr,30)*(sr>srT?1.2:0.4);
      if(g!=null&&tg.gmin>0&&g<tg.gmin)sc+=(q.g-tg.gmin)*4;else if(g!=null&&tg.gmax>0&&g>tg.gmax)sc-=(q.g-tg.gmax)*4;else if(tg.gmin>0&&q.g<tg.gmin)sc-=(tg.gmin-q.g)*3;else if(tg.gmax>0&&q.g>tg.gmax)sc-=(q.g-tg.gmax)*2;}
     else{sc+=Math.min(6,oreBelow(q,3)/Math.max(1,oreNeed)*6)*(needStrip?2:1);}
     sc+=q.k*0.15;/* bench atas sedikit didahulukan */const L=last[f2];if(L)sc-=0.25*(Math.abs(L.s-q.s)+Math.abs(L.b-q.b))+0.4*Math.abs(L.k-q.k);
     sc-=1e-4*((sq.ds>0?q.s:-q.s)+(sq.db>0?q.b:-q.b));if(sc>bs){bs=sc;best=q;bf=f2;}}
    if(!best){/* jarak aman / peran menutup semua calon: coba jenis lain */const C2=(C===EO?EW:EO);for(const q of C2){const f2=fleetFor(q,P0,isOreB(q));if(f2>=0){best=q;bf=f2;break;}}}
    if(!best)break;o=best;fi=bf;}
   const r0=rem.has(o.key)?rem.get(o.key).r:1;let room=Math.min(lim-P0.vol,P0.fc[fi]-P0.fu[fi]);
   /* jangan lewati ore maks: ambil sebagian */if(tg.oremax>0&&(o.ore||0)>0){const or=tg.oremax-P0.ore;if(or<=1e-6)break;room=Math.min(room,or/Math.max(1e-9,o.ore)*o.vol);}
   const f=Math.min(r0,room/Math.max(1e-9,o.vol));if(take(o,P0,f,fi)<=1e-6)break;}
  /* blok terkunci ke periode ini */for(const [key,pp] of PL.lock)if(pp===P0.p&&!done.has(key)&&M.has(key)){const o=M.get(key);P0.viol++;take(o,P0,1,0);}
  if(!P0.blocks.length){if(++idle>3)break;continue;}idle=0;
  const sr=P0.ore>0?P0.wv/P0.ore:(P0.wv>0?Infinity:0);P0.sr=sr;P0.missS=tg.srmax>0&&sr>tg.srmax*1.02;P0.forced=forced;
  if(P0.missS){miss++;if(miss>allow){let lo=0,lw=0,ln=0;for(const o of B){if(done.has(o.key))continue;const f=rem.has(o.key)?rem.get(o.key).r:1;lo+=(o.ore||0)*f;lw+=(o.wv!=null?o.wv:o.vol)*f;ln++;}
    stop={p:P0.p,lab:P0.lab,sr,miss,allow,n:P.indexOf(P0)+1,left:ln,lo,lw,srLeft:lo>0?lw/lo:Infinity,srAll:totO>0?totW/totO:Infinity};break;}}}
 while(P.length&&!P[P.length-1].blocks.length)P.pop();if(stop){const i=P.findIndex(q=>q.p===stop.p);if(i>=0)P.length=i+1;}
 const rem2=new Map();for(const [k,v] of rem)rem2.set(k,v.r);
 const left=B.filter(o=>!done.has(o.key)),nMiss=P.filter(q=>q.missS).length,okPct=P.length?Math.round(100*(P.length-nMiss)/P.length):100;
 PL.res={P,done,rem:rem2,part,fleetOf,left,F:F.map(f=>Object.assign({},f)),tg:Object.assign({},tg),man:false,at:Date.now(),stop,okPct,smart:true};if(PL.cur>=P.length||PL.cur<-1)PL.cur=0;plDraw3d();plTL();plUi();
 if(stop){const fS=v=>isFinite(v)?v.toFixed(2):'∞';schMsg('&#9888; <b>Jadwal otomatis dihentikan di '+esc(stop.lab)+'</b>: SR maks '+tg.srmax+' meleset di '+stop.miss+' periode (jatah '+stop.allow+' = '+(100-pct)+'% dari ±'+estN+' periode). Sisa '+stop.left+' blok: ore '+gtShort(stop.lo)+' t, waste '+gtShort(stop.lw)+' BCM → SR sisa <b>'+fS(stop.srLeft)+'</b> (SR seluruh area '+fS(stop.srAll)+'). Saran: naikkan SR maks ke ≥ '+fS(Math.max(stop.srLeft,stop.srAll))+', turunkan % wajib, atau perkecil area / kupas waste lebih dulu.',1);}
 else schMsg('Rencana tambang (otomatis): '+done.size+' blok selesai, '+left.length+' belum'+(tg.srmax>0?' · SR ≤ '+tg.srmax+' tercapai di '+okPct+'% periode':'')+'.');return PL.res;}
{const _r=plRun;plRun=function(){const c=plCfg();if(c.mode==='auto'&&c.sq.smart!==false)return apRun();return _r.apply(this,arguments);};}
/* laporan: kepatuhan rentang */
{const _p=plRep;plRep=function(){const X=_p.apply(this,arguments);try{if(X&&PL.res&&PL.res.smart){const tg=PL.res.tg;for(const q of X.rows){q.okO=(!(tg.ore>0)||q.ore>=tg.ore*0.98)&&(!(tg.oremax>0)||q.ore<=tg.oremax*1.02);q.okG=q.g==null||((!(tg.gmin>0)||q.g>=tg.gmin)&&(!(tg.gmax>0)||q.g<=tg.gmax));}}}catch(_){}return X;};}
/* ---------- UI: sisipkan pengaturan otomatis ke panel ---------- */
{const _u=plUi;plUi=function(){const r=_u.apply(this,arguments);try{const b=$('plwb'),c=plCfg();if(!b||c.mode!=='auto')return r;const tg=c.tg,sq=c.sq,F=plFleets();
  const n=(k,v,w,ph)=>'<input data-ak="'+k+'" type="number" step="any" value="'+(v||'')+'" placeholder="'+(ph||'')+'" style="width:'+(w||56)+'px">';
  /* target lama → rentang */const det=[...b.querySelectorAll('details')].find(d=>/Target per periode/.test(d.querySelector('summary')?d.querySelector('summary').textContent:''));
  if(det){const open=det.open||!!(tg.ore||tg.oremax||tg.gmin||tg.gmax||tg.srmax||tg.bcm);det.open=open;det.innerHTML='<summary style="cursor:pointer"><b>Target per periode</b> <span style="color:#6c757d;font-size:11px">(opsional — rentang; kosong = tanpa batas)</span></summary>'+
   '<div class="r">ore min '+n('tg.ore',tg.ore,70)+' maks '+n('tg.oremax',tg.oremax,70)+' t</div><div class="r">kadar min '+n('tg.gmin',tg.gmin,48)+' maks '+n('tg.gmax',tg.gmax,48)+' g/t</div>'+
   '<div class="r">SR maks '+n('tg.srmax',tg.srmax,48)+' BCM/t, wajib di '+n('tg.srpct',tg.srpct,44)+' % periode</div><div class="r"><label><input type="checkbox" data-ab="tg.lvl"'+(tg.lvl?' checked':'')+'> ratakan SR antar-periode</label> &nbsp;BCM maks '+n('tg.bcm',tg.bcm,70)+'</div>'+
   '<div class="hint"><b>Periode</b> = satu satuan waktu jadwal menurut "tampilkan per" (shift / hari / minggu / bulan). Daftar periode tampil sebagai kartu di <b>lini waktu di bawah 3D</b> setelah ▶ Jalankan. Bila SR maks tidak lagi bisa dicapai (meleset lebih dari jatah), jadwal berhenti dan memberi tahu.</div>';}
  /* aturan otomatis */const run=b.querySelector('[data-pa=run]');if(run&&!b.querySelector('#apbox')){const d=document.createElement('details');d.id='apbox';d.open=!!PL._apOpen;d.style.cssText='margin-top:5px';
   d.innerHTML='<summary style="cursor:pointer"><b>Aturan penggalian</b> <span style="color:#6c757d;font-size:11px">urutan fisik · pengupasan · fleet</span></summary>'+
    '<div class="r">Blok di atas harus habis dulu; beda bench antar blok tetangga maks '+n('sq.maxd',sq.maxd,40)+'</div>'+
    '<div class="r">Stok ore terbuka min '+n('sq.expo',sq.expo,40)+' periode <span class="hint">(kurang dari itu → kupas waste penutup ore lebih dulu; 0 = mati)</span></div>'+
    '<div class="r">Jarak aman antar fleet '+n('sq.sep',sq.sep,40)+' blok</div>'+
    F.map((f,i)=>'<div class="r">'+esc(f.nm)+' menggali <select data-ar="'+i+'"><option value="any"'+((f.role||'any')==='any'?' selected':'')+'>ore & waste</option><option value="ore"'+(f.role==='ore'?' selected':'')+'>ore saja</option><option value="waste"'+(f.role==='waste'?' selected':'')+'>waste saja</option></select></div>').join('')+
    '<div class="hint">Titik muat dinamis: blok berikutnya dipilih dari semua blok yang boleh digali sesuai kebutuhan periode, tidak harus menyisir berurutan.</div>';
   run.parentElement.parentElement.insertBefore(d,run.parentElement);d.addEventListener('toggle',()=>{PL._apOpen=d.open;});}
  const re=()=>{plSave();if(PL.res){try{plRun();}catch(e){schMsg(esc(e.message),1);}}};
  b.querySelectorAll('[data-ak]').forEach(x=>x.onchange=()=>{const [a,k]=x.dataset.ak.split('.');c[a][k]=+x.value||0;re();});
  b.querySelectorAll('[data-ab]').forEach(x=>x.onchange=()=>{const [a,k]=x.dataset.ab.split('.');c[a][k]=x.checked;re();});
  b.querySelectorAll('[data-ar]').forEach(x=>x.onchange=()=>{F[+x.dataset.ar].role=x.value;re();});
  /* hasil: ringkasan berhenti */const rr=$('plwr');if(rr&&PL.res&&PL.res.smart&&!rr.querySelector('#apsum')){const R0=PL.res,S=R0.stop,el=document.createElement('div');el.id='apsum';el.className=S?'warn':'info';el.style.cssText='margin:4px 0;padding:5px 7px;border-radius:5px';
   el.innerHTML=S?'&#9888; <b>Berhenti di '+esc(S.lab)+'</b>: SR maks '+R0.tg.srmax+' meleset '+S.miss+'× (jatah '+S.allow+'). Sisa '+S.left+' blok ber-SR '+(isFinite(S.srLeft)?S.srLeft.toFixed(2):'∞')+'.':(R0.tg.srmax>0?'SR ≤ '+R0.tg.srmax+' tercapai di <b>'+R0.okPct+'%</b> periode (wajib '+(R0.tg.srpct||0)+'%).':'Semua blok terjadwal menurut aturan fisik.');
   const d0=rr.querySelector('details.plsec>div');if(d0)d0.insertBefore(el,d0.firstChild);}}catch(e){console.warn('apUi',e);}return r;};}
try{window.__PS3.ap={run:()=>apRun(),res:()=>{const r=PL.res;return r?{n:r.P.length,done:r.done.size,left:r.left.length,stop:r.stop&&{lab:r.stop.lab,miss:r.stop.miss,allow:r.stop.allow,srLeft:r.stop.srLeft},okPct:r.okPct,sr:r.P.map(q=>q.ore>0?+(q.wv/q.ore).toFixed(2):null),ore:r.P.map(q=>Math.round(q.ore)),fu:r.P.slice(0,3).map(q=>q.fu.map(Math.round))}:null;}};}catch(_){}
