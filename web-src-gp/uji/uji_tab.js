/* Uji pembaca MapInfo TAB native (.MAP/.ID/.DAT) dengan data fiktif buatan GDAL: node web-src-gp/uji/uji_tab.js */
const GC=require('../core.js'),fs=require('fs'),path=require('path');let fail=0;const ok=(c,m)=>{console.log((c?'PASS ':'FAIL ')+m);if(!c)fail++;};
const D=path.join(__dirname,'data'),it=['tab','dat','map','id'].map(e=>{const b=fs.readFileSync(path.join(D,'campur_fiktif.'+e));return {name:'campur_fiktif.'+e,buf:b.buffer.slice(b.byteOffset,b.byteOffset+b.length)};});
const jobs=GC.groupFiles(it);ok(jobs.length===1&&jobs[0].aux.map&&jobs[0].aux.id&&jobs[0].aux.dat,'TAB + DAT + MAP + ID dikelompokkan jadi satu');
const r=GC.parse(jobs[0].name,jobs[0].buf,jobs[0].aux),g=r.geoms[0],near=(a,b)=>Math.abs(a-b)<0.01;
ok(g.PT.length===6,'titik: 1 + multipoint 5 = '+g.PT.length);
ok(g.P.length===6&&g.P.filter(p=>p.closed).length===4,'garis/poligon: 2 garis + 4 cincin (blok berlubang 2, multipoligon 2)');
ok(near(g.V[3*g.PT[0]],10010.5)&&near(g.V[3*g.PT[0]+1],20020.25),'koordinat titik tepat');
const s=g.P.find(p=>p.idx.length===300);ok(!!s&&near(g.V[3*s.idx[299]],10000+3*299),'string 300 titik melintasi blok koordinat');
const b=g.P.find(p=>p.closed&&p.attr&&p.attr[0]==='blok');ok(!!b&&b.idx.length===4&&b.attr[1]==='4','atribut .DAT menempel ke objek: NAMA = blok, NILAI (Float biner) = '+(b&&b.attr[1]));
ok(g.PA[0][0]==='titik'&&g.PA[0][1]==='1.5','teks tanpa byte NUL; Float 1.5 terbaca');
ok(g.meta.crs&&g.meta.crs.zone===50&&g.meta.crs.south===true,'proyeksi UTM 50S dikenali dari header .MAP');
console.log(fail?'GAGAL '+fail:'SEMUA LULUS');process.exit(fail?1:0);
