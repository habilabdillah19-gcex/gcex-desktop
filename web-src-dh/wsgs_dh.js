/* ================= VARIOGRAM WASTE DIFIT SENDIRI DI GEOSTATISTIK =================
   Sampai 0.24.20, blok waste memakai SALINAN variogram domain terdekat. Itu pinjaman: kontinuitas halo
   di luar solid tidak harus sama dengan kontinuitas bijih di dalamnya — biasanya nugget lebih besar,
   sill lebih kecil, dan range lebih panjang karena kadarnya rendah dan meratanya lebih luas.

   Modul ini membuka seluruh mesin Geostatistik yang sudah ada untuk populasi WASTE:
     - pilihan "WASTE (di luar semua domain)" pada bilah Domain di menu Geostatistik. Komposit yang
       dipakai hanya interval yang TIDAK di-flag domain apa pun — populasi yang sama dengan sampel
       estimasi waste, jadi variogram yang difit memang variogram populasi yang diestimasi;
     - seluruh alat ikut berlaku apa adanya: statistik, histogram, variogram arah & fan, fitting model,
       KNA, uji estimasi;
     - tombol "Simpan ke WASTE" di tab Uji estimasi menyimpan model variogram + elipsoid + pass +
       diskretisasi + top-cut + panjang komposit ke parameter waste (ME.store.ws.est), ikut tersimpan
       di proyek.

   Begitu variogram waste sendiri ada, estimasi waste memakainya untuk SELURUH blok waste (tanpa uji
   jarak ke domain), dan IDW hanya dipakai bila sampel di sekitar blok tidak cukup. Bila belum ada,
   perilaku lama berlaku: variogram domain terdekat, IDW bila jauh.                                   */
