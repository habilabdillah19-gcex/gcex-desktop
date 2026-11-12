/* ================= SOLID INDUK + CABANG MENYATU (boolean union) -- GC-Ex Drill Hole 0.24.84 =================
   Pemilik 12 Nov 2026: "Bisakah GCex menyambungkan cabang dengan induk sehingga benar-benar menyatu? seperti yang ada di
   gambar" (sayatan Leapfrog, vein bercabang bergaris luar Y) -> Pilihan 1: boolean union mesh.

   Tiap domain tetap dibangun sendiri (imBuild); untuk domain INDUK yang punya cabang, solid induk + semua cabangnya
   digabung dengan boolean UNION (pustaka manifold-3d, WASM tertanam: web-src-dh/vendor/manifold_dh.js) menjadi SATU
   solid tertutup -- seperti Solid > Boolean > Union di Surpac. Dipakai untuk:
     - tampilan 3D & sayatan (2D / slab): satu kulit, garis luar menyatu di titik percabangan;
     - ekspor per domain bila "Export cabang digabung ke file domain induk" (bawaan kini NYALA) dan ekspor Vein System;
     - volume gabungan per induk (eksak, menggantikan sampling grid bila union berhasil).
   TIDAK mengubah estimasi: Model Estimation sudah memperlakukan induk + cabang sebagai satu domain (ME._grp).
   Pilihan GM.opt.imUni (bawaan nyala): mati = dua kulit seperti sebelumnya. Bila union gagal (mesh tidak manifold),
   jatuh ke dua kulit + pesan.
   WASM dimuat ASINKRON sekali (Chrome tidak mengizinkan kompilasi WASM besar secara sinkron); selama belum siap,
   tampilan memakai dua kulit lalu digambar ulang begitu siap. */
