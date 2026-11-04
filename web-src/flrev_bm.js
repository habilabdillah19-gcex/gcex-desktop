/* ================= GC-Ex Block Model 0.20: ADDITIONAL FLAGGING + REVIEW FLITCH PER FLITCH =================
   ADDITIONAL FLAGGING (menggantikan "Aturan sulfida / material SxS")
   - Daftar aturan: bila KOMPOSIT (rata-rata tertimbang tonase di dalam poligon dig block) unsur tertentu melewati COG,
     SELURUH poligon diberi flag (mis. "Ore Sulfide": S > 0,8 %; "Zn tinggi": Zn > 500 ppm). Aturan kode kategori
     (>= 50 % tonase berkode tertentu) tetap didukung. Poligon ber-flag -> garis ganda + nama flag di label / laporan;
     aturan Tujuan (DEST) "Flag? Ya / Tidak" memakai flag ini. Pengaturan lama (kolom sxs & batas, kode sulfida) dipindah
     otomatis menjadi aturan "Ore Sulfide".
   REVIEW PER FLITCH di Project Tree (semua dihitung dari poligon tersimpan; flitch aktif tidak berubah saat menghitung):
   - Dig Block > Per flitch: poligon (material -> tujuan, ton @ kadar, flag); klik = buka flitch & sorot
   - Laporan Grade x Tonnage > Per flitch: ton @ kadar per tujuan; Rekap semua flitch (CSV)
   - As-Mined > Per flitch: rencana (dig block) vs aktual (as-mined) ton @ kadar & selisih; klik = buka flitch dengan
     poligon dig block (rencana) dan as-mined (aktual) bertumpuk di Sayatan 2D */
