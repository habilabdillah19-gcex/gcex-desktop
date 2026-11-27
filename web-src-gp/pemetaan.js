'use strict';
/* Geo Pocket — Mode Pemetaan (F8): kategori pemetaan lapangan di peta 2D.
   Skema kategori dan atribut mengikuti Studio Pemetaan Ore Works, dengan nama kolom pendek (≤ 10 huruf) agar aman di DBF / MapInfo. */
const MK={
 vein:{n:'Vein',k:'line',key:'1',col:'#D97706',lw:2.5,cols:['LAYER','JENIS','TEBAL_M','DIP','DIPDIR','MINERAL','TEKSTUR','KET'],en:{JENIS:['Vein','Veinlet','Stockwork','Breksi hidrotermal','Vein zone']},lab:'LAYER',tip:'Klik titik-titik sepanjang singkapan vein; Enter / klik ganda = selesai.'},
 kon:{n:'Kontak',k:'line',key:'2',col:'#1C2733',lw:1.6,cols:['LAYER','DARI','KE','JENIS','KET'],en:{JENIS:['Tajam','Gradasional','Sesar','Intrusif','Tidak pasti']},tip:'Klik titik-titik sepanjang kontak; Enter = selesai. "Tidak pasti" digambar putus-putus.'},
 sl:{n:'Struktur',k:'line',key:'3',col:'#C2413B',lw:2,cols:['LAYER','JENIS','DIP','DIPDIR','KET'],en:{JENIS:['Sesar','Sesar dugaan','Kekar','Shear zone','Breksi sesar','Lainnya']},lab:'JENIS',tip:'Klik titik-titik jejak struktur; Enter = selesai. "Sesar dugaan" digambar putus-putus.'},
 pol:{n:'Poligon',k:'poly',key:'4',col:'#7B1FA2',lw:1.5,fill:0.2,cols:['TIPE','KODE','KET'],en:{TIPE:['Litologi','Alterasi','Mineralisasi','Oksidasi','Lainnya']},lab:'KODE',tip:'Poligon litologi / alterasi: klik sudut-sudutnya, Enter = tutup. Luas tampil langsung.'},
 grab:{n:'Grab',k:'point',key:'5',col:'#2B5F9E',sym:'sq',cols:['LAYER','SAMPLE_ID','TANGGAL','LITO','ALTERASI','AU_PPM','KET'],en:{},lab:'SAMPLE_ID',tip:'Satu klik = satu sampel grab. Sample_ID bertambah otomatis.'},
 sd:{n:'Strike/dip',k:'sd',key:'6',col:'#3B2A20',sym:'sd',cols:['JENIS','STRIKE','DIP','DIPDIR','KET'],en:{JENIS:['Bedding','Foliasi','Kekar','Sesar','Shear zone','Vein','Veinlet','Kontak','Lineasi / striasi','Lainnya']},tip:'Klik lokasi lalu seret ke arah strike (aturan tangan kanan: dip ke kanan arah seret). Klik tanpa seret = pakai Strike di bilah.'},
 obs:{n:'Observasi',k:'point',key:'7',col:'#00897B',sym:'tri',cols:['LAYER','STASIUN','TANGGAL','FOTO','KET'],en:{},lab:'STASIUN',tip:'Satu klik = satu stasiun observasi. Nomor stasiun bertambah otomatis.'}};
const MP={on:false,cat:null,layer:'',jenis:{},dip:'',strike:'',rl:'dem',rlv:0,pick:null,fold:null,seq:{grab:1,obs:1}};
const mpCats=()=>Object.keys(MK);
const mpCol=(g,c)=>g.meta.cols?g.meta.cols.indexOf(c):-1;
const mpToday=()=>new Date().toISOString().slice(0,10);

