/* ================= Drillhole 0.24.98: grid permukaan desain pit / topografi untuk filter import .mdl =================
   SALINAN SA.surfGrid / surfAt / gridFill / hull2d / rasterPoly dari web-src/gcex_base.html (Block Model 0.24.81-0.24.83),
   supaya aturan "Hanya di dalam desain pit" / "Hanya di bawah topografi asbuilt" sama persis dengan Block Model:
   pit  : blok disimpan bila permukaan pit di titik tengah (E,N) lebih rendah dari ATAP blok, di dalam batas crest;
   topo : blok disimpan bila DASAR blok di bawah topografi (di luar cakupan topografi = tetap disimpan).
   Bila salah satu diubah, ubah juga yang lain. */
(function(){if(SA.surfGrid)return;
SA.surfGrid=function(lines,mode){var segs=[],cur=[];(lines||[]).forEach(function(p){if(p===null||p===undefined){if(cur.length)segs.push(cur);cur=[];}else if(isFinite(p[0])&&isFinite(p[1])&&isFinite(p[2]))cur.push(p);});if(cur.length)segs.push(cur);
  if(!segs.length)return null;var x0=1e18,x1=-1e18,y0=1e18,y1=-1e18,np=0;segs.forEach(function(P){P.forEach(function(p){np++;if(p[0]<x0)x0=p[0];if(p[0]>x1)x1=p[0];if(p[1]<y0)y0=p[1];if(p[1]>y1)y1=p[1];});});
  var W=x1-x0,Hh=y1-y0,c=Math.max(0.5,Math.sqrt(Math.max(1,W*Hh)/4e6));c=c<=1?(c<=0.5?0.5:1):Math.ceil(c);
  x0-=c;y0-=c;var nx=Math.ceil((W+2*c)/c)+1,ny=Math.ceil((Hh+2*c)/c)+1,NN=nx*ny,S=new Float64Array(NN),K=new Float32Array(NN);
  var put=function(x,y,z){var i=Math.floor((x-x0)/c),j=Math.floor((y-y0)/c);if(i<0||j<0||i>=nx||j>=ny)return;var q=j*nx+i;S[q]+=z;K[q]++;};
  segs.forEach(function(P){if(P.length===1){put(P[0][0],P[0][1],P[0][2]);return;}for(var k=0;k+1<P.length;k++){var a=P[k],b=P[k+1],d=Math.hypot(b[0]-a[0],b[1]-a[1]),m=Math.max(1,Math.ceil(d/(c*0.5)));
    for(var t=0;t<=m;t++){var f=t/m;put(a[0]+(b[0]-a[0])*f,a[1]+(b[1]-a[1])*f,a[2]+(b[2]-a[2])*f);}}});
  var Z=new Float32Array(NN),KN=new Uint8Array(NN);for(var q=0;q<NN;q++){if(K[q]){Z[q]=S[q]/K[q];KN[q]=1;}}S=K=null;
  SA.gridFill(Z,KN,nx,ny);
  /* 0.24.60 (pemilik 10-11-2026): Z sel = TRIANGULASI vertex string (seperti DTM Surpac, web-src/tinz.js); rata-rata per sel + isian piramida di atas hanya cadangan di luar segitiga */
  if(window.TINZ){var TPv=[];segs.forEach(function(P){P.forEach(function(p){TPv.push({x:p[0],y:p[1],z:p[2]});});});var SP=null;if(window.TIN&&TIN.soup){var s_x=[],s_y=[],s_z=[];segs.forEach(function(P){P.forEach(function(p){s_x.push(p[0]);s_y.push(p[1]);s_z.push(p[2]);});s_x.push(null);s_y.push(null);s_z.push(null);});SP=TIN.soup({x:s_x,y:s_y,z:s_z});}/* 0.24.83: DXF 3DFACE = segitiga DTM asli */
    var TN=SP?TINZ(null,{tri:SP}):TINZ(TPv,{faktor:(window.TIN&&TIN.faktor)||8});if(TN){for(var jy=0;jy<ny;jy++)for(var ix2=0;ix2<nx;ix2++){var zv=TN.f(x0+(ix2+0.5)*c,y0+(jy+0.5)*c);if(zv!=null&&isFinite(zv))Z[jy*nx+ix2]=zv;}}}
  /* mask cakupan */
  var M=new Uint8Array(NN),polys=[];
  if(mode==='crest'){segs.forEach(function(P){if(P.length<4)return;var a=P[0],b=P[P.length-1];if(Math.hypot(a[0]-b[0],a[1]-b[1])<=Math.max(2*c,1.5))polys.push(P);});}
  if(!polys.length){var pts=[];segs.forEach(function(P){P.forEach(function(p){pts.push([p[0],p[1]]);});});polys=[SA.hull2d(pts)];}
  polys.forEach(function(P){SA.rasterPoly(P,M,x0,y0,c,nx,ny);});
  var nin=0;for(q=0;q<NN;q++){if(!M[q])Z[q]=NaN;else nin++;}
  return{x0:x0,y0:y0,c:c,nx:nx,ny:ny,z:Z,mode:mode,area:nin*c*c,nPoly:polys.length,np:np};};
SA.surfAt=function(g,x,y){var i=Math.floor((x-g.x0)/g.c),j=Math.floor((y-g.y0)/g.c);if(i<0||j<0||i>=g.nx||j>=g.ny)return NaN;return g.z[j*g.nx+i];};
/* isi sel kosong: piramida (rata-rata ke kasar, interpolasi bilinear ke halus, lalu penghalusan Jacobi) */
SA.gridFill=function(Z,KN,nx,ny){var any=0,all=1;for(var q=0;q<Z.length;q++){if(KN[q])any=1;else all=0;}if(all||!any)return;
  if(nx<=2&&ny<=2){var s=0,k=0;for(q=0;q<Z.length;q++)if(KN[q]){s+=Z[q];k++;}for(q=0;q<Z.length;q++)if(!KN[q])Z[q]=s/k;return;}
  var cx=Math.ceil(nx/2),cy=Math.ceil(ny/2),CZ=new Float32Array(cx*cy),CS=new Float32Array(cx*cy),CK=new Uint8Array(cx*cy),i,j;
  for(j=0;j<ny;j++)for(i=0;i<nx;i++){var p=j*nx+i;if(KN[p]){var cp=(j>>1)*cx+(i>>1);CZ[cp]+=Z[p];CS[cp]++;}}
  for(q=0;q<CZ.length;q++)if(CS[q]){CZ[q]/=CS[q];CK[q]=1;}
  SA.gridFill(CZ,CK,cx,cy);
  for(j=0;j<ny;j++){var fy=Math.min(cy-1,Math.max(0,(j+0.5)/2-0.5)),j0=Math.floor(fy),j1=Math.min(cy-1,j0+1),ty=fy-j0;
    for(i=0;i<nx;i++){p=j*nx+i;if(KN[p])continue;var fx=Math.min(cx-1,Math.max(0,(i+0.5)/2-0.5)),i0=Math.floor(fx),i1=Math.min(cx-1,i0+1),tx=fx-i0;
      Z[p]=(CZ[j0*cx+i0]*(1-tx)+CZ[j0*cx+i1]*tx)*(1-ty)+(CZ[j1*cx+i0]*(1-tx)+CZ[j1*cx+i1]*tx)*ty;}}
  for(var it=0;it<3;it++)for(j=0;j<ny;j++)for(i=0;i<nx;i++){p=j*nx+i;if(KN[p])continue;var s2=0,k2=0;if(i>0){s2+=Z[p-1];k2++;}if(i<nx-1){s2+=Z[p+1];k2++;}if(j>0){s2+=Z[p-nx];k2++;}if(j<ny-1){s2+=Z[p+nx];k2++;}Z[p]=s2/k2;}};
SA.hull2d=function(P){P=P.slice().sort(function(a,b){return a[0]-b[0]||a[1]-b[1];});var cr=function(o,a,b){return(a[0]-o[0])*(b[1]-o[1])-(a[1]-o[1])*(b[0]-o[0]);},lo=[],up=[],i;
  for(i=0;i<P.length;i++){while(lo.length>=2&&cr(lo[lo.length-2],lo[lo.length-1],P[i])<=0)lo.pop();lo.push(P[i]);}
  for(i=P.length-1;i>=0;i--){while(up.length>=2&&cr(up[up.length-2],up[up.length-1],P[i])<=0)up.pop();up.push(P[i]);}
  up.pop();lo.pop();return lo.concat(up);};
SA.rasterPoly=function(P,M,x0,y0,c,nx,ny){var n=P.length;if(n<3)return;for(var j=0;j<ny;j++){var yc=y0+(j+0.5)*c,xs=[];
    for(var k=0;k<n;k++){var a=P[k],b=P[(k+1)%n];if((a[1]>yc)!==(b[1]>yc))xs.push(a[0]+(yc-a[1])/(b[1]-a[1])*(b[0]-a[0]));}
    if(xs.length<2)continue;xs.sort(function(a,b){return a-b;});
    for(var q=0;q+1<xs.length;q+=2){var i0=Math.max(0,Math.ceil((xs[q]-x0)/c-0.5)),i1=Math.min(nx-1,Math.floor((xs[q+1]-x0)/c-0.5));for(var i=i0;i<=i1;i++)M[j*nx+i]=1;}}};
})();
