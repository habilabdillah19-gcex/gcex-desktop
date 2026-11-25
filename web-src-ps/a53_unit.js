/* a53: PENGATURAN UNIT (pustaka alat gali) — pemilik 23 Nov 2026: "Pengaturan unit dibuat di menu terpisah … tidak perlu diisi ulang
   kalau unitnya masih sama". Seperti perangkat lunak penjadwalan tambang (setelan peralatan dibuat sekali di setup, fleet tinggal
   memakainya): tiap unit menyimpan jenis alat, bucket, fill factor, cycle, efisiensi, swell, jam jadwal, PA, UA. Disimpan di komputer
   (localStorage psUnitLib); bila belum diatur dipakai nilai bawaan. Kartu fleet cukup memilih unit + jumlah; angka rinci disembunyikan
   (ringkasan satu baris). Mengubah unit di pustaka langsung berlaku ke semua fleet yang memakainya. */
const ULF=['alat','bkt','ff','cyc','eff','sw','sch','pa','ua','prod'];
function ulDef(){return SCHA.filter(a=>a[0]!=='man').map(a=>({id:'u_'+a[0],nm:a[1].replace(/^Excavator kelas /,'Excavator ').replace(/\s*\(/,' (')
 ,alat:a[0],bkt:a[2],ff:0.85,cyc:a[3],eff:0.83,sw:30,sch:11,pa:90,ua:80,prod:0}));}
let UL=null;function ulGet(){if(UL)return UL;try{UL=JSON.parse(localStorage.getItem('psUnitLib')||'null');}catch(_){UL=null;}if(!Array.isArray(UL)||!UL.length)UL=ulDef();return UL;}
function ulSave(){try{localStorage.setItem('psUnitLib',JSON.stringify(UL));}catch(_){}}
function ulApply(t,u){if(!t||!u)return;for(const k of ULF)if(u[k]!==undefined)t[k]=u[k];t.pm2=u.alat==='man'?'man':'bkt';t.ulib=u.id;}
function ulSum(u){const f=(v,d)=>schF(+v,d);return u.alat==='man'?f(u.prod)+' BCM/jam':'bucket '+f(u.bkt,1)+' m³ · FF '+f(u.ff,2)+' · cycle '+f(u.cyc)+' s · efisiensi '+f(u.eff,2)+' · swell '+f(u.sw)+'%'+' · jam '+f(u.sch)+' · PA '+f(u.pa)+'% · UA '+f(u.ua)+'%';}
function ulPropagate(u){let n=0;for(const t of SCH.tasks)if(t.ulib===u.id){ulApply(t,u);n++;}if(n){try{schTasks();schDrawStatic();}catch(_){}try{schMsg('Unit "'+esc(u.nm)+'" diperbarui di '+n+' jalur / area — tekan <b>Jalankan</b> untuk menghitung ulang.');}catch(_){}}}
function ulOpen(){ulDraw();winShow($('ulw'),true);}
function ulDraw(){const b=$('ulwb');if(!b)return;const L=ulGet(),n=(k,v,st)=>'<input data-f="'+k+'" type="number" step="any" value="'+v+'" style="width:'+(st||52)+'px">';
 let h='<div class="hint" style="margin-bottom:6px">Atur sekali, dipakai semua fleet. Disimpan di komputer ini; fleet yang memakai unit ikut berubah.</div>';
 for(const u of L){h+='<div class="ulu" data-id="'+u.id+'" style="border:1px solid #D3CDC1;border-left:3px solid #B5893E;border-radius:4px;padding:5px 7px;margin:5px 0;background:#fff">'+
  '<div style="display:flex;gap:6px;align-items:center"><input data-f="nm" type="text" value="'+esc(u.nm)+'" style="flex:1;font-weight:600"><select data-f="alat">'+SCHA.map(a=>'<option value="'+a[0]+'"'+(a[0]===u.alat?' selected':'')+'>'+esc(a[1].replace(/ \(.*$/,''))+'</option>').join('')+'</select><button data-x title="Hapus unit">&#10005;</button></div>'+
  (u.alat==='man'?'<div class="r" style="margin-top:4px">produktivitas '+n('prod',u.prod,70)+' BCM/jam</div>':'<div style="margin-top:4px;display:grid;grid-template-columns:auto auto auto auto auto auto;gap:3px 6px;align-items:center;font-size:11.5px">bucket '+n('bkt',u.bkt)+' FF '+n('ff',u.ff)+' cycle (s) '+n('cyc',u.cyc)+'efisiensi '+n('eff',u.eff)+' swell % '+n('sw',u.sw)+'<span></span><span></span></div>')+
  '<div style="margin-top:3px;display:flex;gap:6px;align-items:center;font-size:11.5px">jam/shift '+n('sch',u.sch,46)+' PA % '+n('pa',u.pa,46)+' UA % '+n('ua',u.ua,46)+'</div>'+
  '<div style="font-size:11px;color:#5b3a12;margin-top:2px">≈ '+schF(ulCap(u))+' BCM/shift per unit</div></div>';}
 h+='<div style="display:flex;gap:6px;margin-top:6px"><button id="uladd" class="pri">+ Tambah unit</button><button id="ulrst" title="Kembalikan daftar bawaan">Kembalikan bawaan</button></div>';
 b.innerHTML=h;
 b.querySelectorAll('.ulu').forEach(d=>{const u=L.find(x=>x.id===d.dataset.id);d.querySelectorAll('[data-f]').forEach(c=>c.onchange=()=>{const k=c.dataset.f;u[k]=c.type==='number'?+c.value:c.value;if(k==='alat'){const a=SCHA.find(x=>x[0]===u.alat);if(a&&a[2]){u.bkt=a[2];u.cyc=a[3];}}ulSave();ulPropagate(u);ulDraw();});
  d.querySelector('[data-x]').onclick=()=>{if(L.length<=1)return;if(SCH.tasks.some(t=>t.ulib===u.id)&&!confirm('Unit ini dipakai fleet. Hapus? (fleet tetap memakai angka terakhir, menjadi atur manual)'))return;for(const t of SCH.tasks)if(t.ulib===u.id)delete t.ulib;L.splice(L.indexOf(u),1);ulSave();ulDraw();try{schEdit();}catch(_){}};});
 $('uladd').onclick=()=>{const base=L[L.length-1]||ulDef()[0],u=Object.assign({},base,{id:'u_'+Date.now().toString(36),nm:'Unit baru'});L.push(u);ulSave();ulDraw();};
 $('ulrst').onclick=()=>{if(!confirm('Kembalikan daftar unit bawaan? Unit buatan sendiri dihapus.'))return;UL=ulDef();ulSave();for(const t of SCH.tasks){const u=UL.find(x=>x.id===t.ulib);if(u)ulApply(t,u);else delete t.ulib;}ulDraw();try{schEdit();}catch(_){}};}
function ulCap(u){try{const t=Object.assign({nu:1,pm2:u.alat==='man'?'man':'bkt'},u);return schCap(t);}catch(_){return 0;}}
/* kartu fleet: pilih unit dari pustaka; rincian disembunyikan */
{const _e=schEdit;schEdit=function(){const r=_e.apply(this,arguments);try{const el=$('sched');if(!el||el.style.display==='none')return r;const F=schFleets(),fg=typeof SCH.sel==='string'?SCH.sel.slice(2):null,FL=fg?F.get(fg):null,t=FL?FL[0]:SCH.tasks.find(x=>x.id===SCH.sel);if(!t)return r;
 const L=ulGet(),u=L.find(x=>x.id===t.ulib),sa=el.querySelector('select[data-k="alat"]');if(!sa)return r;const row=sa.closest('.r');
 const us=document.createElement('select');us.title='Unit dari Pengaturan unit (menu Jadwal)';us.innerHTML=L.map(x=>'<option value="'+x.id+'"'+(u&&x.id===u.id?' selected':'')+'>'+esc(x.nm)+'</option>').join('')+'<option value=""'+(u?'':' selected')+'>(atur manual)</option>';row.insertBefore(us,sa);
 const go=document.createElement('a');go.href='#';go.textContent='⚙ unit';go.title='Buka Pengaturan unit';go.style.cssText='font-size:11px;margin-left:4px';go.onclick=e=>{e.preventDefault();ulOpen();};row.appendChild(go);
 us.onchange=()=>{const v=L.find(x=>x.id===us.value),tg=FL||[t];for(const l of tg){if(v)ulApply(l,v);else delete l.ulib;}try{uxEqSave();}catch(_){}schTasks();schDrawStatic();};
 if(u){sa.style.display='none';const rs=el.querySelector('[data-k="sch"]');if(rs)rs.closest('.r').style.display='none';
  const s1=document.createElement('div');s1.className='r';s1.style.cssText='font-size:11px;color:#6c757d;margin-top:-2px';s1.textContent=ulSum(u);row.insertAdjacentElement('afterend',s1);
  const bk=el.querySelector('#schadv2 [data-k="bkt"]');if(bk)bk.closest('.r').style.display='none';const st=el.querySelector('#schadv2 [data-k="start"]');if(st){const r2=st.closest('.r');const nr=document.createElement('div');nr.className='r';nr.append('mulai shift ',st);r2.replaceWith(nr);}}}catch(e){console.warn('unit',e);}return r;};}
/* fleet / area baru tanpa pilihan tersimpan → unit pustaka yang cocok dengan jenis alatnya */
try{UXEQ.push('ulib');}catch(_){}
{const _a=schAdd;schAdd=function(type,P,o){const r=_a.apply(this,arguments);try{const t=SCH.tasks[SCH.tasks.length-1];if(t&&(t.type==='line'||t.type==='poly')){const L=ulGet();let u=L.find(x=>x.id===t.ulib);if(!u&&!t.ulib)u=L.find(x=>x.alat===t.alat);if(u)ulApply(t,u);}}catch(_){}return r;};}
try{if(SCH.jOpen===undefined)SCH.jOpen=false;if(SCH.aOpen===undefined)SCH.aOpen=false;}catch(_){}
