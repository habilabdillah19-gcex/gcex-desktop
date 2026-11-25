/* a51: EKSPOR STRING TERTUTUP (.str / .dxf) — pemilik 23 Nov 2026: "hasil export tidak membentuk string tertutup".
   Sebab: string bench dipotong di topografi (opsi "Potong string di topografi") lalu tiap potongan ditulis sebagai string terbuka.
   Sekarang (opsi "Tutup string", bawaan menyala):
   • crest / toe / lantai / pit lama: potongan-potongan satu bench disambung kembali; celah di bagian yang "menggantung" di atas topografi
     ditutup MENGIKUTI KONTUR TOPOGRAFI pada RL bench itu (seperti batas galian di Surpac), lalu titik akhir = titik awal.
     String yang memang terbuka di desain (mis. lantai yang keluar ke lereng) ditutup dengan cara yang sama bila ujungnya di topografi,
     selain itu dengan garis lurus.
   • jalan: dua tepi jalan dipasangkan menjadi satu poligon pita (tepi A → tepi B dibalik → kembali ke awal); garis penutup ujung
     jalan yang lama tidak ditulis lagi.
   • potong topografi (daylight): ditulis tertutup; potongan yang kurang dari 3 titik dibuang.
   • DXF: POLYLINE 3D dengan bendera tertutup (70 = 9). */
function xcRing(s){const P=s.pts;if(!P||P.length<3)return false;return s.closed===true||Math.hypot(P[0][0]-P[P.length-1][0],P[0][1]-P[P.length-1][1])<1.0;}
/* kontur topografi pada RL z di sekitar A–B → lintasan A→B (tanpa A dan B) atau null */
function xcTopoPath(A,B,z){const d=Math.hypot(A[0]-B[0],A[1]-B[1]);if(d<0.05)return [];const pad=Math.max(15,0.6*d);
 const x0=Math.min(A[0],B[0])-pad,x1=Math.max(A[0],B[0])+pad,y0=Math.min(A[1],B[1])-pad,y1=Math.max(A[1],B[1])+pad;let st=1;while((x1-x0)/st*(y1-y0)/st>250000)st*=1.5;
 const nx=Math.ceil((x1-x0)/st)+1,ny=Math.ceil((y1-y0)/st)+1,F=new Float64Array(nx*ny);for(let j=0;j<ny;j++)for(let i=0;i<nx;i++){const t=topoZ(x0+i*st,y0+j*st);F[j*nx+i]=isFinite(t)?t-z:NaN;}
 /* marching squares; titik potong diberi kunci rusuk agar segmen tersambung tepat */
 const P=new Map(),adj=new Map(),pt=(k,x,y)=>{if(!P.has(k))P.set(k,[x,y]);},link=(a,b)=>{(adj.get(a)||adj.set(a,[]).get(a)).push(b);(adj.get(b)||adj.set(b,[]).get(b)).push(a);};
 const eH=(i,j)=>{const a=F[j*nx+i],b=F[j*nx+i+1];if(!(a===a)||!(b===b)||(a>0)===(b>0))return null;const k='h'+i+'_'+j,t=a/(a-b);pt(k,x0+(i+t)*st,y0+j*st);return k;};
 const eV=(i,j)=>{const a=F[j*nx+i],b=F[(j+1)*nx+i];if(!(a===a)||!(b===b)||(a>0)===(b>0))return null;const k='v'+i+'_'+j,t=a/(a-b);pt(k,x0+i*st,y0+(j+t)*st);return k;};
 for(let j=0;j<ny-1;j++)for(let i=0;i<nx-1;i++){const E=[eH(i,j),eV(i+1,j),eH(i,j+1),eV(i,j)].filter(Boolean);if(E.length===2)link(E[0],E[1]);else if(E.length===4){link(E[0],E[1]);link(E[2],E[3]);}}
 if(!P.size)return null;
 /* kunci terdekat A dan B */let ka=null,kb=null,da=1e18,db=1e18;for(const [k,p] of P){const a=Math.hypot(p[0]-A[0],p[1]-A[1]),b=Math.hypot(p[0]-B[0],p[1]-B[1]);if(a<da){da=a;ka=k;}if(b<db){db=b;kb=k;}}
 const tol=Math.max(3,2.5*st);if(da>tol||db>tol)return null;
 /* BFS sepanjang kontur dari ka ke kb (lintasan terpendek bila kontur melingkar) */const prev=new Map([[ka,null]]),q=[ka];let found=false;
 for(let h=0;h<q.length;h++){const k=q[h];if(k===kb){found=true;break;}for(const n of adj.get(k)||[])if(!prev.has(n)){prev.set(n,k);q.push(n);}}
 if(!found)return null;const path=[];for(let k=kb;k!==null;k=prev.get(k))path.push(P.get(k));path.reverse();
 /* lintasan yang jauh lebih panjang dari jarak lurus (mis. memutari bukit) tidak dipakai */let L=0;for(let i=1;i<path.length;i++)L+=Math.hypot(path[i][0]-path[i-1][0],path[i][1]-path[i-1][1]);if(L>Math.max(4*d,d+80))return null;
 return path.map(p=>[p[0],p[1],z]);}
