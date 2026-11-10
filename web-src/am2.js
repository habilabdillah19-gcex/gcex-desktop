
/* ================= AS-MINED v2: REGISTER POLIGON (selaras dig block & register Excel) =================
   Setiap boundary aktual = satu poligon as-mined dengan kode unik, string ID & warna kelas, register
   (pit, flitch, block, tanggal, shift, kode ore, tujuan), tonase & kadar per poligon, layout PDF dan
   ekspor register (kolom sama dengan "REGISTER POLIGON GC - AS-MINED"). */
var AMMON=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
function amToday(){var d=new Date(),p=function(n){return('0'+n).slice(-2);};return d.getFullYear()+'-'+p(d.getMonth()+1)+'-'+p(d.getDate());}
function amR(){var U=amU();if(!U.reg)U.reg={};var R=U.reg,m=BX.m,D={pit:'',date:amToday(),shift:'DS',block:'',tpl:'{PIT}_{RL}_{BLOCK}_{DDMM}{SHIFT}_{ORE}_{DEST}',auto:true,sep:'id',lyPit:false,lyTopo:false,lyBlk:true,
    cls:[{m:'MO',lo:0.3,hi:0.5,n:13,c:'#ffd43b'},{m:'LG',lo:0.5,hi:1,n:14,c:'#4caf50'},{m:'HG',lo:1,hi:'',n:17,c:'#ff1a1a'}],ws:{m:'WS',n:1,c:'#9aa3ad'},
    sxsThr:0.8,
    dst:[{o:'HG*',d:'ROM',l:'ROM Pad',j:'ROM Bin'},{o:'LGSF',d:'SPL',l:'Stockpile LG',j:'Stockpile'},{o:'MOSF',d:'SPL',l:'Stockpile LG',j:'Stockpile'},{o:'*OX',d:'SPO',l:'Stockpile Oksida',j:'Stockpile'},{o:'WS*',d:'WD',l:'Waste Dump',j:'Dump'}]};
  for(var k in D)if(R[k]===undefined)R[k]=JSON.parse(JSON.stringify(D[k]));
  if(R.sxs===undefined&&m){var nm=Object.keys(m.num);R.sxs=(window.dbU&&dbU().sxsAttr)||nm.filter(function(a){return /^s(x|ulph?|ulf)?s$|^sxs|^s_?ox|^stot$|^s$/i.test(a);})[0]||'';}
  if(R.ag===undefined&&m){R.ag=Object.keys(m.num).filter(function(a){return /^ag/i.test(a);})[0]||'';}
  return R;}
function amSGKey(){var U=BX.ui||{};return lyCalcM()+'|'+(U.sgCol||'')+'|'+(U.sgCol?(U.sgZero==='zero'?'0':String(bxSGrep())):String(U.sg))+(window.amFloorKey?amFloorKey():'')+(window.amRoofKey?amRoofKey():'');}
function amSGTxt(){var U=BX.ui||{};return U.sgCol?('SG kolom '+U.sgCol+(U.sgZero==='zero'?', blok <=0 = 0':', blok <=0 = '+bxSGrep())):('SG tetap '+U.sg);}
function amCMTxt(cm){return(cm||lyCalcM())==='surpac'?'Seperti Surpac (blok utuh, titik tengah)':'Presisi GC-Ex (dipotong di garis boundary)';}
function amShiftTxt(s){return /^N/i.test(s)?'Malam':'Siang';}
function amDateTxt(d){var p=String(d||'').split('-');if(p.length<3)return String(d||'');return(+p[2])+'-'+AMMON[(+p[1]-1)%12]+'-'+p[0].slice(2);}
function amDDMM(d){var p=String(d||'').split('-');return p.length<3?'':p[2]+p[1];}
/* ---------- boundary = poligon (field register disimpan di objek boundary, ikut proyek) ---------- */
function amBndAdd(pts,name,opt){/* opt (0.24.54): {top,bot,date,pit} dari NAMA FILE pick-up -- flitch, tanggal & pit tidak lagi ditebak dari flitch aktif / hari ini */var D=amD(),B=lyBench(),R=amR(),ZS=amZStat(pts);if(opt&&isFinite(opt.top)&&isFinite(opt.bot)&&opt.top>opt.bot)B=[+opt.top,+opt.bot];else if(ZS&&R.bndZ==='auto')B=amFlitchOfZ(ZS.med,B);var P=pts.map(function(q){return[+q[0],+q[1]];}),a=P[0],b=P[P.length-1];if(P.length>3&&Math.hypot(a[0]-b[0],a[1]-b[1])<0.05)P.pop();if(P.length<3)return false;
  var key=P.map(function(q){return q[0].toFixed(2)+','+q[1].toFixed(2);}).join(';');if(D.bnd.some(function(x){return x.key===key&&Math.abs(x.top-B[0])<1e-6&&Math.abs(x.bot-B[1])<1e-6;}))return false;
  var o={id:amBid(),name:name,top:B[0],bot:B[1],zs:ZS,pts:P,key:key,on:true,pit:(opt&&opt.pit)||R.pit,blk:R.block,date:(opt&&opt.date)||R.date,shift:R.shift,src:(opt&&opt.src)||'',ore:'',dest:'',code:'',sid:'',dens:'',ket:'',print:true,st:null,open:false};
  D.bnd.push(o);AM.last=o.id;AM.lastFl=B;amAuto();return true;}
function amBndAll(){return(amD().bnd||[]);}
function amPolys(){return amBndCur().filter(function(x){return x.on;}).map(function(x){return{id:x.id,r:x.pts,b:lyBB(x.pts),area:lyArea(x.pts),name:x.name};});}
function amBndDel(id){var D=amD();D.bnd=D.bnd.filter(function(x){return x.id!==id;});amAuto();amPanel();updatePlot();amDirty();}
function amBndOn(id,on){amD().bnd.forEach(function(x){if(x.id===id)x.on=on;});amAuto();amPanel();updatePlot();amDirty();}
var AMT=null;function amAuto(){if(!amR().auto)return;clearTimeout(AMT);AMT=setTimeout(function(){try{if(amBndCur().some(function(x){return x.on;}))amRun(true);}catch(e){console.error(e);}},60);}
/* ---------- klasifikasi, kode, tujuan ---------- */
function amCls(v){var R=amR(),best=null;(R.cls||[]).forEach(function(q){var lo=parseFloat(q.lo),hi=parseFloat(q.hi);if(isFinite(lo)&&v>=lo&&(!isFinite(hi)||v<hi)){if(!best||lo>parseFloat(best.lo))best=q;}});return best;}
function amClsByM(mm){var R=amR(),k=String(mm||'').toUpperCase();var q=(R.cls||[]).filter(function(c){return String(c.m).toUpperCase()===k;})[0];return q||(k===String(R.ws.m).toUpperCase()?R.ws:null);}
function amPat(p,s){var re=new RegExp('^'+String(p||'').toUpperCase().replace(/[.+?^${}()|[\]\\]/g,'\\$&').replace(/\*/g,'.*')+'$');return re.test(String(s||'').toUpperCase());}
function amDst(ore){var R=amR(),L=R.dst||[];for(var i=0;i<L.length;i++)if(L[i].o&&amPat(L[i].o,ore))return L[i];return null;}
function amDstByCode(d){var L=amR().dst||[];for(var i=0;i<L.length;i++)if(String(L[i].d)===String(d))return L[i];return{d:d,l:String(d),j:''};}
/* info lengkap satu poligon (dipakai panel, peta, PDF, CSV) */
function amInfo(x){var R=amR(),s=x.st,g=s&&s.n?s.gA:NaN,sx=s&&s.n?s.sx:NaN,ox=isFinite(sx)?(sx>(+R.sxsThr||0.8)?'SF':'OX'):'',c=s?(isFinite(g)?amCls(g):null):null;
  var auto=s?((c?c.m:R.ws.m)+ox):'??',ore=String(x.ore||'').trim()||auto,cm=ore.replace(/(SF|OX)$/i,''),oxo=(ore.match(/(SF|OX)$/i)||[''])[0].toUpperCase(),cc=amClsByM(cm)||(c||R.ws);
  var dr=x.dest?amDstByCode(x.dest):(s?amDst(ore):null),dest=dr?String(dr.d):'',area=lyArea(x.pts),hasV=!!(s&&s.v>0),bcm=hasV?s.v:area*(x.top-x.bot),sgM=hasV?s.t/s.v:(s&&s.sgM>=0?s.sgM:bxSGrep()),ov=parseFloat(x.dens)>0,dens=ov?parseFloat(x.dens):sgM,ton=ov?bcm*dens:(hasV?s.t:bcm*sgM),tM=hasV?s.t:bcm*sgM,stale=!!(s&&s.key!==amSGKey());
  var sid=parseInt(x.sid)>0?parseInt(x.sid):cc.n,col=x.col||cc.c;
  return{x:x,st:s,ore:ore,oreAuto:auto,cls:cm,ox:oxo,jenis:(oxo?oxo+'-':'')+cm,dest:dest,lok:dr?dr.l:'',jl:dr?dr.j:'',dens:dens,sgM:sgM,area:area,bcm:bcm,ton:ton,tM:tM,stale:stale,cm:s&&s.cm||'',
    el:s&&s.n&&s.el?s.el:{},elA:s&&s.elA?s.elA:[],gA:g,gO:s&&s.n?s.gO:NaN,ag:s&&s.n?s.ag:NaN,sx:sx,sid:sid,col:col,calc:!!s,pu:s&&s.t?s.tu/s.t*100:0};}
function amCode(I,x){var R=amR();if(String(x.code||'').trim())return String(x.code).trim();
  return String(R.tpl||'').replace('{PIT}',x.pit||lyZone()).replace('{RL}',lyNum(x.top)).replace('{TOP}',lyNum(x.top)).replace('{BOT}',lyNum(x.bot)).replace('{BLOCK}',x.blk||'?').replace('{DDMM}',amDDMM(x.date)).replace('{DATE}',String(x.date||'').replace(/-/g,'').slice(2))
    .replace('{SHIFT}',x.shift||'').replace('{ORE}',I.ore).replace('{DEST}',I.dest||'?').replace('{SID}',I.sid).replace(/\s+/g,'');}
/* semua poligon + kode unik (duplikat diberi akhiran _2, _3 ...) */
function amAllInfo(){var L=amBndAll().map(function(x){var I=amInfo(x);I.code=amCode(I,x);return I;}),seen={};
  L.forEach(function(I){var c=I.code,k=c.toUpperCase();if(seen[k]){seen[k]++;I.dup=true;I.code=c+'_'+seen[k];}else seen[k]=1;});return L;}
