/* a23: Lantai bertingkat + jalan tengah (pit lereng / sidehill).
   Sumbu jalan digambar dari sisi atas lereng ke bawah. Jalan turun dengan kemiringan rencana; tiap turun 1 bench (H) jalan butuh H/g m.
   Pit dari batas topo (atas → bawah) dipotong melintang: lantai RL z_k terbentang sepanjang P = H/g + landasan di sepanjang sumbu,
   dinding melintang (muka bench) turun ke lantai berikutnya, dan badan jalan ditinggalkan sebagai taji batuan di tengah pit. */
const TER={on:false,line:null,z0:NaN,land:20,info:''};
function terP(){const p=prmAt(TER.z0-0.01),g=Math.max(0.01,(+$('rG').value||10)/100),W=+$('rW').value||12,H=p.H,d=p.a,Lr=H/g,P=Lr+Math.max(0,TER.land);return {g,W,H,d,Lr,P,A:p.A};}
function terArc(L){const S=[0];for(let i=1;i<L.length;i++)S.push(S[i-1]+Math.hypot(L[i][0]-L[i-1][0],L[i][1]-L[i-1][1]));return S;}
function terAt(L,S,s){if(s<=0){const a=L[0],b=L[1],l=S[1]||1;return [a[0]+(b[0]-a[0])*s/l,a[1]+(b[1]-a[1])*s/l];}const n=L.length-1;if(s>=S[n]){const a=L[n-1],b=L[n],l=(S[n]-S[n-1])||1,e=s-S[n];return [b[0]+(b[0]-a[0])*e/l,b[1]+(b[1]-a[1])*e/l];}let i=1;while(S[i]<s)i++;const t=(s-S[i-1])/((S[i]-S[i-1])||1);return [L[i-1][0]+(L[i][0]-L[i-1][0])*t,L[i-1][1]+(L[i][1]-L[i-1][1])*t];}
function terSub(s0,s1){/* potongan sumbu (diperpanjang 3 km di kedua ujung) dari s0 ke s1 */const L=TER.line,S=terArc(L),E=3000;s0=Math.max(-E,s0);s1=Math.min(S[S.length-1]+E,s1);if(s1-s0<0.5)return null;const o=[terAt(L,S,s0)];for(let i=0;i<L.length;i++)if(S[i]>s0&&S[i]<s1)o.push(L[i]);o.push(terAt(L,S,s1));return o;}
function terBand(s0,s1,half,butt){const L=terSub(s0,s1);if(!L)return [];const co=new ClipperLib.ClipperOffset(2,0.1*CS);co.AddPath(toC(L),JT.jtRound,butt?ET.etOpenButt:ET.etOpenRound);const out=new ClipperLib.Paths();co.Execute(out,half*CS);return cClean(out);}
/* daerah hilir: titik yang proyeksinya pada sumbu ≥ s (lebar 3 km) */
function terDown(s){TER.rc=TER.rc||new Map();const k=Math.round(s*10);if(TER.rc.has(k))return TER.rc.get(k);const S=terArc(TER.line),R=terBand(s,S[S.length-1]+3000,3000,true);TER.rc.set(k,R);return R;}
function terZroad(s){const p=terP();if(s<=0)return TER.z0;const k=Math.floor(s/p.P),r=s-k*p.P;return TER.z0-k*p.H-Math.min(p.H,r*p.g);}
/* badan jalan di atas RL z (taji batuan) + kaki lerengnya */
function terSpur(z){const p=terP(),U=[];const k=Math.floor((TER.z0-z)/p.H-1e-6);if(k<0)return [];const s0=k*p.P,s1=s0+p.Lr;for(let s=s0;s<s1-0.01;s+=5){const e=Math.min(s1,s+5),zr=terZroad(s+0.01);if(zr<=z+0.05)continue;const h=zr-z,w=p.W/2+projDist(h,prmAt(z+0.01))+0.5;const B=terBand(s,e+1,w,true);if(B.length)U.push(...B);}
 return U.length?cBool(U,[],ClipperLib.ClipType.ctUnion):[];}
