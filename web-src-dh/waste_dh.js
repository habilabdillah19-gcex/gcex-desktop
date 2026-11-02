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
              terpisah tegas dari est_type 1 (koreksi di solid) dan 2 (blok tambahan di solid).

   est_type = 3 membuat blok waste:
     - tidak pernah ikut pelaporan sumber daya per domain vein;
     - tidak diberi kelas keyakinan (Measured / Indicated / Inferred) — lihat cls_dh.js;
     - tetap terbawa ke Reporting BM sebagai material, jadi volume & tonase waste di bawah
       topografi atau di dalam pit bisa dilaporkan bersama ore.

   Blok waste harus SUDAH ADA di block model aktif (modul ini tidak membuat blok baru). Bila cakupan
   .mdl impor lebih sempit dari area of interest, lengkapi dulu dengan "Buat kerangka blok (AOI)"
   di menu Block Model (aoi_dh.js).                                                                */
(function () {
  if (typeof ME === 'undefined' || typeof BX === 'undefined') return;
  var WID = '__waste', WNAME = 'WASTE';
  var WS = { job: null, msg: '', last: null };
  window.WS = WS;
  window.wsId = function () { return WID; };

  function wE(s) { return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) { return '&#' + c.charCodeAt(0) + ';'; }); }
  function fmt(v, d) { return v == null || !isFinite(v) ? '-' : (+v).toLocaleString('id-ID', { minimumFractionDigits: d || 0, maximumFractionDigits: d || 0 }); }

  /* ---------- parameter waste (disimpan bersama hasil estimasi di proyek) ---------- */
  function defPar() { return { src: '', tc: 0, L: 2, mult: 1, topo: 1, pit: 0, on: false }; }
  window.wsPar = function () {
    if (!ME.store) return defPar();
    if (!ME.store.ws) ME.store.ws = defPar();
    var o = ME.store.ws;
    Object.keys(defPar()).forEach(function (k) { if (o[k] === undefined) o[k] = defPar()[k]; });
    return o;
  };

  /* parameter kriging waste = salinan parameter domain sumber, dengan top-cut, panjang komposit dan
     pengali radius sendiri (kontinuitas halo berbeda dari vein, kadarnya jauh lebih rendah) */
  function parOf() {
    var o = wsPar(), L = (window.gmTops ? gmTops() : (window.GM ? GM.doms : [])) || [];
    var d = null;
    L.forEach(function (q) { if (String(q.id) === String(o.src)) d = q; });
    if (!d) L.forEach(function (q) { if (!d && meParOf(q)) d = q; });
    var P = d ? meParOf(d) : null;
    if (!P) return null;
    var R = JSON.parse(JSON.stringify(P));
    R.tc = +o.tc || 0; R.L = +o.L || 0; R.srcDom = d.name;
    R.P = (R.P || []).map(function (p) { return Object.assign({}, p, { mult: (+p.mult || 1) * (+o.mult || 1) }); });
    return R;
  }
  window.wsParOf = parOf;

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
  function comps(P) {
    var ei = elements.indexOf(P.el), L = +P.L || 0, tc = +P.tc || 0, R = runsOut(), C = [];
    if (ei < 0) throw new Error('unsur ' + P.el + ' tidak ada di database');
    Object.keys(R).forEach(function (id) {
      var A = (groupedAssays[id] || []).filter(function (a) { return a[4][ei] !== null && a[2] > a[1]; }).sort(function (p, q) { return p[1] - q[1]; });
      if (!A.length) return;
      R[id].forEach(function (r) {
        var n = L > 0 ? Math.max(1, Math.round((r[1] - r[0]) / L)) : 0, S = [];
        if (n) { for (var k = 0; k < n; k++) S.push([r[0] + (r[1] - r[0]) * k / n, r[0] + (r[1] - r[0]) * (k + 1) / n]); }
        else A.forEach(function (a) { var f = Math.max(a[1], r[0]), t = Math.min(a[2], r[1]); if (t > f) S.push([f, t]); });
        S.forEach(function (sg) {
          var sl = 0, sv = 0;
          A.forEach(function (a) { var o = Math.min(sg[1], a[2]) - Math.max(sg[0], a[1]); if (o > 0) { sl += o; sv += o * a[4][ei]; } });
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

  /* ---------- perkiraan sebelum dijalankan ---------- */
  window.wsCheck = function () {
    try {
      if (!BX.m) throw new Error('Belum ada block model aktif.');
      var P = parOf();
      if (!P) throw new Error('Belum ada domain yang punya parameter estimasi. Simpan parameter dari menu Geostatistik dulu (dipakai sebagai dasar parameter waste).');
      var o = wsPar(), B = blocksOut(o), C = comps(P);
      WS.last = { nb: B.idx.length, nSol: B.nSol, nTopo: B.nTopo, nPit: B.nPit, nDom: B.nDom, nc: C.length, dom: P.srcDom, el: P.el };
      WS.msg = '';
    } catch (e) { WS.last = null; WS.msg = '<span class=warn>' + wE(e.message || e) + '</span>'; }
    if (window.mePanel) mePanel();
  };

  /* ---------- jalankan ---------- */
  window.wsRun = function () {
    if (WS.job) { WS.job.cancel = true; return; }
    try {
      var m = BX.m;
      if (!m) throw new Error('Belum ada block model aktif.');
      if (typeof meEnsure === 'function') meEnsure();
      if (typeof imSync === 'function') imSync();
      var P = parOf();
      if (!P) throw new Error('Belum ada domain dengan parameter estimasi; parameter waste memakai salinannya.');
      if (ME.store && ME.store.el && ME.store.el !== P.el) throw new Error('Hasil tersimpan memakai unsur ' + ME.store.el + ', parameter waste memakai ' + P.el + '. Samakan unsurnya dulu.');
      var o = wsPar(), B = blocksOut(o);
      if (!B.idx.length) throw new Error('Tidak ada blok di luar solid yang memenuhi batas. Periksa batas topografi / pit, atau lengkapi cakupan block model dengan "Buat kerangka blok (AOI)".');
      var C = comps(P);
      if (C.length < 3) throw new Error('Komposit di luar flag domain hanya ' + C.length + '. Perlu minimal 3; periksa panjang komposit dan flag domain.');
      if (!ME.store) { ME.store = meNew(); ME.store.el = P.el; }
      if (!ME.store.el) ME.store.el = P.el;
      ME.store.gc = ME.store.gc || meGcAttr();
      ME.undo = JSON.stringify(ME.store);
      var mo = meModel(P), I = okIndex(C, Math.max(5, mo.R[0] * P.P[0].mult / 2));
      var items = B.idx.map(function (i) { return { i: i, x: m.x[i], y: m.y[i], z: m.z[i], sx: m.sx[i], sy: m.sy[i], sz: m.sz[i] }; });
      var runId = (ME.store.runs.length ? ME.store.runs[ME.store.runs.length - 1].id : 0) + 1;
      WS.job = { items: items, i: 0, res: new Array(items.length), cancel: false, t0: performance.now(),
                 P: P, mo: mo, C: C, I: I, z: C.map(function (c) { return c.vc; }), dc: {}, cnt: [0, 0, 0, 0, 0, 0],
                 nEst: 0, fail: 0, runId: runId, today: meToday(), B: B };
      WS.msg = ''; if (window.mePanel) mePanel();
      setTimeout(step, 10);
    } catch (e) { WS.msg = '<span class=warn>' + wE(e.message || e) + '</span>'; if (window.mePanel) mePanel(); }
  };

  function step() {
    var J = WS.job; if (!J) return;
    var t = performance.now(), P = J.P, mo = J.mo;
    while (J.i < J.items.length && performance.now() - t < 45) {
      var it = J.items[J.i], sk = it.sx + '_' + it.sy + '_' + it.sz, dc = J.dc[sk];
      if (!dc) { var D2 = okDisc([it.sx, it.sy, it.sz], P.nd || [3, 3, 2]); dc = J.dc[sk] = { D: D2, cbb: okCbb(mo, D2) }; }
      var x = it.x - offX, y = it.y - offY, z = it.z, res = null;
      for (var p = 0; p < P.P.length; p++) {
        var pp = P.P[p], sel = okSearch(mo, J.I, J.C, x, y, z, +pp.mult, +pp.max, +pp.mph || 0);
        if (sel.length < +pp.min) continue;
        var r = okKrige(mo, J.C, J.z, sel, x, y, z, dc.D, dc.cbb);
        if (!r) continue;
        res = { est: r.est, pass: p + 1, sor: r.sor, ke: r.ke, kv: r.kv, ns: sel.length };
        if (typeof meSpasi === 'function') { var sp = meSpasi(J.C, sel, x, y, z); res.nh = sp.nh; res.dmin = sp.dmin; res.spasi = sp.spasi; }
        J.cnt[p]++; break;
      }
      if (res) J.nEst++; else J.fail++;
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
    var del = new Set();
    /* baris WASTE lama yang tidak lagi terpilih dibuang supaya tidak ada sisa dari run sebelumnya */
    var keepKey = new Set();
    J.items.forEach(function (it) { keepKey.add(meKey(it.x, it.y, it.z)); });
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
                  dom: WNAME, domId: WID, el: S.el, par: 'waste (dasar: ' + J.P.srcDom + ')', first: true, force: true, parChg: false,
                  holes: [], nHole: 0, nComp: J.C.length, nIn: J.items.length, nAff: J.items.length, nEst: J.nEst, nFail: J.fail,
                  nAddC: 0, nRev: 0, cnt: J.cnt, ms: ms, waste: true,
                  v: J.nEst ? { comp: cm / J.C.length, mean: sum / nv, gc: null, vol: 0, ton: 0, metal: 0, metalGc: 0 } : null });
    S.ver = Date.now();
    WS.job = null; ME.undo = null;
    WS.last = { nb: J.items.length, nEst: J.nEst, fail: J.fail, mean: nv ? sum / nv : null, min: nv ? mn : null, max: nv ? mx : null,
                nc: J.C.length, cnt: J.cnt.slice(), ms: ms, dom: J.P.srcDom, nSol: J.B.nSol, nTopo: J.B.nTopo, nPit: J.B.nPit };
    WS.msg = '&#10003; Estimasi waste selesai: <b>' + fmt(J.nEst) + '</b> blok terestimasi' + (J.fail ? ', ' + fmt(J.fail) + ' tanpa sampel cukup' : '') +
      ' &middot; rata-rata ' + (nv ? (sum / nv).toFixed(3) : '-') + ' &middot; ' + (ms / 1000).toFixed(1) + ' detik.';
    if (typeof meApply === 'function') { try { meApply(true); } catch (e) {} }
    if (window.clsBuild) { try { clsBuild(true); } catch (e) {} }
    if (window.BX) BX.sc = {};
    if (SA.dirty) SA.dirty();
    if (window.mePanel) mePanel();
    if (typeof updatePlot === 'function') updatePlot();
  }

  /* ---------- panel: bagian ⑥ di Model Estimation ---------- */
  function sel(id, list, cur, on) {
    return '<select id=' + id + ' onchange="' + on + '">' + list.map(function (q) {
      return '<option value="' + wE(q[0]) + '"' + (String(q[0]) === String(cur) ? ' selected' : '') + '>' + wE(q[1]) + '</option>';
    }).join('') + '</select>';
  }
  function fld(k, lab, tip, step) {
    var o = wsPar();
    return '<div><label title="' + tip + '">' + lab + '</label><input type=number step="' + (step || 'any') + '" value="' + o[k] +
      '" onchange="wsPar()[\'' + k + '\']=+this.value;WS.last=null;mePanel()"></div>';
  }

  window.wsBox = function () {
    var m = BX.m, o = wsPar();
    var h = '<div class=gmsec><h4>&#9317; Estimasi waste (material di luar seluruh solid)</h4>';
    if (!m) return h + '<div class=hint>Belum ada block model aktif.</div></div>';
    var DL = ((window.gmTops ? gmTops() : GM.doms) || []).filter(function (d) { return meParOf(d); }).map(function (d) { return [d.id, d.name]; });
    h += '<div class=hint>Blok di luar semua solid domain diestimasi dari komposit interval yang <b>tidak di-flag domain apa pun</b> (hard boundary waste). ' +
      'Hasilnya ditandai <code>domain_est = WASTE</code> dan <code>est_type = 3</code>: tidak ikut pelaporan sumber daya dan tidak diberi kelas keyakinan, ' +
      'tetapi volume &amp; tonasenya bisa dilaporkan bersama ore di Reporting BM.</div>';
    if (!DL.length) return h + '<div class=hint><span class=warn>Belum ada domain dengan parameter estimasi.</span> Parameter waste memakai salinan parameter sebuah domain (variogram &amp; elipsoid); simpan dulu dari menu Geostatistik.</div></div>';
    h += '<div class=g2 style="margin-bottom:4px">' + '<div><label title="Variogram &amp; elipsoid disalin dari domain ini, lalu top-cut / panjang komposit / radius di bawah berlaku untuk waste">Dasar parameter</label>' +
      sel('wsSrc', DL, o.src || DL[0][0], 'wsPar().src=this.value;WS.last=null;mePanel()') + '</div>' +
      fld('mult', 'Pengali radius', 'Radius pencarian waste = radius domain sumber &times; pengali ini. Halo biasanya lebih menerus daripada vein, jadi > 1 wajar.', '0.1') +
      fld('L', 'Panjang komposit (m)', 'Komposit panjang tetap pada interval di luar flag domain. 0 = pakai interval assay apa adanya.', '0.5') +
      fld('tc', 'Top-cut', 'Batas atas kadar komposit waste (0 = tanpa top-cut). Mencegah satu assay tinggi di luar solid menarik kadar halo.', '0.1') + '</div>';
    h += '<label class=sw><input type=checkbox ' + (o.topo ? 'checked' : '') + ' onchange="wsPar().topo=this.checked?1:0;WS.last=null;mePanel()">Hanya blok di bawah topografi aktif</label>' +
      '<label class=sw><input type=checkbox ' + (o.pit ? 'checked' : '') + ' onchange="wsPar().pit=this.checked?1:0;WS.last=null;mePanel()">Hanya blok di dalam desain pit</label>';
    if (WS.job) {
      h += '<div class=row><button class=btn-pri onclick="wsRun()">Batalkan</button><div class=prog><div id=wsBar style="height:100%;width:0;background:var(--ac);transition:width .2s"></div></div></div><div id=wsPct class=note></div>';
    } else {
      h += '<div class=g2 style="margin-top:4px"><button onclick="wsCheck()">Periksa dulu</button><button class=btn-pri onclick="wsRun()">&#9654; Jalankan estimasi waste</button></div>';
      var L = WS.last;
      if (L && L.nEst === undefined) h += '<div class=hint style="margin-top:4px"><b>' + fmt(L.nb) + '</b> blok di luar solid akan diestimasi dari <b>' + fmt(L.nc) + '</b> komposit waste (unsur ' + wE(L.el) + ', dasar parameter ' + wE(L.dom) + ').' +
        '<br>dilewati: ' + fmt(L.nSol) + ' blok di dalam ' + L.nDom + ' solid' + (L.nTopo ? ' &middot; ' + fmt(L.nTopo) + ' di atas topografi' : '') + (L.nPit ? ' &middot; ' + fmt(L.nPit) + ' di luar pit' : '') + '</div>';
      else if (L && L.nEst !== undefined) h += '<div class=hint style="margin-top:4px">Run terakhir: <b>' + fmt(L.nEst) + '</b> dari ' + fmt(L.nb) + ' blok terestimasi' + (L.fail ? ', ' + fmt(L.fail) + ' tanpa sampel cukup' : '') +
        ' &middot; pass 1/2/3: ' + (L.cnt[0] || 0) + '/' + (L.cnt[1] || 0) + '/' + (L.cnt[2] || 0) +
        '<br>kadar waste: rata-rata <b>' + (L.mean == null ? '-' : L.mean.toFixed(3)) + '</b>, rentang ' + (L.min == null ? '-' : L.min.toFixed(3)) + ' &ndash; ' + (L.max == null ? '-' : L.max.toFixed(3)) +
        ' &middot; dari ' + fmt(L.nc) + ' komposit waste</div>';
    }
    if (WS.msg) h += '<div class=hint style="margin-top:4px">' + WS.msg + '</div>';
    return h + '</div>';
  };

  /* sisipkan bagian ⑥ di akhir panel Model Estimation */
  if (typeof window.mePanel === 'function') {
    var _mp = window.mePanel;
    window.mePanel = function () {
      var r = _mp.apply(this, arguments);
      try {
        var b = document.getElementById('meBody') || document.getElementById('pME');
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