function xcJoin(A,B,z){const p=xcTopoPath(A,B,z);return p&&p.length?p:[];}
function xcStrings(r){const out=[],cut=$('xcut').checked&&TP.length,closeOn=!$('xclose')||$('xclose').checked;const S=r.S.concat(r.day||[]);
 if(!closeOn){for(const s of S)for(const pc of (s.t==='day'?[s.pts]:cutPieces(s)))out.push({t:s.t,z:s.z,pts:pc,closed:false});return out;}
 /* jalan: pasangkan tepi A–B */const roads=S.filter(s=>s.t==='road'&&s.pts.length>1),used=new Set(),ribs=[];
 for(let a=0;a<roads.length;a++){if(used.has(a))continue;const A=roads[a].pts;if(A.length<4)continue;let best=-1,bd=1e18;
  for(let b=a+1;b<roads.length;b++){if(used.has(b))continue;const B=roads[b].pts;if(B.length<4)continue;const d0=Math.hypot(A[0][0]-B[0][0],A[0][1]-B[0][1]),d1=Math.hypot(A[A.length-1][0]-B[B.length-1][0],A[A.length-1][1]-B[B.length-1][1]),dz=Math.abs(A[0][2]-B[0][2])+Math.abs(A[A.length-1][2]-B[B.length-1][2]);
   if(d0<30&&d1<30&&dz<3&&d0+d1<bd){bd=d0+d1;best=b;}}
  if(best>=0){used.add(a);used.add(best);const B=roads[best].pts;ribs.push({a:A,b:B});out.push({t:'road',z:roads[a].z,pts:A.concat(B.slice().reverse()),closed:true});}}
 /* garis penutup ujung jalan (pendek, kedua ujungnya di ujung pita) → sudah menjadi sisi pita */
 const nearEnd=p=>ribs.some(R=>[R.a[0],R.b[0],R.a[R.a.length-1],R.b[R.b.length-1]].some(q=>Math.hypot(q[0]-p[0],q[1]-p[1])<1.0));
 roads.forEach((s,i)=>{if(used.has(i))return;const P=s.pts;if(nearEnd(P[0])&&nearEnd(P[P.length-1]))return;out.push({t:'road',z:s.z,pts:P,closed:false});});
 for(const s of S){if(s.t==='road')continue;
  if(s.t==='day'){if(s.pts.length>=3)out.push({t:'day',z:s.z,pts:s.pts,closed:true});continue;}
  if(s.t==='xroad'||s.t==='xcut'||s.t==='xfill'){for(const pc of (cut?cutPieces(s):[s.pts]))out.push({t:s.t,z:s.z,pts:pc,closed:false});continue;}
  const z=+s.z,ring=xcRing(s);const whole=!cut||s.pts.every(p=>{const t=topoZ(p[0],p[1]);return !isFinite(t)||p[2]<=t+0.05;});if(ring&&whole){out.push({t:s.t,z:s.z,pts:s.pts,closed:true});continue;}let pcs=cut&&!whole?cutPieces(s):[s.pts];pcs=pcs.filter(p=>p.length>1);if(!pcs.length)continue;
  if(!isFinite(z)){for(const pc of pcs)out.push({t:s.t,z:s.z,pts:pc,closed:false});continue;}
  if(ring&&pcs.length===1&&pcs[0]===s.pts){out.push({t:s.t,z,pts:s.pts,closed:true});continue;}
  const R=[];for(let i=0;i<pcs.length;i++){const pc=pcs[i],nx=pcs[(i+1)%pcs.length];for(const p of pc)R.push(p);const A=pc[pc.length-1],B=nx[0];R.push(...xcJoin(A,B,z));}
  out.push({t:s.t,z,pts:R,closed:true});}
 return out;}
