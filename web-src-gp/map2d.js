'use strict';
/* Geo Pocket — peta 2D (kanvas), alat info / ukur / digitasi / edit vertex */
const M2=(function(){
let cv,cx,H={},W=1,Ht=1,dpr=1,raf=0;
const view={cx:0,cy:0,s:1},st={tool:'pan',draft:[],meas:[],measDone:false,cur:null,snap:null,hov:null,drag:null,grid:true,labels:true};
const hex=(c,a)=>{const n=parseInt(c.slice(1),16);return 'rgba('+(n>>16)+','+((n>>8)&255)+','+(n&255)+','+a+')';};
const sty=(g)=>g.style||(g.style={lw:1.5,fill:0.18,pt:4,label:-1,colorBy:-1});
function ext(g){if(g.ras)return g.ras.ext;if(g.dem)return GC.demExt(g.dem);if(g._bbV!==g.V){const b=GC.bbox(g);g._bb=b?[b.min[0],b.min[1],b.max[0],b.max[1]]:null;g._bbV=g.V;}return g._bb;}
function nice(v){const p=Math.pow(10,Math.floor(Math.log10(v))),m=v/p;return (m<=1?1:m<=2?2:m<=5?5:10)*p;}
function rampCss(t){t=t<0?0:t>1?1:t;const h=(1-t)*240;return 'hsl('+h.toFixed(0)+',85%,45%)';}
function colorBy(g){const s=sty(g);if(s.colorBy<0||!g.PA.length)return null;const key=s.colorBy+':'+g.PA.length;if(g._cb&&g._cb.key===key)return g._cb;
 let mn=Infinity,mx=-Infinity;const v=new Float64Array(g.PA.length);for(let k=0;k<g.PA.length;k++){const x=g.PA[k]?parseFloat(g.PA[k][s.colorBy]):NaN;v[k]=x;if(x===x){if(x<mn)mn=x;if(x>mx)mx=x;}}
 const sv=Array.from(v).filter(x=>x===x).sort((p,q)=>p-q);if(sv.length>20){const lo=sv[Math.floor(sv.length*0.02)],hi=sv[Math.floor(sv.length*0.98)];if(hi>lo){mn=lo;mx=hi;}}
 return (g._cb={key:key,v:v,min:mn,max:mx});}

/* simbol pemetaan: strike/dip (T), grab (kotak), observasi (segitiga) */
function sym(c,g,s,k,x,y,r,px,op){const a=g.PA[k]||[],cols=g.meta.cols||[];
 if(s.sym==='sd'){const st=parseFloat(a[cols.indexOf('STRIKE')]),dp=a[cols.indexOf('DIP')];if(st!==st){c.beginPath();c.arc(x,y,r,0,6.2832);c.fill();return;}
  const t=st*Math.PI/180,L=r*2.6,ux=Math.sin(t),uy=-Math.cos(t),dx=Math.sin(t+Math.PI/2),dy=-Math.cos(t+Math.PI/2);c.save();const col=c.fillStyle;c.lineCap='butt';const path=()=>{c.beginPath();c.moveTo(x-ux*L,y-uy*L);c.lineTo(x+ux*L,y+uy*L);c.moveTo(x,y);c.lineTo(x+dx*L*0.5,y+dy*L*0.5);};
  path();c.strokeStyle='rgba(255,255,255,.85)';c.lineWidth=4.5*px;c.stroke();path();c.strokeStyle=col;c.lineWidth=2.2*px;c.stroke();c.fillStyle=col;
  if(dp!==''&&dp!=null&&!(s.label>=0)){c.font='600 '+(10.5*px)+'px "Segoe UI",system-ui,sans-serif';c.textAlign='center';c.textBaseline='middle';c.lineWidth=3*px;c.strokeStyle='rgba(255,255,255,.9)';const tx=x+dx*L*0.95,ty=y+dy*L*0.95;c.strokeText(dp,tx,ty);c.fillText(dp,tx,ty);}c.restore();return;}
 c.beginPath();if(s.sym==='sq')c.rect(x-r,y-r,2*r,2*r);else{c.moveTo(x,y-r*1.25);c.lineTo(x+r*1.1,y+r*0.75);c.lineTo(x-r*1.1,y+r*0.75);c.closePath();}c.fill();c.stroke();}
/* ---------- gambar lapisan (dipakai peta dan layout) ---------- */
function drawLayers(c,tf,o){
 o=o||{};const px=o.px||1,X=(x)=>(x-tf.cx)*tf.s+tf.W/2,Y=(y)=>tf.H/2-(y-tf.cy)*tf.s;
 const vx0=tf.cx-tf.W/2/tf.s,vx1=tf.cx+tf.W/2/tf.s,vy0=tf.cy-tf.H/2/tf.s,vy1=tf.cy+tf.H/2/tf.s,L=o.layers||H.layers();
 for(let li=L.length-1;li>=0;li--){const g=L[li];if(!g.visible)continue;const e=ext(g);if(!e||e[2]<vx0||e[0]>vx1||e[3]<vy0||e[1]>vy1)continue;const op=g.opacity==null?1:g.opacity,s=sty(g);
  if(g.ras||g.dem){const im=g.ras?g.ras.cv:g.dem.cv;if(!im)continue;c.globalAlpha=op;c.imageSmoothingEnabled=true;c.imageSmoothingQuality='high';
   c.drawImage(im,X(e[0]),Y(e[3]),(e[2]-e[0])*tf.s,(e[3]-e[1])*tf.s);
   const d=g.ras&&g.ras.detail;if(d)c.drawImage(d.cv,X(d.ext[0]),Y(d.ext[3]),(d.ext[2]-d.ext[0])*tf.s,(d.ext[3]-d.ext[1])*tf.s);c.globalAlpha=1;continue;}
  const V=g.V,col=g.color;c.lineJoin='round';c.lineCap='round';
  if(g.F.length){const nt=g.F.length/3;c.beginPath();for(let t=0;t<g.F.length;t+=3){const a=g.F[t],b=g.F[t+1],d=g.F[t+2];c.moveTo(X(V[3*a]),Y(V[3*a+1]));c.lineTo(X(V[3*b]),Y(V[3*b+1]));c.lineTo(X(V[3*d]),Y(V[3*d+1]));c.closePath();}
   c.fillStyle=hex(col,0.30*op);c.fill();if(nt<=60000&&!o.fast){c.strokeStyle=hex(col,0.55*op);c.lineWidth=0.5*px;c.stroke();}}
  if(g.P.length){c.lineWidth=s.lw*px;c.strokeStyle=hex(col,op);
   if(s.fill>0){c.beginPath();let any=false;for(const p of g.P){if(!p.closed||p.idx.length<3)continue;any=true;c.moveTo(X(V[3*p.idx[0]]),Y(V[3*p.idx[0]+1]));for(let k=1;k<p.idx.length;k++)c.lineTo(X(V[3*p.idx[k]]),Y(V[3*p.idx[k]+1]));c.closePath();}if(any){c.fillStyle=hex(col,s.fill*op);c.fill('evenodd');}}
   const dash=(p)=>s.dashBy>=0&&p.attr&&/dugaan|tidak pasti/i.test(p.attr[s.dashBy]||'');
   for(const dd of (s.dashBy>=0?[false,true]:[false])){c.setLineDash(dd?[7*px,5*px]:[]);c.beginPath();for(const p of g.P){if(s.dashBy>=0&&dash(p)!==dd)continue;c.moveTo(X(V[3*p.idx[0]]),Y(V[3*p.idx[0]+1]));for(let k=1;k<p.idx.length;k++)c.lineTo(X(V[3*p.idx[k]]),Y(V[3*p.idx[k]+1]));if(p.closed)c.closePath();}c.stroke();}c.setLineDash([]);}
  if(g.PT.length){const n=g.PT.length,r=s.pt*px,cb=colorBy(g),rg=cb?(cb.max-cb.min)||1:1;
   if(n>25000&&!cb){c.fillStyle=hex(col,op);const q=Math.max(1.5*px,r*0.5);for(let k=0;k<n;k++){const i=g.PT[k],x=X(V[3*i]),y=Y(V[3*i+1]);if(x<-5||y<-5||x>tf.W+5||y>tf.H+5)continue;c.fillRect(x-q/2,y-q/2,q,q);}}
   else{c.lineWidth=0.8*px;c.strokeStyle='rgba(28,39,51,'+0.55*op+')';c.fillStyle=hex(col,op);
    for(let k=0;k<n;k++){const i=g.PT[k],x=X(V[3*i]),y=Y(V[3*i+1]);if(x<-9||y<-9||x>tf.W+9||y>tf.H+9)continue;if(cb){const v=cb.v[k];c.fillStyle=v===v?rampCss((v-cb.min)/rg):'#999';}if(s.sym){sym(c,g,s,k,x,y,r,px,op);continue;}c.beginPath();c.arc(x,y,r,0,6.2832);c.fill();if(n<6000)c.stroke();}}}
  if(s.label>=0&&st.labels&&!o.noLabels){c.font=(11*px)+'px "Segoe UI",system-ui,sans-serif';c.textBaseline='middle';c.lineWidth=3*px;c.strokeStyle='rgba(255,255,255,.85)';c.fillStyle='#1C2733';let cnt=0;
   const put=(t,x,y)=>{if(t===''||t==null||x<0||y<0||x>tf.W||y>tf.H||cnt>600)return;cnt++;c.strokeText(t,x,y);c.fillText(t,x,y);};
   for(let k=0;k<g.PT.length&&cnt<=600;k++){const a=g.PA[k];if(a)put(a[s.label],X(V[3*g.PT[k]])+(s.pt+3)*px,Y(V[3*g.PT[k]+1]));}
   for(const p of g.P){if(!p.attr||cnt>600)continue;let sx=0,sy=0;for(const i of p.idx){sx+=V[3*i];sy+=V[3*i+1];}const m=p.idx[p.idx.length>>1];c.textAlign='center';if(p.closed)put(p.attr[s.label],X(sx/p.idx.length),Y(sy/p.idx.length));else put(p.attr[s.label],X(V[3*m]),Y(V[3*m+1])-8*px);c.textAlign='left';}}
 }
}
function drawGrid(c,tf,o){
 o=o||{};const px=o.px||1,step=o.step||nice(140/tf.s),X=(x)=>(x-tf.cx)*tf.s+tf.W/2,Y=(y)=>tf.H/2-(y-tf.cy)*tf.s;
 const x0=tf.cx-tf.W/2/tf.s,x1=tf.cx+tf.W/2/tf.s,y0=tf.cy-tf.H/2/tf.s,y1=tf.cy+tf.H/2/tf.s,fmt=(v)=>Math.round(v).toLocaleString('id-ID');
 c.lineWidth=(o.lw||0.6)*px;c.strokeStyle=o.color||'rgba(28,39,51,.16)';c.beginPath();
 for(let x=Math.ceil(x0/step)*step;x<=x1;x+=step){c.moveTo(X(x),0);c.lineTo(X(x),tf.H);}for(let y=Math.ceil(y0/step)*step;y<=y1;y+=step){c.moveTo(0,Y(y));c.lineTo(tf.W,Y(y));}c.stroke();
 c.font=(o.font||10.5)*px+'px "Segoe UI",system-ui,sans-serif';c.fillStyle=o.text||'rgba(28,39,51,.75)';c.strokeStyle='rgba(255,255,255,.9)';c.lineWidth=3*px;c.textBaseline='alphabetic';
 for(let x=Math.ceil(x0/step)*step;x<=x1;x+=step){const t=fmt(x)+(o.suffix?' E':'');c.textAlign='left';c.strokeText(t,X(x)+3*px,tf.H-4*px);c.fillText(t,X(x)+3*px,tf.H-4*px);if(o.both){c.textBaseline='top';c.strokeText(t,X(x)+3*px,4*px);c.fillText(t,X(x)+3*px,4*px);c.textBaseline='alphabetic';}}
 for(let y=Math.ceil(y0/step)*step;y<=y1;y+=step){const t=fmt(y)+(o.suffix?' N':'');c.save();c.translate(4*px,Y(y)-3*px);c.textAlign='left';c.strokeText(t,0,0);c.fillText(t,0,0);c.restore();
  if(o.both){c.save();c.translate(tf.W-4*px,Y(y)-3*px);c.textAlign='right';c.strokeText(t,0,0);c.fillText(t,0,0);c.restore();}}
 return step;
}
function scaleBar(c,x,y,s,px,maxW){const m=nice((maxW||130)*px/s/1.6),w=m*s;c.fillStyle='rgba(247,245,240,.9)';c.fillRect(x-6*px,y-18*px,w+12*px,26*px);c.fillStyle='#1C2733';c.fillRect(x,y,w,3*px);c.fillRect(x,y-4*px,1*px,7*px);c.fillRect(x+w-1*px,y-4*px,1*px,7*px);c.fillRect(x+w/2,y-2*px,1*px,5*px);
 c.font=10.5*px+'px "Segoe UI",system-ui,sans-serif';c.textAlign='center';c.textBaseline='alphabetic';c.fillText(m>=1000?(m/1000)+' km':m+' m',x+w/2,y-6*px);c.textAlign='left';return w;}

/* ---------- render ---------- */
function tf(){return {cx:view.cx,cy:view.cy,s:view.s,W:W,H:Ht};}
const SX=(x)=>(x-view.cx)*view.s+W/2,SY=(y)=>Ht/2-(y-view.cy)*view.s,WX=(sx)=>(sx-W/2)/view.s+view.cx,WY=(sy)=>(Ht/2-sy)/view.s+view.cy;
function draw(){if(raf||!cv)return;raf=requestAnimationFrame(()=>{raf=0;render();});}
function fmtLen(m){return m>=1000?(m/1000).toLocaleString('id-ID',{maximumFractionDigits:3})+' km':m.toLocaleString('id-ID',{maximumFractionDigits:2})+' m';}
function fmtArea(a){return a.toLocaleString('id-ID',{maximumFractionDigits:1})+' m² ('+(a/10000).toLocaleString('id-ID',{maximumFractionDigits:4})+' ha)';}
function shoelace(P){let a=0;for(let k=0;k<P.length;k++){const p=P[k],q=P[(k+1)%P.length];a+=p[0]*q[1]-q[0]*p[1];}return Math.abs(a)/2;}
function pathLen(P,closed){let L=0;for(let k=1;k<P.length;k++)L+=Math.hypot(P[k][0]-P[k-1][0],P[k][1]-P[k-1][1]);if(closed&&P.length>2)L+=Math.hypot(P[0][0]-P[P.length-1][0],P[0][1]-P[P.length-1][1]);return L;}
function render(){
 if(!cv||!W)return;const c=cx;c.setTransform(dpr,0,0,dpr,0,0);c.clearRect(0,0,W,Ht);
 drawLayers(c,tf(),{fast:!!st.pan&&st.pan.moved});
 if(st.grid)drawGrid(c,tf(),{});
 /* fitur terpilih */
 const sel=H.selected&&H.selected();
 if(sel&&sel.g&&sel.g.visible&&!sel.g.ras&&!sel.g.dem){const g=sel.g,V=g.V;c.strokeStyle='#F2B705';c.lineWidth=3;c.fillStyle='#F2B705';
  if(sel.type==='pl'&&g.P[sel.i]){const p=g.P[sel.i];c.beginPath();p.idx.forEach((i,k)=>{k?c.lineTo(SX(V[3*i]),SY(V[3*i+1])):c.moveTo(SX(V[3*i]),SY(V[3*i+1]));});if(p.closed)c.closePath();c.stroke();
   if(st.tool==='edit'){c.lineWidth=1.2;c.strokeStyle='#1C2733';const n=p.idx.length,m=p.closed?n:n-1;
    for(let k=0;k<m;k++){const a=p.idx[k],b=p.idx[(k+1)%n],mx=SX((V[3*a]+V[3*b])/2),my=SY((V[3*a+1]+V[3*b+1])/2);c.fillStyle='rgba(255,255,255,.9)';c.beginPath();c.arc(mx,my,3,0,6.2832);c.fill();c.stroke();}
    for(let k=0;k<n;k++){const i=p.idx[k],hv=st.hov&&st.hov.k===k&&!st.hov.mid;c.fillStyle=hv?'#F2B705':'#fff';c.fillRect(SX(V[3*i])-4,SY(V[3*i+1])-4,8,8);c.strokeRect(SX(V[3*i])-4,SY(V[3*i+1])-4,8,8);}}}
  else if(sel.type==='pt'&&sel.i<g.PT.length){const i=g.PT[sel.i];c.beginPath();c.arc(SX(V[3*i]),SY(V[3*i+1]),sty(g).pt+4,0,6.2832);c.stroke();}}
 /* draf digitasi / ukur */
 const live=(P,closed,color,label)=>{if(!P.length)return;const Q=st.cur&&!st.measDone?P.concat([st.cur]):P;c.strokeStyle=color;c.lineWidth=2;c.setLineDash([]);c.beginPath();Q.forEach((p,k)=>{k?c.lineTo(SX(p[0]),SY(p[1])):c.moveTo(SX(p[0]),SY(p[1]));});
  if(closed&&Q.length>2){c.closePath();c.fillStyle=hex(color,0.15);c.fill();}c.stroke();c.fillStyle='#fff';c.lineWidth=1.2;for(const p of P){c.fillRect(SX(p[0])-3,SY(p[1])-3,6,6);c.strokeRect(SX(p[0])-3,SY(p[1])-3,6,6);}
  if(label&&Q.length>1){const t=closed&&Q.length>2?'Luas '+fmtArea(shoelace(Q))+' · keliling '+fmtLen(pathLen(Q,true)):'Jarak '+fmtLen(pathLen(Q,false)),q=Q[Q.length-1];c.font='600 12px "Segoe UI",system-ui,sans-serif';const w=c.measureText(t).width;let tx=SX(q[0])+12,ty=SY(q[1])-12;if(tx+w+10>W)tx=W-w-10;if(ty<20)ty=20;
   c.fillStyle='rgba(28,39,51,.9)';c.fillRect(tx-5,ty-14,w+10,20);c.fillStyle='#fff';c.textAlign='left';c.textBaseline='alphabetic';c.fillText(t,tx,ty);if(H.onMeasure)H.onMeasure(t);}};
 if(st.tool==='dist')live(st.meas,false,'#C2413B',true);else if(st.tool==='area')live(st.meas,true,'#C2413B',true);
 else if(st.tool==='poly')live(st.draft,true,'#17806B',true);else if(st.tool==='line')live(st.draft,false,'#17806B',true);
 if(st.sdd){const d=st.sdd,ddx=d.cur[0]-d.sx,ddy=d.cur[1]-d.sy,L=Math.hypot(ddx,ddy);c.strokeStyle='#6D4C41';c.lineWidth=2;c.beginPath();c.arc(d.sx,d.sy,4,0,6.2832);c.stroke();if(L>8){const ux=ddx/L,uy=ddy/L;c.beginPath();c.moveTo(d.sx-ux*L,d.sy-uy*L);c.lineTo(d.sx+ux*L,d.sy+uy*L);c.moveTo(d.sx,d.sy);c.lineTo(d.sx-uy*18,d.sy+ux*18);c.stroke();let az=Math.atan2(ddx,-ddy)*180/Math.PI;if(az<0)az+=360;const t='strike '+Math.round(az)+'° · dip ke '+Math.round((az+90)%360)+'°';c.font='600 12px "Segoe UI",system-ui,sans-serif';const w=c.measureText(t).width;c.fillStyle='rgba(28,39,51,.9)';c.fillRect(d.cur[0]+12,d.cur[1]-10,w+10,20);c.fillStyle='#fff';c.textAlign='left';c.textBaseline='middle';c.fillText(t,d.cur[0]+17,d.cur[1]);}}
 if(st.snap){c.strokeStyle=st.snapPU?'#17806B':'#F2B705';c.lineWidth=2;c.strokeRect(SX(st.snap[0])-6,SY(st.snap[1])-6,12,12);}
 /* utara + skala */
 const sm=nice(130/view.s/1.6)*view.s,bx=W-sm-20,by=Ht-16;scaleBar(c,bx,by,view.s,1,130);
 c.save();c.translate(W-28,by-46);c.fillStyle='rgba(247,245,240,.9)';c.beginPath();c.arc(0,0,15,0,6.2832);c.fill();c.fillStyle='#1C2733';c.beginPath();c.moveTo(0,-11);c.lineTo(5,6);c.lineTo(0,2);c.lineTo(-5,6);c.closePath();c.fill();c.font='600 9px "Segoe UI",sans-serif';c.textAlign='center';c.fillText('U',0,13);c.restore();
}
function resize(){if(!cv)return;const r=cv.parentNode.getBoundingClientRect();if(!r.width||!r.height)return;dpr=window.devicePixelRatio||1;W=r.width;Ht=r.height;cv.width=Math.round(W*dpr);cv.height=Math.round(Ht*dpr);cv.style.width=W+'px';cv.style.height=Ht+'px';draw();}
function fitExt(e,pad){if(!e||!isFinite(e[0]))return;view.cx=(e[0]+e[2])/2;view.cy=(e[1]+e[3])/2;const w=Math.max(e[2]-e[0],1e-6),h=Math.max(e[3]-e[1],1e-6);view.s=Math.min(W/w,Ht/h)*(pad||0.9);if(!isFinite(view.s)||view.s<=0)view.s=1;if(w<=1e-6&&h<=1e-6)view.s=2;draw();moved();}
/* batas tahan pencilan: titik nyasar (mis. koordinat 0,0) tidak membuat zoom semua menjauh */
function rext(g){const b=ext(g);if(!b||g.ras||g.dem||g.V.length<60)return b;if(g._rbV===g.V)return g._rb;const n=g.V.length/3,st=Math.max(1,Math.floor(n/4000)),xs=[],ys=[];for(let i=0;i<n;i+=st){xs.push(g.V[3*i]);ys.push(g.V[3*i+1]);}
 xs.sort((p,q)=>p-q);ys.sort((p,q)=>p-q);const q=(a,f)=>a[Math.min(a.length-1,Math.max(0,Math.round(f*(a.length-1))))];let r=b;
 for(const f of [0.02,0.1,0.2,0.3]){const x0=q(xs,f),x1=q(xs,1-f),y0=q(ys,f),y1=q(ys,1-f),w=Math.max(x1-x0,1),h=Math.max(y1-y0,1);if((b[2]-b[0])>12*w||(b[3]-b[1])>12*h){r=[x0-w*0.25,y0-h*0.25,x1+w*0.25,y1+h*0.25];break;}}
 g._rbV=g.V;g._rb=r;return r;}
function fit(only){let e=null;for(const g of (only||H.layers())){if(!only&&!g.visible)continue;const b=rext(g);if(!b)continue;e=e?[Math.min(e[0],b[0]),Math.min(e[1],b[1]),Math.max(e[2],b[2]),Math.max(e[3],b[3])]:b.slice();}fitExt(e);}
let mvT=0;function moved(){clearTimeout(mvT);mvT=setTimeout(()=>{if(H.onView)H.onView();},280);}

/* ---------- snap, hit test ---------- */
function snapAt(sx,sy){let best=null,bd=10;const wx=WX(sx),wy=WY(sy),tol=bd/view.s;let tot=0;
 const pg=H.snapPref&&H.snapPref();if(pg){const V=pg.V,n=pg.PT.length||V.length/3,t2=16/view.s;let pb=null,pd=16;for(let k=0;k<n;k++){const i=pg.PT.length?pg.PT[k]:k,dx=Math.abs(V[3*i]-wx);if(dx>t2)continue;const dy=Math.abs(V[3*i+1]-wy);if(dy>t2)continue;const d=Math.hypot(dx,dy)*view.s;if(d<pd){pd=d;pb=[V[3*i],V[3*i+1],V[3*i+2]];}}if(pb){st.snapPU=true;return pb;}}st.snapPU=false;
 for(const g of H.layers()){if(!g.visible||g.ras||g.dem||!g.V.length)continue;const e=ext(g);if(!e||wx<e[0]-tol||wx>e[2]+tol||wy<e[1]-tol||wy>e[3]+tol)continue;tot+=g.V.length/3;if(tot>400000)break;const V=g.V;
  for(let i=0;i<V.length;i+=3){const dx=Math.abs(V[i]-wx);if(dx>tol)continue;const dy=Math.abs(V[i+1]-wy);if(dy>tol)continue;const d=Math.hypot(dx,dy)*view.s;if(d<bd){bd=d;best=[V[i],V[i+1],V[i+2]];}}}
 return best;}
function zAt(x,y){for(const g of H.layers()){if(!g.visible||!g.dem)continue;const z=GC.demZ(g.dem,x,y);if(z===z)return z;}return 0;}
function world(e,snap){const r=cv.getBoundingClientRect(),sx=e.clientX-r.left,sy=e.clientY-r.top;const s=snap?snapAt(sx,sy):null;st.snap=s;if(s)return s.slice();const x=WX(sx),y=WY(sy);return [x,y,zAt(x,y)];}
function segDist(px,py,ax,ay,bx,by){const vx=bx-ax,vy=by-ay,l2=vx*vx+vy*vy;let t=l2?((px-ax)*vx+(py-ay)*vy)/l2:0;t=t<0?0:t>1?1:t;return Math.hypot(px-ax-t*vx,py-ay-t*vy);}
function inPoly(V,idx,x,y){let c=false;for(let k=0,j=idx.length-1;k<idx.length;j=k++){const xi=V[3*idx[k]],yi=V[3*idx[k]+1],xj=V[3*idx[j]],yj=V[3*idx[j]+1];if((yi>y)!==(yj>y)&&x<(xj-xi)*(y-yi)/(yj-yi)+xi)c=!c;}return c;}
function hit(x,y,linesOnly){const tol=7/view.s,L=H.layers().filter(g=>g.visible),inE=(g)=>{const e=ext(g);return e&&x>=e[0]-tol&&x<=e[2]+tol&&y>=e[1]-tol&&y<=e[3]+tol;};
 for(const g of L){if(g.ras||g.dem||!inE(g))continue;const V=g.V;
  if(!linesOnly){let b=-1,bd=tol;for(let k=0;k<g.PT.length;k++){const i=g.PT[k],d=Math.hypot(V[3*i]-x,V[3*i+1]-y);if(d<bd){bd=d;b=k;}}if(b>=0)return {g:g,type:'pt',i:b};}
  let b=-1,bd=tol;for(let q=0;q<g.P.length;q++){const p=g.P[q],n=p.idx.length,m=p.closed?n:n-1;for(let k=0;k<m;k++){const a=p.idx[k],c=p.idx[(k+1)%n],d=segDist(x,y,V[3*a],V[3*a+1],V[3*c],V[3*c+1]);if(d<bd){bd=d;b=q;}}}
  if(b>=0)return {g:g,type:'pl',i:b};}
 for(const g of L){if(g.ras||g.dem||!inE(g))continue;let b=-1,ba=Infinity;for(let q=0;q<g.P.length;q++){const p=g.P[q];if(p.closed&&p.idx.length>2&&inPoly(g.V,p.idx,x,y)){const a=GC.polyArea(g.V,p.idx);if(a<ba){ba=a;b=q;}}}if(b>=0)return {g:g,type:'pl',i:b};}
 if(linesOnly)return null;
 for(const g of L){if(g.ras||g.dem||!g.F.length||!inE(g))continue;const V=g.V;for(let t=0;t<g.F.length;t+=3){const a=g.F[t],b=g.F[t+1],c=g.F[t+2],ax=V[3*a],ay=V[3*a+1],bx=V[3*b],by=V[3*b+1],qx=V[3*c],qy=V[3*c+1],den=(by-qy)*(ax-qx)+(qx-bx)*(ay-qy);if(Math.abs(den)<1e-12)continue;
   const w1=((by-qy)*(x-qx)+(qx-bx)*(y-qy))/den,w2=((qy-ay)*(x-qx)+(ax-qx)*(y-qy))/den,w3=1-w1-w2;if(w1>=0&&w2>=0&&w3>=0)return {g:g,type:'mesh',i:t/3,z:w1*V[3*a+2]+w2*V[3*b+2]+w3*V[3*c+2],x:x,y:y};}}
 for(const g of L){if(g.dem){const z=GC.demZ(g.dem,x,y);if(z===z)return {g:g,type:'dem',z:z,x:x,y:y};}else if(g.ras){const e=g.ras.ext;if(x>=e[0]&&x<=e[2]&&y>=e[1]&&y<=e[3])return {g:g,type:'ras',x:x,y:y};}}
 return null;}
function compact(g){const n=g.V.length/3,map=new Int32Array(n).fill(-1),out=[];const ref=(i)=>{if(map[i]<0){map[i]=out.length/3;out.push(g.V[3*i],g.V[3*i+1],g.V[3*i+2]);}return map[i];};
 const F=Uint32Array.from(g.F,ref);for(const p of g.P)p.idx=p.idx.map(ref);const PT=Uint32Array.from(g.PT,ref);g.F=F;g.PT=PT;g.V=Float64Array.from(out);GC.bake(g);g._ms=undefined;}

/* ---------- interaksi ---------- */
function handleAt(sx,sy){const sel=H.selected&&H.selected();if(!sel||sel.type!=='pl'||!sel.g.P[sel.i])return null;const g=sel.g,p=g.P[sel.i],V=g.V,n=p.idx.length;
 for(let k=0;k<n;k++){const i=p.idx[k];if(Math.abs(SX(V[3*i])-sx)<=7&&Math.abs(SY(V[3*i+1])-sy)<=7)return {k:k};}
 const m=p.closed?n:n-1;for(let k=0;k<m;k++){const a=p.idx[k],b=p.idx[(k+1)%n];if(Math.hypot(SX((V[3*a]+V[3*b])/2)-sx,SY((V[3*a+1]+V[3*b+1])/2)-sy)<=6)return {k:k,mid:true};}return null;}
function finishDraft(){const P=st.draft;st.draft=[];st.snap=null;const need=st.tool==='poly'?3:2;if(P.length>=need&&H.onDigit)H.onDigit(st.tool,P);draw();}
function setTool(t){st.tool=t;st.sdd=null;st.draft=[];st.meas=[];st.measDone=false;st.snap=null;st.hov=null;cv.style.cursor=t==='pan'?'grab':t==='info'?'help':t==='edit'?'default':'crosshair';if(H.onMeasure)H.onMeasure('');draw();}
function init(canvas,hooks){
 cv=canvas;cx=cv.getContext('2d');H=hooks;
 cv.addEventListener('contextmenu',e=>e.preventDefault());
 cv.addEventListener('wheel',(e)=>{e.preventDefault();const r=cv.getBoundingClientRect(),sx=e.clientX-r.left,sy=e.clientY-r.top,wx=WX(sx),wy=WY(sy),k=Math.exp(-e.deltaY*0.0015);view.s=Math.max(1e-6,Math.min(1e6,view.s*k));view.cx=wx-(sx-W/2)/view.s;view.cy=wy+(sy-Ht/2)/view.s;draw();moved();},{passive:false});
 cv.addEventListener('pointerdown',(e)=>{cv.setPointerCapture(e.pointerId);const r=cv.getBoundingClientRect(),sx=e.clientX-r.left,sy=e.clientY-r.top;
  if(st.tool==='edit'&&e.button===0){const h=handleAt(sx,sy);if(h){const sel=H.selected(),g=sel.g,p=g.P[sel.i];if(H.beforeEdit)H.beforeEdit(g);GC.bake(g);
    if(h.mid){const a=p.idx[h.k],b=p.idx[(h.k+1)%p.idx.length],o=g.V.length/3,V=new Float64Array(g.V.length+3);V.set(g.V);V.set([(g.V[3*a]+g.V[3*b])/2,(g.V[3*a+1]+g.V[3*b+1])/2,(g.V[3*a+2]+g.V[3*b+2])/2],g.V.length);g.V=V;p.idx.splice(h.k+1,0,o);h.k=h.k+1;h.mid=false;}
    st.drag={g:g,p:p,k:h.k};return;}}
  if(st.tool==='sd'&&e.button===0&&!st.pickCb){st.sdd={p:world(e,true),sx:sx,sy:sy,cur:[sx,sy]};draw();return;}
  st.pan={x:e.clientX,y:e.clientY,x0:e.clientX,y0:e.clientY,moved:false,btn:e.button};cv.style.cursor=st.tool==='pan'?'grabbing':cv.style.cursor;});
 cv.addEventListener('pointermove',(e)=>{const r=cv.getBoundingClientRect(),sx=e.clientX-r.left,sy=e.clientY-r.top;
  if(st.drag){const w=world(e,true),d=st.drag,i=d.p.idx[d.k];d.g.V[3*i]=w[0];d.g.V[3*i+1]=w[1];if(st.snap||zAt(w[0],w[1]))d.g.V[3*i+2]=w[2];d.g._bbV=null;draw();if(H.onCursor)H.onCursor(w[0],w[1]);return;}
  if(st.sdd){st.sdd.cur=[sx,sy];draw();if(H.onCursor)H.onCursor(WX(sx),WY(sy));return;}
  if(st.pan){const dx=e.clientX-st.pan.x,dy=e.clientY-st.pan.y;if(!st.pan.moved&&Math.hypot(e.clientX-st.pan.x0,e.clientY-st.pan.y0)>4)st.pan.moved=true;if(st.pan.moved){view.cx-=dx/view.s;view.cy+=dy/view.s;st.pan.x=e.clientX;st.pan.y=e.clientY;draw();moved();}return;}
  const dig=!!st.pickCb||st.tool==='sd'||st.tool==='poly'||st.tool==='line'||st.tool==='point'||st.tool==='dist'||st.tool==='area';
  if(dig){st.cur=world(e,true);draw();}else{st.cur=null;if(st.snap){st.snap=null;draw();}}
  if(st.tool==='edit'){const h=handleAt(sx,sy);if((h&&!st.hov)||(!h&&st.hov)||(h&&st.hov&&(h.k!==st.hov.k||h.mid!==st.hov.mid))){st.hov=h;cv.style.cursor=h?'move':'default';draw();}}
  if(H.onCursor)H.onCursor(WX(sx),WY(sy));});
 cv.addEventListener('pointerup',(e)=>{
  if(st.drag){const d=st.drag;st.drag=null;st.snap=null;GC.bake(d.g);d.g._bbV=null;if(H.onChange)H.onChange(d.g);draw();return;}
  if(st.sdd){const d=st.sdd;st.sdd=null;st.snap=null;const ddx=d.cur[0]-d.sx,ddy=d.cur[1]-d.sy,mv=Math.hypot(ddx,ddy)>8;let az=null;if(mv){az=Math.atan2(ddx,-ddy)*180/Math.PI;if(az<0)az+=360;}if(H.onDigit)H.onDigit('sd',[d.p],{az:az});draw();return;}
  const p=st.pan;st.pan=null;cv.style.cursor=st.tool==='pan'?'grab':cv.style.cursor;if(!p)return;if(p.moved){draw();return;}
  if(st.pickCb&&p.btn===0){const cb=st.pickCb;st.pickCb=null;const w=world(e,true);st.snap=null;cv.style.cursor=st.tool==='pan'?'grab':'crosshair';cb(w);draw();return;}
  if(p.btn===2){if(st.draft.length)finishDraft();else if(st.meas.length){st.measDone=true;draw();}return;}if(p.btn!==0)return;
  const w=world(e,st.tool!=='info'&&st.tool!=='pan'&&st.tool!=='edit');
  if(st.tool==='info'||st.tool==='pan'||st.tool==='edit'){const h=hit(w[0],w[1],st.tool==='edit');if(st.tool!=='pan'||h)if(H.onPick)H.onPick(h,st.tool);draw();}
  else if(st.tool==='dist'||st.tool==='area'){if(st.measDone){st.meas=[];st.measDone=false;}st.meas.push(w);draw();}
  else if(st.tool==='point'){if(H.onDigit)H.onDigit('point',[w]);}
  else{const l=st.draft[st.draft.length-1];if(!l||Math.hypot(SX(l[0])-SX(w[0]),SY(l[1])-SY(w[1]))>2)st.draft.push(w);draw();}});
 cv.addEventListener('dblclick',(e)=>{if(st.tool==='poly'||st.tool==='line')finishDraft();else if(st.tool==='dist'||st.tool==='area'){st.measDone=true;draw();}else if(st.tool==='pan')fit();});
 cv.addEventListener('pointerleave',()=>{if(H.onCursor)H.onCursor(null);});
}
function key(e){
 if(e.key==='Escape'&&st.pickCb){const cb=st.pickCb;st.pickCb=null;st.snap=null;cb(null);draw();return true;}
 if(e.key==='Escape'){if(st.draft.length||st.meas.length){st.draft=[];st.meas=[];st.measDone=false;st.snap=null;draw();return true;}return false;}
 if(e.key==='Enter'){if(st.draft.length){finishDraft();return true;}if(st.meas.length){st.measDone=true;draw();return true;}}
 if(e.key==='Backspace'&&st.draft.length){st.draft.pop();draw();return true;}
 if((e.key==='Delete')&&st.tool==='edit'&&st.hov&&!st.hov.mid){const sel=H.selected();if(sel&&sel.type==='pl'){const g=sel.g,p=g.P[sel.i];if(p.idx.length>(p.closed?3:2)){if(H.beforeEdit)H.beforeEdit(g);p.idx.splice(st.hov.k,1);compact(g);st.hov=null;if(H.onChange)H.onChange(g);draw();}return true;}}
 return false;}
return {pickOnce:(cb)=>{st.pickCb=cb;cv.style.cursor='crosshair';},init:init,draw:draw,resize:resize,fit:fit,fitExt:fitExt,setTool:setTool,tool:()=>st.tool,key:key,view:view,st:st,drawLayers:drawLayers,drawGrid:drawGrid,scaleBar:scaleBar,ext:ext,sty:sty,compact:compact,nice:nice,fmtLen:fmtLen,fmtArea:fmtArea,size:()=>[W,Ht],hit:hit,png:()=>cv.toDataURL('image/png')};
})();
