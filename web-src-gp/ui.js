'use strict';
/* Geo Pocket — antarmuka: peta 2D ala Global Mapper dalam kerangka Ore Works */
const $=(s,r)=>(r||document).querySelector(s),$$=(s,r)=>Array.from((r||document).querySelectorAll(s));
const esc=(s)=>String(s==null?'':s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const nf=(v,d)=>(+v).toLocaleString('id-ID',{minimumFractionDigits:d||0,maximumFractionDigits:d||0});
const el=(t,c)=>{const e=document.createElement(t);if(c)e.className=c;return e;};
const ic=(n)=>'<svg class="ic"><use href="#i-'+n+'"/></svg>';
const store={get(k,d){try{const v=localStorage.getItem(k);return v===null?d:v;}catch(e){return d;}},set(k,v){try{localStorage.setItem(k,v);}catch(e){}}};
const S={folders:[],selFold:null,geoms:[],sel:null,selF:null,tab:'2d',log:[],filter:'',view:null,tfilter:'',undo:[],crs:null};
const C={fmt:'dxf',soft:'Semua',mode:'auto',dec:3,sep:',',base:'',off:new Set()};
const FMT=Object.fromEntries(GC.FORMATS.map(f=>[f.id,f]));
const gById=(id)=>S.geoms.find(g=>g.id===id);
const isVec=(g)=>!g.ras&&!g.dem;
const vecs=()=>S.geoms.filter(isVec);
(function(){const z=+store.get('gc_zone','50'),s=store.get('gc_south','1')==='1',on=store.get('gc_crs','1')==='1';S.crs=on?{zone:z,south:s}:null;})();

/* ---------- pesan / status ---------- */
function msg(t,lv){S.log.unshift({t:new Date().toLocaleTimeString('id-ID'),txt:t,lv:lv||'i'});if(S.log.length>300)S.log.pop();renderStatus();if($('#logpop').style.display==='block')renderLog();}
function renderStatus(){const m=S.log[0],n=S.log.filter(l=>l.lv!=='i').length;$('#sbmsg').innerHTML=m?esc(m.txt)+(n?'<span class="cnt">'+n+' peringatan</span>':''):'Siap. Seret file untuk memulai.';$('#sbcrs').textContent=S.crs?'UTM '+S.crs.zone+(S.crs.south?'S':'N')+' · WGS84':'CRS lokal';}
function renderLog(){$('#logpop').innerHTML=S.log.length?S.log.map(l=>'<div class="lg '+l.lv+'"><small>'+l.t+'</small>'+esc(l.txt)+'</div>').join(''):'<div class="lg">Belum ada pesan.</div>';}
$('#sbmsg').onclick=(e)=>{e.stopPropagation();const p=$('#logpop');if(p.style.display==='block')p.style.display='none';else{renderLog();p.style.display='block';}};
$('#sbcrs').onclick=(e)=>{e.stopPropagation();dlgCRS();};
function onCursor(x,y){const c=$('#sbcoord');if(x===null||x===undefined){c.textContent='';return;}let t='E '+nf(x,2)+'  N '+nf(y,2);
 if(S.crs&&x>100000&&x<900000&&y>=0&&y<=10000000){const ll=GC.utm2ll(x,y,S.crs.zone,S.crs.south);if(isFinite(ll[0])&&Math.abs(ll[0])<=90)t+='  ·  '+Math.abs(ll[0]).toFixed(6)+'°'+(ll[0]<0?'LS':'LU')+' '+Math.abs(ll[1]).toFixed(6)+'°'+(ll[1]<0?'BB':'BT');}
 for(const g of S.geoms)if(g.visible&&g.dem){const z=GC.demZ(g.dem,x,y);if(z===z){t+='  ·  Z '+nf(z,2);break;}}
 c.textContent=t+'  ·  1:'+nf(96/0.0254/M2.view.s);}

/* ---------- menu ---------- */
function buildMenu(items){const dd=el('div','dd');
 for(const it of items){if(it==='-'){dd.append(el('div','sep'));continue;}const dis=it.dis&&it.dis(),row=el('div','cmi'+(dis?' dis':''));
  row.innerHTML='<span class="ic0">'+(it.chk?(it.chk()?'✓':''):'')+'</span><span>'+it.t+'</span>'+(it.k?'<span class="k">'+it.k+'</span>':'')+(it.sub?'<span class="arr">▸</span>':'');
  if(it.sub)row.append(buildMenu(it.sub));else row.onclick=(e)=>{e.stopPropagation();closeMenus();it.fn();};dd.append(row);}
 return dd;}
function closeMenus(){$$('#menus .dd').forEach(d=>d.remove());$$('.mb.on').forEach(b=>b.classList.remove('on'));$('#ctx').innerHTML='';$('#logpop').style.display='none';}
const wfmt=()=>GC.FORMATS.filter(f=>f.w);
const exportSub=(fn)=>wfmt().map(f=>({t:f.label,fn:()=>fn(f.id)}));
const MENUS=[
 {t:'Berkas',items:()=>[{t:'Buka file…',k:'Ctrl+O',fn:()=>$('#fin').click()},'-',
   {t:'Ekspor lapisan terpilih sebagai',sub:exportSub((f)=>quickExport(f,S.sel?[gById(S.sel)]:[]))},
   {t:'Ekspor semua lapisan tampil sebagai',sub:exportSub((f)=>quickExport(f,S.geoms.filter(g=>g.visible)))},'-',
   {t:'Simpan tampilan peta (PNG)',fn:()=>dl('geopocket_peta.png',dataUrlBytes(S.tab==='3d'?V3.png():M2.png()),'image/png')},'-',
   {t:'Kosongkan semua',fn:()=>{if(confirm('Kosongkan semua lapisan?'))clearAll();},dis:()=>!S.geoms.length}]},
 {t:'Proyek',items:()=>[{t:'Sistem koordinat…',fn:dlgCRS},{t:'Proyeksikan lapisan terpilih (lintang/bujur → UTM)',fn:reprojSel,dis:()=>!S.sel||!S.crs}]},
 {t:'Digitasi',items:()=>[{t:'Poligon',k:'P',fn:()=>setTool('poly')},{t:'Garis',k:'L',fn:()=>setTool('line')},{t:'Titik',fn:()=>setTool('point')},{t:'Edit vertex',k:'E',fn:()=>setTool('edit')},'-',
   {t:'Lapisan digitasi baru…',fn:newDigit},{t:'Folder baru…',fn:()=>askFolder(null)},{t:'Urungkan',k:'Ctrl+Z',fn:undo,dis:()=>!S.undo.length}]},
 {t:'Analisis',items:()=>[{t:'Ukur jarak',k:'D',fn:()=>setTool('dist')},{t:'Ukur luas',k:'A',fn:()=>setTool('area')},{t:'Tabel luas poligon lapisan terpilih',fn:()=>{S.view='pl';showTab('tbl');},dis:()=>!S.sel||!gById(S.sel).P.length},'-',
   {t:'Buat DEM dari topografi (string / DXF)…',fn:dlgDEM,dis:()=>!vecs().some(g=>g.V.length)},{t:'Buat kontur dari DEM…',fn:dlgContour,dis:()=>!S.geoms.some(g=>g.dem)}]},
 {t:'Peta',items:()=>[{t:'Layout peta (PNG / PDF)…',fn:dlgLayout,dis:()=>!S.geoms.length},'-',{t:'Grid koordinat',chk:()=>M2.st.grid,fn:()=>{M2.st.grid=!M2.st.grid;M2.draw();}},{t:'Label',chk:()=>M2.st.labels,fn:()=>{M2.st.labels=!M2.st.labels;M2.draw();}},'-',{t:'Zoom semua',k:'Home',fn:fitAll}]},
 {t:'Tampilan',items:()=>[
   {t:'Palet warna',sub:[['keluarga','Keluarga GC-Ex · Malakit'],['oksida','Oksida'],['kuarsa','Kuarsa-Emas'],['azurit','Azurit'],['hitam','Hitam-putih']].map(p=>({t:p[1],chk:()=>document.documentElement.dataset.palet===p[0],fn:()=>{document.documentElement.dataset.palet=p[0];store.set('gc_palet',p[0]);}}))},
   {t:'Latar',sub:[['hangat','Hangat'],['terang','Putih'],['gelap','Gelap']].map(p=>({t:p[1],chk:()=>document.documentElement.dataset.latar===p[0],fn:()=>{document.documentElement.dataset.latar=p[0];store.set('gc_latar',p[0]);}}))},
   {t:'Mode 3D',sub:[['solid','Solid'],['solidwire','Solid + garis tepi'],['wire','Kerangka'],['points','Titik vertex']].map(p=>({t:p[1],chk:()=>V3.getMode()===p[0],fn:()=>V3.setMode(p[0])}))},'-',
   {t:'Panel Project Tree',chk:()=>$('#left').style.display!=='none',fn:()=>togDock('left')},{t:'Panel Properti',chk:()=>$('#right').style.display!=='none',fn:()=>togDock('right')}]},
 {t:'Bantuan',items:()=>[{t:'Format yang didukung',fn:showFormats},{t:'Pintasan & cara pakai',fn:showHelp},{t:'Tentang',fn:showAbout}]}
];
function initMenus(){const host=$('#menus');
 MENUS.forEach(m=>{const b=el('button','mb');b.textContent=m.t;host.append(b);
  const open=()=>{closeMenus();b.classList.add('on');const dd=buildMenu(m.items());dd.style.left=b.offsetLeft+'px';dd.style.top='28px';host.append(dd);};
  b.onclick=(e)=>{e.stopPropagation();if(b.classList.contains('on'))closeMenus();else open();};b.onmouseenter=()=>{if($$('.mb.on').length&&!b.classList.contains('on'))open();};});}
document.addEventListener('click',closeMenus);
function showCtx(x,y,items){closeMenus();const dd=buildMenu(items);dd.style.position='fixed';dd.style.left=Math.min(x,innerWidth-250)+'px';dd.style.top=Math.min(y,innerHeight-items.length*24-10)+'px';$('#ctx').append(dd);}
function modal(title,html,wide){const m=el('div','modal');m.innerHTML='<div class="mc'+(wide?' wide':'')+'"><div class="mh">'+esc(title)+'<button class="btn2" data-close>Tutup</button></div><div class="mb2">'+html+'</div></div>';m.addEventListener('click',(e)=>{if(e.target===m||e.target.closest('[data-close]'))m.remove();});document.body.append(m);return m;}
function showFormats(){modal('Format yang didukung','<table><tr><th>Format</th><th>Baca</th><th>Tulis</th><th>Catatan</th></tr>'+GC.FORMATS.map(f=>'<tr><td><b>'+esc(f.label)+'</b><br><small>'+esc(f.soft)+'</small></td><td>'+(f.r?'✓':'–')+'</td><td>'+(f.w?'✓':'–')+'</td><td>'+esc(f.note)+'</td></tr>').join('')+
 '<tr><td><b>GeoTIFF ortofoto (.tif)</b></td><td>✓</td><td>–</td><td>RGB/RGBA, LZW/Deflate/JPEG, bertingkat (overview); detail dibaca sesuai zoom. ECW dan MrSID tidak didukung (format tertutup).</td></tr>'+
 '<tr><td><b>JPG / PNG + world file</b></td><td>✓</td><td>–</td><td>Pilih gambar bersama .jgw / .pgw / .wld.</td></tr>'+
 '<tr><td><b>MapInfo TAB / DAT</b></td><td>atribut</td><td>–</td><td>Geometri .MAP/.ID tertutup. Ekspor dari MapInfo ke MIF/MID atau SHP.</td></tr></table>'+
 '<p class="hint"><b>Berkas berpasangan</b> pilih bersama: SHP + DBF, MIF + MID, TAB + DAT, DTM + STR, gambar + world file.</p>',true);}
function showHelp(){modal('Pintasan & cara pakai','<table><tr><th>Aksi</th><th>Cara</th></tr>'+[['Geser peta','seret (di semua alat)'],['Zoom','roda mouse; <b>Home</b> = zoom semua'],['Info fitur','klik fitur (alat Geser / Info)'],['Digit poligon / garis','<b>P</b> / <b>L</b>, klik titik-titik, klik ganda / Enter / klik kanan = selesai, Backspace = hapus titik terakhir, Esc = batal'],['Snap','otomatis ke vertex terdekat (kotak kuning)'],['Edit vertex','<b>E</b>, klik fitur, seret kotak; bulatan = sisip titik; Delete di atas kotak = hapus titik'],['Hapus fitur','pilih fitur lalu Delete'],['Ukur jarak / luas','<b>D</b> / <b>A</b>'],['Urungkan','Ctrl+Z'],['Urutan lapisan','seret baris di panel Lapisan (atas = digambar paling akhir)'],['Folder / subfolder','tombol <b>＋ Folder</b>, lalu seret lapisan atau folder ke dalamnya; klik kanan folder untuk subfolder, ekspor isi, atau hapus']].map(r=>'<tr><td>'+r[0]+'</td><td>'+r[1]+'</td></tr>').join('')+'</table>');}
function showAbout(){modal('Tentang Geo Pocket','<p><b>Geo Pocket</b> (sebelumnya GeoConv): penampil peta 2D, digitasi, luas, layout, dan konverter data geologi/tambang. Berjalan sepenuhnya di komputer Anda (offline).</p><p>Memakai ulang kode GC-Ex / Ore Works / Pit Studio: pembaca MSH, DTM+STR Surpac, STR biner, DXF BLOCK/INSERT, aturan TIN (rapatkan string 2 m, buang segitiga tepi panjang), serta pustaka yang sudah ada di repo: geotiff.js 2.1.3 (MIT) dan Delaunator (ISC).</p>');}
function togDock(w){const d=$('#'+w),s=$(w==='left'?'#sp1':'#sp2'),on=d.style.display==='none';d.style.display=on?'':'none';s.style.display=on?'':'none';M2.resize();V3.resize();}
$('#bleftc').onclick=()=>togDock('left');$('#brightc').onclick=()=>togDock('right');
function dataUrlBytes(u){const b=atob(u.split(',')[1]),a=new Uint8Array(b.length);for(let i=0;i<b.length;i++)a[i]=b.charCodeAt(i);return a;}
function dl(name,data,mime){const b=data instanceof Blob?data:new Blob([data],{type:mime||'application/octet-stream'}),a=document.createElement('a');a.href=URL.createObjectURL(b);a.download=name;document.body.append(a);a.click();setTimeout(()=>{URL.revokeObjectURL(a.href);a.remove();},1500);}

/* ---------- sistem koordinat ---------- */
function dlgCRS(){const c=S.crs||{zone:50,south:true};
 const m=modal('Sistem koordinat proyek','<p class="hint">Dipakai untuk lintang/bujur di status bar, KML/KMZ/GeoJSON, file .prj Shapefile, CoordSys MIF, dan GeoTIFF. Datum WGS84.</p><div class="fr"><span>Jenis</span><select id="ctype"><option value="1"'+(S.crs?' selected':'')+'>UTM (WGS84)</option><option value="0"'+(S.crs?'':' selected')+'>Lokal / tidak ditentukan</option></select></div><div class="fr"><span>Zona UTM</span><select id="cz">'+Array.from({length:60},(_,i)=>'<option'+(i+1===c.zone?' selected':'')+' value="'+(i+1)+'">'+(i+1)+'  ('+(i*6-180)+'° s/d '+(i*6-174)+'°)</option>').join('')+'</select></div><div class="fr"><span>Belahan</span><select id="cs"><option value="1"'+(c.south?' selected':'')+'>Selatan (S)</option><option value="0"'+(c.south?'':' selected')+'>Utara (N)</option></select></div><p class="hint">Indonesia: 46–54. Sumbawa dan Lombok = <b>50S</b>; Jawa Timur–Bali 49S/50S; Flores 51S.</p><div class="row"><button class="btn" id="cok">Terapkan</button></div>');
 $('#cok',m).onclick=()=>{S.crs=$('#ctype',m).value==='1'?{zone:+$('#cz',m).value,south:$('#cs',m).value==='1'}:null;store.set('gc_crs',S.crs?'1':'0');if(S.crs){store.set('gc_zone',S.crs.zone);store.set('gc_south',S.crs.south?'1':'0');}m.remove();renderStatus();msg('Sistem koordinat proyek: '+GC.crsName(S.crs));if(S.tab==='conv')renderConv();};}
function reprojSel(){const g=gById(S.sel);if(!g||!isVec(g))return;if(!GC.looksGeo(g)){msg(g.name+': koordinat bukan lintang/bujur (di luar ±180/±90).','w');return;}GC.projectGeom(g,S.crs);refreshAll();M2.fit([g]);msg(g.name+' diproyeksikan ke '+GC.crsName(S.crs)+'.');}

/* ---------- muat file ---------- */
const RASX=/^(tif|tiff|jpg|jpeg|png)$/,WLDX=/^(tfw|tifw|jgw|jpgw|pgw|pngw|wld)$/;
async function unzip(buf){const u=new Uint8Array(buf),dv=new DataView(buf);let e=u.length-22;while(e>=0&&dv.getUint32(e,true)!==0x06054b50)e--;if(e<0)throw new Error('Bukan arsip ZIP/KMZ');
 const n=dv.getUint16(e+10,true);let p=dv.getUint32(e+16,true);const out=[];
 for(let i=0;i<n;i++){if(dv.getUint32(p,true)!==0x02014b50)break;const meth=dv.getUint16(p+10,true),cs=dv.getUint32(p+20,true),nl=dv.getUint16(p+28,true),xl=dv.getUint16(p+30,true),cl=dv.getUint16(p+32,true),lo=dv.getUint32(p+42,true),name=new TextDecoder().decode(u.subarray(p+46,p+46+nl));
  const ds=lo+30+dv.getUint16(lo+26,true)+dv.getUint16(lo+28,true),raw=u.subarray(ds,ds+cs);
  if(meth===0)out.push({name:name,buf:raw.slice().buffer});else if(meth===8)out.push({name:name,buf:await new Response(new Blob([raw]).stream().pipeThrough(new DecompressionStream('deflate-raw'))).arrayBuffer()});
  p+=46+nl+xl+cl;}
 return out;}
function addGeom(g,file){g.file=file;g.base=file.replace(/\.[^.]+$/,'');g.fold=S.selFold&&fById(S.selFold)?S.selFold:null;S.geoms.unshift(g);return g;}
function postVec(g,fname){if(isVec(g)&&g.V.length&&GC.looksGeo(g)){if(S.crs){GC.projectGeom(g,S.crs);msg(fname+': koordinat lintang/bujur diproyeksikan ke '+GC.crsName(S.crs)+'.');}else msg(fname+': koordinat tampak lintang/bujur. Tentukan sistem koordinat proyek lalu Proyek → Proyeksikan lapisan.','w');}}
async function loadFiles(list){
 const all=Array.from(list),vec=[],ras=[],wld={};
 for(const f of all){const x=(f.name.match(/\.([^.]+)$/)||[,''])[1].toLowerCase();if(RASX.test(x))ras.push(f);else if(WLDX.test(x))wld[f.name.replace(/\.[^.]+$/,'').toLowerCase()]=f;else vec.push(f);}
 const first=!S.geoms.length;let added=null;msg('Memuat '+all.length+' file…');await new Promise(r=>setTimeout(r,16));
 const items=[];
 for(const f of vec){try{const buf=await f.arrayBuffer();if(/\.kmz$/i.test(f.name)){const z=await unzip(buf),k=z.find(e=>/\.kml$/i.test(e.name));if(!k)throw new Error('KMZ tidak berisi file KML');items.push({name:f.name.replace(/\.kmz$/i,'.kml'),buf:k.buf,as:f.name});}else items.push({name:f.name,buf:buf});}catch(e){msg(f.name+': '+e.message,'e');}}
 const asName={};items.forEach(i=>{if(i.as)asName[i.name]=i.as;});
 for(const j of GC.groupFiles(items)){j.name=asName[j.name]?j.name:j.name;try{const t0=performance.now(),r=GC.parse(j.name,j.buf,j.aux);r.warn.forEach(w=>msg(w,'w'));
   const fo=r.geoms.length>1?newFolder(j.name,S.selFold&&fById(S.selFold)?S.selFold:null,true):null;if(fo)fo.open=r.geoms.length<=12;
   for(const g of r.geoms.slice().reverse()){if(g.dem)g.dem.cv=demCanvas(g.dem,'hyps');addGeom(g,j.name);if(fo)g.fold=fo.id;postVec(g,j.name);}added=added||r.geoms[0];
   msg('Dimuat '+j.name+': '+r.geoms.length+' lapisan ('+Math.round(performance.now()-t0)+' ms)');}catch(e){msg(j.name+': '+e.message,'e');}}
 for(const f of ras){try{const g=await loadRaster(f,wld[f.name.replace(/\.[^.]+$/,'').toLowerCase()]);addGeom(g,f.name);added=added||g;msg('Dimuat '+f.name+': '+(g.dem?'DEM '+g.dem.nx+' × '+g.dem.ny+' sel':'citra '+nf(g.ras.W)+' × '+nf(g.ras.H)+' piksel, resolusi '+g.ras.px.toFixed(3)+' m'));}catch(e){msg(f.name+': '+e.message,'e');}}
 if(!added)return;refreshAll();if(first)fitAll();select(added.id);if(S.tab!=='2d'&&S.tab!=='3d')showTab('2d');
}
function demCanvas(d,mode){const c=document.createElement('canvas');c.width=d.nx;c.height=d.ny;c.getContext('2d').putImageData(new ImageData(GC.demRGBA(d,{mode:mode==='gray'?'gray':mode==='flat'?'flat':'hyps'}),d.nx,d.ny),0,0);d.mode=mode;return c;}
function rgbCanvas(data,w,h){const ch=Math.round(data.length/(w*h)),id=new ImageData(w,h),o=id.data,sh=data.BYTES_PER_ELEMENT===2;let mx=255;if(sh){mx=0;for(let i=0;i<data.length;i+=97)if(data[i]>mx)mx=data[i];mx=mx||65535;}
 for(let i=0,j=0;i<w*h;i++,j+=ch){const k=4*i;if(ch>=3){o[k]=sh?data[j]*255/mx:data[j];o[k+1]=sh?data[j+1]*255/mx:data[j+1];o[k+2]=sh?data[j+2]*255/mx:data[j+2];o[k+3]=ch>3?(sh?data[j+3]*255/mx:data[j+3]):255;}else{const v=sh?data[j]*255/mx:data[j];o[k]=o[k+1]=o[k+2]=v;o[k+3]=255;}}
 const c=document.createElement('canvas');c.width=w;c.height=h;c.getContext('2d').putImageData(id,0,0);return c;}
async function loadRaster(f,wf){
 const base=f.name.replace(/\.[^.]+$/,''),g=GC.mk({name:base,src:'tif'});
 if(!/\.tiff?$/i.test(f.name)){if(!wf)throw new Error('gambar tanpa world file (.jgw / .pgw / .wld); pilih keduanya bersamaan.');const w=GC.worldFile(await wf.text()),bm=await createImageBitmap(f),k=Math.min(1,8192/Math.max(bm.width,bm.height)),c=document.createElement('canvas');c.width=Math.round(bm.width*k);c.height=Math.round(bm.height*k);c.getContext('2d').drawImage(bm,0,0,c.width,c.height);
  g.src='img';g.ras={cv:c,W:bm.width,H:bm.height,px:w.px,py:w.py,ext:[w.x0,w.y1-bm.height*w.py,w.x0+bm.width*w.px,w.y1]};return g;}
 if(typeof GeoTIFF==='undefined')throw new Error('pustaka GeoTIFF tidak termuat');
 const tiff=await GeoTIFF.fromBlob(f),img=await tiff.getImage(0),W=img.getWidth(),Hh=img.getHeight(),fd=img.fileDirectory;let px,py,x0,y1;
 try{const o=img.getOrigin(),r=img.getResolution();px=Math.abs(r[0]);py=Math.abs(r[1]);x0=o[0];y1=o[1];const gk=img.getGeoKeys()||{};if(gk.GTRasterTypeGeoKey===2){x0-=px/2;y1+=py/2;}}
 catch(e){if(!wf)throw new Error('TIFF tanpa georeferensi (bukan GeoTIFF dan tidak ada .tfw).');const w=GC.worldFile(await wf.text());px=w.px;py=w.py;x0=w.x0;y1=w.y1;}
 const ext=[x0,y1-Hh*py,x0+W*px,y1];if(Math.abs(ext[0])<=180&&Math.abs(ext[2])<=180&&Math.abs(ext[1])<=90&&Math.abs(ext[3])<=90)msg(f.name+': GeoTIFF berkoordinat lintang/bujur; raster tidak diproyeksikan ulang. Simpan dalam UTM agar bertumpuk dengan data lain.','w');
 const spp=img.getSamplesPerPixel(),bps=img.getBitsPerSample(),sf=fd.SampleFormat?fd.SampleFormat[0]:1;
 if(spp===1&&(sf===3||bps>=16)&&fd.PhotometricInterpretation!==3){const k=Math.min(1,3000/Math.max(W,Hh)),w=Math.max(1,Math.round(W*k)),h=Math.max(1,Math.round(Hh*k)),nd=img.getGDALNoData();
  const r=await img.readRasters({samples:[0],width:w,height:h,resampleMethod:'nearest'}),a=r[0],z=new Float32Array(w*h);for(let i=0;i<z.length;i++){const v=a[i];z[i]=(v===nd||v<-1e30||v>1e30||v!==v)?NaN:v;}
  g.src='tif';g.dem=GC.mkDEM(w,h,x0,y1,px*W/w,z,py*Hh/h);g.dem.cv=demCanvas(g.dem,'hyps');if(k<1)msg(f.name+': DEM '+W+' × '+Hh+' dicuplik ke '+w+' × '+h+' untuk tampilan dan analisis.','w');return g;}
 const n=await tiff.getImageCount(),lv=[{img:img,w:W,h:Hh}];for(let i=1;i<n;i++){const im=await tiff.getImage(i),t=im.fileDirectory.NewSubfileType||0;if((t&1)&&!(t&4))lv.push({img:im,w:im.getWidth(),h:im.getHeight()});}
 lv.sort((a,b)=>b.w-a.w);g.ras={W:W,H:Hh,px:px,py:py,ext:ext,lv:lv,detail:null,tok:0};
 const k=Math.min(1,4096/Math.max(W,Hh)),bw=Math.max(1,Math.round(W*k)),bh=Math.max(1,Math.round(Hh*k)),L=pickLevel(g.ras,bw);
 g.ras.cv=rgbCanvas(await L.img.readRGB({width:bw,height:bh,enableAlpha:true}),bw,bh);return g;}
function pickLevel(r,needW){let best=r.lv[0];for(const l of r.lv)if(l.w>=needW)best=l;return best;}
async function readDetail(g,e,maxPx){const r=g.ras,x0=Math.max(e[0],r.ext[0]),x1=Math.min(e[2],r.ext[2]),y0=Math.max(e[1],r.ext[1]),y1=Math.min(e[3],r.ext[3]);if(x1<=x0||y1<=y0)return null;
 const need=Math.min((x1-x0)/r.px,maxPx*(x1-x0)/Math.max(x1-x0,y1-y0)),fullNeed=need*(r.ext[2]-r.ext[0])/(x1-x0),L=pickLevel(r,fullNeed),kx=L.w/r.W,ky=L.h/r.H;
 const wl=Math.floor((x0-r.ext[0])/r.px*kx),wr=Math.min(L.w,Math.ceil((x1-r.ext[0])/r.px*kx)),wt=Math.floor((r.ext[3]-y1)/r.py*ky),wb=Math.min(L.h,Math.ceil((r.ext[3]-y0)/r.py*ky));if(wr-wl<1||wb-wt<1)return null;
 const sc=Math.min(1,maxPx/Math.max(wr-wl,wb-wt)),ow=Math.max(1,Math.round((wr-wl)*sc)),oh=Math.max(1,Math.round((wb-wt)*sc));
 const d=await L.img.readRGB({window:[wl,wt,wr,wb],width:ow,height:oh,enableAlpha:true});
 return {cv:rgbCanvas(d,ow,oh),ext:[r.ext[0]+wl/kx*r.px,r.ext[3]-wb/ky*r.py,r.ext[0]+wr/kx*r.px,r.ext[3]-wt/ky*r.py]};}
async function refineRasters(){if(S.tab!=='2d')return;const v=M2.view,sz=M2.size(),e=[v.cx-sz[0]/2/v.s,v.cy-sz[1]/2/v.s,v.cx+sz[0]/2/v.s,v.cy+sz[1]/2/v.s];
 for(const g of S.geoms){if(!g.visible||!g.ras||!g.ras.lv)continue;const r=g.ras,baseRes=(r.ext[2]-r.ext[0])/r.cv.width,need=1/(v.s*(window.devicePixelRatio||1));
  if(baseRes<=need*1.3||r.px>=baseRes*0.99){if(r.detail){r.detail=null;M2.draw();}continue;}
  const d=r.detail;if(d&&d.ext[0]<=Math.max(e[0],r.ext[0])+1e-6&&d.ext[2]>=Math.min(e[2],r.ext[2])-1e-6&&d.ext[1]<=Math.max(e[1],r.ext[1])+1e-6&&d.ext[3]>=Math.min(e[3],r.ext[3])-1e-6&&(d.ext[2]-d.ext[0])/d.cv.width<=need*1.5)continue;
  const tok=++r.tok;try{const nd=await readDetail(g,e,Math.min(4096,Math.round(Math.max(sz[0],sz[1])*(window.devicePixelRatio||1))));if(tok===r.tok&&nd){r.detail=nd;M2.draw();}}catch(er){msg(g.name+': gagal membaca detail citra ('+er.message+')','w');}}}

function clearAll(){S.folders=[];S.selFold=null;S.geoms=[];S.sel=null;S.selF=null;S.undo=[];C.off=new Set();refreshAll();msg('Semua lapisan dikosongkan.');}
function delGeom(id){S.geoms=S.geoms.filter(x=>x.id!==id);if(S.sel===id){S.sel=null;S.selF=null;}refreshAll();}
function refreshAll(){V3.rebuild(vecs().filter(g=>g.V.length));renderTree();renderLegend();renderProps();renderStatus();M2.draw();if(S.tab==='tbl')renderTable();if(S.tab==='conv')renderConv();$('#nodata').style.display=S.geoms.length?'none':'flex';
 let nv=0,nt=0,np=0,npt=0;for(const g of S.geoms){nv+=g.V.length/3;nt+=g.F.length/3;np+=g.P.length;npt+=g.PT.length;}$('#sbinfo').textContent=S.geoms.length?S.geoms.length+' lapisan'+(nt?' · '+nf(nt)+' segitiga':'')+(np?' · '+nf(np)+' garis/poligon':'')+(npt?' · '+nf(npt)+' titik':''):'';}
function select(id,keepF){S.sel=id;if(!keepF)S.selF=null;V3.setSel(id);S.view=null;renderTree();renderProps();M2.draw();if(S.tab==='tbl')renderTable();}
function fitAll(){M2.fit();V3.fit();}

/* ---------- panel Lapisan (Project Tree berfolder; urutan pohon = urutan gambar, atas = digambar terakhir) ---------- */
const kindOf=(g)=>g.ras?'img':g.dem?'dem':g.F.length?'mesh':g.P.length?'line':g.PT.length||g.V.length?'pts':'tab';
const badge=(g)=>g.ras?'citra':g.dem?'DEM '+g.dem.nx+'×'+g.dem.ny:g.F.length?nf(g.F.length/3)+' seg.':g.P.length?(()=>{const c=g.P.filter(p=>p.closed).length,o=g.P.length-c;return (c?nf(c)+' poligon':'')+(c&&o?' + ':'')+(o?nf(o)+' garis':'');})()+(g.PT.length?' + '+nf(g.PT.length)+' tt.':''):g.PT.length?nf(g.PT.length)+' titik':g.meta.rows?nf(g.meta.rows.length)+' baris':'kosong';
let FID=1;
const fById=(id)=>S.folders.find(f=>f.id===id);
const fold=(g)=>(g.fold&&fById(g.fold))?g.fold:null;
function fAnc(id,anc){for(let f=fById(id);f;f=fById(f.parent)){if(f.id===anc)return true;}return false;}
function fLayers(id){return S.geoms.filter(g=>fold(g)!==null&&fAnc(g.fold,id));}
function fPath(id){const p=[];for(let f=fById(id);f;f=fById(f.parent))p.unshift(f.name);return p.join(' / ');}
function newFolder(name,parent,quiet){const f={id:FID++,name:name,parent:parent||null,open:true};S.folders.push(f);if(!quiet){renderTree();}return f;}
function askFolder(parent){const nm=prompt(parent?'Nama subfolder di dalam "'+fById(parent).name+'"':'Nama folder baru','Folder '+(S.folders.length+1));if(!nm)return null;const f=newFolder(nm.trim()||'Folder',parent);if(parent)fById(parent).open=true;renderTree();return f;}
function treeNodes(parent){const pos=new Map();S.geoms.forEach((g,i)=>pos.set(g.id,i));const out=[];
 for(const f of S.folders){if((fById(f.parent)?f.parent:null)!==parent)continue;const L=fLayers(f.id);out.push({f:f,k:L.length?Math.min(...L.map(g=>pos.get(g.id))):-1e9+f.id});}
 for(const g of S.geoms)if(fold(g)===parent)out.push({g:g,k:pos.get(g.id)});
 return out.sort((a,b)=>a.k-b.k);}
function normalize(){const out=[];(function walk(p){for(const n of treeNodes(p)){if(n.g)out.push(n.g);else walk(n.f.id);}})(null);if(out.length===S.geoms.length)S.geoms=out;}
function renderTree(){normalize();const t=$('#tree'),sc=t.scrollTop,q=S.filter.toLowerCase();let h='';
 const match=(g)=>!q||g.name.toLowerCase().indexOf(q)>=0||(g.file||'').toLowerCase().indexOf(q)>=0;
 const anyIn=(id)=>fLayers(id).some(match)||(!q);
 (function walk(p,d){for(const n of treeNodes(p)){const pad='style="padding-left:'+(6+d*14)+'px"';
   if(n.f){const f=n.f,L=fLayers(f.id);if(q&&!L.some(match))continue;const vis=L.some(g=>g.visible);
    h+='<div class="nd fd'+(S.selFold===f.id?' sel':'')+'" data-fd="'+f.id+'" draggable="true" '+pad+' title="'+esc(fPath(f.id))+'"><span class="tw" data-tw="'+f.id+'">'+(f.open||q?'▾':'▸')+'</span><input type="checkbox" '+(vis?'checked':'')+' data-fvis="'+f.id+'" aria-label="Tampilkan folder '+esc(f.name)+'">'+ic('folder')+'<span class="nm"><b>'+esc(f.name)+'</b></span><span class="bd">'+L.length+' lapisan</span></div>';
    if(f.open||q)walk(f.id,d+1);}
   else{const g=n.g;if(!match(g))continue;
    h+='<div class="nd'+(g.id===S.sel?' sel':'')+(g.visible?'':' off')+'" data-g="'+g.id+'" draggable="true" style="padding-left:'+(6+d*14+(d?12:0))+'px" title="'+esc((g.file||'digitasi')+' · '+g.name)+'"><input type="checkbox" '+(g.visible?'checked':'')+' data-vis="'+g.id+'" aria-label="Tampilkan '+esc(g.name)+'"><span class="sw" style="background:'+(g.ras?'#888':g.dem?'#8FAA68':g.color)+'"></span>'+ic(kindOf(g))+'<span class="nm">'+esc(g.name)+'</span><span class="bd">'+badge(g)+'</span></div>';}}})(null,0);
 if(!S.geoms.length&&!S.folders.length)h='<div class="empty">Belum ada data.<br>Seret file ke jendela ini, atau pilih <b>Berkas → Buka file…</b><br><br>Lapisan teratas digambar paling akhir (di atas). Seret lapisan ke folder untuk mengelompokkan.</div>';
 t.innerHTML=h;t.scrollTop=sc;}
function redrawAll(){renderTree();renderLegend();M2.draw();V3.draw();}
$('#tree').addEventListener('click',(e)=>{const tw=e.target.closest('[data-tw]');if(tw){const f=fById(+tw.dataset.tw);f.open=!f.open;renderTree();return;}
 const fv=e.target.closest('[data-fvis]');if(fv){fLayers(+fv.dataset.fvis).forEach(g=>g.visible=fv.checked);redrawAll();e.stopPropagation();return;}
 const v=e.target.closest('[data-vis]');if(v){gById(+v.dataset.vis).visible=v.checked;redrawAll();e.stopPropagation();return;}
 const fd=e.target.closest('[data-fd]');if(fd){S.selFold=+fd.dataset.fd;renderTree();return;}
 const n=e.target.closest('[data-g]');if(n){S.selFold=null;select(+n.dataset.g);}});
$('#tree').addEventListener('dblclick',(e)=>{if(e.target.tagName==='INPUT'||e.target.closest('[data-tw]'))return;const fd=e.target.closest('[data-fd]');if(fd){const L=fLayers(+fd.dataset.fd);if(L.length){L.forEach(g=>g.visible=true);redrawAll();M2.fit(L);}return;}
 const n=e.target.closest('[data-g]');if(n){const g=gById(+n.dataset.g);g.visible=true;renderTree();M2.fit([g]);}});
/* seret-lepas: lapisan atau folder; zona atas / ke dalam (folder) / bawah */
let dragIt=null;
const rowOf=(e)=>e.target.closest('[data-g],[data-fd]');
function dropZone(n,e){const r=n.getBoundingClientRect(),y=(e.clientY-r.top)/r.height;if(n.dataset.fd)return y<0.25?'a':y>0.75?'b':'in';return y<0.5?'a':'b';}
function clearDrop(){$$('#tree .nd').forEach(x=>x.classList.remove('dropa','dropb','dropin'));}
$('#tree').addEventListener('dragstart',(e)=>{const n=rowOf(e);if(!n)return;dragIt=n.dataset.fd?{f:+n.dataset.fd}:{g:+n.dataset.g};e.dataTransfer.effectAllowed='move';e.dataTransfer.setData('text/plain','layer');});
$('#tree').addEventListener('dragover',(e)=>{if(!dragIt)return;e.preventDefault();e.stopPropagation();clearDrop();const n=rowOf(e);if(n)n.classList.add({a:'dropa',b:'dropb','in':'dropin'}[dropZone(n,e)]);});
$('#tree').addEventListener('drop',(e)=>{if(!dragIt)return;e.preventDefault();e.stopPropagation();const it=dragIt,n=rowOf(e);dragIt=null;clearDrop();
 const block=it.f?fLayers(it.f):[gById(it.g)],setParent=(p)=>{if(it.f){if(p&&fAnc(p,it.f))return false;fById(it.f).parent=p;}else block[0].fold=p;return true;};
 if(!n){setParent(null);S.geoms=S.geoms.filter(g=>block.indexOf(g)<0).concat(block);redrawAll();return;}
 const z=dropZone(n,e),tf=n.dataset.fd?+n.dataset.fd:null,tg=n.dataset.g?gById(+n.dataset.g):null;if((it.f&&tf===it.f)||(tg&&block.indexOf(tg)>=0)){renderTree();return;}
 const tl=tf?fLayers(tf).filter(g=>block.indexOf(g)<0):[tg],newParent=z==='in'?tf:(tf?(fById(tf).parent||null):fold(tg));
 if(!setParent(fById(newParent)?newParent:null)){msg('Folder tidak bisa dipindah ke dalam dirinya sendiri.','w');renderTree();return;}
 const rest=S.geoms.filter(g=>block.indexOf(g)<0);let i=rest.length;if(tl.length){const idx=tl.map(g=>rest.indexOf(g));i=z==='b'?Math.max(...idx)+1:Math.min(...idx);}
 rest.splice(i,0,...block);S.geoms=rest;if(z==='in')fById(tf).open=true;redrawAll();});
$('#tree').addEventListener('dragend',()=>{dragIt=null;clearDrop();});
function delFolder(id,withLayers){const f=fById(id);if(!f)return;const sub=S.folders.filter(x=>fAnc(x.id,id)).map(x=>x.id);
 if(withLayers){const L=fLayers(id);S.geoms=S.geoms.filter(g=>L.indexOf(g)<0);if(S.sel&&!gById(S.sel)){S.sel=null;S.selF=null;}S.folders=S.folders.filter(x=>sub.indexOf(x.id)<0);}
 else{S.geoms.forEach(g=>{if(g.fold===id)g.fold=f.parent||null;});S.folders.forEach(x=>{if(x.parent===id)x.parent=f.parent||null;});S.folders=S.folders.filter(x=>x!==f);}
 if(S.selFold===id)S.selFold=null;refreshAll();}
const moveSub=(fn)=>[{t:'(tanpa folder)',fn:()=>fn(null)}].concat(S.folders.map(f=>({t:esc(fPath(f.id)),fn:()=>fn(f.id)}))).concat(['-',{t:'Folder baru…',fn:()=>{const f=askFolder(null);if(f)fn(f.id);}}]);
$('#tree').addEventListener('contextmenu',(e)=>{e.preventDefault();const fd=e.target.closest('[data-fd]'),n=e.target.closest('[data-g]');
 if(fd){const f=fById(+fd.dataset.fd),L=fLayers(f.id);S.selFold=f.id;renderTree();
  showCtx(e.clientX,e.clientY,[{t:'Zoom ke folder',fn:()=>{L.forEach(g=>g.visible=true);redrawAll();M2.fit(L);},dis:()=>!L.length},{t:'Tampilkan hanya folder ini',fn:()=>{S.geoms.forEach(g=>g.visible=L.indexOf(g)>=0);redrawAll();M2.fit(L);},dis:()=>!L.length},'-',
   {t:'Subfolder baru…',fn:()=>askFolder(f.id)},{t:'Ganti nama…',fn:()=>{const v=prompt('Nama folder',f.name);if(v){f.name=v;renderTree();}}},{t:'Pindahkan ke dalam',sub:moveSub((p)=>{if(p&&fAnc(p,f.id)){msg('Folder tidak bisa dipindah ke dalam dirinya sendiri.','w');return;}f.parent=p;redrawAll();})},'-',
   {t:'Ekspor isi folder sebagai',sub:exportSub((fm)=>quickExport(fm,L,f.name))},'-',{t:'Hapus folder (isi dikeluarkan)',fn:()=>delFolder(f.id,false)},{t:'Hapus folder beserta isinya',fn:()=>{if(confirm('Hapus folder "'+f.name+'" beserta '+L.length+' lapisan di dalamnya?'))delFolder(f.id,true);}}]);return;}
 if(!n){showCtx(e.clientX,e.clientY,[{t:'Folder baru…',fn:()=>askFolder(null)}]);return;}
 const g=gById(+n.dataset.g);S.selFold=null;select(g.id);const sib=()=>S.geoms.filter(x=>fold(x)===fold(g));
 const mv=(d)=>{const s=sib(),k=s.indexOf(g),t=d==='top'?s[0]:d==='bot'?s[s.length-1]:s[k+d];if(!t||t===g)return;const rest=S.geoms.filter(x=>x!==g),i=rest.indexOf(t)+((d==='bot'||d===1)?1:0);rest.splice(i,0,g);S.geoms=rest;redrawAll();};
 showCtx(e.clientX,e.clientY,[{t:'Zoom ke lapisan',fn:()=>{g.visible=true;renderTree();M2.fit([g]);}},{t:'Tampilkan hanya ini',fn:()=>{S.geoms.forEach(x=>x.visible=x===g);redrawAll();fitAll();}},{t:'Tampilkan semua',fn:()=>{S.geoms.forEach(x=>x.visible=true);redrawAll();}},'-',
  {t:'Pindah ke folder',sub:moveSub((p)=>{g.fold=p;if(p)fById(p).open=true;redrawAll();})},{t:'Naik ke paling atas',fn:()=>mv('top')},{t:'Naik',fn:()=>mv(-1)},{t:'Turun',fn:()=>mv(1)},{t:'Turun ke paling bawah',fn:()=>mv('bot')},'-',
  {t:'Ekspor lapisan ini sebagai',sub:exportSub((f)=>quickExport(f,[g]))},{t:'Ganti nama…',fn:()=>{const v=prompt('Nama lapisan',g.name);if(v){g.name=v;renderTree();renderLegend();renderProps();}}},'-',{t:'Hapus lapisan',fn:()=>delGeom(g.id)}]);});
$('#search').oninput=(e)=>{S.filter=e.target.value;renderTree();};
$('#bfold').onclick=()=>{const f=askFolder(S.selFold&&fById(S.selFold)?S.selFold:null);if(f){S.selFold=f.id;renderTree();}};

/* ---------- legenda ---------- */
function renderLegend(){const L=S.geoms.filter(g=>g.visible);$('#legend').style.display=L.length?'':'none';$('#legbody').innerHTML=L.map(g=>'<div class="li"><span class="sw" style="background:'+(g.ras?'#888':g.dem?'linear-gradient(90deg,#3E7A5E,#DECD8C,#B08054)':g.color)+'"></span>'+esc(g.name)+'</div>').join('');}
$('#legmin').onclick=()=>$('#legend').classList.toggle('min');
(function(){const lg=$('#legend');let d=null;$('.lh',lg).addEventListener('pointerdown',(e)=>{if(e.target.tagName==='BUTTON')return;const r=lg.getBoundingClientRect(),p=lg.parentNode.getBoundingClientRect();d={dx:e.clientX-r.left,dy:e.clientY-r.top,px:p.left,py:p.top};lg.setPointerCapture(e.pointerId);});
 lg.addEventListener('pointermove',(e)=>{if(!d)return;lg.style.right='auto';lg.style.left=Math.max(0,e.clientX-d.px-d.dx)+'px';lg.style.top=Math.max(0,e.clientY-d.py-d.dy)+'px';});lg.addEventListener('pointerup',()=>{d=null;});})();

/* ---------- Properti ---------- */
function sec(t,body,open){return '<details class="sc" '+(open===false?'':'open')+'><summary>'+t+'</summary><div class="sb">'+body+'</div></details>';}
function featHtml(g,f){const V=g.V,cols=g.meta.cols;let h='';
 if(f.type==='pl'&&g.P[f.i]){const p=g.P[f.i],L=GC.polyLen(V,p.idx,p.closed,false),A=p.closed&&p.idx.length>2?GC.polyArea(V,p.idx):0;let z0=Infinity,z1=-Infinity;for(const i of p.idx){if(V[3*i+2]<z0)z0=V[3*i+2];if(V[3*i+2]>z1)z1=V[3*i+2];}
  h+='<div class="kv"><span>Tipe</span><span>'+(p.closed?'Poligon':'Garis')+' #'+(f.i+1)+'</span><span>Titik</span><span>'+p.idx.length+'</span><span>'+(p.closed?'Keliling':'Panjang')+'</span><span>'+nf(L,2)+' m</span>'+(p.closed?'<span>Luas</span><span><b>'+nf(A,2)+' m²</b></span><span>Luas</span><span><b>'+nf(A/10000,4)+' ha</b></span>':'')+'<span>Z</span><span>'+nf(z0,2)+' s/d '+nf(z1,2)+'</span></div>';
  if(cols&&!g.meta.map)h+='<div class="kv" style="margin-top:6px">'+cols.map((c,k)=>'<span>'+esc(c)+'</span><input type="text" data-fa="'+k+'" value="'+esc(p.attr&&p.attr[k]!=null?p.attr[k]:'')+'">').join('')+'</div>';
  h+='<div class="row" style="margin-top:6px"><button class="btn2" id="fzoom">Zoom</button><button class="btn2" id="ftog">'+(p.closed?'Buka (jadi garis)':'Tutup (jadi poligon)')+'</button><button class="btn2" id="fdel">Hapus fitur</button></div>';}
 else if(f.type==='pt'&&f.i<g.PT.length){const i=g.PT[f.i],a=g.PA[f.i];h+='<div class="kv"><span>Tipe</span><span>Titik #'+(f.i+1)+'</span><span>X / Easting</span><span>'+nf(V[3*i],3)+'</span><span>Y / Northing</span><span>'+nf(V[3*i+1],3)+'</span><span>Z</span><span>'+nf(V[3*i+2],3)+'</span></div>';
  if(cols&&a)h+='<div class="kv" style="margin-top:6px">'+cols.map((c,k)=>'<span>'+esc(c)+'</span>'+(g.meta.map?'<span>'+esc(a[k])+'</span>':'<input type="text" data-fa="'+k+'" value="'+esc(a[k]!=null?a[k]:'')+'">')).join('')+'</div>';
  h+='<div class="row" style="margin-top:6px"><button class="btn2" id="fdel">Hapus fitur</button></div>';}
 else if(f.type==='mesh'||f.type==='dem')h+='<div class="kv"><span>Posisi</span><span>'+nf(f.x,2)+' E, '+nf(f.y,2)+' N</span><span>Elevasi</span><span><b>'+nf(f.z,3)+' m</b></span></div>';
 else if(f.type==='ras')h+='<div class="kv"><span>Posisi</span><span>'+nf(f.x,2)+' E, '+nf(f.y,2)+' N</span></div>';
 return h;}
function renderProps(){const g=gById(S.sel),P=$('#props');
 if(!g){P.innerHTML='<div class="empty">Pilih lapisan di panel Lapisan, atau klik fitur di peta, untuk melihat properti, luas, dan gaya tampilan.</div>';return;}
 const e=M2.ext(g),s=M2.sty(g),f=S.selF&&S.selF.g===g?S.selF:null;let h='';
 if(f)h+=sec('Fitur terpilih',featHtml(g,f));
 h+=sec('Lapisan','<div class="kv"><span>Nama</span><input type="text" id="pnm" value="'+esc(g.name)+'"><span>Berkas</span><span>'+esc(g.file||'(digitasi)')+'</span>'+(g.ras?'<span>Ukuran asli</span><span>'+nf(g.ras.W)+' × '+nf(g.ras.H)+' piksel</span><span>Resolusi</span><span>'+g.ras.px.toFixed(3)+' m/piksel</span>'+(g.ras.lv?'<span>Tingkat</span><span>'+g.ras.lv.length+' (overview)</span>':''):g.dem?'<span>Grid</span><span>'+nf(g.dem.nx)+' × '+nf(g.dem.ny)+' sel</span><span>Ukuran sel</span><span>'+g.dem.cell.toFixed(3)+' m</span><span>Elevasi</span><span>'+nf(g.dem.min,2)+' s/d '+nf(g.dem.max,2)+' m</span>':
  (g.F.length?'<span>Segitiga</span><span>'+nf(g.F.length/3)+'</span>':'')+(g.P.length?'<span>Garis / poligon</span><span>'+nf(g.P.length)+' ('+nf(g.P.filter(p=>p.closed).length)+' tertutup)</span>':'')+(g.PT.length?'<span>Titik</span><span>'+nf(g.PT.length)+'</span>':'')+'<span>Vertex</span><span>'+nf(g.V.length/3)+'</span>')+'</div>',!f);
 if(isVec(g)&&g.P.some(p=>p.closed)){let A=0,n=0;for(const p of g.P)if(p.closed&&p.idx.length>2){A+=GC.polyArea(g.V,p.idx);n++;}h+=sec('Luas','<div class="kv"><span>Poligon</span><span>'+nf(n)+'</span><span>Total luas</span><span><b>'+nf(A,2)+' m²</b></span><span></span><span><b>'+nf(A/10000,4)+' ha</b></span></div><div class="row" style="margin-top:4px"><button class="btn2" id="parea">Tabel luas</button></div><p class="hint">Luas planimetrik (tampak atas) pada bidang proyeksi.</p>');}
 if(e)h+=sec('Batas koordinat','<table class="mini"><tr><th></th><th>Min</th><th>Maks</th><th>Rentang</th></tr><tr><td>X</td><td>'+nf(e[0],2)+'</td><td>'+nf(e[2],2)+'</td><td>'+nf(e[2]-e[0],2)+'</td></tr><tr><td>Y</td><td>'+nf(e[1],2)+'</td><td>'+nf(e[3],2)+'</td><td>'+nf(e[3]-e[1],2)+'</td></tr>'+(isVec(g)&&g.V.length?(()=>{const b=GC.bbox(g);return '<tr><td>Z</td><td>'+nf(b.min[2],2)+'</td><td>'+nf(b.max[2],2)+'</td><td>'+nf(b.max[2]-b.min[2],2)+'</td></tr>';})():'')+'</table>',false);
 if(isVec(g)&&g.F.length){if(g._ms===undefined)g._ms=g.F.length<=1200000?GC.meshStats(g):null;const m=g._ms;h+=sec('Mesh',m?'<div class="kv"><span>Luas permukaan</span><span>'+nf(m.area,1)+' m²</span><span>Volume</span><span>'+(m.closed?nf(m.volume,1)+' m³':'<span class="warn">– (mesh terbuka)</span>')+'</span><span>Status</span><span class="'+(m.closed?'ok':'warn')+'">'+(m.closed?'tertutup (solid)':'terbuka: '+nf(m.open)+' sisi batas')+'</span></div>':'<p class="hint">Mesh terlalu besar untuk statistik otomatis.</p>',false);}
 if(g.meta.raw&&g.meta.map){const o=(sel)=>g.meta.cols.map((c,i)=>'<option value="'+i+'"'+(i===sel?' selected':'')+'>'+esc(c)+'</option>').join('');h+=sec('Kolom koordinat','<div class="kv"><span>X / Easting</span><select id="cx">'+o(g.meta.map.x)+'</select><span>Y / Northing</span><select id="cy">'+o(g.meta.map.y)+'</select><span>Z / RL</span><select id="cz"><option value="-1">(tidak ada)</option>'+o(g.meta.map.z)+'</select></div>',false);}
 const cols=g.meta.cols,co=(sel,none)=>'<option value="-1">'+none+'</option>'+(cols||[]).map((c,i)=>'<option value="'+i+'"'+(i===sel?' selected':'')+'>'+esc(c)+'</option>').join('');
 h+=sec('Gaya','<div class="kv">'+(isVec(g)?'<span>Warna</span><input type="color" id="pcol" value="'+g.color+'">':'')+'<span>Opasitas</span><input type="range" id="pop" min="5" max="100" value="'+Math.round((g.opacity==null?1:g.opacity)*100)+'">'+
  (isVec(g)&&g.P.length?'<span>Tebal garis</span><input type="number" id="plw" min="0.5" max="10" step="0.5" value="'+s.lw+'"><span>Isi poligon</span><input type="range" id="pfill" min="0" max="100" value="'+Math.round(s.fill*100)+'">':'')+
  (isVec(g)&&g.PT.length?'<span>Ukuran titik</span><input type="number" id="ppt" min="1" max="20" step="0.5" value="'+s.pt+'">':'')+
  (isVec(g)&&cols?'<span>Label</span><select id="plab">'+co(s.label,'(tanpa label)')+'</select>':'')+(isVec(g)&&cols&&g.PT.length?'<span>Warna titik</span><select id="pcb">'+co(s.colorBy,'(warna lapisan)')+'</select>':'')+
  (g.dem?'<span>Tampilan</span><select id="pdm"><option value="hyps"'+(g.dem.mode==='hyps'?' selected':'')+'>Warna elevasi + bayangan</option><option value="gray"'+(g.dem.mode==='gray'?' selected':'')+'>Bayangan abu-abu</option><option value="flat"'+(g.dem.mode==='flat'?' selected':'')+'>Warna elevasi saja</option></select>':'')+'</div>'+(g.dem?'<div class="row" style="margin-top:6px"><button class="btn2" id="pcont">Buat kontur…</button></div>':''));
 if(isVec(g)&&g.V.length){const x=g.xf;h+=sec('Transformasi','<div class="row"><label><input type="checkbox" id="xsw" '+(x.swap?'checked':'')+'> Tukar X ↔ Y</label></div><div class="row"><label><input type="checkbox" id="xfz" '+(x.flipZ?'checked':'')+'> Balik tanda Z</label></div><div class="kv"><span>Geser X</span><input type="number" id="xdx" value="'+x.dx+'" step="any"><span>Geser Y</span><input type="number" id="xdy" value="'+x.dy+'" step="any"><span>Geser Z</span><input type="number" id="xdz" value="'+x.dz+'" step="any"></div><div class="row"><button class="btn2" id="xap">Terapkan</button><button class="btn2" id="xrs">Reset</button></div>',false);}
 P.innerHTML=h;const $i=(id)=>document.getElementById(id),on=(id,ev,fn)=>{const x=$i(id);if(x)x[ev]=fn;};
 on('pnm','onchange',(ev)=>{g.name=ev.target.value||g.name;renderTree();renderLegend();});
 if($i('cx'))for(const k of ['cx','cy','cz'])$i(k).onchange=()=>{try{GC.remapPoints(g,{x:+$i('cx').value,y:+$i('cy').value,z:+$i('cz').value});postVec(g,g.name);refreshAll();}catch(er){msg('Kolom: '+er.message,'e');}};
 on('xap','onclick',()=>{g.xf={swap:$i('xsw').checked,flipZ:$i('xfz').checked,dx:+$i('xdx').value||0,dy:+$i('xdy').value||0,dz:+$i('xdz').value||0};GC.applyXf(g);g._ms=undefined;refreshAll();msg('Transformasi diterapkan pada '+g.name+'.');});
 on('xrs','onclick',()=>{g.xf={swap:false,flipZ:false,dx:0,dy:0,dz:0};GC.applyXf(g);g._ms=undefined;refreshAll();});
 on('pcol','oninput',(ev)=>{g.color=ev.target.value;renderTree();renderLegend();M2.draw();V3.draw();});on('pop','oninput',(ev)=>{g.opacity=ev.target.value/100;M2.draw();V3.draw();});
 on('plw','oninput',(ev)=>{s.lw=+ev.target.value||1;M2.draw();});on('pfill','oninput',(ev)=>{s.fill=ev.target.value/100;M2.draw();});on('ppt','oninput',(ev)=>{s.pt=+ev.target.value||3;M2.draw();});
 on('plab','onchange',(ev)=>{s.label=+ev.target.value;M2.draw();});on('pcb','onchange',(ev)=>{s.colorBy=+ev.target.value;g._cb=null;M2.draw();});
 on('pdm','onchange',(ev)=>{g.dem.cv=demCanvas(g.dem,ev.target.value);M2.draw();});on('pcont','onclick',dlgContour);on('parea','onclick',()=>{S.view='pl';showTab('tbl');});
 if(f){$$('[data-fa]',P).forEach(inp=>inp.onchange=()=>{const k=+inp.dataset.fa;if(f.type==='pl'){const p=g.P[f.i];if(!p.attr)p.attr=cols.map(()=>'');p.attr[k]=inp.value;}else{if(!g.PA[f.i])g.PA[f.i]=cols.map(()=>'');g.PA[f.i][k]=inp.value;}M2.draw();if(S.tab==='tbl')renderTable();});
  on('fzoom','onclick',()=>{const p=g.P[f.i];let a=[Infinity,Infinity,-Infinity,-Infinity];for(const i of p.idx){a=[Math.min(a[0],g.V[3*i]),Math.min(a[1],g.V[3*i+1]),Math.max(a[2],g.V[3*i]),Math.max(a[3],g.V[3*i+1])];}M2.fitExt(a,0.7);});
  on('ftog','onclick',()=>{pushUndo(g,'ubah tipe');g.P[f.i].closed=!g.P[f.i].closed;changed(g);});on('fdel','onclick',delFeature);}
}
function delFeature(){const f=S.selF;if(!f||!(f.type==='pl'||f.type==='pt'))return false;const g=f.g;pushUndo(g,'hapus fitur');
 if(f.type==='pl')g.P.splice(f.i,1);else{const PT=Array.from(g.PT);PT.splice(f.i,1);g.PT=Uint32Array.from(PT);g.PA.splice(f.i,1);if(g.meta.raw)g.meta.raw=g.PA.slice();}
 M2.compact(g);S.selF=null;changed(g);msg('Fitur dihapus dari '+g.name+'.');return true;}
function changed(g){g._ms=undefined;g._bbV=null;g._cb=null;V3.rebuild(vecs().filter(x=>x.V.length));renderTree();renderProps();renderStatus();M2.draw();if(S.tab==='tbl')renderTable();}
function pushUndo(g,label){S.undo.push({id:g.id,snap:GC.snapshot(g),label:label});if(S.undo.length>40)S.undo.shift();}
function undo(){const u=S.undo.pop();if(!u){msg('Tidak ada yang bisa diurungkan.');return;}const g=gById(u.id);if(!g)return;GC.restore(g,u.snap);S.selF=null;changed(g);msg('Diurungkan: '+u.label+'.');}

/* ---------- digitasi ---------- */
function newDigit(ask){const nm=ask===false?'Digitasi':prompt('Nama lapisan digitasi','Digitasi '+(S.geoms.filter(g=>g.src==='digit').length+1));if(!nm)return null;const g=GC.mk({name:nm,src:'digit',meta:{cols:['NAMA','KET']}});S.geoms.unshift(g);g.base=nm;refreshAll();select(g.id);return g;}
function digitLayer(){const s=gById(S.sel);if(s&&s.src==='digit')return s;return S.geoms.find(g=>g.src==='digit')||newDigit(false);}
function onDigit(kind,pts){const g=digitLayer();pushUndo(g,'digitasi');let f;
 if(kind==='point'){const i=GC.addPoint(g,pts[0],['','']);f={g:g,type:'pt',i:i};}else{const n=g.P.length+1,i=GC.addPoly(g,pts,kind==='poly',[(kind==='poly'?'Poligon ':'Garis ')+n,'']);f={g:g,type:'pl',i:i};
  msg(kind==='poly'?'Poligon '+n+': luas '+M2.fmtArea(GC.polyArea(g.V,g.P[i].idx))+', keliling '+M2.fmtLen(GC.polyLen(g.V,g.P[i].idx,true)):'Garis '+n+': panjang '+M2.fmtLen(GC.polyLen(g.V,g.P[i].idx,false)));}
 g.visible=true;S.sel=g.id;S.selF=f;changed(g);renderLegend();}
function onPick(h,tool){if(!h){if(S.selF){S.selF=null;renderProps();M2.draw();}return;}S.selF=h;if(S.sel!==h.g.id)select(h.g.id,true);else{renderProps();M2.draw();}if(S.tab==='tbl')renderTable();}
function setTool(t){if(S.tab!=='2d')showTab('2d');M2.setTool(t);$$('#tb2 [data-tool]').forEach(b=>b.classList.toggle('on',b.dataset.tool===t));
 const tip={pan:'',info:'Klik fitur untuk melihat atribut, luas, atau elevasi.',dist:'Klik titik-titik; klik ganda untuk selesai.',area:'Klik sudut-sudut area; klik ganda untuk selesai.',poly:'Digit poligon: klik sudut-sudutnya, klik ganda / Enter untuk selesai. Luas tampil langsung.',line:'Digit garis: klik titik-titiknya, klik ganda / Enter untuk selesai.',point:'Klik untuk menaruh titik.',edit:'Klik poligon/garis, lalu seret kotak vertex. Bulatan = sisip titik. Delete = hapus.'}[t];$('#tip').textContent=tip;$('#tip').style.display=tip?'':'none';}
$('#tb2').onclick=(e)=>{const b=e.target.closest('button');if(!b)return;if(b.dataset.tool)setTool(b.dataset.tool);else if(b.dataset.v==='fit')M2.fit();else if(b.dataset.v==='layout')dlgLayout();};

/* ---------- Tabel atribut ---------- */
const R20=20;let TM=null;
function tableViews(g){const v=[];if(g.meta.tableOnly)v.push(['tbl','Tabel']);if(g.P.length)v.push(['pl','Garis / poligon (panjang & luas)']);if(g.PT.length&&g.meta.cols&&g.PA.length)v.push(['pt','Titik + atribut']);if(g.V.length)v.push(['vtx','Vertex']);if(g.F.length)v.push(['tri','Segitiga']);return v;}
function tableModel(g,view){const f3=(v)=>v.toFixed(3);
 if(view==='tbl')return {cols:g.meta.cols,n:g.meta.rows.length,row:(i)=>g.meta.rows[i]};
 if(view==='pt')return {cols:['#'].concat(g.meta.cols),n:g.PT.length,row:(i)=>[i+1].concat(g.PA[i]||[]),num:[0],pick:(i)=>({g:g,type:'pt',i:i})};
 if(view==='pl'){const ac=g.meta.cols&&!g.meta.map?g.meta.cols:[];return {cols:['#','Tipe','Titik','Panjang (m)','Luas (m²)','Luas (ha)'].concat(ac),n:g.P.length,row:(i)=>{const p=g.P[i],A=p.closed&&p.idx.length>2?GC.polyArea(g.V,p.idx):0;return [i+1,p.closed?'Poligon':'Garis',p.idx.length,GC.polyLen(g.V,p.idx,p.closed).toFixed(2),p.closed?A.toFixed(2):'',p.closed?(A/10000).toFixed(4):''].concat(ac.map((c,k)=>p.attr&&p.attr[k]!=null?p.attr[k]:''));},num:[0,2,3,4,5],pick:(i)=>({g:g,type:'pl',i:i}),sum:4};}
 if(view==='tri')return {cols:['#','V1','V2','V3','Z rata-rata'],n:g.F.length/3,row:(i)=>[i+1,g.F[3*i]+1,g.F[3*i+1]+1,g.F[3*i+2]+1,f3((g.V[3*g.F[3*i]+2]+g.V[3*g.F[3*i+1]+2]+g.V[3*g.F[3*i+2]+2])/3)],num:[0,1,2,3,4]};
 return {cols:['#','X','Y','Z'],n:g.V.length/3,row:(i)=>[i+1,f3(g.V[3*i]),f3(g.V[3*i+1]),f3(g.V[3*i+2])],num:[0,1,2,3]};}
function renderTable(){const g=gById(S.sel),bar=$('#tbar'),box=$('#tview');TM=null;
 if(!g||!isVec(g)){bar.innerHTML='<span class="hint" style="margin:0">Pilih lapisan vektor di panel Lapisan.</span>';box.innerHTML='';return;}
 const vs=tableViews(g);if(!vs.length){bar.innerHTML='<span class="hint" style="margin:0">Lapisan ini belum punya data.</span>';box.innerHTML='';return;}
 if(!S.view||!vs.some(v=>v[0]===S.view))S.view=vs[0][0];
 bar.innerHTML='<b>'+esc(g.name)+'</b><select id="tvs" style="width:auto">'+vs.map(v=>'<option value="'+v[0]+'"'+(v[0]===S.view?' selected':'')+'>'+v[1]+'</option>').join('')+'</select><input type="text" id="tfil" placeholder="Saring…" value="'+esc(S.tfilter)+'" style="width:160px"><span class="hint" id="tcnt" style="margin:0;flex:1"></span><button class="btn2" id="tcsv">Unduh CSV</button>';
 $('#tvs').onchange=(e)=>{S.view=e.target.value;renderTable();};$('#tfil').oninput=(e)=>{S.tfilter=e.target.value;applyFilter();};
 TM=tableModel(g,S.view);$('#tcsv').onclick=()=>{const O=[TM.cols.join(',')];for(const i of TM.idx)O.push(TM.row(i).map(v=>/[",\n]/.test(String(v))?'"'+String(v).replace(/"/g,'""')+'"':v).join(','));dl((g.base||g.name)+'_'+S.view+'.csv',O.join('\n')+'\n','text/csv');};
 box.innerHTML='<div id="tsp"></div><table><thead></thead><tbody></tbody></table>';applyFilter();}
function applyFilter(){if(!TM)return;const q=S.tfilter.trim().toLowerCase();TM.idx=[];if(!q||TM.n>300000){for(let i=0;i<TM.n;i++)TM.idx.push(i);}else for(let i=0;i<TM.n;i++){if(TM.row(i).some(v=>String(v).toLowerCase().indexOf(q)>=0))TM.idx.push(i);}
 let t=nf(TM.idx.length)+(TM.idx.length!==TM.n?' dari '+nf(TM.n):'')+' baris';if(TM.sum!==undefined){let s=0;for(const i of TM.idx)s+=+TM.row(i)[TM.sum]||0;t+='  ·  total luas '+nf(s,2)+' m² ('+nf(s/10000,4)+' ha)';}
 $('#tcnt').textContent=t;$('#tsp').style.height=(TM.idx.length*R20+24)+'px';$('#tview').scrollTop=0;drawRows();}
function drawRows(){if(!TM)return;const box=$('#tview'),tb=$('#tview table'),vis=Math.ceil(box.clientHeight/R20)+4,st=Math.max(0,Math.floor(box.scrollTop/R20)-1),en=Math.min(TM.idx.length,st+vis),num=new Set(TM.num||[]),sf=S.selF&&TM.pick?S.selF:null;
 tb.querySelector('thead').innerHTML='<tr>'+TM.cols.map((c,i)=>'<th'+(num.has(i)?' class="n"':'')+'>'+esc(c)+'</th>').join('')+'</tr>';let h='';
 for(let q=st;q<en;q++){const i=TM.idx[q],r=TM.row(i),on=sf&&sf.i===i&&TM.pick(i).type===sf.type;h+='<tr data-r="'+i+'"'+(on?' class="sel"':'')+'>'+TM.cols.map((c,k)=>'<td'+(num.has(k)?' class="n"':'')+'>'+esc(r[k])+'</td>').join('')+'</tr>';}
 tb.querySelector('tbody').innerHTML=h;tb.style.top=(st*R20)+'px';}
$('#tview').addEventListener('scroll',()=>drawRows());
$('#tview').addEventListener('click',(e)=>{const tr=e.target.closest('tr[data-r]');if(!tr||!TM||!TM.pick)return;S.selF=TM.pick(+tr.dataset.r);renderProps();drawRows();M2.draw();});
$('#tview').addEventListener('dblclick',(e)=>{const tr=e.target.closest('tr[data-r]');if(!tr||!TM||!TM.pick)return;const f=TM.pick(+tr.dataset.r),g=f.g;let a=[Infinity,Infinity,-Infinity,-Infinity];for(const i of (f.type==='pl'?g.P[f.i].idx:[g.PT[f.i]])){a=[Math.min(a[0],g.V[3*i]),Math.min(a[1],g.V[3*i+1]),Math.max(a[2],g.V[3*i]),Math.max(a[3],g.V[3*i+1])];}showTab('2d');if(a[2]-a[0]<1&&a[3]-a[1]<1)a=[a[0]-25,a[1]-25,a[2]+25,a[3]+25];M2.fitExt(a,0.7);});

/* ---------- tab ---------- */
function showTab(t){S.tab=t;$$('.tab').forEach(b=>b.classList.toggle('on',b.dataset.t===t));$('#p2d').classList.toggle('on',t==='2d');$('#p3d').classList.toggle('on',t==='3d');$('#pt').classList.toggle('on',t==='tbl');$('#pc').classList.toggle('on',t==='conv');
 if(t==='2d'){$('#p2d').append($('#legend'));M2.resize();}else if(t==='3d'){$('#p3d').append($('#legend'));V3.resize();if(!S._fit3){S._fit3=true;V3.fit();}}else if(t==='tbl')renderTable();else renderConv();}
$$('.tab').forEach(b=>b.onclick=()=>showTab(b.dataset.t));

/* ---------- Konversi ---------- */
const SOFTS=['Semua','Leapfrog','Surpac','MapInfo','Global Mapper','Google Earth'];
const SOFTHINT={'Semua':'Pilih tujuan software untuk melihat format yang disarankan, atau langsung pilih format.','Leapfrog':'Mesh: MSH atau OBJ. Garis dan titik: DXF atau CSV.','Surpac':'Permukaan/solid: DTM + STR (dibuka bersama). String: STR. Umum: DXF.','MapInfo':'Impor MIF/MID lalu simpan sebagai TAB. SHP dan DXF juga terbuka. MapInfo 2D: Z jadi kolom atribut.','Global Mapper':'SHP (membawa Z dan atribut), DXF, KML, GeoJSON, GeoTIFF DEM, CSV.','Google Earth':'KML atau KMZ (lintang/bujur WGS84; perlu sistem koordinat proyek).'};
const srcFor=(f)=>S.geoms.filter(g=>FMT[f].dem?!!g.dem:isVec(g));
const convGeoms=()=>srcFor(C.fmt).filter(g=>!C.off.has(g.id));
function planInfo(){const gs=convGeoms(),f=C.fmt,out=[];let nt=0,np=0,npt=0,big=false;
 if(FMT[f].dem){if(!gs.length)out.push(['e','Format ini hanya untuk lapisan DEM. Buat dulu lewat Analisis → Buat DEM dari topografi.']);else out.push(['i','Siap: '+gs.length+' DEM.']);if(f==='tif'&&!S.crs)out.push(['w','Sistem koordinat proyek belum ditentukan; GeoTIFF ditulis tanpa kode EPSG.']);return out;}
 for(const g of gs){nt+=g.F.length/3;np+=g.P.length;npt+=g.PT.length;if(!big)for(let i=0;i<g.V.length;i+=3)if(Math.abs(g.V[i])>1e5){big=true;break;}}
 if(!gs.length){out.push(['e','Pilih minimal satu lapisan vektor di kolom Sumber.']);return out;}
 if(['msh','stl','stlb','ply','dtm'].indexOf(f)>=0){if(!nt)out.push(['e',FMT[f].label+' hanya menyimpan mesh segitiga; lapisan terpilih tidak punya segitiga.']);else if(np||npt)out.push(['w','Garis dan titik tidak ikut ditulis (hanya mesh).']);}
 if(f==='dtm'&&nt)out.push(['i','Menghasilkan pasangan .dtm + .str per lapisan mesh; keduanya dibuka bersama di Surpac.']);
 if(f==='str'){if(!np&&!npt)out.push(['e','STR menyimpan garis/titik. Untuk mesh pilih Surpac DTM + STR.']);else if(nt)out.push(['w','Mesh tidak ditulis ke STR.']);}
 if(f==='csv'&&(nt||np))out.push(['w','CSV hanya memuat koordinat vertex; hubungan segitiga/garis hilang.']);
 if(f==='mif')out.push(['w','MapInfo 2D: Z disimpan sebagai kolom atribut.']);
 if(f==='shp')out.push(['i','Satu shapefile per tipe geometri (poligon/garis/titik), membawa atribut, luas, dan panjang; dikemas ZIP.']);
 if((f==='kml'||f==='kmz')&&!S.crs)out.push(['e','KML memakai lintang/bujur: tentukan dulu sistem koordinat proyek (Proyek → Sistem koordinat).']);
 if((f==='shp'||f==='mif'||f==='geojson')&&!S.crs)out.push(['w','Sistem koordinat proyek belum ditentukan; hasil tanpa informasi proyeksi.']);
 if(f==='stlb'&&big)out.push(['w','Koordinat UTM: float32 mengurangi presisi hingga ±1 m. Pakai STL ASCII bila presisi penting.']);
 if(!out.length)out.push(['i','Siap: '+gs.length+' lapisan, '+nf(nt)+' segitiga, '+nf(np)+' garis/poligon, '+nf(npt)+' titik.']);return out;}
function renderConv(){const P=$('#pc'),sc=P.scrollTop,rec=GC.SOFT[C.soft]||[],L=srcFor(C.fmt);
 const src=L.length?L.map(g=>'<div class="row"><input type="checkbox" data-cs="'+g.id+'" '+(C.off.has(g.id)?'':'checked')+' id="cs'+g.id+'"><span class="sw" style="background:'+(g.dem?'#8FAA68':g.color)+'"></span><label for="cs'+g.id+'" title="'+esc(g.name)+'">'+esc(g.name)+' <span style="color:var(--sub)">'+esc(badge(g))+'</span></label></div>').join(''):'<div class="empty" style="padding:0">'+(FMT[C.fmt].dem?'Belum ada lapisan DEM.':'Belum ada lapisan vektor. Buka file dulu.')+'</div>';
 const fm=wfmt().map(f=>'<div class="fmt'+(f.id===C.fmt?' on':'')+'" data-fm="'+f.id+'"><input type="radio" name="fmt" '+(f.id===C.fmt?'checked':'')+' aria-label="'+esc(f.label)+'"><div><b>'+esc(f.label)+(rec.indexOf(f.id)>=0?' <span class="bd" style="color:var(--gold)">· disarankan</span>':'')+'</b><small>'+esc(f.note)+'</small></div></div>').join('');
 const multi=new Set(convGeoms().map(g=>g.base||g.name)).size>1,pl=planInfo();
 P.innerHTML='<div id="cgrid"><div class="cc"><div class="ch">1 · Sumber</div><div class="cb">'+src+(L.length?'<div class="row" style="margin-top:6px"><button class="btn2" id="call">Semua</button><button class="btn2" id="cnone">Kosongkan</button></div>':'')+'<p class="hint">Citra (ortofoto) tidak dikonversi. DEM hanya ke GeoTIFF / ASC / grid XYZ.</p></div></div>'+
 '<div class="cc"><div class="ch">2 · Tujuan</div><div class="cb"><div class="chips">'+SOFTS.map(s=>'<button class="chip'+(C.soft===s?' on':'')+'" data-soft="'+s+'">'+s+'</button>').join('')+'</div><div class="hint">'+esc(SOFTHINT[C.soft])+'</div>'+fm+'</div></div>'+
 '<div class="cc"><div class="ch">3 · Opsi &amp; unduh</div><div class="cb"><div class="fr"><span>Nama file</span><input type="text" id="cbase" placeholder="otomatis" value="'+esc(C.base)+'"></div><div class="fr"><span>Desimal</span><input type="number" id="cdec" min="0" max="8" value="'+C.dec+'"></div>'+
 (C.fmt==='csv'||C.fmt==='xyz'?'<div class="fr"><span>Pemisah</span><select id="csep"><option value=","'+(C.sep===','?' selected':'')+'>koma ( , )</option><option value=";"'+(C.sep===';'?' selected':'')+'>titik koma ( ; )</option><option value="tab"'+(C.sep==='tab'?' selected':'')+'>tab</option></select></div>':'')+
 (multi?'<div class="fr"><span>Banyak file</span><select id="cmode"><option value="auto"'+(C.mode==='auto'?' selected':'')+'>Per file sumber</option><option value="merge"'+(C.mode==='merge'?' selected':'')+'>Gabung jadi satu</option></select></div>':'')+
 '<div class="fr"><span>Koordinat</span><span><a href="#" id="ccrs">'+esc(GC.crsName(S.crs))+'</a></span></div>'+
 '<div class="plan">'+pl.map(p=>'<div class="'+(p[0]==='w'?'w':p[0]==='e'?'e':'')+'">'+(p[0]==='w'?'⚠ ':p[0]==='e'?'✕ ':'')+esc(p[1])+'</div>').join('')+'</div><button class="btn" id="cgo"'+(pl.some(p=>p[0]==='e')?' disabled':'')+'>Konversi &amp; unduh</button></div></div></div>';
 P.scrollTop=sc;
 $$('[data-cs]',P).forEach(c=>c.onchange=()=>{const id=+c.dataset.cs;if(c.checked)C.off.delete(id);else C.off.add(id);renderConv();});
 if($('#call'))$('#call').onclick=()=>{C.off.clear();renderConv();};if($('#cnone'))$('#cnone').onclick=()=>{S.geoms.forEach(g=>C.off.add(g.id));renderConv();};
 $$('[data-soft]',P).forEach(b=>b.onclick=()=>{C.soft=b.dataset.soft;const r=GC.SOFT[C.soft];if(r&&r.indexOf(C.fmt)<0)C.fmt=r[0];renderConv();});$$('[data-fm]',P).forEach(b=>b.onclick=()=>{C.fmt=b.dataset.fm;renderConv();});
 $('#cbase').onchange=(e)=>{C.base=e.target.value.replace(/[\\\/:*?"<>|]/g,'_');};$('#cdec').onchange=(e)=>{C.dec=Math.max(0,Math.min(8,+e.target.value||0));};
 if($('#csep'))$('#csep').onchange=(e)=>{C.sep=e.target.value;};if($('#cmode'))$('#cmode').onchange=(e)=>{C.mode=e.target.value;};$('#ccrs').onclick=(e)=>{e.preventDefault();dlgCRS();};
 $('#cgo').onclick=()=>runConvert(C.fmt,convGeoms(),null);}
function groupsFor(gs,forceBase){if(forceBase)return [{base:forceBase,geoms:gs}];const bases=Array.from(new Set(gs.map(g=>g.base||g.name)));
 if(bases.length>1&&C.mode==='auto')return bases.map(b=>({base:b,geoms:gs.filter(g=>(g.base||g.name)===b)}));return [{base:C.base||(bases.length===1?bases[0]:'konversi'),geoms:gs}];}
function runConvert(fmt,gs,forceBase){gs=gs.filter(g=>FMT[fmt].dem?!!g.dem:isVec(g));if(!gs.length){msg('Tidak ada lapisan yang cocok untuk '+FMT[fmt].label+'.','e');return;}
 const out=[];let warns=[];const gr=groupsFor(gs,forceBase);
 try{for(const grp of gr){const r=GC.write(fmt,grp.geoms,{base:grp.base,dec:C.dec,sep:C.sep==='tab'?'\t':C.sep,utm:S.crs});out.push(...r.files);warns.push(...r.warn);}}catch(e){msg('Gagal konversi ke '+FMT[fmt].label+': '+e.message,'e');return;}
 Array.from(new Set(warns)).forEach(w=>msg(w,'w'));
 if(out.length===1){dl(out[0].name,out[0].data);msg('Selesai: '+out[0].name+' ('+nf(out[0].data.length/1024)+' KB)');}
 else{const nm=(gr.length>1?(C.base||'konversi'):out[0].name.replace(/\.[^.]+$/,'').replace(/_(garis_tertutup|garis|titik|poligon)$/,''))+'_'+fmt+'.zip';dl(nm,GC.zip(out),'application/zip');msg('Selesai: '+nm+' ('+out.length+' file: '+out.map(f=>f.name).join(', ')+')');}}
function quickExport(fmt,gs,base){gs=gs.filter(Boolean);if(!gs.length){msg('Tidak ada lapisan terpilih.','w');return;}runConvert(fmt,gs,base||(gs.length===1?(gs[0].base&&gs[0].base!==gs[0].name?gs[0].base+'_'+gs[0].name:gs[0].name):C.base||'konversi'));}

/* ---------- Analisis: DEM & kontur ---------- */
function dlgDEM(){const L=vecs().filter(g=>g.V.length);
 const m=modal('Buat DEM dari topografi','<p class="hint">Titik, string, atau mesh berelevasi ditriangulasi (TIN, cara DTM Surpac), lalu dijadikan grid elevasi. String dirapatkan agar bentuk jenjang terjaga.</p><div class="ch2">Sumber</div>'+L.map(g=>{const b=GC.bbox(g),flat=b.max[2]-b.min[2]<1e-6;return '<div class="row"><label><input type="checkbox" data-ds="'+g.id+'" '+(g.visible&&!flat&&g.src!=='digit'&&g.src!=='kontur'?'checked':'')+'> '+esc(g.name)+' <span style="color:var(--sub)">'+esc(badge(g))+' · Z '+nf(b.min[2],1)+' s/d '+nf(b.max[2],1)+(flat?' (datar)':'')+'</span></label></div>';}).join('')+
 '<div class="fr" style="margin-top:8px"><span>Ukuran sel (m)</span><input type="number" id="dcell" min="0.05" step="any" placeholder="otomatis"></div><div class="fr"><span>Rapatkan string (m)</span><input type="number" id="dstep" value="2" min="0" step="any"></div><div class="fr"><span>Buang segitiga tepi</span><select id="dfac"><option value="8">lebih panjang dari 8 × median (bawaan)</option><option value="4">4 × median</option><option value="16">16 × median</option><option value="0">jangan dibuang</option></select></div><div class="fr"><span>Kontur (m)</span><input type="number" id="dci" min="0" step="any" placeholder="kosong = tanpa kontur"></div><div class="row"><label><input type="checkbox" id="dtin" checked> Simpan juga TIN sebagai lapisan mesh (bisa diekspor ke DTM Surpac / DXF)</label></div><div class="row"><button class="btn" id="dgo">Buat DEM</button><span class="hint" id="dinfo" style="margin:0"></span></div>');
 $('#dgo',m).onclick=async()=>{const src=$$('[data-ds]',m).filter(c=>c.checked).map(c=>gById(+c.dataset.ds));if(!src.length){$('#dinfo',m).textContent='Pilih minimal satu sumber.';return;}$('#dinfo',m).textContent='Menghitung…';await new Promise(r=>setTimeout(r,30));
  try{const t0=performance.now(),tin=GC.buildTIN(src,{step:+$('#dstep',m).value||0,factor:+$('#dfac',m).value}),cell=+$('#dcell',m).value||GC.niceCell(tin,1500),dem=GC.tinToDEM(tin,cell),nm=src.length===1?src[0].name:'Topografi';
   const g=GC.mk({name:'DEM '+nm,src:'dem'});g.dem=dem;dem.cv=demCanvas(dem,'hyps');g.base='DEM_'+(src[0].base||nm);g.file='(dari '+src.map(x=>x.name).join(', ')+')';
   if($('#dtin',m).checked&&tin.src!=='mesh'){const t=GC.tinGeom(tin,'TIN '+nm);t.base='TIN_'+(src[0].base||nm);t.file=g.file;t.visible=false;S.geoms.push(t);}
   const ci=+$('#dci',m).value;if(ci>0){const c=GC.contours(dem,ci,'Kontur '+ci+' m '+nm);c.base='Kontur_'+(src[0].base||nm);c.file=g.file;c.color='#7A5A3A';M2.sty(c).lw=1;M2.sty(c).fill=0;S.geoms.unshift(c);}
   const i=Math.max(...src.map(x=>S.geoms.indexOf(x)));S.geoms.splice(i+1,0,g);m.remove();refreshAll();select(g.id);showTab('2d');
   msg('DEM dibuat: '+nf(tin.X.length)+' titik, '+nf(tin.T.length/3)+' segitiga'+(tin.dropped?' ('+nf(tin.dropped)+' segitiga tepi dibuang)':'')+', grid '+dem.nx+' × '+dem.ny+' sel '+cell+' m, elevasi '+nf(dem.min,2)+' s/d '+nf(dem.max,2)+' m ('+Math.round(performance.now()-t0)+' ms)');}
  catch(e){$('#dinfo',m).textContent=e.message;msg('DEM: '+e.message,'e');}};}
function dlgContour(){const L=S.geoms.filter(g=>g.dem),cur=gById(S.sel),def=cur&&cur.dem?cur:L[0];if(!def)return;const rg=def.dem.max-def.dem.min,sug=M2.nice(rg/15);
 const m=modal('Buat kontur dari DEM','<div class="fr"><span>DEM</span><select id="kd">'+L.map(g=>'<option value="'+g.id+'"'+(g===def?' selected':'')+'>'+esc(g.name)+'</option>').join('')+'</select></div><div class="fr"><span>Interval (m)</span><input type="number" id="ki" value="'+sug+'" min="0.01" step="any"></div><p class="hint">Hasil berupa lapisan garis ber-Z dengan atribut ELEV; bisa diekspor ke DXF, STR, SHP, atau KML.</p><div class="row"><button class="btn" id="kgo">Buat kontur</button><span class="hint" id="kinfo" style="margin:0"></span></div>');
 $('#kgo',m).onclick=()=>{try{const g=gById(+$('#kd',m).value),iv=+$('#ki',m).value,c=GC.contours(g.dem,iv,'Kontur '+iv+' m '+g.name.replace(/^DEM /,''));c.base='Kontur_'+(g.base||g.name);c.file='(dari '+g.name+')';c.color='#7A5A3A';M2.sty(c).lw=1;M2.sty(c).fill=0;S.geoms.splice(Math.max(0,S.geoms.indexOf(g)),0,c);m.remove();refreshAll();select(c.id);msg('Kontur dibuat: '+nf(c.P.length)+' garis, interval '+iv+' m.');}catch(e){$('#kinfo',m).textContent=e.message;}};}

/* ---------- Layout peta ---------- */
const niceDown=(v)=>{const p=Math.pow(10,Math.floor(Math.log10(v))),m=v/p;return (m>=5?5:m>=2?2:1)*p;};
const PAPER={A4:[297,210],A3:[420,297],A2:[594,420],A1:[841,594]},SCALES=[100,200,250,500,750,1000,1250,1500,2000,2500,4000,5000,7500,10000,12500,15000,20000,25000,50000,75000,100000,250000];
const LY={paper:'A3',land:true,scale:0,dpi:150,title:'PETA',sub:'',by:'',no:'',note:'',grid:true,legend:true};
function layoutGeom(c){const p=PAPER[c.paper],W=c.land?p[0]:p[1],H=c.land?p[1]:p[0],m=8,pw=c.land?64:0,ph=c.land?0:58;return {W:W,H:H,m:m,fx:m,fy:m,fw:W-2*m-(pw?pw+3:0),fh:H-2*m-(ph?ph+3:0),px:pw?W-m-pw:m,py:pw?m:H-m-ph,pw:pw||W-2*m,ph:pw?H-2*m:ph};}
function autoScale(c){const G=layoutGeom(c),v=M2.view,sz=M2.size(),need=Math.max(sz[0]/v.s/(G.fw/1000),sz[1]/v.s/(G.fh/1000));for(const s of SCALES)if(s>=need*0.98)return s;return Math.ceil(need/50000)*50000;}
async function renderLayout(c,dpi,hires){const G=layoutGeom(c),k=dpi/25.4,cv=document.createElement('canvas');cv.width=Math.round(G.W*k);cv.height=Math.round(G.H*k);const x=cv.getContext('2d'),sc=c.scale||autoScale(c),pt=(p)=>p/72*dpi;
 x.fillStyle='#fff';x.fillRect(0,0,cv.width,cv.height);const tf={cx:M2.view.cx,cy:M2.view.cy,s:k*1000/sc,W:G.fw*k,H:G.fh*k},L=S.geoms.filter(g=>g.visible),saved=[];
 if(hires)for(const g of L)if(g.ras&&g.ras.lv){try{const e=[tf.cx-tf.W/2/tf.s,tf.cy-tf.H/2/tf.s,tf.cx+tf.W/2/tf.s,tf.cy+tf.H/2/tf.s],d=await readDetail(g,e,4096);saved.push([g,g.ras.detail]);if(d)g.ras.detail=d;}catch(e){}}
 x.save();x.beginPath();x.rect(G.fx*k,G.fy*k,tf.W,tf.H);x.clip();x.translate(G.fx*k,G.fy*k);M2.drawLayers(x,tf,{px:dpi/110,layers:S.geoms});
 let step=0;if(c.grid)step=M2.drawGrid(x,tf,{px:dpi/96,step:M2.nice(55*sc/1000),both:true,suffix:true,color:'rgba(0,0,0,.28)',text:'#111',font:8.5,lw:0.5});x.restore();
 saved.forEach(s=>s[0].ras.detail=s[1]);
 x.strokeStyle='#111';x.lineWidth=0.5*k;x.strokeRect(G.fx*k,G.fy*k,tf.W,tf.H);x.strokeRect(G.px*k,G.py*k,G.pw*k,G.ph*k);x.lineWidth=0.25*k;x.strokeRect(3*k,3*k,(G.W-6)*k,(G.H-6)*k);
 /* panel */
 const X0=G.px*k,Y0=G.py*k,PW=G.pw*k,pad=3.5*k;x.fillStyle='#111';x.textBaseline='alphabetic';x.textAlign='left';
 const font=(p,b)=>{x.font=(b?'700 ':'')+pt(p)+'px "Segoe UI",Arial,sans-serif';};
 const wrap=(t,xx,yy,w,lh)=>{const ws=String(t).split(/\s+/);let ln='';for(const wd of ws){if(x.measureText(ln+' '+wd).width>w&&ln){x.fillText(ln,xx,yy);yy+=lh;ln=wd;}else ln=ln?ln+' '+wd:wd;}if(ln){x.fillText(ln,xx,yy);yy+=lh;}return yy;};
 const rule=(yy)=>{x.strokeStyle='#111';x.lineWidth=0.25*k;x.beginPath();x.moveTo(X0,yy);x.lineTo(X0+PW,yy);x.stroke();};
 const block=(x0,w,y0)=>{let y=y0+pad+pt(13);font(13,true);y=wrap(c.title||'PETA',x0+pad,y,w-2*pad,pt(15));if(c.sub){font(9);y=wrap(c.sub,x0+pad,y+pt(1),w-2*pad,pt(11));}return y;};
 const scaleBlk=(x0,w,y)=>{x.save();x.translate(x0+pad+5*k,y+9*k);x.beginPath();x.moveTo(0,-7*k);x.lineTo(3.2*k,4*k);x.lineTo(0,1.5*k);x.lineTo(-3.2*k,4*k);x.closePath();x.fill();font(8,true);x.textAlign='center';x.fillText('U',0,8.5*k);x.restore();x.textAlign='left';
  font(10,true);x.fillText('SKALA 1 : '+nf(sc),x0+pad+14*k,y+6*k);const m=niceDown(Math.min(38,(w/k)-22)*sc/1000),bw=m*1000/sc*k,bx=x0+pad+14*k,by=y+12*k;x.fillRect(bx,by,bw,0.8*k);for(let i=0;i<=4;i++)x.fillRect(bx+bw*i/4-0.1*k,by-1.2*k,0.25*k,2*k);x.fillRect(bx,by,bw/4,0.8*k);font(7.5);x.textAlign='center';x.fillText('0',bx,by-2*k);x.fillText(m>=1000?m/1000+' km':m+' m',bx+bw,by-2*k);x.fillText(String(m/2>=1000?m/2000:m/2),bx+bw/2,by-2*k);x.textAlign='left';return y+18*k;};
 const legendBlk=(x0,w,y,maxY)=>{font(8.5,true);x.fillText('LEGENDA',x0+pad,y+pt(9));y+=pt(9)+2*k;font(8);const lh=4.6*k;
  for(const g of L){if(y+lh>maxY){x.fillText('…',x0+pad,y+3*k);break;}const sx=x0+pad,sy=y+0.8*k,sw=7*k,sh=3.2*k,col=g.color;x.lineWidth=0.4*k;
   if(g.ras){x.fillStyle='#bbb';x.fillRect(sx,sy,sw,sh);}else if(g.dem){const gr=x.createLinearGradient(sx,0,sx+sw,0);gr.addColorStop(0,'#3E7A5E');gr.addColorStop(0.5,'#DECD8C');gr.addColorStop(1,'#B08054');x.fillStyle=gr;x.fillRect(sx,sy,sw,sh);}
   else if(g.F.length||(M2.sty(g).fill>0&&g.P.some(p=>p.closed))){x.globalAlpha=g.F.length?0.35:Math.max(0.15,M2.sty(g).fill);x.fillStyle=col;x.fillRect(sx,sy,sw,sh);x.globalAlpha=1;x.strokeStyle=col;x.strokeRect(sx,sy,sw,sh);}
   else if(g.P.length){x.strokeStyle=col;x.lineWidth=0.6*k;x.beginPath();x.moveTo(sx,sy+sh/2);x.lineTo(sx+sw,sy+sh/2);x.stroke();}else{x.fillStyle=col;x.beginPath();x.arc(sx+sw/2,sy+sh/2,1.2*k,0,6.2832);x.fill();}
   x.fillStyle='#111';let t=g.name;while(x.measureText(t).width>w-2*pad-9*k&&t.length>4)t=t.slice(0,-2);x.fillText(t+(t!==g.name?'…':''),sx+sw+2*k,y+3.6*k);y+=lh;}return y;};
 const infoBlk=(x0,w,y)=>{const rows=[['Sistem koordinat',GC.crsName(S.crs)],['Grid',step?nf(step)+' m':'–'],['Dibuat oleh',c.by||'–'],['Tanggal',new Date().toLocaleDateString('id-ID',{day:'2-digit',month:'long',year:'numeric'})],['No. peta',c.no||'–']];if(c.note)rows.push(['Catatan',c.note]);
  for(const r of rows){font(7);x.fillStyle='#555';x.fillText(r[0],x0+pad,y+pt(7));font(8.5);x.fillStyle='#111';y=wrap(r[1],x0+pad,y+pt(7)+pt(9.5),w-2*pad,pt(10))-pt(10)+1.8*k;}return y;};
 if(c.land){let y=block(X0,PW,Y0);rule(y+1*k);y=scaleBlk(X0,PW,y+2.5*k);rule(y);const ib=Y0+G.ph*k-(c.note?50:42)*k;if(c.legend)legendBlk(X0,PW,y+1.5*k,ib-2*k);rule(ib);infoBlk(X0,PW,ib+1*k);}
 else{const w3=PW/3;block(X0,w3,Y0);scaleBlk(X0,w3,Y0+G.ph*k-22*k);x.lineWidth=0.25*k;x.beginPath();x.moveTo(X0+w3,Y0);x.lineTo(X0+w3,Y0+G.ph*k);x.moveTo(X0+2*w3,Y0);x.lineTo(X0+2*w3,Y0+G.ph*k);x.stroke();if(c.legend)legendBlk(X0+w3,w3,Y0+1.5*k,Y0+G.ph*k-2*k);infoBlk(X0+2*w3,w3,Y0+1*k);}
 return {cv:cv,G:G,scale:sc};}
function dlgLayout(){if(S.tab!=='2d')showTab('2d');LY.by=LY.by||store.get('gc_by','');
 const m=modal('Layout peta','<div class="lyo"><div class="lyf"><p class="hint">Peta dicetak pada <b>pusat tampilan 2D saat ini</b>. Geser/zoom peta dulu, lalu buka dialog ini.</p><div class="fr"><span>Kertas</span><span style="display:flex;gap:6px"><select id="lp">'+Object.keys(PAPER).map(p=>'<option'+(p===LY.paper?' selected':'')+'>'+p+'</option>').join('')+'</select><select id="lo"><option value="1"'+(LY.land?' selected':'')+'>Mendatar</option><option value="0"'+(LY.land?'':' selected')+'>Tegak</option></select></span></div><div class="fr"><span>Skala</span><select id="lsc"><option value="0">Otomatis (muat tampilan)</option>'+SCALES.map(s=>'<option value="'+s+'"'+(s===LY.scale?' selected':'')+'>1 : '+nf(s)+'</option>').join('')+'</select></div><div class="fr"><span>Judul</span><input type="text" id="lt" value="'+esc(LY.title)+'"></div><div class="fr"><span>Subjudul</span><input type="text" id="ls" value="'+esc(LY.sub)+'"></div><div class="fr"><span>Dibuat oleh</span><input type="text" id="lb" value="'+esc(LY.by)+'"></div><div class="fr"><span>No. peta</span><input type="text" id="ln" value="'+esc(LY.no)+'"></div><div class="fr"><span>Catatan</span><input type="text" id="lnt" value="'+esc(LY.note)+'"></div><div class="row"><label><input type="checkbox" id="lg" '+(LY.grid?'checked':'')+'> Grid koordinat</label><label><input type="checkbox" id="ll" '+(LY.legend?'checked':'')+'> Legenda</label></div><div class="fr"><span>Resolusi</span><select id="ld">'+[100,150,200,300].map(d=>'<option value="'+d+'"'+(d===LY.dpi?' selected':'')+'>'+d+' dpi</option>').join('')+'</select></div><div class="row" style="margin-top:8px"><button class="btn" id="lpdf">Unduh PDF</button><button class="btn2" id="lpng">Unduh PNG</button></div><p class="hint" id="linfo"></p></div><div class="lyp"><canvas id="lcv"></canvas></div></div>',true);
 const rd=()=>{LY.paper=$('#lp',m).value;LY.land=$('#lo',m).value==='1';LY.scale=+$('#lsc',m).value;LY.title=$('#lt',m).value;LY.sub=$('#ls',m).value;LY.by=$('#lb',m).value;LY.no=$('#ln',m).value;LY.note=$('#lnt',m).value;LY.grid=$('#lg',m).checked;LY.legend=$('#ll',m).checked;LY.dpi=+$('#ld',m).value;store.set('gc_by',LY.by);};
 let tk=0;const prev=async()=>{rd();const t=++tk,r=await renderLayout(LY,60,false);if(t!==tk||!m.isConnected)return;const c=$('#lcv',m);c.width=r.cv.width;c.height=r.cv.height;c.getContext('2d').drawImage(r.cv,0,0);$('#linfo',m).textContent='Skala 1 : '+nf(r.scale)+' · '+LY.paper+' '+r.G.W+' × '+r.G.H+' mm';};
 $$('input,select',m).forEach(i=>i.addEventListener('input',()=>{clearTimeout(prev.t);prev.t=setTimeout(prev,200);}));prev();
 const out=async(kind)=>{rd();$('#linfo',m).textContent='Menyusun halaman…';await new Promise(r=>setTimeout(r,30));let dpi=LY.dpi;const p=PAPER[LY.paper];while(p[0]*p[1]/645.16*dpi*dpi>90e6&&dpi>72)dpi-=25;
  try{const r=await renderLayout(LY,dpi,true),nm=(LY.title||'peta').replace(/[\\\/:*?"<>|]+/g,'_').trim()||'peta';
   if(kind==='png')r.cv.toBlob(b=>dl(nm+'.png',b),'image/png');else dl(nm+'.pdf',GC.pdfFromJpeg(dataUrlBytes(r.cv.toDataURL('image/jpeg',0.93)),r.cv.width,r.cv.height,r.G.W,r.G.H),'application/pdf');
   $('#linfo',m).textContent='Selesai: skala 1 : '+nf(r.scale)+', '+dpi+' dpi.';msg('Layout peta '+kind.toUpperCase()+': '+nm+', '+LY.paper+', skala 1:'+nf(r.scale)+', '+dpi+' dpi.');}catch(e){$('#linfo',m).textContent=e.message;msg('Layout: '+e.message,'e');}};
 $('#lpdf',m).onclick=()=>out('pdf');$('#lpng',m).onclick=()=>out('png');}

/* ---------- 3D toolbar, pembagi panel, seret-lepas, tombol ---------- */
$('#tb3').onclick=(e)=>{const b=e.target.closest('button');if(!b)return;const v=b.dataset.v;if(v==='fit')V3.fit();else if(v==='ortho'){V3.setOrtho(!V3.getOrtho());b.classList.toggle('on',V3.getOrtho());}else V3.preset(v);};
(function(){let w=null;const drag=(id,dock,dir)=>{$(id).addEventListener('pointerdown',(e)=>{w={d:$(dock),x:e.clientX,w0:$(dock).offsetWidth,dir:dir};$(id).setPointerCapture(e.pointerId);});
 $(id).addEventListener('pointermove',(e)=>{if(!w||w.d!==$(dock))return;w.d.style.width=Math.max(180,Math.min(560,w.w0+(e.clientX-w.x)*w.dir))+'px';M2.resize();V3.resize();});$(id).addEventListener('pointerup',()=>{w=null;});};drag('#sp1','#left',1);drag('#sp2','#right',-1);})();
let dc=0;const isFileDrag=(e)=>e.dataTransfer&&Array.from(e.dataTransfer.types||[]).indexOf('Files')>=0;
addEventListener('dragenter',(e)=>{if(!isFileDrag(e))return;e.preventDefault();dc++;$('#drop').classList.add('on');});addEventListener('dragover',(e)=>{if(isFileDrag(e))e.preventDefault();});
addEventListener('dragleave',(e)=>{if(!isFileDrag(e))return;if(--dc<=0){dc=0;$('#drop').classList.remove('on');}});
addEventListener('drop',(e)=>{if(!isFileDrag(e))return;e.preventDefault();dc=0;$('#drop').classList.remove('on');if(e.dataTransfer.files.length)loadFiles(e.dataTransfer.files);});
$('#fin').onchange=(e)=>{if(e.target.files.length)loadFiles(e.target.files);e.target.value='';};
addEventListener('keydown',(e)=>{const typing=/INPUT|SELECT|TEXTAREA/.test(document.activeElement.tagName);
 if((e.ctrlKey||e.metaKey)&&e.key.toLowerCase()==='o'){e.preventDefault();$('#fin').click();return;}
 if((e.ctrlKey||e.metaKey)&&e.key.toLowerCase()==='z'&&!typing){e.preventDefault();undo();return;}
 if(typing||$('.modal'))return;
 if(S.tab==='2d'){if(M2.key(e)){e.preventDefault();return;}if(e.key==='Delete'&&delFeature()){e.preventDefault();return;}if(e.key==='Escape'&&M2.tool()!=='pan'){setTool('pan');return;}
  const k={p:'poly',l:'line',e:'edit',d:'dist',a:'area',i:'info',g:'pan'}[e.key.toLowerCase()];if(k&&!e.ctrlKey&&!e.metaKey&&!e.altKey){setTool(k);return;}}
 if(e.key==='Home'){if(S.tab==='3d')V3.fit();else M2.fit();}else if(e.key==='Escape')closeMenus();});
addEventListener('resize',()=>{M2.resize();V3.resize();});
if(window.ResizeObserver){new ResizeObserver(()=>M2.resize()).observe($('#p2d'));new ResizeObserver(()=>V3.resize()).observe($('#p3d'));}

/* ---------- mulai ---------- */
document.documentElement.dataset.palet=store.get('gc_palet','keluarga');document.documentElement.dataset.latar=store.get('gc_latar','hangat');
initMenus();
M2.init($('#mc'),{layers:()=>S.geoms,selected:()=>S.selF,onCursor:onCursor,onPick:onPick,onDigit:onDigit,onView:refineRasters,beforeEdit:(g)=>pushUndo(g,'edit vertex'),onChange:(g)=>changed(g),onMeasure:()=>{}});
try{if(!V3.init($('#cv'),$('#gz')))msg('WebGL tidak tersedia; tab 3D dimatikan, peta 2D dan konversi tetap bisa dipakai.','w');}catch(e){msg('3D gagal: '+e.message,'e');}
M2.resize();setTool('pan');refreshAll();
window.__GC={S:S,C:C,GC:GC,V3:V3,M2:M2,loadFiles:loadFiles,runConvert:runConvert,select:select,showTab:showTab,setTool:setTool,renderLayout:renderLayout,LY:LY,dlgDEM:dlgDEM,dlgLayout:dlgLayout};
