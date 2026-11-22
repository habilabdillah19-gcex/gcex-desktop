/* a36: GRADE × TONNAGE dari Pit Schedule (22 Nov 2026).
   Block model Surpac .mdl dibaca dengan pembaca GC-Ex (a35_mdl.js, disalin apa adanya).
   Aturan bawaan = cara Surpac: blok dihitung UTUH pada periode ketika permukaan jadwal turun melewati TITIK PUSAT blok
   (pusat blok harus di bawah topografi awal fase). Opsi: proporsional (fraksi tinggi blok di antara permukaan sebelum/sesudah).
   Kelas kadar & tujuan mengikuti format preset GC-Ex Block Model (BX.ui.rules / destR / pst) — bisa diimpor dari gcex_project.json.
   Laporan per periode (jam … bench, sama dengan pilihan periode Pit Schedule) × fleet: ton @ kadar per kelas, waste, SR, logam. */
const GT={m:null,H:null,file:null,attr:'',sg:'',sgc:2.6,sx:'',rule:'pusat',rules:[{lo:0.4,hi:1,c:'#7ee04a',m:'LG'},{lo:1,hi:'',c:'#ff1a1a',m:'HG'}],sfOn:false,sxsThr:0.8,destR:[{m:'LG',sf:'any',d:'Stockpile LG'},{m:'HG',sf:'any',d:'ROM'}],dest:'',fleet:false,res:null,dres:null,topoF:true,src:'bawaan GC-Ex'};
(function(){const st=document.createElement('style');st.textContent=
`#gtbox{border-top:1px solid #e3e7ef;margin-top:6px;padding-top:4px}#gtbox summary{cursor:pointer;font-weight:600;color:#5b3a12}
#gttb{max-height:240px;overflow:auto;border:1px solid #e3e7ef;margin-top:4px}#gttb table{border-collapse:collapse;width:100%;font-size:11px}#gttb th,#gttb td{border-bottom:1px solid #eef1f6;padding:2px 4px;text-align:right;white-space:nowrap}
#gttb th{position:sticky;top:0;background:#f1f3f7}#gttb td:first-child,#gttb th:first-child{text-align:left}#gttb tr.on td{background:#fff3bf}#gttb tr.tot td{font-weight:700;border-top:2px solid #c9a77a}
#gtrl input[type=number]{width:52px}#gtrl input[type=text]{width:58px}#gtrl input[type=color]{width:24px;height:18px;padding:0;border:0}`;document.head.appendChild(st);})();
/* Jendela "Block model" (menu Impor): muat .mdl, atribut, filter topografi, kelas & tujuan, laporan per DESAIN (pit final / staging / edit).
   Kotak ringkas di hasil Pit Schedule memakai block model & pengaturan yang sama. */
