/* ================= AS-MINED: elevasi pick-up / boundary yang tidak rata & tidak tepat di RL flitch =================
   1) Titik pick-up: toleransi tampil ± m dari flitch bisa diatur; warna menurut posisi Z terhadap flitch
      (di bawah lantai flitch / sekitar lantai / di dalam flitch / di atas flitch / tanpa Z), hover menampilkan Z & selisih.
   2) Import boundary: flitch tujuan = flitch aktif (abaikan Z, seperti sebelumnya) ATAU otomatis menurut median Z string
      (flitch dengan RL bawah terdekat). Statistik Z tiap boundary disimpan & ditampilkan; penyimpangan ditandai.
   3) Volume as-mined: "Tebal flitch penuh" (bawaan, rumus lama) ATAU "Ikuti lantai pick-up": lantai tiap poligon
      diinterpolasi (IDW) dari titik pick-up di dalam / sekitar poligon dalam pita elevasi lantai; sub-blok dihitung
      dari lantai aktual sampai RL atas flitch (lantai lebih rendah = overdig ikut terhitung, lebih tinggi = underdig). */
function amNumOr(v,d){var x=parseFloat(v);return isFinite(x)?x:d;}
function amZStat(pts){var z=[];(pts||[]).forEach(function(q){var v=q&&q.length>2?+q[2]:NaN;if(isFinite(v)&&!(v===0&&+q[0]===0))z.push(v);});if(!z.length)return null;z.sort(function(a,b){return a-b;});
  return{n:z.length,min:z[0],max:z[z.length-1],med:z.length%2?z[(z.length-1)/2]:(z[z.length/2-1]+z[z.length/2])/2};}
/* flitch (grid sama dengan flitch aktif) yang RL bawahnya paling dekat dengan z */
function amFlitchOfZ(z,B){var fh=B[0]-B[1];if(!(fh>0)||!isFinite(z))return B;var k=Math.round((B[1]-z)/fh);return[+(B[0]-k*fh).toFixed(4),+(B[1]-k*fh).toFixed(4)];}
function amDistPoly(P,x,y){var d=Infinity;for(var i=0,n=P.length;i<n;i++){var a=P[i],b=P[(i+1)%n],vx=b[0]-a[0],vy=b[1]-a[1],L=vx*vx+vy*vy,t=L>0?((x-a[0])*vx+(y-a[1])*vy)/L:0;t=t<0?0:t>1?1:t;var dx=a[0]+t*vx-x,dy=a[1]+t*vy-y,q=Math.sqrt(dx*dx+dy*dy);if(q<d)d=q;}return d;}
function amFloorPar(B){var R=amR(),fh=B[0]-B[1];return{dn:Math.max(0,amNumOr(R.flDn,2)),up:Math.max(0,amNumOr(R.flUp,+(0.6*fh).toFixed(2))),buf:Math.max(0,amNumOr(R.flBuf,2)),code:String(R.flCode||'').trim()};}
function amFloorKey(){var R=amR();return R.floor==='pickup'?'|fl:'+['tin',R.flDn,R.flUp,R.flBuf,R.flCode,(amD().pts||[]).length].join(','):'';}
/* titik lantai untuk satu poligon */
function amFloorPts(o,B){var D=amD(),P=D.pts||[],F=amFloorPar(B),lo=B[1]-F.dn,hi=Math.min(B[0]-0.05,B[1]+F.up),b=o.b,buf=F.buf,rx=null,out=[];
  if(F.code){try{rx=new RegExp(F.code,'i');}catch(e){rx=null;}}
  for(var i=0;i<P.length;i++){var q=P[i];if(!isFinite(q.z)||q.z<lo||q.z>hi)continue;if(rx&&!rx.test(q.c||'')&&!rx.test(q.id||''))continue;
    if(q.x<b[0]-buf||q.x>b[1]+buf||q.y<b[2]-buf||q.y>b[3]+buf)continue;if(!lyInS(o.r,q.x,q.y)&&amDistPoly(o.r,q.x,q.y)>buf)continue;out.push(q);}
  return{pts:out,lo:lo,hi:hi};}
