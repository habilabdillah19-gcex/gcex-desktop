/* GC-Ex — PERMUKAAN TOPOGRAFI & DESAIN PIT RESOLUSI PENUH (TIN) — Block Model & Drill Hole (0.24.50 / 0.24.57)
   =============================================================================================================
   Permintaan pemilik (10 Nov 2026): tampilan permukaan topo / pit / ortho tidak boleh berkualitas jelek; lekuk harus terlihat.

   Sebelumnya permukaan topo & pit digambar sebagai mesh3d TANPA indeks: Plotly men-triangulasi sendiri (Delaunay) setiap kali
   trace berubah, dan karena itu jumlah titiknya dibatasi (15.000 titik; HR.topoMesh mendesimasi per sel sesuai tampilan). Dua
   akibat: (1) lekuk kecil hilang — survei 33.000 titik hanya tampil separuh; (2) setiap zoom men-triangulasi ulang.

   Modul ini membangun TIN SEKALI per sumber titik dari SELURUH titik (sampai TIN.cap, bawaan 400.000) dengan Delaunator
   (ISC, web-src/delaunator.min.js), lalu trace memakai i/j/k tetap: Plotly tidak men-triangulasi lagi, geometrinya sama
   persis pada semua zoom, dan glskip bisa melewatinya saat tidak berubah.

   - Titik duplikat / sangat berdekatan (< 1e-3 m) disatukan supaya triangulasi stabil.
   - Segitiga "sliver" di tepi cekung (sisi terpanjang > TIN.faktor x median sisi, bawaan 8) dibuang supaya tidak ada
     kipas lebar menyeberangi lubang / tepi data kontur. Angka ini hanya memengaruhi gambar, bukan topoZ / reporting.
   - Cache per objek sumber (WeakMap) + panjang; data baru (prep ulang) membuat TIN baru.
   - Bila Delaunator tidak ada atau gagal, pemanggil memakai cara lama (mesh tanpa indeks). */
