'use strict';
/* Geo Pocket — simpan / buka proyek (.gpk = ZIP: proyek.json + data biner + citra PNG). Offline, tanpa server. */
const PJ={handle:null,name:'',dirty:false,FORMAT:1};
async function deflateRaw(u){return new Uint8Array(await new Response(new Blob([u]).stream().pipeThrough(new CompressionStream('deflate-raw'))).arrayBuffer());}
async function zipDeflate(files){
 const F=[];for(const f of files){const d=typeof f.data==='string'?GC.enc(f.data):f.data,c=GC.crc32(d);let z=d,m=0;if(d.length>64&&typeof CompressionStream!=='undefined'){const k=await deflateRaw(d);if(k.length<d.length){z=k;m=8;}}F.push({n:GC.enc(f.name),d:d,z:z,m:m,c:c});}
 let size=22;F.forEach(f=>size+=30+f.n.length+f.z.length+46+f.n.length);const out=new Uint8Array(size),dv=new DataView(out.buffer);let p=0;const offs=[];
 const now=new Date(),dt=((now.getHours()<<11)|(now.getMinutes()<<5)|(now.getSeconds()>>1))&0xFFFF,dd=(((now.getFullYear()-1980)<<9)|((now.getMonth()+1)<<5)|now.getDate())&0xFFFF;
 const hdr=(q,f,central)=>{dv.setUint16(q,20,true);dv.setUint16(q+2,0x0800,true);dv.setUint16(q+4,f.m,true);dv.setUint16(q+6,dt,true);dv.setUint16(q+8,dd,true);dv.setUint32(q+10,f.c,true);dv.setUint32(q+14,f.z.length,true);dv.setUint32(q+18,f.d.length,true);dv.setUint16(q+22,f.n.length,true);dv.setUint16(q+24,0,true);};
 for(const f of F){offs.push(p);dv.setUint32(p,0x04034b50,true);hdr(p+4,f);out.set(f.n,p+30);out.set(f.z,p+30+f.n.length);p+=30+f.n.length+f.z.length;}
 const cs=p;F.forEach((f,i)=>{dv.setUint32(p,0x02014b50,true);dv.setUint16(p+4,20,true);hdr(p+6,f);dv.setUint16(p+32,0,true);dv.setUint16(p+34,0,true);dv.setUint16(p+36,0,true);dv.setUint32(p+38,0,true);dv.setUint32(p+42,offs[i],true);out.set(f.n,p+46);p+=46+f.n.length;});
 dv.setUint32(p,0x06054b50,true);dv.setUint16(p+8,F.length,true);dv.setUint16(p+10,F.length,true);dv.setUint32(p+12,p-cs,true);dv.setUint32(p+16,cs,true);return out;}
