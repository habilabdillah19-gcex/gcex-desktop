/* ============ SOLID VEIN AKTUAL (trial) — GC-Ex Block Model ============
   Node khusus (keputusan pemilik: perlakuannya tidak lazim seperti As-Mined, dan menu boleh
   berulang dengan menu di atasnya). Tujuannya: tubuh vein yang BENAR-BENAR tergali, sebagai solid
   wireframe tertutup, dibangun dari poligon as-mined per flitch dan titik pick-up ATAP galian.

   Alur (grup per PERIODE):
     1. Titik atap  : pick-up roof, disimpan SENDIRI di BX.ui.sv.pts (0.24.53: lepas dari As-Mined & Dig Block).
     2. Poligon     : satu poligon per flitch per pulau — didigit di plan dengan snap ke titik atap,
                      atau usulan 'garis luar otomatis'; titik poligon bisa diedit.
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
  function parDef() { var fh = 1.5; try { var B = lyBench(); fh = +(B[0] - B[1]).toFixed(3) || 1.5; } catch (e) {} return { dmax: 3, aEdge: 12, zMode: 'idw', rIdw: 6, /* 'idw' = TIN sejak 0.24.59 (nama lama dipertahankan untuk proyek tersimpan) */ zTol: +(fh / 2).toFixed(3), capPts: true, method: 'min', sg: (BX.ui && BX.ui.sg) || 2.6, reg: true }; }
  function P(p) { p = p || per(); if (!p) return parDef(); p.par = p.par || {}; var d = parDef(); for (var k in d) if (p.par[k] === undefined) p.par[k] = d[k]; return p.par; }
  SV.D = D; SV.per = per;

  /* ---------- titik atap ---------- */
  /* Sejak 0.24.53 titik atap DISIMPAN SENDIRI di BX.ui.sv.pts (keputusan pemilik 10-11-2026: menu ini
     harus terlepas dari data & algoritma Dig Block maupun As-Mined). Tidak lagi membaca amD().ptsR. */
  function pts() { var d = D(); if (!d.pts) d.pts = []; return d.pts; }
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
  /* FLITCH KERJA SOLID VEIN (pemilik 10-11-2026): milik menu ini sendiri (D().lv), TIDAK terikat flitch aktif Dig Block /
     As-Mined. Belum pernah diisi -> mulai dari flitch aktif saat itu (hanya sebagai nilai awal). */
  function lvB() { var v = D().lv; if (v && isFinite(+v.top) && isFinite(+v.bot) && +v.top > +v.bot) return [+v.top, +v.bot]; var B = null; try { B = lyBench(); } catch (e) {} return B || [NaN, NaN]; }
  /* plan 2D sedang memperlihatkan flitch kerja ini? */
  function lvOn() { var B = lvB(); try { if (!window.VIEW2D || secGeom().m !== 'H') return false; var pos = +$('pos').value; return Math.abs(pos - (B[0] + B[1]) / 2) < 1e-6 && Math.abs((parseFloat($('thick').value) || 0) - (B[0] - B[1])) < 1e-3; } catch (e) { return false; } }
  SV.lvB = lvB; SV.lvOn = lvOn;
  function band() { var f = D().filt, B = lvB(); if (!isFinite(B[0])) B = null; var lo = parseFloat(f.z0), hi = parseFloat(f.z1); if (!isFinite(lo) && B) lo = B[1] - (B[0] - B[1]); if (!isFinite(hi) && B) hi = B[0] + (B[0] - B[1]); return [isFinite(lo) ? lo : -1e9, isFinite(hi) ? hi : 1e9]; }
  function bandMan() { var f = D().filt; return isFinite(parseFloat(f.z0)) || isFinite(parseFloat(f.z1)); }
  /* titik milik flitch ber-RL atas `top`: file yang flitch-nya (nama file / isian) = flitch itu; file tanpa
     flitch -> titik yang Z-nya dalam +-tol dari RL atas (cara lama) */
  function ptsLv(top, tol) { var off = D().filt.off || {}, C = {}, t = isFinite(tol) ? tol : 0.75; return pts().filter(function (q) { var c = fname(q); if (off[c] || !isFinite(q.z)) return false; var fl = C[c]; if (fl === undefined) fl = C[c] = fileFl(c) || null; return fl ? Math.abs(fl.top - top) < 1e-3 : Math.abs(q.z - top) <= t; }); }
  /* titik yang dipakai di layar (snap & gambar): RL min/maks diisi -> pita itu; kosong -> titik flitch aktif */
  function ptsOn(bd) { var off = D().filt.off || {}; if (bd || bandMan()) { var b = bd || band(); return pts().filter(function (q) { return !off[fname(q)] && isFinite(q.z) && q.z >= b[0] && q.z <= b[1]; }); }
    var B = lvB(); if (!isFinite(B[0])) return pts().filter(function (q) { return !off[fname(q)] && isFinite(q.z); }); return ptsLv(B[0], B[0] - B[1]); }
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

  /* ---------- gabungan (union) dua poligon sederhana ----------
     Dipakai untuk poligon BERTAMPALAN di satu flitch (keputusan pemilik 10-11-2026: digabung otomatis jadi satu tubuh).
     Kedua poligon dibuat searah, tiap sisi dipecah di titik potong & di titik poligon lawan yang menempel padanya,
     lalu potongan sisi A yang di LUAR B dan potongan sisi B yang di LUAR A dirangkai. Sisi berimpit (lazim, karena
     keduanya di-snap ke titik pick-up yang sama): searah -> dipakai sekali; berlawanan -> dibuang (sisi dalam).
     Hasil = loop terluar; lubang di dalam gabungan diabaikan. null bila rangkaian tidak menutup (pemanggil lalu
     membiarkan kedua poligon terpisah dan memperingatkan). */
  function shoe(P) { var a = 0; for (var i = 0, n = P.length; i < n; i++) { var q = P[i], r = P[(i + 1) % n]; a += q[0] * r[1] - r[0] * q[1]; } return a / 2; }
  function onSeg(p, a, b, eps) { return dSeg(p, a, b) <= eps; }
  function polyUnion(A0, B0) { var eps = 1e-6, A = shoe(A0) < 0 ? A0.slice().reverse() : A0.slice(), B = shoe(B0) < 0 ? B0.slice().reverse() : B0.slice();
    var cut = function (Pa, Pb) { var out = []; for (var i = 0, n = Pa.length; i < n; i++) { var a = Pa[i], b = Pa[(i + 1) % n], dx = b[0] - a[0], dy = b[1] - a[1], L2 = dx * dx + dy * dy, ts = [0, 1]; if (L2 < 1e-12) continue;
          for (var j = 0, m = Pb.length; j < m; j++) { var c = Pb[j], d = Pb[(j + 1) % m]; if (onSeg(c, a, b, eps)) ts.push(((c[0] - a[0]) * dx + (c[1] - a[1]) * dy) / L2);
            var ex = d[0] - c[0], ey = d[1] - c[1], den = dx * ey - dy * ex; if (Math.abs(den) > 1e-12) { var t = ((c[0] - a[0]) * ey - (c[1] - a[1]) * ex) / den, u = ((c[0] - a[0]) * dy - (c[1] - a[1]) * dx) / den; if (t > 1e-9 && t < 1 - 1e-9 && u > -1e-9 && u < 1 + 1e-9) ts.push(t); } }
          ts = ts.filter(function (t) { return t >= 0 && t <= 1; }).sort(function (x, y) { return x - y; }); for (var k = 1; k < ts.length; k++) { if (ts[k] - ts[k - 1] < 1e-9) continue; out.push([[a[0] + dx * ts[k - 1], a[1] + dy * ts[k - 1]], [a[0] + dx * ts[k], a[1] + dy * ts[k]]]); } } return out; };
    /* letak titik tengah potongan terhadap poligon lawan: 1 dalam, 0 luar, 2 di sisi searah, -2 di sisi berlawanan */
    var loc = function (sg, Pq) { var mx = (sg[0][0] + sg[1][0]) / 2, my = (sg[0][1] + sg[1][1]) / 2, dx = sg[1][0] - sg[0][0], dy = sg[1][1] - sg[0][1]; for (var j = 0, m = Pq.length; j < m; j++) { var c = Pq[j], d = Pq[(j + 1) % m]; if (onSeg([mx, my], c, d, 1e-5)) return (dx * (d[0] - c[0]) + dy * (d[1] - c[1])) >= 0 ? 2 : -2; } return inPoly(Pq, mx, my) ? 1 : 0; };
    var S = []; cut(A, B).forEach(function (sg) { var l = loc(sg, B); if (l === 0 || l === 2) S.push(sg); }); cut(B, A).forEach(function (sg) { if (loc(sg, A) === 0) S.push(sg); }); if (S.length < 3) return null;
    var key = function (q) { return q[0].toFixed(4) + ',' + q[1].toFixed(4); }, out = {}; S.forEach(function (sg) { (out[key(sg[0])] = out[key(sg[0])] || []).push(sg); });
    var loops = [], used = 0, guard = 0; S.forEach(function (st) { if (st._u) return; var lp = [], cur = st, k0 = key(st[0]); while (cur && !cur._u && guard++ < 200000) { cur._u = 1; used++; lp.push(cur[0]); var kn = key(cur[1]); if (kn === k0) { loops.push(lp); lp = null; break; } var O = (out[kn] || []).filter(function (x) { return !x._u; }); if (!O.length) break;
          if (O.length > 1) { var bx = cur[1][0] - cur[0][0], by = cur[1][1] - cur[0][1], best = null, ba = 9; O.forEach(function (x) { var cx = x[1][0] - x[0][0], cy = x[1][1] - x[0][1], an = Math.atan2(bx * cy - by * cx, bx * cx + by * cy); if (an < ba) { ba = an; best = x; } }); cur = best; } else cur = O[0]; } });
    if (!loops.length) return null; loops.sort(function (x, y) { return Math.abs(shoe(y)) - Math.abs(shoe(x)); }); var U = clean(loops[0]); if (U.length < 3 || Math.abs(shoe(U)) + 1e-6 < Math.max(Math.abs(shoe(A)), Math.abs(shoe(B)))) return null; return U; }
  SV.polyUnion = polyUnion;
  function addPoly(p, P2, top, bot, src, name) { var pts2 = clean(P2); if (pts2.length < 3) return null;
    var key = pts2.map(function (q) { return q[0].toFixed(2) + ',' + q[1].toFixed(2); }).join(';');
    if (p.polys.some(function (x) { return x.key === key && Math.abs(x.top - top) < 1e-6; })) return null;
    var o = { id: uid('v'), top: +(+top).toFixed(4), bot: +(+bot).toFixed(4), pts: pts2, key: key, src: src || 'digit', name: name || '', on: true }; p.polys.push(o); p.stale = true; return o; }
  /* Kumulatif (par.kum): poligon periode-periode SEBELUMNYA (urutan daftar) ikut dibangun, supaya galian minggu
     ini menyambung ke tubuh minggu lalu di flitch atas / bawahnya. Poligon tetap milik periodenya masing-masing. */
  function polysOf(p) { if (!p) return []; if (!(p.par && p.par.kum)) return p.polys || []; var L = [], d = D(); for (var i = 0; i < d.per.length; i++) { L = L.concat(d.per[i].polys || []); if (d.per[i].id === p.id) break; } return L; }
  function levels(p) { var G = {}, ord = []; polysOf(p).forEach(function (x) { var k = x.top.toFixed(3); if (!G[k]) { G[k] = { top: x.top, bot: x.bot, L: [] }; ord.push(k); } G[k].L.push(x); }); ord.sort(function (a, b) { return +b - +a; }); return ord.map(function (k) { return G[k]; }); }
  SV.levels = levels;

  /* ---------- Z atap tiap titik poligon: triangulasi (TIN) titik pick-up pita RL flitch; IDW radius = cadangan ---------- */
  /* 0.24.59 (pemilik 10-11-2026): Z atap = TRIANGULASI titik pick-up (interpolasi linear dalam segitiga, cara Surpac DTM,
     web-src/tinz.js). zMode 'idw' (nilai tersimpan proyek lama) kini berarti TIN; IDW radius tinggal sebagai 'idwr' dan
     sebagai cadangan di luar selubung titik. TIN di-cache per daftar titik Q. */
  var TINC = typeof WeakMap !== 'undefined' ? new WeakMap() : null;
  function zRoof(x, y, top, pr, Q) { if (pr.zMode === 'flat' || !Q.length) return top;
    if (pr.zMode !== 'idwr' && window.TINZ) { var tn = TINC && TINC.get(Q); if (tn === undefined) { tn = TINZ(Q) || null; if (TINC) TINC.set(Q, tn); }
      if (tn) { var v = tn.f(x, y); if (v != null && isFinite(v)) return v; } }
    return zIdw(x, y, top, pr, Q); }
  function zIdw(x, y, top, pr, Q) { var R = +pr.rIdw || 6, R2 = R * R, sw = 0, sz = 0, ex = null;
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
    var warn = [], info = [], nodes = [], byLv = [];
    /* 1. ring tiap poligon (CCW, z atap) */
    Lv.forEach(function (g, li) { var row = []; g.L.forEach(function (x) { if (x.on === false) return; var Pp = ccw(clean(x.pts)); if (Pp.length < 3) return; if (!simple(Pp)) warn.push('Poligon ' + (x.name || x.id) + ' RL ' + f2(x.top) + ' memotong dirinya sendiri: hasil di situ bisa cacat.');
      var Qb = ptsLv(g.top, +pr.zTol || 0.75).map(function (q) { return { x: q.x - offX, y: q.y - offY, z: q.z }; });
      var ring = Pp.map(function (q) { return V.add(q[0], q[1], zRoof(q[0], q[1], g.top, pr, Qb)); });
      var nd = { poly: x, lv: li, top: g.top, bot: g.bot, ring: ring, P: Pp, c: cen(Pp), kids: [], pars: [], Qb: Qb }; nodes.push(nd); row.push(nd); }); byLv.push(row); });
    if (!nodes.length) return { err: 'Belum ada poligon yang aktif.' };
    /* 1b. Poligon BERTAMPALAN di flitch yang sama (dig block dipasang dua kali karena lantai belum tuntas):
       keduanya tetap jadi solid sendiri-sendiri, sehingga bagian yang bertampalan TERHITUNG DUA KALI. Modul ini
       belum menggabungkan poligon; yang dilakukan: mengukur luas tampalan (kisi) dan volume gandanya, lalu memperingatkan. */
    var ovl = []; byLv.forEach(function (row) { for (var a = 0; a < row.length; a++) for (var b = a + 1; b < row.length; b++) { var A = row[a], Bn = row[b], bb = function (Pq) { var r = [1e18, -1e18, 1e18, -1e18]; Pq.forEach(function (q) { if (q[0] < r[0]) r[0] = q[0]; if (q[0] > r[1]) r[1] = q[0]; if (q[1] < r[2]) r[2] = q[1]; if (q[1] > r[3]) r[3] = q[1]; }); return r; }, ba = bb(A.P), b2 = bb(Bn.P), x0 = Math.max(ba[0], b2[0]), x1 = Math.min(ba[1], b2[1]), y0 = Math.max(ba[2], b2[2]), y1 = Math.min(ba[3], b2[3]); if (x1 <= x0 || y1 <= y0) continue;
        var st = Math.max(0.1, Math.sqrt((x1 - x0) * (y1 - y0)) / 90), n = 0; for (var x = x0 + st / 2; x < x1; x += st) for (var y = y0 + st / 2; y < y1; y += st) if (inPoly(A.P, x, y) && inPoly(Bn.P, x, y)) n++; var ar = n * st * st; if (ar < 0.5) continue;
        var mz = function (nd) { var t = 0; nd.ring.forEach(function (v) { t += V.z[v]; }); return t / nd.ring.length; }, za = mz(A), zb = mz(Bn), vd = ar * Math.max(0, Math.min(za, zb) - A.bot); ovl.push({ a: A.poly.id, b: Bn.poly.id, top: A.top, area: ar, vol: vd });
        warn.push('RL ' + f2(A.top) + ': poligon ' + (A.poly.name || A.poly.id) + ' dan ' + (Bn.poly.name || Bn.poly.id) + ' BERTAMPALAN ' + ar.toFixed(1) + ' m\u00b2 (atap rata-rata ' + za.toFixed(2) + ' dan ' + zb.toFixed(2) + '): sekitar ' + vd.toFixed(1) + ' m\u00b3 terhitung dua kali.'); } });
    /* 1c. GABUNG poligon bertampalan per flitch (par.gab, bawaan menyala). Atap gabungan = permukaan TERTINGGI:
       titik milik satu poligon memakai Z-nya sendiri; bila titik itu juga di dalam poligon lain, dibandingkan dengan
       permukaan poligon lain itu (triangulasi Z sudut-sudutnya) dan diambil yang lebih tinggi. Titik pick-up di dalam
       daerah tampalan yang lebih RENDAH dari permukaan tertinggi (pick-up susulan) tidak dipakai menurunkan atap. */
    if (pr.gab !== false && ovl.length) { var par2 = {}, find = function (k) { while (par2[k] && par2[k] !== k) k = par2[k]; return k; }, byId = {}; nodes.forEach(function (n) { byId[n.poly.id + '|' + n.lv] = n; par2[n.poly.id + '|' + n.lv] = n.poly.id + '|' + n.lv; });
      ovl.forEach(function (o) { var A = nodes.filter(function (n) { return n.poly.id === o.a && Math.abs(n.top - o.top) < 1e-6; })[0], Bn = nodes.filter(function (n) { return n.poly.id === o.b && Math.abs(n.top - o.top) < 1e-6; })[0]; if (A && Bn) { o._A = A; o._B = Bn; par2[find(A.poly.id + '|' + A.lv)] = find(Bn.poly.id + '|' + Bn.lv); } });
      var G = {}; nodes.forEach(function (n) { var r = find(n.poly.id + '|' + n.lv); (G[r] = G[r] || []).push(n); });
      Object.keys(G).forEach(function (r) { var M = G[r]; if (M.length < 2) return; var U = M[0].P, okU = true; for (var q = 1; q < M.length && okU; q++) { var u2 = polyUnion(U, M[q].P); if (!u2) okU = false; else U = u2; }
        var nmG = M.map(function (n) { return n.poly.name || n.poly.id; }).join(' + '); if (!okU) { warn.push('RL ' + f2(M[0].top) + ': ' + nmG + ' tidak bisa digabung otomatis (bentuk tampalannya rumit): tetap terpisah, volume tampalan terhitung dua kali.'); return; }
        U = ccw(clean(U)); var surf = M.map(function (n) { var L = n.ring.map(function (v) { return { x: V.x[v], y: V.y[v], z: V.z[v] }; }); var idwL = function (x, y) { var sw = 0, sz = 0; for (var i = 0; i < L.length; i++) { var dx = L[i].x - x, dy = L[i].y - y, d2 = dx * dx + dy * dy; if (d2 < 1e-8) return L[i].z; var w = 1 / d2; sw += w; sz += w * L[i].z; } return sz / sw; };
          /* permukaan poligon = triangulasi sudut-sudutnya (TIN), IDW hanya di luar selubung */ var tn = window.TINZ ? TINZ(L, { luar: idwL }) : null; return tn ? tn.f : idwL; });
        var hi = function (x, y) { var z = -1e18, k = 0; M.forEach(function (n, i) { var on = false; for (var e = 0; e < n.P.length && !on; e++) on = dSeg([x, y], n.P[e], n.P[(e + 1) % n.P.length]) < 1e-4; if (on || inPoly(n.P, x, y)) { var v = surf[i](x, y); if (v > z) z = v; k++; } }); return { z: z > -1e17 ? z : M[0].top, k: k }; };
        var ring = U.map(function (q) { return V.add(q[0], q[1], hi(q[0], q[1]).z); }), Qb = M[0].Qb.filter(function (q) { var h = hi(q.x, q.y); return h.k < 2 || q.z >= h.z - 1e-6; });
        var nd = { poly: { id: M.map(function (n) { return n.poly.id; }).join('+'), name: nmG }, lv: M[0].lv, top: M[0].top, bot: M[0].bot, ring: ring, P: U, c: cen(U), kids: [], pars: [], Qb: Qb, gab: M.length };
        nodes = nodes.filter(function (n) { return M.indexOf(n) < 0; }); nodes.push(nd); byLv[nd.lv] = byLv[nd.lv].filter(function (n) { return M.indexOf(n) < 0; }); byLv[nd.lv].push(nd);
        var ids = {}; M.forEach(function (n) { ids[n.poly.id] = 1; }); var arG = 0; ovl = ovl.filter(function (o) { if (ids[o.a] && ids[o.b] && Math.abs(o.top - nd.top) < 1e-6) { arG += o.area; return false; } return true; });
        warn = warn.filter(function (w) { return !(w.indexOf('BERTAMPALAN') >= 0 && w.indexOf('RL ' + f2(nd.top) + ':') === 0 && M.some(function (n) { return w.indexOf('poligon ' + (n.poly.name || n.poly.id) + ' dan ') >= 0; })); });
        info.push('RL ' + f2(nd.top) + ': ' + nmG + ' bertampalan ' + arG.toFixed(1) + ' m² → digabung jadi satu tubuh (atap = permukaan tertinggi).'); }); }
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
    return { V: V, IS: IS, warn: warn, info: info, ovl: ovl, nTri: T.length, date: new Date().toISOString() }; };
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
  SV.run = function () { var p = per(); if (!p) { alert('Tambah periode dulu.'); return; } if (!polysOf(p).length) { alert('Belum ada poligon di periode ini.'); return; } if (SV.ed) SV.edDone(); SV.busy = true; panel();
    setTimeout(function () { try { var R = SV.build(p); if (R.err) { SV.msg = '<span class=warn>' + E(R.err) + '</span>'; p.res = null; }
        else { p.res = { date: R.date, nTri: R.nTri, warn: R.warn, info: R.info || [], ovl: (R.ovl || []).map(function (o) { return { a: o.a, b: o.b, top: o.top, area: o.area, vol: o.vol }; }), IS: R.IS.map(function (s) { return { n: s.n, vol: s.vol, area: s.area, closed: s.closed, open: s.open, dup: s.dup, top: s.top, bot: s.bot, nPoly: s.nPoly, nLv: s.nLv, nt: s.tri.length, polys: s.polys, vis: true }; }) }; SV._R = R; SV._Rid = p.id; p.stale = false; reg(p, R); SV.msg = ''; }
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
  SV.setPar = function (k, v) { var p = per(); if (!p) return; P(p)[k] = v; if (['snap', 'reg', 'sg', 'aEdge'].indexOf(k) < 0) p.stale = true; dirty(); if (k === 'reg') { if (v) { var r = R(p); if (r) reg(p, r); } else unreg(p); updatePlot(); } panel(); };
  SV.setFilt = function (k, v) { D().filt[k] = v; dirty(); panel(); updatePlot(); };
  SV.fileOn = function (c, v) { var f = D().filt; f.off = f.off || {}; if (v) delete f.off[c]; else f.off[c] = 1; dirty();
    /* pemilik 10-11-2026: mencentang file harus langsung memperlihatkan titiknya, tanpa kembali ke menu Dig Block / As-Mined
       untuk mengganti flitch -> flitch kerja pindah ke flitch file itu (RL dari nama file). Pita RL manual tidak diganggu. */
    if (v && !bandMan()) { var fl = fileFl(c), B = lvB(); if (fl && isFinite(fl.top) && isFinite(fl.bot) && !(Math.abs(B[0] - fl.top) < 1e-3 && Math.abs(B[1] - fl.bot) < 1e-3 && lvOn())) { SV.goLv(fl.top, fl.bot); return; } }
    panel(); updatePlot(); };
  /* flitch kerja diatur dari panel ini sendiri (seperti As-Mined): tinggi, RL atas, RL bawah, Terapkan */
  SV.flSet = function (k, v) { var B = lvB(), x = parseFloat(v), t = B[0], b = B[1], fh = isFinite(t - b) && t > b ? t - b : 1.5; if (!isFinite(x)) return;
    if (k === 'fh') { if (x > 0 && isFinite(t)) b = t - x; } else if (k === 'top') { t = x; b = x - fh; } else b = x; if (!(t > b)) { alert('RL atas harus di atas RL bawah.'); panel(); return; }
    D().lv = { top: +(+t).toFixed(3), bot: +(+b).toFixed(3) }; dirty(); panel(); updatePlot(); };
  SV.flApply = function () { var B = lvB(); SV.goLv(B[0], B[1]); };
  /* Pembaca sendiri (tidak memakai pembaca As-Mined). CSV / TXT: pemisah , ; tab; dengan atau tanpa baris judul.
     Kolom E & N dikenali dari judul, atau -- tanpa judul -- dari besarannya (dua kolom berdampingan bernilai >= 1000);
     Z = kolom sesudah N, ID = kolom sebelum E, kode = kolom sesudah Z. STR / DXF lewat pembaca garis umum SA.readLines.
     UPSERT: file bernama sama MENGGANTI titik file itu (pick-up susulan / koreksi), file lain tidak tersentuh. */
  function bacaCsv(txt) { var L = String(txt).replace(/^﻿/, '').split(/\r?\n/).filter(function (l) { return l.trim() !== ''; }); if (!L.length) return []; var dl = ',', bn = -1; [',', ';', '\t'].forEach(function (c) { var n = L[0].split(c).length; if (n > bn) { bn = n; dl = c; } });
    var R = L.map(function (l) { return l.split(dl).map(function (v) { return v.trim().replace(/^"|"$/g, ''); }); }), num = function (v) { var x = parseFloat(String(v).replace(',', '.')); return isFinite(x) ? x : NaN; }, h = R[0], ix = -1, iy = -1, iz = -1, ii = -1, ic = -1, body = R;
    var col = function (re) { for (var k = 0; k < h.length; k++) if (re.test(h[k])) return k; return -1; };
    if (h.some(function (v) { return v !== '' && !isFinite(num(v)); }) && (col(/^(x|east|easting|e)$/i) >= 0)) { ix = col(/^(x|east|easting|e)$/i); iy = col(/^(y|north|northing|n)$/i); iz = col(/^(z|rl|elev|elevation|h|height)$/i); ii = col(/^(id|pt|point|ptid|point_?id|name|no|nama)$/i); ic = col(/^(code|kode|desc|description|keterangan|ket|remark|layer)$/i); body = R.slice(1); }
    if (ix < 0 || iy < 0) { body = R; var nc = 0; body.forEach(function (r) { if (r.length > nc) nc = r.length; }); var med = function (c) { var v = []; for (var q = 0; q < body.length && q < 200; q++) { var t = num(body[q][c]); if (isFinite(t)) v.push(Math.abs(t)); } if (!v.length) return NaN; v.sort(function (a, b) { return a - b; }); return v[v.length >> 1]; }, M = []; for (var c = 0; c < nc; c++) M.push(med(c));
      var j0 = -1; for (c = 0; c + 1 < nc; c++) if (M[c] >= 1000 && M[c + 1] >= 1000) { j0 = c; break; } if (j0 < 0) { j0 = isFinite(M[0]) && isFinite(M[1]) && isFinite(M[2]) && nc === 3 ? 0 : (nc >= 4 ? 1 : 0); } ix = j0; iy = j0 + 1; iz = j0 + 2 < nc ? j0 + 2 : -1; ii = j0 > 0 ? j0 - 1 : -1; ic = j0 + 3 < nc ? j0 + 3 : -1;
      /* baris pertama = judul hanya bila kolom E / N-nya bukan angka (kolom kode berisi teks spt 'OB' bukan tanda judul) */ if (!isFinite(num(h[ix])) || !isFinite(num(h[iy]))) body = R.slice(1); }
    var out = []; body.forEach(function (r) { var x = num(r[ix]), y = num(r[iy]), z = iz >= 0 ? num(r[iz]) : NaN; if (isFinite(x) && isFinite(y)) out.push({ x: x, y: y, z: z, id: ii >= 0 ? String(r[ii] || '') : '', c: ic >= 0 ? String(r[ic] || '') : '' }); }); return out; }
  SV.bacaCsv = bacaCsv;
  SV.importFiles = async function (files) { var L = Array.prototype.slice.call(files || []), d = D(), info = [], ganti = 0; pts();
    for (var i = 0; i < L.length; i++) { var f = L[i], ext = (f.name.split('.').pop() || '').toLowerCase(), Q = [];
      try { if (ext === 'str' || ext === 'dxf') { var segs = await SA.readLines({ f: f, k: ext }); segs.forEach(function (S) { S.forEach(function (q) { Q.push({ x: +q[0], y: +q[1], z: +q[2], id: '', c: '' }); }); }); } else Q = bacaCsv(await f.text()); } catch (e) { info.push('<span class=warn>' + E(f.name) + ': ' + E(e.message) + '</span>'); continue; }
      if (!Q.length) { info.push('<span class=warn>' + E(f.name) + ': tidak ada titik terbaca</span>'); continue; }
      var n0 = d.pts.length; d.pts = d.pts.filter(function (q) { return q.f !== f.name; }); var lama = n0 - d.pts.length; if (lama) ganti++; Q.forEach(function (q) { q.f = f.name; d.pts.push(q); }); var fl = fileFl(f.name);
      info.push(E(f.name) + ': ' + Q.length + ' titik' + (lama ? ' (mengganti ' + lama + ' titik lama file ini)' : '') + (fl ? ' &middot; RL ' + f2(fl.top) + '&ndash;' + f2(fl.bot) : ' &middot; <span class=warn>RL flitch belum dikenali, isi di tabel</span>')); }
    SV.msgPts = info.join('<br>'); dirty();
    /* pemilik 10-11-2026: selesai import, titik langsung tampil & siap didigit -> flitch kerja = flitch file terakhir yang
       terbaca (RL dari nama file), file itu dicentang, plan-nya dibuka. Pita RL manual tidak diganggu. */
    var akhir = null; for (var j = L.length - 1; j >= 0 && !akhir; j--) { var fj = fileFl(L[j].name); if (fj && pts().some(function (q) { return q.f === L[j].name; })) akhir = { c: L[j].name, fl: fj }; }
    if (akhir && !bandMan()) { var fo = d.filt.off || {}; delete fo[akhir.c]; SV.view(akhir.fl.top, akhir.fl.bot); return info; }
    panel(); tree(); updatePlot(); return info; };
  SV.import = function (inp) { if (!inp || !inp.files || !inp.files.length) return; var F = Array.prototype.slice.call(inp.files); inp.value = ''; SV.importFiles(F); };
  SV.clearPts = function () { if (!confirm('Hapus SEMUA titik atap Solid Vein? (Poligon yang sudah didigit tetap ada.)')) return; D().pts = []; SV.msgPts = ''; dirty(); panel(); tree(); updatePlot(); };
  SV.delFile = function (i) { var f = files()[i]; if (!f || !confirm('Hapus ' + f.n + ' titik dari file ' + f.c + '?')) return; D().pts = pts().filter(function (q) { return fname(q) !== f.c; }); dirty(); panel(); tree(); updatePlot(); };

  /* ---------- poligon: digit (snap titik atap), ambil dari as-mined / dig block ---------- */
  SV.dig = function () { var p = per(); if (!p) { alert('Tambah periode dulu.'); return; } if (!BX.m) { alert('Import block model dulu.'); return; }
    var B = lvB(); if (!isFinite(B[0])) { alert('Isi RL atas / bawah flitch kerja dulu (atau centang file titik atap).'); return; } if (!lvOn()) SV.view(B[0], B[1]); uiTab('SV'); DG.svm = p.id; if ($('dgDesc')) $('dgDesc').value = 'VEIN'; dgStart(); panel(); };
  /* snap ke titik atap dalam pita RL (9 px), dipanggil dgSnap2 lebih dulu */
  var _hook = window.dgSnapHook; window.dgSnapHook = function (A, px, py) { if (DG.svm) { var Q = ptsOn(), best = 9, res = null, pr = P(); if (pr.snap === false) return _hook ? _hook(A, px, py) : null;
      for (var i = 0; i < Q.length; i++) { var q = Q[i], pp = dgPx(A, q.x, q.y), dd = Math.hypot(pp[0] - px, pp[1] - py); if (dd < best) { best = dd; res = [q.x, q.y]; } } if (res) return res; }
    return _hook ? _hook(A, px, py) : null; };
  (function () { var _f = dgFinish; dgFinish = function (closed) { if (!DG.svm) return _f.apply(this, arguments); var pid = DG.svm, p = D().per.filter(function (q) { return q.id === pid; })[0];
      if (!closed) { alert('Poligon vein harus tertutup: klik titik pertama lagi atau tekan Enter.'); return; }
      if (!DG.on || DG.cur.length < 3) { alert('Poligon butuh minimal 3 titik.'); return; }
      var B = lvB(), o = p ? addPoly(p, DG.cur.map(function (q) { return [q[0], q[1]]; }), B[0], B[1], 'digit', 'V' + (p.polys.length + 1)) : null;
      DG.svm = null; dgCancel(); if (o) { dirty(); SV.msg = 'Poligon ' + E(o.name) + ' (' + N(Math.abs(sArea(o.pts)), 1) + ' m²) ditambahkan di flitch RL ' + f2(B[0]) + '–' + f2(B[1]) + '.'; } panel(); tree(); updatePlot(); }; })();
  (function () { var _c = dgCancel; dgCancel = function () { var r = _c.apply(this, arguments); if (DG.svm) { DG.svm = null; try { panel(); } catch (e) {} } return r; }; })();
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
  /* ---------- edit titik poligon (penyunting sendiri, tidak memakai penyunting dig block) ----------
     Bekerja di plan 2D flitch poligon itu. Kanvas tipis di atas plot menggambar bentuk yang sedang diedit;
     geser = seret titik (menempel ke titik atap <= 9 px bila snap menyala), sisip = seret pegangan tengah sisi,
     hapus = klik ganda / klik kanan titik (minimal 3 titik tersisa). Poligon baru dipakai sesudah Selesai. */
  function edCv() { var c = $('svCv'); if (c) return c; var host = $('plotDiv').parentNode; if (getComputedStyle(host).position === 'static') host.style.position = 'relative'; c = document.createElement('canvas'); c.id = 'svCv'; c.style.cssText = 'position:absolute;left:0;top:0;pointer-events:none;z-index:5'; host.appendChild(c); return c; }
  function edPix(A) { return SV.ed.pts.map(function (q) { return dgPx(A, q[0] + offX, q[1] + offY); }); }
  function edDraw() { var c = $('svCv'); if (!c) return; var gd = $('plotDiv'), hr = gd.parentNode.getBoundingClientRect(), gr = gd.getBoundingClientRect(), d = window.devicePixelRatio || 1; c.style.left = (gr.left - hr.left) + 'px'; c.style.top = (gr.top - hr.top) + 'px'; c.style.width = gr.width + 'px'; c.style.height = gr.height + 'px'; c.width = gr.width * d; c.height = gr.height * d; var x = c.getContext('2d'); x.setTransform(d, 0, 0, d, 0, 0); x.clearRect(0, 0, gr.width, gr.height);
    if (!SV.ed || !window.VIEW2D) return; var A = dgAx(); if (!A) return; var Pp = edPix(A), n = Pp.length; x.lineWidth = 2.5; x.strokeStyle = '#d6336c'; x.fillStyle = 'rgba(214,51,108,.10)'; x.beginPath(); Pp.forEach(function (q, i) { if (i) x.lineTo(q[0], q[1]); else x.moveTo(q[0], q[1]); }); x.closePath(); x.fill(); x.stroke();
    for (var i = 0; i < n; i++) { var a = Pp[i], b = Pp[(i + 1) % n], mx = (a[0] + b[0]) / 2, my = (a[1] + b[1]) / 2; x.fillStyle = '#fff'; x.strokeStyle = '#d6336c'; x.lineWidth = 1.5; x.fillRect(mx - 3.5, my - 3.5, 7, 7); x.strokeRect(mx - 3.5, my - 3.5, 7, 7); }
    Pp.forEach(function (q, i) { x.beginPath(); x.arc(q[0], q[1], i === SV.ed.drag ? 7 : 5, 0, 7); x.fillStyle = i === SV.ed.drag ? '#d6336c' : '#fff'; x.fill(); x.lineWidth = 2; x.strokeStyle = '#d6336c'; x.stroke(); }); }
  function edHit(A, px, py) { var Pp = edPix(A), n = Pp.length, i; for (i = 0; i < n; i++) if (Math.hypot(Pp[i][0] - px, Pp[i][1] - py) < 9) return { v: i }; for (i = 0; i < n; i++) { var a = Pp[i], b = Pp[(i + 1) % n]; if (Math.hypot((a[0] + b[0]) / 2 - px, (a[1] + b[1]) / 2 - py) < 8) return { m: i }; } return null; }
  function edMouse(e, type) { if (!SV.ed || !window.VIEW2D) return; var A = dgAx(); if (!A) return; var px = e.clientX - A.r.left, py = e.clientY - A.r.top, ed = SV.ed;
    if (type === 'down') { if (e.button !== 0) return; var h = edHit(A, px, py); if (!h) return; if (h.m !== undefined) { var a = ed.pts[h.m], b = ed.pts[(h.m + 1) % ed.pts.length]; ed.pts.splice(h.m + 1, 0, [(a[0] + b[0]) / 2, (a[1] + b[1]) / 2]); ed.drag = h.m + 1; } else ed.drag = h.v; ed.moved = true; e.stopPropagation(); e.preventDefault(); edDraw(); return; }
    if (type === 'move') { if (ed.drag < 0) return; var wx = A.x.p2d(px - A.x._offset), wy = A.y.p2d(py - A.y._offset); if (P().snap !== false) { var Q = ptsOn(), best = 9, hit = null; for (var i = 0; i < Q.length; i++) { var pp = dgPx(A, Q[i].x, Q[i].y), dd = Math.hypot(pp[0] - px, pp[1] - py); if (dd < best) { best = dd; hit = Q[i]; } } if (hit) { wx = hit.x; wy = hit.y; } }
      ed.pts[ed.drag] = [+(wx - offX).toFixed(3), +(wy - offY).toFixed(3)]; e.stopPropagation(); e.preventDefault(); edDraw(); return; }
    if (type === 'up') { if (ed.drag >= 0) { ed.drag = -1; edDraw(); e.stopPropagation(); } return; }
    if (type === 'del') { var h2 = edHit(A, px, py); if (h2 && h2.v !== undefined) { e.stopPropagation(); e.preventDefault(); if (ed.pts.length <= 3) return; ed.pts.splice(h2.v, 1); ed.moved = true; edDraw(); } } }
  (function () { var gd = $('plotDiv'); if (!gd) return; gd.addEventListener('mousedown', function (e) { edMouse(e, 'down'); }, true); window.addEventListener('mousemove', function (e) { edMouse(e, 'move'); }, true); window.addEventListener('mouseup', function (e) { edMouse(e, 'up'); }, true);
    gd.addEventListener('dblclick', function (e) { edMouse(e, 'del'); }, true); gd.addEventListener('contextmenu', function (e) { edMouse(e, 'del'); }, true); })();
  SV.edit = function (id) { var p = per(); if (!p) return; var v = p.polys.filter(function (x) { return x.id === id; })[0]; if (!v) return; if (SV.ed) SV.edDone(); if (window.DG && DG.on) dgCancel();
    var B = lvB(), sama = lvOn() && Math.abs(B[0] - v.top) < 1e-3 && Math.abs(B[1] - v.bot) < 1e-3; SV.ed = { id: id, pts: v.pts.map(function (q) { return [q[0], q[1]]; }), drag: -1, moved: false };
    if (!sama) SV.goLv(v.top, v.bot); var buka = function (k) { if (!SV.ed) return; if (!window.VIEW2D) { if (k === 0) toggle2D(); if (k < 30) setTimeout(function () { buka(k + 1); }, 200); return; } edCv(); edDraw(); }; setTimeout(function () { buka(0); }, sama ? 0 : 500);
    clearInterval(SV._edT); SV._edT = setInterval(function () { if (!SV.ed) { clearInterval(SV._edT); return; } if (SV.ed.drag < 0) edDraw(); }, 300); panel(); };
  SV.edDone = function (batal) { var ed = SV.ed; if (!ed) return; SV.ed = null; clearInterval(SV._edT); edDraw(); var p = per(), v = p && p.polys.filter(function (x) { return x.id === ed.id; })[0];
    if (v && !batal && ed.moved) { var Pn = clean(ed.pts); if (Pn.length < 3) { alert('Poligon butuh minimal 3 titik: perubahan dibatalkan.'); } else { if (!simple(Pn) && !confirm('Poligon hasil edit memotong dirinya sendiri. Tetap simpan?')) { SV.ed = ed; SV._edT = setInterval(function () { if (SV.ed && SV.ed.drag < 0) edDraw(); }, 300); edDraw(); return; }
        v.pts = Pn; v.key = Pn.map(function (q) { return q[0].toFixed(2) + ',' + q[1].toFixed(2); }).join(';'); if (v.src === 'auto') v.src = 'digit'; p.stale = true; SV.msg = 'Poligon ' + E(v.name || '') + ' diubah (' + Pn.length + ' titik, ' + N(Math.abs(sArea(Pn)), 1) + ' m\u00b2). Bangun solid lagi.'; dirty(); } }
    panel(); tree(); updatePlot(); };
  SV.delPoly = function (id) { var p = per(); if (!p) return; p.polys = p.polys.filter(function (x) { return x.id !== id; }); p.stale = true; if (SV.ed && SV.ed.id === id) SV.edDone(true); dirty(); panel(); tree(); updatePlot(); };
  SV.polyOn = function (id, v) { var p = per(); if (!p) return; p.polys.forEach(function (x) { if (x.id === id) x.on = v; }); p.stale = true; dirty(); panel(); updatePlot(); };
  /* buka plan flitch kerja Solid Vein: sayatan horizontal di RL itu (seperti lyApply), TANPA mengubah flitch Dig Block /
     As-Mined (lySet tidak disentuh). Flitch global yang sedang aktif dimatikan tampilannya supaya model yang tampak = RL ini. */
  SV.view = function (top, bot) { top = +top; bot = +bot; if (!(top > bot)) return; D().lv = { top: top, bot: bot }; dirty();
    try { if (window.DG && DG.on && !DG.svm) dgCancel(); if (window.BX && BX.ui && BX.ui.fl) { BX.ui.fl = false; BX.sc = {}; }
      $('sMode').value = 'H'; modeChanged(); $('pos').step = 'any'; $('pos').value = (top + bot) / 2; $('thick').value = +(top - bot).toFixed(3); $('sliceClip').checked = true;
      if (window.PT && PT.select && !/^sv(\.|$)/.test(PT.sel || '')) { try { PT.select('sv'); } catch (e) {} } uiTab('SV'); if (!window.VIEW2D) toggle2D(); else updatePlot(); if (window.bxPanel) bxPanel(); } catch (e) { console.error(e); } panel(); tree(); };
  SV.goLv = function (top, bot) { SV.view(top, bot); };
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
    var plan2 = false; try { plan2 = !!window.VIEW2D && secGeom().m === 'H'; } catch (e) { }
    Q.forEach(function (q) { var pp = { x: q.x - offX, y: q.y - offY, z: q.z }; if (clip && !plan2 && !inK(o.K, pp)) return; /* plan: titik sudah dipilih per flitch file, Z boleh di luar slab */ x.push(pp.x); y.push(pp.y); z.push(pp.z); h.push((q.id || q.c || '') + ' Z ' + (+q.z).toFixed(2)); });
    if (x.length) T.push({ type: 'scatter3d', mode: 'markers', x: x, y: y, z: z, hovertext: h, hoverinfo: 'text', name: 'Titik atap (' + x.length + ')', marker: { size: 2.6, color: '#c2185b', symbol: 'cross' }, showlegend: true });
    var p = per(); if (!p) return; p.polys.forEach(function (v, i) { if (v.on === false) return; var pts2 = v.pts.map(function (q) { return { x: q[0], y: q[1], z: v.top }; }); pts2.push(pts2[0]); var X = [], Y = [], Z = [], any = false;
      for (var k = 1; k < pts2.length; k++) { var sg = [pts2[k - 1], pts2[k]]; if (clip) { sg = clipSeg(pts2[k - 1], pts2[k], o.K); if (!sg) continue; } X.push(sg[0].x, sg[1].x, null); Y.push(sg[0].y, sg[1].y, null); Z.push(sg[0].z, sg[1].z, null); any = true; }
      if (any) T.push({ type: 'scatter3d', mode: 'lines', x: X, y: Y, z: Z, name: 'Vein ' + (v.name || i + 1) + ' RL ' + f2(v.top), line: { color: PAL[i % PAL.length], width: 5 }, hoverinfo: 'name', showlegend: true }); }); }

  /* ---------- Lihat di 3D: kamera diarahkan & didekatkan ke poligon + solid periode aktif ----------
     Tubuh vein hanya beberapa puluh meter, sedangkan adegan 3D selebar pit: tanpa ini solidnya memang
     tergambar tetapi cuma setitik. Kamera Plotly bekerja di koordinat kubus adegan, jadi kotak batas
     vein diubah dulu ke koordinat itu (rentang sumbu & rasio aspek yang sedang dipakai). */
  /* ================= REPORT BLOCK MODEL DI DALAM SOLID VEIN (pemilik 10-11-2026) =================
     "tambahkan satu subnode ... report block model mentah dengan constraint Solid Vein yang sudah terbentuk. Solid vein
     sendiri bisa disesuaikan periode cut off date-nya." Blok block model resmi (bukan as-mined) dihitung bila TITIK
     PUSATNYA di dalam solid periode itu (blok utuh, cara Surpac). Solid = hasil Bangun solid periode (ikut pilihan
     Kumulatif). Uji titik-di-dalam: sinar tegak ke atas, hitung segitiga yang dilewati (ganjil = di dalam), per pulau. */
  function inSolid(V, tri) { var x0 = 1e18, x1 = -1e18, y0 = 1e18, y1 = -1e18, z0 = 1e18, z1 = -1e18; tri.forEach(function (t) { t.forEach(function (i) { var x = V.x[i], y = V.y[i], z = V.z[i]; if (x < x0) x0 = x; if (x > x1) x1 = x; if (y < y0) y0 = y; if (y > y1) y1 = y; if (z < z0) z0 = z; if (z > z1) z1 = z; }); });
    var cs = Math.max(0.5, Math.sqrt(Math.max(1, (x1 - x0) * (y1 - y0)) / Math.max(1, tri.length / 4))), nx = Math.max(1, Math.ceil((x1 - x0) / cs)), ny = Math.max(1, Math.ceil((y1 - y0) / cs)), G = {};
    tri.forEach(function (t, k) { var a = t[0], b = t[1], c = t[2], i0 = Math.floor((Math.min(V.x[a], V.x[b], V.x[c]) - x0) / cs), i1 = Math.floor((Math.max(V.x[a], V.x[b], V.x[c]) - x0) / cs), j0 = Math.floor((Math.min(V.y[a], V.y[b], V.y[c]) - y0) / cs), j1 = Math.floor((Math.max(V.y[a], V.y[b], V.y[c]) - y0) / cs);
      for (var i = i0; i <= i1; i++) for (var j = j0; j <= j1; j++) (G[i + '|' + j] = G[i + '|' + j] || []).push(k); });
    return { b: [x0, x1, y0, y1, z0, z1], f: function (px, py, pz) { if (px < x0 || px > x1 || py < y0 || py > y1 || pz < z0 || pz > z1) return false; px += 1.37e-7; py += 2.71e-7; var L = G[Math.floor((px - x0) / cs) + '|' + Math.floor((py - y0) / cs)]; if (!L) return false; var n = 0;
        for (var q = 0; q < L.length; q++) { var t = tri[L[q]], a = t[0], b = t[1], c = t[2], ax = V.x[a], ay = V.y[a], bx = V.x[b], by = V.y[b], cx = V.x[c], cy = V.y[c], den = (by - cy) * (ax - cx) + (cx - bx) * (ay - cy); if (Math.abs(den) < 1e-12) continue;
          var wa = ((by - cy) * (px - cx) + (cx - bx) * (py - cy)) / den, wb = ((cy - ay) * (px - cx) + (ax - cx) * (py - cy)) / den, wc = 1 - wa - wb; if (wa < 0 || wb < 0 || wc < 0) continue; if (wa * V.z[a] + wb * V.z[b] + wc * V.z[c] > pz) n++; } return (n & 1) === 1; } }; }
  SV.rep = SV.rep || { cuts: '0', gr: '' };
  SV.repHitung = function (p) { var r = R(p), m = BX.m; if (!r || !m) return null; var U = BX.ui || {}, sgA = U.sgCol && m.num[U.sgCol] ? m.num[U.sgCol] : null, sg0 = +U.sg || 2.6;
    var EL = (window.elList ? elList(U.attr) : [U.attr]).filter(function (a) { return a && m.num[a]; }); if (!EL.length) EL = Object.keys(m.num).slice(0, 1);
    var gr = SV.rep.gr && m.num[SV.rep.gr] ? SV.rep.gr : EL[0]; if (EL.indexOf(gr) < 0) EL.unshift(gr);
    var IS = r.IS.map(function (s) { var o = inSolid(r.V, s.tri); o.n = s.n; o.vol = s.vol; o.closed = s.closed; return o; }), Lv = levels(p), B = [], t0 = Date.now();
    for (var i = 0; i < m.n; i++) { var x = m.x[i] - offX, y = m.y[i] - offY, z = m.z[i]; for (var k = 0; k < IS.length; k++) { if (IS[k].f(x, y, z)) { var sg = sgA && isFinite(sgA[i]) && sgA[i] > 0 ? sgA[i] : sg0, v = m.sx[i] * m.sy[i] * m.sz[i], lv = null;
            for (var q = 0; q < Lv.length; q++) if (z <= Lv[q].top + 1e-9 && z > Lv[q].bot - 1e-9) { lv = Lv[q]; break; } B.push({ i: i, isl: IS[k].n, lv: lv ? f2(lv.top) + ' – ' + f2(lv.bot) : 'di luar flitch poligon', lvt: lv ? lv.top : -1e9, v: v, t: v * sg }); break; } } }
    var cuts = String(SV.rep.cuts || '0').split(/[;,\s]+/).map(Number).filter(isFinite); if (!cuts.length) cuts = [0]; cuts.sort(function (a, b) { return a - b; });
    var agg = function (L) { var o = { n: L.length, v: 0, t: 0, g: {} }, w = {}; L.forEach(function (b) { o.v += b.v; o.t += b.t; EL.forEach(function (e) { var val = m.num[e][b.i]; if (isFinite(val)) { o.g[e] = (o.g[e] || 0) + val * b.t; w[e] = (w[e] || 0) + b.t; } }); }); EL.forEach(function (e) { o.g[e] = w[e] ? o.g[e] / w[e] : NaN; }); return o; };
    var G = m.num[gr], pass = function (c) { return B.filter(function (b) { var g = G[b.i]; return isFinite(g) && g >= c; }); };
    var byKey = function (L, key) { var M = {}, ord = []; L.forEach(function (b) { var k = b[key]; if (!M[k]) { M[k] = []; ord.push(k); } M[k].push(b); }); return ord.map(function (k) { return { k: k, a: agg(M[k]), s: M[k][0] }; }); };
    var c0 = cuts[0], L0 = pass(c0); return { p: p, EL: EL, gr: gr, cuts: cuts.map(function (c) { return { c: c, a: agg(pass(c)) }; }), all: agg(B), nB: B.length, isl: byKey(L0, 'isl').sort(function (a, b) { return a.k - b.k; }), lv: byKey(L0, 'lv').sort(function (a, b) { return b.s.lvt - a.s.lvt; }), c0: c0,
      volSolid: r.IS.reduce(function (t, s) { return t + (s.vol || 0); }, 0), open: r.IS.filter(function (s) { return !s.closed; }).length, ms: Date.now() - t0 }; };
  SV.repTsv = function (H) { var rows = [['Periode', H.p.name, 'Cut-off date', (H.p.from || '') + ' s/d ' + (H.p.to || '')]], hd = function (k) { return [k, 'Blok', 'Volume (m3)', 'Ton'].concat(H.EL); }, ln = function (lab, a) { return [lab, a.n, a.v.toFixed(1), a.t.toFixed(1)].concat(H.EL.map(function (e) { return isFinite(a.g[e]) ? a.g[e].toFixed(4) : ''; })); };
    rows.push([]); rows.push(hd('Cut-off ' + H.gr)); H.cuts.forEach(function (c) { rows.push(ln('>= ' + c.c, c.a)); });
    rows.push([]); rows.push(hd('Pulau (cut-off ' + H.c0 + ')')); H.isl.forEach(function (g) { rows.push(ln('#' + g.k, g.a)); });
    rows.push([]); rows.push(hd('Flitch RL (cut-off ' + H.c0 + ')')); H.lv.forEach(function (g) { rows.push(ln(g.k, g.a)); }); return rows.map(function (r) { return r.join('\t'); }).join('\r\n'); };
  SV.report = function (pid) { var d = D(), p = pid ? d.per.filter(function (q) { return q.id === pid; })[0] : per(); if (!p) { alert('Pilih periode dulu.'); return; } if (!BX.m) { alert('Import block model dulu.'); return; }
    if (!p.res) { alert('Periode ' + p.name + ' belum punya solid. Buka "Parameter & bangun" lalu tekan Bangun solid.'); return; }
    var H = SV.repHitung(p); if (!H) { alert('Solid periode ini tidak bisa dibaca ulang. Bangun solid lagi.'); return; } SV._repH = H; SV._repP = p.id;
    var m = BX.m, nums = Object.keys(m.num), tb = function (judul, L, lab) { return '<h4 style="margin:8px 0 4px">' + judul + '</h4><table class=gxtb><tr><th>' + lab + '</th><th>Blok</th><th>Volume (m&sup3;)</th><th>Ton</th>' + H.EL.map(function (e) { return '<th>' + E(e) + '</th>'; }).join('') + '</tr>' +
        L.map(function (o) { var a = o.a; return '<tr' + (o.tot ? ' class=tot' : '') + '><td>' + E(o.lab) + '</td><td>' + N(a.n) + '</td><td>' + N(a.v, 1) + '</td><td>' + N(a.t, 1) + '</td>' + H.EL.map(function (e) { return '<td>' + (isFinite(a.g[e]) ? N(a.g[e], 3) : '-') + '</td>'; }).join('') + '</tr>'; }).join('') + '</table>'; };
    var h = '<div class=hint style="margin-bottom:6px">Periode <b>' + E(p.name) + '</b>' + (p.from || p.to ? ' &middot; cut-off date ' + E(p.from || '?') + ' s/d ' + E(p.to || '?') : '') + (P(p).kum ? ' &middot; <b>kumulatif</b> (poligon periode sebelumnya ikut)' : '') + ' &middot; ' + r2(H) + '</div>' +
      '<div class=g3 style="align-items:end"><div><label>Atribut cut-off</label><select onchange="SV.rep.gr=this.value;SV.report(\'' + p.id + '\')">' + nums.map(function (a) { return '<option' + (a === H.gr ? ' selected' : '') + '>' + E(a) + '</option>'; }).join('') + '</select></div><div><label>Cut-off (pisah koma)</label><input type=text value="' + E(SV.rep.cuts) + '" onchange="SV.rep.cuts=this.value;SV.report(\'' + p.id + '\')"></div><div style="display:flex;gap:4px"><button onclick="SV.repCopy()">Salin ke Excel</button><button onclick="SV.repCsv()">CSV</button></div></div>' +
      tb('Grade &times; tonase per cut-off (' + E(H.gr) + ')', H.cuts.map(function (c) { return { lab: '≥ ' + c.c, a: c.a }; }), 'Cut-off') +
      tb('Per pulau solid (cut-off ' + H.c0 + ')', H.isl.map(function (g) { return { lab: 'Pulau #' + g.k, a: g.a }; }), 'Pulau') +
      tb('Per flitch RL (cut-off ' + H.c0 + ')', H.lv.map(function (g) { return { lab: g.k, a: g.a }; }), 'Flitch RL') +
      '<div class=hint id=svRepMsg>Blok <b>utuh</b> dihitung bila titik pusatnya di dalam solid (cara Surpac); kadar tertimbang tonase; SG ' + (BX.ui.sgCol && m.num[BX.ui.sgCol] ? 'kolom ' + E(BX.ui.sgCol) : 'tetap ' + E(BX.ui.sg || 2.6)) + '. Volume solid ' + N(H.volSolid, 1) + ' m&sup3; vs volume blok terhitung ' + N(H.all.v, 1) + ' m&sup3; (selisih = blok di tepi solid).' + (H.open ? ' <span class=warn>' + H.open + ' pulau tidak tertutup: hasil untuk pulau itu tidak andal.</span>' : '') + '</div>';
    var w = (window.POP && POP.win) ? POP.win('svRepPop', 'Report block model dalam Solid Vein — ' + p.name, h) : null; if (w && !w._pos) { w._pos = 1; w.style.left = '440px'; w.style.top = '90px'; w.style.width = 'min(820px,calc(100vw - 460px))'; } };
  function r2(H) { return N(H.nB) + ' blok di dalam solid (' + H.ms + ' ms)'; }
  SV.repCopy = function () { var H = SV._repH; if (!H) return; var t = SV.repTsv(H), ok = false; try { var a = document.createElement('textarea'); a.value = t; a.style.position = 'fixed'; a.style.opacity = '0'; document.body.appendChild(a); a.select(); ok = document.execCommand('copy'); a.remove(); } catch (e) {} var e2 = $('svRepMsg'); if (e2) e2.insertAdjacentHTML('afterbegin', ok ? '<b>Tersalin</b> &mdash; tempel (Ctrl+V) di Excel. ' : 'Gagal menyalin. '); };
  SV.repCsv = function () { var H = SV._repH; if (!H) return; var t = SV.repTsv(H).split('\r\n').map(function (l) { return l.split('\t').map(function (v) { return /[;"]/.test(v) ? '"' + v.replace(/"/g, '""') + '"' : v.replace('.', ','); }).join(';'); }).join('\r\n');
    dgDl('﻿' + t + '\r\n', ('Report_BM_SolidVein_' + (H.p.name || 'periode')).replace(/[^A-Za-z0-9_-]+/g, '_') + '.csv', 'text/csv'); };
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
    var d = D(), p = per(), pr = P(p), B = lvB(), fl = lvOn(), bd = band(), F = files(), on = ptsOn(bd), off = d.filt.off || {};
    var h = '<div class=hint style="margin-bottom:6px"><b>Trial.</b> Tubuh vein aktual: poligon per flitch (didigit dari titik pick-up atap) + titik pick-up atap &rarr; solid wireframe tertutup (cara Surpac: semua titik dipakai, luas permukaan minimum, validasi tertutup).</div>';
    /* periode */
    h += sec('per', 'Periode', '<div class=svrow><select onchange="SV.selPer(this.value)" title="Periode aktif">' + (d.per.length ? d.per.map(function (q) { return '<option value="' + E(q.id) + '"' + (q.id === d.cur ? ' selected' : '') + '>' + E(q.name) + (q.polys.length ? ' · ' + q.polys.length + ' pol' : '') + '</option>'; }).join('') : '<option value="">(belum ada periode)</option>') + '</select><button onclick="SV.addPer()" title="Periode baru (mingguan / bulanan)">+ Periode</button>' + (p ? '<button onclick="var v=prompt(\'Nama periode:\',\'' + E(p.name).replace(/'/g, '') + '\');if(v)SV.renPer(\'' + p.id + '\',v)" title="Ganti nama">&#9998;</button><button class=x onclick="SV.delPer(\'' + p.id + '\')" title="Hapus periode">&times;</button>' : '') + '</div>' +
      (p ? '<div class=g2><div><label>Dari tanggal</label><input type=date value="' + E(p.from) + '" onchange="SV.per().from=this.value;SV.dirty()"></div><div><label>Sampai</label><input type=date value="' + E(p.to) + '" onchange="SV.per().to=this.value;SV.dirty()"></div></div><div class=hint>Tanggal hanya catatan periode. Data menu ini <b>berdiri sendiri</b>: tidak mengambil apa pun dari Dig Block maupun As-Mined.</div>' : '<div class=hint>Klik <b>+ Periode</b> untuk mulai. Semua poligon & solid dikelompokkan per periode.</div>'));
    if (!p) { el.innerHTML = h; return; }
    /* titik atap */
    h += sec('pts', 'Titik atap (pick-up roof)', '<div class=svrow><label class=svbtn><input type=file multiple accept=".csv,.txt,.str,.dxf" style="display:none" onchange="SV.import(this)">Import titik atap (CSV / STR / DXF)&hellip;</label>' + (pts().length ? '<button class=x onclick="SV.clearPts()" title="Hapus semua titik atap">&times;</button>' : '') + '</div>' +
      (pts().length ? '<table class=pltb style="margin-top:4px"><tr><th></th><th>File</th><th>Titik</th><th>Z titik</th><th>RL atas</th><th>RL bawah</th><th></th></tr>' + F.map(function (f, i) { var cur = fl && isFinite(f.top) && Math.abs(f.top - B[0]) < 1e-3 && Math.abs(f.bot - B[1]) < 1e-3; return '<tr' + (cur ? ' class=svcur' : '') + '><td><input type=checkbox ' + (off[f.c] ? '' : 'checked') + ' onchange="SV.fileOn(SV.files()[' + i + '].c,this.checked)" title="Pakai file ini"></td><td title="' + E(f.c) + '" style="max-width:92px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">' + E(f.c) + '</td><td>' + N(f.n) + '</td><td><small>' + (f.n && f.z1 >= f.z0 ? f2(f.z0) + '&ndash;' + f2(f.z1) : '-') + '</small></td>' +
          '<td><input type=number step=any style="width:54px" value="' + (isFinite(f.top) ? f.top : '') + '" onchange="SV.setFl(' + i + ',\'top\',this.value)" title="RL atas flitch file ini (dibaca dari nama file; bisa dikoreksi)"></td><td><input type=number step=any style="width:54px" value="' + (isFinite(f.bot) ? f.bot : '') + '" onchange="SV.setFl(' + i + ',\'bot\',this.value)"></td>' +
          '<td>' + (isFinite(f.top) ? '<button onclick="SV.goLv(' + f.top + ',' + f.bot + ')" title="Jadikan flitch kerja Solid Vein & buka plan-nya">Buka</button>' + '<button class=x onclick="SV.delFile(' + i + ')" title="Hapus titik file ini">&times;</button>' : '<span class=warn title="Nama file tidak memuat RL flitch: isi RL atas & bawah">?</span>') + '</td></tr>'; }).join('') + '</table>' +
        (SV.msgPts ? '<div class=hint>' + SV.msgPts + '</div>' : '') +
        '<div class=hint>Import ulang file <b>bernama sama</b> mengganti titik file itu (pick-up susulan / koreksi); file lain tidak berubah. RL flitch dibaca dari <b>nama file</b> (mis. <code>&hellip;_235-5_234_&hellip;</code> = RL 235,5&ndash;234) dan menentukan titik mana milik flitch mana &mdash; bukan dari Z titiknya, karena atap galian nyata naik-turun melewati batas flitch.</div>' +
        '<div class=g3><div><label>RL min</label><input type=number step=any value="' + (d.filt.z0 === undefined || d.filt.z0 === '' ? '' : d.filt.z0) + '" placeholder="' + f2(bd[0]) + '" onchange="SV.setFilt(\'z0\',this.value)"></div><div><label>RL maks</label><input type=number step=any value="' + (d.filt.z1 === undefined || d.filt.z1 === '' ? '' : d.filt.z1) + '" placeholder="' + f2(bd[1]) + '" onchange="SV.setFilt(\'z1\',this.value)"></div><div><label>&nbsp;</label><button onclick="SV.setFilt(\'z0\',\'\');SV.setFilt(\'z1\',\'\')" title="Kosongkan = titik milik flitch aktif (menurut file)">Auto</button></div></div>' +
        '<div class=hint>' + N(on.length) + ' dari ' + N(pts().length) + ' titik dipakai untuk ' + (bandMan() ? 'pita RL ' + f2(bd[0]) + '&ndash;' + f2(bd[1]) : 'flitch kerja RL ' + f2(B[0]) + '&ndash;' + f2(B[1])) + '. Titik ini jadi sasaran <b>snap</b> saat mendigit dan sumber Z atap tiap sudut poligon. RL min / maks hanya diisi bila ingin menyaring manual.</div>' : '<div class=hint>Belum ada titik atap. Import pick-up survey atap galian (ID, X, Y, Z, kode) atau STR/DXF.</div>'));
    /* poligon */
    var Lv = levels(p);
    var Ff = F.filter(function (f) { return isFinite(f.top) && isFinite(f.bot) && !off[f.c]; }), seenF = {};
    h += sec('poly', 'Poligon per flitch', '<div class=g3><div><label>Tinggi flitch</label><input type=number step=any value="' + f2(B[0] - B[1]) + '" onchange="SV.flSet(\'fh\',this.value)"></div><div><label>RL atas</label><input type=number step=any value="' + B[0] + '" onchange="SV.flSet(\'top\',this.value)"></div><div><label>RL bawah</label><input type=number step=any value="' + B[1] + '" onchange="SV.flSet(\'bot\',this.value)"></div></div>' +
      (Ff.length ? '<div class=svrow style="margin-top:4px"><label style="margin:0">Flitch dari file titik:</label>' + Ff.filter(function (f) { var k = f.top + '|' + f.bot; if (seenF[k]) return false; seenF[k] = 1; return true; }).sort(function (a, b) { return b.top - a.top; }).map(function (f) { var cur = fl && Math.abs(f.top - B[0]) < 1e-3 && Math.abs(f.bot - B[1]) < 1e-3; return '<button' + (cur ? ' class=btn-pri' : '') + ' onclick="SV.goLv(' + f.top + ',' + f.bot + ')" title="Jadikan flitch kerja & buka plan-nya">RL ' + f2(f.top) + '&ndash;' + f2(f.bot) + '</button>'; }).join('') + '</div>' : '') +
      '<button class="' + (fl ? '' : 'btn-pri') + '" style="width:100%;margin-top:4px" onclick="SV.flApply()">' + (fl ? '&#10003; Flitch kerja RL ' + f2(B[0]) + '&ndash;' + f2(B[1]) + ' di Sayatan 2D' : 'Buka plan flitch kerja (2D)') + '</button>' +
      '<div class=hint>Flitch kerja Solid Vein <b>milik menu ini sendiri</b> &mdash; tidak mengubah dan tidak bergantung pada flitch Dig Block / As-Mined. Mencentang file titik langsung memindah flitch kerja ke flitch file itu dan membuka plan-nya. Satu poligon per pulau per flitch; snap ke titik atap otomatis.</div>' +
      '<div><button class=btn-pri style="width:100%" onclick="SV.dig()" ' + (DG.svm ? 'disabled' : '') + ' title="Digit poligon tertutup di plan flitch kerja Solid Vein (snap ke titik atap). Klik titik pertama lagi / Enter untuk menutup.">' + (DG.svm ? '&#9679; Mendigit&hellip;' : 'Digit poligon') + '</button></div>' +
      '<div class=g2 style="margin-top:4px"><button onclick="SV.auto()" ' + (pts().length ? '' : 'disabled') + ' title="Usulan poligon untuk SEMUA file ber-flitch: garis luar gugus titik pick-up (alpha shape). Periksa hasilnya di plan; hapus & digit ulang yang tidak cocok.">Garis luar otomatis (semua file)</button><div><label>Sisi terpanjang (m)</label><input type=number step=any min=1 value="' + pr.aEdge + '" onchange="SV.setPar(\'aEdge\',+this.value)" title="Dua titik dianggap satu tubuh bila bisa dihubungkan segitiga dengan sisi <= ini. Kecil = mengikuti lekuk & memisah pulau; besar = lebih membulat & menyatukan."></div></div>' +
      (DG.svm ? '<div class=hint><label class=sw><input type=checkbox ' + (pr.snap === false ? '' : 'checked') + ' onchange="SV.setPar(\'snap\',this.checked)">Snap ke titik atap</label> &middot; <button onclick="dgUndo()">Undo titik</button> <button onclick="dgCancel()">Batal</button></div>' : '') +
      (SV.ed ? '<div class=hint style="border-left:3px solid var(--ac);padding-left:6px"><b>&#9998; Mengedit titik poligon.</b> Seret titik bulat untuk menggeser (menempel ke titik atap), seret kotak kecil di tengah sisi untuk menyisip titik, klik ganda / klik kanan titik untuk menghapusnya. <button class=btn-pri onclick="SV.edDone()">Selesai</button> <button onclick="SV.edDone(true)">Batal</button></div>' : '') +
      (Lv.length ? '<table class=pltb style="margin-top:4px"><tr><th></th><th>Flitch</th><th>Nama</th><th>Titik</th><th>Luas</th><th>Sumber</th><th></th></tr>' + Lv.map(function (g) { return g.L.map(function (v, i) { return '<tr' + (Math.abs(g.top - B[0]) < 1e-6 && fl ? ' class=svcur' : '') + '><td><input type=checkbox ' + (v.on === false ? '' : 'checked') + ' onchange="SV.polyOn(\'' + v.id + '\',this.checked)" title="Ikut dibangun"></td>' + (i === 0 ? '<td rowspan=' + g.L.length + '><a href="javascript:void(0)" onclick="SV.goLv(' + g.top + ',' + g.bot + ')" title="Buka flitch ini">RL ' + f2(g.top) + '<br><small>' + f2(g.bot) + '</small></a></td>' : '') + '<td>' + E(v.name || '-') + '</td><td>' + v.pts.length + '</td><td>' + N(Math.abs(sArea(v.pts)), 0) + ' m&sup2;</td><td><small>' + ({ digit: 'digit', am: 'as-mined', db: 'dig block', auto: 'garis luar' }[v.src] || v.src) + '</small></td><td style="white-space:nowrap"><button onclick="SV.edit(\'' + v.id + '\')" title="Edit titik: geser (snap ke titik atap), sisip di tengah sisi, hapus titik"' + (SV.ed && SV.ed.id === v.id ? ' class=btn-pri' : '') + '>&#9998;</button><button class=x onclick="SV.delPoly(\'' + v.id + '\')" title="Hapus">&times;</button></td></tr>'; }).join(''); }).join('') + '</table>' + '<button style="margin-top:4px;width:100%" onclick="SV.lihat()" title="Poligon digambar di RL atas flitchnya; kamera 3D didekatkan ke sana">Lihat poligon di 3D</button>' : '<div class=hint>Belum ada poligon.</div>'));
    /* parameter */
    h += sec('par', 'Parameter solid', '<div class=g2><div><label>Jarak sambung maks (m)</label><input type=number step=any min=0 value="' + pr.dmax + '" onchange="SV.setPar(\'dmax\',+this.value)" title="Poligon dua flitch berurutan disambung bila jarak datarnya <= ini; lebih jauh = pulau terpisah (ditutup sendiri)"></div><div><label>Metode sambung (Surpac)</label><select onchange="SV.setPar(\'method\',this.value)"><option value=min' + (pr.method === 'min' ? ' selected' : '') + '>Luas permukaan minimum</option><option value=equi' + (pr.method === 'equi' ? ' selected' : '') + '>Equi-angular</option><option value=prop' + (pr.method === 'prop' ? ' selected' : '') + '>Proporsional keliling</option></select></div></div>' +
      '<div class=g3><div><label>Z atap sudut poligon</label><select onchange="SV.setPar(\'zMode\',this.value)"><option value=idw' + (pr.zMode === 'idw' || pr.zMode === 'tin' ? ' selected' : '') + '>Triangulasi (TIN) titik atap &middot; seperti Surpac</option><option value=idwr' + (pr.zMode === 'idwr' ? ' selected' : '') + '>IDW radius (cara lama)</option><option value=flat' + (pr.zMode === 'flat' ? ' selected' : '') + '>Datar = RL atas flitch</option></select></div><div><label title="Dipakai untuk IDW radius, dan sebagai cadangan TIN di luar jangkauan titik">Radius IDW / cadangan (m)</label><input type=number step=any min=0.1 value="' + pr.rIdw + '" onchange="SV.setPar(\'rIdw\',+this.value)"></div><div><label>Pita RL titik &plusmn; (m)</label><input type=number step=any min=0 value="' + pr.zTol + '" onchange="SV.setPar(\'zTol\',+this.value)" title="Titik atap yang dipakai untuk flitch = yang Z-nya dalam ± ini dari RL atas flitch"></div></div>' +
      '<div class=g2><div><label class=sw><input type=checkbox ' + (pr.capPts ? 'checked' : '') + ' onchange="SV.setPar(\'capPts\',this.checked)">Atap pulau teratas ikut titik pick-up di dalam poligon</label></div><div><label>SG (t/m&sup3;)</label><input type=number step=any min=0 value="' + pr.sg + '" onchange="SV.setPar(\'sg\',+this.value)"></div></div>' +
      '<div><label class=sw title="Poligon yang bertampalan di flitch yang sama (dig block dipasang ulang karena lantai belum tuntas) digabung jadi satu tubuh; atap memakai permukaan tertinggi, sehingga tampalan tidak terhitung dua kali"><input type=checkbox ' + (pr.gab === false ? '' : 'checked') + ' onchange="SV.setPar(\'gab\',this.checked)">Gabung poligon bertampalan (atap = permukaan tertinggi)</label></div>' +
      '<div><label class=sw title="Poligon periode-periode sebelumnya (urutan daftar periode) ikut dibangun, supaya galian baru menyambung ke tubuh yang sudah ada"><input type=checkbox ' + (pr.kum ? 'checked' : '') + ' onchange="SV.setPar(\'kum\',this.checked)">Kumulatif: ikutkan poligon periode sebelumnya</label></div>' +
      '<div class=g2><button class=btn-pri onclick="SV.run()" ' + (SV.busy || !polysOf(p).length ? 'disabled' : '') + '>' + (SV.busy ? 'Membangun&hellip;' : 'Bangun solid') + '</button><label class=sw title="Solid ikut Wireframe geologi: tampil di 3D/sayatan dan bisa jadi batas domain Reporting"><input type=checkbox ' + (pr.reg ? 'checked' : '') + ' onchange="SV.setPar(\'reg\',this.checked)">Daftarkan ke Wireframe geologi</label></div>' + (SV.msg ? '<div class=hint>' + SV.msg + '</div>' : ''));
    /* hasil */
    var r = p.res, sg = +pr.sg || 0;
    h += sec('res', 'Hasil: solid per pulau', r ? ((p.stale ? '<div class=hint><span class=warn><b>Poligon / titik berubah sesudah solid ini dibangun.</b> Klik <b>Bangun solid</b> lagi.</span></div>' : '') + (r.ovl && r.ovl.length ? '<div class=hint><span class=warn>Volume ganda karena poligon bertampalan: &plusmn; ' + N(r.ovl.reduce(function (a, o) { return a + o.vol; }, 0), 1) + ' m&sup3; (sudah termasuk di total di bawah).</span></div>' : '') + '<div class=hint>' + N(r.nTri) + ' segitiga &middot; ' + r.IS.length + ' pulau &middot; dibangun ' + new Date(r.date).toLocaleString() + '</div>' + (r.info && r.info.length ? '<div class=hint>' + r.info.map(E).join('<br>') + '</div>' : '') + (r.warn && r.warn.length ? '<div class=hint><span class=warn>' + r.warn.map(E).join('<br>') + '</span></div>' : '') +
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
      var st = { s: 'Periode', t: 'Solid Vein Aktual (trial)', dur: 7, el: '.ptr[data-id="sv"], #pSV', d: 'Node khusus, berdiri sendiri: poligon tiap flitch didigit dari titik pick-up atap, disambung cara Surpac menjadi solid tertutup per pulau, dilihat di 3D dan dihitung volumenya. Sub-node Report block model dalam solid menghitung grade x tonase block model resmi di dalam solid periode itu.',
        run: function (A) { A(0, function () { try { if (window.PT && PT.select) PT.select('sv'); } catch (e) {} }); } };
      var k = S.length - 1; while (k > 0 && S[k].s !== 'Penutup') k--; if (k <= 0) k = S.length; S.splice(k, 0, st); return S; }; })();

  /* ---------- Project Tree: node khusus ---------- */
  window.svTree = function () { var d = D(), p = per(), per2 = d.per, nP = per2.length;
    var kids = per2.map(function (q) { var Lv = levels(q), r = q.res; return { id: 'sv.p.' + q.id, t: q.name, ic: 'folder', fold: 1, tab: 'SV', b: (q.polys.length ? q.polys.length + ' pol' : '') + (r ? ' · ' + r.IS.length + ' solid' : ''), go: function () { if (d.cur !== q.id) SV.selPer(q.id); SV.focus('per'); }, rename: function (nm) { SV.renPer(q.id, nm); }, del: function () { SV.delPer(q.id); },
        menu: function () { return [{ t: 'Lihat di 3D (zoom ke vein)', fn: function () { SV.selPer(q.id); SV.lihat(); }, dis: !q.polys.length }, { t: 'Bangun solid', fn: function () { SV.selPer(q.id); SV.run(); }, dis: !q.polys.length }, { sep: 1 }, { t: 'Export DTM + STR Surpac', fn: function () { SV.selPer(q.id); SV.expDtm(); }, dis: !r }, { t: 'Export DXF 3DFACE', fn: function () { SV.selPer(q.id); SV.expDxf(); }, dis: !r }, { t: 'Export CSV volume', fn: function () { SV.selPer(q.id); SV.expCsv(); }, dis: !r }, { sep: 1 }, { t: 'Ganti nama…', fn: function () { var v = prompt('Nama periode:', q.name); if (v) SV.renPer(q.id, v); } }, { t: 'Hapus periode…', danger: 1, fn: function () { SV.delPer(q.id); } }]; },
        kids: [{ id: 'sv.p.' + q.id + '.pts', t: 'Titik atap', ic: 'pts', tab: 'SV', b: pts().length ? N(ptsOn().length) + '/' + N(pts().length) : '', dim: !pts().length, go: function () { SV.selPer(q.id); SV.focus('pts'); }, hint: 'Pick-up roof: import, filter pita RL, pilih file' },
          { id: 'sv.p.' + q.id + '.poly', t: 'Poligon per flitch', ic: 'poly', tab: 'SV', b: q.polys.length ? Lv.length + ' flitch' : '', dim: !q.polys.length, go: function () { SV.selPer(q.id); SV.focus('poly'); }, hint: 'Digit (snap titik atap), ambil dari as-mined / dig block', fold: 1,
            kids: Lv.map(function (g) { return { id: 'sv.p.' + q.id + '.lv.' + g.top.toFixed(3), t: 'RL ' + f2(g.top) + ' – ' + f2(g.bot), ic: 'flitch', tab: 'SV', b: g.L.length + ' pol', go: function () { SV.selPer(q.id); SV.goLv(g.top, g.bot); SV.focus('poly'); } }; }),
            add: { t: '+ Digit poligon di flitch kerja', fn: function () { SV.selPer(q.id); SV.dig(); } } },
          { id: 'sv.p.' + q.id + '.par', t: 'Parameter & bangun', ic: 'gear', tab: 'SV', go: function () { SV.selPer(q.id); SV.focus('par'); }, hint: 'Jarak sambung maks, metode Surpac, Z atap, SG' },
          { id: 'sv.p.' + q.id + '.rep', t: 'Report block model dalam solid', ic: 'report', dim: !r, b: r ? 'BM mentah' : 'bangun solid dulu', go: function () { SV.selPer(q.id); SV.report(q.id); }, hint: 'Grade × tonase block model resmi di dalam solid periode ini (cut-off date periode), per cut-off, pulau & flitch' },
          { id: 'sv.p.' + q.id + '.res', t: 'Solid (' + (r ? r.IS.length : 0) + ')', ic: 'solid', tab: 'SV', dim: !r, go: function () { SV.selPer(q.id); SV.focus('res'); }, hint: 'Volume & tonase per pulau, export DTM/STR/DXF/CSV', fold: 1,
            kids: r ? r.IS.map(function (s) { return { id: 'sv.p.' + q.id + '.isl.' + s.n, t: 'Pulau #' + s.n + ' RL ' + f2(s.top) + '–' + f2(s.bot), ic: 'solid', tab: 'SV', b: N(s.vol, 0) + ' m³' + (s.closed ? '' : ' · terbuka'), chk: s.vis !== false, onChk: function (v) { SV.islVis(s.n, v); }, go: function () { SV.selPer(q.id); SV.focus('res'); } }; }) : [] }] }; });
    return [{ id: 'sv', step: '11', st: nP ? (per2.some(function (q) { return q.res; }) ? 'done' : 'part') : 'opt', t: 'Solid Vein Aktual (trial)', ic: 'solid', fold: 1, tab: 'SV', b: nP ? nP + ' periode' : 'trial', chk: SV.show, onChk: function (v) { SV.show = v; try { var hid = {}; D().per.forEach(function (q) { ((q.res || {}).IS || []).forEach(function (z) { if (z.vis === false) hid[q.id + '|' + z.n] = 1; }); }); (MD.models || []).forEach(function (m) { if (m.sv) m.vis = v && !hid[m.sv + '|' + m.svn]; }); MD.ver++; MD.sc = {}; if (window.mdList) mdList(); } catch (e) {} updatePlot(); }, hint: 'Tubuh vein yang benar-benar tergali: poligon per flitch + titik atap → solid wireframe tertutup (cara Surpac)',
      go: function () { SV.focus(''); }, kids: kids, add: { t: '+ Tambah periode…', fn: function () { SV.addPer(); } },
      menu: function () { return [{ t: 'Tambah periode…', fn: function () { SV.addPer(); } }, { t: 'Bangun solid periode aktif', fn: function () { SV.run(); }, dis: !p || !p.polys.length }]; } }]; };
})();
