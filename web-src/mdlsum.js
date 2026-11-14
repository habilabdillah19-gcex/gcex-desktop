/* ================= ringkasan SELURUH block model per RL (dihitung backend dari cache, model besar) ================= */
/* Dulu ringkasan ini HANYA untuk .mdl besar yang dibuka lewat backend, dan model lain ditolak dengan
   kotak pesan. Itu salah arah: yang justru paling mudah dihitung adalah model yang sudah ada di memori.
   Sekarang ada dua jalur dengan hasil yang sama persis (rumusnya ditiru baris demi baris dari
   backend bench_summary): backend untuk model yang hanya dimuat sepotong, dan JS lokal untuk model
   yang dimuat penuh. Tidak ada lagi syarat ukuran. */
/* 0.24.82: juga model .mdl besar yang dibaca LANGSUNG dengan filter pit/topografi (m.mdl.bigPath) -> ringkasan tetap atas seluruh file */
function bsBack(){var m=BX.m;return !!(m&&m.mdl&&(m.mdl.via==='backend'||m.mdl.bigPath)&&m.mdl.path&&window.gcexDesktop&&gcexDesktop.api);}
function bsOn(){return !!(BX.m&&(bsBack()||BX.m.n>0));}
function bsAttrs(){var m=BX.m,st={};
  if(bsBack()&&m.mdl&&m.mdl.st)(m.mdl.st||[]).forEach(function(a){if(a.type!==3)st[a.name]=1;});
  else Object.keys(m.num||{}).forEach(function(a){st[a]=1;});
  var L=(window.elList?elList():[BX.ui.attr]).filter(function(a){return st[a];});
  if(!L.length&&BX.ui.attr&&st[BX.ui.attr])L=[BX.ui.attr];
  return L;}
function bsOpen(){if(!(BX.m&&BX.m.n)){alert('Import block model dulu.');return;}var d=$('bsDlg');if(!d){d=document.createElement('div');d.id='bsDlg';d.className='bsdlg';document.body.appendChild(d);}d.style.display='flex';bsRender(BX.bsR&&BX.bsR.ver===BX.ver?BX.bsR:null);}
function bsClose(){var d=$('bsDlg');if(d)d.style.display='none';}
function bsPar(){var U=BX.ui,B=lyBench(),S=BX.bs||(BX.bs={});if(S.bench==null)S.bench=+(B[0]-B[1]).toFixed(3);if(S.ref==null)S.ref=B[1];if(S.cut==null)S.cut='';if(S.cutA==null)S.cutA=bsAttrs()[0]||'';return S;}
function bsRender(R){var d=$('bsDlg');if(!d)return;var S=bsPar(),m=BX.m,A=bsAttrs(),U=BX.ui;
  var h='<div class=bsbox><div class=bsh><b>Ringkasan seluruh model per RL</b><span>'+bxE((m.mdl&&m.mdl.file)||m.name)+' &middot; '+(bsBack()?(m.mdl.nRead||0).toLocaleString()+' blok (seluruh file, dihitung di backend)':m.n.toLocaleString()+' blok (seluruh model yang dimuat, dihitung di aplikasi)')+'</span><button class=x onclick="bsClose()">&times;</button></div>'+
    '<div class=bsp><label>Tinggi bench (m)<input type=number step=any value="'+S.bench+'" onchange="BX.bs.bench=+this.value"></label><label>RL acuan (batas bench)<input type=number step=any value="'+S.ref+'" onchange="BX.bs.ref=+this.value"></label>'+
    '<label>Cut-off<select onchange="BX.bs.cutA=this.value">'+A.map(function(a){return '<option'+(a===S.cutA?' selected':'')+'>'+bxE(a)+'</option>';}).join('')+'</select></label><label>&ge;<input type=number step=any placeholder="kosong = semua blok" value="'+bxE(S.cut)+'" onchange="BX.bs.cut=this.value"></label>'+
    '<label class=sw style="flex-direction:row;align-items:center"><input type=checkbox '+(S.hide0!==false?'checked':'')+' onchange="BX.bs.hide0=this.checked;bsRender(BX.bsR)">Sembunyikan bench 0 ton</label>'+bsConHtml(S)+'<button class=btn-pri onclick="bsRun()">Hitung</button>'+(R&&R.busy&&R.stop?'<button onclick="BX.bsStop=1">Batal</button>':'')+(R&&R.rows?'<button onclick="bsCsv()">&#8681; CSV</button>':'')+'</div>'+
    '<div class=hint>Elemen: <b>'+A.map(bxE).join(', ')+'</b> (daftar Elemen laporan; atribut kalkulasi IIF tidak ikut). SG: '+(U.sgCol?'kolom '+bxE(U.sgCol)+(', &le;0 / kosong = '+bxSGeff()+(bxSGkos()==='rep'?' (SG pengganti, cara GC-Ex)':' (seperti Surpac)')):'tetap '+U.sg)+'. Blok masuk bench menurut titik tengahnya (di atas RL bawah, tidak di atas RL atas), sama dengan metode Seperti Surpac.</div>';
  if(R&&R.err)h+='<div class=warn>&#9888; '+bxE(R.err)+'</div>'+(R.cache&&SA.mdlCacheHtml?SA.mdlCacheHtml():'');
  if(R&&R.busy)h+='<div class=hint>&#8987; '+(R.msg?bxE(R.msg):'Menghitung&hellip;')+'</div>';
  if(R&&R.rows&&R.con)h+='<div class=hint><b>'+bxE(R.con)+'</b></div>';
  if(R&&R.rows){var f=function(a,v){return v==null?'-':(window.elF?elF(a,v):v.toFixed(3));};
    h+='<div class=bstb><table class=pltb><tr><th>RL atas</th><th>RL bawah</th><th>Blok</th><th>Volume (m3)</th><th>Ton</th>'+A.map(function(a){return '<th>'+bxE(a)+'</th>';}).join('')+'</tr>'+
      R.rows.filter(function(r){return S.hide0===false||r.ton>0;}).map(function(r){return '<tr><td>'+lyFmt(r.top)+'</td><td>'+lyFmt(r.bot)+'</td><td>'+r.n.toLocaleString()+'</td><td>'+Math.round(r.vol).toLocaleString()+'</td><td>'+Math.round(r.ton).toLocaleString()+'</td>'+A.map(function(a){return '<td>'+f(a,r.grade[a])+'</td>';}).join('')+'</tr>';}).join('')+
      '<tr class=tot><td colspan=2>Total</td><td>'+R.total.n.toLocaleString()+'</td><td>'+Math.round(R.total.vol).toLocaleString()+'</td><td>'+Math.round(R.total.ton).toLocaleString()+'</td>'+A.map(function(a){return '<td>'+f(a,R.total.grade[a])+'</td>';}).join('')+'</tr></table></div>';}
  d.innerHTML=h+'</div>';BX.bsR=R||BX.bsR;}