function amInfoById(id){var L=amAllInfo();for(var i=0;i<L.length;i++)if(L[i].x.id===id)return L[i];return null;}
/* ---------- hitung as-mined flitch aktif (+ statistik per poligon) ---------- */
function amRun(silent){var m=BX.m;if(!m)return;var U=amU(),R=amR(),B=lyBench(),fh=B[0]-B[1],P=amPolys();
  if(!P.length){AM.msg='<span class=warn>Belum ada poligon aktif di flitch RL '+lyFmt(B[0])+'&ndash;'+lyFmt(B[1])+'. Digit atau import boundary dulu (tab <b>Poligon</b>).</span>';amPanel();return;}
  var AMJ={a:0,p:P.map(function(){return 0;})};
  /* AMR = luas yang berada DI LUAR permukaan atap (hanya mode 'dtm'): di situ atap
     tidak diketahui, jadi dipakai RL atas flitch nominal dan luasnya DICATAT. Tanpa
     dicatat, bagian poligon yang permukaannya tidak menjangkau akan diam-diam dihitung
     dengan atap asumsi dan tidak ada yang tahu seberapa luas. */
  var AMR={a:0,p:P.map(function(){return 0;})};
  var CM=lyCalcM(),t0=Date.now(),G=amGrid(),dx=G.dx,dy=G.dy,dz=G.dz,O=G.O,cells=new Map(),Ga=m.num[U.attr],sgA=BX.ui.sgCol&&m.num[BX.ui.sgCol]?m.num[BX.ui.sgCol]:null,AG=R.ag&&m.num[R.ag]?m.num[R.ag]:null,SX=R.sxs&&m.num[R.sxs]?m.num[R.sxs]:null;
  var FM=R.floor==='pickup',FL=null,zLo=B[1];if(FM){FL=P.map(function(o){var F=amFloorFn(o,B);if(F.ok&&F.zmin<zLo)zLo=F.zmin;return F;});}
  /* ATAP. Bawaan tetap RL atas flitch nominal (B[0]) supaya tidak ada angka lama yang
     berubah diam-diam; lihat web-src/amroof.js. `zHi` melebar bila ada atap pick-up di
     ATAS RL nominal (overdig atap), kalau tidak blok di situ tidak akan ikut dicari. */
  var RM=(typeof amRoofMode==='function')&&amRoofMode()!=='flitch',RF=null,zHi=B[0];
  if(RM){RF=P.map(function(o){var F=amRoofFn(o,B);if(F.ok&&F.zmax>zHi)zHi=F.zmax;return F;});}
  var IX=lyCandZ(zLo,zHi);
  var iz0=Math.floor((B[1]-O[2])/dz+1e-9),iz1=Math.ceil((B[0]-O[2])/dz-1e-9)-1,ca=dx*dy;
  P.forEach(function(o,pi){var Rr=o.r,b=o.b,FP0=FM&&FL[pi].ok?FL[pi]:null,iz0p=FP0?Math.floor((FP0.zmin-O[2])/dz+1e-9):iz0,RP0=RM&&RF[pi].ok?RF[pi]:null,iz1p=RP0?Math.ceil((RP0.zmax-O[2])/dz-1e-9)-1:iz1;for(var t=0;t<IX.length;t++){var i=IX[t],hx=m.sx[i]/2,hy=m.sy[i]/2,hz=m.sz[i]/2;if(m.x[i]+hx<=b[0]||m.x[i]-hx>=b[1]||m.y[i]+hy<=b[2]||m.y[i]-hy>=b[3])continue;
      var bx0=Math.round((m.x[i]-hx-O[0])/dx),bx1=Math.round((m.x[i]+hx-O[0])/dx),by0=Math.round((m.y[i]-hy-O[1])/dy),by1=Math.round((m.y[i]+hy-O[1])/dy),bz0=Math.round((m.z[i]-hz-O[2])/dz),bz1=Math.round((m.z[i]+hz-O[2])/dz);
      if(CM==='surpac'){var zc=m.z[i],fbS=FP0?FP0.f(m.x[i],m.y[i]):B[1],rtS=RP0?RP0.f(m.x[i],m.y[i]):B[0];if(!isFinite(rtS))rtS=B[0];if(!(zc>fbS+1e-9&&zc<=rtS+1e-9))continue;if(!lyInS(Rr,m.x[i],m.y[i]))continue;
        for(var ix=bx0;ix<bx1;ix++)for(var iy=by0;iy<by1;iy++)for(var iz=bz0;iz<bz1;iz++){var k=ix+'|'+iy+'|'+iz+'|'+pi;if(!cells.has(k))cells.set(k,{ix:ix,iy:iy,iz:iz,p:i,pg:pi,pid:o.id,f:1});}continue;}
      var a0=Math.max(bx0,Math.floor((b[0]-O[0])/dx)),a1=Math.min(bx1,Math.ceil((b[1]-O[0])/dx)),c0=Math.max(by0,Math.floor((b[2]-O[1])/dy)),c1=Math.min(by1,Math.ceil((b[3]-O[1])/dy)),z0=Math.max(iz0p,bz0),z1=Math.min(iz1p,bz1-1);if(z1<z0)continue;
      for(var ix=a0;ix<a1;ix++)for(var iy=c0;iy<c1;iy++){var x0=O[0]+ix*dx,y0=O[1]+iy*dy,af=lyClip(Rr,[x0,x0+dx,y0,y0+dy])/ca;if(af<=1e-9)continue;if(af>1)af=1;var fb=FP0?FP0.f(x0+dx/2,y0+dy/2):B[1],rt=RP0?RP0.f(x0+dx/2,y0+dy/2):B[0];
        if(RP0&&!isFinite(rt)){AMR.a+=af*ca;AMR.p[pi]=(AMR.p[pi]||0)+af*ca;rt=B[0];}
        if(rt<=fb+1e-9){AMJ.a+=af*ca;AMJ.p[pi]=(AMJ.p[pi]||0)+af*ca;continue;}
        for(var iz=z0;iz<=z1;iz++){var zb=O[2]+iz*dz,zf=(Math.min(zb+dz,rt)-Math.max(zb,fb))/dz;if(zf<=1e-9)continue;var k=ix+'|'+iy+'|'+iz+'|'+pi;if(!cells.has(k))cells.set(k,{ix:ix,iy:iy,iz:iz,p:i,pg:pi,pid:o.id,f:af*Math.min(1,zf)});}}}});
  var C=Array.from(cells.values());
  /* AMJ = luas (m2) yang atapnya berada di bawah / sama dengan lantai: tebal nol.
     Terjadi pada underdig nyata atau titik dari hari yang salah. Dilaporkan, bukan
     dijepit diam-diam -- menjepit tanpa memberi tahu menyembunyikan masalah survei
     sebagai angka yang kelihatan wajar. */
  AM.jepit={a:AMJ.a,p:AMJ.p.slice()};
  AM.luarAtap={a:AMR.a,p:AMR.p.slice(),
               ganda:(RM&&RF?RF.reduce(function(n,F){return n+((F.cnt&&F.cnt.ganda)||0);},0):0)};
  var UPD=U.mode!=='full',nNoM=0,haveS=AM.comps.length>0;if(!haveS&&!UPD){AM.msg='<span class=warn>Estimasi ulang penuh butuh data sampel. Import collar &amp; assay dulu (tab <b>Sampel</b>), atau pakai metode Update model GC.</span>';amPanel();return;}
  if(UPD&&haveS){AM.comps.forEach(function(q){q.m=amModelAt(q.x,q.y,q.z,Ga);q.r=isFinite(q.m)?q.g-q.m:NaN;if(!isFinite(q.r))nNoM++;});}
  var Rs=Math.max(0.1,+U.R||15),Hs={},cs=Rs,key=function(a,b,c){return a+'|'+b+'|'+c;};AM.comps.forEach(function(q,j){if(UPD&&!isFinite(q.r))return;var k=key(Math.floor(q.x/cs),Math.floor(q.y/cs),Math.floor(q.z/cs));(Hs[k]=Hs[k]||[]).push(j);});
  var nd=Math.max(1,Math.min(4,+U.nd||2)),DP=[];for(var a=0;a<nd;a++)for(var b2=0;b2<nd;b2++)for(var c=0;c<nd;c++)DP.push([((a+0.5)/nd-0.5)*dx,((b2+0.5)/nd-0.5)*dy,((c+0.5)/nd-0.5)*dz]);
  var cbb=0;DP.forEach(function(p){DP.forEach(function(q){cbb+=amCov(Math.hypot(p[0]-q[0],p[1]-q[1],p[2]-q[2]),U);});});cbb/=DP.length*DP.length;
  var minS=Math.max(1,+U.minS||1),maxS=Math.max(minS,+U.maxS||12),s={vol:0,t:0,gO:0,gA:0,ne:0,nf:0,ns:0,tu:0,mode:UPD?'upd':'full',E:elQInit(U.attr)},PS=P.map(function(){return{n:0,ne:0,v:0,t:0,tu:0,gA:0,gO:0,ag:0,agT:0,sx:0,sxT:0,E:elQInit(U.attr)};});
  C.forEach(function(cl){var cx=O[0]+(cl.ix+0.5)*dx,cy=O[1]+(cl.iy+0.5)*dy,cz=O[2]+(cl.iz+0.5)*dz;cl.x=cx;cl.y=cy;cl.z=cz;var gx=Math.floor(cx/cs),gy=Math.floor(cy/cs),gz=Math.floor(cz/cs),N=[];
    for(var a=-1;a<=1;a++)for(var b=-1;b<=1;b++)for(var c=-1;c<=1;c++){var L=Hs[key(gx+a,gy+b,gz+c)];if(L)L.forEach(function(j){var q=AM.comps[j],d=Math.hypot(q.x-cx,q.y-cy,q.z-cz);if(d<=Rs)N.push([d,j]);});}
    N.sort(function(p,q){return p[0]-q[0];});N=N.slice(0,maxS);cl.go=Ga?Ga[cl.p]:NaN;
    if(N.length<minS){cl.est=0;cl.g=cl.go;cl.ns=N.length;cl.kv=NaN;cl.dmin=N.length?N[0][0]:NaN;cl.res=0;}
    else if(UPD){var n=N.length,Mx=[],rhs=[];for(var i=0;i<n;i++){var qi=AM.comps[N[i][1]],row=[];for(var j=0;j<n;j++){var qj=AM.comps[N[j][1]];row.push(amCov(Math.hypot(qi.x-qj.x,qi.y-qj.y,qi.z-qj.z),U));}Mx.push(row);
        var cb=0;DP.forEach(function(p){cb+=amCov(Math.hypot(qi.x-(cx+p[0]),qi.y-(cy+p[1]),qi.z-(cz+p[2])),U);});rhs.push(cb/DP.length);}
      var w=amSolve(Mx,rhs),rs=0,kv=cbb;if(w){for(i=0;i<n;i++){rs+=w[i]*AM.comps[N[i][1]].r;kv-=w[i]*rhs[i];}}else kv=NaN;var base=isFinite(cl.go)?cl.go:0;cl.res=rs;cl.g=Math.max(0,base+rs);cl.kv=kv;cl.est=1;cl.ns=n;cl.dmin=N[0][0];}
    else{var n=N.length,Mx=[],rhs=[];for(var i=0;i<n;i++){var qi=AM.comps[N[i][1]],row=[];for(var j=0;j<n;j++){var qj=AM.comps[N[j][1]];row.push(amCov(Math.hypot(qi.x-qj.x,qi.y-qj.y,qi.z-qj.z),U));}row.push(1);Mx.push(row);
        var cb=0;DP.forEach(function(p){cb+=amCov(Math.hypot(qi.x-(cx+p[0]),qi.y-(cy+p[1]),qi.z-(cz+p[2])),U);});rhs.push(cb/DP.length);}
      Mx.push(N.map(function(){return 1;}).concat([0]));rhs.push(1);var w=amSolve(Mx,rhs);
      if(!w){var sw=0,sg=0;N.forEach(function(p){var ww=1/Math.max(0.01,p[0]*p[0]);sw+=ww;sg+=ww*AM.comps[p[1]].g;});cl.g=sg/sw;cl.kv=NaN;}
      else{var g=0,kv=cbb;for(i=0;i<n;i++){g+=w[i]*AM.comps[N[i][1]].g;kv-=w[i]*rhs[i];}kv-=w[n];cl.g=g;cl.kv=kv;}cl.est=1;cl.ns=n;cl.dmin=N[0][0];}
    var sg2=sgA&&isFinite(sgA[cl.p])&&sgA[cl.p]>0?sgA[cl.p]:BX.ui.sg,v=dx*dy*dz*(cl.f||1),t=v*sg2;cl.t=t;s.vol+=v;s.t+=t;if(isFinite(cl.go))s.gO+=cl.go*t;if(isFinite(cl.g))s.gA+=cl.g*t;if(cl.est){s.ne++;s.tu+=t;}else s.nf++;s.ns+=cl.ns;
    var q=PS[cl.pg];q.n++;q.v+=v;q.t+=t;if(cl.est){q.ne++;q.tu+=t;}if(isFinite(cl.g))q.gA+=cl.g*t;if(isFinite(cl.go))q.gO+=cl.go*t;if(AG&&isFinite(AG[cl.p])){q.ag+=AG[cl.p]*t;q.agT+=t;}if(SX&&isFinite(SX[cl.p])){q.sx+=SX[cl.p]*t;q.sxT+=t;}elQAdd(q,cl.p,t);elQAdd(s,cl.p,t);});var sEL=elQFin(s,s.t?s.gA/s.t:NaN);s.el=sEL.el;s.elw=sEL.elw;s.elA=sEL.elA;delete s.E;
  var now=new Date().toISOString(),byId={};amBndAll().forEach(function(x){byId[x.id]=x;});
  P.forEach(function(o,pi){var q=PS[pi],x=byId[o.id];if(!x)return;var EQ=elQFin(q,q.t?q.gA/q.t:NaN);x.st={fl:FM?(FL[pi].ok?{n:FL[pi].n,med:FL[pi].med,min:FL[pi].zmin,max:FL[pi].zmax}:{n:FL[pi].n,none:1}):null,el:EQ.el,elw:EQ.elw,elA:EQ.elA,n:q.n,ne:q.ne,v:q.v,t:q.t,tu:q.tu,cm:CM,key:amSGKey(),sgM:q.v?q.t/q.v:NaN,gA:q.t?q.gA/q.t:NaN,gO:q.t?q.gO/q.t:NaN,ag:q.agT?q.ag/q.agT:NaN,sx:q.sxT?q.sx/q.sxT:NaN,attr:U.attr,agA:R.ag,sxA:R.sxs,mode:s.mode,at:now};});
  var areaP=0;P.forEach(function(o){areaP+=o.area;});
  /* Volume bila SEMUA sel dihitung penuh -- itulah yang akan didapat siapa pun yang
     menghitung ulang dari dimensi blok di Surpac, sebab ekspor .mdl / CSV menulis DX/DY/DZ
     ukuran sel penuh. Selisihnya terhadap s.vol ada di sel pecahan (tepi poligon, atap,
     lantai) dan harus TERLIHAT, bukan ditemukan orang lain saat rekonsiliasi. */
  s.volPenuh=C.length*dx*dy*dz;
  AM.res[lyFmt(B[0])+'_'+lyFmt(B[1])]={top:B[0],bot:B[1],cells:C,sum:s,polys:P.map(function(o){return o.name;}),area:areaP,volP:areaP*fh,ms:Date.now()-t0,attr:U.attr,par:JSON.parse(JSON.stringify(U)),nComp:AM.comps.length,date:now};
  AM.msg=(window.amVolTxt?amVolTxt(s):'')+P.length+' poligon dihitung ('+(CM==='surpac'?'Seperti Surpac: blok utuh, titik tengah':'Presisi: dipotong di garis boundary')+', '+amSGTxt()+') di flitch RL '+lyFmt(B[0])+'&ndash;'+lyFmt(B[1])+': <b>'+C.length.toLocaleString()+'</b> sub-blok'+(haveS?', <b>'+s.ne.toLocaleString()+'</b> '+(UPD?'diperbarui data baru':'terestimasi')+', '+s.nf.toLocaleString()+' mewarisi model GC':' &middot; <span class=warn>belum ada data sampel: kadar = model GC</span>')+(UPD&&nNoM?' &middot; <span class=warn>'+nNoM+' komposit di luar block model</span>':'')+' &middot; '+((Date.now()-t0)/1000).toFixed(1)+' s';
  amPanel();updatePlot();amDirty();}
