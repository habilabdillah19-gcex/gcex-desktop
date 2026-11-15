/* ================= Drillhole 0.24.98: Ringkasan seluruh model per RL (web-src/mdlsum.js) di Drillhole =================
   Pemilik 16 Nov 2026: penanganan .mdl sangat besar dari Block Model juga untuk Drillhole. mdlsum.js memakai beberapa
   fungsi Block Model; di Drillhole disediakan padanannya di sini (tanpa mengubah perilaku Drillhole lain):
   - lyBench(): bench bawaan = tinggi blok terbanyak, acuan = RL dasar model (bisa diubah di dialog);
   - lyFmt(): format angka RL;
   - SG: kolom SG bila dipilih di Block Model > Filter & SG, nilai <= 0 / kosong = SG tetap (sama dengan Statistik DH). */
(function () {
  if (typeof window.lyFmt !== 'function') window.lyFmt = function (v) { return String(+(+v).toFixed(2)); };
  if (typeof window.lyBench !== 'function') window.lyBench = function () {
    var m = window.BX && BX.m; if (!m || !m.n) return [1.5, 0];
    var C = {}, st = Math.max(1, Math.floor(m.n / 20000)), best = 0, h = 1.5;
    for (var i = 0; i < m.n; i += st) { var z = +(+m.sz[i]).toFixed(3); C[z] = (C[z] || 0) + 1; if (C[z] > best) { best = C[z]; h = z; } }
    var ref = m.ext ? Math.floor(m.ext[4] - (m.sz[0] || h) / 2) : 0; return [ref + h, ref];
  };
  if (typeof window.bxSGkos !== 'function') {
    window.bxSGkos = function () { return 'rep'; };
    window.bxSGeff = function () { var U = (window.BX && BX.ui) || {}; return +U.sg || 2.6; };
    window.bxSGv = function (v) { var U = window.BX && BX.ui; if (!U) return 2.6; if (!U.sgCol) return +U.sg || 2.6; if (isFinite(v) && v > 0) return v; return +U.sg || 2.6; };
  }
})();