/* ===== BM 0.24.84 (pemilik 14 Nov 2026: "adakah solusi lain untuk block model > 4 juta blok ... di Surpac tidak masalah") =====
   Hitungan dipisah dari tampilan: ringkasan per RL atas SELURUH file .mdl dengan batas "di dalam desain pit" dan / atau
   "di bawah topografi" dihitung sambil membaca file (streaming, blok tidak disimpan di memori), jadi 88 juta blok pun
   terlapor walau yang tampil di 3D hanya potongan. Aturan cara Surpac: blok masuk bila TITIK TENGAHNYA memenuhi batas
   (tidak di bawah permukaan desain pit dan di dalam cakupannya; tidak di atas topografi — sama dengan Reporting rpbm.js), seluruh volumenya dihitung. Permukaan =
   TIN yang sama dengan Reporting (TP.zf). Rumus bench / SG / kadar = bsLocal. */
function bsFile(){var f=SA.mdlFileLast,m=BX.m;return f&&m&&m.mdl&&m.mdl.file===f.name&&(!m.mdl.size||m.mdl.size===f.size)?f:null;}
function bsConAda(){var m=BX.m;return !!(m&&m.mdl&&m.mdl.file&&/\.mdl$/i.test(m.mdl.file)&&m.mdl.st);}
function bsConHtml(S){if(!bsConAda())return '';var hp=!!(window.OV&&OV.pitF&&OV.pitF.x&&OV.pitF.x.length),ht=!!(window.OV&&OV.topoF&&OV.topoF.x&&OV.topoF.x.length),f=bsFile();
  return '<label class=sw style="flex-direction:row;align-items:center"><input type=checkbox id=bsPit '+(S.pit&&hp?'checked':'')+(hp?'':' disabled')+' onchange="BX.bs.pit=this.checked">Hanya di dalam desain pit</label>'+
    '<label class=sw style="flex-direction:row;align-items:center"><input type=checkbox id=bsTopo '+(S.topo&&ht?'checked':'')+(ht?'':' disabled')+' onchange="BX.bs.topo=this.checked">Hanya di bawah topografi</label>'+
    (f?'':'<label class=sw style="flex-direction:row;align-items:center" title="Batas pit / topografi dihitung langsung dari file .mdl">File .mdl: <input type=file accept=".mdl" onchange="bsPilih(this)"></label>');}
