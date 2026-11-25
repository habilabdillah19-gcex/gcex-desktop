/* a69 · Tombol cepat "Reset" di bilah alat (24 Nov 2026, permintaan pemilik)
   Satu tombol, isi menurut konteks:
   - Pit Schedule terbuka → Hapus hasil jadwal (jalur / urutan tetap) · Kosongkan jadwal (batas area tetap)
   - Desain baru          → Hapus hasil Pit final / Staging (bentuk awal, geoteknik, jalan tetap)
   - Edit pit             → Batalkan semua edit (kembali ke pit awal)
   Juga: caraOpen mengingat cara gali terakhir (dulu memaksa "Klik blok"). */
function rsSchOn(){try{return caraSchOn();}catch(_){return false;}}
function rsAfter(){try{schTasks();schDrawStatic();schPhBar();}catch(_){}try{plUi();plDraw3d();plTL();}catch(_){}try{if(MB.R)mbDraw();}catch(_){}try{uxSync(true);}catch(_){}try{SH.sig='';shTreeDraw();}catch(_){}try{legend();}catch(_){}}
/* hasil jadwal fase aktif dibuang; jalur gali, antrean klik blok, batas, blok tambang tetap */
function rsSchRes(){const ph=schPh();if(ph.lock)throw new Error(ph.nm+' sudah dikunci — buka kunci dulu.');schStop();schDigEnd(false);
 if(SCH.mesh){SCH.g.remove(SCH.mesh);clr(SCH.mesh);SCH.mesh=null;}for(const m of SCH.mk){SCH.g.remove(m);clr(m);}SCH.mk=[];if(SCH.tkG)SCH.tkG.visible=false;schShow(false);
 SCH.sim=null;ph.sim=null;ph.out=null;SCH.p=-1;SCH.pi=-1;SCH.cur=null;SCH.curp=-2;SCHFD.res=[];try{$('schfdr').innerHTML='';if(SCH.fdG)while(SCH.fdG.children.length){const c=SCH.fdG.children[0];SCH.fdG.remove(c);clr(c);}}catch(_){}
 try{$('schres').style.display='none';}catch(_){}try{KDL.ran=new Set();}catch(_){}
 try{plStop();PL.res=null;PL.qN=0;}catch(_){}rsAfter();schMsg('Hasil jadwal dihapus. Jalur / urutan gali masih ada — tekan <b>▶ Jalankan</b> untuk menghitung ulang.');}
/* semua jalur, urutan & hasil dibuang; batas area (langkah 1) dan block model tetap */
function rsSchAll(){if(SCH.phs.some(f=>f.lock)&&!confirm('Ada fase yang sudah dikunci. Kosongkan semuanya?'))return;const bnd=SCH.phs[0]&&SCH.phs[0].bnd,ref=SCH.refId;
 schReset();try{if(bnd)schPh().bnd=bnd;SCH.refId=ref;}catch(_){}try{plStop();PL.q=[];PL.qN=0;PL.res=null;PL.lock.clear();PL.pick=false;}catch(_){}
 try{caraSet(CARA.v);}catch(_){}rsAfter();try{mbAutoCalc();}catch(_){}schMsg('Jadwal dikosongkan. Batas area tetap — mulai lagi dari langkah 3.');}
function rsDes(){const st=MODE==='stage';if(st)STG=null;else RES=null;try{if(MST[MODE]){MST[MODE].res='';MST[MODE].st5='';}}catch(_){}
 for(const k of ['pit','str','lab','tmp'])try{clr(G[k]);}catch(_){}try{$('res').innerHTML='';stepSt('s5','',false);}catch(_){}try{TIDY_RES=null;const w=$('tdw');if(w)w.style.display='none';}catch(_){}
 try{pitRedraw();}catch(_){}rsAfter();try{$('res').innerHTML='<div class="hint">Hasil '+(st?'Staging':'Pit final')+' dihapus. Bentuk awal, geoteknik dan jalan tetap — klik <b>Buat pit</b> untuk membangun ulang.</div>';}catch(_){}}
