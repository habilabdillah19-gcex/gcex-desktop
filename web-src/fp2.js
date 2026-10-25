
/* ================= FOLDER PROYEK v2: folder per proyek, bilah peringatan, perangkat sama, cek izin, retry, konflik, peringatan tutup ================= */
FP.dev=(function(){var d='';try{d=localStorage.getItem('gcex_dev')||'';if(!d){d='d'+Date.now().toString(36)+Math.random().toString(36).slice(2,8);localStorage.setItem('gcex_dev',d);}}catch(e){d='d'+FP.sess;}return d;})();
FP.PERMMS=15000;
/* --- komputer (profil browser) yang sama bukan "orang lain" --- */
FP.lockFree=function(L){return !L||L.session===FP.sess||(L.dev&&L.dev===FP.dev)||(Date.now()-(L.beat||0))>FP.STALE;};
FP.lockWrite=async function(){if(!FP.dir||FP.ro)return;var L={user:FP.user(),session:FP.sess,dev:FP.dev,since:FP.since||(FP.since=Date.now()),beat:Date.now(),app:'GC-Ex',ua:navigator.userAgent.slice(0,80)};
  try{var cur=await FP.lockRead();if(cur&&!FP.lockFree(cur)&&!FP.take){FP.ro=true;FP.roBy=cur.user;FP.ind();FP.toast('Proyek sekarang dipakai <b>'+esc(cur.user)+'</b> di komputer lain. GC-Ex Anda beralih ke hanya-baca agar tidak saling menimpa.',true,0);return;}
    await FP.write(FP.dir,FP.LOCKF,JSON.stringify(L));FP.take=false;}catch(e){}};
/* --- peta proyek -> folder & rev terakhir --- */
FP.mapGet=function(nm){return nm?idbGet('fpDirP:'+nm):Promise.resolve(null);};
FP.mapSet=async function(nm,h){if(nm&&h){try{await idbPut('fpDirP:'+nm,h);await idbPut('fpDir',h);}catch(e){}}};
FP.revSet=function(nm){if(nm&&FP.dir)try{idbPut('fpRevP:'+nm,{rev:FP.base,at:Date.now(),dir:FP.dir.name});}catch(e){}};
/* --- bilah peringatan persisten --- */
FP.bar=function(){var b=E('fpBar');if(!b){b=document.createElement('div');b.id='fpBar';document.body.appendChild(b);}
  var tip='<div class=fptip>Saat browser bertanya, pilih <b>&ldquo;Izinkan pada setiap kunjungan&rdquo;</b> (Allow on every visit) bila tersedia, supaya tidak perlu mengizinkan lagi setiap kali GC-Ex dibuka.</div>',h='';
  if(!SA.pname||(E('imp')&&!E('imp').classList.contains('off')&&!FP.dir&&!FP.pendDir)){b.style.display='none';return;}
  if(FP.conf){var M=FP.conf;h='<div class=fpmsg><b>&#9888; Folder berisi versi yang lebih baru.</b> Rev '+(M.rev||'?')+' disimpan oleh <b>'+esc(M.savedBy||'pengguna lain')+'</b>'+(M.savedAt?' ('+new Date(M.savedAt).toLocaleString()+')':'')+'; versi Anda di browser berbeda. Pilih versi yang dipakai:</div><div class=fpbtn><button class=pri onclick="FP.confLoad(1)">&#8635; Muat versi folder</button><button onclick="FP.confKeep(1)">Pakai versi saya</button></div>';}
  else if(!FP.dir&&FP.pendDir){h='<div class=fpmsg><b>&#128193; Proyek ini tersimpan di folder &ldquo;'+esc(FP.pendDir.name)+'&rdquo;</b>, tetapi izin akses folder belum diberikan. Perubahan saat ini hanya tersimpan di browser.</div><div class=fpbtn><button class=pri onclick="FP.connectNow()">&#128279; Hubungkan sekarang</button></div>'+tip;}
  else if(FP.dir&&FP.err){var pm=FP.permLost||/izin|NotAllowed|Security/i.test(FP.err);h='<div class=fpmsg><b>&#9888; '+(pm?'Izin folder &ldquo;'+esc(FP.dir.name)+'&rdquo; belum ada / dicabut.':'Gagal menyimpan ke folder &ldquo;'+esc(FP.dir.name)+'&rdquo;.')+'</b> '+(pm?'Perubahan ditahan di browser sampai folder terhubung lagi.':esc(FP.err)+'. GC-Ex mencoba lagi otomatis tiap 15 detik.')+'</div><div class=fpbtn>'+(pm?'<button class=pri onclick="FP.connectNow()">&#128279; Hubungkan sekarang</button>':'<button class=pri onclick="FP.retryNow()">&#8635; Coba simpan sekarang</button><button onclick="FP.connectNow()">Hubungkan ulang</button>')+'</div>'+(pm?tip:'');}
  if(!h){b.style.display='none';b.innerHTML='';return;}b.innerHTML=h;b.style.display='flex';};
