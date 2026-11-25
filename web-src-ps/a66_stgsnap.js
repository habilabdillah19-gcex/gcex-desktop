/* a66: STAGING MENEMPEL PIT FINAL (pemilik 24 Nov): "bila jarak batas staging di topografi ke desain final < 12 m, sistem
   menganggap user ingin staging mengambil string desain final; bila > 12 m pakai hasil simulasi."
   Cara: dari batas staging (garis atas di topografi) tiap ruas diukur ke tapak pit final (garis daylight final). Ruas yang
   < jarak tangkap (bawaan 12 m) → sektor "ikut final": kipas dari ruas itu ke titik tengah tapak final. Di dalam sektor,
   pada setiap RL staging = batas pit final (string final dipakai apa adanya); di luar sektor = hasil simulasi (dipotong final)
   dengan aturan celah tipis lama. Sektor dihitung sekali per pembuatan desain, sehingga dinding yang menempel final lurus
   dari atas sampai bawah — tidak berganti-ganti per bench (penyebab bentuk "tidak karuan"). */
(function(){const e=$('sfsnap');if(e){if(e.value==='10'||e.value==='')e.value=12;e.title='Jarak tangkap ke pit final: bagian batas staging yang berjarak kurang dari ini ke tapak pit final mengikuti string pit final dari atas sampai bawah; selebihnya hasil simulasi. 0 = mati.';}})();
function stgSector(d){if(!FIN||!FIN.footP||!FIN.footP.length||!BASE)return null;
 const top=(BASE.src3&&BASE.src3.length>2)?BASE.src3:(BASE.src&&BASE.src.length>2?BASE.src:null);if(!top)return null;
 const F=FIN.footP.map(r=>ringOf(r)).filter(r=>r.length>2);if(!F.length)return null;
 const dSeg=(p,a,b)=>{const dx=b[0]-a[0],dy=b[1]-a[1],L2=dx*dx+dy*dy||1,t=Math.max(0,Math.min(1,((p[0]-a[0])*dx+(p[1]-a[1])*dy)/L2));return Math.hypot(p[0]-a[0]-dx*t,p[1]-a[1]-dy*t);};
 const dF=p=>{let m=1e18;for(const r of F)for(let i=0;i<r.length;i++){const v=dSeg(p,r[i],r[(i+1)%r.length]);if(v<m)m=v;}return m;};
 let cx=0,cy=0,n=0;for(const r of F)for(const p of r){cx+=p[0];cy+=p[1];n++;}cx/=n;cy/=n;
 const T=top.map(p=>[p[0],p[1]]),N=T.length,near=T.map(p=>dF(p)<d);let tri=[];
 for(let i=0;i<N;i++){const j=(i+1)%N;if(!(near[i]&&near[j]))continue;const a=T[i],b=T[j];/* kipas diperpanjang sedikit keluar supaya menutup dinding final di bibir */
  const ex=p=>{const vx=p[0]-cx,vy=p[1]-cy,l=Math.hypot(vx,vy)||1;return [p[0]+vx/l*(d+5),p[1]+vy/l*(d+5)];};tri.push(toC([[cx,cy],ex(a),ex(b)]));}
 if(!tri.length)return {Z:[],n:0,N};let Z=[];try{Z=cBool(tri.map(t=>[t]).flat(),[],ClipperLib.ClipType.ctUnion);}catch(_){try{Z=tri.reduce((u,t)=>u.length?cUnion(u,[t]):[t],[]);}catch(__){Z=[];}}
 return {Z,n:near.filter(Boolean).length,N};}
{const _f=finClamp;finClamp=function(){const base=_f.apply(this,arguments);if(!base)return base;const d=Math.max(0,+$('sfsnap').value||0);let S=null;try{if(d>0&&MODE==='stage')S=stgSector(d);}catch(e){console.warn('stgSector',e);}
 FIN.sec=S;if(!S||!S.Z.length)return base;
 return (P,z,kind)=>{const out=base(P,z,kind);try{if(!(z<=FIN.zmax-0.01))return out;const L=limAt(z,kind);if(!L.length)return out;const add=cInter(L,S.Z);if(!add.length)return out;
   /* hanya bagian sektor yang bersambung dengan galian staging di level ini (bukan pulau terpisah di dasar final) */const A=out&&out.length?out:P;const Ag=cOff(A,0.5),keep=add.filter(r=>cInter([r],Ag).length);if(!keep.length)return out;FIN.hits.add(Math.round(z*10)/10);return tidy(cUnion(A,keep));}catch(e){console.warn(e);return out;}};};}
try{const _si=stgInfo;stgInfo=function(R0){let h=_si.apply(this,arguments);try{const S=FIN&&FIN.sec;if(S&&S.n)h+='<br>Ikut string pit final pada '+Math.round(100*S.n/S.N)+'% batas staging (jarak ke tapak final &lt; '+(+$('sfsnap').value||0)+' m); sisanya hasil simulasi.';}catch(_){}return h;};}catch(_){}
try{window.__PS3.stgs={sec:()=>FIN&&FIN.sec?{n:FIN.sec.n,N:FIN.sec.N,nz:FIN.sec.Z.length}:null};}catch(_){}
