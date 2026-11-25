/* a62: GEOTEKNIK PER BENCH / RL (permintaan klien 24 Nov; acuan Datamine Studio OP "Geotechnical Controls"):
   Studio OP: nilai geoteknik bisa per slope region (poligon / model) DAN per bench (Bench ID = RL, Berm Type Standard / Catch /
   None, Default Region, Face Angle, Berm Width). Pit Studio sudah punya: parameter umum, zona poligon (+ batas RL z0..z1 =
   "elevation constraint"), dan baris rentang RL. Yang ditambah di sini = TABEL PER BENCH:
     - satu baris per bench (RL lantai → RL crest, selang = tinggi bench), dibuat otomatis dari lantai desain s/d puncak topografi;
     - Tipe berm: ikut pola (berm tiap N bench, bawaan) · Standar · Catch · Tanpa — lebar Standar & Catch diatur di kepala tabel;
     - Zona: pakai nilai zona geoteknik bernama untuk SELURUH bench itu (seperti "Default Region" Studio OP, tanpa poligon);
     - Muka ° dan Berm m sendiri (kosong = ikut zona / umum).
   Urutan nilai (per titik): nilai bench sendiri (Tipe berm / Muka / Zona) → zona poligon yang memuat titik → rentang RL → umum
   (daftar urutan Studio OP: individual bench → rosette → slope region bench → DEFAULT).
   Data disimpan di OVR (ikut proyek & preset geoteknik) sebagai baris {bench:true, bt, zn}. */
const GBH={bs:NaN,bc:NaN};try{Object.assign(GBH,JSON.parse(localStorage.getItem('psGeoBench')||'{}'));}catch(_){}
/* bawaan: Standar = berm umum (langkah 3), Catch = 2 × itu */try{const b=+$('pB').value||4;if(!(GBH.bs>=0))GBH.bs=b;if(!(GBH.bc>=0))GBH.bc=Math.max(b*2,8);}catch(_){GBH.bs=4;GBH.bc=8;}
function gbSave(){try{localStorage.setItem('psGeoBench',JSON.stringify(GBH));}catch(_){}}
function gbRows(){return OVR.filter(o=>o.bench);}
function gbBs(){const b=+$('pB').value||4;return GBH.u?GBH.bs:b;}function gbBc(){const b=+$('pB').value||4;return GBH.u?GBH.bc:Math.max(2*b,8);}
function gbB(o){return o.bt==='std'?gbBs():o.bt==='catch'?gbBc():o.bt==='none'?0:NaN;}
/* rentang RL: lantai desain → puncak topografi */
function gbRange(){const H=PN().H;let zb=NaN,zt=NaN;try{if(BASE&&isFinite(BASE.z))zb=BASE.z;}catch(_){}
 try{if(!isFinite(zb)&&RES&&RES.S)zb=Math.min(...RES.S.map(s=>s.z).filter(isFinite));}catch(_){}
 try{for(const t of TP){if(!t.G)continue;let m=-1e18;for(const z of t.G.Z)if(z===z&&z>m)m=z;if(m>-1e17)zt=isFinite(zt)?Math.max(zt,m):m;}}catch(_){}
 /* batasi ke puncak desain yang ada (+1 bench) supaya daftar tidak memanjang ke puncak bukit di luar pit */try{const D=[RES,STG].filter(Boolean);let m=-1e18;for(const d of D)for(const s of (d.S||[]))if(isFinite(s.z)&&s.z>m)m=s.z;if(m>-1e17)zt=Math.min(isFinite(zt)?zt:m+H,m+H);}catch(_){}
 if(!isFinite(zb)||!isFinite(zt))return null;return {zb,zt,H};}
function gbFill(){const R=gbRange();if(!R){alert('Butuh lantai desain (bentuk awal / pit) dan topografi untuk membuat daftar bench.');return;}
 const keep=new Map(gbRows().map(o=>[Math.round(o.z0*100),o]));OVR=OVR.filter(o=>!o.bench);
 for(let z=R.zb;z<R.zt+R.H-1e-6;z+=R.H){const k=Math.round(z*100),o=keep.get(k)||{z0:z,z1:z+R.H,A:NaN,B:NaN,N:NaN,bench:true,bt:'',zn:''};o.z0=z;o.z1=z+R.H;OVR.push(o);}
 gbDraw();prmUpd();}
