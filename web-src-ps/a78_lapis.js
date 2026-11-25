/* a78 · Lapisan jadwal bisa disembunyikan satu per satu (24 Nov 2026, pemilik: "kerangka Block Strip kadang menutupi permukaan
   topo setelah diturunkan… Ya, saya mau ketiganya")
   1) Centang per lapisan di panel Lapisan: Blok tambang · warna / garis kerangka / label / blok terpilih, Block model 3D.
   2) Tombol "Hanya permukaan" (panel Lapisan + bilah alat saat Pit Schedule terbuka): sekali klik menyembunyikan semua kerangka,
      jalur & batas dan Block model 3D; klik lagi mengembalikan persis seperti sebelumnya.
   3) Penggeser transparansi blok (0–100 %): warna & kerangka tetap terlihat samar.
   Berlaku untuk blok tambang (MB.g) dan tampilan rencana Klik blok / Otomatis (PL.g). Diingat per komputer (psLapis). */
const LYX={fill:true,frame:true,lab:true,sel:true,b3:true,op:100,solo:false};try{Object.assign(LYX,JSON.parse(localStorage.getItem('psLapis')||'{}'));LYX.solo=false;}catch(_){}
function lyxSave(){try{const o=Object.assign({},LYX);delete o.solo;localStorage.setItem('psLapis',JSON.stringify(o));}catch(_){}}
function lyxKind(c){if(c.userData&&c.userData.lk)return c.userData.lk;let k='frame';if(c.isSprite)k='lab';else if(c.isMesh)k='fill';else if(c.isLine||c.isLineSegments){const m=c.material;k=(m&&m.color&&!m.vertexColors&&m.color.getHex()!==0x3d2608)?'sel':'frame';}c.userData.lk=k;return k;}
function lyxApply(){const f=Math.max(0,Math.min(1,LYX.op/100));for(const g of [typeof MB!=='undefined'?MB.g:null,typeof PL!=='undefined'?PL.g:null]){if(!g)continue;for(const c of g.children){const k=lyxKind(c);c.visible=!LYX.solo&&LYX[k]!==false;const m=c.material;if(m&&(k==='fill'||k==='frame')){if(c.userData.op0===undefined){c.userData.op0=m.opacity===undefined?1:m.opacity;c.userData.tr0=!!m.transparent;c.userData.dw0=m.depthWrite;}
    const o=c.userData.op0*f;if(Math.abs(m.opacity-o)>1e-4||m.transparent!==(f<1||c.userData.tr0)){m.opacity=o;m.transparent=f<1||c.userData.tr0;if(k==='fill')m.depthWrite=f<1?false:c.userData.dw0;m.needsUpdate=true;}}}}
 try{if(B3.g)B3.g.visible=!LYX.solo&&LYX.b3!==false;}catch(_){}
 try{if(SCH.gs){if(LYX.solo){if(LYX._gs===undefined)LYX._gs=SCH.gs.visible;SCH.gs.visible=false;}else if(LYX._gs!==undefined){SCH.gs.visible=LYX._gs;delete LYX._gs;}}}catch(_){}
 try{const b=$('ptbs');if(b)b.classList.toggle('on',!!LYX.solo);}catch(_){}}
