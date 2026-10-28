/* ================= GC-Ex Drillhole 0.16: SELUBUNG MINERALISASI (envelope / halo) per domain vein =================
   Alur yang umum di proyek: domain vein utama dibatasi COG tertentu, lalu dibuat selubung (halo) ber-COG lebih kecil
   (mis. Au > 0,2 g/t) di sekitar vein; estimasi halo memakai soft boundary.
   - Selubung = domain khusus yang terikat ke satu domain vein (d.env = id vein). Interval halo disimpan di lapisan
     TERPISAH (GM.envF), sehingga boleh menumpuk dengan flag vein (satu interval bor tetap bisa vein, halo = di luarnya).
   - Usulan otomatis: run kadar >= COG halo (dengan dilusi internal & panjang min) yang MENYENTUH / dekat run vein di bor
     yang sama, dikurangi interval vein; opsional dibatasi jarak perluasan maks dari kontak vein. Bor tanpa vein bisa
     diikutkan (opsi). Bisa dikoreksi manual di Penampang 2D (mode Flag / Hapus flag saat domain selubung aktif).
   - Solid selubung (RBF HW/FW biasa) dibangun dari kontak LUAR = gabungan vein + halo per bor. Di sisi yang tidak punya
     halo, kontak luar = kontak vein -> selubung pinch-out ke vein di sisi itu (tidak harus melingkupi seluruh vein).
   - Model Estimation: blok di dalam solid vein = milik vein; blok selubung = di dalam solid selubung DAN di luar solid vein.
     Komposit halo: soft boundary (halo + sampel vein, bawaan) atau hard boundary (halo saja).
   - Atribut Domain vein (Geological Modelling) juga memberi kode halo -> Geostatistik bisa memfilter halo. */
var ENVD={cut:0.2,dil:3,minL:1,ext:0,iso:false,soft:true};
function envIs(d){if(typeof d==='string')d=gmDom(d);return !!(d&&d.env);}
function envOf(vid){for(var i=0;i<GM.doms.length;i++)if(GM.doms[i].env===vid)return GM.doms[i];return null;}
function envO(d){return Object.assign({},ENVD,d&&d.envO||{});}
function envStore(id){GM.envF=GM.envF||{};return GM.envF[id]||(GM.envF[id]={});}
function envMerge(L,tol){tol=tol==null?1e-6:tol;var o=[];L.slice().sort(function(a,b){return a[0]-b[0];}).forEach(function(r){var l=o[o.length-1];if(l&&r[0]<=l[1]+tol)l[1]=Math.max(l[1],r[1]);else o.push([r[0],r[1]]);});return o;}
function envSub(L,V){var out=[];L.forEach(function(r){var P=[[r[0],r[1]]];V.forEach(function(v){var nx=[];P.forEach(function(p){if(v[1]<=p[0]||v[0]>=p[1]){nx.push(p);return;}if(v[0]>p[0])nx.push([p[0],v[0]]);if(v[1]<p[1])nx.push([v[1],p[1]]);});P=nx;});P.forEach(function(p){if(p[1]-p[0]>1e-6)out.push(p);});});return out;}
/* interval vein (seluruh grup vein: induk + cabang) di satu bor */
function envVeinIv(d,hole){var G=new Set(window.gmGroup?gmGroup(d.env):[d.env]);return envMerge((GM.flags[hole]||[]).filter(function(f){return G.has(f[2]);}).map(function(f){return[f[0],f[1]];}),0.01);}
function envHalo(d,hole){var S=(GM.envF&&GM.envF[d.id])||{};return(S[hole]||[]).slice();}
function envSetIv(eid,hole,f,t,on){var d=gmDom(eid);if(!d)return;var S=envStore(eid),L=S[hole]||[];f=+f;t=+t;if(!(t>f))return;
  L=envSub(L,[[f,t]]);if(on)L=envMerge(L.concat(envSub([[f,t]],envVeinIv(d,hole))),1e-6);if(L.length)S[hole]=L;else delete S[hole];}
