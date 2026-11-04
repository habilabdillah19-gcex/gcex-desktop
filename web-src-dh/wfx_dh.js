/* ============ WIREFRAME LUAR (LEAPFROG / SURPAC) SEBAGAI DOMAIN GC-EX ============
   Dua cara memakai wireframe implicit dari Leapfrog, untuk dua tujuan yang berbeda.

   MODE B — DISERAP (bisa diedit, ikut berubah saat ada bor baru)
     wireframe -> diiris per section -> tiap loop tertutup dibelah jadi string HW & FW ->
     string kontrol domain -> solid RBF. Sesudah ini domainnya sama saja dengan domain yang
     digambar sendiri: titik string bisa ditarik, section bisa ditambah, solid rebuild otomatis.
     Bentuknya REKONSTRUKSI, bukan salinan: diresample sesuai spasi section lalu dihaluskan RBF.
     Fungsi gmWfFlag() + gmWfStrings() sudah ada di panel Geomodeller Vein; modul ini hanya
     menjadikannya SATU perintah (wfSerap) dan menambahkan kontrol mutunya: volume wireframe
     vs volume solid hasil serap.

   MODE A — EKSAK (dipakai apa adanya, tidak bisa diedit)
     domain "dikunci" ke wireframe: uji titik-di-dalam memakai mesh Leapfrog itu sendiri, tanpa
     RBF. Volumenya volume mesh. Gunanya audit — mengestimasi dua kali (batas Leapfrog eksak vs
     solid GC-Ex) lalu membandingkan tonase. Karena bentuknya milik Leapfrog, ia TIDAK berubah
     saat ada bor baru; itu sifat yang diinginkan untuk audit, dan kekurangannya untuk kerja
     harian.
     Disambungkan pada SATU titik: meGrpR(d). Seluruh mesin GC-Ex (estimasi, waste, sub-blocking,
     filter posisi, pelaporan) membaca solid domain lewat fungsi itu, jadi satu sambungan membuat
     mode eksak berlaku di semuanya tanpa menyentuh fungsi analisis mana pun.                   */
