/* ============ ORTHOFOTO RESOLUSI TINGGI DI PENAMPANG 2D & FLITCH (GC-Ex Block Model) ============
   Masalah yang diperbaiki.
   Latar orthofoto di Penampang 2D horizontal (plan) -- termasuk tampilan FLITCH, karena flitch
   adalah plan 2D -- dibuat oleh orthoImg2D(): satu JPEG seukuran ortho penuh, dibuat sekali lalu
   DI-CACHE di ORT.url selamanya. Akibatnya:
     - resolusinya tetap. Ortho dibatasi 2,5 juta piksel saat import, jadi area 1,5 km hanya punya
       ~1 m/piksel; di flitch sempit (mis. 50 x 50 m) gambarnya buram dan zoom tidak menolong.
     - piramida LOD di hires.js (HR.mapImage, sampai 4096 px dan dipotong sesuai tampilan) SUDAH ADA
       di Block Model tetapi tidak pernah dipanggil dari jalur 2D -- hanya dipakai Peta Drill Hole.
     - HR.extW (bentang dunia tampilan) tidak pernah terisi di Block Model: HR.attach memasang
       pemantau zoom dengan world=false untuk grafik utama, dan world=true hanya untuk Peta, yang
       tidak ada di Block Model. Tanpa HR.extW, HR.mapImage tidak tahu harus memotong di mana.

   Yang dikerjakan modul ini.
     1. orthoImg2D() memakai HR.mapImage() lebih dulu; bila tidak tersedia, kembali ke JPEG lama.
        Jadi tidak ada jalur yang hilang -- hanya ditambah yang lebih tajam.
     2. Memasang pemantau zoom/geser sendiri di plot 2D. Saat tampilan sedang 2D PLAN, sumbu x/y
        adalah Easting/Northing, jadi bentangnya diteruskan sebagai bentang DUNIA (HR.setExt world
        = true) dan HR.ext (bentang lokal untuk mesh 3D) dikosongkan supaya jalur 3D tidak tercemar.
        Sesudah itu gambar disusun ulang (ditunda sesaat) sehingga zoom masuk benar-benar makin tajam.
     3. Node "Orthofoto (latar plan / flitch)" di bawah Flitch Aktif: nyala/mati dan opasitas tanpa
        harus pergi ke menu Overlay.                                                                */
