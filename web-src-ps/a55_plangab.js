/* a55: Rencana tambang DIGABUNG ke Pit Schedule (23 Nov). Tidak ada menu terpisah lagi.
   Langkah 3 "Urutan gali" memilih CARA GALI:
     klik  = Klik blok (bawaan, manual)   → urutan klik blok tambang, periode mengalir menurut kapasitas fleet
     auto  = Otomatis                     → sistem menyusun urutan bench / strip, target opsional
     jalur = Tarik jalur alat (cara lama) → garis gerak alat, simulasi sel lapis demi lapis
   Klik blok & Otomatis memakai mesin a54 (kalender mengalir, lini waktu, blok padat 3D, kunci, cabang, face position);
   hasilnya tampil di langkah 4. Pilihan diingat (localStorage psSchCara). */
const CARA={v:'klik'};try{const v=localStorage.getItem('psSchCara');if(v==='klik'||v==='auto'||v==='jalur')CARA.v=v;}catch(_){}
function caraPlan(){return CARA.v!=='jalur';}
function caraSchOn(){const w=$('schw');return !!(w&&w.style.display!=='none'&&w.style.display!=='');}
(function(){const b3=$('uxb3'),b4=$('uxb4');if(!b3||!b4)return;
 try{const t=document.querySelector('#uxs3 .uxt');if(t)t.textContent='Urutan gali';}catch(_){}
 const st=document.createElement('style');st.textContent=
 '#cara{display:flex;gap:0;margin:3px 0 4px;border:1px solid #c5ccd8;border-radius:6px;overflow:hidden}#cara button{flex:1;border:0;border-radius:0;padding:5px 4px;background:#f6f7fa;font-weight:600;line-height:1.15}'+
 '#cara button+button{border-left:1px solid #c5ccd8}#cara button.on{background:#2B5F9E;color:#fff}#cara button small{display:block;font-weight:400;font-size:10px;opacity:.8}#carah{font-size:11px;color:#6c757d;margin:0 0 3px}';
 document.head.appendChild(st);
 const seg=document.createElement('div');seg.id='cara';
 seg.innerHTML='<button data-cv="klik" title="Klik blok tambang di 3D; urutan klik = urutan gali">☝ Klik blok<small>manual</small></button>'+
  '<button data-cv="auto" title="Sistem menyusun urutan bench / strip; target per periode opsional">⚙ Otomatis<small>aturan + target</small></button>'+
  '<button data-cv="jalur" title="Tarik garis gerak alat; simulasi sel ±5 m lapis demi lapis (rinci, jangka pendek)">➝ Tarik jalur alat<small>simulasi rinci</small></button>';
 const hint=document.createElement('div');hint.id='carah';
 const J=document.createElement('div');J.id='caraJ';while(b3.firstChild)J.appendChild(b3.firstChild);
 const P=document.createElement('div');P.id='caraP';let pb=$('plwb');if(!pb){pb=document.createElement('div');pb.id='plwb';}P.appendChild(pb);
 b3.appendChild(seg);b3.appendChild(hint);b3.appendChild(P);b3.appendChild(J);
 const S=document.createElement('div');S.id='caraS';while(b4.firstChild)S.appendChild(b4.firstChild);
 const Rr=document.createElement('div');Rr.id='plwr';b4.appendChild(Rr);b4.appendChild(S);
 try{const w=$('plw');if(w)w.remove();}catch(_){}
 seg.onclick=e=>{const x=e.target.closest('[data-cv]');if(x)caraSet(x.dataset.cv,true);};
 caraApply();})();
/* baris "klik blok" lama (tugas sel) disembunyikan — Klik blok kini cara gali sendiri; demo lama tetap memakainya */
function caraApply(){const p=caraPlan(),demo=(typeof DMO!=='undefined'&&DMO.on);
 document.querySelectorAll('#cara [data-cv]').forEach(x=>x.classList.toggle('on',x.dataset.cv===CARA.v));
 const s=(id,on)=>{const e=$(id);if(e)e.style.display=on?'':'none';};s('caraP',p);s('caraJ',!p);s('plwr',p);s('caraS',!p);
 try{const r=$('mbpk')&&$('mbpk').closest('.uxway');if(r)r.style.display=demo?'':'none';}catch(_){}
 const h=$('carah');if(h)h.innerHTML=CARA.v==='klik'?'Klik blok tambang di 3D sesuai urutan gali. Periode terisi sendiri menurut kapasitas fleet — lama jadwal mengalir dari volume.':
  CARA.v==='auto'?'Sistem memilih blok berikutnya menurut aturan urutan. Target per periode boleh dikosongkan.':'Tarik garis arah gali alat di 3D; sistem mensimulasikan galian sel lapis demi lapis.';}