(function(){var _i=FP.ind;FP.ind=function(){try{_i.apply(this,arguments);}catch(e){}try{FP.bar();}catch(e){}};})();
/* --- hubungkan (satu klik) --- */
FP.connectNow=async function(silent){var p=E('pjMenu');if(p)p.style.display='none';
  var h=FP.dir||FP.pendDir||await FP.mapGet(SA.pname)||await idbGet('fpDir');if(!h){if(!silent)FP.pick();return false;}
  var ok=await FP.perm(h,!silent);if(!ok){if(!silent){FP.toast('Izin folder belum diberikan. Klik <b>Hubungkan sekarang</b> lagi lalu pilih <b>Izinkan</b> (sebaiknya &ldquo;Izinkan pada setiap kunjungan&rdquo;).',true,9000);}if(!FP.dir)FP.pendDir=h;FP.ind();return false;}
  FP.permLost=false;FP.err='';FP._errShown=0;
  if(FP.dir){await FP.mapSet(SA.pname,FP.dir);FP.lockStart();FP.ind();FP.save(true,'hubungkan lagi');return true;}
  FP.dir=h;FP.pendDir=null;FP.ro=false;FP.conf=null;FP.newTarget=false;var R=await idbGet('fpRevP:'+SA.pname);FP.base=R&&R.rev||0;FP.lastHash='';FP.dataWritten='';
  await FP.mapSet(SA.pname,h);var M=await FP.meta();
  if(M&&M.format==='gcex-project'&&M.rev>FP.base){var mine=null;try{mine=FP.bodyHash();}catch(e){}var same=false;try{var t=await FP.readText(h,FP.MAINF),u=FP.unpack(t);same=!!mine&&FP.hash(JSON.stringify(u.body,encTA))===mine;}catch(e){}
    if(same){FP.base=M.rev;FP.lastHash=mine;FP.revSet(SA.pname);await FP.afterConnect(false);return true;}
    FP.conf=M;FP.lockStart();FP.ind();FP.menu();return true;}
  await FP.afterConnect(!M);FP.revSet(SA.pname);return true;};
FP.retryNow=async function(){FP.err='';FP._errShown=1;var ok=await FP.save(true,'coba lagi');FP._errShown=0;FP.ind();if(ok)FP.toast('&#10003; Tersimpan di folder <b>'+esc(FP.dir.name)+'</b> (rev '+FP.base+').',false,4000);};
FP.reconnectViewer=function(){return FP.connectNow();};
/* --- konflik: muat versi folder / pakai versi saya --- */
FP.confLoad=async function(direct){if(!direct&&!confirm('Muat versi terbaru dari folder? Versi Anda tetap diamankan di backup/KONFLIK_….'))return;
  try{var mine=FP.pack({format:'gcex-project',version:2,name:SA.pname,rev:FP.base,savedAt:new Date().toISOString(),savedBy:FP.user(),session:FP.sess,dev:FP.dev,conflictWith:FP.conf&&FP.conf.rev},JSON.stringify({work:FP.workObj(),dataHash:FP.dataHash,dataFile:FP.DATAF},encTA));
    await FP.write(await FP.sub(['backup']),'KONFLIK_'+FP.ts()+'_'+FP.slug(FP.user())+'.json',mine.text);}catch(e){}
  await idbPut('fpDir',FP.dir);await idbPut('fpAuto',1);FP.conf=null;FP._noWarn=true;location.reload();};
FP.confKeep=async function(direct){if(!direct&&!confirm('Timpa proyek di folder dengan versi Anda? Versi di folder diamankan dulu di backup.'))return;var M=FP.conf;
  try{var t=await FP.readText(FP.dir,FP.MAINF);if(t)await FP.write(await FP.sub(['backup']),'SEBELUM_TIMPA_'+FP.ts()+'_r'+((M&&M.rev)||0)+'_'+FP.slug((M&&M.savedBy)||'lain')+'.json',t);}catch(e){}
  FP.conf=null;FP.base=Math.max(FP.base,(M&&M.rev)||0);if(!FP.hb)FP.lockStart();var ok=await FP.save(true,'pakai versi saya');FP.revSet(SA.pname);
  FP.toast(ok?'&#10003; Versi Anda disimpan ke folder sebagai rev '+FP.base+'. Versi '+esc((M&&M.savedBy)||'lain')+' diamankan di backup/SEBELUM_TIMPA_….':'Gagal menyimpan: '+esc(FP.err||''),!ok,8000);FP.menu();FP.ind();};