/* fungsi lantai z(x,y) satu poligon: triangulasi (TIN) titik pick-up; IDW pangkat 2 (≤300 titik: semua; lebih: 16 terdekat lewat grid 5 m) = cadangan di luar segitiga */
function amFloorFn(o,B){var Q=amFloorPts(o,B),A=Q.pts,n=A.length;if(n<3)return{ok:false,n:n,f:function(){return B[1];}};
  var z=A.map(function(q){return q.z;}).sort(function(a,b){return a-b;}),med=n%2?z[(n-1)/2]:(z[n/2-1]+z[n/2])/2,lo=Q.lo,hi=Q.hi;
  var idw=function(L,x,y){var sw=0,sz=0;for(var i=0;i<L.length;i++){var q=L[i],dx=q.x-x,dy=q.y-y,d2=dx*dx+dy*dy;if(d2<1e-6)return q.z;var w=1/d2;sw+=w;sz+=w*q.z;}return sz/sw;};
  var f;if(n<=300)f=function(x,y){var v=idw(A,x,y);return v<lo?lo:v>hi?hi:v;};
  else{var cs=5,H={},key=function(i,j){return i+'|'+j;};A.forEach(function(q){var k=key(Math.floor(q.x/cs),Math.floor(q.y/cs));(H[k]=H[k]||[]).push(q);});
    f=function(x,y){var ci=Math.floor(x/cs),cj=Math.floor(y/cs),L=[];for(var r=0;r<40&&L.length<16;r++){for(var i=ci-r;i<=ci+r;i++)for(var j=cj-r;j<=cj+r;j++){if(Math.max(Math.abs(i-ci),Math.abs(j-cj))!==r)continue;var c=H[key(i,j)];if(c)L=L.concat(c);}}
      if(L.length>16){L.sort(function(a,b){return(a.x-x)*(a.x-x)+(a.y-y)*(a.y-y)-(b.x-x)*(b.x-x)-(b.y-y)*(b.y-y);});L=L.slice(0,16);}var v=idw(L,x,y);return v<lo?lo:v>hi?hi:v;};}
  /* 0.24.60 (pemilik 10-11-2026): lantai = TRIANGULASI titik pick-up (seperti atap, web-src/tinz.js); IDW di atas hanya cadangan di luar jangkauan titik */
  var TN=window.TINZ?TINZ(A):null,tin=0;if(TN){var fi=f;tin=TN.nt;f=function(x,y){var v=TN.f(x,y);if(v==null||!isFinite(v))return fi(x,y);return v<lo?lo:v>hi?hi:v;};}
  return{ok:true,n:n,f:f,zmin:z[0],zmax:z[n-1],med:med,tin:tin};}
/* ---------- titik pick-up: toleransi tampil & kategori Z ---------- */
function amPTol(){var D=amD();return Math.max(0,amNumOr(D.pTol,3));}
function amPtsNear(){var D=amD(),P=D.pts||[],B=lyBench();if(D.pAll)return P;var t=amPTol(),lo=B[1]-t,hi=B[0]+t;return P.filter(function(q){return !isFinite(q.z)||(q.z>=lo&&q.z<=hi);});}
var AMPC=[['bw','di bawah lantai flitch','#1971c2'],['fl','sekitar RL bawah (±0.3 m)','#2f9e44'],['in','di dalam flitch','#f08c00'],['ab','di atas flitch','#c2185b'],['nz','tanpa Z','#868e96']];
function amPCat(z,B){if(!isFinite(z))return 'nz';if(z<B[1]-0.3)return 'bw';if(z<=B[1]+0.3)return 'fl';if(z<=B[0]+1e-9)return 'in';return 'ab';}
function amPStat(){var B=lyBench(),P=amPtsNear(),c={bw:0,fl:0,in:0,ab:0,nz:0},z=[];P.forEach(function(q){c[amPCat(q.z,B)]++;if(isFinite(q.z))z.push(q.z);});z.sort(function(a,b){return a-b;});
  return{c:c,n:P.length,med:z.length?z[Math.floor(z.length/2)]:NaN,min:z[0],max:z[z.length-1],B:B};}
