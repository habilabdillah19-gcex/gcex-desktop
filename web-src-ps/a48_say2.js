/* a48: SAYATAN v2 — penampang dengan BLOCK MODEL dan tata letak siap lapor.
   • Blok model yang terpotong bidang sayatan digambar sebagai kotak berwarna (per kelas kadar atau nilai kadar), penuh di dalam galian
     (antara topografi dan desain), pudar di luarnya; ringkasan ore / waste pada sayatan dihitung dari luas potongannya.
   • Tata letak: kepala gambar (judul, azimut, panjang, geser, skala), tanah & galian diarsir, sumbu RL kiri-kanan, koordinat ujung A / B,
     batang skala, legenda di dalam gambar (ikut ke PNG).
   • Interaktif: garis bidik + kotak baca (RL tiap permukaan, tebal galian, kadar blok di bawah kursor) dan alat Ukur (jarak, ΔRL, sudut lereng).
   Catatan: blok dianggap sejajar sumbu E–N (block model terotasi belum digambar miring di sayatan). */
const SY2={bm:true,mode:'kls',lab:true,hov:null,ms:[],msOn:false,blk:null,key:'',m:null,D:null,dkey:'',raf:0,sum:null};
(function(){const st=document.createElement('style');st.textContent=
`#sayw{border-color:#1C2733;border-radius:4px}#sayh{background:#1C2733;border-bottom:2px solid #B5893E;padding:6px 10px}#sayh b{letter-spacing:.2px}#sayh button{background:#2c3b4d;border-radius:3px}#sayh button:hover{background:#2B5F9E}
#sayb{background:#F7F5F0;border-bottom:1px solid #D3CDC1;gap:5px 9px;color:#1C2733}#sayb button{border:1px solid #c9c2b4;background:#fff;border-radius:3px;cursor:pointer}#sayb button:hover{border-color:#2B5F9E;color:#2B5F9E}#sayb button.on{background:#2B5F9E;color:#fff;border-color:#2B5F9E}
#sayb .sep{width:1px;height:18px;background:#D3CDC1}#sayb label{display:flex;align-items:center;gap:3px;cursor:pointer}#sayb select{font:12px system-ui;padding:1px 2px}
#saylg{background:#fff;border-bottom:1px solid #EDEBE6;font-size:11.5px}#saycv{background:#fff}#sayinf{background:#EDEBE6;border-top:1px solid #D3CDC1;font-size:11.5px;color:#1C2733}`;document.head.appendChild(st);
 const b=$('sayb');if(!b)return;const x=document.createElement('span');x.style.cssText='display:contents';x.innerHTML='<span class="sep"></span><label title="Gambar blok model yang terpotong sayatan (perlu block model .mdl dimuat)"><input type="checkbox" id="saybm" checked> block model</label><select id="saybmm" title="Pewarnaan blok"><option value="kls">per kelas kadar</option><option value="val">nilai kadar</option></select><label title="Tulis nilai kadar di dalam blok bila cukup besar"><input type="checkbox" id="saybl" checked> angka</label><span class="sep"></span><button id="sayms" title="Ukur: klik dua titik di penampang → jarak, beda RL dan sudut lereng. Klik ketiga = mulai lagi.">&#128208; Ukur</button>';b.appendChild(x);
 $('saybm').onchange=()=>{SY2.bm=$('saybm').checked;sayDraw();};$('saybmm').onchange=()=>{SY2.mode=$('saybmm').value;sayDraw();};$('saybl').onchange=()=>{SY2.lab=$('saybl').checked;sayDraw();};
 $('sayms').onclick=()=>{SY2.msOn=!SY2.msOn;SY2.ms=[];$('sayms').classList.toggle('on',SY2.msOn);$('saycv').style.cursor=SY2.msOn?'copy':'crosshair';sayDraw();};
 const c=$('saycv');let dn=null;const later=()=>{if(SY2.raf)return;SY2.raf=requestAnimationFrame(()=>{SY2.raf=0;try{sayDraw();}catch(_){}});};
 c.addEventListener('mousemove',e=>{const r=c.getBoundingClientRect();SY2.hov=[e.clientX-r.left,e.clientY-r.top];later();});c.addEventListener('mouseleave',()=>{SY2.hov=null;later();});
 c.addEventListener('mousedown',e=>{dn=[e.clientX,e.clientY];});
 c.addEventListener('click',e=>{if(!SY2.msOn||!SAY.view||!dn||Math.hypot(e.clientX-dn[0],e.clientY-dn[1])>3)return;const r=c.getBoundingClientRect(),q=sayInv(e.clientX-r.left,e.clientY-r.top);if(SY2.ms.length>=2)SY2.ms=[];SY2.ms.push(q);later();});
 
})();
function sy2Col(g){const k=gtCls(g);if(SY2.mode==='kls')return k<0?'#cfd4da':(GT.rules[k].c||'#f08c00');if(k<0||!(g===g))return '#cfd4da';const lo=+GT.rules.reduce((a,r)=>Math.min(a,+r.lo),1e9),hi=Math.max(lo*4,+GT.rules.reduce((a,r)=>Math.max(a,+r.lo),0)*2),t=Math.max(0,Math.min(1,(g-lo)/(hi-lo||1)));
 const S=[[255,224,102],[250,176,5],[240,62,62],[166,30,77],[95,61,196]],x=t*(S.length-1),i=Math.min(S.length-2,Math.floor(x)),f=x-i;return 'rgb('+S[i].map((v,j)=>Math.round(v+(S[i+1][j]-v)*f)).join(',')+')';}