(function(){
  if(!window.BX||typeof window.dbU!=='function'||typeof window.lyTon!=='function')return;
  var esc=function(s){return String(s==null?'':s).replace(/[&<>"]/g,function(c){return{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c];});};
  var f3=function(v){return String(+(+v).toFixed(3));},N=function(v){return Math.round(v).toLocaleString('id-ID');};
  /* ---------- aturan ---------- */
  window.afRules=function(){var U=dbU();if(!Array.isArray(U.af)){U.af=[];
      if(U.sxsAttr)U.af.push({n:'Ore Sulfide',k:'num',a:U.sxsAttr,op:'>',c:+U.sxsThr||0.8,on:true});
      if(U.sfAttr)U.af.push({n:'Ore Sulfide (kode)',k:'cat',a:U.sfAttr,codes:U.sfCodes||'SF,SULFIDE,SULPHIDE,SUL',on:true});}
    return U.af;};
  function afPass(P,excl,R){var m=BX.m,B=lyBench(),b=lyBB(P),L=lyU(),sgA=BX.ui.sgCol&&m.num[BX.ui.sgCol]?m.num[BX.ui.sgCol]:null,out=R.map(function(){return{s:0,w:0};}),T=0;
    var A=R.map(function(r){if(r.k==='cat'){var C=m.cat[r.a];if(!C)return null;var cl=String(r.codes||'').toUpperCase().split(',').map(function(x){return x.trim();}),S={};C.dict.forEach(function(d,k){if(cl.indexOf(String(d).toUpperCase())>=0)S[k]=1;});return{c:C.codes,S:S};}return m.num[r.a]?{n:m.num[r.a]}:null;});
    var C=lyCandZ(B[1],B[0]);for(var t=0;t<C.length;t++){var i=C[t],z=m.z[i];if(!(z>B[1]+1e-9&&z<=B[0]+1e-9))continue;var x=m.x[i],y=m.y[i];if(x<b[0]-1e-6||x>b[1]+1e-6||y<b[2]-1e-6||y>b[3]+1e-6)continue;if(L.onlyPass&&!bxPass(i))continue;
      if(!lyInS(P,x,y))continue;var sk=false;for(var e=0;e<excl.length;e++){if(lyIn(excl[e].p,x,y)&&!lyOnEdge(excl[e].p,x,y)){sk=true;break;}}if(sk)continue;
      var tt=m.sx[i]*m.sy[i]*m.sz[i]*bxSGv(sgA?sgA[i]:NaN);T+=tt;
      for(var q=0;q<R.length;q++){var a=A[q];if(!a)continue;if(a.c){if(a.S[a.c[i]])out[q].s+=tt;out[q].w+=tt;}else if(isFinite(a.n[i])){out[q].s+=a.n[i]*tt;out[q].w+=tt;}}}
    return out;}
  function afEval(r,P,excl){var R=afRules().filter(function(q){return q.on!==false&&q.a&&(q.k==='cat'||isFinite(+q.c));});r.af=[];r.afv={};if(!R.length||!(r.t>0)||!BX.m)return;
    var need=[],idx=[];R.forEach(function(q,k){if(q.k!=='cat'&&r.el&&isFinite(r.el[q.a])){r.afv[q.n]=r.el[q.a];}else{need.push(q);idx.push(k);}});
    if(need.length){var o=afPass(P,excl||[],need);need.forEach(function(q,j){var v=o[j].w?o[j].s/o[j].w:NaN;r.afv[q.n]=q.k==='cat'?v*100:v;});}
    R.forEach(function(q){var v=r.afv[q.n];if(!isFinite(v))return;var hit=q.k==='cat'?v>=50:(q.op==='>='?v>=+q.c:v>+q.c);if(hit)r.af.push(q.n);});}
  var _lt=lyTon;lyTon=function(P,zs0,excl){var r=_lt.apply(this,arguments);try{afEval(r,P,excl);var U=dbU();r.sulf=!!(U.sfOn!==false&&r.af&&r.af.length);}catch(e){console.error(e);}return r;};
  window.afTxt=function(t){return t&&t.af&&t.af.length?'  ('+t.af.join(', ')+')':'';};
  window.afSet=function(k,f,v){var R=afRules();if(!R[k])return;R[k][f]=v;afDirty();};
  window.afAdd=function(){var m=BX.m,nums=m?Object.keys(m.num):[];afRules().push({n:'Flag '+(afRules().length+1),k:'num',a:nums.filter(function(a){return /^(zn|cu|s|sxs|stot|as|pb)/i.test(a);})[0]||nums[0]||'',op:'>',c:0,on:true});afDirty();};
  window.afDel=function(k){afRules().splice(k,1);afDirty();};
  function afDirty(){try{if(window.LY)LY.cache=null;}catch(e){}try{if(window.dgSave)dgSave();}catch(e){}FLC={};try{dbPanel();}catch(e){}try{if(window.SA&&SA.dirty)SA.dirty();}catch(e){}}
  function afHtml(){var U=dbU(),m=BX.m,nums=Object.keys(m.num),cats=Object.keys(m.cat),R=afRules();
    var opt=function(L,v){return L.map(function(a){return '<option'+(a===v?' selected':'')+'>'+esc(a)+'</option>';}).join('');};
    return '<summary>Additional flagging (garis ganda)</summary>'+
      '<label class=sw style="margin-top:6px"><input type=checkbox '+(U.sfOn!==false?'checked':'')+' onchange="dbSet(\'sfOn\',this.checked);afDirty2()">Poligon ber-flag dibuat garis ganda</label>'+
      '<div class=hint>Flag diberikan ke <b>seluruh poligon</b> bila <b>komposit</b> unsur di dalam poligon (rata-rata tertimbang tonase) melewati COG. Contoh: Ore Sulfide = S &gt; 0,8 %; Zn tinggi = Zn &gt; 500 ppm. Satuan mengikuti kolom block model.</div>'+
      '<table class="pltb aftb"><tr><th></th><th>Nama flag</th><th>Unsur</th><th></th><th>COG</th><th></th></tr>'+
      R.map(function(q,k){return '<tr><td><input type=checkbox '+(q.on!==false?'checked':'')+' onchange="afSet('+k+',\'on\',this.checked)" title="Aktif"></td>'+
        '<td><input type=text value="'+esc(q.n)+'" onchange="afSet('+k+',\'n\',this.value.trim()||\'Flag\')"></td>'+
        (q.k==='cat'?'<td><select onchange="afSet('+k+',\'a\',this.value)">'+opt(cats,q.a)+'</select></td><td>kode</td><td><input type=text value="'+esc(q.codes)+'" title="Kode dipisah koma; flag bila &ge; 50 % tonase berkode ini" onchange="afSet('+k+',\'codes\',this.value)"></td>'
          :'<td><select onchange="afSet('+k+',\'a\',this.value)">'+opt(nums,q.a)+'</select></td><td><select onchange="afSet('+k+',\'op\',this.value)"><option'+(q.op!=='>='?' selected':'')+'>&gt;</option><option value="&gt;="'+(q.op==='>='?' selected':'')+'>&ge;</option></select></td><td><input type=number step=any value="'+esc(q.c)+'" onchange="afSet('+k+',\'c\',+this.value)"></td>')+
        '<td><button class=x onclick="afDel('+k+')" title="Hapus aturan">&times;</button></td></tr>';}).join('')+'</table>'+
      '<div class=g2 style="margin-top:4px"><button onclick="afAdd()">+ Aturan flag</button><button onclick="var r=dbInner();DB.msg=r.n+\' garis ganda dibuat\'+(r.f?\', \'+r.f+\' poligon terlalu sempit\':\'\');dbPanel()">Perbarui garis ganda</button></div>';}
  window.afDirty2=function(){afDirty();};
  var _dp=window.dbPanel;if(_dp){dbPanel=function(){var r=_dp.apply(this,arguments);try{var b=$('dbBody');if(b&&BX.m){Array.prototype.forEach.call(b.querySelectorAll('details.mini'),function(d){var s=d.querySelector('summary');if(s&&/sulfida/i.test(s.textContent)){var o=d.open;d.innerHTML=afHtml();d.open=o;}});}}catch(e){console.error(e);}return r;};}
  var st=document.createElement('style');st.textContent='.aftb input,.aftb select{width:100%;min-width:0;height:24px!important;padding:1px 4px!important;font-size:12px!important}.aftb td{padding:2px 3px}.aftb td:nth-child(2){width:32%}.aftb td:nth-child(5){width:18%}';document.head.appendChild(st);
  /* ---------- hitung per flitch (tanpa mengubah flitch aktif) ---------- */
  var FLC={};
  window.flGroups=function(){var G={},ord=[],grp=function(top,bot){var k=f3(top)+'|'+f3(bot);if(!G[k]){G[k]={k:k,top:+top,bot:+bot,db:[],am:[]};ord.push(k);}return G[k];};
    (window.DG?DG.S:[]).forEach(function(q,i){if(q.inner||q.amTmp)return;var top,bot;if(q.db){top=q.db.top;bot=q.db.bot;}else{var p=q.pl;if(!p||p.m!=='H'||!isFinite(+p.pos)||!q.closed)return;var th=+p.thick||0;top=+p.pos+th/2;bot=+p.pos-th/2;}grp(top,bot).db.push(q);});
    try{amBndAll().forEach(function(x){if(isFinite(+x.top)&&isFinite(+x.bot))grp(x.top,x.bot).am.push(x);});}catch(e){}
    ord.sort(function(a,b){return G[b].top-G[a].top;});return ord.map(function(k){return G[k];});};
  window.flCalc=function(g){if(!BX.m||!g.db.length)return null;var sig=[BX.ver,lyU().flMode,lyU().gAttr,BX.ui.sgCol,JSON.stringify(afRules()),JSON.stringify(lyU().destR||[]),g.db.map(function(q){return (q.id||'')+':'+q.pts.length+':'+(q.pts[0]||[]).join(',')+':'+q.d+':'+(q.dest||'');}).join(';')].join('|');
    if(FLC[g.k]&&FLC[g.k].sig===sig)return FLC[g.k].r;var L=lyU(),sv={top:L.top,bot:L.bot,fh:L.fh},it=[];
    try{L.top=+g.top;L.fh=+(g.top-g.bot).toFixed(3);L.bot='';it=lyItems(true);}catch(e){console.error(e);}finally{L.top=sv.top;L.bot=sv.bot;L.fh=sv.fh;}
    /* el / elw ikut disimpan supaya rekap CSV bisa memuat SEMUA unsur terpilih (bukan satu kadar
       saja), dan centroid poligon dihitung sekali di sini untuk dipakai dispatch / fleet system. */
    var ctr=function(R){if(!R||R.length<3)return null;var A=0,cx=0,cy=0;
      for(var i=0,n=R.length;i<n;i++){var a=R[i],b=R[(i+1)%n],f=a[0]*b[1]-b[0]*a[1];A+=f;cx+=(a[0]+b[0])*f;cy+=(a[1]+b[1])*f;}
      if(Math.abs(A)<1e-9){var sx=0,sy=0;R.forEach(function(q){sx+=q[0];sy+=q[1];});return[sx/R.length,sy/R.length];}
      return[cx/(3*A),cy/(3*A)];};
    var r={it:it.map(function(o){var t=o.ton||{},c=ctr(o.r);return{s:o.s,name:o.name,d:o.s.d||'',dest:o.dest||'',area:o.area,t:t.t||0,g:t.grade,af:t.af||[],
      el:t.el||{},elw:t.elw||{},cx:c?c[0]:NaN,cy:c?c[1]:NaN,ton:t};}),t:0,m:0,by:{}};
    r.it.forEach(function(o){r.t+=o.t;if(isFinite(o.g))r.m+=o.g*o.t;var k=(o.d||'-')+' → '+(o.dest||'-');var b=r.by[k]||(r.by[k]={t:0,m:0,n:0});b.t+=o.t;b.n++;if(isFinite(o.g))b.m+=o.g*o.t;});
    FLC[g.k]={sig:sig,r:r};return r;};
  var tg=function(t,m){return t?N(t)+' t @ '+(m/t).toFixed(2):'0 t';};
  window.flOpen=function(g,then){lySet('fh',+(g.top-g.bot).toFixed(3));lyU().bot='';lySet('top',+(+g.top).toFixed(3));lyApply();if(then)setTimeout(then,150);};
  window.flCsvAll=function(){var a=lyGradeAttr();
    /* SEMUA unsur yang dicentang di "Elemen laporan" ikut, bukan hanya kadar utama; plus metal tiap
       unsur yang satuannya memungkinkan, dan centroid poligon untuk dispatch / fleet system. */
    var EL=(typeof elList==='function'?elList():[a]).filter(Boolean);
    var MET=EL.filter(function(x){return typeof elMetU==='function'?elMetU(x):false;});
    var hd=['RL_atas','RL_bawah','Nama','Material','Tujuan','Luas_m2','Ton']
      .concat(EL.map(function(x){var u=(typeof elUnit==='function'&&elUnit(x))||'';return x+(u?'_'+String(u).replace('/','p').replace('%','pct'):'');}))
      .concat(MET.map(function(x){return 'Metal_'+x;}))
      .concat(['Centroid_X','Centroid_Y','Flag']);
    var r=[hd.join(',')];
    flGroups().forEach(function(g){var c=flCalc(g);if(!c)return;c.it.forEach(function(o){
      var gv=function(x){var v=(o.el&&isFinite(o.el[x]))?o.el[x]:(x===a?o.g:NaN);return v;};
      r.push([g.top,g.bot,'"'+o.name+'"',o.d,o.dest,o.area.toFixed(2),o.t.toFixed(2)]
        .concat(EL.map(function(x){var v=gv(x);return isFinite(v)?v.toFixed(4):'';}))
        .concat(MET.map(function(x){var v=gv(x),w=(o.elw&&isFinite(o.elw[x]))?o.elw[x]:o.t;
          var mm=(typeof elMet==='function')?elMet(x,v,w):(isFinite(v)?v*w:NaN);return isFinite(mm)?mm.toFixed(3):'';}))
        .concat([isFinite(o.cx)?o.cx.toFixed(2):'',isFinite(o.cy)?o.cy.toFixed(2):'','"'+o.af.join('; ')+'"']).join(','));});});
    var b=new Blob(['﻿'+r.join('\r\n')],{type:'text/csv'}),l=document.createElement('a');l.href=URL.createObjectURL(b);l.download='GCEx_RekapDigBlock_SemuaFlitch.csv';document.body.appendChild(l);l.click();setTimeout(function(){URL.revokeObjectURL(l.href);l.remove();},800);};
  /* ---------- node Project Tree ---------- */
  if(window.PT&&PT.def&&PT.def.nodes){var _nodes=PT.def.nodes;
    PT.def.nodes=function(){var L=_nodes.apply(this,arguments);try{
      var G=flGroups(),B=lyBench(),act=function(g){return Math.abs(g.top-B[0])<1e-6&&Math.abs(g.bot-B[1])<1e-6;},lab=function(g){return 'RL '+f3(g.top)+' – '+f3(g.bot)+(act(g)?' (aktif)':'');};
      var find=function(id){for(var i=0;i<L.length;i++)if(L[i]&&L[i].id===id)return L[i];return null;};
      var GD=G.filter(function(g){return g.db.length;}),GA=G.filter(function(g){return g.am.length||g.db.length;});
      var dig=find('dig');if(dig&&GD.length)dig.kids=(dig.kids||[]).concat([{id:'dig.fl',t:'Per flitch ('+GD.length+')',ic:'flitch',fold:1,hint:'Semua dig block yang sudah dibuat, per flitch',kids:GD.map(function(g){var c=flCalc(g);
          return{id:'dig.fl.'+g.k,t:lab(g),ic:'flitch',b:g.db.length+' DB'+(c?' · '+tg(c.t,c.m):''),fold:1,go:function(){flOpen(g,function(){PT.goSub('BM','Dig block');});},
            kids:(c?c.it:[]).map(function(o){var q=o.s;return{id:'dig.fl.'+g.k+'.'+(q.id||q.no),t:o.name+' · '+(o.d||'-')+' → '+(o.dest||'-'),ic:q.manual?'digit':'poly',b:tg(o.t,isFinite(o.g)?o.g*o.t:0)+(o.af.length?' · ⚑ '+o.af.join(', '):''),
              hint:o.af.length?'Additional flagging: '+o.af.join(', '):'',go:function(){flOpen(g,function(){if(window.DGM)DGM.last=q.id;DB.sel=q.id;PT.goSub('BM','Dig block');try{dbPanel();}catch(e){}updatePlot();});},
              menu:function(){return[{t:'Edit bentuk…',fn:function(){flOpen(g,function(){dbEdStart(DG.S.indexOf(q));});}},{t:'Hapus dig block…',danger:1,fn:function(){if(confirm('Hapus dig block '+o.name+'?')){var i=DG.S.indexOf(q);if(i>=0)dgDel(i);}}}];}};})};})}]);
      var rep=find('rep');if(rep&&GD.length)rep.kids=(rep.kids||[]).concat([{id:'rep.fl',t:'Per flitch ('+GD.length+')',ic:'flitch',fold:1,kids:GD.map(function(g){var c=flCalc(g);
          return{id:'rep.fl.'+g.k,t:lab(g),ic:'flitch',b:c?tg(c.t,c.m):'',fold:1,go:function(){flOpen(g,function(){PT.goSub('BM','Dig block');});},
            kids:c?Object.keys(c.by).sort().map(function(k){var b=c.by[k];return{id:'rep.fl.'+g.k+'.'+k,t:k,ic:'table',b:b.n+' DB · '+tg(b.t,b.m),go:function(){flOpen(g,function(){PT.goSub('BM','Dig block');});}};}):[]};})},
        {id:'rep.all',t:'Rekap semua flitch (CSV)',ic:'export',go:flCsvAll,hint:'Satu baris per dig block di semua flitch: RL, material, tujuan, luas, ton, kadar, metal, flag'}]);
      var am=find('am');if(am&&GA.length)am.kids=(am.kids||[]).concat([{id:'am.fl',t:'Per flitch ('+GA.length+')',ic:'flitch',fold:1,hint:'Rencana (dig block) vs aktual (as-mined) per flitch',kids:GA.map(function(g){var c=flCalc(g),at=0,am2=0,nc=0;
          g.am.forEach(function(x){var I=null;try{I=amInfoById(x.id);}catch(e){}if(I&&I.calc&&x.on!==false){nc++;at+=I.ton;if(isFinite(I.gA))am2+=I.gA*I.ton;}});
          var pt=c?c.t:0,d=pt&&nc?' · Δ '+((at-pt)/pt*100).toFixed(1)+' %':'';
          return{id:'am.fl.'+g.k,t:lab(g),ic:'flitch',b:nc&&pt?'Δ '+((at-pt)/pt*100).toFixed(1)+' %':(g.am.length?g.am.length+' pol':'rencana'),
            hint:'Klik: buka flitch dengan dig block (rencana) dan poligon as-mined (aktual) bertumpuk di Sayatan 2D',
            go:function(){flOpen(g,function(){try{AM.show=true;}catch(e){}try{uiTab('AM');PT.goSub('AM','Poligon');}catch(e){}try{if(window.amApply&&g.am.length)amApply();}catch(e){}updatePlot();});},
            kids:[{id:'am.fl.'+g.k+'.r',t:'Rencana (dig block)',ic:'poly',b:c?g.db.length+' DB · '+tg(c.t,c.m):'-',go:function(){flOpen(g,function(){PT.goSub('BM','Dig block');});}},
              {id:'am.fl.'+g.k+'.a',t:'Aktual (as-mined)',ic:'asmined',b:nc?nc+' pol · '+tg(at,am2)+d:(g.am.length?g.am.length+' pol (belum dihitung)':'belum ada poligon'),go:function(){flOpen(g,function(){try{AM.show=true;uiTab('AM');PT.goSub('AM','Register');if(window.amApply&&g.am.length)amApply();}catch(e){}updatePlot();});}}].concat(g.am.map(function(x){var I=null;try{I=amInfoById(x.id);}catch(e){}return{id:'am.fl.'+g.k+'.'+x.id,t:(I&&I.code)||x.name||x.id,ic:'poly',b:I&&I.calc?tg(I.ton,isFinite(I.gA)?I.gA*I.ton:0):'belum dihitung',
              go:function(){flOpen(g,function(){uiTab('AM');PT.goSub('AM','Register');amBndAll().forEach(function(q){q.open=q.id===x.id;});amPanel();});}};}))};})}]);
    }catch(e){console.error(e);}return L;};
    try{PT.render(true);}catch(e){}}
})();
