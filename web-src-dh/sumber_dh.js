/* ============ SUMBER SAMPEL ESTIMASI & DOMAIN WIREFRAME EKSAK (GC-Ex Drillhole 0.24.66) ============
   Temuan simulasi wireframe BMGC (pemilik 11-11-2026, "jika saya berikan wireframe yang sama ... apakah block model
   hasil estimasinya akan sama?"): log Surpac BMGC menjalankan BM FILL OK dengan data source constrain = "N".
   Artinya BLOK dibatasi wireframe, tetapi SAMPEL tidak: komposit di luar vein (waste) ikut menimbang kadar blok
   vein. GC-Ex selalu memakai sampel di dalam domain (hard boundary), sehingga kadarnya lebih tinggi walau
   wireframenya sama persis.
   1. Parameter domain `est.sAll`: "Sampel yang dipakai" = hanya di dalam domain (bawaan, hard boundary) atau
      SEMUA sampel database (seperti Surpac BM FILL dengan data tidak dibatasi constraint). Blok tetap hanya di
      dalam solid / wireframe domain. Mengubahnya = domain diestimasi ulang (hash parameter berubah).
   2. Mengunci domain ke wireframe impor (mode eksak, wfx_dh.js) sekarang langsung siap estimasi: interval bor di
      dalam wireframe di-flag otomatis bila domain belum punya flag, dan solid domain dianggap aktif.          */
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
  window.meComps = meComps = function (d, P) {
    if (!(P && P.sAll)) return _mc.apply(this, arguments);
    var _r = window.meRuns; window.meRuns = meRuns = function () { return SUMBER.runsAll(); };
    try { return _mc.apply(this, arguments); } finally { window.meRuns = meRuns = _r; }
  };
  SUMBER.set = function (id, v) {
    var d = typeof gmDom === 'function' ? gmDom(id) : null; if (!d || !d.est) return;
    if (v === 'all') d.est.sAll = true; else delete d.est.sAll;
    try { gmDirty(true); } catch (e) {} try { mePanel(); } catch (e) {}
  };
  if (typeof window.meParHtml === 'function') {
    var _ph = window.meParHtml;
    window.meParHtml = meParHtml = function (id) {
      var h = _ph.apply(this, arguments), d = typeof gmDom === 'function' ? gmDom(id) : null; if (!d || !d.est) return h;
      var all = !!d.est.sAll;
      var box = '<div class=box style="margin:6px 0"><b>Sampel yang dipakai</b>' +
        '<select style="width:100%;margin-top:3px" onchange="SUMBER.set(\'' + id + '\',this.value)">' +
        '<option value="dom"' + (all ? '' : ' selected') + '>Hanya sampel di dalam domain (hard boundary, bawaan GC-Ex)</option>' +
        '<option value="all"' + (all ? ' selected' : '') + '>Semua sampel database (seperti Surpac: data tidak dibatasi constraint)</option></select>' +
        '<div class=hint>' + (all ? '<span class=warn>Sampel di luar domain (termasuk waste) ikut menimbang kadar blok.</span> Blok tetap hanya di dalam solid / wireframe domain. Pilihan ini meniru BMGC Surpac yang menjalankan <i>BM FILL OK</i> dengan data source <i>constrain = N</i>; biasanya menurunkan kadar dan menaikkan tonase di cut-off rendah.'
          : 'Hanya interval yang di-flag domain ini. Pilih &quot;Semua sampel&quot; untuk meniru block model Surpac yang dibuat dengan data tidak dibatasi constraint.') + '</div></div>';
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
