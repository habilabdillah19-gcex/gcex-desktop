/* ============ SOLID VEIN AKTUAL: SATUKAN PULAU (boolean union) -- GC-Ex Block Model 0.24.71 ============
   Pemilik 12 Nov 2026 memilih "Union + rekonsiliasi dengan wireframe model" untuk Solid Vein.
   Loft cara Surpac (svein_bm.js) tetap membentuk solid per pulau. Sesudahnya, pulau-pulau yang SALING
   BERTAMPALAN (kotak batasnya berpotongan) disatukan dengan boolean union (web-src/mfbool.js) menjadi satu tubuh
   tertutup -- seperti Solid > Boolean > Union di Surpac sebelum validasi. Ini menghapus volume ganda dari:
     - poligon bertampalan satu flitch yang tidak bisa digabung 2D ("bentuk tampalannya rumit");
     - pertemuan n-m / cabang yang "ditutup sendiri" sehingga menembus tubuh tetangganya;
     - mode Kumulatif yang membangun ulang area yang sama.
   Pulau yang tidak bertampalan dengan pulau lain TIDAK disentuh (geometri & volume identik dengan sebelumnya).
   Hasil union menggantikan daftar pulau (R.IS); tampilan, pendaftaran Wireframe geologi, ekspor DTM/STR/DXF, CSV
   dan Report block model ikut otomatis. Pulau asli disimpan di R.IS0. Pilihan per periode: P(p).uni (bawaan nyala). */
