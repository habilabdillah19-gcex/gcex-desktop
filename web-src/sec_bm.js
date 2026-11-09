/* ================= GC-Ex Block Model 0.14: UI sayatan SAMA dengan GC-Ex Drillhole =================
   Disalin dari sumber GC-Ex Drillhole (web-src-dh): Sayatan garis bebas dari jendela 3D (S3), menu "Sayatan ▾" di bilah atas
   (Penampang (Sayatan) 2D, Sayatan 3D, opsi slab, digitasi, pengaturan) dan bilah sayatan mengambang (Mundur / posisi / Maju /
   tebal / 2D-3D, PageUp / PageDown). Tambahan khusus Block Model: menu "Pilih arah sayatan di tampak atas (gambar garis)"
   tetap tersedia (fitur lama drawOpen('line')). */
(function(){var st=document.createElement('style');st.textContent='#s3Box{position:absolute;left:14px;top:12px;z-index:9;display:none;width:300px;background:var(--sf);border:1px solid var(--bd);border-left:4px solid #fcc419;border-radius:9px;padding:9px 11px;box-shadow:0 4px 18px rgba(0,0,0,.18);font-size:12.5px}\n#s3Box .s3seg{display:grid;grid-template-columns:1fr 1fr;gap:4px;margin:6px 0}#s3Box .s3seg button.on{background:var(--pr);color:#fff;border-color:var(--pr)}\n#s3Box .s3t{margin:4px 0;line-height:1.35}#s3Box .s3r{display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin-top:5px}#s3Box .s3r input[type=number]{width:60px;padding:2px 4px}#s3Box .s3r label{display:flex;gap:4px;align-items:center;margin:0}\n#btnSec3.on{background:#fcc419;color:#111}';document.head.appendChild(st);})();
/* ================= SAYATAN GARIS BEBAS DARI JENDELA 3D =================
   Satu mode saja: garis bebas, tidak terikat bor / collar / topografi / solid.
   Klik-tahan lalu tarik garis di mana saja pada jendela 3D (atau klik dua titik). Garis bekerja seperti pisau yang memotong
   lurus ke dalam layar: posisi garis dihitung dari kamera (matriks proyeksi Plotly), bukan dari objek di bawah kursor.
   "Bidang tegak" (bawaan) = sayatan vertikal dip 90 deg mengikuti jejak garis; dimatikan = bidang ikut kemiringan pandangan.
   Tampak atas (Top) = garis persis seperti digambar di peta. Scroll = zoom, klik kanan + tarik = geser tetap aktif. Esc = batal. */
var S3={mode:null,p1:null,drag:null,cur:null,to2d:true,vert:true};
function m4mul(a,b){var o=new Array(16);for(var i=0;i<4;i++)for(var j=0;j<4;j++){var s=0;for(var k=0;k<4;k++)s+=a[k*4+i]*b[j*4+k];o[j*4+i]=s;}return o;}
function m4xf(m,v){var o=[0,0,0,0];for(var i=0;i<4;i++)for(var j=0;j<4;j++)o[i]+=m[j*4+i]*v[j];return o;}
function m4inv(m){var a=m,b=[],i;var a00=a[0],a01=a[1],a02=a[2],a03=a[3],a10=a[4],a11=a[5],a12=a[6],a13=a[7],a20=a[8],a21=a[9],a22=a[10],a23=a[11],a30=a[12],a31=a[13],a32=a[14],a33=a[15];
  var b00=a00*a11-a01*a10,b01=a00*a12-a02*a10,b02=a00*a13-a03*a10,b03=a01*a12-a02*a11,b04=a01*a13-a03*a11,b05=a02*a13-a03*a12,b06=a20*a31-a21*a30,b07=a20*a32-a22*a30,b08=a20*a33-a23*a30,b09=a21*a32-a22*a31,b10=a21*a33-a23*a31,b11=a22*a33-a23*a32;
  var d=b00*b11-b01*b10+b02*b09+b03*b08-b04*b07+b05*b06;if(!d||!isFinite(d))return null;d=1/d;
  b=[(a11*b11-a12*b10+a13*b09)*d,(a02*b10-a01*b11-a03*b09)*d,(a31*b05-a32*b04+a33*b03)*d,(a22*b04-a21*b05-a23*b03)*d,(a12*b08-a10*b11-a13*b07)*d,(a00*b11-a02*b08+a03*b07)*d,(a32*b02-a30*b05-a33*b01)*d,(a20*b05-a22*b02+a23*b01)*d,
    (a10*b10-a11*b08+a13*b06)*d,(a01*b08-a00*b10-a03*b06)*d,(a30*b04-a31*b02+a33*b00)*d,(a21*b02-a20*b04-a23*b00)*d,(a11*b07-a10*b09-a12*b06)*d,(a00*b09-a01*b07+a02*b06)*d,(a31*b01-a30*b03-a32*b00)*d,(a20*b03-a21*b01+a22*b00)*d];return b;}
function s3Cam(){var gd=$('plotDiv'),L=gd&&gd._fullLayout,sc=L&&L.scene&&L.scene._scene;if(!sc||!sc.glplot||!sc.glplot.cameraParams||!sc.dataScale)return null;
  var cp=sc.glplot.cameraParams,M=m4mul(cp.projection,m4mul(cp.view,cp.model)),I=m4inv(M);if(!I)return null;return{M:M,I:I,ds:sc.dataScale,r:sc.glplot.canvas.getBoundingClientRect()};}
