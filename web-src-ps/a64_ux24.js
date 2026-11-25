/* a64: (24 Nov, keluhan pemilik)
   1) Panel Properti tidak bisa digeser lebarnya: pegangan .shrz tersembunyi oleh aturan kerangka "#side>* selain dock" → diperlihatkan.
   2) Sembunyikan Properti / Project Tree kini menyisakan TAB TIPIS di tepi kanan / kiri (klik = buka lagi), tidak hilang total.
   3) Pop-up Rekomendasi sistem muncul lagi setelah ditutup: kini setelah ditutup (×) tidak muncul otomatis lagi sampai pengguna
      membuat / menerapkan desain baru (Buat pit, Terapkan) — tautan "Lihat peringatan" & tombol cari tetap membukanya.
   4) Label RL dasar vs RL bawah galian diperjelas.
   5) Ubah bentuk poligon / garis urat bentuk awal yang sudah digambar: tombol ✎ per area → seret titik, klik titik tengah
      ruas = sisip titik, Shift + klik titik = hapus, Esc / klik ✎ lagi = selesai. */
(function(){const st=document.createElement('style');st.textContent=
 'body.shx #side>.shrz:not(#dock):not(#shpe):not(.shph):not(.x1){display:block!important;left:0}'+
 '.shtab{display:none;order:4;flex:0 0 24px;width:24px;background:var(--sh-pn,#f5f6f8);border-left:1px solid var(--sh-ln,#d6dbe1);cursor:pointer;align-items:flex-start;justify-content:center;padding-top:8px;user-select:none}'+
 '.shtab span{writing-mode:vertical-rl;font:600 11px "Segoe UI",system-ui,Arial;letter-spacing:.06em;color:#51607a;text-transform:uppercase;white-space:nowrap}.shtab b{display:block;margin-bottom:6px;color:#2B5F9E;font-size:13px}.shtab:hover{background:#e8eef7}'+
 '#shTabL{order:0;border-left:0;border-right:1px solid var(--sh-ln,#d6dbe1)}#shTabL span{transform:rotate(180deg)}'+
 'body.shx.sh-noprop #shTabR{display:flex;flex-direction:column;align-items:center}body.shx.sh-notree #shTabL{display:flex;flex-direction:column;align-items:center}';
 document.head.appendChild(st);
 const side=$('side'),L=$('shL');if(!side||!side.parentElement)return;const wrap=side.parentElement;
 const mk=(id,lab,arrow,fn)=>{const d=document.createElement('div');d.id=id;d.className='shtab';d.title='Tampilkan '+lab;d.innerHTML='<b>'+arrow+'</b><span>'+lab+'</span>';d.onclick=fn;return d;};
 wrap.appendChild(mk('shTabR','Properti','«',()=>shProp(true)));wrap.insertBefore(mk('shTabL','Project Tree','»',()=>shTree(true)),wrap.firstChild);})();
/* 3) rekomendasi */
const TDWX={off:false};
{const _w=winShow;winShow=function(w,on){try{if(w&&w.id==='tdw'&&on===true&&TDWX.off&&!window.__TDWFORCE&&!(typeof DMO!=='undefined'&&DMO.on))return;}catch(_){}return _w.apply(this,arguments);};}
document.addEventListener('click',e=>{const t=e.target;if(!t||!t.closest)return;
 if(t.closest('#tdw .x'))TDWX.off=true;
 if(t.closest('#go,#eapply,#eacc,[data-tidy],#tidygo'))TDWX.off=false;
 if(t.id==='tdwo'||t.closest('#tidygo')){window.__TDWFORCE=1;setTimeout(()=>{window.__TDWFORCE=0;},80);}},true);
/* 4) label RL */
(function(){try{const f=$('pZmin');if(f){f.title='Batas TERDALAM galian untuk semua area. Mode Dasar pit: lantai tiap area = RL dasar-nya; isian ini hanya membatasi (opsional). Mode Puncak pit / Batas topo: inilah lantai pit.';}
 const z=document.querySelector('#bz, #pBz, #zbase');
 const lb=$('rllb');if(lb)lb.title='Elevasi lantai area yang sedang / akan digambar (Dasar pit) atau RL crest (Puncak pit). Area berikutnya bisa punya RL sendiri di daftar area.';
 const h=document.querySelector('.rlbox .hint');
 if(h)h.innerHTML='Batas galian untuk semua area (opsional). <b>RL dasar</b> di bawah = lantai area yang digambar; <b>RL bawah galian</b> = batas terdalam — dipakai sebagai lantai pada mode Puncak pit / Batas topo. Isian per area di daftar menimpa nilai ini.';}catch(_){}})();
