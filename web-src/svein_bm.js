/* ============ SOLID VEIN AKTUAL (trial) — GC-Ex Block Model ============
   Node khusus (keputusan pemilik: perlakuannya tidak lazim seperti As-Mined, dan menu boleh
   berulang dengan menu di atasnya). Tujuannya: tubuh vein yang BENAR-BENAR tergali, sebagai solid
   wireframe tertutup, dibangun dari poligon as-mined per flitch dan titik pick-up ATAP galian.

   Alur (grup per PERIODE):
     1. Titik atap  : pick-up roof (amD().ptsR, sama dengan As-Mined › atap), difilter pita RL.
     2. Poligon     : satu poligon per flitch per pulau — didigit di plan dengan snap ke titik atap,
                      atau diambil dari register as-mined / dig block flitch aktif.
     3. Solid       : poligon flitch berurutan disambung (loft) bila jarak datarnya <= jarak sambung
                      maksimum; lebih jauh dari itu TIDAK disambung (pulau tertutup sendiri). Flitch
                      tanpa poligon = solid putus. Poligon induk yang bercabang ke beberapa anak dibelah
                      garis bagi antar anak (tiap belahan disambung ke anaknya; bidang belahnya tidak
                      digambar, jadi tetap satu solid tertutup).

   CARA SURPAC (permintaan pemilik 10-11-2026: "seakurat mungkin dengan cara kerja Surpac"):
     - Titik poligon TIDAK di-resample: semua titik asli dipakai, seperti "Triangulate between
       segments" Surpac. Pasangan titik awal dipilih otomatis (titik terdekat; semua kandidat awal
       dicoba, yang luasnya terkecil dipakai).
     - Metode sambung: LUAS PERMUKAAN MINIMUM (bawaan Surpac, dynamic programming -- optimum, bukan
       greedy), EQUI-ANGULAR (diagonal terpendek -> segitiga tidak lancip), atau PROPORSIONAL
       (pasangan menurut jarak proporsional sepanjang keliling).
     - Arah string disamakan otomatis (keduanya berlawanan jarum jam dilihat dari atas; Surpac:
       "reverse direction").
     - Tutup ujung = "Triangulate a segment": ear-clipping poligon (cekung pun bisa); atap pulau
       teratas boleh diperhalus dengan titik pick-up di dalam poligon (sisip + Lawson flip, tepi
       poligon tidak pernah dilanggar).
     - "Validate solid": tiap sisi harus dipakai tepat dua segitiga berlawanan arah (tertutup &
       orientasi konsisten), segitiga nol dibuang, normal menghadap ke luar (volume bertanda > 0).
     - Volume dari jumlah tetrahedron bertanda (sama dengan "Report volume of solid"); tonase =
       volume x SG.
     - Ekspor DTM + STR Surpac dengan OBJECT / TRISOLATION per pulau dan nomor segitiga tetangga,
       DXF 3DFACE, CSV ringkasan.
   Solid yang jadi juga didaftarkan ke Wireframe geologi (MD.models, jenis 'geo', tanda sv) supaya
   tampil di 3D & sayatan 2D dan bisa dipakai Reporting Block Model sebagai batas domain.
   Data tersimpan di BX.ui.sv (ikut proyek, seperti amData).                                        */