function mpFolder(){if(MP.fold&&fById(MP.fold))return MP.fold;const f=S.folders.find(x=>x.name==='Pemetaan'&&!x.parent)||newFolder('Pemetaan',null,true);MP.fold=f.id;return f.id;}
function mpStyle(g){const d=MK[g.mapc],s=M2.sty(g);s.lw=d.lw||1.5;s.fill=d.fill||0;s.pt=d.sym==='sd'?6:d.sym?5:4;s.sym=d.sym||null;s.label=d.lab?d.cols.indexOf(d.lab):-1;s.dashBy=d.cols.indexOf('JENIS');if(d.cols.indexOf('TIPE')>=0&&g.mapc==='pol')s.dashBy=-1;}
function mpLayer(cat,create){let g=S.geoms.find(x=>x.mapc===cat);if(g||create===false)return g||null;const d=MK[cat];
 g=GC.mk({name:'Pemetaan_'+d.n.replace(/[^A-Za-z]/g,''),src:'map',meta:{cols:d.cols.slice(),enums:JSON.parse(JSON.stringify(d.en))}});g.mapc=cat;g.color=d.col;g.base='Pemetaan_'+d.n.replace(/[^A-Za-z]/g,'');g.file='(pemetaan)';g.fold=mpFolder();mpStyle(g);S.geoms.unshift(g);return g;}
function mpPickLayer(){const g=MP.pick&&gById(MP.pick);return g&&isVec(g)&&g.visible?g:null;}
function mpNearPick(x,y,maxd){const g=mpPickLayer();if(!g)return null;const V=g.V;let b=null,bd=maxd;const n=g.PT.length?g.PT.length:V.length/3;
 for(let k=0;k<n;k++){const i=g.PT.length?g.PT[k]:k,d=Math.hypot(V[3*i]-x,V[3*i+1]-y);if(d<bd){bd=d;b=i;}}return b===null?null:[V[3*b],V[3*b+1],V[3*b+2]];}
function mpZ(p){if(MP.rl==='tetap')return [p[0],p[1],+MP.rlv||0];if(MP.rl==='pickup'){const q=mpNearPick(p[0],p[1],8);if(q)return [p[0],p[1],q[2]];}return p;}
function mpSeq(cat){const g=mpLayer(cat,false),c=g?mpCol(g,cat==='grab'?'SAMPLE_ID':'STASIUN'):-1;let n=MP.seq[cat]||1;
 if(g&&c>=0){const used=new Set(g.PA.map(a=>a&&a[c]));while(used.has((cat==='grab'?'GR-':'ST-')+String(n).padStart(3,'0')))n++;}return n;}
function mpDigit(kind,pts,extra){const cat=MP.cat,d=MK[cat];if(!d)return false;
 const ok=d.k===kind||(d.k==='sd'&&kind==='sd');if(!ok){msg('Alat '+d.n+' tidak cocok dengan digitasi '+kind+'.','w');return true;}
 const g=mpLayer(cat),a=d.cols.map(()=>''),set=(c,v)=>{const i=d.cols.indexOf(c);if(i>=0)a[i]=v;};pushUndo(g,'pemetaan '+d.n);
 if(MP.layer)set('LAYER',MP.layer);const j=d.en.JENIS?'JENIS':d.en.TIPE?'TIPE':null;if(j)set(j,MP.jenis[cat]||(d.en[j]||[])[0]||'');
 if(cat==='vein'||cat==='sl'||cat==='sd'){if(MP.dip!=='')set('DIP',String(MP.dip));}
 if(cat==='grab'||cat==='obs'){const n=mpSeq(cat);set(cat==='grab'?'SAMPLE_ID':'STASIUN',(cat==='grab'?'GR-':'ST-')+String(n).padStart(3,'0'));MP.seq[cat]=n+1;set('TANGGAL',mpToday());}
 let st=null;if(cat==='sd'){st=extra&&extra.az!=null?extra.az:(MP.strike!==''?+MP.strike:null);if(st===null){msg('Strike/dip: seret ke arah strike, atau isi Strike di bilah Pemetaan.','w');S.undo.pop();return true;}
  st=((Math.round(st)%360)+360)%360;set('STRIKE',String(st));set('DIPDIR',String((st+90)%360));}
 if(cat==='vein'||cat==='sl'){if(MP.dip!==''&&extra&&extra.dd!=null)set('DIPDIR',String(extra.dd));}
 const P=pts.map(mpZ);let f;
 if(d.k==='line'||d.k==='poly'){const i=GC.addPoly(g,P,d.k==='poly',a);f={g:g,type:'pl',i:i};
  msg(d.n+' '+(i+1)+': '+(d.k==='poly'?'luas '+M2.fmtArea(GC.polyArea(g.V,g.P[i].idx)):'panjang '+M2.fmtLen(GC.polyLen(g.V,g.P[i].idx,false)))+'. Lengkapi atributnya di panel Properti.');}
 else{const i=GC.addPoint(g,P[0],a);f={g:g,type:'pt',i:i};msg(d.n+(cat==='sd'?' '+a[1]+'/'+(a[2]||'?')+' ('+a[0]+')':' '+(a[1]||''))+' ditambahkan.');}
 g.visible=true;S.sel=g.id;S.selF=f;refreshAll();M2.draw();return true;}