function gtWin(){if($('bmw'))return;const st=document.createElement('style');st.textContent=
`#bmw{position:fixed;right:270px;top:78px;width:520px;max-height:calc(100vh - 100px);background:#fff;border:1px solid #9fb0cc;border-radius:7px;box-shadow:0 8px 28px rgba(20,32,58,.28);z-index:41;display:none;flex-direction:column;font:12px system-ui,Segoe UI,Arial,sans-serif}
#bmwh{display:flex;align-items:center;gap:6px;padding:5px 8px;background:linear-gradient(#1f3a5f,#152a47);color:#fff;cursor:move;user-select:none;border-radius:7px 7px 0 0}#bmwh button{background:#34527d;color:#fff;border:0;border-radius:4px;padding:2px 8px;cursor:pointer}
#bmwb{overflow:auto;padding:6px 8px 8px}#bmwb .r{display:flex;flex-wrap:wrap;align-items:center;gap:4px 8px;margin:3px 0}#bmwb input[type=number]{width:58px}#bmwb fieldset{border:1px solid #dde3ee;border-radius:5px;margin:4px 0;padding:3px 7px 6px}#bmwb legend{font-weight:600;color:#1f3a5f;padding:0 4px}
#gdtb{max-height:260px;overflow:auto;border:1px solid #e3e7ef;margin-top:4px}#gdtb table{border-collapse:collapse;width:100%;font-size:11px}#gdtb th,#gdtb td{border-bottom:1px solid #eef1f6;padding:2px 4px;text-align:right;white-space:nowrap}#gdtb th{position:sticky;top:0;background:#f1f3f7}#gdtb td:first-child,#gdtb th:first-child{text-align:left}#gdtb tr.tot td{font-weight:700;border-top:2px solid #9fb0cc}`;document.head.appendChild(st);
 const w=document.createElement('div');w.id='bmw';w.innerHTML='<div id="bmwh"><b>&#9878; Block model &amp; Grade × Tonnage</b><span style="flex:1"></span><button id="bmwx">&#10005;</button></div><div id="bmwb">'+
 '<div class="r"><button id="gtld" title="Muat block model Surpac .mdl (Version 4.0) — dibaca dengan pembaca GC-Ex Block Model">&#128194; Muat .mdl…</button><input id="gtf" type="file" accept=".mdl" style="display:none"><span id="gtst" style="font-size:11px;color:#6c757d;flex:1">belum ada block model</span></div>'+
 '<div id="gtcfg" style="display:none"><div class="r">kadar <select id="gtat"></select> SG <select id="gtsg"></select> <input id="gtsgc" type="number" step="any" value="2.6" title="SG bila atribut kosong / tidak dipilih" style="width:46px"> aturan <select id="gtru"><option value="pusat">pusat blok (cara Surpac)</option><option value="prop">proporsional</option></select></div>'+
 '<div class="r"><label title="Seperti GC-Ex: blok di atas topografi tidak dimuat (memperkecil block model besar)"><input type="checkbox" id="gttp" checked> hanya di bawah topografi</label> <label title="Hanya blok di area kerja (desain / AOI jadwal) yang dimuat — selalu aktif"><input type="checkbox" checked disabled> hanya di area desain / AOI</label></div>'+
 '<details id="gtkd"><summary style="cursor:pointer;color:#1f3a5f">kelas kadar &amp; tujuan <span id="gtsrc" style="font-weight:400;color:#6c757d"></span></summary><div id="gtrl"></div>'+
 '<div class="r"><button id="gtra">+ kelas</button><button id="gtpj" title="Ambil preset kelas kadar & tujuan dari file proyek GC-Ex Block Model (gcex_project.json)">&#8681; Impor preset GC-Ex…</button><input id="gtpf" type="file" accept=".json" style="display:none"><select id="gtps" style="display:none"></select></div>'+
 '<div class="r">sulfida <select id="gtsx"></select> &gt; <input id="gtsxt" type="number" step="any" value="0.8" style="width:46px"> <label><input type="checkbox" id="gtsfo"> pakai</label></div></details>'+
 '<fieldset><legend>Laporan desain (topografi → desain)</legend><div class="r">desain <select id="gdds"></select> tinggi bench <input id="gdhb" type="number" step="any" value="10"> m <button id="gdgo" style="font-weight:700">&#9654; Hitung</button><button id="gdcsv">&#8681; CSV</button></div><div id="gdsum" style="font-size:11px"></div><div id="gdtb"></div></fieldset>'+
 '<div class="r" style="color:#6c757d;font-size:11px">Laporan per periode jadwal ada di Pit Schedule → hasil → Grade × Tonnage (memakai block model & kelas yang sama).</div></div></div>';
 document.body.appendChild(w);let mv=null;$('bmwh').addEventListener('mousedown',e=>{if(e.target.tagName==='BUTTON')return;mv=[e.clientX,e.clientY,w.offsetLeft,w.offsetTop];e.preventDefault();});
 window.addEventListener('mousemove',e=>{if(!mv)return;w.style.left=Math.max(0,mv[2]+e.clientX-mv[0])+'px';w.style.right='auto';w.style.top=Math.max(0,mv[3]+e.clientY-mv[1])+'px';});window.addEventListener('mouseup',()=>{mv=null;});
 w.addEventListener('mousedown',()=>{let m=40;document.querySelectorAll('.flw.win,#schw,#sayw').forEach(x=>{const z=+getComputedStyle(x).zIndex||0;if(z>m&&z<60)m=z;});w.style.zIndex=Math.min(58,m+1);},true);
 $('bmwx').onclick=()=>gtOpen(false);
 $('gtld').onclick=()=>$('gtf').click();$('gtf').onchange=e=>{const f=e.target.files&&e.target.files[0];e.target.value='';if(f)gtLoad(f);};
 $('gtpj').onclick=()=>$('gtpf').click();$('gtpf').onchange=e=>{const f=e.target.files&&e.target.files[0];e.target.value='';if(f)gtPreset(f);};
 $('gtra').onclick=()=>{const L=GT.rules,hi=L.length?+L[L.length-1].lo||0:0;GT.rules.push({lo:hi+1,hi:'',c:'#ffa94d',m:'K'+(L.length+1)});GT.src='diubah';gtRules();};
 const rd=()=>{GT.attr=$('gtat').value;GT.sg=$('gtsg').value;GT.sgc=+$('gtsgc').value||2.6;GT.rule=$('gtru').value;GT.sx=$('gtsx').value;GT.sxsThr=+$('gtsxt').value||0;GT.sfOn=$('gtsfo').checked;if(GT.topoF!==$('gttp').checked){GT.topoF=$('gttp').checked;GT.win=null;}gtRedo();};
 ['gtat','gtsg','gtsgc','gtru','gtsx','gtsxt','gtsfo','gttp'].forEach(i=>$(i).onchange=rd);
 $('gdgo').onclick=()=>{gtDesign().catch(err=>{$('gdsum').innerHTML='<span style="color:#c92a2a">'+esc(err.message)+'</span>';console.error(err);});};$('gdcsv').onclick=()=>gtCsvX(GT.dres,'grade_tonnage_desain_'+(GT.dres?GT.dres.nm.replace(/\s/g,'_'):''));
 /* pintu masuk: menu Impor (di awal alur) + Hasil & volume */
 for(const [id,txt] of [['iw','&#9878; Block model (.mdl) & Grade × Tonnage…'],['hw','&#9878; Laporan Grade × Tonnage (block model)…']]){const fb=document.querySelector('#'+id+' .flb');if(!fb)continue;const b=document.createElement('button');b.className='fbtn';b.style.cssText='display:block;width:100%;margin-top:6px;text-align:left';b.innerHTML=txt;b.onclick=()=>gtOpen(true);fb.appendChild(b);}
 gtRules();}
