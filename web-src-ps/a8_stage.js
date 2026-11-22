let FIN_HITOP=false;
/* ================= Staging bulanan: dibatasi pit final ================= */
function finBuild(S,levels,nm,rg){/* levels: Map(z -> {T:toe/irisan atas, C:crest/irisan bawah}) */const lv=[...levels.entries()].map(([k,v])=>({z:k/100,P:v.T,C:v.C&&v.C.length?v.C:v.T})).sort((a,b)=>a.z-b.z);const foot=footOf(S);const footP=foot.length?cClean(ClipperLib.Clipper.SimplifyPolygons(foot.map(r=>toC(r)),ClipperLib.PolyFillType.pftNonZero)):[];
 FIN={S:S.map(s=>({t:'fin',z:s.z,pts:s.pts})),lv,footP,nm,rg:rg||null,rc:new Map(),zmin:lv.length?lv[0].z:NaN,zmax:lv.length?lv[lv.length-1].z:NaN};
 let h='<b>'+esc(nm)+'</b>: '+lv.length+' level RL ('+f1(FIN.zmin)+' – '+f1(FIN.zmax)+').';if(!lv.length)h='<span class="bad">Tidak ada string bench tertutup di pit final.</span>';if(lv.length)h+=' <a href="#" class="del" id="sfdel">&#128465; Hapus batas</a>';$('sfinfo').innerHTML=h;const dd=$('sfdel');if(dd)dd.onclick=ev=>{ev.preventDefault();if(!confirm('Hapus batas pit final?'))return;FIN=null;STG=null;finDraw();pitRedraw();$('sfinfo').innerHTML='';$('s0st').textContent='';$('res').innerHTML='';};$('s0st').textContent=lv.length?'✓ '+lv.length+' RL':'';
 if(STG)STG=null;finDraw();pitRedraw();}
function addLv(m,z,P,kind){if(!P||!P.length)return;const k=Math.round(z*100);if(!m.has(k))m.set(k,{T:[],C:[]});const v=m.get(k);if(kind!=='C')v.T=v.T.length?cUnion(v.T,P):P;if(kind!=='T')v.C=v.C.length?cUnion(v.C,P):P;}
$('sfuse').onclick=()=>{if(!RES){alert('Belum ada pit final. Buat dulu di tab "Pit final", atau impor file pit final (.str).');return;}const m=new Map();for(const b of RES.B){addLv(m,b.zt,b.toe,'T');addLv(m,b.zc,b.crest,'C');}if(RES.floor)addLv(m,RES.floor.z,RES.floor.P,'C');for(const v of m.values())if(!v.T.length)v.T=v.C;finBuild(RES.S,m,'Hasil tab Pit final');};
function finFromL(L,nm){const S=oldS(L),m=new Map();
  const fl=S.filter(s=>s.flat&&s.pure&&s.closed&&s.area>5);for(const s of fl){const P=cClean(ClipperLib.Clipper.SimplifyPolygons([toC(s.pts)],ClipperLib.PolyFillType.pftNonZero));
   /* string yang memuat string lain di RL sama = toe (kaki bench atas); yang tidak memuat = crest */const inner=fl.some(q=>q!==s&&Math.abs(q.z-s.z)<0.2&&q.area<s.area-5&&inPoly(q.pts[0],s.pts));addLv(m,s.z,P,inner?'T':'');}
  for(const v of m.values()){if(!v.T.length)v.T=v.C;}
  /* permukaan pit final mematuhi string-nya (garis patah), supaya penampang raster yang membatasi staging sejalan dengan string crest/toe/jalan pit final */const tin=tinFrom(L,30,!!window.__FINBRK);tin.G=gridOf(tin,1);finBuild(S,m,nm,tin);}