function s3Ray(C,sx,sy){var nx=2*(sx-C.r.left)/C.r.width-1,ny=1-2*(sy-C.r.top)/C.r.height,f=function(z){var p=m4xf(C.I,[nx,ny,z,1]);return[p[0]/p[3]/C.ds[0],p[1]/p[3]/C.ds[1],p[2]/p[3]/C.ds[2]];};return{a:f(-1),b:f(1)};}
function s3Sub(a,b){return[a[0]-b[0],a[1]-b[1],a[2]-b[2]];}
/* garis layar s1-s2 -> bidang sayatan {a,b (lokal, di elevasi tengah), dip} atau {h:elevasi} untuk bidang datar */
function s3Plane(s1,s2){var C=s3Cam();if(!C)return{err:'Kamera 3D belum siap.'};var r1=s3Ray(C,s1[0],s1[1]),r2=s3Ray(C,s2[0],s2[1]),rm=s3Ray(C,(s1[0]+s2[0])/2,(s1[1]+s2[1])/2);
  var N=nrm(cross(s3Sub(r2.a,r1.a),s3Sub(r1.b,r1.a)));if(!isFinite(N[0]+N[1]+N[2]))return{err:'Garis terlalu pendek.'};if(N[2]<0)N=[-N[0],-N[1],-N[2]];
  var zc=(G.z0+G.z1)/2,ctr=[(G.x0+G.x1)/2,(G.y0+G.y1)/2,zc],vd=nrm(s3Sub(rm.b,rm.a)),hit=function(r){var d=s3Sub(r.b,r.a),den=dot3(d,vd),t=den?dot3(s3Sub(ctr,r.a),vd)/den:0;return[r.a[0]+t*d[0],r.a[1]+t*d[1],r.a[2]+t*d[2]];};
  var Q1=hit(r1),Q2=hit(r2),Qm=hit(rm),h=Math.hypot(N[0],N[1]),dip=Math.acos(Math.min(1,N[2]))*180/Math.PI;
  if(S3.vert){if(h<0.08)return{err:'Dari sudut pandang ini garis sejajar bidang datar. Tekan <b>Tampak atas</b> atau putar kamera, lalu gambar lagi.'};dip=90;}
  else if(dip<2)return{h:Qm[2]};
  var u=[-N[1]/h,N[0]/h,0];if(S3.vert&&dot3(u,s3Sub(Q2,Q1))<0)u=[-u[0],-u[1],0];
  var dd=S3.vert?[0,0,1]:cross(N,u),R=Qm.slice();if(Math.abs(dd[2])>1e-6){var t=(zc-Qm[2])/dd[2];R=[Qm[0]+t*dd[0],Qm[1]+t*dd[1],zc];}
  var t1=dot3(s3Sub(Q1,R),u),t2=dot3(s3Sub(Q2,R),u),full=false,dq=Math.sqrt(dot3(s3Sub(Q2,Q1),s3Sub(Q2,Q1)));if(t1>t2){var q=t1;t1=t2;t2=q;}
  /* garis hampir tegak di layar (mis. tampak depan): sayatan menembus searah pandangan -> pakai seluruh bentang data */
  if(t2-t1<2||(t2-t1)<0.5*dq){full=true;t1=1e18;t2=-1e18;[G.x0,G.x1].forEach(function(x){[G.y0,G.y1].forEach(function(y){var t=(x-R[0])*u[0]+(y-R[1])*u[1];t1=Math.min(t1,t);t2=Math.max(t2,t);});});t1-=10;t2+=10;}
  return{a:[R[0]+t1*u[0],R[1]+t1*u[1]],b:[R[0]+t2*u[0],R[1]+t2*u[1]],dip:Math.round(dip*10)/10,len:t2-t1,az:normAz(Math.atan2(u[0],u[1])*180/Math.PI),full:full};}
function s3Box(){var b=$('s3Box');if(!b){b=document.createElement('div');b.id='s3Box';$('plotDiv').parentNode.appendChild(b);}
  if(!S3.mode){b.style.display='none';return;}b.style.display='block';
  b.innerHTML='<b>&#9986; Sayatan garis bebas</b>'+
    '<div class=s3t>'+(S3.p1?'Titik 1 terpasang. <b>Klik titik 2</b> (atau Esc).':'<b>Tarik garis</b> di mana saja pada jendela 3D (klik-tahan, geser, lepas) &mdash; atau klik dua titik. Tidak perlu mengenai bor / objek.')+
    '<br><small>Garis memotong lurus ke dalam layar. Scroll = zoom &middot; klik kanan + tarik = geser &middot; Esc = batal.</small></div>'+
    '<div class=s3r><button onclick="setCam(0,-0.01,2.5)" title="Kamera tampak atas: garis persis seperti di peta">Tampak atas</button><label title="Mati = bidang mengikuti kemiringan pandangan kamera"><input type=checkbox '+(S3.vert?'checked':'')+' onchange="S3.vert=this.checked;s3Paint()"> Bidang tegak (dip 90&deg;)</label></div>'+
    '<div class=s3r><label>Tebal (m) <input type=number step=any min=0.5 value="'+($('thick').value||10)+'" onchange="$(\'thick\').value=this.value"></label><label><input type=checkbox '+(S3.to2d?'checked':'')+' onchange="S3.to2d=this.checked"> buka Penampang 2D</label></div>'+
    '<div class=s3r><button onclick="s3Off()">Batal</button></div><div id=s3msg class=s3t></div>';}
