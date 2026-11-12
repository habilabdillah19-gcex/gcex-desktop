/* ================= BOOLEAN MESH (MFB) -- dipakai GC-Ex Drill Hole & GC-Ex Block Model =================
   Pembungkus web-src/manifold.js (manifold-3d, Apache-2.0, WASM tertanam; aplikasi tetap offline).
   Format mesh "datar": { v: Float64Array [x0,y0,z0, x1,...] koordinat DUNIA, t: Uint32Array [a0,b0,c0, ...], nv, nt } --
   sama dengan MD.models. Semua operasi menggeser koordinat ke pusat bersama (presisi float32 di UTM), membalik
   orientasi bila volume bertanda negatif, dan membuang bagian bervolume praktis nol (serpihan ujung pinch-out).
     MFB.load()          -> Promise (WASM dimuat asinkron sekali; Chrome tidak mengizinkan kompilasi besar sinkron)
     MFB.ok()            -> true bila sudah siap
     MFB.union(L)        -> {bodies:[flat...], vol, nSerpih}   (satu tubuh per bagian terhubung)
     MFB.ops(A, B, Z)    -> irisan & selisih dua kumpulan mesh: {AnB, AmB, BmA} (masing-masing {bodies, vol}); Z (opsional)
                            membatasi B HANYA untuk B - A (zona penilaian ore loss)
     MFB.zona(L, c)      -> Manifold ekstrusi poligon ber-offset (dipakai rekonsiliasi Solid Vein) -- internal
   Galat (mesh tidak tertutup) dilempar sebagai Error berbahasa Indonesia. */
