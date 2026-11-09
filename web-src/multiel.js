/* ================= MULTI-ELEMEN: elemen laporan yang bisa dicentang (Au, Ag, Cu, Pb, Zn, SxS, ...) =================
   Satu daftar centang dipakai semua laporan grade x tonase: ringkasan kelas block model, dig block (panel, running grade,
   popup, label & ringkasan layout PDF, CSV) dan as-mined (panel, register CSV/Excel, report & layout PDF).
   Kadar tiap elemen = rata-rata tertimbang TON dari blok / sub-blok yang sama dengan tonase-nya.
   Elemen utama (atribut kadar aktif) selalu tampil dan tetap dipakai untuk kelas material. */
var ELX=/^(x|y|z|xc|yc|zc|xcentre|ycentre|zcentre|xcenter|ycenter|zcenter|xinc|yinc|zinc|dx|dy|dz|xmorig|ymorig|zmorig|ijk|id|idx|index|blockid|block_id|ix|iy|iz|i|j|k|vol|volume|ton|tonnes|tonnage|mass|pass|domain|zone|class|rescat|rcat|cat|code|flag|seq|nsamp|ns|nsam|dist|kv|kvar|krig.*|slope|var|ss|pass_?\d*|ndh|nhole|nholes|sg.*|dens.*|density|bd|moist.*|h2o|mc)$/i;
var ELPREF=[/^ag/i,/^cu/i,/^pb/i,/^zn/i,/^(sxs|s_?xs|scis|sulf)/i,/^(s_?tot|stot|ts)$/i,/^as(?!h)/i,/^hg/i,/^(c_?org|corg|tc|toc)$/i];
function elModel(){return BX&&BX.m?BX.m:null;}
function elCands(){var m=elModel();if(!m)return[];var sg=BX.ui&&BX.ui.sgCol;return Object.keys(m.num).filter(function(a){return a!==sg&&!ELX.test(String(a).trim());});}
function elPrim(){try{return lyGradeAttr();}catch(e){return BX.ui&&BX.ui.attr||'';}}
function elDef(){var c=elCands(),p=elPrim(),out=[];ELPREF.forEach(function(re){var a=c.filter(function(x){return re.test(x)&&x!==p;})[0];if(a&&out.indexOf(a)<0)out.push(a);});return out;}
/* daftar terpilih (tanpa elemen utama); disimpan di BX.ui supaya ikut tersimpan di proyek */
function elSel(){var U=BX.ui;if(!U)return[];var m=elModel(),c=elCands();if(!Array.isArray(U.rptEl)||(m&&U.rptElM!==m.name)){if(!Array.isArray(U.rptEl)||!U.rptEl.some(function(a){return c.indexOf(a)>=0;})){U.rptEl=elDef();}if(m)U.rptElM=m.name;}
  return U.rptEl.filter(function(a){return c.indexOf(a)>=0;});}
/* elemen yang dilaporkan: elemen utama dulu, lalu yang dicentang (urutan kolom model) */
function elList(prim){var p=prim||elPrim(),s=elSel(),c=elCands(),out=p?[p]:[];c.forEach(function(a){if(a!==p&&s.indexOf(a)>=0)out.push(a);});return out;}
function elExtra(prim){return elList(prim).slice(1);}
function elUnit(a){var U=BX.ui||{},o=U.rptU&&U.rptU[a];if(o)return o;var s=String(a).toLowerCase();
  if(/(pct|perc|%|_p$|pc$)/.test(s))return '%';if(/ppm/.test(s))return 'ppm';if(/ppb/.test(s))return 'ppb';if(/(gpt|g_?t$|gt$|gpt$)/.test(s))return 'g/t';
  if(/^(au|ag|pt|pd)/.test(s))return 'g/t';if(/^(cu|pb|zn|fe|mn|ni|s|sxs|scis|stot|c|al|si|mg|ca)/.test(s))return '%';return '';}
