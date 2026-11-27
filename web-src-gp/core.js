'use strict';
/* Geo Pocket core — parser & writer (tanpa DOM, bisa diuji di Node) */
const GC=(function(){
const FORMATS=[
 {id:'msh',label:'Leapfrog MSH (.msh)',ext:'msh',soft:'Leapfrog',r:1,w:1,note:'Mesh ARANZ biner (segitiga + vertex)'},
 {id:'obj',label:'Wavefront OBJ (.obj)',ext:'obj',soft:'Leapfrog · Global Mapper',r:1,w:1,note:'Mesh, garis, titik; grup per lapisan'},
 {id:'dxf',label:'AutoCAD DXF (.dxf)',ext:'dxf',soft:'Surpac · Leapfrog · MapInfo · Global Mapper',r:1,w:1,note:'3DFACE, POLYLINE, POINT; lapisan dipertahankan'},
 {id:'stl',label:'STL ASCII (.stl)',ext:'stl',soft:'Umum',r:1,w:1,note:'Mesh saja, presisi penuh'},
 {id:'stlb',label:'STL biner (.stl)',ext:'stl',soft:'Umum',r:0,w:1,note:'Mesh saja, float32 (presisi turun pada koordinat UTM)'},
 {id:'ply',label:'PLY ASCII (.ply)',ext:'ply',soft:'Leapfrog · umum',r:1,w:1,note:'Mesh saja'},
 {id:'dtm',label:'Surpac DTM + STR (.dtm + .str)',ext:'dtm',soft:'Surpac',r:1,w:1,note:'Solid/permukaan triangulasi, pasangan DTM teks + STR'},
 {id:'str',label:'Surpac STR (.str)',ext:'str',soft:'Surpac',r:1,w:1,note:'String teks (Y, X, Z)'},
 {id:'shp',label:'Shapefile (.shp + .dbf + .shx)',ext:'shp',soft:'MapInfo · Global Mapper · GIS',r:1,w:1,note:'PointZ / PolyLineZ / PolygonZ + atribut'},
 {id:'mif',label:'MapInfo MIF/MID',ext:'mif',soft:'MapInfo · Global Mapper',r:1,w:1,note:'Teks 2D; Z disimpan sebagai kolom atribut'},
 {id:'tab',label:'MapInfo TAB (.tab + .dat + .map + .id)',ext:'tab',soft:'MapInfo',r:1,w:0,note:'Titik, garis, poligon, multipoint + atribut; proyeksi UTM dikenali. Teks, busur, elips dilewati'},
 {id:'csv',label:'CSV / XYZ (.csv)',ext:'csv',soft:'Semua',r:1,w:1,note:'Tabel titik X,Y,Z + atribut'}
];
const SOFT={'Leapfrog':['msh','obj','dxf','csv'],'Surpac':['dtm','str','dxf','csv'],'MapInfo':['mif','shp','dxf'],'Global Mapper':['shp','dxf','obj','csv']};
const PALETTE=['#17806B','#B5893E','#2B5F9E','#B8692E','#7B4FA0','#C2413B','#4A6B8A','#6B8E23','#D2691E','#008B8B'];
const ACI=[3,5,2,6,4,1,30,150,200,40];
let UID=1;

function u8of(b){return b instanceof Uint8Array?b:(ArrayBuffer.isView(b)?new Uint8Array(b.buffer,b.byteOffset,b.byteLength):new Uint8Array(b));}
function dec(b){const u=u8of(b);let s;try{s=new TextDecoder('utf-8',{fatal:true}).decode(u);}catch(e){s=new TextDecoder('windows-1252').decode(u);}return s.replace(/^﻿/,'');}
function enc(s){return new TextEncoder().encode(s);}
function fx(v,d){let s=v.toFixed(d);if(/^-0(\.0*)?$/.test(s))s=s.slice(1);return s;}
function lines(s){return s.split(/\r?\n/);}

/* ---------- model ---------- */
function mk(o){
 o.id=UID++;o.F=o.F||new Uint32Array(0);o.P=o.P||[];o.PT=o.PT||new Uint32Array(0);o.PA=o.PA||[];
 o.V=o.V||new Float64Array(0);o.V0=Float64Array.from(o.V);o.meta=o.meta||{};
 o.xf={swap:false,flipZ:false,dx:0,dy:0,dz:0};o.visible=true;o.color=PALETTE[(o.id-1)%PALETTE.length];return o;
}
class GB{
 constructor(name){this.name=name;this.v=[];this.f=[];this.p=[];this.pt=[];this.ptA=[];this.map=null;}
 add(x,y,z){this.v.push(x,y,z);return this.v.length/3-1;}
 addD(x,y,z){if(!this.map)this.map=new Map();const k=x+','+y+','+z;let i=this.map.get(k);if(i===undefined){i=this.add(x,y,z);this.map.set(k,i);}return i;}
 tri(a,b,c){if(a!==b&&b!==c&&a!==c)this.f.push(a,b,c);}
 poly(idx,closed,attr){if(idx.length>1)this.p.push({idx:idx,closed:!!closed,attr:attr||null});else if(idx.length===1)this.point(idx[0],attr);}
 point(i,attr){this.pt.push(i);this.ptA.push(attr||null);}
 empty(){return !this.v.length;}
 done(src,meta){return mk({name:this.name,V:Float64Array.from(this.v),F:Uint32Array.from(this.f),P:this.p,PT:Uint32Array.from(this.pt),PA:this.ptA,src:src,meta:meta||{}});}
}
function applyXf(g){
 const a=g.V0,b=g.V,x=g.xf;
 for(let i=0;i<a.length;i+=3){let X=a[i],Y=a[i+1],Z=a[i+2];if(x.swap){const t=X;X=Y;Y=t;}if(x.flipZ)Z=-Z;b[i]=X+x.dx;b[i+1]=Y+x.dy;b[i+2]=Z+x.dz;}
}
function bbox(g){
 const V=g.V;if(!V.length)return null;const mn=[Infinity,Infinity,Infinity],mx=[-Infinity,-Infinity,-Infinity];
 for(let i=0;i<V.length;i+=3)for(let k=0;k<3;k++){const v=V[i+k];if(v<mn[k])mn[k]=v;if(v>mx[k])mx[k]=v;}
 return {min:mn,max:mx};
}
function meshStats(g){
 const F=g.F,V=g.V,nt=F.length/3;if(!nt)return null;
 const bb=bbox(g),cx=(bb.min[0]+bb.max[0])/2,cy=(bb.min[1]+bb.max[1])/2,cz=(bb.min[2]+bb.max[2])/2;
 let area=0,vol=0;const E=new Map(),N=V.length/3;
 for(let t=0;t<nt;t++){
  const a=F[3*t],b=F[3*t+1],c=F[3*t+2];
  const ax=V[3*a]-cx,ay=V[3*a+1]-cy,az=V[3*a+2]-cz,bx=V[3*b]-cx,by=V[3*b+1]-cy,bz=V[3*b+2]-cz,qx=V[3*c]-cx,qy=V[3*c+1]-cy,qz=V[3*c+2]-cz;
  const ux=bx-ax,uy=by-ay,uz=bz-az,wx=qx-ax,wy=qy-ay,wz=qz-az;
  const nx=uy*wz-uz*wy,ny=uz*wx-ux*wz,nz=ux*wy-uy*wx;area+=0.5*Math.sqrt(nx*nx+ny*ny+nz*nz);
  vol+=(ax*(by*qz-bz*qy)-ay*(bx*qz-bz*qx)+az*(bx*qy-by*qx))/6;
  const e=[[a,b],[b,c],[c,a]];for(const p of e){const k=Math.min(p[0],p[1])*N+Math.max(p[0],p[1]);E.set(k,(E.get(k)||0)+1);}
 }
 let open=0,nm=0;E.forEach(v=>{if(v===1)open++;else if(v>2)nm++;});
 return {tris:nt,area:area,volume:Math.abs(vol),open:open,nonManifold:nm,closed:open===0&&nm===0};
}

/* ---------- tabel (CSV / DBF) ---------- */
function isNum(s){return s!==''&&s!==null&&s!==undefined&&isFinite(+s);}
function splitLine(line,d){
 if(d===' ')return line.trim().split(/\s+/);
 if(line.indexOf('"')<0)return line.split(d);
 const out=[];let cur='',q=false;
 for(let i=0;i<line.length;i++){const ch=line[i];if(q){if(ch==='"'){if(line[i+1]==='"'){cur+='"';i++;}else q=false;}else cur+=ch;}else if(ch==='"')q=true;else if(ch===d){out.push(cur);cur='';}else cur+=ch;}
 out.push(cur);return out;
}
function detectDelim(L){
 let best=' ',bs=-1;
 for(const d of [',',';','\t']){const c=L.slice(0,6).map(l=>l.split(d).length-1);if(c[0]>0&&c.every(v=>v===c[0])&&c[0]>bs){bs=c[0];best=d;}}
 return best;
}
function parseTable(text){
 const L=lines(text).filter(l=>l.trim()!==''&&!/^\s*(#|\/\/)/.test(l));
 if(!L.length)return {cols:[],rows:[],delim:','};
 const d=detectDelim(L);let first=splitLine(L[0],d).map(s=>s.trim());
 const hasHead=first.some(s=>!isNum(s));
 const rows=[];for(let i=hasHead?1:0;i<L.length;i++)rows.push(splitLine(L[i],d).map(s=>s.trim()));
 const cols=hasHead?first:first.map((_,i)=>'C'+(i+1));
 return {cols:cols,rows:rows,delim:d};
}
function guessMap(cols,rows){
 const f=(re)=>cols.findIndex(c=>re.test(c.trim()));
 const numc=(c)=>{let ok=0,t=0;for(let r=0;r<Math.min(rows.length,50);r++){const v=rows[r][c];if(v===''||v==null)continue;t++;if(isNum(v))ok++;}return t>0&&ok===t;},f2=(re)=>cols.findIndex((c,i)=>re.test(c.trim())&&numc(i));
 let x=f(/^(x|e|east|easting|xcentre|xc|x_?coord\w*|xm|lon\w*|bujur)$/i),y=f(/^(y|n|north|northing|ycentre|yc|y_?coord\w*|ym|lat\w*|lintang)$/i),z=f(/^(z|rl|elev\w*|alt\w*|h|zc|zcentre|zm|tinggi|depth)$/i);
 if(x<0||y<0||!numc(x)||!numc(y)){const x2=f2(/^(utm_?)?(m_?e|east(ing)?)(_?m)?$|^(utm_?)?x(_?utm)?$|^e(asting)?_?utm$/i),y2=f2(/^(utm_?)?(m_?n|north(ing)?)(_?m)?$|^(utm_?)?y(_?utm)?$|^n(orthing)?_?utm$/i);if(x2>=0&&y2>=0){x=x2;y=y2;}}
 if(x<0||y<0){const nu=[];for(let c=0;c<cols.length;c++){let ok=0,t=0;for(let r=0;r<Math.min(rows.length,20);r++){t++;if(isNum(rows[r][c]))ok++;}if(t&&ok===t)nu.push(c);}
  if(x<0)x=nu[0]!==undefined?nu[0]:-1;if(y<0)y=nu.filter(c=>c!==x)[0];if(y===undefined)y=-1;if(z<0)z=nu.filter(c=>c!==x&&c!==y)[0];if(z===undefined)z=-1;}
 return {x:x,y:y,z:z};
}
function tableToPoints(name,cols,rows,map,src){
 const gb=new GB(name);
 for(const r of rows){const x=parseFloat(r[map.x]),y=parseFloat(r[map.y]);if(!isFinite(x)||!isFinite(y))continue;const z=map.z>=0?parseFloat(r[map.z]):0;gb.point(gb.add(x,y,isFinite(z)?z:0),r);}
 return gb.done(src,{cols:cols,map:map,raw:rows});
}
function remapPoints(g,map){
 const g2=tableToPoints(g.name,g.meta.cols,g.meta.raw,map,g.src);
 g.V0=g2.V0;g.V=Float64Array.from(g2.V0);g.PT=g2.PT;g.PA=g2.PA;g.meta.map=map;applyXf(g);
}
function fromTable(name,cols,rows,src,W){
 const map=guessMap(cols,rows);
 if(map.x>=0&&map.y>=0)return tableToPoints(name,cols,rows,map,src);
 W.push('Tabel '+name+': kolom koordinat X/Y tidak terdeteksi, dimuat sebagai tabel atribut saja.');
 return mk({name:name,src:src,meta:{cols:cols,rows:rows,tableOnly:true}});
}

/* ---------- DBF ---------- */
function parseDBF(buf,keep){
 const u=u8of(buf),dv=new DataView(u.buffer,u.byteOffset,u.byteLength);
 const nrec=dv.getUint32(4,true),hl=dv.getUint16(8,true),rl=dv.getUint16(10,true);
 const fields=[];for(let p=32;p<hl-1&&u[p]!==0x0D;p+=32){let nm='';for(let i=0;i<11&&u[p+i];i++)nm+=String.fromCharCode(u[p+i]);fields.push({name:nm,type:String.fromCharCode(u[p+11]),len:u[p+16]});}
 const rows=[],del=[];
 for(let r=0;r<nrec;r++){const o=hl+r*rl;if(o+rl>u.length)break;const dl=u[o]===0x2A;if(dl&&!keep)continue;del.push(dl);let p=o+1;const row=[];
  for(const f of fields){const s=dec(u.subarray(p,p+f.len)).replace(/\0/g,'').trim();p+=f.len;row.push(s);}rows.push(row);}
 return {cols:fields.map(f=>f.name),rows:rows,del:del,types:fields.map(f=>f.type)};
}
function buildDBF(cols,rows){
 const types=cols.map((c,i)=>rows.length&&rows.every(r=>isNum(r[i]))?'N':'C');
 const lens=cols.map((c,i)=>types[i]==='N'?19:Math.min(80,Math.max(1,...rows.map(r=>enc(String(r[i]===undefined||r[i]===null?'':r[i])).length))));
 const dcs=cols.map((c,i)=>types[i]==='N'?6:0);
 const nf=cols.length,hl=32+32*nf+1,rl=1+lens.reduce((a,b)=>a+b,0);
 const out=new Uint8Array(hl+rl*rows.length+1),dv=new DataView(out.buffer);
 const dt=new Date();out[0]=3;out[1]=dt.getFullYear()-1900;out[2]=dt.getMonth()+1;out[3]=dt.getDate();
 dv.setUint32(4,rows.length,true);dv.setUint16(8,hl,true);dv.setUint16(10,rl,true);
 for(let i=0;i<nf;i++){const p=32+32*i;const nm=enc(String(cols[i]).replace(/[^A-Za-z0-9_]/g,'_').slice(0,10));out.set(nm,p);out[p+11]=types[i].charCodeAt(0);out[p+16]=lens[i];out[p+17]=dcs[i];}
 out[hl-1]=0x0D;
 rows.forEach((r,ri)=>{let p=hl+ri*rl;out[p++]=0x20;for(let i=0;i<nf;i++){let s=r[i]===undefined||r[i]===null?'':String(r[i]);
  if(types[i]==='N'){s=s===''?'':(+s).toFixed(6);let b=enc(s);const pad=lens[i]-b.length;for(let k=0;k<pad;k++)out[p+k]=0x20;out.set(b.subarray(0,lens[i]),p+Math.max(0,pad));}
  else{const b=enc(s).subarray(0,lens[i]);out.set(b,p);for(let k=b.length;k<lens[i];k++)out[p+k]=0x20;}
  p+=lens[i];}});
 out[out.length-1]=0x1A;return out;
}

/* ---------- reader: MSH ---------- */
function parseMSH(base,u,W){
 let k=-1;const tag=[91,98,105,110,97,114,121,93];
 for(let i=0;i<Math.min(u.length-8,8192)&&k<0;i++){let m=true;for(let j=0;j<8;j++)if(u[i+j]!==tag[j]){m=false;break;}if(m)k=i;}
 if(k<0)throw new Error('Penanda [binary] tidak ditemukan');
 const hdr=dec(u.subarray(0,k));if(!/^%ARANZ/.test(hdr))throw new Error('Bukan file ARANZ .msh');
 const ent=[];const re=/^\s*(\w+)\s+(Integer|Double|Float|Short|Byte)\s+(\d+)\s+(\d+)\s*;/gm;let m;
 while((m=re.exec(hdr)))ent.push({name:m[1],type:m[2],c:+m[3],n:+m[4]});
 const dv=new DataView(u.buffer,u.byteOffset,u.byteLength);let off=k+8,le=true;
 if(u[off]===0xff&&u[off+1]===0x0f&&u[off+2]===0xf0){const m1=dv.getFloat64(off+4,true);if(Math.abs(m1-1.23456789)>1e-6){const m2=dv.getFloat64(off+4,false);if(Math.abs(m2-1.23456789)<1e-6)le=false;}off+=12;}
 const sz={Integer:4,Double:8,Float:4,Short:2,Byte:1},rd={Integer:(o)=>dv.getInt32(o,le),Double:(o)=>dv.getFloat64(o,le),Float:(o)=>dv.getFloat32(o,le),Short:(o)=>dv.getInt16(o,le),Byte:(o)=>dv.getUint8(o)};
 const data={};
 for(const e of ent){const cnt=e.c*e.n;if(off+cnt*sz[e.type]>u.length)throw new Error('Data biner lebih pendek dari header ('+e.name+')');const a=new Array(cnt);for(let i=0;i<cnt;i++)a[i]=rd[e.type](off+i*sz[e.type]);data[e.name]=a;off+=cnt*sz[e.type];}
 if(off!==u.length)W.push('MSH: '+(u.length-off)+' byte sisa setelah entri terakhir diabaikan.');
 const L=data.Location,T=data.Tri;if(!L)throw new Error('Entri Location tidak ada di file .msh');
 const ign=ent.map(e=>e.name).filter(n=>n!=='Tri'&&n!=='Location');if(ign.length)W.push('MSH: entri diabaikan: '+ign.join(', '));
 const gb=new GB(base);for(let i=0;i<L.length;i+=3)gb.add(L[i],L[i+1],L[i+2]);const nv=L.length/3;
 if(T){let mn=Infinity,mx=-1;for(const v of T){if(v<mn)mn=v;if(v>mx)mx=v;}if(mn>=1&&mx===nv){W.push('MSH: indeks segitiga berbasis 1, dikonversi ke 0.');for(let i=0;i<T.length;i++)T[i]--;}
  for(let i=0;i<T.length;i+=3){const a=T[i],b=T[i+1],c=T[i+2];if(a>=nv||b>=nv||c>=nv||a<0||b<0||c<0){W.push('MSH: indeks segitiga di luar rentang, dilewati.');continue;}gb.f.push(a,b,c);}}
 else for(let i=0;i<nv;i++)gb.point(i);
 return [gb.done('msh')];
}

/* ---------- reader: OBJ / STL / PLY ---------- */
function parseOBJ(base,u,W){
 const gb=new GB(base);const L=lines(dec(u));let nv=0;
 const ix=(t)=>{let i=parseInt(t,10);return i<0?nv+i:i-1;};
 for(const ln of L){const c=ln.charCodeAt(0);if(c===118&&ln.charCodeAt(1)===32){const p=ln.trim().split(/\s+/);gb.add(+p[1],+p[2],+p[3]);nv++;}
  else if(c===102&&ln.charCodeAt(1)===32){const p=ln.trim().split(/\s+/).slice(1).map(ix);for(let i=1;i<p.length-1;i++)gb.tri(p[0],p[i],p[i+1]);}
  else if(c===108&&ln.charCodeAt(1)===32){gb.poly(ln.trim().split(/\s+/).slice(1).map(ix),false);}
  else if(c===112&&ln.charCodeAt(1)===32){ln.trim().split(/\s+/).slice(1).map(ix).forEach(i=>gb.point(i));}}
 if(!nv)throw new Error('OBJ tidak berisi vertex');
 const nvv=gb.v.length/3;for(const i of gb.f)if(i<0||i>=nvv)throw new Error('Indeks OBJ di luar rentang');
 return [gb.done('obj')];
}
function parseSTL(base,u,W){
 const gb=new GB(base);let bin=false;
 if(u.length>=84){const n=new DataView(u.buffer,u.byteOffset,u.byteLength).getUint32(80,true);if(84+50*n===u.length)bin=true;}
 if(bin){const dv=new DataView(u.buffer,u.byteOffset,u.byteLength),n=dv.getUint32(80,true);
  for(let t=0;t<n;t++){const o=84+50*t+12;const id=[];for(let k=0;k<3;k++)id.push(gb.addD(dv.getFloat32(o+12*k,true),dv.getFloat32(o+12*k+4,true),dv.getFloat32(o+12*k+8,true)));gb.tri(id[0],id[1],id[2]);}}
 else{const s=dec(u),re=/vertex\s+([-+0-9.eE]+)\s+([-+0-9.eE]+)\s+([-+0-9.eE]+)/g;let m,c=0,id=[];
  while((m=re.exec(s))){id.push(gb.addD(+m[1],+m[2],+m[3]));if(++c%3===0){gb.tri(id[0],id[1],id[2]);id=[];}}}
 if(!gb.f.length)throw new Error('STL tidak berisi segitiga');
 return [gb.done('stl')];
}
function parsePLY(base,u,W){
 const txt=new TextDecoder('latin1').decode(u.subarray(0,Math.min(u.length,65536)));
 const he=txt.indexOf('end_header');if(he<0||!/^ply/.test(txt))throw new Error('Header PLY tidak valid');
 let body=he+'end_header'.length;if(u[body]===13)body++;if(u[body]===10)body++;
 const H=lines(txt.slice(0,he)),els=[];let fmt='ascii';
 for(const l of H){const p=l.trim().split(/\s+/);if(p[0]==='format')fmt=p[1];else if(p[0]==='element')els.push({name:p[1],n:+p[2],props:[]});
  else if(p[0]==='property'&&els.length){if(p[1]==='list')els[els.length-1].props.push({list:true,ct:p[2],t:p[3],name:p[4]});else els[els.length-1].props.push({t:p[1],name:p[2]});}}
 const gb=new GB(base);
 const SZ={char:1,int8:1,uchar:1,uint8:1,short:2,int16:2,ushort:2,uint16:2,int:4,int32:4,uint:4,uint32:4,float:4,float32:4,double:8,float64:8};
 if(fmt==='ascii'){const L=lines(dec(u.subarray(body))).filter(x=>x.trim()!=='');let li=0;
  for(const e of els){for(let r=0;r<e.n;r++){const p=(L[li++]||'').trim().split(/\s+/);
   if(e.name==='vertex'){const xi=e.props.findIndex(q=>q.name==='x'),yi=e.props.findIndex(q=>q.name==='y'),zi=e.props.findIndex(q=>q.name==='z');gb.add(+p[xi],+p[yi],+p[zi]);}
   else if(e.name==='face'){const n=+p[0],ids=p.slice(1,1+n).map(Number);for(let i=1;i<n-1;i++)gb.tri(ids[0],ids[i],ids[i+1]);}}}}
 else{const le=fmt==='binary_little_endian',dv=new DataView(u.buffer,u.byteOffset,u.byteLength);let o=body;
  const rd=(t,off)=>{switch(t){case 'char':case 'int8':return dv.getInt8(off);case 'uchar':case 'uint8':return dv.getUint8(off);case 'short':case 'int16':return dv.getInt16(off,le);case 'ushort':case 'uint16':return dv.getUint16(off,le);case 'int':case 'int32':return dv.getInt32(off,le);case 'uint':case 'uint32':return dv.getUint32(off,le);case 'float':case 'float32':return dv.getFloat32(off,le);default:return dv.getFloat64(off,le);}};
  for(const e of els){for(let r=0;r<e.n;r++){const rec={};
   for(const q of e.props){if(q.list){const n=rd(q.ct,o);o+=SZ[q.ct];const ids=[];for(let i=0;i<n;i++){ids.push(rd(q.t,o));o+=SZ[q.t];}rec[q.name]=ids;}else{rec[q.name]=rd(q.t,o);o+=SZ[q.t];}}
   if(e.name==='vertex')gb.add(rec.x,rec.y,rec.z);else if(e.name==='face'){const ids=rec.vertex_indices||rec.vertex_index||[];for(let i=1;i<ids.length-1;i++)gb.tri(ids[0],ids[i],ids[i+1]);}}}}
 if(!gb.v.length)throw new Error('PLY tidak berisi vertex');
 if(!gb.f.length)for(let i=0;i<gb.v.length/3;i++)gb.point(i);
 return [gb.done('ply')];
}

/* ---------- reader: DXF (diport dari GC-Ex / Ore Works: BLOCK + INSERT, polyface, polygon mesh) ---------- */
function parseDXF(base,u,W){
 const s=dec(u);if(/^AutoCAD Binary DXF/.test(s))throw new Error('DXF biner belum didukung; simpan sebagai DXF ASCII.');
 const L=lines(s),blocks={},top=[],skip={};let sec='',expect=false,cur=null,blk=null,poly=null;
 const emit=(it)=>{(blk?blk.ents:top).push(it);};
 const num=(e,c,d)=>{for(const p of e.d)if(p[0]===c){const v=parseFloat(p[1]);return isFinite(v)?v:d;}return d;};
 const all=(e,c)=>{const r=[];for(const p of e.d)if(p[0]===c)r.push(parseFloat(p[1]));return r;};
 const str=(e,c,d)=>{for(const p of e.d)if(p[0]===c)return p[1].trim();return d;};
 const flush=()=>{if(!poly)return;const P=poly;poly=null;
  if(P.flags&64)emit({k:'pf',ly:P.ly,verts:P.verts,faces:P.faces});else if(P.flags&16)emit({k:'pm',ly:P.ly,verts:P.verts,m:P.m,n:P.n});else emit({k:'poly',ly:P.ly,P:P.verts,closed:!!(P.flags&1)});};
 function ent(e){
  const ly=str(e,8,'0');
  switch(e.t){
   case '3DFACE':{const P=[];for(let k=0;k<4;k++)P.push([num(e,10+k,0),num(e,20+k,0),num(e,30+k,0)]);emit({k:'face',ly:ly,P:P});break;}
   case 'LINE':emit({k:'poly',ly:ly,P:[[num(e,10,0),num(e,20,0),num(e,30,0)],[num(e,11,0),num(e,21,0),num(e,31,0)]],closed:false});break;
   case 'POINT':emit({k:'pt',ly:ly,P:[[num(e,10,0),num(e,20,0),num(e,30,0)]]});break;
   case 'LWPOLYLINE':{const xs=all(e,10),ys=all(e,20),z=num(e,38,0);emit({k:'poly',ly:ly,P:xs.map((x,i)=>[x,ys[i],z]),closed:(num(e,70,0)&1)===1});break;}
   case 'POLYLINE':flush();poly={ly:ly,flags:num(e,70,0)|0,m:num(e,71,0)|0,n:num(e,72,0)|0,elev:num(e,30,0),verts:[],faces:[]};break;
   case 'VERTEX':if(poly){const f=num(e,70,0)|0;if((f&128)&&!(f&64))poly.faces.push([num(e,71,0),num(e,72,0),num(e,73,0),num(e,74,0)]);else poly.verts.push([num(e,10,0),num(e,20,0),num(e,30,poly.elev)]);}break;
   case 'SEQEND':flush();break;
   case 'INSERT':emit({k:'ins',ly:ly,name:str(e,2,''),x:num(e,10,0),y:num(e,20,0),z:num(e,30,0),sx:num(e,41,1),sy:num(e,42,1),sz:num(e,43,1),rot:num(e,50,0)});break;
   case 'BLOCK':if(blk&&!blk.name)blk.name=str(e,2,'');break;
   case 'ATTRIB':case 'ATTDEF':break;
   default:skip[e.t]=(skip[e.t]||0)+1;
  }
 }
 const live=()=>sec==='ENTITIES'||(sec==='BLOCKS'&&blk);
 for(let i=0;i+1<L.length;i+=2){
  const c=parseInt(L[i],10),v=L[i+1];
  if(c===0){if(cur&&live())ent(cur);cur=null;const t=v.trim();
   if(t==='SECTION')expect=true;else if(t==='ENDSEC'){flush();sec='';}
   else if(t==='BLOCK'){flush();blk={name:'',ents:[]};cur={t:'BLOCK',d:[]};}
   else if(t==='ENDBLK'){flush();if(blk)blocks[blk.name]=blk.ents;blk=null;}
   else if(live())cur={t:t,d:[]};}
  else if(expect&&c===2){sec=v.trim();expect=false;}
  else if(cur)cur.d.push([c,v]);
 }
 if(cur&&live())ent(cur);flush();
 const layers=new Map(),G=(ly)=>{let g=layers.get(ly);if(!g){g=new GB(ly);layers.set(ly,g);}return g;};
 const mkT=(chain)=>(p)=>{let q=p;for(const c of chain){const cs=Math.cos(c.rot*Math.PI/180),sn=Math.sin(c.rot*Math.PI/180);q=[c.x+q[0]*c.sx*cs-q[1]*c.sy*sn,c.y+q[0]*c.sx*sn+q[1]*c.sy*cs,c.z+q[2]*c.sz];}return q;};
 let badIns=0;
 function place(items,chain){
  const T=mkT(chain);
  for(const it of items){
   if(it.k==='ins'){if(chain.length>=4)continue;const B=blocks[it.name];if(!B){badIns++;continue;}place(B,[it].concat(chain));continue;}
   const ly=(it.ly==='0'&&chain.length)?chain[chain.length-1].ly:it.ly,g=G(ly),add=(p)=>{const q=T(p);return g.addD(q[0],q[1],q[2]);};
   if(it.k==='face'){const id=it.P.map(add);g.tri(id[0],id[1],id[2]);if(id[3]!==id[2])g.tri(id[0],id[2],id[3]);}
   else if(it.k==='poly')g.poly(it.P.map(add),it.closed);
   else if(it.k==='pt'){const q=T(it.P[0]);g.point(g.add(q[0],q[1],q[2]));}
   else if(it.k==='pf'){const ids=it.verts.map(add);for(const q of it.faces){const ix=q.filter(v=>v!==0).map(v=>Math.abs(v)-1).filter(v=>v>=0&&v<ids.length).map(v=>ids[v]);for(let i=1;i<ix.length-1;i++)g.tri(ix[0],ix[i],ix[i+1]);}}
   else if(it.k==='pm'){const ids=it.verts.map(add),m=it.m,n=it.n;for(let i=0;i<m-1;i++)for(let j=0;j<n-1;j++){const a=ids[i*n+j],b=ids[i*n+j+1],c=ids[(i+1)*n+j],d=ids[(i+1)*n+j+1];if(a!==undefined&&d!==undefined){g.tri(a,b,c);g.tri(b,d,c);}}}
  }
 }
 place(top,[]);
 const sk=Object.keys(skip);if(sk.length)W.push('DXF: entitas dilewati: '+sk.map(k=>k+' ×'+skip[k]).join(', '));
 if(badIns)W.push('DXF: '+badIns+' INSERT merujuk blok yang tidak ada.');
 const out=[];layers.forEach(g=>{if(!g.empty())out.push(g.done('dxf'));});
 if(!out.length)throw new Error('DXF tidak berisi geometri yang dikenali');
 return out;
}

/* ---------- reader: Surpac STR (teks + biner; diport dari GC-Ex readStr) ---------- */
const RXN=/^[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?$/;
function beD(u,o){return new DataView(u.buffer,u.byteOffset+o,8).getFloat64(0,false);}
function strSeqBin(u,ds,end,yx){
 const dv=new DataView(u.buffer,u.byteOffset,u.byteLength),ok1=(v)=>isFinite(v)&&Math.abs(v)<1e8,
 sane=(p)=>{if(p+29>end)return false;const y0=dv.getFloat64(p+5,false),x0=dv.getFloat64(p+13,false),z0=dv.getFloat64(p+21,false);return (x0===0&&y0===0&&z0===0)||(ok1(x0)&&ok1(y0)&&Math.abs(z0)<1e6&&(Math.abs(x0)>1e-3||Math.abs(y0)>1e-3));};
 let start=-1;
 for(let k=0;k<=16;k++){const p=ds+k;if(u[p]!==0||!sane(p))continue;let nx=p+29;while(nx<end&&u[nx]>=32&&u[nx]<=126)nx++;if(nx+29>end||(u[nx]===0&&sane(nx))){start=p;break;}}
 if(start<0)return null;
 const segs=[];let cur=[],csn=null,pn=-1,o=start,nd=0;const flush=()=>{if(cur.length){cur.sn=csn;segs.push(cur);}cur=[];};
 while(o+29<=end){if(u[o]!==0||!sane(o)){if(end-o>64)return null;break;}
  const no=dv.getInt32(o+1,false);let Y=dv.getFloat64(o+5,false),X=dv.getFloat64(o+13,false);const Z=dv.getFloat64(o+21,false);
  if(!yx){const t=X;X=Y;Y=t;}
  if(X===0&&Y===0&&Z===0){flush();pn=-1;}else{if(pn>=0&&no!==pn)flush();pn=no;csn=no;cur.push([X,Y,Z]);}
  o+=29;const o1=o;while(o<end&&u[o]>=32&&u[o]<=126)o++;if(o>o1)nd++;}
 if(!nd)return null;flush();return segs;
}
function strSegs(u,yx){
 let nl=0,ds=-1;for(let i=0;i<u.length;i++){if(u[i]===10){nl++;if(nl===2){ds=i+1;break;}}}
 if(ds<0||ds>=u.length)throw new Error('format STR tidak dikenali');
 const c=u[ds];let segs=[],cur=[],prev=null,csn=null;const flush=()=>{if(cur.length){cur.sn=csn;segs.push(cur);}cur=[];};
 if((c>=48&&c<=57)||c===32||c===45||c===13||c===10||c===9||c===43||c===46){
  const L=dec(u).split(/\r?\n/);
  for(let j=0;j<L.length;j++){const ln=L[j].replace(/\t/g,' ').trim();if(!ln)continue;let a=ln.indexOf(',')>=0?ln.split(','):ln.split(/\s+/),sn=null,x,y,z,ok=false;a=a.map(v=>v.trim());
   if(a.length>=4&&RXN.test(a[0])&&RXN.test(a[1])&&RXN.test(a[2])&&RXN.test(a[3])){sn=a[0];x=+a[1];y=+a[2];z=+a[3];ok=true;}
   else if(a.length===3&&RXN.test(a[0])&&RXN.test(a[1])&&RXN.test(a[2])){sn='1';x=+a[0];y=+a[1];z=+a[2];ok=true;}
   if(!ok)continue;if(yx){const t=x;x=y;y=t;}
   if(x===0&&y===0&&z===0){flush();prev=null;continue;}if(prev!==null&&sn!==prev)flush();prev=sn;csn=+sn;cur.push([x,y,z]);}
  flush();return segs;}
 let end=u.length;for(let k=u.length-3;k>=ds&&u.length-k<=64;k--){if(u[k]===69&&u[k+1]===78&&u[k+2]===68){end=k;break;}}
 const sq=strSeqBin(u,ds,end,yx);if(sq)return sq;
 const ok1=(v)=>isFinite(v)&&Math.abs(v)<1e8;let R=29,best=-1;
 for(let rs=29;rs<=29+8*12;rs+=8){const o0=ds+((end-ds)%rs),nr=Math.floor((end-o0)/rs),st=Math.max(1,Math.floor(nr/3000));let good=0,tot=0;
  for(let q=0;q<nr;q+=st){const p=o0+q*rs,y0=beD(u,p+5),x0=beD(u,p+13),z0=beD(u,p+21);tot++;if((x0===0&&y0===0&&z0===0)||(ok1(x0)&&ok1(y0)&&Math.abs(z0)<1e6&&(Math.abs(x0)>1e-3||Math.abs(y0)>1e-3)))good++;}
  const sc=tot?good/tot:0;if(sc>best+1e-9){best=sc;R=rs;}if(sc===1)break;}
 let o=ds+((end-ds)%R),pn=-1;
 while(o+R<=end){const no=u[o+1]*16777216+(u[o+2]<<16|u[o+3]<<8|u[o+4]);let Y=beD(u,o+5),X=beD(u,o+13);const Z=beD(u,o+21);
  if(!yx){const t=X;X=Y;Y=t;}if(X===0&&Y===0&&Z===0){flush();pn=-1;}else{if(pn>=0&&no!==pn)flush();pn=no;csn=no;cur.push([X,Y,Z]);}o+=R;}
 flush();return segs;
}
function parseSTR(base,u,W){
 const segs=strSegs(u,true),gb=new GB(base);
 for(const sg of segs){const ids=sg.map(p=>gb.add(p[0],p[1],p[2]));let closed=false;const a=sg[0],b=sg[sg.length-1];
  if(ids.length>3&&a[0]===b[0]&&a[1]===b[1]&&a[2]===b[2]){ids.pop();closed=true;}gb.poly(ids,closed,[sg.sn===undefined?null:sg.sn]);}
 if(!gb.v.length)throw new Error('STR tidak berisi titik');
 return [gb.done('str',{cols:['STRING']})];
}

/* ---------- reader: Surpac DTM (teks + biner; diport dari GC-Ex readDtm / dtmBin) ---------- */
function dtmBin(u){
 let hdrEnd=-1,i;
 for(i=1;i<u.length-3;i++){if(u[i]===69&&u[i+1]===78&&u[i+2]===68&&u[i-1]===0){let j=i+3;while(j<u.length&&u[j]===0)j++;if(u[j]===1||u[j]===2){hdrEnd=i+3;break;}}}
 if(hdrEnd<0)for(i=0;i<Math.min(u.length-3,4096);i++){if(u[i]===69&&u[i+1]===78&&u[i+2]===68){hdrEnd=i+3;break;}}
 if(hdrEnd<0)return null;
 const dv=new DataView(u.buffer,u.byteOffset,u.byteLength),I=(o)=>dv.getInt32(o,false);let o=hdrEnd,mx=0,nb=false,rs=0;const tri=[];
 while(o<u.length&&u[o]===0)o++;
 while(o<u.length){const t=u[o];
  if(t===1){o+=9;while(o<u.length&&u[o]===0)o++;continue;}
  if(t===2){let j=o+5;while(j<u.length&&u[j]!==0)j++;const txt=new TextDecoder().decode(u.subarray(o+5,j));nb=/neighbours\s*=\s*yes/i.test(txt);o=j;while(o<u.length&&u[o]===0)o++;rs=0;continue;}
  if(t===3){if(!rs){const id0=I(o+1),cand=[nb?33:21,33,21,29,25,37,41];for(const cd of cand){const q=o+cd;if(q>=u.length||u[q]===255||((u[q]===3)&&I(q+1)===id0+1)||u[q]===1||u[q]===2){rs=cd;break;}}if(!rs)throw new Error('struktur record segitiga DTM biner tidak dikenali');}
   const a=I(o+5),b=I(o+9),c2=I(o+13);if(a<1||b<1||c2<1)throw new Error('indeks titik DTM biner tidak valid (byte '+o+')');tri.push(a-1,b-1,c2-1);if(a>mx)mx=a;if(b>mx)mx=b;if(c2>mx)mx=c2;o+=rs;continue;}
  if(t===255||t===0)break;throw new Error('record DTM biner tidak dikenali (tipe '+t+' di byte '+o+')');}
 return {tri:tri,mx:mx};
}
function parseDTM(base,u,W,aux){
 let nl=0;while(nl<u.length&&u[nl]!==10&&nl<2000)nl++;
 const head=new TextDecoder().decode(u.subarray(0,nl)),ref=(head.split(',')[0]||'').trim();let tri=[],mx=0,bin=false,i;
 for(i=nl+1;i<Math.min(u.length,nl+400);i++)if(u[i]===0){bin=true;break;}
 if(bin){const B=dtmBin(u);if(B){tri=B.tri;mx=B.mx;}}
 else{const L=new TextDecoder().decode(u).split(/\r?\n/);for(i=1;i<L.length;i++){const a=L[i].split(',');if(a.length<4||!/^\s*\d+\s*$/.test(a[0]))continue;const p=+a[1],q=+a[2],r=+a[3];if(!(p>0&&q>0&&r>0))continue;tri.push(p-1,q-1,r-1);mx=Math.max(mx,p,q,r);}}
 if(!tri.length)throw new Error('DTM: tidak ada segitiga di file');
 const strs=(aux&&aux.strs)||[],low=ref.toLowerCase().replace(/\.str$/,''),bn=(n)=>n.toLowerCase().replace(/^.*[\\\/]/,'').replace(/\.str$/,'');
 let s=strs.filter(x=>{const n=bn(x.name);return low&&(n===low||n.slice(-low.length-1)==='_'+low||n.slice(-low.length-1)==='-'+low||n.slice(-low.length)===low);})[0];
 if(!s&&strs.length===1){s=strs[0];W.push('DTM: nama pasangan di header ("'+ref+'") tidak cocok dengan '+s.name+'; dipakai karena satu-satunya file STR.');}
 if(!s)throw new Error('DTM: titiknya tersimpan di file string "'+(ref||'*.str')+'"'+(strs.length?' — file STR yang dipilih ('+strs.map(x=>x.name).join(', ')+') bukan pasangannya':'')+'. Pilih file "'+(ref||'.str')+'" bersama file .dtm ini (nama file jangan diubah).');
 const segs=strSegs(u8of(s.buf),true),P=[],PS=[];segs.forEach(g=>{g.forEach(p=>{P.push(p);PS.push(p);});PS.push(null);});
 const nt0=tri.length/3,lim=Math.floor(nt0*0.005),bad=(A)=>{let b=0;for(let t=0;t<tri.length;t+=3){if(!A[tri[t]]||!A[tri[t+1]]||!A[tri[t+2]])b++;}return b;};
 const bP=bad(P),bS=bad(PS),okP=bP<=lim,okS=bS<=lim;
 const med=(A)=>{const Lm=[],st=Math.max(3,Math.floor(tri.length/3/3000)*3);for(let t=0;t<tri.length;t+=st){const p=A[tri[t]],q=A[tri[t+1]];if(p&&q)Lm.push(Math.hypot(p[0]-q[0],p[1]-q[1]));}Lm.sort((x,y)=>x-y);return Lm.length?Lm[Lm.length>>1]:Infinity;};
 const useS=okS&&(!okP||segs.length>1&&med(PS)<med(P));
 if(!okP&&!okS)throw new Error('DTM merujuk titik ke-'+mx+' tetapi '+s.name+' hanya berisi '+P.length+' titik ('+PS.length+' record termasuk pemisah): file string tidak cocok.');
 const AA=useS?PS:P;let drop=0;
 if(useS?bS:bP){const t2=[];for(let k=0;k<tri.length;k+=3){if(AA[tri[k]]&&AA[tri[k+1]]&&AA[tri[k+2]])t2.push(tri[k],tri[k+1],tri[k+2]);else drop++;}tri=t2;}
 if(useS){const map=new Int32Array(PS.length).fill(-1);let n=0;for(let k=0;k<PS.length;k++)if(PS[k])map[k]=n++;for(let k=0;k<tri.length;k++)tri[k]=map[tri[k]];}
 const gb=new GB(base);P.forEach(p=>gb.add(p[0],p[1],p[2]));for(let t=0;t<tri.length;t+=3)gb.f.push(tri[t],tri[t+1],tri[t+2]);
 if(drop)W.push('DTM: '+drop+' segitiga merujuk titik di luar file STR dan dibuang.');
 if(bin)W.push('DTM biner Surpac dibaca (struktur record dari GC-Ex).');
 return [gb.done('dtm',{pair:s.name})];
}

/* ---------- reader: SHP ---------- */
function parseSHP(base,u,W,aux){
 const dv=new DataView(u.buffer,u.byteOffset,u.byteLength);
 if(dv.getInt32(0,false)!==9994)throw new Error('Bukan file .shp');
 const gb=new GB(base);let dbf=null;
 if(aux&&aux.dbf){try{dbf=parseDBF(aux.dbf);}catch(e){W.push('SHP: .dbf gagal dibaca ('+e.message+')');}}
 else W.push('SHP: file .dbf tidak disertakan, atribut tidak dimuat.');
 let o=100,rec=0;const types={};
 while(o+8<=u.length){const clen=dv.getInt32(o+4,false)*2,p=o+8;o=p+clen;const t=dv.getInt32(p,true);types[t]=1;const row=dbf?dbf.rows[rec]||null:null;rec++;
  if(t===0)continue;
  const hasZ=(t===11||t===13||t===15||t===18||t===31);
  if(t===1||t===11||t===21){gb.point(gb.add(dv.getFloat64(p+4,true),dv.getFloat64(p+12,true),hasZ?dv.getFloat64(p+20,true):0),row);continue;}
  if(t===8||t===18||t===28){const n=dv.getInt32(p+36,true);const zo=p+40+16*n+16;for(let i=0;i<n;i++)gb.point(gb.add(dv.getFloat64(p+40+16*i,true),dv.getFloat64(p+48+16*i,true),hasZ?dv.getFloat64(zo+8*i,true):0),row);continue;}
  if([3,5,13,15,23,25,31].indexOf(t)<0){W.push('SHP: tipe shape '+t+' dilewati.');continue;}
  const np=dv.getInt32(p+36,true),n=dv.getInt32(p+40,true);let q=p+44;const parts=[];for(let i=0;i<np;i++){parts.push(dv.getInt32(q,true));q+=4;}
  let pt=null;if(t===31){pt=[];for(let i=0;i<np;i++){pt.push(dv.getInt32(q,true));q+=4;}}
  const po=q,zo=po+16*n+16;const get=(i)=>[dv.getFloat64(po+16*i,true),dv.getFloat64(po+16*i+8,true),hasZ?dv.getFloat64(zo+8*i,true):0];
  parts.push(n);
  for(let k=0;k<np;k++){const a=parts[k],b=parts[k+1];const P=[];for(let i=a;i<b;i++)P.push(get(i));if(P.length<2)continue;
   const kind=t===31?pt[k]:((t===5||t===15||t===25)?2:-1);
   if(kind===0){const id=P.map(v=>gb.addD(v[0],v[1],v[2]));for(let i=2;i<id.length;i++)(i%2===0)?gb.tri(id[i-2],id[i-1],id[i]):gb.tri(id[i-1],id[i-2],id[i]);}
   else if(kind===1){const id=P.map(v=>gb.addD(v[0],v[1],v[2]));for(let i=2;i<id.length;i++)gb.tri(id[0],id[i-1],id[i]);}
   else if(kind>=2){const R=P.slice();const same=R.length>1&&R[0][0]===R[R.length-1][0]&&R[0][1]===R[R.length-1][1]&&R[0][2]===R[R.length-1][2];if(same)R.pop();
    if(R.length===3&&hasZ){const id=R.map(v=>gb.addD(v[0],v[1],v[2]));gb.tri(id[0],id[1],id[2]);}else gb.poly(R.map(v=>gb.addD(v[0],v[1],v[2])),true,row);}
   else gb.poly(P.map(v=>gb.add(v[0],v[1],v[2])),false,row);}}
 if(!gb.v.length)throw new Error('SHP tidak berisi geometri');
 return [gb.done('shp',{cols:dbf?dbf.cols:null})];
}

/* ---------- reader: MapInfo MIF/MID, TAB, DAT ---------- */
function parseMIF(base,u,W,aux){
 const L=lines(dec(u));let i=0,cols=[],delim='\t';
 for(;i<L.length;i++){const l=L[i].trim();if(/^Delimiter/i.test(l)){const m=l.match(/"(.)"/);if(m)delim=m[1];}
  else if(/^Columns/i.test(l)){const n=parseInt(l.split(/\s+/)[1],10);for(let k=0;k<n;k++)cols.push(L[++i].trim().split(/\s+/)[0]);}
  else if(/^Data/i.test(l)){i++;break;}}
 let mid=[];if(aux&&aux.mid)mid=lines(dec(aux.mid)).filter(x=>x.trim()!=='').map(x=>splitLine(x,delim));else W.push('MIF: file .mid tidak disertakan, atribut tidak dimuat.');
 const zc=cols.findIndex(c=>/^(z|rl|elev\w*|alt\w*)$/i.test(c));
 const gb=new GB(base);let obj=0;const skip={};
 const kw=/^\s*(Point|Line|Pline|Region|Multipoint|Text|Rect|RoundRect|Ellipse|Arc|None)\b/i;
 const rowZ=(r)=>{if(zc<0||!r)return 0;const v=parseFloat(r[zc]);return isFinite(v)?v:0;};
 while(i<L.length){const l=L[i];const m=kw.exec(l);if(!m){i++;continue;}
  const k=m[1].toLowerCase(),p=l.trim().split(/\s+/),row=mid[obj]||null,z=rowZ(row);obj++;i++;
  if(k==='point'){gb.point(gb.add(+p[1],+p[2],z),row);}
  else if(k==='line'){gb.poly([gb.add(+p[1],+p[2],z),gb.add(+p[3],+p[4],z)],false,row);}
  else if(k==='pline'){let np=0,multi=false;if(/multiple/i.test(l)){multi=true;np=+p[2];}else np=+p[1];
   const sections=multi?np:1;for(let s=0;s<sections;s++){const n=multi?parseInt(L[i++],10):np;const id=[];for(let j=0;j<n;j++){const q=L[i++].trim().split(/\s+/);id.push(gb.add(+q[0],+q[1],z));}gb.poly(id,false,row);}}
  else if(k==='region'){const np=+p[1];for(let s=0;s<np;s++){const n=parseInt(L[i++],10);const id=[];for(let j=0;j<n;j++){const q=L[i++].trim().split(/\s+/);id.push(gb.add(+q[0],+q[1],z));}
    if(id.length>1&&gb.v[3*id[0]]===gb.v[3*id[id.length-1]]&&gb.v[3*id[0]+1]===gb.v[3*id[id.length-1]+1])id.pop();gb.poly(id,true,row);}}
  else if(k==='multipoint'){const n=+p[1];for(let j=0;j<n;j++){const q=L[i++].trim().split(/\s+/);gb.point(gb.add(+q[0],+q[1],z),row);}}
  else if(k!=='none'){skip[k]=(skip[k]||0)+1;}
 }
 const sk=Object.keys(skip);if(sk.length)W.push('MIF: objek dilewati: '+sk.join(', '));
 if(!gb.v.length)throw new Error('MIF tidak berisi geometri yang dikenali');
 return [gb.done('mif',{cols:cols.length?cols:null})];
}
/* ---------- reader: MapInfo TAB native (.MAP + .ID + .DAT). Struktur objek mengikuti dokumentasi terbuka MITAB/GDAL. ---------- */
function readMAP(mapBuf,idBuf,W){
 const u=u8of(mapBuf),dv=new DataView(u.buffer,u.byteOffset,u.byteLength),iu=u8of(idBuf),idv=new DataView(iu.buffer,iu.byteOffset,iu.byteLength);
 if(u.length<512||dv.getInt32(0x100,true)!==42424242)throw new Error('file .MAP tidak dikenali (bukan MapInfo MAP)');
 const ver=dv.getInt16(0x104,true),bs=dv.getInt16(0x106,true)||512,quad=u[0x161],proj=u[0x16d],units=u[0x16f];
 const xs=dv.getFloat64(0x170,true),ys=dv.getFloat64(0x178,true),xd=dv.getFloat64(0x180,true),yd=dv.getFloat64(0x188,true),pp=[];for(let k=0;k<6;k++)pp.push(dv.getFloat64(0x190+8*k,true));
 const CX=(quad===2||quad===3||quad===0)?(n)=>-(n+xd)/xs:(n)=>(n-xd)/xs,CY=(quad===3||quad===4||quad===0)?(n)=>-(n+yd)/ys:(n)=>(n-yd)/ys;
 /* pembaca blok koordinat berantai (tipe 3: int16 tipe, int16 n, int32 berikut; data mulai byte 8) */
 function coordReader(ptr){let blk=Math.floor(ptr/bs)*bs,p=ptr;const need=(n)=>{if(p+n>blk+bs){const nx=dv.getInt32(blk+4,true);if(nx<=0||nx>=u.length)throw new Error('rantai blok koordinat .MAP terputus');blk=Math.floor(nx/bs)*bs;p=blk+8;}};
  return {i16:()=>{need(2);const v=dv.getInt16(p,true);p+=2;return v;},i32:()=>{need(4);const v=dv.getInt32(p,true);p+=4;return v;}};}
 const nrec=Math.floor(iu.length/4),out=new Array(nrec).fill(null),skip={};let nogeo=0;
 const COMP=new Set([1,4,7,10,13,16,19,22,25,37,40,43,46,49,52,55,58,61,64,67]);
 for(let r=0;r<nrec;r++){const o=idv.getInt32(4*r,true);if(o<=0||o+5>u.length){nogeo++;continue;}
  const t=u[o],b=Math.floor(o/bs)*bs,cx=dv.getInt32(b+4,true),cy=dv.getInt32(b+8,true),c=COMP.has(t);let q=o+5;
  try{
   if(t===1||t===2||t===40||t===41||t===43||t===44){const x=c?dv.getInt16(q,true)+cx:dv.getInt32(q,true),y=c?dv.getInt16(q+2,true)+cy:dv.getInt32(q+4,true);out[r]={k:'pt',P:[[CX(x),CY(y)]]};}
   else if(t===4||t===5){const g=(k)=>c?dv.getInt16(q+2*k,true)+(k%2?cy:cx):dv.getInt32(q+4*k,true);out[r]={k:'pl',S:[{P:[[CX(g(0)),CY(g(1))],[CX(g(2)),CY(g(3))]],closed:false}]};}
   else if(t===19||t===20||t===22||t===23){if(t>=22)q+=c?4:8;const g=(k)=>c?dv.getInt16(q+2*k,true)+(k%2?cy:cx):dv.getInt32(q+4*k,true),x0=CX(g(0)),y0=CY(g(1)),x1=CX(g(2)),y1=CY(g(3));out[r]={k:'pl',S:[{P:[[x0,y0],[x1,y0],[x1,y1],[x0,y1]],closed:true}]};}
   else if([7,8,13,14,37,38,46,47,49,50,58,59,61,62].indexOf(t)>=0){
    const v8=t>=58,v45=t>=46,simple=(t===7||t===8),region=[13,14,46,47,58,59].indexOf(t)>=0,ptr=dv.getInt32(q,true);let size=dv.getInt32(q+4,true)&0x7FFFFFFF;q+=8;
    let ns=1;if(!simple){if(v8){ns=dv.getInt32(q,true);q+=4;}else{ns=dv.getInt16(q,true);q+=2;}}if(v8)q+=33;
    let ox=0,oy=0;if(c){q+=4;ox=dv.getInt32(q,true);oy=dv.getInt32(q+4,true);}
    const R=coordReader(ptr),rd=()=>{const x=c?R.i16()+ox:R.i32(),y=c?R.i16()+oy:R.i32();return [CX(x),CY(y)];},S=[];
    if(simple){const n=Math.floor(size/(c?4:8)),P=[];for(let k=0;k<n;k++)P.push(rd());S.push({P:P,closed:false});}
    else{const nv=[];for(let s=0;s<ns;s++){nv.push(v45?R.i32():R.i16());if(v8)R.i32();else R.i16();if(c){R.i16();R.i16();R.i16();R.i16();}else{R.i32();R.i32();R.i32();R.i32();}R.i32();}
     for(let s=0;s<ns;s++){const P=[];for(let k=0;k<nv[s];k++)P.push(rd());if(region&&P.length>1&&P[0][0]===P[P.length-1][0]&&P[0][1]===P[P.length-1][1])P.pop();S.push({P:P,closed:region});}}
    out[r]={k:'pl',S:S};}
   else if(t===52||t===53||t===64||t===65){const ptr=dv.getInt32(q,true),n=dv.getInt32(q+4,true);q+=8+15+(t>=64?33:0)+2;let ox=0,oy=0;if(c){q+=4;ox=dv.getInt32(q,true);oy=dv.getInt32(q+4,true);}
    const R=coordReader(ptr),P=[];for(let k=0;k<n;k++){const x=c?R.i16()+ox:R.i32(),y=c?R.i16()+oy:R.i32();P.push([CX(x),CY(y)]);}out[r]={k:'pt',P:P};}
   else{const nm={10:'Arc',11:'Arc',16:'Text',17:'Text',25:'Ellipse',26:'Ellipse',55:'Collection',56:'Collection',67:'Collection',68:'Collection'}[t]||('tipe '+t);skip[nm]=(skip[nm]||0)+1;}
  }catch(e){skip['rusak']=(skip['rusak']||0)+1;}}
 const sk=Object.keys(skip);if(sk.length)W.push('TAB: objek dilewati: '+sk.map(k=>k+' ×'+skip[k]).join(', '));
 let crs=null,pj='tidak dikenal';if(proj===1)pj='lintang/bujur';else if(proj===0)pj='NonEarth (lokal)';else if(proj===8){pj='Transverse Mercator';const z=(pp[0]+183)/6;if(Math.abs(z-Math.round(z))<1e-6&&Math.abs(pp[2]-0.9996)<1e-6&&Math.abs(pp[3]-500000)<1e-3&&units===7){crs={zone:Math.round(z),south:pp[4]>1};pj='UTM zona '+crs.zone+(crs.south?'S':'N');}}else pj='proyeksi MapInfo #'+proj;
 return {objs:out,nogeo:nogeo,crs:crs,proj:pj,ver:ver};
}
/* .DAT native MapInfo: header mirip dBase, tetapi Integer/Float/Date biner; tipe kolom ada di definisi .TAB */
function tabFields(def){const m=/Fields\s+(\d+)([\s\S]*)/i.exec(def||'');if(!m)return null;const out=[],L=m[2].split(/\r?\n/);
 for(const l of L){const q=/^\s*(\S+)\s+(Char|Integer|SmallInt|LargeInt|Float|Decimal|Date|Time|DateTime|Logical)\b/i.exec(l);if(q)out.push({name:q[1],type:q[2].toLowerCase()});if(out.length>=+m[1])break;}
 return out.length?out:null;}
function parseDAT(buf,defs){
 const u=u8of(buf),dv=new DataView(u.buffer,u.byteOffset,u.byteLength),nrec=dv.getUint32(4,true),hl=dv.getUint16(8,true),rl=dv.getUint16(10,true),F=[];
 for(let p=32;p<hl-1&&u[p]!==0x0D;p+=32){let nm='';for(let i=0;i<11&&u[p+i];i++)nm+=String.fromCharCode(u[p+i]);F.push({name:nm,len:u[p+16],type:'char'});}
 const useDef=defs&&defs.length===F.length;if(useDef)F.forEach((f,i)=>{f.name=defs[i].name;f.type=defs[i].type;});
 const bin=(o,n)=>{for(let k=0;k<n;k++){const c=u[o+k];if(c!==0&&(c<32||c>126)&&c<160)return true;}return false;};
 if(!useDef&&nrec){let o=1;for(const f of F){let b=0,t=0;for(let r=0;r<Math.min(nrec,40);r++){const p=hl+r*rl+o;if(p+f.len>u.length)break;t++;if(bin(p,f.len)||(f.len===8&&u[p+7]>=0x3F&&u[p+7]<=0x41&&u[p]===0))b++;}if(t&&b>t*0.3)f.type=f.len===8?'float':f.len===4?'integer':f.len===2?'smallint':'char';o+=f.len;}}
 const p2=(n)=>String(n).padStart(2,'0'),rows=[],del=[],td=new TextDecoder('windows-1252');
 for(let r=0;r<nrec;r++){const o=hl+r*rl;if(o+rl>u.length)break;del.push(u[o]===0x2A);let p=o+1;const row=[];
  for(const f of F){let v='';switch(f.type){
    case 'float':{const x=dv.getFloat64(p,true);v=isFinite(x)?String(+x.toPrecision(15)):'';break;}
    case 'integer':v=String(dv.getInt32(p,true));break;case 'smallint':v=String(dv.getInt16(p,true));break;
    case 'largeint':v=String(dv.getBigInt64(p,true));break;
    case 'date':case 'datetime':{const y=dv.getInt16(p,true),mo=u[p+2],d=u[p+3];v=y?y+'-'+p2(mo)+'-'+p2(d):'';if(f.type==='datetime'&&y){const ms=dv.getInt32(p+4,true);if(ms>0)v+=' '+p2(Math.floor(ms/3600000))+':'+p2(Math.floor(ms/60000)%60);}break;}
    case 'time':{const ms=dv.getInt32(p,true);v=ms>=0?p2(Math.floor(ms/3600000))+':'+p2(Math.floor(ms/60000)%60)+':'+p2(Math.floor(ms/1000)%60):'';break;}
    default:{let e=p+f.len;while(e>p&&(u[e-1]===0||u[e-1]===32))e--;let b=p;while(b<e&&u[b]===32)b++;v=td.decode(u.subarray(b,e)).replace(/\0/g,'');}}
   row.push(v);p+=f.len;}rows.push(row);}
 return {cols:F.map(f=>f.name),rows:rows,del:del,types:F.map(f=>f.type)};
}
function parseTAB(base,u,W,aux){
 aux=aux||{};const def=u&&u.length?dec(u):'',ty=(/^\s*Type\s+(\w+)/mi.exec(def)||[,''])[1].toUpperCase();
 let tb=null;if(aux.dat){try{tb=(ty===''||ty==='NATIVE')?parseDAT(aux.dat,tabFields(def)):parseDBF(aux.dat,true);}catch(e){W.push('TAB: .DAT gagal dibaca ('+e.message+')');}}
 else if(ty&&ty!=='NATIVE'){const src=(/File\s+"([^"]+)"/i.exec(def)||[,''])[1];W.push('TAB bertipe '+ty+': atributnya ada di file sumber'+(src?' "'+src+'"':'')+', bukan di .DAT. Hanya geometri yang dimuat; untuk atribut, buka juga file itu sebagai CSV atau simpan tabel sebagai TAB native (Save Copy As) di MapInfo.');}
 if(aux.map&&aux.id){const M=readMAP(aux.map,aux.id,W),gb=new GB(base),cols=tb?tb.cols:['ID'];let n=0,zc=-1;
  if(tb)zc=tb.cols.findIndex(c=>/^(z|rl|elev\w*|alt\w*|elevasi)$/i.test(c.trim()));
  M.objs.forEach((o,i)=>{if(!o)return;if(tb&&tb.del[i])return;const row=tb?(tb.rows[i]||null):[String(i+1)];let z=0;if(zc>=0&&row){const v=parseFloat(row[zc]);if(isFinite(v))z=v;}n++;
   if(o.k==='pt')o.P.forEach(p=>gb.point(gb.add(p[0],p[1],z),row));else o.S.forEach(s=>{if(s.P.length>1)gb.poly(s.P.map(p=>gb.add(p[0],p[1],z)),s.closed,row);});});
  if(n){W.push('TAB: '+n+' objek dibaca dari .MAP (MapInfo v'+M.ver+', '+M.proj+')'+(M.nogeo?'; '+M.nogeo+' baris tanpa objek peta':'')+(zc>=0?'; Z dari kolom '+tb.cols[zc]:'')+'.');
   let zero=0;for(let k=0;k<gb.v.length;k+=3)if(Math.abs(gb.v[k])<1&&Math.abs(gb.v[k+1])<1e4)zero++;if(zero&&M.crs)W.push('TAB: '+zero+' titik berada di sekitar koordinat (0, 0), kemungkinan sampel tanpa koordinat. Zoom semua mengabaikannya.');
   return [gb.done('tab',{cols:cols,crs:M.crs,proj:M.proj})];}
  W.push('TAB: .MAP tidak berisi objek yang bisa dibaca; dicoba dari kolom koordinat tabel.');}
 else if(!aux.map||!aux.id)W.push('TAB: file .MAP dan .ID tidak disertakan, geometri tidak dimuat. Pilih .TAB, .DAT, .MAP, dan .ID bersamaan.');
 if(tb)return [fromTable(base,tb.cols,tb.rows.filter((r,i)=>!tb.del[i]),'tab',W)];
 throw new Error('TAB: tidak ada geometri (.MAP + .ID) maupun atribut (.DAT) yang bisa dibaca. Pilih semua file tabel bersamaan.');
}
function looksDBF(u){return u.length>32&&(u[0]===3||u[0]===0x83||u[0]===0x8B||u[0]===0xF5)&&u[u.length-1]===0x1A||(u.length>32&&u[0]===3&&new DataView(u.buffer,u.byteOffset,u.byteLength).getUint16(8,true)<u.length);}

/* ---------- parse dispatcher ---------- */
function parse(name,buf,aux){
 const u=u8of(buf),ext=((name.match(/\.([^.]+)$/)||[,''])[1]).toLowerCase(),base=name.replace(/\.[^.]+$/,'');const W=[];let g;
 const head=new TextDecoder('latin1').decode(u.subarray(0,16));
 if(ext==='msh'||/^%ARANZ/.test(head))g=parseMSH(base,u,W);
 else if(ext==='dxf')g=parseDXF(base,u,W);
 else if(ext==='obj')g=parseOBJ(base,u,W);
 else if(ext==='stl')g=parseSTL(base,u,W);
 else if(ext==='ply')g=parsePLY(base,u,W);
 else if(ext==='str')g=parseSTR(base,u,W);
 else if(ext==='shp')g=parseSHP(base,u,W,aux);
 else if(ext==='mif')g=parseMIF(base,u,W,aux);
 else if(ext==='tab')g=parseTAB(base,u,W,aux);
 else if(ext==='dtm')g=parseDTM(base,u,W,aux);
 else if(ext==='map'||ext==='id')throw new Error('File .'+ext.toUpperCase()+' MapInfo harus dipilih bersama pasangannya (.TAB, .DAT, .MAP, .ID bernama sama).');
 else if((ext==='dbf'||ext==='dat')&&looksDBF(u)){const t=ext==='dat'?(()=>{const q=parseDAT(u,null);q.rows=q.rows.filter((r,i)=>!q.del[i]);return q;})():parseDBF(u);g=[fromTable(base,t.cols,t.rows,ext,W)];}
 else{const t=parseTable(dec(u));if(!t.rows.length)throw new Error('Format file tidak dikenali');g=[fromTable(base,t.cols,t.rows,'csv',W)];}
 return {geoms:g,warn:W};
}
/* set file: grup per nama dasar -> {ext: ArrayBuffer} */
const PRIMARY=['shp','mif','tab'];
function groupFiles(items){ // items: [{name,buf}]
 const by=new Map();
 for(const it of items){const m=it.name.match(/^(.*)\.([^.]+)$/);const base=m?m[1]:it.name,ext=m?m[2].toLowerCase():'';let e=by.get(base.toLowerCase());if(!e){e={base:base,files:{}};by.set(base.toLowerCase(),e);}e.files[ext]=it.buf;}
 const jobs=[],strs=[];
 by.forEach(e=>{if(e.files.str)strs.push({name:e.base+'.str',buf:e.files.str});});
 const usedStr=new Set(),hasDtm=[];
 by.forEach(e=>{const f=e.files;
  if(f.shp)jobs.push({name:e.base+'.shp',buf:f.shp,aux:{dbf:f.dbf}});
  else if(f.mif)jobs.push({name:e.base+'.mif',buf:f.mif,aux:{mid:f.mid}});
  else if(f.tab||(f.map&&f.id))jobs.push({name:e.base+'.tab',buf:f.tab||new ArrayBuffer(0),aux:{dat:f.dat||f.dbf,map:f.map,id:f.id}});
  else for(const k in f){if(k==='shx'||k==='prj'||k==='cpg'||k==='sbn'||k==='sbx'||k==='ind'||(k==='mid'&&f.mif))continue;
   if(k==='dtm'){jobs.push({name:e.base+'.dtm',buf:f[k],aux:{strs:strs},dtm:true});hasDtm.push(e);continue;}
   jobs.push({name:e.base+'.'+k,buf:f[k]});}
 });
 /* STR yang dipakai DTM tidak dimuat ganda sebagai string */
 if(hasDtm.length){const ref=new Set();
  for(const j of jobs)if(j.dtm){const u=u8of(j.buf);let nl=0;while(nl<u.length&&u[nl]!==10&&nl<2000)nl++;const r=(new TextDecoder().decode(u.subarray(0,nl)).split(',')[0]||'').trim().toLowerCase().replace(/\.str$/,'');
   for(const s of strs){const n=s.name.toLowerCase().replace(/\.str$/,'');if(r&&(n===r||n.slice(-r.length)===r)||strs.length===1)ref.add(n);}}
  for(let i=jobs.length-1;i>=0;i--){const n=jobs[i].name.toLowerCase();if(/\.str$/.test(n)&&ref.has(n.replace(/\.str$/,'')))jobs.splice(i,1);}}
 return jobs;
}

/* ---------- writers ---------- */
function merge(gs,name){
 const gb=new GB(name||'gabungan');
 for(const g of gs){const o=gb.v.length/3;for(let i=0;i<g.V.length;i++)gb.v.push(g.V[i]);for(let i=0;i<g.F.length;i++)gb.f.push(g.F[i]+o);
  for(const p of g.P)gb.p.push({idx:Array.from(p.idx,i=>i+o),closed:p.closed,attr:p.attr});for(let i=0;i<g.PT.length;i++){gb.pt.push(g.PT[i]+o);gb.ptA.push(g.PA[i]||null);}}
 return gb.done('merge');
}
function safeName(s,max){let r=String(s).replace(/[^A-Za-z0-9_\-$]/g,'_');if(!r)r='LAYER';return r.slice(0,max||31);}
function uniq(names,max){const seen=new Set();return names.map(n=>{let b=safeName(n,max),r=b,k=2;while(seen.has(r.toLowerCase()))r=b.slice(0,(max||31)-3)+'_'+k++;seen.add(r.toLowerCase());return r;});}
function dxfOut(gs,o,W){
 const d=o.dec,nm=uniq(gs.map(g=>g.name));const O=[];
 O.push('0\nSECTION\n2\nHEADER\n9\n$ACADVER\n1\nAC1009\n0\nENDSEC');
 O.push('0\nSECTION\n2\nTABLES\n0\nTABLE\n2\nLTYPE\n70\n1\n0\nLTYPE\n2\nCONTINUOUS\n70\n0\n3\nSolid line\n72\n65\n73\n0\n40\n0.0\n0\nENDTAB\n0\nTABLE\n2\nLAYER\n70\n'+gs.length+nm.map((n,i)=>'\n0\nLAYER\n2\n'+n+'\n70\n0\n62\n'+ACI[i%ACI.length]+'\n6\nCONTINUOUS').join('')+'\n0\nENDTAB\n0\nENDSEC');
 O.push('0\nSECTION\n2\nENTITIES');
 gs.forEach((g,gi)=>{const ly=nm[gi],V=g.V,P=(i,x)=>fx(V[3*i+x],d);
  for(let t=0;t<g.F.length;t+=3){const a=g.F[t],b=g.F[t+1],c=g.F[t+2];let s='0\n3DFACE\n8\n'+ly;
   [a,b,c,c].forEach((v,j)=>{s+='\n'+(10+j)+'\n'+P(v,0)+'\n'+(20+j)+'\n'+P(v,1)+'\n'+(30+j)+'\n'+P(v,2);});O.push(s);}
  for(const p of g.P){let s='0\nPOLYLINE\n8\n'+ly+'\n66\n1\n70\n'+(p.closed?9:8);O.push(s);
   for(const i of p.idx)O.push('0\nVERTEX\n8\n'+ly+'\n10\n'+P(i,0)+'\n20\n'+P(i,1)+'\n30\n'+P(i,2)+'\n70\n32');O.push('0\nSEQEND\n8\n'+ly);}
  for(const i of g.PT)O.push('0\nPOINT\n8\n'+ly+'\n10\n'+P(i,0)+'\n20\n'+P(i,1)+'\n30\n'+P(i,2));});
 O.push('0\nENDSEC\n0\nEOF');
 return [{name:o.base+'.dxf',data:O.join('\n')+'\n'}];
}
function objOut(gs,o,W){
 const d=o.dec,O=['# Geo Pocket OBJ'];let off=0;const nm=uniq(gs.map(g=>g.name),60);
 gs.forEach((g,gi)=>{O.push('g '+nm[gi]);const V=g.V;for(let i=0;i<V.length;i+=3)O.push('v '+fx(V[i],d)+' '+fx(V[i+1],d)+' '+fx(V[i+2],d));
  for(let t=0;t<g.F.length;t+=3)O.push('f '+(g.F[t]+off+1)+' '+(g.F[t+1]+off+1)+' '+(g.F[t+2]+off+1));
  for(const p of g.P)O.push('l '+p.idx.map(i=>i+off+1).join(' ')+(p.closed?' '+(p.idx[0]+off+1):''));
  if(g.PT.length)O.push('p '+Array.from(g.PT,i=>i+off+1).join(' '));off+=V.length/3;});
 return [{name:o.base+'.obj',data:O.join('\n')+'\n'}];
}
function needMesh(gs,fmt,W){const m=merge(gs);if(!m.F.length)throw new Error(fmt+' hanya menyimpan mesh segitiga, tetapi lapisan terpilih tidak punya segitiga.');if(m.P.length||m.PT.length)W.push(fmt+': garis dan titik tidak ikut ditulis (hanya mesh).');return m;}
function normal(V,a,b,c){const ux=V[3*b]-V[3*a],uy=V[3*b+1]-V[3*a+1],uz=V[3*b+2]-V[3*a+2],wx=V[3*c]-V[3*a],wy=V[3*c+1]-V[3*a+1],wz=V[3*c+2]-V[3*a+2];let nx=uy*wz-uz*wy,ny=uz*wx-ux*wz,nz=ux*wy-uy*wx;const l=Math.sqrt(nx*nx+ny*ny+nz*nz)||1;return [nx/l,ny/l,nz/l];}
function stlOut(gs,o,W){
 const m=needMesh(gs,'STL',W),V=m.V,d=Math.max(o.dec,4),n=m.F.length/3;const O=['solid '+safeName(o.base,60)];
 for(let t=0;t<n;t++){const a=m.F[3*t],b=m.F[3*t+1],c=m.F[3*t+2],N=normal(V,a,b,c);O.push('facet normal '+N.map(v=>v.toExponential(5)).join(' ')+'\nouter loop');
  for(const v of [a,b,c])O.push('vertex '+fx(V[3*v],d)+' '+fx(V[3*v+1],d)+' '+fx(V[3*v+2],d));O.push('endloop\nendfacet');}
 O.push('endsolid '+safeName(o.base,60));return [{name:o.base+'.stl',data:O.join('\n')+'\n'}];
}
function stlbOut(gs,o,W){
 const m=needMesh(gs,'STL',W),V=m.V,n=m.F.length/3,out=new Uint8Array(84+50*n),dv=new DataView(out.buffer);
 out.set(enc('Geo Pocket binary STL'),0);dv.setUint32(80,n,true);
 let big=false;for(let i=0;i<V.length;i++)if(Math.abs(V[i])>1e5){big=true;break;}
 if(big)W.push('STL biner memakai float32: koordinat besar (UTM) kehilangan presisi hingga ±1 m. Pakai STL ASCII bila presisi penting.');
 for(let t=0;t<n;t++){const a=m.F[3*t],b=m.F[3*t+1],c=m.F[3*t+2],N=normal(V,a,b,c),p=84+50*t;for(let k=0;k<3;k++)dv.setFloat32(p+4*k,N[k],true);
  [a,b,c].forEach((v,j)=>{for(let k=0;k<3;k++)dv.setFloat32(p+12+12*j+4*k,V[3*v+k],true);});}
 return [{name:o.base+'.stl',data:out}];
}
function plyOut(gs,o,W){
 const m=needMesh(gs,'PLY',W),V=m.V,d=o.dec,O=['ply','format ascii 1.0','comment Geo Pocket','element vertex '+V.length/3,'property double x','property double y','property double z','element face '+m.F.length/3,'property list uchar int vertex_indices','end_header'];
 for(let i=0;i<V.length;i+=3)O.push(fx(V[i],d)+' '+fx(V[i+1],d)+' '+fx(V[i+2],d));for(let t=0;t<m.F.length;t+=3)O.push('3 '+m.F[t]+' '+m.F[t+1]+' '+m.F[t+2]);
 return [{name:o.base+'.ply',data:O.join('\n')+'\n'}];
}
function mshOut(gs,o,W){
 const m=needMesh(gs,'MSH',W),nv=m.V.length/3,nt=m.F.length/3;
 const hdr=enc('%ARANZ-1.0\n\n[index]\nTri Integer 3 '+nt+';\nLocation Double 3 '+nv+';\n\n[binary]');
 const out=new Uint8Array(hdr.length+12+12*nt+24*nv),dv=new DataView(out.buffer);out.set(hdr,0);let p=hdr.length;
 out.set([0xff,0x0f,0xf0,0x00,0x1b,0xde,0x83,0x42,0xca,0xc0,0xf3,0x3f],p);p+=12;
 for(let i=0;i<m.F.length;i++){dv.setInt32(p,m.F[i],true);p+=4;}for(let i=0;i<m.V.length;i++){dv.setFloat64(p,m.V[i],true);p+=8;}
 return [{name:o.base+'.msh',data:out}];
}
function csvOut(gs,o,W){
 const d=o.dec,sep=o.sep||',',O=[];
 const g0=gs[0];
 if(gs.length===1&&g0.meta.tableOnly){O.push(g0.meta.cols.join(sep));for(const r of g0.meta.rows)O.push(r.join(sep));return [{name:o.base+'.csv',data:O.join('\n')+'\n'}];}
 if(gs.length===1&&g0.meta.cols&&g0.meta.map&&g0.PT.length&&g0.PT.length===g0.PA.length){
  const mp=g0.meta.map,cols=g0.meta.cols;O.push(cols.join(sep));
  for(let k=0;k<g0.PT.length;k++){const i=g0.PT[k],r=g0.PA[k].slice();r[mp.x]=fx(g0.V[3*i],d);r[mp.y]=fx(g0.V[3*i+1],d);if(mp.z>=0)r[mp.z]=fx(g0.V[3*i+2],d);O.push(r.join(sep));}
  return [{name:o.base+'.csv',data:O.join('\n')+'\n'}];}
 const multi=gs.length>1;O.push('X'+sep+'Y'+sep+'Z'+(multi?sep+'LAYER':''));
 let mesh=false;for(const g of gs){if(g.F.length||g.P.length)mesh=true;const V=g.V;for(let i=0;i<V.length;i+=3)O.push(fx(V[i],d)+sep+fx(V[i+1],d)+sep+fx(V[i+2],d)+(multi?sep+g.name:''));}
 if(mesh)W.push('CSV: hanya koordinat vertex yang ditulis; hubungan segitiga/garis hilang.');
 return [{name:o.base+'.csv',data:O.join('\n')+'\n'}];
}
function strOut(gs,o,W){
 const d=o.dec,O=[safeName(o.base,60)+','+new Date().toISOString().slice(0,10)+',,','0, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000'];
 const sep='0, 0.000, 0.000, 0.000,',rec=(no,V,i)=>no+', '+fx(V[3*i+1],d)+', '+fx(V[3*i],d)+', '+fx(V[3*i+2],d)+',';
 let tri=false;
 gs.forEach((g,gi)=>{const no=gi+1,V=g.V;
  for(const p of g.P){for(const i of p.idx)O.push(rec(no,V,i));if(p.closed)O.push(rec(no,V,p.idx[0]));O.push(sep);}
  for(const i of g.PT){O.push(rec(no,V,i));O.push(sep);}
  if(g.F.length)tri=true;});
 if(tri)W.push('STR: mesh segitiga tidak ditulis ke STR (hanya garis/titik). Untuk permukaan/solid pilih format Surpac DTM + STR.');
 if(O.length<=2)throw new Error('Tidak ada garis atau titik untuk ditulis ke STR. Untuk mesh pilih Surpac DTM + STR.');
 O.push('0, 0.000, 0.000, 0.000, END');return [{name:o.base+'.str',data:O.join('\n')+'\n'}];
}

function dtmOut(gs,o,W){
 const meshes=gs.filter(g=>g.F.length);if(!meshes.length)throw new Error('DTM hanya untuk mesh segitiga; lapisan terpilih tidak punya segitiga.');
 if(meshes.length<gs.length)W.push('DTM: lapisan tanpa segitiga dilewati.');
 const f3=(v)=>fx(v,3),dt=new Date(),sd=('0'+dt.getDate()).slice(-2)+'-'+['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'][dt.getMonth()]+'-'+String(dt.getFullYear()).slice(-2);
 const nm=uniq(meshes.map(g=>g.name),40).map(n=>n.toLowerCase()),files=[];
 meshes.forEach((g,gi)=>{const sn=nm[gi],V=g.V,used=new Int32Array(V.length/3).fill(-1),vs=[],tri=[];
  for(let t=0;t<g.F.length;t+=3){tri.push([g.F[t],g.F[t+1],g.F[t+2]].map(v=>{if(used[v]<0){used[v]=vs.length;vs.push(v);}return used[v];}));}
  const S=[sn+','+sd+',,ssi_styles:styles.ssi','0, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000'];
  vs.forEach(v=>S.push('1, '+f3(V[3*v+1])+', '+f3(V[3*v])+', '+f3(V[3*v+2])+','));S.push('0, 0.000, 0.000, 0.000,','0, 0.000, 0.000, 0.000, END');
  const E={},key=(a,b)=>a<b?a+'_'+b:b+'_'+a;
  tri.forEach((a,ti)=>{[[a[0],a[1]],[a[1],a[2]],[a[2],a[0]]].forEach(e=>{(E[key(e[0],e[1])]=E[key(e[0],e[1])]||[]).push(ti);});});
  const st=meshStats(g),D=[sn+'.str,'+sd+',,ssi_styles:styles.ssi','0, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000','OBJECT, 1,','TRISOLATION, 1, neighbours=yes,validated=true,closed='+(st&&st.closed?'yes':'no')];
  tri.forEach((a,ti)=>{const nb=[[a[0],a[1]],[a[1],a[2]],[a[2],a[0]]].map(e=>{const L2=E[key(e[0],e[1])];for(let q=0;q<L2.length;q++)if(L2[q]!==ti)return L2[q]+1;return 0;});D.push((ti+1)+', '+(a[0]+1)+', '+(a[1]+1)+', '+(a[2]+1)+', '+nb.join(', ')+',');});D.push('END');
  files.push({name:sn+'.str',data:S.join('\r\n')+'\r\n'},{name:sn+'.dtm',data:D.join('\r\n')+'\r\n'});});
 W.push('DTM: pasangan .dtm + .str harus dibuka bersama di Surpac; nama file jangan diubah.');
 return files;
}
function prjWKT(u){if(!u)return null;const z=+u.zone,s=!!u.south;return 'PROJCS["WGS_1984_UTM_Zone_'+z+(s?'S':'N')+'",GEOGCS["GCS_WGS_1984",DATUM["D_WGS_1984",SPHEROID["WGS_1984",6378137.0,298.257223563]],PRIMEM["Greenwich",0.0],UNIT["Degree",0.0174532925199433]],PROJECTION["Transverse_Mercator"],PARAMETER["False_Easting",500000.0],PARAMETER["False_Northing",'+(s?'10000000.0':'0.0')+'],PARAMETER["Central_Meridian",'+(z*6-183)+'.0],PARAMETER["Scale_Factor",0.9996],PARAMETER["Latitude_Of_Origin",0.0],UNIT["Meter",1.0]]';}
function buildSHP(type,items){
 const isPt=type===11;let total=100;
 const sizes=items.map(it=>isPt?36:(4+32+8+4*it.parts.length+16*it.n+16+8*it.n));
 sizes.forEach(s=>total+=8+s);
 const shp=new Uint8Array(total),shx=new Uint8Array(100+8*items.length),dv=new DataView(shp.buffer),dx=new DataView(shx.buffer);
 let mn=[Infinity,Infinity,Infinity],mx=[-Infinity,-Infinity,-Infinity];
 const allpts=(it)=>isPt?[it.pt]:it.parts.flat();
 for(const it of items)for(const p of allpts(it))for(let k=0;k<3;k++){if(p[k]<mn[k])mn[k]=p[k];if(p[k]>mx[k])mx[k]=p[k];}
 if(!items.length){mn=[0,0,0];mx=[0,0,0];}
 for(const [d,len] of [[dv,total/2],[dx,(100+8*items.length)/2]]){d.setInt32(0,9994,false);d.setInt32(24,len,false);d.setInt32(28,1000,true);d.setInt32(32,type,true);
  [mn[0],mn[1],mx[0],mx[1],mn[2],mx[2],0,0].forEach((v,i)=>d.setFloat64(36+8*i,v,true));}
 let o=100;
 items.forEach((it,ri)=>{const cl=sizes[ri];dv.setInt32(o,ri+1,false);dv.setInt32(o+4,cl/2,false);dx.setInt32(100+8*ri,o/2,false);dx.setInt32(104+8*ri,cl/2,false);
  let p=o+8;dv.setInt32(p,type,true);
  if(isPt){dv.setFloat64(p+4,it.pt[0],true);dv.setFloat64(p+12,it.pt[1],true);dv.setFloat64(p+20,it.pt[2],true);dv.setFloat64(p+28,0,true);}
  else{const P=it.parts.flat();let a=[Infinity,Infinity,Infinity],b=[-Infinity,-Infinity,-Infinity];for(const q of P)for(let k=0;k<3;k++){if(q[k]<a[k])a[k]=q[k];if(q[k]>b[k])b[k]=q[k];}
   [a[0],a[1],b[0],b[1]].forEach((v,i)=>dv.setFloat64(p+4+8*i,v,true));dv.setInt32(p+36,it.parts.length,true);dv.setInt32(p+40,it.n,true);let q=p+44,s=0;
   for(const pt of it.parts){dv.setInt32(q,s,true);q+=4;s+=pt.length;}
   for(const pt of P){dv.setFloat64(q,pt[0],true);dv.setFloat64(q+8,pt[1],true);q+=16;}
   dv.setFloat64(q,a[2],true);dv.setFloat64(q+8,b[2],true);q+=16;for(const pt of P){dv.setFloat64(q,pt[2],true);q+=8;}}
  o+=8+cl;});
 return {shp:shp,shx:shx};
}
function shpOut(gs,o,W){
 const multi=gs.length>1,sets={tri:[],line:[],pt:[]},rows={tri:[],line:[],pt:[]};
 const attrMode=gs.length===1&&gs[0].meta.cols&&gs[0].meta.map&&gs[0].PT.length&&gs[0].PT.length===gs[0].PA.length;
 const ptAttr=!attrMode&&gs.length===1&&gs[0].meta.cols&&gs[0].PA.some(a=>a);
 const lineAttr=gs.length===1&&gs[0].meta.cols&&!gs[0].meta.map&&gs[0].P.some(p=>p.attr),lineCols0=lineAttr?gs[0].meta.cols:[],lineCols=lineAttr?lineCols0.concat(['Z_MEAN','LUAS_M2','PANJANG_M']):['ID','LAYER','Z_MEAN','LUAS_M2','PANJANG_M'];
 gs.forEach((g,gi)=>{const V=g.V,gp=(i)=>[V[3*i],V[3*i+1],V[3*i+2]];
  for(let t=0;t<g.F.length;t+=3){let r=[gp(g.F[t]),gp(g.F[t+1]),gp(g.F[t+2])];const ar=(r[1][0]-r[0][0])*(r[2][1]-r[0][1])-(r[2][0]-r[0][0])*(r[1][1]-r[0][1]);if(ar>0)r=[r[0],r[2],r[1]];r.push(r[0]);
   sets.tri.push({parts:[r],n:4});rows.tri.push([sets.tri.length,g.name,(r[0][2]+r[1][2]+r[2][2])/3]);}
  for(const p of g.P){let r=p.idx.map(gp);let ar=0,ln=0;for(let k=0;k<r.length;k++){const a=r[k],b=r[(k+1)%r.length];if(p.closed)ar+=a[0]*b[1]-b[0]*a[1];if(p.closed||k<r.length-1)ln+=Math.hypot(a[0]-b[0],a[1]-b[1]);}ar=p.closed?Math.abs(ar)/2:0;if(p.closed){r.push(r[0]);}sets.line.push({parts:[r],n:r.length,closed:p.closed});
   const zm=r.reduce((a,b)=>a+b[2],0)/r.length;rows.line.push(lineAttr?lineCols0.map((c,ci)=>p.attr&&p.attr[ci]!==undefined&&p.attr[ci]!==null?p.attr[ci]:'').concat([zm,ar,ln]):[sets.line.length,g.name,zm,ar,ln]);}
  for(let k=0;k<g.PT.length;k++){const i=g.PT[k];sets.pt.push({pt:gp(i)});rows.pt.push(attrMode?g.PA[k].map((v,ci)=>ci===g.meta.map.x?fx(V[3*i],o.dec):ci===g.meta.map.y?fx(V[3*i+1],o.dec):ci===g.meta.map.z?fx(V[3*i+2],o.dec):v):ptAttr?gs[0].meta.cols.map((c,ci)=>g.PA[k]&&g.PA[k][ci]!=null?g.PA[k][ci]:'').concat([V[3*i+2]]):[sets.pt.length,g.name,V[3*i+2]]);}});
 const kinds=['tri','line','pt'].filter(k=>sets[k].length);if(!kinds.length)throw new Error('Tidak ada geometri untuk ditulis ke SHP.');
 const files=[],prj=prjWKT(o.utm);const nameOf={tri:'_poligon',line:'_garis',pt:'_titik'};
 for(const k of kinds){const base=o.base+(kinds.length>1?nameOf[k]:'');let type=k==='pt'?11:15;
  if(k==='line'){type=sets.line.every(s=>s.closed)?15:13;if(type===15&&0){}
   if(sets.line.some(s=>s.closed)&&!sets.line.every(s=>s.closed)){W.push('SHP: garis tertutup dan terbuka dipisah menjadi dua shapefile.');
    const cl={parts:0},op=[];const A=[],B=[],ra=[],rb=[];sets.line.forEach((s,i)=>{(s.closed?A:B).push(s);(s.closed?ra:rb).push(rows.line[i]);});
    for(const [S,R,t,sfx] of [[A,ra,15,'_garis_tertutup'],[B,rb,13,'_garis']]){if(!S.length)continue;const b=buildSHP(t,S);files.push({name:o.base+sfx+'.shp',data:b.shp},{name:o.base+sfx+'.shx',data:b.shx},{name:o.base+sfx+'.dbf',data:buildDBF(lineCols,R)});if(prj)files.push({name:o.base+sfx+'.prj',data:prj});}
    continue;}}
  const b=buildSHP(type,sets[k]);files.push({name:base+'.shp',data:b.shp},{name:base+'.shx',data:b.shx});
  files.push({name:base+'.dbf',data:buildDBF(k==='pt'&&attrMode?gs[0].meta.cols:k==='pt'&&ptAttr?gs[0].meta.cols.concat(['Z']):k==='line'?lineCols:['ID','LAYER','Z_MEAN'],rows[k])});if(prj)files.push({name:base+'.prj',data:prj});}
 if(!prj)W.push('SHP: tanpa file .prj (sistem koordinat tidak diisi). Pilih zona UTM di opsi bila perlu.');
 return files;
}
function mifOut(gs,o,W){
 const d=o.dec;let cs='CoordSys NonEarth Units "m"';
 if(o.utm){const z=+o.utm.zone;cs='CoordSys Earth Projection 8, 104, "m", '+(z*6-183)+', 0, 0.9996, 500000, '+(o.utm.south?10000000:0);}
 /* atribut ikut ditulis bila semua lapisan memakai kolom yang sama (mis. satu tabel / satu kategori pemetaan) */
 const c0=gs[0].meta&&gs[0].meta.cols,XC=c0&&!gs[0].meta.map&&!gs[0].meta.tableOnly&&gs.every(g=>g.meta&&g.meta.cols&&g.meta.cols.join('|')===c0.join('|'))?c0:null,used=new Set(['ID','LAYER','TIPE','Z','NAMA','LUAS_M2']),XN=[],XW=[];
 if(XC){XC.forEach((c,k)=>{let b=String(c).replace(/[^A-Za-z0-9_]/g,'_').replace(/^([0-9])/,'_$1').slice(0,28)||'K'+k,nm=b,j=2;while(used.has(nm.toUpperCase()))nm=b+'_'+(j++);used.add(nm.toUpperCase());XN.push(nm);let w=1;for(const g of gs){for(const p of g.P)if(p.attr&&p.attr[k]!=null)w=Math.max(w,String(p.attr[k]).length);for(const a of g.PA)if(a&&a[k]!=null)w=Math.max(w,String(a[k]).length);}XW.push(Math.min(254,w));});}
 const M=['Version 300','Charset "WindowsLatin1"','Delimiter ","',cs,'Columns '+(6+XN.length),'  ID Integer','  LAYER Char(32)','  TIPE Char(8)','  Z Float','  NAMA Char(64)','  LUAS_M2 Float'].concat(XN.map((c,k)=>'  '+c+' Char('+XW[k]+')'),['Data']);const D=[];let n=0;const tri=[];
 const q=(v)=>'"'+String(v==null?'':v).replace(/"/g,"'").replace(/[\r\n]+/g,' ')+'"';
 const row=(ly,tp,z,nm,ar,at)=>{n++;D.push(n+','+q(ly)+',"'+tp+'",'+fx(z,d)+','+q(nm)+','+fx(ar||0,2)+(XN.length?','+XN.map((c,k)=>q(at?at[k]:'')).join(','):''));};
 for(const g of gs){const V=g.V,X=(i)=>fx(V[3*i],d)+' '+fx(V[3*i+1],d);
  for(let t=0;t<g.F.length;t+=3){const a=g.F[t],b=g.F[t+1],c=g.F[t+2];M.push('Region 1','  4','  '+X(a),'  '+X(b),'  '+X(c),'  '+X(a));row(g.name,'TRI',(V[3*a+2]+V[3*b+2]+V[3*c+2])/3);tri.push(1);}
  for(const p of g.P){const z=p.idx.reduce((s,i)=>s+V[3*i+2],0)/p.idx.length;if(p.closed){M.push('Region 1','  '+(p.idx.length+1),...p.idx.map(i=>'  '+X(i)),'  '+X(p.idx[0]));let ar=0;for(let k=0;k<p.idx.length;k++){const a=p.idx[k],b=p.idx[(k+1)%p.idx.length];ar+=V[3*a]*V[3*b+1]-V[3*b]*V[3*a+1];}row(g.name,'RING',z,p.attr&&p.attr[0],Math.abs(ar)/2,p.attr);}else{M.push('Pline '+p.idx.length,...p.idx.map(i=>'  '+X(i)));row(g.name,'LINE',z,p.attr&&p.attr[0],0,p.attr);}}
  for(let k=0;k<g.PT.length;k++){const i=g.PT[k];M.push('Point '+X(i));row(g.name,'PT',V[3*i+2],g.PA[k]&&!g.meta.map?g.PA[k][0]:'',0,g.PA[k]);}}
 if(!n)throw new Error('Tidak ada geometri untuk ditulis ke MIF.');
 if(tri.length)W.push('MIF: MapInfo 2D, segitiga ditulis sebagai Region bidang datar (tampak atas); Z rata-rata disimpan di kolom Z.');else W.push('MIF: Z disimpan di kolom atribut Z (MapInfo 2D).');
 return [{name:o.base+'.mif',data:M.join('\n')+'\n'},{name:o.base+'.mid',data:D.join('\n')+'\n'}];
}
const WRITERS={dtm:dtmOut,dxf:dxfOut,obj:objOut,stl:stlOut,stlb:stlbOut,ply:plyOut,msh:mshOut,csv:csvOut,str:strOut,shp:shpOut,mif:mifOut};
function write(fmt,gs,opt){
 const o=Object.assign({dec:3,sep:',',base:'hasil',utm:null},opt||{});const W=[];
 if(!WRITERS[fmt])throw new Error('Format tujuan tidak dikenal: '+fmt);
 if(!gs.length)throw new Error('Tidak ada lapisan yang dipilih.');
 const files=WRITERS[fmt](gs,o,W);return {files:files,warn:W};
}

/* ---------- ZIP (store) ---------- */
let CRC=null;
function crc32(u){if(!CRC){CRC=new Uint32Array(256);for(let n=0;n<256;n++){let c=n;for(let k=0;k<8;k++)c=c&1?0xEDB88320^(c>>>1):c>>>1;CRC[n]=c>>>0;}}let c=0xFFFFFFFF;for(let i=0;i<u.length;i++)c=CRC[(c^u[i])&255]^(c>>>8);return (c^0xFFFFFFFF)>>>0;}
function zip(files){
 const F=files.map(f=>({n:enc(f.name),d:typeof f.data==='string'?enc(f.data):f.data}));const now=new Date();
 const dt=((now.getHours()<<11)|(now.getMinutes()<<5)|(now.getSeconds()>>1))&0xFFFF,dd=(((now.getFullYear()-1980)<<9)|((now.getMonth()+1)<<5)|now.getDate())&0xFFFF;
 let size=22;F.forEach(f=>size+=30+f.n.length+f.d.length+46+f.n.length);
 const out=new Uint8Array(size),dv=new DataView(out.buffer);let p=0;const offs=[];
 for(const f of F){const c=crc32(f.d);offs.push(p);dv.setUint32(p,0x04034b50,true);dv.setUint16(p+4,20,true);dv.setUint16(p+6,0x0800,true);dv.setUint16(p+8,0,true);dv.setUint16(p+10,dt,true);dv.setUint16(p+12,dd,true);dv.setUint32(p+14,c,true);dv.setUint32(p+18,f.d.length,true);dv.setUint32(p+22,f.d.length,true);dv.setUint16(p+26,f.n.length,true);dv.setUint16(p+28,0,true);out.set(f.n,p+30);out.set(f.d,p+30+f.n.length);p+=30+f.n.length+f.d.length;f.c=c;}
 const cs=p;F.forEach((f,i)=>{dv.setUint32(p,0x02014b50,true);dv.setUint16(p+4,20,true);dv.setUint16(p+6,20,true);dv.setUint16(p+8,0x0800,true);dv.setUint16(p+10,0,true);dv.setUint16(p+12,dt,true);dv.setUint16(p+14,dd,true);dv.setUint32(p+16,f.c,true);dv.setUint32(p+20,f.d.length,true);dv.setUint32(p+24,f.d.length,true);dv.setUint16(p+28,f.n.length,true);dv.setUint32(p+42,offs[i],true);out.set(f.n,p+46);p+=46+f.n.length;});
 dv.setUint32(p,0x06054b50,true);dv.setUint16(p+8,F.length,true);dv.setUint16(p+10,F.length,true);dv.setUint32(p+12,p-cs,true);dv.setUint32(p+16,cs,true);
 return out;
}

return {WRITERS:WRITERS,fx:fx,safeName:safeName,uniq:uniq,enc:enc,dec:dec,lines:lines,u8of:u8of,crc32:crc32,prjWKT:prjWKT,FORMATS:FORMATS,SOFT:SOFT,PALETTE:PALETTE,parse:parse,groupFiles:groupFiles,write:write,zip:zip,merge:merge,applyXf:applyXf,bbox:bbox,meshStats:meshStats,remapPoints:remapPoints,guessMap:guessMap,mk:mk,GB:GB};
})();
if(typeof module!=='undefined')module.exports=GC;
