# -*- coding: utf-8 -*-
"""GC-Ex Block Model 0.13 — perbaikan tampilan & dig block manual.
  1. Garis string/dig block tidak lagi patah-patah (tampak putus-putus) di Penampang 2D:
     ruas yang bersambung digabung jadi satu polyline (bukan satu ruas + null per segmen).
  2. Blok BM di Penampang 2D digabung jadi persegi panjang (run-merge) -> jumlah path SVG turun
     drastis sehingga window zoom in / out tidak lagi tersendat.
  3. Digitasi manual dig block: Enter = tutup poligon otomatis, nomor & warna string mengikuti
     aturan material (sama dengan dig block otomatis), dicap ke flitch aktif, langsung masuk
     daftar Running grade & tonnage (bisa diedit bentuk / warna / nama / tujuan).
Dipanggil dari build.py: s = bmfix_patch.patch(s)
"""


def rep(s, a, b, n=1):
    c = s.count(a)
    assert c == n, 'bmfix_patch: pola ditemukan %d kali (harus %d): %s' % (c, n, a[:100])
    return s.replace(a, b)


HELP = r"""
/* ---------- gabung ruas yang bersambung jadi satu polyline (garis tidak patah-patah) ---------- */
function segJoin(){return{X:[],Y:[],Z:[],last:null,n:0,
  add:function(a,b){var L=this.last,e=1e-7;
    if(!L||Math.abs(L.x-a.x)>e||Math.abs(L.y-a.y)>e||Math.abs((L.z||0)-(a.z||0))>e){if(L){this.X.push(null);this.Y.push(null);this.Z.push(null);}this.X.push(a.x);this.Y.push(a.y);this.Z.push(a.z);}
    this.X.push(b.x);this.Y.push(b.y);this.Z.push(b.z);this.last=b;this.n++;},
  brk:function(){this.last=null;}};}
/* ---------- banyak kotak -> WebGL (zoom / geser Penampang 2D tetap ringan) ---------- */
function bx2dGl(t,n){if(n>150&&window.BXGL!==false)t.type='scattergl';return t;}
/* ---------- gabung blok sekelas jadi persegi panjang (jumlah path SVG jauh lebih sedikit) ---------- */
function bxMergeRects(R){if(R.length<2)return R;var e=1e-6,out=[];
  R.sort(function(a,b){return a[2]-b[2]||a[0]-b[0];});
  var run=null;R.forEach(function(r){if(run&&Math.abs(run[2]-r[2])<e&&Math.abs(run[3]-r[3])<e&&Math.abs(run[1]-r[0])<e)run[1]=r[1];else{run=r.slice();out.push(run);}});
  out.sort(function(a,b){return a[0]-b[0]||a[1]-b[1]||a[2]-b[2];});
  var col=null,out2=[];out.forEach(function(r){if(col&&Math.abs(col[0]-r[0])<e&&Math.abs(col[1]-r[1])<e&&Math.abs(col[3]-r[2])<e)col[3]=r[3];else{col=r.slice();out2.push(col);}});
  return out2;}
"""


