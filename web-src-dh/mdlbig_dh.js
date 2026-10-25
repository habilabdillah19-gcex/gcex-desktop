/* ================= GC-Ex Desktop (Drillhole): block model .mdl besar lewat backend Python =================
   Drillhole menyaring blok menurut TITIK TENGAH di dalam kotak E/N/RL (dialog "Block model besar") dan semua jalur
   muat (panel awal, Import BM, buka ulang dari folder proyek) memanggil SA.mdlRun(f,H,st,...).
   Untuk file >= SA.MDL_BIG_MB di GC-Ex Desktop: backend membaca file sekali ke cache disk, lalu hanya mengirim blok
   yang lolos filter; pembaca Drillhole sendiri yang memprosesnya (hasil identik). Gagal -> pembacaan langsung. */
(function(){var _run=SA.mdlRun;if(!_run||SA._mdlRunBig)return;SA._mdlRunBig=1;
  var nz=function(v){return v==null||v===''||!isFinite(+v)?null:+v;};
  SA.mdlRun=async function(f,H,st,topo,pit,say,stop){var D=window.gcexDesktop,self=this,args=arguments;
    if(!D||!D.apiBin||!f||f.size<SA.MDL_BIG_MB*1048576)return _run.apply(self,args);
    var path=await SA.mdlPathOf(f);if(!path)return _run.apply(self,args);
    st=st||{};say=say||function(){};var t0=Date.now(),I,s;
    try{for(;;){if(stop&&stop()){try{await D.api('/mdl/cancel',{path:path});}catch(e){}throw new Error('Pembacaan block model dibatalkan.');}
        s=await D.api('/mdl/open',{path:path});if(s.state==='ready'){I=s.info;break;}if(s.state==='error')throw new Error(s.error||'backend gagal membaca .mdl');
        var pc=Math.round((s.pct||0)*0.9);say('Membaca '+f.name+' sekali ke cache disk (backend): <b>'+pc+'%</b> &middot; '+(s.n||0).toLocaleString('id-ID')+' blok'+(s.mbps?' &middot; '+s.mbps+' MB/s':''),pc);
        await new Promise(function(z){setTimeout(z,600);});}
      var bb=[nz(st.x0),nz(st.x1),nz(st.y0),nz(st.y1)],body={path:path,z_min:nz(st.lo),z_max:nz(st.hi),bbox:bb.some(function(v){return v!==null;})?bb:null,center:true};
      say('Mengambil blok di dalam filter dari cache&hellip;',90);
      var r=await D.apiBin('/mdl/subset',body),nSub=+(r.headers['x-gcex-n']||0);
      if(!nSub)throw Object.assign(new Error('Tidak ada blok di dalam filter (area / elevasi). Model berisi '+I.n.toLocaleString('id-ID')+' blok, RL '+(+I.zmin).toFixed(2)+'–'+(+I.zmax).toFixed(2)+'.'),{noFallback:true});
      var sf=new File([r.buf],f.name,{type:'application/octet-stream',lastModified:f.lastModified}),H2=await SA.mdlHead(sf);
      /* pilihan Float32 mengikuti ukuran file ASLI (bukan potongan) supaya hasil sama persis */
      var st2=Object.assign({},st,{f32:st.f32!==false&&(st.f32===true||(H&&H.estN>2e6))});
      var m=await _run.call(self,sf,H2,st2,topo,pit,function(h,p){say(h,90+Math.round((p||0)*0.1));},stop);
      var M=m.mdl||(m.mdl={});M.file=f.name;M.size=f.size;M.via='backend';M.path=path;M.ms=Date.now()-t0;
      var allA=(M.st||[]).map(function(a){return a.name;});if(M.filt){M.filt.nTot=I.n;if(!(M.filt.st.keep||[]).length)M.filt.st.keep=allA;}else if(m.n<I.n)M.filt={nTot:I.n,n:m.n,st:{x0:bb[0],x1:bb[1],y0:bb[2],y1:bb[3],lo:body.z_min,hi:body.z_max,keep:st.keep&&st.keep.length?st.keep:allA}};
      (M.notes||(M.notes=[])).push('Dibaca lewat backend GC-Ex Desktop (cache disk): '+nSub.toLocaleString('id-ID')+' dari '+I.n.toLocaleString('id-ID')+' blok dikirim ke tampilan.');
      SA.mdlPathSave(f,path);return m;}
    catch(e){if(e.noFallback||/dibatalkan/.test(e.message)||(stop&&stop()))throw e;console.warn('[GC-Ex] backend .mdl gagal, baca langsung:',e);return _run.apply(self,args);}};})();