(function () {
  if (!window.SV || !SV.build || window.SVB) return;
  var SVB = window.SVB = {};
  var _build = SV.build, _run = SV.run;
  var on = function (p) { return SV.P(p).uni !== false; };
  var N = function (v, d) { return (+v).toLocaleString('id-ID', { minimumFractionDigits: d || 0, maximumFractionDigits: d || 0 }); };

  function bb(V, tri) { var b = [1e18, -1e18, 1e18, -1e18, 1e18, -1e18]; tri.forEach(function (t) { t.forEach(function (i) { var x = V.x[i], y = V.y[i], z = V.z[i]; if (x < b[0]) b[0] = x; if (x > b[1]) b[1] = x; if (y < b[2]) b[2] = y; if (y > b[3]) b[3] = y; if (z < b[4]) b[4] = z; if (z > b[5]) b[5] = z; }); }); return b; }
  function pot(a, b, e) { e = e || 0; return a[0] <= b[1] + e && b[0] <= a[1] + e && a[2] <= b[3] + e && b[2] <= a[3] + e && a[4] <= b[5] + e && b[4] <= a[5] + e; }
  function datar(V, tri) { var map = {}, v = [], t = []; tri.forEach(function (tr) { tr.forEach(function (ix) { if (map[ix] === undefined) { map[ix] = v.length / 3; v.push(V.x[ix] + offX, V.y[ix] + offY, V.z[ix]); } t.push(map[ix]); }); }); return { v: new Float64Array(v), t: new Uint32Array(t), nv: v.length / 3, nt: t.length / 3 }; }

  /* R hasil loft -> R dengan pulau bertampalan disatukan */
  SVB.satukan = function (R, p) {
    if (!R || R.err || !R.IS || !R.IS.length || !on(p)) return R;
    if (!MFB.ok()) { R.uniPending = true; return R; }
    /* satuan kerja = CANGKANG tertutup: satu pulau bisa berisi beberapa cangkang yang saling menembus (pemasangan n-m
       menurut centroid menyatukan graf pulau tanpa menyatukan mesh-nya) */
    var IS = [], IS0 = R.IS;
    IS0.forEach(function (s) { var P = {}, cariV = function (v) { var r = v; while (P[r] !== r) r = P[r]; while (P[v] !== r) { var n = P[v]; P[v] = r; v = n; } return r; };
      s.tri.forEach(function (t) { t.forEach(function (v) { if (P[v] === undefined) P[v] = v; }); var a0 = cariV(t[0]); [t[1], t[2]].forEach(function (v) { var b0 = cariV(v); if (a0 !== b0) P[b0] = a0; }); });
      var C = {}; s.tri.forEach(function (t) { var k = cariV(t[0]); (C[k] = C[k] || []).push(t); }); var ks = Object.keys(C);
      if (ks.length === 1) IS.push(s); else ks.forEach(function (k) { IS.push(Object.assign({}, s, { tri: C[k], vol: Math.abs(SV.volume(R.V, C[k])), _bag: 1 })); }); });
    if (IS.length < 2) { R.uni = { nIn: IS0.length, nOut: IS0.length, volIn: sum(IS0), vol: sum(IS0), nGab: 0, nSerpih: 0 }; return R; }
    var B = IS.map(function (s) { return bb(R.V, s.tri); }), par = IS.map(function (_, i) { return i; }), cari = function (i) { while (par[i] !== i) i = par[i] = par[par[i]]; return i; };
    for (var a = 0; a < IS.length; a++) for (var b = a + 1; b < IS.length; b++) if (pot(B[a], B[b], 1e-6)) par[cari(a)] = cari(b);
    var G = {}; IS.forEach(function (s, i) { var k = cari(i); (G[k] = G[k] || []).push(i); });
    var grp = Object.keys(G).map(function (k) { return G[k]; });
    if (grp.every(function (g) { return g.length === 1; })) { R.uni = { nIn: IS0.length, nOut: IS0.length, volIn: sum(IS0), vol: sum(IS0), nGab: 0, nSerpih: 0 }; return R; }
    var V = { x: [], y: [], z: [] }, out = [], nGab = 0, nSerpih = 0, gagal = [];
    grp.forEach(function (g) {
      var bodies = null;
      if (g.length > 1) {
        try { var U = MFB.union(g.map(function (i) { return datar(R.V, IS[i].tri); })); bodies = U.bodies; nSerpih += U.nSerpih; nGab += g.length; }
        catch (e) { gagal.push(g.map(function (i) { return '#' + IS[i].n; }).join('+') + ': ' + e.message); bodies = null; }
      }
      if (!bodies) { g.forEach(function (i) { var s = IS[i], map = {}, tri = s.tri.map(function (t) { return t.map(function (ix) { if (map[ix] === undefined) { map[ix] = V.x.length; V.x.push(R.V.x[ix]); V.y.push(R.V.y[ix]); V.z.push(R.V.z[ix]); } return map[ix]; }); }); out.push(Object.assign({}, s, { tri: tri, asal: [s.n] })); }); return; }
      var src = g.map(function (i) { return IS[i]; });
      bodies.forEach(function (bd) {
        var o = V.x.length, tri = [];
        for (var i = 0; i < bd.nv; i++) { V.x.push(bd.v[3 * i] - offX); V.y.push(bd.v[3 * i + 1] - offY); V.z.push(bd.v[3 * i + 2]); }
        for (i = 0; i < bd.nt; i++) tri.push([o + bd.t[3 * i], o + bd.t[3 * i + 1], o + bd.t[3 * i + 2]]);
        var bx = bb(V, tri), asal = src.filter(function (s) { return pot(bb(R.V, s.tri), bx, 1e-6); }), ed = SV.edges(tri);
        var polys = []; asal.forEach(function (s) { (s.polys || []).forEach(function (id) { if (polys.indexOf(id) < 0) polys.push(id); }); });
        out.push({ n: 0, tri: tri, vol: Math.abs(bd.vol), area: SV.areaOf(V, tri), closed: ed.open === 0 && ed.dup === 0, open: ed.open, dup: ed.dup, top: bx[5], bot: bx[4],
          nPoly: polys.length || asal.reduce(function (t, s) { return t + (s.nPoly || 0); }, 0), nLv: asal.reduce(function (t, s) { return Math.max(t, s.nLv || 0); }, 0), polys: polys, asal: asal.map(function (s) { return s.n; }), gab: true });
      });
    });
    out.sort(function (a, b) { return b.vol - a.vol; }); out.forEach(function (s, i) { s.n = i + 1; });
    var R2 = Object.assign({}, R, { V: V, IS: out, IS0: IS0, nTri: out.reduce(function (t, s) { return t + s.tri.length; }, 0) });
    R2.uni = { nIn: IS0.length, nOut: out.length, volIn: sum(IS0), vol: sum(out), nGab: nGab, nSerpih: nSerpih, gagal: gagal };
    if (gagal.length) R2.warn = (R.warn || []).concat(gagal.map(function (g) { return 'Satukan pulau ' + g + ' -- pulau itu tetap terpisah.'; }));
    return R2;
  };
  function sum(L) { return L.reduce(function (t, s) { return t + (s.vol || 0); }, 0); }

  SV.build = function (p) { var r = _build.apply(this, arguments); try { return SVB.satukan(r, p || SV.per()); } catch (e) { console.error(e); return r; } };
  /* Bangun solid: pustaka dimuat dulu (asinkron, sekali) supaya hasil yang disimpan sudah tersatukan */
  SV.run = function () { var self = this, a = arguments, p = SV.per();
    if (p && on(p) && !MFB.ok()) { SV.busy = true; try { SV.panel(); } catch (e) {} MFB.load().then(function () { SV.busy = false; _run.apply(self, a); }, function () { SV.busy = false; _run.apply(self, a); }); return; }
    return _run.apply(self, a); };
  /* geometri di memori dibangun tanpa union karena pustaka belum siap -> bangun ulang begitu siap */
  (function () { var tunggu = function () { var p = SV.per(); if (p && p.res && on(p) && !MFB.ok()) MFB.load().then(function () { SV._R = null; try { SV.panel(); } catch (e) {} try { updatePlot(); } catch (e) {} }); }; setTimeout(tunggu, 3000); })();

  SVB.set = function (v) { var p = SV.per(); if (!p) return; SV.P(p).uni = !!v; SV._R = null; if (p.res) p.stale = true; SV.dirty(); SV.panel(); };
  SV.uniHtml = function (p, r) {
    var u = r.uni, h = '<div class=hint style="margin:2px 0 4px"><label class=sw title="Pulau yang saling bertampalan disatukan dengan boolean union (seperti Solid > Boolean > Union di Surpac) sehingga volumenya tidak terhitung dua kali dan ekspornya satu solid valid. Pulau yang tidak bertampalan tidak diubah."><input type=checkbox ' + (on(p) ? 'checked' : '') + ' onchange="SVB.set(this.checked)">Satukan pulau yang bertampalan (boolean union)</label>';
    if (on(p) && u) h += '<br>' + (u.nGab ? N(u.nGab) + ' pulau bertampalan disatukan: ' + N(u.nIn) + ' &rarr; <b>' + N(u.nOut) + ' tubuh</b>; volume ' + N(u.volIn, 1) + ' &rarr; <b>' + N(u.vol, 1) + ' m&sup3;</b> (ganda ' + N(Math.max(0, u.volIn - u.vol), 1) + ' m&sup3; dihapus)' + (u.nSerpih ? '; ' + u.nSerpih + ' serpihan tanpa volume dibuang' : '') : 'Tidak ada pulau yang bertampalan &mdash; solid tidak diubah.') +
      (u.gagal && u.gagal.length ? '<br><span class=warn>' + u.gagal.length + ' kelompok gagal disatukan (tetap terpisah).</span>' : '');
    else if (on(p) && r.uni === undefined && !MFB.ok()) h += '<br>' + (MFB.err ? '<span class=warn>' + MFB.err + '</span>' : 'Menyiapkan pustaka boolean&hellip;');
    return h + '</div>';
  };
})();
