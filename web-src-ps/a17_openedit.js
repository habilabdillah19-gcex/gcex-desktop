/* a17 — string terbuka datar (bagian bench yang terputus / sudah dihaluskan di Edit Manual) bisa dipakai "Perbarui bench di bawah".
   String terbuka disambungkan kembali ke cincin bench asalnya (RL sama): bagian cincin di antara kedua ujungnya diganti string terbuka itu.
   Bila tidak ada cincin asal (mis. pit impor yang crest-nya terpotong topo), string ditutup dengan garis lurus antar-ujung — bagian penutup
   biasanya berada di udara (di atas topo) sehingga ikut terpotong saat tampil/ekspor.
   Hanya bench & jalan di BAWAH string ini yang dibangun ulang; bench di atasnya tidak diubah. */
function oeFlat(s){if(!s||s.closed||s.pts.length<3)return false;let a=1e9,b=-1e9;for(const p of s.pts){a=Math.min(a,p[2]);b=Math.max(b,p[2]);}return b-a<=0.2;}
function oeZ(s){return s.pts.reduce((t,p)=>t+p[2],0)/s.pts.length;}
/* posisi terdekat pada cincin tertutup R (titik terakhir = titik pertama): {i (ruas), t, d, x, y} */
function oeProj(R,p){let b={i:0,t:0,d:1e18,x:R[0][0],y:R[0][1]};for(let i=0;i<R.length-1;i++){const a=R[i],c=R[i+1],dx=c[0]-a[0],dy=c[1]-a[1],L=dx*dx+dy*dy;let t=L>0?((p[0]-a[0])*dx+(p[1]-a[1])*dy)/L:0;t=Math.max(0,Math.min(1,t));const x=a[0]+dx*t,y=a[1]+dy*t,d=Math.hypot(x-p[0],y-p[1]);if(d<b.d)b={i,t,d,x,y};}return b;}
function oeDistPL(p,P){let d=1e18;for(let i=1;i<P.length;i++)d=Math.min(d,smDist(p,P[i-1],P[i]));return d;}
/* busur maju pada cincin dari posisi u ke v (tanpa ujung) */
function oeArc(R,u,v){const m=R.length-1,out=[];let i=(u.i+1)%m;const end=(v.i+1)%m;let g=0;if(u.i===v.i&&v.t>=u.t)return out;while(g++<=m){out.push(R[i]);if(i===v.i)break;i=(i+1)%m;}return out;}
/* cincin baru = string terbuka O menggantikan busur cincin R yang paling dekat dengannya */
function oeSplice(R,O,z){const a=O[0],b=O[O.length-1],pa=oeProj(R,a),pb=oeProj(R,b);const A1=oeArc(R,pa,pb),A2=oeArc(R,pb,pa);
 const md=A=>A.length?A.reduce((t,p)=>t+oeDistPL(p,O),0)/A.length:0;/* busur yang diganti = yang lebih dekat dengan string terbuka */
 const rep1=md(A1)<=md(A2);let Q;if(rep1)Q=O.map(p=>[p[0],p[1],z]).concat(A2.map(p=>[p[0],p[1],z]));else Q=O.slice().reverse().map(p=>[p[0],p[1],z]).concat(A1.map(p=>[p[0],p[1],z]));
 Q.push(Q[0].slice());return {Q,da:pa.d,db:pb.d};}
/* rangkai potongan terbuka datar RL sama mulai dari string i: sambung ke ujung terdekat (boleh dibalik) bila celah ≤ batas, sampai kembali ke awal */
function oeChain(S,i,z){const G=Math.max(25,2*(RAMP().W||12)),used=[i],P0=S[i].pts.map(p=>[p[0],p[1],z]);let Q=P0.slice(),gap=0;const cand=[];S.forEach((q,j)=>{if(j!==i&&oeFlat(q)&&Math.abs(oeZ(q)-z)<=0.2)cand.push(j);});
 for(let g=0;g<50;g++){const e=Q[Q.length-1],s0=Q[0];const dc=Math.hypot(e[0]-s0[0],e[1]-s0[1]);let bj=-1,bd=G,rev=false;for(const j of cand){if(used.includes(j))continue;const P=S[j].pts,a=P[0],b=P[P.length-1],da=Math.hypot(a[0]-e[0],a[1]-e[1]),db=Math.hypot(b[0]-e[0],b[1]-e[1]);if(da<bd){bd=da;bj=j;rev=false;}if(db<bd){bd=db;bj=j;rev=true;}}
  if(bj<0||(dc<=G&&dc<=bd&&used.length>1))break;used.push(bj);gap=Math.max(gap,bd);const P=S[bj].pts.map(p=>[p[0],p[1],z]);if(rev)P.reverse();Q=Q.concat(P);}
 const e=Q[Q.length-1],s0=Q[0],dc=Math.hypot(e[0]-s0[0],e[1]-s0[1]);const closed=used.length>1&&dc<=G;if(closed){gap=Math.max(gap,dc);Q.push(Q[0].slice());}return {Q,used,closed,gap};}
