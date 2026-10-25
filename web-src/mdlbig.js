/* ================= GC-Ex Desktop: prompt(), alert(), confirm(), drag-drop =================
   Electron tidak menyediakan prompt() (melempar galat "prompt() is and will not be supported").
   Di GC-Ex Desktop, prompt() diarahkan ke jendela isian kecil milik aplikasi; di browser tidak berubah. */
(function(){var D=window.gcexDesktop;if(!D)return;
  if(typeof D.prompt==='function'){try{window.prompt=function(m,d){var r=D.prompt(m==null?'':String(m),d==null?'':String(d));return r==null?null:String(r);};}catch(e){}}
  /* alert/confirm lewat kotak pesan Windows asli (menghindari kolom isian 'macet' setelah dialog bawaan Electron) */
  if(typeof D.alert==='function'){try{window.alert=function(m){D.alert(m==null?'':String(m));};}catch(e){}}
  if(typeof D.confirm==='function'){try{window.confirm=function(m){return D.confirm(m==null?'':String(m))===true;};}catch(e){}}
  /* file yang dijatuhkan di luar kotak unggah tidak boleh membuka file itu menggantikan GC-Ex */
  var isF=function(e){try{return Array.prototype.indexOf.call((e.dataTransfer&&e.dataTransfer.types)||[],'Files')>=0;}catch(x){return false;}};
  document.addEventListener('dragover',function(e){if(isF(e))e.preventDefault();});
  document.addEventListener('drop',function(e){if(isF(e)&&!e.defaultPrevented)e.preventDefault();});})();
/* ================= GC-Ex Desktop: block model .mdl besar lewat backend Python (tahap 3) =================
   File .mdl >= SA.MDL_BIG_MB dibaca SEKALI oleh backend menjadi cache kolom di disk; setiap kali GC-Ex butuh
   rentang RL / area, backend mengirim potongan .mdl mini yang sah, lalu potongan itu dibaca oleh pembaca .mdl
   GC-Ex yang sama (filter pit/topografi, atribut kalkulasi IIF, kategori, ekspor .mdl tetap identik).
   Di browser biasa / bila backend gagal: kembali ke pembacaan langsung seperti sebelumnya. */
SA.MDL_BIG_MB=150;
SA.mdlPathMap=function(){try{return JSON.parse(localStorage.getItem('gcexMdlPaths')||'{}');}catch(e){return{};}};
SA.mdlPathSave=function(f,p){try{var m=SA.mdlPathMap();m[f.name+'|'+f.size]=p;localStorage.setItem('gcexMdlPaths',JSON.stringify(m));}catch(e){}};
SA.mdlPathOf=async function(f){var D=window.gcexDesktop;if(!D||!D.pathOf||!D.api)return '';var p=D.pathOf(f);if(p)return p;
  var h=SA.mdlPathMap()[f.name+'|'+f.size];if(!h)return '';try{var s=await D.api('/mdl/stat',{path:h});return s.exists&&s.size===f.size?h:'';}catch(e){return '';}};
SA.mdlBig=async function(f,path,prog,opt,orig){var D=window.gcexDesktop,t0=Date.now(),cancel=opt&&opt.cancel,st;
  for(;;){if(cancel&&cancel()){try{await D.api('/mdl/cancel',{path:path});}catch(e){}throw new Error('Pembacaan dibatalkan.');}
    st=await D.api('/mdl/open',{path:path});if(st.state==='ready')break;if(st.state==='error')throw new Error(st.error||'Backend gagal membaca .mdl');
    if(prog)prog(Math.max(0,Math.min(89,Math.round((st.pct||0)*0.9))),0,st.n||0);await new Promise(function(r){setTimeout(r,600);});}
  var I=st.info,bb=null,G=[opt&&opt.pit,opt&&opt.topo].filter(Boolean);
  G.forEach(function(g){var b=[g.x0,g.x0+g.nx*g.c,g.y0,g.y0+g.ny*g.c];bb=bb?[Math.max(bb[0],b[0]),Math.min(bb[1],b[1]),Math.max(bb[2],b[2]),Math.min(bb[3],b[3])]:b;});
  var body={path:path,z_min:isFinite(opt&&opt.zMin)?opt.zMin:null,z_max:isFinite(opt&&opt.zMax)?opt.zMax:null,bbox:bb};
  if(prog)prog(90,0,I.n);var r=await D.apiBin('/mdl/subset',body),nSub=+(r.headers['x-gcex-n']||0);
  if(!nSub)throw Object.assign(new Error('Tidak ada blok yang lolos filter (RL '+(body.z_min==null?'min':body.z_min)+'–'+(body.z_max==null?'max':body.z_max)+(bb?', area pit/topografi':'')+'). Model berisi '+I.n.toLocaleString()+' blok, RL '+(+I.zmin).toFixed(2)+'–'+(+I.zmax).toFixed(2)+'.'),{noFallback:true});
  var sf=new File([r.buf],f.name,{type:'application/octet-stream',lastModified:f.lastModified});
  var m=await orig(sf,function(pc,nk,nr){if(prog)prog(90+Math.round(pc*0.1),nk,I.n);},opt);
  var M=m.mdl;M.drop.rl+=I.n-nSub;M.nRead=I.n;M.size=f.size;M.file=f.name;M.ms=Date.now()-t0;M.via='backend';M.path=path;M.cacheBuild=I.build_s;
  M.flt=(M.flt?M.flt+' · ':'')+'dibaca lewat backend (cache disk, '+nSub.toLocaleString()+' blok dikirim)';SA.mdlPathSave(f,path);return m;};
(function(){var _r=SA.readMDL;if(!_r||SA._mdlBigOn)return;SA._mdlBigOn=1;
  SA.readMDL=async function(f,prog,opt){var D=window.gcexDesktop;if(!D||!D.apiBin||!f||f.size<SA.MDL_BIG_MB*1048576)return _r.apply(this,arguments);
    var path=await SA.mdlPathOf(f);if(!path)return _r.apply(this,arguments);
    try{return await SA.mdlBig(f,path,prog,opt||{},_r);}
    catch(e){if(e.noFallback||/dibatalkan/.test(e.message)||(opt&&opt.cancel&&opt.cancel()))throw e;console.warn('[GC-Ex] backend .mdl gagal, baca langsung:',e);
      if(prog)prog(0,0,0);var m=await _r.apply(this,arguments);try{m.mdl.notes=(m.mdl.notes||[]).concat(['Backend tidak dipakai: '+e.message]);}catch(x){}return m;}};})();
