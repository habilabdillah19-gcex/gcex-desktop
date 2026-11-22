/* ================= UI umum ================= */
const COL={fin:'#495057',crest:'#c92a2a',toe:'#1f6feb',road:'#e8590c',floor:'#2b8a3e',ref:'#7048e8',old:'#7c8594',sel:'#fab005'};
function stepSt(id,txt,ok){const el=$(id+'st');if(el)el.textContent=txt||'';const s=$(id);if(s)s.classList.toggle('done',!!ok);}
document.querySelectorAll('#m-new .step .sh').forEach(h=>h.onclick=()=>{const s=h.parentNode,o=s.classList.contains('open');document.querySelectorAll('#m-new .step').forEach(x=>x.classList.remove('open'));if(!o)s.classList.add('open');});
function openStep(id){document.querySelectorAll('#m-new .step').forEach(x=>x.classList.toggle('open',x.id===id));}
openStep('s2');
function segOf(id,cb){const el=$(id);el.querySelectorAll('button').forEach(b=>b.onclick=()=>{el.querySelectorAll('button').forEach(x=>x.classList.toggle('on',x===b));cb&&cb(b.dataset.v);});return ()=>el.querySelector('button.on').dataset.v;}
let MODE='new';
const MST={};
function modeSave(m){if(m==='edit')return;MST[m]={BASE,RSTART,srl:$('srl').value,zmax:$('pZmax').value,sm:smode(),res:$('res').innerHTML,st5:$('s5st').textContent};}
function modeLoad(m){if(m==='edit')return;const s=MST[m]||{BASE:null,RSTART:null,srl:'',zmax:'',sm:'bot',res:'',st5:''};BASE=s.BASE;RSTART=s.RSTART;$('srl').value=s.srl;$('pZmax').value=s.zmax;$('smode').querySelectorAll('button').forEach(x=>x.classList.toggle('on',x.dataset.v===s.sm));$('rllb').textContent=s.sm==='bot'?'RL dasar':'RL crest atas';$('res').innerHTML=s.res;stepSt('s5',s.st5,!!s.st5);baseApply();}
$('mode').querySelectorAll('button').forEach(b=>b.onclick=()=>{if(b.dataset.m===MODE)return;digStop();edStopPick();rPickStop();modeSave(MODE);MODE=b.dataset.m;$('mode').querySelectorAll('button').forEach(x=>x.classList.toggle('on',x===b));$('m-new').hidden=MODE==='edit';$('m-stg').hidden=MODE!=='stage';$('m-edit').hidden=MODE!=='edit';
 $('go').innerHTML=MODE==='stage'?'&#9654; Buat staging':'&#9654; Buat pit';modeLoad(MODE);finDraw();pitRedraw();if(window.syncTabs)syncTabs();});
/* jendela melayang */
function flDrag(win){const hd=win.querySelector('.flh');if(!hd)return;hd.addEventListener('pointerdown',e=>{if(e.target.closest('button,input,select'))return;const r=win.getBoundingClientRect(),p=cv.getBoundingClientRect(),dx=e.clientX-r.left,dy=e.clientY-r.top;
 const mv=ev=>{win.style.left=Math.max(0,Math.min(p.width-60,ev.clientX-p.left-dx))+'px';win.style.top=Math.max(0,Math.min(p.height-30,ev.clientY-p.top-dy))+'px';win.style.right='auto';win.style.bottom='auto';};
 const up=()=>{removeEventListener('pointermove',mv);removeEventListener('pointerup',up);};addEventListener('pointermove',mv);addEventListener('pointerup',up);});}
document.querySelectorAll('.flw.win,#lyw').forEach(flDrag);
let ZW=10;function winShow(w,on){if(on===undefined)on=w.style.display!=='block';w.style.display=on?'block':'none';if(on)w.style.zIndex=++ZW;document.querySelectorAll('#mbar .mbb[data-w="'+w.id+'"]').forEach(b=>b.classList.toggle('on',on));if(on&&w.id==='hw')hwFill();}
document.querySelectorAll('#mbar .mbb[data-w]').forEach(b=>b.onclick=()=>winShow($(b.dataset.w)));
document.querySelectorAll('.flw .x').forEach(x=>x.onclick=()=>{const w=x.closest('.flw');if(w.id==='lyw')lyShow(false);else winShow(w,false);});
document.querySelectorAll('.flw.win').forEach(w=>w.addEventListener('pointerdown',()=>w.style.zIndex=++ZW));
/* tampilan */
function bounds(){const b=new THREE.Box3();for(const k of ['topo','pit','str','ref','edit']){if(G[k].visible&&G[k].children.length)b.expandByObject(G[k]);}return b.isEmpty()?null:b;}
function view(v,soft){const b=bounds();if(!b){if(!soft)C.position.set(-300,300,300);return;}const c=b.getCenter(new THREE.Vector3()),r=Math.max(b.getSize(new THREE.Vector3()).length()*0.62,30);CT.target.copy(c);
 const d={plan:[0,1,0.0001],sw:[-0.62,0.62,0.48],ne:[0.62,0.62,-0.48],ew:[0,0.05,1],ns:[1,0.05,0],fit:null}[v];
 if(d){const n=new THREE.Vector3(...d).normalize();C.position.copy(c).addScaledVector(n,r*1.55);}else{const dir=C.position.clone().sub(CT.target).normalize();C.position.copy(c).addScaledVector(dir,r*1.55);}
 C.up.set(0,1,0);C.near=Math.max(0.2,r/500);C.far=r*30;C.updateProjectionMatrix();CT.update();}
