
/* ================= SG terpusat, metode tonase "Seperti Surpac", audit blok per poligon ================= */
/* SG satu blok: kolom SG (> 0) -> nilainya; <= 0 / kosong -> SG pengganti atau 0 (seperti Surpac) */
function bxSGv(v){var U=BX.ui;if(!U)return 2.6;if(!U.sgCol)return U.sg;if(isFinite(v)&&v>0)return v;if(U.sgZero==='zero')return 0;var r=parseFloat(U.sgRep);return r>0?r:U.sg;}
function bxSGrep(){var U=BX.ui,r=parseFloat(U&&U.sgRep);return r>0?r:(U?U.sg:2.6);}
/* hitung blok SG <= 0 (cache per model & kolom) */
function bxSGbad(){var U=BX.ui,m=BX.m;if(!U||!m||!U.sgCol||!m.num[U.sgCol])return null;var k=BX.ver+'|'+U.sgCol+'|'+m.n;if(BX._sgb&&BX._sgb.k===k)return BX._sgb;var A=m.num[U.sgCol],n=0;for(var i=0;i<m.n;i++){var v=A[i];if(!(isFinite(v)&&v>0))n++;}BX._sgb={k:k,n:n,N:m.n};return BX._sgb;}
function bxSGbadFl(){var U=BX.ui,m=BX.m;if(!U||!m||!U.sgCol||!m.num[U.sgCol]||!U.fl)return null;var B=lyBench(),k=BX.ver+'|'+U.sgCol+'|'+B[0]+'|'+B[1];if(BX._sgf&&BX._sgf.k===k)return BX._sgf;var A=m.num[U.sgCol],C=lyCandZ(B[1],B[0]),n=0,N=0;for(var t=0;t<C.length;t++){var i=C[t];if(lyOv(i,B,'comp')<=0)continue;N++;var v=A[i];if(!(isFinite(v)&&v>0))n++;}BX._sgf={k:k,n:n,N:N,B:B};return BX._sgf;}
function bxSGset(k,v){var U=BX.ui;if(!U)return;U[k]=v;LY.ix=null;LY.fc=null;BX.sc={};if(window.DB)DB.rk='';try{bxPanel();}catch(e){}try{dbPanel();}catch(e){}try{lyPanel();}catch(e){}try{updatePlot();}catch(e){}try{if(window.amPanel)amPanel();if(window.amAuto)amAuto();}catch(e){}if(window.SA&&SA.dirty)SA.dirty();}
/* kontrol SG <= 0 di tab Filter & SG */
(function(){var _p=window.bxPanel;if(!_p)return;bxPanel=function(){var r=_p.apply(this,arguments);try{var b=$('bxBody');if(!b||!BX.m)return r;var U=BX.ui;
    var g=Array.prototype.slice.call(b.children).filter(function(n){return /SG tetap/i.test(n.textContent||'')&&n.classList.contains('g2');})[0];if(!g)return r;
    var S=bxSGbad(),d=document.createElement('div');d.className='sgz';
    if(!U.sgCol){d.innerHTML='<div class=hint>SG tetap '+U.sg+' dipakai untuk semua blok. Pilih kolom SG (mis. sg3) agar densitas per blok dipakai.</div>';}
    else{var pc=S&&S.N?S.n/S.N*100:0;
      var F=bxSGbadFl();
      d.innerHTML=(S&&S.n?'<div class=sgw>&#9888; Blok dengan '+bxE(U.sgCol)+' &le; 0 / kosong (biasanya blok tidak terestimasi)'+(F?': <b>'+F.n.toLocaleString()+'</b> dari '+F.N.toLocaleString()+' blok ('+(F.N?F.n/F.N*100:0).toFixed(0)+'%) di flitch aktif RL '+lyFmt(F.B[0])+'&ndash;'+lyFmt(F.B[1]):'')+'. Seluruh model: '+S.n.toLocaleString()+' dari '+S.N.toLocaleString()+' ('+pc.toFixed(0)+'%, termasuk blok udara / di luar domain). Pilih cara menghitungnya:</div>':'<div class=hint>Semua blok punya '+bxE(U.sgCol)+' &gt; 0.</div>')+
        '<div class=g2><div><label>Blok '+bxE(U.sgCol)+' &le; 0</label><select onchange="bxSGset(\'sgZero\',this.value)"><option value=rep'+(U.sgZero!=='zero'?' selected':'')+'>Pakai SG pengganti</option><option value=zero'+(U.sgZero==='zero'?' selected':'')+'>Anggap 0 (seperti Surpac)</option></select></div>'+
        '<div><label>SG pengganti</label><input type=number step=any value="'+bxE(U.sgRep!==undefined&&U.sgRep!==''?U.sgRep:U.sg)+'"'+(U.sgZero==='zero'?' disabled':'')+' onchange="bxSGset(\'sgRep\',this.value)"></div></div>'+
        '<div class=hint>'+(U.sgZero==='zero'?'Seperti Surpac: volume blok tetap dihitung, tonasenya 0 &rarr; tonase lebih kecil, kadar lebih tinggi.':'Blok tetap berbobot dengan SG pengganti; kadarnya apa adanya (biasanya 0 = pengencer).')+'</div>';}
    b.insertBefore(d,g.nextSibling);}catch(e){console.error(e);}return r;};})();