/* tabel rentang lama: hanya baris non-bench */
ovrDraw=function(){const tb=$('ovb');if(!tb)return;tb.innerHTML='';OVR.forEach((o,i)=>{if(o.bench)return;const tr=document.createElement('tr');tr.innerHTML=['z0','z1','A','B','N'].map(k=>'<td><input data-k="'+k+'" type="number" step="any" value="'+(isFinite(o[k])?o[k]:'')+'"></td>').join('')+'<td><button title="Hapus">&#10005;</button></td>';
 tr.querySelectorAll('input').forEach(inp=>inp.onchange=()=>{o[inp.dataset.k]=inp.value===''?NaN:+inp.value;prmUpd();});tr.querySelector('button').onclick=()=>{OVR.splice(OVR.indexOf(o),1);ovrDraw();prmUpd();};tb.appendChild(tr);});
 const nr=OVR.filter(o=>!o.bench).length,nb=gbRows().filter(o=>o.bt||o.zn||isFinite(o.A)||isFinite(o._B)).length;
 const el=$('ovr');if(el)el.innerHTML='&#9881; Geoteknik per bench / RL'+((nr||nb)?' ('+(nb?nb+' bench':'')+(nb&&nr?' · ':'')+(nr?nr+' rentang':'')+')':' (mis. zona oksida, catch berm)')+'…';try{gbDraw();}catch(_){}};
/* zona untuk satu bench penuh + tipe berm */
{const _p=prmAt;prmAt=function(z){const p=_p.apply(this,arguments);try{for(const o of OVR){if(!o.bench||!(z>=o.z0-1e-6&&z<o.z1-1e-6))continue;
  if(o.zn){const s=(window.SECT||[]).find(q=>q.nm===o.zn);if(s){if(!isFinite(o.A)&&isFinite(s.A)&&s.A>0)p.A=s.A;if(!o.bt&&isFinite(s.B)&&s.B>=0)p.B=s.B;if(!o.bt&&isFinite(s.N)&&s.N>=1)p.N=Math.round(s.N);}}
  if(o.bt){p.B=o.bt==='none'?0:(isFinite(o._B)&&o._B>=0?o._B:gbB(o));p.N=1;}if(isFinite(o.A)&&o.A>0)p.A=o.A;}p.a=p.H/Math.tan(Math.min(p.A,88.9)*Math.PI/180);}catch(_){}return p;};}
/* ---------- UI ---------- */
(function(){const w=$('ovw');if(!w)return;w.style.width='560px';const hb=w.querySelector('.flh b');if(hb)hb.textContent='Geoteknik per bench / RL';const fb=w.querySelector('.flb');
 const st=document.createElement('style');st.textContent='#gbt{width:100%;border-collapse:collapse;font-size:11.5px;table-layout:fixed}#gbt th:nth-child(1){width:64px}#gbt th:nth-child(2){width:76px}#gbt th:nth-child(3){width:62px}#gbt th:nth-child(4),#gbt th:nth-child(5){width:42px}#gbt td:last-child{font-size:11px;overflow:hidden;text-overflow:ellipsis}#gbt select,#gbt input{width:100%!important;box-sizing:border-box;padding:1px 2px;font-size:11.5px}#gbt th{position:sticky;top:0;background:#eef1f5;font-weight:600;padding:3px 4px;text-align:left}#gbt td{padding:1px 3px;border-top:1px solid #edf0f3}#gbt tr.on td{background:#fff8e1}#gbw{max-height:46vh;overflow:auto;border:1px solid #dfe3e8;border-radius:4px}.gbh{font-weight:600;margin:8px 0 3px}';document.head.appendChild(st);
 const d=document.createElement('div');d.id='gbs';d.innerHTML='<div class="gbh">Per bench</div><div class="hint">Satu baris = satu bench (RL lantai → RL crest). Kosong = ikut zona poligon / umum. Zona = pakai nilai zona geoteknik untuk seluruh bench tanpa poligon.</div>'+
  '<div class="r" style="display:flex;gap:6px;align-items:center;flex-wrap:wrap;margin:4px 0">Berm Standar <input id="gbbs" type="number" step="any" style="width:52px"> m · Catch <input id="gbbc" type="number" step="any" style="width:52px"> m <button id="gbfill">&#8635; Isi daftar bench</button><button id="gbclr" title="Hapus semua baris per bench">Kosongkan</button></div>'+
  '<div id="gbw"></div><div class="hint" id="gbinfo" style="margin-top:3px"></div><div class="gbh">Per rentang RL</div>';
 fb.insertBefore(d,fb.firstChild);
 $('gbbs').value=gbBs();$('gbbc').value=gbBc();$('gbbs').onchange=()=>{GBH.bs=Math.max(0,+$('gbbs').value||0);GBH.bc=Math.max(0,+$('gbbc').value||0);GBH.u=1;gbSave();gbDraw();prmUpd();};$('gbbc').onchange=()=>{GBH.bc=Math.max(0,+$('gbbc').value||0);GBH.bs=Math.max(0,+$('gbbs').value||0);GBH.u=1;gbSave();gbDraw();prmUpd();};
 $('gbfill').onclick=gbFill;$('gbclr').onclick=()=>{OVR=OVR.filter(o=>!o.bench);gbDraw();ovrDraw();prmUpd();};})();