function terClip(P,z,kind){if(!P||!P.length||!TER.on||!TER.line||!isFinite(TER.z0)||z>TER.z0+0.01)return P;const p=terP(),n=(TER.z0-z)/p.H;
 const s=kind==='T'?(n-1)*p.P+p.d:n*p.P;/* crest RL z mulai di s; toe RL z mulai setelah muka melintang */let Q=n<0.999&&kind==='T'?P:cInter(P,terDown(s));
 const SP=terSpur(z);if(SP.length&&Q.length)Q=cDiff(Q,SP);return cClean(Q);}
{const _g=genDown;genDown=function(C0,zc0,o){if(!TER.on||!TER.line)return _g(C0,zc0,o);const c0=o&&o.clamp;const H0=prmAt(zc0).H;if(isFinite(TER.z0u)){TER.z0=zc0-Math.max(0,Math.round((zc0-TER.z0u)/H0))*H0;}const o2=Object.assign({},o,{noAdopt:true,clamp:(P,z,k)=>terClip(c0?c0(P,z,k):P,z,k),ramps:[]});TER.rc=null;return _g(C0,zc0,o2);};}
/* jalan: tepi kiri/kanan sepanjang sumbu, RL mengikuti terZroad */
function terRoad(){if(!TER.on||!TER.line)return [];const p=terP(),L=TER.line,S=terArc(L),Ls=S[S.length-1],out=[];const sEnd=Math.min(Ls,Math.ceil((TER.z0-(+$('pZmin').value||-1e9))/p.H)*p.P);
 const pts=[];for(let s=0;s<=sEnd+1e-6;s+=2){const a=terAt(L,S,Math.min(s,sEnd)),b=terAt(L,S,Math.min(s,sEnd)+0.5),dx=b[0]-a[0],dy=b[1]-a[1],l=Math.hypot(dx,dy)||1,nx=-dy/l,ny=dx/l,z=terZroad(Math.min(s,sEnd));pts.push([a,nx,ny,z]);/* jalan keluar ke permukaan di sisi bawah lereng: berhenti di titik jalan = tanah */const t=topoZ(a[0],a[1]);if(s>p.P*0.5&&isFinite(t)&&z>=t-0.05){pts[pts.length-1][3]=t;break;}}
 if(pts.length<2)return [];const eI=pts.map(q=>[q[0][0]+q[1]*p.W/2,q[0][1]+q[2]*p.W/2,q[3]]),eO=pts.map(q=>[q[0][0]-q[1]*p.W/2,q[0][1]-q[2]*p.W/2,q[3]]);return [{t:'road',z:TER.z0,pts:eI,ter:true},{t:'road',z:TER.z0,pts:eO,ter:true}];}
{const _b=benchStrings;benchStrings=function(B,floor){const S=_b(B,floor);try{if(TER.on&&TER.line&&MODE!=='edit'){for(const r of terRoad())S.push(r);}}catch(e){console.warn('terRoad',e);}return S;};}
{const _r=runNew;runNew=function(){if(!TER.on)return _r.apply(this,arguments);const on=$('rOn').checked;$('rOn').checked=false;try{return _r.apply(this,arguments);}finally{$('rOn').checked=on;try{const e=$('res');if(e&&TER.info)e.insertAdjacentHTML('afterbegin','<div class="hint">'+TER.info+'</div>');}catch(_){}}};}
/* ---------- jendela ---------- */
function terWin(){let w=$('terw');if(w)return w;const host=$('mw').parentNode;w=document.createElement('div');w.id='terw';w.className='flw win edw';
 w.innerHTML='<div class="flh"><b><span class="cr">Desain baru &#8250; </span>Lantai bertingkat + jalan tengah</b><span class="sp"></span><button class="x">&#10005;</button></div><div class="flb">'+
 '<div class="hint">Untuk pit di lereng: jalan lurus di tengah pit dari atas ke bawah, lantai turun bertingkat mengikuti jalan, badan jalan menjadi taji batuan. Pakai bersama <b>Bentuk awal dari batas topo</b> (langkah 1, atas → bawah). Tinggi bench, sudut muka (langkah 2), lebar &amp; kemiringan jalan (langkah 3) dipakai.</div>'+
 '<div class="fl"><b>1.</b>&nbsp;<button id="terdig">&#9998; Gambar sumbu jalan</button><span class="hint">&nbsp;klik dari sisi atas lereng ke bawah, klik ganda = selesai</span></div><div id="terli" class="hint">Belum ada sumbu.</div>'+
 '<div class="fl"><b>2.</b>&nbsp;RL lantai teratas <input id="terz0" type="number" step="any" style="width:70px" placeholder="otomatis"><span class="u">m</span>&nbsp; landasan <input id="terld" type="number" value="20" style="width:52px"><span class="u">m</span></div>'+
 '<div class="fl"><b>3.</b>&nbsp;<label><input type="checkbox" id="teron"> aktifkan</label>&nbsp;<button id="tergo" class="pri">&#9654; Buat pit</button></div><div id="terinf"></div></div>';
 host.appendChild(w);w.querySelector('.x').onclick=()=>winShow(w,false);try{dockInit();}catch(_){}
 $('terdig').onclick=()=>{if(!TP.length){alert('Impor topografi dulu.');return;}digStart('line',pts=>{terSet(pts);});const m=$('dgmsg');if(m)m.innerHTML='<b>Sumbu jalan tengah</b> — klik dari ujung atas lereng ke ujung bawah, klik ganda / Enter = selesai.';};
 $('terz0').onchange=()=>{terZ0();terInfo();};$('terld').onchange=()=>{TER.land=+$('terld').value||0;terInfo();};$('teron').onchange=()=>{TER.on=$('teron').checked;terInfo();};
 $('tergo').onclick=()=>{try{if(!TER.line)throw new Error('Gambar sumbu jalan dulu.');TER.on=true;$('teron').checked=true;terZ0();runNew();terInfo();}catch(e){alert(e.message);}};return w;}
