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

/* ---------- bilah atas: satu menu "Sayatan" ---------- */
(function(){var b2=$('btn2d');if(!b2||$('btnSecM'))return;var b3=$('btnSec3');
  var st=document.createElement('style');st.textContent='#secMenu{position:fixed;z-index:2000;display:none;width:300px;background:var(--sf,#fff);color:var(--tx,#212529);border:1px solid var(--bd,#ced4da);border-radius:10px;box-shadow:0 10px 28px rgba(0,0,0,.2);padding:6px}'+
    '#secMenu .smh{font-size:10.5px;font-weight:700;letter-spacing:.04em;color:var(--mu,#868e96);margin:6px 8px 3px;text-transform:uppercase}#secMenu button.tb,#secMenu .smi{display:flex;align-items:center;gap:8px;width:100%;justify-content:flex-start;height:34px;margin:2px 0;padding:0 10px;border-radius:7px;font-size:12.5px;text-align:left}'+
    '#secMenu .smi{border:0;background:none;color:inherit;cursor:pointer}#secMenu .smi:hover{background:rgba(0,0,0,.06)}#secMenu button.tb svg{width:16px;height:16px}#secMenu label{display:flex;gap:8px;align-items:center;padding:4px 10px;font-size:12.5px;cursor:pointer;border-radius:6px}#secMenu label:hover{background:rgba(0,0,0,.05)}#secMenu hr{border:0;border-top:1px solid var(--bd,#dee2e6);margin:5px 4px}'+
    '#btnSecM .sm2d{font-size:10px;font-weight:700;background:var(--pr,#1c3d8f);color:#fff;border-radius:4px;padding:0 4px;margin-left:2px}';document.head.appendChild(st);
  var bt=document.createElement('button');bt.className='tb';bt.id='btnSecM';bt.title='Sayatan & Penampang: Penampang (sayatan) 2D, Sayatan 3D, opsi slab, digitasi string, pengaturan';
  bt.innerHTML='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 20L20 4"/><rect x="3" y="5" width="18" height="14" rx="1" stroke-width="1.6"/></svg>Sayatan<span id=secM2d></span> &#9662;';
  b2.parentNode.insertBefore(bt,b2);var m=document.createElement('div');m.id='secMenu';document.body.appendChild(m);
  var t2=[].slice.call(b2.childNodes).filter(function(n){return n.nodeType===3&&/Penampang/.test(n.textContent);})[0];if(t2)t2.textContent='Penampang (Sayatan) 2D';
  var ck=function(id,t){var e=$(id);if(!e)return '';return '<label><input type=checkbox '+(e.checked?'checked':'')+' onchange="var e=document.getElementById(\''+id+'\');e.checked=this.checked;e.dispatchEvent(new Event(\'change\',{bubbles:true}));">'+t+'</label>';};
  var head=document.createElement('div');head.innerHTML='<div class=smh>Sayatan &amp; Penampang</div>';m.appendChild(head);m.appendChild(b2);if(b3)m.appendChild(b3);var mx=document.createElement('div');m.appendChild(mx);
  var close=function(){m.style.display='none';};
  var render=function(){mx.innerHTML='<hr><div class=smh>Opsi slab</div>'+ck('sliceClip','Potong data di dalam slab (3D)')+ck('showPlane','Tampilkan bidang potong')+ck('showProf','Profil topo / pit pada sayatan')+
      '<hr><button class=smi data-a=dig>&#9998; Digitasi string di penampang</button><button class=smi data-a=set>&#9881; Pengaturan Sayatan &amp; Penampang&hellip;</button>';};
  mx.addEventListener('click',function(e){var b=e.target.closest('button[data-a]');if(!b)return;close();if(b.dataset.a==='set'){uiTab('Slice');}else{uiTab('Dig');}});
  bt.addEventListener('click',function(e){e.stopPropagation();if(m.style.display==='block'){close();return;}render();var r=bt.getBoundingClientRect();m.style.display='block';m.style.top=(r.bottom+6)+'px';m.style.left=Math.max(8,Math.min(innerWidth-310,r.left))+'px';});
  [b2,b3].forEach(function(b){if(b)b.addEventListener('click',function(){setTimeout(close,0);});});
  document.addEventListener('mousedown',function(e){if(m.style.display==='block'&&!m.contains(e.target)&&e.target!==bt&&!bt.contains(e.target))close();});
  document.addEventListener('keydown',function(e){if(e.key==='Escape')close();});
  var sync=function(){var s=$('secM2d');if(s)s.innerHTML=window.VIEW2D?' <span class=sm2d>2D</span>':'';bt.classList.toggle('on',!!window.VIEW2D);};
  var _t=toggle2D;toggle2D=function(){var r=_t.apply(this,arguments);sync();return r;};sync();})();
