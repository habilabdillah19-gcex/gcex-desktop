/* a37: Pit Studio Desktop (Electron, keluarga GC-Ex). Di browser biasa berkas ini tidak berpengaruh.
   - prompt() / alert() / confirm() lewat jendela milik aplikasi (Electron tidak menyediakan prompt()).
   - File yang dijatuhkan di luar kotak unggah tidak menggantikan halaman aplikasi.
   - Block model .mdl besar dibaca lewat backend GC-Ex (a36_gt.js gtEnsure: /mdl/open + /mdl/subset). */
(function(){var D=window.gcexDesktop;if(!D)return;
  if(typeof D.prompt==='function'){try{window.prompt=function(m,d){var r=D.prompt(m==null?'':String(m),d==null?'':String(d));return r==null?null:String(r);};}catch(e){}}
  if(typeof D.alert==='function'){try{window.alert=function(m){D.alert(m==null?'':String(m));};}catch(e){}}
  if(typeof D.confirm==='function'){try{window.confirm=function(m){return D.confirm(m==null?'':String(m))===true;};}catch(e){}}
  var isF=function(e){try{return Array.prototype.indexOf.call((e.dataTransfer&&e.dataTransfer.types)||[],'Files')>=0;}catch(x){return false;}};
  document.addEventListener('dragover',function(e){if(isF(e))e.preventDefault();});
  document.addEventListener('drop',function(e){if(isF(e)&&!e.defaultPrevented)e.preventDefault();});
  document.body.classList.add('desktop');})();
/* cap versi di bilah status */
try{var _v=window.GCEX_VER,_sb=document.querySelector('.cpy');if(_v&&_sb&&_sb.textContent.indexOf(_v)<0)_sb.textContent=_sb.textContent.replace('Pit Studio ·','Pit Studio '+_v+' ·');}catch(e){}
