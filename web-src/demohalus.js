/* ================= GC-Ex (BM 0.24.104 / DH 0.24.107): DEMO SEHALUS VIDEO TANGKAPAN LAYAR =================
   Pemilik 17 Nov 2026: "Demo berjalan seperti video tangkapan layar: kursor bergerak halus ke tombol dan mengklik; angka
   diketik huruf demi huruf; poligon dan garis urat digambar perlahan di peta; kamera berpindah dengan mulus; ada bilah
   keterangan di bawah: bab, judul langkah, dan satu kalimat penjelasan."
   Modul bersama (dipasang sesudah demox.js), hanya mengubah perilaku SAAT DEMO BERJALAN (DM.on):
   1. Kursor tidak lagi disembunyikan tiap langkah: ia meluncur (kurva ease-in-out) dari tombol ke tombol. dmSet / dmClick
      menunggu kursor tiba, baru "mengklik" (riak) dan menjalankan aksinya.
   2. Isian teks / angka diketik huruf demi huruf (±55 ms per huruf), baru onchange dijalankan.
   3. Digitasi poligon / string (dig block, garis urat di penampang): tiap titik baru digambar sebagai garis yang memanjang
      dari titik sebelumnya, dengan kursor mengikuti ujungnya, lalu titik "diklik".
   4. setCam (Top / Front / Side / Iso / langkah demo) berpindah mulus: mata kamera diinterpolasi ±0,9 s, bukan meloncat.
   5. Bilah keterangan di bawah: bab · judul langkah · satu kalimat (kalimat pertama keterangan), teks memudar saat berganti.
   Di luar demo semua fungsi bekerja seperti biasa. */