function s3Open(){if(S3.mode){s3Off();return;}if(VIEW2D)toggle2D();S3.mode='free';S3.p1=null;S3.drag=null;s3Box();var b=$('btnSec3');if(b)b.classList.add('on');var gd=$('plotDiv');if(gd)gd.classList.add('s3on');s3Paint();}
function s3Off(){S3.mode=null;S3.p1=null;S3.drag=null;s3Box();var b=$('btnSec3');if(b)b.classList.remove('on');var gd=$('plotDiv');if(gd)gd.classList.remove('s3on');s3Paint();}
function s3Msg(t){var e=$('s3msg');if(e)e.innerHTML=t;}
/* terapkan garis sayatan (koordinat lokal) */
function s3Apply(a,b,dip){var L=Math.hypot(b[0]-a[0],b[1]-a[1]);if(L<1){s3Msg('<span class=warn>Garis terlalu pendek.</span>');return;}dip=dip==null?90:dip;
  $('sMode').value='P';$('p1e').value=(a[0]+offX).toFixed(2);$('p1n').value=(a[1]+offY).toFixed(2);$('p2e').value=(b[0]+offX).toFixed(2);$('p2n').value=(b[1]+offY).toFixed(2);$('dipS').value=dip;$('dipN').value=dip;
  modeChanged();$('pos').value=0;var sp=$('showPlane');if(sp)sp.checked=true;var go=S3.to2d;s3Off();if(go&&!VIEW2D)toggle2D();else updatePlot();try{if(typeof lineInfoUpd==='function')lineInfoUpd();}catch(e){}try{if(window.SA&&SA.dirty)SA.dirty();}catch(e){}}
function s3Finish(s1,s2){var r=s3Plane(s1,s2);S3.p1=null;S3.drag=null;
  if(r.err){s3Box();s3Msg('<span class=warn>'+r.err+'</span>');s3Paint();return;}
  if(r.h!=null){var go=S3.to2d;setTimeout(function(){$('sMode').value='H';modeChanged();$('pos').value=Math.round(r.h*2)/2;s3Off();if(go&&!VIEW2D)toggle2D();else updatePlot();},30);return;}
  setTimeout(function(){s3Apply(r.a,r.b,r.dip);},30);}
function s3Paint(){var gd=$('plotDiv');if(!gd)return;var c=$('s3Cv');if(!c){c=document.createElement('canvas');c.id='s3Cv';c.style.cssText='position:absolute;left:0;top:0;pointer-events:none;z-index:8';gd.parentNode.appendChild(c);}
  var a=S3.mode?(S3.drag?S3.drag.s:S3.p1):null;if(!a||!S3.cur){c.style.display='none';return;}
  var r=gd.getBoundingClientRect(),pr=gd.parentNode.getBoundingClientRect(),dp=window.devicePixelRatio||1;c.style.display='block';c.style.left=(r.left-pr.left)+'px';c.style.top=(r.top-pr.top)+'px';c.style.width=r.width+'px';c.style.height=r.height+'px';c.width=r.width*dp;c.height=r.height*dp;
  var x=c.getContext('2d');x.setTransform(dp,0,0,dp,0,0);x.clearRect(0,0,r.width,r.height);var p=[a[0]-r.left,a[1]-r.top],q=[S3.cur[0]-r.left,S3.cur[1]-r.top];
  x.lineWidth=5;x.strokeStyle='rgba(17,17,17,.55)';x.beginPath();x.moveTo(p[0],p[1]);x.lineTo(q[0],q[1]);x.stroke();x.lineWidth=2.5;x.strokeStyle='#fcc419';x.setLineDash([10,6]);x.beginPath();x.moveTo(p[0],p[1]);x.lineTo(q[0],q[1]);x.stroke();x.setLineDash([]);
  [p,q].forEach(function(s,i){x.beginPath();x.arc(s[0],s[1],i?4.5:6,0,7);x.fillStyle='#fcc419';x.fill();x.lineWidth=1.6;x.strokeStyle='#111';x.stroke();});
  if(Math.hypot(q[0]-p[0],q[1]-p[1])>8){var R=s3Plane(a,S3.cur),t=R.err?'garis sejajar bidang datar':R.h!=null?'bidang datar Z '+fx(R.h,1)+' m':(R.full?'memotong seluruh data':'~'+fx(R.len,0)+' m')+' · arah '+fx(R.az,0)+'°'+(R.dip<90?' · dip '+fx(R.dip,0)+'°':'');
    x.font='600 12px Arial';var w=x.measureText(t).width+12,lx=Math.min(r.width-w-4,Math.max(4,q[0]+12)),ly=Math.max(18,q[1]-10);x.fillStyle='rgba(17,17,17,.82)';x.fillRect(lx,ly-14,w,20);x.fillStyle='#fff';x.fillText(t,lx+6,ly);}}