function envStat(d){var S=(GM.envF&&GM.envF[d.id])||{},nh=0,m=0;Object.keys(S).forEach(function(h){if(!S[h].length)return;nh++;S[h].forEach(function(r){m+=r[1]-r[0];});});return{nh:nh,m:m};}
/* ---------- usulan otomatis halo ---------- */
function envAuto(eid,silent){var d=gmDom(eid);if(!d||!d.env)return;var v=gmDom(d.env);if(!v){alert('Domain vein induk selubung ini tidak ada.');return;}var O=envO(d),ei=elements.indexOf(GM.opt.el||$('elementFilter').value);if(ei<0){alert('Pilih unsur.');return;}
  var ids=visHoles();if(GM.opt.scope==='slab'){var K=secK().K;ids=ids.filter(function(id){var h=holeData[id];if(!h)return false;var pp=h.pp||[{x:h.x,y:h.y,z:h.z},getXYZ(id,h.maxD)];for(var j=1;j<pp.length;j++)if(clipSeg(pp[j-1],pp[j],K))return true;return false;});}
  gmPush();var S=envStore(eid),nh=0,len=0,nv=0;
  ids.forEach(function(id){var V=envVeinIv(d,id);if(V.length)nv++;var R=gmAutoRuns(id,ei,{cut:+O.cut,dil:+O.dil,minL:+O.minL}).map(function(r){return[r.f,r.t];});
    var keep=R.filter(function(r){if(!V.length)return !!O.iso;return V.some(function(q){return r[0]<=q[1]+(+O.dil)+1e-6&&r[1]>=q[0]-(+O.dil)-1e-6;});});
    var H=envSub(keep,V);if(+O.ext>0&&V.length){var Wn=envMerge(V.map(function(q){return[q[0]-(+O.ext),q[1]+(+O.ext)];}));H=H.map(function(r){var o=[];Wn.forEach(function(w){var a=Math.max(r[0],w[0]),b=Math.min(r[1],w[1]);if(b>a)o.push([a,b]);});return o;}).reduce(function(a,b){return a.concat(b);},[]);}
    H=H.filter(function(r){return r[1]-r[0]>0.05;});if(H.length){S[id]=envMerge(H);nh++;H.forEach(function(r){len+=r[1]-r[0];});}else delete S[id];});
  d.envMsg=nh?'Halo diusulkan di <b>'+nh+'</b> bor ('+len.toFixed(1)+' m) dari '+nv+' bor yang menembus '+gmE(v.name)+'. Koreksi di Penampang 2D bila perlu.':'<span class=warn>Tidak ada halo &ge; '+O.cut+' yang menyambung ke '+gmE(v.name)+(GM.opt.scope==='slab'?' di slab aktif':'')+'.</span>';
  if(!silent)gmDirty();}
function envNew(vid){var v=gmDom(vid);if(!v||v.env)return;if(envOf(vid)){GM.act=envOf(vid).id;gmPanel();return;}
  var d=gmAddDom(v.name+'_HALO');d.env=vid;d.envO=Object.assign({},ENVD);d.col=envTint(v.col);d.im=Object.assign({},imPar(v),{on:imPar(v).on});
  var i=gmIdx(d.id),j=gmIdx(vid);GM.doms.splice(i,1);GM.doms.splice(j+1,0,d);GM.act=d.id;envAuto(d.id,true);gmDirty();}
