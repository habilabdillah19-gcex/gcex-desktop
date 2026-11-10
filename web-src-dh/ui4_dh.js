/* ================= GC-Ex Drillhole 0.12: menu Sayatan di bilah atas, Peta (Mapping) & Layout terpisah =================
   - Bilah atas: satu tombol "Sayatan ▾" berisi Penampang (Sayatan) 2D, Sayatan 3D, opsi slab, digitasi string,
     dan pengaturan Sayatan & Penampang (panel Properti tetap ada).
   - Peta: layer isi peta terperinci (per sumber struktur, per kelompok fitur digitasi, per file / kode pick-up, per domain)
     — hanya memengaruhi peta & layout, tidak mengubah data pemodelan.
   - Titik struktur langsung di peta (Mapping) -> basis data struktur (Struktur Geologi), elevasi dari topografi. */

/* ---------- status peta tambahan ---------- */
if(window.MAP){MAP.hid=MAP.hid||{};MAP.lo=MAP.lo||{leg:true,sc:true,na:true,grid:true};if(MAP.lay&&MAP.lay.lin===undefined)MAP.lay.lin=true;}
function mapHidF(f){return !!(MAP.hid&&MAP.hid['F:'+f.kind+'|'+(f.kind==='str'?f.type:f.name)]);}
function mapHid(k,show){if(!MAP.hid)MAP.hid={};if(show)delete MAP.hid[k];else MAP.hid[k]=1;if(window.SA&&SA.dirty)SA.dirty();mapRefresh();}
function mapLo(k,v){MAP.lo[k]=v;if(window.SA&&SA.dirty)SA.dirty();}