function oeHost(S,i){const s=S[i],z=oeZ(s),O=s.pts;let best=-1,bs=1e18;
 S.forEach((q,j)=>{if(j===i||!q.closed||!q.flat||Math.abs(q.z-z)>0.2||q.pts.length<4)return;const da=oeProj(q.pts,O[0]).d,db=oeProj(q.pts,O[O.length-1]).d;if(da>1.5||db>1.5)return;
  let m=0;for(const p of O)m+=oeProj(q.pts,p).d;m/=O.length;if(m>4)return;if(m+da+db<bs){bs=m+da+db;best=j;}});return best;}
{const _re=runEdit;runEdit=function(){const S=ED.base.S,i=ED.sel,s=S[i];if(!s||s.closed||!oeFlat(s))return _re();
 const z=oeZ(s),open0=ED.orig,eup=$('eup').checked,h=oeHost(S,i);let host0=null,note,drop=[i];
 if(h>=0){const sp=oeSplice(S[h].pts,s.pts,S[h].z);host0=S[h].pts;S[h].pts=sp.Q;S[h].area=ringArea(sp.Q);ED.sel=h;ED.orig=host0;note='String terbuka disambungkan ke cincin bench RL '+f1(S[h].z)+' (bagian cincin di antara kedua ujungnya diganti).';}
 else{/* rangkai potongan terbuka lain pada RL sama (bench yang terputus jalan / topo) menjadi satu cincin */const ch=oeChain(S,i,z);drop=ch.used;if(ch.closed){const Q=ch.Q;S.push({t:'crest',z,pts:Q,closed:true,flat:true,pure:true,area:ringArea(Q)});ED.sel=S.length-1;ED.orig=Q.map(p=>p.slice());note='String terbuka dirangkai dengan '+(ch.used.length-1)+' potongan lain pada RL '+f1(z)+' menjadi satu cincin bench (celah terbesar '+f1(ch.gap)+' m disambung lurus).';}
 else{const Q=ch.Q;Q.push(Q[0].slice());S.push({t:'crest',z,pts:Q,closed:true,flat:true,pure:true,area:ringArea(Q)});ED.sel=S.length-1;ED.orig=Q.map(p=>p.slice());note='Tidak ada cincin bench asal pada RL '+f1(z)+': '+(ch.used.length>1?'string dirangkai dengan '+(ch.used.length-1)+' potongan lain lalu ':'string ')+'ditutup dengan garis lurus antar-ujung (bagian penutup di atas topo ikut terpotong).';}}
 ED.drop=drop;$('eup').checked=false;let r;
 try{r=_re();}finally{if(h>=0)S[h].pts=host0;else S.pop();if(h>=0)S[h].area=ringArea(host0);ED.sel=i;ED.orig=open0;ED.drop=null;$('eup').checked=eup;}
 try{const e=$('eres');if(e&&e.innerHTML)e.innerHTML='<div class="hint">ℹ '+esc(note)+' Hanya bench &amp; jalan di bawah RL '+f1(z)+' yang dibangun ulang.</div>'+e.innerHTML;}catch(_){}return r;};}