function gtOpen(on){gtWin();const w=$('bmw');w.style.display=on?'flex':'none';if(on){const D=schDes(),s=$('gdds'),v=s.value;s.innerHTML=D.length?D.map(x=>'<option value="'+x.id+'">'+esc(x.nm)+'</option>').join(''):'<option value="">(belum ada desain)</option>';if(v&&D.some(x=>x.id===v))s.value=v;try{const ph=$('pH');if(ph&&+ph.value>0&&!GT.hbSet)$('gdhb').value=ph.value;}catch(_){}}}
function gtRedo(){if(GT.res)gtRun().catch(()=>{});if(GT.dres)gtDesign().catch(()=>{});}
function gtMount(){gtWin();const R=$('schres');if(!R||$('gtbox'))return;const d=document.createElement('details');d.id='gtbox';
 d.innerHTML='<summary>&#9878; Grade × Tonnage (block model)</summary>'+
 '<div class="r"><button id="gtop" title="Muat .mdl, atribut, filter topografi, kelas kadar & tujuan">&#9881; Block model…</button><label title="Rincian per fleet"><input type="checkbox" id="gtfl"> per fleet</label><button id="gtgo" style="font-weight:700">&#9654; Hitung laporan</button><button id="gtcsv">&#8681; CSV</button></div><div id="gtsum" style="font-size:11px"></div><div id="gttb"></div>';
 R.appendChild(d);d.addEventListener('toggle',()=>{const w=$('schw');w.style.width=d.open?'560px':'';});
 $('gtop').onclick=()=>gtOpen(true);$('gtfl').onchange=()=>{GT.fleet=$('gtfl').checked;if(GT.res)gtTable();};
 $('gtgo').onclick=()=>{if(!GT.file){gtOpen(true);return;}gtRun().catch(err=>{$('gtsum').innerHTML='<span style="color:#c92a2a">'+esc(err.message)+'</span>';console.error(err);});};$('gtcsv').onclick=gtCsv;}
function gtRules(){const el=$('gtrl');if(!el)return;$('gtsrc').textContent='('+GT.src+')';
 el.innerHTML='<table style="font-size:11px;width:100%"><tr style="color:#6c757d"><td>kelas</td><td>≥ dari</td><td>&lt; sampai</td><td>tujuan</td><td></td></tr>'+GT.rules.map((r,i)=>'<tr><td><input type="color" data-i="'+i+'" data-k="c" value="'+r.c+'"> <input type="text" data-i="'+i+'" data-k="m" value="'+esc(r.m)+'"></td><td><input type="number" step="any" data-i="'+i+'" data-k="lo" value="'+r.lo+'"></td><td><input type="number" step="any" data-i="'+i+'" data-k="hi" value="'+(r.hi===''?'':r.hi)+'" placeholder="∞"></td><td><input type="text" data-d="'+esc(r.m)+'" value="'+esc(gtDestOf(r.m,false))+'" title="Tujuan (mis. ROM / stockpile); aturan sulfida dari preset GC-Ex tetap dipakai"></td><td><button data-x="'+i+'" style="padding:0 4px">&#10005;</button></td></tr>').join('')+
  '<tr><td colspan=5 style="color:#6c757d">di luar kelas = WASTE → <input type="text" id="gtwd" value="'+esc(GT.wdest||'Waste dump')+'" style="width:80px"></td></tr></table>';
 el.querySelectorAll('[data-k]').forEach(c=>c.onchange=()=>{const r=GT.rules[+c.dataset.i],k=c.dataset.k;r[k]=k==='lo'?+c.value:k==='hi'?(c.value===''?'':+c.value):c.value;GT.src='diubah';gtRules();gtRedo();});
 el.querySelectorAll('[data-d]').forEach(c=>c.onchange=()=>{const m=c.dataset.d;GT.destR=GT.destR.filter(x=>!(x.m===m&&x.sf==='any'));GT.destR.push({m,sf:'any',d:c.value});GT.src='diubah';});
 el.querySelectorAll('[data-x]').forEach(b=>b.onclick=()=>{GT.rules.splice(+b.dataset.x,1);GT.src='diubah';gtRules();});$('gtwd').onchange=e=>{GT.wdest=e.target.value;};}
/* kelas & tujuan — sama dengan GC-Ex: kelas pertama yang memenuhi lo ≤ kadar < hi; tujuan dari destR (m + sulfida yes/no/any), cadangan = dest umum */
function gtCls(g){if(!(g===g))return -1;for(let i=0;i<GT.rules.length;i++){const r=GT.rules[i];if(g>=+r.lo&&(r.hi===''||r.hi===undefined||r.hi===null||g<+r.hi))return i;}return -1;}
function gtDestOf(m,sulf){const L=GT.destR||[];let r=L.find(x=>x.m===m&&(x.sf===(sulf?'yes':'no')));if(!r)r=L.find(x=>x.m===m&&(x.sf==='any'||!x.sf));return r?r.d:(GT.dest||'');}
/* ---- muat block model ----
   gtLoad: HEADER saja (cepat, file GB tidak dibaca). Blok dimuat saat menghitung (gtEnsure) HANYA untuk jendela yang
   dibutuhkan jadwal: kotak AOI × RL (dasar galian − cadangan … topografi). Jendela disimpan: Jalankan ulang di AOI yang
   sama tidak membaca file lagi.
   Desktop (window.gcexDesktop) & file ≥ GT.BIG_MB: lewat BACKEND GC-Ex — /mdl/open membangun cache kolom di disk sekali,
   /mdl/subset mengirim potongan .mdl mini (kotak XY + rentang RL) yang lalu dibaca pembaca .mdl yang sama.
   Browser / file kecil / backend gagal: dibaca langsung bertahap dengan filter yang sama. */
