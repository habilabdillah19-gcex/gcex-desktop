/* GC-Ex — TOPOGRAFI & ORTHOFOTO RESOLUSI SANGAT TINGGI TANPA KORBAN PERFORMA (0.24 / 0.14)
   =======================================================================================
   Dipakai GC-Ex Drill Hole Ultimate dan GC-Ex Block Model.

   Masalah sebelumnya
   ------------------
   - Orthofoto digambar sebagai mesh3d berwarna per-titik dengan resolusi TETAP dari kotak "Resolusi (m)"
     dan dibatasi 300.000 titik. Zoom masuk tidak menambah detail (titiknya tetap jarang), zoom keluar
     membuang waktu menghitung titik yang tidak terlihat. Warna diambil titik (point sample) sehingga
     berkerlip / aliasing saat dikecilkan.
   - Peta (Mapping) memakai satu gambar JPEG seluruh ortho yang dipaksa maksimum 3000 px sisi panjang:
     ortho 20.000 px pun hanya tampil 3000 px, sehingga zoom masuk tampak buram.
   - Topografi digambar dari desimasi "ambil tiap titik ke-n" ke 15.000 titik sekali saja saat proyek
     dibuka: zoom masuk tetap kasar, dan titik yang terbuang tidak pernah kembali.
   - topoZ(x,y) menghitung IDW ulang (mencari tetangga di indeks sel 10 m) SETIAP kali dipanggil —
     dipanggil 300.000 kali saat menggambar ortho drape dan sekali per blok saat reporting.

   Yang dilakukan modul ini
   ------------------------
   1. PIRAMIDA ORTHO (LOD). Level 0 = piksel asli; tiap level berikutnya rata-rata 2x2 (seperempat
      ukuran). Total tambahan memori = 1/3 level 0. Pengambilan warna memakai level yang texel-nya
      sepadan dengan resolusi mesh, jadi warnanya rata-rata area (anti-alias, tidak berkerlip) dan
      pembacaannya 4^L kali lebih sedikit.
   2. RESOLUSI MENGIKUTI TAMPILAN. Mesh ortho & desimasi topografi memakai luas area yang sedang
      terlihat: zoom masuk otomatis makin detail pada jumlah titik yang sama; zoom keluar tidak
      menghitung yang di luar layar.
   3. GAMBAR ASLI DI PETA 2D. Di menu Peta (Mapping) ortho dipotong sesuai tampilan dan dikirim sebagai
      gambar sampai 4096 px — di zoom dekat ini berarti resolusi asli penuh, tanpa mesh sama sekali.
   4. DESIMASI TOPOGRAFI PER SEL. Satu titik per sel grid (bukan "tiap ke-n"), dihitung dari seluruh
      data di dalam tampilan: sebaran tetap merata dan detail penuh muncul saat zoom masuk.
   5. RASTER topoZ. Grid elevasi dibangun sekali lalu dibaca bilinear O(1).

   Semua tetap jalan apa adanya bila modul gagal / data belum ada (fungsi lama dipakai sebagai cadangan). */
var HR = window.HR = {
  on: true,
  ext: null,          /* {x0,x1,y0,y1} koordinat LOKAL yang sedang terlihat (null = belum tahu) */
  extW: null,         /* idem dalam koordinat DUNIA (Easting/Northing), untuk peta 2D */
  budget: 300000,     /* anggaran titik mesh ortho */
  tbudget: 15000,     /* anggaran titik mesh topografi */
  mapPx: 4096,        /* batas KERAS sisi gambar ortho di Peta 2D */
  ver: 0              /* naik setiap tampilan berubah -> cache ikut berganti */
};

/* ============================ 1. piramida ortho ============================ */
HR.pyr = function () {
  var O = window.ORT;
  if (!O || !O.m || !O.px) return null;
  if (O._pyr && O._pyr.m === O.m) return O._pyr;
  var m = O.m, L = [{ px: O.px, w: m.w, h: m.h, dx: m.dx, dy: m.dy }];
  var w = m.w, h = m.h, src = O.px;
  while (w > 256 && h > 256 && L.length < 12) {
    var w2 = w >> 1, h2 = h >> 1, out = new Uint8Array(w2 * h2 * 3);
    for (var r = 0; r < h2; r++) {
      var r0 = (r << 1) * w, r1 = ((r << 1) + 1) * w;
      for (var c = 0; c < w2; c++) {
        var a = (r0 + (c << 1)) * 3, b = (r0 + (c << 1) + 1) * 3, d = (r1 + (c << 1)) * 3, e = (r1 + (c << 1) + 1) * 3, o = (r * w2 + c) * 3;
        out[o] = (src[a] + src[b] + src[d] + src[e] + 2) >> 2;
        out[o + 1] = (src[a + 1] + src[b + 1] + src[d + 1] + src[e + 1] + 2) >> 2;
        out[o + 2] = (src[a + 2] + src[b + 2] + src[d + 2] + src[e + 2] + 2) >> 2;
      }
    }
    var k = L.length;
    L.push({ px: out, w: w2, h: h2, dx: m.dx * (1 << k), dy: m.dy * (1 << k) });
    src = out; w = w2; h = h2;
  }
  O._pyr = { m: m, L: L };
  return O._pyr;
};

