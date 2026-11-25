/* a61: (24 Nov) 1) menu Tampilan disusun ulang + ikon semua menu sejajar dalam satu kolom;
   2) label 3D (RL bench, lantai, simpang, dll.) ukurannya adaptif terhadap zoom dan label yang bertumpuk disembunyikan. */
/* ---------- 1. menu ---------- */
(function(){const m=[...document.querySelectorAll('.shm')].find(x=>x.firstChild&&x.firstChild.textContent==='Tampilan');if(!m)return;const p=m.querySelector('.shmp');
 const g=s=>p.querySelector(s),hr=()=>document.createElement('hr');
 const A=[g('[data-w=vw2]'),g('[data-a=bm3d]'),g('#mbsay')],B=[g('[data-a=tree]'),g('[data-a=prop]'),g('#mbfs'),g('[data-a=reset]')],C=[g('[data-a=klasik]')];
 const rest=[...p.children].filter(e=>e.tagName!=='HR'&&![...A,...B,...C].includes(e));
 p.innerHTML='';const put=L=>L.forEach(e=>e&&p.appendChild(e));put(A);p.appendChild(hr());put(B);p.appendChild(hr());put(C);if(rest.length){p.appendChild(hr());put(rest);}
 /* grup bertajuk kecil */
 const cap=(t,before)=>{const d=document.createElement('div');d.className='shcap';d.textContent=t;p.insertBefore(d,before);};cap('Tampilan 3D',p.firstChild);const h=p.querySelectorAll('hr');if(h[0])cap('Tata letak',h[0].nextSibling);
})();
const SHIC={tree:'☰',prop:'▤',reset:'↺',klasik:'▭',bm3d:'▦',unit:'⚙',bm:'▦',cad:'▥',gt:'Σ',gd:'Σ',plan:'📅',edhint:''};
function shIcons(){for(const b of document.querySelectorAll('.shmp .mbb,.shmp .shi')){if(b._icv===b.innerHTML)continue;
  let ic='',tx=b.textContent.replace(/^\s+/,'');const a=b.dataset.a;
  const mm=tx.match(/^([^\p{L}\p{N}\s(\[][^\s]*)\s+/u);if(mm){ic=mm[1];tx=tx.slice(mm[0].length);}
  if(a&&SHIC[a]!==undefined&&!ic)ic=SHIC[a];if(b.dataset.w==='vw2')ic='◎';if(ic==='👁')ic='◎';
  b.innerHTML='<span class="shic">'+esc(ic)+'</span>'+esc(tx);b.style.setProperty('padding-left','32px','important');b.style.setProperty('position','relative','important');b._icv=b.innerHTML;}}
(function(){const st=document.createElement('style');st.textContent='.shmp .mbb,.shmp .shi{padding-left:32px!important;position:relative}.shmp .shic{position:absolute;left:10px;top:50%;transform:translateY(-50%);width:16px;text-align:center;color:#5b6b80;font-size:12px}'+
 '.shmp .shcap{font:600 10.5px "Segoe UI",system-ui,Arial;color:#8a94a3;text-transform:uppercase;letter-spacing:.04em;padding:6px 12px 2px}';document.head.appendChild(st);
 shIcons();const _m=shMenuState;shMenuState=function(){const r=_m.apply(this,arguments);try{shIcons();}catch(_){}return r;};})();
/* ---------- 2. label adaptif ---------- */
const LBA={k:1,last:'',t:0};
function lbaVis(o){for(let q=o;q;q=q.parent)if(!q.visible)return false;return true;}
function lbaTick(){const t=performance.now();if(t-LBA.t<120)return;LBA.t=t;
 let dT=500;try{dT=C.position.distanceTo(CT.target);}catch(_){}
 /* jarak kamera ke sasaran (m, sebelum eksagerasi): dekat → label membesar (maks 1,25×), jauh → mengecil (min 0,55×) */
 const f=Math.max(0.55,Math.min(1.25,Math.pow(450/Math.max(dT,1),0.3)));
 const key=f.toFixed(3)+'|'+C.position.toArray().map(v=>v.toFixed(1)).join(',')+'|'+LBLS.size;if(key===LBA.last)return;LBA.last=key;
 const r=R.domElement.getBoundingClientRect(),Wd=r.width,Hd=r.height,boxes=[],L=[];
 for(const s of LBLS){if(!s.parent){LBLS.delete(s);continue;}const b=s.userData.lb;if(!b)continue;s.scale.set(b[0]*f,b[1]*f,1);if(!lbaVis(s))continue;L.push(s);}
 /* tumpukan: label dengan renderOrder lebih tinggi / lebih dekat ke kamera diutamakan; yang menimpa > 35% diredupkan habis */
 const P=new THREE.Vector3();L.forEach(s=>{s.getWorldPosition(P);s._d=P.distanceTo(C.position);P.project(C);s._x=(P.x+1)/2*Wd;s._y=(1-P.y)/2*Hd;s._in=P.z<1&&P.z>-1;});
 L.sort((a,b)=>(b.renderOrder-a.renderOrder)||(a._d-b._d));
 for(const s of L){if(!s._in){continue;}const pk=C.projectionMatrix.elements[5]*Hd/2,w=s.scale.x*pk,h=s.scale.y*pk,bx=[s._x,s._y-h,s._x+w,s._y];let hit=false;
  for(const q of boxes){const ix=Math.min(bx[2],q[2])-Math.max(bx[0],q[0]),iy=Math.min(bx[3],q[3])-Math.max(bx[1],q[1]);if(ix>0&&iy>0&&ix*iy>0.35*Math.min((bx[2]-bx[0])*(bx[3]-bx[1]),(q[2]-q[0])*(q[3]-q[1]))){hit=true;break;}}
  const op=hit?0:1;if(s.material.opacity!==op){s.material.opacity=op;s.material.needsUpdate=true;}if(!hit)boxes.push(bx);}}
(function loop(){try{lbaTick();}catch(e){}requestAnimationFrame(loop);})();
