/* ================= GC-Ex: tipografi grafik seragam (font UI sistem) =================
   Teks Plotly (sumbu, legenda, label) memakai font UI sistem yang sama dengan menu, warna charcoal / terang. */
(function(){if(!window.Plotly)return;var F="'Segoe UI',Tahoma,Arial,sans-serif";
  var fix=function(L){if(!L||typeof L!=='object')return L;L.font=L.font||{};if(!L.font.family)L.font.family=F;return L;};
  ['newPlot','react'].forEach(function(k){var f=Plotly[k];if(typeof f!=='function'||f._gcFont)return;var g=function(gd,d,L,c){if(L&&typeof L==='object')fix(L);else if(d&&typeof d==='object'&&!Array.isArray(d)&&d.layout)fix(d.layout);return f.apply(this,arguments);};g._gcFont=1;Plotly[k]=g;});})();