/* level yang texel-nya sepadan dengan res (meter per titik mesh). Hasilnya di-cache karena
   pemanggilnya menyampling ratusan ribu titik dengan res yang sama. */
HR.level = function (res) {
  var P = HR.pyr(); if (!P) return null;
  var c = HR._lv;
  if (c && c.P === P && c.res === res) return c.lv;
  var d0 = P.L[0].dx || 1, k = Math.floor(Math.log(Math.max(1, res / d0)) / Math.LN2);
  var lv = P.L[Math.max(0, Math.min(P.L.length - 1, k))];
  HR._lv = { P: P, res: res, lv: lv };
  return lv;
};

/* warna rata-rata area pada resolusi res; xl,yl = koordinat LOKAL.
   Nilainya diambil dari level piramida yang texel-nya sepadan res, jadi warnanya rata-rata
   area (anti-alias) — bukan titik tunggal yang berkerlip saat gambar dikecilkan. */
HR.rgb = function (xl, yl, res) {
  var O = window.ORT; if (!O || !O.m) return null;
  var lv = HR._lv && HR._lv.res === res && HR._lv.P === O._pyr ? HR._lv.lv : HR.level(res);
  if (!lv) return null;
  var m = O.m, c = ((xl + offX - m.e0) / lv.dx + 0.5) | 0, r = ((m.n0 - (yl + offY)) / lv.dy + 0.5) | 0;
  if (c < 0 || r < 0 || c >= lv.w || r >= lv.h) return null;
  var p = (r * lv.w + c) * 3, px = lv.px;
  return [px[p], px[p + 1], px[p + 2]];
};

/* resolusi mesh ortho dari luas tampilan + anggaran titik */
HR.resFor = function (x0, x1, y0, y1, budget) {
  var w = Math.max(1, x1 - x0), h = Math.max(1, y1 - y0), n = Math.max(1000, budget || HR.budget);
  var r = Math.sqrt(w * h / n);
  var O = window.ORT, mn = (O && O.m && O.m.dx) ? O.m.dx : 0.05;   /* tidak lebih halus dari piksel asli */
  return Math.max(mn, r);
};

/* ============================ 2. tampilan yang sedang terlihat ============================ */
HR.setExt = function (x0, x1, y0, y1, world) {
  if (!isFinite(x0) || !isFinite(x1) || !isFinite(y0) || !isFinite(y1) || x1 <= x0 || y1 <= y0) return;
  var ox = world ? (window.offX || 0) : 0, oy = world ? (window.offY || 0) : 0;
  var e = { x0: x0 - ox, x1: x1 - ox, y0: y0 - oy, y1: y1 - oy };
  var o = HR.ext;
  if (o && Math.abs(o.x0 - e.x0) < 1e-6 && Math.abs(o.x1 - e.x1) < 1e-6 && Math.abs(o.y0 - e.y0) < 1e-6 && Math.abs(o.y1 - e.y1) < 1e-6) return;
  HR.ext = e;
  HR.extW = { x0: e.x0 + (window.offX || 0), x1: e.x1 + (window.offX || 0), y0: e.y0 + (window.offY || 0), y1: e.y1 + (window.offY || 0) };
  HR.ver++;
};

/* tampilan efektif: perpotongan extent terlihat dengan kotak data (bila belum tahu, pakai kotak data) */
HR.box = function (b) {
  var e = HR.on && HR.ext ? HR.ext : null;
  if (!e) return b;
  var mg = 0.08 * Math.max(e.x1 - e.x0, e.y1 - e.y0);  /* sedikit margin supaya geser kecil tidak kosong */
  var q = { x0: Math.max(b.x0, e.x0 - mg), x1: Math.min(b.x1, e.x1 + mg), y0: Math.max(b.y0, e.y0 - mg), y1: Math.min(b.y1, e.y1 + mg) };
  if (q.x1 <= q.x0 || q.y1 <= q.y0) return b;          /* tidak bertumpang -> jangan kosongkan tampilan */
  return q;
};

