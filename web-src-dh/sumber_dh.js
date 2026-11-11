/* ============ SUMBER SAMPEL ESTIMASI & DOMAIN WIREFRAME EKSAK (GC-Ex Drillhole 0.24.66 / 0.24.68) ============
   Temuan simulasi wireframe BMGC (pemilik 11-11-2026): log Surpac BMGC menjalankan BM FILL OK dengan data source
   constrain = "N": BLOK dibatasi wireframe, SAMPEL tidak; komposit di luar vein ikut menimbang kadar blok vein.
   0.24.66 menambah pilihan per domain (hanya sampel domain / semua sampel).
   0.24.68 (pemilik 11-11-2026: "Harus sama persis seperti Surpac"): bawaan = semua sampel database, seperti Surpac.
   0.24.69 (pemilik 11-11-2026: "pilihan hard boundary dan soft boundary jangan dihilangkan"): pilihan per domain
   kembali: SOFT boundary = semua sampel (bawaan, seperti Surpac) atau HARD boundary = hanya sampel domain (est.hard).
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
    if (!SUMBER.on || (P && P.hard)) return _mc.apply(this, arguments);
    var _r = window.meRuns; window.meRuns = meRuns = function () { return SUMBER.runsAll(); };
    try { return _mc.apply(this, arguments); } finally { window.meRuns = meRuns = _r; }
  };
  if (typeof window.meRun === 'function') {
    var _run = window.meRun;
    window.meRun = meRun = function () { SUMBER.on = true; try { return _run.apply(this, arguments); } finally { SUMBER.on = false; } };
  }
  /* parameter 0.24.66 (sAll) tidak dipakai lagi: soft boundary (semua sampel) adalah bawaan; est.hard = hard boundary */
  SUMBER.set = function (id, v) {
    var d = typeof gmDom === 'function' ? gmDom(id) : null; if (!d || !d.est) return;
    if (v === 'hard') d.est.hard = true; else delete d.est.hard; delete d.est.sAll;
    try { gmDirty(true); } catch (e) {} try { mePanel(); } catch (e) {}
  };
  if (typeof window.meParHtml === 'function') {
    var _ph = window.meParHtml;
    window.meParHtml = meParHtml = function (id) {
      var h = _ph.apply(this, arguments), d = typeof gmDom === 'function' ? gmDom(id) : null; if (!d || !d.est) return h;
      var hard = !!d.est.hard;
      var box = '<div class=box style="margin:6px 0"><b>Batas sampel</b>' +
        '<select style="width:100%;margin-top:3px" onchange="SUMBER.set(\'' + id + '\',this.value)">' +
        '<option value="soft"' + (hard ? '' : ' selected') + '>Soft boundary: semua sampel database (seperti Surpac, bawaan)</option>' +
        '<option value="hard"' + (hard ? ' selected' : '') + '>Hard boundary: hanya sampel di dalam domain</option></select>' +
        '<div class=hint>' + (hard ? 'Hanya interval yang di-flag domain ini yang menimbang kadar blok.'
          : 'Sama dengan Surpac <i>BM FILL</i> (data source <i>constrain = N</i>): semua komposit di database, termasuk lubang eksplorasi yang digabung lewat <b>Database &rsaquo; Tambah / perbarui beberapa tabel sekaligus (upsert)</b>, ikut menimbang kadar blok.') +
        ' Blok selalu hanya di dalam solid / wireframe domain. Mengubah pilihan = domain diestimasi ulang.</div></div>';
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
