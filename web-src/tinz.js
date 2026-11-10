/* GC-Ex — INTERPOLASI Z DARI TITIK DENGAN TRIANGULASI (TIN), cara Surpac DTM — Block Model 0.24.59
   Keputusan pemilik (10 Nov 2026): permukaan dari titik pick-up dihitung seperti Surpac — titik ditriangulasi (Delaunay,
   web-src/delaunator.min.js) lalu Z di (x,y) = interpolasi LINEAR di dalam segitiga yang memuatnya. Titik pick-up selalu
   dihormati persis (tepat di titik = Z titik itu), tidak ada "penghalusan" IDW yang menurunkan puncak / menaikkan lembah.
   Dipakai: atap As-Mined dari pick-up (amroof.js, mode 'pickup') dan Z atap sudut poligon Solid Vein (svein_bm.js).
   Di luar selubung (hull) triangulasi tidak ada segitiga: pemanggil memberi cadangan (IDW / RL nominal) lewat opt.luar.

   TINZ(P, opt) -> { f(x,y), nt, n } atau null bila < 3 titik tak segaris / Delaunator tidak ada.
     P   : [{x,y,z}] (titik ber-Z tak hingga dibuang; titik < 1 mm disatukan, Z rata-rata)
     opt : { luar: function(x,y) -> z | null }  (bawaan: null) */
(function () {
  function TINZ(P, opt) {
    opt = opt || {}; var D = window.Delaunator; if (!D || !P || P.length < 3) return null;
    var M = {}, X = [], Y = [], Z = [], K = [];
    for (var i = 0; i < P.length; i++) { var q = P[i]; if (!q || !isFinite(q.x) || !isFinite(q.y) || !isFinite(q.z)) continue; var k = Math.round(q.x * 1000) + ':' + Math.round(q.y * 1000);
      if (M[k] !== undefined) { var j = M[k]; Z[j] += q.z; K[j]++; continue; } M[k] = X.length; X.push(+q.x); Y.push(+q.y); Z.push(+q.z); K.push(1); }
    for (i = 0; i < Z.length; i++) Z[i] /= K[i];
    var n = X.length; if (n < 3) return null;
    /* koordinat dikurangi titik pertama supaya presisi tidak hilang pada koordinat UTM besar */
    var ox = X[0], oy = Y[0], C = new Float64Array(2 * n); for (i = 0; i < n; i++) { C[2 * i] = X[i] - ox; C[2 * i + 1] = Y[i] - oy; }
    var d; try { d = new D(C); } catch (e) { return null; } var T = d.triangles, nt = T.length / 3; if (!nt) return null;
    /* indeks grid kotak pembatas segitiga */
    var x0 = 1e18, x1 = -1e18, y0 = 1e18, y1 = -1e18; for (i = 0; i < n; i++) { var xx = C[2 * i], yy = C[2 * i + 1]; if (xx < x0) x0 = xx; if (xx > x1) x1 = xx; if (yy < y0) y0 = yy; if (yy > y1) y1 = yy; }
    var cs = Math.max(0.5, Math.sqrt(Math.max(1, (x1 - x0) * (y1 - y0)) / nt) * 1.5), H = {};
    for (var t = 0; t < nt; t++) { var a = T[3 * t], b = T[3 * t + 1], c = T[3 * t + 2], bx0 = Math.min(C[2 * a], C[2 * b], C[2 * c]), bx1 = Math.max(C[2 * a], C[2 * b], C[2 * c]), by0 = Math.min(C[2 * a + 1], C[2 * b + 1], C[2 * c + 1]), by1 = Math.max(C[2 * a + 1], C[2 * b + 1], C[2 * c + 1]);
      for (var ci = Math.floor((bx0 - x0) / cs); ci <= Math.floor((bx1 - x0) / cs); ci++) for (var cj = Math.floor((by0 - y0) / cs); cj <= Math.floor((by1 - y0) / cs); cj++) { var kk = ci + '|' + cj; (H[kk] || (H[kk] = [])).push(t); } }
    var luar = typeof opt.luar === 'function' ? opt.luar : function () { return null; };
    var f = function (x, y) { var px = x - ox, py = y - oy, L = H[Math.floor((px - x0) / cs) + '|' + Math.floor((py - y0) / cs)];
      if (L) for (var s = 0; s < L.length; s++) { var tt = L[s], a = T[3 * tt], b = T[3 * tt + 1], c = T[3 * tt + 2], ax = C[2 * a], ay = C[2 * a + 1], bx = C[2 * b], by = C[2 * b + 1], cx = C[2 * c], cy = C[2 * c + 1];
          var den = (by - cy) * (ax - cx) + (cx - bx) * (ay - cy); if (Math.abs(den) < 1e-12) continue;
          var wa = ((by - cy) * (px - cx) + (cx - bx) * (py - cy)) / den, wb = ((cy - ay) * (px - cx) + (ax - cx) * (py - cy)) / den, wc = 1 - wa - wb, e = -1e-9;
          if (wa >= e && wb >= e && wc >= e) return wa * Z[a] + wb * Z[b] + wc * Z[c]; }
      return luar(x, y); };
    return { f: f, nt: nt, n: n };
  }
  window.TINZ = TINZ;
})();