function gbDraw(){const w=$('gbw');if(!w)return;try{if(!GBH.u){$('gbbs').value=gbBs();$('gbbc').value=gbBc();}}catch(_){}const R=gbRows().slice().sort((a,b)=>b.z0-a.z0),Z=(window.SECT||[]).map(s=>s.nm);
 if(!R.length){w.innerHTML='<div class="hint" style="padding:8px">Belum ada daftar bench. Klik <b>Isi daftar bench</b> (dari lantai desain sampai puncak topografi).</div>';$('gbinfo').textContent='';return;}
 const o2=(v,l,c)=>'<option value="'+esc(v)+'"'+(v===c?' selected':'')+'>'+esc(l)+'</option>';
 let h='<table id="gbt"><thead><tr><th title="RL lantai → RL crest bench">Bench RL</th><th>Tipe berm</th><th>Zona</th><th>Muka °</th><th>Berm m</th><th title="Nilai yang dipakai: sudut muka · lebar berm di crest bench">Hasil</th></tr></thead><tbody>';
 for(const o of R){const i=OVR.indexOf(o),p=prmAt(o.z0+0.01),hasil=Math.round(p.A)+'° '+(p.B>0&&(p.N===1||isBerm(o.z1,gbRange()?gbRange().zb:o.z0,p))?'B '+f1(p.B):'—');
  h+='<tr data-i="'+i+'"'+((o.bt||o.zn||isFinite(o.A)||isFinite(o._B))?' class="on"':'')+'><td>'+Math.round(o.z0)+'–'+Math.round(o.z1)+'</td><td><select data-g="bt">'+o2('','ikut pola',o.bt)+o2('std','Standar',o.bt)+o2('catch','Catch',o.bt)+o2('none','Tanpa',o.bt)+'</select></td>'+
   '<td><select data-g="zn">'+o2('','—',o.zn)+Z.map(n=>o2(n,n,o.zn)).join('')+'</select></td><td><input data-g="A" type="number" step="any" value="'+(isFinite(o.A)?o.A:'')+'"></td><td><input data-g="_B" type="number" step="any" value="'+(isFinite(o._B)?o._B:'')+'" placeholder="'+(o.bt==='std'?gbBs():o.bt==='catch'?gbBc():'')+'"'+(o.bt&&o.bt!=='none'?'':' disabled')+'></td><td style="color:#495057;white-space:nowrap">'+hasil+'</td></tr>';}
 w.innerHTML=h+'</tbody></table>';
 w.querySelectorAll('[data-g]').forEach(c=>c.onchange=()=>{const o=OVR[+c.closest('tr').dataset.i],k=c.dataset.g;if(k==='bt'||k==='zn')o[k]=c.value;else o[k]=c.value===''?NaN:+c.value;o.B=gbB(o);o.N=o.bt?1:NaN;prmUpd();gbDraw();ovrDraw();});
 const n=R.filter(o=>o.bt||o.zn||isFinite(o.A)||isFinite(o._B)).length;$('gbinfo').innerHTML=R.length+' bench · '+n+' diubah'+(window.SECT&&SECT.length?' · kolom kosong ikut zona poligon':'')+' · klik <b>Buat pit</b> / perbarui desain untuk menerapkan.';}