function lyxSolo(v){LYX.solo=v===undefined?!LYX.solo:!!v;lyxApply();try{layRender();}catch(_){}try{schMsg(LYX.solo?'Hanya permukaan: kerangka blok, jalur & batas disembunyikan — klik lagi untuk menampilkan.':'Lapisan jadwal ditampilkan kembali.');}catch(_){}}
function lyxHas(){try{return !!((MB.g&&MB.g.children.length)||(PL.g&&PL.g.children.length));}catch(_){return false;}}
for(const fn of ['mbDraw','plDraw3d','b3Draw']){try{const _f=eval(fn);const w=function(){const r=_f.apply(this,arguments);try{lyxApply();}catch(_){}return r;};eval(fn+'=w');}catch(e){console.warn('lyx',fn,e);}}
{const _l=window.layRender;window.layRender=function(){const r=_l.apply(this,arguments);try{const el=$('layb');if(!el)return r;const has=lyxHas();let b3=false;try{b3=!!B3.g;}catch(_){}if(!has&&!b3)return r;
  const rows=[];if(has){rows.push(['fill','Blok tambang · warna','#7ee04a'],['frame','Blok tambang · garis kerangka','#3d2608'],['lab','Blok tambang · label','#868e96'],['sel','Blok tambang · blok terpilih','#ffd43b']);}
  for(const [k,nm,col] of rows){const d=document.createElement('div');d.className='lrow';d.innerHTML='<input type="checkbox"'+(LYX[k]!==false&&!LYX.solo?' checked':'')+(LYX.solo?' disabled':'')+'><i style="background:'+col+'"></i><span class="t" title="'+nm+'">'+nm+'</span>';d.querySelector('input').onchange=e=>{LYX[k]=e.target.checked;lyxSave();lyxApply();};el.appendChild(d);}
  const c=document.createElement('div');c.className='lrow';c.id='lyxc';c.style.cssText='flex-wrap:wrap;gap:4px 6px;padding:5px 0';
  c.innerHTML='<button id="lyxs" class="sm'+(LYX.solo?' on':'')+'" style="flex:none" title="Sembunyikan semua kerangka blok, jalur & batas dan Block model 3D sekaligus — klik lagi untuk mengembalikan">'+(LYX.solo?'&#9635; Tampilkan kerangka':'&#9634; Hanya permukaan')+'</button><span style="flex:1 1 120px;display:flex;align-items:center;gap:5px;min-width:0" title="Transparansi warna & kerangka blok tambang"><span style="color:#6c757d;font-size:11px;white-space:nowrap">blok</span><input id="lyxo" type="range" min="0" max="100" step="5" value="'+LYX.op+'" style="flex:1;min-width:0"><span id="lyxv" style="font-size:11px;width:30px;text-align:right">'+LYX.op+'%</span></span>';
  el.insertBefore(c,el.firstChild);c.querySelector('#lyxs').onclick=()=>lyxSolo();const sl=c.querySelector('#lyxo');sl.oninput=()=>{LYX.op=+sl.value;c.querySelector('#lyxv').textContent=LYX.op+'%';lyxApply();};sl.onchange=()=>lyxSave();}catch(e){console.warn('lay lyx',e);}return r;};}
/* tombol cepat di bilah alat, tampil saat Pit Schedule terbuka */
{const _b=tbBuild;tbBuild=function(){_b();try{const T=$('ptb');if(T&&!$('ptbs')){const b=document.createElement('button');b.id='ptbs';b.className='tb';b.title='Hanya permukaan: sembunyikan / tampilkan semua kerangka blok, jalur & batas (rincian per lapisan ada di panel Lapisan)';b.innerHTML='<i>&#9634;</i><span>Permukaan</span>';b.onclick=()=>lyxSolo();const l=$('ptbl');if(l)T.insertBefore(b,l);else T.appendChild(b);}}catch(e){console.warn('lyx tb',e);}};}
{const _s=tbState;tbState=function(){_s();try{const b=$('ptbs');if(b){let on=false;try{on=caraSchOn();}catch(_){}b.style.display=on||LYX.solo?'':'none';b.classList.toggle('on',!!LYX.solo);}}catch(_){}};}
try{tbBuild();}catch(_){}
/* panel Lapisan disegarkan saat lapisan jadwal muncul / hilang */
{let sig='';setInterval(()=>{try{let b3=false;try{b3=!!B3.g;}catch(_){}const s=(lyxHas()?1:0)+'|'+(b3?1:0)+'|'+(caraSchOn()?1:0);if(s!==sig){sig=s;layRender();tbState();}}catch(_){}},900);}
try{window.__PS3.lyx={st:()=>Object.assign({},LYX),set:o=>{Object.assign(LYX,o);lyxSave();lyxApply();try{layRender();}catch(_){}} ,solo:v=>lyxSolo(v),cnt:()=>{const o={};for(const g of [MB.g,PL.g])if(g)for(const c of g.children){const k=lyxKind(c)+(c.visible?'+':'-');o[k]=(o[k]||0)+1;}return o;}};}catch(_){}
