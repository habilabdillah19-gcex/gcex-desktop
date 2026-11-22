/* a49: UKUR — satu tombol kecil (pojok kanan atas 3D) untuk mengukur jarak, sudut dan arah; berlaku di 3D dan di penampang Sayatan (2D).
   3D: klik dua titik di permukaan (topografi / pit) → jarak datar, jarak miring, beda RL, sudut lereng (° dan %), arah (azimut & bearing).
   Sayatan: klik dua titik di penampang → sama, arah mengikuti azimut sayatan. Klik ketiga = mulai lagi, Esc = selesai. Memutar 3D tetap bisa (seret). */
const UK={on:false,p:[],dn:null,raf:0};
function ukFmt(n,d){return n.toLocaleString('id-ID',{minimumFractionDigits:d===undefined?1:d,maximumFractionDigits:d===undefined?1:d});}
function ukBear(az){az=((az%360)+360)%360;return az<=90?'N '+ukFmt(az)+'° E':az<=180?'S '+ukFmt(180-az)+'° E':az<=270?'S '+ukFmt(az-180)+'° W':'N '+ukFmt(360-az)+'° W';}
function ukText(a,b){const dx=b[0]-a[0],dy=b[1]-a[1],dz=b[2]-a[2],h=Math.hypot(dx,dy),s=Math.hypot(h,dz),an=Math.atan2(Math.abs(dz),h)*180/Math.PI,az=((Math.atan2(dx,dy)*180/Math.PI)+360)%360;
 return {h,s,dz,an,az,html:'Jarak datar <b>'+ukFmt(h)+' m</b> · miring <b>'+ukFmt(s)+' m</b> · ΔRL <b>'+(dz>0?'+':'')+ukFmt(dz)+' m</b> · sudut <b>'+ukFmt(an)+'°</b>'+(h>0.01?' ('+ukFmt(Math.abs(dz)/h*100)+'%)':'')+' · arah <b>'+ukFmt(az)+'°</b> ('+ukBear(az)+')',short:ukFmt(s)+' m · '+ukFmt(an)+'° · az '+ukFmt(az,0)+'°'};}
function ukDraw(tmp){if(!G.uk){G.uk=new THREE.Group();W.add(G.uk);}clr(G.uk);const P=UK.p.slice();if(P.length===1&&tmp)P.push(tmp);const r=$('ukres');
 if(!UK.on){if(r)r.style.display='none';return;}
 for(const p of P){const v=lineObj([[p[0],p[1],p[2]-6],[p[0],p[1],p[2]+6]],'#d6336c',false,{depthTest:false});v.renderOrder=9;G.uk.add(v);}
 if(P.length===2){const o=lineObj(P,'#d6336c',false,{depthTest:false});o.renderOrder=9;G.uk.add(o);const t=ukText(P[0],P[1]);try{const sp=sprite(t.short,'#a61e4d',0.026,V((P[0][0]+P[1][0])/2,(P[0][1]+P[1][1])/2,(P[0][2]+P[1][2])/2+3));sp.renderOrder=10;if(sp.material)sp.material.depthTest=false;G.uk.add(sp);}catch(_){}
  r.innerHTML=t.html+(tmp?'':' <a id="ukcl" title="Hapus ukuran">hapus</a>');}
 else r.innerHTML=P.length?'Klik titik kedua…':'<b>Ukur</b> — klik dua titik di 3D atau di penampang Sayatan. Esc = selesai.';r.style.display='block';const c=$('ukcl');if(c)c.onclick=()=>{UK.p=[];ukDraw();};}
function ukToggle(on){UK.on=on===undefined?!UK.on:!!on;UK.p=[];const b=$('ukb');if(b)b.classList.toggle('on',UK.on);try{SY2.msOn=UK.on;SY2.ms=[];const s=$('sayms');if(s)s.classList.toggle('on',UK.on);$('saycv').style.cursor=UK.on?'copy':'crosshair';if($('sayw').style.display==='flex')sayDraw();}catch(_){}
 try{if(UK.on){if(SAY.pick)sayPickToggle(false);}cv.style.cursor=UK.on?'crosshair':'';}catch(_){}ukDraw();}
(function(){const st=document.createElement('style');st.textContent='#ukb{position:fixed;z-index:9;width:28px;height:28px;padding:0;border:1px solid #c9c2b4;border-radius:4px;background:rgba(255,255,255,.95);cursor:pointer;font-size:15px;line-height:26px;text-align:center;box-shadow:0 1px 5px rgba(0,0,0,.15)}#ukb:hover{border-color:#2B5F9E}#ukb.on{background:#d6336c;border-color:#d6336c;color:#fff}#ukres{position:fixed;z-index:9;background:rgba(255,255,255,.96);border:1px solid #D3CDC1;border-left:3px solid #d6336c;border-radius:4px;padding:4px 9px;font:11.5px/1.5 system-ui,Segoe UI,Arial,sans-serif;color:#1C2733;box-shadow:0 2px 8px rgba(0,0,0,.12);display:none;max-width:60vw}#ukres b{color:#a61e4d}#ukres a{color:#2B5F9E;cursor:pointer;text-decoration:underline;margin-left:4px}';document.head.appendChild(st);
 const b=document.createElement('button');b.id='ukb';b.innerHTML='&#128208;';b.title='Ukur jarak, sudut & arah — klik dua titik di 3D atau di penampang Sayatan (Esc = selesai)';document.body.appendChild(b);const r=document.createElement('div');r.id='ukres';document.body.appendChild(r);b.onclick=()=>ukToggle();
 const place=()=>{try{const c=$('cv').getBoundingClientRect();b.style.left=(c.right-38)+'px';b.style.top=(c.top+8)+'px';r.style.right=(innerWidth-c.right+8)+'px';r.style.top=(c.top+42)+'px';b.style.display=c.width>80?'block':'none';}catch(_){}};place();setInterval(place,400);
 try{const s=$('sayms');if(s)s.onclick=()=>ukToggle();}catch(_){}
 const dom=R.domElement;
 dom.addEventListener('pointerdown',e=>{UK.dn=UK.on&&e.button===0?[e.clientX,e.clientY]:null;},true);
 dom.addEventListener('pointerup',e=>{if(!UK.on||!UK.dn)return;const d=Math.hypot(e.clientX-UK.dn[0],e.clientY-UK.dn[1]);UK.dn=null;if(d>4)return;let p=null;try{p=sayHit(e);}catch(_){}if(!p)return;if(UK.p.length>=2)UK.p=[];UK.p.push([p[0],p[1],p[2]]);ukDraw();},true);
 dom.addEventListener('pointermove',e=>{if(!UK.on||UK.p.length!==1||UK.raf)return;UK.raf=requestAnimationFrame(()=>{UK.raf=0;let p=null;try{p=sayHit(e);}catch(_){}if(p&&UK.p.length===1)ukDraw([p[0],p[1],p[2]]);});},true);
 dom.addEventListener('click',e=>{if(UK.on){e.stopImmediatePropagation();}},true);
 window.addEventListener('keydown',e=>{if(e.key==='Escape'&&UK.on)ukToggle(false);});
})();
try{window.__PS3.uk={S:UK,toggle:on=>ukToggle(on),set:(a,b)=>{UK.on=true;UK.p=[a,b];$('ukb').classList.add('on');ukDraw();return ukText(a,b);}};}catch(_){}