(function(){var gd=$('plotDiv');if(!gd)return;var inPlot=function(e){var t=e.target;return gd.contains(t)&&!(t.closest&&t.closest('.modebar'));};
  /* tangkap lebih dulu (fase capture di window) supaya Plotly tidak memutar kamera saat menggambar */
  window.addEventListener('mousedown',function(e){if(!S3.mode||VIEW2D||e.button!==0||!inPlot(e))return;e.stopPropagation();e.preventDefault();S3.drag={s:[e.clientX,e.clientY]};S3.cur=[e.clientX,e.clientY];s3Paint();},true);
  window.addEventListener('mousemove',function(e){if(!S3.mode)return;S3.cur=[e.clientX,e.clientY];if(S3.drag){e.stopPropagation();e.preventDefault();}if(S3.drag||S3.p1)s3Paint();},true);
  window.addEventListener('mouseup',function(e){if(!S3.mode||!S3.drag||e.button!==0)return;e.stopPropagation();e.preventDefault();var s=S3.drag.s,c=[e.clientX,e.clientY];S3.drag=null;
    if(Math.hypot(c[0]-s[0],c[1]-s[1])>8){s3Finish(s,c);return;}
    if(!S3.p1){S3.p1=s;s3Box();s3Paint();return;}if(Math.hypot(c[0]-S3.p1[0],c[1]-S3.p1[1])<8)return;s3Finish(S3.p1,c);},true);
  document.addEventListener('keydown',function(e){if(S3.mode&&e.key==='Escape')s3Off();});
  /* kamera berubah di antara klik 1 dan 2 -> titik 1 dibatalkan (posisi layar tidak lagi sama) */
  var hook=function(){if(gd.on&&gd._ev&&!gd._ev._s3Hook){gd._ev._s3Hook=1;gd.on('plotly_relayout',function(ev){if(S3.mode&&S3.p1&&ev&&ev['scene.camera']){S3.p1=null;s3Box();s3Msg('Kamera berubah: titik 1 dibatalkan, gambar lagi.');s3Paint();}});}};setInterval(hook,800);})();
(function(){var b2=$('btn2d');if(!b2||$('btnSec3'))return;var b=document.createElement('button');b.className='tb';b.id='btnSec3';b.title='Sayatan garis bebas: tarik garis di mana saja pada jendela 3D';
  b.innerHTML='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="6" cy="6" r="2.5"/><circle cx="6" cy="18" r="2.5"/><path d="M8 7.5L20 16M8 16.5L20 8"/></svg>Sayatan 3D';b.onclick=s3Open;b2.parentNode.insertBefore(b,b2.nextSibling);})();

/* ================= GC-Ex Drillhole: bilah sayatan mengambang (Maju / Mundur) =================
   Tombol Maju / Mundur dipindah dari bilah atas ke bilah kecil di area tampilan. Bilah hanya muncul saat
   sayatan dipakai: Penampang 2D aktif, atau di 3D "Potong data (hanya dalam slab)" / "Tampilkan bidang potong" dicentang.
   Isi: Mundur, posisi (bisa diketik), Maju, tebal slab, tombol 2D/3D. PageUp / PageDown = Maju / Mundur. */