function elDp(a,v){var u=elUnit(a);if(u==='ppm'||u==='ppb')return Math.abs(v)>=100?0:1;if(u==='%')return Math.abs(v)<1?3:2;return Math.abs(v)<10?2:1;}
function elF(a,v){return isFinite(v)?v.toFixed(elDp(a,v)):'-';}
/* metal: g/t x t = g ; ppm x t = g ; ppb x t = mg -> g/1000 ; % x t / 100 = t */
function elMetU(a){var u=elUnit(a);return u==='%'?'t':(u?'g':'');}
function elMet(a,g,t){if(!isFinite(g)||!isFinite(t))return NaN;var u=elUnit(a);return u==='%'?g*t/100:(u==='ppb'?g*t/1000:(u?g*t:NaN));}
function elMetF(a,v){return isFinite(v)?(elMetU(a)==='t'?v.toFixed(Math.abs(v)<10?3:1):v.toFixed(Math.abs(v)<100?1:0)):'-';}
function elHd(a){var u=elUnit(a);return a+(u?' ('+u+')':'');}
/* ---------- akumulator per perhitungan (dipanggil dari lyTon / lyTonS / ringkasan kelas / as-mined) ---------- */
function elInit(prim){var m=elModel();if(!m)return null;return elList(prim).map(function(a){return{a:a,A:m.num[a],s:0,w:0};});}
function elAdd(r,i,t){var E=r.E;if(!E)return;for(var k=0;k<E.length;k++){var e=E[k],v=e.A?e.A[i]:NaN;if(v===v&&isFinite(v)){e.s+=v*t;e.w+=t;}}}
function elFin(r){var E=r.E;if(!E)return r;r.el={};r.elw={};E.forEach(function(e,k){var w=e.w,s=e.s;if(k>0&&r.wT>0){w+=r.wT;}/* dilusi skin = kadar 0 utk elemen tambahan */
    r.el[e.a]=w?s/w:NaN;r.elw[e.a]=w;});if(E.length&&isFinite(r.grade)){r.el[E[0].a]=r.grade;if(r.gt)r.elw[E[0].a]=r.gt;}r.elA=E.map(function(e){return e.a;});delete r.E;return r;}
/* gabungan beberapa hasil (dig block per material / tujuan / total) */
function elAgg(){return{t:0,n:0,s:{},w:{},add:function(r,t){t=isFinite(t)?t:(r&&r.t)||0;this.t+=t;this.n++;if(!r||!r.el)return;var me=this;Object.keys(r.el).forEach(function(a){var g=r.el[a],w=r.elw&&isFinite(r.elw[a])?Math.min(r.elw[a],t||r.elw[a]):t;if(isFinite(g)&&w>0){me.s[a]=(me.s[a]||0)+g*w;me.w[a]=(me.w[a]||0)+w;}});},
  g:function(a){return this.w[a]?this.s[a]/this.w[a]:NaN;},met:function(a){return this.w[a]?elMet(a,this.s[a]/this.w[a],this.w[a]):NaN;}};}
/* teks ringkas elemen tambahan: "Ag 12.3 g/t · Cu 0.120 %" */
function elTxt(r,prim,sep){if(!r||!r.el)return '';var L=elExtra(prim||(r.elA&&r.elA[0]));return L.filter(function(a){return a in r.el;}).map(function(a){var u=elUnit(a);return a+' '+elF(a,r.el[a])+(u&&u!=='g/t'?' '+u:'');}).join(sep||'  ·  ');}
function elTxtH(r){var t=elTxt(r);return t?' &middot; <span class=eltx>'+bxE(t).replace(/  ·  /g,' &middot; ')+'</span>':'';}
function elLbl(r){return elTxt(r,null,'  |  ');}
/* ---------- daftar centang (dipakai di tab Dig block, Layout, As-Mined) ---------- */
function elBox(prim,ctx){var c=elCands();if(!c.length)return '';var p=prim||elPrim(),s=elSel();
  return '<div class=elbox><div class=elh><b>Elemen laporan</b> <small>kadar &amp; metal tiap elemen ikut di tabel, CSV, PDF &amp; register</small></div><div class=elck>'+
    c.map(function(a){var on=a===p||s.indexOf(a)>=0,lk=a===p;return '<label class="sw'+(lk?' elp':'')+'" title="'+(lk?'Elemen utama (kelas material) — ganti di pilihan Atribut kadar':'Satuan: '+(elUnit(a)||'tanpa satuan'))+'"><input type=checkbox '+(on?'checked ':'')+(lk?'disabled ':'')+'onchange="elToggle(\''+bxE(a)+'\',this.checked)">'+bxE(a)+(elUnit(a)?' <small>'+bxE(elUnit(a))+'</small>':'')+'</label>';}).join('')+'</div>'+
    '<div class=elbt><button onclick="elAll(1)">Semua</button><button onclick="elAll(0)">Hanya utama</button><button onclick="elAll(2)">Bawaan</button><button onclick="elUnitDlg()" title="Ubah satuan elemen (g/t, %, ppm)">Satuan&hellip;</button></div></div>';}