/* penanda sumber supaya cache tidak tertukar antar kumpulan titik (mis. topoC vs topoF) */
HR._hid = 0;
HR.hid = function (o) { if (!o._hid) { o._hid = 'h' + (++HR._hid); } return o._hid + ':' + o.x.length; };

/* ============================ 3. desimasi topografi per sel ============================ */
/* src: {x,y,z} koordinat lokal (boleh berisi null sebagai pemutus garis). Hasil: titik untuk mesh. */
HR.topoMesh = function (src, budget) {
  if (!src || !src.x || !src.x.length) return src;
  budget = Math.max(1000, budget || HR.tbudget);
  var key = 'tm|' + budget + '|' + HR.ver + '|' + HR.hid(src);
  if (HR._tm && HR._tm.key === key) return HR._tm.o;
  var b = src.b || { x0: -1e9, x1: 1e9, y0: -1e9, y1: 1e9 }, e = HR.box(b);
  var w = Math.max(1, e.x1 - e.x0), h = Math.max(1, e.y1 - e.y0);
  var cell = Math.sqrt(w * h / budget), nx = Math.max(1, Math.ceil(w / cell)), ny = Math.max(1, Math.ceil(h / cell));
  var seen = new Uint8Array(nx * ny), X = [], Y = [], Z = [], i, n = src.x.length, kept = 0;
  for (i = 0; i < n; i++) {
    var x = src.x[i]; if (x === null) continue;
    var y = src.y[i];
    if (x < e.x0 || x > e.x1 || y < e.y0 || y > e.y1) continue;
    var cx = Math.min(nx - 1, Math.floor((x - e.x0) / cell)), cy = Math.min(ny - 1, Math.floor((y - e.y0) / cell)), k = cy * nx + cx;
    if (seen[k]) continue;
    seen[k] = 1; X.push(x); Y.push(y); Z.push(src.z[i]); kept++;
  }
  if (kept < 3) return src;
  var o = { x: X, y: Y, z: Z, b: src.b, hr: { cell: cell, n: kept, dari: n } };
  HR._tm = { key: key, o: o };
  return o;
};

/* garis kontur: hanya segmen di dalam tampilan (null tetap jadi pemutus) */
HR.topoLines = function (src) {
  if (!src || !src.x || !src.x.length || !HR.on || !HR.ext) return src;
  var key = 'tl|' + HR.ver + '|' + HR.hid(src);
  if (HR._tl && HR._tl.key === key) return HR._tl.o;
  var e = HR.box(src.b || { x0: -1e9, x1: 1e9, y0: -1e9, y1: 1e9 });
  var X = [], Y = [], Z = [], last = true, n = src.x.length, keep = 0;
  for (var i = 0; i < n; i++) {
    var x = src.x[i];
    var ok = x !== null && x >= e.x0 && x <= e.x1 && src.y[i] >= e.y0 && src.y[i] <= e.y1;
    if (ok) { X.push(x); Y.push(src.y[i]); Z.push(src.z[i]); last = false; keep++; }
    else if (!last) { X.push(null); Y.push(null); Z.push(null); last = true; }
  }
  if (keep < 2) return src;
  var o = { x: X, y: Y, z: Z, b: src.b };
  HR._tl = { key: key, o: o };
  return o;
};

/* ============================ 4. raster topografi UNTUK TAMPILAN SAJA ============================
   PENTING: raster ini TIDAK dipakai reporting / estimasi. Nilainya diambil dengan memanggil topoZ()
   yang asli pada titik-titik grid, lalu dibaca bilinear. Jadi medannya sama dengan IDW asli, hanya
   didekati antar simpul grid (jarak simpul <= beberapa meter) dan dipakai hanya untuk menempelkan
   warna ortho ke topografi (drape) di tampilan 3D. Semua perhitungan tonase tetap memakai topoZ()
   asli, supaya hasil laporan tidak berubah sedikit pun oleh modul ini. */