/* 5) ubah bentuk area */
const BED={on:-1,g:null,drag:null};
function bedZ(a){return isFinite(a.z)?a.z:(BASE&&isFinite(BASE.z)?BASE.z:O[2]);}
function bedTopo(){return !!(BASE&&BASE.mode==='topo');}
/* z titik pegangan: mode Batas topo = di permukaan topografi */function bedPZ(a,p){if(bedTopo()){const z=topoZ(p[0],p[1]);if(isFinite(z))return z;}return bedZ(a);}
function bedDraw(){if(BED.g){BED.g.parent&&BED.g.parent.remove(BED.g);clr(BED.g);BED.g=null;}const a=areas()[BED.on];if(!a)return;const z=bedZ(a)+0.4,g=new THREE.Group(),P=a.src,cl=a.kind!=='line';
 const ln=lineObj((cl?P.concat([P[0]]):P).map(p=>[p[0],p[1],bedTopo()?bedPZ(a,p)+0.4:z]),'#f08c00',false,{depthTest:false});ln.renderOrder=20;g.add(ln);
 const pt=(L,c,s)=>{const m=new THREE.Points(new THREE.BufferGeometry().setFromPoints(L.map(p=>V(p[0],p[1],bedTopo()?bedPZ(a,p)+0.4:z))),new THREE.PointsMaterial({color:c,size:s,sizeAttenuation:false,depthTest:false}));m.renderOrder=21;g.add(m);};
 pt(P,'#ffffff',11);pt(P,'#f08c00',7);const M=[];for(let i=0;i<P.length-(cl?0:1);i++){const b=P[(i+1)%P.length];M.push([(P[i][0]+b[0])/2,(P[i][1]+b[1])/2]);}pt(M,'#f08c00',5);W.add(g);BED.g=g;BED.M=M;}
function bedSet(i){/* batas topo: titik rapat 2 m disederhanakan dulu supaya pegangan sedikit & bentuk tetap */try{if(i>=0&&bedTopo()&&BASE.src.length>40){const r=rdpL(BASE.src.concat([BASE.src[0]]),0.8).slice(0,-1);if(r.length>=3)BASE.src=r.map(p=>[p[0],p[1]]);}}catch(_){}BED.on=i;bedDraw();try{cv.style.cursor=i>=0?'crosshair':'';}catch(_){}document.querySelectorAll('[data-ae]').forEach(b=>b.classList.toggle('on',+b.dataset.ae===i));
 try{const el=$('plinfo');const n=el&&el.querySelector('#bedh');if(n)n.remove();if(i>=0&&el)el.insertAdjacentHTML('afterbegin','<div id="bedh" class="info">✎ <b>Ubah bentuk</b>: seret titik putih · klik titik jingga kecil (tengah ruas) = sisip · Shift + klik titik = hapus · Esc / klik ✎ lagi = selesai. Klik <b>Buat pit</b> untuk membangun ulang.</div>');}catch(_){}}
function bedHit(e){const a=areas()[BED.on];if(!a)return null;const z=bedZ(a),r=R.domElement.getBoundingClientRect(),mx=e.clientX-r.left,my=e.clientY-r.top;let b=null,bd=11;
 a.src.forEach((p,i)=>{const q=scr(p[0],p[1],bedTopo()?bedPZ(a,p):z);const d=Math.hypot(q[0]-mx,q[1]-my);if(d<bd){bd=d;b={v:i};}});if(b)return b;(BED.M||[]).forEach((p,i)=>{const q=scr(p[0],p[1],bedTopo()?bedPZ(a,p):z);const d=Math.hypot(q[0]-mx,q[1]-my);if(d<bd){bd=d;b={m:i};}});return b;}
R.domElement.addEventListener('pointerdown',e=>{if(BED.on<0||e.button!==0||MODE==='edit')return;const a=areas()[BED.on];if(!a)return;const h=bedHit(e);if(!h)return;e.stopImmediatePropagation();e.preventDefault();
 if(h.v!=null&&e.shiftKey){if(a.src.length>(a.kind==='line'?2:3)){a.src.splice(h.v,1);bedDraw();baseApply();try{prmUpd();}catch(_){}}return;}
 let vi=h.v;if(h.m!=null){a.src.splice(h.m+1,0,[BED.M[h.m][0],BED.M[h.m][1]]);vi=h.m+1;}BED.drag={vi,a};CT.enabled=false;bedDraw();},true);
