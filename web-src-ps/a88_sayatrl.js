/* a88: SAYAT HORIZONTAL DI RL SAAT MENDIGIT DASAR PIT (pemilik 26 Nov 2026: "pada saat mendigit poligon manual untuk membuat bottom pit,
   saya bisa memilih opsi menyayat horizontal di elevasi yang menjadi base" — seperti kebiasaan di Surpac).
   Selama digit ada keping "Sayat di RL" di kiri atas kanvas (bawaan MATI). Saat menyala selama digit garis urat / poligon:
     · semua yang di ATAS RL dasar dipotong dari tampilan (topografi, block model 3D, desain) → terlihat irisan mendatar di RL itu;
     · titik digit jatuh tepat di bidang RL (bukan di permukaan topografi yang sudah terpotong);
     · RL diubah / perbesaran tegak berubah → bidang ikut; digit selesai / batal → tampilan kembali utuh (potongan Sayatan 3D dipulihkan).
   Tidak tampil pada mode "Batas topo" dan pada digit milik alat lain (tidak relevan di sana). */
const DSL={on:false,act:false,prev:null,z:null};
function dslOk(){try{return !!DG&&!DG.cb&&smode()!=='topo';}catch(_){return false;}}
function dslOff(){if(!DSL.act)return;DSL.act=false;DSL.z=null;try{R.clippingPlanes=DSL.prev||[];}catch(_){}DSL.prev=null;try{if(DG)delete DG.zp;}catch(_){}}
function dslApply(){const z=dslOk()&&DSL.on?dgZ():null;if(z===null){dslOff();dslUi();return;}if(!DSL.act){DSL.prev=R.clippingPlanes||[];DSL.act=true;}DSL.z=z;DSL.sy=W.scale.y;
 /* bidang 0,5 m di atas RL: garis bantu digit (RL + 0,3) dan kontur sorot tetap tampil */R.clippingPlanes=[new THREE.Plane(new THREE.Vector3(0,-1,0),(z+0.5-O[2])*W.scale.y)];DG.zp=z;dslUi();}
function dslUi(){const ok=dslOk();if(!ok&&!$('dgslw'))return;const l=dslChip(),c=$('dgsl'),z=ok?dgZ():null;l.style.display=ok?'flex':'none';c.checked=DSL.on;c.disabled=z===null;
 $('dgslt').textContent=z===null?'Sayat di RL (isi RL dulu)':'Sayat di RL '+(+z.toFixed(2));l.title=z===null?'Isi RL dasar / RL crest di panel dulu, baru tampilan bisa disayat mendatar di elevasi itu.':'Potong tampilan mendatar di RL ini: semua yang di atasnya disembunyikan dan titik digit jatuh tepat di bidang RL.';}
/* keping sendiri di kiri atas kanvas (bilah "Bantu gambar" sudah penuh) — hanya ada selama digit */
function dslChip(){let l=$('dgslw');if(l)return l;l=document.createElement('label');l.id='dgslw';l.style.cssText='position:absolute;left:10px;top:52px;z-index:31;background:#F7F5F0;border:1px solid #D3CDC1;border-radius:2px;padding:4px 9px;font-size:12px;display:none;align-items:center;gap:6px;box-shadow:0 2px 8px #0000002a;white-space:nowrap;cursor:pointer';
 l.innerHTML='<input type="checkbox" id="dgsl"> <span id="dgslt">Sayat di RL</span>';cv.appendChild(l);for(const ev of ['pointerdown','pointerup','click','dblclick'])l.addEventListener(ev,e=>e.stopPropagation());$('dgsl').onchange=e=>{DSL.on=e.target.checked;dslApply();};return l;}
{const _s=digStart;digStart=function(){const r=_s.apply(this,arguments);try{dslApply();}catch(e){console.warn('dsl',e);}return r;};}
{const _e=digStop;digStop=function(){try{dslOff();}catch(_){}const r=_e.apply(this,arguments);try{dslUi();}catch(_){}return r;};}
try{$('srl').addEventListener('change',()=>{if(DG)dslApply();});$('srl').addEventListener('input',()=>{if(DG)dslApply();});}catch(_){}
/* penjaga: RL / perbesaran tegak / mode berubah, atau alat lain mengambil alih bidang potong */
setInterval(()=>{try{if(!DSL.act){if(DG&&DSL.on)dslApply();else if(DG)dslUi();return;}if(!dslOk()||!DSL.on){dslOff();dslUi();return;}const z=dgZ();if(z!==DSL.z||W.scale.y!==DSL.sy)dslApply();}catch(_){}},400);
try{window.__PS3.dsl={st:()=>({on:DSL.on,act:DSL.act,z:DSL.z,n:(R.clippingPlanes||[]).length,zp:DG?DG.zp:undefined,dg:!!DG,pts:DG?DG.pts.map(p=>p.slice()):null}),set:v=>{DSL.on=!!v;dslApply();}};}catch(_){}
