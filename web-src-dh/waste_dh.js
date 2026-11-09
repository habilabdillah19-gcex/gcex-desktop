/* ================= ESTIMASI WASTE — material di luar seluruh solid domain =================
   Model Estimation biasa adalah hard boundary per domain: hanya blok yang pusatnya di dalam solid
   vein yang diestimasi, blok di luarnya tidak disentuh. Akibatnya kadar waste di sekitar wireframe
   ore tidak pernah ada, padahal justru itu yang menentukan dilusi, ore loss, dan tonase total
   material di bawah topografi / di dalam desain pit.

   Modul ini menambah satu domain semu WASTE:
     blok   = blok block model aktif yang pusatnya DI LUAR semua solid domain (opsional: hanya yang
              di bawah topografi aktif, dan/atau di dalam desain pit);
     sampel = komposit dari interval bor yang TIDAK di-flag domain apa pun (hard boundary waste:
              interval ore tidak ikut, sehingga kadar halo tidak tertarik oleh kadar vein);
     hasil  = ditulis ke baris hasil estimasi dengan domain_est = 'WASTE' dan est_type = 3,
              terpisah tegas dari est_type 1 (koreksi di solid) dan 2 (blok tambahan di dalam solid).

   PEMILIHAN METODE PER BLOK (0.24.18, permintaan pemilik):
     - domain terdekat dicari dari komposit ber-flag tiap domain. Bila jaraknya <= ambang, blok
       dikrige dengan VARIOGRAM & ELIPSOID domain terdekat itu (kontinuitas lokal diwarisi dari
       domain yang paling dekat, bukan dari satu domain yang dipilih tangan);
     - bila jaraknya > ambang — jauh dari semua domain, sehingga tidak ada model kontinuitas yang
       bisa dipertanggungjawabkan — blok diisi dengan IDW (inverse distance weighting) pada komposit
       waste. Penanda: est_pass = 9, dan est_sor / est_ke / est_kv = -99 (tidak berlaku untuk IDW).

   est_type = 3 membuat blok waste:
     - tidak pernah ikut pelaporan sumber daya per domain vein;
     - tidak diberi kelas keyakinan (Measured / Indicated / Inferred) — lihat cls_dh.js;
     - tetap terbawa ke Reporting BM sebagai material, jadi volume & tonase waste di bawah
       topografi atau di dalam desain pit bisa dilaporkan bersama ore.

   Blok waste harus SUDAH ADA di block model aktif (modul ini tidak membuat blok baru). Bila belum
   ada block model sama sekali, atau cakupan .mdl impor lebih sempit dari area of interest, buat /
   lengkapi dulu dengan "Buat kerangka blok (AOI)" di menu Block Model (aoi_dh.js).

   Lingkup: jalur domain solid (Geomodeller Vein) — berlaku untuk semua tipe deposit yang dimodelkan
   sebagai solid domain. Jalur Stratified-Laterite punya penyimpanan & estimasi sendiri (sl_dh.js)
   dan TIDAK memakai modul ini.                                                                     */