HR.zGrid = function () {
  var o = window.OV && OV.topoF;
  if (!o || !o.x || !o.x.length || typeof window.topoZ !== 'function') return null;
  if (HR._ras && HR._ras.src === o && HR._ras.ver === (OV._ver || 0)) return HR._ras;
  var b = o.b, w = Math.max(1, b.x1 - b.x0), h = Math.max(1, b.y1 - b.y0);
  var N = 384, nx = N, ny = N;                       /* 384 x 384 = 147.456 panggilan topoZ, sekali saja */
  if (w > h) ny = Math.max(16, Math.round(N * h / w)); else nx = Math.max(16, Math.round(N * w / h));
  var dx = w / (nx - 1), dy = h / (ny - 1), Z = new Float32Array(nx * ny), have = new Uint8Array(nx * ny);
  for (var j = 0; j < ny; j++) for (var i = 0; i < nx; i++) {
    var q = window.topoZ(b.x0 + i * dx, b.y0 + j * dy), k = j * nx + i;
    if (q !== null && isFinite(q)) { Z[k] = q; have[k] = 1; }
  }
  HR._ras = { src: o, ver: (OV._ver || 0), b: b, nx: nx, ny: ny, dx: dx, dy: dy, z: Z, have: have };
  return HR._ras;
};

/* elevasi cepat untuk TAMPILAN; null bila di luar jangkauan data (pemanggil boleh jatuh ke topoZ asli) */
HR.zFast = function (x, y) {
  var R = HR.zGrid(); if (!R) return null;
  var fx = (x - R.b.x0) / R.dx, fy = (y - R.b.y0) / R.dy;
  if (!(fx >= 0 && fy >= 0 && fx <= R.nx - 1 && fy <= R.ny - 1)) return null;
  var i0 = Math.min(R.nx - 2, Math.floor(fx)), j0 = Math.min(R.ny - 2, Math.floor(fy)), tx = fx - i0, ty = fy - j0;
  var k = j0 * R.nx + i0, k2 = k + R.nx;
  if (!(R.have[k] && R.have[k + 1] && R.have[k2] && R.have[k2 + 1])) return null;
  return (R.z[k] * (1 - tx) + R.z[k + 1] * tx) * (1 - ty) + (R.z[k2] * (1 - tx) + R.z[k2 + 1] * tx) * ty;
};

/* ============================ 5. gambar ortho resolusi penuh untuk Peta 2D ============================ */
/* Potong ortho sesuai tampilan, sampai HR.mapPx px pada sisi panjang: di zoom dekat = resolusi asli. */
HR.screenPx = function () {
  var el = null;
  try { el = (window.mapGd && mapGd()) || document.querySelector('.js-plotly-plot'); } catch (e) { }
  var w = el && el.clientWidth ? el.clientWidth : 1200, h = el && el.clientHeight ? el.clientHeight : 800;
  var dpr = Math.min(2, window.devicePixelRatio || 1);
  return Math.max(768, Math.min(HR.mapPx, Math.round(Math.max(w, h) * dpr * 1.5)));
};

HR.mapImage = function () {
  var O = window.ORT, m = O && O.m;
  if (!m || !O.px) return null;
  var P = HR.pyr(); if (!P) return null;
  var ex = HR.extW, e0 = m.e0, n0 = m.n0, W = m.w * m.dx, H = m.h * m.dy;
  var x0 = e0, x1 = e0 + W, y1 = n0, y0 = n0 - H;
  if (HR.on && ex) {
    var mg = 0.05 * Math.max(ex.x1 - ex.x0, ex.y1 - ex.y0);
    x0 = Math.max(x0, ex.x0 - mg); x1 = Math.min(x1, ex.x1 + mg);
    y0 = Math.max(y0, ex.y0 - mg); y1 = Math.min(y1, ex.y1 + mg);
    if (x1 - x0 < m.dx * 2 || y1 - y0 < m.dy * 2) { x0 = e0; x1 = e0 + W; y0 = n0 - H; y1 = n0; }
  }
  /* cukup setajam layar: membuat JPEG 4096 px untuk tampilan selebar 1200 px hanya membuang waktu */
  var scr = HR.screenPx();
  var res = Math.max(m.dx, (x1 - x0) / scr, (y1 - y0) / scr);
  var key = [Math.round(x0 * 100), Math.round(x1 * 100), Math.round(y0 * 100), Math.round(y1 * 100), Math.round(res * 1000)].join('|');
  if (O._mi && O._mi.key === key) return O._mi.o;
  var lv = HR.level(res);
  var w = Math.max(1, Math.min(scr, Math.round((x1 - x0) / res))), h = Math.max(1, Math.min(scr, Math.round((y1 - y0) / res)));
  var cv = document.createElement('canvas'); cv.width = w; cv.height = h;
  var cx = cv.getContext('2d'), im = cx.createImageData(w, h), D = im.data;
  for (var r = 0; r < h; r++) {
    var wy = y1 - (r + 0.5) * (y1 - y0) / h, sr = Math.round((n0 - wy) / lv.dy);
    if (sr < 0) sr = 0; if (sr >= lv.h) sr = lv.h - 1;
    for (var c = 0; c < w; c++) {
      var wx = x0 + (c + 0.5) * (x1 - x0) / w, sc = Math.round((wx - e0) / lv.dx);
      if (sc < 0) sc = 0; if (sc >= lv.w) sc = lv.w - 1;
      var s = (sr * lv.w + sc) * 3, o2 = (r * w + c) * 4;
      D[o2] = lv.px[s]; D[o2 + 1] = lv.px[s + 1]; D[o2 + 2] = lv.px[s + 2]; D[o2 + 3] = 255;
    }
  }
  cx.putImageData(im, 0, 0);
  var o = { m: m, src: cv.toDataURL('image/jpeg', 0.9), x: x0, y: y1, sx: x1 - x0, sy: y1 - y0, px: w + 'x' + h, res: res };
  O._mi = { key: key, o: o };
  return o;
};