function bsPilih(el){var f=el.files&&el.files[0],m=BX.m;if(!f)return;if(m.mdl.file!==f.name||(m.mdl.size&&m.mdl.size!==f.size)){alert('File tidak sama dengan block model yang dimuat ('+m.mdl.file+').');el.value='';return;}SA.mdlFileLast=f;bsRender(BX.bsR);}
function bsZf(role){var o=window.OV&&(role==='pit'?OV.pitF:OV.topoF);if(!o||!o.x||!o.x.length)return null;if(window.TP&&TP.zf)return TP.zf('ov:'+role);
  var o2=window.TIN&&TIN.rapat?TIN.rapat(o,2):o,t=window.TINZ&&TINZ.of?TINZ.of(o2,o2!==o&&o2.x.length>o.x.length):null;return t?function(x,y){var v=t.f(x,y);return v!=null&&isFinite(v)?v:null;}:null;}
async function bsStream(S,A,con){var m=BX.m,U=BX.ui,f=bsFile(),bench=+S.bench,ref=+S.ref,t0=Date.now();
  if(!f)throw new Error('Pilih file .mdl-nya dulu (kotak "File .mdl" di atas): batas pit / topografi dihitung langsung dari file.');
  if(!(bench>0))throw new Error('Tinggi bench harus > 0.');
  var H=await SA.mdlHead(f),nm=H.stored.map(function(a){return a.name;}),ix=function(a){var k=nm.indexOf(a);if(k<0||H.stored[k].type===3)throw new Error('Atribut bukan angka tersimpan di file: '+a+' (atribut kalkulasi / teks tidak bisa dipakai di sini).');return k;};
  var cut=String(S.cut).trim()===''?null:parseFloat(S.cut),cA=cut==null?null:S.cutA,kA=A.map(ix),kC=cA?ix(cA):-1,kS=U.sgCol?ix(U.sgCol):-1,na=A.length;
  var fp=con.pit?bsZf('pit'):null,ft=con.topo?bsZf('topo'):null;if(con.pit&&!fp)throw new Error('Desain pit belum ada.');if(con.topo&&!ft)throw new Error('Topografi belum ada.');
  var RT=H.root,VL=[],l;for(l=0;l<32;l++)VL.push(RT[0]*RT[1]*RT[2]*Math.pow(2,-3*l));
  var G={},key=[],ox=(typeof offX!=='undefined'&&isFinite(offX))?offX:0,oy=(typeof offY!=='undefined'&&isFinite(offY))?offY:0,j,nPit=0,nTopo=0;
  var scan=function(cx,cy,cz,Lv,VAL){
    if(kC>=0){var cv=VAL[kC][0];if(!(isFinite(cv)&&cv>=cut))return;}
    if(fp){var zp=fp(cx-ox,cy-oy);if(zp==null||!(cz>=zp)){nPit++;return;}}
    if(ft){var zt=ft(cx-ox,cy-oy);if(zt==null||!(cz<=zt)){nTopo++;return;}}
    var k=Math.ceil((cz-ref)/bench-1e-9)-1,o=G[k];
    if(!o){o=G[k]={n:0,vol:0,ton:0,s:new Float64Array(na),w:new Float64Array(na)};key.push(k);}
    var vol=VL[Lv],t=vol*bxSGv(kS>=0?VAL[kS][0]:undefined);
    o.n++;o.vol+=vol;o.ton+=t;
    for(var q=0;q<na;q++){var v=VAL[kA[q]][0];if(isFinite(v)&&v>-1e20){o.s[q]+=v*t;o.w[q]+=t;}}};
  BX.bsStop=0;var keep=A.concat(cA?[cA]:[]).concat(U.sgCol?[U.sgCol]:[]),last=0;
  var r=await SA.readMDLraw(f,function(pc,nk,nr){if(Date.now()-last<400)return;last=Date.now();var s=(Date.now()-t0)/1000;bsRender({busy:1,stop:1,msg:'Membaca seluruh file: '+pc+'% \u00b7 '+nr.toLocaleString()+' blok \u00b7 '+s.toFixed(0)+' dtk'});},{head:H,keep:keep,scan:scan,cancel:function(){return !!BX.bsStop;}});
  key.sort(function(a,b){return b-a;});
  var T={n:0,vol:0,ton:0,s:new Float64Array(na),w:new Float64Array(na)};
  var rows=key.map(function(k){var o=G[k],g={};for(j=0;j<na;j++){g[A[j]]=o.w[j]?o.s[j]/o.w[j]:null;T.s[j]+=o.s[j];T.w[j]+=o.w[j];}T.n+=o.n;T.vol+=o.vol;T.ton+=o.ton;return{bot:ref+k*bench,top:ref+(k+1)*bench,n:o.n,vol:o.vol,ton:o.ton,grade:g};});
  var tg={};for(j=0;j<na;j++)tg[A[j]]=T.w[j]?T.s[j]/T.w[j]:null;
  return{rows:rows,total:{n:T.n,vol:T.vol,ton:T.ton,grade:tg},attrs:A,par:{bench:bench,ref:ref,cut:cut,cutA:cA,pit:!!con.pit,topo:!!con.topo},n_model:r.nRead,file:f.name,
    con:'Batas: '+[con.pit?'di dalam desain pit':'',con.topo?'di bawah topografi':''].filter(Boolean).join(' + ')+' (titik tengah blok, cara Surpac) \u00b7 '+r.nRead.toLocaleString()+' blok dibaca dari file, '+T.n.toLocaleString()+' masuk \u00b7 '+((Date.now()-t0)/1000).toFixed(0)+' dtk'};}