(function () {
  if (window.SV || typeof BX === 'undefined') return;
  var $ = function (i) { return document.getElementById(i); };
  var E = function (s) { return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) { return '&#' + c.charCodeAt(0) + ';'; }); };
  var N = function (v, d) { return (v == null || !isFinite(v)) ? '-' : (+v).toLocaleString('id-ID', { minimumFractionDigits: d || 0, maximumFractionDigits: d || 0 }); };
  var f2 = function (v) { return String(+(+v).toFixed(2)); };
  var PAL = ['#c0392b', '#8e44ad', '#d35400', '#16a085', '#2980b9', '#7f8c8d', '#27ae60', '#f39c12'];
  var SV = window.SV = { show: true, foc: '', msg: '', busy: false };

  /* ---------- data (ikut proyek) ---------- */
  function D() {
    if (!BX.ui) return SV._tmp || (SV._tmp = { per: [], cur: '', filt: {} });
    if (!BX.ui.sv) BX.ui.sv = SV._tmp || { per: [], cur: '', filt: {} };
    var d = BX.ui.sv; d.per = d.per || []; d.filt = d.filt || {}; return d;
  }
  function dirty() { try { if (window.SA && SA.dirty) SA.dirty(); } catch (e) {} }
  function uid(p) { return p + Math.random().toString(36).slice(2, 8); }
  function per() { var d = D(), p = null; d.per.forEach(function (q) { if (q.id === d.cur) p = q; }); if (!p && d.per.length) { p = d.per[0]; d.cur = p.id; } return p; }
  function parDef() { var fh = 1.5; try { var B = lyBench(); fh = +(B[0] - B[1]).toFixed(3) || 1.5; } catch (e) {} return { dmax: 3, aEdge: 12, zMode: 'idw', rIdw: 6, zTol: +(fh / 2).toFixed(3), capPts: true, method: 'min', sg: (BX.ui && BX.ui.sg) || 2.6, reg: true }; }
  function P(p) { p = p || per(); if (!p) return parDef(); p.par = p.par || {}; var d = parDef(); for (var k in d) if (p.par[k] === undefined) p.par[k] = d[k]; return p.par; }
  SV.D = D; SV.per = per;

  /* ---------- titik atap ---------- */
  function pts() { try { return (amD().ptsR || []); } catch (e) { return []; } }
  /* Tiap titik membawa NAMA FILE asalnya (q.f, sejak 0.24.52). Sebelumnya pengelompokan memakai q.c,
     padahal untuk CSV q.c = kolom KODE survey (mis. "204" di semua file) -- enam file pick-up nyata
     pemilik melebur jadi satu baris dan tidak bisa dipilih per file.
     RL flitch dibaca dari NAMA FILE (pola pemilik: ACT_SO261108OB_235-5_234_Z4.csv = RL 235,5-234).
     Titik atap TIDAK boleh dipilah ke flitch dari Z-nya: pada data nyata Z atap flitch 235,5-234
     tersebar 234,23-236,32 (0,8 m di atas RL atas, 1,3 m di bawahnya), jadi pita +-setengah flitch
     membuang sepertiga titik dan mencampur flitch bertetangga. */
  function fname(q) { return q.f || q.c || '(tanpa nama)'; }
  function flParse(nm) { var b = String(nm || '').replace(/\.[^.]+$/, ''), re = /(?:^|_)(\d{1,4}(?:-\d{1,2})?)_(\d{1,4}(?:-\d{1,2})?)(?=_|$)/g, m, best = null;
    while ((m = re.exec(b))) { var a = parseFloat(m[1].replace('-', '.')), c = parseFloat(m[2].replace('-', '.')), t = Math.max(a, c), bo = Math.min(a, c); if (t - bo > 0 && t - bo <= 12) best = { top: t, bot: bo }; re.lastIndex = m.index + 1; } return best; }
  function fileFl(nm) { var o = (D().filt.fl || {})[nm]; if (o && isFinite(+o.top) && isFinite(+o.bot) && +o.top > +o.bot) return { top: +o.top, bot: +o.bot, man: 1 }; return flParse(nm); }
  function files() { var F = {}, o = []; pts().forEach(function (q) { var c = fname(q), r = F[c]; if (!r) { r = F[c] = { c: c, n: 0, z0: 1e18, z1: -1e18 }; o.push(c); } r.n++; if (isFinite(q.z)) { if (q.z < r.z0) r.z0 = q.z; if (q.z > r.z1) r.z1 = q.z; } }); return o.map(function (c) { var r = F[c], fl = fileFl(c); r.top = fl ? fl.top : NaN; r.bot = fl ? fl.bot : NaN; r.man = fl ? !!fl.man : false; return r; }); }
  function band() { var f = D().filt, B = null; try { B = lyBench(); } catch (e) {} var lo = parseFloat(f.z0), hi = parseFloat(f.z1); if (!isFinite(lo) && B) lo = B[1] - (B[0] - B[1]); if (!isFinite(hi) && B) hi = B[0] + (B[0] - B[1]); return [isFinite(lo) ? lo : -1e9, isFinite(hi) ? hi : 1e9]; }
  function bandMan() { var f = D().filt; return isFinite(parseFloat(f.z0)) || isFinite(parseFloat(f.z1)); }
  /* titik milik flitch ber-RL atas `top`: file yang flitch-nya (nama file / isian) = flitch itu; file tanpa
     flitch -> titik yang Z-nya dalam +-tol dari RL atas (cara lama) */
  function ptsLv(top, tol) { var off = D().filt.off || {}, C = {}, t = isFinite(tol) ? tol : 0.75; return pts().filter(function (q) { var c = fname(q); if (off[c] || !isFinite(q.z)) return false; var fl = C[c]; if (fl === undefined) fl = C[c] = fileFl(c) || null; return fl ? Math.abs(fl.top - top) < 1e-3 : Math.abs(q.z - top) <= t; }); }
  /* titik yang dipakai di layar (snap & gambar): RL min/maks diisi -> pita itu; kosong -> titik flitch aktif */
  function ptsOn(bd) { var off = D().filt.off || {}; if (bd || bandMan()) { var b = bd || band(); return pts().filter(function (q) { return !off[fname(q)] && isFinite(q.z) && q.z >= b[0] && q.z <= b[1]; }); }
    var B = null; try { B = lyBench(); } catch (e) {} if (!B) return pts().filter(function (q) { return !off[fname(q)] && isFinite(q.z); }); return ptsLv(B[0], B[0] - B[1]); }
  SV.ptsLv = ptsLv; SV.files = files; SV.flParse = flParse;
  SV.ptsOn = ptsOn;

  /* ---------- poligon ---------- */
  function clean(P) { var o = []; P.forEach(function (q) { var l = o[o.length - 1]; if (!l || Math.hypot(l[0] - q[0], l[1] - q[1]) > 1e-4) o.push([+q[0], +q[1]]); }); if (o.length > 2 && Math.hypot(o[0][0] - o[o.length - 1][0], o[0][1] - o[o.length - 1][1]) < 1e-4) o.pop(); return o; }
  function sArea(P) { var a = 0; for (var i = 0, j = P.length - 1; i < P.length; j = i++) a += (P[j][0] + P[i][0]) * (P[j][1] - P[i][1]); return a / 2; }
  /* sArea (rumus lyArea) bernilai NEGATIF untuk urutan berlawanan jarum jam */
  function ccw(P) { return sArea(P) > 0 ? P.slice().reverse() : P; }
  function cen(P) { var x = 0, y = 0; P.forEach(function (q) { x += q[0]; y += q[1]; }); return [x / P.length, y / P.length]; }
  function inPoly(P, x, y) { var c = false; for (var i = 0, j = P.length - 1; i < P.length; j = i++) { if (((P[i][1] > y) !== (P[j][1] > y)) && (x < (P[j][0] - P[i][0]) * (y - P[i][1]) / (P[j][1] - P[i][1]) + P[i][0])) c = !c; } return c; }
  function segInt(a, b, c, d) { var r = [b[0] - a[0], b[1] - a[1]], s = [d[0] - c[0], d[1] - c[1]], den = r[0] * s[1] - r[1] * s[0]; if (Math.abs(den) < 1e-12) return false; var q = [c[0] - a[0], c[1] - a[1]], t = (q[0] * s[1] - q[1] * s[0]) / den, u = (q[0] * r[1] - q[1] * r[0]) / den; return t > 1e-9 && t < 1 - 1e-9 && u > 1e-9 && u < 1 - 1e-9; }
  function simple(P) { var n = P.length; for (var i = 0; i < n; i++) for (var j = i + 2; j < n; j++) { if (i === 0 && j === n - 1) continue; if (segInt(P[i], P[(i + 1) % n], P[j], P[(j + 1) % n])) return false; } return true; }
  function dSeg(p, a, b) { var dx = b[0] - a[0], dy = b[1] - a[1], L = dx * dx + dy * dy, t = L > 0 ? Math.max(0, Math.min(1, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / L)) : 0; return Math.hypot(p[0] - a[0] - t * dx, p[1] - a[1] - t * dy); }
  /* jarak datar dua poligon: 0 bila bersinggungan / bertumpuk, selain itu jarak terdekat antar tepi */
  function dPoly(A, B) { var i, j, m = A.length, n = B.length;
    for (i = 0; i < m; i++) if (inPoly(B, A[i][0], A[i][1])) return 0; for (j = 0; j < n; j++) if (inPoly(A, B[j][0], B[j][1])) return 0;
    var best = 1e18; for (i = 0; i < m; i++) { var a = A[i], a2 = A[(i + 1) % m]; for (j = 0; j < n; j++) { var b = B[j], b2 = B[(j + 1) % n]; if (segInt(a, a2, b, b2)) return 0; best = Math.min(best, dSeg(a, b, b2), dSeg(b, a, a2)); } } return best; }
  SV.dPoly = dPoly;

  function addPoly(p, P2, top, bot, src, name) { var pts2 = clean(P2); if (pts2.length < 3) return null;
    var key = pts2.map(function (q) { return q[0].toFixed(2) + ',' + q[1].toFixed(2); }).join(';');
    if (p.polys.some(function (x) { return x.key === key && Math.abs(x.top - top) < 1e-6; })) return null;
    var o = { id: uid('v'), top: +(+top).toFixed(4), bot: +(+bot).toFixed(4), pts: pts2, key: key, src: src || 'digit', name: name || '', on: true }; p.polys.push(o); return o; }
  function levels(p) { var G = {}, ord = []; (p.polys || []).forEach(function (x) { var k = x.top.toFixed(3); if (!G[k]) { G[k] = { top: x.top, bot: x.bot, L: [] }; ord.push(k); } G[k].L.push(x); }); ord.sort(function (a, b) { return +b - +a; }); return ord.map(function (k) { return G[k]; }); }
  SV.levels = levels;

  /* ---------- Z atap tiap titik poligon: IDW titik pick-up dalam radius & pita RL flitch ---------- */
  function zRoof(x, y, top, pr, Q) { if (pr.zMode !== 'idw' || !Q.length) return top; var R = +pr.rIdw || 6, R2 = R * R, sw = 0, sz = 0, ex = null;
    for (var i = 0; i < Q.length; i++) { var q = Q[i], dx = q.x - x, dy = q.y - y, d2 = dx * dx + dy * dy; if (d2 > R2) continue; if (d2 < 4e-4) { ex = q.z; break; } /* sudut poligon = titik pick-up (snap / garis luar otomatis): Z-nya dipakai persis */ var w = 1 / d2; sw += w; sz += w * q.z; }
    if (ex !== null) return ex; return sw > 0 ? sz / sw : top; }

  /* ================= geometri solid (cara Surpac) ================= */
  /* Loft dua ring (indeks ke V) tanpa resample: dynamic programming luas minimum / equi-angular /
     proporsional. A = ring atas, B = ring bawah, keduanya CCW dari atas. Mengembalikan segitiga
     [a,b,c] dengan normal ke luar. */
  function loft(V, A, B, method) { var m = A.length, n = B.length, X = V.x, Y = V.y, Z = V.z;
    var LA = perim(V, A), LB = perim(V, B);
    var tcost = function (a, b, c, ia, jb) { var ax = X[a], ay = Y[a], az = Z[a], ux = X[b] - ax, uy = Y[b] - ay, uz = Z[b] - az, vx = X[c] - ax, vy = Y[c] - ay, vz = Z[c] - az, cx = uy * vz - uz * vy, cy = uz * vx - ux * vz, cz = ux * vy - uy * vx, ar = Math.sqrt(cx * cx + cy * cy + cz * cz) / 2;
      if (method === 'equi') { var d = (X[b] - X[c]) * (X[b] - X[c]) + (Y[b] - Y[c]) * (Y[b] - Y[c]) + (Z[b] - Z[c]) * (Z[b] - Z[c]); return ar + d; }
      if (method === 'prop') { var pa = LA.s[ia] / LA.L, pb = LB.s[jb] / LB.L, dp = Math.abs(pa - pb); dp = Math.min(dp, 1 - dp); return ar + dp * dp * (LA.L + LB.L) * (LA.L + LB.L) * 0.25; }
      return ar; };
    var run = function (i0, j0, want) { /* DP di kisi (m+1)x(n+1) */ var W = n + 1, C = new Float64Array((m + 1) * W), F = new Uint8Array((m + 1) * W), i, j;
      for (i = 0; i <= m; i++) for (j = 0; j <= n; j++) { if (!i && !j) { C[0] = 0; continue; } var a = A[(i0 + i) % m], b = B[(j0 + j) % n], best = Infinity, fr = 0;
        if (i) { var a0 = A[(i0 + i - 1) % m], c1 = C[(i - 1) * W + j] + tcost(a0, b, a, (i0 + i - 1) % m, (j0 + j) % n); if (c1 < best) { best = c1; fr = 1; } }
        if (j) { var b0 = B[(j0 + j - 1) % n], c2 = C[i * W + j - 1] + tcost(a, b0, b, (i0 + i) % m, (j0 + j - 1) % n); if (c2 < best) { best = c2; fr = 2; } }
        C[i * W + j] = best; F[i * W + j] = fr; }
      if (!want) return C[m * W + n];
      var T = []; i = m; j = n; while (i || j) { var f = F[i * W + j]; if (f === 1) { T.push([A[(i0 + i - 1) % m], B[(j0 + j) % n], A[(i0 + i) % m]]); i--; } else { T.push([A[(i0 + i) % m], B[(j0 + j - 1) % n], B[(j0 + j) % n]]); j--; } }
      return T; };
    /* titik awal: semua j0 dicoba (atau 12 terdekat bila besar), yang biayanya terkecil dipakai */
    var cands = []; for (var j = 0; j < n; j++) cands.push([j, Math.hypot(X[A[0]] - X[B[j]], Y[A[0]] - Y[B[j]])]);
    cands.sort(function (a, b) { return a[1] - b[1]; }); if (m * n * n > 3e7) cands = cands.slice(0, 12);
    var bj = cands[0][0], bc = Infinity; cands.forEach(function (c) { var v = run(0, c[0], false); if (v < bc) { bc = v; bj = c[0]; } });
    return run(0, bj, true); }
  function perim(V, R) { var s = [0], L = 0; for (var i = 0; i < R.length; i++) { var a = R[i], b = R[(i + 1) % R.length]; L += Math.hypot(V.x[b] - V.x[a], V.y[b] - V.y[a]); s.push(L); } return { s: s, L: L || 1 }; }

  /* "Triangulate a segment": ear clipping di bidang datar (poligon cekung boleh). R = ring CCW. */
  /* Titik segaris (mis. titik potong garis bagi cabang, yang selalu jatuh DI sisi poligon) tidak boleh
     ikut ear-clipping: ia tidak pernah bisa jadi telinga dan berakhir sebagai segitiga berluas nol,
     yang lalu dibuang dan meninggalkan sisi terbuka. Jadi: triangulasi ring TANPA titik segaris, lalu
     tiap titik segaris disisipkan dengan membelah segitiga pemilik sisi itu. */
  function ears(V, R) { var X = V.x, Y = V.y, keep = [], drop = [], n = R.length, i;
    var cr = function (a, b, c) { return (X[b] - X[a]) * (Y[c] - Y[a]) - (Y[b] - Y[a]) * (X[c] - X[a]); };
    for (i = 0; i < n; i++) { var a = R[(i + n - 1) % n], b = R[i], c = R[(i + 1) % n], L = Math.hypot(X[c] - X[a], Y[c] - Y[a]) || 1; if (Math.abs(cr(a, b, c)) / L < 1e-7 && (X[b] - X[a]) * (X[c] - X[b]) + (Y[b] - Y[a]) * (Y[c] - Y[b]) > 0) drop.push(b); else keep.push(b); }
    if (keep.length < 3 || !drop.length) return ears0(V, R);
    var T = ears0(V, keep);
    drop.forEach(function (v) { for (var t = 0; t < T.length; t++) { var r = T[t]; for (var e = 0; e < 3; e++) { var p = r[e], q = r[(e + 1) % 3], w = r[(e + 2) % 3], Lq = Math.hypot(X[q] - X[p], Y[q] - Y[p]) || 1;
          if (Math.abs(cr(p, q, v)) / Lq < 1e-6 && (X[v] - X[p]) * (X[q] - X[v]) + (Y[v] - Y[p]) * (Y[q] - Y[v]) > 0) { T[t] = [p, v, w]; T.push([v, q, w]); return; } } } });
    return T; }
  function ears0(V, R) { var idx = R.slice(), T = [], X = V.x, Y = V.y, guard = 0;
    var cross = function (a, b, c) { return (X[b] - X[a]) * (Y[c] - Y[a]) - (Y[b] - Y[a]) * (X[c] - X[a]); };
    var inTri = function (p, a, b, c) { var d1 = cross(a, b, p), d2 = cross(b, c, p), d3 = cross(c, a, p); return !((d1 < 0 || d2 < 0 || d3 < 0) && (d1 > 0 || d2 > 0 || d3 > 0)); };
    while (idx.length > 3 && guard++ < 20000) { var cut = false, k = idx.length;
      for (var i = 0; i < k; i++) { var a = idx[(i + k - 1) % k], b = idx[i], c = idx[(i + 1) % k]; if (cross(a, b, c) <= 1e-9) continue; var okk = true;
        for (var j = 0; j < k; j++) { var p = idx[j]; if (p === a || p === b || p === c) continue; if (inTri(p, a, b, c)) { okk = false; break; } }
        if (okk) { T.push([a, b, c]); idx.splice(i, 1); cut = true; break; } }
      if (!cut) { /* poligon rusak (memotong diri / kolinear): sisa ditutup kipas supaya tetap tertutup */ for (var q = 1; q + 1 < idx.length; q++) T.push([idx[0], idx[q], idx[q + 1]]); idx = []; break; } }
    if (idx.length === 3) T.push([idx[0], idx[1], idx[2]]); return T; }

  /* Atap mengikuti titik pick-up di dalam poligon: sisipkan titik (pecah segitiga) lalu Lawson flip
     pada sisi DALAM saja -- sisi poligon (tepi solid) tidak pernah dibalik, jadi solid tetap tertutup. */
  function refine(V, T, R, Q) { if (!Q.length || !T.length) return T; var X = V.x, Y = V.y, bnd = {}; for (var i = 0; i < R.length; i++) { var a = R[i], b = R[(i + 1) % R.length]; bnd[a < b ? a + '_' + b : b + '_' + a] = 1; }
    var cross = function (ax, ay, bx, by, cx, cy) { return (bx - ax) * (cy - ay) - (by - ay) * (cx - ax); };
    var locate = function (x, y) { for (var t = 0; t < T.length; t++) { var r = T[t], d1 = cross(X[r[0]], Y[r[0]], X[r[1]], Y[r[1]], x, y), d2 = cross(X[r[1]], Y[r[1]], X[r[2]], Y[r[2]], x, y), d3 = cross(X[r[2]], Y[r[2]], X[r[0]], Y[r[0]], x, y); if (d1 > 1e-7 && d2 > 1e-7 && d3 > 1e-7) return t; } return -1; };
    var circ = function (a, b, c, p) { var ax = X[a] - X[p], ay = Y[a] - Y[p], bx = X[b] - X[p], by = Y[b] - Y[p], cx = X[c] - X[p], cy = Y[c] - Y[p]; return (ax * ax + ay * ay) * (bx * cy - cx * by) - (bx * bx + by * by) * (ax * cy - cx * ay) + (cx * cx + cy * cy) * (ax * by - bx * ay) > 1e-9; };
    var flips = function () { var ch = true, g = 0; while (ch && g++ < 50) { ch = false; var EM = {}; T.forEach(function (r, t) { for (var e = 0; e < 3; e++) { var a = r[e], b = r[(e + 1) % 3], k = a < b ? a + '_' + b : b + '_' + a; (EM[k] = EM[k] || []).push(t); } });
        for (var k in EM) { if (bnd[k] || EM[k].length !== 2) continue; var t1 = EM[k][0], t2 = EM[k][1], r1 = T[t1], r2 = T[t2], ab = k.split('_').map(Number), a = ab[0], b = ab[1], c = r1.filter(function (v) { return v !== a && v !== b; })[0], d = r2.filter(function (v) { return v !== a && v !== b; })[0]; if (c === undefined || d === undefined) continue;
          if (circ(r1[0], r1[1], r1[2], d)) { /* flip ab -> cd, jaga orientasi CCW */ var n1 = [c, d, a], n2 = [d, c, b]; if (cross(X[n1[0]], Y[n1[0]], X[n1[1]], Y[n1[1]], X[n1[2]], Y[n1[2]]) <= 1e-9 || cross(X[n2[0]], Y[n2[0]], X[n2[1]], Y[n2[1]], X[n2[2]], Y[n2[2]]) <= 1e-9) { n1 = [d, c, a]; n2 = [c, d, b]; } if (cross(X[n1[0]], Y[n1[0]], X[n1[1]], Y[n1[1]], X[n1[2]], Y[n1[2]]) <= 1e-9 || cross(X[n2[0]], Y[n2[0]], X[n2[1]], Y[n2[1]], X[n2[2]], Y[n2[2]]) <= 1e-9) continue; T[t1] = n1; T[t2] = n2; ch = true; break; } } } };
    var nIns = 0; for (var q = 0; q < Q.length && nIns < 2500; q++) { var t = locate(Q[q].x, Q[q].y); if (t < 0) continue; var r = T[t], v = V.add(Q[q].x, Q[q].y, Q[q].z); T[t] = [r[0], r[1], v]; T.push([r[1], r[2], v], [r[2], r[0], v]); nIns++; if (nIns % 8 === 0) flips(); }
    flips(); return T; }

  /* belah ring dengan garis (m, d): sisi negatif & positif; titik tepat di garis masuk keduanya.
     Titik potong baru disisipkan ke SEMUA ring yang memuat sisi itu (hindari T-junction). */
  function splitRing(V, ring, m, d, rings) { ring = ring.slice(); /* salinan: ring asli ikut disisipi titik potong di bawah */ var X = V.x, Y = V.y, Z = V.z, n = ring.length, sd = ring.map(function (v) { var s = (X[v] - m[0]) * d[0] + (Y[v] - m[1]) * d[1]; return Math.abs(s) < 1e-6 ? 0 : s; }), neg = [], pos = [];
    for (var i = 0; i < n; i++) { var a = ring[i], b = ring[(i + 1) % n], sa = sd[i], sb = sd[(i + 1) % n]; if (sa <= 0) neg.push(a); if (sa >= 0) pos.push(a);
      if ((sa < 0 && sb > 0) || (sa > 0 && sb < 0)) { var t = sa / (sa - sb), v = V.add(X[a] + t * (X[b] - X[a]), Y[a] + t * (Y[b] - Y[a]), Z[a] + t * (Z[b] - Z[a])); neg.push(v); pos.push(v);
        rings.forEach(function (R) { for (var k = 0; k < R.length; k++) { var p = R[k], q = R[(k + 1) % R.length]; if ((p === a && q === b) || (p === b && q === a)) { R.splice(k + 1, 0, v); return; } } }); } }
    return [neg.length > 2 ? neg : null, pos.length > 2 ? pos : null]; }

  /* ---------- bangun solid satu periode ---------- */
  SV.build = function (p) { p = p || per(); if (!p) return null; var pr = P(p), Lv = levels(p), V = { x: [], y: [], z: [], add: function (x, y, z) { this.x.push(x); this.y.push(y); this.z.push(z); return this.x.length - 1; } };
    var Q = pts().filter(function (q) { return !((D().filt.off || {})[fname(q)]) && isFinite(q.z); }).map(function (q) { return { x: q.x - offX, y: q.y - offY, z: q.z }; });
    var warn = [], nodes = [], byLv = [];
    /* 1. ring tiap poligon (CCW, z atap) */
    Lv.forEach(function (g, li) { var row = []; g.L.forEach(function (x) { if (x.on === false) return; var Pp = ccw(clean(x.pts)); if (Pp.length < 3) return; if (!simple(Pp)) warn.push('Poligon ' + (x.name || x.id) + ' RL ' + f2(x.top) + ' memotong dirinya sendiri: hasil di situ bisa cacat.');
      var Qb = ptsLv(g.top, +pr.zTol || 0.75).map(function (q) { return { x: q.x - offX, y: q.y - offY, z: q.z }; });
      var ring = Pp.map(function (q) { return V.add(q[0], q[1], zRoof(q[0], q[1], g.top, pr, Qb)); });
      var nd = { poly: x, lv: li, top: g.top, bot: g.bot, ring: ring, P: Pp, c: cen(Pp), kids: [], pars: [], Qb: Qb }; nodes.push(nd); row.push(nd); }); byLv.push(row); });
    if (!nodes.length) return { err: 'Belum ada poligon yang aktif.' };
    /* 2. pasangan antar level berurutan (jarak datar <= dmax). Level kosong di antaranya = putus. */
    var dmax = +pr.dmax || 0;
    for (var li = 0; li + 1 < byLv.length; li++) { var up = byLv[li], dn = byLv[li + 1], gap = Math.abs(Lv[li].bot - Lv[li + 1].top) > 1e-3; if (gap) continue; /* flitch di antaranya tidak punya poligon */
      up.forEach(function (a) { dn.forEach(function (b) { if (dPoly(a.P, b.P) <= dmax) { a.kids.push(b); b.pars.push(a); } }); }); }
    /* pasangan yang dipakai loft: komponen 1-1, 1-n (induk dibelah), n-1 (anak dibelah), n-m (terdekat) */
    var pairs = [], rings = nodes.map(function (n) { return n.ring; });
    var bis = function (owner, group, down) { /* belah ring owner menurut kelompok (rekursif) -> [{ring,node}] */ if (group.length === 1) return [{ ring: owner.ring, node: group[0] }];
      var ringOwner = owner.ring; var rec = function (ring, grp) { if (grp.length === 1) return [{ ring: ring, node: grp[0] }];
        /* sumbu utama centroid anak, pisah di celah terbesar */ var cx = 0, cy = 0; grp.forEach(function (g) { cx += g.c[0]; cy += g.c[1]; }); cx /= grp.length; cy /= grp.length; var sxx = 0, sxy = 0, syy = 0; grp.forEach(function (g) { var dx = g.c[0] - cx, dy = g.c[1] - cy; sxx += dx * dx; sxy += dx * dy; syy += dy * dy; });
        var th = 0.5 * Math.atan2(2 * sxy, sxx - syy), ax = Math.cos(th), ay = Math.sin(th), srt = grp.map(function (g) { return { g: g, t: (g.c[0] - cx) * ax + (g.c[1] - cy) * ay }; }).sort(function (a, b) { return a.t - b.t; }), bi = 1, bg = -1;
        for (var i = 1; i < srt.length; i++) { var gp = srt[i].t - srt[i - 1].t; if (gp > bg) { bg = gp; bi = i; } } var g1 = srt.slice(0, bi).map(function (s) { return s.g; }), g2 = srt.slice(bi).map(function (s) { return s.g; });
        var c1 = [0, 0], c2 = [0, 0]; g1.forEach(function (g) { c1[0] += g.c[0] / g1.length; c1[1] += g.c[1] / g1.length; }); g2.forEach(function (g) { c2[0] += g.c[0] / g2.length; c2[1] += g.c[1] / g2.length; });
        var dd = [c2[0] - c1[0], c2[1] - c1[1]], L = Math.hypot(dd[0], dd[1]) || 1; dd = [dd[0] / L, dd[1] / L]; var md = [(c1[0] + c2[0]) / 2, (c1[1] + c2[1]) / 2];
        var sp = splitRing(V, ring, md, dd, rings.concat(SUB)); var out = [];
        if (sp[0]) out = out.concat(rec(sp[0], g1)); else warn.push('Cabang di RL ' + f2(owner.top) + ': salah satu poligon pasangannya terlalu ke samping untuk dibelah; poligon itu ditutup sendiri (tidak disambung).');
        if (sp[1]) out = out.concat(rec(sp[1], g2)); else if (sp[0]) warn.push('Cabang di RL ' + f2(owner.top) + ': salah satu poligon pasangannya terlalu ke samping untuk dibelah; poligon itu ditutup sendiri (tidak disambung).');
        if (!sp[0] && !sp[1]) return [{ ring: ring, node: grp[0] }]; return out; };
      var r = rec(ringOwner, group); r.forEach(function (o) { if (o.ring !== ringOwner) SUB.push(o.ring); }); return r; };
    var SUB = [];
    /* komponen bipartit antar level */
    for (li = 0; li + 1 < byLv.length; li++) { var seen = {}; byLv[li].forEach(function (a) { if (seen[a.poly.id] || !a.kids.length) return; var U = [a], Dn = [], st = [a], uS = {}, dS = {}; uS[a.poly.id] = 1;
        while (st.length) { var x = st.pop(); (x.kids || []).forEach(function (k) { if (!dS[k.poly.id]) { dS[k.poly.id] = 1; Dn.push(k); k.pars.forEach(function (pp) { if (!uS[pp.poly.id]) { uS[pp.poly.id] = 1; U.push(pp); st.push(pp); } }); } }); }
        U.forEach(function (u) { seen[u.poly.id] = 1; });
        if (U.length === 1 && Dn.length === 1) pairs.push({ up: U[0].ring, dn: Dn[0].ring, u: U[0], d: Dn[0] });
        else if (U.length === 1) bis(U[0], Dn).forEach(function (o) { pairs.push({ up: o.ring, dn: o.node.ring, u: U[0], d: o.node }); });
        else if (Dn.length === 1) bis(Dn[0], U).forEach(function (o) { pairs.push({ up: o.node.ring, dn: o.ring, u: o.node, d: Dn[0] }); });
        else { /* n-m: pasangan centroid terdekat, sisanya ditutup sendiri */ warn.push('Pertemuan ' + U.length + ' poligon RL ' + f2(U[0].top) + ' dengan ' + Dn.length + ' poligon di bawahnya: dipasangkan menurut centroid terdekat.'); var used = {};
          U.forEach(function (u) { var best = null, bd = 1e18; Dn.forEach(function (d) { if (used[d.poly.id]) return; var dd = Math.hypot(u.c[0] - d.c[0], u.c[1] - d.c[1]); if (dd < bd) { bd = dd; best = d; } }); if (best) { used[best.poly.id] = 1; pairs.push({ up: u.ring, dn: best.ring, u: u, d: best }); } else { u.kids = []; } });
          Dn.forEach(function (d) { if (!used[d.poly.id]) d.pars = []; }); } }); }
    /* 3. segitiga: dinding loft, tutup atas (pulau teratas, atap mengikuti pick-up), lantai (terbawah) */
    var T = [], own = [];
    pairs.forEach(function (pq) { var tr = loft(V, pq.up, pq.dn, pr.method); tr.forEach(function (t) { T.push(t); own.push(pq.u); }); pq.d._joined = 1; pq.u._joinedDn = 1; });
    nodes.forEach(function (nd) { if (!nd.pars.length || !nd._joined) { var cap = ears(V, nd.ring); if (pr.capPts && nd.Qb.length) { var Qi = nd.Qb.filter(function (q) { return inPoly(nd.P, q.x, q.y); }); if (Qi.length) cap = refine(V, cap, nd.ring, Qi); } cap.forEach(function (t) { T.push(t); own.push(nd); }); }
      if (!nd.kids.length || !nd._joinedDn) { /* lantai datar di RL bawah flitch: dinding tegak + tutup bawah */ var fl = nd.ring.map(function (v) { return V.add(V.x[v], V.y[v], nd.bot); }), n = fl.length;
        for (var i = 0; i < n; i++) { var a = nd.ring[i], b = nd.ring[(i + 1) % n], c = fl[i], d = fl[(i + 1) % n]; T.push([a, c, b], [b, c, d]); own.push(nd, nd); }
        ears(V, fl).forEach(function (t) { T.push([t[0], t[2], t[1]]); own.push(nd); }); } });
    /* 4. pulau = komponen pasangan; validasi (tertutup, orientasi, volume > 0) per pulau */
    var isl = {}, iid = 0; nodes.forEach(function (nd) { if (nd._isl) return; var id = ++iid, st = [nd]; nd._isl = id; while (st.length) { var x = st.pop(); x.kids.concat(x.pars).forEach(function (y) { if (!y._isl) { y._isl = id; st.push(y); } }); } });
    var IS = []; for (var k = 1; k <= iid; k++) { var tri = [], nds = nodes.filter(function (n) { return n._isl === k; }); T.forEach(function (t, i) { if (own[i]._isl === k) tri.push(t); });
      /* buang segitiga nol */ tri = tri.filter(function (t) { var a = t[0], b = t[1], c = t[2]; if (a === b || b === c || a === c) return false; var ux = V.x[b] - V.x[a], uy = V.y[b] - V.y[a], uz = V.z[b] - V.z[a], vx = V.x[c] - V.x[a], vy = V.y[c] - V.y[a], vz = V.z[c] - V.z[a]; return Math.hypot(uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx) > 1e-9; });
      var vol = volume(V, tri); if (vol < 0) { tri = tri.map(function (t) { return [t[0], t[2], t[1]]; }); vol = -vol; }
      var ed = edges(tri), tops = nds.map(function (n) { return n.top; }), bots = nds.map(function (n) { return n.bot; });
      IS.push({ n: k, tri: tri, vol: vol, area: areaOf(V, tri), closed: ed.open === 0 && ed.dup === 0, open: ed.open, dup: ed.dup, top: Math.max.apply(null, tops), bot: Math.min.apply(null, bots), nPoly: nds.length, nLv: uniq(tops).length, polys: nds.map(function (n) { return n.poly.id; }) }); }
    IS.sort(function (a, b) { return b.vol - a.vol; }); IS.forEach(function (s, i) { s.n = i + 1; });
    return { V: V, IS: IS, warn: warn, nTri: T.length, date: new Date().toISOString() }; };
  function uniq(a) { var s = {}; return a.filter(function (v) { var k = v.toFixed(3); if (s[k]) return false; s[k] = 1; return true; }); }
  function volume(V, T) { var s = 0; for (var i = 0; i < T.length; i++) { var a = T[i][0], b = T[i][1], c = T[i][2]; s += V.x[a] * (V.y[b] * V.z[c] - V.z[b] * V.y[c]) - V.y[a] * (V.x[b] * V.z[c] - V.z[b] * V.x[c]) + V.z[a] * (V.x[b] * V.y[c] - V.y[b] * V.x[c]); } return s / 6; }
  function areaOf(V, T) { var s = 0; for (var i = 0; i < T.length; i++) { var a = T[i][0], b = T[i][1], c = T[i][2], ux = V.x[b] - V.x[a], uy = V.y[b] - V.y[a], uz = V.z[b] - V.z[a], vx = V.x[c] - V.x[a], vy = V.y[c] - V.y[a], vz = V.z[c] - V.z[a]; s += Math.hypot(uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx) / 2; } return s; }
  /* validasi: tiap sisi tak berarah dipakai tepat 2x dengan arah berlawanan */
  function edges(T) { var M = {}, dup = 0, open = 0; T.forEach(function (t) { for (var e = 0; e < 3; e++) { var a = t[e], b = t[(e + 1) % 3], k = a + '>' + b; M[k] = (M[k] || 0) + 1; } });
    for (var k in M) { var ab = k.split('>'), r = ab[1] + '>' + ab[0]; if (M[k] > 1) dup++; if (!M[r]) open++; } return { open: open, dup: dup }; }
  SV.volume = volume; SV.edges = edges;

  /* ---------- hasil -> MD.models (Wireframe geologi) ---------- */
  function unreg(p) { if (!window.MD || !MD.models) return; var n0 = MD.models.length; MD.models = MD.models.filter(function (m) { return !(m.sv && m.sv === p.id); }); if (MD.models.length !== n0 && window.mdBump) mdBump(true); }
  function reg(p, R) { if (!window.MD || !MD.models) return; unreg(p); if (!P(p).reg) return; var V = R.V;
    R.IS.forEach(function (s, i) { var map = {}, v = [], t = []; s.tri.forEach(function (tr) { tr.forEach(function (ix) { if (map[ix] === undefined) { map[ix] = v.length / 3; v.push(V.x[ix] + offX, V.y[ix] + offY, V.z[ix]); } t.push(map[ix]); }); });
      MD.models.push({ name: 'Vein aktual ' + (p.name || '') + ' #' + s.n, v: new Float64Array(v), t: new Uint32Array(t), nv: v.length / 3, nt: t.length / 3, col: PAL[i % PAL.length], op: 0.7, vis: s.vis !== false, jenis: 'geo', sv: p.id, svn: s.n }); });
    if (window.mdBump) mdBump(true); }
  SV.run = function () { var p = per(); if (!p) { alert('Tambah periode dulu.'); return; } if (!p.polys.length) { alert('Belum ada poligon di periode ini.'); return; } SV.busy = true; panel();
    setTimeout(function () { try { var R = SV.build(p); if (R.err) { SV.msg = '<span class=warn>' + E(R.err) + '</span>'; p.res = null; }
        else { p.res = { date: R.date, nTri: R.nTri, warn: R.warn, IS: R.IS.map(function (s) { return { n: s.n, vol: s.vol, area: s.area, closed: s.closed, open: s.open, dup: s.dup, top: s.top, bot: s.bot, nPoly: s.nPoly, nLv: s.nLv, nt: s.tri.length, polys: s.polys, vis: true }; }) }; SV._R = R; SV._Rid = p.id; reg(p, R); SV.msg = ''; }
      } catch (e) { console.error(e); SV.msg = '<span class=warn>Gagal: ' + E(e.message) + '</span>'; } SV.busy = false; dirty(); panel(); try { if (window.PT && PT.soon) PT.soon(); } catch (e) {} updatePlot(); }, 30); };
  /* geometri hasil tidak disimpan ke proyek (bisa dibangun ulang); bila belum ada di memori, bangun lagi */
  function R(p) { p = p || per(); if (!p || !p.res) return null; if (SV._R && SV._Rid === p.id) return SV._R; try { var r = SV.build(p); if (!r.err) { SV._R = r; SV._Rid = p.id; return r; } } catch (e) {} return null; }
  SV.R = R;
  /* dipanggil saat proyek dipulihkan: daftarkan ulang solid ke MD.models bila belum ada */
  SV.restore = function () { try { var d = D(); d.per.forEach(function (p) { if (p.res && P(p).reg && !(MD.models || []).some(function (m) { return m.sv === p.id; })) { var r = R(p); if (r) reg(p, r); } }); } catch (e) {} };

  /* ---------- periode ---------- */
  SV.addPer = function () { var nm = prompt('Nama periode (mis. Nov-2026 W1):', ''); if (nm === null) return; var d = D(), p = { id: uid('p'), name: nm || ('Periode ' + (d.per.length + 1)), from: '', to: '', polys: [], par: parDef(), res: null }; d.per.push(p); d.cur = p.id; dirty(); panel(); tree(); };
  SV.delPer = function (id) { var d = D(), p = d.per.filter(function (q) { return q.id === id; })[0]; if (!p || !confirm('Hapus periode "' + p.name + '" beserta poligon & solidnya?')) return; unreg(p); d.per = d.per.filter(function (q) { return q.id !== id; }); if (d.cur === id) d.cur = d.per.length ? d.per[0].id : ''; dirty(); panel(); tree(); updatePlot(); };
  SV.renPer = function (id, nm) { var p = D().per.filter(function (q) { return q.id === id; })[0]; if (p && nm) { p.name = nm; if (p.res) { var r = R(p); if (r) reg(p, r); } dirty(); panel(); tree(); } };
  SV.selPer = function (id) { D().cur = id; SV._R = null; dirty(); panel(); tree(); updatePlot(); };
  SV.setPar = function (k, v) { var p = per(); if (!p) return; P(p)[k] = v; dirty(); if (k === 'reg') { if (v) { var r = R(p); if (r) reg(p, r); } else unreg(p); updatePlot(); } panel(); };
  SV.setFilt = function (k, v) { D().filt[k] = v; dirty(); panel(); updatePlot(); };
  SV.fileOn = function (c, v) { var f = D().filt; f.off = f.off || {}; if (v) delete f.off[c]; else f.off[c] = 1; dirty(); panel(); updatePlot(); };
  SV.import = function (inp) { if (!inp || !inp.files || !inp.files.length) return; if (typeof amPtsFile !== 'function') { alert('Modul As-Mined belum siap.'); return; } amPtsFile(inp.files, 'ptsR'); inp.value = ''; setTimeout(panel, 400); setTimeout(panel, 1500); };
  SV.clearPts = function () { if (!confirm('Hapus SEMUA titik atap (juga dipakai As-Mined › atap)?')) return; if (typeof amPtsClear === 'function') amPtsClear('ptsR'); panel(); };

  /* ---------- poligon: digit (snap titik atap), ambil dari as-mined / dig block ---------- */
  SV.dig = function () { var p = per(); if (!p) { alert('Tambah periode dulu.'); return; } if (!BX.m) { alert('Import block model dulu.'); return; }
    if (!(window.dbFlOn && dbFlOn())) { if (window.PT && PT.mau) PT.mau('sv'); lyApply(); } if (window.VIEW2D === false) toggle2D(); uiTab('SV'); DG.svm = p.id; if ($('dgDesc')) $('dgDesc').value = 'VEIN'; dgStart(); panel(); };
  /* snap ke titik atap dalam pita RL (9 px), dipanggil dgSnap2 lebih dulu */
  var _hook = window.dgSnapHook; window.dgSnapHook = function (A, px, py) { if (DG.svm) { var Q = ptsOn(), best = 9, res = null, pr = P(); if (pr.snap === false) return _hook ? _hook(A, px, py) : null;
      for (var i = 0; i < Q.length; i++) { var q = Q[i], pp = dgPx(A, q.x, q.y), dd = Math.hypot(pp[0] - px, pp[1] - py); if (dd < best) { best = dd; res = [q.x, q.y]; } } if (res) return res; }
    return _hook ? _hook(A, px, py) : null; };
  (function () { var _f = dgFinish; dgFinish = function (closed) { if (!DG.svm) return _f.apply(this, arguments); var pid = DG.svm, p = D().per.filter(function (q) { return q.id === pid; })[0];
      if (!closed) { alert('Poligon vein harus tertutup: klik titik pertama lagi atau tekan Enter.'); return; }
      if (!DG.on || DG.cur.length < 3) { alert('Poligon butuh minimal 3 titik.'); return; }
      var B = lyBench(), o = p ? addPoly(p, DG.cur.map(function (q) { return [q[0], q[1]]; }), B[0], B[1], 'digit', 'V' + (p.polys.length + 1)) : null;
      DG.svm = null; dgCancel(); if (o) { dirty(); SV.msg = 'Poligon ' + E(o.name) + ' (' + N(Math.abs(sArea(o.pts)), 1) + ' m²) ditambahkan di flitch RL ' + f2(B[0]) + '–' + f2(B[1]) + '.'; } panel(); tree(); updatePlot(); }; })();
  (function () { var _c = dgCancel; dgCancel = function () { var r = _c.apply(this, arguments); if (DG.svm) { DG.svm = null; try { panel(); } catch (e) {} } return r; }; })();
  SV.fromAM = function () { var p = per(); if (!p) return; var B = (window.amBndAll ? amBndAll() : []), n = 0, f = p.from || '', t = p.to || '';
    B.forEach(function (x) { if (x.on === false) return; var d = String(x.date || ''); if (f && d && d < f) return; if (t && d && d > t) return; if (addPoly(p, x.pts, x.top, x.bot, 'am', x.name || x.code || x.id)) n++; });
    SV.msg = n ? n + ' poligon as-mined diambil' + (f || t ? ' (tanggal ' + (f || '…') + ' s.d. ' + (t || '…') + ')' : '') + '.' : '<span class=warn>Tidak ada poligon as-mined baru' + (f || t ? ' pada rentang tanggal periode ini' : '') + '.</span>'; dirty(); panel(); tree(); updatePlot(); };
  SV.fromDB = function () { var p = per(); if (!p || !BX.m) return; var B = lyBench(), n = 0; (window.lyPolys ? lyPolys() : []).forEach(function (o) { if (addPoly(p, o.s.pts.map(function (q) { return [q[0], q[1]]; }), B[0], B[1], 'db', o.s.d ? o.s.d + ' ' + o.s.no : 'DB ' + o.s.no)) n++; });
    SV.msg = n ? n + ' dig block flitch aktif diambil sebagai poligon.' : '<span class=warn>Tidak ada dig block baru di flitch aktif.</span>'; dirty(); panel(); tree(); updatePlot(); };
  SV.setFl = function (i, k, v) { var f = files()[i]; if (!f) return; var d = D().filt; d.fl = d.fl || {}; var o = d.fl[f.c] || { top: isFinite(f.top) ? f.top : '', bot: isFinite(f.bot) ? f.bot : '' }; o[k] = v === '' ? '' : +v; d.fl[f.c] = o; dirty(); panel(); updatePlot(); };
  /* ---------- garis luar otomatis (alpha shape) ----------
     Pick-up nyata = sudut-sudut dig block aktual, beberapa dig block per file, TANPA pemisah, dan sisi
     bersama antar dig block tidak diukur ulang -- jadi urutan titik tidak bisa dipakai sebagai poligon.
     Yang bisa diturunkan dengan jujur dari titik saja adalah GARIS LUAR gugusnya: triangulasi Delaunay,
     buang segitiga yang punya sisi > `L`, sisi yang tersisa dipakai satu segitiga saja = batas. Titik di
     dalam batas tetap dipakai sebagai atap (opsi atap ikut titik pick-up). Ini USULAN: pemakai memeriksa. */
  function outline(Q, L) { var P = [], seen = {}; Q.forEach(function (q) { var k = q.x.toFixed(2) + ',' + q.y.toFixed(2); if (!seen[k]) { seen[k] = 1; P.push([q.x, q.y]); } }); if (P.length < 3 || !window.Delaunator) return [];
    var dl; try { dl = Delaunator.from(P); } catch (e) { return []; } var T = dl.triangles, E2 = {}, L2 = L * L, d2 = function (a, b) { var dx = P[a][0] - P[b][0], dy = P[a][1] - P[b][1]; return dx * dx + dy * dy; };
    for (var t = 0; t < T.length; t += 3) { var a = T[t], b = T[t + 1], c = T[t + 2]; if (d2(a, b) > L2 || d2(b, c) > L2 || d2(c, a) > L2) continue; var cr = (P[b][0] - P[a][0]) * (P[c][1] - P[a][1]) - (P[b][1] - P[a][1]) * (P[c][0] - P[a][0]); if (Math.abs(cr) < 1e-9) continue; if (cr < 0) { var w = b; b = c; c = w; }
      [[a, b], [b, c], [c, a]].forEach(function (e) { var r = e[1] + '>' + e[0]; if (E2[r]) delete E2[r]; else E2[e[0] + '>' + e[1]] = e; }); }
    /* sisi batas berarah (segitiga di kiri) -> rangkai jadi loop; di titik jepit pilih belokan paling KIRI: tiap cuping jadi loop sendiri yang sederhana */
    var out = {}; for (var k in E2) { var e = E2[k]; (out[e[0]] = out[e[0]] || []).push(e[1]); } var loops = [];
    for (var s0 in out) { while (out[s0] && out[s0].length) { var st = +s0, cur = st, nx = out[st].pop(), lp = [st], prev = st, g = 0; while (nx !== st && g++ < 100000) { lp.push(nx); var O = out[nx]; if (!O || !O.length) { lp = null; break; } var pick = 0; if (O.length > 1) { var bx = P[nx][0] - P[prev][0], by = P[nx][1] - P[prev][1], ba = -9; O.forEach(function (c2, ix) { var cx = P[c2][0] - P[nx][0], cy = P[c2][1] - P[nx][1], an = Math.atan2(bx * cy - by * cx, bx * cx + by * cy); if (an > ba) { ba = an; pick = ix; } }); }
          prev = nx; nx = O.splice(pick, 1)[0]; } if (lp && lp.length >= 3) loops.push(lp.map(function (ix) { return P[ix]; })); } }
    return loops.filter(function (lp) { return -sArea(lp) > 1; }); /* sArea() di modul ini NEGATIF untuk loop berlawanan jarum jam = loop luar; lubang & serpihan < 1 m2 dibuang */ }
  SV.outline = outline;
  SV.auto = function () { var p = per(); if (!p) { alert('Tambah periode dulu.'); return; } var pr = P(p), F = files().filter(function (f) { return isFinite(f.top) && !(D().filt.off || {})[f.c]; }), n = 0, tanpa = files().length - F.length, off = D().filt.off || {};
    if (!F.length) { alert('Tidak ada file titik atap yang RL flitch-nya diketahui. Isi RL atas & bawah di tabel file.'); return; }
    var ada = p.polys.filter(function (x) { return x.src === 'auto'; }).length; if (ada && !confirm('Ganti ' + ada + ' poligon garis-luar otomatis yang sudah ada? (Poligon hasil digit / as-mined tidak disentuh.)')) return; p.polys = p.polys.filter(function (x) { return x.src !== 'auto'; });
    F.forEach(function (f) { var Q = pts().filter(function (q) { return fname(q) === f.c && isFinite(q.z); }).map(function (q) { return { x: q.x - offX, y: q.y - offY }; }), nm = f.c.replace(/\.[^.]+$/, ''); outline(Q, +pr.aEdge || 12).forEach(function (lp, i) { if (addPoly(p, lp, f.top, f.bot, 'auto', nm.length > 22 ? nm.slice(0, 20) + '… #' + (i + 1) : nm + ' #' + (i + 1))) n++; }); });
    SV.msg = n + ' poligon garis luar dibuat dari ' + F.length + ' file' + (tanpa ? ' (' + tanpa + ' file dilewati: RL flitch belum diisi / dimatikan)' : '') + '. <b>Periksa di plan tiap flitch</b> (tombol Buka); poligon yang tidak cocok dihapus lalu didigit.'; dirty(); panel(); tree(); updatePlot(); };
  SV.delPoly = function (id) { var p = per(); if (!p) return; p.polys = p.polys.filter(function (x) { return x.id !== id; }); dirty(); panel(); tree(); updatePlot(); };
  SV.polyOn = function (id, v) { var p = per(); if (!p) return; p.polys.forEach(function (x) { if (x.id === id) x.on = v; }); dirty(); panel(); updatePlot(); };
  SV.goLv = function (top, bot) { try { lySet('fh', +(top - bot).toFixed(3)); lyU().bot = ''; lySet('top', +(+top).toFixed(3)); if (window.PT && PT.mau) PT.mau('sv'); lyApply(); uiTab('SV'); panel(); } catch (e) { console.error(e); } };
  SV.islVis = function (n, v) { var p = per(); if (!p || !p.res) return; p.res.IS.forEach(function (s) { if (s.n === n) s.vis = v; }); (MD.models || []).forEach(function (m) { if (m.sv === p.id && m.svn === n) m.vis = v; }); if (window.mdBump) mdBump(); dirty(); panel(); };

  /* ---------- ekspor ---------- */
  function fnm(p, ext) { return ('VeinAktual_' + (p.name || 'periode')).replace(/[^A-Za-z0-9_-]+/g, '_') + '.' + ext; }
  SV.expDtm = function () { var p = per(), r = R(p); if (!r) { alert('Bangun solid dulu.'); return; } var V = r.V, d = new Date(), mo = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'][d.getMonth()], base = fnm(p, 'str').replace(/\.str$/, ''), hdr = base + ',' + ('0' + d.getDate()).slice(-2) + '-' + mo + '-' + String(d.getFullYear()).slice(-2) + ',,ssi_styles:styles.ssi';
    /* STR: semua titik (string 1), berurutan = indeks titik yang dirujuk DTM */ var S = [hdr, '0, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000'], map = {}, np = 0, f3 = function (v) { return (+v).toFixed(3); };
    var T = [hdr, '0, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000', 'OBJECT, 1,'], nt = 0;
    r.IS.forEach(function (s) { var tri = s.tri, loc = []; tri.forEach(function (t) { t.forEach(function (ix) { if (map[ix] === undefined) { map[ix] = ++np; S.push('1, ' + f3(V.y[ix] + offY) + ', ' + f3(V.x[ix] + offX) + ', ' + f3(V.z[ix]) + ','); } }); });
      /* tetangga: segitiga yang berbagi sisi (p1p2, p2p3, p3p1) */ var EM = {}; tri.forEach(function (t, i) { for (var e = 0; e < 3; e++) { var a = t[e], b = t[(e + 1) % 3], k = a < b ? a + '_' + b : b + '_' + a; (EM[k] = EM[k] || []).push(i); } });
      T.push('TRISOLATION, ' + s.n + ', neighbours=yes, validated=' + (s.closed ? 'true' : 'false') + ', closed=' + (s.closed ? 'true' : 'false') + ', solid=true,');
      tri.forEach(function (t, i) { var nb = []; for (var e = 0; e < 3; e++) { var a = t[e], b = t[(e + 1) % 3], k = a < b ? a + '_' + b : b + '_' + a, o = (EM[k] || []).filter(function (j) { return j !== i; })[0]; nb.push(o === undefined ? 0 : nt + o + 1); } T.push((nt + i + 1) + ', ' + map[t[0]] + ', ' + map[t[1]] + ', ' + map[t[2]] + ', ' + nb.join(', ') + ','); }); nt += tri.length; });
    S.push('0, 0.000, 0.000, 0.000,', '0, 0.000, 0.000, 0.000, END'); T.push('END');
    gxSimpan(T.join('\r\n') + '\r\n', base + '.dtm').then(function (ok) { if (ok !== null) gxSimpan(S.join('\r\n') + '\r\n', base + '.str'); }); };
  SV.expDxf = function () { var p = per(), r = R(p); if (!r) { alert('Bangun solid dulu.'); return; } var V = r.V, f3 = function (v) { return (+v).toFixed(3); }, L = ['0', 'SECTION', '2', 'HEADER', '9', '$ACADVER', '1', 'AC1009', '0', 'ENDSEC', '0', 'SECTION', '2', 'ENTITIES'];
    r.IS.forEach(function (s) { var ly = ('VEIN_' + (p.name || '') + '_' + s.n).replace(/[^A-Za-z0-9_-]+/g, '_'); s.tri.forEach(function (t) { L.push('0', '3DFACE', '8', ly); [0, 1, 2, 2].forEach(function (q, k) { var ix = t[q]; L.push(String(10 + k), f3(V.x[ix] + offX), String(20 + k), f3(V.y[ix] + offY), String(30 + k), f3(V.z[ix])); }); }); });
    L.push('0', 'ENDSEC', '0', 'EOF'); gxSimpan(L.join('\r\n') + '\r\n', fnm(p, 'dxf'), 'application/dxf'); };
  SV.expCsv = function () { var p = per(); if (!p || !p.res) { alert('Bangun solid dulu.'); return; } var sg = +P(p).sg || 0, o = ['Periode,Pulau,RL atas,RL bawah,Jumlah flitch,Jumlah poligon,Segitiga,Tertutup,Luas permukaan (m2),Volume (m3),SG,Tonase (t)'];
    p.res.IS.forEach(function (s) { o.push([p.name, s.n, s.top.toFixed(3), s.bot.toFixed(3), s.nLv, s.nPoly, s.nt, s.closed ? 'ya' : 'TIDAK (' + s.open + ' sisi terbuka)', s.area.toFixed(2), s.vol.toFixed(3), sg, (s.vol * sg).toFixed(1)].map(function (v) { return '"' + String(v).replace(/"/g, '""') + '"'; }).join(',')); });
    gxSimpan(o.join('\r\n') + '\r\n', fnm(p, 'csv'), 'text/csv'); };

  /* ---------- gambar: titik atap & poligon (3D dan plan 2D lewat dgTraces) ---------- */
  (function () { var _d = window.dgTraces; if (typeof _d !== 'function') return; window.dgTraces = function (T, o) { var r = _d.apply(this, arguments); try { if (SV.show && BX.m) svTraces(T, o, !!(window.PT && PT.sel && /^sv(\.|$)/.test(PT.sel) || DG.svm || (SV._tab && $('pSV') && !$('pSV').hidden))); } catch (e) { console.error(e); } return r; }; })();
  /* Poligon & solid SELALU tampil di 3D selama node dicentang (permintaan pemilik); titik atap hanya saat
     node Solid Vein dibuka supaya tampilan lain tidak penuh titik. Solid yang didaftarkan ke Wireframe
     geologi digambar mdTraces; yang tidak didaftarkan digambar di sini. */
  function svTraces(T, o, aktif) { /* di 3D poligon & solid vein TIDAK ikut dipotong slab (pemilik 10-11-2026: keduanya harus terlihat di jendela 3D); di plan 2D tetap per slab */ var clip = !!window.VIEW2D, Q = aktif ? ptsOn() : [], x = [], y = [], z = [], h = [];
    var p0 = per(); if (p0 && p0.res && !P(p0).reg && !window.VIEW2D) { var r0 = R(p0); if (r0) r0.IS.forEach(function (s, i) { var vis = true; p0.res.IS.forEach(function (q) { if (q.n === s.n && q.vis === false) vis = false; }); if (!vis) return; var I = [], J = [], K = []; s.tri.forEach(function (t) { I.push(t[0]); J.push(t[1]); K.push(t[2]); });
        T.push({ type: 'mesh3d', name: 'Vein aktual ' + (p0.name || '') + ' #' + s.n, x: r0.V.x, y: r0.V.y, z: r0.V.z, i: I, j: J, k: K, color: PAL[i % PAL.length], opacity: 0.7, flatshading: true, lighting: { ambient: 0.55, diffuse: 0.75, specular: 0.15, roughness: 0.7 }, hoverinfo: 'name', showlegend: true, showscale: false }); }); }
    Q.forEach(function (q) { var pp = { x: q.x - offX, y: q.y - offY, z: q.z }; if (clip && !inK(o.K, pp)) return; x.push(pp.x); y.push(pp.y); z.push(pp.z); h.push((q.id || q.c || '') + ' Z ' + (+q.z).toFixed(2)); });
    if (x.length) T.push({ type: 'scatter3d', mode: 'markers', x: x, y: y, z: z, hovertext: h, hoverinfo: 'text', name: 'Titik atap (' + x.length + ')', marker: { size: 2.6, color: '#c2185b', symbol: 'cross' }, showlegend: true });
    var p = per(); if (!p) return; p.polys.forEach(function (v, i) { if (v.on === false) return; var pts2 = v.pts.map(function (q) { return { x: q[0], y: q[1], z: v.top }; }); pts2.push(pts2[0]); var X = [], Y = [], Z = [], any = false;
      for (var k = 1; k < pts2.length; k++) { var sg = [pts2[k - 1], pts2[k]]; if (clip) { sg = clipSeg(pts2[k - 1], pts2[k], o.K); if (!sg) continue; } X.push(sg[0].x, sg[1].x, null); Y.push(sg[0].y, sg[1].y, null); Z.push(sg[0].z, sg[1].z, null); any = true; }
      if (any) T.push({ type: 'scatter3d', mode: 'lines', x: X, y: Y, z: Z, name: 'Vein ' + (v.name || i + 1) + ' RL ' + f2(v.top), line: { color: PAL[i % PAL.length], width: 5 }, hoverinfo: 'name', showlegend: true }); }); }

  /* ---------- Lihat di 3D: kamera diarahkan & didekatkan ke poligon + solid periode aktif ----------
     Tubuh vein hanya beberapa puluh meter, sedangkan adegan 3D selebar pit: tanpa ini solidnya memang
     tergambar tetapi cuma setitik. Kamera Plotly bekerja di koordinat kubus adegan, jadi kotak batas
     vein diubah dulu ke koordinat itu (rentang sumbu & rasio aspek yang sedang dipakai). */
  SV.lihat = function () { var p = per(); if (!p) return; var b = [1e18, -1e18, 1e18, -1e18, 1e18, -1e18], add = function (x, y, z) { if (x < b[0]) b[0] = x; if (x > b[1]) b[1] = x; if (y < b[2]) b[2] = y; if (y > b[3]) b[3] = y; if (z < b[4]) b[4] = z; if (z > b[5]) b[5] = z; };
    (p.polys || []).forEach(function (v) { if (v.on === false) return; v.pts.forEach(function (q) { add(q[0], q[1], v.top); add(q[0], q[1], v.bot); }); }); if (b[0] > b[1]) { alert('Belum ada poligon di periode ini.'); return; }
    SV.show = true; /* slab dimatikan: wireframe geologi di dalam slab digambar samar (opasitas 0,25) */ try { if ($('sliceClip') && $('sliceClip').checked) $('sliceClip').checked = false; } catch (e) {}
    SV.show = true; var go = function (k) { var gd = $('plotDiv'), L = gd && gd._fullLayout, sc = L && L.scene; if (!sc || !sc.xaxis || !sc.xaxis.range) { if (k < 20) setTimeout(function () { go(k + 1); }, 150); return; }
      var ar = sc.aspectratio || { x: 1, y: 1, z: 1 }, f = function (ax, v, a) { var r = ax.range; return ((v - (r[0] + r[1]) / 2) / ((r[1] - r[0]) || 1)) * a; };
      var c = { x: f(sc.xaxis, (b[0] + b[1]) / 2, ar.x), y: f(sc.yaxis, (b[2] + b[3]) / 2, ar.y), z: f(sc.zaxis, (b[4] + b[5]) / 2, ar.z) };
      var sx = Math.abs(f(sc.xaxis, b[1], ar.x) - f(sc.xaxis, b[0], ar.x)), sy = Math.abs(f(sc.yaxis, b[3], ar.y) - f(sc.yaxis, b[2], ar.y)), sz = Math.abs(f(sc.zaxis, b[5], ar.z) - f(sc.zaxis, b[4], ar.z)), d = Math.max(0.02, Math.sqrt(sx * sx + sy * sy + sz * sz)) * 1.5;
      try { Plotly.relayout(gd, { 'scene.camera': { center: c, eye: { x: c.x + d * 0.62, y: c.y - d * 0.62, z: c.z + d * 0.48 }, up: { x: 0, y: 0, z: 1 } } }); } catch (e) { console.error(e); } };
    if (window.VIEW2D) { toggle2D(); setTimeout(function () { go(0); }, 500); } else { updatePlot(); setTimeout(function () { go(0); }, 120); } };

  /* ---------- panel ---------- */
  function sec(id, title, body) { return '<div class="svsec' + (SV.foc === id ? ' foc' : '') + '" data-sec="' + id + '"><div class=svh>' + title + '</div>' + body + '</div>'; }
  function panel() { var el = $('svBody'); if (!el) return; var m = BX.m; if (!m) { el.innerHTML = '<div class=hint>Buka block model dulu (menu <b>Block Model</b>). Flitch, SG dan titik atap mengikuti block model aktif.</div>'; return; }
    var d = D(), p = per(), pr = P(p), B = lyBench(), fl = window.dbFlOn && dbFlOn(), bd = band(), F = files(), on = ptsOn(bd), off = d.filt.off || {};
    var h = '<div class=hint style="margin-bottom:6px"><b>Trial.</b> Tubuh vein aktual: poligon as-mined per flitch + titik pick-up atap &rarr; solid wireframe tertutup (cara Surpac: semua titik dipakai, luas permukaan minimum, validasi tertutup).</div>';
    /* periode */
    h += sec('per', 'Periode', '<div class=svrow><select onchange="SV.selPer(this.value)" title="Periode aktif">' + (d.per.length ? d.per.map(function (q) { return '<option value="' + E(q.id) + '"' + (q.id === d.cur ? ' selected' : '') + '>' + E(q.name) + (q.polys.length ? ' · ' + q.polys.length + ' pol' : '') + '</option>'; }).join('') : '<option value="">(belum ada periode)</option>') + '</select><button onclick="SV.addPer()" title="Periode baru (mingguan / bulanan)">+ Periode</button>' + (p ? '<button onclick="var v=prompt(\'Nama periode:\',\'' + E(p.name).replace(/'/g, '') + '\');if(v)SV.renPer(\'' + p.id + '\',v)" title="Ganti nama">&#9998;</button><button class=x onclick="SV.delPer(\'' + p.id + '\')" title="Hapus periode">&times;</button>' : '') + '</div>' +
      (p ? '<div class=g2><div><label>Dari tanggal</label><input type=date value="' + E(p.from) + '" onchange="SV.per().from=this.value;SV.dirty()"></div><div><label>Sampai</label><input type=date value="' + E(p.to) + '" onchange="SV.per().to=this.value;SV.dirty()"></div></div><div class=hint>Rentang tanggal dipakai saat <i>Ambil poligon as-mined</i> (tanggal register as-mined).</div>' : '<div class=hint>Klik <b>+ Periode</b> untuk mulai. Semua poligon & solid dikelompokkan per periode.</div>'));
    if (!p) { el.innerHTML = h; return; }
    /* titik atap */
    h += sec('pts', 'Titik atap (pick-up roof)', '<div class=svrow><label class=svbtn><input type=file multiple accept=".csv,.txt,.str,.dxf" style="display:none" onchange="SV.import(this)">Import titik atap (CSV / STR / DXF)&hellip;</label>' + (pts().length ? '<button class=x onclick="SV.clearPts()" title="Hapus semua titik atap">&times;</button>' : '') + '</div>' +
      (pts().length ? '<table class=pltb style="margin-top:4px"><tr><th></th><th>File</th><th>Titik</th><th>Z titik</th><th>RL atas</th><th>RL bawah</th><th></th></tr>' + F.map(function (f, i) { var cur = fl && isFinite(f.top) && Math.abs(f.top - B[0]) < 1e-3 && Math.abs(f.bot - B[1]) < 1e-3; return '<tr' + (cur ? ' class=svcur' : '') + '><td><input type=checkbox ' + (off[f.c] ? '' : 'checked') + ' onchange="SV.fileOn(SV.files()[' + i + '].c,this.checked)" title="Pakai file ini"></td><td title="' + E(f.c) + '" style="max-width:92px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">' + E(f.c) + '</td><td>' + N(f.n) + '</td><td><small>' + (f.n && f.z1 >= f.z0 ? f2(f.z0) + '&ndash;' + f2(f.z1) : '-') + '</small></td>' +
          '<td><input type=number step=any style="width:54px" value="' + (isFinite(f.top) ? f.top : '') + '" onchange="SV.setFl(' + i + ',\'top\',this.value)" title="RL atas flitch file ini (dibaca dari nama file; bisa dikoreksi)"></td><td><input type=number step=any style="width:54px" value="' + (isFinite(f.bot) ? f.bot : '') + '" onchange="SV.setFl(' + i + ',\'bot\',this.value)"></td>' +
          '<td>' + (isFinite(f.top) ? '<button onclick="SV.goLv(' + f.top + ',' + f.bot + ')" title="Jadikan flitch aktif & buka plan-nya">Buka</button>' : '<span class=warn title="Nama file tidak memuat RL flitch: isi RL atas & bawah">?</span>') + '</td></tr>'; }).join('') + '</table>' +
        '<div class=hint>RL flitch dibaca dari <b>nama file</b> (mis. <code>&hellip;_235-5_234_&hellip;</code> = RL 235,5&ndash;234) dan menentukan titik mana milik flitch mana &mdash; bukan dari Z titiknya, karena atap galian nyata naik-turun melewati batas flitch.</div>' +
        '<div class=g3><div><label>RL min</label><input type=number step=any value="' + (d.filt.z0 === undefined || d.filt.z0 === '' ? '' : d.filt.z0) + '" placeholder="' + f2(bd[0]) + '" onchange="SV.setFilt(\'z0\',this.value)"></div><div><label>RL maks</label><input type=number step=any value="' + (d.filt.z1 === undefined || d.filt.z1 === '' ? '' : d.filt.z1) + '" placeholder="' + f2(bd[1]) + '" onchange="SV.setFilt(\'z1\',this.value)"></div><div><label>&nbsp;</label><button onclick="SV.setFilt(\'z0\',\'\');SV.setFilt(\'z1\',\'\')" title="Kosongkan = titik milik flitch aktif (menurut file)">Auto</button></div></div>' +
        '<div class=hint>' + N(on.length) + ' dari ' + N(pts().length) + ' titik dipakai untuk ' + (bandMan() ? 'pita RL ' + f2(bd[0]) + '&ndash;' + f2(bd[1]) : 'flitch aktif') + '. Titik ini jadi sasaran <b>snap</b> saat mendigit dan sumber Z atap tiap sudut poligon. RL min / maks hanya diisi bila ingin menyaring manual.</div>' : '<div class=hint>Belum ada titik atap. Import pick-up survey atap galian (ID, X, Y, Z, kode) atau STR/DXF.</div>'));
    /* poligon */
    var Lv = levels(p);
    h += sec('poly', 'Poligon per flitch', '<div class=hint>Flitch aktif: <b>' + (fl ? 'RL ' + f2(B[0]) + '&ndash;' + f2(B[1]) : 'belum diterapkan (tombol Digit menerapkannya)') + '</b>. Satu poligon per pulau per flitch; snap ke titik atap otomatis.</div>' +
      '<div class=g3><button class=btn-pri onclick="SV.dig()" ' + (DG.svm ? 'disabled' : '') + ' title="Digit poligon tertutup di plan flitch aktif (snap ke titik atap). Klik titik pertama lagi / Enter untuk menutup.">' + (DG.svm ? '&#9679; Mendigit&hellip;' : 'Digit poligon') + '</button><button onclick="SV.fromAM()" title="Semua poligon register as-mined (semua flitch) dalam rentang tanggal periode">Ambil as-mined</button><button onclick="SV.fromDB()" title="Dig block flitch aktif menjadi poligon">Ambil dig block</button></div>' +
      '<div class=g2 style="margin-top:4px"><button onclick="SV.auto()" ' + (pts().length ? '' : 'disabled') + ' title="Usulan poligon untuk SEMUA file ber-flitch: garis luar gugus titik pick-up (alpha shape). Periksa hasilnya di plan; hapus & digit ulang yang tidak cocok.">Garis luar otomatis (semua file)</button><div><label>Sisi terpanjang (m)</label><input type=number step=any min=1 value="' + pr.aEdge + '" onchange="SV.setPar(\'aEdge\',+this.value)" title="Dua titik dianggap satu tubuh bila bisa dihubungkan segitiga dengan sisi <= ini. Kecil = mengikuti lekuk & memisah pulau; besar = lebih membulat & menyatukan."></div></div>' +
      (DG.svm ? '<div class=hint><label class=sw><input type=checkbox ' + (pr.snap === false ? '' : 'checked') + ' onchange="SV.setPar(\'snap\',this.checked)">Snap ke titik atap</label> &middot; <button onclick="dgUndo()">Undo titik</button> <button onclick="dgCancel()">Batal</button></div>' : '') +
      (Lv.length ? '<table class=pltb style="margin-top:4px"><tr><th></th><th>Flitch</th><th>Nama</th><th>Titik</th><th>Luas</th><th>Sumber</th><th></th></tr>' + Lv.map(function (g) { return g.L.map(function (v, i) { return '<tr' + (Math.abs(g.top - B[0]) < 1e-6 && fl ? ' class=svcur' : '') + '><td><input type=checkbox ' + (v.on === false ? '' : 'checked') + ' onchange="SV.polyOn(\'' + v.id + '\',this.checked)" title="Ikut dibangun"></td>' + (i === 0 ? '<td rowspan=' + g.L.length + '><a href="javascript:void(0)" onclick="SV.goLv(' + g.top + ',' + g.bot + ')" title="Buka flitch ini">RL ' + f2(g.top) + '<br><small>' + f2(g.bot) + '</small></a></td>' : '') + '<td>' + E(v.name || '-') + '</td><td>' + v.pts.length + '</td><td>' + N(Math.abs(sArea(v.pts)), 0) + ' m&sup2;</td><td><small>' + ({ digit: 'digit', am: 'as-mined', db: 'dig block', auto: 'garis luar' }[v.src] || v.src) + '</small></td><td><button class=x onclick="SV.delPoly(\'' + v.id + '\')" title="Hapus">&times;</button></td></tr>'; }).join(''); }).join('') + '</table>' + '<button style="margin-top:4px;width:100%" onclick="SV.lihat()" title="Poligon digambar di RL atas flitchnya; kamera 3D didekatkan ke sana">Lihat poligon di 3D</button>' : '<div class=hint>Belum ada poligon.</div>'));
    /* parameter */
    h += sec('par', 'Parameter solid', '<div class=g2><div><label>Jarak sambung maks (m)</label><input type=number step=any min=0 value="' + pr.dmax + '" onchange="SV.setPar(\'dmax\',+this.value)" title="Poligon dua flitch berurutan disambung bila jarak datarnya <= ini; lebih jauh = pulau terpisah (ditutup sendiri)"></div><div><label>Metode sambung (Surpac)</label><select onchange="SV.setPar(\'method\',this.value)"><option value=min' + (pr.method === 'min' ? ' selected' : '') + '>Luas permukaan minimum</option><option value=equi' + (pr.method === 'equi' ? ' selected' : '') + '>Equi-angular</option><option value=prop' + (pr.method === 'prop' ? ' selected' : '') + '>Proporsional keliling</option></select></div></div>' +
      '<div class=g3><div><label>Z atap sudut poligon</label><select onchange="SV.setPar(\'zMode\',this.value)"><option value=idw' + (pr.zMode === 'idw' ? ' selected' : '') + '>IDW titik atap</option><option value=flat' + (pr.zMode === 'flat' ? ' selected' : '') + '>Datar = RL atas flitch</option></select></div><div><label>Radius IDW (m)</label><input type=number step=any min=0.1 value="' + pr.rIdw + '" onchange="SV.setPar(\'rIdw\',+this.value)"></div><div><label>Pita RL titik &plusmn; (m)</label><input type=number step=any min=0 value="' + pr.zTol + '" onchange="SV.setPar(\'zTol\',+this.value)" title="Titik atap yang dipakai untuk flitch = yang Z-nya dalam ± ini dari RL atas flitch"></div></div>' +
      '<div class=g2><div><label class=sw><input type=checkbox ' + (pr.capPts ? 'checked' : '') + ' onchange="SV.setPar(\'capPts\',this.checked)">Atap pulau teratas ikut titik pick-up di dalam poligon</label></div><div><label>SG (t/m&sup3;)</label><input type=number step=any min=0 value="' + pr.sg + '" onchange="SV.setPar(\'sg\',+this.value)"></div></div>' +
      '<div class=g2><button class=btn-pri onclick="SV.run()" ' + (SV.busy || !p.polys.length ? 'disabled' : '') + '>' + (SV.busy ? 'Membangun&hellip;' : 'Bangun solid') + '</button><label class=sw title="Solid ikut Wireframe geologi: tampil di 3D/sayatan dan bisa jadi batas domain Reporting"><input type=checkbox ' + (pr.reg ? 'checked' : '') + ' onchange="SV.setPar(\'reg\',this.checked)">Daftarkan ke Wireframe geologi</label></div>' + (SV.msg ? '<div class=hint>' + SV.msg + '</div>' : ''));
    /* hasil */
    var r = p.res, sg = +pr.sg || 0;
    h += sec('res', 'Hasil: solid per pulau', r ? ('<div class=hint>' + N(r.nTri) + ' segitiga &middot; ' + r.IS.length + ' pulau &middot; dibangun ' + new Date(r.date).toLocaleString() + '</div>' + (r.warn && r.warn.length ? '<div class=hint><span class=warn>' + r.warn.map(E).join('<br>') + '</span></div>' : '') +
      '<table class=pltb><tr><th></th><th>#</th><th>RL</th><th>Flitch</th><th>Tertutup</th><th>Volume m&sup3;</th><th>Ton</th></tr>' + r.IS.map(function (s) { return '<tr><td><input type=checkbox ' + (s.vis === false ? '' : 'checked') + ' onchange="SV.islVis(' + s.n + ',this.checked)" title="Tampilkan"></td><td>' + s.n + '</td><td>' + f2(s.top) + '<br><small>' + f2(s.bot) + '</small></td><td>' + s.nLv + '</td><td>' + (s.closed ? '&#10003;' : '<span class=warn title="' + s.open + ' sisi terbuka, ' + s.dup + ' sisi ganda">&#10007; ' + s.open + '</span>') + '</td><td>' + N(s.vol, 1) + '</td><td>' + N(s.vol * sg, 0) + '</td></tr>'; }).join('') +
      '<tr><th colspan=5>Total</th><th>' + N(r.IS.reduce(function (a, s) { return a + s.vol; }, 0), 1) + '</th><th>' + N(r.IS.reduce(function (a, s) { return a + s.vol; }, 0) * sg, 0) + '</th></tr></table>' +
      '<button class=btn-pri style="margin-top:4px;width:100%" onclick="SV.lihat()" title="Kamera 3D diarahkan dan didekatkan ke poligon + solid periode ini">Lihat di 3D (zoom ke vein)</button>'+
      '<div class=g3 style="margin-top:4px"><button onclick="SV.expDtm()" title="DTM + STR Surpac (OBJECT / TRISOLATION per pulau)">DTM + STR</button><button onclick="SV.expDxf()">DXF 3DFACE</button><button onclick="SV.expCsv()">CSV volume</button></div>') : '<div class=hint>Belum dibangun.</div>');
    el.innerHTML = h; if (SV.foc) { var f = el.querySelector('.svsec.foc'); if (f) try { f.scrollIntoView({ block: 'start' }); } catch (e) {} } }
  SV.panel = panel; SV.dirty = dirty;
  SV.focus = function (id) { SV.foc = id || ''; panel(); };
  function tree() { try { if (window.PT && PT.soon) PT.soon(); } catch (e) {} }
  (function () { var _u = window.uiTab; if (typeof _u === 'function') window.uiTab = function (n) { var r = _u.apply(this, arguments); var was = SV._tab; SV._tab = n === 'SV'; if (was !== SV._tab && SV.show && pts().length) { clearTimeout(SV._tt); SV._tt = setTimeout(function () { try { updatePlot(); } catch (e) {} }, 60); } if (n === 'SV') { try { panel(); } catch (e) { console.error(e); } } return r; }; })();
  (function () { var _a = window.SA && SA.applyWork; if (_a) SA.applyWork = function (W) { var r = _a.apply(this, arguments); try { SV._R = null; SV.restore(); } catch (e) {} return r; }; })();
  (function () { var _p = window.SA && SA.mdPack; if (_p) SA.mdPack = function () { var o = _p.apply(this, arguments); try { o.models.forEach(function (q, i) { var m = MD.models[i]; if (m && m.sv) { q.sv = m.sv; q.svn = m.svn; } }); } catch (e) {} return o; }; })();
  (function () { var st = document.createElement('style'); st.textContent = '.svsec{margin:6px 0 8px;padding:6px 8px;border:1px solid var(--bd,#d8dde6);border-radius:6px}.svsec.foc{border-color:var(--ac);box-shadow:0 0 0 1px var(--ac)}.svh{font-weight:700;font-size:11.5px;margin-bottom:4px;color:var(--pr,#1f4e9c)}' +
      '.svrow{display:flex;gap:5px;align-items:center}.svrow select{flex:1;min-width:0}.svfiles label{display:block;font-size:11px}.svfiles small{color:var(--mu,#5b6478)}label.svbtn{display:inline-block;padding:3px 8px;border:1px solid var(--bd,#c9d0dc);border-radius:4px;cursor:pointer;font-size:11.5px;background:var(--bt,#f4f6fa)}label.svbtn:hover{filter:brightness(.96)}' +
      '#svBody table.pltb tr.svcur td{background:var(--acs,#eef4ff)}#svBody table.pltb td,#svBody table.pltb th{font-size:11px;padding:2px 4px}'; document.head.appendChild(st); })();

  /* ---------- Demo: satu langkah, disisipkan sebelum Penutup (di sini, bukan di demox.js yang dipakai juga oleh Drill Hole) ---------- */
  (function () { var _s = window.dmSteps; if (typeof _s !== 'function') return; window.dmSteps = dmSteps = function () { var S = _s.apply(this, arguments) || []; if (S.length < 3) return S;
      var st = { s: 'Periode', t: 'Solid Vein Aktual (trial)', dur: 7, el: '.ptr[data-id="sv"], #pSV', d: 'Node khusus: poligon as-mined tiap flitch + titik pick-up atap disambung cara Surpac menjadi solid tertutup per pulau, lalu dilihat di 3D dan dihitung volumenya.',
        run: function (A) { A(0, function () { try { if (window.PT && PT.select) PT.select('sv'); } catch (e) {} }); } };
      var k = S.length - 1; while (k > 0 && S[k].s !== 'Penutup') k--; if (k <= 0) k = S.length; S.splice(k, 0, st); return S; }; })();

  /* ---------- Project Tree: node khusus ---------- */
  window.svTree = function () { var d = D(), p = per(), per2 = d.per, nP = per2.length;
    var kids = per2.map(function (q) { var Lv = levels(q), r = q.res; return { id: 'sv.p.' + q.id, t: q.name, ic: 'folder', fold: 1, tab: 'SV', b: (q.polys.length ? q.polys.length + ' pol' : '') + (r ? ' · ' + r.IS.length + ' solid' : ''), go: function () { if (d.cur !== q.id) SV.selPer(q.id); SV.focus('per'); }, rename: function (nm) { SV.renPer(q.id, nm); }, del: function () { SV.delPer(q.id); },
        menu: function () { return [{ t: 'Lihat di 3D (zoom ke vein)', fn: function () { SV.selPer(q.id); SV.lihat(); }, dis: !q.polys.length }, { t: 'Bangun solid', fn: function () { SV.selPer(q.id); SV.run(); }, dis: !q.polys.length }, { sep: 1 }, { t: 'Export DTM + STR Surpac', fn: function () { SV.selPer(q.id); SV.expDtm(); }, dis: !r }, { t: 'Export DXF 3DFACE', fn: function () { SV.selPer(q.id); SV.expDxf(); }, dis: !r }, { t: 'Export CSV volume', fn: function () { SV.selPer(q.id); SV.expCsv(); }, dis: !r }, { sep: 1 }, { t: 'Ganti nama…', fn: function () { var v = prompt('Nama periode:', q.name); if (v) SV.renPer(q.id, v); } }, { t: 'Hapus periode…', danger: 1, fn: function () { SV.delPer(q.id); } }]; },
        kids: [{ id: 'sv.p.' + q.id + '.pts', t: 'Titik atap', ic: 'pts', tab: 'SV', b: pts().length ? N(ptsOn().length) + '/' + N(pts().length) : '', dim: !pts().length, go: function () { SV.selPer(q.id); SV.focus('pts'); }, hint: 'Pick-up roof: import, filter pita RL, pilih file' },
          { id: 'sv.p.' + q.id + '.poly', t: 'Poligon per flitch', ic: 'poly', tab: 'SV', b: q.polys.length ? Lv.length + ' flitch' : '', dim: !q.polys.length, go: function () { SV.selPer(q.id); SV.focus('poly'); }, hint: 'Digit (snap titik atap), ambil dari as-mined / dig block', fold: 1,
            kids: Lv.map(function (g) { return { id: 'sv.p.' + q.id + '.lv.' + g.top.toFixed(3), t: 'RL ' + f2(g.top) + ' – ' + f2(g.bot), ic: 'flitch', tab: 'SV', b: g.L.length + ' pol', go: function () { SV.selPer(q.id); SV.goLv(g.top, g.bot); SV.focus('poly'); } }; }),
            add: { t: '+ Digit poligon di flitch aktif', fn: function () { SV.selPer(q.id); SV.dig(); } } },
          { id: 'sv.p.' + q.id + '.par', t: 'Parameter & bangun', ic: 'gear', tab: 'SV', go: function () { SV.selPer(q.id); SV.focus('par'); }, hint: 'Jarak sambung maks, metode Surpac, Z atap, SG' },
          { id: 'sv.p.' + q.id + '.res', t: 'Solid (' + (r ? r.IS.length : 0) + ')', ic: 'solid', tab: 'SV', dim: !r, go: function () { SV.selPer(q.id); SV.focus('res'); }, hint: 'Volume & tonase per pulau, export DTM/STR/DXF/CSV', fold: 1,
            kids: r ? r.IS.map(function (s) { return { id: 'sv.p.' + q.id + '.isl.' + s.n, t: 'Pulau #' + s.n + ' RL ' + f2(s.top) + '–' + f2(s.bot), ic: 'solid', tab: 'SV', b: N(s.vol, 0) + ' m³' + (s.closed ? '' : ' · terbuka'), chk: s.vis !== false, onChk: function (v) { SV.islVis(s.n, v); }, go: function () { SV.selPer(q.id); SV.focus('res'); } }; }) : [] }] }; });
    return [{ id: 'sv', step: '11', st: nP ? (per2.some(function (q) { return q.res; }) ? 'done' : 'part') : 'opt', t: 'Solid Vein Aktual (trial)', ic: 'solid', fold: 1, tab: 'SV', b: nP ? nP + ' periode' : 'trial', chk: SV.show, onChk: function (v) { SV.show = v; try { var hid = {}; D().per.forEach(function (q) { ((q.res || {}).IS || []).forEach(function (z) { if (z.vis === false) hid[q.id + '|' + z.n] = 1; }); }); (MD.models || []).forEach(function (m) { if (m.sv) m.vis = v && !hid[m.sv + '|' + m.svn]; }); MD.ver++; MD.sc = {}; if (window.mdList) mdList(); } catch (e) {} updatePlot(); }, hint: 'Tubuh vein yang benar-benar tergali: poligon per flitch + titik atap → solid wireframe tertutup (cara Surpac)',
      go: function () { SV.focus(''); }, kids: kids, add: { t: '+ Tambah periode…', fn: function () { SV.addPer(); } },
      menu: function () { return [{ t: 'Tambah periode…', fn: function () { SV.addPer(); } }, { t: 'Bangun solid periode aktif', fn: function () { SV.run(); }, dis: !p || !p.polys.length }]; } }]; };
})();