(function () {
  if (window.MFB) return;
  var MFB = window.MFB = { mod: null, err: '', _p: null };
  MFB.ok = function () { return !!MFB.mod; };
  MFB.load = function () {
    if (MFB._p) return MFB._p;
    if (!window.__MF_MODULE || !window.__MF_WASM_B64) { MFB.err = 'pustaka boolean tidak tertanam di build ini'; return (MFB._p = Promise.reject(new Error(MFB.err))); }
    MFB._p = new Promise(function (ok, gagal) {
      try {
        var s = atob(window.__MF_WASM_B64), b = new Uint8Array(s.length);
        for (var i = 0; i < s.length; i++) b[i] = s.charCodeAt(i);
        window.__MF_MODULE({ wasmBinary: b }).then(function (W) { W.setup(); MFB.mod = W; ok(W); },
          function (e) { MFB.err = 'pustaka boolean gagal dimuat: ' + (e && e.message || e); gagal(e); });
      } catch (e) { MFB.err = 'pustaka boolean gagal dimuat: ' + e.message; gagal(e); }
    });
    MFB._p.catch(function (e) { console.error(e); });
    return MFB._p;
  };

  function pusat(L) {
    var c = [0, 0, 0], n = 0;
    L.forEach(function (m) { for (var i = 0; i < m.nv; i += 5) { c[0] += m.v[3 * i]; c[1] += m.v[3 * i + 1]; c[2] += m.v[3 * i + 2]; n++; } });
    return n ? c.map(function (v) { return v / n; }) : c;
  }
  function keMf(W, m, c) {
    var n = m.nv, vp = new Float32Array(n * 3), tv = new Uint32Array(m.t), i, vol = 0;
    for (i = 0; i < n; i++) { vp[3 * i] = m.v[3 * i] - c[0]; vp[3 * i + 1] = m.v[3 * i + 1] - c[1]; vp[3 * i + 2] = m.v[3 * i + 2] - c[2]; }
    for (i = 0; i < m.nt; i++) {
      var a = tv[3 * i], b = tv[3 * i + 1], d = tv[3 * i + 2];
      vol += vp[3 * a] * (vp[3 * b + 1] * vp[3 * d + 2] - vp[3 * b + 2] * vp[3 * d + 1]) - vp[3 * a + 1] * (vp[3 * b] * vp[3 * d + 2] - vp[3 * b + 2] * vp[3 * d]) + vp[3 * a + 2] * (vp[3 * b] * vp[3 * d + 1] - vp[3 * b + 1] * vp[3 * d]);
    }
    if (vol < 0) for (i = 0; i < m.nt; i++) { var t = tv[3 * i + 1]; tv[3 * i + 1] = tv[3 * i + 2]; tv[3 * i + 2] = t; }
    var ms = new W.Mesh({ numProp: 3, vertProperties: vp, triVerts: tv }), mf = null;
    try { mf = new W.Manifold(ms); } catch (e) { mf = null; }
    if (!mf || mf.status() !== 'NoError') {
      if (mf) mf.delete();
      try { ms.merge(); mf = new W.Manifold(ms); } catch (e) { throw new Error((m.name || 'solid') + ' bukan mesh tertutup (manifold)'); }
      if (mf.status() !== 'NoError') { var st = mf.status(); mf.delete(); throw new Error((m.name || 'solid') + ' bukan mesh tertutup (' + st + ')'); }
    }
    return mf;
  }
  function keDatar(U, c) {
    var g = U.getMesh(), np = g.numProp, nv = g.vertProperties.length / np, v = new Float64Array(nv * 3);
    for (var i = 0; i < nv; i++) { v[3 * i] = g.vertProperties[i * np] + c[0]; v[3 * i + 1] = g.vertProperties[i * np + 1] + c[1]; v[3 * i + 2] = g.vertProperties[i * np + 2] + c[2]; }
    return { v: v, t: new Uint32Array(g.triVerts), nv: nv, nt: g.triVerts.length / 3 };
  }
  /* Manifold -> tubuh-tubuh datar (bagian terhubung, besar dulu), serpihan dibuang */
  function pecah(U, c) {
    var tot = Math.abs(U.volume()), lim = Math.max(1e-3, 1e-7 * tot), P = U.decompose(), out = [], buang = 0;
    P.forEach(function (p) { var v = p.volume(); if (Math.abs(v) > lim) { var f = keDatar(p, c); f.vol = v; out.push(f); } else buang++; if (p !== U) p.delete(); });
    out.sort(function (a, b) { return b.vol - a.vol; });
    return { bodies: out, vol: out.reduce(function (s, b) { return s + b.vol; }, 0), nSerpih: buang };
  }
  MFB._keMf = keMf; MFB._pecah = pecah; MFB._pusat = pusat;

  function bebas(L) { L.forEach(function (m) { try { if (m && m.delete) m.delete(); } catch (e) {} }); }
  function satu(W, L, c) { var M = L.map(function (m) { return keMf(W, m, c); }); if (M.length === 1) return M[0]; var U = W.Manifold.union(M); bebas(M); return U; }

  MFB.union = function (L) {
    var W = MFB.mod; if (!W) throw new Error('pustaka boolean belum siap'); if (!L.length) return { bodies: [], vol: 0, nSerpih: 0 };
    var c = pusat(L), U = satu(W, L, c);
    try { return pecah(U, c); } finally { bebas([U]); }
  };
  /* A, B = kumpulan mesh datar; Z (opsional) = function(W, c) -> Manifold pembatas B (mis. zona penilaian) */
  MFB.ops = function (A, B, Z) {
    var W = MFB.mod; if (!W) throw new Error('pustaka boolean belum siap');
    var c = pusat(A.concat(B)), MA = null, MB = null, MZ = null, K = [];
    try {
      MA = A.length ? satu(W, A, c) : null; MB = B.length ? satu(W, B, c) : null;
      /* zona hanya membatasi B - A (mis. ore loss); A ∩ B dan A - B memakai B utuh */
      var MBz = MB; if (MB && Z) { MZ = Z(W, c); if (MZ) MBz = MB.intersect(MZ); }
      var kos = { bodies: [], vol: 0, nSerpih: 0 };
      var AnB = MA && MB ? MA.intersect(MB) : null, AmB = MA ? (MB ? MA.subtract(MB) : MA) : null, BmA = MBz ? (MA ? MBz.subtract(MA) : MBz) : null;
      K = [AnB, AmB, BmA, MBz];
      return { AnB: AnB ? pecah(AnB, c) : kos, AmB: AmB ? pecah(AmB, c) : kos, BmA: BmA ? pecah(BmA, c) : kos, volA: MA ? MA.volume() : 0, volB: MBz ? MBz.volume() : 0 };
    } finally { bebas(K.concat([MA, MB, MZ]).filter(function (x, i, s) { return x && s.indexOf(x) === i; })); }
  };
  /* zona penilaian: tiap lapis {pts:[[x,y],...] DUNIA, top, bot}; poligon digabung per lapis, di-offset d m (bulat), diekstrusi */
  MFB.zona = function (lapis, d) {
    return function (W, c) {
      var M = [];
      lapis.forEach(function (L) {
        if (!(L.top > L.bot) || !L.polys.length) return;
        var cs = new W.CrossSection(L.polys.map(function (P) { var Q = P.map(function (q) { return [q[0] - c[0], q[1] - c[1]]; }), s = 0;
          for (var i = 0; i < Q.length; i++) { var a = Q[i], b = Q[(i + 1) % Q.length]; s += a[0] * b[1] - b[0] * a[1]; } return s < 0 ? Q.reverse() : Q; }), 'NonZero');
        var o = d > 0 ? cs.offset(d, 'Round', 2, 24) : cs, e = o.extrude(L.top - L.bot).translate([0, 0, L.bot - c[2]]);
        if (o !== cs) o.delete(); cs.delete(); M.push(e);
      });
      if (!M.length) return null; if (M.length === 1) return M[0];
      var U = W.Manifold.union(M); bebas(M); return U;
    };
  };
})();