/* tulis ulang tombol ekspor */
(function(){const cb=$('xcut');if(cb&&!$('xclose')){const l=document.createElement('label');l.innerHTML='<input type="checkbox" id="xclose" checked> Tutup string (bench ditutup mengikuti kontur topografi, jalan jadi poligon pita)';l.title='Matikan untuk menulis potongan string apa adanya (cara lama)';const pl=cb.closest('label');(pl||cb).insertAdjacentElement('afterend',l);if(pl)l.style.display='block';}
 $('xstr').onclick=()=>{const r=needR();if(!r)return;const L=[pjName()+','+new Date().toLocaleDateString('en-GB')+',,ssi_styles:survey.ssi','0, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000'];
  for(const o of xcStrings(r)){const P=o.pts.slice();if(o.closed&&P.length>2){const a=P[0],b=P[P.length-1];if(Math.hypot(a[0]-b[0],a[1]-b[1])>1e-4||Math.abs(a[2]-b[2])>1e-4)P.push(a);}const c=CODE[o.t]||9;
   for(const p of P)L.push(c+', '+p[1].toFixed(3)+', '+p[0].toFixed(3)+', '+p[2].toFixed(3)+', '+TNM[o.t]+', '+(o.t==='day'?'0.0':(+o.z).toFixed(1)));L.push('0, 0.000, 0.000, 0.000,');}
  L.push('0, 0.000, 0.000, 0.000, END');dl(L.join('\r\n')+'\r\n',pjName()+'_'+today()+'.str');};
 $('xdxf').onclick=()=>{const r=needR();if(!r)return;let d=dxfHead();const LY={crest:'CREST',toe:'TOE',road:'JALAN',floor:'LANTAI',day:'POTONG_TOPO',old:'PIT_LAMA',xroad:'JALAN_LUAR',xcut:'CREST_POTONG',xfill:'KAKI_TIMBUNAN'};
  for(const o of xcStrings(r)){let P=o.pts;if(o.closed&&P.length>3){const a=P[0],b=P[P.length-1];if(Math.hypot(a[0]-b[0],a[1]-b[1])<1e-4)P=P.slice(0,-1);}const ly=LY[o.t]||'PIT';
   d+='0\nPOLYLINE\n8\n'+ly+'\n66\n1\n70\n'+(o.closed?9:8)+'\n10\n0\n20\n0\n30\n0\n';for(const p of P)d+='0\nVERTEX\n8\n'+ly+'\n10\n'+p[0].toFixed(3)+'\n20\n'+p[1].toFixed(3)+'\n30\n'+p[2].toFixed(3)+'\n70\n32\n';d+='0\nSEQEND\n8\n'+ly+'\n';}
  dl(d+'0\nENDSEC\n0\nEOF\n',pjName()+'_string_'+today()+'.dxf');};})();
try{window.__PS3.xc={tpath:(A,B,z)=>{const p=xcTopoPath(A,B,z);return p?{n:p.length,dz:Math.max(...p.map(q=>Math.abs(topoZ(q[0],q[1])-z))),L:p.reduce((s,q,i)=>i?s+Math.hypot(q[0]-p[i-1][0],q[1]-p[i-1][1]):0,0)}:null;},tz:(x,y)=>topoZ(x,y),dbg:(z)=>{const r=curR();const s=r.S.find(q=>(q.t==='crest'||q.t==='toe')&&+q.z===z&&cutPieces(q).length>0&&xcRing(q));if(!s)return null;const P=cutPieces(s);return P.map(pc=>({n:pc.length,a:pc[0],b:pc[pc.length-1]})).concat([{path:(()=>{const A=P[P.length-1][P[P.length-1].length-1],B=P[0][0];const pth=xcTopoPath(A,B,z);return pth?pth.length:null;})(),tA:topoZ(P[0][0][0],P[0][0][1])}]);},vol:()=>{const r=curR();if(!r)return null;if(!r.vol)r.vol=volOf(r);return r.vol.tot;},strings:()=>{const r=curR();return r?xcStrings(r).map(o=>({t:o.t,z:o.z,n:o.pts.length,closed:o.closed,gap:Math.hypot(o.pts[0][0]-o.pts[o.pts.length-1][0],o.pts[0][1]-o.pts[o.pts.length-1][1]),pts:o.pts})):null;},raw:()=>{const r=curR();return r?r.S.concat(r.day||[]).map(s=>({t:s.t,z:s.z,n:s.pts.length,ring:xcRing(s),pcs:cutPieces(s).length})):null;}};}catch(_){}