function terZ0(){const v=$('terz0')?$('terz0').value:'';if(v!==''&&isFinite(+v)){TER.z0=+v;TER.z0u=+v;return;}if(!TER.line)return;const a=TER.line[0],t=topoZ(a[0],a[1]),H=prmAt(t).H||5;TER.z0=isFinite(t)?Math.floor((t-H*0.5)/H)*H:NaN;TER.z0u=TER.z0;}
function terSet(pts){if(!pts||pts.length<2){alert('Sumbu perlu ≥ 2 titik.');return;}TER.line=pts.map(p=>[p[0],p[1]]);TER.rc=null;terZ0();terDraw();terInfo();}
function terInfo(){const e=$('terinf'),li=$('terli');if(!e)return;if(!TER.line){li.textContent='Belum ada sumbu.';e.innerHTML='';return;}const p=terP(),S=terArc(TER.line),L=S[S.length-1],zb=+$('pZmin').value;const nz=Math.floor(L/p.P),zEnd=TER.z0-(nz+ (L-nz*p.P>=p.Lr?1:0))*p.H;
 li.innerHTML='Sumbu: '+TER.line.length+' titik · panjang '+f1(L)+' m · RL topo di awal '+f1(topoZ(TER.line[0][0],TER.line[0][1]));
 TER.info='Lantai bertingkat + jalan tengah: lantai teratas RL '+f1(TER.z0)+', tiap '+f1(p.P)+' m sepanjang sumbu lantai turun '+f1(p.H)+' m (jalan '+f1(p.Lr)+' m pada '+f1(p.g*100)+'% + landasan '+f1(TER.land)+' m).';
 e.innerHTML='<div class="hint">'+TER.info+' Sumbu sepanjang '+f1(L)+' m cukup sampai RL ±'+f1(zEnd)+(isFinite(zb)&&zb<zEnd-0.01?' — <span class="warn">RL bawah '+f1(zb)+' tidak tercapai; perpanjang sumbu ±'+f1((zEnd-zb)/p.H*p.P)+' m atau naikkan RL bawah.</span>':'')+'.</div>'+(TER.on?'<span class="ok">&#10003; aktif — "Buat pit" memakai lantai bertingkat.</span>':'<span class="hint">Belum aktif.</span>');}
function terDraw(){if(!G.ter){G.ter=new THREE.Group();W.add(G.ter);}clr(G.ter);if(!TER.line)return;const P=densify(TER.line.map(p=>[p[0],p[1],0]),3).map(p=>{const z=topoZ(p[0],p[1]);return [p[0],p[1],(isFinite(z)?z:TER.z0)+2];});const o=lineObj(P,'#e8590c',false,{depthTest:false});o.renderOrder=9;G.ter.add(o);}
function terOpen(){const w=terWin();winShow(w,true);terInfo();}
{const _m=dsMenu;dsMenu=function(){const a=_m();const k=a.findIndex(x=>x&&x.t&&/Bandingkan ramp di luar/.test(x.t));a.splice(k>=0?k+1:a.length,0,{t:'Lantai bertingkat + jalan tengah…',ic:'&#9776;',fn:terOpen});return a;};}
window.__PS3=window.__PS3||{};window.__PS3.ter={set:(pts,z0,land)=>{terOpen();if(z0!==undefined&&z0!==null)$('terz0').value=z0;if(land!==undefined)$('terld').value=land;TER.land=+$('terld').value||0;terSet(pts);},on:v=>{TER.on=!!v;$('teron').checked=!!v;terInfo();},go:()=>$('tergo').click(),st:()=>({on:TER.on,z0:TER.z0,p:terP(),info:TER.info})};

{const _j=joinRoads;joinRoads=function(B){if(TER.on&&TER.line)return [];return _j.apply(this,arguments);};}