function envTint(c){var m=/^#?([0-9a-f]{6})$/i.exec(String(c||''));if(!m)return '#f2c879';var n=parseInt(m[1],16),r=n>>16,g=(n>>8)&255,b=n&255,k=0.55;r=Math.round(r+(255-r)*k);g=Math.round(g+(255-g)*k);b=Math.round(b+(255-b)*k);return '#'+((1<<24)|(r<<16)|(g<<8)|b).toString(16).slice(1);}
function envSetO(eid,k,v){var d=gmDom(eid);if(!d)return;d.envO=envO(d);d.envO[k]=v;if(window.SA&&SA.dirty)SA.dirty();gmPanel();}
function envCopyEst(eid){var d=gmDom(eid),v=d&&gmDom(d.env);if(!v||!meParOf(v)){alert('Domain vein belum punya parameter estimasi.');return;}d.est=JSON.parse(JSON.stringify(v.est));d.est.src=(v.est.src||'')+' (disalin dari '+v.name+')';gmDirty(true);try{mePanel();}catch(e){}}
/* ---------- integrasi ke Geological Modelling ---------- */
(function(){
  /* kontak luar selubung = gabungan vein + halo per bor */
  var _gr=gmRuns;gmRuns=function(dom){var d=gmDom(dom);if(!d||!d.env)return _gr.apply(this,arguments);var R=[],hs={};
    Object.keys(GM.flags).forEach(function(h){hs[h]=1;});Object.keys((GM.envF&&GM.envF[d.id])||{}).forEach(function(h){hs[h]=1;});
    Object.keys(hs).forEach(function(h){if(!holeData[h])return;var H=envHalo(d,h);if(!H.length)return;/* bor tanpa halo tidak memberi kontak selubung -> diinterpolasi */
      envMerge(H.concat(envVeinIv(d,h)),0.05).forEach(function(r){var t=Math.min(r[1],holeData[h].maxD);if(t>r[0])R.push({id:h,f:r[0],t:t});});});
    /* bor yang menembus vein tapi tanpa halo: kontak luar = kontak vein (halo pinch-out di bor itu) */
    Object.keys(GM.flags).forEach(function(h){if(!holeData[h]||envHalo(d,h).length)return;envVeinIv(d,h).forEach(function(r){var t=Math.min(r[1],holeData[h].maxD);if(t>r[0])R.push({id:h,f:r[0],t:t});});});
    return R;};
  var _sr=gmSetRange;gmSetRange=function(id,f,t,dom){var d=dom?gmDom(dom):null;if(d&&d.env){envSetIv(d.id,id,f,t,true);return;}
    if(!dom&&GM.act&&envIs(GM.act)&&(GM.mode==='flag'||GM.mode==='erase')){envSetIv(GM.act,id,f,t,false);return;}return _sr.apply(this,arguments);};
  var _gc=gmCodeAt;gmCodeAt=function(id,m){var c=_gc.apply(this,arguments);if(c>=0||!GM.envF)return c;for(var k in GM.envF){var L=GM.envF[k][id];if(!L)continue;for(var i=0;i<L.length;i++)if(L[i][0]<=m&&m<L[i][1]){var ix=gmIdx(k);if(ix>=0)return ix;}}return c;};
  var _pu=gmPush;gmPush=function(){GM.und.push(JSON.stringify({__e:1,f:GM.flags,e:GM.envF||{}}));if(GM.und.length>40)GM.und.shift();};
  var _un=gmUndo;gmUndo=function(){if(!GM.und.length)return;var o=JSON.parse(GM.und.pop());if(o&&o.__e){GM.flags=o.f||{};GM.envF=o.e||{};}else GM.flags=o;gmDirty();};
  var _au=gmAuto;gmAuto=function(){if(GM.act&&envIs(GM.act))return envAuto(GM.act);return _au.apply(this,arguments);};
  var _pk=gmPack;gmPack=function(){var o=_pk.apply(this,arguments);o.envF=GM.envF||{};return o;};
  var _ld=gmLoad;gmLoad=function(o){var r=_ld.apply(this,arguments);GM.envF=(o&&o.envF)||{};return r;};
  var _dd=gmDelDom;gmDelDom=function(id){var d=gmDom(id),e=d&&!d.env?envOf(id):null;var r=_dd.apply(this,arguments);if(!gmDom(id)){if(GM.envF)delete GM.envF[id];if(e&&gmDom(e.id)){delete e.env;if(GM.envF)delete GM.envF[e.id];gmDirty();}}return r;};
  /* pita halo di Penampang 2D (warna selubung, di posisi yang sama dengan pita domain) */
  var _rb=gmRibbons2D;gmRibbons2D=function(o,F){var out=_rb.apply(this,arguments);try{if(!o.vis||!GM.lay.band||!GM.envF)return out;if($('geoRib').checked&&+$('geoAttr').value===GMCI)return out;var W=Math.max(0.5,(+$('geoW').value||2)*0.55),gap=Math.max(0.3,W*0.4);
      GM.doms.forEach(function(d){if(!d.env||!d.vis)return;var x=[],y=[];o.vis.forEach(function(id){envHalo(d,id).forEach(function(f){if(!holeData[id])return;var t=Math.min(f[1],holeData[id].maxD);if(t<=f[0])return;
          var sg=clipSeg(getXYZ(id,f[0]),getXYZ(id,t),o.K);if(!sg)return;var A=F(sg[0].x,sg[0].y,sg[0].z),B=F(sg[1].x,sg[1].y,sg[1].z),dx=B[0]-A[0],dy=B[1]-A[1],L=Math.sqrt(dx*dx+dy*dy);if(L<1e-6)return;
          var px=-dy/L,py=dx/L;if(px>0||(px===0&&py>0)){px=-px;py=-py;}x.push(A[0]+px*gap,B[0]+px*gap,B[0]+px*(gap+W),A[0]+px*(gap+W),A[0]+px*gap,null);y.push(A[1]+py*gap,B[1]+py*gap,B[1]+py*(gap+W),A[1]+py*(gap+W),A[1]+py*gap,null);});});
        if(x.length)out.push({type:'scatter',mode:'lines',x:x,y:y,fill:'toself',fillcolor:d.col,line:{color:d.col,width:0.8,dash:'dot'},opacity:0.9,name:'Halo '+d.name,legendgroup:'gm'+d.id,showlegend:true,hoverinfo:'name'});});}catch(e){console.error(e);}return out;};
  /* panel: tombol + Selubung di kartu vein, pengaturan di kartu selubung */
  var _gp=gmPanel;gmPanel=function(){var r=_gp.apply(this,arguments);try{var b=$('gmBody');if(!b)return r;
    b.querySelectorAll('.gmd').forEach(function(c){var rd=c.querySelector('input[type=radio][onchange*="gmAct("]');if(!rd)return;var m=/gmAct\('([^']+)'\)/.exec(rd.getAttribute('onchange')||'');if(!m)return;var d=gmDom(m[1]);if(!d)return;
      if(d.env){var v=gmDom(d.env),st=envStat(d),O=envO(d),sel=c.querySelector('select.gmpar,span.gmpar');var lab=document.createElement('span');lab.className='gmpar envlab';lab.innerHTML='&#9676; selubung dari <b>'+gmE(v?v.name:'?')+'</b> &middot; COG '+O.cut;if(sel)sel.replaceWith(lab);else c.appendChild(lab);
        var sm=c.querySelector('small');if(sm)sm.innerHTML='halo '+st.nh+' bor &middot; '+st.m.toFixed(1)+' m';c.classList.add('envd');
        if(d.id===GM.act){var box=document.createElement('div');box.className='envbox';
          box.innerHTML='<div class=g2><div><label title="Batas kadar halo">COG halo</label><input type=number step=any value="'+O.cut+'" onchange="envSetO(\''+d.id+'\',\'cut\',+this.value)"></div><div><label title="Sela waste maks. di dalam halo">Dilusi (m)</label><input type=number step=any min=0 value="'+O.dil+'" onchange="envSetO(\''+d.id+'\',\'dil\',+this.value)"></div><div><label>Panjang min.</label><input type=number step=any min=0 value="'+O.minL+'" onchange="envSetO(\''+d.id+'\',\'minL\',+this.value)"></div><div><label title="Perluasan maks. halo dari kontak vein di sepanjang bor (0 = bebas)">Maks dari vein</label><input type=number step=any min=0 value="'+O.ext+'" onchange="envSetO(\''+d.id+'\',\'ext\',+this.value)"></div></div>'+
            '<label class=sw><input type=checkbox '+(O.iso?'checked':'')+' onchange="envSetO(\''+d.id+'\',\'iso\',this.checked)">Ikutkan bor yang tidak menembus vein (halo tanpa vein)</label>'+
            '<label class=sw><input type=checkbox '+(O.soft?'checked':'')+' onchange="envSetO(\''+d.id+'\',\'soft\',this.checked);gmDirty(true)">Estimasi soft boundary (komposit halo + vein)</label>'+
            '<div class=g2><button class=btn-pri onclick="envAuto(\''+d.id+'\')">&#9676; Usulkan halo</button><button onclick="envCopyEst(\''+d.id+'\')" title="Salin variogram, pass & top-cut dari domain vein">Salin parameter vein</button></div>'+
            (d.envMsg?'<div class=hint>'+d.envMsg+'</div>':'')+'<div class=hint>Koreksi manual: tab Flag &rarr; &#9998; Flag / &#9003; Hapus flag saat selubung aktif hanya mengubah halo (flag vein aman). Lalu String &rarr; Tarik otomatis &amp; Solid seperti vein biasa; di sisi tanpa halo selubung pinch-out ke kontak vein.</div>';
          box.insertAdjacentHTML('afterbegin','<div class=envh>&#9676; Selubung <b>'+gmE(d.name)+'</b> <small>(halo '+gmE(v?v.name:'?')+')</small></div>');
          var nr=$('gmNewNm'),row=nr&&nr.closest('.g2');if(row&&row.parentNode)row.parentNode.insertBefore(box,row.nextSibling);else c.appendChild(box);}}
      else if(!gmIsKid(d)&&!envOf(d.id)){var bt=document.createElement('button');bt.className='envadd';bt.title='Buat selubung (halo) ber-COG lebih kecil di sekitar vein ini';bt.innerHTML='&#9676; + Selubung';bt.onclick=function(e){e.stopPropagation();envNew(d.id);};var sm2=c.querySelector('small');if(sm2)sm2.appendChild(bt);else c.appendChild(bt);}});
  }catch(e){console.error(e);}return r;};
})();
/* ---------- integrasi ke Model Estimation ---------- */
(function(){if(typeof meRuns!=='function')return;
  var _mr=meRuns;meRuns=function(dom){var d=gmDom(dom);if(!d||!d.env)return _mr.apply(this,arguments);var O=envO(d),R={};
    var hs={};Object.keys((GM.envF&&GM.envF[d.id])||{}).forEach(function(h){hs[h]=1;});if(O.soft)Object.keys(GM.flags).forEach(function(h){hs[h]=1;});
    Object.keys(hs).forEach(function(h){if(!holeData[h])return;var L=envHalo(d,h);if(O.soft)L=L.concat(envVeinIv(d,h));L=envMerge(L).map(function(r){return[r[0],Math.min(r[1],holeData[h].maxD)];}).filter(function(r){return r[1]>r[0];});if(L.length)R[h]=L;});return R;};
  var _mg=meGrpR;meGrpR=function(d){if(!d||!d.env)return _mg.apply(this,arguments);var R0=IM.R[d.id];if(!R0||!R0.mesh)return R0;var v=gmDom(d.env),RV=v?_mg(v):null;
    var key=R0.key+'|'+(RV&&RV.key||RV&&RV.mesh&&RV.mesh.x&&RV.mesh.x.length||'-');ME._env=ME._env||{};var c=ME._env[d.id];if(c&&c.key===key)return c;
    var WO=R0._W||(R0._W=wfInside(R0.mesh)),WV=RV&&RV.mesh?(RV.W||RV._W||(RV._W=wfInside(RV.mesh))):null;
    c={key:key,mesh:R0.mesh,W:{f:function(x,y,z){return WO.f(x,y,z)&&!(WV&&WV.f(x,y,z));},open:WO.open||0},fr:R0.fr,st:R0.st,env:true};ME._env[d.id]=c;return c;};
  var _rd=meDomsReady;meDomsReady=function(){var L=_rd.apply(this,arguments);return L.filter(function(d){return !d.env;}).concat(L.filter(function(d){return d.env;}));};})();
(function(){var st=document.createElement('style');st.textContent='#gmBody .gmd.envd{border-left:3px dotted var(--ac,#c49a4c);margin-left:10px}#gmBody .envlab{font-size:11px;color:var(--mu)}'+
  '#gmBody button.envadd{margin-left:6px;font-size:10.5px;padding:0 6px;min-height:18px}#gmBody .envbox{margin:8px 0 4px;padding:7px 8px;border:1px solid var(--bd);border-left:4px solid var(--ac,#c49a4c);border-radius:6px;background:var(--sf2)}#gmBody .envbox .envh{font-size:12px;margin-bottom:4px}#gmBody .envbox .g2{gap:5px;margin-bottom:4px}#gmBody .envbox label{font-size:10.5px}#gmBody .envbox input[type=number]{width:100%}';document.head.appendChild(st);})();
