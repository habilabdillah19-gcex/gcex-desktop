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
  var sx=x1-x0,sy=y1-y0,ppm=Math.min(BMIMG.max/sx,BMIMG.max/sy,Math.max(2,6/Math.max(mw,1e-3)));if(!(ppm>0))return null;
  var W=Math.max(1,Math.round(sx*ppm)),H=Math.max(1,Math.round(sy*ppm)),cv=document.createElement('canvas');cv.width=W;cv.height=H;var g=cv.getContext('2d');g.imageSmoothingEnabled=false;
  T.forEach(function(t){var X=t.x,Y=t.y;g.globalAlpha=t.opacity==null?1:t.opacity;g.fillStyle=t.fillcolor||(t.line&&t.line.color)||'#999';
    for(var j=0;j+4<X.length;j+=6){var a=X[j],b=X[j+1],c=Y[j],d=Y[j+2];if(a===null||b===null)continue;
      var px0=Math.floor((a-x0)*ppm),px1=Math.ceil((b-x0)*ppm),py0=Math.floor((y1-d)*ppm),py1=Math.ceil((y1-c)*ppm);g.fillRect(px0,py0,Math.max(1,px1-px0),Math.max(1,py1-py0));}});
  BMIMG.key=key;BMIMG.url=cv.toDataURL('image/png');
  BMIMG.box={source:BMIMG.url,xref:'x',yref:'y',x:x0,y:y1,sizex:sx,sizey:sy,xanchor:'left',yanchor:'top',sizing:'stretch',layer:'below',opacity:1,name:'bmimg'};return BMIMG.box;}
(function(){if(typeof window.bxTraces2D!=='function')return;var _bt=bxTraces2D;
  bxTraces2D=function(o,F){var T=_bt.apply(this,arguments);BMIMG.cur=null;if(!BMIMG.on||!T||!T.length)return T;
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
