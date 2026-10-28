/* ================= GC-Ex Block Model: isi PROJECT TREE (urut langkah kerja grade control) =================
   Sebelum penambangan:  1 Proyek · 2 Data Spasial · 3 Block Model · 4 Data Referensi · 5 Flitch Aktif · 6 Dig Block ·
                         7 Laporan Grade × Tonnage · 8 Layout & Ekspor Dig Plan
   Sesudah penambangan:  9 As-Mined (setup, sampel, poligon & pick-up, parameter) · 10 Register & Laporan As-Mined
   Tiap langkah punya status (✓ selesai, berikutnya, belum, opsional); panel Properti hanya menampilkan bagian langkah itu
   (panel Dig block yang panjang dipecah: flitch, dig block otomatis / manual, laporan, ekspor) dan di bawahnya ada tombol
   langkah sebelumnya / berikutnya. */
(function(){if(!window.PT||PT.def)return;
  var $=function(i){return document.getElementById(i);},U=PT.u,N=U.num,ok=function(f,d){try{var r=f();return r===undefined?d:r;}catch(e){return d;}};
  var A=function(fn){var a=[].slice.call(arguments,1);return function(){if(typeof window[fn]==='function')return window[fn].apply(window,a);};};
  var tab=function(t,sub){return function(){uiTab(t);if(sub)setTimeout(function(){PT.goSub(t,sub);},30);};};
  var sub=function(id,t,ic,tb,re,o){return Object.assign({id:id,t:t,ic:ic,tab:tb,sub:re},o||{});};
  var reimp={t:'Ganti / tambah lewat Import ulang…',fn:function(){if(SA.reopen)SA.reopen();}};
  var has=function(a){return !!(a&&a.length);};
  /* ---------- fokus bagian panel Dig block (#dbBody dipecah per segmen) ---------- */
  var FOC='';
  function segTag(){var b=$('dbBody');if(!b)return;var seg='fl';[].forEach.call(b.children,function(c){
      if(c.classList.contains('dbsub')){var t=c.textContent||'';seg=/otomatis|tujuan/i.test(t)?'auto':/digit manual/i.test(t)?'man':/export/i.test(t)?'exp':/running grade/i.test(t)?'rep':seg;}
      else if(c.classList.contains('elbox')&&seg==='fl')seg='el';
      /* aturan kelas (string number / warna / material) & tujuan dipakai dig block otomatis DAN manual */
      var rule=seg==='auto'&&(c.classList.contains('dbrt')||c.classList.contains('dbdt')||(c.classList.contains('dbsub')&&/tujuan/i.test(c.textContent||''))||
        (c.tagName==='BUTTON'&&/dbRAdd/.test(c.getAttribute('onclick')||''))||!!(c.querySelector&&c.querySelector('select[onchange*="rAttr"],button[onclick*="lyDestAdd"]')));
      c.setAttribute('data-seg',rule?'rule':seg);});
    if(FOC)b.setAttribute('data-f',FOC);else b.removeAttribute('data-f');}
  function focus(f){FOC=f||'';segTag();var b=$('dbBody');if(b&&f){var sd=$('side');if(sd)sd.scrollTop=0;}}
  (function(){var d=window.dbPanel;if(typeof d==='function'&&!d._ptf){window.dbPanel=function(){var r=d.apply(this,arguments);try{segTag();}catch(e){}return r;};window.dbPanel._ptf=1;}})();
  (function(){var u=window.uiTab;if(typeof u==='function')window.uiTab=function(){var r=u.apply(this,arguments);try{if(Date.now()-(PT._qt||0)>1500){if(FOC)focus('');document.body.classList.remove('pt-bmhd');}}catch(e){}return r;};})();
  /* ---------- tampilkan sebagai ---------- */
  var topoAs=function(){var s=U.cb('ovTopoS'),l=U.cb('ovTopoL');return s&&l?'both':s?'surf':l?'line':'';};
  var topoPref=function(){var m='surf';try{m=localStorage.getItem('gcex_pt_topo')||'surf';}catch(e){}return m;};
  var setTopo=function(m){if(m)try{localStorage.setItem('gcex_pt_topo',m);}catch(e){}var S=$('ovTopoS'),L=$('ovTopoL');if(S)S.checked=m==='surf'||m==='both';if(L)L.checked=m==='line'||m==='both';updatePlot();};
  var asMenu=function(cur,set){return[{h:'Tampilkan sebagai'},{t:'Surface (permukaan)',on:cur==='surf',fn:function(){set('surf');}},{t:'Garis (kontur / crest-toe)',on:cur==='line',fn:function(){set('line');}},{t:'Surface + garis',on:cur==='both',fn:function(){set('both');}}];};
  /* ---------- status ---------- */
  function S(){var m=window.BX&&BX.m,fl=ok(function(){return !!(window.dbFlOn&&dbFlOn());},false),dig=m?ok(function(){return lyItems(true).length;},0):0,
      bnd=ok(function(){return amD().bnd||[];},[]),amc=bnd.filter(function(x){return x.st;}).length;
    return{fp:!!(window.FP&&FP.dir),sp:has(window.topoData)||has(window.pitData)||!!window.orthoImg,bm:!!m,ref:ok(function(){return MD.models.length+MD.pts.length+(MD.str||[]).length;},0),
      fl:fl,dig:dig,ly:ok(function(){return LY.pages.length;},0)>0,bnd:bnd.length,amc:amc};}
  function flTxt(){var B=ok(function(){return lyBench();},null);return B?'RL '+lyFmt(B[0])+' – '+lyFmt(B[1]):'';}
  function nodes(){var s=S(),m=window.BX&&BX.m,L=[],add=function(f,id,t){try{L.push(f());}catch(e){console.warn('tree',id,e);L.push({id:id,t:t,ic:'folder',fold:1});}};
    /* status & langkah berikutnya (langkah wajib berurutan) */
    var st={proj:s.fp?'done':'opt',sp:s.sp?'done':'opt',bm:s.bm?'done':'todo',ref:s.ref?'done':'opt',fl:s.fl?'done':'todo',dig:s.dig?'done':'todo',rep:s.dig?'done':'todo',out:s.ly?'done':'todo',
      am:s.amc&&s.amc===s.bnd?'done':s.bnd?'part':'todo',reg:s.amc?'done':'todo'};
    ['bm','fl','dig','out','am','reg'].some(function(k){if(st[k]!=='done'){st[k]=st[k]==='part'?'part':'next';return true;}return false;});
    add(function(){var fp=window.FP&&FP.dir;return{id:'proj',step:'1',st:st.proj,t:'Proyek: '+(SA.pname||'-'),ic:'proj',fold:1,b:fp?'folder':'lokal',hint:fp?'Folder proyek: '+FP.dir.name:'Tersimpan di komputer ini (belum terhubung ke folder proyek)',
      go:function(){var b=$('pjBtn');if(b)b.click();},
      menu:function(){return[{t:'Simpan sekarang',fn:function(){if(SA.saveNow)SA.saveNow();}},{t:'Simpan sebagai file .prj…',fn:function(){SA.prjSave();}},{t:'Buka file .prj…',fn:function(){PT.pick('.prj',false,function(i){SA.prjOpen(i.files[0]);});}},{t:'Unduh file proyek (.dh3d)',fn:function(){if(SA.downloadProj)SA.downloadProj();}},{t:'Import ulang (data lain dipertahankan)…',fn:function(){if(SA.reopen)SA.reopen();}},{sep:1},{t:'Menu proyek & folder…',fn:function(){var b=$('pjBtn');if(b)b.click();}}];}};},'proj','Proyek');
    add(function(){var T=window.topoData,Pd=window.pitData,O=window.orthoImg;
      return{id:'sp',step:'2',st:st.sp,t:'Data Spasial',ic:'folder',fold:1,tab:'Overlay',hint:'Topografi, desain pit & orthofoto (opsional)',menu:function(){return[reimp,{t:'Pengaturan overlay…',fn:tab('Overlay')}];},
        kids:[{id:'sp.topo',t:'Topografi',ic:'topo',tab:'Overlay',dim:!has(T),chk:has(T)?!!topoAs():undefined,onChk:function(v){setTopo(v?topoPref():'');},
            b:topoAs()==='line'?'garis':topoAs()==='both'?'surface+garis':topoAs()?'surface':'',menu:function(){return[reimp,{sep:1}].concat(asMenu(topoAs(),setTopo));}},
          {id:'sp.pit',t:'Desain pit',ic:'pit',tab:'Overlay',dim:!has(Pd),chk:has(Pd)?!!U.cb('ovPit'):undefined,onChk:function(v){U.setCb('ovPit',v);},b:has(Pd)?({surf:'surface',line:'garis',both:'surface+garis'}[U.val('ovPitMode')]||''):'',
            menu:function(){return[reimp,{sep:1}].concat(asMenu(U.val('ovPitMode'),function(mm){var S2=$('ovPitMode');if(S2)S2.value=mm;U.setCb('ovPit',true);updatePlot();}));}},
          {id:'sp.ortho',t:'Orthofoto',ic:'ortho',tab:'Overlay',dim:!O,chk:O?!!U.cb('ovOrtho'):undefined,onChk:function(v){U.setCb('ovOrtho',v);},b:O?({base:'latar',drape:'drape',flat:'datar'}[U.val('orMode')]||''):'',
            menu:function(){var mm=U.val('orMode');return[reimp,{sep:1},{h:'Posisi orthofoto'},{t:'Latar paling bawah (lepas elevasi)',on:mm==='base',fn:function(){U.setVal('orMode','base');}},{t:'Drape ke topografi',on:mm==='drape',fn:function(){U.setVal('orMode','drape');}},{t:'Bidang datar (di atas data)',on:mm==='flat',fn:function(){U.setVal('orMode','flat');}}];}}]};},'sp','Data Spasial');
    add(function(){var at=m?Object.keys(m.num||{}).concat(Object.keys(m.cat||{})):[],ca=ok(function(){return BX.ui.attr;},'');
      return{id:'bm',step:'3',st:st.bm,t:'Block Model',ic:'folder',fold:1,tab:'BM',sub:'Block model',b:m?N(m.n)+' blok':'',chk:m?U.cb('bxShow'):undefined,onChk:function(v){U.setCb('bxShow',v);},hint:m?m.name:'Import block model resmi (.mdl Surpac atau CSV)',
        menu:function(){return[{t:'Import block model…',fn:A('bxDlg')},{t:'Reporting grade × tonase (constraint)…',dis:!m,fn:function(){PT.select('bm.rep');}},{t:'Ringkasan seluruh model per RL…',fn:A('bsOpen'),dis:!(m&&window.bsOn&&bsOn())},{sep:1},{t:'Hapus block model',danger:1,dis:!m,fn:A('bxClear')}];},
        kids:m?[{id:'bm.cur',t:m.name,ic:'block',tab:'BM',sub:'Block model',b:ok(function(){return m.mdl&&m.mdl.via==='backend'?'.mdl besar':'';},''),hint:ok(function(){return m.src.name;},'')},
          {id:'bm.attr',t:'Atribut',ic:'attr',tab:'BM',sub:'Block model',b:at.length,kids:at.map(function(k){return{id:'bm.a.'+k,t:k,ic:m.cat&&m.cat[k]?'geo':'el',tab:'BM',sub:'Block model',mark:k===ca?'warna':'',go:function(){bxSet('attr',k);}};})},
          sub('bm.cls','Warna & kelas kadar','color','BM',['Block model','Warna']),sub('bm.flt','Filter & SG','attr','BM',['Block model','Filter']),sub('bm.stat','Statistik','chart','BM',['Block model','Statistik']),
          {id:'bm.rep',t:'Reporting (constraint)',ic:'report',tab:'Rep',b:ok(function(){return window.RP&&RP.res&&RP.res.bm===m.name?N(RP.res.nb)+' blok':'';},''),hint:'Grade × tonase sisa dengan constraint topografi / pit / DTM / domain / poligon / RL, ringkasan per RL',
            go:function(){if(window.RP){RP.sec=RP.res?'2':'1';rpPanel();}},
            kids:[{id:'bm.rep.1',t:'Atribut & ringkasan per RL',ic:'attr',tab:'Rep',go:function(){RP.sec='1';rpPanel();}},{id:'bm.rep.2',t:'Constraint',ic:'filter',tab:'Rep',go:function(){RP.sec='c';rpPanel();}},{id:'bm.rep.3',t:'Hasil grade × tonase',ic:'chart',tab:'Rep',go:function(){RP.sec='2';rpPanel();}}]},
          {id:'bm.rl',t:'Ringkasan seluruh model per RL',ic:'report',go:A('bsOpen'),dim:!(window.bsOn&&bsOn()),hint:'Untuk .mdl besar yang dibuka lewat backend (seluruh file, bukan hanya potongan)'}]:[]};},'bm','Block Model');
    add(function(){var mdK=function(kind,ic,lab){return ok(function(){return MD[kind].map(function(o,i){return{id:'ref.'+kind+'.'+i+'.'+o.name,t:o.name,ic:ic,tab:'Model',sub:lab,chk:!!o.vis,onChk:function(v){mdSet(kind,i,'vis',v);},
        b:o.nt?N(o.nt)+' segitiga':'',menu:function(){return[{t:'Hapus',danger:1,fn:function(){mdDel(kind,i);}}];}};});},[]);};
      var K=[].concat(mdK('models','ref','Wireframe'),mdK('pts','pts','Titik'),mdK('str','string','String'));
      return{id:'ref',step:'4',st:st.ref,t:'Data Referensi',ic:'folder',fold:1,tab:'Model',b:K.length||'',hint:'Opsional: solid & string Surpac, titik survey sebagai acuan',
        menu:function(){return[{t:'Import model vein / solid…',fn:function(){PT.pick('.dtm,.str,.msh,.obj,.dxf',true,function(i){mdImport(i);});}},{t:'Import titik survey…',fn:function(){PT.pick('.csv,.txt',true,function(i){mdPts(i);});}},{t:'Import string (.str / .dxf)…',fn:function(){PT.pick('.str,.dxf',true,function(i){mdStr(i);});}}];},kids:K};},'ref','Data Referensi');
    /* 5 flitch: SEMUA flitch yang sudah dikerjakan (dig block, string, poligon as-mined) sebagai subnode untuk audit / review */
    add(function(){var Sg=ok(function(){return DG.S;},[]),AMB=ok(function(){return amBndAll();},[]),G={},ord=[],fmt=function(v){return String(+(+v).toFixed(3));};
      var grp=function(top,bot){var k=(+top).toFixed(3)+'|'+(+bot).toFixed(3);if(!G[k]){G[k]={top:+top,bot:+bot,db:[],am:[]};ord.push(k);}return G[k];};
      Sg.forEach(function(q,i){if(q.inner||q.amTmp)return;var top,bot;if(q.db){top=q.db.top;bot=q.db.bot;}else{var p=q.pl;if(!p||p.m!=='H'||!isFinite(+p.pos)||!q.closed)return;var th=+p.thick||0;top=+p.pos+th/2;bot=+p.pos-th/2;}grp(top,bot).db.push({s:q,i:i});});
      AMB.forEach(function(x){if(isFinite(+x.top)&&isFinite(+x.bot))grp(x.top,x.bot).am.push(x);});
      ord.sort(function(a,b){return G[b].top-G[a].top;});
      var open=function(g){lySet('fh',+(g.top-g.bot).toFixed(3));lyU().bot='';lySet('top',+(+g.top).toFixed(3));lyApply();};
      var B=ok(function(){return lyBench();},[NaN,NaN]),isAct=function(g){return Math.abs(g.top-B[0])<1e-6&&Math.abs(g.bot-B[1])<1e-6;};
      var fl=ord.map(function(k){var g=G[k],ak=isAct(g),bd=[g.db.length?g.db.length+' DB':'',g.am.length?g.am.length+' AM':''].filter(Boolean).join(' · ');
        var kids=[];
        if(g.db.length)kids.push({id:'fl.'+k+'.db',t:'Dig block ('+g.db.length+')',ic:'poly',fold:1,kids:g.db.map(function(o){var q=o.s;return{id:'fl.'+k+'.db.'+(q.id||o.i),t:'#'+q.no+' '+(q.d||'string')+(q.dest?' → '+q.dest:''),ic:q.manual?'digit':'poly',
          b:(function(){try{var a=dgArea(q);return a?a.toFixed(0)+' m²':'';}catch(e){return '';}})(),
          go:function(){try{if(!isAct(g))open(g);setTimeout(function(){if(window.DGM)DGM.last=q.id;DB.sel=q.id;PT.goSub('BM','Dig block');try{dbPanel();}catch(e){}updatePlot();},120);}catch(e){console.error(e);}},
          menu:function(){return[{t:'Buka flitch & sorot',fn:function(){if(!isAct(g))open(g);}},{t:'Edit bentuk…',fn:function(){if(!isAct(g))open(g);setTimeout(function(){dbEdStart(DG.S.indexOf(q));},200);}}];}};})});
        if(g.am.length)kids.push({id:'fl.'+k+'.am',t:'Poligon as-mined ('+g.am.length+')',ic:'poly',fold:1,kids:g.am.map(function(x){var I=ok(function(){return amInfoById(x.id);},null);return{id:'fl.'+k+'.am.'+x.id,t:(I&&I.code)||x.name||x.id,ic:'poly',
          b:I&&I.calc?N(Math.round(I.ton))+' t @ '+(isFinite(I.gA)?I.gA.toFixed(2):'-'):'',
          go:function(){try{if(!isAct(g))open(g);setTimeout(function(){uiTab('AM');PT.goSub('AM','Register');amBndAll().forEach(function(q){q.open=q.id===x.id;});amPanel();},150);}catch(e){console.error(e);}},
          menu:function(){return[{t:'Buka di register',fn:function(){if(!isAct(g))open(g);uiTab('AM');amBndAll().forEach(function(q){q.open=q.id===x.id;});amPanel();}},{t:'Edit bentuk…',fn:function(){if(!isAct(g))open(g);setTimeout(function(){amEdShape(x.id);},200);}}];}};})});
        return{id:'fl.'+k,t:'RL '+fmt(g.top)+' – '+fmt(g.bot)+(ak?' (aktif)':''),ic:'flitch',tab:'BM',sub:'Dig block',b:bd,fold:1,kids:kids,
        foc:'rep',go:function(){try{open(g);setTimeout(function(){PT.goSub('BM','Dig block');},80);}catch(e){console.error(e);}},
        menu:function(){return[{t:'Buka flitch ini (Penampang 2D)',fn:function(){open(g);}},{t:'Register as-mined flitch ini',fn:function(){open(g);uiTab('AM');}},{sep:1},{t:'Hapus semua dig block di flitch ini…',danger:1,fn:function(){open(g);setTimeout(A('dbDelFlitch'),200);}}];}};});
      return{id:'fl',step:'5',st:st.fl,t:'Flitch Aktif',ic:'folder',fold:1,tab:'BM',sub:'Dig block',foc:'fl',b:m?flTxt():'',hint:'Tinggi flitch, RL atas / bawah, metode tonase, lalu Terapkan flitch (Penampang 2D)',
        menu:function(){return[{t:'Terapkan flitch (buka Penampang 2D)',fn:A('lyApply'),dis:!m}];},
        kids:[{id:'fl.2d',t:'Penampang 2D',ic:'s2d',tab:'Slice',chk:ok(function(){return !!VIEW2D;}),onChk:function(){toggle2D();}}].concat(fl.length?[{id:'fl.list',t:'Semua flitch ('+fl.length+')',ic:'flitch',b:fl.length,fold:1,kids:fl}]:[])};},'fl','Flitch Aktif');
    add(function(){return{id:'dig',step:'6',st:st.dig,t:'Dig Block',ic:'folder',fold:1,tab:'BM',sub:'Dig block',foc:'auto',b:s.dig?s.dig+' poligon':'',hint:'Dig block otomatis dari kelas kadar & tujuan material, atau digit manual (flitch aktif)',
        menu:function(){return[{t:'Buat dig block otomatis (flitch aktif)',fn:function(){A('dbAuto')();},dis:!m},{t:'Hapus semua dig block di flitch aktif…',danger:1,fn:A('dbDelFlitch'),dis:!s.dig}];},
        kids:[{id:'dig.auto',t:'Otomatis (kelas & tujuan)',ic:'poly',tab:'BM',sub:'Dig block',foc:'auto'},{id:'dig.man',t:'Digit manual (snap sudut blok)',ic:'digit',tab:'BM',sub:'Dig block',foc:'man'},
          {id:'dig.str',t:'Digitasi string bebas',ic:'string',tab:'Dig',b:ok(function(){return DG.S.length;},0)||''}]};},'dig','Dig Block');
    add(function(){return{id:'rep',step:'7',st:st.rep,t:'Laporan Grade × Tonnage',ic:'folder',fold:1,tab:'BM',sub:'Dig block',foc:'rep',hint:'Running grade & tonnage per dig block, multi-elemen',
        kids:[{id:'rep.run',t:'Running grade & tonnage',ic:'table',tab:'BM',sub:'Dig block',foc:'rep'},{id:'rep.el',t:'Elemen laporan & kadar tonase',ic:'el',tab:'BM',sub:'Dig block',foc:'el'},
          {id:'rep.unit',t:'Satuan elemen…',ic:'attr',go:A('elUnitDlg')},{id:'rep.csv',t:'Ringkasan tonase (CSV)',ic:'export',go:A('lyCsv')},{id:'rep.rl',t:'Ringkasan seluruh model per RL',ic:'report',go:A('bsOpen'),dim:!(window.bsOn&&bsOn()),hint:'Untuk .mdl besar yang dibuka lewat backend'}]};},'rep','Laporan');
    add(function(){return{id:'out',step:'8',st:st.out,t:'Layout & Ekspor Dig Plan',ic:'folder',fold:1,tab:'BM',sub:'Layout',hint:'Layout & plot PDF, export STR / DXF untuk Surpac',
        kids:[sub('out.ly','Layout & plot PDF','map','BM','Layout'),{id:'out.str',t:'Export STR / DXF (Surpac)',ic:'export',tab:'BM',sub:'Dig block',foc:'exp'},{id:'out.png',t:'Simpan gambar PNG',ic:'image',go:A('savePNG')}]};},'out','Layout');
    add(function(){return{id:'am',step:'9',st:st.am,t:'As-Mined',ic:'folder',fold:1,tab:'AM',sub:'Poligon',b:s.bnd?s.amc+'/'+s.bnd+' poligon':'',chk:ok(function(){return !!AM.show;}),onChk:function(v){AM.show=v;updatePlot();if(window.amPanel)amPanel();},hint:'Sesudah penambangan: sampel, pick-up, boundary aktual & hitung',
        kids:[sub('am.1','Setup register & kelas','gear','AM','Setup'),sub('am.2','Sampel (collar / assay)','table','AM','Sampel'),sub('am.3','Poligon, pick-up & lantai','poly','AM','Poligon'),sub('am.4','Parameter estimasi','attr','AM','Parameter')]};},'am','As-Mined');
    add(function(){return{id:'reg',step:'10',st:st.reg,t:'Register & Laporan As-Mined',ic:'folder',fold:1,tab:'AM',sub:'Register',hint:'Register poligon → Excel, layout & report rekonsiliasi',
        menu:function(){return[{t:'Kirim register ke Excel…',fn:A('amXlSend'),dis:typeof window.amXlSend!=='function'},{t:'Salin register ke Excel',fn:A('amRegCopy')},{t:'Register (CSV)',fn:A('amRegCsv')},{sep:1},{t:'Report rekonsiliasi (PDF)',fn:A('amPdf')},{t:'Rekonsiliasi (CSV)',fn:A('amCsv')},{t:'Block model as-mined (.mdl)',fn:A('amMdl')}];},
        kids:[sub('reg.1','Register poligon','report','AM','Register')].concat((function(){var G={},ord=[];ok(function(){return amBndAll();},[]).forEach(function(x){var k=(+x.top).toFixed(3)+'|'+(+x.bot).toFixed(3);if(!G[k]){G[k]={top:+x.top,bot:+x.bot,n:0,t:0,m:0};ord.push(k);}var I=ok(function(){return amInfoById(x.id);},null);G[k].n++;if(I&&I.calc&&x.on){G[k].t+=I.ton;if(isFinite(I.gA))G[k].m+=I.gA*I.ton;}});
            if(!ord.length)return[];ord.sort(function(a,b){return G[b].top-G[a].top;});var f=function(v){return String(+(+v).toFixed(3));};
            return[{id:'reg.fl',t:'Per flitch ('+ord.length+')',ic:'flitch',fold:1,kids:ord.map(function(k){var g=G[k];return{id:'reg.fl.'+k,t:'RL '+f(g.top)+' – '+f(g.bot),ic:'flitch',b:g.n+' pol · '+N(Math.round(g.t))+' t'+(g.t?' @ '+(g.m/g.t).toFixed(2):''),tab:'AM',sub:'Register',
              go:function(){lySet('fh',+(g.top-g.bot).toFixed(3));lyU().bot='';lySet('top',+g.top.toFixed(3));amApply();}};})}];})()).concat([sub('reg.2','Layout as-mined','map','AM','Layout'),{id:'reg.xl',t:'Kirim register ke Excel…',ic:'export',go:A('amXlSend'),dim:typeof window.amXlSend!=='function'},
          {id:'reg.pdf',t:'Report rekonsiliasi (PDF)',ic:'report',go:A('amPdf')},{id:'reg.mdl',t:'Block model as-mined (.mdl)',ic:'block',go:A('amMdl')}])};},'reg','Register');
    L.push({id:'set',t:'Pengaturan tampilan',ic:'folder',fold:1,kids:[{id:'set.s',t:'Sayatan',ic:'section',tab:'Slice'},{id:'set.o',t:'Overlay',ic:'eye',tab:'Overlay'},{id:'set.v',t:'Tampilan & performa',ic:'gear',tab:'View'}]});
    return L;}
  PT.install({app:'bm',nodes:nodes,nav:true,openDef:['bm','fl','dig','am'],
    onSelect:function(n){var f=n.foc||'';focus(f);setTimeout(function(){focus(f);},120);document.body.classList.toggle('pt-bmhd',n.tab==='BM'&&!/^bm(\.|$)/.test(n.id));},
    css:'#pBM>.uitabs,#amBody>.uitabs,#pAM .amflow{display:none!important}'+
      'body.pt-bmhd #pBM>:not(.uisec){display:none!important}'+
      [['fl'],['el'],['auto','rule','rep'],['man','rule','rep'],['exp'],['rep']].map(function(K){return '#dbBody[data-f='+K[0]+']>[data-seg]'+K.map(function(k){return ':not([data-seg='+k+'])';}).join('')+'{display:none!important}';}).join('')+
      '#dbBody[data-f=man]{display:flex;flex-direction:column}#dbBody[data-f=man]>[data-seg=man]{order:1}#dbBody[data-f=man]>[data-seg=rule]{order:2}#dbBody[data-f=man]>[data-seg=rep]{order:3}'});
})();