(function () {
  if (window.VU) return;
  var VU = window.VU = { mod: null, busy: false, err: '', C: {} };

  VU.on = function () { return !(GM.opt && GM.opt.imUni === false); };
  VU.load = function () {
    if (VU.mod || VU.busy || VU.err || !window.__MF_MODULE || !window.__MF_WASM_B64) return;
    VU.busy = true;
    try {
      var s = atob(window.__MF_WASM_B64), b = new Uint8Array(s.length);
      for (var i = 0; i < s.length; i++) b[i] = s.charCodeAt(i);
      window.__MF_MODULE({ wasmBinary: b }).then(function (W) {
        W.setup(); VU.mod = W; VU.busy = false;
        try { if (window.gmPanel) gmPanel(); } catch (e) {}
        try { if (window.updatePlot) updatePlot(); } catch (e) {}
      }, function (e) { VU.busy = false; VU.err = 'pustaka boolean gagal dimuat: ' + (e && e.message || e); console.error(e); });
    } catch (e) { VU.busy = false; VU.err = 'pustaka boolean gagal dimuat: ' + e.message; console.error(e); }
  };

  /* mesh GC-Ex {_x,_y,_z,_i,_j,_k,nv,nt} -> Manifold; koordinat digeser ke pusat c (presisi float32) */
  function keMf(W, m, c) {
    var n = m.nv, vp = new Float32Array(n * 3), tv = new Uint32Array(m.nt * 3), i, vol = 0;
    for (i = 0; i < n; i++) { vp[3 * i] = m._x[i] - c[0]; vp[3 * i + 1] = m._y[i] - c[1]; vp[3 * i + 2] = m._z[i] - c[2]; }
    for (i = 0; i < m.nt; i++) {
      var a = m._i[i], b = m._j[i], d = m._k[i]; tv[3 * i] = a; tv[3 * i + 1] = b; tv[3 * i + 2] = d;
      var ax = vp[3 * a], ay = vp[3 * a + 1], az = vp[3 * a + 2], bx = vp[3 * b], by = vp[3 * b + 1], bz = vp[3 * b + 2], qx = vp[3 * d], qy = vp[3 * d + 1], qz = vp[3 * d + 2];
      vol += ax * (by * qz - bz * qy) - ay * (bx * qz - bz * qx) + az * (bx * qy - by * qx);
    }
    if (vol < 0) for (i = 0; i < m.nt; i++) { var t = tv[3 * i + 1]; tv[3 * i + 1] = tv[3 * i + 2]; tv[3 * i + 2] = t; }   /* hadap luar */
    var mf = null, ms = new W.Mesh({ numProp: 3, vertProperties: vp, triVerts: tv });
    try { mf = new W.Manifold(ms); } catch (e) { mf = null; }
    if (!mf || mf.status() !== 'NoError') {               /* coba sekali lagi dengan simpul berimpit digabung */
      if (mf) mf.delete();
      try { ms.merge(); mf = new W.Manifold(ms); } catch (e) { throw new Error('solid ' + (m.name || '') + ' bukan mesh tertutup (manifold): ' + (e.message || e)); }
      if (mf.status() !== 'NoError') { var st = mf.status(); mf.delete(); throw new Error('solid ' + (m.name || '') + ' bukan mesh tertutup (' + st + ')'); }
    }
    return mf;
  }
  function dariMf(U, c, name) {
    var g = U.getMesh(), np = g.numProp, nv = g.vertProperties.length / np, nt = g.triVerts.length / 3;
    var x = new Float32Array(nv), y = new Float32Array(nv), z = new Float32Array(nv), I = new Int32Array(nt), J = new Int32Array(nt), K = new Int32Array(nt), i;
    for (i = 0; i < nv; i++) { x[i] = g.vertProperties[i * np] + c[0]; y[i] = g.vertProperties[i * np + 1] + c[1]; z[i] = g.vertProperties[i * np + 2] + c[2]; }
    for (i = 0; i < nt; i++) { I[i] = g.triVerts[3 * i]; J[i] = g.triVerts[3 * i + 1]; K[i] = g.triVerts[3 * i + 2]; }
    return { name: name, _x: x, _y: y, _z: z, _i: I, _j: J, _k: K, nv: nv, nt: nt, ntop: nt, nbot: nt };
  }
  /* union mesh apa saja (dipakai juga oleh uji). Hasil: {mesh, vol, nKomp} */
  VU.union = function (L, name) {
    var W = VU.mod; if (!W) throw new Error('pustaka boolean belum siap');
    var c = [0, 0, 0], n = 0; L.forEach(function (m) { for (var i = 0; i < m.nv; i += 7) { c[0] += m._x[i]; c[1] += m._y[i]; c[2] += m._z[i]; n++; } });
    c = c.map(function (v) { return n ? v / n : 0; });
    var M = [], U = null;
    try {
      L.forEach(function (m) { M.push(keMf(W, m, c)); });
      U = M.length === 1 ? M[0] : W.Manifold.union(M);
      /* bagian bervolume praktis nol (serpihan dari ujung pinch-out bertebal 0) dibuang; bagian nyata dipertahankan */
      var P = U.decompose(), tot = Math.abs(U.volume()), lim = Math.max(1e-3, 1e-7 * tot), keep = [], buang = 0;
      P.forEach(function (p) { if (Math.abs(p.volume()) > lim) keep.push(p); else { buang++; p.delete(); } });
      if (buang && keep.length) { var U2 = keep.length === 1 ? keep[0] : W.Manifold.compose(keep); if (U2 !== keep[0]) keep.forEach(function (p) { p.delete(); }); U.delete(); U = U2; }
      else keep.forEach(function (p) { if (p !== U) p.delete(); });
      var vk = []; (function () { var Q = U.decompose(); Q.forEach(function (p) { vk.push(p.volume()); if (p !== U) p.delete(); }); })(); vk.sort(function (a, b) { return b - a; });
      var out = { mesh: dariMf(U, c, name), vol: U.volume(), nKomp: vk.length, vKomp: vk, nSerpih: buang };
      return out;
    } finally { M.forEach(function (m) { if (m !== U) try { m.delete(); } catch (e) {} }); if (U) try { U.delete(); } catch (e) {} }
  };

  /* union grup induk (cache per kunci anggota). null = belum bisa (pustaka belum siap / dimatikan / gagal) */
  VU.grup = function (top) {
    if (!VU.on()) return null;
    var ids = gmGroup(top), L = [];
    ids.forEach(function (id) { var R = IM.R[id], d = gmDom(id); if (d && d.vis !== false && R && R.mesh) L.push({ d: d, R: R }); });
    if (L.length < 2) return null;
    var key = L.map(function (o) { return o.d.id + ':' + o.R.key; }).join('|'), c = VU.C[top];
    if (c && c.key === key) return c.ok ? c : null;
    if (!VU.mod) { VU.load(); return null; }
    var t0 = performance.now(), d0 = gmDom(top);
    try {
      var r = VU.union(L.map(function (o) { return o.R.mesh; }), d0.name + '_gabungan');
      c = VU.C[top] = { key: key, ok: true, mesh: r.mesh, vol: r.vol, nKomp: r.nKomp, names: L.map(function (o) { return o.d.name; }), ms: performance.now() - t0 };
      c.R = { key: 'U:' + key, mesh: r.mesh, st: Object.assign({}, IM.R[top] && IM.R[top].st, { vol: r.vol }) };
      return c;
    } catch (e) { VU.C[top] = { key: key, ok: false, err: e.message }; console.error(e); return null; }
  };
  VU.tops = function () { return gmTops().filter(function (t) { return gmKids(t.id).length; }); };

  /* jalankan fn dengan GM.doms / IM.R di mana tiap grup induk diganti satu solid gabungan */
  VU.dengan = function (fn) {
    var T = VU.tops(); if (!T.length || !VU.on()) return fn();
    try { imSync(); } catch (e) { console.error(e); }
    var map = {}, any = false; T.forEach(function (t) { var g = VU.grup(t.id); if (g) { map[t.id] = g; any = true; } });
    if (!any) return fn();
    var D0 = GM.doms, R0 = IM.R, S0 = window.imSync, R1 = Object.assign({}, R0), D1 = [];
    D0.forEach(function (d) {
      if (gmIsKid(d) && map[d.par]) return;                         /* cabang sudah ada di solid gabungan induknya */
      if (map[d.id]) R1[d.id] = map[d.id].R;
      D1.push(d);
    });
    GM.doms = D1; IM.R = R1; imSync = window.imSync = function () { return false; };
    try { return fn(); } finally { GM.doms = D0; IM.R = R0; imSync = window.imSync = S0; }
  };

  /* ---- tampilan 3D & sayatan ---- */
  var _t3 = imTraces, _t2 = imTraces2D;
  imTraces = window.imTraces = function (T, o) { return VU.dengan(function () { return _t3(T, o); }); };
  imTraces2D = window.imTraces2D = function (o, F) { return VU.dengan(function () { return _t2(o, F); }); };

  /* ---- ekspor per domain: cabang digabung ke berkas induk (bawaan nyala) memakai solid union ---- */
  /* bawaan: cabang ikut berkas induk (proyek lama tanpa pengaturan ini ikut menyala) */
  VU.def = function () { if (GM.opt && GM.opt.imGrp == null) GM.opt.imGrp = true; };
  VU.def();
  var _files = imFiles;
  imFiles = window.imFiles = function (fmt, surf) {
    var self = this, a = arguments;
    VU.def(); if (surf || !GM.opt.imGrp) return _files.apply(self, a);       /* permukaan HW / FW atau berkas per domain: tanpa union */
    return VU.dengan(function () { return _files.apply(self, a); });
  };

  /* ---- ekspor Vein System gabungan: grup induk = satu solid union ---- */
  if (window.VS && VS.ekspor) {
    var _ve = VS.ekspor;
    VS.ekspor = function (fmt) { var self = this, a = arguments; return VU.dengan(function () { return _ve.apply(self, a); }); };
  }

  /* ---- volume gabungan per induk: eksak dari union bila tersedia ---- */
  var _gs = imGrpStat;
  imGrpStat = window.imGrpStat = function (top) {
    var st = _gs.apply(this, arguments), g = VU.grup(top);
    if (st && g) { st = Object.assign({}, st, { volGrid: st.vol, vol: g.vol, ov: Math.max(0, (st.sum || 0) - g.vol), uni: true, nKomp: g.nKomp }); }
    return st;
  };

  /* ---- panel: status union di kotak "Solid gabungan per domain induk" ---- */
  var _gp = gmPanel;
  gmPanel = window.gmPanel = function () {
    VU.def(); var r = _gp.apply(this, arguments);
    try {
      var box = document.querySelector('#gmBody .grpbox'); if (!box || box.querySelector('.vuopt')) return r;
      var T = VU.tops(), s = T.map(function (t) {
        var c = VU.C[t.id], g = VU.grup(t.id);
        if (g) return gmE(t.name) + ': <b>satu solid</b>' + (g.nKomp > 1 ? ' <span class=warn>(' + g.nKomp + ' bagian terpisah &mdash; cabang tidak menyentuh induk; periksa Sambung ke induk)</span>' : '') + ' &middot; ' + imN(g.vol) + ' m&sup3;';
        if (c && !c.ok) return gmE(t.name) + ': <span class=warn>gagal digabung (' + gmE(c.err) + ') &mdash; ditampilkan dua kulit</span>';
        return gmE(t.name) + ': ' + (VU.err ? '<span class=warn>' + gmE(VU.err) + '</span>' : VU.on() ? 'menyiapkan pustaka boolean&hellip;' : 'dua kulit (penggabungan dimatikan)');
      });
      var d = document.createElement('div'); d.className = 'vuopt';
      d.innerHTML = '<label class=sw style="margin:6px 0 0"><input type=checkbox ' + (VU.on() ? 'checked' : '') + ' onchange="gmOpt(\'imUni\',this.checked);gmPanel();updatePlot()">Satukan induk + cabang (boolean union) &mdash; satu solid tertutup untuk tampilan, sayatan &amp; ekspor</label>' +
        (VU.on() && s.length ? '<div class=hint>' + s.join('<br>') + '</div>' : '');
      box.appendChild(d);
    } catch (e) { console.error(e); }
    return r;
  };

  /* muat pustaka di latar sesudah aplikasi tenang */
  setTimeout(function () { try { if (VU.tops().length) VU.load(); } catch (e) {} }, 2500);
})();
