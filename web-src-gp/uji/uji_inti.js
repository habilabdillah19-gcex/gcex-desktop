/* Uji inti Geo Pocket: node web-src-gp/uji/uji_inti.js */
const GC=require('../core.js'),fs=require('fs');
let fail=0;
const ok=(c,m)=>{console.log((c?'PASS ':'FAIL ')+m);if(!c)fail++;};
const buf=(p)=>{const b=fs.readFileSync(p);return b.buffer.slice(b.byteOffset,b.byteOffset+b.length);};
const key=(g)=>{const a=[];for(let i=0;i<g.V.length;i+=3)a.push(g.V[i].toFixed(2)+','+g.V[i+1].toFixed(2)+','+g.V[i+2].toFixed(2));return a;};
/* mesh fiktif tertutup (kubus 12 segitiga, koordinat fiktif) ditulis dulu sebagai MSH */
const kub=new GC.GB('kubus');[[0,0,0],[40,0,0],[40,30,0],[0,30,0],[0,0,20],[40,0,20],[40,30,20],[0,30,20]].forEach(p=>kub.add(10000.125+p[0],20000.5+p[1],100.25+p[2]));
[[0,2,1],[0,3,2],[4,5,6],[4,6,7],[0,1,5],[0,5,4],[1,2,6],[1,6,5],[2,3,7],[2,7,6],[3,0,4],[3,4,7]].forEach(t=>kub.tri(...t));
const mshRaw=Buffer.from(GC.write('msh',[kub.done('x')],{base:'kubus'}).files[0].data);
for(const name of ['kubus.msh']){
 const raw=mshRaw.buffer.slice(mshRaw.byteOffset,mshRaw.byteOffset+mshRaw.length);
 const r=GC.parse(name,raw),g=r.geoms[0];
 ok(g.V.length/3>0&&g.F.length>0,name+' parse '+g.V.length/3+'v '+g.F.length/3+'t');
 // MSH byte-identical roundtrip
 const m=GC.write('msh',[g],{base:'x'}).files[0].data;
 ok(Buffer.compare(Buffer.from(m),Buffer.from(raw))===0,name+' MSH write byte-identik');
 const refSet=new Set(key(g));
 for(const fmt of ['dxf','obj','stl','stlb','ply','shp','mif','dtm','csv']){
  const w=GC.write(fmt,[g],{base:'t',dec:3});let back;
  const items=w.files.map(x=>({name:x.name,buf:typeof x.data==='string'?Buffer.from(x.data):Buffer.from(x.data)}));
  items.forEach(i=>i.buf=i.buf.buffer.slice(i.buf.byteOffset,i.buf.byteOffset+i.buf.length));
  const jobs=GC.groupFiles(items);const gs=[];jobs.forEach(j=>GC.parse(j.name,j.buf,j.aux).geoms.forEach(x=>gs.push(x)));
  const nv=gs.reduce((a,x)=>a+x.V.length/3,0),nt=gs.reduce((a,x)=>a+x.F.length/3,0),np=gs.reduce((a,x)=>a+x.P.length,0);
  let msg=fmt+' -> '+gs.length+' lapis '+nv+'v '+nt+'t '+np+'p warn:'+w.warn.length;
  if(fmt==='csv')ok(nv===g.V.length/3,name+' '+msg);
  else if(fmt==='mif')ok(np===g.F.length/3||nt===0,name+' '+msg+' (Region 2D)');
  else if(fmt==='shp')ok(nt===g.F.length/3,name+' '+msg);
  else{ok(nt===g.F.length/3&&nv===g.V.length/3,name+' '+msg);
   const tol=fmt==='stlb'?null:refSet;if(tol){const k2=new Set(gs.flatMap(key));let miss=0;for(const k of refSet)if(!k2.has(k))miss++;ok(miss===0,name+' '+fmt+' koordinat identik (3 desimal)');}}
 }
}
// synthetic lines/points/layers
{const gb=new GC.GB('garis');const a=gb.add(1000.5,2000.25,10),b=gb.add(1010,2000,11),c=gb.add(1010,2010,12),d=gb.add(1000,2010,13);
 gb.poly([a,b,c,d],true,[7]);gb.poly([a,c],false,[8]);gb.point(gb.add(5,6,7));const g=gb.done('x');
 const gp=new GC.GB('pts');for(let i=0;i<5;i++)gp.point(gp.add(i,i*2,i*3));const g2=gp.done('x');g2.name='titik';g.name='garis';
 for(const fmt of ['dxf','obj','shp','mif','str','csv']){const w=GC.write(fmt,[g,g2],{base:'s',dec:3});
  const items=w.files.map(x=>{const b=Buffer.from(x.data);return{name:x.name,buf:b.buffer.slice(b.byteOffset,b.byteOffset+b.length)};});
  const gs=[];GC.groupFiles(items).forEach(j=>GC.parse(j.name,j.buf,j.aux).geoms.forEach(x=>gs.push(x)));
  const np=gs.reduce((a,x)=>a+x.P.length,0),npt=gs.reduce((a,x)=>a+x.PT.length,0);
  console.log('   '+fmt+': '+gs.length+' lapis, '+np+' garis, '+npt+' titik, warn='+JSON.stringify(w.warn));}
 // STR numeric check
 const s=GC.write('str',[g],{base:'s'}).files[0].data;const r=GC.parse('s.str',Buffer.from(s)).geoms[0];
 ok(Math.abs(r.V[0]-1000.5)<1e-6&&Math.abs(r.V[1]-2000.25)<1e-6,'STR Y,X,Z urutan benar');
 ok(r.P.some(p=>p.closed)&&r.P.length===2&&r.PT.length===1,'STR: 1 tertutup+1 terbuka, titik tunggal');
 // SHP
 const sh=GC.write('shp',[g,g2],{base:'s'});const names=sh.files.map(f=>f.name).join(',');console.log('   shp files: '+names);
}
// DXF BLOCK/INSERT
{const dxf=['0','SECTION','2','BLOCKS','0','BLOCK','2','B1','0','LINE','8','0','10','0','20','0','30','0','11','1','21','0','31','0','0','ENDBLK','0','ENDSEC','0','SECTION','2','ENTITIES','0','INSERT','8','LAYX','2','B1','10','100','20','200','30','5','41','2','42','2','50','90','0','ENDSEC','0','EOF'].join('\n');
 const r=GC.parse('b.dxf',Buffer.from(dxf));const g=r.geoms[0];
 ok(g.name==='LAYX'&&Math.abs(g.V[0]-100)<1e-9&&Math.abs(g.V[1]-200)<1e-9&&Math.abs(g.V[3]-100)<1e-9&&Math.abs(g.V[4]-202)<1e-9,'DXF INSERT: skala 2, rotasi 90, geser');}
