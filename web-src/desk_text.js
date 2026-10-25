/* ================= GC-Ex Desktop: teks antarmuka tanpa istilah "browser" =================
   Banyak teks GC-Ex ditulis untuk versi HTML di browser ("tersimpan di browser ini", "Pakai Edge / Chrome",
   "Saat browser meminta izin folder ..."). Di GC-Ex Desktop (.exe) istilah itu membingungkan, jadi teks di layar dan di
   kotak pesan disesuaikan. Hanya aktif di aplikasi desktop; di browser teks aslinya tetap. */
(function(){var D=window.gcexDesktop;if(!D||window.GCTX)return;
  var R=[[/berjalan offline di browser/g,'berjalan offline di komputer ini'],[/(di|ke|dari) browser komputer ini/g,'$1 komputer ini'],
    [/penyimpanan browser/g,'penyimpanan GC-Ex di komputer ini'],[/salinan browser( ini)?/g,'salinan di komputer ini'],[/versi Anda di browser/g,'versi Anda di komputer ini'],
    [/daftar (proyek )?browser/g,'daftar proyek di komputer ini'],[/proyek yang dibuka dari daftar browser/g,'proyek yang dibuka dari daftar komputer ini'],
    [/Browser menolak akses clipboard/g,'Akses clipboard ditolak'],[/\(Edge \/ Chrome\)/g,'(GC-Ex Desktop, Edge atau Chrome)'],
    [/supaya browser tidak hang/g,'supaya tampilan tidak hang'],[/membekukan browser/g,'membekukan tampilan'],
    [/[Ii]zin (akses )?folder (dari |ditolak )?browser/g,'izin folder'],[/[Ii]zin browser/g,'Izin folder'],[/izin folder ditolak browser/g,'izin folder ditolak'],
    [/Browser meminta izin folder lagi/g,'GC-Ex meminta izin folder lagi'],[/Saat browser (meminta izin folder|bertanya)/g,'Saat diminta izin folder'],[/saat diminta browser/g,'saat diminta'],
    [/(di|ke|dari) browser ini/g,'$1 komputer ini'],[/\b(di|ke|dari) browser\b/g,'$1 komputer ini'],[/langsung di komputer ini/g,'langsung di GC-Ex']];
  var fix=function(t){if(!t||t.indexOf('rowser')<0&&t.indexOf('Edge /')<0)return t;var o=t;R.forEach(function(r){o=o.replace(r[0],r[1]);});return o;};
  window.GCTX={fix:fix};
  var walk=function(root){if(!root)return;if(root.nodeType===3){var v=root.nodeValue,n=fix(v);if(n!==v)root.nodeValue=n;return;}
    if(root.nodeType!==1||/^(SCRIPT|STYLE|TEXTAREA|INPUT)$/.test(root.nodeName))return;
    if(root.hasAttribute&&root.hasAttribute('title')){var tt=root.getAttribute('title'),tn=fix(tt);if(tn!==tt)root.setAttribute('title',tn);}
    if((root.textContent||'').indexOf('rowser')<0&&(root.textContent||'').indexOf('Edge /')<0&&!(root.querySelector&&root.querySelector('[title*=rowser]')))return;
    for(var c=root.firstChild;c;c=c.nextSibling)walk(c);};
  var start=function(){walk(document.body);new MutationObserver(function(ms){ms.forEach(function(m){if(m.type==='characterData')walk(m.target);else m.addedNodes.forEach(walk);});})
    .observe(document.body,{childList:true,subtree:true,characterData:true});};
  if(document.body)start();else document.addEventListener('DOMContentLoaded',start);
  /* kotak pesan & isian */
  ['alert','confirm','prompt'].forEach(function(k){var f=window[k];if(typeof f!=='function')return;window[k]=function(m){var a=Array.prototype.slice.call(arguments);if(a.length)a[0]=fix(String(m==null?'':m));return f.apply(window,a);};});
  /* petunjuk izin folder browser tidak relevan di desktop (izin folder sudah otomatis) */
  var st=document.createElement('style');st.textContent='#fpTip{display:none!important}';(document.head||document.documentElement).appendChild(st);
})();