GT.BIG_MB=150;GT.ZMARG=10;
function gtBigMB(){let v=0;try{v=parseFloat(localStorage.getItem('psMdlBigMB'));}catch(_){}return v>0?v:GT.BIG_MB;}
function gtMaxN(){let v=0;try{v=parseInt(localStorage.getItem('gcexMdlMaxBlk'),10);}catch(_){}if(v>=100000)return v;const dm=+navigator.deviceMemory||8;return dm<=4?3000000:dm<8?6000000:12000000;}
async function gtLoad(f){const st=$('gtst');st.textContent='membaca header…';try{const H=await MDLSA.mdlHead(f);GT.H=H;GT.file=f;GT.m=null;GT.win=null;GT.res=null;
  const num=H.attrs.filter(a=>a.calc||a.type===2||a.type===1).map(a=>a.name),opt=(sel,L,blank)=>{sel.innerHTML=(blank?'<option value="">'+blank+'</option>':'')+L.map(n=>'<option>'+esc(n)+'</option>').join('');};
  opt($('gtat'),num);opt($('gtsg'),num,'(konstanta)');opt($('gtsx'),num,'(tidak ada)');
  const pick=(re,sel)=>{const n=num.find(x=>re.test(x));if(n)$(sel).value=n;};pick(/^au|au$|grade|kadar/i,'gtat');pick(/^sg|dens|bd$|^sg/i,'gtsg');pick(/sxs|sulf|^s_?tot|stot/i,'gtsx');
  GT.attr=$('gtat').value;GT.sg=$('gtsg').value;GT.sx=$('gtsx').value;$('gtcfg').style.display='';GT.dres=null;try{$('gdtb').innerHTML='';$('gdsum').innerHTML='';}catch(_){}
  st.innerHTML='<b>'+esc(H.name)+'</b> · '+schF(f.size/1048576,1)+' MB · ±'+H.estN.toLocaleString('id-ID')+' blok · '+H.attrs.length+' atribut'+(H.rot?' · <span style="color:#c92a2a">model memakai rotasi (belum diterapkan)</span>':'')+' — blok dimuat saat menghitung, hanya di jendela AOI';
  if(SCH.sim)await gtRun();}catch(e){st.innerHTML='<span style="color:#c92a2a">'+esc(e.message)+'</span>';console.error(e);}}
/* jendela yang dibutuhkan fase aktif */
function gtNeed(F){const Sm=F.sim,Gd=F.grid,S=schSurf(Sm.np-1),n=Gd.nx*Gd.ny;let x0=1e18,x1=-1e18,y0=1e18,y1=-1e18,zlo=1e18,zhi=-1e18;
 for(const [i,j] of [[0,0],[Gd.nx,0],[Gd.nx,Gd.ny],[0,Gd.ny]]){const p=schCorner(Gd,i,j);x0=Math.min(x0,p[0]);x1=Math.max(x1,p[0]);y0=Math.min(y0,p[1]);y1=Math.max(y1,p[1]);}
 for(let c=0;c<n;c++){if(!isFinite(Gd.z0[c]))continue;if(Gd.z0[c]>zhi)zhi=Gd.z0[c];if(Sm.first[c]>=0&&S[c]<zlo)zlo=S[c];}if(!(zlo<1e17))zlo=zhi;
 const tp=TP.find(q=>q.on&&q.G)||TP.find(q=>q.G);return {x0,x1,y0,y1,zlo,zhi,tp,c:Math.min(Gd.bx,Gd.by)};}
async function gtEnsure(N){const f=GT.file,H=GT.H,W=GT.win,st=$('gtst');
 if(GT.m&&W&&W.f===f&&W.tp===N.tp&&N.x0>=W.x0-1e-6&&N.x1<=W.x1+1e-6&&N.y0>=W.y0-1e-6&&N.y1<=W.y1+1e-6&&N.zlo>=W.zlo-1e-6&&N.zhi<=W.zhi+1e-6)return;
 if(!f)throw new Error('Muat block model .mdl dulu.');const t0=performance.now(),zlo=N.zlo-GT.ZMARG,zhi=N.zhi+0.01,c=Math.max(1,N.c||2.5);
 /* filter pembaca GC-Ex: pit = grid datar di RL dasar jendela (NaN di luar kotak AOI → dibuang), topo = grid topografi aktif */
 const nx=Math.ceil((N.x1-N.x0)/c),ny=Math.ceil((N.y1-N.y0)/c),PG={x0:N.x0,y0:N.y0,c,nx,ny,z:new Float32Array(nx*ny).fill(zlo-1)};
 const TG=N.tp&&GT.topoF!==false?{x0:N.tp.G.x0,y0:N.tp.G.y0,c:N.tp.G.cell,nx:N.tp.G.nx,ny:N.tp.G.ny,z:N.tp.G.Z}:null,maxN=gtMaxN(),prog=(pc,n)=>{st.textContent='membaca '+pc+'% · '+(n||0).toLocaleString('id-ID')+' blok';};
 const D=window.gcexDesktop;let m=null,via='langsung',note='';
 if(D&&D.apiBin&&D.api&&f.size>=gtBigMB()*1048576){try{let path=D.pathOf?D.pathOf(f):'';if(!path)throw new Error('lokasi file tidak diketahui');
   for(;;){const s=await D.api('/mdl/open',{path});if(s.state==='ready')break;if(s.state==='error')throw new Error(s.error||'backend gagal membaca .mdl');st.textContent='backend: membangun cache .mdl '+Math.round(s.pct||0)+'% · '+(s.n||0).toLocaleString('id-ID')+' blok (sekali saja)';await new Promise(r=>setTimeout(r,600));}
   st.textContent='backend: mengambil potongan area…';const r=await D.apiBin('/mdl/subset',{path,z_min:zlo,z_max:zhi,bbox:[N.x0,N.x1,N.y0,N.y1],max_n:maxN}),nSub=+(r.headers['x-gcex-n']||0);
   if(!nSub)throw Object.assign(new Error('Tidak ada blok model di jendela AOI (RL '+schF(zlo,1)+'–'+schF(zhi,1)+').'),{keras:1});
   if(r.headers['x-gcex-capped']==='1')note=' · <span style="color:#c92a2a">melebihi batas '+maxN.toLocaleString('id-ID')+' blok: hanya RL ≥ '+esc(r.headers['x-gcex-zmin'])+' yang dimuat — perkecil AOI / fase</span>';
   m=await MDLSA.readMDL(new File([r.buf],f.name),null,{pit:PG,topo:TG,zMin:zlo,zMax:zhi});via='backend GC-Ex (cache disk, '+nSub.toLocaleString('id-ID')+' blok dikirim)';}
  catch(e){if(e.keras)throw e;console.warn('[Pit Studio] backend .mdl gagal, baca langsung:',e);note=' · backend tidak dipakai: '+esc(e.message);m=null;}}
 if(!m){m=await MDLSA.readMDL(f,prog,{head:H,pit:PG,topo:TG,zMin:zlo,zMax:zhi,maxN});if(m.mdl&&m.mdl.over)note+=' · <span style="color:#c92a2a">'+m.mdl.over.toLocaleString('id-ID')+' blok melebihi batas memori — perkecil AOI / fase</span>';}
 GT.m=m;GT.win={f,tp:N.tp,x0:N.x0,x1:N.x1,y0:N.y0,y1:N.y1,zlo,zhi};GT.via=via;
 st.innerHTML='<b>'+esc(H.name)+'</b> · '+m.n.toLocaleString('id-ID')+' blok di jendela kerja'+(GT.topoF!==false?', di bawah topografi':'')+' (RL '+schF(zlo,1)+'–'+schF(zhi,1)+') · '+esc(via)+' · '+Math.round(performance.now()-t0)+' ms'+(m.warn?' · <span style="color:#c92a2a">'+esc(m.warn)+'</span>':'')+note;}