/* pilih string terbuka datar di Edit pit: tampilkan pilihan tipe & petunjuk "Perbarui bench di bawah" */
{const _ec=window.edClick;window.edClick=function(e){const r=_ec.apply(this,arguments);try{if(ED&&ED.sel>=0){const s=ED.base.S[ED.sel];if(s&&!s.closed&&oeFlat(s)){$('etyrow').hidden=false;const el=$('eseli');if(el)el.innerHTML='Terpilih: <b>string terbuka datar</b> · RL '+f1(oeZ(s))+' · '+s.pts.length+' titik<br><span class="hint">Boleh diedit bebas (seret titik) atau lewat Edit Manual (kurangi titik / haluskan). <b>Perbarui bench di bawah</b> memperbarui bench &amp; jalan di bawahnya saja.</span><label style="display:block;margin-top:4px"><input type="checkbox" id="oeloc" checked> Batasi sepanjang string ini (bench di bawah digeser mengikuti perubahan string; di luar panjangnya tidak berubah)</label><span class="hint">Tanpa centang: string disambung ke cincin bench asalnya lalu seluruh bench &amp; jalan di bawah dibangun ulang.</span>';}}}catch(_){}return r;};}
window.__PS3=window.__PS3||{};window.__PS3.oe={pre:()=>OE_PRE.length,flat:oeFlat,host:i=>oeHost(ED.base.S,i),pick:i=>{ED.sel=i;ED.orig=ED.base.S[i].pts.map(p=>p.slice());ED.out=null;}};
/* potongan jalan buntu: ruas jalan pendek (< 15 m) yang mulai di toe bench tetapi berhenti di tengah bench (tidak sampai crest) dan tidak
   dilanjutkan jalan di bench atasnya — sisa ramp yang terpotong batas RL atas area (kasus dua area bottom-up). Dibuang supaya tidak
   menggantung / bersilang. Flag uji: __NOSTUB. */
function roadStubs(B){if(window.__NOSTUB||!B||!B.length)return 0;let n=0;const L=P=>{let s=0;for(let i=1;i<P.length;i++)s+=Math.hypot(P[i][0]-P[i-1][0],P[i][1]-P[i-1][1]);return s;};
 for(let k=0;k<B.length;k++){const b=B[k];if(!b.roads||!b.roads.length)continue;const up=B.find(q=>Math.abs(q.zt-b.zc)<0.05);
  b.roads=b.roads.filter(r=>{if(r.fin||r.landing||!r.in||r.in.length<2)return true;const P=r.in,e=P[P.length-1],s=P[0];if(e[2]>=b.zc-0.5)return true;
   /* lebih panjang dari 15 m: hanya bila benar-benar buntu (tak ada ruas lain di bench ini yang mulai/berakhir dekat ujungnya, ujung tidak di permukaan) */if(L(P)>=15){if(L(P)>=80)return true;const near=b.roads.some(q=>q!==r&&q.in&&q.in.length&&[q.in[0],q.in[q.in.length-1]].some(t=>Math.hypot(t[0]-e[0],t[1]-e[1])<6));if(near)return true;const tz=topoZ(e[0],e[1]);if(isFinite(tz)&&tz<=e[2]+1.5)return true;if(window.__NOSTUB2)return true;
    /* awal ruas: dibuang hanya bila jalan tetap bersambung tanpa ruas ini (ada ruas lain di bench ini yang mulai di titik yang sama), atau tidak ada jalan di bench bawah yang berakhir di situ */const lo=B.find(q=>Math.abs(q.zc-b.zt)<0.05),fromBelow=lo&&(lo.roads||[]).some(q=>q.in&&q.in.length&&Math.hypot(q.in[q.in.length-1][0]-s[0],q.in[q.in.length-1][1]-s[1])<6),sib=b.roads.some(q=>q!==r&&q.in&&q.in.length&&Math.hypot(q.in[0][0]-s[0],q.in[0][1]-s[1])<6);if(fromBelow&&!sib)return true;}
   const cont=up&&(up.roads||[]).some(q=>q.in&&q.in.length&&Math.hypot(q.in[0][0]-e[0],q.in[0][1]-e[1])<4);if(cont)return true;n++;return false;});}
 return n;}
{const _bs2=benchStrings;benchStrings=function(B,floor){try{const n=roadStubs(B);if(n)window.__PS3.stubs=n;}catch(e){console.warn(e);}return _bs2(B,floor);};}
/* ===== Perbarui bench di bawah — TERBATAS sepanjang string terbuka acuan =====
   Perubahan string terbuka (versi lama → versi baru, mis. dihaluskan / dikurangi titiknya) menjadi medan geser; setiap titik bench & jalan di
   BAWAH RL string itu yang "berada di bawah" bagian string tersebut (titik terdekatnya pada cincin RL acuan jatuh pada string itu) digeser
   dengan geseran yang sama — gelombang yang diwarisi dari string atas ikut hilang. Di luar panjang string tidak ada yang berubah; dekat kedua
   ujungnya geseran memudar (transisi). Karena semua string memakai medan geser yang sama, bench & jalan tetap berimpit (tidak menggantung). */