/* ---------- metode tonase "Seperti Surpac": blok utuh, titik tengah di dalam string & flitch ---------- */
function lyCalcM(){var L=lyU();return L.calcM==='surpac'?'surpac':'clip';}
function lyOnEdge(P,x,y){for(var i=0,j=P.length-1;i<P.length;j=i++){var a=P[j],b=P[i],cr=(b[0]-a[0])*(y-a[1])-(b[1]-a[1])*(x-a[0]);if(Math.abs(cr)>1e-6*Math.max(1,Math.hypot(b[0]-a[0],b[1]-a[1])))continue;if(x>=Math.min(a[0],b[0])-1e-6&&x<=Math.max(a[0],b[0])+1e-6&&y>=Math.min(a[1],b[1])-1e-6&&y<=Math.max(a[1],b[1])+1e-6)return true;}return false;}
function lyInS(P,x,y){return lyOnEdge(P,x,y)||lyIn(P,x,y);}
function lyCandZ(lo,hi){var m=BX.m;if(m.n>=200000&&window.bxZCand)return bxZCand(lo,hi);var a=[];for(var i=0;i<m.n;i++){if(m.z[i]+m.sz[i]/2>lo&&m.z[i]-m.sz[i]/2<hi)a.push(i);}return a;}
function lyTonS(P,zs0,excl){var m=BX.m;excl=excl||[];var L=lyU(),B=lyBench(),fh=B[0]-B[1],ga=lyGradeAttr(),G=ga?m.num[ga]:null,U=BX.ui,sgA=U.sgCol&&m.num[U.sgCol]?m.num[U.sgCol]:null,b=lyBB(P);
  var r={n:0,v:0,t:0,g:0,gt:0,a:0,attr:ga,zs:isFinite(zs0)?zs0:lyZs(),fh:fh,sfT:0,sx:0,sxT:0,wA:0,wT:0,m:'surpac',E:window.elInit?elInit(ga):null},DU=window.dbU?dbU():{},SX=DU.sxsAttr&&m.num[DU.sxsAttr]?m.num[DU.sxsAttr]:null,SC=DU.sfAttr&&m.cat[DU.sfAttr]?m.cat[DU.sfAttr]:null,SFS={};
  if(SC){var cl0=String(DU.sfCodes||'').toUpperCase().split(',').map(function(x){return x.trim();});SC.dict.forEach(function(d,k){if(cl0.indexOf(String(d).toUpperCase())>=0)SFS[k]=1;});}
  var C=lyCandZ(B[1],B[0]),N=C.length;for(var t=0;t<N;t++){var i=C[t],z=m.z[i];if(!(z>B[1]+1e-9&&z<=B[0]+1e-9))continue;var x=m.x[i],y=m.y[i];if(x<b[0]-1e-6||x>b[1]+1e-6||y<b[2]-1e-6||y>b[3]+1e-6)continue;if(L.onlyPass&&!bxPass(i))continue;
    if(!lyInS(P,x,y))continue;var skip=false;for(var e=0;e<excl.length;e++){if(lyIn(excl[e].p,x,y)&&!lyOnEdge(excl[e].p,x,y)){skip=true;break;}}if(skip)continue;
    var v=m.sx[i]*m.sy[i]*m.sz[i],sg=bxSGv(sgA?sgA[i]:NaN),tt=v*sg;r.n++;r.v+=v;r.t+=tt;if(r.E)elAdd(r,i,tt);r.a+=v/fh;if(SC&&SFS[SC.codes[i]])r.sfT+=tt;if(SX&&isFinite(SX[i])){r.sx+=SX[i]*tt;r.sxT+=tt;}if(G&&isFinite(G[i])){r.g+=G[i]*tt;r.gt+=tt;}}
  r.grade=r.gt?r.g/r.gt:NaN;r.sxs=r.sxT?r.sx/r.sxT:NaN;r.sulf=!!(DU.sfOn&&r.t>0&&((SC&&r.sfT/r.t>=0.5)||(isFinite(r.sxs)&&r.sxs>(+DU.sxsThr||0.8))));var ea=0;excl.forEach(function(Q){ea+=lyArea(Q.p);});r.cov=r.a/Math.max(1e-9,lyArea(P)-ea);if(r.E)elFin(r);return r;}