async function gtPreset(f){try{const J=JSON.parse(await f.text());const fd=(o,d)=>{if(!o||typeof o!=='object'||d>8)return null;if(o.bxui&&typeof o.bxui==='object')return o.bxui;if(Array.isArray(o.rules)&&('rAttr' in o||'pst' in o))return o;for(const k of Object.keys(o)){const r=fd(o[k],d+1);if(r)return r;}return null;};
  const U=fd(J,0);if(!U)throw new Error('Tidak ada pengaturan kelas kadar di file ini (bukan gcex_project.json GC-Ex Block Model?).');
  const L=[];if(U.rules)L.push({name:'(aktif di proyek)',p:{rules:U.rules,rAttr:U.rAttr,sfOn:U.sfOn,sxsThr:U.sxsThr,destR:(J.work&&J.work.ly&&J.work.ly.destR)||U.destR,dest:U.dest}});(U.pst||[]).forEach(x=>L.push(x));
  const s=$('gtps');s.style.display='';s.innerHTML=L.map((x,i)=>'<option value="'+i+'">'+esc(x.name)+' — '+((x.p&&x.p.rules)||[]).length+' kelas</option>').join('');
  const ap=i=>{const p=L[i].p||{};if(p.rules&&p.rules.length)GT.rules=p.rules.map(r=>({lo:+r.lo||0,hi:r.hi===''||r.hi==null?'':+r.hi,c:r.c||'#ffa94d',m:r.m||'ORE'}));GT.destR=JSON.parse(JSON.stringify(p.destR||[]));GT.dest=p.dest||'';if(p.sxsThr!==undefined){GT.sxsThr=+p.sxsThr;$('gtsxt').value=GT.sxsThr;}if(p.sfOn!==undefined){GT.sfOn=!!p.sfOn;$('gtsfo').checked=GT.sfOn;}
   if(p.rAttr&&GT.H&&[...$('gtat').options].some(o=>o.value===p.rAttr)){$('gtat').value=p.rAttr;GT.attr=p.rAttr;}GT.src='preset GC-Ex "'+L[i].name+'"';gtRules();gtRedo();};
  s.onchange=()=>ap(+s.value);ap(0);$('gtkd').open=true;}catch(e){alert(e.message);}}
/* ---- hitung: penugasan blok → (periode jam, fleet) ---- */
function gtPhase(F){const Sm=F.sim,Gd=F.grid,m=GT.m,{nx,ny,z0}=Gd,n=nx*ny,NP=Sm.np;
 /* riwayat per sel (CSR): urutan periode naik */const cnt=new Int32Array(n+1);for(let p=0;p<NP;p++)for(const c of Sm.DC[p])cnt[c+1]++;for(let c=0;c<n;c++)cnt[c+1]+=cnt[c];
 const HP=new Int32Array(cnt[n]),HZ=new Float32Array(cnt[n]),HO=new Int8Array(cnt[n]),w=cnt.slice(0,n);for(let p=0;p<NP;p++){const C=Sm.DC[p],Z=Sm.DZ[p],Ow=Sm.DO?Sm.DO[p]:null;for(let i=0;i<C.length;i++){const k=w[C[i]]++;HP[k]=p;HZ[k]=Z[i];HO[k]=Ow?Ow[i]:0;}}
 const G=m.num[GT.attr],SGa=GT.sg?m.num[GT.sg]:null,SX=GT.sx?m.num[GT.sx]:null,prop=GT.rule==='prop',out=[];let nIn=0;
 for(let b=0;b<m.n;b++){const x=m.x[b],y=m.y[b],s=x*Gd.ux+y*Gd.uy,q=x*Gd.vx+y*Gd.vy,i=Math.floor((s-Gd.s0)/Gd.bx),j=Math.floor((q-Gd.t0)/Gd.by);if(i<0||j<0||i>=nx||j>=ny)continue;const c=j*nx+i;if(cnt[c]===cnt[c+1])continue;
  const zt=z0[c],cz=m.z[b],hz=m.sz[b]/2;if(!(zt===zt))continue;const vol=m.sx[b]*m.sy[b]*m.sz[b];let sg=SGa?SGa[b]:GT.sgc;if(!(sg>0))sg=GT.sgc;const g=G?G[b]:NaN,k=gtCls(g),sul=!!(GT.sfOn&&SX&&SX[b]>GT.sxsThr);
  if(!prop){if(!(cz<zt))continue;/* pusat di bawah topo awal fase */for(let h=cnt[c];h<cnt[c+1];h++)if(HZ[h]<cz){out.push(HP[h],HO[h],k,vol*sg,g,sul?1:0,c);nIn++;break;}}
  else{let zp=zt;for(let h=cnt[c];h<cnt[c+1];h++){const za=HZ[h],top=Math.min(zp,cz+hz),bot=Math.max(za,cz-hz);if(top>bot){const f=(top-bot)/(2*hz);out.push(HP[h],HO[h],k,vol*sg*f,g,sul?1:0,c);nIn++;}zp=za;}}}
 return {out,nIn,F};}
