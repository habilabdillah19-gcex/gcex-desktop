/* ================= Watermark hak cipta (kedua aplikasi) =================
   Teks kecil & redup di ujung kanan bilah status bawah dan di kepala jendela Import data — tidak menutupi tampilan / tombol. */
(function(){var T='Copyright Habil Abdillah 2026';window.GCEX_COPY=T;
  function put(){var f=document.getElementById('status');if(f&&!document.getElementById('wmark')){var s=document.createElement('span');s.id='wmark';s.textContent='© '+T;s.title='GC-Ex · Grade Control Excellence · '+T+'\nKomponen open-source (Plotly.js MIT, Electron, Python, dll.) & penafian merek dagang: menu Bantuan › Lisensi pihak ketiga & merek dagang';f.appendChild(s);}
    var h=document.querySelector('#imp .impHead');if(h&&!document.getElementById('wmarkImp')){var t=document.createElement('span');t.id='wmarkImp';t.textContent='© '+T;h.appendChild(t);}}
  var css=document.createElement('style');css.id='wmCss';css.textContent='#wmark{margin-left:12px;padding-left:10px;border-left:1px solid var(--bd,#d5dbe3);color:var(--mu,#6b7785);opacity:.8;font-size:10.5px;white-space:nowrap;user-select:none;pointer-events:auto}'+
    '#wmarkImp{margin-left:auto;align-self:flex-end;font-size:10.5px;opacity:.7;white-space:nowrap;user-select:none;padding-left:12px}';
  (document.head||document.documentElement).appendChild(css);
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',put);else put();setTimeout(put,1500);})();
/* ================= Layar penuh (kedua aplikasi): tombol di bilah atas + F11 ================= */
(function(){var D=window.gcexDesktop,st=false,btn=null;
  var IC_ON='<svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M4 9V4h5M20 9V4h-5M4 15v5h5M20 15v5h-5"/></svg>',
      IC_OFF='<svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M9 4v5H4M15 4v5h5M9 20v-5H4M15 20v-5h5"/></svg>';
  function upd(v){st=!!v;document.body.classList.toggle('gcex-fs',st);if(btn){btn.innerHTML=st?IC_OFF:IC_ON;btn.title=st?'Keluar layar penuh (F11)':'Layar penuh (F11)';btn.classList.toggle('on',st);}
    try{setTimeout(function(){if(window.Plotly&&Plotly.Plots)document.querySelectorAll('.js-plotly-plot').forEach(function(p){try{Plotly.Plots.resize(p);}catch(e){}});},250);}catch(e){}}
  window.gcexFullscreen=async function(on){if(D&&D.fullscreen){upd(await D.fullscreen(on));return st;}
    var want=on==null?!document.fullscreenElement:!!on;try{if(want&&!document.fullscreenElement)await document.documentElement.requestFullscreen();else if(!want&&document.fullscreenElement)await document.exitFullscreen();}catch(e){}return !!document.fullscreenElement;};
  if(D&&D.onFullscreen)D.onFullscreen(upd);document.addEventListener('fullscreenchange',function(){if(!D||!D.fullscreen)upd(!!document.fullscreenElement);});
  /* browser biasa: F11 bawaan browser tetap bekerja; tombol memakai Fullscreen API */
  function put(){var top=document.getElementById('top');if(!top||document.getElementById('fsBtn'))return;var png=[].filter.call(top.querySelectorAll('button'),function(b){return /PNG/.test(b.textContent);})[0];
    btn=document.createElement('button');btn.id='fsBtn';btn.type='button';btn.className=png?png.className:'tb';btn.style.padding='2px 7px';btn.onclick=function(){window.gcexFullscreen();};upd(st);
    if(png&&png.parentNode)png.parentNode.insertBefore(btn,png.nextSibling);else top.appendChild(btn);}
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',put);else put();setTimeout(put,1500);setTimeout(put,5000);})();
