/* ================= GC-Ex Block Model 0.14: sampel as-mined (channel & bor) — Ganti / Upsert / Append =================
   Tiap set (Channel sampling, Bor grade control) punya mode import:
   - Ganti  : file baru menggantikan seluruh data jenis itu (perilaku lama).
   - Upsert : collar per HoleID, survey per HoleID+Depth, assay per interval: interval sama diperbarui, interval lama yang
              tumpang tindih dengan interval baru diganti, interval & lubang lain tetap. Cocok untuk koreksi / re-assay / bor baru.
   - Append : baris baru ditambahkan; baris kembar (collar: HoleID, assay: HoleID+From+To, survey: HoleID+Depth) dilewati.
   Kolom dicocokkan menurut nama (tidak peka huruf besar/kecil); kolom baru ditambahkan. Riwayat import dicatat per set. */
var AMUP={};
function amUpMode(set){var S=amD().sets[set];return(S&&S.mode)||(S&&(S.col||S.asy)?'upsert':'ganti');}
function amUpSet(set,v){var D=amD(),S=D.sets[set]||(D.sets[set]={fn:{}});S.mode=v;amPanel();amDirty();}
function amUpKey(kind,h){var id=amCol(h,/^(hole|bhid|hole_?id|holeid|id|channel|ch_?id)$/i);if(id<0)id=0;
  if(kind==='asy')return{id:id,k:[id,amCol(h,/^(from|dari|depth_?from|mfrom)$/i),amCol(h,/^(to|sampai|ke|depth_?to|mto)$/i)]};
  if(kind==='sur')return{id:id,k:[id,amCol(h,/^(depth|at|kedalaman|dist)$/i)]};return{id:id,k:[id]};}
function amUpMerge(O,T,kind,mode){var H=O.h.slice(),low=H.map(function(x){return String(x).trim().toLowerCase();}),map=[];
  T.h.forEach(function(c){var i=low.indexOf(String(c).trim().toLowerCase());if(i<0){H.push(c);low.push(String(c).trim().toLowerCase());i=H.length-1;}map.push(i);});
  var pad=function(r){var o=r.slice();while(o.length<H.length)o.push('');return o;},NR=T.r.map(function(r){var o=new Array(H.length).fill('');r.forEach(function(v,j){o[map[j]]=v;});return o;});
  var K=amUpKey(kind,H),kk=function(r){return K.k.map(function(i){return i<0?'':String(r[i]).trim().toUpperCase().replace(/\.0+$/,'');}).join('|');},hid=function(r){return String(r[K.id]||'').trim().toUpperCase();};
  var old=O.r.map(pad),st={add:0,upd:0,skip:0,del:0};
  if(mode==='upsert'){
    if(kind==='asy'&&K.k[1]>=0&&K.k[2]>=0){/* assay: interval sama diperbarui, interval lama yang tumpang tindih dengan interval baru diganti, sisanya tetap */
      var nf=K.k[1],nt=K.k[2],by={};NR.forEach(function(r){var f=amNum(r[nf]),t=amNum(r[nt]);(by[hid(r)]=by[hid(r)]||[]).push([f,t]);});var ok={};old.forEach(function(r){ok[kk(r)]=1;});
      var keep=old.filter(function(r){var L=by[hid(r)];if(!L)return true;var f=amNum(r[nf]),t=amNum(r[nt]);for(var i=0;i<L.length;i++)if(f<L[i][1]-1e-6&&t>L[i][0]+1e-6){st.del++;return false;}return true;});
      NR.forEach(function(r){if(ok[kk(r)])st.upd++;else st.add++;});st.del=Math.max(0,st.del-st.upd);
      var out=keep.concat(NR),ii=K.id;out.sort(function(x,y){var a=String(x[ii]),b=String(y[ii]);return a<b?-1:a>b?1:amNum(x[nf])-amNum(y[nf]);});return{h:H,r:out,st:st};}
    /* collar / survey: baris dengan kunci sama (HoleID / HoleID+Depth) diganti, baru ditambahkan */
    var idx={};old.forEach(function(r,i){idx[kk(r)]=i;});var out2=old.slice();NR.forEach(function(r){var k=kk(r);if(k in idx){out2[idx[k]]=r;st.upd++;}else{idx[k]=out2.length;out2.push(r);st.add++;}});return{h:H,r:out2,st:st};}
  var seen={};old.forEach(function(r){seen[kk(r)]=1;});var add=[];NR.forEach(function(r){var k=kk(r);if(seen[k]){st.skip++;return;}seen[k]=1;add.push(r);st.add++;});return{h:H,r:old.concat(add),st:st};}
