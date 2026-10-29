/* ================= GC-Ex Block Model 0.14: blok BM di Penampang 2D sebagai SATU gambar raster =================
   Sebelumnya (0.13) blok digambar sebagai ribuan path SVG / WebGL. WebGL Plotly selalu berada DI ATAS garis SVG,
   sehingga garis dig block, string & poligon as-mined tertutup blok, dan zoom masih berat.
   Sekarang semua blok (semua kelas) dilukis ke satu kanvas lalu dipasang sebagai layout.images (layer 'below'):
   zoom / geser hanya menskalakan satu gambar (ringan, tanpa jeda), dan semua garis / poligon selalu tampil di atasnya.
   Legenda kelas tetap ada (trace legenda tanpa data). Gambar di-cache: digitasi / hover tidak melukis ulang. */
var BMIMG={on:true,cur:null,t:0,key:'',url:'',box:null,max:3200};
function bmImgRaster(T){var x0=1e300,x1=-1e300,y0=1e300,y1=-1e300,mw=1e300,ks=[T.length],i,t;
  for(var k=0;k<T.length;k++){t=T[k];var X=t.x,Y=t.y;ks.push(t.fillcolor,t.opacity,X.length);
    for(i=0;i+4<X.length;i+=6){var a=X[i],b=X[i+1],c=Y[i],d=Y[i+2];if(a===null||b===null)continue;if(a<x0)x0=a;if(b>x1)x1=b;if(c<y0)y0=c;if(d>y1)y1=d;var w=Math.min(b-a,d-c);if(w>1e-6&&w<mw)mw=w;}
    if(X.length>6)ks.push(X[0],Y[0],X[X.length-6],Y[Y.length-6]);}
  if(!(x1>x0&&y1>y0))return null;var key=ks.join('|')+'|'+x0+'|'+x1+'|'+y0+'|'+y1;
  if(key===BMIMG.key&&BMIMG.url)return BMIMG.box;
  /* resolusi: blok terkecil = 4 piksel bulat (tepi blok tetap tajam saat zoom), dikecilkan bila melebihi BMIMG.max piksel */
  var sx=x1-x0,sy=y1-y0,mwc=Math.max(mw,1e-3),kp=4;while(kp>1&&Math.max(sx,sy)*kp/mwc>BMIMG.max)kp--;var ppm=Math.min(kp/mwc,BMIMG.max/sx,BMIMG.max/sy);if(!(ppm>0))return null;
  /* piksel diisi langsung ke larik (tanpa API kanvas per kotak: jutaan fillRect lambat di GPU), lalu dikodekan PNG */
  var W=Math.max(1,Math.round(sx*ppm)),H=Math.max(1,Math.round(sy*ppm)),buf=new Uint32Array(W*H);
  T.forEach(function(t){var px=bmImgRGBA(t.fillcolor||(t.line&&t.line.color)||'#999',t.opacity==null?1:t.opacity),X=t.x,Y=t.y;
    for(var j=0;j+4<X.length;j+=6){var a=X[j],b=X[j+1],c=Y[j],d=Y[j+2];if(a===null||b===null)continue;
      var px0=Math.max(0,Math.floor((a-x0)*ppm+1e-6)),px1=Math.min(W,Math.max(px0+1,Math.ceil((b-x0)*ppm-1e-6))),py0=Math.max(0,Math.floor((y1-d)*ppm+1e-6)),py1=Math.min(H,Math.max(py0+1,Math.ceil((y1-c)*ppm-1e-6)));
      for(var yy=py0;yy<py1;yy++)buf.fill(px,yy*W+px0,yy*W+px1);}});
  var cv=document.createElement('canvas');cv.width=W;cv.height=H;cv.getContext('2d',{willReadFrequently:true}).putImageData(new ImageData(new Uint8ClampedArray(buf.buffer),W,H),0,0);
  /* gambar besar: pratinjau kecil dulu (cepat), PNG penuh dikodekan di latar (toBlob, tidak membekukan layar) */
  BMIMG.key=key;var big=W*H>1.5e6&&cv.toBlob,src;
  if(big){var f=Math.ceil(Math.sqrt(W*H/4e5)),pw=Math.ceil(W/f),ph=Math.ceil(H/f),pb=new Uint32Array(pw*ph);for(var yy=0;yy<ph;yy++){var r0=yy*f*W;for(var xx=0;xx<pw;xx++)pb[yy*pw+xx]=buf[r0+xx*f];}
    var pv=document.createElement('canvas');pv.width=pw;pv.height=ph;pv.getContext('2d',{willReadFrequently:true}).putImageData(new ImageData(new Uint8ClampedArray(pb.buffer),pw,ph),0,0);src=pv.toDataURL('image/png');}
  else src=cv.toDataURL('image/png');
  buf=null;
  if(BMIMG.blob){try{URL.revokeObjectURL(BMIMG.blob);}catch(e){}BMIMG.blob='';}
  BMIMG.url=src;BMIMG.box={source:src,xref:'x',yref:'y',x:x0,y:y1,sizex:sx,sizey:sy,xanchor:'left',yanchor:'top',sizing:'stretch',layer:'below',opacity:1,name:'bmimg'};
  if(big){var myKey=key;cv.toBlob(function(b){if(!b||BMIMG.key!==myKey)return;var u=URL.createObjectURL(b);BMIMG.blob=u;BMIMG.url=u;BMIMG.box.source=u;
    var gd=document.getElementById('plotDiv'),I=gd&&gd.layout&&gd.layout.images;if(!I)return;for(var q=0;q<I.length;q++)if(I[q]&&I[q].name==='bmimg'){var o={};o['images['+q+'].source']=u;try{Plotly.relayout(gd,o);}catch(e){}break;}},'image/png');}
  return BMIMG.box;}