(function(){if(window.SLB||typeof stepPos!=='function'||typeof updatePlot!=='function')return;
  var $=function(i){return document.getElementById(i);},bar=null;
  var on=function(){try{return !!(VIEW2D||($('sliceClip')&&$('sliceClip').checked)||($('showPlane')&&$('showPlane').checked));}catch(e){return false;}};
  var axis=function(){var m='H';try{m=secGeom().m;}catch(e){}return m==='H'?'Elevasi':'offset';};
  function build(){var st=$('stage');if(!st||bar)return;bar=document.createElement('div');bar.id='slabBar';bar.setAttribute('role','toolbar');
    bar.innerHTML='<span class="sbt" title="Sayatan aktif">Sayatan</span>'+
      '<button type="button" data-d="-1" title="Mundur sejauh tebal slab (PageDown)">&#9664; Mundur</button>'+
      '<label class="sbp" title="Posisi sayatan; ketik angka lalu Enter"><input type="number" step="any" id="sbPos"><span id="sbAx"></span></label>'+
      '<button type="button" data-d="1" title="Maju sejauh tebal slab (PageUp)">Maju &#9654;</button>'+
      '<label class="sbk" title="Tebal slab = jarak satu langkah">Tebal <input type="number" step="any" min="0.1" id="sbThick"> m</label>'+
      '<button type="button" id="sb2d" title="Ganti Penampang 2D / tampilan 3D">2D</button>';
    st.appendChild(bar);
    bar.addEventListener('click',function(e){var b=e.target.closest('button');if(!b)return;if(b.id==='sb2d'){toggle2D();return;}stepPos(+b.getAttribute('data-d'));});
    $('sbPos').addEventListener('change',function(){var p=$('pos'),v=parseFloat(this.value);if(!p||!isFinite(v))return;p.value=Math.min(+p.max,Math.max(+p.min,v));updatePlot();});
    $('sbThick').addEventListener('change',function(){var t=$('thick'),v=parseFloat(this.value);if(!t||!(v>0))return;t.value=v;updatePlot();});
    ['sbPos','sbThick'].forEach(function(k){$(k).addEventListener('keydown',function(e){if(e.key==='Enter'){this.blur();}});});}
  function sync(){if(!bar)build();if(!bar)return;var vis=on();bar.style.display=vis?'flex':'none';if(!vis)return;
    var p=$('pos'),t=$('thick'),a=document.activeElement;if(p&&a!==$('sbPos'))$('sbPos').value=(+p.value||0).toFixed(1);if(t&&a!==$('sbThick'))$('sbThick').value=t.value;
    $('sbAx').textContent='m '+axis();var b=$('sb2d');b.textContent=VIEW2D?'3D':'2D';b.title=VIEW2D?'Kembali ke tampilan 3D':'Buka Penampang 2D dari slab ini';b.classList.toggle('on',!!VIEW2D);}
  var up=updatePlot;updatePlot=function(){var r=up.apply(this,arguments);try{sync();}catch(e){}return r;};
  document.addEventListener('change',function(e){var id=e.target&&e.target.id;if(id==='sliceClip'||id==='showPlane'||id==='sMode'||id==='thick')setTimeout(sync,0);},true);
  var p=$('pos');if(p)p.addEventListener('input',function(){if(bar&&document.activeElement!==$('sbPos'))$('sbPos').value=(+p.value||0).toFixed(1);});
  document.addEventListener('keydown',function(e){if(!on()||e.ctrlKey||e.altKey||e.metaKey)return;var t=e.target,tag=t&&t.tagName;if(tag==='INPUT'||tag==='TEXTAREA'||tag==='SELECT'||(t&&t.isContentEditable))return;
    if(e.key==='PageUp'){e.preventDefault();stepPos(1);}else if(e.key==='PageDown'){e.preventDefault();stepPos(-1);}});
  var css=document.createElement('style');css.id='slabBarCss';css.textContent=
    '#hdStep{display:none!important}'+
    '#slabBar{position:absolute;top:8px;left:50%;transform:translateX(-50%);z-index:6;display:none;align-items:center;gap:4px;padding:4px 6px;background:var(--sf,#fff);color:var(--tx,#1c2733);'+
      'border:1px solid var(--bd,#c9d3de);border-bottom-color:#9eabbc;border-radius:7px;box-shadow:0 3px 0 rgba(16,24,40,.12);font-size:11.5px;white-space:nowrap;pointer-events:auto}'+
    '#slabBar .sbt{font-weight:700;font-size:10.5px;letter-spacing:.05em;text-transform:uppercase;color:var(--mu,#6b7785);padding:0 4px 0 2px}'+
    '#slabBar button{font:inherit;min-height:24px;padding:2px 8px;border-radius:5px;border:1px solid var(--bd,#c9d3de);border-bottom-color:#9eabbc;background:var(--bg,#f4f6f9);color:inherit;cursor:pointer}'+
    '#slabBar button:hover{filter:brightness(1.04)}#slabBar button:active{transform:translateY(1px)}'+
    '#slabBar button.on,#slabBar #sb2d{background:var(--mj,#f0c047);border-color:var(--mjln,#d6a12b);color:var(--mjtx,#1d2b5e);font-weight:700}'+
    '#slabBar input{font:inherit;width:62px;height:22px;padding:0 4px;border:1px solid var(--bd,#c9d3de);border-radius:4px;background:var(--sf,#fff);color:inherit;text-align:right;font-variant-numeric:tabular-nums}'+
    '#slabBar .sbk input{width:44px}#slabBar label{display:inline-flex;align-items:center;gap:4px;color:var(--mu,#6b7785)}#slabBar .sbp{color:inherit}'+
    'body.dark #slabBar{box-shadow:0 3px 0 rgba(0,0,0,.4)}';
  (document.head||document.documentElement).appendChild(css);
  window.SLB={sync:sync,on:on};
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',function(){build();sync();});else{build();sync();}
})();

/* ---------- bilah atas: satu menu "Sayatan" ---------- */
/* ---------- bilah atas: SATU tombol "Slicer" (DH 0.24.56 / BM 0.24.50, contoh dari Leapfrog: dip, dip azimuth, lebar slab, langkah, lokasi) ----------
   Mengganti menu "Sayatan ▾". Popup memuat seluruh kendali sayatan: dip / dip azimuth bebas (mode S di secGeom), preset plan / E-W / N-S,
   lebar slab & langkah terpisah, titik pusat (X Y Z, bisa diambil dari pusat data / pusat pandangan), Mundur / Maju, opsi slab,
   Penampang 2D, Sayatan 3D garis bebas, garis di peta, digitasi, pengaturan lanjutan (panel Sayatan). Panel Properti Sayatan tetap ada. */