amFile=function(set,kind,f){if(!f)return;f.text().then(function(t){var D=amD(),S=D.sets[set]||(D.sets[set]={fn:{}}),T=amParse(t),mode=amUpMode(set),st=null;
    if(!T.h.length){AM.msg='<span class=warn>'+amE(f.name)+': file kosong</span>';amPanel();return;}
    if(mode!=='ganti'&&S[kind]&&S[kind].h&&S[kind].h.length){var M=amUpMerge(S[kind],T,kind,mode);S[kind]={h:M.h,r:M.r};st=M.st;}else{S[kind]=T;st={add:T.r.length,upd:0,skip:0,del:0};mode='ganti';}
    S.fn=S.fn||{};S.fn[kind]=(mode==='ganti'||!S.fn[kind])?f.name:(String(S.fn[kind]).split(' + ').slice(-2).join(' + ')+' + '+f.name);
    var lb={col:'Collar',asy:'Assay',sur:'Survey'}[kind],d=new Date(),p=function(n){return('0'+n).slice(-2);};
    (S.log=S.log||[]).push({t:d.getFullYear()+'-'+p(d.getMonth()+1)+'-'+p(d.getDate())+' '+p(d.getHours())+':'+p(d.getMinutes()),k:lb,f:f.name,m:mode,a:st.add,u:st.upd,s:st.skip,n:S[kind].r.length});if(S.log.length>40)S.log=S.log.slice(-40);
    AMUP[set]=lb+' '+({ganti:'diganti',upsert:'upsert',append:'append'}[mode])+': <b>'+st.add+'</b> baru'+(st.upd?', <b>'+st.upd+'</b> diperbarui':'')+(st.skip?', '+st.skip+' kembar dilewati':'')+' &middot; total '+S[kind].r.length+' baris';
    amBuild();amPanel();updatePlot();amDirty();}).catch(function(e){AM.msg='<span class=warn>'+amE(e.message)+'</span>';amPanel();});};
(function(){var _p=amPanel;amPanel=function(){var r=_p.apply(this,arguments);try{var el=$('amBody');if(!el)return r;
    el.querySelectorAll('.amset').forEach(function(box){var c=box.querySelector('input[type=file][onchange*="amFile("]');if(!c)return;var m=/amFile\('(\w+)'/.exec(c.getAttribute('onchange')||'');if(!m)return;var set=m[1],S=amD().sets[set]||{},mode=amUpMode(set);
      var w=document.createElement('div');w.className='amupm';
      w.innerHTML='<span>Import:</span>'+[['ganti','Ganti','File baru menggantikan seluruh data jenis itu'],['upsert','Upsert','Perbarui yang sama (collar per HoleID, assay per interval From-To; interval lama yang tumpang tindih diganti), tambahkan yang baru; data lain tetap'],['append','Append','Tambah baris baru; baris kembar dilewati']].map(function(q){
        return '<button class="'+(mode===q[0]?'on':'')+'" title="'+q[2]+'" onclick="amUpSet(\''+set+'\',\''+q[0]+'\')">'+q[1]+'</button>';}).join('')+
        ((S.col||S.asy)?'<small>'+[S.col?'collar '+S.col.r.length:'',S.asy?'assay '+S.asy.r.length:'',S.sur?'survey '+S.sur.r.length:''].filter(Boolean).join(' &middot; ')+'</small>':'');
      var g=box.querySelector('.amf');box.insertBefore(w,g||null);
      if(AMUP[set]){var n=document.createElement('div');n.className='hint amupmsg';n.innerHTML='&#10003; '+AMUP[set];box.appendChild(n);}
      if(S.log&&S.log.length){var dd=document.createElement('details');dd.className='amuplog';dd.innerHTML='<summary>Riwayat import ('+S.log.length+')</summary><table class=pltb><tr><th>Waktu</th><th>Data</th><th>Mode</th><th>File</th><th>+</th><th>~</th><th>=</th></tr>'+
        S.log.slice().reverse().map(function(q){return '<tr><td>'+amE(q.t)+'</td><td>'+amE(q.k)+'</td><td>'+amE(q.m)+'</td><td title="'+amE(q.f)+'">'+amE(String(q.f).slice(0,18))+'</td><td>'+q.a+'</td><td>'+q.u+'</td><td>'+q.s+'</td></tr>';}).join('')+'</table>';box.appendChild(dd);}});
  }catch(e){console.error(e);}return r;};})();
(function(){var st=document.createElement('style');st.textContent='#amBody .amupm{display:flex;flex-wrap:wrap;gap:3px;align-items:center;margin:3px 0 4px;font-size:11px}#amBody .amupm>span{color:var(--mu);margin-right:2px}'+
  '#amBody .amupm button{font-size:11px;padding:1px 7px;min-height:21px}#amBody .amupm button.on{background:var(--pr)!important;color:#f8f6f1!important;border-color:var(--pr)!important}#amBody .amupm small{margin-left:auto;color:var(--mu)}'+
  '#amBody .amuplog{margin-top:3px;font-size:11px}#amBody .amuplog summary{cursor:pointer;color:var(--pr)}#amBody .amuplog table{font-size:10.5px}#amBody .amupmsg{color:var(--pr)}';document.head.appendChild(st);})();