/* --- simpan: catat rev per proyek; gagal -> dicoba lagi oleh pemeriksa 15 detik --- */
(function(){var _s=FP.save;FP.save=async function(force){if(!force&&FP.dir&&!FP.err&&!FP.dirtyLocal&&FP.lastHash&&!FP.conf)return true;/* tidak ada perubahan: lewati serialisasi proyek */var s0=FP.dseq||0;var ok=await _s.apply(this,arguments);if(ok){FP.revSet(SA.pname);if((FP.dseq||0)===s0)FP.dirtyLocal=false;}FP.ind();return ok;};
  var _a=FP.afterConnect;FP.afterConnect=async function(){await FP.mapSet(SA.pname,FP.dir);FP.pendDir=null;var r=await _a.apply(this,arguments);FP.revSet(SA.pname);FP.ind();return r;};
  var _d=FP.detach;FP.detach=async function(){var nm=SA.pname,had=!!FP.dir;await _d.apply(this,arguments);if(had&&!FP.dir&&nm){try{await idbDel('fpDirP:'+nm);await idbDel('fpRevP:'+nm);}catch(e){}FP.pendDir=null;FP.ind();}};
  var _u=FP.use;FP.use=async function(){FP._noWarn=true;try{return await _u.apply(this,arguments);}finally{setTimeout(function(){FP._noWarn=false;},4000);}};
  var _r=SA.reopen;SA.reopen=async function(){try{if(FP.dir&&!FP.ro&&!FP.conf)await FP.save(false,'tutup');}catch(e){}FP._noWarn=true;return _r.apply(this,arguments);};})();
/* --- buka proyek dari daftar: langsung dari foldernya --- */
(function(){var _o=SA.openProj;SA.openProj=async function(nm){var h=null;try{h=await FP.mapGet(nm);}catch(e){}
    if(h&&FP.ok()){var ok=await FP.perm(h,true);if(ok){var t=await FP.readText(h,FP.MAINF);if(t){await idbPut('fpDir',h);FP.askUser();msg('Memuat proyek <b>'+esc(nm)+'</b> dari folder <b>'+esc(h.name)+'</b>&hellip;');return FP.openFolder(h,t);}}
      FP.pendDir=h;FP.pendFor=nm;}
    return _o.apply(this,arguments);};
  var _l=SA.listProj;SA.listProj=async function(){await _l.apply(this,arguments);try{var box=E('pjList');if(!box)return;var rows=box.querySelectorAll('.fi.pj');for(var i=0;i<rows.length;i++){var b=rows[i].querySelector('.nm b'),nm=b?b.textContent:'';var h=await FP.mapGet(nm);if(h){var s=document.createElement('span');s.className='fpbadge';s.title='Proyek ini tersimpan di folder; tombol Buka memuat versi terbaru dari folder';s.innerHTML='&#128193; '+esc(h.name);b.parentNode.insertBefore(s,b.nextSibling);}}}catch(e){}};
  setTimeout(function(){try{if(E('pjList'))SA.listProj();}catch(e){}},300);
  var _b=SA.boot;SA.boot=function(D,W){var r=_b.apply(this,arguments);setTimeout(async function(){try{if(FP.dir){await FP.mapSet(SA.pname,FP.dir);FP.ind();return;}var h=FP.pendFor===SA.pname&&FP.pendDir?FP.pendDir:await FP.mapGet(SA.pname);if(!h){FP.ind();return;}FP.pendDir=h;
      if(await FP.perm(h,false))await FP.connectNow(true);FP.ind();}catch(e){console.warn(e);}},400);return r;};
  var _dy=SA.dirty;SA.dirty=function(){FP.dirtyLocal=true;FP.dseq=(FP.dseq||0)+1;return _dy.apply(this,arguments);};})();
/* --- izin folder dicek tiap 15 detik; simpan ulang otomatis bila ada perubahan / gagal --- */
setInterval(async function(){try{if(FP.dir){var ok=await FP.perm(FP.dir,false);if(!ok){if(!FP.permLost){FP.permLost=true;FP.err='izin folder belum ada / dicabut';FP.ind();}return;}
      if(FP.permLost){FP.permLost=false;FP.err='';}
      if(!FP.ro&&!FP.conf&&!FP.busy){var need=!!FP.err;if(!need&&FP.dirtyLocal&&FP.lastHash){try{need=FP.bodyHash()!==FP.lastHash;if(!need)FP.dirtyLocal=false;}catch(e){}}if(need)await FP.save(false,FP.err?'coba lagi otomatis':'otomatis');}
      FP.ind();}
    else if(FP.pendDir&&await FP.perm(FP.pendDir,false)){await FP.connectNow(true);}}catch(e){}},FP.PERMMS);
