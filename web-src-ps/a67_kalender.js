/* a67: KALENDER KERJA sebagai pengaturan tersimpan (pemilik 24 Nov: "selain unit, kalender harus bersifat memori, disetting di awal").
   Menu Jadwal → Kalender kerja…: tanggal mulai, shift per hari, hari libur mingguan, tanggal libur. Disimpan (localStorage,
   bersama pengaturan rencana) dan dipakai semua jadwal; di panel Pit Schedule hanya ringkasan + pilihan "tampilkan per". */
const KHARI=['Min','Sen','Sel','Rab','Kam','Jum','Sab'];
function kalSum(){const c=plCfg().cal,off=(c.off||[]).map(Number),lib=String(c.lib||'').split(/[,;\s]+/).filter(Boolean);let d='';try{const x=new Date((c.start||'')+'T00:00:00');d=x.getDate()+' '+PLBL[x.getMonth()]+' '+x.getFullYear();}catch(_){d=c.start;}
 return 'mulai '+d+' · '+(c.sh|0||2)+' shift/hari · '+(off.length?'libur '+off.map(i=>KHARI[i]).join(', '):'7 hari/minggu')+(lib.length?' · '+lib.length+' tanggal libur':'');}
function kalDraw(){const b=$('kalb');if(!b)return;const c=plCfg().cal,off=new Set((c.off||[]).map(Number));
 b.innerHTML='<div class="hint">Disimpan dan dipakai semua jadwal Pit Schedule. Lama jadwal tidak diisi di sini — mengalir dari volume ÷ kapasitas fleet.</div>'+
  '<div class="r">Tanggal mulai <input id="kalst" type="date" value="'+esc(c.start||'')+'"></div>'+
  '<div class="r">Shift per hari <input id="kalsh" type="number" min="1" max="3" step="1" value="'+(c.sh|0||2)+'" style="width:56px"> <span class="hint">(jam kerja per shift diatur di Pengaturan unit)</span></div>'+
  '<div class="r">Libur mingguan '+KHARI.map((h,i)=>'<label style="margin-right:6px"><input type="checkbox" data-ko="'+i+'"'+(off.has(i)?' checked':'')+'> '+h+'</label>').join('')+'</div>'+
  '<div class="r" style="align-items:flex-start">Tanggal libur <textarea id="kallib" rows="3" style="flex:1;min-width:180px" placeholder="2026-12-25, 2027-01-01">'+esc(c.lib||'')+'</textarea></div>'+
  '<div class="hint">Format tanggal: TTTT-BB-HH, dipisah koma atau baris baru.</div><div class="r"><b>Ringkasan:</b>&nbsp;<span id="kalsum">'+esc(kalSum())+'</span></div>';
 const sv=()=>{c.start=$('kalst').value||c.start;c.sh=Math.max(1,Math.min(3,+$('kalsh').value||2));c.off=[...b.querySelectorAll('[data-ko]')].filter(x=>x.checked).map(x=>+x.dataset.ko);c.lib=$('kallib').value.trim();plSave();$('kalsum').textContent=kalSum();try{if(PL.res)plRun();else plUi();}catch(_){try{plUi();}catch(__){}}};
 b.querySelectorAll('input,textarea').forEach(x=>x.onchange=sv);}
function kalOpen(){kalDraw();winShow($('kalw'),true);}
(function(){const w=document.createElement('div');w.id='kalw';w.className='flw win';w.style.width='380px';w.innerHTML='<div class="flh"><b>&#128197; Kalender kerja</b><span class="sp"></span><button class="x">&#10005;</button></div><div class="flb" id="kalb"></div>';
 const iw=$('iw');(iw&&iw.parentNode?iw.parentNode:document.body).insertBefore(w,iw||null);w.querySelector('.x').onclick=()=>winShow(w,false);try{flDrag(w);}catch(_){}/* panel dibuat sesudah dockInit: pasang tombol tempel / lepas (pemilik 25 Nov: panel tidak bisa digeser) */try{dockInit();}catch(_){}
 const st=document.createElement('style');st.textContent='#kalb .r{display:flex;gap:6px;align-items:center;margin:5px 0;flex-wrap:wrap}';document.head.appendChild(st);
 try{const m=[...document.querySelectorAll('.shm')].find(x=>x.firstChild&&x.firstChild.textContent==='Jadwal');if(m){const p=m.querySelector('.shmp'),b=document.createElement('button');b.className='shi';b.dataset.a='kal';b.textContent='📅 Kalender kerja…';b.onclick=()=>{try{shClose();}catch(_){}kalOpen();};const u=p.querySelector('[data-a=unit]');p.insertBefore(b,u?u.nextSibling:null);}}catch(_){}})();
/* warna blok padat mengikuti pilihan warna blok tambang (langkah 2) */
try{const cs=$('mbcol');if(cs)cs.addEventListener('change',()=>{try{if(PL.on){PL.col='kadar';plDraw3d();plUi();}}catch(_){}});}catch(_){}
