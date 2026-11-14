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
/* batas blok per pemuatan supaya RAM / VRAM 4 GB tidak penuh dan layar tidak tersendat (dari memori komputer;
   bisa diubah: localStorage gcexMdlMaxBlk). Model > batas: dimuat rentang RL teratas yang muat, sisanya lewat filter RL. */
SA.mdlMaxBlk=function(){var v=0;try{v=parseInt(localStorage.getItem('gcexMdlMaxBlk'),10);}catch(e){}if(v>=100000)return v;
  var dm=+navigator.deviceMemory||8;return dm<=4?1500000:dm<8?2500000:3500000;};
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
  var body={path:path,z_min:isFinite(opt&&opt.zMin)?opt.zMin:null,z_max:isFinite(opt&&opt.zMax)?opt.zMax:null,bbox:bb,max_n:SA.mdlMaxBlk()};
  if(prog)prog(90,0,I.n);var r=await D.apiBin('/mdl/subset',body),nSub=+(r.headers['x-gcex-n']||0);
  if(!nSub)throw Object.assign(new Error('Tidak ada blok yang lolos filter (RL '+(body.z_min==null?'min':body.z_min)+'–'+(body.z_max==null?'max':body.z_max)+(bb?', area pit/topografi':'')+'). Model berisi '+I.n.toLocaleString()+' blok, RL '+(+I.zmin).toFixed(2)+'–'+(+I.zmax).toFixed(2)+'.'),{noFallback:true});
  var H=r.headers,cap=H['x-gcex-capped']==='1',zc=parseFloat(H['x-gcex-zmin']),nReq=+(H['x-gcex-nreq']||0);
  var sf=new File([r.buf],f.name,{type:'application/octet-stream',lastModified:f.lastModified});r=null;
  var m=await orig(sf,function(pc,nk,nr){if(prog)prog(90+Math.round(pc*0.1),nk,I.n);},opt);
  var M=m.mdl;M.drop.rl+=I.n-nSub;M.nRead=I.n;M.size=f.size;M.file=f.name;M.ms=Date.now()-t0;M.via='backend';M.path=path;M.cacheBuild=I.build_s;
  M.flt=(M.flt?M.flt+' · ':'')+'dibaca lewat backend (cache disk, '+nSub.toLocaleString()+' blok dikirim)';
  if(cap){var zt=body.z_max==null?'atas model':body.z_max;M.capped={zMin:zc,zMax:body.z_max,nReq:nReq,max:body.max_n};
    var w='Model sangat besar: rentang RL diminta berisi ±'+nReq.toLocaleString()+' blok, melebihi batas lancar komputer ini ('+body.max_n.toLocaleString()+' blok). '+
      'Yang dimuat hanya RL '+zc+' – '+zt+' (bagian teratas rentang). '+(function(){var a=+zc,b=body.z_max==null?+I.zmax:+body.z_max,t=b-a;if(!(t>0)||body.z_min!=null&&a<=body.z_min)return '';var lo=Math.max(body.z_min==null?+I.zmin:+body.z_min,a-t);
        return 'Rentang berikutnya: isi RL bawah '+(Math.round(lo*100)/100)+' dan RL atas '+zc+'. ';})()+'Lebih ringkas: nyalakan "Hanya di dalam desain pit" / "Hanya di bawah topografi" (dibaca langsung, tanpa batas rentang).';
    m.warn=(m.warn?m.warn+' ':'')+w;try{setTimeout(function(){alert(w);},300);}catch(e){}}
  SA.mdlPathSave(f,path);return m;};
