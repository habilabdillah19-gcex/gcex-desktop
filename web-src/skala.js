/* ================= GC-Ex (Block Model 0.24.91 / Drillhole 0.24.100): SKALA DI SETIAP JENDELA 2D & 3D =================
   Pemilik 16 Nov 2026: "Setiap jendela 2D dan 3D serta layout map harus menyertakan skala. Skala ini yang kita miss."
   Modul bersama (BM: EXTRA di build.py; DH: daftar viewer di build_dh.py). Membungkus Plotly.newPlot / Plotly.react sekali,
   lalu memasang kotak skala (skala batang + rasio 1:N layar) di setiap plot SPASIAL:
     - peta / penampang 2D = sumbu y diikat ke x (yaxis.scaleanchor 'x'; satuan meter). Penampang ber-eksagerasi
       vertikal (scaleratio != 1): skala batang mengikuti sumbu horizontal + keterangan "VE n×";
     - tampilan 3D (gl3d scene): skala di titik pusat pandangan, dihitung dari matriks kamera Plotly (perspektif:
       benda yang lebih dekat tampak lebih besar, jadi skala 3D adalah perkiraan di pusat; proyeksi ortografik = tepat).
   Grafik non-spasial (histogram, variogram, swath, dsb.) tidak disentuh. Plot yang sudah menggambar skala sendiri
   (peta level Ore Geometry Studio, Layout & Plot PDF) memberi tanda gd.dataset.skala='off'.
   Rasio 1:N memakai 96 dpi layar (1 px = 0,2646 mm) — sama dengan cara aplikasi CAD menampilkan skala layar. */