R.domElement.addEventListener('pointermove',e=>{if(!BED.drag)return;const d=BED.drag;let p=null;if(bedTopo()){try{p=hitTopo(e);}catch(_){}}if(!p)p=hitPlane(e,bedZ(d.a));if(!p)return;d.a.src[d.vi]=[p[0],p[1]].concat(d.a.src[d.vi].length>2?[d.a.src[d.vi][2]]:[]);if(!BED.raf)BED.raf=requestAnimationFrame(()=>{BED.raf=0;bedDraw();});});
addEventListener('pointerup',()=>{if(!BED.drag)return;BED.drag=null;CT.enabled=true;try{if(BASE&&BASE.src3&&BASE.mode==='topo'){let s3=null;try{s3=drape(densify(BASE.src.map(p=>[p[0],p[1],p[2]||0]),2));}catch(_){}BASE.src3=(s3&&s3.length>2)?s3:BASE.src.map(p=>[p[0],p[1],topoZ(p[0],p[1])]);}}catch(_){}baseApply();bedDraw();try{if(RES)RES.stale=true;prmUpd();}catch(_){}});
addEventListener('keydown',e=>{if(e.key==='Escape'&&BED.on>=0)bedSet(-1);});
/* tombol ✎ di tiap baris area */
{const _b=baseApply;baseApply=function(){const r=_b.apply(this,arguments);try{const el=$('plinfo');if(el){el.querySelectorAll('.ar').forEach((row,i)=>{if(row.querySelector('[data-ae]'))return;const x=row.querySelector('[data-ai]');const b=document.createElement('button');b.dataset.ae=i;b.title='Ubah bentuk area ini (seret / sisip / hapus titik)';b.innerHTML='&#9998;';if(BED.on===i)b.classList.add('on');b.onclick=ev=>{ev.preventDefault();bedSet(BED.on===i?-1:i);};row.insertBefore(b,x||null);});if(bedTopo()&&!el.querySelector('[data-ae]')){const b=document.createElement('button');b.dataset.ae=0;b.className='sm';b.style.marginTop='4px';b.innerHTML='&#9998; Ubah bentuk batas';b.title='Seret / sisip / hapus titik batas topo';if(BED.on===0)b.classList.add('on');b.onclick=ev=>{ev.preventDefault();bedSet(BED.on===0?-1:0);};el.appendChild(b);}if(BED.on>=0&&!el.querySelector('#bedh'))bedSet(BED.on);}}catch(e){console.warn(e);}if(BED.on>=0&&!areas()[BED.on])bedSet(-1);return r;};}
setInterval(()=>{if(BED.on>=0&&(MODE==='edit'||!BASE))bedSet(-1);},700);
try{baseApply();}catch(_){}
try{window.__PS3.bed={set:i=>bedSet(i),st:()=>BED.on,src:i=>areas()[i].src.map(p=>p.slice()),scr:(i,j)=>{const a=areas()[i],p=a.src[j],q=scr(p[0],p[1],bedZ(a)),r=R.domElement.getBoundingClientRect();return [q[0]+r.left,q[1]+r.top];}};}catch(_){}
/* 6) jendela mengambang bisa dilebarkan / ditinggikan: pegangan di pojok kanan-bawah & tepi kanan (pemilik 24 Nov) */
(function(){const st=document.createElement('style');st.textContent='.flrz{position:absolute;right:0;bottom:0;width:16px;height:16px;cursor:nwse-resize;z-index:5;background:linear-gradient(135deg,transparent 50%,#9aa7b8 50%,#9aa7b8 58%,transparent 58%,transparent 70%,#9aa7b8 70%,#9aa7b8 78%,transparent 78%)}.flrzr{position:absolute;right:0;top:30px;bottom:16px;width:6px;cursor:ew-resize;z-index:5}.flrzr:hover,.flrz:hover{background-color:rgba(43,95,158,.25)}.flw.docked>.flrz,.flw.docked>.flrzr,.dkd>.flrz,.dkd>.flrzr{display:none}';document.head.appendChild(st);
 const arm=w=>{if(w._rz)return;w._rz=1;const flex=getComputedStyle(w).display==='flex';if(getComputedStyle(w).position==='static')w.style.position='absolute';
  for(const [cls,both] of [['flrz',true],['flrzr',false]]){const g=document.createElement('div');g.className=cls;g.title=both?'Seret untuk mengubah ukuran jendela (klik 2× = ukuran semula)':'Seret untuk melebarkan';w.appendChild(g);
   g.addEventListener('dblclick',()=>{w.style.width='';w.style.height='';const b=w.querySelector('.flb');if(b){b.style.maxHeight='';b.style.height='';}});
   g.addEventListener('pointerdown',e=>{e.preventDefault();e.stopPropagation();const r=w.getBoundingClientRect(),x0=e.clientX,y0=e.clientY,b=w.querySelector('.flb'),hh=b?r.height-b.getBoundingClientRect().height:0;g.setPointerCapture(e.pointerId);
    const mv=ev=>{const nw=Math.max(240,Math.min(innerWidth-r.left-4,r.width+ev.clientX-x0));w.style.width=nw+'px';w.style.maxWidth='none';if(both){const nh=Math.max(140,Math.min(innerHeight-r.top-4,r.height+ev.clientY-y0));w.style.height=nh+'px';w.style.maxHeight='none';if(b&&!flex){b.style.maxHeight='none';b.style.height=(nh-hh)+'px';b.style.overflow='auto';}}};
    const up=()=>{g.removeEventListener('pointermove',mv);g.removeEventListener('pointerup',up);try{window.dispatchEvent(new Event('resize'));}catch(_){}};g.addEventListener('pointermove',mv);g.addEventListener('pointerup',up);});}};
 document.addEventListener('pointerover',e=>{const w=e.target&&e.target.closest&&e.target.closest('.flw,#schw,#gtrw,#mbw,#bmw,#sayw');if(w)arm(w);},true);})();
