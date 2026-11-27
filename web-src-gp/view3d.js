'use strict';
/* Geo Pocket — pratinjau 3D WebGL (Z ke atas, koordinat dikurangi titik asal agar presisi UTM aman) */
const V3=(function(){
let cv,gl,gz,gzc,prog,L={},items=[],origin=[0,0,0],dirty=true,W=1,H=1,dpr=1,sel=-1,mode='solid',ortho=false,raf=0;
const cam={yaw:-0.8,pitch:0.55,dist:100,t:[0,0,0]},FOV=Math.PI/4;
const VS='attribute vec3 aPos;attribute vec3 aNor;uniform mat4 uMVP;uniform vec3 uLight;uniform float uPt;varying float vL;void main(){gl_Position=uMVP*vec4(aPos,1.0);vL=abs(dot(aNor,uLight));gl_PointSize=uPt;}';
const FS='precision mediump float;uniform vec4 uCol;uniform float uFlat;uniform float uRound;varying float vL;void main(){if(uRound>0.5){vec2 c=gl_PointCoord-0.5;if(dot(c,c)>0.25)discard;}float l=mix(0.32+0.68*vL,1.0,uFlat);gl_FragColor=vec4(uCol.rgb*l,uCol.a);}';
function sh(t,s){const o=gl.createShader(t);gl.shaderSource(o,s);gl.compileShader(o);if(!gl.getShaderParameter(o,gl.COMPILE_STATUS))throw new Error(gl.getShaderInfoLog(o));return o;}
function init(canvas,gizmo){
 cv=canvas;gl=cv.getContext('webgl',{antialias:true,alpha:true,premultipliedAlpha:false,preserveDrawingBuffer:true})||cv.getContext('experimental-webgl');
 gz=gizmo;gzc=gz.getContext('2d');
 if(!gl){return false;}
 prog=gl.createProgram();gl.attachShader(prog,sh(gl.VERTEX_SHADER,VS));gl.attachShader(prog,sh(gl.FRAGMENT_SHADER,FS));gl.linkProgram(prog);
 if(!gl.getProgramParameter(prog,gl.LINK_STATUS))throw new Error(gl.getProgramInfoLog(prog));
 gl.useProgram(prog);for(const n of ['aPos','aNor'])L[n]=gl.getAttribLocation(prog,n);for(const n of ['uMVP','uLight','uPt','uCol','uFlat','uRound'])L[n]=gl.getUniformLocation(prog,n);
 let drag=null;
 cv.addEventListener('contextmenu',e=>e.preventDefault());
 cv.addEventListener('pointerdown',e=>{cv.setPointerCapture(e.pointerId);drag={x:e.clientX,y:e.clientY,pan:e.button===2||e.shiftKey||e.button===1};});
 cv.addEventListener('pointermove',e=>{if(!drag)return;const dx=e.clientX-drag.x,dy=e.clientY-drag.y;drag.x=e.clientX;drag.y=e.clientY;
  if(drag.pan){const s=2*cam.dist*Math.tan(FOV/2)/H,b=basis();for(let k=0;k<3;k++)cam.t[k]+=(-b.r[k]*dx+b.u[k]*dy)*s;}
  else{cam.yaw-=dx*0.008;cam.pitch=Math.max(-1.5533,Math.min(1.5533,cam.pitch+dy*0.008));}draw();});
 cv.addEventListener('pointerup',e=>{drag=null;});
 cv.addEventListener('wheel',e=>{e.preventDefault();cam.dist*=Math.exp(e.deltaY*0.0012);draw();},{passive:false});
 cv.addEventListener('dblclick',()=>fit());
 return true;
}
function basis(){const cp=Math.cos(cam.pitch),f=[-cp*Math.cos(cam.yaw),-cp*Math.sin(cam.yaw),-Math.sin(cam.pitch)];
 let r=[f[1]*1-f[2]*0,f[2]*0-f[0]*1,0];const l=Math.hypot(r[0],r[1])||1;r=[r[0]/l,r[1]/l,0];
 const u=[r[1]*f[2]-r[2]*f[1],r[2]*f[0]-r[0]*f[2],r[0]*f[1]-r[1]*f[0]];return {f:f,r:r,u:u};}
function persp(a,n,f){const t=1/Math.tan(FOV/2),m=new Float32Array(16);m[0]=t/a;m[5]=t;m[10]=(f+n)/(n-f);m[11]=-1;m[14]=2*f*n/(n-f);return m;}
function orth(hw,hh,n,f){const m=new Float32Array(16);m[0]=1/hw;m[5]=1/hh;m[10]=-2/(f-n);m[14]=-(f+n)/(f-n);m[15]=1;return m;}
function lookAt(e,c){let z=[e[0]-c[0],e[1]-c[1],e[2]-c[2]];let l=Math.hypot(...z);z=z.map(v=>v/l);let x=[z[1],-z[0],0];l=Math.hypot(x[0],x[1])||1;x=[x[0]/l,x[1]/l,0];
 const y=[z[1]*x[2]-z[2]*x[1],z[2]*x[0]-z[0]*x[2],z[0]*x[1]-z[1]*x[0]];
 return new Float32Array([x[0],y[0],z[0],0,x[1],y[1],z[1],0,x[2],y[2],z[2],0,-(x[0]*e[0]+x[1]*e[1]+x[2]*e[2]),-(y[0]*e[0]+y[1]*e[1]+y[2]*e[2]),-(z[0]*e[0]+z[1]*e[1]+z[2]*e[2]),1]);}
function mul(a,b){const o=new Float32Array(16);for(let i=0;i<4;i++)for(let j=0;j<4;j++){let s=0;for(let k=0;k<4;k++)s+=a[k*4+j]*b[i*4+k];o[i*4+j]=s;}return o;}
function buf(data){const b=gl.createBuffer();gl.bindBuffer(gl.ARRAY_BUFFER,b);gl.bufferData(gl.ARRAY_BUFFER,data,gl.STATIC_DRAW);return {b:b,n:data.length/3};}
function freeAll(){for(const it of items)for(const k of ['tri','nor','edge','line','pt','vtx'])if(it[k])gl.deleteBuffer(it[k].b);items=[];}
function rebuild(geoms){
 if(!gl)return;freeAll();
 const mn=[Infinity,Infinity,Infinity],mx=[-Infinity,-Infinity,-Infinity];
 for(const g of geoms)for(let i=0;i<g.V.length;i+=3)for(let k=0;k<3;k++){const v=g.V[i+k];if(v<mn[k])mn[k]=v;if(v>mx[k])mx[k]=v;}
 origin=isFinite(mn[0])?[(mn[0]+mx[0])/2,(mn[1]+mx[1])/2,(mn[2]+mx[2])/2]:[0,0,0];
 for(const g of geoms){const V=g.V,o=origin,it={g:g};
  const P=(i,k)=>V[3*i+k]-o[k];
  if(g.F.length){const nt=g.F.length/3,pos=new Float32Array(nt*9),nor=new Float32Array(nt*9);
   for(let t=0;t<nt;t++){const a=g.F[3*t],b=g.F[3*t+1],c=g.F[3*t+2];const ax=P(a,0),ay=P(a,1),az=P(a,2),bx=P(b,0),by=P(b,1),bz=P(b,2),cx=P(c,0),cy=P(c,1),cz=P(c,2);
    const ux=bx-ax,uy=by-ay,uz=bz-az,wx=cx-ax,wy=cy-ay,wz=cz-az;let nx=uy*wz-uz*wy,ny=uz*wx-ux*wz,nz=ux*wy-uy*wx;const l=Math.hypot(nx,ny,nz)||1;nx/=l;ny/=l;nz/=l;
    pos.set([ax,ay,az,bx,by,bz,cx,cy,cz],t*9);nor.set([nx,ny,nz,nx,ny,nz,nx,ny,nz],t*9);}
   it.tri=buf(pos);it.nor=buf(nor);
   if(nt<=250000){const e=new Float32Array(nt*18);for(let t=0;t<nt;t++){const id=[g.F[3*t],g.F[3*t+1],g.F[3*t+2]];for(let k=0;k<3;k++){const a=id[k],b=id[(k+1)%3];e.set([P(a,0),P(a,1),P(a,2),P(b,0),P(b,1),P(b,2)],t*18+k*6);}}it.edge=buf(e);}}
  if(g.P.length){let n=0;for(const p of g.P)n+=(p.idx.length-1+(p.closed?1:0));const l=new Float32Array(n*6);let q=0;
   for(const p of g.P){const m=p.idx.length;for(let k=0;k<m-1+(p.closed?1:0);k++){const a=p.idx[k],b=p.idx[(k+1)%m];l.set([P(a,0),P(a,1),P(a,2),P(b,0),P(b,1),P(b,2)],q);q+=6;}}it.line=buf(l);}
  if(g.PT.length){const p=new Float32Array(g.PT.length*3);for(let k=0;k<g.PT.length;k++){const i=g.PT[k];p.set([P(i,0),P(i,1),P(i,2)],k*3);}it.pt=buf(p);}
  if(V.length){const p=new Float32Array(V.length);for(let i=0;i<V.length/3;i++)p.set([P(i,0),P(i,1),P(i,2)],i*3);it.vtx=buf(p);}
  items.push(it);}
 draw();
}
function hex(c){const n=parseInt(c.slice(1),16);return [(n>>16)/255,((n>>8)&255)/255,(n&255)/255];}
function fit(){
 const mn=[Infinity,Infinity,Infinity],mx=[-Infinity,-Infinity,-Infinity];let any=false;
 for(const it of items){if(!it.g.visible)continue;const V=it.g.V;for(let i=0;i<V.length;i+=3)for(let k=0;k<3;k++){const v=V[i+k]-origin[k];any=true;if(v<mn[k])mn[k]=v;if(v>mx[k])mx[k]=v;}}
 if(!any){cam.t=[0,0,0];cam.dist=100;draw();return;}
 cam.t=[(mn[0]+mx[0])/2,(mn[1]+mx[1])/2,(mn[2]+mx[2])/2];const r=Math.hypot(mx[0]-mn[0],mx[1]-mn[1],mx[2]-mn[2])/2||1;cam.dist=r/Math.sin(FOV/2)*1.05;cam.r=r;draw();
}
function preset(n){const P={top:[-Math.PI/2,1.5533],front:[-Math.PI/2,0],side:[0,0],iso:[-0.8,0.55]}[n];cam.yaw=P[0];cam.pitch=P[1];draw();}
function resize(){if(!cv)return;const r=cv.parentNode.getBoundingClientRect();dpr=window.devicePixelRatio||1;W=Math.max(1,r.width);H=Math.max(1,r.height);cv.width=Math.round(W*dpr);cv.height=Math.round(H*dpr);cv.style.width=W+'px';cv.style.height=H+'px';draw();}
function draw(){if(raf)return;raf=requestAnimationFrame(()=>{raf=0;render();});}
function render(){
 if(!gl||!W)return;gl.viewport(0,0,cv.width,cv.height);gl.clearColor(0,0,0,0);gl.clear(gl.COLOR_BUFFER_BIT|gl.DEPTH_BUFFER_BIT);gl.enable(gl.DEPTH_TEST);gl.useProgram(prog);
 const b=basis(),e=[cam.t[0]-b.f[0]*cam.dist,cam.t[1]-b.f[1]*cam.dist,cam.t[2]-b.f[2]*cam.dist],R=cam.r||cam.dist;
 const view=lookAt(e,cam.t),asp=W/H;let proj;
 if(ortho){const hh=cam.dist*Math.tan(FOV/2);proj=orth(hh*asp,hh,cam.dist-R*6,cam.dist+R*6);}else proj=persp(asp,Math.max(cam.dist*0.005,0.01),cam.dist*400+R*10);
 gl.uniformMatrix4fv(L.uMVP,false,mul(proj,view));
 let lg=[-b.f[0]+b.u[0]*0.5+b.r[0]*0.3,-b.f[1]+b.u[1]*0.5+b.r[1]*0.3,-b.f[2]+b.u[2]*0.5+b.r[2]*0.3];const ll=Math.hypot(...lg);gl.uniform3f(L.uLight,lg[0]/ll,lg[1]/ll,lg[2]/ll);
 const attr=(bf,loc)=>{gl.bindBuffer(gl.ARRAY_BUFFER,bf.b);gl.enableVertexAttribArray(loc);gl.vertexAttribPointer(loc,3,gl.FLOAT,false,0,0);};
 const flatNor=()=>{gl.disableVertexAttribArray(L.aNor);gl.vertexAttrib3f(L.aNor,0,0,1);};
 gl.enable(gl.POLYGON_OFFSET_FILL);gl.polygonOffset(1,1);
 for(const it of items){const g=it.g;if(!g.visible)continue;const c=hex(g.color),op=g.opacity==null?1:g.opacity;
  const solid=(mode==='solid'||mode==='solidwire');
  if(it.tri&&solid){gl.uniform4f(L.uCol,c[0],c[1],c[2],op);gl.uniform1f(L.uFlat,0);gl.uniform1f(L.uRound,0);attr(it.tri,L.aPos);attr(it.nor,L.aNor);
   if(op<1){gl.enable(gl.BLEND);gl.blendFunc(gl.SRC_ALPHA,gl.ONE_MINUS_SRC_ALPHA);gl.depthMask(false);}gl.drawArrays(gl.TRIANGLES,0,it.tri.n);if(op<1){gl.disable(gl.BLEND);gl.depthMask(true);}}
  gl.disable(gl.POLYGON_OFFSET_FILL);
  const wire=(mode==='solidwire'||mode==='wire'||g.id===sel);
  if(it.edge&&wire){const k=mode==='wire'?c:[c[0]*0.35,c[1]*0.35,c[2]*0.35];gl.uniform4f(L.uCol,k[0],k[1],k[2],mode==='solidwire'||mode==='wire'?0.9:0.55);gl.uniform1f(L.uFlat,1);flatNor();attr(it.edge,L.aPos);
   gl.enable(gl.BLEND);gl.blendFunc(gl.SRC_ALPHA,gl.ONE_MINUS_SRC_ALPHA);gl.drawArrays(gl.LINES,0,it.edge.n);gl.disable(gl.BLEND);}
  if(it.line){gl.uniform4f(L.uCol,c[0],c[1],c[2],1);gl.uniform1f(L.uFlat,1);flatNor();attr(it.line,L.aPos);gl.drawArrays(gl.LINES,0,it.line.n);}
  const pts=(mode==='points'&&it.vtx)?it.vtx:it.pt;
  if(pts){gl.uniform4f(L.uCol,c[0],c[1],c[2],1);gl.uniform1f(L.uFlat,1);gl.uniform1f(L.uRound,1);gl.uniform1f(L.uPt,Math.max(3,Math.round(4*dpr)));flatNor();attr(pts,L.aPos);gl.drawArrays(gl.POINTS,0,pts.n);gl.uniform1f(L.uRound,0);}
  gl.enable(gl.POLYGON_OFFSET_FILL);}
 gl.disable(gl.POLYGON_OFFSET_FILL);
 gizmo(b);
}
function gizmo(b){
 const s=gz.width=gz.height=Math.round(76*dpr);gz.style.width=gz.style.height='76px';gzc.clearRect(0,0,s,s);gzc.scale(dpr,dpr);
 const cx=38,cy=38,len=26;const ax=[[1,0,0,'X','#C2413B'],[0,1,0,'Y','#2E8B57'],[0,0,1,'Z','#2B5F9E']];
 const pr=ax.map(a=>({x:a[0]*b.r[0]+a[1]*b.r[1]+a[2]*b.r[2],y:a[0]*b.u[0]+a[1]*b.u[1]+a[2]*b.u[2],d:a[0]*b.f[0]+a[1]*b.f[1]+a[2]*b.f[2],n:a[3],c:a[4]})).sort((p,q)=>q.d-p.d);
 gzc.lineWidth=2;gzc.font='600 10px Segoe UI,system-ui,sans-serif';gzc.textAlign='center';gzc.textBaseline='middle';
 for(const p of pr){gzc.strokeStyle=p.c;gzc.fillStyle=p.c;gzc.beginPath();gzc.moveTo(cx,cy);gzc.lineTo(cx+p.x*len,cy-p.y*len);gzc.stroke();gzc.fillText(p.n,cx+p.x*(len+8),cy-p.y*(len+8));}
 gzc.setTransform(1,0,0,1,0,0);
}
return {init:init,rebuild:rebuild,fit:fit,preset:preset,resize:resize,draw:draw,
 setMode:(m)=>{mode=m;draw();},getMode:()=>mode,setOrtho:(o)=>{ortho=!!o;draw();},getOrtho:()=>ortho,setSel:(id)=>{sel=id;draw();},
 info:()=>({dist:cam.dist}),ok:()=>!!gl,png:()=>cv.toDataURL('image/png')};
})();