function elRefresh(){if(window.BX)BX.sc={};
  ['bxPanel','dbPanel','lyPanel','amPanel'].forEach(function(f){try{if(window[f])window[f]();}catch(e){}});try{updatePlot();}catch(e){}try{if(window.SA&&SA.dirty)SA.dirty();}catch(e){}try{if(window.amDirty)amDirty();}catch(e){}}
function elToggle(a,on){var s=elSel().slice(),i=s.indexOf(a);if(on&&i<0)s.push(a);if(!on&&i>=0)s.splice(i,1);BX.ui.rptEl=s;elRefresh();}
function elAll(k){BX.ui.rptEl=k===1?elCands().filter(function(a){return a!==elPrim();}):(k===2?elDef():[]);elRefresh();}
function elUnitDlg(){var L=elList(),U=BX.ui;U.rptU=U.rptU||{};var sebelum=JSON.stringify(U.rptU);var t=prompt('Satuan elemen, format  nama=satuan  dipisah koma (g/t, %, ppm, ppb, atau kosong).\nContoh: cugpt=ppm, pbpct=%',L.map(function(a){return a+'='+elUnit(a);}).join(', '));if(t==null)return;
  t.split(',').forEach(function(p){var q=p.split('=');if(q.length<2)return;var a=q[0].trim(),u=q[1].trim();if(!a)return;if(['g/t','%','ppm','ppb',''].indexOf(u)<0)return;U.rptU[a]=u;});if(JSON.stringify(U.rptU)!==sebelum)elRefresh();}
/* ---------- ringkasan per kelas block model (per blok & komposit flitch) dengan kolom per elemen ---------- */
function elStTbl(C,cnt,hint){var L=elList(bxStatPrim()),T=elAgg(),keys=Object.keys(C).map(Number).sort(function(p,q){return p-q;}),tn=0,tv=0;
  var hd='<tr><th>Kelas</th><th>'+cnt+'</th><th>Vol (m3)</th><th>Ton</th>'+L.map(function(a){return '<th>'+bxE(a)+'</th>';}).join('')+'</tr>';
  var rows=keys.map(function(k){var r=C[k],ci=bxClassInfo(k);elFin(r);tn+=r.n;tv+=r.v;T.add(r,r.t);return '<tr><td><span class=bxsw style=background:'+ci.col+'></span>'+bxE(ci.lab)+'</td><td>'+r.n.toLocaleString()+'</td><td>'+Math.round(r.v).toLocaleString()+'</td><td>'+Math.round(r.t).toLocaleString()+'</td>'+L.map(function(a){return '<td>'+elF(a,r.el?r.el[a]:NaN)+'</td>';}).join('')+'</tr>';}).join('');
  return '<div class=elsc><table class=pltb>'+hd+rows+'<tr class=tot><td>Total</td><td>'+tn.toLocaleString()+'</td><td>'+Math.round(tv).toLocaleString()+'</td><td>'+Math.round(T.t).toLocaleString()+'</td>'+L.map(function(a){return '<td>'+elF(a,T.g(a))+'</td>';}).join('')+'</tr>'+
    (L.length?'<tr class=elmet><td colspan=4>Metal</td>'+L.map(function(a){return '<td>'+elMetF(a,T.met(a))+(elMetU(a)?' '+elMetU(a):'')+'</td>';}).join('')+'</tr>':'')+'</table></div>'+hint;}
function bxStatPrim(){var U=BX.ui,m=BX.m,a=U.attr;if(!m.cat[a])return a;return m.num[U.fAttr]?U.fAttr:(Object.keys(m.num).filter(function(n){return /^AU/i.test(n);})[0]||'');}
function bxStats(idx,cl){var el=$('bxStat');if(!el)return;if(window.lyFcOn&&lyFcOn()&&LY.fst){bxStatsFc(LY.fst,LY.fc?LY.fc.s:1);return;}var U=BX.ui,m=BX.m,sgA=U.sgCol&&m.num[U.sgCol]?m.num[U.sgCol]:null,C={},pr=bxStatPrim();
  idx.forEach(function(i,j){var v=m.sx[i]*m.sy[i]*m.sz[i],t=v*bxSGv(sgA?sgA[i]:NaN),k=cl[j],r=C[k]||(C[k]={n:0,v:0,t:0,E:elInit(pr)});r.n++;r.v+=v;r.t+=t;elAdd(r,i,t);});
  el.innerHTML=elStTbl(C,'Blok','<div class=hint>'+($('sliceClip').checked||VIEW2D?'Hanya blok di dalam slab aktif.':'Seluruh model (aktifkan Potong data di menu Sayatan untuk per slab).')+' Tonase = volume &times; '+(sgA?'kolom '+bxE(U.sgCol):'SG '+U.sg)+'; kadar tiap elemen = rata-rata tertimbang ton.</div>');}
