/* ================= GC-Ex Block Model 0.14: digitasi manual dig block setara otomatis =================
   - Material dipilih dari daftar kelas (string number & warna ikut aturan kelas, sama dengan dig block otomatis)
     + isian bebas; tujuan (DEST) bisa ditetapkan sebelum mendigit (kosong = ikut aturan tujuan).
   - Enter menutup poligon & langsung menjadi dig block selama flitch aktif (juga dari menu Digitasi string bebas).
   - Sesudah Enter: ringkasan grade × tonnage dig block baru tampil di panel & baris daftarnya disorot; bentuk / warna /
     nama / tujuan diedit dari daftar (✎) atau klik garisnya di Penampang 2D.
   - String tertutup di menu Digitasi bisa dijadikan dig block (tombol ⇢ DB). */
var DGM={dest:'',last:null};
function dgmMats(){var U=dbU(),seen={},out=[];(U.rules||[]).forEach(function(q){var m=String(q.m||'').trim().toUpperCase();if(m&&!seen[m]){seen[m]=1;out.push(m);}});
  ['WASTE'].forEach(function(m){if(!seen[m]){seen[m]=1;out.push(m);}});var c=String(U.dbMat||'').trim().toUpperCase();if(c&&!seen[c])out.unshift(c);return out;}
function dgmDests(){var L=lyU(),seen={},out=[];(L.destR||[]).forEach(function(q){var d=String(q.d||'').trim();if(d&&!seen[d]){seen[d]=1;out.push(d);}});var d0=String(L.dest||'').trim();if(d0&&!seen[d0])out.push(d0);return out;}
function dgmSetMat(v){v=String(v||'').trim().toUpperCase();if(!v)return;BX.ui.dbMat=v;if($('dgDesc'))$('dgDesc').value=v;try{if(SA&&SA.dirty)SA.dirty();}catch(e){}dbPanel();}
function dgmStamp(s){if(!s||!s.closed||s.db||s.inner||!window.dbSN)return false;var B=lyBench(),t=dbSN(s.d||BX.ui.dbMat||'ORE');s.d=s.d||BX.ui.dbMat||'ORE';s.no=t.n;s.col=t.c;s.db={top:B[0],bot:B[1],zs:lyZs()};s.manual=true;if(!s.id)s.id=dbId();return true;}
function dgmToDb(i){var s=DG.S[i];if(!s)return;if(!s.closed){alert('Hanya string tertutup yang bisa dijadikan dig block.');return;}if(!dbFlOn()){alert('Terapkan flitch dulu (Dig Block › Flitch), lalu buka Penampang 2D.');return;}
  var z=s.pts[0][2],B=lyBench();if(!(z>=B[1]-1e-6&&z<=B[0]+1e-6)&&!confirm('String ini tidak berada di flitch aktif (RL '+lyFmt(B[0])+'–'+lyFmt(B[1])+'). Tetap jadikan dig block flitch aktif?'))return;
  if(!s.d)s.d=BX.ui.dbMat||'ORE';dgmStamp(s);DGM.last=s.id;dgSave();dgList();updatePlot();try{dbPanel();}catch(e){}}
/* ---------- Enter menutup poligon bila flitch aktif (juga dari Digitasi string bebas) ---------- */
window.addEventListener('keydown',function(e){if(e.key!=='Enter'||!window.DG||!DG.on||DG.dbm)return;var tg=(e.target&&e.target.tagName)||'';if(tg==='INPUT'||tg==='SELECT'||tg==='TEXTAREA')return;
  try{if(DG.cur.length>=3&&dbFlOn())DG.dbm=String(BX.ui.dbMat||$('dgDesc')&&$('dgDesc').value||'ORE');}catch(x){}},true);
(function(){var _f=dgFinish;dgFinish=function(closed){var n0=DG.S.length,man=!!DG.dbm;var r=_f.apply(this,arguments);
    try{if(DG.S.length>n0){var s=DG.S[DG.S.length-1];if(closed&&!s.db&&dbFlOn()&&s.pl&&s.pl.m==='H'){dgmStamp(s);dgSave();}
        if(s.db){if(DGM.dest)s.dest=DGM.dest;DGM.last=s.id;dgSave();dgList();try{dbPanel();}catch(x){}try{if(window.amPanel&&$('pAM')&&!$('pAM').hidden)amPanel();}catch(x){}updatePlot();}}}catch(e){console.error(e);}
    return r;};})();
/* ---------- panel: material dari kelas, tujuan, ringkasan dig block terakhir ---------- */
function dgmLastHtml(){if(!DGM.last)return '';var it=null;try{it=lyItems(true).filter(function(o){return o.s.id===DGM.last;})[0];}catch(e){}if(!it)return '';var t=it.ton||{t:0,grade:NaN};
  return '<div class=dgmlast><b>&#10003; Dig block tersimpan:</b> <i class=dgmsw style="background:'+bxE(it.s.col)+'">'+it.s.no+'</i> '+bxE(it.name)+'<br>'+it.area.toFixed(1)+' m&sup2; &middot; <b>'+(t.t?lyFmt(t.t)+' t @ '+(isFinite(t.grade)?t.grade.toFixed(2):'-')+' g/t':'-')+'</b> &middot; '+bxE(it.s.d||'-')+' &rarr; '+bxE(it.dest||'-')+
    '<div class=g3 style="margin-top:4px"><button onclick="dbEdStart('+it.idx+')" title="Geser / tambah / hapus titik">&#9998; Edit bentuk</button><button onclick="dbPop&&dbPop('+it.idx+')" title="Warna, nomor, material, tujuan">&#9881; Properti</button><button onclick="dbDel('+it.idx+')">&times; Hapus</button></div></div>';}