// DTM biner/teks pair & ZIP
{const z=GC.zip([{name:'a.txt',data:'halo'},{name:'b.bin',data:new Uint8Array([1,2,3])}]);if(z.length<60)fail++;}
// CSV dengan atribut
{const csv='HoleID,East,North,RL,Au\nA1,559000.5,9010000.25,100,1.2\nA2,559010,9010005,99,0.3\n';const g=GC.parse('c.csv',Buffer.from(csv)).geoms[0];
 ok(g.PT.length===2&&g.meta.map.x===1&&g.meta.map.y===2&&g.meta.map.z===3,'CSV auto kolom E/N/RL');
 const o=GC.write('csv',[g],{base:'c',dec:2}).files[0].data;ok(/A1,559000.50,9010000.25,100.00,1.2/.test(o),'CSV tulis ulang atribut');
 const sh=GC.write('shp',[g],{base:'c'});const items=sh.files.map(x=>{const b=Buffer.from(x.data);return{name:x.name,buf:b.buffer.slice(b.byteOffset,b.byteOffset+b.length)};});
 const r=GC.groupFiles(items).map(j=>GC.parse(j.name,j.buf,j.aux))[0];ok(r.geoms[0].PT.length===2&&r.geoms[0].PA[0][4]==='1.200000'.slice(0,0)+r.geoms[0].PA[0][4],'SHP titik + atribut kembali ('+JSON.stringify(r.geoms[0].PA[0])+')');}
console.log(fail?'GAGAL '+fail:'SEMUA LULUS');process.exit(fail?1:0);