function bxStatsFc(C,s){var el=$('bxStat');if(!el)return;var U=BX.ui,sgA=U.sgCol&&BX.m.num[U.sgCol],B=lyBench();
  el.innerHTML=elStTbl(C,'Kolom','<div class=hint>Komposit flitch RL '+lyFmt(B[0])+'&ndash;'+lyFmt(B[1])+': tiap kolom '+s+'&times;'+s+' m = rata-rata tertimbang tebal &times; SG dari semua blok di dalam flitch. Tonase = volume di dalam flitch &times; '+(sgA?'kolom '+bxE(U.sgCol):'SG '+U.sg)+'.</div>');}
/* komposit flitch: nilai kolom tiap elemen (dipanggil dari lyFcRects) */
function elFcVals(fc){var pr=bxStatPrim();return elList(pr).map(function(a){return{a:a,V:lyFcNum(fc,a)};}).filter(function(e){return e.V;});}
function elStAdd(S,EV,q,w){if(!S.E)S.E=EV.map(function(e){return{a:e.a,A:null,s:0,w:0};});for(var k=0;k<EV.length;k++){var v=EV[k].V[q];if(v===v){S.E[k].s+=v*w;S.E[k].w+=w;}}}
/* ---------- dig block: tabel elemen per material / tujuan / total (di bawah tabel total) ---------- */
function elDbTbl(it){var L=elList();if(L.length<2||!it.length)return '';var G={},D={},T=elAgg();
  it.forEach(function(o){var t=o.ton;if(!t)return;var mt=o.s.d||'-',d=o.dest||'-';(G[mt]=G[mt]||elAgg()).add(t,t.t);(D[d]=D[d]||elAgg()).add(t,t.t);T.add(t,t.t);});
  var row=function(lab,A,cls){return '<tr'+(cls?' class='+cls:'')+'><td>'+lab+'</td><td>'+lyFmt(A.t)+'</td>'+L.map(function(a){return '<td>'+elF(a,A.g(a))+'</td>';}).join('')+'</tr>';};
  return '<div class=elsc><table class="pltb dbtot elt"><tr><th>Kadar elemen</th><th>Ton</th>'+L.map(function(a){return '<th>'+bxE(a)+'</th>';}).join('')+'</tr>'+
    Object.keys(G).map(function(k){return row(bxE(k)+' ('+G[k].n+')',G[k]);}).join('')+Object.keys(D).map(function(k){return row('&rarr; '+bxE(k)+' ('+D[k].n+')',D[k],'dst');}).join('')+row('Total',T,'tot')+
    '<tr class=elmet><td colspan=2>Metal total</td>'+L.map(function(a){return '<td>'+elMetF(a,T.met(a))+(elMetU(a)?' '+elMetU(a):'')+'</td>';}).join('')+'</tr></table></div>';}
