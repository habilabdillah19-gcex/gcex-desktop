/* ================= GC-Ex 0.20.3: DATABASE PROYEK (SQLite) di folder proyek =================
   Setiap kali proyek tersimpan ke folder proyek, isi proyek dikirim sebagai tabel ke backend GC-Ex (Python, sqlite3),
   yang memperbarui gcex_proyek.db, mencatat setiap perubahan baris di tabel `riwayat`, lalu file .db ditulis ke folder.
   Saat folder proyek dibuka, gcex_proyek.db yang ada dipakai sebagai dasar (riwayat lama tetap). Proyek lama tanpa .db:
   database dibuat otomatis pada penyimpanan pertama.
   Tabel - Block Model: digblock, asmined (+ view rekap_flitch). Drill Hole Ultimate: collar, survey, assay, geologi,
   domain, flag_domain, estimasi_run (+ view assay_domain). Bersama: meta, riwayat, sinkron.
   Hanya di aplikasi desktop (perlu backend); di browser biasa modul ini diam. */
(function(){
  var DSK=window.gcexDesktop;if(!DSK||!DSK.api||!DSK.apiBin||!window.FP||!window.SA)return;
  var PDB=window.PDB={sig:'',busy:false,pend:false,err:'',at:'',sum:null,key:'',loaded:''};var FN='gcex_proyek.db';
  var app=function(){return window.GCEX_APP||'bm';},r3=function(v){return isFinite(v)?Math.round(v*1000)/1000:null;};
  function key(){return FP.dir?(FP.dir.name+'|'+(SA.pname||'')):'';}
  function ver(){return window.GCEX_VER||'';}
  function user(){try{return (FP.user&&FP.user())||localStorage.getItem('gcex_user')||'';}catch(e){return '';}}
  function catCols(src){var o=[];try{(window.CAT||[]).forEach(function(c,ci){if(c&&c.src===src)o.push({ci:ci,k:c.k,n:c.name,d:c.d||[]});});}catch(e){}return o;}
  /* ---------- isi proyek -> tabel ---------- */
  PDB.tables=function(){var T=[];
    /* Block Model: dig block & as-mined per flitch */
    if(typeof window.flGroups==='function'&&typeof window.flCalc==='function'&&window.BX&&BX.m){var db=[],am=[],ox=window.offX||0,oy=window.offY||0;
      flGroups().forEach(function(g){var c=flCalc(g);if(c)c.it.forEach(function(o,i){var s=o.s;if(!s.id&&window.dbId)s.id=dbId();
          db.push([s.id||('db'+g.k+'_'+i),g.top,g.bot,o.name,o.d||'',o.dest||'',r3(o.area),r3(o.t),r3(o.g),(o.af||[]).join('; '),s.pts.map(function(q){return[r3(q[0]+ox),r3(q[1]+oy)];})]);});
        g.am.forEach(function(x){var I=null;try{I=amInfoById(x.id);}catch(e){}am.push([x.id,g.top,g.bot,(I&&I.code)||'',x.name||'',x.on!==false?1:0,I&&I.calc?1:0,I?r3(I.bcm):null,I?r3(I.ton):null,I?r3(I.gA):null,(x.pts||[]).map(function(q){return[r3(+q[0]),r3(+q[1])];})]);});});
      T.push({name:'digblock',key:['id'],cols:['id','rl_atas','rl_bawah','nama','material','tujuan','luas_m2','ton','kadar','flag','titik_xy'],rows:db});
      T.push({name:'asmined',key:['id'],cols:['id','rl_atas','rl_bawah','kode','nama','aktif','dihitung','bcm','ton','kadar','titik_xy'],rows:am});}
    /* Drill Hole Ultimate: database bor */
    if(app()==='dh'&&window.collars&&collars.length&&window.assays&&window.elements){
      T.push({name:'collar',key:['hole_id'],cols:['hole_id','easting','northing','rl','kedalaman'],rows:collars.map(function(c){return[c[0],r3(c[1]),r3(c[2]),r3(c[3]),r3(c[4])];})});
      if(window.surveys)T.push({name:'survey',key:['hole_id','kedalaman'],cols:['hole_id','kedalaman','dip','azimuth'],rows:surveys.map(function(s){return[s[0],r3(s[1]),r3(s[2]),r3(s[3])];})});
      var AC=catCols('a');T.push({name:'assay',key:['hole_id','dari','sampai'],cols:['hole_id','dari','sampai','sample_id'].concat(elements,AC.map(function(c){return c.n;})),
        rows:assays.map(function(a){var v=a[4]||[],cc=a[5]||[];return[a[0],r3(a[1]),r3(a[2]),a[3]==null?'':String(a[3])].concat(elements.map(function(_,i){return v[i]==null?null:v[i];}),AC.map(function(c){var k=cc[c.k];return k==null||k<0?null:(c.d[k]!=null?c.d[k]:k);}));})});
      var GC=catCols('g'),GR=window.geoRows||[];if(GR.length&&GC.length)T.push({name:'geologi',key:['hole_id','dari','sampai'],cols:['hole_id','dari','sampai'].concat(GC.map(function(c){return c.n;})),
        rows:GR.map(function(g){var cc=g[3]||[];return[g[0],r3(g[1]),r3(g[2])].concat(GC.map(function(c){var k=cc[c.k];return k==null||k<0?null:(c.d[k]!=null?c.d[k]:k);}));})});}
    /* Drill Hole Ultimate: domain & flag interval, run estimasi */
    if(app()==='dh'&&window.GM&&GM.doms){var nm={};GM.doms.forEach(function(d){nm[d.id]=d.name;});
      T.push({name:'domain',key:['id'],cols:['id','nama','induk','selubung_dari','warna'],rows:GM.doms.map(function(d){return[d.id,d.name,d.par?(nm[d.par]||d.par):'',d.env?(nm[d.env]||d.env):'',d.col||''];})});
      var F=[];Object.keys(GM.flags||{}).forEach(function(h){(GM.flags[h]||[]).forEach(function(f){F.push([h,r3(f[0]),r3(f[1]),nm[f[2]]||f[2]]);});});
      T.push({name:'flag_domain',key:['hole_id','dari','sampai'],cols:['hole_id','dari','sampai','domain'],rows:F});
      try{var R=(window.ME&&ME.store&&ME.store.runs)||[];T.push({name:'estimasi_run',key:['id'],cols:['id','domain','tanggal','pengguna','blok_di_solid','blok_diestimasi','blok_tambahan','hole_berubah','mode','data'],
        rows:R.map(function(q){return[q.id,nm[q.domId]||q.domId||'',q.date||'',q.user||'',q.nIn==null?null:q.nIn,q.nAff==null?null:q.nAff,q.nAddC==null?null:q.nAddC,q.nHole==null?null:q.nHole,q.first?'pertama':q.force?'semua blok':'koreksi',q];})});}catch(e){}}
    return T;};
  /* tanda tangan murah: hanya sinkron bila isi berubah */
  function sigOf(T){var h=0,s,i;for(var t=0;t<T.length;t++){var R=T[t].rows;s=T[t].name+R.length+T[t].cols.join();for(i=0;i<s.length;i++)h=(h*31+s.charCodeAt(i))|0;
      for(i=0;i<R.length;i++){var x=JSON.stringify(R[i]);for(var j=0;j<x.length;j++)h=(h*31+x.charCodeAt(j))|0;}}return h+':'+T.reduce(function(a,t){return a+t.rows.length;},0);}
  function b64(buf){var u=new Uint8Array(buf),s='',C=0x8000;for(var i=0;i<u.length;i+=C)s+=String.fromCharCode.apply(null,u.subarray(i,i+C));return btoa(s);}
  /* ---------- muat .db dari folder proyek ---------- */
  PDB.load=async function(){var k=key();if(!k||PDB.loaded===k)return;PDB.loaded=k;PDB.sig='';
    try{var fh=null;try{fh=await FP.dir.getFileHandle(FN);}catch(e){fh=null;}if(!fh)return;var buf=await (await fh.getFile()).arrayBuffer();
      var r=await DSK.api('/proj/db/load',{key:k,db_b64:b64(buf)});if(r&&r.ok===false)PDB.err=r.error||'';}catch(e){PDB.err=String(e.message||e);console.warn('[GC-Ex] database proyek:',e);}};
  /* ---------- sinkron & tulis ke folder ---------- */
  PDB.sync=async function(force){if(!FP.dir||FP.ro||FP.conf||!SA.pname)return false;if(PDB.busy){PDB.pend=true;return false;}PDB.busy=true;var ok=false;
    try{await PDB.load();var T=PDB.tables();if(!T.length){PDB.busy=false;return false;}var sg=sigOf(T);if(!force&&sg===PDB.sig){PDB.busy=false;return true;}
      var r=await DSK.apiBin('/proj/db/sync',{key:key(),app:app(),user:user(),version:ver(),tables:T});
      var info={};try{info=JSON.parse(r.headers['x-gcex-sync']||'{}');}catch(e){}
      await FP.write(FP.dir,FN,new Blob([r.buf],{type:'application/vnd.sqlite3'}));
      PDB.sig=sg;PDB.sum=info.tabel||null;PDB.at=info.waktu||new Date().toLocaleString();PDB.err='';ok=true;
    }catch(e){PDB.err=String(e&&e.message||e);console.warn('[GC-Ex] database proyek:',e);}
    PDB.busy=false;try{if(window.PT&&PT.render)PT.render(true);}catch(e){}
    if(PDB.pend){PDB.pend=false;setTimeout(function(){PDB.sync();},500);}return ok;};
  var tmr=0;PDB.soon=function(ms){clearTimeout(tmr);tmr=setTimeout(function(){PDB.sync();},ms||2500);};
  if(typeof FP.save==='function'){var _sv=FP.save;FP.save=async function(){var r=await _sv.apply(this,arguments);if(r)PDB.soon();return r;};}
  if(typeof FP.afterConnect==='function'){var _ac=FP.afterConnect;FP.afterConnect=async function(){var r=await _ac.apply(this,arguments);PDB.loaded='';PDB.sig='';PDB.soon(4000);return r;};}
  /* ---------- info & node Project Tree ---------- */
  PDB.show=async function(){var k=key(),I=null;if(!k){alert('Database proyek aktif bila proyek disimpan di folder proyek (Proyek > Folder proyek).');return;}
    try{if(!PDB.at)await PDB.sync(true);I=await DSK.api('/proj/db/info',{key:k});}catch(e){alert('Database proyek: '+(e.message||e));return;}
    var esc=function(s){return String(s==null?'':s).replace(/[&<>"]/g,function(c){return{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c];});};
    var w=document.getElementById('pdbBox');if(!w){w=document.createElement('div');w.id='pdbBox';document.body.appendChild(w);}
    var t=I&&I.tabel?Object.keys(I.tabel).map(function(n){return '<tr><td>'+esc(n)+'</td><td style="text-align:right">'+Number(I.tabel[n]).toLocaleString()+'</td></tr>';}).join(''):'';
    var h=I&&I.riwayat?I.riwayat.map(function(q){return '<tr><td>'+esc(q.waktu)+'</td><td>'+esc(q.pengguna)+'</td><td>'+esc(q.tabel)+'</td><td>'+esc(q.aksi)+'</td><td>'+esc(String(q.kunci).slice(0,40))+'</td></tr>';}).join(''):'';
    w.innerHTML='<div class="pdbIn"><div class="pdbH"><b>Database proyek (SQLite)</b><button onclick="document.getElementById(\'pdbBox\').style.display=\'none\'">&times;</button></div>'+
      '<div class="pdbB"><p>File <code>'+FN+'</code> di folder proyek <b>'+esc(FP.dir.name)+'</b>'+(I&&I.bytes?' &middot; '+(I.bytes/1048576).toFixed(2)+' MB':'')+(PDB.at?' &middot; sinkron terakhir '+esc(PDB.at):'')+(PDB.err?'<br><span style="color:var(--dn)">&#9888; '+esc(PDB.err)+'</span>':'')+'</p>'+
      '<div class="pdbG"><div><h5>Tabel</h5><table>'+t+'</table>'+(I&&I.view&&I.view.length?'<h5>View</h5><div>'+I.view.map(esc).join(', ')+'</div>':'')+'</div>'+
      '<div><h5>Riwayat perubahan terakhir</h5><table class="pdbR"><tr><th>Waktu</th><th>Pengguna</th><th>Tabel</th><th>Aksi</th><th>Kunci</th></tr>'+h+'</table></div></div>'+
      '<p class="pdbHint">Buka file .db dengan <b>DB Browser for SQLite</b>, Excel (ODBC), QGIS atau Python. Tabel <code>riwayat</code> mencatat setiap tambah / ubah / hapus beserta data lama; <code>sinkron</code> mencatat siapa menyimpan kapan dengan versi aplikasi mana.</p>'+
      '<div class="pdbF"><button onclick="PDB.sync(true).then(function(){PDB.show();})">&#8635; Sinkronkan sekarang</button><button onclick="document.getElementById(\'pdbBox\').style.display=\'none\'">Tutup</button></div></div></div>';
    w.style.display='flex';};
  var st=document.createElement('style');st.textContent='#pdbBox{position:fixed;inset:0;z-index:30000;background:rgba(15,20,30,.45);display:none;align-items:center;justify-content:center}'+
    '#pdbBox .pdbIn{width:min(900px,94vw);max-height:88vh;display:flex;flex-direction:column;background:var(--sf,#fff);color:var(--tx);border-radius:8px;box-shadow:0 12px 40px rgba(0,0,0,.35);overflow:hidden}'+
    '#pdbBox .pdbH{display:flex;justify-content:space-between;align-items:center;padding:10px 14px;background:var(--top,#1b2333);color:var(--toptx,#fff)}#pdbBox .pdbH button{background:none;border:0;color:inherit;font-size:20px;cursor:pointer}'+
    '#pdbBox .pdbB{padding:10px 14px;overflow:auto;font-size:12.5px}#pdbBox .pdbG{display:grid;grid-template-columns:220px 1fr;gap:14px}#pdbBox h5{margin:6px 0 4px;color:var(--pr)}'+
    '#pdbBox table{border-collapse:collapse;width:100%}#pdbBox td,#pdbBox th{border-bottom:1px solid var(--bd);padding:2px 4px;text-align:left;font-size:12px}#pdbBox .pdbHint{color:var(--mu)}#pdbBox .pdbF{display:flex;gap:8px;justify-content:flex-end;margin-top:8px}';
  document.head.appendChild(st);
  var tries=0,iv=setInterval(function(){if(++tries>600){clearInterval(iv);return;}if(!(window.PT&&PT.def&&PT.def.nodes))return;clearInterval(iv);var _n=PT.def.nodes;
    PT.def.nodes=function(){var L=_n.apply(this,arguments);try{var p=null;for(var i=0;i<L.length;i++)if(L[i]&&L[i].id==='proj'){p=L[i];break;}
        if(p){var on=!!FP.dir,sm=PDB.sum,n=sm?Object.keys(sm).reduce(function(a,k){return a+(sm[k].baris||0);},0):0;
          p.kids=(p.kids||[]).concat([{id:'proj.db',t:'Database proyek (SQLite)',ic:'db',dim:!on,b:!on?'perlu folder proyek':PDB.err?'⚠ galat':PDB.at?n.toLocaleString('id-ID')+' baris':'belum sinkron',
            hint:'gcex_proyek.db di folder proyek: tabel isi proyek + riwayat setiap perubahan',go:function(){PDB.show();},menu:function(){return[{t:'Sinkronkan sekarang',fn:function(){PDB.sync(true);},dis:!on},{t:'Lihat isi & riwayat…',fn:function(){PDB.show();},dis:!on}];}}]);}}catch(e){console.error(e);}return L;};
    try{PT.render(true);}catch(e){}},1000);
})();
