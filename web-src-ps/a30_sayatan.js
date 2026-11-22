/* a30: SAYATAN (penampang 2D) — meniru alat Slicing Ore Works.
   Menu atas "✎ Sayatan": tekan-tarik-lepas di jendela 3D (bebas arah) → garis sayatan A→B; jendela Penampang 2D
   menampilkan overlay profil semua permukaan: tiap lapisan topografi / asbuilt (termasuk hasil Trim Topo), pit final,
   staging, pit lama & hasil edit, plus titik potong string crest / toe / jalan. Maju / Mundur menggeser sayatan tegak lurus.
   Gulir = zoom, seret = geser, klik ganda = pas, ⛶ = layar penuh. Esc = batal menarik. */
const SAY={pick:false,a:null,b:null,drag:null,off:0,step:10,ve:1,hide:{},view:null,hover:null};
const SAYC=['#2f9e44','#868e96','#e8590c','#1971c2','#ae3ec9','#c92a2a','#0b7285','#5f3dc4','#d9480f'];
(function(){const st=document.createElement('style');st.textContent=
`#sayw{position:fixed;left:360px;top:90px;width:min(900px,calc(100vw - 420px));height:420px;min-width:420px;min-height:260px;background:#fff;border:1px solid #9fb0cc;border-radius:7px;box-shadow:0 8px 28px rgba(20,32,58,.28);z-index:1200;display:none;flex-direction:column;resize:both;overflow:hidden;font:12px system-ui,Segoe UI,Arial,sans-serif}
#sayw.full{left:8px!important;top:70px!important;width:calc(100vw - 16px)!important;height:calc(100vh - 110px)!important;resize:none}
#sayh{display:flex;align-items:center;gap:6px;padding:5px 8px;background:linear-gradient(#2a3f6c,#1b2a4e);color:#fff;cursor:move;user-select:none}
#sayh b{font-size:12.5px}#sayh button{background:#344d80;color:#fff;border:0;border-radius:4px;padding:2px 8px;cursor:pointer;font:12px system-ui}#sayh button:hover{background:#4a66a3}
#sayb{display:flex;flex-wrap:wrap;align-items:center;gap:6px 10px;padding:5px 8px;border-bottom:1px solid #dde3ee;background:#f5f7fb}
#sayb input[type=number]{width:58px}#sayb button{padding:2px 8px}
#saylg{display:flex;flex-wrap:wrap;gap:4px 12px;padding:4px 8px;border-bottom:1px solid #eef1f6}#saylg label{display:flex;align-items:center;gap:4px;cursor:pointer}#saylg i{display:inline-block;width:18px;height:3px;border-radius:2px}
#saycv{flex:1;width:100%;min-height:120px;display:block;cursor:crosshair;background:#fbfcfe}
#sayinf{padding:3px 8px;color:#495057;border-top:1px solid #eef1f6;min-height:18px}
.mbb.say-on{background:#ff9800!important;color:#fff!important}`;document.head.appendChild(st);
 const w=document.createElement('div');w.id='sayw';w.innerHTML=
 '<div id="sayh"><b>&#9998; Sayatan — Penampang 2D</b><span id="saytt" style="opacity:.85"></span><span style="flex:1"></span><button id="sayre" title="Tarik garis sayatan baru di 3D">&#9998; Tarik ulang</button><button id="sayfs" title="Layar penuh / kembali">&#9974;</button><button id="sayx" title="Tutup">&#10005;</button></div>'+
 '<div id="sayb"><button id="saym" title="Geser sayatan tegak lurus ke kiri garis A→B">&#9664; Mundur</button><button id="sayp" title="Geser sayatan tegak lurus ke kanan garis A→B">Maju &#9654;</button>langkah <input id="says" type="number" step="any" value="10"> m'+
 '<span>geser <b id="sayo">0</b> m</span><button id="sayrv" title="Tukar ujung A ↔ B">&#8644; Balik</button>eksagerasi vertikal <input id="sayve" type="number" step="any" value="1" min="0.1">&times;'+
 '<button id="sayfit" title="Pas ke data (klik ganda di gambar juga bisa)">&#9635; Pas</button><button id="saypng">&#8681; PNG</button><button id="saycsv">&#8681; CSV</button></div>'+
 '<div id="saylg"></div><canvas id="saycv"></canvas><div id="sayinf">Gulir = zoom · seret = geser · klik ganda = pas.</div>';
 document.body.appendChild(w);
 const mb=document.querySelector('#mbar #lytg')||document.querySelector('#mbar .mbb[data-w=bw]');const b=document.createElement('button');b.className='mbb';b.id='mbsay';b.title='Sayatan: tekan-tarik-lepas di jendela 3D untuk membuat penampang 2D (overlay topografi & desain)';b.innerHTML='&#9998; Sayatan';
 if(mb)mb.insertAdjacentElement(mb.id==='lytg'?'afterend':'beforebegin',b);else document.getElementById('mbar').appendChild(b);b.onclick=()=>sayPickToggle();
 /* geser jendela */let mv=null;$('sayh').addEventListener('mousedown',e=>{if(/BUTTON|INPUT/.test(e.target.tagName)||w.classList.contains('full'))return;mv=[e.clientX,e.clientY,w.offsetLeft,w.offsetTop];e.preventDefault();});
 window.addEventListener('mousemove',e=>{if(!mv)return;w.style.left=Math.max(0,mv[2]+e.clientX-mv[0])+'px';w.style.top=Math.max(0,mv[3]+e.clientY-mv[1])+'px';});window.addEventListener('mouseup',()=>{mv=null;});
 $('sayx').onclick=()=>{w.style.display='none';sayLine3D();};$('sayfs').onclick=()=>{w.classList.toggle('full');sayDraw();};$('sayre').onclick=()=>sayPickToggle(true);
 $('saym').onclick=()=>{SAY.off-=SAY.step;sayUpd();};$('sayp').onclick=()=>{SAY.off+=SAY.step;sayUpd();};$('says').onchange=()=>{const v=+$('says').value;if(v>0)SAY.step=v;};
 $('sayrv').onclick=()=>{if(!SAY.a)return;const t=SAY.a;SAY.a=SAY.b;SAY.b=t;SAY.off=-SAY.off;SAY.view=null;sayUpd();};$('sayve').onchange=()=>{const v=+$('sayve').value;SAY.ve=v>0?v:1;SAY.view=null;sayDraw();};
 $('sayfit').onclick=()=>{SAY.view=null;sayDraw();};$('saypng').onclick=()=>{$('saycv').toBlob(bl=>dl(bl,'sayatan.png','image/png'));};$('saycsv').onclick=sayCsv;
 if(typeof ResizeObserver!=='undefined')new ResizeObserver(()=>{if(w.style.display==='flex')sayDraw();}).observe(w);
 /* interaksi kanvas */const cv2=$('saycv');let pan=null;
 cv2.addEventListener('wheel',e=>{e.preventDefault();const V=SAY.view;if(!V)return;const r=cv2.getBoundingClientRect(),mx=e.clientX-r.left,my=e.clientY-r.top,k=e.deltaY>0?1.2:1/1.2,[s,z]=sayInv(mx,my);V.s0=s-(s-V.s0)*k;V.s1=s+(V.s1-s)*k;V.z0=z-(z-V.z0)*k;V.z1=z+(V.z1-z)*k;sayDraw();},{passive:false});
 cv2.addEventListener('mousedown',e=>{if(!SAY.view)return;pan=[e.clientX,e.clientY,Object.assign({},SAY.view)];});
 window.addEventListener('mousemove',e=>{const r=cv2.getBoundingClientRect();if(pan){const V=SAY.view,P=pan[2],sx=(P.s1-P.s0)/SAY.pw,sz=(P.z1-P.z0)/SAY.ph;V.s0=P.s0-(e.clientX-pan[0])*sx;V.s1=P.s1-(e.clientX-pan[0])*sx;V.z0=P.z0+(e.clientY-pan[1])*sz;V.z1=P.z1+(e.clientY-pan[1])*sz;sayDraw();return;}
  if(w.style.display!=='flex'||!SAY.view)return;const mx=e.clientX-r.left,my=e.clientY-r.top;if(mx<0||my<0||mx>r.width||my>r.height)return;const [s,z]=sayInv(mx,my),L=sayGeo();if(!L)return;const E=L.a[0]+L.ux*s,N=L.a[1]+L.uy*s;
  const tz=topoZ(E,N);$('sayinf').textContent='Jarak '+f1(s)+' m · RL '+f1(z)+' · E '+f1(E)+' · N '+f1(N)+(isFinite(tz)?' · topografi RL '+f1(tz):'');});
 window.addEventListener('mouseup',()=>{pan=null;});cv2.addEventListener('dblclick',()=>{SAY.view=null;sayDraw();});
 window.addEventListener('keydown',e=>{if(e.key==='Escape'&&SAY.pick)sayPickToggle(false);});
 /* tarik garis di 3D */let dn=null;
 cv.addEventListener('pointerdown',e=>{if(!SAY.pick||e.button!==0||e.target!==R.domElement)return;const p=sayHit(e);if(!p)return;dn=p;SAY.drag=[p,p];CT.enabled=false;e.stopImmediatePropagation();e.preventDefault();},true);
 cv.addEventListener('pointermove',e=>{if(!SAY.pick||!dn)return;const p=sayHit(e,dn[2]);if(p){SAY.drag=[dn,p];sayLine3D(SAY.drag);}},true);
 cv.addEventListener('pointerup',e=>{if(!SAY.pick||!dn)return;const p=sayHit(e,dn[2])||dn;const a=dn;dn=null;CT.enabled=true;if(Math.hypot(p[0]-a[0],p[1]-a[1])<2){sayLine3D();return;}sayPickToggle(false);saySet(a,p);},true);
})();
function sayHit(e,z){let p=null;try{p=hitTopo(e);}catch(_){}if(!p){try{p=hitPlane(e,isFinite(z)?z:(CT&&CT.target?toW(CT.target)[2]:0));}catch(_){}}return p;}
function sayPickToggle(on){SAY.pick=on===undefined?!SAY.pick:on;$('mbsay').classList.toggle('say-on',SAY.pick);cv.style.cursor=SAY.pick?'crosshair':'';try{CT.enabled=true;}catch(_){}
 if(SAY.pick){try{if(typeof toast==='function')toast('Sayatan: tekan, tarik, lalu lepas di jendela 3D (Esc = batal).');}catch(_){}const m=$('dgmsg');if(m)m.innerHTML='<b>Sayatan</b> — tekan, tarik, lalu lepas di jendela 3D. Esc = batal.';}}
