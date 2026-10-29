/* ================= GC-Ex 0.19: perbaikan UI bersama (Block Model & Drillhole Ultimate) =================
   - "Gambar garis sayatan": tidak lagi jendela gambar kosong; jendela 3D dibuka TAMPAK ATAS (data tetap tampil) lalu
     garis sayatan ditarik di atasnya (alat Sayatan 3D garis bebas, bidang tegak)
   - legenda: string kontrol bernomor (QV_Utama_HW_01, _02, ...) digabung per domain & sisi (QV_Utama_HW / QV_Utama_FW)
   - Block Model: "Rekap & edit string" (daftar string + edit bentuk / buka bidang / tampil / hapus)
   - Drillhole: Geological Modelling - Properti hanya domain aktif (dipilih di Project Tree), tanpa nomor bagian */
(function(){
  /* ---------- 1. garis sayatan di jendela 3D tampak atas ---------- */
  if(typeof window.drawOpen==='function'&&typeof window.s3Open==='function'){var _do=drawOpen;
    drawOpen=function(md){if(md==='plan')return _do.apply(this,arguments);
      try{if(window.S3&&S3.mode)s3Off();}catch(e){}
      try{if(window.VIEW2D)toggle2D();}catch(e){}
      try{setCam(0,-0.01,2.5);}catch(e){}
      setTimeout(function(){try{if(window.S3)S3.vert=true;s3Open();if(window.s3Msg)s3Msg('Tampak atas: klik-tahan lalu tarik garis sayatan P1 &rarr; P2 di atas data (atau klik dua titik). Bidang tegak; dip bisa diubah sesudahnya di Properti. Esc = batal.');}catch(e){console.error(e);}},350);};}
  /* ---------- 2. legenda string digabung ---------- */
  var RX=/^(.+?_(?:HW|FW))_?\d+$/i;
  if(window.Plotly&&Plotly.react&&!Plotly._gx19){var _r=Plotly.react;Plotly._gx19=1;
    Plotly.react=function(gd,d){try{if(Array.isArray(d)){var seen={};d.forEach(function(t){if(!t||typeof t.name!=='string')return;var m=RX.exec(t.name);if(!m||t.showlegend===false)return;
          var g=m[1];t.name=g;t.legendgroup=t.legendgroup||('gx_'+g);if(seen[g])t.showlegend=false;else seen[g]=1;});
          /* nama legenda yang sama (mis. puluhan "String 17 HG" dig block) cukup tampil sekali */
          var dn={};d.forEach(function(t){if(!t||typeof t.name!=='string'||t.showlegend===false||!/lines/.test(t.mode||''))return;if(dn[t.name]){t.showlegend=false;t.legendgroup=dn[t.name];}else{dn[t.name]=t.legendgroup=t.legendgroup||('gxn_'+t.name);}});}}catch(e){console.error(e);}
      return _r.apply(this,arguments);};}
  /* ---------- 3. Block Model: rekap & edit string ---------- */
  if(typeof window.dgList==='function'&&window.DG&&typeof window.dbEdStart==='function'){
    window.dgEditShape=function(i){var s=DG.S[i];if(!s)return;try{if(window.dgGo)dgGo(i);}catch(e){}var sn=window.BX&&BX.ui?BX.ui.snap:undefined;
      setTimeout(function(){dbEdStart(i);if(!s.db&&window.BX&&BX.ui&&sn!==undefined)BX.ui.snap=sn;},120);};
    dgList=function(){var el=$('dgList');if(!el)return;var S=DG.S.filter(function(s){return !s.amTmp&&!s.inner;});
      if(!S.length){el.innerHTML='<div class="gxRekap"><div class="gxRk">Rekap string</div><div class=hint>Belum ada string. Buat string baru dengan <b>Mulai</b> di bawah, lalu klik titik di Sayatan 2D.</div></div>';return;}
      var tl=0,nc=0;S.forEach(function(s){try{tl+=dgLen(s);}catch(e){}if(s.closed)nc++;});
      el.innerHTML='<div class="gxRekap"><div class="gxRk">Rekap string <span>'+S.length+' string &middot; '+nc+' tertutup &middot; '+tl.toFixed(0)+' m</span></div><table class=pltb><tr><th title=Tampilkan></th><th>No</th><th>Ket.</th><th>Titik</th><th>Panjang</th><th>Bidang</th><th></th></tr>'+
        S.map(function(s){var i=DG.S.indexOf(s),A=0;try{A=dgArea(s);}catch(e){}var L=0;try{L=dgLen(s);}catch(e){}
          return '<tr><td><input type=checkbox '+(s.vis?'checked':'')+' onchange="dgVis('+i+',this.checked)" title=Tampilkan></td><td><span style="color:'+s.col+';font-weight:700">'+s.no+'</span></td><td>'+(s.d||'-')+(s.db?' <small>(dig)</small>':'')+'</td>'+
            '<td title="'+(A?'Luas '+A.toFixed(1)+' m2':'')+'">'+s.pts.length+(s.closed?' &#9711;':'')+'</td><td>'+L.toFixed(1)+' m</td>'+
            '<td><a href="javascript:void(0)" onclick="dgGo('+i+')" title="Buka bidang string ini di Sayatan 2D">'+(s.pl?(s.pl.m==='H'?'Z '+(+s.pl.pos).toFixed(1):'S '+normAz(s.pl.az)+'/'+s.pl.dip):'-')+'</a></td>'+
            '<td style="white-space:nowrap"><button class=lb onclick="dgEditShape('+i+')" title="Edit bentuk: tarik titik, tarik titik tengah = tambah, Shift+klik = hapus; Enter / Esc = simpan">&#9998;</button><button class=x onclick="dgDel('+i+')" title=Hapus>&times;</button></td></tr>';}).join('')+'</table></div>';};
    try{dgList();}catch(e){}
    var st=document.createElement('style');st.textContent='.gxRekap{margin:6px 0 10px}.gxRk{font-weight:700;font-size:12px;color:var(--pr);margin:4px 0}.gxRk span{font-weight:400;color:var(--mu);margin-left:6px}.gxRekap td{vertical-align:middle}.gxRekap button.lb{height:20px;padding:0 6px;margin-right:3px}';document.head.appendChild(st);
    /* rekap tampil paling atas, kontrol digitasi di bawahnya sebagai "String baru" */
    (function(){var P=$('pDig'),l=$('dgList');if(!P||!l)return;var h=P.querySelector('h3');if(h){h.textContent='Rekap & edit string';h.parentNode.insertBefore(l,h.nextSibling);l.style.maxHeight='none';
      var sb=document.createElement('h4');sb.className='lyhead';sb.textContent='String baru';var ds=$('dgState');if(ds)ds.parentNode.insertBefore(sb,ds);}})();}
  /* ---------- 4. Drillhole: Geological Modelling hanya domain aktif ---------- */
  if(typeof window.gmPanel==='function'&&window.GM){var CIR=/^[①-⑳❶-❿]\s*/;
    var tidy=function(){var b=$('gmBody');if(!b)return;
      /* hanya domain aktif di Properti */
      var L=b.querySelector('.gmdoms');if(L){var rows=L.querySelectorAll('.gmd');Array.prototype.forEach.call(rows,function(r){r.style.display=r.classList.contains('on')?'':'none';});L.style.maxHeight='none';L.style.overflow='visible';
        if(!L.querySelector('.gmd.on')&&rows.length&&!b.querySelector('.gxNoAct'))L.insertAdjacentHTML('afterend','<div class="hint gxNoAct">Pilih domain di Project Tree (Geological Modelling) untuk mengerjakannya di sini.</div>');}
      /* tambah domain pindah ke Project Tree */
      Array.prototype.forEach.call(b.querySelectorAll('button'),function(bt){if(!/^\+\s*Domain$/i.test(bt.textContent.trim()))return;var r=bt.parentNode;while(r&&r!==b&&!r.querySelector('input[type=text]'))r=r.parentNode;if(r&&r!==b)r.style.display='none';});
      /* tanpa nomor bagian (② Flag, ③ String, ...) */
      Array.prototype.forEach.call(b.querySelectorAll('h4,.gmtabs button,.imsec,summary'),function(h){var w=document.createTreeWalker(h,NodeFilter.SHOW_TEXT,null),n;while((n=w.nextNode())){if(CIR.test(n.textContent)){n.textContent=n.textContent.replace(CIR,'');break;}if(n.textContent.trim())break;}});
      Array.prototype.forEach.call(b.querySelectorAll('h4'),function(h){if(/^domain vein$/i.test(h.textContent.trim()))h.textContent='Domain aktif';});};
    var _gp=gmPanel;gmPanel=function(){var r=_gp.apply(this,arguments);try{tidy();}catch(e){console.error(e);}return r;};
    try{tidy();}catch(e){}}
})();