/* menu Desain → Geoteknik per bench / RL */
try{const m=[...document.querySelectorAll('.shm')].find(x=>x.firstChild&&x.firstChild.textContent==='Desain');if(m){const p=m.querySelector('.shmp'),b=document.createElement('button');b.className='shi';b.dataset.a='geob';b.textContent='⛰ Geoteknik per bench / RL…';b.onclick=()=>{try{shClose();}catch(_){}winShow($('ovw'),true);gbDraw();};const hr=p.querySelector('hr');p.insertBefore(b,hr||null);}}catch(_){}
ovrDraw();
try{window.__PS3.gb={fill:()=>gbFill(),rows:()=>gbRows().map(o=>({z0:o.z0,z1:o.z1,bt:o.bt,zn:o.zn,A:o.A,_B:o._B})),set:(i,k,v)=>{const o=gbRows().sort((a,b)=>a.z0-b.z0)[i];o[k]=v;o.B=gbB(o);o.N=o.bt?1:NaN;prmUpd();gbDraw();},p:z=>{const p=prmAt(z);return {A:p.A,B:p.B,N:p.N};}};}catch(_){}
/* ---- urutan nilai seperti daftar Studio OP: NILAI BENCH SENDIRI dulu, lalu zona poligon, lalu rentang RL, lalu umum ----
   (24 Nov, demo: semua dinding demo masuk salah satu zona poligon → tanpa ini tabel per bench tidak berpengaruh).
   Baris bench yang punya Tipe berm / Muka / Zona = nilai tegas untuk bench itu; kolom kosong tetap ikut zona poligon. */
function gbRowAt(z){for(const o of OVR)if(o.bench&&z>=o.z0-1e-6&&z<o.z1-1e-6)return o;return null;}
function gbRowA(o){if(!o)return NaN;if(isFinite(o.A)&&o.A>0)return o.A;if(o.zn){const s=(window.SECT||[]).find(q=>q.nm===o.zn);if(s&&isFinite(s.A)&&s.A>0)return s.A;}return NaN;}
function gbRowB(o){if(!o)return NaN;if(o.bt)return o.bt==='none'?0:(isFinite(o._B)&&o._B>=0?o._B:gbB(o));if(o.zn){const s=(window.SECT||[]).find(q=>q.nm===o.zn);if(s&&isFinite(s.B)&&s.B>=0)return s.B;}return NaN;}
/* berm di crest RL z ditentukan bench yang crest-nya z (baris z−0,01) — sama untuk desain naik maupun turun */
{const _pb=pB;pB=function(p,z){const o=gbRowAt(z-0.01);if(o){const b=gbRowB(o);if(b===b){const q=Object.assign({},p);q.B=b;q.N=1;return q;}}const up=gbRowAt(z+0.01);if(up&&(up.bt||up.zn)){const bs=prmAt(z-0.01);return _pb.call(this,Object.assign({},p,{B:bs.B,N:bs.N}),z);}return _pb.apply(this,arguments);};}
{const _os=offS;offS=function(P,sg,z,which,p){try{if(which==='B'){const o=gbRowAt(z-0.01),b=gbRowB(o);if(b===b)return tidy(b>0?cOff(P,sg*b):P.slice());}
  else if(which==='a'){const zz=sg>0?z+0.01:z-0.01,o=gbRowAt(zz),A=gbRowA(o);if(A===A){const H=prmAt(zz).H,a=H/Math.tan(Math.min(A,88.9)*Math.PI/180);return tidy(a>0?cOff(P,sg*a):P.slice());}}}catch(e){console.warn('gb',e);}
 return _os.apply(this,arguments);};}
