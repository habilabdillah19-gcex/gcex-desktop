/* a47: demo yang lebih halus & manusiawi. Kursor bergerak melengkung dengan percepatan-perlambatan alami (minimum-jerk), lama gerak
   mengikuti jarak, berhenti sejenak sebelum mengeklik, tombol "ditekan"; teks keterangan berganti dengan pudar-masuk dan diberi waktu
   baca di SEMUA bab; kamera berputar lebih lembut. Hanya cara menampilkan — langkah dan hasil demo tidak berubah. */
const DMH={r:12345,rnd(){this.r=(this.r*1103515245+12345)&0x7fffffff;return this.r/0x7fffffff;}};
{const st=document.createElement('style');st.textContent='#dmoCur{transition:opacity .25s}#dmoCur.dn{filter:drop-shadow(0 1px 1px rgba(0,0,0,.55))}#dmoCur.dn>*{transform:scale(.86);transform-origin:4px 3px}#dmoCur>*{transition:transform .09s}#dmoRip.go{animation:dmoRip .6s cubic-bezier(.2,.7,.3,1)}#dmoTi,#dmoTx,#dmoSec{transition:opacity .22s ease}#dmoBar.sw #dmoTi,#dmoBar.sw #dmoTx{opacity:0}';document.head.appendChild(st);}
const dmhJerk=t=>t*t*t*(10-15*t+6*t*t);
dmMove=async function(x,y,ms){const x0=DMO.cx,y0=DMO.cy,dx=x-x0,dy=y-y0,d=Math.hypot(dx,dy);if(d<1.5){dmoCurAt(x,y);return;}
 ms=ms?ms*1.15:Math.min(1500,300+170*Math.log2(1+d/14));$('dmoCur').style.opacity=1;const T=ms/DMO.spd;
 /* lintasan Bézier: sedikit melengkung, makin jauh makin melengkung (maks 46 px), sisi lengkung acak tapi tetap */
 const bow=Math.min(46,d*0.13)*(DMH.rnd()<0.5?-1:1)*(0.5+0.5*DMH.rnd()),nx=-dy/d,ny=dx/d,c1x=x0+dx*0.32+nx*bow,c1y=y0+dy*0.32+ny*bow,c2x=x0+dx*0.74+nx*bow*0.55,c2y=y0+dy*0.74+ny*bow*0.55;
 let t=0,l=performance.now();while(t<T){if(DMO.stop)throw DMO_STOP;const n=performance.now();if(!DMO.pause)t+=n-l;l=n;const k=dmhJerk(Math.min(1,t/T)),u=1-k;
  dmoCurAt(u*u*u*x0+3*u*u*k*c1x+3*u*k*k*c2x+k*k*k*x,u*u*u*y0+3*u*u*k*c1y+3*u*k*k*c2y+k*k*k*y);await new Promise(r=>requestAnimationFrame(r));}dmoCurAt(x,y);};
/* titik tuju di dalam elemen: tidak selalu tepat di tengah */
dmPoint=async function(s,ms){const e=dmEl(s),r=dmRect(e);if(!r)return null;const jx=(DMH.rnd()-0.5)*Math.min(18,r.width*0.25),jy=(DMH.rnd()-0.5)*Math.min(6,r.height*0.3);
 await dmMove(r.left+Math.min(r.width/2,r.width-8)+jx,r.top+r.height/2+jy,ms);await dW(140);return e;};
{const _r=dmRip;dmRip=function(){try{const c=$('dmoCur');c.classList.add('dn');setTimeout(()=>c.classList.remove('dn'),170);}catch(_){}return _r.apply(this,arguments);};}
dmClick=async function(s,o){const e=await dmPoint(s);if(!e)return null;await dW(170);dmRip();await dW(90);if(!(o&&o.noFire))e.click();await dW(o&&o.after!==undefined?o.after:420);return e;};
/* keterangan: pudar keluar → ganti teks → pudar masuk, lalu waktu baca sesuai panjang teks */
{const _c=dmCap;dmCap=async function(sec,ti,tx){const b=$('dmoBar'),ch=b&&($('dmoTi').textContent!==ti||$('dmoTx').textContent!==(tx||''));if(b&&ch&&b.style.display!=='none'){b.classList.add('sw');await dRaw(Math.min(200,200/DMO.spd));}
  const r=await _c(sec,ti,tx);if(b)b.classList.remove('sw');await dW(Math.min(5200,600+34*String(tx||'').length));return r;};}
/* kamera: gerak lebih panjang dan lembut */
{const _k=dmCam;dmCam=function(f,ms){return _k.call(this,f,Math.round((ms||1300)*1.35));};}
