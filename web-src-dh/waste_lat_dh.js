/* ================= ESTIMASI WASTE LATERIT — material di luar seluruh permukaan lapisan =================
   Pasangan waste_dh.js untuk jalur Stratified-Laterite. Menu Stratified-Laterite punya penyimpanan
   (SL.S) dan mesin estimasinya sendiri: setiap blok dicari lapisannya lewat slLayerAt(), dan blok yang
   TIDAK jatuh di lapisan mana pun (sl_lapisan = kosong) tidak pernah diestimasi. Untuk laporan volume
   ore DAN waste di bawah topografi / di dalam desain pit, blok itu justru harus punya kadar.

   Dua zona waste, masing-masing dengan ruang UNFOLD-nya sendiri supaya pencarian sampel mengikuti
   kelengkungan permukaan lapisan, bukan jarak lurus:

     bawah : blok di bawah permukaan terbawah model. Koordinat unfold z = kedalaman di bawah
             permukaan itu  ->  z = z_dasar(x,y) - z_blok.
     atas  : blok di atas permukaan teratas model tetapi masih DI BAWAH topografi aktif (mis. kontak
             teratas berada di bawah permukaan tanah). Koordinat unfold z = tinggi di atas kontak
             teratas  ->  z = z_blok - z_atap(x,y).  Blok di atas topografi adalah udara, bukan waste,
             jadi tidak pernah ikut.
     (luar): blok di luar cakupan grid permukaan (permukaan NaN). Tidak ada kerangka unfold yang bisa
             dipakai, jadi memakai elevasi apa adanya (3D biasa). Opsional, bawaan mati.

   Sampel: komposit dari interval geologi yang kodenya TIDAK dipetakan ke lapisan mana pun — hard
   boundary waste, sama semangatnya dengan jalur vein. Tiap komposit ditempatkan ke zona yang sesuai
   dengan posisinya sendiri terhadap permukaan, lalu dipakai hanya untuk blok di zona yang sama.

   Metode: IDW di ruang unfold, dengan jarak anisotropis (elipsoid r1/r2 horizontal, r3 vertikal searah
   azimut) — persis cara slStep menghitung jarak. Bukan kriging: variogram lapisan tidak berlaku di luar
   lapisan, dan di jalur laterit tidak ada "domain terdekat" yang variogramnya pantas diwarisi.

   Hasil ditulis ke SL.S yang sedang aktif: sl_<unsur> terisi, sl_pass = 9 (penanda IDW), sl_ns, dan
   sl_lapisan diberi kategori baru 'WASTE (di luar lapisan)'. Karena itu, SETIAP kali estimasi lapisan
   dijalankan ulang, estimasi waste ini harus dijalankan ulang juga (SL.S dibentuk baru).              */