(function(){var _r=SA.readMDL;if(!_r||SA._mdlBigOn)return;SA._mdlBigOn=1;
  SA.readMDL=async function(f,prog,opt){var D=window.gcexDesktop;if(!D||!D.apiBin||!f||f.size<SA.MDL_BIG_MB*1048576)return _r.apply(this,arguments);
    /* BM 0.24.81 (pemilik 14 Nov 2026, .mdl Zona 4 6,48 GB / 88 juta blok): dengan filter desain pit / topografi file dibaca
       LANGSUNG -- filter diterapkan sambil membaca (6,48 GB ±30 detik, tanpa cache disk 10 GB). Lewat backend, batas jumlah
       blok dulu dihitung dari SELURUH kotak model sebelum filter pit/topografi, sehingga yang tersisa hanya potongan RL
       teratas (47 blok di RL 349; 349 blok untuk RL 210-270). */
    if(opt&&(opt.pit||opt.topo)){var mx=SA.mdlMaxBlk(),lebih='',m0=await _r.call(this,f,prog,Object.assign({},opt,{maxN:mx})),pth='';try{pth=await SA.mdlPathOf(f);}catch(x){}
      /* 0.24.83 (pemilik 14 Nov 2026: 39.479.029 blok lolos filter pit -> aplikasi error kehabisan memori). Blok yang lolos
         filter dibatasi mx; bila lebih, jumlah per RL dari bacaan pertama dipakai memilih bagian TERATAS yang muat, lalu
         file dibaca sekali lagi hanya untuk rentang itu. */
      if(m0.mdl.over){var HB=m0.mdl.hist,zB=m0.mdl.origin[2],tot=m0.n+m0.mdl.over,ak=0,b=HB.length-1;for(;b>=0;b--){if(ak+HB[b]>mx&&ak>0)break;ak+=HB[b];if(ak>mx)break;}
        var zCut=zB+Math.max(0,b+(ak>mx?0:1))*0.25,zTop=isFinite(opt.zMax)?opt.zMax:zB+m0.mdl.extent[2];m0=null;
        m0=await _r.call(this,f,prog,Object.assign({},opt,{zMin:zCut,maxN:Math.min(Math.max(ak,mx),mx*3)}));
        lebih='Model sangat besar: '+tot.toLocaleString()+' blok lolos filter, melebihi batas lancar komputer ini ('+mx.toLocaleString()+' blok). Yang dimuat hanya bagian teratas, RL '+zCut+' \u2013 '+zTop+' ('+m0.n.toLocaleString()+' blok). Rentang berikutnya: isi RL atas '+zCut+' (RL bawah lebih rendah). '+(opt.topo?'':' Nyalakan juga "Hanya di bawah topografi asbuilt" supaya blok udara di atas topografi tidak ikut dihitung.')+' Angka seluruh model: Ringkasan seluruh model per RL.';}
      try{var M0=m0.mdl;if(lebih)m0.warn=(m0.warn?m0.warn+' ':'')+lebih;M0.flt=(M0.flt?M0.flt+' · ':'')+'dibaca langsung (filter pit / topografi sambil membaca)';
        /* 0.24.82: path file disimpan supaya "Ringkasan seluruh model per RL" tetap dihitung backend atas SELURUH file */
        if(pth){M0.path=pth;M0.bigPath=1;SA.mdlPathSave(f,pth);}
        }catch(x){}return m0;}
    var path=await SA.mdlPathOf(f);if(!path)return _r.apply(this,arguments);
    try{return await SA.mdlBig(f,path,prog,opt||{},_r);}
    catch(e){if(e.noFallback||/dibatalkan/.test(e.message)||(opt&&opt.cancel&&opt.cancel()))throw e;console.warn('[GC-Ex] backend .mdl gagal, baca langsung:',e);
      if(prog)prog(0,0,0);var m=await _r.apply(this,arguments);try{m.mdl.notes=(m.mdl.notes||[]).concat(['Backend tidak dipakai: '+e.message]);}catch(x){}return m;}};})();
/* ================= BM 0.24.82: folder cache .mdl besar bisa dipindah (pemilik 14 Nov 2026) =================
   Cache Zona 4 butuh ±10,7 GB; C: hanya 7,4 GB bebas. Kotak ini tampil di layar Import block model (file besar) dan di
   Ringkasan seluruh model per RL. Hapus cache tetap satu pintu: menu Bantuan › Hapus cache block model besar. */
SA.mdlGB=function(b){return b==null?'?':(b/1073741824).toFixed(1).replace('.',',')+' GB';};
SA.mdlCacheHtml=function(){if(!(window.gcexDesktop&&gcexDesktop.api))return '';setTimeout(SA.mdlCacheIsi,30);return '<div id="mdlCache" class="hint" style="margin-top:6px">Memeriksa folder cache…</div>';};
SA.mdlCacheIsi=async function(){var el=document.getElementById('mdlCache');if(!el)return;var j;try{j=await gcexDesktop.api('/mdl/cache');}catch(e){el.textContent='Folder cache tidak terbaca: '+e.message;return;}
  var e=function(t){return String(t).replace(/[&<>"]/g,function(c){return{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c];});};
  el.innerHTML='<b>Cache block model besar</b> (dipakai bila import tanpa filter area dan untuk Ringkasan seluruh model per RL): <code>'+e(j.root)+'</code> &middot; terpakai '+SA.mdlGB(j.used)+' ('+(j.items||[]).length+' model) &middot; ruang bebas '+SA.mdlGB(j.free)+
    '<div style="display:flex;gap:6px;flex-wrap:wrap;margin-top:5px"><button type="button" onclick="SA.mdlCacheGanti()">Ganti folder cache&hellip;</button>'+(j.custom?'<button type="button" onclick="SA.mdlCacheGanti(true)">Kembalikan ke folder bawaan</button>':'')+
    '</div><div style="margin-top:3px">Hapus cache: menu <b>Bantuan &rsaquo; Hapus cache block model besar</b>.</div>';};
SA.mdlCacheGanti=async function(bawaan){var D=window.gcexDesktop;if(!D||!D.api)return;var j0;try{j0=await D.api('/mdl/cache');}catch(e){alert(e.message);return;}
  var p=null;if(!bawaan){p=D.openFolder?await D.openFolder({title:'Pilih folder cache block model besar (mis. di drive D:)'}):prompt('Folder cache block model besar:','D:\\GC-Ex-cache');if(!p)return;}
  var hl=j0.used>0&&confirm('Hapus cache di folder lama ('+SA.mdlGB(j0.used)+')?\n\nYa = ruang di drive lama dikosongkan; cache dibuat ulang di folder baru saat dibutuhkan.\nBatal = cache lama dibiarkan.');
  try{var r=await D.api('/mdl/cache/root',{path:p,hapus_lama:!!hl});alert('Folder cache sekarang:\n'+r.root+'\nRuang bebas: '+SA.mdlGB(r.free)+(r.removed_old?'\n'+r.removed_old+' cache lama dihapus.':''));}catch(e){alert('Folder cache tidak diganti: '+e.message);}
  SA.mdlCacheIsi();};