async function bsRun(){var S=bsPar(),U=BX.ui,A=bsAttrs(),m=BX.m;bsRender({busy:1});
  if(bsConAda()&&(S.pit||S.topo)){try{var stN={};(m.mdl.st||[]).forEach(function(a){if(a.type!==3)stN[a.name]=1;});var As=A.filter(function(a){return stN[a];});if(!As.length)throw new Error('Tidak ada elemen laporan berupa atribut angka tersimpan di file (atribut kalkulasi tidak dipakai di sini).');var Rs=await bsStream(S,As,{pit:!!S.pit,topo:!!S.topo});Rs.ver=BX.ver;bsRender(Rs);}catch(e){bsRender({err:String(e&&e.message||e)});}return;}
  if(!bsBack()){setTimeout(function(){try{var R=bsLocal(S,A);R.ver=BX.ver;bsRender(R);}catch(e){bsRender({err:String(e&&e.message||e)});}},20);return;}
  /* cache seluruh file belum ada (model dibaca langsung): bangun sekali di folder cache, dengan progres */
  try{for(;;){var st=await gcexDesktop.api('/mdl/open',{path:m.mdl.path});if(st.state==='ready')break;if(st.state==='error')throw new Error(st.error||'cache gagal');
      bsRender({busy:1,msg:'Membangun cache seluruh model (sekali saja): '+Math.round(st.pct||0)+'% \u00b7 '+(+st.n||0).toLocaleString()+' blok'});await new Promise(function(r){setTimeout(r,800);});}}
  catch(e){bsRender({err:String(e&&e.message||e),cache:1});return;}
  try{var cut=String(S.cut).trim()===''?null:parseFloat(S.cut);var j=await gcexDesktop.api('/mdl/benches',{path:m.mdl.path,bench:+S.bench,ref:+S.ref,attrs:A,sg_col:U.sgCol||null,sg:+U.sg||2.6,sg_zero:bxSGeff()>0?'rep':'zero',sg_rep:bxSGeff()>0?bxSGeff():null,cut_attr:cut==null?null:S.cutA,cut:cut});
    j.attrs=A;j.par={bench:S.bench,ref:S.ref,cut:cut,cutA:S.cutA};j.ver=BX.ver;bsRender(j);}catch(e){bsRender({err:String(e&&e.message||e)});}}
/* Mirror persis backend `bench_summary` (backend/gcex_backend/mdl_io.py):
   - bench blok ditentukan titik TENGAHNYA: k = ceil((z-ref)/bench - 1e-9) - 1, jadi (bawah, atas],
     sama dengan metode "Seperti Surpac" di GC-Ex;
   - volume = sx*sy*sz per blok (di backend root/2^lv, yang nilainya sama);
   - SG memakai aturan GC-Ex yang sama (bxSGv), jadi kolom SG & penggantinya tidak bercabang dua;
   - kadar = rata-rata tertimbang TON, dan blok tanpa nilai tidak ikut penimbang atribut itu.
   Dibuat satu fungsi, bukan disalin ke pemanggilnya, supaya kalau rumusnya berubah ia berubah sekali. */