async function gtRun(){if(!GT.file)throw new Error('Muat block model .mdl dulu.');if(!SCH.sim)throw new Error('Jalankan simulasi Pit Schedule dulu.');if(GT.busy){GT.again=1;return;}GT.busy=1;
 try{schPhSave();const ph=SCH.phs[SCH.ph];await gtEnsure(gtNeed(ph));if(!GT.m.num[GT.attr])throw new Error('Atribut kadar "'+GT.attr+'" tidak ada di block model.');const R=gtPhase(ph);GT.res=R;gtTable();try{if($('schcm').value==='kls')schPaint();}catch(_){}}
 catch(e){GT.res=null;try{$('gttb').innerHTML='';$('gtsum').innerHTML='<span style="color:#c92a2a">'+esc(e.message)+'</span>';}catch(_){}throw e;}
 finally{GT.busy=0;if(GT.again){GT.again=0;gtRun().catch(()=>{});}}}
function gtBand(){/* pita periode = SCH.bd (jam … bench) */return SCH.bd||[];}
function gtAgg(X){X=X||{out:GT.res.out,B:gtBand(),np:GT.res.F.sim.np,TS:GT.res.F.sim.TS,fl:GT.fleet};const O=X.out,B=X.B,K=GT.rules.length,fl=X.fl&&X.TS,pb=new Int32Array(X.np).fill(-1);B.forEach((r,i)=>{for(let p=r.a;p<=r.b;p++)pb[p]=i;});
 const mk=()=>({t:new Float64Array(K+1),gt:new Float64Array(K+1)});const rows=B.map(()=>fl?X.TS.map(mk):[mk()]),tot=mk(),dl={};
 for(let i=0;i<O.length;i+=7){const p=O[i],f=O[i+1],k=O[i+2],t=O[i+3],g=O[i+4],bi=pb[p];if(bi<0)continue;const A=rows[bi][fl?f:0],kk=k<0?K:k;A.t[kk]+=t;A.gt[kk]+=t*(g===g?g:0);tot.t[kk]+=t;tot.gt[kk]+=t*(g===g?g:0);
  const dst=k<0?(GT.wdest||'Waste dump'):(gtDestOf(GT.rules[k].m,O[i+5]===1)||'—');dl[dst]=(dl[dst]||0)+t;}
 return {B,rows,tot,K,TS:X.TS,fl,dl};}
function gtHtml(A,totLab,c0){const {B,rows,tot,K,TS,fl}=A,F=n=>schF(n),G=(t,gt)=>t>0?(gt/t).toFixed(2):'–';
 const oreT=a=>{let s=0;for(let k=0;k<K;k++)s+=a.t[k];return s;},oreM=a=>{let s=0;for(let k=0;k<K;k++)s+=a.gt[k];return s;};
 const cell=a=>GT.rules.map((r,k)=>'<td>'+(a.t[k]>0?F(a.t[k])+' @ '+G(a.t[k],a.gt[k]):'')+'</td>').join('')+'<td>'+(a.t[K]>0?F(a.t[K]):'')+'</td><td><b>'+F(oreT(a)+a.t[K])+'</b></td><td>'+(oreT(a)>0?(a.t[K]/oreT(a)).toFixed(2):'–')+'</td><td>'+F(oreM(a))+'</td><td>'+(oreM(a)/31.1035).toFixed(0)+'</td>';
 let h='<table><thead><tr><th>'+c0+'</th>'+(fl?'<th>Fleet</th>':'')+GT.rules.map(r=>'<th><i style="display:inline-block;width:8px;height:8px;background:'+r.c+'"></i> '+esc(r.m)+' t @ g/t</th>').join('')+'<th>Waste t</th><th>Total t</th><th>SR</th><th>Logam g</th><th>oz</th></tr></thead><tbody>';
 B.forEach((b,i)=>{rows[i].forEach((a,f)=>{const any=oreT(a)+a.t[K]>0;if(fl&&!any)return;h+='<tr data-i="'+i+'"><td>'+esc(b.lab)+'</td>'+(fl?'<td style="color:'+TS[f].t.col+'">'+esc(schWn(TS[f]))+'</td>':'')+cell(a)+'</tr>';});});
 h+='<tr class="tot"><td>'+esc(totLab)+'</td>'+(fl?'<td></td>':'')+cell(tot)+'</tr></tbody></table>';const ot=oreT(tot),om=oreM(tot);
 return {h,sum:'<b>'+F(ot)+' t ore @ '+G(ot,om)+' g/t</b> ('+(om/31.1035).toFixed(0)+' oz) · waste '+F(tot.t[K])+' t · SR '+(ot>0?(tot.t[K]/ot).toFixed(2):'–'),dest:'Tujuan: '+Object.entries(A.dl).map(([d,t])=>esc(d)+' '+F(t)+' t').join(' · ')};}