const OE_PRE=[];/* versi string terbuka sebelum diedit di Edit Manual: {z,a,b,pts} — dicocokkan lewat kedua ujung */
function oePreFind(s){const z=oeZ(s),a=s.pts[0],b=s.pts[s.pts.length-1],m=(p,q)=>Math.hypot(p[0]-q[0],p[1]-q[1])<0.6;for(const e of OE_PRE)if(Math.abs(e.z-z)<0.2&&((m(e.a,a)&&m(e.b,b))||(m(e.a,b)&&m(e.b,a))))return m(e.a,a)?e.pts:e.pts.slice().reverse();return null;}
{const _ma=mwApply;mwApply=function(L,label,newSel){try{const S=mwS();for(const i of (MWS.sel||[])){const s=S[i];if(!s||!oeFlat(s))continue;if(oePreFind(s))continue;OE_PRE.push({z:oeZ(s),a:s.pts[0].slice(),b:s.pts[s.pts.length-1].slice(),pts:s.pts.map(p=>p.slice())});if(OE_PRE.length>60)OE_PRE.shift();}}catch(e){console.warn(e);}return _ma(L,label,newSel);};}
function oeNear(P,p){let b={d:1e18,i:0,t:0,x:P[0][0],y:P[0][1]};for(let i=1;i<P.length;i++){const a=P[i-1],c=P[i],dx=c[0]-a[0],dy=c[1]-a[1],L=dx*dx+dy*dy;let t=L>0?((p[0]-a[0])*dx+(p[1]-a[1])*dy)/L:0;t=Math.max(0,Math.min(1,t));const x=a[0]+dx*t,y=a[1]+dy*t,d=Math.hypot(x-p[0],y-p[1]);if(d<b.d)b={d,i,t,x,y};}return b;}
function runEditLocal(){const S=ED.base.S,i=ED.sel,s=S[i],z=oeZ(s),N=s.pts;let O=oePreFind(s);
 if(!O&&ED.orig&&ED.orig.length>1&&ED.orig.some((p,k)=>!N[k]||Math.hypot(p[0]-N[k][0],p[1]-N[k][1])>0.01))O=ED.orig;
 if(!O)throw new Error('String terbuka ini belum diubah. Edit dulu (Edit Manual → Kurangi titik / Haluskan, atau seret titik), lalu klik lagi.');
 /* cincin acuan pada RL ini (untuk menentukan titik mana yang berada di bawah string): string lama dirangkai dengan potongan lain / cincin asal */
 let REF;const h=oeHost(S,i);if(h>=0)REF=oeSplice(S[h].pts,O,z).Q;else{const keep=s.pts;s.pts=O;try{REF=oeChain(S,i,z).Q;}finally{s.pts=keep;}}
 const Od=densify(O.map(p=>[p[0],p[1],z]),1),OS=smArc(Od),LO=OS[OS.length-1],T=Math.max(5,Math.min(25,0.2*LO));
 const DV=Od.map(p=>{const q=oeNear(N,p);return [q.x-p[0],q.y-p[1]];});
 /* medan geser lunak: titik bench bawah memakai rata-rata berbobot (Gaussian jarak) titik-titik cincin acuan terdekat; bagian cincin di luar
    string bergeser nol, ujung string memudar sepanjang T → medan kontinu (tidak sobek di sudut / garis tengah pit) */
 const RD=densify(REF.map(p=>[p[0],p[1],z]),1),RW=RD.map(p=>{const o=oeNear(Od,p);if(o.d>0.3)return null;const sA=OS[o.i-1]+(OS[o.i]-OS[o.i-1])*o.t,w=Math.max(0,Math.min(1,sA/T,(LO-sA)/T));const a=DV[o.i-1],b=DV[o.i];return [w*(a[0]+(b[0]-a[0])*o.t),w*(a[1]+(b[1]-a[1])*o.t)];});
 if(!RW.some(v=>v&&(v[0]||v[1])))throw new Error('Perubahan string terlalu kecil.');let bx0=1e18,bx1=-1e18,by0=1e18,by1=-1e18;for(const p of Od){bx0=Math.min(bx0,p[0]);bx1=Math.max(bx1,p[0]);by0=Math.min(by0,p[1]);by1=Math.max(by1,p[1]);}
 const field=p=>{let dm=1e18;for(const q of RD){const d=(q[0]-p[0])**2+(q[1]-p[1])**2;if(d<dm)dm=d;}dm=Math.sqrt(dm);const sg=Math.max(4,0.35*dm),lim=dm+3*sg;let gx=0,gy=0,gs=0;
  for(let k=0;k<RD.length;k++){const q=RD[k],d=Math.hypot(q[0]-p[0],q[1]-p[1]);if(d>lim)continue;const g=Math.exp(-0.5*((d-dm)/sg)**2);gs+=g;const v=RW[k];if(v){gx+=g*v[0];gy+=g*v[1];}}return gs>0?[gx/gs,gy/gs]:null;};
 let nMv=0,dMax=0;const NS=S.map((q,j)=>{if(j===i)return q;let lo=1e9;for(const p of q.pts)lo=Math.min(lo,p[2]);if(lo>z-0.05)return q;
  const P=densify(q.pts,1);let any=false;const Q=P.map(p=>{if(p[2]>z-0.05)return p;const d=field(p);if(!d||Math.hypot(d[0],d[1])<0.005)return p;any=true;dMax=Math.max(dMax,Math.hypot(d[0],d[1]));return [p[0]+d[0],p[1]+d[1],p[2]];});
  if(!any)return q;nMv++;let R2=rdp3(Q,0.03);if(q.closed)R2[R2.length-1]=R2[0].slice();return Object.assign({},q,{pts:R2,area:q.closed?ringArea(R2):q.area});});
 const all=NS.map(q=>Object.assign({},q,{pts:q.pts.map(p=>p.slice())})),foot=footOf(all.filter(q=>q.t!=='old'||q.closed)),tin=surfOf(all,foot);let zmin=1e9;for(const q of all)for(const p of q.pts)zmin=Math.min(zmin,p[2]);
 ED.out={S:all,foot,tin,zmin,floorS:[],B:[]};ED.out.vol=volOf(ED.out);ED.out.day=dayOf(ED.out);dayDraw(ED.out);layRender();ED.out.kpi={n:0};clr(G.edit);pitRedraw();
 let dv=0;const cell=ED.out.vol.cell,Fp=ED.out.foot;let x0=1e18,x1=-1e18,y0=1e18,y1=-1e18;for(const r of Fp)for(const q of r){x0=Math.min(x0,q[0]);x1=Math.max(x1,q[0]);y0=Math.min(y0,q[1]);y1=Math.max(y1,q[1]);}
 for(let y=y0+cell/2;y<y1;y+=cell)for(let x=x0+cell/2;x<x1;x+=cell){if(!inFoot(Fp,x,y))continue;const zn=gridZ(tin.G,x,y);let zo=gridZ(ED.base.tin.G,x,y);const zt=topoZ(x,y);if(!isFinite(zn))continue;if(!isFinite(zo))zo=isFinite(zt)?zt:zn;const a=Math.min(zo,isFinite(zt)?zt:1e9),b=Math.min(zn,isFinite(zt)?zt:1e9);dv+=(a-b)*cell*cell;}
 let hh='<div class="kpi"><div><b>'+nMv+'</b><span>string di bawah ikut digeser</span></div><div><b>'+(dv>=0?'+':'')+nf(dv)+'</b><span>m³ vs pit lama</span></div><div><b>'+f1(dMax)+' m</b><span>geser maks</span></div></div>';
 hh+='Bench &amp; jalan di bawah RL '+f1(z)+' digeser mengikuti perubahan string terbuka, <b>hanya sepanjang string itu</b> ('+nf(LO)+' m; transisi '+f1(T)+' m di kedua ujung). Bench di atasnya &amp; bagian lain pit tidak berubah.';
 hh+='<br><a href="#" id="eohw">Volume per bench</a> · <a href="#" id="eoxw">Ekspor</a> · <a href="#" id="eagain">Ubah lagi</a> · <a href="#" id="eacc"><b>Terima &amp; edit lanjut</b></a>';$('eres').innerHTML=hh;$('e3st').textContent='✓';
 $('eohw').onclick=ev=>{ev.preventDefault();winShow($('hw'),true);};$('eoxw').onclick=ev=>{ev.preventDefault();winShow($('xw'),true);};$('eagain').onclick=ev=>{ev.preventDefault();ED.out=null;pitRedraw();$('eres').innerHTML='';};$('eacc').onclick=ev=>{ev.preventDefault();OE_PRE.length=0;edAccept();};
 window.__PS3.oeLast={moved:nMv,dMax:+dMax.toFixed(2),dv:Math.round(dv),L:Math.round(LO)};}
{const _re2=runEdit;runEdit=function(){const s=ED&&ED.base.S[ED.sel];if(s&&!s.closed&&oeFlat(s)&&($('oeloc')?$('oeloc').checked:true))return runEditLocal();return _re2();};}
