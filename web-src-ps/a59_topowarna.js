/* a59: WARNA & SHADING TOPOGRAFI (pemilik 24 Nov: "warna topografi bisa diatur gak? shading sudah diterapkan belum?").
   Dulu: warna elevasi tetap 4 tingkat hijau→krem + pencahayaan Phong datar (tanpa hillshade).
   Kini di Tampilan → Kamera & tampilan 3D → "Warna topografi":
   - skema: Elevasi alami (bawaan) · Spektrum elevasi · Tanah · Abu-abu · Satu warna (pemilih warna)
   - Hillshade: arah matahari (azimut, bawaan 315° = barat laut), tinggi matahari, kekuatan — dipanggang ke warna titik,
     sehingga lereng & teras tetap jelas dari sudut pandang mana pun (juga di tampilan Plan)
   - Garis kontur: tampil / sembunyi + warna
   Pilihan diingat (localStorage psTopoCol) dan berlaku untuk semua topografi. */
const TPC={sk:'alami',one:'#b7c49a',hs:true,az:315,alt:45,k:0.6,kon:true,kc:'#5a4630'};
try{Object.assign(TPC,JSON.parse(localStorage.getItem('psTopoCol')||'{}'));}catch(_){}
function tpcSave(){try{localStorage.setItem('psTopoCol',JSON.stringify(TPC));}catch(_){}}
const TPC_SK={alami:[[.62,.70,.52],[.72,.78,.58],[.84,.82,.66],[.93,.91,.84]],
 spektrum:[[.17,.40,.75],[.20,.66,.45],[.93,.84,.30],[.86,.33,.22]],
 tanah:[[.55,.45,.33],[.68,.57,.42],[.80,.71,.56],[.92,.87,.77]],
 abu:[[.45,.47,.50],[.60,.62,.64],[.76,.77,.78],[.92,.92,.92]]};
