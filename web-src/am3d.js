/* ================= GC-Ex Block Model 0.14: 3D hasil kerja & model as-mined gabungan (puzzle) =================
   Di menu Register & Laporan As-Mined:
   - Rekap per flitch hasil running as-mined (poligon, sub-blok, ton, kadar) + "Hitung semua flitch" (menjalankan ulang
     as-mined untuk setiap flitch yang punya poligon, supaya model gabungan lengkap walau baru dibuka).
   - Model as-mined GABUNGAN: semua sub-blok as-mined dari semua flitch disusun jadi satu model (puzzle) -> export satu
     file .mdl (block model .mdl resmi) atau CSV (block model CSV), dan bisa dilihat di 3D.
   - Tampilan 3D hasil kerja: prisma dig block (rencana), prisma poligon as-mined (aktual) dan sub-blok model as-mined
     berwarna kelas kadar, per flitch dari atas ke bawah. */
var AM3={on:false,db:true,am:true,sb:true,op:0.85};
function am3Flitches(){var G={},o=[];amBndAll().forEach(function(x){if(!x.on||!isFinite(+x.top))return;var k=lyFmt(x.top)+'_'+lyFmt(x.bot);if(!G[k]){G[k]={k:k,top:+x.top,bot:+x.bot,n:0};o.push(G[k]);}G[k].n++;});return o.sort(function(a,b){return b.top-a.top;});}
function am3RunAll(){var F=am3Flitches();if(!F.length){alert('Belum ada poligon as-mined.');return;}var L=lyU(),sv={fh:L.fh,top:L.top,bot:L.bot},n=0,t0=Date.now();
  try{F.forEach(function(f){L.fh=+(f.top-f.bot).toFixed(4);L.top=f.top;L.bot=f.bot;try{amRun(true);n++;}catch(e){console.error(e);}});}finally{L.fh=sv.fh;L.top=sv.top;L.bot=sv.bot;}
  AM3.msg=n+' flitch dihitung ulang ('+((Date.now()-t0)/1000).toFixed(1)+' s).';amPanel();updatePlot();}
function am3Cells(){var all=new Map();Object.keys(AM.res).forEach(function(k){(AM.res[k].cells||[]).forEach(function(c){all.set(c.ix+'|'+c.iy+'|'+c.iz,c);});});return Array.from(all.values());}
function am3Csv(){var C=am3Cells();if(!C.length){alert('Belum ada hasil as-mined. Klik "Hitung semua flitch".');return;}var G=amGrid(),U=amU(),cv=G.dx*G.dy*G.dz,r=['X,Y,Z,DX,DY,DZ,FRAKSI,VOLUME,'+U.attr+'_ASMINED,'+U.attr+'_MODEL,TON,DATA_BARU,FLITCH'];
  var fk=function(z){var ks=Object.keys(AM.res);for(var i=0;i<ks.length;i++){var q=AM.res[ks[i]];if(z<=q.top+1e-6&&z>=q.bot-1e-6)return ks[i];}return '';};
  C.sort(function(a,b){return b.z-a.z||a.y-b.y||a.x-b.x;}).forEach(function(c){var fr=(c.f==null?1:c.f);r.push([(+c.x).toFixed(3),(+c.y).toFixed(3),(+c.z).toFixed(3),G.dx,G.dy,G.dz,fr.toFixed(6),(cv*fr).toFixed(4),isFinite(c.g)?(+c.g).toFixed(4):'',isFinite(c.go)?(+c.go).toFixed(4):'',isFinite(c.t)?(+c.t).toFixed(3):'',c.est?1:0,fk(c.z)].join(','));});
  var nm='asmined_gabungan_'+String(amR().pit||lyZone()).replace(/[^A-Za-z0-9_-]+/g,'_')+'.csv';dgDl(r.join('\r\n')+'\r\n',nm,'text/csv');}
function am3Toggle(v){var was=AM3.on;AM3.on=v==null?!AM3.on:!!v;if(AM3.on&&!Object.keys(AM.res).length&&am3Flitches().length)am3RunAll();if(AM3.on&&window.VIEW2D)toggle2D();
  /* fokus ke hasil kerja: block model & potong slab disembunyikan sementara, dikembalikan saat 3D hasil kerja ditutup */
  var bs=$('bxShow'),sc=$('sliceClip');if(AM3.on&&!was){AM3.sv={bx:bs?bs.checked:null,sc:sc?sc.checked:null};if(bs&&!AM3.bm)bs.checked=false;if(sc)sc.checked=false;}
  else if(!AM3.on&&was&&AM3.sv){if(bs&&AM3.sv.bx!=null)bs.checked=AM3.sv.bx;if(sc&&AM3.sv.sc!=null)sc.checked=AM3.sv.sc;AM3.sv=null;}
  amPanel();updatePlot();}
