/* ---------- Kinerja: diagnosa GPU + catatan jeda nyata di mesin pemakai (Block Model 0.24.47 / Drillhole 0.24.54) ----------
   Pemilik melaporkan jeda saat berganti panel / jendela. Di kontainer uji tidak ada GPU, jadi angkanya tidak mewakili
   laptop. Modul ini mencatat di mesin pemakai sendiri, per aksi (klik Project Tree / rail / tombol): berapa ms JavaScript
   memblokir layar (sinkron), berapa ms long task sesudahnya (termasuk render WebGL), dan panggilan Plotly yang terjadi.
   Juga memeriksa apakah WebGL memakai kartu grafis sungguhan atau perangkat lunak (SwiftShader / llvmpipe / Microsoft
   Basic Render) — penyebab paling umum 3D terasa berat di laptop. Semua tampil di panel "Tampilan & performa" dengan
   tombol salin laporan, supaya pemilik bisa mengirim angkanya. */
(function () {
  if (window.KIN) return;
  var K = window.KIN = { log: [], gpu: null, lunak: false, lt: 0, pl: [], aktif: null, maks: 40 };

  function gpuInfo() {
    try {
      var c = document.createElement('canvas'), gl = c.getContext('webgl2') || c.getContext('webgl') || c.getContext('experimental-webgl');
      if (!gl) return { ok: false, renderer: '(WebGL tidak tersedia)', vendor: '' };
      var d = gl.getExtension('WEBGL_debug_renderer_info'), r = d ? gl.getParameter(d.UNMASKED_RENDERER_WEBGL) : gl.getParameter(gl.RENDERER), v = d ? gl.getParameter(d.UNMASKED_VENDOR_WEBGL) : gl.getParameter(gl.VENDOR);
      var lunak = /swiftshader|llvmpipe|softpipe|software|microsoft basic render|warp/i.test(String(r) + ' ' + String(v));
      var ext = gl.getExtension('WEBGL_lose_context'); if (ext) ext.loseContext();
      return { ok: true, renderer: String(r), vendor: String(v), lunak: lunak, maxTex: gl.getParameter(gl.MAX_TEXTURE_SIZE) };
    } catch (e) { return { ok: false, renderer: '(gagal membaca: ' + e.message + ')', vendor: '' }; }
  }

  /* Waktu kotak dialog (prompt / confirm / alert) TIDAK dihitung (BM 0.24.56 / DH 0.24.61): selama dialog terbuka layar
     memang tertahan menunggu pemakai, bukan karena aplikasi lambat. Dulu "Pakai cut-off" tercatat 7,4 detik padahal
     hitungannya ±0,4 detik -- sisanya waktu pemilik mengetik batas kelas. */
  K.dlg = 0;
  ['prompt', 'confirm', 'alert'].forEach(function (k) { var f = window[k]; if (typeof f !== 'function' || f._kin) return; var w = function () { var t = performance.now(); try { return f.apply(window, arguments); } finally { var d = performance.now() - t; K.dlg += d; if (K.aktif) K.aktif.dlg = (K.aktif.dlg || 0) + d; } }; w._kin = 1; window[k] = w; });
  function catat(nama, sync, dlg) {
    var o = { t: new Date().toISOString().slice(11, 19), aksi: nama + (dlg > 50 ? ' (dialog ' + (dlg / 1000).toFixed(1) + ' dtk tidak dihitung)' : ''), sync: Math.round(Math.max(0, sync)), lt: 0, pl: [], dlg: dlg || 0 };
    K.log.unshift(o); if (K.log.length > K.maks) K.log.length = K.maks;
    K.aktif = o; setTimeout(function () { if (K.aktif === o) K.aktif = null; gambar(); }, 1600);
    return o;
  }
  function pasangPengamat() {
    try {
      new PerformanceObserver(function (l) { l.getEntries().forEach(function (e) { if (!K.aktif) return; var o = K.aktif, d = e.duration, sisa = Math.max(0, (o.dlg || 0) - (o._dlgLt || 0)), pot = Math.min(d, sisa); o._dlgLt = (o._dlgLt || 0) + pot; o.lt += d - pot; }); }).observe({ entryTypes: ['longtask'] });
    } catch (e) {}
    var P = window.Plotly; if (!P || P._kinW) return;
    ['react', 'newPlot', 'relayout', 'restyle'].forEach(function (k) {
      var f = P[k]; if (typeof f !== 'function') return;
      P[k] = function () { var t = performance.now(), o = K.aktif, r = f.apply(this, arguments); var fin = function () { if (o) o.pl.push(k + ':' + Math.round(performance.now() - t)); }; if (r && r.then) r.then(fin, fin); else fin(); return r; };
    });
    if (P.Plots && typeof P.Plots.resize === 'function') { var rs = P.Plots.resize; P.Plots.resize = function () { var t = performance.now(), o = K.aktif, r = rs.apply(this, arguments); var fin = function () { if (o) o.pl.push('resize:' + Math.round(performance.now() - t)); }; if (r && r.then) r.then(fin, fin); else fin(); return r; }; }
    P._kinW = 1;
  }
  /* nama aksi dari elemen yang diklik: baris Project Tree, tombol rail, tombol / label biasa */
  function namaAksi(e) {
    var t = e.target.closest ? e.target.closest('.ptr,.rb,button,label.mdbtn,input[type=checkbox],select,.uitabs button') : null;
    if (!t) return null;
    if (t.classList.contains('ptr')) return 'Tree: ' + ((t.querySelector('.ptl') || t).textContent.trim().slice(0, 40));
    if (t.classList.contains('rb')) return 'Rail: ' + (t.title || t.id);
    var s = (t.textContent || t.value || t.id || t.tagName).trim().slice(0, 40);
    return (t.tagName === 'SELECT' ? 'Pilih: ' : t.type === 'checkbox' ? 'Centang: ' : 'Tombol: ') + (s || t.id);
  }
  function pasangKlik() {
    var t0 = 0, nama = null, d0 = 0;
    document.addEventListener('click', function (e) { nama = namaAksi(e); t0 = nama ? performance.now() : 0; d0 = K.dlg; }, true);
    window.addEventListener('click', function () { if (!t0) return; var dl = K.dlg - d0; catat(nama, performance.now() - t0 - dl, dl); t0 = 0; }, false);
    document.addEventListener('change', function (e) { var n = namaAksi(e); if (n) { t0 = performance.now(); d0 = K.dlg; setTimeout(function () { if (t0) { var dl = K.dlg - d0; catat(n, performance.now() - t0 - dl, dl); t0 = 0; } }, 0); } }, true);
  }

  function laporan() {
    var g = K.gpu || {}, L = ['GC-Ex laporan kinerja ' + new Date().toISOString(), 'Aplikasi: ' + (document.title || '') + ' | UA: ' + navigator.userAgent,
      'CPU logis: ' + (navigator.hardwareConcurrency || '?') + ' | RAM (perkiraan): ' + (navigator.deviceMemory || '?') + ' GB | Layar: ' + screen.width + 'x' + screen.height + ' @' + (window.devicePixelRatio || 1),
      'GPU WebGL: ' + g.renderer + ' | ' + g.vendor + (g.lunak ? '  <<< RENDER PERANGKAT LUNAK (bukan kartu grafis) — penyebab utama jeda' : ''),
      'Data: ' + ringkasData(), '', 'waktu    | sinkron ms | long task ms | aksi | plotly'];
    K.log.slice().reverse().forEach(function (o) { L.push(o.t + ' | ' + String(o.sync).padStart(6) + ' | ' + String(Math.round(o.lt)).padStart(8) + ' | ' + o.aksi + ' | ' + o.pl.join(',')); });
    return L.join('\n');
  }
  function ringkasData() {
    var s = [];
    try { if (window.collars) s.push(collars.length + ' hole'); } catch (e) {}
    try { if (window.assays) s.push(assays.length.toLocaleString() + ' sampel'); } catch (e) {}
    try { if (window.BX && BX.m) s.push(BX.m.n.toLocaleString() + ' blok'); } catch (e) {}
    try { if (window.GLSKIP) s.push('glskip lewati/update ' + GLSKIP.skip + '/' + GLSKIP.run); } catch (e) {}
    try { var gd = document.getElementById('plotDiv'); if (gd && gd.data) s.push(gd.data.length + ' lapisan 3D, ' + gd.data.reduce(function (a, t) { return a + ((t.x && t.x.length) || (t.i && t.i.length) || 0); }, 0).toLocaleString() + ' titik'); } catch (e) {}
    return s.join(' · ') || '-';
  }
  function salin() {
    var t = laporan();
    var done = function () { var b = document.getElementById('kinSalin'); if (b) { b.textContent = 'Tersalin ✓'; setTimeout(function () { b.textContent = 'Salin laporan kinerja'; }, 1500); } };
    if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(t).then(done, function () { prompt('Salin teks ini:', t); });
    else prompt('Salin teks ini:', t);
  }
  K.laporan = laporan; K.salin = salin; K.gambar = function () { gambar(); };

  function gambar() {
    var box = document.getElementById('kinBox'); if (!box) return;
    var g = K.gpu || {}, st = !g.ok ? '<span style="color:#b00">WebGL tidak tersedia</span>' : g.lunak ? '<span style="color:#b00;font-weight:600">Render perangkat lunak — kartu grafis TIDAK dipakai</span>' : '<span style="color:#1b7f3b;font-weight:600">Kartu grafis aktif</span>';
    var rows = K.log.slice(0, 12).map(function (o) { var berat = (o.sync + o.lt) > 400; return '<tr' + (berat ? ' style="color:#b00"' : '') + '><td>' + o.t + '</td><td style="text-align:right">' + o.sync + '</td><td style="text-align:right">' + Math.round(o.lt) + '</td><td title="' + o.pl.join(', ') + '">' + o.aksi + '</td></tr>'; }).join('');
    box.innerHTML = '<h3>Kinerja &amp; grafis</h3><div class="hint">' + st + '<br><span style="font-size:11px">' + (g.renderer || '') + '</span>' +
      (g.lunak ? '<br><b>Yang bisa dilakukan:</b> perbarui driver kartu grafis; di Windows → Settings → System → Display → Graphics: tambahkan GC-Ex dan pilih <i>High performance</i>; pastikan laptop tidak dalam mode hemat daya.' : '') + '</div>' +
      '<div class="hint" style="margin-top:6px">Catatan jeda aksi terakhir (ms; merah = terasa, &gt; 0,4 detik). <i>Sinkron</i> = JavaScript memblokir layar; <i>long task</i> = total pekerjaan berat 1,5 detik sesudah klik, termasuk render 3D.</div>' +
      '<table style="width:100%;font-size:11px;border-collapse:collapse"><tr><th>jam</th><th>sinkron</th><th>long task</th><th style="text-align:left">aksi</th></tr>' + (rows || '<tr><td colspan=4 class=hint>(belum ada)</td></tr>') + '</table>' +
      '<div style="margin-top:6px"><button type="button" id="kinSalin" onclick="KIN.salin()">Salin laporan kinerja</button> <span class="hint">lalu tempel ke pesan untuk dianalisis</span></div>';
  }
  function pasangBox() {
    var p = document.getElementById('pView'); if (!p || document.getElementById('kinBox')) return;
    var box = document.createElement('div'); box.id = 'kinBox'; box.className = 'uisec'; p.appendChild(box); gambar();
  }
  function mulai() {
    K.gpu = gpuInfo(); K.lunak = !!K.gpu.lunak;
    pasangPengamat(); pasangKlik(); pasangBox();
    if (K.lunak) { console.warn('[GC-Ex] WebGL memakai render perangkat lunak: ' + K.gpu.renderer); try { if (window.FP && FP.toast) FP.toast('Kartu grafis tidak dipakai (render perangkat lunak) — 3D akan terasa berat. Lihat panel Tampilan & performa.', 9000); } catch (e) {} }
    setInterval(gambar, 2500);
  }
  if (document.readyState === 'complete') setTimeout(mulai, 1500); else window.addEventListener('load', function () { setTimeout(mulai, 1500); });
})();