(function(){var _t=window.amTraces2D;if(typeof _t!=='function')return;
  amTraces2D=function(){var out=_t.apply(this,arguments);try{var i0=-1;out.forEach(function(t,i){if(t&&String(t.name||'').indexOf('Pick-up survey')===0)i0=i;});if(i0<0)return out;
      var D=amD(),B=lyBench(),P=amPtsNear(),G={};P.forEach(function(q){var k=amPCat(q.z,B),g=G[k]||(G[k]={x:[],y:[],t:[],h:[]});g.x.push(q.x);g.y.push(q.y);g.t.push(D.plab?(q.id||q.c||'')+(isFinite(q.z)?' '+q.z.toFixed(2):''):'');
        g.h.push((q.id?'<b>'+amE(q.id)+'</b> ':'')+(q.c?amE(q.c)+'<br>':'')+'Z '+(isFinite(q.z)?q.z.toFixed(2)+' &middot; &Delta; RL bawah '+(q.z-B[1]>=0?'+':'')+(q.z-B[1]).toFixed(2)+' m':'-'));});
      var add=[];AMPC.forEach(function(c){var g=G[c[0]];if(!g)return;add.push({type:'scatter',mode:D.plab?'markers+text':'markers',x:g.x,y:g.y,text:g.t,hovertext:g.h,hoverinfo:'text',textposition:'top right',textfont:{size:9,color:c[2]},
        marker:{symbol:'cross-thin-open',size:9,color:c[2],line:{width:1.8,color:c[2]}},name:'Pick-up '+c[1]+' ('+g.x.length+')',showlegend:true});});
      out.splice.apply(out,[i0,1].concat(add));}catch(e){console.error(e);}return out;};})();
/* ---------- import boundary: flitch menurut Z (opsional) ---------- */
function amBndFile(files){if(!files||!files.length)return;var L=Array.prototype.slice.call(files),n=0,bad=0,per={};AM.bmsg='Membaca boundary&hellip;';amPanel();
  (async function(){for(var i=0;i<L.length;i++){var f=L[i],k=/\.dxf$/i.test(f.name)?'dxf':'str';try{var segs=await SA.readLines({f:f,k:k});segs.forEach(function(P,j){if(P.length>=3){if(amBndAdd(P,f.name.replace(/\.[^.]+$/,'')+(segs.length>1?' #'+(j+1):''))){n++;var b=AM.lastFl||lyBench(),kk=lyFmt(b[0])+'&ndash;'+lyFmt(b[1]);per[kk]=(per[kk]||0)+1;}}else bad++;});}catch(e){bad++;AM.bmsg='<span class=warn>'+amE(f.name)+': '+amE(e.message)+'</span>';}}
    var B=lyBench(),ks=Object.keys(per),cur=lyFmt(B[0])+'&ndash;'+lyFmt(B[1]),oth=ks.filter(function(k){return k!==cur;});
    AM.bmsg=n+' boundary ditambahkan'+(ks.length?': '+ks.map(function(k){return 'flitch RL '+k+' ('+per[k]+')';}).join(', '):'')+(bad?' &middot; '+bad+' string bukan polygon dilewati':'')+
      (oth.length?'<br><span class=warn>'+oth.reduce(function(a,k){return a+per[k];},0)+' boundary masuk ke flitch lain menurut elevasinya &mdash; ubah RL atas/bawah untuk melihatnya.</span>':'');
    amPanel();updatePlot();amDirty();})();}
/* ---------- tampilan ---------- */
function amFlTxt(I){var x=I.x,s=I.st,out='',B=[x.top,x.bot],t=0.5;
  if(x.zs){var off=x.zs.med<B[1]-t||x.zs.med>B[0]+t;out+=' &middot; <span'+(off?' class=warn':'')+' title="Elevasi string boundary: min '+x.zs.min.toFixed(2)+', median '+x.zs.med.toFixed(2)+', maks '+x.zs.max.toFixed(2)+'">Z '+x.zs.min.toFixed(1)+'&ndash;'+x.zs.max.toFixed(1)+'</span>';}
  if(s&&s.fl){out+=s.fl.none?' &middot; <span class=warn title="Titik pick-up di dalam / sekitar poligon kurang dari 3: lantai = RL bawah flitch">lantai = RL bawah ('+s.fl.n+' titik)</span>':' &middot; <span title="Lantai pick-up: '+s.fl.n+' titik, RL '+s.fl.min.toFixed(2)+'&ndash;'+s.fl.max.toFixed(2)+'">lantai '+s.fl.med.toFixed(2)+'</span>';
    if(s.v>0&&I.area>0)out+=' &middot; tebal '+(s.v/I.area).toFixed(2)+' m';}
  return out;}