const u8=(a)=>new Uint8Array(a.buffer,a.byteOffset,a.byteLength);
function canvasPNG(cv){return new Promise((ok,no)=>cv.toBlob(b=>b?b.arrayBuffer().then(x=>ok(new Uint8Array(x))):no(new Error('citra gagal disimpan')),'image/png'));}
const jsonSafe=(o)=>{try{return JSON.parse(JSON.stringify(o,(k,v)=>ArrayBuffer.isView(v)?Array.from(v):v));}catch(e){return {};}};
async function projBytes(){
 const files=[],L=[];let skipped=0,reduced=0;
 for(const g of S.geoms){const o={id:g.id,name:g.name,src:g.src||'',file:g.file||'',base:g.base||'',fold:g.fold||null,visible:g.visible!==false,color:g.color,opacity:g.opacity==null?1:g.opacity,style:g.style?jsonSafe(g.style):null,mapc:g.mapc||null};
  if(g.ras){if(!g.ras.cv){skipped++;continue;}const r=g.ras;if(r.lv&&Math.max(r.W,r.H)>r.cv.width*1.01)reduced++;o.ras={ext:r.ext,W:r.W,H:r.H,px:r.px,py:r.py,img:'r'+g.id+'.png'};files.push({name:o.ras.img,data:await canvasPNG(r.cv)});}
  else if(g.dem){const d=g.dem;o.dem={nx:d.nx,ny:d.ny,x0:d.x0,y1:d.y1,cell:d.cell,celly:d.celly,mode:d.mode||'hyps',z:'d'+g.id+'.f32'};files.push({name:o.dem.z,data:u8(Float32Array.from(d.z))});}
  else{o.meta=jsonSafe(g.meta);o.xf=g.xf;o.v='v'+g.id+'.f64';files.push({name:o.v,data:u8(Float64Array.from(g.V))});
   const x=g.xf;if(x&&(x.swap||x.flipZ||x.dx||x.dy||x.dz)){o.v0='v0_'+g.id+'.f64';files.push({name:o.v0,data:u8(Float64Array.from(g.V0))});}
   if(g.F.length){o.f='f'+g.id+'.u32';files.push({name:o.f,data:u8(Uint32Array.from(g.F))});}
   if(g.P.length){let n=1+g.P.length;for(const p of g.P)n+=p.idx.length;const a=new Uint32Array(n);a[0]=g.P.length;let q=1+g.P.length;g.P.forEach((p,k)=>{a[1+k]=p.idx.length;a.set(p.idx,q);q+=p.idx.length;});o.p='p'+g.id+'.u32';files.push({name:o.p,data:u8(a)});
    o.pc=g.P.map(p=>p.closed?1:0);if(g.P.some(p=>p.attr))o.pa=g.P.map(p=>p.attr||null);}
   if(g.PT.length){o.pt='t'+g.id+'.u32';files.push({name:o.pt,data:u8(Uint32Array.from(g.PT))});if(g.PA.length)o.ptA=g.PA;}}
  L.push(o);}
 const pr={app:'Geo Pocket',format:PJ.FORMAT,saved:new Date().toISOString(),crs:S.crs||null,crsUser:!!S._crsUser,folders:S.folders,selFold:S.selFold,sel:S.sel,view:{cx:M2.view.cx,cy:M2.view.cy,s:M2.view.s},
  map:{on:MP.on,layer:MP.layer,jenis:MP.jenis,dip:MP.dip,strike:MP.strike,rl:MP.rl,rlv:MP.rlv,pick:MP.pick,fold:MP.fold,seq:MP.seq},layout:jsonSafe(LY),layers:L};
 files.unshift({name:'proyek.json',data:JSON.stringify(pr)});return {bytes:await zipDeflate(files),skipped:skipped,reduced:reduced,n:L.length};}
async function projSave(as){if(!S.geoms.length){msg('Belum ada lapisan untuk disimpan.','w');return;}
 msg('Menyimpan proyek…');let r;try{r=await projBytes();}catch(e){msg('Gagal menyimpan proyek: '+e.message,'e');return;}
 const nm=(PJ.name||'proyek_geopocket')+'.gpk';let done=false;
 if(window.showSaveFilePicker&&!PJ.noPicker){try{if(as||!PJ.handle)PJ.handle=await window.showSaveFilePicker({suggestedName:nm,types:[{description:'Proyek Geo Pocket',accept:{'application/zip':['.gpk']}}]});
   const w=await PJ.handle.createWritable();await w.write(r.bytes);await w.close();PJ.name=PJ.handle.name.replace(/\.gpk$/i,'');done=true;}
  catch(e){if(e&&e.name==='AbortError'){msg('Simpan dibatalkan.');return;}PJ.handle=null;}}
 if(!done){if(as||!PJ.name){const v=prompt('Nama file proyek',PJ.name||'proyek_geopocket');if(!v)return;PJ.name=v.replace(/\.gpk$/i,'').trim()||'proyek_geopocket';}dl(PJ.name+'.gpk',r.bytes,'application/zip');}
 PJ.dirty=false;projTitle();msg('Proyek disimpan: '+PJ.name+'.gpk ('+r.n+' lapisan, '+nf(r.bytes.length/1024)+' KB)'+(r.skipped?'; '+r.skipped+' citra tanpa gambar dilewati':'')+'.'+(r.reduced?' '+r.reduced+' GeoTIFF besar disimpan sebagai pratinjau (≤ 4096 piksel); untuk detail penuh buka lagi file aslinya.':''),r.reduced?'w':'i');}