function tpcHex(h){const c=new THREE.Color(h);return [c.r,c.g,c.b];}
/* warnai ulang mesh topografi yang sudah dibangun tpBuild */
function tpcPaint(s){if(!s||!s.mesh)return;const g=s.mesh.geometry,P=g.attributes.position,C=g.attributes.color;if(!P||!C)return;const n=P.count;
 let z0=1e18,z1=-1e18;for(let i=0;i<n;i++){const z=P.getY(i);if(z<z0)z0=z;if(z>z1)z1=z;}const zr=Math.max(z1-z0,1e-6),R3=TPC.sk==='satu'?null:(TPC_SK[TPC.sk]||TPC_SK.alami),one=tpcHex(TPC.one);
 let N=null;if(TPC.hs){if(!g.attributes.normal)g.computeVertexNormals();N=g.attributes.normal;}
 const az=TPC.az*Math.PI/180,al=TPC.alt*Math.PI/180,sx=Math.cos(al)*Math.sin(az),sy=Math.sin(al),sz=-Math.cos(al)*Math.cos(az),k=Math.max(0,Math.min(1,TPC.k)),vx=(W&&W.scale&&W.scale.y)||1;
 for(let i=0;i<n;i++){let c;if(R3){const t=(P.getY(i)-z0)/zr*3,a=Math.min(Math.floor(t),2),f=t-a;c=[0,1,2].map(j=>R3[a][j]+(R3[a+1][j]-R3[a][j])*f);}else c=one.slice();
  if(N){let nx=N.getX(i),ny=N.getY(i)/vx,nz=N.getZ(i);const L=Math.hypot(nx,ny,nz)||1;if(ny<0){nx=-nx;ny=-ny;nz=-nz;}const d=Math.max(0,(nx*sx+ny*sy+nz*sz)/L),sh=0.3+0.75*d;const m=(1-k+k*sh)*(1-0.12*k);c=c.map(v=>Math.min(1,v*m));}
  C.setXYZ(i,c[0],c[1],c[2]);}
 C.needsUpdate=true;
 /* dengan hillshade, cahaya arah dari adegan dilemahkan supaya tidak dobel */try{s.mesh.material.flatShading=!TPC.hs;s.mesh.material.shininess=TPC.hs?1:8;s.mesh.material.specular.set(TPC.hs?0x000000:0x111111);s.mesh.material.needsUpdate=true;}catch(_){}
 try{s.g.children.forEach(o=>{if(o.isLineSegments){o.visible=TPC.kon;o.material.color.set(TPC.kc);}});}catch(_){}}
{const _b=tpBuild;tpBuild=function(s){const r=_b.apply(this,arguments);try{tpcPaint(s);}catch(e){console.warn('warna topo',e);}return r;};}
function tpcAll(){try{TP.forEach(s=>tpcPaint(s));}catch(_){}}
/* panel */
(function(){const host=document.querySelector('#vw2 .flb');if(!host)return;const d=document.createElement('details');d.id='tpcw';d.open=false;
 d.innerHTML='<summary style="cursor:pointer;font-weight:600;margin-top:6px">🎨 Warna topografi</summary>'+
 '<div class="fl">Skema <select id="tpcsk"><option value="alami">Elevasi alami</option><option value="spektrum">Spektrum elevasi</option><option value="tanah">Tanah</option><option value="abu">Abu-abu</option><option value="satu">Satu warna</option></select> <input id="tpcone" type="color" style="width:34px;height:22px;padding:0;border:0;vertical-align:middle"></div>'+
 '<div id="tpcbar" style="height:8px;border-radius:4px;margin:2px 0 6px"></div>'+
 '<label><input type="checkbox" id="tpchs"> Hillshade (bayangan lereng)</label>'+
 '<div class="fl" id="tpchr">Arah matahari <input id="tpcaz" type="range" min="0" max="359" step="15" style="width:90px"><b id="tpcazv"></b></div>'+
 '<div class="fl" id="tpchr2">Tinggi matahari <input id="tpcal" type="range" min="15" max="75" step="5" style="width:90px"><b id="tpcalv"></b></div>'+
 '<div class="fl" id="tpchr3">Kekuatan <input id="tpck" type="range" min="0.1" max="1" step="0.05" style="width:90px"><b id="tpckv"></b></div>'+
 '<label><input type="checkbox" id="tpckon"> Garis kontur</label> <input id="tpckc" type="color" style="width:34px;height:22px;padding:0;border:0;vertical-align:middle">'+
 '<div style="margin-top:4px"><button id="tpcdef" title="Kembali ke warna & shading bawaan">Bawaan</button></div>';
 host.appendChild(d);
 const dir=a=>['U','TL','T','TG','S','BD','B','BL'][Math.round(a/45)%8];
 const ui=()=>{$('tpcsk').value=TPC.sk;$('tpcone').value=TPC.one;$('tpcone').style.display=TPC.sk==='satu'?'':'none';$('tpchs').checked=TPC.hs;$('tpcaz').value=TPC.az;$('tpcal').value=TPC.alt;$('tpck').value=TPC.k;
  $('tpcazv').textContent=' '+TPC.az+'° ('+dir(TPC.az)+')';$('tpcalv').textContent=' '+TPC.alt+'°';$('tpckv').textContent=' '+Math.round(TPC.k*100)+'%';['tpchr','tpchr2','tpchr3'].forEach(id=>$(id).style.opacity=TPC.hs?1:.4);
  $('tpckon').checked=TPC.kon;$('tpckc').value=TPC.kc;
  const R3=TPC.sk==='satu'?[tpcHex(TPC.one),tpcHex(TPC.one)]:TPC_SK[TPC.sk];$('tpcbar').style.background='linear-gradient(90deg,'+R3.map(c=>'rgb('+c.map(v=>Math.round(v*255)).join(',')+')').join(',')+')';$('tpcbar').title='rendah → tinggi';};
 let t=0;const go=()=>{tpcSave();ui();clearTimeout(t);t=setTimeout(tpcAll,60);};
 $('tpcsk').onchange=()=>{TPC.sk=$('tpcsk').value;go();};$('tpcone').oninput=()=>{TPC.one=$('tpcone').value;go();};$('tpchs').onchange=()=>{TPC.hs=$('tpchs').checked;go();};
 $('tpcaz').oninput=()=>{TPC.az=+$('tpcaz').value;go();};$('tpcal').oninput=()=>{TPC.alt=+$('tpcal').value;go();};$('tpck').oninput=()=>{TPC.k=+$('tpck').value;go();};
 $('tpckon').onchange=()=>{TPC.kon=$('tpckon').checked;go();};$('tpckc').oninput=()=>{TPC.kc=$('tpckc').value;go();};
 $('tpcdef').onclick=()=>{Object.assign(TPC,{sk:'alami',one:'#b7c49a',hs:true,az:315,alt:45,k:0.6,kon:true,kc:'#5a4630'});go();};
 ui();})();
/* eksagerasi vertikal mengubah kemiringan tampak → hillshade dihitung ulang */
try{const v=$('vx');if(v)v.addEventListener('input',()=>{clearTimeout(TPC._t);TPC._t=setTimeout(tpcAll,120);});}catch(_){}
tpcAll();
try{window.__PS3.tpc={get:()=>JSON.parse(JSON.stringify(TPC)),set:o=>{Object.assign(TPC,o);tpcSave();tpcAll();},col:(i,j)=>{const s=TP[i];const C=s.mesh.geometry.attributes.color;return [C.getX(j),C.getY(j),C.getZ(j)];}};}catch(_){}
