/* ---------- SET PLAN BOR (Drillhole 0.24.44) ----------
   Permintaan pemilik 8 Nov 2026: plan bor yang dibuat setiap hari (di tempat berbeda, atau extend di
   lokasi yang sama) muncul BERURUTAN sebagai sub-node Project Tree di bawah "Plan bor (rencana)".

   Rancangan:
   - PL.sets = [{id, name, date, bench, vis, h:[titik...]}], urut sesuai waktu dibuat; PL.act = id set aktif.
   - PL.h SELALU menunjuk ke array titik set aktif. Seluruh alat lama (titik / garis / grid, impor CSV,
     edit tabel, nomori ulang, export) bekerja pada PL.h, jadi otomatis bekerja pada set aktif =
     "extend di set ini". Bila fungsi lama mengganti PL.h dengan array baru (plClear, applyWork), array itu
     dipasang kembali ke set aktif di plRefresh.
   - "+ Tambah plan bor…" (baris di Project Tree) membuat set kosong yang langsung aktif; titik berikutnya masuk ke sana.
   - Data lama (sebelum fitur ini) masuk ke satu set "Plan lama" -- tidak ada titik yang hilang.
   - Tiap set punya centang tampil; set aktif digambar magenta tegas, set lain lebih pudar.        */
(function () {
  if (window.PLS || typeof PL === 'undefined' || typeof plRefresh !== 'function') return;
  var PLS = window.PLS = {};
  var $ = function (i) { return document.getElementById(i); };
  var esc = function (s) { return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; }); };
  var tgl = function (d) { d = d || new Date(); var p = function (n) { return (n < 10 ? '0' : '') + n; }; return p(d.getDate()) + '-' + p(d.getMonth() + 1) + '-' + d.getFullYear(); };
  var baru = function (name, h) { return { id: 'pls_' + Date.now().toString(36) + Math.random().toString(36).slice(2, 5), name: name, date: new Date().toISOString(), bench: ($('plBench') || {}).value || '', vis: true, h: h || [] }; };
  var KEY = function () { return plKey() + '_sets'; };

  function cur() { var s = null; (PL.sets || []).forEach(function (x) { if (x.id === PL.act) s = x; }); return s; }
  /* pastikan selalu ada set aktif dan PL.h = titik set aktif */
  function rapikan() {
    if (!PL.sets || !PL.sets.length) { PL.sets = [baru(PL.h && PL.h.length ? 'Plan lama' : namaBawaan(), PL.h || [])]; if (PL.h && PL.h.length) PL.sets[0].date = ''; }
    if (!cur()) PL.act = PL.sets[PL.sets.length - 1].id;
    var c = cur(); if (PL.h !== c.h) { if (PL.h && PL.h !== c.h && PL._hDari === PL.act) c.h = PL.h; PL.h = c.h; }
    PL._hDari = PL.act;
  }
  PLS.cur = cur;

  function simpan() { try { localStorage.setItem(KEY(), JSON.stringify({ sets: PL.sets, act: PL.act })); } catch (e) {} if (window.SA && SA.dirty) SA.dirty(); }
  function muat() {
    try {
      var o = JSON.parse(localStorage.getItem(KEY()) || 'null');
      if (o && o.sets && o.sets.length) { PL.sets = o.sets; PL.act = o.act; var c = cur() || PL.sets[PL.sets.length - 1]; PL.act = c.id; PL.h = c.h; PL._hDari = PL.act; return; }
    } catch (e) {}
    PL.sets = null; rapikan();
  }

  /* ---------- perintah ---------- */
  /* nama bawaan: "Plan <tanggal> · <bench>"; plan kedua di hari & bench yang sama diberi #2, #3, ... */
  function namaBawaan() {
    var b = ($('plBench') || {}).value || '', d = 'Plan ' + tgl() + (b ? ' \u00b7 ' + b : ''), nm = d, k = 1;
    var ada = function (n) { return (PL.sets || []).some(function (s) { return s.name === n; }); };
    while (ada(nm)) nm = d + ' #' + (++k);
    return nm;
  }
  PLS.buat = function (nm) { rapikan(); var s = baru(String(nm || '').trim() || namaBawaan()); PL.sets.push(s); PL.act = s.id; PL.h = s.h; PL._hDari = s.id; plRefresh(); return s; };
  PLS.baru = function () {
    rapikan(); var def = namaBawaan();
    var nm = prompt('Nama plan bor baru (titik berikutnya masuk ke plan ini):', def); if (nm === null) return;
    PLS.buat(String(nm).trim() || def);
  };
  PLS.aktif = function (id) { var s = null; PL.sets.forEach(function (x) { if (x.id === id) s = x; }); if (!s) return; rapikan(); PL.act = id; PL.h = s.h; PL._hDari = id; s.vis = true; plRefresh(); };
  PLS.nama = function (id) { var s = null; PL.sets.forEach(function (x) { if (x.id === id) s = x; }); if (!s) return; var nm = prompt('Nama plan bor:', s.name); if (nm === null) return; s.name = String(nm).trim() || s.name; plRefresh(true); };
  PLS.tampil = function (id, v) { PL.sets.forEach(function (x) { if (x.id === id) x.vis = !!v; }); simpan(); try { updatePlot(); } catch (e) {} try { if (DRW.on) drawRender(); } catch (e) {} };
  PLS.hapus = function (id) {
    var i = -1; PL.sets.forEach(function (x, k) { if (x.id === id) i = k; }); if (i < 0) return; var s = PL.sets[i];
    if (!confirm('Hapus plan "' + s.name + '" beserta ' + s.h.length + ' titiknya?')) return;
    PL.sets.splice(i, 1); if (PL.act === id) PL.act = null; if (!PL.sets.length) PL.sets = null; PL.h = []; PL._hDari = null; rapikan(); plRefresh();
  };
  function baris(h) {
    var Q = String.fromCharCode(34), rd = ($('plRound') || {}).checked, q = function (s) { s = String(s || ''); return /[,\n]/.test(s) || s.indexOf(Q) >= 0 ? Q + s.split(Q).join(Q + Q) + Q : s; };
    return [q(h.n), plF(h.x + offX, 4), plF(h.y + offY, 4), rd ? Math.round(h.z) : plF(h.z, 2), plF(h.az, 2), plF(h.dip, 2), plF(h.lift, 3), plF(h.drift, 3), plF(h.dist, 2), plF(h.ext, 2), plF(h.td, 2), q(h.cm)].join(',');
  }
  var HDR = 'Drillhole Name,Easting,Northing,Elevation,Azimuth,Dip,Lift Rate,Drift Rate,Distance,Extension,Target Depth,Comment';
  var slug = function (s) { return String(s || 'plan').replace(/[^A-Za-z0-9_-]+/g, '_').replace(/^_+|_+$/g, '') || 'plan'; };
  PLS.export = function (id) {
    var s = null; PL.sets.forEach(function (x) { if (x.id === id) s = x; }); if (!s) return; if (!s.h.length) { alert('Plan "' + s.name + '" belum punya titik.'); return; }
    gxSimpan(new Blob([[HDR].concat(s.h.map(baris)).join('\r\n') + '\r\n'], { type: 'text/csv' }), 'Plan_Bor_' + ZONE + '_' + slug(s.name) + '.csv');
  };
  PLS.exportSemua = function () {
    var L = []; PL.sets.forEach(function (s) { s.h.forEach(function (h) { L.push(baris(h)); }); }); if (!L.length) { alert('Belum ada titik rencana.'); return; }
    gxSimpan(new Blob([[HDR].concat(L).join('\r\n') + '\r\n'], { type: 'text/csv' }), 'Plan_Bor_' + ZONE + '_semua_plan.csv');
  };

  /* ---------- export plan aktif: nama berkas mengikuti nama plan ---------- */
  window.plExport = plExport = function () { rapikan(); PLS.export(PL.act); };

  /* ---------- kotak "Plan aktif" di atas panel Plan Bor ---------- */
  function kotak() {
    var sec = $('pPlan'); if (!sec) return; var b = $('plSetBox');
    if (!b) { b = document.createElement('div'); b.id = 'plSetBox'; b.className = 'box'; b.style.cssText = 'font-size:12px;margin-bottom:8px'; var h3 = sec.querySelector('h3'); sec.insertBefore(b, h3 ? h3.nextSibling : sec.firstChild); }
    var c = cur(), tot = 0; PL.sets.forEach(function (s) { tot += s.h.length; });
    b.innerHTML = '<label>Plan aktif (titik baru masuk ke sini)</label><select id=plSetSel style="width:100%" onchange="PLS.aktif(this.value)">' +
      PL.sets.map(function (s, i) { return '<option value="' + s.id + '"' + (s.id === PL.act ? ' selected' : '') + '>' + (i + 1) + '. ' + esc(s.name) + ' (' + s.h.length + ')</option>'; }).join('') +
      '</select>' +
      '<div class=hint style="margin-top:4px">' + PL.sets.length + ' plan &middot; ' + tot + ' titik. Untuk <b>extend</b> di lokasi yang sama, pilih plan-nya di atas lalu tambah titik; untuk plan hari lain, klik <b>+ Tambah plan bor&hellip;</b> di Project Tree (baris terbawah di bawah <b>Plan bor (rencana)</b>). Setiap plan muncul berurutan di sana.</div>';
  }

  /* ---------- sambungan ke fungsi lama ---------- */
  var _r = plRefresh;
  window.plRefresh = plRefresh = function (noPlot) { rapikan(); var r = _r.apply(this, arguments); simpan(); try { kotak(); } catch (e) {} try { if (window.PT && PT.render) PT.render(); } catch (e) {} return r; };

  /* 3D: semua plan yang dicentang; plan aktif tegas, plan lain pudar */
  window.planTraces = planTraces = function (T, o) {
    if (!$('plShow') || !$('plShow').checked) return; rapikan();
    PL.sets.forEach(function (s) {
      if (!s.vis || !s.h.length) return; var akt = s.id === PL.act, col = akt ? '#d6249f' : '#b77fa8', X = [], Y = [], Z = [], cx = [], cy = [], cz = [], ct = [], ht = [], n = 0;
      s.h.forEach(function (h) {
        var a = { x: h.x, y: h.y, z: h.z }, b = plEnd(h), g = [a, b]; if (o.clip) { g = clipSeg(a, b, o.K); if (!g) return; }
        X.push(g[0].x, g[1].x, null); Y.push(g[0].y, g[1].y, null); Z.push(g[0].z, g[1].z, null); n++;
        if (!o.clip || inK(o.K, a)) { cx.push(a.x); cy.push(a.y); cz.push(a.z); ct.push(h.n); ht.push('<b>' + esc(h.n) + '</b> (' + esc(s.name) + ')<br>E ' + (h.x + offX).toFixed(2) + ' N ' + (h.y + offY).toFixed(2) + ' RL ' + h.z.toFixed(1) + '<br>Az ' + h.az + '° Dip ' + h.dip + '° Depth ' + h.td + ' m'); }
      });
      if (!n) return;
      T.push({ type: 'scatter3d', mode: 'lines', x: X, y: Y, z: Z, name: s.name + ' (' + s.h.length + ')' + (akt ? ' ← aktif' : ''), line: { color: col, width: akt ? 7 : 4, dash: 'dash' }, opacity: akt ? 1 : 0.7, hoverinfo: 'skip', showlegend: true });
      if (cx.length) T.push({ type: 'scatter3d', mode: akt && ct.length <= 80 ? 'markers+text' : 'markers', x: cx, y: cy, z: cz, text: ct, textposition: 'top center', textfont: { color: col, size: 11 },
        marker: { color: col, size: akt ? 5 : 4, symbol: 'diamond' }, hovertext: ht, hoverinfo: 'text', showlegend: false });
    });
  };
  /* peta plan (2D): plan lain digambar tipis di bawah plan aktif yang sedang diedit */
  var _d = planDraw;
  window.planDraw = planDraw = function (x, dk) {
    rapikan();
    try {
      x.save(); x.globalAlpha = 0.45; x.strokeStyle = '#b77fa8'; x.fillStyle = '#b77fa8'; x.lineWidth = 1.5;
      PL.sets.forEach(function (s) { if (s.id === PL.act || !s.vis) return; s.h.forEach(function (h) { var e = plEnd(h), p = w2s(h.x, h.y), q = w2s(e.x, e.y); x.beginPath(); x.moveTo(p[0], p[1]); x.lineTo(q[0], q[1]); x.stroke(); x.beginPath(); x.arc(p[0], p[1], 3.5, 0, 7); x.fill(); }); });
      x.restore();
    } catch (e) {}
    return _d.apply(this, arguments);
  };

  /* proyek: simpan & buka */
  var _c = SA.collectWork;
  SA.collectWork = function () { var w = _c.apply(this, arguments); try { rapikan(); if (w.plan) { w.plan.sets = PL.sets; w.plan.act = PL.act; } } catch (e) {} return w; };
  var _a = SA.applyWork;
  SA.applyWork = function (W) {
    var r = _a.apply(this, arguments);
    try {
      if (W && W.plan) {
        if (W.plan.sets && W.plan.sets.length) { PL.sets = W.plan.sets; PL.act = W.plan.act; var c = cur() || PL.sets[PL.sets.length - 1]; PL.act = c.id; PL.h = c.h; PL._hDari = c.id; }
        else { PL.sets = null; PL._hDari = null; rapikan(); }
        plRefresh(true);
      }
    } catch (e) { console.error(e); }
    return r;
  };

  /* ---------- sub-node Project Tree ---------- */
  PLS.kids = function () {
    rapikan();
    return PL.sets.map(function (s, i) {
      var tg = s.date ? tgl(new Date(s.date)) : '';
      return {
        id: 'db.plan.' + s.id, t: (i + 1) + '. ' + s.name, ic: 'plan', tab: 'Plan', mark: s.id === PL.act ? 'aktif' : '',
        b: s.h.length + ' titik', chk: !!s.vis, onChk: function (v) { PLS.tampil(s.id, v); },
        hint: (tg ? 'Dibuat ' + tg + ' · ' : '') + (s.bench ? 'bench ' + s.bench + ' · ' : '') + s.h.length + ' titik. Klik = jadikan plan aktif (titik baru masuk ke sini).',
        go: function () { if (PL.act !== s.id) PLS.aktif(s.id); },
        menu: function () {
          return [{ t: 'Jadikan plan aktif (extend di sini)', dis: s.id === PL.act, fn: function () { PLS.aktif(s.id); } },
            { t: 'Ganti nama…', fn: function () { PLS.nama(s.id); } },
            { t: 'Export CSV plan ini…', dis: !s.h.length, fn: function () { PLS.export(s.id); } },
            { sep: 1 }, { t: 'Hapus plan ini…', danger: 1, fn: function () { PLS.hapus(s.id); } }];
        }
      };
    });
  };

  muat(); try { _r(true); } catch (e) {} simpan(); try { kotak(); } catch (e) {}
})();