function mpTool(cat){if(!MP.on)mpToggle(true);const d=MK[cat];setTool(d.k==='sd'?'sd':d.k);MP.cat=cat;$$('#tb2 [data-tool]').forEach(b=>b.classList.remove('on'));renderMapBar();$('#tip').textContent=d.n+': '+d.tip;$('#tip').style.display='';}
function mpToggle(on){MP.on=on===undefined?!MP.on:on;if(!MP.on){MP.cat=null;if(['poly','line','point','sd'].indexOf(M2.tool())>=0)setTool('pan');}
 else{if(S.tab!=='2d')showTab('2d');if(!MP.pick){const c=S.geoms.filter(g=>isVec(g)&&g.visible&&!g.mapc&&(g.PT.length||(!g.P.length&&!g.F.length&&g.V.length)));const p=c.find(g=>/pick|pu_|survey|ukur/i.test(g.name+' '+(g.file||'')))||null;if(p)MP.pick=p.id;}
  msg('Mode Pemetaan aktif: pilih kategori (tombol 1–7), lalu digit di peta. Fitur masuk folder "Pemetaan".');}
 renderMapBar();renderProps();}
function renderMapBar(){const b=$('#mapbar');if(!b)return;b.style.display=MP.on&&S.tab==='2d'?'':'none';$('#tip').classList.toggle('low',MP.on);if(!MP.on)return;
 const cat=MP.cat,d=cat&&MK[cat],jk=d?(d.en.JENIS?'JENIS':d.en.TIPE?'TIPE':null):null,pk=S.geoms.filter(g=>isVec(g)&&!g.mapc&&g.V.length&&!g.F.length);
 let h='<span class="tg mpcat">'+mpCats().map(c=>'<button data-mc="'+c+'" class="'+(c===cat?'on':'')+'" title="'+MK[c].n+' ('+MK[c].key+')"><i class="mpsw" style="background:'+MK[c].col+'"></i>'+MK[c].n+'<small>'+MK[c].key+'</small></button>').join('')+'</span>';
 h+='<span class="tg mpf">';
 if(jk)h+='<label>'+(jk==='TIPE'?'Tipe':'Jenis')+' <select id="mpj">'+d.en[jk].map(v=>'<option'+((MP.jenis[cat]||d.en[jk][0])===v?' selected':'')+'>'+esc(v)+'</option>').join('')+'</select></label>';
 if(d&&(cat==='vein'||cat==='sl'||cat==='sd'))h+='<label>Dip <input id="mpdip" type="number" min="0" max="90" step="1" value="'+esc(MP.dip)+'" style="width:52px"></label>';
 if(cat==='sd')h+='<label>Strike <input id="mpst" type="number" min="0" max="360" step="1" value="'+esc(MP.strike)+'" style="width:56px" title="Dipakai bila klik tanpa seret"></label>';
 if(d&&d.cols.indexOf('LAYER')>=0)h+='<label>Layer <input id="mplay" type="text" value="'+esc(MP.layer)+'" placeholder="mis. VN_A" style="width:90px"></label>';
 h+='<label>RL <select id="mprl"><option value="dem"'+(MP.rl==='dem'?' selected':'')+'>Dari DEM</option><option value="pickup"'+(MP.rl==='pickup'?' selected':'')+'>Pick-up terdekat</option><option value="tetap"'+(MP.rl==='tetap'?' selected':'')+'>Tetap</option></select></label>'+(MP.rl==='tetap'?'<input id="mprlv" type="number" step="any" value="'+esc(MP.rlv)+'" style="width:64px">':'');
 h+='<label>Pick-up <select id="mppk"><option value="">(tidak ada)</option>'+pk.map(g=>'<option value="'+g.id+'"'+(g.id===MP.pick?' selected':'')+'>'+esc(g.name)+'</option>').join('')+'</select></label>';
 h+='</span><span class="tg"><button id="mpexp" title="Ekspor semua kategori sekaligus">Ekspor set…</button><button id="mpoff" title="Tutup Mode Pemetaan (F8)">✕</button></span>';
 b.innerHTML=h;const on=(id,ev,fn)=>{const x=document.getElementById(id);if(x)x[ev]=fn;};
 $$('[data-mc]',b).forEach(x=>x.onclick=()=>mpTool(x.dataset.mc));
 on('mpj','onchange',(e)=>{MP.jenis[cat]=e.target.value;});on('mpdip','onchange',(e)=>{MP.dip=e.target.value;});on('mpst','onchange',(e)=>{MP.strike=e.target.value;});on('mplay','onchange',(e)=>{MP.layer=e.target.value.trim();});
 on('mprl','onchange',(e)=>{MP.rl=e.target.value;if(MP.rl==='pickup'&&!mpPickLayer())msg('Pilih lapisan pick-up dulu; tanpa itu RL diambil dari DEM.','w');renderMapBar();});on('mprlv','onchange',(e)=>{MP.rlv=+e.target.value||0;});
 on('mppk','onchange',(e)=>{MP.pick=+e.target.value||null;M2.draw();});on('mpexp','onclick',dlgMapExport);on('mpoff','onclick',()=>mpToggle(false));}