(function () {
  if (typeof ME === 'undefined' || typeof BX === 'undefined') return;
  var WID = '__waste', WNAME = 'WASTE', IDWP = 9;
  var WS = { job: null, msg: '', last: null };
  window.WS = WS;
  window.wsId = function () { return WID; };

  function wE(s) { return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) { return '&#' + c.charCodeAt(0) + ';'; }); }
  function fmt(v, d) { return v == null || !isFinite(v) ? '-' : (+v).toLocaleString('id-ID', { minimumFractionDigits: d || 0, maximumFractionDigits: d || 0 }); }

  /* ---------- parameter waste (disimpan bersama hasil estimasi di proyek) ---------- */
  function defPar() { return { tc: 0, L: 2, mult: 1, maxd: 50, p: 2, nmax: 12, rad: 60, topo: 1, pit: 0, mode: 'auto', est: null }; }
  window.wsPar = function () {
    if (!ME.store) return defPar();
    if (!ME.store.ws) ME.store.ws = defPar();
    var o = ME.store.ws, D = defPar();
    Object.keys(D).forEach(function (k) { if (o[k] === undefined) o[k] = D[k]; });
    delete o.src; delete o.on;
    return o;
  };

  /* variogram waste hasil fitting sendiri (disimpan dari Geostatistik -> "Simpan ke WASTE"); null bila belum ada */
  window.wsOwn = function () { var o = wsPar(), e = o && o.est; return (e && e.m && e.m.cs) ? e : null; };
  /* mode efektif: 'own' = variogram waste sendiri untuk seluruh blok, 'dom' = variogram domain terdekat */
  window.wsMode = function () { var o = wsPar(); if (o.mode === 'dom') return 'dom'; return wsOwn() ? 'own' : 'dom'; };

  /* ---------- indeks titik sederhana (sel kubus) untuk cari terdekat ---------- */
  function pIndex(pts, cell) {
    var B = Math.max(1, cell || 25), H = {};
    pts.forEach(function (p, i) {
      var k = Math.floor(p.x / B) + '_' + Math.floor(p.y / B) + '_' + Math.floor(p.z / B);
      (H[k] || (H[k] = [])).push(i);
    });
    return {
      B: B, H: H, pts: pts,
      near: function (x, y, z, rmax) {
        var cx = Math.floor(x / B), cy = Math.floor(y / B), cz = Math.floor(z / B), R = Math.max(1, Math.ceil(rmax / B));
        var best = -1, bd = Infinity;
        for (var r = 0; r <= R; r++) {
          for (var a = cx - r; a <= cx + r; a++) for (var b = cy - r; b <= cy + r; b++) for (var c = cz - r; c <= cz + r; c++) {
            if (r > 0 && Math.abs(a - cx) !== r && Math.abs(b - cy) !== r && Math.abs(c - cz) !== r) continue;
            var L = H[a + '_' + b + '_' + c]; if (!L) continue;
            for (var q = 0; q < L.length; q++) {
              var p = pts[L[q]], d2 = (p.x - x) * (p.x - x) + (p.y - y) * (p.y - y) + (p.z - z) * (p.z - z);
              if (d2 < bd) { bd = d2; best = L[q]; }
            }
          }
          if (best >= 0 && Math.sqrt(bd) <= r * B) break;
        }
        return best < 0 ? null : { i: best, d: Math.sqrt(bd) };
      },
      list: function (x, y, z, rmax, nmax) {
        var cx = Math.floor(x / B), cy = Math.floor(y / B), cz = Math.floor(z / B), R = Math.max(1, Math.ceil(rmax / B)), out = [];
        for (var a = cx - R; a <= cx + R; a++) for (var b = cy - R; b <= cy + R; b++) for (var c = cz - R; c <= cz + R; c++) {
          var L = H[a + '_' + b + '_' + c]; if (!L) continue;
          for (var q = 0; q < L.length; q++) {
            var p = pts[L[q]], d = Math.sqrt((p.x - x) * (p.x - x) + (p.y - y) * (p.y - y) + (p.z - z) * (p.z - z));
            if (d <= rmax) out.push({ i: L[q], d: d });
          }
        }
        out.sort(function (u, v) { return u.d - v.d; });
        return out.slice(0, Math.max(1, nmax || 12));
      }
    };
  }

  /* ---------- domain yang punya parameter estimasi + titik komposit ber-flag-nya ---------- */
  function domList() {
    var o = wsPar(), L = (window.gmTops ? gmTops() : (window.GM ? GM.doms : [])) || [], out = [], pts = [], el = '';
    if (wsMode() === 'own') {
      var E = wsOwn(), P0 = JSON.parse(JSON.stringify(E));
      P0.P = (P0.P || []).map(function (q) { return Object.assign({}, q, { mult: (+q.mult || 1) * (+o.mult || 1) }); });
      return { doms: [{ d: null, name: 'WASTE (variogram sendiri)', P: P0, mo: meModel(P0) }], idx: null, el: P0.el, own: true };
    }
    L.forEach(function (d) {
      var P0 = meParOf(d); if (!P0) return;
      var P = JSON.parse(JSON.stringify(P0));
      el = el || P.el;
      if (P.el !== el) return; /* satu run satu unsur */
      P.P = (P.P || []).map(function (p) { return Object.assign({}, p, { mult: (+p.mult || 1) * (+o.mult || 1) }); });
      var C = [];
      try { C = meComps(d, P0); } catch (e) { C = []; }
      if (!C.length) return;
      var di = out.length;
      out.push({ d: d, name: d.name, P: P, mo: meModel(P) });
      C.forEach(function (c) { pts.push({ x: c.x, y: c.y, z: c.z, di: di }); });
    });
    return { doms: out, idx: pts.length ? pIndex(pts, 25) : null, el: el };
  }
  window.wsDoms = domList;

  /* ---------- interval bor di luar semua flag domain ---------- */
  function runsOut() {
    var R = {}, F = (window.GM && GM.flags) || {};
    Object.keys(holeData).forEach(function (id) {
      var md = holeData[id].maxD; if (!(md > 0)) return;
      var L = (F[id] || []).map(function (f) { return [Math.max(0, f[0]), Math.min(f[1], md)]; })
        .filter(function (r) { return r[1] > r[0]; }).sort(function (a, b) { return a[0] - b[0]; });
      var M = [];
      L.forEach(function (r) { var l = M[M.length - 1]; if (l && r[0] <= l[1] + 1e-6) l[1] = Math.max(l[1], r[1]); else M.push(r.slice()); });
      var out = [], p = 0;
      M.forEach(function (r) { if (r[0] - p > 1e-6) out.push([p, r[0]]); p = Math.max(p, r[1]); });
      if (md - p > 1e-6) out.push([p, md]);
      if (out.length) R[id] = out;
    });
    return R;
  }

  /* komposit panjang tetap pada interval di luar flag (algoritma sama dengan meComps) */
  function comps(el) {
    var o = wsPar(), ei = elements.indexOf(el), L = +o.L || 0, tc = +o.tc || 0, R = runsOut(), C = [];
    if (ei < 0) throw new Error('unsur ' + el + ' tidak ada di database');
    Object.keys(R).forEach(function (id) {
      var A = (groupedAssays[id] || []).filter(function (a) { return a[4][ei] !== null && a[2] > a[1]; }).sort(function (p, q) { return p[1] - q[1]; });
      if (!A.length) return;
      R[id].forEach(function (r) {
        var n = L > 0 ? Math.max(1, Math.round((r[1] - r[0]) / L)) : 0, S = [];
        if (n) { for (var k = 0; k < n; k++) S.push([r[0] + (r[1] - r[0]) * k / n, r[0] + (r[1] - r[0]) * (k + 1) / n]); }
        else A.forEach(function (a) { var f = Math.max(a[1], r[0]), t = Math.min(a[2], r[1]); if (t > f) S.push([f, t]); });
        S.forEach(function (sg) {
          var sl = 0, sv = 0;
          A.forEach(function (a) { var ov = Math.min(sg[1], a[2]) - Math.max(sg[0], a[1]); if (ov > 0) { sl += ov; sv += ov * a[4][ei]; } });
          if (sl < 0.5 * (sg[1] - sg[0]) - 1e-9) return;
          var v = sv / sl, p = getXYZ(id, (sg[0] + sg[1]) / 2);
          C.push({ id: id, f: sg[0], t: sg[1], len: sg[1] - sg[0], x: p.x, y: p.y, z: p.z, v: v, vc: tc > 0 ? Math.min(v, tc) : v });
        });
      });
    });
    return C;
  }
  window.wsComps = comps;

  /* ---------- blok di luar semua solid domain ---------- */
  function surfFn(which) {
    try {
      var a = (typeof spAct === 'function') ? spAct(which) : null;
      if (a && a.tin && typeof rpTinFn === 'function') { var f = rpTinFn(a.tin); return function (x, y) { var r = f(x + offX, y + offY); return r ? (which === 'pit' ? r[0] : r[1]) : null; }; }
    } catch (e) {}
    if (which === 'pit') return (typeof OV !== 'undefined' && OV.pitF && OV.pitF.x.length) ? rpSurf(OV.pitF) : null;
    if (typeof imTopoOk === 'function' && !imTopoOk()) return null;
    return rpSurf(OV.topoF);
  }

  function blocksOut(o) {
    var m = BX.m, L = (window.gmTops ? gmTops() : GM.doms) || [], W = [];
    L.forEach(function (d) {
      var R = (typeof meGrpR === 'function') ? meGrpR(d) : null;
      if (R && R.mesh) W.push({ w: R.W || (R._W || (R._W = wfInside(R.mesh))), bb: meBBox(R.mesh) });
    });
    var tz = o.topo ? surfFn('topo') : null, pz = o.pit ? surfFn('pit') : null;
    if (o.topo && !tz) throw new Error('Topografi belum ada: matikan batas topografi atau impor topografi dulu (menu Data Spasial).');
    if (o.pit && !pz) throw new Error('Desain pit belum ada: matikan batas pit atau impor desain pit dulu (menu Data Spasial).');
    var out = [], nSol = 0, nTopo = 0, nPit = 0, cz = {}, cp = {};
    for (var i = 0; i < m.n; i++) {
      var x = m.x[i] - offX, y = m.y[i] - offY, z = m.z[i], inside = false;
      for (var q = 0; q < W.length && !inside; q++) {
        var b = W[q].bb;
        if (x < b[0] || x > b[1] || y < b[2] || y > b[3] || z < b[4] || z > b[5]) continue;
        if (W[q].w.f(x, y, z)) inside = true;
      }
      if (inside) { nSol++; continue; }
      var ck = Math.round(x * 2) + '_' + Math.round(y * 2);
      if (tz) { var zv = cz[ck]; if (zv === undefined) zv = cz[ck] = tz(x, y); if (zv == null || !isFinite(zv) || z > zv) { nTopo++; continue; } }
      if (pz) { var pv = cp[ck]; if (pv === undefined) pv = cp[ck] = pz(x, y); if (pv == null || !isFinite(pv) || z < pv) { nPit++; continue; } }
      out.push(i);
    }
    return { idx: out, nSol: nSol, nTopo: nTopo, nPit: nPit, nDom: W.length };
  }
  window.wsBlocks = blocksOut;

  /* ---------- siapkan satu run ---------- */
  function prep() {
    if (!BX.m) throw new Error('Belum ada block model aktif. Import block model, atau buat kerangka blok (AOI) di menu Block Model.');
    var D = domList();
    if (!D.doms.length) throw new Error('Belum ada variogram untuk waste. Dua pilihan: (a) di Geostatistik pilih populasi WASTE, fitting model, lalu "Simpan ke WASTE" \u2014 variogram waste sendiri dipakai untuk seluruh blok waste; atau (b) simpan parameter untuk sebuah domain vein, lalu blok waste di sekitarnya memakai variogram domain terdekat.');
    var o = wsPar(), B = blocksOut(o), C = comps(D.el);
    if (C.length < 1) throw new Error('Tidak ada komposit di luar flag domain. Periksa panjang komposit dan flag domain.');
    return { D: D, o: o, B: B, C: C, CI: pIndex(C, Math.max(10, (+o.rad || 60) / 2)) };
  }

  window.wsCheck = function () {
    try {
      var J = prep(), near = 0, far = 0, i, ns = 0;
      if (J.D.own) { near = 1; ns = 1; }
      else {
        var st = Math.max(1, Math.floor(J.B.idx.length / 2000));
        for (i = 0; i < J.B.idx.length; i += st) {
          var q = J.B.idx[i], r = J.D.idx ? J.D.idx.near(BX.m.x[q] - offX, BX.m.y[q] - offY, BX.m.z[q], +J.o.maxd * 3 + 50) : null;
          ns++; if (r && r.d <= +J.o.maxd) near++; else far++;
        }
      }
      WS.last = { chk: true, nb: J.B.idx.length, nSol: J.B.nSol, nTopo: J.B.nTopo, nPit: J.B.nPit, nDom: J.B.nDom,
                  nc: J.C.length, el: J.D.el, nd: J.D.doms.length, doms: J.D.doms.map(function (q) { return q.name; }),
                  own: !!J.D.own, pNear: ns ? near / ns : 0, pFar: ns ? far / ns : 0 };
      WS.msg = '';
    } catch (e) { WS.last = null; WS.msg = '<span class=warn>' + wE(e.message || e) + '</span>'; }
    if (window.mePanel) mePanel();
  };

  /* ---------- jalankan ---------- */
  window.wsRun = function () {
    if (WS.job) { WS.job.cancel = true; return; }
    try {
      if (typeof meEnsure === 'function') meEnsure();
      if (typeof imSync === 'function') imSync();
      var J0 = prep(), m = BX.m;
      if (!J0.B.idx.length) throw new Error('Tidak ada blok di luar solid yang memenuhi batas. Periksa batas topografi / pit, atau lengkapi cakupan block model dengan "Buat kerangka blok (AOI)".');
      if (ME.store && ME.store.el && ME.store.el !== J0.D.el) throw new Error('Hasil tersimpan memakai unsur ' + ME.store.el + ', parameter domain memakai ' + J0.D.el + '. Samakan unsurnya dulu.');
      if (!ME.store) { ME.store = meNew(); ME.store.el = J0.D.el; }
      if (!ME.store.el) ME.store.el = J0.D.el;
      ME.store.gc = ME.store.gc || meGcAttr();
      ME.undo = JSON.stringify(ME.store);
      /* indeks komposit waste per domain: radius pencarian memakai elipsoid domain itu */
      J0.D.doms.forEach(function (q) { q.I = okIndex(J0.C, Math.max(5, q.mo.R[0] * q.P.P[0].mult / 2)); });
      var items = J0.B.idx.map(function (i) { return { i: i, x: m.x[i], y: m.y[i], z: m.z[i], sx: m.sx[i], sy: m.sy[i], sz: m.sz[i] }; });
      var runId = (ME.store.runs.length ? ME.store.runs[ME.store.runs.length - 1].id : 0) + 1;
      WS.job = { items: items, i: 0, res: new Array(items.length), cancel: false, t0: performance.now(),
                 D: J0.D, o: J0.o, C: J0.C, CI: J0.CI, z: J0.C.map(function (c) { return c.vc; }), dc: {},
                 cnt: [0, 0, 0, 0, 0, 0], nIdw: 0, nEst: 0, fail: 0, byDom: {},
                 runId: runId, today: meToday(), B: J0.B };
      WS.msg = ''; if (window.mePanel) mePanel();
      setTimeout(step, 10);
    } catch (e) { WS.msg = '<span class=warn>' + wE(e.message || e) + '</span>'; if (window.mePanel) mePanel(); }
  };

  function idw(J, x, y, z) {
    var o = J.o, N = J.CI.list(x, y, z, +o.rad || 60, +o.nmax || 12);
    if (!N.length) return null;
    var p = +o.p || 2, sw = 0, sv = 0, i;
    for (i = 0; i < N.length; i++) {
      var d = Math.max(0.01, N[i].d), w = 1 / Math.pow(d, p);
      sw += w; sv += w * J.z[N[i].i];
    }
    if (!(sw > 0)) return null;
    return { est: sv / sw, pass: IDWP, sor: -99, ke: -99, kv: -99, ns: N.length, idw: true, sel: N.map(function (q) { return q.i; }) };
  }

  function step() {
    var J = WS.job; if (!J) return;
    var t = performance.now(), o = J.o, maxd = +o.maxd || 0;
    while (J.i < J.items.length && performance.now() - t < 45) {
      var it = J.items[J.i], x = it.x - offX, y = it.y - offY, z = it.z, res = null, dn = '(IDW)';
      /* variogram waste sendiri: dipakai untuk SELURUH blok waste, tanpa uji jarak ke domain */
      var own = J.D.own, nr = own ? { d: 0, i: 0 } : (J.D.idx ? J.D.idx.near(x, y, z, maxd) : null);
      if (own || (nr && nr.d <= maxd)) {
        var X = own ? J.D.doms[0] : J.D.doms[J.D.idx.pts[nr.i].di], P = X.P, mo = X.mo;
        var sk = X.name + '|' + it.sx + '_' + it.sy + '_' + it.sz, dc = J.dc[sk];
        if (!dc) { var D2 = okDisc([it.sx, it.sy, it.sz], P.nd || [3, 3, 2]); dc = J.dc[sk] = { D: D2, cbb: okCbb(mo, D2) }; }
        for (var p = 0; p < P.P.length; p++) {
          var pp = P.P[p], sel = okSearch(mo, X.I, J.C, x, y, z, +pp.mult, +pp.max, +pp.mph || 0);
          if (sel.length < +pp.min) continue;
          var r = okKrige(mo, J.C, J.z, sel, x, y, z, dc.D, dc.cbb);
          if (!r) continue;
          res = { est: r.est, pass: p + 1, sor: r.sor, ke: r.ke, kv: r.kv, ns: sel.length, sel: sel };
          J.cnt[p]++; dn = X.name; break;
        }
        /* dekat domain tetapi sampel waste tidak cukup untuk krige -> jatuh ke IDW, bukan dibiarkan kosong */
        if (!res) { res = idw(J, x, y, z); if (res) { J.nIdw++; dn = '(IDW)'; } }
      } else {
        res = idw(J, x, y, z); if (res) J.nIdw++;
      }
      if (res) {
        J.nEst++;
        J.byDom[dn] = (J.byDom[dn] || 0) + 1;
        if (typeof meSpasi === 'function' && res.sel) { try { var sp = meSpasi(J.C, res.sel, x, y, z); res.nh = sp.nh; res.dmin = sp.dmin; res.spasi = sp.spasi; } catch (e) {} }
      } else J.fail++;
      J.res[J.i] = res; J.i++;
      if (J.cancel) break;
    }
    var pc = J.items.length ? Math.round(100 * J.i / J.items.length) : 100, bar = document.getElementById('wsBar'), tx = document.getElementById('wsPct');
    if (bar) bar.style.width = pc + '%';
    if (tx) tx.textContent = pc + '% (' + fmt(J.i) + '/' + fmt(J.items.length) + ' blok)';
    if (J.cancel) { WS.job = null; ME.undo = null; WS.msg = 'Dibatalkan, tidak ada perubahan.'; if (window.mePanel) mePanel(); return; }
    if (J.i >= J.items.length) { commit(J); return; }
    setTimeout(step, 0);
  }

  function commit(J) {
    var S = ME.store, B = S.B, rowOf = new Map(), r, sum = 0, nv = 0, mn = 1e18, mx = -1e18;
    if (typeof meExPrep === 'function') { try { meExPrep(S); } catch (e) {} }
    for (r = 0; r < B.x.length; r++) rowOf.set(meKey(B.x[r], B.y[r], B.z[r]), r);
    var del = new Set(), keepKey = new Set();
    J.items.forEach(function (it) { keepKey.add(meKey(it.x, it.y, it.z)); });
    /* baris WASTE lama yang tidak lagi terpilih dibuang supaya tidak ada sisa run sebelumnya */
    for (r = 0; r < B.x.length; r++) if (B.dom[r] === WID && !keepKey.has(meKey(B.x[r], B.y[r], B.z[r]))) del.add(r);
    J.items.forEach(function (it, q) {
      var res = J.res[q], k = meKey(it.x, it.y, it.z), row = rowOf.get(k);
      if (!res) { if (row !== undefined && B.dom[row] === WID) del.add(row); return; }
      if (row === undefined) { row = B.x.length; MEF.forEach(function (f) { B[f].push(0); }); Object.keys(B.ex || {}).forEach(function (e) { B.ex[e].push(-99); }); rowOf.set(k, row); }
      else del.delete(row);
      B.x[row] = it.x; B.y[row] = it.y; B.z[row] = it.z; B.sx[row] = it.sx; B.sy[row] = it.sy; B.sz[row] = it.sz;
      B.dom[row] = WID; B.type[row] = 3; B.date[row] = J.today; B.run[row] = J.runId;
      B.est[row] = res.est; B.pass[row] = res.pass; B.sor[row] = res.sor; B.ke[row] = res.ke; B.kv[row] = res.kv; B.ns[row] = res.ns;
      if (B.nh) { B.nh[row] = res.nh == null ? 0 : res.nh; B.dmin[row] = res.dmin == null ? -99 : res.dmin; B.spasi[row] = res.spasi == null ? -99 : res.spasi; }
      Object.keys(B.ex || {}).forEach(function (e) { B.ex[e][row] = -99; });
      sum += res.est; nv++; if (res.est < mn) mn = res.est; if (res.est > mx) mx = res.est;
    });
    if (del.size) {
      var keep = [];
      for (r = 0; r < B.x.length; r++) if (!del.has(r)) keep.push(r);
      MEF.forEach(function (f) { var a = B[f]; B[f] = keep.map(function (q) { return a[q]; }); });
      Object.keys(B.ex || {}).forEach(function (e) { var a = B.ex[e]; B.ex[e] = keep.map(function (q) { return a[q]; }); });
    }
    S.dn[WID] = WNAME;
    var ms = Math.round(performance.now() - J.t0), cm = 0;
    J.C.forEach(function (c) { cm += c.vc; });
    S.runs.push({ id: J.runId, date: new Date().toISOString().slice(0, 16).replace('T', ' '), user: (typeof meUser === 'function' ? meUser() : ''),
                  dom: WNAME, domId: WID, el: S.el, par: (J.D.own ? ('waste: variogram sendiri (' + (J.D.doms[0].P.src || 'fitting Geostatistik') + '), IDW p=' + J.o.p + ' bila sampel kurang') : ('waste: variogram domain terdekat (<= ' + J.o.maxd + ' m), selebihnya IDW p=' + J.o.p)),
                  first: true, force: true, parChg: false, holes: [], nHole: 0, nComp: J.C.length,
                  nIn: J.items.length, nAff: J.items.length, nEst: J.nEst, nFail: J.fail, nAddC: 0, nRev: 0,
                  cnt: J.cnt, ms: ms, waste: true, nIdw: J.nIdw, byDom: J.byDom,
                  v: J.nEst ? { comp: cm / J.C.length, mean: sum / nv, gc: null, vol: 0, ton: 0, metal: 0, metalGc: 0 } : null });
    S.ver = Date.now();
    WS.job = null; ME.undo = null;
    WS.last = { nb: J.items.length, nEst: J.nEst, fail: J.fail, nIdw: J.nIdw, byDom: J.byDom,
                mean: nv ? sum / nv : null, min: nv ? mn : null, max: nv ? mx : null,
                nc: J.C.length, cnt: J.cnt.slice(), ms: ms, nSol: J.B.nSol, nTopo: J.B.nTopo, nPit: J.B.nPit };
    WS.msg = '&#10003; Estimasi waste selesai: <b>' + fmt(J.nEst) + '</b> blok terestimasi' + (J.fail ? ', ' + fmt(J.fail) + ' tanpa sampel' : '') +
      ' &middot; ' + fmt(J.nEst - J.nIdw) + ' kriging (' + (J.D.own ? 'variogram WASTE sendiri' : 'variogram domain terdekat') + '), ' + fmt(J.nIdw) + ' IDW' +
      ' &middot; rata-rata ' + (nv ? (sum / nv).toFixed(3) : '-') + ' &middot; ' + (ms / 1000).toFixed(1) + ' detik.';
    if (typeof meApply === 'function') { try { meApply(true); } catch (e) {} }
    if (window.clsBuild) { try { clsBuild(true); } catch (e) {} }
    if (window.BX) BX.sc = {};
    if (SA.dirty) SA.dirty();
    if (window.mePanel) mePanel();
    if (typeof updatePlot === 'function') updatePlot();
  }

  /* ---------- panel: bagian di Model Estimation ---------- */
  function fld(k, lab, tip, step) {
    var o = wsPar();
    return '<div><label title="' + tip + '">' + lab + '</label><input type=number step="' + (step || 'any') + '" value="' + o[k] +
      '" onchange="wsPar()[\'' + k + '\']=+this.value;WS.last=null;mePanel()"></div>';
  }

  window.wsBox = function () {
    var m = BX.m, o = wsPar();
    var h = '<div class=gmsec><h4>Estimasi waste (material di luar seluruh solid)</h4>';
    if (!m) return h + '<div class=hint>Belum ada block model aktif. Import block model, atau buat <b>kerangka blok (AOI)</b> di menu Block Model.</div></div>';
    var DL = ((window.gmTops ? gmTops() : GM.doms) || []).filter(function (d) { return meParOf(d); });
    h += '<div class=hint>Blok di luar semua solid domain diestimasi dari komposit interval yang <b>tidak di-flag domain apa pun</b> (hard boundary waste). ' +
      'Tiap blok memakai <b>variogram &amp; elipsoid domain terdekat</b>; blok yang jaraknya melebihi ambang di bawah diisi <b>IDW</b> ' +
      '(ditandai <code>est_pass = 9</code>). Hasil ditandai <code>domain_est = WASTE</code> dan <code>est_type = 3</code>: tidak ikut pelaporan sumber daya ' +
      'dan tidak diberi kelas keyakinan, tetapi volume &amp; tonasenya bisa dilaporkan bersama ore di Reporting BM.</div>';
    if (!DL.length && !wsOwn()) return h + '<div class=hint><span class=warn>Belum ada variogram untuk waste.</span> Dua jalan: di <b>Geostatistik</b> pilih populasi <b>WASTE (di luar semua domain)</b>, fitting model, lalu <b>Simpan ke WASTE</b> &mdash; atau simpan parameter untuk sebuah domain vein, lalu blok waste di sekitarnya memakai variogram domain terdekat.</div></div>';
    var OWN = wsOwn(), MD = wsMode();
    h += '<div class=lab>Variogram yang dipakai</div><div class=f style="margin-bottom:4px"><select onchange="wsPar().mode=this.value;WS.last=null;mePanel()">' +
      '<option value=auto' + (o.mode === 'auto' ? ' selected' : '') + '>Otomatis &mdash; variogram waste sendiri bila ada, kalau tidak domain terdekat</option>' +
      '<option value=dom' + (o.mode === 'dom' ? ' selected' : '') + '>Variogram domain terdekat</option>' +
      '</select></div>';
    h += OWN
      ? '<div class=hint style="margin:-2px 0 6px">&#10003; Variogram waste sendiri tersimpan: unsur <b>' + wE(OWN.el) + '</b> &middot; ' + wE(OWN.src || '') + ' &middot; ' + wE(OWN.date || '') +
        '<br>' + (MD === 'own' ? 'Dipakai untuk <b>seluruh</b> blok waste; IDW hanya bila sampel di sekitar blok tidak cukup.' : 'Sedang <b>tidak</b> dipakai karena mode disetel ke domain terdekat.') + '</div>'
      : '<div class=hint style="margin:-2px 0 6px">Belum ada variogram waste sendiri. Di <b>Geostatistik</b>: pilih populasi <b>WASTE (di luar semua domain)</b> pada bilah Domain, fitting model, lalu tab <b>Uji estimasi</b> &rarr; <b>Simpan ke WASTE</b>. Sementara itu dipakai variogram <b>domain terdekat</b>.</div>';
    h += '<div class=g2 style="margin-bottom:4px">' +
      (MD === 'own' ? '<div><label title="Tidak berlaku: variogram waste sendiri dipakai untuk seluruh blok waste">Jarak maks. ke domain (m)</label><input type=text disabled value="tidak dipakai"></div>'
                    : fld('maxd', 'Jarak maks. ke domain (m)', 'Blok dengan komposit domain terdekat dalam jarak ini dikrige memakai variogram domain itu. Lebih jauh dari ini -> IDW.', '1')) +
      fld('mult', 'Pengali radius', 'Radius pencarian = radius elipsoid domain terdekat x pengali ini. Halo biasanya lebih menerus daripada vein, jadi > 1 wajar.', '0.1') +
      fld('L', 'Panjang komposit (m)', 'Komposit panjang tetap pada interval di luar flag domain. 0 = pakai interval assay apa adanya.', '0.5') +
      fld('tc', 'Top-cut', 'Batas atas kadar komposit waste (0 = tanpa top-cut). Mencegah satu assay tinggi di luar solid menarik kadar halo.', '0.1') + '</div>';
    h += '<div class=lab>IDW untuk blok jauh dari semua domain</div><div class=g3 style="margin-bottom:4px">' +
      fld('p', 'Pangkat jarak', 'Bobot = 1 / jarak^pangkat. 2 = inverse distance squared (lazim).', '0.5') +
      fld('nmax', 'Maks titik', 'Jumlah komposit waste terdekat yang dipakai satu blok.', '1') +
      fld('rad', 'Radius (m)', 'Komposit waste di luar radius ini tidak dipakai. Blok tanpa satu pun komposit dalam radius dibiarkan tanpa kadar.', '5') + '</div>';
    h += '<label class=sw><input type=checkbox ' + (o.topo ? 'checked' : '') + ' onchange="wsPar().topo=this.checked?1:0;WS.last=null;mePanel()">Hanya blok di bawah topografi aktif</label>' +
      '<label class=sw><input type=checkbox ' + (o.pit ? 'checked' : '') + ' onchange="wsPar().pit=this.checked?1:0;WS.last=null;mePanel()">Hanya blok di dalam desain pit</label>';
    if (WS.job) {
      h += '<div class=row><button class=btn-pri onclick="wsRun()">Batalkan</button><div class=prog><div id=wsBar style="height:100%;width:0;background:var(--ac);transition:width .2s"></div></div></div><div id=wsPct class=note></div>';
    } else {
      h += '<div class=g2 style="margin-top:4px"><button onclick="wsCheck()">Periksa dulu</button><button class=btn-pri onclick="wsRun()">&#9654; Jalankan estimasi waste</button></div>';
      var L = WS.last;
      if (L && L.chk) h += '<div class=hint style="margin-top:4px"><b>' + fmt(L.nb) + '</b> blok di luar solid akan diestimasi dari <b>' + fmt(L.nc) + '</b> komposit waste (unsur ' + wE(L.el) + ').' +
        (L.own ? '<br>variogram: <b>waste sendiri</b> &mdash; dipakai untuk seluruh blok; IDW hanya bila sampel kurang'
               : '<br>variogram domain terdekat dari ' + L.nd + ' domain: ' + wE(L.doms.join(', ')) +
                 '<br>perkiraan pembagian: &asymp; ' + Math.round(L.pNear * 100) + '% kriging, &asymp; ' + Math.round(L.pFar * 100) + '% IDW (cuplikan)') +
        '<br>dilewati: ' + fmt(L.nSol) + ' blok di dalam ' + L.nDom + ' solid' + (L.nTopo ? ' &middot; ' + fmt(L.nTopo) + ' di atas topografi' : '') + (L.nPit ? ' &middot; ' + fmt(L.nPit) + ' di luar pit' : '') + '</div>';
      else if (L) {
        var bd = Object.keys(L.byDom || {}).map(function (k) { return wE(k) + ' ' + fmt(L.byDom[k]); }).join(' &middot; ');
        h += '<div class=hint style="margin-top:4px">Run terakhir: <b>' + fmt(L.nEst) + '</b> dari ' + fmt(L.nb) + ' blok terestimasi' + (L.fail ? ', ' + fmt(L.fail) + ' tanpa sampel' : '') +
          '<br>' + fmt(L.nEst - L.nIdw) + ' kriging (pass 1/2/3: ' + (L.cnt[0] || 0) + '/' + (L.cnt[1] || 0) + '/' + (L.cnt[2] || 0) + ') &middot; ' + fmt(L.nIdw) + ' IDW' +
          (bd ? '<br>variogram yang dipakai: ' + bd : '') +
          '<br>kadar waste: rata-rata <b>' + (L.mean == null ? '-' : L.mean.toFixed(3)) + '</b>, rentang ' + (L.min == null ? '-' : L.min.toFixed(3)) + ' &ndash; ' + (L.max == null ? '-' : L.max.toFixed(3)) +
          ' &middot; dari ' + fmt(L.nc) + ' komposit waste</div>';
      }
    }
    if (WS.msg) h += '<div class=hint style="margin-top:4px">' + WS.msg + '</div>';
    return h + '</div>';
  };

  /* sisipkan bagian di akhir panel Model Estimation */
  if (typeof window.mePanel === 'function') {
    var _mp = window.mePanel;
    window.mePanel = function () {
      var r = _mp.apply(this, arguments);
      try {
        var b = document.getElementById('meBody');
        if (b && BX.m) {
          var old = document.getElementById('wsSec');
          if (old) old.parentNode.removeChild(old);
          var w = document.createElement('div'); w.id = 'wsSec'; w.innerHTML = wsBox();
          b.appendChild(w);
        }
      } catch (e) { console.error(e); }
      return r;
    };
  }
})();