/* ============================ 6. pantau tampilan (zoom / geser) ============================ */
(function () {
  var tmr = null, redraw = function () {
    tmr = null;
    try {
      if (window.MAP && MAP.on && window.mapRefresh) mapRefresh(true);
      else if (window.updatePlot) { if (window.OVC) window.OVC = {}; updatePlot(); }
    } catch (e) { }
  };
  var bump = function () { if (tmr) clearTimeout(tmr); tmr = setTimeout(redraw, 260); };
  HR.fromRelayout = function (ev, world) {
    if (!ev || !HR.on) return;
    var v = HR.ver;
    var sx = ev['scene.xaxis.range'], sy = ev['scene.yaxis.range'];
    if (sx && sy) HR.setExt(sx[0], sx[1], sy[0], sy[1], false);
    var ax = ev['xaxis.range'] || (ev['xaxis.range[0]'] !== undefined ? [ev['xaxis.range[0]'], ev['xaxis.range[1]']] : null);
    var ay = ev['yaxis.range'] || (ev['yaxis.range[0]'] !== undefined ? [ev['yaxis.range[0]'], ev['yaxis.range[1]']] : null);
    if (ax && ay) HR.setExt(+ax[0], +ax[1], +ay[0], +ay[1], !!world);
    /* reset tampilan (klik ganda / autoscale): lupakan extent supaya mesh kembali menutupi seluruh area */
    if (!sx && !ax && (ev['xaxis.autorange'] || ev['yaxis.autorange'] || ev['scene.xaxis.autorange'] ||
      ev['scene.aspectmode'] === 'auto' || ev.autosize)) { if (HR.ext) { HR.ext = null; HR.extW = null; HR.ver++; } }
    if (HR.ver !== v) bump();
  };
  HR.attach = function (gd, world) {
    if (!gd || gd._hrOn || !gd.on) return;
    gd._hrOn = 1;
    try { gd.on('plotly_relayout', function (ev) { HR.fromRelayout(ev, world); }); } catch (e) { }
  };
  /* pasang ke grafik utama & peta begitu ada */
  var t = setInterval(function () {
    try {
      var a = document.getElementById('plot') || document.getElementById('graph') || document.querySelector('.js-plotly-plot');
      if (a) HR.attach(a, false);
      var b = window.mapGd && mapGd(); if (b) HR.attach(b, true);
    } catch (e) { }
  }, 1200);
  setTimeout(function () { clearInterval(t); }, 120000);
})();

HR.info = function () {
  var P = HR.pyr(), R = HR.zGrid && HR._ras, o = [];
  if (P) o.push('ortho piramida ' + P.L.length + ' level (' + P.L[0].w + 'x' + P.L[0].h + ' px @ ' + P.L[0].dx + ' m)');
  if (R) o.push('grid topo tampilan ' + R.nx + 'x' + R.ny + ' sel @ ' + (Math.round(R.dx * 100) / 100) + ' m');
  if (HR.ext) o.push('tampilan ' + Math.round(HR.ext.x1 - HR.ext.x0) + ' x ' + Math.round(HR.ext.y1 - HR.ext.y0) + ' m');
  return o.join(' · ');
};