function saySet(a,b){SAY.a=[a[0],a[1]];SAY.b=[b[0],b[1]];SAY.off=0;SAY.view=null;$('sayw').style.display='flex';sayUpd();}
function sayGeo(){if(!SAY.a)return null;const dx=SAY.b[0]-SAY.a[0],dy=SAY.b[1]-SAY.a[1],L=Math.hypot(dx,dy);if(L<1)return null;const ux=dx/L,uy=dy/L,nx=uy,ny=-ux;/* kanan A→B */return {a:[SAY.a[0]+nx*SAY.off,SAY.a[1]+ny*SAY.off],b:[SAY.b[0]+nx*SAY.off,SAY.b[1]+ny*SAY.off],L,ux,uy,az:((Math.atan2(ux,uy)*180/Math.PI)+360)%360};}
function sayUpd(){$('sayo').textContent=f1(SAY.off);const L=sayGeo();if(L)$('saytt').textContent='  A→B '+f1(L.L)+' m · azimut '+f1(L.az)+'°';sayLine3D();sayDraw();}
function sayLine3D(tmp){if(!G.say){G.say=new THREE.Group();W.add(G.say);}clr(G.say);let a,b;if(tmp){a=tmp[0];b=tmp[1];}else{if($('sayw').style.display!=='flex')return;const L=sayGeo();if(!L)return;a=L.a;b=L.b;}
 const P=densify([[a[0],a[1],0],[b[0],b[1],0]],4).map(q=>{const t=topoZ(q[0],q[1]);return [q[0],q[1],(isFinite(t)?t:(a[2]||0))+1.5];});const o=lineObj(P,'#ff6f00',false,{depthTest:false});o.renderOrder=8;G.say.add(o);
 for(const [p,c] of [[P[0],'#ff6f00'],[P[P.length-1],'#1b2a4e']]){const v=lineObj([[p[0],p[1],p[2]-40],[p[0],p[1],p[2]+40]],c,false,{depthTest:false});v.renderOrder=8;G.say.add(v);}}