(function(){var _t=window.lyTon;if(!_t)return;lyTon=function(P,zs0,excl){if(BX.m&&lyCalcM()==='surpac')return lyTonS(P,zs0,excl);return _t.apply(this,arguments);};})();
/* pilihan metode di tab Dig block (di bawah pilihan Sayatan BM) */
(function(){var _d=window.dbPanel;if(!_d)return;dbPanel=function(){var r=_d.apply(this,arguments);try{var b=$('dbBody');if(!b)return r;var s=b.querySelector('select[onchange*=flMode]');if(!s||b.querySelector('.calcm'))return r;var host=s.closest('.g2')||s.parentNode;
    var d=document.createElement('div');d.className='calcm';var sm=lyCalcM()==='surpac';
    d.innerHTML='<label>Metode tonase</label><select onchange="lyU().calcM=this.value;bxSGset(\'_x\',Date.now())"><option value=clip'+(sm?'':' selected')+'>Presisi GC-Ex (potong di garis string, tebal di flitch)</option><option value=surpac'+(sm?' selected':'')+'>Seperti Surpac (blok utuh, titik tengah di dalam string &amp; flitch)</option></select>'+
      '<div class=hint>'+(sm?'Sama dengan Surpac <i>Keep partial = False</i>: blok dihitung utuh bila titik tengahnya di dalam string dan RL flitch. Untuk rekonsiliasi dengan report Surpac.':'Blok dipotong tepat di garis string dan ditimbang tebalnya di dalam flitch (disarankan untuk dig plan).')+((window.dbU&&dbU().wOn)?'<div style="margin-top:3px"><span class=warn>Perhatikan saat membandingkan:</span> pilihan <b>Area polygon tanpa blok BM dihitung sebagai waste default</b> sedang <b>menyala</b>. Pilihan itu hanya dipakai metode <b>Presisi GC-Ex</b>; metode <b>Seperti Surpac</b> mengabaikannya. Jadi sebagian selisih antara kedua metode berasal dari waste pengisi itu, bukan dari aturan blok perbatasan &mdash; rinciannya ada di Audit CSV.</div>':'')+'</div>'+
      '<button style="width:100%;margin-top:4px" onclick="lyAuditCsv()" title="Daftar setiap blok per poligon dengan perhitungan kedua metode">&#128269; Audit blok per poligon (CSV)</button>';
    host.parentNode.insertBefore(d,host.nextSibling);}catch(e){console.error(e);}return r;};})();