(function () {
  if (typeof GS === 'undefined' || typeof ME === 'undefined') return;

  function gE(s) { return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) { return '&#' + c.charCodeAt(0) + ';'; }); }

  /* ---------- populasi WASTE di Geostatistik ---------- */
  GS.wasteOnly = false;

  /* gsComps dibungkus: domOK hanya meloloskan interval yang tidak di-flag domain apa pun.
     Dipasang DI LUAR pembungkus dom20_dh.js, dan GS.domOnly dimatikan supaya filter domain tidak ikut. */
  if (typeof window.gsComps === 'function') {
    var _gc = window.gsComps;
    window.gsComps = function () {
      if (!GS.wasteOnly) return _gc.apply(this, arguments);
      var o = window.domOK;
      window.domOK = function (id, a) {
        if (!o(id, a)) return false;
        try { return gmCodeAt(id, (a[1] + a[2]) / 2) < 0; } catch (e) { return true; }
      };
      try { return _gc.apply(this, arguments); } finally { window.domOK = o; }
    };
  }

  window.gxWasteAct = function (on) {
    GS.wasteOnly = !!on;
    if (on) GS.domOnly = false;
    try { if (!GS.open) gsToggle(); else gsRun(); } catch (e) {}
    try { gsBar(); } catch (e) {}
    try { mePanel(); } catch (e) {}
  };

  /* bilah Domain: tambahkan pilihan WASTE, dan tandai saat populasi waste aktif */
  if (typeof window.gsBar === 'function') {
    var _gb = window.gsBar;
    window.gsBar = function () {
      var r = _gb.apply(this, arguments);
      try {
        var b = document.getElementById('gsDomBar'); if (!b) return r;
        var sel = b.querySelector('select');
        if (sel && !sel.querySelector('option[value="__waste"]')) {
          var op = document.createElement('option');
          op.value = '__waste'; op.text = 'WASTE (di luar semua domain)';
          sel.appendChild(op);
          sel.onchange = function () {
            if (this.value === '__waste') gxWasteAct(true);
            else { GS.wasteOnly = false; gxDomAct(this.value || null, 'gs'); }
          };
        }
        if (GS.wasteOnly) {
          if (sel) sel.value = '__waste';
          b.className = 'gsDomBar on';
          var sm = b.querySelector('small');
          if (sm) { sm.className = ''; sm.innerHTML = 'hanya sampel <b>di luar semua domain</b> &mdash; populasi waste'; }
        }
      } catch (e) { console.error(e); }
      return r;
    };
  }

  /* ---------- simpan hasil fitting ke parameter waste ---------- */
  window.wsFromGs = function () {
    var m = (typeof okModel === 'function') ? okModel() : null;
    if (!m) { alert('Jalankan analisis Geostatistik & fitting model dulu (tab Model).'); return false; }
    if (!GS.R) { alert('Belum ada hasil analisis Geostatistik.'); return false; }
    if (!GS.wasteOnly && !confirm('Populasi yang sedang dianalisis BUKAN waste (pilih "WASTE (di luar semua domain)" pada bilah Domain).\n\n' +
      'Variogram ini akan disimpan sebagai variogram waste walaupun difit dari populasi lain. Lanjutkan?')) return false;
    var P = (typeof okPasses === 'function') ? okPasses() : [];
    if (!P.length) P = [{ mult: 1, min: 6, max: 16, mph: 4 }, { mult: 1.5, min: 4, max: 16, mph: 4 }, { mult: 2.5, min: 2, max: 12, mph: 0 }];
    if (!ME.store) { ME.store = meNew(); ME.store.el = GS.R.el; }
    if (!ME.store.el) ME.store.el = GS.R.el;
    if (ME.store.el !== GS.R.el) {
      if (!confirm('Hasil estimasi tersimpan memakai unsur ' + ME.store.el + ', analisis ini memakai ' + GS.R.el + '.\n\nSimpan tetap? Estimasi waste akan menolak dijalankan sampai unsurnya sama.')) return false;
    }
    var o = wsPar();
    o.est = { el: GS.R.el, L: GS.R.L || 0, tc: GS.R.tc || 0, nd: (typeof okNd === 'function' ? okNd() : [3, 3, 2]),
              m: { vM: m.vM, vS: m.vS, vN: m.vN, c0: m.c0, cs: m.cs, A: m.A, B: m.B, Cn: m.Cn }, P: P, tr: m.tr || '',
              src: (GS.wasteOnly ? 'populasi WASTE' : 'populasi ' + (GS.R.label || 'lain')) + (GS.R.st ? ', n=' + GS.R.st.n : ''),
              date: new Date().toISOString().slice(0, 16).replace('T', ' '), n: GS.R.st ? GS.R.st.n : 0 };
    o.mode = 'auto';
    o.L = GS.R.L || o.L; o.tc = GS.R.tc || 0;
    if (SA.dirty) SA.dirty();
    try { mePanel(); } catch (e) {}
    return true;
  };

  window.wsClearGs = function () {
    if (!confirm('Hapus variogram waste hasil fitting?\n\nEstimasi waste akan kembali memakai variogram domain terdekat.')) return;
    var o = wsPar(); o.est = null;
    if (SA.dirty) SA.dirty();
    try { mePanel(); } catch (e) {}
    try { if (typeof gsTab === 'function') gsTab('E'); } catch (e) {}
  };

  /* kotak "Simpan ke WASTE" di tab Uji estimasi, di bawah "Simpan parameter ke domain" */
  if (typeof window.gsToDomHtml === 'function') {
    var _gt = window.gsToDomHtml;
    window.gsToDomHtml = function () {
      var h = _gt.apply(this, arguments), E = (typeof wsOwn === 'function') ? wsOwn() : null;
      h += '<div class=box style="margin-top:8px"><b>Simpan parameter ke WASTE</b>' +
        '<div class=note>Variogram untuk <b>material di luar seluruh solid</b>. Fit dari populasi <b>WASTE</b> (pilih pada bilah Domain di atas) supaya variogramnya ' +
        'memang variogram populasi yang diestimasi &mdash; kontinuitas halo tidak harus sama dengan kontinuitas bijih: biasanya nugget lebih besar, sill lebih kecil, range lebih panjang.</div>' +
        '<div class=g2><button class=btn-pri onclick="if(wsFromGs()){$(\'wsGsMsg\').innerHTML=\'&#10003; Tersimpan sebagai variogram waste. Lanjut di menu Model Estimation &rarr; Estimasi waste.\';}">&#8681; Simpan ke WASTE</button>' +
        (E ? '<button onclick="wsClearGs()">Hapus variogram waste</button>' : '<div></div>') + '</div>' +
        (E ? '<div class=note>Tersimpan: unsur <b>' + gE(E.el) + '</b> &middot; ' + gE(E.src || '') + ' &middot; ' + gE(E.date || '') + '</div>' : '') +
        '<div id=wsGsMsg class=note></div></div>';
      return h;
    };
  }
})();