function rsEdit(){if(!ED||!EH.st.length)return;ehGo(0);rsAfter();}
function rsItems(){const it=[];
 if(rsSchOn()){const has=!!SCH.sim||!!(PL.res),any=has||SCH.tasks.length||PL.q.length;
  it.push({t:'Hapus hasil jadwal',s:'jalur / urutan gali tetap',dis:!has,fn:rsSchRes});
  it.push({t:'Kosongkan jadwal',s:'jalur, urutan & hasil dihapus · batas area tetap',dis:!any,cf:'Kosongkan seluruh jalur, urutan gali dan hasil jadwal?',fn:rsSchAll});}
 else if(MODE==='edit')it.push({t:'Batalkan semua edit',s:'kembali ke pit awal (masih bisa Ctrl+Y)',dis:!(ED&&EH.i>0),fn:rsEdit});
 else{const st=MODE==='stage',has=!!(st?STG:RES);it.push({t:'Hapus hasil '+(st?'Staging':'Pit final'),s:'bentuk awal, geoteknik, jalan tetap',dis:!has,cf:'Hapus hasil desain '+(st?'Staging':'Pit final')+'?',fn:rsDes});}
 return it;}
function rsMenu(btn){let m=$('rsm');if(m){m.remove();return;}const it=rsItems();m=document.createElement('div');m.id='rsm';const r=btn.getBoundingClientRect();
 m.style.cssText='position:fixed;z-index:9000;left:'+Math.max(4,Math.min(innerWidth-270,r.left))+'px;top:'+(r.bottom+3)+'px;width:262px;background:#fff;border:1px solid #c9d3e1;border-radius:6px;box-shadow:0 6px 20px rgba(0,0,0,.18);padding:4px;font-size:12.5px';
 m.innerHTML='<div style="padding:3px 8px;color:#6c757d;font-size:11px">'+(rsSchOn()?'Pit Schedule':MODE==='edit'?'Edit pit':'Desain')+'</div>'+it.map((x,i)=>'<button data-i="'+i+'"'+(x.dis?' disabled':'')+' style="display:block;width:100%;text-align:left;border:0;background:none;padding:6px 8px;border-radius:4px;cursor:'+(x.dis?'default':'pointer')+';opacity:'+(x.dis?.45:1)+'"><b style="color:#c92a2a">'+x.t+'</b><br><span style="color:#6c757d;font-size:11px">'+x.s+(x.dis?' · belum ada':'')+'</span></button>').join('');
 document.body.appendChild(m);m.onclick=e=>{const b=e.target.closest('button[data-i]');if(!b||b.disabled)return;const x=it[+b.dataset.i];m.remove();if(x.cf&&!confirm(x.cf))return;try{x.fn();}catch(err){alert(err.message);}try{tbState();}catch(_){}};
 setTimeout(()=>{const off=e=>{if(!m.contains(e.target)&&e.target!==btn&&!btn.contains(e.target)){m.remove();removeEventListener('pointerdown',off,true);}};addEventListener('pointerdown',off,true);},0);}
{const _b=tbBuild;tbBuild=function(){_b();const T=$('ptb');if(!T||$('ptbr'))return;const b=document.createElement('button');b.id='ptbr';b.className='tb';b.title='Reset / hapus hasil yang sudah dijalankan (jadwal atau desain, menurut panel yang sedang terbuka)';b.innerHTML='<i style="color:#c92a2a">&#8634;</i><span style="color:#c92a2a">Reset</span>';b.onclick=()=>rsMenu(b);T.insertAdjacentHTML('beforeend','<span class="ts"></span>');T.appendChild(b);};}
try{tbBuild();}catch(e){console.warn('rs',e);}
/* buka ulang Pit Schedule lewat menu / Project Tree: cara gali terakhir diingat */
caraOpen=function(){if(!caraSchOn()){const b=$('mbsch');if(b)b.click();else schOpen(true);}caraSet(CARA.v);try{UX.sel=3;uxSync(true);}catch(_){}};
try{window.__PS3.rs={items:()=>rsItems().map(x=>[x.t,!x.dis]),schRes:()=>rsSchRes(),schAll:()=>rsSchAll(),des:()=>rsDes(),edit:()=>rsEdit()};}catch(_){}