/* ---------- audit blok per poligon ---------- */
function lyAuditCsv(){var m=BX.m;if(!m){alert('Import block model dulu.');return;}var it=lyItems();if(!it.length){alert('Belum ada dig block tercentang di flitch ini.');return;}
  var U=BX.ui,B=lyBench(),fh=B[0]-B[1],ga=lyGradeAttr(),G=ga?m.num[ga]:null,sgA=U.sgCol&&m.num[U.sgCol]?m.num[U.sgCol]:null,md=lyFlMode();
  var R=it.map(function(o){return{p:o.r,b:lyBB(o.r),a:lyArea(o.r)};});
  var sep=';',dec=',',f=function(v,d){if(v===''||v==null)return '';if(typeof v!=='number')return String(v).indexOf(sep)>=0?'"'+v+'"':v;return isFinite(v)?(d==null?String(v):v.toFixed(d)).replace('.',dec):'';};
  var hdr=['Poligon','Nama','X','Y','Z','DX','DY','DZ',ga,(U.sgCol||'SG')+' (asli)','Luas terpotong m2','Tebal di flitch m','Vol presisi m3','SG dipakai','Ton presisi','Metal presisi g','Titik tengah masuk (Surpac)','Vol Surpac m3','Ton Surpac','Metal Surpac g','Catatan'],out=[hdr.join(sep)],SUM=[];
  var C=lyCandZ(B[1],B[0]);
  it.forEach(function(o,k){var P=o.r,b=R[k].b,ex=[];R.forEach(function(q,j){if(j===k||q.a>=R[k].a)return;if(q.b[0]<b[0]||q.b[1]>b[1]||q.b[2]<b[2]||q.b[3]>b[3])return;if(q.p.every(function(v){return lyIn(P,v[0],v[1]);}))ex.push(q);});
    var s={vp:0,tp:0,mp:0,vs:0,ts:0,ms:0,n0:0,ar:0};
    for(var t=0;t<C.length;t++){var i=C[t],hx=m.sx[i]/2,hy=m.sy[i]/2,x=m.x[i],y=m.y[i],z=m.z[i];if(x+hx<b[0]||x-hx>b[1]||y+hy<b[2]||y-hy>b[3])continue;
      var ov=lyOv(i,B,md),rc=[x-hx,x+hx,y-hy,y+hy],ar=ov>0?lyClip(P,rc):0;if(ar>1e-6)ex.forEach(function(Q){if(!(rc[1]<Q.b[0]||rc[0]>Q.b[1]||rc[3]<Q.b[2]||rc[2]>Q.b[3]))ar-=lyClip(Q.p,rc);});if(ar<=1e-6)ar=0;
      var cin=(z>B[1]+1e-9&&z<=B[0]+1e-9)&&lyInS(P,x,y)&&!ex.some(function(Q){return lyIn(Q.p,x,y)&&!lyOnEdge(Q.p,x,y);});if(!ar&&!cin)continue;
      var raw=sgA?sgA[i]:NaN,sg=bxSGv(raw),g=G?G[i]:NaN,vp=ar*ov,tp=vp*sg,vs=cin?m.sx[i]*m.sy[i]*m.sz[i]:0,ts=vs*sg;s.vp+=vp;s.tp+=tp;s.vs+=vs;s.ts+=ts;s.ar+=ar*ov/fh;if(isFinite(g)){s.mp+=tp*g;s.ms+=ts*g;}if(sgA&&!(isFinite(raw)&&raw>0))s.n0++;
      out.push([k+1,o.name,x,y,z,m.sx[i],m.sy[i],m.sz[i],g,raw,ar,ov,vp,sg,tp,isFinite(g)?tp*g:'',cin?'Ya':'Tidak',vs,ts,isFinite(g)?ts*g:'',(sgA&&!(isFinite(raw)&&raw>0))?'SG<=0':''].map(function(v,j){return j<2||j===16||j===20?f(v):f(v,j>=2&&j<=4?3:4);}).join(sep));}
    SUM.push([k+1,o.name,s,o.ton]);});
  /* Waste pengisi: area poligon yang TIDAK tertutup blok BM, dihitung sebagai waste bila pilihan
     "Area polygon tanpa blok BM dihitung sebagai waste default" menyala (bawaannya MENYALA).
     Angka ini ikut di tonase panel pada metode Presisi GC-Ex, tetapi TIDAK ada pada metode Seperti
     Surpac, dan ia bukan blok sehingga tidak muncul di daftar per-blok di atas. Tanpa kolom ini,
     total audit tidak akan pernah cocok dengan total di panel -- justru itu yang dulu membuat
     angkanya diperdebatkan. */
  var DU2=window.dbU?dbU():{},wsg=parseFloat(DU2.wSG);if(!(wsg>0))wsg=U.sg;var wg=+DU2.wG||0;
  out.push('');out.push(['RINGKASAN','Nama','Vol presisi m3','Ton presisi','Kadar presisi','Waste pengisi m2','Vol waste pengisi m3','Ton waste pengisi','Vol presisi + waste m3','Ton presisi + waste','Vol Surpac m3','Ton Surpac','Kadar Surpac','Blok SG<=0','Metode aktif'].join(sep));
  SUM.forEach(function(q,k2){var s=q[2],PA=R[k2].a,wa=DU2.wOn?Math.max(0,PA-s.ar):0,wv=wa*fh,wt=wv*wsg;
    out.push([q[0],q[1],f(s.vp,2),f(s.tp,2),f(s.tp?s.mp/s.tp:NaN,4),f(wa,2),f(wv,2),f(wt,2),f(s.vp+wv,2),f(s.tp+wt,2),f(s.vs,2),f(s.ts,2),f(s.ts?s.ms/s.ts:NaN,4),s.n0,lyCalcM()==='surpac'?'Seperti Surpac':'Presisi GC-Ex'].join(sep));});
  out.push('');
  out.push('Waste pengisi = area poligon tanpa blok BM x tebal flitch x SG waste'+sep+(DU2.wOn?('MENYALA; SG '+f(wsg,3)+', kadar '+f(wg,4)):'MATI (tidak dihitung)'));
  out.push('Metode Seperti Surpac TIDAK memuat waste pengisi: kolom Ton Surpac hanya blok yang titik tengahnya masuk.'+sep+'Kolom "Ton presisi + waste" itulah yang cocok dengan tonase di panel Dig block saat metode Presisi GC-Ex dipakai.');
  out.push('');out.push('Flitch RL '+lyFmt(B[0])+' - '+lyFmt(B[1])+sep+'Kadar '+ga+sep+'SG '+(U.sgCol?'kolom '+U.sgCol+'; blok <=0 = '+(U.sgZero==='zero'?'0 (seperti Surpac)':'pengganti '+bxSGrep()):'tetap '+U.sg)+sep+'Sayatan BM '+(md==='comp'?'komposit tebal flitch':'bidang tengah'));
  dgDl('﻿'+out.join('\r\n')+'\r\n','Audit_Blok_'+String(ZONE).replace(/[^A-Za-z0-9_-]+/g,'_')+'_'+lyNum(B[0])+'-'+lyNum(B[1])+'.csv','text/csv');}