$('sff').onchange=async e=>{const f=e.target.files[0];e.target.value='';if(!f)return;if(MODE!=='stage')$('mode').querySelector('[data-m="stage"]').click();winShow($('iw'),false);try{const L=await readFileL(f);setO(L[0][0]);finFromL(L,f.name);if(!TP.length)view('sw');}catch(err){alert(f.name+': '+err.message);}};
$('sfsnap').onchange=()=>{if(STG)$('res').innerHTML+='<br><span class="warn">Jarak tangkap diubah — klik Buat staging lagi.</span>';};
function finDraw(){clr(G.fin);if(!FIN||MODE!=='stage')return;/* garis final tembus pandang (terlihat walau di bawah topografi) */for(const s of FIN.S){const o=lineObj(s.pts.map(p=>[p[0],p[1],p[2]+0.05]),COL.fin,false,{transparent:true,opacity:.38,depthTest:false,depthWrite:false});o.renderOrder=2;G.fin.add(o);}}
/* batas final pada RL z: level final tertinggi yang <= z (lebih aman); di atas level teratas = jejak permukaan final */
/* irisan raster permukaan final: area dengan RL final <= z (untuk RL tanpa string tertutup, mis. bench atas yang terpotong topografi) */
/* penyederhanaan Douglas-Peucker untuk ring Clipper (toleransi dalam meter) — dipakai mode kotak agar batas raster tidak bertangga */
function rdpC(r,tol){const n=r.length;if(n<5)return r;const T=tol*CS,T2=T*T;let ia=0,ib=0,bd=-1;for(let i=1;i<n;i++){const d=(r[i].X-r[0].X)**2+(r[i].Y-r[0].Y)**2;if(d>bd){bd=d;ib=i;}}
 const run=(a,b)=>{const pts=[];for(let i=a;;i=(i+1)%n){pts.push(r[i]);if(i===b)break;}const keep=new Uint8Array(pts.length);keep[0]=keep[pts.length-1]=1;const st=[[0,pts.length-1]];while(st.length){const [i0,i1]=st.pop();if(i1-i0<2)continue;const A=pts[i0],B=pts[i1],dx=B.X-A.X,dy=B.Y-A.Y,L2=dx*dx+dy*dy||1;let m=-1,mi=-1;for(let i=i0+1;i<i1;i++){const t=Math.max(0,Math.min(1,((pts[i].X-A.X)*dx+(pts[i].Y-A.Y)*dy)/L2)),ex=pts[i].X-A.X-t*dx,ey=pts[i].Y-A.Y-t*dy,d=ex*ex+ey*ey;if(d>m){m=d;mi=i;}}if(m>T2){keep[mi]=1;st.push([i0,mi],[mi,i1]);}}return pts.filter((q,i)=>keep[i]);};
 const A=run(ia,ib),B=run(ib,ia);return A.slice(0,-1).concat(B.slice(0,-1));}
function rasSec(z){const bx=window.__BOXY?1:0,k=Math.round(z*100)*2+bx;if(FIN.rc.has(k))return FIN.rc.get(k);const Gd=FIN.rg.G,R=[];for(let j=0;j<Gd.ny;j++){let i0=-1;for(let i=0;i<=Gd.nx;i++){const v=i<Gd.nx?Gd.Z[j*Gd.nx+i]:NaN;let ok=v<=z;if(ok&&TP.length){const tz=topoZ(Gd.x0+i*Gd.cell,Gd.y0+j*Gd.cell);if(isFinite(tz)&&v>tz-0.3)ok=false;}if(ok&&i0<0)i0=i;else if(!ok&&i0>=0){const x0=Gd.x0+(i0-0.5)*Gd.cell,x1=Gd.x0+(i-0.5)*Gd.cell,y0=Gd.y0+(j-0.5)*Gd.cell,y1=y0+Gd.cell;R.push(toC([[x0,y0],[x1,y0],[x1,y1],[x0,y1]]));i0=-1;}}}
 let P=R.length?cBool(R,[],ClipperLib.ClipType.ctUnion):[];const k0=CORNER;CORNER='round';P=cOff(cOff(P,2),-2);P=cOff(cOff(P,-2),2);CORNER=k0;P=cClean(ClipperLib.Clipper.CleanPolygons(P,0.15*CS),4);if(bx){/* garis lurus, digeser masuk setengah sel agar tetap di dalam pit final */const k1=CORNER;CORNER='miter';P=cOff(P.map(r=>rdpC(r,Gd.cell)).filter(r=>r.length>=3),-0.5*Gd.cell);CORNER=k1;P=cClean(P,4);}FIN.rc.set(k,P);return P;}