(function () {
  if (window.WFX) return;
  var WFX = window.WFX = { c: {}, o: { sp: 0, nama: '', mi: 0, mode: 'B' }, log: null };

  function E(s) { return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; }); }
  function N(v, d) { return (v == null || !isFinite(v)) ? '-' : (+v).toLocaleString('id-ID', { maximumFractionDigits: d == null ? 0 : d }); }
  function $(i) { return document.getElementById(i); }
  function fn(n) { return typeof window[n] === 'function'; }
  function models() { return (window.MD && MD.models) || []; }
  function byName(nm) { var o = null; models().forEach(function (m) { if (m.name === nm) o = m; }); return o; }

  /* ---------- volume mesh tertutup: jumlah tetrahedron bertanda terhadap titik asal ---------- */
  function volMesh(m) {
    if (!m || !m.nt) return null;
    if (fn('mdLocal')) mdLocal(m);
    var X = m._x, Y = m._y, Z = m._z, I = m._i, J = m._j, K = m._k, s = 0;
    if (!X || !I) return null;
    for (var t = 0; t < m.nt; t++) {
      var a = I[t], b = J[t], c = K[t];
      s += (X[a] * (Y[b] * Z[c] - Z[b] * Y[c])
          - Y[a] * (X[b] * Z[c] - Z[b] * X[c])
          + Z[a] * (X[b] * Y[c] - Y[b] * X[c])) / 6;
    }
    return Math.abs(s);
  }
  window.wfVol = volMesh;

  /* ---------- kerangka (pusat + sumbu utama) dari verteks mesh, untuk tampilan elipsoid ---------- */
  function frameMesh(m) {
    if (fn('mdLocal')) mdLocal(m);
    var X = m._x, Y = m._y, Z = m._z, n = m.nv, c = [0, 0, 0], i;
    if (!X || !n) return null;
    for (i = 0; i < n; i++) { c[0] += X[i]; c[1] += Y[i]; c[2] += Z[i]; }
    c = [c[0] / n, c[1] / n, c[2] / n];
    /* kovarians 3x3 -> sumbu utama lewat iterasi daya sederhana (cukup untuk tampilan) */
    var C = [0, 0, 0, 0, 0, 0, 0, 0, 0];
    for (i = 0; i < n; i++) {
      var d0 = X[i] - c[0], d1 = Y[i] - c[1], d2 = Z[i] - c[2], D = [d0, d1, d2];
      for (var p = 0; p < 3; p++) for (var q = 0; q < 3; q++) C[p * 3 + q] += D[p] * D[q];
    }
    var mul = function (v) { return [C[0] * v[0] + C[1] * v[1] + C[2] * v[2], C[3] * v[0] + C[4] * v[1] + C[5] * v[2], C[6] * v[0] + C[7] * v[1] + C[8] * v[2]]; };
    var norm = function (v) { var L = Math.hypot(v[0], v[1], v[2]) || 1; return [v[0] / L, v[1] / L, v[2] / L]; };
    var daya = function (v0) { var v = v0; for (var k = 0; k < 40; k++) v = norm(mul(v)); return v; };
    var u = daya([1, 0.3, 0.1]);
    var sub = function (v, w, s) { return [v[0] - w[0] * s, v[1] - w[1] * s, v[2] - w[2] * s]; };
    var dot = function (v, w) { return v[0] * w[0] + v[1] * w[1] + v[2] * w[2]; };
    var v2 = daya(norm(sub([0.2, 1, 0.4], u, dot([0.2, 1, 0.4], u))));
    v2 = norm(sub(v2, u, dot(v2, u)));
    var n3 = norm([u[1] * v2[2] - u[2] * v2[1], u[2] * v2[0] - u[0] * v2[2], u[0] * v2[1] - u[1] * v2[0]]);
    return { c: c, u: u, v: v2, n: n3 };
  }

  /* ================= MODE A: domain dikunci ke mesh wireframe ================= */

  window.wfxOf = function (d) { return d && d.wfx ? d.wfx : null; };
  window.wfxPakai = function (domId, nama) {
    var d = fn('gmDom') ? gmDom(domId) : null; if (!d) return;
    var m = byName(nama);
    if (!m) { alert('Wireframe "' + nama + '" tidak ada di Data Referensi.'); return; }
    var V = volMesh(m), W = fn('wfInside') ? wfInside(m) : null;
    if (W && W.open) {
      if (!confirm('Wireframe "' + nama + '" tidak tertutup rapat (' + W.open + ' dari ' + W.ne +
                   ' sisi terbuka). Uji titik-di-dalam pada wireframe bocor tidak bisa dipercaya, ' +
                   'dan estimasi akan memakai hasilnya apa adanya.\n\nTetap pakai sebagai batas eksak?')) return;
    }
    d.wfx = nama; WFX.c = {};
    alert('Domain "' + d.name + '" sekarang memakai wireframe "' + nama + '" sebagai batas EKSAK' +
          (V ? ' (volume ' + N(V) + ' m³)' : '') + '.\n\n' +
          'Bentuknya milik Leapfrog: tidak bisa diedit di GC-Ex dan TIDAK berubah saat ada bor baru. ' +
          'Untuk domain yang bisa diedit dan ikut diperbarui, pakai "Serap wireframe".');
    try { gmDirty(); } catch (e) {}
    try { if (window.PT && PT.render) PT.render(true); } catch (e) {}
  };
  window.wfxLepas = function (domId) {
    var d = fn('gmDom') ? gmDom(domId) : null; if (!d || !d.wfx) return;
    delete d.wfx; WFX.c = {};
    try { gmDirty(); } catch (e) {}
    try { if (window.PT && PT.render) PT.render(true); } catch (e) {}
  };

  /* satu-satunya sambungan mode eksak: seluruh mesin membaca solid domain lewat meGrpR() */
  if (fn('meGrpR')) {
    var _g = window.meGrpR;
    window.meGrpR = function (d) {
      var nm = d && d.wfx;
      if (!nm) return _g.apply(this, arguments);
      var m = byName(nm);
      if (!m) return _g.apply(this, arguments);   /* wireframe belum diimport ulang -> kembali ke RBF */
      var key = nm + '|' + m.nt + '|' + m.nv, c = WFX.c[d.id];
      if (c && c.key === key) return c;
      var W = wfInside(m), V = volMesh(m);
      c = {
        key: key, mesh: m, W: W, fr: frameMesh(m), wfx: nm,
        st: { vol: V, area: null, tav: 0, tmin: 0, tmax: 0, nH: 0, nW: 0, nHt: 0, nWt: 0, nc: 0, rms: 0, emax: 0 }
      };
      WFX.c[d.id] = c; return c;
    };
  }

  /* ================= MODE B: serap wireframe menjadi domain yang bisa diedit ================= */

  function lap(o) { WFX.log.baris.push(o); kotak(); }
  function kotak() {
    var d = $('wfxDlg');
    if (!d) { d = document.createElement('div'); d.id = 'wfxDlg'; d.className = 'bxdlg'; document.body.appendChild(d); }
    var L = WFX.log || { judul: '', baris: [] };
    d.innerHTML = '<div class=impBox style=width:min(880px,100%)><div class=impHead><div class=impBrand><div><b>' + E(L.judul) + '</b>' +
      '<small>Wireframe diubah menjadi string kontrol HW / FW, lalu solid dibangun RBF. Sesudah ini domainnya bisa diedit dan ikut diperbarui saat ada bor baru.</small>' +
      '</div></div><button class="ib ghost" onclick="wfxClose()">Tutup</button></div><div class=impBody>' +
      '<table class=pltb><tr><th>Langkah</th><th>Hasil</th><th>Catatan</th></tr>' +
      (L.baris.map(function (b) {
        return '<tr' + (b.lewat ? ' style="opacity:.75"' : '') + '><td><b>' + E(b.nama) + '</b></td><td>' +
          (b.lewat ? '<span class=warn>' + (b.hasil || 'dilewati') + '</span>' : (b.hasil || '')) +
          '</td><td><small>' + (b.ket || '') + '</small></td></tr>';
      }).join('') || '<tr><td colspan=3 class=hint>&hellip;</td></tr>') + '</table>' +
      (L.pesan ? '<div class=box>' + L.pesan + '</div>' : '') +
      '</div><div class=impFoot><div class=hint></div><button class=ib onclick="wfxClose()">Selesai</button></div></div>';
    d.style.display = 'flex';
  }
  window.wfxClose = function () { var d = $('wfxDlg'); if (d) d.style.display = 'none'; };
  window.wfxLihat = function () { if (WFX.log) kotak(); else alert('Belum ada penyerapan wireframe di sesi ini.'); };

  /* strike dari verteks mesh di bidang datar (sumbu utama XY) */
  function strikeMesh(m) {
    if (fn('mdLocal')) mdLocal(m);
    var X = m._x, Y = m._y, n = m.nv, mx = 0, my = 0, i;
    for (i = 0; i < n; i++) { mx += X[i]; my += Y[i]; }
    mx /= n; my /= n;
    var sxx = 0, syy = 0, sxy = 0;
    for (i = 0; i < n; i++) { var dx = X[i] - mx, dy = Y[i] - my; sxx += dx * dx; syy += dy * dy; sxy += dx * dy; }
    var ang = 0.5 * Math.atan2(2 * sxy, sxx - syy), ux = Math.cos(ang), uy = Math.sin(ang);
    var az = Math.atan2(ux, uy) * 180 / Math.PI;
    az = ((az % 180) + 180) % 180;
    var vx = Math.cos(ang + Math.PI / 2), vy = Math.sin(ang + Math.PI / 2), lo = 1e18, hi = -1e18;
    for (i = 0; i < n; i++) { var s = (X[i] - mx) * vx + (Y[i] - my) * vy; lo = Math.min(lo, s); hi = Math.max(hi, s); }
    return { az: az, c: [mx, my], panjang: Math.max(50, (hi - lo) * 1.4) };
  }

  window.wfSerap = function () {
    var M = models();
    var m = M[WFX.o.mi | 0];
    if (!m) { alert('Import wireframe dulu di menu Data Referensi (.msh / .obj / .dxf / .dtm + .str).'); return; }
    if (!window.GM) { alert('Menu Geomodeller Vein belum siap.'); return; }

    var nm = (WFX.o.nama || '').trim() || String(m.name).replace(/\.[^.]+$/, '').replace(/[^A-Za-z0-9_-]+/g, '_').slice(0, 30) || 'Vein_WF';
    WFX.log = { judul: 'Serap wireframe — ' + m.name + ' → domain ' + nm, baris: [], pesan: '' };
    kotak();

    var Vwf = volMesh(m), W = fn('wfInside') ? wfInside(m) : null;
    lap({ nama: '0. Wireframe', hasil: N(m.nt) + ' segitiga &middot; volume <b>' + N(Vwf) + '</b> m&sup3;',
          ket: W ? (W.open ? '<span class=warn>tidak tertutup rapat: ' + W.open + ' dari ' + W.ne + ' sisi terbuka</span> &mdash; uji titik-di-dalam pada wireframe bocor tidak bisa dipercaya, rapikan dulu di Leapfrog' : 'tertutup rapat') : '' });

    /* 1. domain */
    var d = null;
    GM.doms.forEach(function (x) { if (x.name.toLowerCase() === nm.toLowerCase()) d = x; });
    var baru = !d;
    if (!d) { d = gmAddDom(nm); }
    if (!d) { lap({ nama: '1. Domain', lewat: 1, hasil: 'gagal dibuat' }); return; }
    GM.act = d.id;
    lap({ nama: '1. Domain', hasil: baru ? 'dibuat: <b>' + E(d.name) + '</b>' : 'dipakai yang sudah ada: <b>' + E(d.name) + '</b>',
          ket: baru ? 'nama diambil dari nama berkas wireframe' : 'string impor lama di section yang sama akan diganti; string yang sudah Anda edit tidak disentuh' });

    /* 2. flag interval bor di dalam wireframe */
    var f0 = 0; try { f0 = Object.keys(GM.flags || {}).length; } catch (e) {}
    window.WF = window.WF || {};
    WF.mi = WFX.o.mi | 0; WF.dom = d.id; WF.sp = +WFX.o.sp || 0;
    try {
      gmWfFlag();
      var pesan = String(WF.msg || '').replace(/<[^>]+>/g, '');
      var R = fn('meRuns') ? meRuns(d.id) : {};
      var nH = Object.keys(R).length;
      lap({ nama: '2. Flag interval bor', hasil: nH ? '<b>' + N(nH) + '</b> hole menembus wireframe' : '<span class=warn>tidak ada</span>',
            lewat: !nH, ket: E(pesan) });
      if (!nH) {
        WFX.log.pesan = '<b>Tidak ada interval bor di dalam wireframe.</b> Biasanya berarti sistem koordinatnya berbeda ' +
          '(wireframe lokal vs collar UTM) atau wireframe-nya bukan untuk area ini. Periksa di 3D: wireframe harus ' +
          'bertumpuk dengan lubang bornya.';
        kotak(); return;
      }
    } catch (e) {
      lap({ nama: '2. Flag interval bor', lewat: 1, hasil: 'gagal', ket: E(e.message || e) });
      return;
    }

    /* 3. section tegak lurus strike wireframe */
    var S = strikeMesh(m), sp = Math.max(0.5, +WFX.o.sp || +(($('thick') || {}).value) || 10);
    var azL = (S.az + 90) % 180, r = azL * Math.PI / 180, ux = Math.sin(r), uy = Math.cos(r), L2 = S.panjang / 2;
    var ox = (window.offX || 0), oy = (window.offY || 0);
    var simpan = {};
    ['sMode', 'p1e', 'p1n', 'p2e', 'p2n', 'dipS', 'thick'].forEach(function (i) { var e = $(i); if (e) simpan[i] = e.value; });
    var ls = $('limSeg'); var simpanLs = ls ? ls.checked : null;
    if ($('sMode')) $('sMode').value = 'P';
    if ($('p1e')) $('p1e').value = (S.c[0] - ux * L2 + ox).toFixed(2);
    if ($('p1n')) $('p1n').value = (S.c[1] - uy * L2 + oy).toFixed(2);
    if ($('p2e')) $('p2e').value = (S.c[0] + ux * L2 + ox).toFixed(2);
    if ($('p2n')) $('p2n').value = (S.c[1] + uy * L2 + oy).toFixed(2);
    if ($('dipS')) $('dipS').value = 90;
    if ($('thick')) $('thick').value = sp;
    if (ls) ls.checked = false;
    try { if (fn('modeChanged')) modeChanged(); } catch (e) {}
    lap({ nama: '3. Section', hasil: 'strike wireframe <b>' + N(S.az, 0) + '&deg;</b>, section tegak lurus (' + N(azL, 0) + '&deg;)',
          ket: 'spasi ' + N(sp, 1) + ' m &mdash; makin rapat makin setia bentuknya; untuk vein tipis pakai serapat spasi bor' });

    /* 4. iris wireframe menjadi string HW / FW */
    var s0 = GM.str.length;
    try {
      WF.sp = sp;
      gmWfStrings(true);
      var ps = String(WF.msg || '').replace(/<[^>]+>/g, '');
      lap({ nama: '4. String kontrol HW / FW', hasil: '<b>' + N(GM.str.length - s0) + '</b> string baru (total ' + N(GM.str.length) + ')', ket: E(ps) });
    } catch (e) {
      lap({ nama: '4. String kontrol HW / FW', lewat: 1, hasil: 'gagal', ket: E(e.message || e) });
    }

    /* 5. solid RBF + kontrol mutu volume */
    setTimeout(function () {
      ['sMode', 'p1e', 'p1n', 'p2e', 'p2n', 'dipS', 'thick'].forEach(function (i) { var e = $(i); if (e && simpan[i] != null) e.value = simpan[i]; });
      if (ls && simpanLs != null) ls.checked = simpanLs;
      try { if (fn('modeChanged')) modeChanged(); } catch (e) {}
      var V2 = null;
      try { if (fn('imSync')) imSync(); var R2 = meGrpR(d); V2 = R2 && R2.st ? R2.st.vol : null; } catch (e) {}
      var sel = (Vwf && V2 != null) ? 100 * (V2 - Vwf) / Vwf : null;
      lap({ nama: '5. Solid GC-Ex (RBF)', hasil: V2 != null ? '<b>' + N(V2) + '</b> m&sup3;' : '<span class=warn>belum terbentuk</span>',
            lewat: V2 == null,
            ket: sel != null
              ? 'volume wireframe ' + N(Vwf) + ' m&sup3; &rarr; solid ' + N(V2) + ' m&sup3; &middot; selisih <b>' +
                (sel >= 0 ? '+' : '') + N(sel, 1) + '%</b>' +
                (Math.abs(sel) > 10 ? ' <span class=warn>&mdash; rapatkan spasi section lalu serap ulang</span>'
                                    : ' &mdash; dalam batas wajar untuk rekonstruksi')
              : 'periksa string HW / FW di penampang' });
      WFX.log.pesan = 'Domain <b>' + E(d.name) + '</b> sekarang domain GC-Ex biasa: string kontrolnya bisa ditarik, ' +
        'section bisa ditambah, dan solidnya <b>ikut berubah saat ada bor baru</b> &mdash; jalankan ' +
        '<b>Autorun Wireframe</b> sesudah flagging bor baru, string hasil edit tangan tidak akan ditimpa. ' +
        'Untuk estimasi, lanjutkan ke Geostatistik lalu simpan parameternya ke domain ini.' +
        (Math.abs(sel || 0) > 10 ? '<br><br><span class=warn>Selisih volume ' + N(sel, 1) + '% cukup besar.</span> ' +
          'Rekonstruksi memakai irisan tiap ' + N(sp, 1) + ' m; bagian wireframe yang lebih halus dari itu tidak terwakili. ' +
          'Rapatkan spasi section dan serap ulang ke domain yang sama.' : '');
      kotak();
      try { gmDirty(); } catch (e) {}
      try { if (window.PT && PT.render) PT.render(true); } catch (e) {}
    }, 400);
  };

  /* ---------- dialog: tiga isian ---------- */
  window.wfxSet = function (k, v) { WFX.o[k] = (k === 'sp' ? (+v || 0) : (k === 'mi' ? (v | 0) : v)); dlg(); };
  window.wfxDlg = function () { dlg(); };
  function dlg() {
    var d = $('wfxSetDlg');
    if (!d) { d = document.createElement('div'); d.id = 'wfxSetDlg'; d.className = 'bxdlg'; document.body.appendChild(d); }
    var M = models(), o = WFX.o, m = M[o.mi | 0];
    var auto = m ? String(m.name).replace(/\.[^.]+$/, '').replace(/[^A-Za-z0-9_-]+/g, '_').slice(0, 30) : '';
    var V = m ? volMesh(m) : null, W = m && fn('wfInside') ? wfInside(m) : null;
    d.innerHTML = '<div class=impBox style=width:min(660px,100%)><div class=impHead><div class=impBrand><div><b>Serap wireframe → domain</b>' +
      '<small>Wireframe implicit dari Leapfrog (atau Surpac) menjadi domain GC-Ex yang bisa diedit dan ikut diperbarui saat ada bor baru.</small>' +
      '</div></div><button class="ib ghost" onclick="wfxSetClose()">Tutup</button></div><div class=impBody>' +
      (!M.length
        ? '<div class=box>Belum ada wireframe. Import dulu di menu <b>Data Referensi</b> (<code>.msh</code>, <code>.obj</code>, <code>.dxf</code>, atau <code>.dtm</code> + <code>.str</code> Surpac), lalu kembali ke sini.</div>'
        : '<div><label>Wireframe</label><select onchange="wfxSet(\'mi\',this.value)">' +
          M.map(function (x, i) { return '<option value=' + i + (i === (o.mi | 0) ? ' selected' : '') + '>' + E(x.name) + '</option>'; }).join('') +
          '</select><div class=hint>' + (m ? N(m.nt) + ' segitiga &middot; volume ' + N(V) + ' m&sup3; &middot; ' +
            (W && W.open ? '<span class=warn>' + W.open + ' sisi terbuka (tidak tertutup rapat)</span>' : 'tertutup rapat') : '') + '</div></div>' +
          '<div class="g2 f"><div><label>Spasi section (m)</label><input type=number step=any min=0 value="' + (o.sp || '') + '" placeholder="= tebal slab" onchange="wfxSet(\'sp\',this.value)">' +
          '<div class=hint>Jarak irisan. Makin rapat makin setia bentuknya &mdash; untuk vein tipis pakai serapat spasi bor.</div></div>' +
          '<div><label>Nama domain</label><input value="' + E(o.nama || '') + '" placeholder="' + E(auto) + '" onchange="wfxSet(\'nama\',this.value)">' +
          '<div class=hint>Kosong = ikut nama berkas. Nama yang sudah ada akan dipakai ulang (serap ulang ke domain yang sama).</div></div></div>' +
          '<div class=box><b>Yang akan dikerjakan:</b> buat domain &rarr; flag interval bor di dalam wireframe &rarr; hitung strike &rarr; pasang section tegak lurus strike &rarr; iris jadi string HW / FW &rarr; bangun solid RBF &rarr; bandingkan volumenya dengan volume wireframe.</div>') +
      '</div><div class=impFoot><div class=hint></div>' +
      (M.length ? '<button class=ib onclick="wfxSetClose();wfSerap()">Serap sekarang &rarr;</button>' : '') +
      '</div></div>';
    d.style.display = 'flex';
  }
  window.wfxSetClose = function () { var d = $('wfxSetDlg'); if (d) d.style.display = 'none'; };

  /* ---------- node Project Tree ---------- */
  window.wfxTree = function () {
    if (!window.GM || !fn('gmTops')) return [];
    var M = models(), D = gmTops();
    var terkunci = D.filter(function (d) { return d.wfx; });
    var kids = D.map(function (d) {
      var nm = d.wfx, ada = nm ? !!byName(nm) : false;
      return {
        id: 'wfx.' + d.id, t: d.name, ic: 'dom',
        b: nm ? (ada ? 'eksak: ' + nm : 'eksak: ' + nm + ' (hilang)') : 'solid GC-Ex',
        dim: !nm,
        hint: nm ? (ada ? 'Batas EKSAK dari wireframe — tidak bisa diedit dan tidak berubah saat ada bor baru'
                        : 'Wireframe belum diimport ulang di Data Referensi — sementara kembali memakai solid RBF')
                 : 'Memakai solid RBF dari string kontrol — bisa diedit, ikut berubah saat ada bor baru',
        menu: function () {
          var L = [];
          if (nm) L.push({ t: 'Lepaskan dari wireframe (kembali ke solid RBF)', fn: function () { wfxLepas(d.id); } });
          M.forEach(function (x) {
            L.push({ t: (x.name === nm ? '✓ ' : '') + 'Pakai EKSAK: ' + x.name, dis: x.name === nm, fn: function () { wfxPakai(d.id, x.name); } });
          });
          if (!M.length) L.push({ t: 'Belum ada wireframe di Data Referensi', dis: 1 });
          return L;
        }
      };
    });
    return [{
      id: 'wfx', t: 'Wireframe luar (Leapfrog / Surpac)', ic: 'ref', fold: 1, tab: 'GM',
      b: M.length ? (M.length + ' wireframe' + (terkunci.length ? ' · ' + terkunci.length + ' domain eksak' : '')) : 'belum ada',
      dim: !M.length,
      hint: 'Serap menjadi domain yang bisa diedit (Mode B), atau pakai eksak sebagai batas estimasi untuk audit (Mode A)',
      menu: function () {
        return [
          { h: 'Mode B — diserap (bisa diedit, ikut bor baru)' },
          { t: 'Serap wireframe → domain…', dis: !M.length, fn: function () { wfxDlg(); } },
          { t: 'Lihat laporan penyerapan terakhir', dis: !WFX.log, fn: function () { wfxLihat(); } },
          { sep: 1 },
          { h: 'Mode A — eksak (untuk audit)' },
          { t: 'Pilih di anak node: tiap domain bisa dikunci ke satu wireframe', dis: 1 },
          { sep: 1 },
          { t: 'Import wireframe… (Data Referensi)', fn: function () { try { uiTab('Ref'); } catch (e) { try { uiTab('SP'); } catch (e2) {} } } }
        ];
      },
      kids: kids
    }];
  };

  /* pengaturan dialog ikut tersimpan di berkas proyek (d.wfx sendiri ikut lewat gmPack) */
  if (window.SA && SA.collectWork) {
    var _c = SA.collectWork;
    SA.collectWork = function () { var w = _c.apply(this, arguments); try { w.wfx = { o: WFX.o }; } catch (e) {} return w; };
    var _a = SA.applyWork;
    SA.applyWork = function (W) {
      try { if (W && W.wfx && W.wfx.o) Object.keys(W.wfx.o).forEach(function (k) { WFX.o[k] = W.wfx.o[k]; }); } catch (e) {}
      WFX.c = {};
      return _a.apply(this, arguments);
    };
  }
})();
