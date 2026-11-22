/* a34: review sinkronisasi menu & UI/UX (19 Nov 2026).
   1) Bilah menu responsif (1280–1560 px): padding/huruf mengecil, chip status dipotong elipsis — tidak ada menu yang tersembunyi.
   2) Urutan jendela: Pit Schedule & Sayatan memakai skema "klik = ke depan" yang sama dengan jendela lain, selalu di bawah menu tarik-turun.
   3) Mode gambar saling eksklusif: menggambar desain / sayatan / jalur gali tidak bisa aktif bersamaan.
   4) Panel Lapisan ikut menampilkan Pit Schedule (permukaan, kontur teras, alat & DT, jalur fleet) dan garis Sayatan.
   5) Project baru / muat project → jadwal direset (jadwal terikat topografi). */
(function(){const st=document.createElement('style');st.textContent=
`#dbar .chip{max-width:170px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
@media (max-width:1580px){#mbar .mbb{padding-left:5px!important;padding-right:5px!important}#mbar .sep{margin:0 3px!important}#dbar .chip{max-width:120px}}
@media (max-width:1440px){#mbar .mbb{font-size:12px!important;padding-left:4px!important;padding-right:4px!important}#pjname{max-width:92px;overflow:hidden;text-overflow:ellipsis}#mbar #tabs .tb,#mbar #tabs button{padding-left:6px!important;padding-right:6px!important}#dbar .chip{max-width:30px!important;padding-left:7px!important;padding-right:4px!important}#dbar .chip:hover{max-width:260px!important;position:relative;z-index:5}}
@media (max-width:1320px){#mbar .brand .bx{display:none}#pjname{max-width:62px}#mbar .mbb{font-size:11.5px!important;padding-left:3px!important;padding-right:3px!important}}
#schw,#sayw{z-index:40}`;document.head.appendChild(st);})();
/* 2) ke depan saat diklik — tetap di bawah .cmenu (z 60) dan bilah demo */
(function(){let top=40;const raise=w=>{let m=0;document.querySelectorAll('.flw.win,#schw,#sayw').forEach(x=>{const z=+getComputedStyle(x).zIndex||0;if(x!==w&&z>m&&z<60)m=z;});top=Math.min(58,Math.max(top,m)+1);w.style.zIndex=top;};
 for(const id of ['schw','sayw']){const w=$(id);if(w)w.addEventListener('mousedown',()=>raise(w),true);}
 const ob=$('mbsch'),os=$('mbsay');if(ob)ob.addEventListener('click',()=>{const w=$('schw');if(w)raise(w);});if(os)os.addEventListener('click',()=>setTimeout(()=>{const w=$('sayw');if(w&&w.style.display!=='none')raise(w);},0));})();
/* 3) mode gambar saling eksklusif */
{const _s=schDigStart;schDigStart=function(){try{if(SAY.pick)sayPickToggle(false);}catch(_){}try{if(typeof DG!=='undefined'&&DG)digStop();}catch(_){}return _s.apply(this,arguments);};}
{const _p=sayPickToggle;sayPickToggle=function(on){const want=on===undefined?!SAY.pick:on;if(want){try{if(SCH.dig)schDigEnd(false);}catch(_){}try{if(typeof DG!=='undefined'&&DG)digStop();}catch(_){}}return _p.apply(this,arguments);};}
try{const _ds=digStart;digStart=function(){try{if(SCH.dig)schDigEnd(false);}catch(_){}try{if(SAY.pick)sayPickToggle(false);}catch(_){}return _ds.apply(this,arguments);};}catch(_){}
/* 4) Panel Lapisan: baris Pit Schedule & Sayatan */
{const _l=window.layRender;window.layRender=function(){const r=_l.apply(this,arguments);try{const el=$('layb');if(!el)return r;const rows=[];
  if(SCH.sim&&SCH.mesh){rows.push({nm:'Pit Schedule · permukaan',col:'#e8590c',vis:()=>SCH.show&&SCH.mesh.visible,set:v=>{$('schshw').checked=v;schShow(v);}});
   rows.push({nm:'Pit Schedule · kontur teras',col:'#3d2608',vis:()=>$('schct').checked,set:v=>{$('schct').checked=v;schPaint();}});
   rows.push({nm:'Pit Schedule · alat & DT',col:'#f2b705',vis:()=>SCH.mk.some(m=>m.visible!==false)&&(!SCH.tkG||SCH.tkG.visible!==false)&&!SCH.hideEq,set:v=>{SCH.hideEq=!v;for(const m of SCH.mk)m.visible=v;if(SCH.tkG)SCH.tkG.visible=v;if(v)schPaint();}});}
  if(SCH.gs&&SCH.gs.children.length)rows.push({nm:'Pit Schedule · jalur & batas',col:'#c9a77a',vis:()=>SCH.gs.visible,set:v=>SCH.gs.visible=v});
  if(typeof SAY!=='undefined'&&SAY.a)rows.push({nm:'Sayatan · garis A→B',col:'#e8590c',vis:()=>!SAY.hideLine,set:v=>{SAY.hideLine=!v;try{sayLine3D();}catch(_){}}});
  for(const r2 of rows){const d=document.createElement('div');d.className='lrow';d.innerHTML='<input type="checkbox"'+(r2.vis()?' checked':'')+'><i style="background:'+r2.col+'"></i><span class="t" title="'+esc(r2.nm)+'">'+esc(r2.nm)+'</span>';d.querySelector('input').onchange=e=>r2.set(e.target.checked);el.appendChild(d);}}catch(e){console.warn('lay sch',e);}return r;};}
/* alat & DT tetap tersembunyi bila dimatikan di Lapisan */
{const _p=schPaint;schPaint=function(){const r=_p.apply(this,arguments);if(SCH.hideEq){for(const m of SCH.mk)m.visible=false;if(SCH.tkG)SCH.tkG.visible=false;}return r;};}
{const _a=schAnimStep;schAnimStep=function(){if(SCH.hideEq){if(SCH.tkG)SCH.tkG.visible=false;return;}return _a.apply(this,arguments);};}
/* panel Lapisan diperbarui saat jadwal berubah */
{const _f=schRun;schRun=function(){const r=_f.apply(this,arguments);try{layRender();}catch(_){}return r;};}
{const _f=schShow;schShow=function(){const r=_f.apply(this,arguments);try{layRender();}catch(_){}return r;};}
{const _f=schReset;schReset=function(){const r=_f.apply(this,arguments);try{layRender();}catch(_){}return r;};}
{const _f=sayUpd;sayUpd=function(){const r=_f.apply(this,arguments);try{layRender();}catch(_){}return r;};}
/* garis sayatan di 3D bisa disembunyikan dari Lapisan */
try{const _sl=sayLine3D;sayLine3D=function(){const r=_sl.apply(this,arguments);try{if(SAY.hideLine&&G.say)G.say.visible=false;else if(G.say)G.say.visible=true;}catch(_){}return r;};}catch(_){}
/* 5) project baru / muat project: jadwal direset */
try{const _r=pjReset;pjReset=function(){const r=_r.apply(this,arguments);try{schReset();$('schw').style.display='none';$('mbsch').classList.remove('sch-on');}catch(_){}return r;};}catch(_){}