(function(){var _t=window.dbTable;if(!_t)return;dbTable=function(){var h=_t.apply(this,arguments);try{var it=lyItems(true);h+=elDbTbl(it);}catch(e){console.error(e);}return h;};})();
/* daftar centang di tab Dig block (di atas daftar dig block) */
(function(){var _d=window.dbPanel;if(!_d)return;dbPanel=function(){var r=_d.apply(this,arguments);try{var b=$('dbBody');if(b&&!b.querySelector('.elbox')&&BX.m){var d=document.createElement('div');d.innerHTML=elBox();var c=b.querySelector('.calcm');if(c&&c.nextSibling)b.insertBefore(d.firstChild,c.nextSibling);else b.insertBefore(d.firstChild,b.firstChild);}}catch(e){console.error(e);}return r;};})();
/* ---------- layout PDF: halaman ringkasan dig block dengan kolom per elemen ---------- */
function lySummary(it){var L=lyU(),ps=PAPER[L.paper]||PAPER.A4,W=L.orient==='L'?ps[0]:ps[1],H=L.orient==='L'?ps[1]:ps[0],ops=[],y=H-24,B=lyBench(),EL=elList(),T=elAgg(),ta=0,tv=0;
  var tx=function(x,yy,s,t,f,c){ops.push({t:'text',x:x,y:yy,s:s,txt:String(t),col:c||'#000',font:f||'H'});};
  tx(15,H-15,5,'Ringkasan dig block - '+lyTitle(L.title),'B');tx(15,H-20.5,2.8,(L.company?L.company+'  |  ':'')+'Flitch RL '+lyFmt(B[0])+' - '+lyFmt(B[1])+' (sayatan BM '+lyFmt(lyZs())+')  |  SG '+(BX.ui&&BX.ui.sgCol?'kolom '+BX.ui.sgCol:(BX.ui?BX.ui.sg:''))+'  |  '+lyDateTxt(),'H','#444');
  /* kolom tetap + per elemen: kadar; metal untuk elemen utama. Lebar nama & tinggi baris menyesuaikan isi supaya TOTAL selalu muat */
  var nT=2+Object.keys(lyDestSum(it)).length,avail=(H-32)-16,rh=Math.max(3.3,Math.min(6.2,avail/Math.max(1,it.length+nT*1.1))),fs=Math.min(EL.length>4?2.3:2.7,rh*0.47);
  var mx=it.reduce(function(a,o){return Math.max(a,String(o.name).length);},12),fixW=8+18+18+17+19+19,nE=EL.length+1,nameW=Math.min(110,mx*fs*0.62+3),eW=(W-30-fixW-nameW)/nE;
  if(eW<12){eW=12;nameW=Math.max(30,W-30-fixW-eW*nE);fs=Math.min(fs,(nameW-3)/(mx*0.62));}eW=Math.min(eW,24);
  var cols=[],x=15;[['No',8],['Nama polygon',nameW],['Material',18],['Tujuan',18],['Luas (m2)',17],['Volume (m3)',19],['Ton',19]].forEach(function(c){cols.push([x,c[0]]);x+=c[1];});EL.forEach(function(a){cols.push([x,elHd(a)]);x+=eW;});cols.push([x,EL.length?EL[0]+' ('+(elMetU(EL[0])||'metal')+')':'Metal']);
  y-=8;ops.push({t:'rect',x:13,y:y-1.8,w:W-26,h:6,fill:'#e8edf5'});cols.forEach(function(c){tx(c[0],y,Math.min(2.8,fs+0.2),c[1],'B');});
  var DS={};it.forEach(function(o,i){var t=o.ton||{t:0,v:0,grade:NaN};T.add(t,t.t);ta+=o.area;tv+=t.v||0;var dk=o.dest||'-';(DS[dk]=DS[dk]||elAgg()).add(t,t.t);DS[dk].a=(DS[dk].a||0)+o.area;y-=rh;if(y<15)return;
    var v=[String(i+1),o.name,o.s.d||'',o.dest||'',o.area.toFixed(1),t.v?t.v.toFixed(1):'-',t.t?t.t.toFixed(2):'-'].concat(EL.map(function(a){return elF(a,t.el?t.el[a]:(a===EL[0]?t.grade:NaN));}));v.push(EL.length?elMetF(EL[0],elMet(EL[0],t.el?t.el[EL[0]]:t.grade,t.t)):'-');
    v.forEach(function(s,k){tx(cols[k][0],y,fs,s,k===1?'C':'H');});ops.push({t:'line',pts:[[13,y-rh*0.33],[W-13,y-rh*0.33]],col:'#d5dbe3',lw:0.15});});
  var tot=function(lab,A,area,vol,c,f){y-=c?Math.max(3.6,rh*0.9):Math.max(4.6,rh*1.1);if(y<14)return;var v=[ '',lab,'','',area!=null?area.toFixed(1):'',vol!=null?vol.toFixed(1):'',A.t.toFixed(2)].concat(EL.map(function(a){return elF(a,A.g(a));}));v.push(EL.length?elMetF(EL[0],A.met(EL[0])):'');v.forEach(function(s,k){if(s!=='')tx(cols[k][0],y,c?Math.min(2.6,fs):Math.min(2.9,fs+0.2),s,f,c);});};
  tot('TOTAL',T,ta,tv,null,'B');Object.keys(DS).forEach(function(k){tot('Tujuan '+k+' ('+DS[k].n+' dig block)',DS[k],DS[k].a,null,'#233a7e','B');});
  if(EL.length>1&&y>18){y-=Math.max(4.5,rh);tx(25,y,2.5,'Metal total: '+EL.map(function(a){return a+' '+elMetF(a,T.met(a))+' '+elMetU(a);}).join('   |   '),'B','#233a7e');}
  tx(15,10,2.2,(lyFlMode()==='comp'?'Tonase = luas blok di dalam polygon x tebal blok di dalam flitch x SG; komposit seluruh tebal flitch '+lyFmt(B[0])+' - '+lyFmt(B[1])+'.':'Tonase = luas blok di dalam polygon x tinggi flitch '+lyFmt(B[0]-B[1])+' m x SG; blok dari sayatan block model di RL '+lyFmt(lyZs())+' (flitch '+lyFmt(B[0])+' - '+lyFmt(B[1])+').')+' Kadar tiap elemen = rata-rata tertimbang tonase dari blok yang sama.','H','#555');
  return{W:W,H:H,ops:ops,scale:0};}
