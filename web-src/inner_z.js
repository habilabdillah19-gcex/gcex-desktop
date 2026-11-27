/* ================= String ganda / flagging sejajar dengan string induknya (BM 0.24.116, pemilik 27-11-2026) =================
   Laporan pemilik (dilihat di Surpac): "string flagging ada di bawah string utama; harusnya elevasinya sejajar, hanya shrinkage".
   Penyebab: dbInner() menaruh string ganda di RL BAWAH flitch (dbTag), sedangkan string induk yang berasal dari Digitasi biasa
   atau string import tidak punya s.db dan tetap di elevasi digitasinya -- biasanya tengah flitch (= elevasi Sayatan 2D).
   Selisihnya setengah tebal flitch (0.75 m untuk flitch 1.5 m).
   Perbaikan: Z string ganda = Z string induknya (median Z induk; string dig block datar). Dipakai saat dibuat (dbInner),
   saat ekspor STR / DXF, dan sekali saat daftar string dimuat ulang -- proyek lama ikut terbetulkan tanpa digit ulang.
   Bentuk (shrinkage), warna, nomor string & flag tidak berubah. */
(function () {
  function zInduk(s) { var z = (s.pts || []).map(function (q) { return +q[2]; }).filter(isFinite).sort(function (a, b) { return a - b; }); return z.length ? z[z.length >> 1] : NaN; }
  function samakan() {
    if (!window.DG || !DG.S) return 0; var by = {}, n = 0;
    DG.S.forEach(function (s) { if (!s.inner && s.id) by[s.id] = s; });
    DG.S.forEach(function (s) { if (!s.inner || !s.parent) return; var p = by[s.parent]; if (!p) return; var z = zInduk(p); if (!isFinite(z)) return;
      s.pts.forEach(function (q) { if (!(Math.abs(+q[2] - z) < 1e-6)) { q[2] = z; n++; } }); });
    return n;
  }
  function bungkus(nm, sebelum) {
    var f = window[nm]; if (typeof f !== 'function' || f._iz) return false;
    var g = function () { if (sebelum) { if (samakan()) { try { dgSave(); } catch (e) {} } return f.apply(this, arguments); }
      var r = f.apply(this, arguments); if (samakan()) { try { dgSave(); } catch (e) {} } return r; };
    g._iz = 1; window[nm] = g; try { eval(nm + '=g'); } catch (e) {} return true;
  }
  var tunda = 0;
  function pasang() {
    if (!window.dbInner || !window.dbExport || !window.dgList) return setTimeout(pasang, 400);
    bungkus('dbInner', false); bungkus('dbExport', true); if (window.dgExport) bungkus('dgExport', true);
    var dl = window.dgList; if (!dl._iz) { var g = function () { var r = dl.apply(this, arguments); clearTimeout(tunda); tunda = setTimeout(function () { if (samakan()) { try { dgSave(); updatePlot(); } catch (e) {} } }, 50); return r; }; g._iz = 1; window.dgList = dgList = g; }
    window.INNERZ = { samakan: samakan };
    if (samakan()) { try { dgSave(); } catch (e) {} }
  }
  pasang();
})();