/* ---------- laporan titik LANTAI (selaras amRoofStat) ----------
   Tanpa laporan ini, titik lantai di luar pita dibuang diam-diam dan poligonnya jatuh ke RL bawah
   nominal: tonase berubah tanpa satu pun tanda. Dihitung dari pita yang SAMA dengan amFloorPts. */
function amFloorStat(B){var D=amD(),P=D.pts||[],F=amFloorPar(B),lo=B[1]-F.dn,hi=Math.min(B[0]-0.05,B[1]+F.up),n=0,bw=0,ab=0,nz=0;
  P.forEach(function(q){if(!isFinite(q.z)){nz++;return;}if(q.z<lo)bw++;else if(q.z>hi)ab++;else n++;});
  var pol=0,jatuh=[];try{amBndCur().forEach(function(x){if(!x.on)return;pol++;if(x.st&&x.st.fl&&x.st.fl.none)jatuh.push(x);});}catch(e){}
  return{n:P.length,nPita:n,bw:bw,ab:ab,nz:nz,lo:lo,hi:hi,pol:pol,jatuh:jatuh};}
function amFloorWarn(B){var R=amR();if(R.floor!=='pickup')return '';var D=amD(),S=amFloorStat(B),h='';
  if(!S.n)return '<div class=hint><span class=warn>Mode &ldquo;Ikuti lantai pick-up&rdquo; aktif, tetapi belum ada titik pick-up LANTAI: semua poligon memakai RL bawah nominal '+lyFmt(B[1])+'.</span></div>';
  h+='<div class=hint id=amFloorStat>'+S.n.toLocaleString()+' titik lantai, <b>'+S.nPita.toLocaleString()+'</b> di dalam pita RL '+S.lo.toFixed(2)+'&ndash;'+S.hi.toFixed(2);
  var luar=S.bw+S.ab+S.nz;
  if(luar)h+=' &middot; <span'+(S.nPita?'':' class=warn')+'>'+luar.toLocaleString()+' tidak dipakai ('+[S.bw?S.bw.toLocaleString()+' di bawah pita':'',S.ab?S.ab.toLocaleString()+' di atas pita':'',S.nz?S.nz.toLocaleString()+' tanpa Z':''].filter(Boolean).join(', ')+')</span>';
  h+='</div>';
  if(!S.nPita)h+='<div class=hint><span class=warn>Tidak satu pun titik lantai jatuh di pita elevasi flitch ini, jadi semua poligon memakai RL bawah nominal '+lyFmt(B[1])+'.</span> Kemungkinan titiknya dari flitch lain, kolom koordinatnya tertukar, atau pitanya terlalu sempit (Setelan lanjutan).</div>';
  else if(S.jatuh.length)h+='<div class=hint><span class=warn>'+S.jatuh.length+' dari '+S.pol+' poligon punya &lt; 3 titik lantai di dalam / dekat poligon</span> &mdash; lantainya memakai RL bawah nominal '+lyFmt(B[1])+': '+S.jatuh.slice(0,6).map(function(x){var I=null;try{I=amInfoById(x.id);}catch(e){}return amE((I&&I.code)||x.name||x.id);}).join(', ')+(S.jatuh.length>6?', &hellip;':'')+'.</div>';
  if(window.AM&&AM.jepit&&AM.jepit.a>0.01)h+='<div class=hint><span class=warn>Perhitungan terakhir: '+AM.jepit.a.toFixed(1)+' m&sup2; luas yang atapnya berada di bawah / sama dengan lantai</span> &mdash; tebalnya dihitung NOL di situ. Itu underdig nyata, atau titik pick-up lantai / atap dari hari atau flitch yang salah. Periksa sebelum angkanya dilaporkan.</div>';
  return h;}