function am3Bm(v){AM3.bm=!!v;var bs=$('bxShow');if(bs&&AM3.on)bs.checked=AM3.bm;updatePlot();}
/* ---------- trace 3D ---------- */
function am3Prism(T,pts,top,bot,col,nm,dash,w){var X=[],Y=[],Z=[],n=pts.length,i;if(n<3)return;var P=pts.map(function(p){return[+p[0]-offX,+p[1]-offY];});
  [top,bot].forEach(function(z){for(i=0;i<=n;i++){var q=P[i%n];X.push(q[0]);Y.push(q[1]);Z.push(z);}X.push(null);Y.push(null);Z.push(null);});
  for(i=0;i<n;i++){X.push(P[i][0],P[i][0],null);Y.push(P[i][1],P[i][1],null);Z.push(top,bot,null);}
  T.push({type:'scatter3d',mode:'lines',x:X,y:Y,z:Z,line:{color:col,width:w||4,dash:dash||'solid'},name:nm,hoverinfo:'name',showlegend:false});}
function am3Traces(T){var U=amU(),lg={};
  if(AM3.db){DG.S.forEach(function(s){if(!s.db||s.inner||s.amTmp||!s.closed)return;var z=s.pts.map(function(q){return[q[0]+offX,q[1]+offY];});am3Prism(T,z,s.db.top,s.db.bot,s.col||'#888','Dig block #'+s.no+' '+(s.d||'')+' RL '+lyFmt(s.db.top)+'–'+lyFmt(s.db.bot),'dot',3);});
    T.push({type:'scatter3d',mode:'lines',x:[null],y:[null],z:[null],line:{color:'#888',width:3,dash:'dot'},name:'Dig block (rencana)',showlegend:true});}
  if(AM3.am){amAllInfo().forEach(function(I){var x=I.x;if(!x.on)return;am3Prism(T,x.pts,x.top,x.bot,I.col||'#2b8a3e','As-mined '+I.code+(I.calc?' · '+lyFmt(I.ton.toFixed(0))+' t @ '+amF(I.gA,2):''),'solid',5);});
    T.push({type:'scatter3d',mode:'lines',x:[null],y:[null],z:[null],line:{color:'#2b8a3e',width:5},name:'Poligon as-mined (aktual)',showlegend:true});}
  if(AM3.sb){var C=am3Cells();if(C.length){var G=amGrid(),a=U.attr,L=bxCls(a),hx=G.dx/2,hy=G.dy/2,hz=G.dz/2,grp={};
      C.forEach(function(c){var v=c.g,k=-1;for(var j=0;j<L.length;j++){var q=L[j];if((q.lo===null||v>=q.lo)&&(q.hi===null||v<q.hi)){k=j;break;}}(grp[k]=grp[k]||[]).push(c);});
      Object.keys(grp).forEach(function(k){var cs=grp[k],q=L[+k],X=[],Y=[],Z=[],I=[],J=[],K=[];
        cs.forEach(function(c){var b=X.length,x=c.x-offX,y=c.y-offY,z=c.z;[[-1,-1,-1],[1,-1,-1],[1,1,-1],[-1,1,-1],[-1,-1,1],[1,-1,1],[1,1,1],[-1,1,1]].forEach(function(d){X.push(x+d[0]*hx);Y.push(y+d[1]*hy);Z.push(z+d[2]*hz);});
          [[0,1,2],[0,2,3],[4,6,5],[4,7,6],[0,4,5],[0,5,1],[1,5,6],[1,6,2],[2,6,7],[2,7,3],[3,7,4],[3,4,0]].forEach(function(f){I.push(b+f[0]);J.push(b+f[1]);K.push(b+f[2]);});});
        T.push({type:'mesh3d',x:X,y:Y,z:Z,i:I,j:J,k:K,color:q?q.col:'#999',opacity:AM3.op,flatshading:true,name:'As-mined '+a+' '+(q?bxLab(q):'?')+' ('+cs.length+' sub-blok)',hoverinfo:'name',showlegend:true,lighting:{ambient:0.75,diffuse:0.5}});});}}}