(function(){var _p=dbPanel;dbPanel=function(){var r=_p.apply(this,arguments);try{var el=$('dbBody');if(!el||!BX.m)return r;var U=dbU();
    /* daftar ganda (0.13) di bagian manual dibuang: daftar Running grade & tonnage di bawah sudah lengkap */
    [].slice.call(el.children).forEach(function(c){if(c.classList.contains('dbsub')&&/daftar dig block/i.test(c.textContent||'')){var n=c;while(n){var nx=n.nextElementSibling;el.removeChild(n);n=nx&&!nx.classList.contains('dbsub')?nx:null;}}});
    var inp=el.querySelector('input[onchange*="dbSet(\'dbMat\'"]');
    if(inp){var box=inp.parentNode,cur=String(U.dbMat||'ORE').toUpperCase(),M=dgmMats(),sn=dbSN(cur),D=dgmDests();
      box.innerHTML='<label>Material / kelas</label><div class=dgmrow><i class=dgmsw style="background:'+bxE(sn.c)+'" title="Warna string">'+sn.n+'</i><select onchange="if(this.value===\'*\'){var v=prompt(\'Nama material baru:\',\'\');if(v)dgmSetMat(v);else dbPanel();}else dgmSetMat(this.value)">'+
        M.map(function(m){var t=dbSN(m);return '<option value="'+bxE(m)+'"'+(m===cur?' selected':'')+'>'+bxE(m)+' · string '+t.n+'</option>';}).join('')+'<option value="*">+ Material lain…</option></select></div>';
      var row=box.parentNode,extra=document.createElement('div');extra.className='g2 dgmx';extra.setAttribute('data-seg','man');
      extra.innerHTML='<div><label>Tujuan (DEST)</label><select onchange="DGM.dest=this.value"><option value="">auto (aturan tujuan)</option>'+D.map(function(d){return '<option'+(d===DGM.dest?' selected':'')+'>'+bxE(d)+'</option>';}).join('')+'</select></div>'+
        '<div><label>Warna kelas</label><input type=color value="'+bxE(sn.c)+'" onchange="dbSNset(\''+bxE(cur)+'\',\'c\',this.value);dbPanel()" title="Warna string untuk material ini (berlaku juga untuk dig block otomatis)"></div>';
      row.parentNode.insertBefore(extra,row.nextSibling);
      var run=$('dbRun');if(run&&!DG.on){var lh=dgmLastHtml();if(lh){var d=document.createElement('div');d.innerHTML=lh;d.firstChild.setAttribute('data-seg','man');run.parentNode.insertBefore(d.firstChild,run.nextSibling);}}}
    if(DGM.last){var rows=el.querySelectorAll('.lylist .lyrow');rows.forEach(function(rw){var b=rw.querySelector('button.ed');if(b&&/dbEdStart\((\d+)\)/.test(b.getAttribute('onclick')||'')){var i=+RegExp.$1;if(DG.S[i]&&DG.S[i].id===DGM.last)rw.classList.add('dgmhl');}});}
  }catch(e){console.error(e);}return r;};})();
/* ---------- daftar string Digitasi: tombol jadikan dig block ---------- */
(function(){var _l=dgList;dgList=function(){var r=_l.apply(this,arguments);try{var el=$('dgList');if(!el)return r;var tr=el.querySelectorAll('tr');
    DG.S.forEach(function(s,i){var row=tr[i+1];if(!row)return;var td=row.lastElementChild;if(!td)return;
      if(s.db){var t=document.createElement('small');t.className='dgmtag';t.title='Dig block flitch RL '+lyFmt(s.db.top)+'–'+lyFmt(s.db.bot);t.textContent='DB';td.insertBefore(t,td.firstChild);}
      else if(s.closed){var b=document.createElement('button');b.className='lb';b.title='Jadikan dig block flitch aktif (grade × tonnage, nomor & warna kelas)';b.innerHTML='&#8680;DB';b.onclick=function(){dgmToDb(i);};td.insertBefore(b,td.firstChild);}});}catch(e){console.error(e);}return r;};
  try{dgList();}catch(e){}})();
(function(){var st=document.createElement('style');st.textContent=
  '.dgmrow{display:flex;gap:5px;align-items:center}.dgmrow select{flex:1;min-width:0}'+
  'i.dgmsw{display:inline-flex;align-items:center;justify-content:center;min-width:22px;height:18px;border-radius:3px;font:700 10px/1 var(--ui-font,Arial);color:#fff;text-shadow:0 0 2px rgba(0,0,0,.7);font-style:normal;flex:0 0 auto}'+
  '.dgmx{margin-top:6px}.dgmlast{margin:6px 0;padding:6px 8px;border:1px solid var(--ac);border-left:4px solid var(--ac);border-radius:5px;background:var(--acs);font-size:11.5px;line-height:1.45}'+
  '#dbBody .lyrow.dgmhl{outline:2px solid var(--ac);outline-offset:-1px;border-radius:4px}#dgList small.dgmtag{display:inline-block;padding:0 4px;margin-right:3px;border-radius:3px;background:var(--prs);color:var(--pr);font-weight:700}'+
  '#dgList button.lb{font-size:10.5px;padding:0 4px;min-height:18px;margin-right:3px}';document.head.appendChild(st);})();