/* daftar permukaan: semua topografi + desain yang ada */
function saySurf(){const o=[];let k=0;for(const t of TP)if(t.G)o.push({id:'tp:'+t.nm,nm:t.nm,G:t.G,col:SAYC[(k++)%2===0?0:1],w:2,topo:true,on:t.on});
 const add=(id,nm,R,col)=>{if(R&&R.tin&&R.tin.G&&!o.some(x=>x.G===R.tin.G))o.push({id,nm,G:R.tin.G,col,w:2.2,R});};
 try{add('res','Pit final (Desain baru)',RES,'#1971c2');}catch(_){}try{add('stg','Staging',STG,'#e8590c');}catch(_){}try{if(ED){add('edo','Pit hasil edit',ED.out,'#ae3ec9');add('edb','Pit lama (sebelum edit)',ED.base,'#868e96');}}catch(_){}return o;}
function sayProfiles(){const L=sayGeo();if(!L)return null;const n=Math.min(1600,Math.max(60,Math.ceil(L.L/1)));const S=saySurf(),out=[];
 for(const s of S){const P=[];for(let i=0;i<=n;i++){const d=L.L*i/n,E=L.a[0]+L.ux*d,N=L.a[1]+L.uy*d;let z=gridZ(s.G,E,N);if(!s.topo&&isFinite(z)){const t=topoZ(E,N);if(isFinite(t)&&z>t+0.05)z=NaN;/* bagian pit di atas tanah = udara */}P.push([d,z]);}out.push(Object.assign({P},s));}
 /* titik potong string desain */const X=[];try{const R=curR();if(R&&R.S)for(const s of R.S){if(!/^(crest|toe|road|floor)$/.test(s.t)||!s.pts)continue;const p=s.pts;for(let i=1;i<p.length;i++){const a=p[i-1],b=p[i],r=sayX(L,a,b);if(r){const z=a[2]+(b[2]-a[2])*r[1],E=L.a[0]+L.ux*r[0],N=L.a[1]+L.uy*r[0],tz=topoZ(E,N);if(!(isFinite(tz)&&z>tz+0.5))X.push({d:r[0],z,t:s.t});}}}}catch(_){}
 return {L,out,X};}