(function(){var _d=dgTraces;dgTraces=function(T,o){var r=_d.apply(this,arguments);try{if(AM3.on&&!window.VIEW2D&&BX.m)am3Traces(T);}catch(e){console.error(e);}return r;};})();
/* ---------- panel: kotak rekap di Register ---------- */
function am3Box(){var F=am3Flitches(),ks=Object.keys(AM.res).sort(function(a,b){return AM.res[b].top-AM.res[a].top;}),C=am3Cells(),T=0,M=0,h;
  h='<div class=am3box><div class=amst><b>&#9707; Rekap &amp; model as-mined gabungan</b><small>'+F.length+' flitch berpoligon</small></div>';
  h+='<table class="pltb am3t"><tr><th>Flitch RL</th><th>Pol.</th><th>Sub-blok</th><th>Ton</th><th>Kadar</th></tr>'+F.map(function(f){var r=AM.res[f.k],s=r&&r.sum,t=s?s.t:0,g=s&&s.t?s.gA/s.t:NaN;if(t){T+=t;M+=g*t;}
    return '<tr'+(r?'':' class=am3no')+'><td>'+lyFmt(f.top)+'&ndash;'+lyFmt(f.bot)+'</td><td>'+f.n+'</td><td>'+(r?r.cells.length.toLocaleString():'<span class=warn>belum</span>')+'</td><td>'+(t?lyFmt(t.toFixed(0)):'-')+'</td><td>'+(isFinite(g)?g.toFixed(2):'-')+'</td></tr>';}).join('')+
    '<tr class=tot><td>Gabungan</td><td>'+F.reduce(function(a,f){return a+f.n;},0)+'</td><td>'+C.length.toLocaleString()+'</td><td>'+(T?lyFmt(T.toFixed(0)):'-')+'</td><td>'+(T?(M/T).toFixed(2):'-')+'</td></tr></table>';
  h+='<div class=g2 style="margin-top:4px"><button onclick="am3RunAll()" title="Jalankan as-mined untuk setiap flitch yang punya poligon">&#8635; Hitung semua flitch</button><button class="'+(AM3.on?'btn-pri':'')+'" onclick="am3Toggle()">&#9707; '+(AM3.on?'Sembunyikan 3D':'Lihat 3D hasil kerja')+'</button></div>';
  h+='<div class=am3ly><label class=sw><input type=checkbox '+(AM3.db?'checked':'')+' onchange="AM3.db=this.checked;updatePlot()">Dig block (rencana)</label><label class=sw><input type=checkbox '+(AM3.am?'checked':'')+' onchange="AM3.am=this.checked;updatePlot()">Poligon as-mined</label><label class=sw><input type=checkbox '+(AM3.sb?'checked':'')+' onchange="AM3.sb=this.checked;updatePlot()">Sub-blok model as-mined</label><label class=sw><input type=checkbox '+(AM3.bm?'checked':'')+' onchange="am3Bm(this.checked)">Block model GC (konteks)</label></div>';
  var mdlOk=!!(BX.m&&BX.m.mdl&&BX.m.mdl.hraw);
  /* Tombol export dipindahkan ke Register & Laporan As-Mined > Ekspor As-Mined. amMdl() sebelumnya
     bisa dipanggil dari TIGA tempat dengan tiga nama berbeda (.mdl gabungan di sini, "Export .mdl
     gabungan" di node Rekap, dan "Block model as-mined (.mdl)" di node tersendiri) -- padahal
     berkas yang dihasilkan sama persis. */
  h+='<div class=hint style="margin-top:4px">Export .mdl / CSV gabungan ada di <b>Register &amp; Laporan As-Mined &rsaquo; Ekspor As-Mined</b>.'+
     (mdlOk?'':' Export .mdl aktif bila block model dibuka dari file .mdl; untuk block model CSV pakai Rekap gabungan (CSV).')+'</div>';
  h+='<div class=hint>'+(AM3.msg?AM3.msg+' ':'')+'Model gabungan = semua sub-blok as-mined dari semua flitch (sub-blok yang sama dari run berbeda diambil yang terakhir).'+'</div></div>';return h;}
(function(){var _p=amPanel;amPanel=function(){var r=_p.apply(this,arguments);try{var el=$('amBody');if(!el||!BX.m)return r;var sec=el.querySelector('.uisec[data-k="5"]');var host=sec||el;var d=document.createElement('div');d.innerHTML=am3Box();host.appendChild(d.firstChild);}catch(e){console.error(e);}return r;};})();
(function(){var st=document.createElement('style');st.textContent='#amBody .am3box{margin-top:10px;padding:7px 8px;border:1px solid var(--bd);border-left:4px solid var(--pr);border-radius:6px;background:var(--sf2)}'+
  '#amBody .am3t{width:100%;font-size:11px;margin-top:4px}#amBody .am3t td,#amBody .am3t th{padding:2px 4px;text-align:right}#amBody .am3t td:first-child,#amBody .am3t th:first-child{text-align:left}#amBody .am3t tr.tot td{font-weight:700;border-top:2px solid var(--pr)}#amBody .am3t tr.am3no{opacity:.7}'+
  '#amBody .am3ly{display:flex;flex-direction:column;gap:1px;margin-top:4px}';document.head.appendChild(st);})();