function caraSet(v,user){if(v!=='klik'&&v!=='auto'&&v!=='jalur')return;const was=CARA.v;CARA.v=v;try{localStorage.setItem('psSchCara',v);}catch(_){}
 try{if(SCH.dig)schDigEnd(false);}catch(_){}try{mbPick(false);}catch(_){}
 if(caraPlan()){const c=plCfg();c.mode=v==='auto'?'auto':'man';plSave();if(was!==v&&PL.res&&PL.res.man!==(v!=='auto'))PL.res=null;
  if(v==='auto'&&PL.pick==='q')PL.pick=false;if(user&&v==='klik'&&MB.R)PL.pick='q';
  PL.on=caraSchOn();try{$('cv').style.cursor=PL.pick?'pointer':'';}catch(_){}
  if(!MB.R&&PL.on){try{mbAutoCalc();}catch(_){}}}
 else{PL.pick=false;plStop();PL.on=false;try{$('cv').style.cursor='';}catch(_){}}
 caraApply();try{plUi();plDraw3d();plTL();}catch(_){}try{if(MB.R)mbDraw();}catch(_){}try{UX.sel=3;uxSync(true);}catch(_){}}
/* dipanggil oleh menu lama / Project Tree: buka Pit Schedule di langkah 3 */
function caraOpen(){if(!caraSchOn()){const b=$('mbsch');if(b)b.click();else schOpen(true);}if(!caraPlan())caraSet('klik');else caraSet(CARA.v);try{UX.sel=3;uxSync(true);}catch(_){}}
/* panel Pit Schedule dibuka / ditutup → blok padat & lini waktu ikut */
{const _o=schOpen;schOpen=function(on){const r=_o.apply(this,arguments);try{if(on&&typeof DMO!=='undefined'&&DMO.on&&CARA.v!=='jalur'){CARA._dm=CARA.v;CARA.v='jalur';}
  if(!on&&CARA._dm&&!(typeof DMO!=='undefined'&&DMO.on)){CARA.v=CARA._dm;CARA._dm=null;}
  if(on&&caraPlan()){PL.on=true;caraApply();plUi();plDraw3d();plTL();}else{PL.pick=false;plStop();PL.on=false;caraApply();plDraw3d();plTL();if(on&&MB.R)mbDraw();}}catch(e){console.warn('cara',e);}return r;};}
/* status langkah 3 & 4 mengikuti cara gali */
{const _s=uxState;uxState=function(){const X=_s.apply(this,arguments);if(!caraPlan())return X;try{const r=PL.res,q=PL.q?PL.q.length-(PL.qN|0):0;
 X.d[2]=!!r;X.d[3]=!!r;X.I[2]=r?''+r.done.size+' blok · '+r.P.length+' periode'+(q>0?' · '+q+' menunggu Jalankan':''):CARA.v==='klik'?(q?q+' blok dipilih → ▶ Jalankan':MB.R?'klik blok di 3D':'setelah blok tambang ada'):'otomatis → ▶ Jalankan';
 if(r){let o=0,m=0;for(const p of r.P){o+=p.ore;m+=p.met;}const L=r.P[r.P.length-1];X.I[3]=(L?'selesai '+plDay(L.d1)+' '+L.d1.getFullYear()+' · ':'')+gtShort(o)+' t ore'+(o>0?' @ '+(m/o).toFixed(2)+' g/t':'');}else X.I[3]='muncul setelah Jalankan';
 X.cur=!X.d[0]?0:(!r||PL.pick)?2:3;}catch(_){}return X;};}
/* susun periode / klik blok → status langkah diperbarui */
{const _r=plRun;plRun=function(){const r=_r.apply(this,arguments);try{uxSync(true);}catch(_){}return r;};}
try{window.__PS3.cara={get:()=>CARA.v,set:v=>caraSet(v),open:()=>caraOpen(),scr:key=>{const [k,sb]=[+key.split('|')[0],key.split('|').slice(1).join('|')],CM=plCells(),Gd=SCH.grid,c=CM&&CM.get(sb);if(!c)return null;const cc=c[c.length>>1],i=cc%Gd.nx,j=(cc-i)/Gd.nx,w=schCorner(Gd,i+0.5,j+0.5),z=Math.min(Gd.z0[cc],(k+1)*MB.R.bhE),q=scr(w[0],w[1],z),r=R.domElement.getBoundingClientRect();return [q[0]+r.left,q[1]+r.top,q[2]];}};}catch(_){}