function sayX(L,a,b){const ex=L.b[0]-L.a[0],ey=L.b[1]-L.a[1],fx=b[0]-a[0],fy=b[1]-a[1],den=ex*fy-ey*fx;if(Math.abs(den)<1e-9)return null;const gx=a[0]-L.a[0],gy=a[1]-L.a[1],t=(gx*fy-gy*fx)/den,u=(gx*ey-gy*ex)/den;if(t<0||t>1||u<0||u>1)return null;return [t*L.L,u];}
function sayInv(mx,my){const V=SAY.view;return [V.s0+(mx-SAY.ml)/SAY.pw*(V.s1-V.s0),V.z1-(my-SAY.mt)/SAY.ph*(V.z1-V.z0)];}
function sayDraw(){const w=$('sayw');if(w.style.display!=='flex')return;const D=sayProfiles(),cv2=$('saycv'),r=cv2.getBoundingClientRect(),dpr=window.devicePixelRatio||1;cv2.width=Math.max(10,r.width*dpr);cv2.height=Math.max(10,r.height*dpr);const g=cv2.getContext('2d');g.setTransform(dpr,0,0,dpr,0,0);g.clearRect(0,0,r.width,r.height);
 if(!D){g.fillStyle='#868e96';g.fillText('Tekan "Tarik ulang", lalu tekan-tarik-lepas di jendela 3D.',20,30);return;}
 /* legenda */const lg=$('saylg');lg.innerHTML=D.out.map(s=>'<label><input type="checkbox" data-sy="'+esc(s.id)+'"'+(SAY.hide[s.id]?'':' checked')+'><i style="background:'+s.col+'"></i>'+esc(s.nm)+'</label>').join('')+'<label><input type="checkbox" data-sy="__x"'+(SAY.hide.__x?'':' checked')+'><i style="background:linear-gradient(90deg,#c92a2a 50%,#1971c2 50%)"></i>titik crest / toe / jalan</label>';
 lg.querySelectorAll('[data-sy]').forEach(c=>c.onchange=()=>{SAY.hide[c.dataset.sy]=!c.checked;sayDraw();});
 const ml=58,mr=14,mt=12,mb=30,pw=r.width-ml-mr,ph=r.height-mt-mb;SAY.ml=ml;SAY.mt=mt;SAY.pw=pw;SAY.ph=ph;
 if(!SAY.view){let z0=1e9,z1=-1e9;for(const s of D.out){if(SAY.hide[s.id])continue;for(const p of s.P)if(isFinite(p[1])){z0=Math.min(z0,p[1]);z1=Math.max(z1,p[1]);}}if(!(z1>z0)){z0=0;z1=100;}const pad=(z1-z0)*0.08+2;z0-=pad;z1+=pad;
  /* skala 1:1 × eksagerasi: m per piksel sama di kedua sumbu kecuali dikali VE */let s0=0,s1=D.L.L;const mx=(s1-s0)/pw,mz=(z1-z0)/ph/SAY.ve;if(mz>mx){const c=(s0+s1)/2,h=mz*pw/2;s0=c-h;s1=c+h;}else{const c=(z0+z1)/2,h=mx*SAY.ve*ph/2;z0=c-h;z1=c+h;}SAY.view={s0,s1,z0,z1};}
 const V=SAY.view,X=s=>ml+(s-V.s0)/(V.s1-V.s0)*pw,Y=z=>mt+(V.z1-z)/(V.z1-V.z0)*ph;
 const nice=(span,n)=>{const r0=span/n,p=Math.pow(10,Math.floor(Math.log10(r0))),m=r0/p;return (m<1.5?1:m<3?2:m<7?5:10)*p;};
 g.font='11px system-ui,Arial';g.strokeStyle='#e9edf3';g.fillStyle='#495057';g.lineWidth=1;const ds=nice(V.s1-V.s0,8),dz=nice(V.z1-V.z0,6);
 for(let s=Math.ceil(V.s0/ds)*ds;s<=V.s1;s+=ds){const x=X(s);g.beginPath();g.moveTo(x,mt);g.lineTo(x,mt+ph);g.stroke();g.fillText(f1(s).replace(/\.0$/,''),x-10,mt+ph+14);}
 for(let z=Math.ceil(V.z0/dz)*dz;z<=V.z1;z+=dz){const y=Y(z);g.beginPath();g.moveTo(ml,y);g.lineTo(ml+pw,y);g.stroke();g.fillText('RL '+f1(z).replace(/\.0$/,''),4,y+4);}
 g.fillText('jarak dari A (m) · eksagerasi vertikal '+SAY.ve+'×',ml+pw-230,mt+ph+26);
 g.save();g.beginPath();g.rect(ml,mt,pw,ph);g.clip();
 /* arsir galian di bawah topografi aktif sampai permukaan desain aktif */
 for(const s of D.out){if(SAY.hide[s.id])continue;g.strokeStyle=s.col;g.lineWidth=s.w;g.setLineDash(s.topo&&!s.on?[6,4]:[]);g.beginPath();let pen=false;for(const p of s.P){if(!isFinite(p[1])){pen=false;continue;}const x=X(p[0]),y=Y(p[1]);if(!pen){g.moveTo(x,y);pen=true;}else g.lineTo(x,y);}g.stroke();}
 g.setLineDash([]);if(!SAY.hide.__x)for(const q of D.X){g.fillStyle=q.t==='crest'?'#c92a2a':q.t==='toe'?'#1971c2':q.t==='floor'?'#2f9e44':'#e8590c';g.beginPath();g.arc(X(q.d),Y(q.z),3,0,7);g.fill();}
 g.restore();g.strokeStyle='#adb5bd';g.strokeRect(ml,mt,pw,ph);g.fillStyle='#ff6f00';g.font='bold 12px system-ui';g.fillText('A',X(0)-4,mt+12);g.fillStyle='#1b2a4e';g.fillText('B',X(D.L.L)-4,mt+12);}