function amFloorBox(){var D=amD(),R=amR(),B=lyBench(),fh=B[0]-B[1],F=amFloorPar(B),has=(D.pts||[]).length>0,S=has?amPStat():null;
  var sel=function(v,opts,on){return '<select onchange="'+on+'">'+opts.map(function(o){return '<option value="'+o[0]+'"'+(String(o[0])===String(v)?' selected':'')+'>'+o[1]+'</option>';}).join('')+'</select>';};
  var h='<div class=amset id=amFloorBox><div class=amst><b>Elevasi pick-up &amp; lantai</b></div>';
  if(has){h+='<div class=g2><div><label>Tampilkan pick-up &plusmn; (m dari flitch)</label><input type=number step=any min=0 value="'+amE(amPTol())+'" onchange="amD().pTol=this.value;amPanel();updatePlot();amDirty()"'+(D.pAll?' disabled title="Semua RL dicentang"':'')+'></div>'+
      '<div class=hint style="align-self:end;margin:0">Median Z titik tampil: <b>'+(isFinite(S.med)?S.med.toFixed(2):'-')+'</b>'+(isFinite(S.med)?' ('+(S.med-B[1]>=0?'+':'')+(S.med-B[1]).toFixed(2)+' m dari RL bawah)':'')+'</div></div>'+
      '<div class=amzc>'+AMPC.map(function(c){return S.c[c[0]]?'<span><i style="background:'+c[2]+'"></i>'+c[1]+' <b>'+S.c[c[0]].toLocaleString()+'</b></span>':'';}).join('')+'</div>';}
  h+='<div class=g2 style="margin-top:4px"><div><label>Import boundary masuk ke</label>'+sel(R.bndZ||'active',[['active','Flitch aktif (abaikan Z)'],['auto','Flitch menurut elevasi string']],"amRSet('bndZ',this.value)")+'</div>'+
    '<div><label>Volume as-mined</label>'+sel(R.floor||'flitch',[['flitch','Tebal flitch penuh'],['pickup','Ikuti lantai pick-up (triangulasi / TIN)']],"amRSet('floor',this.value);amAuto()")+'</div></div>';
  if(R.floor==='pickup'){h+=amFloorWarn(B)+'<details class=amadv><summary>Setelan lanjutan (pita, jarak, kode titik)</summary><div class=g3 style="margin-top:4px"><div><label>Lantai s/d bawah RL bawah (m)</label><input type=number step=any min=0 value="'+amE(F.dn)+'" onchange="amRSet(\'flDn\',this.value);amAuto()"></div>'+
      '<div><label>s/d atas RL bawah (m)</label><input type=number step=any min=0 value="'+amE(F.up)+'" onchange="amRSet(\'flUp\',this.value);amAuto()"></div><div><label>Jarak dari poligon (m)</label><input type=number step=any min=0 value="'+amE(F.buf)+'" onchange="amRSet(\'flBuf\',this.value);amAuto()"></div></div>'+
      '<div style="margin-top:4px"><label>Hanya kode / ID titik (opsional, mis. TOE|FLOOR)</label><input type=text value="'+amE(F.code)+'" placeholder="semua titik" onchange="amRSet(\'flCode\',this.value);amAuto()"></div>'+
      '<div class=hint>Lantai tiap poligon diinterpolasi dari titik pick-up di dalam / &le; '+F.buf+' m dari poligon dengan Z antara RL '+(B[1]-F.dn).toFixed(2)+' dan '+Math.min(B[0]-0.05,B[1]+F.up).toFixed(2)+'. Tonase = dari lantai aktual sampai RL atas '+lyFmt(B[0])+': lantai lebih rendah (overdig) ikut terhitung, lebih tinggi (underdig) dikurangi. Poligon dengan &lt; 3 titik memakai RL bawah flitch.</div></details>';}
  else h+='<div class=hint>'+(R.bndZ==='auto'?'Boundary dari file dimasukkan ke flitch yang RL bawahnya paling dekat dengan median Z string (tinggi flitch '+lyFmt(fh)+' m). ':'Boundary dari file masuk ke flitch aktif, Z string hanya dicatat. ')+'Pilih <b>Ikuti lantai pick-up</b> bila lantai ore yang tertambang tidak rata / tidak tepat di RL flitch.</div>';
  return h+'</div>';}
(function(){var st=document.createElement('style');st.textContent='.amzc{display:flex;flex-wrap:wrap;gap:4px 10px;margin-top:4px;font-size:11px}.amzc i{display:inline-block;width:9px;height:9px;border-radius:2px;margin-right:4px;vertical-align:-1px}details.amadv{margin-top:6px;border-top:1px solid var(--bd,#d7dde5);padding-top:4px}details.amadv>summary{cursor:pointer;font-size:11.5px;color:var(--mu,#667);user-select:none}details.amadv[open]>summary{margin-bottom:2px}';document.head.appendChild(st);})();
