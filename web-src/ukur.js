/* ================= GC-Ex (Block Model 0.24.99 / Drillhole 0.24.102): UKUR JARAK DI 3D & PENAMPANG / PETA 2D =================
   Pemilik 17 Nov 2026: "tambahkan fitur ukur jarak baik dalam penampang 3d maupun penampang 2d".
   Modul bersama (BM: EXTRA sesudah skala.js; DH: daftar viewer sesudah skala.js). Tombol "Ukur" dipasang oleh skala.js di
   samping kotak skala pada setiap plot SPASIAL (peta / penampang 2D bersumbu meter, dan tampilan 3D).
   - Klik tombol (atau tekan U saat kursor di atas plot) -> mode ukur. Setiap klik menambah titik; jarak per ruas + total.
     Geser (drag) tetap memutar / menggeser tampilan seperti biasa; hanya klik tanpa geser yang menjadi titik.
   - 3D: titik MENEMPEL ke data terdekat di layar (bor, collar, permukaan, solid, titik; radius 14 px), karena satu klik di
     layar 3D tidak punya kedalaman. Hasil: jarak miring, horizontal, beda Z, azimuth & plunge, koordinat E N Z.
   - 2D: titik di posisi klik (koordinat sumbu). Jarak = jarak sebenarnya di bidang plot (meter), juga bila penampang
     memakai eksagerasi vertikal (VE hanya mengubah tampilan). Hasil: jarak, beda sumbu x & y, arah.
   - Klik kanan / Backspace = hapus titik terakhir; Esc atau tombol lagi = selesai; "Salin" = teks ke clipboard.
   Tidak mengubah data apa pun. */
