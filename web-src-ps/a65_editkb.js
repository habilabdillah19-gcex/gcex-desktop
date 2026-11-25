/* a65: EDIT dengan mouse & keyboard (pemilik 24 Nov):
   - klik 1× string  → string terpilih (Shift / Ctrl + klik = tambah / kurangi pilihan)
   - klik 2× string  → RUAS di bawah kursor terpilih (disorot merah)
   - klik titik ujung ruas terpilih → menu titik: Seret / pindah · Snap ke titik terdekat · Hapus titik · Sisip titik tengah ruas · Putus di titik ini
   - Delete = hapus ruas terpilih (string terputus) atau hapus string terpilih · Ctrl+Z = urungkan · Ctrl+Y = ulangi · Esc = lepas pilihan
   Berlaku bila tidak ada alat lain yang aktif (Putus, Sambung, kuas, Pindah titik, Edit titik, menggambar). */
const SEG={s:null,g:null};
function ekBusy(){try{return PUT.on||SMB.on||PD.arm||MVX.on||(BED&&BED.on>=0)||MWS.ppick||EPICK||(ED&&ED.sel>=0)||DG||(typeof TRM!=='undefined'&&TRM.dig);}catch(_){return false;}}
function segHl(){if(SEG.g){SEG.g.parent&&SEG.g.parent.remove(SEG.g);clr(SEG.g);SEG.g=null;}const h=SEG.s;if(!h)return;const s=mwS()[h.si];if(!s)return;const a=s.pts[h.i],b=s.pts[h.i+1];if(!a||!b)return;const g=new THREE.Group();
 const o=lineObj([a,b].map(p=>[p[0],p[1],p[2]+0.3]),'#e03131',false,{depthTest:false});o.renderOrder=22;g.add(o);
 const m=new THREE.Points(new THREE.BufferGeometry().setFromPoints([a,b].map(p=>V(p[0],p[1],p[2]+0.35))),new THREE.PointsMaterial({color:'#e03131',size:13,sizeAttenuation:false,depthTest:false}));m.renderOrder=23;g.add(m);W.add(g);SEG.g=g;}
function segSet(h){SEG.s=h;segHl();ekMenu(null);if(h){const s=mwS()[h.si];try{mwInfo('<b>Ruas '+(h.i+1)+'</b> string '+(h.si+1)+' terpilih ('+f1(Math.hypot(s.pts[h.i+1][0]-s.pts[h.i][0],s.pts[h.i+1][1]-s.pts[h.i][1]))+' m). <b>Delete</b> = hapus ruas · klik titik ujungnya = menu titik · Esc = lepas.','ok');}catch(_){}}}
/* menu titik */
function ekMenu(o){let m=$('ekmenu');if(!o){if(m)m.remove();return;}if(!m){m=document.createElement('div');m.id='ekmenu';m.style.cssText='position:fixed;z-index:70;background:#fff;border:1px solid #c5ccd8;border-radius:6px;box-shadow:0 4px 14px rgba(0,0,0,.18);font:12px "Segoe UI",system-ui,Arial;padding:4px 0;min-width:190px';document.body.appendChild(m);}
 const it=(k,t,d)=>'<div data-ek="'+k+'" style="padding:5px 12px;cursor:pointer'+(d?';color:#adb5bd;pointer-events:none':'')+'" onmouseover="this.style.background=\'#eef3fb\'" onmouseout="this.style.background=\'\'">'+t+'</div>';
 const s=mwS()[o.si];m.innerHTML='<div style="padding:3px 12px 5px;color:#6c757d;font-size:11px;border-bottom:1px solid #eef0f3">Titik '+(o.vi+1)+' · string '+(o.si+1)+'</div>'+it('mv','✥ Seret / pindah titik')+it('snap','⌖ Snap ke titik terdekat')+it('del','✕ Hapus titik',s.pts.length<=(s.closed?4:2))+it('ins','＋ Sisip titik di tengah ruas')+it('brk','✂ Putus di titik ini');
 m.style.left=Math.min(innerWidth-210,o.x+8)+'px';m.style.top=Math.min(innerHeight-170,o.y+8)+'px';
 m.onclick=e=>{const k=e.target.closest('[data-ek]');if(!k)return;ekMenu(null);try{ekDo(k.dataset.ek,o);}catch(err){try{mwAfter('&#9888; '+esc(err.message),'warn');}catch(_){}}};}
