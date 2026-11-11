/* ============ SUMBER SAMPEL ESTIMASI & DOMAIN WIREFRAME EKSAK (GC-Ex Drillhole 0.24.66 / 0.24.68) ============
   Temuan simulasi wireframe BMGC (pemilik 11-11-2026): log Surpac BMGC menjalankan BM FILL OK dengan data source
   constrain = "N": BLOK dibatasi wireframe, SAMPEL tidak; komposit di luar vein ikut menimbang kadar blok vein.
   0.24.66 menambah pilihan per domain (hanya sampel domain / semua sampel).
   0.24.68 (keputusan pemilik 11-11-2026: "Harus sama persis seperti Surpac. Hilangkan opsi lain selain itu."):
   Model Estimation SELALU memakai semua sampel database, seperti Surpac; pilihan hard boundary dihapus.
   Blok tetap hanya di dalam solid / wireframe domain. Lubang eksplorasi digabung lewat menu upsert database.
   Mengunci domain ke wireframe impor (mode eksak, wfx_dh.js) langsung siap estimasi: interval bor di dalam
   wireframe di-flag otomatis bila domain belum punya flag, dan solid domain dianggap aktif.                 */
(function () {
  if (window.SUMBER || typeof window.meComps !== 'function') return;
  var SUMBER = window.SUMBER = {};
  function E(s) { return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; }); }

  /* ---------- 1. semua sampel database sebagai komposit domain ---------- */
  SUMBER.runsAll = function () {
    var R = {};
    (window.collars || []).forEach(function (c) { var id = c[0], h = window.holeData && holeData[id]; if (h && h.maxD > 0) R[id] = [[0, h.maxD]]; });
    return R;
  };
  var _mc = window.meComps;
  /* hanya saat Model Estimation menjalankan estimasi; validasi & statistik domain tetap memakai komposit domain */
  window.meComps = meComps = function (d, P) {
    if (!SUMBER.on) return _mc.apply(this, arguments);
    var _r = window.meRuns; window.meRuns = meRuns = function () { return SUMBER.runsAll(); };
    try { return _mc.apply(this, arguments); } finally { window.meRuns = meRuns = _r; }
  };
  if (typeof window.meRun === 'function') {
    var _run = window.meRun;
    window.meRun = meRun = function () { SUMBER.on = true; try { return _run.apply(this, arguments); } finally { SUMBER.on = false; } };
  }
  /* parameter lama (0.24.66) masih bisa membawa sAll; tidak berpengaruh lagi -- semua domain memakai semua sampel */
  if (typeof window.meParHtml === 'function') {
    var _ph = window.meParHtml;
    window.meParHtml = meParHtml = function (id) {
      var h = _ph.apply(this, arguments), d = typeof gmDom === 'function' ? gmDom(id) : null; if (!d || !d.est) return h;
      var box = '<div class=box style="margin:6px 0"><b>Sampel yang dipakai: semua sampel database</b>' +
        '<div class=hint>Sama dengan Surpac <i>BM FILL</i> (data source <i>constrain = N</i>): semua komposit di database, termasuk lubang eksplorasi yang digabung lewat <b>Database &rsaquo; Tambah / perbarui beberapa tabel sekaligus (upsert)</b>, ikut menimbang kadar blok. Blok tetap hanya di dalam solid / wireframe domain.</div></div>';
      var at = h.indexOf('<div class="g3 f"><div><label>Unsur</label>');
      return at >= 0 ? h.slice(0, at) + box + h.slice(at) : h + box;
    };
  }

  /* ---------- 2. domain dikunci ke wireframe: flag otomatis + siap estimasi ---------- */
  if (typeof window.wfxPakai === 'function') {
    var _wp = window.wfxPakai;
    window.wfxPakai = function (domId, nama) {
      var r = _wp.apply(this, arguments);
      try {
        var d = gmDom(domId); if (!d || d.wfx !== nama) return r;
        d.im = Object.assign(imPar(d), { on: true });
        var R = typeof meRuns === 'function' ? meRuns(d.id) : {};
        if (!Object.keys(R).length && typeof gmWfFlag === 'function') {
          var mi = -1; (MD.models || []).forEach(function (m, i) { if (m.name === nama) mi = i; });
          if (mi >= 0) { window.WF = window.WF || {}; var sv = { mi: WF.mi, dom: WF.dom, sp: WF.sp, keep: WF.keep }; WF.mi = mi; WF.dom = d.id; WF.sp = 0; WF.keep = true;
            try { gmWfFlag(); } finally { WF.mi = sv.mi; WF.dom = sv.dom; WF.sp = sv.sp; WF.keep = sv.keep; } }
        }
        gmDirty(true);
      } catch (e) { console.error(e); }
      return r;
    };
  }
})();