/* --- peringatan sebelum menutup bila ada perubahan yang belum masuk folder --- */
FP.unsaved=function(){if(FP._noWarn||(window.DM&&DM.on))return false;try{if(FP.dir&&!FP.ro){if(FP.busy||FP.pend||FP.err||FP.conf)return true;if(FP.dirtyLocal&&FP.lastHash&&FP.bodyHash()!==FP.lastHash)return true;return false;}
  if(!FP.dir&&FP.pendDir&&FP.dirtyLocal)return true;}catch(e){}return false;};
/* GC-Ex Desktop: dipanggil aplikasi saat jendela akan ditutup -> simpan dulu (komputer + folder proyek), lepas kunci */
window.gcexFlush=async function(){var r={ok:true,folder:!!FP.dir,err:''};
  try{if(window.SA&&SA.saveWork)await SA.saveWork();}catch(e){r.err='penyimpanan komputer: '+(e&&e.message||e);}
  try{if(FP.dir&&!FP.ro){if(FP.busy){for(var i=0;i<40&&FP.busy;i++)await new Promise(function(z){setTimeout(z,150);});}
      if(FP.unsaved()){if(FP.toast)FP.toast('Menyimpan ke folder proyek sebelum menutup&hellip;',false,4000);await FP.save(true,'saat menutup');}
      if(FP.unsaved()){r.ok=false;r.err=FP.err||'perubahan belum masuk folder proyek';}
      else{try{await FP.lockRelease();}catch(e){}}}}
  catch(e){r.ok=false;r.err=String(e&&e.message||e);}
  if(r.ok)FP._noWarn=true;return r;};
window.addEventListener('beforeunload',function(e){if(FP.unsaved()){e.preventDefault();e.returnValue='Ada perubahan yang belum tersimpan di folder proyek.';return e.returnValue;}});
/* --- petunjuk izin di kartu folder awal --- */
(function(){var _st=FP.startUI;FP.startUI=async function(){await _st.apply(this,arguments);var s=E('fpStat');if(s&&!E('fpTip')){var d=document.createElement('div');d.id='fpTip';d.className='hint2';d.innerHTML='Saat browser meminta izin folder, pilih <b>&ldquo;Izinkan pada setiap kunjungan&rdquo;</b> bila tersedia. Setiap proyek mengingat foldernya: tombol <b>Buka</b> di daftar proyek langsung memuat versi terbaru dari folder.';s.parentNode.insertBefore(d,s.nextSibling);}};})();

/* ================= pemulihan tampilan 3D (WebGL hilang / laptop bangun dari sleep) ================= */
(function(){var last=Date.now(),busy=false;FP.glRec=0;
  function lost(){var gd=document.getElementById('plotDiv');if(!gd)return false;var C=gd.querySelectorAll('canvas');for(var i=0;i<C.length;i++){var g=null;try{g=C[i].getContext('webgl2')||C[i].getContext('webgl');}catch(e){}if(g&&g.isContextLost&&g.isContextLost())return true;}return false;}
  function rebuild(why){if(busy||!window.Plotly||!document.getElementById('plotDiv')||!window.SA||!SA.pname)return;busy=true;var gd=document.getElementById('plotDiv'),cam=null;try{if(!VIEW2D)cam=JSON.parse(JSON.stringify(gd._fullLayout.scene.camera));}catch(e){}
    setTimeout(function(){try{Plotly.purge('plotDiv');}catch(e){}try{updatePlot();if(cam&&!VIEW2D)Plotly.relayout('plotDiv',{'scene.camera':cam});}catch(e){console.warn(e);}FP.glRec++;busy=false;
      try{FP.toast('&#8635; Tampilan 3D dipulihkan otomatis ('+why+').',false,3500);}catch(e){}},why==='grafis hilang'?400:900);}
  window.gcexGLRebuild=rebuild;
  document.addEventListener('webglcontextlost',function(e){var t=e.target;if(t&&t.closest&&t.closest('#plotDiv')){FP._glLostAt=Date.now();try{e.preventDefault();}catch(x){}rebuild('grafis hilang');}},true);
  var _oe=window.onerror;window.onerror=function(m,src,l){if((Date.now()-(FP._glLostAt||0))<15000&&/\bgl\b|webgl|context|scene/i.test(String(m))){console.warn('GC-Ex: galat grafis saat pemulihan diabaikan:',m);return true;}return _oe?_oe.apply(this,arguments):false;};
  window.addEventListener('error',function(ev){if((Date.now()-(FP._glLostAt||0))<15000&&/\bgl\b|webgl|context|scene/i.test(String(ev.message))){ev.preventDefault();ev.stopImmediatePropagation();}},true);
  setInterval(function(){var n=Date.now(),gap=n-last;last=n;if(document.hidden)return;if(gap>60000)rebuild('bangun dari sleep');else if(gap>4000&&lost())rebuild('grafis hilang');},5000);
  document.addEventListener('visibilitychange',function(){if(!document.hidden&&lost())rebuild('grafis hilang');});})();