/* blok yang terpotong bidang sayatan → [d0,d1,zBawah,zAtas,kadar,indeks] */
function sy2Blocks(L){const m=GT.m;if(!m||!GT.attr||!m.num||!m.num[GT.attr])return null;const key=[L.a[0].toFixed(2),L.a[1].toFixed(2),L.b[0].toFixed(2),L.b[1].toFixed(2),GT.attr,m.n].join(',');if(SY2.key===key&&SY2.m===m)return SY2.blk;
 const Gr=m.num[GT.attr],out=[],nx=L.uy,ny=-L.ux,ax=Math.abs(nx),ay=Math.abs(ny);
 for(let b=0;b<m.n;b++){const hx=m.sx[b]/2,hy=m.sy[b]/2,dx=m.x[b]-L.a[0],dy=m.y[b]-L.a[1];if(Math.abs(dx*nx+dy*ny)>ax*hx+ay*hy)continue;let t0=0,t1=L.L;
  if(Math.abs(L.ux)>1e-9){const p=(dx-hx)/L.ux,q=(dx+hx)/L.ux;t0=Math.max(t0,Math.min(p,q));t1=Math.min(t1,Math.max(p,q));}else if(Math.abs(dx)>hx)continue;
  if(Math.abs(L.uy)>1e-9){const p=(dy-hy)/L.uy,q=(dy+hy)/L.uy;t0=Math.max(t0,Math.min(p,q));t1=Math.min(t1,Math.max(p,q));}else if(Math.abs(dy)>hy)continue;
  if(!(t1-t0>0.02))continue;const hz=m.sz[b]/2;out.push([t0,t1,m.z[b]-hz,m.z[b]+hz,Gr[b],b]);}
 SY2.key=key;SY2.m=m;SY2.blk=out;return out;}
function sy2Prof(){const L=sayGeo();if(!L)return null;let k=[L.a[0].toFixed(2),L.a[1].toFixed(2),L.b[0].toFixed(2),L.b[1].toFixed(2)].join(',');const S=saySurf();if(SY2.D&&SY2.dkey===k&&SY2.dS&&SY2.dS.length===S.length&&S.every((s,i)=>s.G===SY2.dS[i].G&&s.on===SY2.dS[i].on)&&SY2.dT===(typeof curR==='function'?curR():null))return SY2.D;
 const D=sayProfiles();SY2.D=D;SY2.dkey=k;SY2.dS=S;try{SY2.dT=curR();}catch(_){SY2.dT=null;}return D;}