function limAt(z,kind){if(FIN.rg&&(z>FIN.zmax+0.01||!FIN.lv.some(l=>Math.abs(l.z-z)<0.02))){const Lr=rasSec(kind==='C'?z-0.05:z+0.05);if(window.__NOSAND||z>FIN.zmax+0.01)return Lr;
  /* RL di antara dua level string pit final: penampang raster dijepit di antara toe level bawah dan crest level atas pit final.
     Tanpa ini, pada muka final yang curam derau raster membuat garis RL antara menyilang string level di atas / di bawahnya. */
  FIN.rs=FIN.rs||new Map();const k=Math.round(z*100)+kind;if(FIN.rs.has(k))return FIN.rs.get(k);let bl=null,bu=null;for(const l of FIN.lv){if(l.z<z-0.02)bl=l;else if(l.z>z+0.02&&!bu)bu=l;}
  let L=Lr;try{if(bu&&bu.C&&bu.C.length){const q=cInter(L,bu.C);if(q.length)L=q;}if(bl&&bl.P&&bl.P.length)L=cUnion(L,bl.P);}catch(e){L=Lr;}FIN.rs.set(k,L);return L;}let b=null;for(const l of FIN.lv){if(l.z<=z+0.01)b=l;else break;}if(!b)return [];if(z>FIN.zmax+0.01&&FIN.footP.length)return FIN.footP;return kind==='C'&&Math.abs(b.z-z)<0.02?b.C:b.P;}
function finClamp(){if(!FIN||!FIN.lv.length)return null;const d=Math.max(0,+$('sfsnap').value||0);FIN.hits=new Set();
 return (P,z,kind)=>{const L=limAt(z,kind);if(!L.length)return [];const A=cInter(P,L);if(!A.length)return [];let out=A;
  if(d>0){const gap=cDiff(L,A);if(gap.length){const open=cOff(cOff(gap,-d/2),d/2+0.05),thin=open.length?cDiff(gap,open):gap;const Ag=cOff(A,0.3),th=thin.filter(r=>cInter([r],Ag).length);if(th.length){out=cUnion(A,th);FIN.hits.add(Math.round(z*10)/10);}}}
  let a0=0,a1=0;for(const r of P)a0+=cArea(r);for(const r of A)a1+=cArea(r);if(a0-a1>2)FIN.hits.add(Math.round(z*10)/10);return out;};}
function stgInfo(R0){if(!FIN)return '<br><span class="warn">Tanpa batas pit final.</span>';const h=FIN&&FIN.hits&&FIN.hits.size?[...FIN.hits].sort((a,b)=>a-b):[];return '<br>'+(h.length?'Menempel / dipotong pit final pada RL: <b>'+h.join(', ')+'</b>':'Staging seluruhnya di dalam pit final (belum menyentuh dinding final).');}
window.__PS2={lim:(z,k)=>limAt(z,k).map(p=>p.map(q=>[q.X/CS+O[0],q.Y/CS+O[1]])),get STG(){return STG;},get FIN(){return FIN;},chk(){/* luas staging di luar final per string */const o=[];for(const s of STG.S){if(s.t!=='crest'&&s.t!=='toe'&&s.t!=='floor')continue;const L=limAt(s.z,s.t==='toe'?'T':'C');const d=cDiff([toC(s.pts.slice(0,-1))],L);let a=0;for(const r of d)a+=Math.abs(cArea(r));o.push([s.t,s.z,+a.toFixed(2)]);}return o;}};
window.__CL={sec:z=>rasSec(z).map(r=>ringOf(r)),diffRing:(z,ring)=>cDiff(rasSec(z),[toC(ring)]).filter(r=>cArea(r)>0).map(r=>ringOf(r)),simp:(ring,d)=>{const P=ClipperLib.Clipper.CleanPolygons([toC(ring)],d*CS);return P.map(r=>ringOf(r));}};