/* daftar fitur per kategori (panel Properti) */
function mpFeatName(g,t,i){const a=t==='pl'?g.P[i].attr:g.PA[i],c=(n)=>{const k=mpCol(g,n);return k>=0&&a?a[k]:'';};
 switch(g.mapc){case 'vein':return (c('LAYER')||'Vein '+(i+1))+(c('JENIS')?' · '+c('JENIS'):'');case 'kon':return (c('DARI')&&c('KE')?c('DARI')+' / '+c('KE'):'Kontak '+(i+1))+(c('JENIS')?' · '+c('JENIS'):'');
  case 'sl':return (c('JENIS')||'Struktur')+' '+(i+1)+(c('DIP')?' · '+c('DIP')+'°':'');case 'pol':return (c('KODE')||'Poligon '+(i+1))+' · '+M2.fmtArea(GC.polyArea(g.V,g.P[i].idx));
  case 'grab':return (c('SAMPLE_ID')||'Grab '+(i+1))+(c('AU_PPM')?' · Au '+c('AU_PPM'):'');case 'sd':return (c('JENIS')||'S/D')+' '+(c('STRIKE')||'?')+'/'+(c('DIP')||'?');case 'obs':return c('STASIUN')||'Obs '+(i+1);}return '#'+(i+1);}
function mpListHtml(){const L=mpCats().map(c=>mpLayer(c,false)).filter(Boolean);
 let h='<div class="mpl">';if(!L.length)h+='<p class="hint">Belum ada fitur. Pilih kategori di bilah Pemetaan lalu digit di peta.</p>';
 for(const g of L){const items=g.mapc&&MK[g.mapc].k==='line'||g.mapc==='pol'?g.P.map((p,i)=>['pl',i]):g.PT.length?Array.from(g.PT,(x,i)=>['pt',i]):[];
  h+='<div class="mph"><i class="mpsw" style="background:'+g.color+'"></i>'+esc(MK[g.mapc].n)+'<span>'+items.length+'</span></div>';
  h+=items.slice(0,300).map(([t,i])=>{const on=S.selF&&S.selF.g===g&&S.selF.type===t&&S.selF.i===i;return '<div class="mpi'+(on?' on':'')+'" data-mpg="'+g.id+'" data-mpt="'+t+'" data-mpi="'+i+'">'+esc(mpFeatName(g,t,i))+'</div>';}).join('')+(items.length>300?'<p class="hint">… '+(items.length-300)+' fitur lain</p>':'');}
 return h+'</div>';}
function mpBindList(P){$$('[data-mpi]',P).forEach(x=>x.onclick=()=>{const g=gById(+x.dataset.mpg),t=x.dataset.mpt,i=+x.dataset.mpi;if(!g)return;S.selF={g:g,type:t,i:i};S.sel=g.id;
  const V=g.V,idx=t==='pl'?g.P[i].idx:[g.PT[i]];let sx=0,sy=0;for(const k of idx){sx+=V[3*k];sy+=V[3*k+1];}M2.view.cx=sx/idx.length;M2.view.cy=sy/idx.length;renderTree();renderProps();M2.draw();});}