/* warna CSS apa pun -> piksel RGBA 32-bit (little-endian: A B G R) */
var BMRGBA={};
function bmImgRGBA(c,op){var k=c+'|'+op;if(BMRGBA[k]!==undefined)return BMRGBA[k];var g=bmImgRGBA.g||(bmImgRGBA.g=document.createElement('canvas').getContext('2d'));
  g.fillStyle='#000';g.fillStyle=c;var s=String(g.fillStyle),r=0,gg=0,b=0,a=1,m;
  if(s[0]==='#'){r=parseInt(s.substr(1,2),16);gg=parseInt(s.substr(3,2),16);b=parseInt(s.substr(5,2),16);}
  else if((m=/rgba?\(([^)]+)\)/.exec(s))){var p=m[1].split(',').map(parseFloat);r=p[0];gg=p[1];b=p[2];if(p.length>3)a=p[3];}
  var A=Math.max(0,Math.min(255,Math.round(a*op*255)));return BMRGBA[k]=((A<<24)|(b<<16)|(gg<<8)|r)>>>0;}
(function(){if(typeof window.bxTraces2D!=='function')return;var _bt=bxTraces2D;
  /* blok sudah dilukis per kotak di kanvas -> penggabungan persegi panjang (sort jutaan kotak) tidak diperlukan */
  if(typeof window.bxMergeRects==='function'){var _mr=bxMergeRects;bxMergeRects=function(R){return BMIMG.on&&R.length>5000?R:_mr(R);};}
  /* hasil penampang di-cache: menggambar ulang tanpa perubahan data / sayatan / kelas tidak menghitung ulang jutaan blok */
  var C2={k:null,T:null,img:null};
  bxTraces2D=function(o,F){var key=null;
    try{if(BMIMG.on&&BX.m&&!(window.lyFcOn&&lyFcOn())&&$('bxShow')&&$('bxShow').checked){var S=bxSel({clip:true,K:o.K}),U=BX.ui;
      key=[S,JSON.stringify([o.K,o.g,offX,offY,U.op,U.attr,U.cls[U.attr]||0,U.catCol[U.attr]||0,U.catOn[U.attr]||0])];
      if(C2.k&&C2.k[0]===key[0]&&C2.k[1]===key[1]&&C2.T){BMIMG.cur=C2.img;BMIMG.t=Date.now();if(C2.img&&BMIMG.box)BMIMG.cur=BMIMG.box;return C2.T.slice();}}}catch(e){key=null;}
    var T=bxTraces2Dr.apply(this,arguments);C2.k=key;C2.T=T&&T.slice();C2.img=BMIMG.cur;return T;};
  var bxTraces2Dr=function(o,F){var T=_bt.apply(this,arguments);BMIMG.cur=null;if(!BMIMG.on||!T||!T.length)return T;
    var R=T.filter(function(t){return t&&t.fill==='toself'&&Array.isArray(t.x);});if(!R.length)return T;var img=null;try{img=bmImgRaster(R);}catch(e){console.error(e);}if(!img)return T;
    BMIMG.cur=img;BMIMG.t=Date.now();
    var bb={type:'scatter',mode:'markers',x:[img.x,img.x+img.sizex],y:[img.y-img.sizey,img.y],marker:{size:1,opacity:0},hoverinfo:'skip',showlegend:false,name:'bmimg-bb'};
    return [bb].concat(T.map(function(t){if(R.indexOf(t)<0)return t;return{type:'scatter',mode:'markers',x:[null],y:[null],name:t.name,showlegend:t.showlegend!==false,hoverinfo:'skip',
      marker:{symbol:'square',size:11,color:t.fillcolor,opacity:Math.min(1,(t.opacity||1)+0.15),line:{width:0}}};}));};
  var _r=Plotly.react;Plotly.react=function(gd,d,L,c){try{var id=typeof gd==='string'?gd:gd&&gd.id;
      if(id==='plotDiv'&&L&&typeof L==='object'&&!L.scene){var I=(L.images||[]).filter(function(q){return q&&q.name!=='bmimg';});
        if(BMIMG.cur&&Date.now()-BMIMG.t<2000)I.push(BMIMG.cur);BMIMG.cur=null;L.images=I;
        /* garis string / dig block / poligon diberi tepi gelap supaya tetap kontras di atas warna blok */
        if(Array.isArray(d)&&BMIMG.halo!==false){var o2=[];d.forEach(function(t){if(t&&(t.type==='scatter'||t.type==null)&&/lines/.test(t.mode||'')&&!t.fill&&t.line&&typeof t.line.color==='string'&&/^(String|Dig|Poligon|As-?mined|AM )/i.test(t.name||'')&&Array.isArray(t.x)&&t.x.length<200000)
            o2.push({type:'scatter',mode:'lines',x:t.x,y:t.y,line:{color:'rgba(20,22,26,.72)',width:(t.line.width||2)+2.6},hoverinfo:'skip',showlegend:false,name:'halo'});o2.push(t);});d=o2;arguments[1]=d;}}}catch(e){console.error(e);}
    return _r.apply(this,arguments);};
  var st=document.createElement('style');st.textContent='#plotDiv .layer-below image,#plotDiv .layer-above image{image-rendering:pixelated;image-rendering:crisp-edges}';document.head.appendChild(st);})();