(function () {
  if (window.UKUR) return;
  var U = window.UKUR = { aktif: null };
  var fx = function (v, d) { return (+v).toLocaleString('id-ID', { minimumFractionDigits: d, maximumFractionDigits: d }); };
  var css = document.createElement('style');
  css.textContent = '.gxUkurB{position:absolute;z-index:7;font:600 11px Segoe UI,Arial,sans-serif;padding:3px 8px;border-radius:4px;border:1px solid rgba(0,0,0,.25);background:rgba(255,255,255,.9);color:#1d2433;cursor:pointer}' +
    '.gxUkurB.on{background:#fcc419;border-color:#b08900}.gxUkurP{position:absolute;z-index:7;max-width:340px;font:11.5px/1.35 Segoe UI,Arial,sans-serif;background:rgba(17,24,39,.9);color:#fff;border-radius:6px;padding:6px 9px;pointer-events:auto}' +
    '.gxUkurP b{color:#fcc419}.gxUkurP .r{display:flex;gap:6px;margin-top:5px}.gxUkurP button{font:11px Segoe UI,Arial;padding:2px 7px;border-radius:3px;border:1px solid #888;background:#2b3445;color:#fff;cursor:pointer}' +
    '.gxUkurC{position:absolute;left:0;top:0;pointer-events:none;z-index:6}body.dark .gxUkurB,.dark .gxUkurB{background:rgba(26,32,44,.9);color:#e6e9ef;border-color:rgba(255,255,255,.3)}body.dark .gxUkurB.on{background:#fcc419;color:#111}';
  document.head.appendChild(css);
  var off = function () { return [+(window.offX || 0) || 0, +(window.offY || 0) || 0]; };
  var is3d = function (gd) { var fl = gd._fullLayout; return !!(fl && fl.scene && fl.scene._scene); };

  /* ---- tombol per plot (dipanggil skala.js setiap plot digambar ulang) ---- */
  U.pasang = function (gd, I, skBox) {
    var b = gd.querySelector(':scope > .gxUkurB');
    if (!I) { if (b) b.style.display = 'none'; if (U.aktif && U.aktif.gd === gd) U.selesai(); return; }
    if (!b) {
      b = document.createElement('button'); b.className = 'gxUkurB'; b.type = 'button'; b.innerHTML = '&#128207; Ukur';
      b.title = 'Ukur jarak (U): klik titik-titik di plot. ' + 'Klik kanan / Backspace = hapus titik terakhir, Esc = selesai.';
      b.onclick = function (e) { e.stopPropagation(); if (U.aktif && U.aktif.gd === gd) U.selesai(); else U.mulai(gd); };
      gd.appendChild(b);
    }
    b.style.display = '';
    var l = 10, bt = 10; if (skBox && skBox.style.display !== 'none') { l = skBox.offsetLeft + skBox.offsetWidth + 6; bt = parseFloat(skBox.style.bottom) || 10; }
    b.style.left = Math.round(l) + 'px'; b.style.bottom = Math.round(bt) + 'px'; b.classList.toggle('on', !!(U.aktif && U.aktif.gd === gd));
    if (U.aktif && U.aktif.gd === gd) gambar();
  };

  /* ---- mulai / selesai ---- */
  U.mulai = function (gd) {
    if (U.aktif) U.selesai(); gd = typeof gd === 'string' ? document.getElementById(gd) : gd; if (!gd || !gd._fullLayout) return;
    var A = U.aktif = { gd: gd, d3: is3d(gd), P: [], down: null, sig: '' };
    var c = document.createElement('canvas'); c.className = 'gxUkurC'; gd.appendChild(c); A.cv = c;
    var p = document.createElement('div'); p.className = 'gxUkurP'; gd.appendChild(p); A.pn = p;
    A.onDown = function (e) { if (e.button !== 0 || !inPlot(e)) return; A.down = [e.clientX, e.clientY]; };
    A.onUp = function (e) {
      if (e.button !== 0 || !A.down) return; var d = Math.hypot(e.clientX - A.down[0], e.clientY - A.down[1]); A.down = null; if (d > 4) return; /* target pointerup bisa 'dragcover' Plotly (di luar gd): cukup pointerdown di dalam plot */
      var r = gd.getBoundingClientRect(); U.tambahPx(e.clientX - r.left, e.clientY - r.top);
    };
    A.onCtx = function (e) { if (!inPlot(e)) return; e.preventDefault(); e.stopPropagation(); A.P.pop(); A.pesan = ''; gambar(); };
    A.onKey = function (e) {
      if (U.aktif !== A) return; var t = e.target && e.target.tagName; if (t === 'INPUT' || t === 'TEXTAREA' || t === 'SELECT') return;
      if (e.key === 'Escape') { U.selesai(); e.preventDefault(); } else if (e.key === 'Backspace') { A.P.pop(); A.pesan = ''; gambar(); e.preventDefault(); }
    };
    window.addEventListener('pointerdown', A.onDown, true); window.addEventListener('pointerup', A.onUp, true);
    gd.addEventListener('contextmenu', A.onCtx, true); window.addEventListener('keydown', A.onKey, true);
    /* 3D: kamera bisa diputar kapan saja -> gambar ulang bila matriks berubah */
    var loop = function () { if (U.aktif !== A) return; if (A.d3) { var s = kameraSig(gd); if (s !== A.sig) { A.sig = s; gambar(); } } A.raf = requestAnimationFrame(loop); };
    A.raf = requestAnimationFrame(loop);
    gd.classList.add('gxUkurOn'); gambar();
    var b = gd.querySelector(':scope > .gxUkurB'); if (b) b.classList.add('on');
  };
  U.selesai = function () {
    var A = U.aktif; if (!A) return; U.aktif = null; cancelAnimationFrame(A.raf);
    window.removeEventListener('pointerdown', A.onDown, true); window.removeEventListener('pointerup', A.onUp, true);
    A.gd.removeEventListener('contextmenu', A.onCtx, true); window.removeEventListener('keydown', A.onKey, true);
    if (A.cv) A.cv.remove(); if (A.pn) A.pn.remove(); A.gd.classList.remove('gxUkurOn');
    var b = A.gd.querySelector(':scope > .gxUkurB'); if (b) b.classList.remove('on');
  };
  function inPlot(e) { var A = U.aktif; if (!A) return false; var t = e.target; if (!A.gd.contains(t)) return false; if (t.closest && (t.closest('.modebar') || t.closest('.gxUkurP') || t.closest('.gxUkurB') || t.closest('.legend'))) return false; return true; }
  function kameraSig(gd) { try { var cp = gd._fullLayout.scene._scene.glplot.cameraParams; return cp.view.join(',') + cp.projection.join(',') + gd.clientWidth; } catch (e) { return ''; } }

  /* ---- piksel -> titik data ---- */
  U.tambahPx = function (px, py) {
    var A = U.aktif; if (!A) return null; var q = A.d3 ? snap3d(A.gd, px, py) : px2d(A.gd, px, py);
    if (!q) { A.pesan = A.d3 ? 'Klik tepat pada data (bor, collar, permukaan, solid) — titik 3D menempel ke data terdekat di layar.' : 'Klik di dalam area plot.'; gambar(); return null; }
    A.pesan = ''; A.P.push(q); gambar(); return q;
  };
  function px2d(gd, px, py) {
    var fl = gd._fullLayout, xa = fl.xaxis, ya = fl.yaxis; if (!xa || !ya) return null;
    var x = xa.p2l(px - xa._offset), y = ya.p2l(py - ya._offset); if (!isFinite(x) || !isFinite(y)) return null;
    if (px < xa._offset || px > xa._offset + xa._length || py < ya._offset || py > ya._offset + ya._length) return null; return [x, y];
  }
  function snap3d(gd, px, py) {
    var pr = window.SKL && SKL.proj3d ? SKL.proj3d(gd) : null; if (!pr) return null; var best = null, bd = 14 * 14;
    (gd.data || []).forEach(function (t) {
      if (t.visible === false || t.visible === 'legendonly' || (t.type !== 'scatter3d' && t.type !== 'mesh3d' && t.type !== 'cone')) return;
      var X = t.x, Y = t.y, Z = t.z; if (!X || !Y || !Z) return; var n = Math.min(X.length, Y.length, Z.length);
      for (var i = 0; i < n; i++) { var x = X[i], y = Y[i], z = Z[i]; if (x == null || y == null || z == null) continue; var s = pr(+x, +y, +z); if (!(s[2] > 0)) continue; var dx = s[0] - px, dy = s[1] - py, d = dx * dx + dy * dy; if (d < bd || (d === bd && best && s[2] < best.w)) { bd = d; best = { p: [+x, +y, +z], w: s[2] }; } }
    });
    return best ? best.p : null;
  }

  /* ---- hitung ---- */
  var az = function (dx, dy) { var a = Math.atan2(dx, dy) * 180 / Math.PI; return (a + 360) % 360; };
  U.hasil = function () {
    var A = U.aktif; if (!A) return null; var P = A.P, S = [], tot = 0, totH = 0;
    for (var i = 1; i < P.length; i++) {
      var a = P[i - 1], b = P[i];
      if (A.d3) { var dx = b[0] - a[0], dy = b[1] - a[1], dz = b[2] - a[2], h = Math.hypot(dx, dy), m = Math.hypot(h, dz); S.push({ d: m, h: h, dz: dz, az: az(dx, dy), pl: Math.atan2(dz, h) * 180 / Math.PI }); tot += m; totH += h; }
      else { var ex = b[0] - a[0], ey = b[1] - a[1], m2 = Math.hypot(ex, ey); S.push({ d: m2, dx: ex, dy: ey, ar: Math.atan2(ey, ex) * 180 / Math.PI }); tot += m2; }
    }
    return { d3: A.d3, P: P.slice(), ruas: S, total: tot, totalH: totH };
  };
  function judulSumbu(gd, a) { try { var t = gd._fullLayout[a].title; t = (t && (t.text || t)) || ''; t = String(t).replace(/<[^>]+>/g, '').trim(); return t.length > 18 ? t.slice(0, 18) + '…' : t; } catch (e) { return ''; } }
  function teks() {
    var A = U.aktif, R = U.hasil(), o = off(), L = [];
    if (!R.P.length) return A.d3 ? 'Klik data di 3D (bor, collar, permukaan) untuk titik pertama.' : 'Klik titik pertama di plot.';
    if (A.d3) {
      var p0 = R.P[R.P.length - 1]; L.push('Titik ' + R.P.length + ': E ' + fx(p0[0] + o[0], 2) + ' · N ' + fx(p0[1] + o[1], 2) + ' · Z ' + fx(p0[2], 2));
      R.ruas.forEach(function (s, i) { L.push((R.ruas.length > 1 ? 'Ruas ' + (i + 1) + ': ' : '') + '<b>' + fx(s.d, 2) + ' m</b> miring · horizontal ' + fx(s.h, 2) + ' m · ΔZ ' + (s.dz >= 0 ? '+' : '') + fx(s.dz, 2) + ' m · azimuth ' + fx(s.az, 1) + '° · plunge ' + fx(s.pl, 1) + '°'); });
      if (R.ruas.length > 1) L.push('<b>Total ' + fx(R.total, 2) + ' m</b> (horizontal ' + fx(R.totalH, 2) + ' m)');
    } else {
      var tx = judulSumbu(A.gd, 'xaxis') || 'x', ty = judulSumbu(A.gd, 'yaxis') || 'y';
      R.ruas.forEach(function (s, i) { L.push((R.ruas.length > 1 ? 'Ruas ' + (i + 1) + ': ' : '') + '<b>' + fx(s.d, 2) + ' m</b> · Δ' + tx + ' ' + fx(s.dx, 2) + ' · Δ' + ty + ' ' + fx(s.dy, 2)); });
      if (R.ruas.length > 1) L.push('<b>Total ' + fx(R.total, 2) + ' m</b>');
      if (!R.ruas.length) L.push('Klik titik berikutnya.');
    }
    return L.join('<br>');
  }
  U.salin = function () {
    var R = U.hasil(); if (!R) return ''; var o = off(), L = [];
    R.P.forEach(function (p, i) { L.push('P' + (i + 1) + '\t' + (R.d3 ? [p[0] + o[0], p[1] + o[1], p[2]] : p).map(function (v) { return (+v).toFixed(3); }).join('\t')); });
    R.ruas.forEach(function (s, i) { L.push('Ruas ' + (i + 1) + '\t' + s.d.toFixed(3) + ' m' + (R.d3 ? '\th ' + s.h.toFixed(3) + '\tdZ ' + s.dz.toFixed(3) + '\taz ' + s.az.toFixed(1) + '\tplunge ' + s.pl.toFixed(1) : '\tdx ' + s.dx.toFixed(3) + '\tdy ' + s.dy.toFixed(3))); });
    if (R.ruas.length > 1) L.push('Total\t' + R.total.toFixed(3) + ' m');
    var t = L.join('\n'); try { navigator.clipboard.writeText(t); } catch (e) { } return t;
  };

  /* ---- gambar garis, titik & panel ---- */
  function gambar() {
    var A = U.aktif; if (!A) return; var gd = A.gd, c = A.cv, W = gd.clientWidth, H = gd.clientHeight, dp = window.devicePixelRatio || 1;
    c.style.width = W + 'px'; c.style.height = H + 'px'; if (c.width !== Math.round(W * dp)) c.width = Math.round(W * dp); if (c.height !== Math.round(H * dp)) c.height = Math.round(H * dp);
    var x = c.getContext('2d'); x.setTransform(dp, 0, 0, dp, 0, 0); x.clearRect(0, 0, W, H);
    var S = [];
    if (A.d3) { var pr = window.SKL && SKL.proj3d ? SKL.proj3d(gd) : null; if (pr) S = A.P.map(function (p) { return pr(p[0], p[1], p[2]); }); }
    else { var fl = gd._fullLayout, xa = fl.xaxis, ya = fl.yaxis; if (xa && ya) S = A.P.map(function (p) { return [xa._offset + xa.l2p(p[0]), ya._offset + ya.l2p(p[1]), 1]; }); }
    if (S.length > 1) {
      x.lineWidth = 5; x.strokeStyle = 'rgba(17,17,17,.55)'; x.beginPath(); S.forEach(function (s, i) { if (i) x.lineTo(s[0], s[1]); else x.moveTo(s[0], s[1]); }); x.stroke();
      x.lineWidth = 2.5; x.strokeStyle = '#fcc419'; x.beginPath(); S.forEach(function (s, i) { if (i) x.lineTo(s[0], s[1]); else x.moveTo(s[0], s[1]); }); x.stroke();
      var R = U.hasil(); x.font = '600 11px Arial';
      for (var i = 1; i < S.length; i++) { var t = fx(R.ruas[i - 1].d, 1) + ' m', w = x.measureText(t).width + 8, mx = (S[i - 1][0] + S[i][0]) / 2, my = (S[i - 1][1] + S[i][1]) / 2; x.fillStyle = 'rgba(17,17,17,.82)'; x.fillRect(mx - w / 2, my - 18, w, 16); x.fillStyle = '#fff'; x.fillText(t, mx - w / 2 + 4, my - 6); }
    }
    S.forEach(function (s, i) { x.beginPath(); x.arc(s[0], s[1], 5, 0, 7); x.fillStyle = '#fcc419'; x.fill(); x.lineWidth = 1.5; x.strokeStyle = '#111'; x.stroke(); });
    var b = gd.querySelector(':scope > .gxUkurB'), pn = A.pn;
    pn.innerHTML = '<div><b>Ukur jarak</b> ' + (A.d3 ? '(3D, menempel ke data)' : '(2D)') + '</div><div>' + teks() + '</div>' + (A.pesan ? '<div style="color:#ffb4a2;margin-top:3px">' + A.pesan + '</div>' : '') +
      '<div class=r><button data-a=s>Salin</button><button data-a=h>Hapus</button><button data-a=x>Selesai (Esc)</button></div>';
    pn.querySelector('[data-a=s]').onclick = function (e) { e.stopPropagation(); U.salin(); };
    pn.querySelector('[data-a=h]').onclick = function (e) { e.stopPropagation(); A.P = []; A.pesan = ''; gambar(); };
    pn.querySelector('[data-a=x]').onclick = function (e) { e.stopPropagation(); U.selesai(); };
    var bl = b ? b.offsetLeft : 10, bb = b ? (parseFloat(b.style.bottom) || 10) + b.offsetHeight + 6 : 40; pn.style.left = bl + 'px'; pn.style.bottom = bb + 'px';
  }
  /* pintasan U saat kursor di atas plot spasial */
  var hover = null; document.addEventListener('pointermove', function (e) { var g = e.target && e.target.closest ? e.target.closest('.js-plotly-plot') : null; hover = g; }, true);
  window.addEventListener('keydown', function (e) {
    if ((e.key !== 'u' && e.key !== 'U') || e.ctrlKey || e.altKey || e.metaKey) return; var t = e.target && e.target.tagName; if (t === 'INPUT' || t === 'TEXTAREA' || t === 'SELECT' || (e.target && e.target.isContentEditable)) return;
    var g = hover; if (!g) return; var b = g.querySelector(':scope > .gxUkurB'); if (!b || b.style.display === 'none') return; e.preventDefault(); if (U.aktif && U.aktif.gd === g) U.selesai(); else U.mulai(g);
  });
})();