document.querySelectorAll('#vw2 [data-v]').forEach(b=>b.onclick=()=>view(b.dataset.v));
$('vx').oninput=()=>{W.scale.y=+$('vx').value;$('vxv').textContent=$('vx').value+'×';};
document.querySelectorAll('.ly').forEach(c=>c.onchange=()=>{G[c.dataset.l].visible=c.checked;});
$('lbrl').onchange=()=>{G.lab.visible=$('lbrl').checked;};
function legend(){if(window.layRender)setTimeout(layRender,0);const it=[];if(TP.length)it.push(['area','#b5c98e','Topografi']);if(curR()&&(MODE!=='edit'||ED.out)){it.push(['line','#0b7285','Garis potong topo'],['line',COL.crest,'Crest (puncak lereng)'],['line',COL.toe,'Toe (kaki lereng)'],['line',COL.road,'Tepi jalan'],['line',COL.floor,'Lantai pit']);it.push(['area','#9fb4d6','Permukaan pit']);}
 if(ED&&MODE==='edit')it.push(['line',COL.old,'Pit lama (tetap)']);if(FIN&&MODE==='stage')it.push(['line',COL.fin,'Pit final (batas staging)']);if(BASE)it.push(['line',COL.ref,'Bentuk awal / acuan']);
 $('lgb').innerHTML=it.length?it.map(q=>'<div class="lr"><i style="'+(q[0]==='line'?'height:3px;background:':'height:11px;border:1px solid #0002;background:')+q[1]+'"></i>'+q[2]+'</div>').join(''):'<div class="hint">Belum ada data.</div>';}
/* raycast */
const RC=new THREE.Raycaster(),MS=new THREE.Vector2();
function ndc(e){const r=R.domElement.getBoundingClientRect();MS.set((e.clientX-r.left)/r.width*2-1,-(e.clientY-r.top)/r.height*2+1);RC.setFromCamera(MS,C);}
function toW(p){const q=W.worldToLocal(p.clone());return [q.x+O[0],-q.z+O[1],q.y+O[2]];}
function hitTopo(e){ndc(e);const ms=[];for(const s of TP)if(s.on&&s.mesh)ms.push(s.mesh);if(CURM&&G.pit.visible)ms.push(CURM);const h=RC.intersectObjects(ms,false)[0];return h?toW(h.point):null;}
function hitPlane(e,z){ndc(e);const y=(z-O[2])*W.scale.y,pl=new THREE.Plane(new THREE.Vector3(0,1,0),-y),p=new THREE.Vector3();if(!RC.ray.intersectPlane(pl,p))return null;return toW(p);}
function scr(E,N,Z){const v=V(E,N,Z);v.y*=W.scale.y;v.project(C);const r=R.domElement.getBoundingClientRect();return [(v.x+1)/2*r.width,(1-v.y)/2*r.height,v.z];}
let hudT=0;R.domElement.addEventListener('pointermove',e=>{const t=performance.now();if(t-hudT<60)return;hudT=t;const p=hitTopo(e);$('hud').textContent=p?'E '+p[0].toFixed(1)+'   N '+p[1].toFixed(1)+'   RL '+p[2].toFixed(1):'E/N/RL: arahkan kursor ke permukaan';});
function tip(t,e){const el=$('tip');if(!t){el.style.display='none';return;}const r=cv.getBoundingClientRect();el.innerHTML=t;el.style.display='block';el.style.left=(e.clientX-r.left+14)+'px';el.style.top=(e.clientY-r.top+14)+'px';}
function rlLabel(txt,E,N,Z,col){G.lab.add(sprite(txt,col||'#1b2a4e',0.021,V(E,N,Z)));}


/* panel kiri: seret untuk ubah lebar, klik ganda untuk sembunyi/tampil */
{const sp=$('split'),sd=$('side');let w0=null;try{const w=+localStorage.getItem('pitSideW');if(w>=240&&w<=700)sd.style.width=w+'px';}catch(_){}
 sp.addEventListener('pointerdown',e=>{if(sd.classList.contains('hid'))return;sp.setPointerCapture(e.pointerId);sp.classList.add('on');w0=[e.clientX,sd.getBoundingClientRect().width];});
 sp.addEventListener('pointermove',e=>{if(!w0)return;const w=Math.max(240,Math.min(700,w0[1]+e.clientX-w0[0]));sd.style.width=w+'px';rs();});
 sp.addEventListener('pointerup',()=>{if(!w0)return;w0=null;sp.classList.remove('on');try{localStorage.setItem('pitSideW',parseInt(sd.style.width));}catch(_){}});
 sp.addEventListener('dblclick',()=>{sd.classList.toggle('hid');rs();});}