/* block model belum pernah dimuat ke memori → muat untuk koridor sayatan (sekali) */
function sy2Need(D){if(!SY2.bm||!GT.file||GT.m||SY2.load||GT.busy)return;const tp=TP.find(q=>q.on&&q.G)||TP.find(q=>q.G);if(!tp)return;let z0=1e9,z1=-1e9;for(const s of D.out)for(const p of s.P)if(isFinite(p[1])){z0=Math.min(z0,p[1]);z1=Math.max(z1,p[1]);}if(!(z1>z0))return;
 const L=D.L,x0=Math.min(L.a[0],L.b[0])-30,x1=Math.max(L.a[0],L.b[0])+30,y0=Math.min(L.a[1],L.b[1])-30,y1=Math.max(L.a[1],L.b[1])+30;SY2.load=1;gtEnsure({x0,x1,y0,y1,zlo:z0-40,zhi:z1,tp,c:Math.max(1,tp.G.cell)}).then(()=>{SY2.load=0;sayDraw();}).catch(()=>{SY2.load=2;});}
sayDraw=function(){const w=$('sayw');if(w.style.display!=='flex')return;const D=sy2Prof(),cv2=$('saycv'),r=cv2.getBoundingClientRect(),dpr=window.devicePixelRatio||1;cv2.width=Math.max(10,r.width*dpr);cv2.height=Math.max(10,r.height*dpr);const g=cv2.getContext('2d');g.setTransform(dpr,0,0,dpr,0,0);g.fillStyle='#fff';g.fillRect(0,0,r.width,r.height);
 const FT='system-ui,Segoe UI,Arial,sans-serif',NV='#1C2733',GD='#B5893E',MU='#6b7280',id=n=>n.toLocaleString('id-ID',{minimumFractionDigits:1,maximumFractionDigits:1});
 if(!D){g.fillStyle=MU;g.font='13px '+FT;g.fillText('Tekan "Tarik ulang", lalu tekan-tarik-lepas di jendela 3D.',20,34);return;}
 const haveBm=!!(GT.file&&GT.attr);try{sy2Need(D);}catch(_){}
 /* legenda DOM (centang tampil / sembunyi) */const lg=$('saylg'),lh=D.out.map(s=>'<label><input type="checkbox" data-sy="'+esc(s.id)+'"'+(SAY.hide[s.id]?'':' checked')+'><i style="background:'+s.col+'"></i>'+esc(s.nm)+'</label>').join('')+'<label><input type="checkbox" data-sy="__x"'+(SAY.hide.__x?'':' checked')+'><i style="background:linear-gradient(90deg,#c92a2a 50%,#1971c2 50%)"></i>titik crest / toe / jalan</label>';
 if(lg._h!==lh){lg._h=lh;lg.innerHTML=lh;lg.querySelectorAll('[data-sy]').forEach(c=>c.onchange=()=>{SAY.hide[c.dataset.sy]=!c.checked;lg._h='';sayDraw();});}
 const ml=62,mr=54,mt=46,mb=44,pw=Math.max(40,r.width-ml-mr),ph=Math.max(40,r.height-mt-mb);SAY.ml=ml;SAY.mt=mt;SAY.pw=pw;SAY.ph=ph;
 if(!SAY.view){let z0=1e9,z1=-1e9;for(const s of D.out){if(SAY.hide[s.id])continue;for(const p of s.P)if(isFinite(p[1])){z0=Math.min(z0,p[1]);z1=Math.max(z1,p[1]);}}if(!(z1>z0)){z0=0;z1=100;}const pad=(z1-z0)*0.1+3;z0-=pad*1.4;z1+=pad;
  let s0=0,s1=D.L.L;const mx=(s1-s0)/pw,mz=(z1-z0)/ph/SAY.ve;if(mz>mx){const c=(s0+s1)/2,h=mz*pw/2;s0=c-h;s1=c+h;}else{const c=(z0+z1)/2,h=mx*SAY.ve*ph/2;z0=c-h;z1=c+h;}SAY.view={s0,s1,z0,z1};}
 const V=SAY.view,X=s=>ml+(s-V.s0)/(V.s1-V.s0)*pw,Y=z=>mt+(V.z1-z)/(V.z1-V.z0)*ph,vis=D.out.filter(s=>!SAY.hide[s.id]);
 const tp=vis.find(s=>s.topo&&s.on)||vis.find(s=>s.topo),ds=vis.find(s=>s.id==='edo')||vis.find(s=>s.id==='stg')||vis.find(s=>s.id==='res')||vis.find(s=>!s.topo);
 const nice=(span,n)=>{const r0=span/n,p=Math.pow(10,Math.floor(Math.log10(r0))),m=r0/p;return (m<1.5?1:m<3?2:m<7?5:10)*p;};
 /* ---- kepala gambar ---- */
 g.fillStyle=NV;g.font='600 14px '+FT;g.textBaseline='alphabetic';g.fillText('PENAMPANG A – B',ml,19);g.fillStyle=GD;g.fillRect(ml,25,34,2);
 g.fillStyle=MU;g.font='11.5px '+FT;g.fillText('Azimut '+id(D.L.az)+'°  ·  panjang '+id(D.L.L)+' m  ·  geser '+(SAY.off>0?'+':'')+id(SAY.off)+' m  ·  skala vertikal '+SAY.ve+'×',ml,39);
 /* ---- isi gambar ---- */g.save();g.beginPath();g.rect(ml,mt,pw,ph);g.clip();
 {const sk=g.createLinearGradient(0,mt,0,mt+ph);sk.addColorStop(0,'#f4f8fc');sk.addColorStop(1,'#ffffff');g.fillStyle=sk;g.fillRect(ml,mt,pw,ph);}
 if(tp){/* tanah di bawah topografi */g.beginPath();let pen=false,lx=0;for(const p of tp.P){if(!isFinite(p[1])){if(pen){g.lineTo(lx,mt+ph+4);g.closePath();pen=false;}continue;}const x=X(p[0]),y=Y(p[1]);if(!pen){g.moveTo(x,mt+ph+4);g.lineTo(x,y);pen=true;}else g.lineTo(x,y);lx=x;}if(pen){g.lineTo(lx,mt+ph+4);g.closePath();}g.fillStyle='#f3eee3';g.fill();}
 if(tp&&ds){/* galian: antara topografi dan desain */g.fillStyle='rgba(43,95,158,.10)';let run=[];const flush=()=>{if(run.length>1){g.beginPath();run.forEach((q,i)=>{const x=X(q[0]),y=Y(q[1]);i?g.lineTo(x,y):g.moveTo(x,y);});for(let i=run.length-1;i>=0;i--)g.lineTo(X(run[i][0]),Y(run[i][2]));g.closePath();g.fill();}run=[];};
  for(let i=0;i<tp.P.length;i++){const t=tp.P[i][1],d=ds.P[i]?ds.P[i][1]:NaN;if(isFinite(t)&&isFinite(d)&&d<t-0.05)run.push([tp.P[i][0],t,d]);else flush();}flush();}
 /* ---- grid ---- */g.strokeStyle='rgba(28,39,51,.07)';g.lineWidth=1;const dS=nice(V.s1-V.s0,Math.max(4,pw/110)),dZ=nice(V.z1-V.z0,Math.max(3,ph/52));
 for(let s=Math.ceil(V.s0/dS)*dS;s<=V.s1;s+=dS){const x=Math.round(X(s))+.5;g.beginPath();g.moveTo(x,mt);g.lineTo(x,mt+ph);g.stroke();}for(let z=Math.ceil(V.z0/dZ)*dZ;z<=V.z1;z+=dZ){const y=Math.round(Y(z))+.5;g.beginPath();g.moveTo(ml,y);g.lineTo(ml+pw,y);g.stroke();}
 /* ---- block model ---- */let B=null,hb=null;SY2.sum=null;
 if(SY2.bm&&haveBm){try{B=sy2Blocks(D.L);}catch(_){B=null;}}
 if(B&&B.length){const n=tp?tp.P.length-1:0,zAt=(P,d)=>{if(!P||!n)return NaN;const f=d/D.L.L*n,i=Math.max(0,Math.min(n-1,Math.floor(f))),a=P[i][1],b=P[i+1][1];return isFinite(a)&&isFinite(b)?a+(b-a)*(f-i):(isFinite(a)?a:b);};
  let oa=0,og=0,wa=0,ot=0;const SGa=GT.sg&&GT.m.num?GT.m.num[GT.sg]:null;const hv=SY2.hov&&SAY.view?sayInv(SY2.hov[0],SY2.hov[1]):null,pxm=pw/(V.s1-V.s0),pzm=ph/(V.z1-V.z0);g.lineWidth=0.6;
  for(const q of B){const dm=(q[0]+q[1])/2,zc=(q[2]+q[3])/2,zt=zAt(tp&&tp.P,dm);if(isFinite(zt)&&zc>zt)continue;const zd=ds?zAt(ds.P,dm):NaN,ins=isFinite(zd)&&isFinite(zt)&&zd<zt-0.05&&zc>=zd;
   if(ins){const a=(q[1]-q[0])*(q[3]-q[2]);if(gtCls(q[4])>=0){let sg=SGa?SGa[q[5]]:GT.sgc;if(!(sg>0))sg=GT.sgc||2.6;oa+=a;og+=a*q[4];ot+=a*sg;}else wa+=a;}
   if(q[1]<V.s0||q[0]>V.s1||q[3]<V.z0||q[2]>V.z1)continue;const x=X(q[0]),y=Y(q[3]),bw=(q[1]-q[0])*pxm,bh=(q[3]-q[2])*pzm;g.globalAlpha=ins?0.92:(ds?0.28:0.8);g.fillStyle=sy2Col(q[4]);g.fillRect(x,y,bw,bh);
   if(bw>5&&bh>5){g.globalAlpha=ins?0.55:0.25;g.strokeStyle='#fff';g.strokeRect(x+.3,y+.3,bw-.6,bh-.6);}
   if(SY2.lab&&bw>30&&bh>13&&q[4]===q[4]&&(ins||!ds)){g.globalAlpha=1;g.fillStyle=gtCls(q[4])<0?'#5c6370':'#1b1b1b';g.font='10px '+FT;g.textAlign='center';g.fillText(q[4].toFixed(2),x+bw/2,y+bh/2+3.5);g.textAlign='left';}
   if(hv&&hv[0]>=q[0]&&hv[0]<=q[1]&&hv[1]>=q[2]&&hv[1]<=q[3])hb=q;}
  g.globalAlpha=1;SY2.sum={oa,g:oa>0?og/oa:0,wa,ot};if(hb){g.strokeStyle=NV;g.lineWidth=1.6;g.strokeRect(X(hb[0]),Y(hb[3]),(hb[1]-hb[0])*pxm,(hb[3]-hb[2])*pzm);}}
 /* ---- garis permukaan ---- */g.lineJoin='round';g.lineCap='round';
 for(const s of vis){g.strokeStyle=s.col;g.lineWidth=s.topo?(s.on?2:1.3):2.4;g.setLineDash(s.topo&&!s.on?[6,4]:[]);g.beginPath();let pen=false;for(const p of s.P){if(!isFinite(p[1])){pen=false;continue;}const x=X(p[0]),y=Y(p[1]);if(!pen){g.moveTo(x,y);pen=true;}else g.lineTo(x,y);}g.stroke();}
 g.setLineDash([]);if(!SAY.hide.__x)for(const q of D.X){g.fillStyle=q.t==='crest'?'#c92a2a':q.t==='toe'?'#1971c2':q.t==='floor'?'#2f9e44':'#e8590c';g.strokeStyle='#fff';g.lineWidth=1.2;g.beginPath();g.arc(X(q.d),Y(q.z),3.4,0,7);g.fill();g.stroke();}
 /* ujung A / B */for(const [d,c,t] of [[0,'#ff6f00','A'],[D.L.L,NV,'B']]){const x=X(d);g.strokeStyle=c;g.lineWidth=1;g.setLineDash([3,3]);g.beginPath();g.moveTo(x,mt);g.lineTo(x,mt+ph);g.stroke();g.setLineDash([]);g.fillStyle=c;g.beginPath();g.arc(x,mt+11,9,0,7);g.fill();g.fillStyle='#fff';g.font='600 11px '+FT;g.textAlign='center';g.fillText(t,x,mt+15);g.textAlign='left';}
 /* ---- alat ukur ---- */if(SY2.ms.length){const P=SY2.ms.slice();if(P.length===1&&SY2.hov&&SY2.msOn)P.push(sayInv(SY2.hov[0],SY2.hov[1]));g.strokeStyle='#d6336c';g.fillStyle='#d6336c';g.lineWidth=1.6;g.beginPath();P.forEach((q,i)=>{const x=X(q[0]),y=Y(q[1]);i?g.lineTo(x,y):g.moveTo(x,y);});g.stroke();for(const q of P){g.beginPath();g.arc(X(q[0]),Y(q[1]),3.2,0,7);g.fill();}
  if(P.length===2){const dd=P[1][0]-P[0][0],dz=P[1][1]-P[0][1],sl=Math.hypot(dd,dz),an=Math.abs(Math.atan2(dz,Math.abs(dd))*180/Math.PI),t='Δ jarak '+id(Math.abs(dd))+' m · ΔRL '+(dz>0?'+':'')+id(dz)+' m · miring '+id(sl)+' m · sudut '+id(an)+'°'+(Math.abs(dd)>0.01?' ('+id(Math.abs(dz/dd)*100)+'%)':'')+' · arah '+id(dd>=0?D.L.az:(D.L.az+180)%360)+'°';
   g.font='600 11.5px '+FT;const tw=g.measureText(t).width+12,cx=Math.max(ml+4,Math.min(ml+pw-tw-4,(X(P[0][0])+X(P[1][0]))/2-tw/2)),cy=Math.max(mt+26,(Y(P[0][1])+Y(P[1][1]))/2-16);g.fillStyle='rgba(255,255,255,.95)';g.fillRect(cx,cy-13,tw,18);g.strokeStyle='#d6336c';g.lineWidth=1;g.strokeRect(cx+.5,cy-12.5,tw,18);g.fillStyle='#a61e4d';g.fillText(t,cx+6,cy);}}
 /* ---- batang skala ---- */{const bl=nice((V.s1-V.s0)/5,1),bx=ml+12,by=mt+ph-14,bp=bl/(V.s1-V.s0)*pw;g.fillStyle='rgba(255,255,255,.9)';g.fillRect(bx-6,by-16,bp+48,26);for(let i=0;i<4;i++){g.fillStyle=i%2?'#fff':NV;g.fillRect(bx+bp*i/4,by,bp/4,5);}g.strokeStyle=NV;g.lineWidth=1;g.strokeRect(bx+.5,by+.5,bp,5);g.fillStyle=NV;g.font='10.5px '+FT;g.fillText('0',bx-2,by-3);g.fillText(String(bl).replace('.',',')+' m',bx+bp-8,by-3);}
 /* ---- legenda dalam gambar ---- */{const it=vis.map(s=>({c:s.col,t:s.nm.replace(/^[0-9a-f]{8}-/,''),ln:1,da:s.topo&&!s.on}));if(B&&B.length){if(SY2.mode==='kls'){GT.rules.forEach(rl=>it.push({c:rl.c||'#f08c00',t:rl.m+(rl.lo!==''&&rl.lo!==undefined?' ≥ '+rl.lo:'')+' g/t'}));it.push({c:'#cfd4da',t:'waste'});}else{it.push({c:'#fab005',t:'kadar rendah → '});it.push({c:'#a61e4d',t:'kadar tinggi ('+esc(GT.attr)+')'});it.push({c:'#cfd4da',t:'waste'});}}
  g.font='11px '+FT;const lw=Math.min(pw*0.42,Math.max(...it.map(q=>g.measureText(q.t).width))+34),lhh=it.length*15+10,lx=ml+pw-lw-10,ly=mt+ph-lhh-10;g.fillStyle='rgba(255,255,255,.93)';g.fillRect(lx,ly,lw,lhh);g.strokeStyle='#D3CDC1';g.lineWidth=1;g.strokeRect(lx+.5,ly+.5,lw,lhh);
  it.forEach((q,i)=>{const y=ly+15+i*15;if(q.ln){g.strokeStyle=q.c;g.lineWidth=2.4;g.setLineDash(q.da?[4,3]:[]);g.beginPath();g.moveTo(lx+8,y-4);g.lineTo(lx+24,y-4);g.stroke();g.setLineDash([]);}else{g.fillStyle=q.c;g.fillRect(lx+10,y-9,12,10);}g.fillStyle=NV;g.fillText(q.t.length>34?q.t.slice(0,33)+'…':q.t,lx+30,y);});}
 /* ---- bidik & kotak baca ---- */let tip=null;if(SY2.hov&&SY2.hov[0]>=ml&&SY2.hov[0]<=ml+pw&&SY2.hov[1]>=mt&&SY2.hov[1]<=mt+ph){const [s,z]=sayInv(SY2.hov[0],SY2.hov[1]),x=Math.round(SY2.hov[0])+.5;g.strokeStyle='rgba(28,39,51,.45)';g.lineWidth=1;g.setLineDash([4,3]);g.beginPath();g.moveTo(x,mt);g.lineTo(x,mt+ph);g.moveTo(ml,Math.round(SY2.hov[1])+.5);g.lineTo(ml+pw,Math.round(SY2.hov[1])+.5);g.stroke();g.setLineDash([]);
   if(s>=0&&s<=D.L.L){const n=vis[0]?vis[0].P.length-1:0,f=s/D.L.L*n,i=Math.max(0,Math.min(n-1,Math.floor(f))),R=[];let zt=NaN,zd=NaN;for(const sf of vis){const a=sf.P[i][1],b=sf.P[i+1][1];if(!isFinite(a)||!isFinite(b))continue;const zz=a+(b-a)*(f-i);R.push([sf.col,sf.nm.replace(/^[0-9a-f]{8}-/,''),zz]);if(sf===tp)zt=zz;if(sf===ds)zd=zz;g.fillStyle=sf.col;g.strokeStyle='#fff';g.lineWidth=1.5;g.beginPath();g.arc(X(s),Y(zz),4,0,7);g.fill();g.stroke();}
    tip={s,z,R,th:isFinite(zt)&&isFinite(zd)&&zd<zt?zt-zd:null,hb};}}
 g.restore();
 /* ---- bingkai & sumbu ---- */g.strokeStyle=NV;g.lineWidth=1;g.strokeRect(ml+.5,mt+.5,pw,ph);g.fillStyle=NV;g.font='11px '+FT;
 for(let s=Math.ceil(V.s0/dS)*dS;s<=V.s1+1e-9;s+=dS){const x=X(s);g.beginPath();g.moveTo(x,mt+ph);g.lineTo(x,mt+ph+4);g.stroke();g.textAlign='center';g.fillText(String(Math.round(s*100)/100).replace('.',','),x,mt+ph+16);}
 for(let z=Math.ceil(V.z0/dZ)*dZ;z<=V.z1+1e-9;z+=dZ){const y=Y(z),t=String(Math.round(z*100)/100).replace('.',',');g.beginPath();g.moveTo(ml-4,y);g.lineTo(ml,y);g.moveTo(ml+pw,y);g.lineTo(ml+pw+4,y);g.stroke();g.textAlign='right';g.fillText(t,ml-7,y+4);g.textAlign='left';g.fillText(t,ml+pw+7,y+4);}
 g.textAlign='left';g.fillStyle=MU;g.font='10.5px '+FT;g.save();g.translate(13,mt+ph/2);g.rotate(-Math.PI/2);g.textAlign='center';g.fillText('Elevasi (RL, m)',0,0);g.restore();g.textAlign='center';g.fillText('Jarak dari A (m)',ml+pw/2,mt+ph+31);
 g.textAlign='left';g.fillStyle='#ff6f00';g.font='600 10.5px '+FT;g.fillText('A',ml,mt+ph+31);g.fillStyle=MU;g.font='10.5px '+FT;g.fillText('  E '+id(D.L.a[0])+' · N '+id(D.L.a[1]),ml+8,mt+ph+31);
 g.textAlign='right';g.fillText('E '+id(D.L.b[0])+' · N '+id(D.L.b[1])+'  ',ml+pw-9,mt+ph+31);g.fillStyle=NV;g.font='600 10.5px '+FT;g.fillText('B',ml+pw,mt+ph+31);
 /* ringkasan kanan-atas */g.textAlign='right';g.fillStyle=NV;g.font='11.5px '+FT;let sm='';if(SY2.sum&&(SY2.sum.oa>0||SY2.sum.wa>0))sm='Galian pada sayatan: ore '+Math.round(SY2.sum.oa).toLocaleString('id-ID')+' m² @ '+SY2.sum.g.toFixed(2)+' g/t · waste '+Math.round(SY2.sum.wa).toLocaleString('id-ID')+' m²'+(SY2.sum.ot>0?' · SR '+(SY2.sum.wa/SY2.sum.ot).toFixed(2)+' BCM/t (per m tebal)':'');
 else if(SY2.bm&&!GT.file)sm='block model belum dimuat (Impor → Block model)';else if(SY2.bm&&haveBm&&!(B&&B.length))sm=SY2.load===1?'memuat block model…':'tidak ada blok model di sayatan ini';
 if(sm)g.fillText(sm,ml+pw,19);g.fillStyle=MU;g.font='10.5px '+FT;g.fillText('Pit Studio · '+new Date().toLocaleDateString('id-ID',{day:'numeric',month:'short',year:'numeric'}),ml+pw,39);g.textAlign='left';
 /* kotak baca */if(tip){const Ls=['Jarak '+id(tip.s)+' m  ·  RL '+id(tip.z)];for(const q of tip.R)Ls.push(['●',q[0],q[1].slice(0,26)+'  RL '+id(q[2])]);if(tip.th!=null)Ls.push('Tebal galian '+id(tip.th)+' m');if(tip.hb){const q=tip.hb,k=gtCls(q[4]),m=GT.m;Ls.push('Blok '+GT.attr+' '+(q[4]===q[4]?q[4].toFixed(2):'–')+' g/t · '+(k<0?'waste':GT.rules[k].m)+' · '+m.sx[q[5]]+'×'+m.sy[q[5]]+'×'+m.sz[q[5]]+' m');}
  g.font='11px '+FT;const tw=Math.max(...Ls.map(q=>g.measureText(typeof q==='string'?q:'●  '+q[2]).width))+18,thh=Ls.length*15+9;let tx=SY2.hov[0]+14,ty=SY2.hov[1]+14;if(tx+tw>ml+pw)tx=SY2.hov[0]-tw-12;if(ty+thh>mt+ph)ty=SY2.hov[1]-thh-10;
  g.fillStyle='rgba(28,39,51,.94)';g.fillRect(tx,ty,tw,thh);g.fillStyle=GD;g.fillRect(tx,ty,3,thh);Ls.forEach((q,i)=>{const y=ty+16+i*15;if(typeof q==='string'){g.fillStyle=i?'#e9ecef':'#fff';g.font=(i?'':'600 ')+'11px '+FT;g.fillText(q,tx+10,y);}else{g.fillStyle=q[1];g.fillText('●',tx+10,y);g.fillStyle='#e9ecef';g.font='11px '+FT;g.fillText(q[2],tx+23,y);}});}
};
try{window.__PS3.say2={S:SY2,blk:()=>{const L=sayGeo();return L?(sy2Blocks(L)||[]).length:0;}};}catch(_){}