function gtTable(){const el=$('gttb');if(!el||!GT.res)return;const A=gtAgg(),H=gtHtml(A,'Total '+schPh().nm,'Periode');el.innerHTML=H.h;
 el.querySelectorAll('tr[data-i]').forEach(tr=>tr.onclick=()=>{schStop();schSet(+tr.dataset.i);});gtHi();
 $('gtsum').innerHTML=H.sum+' · '+GT.res.nIn.toLocaleString('id-ID')+' blok'+(GT.rule==='prop'?' (proporsional)':' (pusat blok, cara Surpac)')+'<br>'+H.dest;}
/* ---- laporan per DESAIN: blok di antara topografi aktif dan permukaan desain, per bench ---- */
async function gtDesign(){if(!GT.file)throw new Error('Muat block model .mdl dulu.');const D=schDes(),d=D.find(x=>x.id===$('gdds').value)||D[0];if(!d)throw new Error('Belum ada desain (pit final / staging / hasil edit).');
 const tp=TP.find(q=>q.on&&q.G)||TP.find(q=>q.G);if(!tp)throw new Error('Muat topografi dulu.');if(GT.busy)return;GT.busy=1;
 try{const G=d.G,Hb=Math.max(0.5,+$('gdhb').value||10);let x0=1e18,x1=-1e18,y0=1e18,y1=-1e18,zlo=1e18,zhi=-1e18;
  for(let j=0;j<G.ny;j++)for(let i=0;i<G.nx;i++){const z=G.Z[j*G.nx+i];if(!(z===z))continue;const x=G.x0+i*G.cell,y=G.y0+j*G.cell,zt=gridZ(tp.G,x,y);if(!(zt===zt)||!(z<zt-0.05))continue;if(x<x0)x0=x;if(x>x1)x1=x;if(y<y0)y0=y;if(y>y1)y1=y;if(z<zlo)zlo=z;if(zt>zhi)zhi=zt;}
  if(!(zlo<1e17))throw new Error('Desain "'+d.nm+'" tidak memotong topografi aktif.');
  await gtEnsure({x0:x0-G.cell,x1:x1+G.cell,y0:y0-G.cell,y1:y1+G.cell,zlo,zhi,tp,c:Math.max(1,G.cell)});const m=GT.m;if(!m.num[GT.attr])throw new Error('Atribut kadar "'+GT.attr+'" tidak ada di block model.');
  const Gr=m.num[GT.attr],SGa=GT.sg?m.num[GT.sg]:null,SX=GT.sx?m.num[GT.sx]:null,prop=GT.rule==='prop',out=[],kT=Math.ceil(zhi/Hb),NB=kT-Math.floor(zlo/Hb)+1;let nIn=0;
  for(let b=0;b<m.n;b++){const x=m.x[b],y=m.y[b],cz=m.z[b],hz=m.sz[b]/2,zd=gridZ(G,x,y);if(!(zd===zd))continue;const zt=gridZ(tp.G,x,y);if(!(zt===zt)||!(zd<zt-0.05))continue;let f=1;
   if(!prop){if(!(cz>zd&&cz<zt))continue;}else{const top=Math.min(zt,cz+hz),bot=Math.max(zd,cz-hz);if(!(top>bot))continue;f=(top-bot)/(2*hz);}
   let sg=SGa?SGa[b]:GT.sgc;if(!(sg>0))sg=GT.sgc;const g=Gr[b],bi=Math.max(0,Math.min(NB-1,kT-1-Math.floor(cz/Hb)));out.push(bi,0,gtCls(g),m.sx[b]*m.sy[b]*m.sz[b]*sg*f,g,(GT.sfOn&&SX&&SX[b]>GT.sxsThr)?1:0,0);nIn++;}
  const B=[];for(let i=0;i<NB;i++){const top=(kT-i)*Hb;B.push({a:i,b:i,lab:'Bench RL '+schF(top,1)+' → '+schF(top-Hb,1)});}
  GT.dres={out,B,np:NB,nm:d.nm,nIn};const A=gtAgg({out,B,np:NB,fl:false});const keep=[];A.rows.forEach((r,i)=>{let s=0;for(const v of r[0].t)s+=v;if(s>0)keep.push(i);});
  A.B=keep.map(i=>B[i]);A.rows=keep.map(i=>A.rows[i]);const H=gtHtml(A,'Total '+d.nm,'Bench');$('gdtb').innerHTML=H.h;
  $('gdsum').innerHTML='<b>'+esc(d.nm)+'</b> vs topografi "'+esc(tp.nm)+'": '+H.sum+' · '+nIn.toLocaleString('id-ID')+' blok'+(prop?' (proporsional)':' (pusat blok, cara Surpac)')+'<br>'+H.dest;}
 finally{GT.busy=0;}}