function bsLocal(S,A){var m=BX.m,U=BX.ui,bench=+S.bench,ref=+S.ref;
  if(!(bench>0))throw new Error('Tinggi bench harus > 0.');
  var cut=String(S.cut).trim()===''?null:parseFloat(S.cut),cA=cut==null?null:S.cutA;
  var miss=A.concat(cA?[cA]:[]).concat(U.sgCol?[U.sgCol]:[]).filter(function(a){return a&&!m.num[a];});
  if(miss.length)throw new Error('Atribut bukan angka / tidak ada di model: '+miss.join(', '));
  var SGa=U.sgCol?m.num[U.sgCol]:null,CA=cA?m.num[cA]:null,V=A.map(function(a){return m.num[a];}),na=A.length;
  var G={},key=[],i,j;
  for(i=0;i<m.n;i++){
    if(CA){var cv=CA[i];if(!(isFinite(cv)&&cv>=cut))continue;}
    var k=Math.ceil((m.z[i]-ref)/bench-1e-9)-1,o=G[k];
    if(!o){o=G[k]={n:0,vol:0,ton:0,s:new Float64Array(na),w:new Float64Array(na)};key.push(k);}
    var vol=m.sx[i]*m.sy[i]*m.sz[i],t=vol*bxSGv(SGa?SGa[i]:undefined);
    o.n++;o.vol+=vol;o.ton+=t;
    for(j=0;j<na;j++){var v=V[j][i];if(isFinite(v)&&v>-1e20){o.s[j]+=v*t;o.w[j]+=t;}}}
  key.sort(function(a,b){return b-a;});
  var T={n:0,vol:0,ton:0,s:new Float64Array(na),w:new Float64Array(na)};
  var rows=key.map(function(k){var o=G[k],g={};
    for(j=0;j<na;j++){g[A[j]]=o.w[j]?o.s[j]/o.w[j]:null;T.s[j]+=o.s[j];T.w[j]+=o.w[j];}
    T.n+=o.n;T.vol+=o.vol;T.ton+=o.ton;
    return{bot:ref+k*bench,top:ref+(k+1)*bench,n:o.n,vol:o.vol,ton:o.ton,grade:g};});
  var tg={};for(j=0;j<na;j++)tg[A[j]]=T.w[j]?T.s[j]/T.w[j]:null;
  return{rows:rows,total:{n:T.n,vol:T.vol,ton:T.ton,grade:tg},attrs:A,
         par:{bench:bench,ref:ref,cut:cut,cutA:cA},n_model:m.n,file:(m.mdl&&m.mdl.file)||m.name};}
function bsCsv(){var R=BX.bsR;if(!R||!R.rows)return;var A=R.attrs,o=[['RL_atas','RL_bawah','Blok','Volume_m3','Ton'].concat(A).join(',')];R.rows.forEach(function(r){o.push([r.top,r.bot,r.n,r.vol.toFixed(2),r.ton.toFixed(2)].concat(A.map(function(a){return r.grade[a]==null?'':r.grade[a].toFixed(5);})).join(','));});
  o.push(['TOTAL','',R.total.n,R.total.vol.toFixed(2),R.total.ton.toFixed(2)].concat(A.map(function(a){return R.total.grade[a]==null?'':R.total.grade[a].toFixed(5);})).join(','));
  o.push('');o.push('Parameter,bench '+R.par.bench+' m,acuan RL '+R.par.ref+(R.par.cut!=null?',cut-off '+R.par.cutA+' >= '+R.par.cut:',tanpa cut-off')+(R.par.pit?',di dalam desain pit':'')+(R.par.topo?',di bawah topografi':'')+',SG '+(BX.ui.sgCol?BX.ui.sgCol+' ('+('<=0 = '+bxSGeff())+')':'tetap '+BX.ui.sg));
  dgDl(o.join('\r\n')+'\r\n','Ringkasan_PerRL_'+String(BX.m.name).replace(/[^A-Za-z0-9_-]+/g,'_')+'.csv','text/csv');}
(function(){var _p=window.bxPanel;if(!_p)return;bxPanel=function(){var r=_p.apply(this,arguments);
  try{var b=$('bxBody');if(b&&bsOn()&&!b.querySelector('.bsbtn')){var st=$('bxStat'),d=document.createElement('div');d.className='bsbtn';
    d.innerHTML='<button style="width:100%;margin-top:6px" onclick="bsOpen()">&#128202; Ringkasan seluruh model per RL\u2026</button>'+
      '<div class=hint>'+(bsBack()?'Dihitung backend dari seluruh file .mdl \u2014 yang dimuat di tampilan hanya potongan '+bxE(BX.m.mdl.flt||'')+'.':'Dihitung dari seluruh blok yang dimuat.')+'</div>';
    if(st&&st.parentNode)st.parentNode.insertBefore(d,st.nextSibling);else b.appendChild(d);}}catch(e){console.error(e);}return r;};})();