def patch(s):
    # ---- helper ----
    s = rep(s, "function dgTraces(T,o){", HELP + "function dgTraces(T,o){")

    # ---- 1. garis string / dig block: ruas bersambung digabung; titik verteks dibatasi ----
    s = rep(s, """    var X=[],Y=[],Z=[],any=false,clip=o.clip||VIEW2D;if(!clip&&!showAll)return;
    for(var i=1;i<p.length;i++){var sg=[p[i-1],p[i]];if(clip){sg=clipSeg(p[i-1],p[i],o.K);if(!sg)continue;}X.push(sg[0].x,sg[1].x,null);Y.push(sg[0].y,sg[1].y,null);Z.push(sg[0].z,sg[1].z,null);any=true;}
    if(!any)return;T.push({type:'scatter3d',mode:'lines',x:X,y:Y,z:Z,name:'String '+s.no+(s.d?' '+s.d:''),line:{color:s.col,width:5},hoverinfo:'name',showlegend:true});
    var vx=[],vy=[],vz=[];s.pts.forEach(function(q){var pp={x:q[0],y:q[1],z:q[2]};if(!clip||inK(o.K,pp)){vx.push(q[0]);vy.push(q[1]);vz.push(q[2]);}});
    if(vx.length)T.push({type:'scatter3d',mode:'markers',x:vx,y:vy,z:vz,marker:{color:s.col,size:2.5},hoverinfo:'skip',showlegend:false});});}""",
            """    var clip=o.clip||VIEW2D,J=segJoin();if(!clip&&!showAll)return;
    for(var i=1;i<p.length;i++){var sg=[p[i-1],p[i]];if(clip){sg=clipSeg(p[i-1],p[i],o.K);if(!sg){J.brk();continue;}}J.add(sg[0],sg[1]);}
    if(!J.n)return;T.push({type:'scatter3d',mode:'lines',x:J.X,y:J.Y,z:J.Z,name:'String '+s.no+(s.d?' '+s.d:''),line:{color:s.col,width:5},hoverinfo:'name',showlegend:true});
    /* titik verteks hanya untuk string hasil digitasi tangan (dig block otomatis bisa ratusan titik) */
    if(!s.auto&&!s.inner&&s.pts.length<=400){var vx=[],vy=[],vz=[];s.pts.forEach(function(q){var pp={x:q[0],y:q[1],z:q[2]};if(!clip||inK(o.K,pp)){vx.push(q[0]);vy.push(q[1]);vz.push(q[2]);}});
      if(vx.length)T.push({type:'scatter3d',mode:'markers',x:vx,y:vy,z:vz,marker:{color:s.col,size:2.5},hoverinfo:'skip',showlegend:false});}});}""")

    # ---- 2. blok BM di Penampang 2D: gabung jadi persegi panjang ----
    s = rep(s, """  Object.keys(G).map(Number).sort(function(a,b){return a-b;}).forEach(function(k){var L=G[k],ci=bxClassInfo(k),X=[],Y=[];
    L.forEach(function(i){var x0,x1,y0,y1;if(g.m==='H'){x0=m.x[i]-m.sx[i]/2;x1=m.x[i]+m.sx[i]/2;y0=m.y[i]-m.sy[i]/2;y1=m.y[i]+m.sy[i]/2;}
      else{var c=F(m.x[i]-offX,m.y[i]-offY,m.z[i]),hw=(m.sx[i]*Math.abs(u[0])+m.sy[i]*Math.abs(u[1]))/2;x0=c[0]-hw;x1=c[0]+hw;y0=c[1]-m.sz[i]/2;y1=c[1]+m.sz[i]/2;}
      X.push(x0,x1,x1,x0,x0,null);Y.push(y0,y0,y1,y1,y0,null);});""",
            """  Object.keys(G).map(Number).sort(function(a,b){return a-b;}).forEach(function(k){var L=G[k],ci=bxClassInfo(k),X=[],Y=[],R=[];
    L.forEach(function(i){var x0,x1,y0,y1;if(g.m==='H'){x0=m.x[i]-m.sx[i]/2;x1=m.x[i]+m.sx[i]/2;y0=m.y[i]-m.sy[i]/2;y1=m.y[i]+m.sy[i]/2;}
      else{var c=F(m.x[i]-offX,m.y[i]-offY,m.z[i]),hw=(m.sx[i]*Math.abs(u[0])+m.sy[i]*Math.abs(u[1]))/2;x0=c[0]-hw;x1=c[0]+hw;y0=c[1]-m.sz[i]/2;y1=c[1]+m.sz[i]/2;}
      R.push([x0,x1,y0,y1]);});
    bxMergeRects(R).forEach(function(r){X.push(r[0],r[1],r[1],r[0],r[0],null);Y.push(r[2],r[2],r[3],r[3],r[2],null);});""")

    # ---- 2b. banyak kotak di Penampang 2D -> WebGL ----
    s = rep(s, "out.push({type:'scatter',mode:'lines',x:X,y:Y,fill:'toself',fillcolor:ci.col,opacity:Math.max(0.35,BX.ui.op),line:{width:0.4,color:ci.col},name:BX.ui.attr+' '+ci.lab+' ('+L.length+')',hoverinfo:'name',showlegend:true});});",
            "out.push(bx2dGl({type:'scatter',mode:'lines',x:X,y:Y,fill:'toself',fillcolor:ci.col,opacity:Math.max(0.35,BX.ui.op),line:{width:0.4,color:ci.col},name:BX.ui.attr+' '+ci.lab+' ('+L.length+')',hoverinfo:'name',showlegend:true},X.length/6));});")
    s = rep(s, "out.push({type:'scatter',mode:'lines',x:X,y:Y,fill:'toself',fillcolor:ci.col,opacity:Math.max(0.35,BX.ui.op),line:{width:0.4,color:ci.col},name:BX.ui.attr+' '+ci.lab+' ('+R.n[k]+')',hoverinfo:'name',showlegend:true});});",
            "out.push(bx2dGl({type:'scatter',mode:'lines',x:X,y:Y,fill:'toself',fillcolor:ci.col,opacity:Math.max(0.35,BX.ui.op),line:{width:0.4,color:ci.col},name:BX.ui.attr+' '+ci.lab+' ('+R.n[k]+')',hoverinfo:'name',showlegend:true},X.length/6));});")

    # ---- 3. digitasi manual dig block ----
    # dbDig menandai sesi digitasi sebagai dig block
    s = rep(s, "function dbDig(){if(!dbEnsure())return;var U=dbU();U.snap=U.snap!==false;",
            "function dbDig(){if(!dbEnsure())return;var U=dbU();U.snap=U.snap!==false;DG.dbm=String(U.dbMat||'ORE');")
    # Enter menutup poligon saat mendigit dig block; dgCancel/dgFinish melepas tanda
    s = rep(s, "if(e.key==='Enter'){dgFinish(false);e.preventDefault();}",
            "if(e.key==='Enter'){dgFinish(!!DG.dbm);e.preventDefault();}")
    s = rep(s, "function dgCancel(){DG.on=false;", "function dgCancel(){DG.dbm=null;DG.on=false;")
    # dgFinish: dig block manual dapat nomor & warna dari aturan material + cap flitch + id
    s = rep(s, """  var no=parseInt($('dgNo').value)||dgNext();DG.S.push({no:no,d:$('dgDesc').value||'',closed:!!closed,pts:DG.cur.slice(),pl:DG.pl,col:DG.pal[DG.S.length%DG.pal.length],vis:true});
  $('dgNo').value=no+1;DG.on=false;DG.cur=[];DG.c2=[];dgSave();dgList();dgDraw();dgState();updatePlot();}""",
            """  var dbm=DG.dbm,o={no:parseInt($('dgNo').value)||dgNext(),d:$('dgDesc').value||'',closed:!!closed,pts:DG.cur.slice(),pl:DG.pl,col:DG.pal[DG.S.length%DG.pal.length],vis:true};
  if(dbm&&closed&&window.dbSN){/* dig block manual: samakan dengan dig block otomatis */
    var B=lyBench(),t=dbSN(o.d||dbm);o.d=o.d||dbm;o.no=t.n;o.col=t.c;o.db={top:B[0],bot:B[1]};o.manual=true;o.id=dbId();}
  DG.S.push(o);DG.dbm=null;
  $('dgNo').value=(o.no|0)+1;DG.on=false;DG.cur=[];DG.c2=[];dgSave();dgList();dgDraw();dgState();updatePlot();
  if(o.db){try{if(dbU().sfOn)dbInner(true);}catch(e){}try{dbPanel();}catch(e){}try{if(window.lyPanel)lyPanel();}catch(e){}}}""")
    # panel digitasi manual: daftar dig block + petunjuk Enter
    s = rep(s, """  h+='<div id=dbRun class=dbrun>'+(DG.on?'<b style="color:#e8590c">&#9679; Mendigit</b> &middot; '+dbRunTxt(dbRunCalc()):'Klik <b>Mulai</b>, lalu klik sudut-sudut blok di Penampang 2D. Tonase &amp; kadar dihitung langsung saat mendigit.')+'</div>';""",
            """  h+='<div id=dbRun class=dbrun>'+(DG.on?'<b style="color:#e8590c">&#9679; Mendigit</b> &middot; '+dbRunTxt(dbRunCalc()):'Klik <b>Mulai</b>, lalu klik sudut-sudut blok di Penampang 2D. Tonase &amp; kadar dihitung langsung saat mendigit.')+'</div>';
  h+='<div class=hint style="margin-top:2px"><b>Enter</b> = tutup poligon &amp; simpan &middot; <b>Backspace</b> = undo titik &middot; <b>Esc</b> = batal. Dig block manual langsung memakai nomor &amp; warna string material <b>'+bxE(U.dbMat)+'</b> dan langsung masuk daftar di bawah &mdash; bentuk, warna, nama &amp; lokasi tujuannya bisa diedit sama seperti hasil otomatis.</div>';
  h+='<div class=dbsub>&#9776; Daftar dig block di flitch ini</div>'+dbTable();""")
    return s