(function () {
  var T = window.TIN = { on: true, cap: 400000, faktor: 8, _wm: (typeof WeakMap !== 'undefined') ? new WeakMap() : null, stat: null };
  function kumpul(src, cap) {
    var n = src.x.length, X = [], Y = [], Z = [], i, x, y;
    var b = src.b || null, area = b ? Math.max(1, (b.x1 - b.x0) * (b.y1 - b.y0)) : 0;
    var nn = 0; for (i = 0; i < n; i++) if (src.x[i] !== null && isFinite(src.z[i])) nn++;
    /* lebih dari cap: satu titik per sel (bukan "tiap ke-n") supaya sebaran merata; <= cap: semua titik */
    var cell = (nn > cap && area) ? Math.sqrt(area / cap) : 0, seen = cell ? new Set() : null;
    var dup = new Set();
    for (i = 0; i < n; i++) {
      x = src.x[i]; if (x === null) continue; y = src.y[i]; var z = src.z[i]; if (!isFinite(x) || !isFinite(y) || !isFinite(z)) continue;
      var kd = (Math.round(x * 1000)) + ':' + (Math.round(y * 1000)); if (dup.has(kd)) continue; dup.add(kd);
      if (cell) { var kc = Math.floor((x - b.x0) / cell) + ':' + Math.floor((y - b.y0) / cell); if (seen.has(kc)) continue; seen.add(kc); }
      X.push(x); Y.push(y); Z.push(z);
    }
    return { x: X, y: Y, z: Z, dari: nn };
  }
  /* BM 0.24.83 (pemilik 14 Nov 2026, pit Zona 4 "bentuknya kusut"): file DXF berisi 3DFACE = DTM Surpac yang SUDAH
     ditriangulasi. Dulu tiap segitiga dibaca sebagai string tertutup, dirapatkan, lalu ditriangulasi ULANG (Delaunay 2D) ->
     dinding jenjang kusut dan Z hitungan tidak sama dengan DTM Surpac. Kini segitiga asli dipakai apa adanya, untuk
     tampilan (T.build) maupun hitungan (TINZ.of, SA.surfGrid).
     T.soup(src) -> { x, y, z, i, j, k, ... } bila >= 80 % string sumber adalah segitiga / segi empat tertutup; selain itu null. */
  var SWM = typeof WeakMap !== 'undefined' ? new WeakMap() : null;
  T.soup = function (src) {
    if (!src || !src.x || src.x.length < 80) return null; var c = SWM && SWM.get(src); if (c && c.n === src.x.length) return c.s;
    var n = src.x.length, nStr = 0, nF = 0, F = [], s = -1, i, t0 = performance.now();
    for (i = 0; i <= n; i++) { var nul = i === n || src.x[i] === null || src.x[i] === undefined;
      if (!nul) { if (s < 0) s = i; continue; } if (s < 0) continue;
      var len = i - s, e = i - 1; nStr++;
      if ((len === 4 || len === 5) && src.x[s] === src.x[e] && src.y[s] === src.y[e] && src.z[s] === src.z[e]) { nF++; F.push(s, s + 1, s + 2); if (len === 5) F.push(s, s + 2, s + 3); }
      s = -1; }
    var out = null;
    if (nF >= 20 && nF >= 0.8 * nStr) { var M = new Map(), X = [], Y = [], Z = [], I = [], J = [], K = [];
      var vid = function (q) { var k = Math.round(src.x[q] * 1000) + ':' + Math.round(src.y[q] * 1000) + ':' + Math.round(src.z[q] * 1000), v = M.get(k); if (v === undefined) { v = X.length; M.set(k, v); X.push(src.x[q]); Y.push(src.y[q]); Z.push(src.z[q]); } return v; };
      for (i = 0; i < F.length; i += 3) { var a = vid(F[i]), b = vid(F[i + 1]), d = vid(F[i + 2]); if (a === b || b === d || a === d) continue; I.push(a); J.push(b); K.push(d); }
      if (I.length >= 20) out = { x: Float64Array.from(X), y: Float64Array.from(Y), z: Float64Array.from(Z), i: Uint32Array.from(I), j: Uint32Array.from(J), k: Uint32Array.from(K), n: X.length, dari: X.length, segitiga: I.length, dibuang: 0, soup: 1, ms: Math.round(performance.now() - t0) }; }
    if (SWM) SWM.set(src, { n: n, s: out }); return out;
  };
  T.build = function (src) {
    if (!T.on || !src || !src.x || src.x.length < 3) return null;
    var sp = T.soup(src); if (sp) { T.stat = sp; return sp; }
    if (typeof Delaunator === 'undefined') return null;
    var c = T._wm && T._wm.get(src); if (c && c.n === src.x.length) return c.tin;
    var t0 = performance.now(), P = kumpul(src, T.cap), m = P.x.length; if (m < 3) return null;
    var co = new Float64Array(m * 2); for (var i = 0; i < m; i++) { co[2 * i] = P.x[i]; co[2 * i + 1] = P.y[i]; }
    var dl, tri; try { dl = new Delaunator(co); tri = dl.triangles; } catch (e) { console.warn('[TIN] gagal', e); return null; }
    var nt = tri.length / 3, L = new Float64Array(nt), q, a, b2, c2;
    var ed = function (p, r) { var dx = P.x[p] - P.x[r], dy = P.y[p] - P.y[r]; return dx * dx + dy * dy; };
    for (q = 0; q < nt; q++) { a = tri[3 * q]; b2 = tri[3 * q + 1]; c2 = tri[3 * q + 2]; L[q] = Math.max(ed(a, b2), ed(b2, c2), ed(c2, a)); }
    var srt = Float64Array.from(L).sort(), med = srt[Math.floor(nt / 2)] || 0, lim = med * T.faktor * T.faktor, keep = 0;
    /* 13 Nov 2026 (pemilik: "jelek sekali bentuknya", lubang putih di topografi): segitiga panjang HANYA dikupas dari tepi
       luar (mulai dari segitiga di tepi hull, merambat lewat tetangga yang juga panjang) — kipas di tepi cekung / celah
       data tetap hilang, tetapi segitiga panjang di bagian DALAM (lantai pit datar, kontur jarang) tidak lagi berlubang.
       Seperti Pit Studio (tinFrom tanpa pembuangan). Hanya tampilan; hitungan memakai tinz.js. */
    var buang = new Uint8Array(nt), H = dl.halfedges, antre = [];
    if (lim > 0) { for (q = 0; q < nt; q++) if (L[q] > lim && (H[3 * q] < 0 || H[3 * q + 1] < 0 || H[3 * q + 2] < 0)) { buang[q] = 1; antre.push(q); }
      while (antre.length) { var t = antre.pop(); for (var e2 = 0; e2 < 3; e2++) { var o = H[3 * t + e2]; if (o < 0) continue; var u = (o / 3) | 0; if (!buang[u] && L[u] > lim) { buang[u] = 1; antre.push(u); } } } }
    for (q = 0; q < nt; q++) if (!buang[q]) keep++;
    var I = new Uint32Array(keep), J = new Uint32Array(keep), K = new Uint32Array(keep), w = 0;
    for (q = 0; q < nt; q++) { if (buang[q]) continue; I[w] = tri[3 * q]; J[w] = tri[3 * q + 1]; K[w] = tri[3 * q + 2]; w++; }
    var tin = { x: Float64Array.from(P.x), y: Float64Array.from(P.y), z: Float64Array.from(P.z), i: I, j: J, k: K, n: m, dari: P.dari, segitiga: keep, dibuang: nt - keep, ms: Math.round(performance.now() - t0) };
    T.stat = tin; if (T._wm) T._wm.set(src, { n: src.x.length, tin: tin });
    return tin;
  };
  /* 13 Nov 2026: titik string DESAIN PIT dirapatkan tiap `step` m sebelum ditriangulasi (cara Pit Studio surfOf ->
     densify(pts,2)). Tanpa ini segitiga Delaunay menghubungkan titik jauh di crest dan toe yang berbeda sehingga bidang
     jenjang bergerigi. Sumber {x,y,z} (string dipisah null) -> objek baru yang sama bentuknya (cache per objek sumber). */
  var RWM = typeof WeakMap !== 'undefined' ? new WeakMap() : null;
  T.rapat = function (src, step) {
    if (!src || !src.x || !src.x.length) return src; if (T.soup(src)) return src; /* segitiga DTM asli: tidak dirapatkan */ step = step || 2; var c = RWM && RWM.get(src); if (c && c.n === src.x.length && c.s === step) return c.o;
    /* hanya sumber STRING (ada pemisah null antar-string, seperti .str / .dxf); awan titik XYZ / CSV tidak dirapatkan —
       titik berurutan di sana tidak tersambung sebagai garis */
    var adaPisah = false; for (var q0 = 0; q0 < src.x.length; q0++) if (src.x[q0] === null || src.x[q0] === undefined) { adaPisah = true; break; }
    if (!adaPisah) { if (RWM) RWM.set(src, { n: src.x.length, s: step, o: src }); return src; }
    var X = [], Y = [], Z = [], px = null, py = null, pz = null, n = src.x.length;
    for (var i = 0; i < n; i++) { var x = src.x[i], y = src.y[i], z = src.z[i];
      if (x === null || x === undefined || !isFinite(x) || !isFinite(y) || !isFinite(z)) { if (px !== null) { X.push(null); Y.push(null); Z.push(null); } px = null; continue; }
      if (px !== null) { var d = Math.hypot(x - px, y - py), m = Math.ceil(d / step); for (var k = 1; k < m; k++) { var t = k / m; X.push(px + (x - px) * t); Y.push(py + (y - py) * t); Z.push(pz + (z - pz) * t); } }
      X.push(x); Y.push(y); Z.push(z); px = x; py = y; pz = z; }
    var o = { x: X, y: Y, z: Z }; if (src.b) o.b = src.b; if (RWM) RWM.set(src, { n: n, s: step, o: o }); return o;
  };
  /* trace mesh3d siap pakai: warna seragam (color) atau gradasi elevasi (intensity+colorscale) */
  T.trace = function (src, opt) {
    var tin = T.build(src); if (!tin) return null; opt = opt || {};
    var t = { type: 'mesh3d', x: tin.x, y: tin.y, z: tin.z, i: tin.i, j: tin.j, k: tin.k, opacity: opt.opacity == null ? 1 : opt.opacity, showscale: false, hoverinfo: 'skip', flatshading: opt.flat !== false, showlegend: false, lighting: opt.lighting || { ambient: 0.7, diffuse: 0.6, specular: 0.05, roughness: 0.9 } };
    var hs = opt.shade != null ? opt.shade : T.shadeMode();
    if (hs !== 'plotly' && T.hillshade(t, tin, opt, hs)) { if (opt.name) t.name = opt.name; if (opt.uid) t.uid = opt.uid; return t; }
    if (opt.grad) { t.intensity = tin.z; t.colorscale = opt.colorscale || 'Earth'; } else t.color = opt.color || '#a7b58a';
    if (opt.name) t.name = opt.name; if (opt.uid) t.uid = opt.uid;
    return t;
  };
  /* ---- HILLSHADE per segitiga (pemilik 12 Nov 2026: "shading yang jelas dan terlihat") ----
     Warna tiap segitiga = warna dasar x (ambient + (1 - ambient) x max(0, normal . arah cahaya)), cahaya matahari dari
     azimut 315 (barat laut), elevasi 45 derajat -- konvensi hillshade peta. Warna dipanggang ke facecolor dan lampu Plotly
     dimatikan (ambient 1, diffuse 0), jadi lereng, jenjang pit dan punggungan tetap tegas dari sudut kamera mana pun.
     Mode 'kuat' (bawaan) / 'lembut' / 'plotly' (lampu Plotly lama) dari pilihan #ovShade di panel Overlay. */
  T.shadeMode = function () { var e = document.getElementById('ovShade'); return (e && e.value) || 'kuat'; };
  var EARTH = [[0, [0, 0, 130]], [0.1, [0, 180, 180]], [0.2, [40, 210, 40]], [0.4, [230, 230, 50]], [0.6, [120, 70, 20]], [1, [255, 255, 255]]];
  function rgb(c) {
    if (Array.isArray(c)) return c;
    c = String(c || '').trim(); var m;
    if ((m = /^#([0-9a-f]{6})$/i.exec(c))) { var v = parseInt(m[1], 16); return [v >> 16 & 255, v >> 8 & 255, v & 255]; }
    if ((m = /^#([0-9a-f]{3})$/i.exec(c))) return [0, 1, 2].map(function (k) { return parseInt(m[1][k] + m[1][k], 16); });
    if ((m = /rgba?\(([^)]+)\)/i.exec(c))) return m[1].split(',').slice(0, 3).map(function (x) { return +x; });
    return [167, 181, 138];
  }
  function skala(cs) { if (!Array.isArray(cs)) return EARTH; return cs.map(function (p) { return [+p[0], rgb(p[1])]; }); }
  function ambil(S, u) {
    if (!(u > 0)) return S[0][1]; if (u >= 1) return S[S.length - 1][1];
    for (var k = 1; k < S.length; k++) if (u <= S[k][0]) { var a = S[k - 1], b = S[k], w = (u - a[0]) / ((b[0] - a[0]) || 1);
      return [a[1][0] + (b[1][0] - a[1][0]) * w, a[1][1] + (b[1][1] - a[1][1]) * w, a[1][2] + (b[1][2] - a[1][2]) * w]; }
    return S[S.length - 1][1];
  }
  T.hillshade = function (t, tin, opt, mode) {
    var I = tin.i, J = tin.j, K = tin.k, X = tin.x, Y = tin.y, Z = tin.z, nt = I.length;
    if (!nt) return false;
    var amb = mode === 'lembut' ? 0.55 : 0.32, az = (opt.az != null ? opt.az : 315) * Math.PI / 180, al = (opt.alt != null ? opt.alt : 45) * Math.PI / 180;
    var Lx = Math.cos(al) * Math.sin(az), Ly = Math.cos(al) * Math.cos(az), Lz = Math.sin(al);
    var base = rgb(opt.color || '#a7b58a'), S = opt.grad ? skala(opt.colorscale) : null, z0 = Infinity, z1 = -Infinity, q;
    if (S) { for (q = 0; q < Z.length; q++) { if (Z[q] < z0) z0 = Z[q]; if (Z[q] > z1) z1 = Z[q]; } }
    var FC = new Array(nt);
    for (q = 0; q < nt; q++) {
      var a = I[q], b = J[q], c = K[q];
      var ux = X[b] - X[a], uy = Y[b] - Y[a], uz = Z[b] - Z[a], vx = X[c] - X[a], vy = Y[c] - Y[a], vz = Z[c] - Z[a];
      var nx = uy * vz - uz * vy, ny = uz * vx - ux * vz, nz = ux * vy - uy * vx, L = Math.sqrt(nx * nx + ny * ny + nz * nz) || 1;
      if (nz < 0) { nx = -nx; ny = -ny; nz = -nz; }
      var d = (nx * Lx + ny * Ly + nz * Lz) / L, f = amb + (1 - amb) * (d > 0 ? d : 0);
      var col = S ? ambil(S, ((Z[a] + Z[b] + Z[c]) / 3 - z0) / ((z1 - z0) || 1)) : base;
      FC[q] = 'rgb(' + Math.round(col[0] * f) + ',' + Math.round(col[1] * f) + ',' + Math.round(col[2] * f) + ')';
    }
    t.facecolor = FC; t.flatshading = true;
    t.lighting = { ambient: 1, diffuse: 0, specular: 0, roughness: 1, fresnel: 0 };
    delete t.color; delete t.intensity;
    return true;
  };
  T.info = function () { var s = T.stat; return s ? (s.n.toLocaleString('id-ID') + ' titik dari ' + s.dari.toLocaleString('id-ID') + ', ' + s.segitiga.toLocaleString('id-ID') + ' segitiga, ' + s.ms + ' ms') : '-'; };
})();