function lyCsv(){var it=lyItems(),B=lyBench(),EL=elList(),r=[['Nama','Material','Tujuan','RL_atas','RL_bawah','Luas_m2','Volume_m3','Ton'].concat(EL.map(function(a){return a+(elUnit(a)?'_'+elUnit(a).replace('/','p').replace('%','pct'):'');})).concat(EL.filter(function(a){return elMetU(a);}).map(function(a){return 'Metal_'+a+'_'+elMetU(a);})).join(',')];
  it.forEach(function(o){var t=o.ton||{},g=function(a){return t.el?t.el[a]:(a===EL[0]?t.grade:NaN);};r.push([o.name,o.s.d||'',o.dest||'',B[0],B[1],o.area.toFixed(2),(t.v||0).toFixed(2),(t.t||0).toFixed(2)].concat(EL.map(function(a){var v=g(a);return isFinite(v)?v.toFixed(4):'';})).concat(EL.filter(function(a){return elMetU(a);}).map(function(a){var v=elMet(a,g(a),t.t||0);return isFinite(v)?v.toFixed(3):'';})).map(function(v){v=String(v);return /[",\r\n]/.test(v)?'"'+v.replace(/"/g,'""')+'"':v;}).join(','));});
  dgDl(r.join('\r\n')+'\r\n','Ringkasan_DigBlock_'+String(ZONE).replace(/[^A-Za-z0-9_-]+/g,'_')+'.csv','text/csv');}
/* ---------- as-mined: akumulasi elemen dari model per sub-blok ---------- */
function elQInit(prim){var m=elModel();return elList(prim).map(function(a){return{a:a,A:m.num[a],s:0,w:0};});}
function elQAdd(q,p,t){if(!q.E)return;for(var k=0;k<q.E.length;k++){var e=q.E[k],v=e.A?e.A[p]:NaN;if(v===v&&isFinite(v)){e.s+=v*t;e.w+=t;}}}
function elQFin(q,gA){var el={},w={};(q.E||[]).forEach(function(e,k){el[e.a]=e.w?e.s/e.w:NaN;w[e.a]=e.w;});var a0=q.E&&q.E[0]?q.E[0].a:null;if(a0&&isFinite(gA))el[a0]=gA;return{el:el,elw:w,elA:(q.E||[]).map(function(e){return e.a;})};}
/* ---------- as-mined report per flitch: elemen tambahan (dari model GC pada sub-blok yang sama) ---------- */
function elAmX(){var U=amU();return elExtra(U.attr);}
function elAmCsvH(){var L=elAmX();return L.length?','+L.map(function(a){return a+(elUnit(a)?'_'+elUnit(a).replace('/','p').replace('%','pct'):'');}).join(',')+(L.filter(elMetU).length?','+L.filter(elMetU).map(function(a){return 'Metal_'+a+'_'+elMetU(a);}).join(','):''):'';}
function elAmCsvV(x){var L=elAmX(),g=function(a){return x.el&&isFinite(x.el[a])?x.el[a]:NaN;};return L.map(function(a){var v=g(a);return isFinite(v)?v.toFixed(4):'';}).concat(L.filter(elMetU).map(function(a){var v=elMet(a,g(a),x.elw&&x.elw[a]||x.t);return isFinite(v)?v.toFixed(3):'';}));}
function elAmTot(R){var A=elAgg();R.forEach(function(x){A.add({t:x.t,el:x.el||{},elw:x.elw||{}},x.t);});return A;}
function elAmCsvT(R){var L=elAmX(),A=elAmTot(R);return L.map(function(a){var v=A.g(a);return isFinite(v)?v.toFixed(4):'';}).concat(L.filter(elMetU).map(function(a){var v=A.met(a);return isFinite(v)?v.toFixed(3):'';}));}
function elAmPage(R){var L=elAmX();if(!L.length||!R.length)return null;var U=amU(),W=297,H=210,ops=[],y=H-18,A=elAmTot(R);
  var tx=function(x,yy,s,t,f,c,an){ops.push({t:'text',x:x,y:yy,s:s,txt:String(t),col:c||'#000',font:f||'H',anchor:an});};
  ops.push({t:'rect',x:0,y:H-12,w:W,h:12,fill:'#233a7e'});tx(12,H-8,5,'GC-Ex','B','#f0c047');tx(32,H-8,4,'Report As-Mined - elemen lain'+(U.period?' - '+U.period:''),'B','#ffffff');tx(W-12,H-8,2.8,lyDateTxt(),'H','#ffffff','e');
  y-=9;var ew=Math.min(28,(W-12-12-60)/Math.max(1,L.length*2)),cols=[[12,'Flitch (RL)'],[40,'Ton']],x=62;L.forEach(function(a){cols.push([x,elHd(a)]);x+=ew;});L.forEach(function(a){if(elMetU(a)){cols.push([x,'Metal '+a+' ('+elMetU(a)+')']);x+=ew;}});
  var fs=L.length>4?2.2:2.6;ops.push({t:'rect',x:10,y:y-1.8,w:W-20,h:6,fill:'#e8edf5'});cols.forEach(function(c){tx(c[0],y,fs+0.1,c[1],'B');});
  var row=function(lab,t,g,w,b){y-=6;if(y<30)return;var v=[lab,t.toFixed(2)].concat(L.map(function(a){return elF(a,g(a));})).concat(L.filter(elMetU).map(function(a){return elMetF(a,elMet(a,g(a),w(a)));}));v.forEach(function(s,k){tx(cols[k][0],y,fs,s,b?'B':'H');});if(!b)ops.push({t:'line',pts:[[10,y-2],[W-10,y-2]],col:'#d5dbe3',lw:0.15});};
  R.forEach(function(r){row(lyFmt(r.top)+' - '+lyFmt(r.bot),r.t,function(a){return r.el?r.el[a]:NaN;},function(a){return r.elw&&r.elw[a]||r.t;});});
  y-=1;row('TOTAL',A.t,function(a){return A.g(a);},function(a){return A.w[a]||0;},true);
  y-=8;tx(12,y,2.6,'Kadar elemen lain = rata-rata tertimbang ton dari model GC pada sub-blok as-mined yang sama (hanya '+U.attr+' yang dikoreksi data sampel baru). Elemen dipilih di daftar "Elemen laporan".','H','#555');
  if(R.some(function(r){return !r.el;})){y-=4.5;tx(12,y,2.6,'Flitch tanpa nilai elemen dihitung dengan versi GC-Ex sebelumnya: klik Hitung ulang di flitch tersebut.','H','#8a5a00');}
  return{W:W,H:H,ops:ops,scale:0};}
/* opsi label elemen di peta & daftar centang di panel Layout PDF */
(function(){var _l=window.lyPanel;if(!_l)return;lyPanel=function(){var r=_l.apply(this,arguments);try{var b=$('lyBody');if(b&&BX.m&&!b.querySelector('.elbox')){var L=lyU(),d=document.createElement('div');d.innerHTML=elBox()+'';var e=d.firstChild;
      e.insertAdjacentHTML('beforeend','<label class=sw style="margin-top:4px;font-size:12px"><input type=checkbox '+(L.lblEl!==false?'checked':'')+' onchange="lyU().lblEl=this.checked;try{SA.dirty();}catch(x){}">Tulis kadar elemen tambahan di bawah label tonase pada peta</label>');
      var h=b.querySelector('.hint');if(h&&h.nextSibling)b.insertBefore(e,h.nextSibling);else b.insertBefore(e,b.firstChild);}}catch(x){console.error(x);}return r;};})();