(function () {
  if (typeof SL === 'undefined' || typeof BX === 'undefined') return;
  var WNAME = 'WASTE (di luar lapisan)', IDWP = 9;
  var WL = { job: null, msg: '', last: null };
  window.WL = WL;

  function lE(s) { return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) { return '&#' + c.charCodeAt(0) + ';'; }); }
  function fmt(v, d) { return v == null || !isFinite(v) ? '-' : (+v).toLocaleString('id-ID', { minimumFractionDigits: d || 0, maximumFractionDigits: d || 0 }); }

  function defPar() { return { comp: 2, p: 2, nmin: 2, nmax: 12, az: 0, r1: 60, r2: 60, r3: 3, luar: 0 }; }
  window.wlPar = function () {
    if (!SL.o.ws) SL.o.ws = defPar();
    var o = SL.o.ws, D = defPar();
    Object.keys(D).forEach(function (k) { if (o[k] === undefined) o[k] = D[k]; });
    return o;
  };

  /* elipsoid jarak (sama bentuk dengan slMo tanpa variogram: hanya untuk bobot jarak IDW) */
  function ellip(o) {
    var a = (+o.az || 0) * Math.PI / 180;
    return { vM: [Math.sin(a), Math.cos(a), 0], vS: [Math.sin(a + Math.PI / 2), Math.cos(a + Math.PI / 2), 0], vN: [0, 0, 1],
             c0: 0, cs: [1], A: [Math.max(1, +o.r1 || 60)], B: [Math.max(1, +o.r2 || 60)], Cn: [Math.max(0.2, +o.r3 || 3)],
             R: [Math.max(1, +o.r1 || 60), Math.max(1, +o.r2 || 60), Math.max(0.2, +o.r3 || 3)] };
  }

  /* permukaan topografi aktif (koordinat lokal) — pembatas zona 'atas' */
  function topoFn() {
    try {
      var a = (typeof spAct === 'function') ? spAct('topo') : null;
      if (a && a.tin && typeof rpTinFn === 'function') { var f = rpTinFn(a.tin); return function (x, y) { var r = f(x + offX, y + offY); return r ? r[1] : null; }; }
    } catch (e) {}
    if (typeof imTopoOk === 'function' && !imTopoOk()) return null;
    return (typeof OV !== 'undefined' && OV.topoF && OV.topoF.x.length) ? rpSurf(OV.topoF) : null;
  }

  /* zona + koordinat unfold satu titik present (koordinat lokal) */
  function zoneOf(R, x, y, z, tz) {
    var q = (typeof slRest === 'function') ? slRest(x, y, z) : [x, y, z];
    var t = slAt(R, R.S[0], q[0], q[1]), b = slAt(R, R.S[R.nT], q[0], q[1]);
    if (isFinite(b) && q[2] <= b) return { zn: 'bawah', x: q[0], y: q[1], z: b - q[2] };
    if (isFinite(t) && q[2] > t) {
      if (!tz) return null;                       /* tanpa topografi, 'atas' tidak bisa dipisahkan dari udara */
      var ztop = tz(x, y);
      if (ztop == null || !isFinite(ztop) || z > ztop) return null;   /* di atas tanah = udara */
      return { zn: 'atas', x: q[0], y: q[1], z: q[2] - t };
    }
    if (!isFinite(t) && !isFinite(b)) return { zn: 'luar', x: q[0], y: q[1], z: q[2] };
    return null;                                  /* di dalam tumpukan lapisan: bukan waste */
  }

  /* ---------- komposit dari interval yang kodenya tidak dipetakan ke lapisan ---------- */
  function comps(R, els, tz) {
    var o = wlPar(), ci = SL.ci, cm = {}, out = { bawah: [], atas: [], luar: [] }, nSkip = 0;
    if (ci < 0 || !(window.CAT || [])[ci]) throw new Error('kolom geologi lapisan belum dipilih (bagian ① Lapisan).');
    SL.L.forEach(function (l, i) { (l.codes || []).forEach(function (c) { cm[c] = i; }); });
    var EI = els.map(function (e) { return elements.indexOf(e); }), cl = Math.max(0, +o.comp || 0);
    Object.keys(holeData).forEach(function (id) {
      var h = holeData[id], IV = [];
      try { IV = geoIntervals(ci, id) || []; } catch (e) { IV = []; }
      var A = (groupedAssays[id] || []).filter(function (a) { return a[2] > a[1]; }).sort(function (p, q) { return p[1] - q[1]; });
      if (!A.length) return;
      IV.forEach(function (v) {
        if (cm[v[2]] != null) return;                       /* kode ini milik sebuah lapisan: bukan waste */
        var f = Math.max(0, v[0]), t = Math.min(v[1], h.maxD);
        if (!(t > f)) return;
        var segs = [];
        if (cl > 0) { var n = Math.max(1, Math.round((t - f) / cl)); for (var k = 0; k < n; k++) segs.push([f + (t - f) * k / n, f + (t - f) * (k + 1) / n]); }
        else segs.push([f, t]);
        segs.forEach(function (sg) {
          var len = 0, V = EI.map(function () { return [0, 0]; });
          A.forEach(function (a) {
            var ov = Math.min(sg[1], a[2]) - Math.max(sg[0], a[1]); if (ov <= 0) return;
            len += ov;
            EI.forEach(function (ei, q) { var val = ei >= 0 ? a[4][ei] : null; if (val != null && isFinite(val)) { V[q][0] += ov * val; V[q][1] += ov; } });
          });
          if (len < 0.5 * (sg[1] - sg[0]) - 1e-9) return;
          var p = getXYZ(id, (sg[0] + sg[1]) / 2), Z = zoneOf(R, p.x, p.y, p.z, tz);
          if (!Z) { nSkip++; return; }
          out[Z.zn].push({ id: id, x: Z.x, y: Z.y, z: Z.z, v: V.map(function (w) { return w[1] > 0 ? w[0] / w[1] : NaN; }) });
        });
      });
    });
    out.nSkip = nSkip;
    return out;
  }
  window.wlComps = comps;

  /* indeks sel 3D sederhana untuk cari tetangga terdekat di ruang unfold */
  function idx(pts, B) {
    var H = {};
    pts.forEach(function (p, i) { var k = Math.floor(p.x / B) + '_' + Math.floor(p.y / B) + '_' + Math.floor(p.z / B); (H[k] || (H[k] = [])).push(i); });
    return { B: B, H: H, pts: pts };
  }
  function near(I, mo, x, y, z, nmax) {
    var B = I.B, R = 3, cx = Math.floor(x / B), cy = Math.floor(y / B), cz = Math.floor(z / B), out = [];
    for (var a = cx - R; a <= cx + R; a++) for (var b = cy - R; b <= cy + R; b++) for (var c = cz - R; c <= cz + R; c++) {
      var L = I.H[a + '_' + b + '_' + c]; if (!L) continue;
      for (var q = 0; q < L.length; q++) {
        var p = I.pts[L[q]], d2 = meDn(mo, p.x - x, p.y - y, p.z - z, 1);
        if (d2 <= 1) out.push({ i: L[q], d: Math.sqrt(d2) });
      }
    }
    out.sort(function (u, v) { return u.d - v.d; });
    return out.slice(0, Math.max(1, nmax || 12));
  }

  /* ---------- siapkan ---------- */
  function prep() {
    var m = window.BX && BX.m, S = SL.S;
    if (!m) throw new Error('Belum ada block model aktif. Import block model, atau buat kerangka blok (AOI) di menu Block Model.');
    if (!S) throw new Error('Jalankan estimasi lapisan (bagian ③) dulu — estimasi waste menulis ke hasil itu.');
    if (S.key !== slBmKey(m)) throw new Error('Hasil estimasi lapisan tidak cocok dengan block model aktif; jalankan ulang estimasi lapisan.');
    var R = slEnsure();
    if (!R) throw new Error('Permukaan lapisan belum bisa dibangun: ' + (SL.err || ''));
    var o = wlPar(), tz = topoFn(), mo = ellip(o), els = S.els;
    var C = comps(R, els, tz), B = { bawah: [], atas: [], luar: [] }, nAir = 0, nIn = 0;
    for (var i = 0; i < m.n; i++) {
      if (S.lay[i] !== 65535) { nIn++; continue; }                 /* sudah punya lapisan */
      var Z = zoneOf(R, m.x[i] - offX, m.y[i] - offY, m.z[i], tz);
      if (!Z) { nAir++; continue; }
      if (Z.zn === 'luar' && !o.luar) continue;
      Z.i = i; Z.sx = m.sx[i]; Z.sy = m.sy[i]; Z.sz = m.sz[i];
      B[Z.zn].push(Z);
    }
    var I = {};
    ['bawah', 'atas', 'luar'].forEach(function (zn) { I[zn] = C[zn].length ? idx(C[zn], Math.max(5, (+o.r1 || 60) / 3)) : null; });
    return { m: m, S: S, R: R, o: o, mo: mo, els: els, C: C, B: B, I: I, nAir: nAir, nIn: nIn, tz: !!tz };
  }

  window.wlCheck = function () {
    try {
      var J = prep();
      WL.last = { chk: true, nb: { bawah: J.B.bawah.length, atas: J.B.atas.length, luar: J.B.luar.length },
                  nc: { bawah: J.C.bawah.length, atas: J.C.atas.length, luar: J.C.luar.length },
                  nSkip: J.C.nSkip, nAir: J.nAir, nIn: J.nIn, els: J.els, tz: J.tz };
      WL.msg = '';
    } catch (e) { WL.last = null; WL.msg = '<span class=warn>' + lE(e.message || e) + '</span>'; }
    if (typeof slPanel === 'function') slPanel();
  };

  /* ---------- jalankan ---------- */
  window.wlRun = function () {
    if (WL.job) { WL.job.cancel = true; return; }
    try {
      var J = prep(), items = [].concat(J.B.bawah, J.B.atas, J.B.luar);
      if (!items.length) throw new Error('Tidak ada blok di luar permukaan lapisan' + (J.o.luar ? '' : ' (zona "di luar cakupan grid" sedang dimatikan)') + '. Bila cakupan block model lebih sempit dari area of interest, lengkapi dulu dengan "Buat kerangka blok (AOI)".');
      var tot = J.C.bawah.length + J.C.atas.length + J.C.luar.length;
      if (!tot) throw new Error('Tidak ada komposit dari interval di luar kode lapisan. Semua kode geologi sudah dipetakan ke lapisan, jadi tidak ada sampel waste. Lepaskan kode yang memang bukan lapisan dari pemetaan (bagian ① Lapisan), atau nyalakan estimasi untuk lapisan itu sendiri (bagian ③).');
      WL.job = { J: J, items: items, i: 0, res: new Array(items.length), cancel: false, t0: performance.now(), nE: 0, nF: 0, byZn: {} };
      WL.msg = ''; if (typeof slPanel === 'function') slPanel();
      setTimeout(step, 10);
    } catch (e) { WL.msg = '<span class=warn>' + lE(e.message || e) + '</span>'; if (typeof slPanel === 'function') slPanel(); }
  };

  function step() {
    var W = WL.job; if (!W) return;
    var J = W.J, o = J.o, t = performance.now(), pw = Math.max(0.5, +o.p || 2), nmin = Math.max(1, +o.nmin || 2);
    while (W.i < W.items.length && performance.now() - t < 45) {
      var it = W.items[W.i], I = J.I[it.zn], res = null;
      if (I) {
        var N = near(I, J.mo, it.x, it.y, it.z, +o.nmax || 12);
        if (N.length >= nmin) {
          var vals = J.els.map(function () { return [0, 0]; });
          N.forEach(function (q) {
            var c = I.pts[q.i], w = 1 / Math.pow(Math.max(q.d, 1e-3), pw);
            J.els.forEach(function (e, k) { var v = c.v[k]; if (isFinite(v)) { vals[k][0] += w * v; vals[k][1] += w; } });
          });
          res = { ns: N.length, v: vals.map(function (a) { return a[1] > 1e-12 ? a[0] / a[1] : NaN; }) };
        }
      }
      if (res) { W.nE++; W.byZn[it.zn] = (W.byZn[it.zn] || 0) + 1; } else W.nF++;
      W.res[W.i] = res; W.i++;
      if (W.cancel) break;
    }
    var pc = W.items.length ? Math.round(100 * W.i / W.items.length) : 100, bar = document.getElementById('wlBar'), tx = document.getElementById('wlPct');
    if (bar) bar.style.width = pc + '%';
    if (tx) tx.textContent = pc + '% (' + fmt(W.i) + '/' + fmt(W.items.length) + ' blok)';
    if (W.cancel) { WL.job = null; WL.msg = 'Dibatalkan, tidak ada perubahan.'; if (typeof slPanel === 'function') slPanel(); return; }
    if (W.i >= W.items.length) { commit(W); return; }
    setTimeout(step, 0);
  }

  function commit(W) {
    var J = W.J, S = J.S, code = S.names.indexOf(WNAME);
    if (code < 0) { code = S.names.length; S.names.push(WNAME); }
    var lay = S.lay instanceof Uint16Array ? S.lay : Uint16Array.from(S.lay);
    /* bersihkan hasil waste run sebelumnya supaya tidak ada sisa di blok yang kini tidak terpilih */
    for (var i = 0; i < lay.length; i++) if (lay[i] === code) { lay[i] = 65535; S.ps[i] = 0; S.ns[i] = 0; J.els.forEach(function (e) { S.V[e][i] = -99; }); }
    var sum = {}, cnt = {};
    J.els.forEach(function (e) { sum[e] = 0; cnt[e] = 0; });
    W.items.forEach(function (it, q) {
      var r = W.res[q]; if (!r) return;
      lay[it.i] = code; S.ps[it.i] = IDWP; S.ns[it.i] = r.ns;
      J.els.forEach(function (e, k) {
        var v = r.v[k];
        if (isFinite(v)) { S.V[e][it.i] = Math.max(0, v); sum[e] += Math.max(0, v); cnt[e]++; }
      });
    });
    S.lay = lay;
    S.waste = { n: W.nE, fail: W.nF, byZn: W.byZn, when: new Date().toISOString().slice(0, 16).replace('T', ' '),
                mean: J.els.map(function (e) { return cnt[e] ? sum[e] / cnt[e] : null; }) };
    S.when = new Date().toISOString().slice(0, 16).replace('T', ' ') + ' w';   /* paksa slApply menyegarkan */
    var ms = Math.round(performance.now() - W.t0);
    WL.job = null;
    WL.last = { nb: W.items.length, nE: W.nE, fail: W.nF, byZn: W.byZn, els: J.els,
                mean: S.waste.mean, nc: { bawah: J.C.bawah.length, atas: J.C.atas.length, luar: J.C.luar.length }, ms: ms };
    WL.msg = '&#10003; Estimasi waste laterit selesai: <b>' + fmt(W.nE) + '</b> blok' + (W.nF ? ', ' + fmt(W.nF) + ' tanpa sampel cukup' : '') +
      ' &middot; ' + (ms / 1000).toFixed(1) + ' detik.';
    try { slApply(true); } catch (e) { console.error(e); }
    if (typeof slPanel === 'function') slPanel();
    try { updatePlot(); } catch (e) {}
    if (window.SA && SA.dirty) SA.dirty();
  }

  /* ---------- panel ---------- */
  function fld(k, lab, tip, st) {
    var o = wlPar();
    return '<div><label title="' + tip + '">' + lab + '</label><input type=number step="' + (st || 'any') + '" value="' + o[k] +
      '" onchange="wlPar()[\'' + k + '\']=+this.value;WL.last=null;slPanel()"></div>';
  }

  window.wlBox = function () {
    var o = wlPar(), S = SL.S, m = window.BX && BX.m;
    var h = '<div class=gmsec><h4>&#9316;b Estimasi waste (di luar permukaan lapisan)</h4>';
    h += '<div class=hint>Blok yang tidak jatuh di lapisan mana pun diisi <b>IDW di ruang unfold</b>, sehingga pencarian sampel mengikuti kelengkungan permukaan lapisan, bukan jarak lurus: ' +
      'zona <b>bawah</b> memakai kedalaman di bawah permukaan terbawah, zona <b>atas</b> memakai tinggi di atas kontak teratas. ' +
      'Sampelnya komposit dari interval yang <b>kodenya tidak dipetakan ke lapisan mana pun</b> (hard boundary waste). ' +
      'Hasil: <code>sl_pass = 9</code> dan kategori <code>sl_lapisan = ' + lE(WNAME) + '</code>. ' +
      'Blok di atas topografi adalah udara dan tidak pernah ikut.</div>';
    if (!m) return h + '<div class=hint>Belum ada block model aktif.</div></div>';
    if (!S) return h + '<div class=hint>Jalankan <b>estimasi lapisan</b> (bagian &#9314;) dulu — estimasi waste menulis ke hasil itu.</div></div>';
    h += '<div class=g2 style="margin-bottom:4px">' +
      fld('comp', 'Panjang komposit (m)', 'Komposit panjang tetap pada interval di luar kode lapisan. 0 = satu komposit per interval.', '0.5') +
      fld('p', 'Pangkat jarak IDW', 'Bobot = 1 / jarak^pangkat, jarak diukur di ruang unfold dengan elipsoid di bawah.', '0.5') +
      fld('nmin', 'Min titik', 'Blok dengan tetangga kurang dari ini dibiarkan tanpa kadar.', '1') +
      fld('nmax', 'Maks titik', 'Jumlah komposit terdekat yang dipakai satu blok.', '1') + '</div>';
    h += '<div class=lab>Elipsoid pencarian (ruang unfold)</div><div class=g3 style="margin-bottom:4px">' +
      fld('az', 'Azimut (&deg;)', 'Arah sumbu utama r1.', '5') +
      fld('r1', 'r1 (m)', 'Radius sumbu utama, searah azimut.', '5') +
      fld('r2', 'r2 (m)', 'Radius sumbu kedua, tegak lurus azimut.', '5') + '</div>' +
      '<div class=g2 style="margin-bottom:4px">' + fld('r3', 'r3 (m, arah unfold)', 'Radius pada sumbu unfold (kedalaman di bawah / tinggi di atas permukaan). Kecil, karena kadar berubah cepat tegak lurus lapisan.', '0.5') +
      '<div><label title="Blok di luar cakupan grid permukaan tidak punya kerangka unfold; bila dinyalakan, blok ini diestimasi memakai elevasi apa adanya (3D biasa)">Di luar cakupan grid</label>' +
      '<select onchange="wlPar().luar=+this.value;WL.last=null;slPanel()"><option value=0' + (o.luar ? '' : ' selected') + '>dilewati</option><option value=1' + (o.luar ? ' selected' : '') + '>ikut (3D biasa)</option></select></div></div>';
    if (WL.job) {
      h += '<div class=row><button class=btn-pri onclick="wlRun()">Batalkan</button><div class=prog><div id=wlBar style="height:100%;width:0;background:var(--ac);transition:width .2s"></div></div></div><div id=wlPct class=note></div>';
    } else {
      h += '<div class=g2 style="margin-top:4px"><button onclick="wlCheck()">Periksa dulu</button><button class=btn-pri onclick="wlRun()">&#9654; Jalankan estimasi waste</button></div>';
      var L = WL.last;
      if (L && L.chk) h += '<div class=hint style="margin-top:4px">blok: <b>' + fmt(L.nb.bawah) + '</b> di bawah lapisan &middot; <b>' + fmt(L.nb.atas) + '</b> di atas kontak teratas &middot; <b>' + fmt(L.nb.luar) + '</b> di luar cakupan grid' +
        '<br>komposit waste: ' + fmt(L.nc.bawah) + ' / ' + fmt(L.nc.atas) + ' / ' + fmt(L.nc.luar) + ' (bawah / atas / luar)' +
        '<br>dilewati: ' + fmt(L.nIn) + ' blok sudah punya lapisan &middot; ' + fmt(L.nAir) + ' di atas topografi (udara)' +
        (L.tz ? '' : '<br><span class=warn>Topografi belum ada</span> &rarr; zona "atas" tidak bisa dipisahkan dari udara, jadi dilewati seluruhnya.') + '</div>';
      else if (L) {
        var bz = Object.keys(L.byZn || {}).map(function (k) { return k + ' ' + fmt(L.byZn[k]); }).join(' &middot; ');
        h += '<div class=hint style="margin-top:4px">Run terakhir: <b>' + fmt(L.nE) + '</b> dari ' + fmt(L.nb) + ' blok terisi' + (L.fail ? ', ' + fmt(L.fail) + ' tanpa sampel cukup' : '') +
          (bz ? '<br>per zona: ' + bz : '') +
          '<br>rata-rata kadar waste: ' + L.els.map(function (e, k) { return lE(e) + ' ' + (L.mean[k] == null ? '-' : L.mean[k].toFixed(3)); }).join(' &middot; ') + '</div>';
      }
    }
    if (WL.msg) h += '<div class=hint style="margin-top:4px">' + WL.msg + '</div>';
    h += '<div class=clsnote>&#9888; Estimasi lapisan yang dijalankan ulang membentuk hasil baru, sehingga estimasi waste ini ikut terhapus &mdash; jalankan ulang sesudahnya.</div>';
    return h + '</div>';
  };

  /* sisipkan di akhir panel Stratified-Laterite */
  if (typeof slPanel === 'function') {
    var _sp = slPanel;
    slPanel = function () {
      var r = _sp.apply(this, arguments);
      try {
        var b = document.getElementById('slBody');
        if (b) {
          var old = document.getElementById('wlSec');
          if (old) old.parentNode.removeChild(old);
          var w = document.createElement('div'); w.id = 'wlSec'; w.innerHTML = wlBox();
          b.appendChild(w);
        }
      } catch (e) { console.error(e); }
      return r;
    };
    window.slPanel = slPanel;
  }
})();
