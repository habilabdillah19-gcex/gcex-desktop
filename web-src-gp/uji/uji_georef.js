/* Uji georeferensi: afin dari titik kontrol + penulis GeoTIFF citra: node web-src-gp/uji/uji_georef.js */
global.Delaunator=function(){};const GC=require('../core.js');require('../geo2.js');let fail=0;const ok=(c,m)=>{console.log((c?'PASS ':'FAIL ')+m);if(!c)fail++;};
(async()=>{
 const th=12*Math.PI/180,s=0.5,A=s*Math.cos(th),B=s*Math.sin(th),D=s*Math.sin(th),E=-s*Math.cos(th),X0=559000,Y0=9011000,W=(c,r)=>[X0+A*(c-0.5)+B*(r-0.5),Y0+D*(c-0.5)+E*(r-0.5)];
 const P=[[100,100],[700,100],[700,500],[100,500],[400,300]].map(q=>({c:q[0],r:q[1],X:W(q[0],q[1])[0],Y:W(q[0],q[1])[1]})),T=GC.fitAffine(P);
 ok(T&&!T.err&&T.rms<1e-6&&Math.abs(T.aff[0]-A)<1e-9&&Math.abs(T.aff[1]-D)<1e-9&&Math.abs(T.aff[2]-B)<1e-9&&Math.abs(T.aff[3]-E)<1e-9&&Math.abs(T.aff[4]-X0)<1e-4,'afin 5 titik (rotasi 12 derajat, piksel 0,5 m) kembali tepat; RMS '+T.rms.toExponential(1));
 P[4].X+=2;const T2=GC.fitAffine(P);ok(T2.rms>0.5&&T2.res[4]>T2.res[0],'titik menyimpang 2 m tampak di residu (terbesar di titik itu: '+T2.res[4].toFixed(2)+' m)');
 const T3=GC.fitAffine([{c:100,r:100,X:10000,Y:20000},{c:700,r:500,X:10300,Y:19800}]);ok(T3.aff[0]===0.5&&T3.aff[3]===-0.5&&T3.aff[1]===0&&T3.aff[2]===0,'2 titik: sejajar sumbu, piksel 0,5 m');
 ok(!!GC.fitAffine([{c:0,r:0,X:0,Y:0},{c:100,r:100,X:1,Y:1},{c:200,r:200,X:2,Y:2}]).err,'titik segaris ditolak');
 ok(!!GC.fitAffine([{c:0,r:0,X:0,Y:0},{c:100,r:0,X:1,Y:1}]).err,'2 titik sebaris ditolak');
 const w=4,h=3,px=new Uint8ClampedArray(w*h*4).fill(255);px[0]=10;const t=await GC.writeTIFFImage(px,w,h,559000,9011000,0.5,0.5,{zone:50,south:true},true),dv=new DataView(t.buffer);
 let tags={};const n=dv.getUint16(8,true);for(let i=0;i<n;i++){const p=10+12*i;tags[dv.getUint16(p,true)]=[dv.getUint16(p+2,true),dv.getUint32(p+4,true),dv.getUint16(p+8,true)];}
 ok(t[0]===0x49&&dv.getUint16(2,true)===42&&tags[256][2]===4&&tags[257][2]===3&&tags[277][2]===4&&tags[338]&&tags[33550]&&tags[33922]&&tags[34735],'GeoTIFF RGBA: tag ukuran, alpha, skala piksel, tiepoint, geokey ada');
 const ids=Object.keys(tags).map(Number);ok(ids.every((v,i)=>!i||v>ids[i-1]),'tag TIFF urut naik');
 console.log(fail?'GAGAL '+fail:'SEMUA LULUS');process.exit(fail?1:0);})();
