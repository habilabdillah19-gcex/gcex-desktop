/* ================= GC-Ex Drillhole: isi PROJECT TREE (urut alur kerja) =================
   1 Proyek · 2 Data Spasial · 3 Database Bor · 4 Peta (Mapping) · 5 Struktur Geologi · 6 Geomodeller Vein System Deposit · 6b Geomodeller Stratified-Laterite Deposit ·
   (Sayatan & Penampang dipindah ke menu Sayatan di bilah atas) ·
   7 Block Model · 8 Model Estimation · 9 Validasi BM · 10 Reporting BM · 11 Geostatistik · 12 Layout & Ekspor · Pengaturan tampilan.
   Juga: hapus tabel / hole dari database bor (PTD.drop) dengan jalur simpan yang sama seperti upsert (bisa dibatalkan). */
(function(){if(!window.PT||PT.def)return;
  var $=function(i){return document.getElementById(i);},U=PT.u,N=U.num,ok=function(f,d){try{var r=f();return r===undefined?d:r;}catch(e){return d;}};
  var A=function(fn){var a=[].slice.call(arguments,1);return function(){if(typeof window[fn]==='function')return window[fn].apply(window,a);};};
  var tab=function(t,sub){return function(){uiTab(t);if(sub)setTimeout(function(){PT.goSub(t,sub);},30);};};
  /* ---------- hapus tabel / hole (disimpan seperti upsert; Batalkan lewat menu Database Bor) ---------- */
  var PTD=window.PTD={};
  PTD.apply=async function(label,mut){if(!window.UP||!UP.can())return;var H=window._fpH,name=SA.pname,prev=null;
    try{prev=JSON.parse(JSON.stringify(SA.D,H.encTA),H.decTA);
      if(window.FP&&FP.dir){var o0=await FP.flush('sebelum '+label);if(!o0)throw new Error('gagal menyimpan backup: '+(FP.err||''));}
      mut(SA.D);SA.Dver=(SA.Dver||0)+1;
      await H.idbPut('upsPrev:'+name,{date:new Date().toISOString(),data:prev});
      await H.idbPut('proj:'+name,{name:name,date:new Date().toISOString(),data:SA.D});await SA.saveWork();
      if(window.FP&&FP.dir){var o1=await FP.flush(label);if(!o1)throw new Error('gagal menyimpan ke folder proyek: '+(FP.err||''));await H.idbPut('fpAuto',1);}else await H.idbPut('dhAutoOpen',name);
      try{sessionStorage.setItem('gcexUps',JSON.stringify({t:label+'. Bisa dibatalkan: klik kanan Database Bor › Batalkan perubahan terakhir.',at:new Date().toISOString()}));}catch(e){}
      if(window.FP)FP._reloading=1;location.reload();}
    catch(er){console.error(er);try{if(prev){Object.keys(SA.D).forEach(function(k){delete SA.D[k];});Object.assign(SA.D,prev);SA.Dver=(SA.Dver||0)+1;await H.idbPut('proj:'+SA.pname,{name:SA.pname,date:new Date().toISOString(),data:SA.D});}}catch(e2){}
      alert('Gagal: '+er.message+'\nData proyek tidak diubah.');}};
  var TB={survey:['surveys','tabel survey (hole dianggap lurus sesuai collar)'],assay:['assays','tabel assay (semua unsur)'],geo:['geoRows','tabel geologi']};
  PTD.drop=function(kind,ids){var D=SA.D;if(!D)return;
    if(kind==='holes'){var S={};ids.forEach(function(h){S[h]=1;});var nc=(D.collars||[]).filter(function(c){return S[c[0]];}).length;if(!nc){alert('HoleID tidak ditemukan.');return;}
      if(!confirm('Hapus '+nc+' hole ('+ids.slice(0,8).join(', ')+(ids.length>8?', …':'')+') beserta survey, assay & geologinya dari proyek "'+SA.pname+'"?\n\nFolder proyek mendapat backup dulu; bisa dibatalkan.'))return;
      return PTD.apply('Hapus '+nc+' hole',function(D){['collars','surveys','assays','geoRows'].forEach(function(k){if(D[k])D[k]=D[k].filter(function(r){return !S[r[0]];});});});}
    if(kind==='all'){if(!confirm('Hapus SELURUH database bor (collar, survey, assay, geologi: '+(D.collars||[]).length+' hole) dari proyek "'+SA.pname+'"?\n\nData spasial, block model & pekerjaan lain tetap. Bisa dibatalkan.'))return;
      return PTD.apply('Hapus seluruh database bor',function(D){D.collars=[];D.surveys=[];D.assays=[];D.elements=[];D.asCat=[];D.geoRows=[];D.geoCat=[];});}
    var t=TB[kind];if(!t)return;var n=(D[t[0]]||[]).length;if(!n){alert('Tabel ini sudah kosong.');return;}
    if(!confirm('Hapus '+t[1]+': '+N(n)+' baris, dari proyek "'+SA.pname+'"?\n\nUntuk mengganti isinya cukup pakai Tambah / perbarui (upsert). Bisa dibatalkan.'))return;
    return PTD.apply('Hapus '+t[1].replace(/ \(.*/,''),function(D){D[t[0]]=[];if(kind==='assay'){D.elements=[];D.asCat=[];}if(kind==='geo')D.geoCat=[];});};
  var ups=function(){if(window.UP)UP.open();},undoM={t:'Batalkan perubahan database terakhir',fn:function(){if(window.UP)UP.undo();}};
  /* ---------- tampilkan sebagai (topografi / pit) ---------- */
  var topoAs=function(){var s=U.cb('ovTopoS'),l=U.cb('ovTopoL');return s&&l?'both':s?'surf':l?'line':'';};
  var setTopo=function(m){if(m)try{localStorage.setItem('gcex_pt_topo',m);}catch(e){}var s=m==='surf'||m==='both',l=m==='line'||m==='both',S=$('ovTopoS'),L=$('ovTopoL');if(S)S.checked=s;if(L)L.checked=l;updatePlot();};
  var topoPref=function(){var m='surf';try{m=localStorage.getItem('gcex_pt_topo')||'surf';}catch(e){}return m;};
  var asMenu=function(cur,set){return[{h:'Tampilkan sebagai'},{t:'Surface (permukaan)',on:cur==='surf',fn:function(){set('surf');}},{t:'Garis (kontur / crest-toe)',on:cur==='line',fn:function(){set('line');}},{t:'Surface + garis',on:cur==='both',fn:function(){set('both');}}];};
  /* ---------- versi data spasial ---------- */
  var SPN={topo:'topografi',pit:'desain pit',ortho:'orthofoto'},ACC={topo:'.dtm,.str,.dxf,.csv,.txt,.xyz,.asc',pit:'.dtm,.str,.dxf,.csv,.txt,.xyz',ortho:'.tif,.tiff,.jpg,.jpeg,.png,.tfw,.jgw,.pgw,.wld,.tifw,.jpgw,.pngw'};
  var addV=function(role){return{t:'Tambah versi '+SPN[role]+'…',fn:function(){PT.pick(ACC[role],true,function(i){spAdd(role,i);});}};};
  function versions(role){var L=ok(function(){return spL(role);},[]),act=ok(function(){return spAct(role);},null);
    return L.map(function(v){var on=v===act;return{id:'sp.'+role+'.'+v.id,t:v.name||'(tanpa nama)',ic:'ver',mark:on?'aktif':'',b:ok(function(){return spCount(role,v);},''),
      hint:(v.src||'')+(v.note?' · '+v.note:'')+(v.date?' · '+new Date(v.date).toLocaleDateString('id-ID'):''),tab:'SP',
      chk:on||role==='ortho'?undefined:!!v.show,onChk:function(x){spSet(role,v.id,'show',x);},
      rename:function(nm){spSet(role,v.id,'name',nm);},
      menu:function(){return[{t:'Jadikan versi aktif',dis:on,fn:function(){spActivate(role,v.id);}},role!=='ortho'&&!on?{t:(v.show?'Sembunyikan':'Tampilkan')+' sebagai pembanding',fn:function(){spSet(role,v.id,'show',!v.show);}}:null,
        {t:'Catatan…',fn:function(){var r=U.ask('Catatan versi "'+v.name+'":',v.note||'');if(r!=null)spSet(role,v.id,'note',r);}},{sep:1},{t:'Hapus versi ini',danger:1,fn:function(){spDel(role,v.id);}}].filter(Boolean);}};});}
  /* ---------- folder ---------- */
  function fProj(){var fp=window.FP&&FP.dir;return{id:'proj',step:'1',t:'Proyek: '+(SA.pname||'-'),ic:'proj',fold:1,b:fp?'folder':'lokal',hint:fp?'Folder proyek: '+FP.dir.name:'Tersimpan di komputer ini (belum terhubung ke folder proyek)',
    go:function(){var b=$('pjBtn');if(b)b.click();},
    menu:function(){return[{t:'Simpan sekarang',fn:A('_ptSave')},{t:'Simpan sebagai file .prj…',fn:function(){SA.prjSave();}},{t:'Buka file .prj…',fn:function(){PT.pick('.prj',false,function(i){SA.prjOpen(i.files[0]);});}},{t:'Simpan salinan proyek (.dh3d)…',fn:function(){SA.downloadProj();}},{t:'Import ulang (data lain dipertahankan)…',fn:function(){SA.reopen();}},{sep:1},{t:'Menu proyek & folder…',fn:function(){var b=$('pjBtn');if(b)b.click();}}];}};}
  window._ptSave=function(){if(SA.saveNow)SA.saveNow();};
  function fSpatial(){var mdK=function(kind,ic,lab){return ok(function(){return MD[kind].map(function(m,i){return{id:'ref.'+kind+'.'+i+'.'+m.name,t:m.name,ic:ic,tab:'Model',sub:lab,chk:!!m.vis,onChk:function(v){mdSet(kind,i,'vis',v);},
      b:m.nt?N(m.nt)+' segitiga':(m.pts&&m.pts.length?N(m.pts.length)+' titik':''),menu:function(){return[{t:'Hapus',danger:1,fn:function(){mdDel(kind,i);}}];}};});},[]);};
    var refK=[].concat(mdK('pts','pts','Titik'),mdK('str','string','String'));
    return{id:'sp',step:'2',t:'Data Spasial',ic:'folder',fold:1,tab:'SP',hint:'Topografi, desain pit, orthofoto (dengan versi) dan data referensi Surpac',
      menu:function(){return[addV('topo'),addV('pit'),addV('ortho'),{sep:1},{t:'Pengaturan overlay…',fn:tab('Overlay')}];},
      kids:[{id:'sp.topo',t:'Topografi',ic:'topo',tab:'SP',sub:'Topografi',chk:!!topoAs(),onChk:function(v){setTopo(v?topoPref():'');},
          b:topoAs()==='line'?'garis':topoAs()==='both'?'surface+garis':topoAs()?'surface':'',menu:function(){return[addV('topo'),{sep:1}].concat(asMenu(topoAs(),setTopo));},kids:versions('topo')},
        {id:'sp.pit',t:'Desain pit',ic:'pit',tab:'SP',sub:'Pit',chk:!!U.cb('ovPit'),onChk:function(v){U.setCb('ovPit',v);},b:{surf:'surface',line:'garis',both:'surface+garis'}[U.val('ovPitMode')]||'',
          menu:function(){var c=U.val('ovPitMode');return[addV('pit'),{sep:1}].concat(asMenu(c,function(m){var S=$('ovPitMode');if(S)S.value=m;U.setCb('ovPit',true);updatePlot();}));},kids:versions('pit')},
        {id:'sp.ortho',t:'Orthofoto',ic:'ortho',tab:'SP',sub:'Ortho',chk:!!U.cb('ovOrtho'),onChk:function(v){U.setCb('ovOrtho',v);},
          menu:function(){var m=U.val('orMode');return[addV('ortho'),{sep:1},{h:'Posisi orthofoto'},{t:'Latar paling bawah (lepas elevasi)',on:m==='base',fn:function(){U.setVal('orMode','base');}},{t:'Drape ke topografi',on:m==='drape',fn:function(){U.setVal('orMode','drape');}},{t:'Bidang datar (di atas data)',on:m==='flat',fn:function(){U.setVal('orMode','flat');}}];},kids:versions('ortho')},
        {id:'sp.ref',t:'Data referensi (titik survey, string)',ic:'ref',tab:'Model',sub:'Titik survey',b:refK.length||'',dim:!refK.length,
          menu:function(){return[{t:'Import titik survey…',fn:function(){PT.pick('.csv,.txt',true,function(i){mdPts(i);});}},{t:'Import string (.str / .dxf)…',fn:function(){PT.pick('.str,.dxf',true,function(i){mdStr(i);});}}];},kids:refK}]};}
  function fDb(){var C=window.collars||[],Sv=window.surveys||[],As=window.assays||[],G=window.geoRows||[],E=window.elements||[],cur=U.val('elementFilter'),ga=U.val('geoAttr');
    var els=E.map(function(e){return{id:'db.el.'+e,t:e,ic:'el',tab:'Data',mark:e===cur?'warna':'',hint:'Warnai trajectory dengan '+e,go:function(){U.setVal('elementFilter',e);if(window.trajMode)trajMode('grade');},
      menu:function(){return[{t:'Warnai dengan '+e,fn:function(){U.setVal('elementFilter',e);}},{t:'Warna kadar & kelas…',fn:tab('Warna')}];}};});
    var gat=U.opts('geoAttr').map(function(o){return{id:'db.geo.'+o[0],t:o[1],ic:'attr',tab:'Geo',mark:o[0]===ga&&U.val('geoAttr')!==''&&ok(function(){return $('tmL').classList.contains('on');},false)?'warna':'',
      go:function(){U.setVal('geoAttr',o[0]);if(window.trajMode)trajMode('geo');}};});
    var tb=function(id,t,ic,n,kind,o){return Object.assign({id:id,t:t,ic:ic,b:N(n),dim:!n,menu:function(){var L=[{t:'Ganti / perbarui (upsert)…',fn:ups}];if(kind)L.push({sep:1},{t:'Hapus tabel ini…',danger:1,dis:!n,fn:function(){PTD.drop(kind);}});return L;}},o||{});};
    return{id:'db',step:'3',t:'Database Bor',ic:'folder',fold:1,tab:'Data',b:C.length?N(C.length)+' hole':'',
      menu:function(){return[{t:'Tambah / perbarui data bor (upsert)…',fn:ups},{t:'Export database (CSV)',fn:A('gxDbExport')},undoM,{sep:1},{t:'Hapus hole tertentu…',fn:delHoles,dis:!C.length},{t:'Hapus seluruh database bor…',danger:1,dis:!C.length,fn:function(){PTD.drop('all');}}];},
      kids:[tb('db.collar','Collar','collar',C.length,null,{tab:'Data',chk:U.cb('showCollar'),onChk:function(v){U.setCb('showCollar',v);},menu:function(){return[{t:'Ganti / perbarui (upsert)…',fn:ups},{sep:1},{t:'Hapus hole tertentu…',fn:delHoles,dis:!C.length}];}}),
        tb('db.survey','Survey','table',Sv.length,'survey',{tab:'Data'}),
        tb('db.assay','Assay','table',As.length,'assay',{tab:'Data',kids:els}),
        tb('db.geo','Geologi','geo',G.length,'geo',{tab:'Geo',kids:gat}),
        {id:'db.traj',t:'Trajectory',ic:'hole',tab:'View',chk:U.cb('showTraj'),onChk:function(v){U.setCb('showTraj',v);}},
        {id:'db.lbl',t:'Label hole',ic:'attr',tab:'View',chk:U.cb('showLabel'),onChk:function(v){U.setCb('showLabel',v);}},
        {id:'db.plan',t:'Plan bor (rencana)',ic:'plan',tab:'Plan',fold:1,
          /* sejak 0.24.44: tiap "Plan baru" = satu sub-node, berurutan sesuai waktu dibuat (plset_dh.js) */
          b:ok(function(){if(!window.PLS)return PL.h.length;var n=0;PL.sets.forEach(function(s){n+=s.h.length;});return PL.sets.length+' plan \u00b7 '+n+' titik';},0)||'',chk:U.cb('plShow'),onChk:function(v){U.setCb('plShow',v);},
          kids:ok(function(){return window.PLS?PLS.kids():[];},[]),
          menu:function(){return[{t:'Plan baru…',fn:function(){if(window.PLS)PLS.baru();}},{sep:1},{t:'Export CSV plan aktif…',fn:A('plExport')},{t:'Export CSV semua plan…',fn:function(){if(window.PLS)PLS.exportSemua();}},{sep:1},{t:'Hapus semua titik di plan aktif…',danger:1,fn:A('plClear')}];}}]};}
  function delHoles(){var r=U.ask('HoleID yang akan dihapus (pisahkan dengan koma / spasi):','');if(!r)return;var ids=r.split(/[\s,;]+/).filter(Boolean);if(ids.length)PTD.drop('holes',ids);}
  function fStruct(){var F=ok(function(){return STR.F;},[]),P=ok(function(){return STR.P;},[]),cnt=function(id){return P.filter(function(p){return p.fid===id;}).length;};
    var node=function(f,t){var n=cnt(f.id);return{id:'st.'+f.id,t:t||f.name,ic:'pts',tab:'Model',sub:'Struktur',b:n||'',dim:!n,chk:f.on!==false,onChk:function(v){f.on=v;stDirty();},
      menu:(f.kind==='csv'||f.kind==='mapst')&&n?function(){return[{t:'Hapus '+(f.kind==='csv'?'file struktur':'semua titik struktur Mapping'),danger:1,fn:function(){stDelFile(f.id);}}];}:null};};
    var man=F.filter(function(f){return f.id==='man';}),gm=F.filter(function(f){return f.id==='gm';}),mp=F.filter(function(f){return /^map/.test(f.kind||'');}),csv=F.filter(function(f){return f.id!=='man'&&f.id!=='gm'&&!/^map/.test(f.kind||'');});
    var nL=ok(function(){return MAP.F.filter(function(f){return f.kind==='str';}).length;},0),kids=[];
    man.forEach(function(f){kids.push(node(f,'Titik manual (3D)'));});gm.forEach(function(f){kids.push(node(f,'Flag struktur (Geological Modelling)'));});
    kids.push({id:'st.map',t:'Dari Peta (Mapping)',ic:'map',fold:1,tab:'Map',sub:'Titik struktur',b:mp.reduce(function(a,f){return a+cnt(f.id);},0)||'',hint:'Titik struktur yang ditaruh di peta + titik pick-up berkolom Dip / Dip_Azimuth (Plunge / Trend)',
      kids:mp.map(function(f){return node(f,f.kind==='mapst'?'Titik struktur (klik di peta)':String(f.name).replace(/\s*\((Map pick-up|Mapping pick-up)\)\s*$/,'')+' (pick-up)');}).concat(nL?[{id:'st.mapln',t:'Garis struktur peta (sesar, kekar, vein, sumbu lipatan)',ic:'digit',tab:'Map',sub:'Digitasi',b:nL}]:[])});
    var FF=ok(function(){return FLT.F;},[]),TMS={pre:'pre',syn:'syn',post:'post'};
    kids.push({id:'st.flt',t:'Sesar (bidang 3D)',ic:'section',fold:1,tab:'FLT',b:FF.length||'',chk:ok(function(){return FLT.lay!==false;},true),onChk:function(v){FLT.lay=v;fltDirty(false);},hint:'Bidang sesar 3D: dip / dip direction, vektor gerak, offset, pre / syn / post mineralisasi, urutan umur',
      menu:function(){return[{t:'Buka panel Sesar 3D',fn:function(){uiTab('FLT');}},{t:'+ Sesar dari koordinat…',fn:function(){uiTab('FLT');fltManual();}},{t:'Urutkan umur otomatis',fn:A('fltAutoAge')},{t:'Export CSV sesar',fn:A('fltCsv')},{t:'Export DXF bidang sesar',fn:A('fltDxf')}];},
      kids:FF.map(function(f){return{id:'st.flt.'+f.id,t:f.name+' · '+TMS[f.tm]+(f.tm==='post'&&+f.off>0?' · '+f.off+' m':''),ic:'string',tab:'FLT',b:'umur '+f.age,chk:f.on!==false,onChk:function(v){fltSet(f.id,'on',v);},
        go:function(){FLT.sel=f.id;uiTab('FLT');},rename:function(nm){fltSet(f.id,'name',nm);},menu:function(){return[{t:'Edit atribut',fn:function(){FLT.sel=f.id;uiTab('FLT');}},{sep:1},{t:'Hapus sesar',danger:1,fn:function(){fltDel(f.id);}}];}};})});
    if(csv.length)kids.push({id:'st.csv',t:'File CSV struktur',ic:'table',fold:1,tab:'Model',sub:'Struktur',b:csv.reduce(function(a,f){return a+cnt(f.id);},0)||'',kids:csv.map(function(f){return node(f);})});
    return{id:'st',step:'5',t:'Struktur Geologi',ic:'folder',fold:1,tab:'Model',sub:'Struktur',b:P.length||'',chk:ok(function(){return !!STR.lay;}),onChk:function(v){STR.lay=v;updatePlot();},
      hint:'Satu basis data struktur: titik manual, flag Geological Modelling, Peta (Mapping) dan file CSV — dipakai RBF, OK dinamis, Map & 3D',
      menu:function(){return[{t:'Import CSV struktur…',fn:function(){PT.pick('.csv,.txt',false,function(i){stImport(i);});}},{t:'+ Titik (klik di 3D)',fn:function(){tab('Model','Struktur')();stMode('add3d');}},{t:'+ Titik struktur di peta (Mapping)',fn:function(){PT.select('mp.st');}}];},
      kids:kids};}
  function fMapping(){var PF=ok(function(){return MAP.PF;},[]),FF=ok(function(){return MAP.F;},[]),KN={alt:'Alterasi',lith:'Litologi',str:'Struktur',oth:'Garis lain'};
    return{id:'mp',step:'4',t:'Peta (Mapping)',ic:'map',fold:1,tab:'Map',sub:'Pick-up',b:(PF.length?PF.length+' pick-up':'')+(PF.length&&FF.length?' · ':'')+(FF.length?FF.length+' fitur':''),hint:'Pemetaan lapangan: titik pick-up, digitasi boundary / garis struktur, titik struktur. Hasilnya terhubung ke Struktur Geologi & Geological Modelling',
      kids:[{id:'mp.pf',t:'Pick-up survei / pemetaan',ic:'pts',tab:'Map',sub:'Pick-up',b:PF.length||'',menu:function(){return[{t:'Import CSV titik…',fn:function(){PT.pick('.csv,.txt',true,function(i){mapPtImport(i);});}}];},
          kids:PF.map(function(f){return{id:'mp.pf.'+f.id,t:f.name,ic:'table',tab:'Map',sub:'Pick-up',b:f.P.length,chk:!!f.on,onChk:function(v){mapPtSet(f.id,'on',v);},menu:function(){return[{t:'Zoom ke titik',fn:function(){mapZoom(f.id);}},{sep:1},{t:'Hapus file',danger:1,fn:function(){mapPtDel(f.id);}}];}};})},
        {id:'mp.dig',t:'Digitasi peta',ic:'digit',tab:'Map',sub:'Digitasi',b:FF.length||'',
          kids:FF.slice(0,300).map(function(f){return{id:'mp.f.'+f.id,t:f.name,ic:f.closed?'poly':'string',tab:'Map',sub:'Digitasi',b:KN[f.kind]||'',chk:f.vis!==false,onChk:function(v){mapSetF(f.id,'vis',v);},go:function(){MAP.sel=f.id;MAP.mode=null;try{mapPanel();mapDraw();}catch(e){}},
            menu:function(){return[{t:'Hapus fitur',danger:1,fn:function(){mapDel(f.id);}}];}};})},
        {id:'mp.st',t:'Titik struktur (klik di peta)',ic:'pts',tab:'Map',sub:'Titik struktur',b:ok(function(){return STR.P.filter(function(p){return p.fid==='mapst';}).length;},0)||''}]};}
  function fSection(){var S=ok(function(){return DG.S;},[]),m=U.val('sMode'),pos=U.val('pos');
    return{id:'sec',step:'5',t:'Sayatan & Penampang',ic:'folder',fold:1,tab:'Slice',b:(m==='H'?'RL ':'')+(isFinite(+pos)?(+pos).toFixed(1):'')+(m==='H'?'':' m'),
      kids:[{id:'sec.2d',t:'Penampang 2D',ic:'s2d',tab:'Slice',chk:ok(function(){return !!VIEW2D;}),onChk:function(){toggle2D();}},
        {id:'sec.clip',t:'Potong data di dalam slab (3D)',ic:'section',tab:'Slice',chk:U.cb('sliceClip'),onChk:function(v){U.setCb('sliceClip',v);}},
        {id:'sec.plane',t:'Bidang potong',ic:'section',tab:'Slice',chk:U.cb('showPlane'),onChk:function(v){U.setCb('showPlane',v);}},
        {id:'sec.prof',t:'Profil topo / pit pada sayatan',ic:'topo',tab:'Slice',chk:U.cb('showProf'),onChk:function(v){U.setCb('showProf',v);}},
        {id:'sec.dig',t:'Digitasi string',ic:'digit',tab:'Dig',b:S.length||'',menu:function(){return[{t:'Export string digitasi (DXF)',fn:function(){dgExport('dxf');}},{t:'Export string digitasi (STR)',fn:function(){dgExport('str');}}];},
          kids:S.slice(0,300).map(function(s,i){return{id:'dg.'+(s.id||i)+'.'+s.no,t:'String '+s.no+(s.d?' · '+s.d:''),ic:'string',tab:'Dig',chk:!!s.vis,onChk:function(v){dgVis(i,v);},dbl:function(){dgGo(i);},
            menu:function(){return[{t:'Buka di penampangnya',fn:function(){dgGo(i);}},{sep:1},{t:'Hapus string',danger:1,fn:function(){dgDel(i);}}];}};})}]};}
  function fGM(){var D=ok(function(){return GM.doms;},[]),act=ok(function(){return GM.act;});
    var kid=function(d){var ns=ok(function(){return GM.str.filter(function(s){return s.dom===d.id;}).length;},0),ch=D.filter(function(x){return x.par===d.id;});
      return{id:'gm.'+d.id,t:d.name,ic:'dom',tab:'GM',mark:d.id===act?'aktif':'',b:ns?ns+' string':'',chk:d.vis!==false,onChk:function(v){d.vis=v;gmDirty();},
        go:function(){if(GM.act!==d.id){GM.act=d.id;gmPanel();}},rename:function(nm){gmRename(d.id,nm);},
        menu:function(){return[{t:'Jadikan domain aktif',dis:d.id===act,fn:function(){GM.act=d.id;gmPanel();}},{sep:1},{t:'Hapus domain…',danger:1,fn:function(){gmDelDom(d.id);}}];},kids:ch.map(kid)};};
    return{id:'gm',step:'6',t:'Geomodeller Vein System Deposit',ic:'folder',fold:1,tab:'GM',b:D.length?D.length+' domain':'',hint:'Domain vein → flag interval → string kontrol HW/FW → solid',
      menu:function(){return[{t:'+ Domain baru…',fn:function(){var r=U.ask('Nama domain baru:','');if(r!=null){gmAddDom(r);uiTab('GM');}}},{sep:1},{t:'Export flag (CSV)',fn:A('gmFlagCsv')},{t:'Export string kontrol (STR)',fn:function(){gmStrExport('str');}},{t:'Export string kontrol (DXF)',fn:function(){gmStrExport('dxf');}}];},
      kids:[{id:'gm.add',t:'+ Tambah domain…',ic:'dom',hint:'Domain vein / zona baru; dikerjakan di Properti setelah dipilih',go:function(){var r=U.ask('Nama domain baru:','');if(r!=null&&String(r).trim()){gmAddDom(String(r).trim());uiTab('GM');}}}].concat(D.filter(function(d){return !d.par;}).map(kid))};}
  function fSL(){var LL=ok(function(){return SL.L;},[]),so=function(id,t,ic,k){return{id:id,t:t,ic:ic,tab:'SL',go:function(){uiTab('SL');setTimeout(function(){try{uiSecOpen('sl',k);}catch(e){}},40);}};};
    return{id:'sl',step:'6b',t:'Geomodeller Stratified-Laterite Deposit',ic:'folder',fold:1,tab:'SL',b:LL.length?LL.length+' lapisan':'',chk:ok(function(){return SL.lay!==false;},true),onChk:function(v){SL.lay=v;updatePlot();},
      hint:'Laterit Ni / bauksit / stratiform (sedex): lapisan dari log geologi → permukaan atap / lantai → estimasi unfold per lapisan → laporan WMT / DMT',
      menu:function(){return[{t:'Preset laterit nikel',fn:function(){uiTab('SL');slPreset('lat');}},{t:'Preset bauksit',fn:function(){uiTab('SL');slPreset('bx');}},{t:'Preset stratiform (sedex)',fn:function(){uiTab('SL');slPreset('sdx');}},{sep:1},{t:'Jalankan estimasi lapisan',fn:A('slRun')},{t:'Export laporan WMT / DMT (CSV)',fn:A('slRepCsv')}];},
      kids:LL.map(function(l,i){return{id:'sl.l.'+l.id,t:l.name,ic:'dom',chk:l.vis!==false,onChk:function(v){slSetL(i,'vis',v);},tab:'SL',b:(l.codes||[]).length?'':'kode?',rename:function(nm){slSetL(i,'name',nm);},go:function(){uiTab('SL');setTimeout(function(){try{uiSecOpen('sl',1);}catch(e){}},40);}};})
        .concat([so('sl.1','① Lapisan & kode log','attr',1),so('sl.2','② Permukaan (atap / lantai)','topo',2),so('sl.3','③ Estimasi unfold per lapisan','est',3),so('sl.4','④ Laporan WMT / DMT','report',4)])};}
  function fBM(){var m=window.BX&&BX.m,V=ok(function(){return BXV;},[]),cur=m?ok(function(){return bxvKey(m.src);},''):'',at=m?Object.keys(m.num||{}).concat(Object.keys(m.cat||{})):[],ca=ok(function(){return BX.ui.attr;},'');
    return{id:'bm',step:'7',t:'Block Model',ic:'folder',fold:1,tab:'BM',b:m?N(m.n)+' blok':'',chk:m?U.cb('bxShow'):undefined,onChk:function(v){U.setCb('bxShow',v);},
      menu:function(){return[{t:'Import block model…',fn:A('bxDlg')},{t:'Tambah versi block model…',fn:A('bmAdd')},{t:'Export block model GC (.mdl)',fn:A('bxMdlExport'),dis:!m},{sep:1},{t:'Hapus dari tampilan',danger:1,dis:!m,fn:A('bxClear')}];},
      kids:[].concat(V.map(function(v){var on=ok(function(){return bxvKey(v.src)===cur;},false);return{id:'bm.v.'+v.id,t:v.name,ic:'ver',tab:'SP',sub:'Block',mark:on?'aktif':'',b:v.info||'',hint:v.src&&v.src.name,
          rename:function(nm){bmSet(v.id,'name',nm);},menu:function(){return[{t:'Jadikan versi aktif',dis:on,fn:function(){bmActivate(v.id);}},{sep:1},{t:'Hapus dari daftar versi',danger:1,fn:function(){bmDel(v.id);}}];}};}),
        m?[{id:'bm.attr',t:'Atribut',ic:'attr',tab:'BM',b:at.length,kids:at.map(function(k){return{id:'bm.a.'+k,t:k,ic:m.cat&&m.cat[k]?'geo':'el',tab:'BM',mark:k===ca?'warna':'',go:function(){bxSet('attr',k);}};})},
          {id:'bm.cls',t:'Warna & kelas',ic:'color',tab:'BM',sub:'Warna'},{id:'bm.flt',t:'Filter & SG',ic:'attr',tab:'BM',sub:'Filter'},{id:'bm.stat',t:'Statistik',ic:'chart',tab:'BM',sub:'Statistik'}]:[])};}
  var sub=function(id,t,ic,tb,re){return{id:id,t:t,ic:ic,tab:tb,sub:re};};
  function nodes(){var L=[],add=function(f,id,t){try{L.push(f());}catch(e){console.warn('tree',id,e);L.push({id:id,t:t,ic:'folder',fold:1});}};
    add(fProj,'proj','Proyek');add(fSpatial,'sp','Data Spasial');if(window.wfxNode)add(wfxNode,'wf','Import Wireframe Geologi');add(fDb,'db','Database Bor');add(fMapping,'mp','Peta (Mapping)');add(fStruct,'st','Struktur Geologi');
    add(fGM,'gm','Geomodeller Vein System Deposit');add(fSL,'sl','Geomodeller Stratified-Laterite Deposit');add(fBM,'bm','Block Model');
    /* 0.20: domain aktif juga dari node Geostatistik & Model Estimation */
    var actD=ok(function(){return GM.act;}),tops=ok(function(){return gmTops();},[]);
    var gsDom=function(d){var ch=ok(function(){return gmKids(d.id);},[]);return{id:'gs.d.'+d.id,t:d.name,ic:'dom',mark:d.id===actD&&ok(function(){return GS.domOnly!==false;},true)?'aktif':'',
        hint:'Geostatistik hanya memakai sampel di dalam domain ini',go:function(){gxDomAct(d.id,'gs');},kids:ch.map(gsDom)};};
    var meDom=function(d){return{id:'me.d.'+d.id,t:d.name,ic:'dom',mark:ok(function(){return gmTopId(actD)===d.id;},false)?'aktif':'',chk:ok(function(){return ME.sel[d.id]!==false;},true),onChk:function(v){ME.sel[d.id]=v;try{mePanel();}catch(e){}},
        hint:'Klik = domain aktif (parameter & jalankan); centang = ikut "Jalankan semua domain"',go:function(){gxDomAct(d.id,'me');},
        menu:function(){return[{t:'Jalankan estimasi domain ini',fn:function(){gxDomAct(d.id,'me');meRunAct();}},{t:'Jalankan semua domain (dicentang)',fn:A('meRun')}];}};};
    L.push({id:'me',step:'8',t:'Model Estimation',ic:'folder',fold:1,tab:'ME',b:ok(function(){return ME.store&&ME.store.runs&&ME.store.runs.length?ME.store.runs.length+' run':'';},''),
      menu:function(){return[{t:'Jalankan domain aktif',fn:A('meRunAct')},{t:'Jalankan semua domain (dicentang)',fn:A('meRun')}];},
      kids:tops.map(meDom).concat([sub('me.1','Block model','block','ME','Block model'),sub('me.2','Domain & parameter','dom','ME','Domain'),sub('me.3','Jalankan','est','ME','Jalankan'),sub('me.4','Hasil','report','ME','Hasil')])});
    L.push({id:'val',step:'9',t:'Validasi BM',ic:'check',tab:'Val',hint:'Swath plot, komposit vs blok, distribusi, grade-tonase'});
    L.push({id:'rep',step:'10',t:'Reporting BM',ic:'folder',fold:1,tab:'Rep',kids:[sub('rep.1','Atribut','attr','Rep','Atribut'),sub('rep.2','Constraint (topo / pit / domain)','pit','Rep','Constraint'),sub('rep.3','Hasil grade × tonase','chart','Rep','Hasil')].concat(window.rpxTree?rpxTree():[])});
    L.push({id:'gs',step:'11',t:'Geostatistik',ic:'gs',fold:1,hint:'Variogram & panduan (panel kanan); pilih domain aktif di bawahnya',go:function(){var p=$('gsPanel');if(!p||p.hidden||!GS.open)gsToggle();},
      kids:tops.map(gsDom).concat([{id:'gs.all',t:'Semua data (tanpa filter domain)',ic:'db',mark:ok(function(){return GS.domOnly===false;},false)?'aktif':'',go:function(){gxDomAct(null,'gs');}}])});
    L.push({id:'out',step:'12',t:'Layout & Ekspor',ic:'folder',fold:1,kids:[{id:'out.map',t:'Peta (layout cetak)',ic:'map',tab:'Map',sub:'Layer peta',kids:[sub('map.1','Layer peta (isi peta)','eye','Map','Layer peta'),sub('map.4','Layout & cetak','export','Map','Layout')]},
      {id:'out.png',t:'Simpan gambar PNG',ic:'image',go:A('savePNG')}]});
    /* Export database & export block model .mdl hanya di node pemiliknya (Database Bor / Block Model) — satu ekspor, satu node */
    L.push({id:'set',t:'Pengaturan tampilan',ic:'folder',fold:1,kids:[{id:'set.w',t:'Warna kadar',ic:'color',tab:'Warna'},{id:'set.o',t:'Overlay',ic:'eye',tab:'Overlay'},{id:'set.v',t:'Tampilan & performa',ic:'gear',tab:'View'}]});
    if(window.OG)L.push({id:'og',t:'Ore Geometry',ic:'gs',fold:1,tab:'OG',mark:'referensi',b:ok(function(){return OG.R?N(OG.R.nHit)+' bor GT':'';},''),
      hint:'Referensi geologist: intercept & GT long section, ore shoot (pitch / plunge / trend), grade shell 3D. Tidak dipakai pemodelan / estimasi.',
      chk:ok(function(){return OG.on!==false;},true),onChk:function(v){OG.on=v;updatePlot();},
      kids:[sub('og.1','Data & intercept (GT)','attr','OG','Intercept'),sub('og.2','Long section GT','section','OG','Long section'),sub('og.3','Ore shoot (pitch / plunge / trend)','chart','OG','Ore shoot'),sub('og.4','Grade shell 3D','block','OG','Grade shell')]});
    /* Urutan mengikuti alur kerja nyata (permintaan pemilik 8 Nov 2026): Ore Geometry (referensi geologist,
       sebelum pemodelan) sesudah Struktur; Geostatistik (variogram) sebelum Block Model & Model Estimation.
       Node yang tidak dikenal tetap di tempat relatifnya (sesudah pendahulunya). */
    var URUT=['proj','sp','wf','db','mp','st','og','gm','sl','gs','bm','me','val','rep','out','set'],STEP={og:'5b',gs:'7',bm:'8',me:'9',val:'10',rep:'11',out:'12'};
    L.forEach(function(n,i){n._o=i;});
    var rk=function(n){var k=URUT.indexOf(n.id);if(k>=0)return k;for(var j=n._o-1;j>=0;j--){var p=URUT.indexOf(L[j].id);if(p>=0)return p+0.5;}return -0.5;};
    L.sort(function(a,b){var d=rk(a)-rk(b);return d||a._o-b._o;});
    L.forEach(function(n){delete n._o;if(STEP[n.id])n.step=STEP[n.id];});
    return L;}
  PT.install({app:'dh',nodes:nodes,openDef:['sp','db','gm','bm']});
  /* Versi block model dikelola di bagian ④ Block model panel Data Spasial. Saat node versi di bawah
     Block Model dipilih, hanya bagian itu yang tampil (tab Topografi / Pit / Ortho disembunyikan), supaya
     panelnya milik node Block Model, bukan terbaca sebagai panel Data Spasial. */
  (function(){var st=document.createElement('style');st.textContent='#pSP.sp-bmsaja .uitabs{display:none}';document.head.appendChild(st);
    /* klik di tree memakai select() internal, jadi yang diamati adalah perubahan sorotan node, bukan PT.select */
    var cek=function(){try{var p=$('pSP');if(p)p.classList.toggle('sp-bmsaja',/^bm\.v\./.test(String(PT.sel||'')));}catch(e){}};
    var pasang=function(){var t=$('ptree');if(!t)return setTimeout(pasang,300);new MutationObserver(cek).observe(t,{subtree:true,attributes:true,attributeFilter:['class'],childList:true});cek();};pasang();})();
})();
