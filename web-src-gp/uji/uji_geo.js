/* Uji geo Geo Pocket (UTM, TIN/DEM, kontur, KML/GeoJSON): node web-src-gp/uji/uji_geo.js */
const T=require('fs').mkdtempSync(require('path').join(require('os').tmpdir(),'gp-'));
global.Delaunator=require('../../web-src/delaunator.min.js');
const GC=require('../core.js');require('../geo2.js');const fs=require('fs');
const rd=p=>{const b=fs.readFileSync(p);return b.buffer.slice(b.byteOffset,b.byteOffset+b.length);};
let fail=0;const ok=(c,m)=>{console.log((c?'PASS ':'FAIL ')+m);if(!c)fail++;};
const crs={zone:50,south:true};
// UTM
const u=GC.ll2utm(-8.95,117.54,50,true),b=GC.utm2ll(u[0],u[1],50,true);console.log('UTM',u,b);
ok(Math.abs(b[0]+8.95)<1e-9&&Math.abs(b[1]-117.54)<1e-9,'UTM bolak-balik');
const ll=GC.utm2ll(559757.513,9010800.988,50,true);fs.writeFileSync(T+'/utm.json',JSON.stringify({ll:ll,u:u}));
// topo STR -> TIN -> DEM -> kontur -> tif/asc
const R=''+require('path').resolve(__dirname,'../../docs')+'/';
const topo=GC.parse('LTH_topografi.str',rd(R+'tutorial-ow/data/LTH_topografi.str')).geoms[0];
let t0=Date.now();const tin=GC.buildTIN([topo],{step:2,factor:8});const cell=GC.niceCell(tin);const dem=GC.tinToDEM(tin,cell);
console.log('TIN',tin.X.length,'titik',tin.T.length/3,'seg buang',tin.dropped,'cell',cell,'DEM',dem.nx,dem.ny,dem.min.toFixed(2),dem.max.toFixed(2),Date.now()-t0,'ms');
const bb=GC.bbox(topo);ok(dem.min>=bb.min[2]-1e-3&&dem.max<=bb.max[2]+1e-3&&dem.count>0.5*dem.nx*dem.ny,'DEM dalam rentang Z sumber, terisi '+(100*dem.count/dem.nx/dem.ny).toFixed(0)+'%');
// cek interpolasi: titik sumber vs demZ
let se=0,n=0,mxe=0;for(let i=0;i<topo.V.length;i+=3*7){const z=GC.demZ(dem,topo.V[i],topo.V[i+1]);if(z===z){const e=Math.abs(z-topo.V[i+2]);se+=e;n++;if(e>mxe)mxe=e;}}
console.log('selisih DEM vs titik sumber: rata',(se/n).toFixed(3),'maks',mxe.toFixed(3),'n',n);ok(se/n<0.5,'DEM menghormati titik sumber (rata-rata < 0,5 m pada sel '+cell+' m)');
const g=GC.mk({name:'dem',src:'dem'});g.dem=dem;
fs.writeFileSync(T+'/dem.tif',GC.write('tif',[g],{base:'dem',utm:crs}).files[0].data);
fs.writeFileSync(T+'/dem.asc',GC.write('asc',[g],{base:'dem',utm:crs}).files[0].data);
const back=GC.parse('dem.asc',rd(T+'/dem.asc')).geoms[0].dem;ok(back.nx===dem.nx&&Math.abs(back.max-dem.max)<1e-2&&back.count===dem.count,'ASC bolak-balik');
t0=Date.now();const ct=GC.contours(dem,5,'Kontur 5 m');console.log('kontur',ct.P.length,'garis',ct.V.length/3,'titik',Date.now()-t0,'ms tertutup',ct.P.filter(p=>p.closed).length);
ok(ct.P.length>0&&ct.P.every(p=>p.idx.every(i=>Math.abs(ct.V[3*i+2]-(+p.attr[0]))<1e-9)),'kontur: Z = level');
fs.writeFileSync(T+'/kontur.dxf',GC.write('dxf',[ct],{base:'kontur'}).files[0].data);
const tm=GC.tinGeom(tin,'TIN');fs.writeFileSync(T+'/tin.dxf',GC.write('dxf',[tm],{base:'tin'}).files[0].data);
// mesh DXF topo (3DFACE) -> DEM langsung
const sim=GC.parse('SIM_topo_akhir_juni.dxf',rd(R+'tutorial-gcex/data/SIM_topo_akhir_juni.dxf')).geoms[0];const tin2=GC.buildTIN([sim]);const dem2=GC.tinToDEM(tin2,GC.niceCell(tin2));
ok(tin2.src==='mesh'&&dem2.count>0,'DXF 3DFACE → DEM memakai segitiga asli: '+dem2.nx+'×'+dem2.ny);
// vektor: poligon + garis + titik beratribut -> KML/KMZ/GeoJSON/SHP
const gb=new GC.GB('Blok');const P=[[559700,9010800,100],[559760,9010800,101],[559760,9010850,102],[559700,9010850,103]].map(p=>gb.add(...p));gb.poly(P,true,['OB-01','waste']);
gb.poly([gb.add(559700,9010700,90),gb.add(559800,9010720,95)],false,['Jalan','haul']);gb.point(gb.add(559730,9010825,101.5),['BM-1','patok']);
const v=gb.done('digit',{cols:['NAMA','KET']});v.color='#C2413B';
ok(Math.abs(GC.polyArea(v.V,v.P[0].idx)-3000)<1e-6,'luas poligon 60×50 = 3000 m²');
for(const f of ['kml','kmz','geojson','shp']){const w=GC.write(f,[v],{base:'vek',utm:crs,dec:3});w.files.forEach(x=>fs.writeFileSync(T+'/'+x.name,x.data));
 if(f==='kml'||f==='geojson'){const r=GC.parse(w.files[0].name,Buffer.from(w.files[0].data)).geoms[0];ok(GC.looksGeo(r),f+' terbaca sebagai lintang/bujur');GC.projectGeom(r,crs);
  let d=0;for(let i=0;i<3;i++)d=Math.max(d,Math.abs(r.V[i]-v.V[i]));ok(r.P.length===2&&r.PT.length===1&&r.P[0].closed&&d<0.002,f+' bolak-balik: 2 garis/poligon, 1 titik, selisih '+d.toExponential(1)+' m; atribut '+JSON.stringify(r.P[0].attr));}}
const pdf=GC.pdfFromJpeg(new Uint8Array([255,216,255,217]),1,1,297,210);ok(Buffer.from(pdf).toString('latin1').startsWith('%PDF-1.4')&&/startxref/.test(Buffer.from(pdf).toString('latin1')),'PDF: kerangka valid');
console.log(fail?'GAGAL '+fail:'SEMUA LULUS');