(function () {
  if (window.SKL) return;
  var SKL = window.SKL = { on: true };
  try { if (localStorage.getItem('gcex_skala') === '0') SKL.on = false; } catch (e) { }
  var MMPX = 25.4 / 96;
  var NICE = [0.1, 0.2, 0.5, 1, 2, 2.5, 5, 10, 20, 25, 50, 100, 200, 250, 500, 1000, 2000, 2500, 5000, 10000, 20000, 50000];
  var nice = function (v) { var b = NICE[0]; for (var i = 0; i < NICE.length; i++) if (NICE[i] <= v) b = NICE[i]; return b; };
  var fmt = function (n) { return Number(n).toLocaleString('id-ID', { maximumFractionDigits: n < 1 ? 2 : 0 }); };
  var rasio = function (mpp) { var r = mpp * 1000 / MMPX, p = Math.pow(10, Math.floor(Math.log10(r)) - 1), q = Math.round(r / p) * p; return Math.max(1, Math.round(q)); };
  var css = document.createElement('style');
  css.textContent = '.gxSkala{position:absolute;left:10px;bottom:10px;z-index:6;pointer-events:none;font:11px/1.25 Segoe UI,Arial,sans-serif;color:#1d2433;background:transparent;border:0;border-radius:4px;padding:3px 7px 4px;box-shadow:none;text-shadow:0 0 2px #fff,0 0 3px #fff,0 0 4px #fff}' + /* BM 0.24.104 / DH 0.24.107: latar transparan (pemilik 17 Nov 2026), teks diberi halo agar tetap terbaca */
    '.gxSkala .bar{box-shadow:0 0 0 1px rgba(255,255,255,.85)}.gxSkala .gxX{pointer-events:auto}' +
    '.gxSkala .bar{display:flex;height:6px;margin:3px 0 1px;border:1px solid #1d2433}.gxSkala .bar i{flex:1;background:#1d2433}.gxSkala .bar i:nth-child(2n){background:#fff}' +
    '.gxSkala .lb{display:flex;justify-content:space-between;font-size:10px}.gxSkala .rt{font-weight:600}.gxSkala .nt{font-size:9.5px;color:#556}' +
    'body.dark .gxSkala,.dark .gxSkala{background:transparent;color:#e6e9ef;text-shadow:0 0 2px #000,0 0 3px #000,0 0 4px #000}body.dark .gxSkala .bar,.dark .gxSkala .bar{box-shadow:0 0 0 1px rgba(0,0,0,.7)}body.dark .gxSkala .bar,.dark .gxSkala .bar{border-color:#e6e9ef}body.dark .gxSkala .bar i,.dark .gxSkala .bar i{background:#e6e9ef}body.dark .gxSkala .bar i:nth-child(2n),.dark .gxSkala .bar i:nth-child(2n){background:#1a202c}body.dark .gxSkala .nt{color:#aab}';
  document.head.appendChild(css);

  /* ---- 2D: meter per piksel sumbu x ---- */
  function info2d(gd) {
    var fl = gd._fullLayout; if (!fl || !fl.xaxis || !fl.yaxis) return null; var ya = gd.layout && gd.layout.yaxis;
    if (!ya || ya.scaleanchor !== 'x') return null;
    var xa = fl.xaxis, L = xa._length, r = xa.range; if (!(L > 20) || !r) return null; var mpp = Math.abs(r[1] - r[0]) / L; if (!(mpp > 0) || !isFinite(mpp)) return null;
    var ve = +(ya.scaleratio || 1); return { mpp: mpp, ve: ve, w: L, off: { l: xa._offset, b: fl.height - (fl.yaxis._offset + fl.yaxis._length) } };
  }
  /* ---- 3D: proyeksi titik data -> piksel lewat matriks kamera Plotly ---- */
  var mul = function (m, v) { return [m[0] * v[0] + m[4] * v[1] + m[8] * v[2] + m[12] * v[3], m[1] * v[0] + m[5] * v[1] + m[9] * v[2] + m[13] * v[3], m[2] * v[0] + m[6] * v[1] + m[10] * v[2] + m[14] * v[3], m[3] * v[0] + m[7] * v[1] + m[11] * v[2] + m[15] * v[3]]; };
  function info3d(gd) {
    var fl = gd._fullLayout; if (!fl || !fl.scene || !fl.scene._scene) return null; var sc = fl.scene._scene, gp = sc.glplot; if (!gp || !gp.cameraParams) return null;
    var cp = gp.cameraParams, ds = sc.dataScale || [1, 1, 1], dom = fl.scene.domain, W = fl.width * (dom.x[1] - dom.x[0]), H = fl.height * (dom.y[1] - dom.y[0]); if (!(W > 20)) return null;
    var pr = function (p) { var v = [p[0] * ds[0], p[1] * ds[1], p[2] * ds[2], 1]; v = mul(cp.model, v); v = mul(cp.view, v); v = mul(cp.projection, v); return [(v[0] / v[3] + 1) / 2 * W, (1 - v[1] / v[3]) / 2 * H, v[3]]; };
    /* pusat pandangan = titik pusat kamera (layout.scene.camera.center) di ruang data */
    var cam = (fl.scene.camera || {}), c = cam.center || { x: 0, y: 0, z: 0 }, ax = ['xaxis', 'yaxis', 'zaxis'].map(function (a) { return fl.scene[a]; });
    var mid = ax.map(function (a, i) { var r = a.range || [0, 1], m0 = (r[0] + r[1]) / 2; return m0; });
    /* Plotly: pusat kamera dalam koordinat ternormalisasi aspek; dekati dengan titik tengah rentang + geseran center */
    var asp = fl.scene.aspectratio || { x: 1, y: 1, z: 1 }, span = ax.map(function (a) { var r = a.range || [0, 1]; return r[1] - r[0]; });
    var P0 = [mid[0] + c.x / (asp.x || 1) * span[0] / 2, mid[1] + c.y / (asp.y || 1) * span[1] / 2, mid[2] + c.z / (asp.z || 1) * span[2] / 2];
    /* arah "kanan layar" di ruang data horizontal: beda kecil sepanjang x dan y, cari kombinasi yang paling horizontal di layar */
    var a0 = pr(P0); if (!isFinite(a0[0]) || a0[2] <= 0) return null;
    var e = Math.max(span[0], span[1]) * 0.01 || 1, px = pr([P0[0] + e, P0[1], P0[2]]), py = pr([P0[0], P0[1] + e, P0[2]]);
    var gx = [(px[0] - a0[0]) / e, (px[1] - a0[1]) / e], gy = [(py[0] - a0[0]) / e, (py[1] - a0[1]) / e];
    /* vektor horizontal data (u,v) yang memetakan ke piksel layar (1,0): selesaikan [gx gy]·[u v] = [1 0] */
    var det = gx[0] * gy[1] - gy[0] * gx[1], ppm;
    if (Math.abs(det) > 1e-12) { var u = gy[1] / det, v = -gx[1] / det; ppm = 1 / Math.hypot(u, v); }
    else ppm = Math.max(Math.hypot(gx[0], gx[1]), Math.hypot(gy[0], gy[1]));
    if (!(ppm > 0) || !isFinite(ppm)) return null;
    var orto = cam.projection && cam.projection.type === 'orthographic';
    return { mpp: 1 / ppm, ve: 1, w: W, d3: true, orto: orto, off: { l: fl.width * dom.x[0], b: fl.height * dom.y[0] } };
  }
  function box(gd) { var b = gd.querySelector(':scope > .gxSkala'); if (!b) { b = document.createElement('div'); b.className = 'gxSkala'; if (getComputedStyle(gd).position === 'static') gd.style.position = 'relative'; gd.appendChild(b); } return b; }
  function upd(gd) {
    if (!gd || !gd._fullLayout) return; var b = gd.querySelector(':scope > .gxSkala');
    if (!SKL.on || gd.dataset.skala === 'off') { if (b) b.style.display = 'none'; try { if (window.UKUR) UKUR.pasang(gd, null); } catch (e) { } return; }
    var I = null; try { I = gd._fullLayout.scene && gd._fullLayout.scene._scene ? info3d(gd) : info2d(gd); } catch (e) { I = null; }
    if (!I) { if (b) b.style.display = 'none'; try { if (window.UKUR) UKUR.pasang(gd, null); } catch (e) { } return; }
    b = box(gd); b.style.display = '';
    var tgt = Math.max(40, Math.min(160, I.w * 0.18)), m = nice(tgt * I.mpp), px = m / I.mpp, R = rasio(I.mpp);
    var h = '<div class=rt title="Rasio layar (96 dpi)">Skala ' + (I.d3 && !I.orto ? '≈ ' : '') + '1 : ' + fmt(R) + '</div><div class=bar style="width:' + Math.round(px) + 'px"><i></i><i></i><i></i><i></i></div><div class=lb style="width:' + Math.round(px) + 'px"><span>0</span><span>' + fmt(m) + ' m</span></div>';
    if (I.d3 && !I.orto) h += '<div class=nt>di pusat pandangan (perspektif)</div>';
    if (Math.abs(I.ve - 1) > 1e-6) h += '<div class=nt>horizontal · VE ' + fmt(+I.ve.toFixed(2)) + '×</div>';
    if (b._h !== h) { b.innerHTML = h; b._h = h; }
    var ml = (I.off && I.off.l) || 0, mb = (I.off && I.off.b) || 0; b.style.left = Math.round(ml + 10) + 'px'; b.style.bottom = Math.round(mb + 10) + 'px';
    /* BM 0.24.100 / DH 0.24.103 (pemilik 17 Nov 2026: "Skala menghalangi pandangan Ringkasan di kiri bawah"): bila kotak skala
       menimpa kartu yang melayang di atas plot (kartu Ringkasan #statsCard, dsb.), geser ke kanan kartu itu. */
    try { var gr = gd.getBoundingClientRect(), br = b.getBoundingClientRect();
      ['statsCard'].forEach(function (id) { var c = document.getElementById(id); if (!c || !c.offsetParent || gd.contains(c)) return; var cr = c.getBoundingClientRect();
        if (cr.width && cr.left < br.right && cr.right > br.left && cr.top < br.bottom && cr.bottom > br.top) { b.style.left = Math.round(cr.right - gr.left + 10) + 'px'; br = b.getBoundingClientRect(); } });
    } catch (e) { }
    try { if (window.UKUR) UKUR.pasang(gd, I, b); } catch (e) { }
  }
  SKL.upd = upd;
  /* proyeksi 3D titik data -> piksel relatif terhadap gd (dipakai alat Ukur jarak, ukur.js) */
  SKL.proj3d = function (gd) {
    var fl = gd._fullLayout; if (!fl || !fl.scene || !fl.scene._scene) return null; var sc = fl.scene._scene, gp = sc.glplot; if (!gp || !gp.cameraParams) return null;
    var cp = gp.cameraParams, ds = sc.dataScale || [1, 1, 1], dom = fl.scene.domain, W = fl.width * (dom.x[1] - dom.x[0]), H = fl.height * (dom.y[1] - dom.y[0]), L0 = fl.width * dom.x[0], T0 = fl.height * (1 - dom.y[1]);
    var M = cp.model, V = cp.view, Pm = cp.projection;
    return function (x, y, z) { var v = [x * ds[0], y * ds[1], z * ds[2], 1]; v = mul(M, v); v = mul(V, v); v = mul(Pm, v); return [L0 + (v[0] / v[3] + 1) / 2 * W, T0 + (1 - v[1] / v[3]) / 2 * H, v[3]]; };
  };
  SKL.info = function (gd) { gd = typeof gd === 'string' ? document.getElementById(gd) : gd; try { return gd._fullLayout.scene && gd._fullLayout.scene._scene ? info3d(gd) : info2d(gd); } catch (e) { return null; } };
  SKL.set = function (on) { SKL.on = !!on; try { localStorage.setItem('gcex_skala', on ? '1' : '0'); } catch (e) { } document.querySelectorAll('.js-plotly-plot').forEach(upd); };
  var raf = function (gd) { if (gd._sklR) return; gd._sklR = requestAnimationFrame(function () { gd._sklR = 0; upd(gd); }); };
  function hook(gd) {
    if (!gd || gd._sklHook || !gd.on) return; gd._sklHook = 1;
    gd.on('plotly_afterplot', function () { raf(gd); }); gd.on('plotly_relayout', function () { raf(gd); }); gd.on('plotly_relayouting', function () { raf(gd); });
  }
  function wrap() {
    if (!window.Plotly || Plotly._sklW) return !!(window.Plotly && Plotly._sklW); Plotly._sklW = 1;
    ['newPlot', 'react'].forEach(function (fn) {
      var o = Plotly[fn]; Plotly[fn] = function (el) {
        var r = o.apply(this, arguments), gd = typeof el === 'string' ? document.getElementById(el) : el;
        var go = function () { try { hook(gd); raf(gd); } catch (e) { } };
        if (r && r.then) r.then(go, function () { }); else go(); return r;
      };
    });
    window.addEventListener('resize', function () { document.querySelectorAll('.js-plotly-plot').forEach(raf); });
    return true;
  }
  if (!wrap()) { var t = setInterval(function () { if (wrap()) clearInterval(t); }, 200); setTimeout(function () { clearInterval(t); }, 30000); }
})();