/* ekspor satu set pemetaan */
function mpCSV(gs,o){const d=o.dec,O=[];for(const g of gs){const cols=g.meta.cols,head=['X','Y','Z','KATEGORI','FITUR','URUT'].concat(cols);O.push(head.join(','));
 const q=(v)=>{v=v==null?'':String(v);return /[",\n]/.test(v)?'"'+v.replace(/"/g,'""')+'"':v;},V=g.V,f=(v)=>(+v).toFixed(d);
 g.P.forEach((p,n)=>{const idx=p.closed?p.idx.concat([p.idx[0]]):p.idx;idx.forEach((i,k)=>O.push([f(V[3*i]),f(V[3*i+1]),f(V[3*i+2]),MK[g.mapc].n,n+1,k+1].concat((p.attr||[]).map(q)).join(',')));});
 for(let k=0;k<g.PT.length;k++){const i=g.PT[k];O.push([f(V[3*i]),f(V[3*i+1]),f(V[3*i+2]),MK[g.mapc].n,k+1,1].concat((g.PA[k]||[]).map(q)).join(','));}
 return {name:g.base+'.csv',data:O.join('\n')+'\n'};}}
function mpExport(fmt){const gs=mpCats().map(c=>mpLayer(c,false)).filter(g=>g&&(g.P.length||g.PT.length));if(!gs.length){msg('Belum ada fitur pemetaan untuk diekspor.','w');return;}
 const o={dec:3,sep:',',utm:S.crs},out=[],warn=[],day=mpToday().replace(/-/g,'');
 try{if(fmt==='csv')gs.forEach(g=>out.push(mpCSV([g],o)));
  else if(fmt==='dxf'||fmt==='kml'||fmt==='kmz'){const r=GC.write(fmt,gs,Object.assign({base:'Pemetaan_'+day},o));out.push(...r.files);warn.push(...r.warn);}
  else for(const g of gs){const r=GC.write(fmt,[g],Object.assign({base:g.base},o));out.push(...r.files);warn.push(...r.warn);}}
 catch(e){msg('Ekspor pemetaan gagal: '+e.message,'e');return;}
 Array.from(new Set(warn)).forEach(w=>msg(w,'w'));const nm='Pemetaan_'+day+'_'+fmt+'.zip';dl(nm,GC.zip(out),'application/zip');
 msg('Ekspor pemetaan: '+nm+' — '+gs.map(g=>MK[g.mapc].n+' '+(g.P.length||g.PT.length)).join(', ')+' ('+out.length+' file).');}
function dlgMapExport(){const gs=mpCats().map(c=>mpLayer(c,false)).filter(g=>g&&(g.P.length||g.PT.length));
 if(!gs.length){msg('Belum ada fitur pemetaan untuk diekspor.','w');return;}
 const F=[['shp','Shapefile (SHP)','MapInfo, Global Mapper, ArcGIS, Leapfrog — satu shapefile per kategori, atribut lengkap (strike / dip, Sample_ID, kode).'],
  ['mif','MapInfo MIF/MID','MapInfo — satu tabel per kategori.'],['dxf','DXF (satu file)','Surpac, Leapfrog, AutoCAD — satu layer per kategori.'],
  ['csv','CSV','Leapfrog (titik struktur: X, Y, Z, DIP, DIPDIR), Excel — satu tabel per kategori, garis ditulis per vertex.'],
  ['str','Surpac STR','Surpac — satu string file per kategori.'],['kml','KML (satu file)','Google Earth.'],['geojson','GeoJSON','QGIS, web.']];
 const m=modal('Ekspor set pemetaan','<p>Isi: '+gs.map(g=>'<b>'+esc(MK[g.mapc].n)+'</b> '+(g.P.length||g.PT.length)).join(' · ')+'. Semua diunduh sebagai satu ZIP.</p><div class="mpx">'+F.map(f=>'<button class="fmt" data-x="'+f[0]+'"><b>'+f[1]+'</b><small>'+f[2]+'</small></button>').join('')+'</div>');
 $$('[data-x]',m).forEach(b=>b.onclick=()=>{m.remove();mpExport(b.dataset.x);});}
