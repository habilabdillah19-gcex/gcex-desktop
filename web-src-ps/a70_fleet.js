/* a70 · Kartu fleet (Tarik jalur) ringkas: rincian alat tertutup bawaan, satu baris ringkasan (24 Nov 2026, pemilik: "masih kepanjangan ke bawah… bisa ditutup") */
{const _e=schEdit;schEdit=function(){const r=_e.apply(this,arguments);try{const el=$('sched');if(!el||el.style.display==='none'||!el.firstChild||el.querySelector('#schedd'))return r;
  if(SCH.eOpen==null){try{SCH.eOpen=localStorage.getItem('psSchEd')==='1';}catch(_){SCH.eOpen=false;}}
  const fg=typeof SCH.sel==='string'?SCH.sel.slice(2):null,FL=fg?schFleets().get(fg):null,t=FL?FL[0]:SCH.tasks.find(x=>x.id===SCH.sel);if(!t)return r;
  const d=document.createElement('details');d.id='schedd';d.open=!!SCH.eOpen||DMO.on;const s=document.createElement('summary');s.style.cssText='cursor:pointer;font-size:11.5px;color:#5b3a12;line-height:1.35';
  const al=(SCHA.find(a=>a[0]===t.alat)||[0,t.alat])[1];
  s.innerHTML='<b style="color:'+t.col+'">'+(FL?'Fleet '+esc(fg):esc(t.nm))+'</b> · '+esc(al)+' × '+Math.max(1,t.nu|0)+' · <b>'+schF(schCap(t))+'</b> BCM/sh'+(FL?' · jalur baru '+(t.nbN||t.nb||1)+' kotak × '+(t.flN||t.fl||1)+' lapis':'')+' <span style="color:#1d5fd1">· atur</span>';
  s.title='Klik untuk membuka / menutup pengaturan alat, lantai, angkut dan daftar jalur';
  while(el.firstChild)d.appendChild(el.firstChild);d.insertBefore(s,d.firstChild);el.appendChild(d);
  d.addEventListener('toggle',()=>{if(DMO.on)return;SCH.eOpen=d.open;try{localStorage.setItem('psSchEd',d.open?'1':'0');}catch(_){}});}catch(e){console.warn('ringkas',e);}return r;};}