/* ---------- edit field register ---------- */
function amPSet(id,f,v){var x=amBndAll().filter(function(q){return q.id===id;})[0];if(!x)return;x[f]=v;amPanel();if(['ore','dest','sid','col','code','blk','date','shift','pit'].indexOf(f)>=0)updatePlot();amDirty();}
function amPOpen(id){amBndAll().forEach(function(q){q.open=q.id===id?!q.open:q.open;});amPanel();}
function amRSet(k,v){var R=amR();R[k]=v;amPanel();updatePlot();amDirty();}
function amClsSet(i,f,v){var R=amR();if(i==='ws')R.ws[f]=f==='n'?parseInt(v)||1:v;else if(R.cls[i])R.cls[i][f]=f==='n'?parseInt(v)||1:v;amPanel();updatePlot();amDirty();}
function amClsAdd(){amR().cls.push({m:'MG',lo:'',hi:'',n:15,c:'#f08c00'});amPanel();amDirty();}
function amClsDel(i){amR().cls.splice(i,1);amPanel();updatePlot();amDirty();}
function amDstSet(i,f,v){var R=amR();if(R.dst[i])R.dst[i][f]=v;amPanel();updatePlot();amDirty();}
function amDstAdd(){amR().dst.push({o:'',d:'',l:'',j:''});amPanel();amDirty();}
function amDstDel(i){amR().dst.splice(i,1);amPanel();updatePlot();amDirty();}
function amApplyDef(){var R=amR(),n=0;amBndCur().forEach(function(x){x.pit=R.pit;x.date=R.date;x.shift=R.shift;n++;});AM.bmsg=n+' poligon di flitch ini memakai pit / tanggal / shift default.';amPanel();updatePlot();amDirty();}
/* ---------- panel ---------- */
function amPanel(){var el=$('amBody');if(!el)return;var m=BX.m;if(!m){el.innerHTML='<div class=hint>Buka block model <b>resmi</b> (file .mdl Surpac atau CSV) dulu lewat menu <b>Block Model &rarr; Import BM</b> atau jendela awal.</div>';return;}
  var D=amD(),U=amU(),R=amR(),B=lyBench(),L=lyU(),G=amGrid(),nums=Object.keys(m.num),Rw=amRows(),T=amTot(Rw),BC=amBndCur(),on=window.dbFlOn&&dbFlOn(),ALL=amAllInfo(),CUR=ALL.filter(function(I){return Math.abs(I.x.top-B[0])<1e-6&&Math.abs(I.x.bot-B[1])<1e-6;});
  var inp=function(k,lab,st,ti){return '<div><label>'+lab+'</label><input type=number step='+(st||'any')+' value="'+amE(U[k])+'" onchange="amSet(\''+k+'\',this.value)"'+(ti?' title="'+amE(ti)+'"':'')+'></div>';};
  var rin=function(k,lab,type,ph){return '<div><label>'+lab+'</label><input type='+(type||'text')+' value="'+amE(R[k])+'" placeholder="'+amE(ph||'')+'" onchange="amRSet(\''+k+'\',this.value)"></div>';};
  var sel=function(v,opts,on){return '<select onchange="'+on+'">'+opts.map(function(o){var val=o[0],lb=o[1];return '<option value="'+amE(val)+'"'+(String(val)===String(v)?' selected':'')+'>'+amE(lb)+'</option>';}).join('')+'</select>';};
  var h='<div class=amflow>Alur: <b>Setup</b> &rarr; <b>Sampel</b> &rarr; <b>Poligon</b> &rarr; <b>Parameter</b> &rarr; <b>Register</b> &rarr; <b>Layout &amp; export</b></div>';
  /* 1. setup */
  h+='<div class=amh>Setup register &amp; model</div><div class=hint style="margin-top:0">Model resmi: <b>'+amE((m.mdl&&m.mdl.file)||m.name)+'</b> &middot; '+m.n.toLocaleString()+' blok &middot; grid as-mined '+G.dx+' &times; '+G.dy+' &times; '+G.dz+' m</div>'+
    '<div class=amset><div class=amst><b>Default poligon baru</b></div><div class=g3>'+rin('pit','Pit / zona','text','mis. Z4')+rin('date','Tanggal','date')+'<div><label>Shift</label>'+sel(R.shift,[['DS','DS · Siang'],['NS','NS · Malam']],"amRSet('shift',this.value)")+'</div></div>'+
    '<div class=g2 style="margin-top:4px">'+rin('block','Block default','text','mis. 15')+'<div style="align-self:end"><button style="width:100%" onclick="amApplyDef()" title="Terapkan pit, tanggal &amp; shift default ke semua poligon flitch aktif">Terapkan ke flitch ini</button></div></div>'+
    '<div style="margin-top:4px"><label>Templat kode poligon</label><input type=text value="'+amE(R.tpl)+'" onchange="amRSet(\'tpl\',this.value)" style="font-family:Consolas,monospace;font-size:11.5px"></div>'+
    '<div class=hint>Token: {PIT} {RL} {BLOCK} {DDMM} {SHIFT} {ORE} {DEST} &middot; juga {TOP} {BOT} {DATE} {SID}. Contoh: <code>'+amE(amCode({ore:'LGSF',dest:'SPL',sid:14},{pit:R.pit||'P1',top:240,bot:238.5,blk:'15',date:R.date,shift:R.shift}))+'</code></div></div>'+
    '<details class=amdet'+(AM.openRules?' open':'')+' ontoggle="AM.openRules=this.open"><summary>Kelas ore, oksidasi &amp; tujuan dumping</summary>'+
    '<div class=hint>Kelas dari kadar '+amE(U.attr)+' as-mined per poligon (batas bawah &le; kadar &lt; batas atas); string ID &amp; warna dipakai di peta, STR dan PDF.</div><table class="pltb amt amcls"><tr><th>Kode</th><th>Dari</th><th>s/d &lt;</th><th>Str</th><th>Warna</th><th></th></tr>'+
    R.cls.map(function(c,i){return '<tr><td><input value="'+amE(c.m)+'" onchange="amClsSet('+i+',\'m\',this.value.toUpperCase())"></td><td><input type=number step=any value="'+amE(c.lo)+'" onchange="amClsSet('+i+',\'lo\',this.value)"></td><td><input type=number step=any value="'+amE(c.hi)+'" placeholder="max" onchange="amClsSet('+i+',\'hi\',this.value)"></td><td><input type=number value="'+amE(c.n)+'" onchange="amClsSet('+i+',\'n\',this.value)"></td><td><input type=color value="'+amE(c.c)+'" onchange="amClsSet('+i+',\'c\',this.value)"></td><td><button class=x onclick="amClsDel('+i+')" title="Hapus kelas">&times;</button></td></tr>';}).join('')+
    '<tr><td><input value="'+amE(R.ws.m)+'" onchange="amClsSet(\'ws\',\'m\',this.value.toUpperCase())"></td><td colspan=2><small>di bawah kelas terendah</small></td><td><input type=number value="'+amE(R.ws.n)+'" onchange="amClsSet(\'ws\',\'n\',this.value)"></td><td><input type=color value="'+amE(R.ws.c)+'" onchange="amClsSet(\'ws\',\'c\',this.value)"></td><td></td></tr></table><button style="width:100%;margin-top:3px" onclick="amClsAdd()">+ Kelas</button>'+
    '<div class=g3 style="margin-top:6px"><div><label>Kolom Ag</label>'+sel(R.ag,[['','(tidak ada)']].concat(nums.map(function(a){return[a,a];})),"amRSet('ag',this.value)")+'</div><div><label>Kolom SxS</label>'+sel(R.sxs,[['','(tidak ada)']].concat(nums.map(function(a){return[a,a];})),"amRSet('sxs',this.value)")+'</div><div><label>SF bila SxS &gt;</label><input type=number step=any value="'+amE(R.sxsThr)+'" onchange="amRSet(\'sxsThr\',this.value)"></div></div>'+
    '<div class=hint>Kode ore = kelas + oksidasi, mis. LG + SF = <b>LGSF</b>. Tanpa kolom SxS, akhiran oksidasi dikosongkan.</div>'+
    '<div class=hint style="margin-top:6px">Tujuan dumping per kode ore (dibaca dari atas; * = wildcard):</div><table class="pltb amt amdst"><tr><th>Kode ore</th><th>Kode</th><th>Lokasi</th><th>Jenis</th><th></th></tr>'+
    R.dst.map(function(q,i){return '<tr><td><input value="'+amE(q.o)+'" onchange="amDstSet('+i+',\'o\',this.value.toUpperCase())"></td><td><input value="'+amE(q.d)+'" onchange="amDstSet('+i+',\'d\',this.value)"></td><td><input value="'+amE(q.l)+'" onchange="amDstSet('+i+',\'l\',this.value)"></td><td><input value="'+amE(q.j)+'" onchange="amDstSet('+i+',\'j\',this.value)"></td><td><button class=x onclick="amDstDel('+i+')">&times;</button></td></tr>';}).join('')+
    '</table><button style="width:100%;margin-top:3px" onclick="amDstAdd()">+ Aturan tujuan</button></details>';
  /* 2. data sampel */
  h+='<div class=amh>Data sampel (format collar-assay)</div>';
  ['ch','gc'].forEach(function(k){var S=D.sets[k]||{fn:{}},fn=S.fn||{};h+='<div class=amset><div class=amst><b>'+AMSET[k]+'</b>'+(S.col||S.asy?'<button class=x onclick="amClearSet(\''+k+'\')" title="Hapus data '+AMSET[k]+'">&times;</button>':'')+'</div><div class="g3 amf">'+
      ['col','asy','sur'].map(function(q){var lb={col:'Collar',asy:'Assay',sur:'Survey (ops.)'}[q];return '<label class="mdbtn'+(fn[q]?' ok':'')+'" title="'+amE(fn[q]||'')+'"><input type=file accept=".csv,.txt,.tsv" onchange="amFile(\''+k+'\',\''+q+'\',this.files[0]);this.value=\'\'">'+(fn[q]?'&#10003; ':'')+lb+'</label>';}).join('')+'</div>'+
      (S.asy?'<div class=g2 style="margin-top:3px"><div><label>Kolom kadar</label><select onchange="amSetG(\''+k+'\',this.value)">'+S.asy.h.map(function(c){return '<option'+(c===S.gcol?' selected':'')+'>'+amE(c)+'</option>';}).join('')+'</select></div><div class=hint style="align-self:end">'+(S.info||'')+'</div></div>':(S.info?'<div class=hint>'+S.info+'</div>':''))+'</div>';});
  h+='<div class=g2 style="margin-top:4px">'+inp('comp','Panjang komposit (m)')+'<div><label>Konvensi dip</label><select onchange="amSet(\'dipNeg\',this.value===\'1\',1)"><option value=1'+(U.dipNeg?' selected':'')+'>Negatif = ke bawah (Surpac)</option><option value=0'+(!U.dipNeg?' selected':'')+'>Positif = ke bawah</option></select></div></div>'+
    '<div class=hint>Collar: HoleID, East, North, RL, Azimuth, Dip, Depth. Assay: HoleID, From, To, kadar. Channel = lubang dengan dip 0. Total: <b>'+AM.holes.length+'</b> lubang/channel, <b>'+AM.comps.length+'</b> komposit. Tanpa data sampel, kadar poligon = model GC.</div>';
  /* 3. flitch & poligon */
  h+='<div class=amh>Flitch &amp; poligon aktual</div><div class=g3><div><label>Tinggi flitch</label><input type=number step=any value="'+amE(L.fh)+'" onchange="lySet(\'fh\',this.value);amPanel()"></div><div><label>RL atas</label><input type=number step=any value="'+B[0]+'" onchange="lyU().bot=\'\';lySet(\'top\',this.value);amPanel()"></div><div><label>RL bawah</label><input type=number step=any value="'+B[1]+'" onchange="lySet(\'bot\',this.value);amPanel()"></div></div>'+
    '<button class="'+(on?'':'btn-pri')+'" style="width:100%;margin-top:4px" onclick="amApply()">'+(on?'&#10003; Flitch aktif di Penampang 2D':'Terapkan flitch (buka Penampang 2D)')+'</button>'+
    '<div class=amset><div class=amst><b>Titik pick-up LANTAI (floor) penggalian</b>'+((D.pts||[]).length?'<button class=x onclick="amPtsClear()" title="Hapus semua titik lantai">&times;</button>':'')+'</div>'+
    '<label class="mdbtn'+((D.pts||[]).length?' ok':'')+'" style="margin:0;text-align:center"><input type=file multiple accept=".csv,.txt,.str,.dxf" onchange="amPtsFile(this.files);this.value=\'\'">&#8679; Import pick-up lantai (.csv / .txt / .str / .dxf)</label>'+
    '<div class=hint>'+((D.pts||[]).length?'<b>'+D.pts.length.toLocaleString()+'</b> titik lantai &middot; tampil di flitch ini: <b>'+amPtsNear().length.toLocaleString()+'</b>':'Titik lantai hasil survey pick-up. Disimpan TERPISAH dari titik atap. CSV: ID, X/East, Y/North, Z/RL, Kode.')+(AM.pmsg?' &middot; '+AM.pmsg:'')+'</div>'+
    ((D.pts||[]).length?'<div class=g2><label class=sw><input type=checkbox '+(D.pAll?'checked':'')+' onchange="amD().pAll=this.checked;amPanel();updatePlot()">Semua RL</label><label class=sw><input type=checkbox '+(D.plab?'checked':'')+' onchange="amD().plab=this.checked;updatePlot()">Label ID / kode</label></div>':'')+'</div>'+
    (window.amRoofBox?amRoofBox():'')+(window.amFloorBox?amFloorBox():'')+'<div class=amset><div class=amst><b>Default poligon berikutnya</b><small>'+amE(R.pit||lyZone())+' &middot; '+amE(amDateTxt(R.date))+' &middot; '+amE(R.shift)+'</small></div><div class=g2><div><label>Block</label><input type=text value="'+amE(R.block)+'" placeholder="mis. 15" onchange="amRSet(\'block\',this.value)"></div><div><label>Shift</label>'+sel(R.shift,[['DS','DS · Siang'],['NS','NS · Malam']],"amRSet('shift',this.value)")+'</div></div></div>'+
    (AM.digOn?'<div class=amdig><b>&#9679; Mendigit poligon</b> &mdash; klik di Penampang 2D'+((D.pts||[]).length?' (menempel ke titik pick-up)':'')+', klik titik pertama untuk menutup.<div class=g2 style="margin-top:4px"><button class=btn-pri onclick="dgFinish(true)">Tutup &amp; simpan</button><button onclick="dgCancel()">Batal</button></div></div>':
      '<button class=btn-pri style="width:100%;margin-top:6px" onclick="amDig()">&#9998; Digit poligon as-mined'+((D.pts||[]).length?' (snap ke pick-up)':'')+'</button>')+
    '<div class=g2 style="margin-top:6px"><label class=mdbtn style="margin:0;text-align:center"><input type=file multiple accept=".str,.dxf,.csv,.txt" onchange="amBndFile(this.files);this.value=\'\'">&#8679; Import boundary (.str / .dxf / .csv pick-up OB)</label><button onclick="amBndFromDig()" title="Salin string tertutup dari menu Digitasi / dig block di flitch ini">Ambil dari Digitasi</button></div>'+
    (AM.bmsg?'<div class=hint>'+AM.bmsg+'</div>':'')+
    (CUR.length?'<div class=amlist>'+CUR.map(function(I){var x=I.x;return '<div class="amrow ampl'+(AM.last===x.id?' new':'')+'"><input type=checkbox '+(x.on?'checked':'')+' onchange="amBndOn(\''+x.id+'\',this.checked)" title="Dipakai"><span><i class=amsw style="background:'+I.col+'">'+I.sid+'</i><code>'+amE(I.code)+'</code><small>Block <input class=amblk value="'+amE(x.blk)+'" placeholder="?" onchange="amPSet(\''+x.id+'\',\'blk\',this.value)"> &middot; '+I.area.toFixed(1)+' m&sup2;'+(window.amFlTxt?amFlTxt(I):'')+(I.calc?' &middot; '+lyFmt(I.ton.toFixed(0))+' t @ '+amF(I.gA,2):'')+'</small></span><button class=x onclick="amBndDel(\''+x.id+'\')" title="Hapus poligon">&times;</button></div>';}).join('')+'</div>':'<div class=hint>Belum ada poligon di flitch RL '+lyFmt(B[0])+'&ndash;'+lyFmt(B[1])+'. Isi Block lalu klik Digit poligon, atau import boundary.</div>');
  /* 4. parameter */
  h+='<div class=amh>Parameter estimasi (samakan dengan model resmi)</div><div class=amcm><label>Metode tonase (sama dengan Dig block)</label><select onchange="lyU().calcM=this.value;bxSGset(\'_x\',Date.now())"><option value=clip'+(lyCalcM()==='surpac'?'':' selected')+'>Presisi GC-Ex (sub-blok dipotong di garis boundary)</option><option value=surpac'+(lyCalcM()==='surpac'?' selected':'')+'>Seperti Surpac (blok utuh, titik tengah di dalam boundary &amp; flitch)</option></select><div class=hint>'+amE(amSGTxt())+' &middot; ubah di Block Model &rarr; Filter &amp; SG. Tonase &amp; kadar poligon dihitung dari sub-blok yang sama.</div></div><div><label>Metode as-mined</label><select onchange="amSet(\'mode\',this.value)"><option value=upd'+(U.mode!=='full'?' selected':'')+'>Update model GC (warisan + koreksi data baru)</option><option value=full'+(U.mode==='full'?' selected':'')+'>Estimasi ulang penuh (OK dari data yang diimport)</option></select></div>'+
    '<div class=hint>'+(U.mode!=='full'?'Sub-blok mewarisi kadar &amp; atribut model GC. Di sekitar data baru, selisih (data baru &minus; model GC) dikriging lalu ditambahkan ke kadar model GC.':'Kadar sub-blok diestimasi ulang dengan Ordinary Kriging hanya dari data yang diimport.')+' Sub-blok tanpa data baru dalam radius search mewarisi model GC.</div><div class=g3 style="margin-top:4px"><div><label>Atribut kadar</label><select onchange="amSet(\'attr\',this.value)">'+nums.map(function(a){return '<option'+(a===U.attr?' selected':'')+'>'+amE(a)+'</option>';}).join('')+'</select></div>'+inp('tc','Top-cut (kosong = tidak)')+inp('nd','Diskretisasi / sumbu','1')+'</div>'+
    '<div class=g3 style="margin-top:4px">'+inp('R','Radius search (m)')+inp('minS','Min sampel','1')+inp('maxS','Maks sampel','1')+'</div>'+
    '<div class=g3 style="margin-top:4px">'+inp('c0','Nugget C0')+inp('c1','Sill C1 (sferis)')+inp('a','Range a (m)')+'</div>'+
    '<div class=hint>Variogram isotropik satu zona. Ag &amp; SxS poligon diambil dari model GC (warisan).</div>';
  /* 5. register */
  var any=BC.some(function(x){return x.on;});
  h+='<div class=amh>Register poligon</div><div class=g2><button class=btn-pri onclick="amRun()"'+(any?'':' disabled')+'>&#9881; Hitung flitch RL '+lyFmt(B[0])+'&ndash;'+lyFmt(B[1])+'</button><label class=sw style="align-self:center"><input type=checkbox '+(R.auto?'checked':'')+' onchange="amRSet(\'auto\',this.checked)">Hitung otomatis</label></div>'+
    '<label class=sw style="margin-top:4px"><input type=checkbox '+(AM.show?'checked':'')+' onchange="AM.show=this.checked;updatePlot()">Tampilkan poligon, label &amp; sub-blok di Penampang 2D</label>'+(AM.msg?'<div class=hint style="margin-top:4px">'+AM.msg+'</div>':'');
  if(ALL.length){var ttot=0,mtot=0,flt={};ALL.forEach(function(I){var k=lyFmt(I.x.top)+'_'+lyFmt(I.x.bot);(flt[k]=flt[k]||{top:I.x.top,bot:I.x.bot,L:[]}).L.push(I);});
    Object.keys(flt).sort(function(a,b){return flt[b].top-flt[a].top;}).forEach(function(k){var F=flt[k],act=Math.abs(F.top-B[0])<1e-6&&Math.abs(F.bot-B[1])<1e-6,ft=0,fm=0;
      h+='<div class="amflt'+(act?' on':'')+'"><b>Flitch RL '+lyFmt(F.top)+'&ndash;'+lyFmt(F.bot)+'</b>'+(act?' <small>(aktif)</small>':' <a href="#" onclick="lySet(\'fh\','+(F.top-F.bot)+');lyU().bot=\'\';lySet(\'top\','+F.top+');amApply();return false">buka</a>')+'</div><div class=amreg>';
      F.L.forEach(function(I){var x=I.x;if(I.calc&&x.on){ft+=I.ton;if(isFinite(I.gA))fm+=I.gA*I.ton;}
        h+='<div class="amr'+(x.open?' open':'')+(x.on?'':' off')+(I.dup?' dup':'')+'"><div class=amrh><input type=checkbox '+(x.print!==false?'checked':'')+' onchange="amPSet(\''+x.id+'\',\'print\',this.checked)" title="Ikut layout &amp; export"><i class=amsw style="background:'+I.col+'">'+I.sid+'</i><code title="'+amE(I.code)+'" onclick="amPOpen(\''+x.id+'\')">'+amE(I.code)+'</code><button class=ed onclick="amPOpen(\''+x.id+'\')" title="Edit register">&#9998;</button></div>'+
          '<div class=amrs>'+(I.calc?'<b>'+lyFmt(I.ton.toFixed(1))+' t</b> @ '+amF(I.gA,2)+' g/t &middot; '+amE(I.ore)+' &rarr; '+amE(I.lok||I.dest||'?'):'<span class=warn>belum dihitung</span>')+' &middot; '+amE(I.x.shift)+' '+amE(amDateTxt(I.x.date))+(I.dup?' &middot; <span class=warn>kode kembar</span>':'')+(I.stale?' &middot; <span class=warn>metode / SG berubah: hitung ulang</span>':'')+'</div>';
        if(x.open){var oreOpts=[['','auto ('+I.oreAuto+')']];R.cls.concat([R.ws]).forEach(function(c){['SF','OX',''].forEach(function(o){var v=c.m+o;oreOpts.push([v,v]);});});
          var dOpts=[['','auto ('+(I.calc&&amDst(I.ore)?amDst(I.ore).d:'-')+')']];var dseen={};R.dst.forEach(function(q){if(q.d&&!dseen[q.d]){dseen[q.d]=1;dOpts.push([q.d,q.d+' · '+q.l]);}});
          h+='<div class=amed><div class=g2><div><label>Pit</label><input value="'+amE(x.pit)+'" onchange="amPSet(\''+x.id+'\',\'pit\',this.value)"></div><div><label>Block</label><input value="'+amE(x.blk)+'" onchange="amPSet(\''+x.id+'\',\'blk\',this.value)"></div></div><div class=g2><div><label>Shift</label>'+sel(x.shift,[['DS','DS · Siang'],['NS','NS · Malam']],"amPSet('"+x.id+"','shift',this.value)")+'</div>'+
            '<div><label>Tanggal</label><input type=date value="'+amE(x.date)+'" onchange="amPSet(\''+x.id+'\',\'date\',this.value)"></div><div><label>Kode ore</label>'+sel(x.ore,oreOpts,"amPSet('"+x.id+"','ore',this.value)")+'</div></div><div class=g2><div><label>Tujuan</label>'+sel(x.dest,dOpts,"amPSet('"+x.id+"','dest',this.value)")+'</div><div><label>String ID</label><input type=number value="'+amE(x.sid)+'" placeholder="'+I.sid+'" onchange="amPSet(\''+x.id+'\',\'sid\',this.value)"></div></div><div class=g2><div><label>Warna poligon</label><input type=color value="'+amE(I.col)+'" onchange="amPSet(\''+x.id+'\',\'col\',this.value)" title="Warna poligon di peta, layout &amp; register"></div><div><label>&nbsp;</label><button style="width:100%" onclick="amPSet(\''+x.id+'\',\'col\',\'\')" title="Kembali ke warna bawaan kode ore">&#8634; Warna otomatis</button></div></div><div class=g2><div><label>Densitas override</label><input type=number step=any value="'+amE(x.dens)+'" placeholder="'+amF(I.sgM,2)+'" onchange="amPSet(\''+x.id+'\',\'dens\',this.value)"></div><div><label>Kode manual</label><input value="'+amE(x.code)+'" placeholder="auto" onchange="amPSet(\''+x.id+'\',\'code\',this.value)"></div></div>'+
            '<div><label>Keterangan</label><input value="'+amE(x.ket)+'" onchange="amPSet(\''+x.id+'\',\'ket\',this.value)"></div>'+
            (I.calc?'<table class="pltb amt amkv"><tr><td>Luas</td><td>'+I.area.toFixed(1)+' m&sup2;</td><td>BCM</td><td>'+I.bcm.toFixed(1)+'</td></tr><tr><td>Densitas</td><td>'+amF(I.dens,2)+'</td><td>Ton</td><td><b>'+I.ton.toFixed(1)+'</b></td></tr><tr><td>'+amE(U.attr)+' as-mined</td><td><b>'+amF(I.gA,3)+'</b></td><td>'+amE(U.attr)+' model</td><td>'+amF(I.gO,3)+'</td></tr><tr><td>'+amE(R.ag||'Ag')+'</td><td>'+amF(I.ag,2)+'</td><td>'+amE(R.sxs||'SxS')+'</td><td>'+amF(I.sx,2)+'</td></tr>'+amElRows(I)+'<tr><td>Jenis ore</td><td>'+amE(I.jenis)+'</td><td>Lokasi</td><td>'+amE(I.lok)+' <small>'+amE(I.jl)+'</small></td></tr><tr><td>Sub-blok</td><td>'+(I.st.n||0)+'</td><td>Data baru</td><td>'+I.pu.toFixed(0)+'% ton</td></tr></table>':'')+
            '<div class=g2 style="margin-top:4px"><button onclick="amPOpen(\''+x.id+'\')">Tutup</button><button class=dn onclick="if(confirm(\'Hapus poligon '+amE(I.code).replace(/'/g,'')+'?\'))amBndDel(\''+x.id+'\')">Hapus poligon</button></div></div>';}
        h+='</div>';});
      h+='</div><div class=amft>Total flitch: <b>'+lyFmt(ft.toFixed(1))+' t</b> @ '+(ft?(fm/ft).toFixed(2):'-')+' g/t</div>';ttot+=ft;mtot+=fm;});
    h+='<div class=amft style="border-top:2px solid var(--pr)">Total register ('+ALL.length+' poligon): <b>'+lyFmt(ttot.toFixed(1))+' t</b> @ '+(ttot?(mtot/ttot).toFixed(3):'-')+' g/t'+(Rw.length?' &middot; F1 kadar vs model '+amD2(T):'')+'</div>';}
  else h+='<div class=hint>Belum ada poligon. Digit atau import boundary di tab <b>Poligon</b>.</div>';
  /* 6. layout & export */
  var np=ALL.filter(function(I){return I.x.print!==false&&I.calc;}).length,nst=ALL.filter(function(I){return I.calc&&I.stale;}).length;
  h+='<div class=amh>Layout &amp; export</div>'+elBox(U.attr)+'<div class=hint style="margin-top:0">'+np+' poligon tercentang &amp; sudah dihitung. Kertas, skala &amp; layer mengikuti pengaturan <b>Block Model &rarr; Layout PDF</b>.</div>'+
    '<div><label>Cakupan</label>'+sel(R.lyAll?'all':'cur',[['cur','Flitch aktif saja'],['all','Semua flitch di register']],"amRSet('lyAll',this.value==='all')")+'</div>'+
    '<div class=sws style="margin-top:4px"><label class=sw><input type=checkbox '+(R.lyBlk!==false?'checked':'')+' onchange="amRSet(\'lyBlk\',this.checked)">Blok BM (warna kadar)</label><label class=sw><input type=checkbox '+(R.lyPit?'checked':'')+' onchange="amRSet(\'lyPit\',this.checked)">Garis desain pit</label><label class=sw><input type=checkbox '+(R.lyTopo?'checked':'')+' onchange="amRSet(\'lyTopo\',this.checked)">Kontur topografi</label></div>'+
    '<div class=g2 style="margin-top:4px"><button onclick="amLyPreview()"'+(np?'':' disabled')+'>&#128065; Pratinjau layout</button><button class=btn-pri onclick="amLyPdf()"'+(np?'':' disabled')+'>&#8681; Layout PDF</button></div>'+
    '<div class=amset><div class=amst><b>Register untuk database</b></div><div><label>Format angka</label>'+sel(R.sep,[['id','Excel Indonesia ( ; dan desimal koma)'],['en','Internasional ( , dan desimal titik)']],"amRSet('sep',this.value)")+'</div>'+
    '<div class=g2 style="margin-top:4px"><button class=btn-pri onclick="amRegCopy()"'+(np?'':' disabled')+' title="Salin kolom input A&ndash;H (tanpa header) untuk ditempel ke sheet register">&#128203; Salin ke Excel</button><button onclick="amRegCsv()"'+(np?'':' disabled')+'>&#8681; Register CSV</button></div>'+
    '<div class=hint>Salin ke Excel = kolom input A&ndash;H register (Kode &hellip; Model Au); kolom rumus Excel tidak ikut supaya tidak tertimpa. Register CSV = semua kolom'+(amElReg().length?' + '+amElReg().length+' kolom elemen tambahan':'')+'.</div><div id=amRegMsg class=hint></div></div>'+amXlBox()+
    (nst?'<div class=amstale>&#9888; <b>'+nst+'</b> poligon dihitung dengan metode / aturan SG lama. Buka flitch-nya lalu klik Hitung sebelum export.</div>':'')+'<div class=amaud>Metode aktif: <b>'+amE(amCMTxt())+'</b> &middot; '+amE(amSGTxt())+'</div><button style="width:100%;margin-top:4px" onclick="amAuditCsv()"'+(np?'':' disabled')+'>&#128269; Audit blok per poligon as-mined (CSV)</button>'+
    '<div class=g2 style="margin-top:6px"><button onclick="amStr()"'+(np?'':' disabled')+'>&#8681; String poligon (.str)</button><button onclick="amPdf()"'+(Rw.length?'':' disabled')+'>&#8681; Report rekonsiliasi</button></div>'+
    '<div class=g3 style="margin-top:4px"><button onclick="amCsv()"'+(Rw.length?'':' disabled')+'>&#8681; Rekon CSV</button><button onclick="amCells()"'+(Rw.length?'':' disabled')+'>&#8681; Sub-blok CSV</button><button onclick="amMdl()"'+(Rw.length&&!(G.L<0||!m.mdl||!m.mdl.hraw)?'':' disabled title="Butuh block model resmi dari file .mdl dan hasil hitung"')+'>&#8681; .mdl</button></div>'+
    '<div class=g2 style="margin-top:4px"><div><label>Periode / nama</label><input type=text value="'+amE(U.period)+'" placeholder="mis. 2026-10" onchange="amSet(\'period\',this.value,2)"></div></div>';
  el.innerHTML=h;}
/* ---------- peta 2D: poligon berwarna kelas + label kode ---------- */
function amTraces2D(){amD();var B=lyBench(),r=AM.res[lyFmt(B[0])+'_'+lyFmt(B[1])],out=[],U=amU();
  if(r){var G=amGrid(),col={},a=r.attr,L=bxCls(a);r.cells.forEach(function(c){var k=c.ix+'|'+c.iy,q=col[k]||(col[k]={x:c.x,y:c.y,g:0,t:0,est:0});c.est=c.est||0;if(isFinite(c.g)){q.g+=c.g*c.t;q.t+=c.t;}q.est=Math.max(q.est,c.est);});
    var grp={};Object.keys(col).forEach(function(k){var q=col[k],v=q.t?q.g/q.t:NaN,cls=-1;for(var j=0;j<L.length;j++){var c2=L[j];if((c2.lo===null||v>=c2.lo)&&(c2.hi===null||v<c2.hi)){cls=j;break;}}(grp[cls+'|'+q.est]=grp[cls+'|'+q.est]||[]).push(q);});
    Object.keys(grp).forEach(function(k){var X=[],Y=[],kk=k.split('|'),cn=+kk[0],ue=kk[1]==='1',c=cn>=0?L[cn]:null;grp[k].forEach(function(q){var x0=q.x-G.dx/2,x1=q.x+G.dx/2,y0=q.y-G.dy/2,y1=q.y+G.dy/2;X.push(x0,x1,x1,x0,x0,null);Y.push(y0,y0,y1,y1,y0,null);});
      out.push({type:'scatter',mode:'lines',x:X,y:Y,fill:'toself',fillcolor:c?c.col:'#999',opacity:ue?0.9:0.55,line:{width:ue?0.6:0.3,color:ue?'#1a1a1a':'#7a7a7a'},name:'Sub-blok '+(ue?'data baru ':'warisan GC ')+a+' '+(c?bxLab(c):'?')+' ('+grp[k].length+')',hoverinfo:'name',showlegend:true,legendgroup:'amsub'});});}
  var I=amAllInfo().filter(function(I){return Math.abs(I.x.top-B[0])<1e-6&&Math.abs(I.x.bot-B[1])<1e-6&&I.x.on;}),byC={};
  I.forEach(function(q){var k=q.col+'|'+q.sid+'|'+q.cls;(byC[k]=byC[k]||[]).push(q);});
  Object.keys(byC).forEach(function(k){var X=[],Y=[],kk=k.split('|');byC[k].forEach(function(q){q.x.pts.concat([q.x.pts[0]]).forEach(function(p){X.push(p[0]);Y.push(p[1]);});X.push(null);Y.push(null);});
    out.push({type:'scatter',mode:'lines',x:X,y:Y,line:{color:kk[0],width:3},name:'Poligon as-mined '+kk[2]+' · str '+kk[1]+' ('+byC[k].length+')',hoverinfo:'name',showlegend:true});});
  if(I.length){var lx=[],ly=[],lt=[],hv=[];I.forEach(function(q){var p=lyLabelPt(q.x.pts);lx.push(p[0]);ly.push(p[1]);lt.push('<b>'+q.code+'</b>'+(q.calc?'<br>'+q.ton.toFixed(0)+' t @ '+amF(q.gA,2):''));hv.push(q.code+'<br>'+(q.calc?q.ton.toFixed(1)+' t @ '+amF(q.gA,3)+' g/t · '+q.ore+' → '+(q.lok||q.dest):'belum dihitung'));});
    out.push({type:'scatter',mode:'text',x:lx,y:ly,text:lt,hovertext:hv,hoverinfo:'text',textfont:{size:11,color:'#111',family:'Arial'},name:'Label poligon',showlegend:false});}
  var lo=B[1]-3,hi=B[0]+3,cx=[],cy=[],tx=[],lx2=[],ly2=[];AM.holes.forEach(function(h){var p=h.path,ok=p.some(function(q){return q.z>=lo&&q.z<=hi;});if(!ok)return;p.forEach(function(q){lx2.push(q.x);ly2.push(q.y);});lx2.push(null);ly2.push(null);});
  AM.comps.forEach(function(q){if(q.z<lo||q.z>hi)return;cx.push(q.x);cy.push(q.y);tx.push(q.g.toFixed(2));});
  if(lx2.length)out.push({type:'scatter',mode:'lines',x:lx2,y:ly2,line:{color:'#111',width:1.5},name:'Bor / channel',hoverinfo:'skip',showlegend:true});
  if(cx.length)out.push({type:'scatter',mode:'markers',x:cx,y:cy,text:tx,marker:{symbol:'diamond',size:6,color:'#ffd400',line:{color:'#111',width:1}},name:'Komposit '+U.comp+' m ('+cx.length+')',hoverinfo:'text',showlegend:true});
  return out;}
/* ---------- layout PDF (pakai mesin layout dig block) ---------- */
function amLyItems(I){return I.map(function(q,k){return{s:{id:'am_'+q.x.id,col:q.col,d:q.ore,no:q.sid,vis:true},r:q.x.pts,b:lyBB(q.x.pts),name:q.code,ton:{t:q.ton,grade:q.gA,attr:amU().attr,sulf:false,v:q.bcm,el:q.el,elA:q.elA},dest:q.lok||q.dest,area:q.area,am:q};});}
function amLyBuild(){var R=amR(),L=lyU(),B0=lyBench(),all=amAllInfo().filter(function(I){return I.x.print!==false&&I.calc&&I.x.on;});
  if(!R.lyAll)all=all.filter(function(I){return Math.abs(I.x.top-B0[0])<1e-6&&Math.abs(I.x.bot-B0[1])<1e-6;});
  if(!all.length){alert('Belum ada poligon as-mined yang dicentang dan sudah dihitung.');return null;}
  var flt={};all.forEach(function(I){var k=lyFmt(I.x.top)+'_'+lyFmt(I.x.bot);(flt[k]=flt[k]||{top:I.x.top,bot:I.x.bot,L:[]}).L.push(I);});
  var keep={top:L.top,bot:L.bot,title:L.title,pit:L.pit,topo:L.topo,blk:L.blk};L.pit=!!R.lyPit;L.topo=!!R.lyTopo;L.blk=R.lyBlk!==false;var pages=[],items=[],noAll=0;
  try{Object.keys(flt).sort(function(a,b){return flt[b].top-flt[a].top;}).forEach(function(k){var F=flt[k];L.top=F.top;L.bot=F.bot;LY.ix=null;LY.fc=null;L.title='Peta As-Mined '+String(R.pit||'{ZONE}')+' RL {TOP} - {BOT}';
      var it=amLyItems(F.L);it.forEach(function(o){o.no=++noAll;});items=items.concat(it);
      var opt=function(side,pn){return{img:lyOrthoImg,side:side,planNo:pn};},G=L.mode==='one'?[it]:(L.mode==='each'?it.map(function(o){return[o];}):lyGroups(it,Math.max(0,parseFloat(L.gap)||0)));
      G.forEach(function(g){var pg=lyPage(g,opt(g.length>1?g[0].name+' (+'+(g.length-1)+')':g[0].name,String(pages.length+1)));amLyFix(pg,F);pages.push(pg);});});}
  finally{L.top=keep.top;L.bot=keep.bot;L.title=keep.title;L.pit=keep.pit;L.topo=keep.topo;L.blk=keep.blk;LY.ix=null;LY.fc=null;}
  if(L.sum)pages.push(amLySummary(items));LY.pages=pages;LY.items=items;LY.am=true;return pages;}
function amLyFix(pg,F){pg.ops.forEach(function(o){if(o.t!=='text'||typeof o.txt!=='string')return;
  if(o.txt==='Keterangan dig block')o.txt='Keterangan poligon as-mined';else if(/^TOTAL \(\d+ dig block\)$/.test(o.txt))o.txt=o.txt.replace('dig block','poligon');
  else if(/^Ton = /.test(o.txt))o.txt='Metode: '+amCMTxt()+'; '+amSGTxt()+'. Ton & kadar '+amU().attr+' dari sub-blok yang sama (model GC + koreksi data sampel), flitch RL '+lyFmt(F.top)+'-'+lyFmt(F.bot);
  else if(/^GC-Ex  BLOCK MODEL/.test(o.txt))o.txt=o.txt.replace('BLOCK MODEL','AS-MINED');});}
function amLySummary(items){var L=lyU(),R=amR(),U=amU(),ps=PAPER[L.paper]||PAPER.A4,W=Math.max(ps[0],ps[1]),H=Math.min(ps[0],ps[1]),ops=[],y=H-24,sc=W/297;
  var tx=function(x,yy,s,t,f,c,an){ops.push({t:'text',x:x*sc,y:yy,s:s,txt:String(t),col:c||'#000',font:f||'H',anchor:an});};
  tx(15,H-15,5,'Register poligon as-mined'+(U.period?' - '+U.period:''),'B');tx(15,H-20.5,2.8,(L.company?L.company+'  |  ':'')+'Zona '+lyZone()+'  |  model '+((BX.m.mdl&&BX.m.mdl.file)||BX.m.name)+'  |  '+lyDateTxt(),'H','#444');
  /* elemen: utama (as-mined) + Ag/SxS register + elemen yang dicentang */
  var EL=amElCols(),n=EL.length,ew=n>5?11:13,kw=Math.max(40,62-Math.max(0,n*ew-65)),fs=n>5?2.1:2.4,x=13,cols=[];
  [['No',7],['Kode poligon',kw],['Ore',13],['Tujuan',18],['Luas m2',17],['BCM',16],['Dens',12],['Ton',17]].forEach(function(c){cols.push([x,c[0],c[1]]);x+=c[1];});
  EL.forEach(function(a){cols.push([x,a,ew,a]);x+=ew;});cols.push([x,'Model t',18]);x+=18;cols.push([x,'Model '+U.attr,18]);x+=18;cols.push([x,'Shift',12]);
  y-=8;ops.push({t:'rect',x:11*sc,y:y-1.8,w:(W-22*sc),h:6,fill:'#e8edf5'});cols.forEach(function(c){tx(c[0],y,fs+0.1,c[1],'B');});var T=elAgg(),TM={t:0,m:0},TA={a:0,v:0},DS={};
  var gv=function(q,a){return a===U.attr?q.gA:(q.el&&a in q.el?q.el[a]:(a===R.ag?q.ag:(a===R.sxs?q.sx:NaN)));};
  var rr=function(q){var o={t:q.ton,el:{}};EL.forEach(function(a){o.el[a]=gv(q,a);});return o;};
  items.forEach(function(o,i){var q=o.am;y-=5.6;T.add(rr(q),q.ton);TA.a+=q.area;TA.v+=q.bcm;TM.t+=q.tM;if(isFinite(q.gO))TM.m+=q.gO*q.tM;var d=q.lok||q.dest||'-';(DS[d]=DS[d]||elAgg()).add(rr(q),q.ton);
    if(y<16)return;ops.push({t:'circ',x:14.5*sc,y:y+0.7,r:1.4,fill:q.col});
    var v=[String(o.no||i+1),q.code,q.ore,q.dest,q.area.toFixed(1),q.bcm.toFixed(1),amF(q.dens,2),q.ton.toFixed(1)].concat(EL.map(function(a){return elF(a,gv(q,a));})).concat([q.tM.toFixed(1),amF(q.gO,2),q.x.shift]);
    v.forEach(function(s,k){tx(cols[k][0]+(k===0?4:0),y,k===1?2.1:fs,s,k===1?'C':'H');});ops.push({t:'line',pts:[[11*sc,y-1.9],[W-11*sc,y-1.9]],col:'#d5dbe3',lw:0.12});});
  var ne=8,tot=function(lab,A,c,small){y-=small?5:6.5;if(y<16)return;tx(20,y,small?2.4:2.7,lab,'B',c);if(!small){tx(cols[4][0],y,2.6,TA.a.toFixed(1),'B');tx(cols[5][0],y,2.6,TA.v.toFixed(1),'B');}tx(cols[7][0],y,small?2.4:2.6,A.t.toFixed(1),small?'H':'B',c);
    EL.forEach(function(a,k){tx(cols[ne+k][0],y,small?2.3:2.5,elF(a,A.g(a)),small?'H':'B',c);});if(!small){tx(cols[ne+n][0],y,2.6,TM.t.toFixed(1),'B');tx(cols[ne+n+1][0],y,2.6,TM.t?(TM.m/TM.t).toFixed(2):'-','B');}};
  tot('TOTAL ('+items.length+' poligon)',T);Object.keys(DS).forEach(function(k){tot('ke '+k+' ('+DS[k].n+' poligon)',DS[k],'#233a7e',true);});
  if(y>26){y-=6;tx(20,y,2.4,'Metal total: '+EL.filter(function(a){return elMetU(a);}).map(function(a){return a+' '+elMetF(a,T.met(a))+' '+elMetU(a);}).join('   |   '),'B','#233a7e');}
  tx(15,13.5,2.1,'Metode tonase: '+amCMTxt()+'  |  '+amSGTxt(),'B','#233a7e');tx(15,10,2.1,'Ton & BCM = jumlah sub-blok di dalam poligon (atau BCM x densitas override). '+U.attr+' = as-mined (model GC + koreksi channel / bor GC); elemen lain dari model GC pada sub-blok yang sama (rata-rata tertimbang ton).','H','#555');tx(15,7,2.1,'Model t & '+U.attr+' = model resmi sebelum koreksi (F1). Kode ore = kelas + SF/OX (SF bila SxS > '+R.sxsThr+').','H','#555');
  return{W:W,H:H,ops:ops,scale:0};}
/* ---------- multi-elemen as-mined ---------- */
function amElCols(){var U=amU(),R=amR(),L=elList(U.attr);[R.ag,R.sxs].forEach(function(a){if(a&&L.indexOf(a)<0&&BX.m&&BX.m.num[a])L.splice(1,0,a);});
  var seen={};return L.filter(function(a){if(seen[a])return false;seen[a]=1;return true;});}
/* elemen tambahan di luar Ag & SxS (kolom tambahan register: "GC <elemen> (<satuan>)") */
function amElReg(){var U=amU(),R=amR();return elExtra(U.attr).filter(function(a){return a!==R.ag&&a!==R.sxs;});}
function amElRows(I){var L=amElReg().filter(function(a){return I.el&&a in I.el;});if(!L.length)return '';var h='';for(var k=0;k<L.length;k+=2){h+='<tr>'+[L[k],L[k+1]].map(function(a){return a?'<td>'+amE(a)+'</td><td>'+elF(a,I.el[a])+(elUnit(a)&&elUnit(a)!=='g/t'?' '+amE(elUnit(a)):'')+'</td>':'<td></td><td></td>';}).join('')+'</tr>';}return h;}
function amRegH(){return AMREGH.concat(amElReg().map(function(a){return 'GC '+a+(elUnit(a)?' ('+elUnit(a)+')':'');}));}
function amLyPreview(){var P=amLyBuild();if(!P)return;LY.pi=0;var d=$('lyDlg');if(!d){d=document.createElement('div');d.id='lyDlg';document.body.appendChild(d);}d.style.display='flex';lyShow();}
function amLyName(){var U=amU(),R=amR(),B=lyBench();return 'AsMined_Layout_'+String(R.pit||lyZone()).replace(/[^A-Za-z0-9_-]+/g,'_')+'_'+(R.lyAll?'semua':lyNum(B[0])+'-'+lyNum(B[1]))+(U.period?'_'+String(U.period).replace(/[^A-Za-z0-9_-]+/g,'_'):'')+'.pdf';}
function amLyPdf(keep){var P=keep&&LY.am&&LY.pages.length?LY.pages:amLyBuild();if(!P)return;var b=lyPdf(P),fn=amLyName();dgDl(b,fn,'application/pdf');var e=$('amRegMsg');if(e)e.textContent=P.length+' halaman layout → '+fn;}
(function(){var _b=window.lyBuild;if(_b)lyBuild=function(){LY.am=false;return _b.apply(this,arguments);};var _g=window.lyPdfGo;if(_g)lyPdfGo=function(keep){if(keep&&LY.am)return amLyPdf(1);return _g.apply(this,arguments);};})();
/* ---------- register CSV / salin ke Excel / STR ---------- */
var AMREGH=['Kode Poligon GC','Volume As-mined (BCM)','Densitas Override','GC Au (g/t)','GC Ag (g/t)','GC SxS (%)','Model Tonnes (ops)','Model Au g/t (ops)','Ritase Truck Count','TF (wt/rit, ops)','Keterangan','Pit','Flitch / Elevasi','Block','Tgl+Shift','Kode Ore','Kode Tujuan','Tanggal','Shift','Jenis Ore','Tujuan (Lokasi)','Jenis Lokasi','Densitas Dipakai',
  'Tonase As-mined (t)','Luas (m2)','RL Atas','RL Bawah','String ID','Warna','Sub-blok','Data Baru (% ton)','Metal (g)','Dihitung','Metode Tonase','Aturan SG','Perlu Hitung Ulang'];
function amRegRows(){var R=amR();return amAllInfo().filter(function(I){return I.x.print!==false&&I.calc&&I.x.on;}).sort(function(a,b){return b.x.top-a.x.top||String(a.code).localeCompare(String(b.code));}).map(function(I){var x=I.x;
  return[I.code,+I.bcm.toFixed(1),x.dens?+x.dens:'',+amF(I.gA,2)||0,isFinite(I.ag)?+I.ag.toFixed(2):'',isFinite(I.sx)?+I.sx.toFixed(2):'',+I.tM.toFixed(0),isFinite(I.gO)?+I.gO.toFixed(2):'','','',x.ket||'',x.pit||lyZone(),lyFmt(x.top),x.blk||'',amDDMM(x.date)+x.shift,I.ore,I.dest,amDateTxt(x.date),amShiftTxt(x.shift),I.jenis,I.lok,I.jl,+I.dens.toFixed(2),
    +I.ton.toFixed(1),+I.area.toFixed(1),x.top,x.bot,I.sid,I.col,I.st.n,+I.pu.toFixed(0),isFinite(I.gA)?+(I.gA*I.ton).toFixed(1):'',(I.st.at||'').slice(0,16).replace('T',' '),amCMTxt(I.cm),amSGTxt(),I.stale?'YA':''].concat(amElReg().map(function(e){var v=I.el?I.el[e]:NaN;return isFinite(v)?+v.toFixed(4):'';}));});}
function amFmtCell(v,dec,sep){if(typeof v==='number'){var s=String(v);if(dec===',')s=s.replace('.',',');return s;}var s2=String(v==null?'':v);if(s2.indexOf(sep)>=0||s2.indexOf('"')>=0||/[\r\n]/.test(s2))s2='"'+s2.replace(/"/g,'""')+'"';return s2;}
function amRegCsv(){var R=amR(),sep=R.sep==='en'?',':';',dec=R.sep==='en'?'.':',',U=amU(),rows=amRegRows();if(!rows.length)return;var out=[amRegH().map(function(h){return amFmtCell(h,dec,sep);}).join(sep)];rows.forEach(function(r){out.push(r.map(function(v){return amFmtCell(v,dec,sep);}).join(sep));});
  var fn='Register_AsMined_'+String(R.pit||lyZone()).replace(/[^A-Za-z0-9_-]+/g,'_')+'_'+(U.period?String(U.period).replace(/[^A-Za-z0-9_-]+/g,'_'):amToday())+'.csv';dgDl('﻿'+out.join('\r\n')+'\r\n',fn,'text/csv');var e=$('amRegMsg');if(e)e.textContent=rows.length+' baris → '+fn;}
function amRegCopy(){var R=amR(),dec=R.sep==='en'?'.':',',rows=amRegRows();if(!rows.length)return;var t=rows.map(function(r){return r.slice(0,8).map(function(v){return typeof v==='number'?String(v).replace('.',dec):String(v==null?'':v).replace(/[\t\r\n]+/g,' ');}).join('\t');}).join('\r\n');
  var done=function(ok){var e=$('amRegMsg');if(e)e.innerHTML=ok?'<b>'+rows.length+' baris</b> disalin (kolom input A&ndash;H, tanpa header). Klik sel kolom A baris kosong pertama di sheet register, lalu Ctrl+V; kolom rumus di sebelahnya akan terisi otomatis.':'<span class=warn>Browser menolak akses clipboard; pakai Register CSV.</span>';};
  try{navigator.clipboard.writeText(t).then(function(){done(true);},function(){done(amCopyFb(t));});}catch(er){done(amCopyFb(t));}}
function amCopyFb(t){try{var a=document.createElement('textarea');a.value=t;a.style.position='fixed';a.style.opacity='0';document.body.appendChild(a);a.select();var ok=document.execCommand('copy');a.remove();return ok;}catch(e){return false;}}
function amStr(){var R=amR(),U=amU(),L=amAllInfo().filter(function(I){return I.x.print!==false&&I.x.on;});if(!L.length)return;var d=new Date(),o=['AsMined_'+(U.period||amToday())+','+d.getDate()+'-'+AMMON[d.getMonth()]+'-'+String(d.getFullYear()).slice(2)+',,','0,           0.000,           0.000,           0.000,           0.000,           0.000,           0.000'];
  L.sort(function(a,b){return a.sid-b.sid;}).forEach(function(I){var P=I.x.pts.concat([I.x.pts[0]]),z=I.x.bot;P.forEach(function(p){o.push(I.sid+', '+p[1].toFixed(3)+', '+p[0].toFixed(3)+', '+(+z).toFixed(3)+', '+I.code+', '+I.ore+', '+I.dest);});o.push('0, 0.000, 0.000, 0.000,');});
  o.push('0, 0.000, 0.000, 0.000, END');var fn='AsMined_'+String(R.pit||lyZone()).replace(/[^A-Za-z0-9_-]+/g,'_')+'_'+(U.period?String(U.period).replace(/[^A-Za-z0-9_-]+/g,'_'):amToday())+'.str';dgDl(o.join('\r\n')+'\r\n',fn,'text/plain');var e=$('amRegMsg');if(e)e.textContent=L.length+' poligon → '+fn+' (Surpac string teks: StringId, Y, X, Z = RL bawah, D1 = kode, D2 = ore, D3 = tujuan)';}

/* ---------- audit blok per poligon as-mined ---------- */
function amAuditCsv(){var m=BX.m;if(!m)return;var U=amU(),R=amR(),I=amAllInfo().filter(function(q){return q.x.print!==false&&q.calc&&q.x.on;}),sgA=BX.ui.sgCol&&m.num[BX.ui.sgCol]?m.num[BX.ui.sgCol]:null,G=amGrid(),cv=G.dx*G.dy*G.dz;
  if(!I.length){alert('Belum ada poligon as-mined yang dihitung.');return;}var by={};I.forEach(function(q){by[q.x.id]=q;});
  var sep=R.sep==='en'?',':';',dec=R.sep==='en'?'.':',',f=function(v,d){if(v===''||v==null)return '';if(typeof v!=='number'){v=String(v);return v.indexOf(sep)>=0?'"'+v+'"':v;}return isFinite(v)?(d==null?String(v):v.toFixed(d)).replace('.',dec):'';};
  var A={};Object.keys(AM.res).forEach(function(k){AM.res[k].cells.forEach(function(c){var q=by[c.pid];if(!q)return;var key=c.pid+'|'+c.p,o=A[key]||(A[key]={q:q,p:c.p,n:0,v:0,t:0,gA:0,gO:0,ne:0,fr:0});var v=cv*(c.f||1);o.n++;o.v+=v;o.t+=c.t||0;o.fr+=(c.f||1);if(isFinite(c.g))o.gA+=c.g*(c.t||0);if(isFinite(c.go))o.gO+=c.go*(c.t||0);if(c.est)o.ne++;});});
  var out=[['Kode Poligon','X blok','Y blok','Z blok','DX','DY','DZ',(BX.ui.sgCol||'SG')+' asli','SG dipakai','Sub-blok','Fraksi sub-blok','Volume (m3)','Ton',U.attr+' model',U.attr+' as-mined','Sub-blok data baru','Titik tengah blok di dalam (Surpac)','Catatan'].join(sep)];
  Object.keys(A).sort().forEach(function(k){var o=A[k],i=o.p,raw=sgA?sgA[i]:NaN,cin=lyInS(o.q.x.pts,m.x[i],m.y[i])&&m.z[i]>o.q.x.bot+1e-9&&m.z[i]<=o.q.x.top+1e-9;
    out.push([o.q.code,f(m.x[i],3),f(m.y[i],3),f(m.z[i],3),f(m.sx[i],3),f(m.sy[i],3),f(m.sz[i],3),f(raw,4),f(bxSGv(raw),4),o.n,f(o.fr,4),f(o.v,4),f(o.t,4),f(o.t?o.gO/o.t:NaN,4),f(o.t?o.gA/o.t:NaN,4),o.ne,cin?'Ya':'Tidak',(sgA&&!(isFinite(raw)&&raw>0))?'SG<=0':''].join(sep));});
  out.push('');out.push(['RINGKASAN','Flitch','BCM','Ton','Densitas','Densitas override',U.attr+' model',U.attr+' as-mined','Metal (g)','Metode tonase','Aturan SG','Perlu hitung ulang'].join(sep));
  I.forEach(function(q){out.push([q.code,lyFmt(q.x.top)+'-'+lyFmt(q.x.bot),f(q.bcm,2),f(q.ton,2),f(q.ton/q.bcm,4),q.x.dens||'',f(q.gO,4),f(q.gA,4),f(q.gA*q.ton,2),amCMTxt(q.cm),amSGTxt(),q.stale?'YA':''].join(sep));});
  out.push('');out.push('Model: '+((m.mdl&&m.mdl.file)||m.name)+sep+'grid sub-blok '+G.dx+'x'+G.dy+'x'+G.dz+' m'+sep+'metode estimasi: '+(U.mode!=='full'?'Update model GC':'OK penuh')+sep+'dibuat '+new Date().toLocaleString());
  dgDl('﻿'+out.join('\r\n')+'\r\n','Audit_AsMined_'+String(R.pit||lyZone()).replace(/[^A-Za-z0-9_-]+/g,'_')+'_'+(U.period?String(U.period).replace(/[^A-Za-z0-9_-]+/g,'_'):amToday())+'.csv','text/csv');}

/* ---------- kirim register langsung ke workbook Excel (GC-Ex Desktop) ---------- */
function amXlOn(){return !!(window.gcexDesktop&&gcexDesktop.api);}
function amXlName(p){return String(p||'').split(/[\\/]/).pop();}
function amXlBox(){var R=amR(),np=amRegRows().length;
  if(!amXlOn())return '<div class=amset><div class=amst><b>Kirim ke workbook register Excel</b></div><div class=hint>Tersedia di <b>GC-Ex Desktop</b> (.exe): baris register ditulis langsung ke sheet register di workbook Anda (hanya kolom input, rumus tidak disentuh). Di versi browser pakai Salin ke Excel / Register CSV.</div></div>';
  var P=AM.xl&&AM.xl.path===R.xlPath?AM.xl:null;
  return '<div class=amset><div class=amst><b>Kirim ke workbook register Excel</b></div>'+
    '<div class=amxf title="'+amE(R.xlPath||'')+'">'+(R.xlPath?'&#128196; <b>'+amE(amXlName(R.xlPath))+'</b>'+(R.xlSheet?' &middot; sheet '+amE(R.xlSheet):''):'<i>Belum ada workbook dipilih</i>')+'</div>'+
    '<div><label>Kode yang sudah ada di workbook</label><select onchange="amRSet(\'xlMode\',this.value);AM.xl=null;amPanel()"><option value=skip'+(R.xlMode!=='update'?' selected':'')+'>Lewati (tidak diubah)</option><option value=update'+(R.xlMode==='update'?' selected':'')+'>Perbarui kolom input-nya</option></select></div>'+
    '<div class=g3 style="margin-top:4px"><button onclick="amXlPick()">&#128194; Pilih workbook&hellip;</button><button onclick="amXlPlan()"'+(R.xlPath&&np?'':' disabled')+'>&#128269; Periksa</button><button class=btn-pri onclick="amXlSend()"'+(P&&P.plan&&(P.plan.added+P.plan.updated)>0&&!P.busy?'':' disabled')+'>&#10148; Kirim'+(P&&P.plan?' '+(P.plan.added+P.plan.updated)+' baris':'')+'</button></div>'+
    '<div id=amXlMsg class=amxm>'+(P?amXlTxt(P):'<span class=hint>Periksa dulu: GC-Ex menunjukkan kolom yang akan diisi dan baris tujuannya, file belum diubah.</span>')+'</div></div>';}
function amXlTxt(P){if(P.busy)return '<span class=hint>&#8987; '+amE(P.busy)+'</span>';if(P.err)return '<span class=warn>&#9888; '+amE(P.err)+'</span>';var x=P.res||P.plan;if(!x)return '';
  var w=x.mapping.filter(function(m){return m.status==='ditulis';}),f=x.mapping.filter(function(m){return /^rumus/.test(m.status);}),miss=x.mapping.filter(function(m){return !m.column;});
  var h=P.res?'<div class=amxok>&#10004; <b>'+x.added+' baris baru</b>'+(x.updated?' + '+x.updated+' diperbarui':'')+' ditulis ke <b>'+amE(x.sheet)+'</b>'+(x.first_row?' baris '+x.first_row+'&ndash;'+x.last_row:'')+'.'+(x.backup?' Cadangan: <a href="#" onclick="gcexDesktop.showFile(\''+amE(String(x.backup).replace(/\\/g,'\\\\'))+'\');return false">'+amE(amXlName(x.backup))+'</a>':'')+' Buka workbook di Excel; rumus dihitung ulang saat dibuka.</div>':
    '<div>Sheet <b>'+amE(x.sheet)+'</b> &middot; header baris '+x.header_row+' &middot; kunci kolom '+amE(x.key_column)+': <b>'+x.added+' baris baru</b>'+(x.updated?', '+x.updated+' diperbarui':'')+(x.skipped.length?', '+x.skipped.length+' dilewati':'')+'.</div>';
  h+='<div class=hint>Diisi: '+w.map(function(m){return amE(m.header)+' &rarr; '+m.column;}).join(', ')+'</div>';
  if(f.length)h+='<div class=hint>Kolom rumus tidak ditimpa: '+f.map(function(m){return amE(m.header)+' ('+m.column+')';}).join(', ')+'</div>';
  if(miss.length)h+='<div class=hint>Tidak ada di sheet (dilewati): '+miss.map(function(m){return amE(m.header);}).join(', ')+'. Tambahkan header-nya di Excel bila ingin ikut terisi.</div>';
  if(x.rows&&x.rows.length&&!P.res)h+='<div class=amxr>'+x.rows.slice(0,40).map(function(r){return '<span>'+(r.action==='baru'?'+':'&#8635;')+' '+r.row+' &middot; '+amE(r.code)+'</span>';}).join('')+(x.rows.length>40?'<span>&hellip; '+(x.rows.length-40)+' lainnya</span>':'')+'</div>';
  if(x.skipped.length)h+='<div class=hint>Dilewati: '+x.skipped.slice(0,12).map(function(s){return amE(s.code)+' ('+amE(s.reason)+')';}).join('; ')+(x.skipped.length>12?' &hellip;':'')+'</div>';
  (x.warnings||[]).forEach(function(s){h+='<div class=warn>&#9888; '+amE(s)+'</div>';});return h;}
function amXlBody(dry){var R=amR();return{path:R.xlPath,headers:amRegH(),rows:amRegRows(),sheet:R.xlSheet||null,key_header:'Kode Poligon GC',mode:R.xlMode==='update'?'update':'skip',dry_run:!!dry,backup:true};}
async function amXlPick(){var R=amR();var p=await gcexDesktop.openFile({title:'Pilih workbook register as-mined',defaultPath:R.xlPath||undefined,filters:[{name:'Workbook Excel',extensions:['xlsx','xlsm']}]});if(!p)return;amRSet('xlPath',p);R.xlSheet='';AM.xl=null;amPanel();amXlPlan();}
async function amXlPlan(){var R=amR();if(!R.xlPath)return;AM.xl={path:R.xlPath,busy:'Memeriksa workbook…'};amPanel();
  try{var j=await gcexDesktop.api('/excel/register-write',amXlBody(true));R.xlSheet=j.sheet;AM.xl={path:R.xlPath,plan:j};}catch(e){AM.xl={path:R.xlPath,err:String(e&&e.message||e)};}amPanel();}
async function amXlSend(){var R=amR(),P=AM.xl;if(!P||!P.plan)return;var nst=amAllInfo().filter(function(I){return I.calc&&I.stale&&I.x.print!==false&&I.x.on;}).length;
  if(nst&&!confirm(nst+' poligon dihitung dengan metode / aturan SG lama (perlu Hitung ulang). Tetap kirim?'))return;
  if(!confirm('Tulis '+P.plan.added+' baris baru'+(P.plan.updated?' dan perbarui '+P.plan.updated+' baris':'')+' ke '+amXlName(R.xlPath)+' (sheet '+P.plan.sheet+')?\n\nSalinan cadangan dibuat dulu di folder _backup_gcex. Pastikan workbook sudah ditutup di Excel.'))return;
  AM.xl={path:R.xlPath,plan:P.plan,busy:'Menulis ke workbook…'};amPanel();
  try{var j=await gcexDesktop.api('/excel/register-write',amXlBody(false));AM.xl={path:R.xlPath,res:j};var e=$('amRegMsg');if(e)e.textContent=j.added+' baris → '+amXlName(R.xlPath);}catch(e){AM.xl={path:R.xlPath,plan:P.plan,err:String(e&&e.message||e)};}amPanel();}