function projTitle(){document.title=(PJ.name?PJ.name+(PJ.dirty?' •':'')+' — ':'')+'Geo Pocket';}
async function projOpen(file){let z;try{z=await unzip(await file.arrayBuffer());}catch(e){msg(file.name+': bukan file proyek Geo Pocket ('+e.message+').','e');return;}
 const J=z.find(e=>e.name==='proyek.json');if(!J){msg(file.name+': proyek.json tidak ditemukan.','e');return;}
 let pr;try{pr=JSON.parse(new TextDecoder().decode(J.buf));}catch(e){msg(file.name+': proyek.json rusak.','e');return;}
 if(pr.app!=='Geo Pocket'){msg(file.name+': bukan proyek Geo Pocket.','e');return;}if(pr.format>PJ.FORMAT)msg(file.name+': dibuat versi Geo Pocket yang lebih baru; sebagian isi mungkin tidak terbaca.','w');
 if(S.geoms.length&&PJ.dirty&&!confirm('Lapisan yang sedang terbuka belum disimpan dan akan diganti isi proyek. Lanjutkan?'))return;
 const B={};z.forEach(e=>B[e.name]=e.buf);const ab=(n)=>{if(!B[n])throw new Error('data '+n+' hilang');return B[n];};
 if(typeof DM!=='undefined'&&DM.el)dmStop(false);clearAll();const idMap={},out=[];let bad=0;
 for(const o of pr.layers||[]){try{let g;
   if(o.ras){const bm=await createImageBitmap(new Blob([ab(o.ras.img)],{type:'image/png'})),c=document.createElement('canvas');c.width=bm.width;c.height=bm.height;c.getContext('2d').drawImage(bm,0,0);g=GC.mk({name:o.name,src:o.src||'img'});g.ras={cv:c,ext:o.ras.ext,W:o.ras.W,H:o.ras.H,px:o.ras.px,py:o.ras.py};}
   else if(o.dem){const d=o.dem,zz=new Float32Array(ab(d.z));g=GC.mk({name:o.name,src:o.src||'dem'});g.dem=GC.mkDEM(d.nx,d.ny,d.x0,d.y1,d.cell,zz,d.celly);g.dem.mode=d.mode;g.dem.cv=demCanvas(g.dem,d.mode||'hyps');}
   else{g=GC.mk({name:o.name,src:o.src,meta:o.meta||{},V:new Float64Array(ab(o.v))});g.V0=o.v0?new Float64Array(ab(o.v0)):Float64Array.from(g.V);if(o.xf)g.xf=o.xf;
    if(o.f)g.F=new Uint32Array(ab(o.f));
    if(o.p){const a=new Uint32Array(ab(o.p)),n=a[0];let q=1+n;g.P=[];for(let k=0;k<n;k++){const m=a[1+k];g.P.push({idx:Array.from(a.subarray(q,q+m)),closed:!!(o.pc&&o.pc[k]),attr:o.pa?o.pa[k]:null});q+=m;}}
    if(o.pt){g.PT=new Uint32Array(ab(o.pt));g.PA=o.ptA||[];}}
   g.file=o.file;g.base=o.base;g.fold=o.fold;g.visible=o.visible;g.color=o.color||g.color;g.opacity=o.opacity;if(o.style)g.style=o.style;if(o.mapc)g.mapc=o.mapc;
   idMap[o.id]=g.id;out.push(g);}catch(e){bad++;msg(file.name+': lapisan "'+o.name+'" gagal dibuka ('+e.message+').','e');}}
 S.folders=(pr.folders||[]).map(f=>({id:f.id,name:f.name,parent:f.parent||null,open:f.open!==false}));FID=S.folders.reduce((m,f)=>Math.max(m,f.id+1),FID);
 S.selFold=pr.selFold&&fById(pr.selFold)?pr.selFold:null;S.geoms=out;S.crs=pr.crs||S.crs;S._crsUser=!!pr.crsUser;
 if(pr.layout)Object.assign(LY,pr.layout);
 const m=pr.map||{};Object.assign(MP,{layer:m.layer||'',jenis:m.jenis||{},dip:m.dip==null?'':m.dip,strike:m.strike==null?'':m.strike,rl:m.rl||'dem',rlv:m.rlv||0,pick:m.pick?idMap[m.pick]||null:null,fold:m.fold&&fById(m.fold)?m.fold:null,seq:m.seq||{grab:1,obs:1},cat:null});
 PJ.name=file.name.replace(/\.gpk$/i,'');PJ.handle=null;
 refreshAll();if(pr.view&&isFinite(pr.view.s)&&pr.view.s>0){M2.view.cx=pr.view.cx;M2.view.cy=pr.view.cy;M2.view.s=pr.view.s;}else M2.fit();V3.fit();
 if(pr.sel&&idMap[pr.sel])select(idMap[pr.sel]);showTab('2d');mpToggle(!!m.on);
 PJ.dirty=false;projTitle();msg('Proyek dibuka: '+file.name+' ('+out.length+' lapisan, '+S.folders.length+' folder)'+(bad?'; '+bad+' lapisan gagal':'')+'.',bad?'w':'i');}
function projOpenDlg(){const i=document.createElement('input');i.type='file';i.accept='.gpk';i.onchange=()=>{if(i.files[0])projOpen(i.files[0]);};i.click();}
addEventListener('beforeunload',(e)=>{if(PJ.dirty&&S.geoms.length){e.preventDefault();e.returnValue='';}});
