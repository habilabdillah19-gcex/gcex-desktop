/* a44: panel LEPAS – TEMPEL – PERKECIL (seperti Ore Works) untuk Pit Schedule, Block model, Cadangan, Laporan, Lapisan, Legenda.
   Tombol di kepala panel: ◧ tempel kiri · ◨ tempel kanan · ⧉ lepas (mengambang) · ▁ perkecil jadi strip judul.
   Seret kepala panel ke tepi kiri / kanan layar = tempel; klik ganda kepala = tempel ↔ lepas. Tata letak diingat per komputer. */
const DKP={ids:['schw','bmw','mbw','gtrw','lay','lgw'],st:{},last:null};
(function(){const css=document.createElement('style');css.textContent=
`.dkcol{position:fixed;z-index:39;display:flex;flex-direction:column;gap:2px;pointer-events:none}.dkcol>*{pointer-events:auto}
.dkd{position:static!important;left:auto!important;right:auto!important;top:auto!important;width:100%!important;max-width:none!important;max-height:none!important;flex:1 1 0;min-height:0;border-radius:0!important;box-shadow:0 0 0 1px #9fb0cc!important;margin:0!important;overflow:auto}
.dkd.dkm{flex:0 0 auto}.dkm>:not(:first-child){display:none!important}.dkm{height:auto!important;max-height:none!important;min-height:0!important}
.dkb{display:inline-flex;gap:2px;margin-left:6px;vertical-align:middle}.dkb button{background:rgba(255,255,255,.16)!important;color:inherit!important;border:0!important;border-radius:3px!important;padding:0 5px!important;min-width:0!important;height:18px;line-height:16px;font-size:11px!important;cursor:pointer}.dkb button:hover{background:rgba(255,255,255,.34)!important}
#dkL{left:0}#dkR{right:0}#schbd{min-height:0}`;document.head.appendChild(css);
 for(const s of ['L','R']){const c=document.createElement('div');c.className='dkcol';c.id='dk'+s;document.body.appendChild(c);}
 try{DKP.st=JSON.parse(localStorage.getItem('psDock')||'{}')||{};}catch(_){DKP.st={};}})();
function dkpSave(){try{localStorage.setItem('psDock',JSON.stringify(DKP.st));}catch(_){}}
function dkpGeom(){const mb=$('mbar'),tb=document.querySelector('#tbar,.tbar,#tools'),sb=$('sbar');let top=mb?mb.getBoundingClientRect().bottom:30;try{const c=$('cv').getBoundingClientRect();if(c.height>0)top=c.top;}catch(_){}const bot=sb?Math.max(0,innerHeight-sb.getBoundingClientRect().top):22;
 for(const s of ['L','R']){const c=$('dk'+s);c.style.top=top+'px';c.style.bottom=bot+'px';let w=0;for(const k of c.children){if(getComputedStyle(k).display!=='none')w=Math.max(w,+k.dataset.dkw||340);}c.style.width=w?Math.min(w,innerWidth*0.45)+'px':'0px';}}
function dkpSet(id,side){const e=$(id);if(!e)return;const S=DKP.st[id]=DKP.st[id]||{};if(side==='L'||side==='R'){if(!e._dkp){e._dkp=e.parentElement;e._dkn=e.nextSibling;e._dks={l:e.style.left,r:e.style.right,t:e.style.top,w:e.style.width};e.dataset.dkw=Math.round(e.getBoundingClientRect().width)||e.dataset.dkw||340;}
  e.classList.add('dkd');$('dk'+side).appendChild(e);S.side=side;DKP.last=side;}
 else{if(e._dkp){e.classList.remove('dkd');try{e._dkp.insertBefore(e,e._dkn&&e._dkn.parentElement===e._dkp?e._dkn:null);}catch(_){e._dkp.appendChild(e);}e.style.left=e._dks.l;e.style.right=e._dks.r;e.style.top=e._dks.t;e.style.width=e._dks.w;e._dkp=null;}S.side='';}
 dkpGeom();dkpSave();try{window.dispatchEvent(new Event('resize'));}catch(_){}}
function dkpMin(id,on){const e=$(id);if(!e)return;const S=DKP.st[id]=DKP.st[id]||{};S.min=on===undefined?!e.classList.contains('dkm'):!!on;e.classList.toggle('dkm',S.min);dkpGeom();dkpSave();}
function dkpInit(id){const e=$(id);if(!e||e._dk)return;const h=e.firstElementChild;if(!h)return;e._dk=1;const g=document.createElement('span');g.className='dkb';
 g.innerHTML='<button data-dk="L" title="Tempel ke kiri">&#9703;</button><button data-dk="R" title="Tempel ke kanan">&#9704;</button><button data-dk="F" title="Lepas (mengambang)">&#10697;</button><button data-dk="M" title="Perkecil / buka (strip judul)">&#9601;</button>';
 const x=h.querySelector('button');if(x&&x.parentElement===h)h.insertBefore(g,[...h.children].find(c=>c.tagName==='BUTTON'||c.querySelector&&c.querySelector('button'))||null);else h.appendChild(g);
 g.addEventListener('mousedown',ev=>ev.stopPropagation());g.addEventListener('click',ev=>{const b=ev.target.closest('[data-dk]');if(!b)return;ev.stopPropagation();const k=b.dataset.dk;if(k==='M')dkpMin(id);else dkpSet(id,k==='F'?'':k);});
 h.addEventListener('dblclick',ev=>{if(ev.target.closest('button,select,input,label'))return;dkpSet(id,e.classList.contains('dkd')?'':(DKP.last||(id==='lay'||id==='lgw'?'R':'L')));});
 /* seret ke tepi = tempel */
 h.addEventListener('mousedown',ev=>{if(ev.target.closest('button,select,input,label')||e.classList.contains('dkd'))return;const up=u=>{window.removeEventListener('mouseup',up,true);if(Math.hypot(u.clientX-ev.clientX,u.clientY-ev.clientY)<12)return;if(u.clientX<10)dkpSet(id,'L');else if(u.clientX>innerWidth-10)dkpSet(id,'R');};window.addEventListener('mouseup',up,true);});
 const S=DKP.st[id];if(S){if(S.side)dkpSet(id,S.side);if(S.min)dkpMin(id,true);}}
function dkpScan(){for(const id of DKP.ids)dkpInit(id);dkpGeom();}
setInterval(()=>{try{dkpScan();}catch(_){}},700);window.addEventListener('resize',()=>{try{dkpGeom();}catch(_){}});
try{dkpScan();window.__PS3.dock={set:(id,s)=>dkpSet(id,s),min:(id,on)=>dkpMin(id,on),reset:()=>{for(const id of DKP.ids){dkpSet(id,'');dkpMin(id,false);}DKP.st={};dkpSave();}};}catch(_){}