/* ---------- Layer peta (isi peta & layout) ---------- */
function mapLayerHtml(ck,hasT,hasO){var H=MAP.hid||{},sub=function(k,t,on,cnt){return '<label class=sw style="margin:1px 0 1px 20px;font-size:12px"><input type=checkbox '+(on?'checked':'')+' onchange="mapHid(\''+mapE(k).replace(/'/g,'&#39;')+'\',this.checked)">'+t+(cnt!=null?' <small style="opacity:.7">('+cnt+')</small>':'')+'</label>';};
  var h='<h4>Layer peta</h4><div class=hint style="margin-top:-2px">Pilih isi peta untuk tampilan &amp; layout cetak. Hanya memengaruhi peta (tidak mengubah data, Struktur Geologi, maupun pemodelan). Legenda layout mengikuti layer yang tampil.</div>';
  h+='<div class=imsec>Peta dasar</div><div class=g2>'+ck('or','Orthofoto'+(hasO?'':' (belum ada)'),!hasO)+ck('ct','Kontur topografi'+(hasT?'':' (belum ada)'),!hasT)+ck('pit','Desain pit')+ck('lab','Label (collar, kontur)')+'</div>';
  h+='<div class=imsec>Database bor</div><div class=g2>'+ck('co','Collar')+ck('dh','Jejak bor (proyeksi)')+'</div>'+ck('dom','Domain vein (titik tengah interval)');
  if(window.GM&&GM.doms.length&&MAP.lay.dom)h+=GM.doms.map(function(d){return sub('dom:'+d.id,'<span style="color:'+d.col+';font-weight:700">&#9670;</span> '+mapE(d.name),!H['dom:'+d.id]);}).join('');
  h+='<div class=imsec>Struktur</div><div class=g2>'+ck('st','Simbol strike / dip (USGS)')+ck('lin','Panah lineasi (plunge)')+'</div>';
  if(window.STR&&STR.F.length&&MAP.lay.st){var nm=function(f){return f.id==='man'?'Titik manual (3D)':f.id==='gm'?'Flag struktur (Geological Modelling)':f.kind==='mapst'?'Titik struktur (Mapping)':String(f.name);};
    h+=STR.F.map(function(f){var n=STR.P.filter(function(p){return p.fid===f.id;}).length;return n?sub('stf:'+f.id,mapE(nm(f)),!H['stf:'+f.id],n):'';}).join('');}
  h+='<div class=imsec>Fitur digitasi</div>'+ck('F','Boundary &amp; garis hasil digitasi');
  if(MAP.F.length&&MAP.lay.F){var G={};MAP.F.forEach(function(f){var k='F:'+f.kind+'|'+(f.kind==='str'?f.type:f.name);(G[k]=G[k]||{n:0,t:(MAPK[f.kind]||f.kind).replace('Boundary ','')+': '+(f.kind==='str'?f.type:f.name),c:f.kind==='str'?((MAPST[f.type]||{}).c||'#111'):f.col});G[k].n++;});
    h+=Object.keys(G).map(function(k){return sub(k,'<span style="color:'+G[k].c+';font-weight:700">&#9644;</span> '+mapE(G[k].t),!H[k],G[k].n);}).join('');}
  h+='<div class=imsec>Titik pick-up</div>'+ck('pf','Titik pick-up survei / pemetaan');
  if(MAP.PF.length&&MAP.lay.pf){h+=MAP.PF.map(function(f){return sub('pf:'+f.id,mapE(f.name),!H['pf:'+f.id],f.P.length);}).join('');var C={};MAP.PF.forEach(function(f){f.P.forEach(function(p){C[p[4]]=(C[p[4]]||0)+1;});});
    var ks=Object.keys(C).sort();if(ks.length>1)h+='<div class=hint style="margin:2px 0 0 20px">Per kode:</div>'+ks.map(function(c){return sub('pfc:'+c,mapE(c),!H['pfc:'+c],C[c]);}).join('');}
  return h;}
function mapLoHtml(){var L=MAP.lo||{},c=function(k,t){return '<label class=sw style="margin:2px 0"><input type=checkbox '+(L[k]!==false?'checked':'')+' onchange="mapLo(\''+k+'\',this.checked)">'+t+'</label>';};
  return '<div class=imsec>Elemen layout</div><div class=g2>'+c('leg','Legenda')+c('sc','Skala grafis')+c('na','Panah utara')+c('grid','Grid koordinat')+'</div><div class=hint style="margin-top:-2px">Isi peta diatur di bagian <b>Layer peta</b>.</div>';}

/* ---------- Titik struktur di peta (Mapping) ---------- */
function mapStFile(){var f=(STR.F||[]).filter(function(x){return x.id==='mapst';})[0];if(!f){f={id:'mapst',name:'Titik struktur (Mapping)',on:true,kind:'mapst'};STR.F.push(f);}return f;}
function mapStAdd(w){if(!window.STR)return;mapStFile();var z=null;try{z=mapZ(w[0],w[1]);}catch(e){}if(z==null&&window.G)z=G.z1;
  stAdd({x:Math.round(w[0]*100)/100,y:Math.round(w[1]*100)/100,z:z,fid:'mapst'});stDirty(true);mapPanel();mapRefresh();var t=$('mapXY');if(t)t.textContent='Titik struktur ditambahkan (Struktur Geologi › Dari Peta)';}
function mapStHtml(){if(!window.STR)return '';var sd=STR.sd,on=MAP.mode==='stpt',L=STR.P.filter(function(p){return p.fid==='mapst';}),hasT=typeof imTopoOk==='function'&&imTopoOk();
  var h='<h4>Titik struktur</h4><div class=hint style="margin-top:-2px">Klik di peta untuk menaruh pengukuran struktur lapangan. Titik masuk ke <b>Struktur Geologi</b> (satu basis data dengan titik manual, flag GM &amp; pick-up) dan ikut dipakai Geological Modelling. Elevasi dari topografi'+(hasT?'':' <span class=warn>(topografi belum ada: dipakai elevasi puncak data)</span>')+'. Nilai di bawah tetap untuk klik berikutnya.</div>';
  h+='<div class="g3 f"><div><label>Dip (&deg;)</label><input type=number step=any min=0 max=90 value="'+sd.dip+'" onchange="STR.sd.dip=+this.value"></div><div><label>Dip az (&deg;)</label><input type=number step=any min=0 max=360 value="'+sd.az+'" onchange="STR.sd.az=+this.value"></div><div><label>No berikut</label><input type=number step=1 value="'+STR.nx+'" onchange="STR.nx=+this.value||1"></div></div>';
  h+='<div class="g3 f"><div><label>Plunge (&deg;)</label><input type=number step=any min=0 max=90 value="'+(sd.pl!=null?sd.pl:'')+'" placeholder="kosong" onchange="STR.sd.pl=this.value===\'\'?null:+this.value"></div><div><label>Trend (&deg;)</label><input type=number step=any min=0 max=360 value="'+(sd.tr!=null?sd.tr:'')+'" placeholder="kosong" onchange="STR.sd.tr=this.value===\'\'?null:+this.value"></div><div class=hint style="align-self:end;margin:0">plunge / trend = lineasi (opsional)</div></div>';
  h+='<input type=text placeholder="Keterangan (mis. kontak vein, sesar, kekar)" value="'+mapE(sd.ket||'')+'" onchange="STR.sd.ket=this.value" style="margin-bottom:4px">';
  h+='<button class="'+(on?'btn-pri':'')+'" style="width:100%" onclick="MAP.mode=MAP.mode===\'stpt\'?null:\'stpt\';MAP.sel=null;MAP.cur=[];mapPanel();mapDraw()">'+(on?'&#9679; Klik di peta untuk menaruh titik&hellip; (Esc selesai)':'&#9998; Taruh titik struktur di peta')+'</button>';
  if(L.length)h+='<div class=gmlist style="max-height:170px;margin-top:6px"><table class=pltb><tr><th>No</th><th>Dip/Az</th><th>Plunge/Trend</th><th>Ket</th><th></th></tr>'+L.slice().reverse().map(function(p){var q='\''+p.id+'\'';return '<tr><td>'+mapE(p.no)+'</td><td><input type=number step=any value="'+p.dip+'" style="width:40px" onchange="stSet('+q+',\'dip\',+this.value)">/<input type=number step=any value="'+p.az+'" style="width:46px" onchange="stSet('+q+',\'az\',+this.value)"></td>'+
      '<td><input type=number step=any value="'+(p.pl!=null?p.pl:'')+'" placeholder="-" style="width:38px" onchange="stSet('+q+',\'pl\',this.value===\'\'?null:+this.value)">/<input type=number step=any value="'+(p.tr!=null?p.tr:'')+'" placeholder="-" style="width:44px" onchange="stSet('+q+',\'tr\',this.value===\'\'?null:+this.value)"></td><td>'+mapE(p.ket||'')+'</td><td><button class=x onclick="stDel('+q+');mapPanel();mapRefresh()">&times;</button></td></tr>';}).join('')+'</table></div>';
  return h;}

/* ---------- simpan / buka ---------- */
(function(){if(!window.SA)return;var _c=SA.collectWork;SA.collectWork=function(){var w=_c.apply(this,arguments);try{if(w.map){w.map.hid=MAP.hid||{};w.map.lo=MAP.lo;}}catch(e){}return w;};
  var _a=SA.applyWork;SA.applyWork=function(W){try{if(W&&W.map){MAP.hid=W.map.hid||{};MAP.lo=Object.assign({leg:true,sc:true,na:true,grid:true},W.map.lo||{});if(MAP.lay.lin===undefined)MAP.lay.lin=true;}}catch(e){}return _a.apply(this,arguments);};})();

/* ---------- bilah atas: SATU tombol "Slicer" (0.24.56, contoh dari Leapfrog: dip, dip azimuth, lebar slab, langkah, lokasi) ----------
   Mengganti menu "Sayatan ▾". Popup memuat seluruh kendali sayatan: dip / dip azimuth bebas (mode S di secGeom), preset plan / E-W / N-S,
   lebar slab & langkah terpisah, titik pusat (X Y Z, bisa diambil dari pusat data / pusat pandangan), Mundur / Maju, opsi slab,
   Penampang 2D, Sayatan 3D garis bebas, garis di peta, digitasi, pengaturan lanjutan (panel Sayatan). Panel Properti Sayatan tetap ada. */
(function(){var b2=$('btn2d');if(!b2||$('btnSecM'))return;var b3=$('btnSec3');
  var st=document.createElement('style');st.textContent='#secMenu{position:absolute;z-index:2000;display:none;width:340px;background:var(--sf,#fff);color:var(--tx,#212529);border:1px solid var(--bd,#ced4da);border-radius:10px;box-shadow:0 10px 28px rgba(0,0,0,.2);padding:8px}'+
    '#secMenu .smh{font-size:10.5px;font-weight:700;letter-spacing:.04em;color:var(--mu,#868e96);margin:6px 4px 3px;text-transform:uppercase;display:flex;justify-content:space-between;align-items:center}#secMenu .smh button{height:22px;padding:0 7px;font-size:11px}'+
    '#secMenu button.tb,#secMenu .smi{display:flex;align-items:center;gap:8px;width:100%;justify-content:flex-start;height:32px;margin:2px 0;padding:0 10px;border-radius:7px;font-size:12.5px;text-align:left}'+
    '#secMenu .smi{border:0;background:none;color:inherit;cursor:pointer}#secMenu .smi:hover{background:rgba(0,0,0,.06)}#secMenu button.tb svg{width:16px;height:16px}#secMenu label.ck{display:flex;gap:8px;align-items:center;padding:3px 6px;font-size:12.5px;cursor:pointer;border-radius:6px}#secMenu label.ck:hover{background:rgba(0,0,0,.06)}'+
    '#secMenu .slg{display:grid;grid-template-columns:1fr 1fr;gap:6px 8px;margin:4px 0}#secMenu .slg.c3{grid-template-columns:1fr 1fr 1fr}#secMenu .slf{display:flex;flex-direction:column;gap:2px;font-size:11px;color:var(--mu,#868e96)}#secMenu .slf input,#secMenu .slf select{font:inherit;font-size:12.5px;color:var(--tx,#212529);height:26px;padding:0 6px;border:1px solid var(--bd,#ced4da);border-radius:5px;background:var(--bg,#fff);width:100%;box-sizing:border-box}'+
    '#secMenu .slf input[type=range]{height:18px;padding:0;border:0;background:none}#secMenu .slq{display:flex;gap:4px;flex-wrap:wrap;margin:2px 0 4px}#secMenu .slq button{height:24px;padding:0 8px;font-size:11.5px;border-radius:5px}#secMenu .slq button.on{background:var(--mj,#f0c047);border-color:var(--mjln,#d6a12b);color:var(--mjtx,#1d2b5e);font-weight:700}'+
    '#secMenu .slpos{display:grid;grid-template-columns:auto 1fr auto;gap:6px;align-items:center;margin:6px 0 2px}#secMenu .slpos button{height:28px;padding:0 10px;font-weight:600}#secMenu .slpos .slf input{text-align:center;font-weight:600}'+
    '#secMenu hr{border:0;border-top:1px solid var(--bd,#e3e7ec);margin:6px 0}#btnSecM .sm2d{font-size:10px;font-weight:700;background:var(--pr,#1c3d8f);color:#fff;border-radius:4px;padding:0 4px;margin-left:2px}';document.head.appendChild(st);
  var bt=document.createElement('button');bt.className='tb';bt.id='btnSecM';bt.title='Slicer: potong model dari arah mana saja (dip, dip azimuth, lebar slab, langkah, lokasi), sayatan garis bebas, tampilan 2D / 3D, digitasi';
  bt.innerHTML='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 20L20 4"/><rect x="3" y="5" width="18" height="14" rx="1" stroke-width="1.6"/></svg>Slicer<span id=secM2d></span>';
  b2.parentNode.insertBefore(bt,b2);var m=document.createElement('div');m.id='secMenu';document.body.appendChild(m);
  /* Dua tombol tampilan (pemilik 10-11-2026): 'Tampilan 2D' dan 'Tampilan 3D' HANYA berpindah cara melihat sayatan yang sedang aktif.
     Dulu 'Sayatan 3D' membuka alat garis bebas (kini tombol 'Sayatan Garis Bebas') dan 'Sayatan 2D' bolak-balik 2D/3D. */
  var lab=function(b,t){if(!b)return;var n=[].slice.call(b.childNodes).filter(function(n){return n.nodeType===3&&n.textContent.trim();})[0];if(n)n.textContent=t;else b.appendChild(document.createTextNode(t));};
  lab(b2,'Tampilan 2D');b2.title='Lihat sayatan yang aktif sebagai penampang 2D';if(b3){lab(b3,'Tampilan 3D');b3.title='Lihat sayatan yang aktif di jendela 3D';}
  var ck=function(id,t){var e=$(id);if(!e)return '';return '<label class=ck><input type=checkbox '+(e.checked?'checked':'')+' onchange="var e=document.getElementById(\''+id+'\');e.checked=this.checked;e.dispatchEvent(new Event(\'change\',{bubbles:true}));">'+t+'</label>';};
  var head=document.createElement('div');head.innerHTML='<div class=smh><span>Slicer</span><button type=button id=slReset title="Kembali ke plan melalui pusat data">Reset</button></div>';m.appendChild(head);
  var top=document.createElement('div');m.appendChild(top);var mid=document.createElement('div');m.appendChild(mid);m.appendChild(b2);if(b3)m.appendChild(b3);var mx=document.createElement('div');m.appendChild(mx);
  var close=function(){m.style.display='none';};
  var N=function(v,d){return isFinite(v)?(+v).toFixed(d==null?1:d):'';};
  var geom=function(){try{return secGeom();}catch(e){return null;}};
  /* nilai Slicer dari kendali yang ada: mode S memakai slDip / slAz; mode P (garis) dip dari dipS, azimuth dari garis; H = plan */
  var cur=function(){var md=$('sMode').value,g=geom()||{},dip,az;
    if(md==='S'){dip=parseFloat($('slDip').value)||0;az=parseFloat($('slAz').value)||0;}
    else if(md==='P'||md==='A'){dip=parseFloat($('dipS').value)||90;az=((g.az||0)+90+360)%360;}
    else{dip=0;az=0;}
    var c=g.c||[0,0,0],cx=isFinite(parseFloat($('slX').value))?parseFloat($('slX').value):c[0]+offX,cy=isFinite(parseFloat($('slY').value))?parseFloat($('slY').value):c[1]+offY,cz=isFinite(parseFloat($('slZ').value))?parseFloat($('slZ').value):(md==='H'||(md==='S'&&dip<0.5)?+$('pos').value:c[2]);
    return{md:md,dip:dip,az:az,x:cx,y:cy,z:cz,w:parseFloat($('thick').value)||5,step:parseFloat($('slStep').value)||parseFloat($('thick').value)||5,pos:+$('pos').value};};
  /* pindah ke mode S dengan pusat yang masuk akal: pusat garis (mode P) / pusat data */
  var keS=function(){var md=$('sMode').value;if(md==='S')return;var g=geom();
    if(!isFinite(parseFloat($('slX').value))){var c=g&&g.c||[CX,CY,(G.z0+G.z1)/2];if(g&&g.m==='P'&&g.seg){c=[c[0]+g.u[0]*g.seg/2,c[1]+g.u[1]*g.seg/2,c[2]];}if(g&&g.m==='H'){c=[CX,CY,+$('pos').value];}
      $('slX').value=N(c[0]+offX,1);$('slY').value=N(c[1]+offY,1);$('slZ').value=N(c[2],1);}
    if(md==='P'||md==='A'){$('slDip').value=parseFloat($('dipS').value)||90;$('slAz').value=N(((g&&g.az||0)+90+360)%360,1);}
    $('sMode').value='S';modeChanged();};
  var setDipAz=function(dip,az){keS();var was=(parseFloat($('slDip').value)||0)<0.5;if(dip!=null)$('slDip').value=Math.min(90,Math.max(0,dip));if(az!=null)$('slAz').value=((az%360)+360)%360;
    var now=(parseFloat($('slDip').value)||0)<0.5;if(was!==now)updRange(true);else if(!now){/* bidang miring: tetap lewat pusat */}
    updatePlot();try{camFollowHook();}catch(e){}render();};
  var setPusat=function(x,y,z){if(x!=null)$('slX').value=N(x,1);if(y!=null)$('slY').value=N(y,1);if(z!=null)$('slZ').value=N(z,1);keS();var g=geom();if(g&&g.m==='H'&&isFinite(parseFloat($('slZ').value)))$('pos').value=parseFloat($('slZ').value);else $('pos').value=0;updatePlot();render();};
  var pusatPandangan=function(){try{var gd=$('plotDiv'),L=gd&&gd._fullLayout,sc=L&&L.scene,cam=sc&&sc.camera;if(cam&&cam.center&&sc._scene){var S=sc._scene,ds=S.dataScale,b=S.glplot?S.glplot.bounds:null;
        /* pusat kamera dalam koordinat ternormalisasi -> koordinat data */
        var c=cam.center,ctr=[(sc.xaxis.range[0]+sc.xaxis.range[1])/2,(sc.yaxis.range[0]+sc.yaxis.range[1])/2,(sc.zaxis.range[0]+sc.zaxis.range[1])/2],rng=[sc.xaxis.range[1]-sc.xaxis.range[0],sc.yaxis.range[1]-sc.yaxis.range[0],sc.zaxis.range[1]-sc.zaxis.range[0]],ar=sc.aspectratio;
        return[ctr[0]+c.x*rng[0]/(2*ar.x)+offX,ctr[1]+c.y*rng[1]/(2*ar.y)+offY,ctr[2]+c.z*rng[2]/(2*ar.z)];}}catch(e){}return null;};
  var render=function(){var v=cur(),isS=v.md==='S',isP=v.md==='P',plan=v.dip<0.5,g=geom()||{};
    top.innerHTML='<div class=slg><div class=slf><span>Dip (&deg;) &middot; 0 = plan, 90 = tegak</span><input type=range id=slQd min=0 max=90 step=0.5 value="'+v.dip+'"><input type=number id=slQdn step=any min=0 max=90 value="'+N(v.dip,1)+'"></div>'+
      '<div class=slf><span>Dip azimuth (&deg;)'+(isP?' &middot; dari garis':'')+'</span><input type=number id=slQa step=any value="'+N(v.az,1)+'" '+(isP?'disabled':'')+'><div class=slq><button type=button data-az=0>U</button><button type=button data-az=90>T</button><button type=button data-az=180>S</button><button type=button data-az=270>B</button></div></div></div>'+
      '<div class=slq><button type=button data-pre=plan class="'+(plan&&!isP?'on':'')+'">Plan (horizontal)</button><button type=button data-pre=ew class="'+(!plan&&isS&&Math.abs(((v.az%180)+180)%180-0)<0.3&&v.dip>=89.5?'on':'')+'">Tegak E&ndash;W</button><button type=button data-pre=ns class="'+(!plan&&isS&&Math.abs(((v.az%180)+180)%180-90)<0.3&&v.dip>=89.5?'on':'')+'">Tegak N&ndash;S</button><button type=button data-pre=line class="'+((isP||(window.S3&&S3.mode))?'on':'')+'" title="Tarik garis di mana saja pada jendela 3D; bidang sayatan dibuat lewat garis itu">Sayatan Garis Bebas</button></div>'+
      '<div class="slg c3"><div class=slf><span>Lebar slab (m)</span><input type=number id=slQw step=any min=0.1 value="'+v.w+'"></div><div class=slf><span>Langkah (m)</span><input type=number id=slQs step=any min=0.1 value="'+v.step+'"></div><div class=slf><span>Posisi &middot; '+(plan||g.m==='H'?'elevasi':'offset dari pusat')+'</span><input type=number id=slQp step=any value="'+N(v.pos,1)+'"></div></div>'+
      '<div class=slf><span>Pusat bidang (E, N, RL) <small>&middot; dipakai bila dip &gt; 0</small></span><div class="slg c3" style="margin:0"><input type=number id=slQx step=any placeholder=E value="'+N(v.x,1)+'"><input type=number id=slQy step=any placeholder=N value="'+N(v.y,1)+'"><input type=number id=slQz step=any placeholder=RL value="'+N(v.z,1)+'"></div></div>'+
      '<div class=slq><button type=button data-ps=data>Pusat data</button><button type=button data-ps=view>Pusat pandangan</button></div>'+
      '<div class=slpos><button type=button data-d=-1 title="Mundur satu langkah (PageDown)">&#9664; Mundur</button><div class=slf><input type=number id=slQp2 step=any value="'+N(v.pos,1)+'"></div><button type=button data-d=1 title="Maju satu langkah (PageUp)">Maju &#9654;</button></div>';
    mid.innerHTML='<hr>'+ck('sliceClip','Potong data (hanya di dalam slab)')+ck('showPlane','Tampilkan bidang potong')+ck('showProf','Profil topo / pit pada sayatan')+'<hr>';
    /* 'Pengaturan lanjutan (panel Sayatan)' dihapus: pengaturan sayatan terpusat di popup ini (pemilik 10-11-2026), panel Sayatan di Properti tidak lagi dibuka dari sini */
    mx.innerHTML='<button class=smi data-a=dig>&#9998; Digitasi string di penampang</button>';
    b2.classList.toggle('on',!!window.VIEW2D);if(b3)b3.classList.toggle('on',!window.VIEW2D);};
  var ubah=function(e){var t=e.target,id=t.id;if(!id)return;
    if(id==='slQd'||id==='slQdn'){var d=Math.min(90,Math.max(0,parseFloat(t.value)||0));if(id==='slQd'&&e.type==='input'){$('slQdn').value=N(d,1);keS();var was=(parseFloat($('slDip').value)||0)<0.5;$('slDip').value=d;if(was!==(d<0.5))updRange(true);dDraft();return;}setDipAz(d,null);}
    else if(id==='slQa')setDipAz(null,parseFloat(t.value)||0);
    else if(id==='slQw'){var w=parseFloat(t.value);if(w>0){$('thick').value=w;updatePlot();}}
    else if(id==='slQs'){var sv=parseFloat(t.value);if(sv>0)$('slStep').value=sv;}
    else if(id==='slQp'||id==='slQp2'){var p=$('pos'),pv=parseFloat(t.value);if(isFinite(pv)){p.value=Math.min(+p.max,Math.max(+p.min,pv));updatePlot();render();}}
    else if(id==='slQx'||id==='slQy'||id==='slQz'){setPusat(parseFloat($('slQx').value),parseFloat($('slQy').value),parseFloat($('slQz').value));}};
  top.addEventListener('change',ubah);top.addEventListener('input',function(e){if(e.target.id==='slQd')ubah(e);});
  top.addEventListener('click',function(e){var b=e.target.closest('button');if(!b)return;
    if(b.dataset.d){stepPos(+b.dataset.d);setTimeout(render,60);return;}
    if(b.dataset.az!=null){setDipAz(Math.max(parseFloat($('slQdn').value)||0,90),+b.dataset.az);return;}
    if(b.dataset.ps==='data'){setPusat(CX+offX,CY+offY,(G.z0+G.z1)/2);return;}
    if(b.dataset.ps==='view'){var c=pusatPandangan();if(c)setPusat(c[0],c[1],c[2]);else alert('Pusat pandangan hanya tersedia di tampilan 3D.');return;}
    var pre=b.dataset.pre;if(pre==='plan')setDipAz(0,null);else if(pre==='ew')setDipAz(90,0);else if(pre==='ns')setDipAz(90,90);else if(pre==='line'){/* pemilik 10-11-2026: tombol ini membuka popup 'Sayatan garis bebas' (tarik garis di jendela 3D), bukan lagi 'garis di peta' */close();if(typeof s3Open==='function'){if(!(window.S3&&S3.mode))s3Open();}else{$('sMode').value='P';modeChanged();if(typeof drawOpen==='function'&&!lineGet())setTimeout(drawOpen,50);}}});
  head.addEventListener('click',function(e){if(e.target.id==='slReset'){$('slDip').value=0;$('slAz').value=0;$('slX').value='';$('slY').value='';$('slZ').value='';$('slStep').value='';$('sMode').value='S';modeChanged();render();}});
  mx.addEventListener('click',function(e){var b=e.target.closest('button[data-a]');if(!b)return;close();if(b.dataset.a==='set'){uiTab('Slice');}else{uiTab('Dig');}});
  bt.addEventListener('click',function(e){e.stopPropagation();if(m.style.display==='block'){close();return;}render();var r=bt.getBoundingClientRect();m.style.display='block';m.style.top=(r.bottom+6+window.scrollY)+'px';m.style.left=(Math.max(8,Math.min(innerWidth-350,r.left))+window.scrollX)+'px';});
  /* ditangkap di fase capture pada popup, supaya penangan asli tombol (toggle2D / s3Open) tidak ikut jalan */
  m.addEventListener('click',function(e){var t=e.target,in2=b2.contains(t),in3=b3&&b3.contains(t);if(!in2&&!in3)return;e.stopPropagation();e.preventDefault();
    if(in2&&!window.VIEW2D)toggle2D();if(in3&&window.VIEW2D)toggle2D();setTimeout(close,0);},true);
  document.addEventListener('mousedown',function(e){if(m.style.display==='block'&&!m.contains(e.target)&&e.target!==bt&&!bt.contains(e.target))close();});
  document.addEventListener('keydown',function(e){if(e.key==='Escape')close();});
  var sync=function(){var s=$('secM2d');if(s)s.innerHTML=window.VIEW2D?' <span class=sm2d>2D</span>':'';bt.classList.toggle('on',!!window.VIEW2D);if(m.style.display==='block')render();};
  var _t=toggle2D;toggle2D=function(){var r=_t.apply(this,arguments);sync();return r;};
  var _sp=stepPos;stepPos=function(){var r=_sp.apply(this,arguments);if(m.style.display==='block')setTimeout(render,80);return r;};
  window.SLICER={render:render,open:function(){bt.click();},close:close,set:setDipAz,pusat:setPusat};sync();})();
