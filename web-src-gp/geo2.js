'use strict';
/* Geo Pocket geo2 — CRS UTM, KML/GeoJSON, TIN/DEM/kontur, GeoTIFF & ASC (tanpa DOM, bisa diuji di Node) */
(function(GC){
const fx=GC.fx,enc=GC.enc,dec=GC.dec,u8of=GC.u8of;
const xmlEsc=(s)=>String(s==null?'':s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const xmlUn=(s)=>String(s).replace(/<!\[CDATA\[([\s\S]*?)\]\]>/g,'$1').replace(/&lt;/g,'<').replace(/&gt;/g,'>').replace(/&quot;/g,'"').replace(/&apos;/g,"'").replace(/&amp;/g,'&').trim();

/* ---------- UTM WGS84 (deret Krüger) ---------- */
const A_=6378137,F_=1/298.257223563,N_=F_/(2-F_),K0=0.9996,AA=A_/(1+N_)*(1+N_*N_/4+Math.pow(N_,4)/64);
const AL=[N_/2-2*N_*N_/3+5*N_*N_*N_/16,13*N_*N_/48-3*N_*N_*N_/5,61*N_*N_*N_/240];
const BE=[N_/2-2*N_*N_/3+37*N_*N_*N_/96,N_*N_/48+N_*N_*N_/15,17*N_*N_*N_/480];
const DE=[2*N_-2*N_*N_/3-2*N_*N_*N_,7*N_*N_/3-8*N_*N_*N_/5,56*N_*N_*N_/15];
function ll2utm(lat,lon,zone,south){
 const ph=lat*Math.PI/180,l=(lon-(zone*6-183))*Math.PI/180,c=2*Math.sqrt(N_)/(1+N_);
 const t=Math.sinh(Math.atanh(Math.sin(ph))-c*Math.atanh(c*Math.sin(ph))),xi=Math.atan2(t,Math.cos(l)),et=Math.atanh(Math.sin(l)/Math.sqrt(1+t*t));
 let E=et,Nn=xi;for(let j=1;j<=3;j++){E+=AL[j-1]*Math.cos(2*j*xi)*Math.sinh(2*j*et);Nn+=AL[j-1]*Math.sin(2*j*xi)*Math.cosh(2*j*et);}
 return [500000+K0*AA*E,(south?10000000:0)+K0*AA*Nn];
}
function utm2ll(E,Nn,zone,south){
 const xi=(Nn-(south?10000000:0))/(K0*AA),et=(E-500000)/(K0*AA);let x=xi,e=et;
 for(let j=1;j<=3;j++){x-=BE[j-1]*Math.sin(2*j*xi)*Math.cosh(2*j*et);e-=BE[j-1]*Math.cos(2*j*xi)*Math.sinh(2*j*et);}
 const ch=Math.asin(Math.sin(x)/Math.cosh(e));let ph=ch;for(let j=1;j<=3;j++)ph+=DE[j-1]*Math.sin(2*j*ch);
 return [ph*180/Math.PI,(zone*6-183)+Math.atan2(Math.sinh(e),Math.cos(x))*180/Math.PI];
}
function looksGeo(g){const V=g.V0||g.V;if(!V||!V.length)return false;for(let i=0;i<V.length;i+=3)if(Math.abs(V[i])>180||Math.abs(V[i+1])>90)return false;return true;}
function projectGeom(g,crs){const V=g.V0;for(let i=0;i<V.length;i+=3){const p=ll2utm(V[i+1],V[i],crs.zone,crs.south);V[i]=p[0];V[i+1]=p[1];}GC.applyXf(g);}
function crsName(c){return c?'WGS84 / UTM zona '+c.zone+(c.south?'S':'N')+' (EPSG:'+((c.south?32700:32600)+(+c.zone))+')':'Lokal / tidak ditentukan';}

/* ---------- geometri bantu ---------- */
function polyArea(V,idx){let a=0;const n=idx.length;for(let k=0;k<n;k++){const i=idx[k],j=idx[(k+1)%n];a+=V[3*i]*V[3*j+1]-V[3*j]*V[3*i+1];}return Math.abs(a)/2;}
function polyLen(V,idx,closed,d3){let L=0;const n=idx.length,m=closed?n:n-1;for(let k=0;k<m;k++){const i=idx[k],j=idx[(k+1)%n];L+=Math.hypot(V[3*i]-V[3*j],V[3*i+1]-V[3*j+1],d3?V[3*i+2]-V[3*j+2]:0);}return L;}
function setGeom(g,V,P,PT,PA){g.V0=Float64Array.from(V);g.V=Float64Array.from(V);g.P=P;g.PT=Uint32Array.from(PT||[]);g.PA=PA||[];g.xf={swap:false,flipZ:false,dx:0,dy:0,dz:0};g._ms=undefined;}
function bake(g){g.V0=Float64Array.from(g.V);g.xf={swap:false,flipZ:false,dx:0,dy:0,dz:0};}
function addPoly(g,pts,closed,attr){bake(g);const o=g.V.length/3,V=new Float64Array(g.V.length+pts.length*3);V.set(g.V);pts.forEach((p,k)=>V.set([p[0],p[1],p[2]||0],g.V.length+3*k));
 g.V=V;g.V0=Float64Array.from(V);g.P.push({idx:pts.map((_,k)=>o+k),closed:!!closed,attr:attr||null});return g.P.length-1;}
function addPoint(g,p,attr){bake(g);const o=g.V.length/3,V=new Float64Array(g.V.length+3);V.set(g.V);V.set([p[0],p[1],p[2]||0],g.V.length);g.V=V;g.V0=Float64Array.from(V);
 const PT=new Uint32Array(g.PT.length+1);PT.set(g.PT);PT[g.PT.length]=o;g.PT=PT;g.PA.push(attr||null);return g.PT.length-1;}
function snapshot(g){return {V:Float64Array.from(g.V),P:g.P.map(p=>({idx:p.idx.slice(),closed:p.closed,attr:p.attr?p.attr.slice():null})),PT:Uint32Array.from(g.PT),PA:g.PA.map(a=>a?a.slice():null)};}
function restore(g,s){g.V=Float64Array.from(s.V);g.V0=Float64Array.from(s.V);g.P=s.P;g.PT=s.PT;g.PA=s.PA;g.xf={swap:false,flipZ:false,dx:0,dy:0,dz:0};g._ms=undefined;}

/* ---------- KML ---------- */
function kmlColor(hex,a){const h=hex.replace('#','');return (Math.round(a*255).toString(16).padStart(2,'0')+h.slice(4,6)+h.slice(2,4)+h.slice(0,2)).toLowerCase();}
function kmlDoc(gs,o,W){
 if(!o.utm)throw new Error('KML memakai lintang/bujur WGS84: tentukan dulu sistem koordinat proyek (Proyek → Sistem koordinat).');
 const z=o.utm.zone,s=o.utm.south,O=['<?xml version="1.0" encoding="UTF-8"?>','<kml xmlns="http://www.opengis.net/kml/2.2">','<Document>','<name>'+xmlEsc(o.base)+'</name>'];let n=0,tri=0;
 gs.forEach((g,gi)=>{const c=g.color||'#17806B';O.push('<Style id="s'+gi+'"><LineStyle><color>'+kmlColor(c,1)+'</color><width>2</width></LineStyle><PolyStyle><color>'+kmlColor(c,0.35)+'</color></PolyStyle><IconStyle><color>'+kmlColor(c,1)+'</color><scale>0.7</scale></IconStyle></Style>');});
 const amode=o.clamp?'clampToGround':'absolute';
 gs.forEach((g,gi)=>{const V=g.V,cols=g.meta.cols,C=(i)=>{const p=utm2ll(V[3*i],V[3*i+1],z,s);return p[1].toFixed(8)+','+p[0].toFixed(8)+','+fx(V[3*i+2],2);};
  const ext=(a)=>{if(!a||!cols)return '';let h='<ExtendedData>';a.forEach((v,k)=>{if(cols[k]!==undefined&&v!==null&&v!==undefined&&v!=='')h+='<Data name="'+xmlEsc(cols[k])+'"><value>'+xmlEsc(v)+'</value></Data>';});return h+'</ExtendedData>';};
  const nm=(a,d)=>xmlEsc(a&&a[0]!==null&&a[0]!==undefined&&a[0]!==''&&!(g.meta.map)?a[0]:d);
  O.push('<Folder><name>'+xmlEsc(g.name)+'</name>');
  g.P.forEach((p,k)=>{n++;const cs=p.idx.map(C).join(' ');O.push('<Placemark><name>'+nm(p.attr,g.name+' '+(k+1))+'</name><styleUrl>#s'+gi+'</styleUrl>'+ext(p.attr)+(p.closed&&p.idx.length>2?'<Polygon><altitudeMode>'+amode+'</altitudeMode><outerBoundaryIs><LinearRing><coordinates>'+cs+' '+C(p.idx[0])+'</coordinates></LinearRing></outerBoundaryIs></Polygon>':'<LineString><altitudeMode>'+amode+'</altitudeMode><coordinates>'+cs+'</coordinates></LineString>')+'</Placemark>');});
  for(let k=0;k<g.PT.length;k++){n++;const a=g.PA[k];O.push('<Placemark><name>'+xmlEsc(a&&a[0]!==null&&a[0]!==undefined?a[0]:'')+'</name><styleUrl>#s'+gi+'</styleUrl>'+ext(a)+'<Point><altitudeMode>'+amode+'</altitudeMode><coordinates>'+C(g.PT[k])+'</coordinates></Point></Placemark>');}
  if(g.F.length){if(g.F.length/3>60000)throw new Error('Mesh '+g.name+' terlalu besar untuk KML ('+g.F.length/3+' segitiga; batas 60.000).');tri+=g.F.length/3;n++;
   O.push('<Placemark><name>'+xmlEsc(g.name)+'</name><styleUrl>#s'+gi+'</styleUrl><MultiGeometry>');
   for(let t=0;t<g.F.length;t+=3)O.push('<Polygon><altitudeMode>absolute</altitudeMode><outerBoundaryIs><LinearRing><coordinates>'+C(g.F[t])+' '+C(g.F[t+1])+' '+C(g.F[t+2])+' '+C(g.F[t])+'</coordinates></LinearRing></outerBoundaryIs></Polygon>');
   O.push('</MultiGeometry></Placemark>');}
  O.push('</Folder>');});
 if(!n)throw new Error('Tidak ada geometri untuk ditulis ke KML.');
 if(tri)W.push('KML: mesh ditulis sebagai poligon 3D (ketinggian absolut); di Google Earth bagian di bawah permukaan tanah tidak terlihat.');
 O.push('</Document>','</kml>');return O.join('\n')+'\n';
}
function parseKML(base,u,W){
 const s=dec(u),gb=new GC.GB(base),recs=[],keys=[];
 const re=/<(?:\w+:)?Placemark[\s>][\s\S]*?<\/(?:\w+:)?Placemark>/g;let m;
 const coords=(t)=>t.trim().split(/\s+/).map(c=>c.split(',').map(Number)).filter(c=>c.length>=2&&isFinite(c[0])&&isFinite(c[1]));
 while((m=re.exec(s))){const b=m[0],nm=(/<(?:\w+:)?name>([\s\S]*?)<\/(?:\w+:)?name>/.exec(b)||[,''])[1],at={};
  const rd=/<(?:\w+:)?(?:Simple)?Data\s+name="([^"]*)"[^>]*>([\s\S]*?)<\/(?:\w+:)?(?:Simple)?Data>/g;let d;
  while((d=rd.exec(b))){const v=/<(?:\w+:)?value>([\s\S]*?)<\/(?:\w+:)?value>/.exec(d[2]);at[d[1]]=xmlUn(v?v[1]:d[2]);if(keys.indexOf(d[1])<0)keys.push(d[1]);}
  const rg=/<(?:\w+:)?(Point|LineString|LinearRing)[\s>][\s\S]*?<(?:\w+:)?coordinates>([\s\S]*?)<\/(?:\w+:)?coordinates>/g;let q;
  while((q=rg.exec(b)))recs.push({t:q[1],c:coords(q[2]),nm:xmlUn(nm),at:at});}
 const cols=['NAME'].concat(keys);
 for(const r of recs){const a=[r.nm].concat(keys.map(k=>r.at[k]===undefined?'':r.at[k]));
  if(r.t==='Point'){if(r.c[0])gb.point(gb.add(r.c[0][0],r.c[0][1],r.c[0][2]||0),a);}
  else{let c=r.c,closed=r.t==='LinearRing';if(closed&&c.length>1&&c[0][0]===c[c.length-1][0]&&c[0][1]===c[c.length-1][1])c=c.slice(0,-1);gb.poly(c.map(p=>gb.add(p[0],p[1],p[2]||0)),closed,a);}}
 if(!gb.v.length)throw new Error('KML tidak berisi Placemark bergeometri');
 return [gb.done('kml',{cols:cols,geo:true})];
}
GC.WRITERS.kml=(gs,o,W)=>[{name:o.base+'.kml',data:kmlDoc(gs,o,W)}];
GC.WRITERS.kmz=(gs,o,W)=>[{name:o.base+'.kmz',data:GC.zip([{name:'doc.kml',data:kmlDoc(gs,o,W)}])}];

/* ---------- GeoJSON ---------- */
function geojsonOut(gs,o,W){
 const z=o.utm&&o.utm.zone,s=o.utm&&o.utm.south,F=[];let tri=0;
 if(!o.utm)W.push('GeoJSON: sistem koordinat proyek belum ditentukan; koordinat ditulis apa adanya (bukan lintang/bujur WGS84).');
 for(const g of gs){const V=g.V,cols=g.meta.cols,C=(i)=>{if(!o.utm)return [+fx(V[3*i],o.dec),+fx(V[3*i+1],o.dec),+fx(V[3*i+2],3)];const p=utm2ll(V[3*i],V[3*i+1],z,s);return [+p[1].toFixed(8),+p[0].toFixed(8),+fx(V[3*i+2],3)];};
  const pr=(a,x)=>{const r={layer:g.name};if(a&&cols)a.forEach((v,k)=>{if(cols[k]!==undefined)r[cols[k]]=(v!==''&&v!==null&&isFinite(+v))?+v:v;});return Object.assign(r,x||{});};
  g.P.forEach(p=>{const c=p.idx.map(C);if(p.closed&&c.length>2){c.push(c[0]);F.push({type:'Feature',properties:pr(p.attr,{luas_m2:+polyArea(V,p.idx).toFixed(2)}),geometry:{type:'Polygon',coordinates:[c]}});}else F.push({type:'Feature',properties:pr(p.attr),geometry:{type:'LineString',coordinates:c}});});
  for(let k=0;k<g.PT.length;k++)F.push({type:'Feature',properties:pr(g.PA[k]),geometry:{type:'Point',coordinates:C(g.PT[k])}});
  if(g.F.length){tri+=g.F.length/3;const mp=[];for(let t=0;t<g.F.length;t+=3)mp.push([[C(g.F[t]),C(g.F[t+1]),C(g.F[t+2]),C(g.F[t])]]);F.push({type:'Feature',properties:{layer:g.name,tipe:'mesh'},geometry:{type:'MultiPolygon',coordinates:mp}});}}
 if(!F.length)throw new Error('Tidak ada geometri untuk ditulis ke GeoJSON.');
 if(tri)W.push('GeoJSON: mesh ditulis sebagai satu MultiPolygon per lapisan.');
 return [{name:o.base+'.geojson',data:JSON.stringify({type:'FeatureCollection',name:o.base,features:F})+'\n'}];
}
function parseGeoJSON(base,u,W){
 let j;try{j=JSON.parse(dec(u));}catch(e){throw new Error('GeoJSON tidak valid: '+e.message);}
 const feats=j.type==='FeatureCollection'?j.features:j.type==='Feature'?[j]:[{type:'Feature',properties:{},geometry:j}],keys=[];
 for(const f of feats)for(const k in (f.properties||{}))if(keys.indexOf(k)<0)keys.push(k);
 const gb=new GC.GB(base);
 const ring=(c,closed,a)=>{if(closed&&c.length>1&&c[0][0]===c[c.length-1][0]&&c[0][1]===c[c.length-1][1])c=c.slice(0,-1);gb.poly(c.map(p=>gb.add(+p[0],+p[1],+p[2]||0)),closed,a);};
 const geom=(G,a)=>{if(!G)return;const c=G.coordinates;switch(G.type){
  case 'Point':gb.point(gb.add(+c[0],+c[1],+c[2]||0),a);break;case 'MultiPoint':c.forEach(p=>gb.point(gb.add(+p[0],+p[1],+p[2]||0),a));break;
  case 'LineString':ring(c,false,a);break;case 'MultiLineString':c.forEach(l=>ring(l,false,a));break;
  case 'Polygon':c.forEach(r=>ring(r,true,a));break;case 'MultiPolygon':c.forEach(pg=>pg.forEach(r=>ring(r,true,a)));break;
  case 'GeometryCollection':(G.geometries||[]).forEach(x=>geom(x,a));break;}};
 for(const f of feats){const p=f.properties||{};geom(f.geometry,keys.map(k=>p[k]===undefined||p[k]===null?'':(typeof p[k]==='object'?JSON.stringify(p[k]):String(p[k]))));}
 if(!gb.v.length)throw new Error('GeoJSON tidak berisi geometri');
 return [gb.done('geojson',{cols:keys.length?keys:null})];
}
GC.WRITERS.geojson=geojsonOut;

/* ---------- TIN (Delaunay; aturan GC-Ex: rapatkan string, satukan titik < 1 mm, buang segitiga tepi panjang) ---------- */
function getDel(){if(typeof Delaunator!=='undefined')return Delaunator;if(typeof globalThis!=='undefined'&&globalThis.Delaunator)return globalThis.Delaunator;throw new Error('Delaunator tidak tersedia');}
function buildTIN(gs,opt){
 opt=Object.assign({step:2,factor:8},opt||{});
 const meshOnly=gs.length&&gs.every(g=>g.F.length&&!g.P.length&&!g.PT.length);
 if(meshOnly){let n=0,nt=0;for(const g of gs){n+=g.V.length/3;nt+=g.F.length/3;}const X=new Float64Array(n),Y=new Float64Array(n),Z=new Float64Array(n),T=new Uint32Array(nt*3);let o=0,q=0;
  for(const g of gs){for(let i=0;i<g.V.length/3;i++){X[o+i]=g.V[3*i];Y[o+i]=g.V[3*i+1];Z[o+i]=g.V[3*i+2];}for(let i=0;i<g.F.length;i++)T[q++]=g.F[i]+o;o+=g.V.length/3;}
  return {X:X,Y:Y,Z:Z,T:T,src:'mesh',dropped:0};}
 const M=new Map(),X=[],Y=[],Z=[],K=[];
 const put=(x,y,z)=>{if(!isFinite(x)||!isFinite(y)||!isFinite(z))return;const k=Math.round(x*1000)+':'+Math.round(y*1000);const j=M.get(k);if(j!==undefined){Z[j]+=z;K[j]++;return;}M.set(k,X.length);X.push(x);Y.push(y);Z.push(z);K.push(1);};
 for(const g of gs){const V=g.V;
  for(const p of g.P){const n=p.idx.length,m=p.closed?n:n-1;for(let k=0;k<n;k++)put(V[3*p.idx[k]],V[3*p.idx[k]+1],V[3*p.idx[k]+2]);
   if(opt.step>0)for(let k=0;k<m;k++){const a=p.idx[k],b=p.idx[(k+1)%n],L=Math.hypot(V[3*a]-V[3*b],V[3*a+1]-V[3*b+1]),ns=Math.floor(L/opt.step);
    for(let q=1;q<ns;q++){const t=q/ns;put(V[3*a]+(V[3*b]-V[3*a])*t,V[3*a+1]+(V[3*b+1]-V[3*a+1])*t,V[3*a+2]+(V[3*b+2]-V[3*a+2])*t);}}}
  for(const i of g.PT)put(V[3*i],V[3*i+1],V[3*i+2]);
  if(g.F.length){const seen=new Uint8Array(V.length/3);for(const i of g.F)if(!seen[i]){seen[i]=1;put(V[3*i],V[3*i+1],V[3*i+2]);}}}
 const n=X.length;if(n<3)throw new Error('Titik berelevasi kurang dari 3; tidak bisa membuat permukaan.');
 for(let i=0;i<n;i++)Z[i]/=K[i];
 const ox=X[0],oy=Y[0],C=new Float64Array(2*n);for(let i=0;i<n;i++){C[2*i]=X[i]-ox;C[2*i+1]=Y[i]-oy;}
 const D=getDel(),d=new D(C);let T=d.triangles,nt=T.length/3,dropped=0;if(!nt)throw new Error('Triangulasi gagal (titik segaris?).');
 if(opt.factor>0){const len=new Float64Array(nt);for(let t=0;t<nt;t++){let mx=0;for(let k=0;k<3;k++){const a=T[3*t+k],b=T[3*t+(k+1)%3],L=Math.hypot(C[2*a]-C[2*b],C[2*a+1]-C[2*b+1]);if(L>mx)mx=L;}len[t]=mx;}
  const srt=Float64Array.from(len).sort(),lim=srt[nt>>1]*opt.factor,H=d.halfedges,dead=new Uint8Array(nt),st=[];
  for(let e=0;e<H.length;e++)if(H[e]<0){const t=(e/3)|0;if(len[t]>lim&&!dead[t]){dead[t]=1;st.push(t);}}
  while(st.length){const t=st.pop();for(let k=0;k<3;k++){const o=H[3*t+k];if(o<0)continue;const u=(o/3)|0;if(!dead[u]&&len[u]>lim){dead[u]=1;st.push(u);}}}
  const keep=[];for(let t=0;t<nt;t++){if(dead[t])dropped++;else keep.push(T[3*t],T[3*t+1],T[3*t+2]);}T=Uint32Array.from(keep);}
 return {X:Float64Array.from(X),Y:Float64Array.from(Y),Z:Float64Array.from(Z),T:T,src:'delaunay',dropped:dropped};
}
function tinGeom(tin,name){const n=tin.X.length,V=new Float64Array(n*3);for(let i=0;i<n;i++){V[3*i]=tin.X[i];V[3*i+1]=tin.Y[i];V[3*i+2]=tin.Z[i];}return GC.mk({name:name,V:V,F:Uint32Array.from(tin.T),src:'tin'});}
function niceCell(tin,target){let x0=Infinity,x1=-Infinity,y0=Infinity,y1=-Infinity;for(let i=0;i<tin.X.length;i++){if(tin.X[i]<x0)x0=tin.X[i];if(tin.X[i]>x1)x1=tin.X[i];if(tin.Y[i]<y0)y0=tin.Y[i];if(tin.Y[i]>y1)y1=tin.Y[i];}
 const raw=Math.max(x1-x0,y1-y0)/(target||1500),nice=[0.1,0.2,0.25,0.5,1,2,2.5,5,10,20,25,50,100];for(const v of nice)if(v>=raw)return v;return Math.ceil(raw/100)*100;}
function tinToDEM(tin,cell){
 const X=tin.X,Y=tin.Y,Z=tin.Z,T=tin.T;let x0=Infinity,x1=-Infinity,y0=Infinity,y1=-Infinity;
 for(let i=0;i<X.length;i++){if(X[i]<x0)x0=X[i];if(X[i]>x1)x1=X[i];if(Y[i]<y0)y0=Y[i];if(Y[i]>y1)y1=Y[i];}
 x0=Math.floor(x0/cell)*cell;y1=Math.ceil(y1/cell)*cell;const nx=Math.max(1,Math.ceil((x1-x0)/cell)),ny=Math.max(1,Math.ceil((y1-y0)/cell));
 if(nx*ny>36e6)throw new Error('Grid terlalu besar ('+nx+' × '+ny+'); perbesar ukuran sel.');
 const z=new Float32Array(nx*ny).fill(NaN);
 for(let t=0;t<T.length;t+=3){const a=T[t],b=T[t+1],c=T[t+2],ax=X[a],ay=Y[a],bx=X[b],by=Y[b],cx=X[c],cy=Y[c],den=(by-cy)*(ax-cx)+(cx-bx)*(ay-cy);if(Math.abs(den)<1e-12)continue;
  const i0=Math.max(0,Math.floor((Math.min(ax,bx,cx)-x0)/cell-0.5)),i1=Math.min(nx-1,Math.ceil((Math.max(ax,bx,cx)-x0)/cell-0.5)),j0=Math.max(0,Math.floor((y1-Math.max(ay,by,cy))/cell-0.5)),j1=Math.min(ny-1,Math.ceil((y1-Math.min(ay,by,cy))/cell-0.5));
  for(let j=j0;j<=j1;j++){const py=y1-(j+0.5)*cell;for(let i=i0;i<=i1;i++){const px=x0+(i+0.5)*cell,w1=((by-cy)*(px-cx)+(cx-bx)*(py-cy))/den,w2=((cy-ay)*(px-cx)+(ax-cx)*(py-cy))/den,w3=1-w1-w2;
   if(w1>=-1e-9&&w2>=-1e-9&&w3>=-1e-9)z[j*nx+i]=w1*Z[a]+w2*Z[b]+w3*Z[c];}}}
 return mkDEM(nx,ny,x0,y1,cell,z);
}
function mkDEM(nx,ny,x0,y1,cell,z,celly){let mn=Infinity,mx=-Infinity,cnt=0;for(let i=0;i<z.length;i++){const v=z[i];if(v===v){cnt++;if(v<mn)mn=v;if(v>mx)mx=v;}}
 return {nx:nx,ny:ny,x0:x0,y1:y1,cell:cell,celly:celly||cell,z:z,min:mn,max:mx,count:cnt};}
function demExt(d){return [d.x0,d.y1-d.ny*d.celly,d.x0+d.nx*d.cell,d.y1];}
function demZ(d,x,y){const fi=(x-d.x0)/d.cell-0.5,fj=(d.y1-y)/d.celly-0.5,i=Math.floor(fi),j=Math.floor(fj);if(i<-1||j<-1||i>=d.nx||j>=d.ny)return NaN;
 const g=(a,b)=>(a<0||b<0||a>=d.nx||b>=d.ny)?NaN:d.z[b*d.nx+a],a=g(i,j),b=g(i+1,j),c=g(i,j+1),e=g(i+1,j+1),tx=fi-i,ty=fj-j;
 if(a===a&&b===b&&c===c&&e===e)return (a*(1-tx)+b*tx)*(1-ty)+(c*(1-tx)+e*tx)*ty;
 const r=g(Math.round(fi),Math.round(fj));return r;}
const RAMP=[[0,[62,122,94]],[0.25,[143,170,104]],[0.5,[222,205,140]],[0.75,[176,128,84]],[1,[244,240,232]]];
function rampCol(t){t=t<0?0:t>1?1:t;for(let k=1;k<RAMP.length;k++)if(t<=RAMP[k][0]){const a=RAMP[k-1],b=RAMP[k],u=(t-a[0])/(b[0]-a[0]);return [a[1][0]+(b[1][0]-a[1][0])*u,a[1][1]+(b[1][1]-a[1][1])*u,a[1][2]+(b[1][2]-a[1][2])*u];}return RAMP[RAMP.length-1][1];}
function demRGBA(d,opt){opt=opt||{};const nx=d.nx,ny=d.ny,z=d.z,out=new Uint8ClampedArray(nx*ny*4),rg=(d.max-d.min)||1,az=315*Math.PI/180,alt=45*Math.PI/180,lx=Math.sin(az)*Math.cos(alt),ly=Math.cos(az)*Math.cos(alt),lz=Math.sin(alt),ex=opt.exag||1.5;
 for(let j=0;j<ny;j++)for(let i=0;i<nx;i++){const k=j*nx+i,v=z[k];if(v!==v)continue;
  const l=i>0&&z[k-1]===z[k-1]?z[k-1]:v,r=i<nx-1&&z[k+1]===z[k+1]?z[k+1]:v,u=j>0&&z[k-nx]===z[k-nx]?z[k-nx]:v,dn=j<ny-1&&z[k+nx]===z[k+nx]?z[k+nx]:v;
  const dzx=(r-l)/(2*d.cell)*ex,dzy=(u-dn)/(2*d.celly)*ex,nl=Math.sqrt(dzx*dzx+dzy*dzy+1),sh=Math.max(0,(-dzx*lx-dzy*ly+lz)/nl),c=opt.mode==='gray'?[200,200,200]:rampCol((v-d.min)/rg),f=opt.mode==='flat'?1:0.35+0.75*sh;
  out[4*k]=c[0]*f;out[4*k+1]=c[1]*f;out[4*k+2]=c[2]*f;out[4*k+3]=255;}
 return out;}
function contours(d,interval,name){
 if(!(interval>0))throw new Error('Interval kontur harus > 0');const nlev=Math.floor(d.max/interval)-Math.ceil(d.min/interval)+1;if(nlev>2000)throw new Error('Terlalu banyak level kontur ('+nlev+'); perbesar interval.');
 const segs=new Map(),nx=d.nx,ny=d.ny,z=d.z,X=(i)=>d.x0+(i+0.5)*d.cell,Y=(j)=>d.y1-(j+0.5)*d.celly;
 const tri=(p,q,r)=>{const lo=Math.min(p[2],q[2],r[2]),hi=Math.max(p[2],q[2],r[2]);if(lo!==lo||hi!==hi)return;
  for(let L=Math.ceil(lo/interval)*interval;L<=hi;L+=interval){if(L===hi&&lo!==hi)continue;const pts=[];
   for(const e of [[p,q],[q,r],[r,p]]){const a=e[0],b=e[1];if((a[2]<=L&&b[2]>L)||(b[2]<=L&&a[2]>L)){const t=(L-a[2])/(b[2]-a[2]);pts.push([a[0]+(b[0]-a[0])*t,a[1]+(b[1]-a[1])*t]);}}
   if(pts.length===2){const key=Math.round(L/interval);let s=segs.get(key);if(!s){s=[];segs.set(key,s);}s.push(pts);}}};
 for(let j=0;j<ny-1;j++)for(let i=0;i<nx-1;i++){const a=[X(i),Y(j),z[j*nx+i]],b=[X(i+1),Y(j),z[j*nx+i+1]],c=[X(i),Y(j+1),z[(j+1)*nx+i]],e=[X(i+1),Y(j+1),z[(j+1)*nx+i+1]];tri(a,b,c);tri(b,e,c);}
 const gb=new GC.GB(name||'Kontur');const kf=(p)=>Math.round(p[0]*1000)+':'+Math.round(p[1]*1000);
 Array.from(segs.keys()).sort((a,b)=>a-b).forEach(key=>{const L=key*interval,S=segs.get(key),ends=new Map(),used=new Uint8Array(S.length);
  S.forEach((s,i)=>{for(const p of s){const k=kf(p);let a=ends.get(k);if(!a){a=[];ends.set(k,a);}a.push(i);}});
  const next=(p,cur)=>{const a=ends.get(kf(p));if(!a)return -1;for(const i of a)if(!used[i]&&i!==cur)return i;return -1;};
  for(let i=0;i<S.length;i++){if(used[i])continue;used[i]=1;const line=[S[i][0],S[i][1]];
   for(const dir of [1,0]){let cur=i;for(;;){const tip=dir?line[line.length-1]:line[0],n=next(tip,cur);if(n<0)break;used[n]=1;cur=n;const s=S[n],o=kf(s[0])===kf(tip)?s[1]:s[0];if(dir)line.push(o);else line.unshift(o);}}
   let closed=false;if(line.length>3&&kf(line[0])===kf(line[line.length-1])){line.pop();closed=true;}
   gb.poly(line.map(p=>gb.add(p[0],p[1],L)),closed,[fx(L,interval<1?2:interval%1?1:0)]);}});
 if(!gb.v.length)throw new Error('Tidak ada kontur pada interval ini.');
 return gb.done('kontur',{cols:['ELEV']});
}

/* ---------- raster grid: GeoTIFF (Float32) & ESRI ASCII ---------- */
function writeTIFF(d,crs){
 const nx=d.nx,ny=d.ny,ND=-9999,ent=[],extra=[];let eoff=0;
 const dbl=(a)=>{const b=new Uint8Array(a.length*8),v=new DataView(b.buffer);a.forEach((x,i)=>v.setFloat64(8*i,x,true));return b;},sh=(a)=>{const b=new Uint8Array(a.length*2),v=new DataView(b.buffer);a.forEach((x,i)=>v.setUint16(2*i,x,true));return b;};
 const nd=enc(String(ND)+'\0'),epsg=crs?(crs.south?32700:32600)+(+crs.zone):0;
 const keys=crs?[1,1,0,3,1024,0,1,1,1025,0,1,1,3072,0,1,epsg]:[1,1,0,2,1024,0,1,1,1025,0,1,1];
 const T=[[256,4,1,nx],[257,4,1,ny],[258,3,1,32],[259,3,1,1],[262,3,1,1],[273,4,1,'DATA'],[277,3,1,1],[278,4,1,ny],[279,4,1,nx*ny*4],[284,3,1,1],[339,3,1,3],
  [33550,12,3,dbl([d.cell,d.celly,0])],[33922,12,6,dbl([0,0,0,d.x0,d.y1,0])],[34735,3,keys.length,sh(keys)],[42113,2,nd.length,nd]];
 const ifd=8,ifdLen=2+12*T.length+4,exStart=ifd+ifdLen;let exLen=0;for(const t of T)if(t[3] instanceof Uint8Array){t.off=exStart+exLen;exLen+=t[3].length+(t[3].length&1);}
 const dataOff=exStart+exLen,out=new Uint8Array(dataOff+nx*ny*4),v=new DataView(out.buffer);
 out[0]=0x49;out[1]=0x49;v.setUint16(2,42,true);v.setUint32(4,ifd,true);v.setUint16(ifd,T.length,true);
 T.forEach((t,i)=>{const p=ifd+2+12*i;v.setUint16(p,t[0],true);v.setUint16(p+2,t[1],true);v.setUint32(p+4,t[2],true);
  if(t[3] instanceof Uint8Array){v.setUint32(p+8,t.off,true);out.set(t[3],t.off);}else if(t[3]==='DATA')v.setUint32(p+8,dataOff,true);else if(t[1]===3)v.setUint16(p+8,t[3],true);else v.setUint32(p+8,t[3],true);});
 for(let i=0;i<nx*ny;i++){const z=d.z[i];v.setFloat32(dataOff+4*i,z===z?z:ND,true);}
 return out;
}
function writeASC(d,dec){if(Math.abs(d.cell-d.celly)>1e-9)throw new Error('ASC memerlukan sel persegi.');const O=['ncols '+d.nx,'nrows '+d.ny,'xllcorner '+fx(d.x0,4),'yllcorner '+fx(d.y1-d.ny*d.celly,4),'cellsize '+d.cell,'NODATA_value -9999'];
 for(let j=0;j<d.ny;j++){const r=new Array(d.nx);for(let i=0;i<d.nx;i++){const z=d.z[j*d.nx+i];r[i]=z===z?fx(z,dec==null?3:dec):'-9999';}O.push(r.join(' '));}return O.join('\n')+'\n';}
function parseASC(base,u){const s=dec(u),L=s.split(/\r?\n/),h={};let i=0;for(;i<L.length;i++){const m=/^\s*([A-Za-z_]+)\s+(\S+)/.exec(L[i]);if(!m)break;h[m[1].toLowerCase()]=+m[2];}
 const nx=h.ncols,ny=h.nrows,cell=h.cellsize;if(!nx||!ny||!cell)throw new Error('Header ASC tidak lengkap');const nd=h.nodata_value===undefined?-9999:h.nodata_value;
 const x0=h.xllcorner!==undefined?h.xllcorner:h.xllcenter-cell/2,y0=h.yllcorner!==undefined?h.yllcorner:h.yllcenter-cell/2,z=new Float32Array(nx*ny);let k=0;
 for(;i<L.length&&k<nx*ny;i++){const p=L[i].trim().split(/\s+/);for(const t of p){if(t===''||k>=nx*ny)continue;const v=+t;z[k++]=v===nd?NaN:v;}}
 const g=GC.mk({name:base,src:'asc'});g.dem=mkDEM(nx,ny,x0,y0+ny*cell,cell,z);return g;}
function xyzOut(d,o){const sep=o.sep||',',O=['X'+sep+'Y'+sep+'Z'];for(let j=0;j<d.ny;j++)for(let i=0;i<d.nx;i++){const z=d.z[j*d.nx+i];if(z===z)O.push(fx(d.x0+(i+0.5)*d.cell,2)+sep+fx(d.y1-(j+0.5)*d.celly,2)+sep+fx(z,o.dec));}return O.join('\n')+'\n';}
const demOnly=(gs,f)=>{const L=gs.filter(g=>g.dem);if(!L.length)throw new Error(f+' hanya untuk lapisan DEM. Buat dulu lewat Analisis → Buat DEM dari topografi.');return L;};
GC.WRITERS.tif=(gs,o,W)=>demOnly(gs,'GeoTIFF').map(g=>({name:(gs.length>1?GC.safeName(g.name,60):o.base)+'.tif',data:writeTIFF(g.dem,o.utm)}));
GC.WRITERS.asc=(gs,o,W)=>demOnly(gs,'ASC').map(g=>({name:(gs.length>1?GC.safeName(g.name,60):o.base)+'.asc',data:writeASC(g.dem,o.dec)}));
GC.WRITERS.xyz=(gs,o,W)=>demOnly(gs,'XYZ grid').map(g=>({name:(gs.length>1?GC.safeName(g.name,60):o.base)+'_grid.csv',data:xyzOut(g.dem,o)}));
function worldFile(txt){const a=txt.trim().split(/\s+/).map(Number);if(a.length<6||a.some(v=>!isFinite(v)))throw new Error('World file tidak valid');if(Math.abs(a[1])>1e-9||Math.abs(a[2])>1e-9)throw new Error('World file berotasi belum didukung');return {px:a[0],py:-a[3],x0:a[4]-a[0]/2,y1:a[5]-a[3]/2};}

/* ---------- PDF satu halaman berisi gambar JPEG ---------- */
function pdfFromJpeg(jpg,wpx,hpx,wmm,hmm){
 const W=wmm/25.4*72,H=hmm/25.4*72,parts=[],offs=[];let len=0;const push=(x)=>{const b=typeof x==='string'?enc(x):x;parts.push(b);len+=b.length;};
 const obj=(n,body)=>{offs[n]=len;push(n+' 0 obj\n');push(body);push('\nendobj\n');};
 push('%PDF-1.4\n%\xE2\xE3\xCF\xD3\n');
 obj(1,'<< /Type /Catalog /Pages 2 0 R >>');obj(2,'<< /Type /Pages /Kids [3 0 R] /Count 1 >>');
 obj(3,'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 '+W.toFixed(2)+' '+H.toFixed(2)+'] /Resources << /XObject << /Im0 4 0 R >> >> /Contents 5 0 R >>');
 offs[4]=len;push('4 0 obj\n<< /Type /XObject /Subtype /Image /Width '+wpx+' /Height '+hpx+' /ColorSpace /DeviceRGB /BitsPerComponent 8 /Filter /DCTDecode /Length '+jpg.length+' >>\nstream\n');push(jpg);push('\nendstream\nendobj\n');
 const c='q '+W.toFixed(2)+' 0 0 '+H.toFixed(2)+' 0 0 cm /Im0 Do Q';obj(5,'<< /Length '+c.length+' >>\nstream\n'+c+'\nendstream');
 const xr=len;let x='xref\n0 6\n0000000000 65535 f \n';for(let i=1;i<=5;i++)x+=String(offs[i]).padStart(10,'0')+' 00000 n \n';push(x+'trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n'+xr+'\n%%EOF\n');
 const out=new Uint8Array(len);let p=0;for(const b of parts){out.set(b,p);p+=b.length;}return out;
}

/* ---------- daftar format ---------- */
GC.FORMATS.push(
 {id:'kml',label:'Google Earth KML (.kml)',ext:'kml',soft:'Google Earth · Global Mapper',r:1,w:1,note:'Lintang/bujur WGS84; poligon, garis, titik + atribut'},
 {id:'kmz',label:'Google Earth KMZ (.kmz)',ext:'kmz',soft:'Google Earth · Global Mapper',r:1,w:1,note:'KML terkemas ZIP'},
 {id:'geojson',label:'GeoJSON (.geojson)',ext:'geojson',soft:'QGIS · Global Mapper · web',r:1,w:1,note:'Lintang/bujur WGS84 + atribut'},
 {id:'tif',label:'GeoTIFF DEM (.tif)',ext:'tif',soft:'Global Mapper · Surpac · QGIS',r:1,w:1,dem:1,note:'Grid elevasi Float32 + georeferensi UTM (hanya lapisan DEM)'},
 {id:'asc',label:'ESRI ASCII Grid (.asc)',ext:'asc',soft:'Global Mapper · QGIS',r:1,w:1,dem:1,note:'Grid elevasi teks (hanya lapisan DEM)'},
 {id:'xyz',label:'Grid XYZ (.csv)',ext:'csv',soft:'Semua',r:0,w:1,dem:1,note:'Titik tengah sel DEM sebagai X,Y,Z'});
GC.SOFT['Global Mapper']=['shp','dxf','kml','geojson','tif','csv'];GC.SOFT['Google Earth']=['kml','kmz'];GC.SOFT['Surpac']=['dtm','str','dxf','csv'];
const parse0=GC.parse;
GC.parse=function(name,buf,aux){const ext=((name.match(/\.([^.]+)$/)||[,''])[1]).toLowerCase(),base=name.replace(/\.[^.]+$/,''),W=[];
 if(ext==='kml')return {geoms:parseKML(base,u8of(buf),W),warn:W};
 if(ext==='geojson'||ext==='json')return {geoms:parseGeoJSON(base,u8of(buf),W),warn:W};
 if(ext==='asc'||ext==='grd'&&/^\s*ncols/i.test(dec(u8of(buf).subarray(0,20))))return {geoms:[parseASC(base,u8of(buf))],warn:W};
 return parse0(name,buf,aux);};
Object.assign(GC,{ll2utm:ll2utm,utm2ll:utm2ll,looksGeo:looksGeo,projectGeom:projectGeom,crsName:crsName,polyArea:polyArea,polyLen:polyLen,setGeom:setGeom,bake:bake,addPoly:addPoly,addPoint:addPoint,snapshot:snapshot,restore:restore,
 buildTIN:buildTIN,tinGeom:tinGeom,niceCell:niceCell,tinToDEM:tinToDEM,mkDEM:mkDEM,demExt:demExt,demZ:demZ,demRGBA:demRGBA,contours:contours,writeTIFF:writeTIFF,writeASC:writeASC,worldFile:worldFile,pdfFromJpeg:pdfFromJpeg,parseKML:parseKML,xmlEsc:xmlEsc});
})(typeof GC!=='undefined'?GC:require('./core.js'));