(function () {
  if (window.DMH || typeof window.dmSet !== 'function' || typeof window.DM === 'undefined') return;
  var DMH = window.DMH = { tempuh: 650, ketik: 55, garis: 520, kamera: 900 };
  var $ = function (i) { return document.getElementById(i); };
  var aktif = function () { return !!(window.DM && DM.on); };
  var css = document.createElement('style');
  css.textContent = '#dmCur{transition:left .62s cubic-bezier(.45,0,.25,1),top .62s cubic-bezier(.45,0,.25,1),opacity .25s!important}' +
    '#dmBar .dmC>*,#dmSec,#dmT,#dmD{transition:opacity .35s ease}#dmBar.dmGanti #dmSec,#dmBar.dmGanti #dmT,#dmBar.dmGanti #dmD{opacity:0}' +
    '#dmD{display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}';
  document.head.appendChild(css);

  /* ---------- kursor ---------- */
  var kursor = function () { return $('dmCur'); };
  var posKursor = function () { var c = kursor(); if (!c || c.style.opacity === '0' || !c.style.left) return null; return [parseFloat(c.style.left), parseFloat(c.style.top)]; };
  DMH.ke = function (x, y, tap, cepat) {
    var c = kursor(); if (!c) return 0; var p = posKursor(), jauh = p ? Math.hypot(p[0] - x, p[1] - y) : 0;
    if (cepat) { c.style.transition = 'none'; } c.style.left = x + 'px'; c.style.top = y + 'px'; c.style.opacity = 1;
    if (cepat) { void c.offsetWidth; c.style.transition = ''; }
    var t = cepat || jauh < 4 ? 0 : DMH.tempuh * (window.DM && DM.spd ? Math.max(0.6, Math.min(1.2, DM.spd / 0.55)) : 1);
    if (tap) setTimeout(function () { DMH.tap(); }, t);
    return t;
  };
  DMH.tap = function () { var c = kursor(); if (!c) return; c.classList.remove('tap'); void c.offsetWidth; c.classList.add('tap'); };
  var titikEl = function (e) { var r = e.getBoundingClientRect(); return [r.left + Math.min(r.width - 6, Math.max(8, r.width * 0.6)), r.top + r.height * 0.6]; };

  /* dmPoint: sorotan + kursor meluncur (tanpa riak di awal perjalanan) */
  var _point = window.dmPoint;
  window.dmPoint = dmPoint = function (x, tap) {
    if (!aktif()) return _point.apply(this, arguments);
    var e = dmEl(x), h = $('dmHi'); if (!dmVis(e)) { if (h) h.style.opacity = 0; return 0; }
    var r = e.getBoundingClientRect(); h.style.left = (r.left - 4) + 'px'; h.style.top = (r.top - 4) + 'px'; h.style.width = (r.width + 8) + 'px'; h.style.height = (r.height + 8) + 'px'; h.style.opacity = 1;
    var q = titikEl(e); return DMH.ke(q[0], q[1], tap);
  };
  /* dmHide di awal langkah: sorotan saja yang hilang, kursor tetap di tempat (meluncur ke target berikutnya) */
  var _hide = window.dmHide;
  window.dmHide = dmHide = function () { if (!aktif()) return _hide.apply(this, arguments); var h = $('dmHi'); if (h) h.style.opacity = 0; };

  /* ---------- klik & isian: tunggu kursor tiba ---------- */
  var antre = [];
  var tunda = function (ms, fn) { var id = setTimeout(function () { antre = antre.filter(function (x) { return x !== id; }); if (aktif()) fn(); }, ms); antre.push(id); };
  var _set = window.dmSet;
  window.dmSet = dmSet = function (id, v) {
    if (!aktif()) return _set.apply(this, arguments);
    var e = $(id); if (!e || e.disabled) return;
    var t = dmPoint(e, false) || 0, ketik = (e.tagName === 'INPUT' && /^(text|number|search|)$/i.test(e.type)) || e.tagName === 'TEXTAREA';
    tunda(t, function () {
      DMH.tap();
      if (e.type === 'checkbox') { e.checked = !!v; dmFire(e); return; }
      if (!ketik) { e.value = v; dmFire(e); return; }
      /* isian type=number menolak teks setengah jadi ("12.") -> sementara jadi teks selama mengetik */
      var s = String(v), k = 0, angka = e.type === 'number'; if (angka) { try { e.type = 'text'; } catch (x) { angka = false; } } e.value = ''; e.focus && e.focus({ preventScroll: true });
      var akhir = function () { if (angka) { try { e.type = 'number'; } catch (x) { } } e.value = s; try { e.blur(); } catch (x) { } };
      var langkah = function () { if (!aktif()) { akhir(); return; } k++; e.value = s.slice(0, k); if (k < s.length) setTimeout(langkah, DMH.ketik); else { akhir(); dmFire(e); } };
      if (s.length) setTimeout(langkah, 120); else { akhir(); dmFire(e); }
    });
  };
  var _click = window.dmClick;
  window.dmClick = dmClick = function (x) {
    if (!aktif()) return _click.apply(this, arguments);
    var e = dmEl(x); if (!e) return; var t = dmPoint(e, false) || 0;
    tunda(t, function () { DMH.tap(); if (typeof e.onclick === 'function') e.onclick(); });
  };

  /* ---------- digitasi: garis memanjang ke titik baru, kursor mengikuti ---------- */
  if (typeof window.dgDraw === 'function' && window.DG) {
    var _draw = window.dgDraw, nAkhir = 0, anim = null;
    var px = function (q) { try { var A = dgAx(); if (!A) return null; var p = dgPx(A, q[0], q[1]); return [A.r.left + p[0], A.r.top + p[1], p[0], p[1]]; } catch (e) { return null; } };
    window.dgDraw = dgDraw = function () {
      if (!aktif() || !DG.on || !DG.c2 || anim) { if (DG.c2) nAkhir = DG.c2.length; return _draw.apply(this, arguments); }
      var n = DG.c2.length;
      if (n !== nAkhir + 1) { nAkhir = n; return _draw.apply(this, arguments); }
      var q = DG.c2[n - 1], b = px(q); if (!b) { nAkhir = n; return _draw.apply(this, arguments); }
      DG.c2.pop(); var a = n > 1 ? px(DG.c2[n - 2]) : null, t0 = performance.now(), dur = a ? DMH.garis : 0, self = this;
      if (!a) { var tt = DMH.ke(b[0], b[1], false); anim = 1; setTimeout(function () { anim = null; DG.c2.push(q); nAkhir = DG.c2.length; DG.hov = null; DMH.tap(); _draw.call(self); }, tt); return; }
      DMH.ke(a[0], a[1], false, true); anim = 1;
      var f = function () {
        if (!aktif()) { anim = null; DG.c2.push(q); nAkhir = DG.c2.length; DG.hov = null; _draw.call(self); return; }
        var u = Math.min(1, (performance.now() - t0) / dur), e = u < 0.5 ? 2 * u * u : 1 - Math.pow(-2 * u + 2, 2) / 2;
        var x = a[2] + (b[2] - a[2]) * e, y = a[3] + (b[3] - a[3]) * e; DG.hov = [x, y]; _draw.call(self); DMH.ke(a[0] + (b[0] - a[0]) * e, a[1] + (b[1] - a[1]) * e, false, true);
        if (u < 1) requestAnimationFrame(f); else { anim = null; DG.hov = null; DG.c2.push(q); nAkhir = DG.c2.length; DMH.tap(); _draw.call(self); }
      };
      requestAnimationFrame(f);
    };
  }

  /* ---------- kamera mulus ---------- */
  if (typeof window.setCam === 'function') {
    var _cam = window.setCam, gerak = null;
    window.setCam = setCam = function (x, y, z, up) {
      if (!aktif() || window.VIEW2D) return _cam.apply(this, arguments);
      var gd = $('plotDiv'), cam = null; try { cam = gd._fullLayout.scene.camera; } catch (e) { }
      if (!cam || !cam.eye) return _cam.apply(this, arguments);
      var e0 = { x: cam.eye.x, y: cam.eye.y, z: cam.eye.z }, c0 = cam.center || { x: 0, y: 0, z: 0 }, u1 = up || { x: 0, y: 0, z: 1 }, t0 = performance.now(), dur = DMH.kamera, id = {};
      gerak = id;
      /* interpolasi dalam koordinat bola supaya kamera mengitari, bukan menembus model */
      var bola = function (p) { var r = Math.sqrt(p.x * p.x + p.y * p.y + p.z * p.z) || 1; return { r: r, az: Math.atan2(p.y, p.x), el: Math.asin(Math.max(-1, Math.min(1, p.z / r))) }; };
      var A = bola(e0), B = bola({ x: x, y: y, z: z }), dAz = B.az - A.az; if (dAz > Math.PI) dAz -= 2 * Math.PI; if (dAz < -Math.PI) dAz += 2 * Math.PI;
      var f = function () {
        if (gerak !== id) return;
        var u = Math.min(1, (performance.now() - t0) / dur), e = u < 0.5 ? 4 * u * u * u : 1 - Math.pow(-2 * u + 2, 3) / 2;
        var r = A.r + (B.r - A.r) * e, az = A.az + dAz * e, el = A.el + (B.el - A.el) * e;
        var eye = { x: r * Math.cos(el) * Math.cos(az), y: r * Math.cos(el) * Math.sin(az), z: r * Math.sin(el) };
        var ctr = { x: c0.x * (1 - e), y: c0.y * (1 - e), z: c0.z * (1 - e) };
        try { Plotly.relayout(gd, { 'scene.camera': { eye: eye, up: u1, center: ctr } }); } catch (er) { }
        if (u < 1) requestAnimationFrame(f); else { gerak = null; window.__camNext = { eye: { x: x, y: y, z: z }, up: u1, center: { x: 0, y: 0, z: 0 } }; }
      };
      requestAnimationFrame(f);
    };
  }

  /* ---------- bilah keterangan: bab · judul · satu kalimat, memudar saat berganti ---------- */
  var _go = window.dmGo;
  window.dmGo = dmGo = function (i) {
    if (!aktif()) return _go.apply(this, arguments);
    var bar = $('dmBar'); if (bar) bar.classList.add('dmGanti');
    var r = _go.apply(this, arguments);
    var d = $('dmD'); if (d && d.textContent) { var m = /^(.+?[.!?])(\s|$)/.exec(d.textContent.replace(/\s+/g, ' ').trim()); if (m && m[1].length >= 25) { d.title = d.textContent; d.textContent = m[1]; } }
    setTimeout(function () { if (bar) bar.classList.remove('dmGanti'); }, 60);
    return r;
  };
  /* bilah keterangan tidak ikut menyempit saat panel lebar (Geostatistik, Model Estimation) mempersempit area 3D:
     lebar minimal 620 px, tetap di dalam jendela (BM 0.24.106 / DH 0.24.109) */
  if (typeof window.dmPos === 'function') {
    var _pos = window.dmPos;
    window.dmPos = dmPos = function () {
      var r = _pos.apply(this, arguments), b = $('dmBar'), gd = $('plotDiv'); if (!b || !gd) return r;
      var g = gd.getBoundingClientRect(), vw = window.innerWidth, w = Math.min(920, Math.max(620, g.width - 24), vw - 24);
      var cx = g.left + g.width / 2; cx = Math.max(w / 2 + 12, Math.min(vw - w / 2 - 12, cx));
      b.style.width = w + 'px'; b.style.left = cx + 'px'; return r;
    };
  }
  /* berhenti: batalkan aksi yang masih menunggu kursor */
  var _stop = window.dmStop;
  window.dmStop = dmStop = function () { antre.forEach(clearTimeout); antre = []; return _stop.apply(this, arguments); };
})();