function gtHi(){const el=$('gttb');if(!el)return;el.querySelectorAll('tr.on').forEach(r=>r.classList.remove('on'));el.querySelectorAll('tr[data-i="'+SCH.pi+'"]').forEach(r=>{r.classList.add('on');if(SCH.play)r.scrollIntoView({block:'nearest'});});}
function gtCsv(){if(!GT.res)return;gtCsvX({out:GT.res.out,B:gtBand(),np:GT.res.F.sim.np,TS:GT.res.F.sim.TS,fl:GT.fleet,nm:schPh().nm},'pit_schedule_grade_tonnage_'+schPh().nm.replace(/\s/g,''));}
function gtCsvX(X,fn){if(!X)return;const A=gtAgg(X),{B,rows,tot,K,TS,fl}=A,q=s=>'"'+String(s).replace(/"/g,'""')+'"',L=[];
 L.push([X.TS?'Periode':'Bench',...(fl?['Fleet']:[]),...GT.rules.flatMap(r=>[r.m+' t',r.m+' g/t']),'Waste t','Total t','SR','Logam g','Logam oz'].map(q).join(','));
 const row=(lab,fnm,a)=>{let ot=0,om=0,all=a.t[K];for(let k=0;k<K;k++){ot+=a.t[k];om+=a.gt[k];}if(!(ot+all>0))return;L.push([q(lab),...(fl?[q(fnm)]:[]),...GT.rules.flatMap((r,k)=>[a.t[k].toFixed(1),a.t[k]>0?(a.gt[k]/a.t[k]).toFixed(3):'']),a.t[K].toFixed(1),(ot+a.t[K]).toFixed(1),ot>0?(a.t[K]/ot).toFixed(3):'',om.toFixed(1),(om/31.1035).toFixed(2)].join(','));};
 B.forEach((b,i)=>rows[i].forEach((a,f)=>row(b.lab,fl?schWn(TS[f]):'',a)));row('Total '+X.nm,'',tot);
 L.push('');L.push(q('Block model: '+(GT.H?GT.H.name:'')+' · kadar '+GT.attr+' · SG '+(GT.sg||('konstanta '+GT.sgc))+' · aturan '+(GT.rule==='prop'?'proporsional':'pusat blok (cara Surpac)')+' · kelas: '+GT.src+(GT.topoF!==false?' · hanya di bawah topografi':'')));
 L.push(q('Tujuan'));for(const [d,t] of Object.entries(A.dl))L.push(q(d)+','+t.toFixed(1));
 dl('﻿'+L.join('\r\n'),fn+'.csv','text/csv');}
/* integrasi: panel hasil, sorot baris, warna 3D per kelas material */
{const _b=schBuildMesh;schBuildMesh=function(){const r=_b.apply(this,arguments);gtMount();return r;};}
{const _s=schSet;schSet=function(){const r=_s.apply(this,arguments);try{gtHi();}catch(_){}return r;};}
{const _r=schRun;schRun=function(){const r=_r.apply(this,arguments);try{GT.res=null;$('gttb').innerHTML='';$('gtsum').innerHTML='';if(GT.file)gtRun().catch(()=>{});}catch(_){}return r;};}
{const _u=schBnd;schBnd=function(){const r=_u.apply(this,arguments);try{if(GT.res)gtTable();}catch(_){}return r;};}
(function(){const s=$('schcm');if(s&&!s.querySelector('[value=kls]')){const o=document.createElement('option');o.value='kls';o.textContent='kelas material (block model)';s.appendChild(o);}})();
/* warna sel = kelas blok TERAKHIR yang tergali di sel itu s/d periode tampil (cara pusat blok) */
{const _p=schPaint;schPaint=function(){const r=_p.apply(this,arguments);try{if($('schcm').value!=='kls'||!GT.res||!SCH.mesh||!SCH.show)return r;const O=GT.res.out,p=SCH.p,n=SCH.grid.nx*SCH.grid.ny,best=new Int32Array(n).fill(-1),bk=new Int16Array(n).fill(-2),col=SCH.mesh.geometry.attributes.color.array,C=GT.rules.map(q=>new THREE.Color(q.c)),Wc=new THREE.Color('#9a8f80');
  for(let i=0;i<O.length;i+=7){const pp=O[i],c=O[i+6];if(pp<=p&&pp>=best[c]){best[c]=pp;bk[c]=O[i+2];}}
  for(let c=0;c<n;c++){if(bk[c]===-2)continue;const cc=bk[c]<0?Wc:C[bk[c]],f=(col[c*3]+col[c*3+1]+col[c*3+2])/3;const sh=Math.max(0.45,Math.min(1.1,f/0.6));col[c*3]=Math.min(1,cc.r*sh);col[c*3+1]=Math.min(1,cc.g*sh);col[c*3+2]=Math.min(1,cc.b*sh);}
  SCH.mesh.geometry.attributes.color.needsUpdate=true;}catch(e){console.warn('gt warna',e);}return r;};}
window.__PS3=window.__PS3||{};try{gtWin();$('gdhb').oninput=()=>{GT.hbSet=1;};}catch(e){console.warn(e);}
{const _r=schReset;schReset=function(){const r=_r.apply(this,arguments);try{GT.res=null;$('gttb')&&($('gttb').innerHTML='');$('gtsum')&&($('gtsum').innerHTML='');}catch(_){}return r;};}
window.__PS3.gt={grids:()=>{const g=G=>({x0:G.x0,y0:G.y0,cell:G.cell,nx:G.nx,ny:G.ny,Z:[...G.Z].map(v=>v===v?v:null)});return {D:g(RES.tin.G),T:g(TP.find(q=>q.on&&q.G).G)};},open:on=>gtOpen(on!==false),design:()=>gtDesign(),S:GT,load:f=>gtLoad(f),run:()=>gtRun(),busy:()=>!!GT.busy,agg:()=>gtAgg(),mount:()=>gtMount()};