/* ===== Adopsi jalan pit final oleh staging =====
 Badan jalan final pada bench (z0,z1) dibaca dari raster permukaan final: sel dengan z0 < Z < z1 (bukan berm, bukan
 lantai) dan landai (gradien < 25%; muka lereng ±60° jauh lebih curam). Bila badan jalan itu berjarak < jarak tangkap
 dari staging, jalan final dipakai apa adanya: lantai/crest staging dibentuk mengikuti jalan dan string jalan final ikut. */
function finRoadBand(z0,z1){if(!FIN||!FIN.rg)return [];FIN.rb=FIN.rb||new Map();const k=Math.round(z0*100)+'_'+Math.round(z1*100);if(FIN.rb.has(k))return FIN.rb.get(k);
 const Gd=FIN.rg.G,c=Gd.cell,nx=Gd.nx,Z=Gd.Z,R=[];const at=(i,j)=>(i<0||j<0||i>=nx||j>=Gd.ny)?NaN:Z[j*nx+i];
 for(let j=0;j<Gd.ny;j++){let i0=-1;for(let i=0;i<=nx;i++){let ok=false;if(i<nx){const v=at(i,j);if(v>z0+0.15&&v<z1-0.15){const gx=(at(i+1,j)-at(i-1,j))/(2*c),gy=(at(i,j+1)-at(i,j-1))/(2*c);ok=isFinite(gx)&&isFinite(gy)&&Math.hypot(gx,gy)<0.25;if(ok&&TP.length){const tz=topoZ(Gd.x0+i*c,Gd.y0+j*c);if(isFinite(tz)&&v>tz-0.3)ok=false;}}}
  if(ok&&i0<0)i0=i;else if(!ok&&i0>=0){const x0=Gd.x0+(i0-0.5)*c,x1=Gd.x0+(i-0.5)*c,y0=Gd.y0+(j-0.5)*c;R.push(toC([[x0,y0],[x1,y0],[x1,y0+c],[x0,y0+c]]));i0=-1;}}}
 let U=R.length?cBool(R,[],ClipperLib.ClipType.ctUnion):[];const W=RAMP().W;if(U.length){U=cOff(cOff(U,-Math.min(2,W/4)),Math.min(2,W/4)+c);U=U.filter(r=>cArea(r)>Math.max(40,W*W*0.5));}
 FIN.rb.set(k,U);return U;}
