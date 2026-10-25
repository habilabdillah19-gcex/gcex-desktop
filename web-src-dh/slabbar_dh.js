/* ================= GC-Ex Drillhole: bilah sayatan mengambang (Maju / Mundur) =================
   Tombol Maju / Mundur dipindah dari bilah atas ke bilah kecil di area tampilan. Bilah hanya muncul saat
   sayatan dipakai: Penampang 2D aktif, atau di 3D "Potong data (hanya dalam slab)" / "Tampilkan bidang potong" dicentang.
   Isi: Mundur, posisi (bisa diketik), Maju, tebal slab, tombol 2D/3D. PageUp / PageDown = Maju / Mundur. */
(function(){if(window.SLB||typeof stepPos!=='function'||typeof updatePlot!=='function')return;
  var $=function(i){return document.getElementById(i);},bar=null;
  var on=function(){try{return !!(VIEW2D||($('sliceClip')&&$('sliceClip').checked)||($('showPlane')&&$('showPlane').checked));}catch(e){return false;}};
  var axis=function(){var m=$('sMode')?$('sMode').value:'H';return m==='H'?'Elevasi':'offset';};
  function build(){var st=$('stage');if(!st||bar)return;bar=document.createElement('div');bar.id='slabBar';bar.setAttribute('role','toolbar');
    bar.innerHTML='<span class="sbt" title="Sayatan aktif">Sayatan</span>'+
      '<button type="button" data-d="-1" title="Mundur sejauh tebal slab (PageDown)">&#9664; Mundur</button>'+
      '<label class="sbp" title="Posisi sayatan; ketik angka lalu Enter"><input type="number" step="any" id="sbPos"><span id="sbAx"></span></label>'+
      '<button type="button" data-d="1" title="Maju sejauh tebal slab (PageUp)">Maju &#9654;</button>'+
      '<label class="sbk" title="Tebal slab = jarak satu langkah">Tebal <input type="number" step="any" min="0.1" id="sbThick"> m</label>'+
      '<button type="button" id="sb2d" title="Ganti Penampang 2D / tampilan 3D">2D</button>';
    st.appendChild(bar);
    bar.addEventListener('click',function(e){var b=e.target.closest('button');if(!b)return;if(b.id==='sb2d'){toggle2D();return;}stepPos(+b.getAttribute('data-d'));});
    $('sbPos').addEventListener('change',function(){var p=$('pos'),v=parseFloat(this.value);if(!p||!isFinite(v))return;p.value=Math.min(+p.max,Math.max(+p.min,v));updatePlot();});
    $('sbThick').addEventListener('change',function(){var t=$('thick'),v=parseFloat(this.value);if(!t||!(v>0))return;t.value=v;updatePlot();});
    ['sbPos','sbThick'].forEach(function(k){$(k).addEventListener('keydown',function(e){if(e.key==='Enter'){this.blur();}});});}
  function sync(){if(!bar)build();if(!bar)return;var vis=on();bar.style.display=vis?'flex':'none';if(!vis)return;
    var p=$('pos'),t=$('thick'),a=document.activeElement;if(p&&a!==$('sbPos'))$('sbPos').value=(+p.value||0).toFixed(1);if(t&&a!==$('sbThick'))$('sbThick').value=t.value;
    $('sbAx').textContent='m '+axis();var b=$('sb2d');b.textContent=VIEW2D?'3D':'2D';b.title=VIEW2D?'Kembali ke tampilan 3D':'Buka Penampang 2D dari slab ini';b.classList.toggle('on',!!VIEW2D);}
  var up=updatePlot;updatePlot=function(){var r=up.apply(this,arguments);try{sync();}catch(e){}return r;};
  document.addEventListener('change',function(e){var id=e.target&&e.target.id;if(id==='sliceClip'||id==='showPlane'||id==='sMode'||id==='thick')setTimeout(sync,0);},true);
  var p=$('pos');if(p)p.addEventListener('input',function(){if(bar&&document.activeElement!==$('sbPos'))$('sbPos').value=(+p.value||0).toFixed(1);});
  document.addEventListener('keydown',function(e){if(!on()||e.ctrlKey||e.altKey||e.metaKey)return;var t=e.target,tag=t&&t.tagName;if(tag==='INPUT'||tag==='TEXTAREA'||tag==='SELECT'||(t&&t.isContentEditable))return;
    if(e.key==='PageUp'){e.preventDefault();stepPos(1);}else if(e.key==='PageDown'){e.preventDefault();stepPos(-1);}});
  var css=document.createElement('style');css.id='slabBarCss';css.textContent=
    '#hdStep{display:none!important}'+
    '#slabBar{position:absolute;top:8px;left:50%;transform:translateX(-50%);z-index:6;display:none;align-items:center;gap:4px;padding:4px 6px;background:var(--sf,#fff);color:var(--tx,#1c2733);'+
      'border:1px solid var(--bd,#c9d3de);border-bottom-color:#9eabbc;border-radius:7px;box-shadow:0 3px 0 rgba(16,24,40,.12);font-size:11.5px;white-space:nowrap;pointer-events:auto}'+
    '#slabBar .sbt{font-weight:700;font-size:10.5px;letter-spacing:.05em;text-transform:uppercase;color:var(--mu,#6b7785);padding:0 4px 0 2px}'+
    '#slabBar button{font:inherit;min-height:24px;padding:2px 8px;border-radius:5px;border:1px solid var(--bd,#c9d3de);border-bottom-color:#9eabbc;background:var(--bg,#f4f6f9);color:inherit;cursor:pointer}'+
    '#slabBar button:hover{filter:brightness(1.04)}#slabBar button:active{transform:translateY(1px)}'+
    '#slabBar button.on,#slabBar #sb2d{background:var(--mj,#f0c047);border-color:var(--mjln,#d6a12b);color:var(--mjtx,#1d2b5e);font-weight:700}'+
    '#slabBar input{font:inherit;width:62px;height:22px;padding:0 4px;border:1px solid var(--bd,#c9d3de);border-radius:4px;background:var(--sf,#fff);color:inherit;text-align:right;font-variant-numeric:tabular-nums}'+
    '#slabBar .sbk input{width:44px}#slabBar label{display:inline-flex;align-items:center;gap:4px;color:var(--mu,#6b7785)}#slabBar .sbp{color:inherit}'+
    'body.dark #slabBar{box-shadow:0 3px 0 rgba(0,0,0,.4)}';
  (document.head||document.documentElement).appendChild(css);
  window.SLB={sync:sync,on:on};
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',function(){build();sync();});else{build();sync();}
})();
