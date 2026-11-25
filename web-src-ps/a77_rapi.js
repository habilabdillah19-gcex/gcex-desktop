/* a77 · Kerapian kisi Properti (24 Nov 2026, pemilik: "tidak rapih, tidak align — sisanya kamu cari sendiri")
   - label sejajar baris pertama (bukan di tengah bila nilai turun baris), label panjang boleh dua baris (tidak dipotong "…")
   - kotak angka seragam & ringkas supaya satu baris muat; pilihan (select) menyusut mengisi sisa lebar
   - baris tanpa label di kartu fleet diberi label (alat gali, urutan); formulir desain: kotak isian rata kiri & sama lebar */
(function(){const st=document.createElement('style');st.textContent=`
body.shx #dock .r.pgx{align-items:baseline!important;padding:3px 0 3px 2px!important}
body.shx #dock .r.pgx>.pgl{white-space:normal!important;overflow:visible!important;line-height:1.25;flex:0 0 30%!important}
body.shx #dock .r.pgx>.pgv{gap:3px 5px!important;align-items:baseline!important}
body.shx #dock .r.pgx>.pgv>input[type=number]{flex:0 0 56px;width:56px!important;min-width:0}
body.shx #dock .r.pgx>.pgv.pgm>input[type=number]{flex:0 0 44px;width:44px!important}
body.shx #dock .r.pgx>.pgv>select{flex:1 1 56px;min-width:0;max-width:100%;width:auto!important}
body.shx #dock .r.pgx>.pgv>input[type=date]{flex:0 1 112px;width:112px!important;min-width:0}
body.shx #dock .r.pgx>.pgv>input[type=text]{flex:1 1 60px;min-width:0;width:auto!important}
body.shx #dock .r.pgx>.pgv>button{flex:none}
body.shx #dock .r:not(.pgx):not(.pgj){gap:3px 5px!important}body.shx #dock .r:not(.pgx):not(.pgj)>input[type=number]{width:42px!important}
body.shx #dock .pg>label>span>input[type=number],body.shx #dock .pg>label>span>input[type=text]{flex:0 0 96px!important;width:96px!important}
body.shx #dock .pg>label>span>select{flex:1 1 96px!important}
body.shx #dock .fl>input[type=number]:first-of-type{flex:0 0 96px!important;width:96px!important;margin-left:auto}
body.shx #dock .fl>input[type=number]:first-of-type+.u{flex:0 0 calc(50% - 102px);text-align:left}
`;document.head.appendChild(st);})();
{const _w=pgxWrap;pgxWrap=function(root){try{
  /* baris tanpa label di kartu fleet */
  for(const i of root.querySelectorAll('.r:not(.pgx):not(.pgn)>input[data-k="nu"]')){const r=i.parentElement,s=r.firstChild;if(s&&s.nodeType===1&&s.tagName==='SELECT'){r.classList.remove('pgn');r.insertBefore(document.createTextNode('alat gali '),s);}}
  for(const s of root.querySelectorAll('.r:not(.pgx):not(.pgn)>select[data-k="ord"]')){const r=s.parentElement,b=r.firstElementChild;if(b&&b.tagName==='B'&&r.firstChild===b){while(r.firstChild&&r.firstChild!==s)r.removeChild(r.firstChild);r.insertBefore(document.createTextNode('urutan gali '),s);}}
 }catch(e){console.warn('rapi',e);}
 const r=_w.apply(this,arguments);
 try{for(const v of root.querySelectorAll('.r.pgx>.pgv:not(.pgk)')){v.classList.add('pgk');if(v.querySelectorAll(':scope > input[type=number]').length>=2)v.classList.add('pgm');}}catch(_){}
 return r;};}
/* Ganti arah pandang (Plan / SW / NE / Timur / Selatan) MENJAGA titik pusat & jarak zoom yang sedang dipakai
   (pemilik 24 Nov: "display langsung zoom jauh, apakah tidak bisa menjaga skala zoomnya?"). Hanya "Pas" yang membingkai ulang. */
function viewKeep(v){const D={plan:[0,1,0.0001],sw:[-0.62,0.62,0.48],ne:[0.62,0.62,-0.48],ew:[0,0.05,1],ns:[1,0.05,0]}[v];
 if(!D||(typeof DMO!=='undefined'&&DMO.on)||!bounds()){view(v);return;}
 const t=CT.target.clone(),d=C.position.distanceTo(t);view(v);if(!(d>1))return;const n=new THREE.Vector3(...D).normalize();CT.target.copy(t);C.position.copy(t).addScaledVector(n,d);C.up.set(0,1,0);C.updateProjectionMatrix();CT.update();}
document.querySelectorAll('#vw2 [data-v]').forEach(b=>b.onclick=()=>viewKeep(b.dataset.v));
try{window.__PS3.vk=v=>{viewKeep(v);return [C.position.distanceTo(CT.target),CT.target.toArray()];};}catch(_){}
