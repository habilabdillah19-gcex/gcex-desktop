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
  T.build = function (src) {
    if (!T.on || !src || !src.x || src.x.length < 3 || typeof Delaunator === 'undefined') return null;
    var c = T._wm && T._wm.get(src); if (c && c.n === src.x.length) return c.tin;
    var t0 = performance.now(), P = kumpul(src, T.cap), m = P.x.length; if (m < 3) return null;
    var co = new Float64Array(m * 2); for (var i = 0; i < m; i++) { co[2 * i] = P.x[i]; co[2 * i + 1] = P.y[i]; }
    var tri; try { tri = new Delaunator(co).triangles; } catch (e) { console.warn('[TIN] gagal', e); return null; }
    var nt = tri.length / 3, L = new Float64Array(nt), q, a, b2, c2;
    var ed = function (p, r) { var dx = P.x[p] - P.x[r], dy = P.y[p] - P.y[r]; return dx * dx + dy * dy; };
    for (q = 0; q < nt; q++) { a = tri[3 * q]; b2 = tri[3 * q + 1]; c2 = tri[3 * q + 2]; L[q] = Math.max(ed(a, b2), ed(b2, c2), ed(c2, a)); }
    var srt = Float64Array.from(L).sort(), med = srt[Math.floor(nt / 2)] || 0, lim = med * T.faktor * T.faktor, keep = 0;
    for (q = 0; q < nt; q++) if (!(L[q] > lim && lim > 0)) keep++;
    var I = new Uint32Array(keep), J = new Uint32Array(keep), K = new Uint32Array(keep), w = 0;
    for (q = 0; q < nt; q++) { if (L[q] > lim && lim > 0) continue; I[w] = tri[3 * q]; J[w] = tri[3 * q + 1]; K[w] = tri[3 * q + 2]; w++; }
    var tin = { x: Float64Array.from(P.x), y: Float64Array.from(P.y), z: Float64Array.from(P.z), i: I, j: J, k: K, n: m, dari: P.dari, segitiga: keep, dibuang: nt - keep, ms: Math.round(performance.now() - t0) };
    T.stat = tin; if (T._wm) T._wm.set(src, { n: src.x.length, tin: tin });
    return tin;
  };
  /* trace mesh3d siap pakai: warna seragam (color) atau gradasi elevasi (intensity+colorscale) */
  T.trace = function (src, opt) {
    var tin = T.build(src); if (!tin) return null; opt = opt || {};
    var t = { type: 'mesh3d', x: tin.x, y: tin.y, z: tin.z, i: tin.i, j: tin.j, k: tin.k, opacity: opt.opacity == null ? 1 : opt.opacity, showscale: false, hoverinfo: 'skip', flatshading: opt.flat !== false, showlegend: false, lighting: opt.lighting || { ambient: 0.7, diffuse: 0.6, specular: 0.05, roughness: 0.9 } };
    if (opt.grad) { t.intensity = tin.z; t.colorscale = opt.colorscale || 'Earth'; } else t.color = opt.color || '#b9a58c';
    if (opt.name) t.name = opt.name; if (opt.uid) t.uid = opt.uid;
    return t;
  };
  T.info = function () { var s = T.stat; return s ? (s.n.toLocaleString('id-ID') + ' titik dari ' + s.dari.toLocaleString('id-ID') + ', ' + s.segitiga.toLocaleString('id-ID') + ' segitiga, ' + s.ms + ' ms') : '-'; };
})();
