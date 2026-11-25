/* a43: PERMUKAAN HITUNG PRESISI untuk laporan block model — resep GC-Ex Block Model (rpbm.js / tinz.js / tinhr.js), yang
   sudah dicocokkan pemilik dengan DTM Surpac (pit_z3south_r4: rata |dz| 0,86 → 0,05 m):
   1) sumber STRING (topografi, pit final impor) dirapatkan tiap 2 m sepanjang string, lalu ditriangulasi Delaunay;
      segitiga bersisi > 8 × median dibuang hanya bila tersambung ke tepi luar (kipas di cekungan tepi);
   2) desain buatan Pit Studio memakai SEGITIGA TIN desainnya sendiri apa adanya (string = garis patah), tanpa triangulasi ulang;
   3) Z di (x,y) = interpolasi LINEAR di dalam segitiga yang memuat titik itu; di luar segitiga = di luar permukaan (blok tidak dihitung);
   4) cara Surpac: blok utuh masuk bila TITIK PUSATNYA di bawah / pada topografi dan di atas / pada desain;
      cara proporsional (cara GC-Ex): telapak blok dibagi 4 × 4 kolom, tiap kolom dipotong kedua permukaan.
   Sebelumnya Pit Studio membaca Z dari raster TIN (sel 1 m atau lebih) dengan interpolasi bilinear. */
const PX={wm:new WeakMap(),on:true,n:4};
function pxRapat(L,step){const P=[];for(const l of L){let p=null;for(const q of l){if(!(q[0]===q[0]&&q[1]===q[1]&&q[2]===q[2]))continue;if(p){const d=Math.hypot(q[0]-p[0],q[1]-p[1]),m=Math.ceil(d/step);for(let k=1;k<m;k++){const t=k/m;P.push({x:p[0]+(q[0]-p[0])*t,y:p[1]+(q[1]-p[1])*t,z:p[2]+(q[2]-p[2])*t});}}P.push({x:q[0],y:q[1],z:q[2]});p=q;}}return P;}
function pxOfStrings(L){if(!L||!L.length||!window.TINZ)return null;let c=PX.wm.get(L);if(c&&c.n===L.length)return c.t;let t=null;try{t=window.TINZ(pxRapat(L,2),{faktor:8,tepi:true});}catch(e){console.warn('px',e);}PX.wm.set(L,{n:L.length,t});return t;}
function pxOfTin(tin){if(!tin||!tin.T||!tin.X||!window.TINZ)return null;let c=PX.wm.get(tin);if(c&&c.n===tin.T.length)return c.t;const nt=tin.T.length/3|0,I=new Uint32Array(nt),J=new Uint32Array(nt),K=new Uint32Array(nt);for(let q=0;q<nt;q++){I[q]=tin.T[3*q];J[q]=tin.T[3*q+1];K[q]=tin.T[3*q+2];}
 let t=null;try{t=window.TINZ(null,{tri:{x:tin.X,y:tin.Y,z:tin.Z,i:I,j:J,k:K}});}catch(e){console.warn('px',e);}PX.wm.set(tin,{n:tin.T.length,t});return t;}
/* fungsi z(x,y) → angka atau NaN; null bila sumber presisi tidak tersedia (pemanggil kembali ke raster) */
function pxTopoFn(tp){if(!PX.on||!tp)return null;const t=tp.L?pxOfStrings(tp.L):pxOfTin(tp.tin);if(!t)return null;const f=t.f;return (x,y)=>{const v=f(x,y);return v==null?NaN:v;};}
function pxDesFn(d){if(!PX.on||!d)return null;const t=d.L?pxOfStrings(d.L):d.tin?pxOfTin(d.tin):null;if(!t)return null;const f=t.f;return (x,y)=>{const v=f(x,y);return v==null?NaN:v;};}
function pxInfo(tp,d){const a=tp&&(tp.L?pxOfStrings(tp.L):pxOfTin(tp.tin)),b=d&&(d.L?pxOfStrings(d.L):d.tin?pxOfTin(d.tin):null);if(!PX.on||!a||!b)return 'permukaan raster (cara lama)';return 'permukaan TIN presisi seperti GC-Ex / DTM Surpac (topografi '+a.nt.toLocaleString('id-ID')+' segitiga'+(tp.L?', string dirapatkan 2 m':'')+'; desain '+b.nt.toLocaleString('id-ID')+' segitiga'+(d.L?', string dirapatkan 2 m':', TIN desain asli')+')';}
/* proporsi volume blok di antara dua permukaan: n × n kolom (cara GC-Ex, rpsfrac.js) */
function pxFrac(ft,fd,x,y,cz,sx,sy,sz){const n=PX.n,z0=cz-sz/2,z1=cz+sz/2;let s=0;for(let a=0;a<n;a++)for(let b=0;b<n;b++){const xx=x-sx/2+(a+0.5)*sx/n,yy=y-sy/2+(b+0.5)*sy/n,t=ft(xx,yy),d=fd(xx,yy);if(!(t===t)||!(d===d))continue;const top=Math.min(t,z1),bot=Math.max(d,z0);if(top>bot)s+=top-bot;}return s/(n*n*sz);}
try{window.__PS3.px={S:PX,src:()=>{const tp=TP.find(q=>q.on&&q.G)||TP.find(q=>q.G);return {topoL:tp&&tp.L,fin:FIN?FIN.S.map(s=>s.pts):null,resS:RES?RES.S.map(s=>s.pts):null,res:RES&&RES.tin?{X:[...RES.tin.X],Y:[...RES.tin.Y],Z:[...RES.tin.Z],T:[...RES.tin.T]}:null};},z:(id,x,y)=>{const tp=TP.find(q=>q.on&&q.G)||TP.find(q=>q.G);if(id==='topo')return pxTopoFn(tp)(x,y);const d=schDes().find(q=>q.id===id);return pxDesFn(d)(x,y);}};}catch(_){}
/* ---------- menu Layar penuh ---------- */
(function(){const mb=$('mbar');if(!mb||$('mbfs'))return;const b=document.createElement('button');b.id='mbfs';b.className='mbb';b.innerHTML='&#9974; Layar penuh';b.title='Layar penuh (F11). Tekan Esc atau klik lagi untuk keluar.';
 const st=()=>{const on=!!document.fullscreenElement;b.innerHTML=on?'&#9974; Keluar layar penuh':'&#9974; Layar penuh';b.classList.toggle('sch-on',on);},tg=()=>{try{if(document.fullscreenElement)document.exitFullscreen();else document.documentElement.requestFullscreen().catch(e=>{try{schMsg('Layar penuh ditolak peramban: '+esc(e.message),1);}catch(_){}});}catch(_){}};
 b.onclick=tg;document.addEventListener('fullscreenchange',()=>{st();try{window.dispatchEvent(new Event('resize'));}catch(_){}});window.addEventListener('keydown',e=>{if(e.key==='F11'){e.preventDefault();tg();}});
 const ref=$('mbsch');if(ref&&ref.parentElement===mb)ref.insertAdjacentElement('afterend',b);else mb.appendChild(b);})();