(function(){var b2=$('btn2d');if(!b2||$('btnSecM'))return;var b3=$('btnSec3');
  var st=document.createElement('style');st.textContent='#secMenu{position:absolute;z-index:2000;display:none;width:340px;background:var(--sf,#fff);color:var(--tx,#212529);border:1px solid var(--bd,#ced4da);border-radius:10px;box-shadow:0 10px 28px rgba(0,0,0,.2);padding:8px}'+
    '#secMenu .smh{font-size:10.5px;font-weight:700;letter-spacing:.04em;color:var(--mu,#868e96);margin:6px 4px 3px;text-transform:uppercase;display:flex;justify-content:space-between;align-items:center}#secMenu .smh button{height:22px;padding:0 7px;font-size:11px}'+
    '#secMenu button.tb,#secMenu .smi{display:flex;align-items:center;gap:8px;width:100%;justify-content:flex-start;height:32px;margin:2px 0;padding:0 10px;border-radius:7px;font-size:12.5px;text-align:left}'+
    '#secMenu .smi{border:0;background:none;color:inherit;cursor:pointer}#secMenu .smi:hover{background:rgba(0,0,0,.06)}#secMenu button.tb svg{width:16px;height:16px}#secMenu label.ck{display:flex;gap:8px;align-items:center;padding:3px 6px;font-size:12.5px;cursor:pointer;border-radius:6px}#secMenu label.ck:hover{background:rgba(0,0,0,.06)}'+
    '#secMenu .slg{display:grid;grid-template-columns:1fr 1fr;gap:6px 8px;margin:4px 0}#secMenu .slg.c3{grid-template-columns:1fr 1fr 1fr}#secMenu .slf{display:flex;flex-direction:column;gap:2px;font-size:11px;color:var(--mu,#868e96)}#secMenu .slf input,#secMenu .slf select{font:inherit;font-size:12.5px;color:var(--tx,#212529);height:26px;padding:0 6px;border:1px solid var(--bd,#ced4da);border-radius:5px;background:var(--bg,#fff);width:100%;box-sizing:border-box}'+
    '#secMenu .slf input[type=range]{height:18px;padding:0;border:0;background:none}#secMenu .slq{display:flex;gap:4px;flex-wrap:wrap;margin:2px 0 4px}#secMenu .slq button{height:24px;padding:0 8px;font-size:11.5px;border-radius:5px}#secMenu .slq button.on{background:var(--mj,#f0c047);border-color:var(--mjln,#d6a12b);color:var(--mjtx,#1d2b5e);font-weight:700}'+
    '#secMenu .slpos{display:grid;grid-template-columns:auto 1fr auto;gap:6px;align-items:center;margin:6px 0 2px}#secMenu .slpos button{height:28px;padding:0 10px;font-weight:600}#secMenu .slpos .slf input{text-align:center;font-weight:600}'+
    '#secMenu hr{border:0;border-top:1px solid var(--bd,#e3e7ec);margin:6px 0}#btnSecM .sm2d{font-size:10px;font-weight:700;background:var(--pr,#1c3d8f);color:#fff;border-radius:4px;padding:0 4px;margin-left:2px}';document.head.appendChild(st);
  var bt=document.createElement('button');bt.className='tb';bt.id='btnSecM';bt.title='Slicer: potong model dari arah mana saja (dip, dip azimuth, lebar slab, langkah, lokasi), Penampang 2D, Sayatan 3D, digitasi';
  bt.innerHTML='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 20L20 4"/><rect x="3" y="5" width="18" height="14" rx="1" stroke-width="1.6"/></svg>Slicer<span id=secM2d></span>';
  b2.parentNode.insertBefore(bt,b2);var m=document.createElement('div');m.id='secMenu';document.body.appendChild(m);
  var t2=[].slice.call(b2.childNodes).filter(function(n){return n.nodeType===3&&/Penampang/.test(n.textContent);})[0];if(t2)t2.textContent='Penampang (Sayatan) 2D';
  var ck=function(id,t){var e=$(id);if(!e)return '';return '<label class=ck><input type=checkbox '+(e.checked?'checked':'')+' onchange="var e=document.getElementById(\''+id+'\');e.checked=this.checked;e.dispatchEvent(new Event(\'change\',{bubbles:true}));">'+t+'</label>';};
  var head=document.createElement('div');head.innerHTML='<div class=smh><span>Slicer</span><button type=button id=slReset title="Kembali ke plan melalui pusat data">Reset</button></div>';m.appendChild(head);
  var top=document.createElement('div');m.appendChild(top);var mid=document.createElement('div');m.appendChild(mid);m.appendChild(b2);if(b3)m.appendChild(b3);var mx=document.createElement('div');m.appendChild(mx);
  var close=function(){m.style.display='none';};
  var N=function(v,d){return isFinite(v)?(+v).toFixed(d==null?1:d):'';};
  var geom=function(){try{return secGeom();}catch(e){return null;}};
  /* nilai Slicer dari kendali yang ada: mode S memakai slDip / slAz; mode P (garis) dip dari dipS, azimuth dari garis; H = plan */
  var cur=function(){var md=$('sMode').value,g=geom()||{},dip,az;
    if(md==='S'){dip=parseFloat($('slDip').value)||0;az=parseFloat($('slAz').value)||0;}
    else if(md==='P'||md==='A'){dip=parseFloat($('dipS').value)||90;az=((g.az||0)+90+360)%360;}
    else{dip=0;az=0;}
    var c=g.c||[0,0,0],cx=isFinite(parseFloat($('slX').value))?parseFloat($('slX').value):c[0]+offX,cy=isFinite(parseFloat($('slY').value))?parseFloat($('slY').value):c[1]+offY,cz=isFinite(parseFloat($('slZ').value))?parseFloat($('slZ').value):(md==='H'||(md==='S'&&dip<0.5)?+$('pos').value:c[2]);
    return{md:md,dip:dip,az:az,x:cx,y:cy,z:cz,w:parseFloat($('thick').value)||5,step:parseFloat($('slStep').value)||parseFloat($('thick').value)||5,pos:+$('pos').value};};
  /* pindah ke mode S dengan pusat yang masuk akal: pusat garis (mode P) / pusat data */
  var keS=function(){var md=$('sMode').value;if(md==='S')return;var g=geom();
    if(!isFinite(parseFloat($('slX').value))){var c=g&&g.c||[CX,CY,(G.z0+G.z1)/2];if(g&&g.m==='P'&&g.seg){c=[c[0]+g.u[0]*g.seg/2,c[1]+g.u[1]*g.seg/2,c[2]];}if(g&&g.m==='H'){c=[CX,CY,+$('pos').value];}
      $('slX').value=N(c[0]+offX,1);$('slY').value=N(c[1]+offY,1);$('slZ').value=N(c[2],1);}
    if(md==='P'||md==='A'){$('slDip').value=parseFloat($('dipS').value)||90;$('slAz').value=N(((g&&g.az||0)+90+360)%360,1);}
    $('sMode').value='S';modeChanged();};
  var setDipAz=function(dip,az){keS();var was=(parseFloat($('slDip').value)||0)<0.5;if(dip!=null)$('slDip').value=Math.min(90,Math.max(0,dip));if(az!=null)$('slAz').value=((az%360)+360)%360;
    var now=(parseFloat($('slDip').value)||0)<0.5;if(was!==now)updRange(true);else if(!now){/* bidang miring: tetap lewat pusat */}
    updatePlot();try{camFollowHook();}catch(e){}render();};
  var setPusat=function(x,y,z){if(x!=null)$('slX').value=N(x,1);if(y!=null)$('slY').value=N(y,1);if(z!=null)$('slZ').value=N(z,1);keS();var g=geom();if(g&&g.m==='H'&&isFinite(parseFloat($('slZ').value)))$('pos').value=parseFloat($('slZ').value);else $('pos').value=0;updatePlot();render();};
  var pusatPandangan=function(){try{var gd=$('plotDiv'),L=gd&&gd._fullLayout,sc=L&&L.scene,cam=sc&&sc.camera;if(cam&&cam.center&&sc._scene){var S=sc._scene,ds=S.dataScale,b=S.glplot?S.glplot.bounds:null;
        /* pusat kamera dalam koordinat ternormalisasi -> koordinat data */
        var c=cam.center,ctr=[(sc.xaxis.range[0]+sc.xaxis.range[1])/2,(sc.yaxis.range[0]+sc.yaxis.range[1])/2,(sc.zaxis.range[0]+sc.zaxis.range[1])/2],rng=[sc.xaxis.range[1]-sc.xaxis.range[0],sc.yaxis.range[1]-sc.yaxis.range[0],sc.zaxis.range[1]-sc.zaxis.range[0]],ar=sc.aspectratio;
        return[ctr[0]+c.x*rng[0]/(2*ar.x)+offX,ctr[1]+c.y*rng[1]/(2*ar.y)+offY,ctr[2]+c.z*rng[2]/(2*ar.z)];}}catch(e){}return null;};
  var render=function(){var v=cur(),isS=v.md==='S',isP=v.md==='P',plan=v.dip<0.5,g=geom()||{};
    top.innerHTML='<div class=slg><div class=slf><span>Dip (&deg;) &middot; 0 = plan, 90 = tegak</span><input type=range id=slQd min=0 max=90 step=0.5 value="'+v.dip+'"><input type=number id=slQdn step=any min=0 max=90 value="'+N(v.dip,1)+'"></div>'+
      '<div class=slf><span>Dip azimuth (&deg;)'+(isP?' &middot; dari garis':'')+'</span><input type=number id=slQa step=any value="'+N(v.az,1)+'" '+(isP?'disabled':'')+'><div class=slq><button type=button data-az=0>U</button><button type=button data-az=90>T</button><button type=button data-az=180>S</button><button type=button data-az=270>B</button></div></div></div>'+
      '<div class=slq><button type=button data-pre=plan class="'+(plan&&!isP?'on':'')+'">Plan (horizontal)</button><button type=button data-pre=ew class="'+(!plan&&isS&&Math.abs(((v.az%180)+180)%180-0)<0.3&&v.dip>=89.5?'on':'')+'">Tegak E&ndash;W</button><button type=button data-pre=ns class="'+(!plan&&isS&&Math.abs(((v.az%180)+180)%180-90)<0.3&&v.dip>=89.5?'on':'')+'">Tegak N&ndash;S</button><button type=button data-pre=line class="'+(isP?'on':'')+'">Garis di peta&hellip;</button></div>'+
      '<div class="slg c3"><div class=slf><span>Lebar slab (m)</span><input type=number id=slQw step=any min=0.1 value="'+v.w+'"></div><div class=slf><span>Langkah (m)</span><input type=number id=slQs step=any min=0.1 value="'+v.step+'"></div><div class=slf><span>Posisi &middot; '+(plan||g.m==='H'?'elevasi':'offset dari pusat')+'</span><input type=number id=slQp step=any value="'+N(v.pos,1)+'"></div></div>'+
      '<div class=slf><span>Pusat bidang (E, N, RL) <small>&middot; dipakai bila dip &gt; 0</small></span><div class="slg c3" style="margin:0"><input type=number id=slQx step=any placeholder=E value="'+N(v.x,1)+'"><input type=number id=slQy step=any placeholder=N value="'+N(v.y,1)+'"><input type=number id=slQz step=any placeholder=RL value="'+N(v.z,1)+'"></div></div>'+
      '<div class=slq><button type=button data-ps=data>Pusat data</button><button type=button data-ps=view>Pusat pandangan</button></div>'+
      '<div class=slpos><button type=button data-d=-1 title="Mundur satu langkah (PageDown)">&#9664; Mundur</button><div class=slf><input type=number id=slQp2 step=any value="'+N(v.pos,1)+'"></div><button type=button data-d=1 title="Maju satu langkah (PageUp)">Maju &#9654;</button></div>';
    mid.innerHTML='<hr>'+ck('sliceClip','Potong data (hanya di dalam slab)')+ck('showPlane','Tampilkan bidang potong')+ck('showProf','Profil topo / pit pada sayatan')+'<hr>';
    mx.innerHTML='<button class=smi data-a=dig>&#9998; Digitasi string di penampang</button><button class=smi data-a=set>&#9881; Pengaturan lanjutan (panel Sayatan)&hellip;</button>';};
  var ubah=function(e){var t=e.target,id=t.id;if(!id)return;
    if(id==='slQd'||id==='slQdn'){var d=Math.min(90,Math.max(0,parseFloat(t.value)||0));if(id==='slQd'&&e.type==='input'){$('slQdn').value=N(d,1);keS();var was=(parseFloat($('slDip').value)||0)<0.5;$('slDip').value=d;if(was!==(d<0.5))updRange(true);dDraft();return;}setDipAz(d,null);}
    else if(id==='slQa')setDipAz(null,parseFloat(t.value)||0);
    else if(id==='slQw'){var w=parseFloat(t.value);if(w>0){$('thick').value=w;updatePlot();}}
    else if(id==='slQs'){var sv=parseFloat(t.value);if(sv>0)$('slStep').value=sv;}
    else if(id==='slQp'||id==='slQp2'){var p=$('pos'),pv=parseFloat(t.value);if(isFinite(pv)){p.value=Math.min(+p.max,Math.max(+p.min,pv));updatePlot();render();}}
    else if(id==='slQx'||id==='slQy'||id==='slQz'){setPusat(parseFloat($('slQx').value),parseFloat($('slQy').value),parseFloat($('slQz').value));}};
  top.addEventListener('change',ubah);top.addEventListener('input',function(e){if(e.target.id==='slQd')ubah(e);});
  top.addEventListener('click',function(e){var b=e.target.closest('button');if(!b)return;
    if(b.dataset.d){stepPos(+b.dataset.d);setTimeout(render,60);return;}
    if(b.dataset.az!=null){setDipAz(Math.max(parseFloat($('slQdn').value)||0,90),+b.dataset.az);return;}
    if(b.dataset.ps==='data'){setPusat(CX+offX,CY+offY,(G.z0+G.z1)/2);return;}
    if(b.dataset.ps==='view'){var c=pusatPandangan();if(c)setPusat(c[0],c[1],c[2]);else alert('Pusat pandangan hanya tersedia di tampilan 3D.');return;}
    var pre=b.dataset.pre;if(pre==='plan')setDipAz(0,null);else if(pre==='ew')setDipAz(90,0);else if(pre==='ns')setDipAz(90,90);else if(pre==='line'){close();$('sMode').value='P';modeChanged();if(typeof drawOpen==='function'&&!lineGet())setTimeout(drawOpen,50);}});
  head.addEventListener('click',function(e){if(e.target.id==='slReset'){$('slDip').value=0;$('slAz').value=0;$('slX').value='';$('slY').value='';$('slZ').value='';$('slStep').value='';$('sMode').value='S';modeChanged();render();}});
  mx.addEventListener('click',function(e){var b=e.target.closest('button[data-a]');if(!b)return;close();if(b.dataset.a==='set'){uiTab('Slice');}else{uiTab('Dig');}});
  bt.addEventListener('click',function(e){e.stopPropagation();if(m.style.display==='block'){close();return;}render();var r=bt.getBoundingClientRect();m.style.display='block';m.style.top=(r.bottom+6+window.scrollY)+'px';m.style.left=(Math.max(8,Math.min(innerWidth-350,r.left))+window.scrollX)+'px';});
  [b2,b3].forEach(function(b){if(b)b.addEventListener('click',function(){setTimeout(close,0);});});
  document.addEventListener('mousedown',function(e){if(m.style.display==='block'&&!m.contains(e.target)&&e.target!==bt&&!bt.contains(e.target))close();});
  document.addEventListener('keydown',function(e){if(e.key==='Escape')close();});
  var sync=function(){var s=$('secM2d');if(s)s.innerHTML=window.VIEW2D?' <span class=sm2d>2D</span>':'';bt.classList.toggle('on',!!window.VIEW2D);if(m.style.display==='block')render();};
  var _t=toggle2D;toggle2D=function(){var r=_t.apply(this,arguments);sync();return r;};
  var _sp=stepPos;stepPos=function(){var r=_sp.apply(this,arguments);if(m.style.display==='block')setTimeout(render,80);return r;};
  window.SLICER={render:render,open:function(){bt.click();},close:close,set:setDipAz,pusat:setPusat};sync();})();