function sayCsv(){const D=sayProfiles();if(!D)return;const h=['jarak_m','E','N'].concat(D.out.map(s=>'RL_'+s.nm.replace(/[ ,;]+/g,'_')));const n=D.out[0]?D.out[0].P.length:0,rows=[h.join(',')];
 for(let i=0;i<n;i++){const d=D.out[0].P[i][0],E=D.L.a[0]+D.L.ux*d,N=D.L.a[1]+D.L.uy*d;rows.push([d.toFixed(2),E.toFixed(2),N.toFixed(2)].concat(D.out.map(s=>isFinite(s.P[i][1])?s.P[i][1].toFixed(2):'')).join(','));}dl(rows.join('\n'),'sayatan.csv','text/csv');}
/* hasil baru / topo baru → gambar ulang */
{const _sr=showResult;showResult=function(){const r=_sr.apply(this,arguments);try{if($('sayw').style.display==='flex'){SAY.view=SAY.view;sayLine3D();sayDraw();}}catch(_){}return r;};}
try{window.__PS3=window.__PS3||{};window.__PS3.say={set:(a,b)=>saySet(a,b),prof:()=>{const D=sayProfiles();return D&&{L:D.L.L,n:D.out.map(s=>[s.nm,s.P.filter(p=>isFinite(p[1])).length]),x:D.X.length};},step:v=>{SAY.off+=v;sayUpd();},scr:(E,N,Z)=>{const q=scr(E,N,Z),r=R.domElement.getBoundingClientRect();return [q[0]+r.left,q[1]+r.top];}};}catch(_){}