function ekDo(k,o){const S=mwS(),s=S[o.si],L=mwL();let P=s.closed?openPts(s).map(p=>p.slice()):s.pts.map(p=>p.slice());const n=P.length,vi=s.closed?o.vi%n:o.vi;
 const fin=(Q,lab)=>{L[o.si]=s.closed?closeIt(Q):Q;mwApply(L,lab,[o.si]);segSet(null);};
 if(k==='mv'){segSet(null);MWS.sel=[o.si];mwDraw();mvToggle(true);mwInfo('<b>Seret titik</b> '+(o.vi+1)+' ke posisi baru (snap ke titik / garis bila dekat). Esc = selesai.','ok');return;}
 if(k==='del'){P.splice(vi,1);fin(P,'Hapus titik '+(o.vi+1)+' (string '+(o.si+1)+')');return;}
 if(k==='ins'){const h=SEG.s;if(!h)return;const a=s.pts[h.i],b=s.pts[h.i+1],ii=s.closed?(h.i+1)%n:h.i+1;P.splice(ii,0,[(a[0]+b[0])/2,(a[1]+b[1])/2,(a[2]+b[2])/2]);fin(P,'Sisip titik (string '+(o.si+1)+')');return;}
 if(k==='snap'){const p=P[vi];let best=null,bd=15;S.forEach((q,j)=>{if(j===o.si)return;for(const r of q.pts){const d=Math.hypot(r[0]-p[0],r[1]-p[1]);if(d<bd){bd=d;best=r;}}});if(!best){mwInfo('Tidak ada titik string lain dalam 15 m.','warn');return;}P[vi]=best.slice();fin(P,'Snap titik '+(o.vi+1)+' ('+f1(bd)+' m)');return;}
 if(k==='brk'){let out;if(s.closed){const R2=[];for(let q=0;q<=n;q++)R2.push(P[(vi+q)%n].slice());L[o.si]=R2;mwApply(L,'Putus poligon di titik '+(o.vi+1),[o.si]);}else{if(vi===0||vi===n-1){mwInfo('Titik ujung — tidak ada yang diputus.','warn');return;}const A=P.slice(0,vi+1),B=P.slice(vi);out=[];L.forEach((q,j)=>{if(j!==o.si){out.push(q);return;}out.push(A);out.push(B);});mwApply(out,'Putus garis di titik '+(o.vi+1),[o.si]);}segSet(null);}}
/* klik */
{const _ec=window.edClick;window.edClick=e=>{if(MODE==='edit'&&ED&&!ekBusy()&&!MWS.pick){const S=mwS();
  if(SEG.s){const s=S[SEG.s.si];if(s){const r=R.domElement.getBoundingClientRect();for(const vi of [SEG.s.i,SEG.s.i+1]){const p=s.pts[vi],q=scr(p[0],p[1],p[2]);if(Math.hypot(q[0]-(e.clientX-r.left),q[1]-(e.clientY-r.top))<10){ekMenu({si:SEG.s.si,vi,x:e.clientX,y:e.clientY});return;}}}}
  if(e.detail>=2)return;/* klik ke-2 dari klik ganda: ditangani dblclick */
  let i=-1;try{i=nearStr(e,S,false,12);}catch(_){}if(i<0){if(MWS.sel.length||SEG.s){MWS.sel=[];segSet(null);mwDraw();try{mwInfo();}catch(_){}}return _ec&&_ec(e);}
  segSet(null);if(e.shiftKey||e.ctrlKey){MWS.sel=MWS.sel.includes(i)?MWS.sel.filter(x=>x!==i):MWS.sel.concat([i]);}else MWS.sel=[i];mwDraw();
  try{const s=S[i];mwInfo('String '+(i+1)+' terpilih · '+(s.closed?'poligon':'garis terbuka')+' · '+s.pts.length+' titik. Klik 2× = pilih ruas · <b>Delete</b> = hapus string · alat Edit Manual berlaku untuk pilihan ini.','ok');}catch(_){}return;}
 return _ec&&_ec(e);};}
/* klik ganda = pilih ruas (menggantikan klik ganda lama = Edit titik; Edit titik tetap lewat menu titik → Seret, atau tombol Pilih string) */
document.addEventListener('dblclick',e=>{if(e.target!==R.domElement||MODE!=='edit'||!ED||ekBusy())return;const h=putSeg(e);if(!h)return;e.stopPropagation();e.preventDefault();MWS.sel=[h.si];mwDraw();segSet(h);},true);
/* keyboard */
addEventListener('keydown',e=>{if(MODE!=='edit'||!ED||/INPUT|SELECT|TEXTAREA/.test((e.target&&e.target.tagName)||''))return;
 if(e.key==='Delete'||(e.key==='Backspace'&&!DG)){if(ekBusy())return;if(SEG.s){e.preventDefault();const h=SEG.s;segSet(null);try{putCut(h);}catch(err){mwAfter('&#9888; '+esc(err.message),'warn');}return;}
  if(MWS.sel.length){e.preventDefault();try{MWOP.del();}catch(err){mwAfter('&#9888; '+esc(err.message),'warn');}MWS.sel=[];mwDraw();return;}}
 if(e.key==='Escape'){if($('ekmenu')){ekMenu(null);return;}if(SEG.s){segSet(null);return;}}},true);
document.addEventListener('pointerdown',e=>{const m=$('ekmenu');if(m&&!m.contains(e.target))ekMenu(null);},true);
setInterval(()=>{if(SEG.s&&(MODE!=='edit'||!ED||!mwS()[SEG.s.si]))segSet(null);},600);
try{window.__PS3.ek={seg:h=>segSet(h),st:()=>SEG.s,menu:o=>ekMenu(o),do:(k,o)=>ekDo(k,o)};}catch(_){}