function finRoadAdopt(P,z0,z1,up,prevC){if(!FIN||!FIN.rg)return null;const snap=Math.max(0,+$('sfsnap').value||0);if(!(snap>0)||!P.length)return null;
 const Bd=finRoadBand(z0,z1);if(!Bd.length)return null;const W=RAMP().W,near=cOff(P,snap+W);let C=[];
 for(const r of Bd){if(prevC&&prevC.length&&cInter([r],cOff(prevC,W)).length){/* lanjutan tetap dibatasi area staging */const q2=cInter([r],near).filter(x=>cArea(x)>W*W*0.25);C=C.concat(q2);continue;}const q=cInter([r],near).filter(x=>cArea(x)>W*W*0.25);if(!q.length)continue;/* hanya bila badan jalan memang dekat (bukan sekadar tersentuh pita) */const cont=prevC&&prevC.length&&cInter([r],cOff(prevC,W)).length;/* lanjutan jalan final yang sudah dipakai di bench sebelumnya tetap diikuti */if(cont){C.push(r);continue;}if(!cInter([r],cOff(P,snap)).length)continue;C=C.concat(q);}
 if(!C.length)return null;C=cBool(C,[],ClipperLib.ClipType.ctUnion);
 /* string jalan final pada rentang bench ini, di dalam badan jalan yang diadopsi */const Cr=cOff(C,1.5).filter(r=>cArea(r)>0).map(ringOf),strs=[];
 /* titik sambung (lo/hi/arah) tetap dihitung dari potongan mentah agar logika penyambungan jalan staging tidak berubah */let strsX=null;{for(const s of finRoadStrings()){let cur=[];for(const p of densify(s.pts,1.5)){const ok=p[2]>=z0-0.2&&p[2]<=z1+0.2&&Cr.some(r=>inPoly([p[0],p[1]],r));if(ok)cur.push(p.slice());else{if(cur.length>2)strs.push(cur);cur=[];}}if(cur.length>2)strs.push(cur);}}
 if(!window.__FINRAW){strsX=[];/* potongan string jalan final per bench: ujungnya dipanjangkan sepanjang string aslinya sampai TEPAT di RL batas bench (titik sisipan),
   supaya potongan bench atas & bawah bersambung ujung-ke-ujung dan ujung jalan jatuh pada RL string bench */
  const EXT=12,inz=p=>p[2]>=z0-1e-6&&p[2]<=z1+1e-6,cut=(p,q)=>{const zb=q[2]>z1?z1:z0,t=(zb-p[2])/((q[2]-p[2])||1e-9);return [p[0]+(q[0]-p[0])*t,p[1]+(q[1]-p[1])*t,zb];};
  for(const s of finRoadStrings()){const D=densify(s.pts,1.5),n=D.length,ok=D.map(p=>inz(p)&&Cr.some(r=>inPoly([p[0],p[1]],r)));let i=0;
   while(i<n){if(!ok[i]){i++;continue;}let j=i;while(j+1<n&&ok[j+1])j++;if(j-i>=2){const cur=D.slice(i,j+1).map(p=>p.slice());
     /* ke belakang */for(let k=i-1,e=0;k>=0&&e<EXT;k--,e++){if(inz(D[k])){if(ok[k])break;cur.unshift(D[k].slice());}else{cur.unshift(cut(cur[0],D[k]));break;}}
     /* ke depan */for(let k=j+1,e=0;k<n&&e<EXT;k++,e++){if(inz(D[k])){if(ok[k])break;cur.push(D[k].slice());}else{cur.push(cut(cur[cur.length-1],D[k]));break;}}
     let za=1e9,zb=-1e9;for(const p of cur){za=Math.min(za,p[2]);zb=Math.max(zb,p[2]);}/* potongan datar (landasan) hanya ikut bench di bawah RL-nya, tidak rangkap di dua bench */if(zb-za>0.3||Math.abs(zb-z1)<0.2)strsX.push(cur);}
    i=j+1;}}
  /* badan jalan dari string-nya sendiri (bukan dari raster): pasangan tepi jalan → poligon di antaranya, dilebarkan ke samping setengah proyeksi muka bench.
     Garis toe/crest staging lalu mengikuti tepi jalan final dengan rapi dan melewati ujung potongan jalan. */
  try{const NF=strsX.filter(q=>{let a=1e9,b=-1e9;for(const p of q){a=Math.min(a,p[2]);b=Math.max(b,p[2]);}return b-a>0.3;}),mid=q=>q[q.length>>1],used=new Set(),PL=[],dl=Math.max(0.6,0.5*prmAt(z0+0.01).a);
   for(let x=0;x<NF.length;x++){if(used.has(x))continue;let bj=-1,bd=1e9;for(let y=x+1;y<NF.length;y++){if(used.has(y))continue;const d=Math.hypot(mid(NF[x])[0]-mid(NF[y])[0],mid(NF[x])[1]-mid(NF[y])[1]);if(d<bd&&d>0.3*W&&d<1.8*W&&Math.abs(mid(NF[x])[2]-mid(NF[y])[2])<2){bd=d;bj=y;}}if(bj<0)continue;used.add(x);used.add(bj);
    let A=NF[x],B=NF[bj];if((A[A.length-1][2]-A[0][2])*(B[B.length-1][2]-B[0][2])<0)B=B.slice().reverse();
    const sh=(Q,O)=>{const m=Q.length>>1,a=Q[Math.max(0,m-1)],b=Q[Math.min(Q.length-1,m+1)],l=Math.hypot(b[0]-a[0],b[1]-a[1])||1,nn=[-(b[1]-a[1])/l,(b[0]-a[0])/l],sg=(nn[0]*(Q[m][0]-mid(O)[0])+nn[1]*(Q[m][1]-mid(O)[1]))>=0?1:-1;return Q.map((p,i)=>{if(i===0||i===Q.length-1)return [p[0],p[1]];const u=Q[i-1],v=Q[i+1],ll=Math.hypot(v[0]-u[0],v[1]-u[1])||1;return [p[0]-sg*(v[1]-u[1])/ll*dl,p[1]+sg*(v[0]-u[0])/ll*dl];});};
    PL.push(toC(sh(A,B).concat(sh(B,A).reverse())));}
   if(PL.length&&used.size===NF.length){let Cx=cBool(cClean(ClipperLib.Clipper.SimplifyPolygons(PL,ClipperLib.PolyFillType.pftNonZero)),[],ClipperLib.ClipType.ctUnion);const ar=Q=>Q.reduce((t,r)=>t+Math.abs(cArea(r)),0),a0=ar(C),a1=ar(Cx);if(a1>0.4*a0&&a1<2.5*a0)C=Cx;}}catch(e){console.warn('finRoadAdopt',e);}}
 /* ujung bawah jalan (untuk diteruskan jalan staging) */let lo=null;for(const s of strs)for(const p of [s[0],s[s.length-1]])if(!lo||p[2]<lo[2])lo=p;
 let lo2=null;if(lo){let d=1e9;for(const s of strs){if(s.includes(lo))continue;for(const p of [s[0],s[s.length-1]]){const e=Math.hypot(p[0]-lo[0],p[1]-lo[1]);if(Math.abs(p[2]-lo[2])<1.5&&e<d&&e<2*W){d=e;lo2=p;}}}}
 let dirv=null;if(lo){for(const s of strs){const i=s.indexOf(lo);if(i<0)continue;const j=i===0?Math.min(s.length-1,5):Math.max(0,s.length-6);const q=s[j];const l=Math.hypot(lo[0]-q[0],lo[1]-q[1])||1;dirv=[(lo[0]-q[0])/l,(lo[1]-q[1])/l];}}
 let hi=null;for(const s of strs)for(const p of [s[0],s[s.length-1]])if(!hi||p[2]>hi[2])hi=p;
 /* ujung atas jalan final = puncak potongan yang MIRING (ramp), bukan ujung potongan datar (landasan / garis berm di RL atas).
   Jalan staging harus tiba di puncak ramp; memakai ujung landasan membuat jalan staging tiba di samping ramp yang sudah turun beberapa meter. */
 if(strsX&&strsX.length&&(window.__HITOP===1||FIN_HITOP)){/* dipakai hanya bila sambungan cara biasa terbukti beda tinggi (lihat topoDesign): di kasus lain cara ini bisa lebih buruk */let h2=null;for(const q of strsX){let a=1e9,b=-1e9;for(const p of q){a=Math.min(a,p[2]);b=Math.max(b,p[2]);}if(b-a<0.3)continue;for(const p of [q[0],q[q.length-1]])if(!h2||p[2]>h2[2])h2=p;}if(h2)hi=h2;}
 return {C,strs:strsX&&strsX.length?strsX:strs,lo,lo2,dirv,hi};}
