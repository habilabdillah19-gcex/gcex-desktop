/* GC-Ex — INTERPOLASI Z DARI TITIK DENGAN TRIANGULASI (TIN), cara Surpac DTM — Block Model 0.24.59
   Keputusan pemilik (10 Nov 2026): permukaan dari titik pick-up dihitung seperti Surpac — titik ditriangulasi (Delaunay,
   web-src/delaunator.min.js) lalu Z di (x,y) = interpolasi LINEAR di dalam segitiga yang memuatnya. Titik pick-up selalu
   dihormati persis (tepat di titik = Z titik itu), tidak ada "penghalusan" IDW yang menurunkan puncak / menaikkan lembah.
   Dipakai: atap As-Mined dari pick-up (amroof.js, mode 'pickup') dan Z atap sudut poligon Solid Vein (svein_bm.js).
   Di luar selubung (hull) triangulasi tidak ada segitiga: pemanggil memberi cadangan (IDW / RL nominal) lewat opt.luar.

   TINZ(P, opt) -> { f(x,y), nt, n } atau null bila < 3 titik tak segaris / Delaunator tidak ada.
     P   : [{x,y,z}] (titik ber-Z tak hingga dibuang; titik < 1 mm disatukan, Z rata-rata)
     opt : { luar: function(x,y) -> z | null (bawaan: null), faktor: buang segitiga sisi > faktor x median (bawaan: tidak) } */
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
    var cs = Math.max(0.5, Math.sqrt(Math.max(1, (x1 - x0) * (y1 - y0)) / nt) * 1.5), gx, gy;
    while (true) { gx = Math.floor((x1 - x0) / cs) + 1; gy = Math.floor((y1 - y0) / cs) + 1; if (gx * gy <= 4e6) break; cs *= 1.5; }
    /* indeks CSR (larik bertipe): ratusan ribu segitiga topografi tanpa objek per sel */
    /* opt.faktor: buang segitiga yang sisi terpanjangnya > faktor x median (sama dengan tampilan tinhr.js: kipas lebar
       menyeberangi lubang / tepi data kontur) -> di situ tidak ada permukaan, pemanggil memakai cadangan */
    var skip = null; if (opt.faktor > 0) { var mx = new Float64Array(nt); for (var q2 = 0; q2 < nt; q2++) { var p1 = T[3 * q2], p2 = T[3 * q2 + 1], p3 = T[3 * q2 + 2], l1 = Math.hypot(C[2 * p1] - C[2 * p2], C[2 * p1 + 1] - C[2 * p2 + 1]), l2 = Math.hypot(C[2 * p2] - C[2 * p3], C[2 * p2 + 1] - C[2 * p3 + 1]), l3 = Math.hypot(C[2 * p3] - C[2 * p1], C[2 * p3 + 1] - C[2 * p1 + 1]); mx[q2] = Math.max(l1, l2, l3); }
      var srt = Float64Array.from(mx).sort(), med = srt[srt.length >> 1], lim = opt.faktor * med; skip = new Uint8Array(nt); for (q2 = 0; q2 < nt; q2++) if (mx[q2] > lim) skip[q2] = 1; }
    var tb = new Int32Array(4 * nt), cnt = new Uint32Array(gx * gy + 1), t, a, b, c, ci, cj;
    for (t = 0; t < nt; t++) { if (skip && skip[t]) { tb[4 * t] = 1; tb[4 * t + 1] = 0; continue; } a = T[3 * t]; b = T[3 * t + 1]; c = T[3 * t + 2];
      var i0 = Math.floor((Math.min(C[2 * a], C[2 * b], C[2 * c]) - x0) / cs), i1 = Math.floor((Math.max(C[2 * a], C[2 * b], C[2 * c]) - x0) / cs), j0 = Math.floor((Math.min(C[2 * a + 1], C[2 * b + 1], C[2 * c + 1]) - y0) / cs), j1 = Math.floor((Math.max(C[2 * a + 1], C[2 * b + 1], C[2 * c + 1]) - y0) / cs);
      tb[4 * t] = i0; tb[4 * t + 1] = i1; tb[4 * t + 2] = j0; tb[4 * t + 3] = j1; for (ci = i0; ci <= i1; ci++) for (cj = j0; cj <= j1; cj++) cnt[cj * gx + ci + 1]++; }
    for (i = 1; i <= gx * gy; i++) cnt[i] += cnt[i - 1];
    var LST = new Int32Array(cnt[gx * gy]), pos = cnt.slice(0, gx * gy);
    for (t = 0; t < nt; t++) for (ci = tb[4 * t]; ci <= tb[4 * t + 1]; ci++) for (cj = tb[4 * t + 2]; cj <= tb[4 * t + 3]; cj++) LST[pos[cj * gx + ci]++] = t;
    tb = null; pos = null;
    var luar = typeof opt.luar === 'function' ? opt.luar : function () { return null; };
    var f = function (x, y) { var px = x - ox, py = y - oy, ii = Math.floor((px - x0) / cs), jj = Math.floor((py - y0) / cs);
      if (ii >= 0 && jj >= 0 && ii < gx && jj < gy) for (var s = cnt[jj * gx + ii], se = cnt[jj * gx + ii + 1]; s < se; s++) { var tt = LST[s], a = T[3 * tt], b = T[3 * tt + 1], c = T[3 * tt + 2], ax = C[2 * a], ay = C[2 * a + 1], bx = C[2 * b], by = C[2 * b + 1], cx = C[2 * c], cy = C[2 * c + 1];
          var den = (by - cy) * (ax - cx) + (cx - bx) * (ay - cy); if (Math.abs(den) < 1e-12) continue;
          var wa = ((by - cy) * (px - cx) + (cx - bx) * (py - cy)) / den, wb = ((cy - ay) * (px - cx) + (ax - cx) * (py - cy)) / den, wc = 1 - wa - wb, e = -1e-9;
          if (wa >= e && wb >= e && wc >= e) return wa * Z[a] + wb * Z[b] + wc * Z[c]; }
      return luar(x, y); };
    return { f: f, nt: nt, n: n };
  }
  window.TINZ = TINZ;

  /* ---------- 0.24.60 (pemilik 10-11-2026: "Ya kerjakan"): topografi & pit untuk HITUNGAN memakai TIN yang sama dengan
     tampilan (tinhr.js: faktor sliver TIN.faktor) — interpolasi linear dalam segitiga seperti DTM Surpac. IDW lama tetap
     sebagai cadangan di luar cakupan TIN (tepi data / celah kontur). Berlaku di Block Model dan Drillhole. ---------- */
  var WM = typeof WeakMap !== 'undefined' ? new WeakMap() : null;
  function tinOf(o) { if (!o || !o.x || !o.x.length || !WM) return null; var c = WM.get(o); if (c && c.len === o.x.length) return c.tin;
    var P = []; for (var i = 0; i < o.x.length; i++) { if (o.x[i] === null || o.x[i] === undefined) continue; P.push({ x: o.x[i], y: o.y[i], z: o.z[i] }); }
    var t = null; try { t = TINZ(P, { faktor: (window.TIN && TIN.faktor) || 8 }); } catch (e) { console.warn('TINZ', e); } WM.set(o, { len: o.x.length, tin: t }); return t; }
  TINZ.of = tinOf;
  function pasang() {
    if (typeof window.topoZ === 'function' && !window.topoZ._tin) { var _tz = window.topoZ;
      var nz = function (x, y) { var o = window.OV && OV.topoF, t = tinOf(o); if (t) { var v = t.f(x, y); if (v != null && isFinite(v)) return v; } return _tz(x, y); };
      nz._tin = 1; nz._idw = _tz; window.topoZ = nz; try { topoZ = nz; } catch (e) {} }
    /* rpSurf (Reporting) memanggil TINZ.of sendiri (rpbm.js / gcex_dh_base.html): fungsinya di dalam IIFE, tidak bisa dibungkus dari sini */
  }
  pasang(); setTimeout(pasang, 0); TINZ.pasang = pasang;
})();