(function () {
  if (window.ORT2D) return;
  var O2 = window.ORT2D = { ver: 0, tmr: null };
  var $ = function (i) { return document.getElementById(i); };

  function adaOrtho() { return !!(window.ORT && ORT.m && ORT.px); }
  function opasitas() { var e = $('orOp'); return +((e && e.value) || 1); }
  function plan2D() {
    if (!window.VIEW2D) return false;
    try { return (typeof secGeom === 'function') && secGeom().m === 'H'; } catch (e) { return false; }
  }
  O2.plan2D = plan2D;

  /* ---------- 1. latar 2D memakai piramida LOD ---------- */
  var _lama = window.orthoImg2D;
  window.orthoImg2D = function () {
    try {
      if (window.HR && HR.on && HR.mapImage && adaOrtho()) {
        var i = HR.mapImage();
        if (i && i.src) {
          O2.px = i.px; O2.res = i.res;
          return { source: i.src, xref: 'x', yref: 'y', x: i.x, y: i.y, sizex: i.sx, sizey: i.sy,
                   xanchor: 'left', yanchor: 'top', sizing: 'stretch', layer: 'below', opacity: opasitas() };
        }
      }
    } catch (e) { console.error(e); }
    O2.px = null; O2.res = null;
    return _lama ? _lama.apply(this, arguments) : null;
  };

  /* ---------- 2. pantau zoom / geser pada plot 2D ---------- */
  function susunUlang() {
    O2.tmr = null;
    try { if (window.OVC) window.OVC = {}; if (window.updatePlot) updatePlot(); } catch (e) {}
  }
  function tunda() { if (O2.tmr) clearTimeout(O2.tmr); O2.tmr = setTimeout(susunUlang, 280); }

  function dariRelayout(ev) {
    if (!ev || !window.HR || !HR.on || !adaOrtho() || !plan2D()) return;
    var ax = ev['xaxis.range'] || (ev['xaxis.range[0]'] !== undefined ? [ev['xaxis.range[0]'], ev['xaxis.range[1]']] : null);
    var ay = ev['yaxis.range'] || (ev['yaxis.range[0]'] !== undefined ? [ev['yaxis.range[0]'], ev['yaxis.range[1]']] : null);
    if (ax && ay) {
      try {
        HR.setExt(+ax[0], +ax[1], +ay[0], +ay[1], true);   /* bentang DUNIA: sumbu plan = E / N */
        HR.ext = null;                                      /* jangan cemari jalur mesh 3D */
        O2.ver++;
      } catch (e) { return; }
      tunda();
      return;
    }
    if (ev['xaxis.autorange'] || ev['yaxis.autorange'] || ev.autosize) {
      try { HR.extW = null; HR.ext = null; HR.ver++; } catch (e) {}
      tunda();
    }
  }
  O2.dariRelayout = dariRelayout;

  var t = setInterval(function () {
    try {
      var gd = $('plotDiv') || document.querySelector('.js-plotly-plot');
      if (gd && gd.on && !gd._ort2d) {
        gd._ort2d = 1;
        gd.on('plotly_relayout', dariRelayout);
      }
    } catch (e) {}
  }, 1200);
  setTimeout(function () { clearInterval(t); }, 180000);

  /* ---------- 3. node Project Tree di bawah Flitch Aktif ---------- */
  window.ortFlTree = function () {
    if (!adaOrtho()) return [];
    var cb = $('ovOrtho'), on = !!(cb && cb.checked);
    var lod = O2.px ? ('LOD ' + O2.px + ' px @ ' + (O2.res ? O2.res.toFixed(2) + ' m/px' : '-')) : '';
    return [{
      id: 'fl.ortho', t: 'Orthofoto (latar plan / flitch)', ic: 'ortho', tab: 'Overlay',
      chk: on, onChk: function (v) {
        var c = $('ovOrtho'); if (!c) return;
        c.checked = !!v;
        try { if (typeof updatePlot === 'function') updatePlot(); } catch (e) {}
        try { if (window.PT && PT.render) PT.render(true); } catch (e) {}
      },
      b: on ? (plan2D() ? (lod || 'tampil') : 'hanya di plan 2D') : '',
      dim: !on,
      hint: on ? (plan2D() ? 'Dipotong sesuai tampilan dari piramida resolusi tinggi — zoom masuk makin tajam'
                           : 'Menyala, tetapi latar ini hanya digambar pada Penampang 2D horizontal (plan / flitch)')
               : 'Orthofoto sebagai gambar latar di bawah blok dan dig block',
      menu: function () {
        var M = [{ t: on ? 'Sembunyikan orthofoto' : 'Tampilkan orthofoto', fn: function () { ortFlTree()[0].onChk(!on); } },
                 { sep: 1 }, { h: 'Opasitas' }];
        [100, 75, 50, 25].forEach(function (p) {
          M.push({ t: p + '%', on: Math.round(opasitas() * 100) === p, fn: function () {
            var e = $('orOp'); if (!e) return;
            e.value = p / 100;
            try { if (typeof updatePlot === 'function') updatePlot(); } catch (e2) {}
            try { if (window.PT && PT.render) PT.render(true); } catch (e2) {}
          } });
        });
        M.push({ sep: 1 }, { h: 'Resolusi' },
               { t: O2.px ? ('Sekarang: ' + O2.px + ' px' + (O2.res ? ' (' + O2.res.toFixed(2) + ' m/piksel)' : '')) : 'Belum digambar di plan 2D', dis: 1 },
               { t: 'Makin dekat zoom, makin tajam (dipotong sesuai tampilan)', dis: 1 });
        return M;
      }
    }];
  };
})();
