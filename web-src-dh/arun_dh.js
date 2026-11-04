/* ================= AUTORUN — menjahit langkah yang sudah ada menjadi satu perintah =================
   Tidak ada algoritme baru di sini. Modul ini hanya MEMANGGIL fungsi yang sudah dipakai manual,
   mengulanginya per domain / per lapisan, lalu melaporkan hasilnya. Semua pengaman yang sudah ada
   tetap berlaku — terutama:
     - gmDraft(): string yang sudah DIEDIT TANGAN tidak pernah ditimpa (s.auto === false → dilewati),
       section dengan < 2 kontak dilewati. Jadi "dari nol" dan "melanjutkan" adalah operasi yang sama:
       keputusannya diambil per section, bukan per perintah.
     - Model Estimation: parameter per domain yang sudah disimpan dipakai apa adanya. Autorun TIDAK
       pernah melakukan fitting variogram sendiri dan tidak pernah mengganti parameter yang sudah
       disetujui. Domain tanpa parameter DILEWATI dengan alasannya tertulis, bukan dikarang.

   Dua perintah per tipe deposit:
     vein    : arWf()  — string kontrol semua section → solid (Tahap 2)
               arEst() — estimasi update + waste + refresh laporan (Tahap 1)
     laterit : arLap() — usulan lapisan dari log geologi (bila belum ada) → permukaan atap/lantai
               arEstLat() — estimasi unfold per lapisan + waste laterit

   Laporan tiap autorun memuat perbandingan SEBELUM vs SESUDAH (volume solid, jumlah blok, kadar
   rata-rata, tonase). Itu yang membuat hasilnya bisa diperiksa, bukan dipercaya begitu saja.      */
(function () {
  if (window.AR) return;
  var AR = window.AR = {
    busy: false, tahap: '', log: null,
    o: { sp: 10, ulang: false, waste: true, rep: true, minKontak: 2, minHole: 3 }
  };

  function E(s) { return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; }); }
  function N(v, d) { return (v == null || !isFinite(v)) ? '-' : (+v).toLocaleString('id-ID', { maximumFractionDigits: d == null ? 0 : d }); }
  function $(i) { return document.getElementById(i); }
  function fn(n) { return typeof window[n] === 'function'; }

  /* ---------- tunggu job selesai (meRun / wsRun / slRun semuanya memakai pola X.job) ---------- */
  function tunggu(ada, cb, batas) {
    var t0 = Date.now(), lim = batas || 1800000;
    (function p() {
      var masih;
      try { masih = ada(); } catch (e) { masih = false; }
      if (!masih) return cb(null);
      if (Date.now() - t0 > lim) return cb('melewati batas waktu');
      setTimeout(p, 250);
    })();
  }

  /* ================= LAPORAN ================= */
  function mulai(tahap, judul) {
    AR.busy = true; AR.tahap = tahap;
    AR.log = { judul: judul, t0: Date.now(), baris: [], pesan: '', selesai: false };
    kotak();
  }
  function baris(o) { AR.log.baris.push(o); kotak(); }
  function usai(pesan) {
    AR.log.pesan = pesan || '';
    AR.log.ms = Date.now() - AR.log.t0;
    AR.log.selesai = true; AR.busy = false;
    kotak();
    try { if (window.PT && PT.render) PT.render(true); } catch (e) {}
  }

  /* dialog laporan (memakai gaya .bxdlg yang sama dengan AOI / sub-blocking / filter) */
  function kotak() {
    var d = $('arDlg');
    if (!d) { d = document.createElement('div'); d.id = 'arDlg'; d.className = 'bxdlg'; document.body.appendChild(d); }
    var L = AR.log || { judul: '', baris: [], selesai: true };
    var th = '<tr><th>Domain / lapisan</th><th>Hasil</th><th>Sebelum &rarr; sesudah</th><th>Catatan</th></tr>';
    var rows = L.baris.map(function (b) {
      return '<tr' + (b.lewat ? ' style="opacity:.7"' : '') + '><td><b>' + E(b.nama) + '</b></td><td>' +
        (b.lewat ? '<span class=warn>dilewati</span>' : (b.hasil || '')) + '</td><td>' + (b.banding || '') +
        '</td><td><small>' + (b.ket || '') + '</small></td></tr>';
    }).join('') || '<tr><td colspan=4 class=hint>Belum ada hasil.</td></tr>';
    d.innerHTML = '<div class=impBox style=width:min(900px,100%)><div class=impHead><div class=impBrand><div><b>' + E(L.judul) + '</b>' +
      '<small>Autorun hanya mengulang langkah yang sudah ada. Yang dilewati beserta alasannya ikut dicatat di bawah &mdash; tidak ada yang diganti diam-diam.</small>' +
      '</div></div><button class="ib ghost" onclick="arClose()">Tutup</button></div>' +
      '<div class=impBody><table class=pltb>' + th + rows + '</table>' +
      (L.selesai ? '<div class=hint>' + (L.pesan || '') + (L.ms ? ' &middot; ' + (L.ms / 1000).toFixed(1) + ' detik' : '') + '</div>'
                 : '<div class=hint>Sedang berjalan&hellip; jendela ini boleh ditutup, prosesnya tetap lanjut.</div>') +
      '</div><div class=impFoot><div id=arMsg class=hint></div>' +
      (L.selesai ? '<button class=ib onclick="arCsv()">&#8681; Laporan CSV</button>' : '') +
      '<button class=ib onclick="arClose()">Selesai</button></div></div>';
    d.style.display = 'flex';
  }
  window.arClose = function () { var d = $('arDlg'); if (d) d.style.display = 'none'; };
  window.arLihat = function () { if (AR.log) kotak(); else alert('Belum ada autorun yang dijalankan di sesi ini.'); };
  window.arCsv = function () {
    var L = AR.log; if (!L) return;
    var q = function (v) { v = String(v == null ? '' : v).replace(/<[^>]+>/g, '').replace(/&middot;/g, '·').replace(/&rarr;/g, '->'); return /[",\n]/.test(v) ? '"' + v.replace(/"/g, '""') + '"' : v; };
    var t = ['Autorun,' + q(L.judul)].concat(['Nama,Hasil,Sebelum-sesudah,Catatan'],
      L.baris.map(function (b) { return [b.nama, b.lewat ? 'DILEWATI' : b.hasil, b.banding, b.ket].map(q).join(','); })).join('\r\n');
    var a = document.createElement('a');
    a.href = URL.createObjectURL(new Blob([t], { type: 'text/csv' }));
    a.download = 'Autorun_' + (AR.tahap || 'laporan') + '.csv';
    document.body.appendChild(a); a.click(); setTimeout(function () { a.remove(); }, 500);
  };

  /* ================= TAHAP 2a — AUTORUN WIREFRAME (VEIN) ================= */

  /* Strike domain dari titik tengah kontak HW/FW (sumbu utama di bidang datar). Dipakai untuk
     menempatkan garis section TEGAK LURUS strike — itulah orientasi yang benar untuk menarik
     string kontrol, dan yang biasanya diatur manual sebelum menekan "tarik otomatis". */
  function strikeDom(d) {
    if (!fn('gmContacts')) return null;
    var C = gmContacts(d.id);
    if (!C || !C.L || C.L.length < 2) return null;
    var P = C.L.map(function (c) { return [(c.hw.x + c.fw.x) / 2, (c.hw.y + c.fw.y) / 2]; });
    var m = [0, 0];
    P.forEach(function (q) { m[0] += q[0]; m[1] += q[1]; });
    m = [m[0] / P.length, m[1] / P.length];
    var sxx = 0, syy = 0, sxy = 0;
    P.forEach(function (q) { var dx = q[0] - m[0], dy = q[1] - m[1]; sxx += dx * dx; syy += dy * dy; sxy += dx * dy; });
    var ang = 0.5 * Math.atan2(2 * sxy, sxx - syy), ux = Math.cos(ang), uy = Math.sin(ang);
    /* azimuth = sudut dari utara (y) searah jarum jam */
    var az = Math.atan2(ux, uy) * 180 / Math.PI;
    az = ((az % 180) + 180) % 180;
    /* bentang data TEGAK LURUS strike -> panjang garis section */
    var vx = Math.cos(ang + Math.PI / 2), vy = Math.sin(ang + Math.PI / 2), lo = 1e18, hi = -1e18;
    P.forEach(function (q) { var s = (q[0] - m[0]) * vx + (q[1] - m[1]) * vy; lo = Math.min(lo, s); hi = Math.max(hi, s); });
    return { az: az, c: m, n: P.length, panjang: Math.max(50, (hi - lo) * 1.4) };
  }
  window.arStrike = strikeDom;

  /* simpan & pulihkan seluruh pengaturan Sayatan yang disentuh autorun */
  function simpanSec() {
    var k = ['sMode', 'p1e', 'p1n', 'p2e', 'p2n', 'dipS', 'thick', 'pos'], o = { v: {} };
    k.forEach(function (i) { var e = $(i); if (e) o.v[i] = e.value; });
    var ls = $('limSeg'); if (ls) o.limSeg = ls.checked;
    o.act = window.GM ? GM.act : null;
    return o;
  }
  function pulihSec(o) {
    Object.keys(o.v).forEach(function (i) { var e = $(i); if (e) e.value = o.v[i]; });
    var ls = $('limSeg'); if (ls && o.limSeg != null) ls.checked = o.limSeg;
    if (window.GM && o.act != null) GM.act = o.act;
    try { if (fn('modeChanged')) modeChanged(); } catch (e) {}
    try { if (fn('gmPanel')) gmPanel(); } catch (e) {}
  }

  function volSolid(d) {
    try {
      if (fn('imSync')) imSync();
      var R = fn('meGrpR') ? meGrpR(d) : null;
      return (R && R.st && isFinite(R.st.vol)) ? R.st.vol : null;
    } catch (e) { return null; }
  }

  window.arWfDoms = function () {
    if (!window.GM || !fn('gmTops')) return [];
    return gmTops();
  };

  window.arWf = function () {
    if (AR.busy) { alert('Autorun lain sedang berjalan.'); return; }
    var D = arWfDoms().filter(function (d) { return AR.sel('wf', d.id); });
    if (!D.length) { alert('Centang dulu domain yang ikut autorun (node Autorun Wireframe).'); return; }
    if (AR.o.ulang && !confirm('Mode "bangun ulang semua" akan MENIMPA string yang sudah Anda edit tangan di ' +
        D.length + ' domain. Lanjutkan?')) return;

    mulai('wireframe', 'Autorun Wireframe — ' + D.length + ' domain');
    var simpan = simpanSec(), sp = Math.max(0.5, +AR.o.sp || 10), i = 0;

    (function next() {
      if (i >= D.length) {
        pulihSec(simpan);
        try { if (fn('gmDirty')) gmDirty(); } catch (e) {}
        var n = AR.log.baris.filter(function (b) { return !b.lewat; }).length;
        usai(n + ' dari ' + D.length + ' domain diperbarui. Solid dibangun ulang otomatis; periksa kolom ' +
             '<b>Sebelum &rarr; sesudah</b> &mdash; lonjakan volume yang tidak wajar biasanya berarti string ' +
             'otomatis di section bertepi data perlu dirapikan tangan.');
        return;
      }
      var d = D[i++], S = strikeDom(d);
      if (!S) {
        baris({ nama: d.name, lewat: 1, ket: 'kontak flag kurang dari 2 &mdash; flagging domain ini belum cukup untuk menarik string' });
        return setTimeout(next, 10);
      }
      var v0 = volSolid(d);

      /* section TEGAK LURUS strike: garis manual (mode P) lewat centroid */
      var azL = (S.az + 90) % 180, r = azL * Math.PI / 180, ux = Math.sin(r), uy = Math.cos(r), L2 = S.panjang / 2;
      var ox = (window.offX || 0), oy = (window.offY || 0);
      if ($('sMode')) $('sMode').value = 'P';
      if ($('p1e')) $('p1e').value = (S.c[0] - ux * L2 + ox).toFixed(2);
      if ($('p1n')) $('p1n').value = (S.c[1] - uy * L2 + oy).toFixed(2);
      if ($('p2e')) $('p2e').value = (S.c[0] + ux * L2 + ox).toFixed(2);
      if ($('p2n')) $('p2n').value = (S.c[1] + uy * L2 + oy).toFixed(2);
      if ($('dipS')) $('dipS').value = 90;
      if ($('thick')) $('thick').value = sp;
      var ls = $('limSeg'); if (ls) ls.checked = false;   /* jangan batasi di ujung garis */
      try { if (fn('modeChanged')) modeChanged(); } catch (e) {}

      GM.act = d.id;
      if (AR.o.ulang) {
        GM.str.forEach(function (s) { if (s.dom === d.id) s.auto = true; });   /* izinkan ditimpa */
      }
      try {
        if (window.GM) GM.lastDraft = null;
        gmDraft(true);
      } catch (e) {
        baris({ nama: d.name, lewat: 1, ket: 'gagal: ' + E(e.message || e) });
        return setTimeout(next, 10);
      }
      var q = (window.GM && GM.lastDraft) || null;
      /* solid dibangun ulang otomatis (imAuto); beri waktu lalu ukur volumenya */
      setTimeout(function () {
        var v1 = volSolid(d);
        baris({
          nama: d.name,
          hasil: q ? ('<b>' + q.made + '</b> string baru, ' + q.rep + ' diperbarui' + (q.skip ? ', <b>' + q.skip + '</b> dilewati' : '')) : 'selesai',
          banding: (v0 != null || v1 != null)
            ? (N(v0) + ' &rarr; <b>' + N(v1) + '</b> m&sup3;' +
               (v0 > 0 && v1 != null ? '<br><small>' + (v1 >= v0 ? '+' : '') + N(100 * (v1 - v0) / v0, 1) + '%</small>' : ''))
            : '<small>solid belum terbentuk</small>',
          ket: 'strike ' + N(S.az, 0) + '&deg;, section tegak lurus (' + N(azL, 0) + '&deg;) tiap ' + N(sp, 1) + ' m' +
               (q ? ' &middot; ' + q.secN + ' section dengan &ge; 2 kontak' : '') +
               (q && q.skip ? ' &middot; yang dilewati = string hasil edit tangan, tidak ditimpa' : '')
        });
        setTimeout(next, 10);
      }, 350);
    })();
  };

  /* ================= TAHAP 2b — AUTORUN LAPISAN (LATERIT) ================= */

  /* Usulan lapisan dari log geologi: tiap kode diurutkan menurut kedalaman tengah rata-ratanya.
     Hanya dipakai bila BELUM ada lapisan berkode — pekerjaan yang sudah ada tidak pernah dibuang. */
  function usulLapisan(ci) {
    var K = {}, V = (fn('visHolesK') ? visHolesK() : (fn('visHoles') ? visHoles() : []));
    V.forEach(function (id) {
      var h = window.holeData && holeData[id]; if (!h) return;
      (geoIntervals(ci, id) || []).forEach(function (iv) {
        var f = iv[0], t = Math.min(iv[1], h.maxD), c = iv[2];
        if (c == null || c < 0 || !(t > f)) return;
        var e = K[c] || (K[c] = { code: +c, n: 0, hole: {}, sd: 0, len: 0 });
        e.n++; e.hole[id] = 1; e.sd += (f + t) / 2 * (t - f); e.len += (t - f);
      });
    });
    return Object.keys(K).map(function (c) {
      var e = K[c];
      return { code: e.code, nama: (fn('geoName') ? geoName(ci, e.code) : String(e.code)),
               nHole: Object.keys(e.hole).length, dep: e.len ? e.sd / e.len : 0, len: e.len, n: e.n };
    }).sort(function (a, b) { return a.dep - b.dep; });
  }
  window.arUsulLapisan = usulLapisan;

  function catLat() {
    if (window.SL && SL.ci >= 0) return SL.ci;
    var C = fn('slCats') ? slCats() : [];
    return C.length ? C[0] : -1;
  }

  window.arLap = function () {
    if (AR.busy) { alert('Autorun lain sedang berjalan.'); return; }
    if (!window.SL) { alert('Menu Stratified-Laterite belum siap.'); return; }
    var ci = catLat();
    if (ci < 0) { alert('Belum ada atribut geologi / kategori assay yang bisa dipakai sebagai kode lapisan.'); return; }

    mulai('lapisan', 'Autorun Lapisan — ' + (fn('geoName') ? (window.CAT[ci] && CAT[ci].name) : 'kode geologi'));
    var adaKode = (SL.L || []).some(function (l) { return (l.codes || []).length; });
    var U = usulLapisan(ci), buat = 0, lewat = [];

    if (!adaKode) {
      SL.ci = ci;
      if (AR.o.ulang || !(SL.L || []).length) SL.L = [];
      U.forEach(function (u) {
        if (u.nHole < Math.max(1, +AR.o.minHole || 3)) { lewat.push(u.nama + ' (' + u.nHole + ' hole)'); return; }
        var l = slNewL({ name: u.nama, codes: [u.code] }, SL.L.length);
        SL.L.push(l); buat++;
        baris({ nama: u.nama, hasil: 'lapisan ke-' + SL.L.length + ' dibuat',
                banding: N(u.nHole) + ' hole &middot; ' + N(u.len, 1) + ' m',
                ket: 'kedalaman tengah rata-rata ' + N(u.dep, 1) + ' m &mdash; urutan lapisan mengikuti angka ini' });
      });
      if (lewat.length) baris({ nama: 'Kode terlalu jarang', lewat: 1, ket: 'tidak dijadikan lapisan: ' + E(lewat.join(', ')) });
    } else {
      (SL.L || []).forEach(function (l) {
        baris({ nama: l.name, hasil: 'dipakai apa adanya',
                banding: (l.codes || []).length + ' kode',
                ket: 'lapisan ini sudah Anda tetapkan &mdash; autorun tidak mengubah pemetaan kode' });
      });
    }

    /* bangun permukaan atap / lantai */
    var R = null, err = '';
    try { if (fn('slDirty')) slDirty(); R = fn('slEnsure') ? slEnsure() : null; err = SL.err || ''; } catch (e) { err = e.message || String(e); }
    if (R) {
      baris({ nama: 'Permukaan atap / lantai', hasil: '<b>' + N(R.nT || (SL.L || []).length) + '</b> permukaan dibangun',
              banding: N(R.nx) + ' &times; ' + N(R.ny) + ' sel' + (R.cell ? ' @ ' + N(R.cell, 1) + ' m' : ''),
              ket: 'siap dipakai estimasi unfold per lapisan (Autorun Estimasi Lapisan)' });
    } else {
      baris({ nama: 'Permukaan atap / lantai', lewat: 1, ket: 'gagal: ' + E(err || 'tidak diketahui') });
    }
    usai(adaKode ? 'Pemetaan kode yang sudah ada dipertahankan; hanya permukaannya dibangun ulang.'
                 : buat + ' lapisan diusulkan dari log geologi, diurutkan dari yang paling atas. ' +
                   '<b>Periksa dan perbaiki pemetaan kodenya</b> di ① Lapisan & kode log sebelum mengestimasi &mdash; ' +
                   'usulan ini hanya berdasarkan kedalaman, bukan pengertian geologi.');
  };

  /* ================= TAHAP 1a — AUTORUN ESTIMATION UPDATE (VEIN) ================= */

  window.arEstSiap = function () {
    var out = [];
    (fn('gmTops') ? gmTops() : []).forEach(function (d) {
      var on = fn('imPar') ? imPar(d).on : false;
      var R = fn('meGrpR') ? meGrpR(d) : null;
      var P = fn('meParOf') ? meParOf(d) : null;
      var sebab = !on ? 'solid belum dinyalakan (Geomodeller Vein ③)'
                : !(R && R.mesh) ? 'solid gagal / belum terbentuk'
                : !P ? 'belum ada parameter tersimpan — di Geostatistik: fitting model, lalu "Simpan ke domain"'
                : '';
      out.push({ d: d, siap: !sebab, sebab: sebab, P: P, vol: R && R.st ? R.st.vol : null });
    });
    return out;
  };

  function runTerakhir(domId) {
    var S = window.ME && ME.store, last = null;
    if (!S || !S.runs) return null;
    S.runs.forEach(function (q) { if (q.domId === domId) last = q; });
    return last;
  }

  window.arEst = function () {
    if (AR.busy) { alert('Autorun lain sedang berjalan.'); return; }
    if (!(window.BX && BX.m)) { alert('Belum ada block model GC. Import lewat menu Block Model, atau buat kerangka blok (AOI) dulu.'); return; }
    var S = arEstSiap().filter(function (x) { return AR.sel('est', x.d.id); });
    if (!S.length) { alert('Centang dulu domain yang ikut autorun (node Autorun Estimation).'); return; }
    var siap = S.filter(function (x) { return x.siap; });
    if (!siap.length) {
      mulai('estimasi', 'Autorun Estimation — tidak ada domain yang siap');
      S.forEach(function (x) { baris({ nama: x.d.name, lewat: 1, ket: x.sebab }); });
      usai('Tidak ada yang dijalankan. Autorun tidak pernah mengarang parameter: perbaiki dulu sebab di atas.');
      return;
    }

    mulai('estimasi', 'Autorun Estimation (update) — ' + siap.length + ' domain');
    var sebelum = {};
    S.forEach(function (x) {
      if (!x.siap) { baris({ nama: x.d.name, lewat: 1, ket: x.sebab }); return; }
      sebelum[x.d.id] = runTerakhir(x.d.id);
      ME.sel[x.d.id] = true;
    });
    /* domain yang TIDAK ikut dipastikan mati supaya meRun tidak menyentuhnya */
    (fn('gmTops') ? gmTops() : []).forEach(function (d) {
      if (!siap.some(function (x) { return x.d.id === d.id; })) ME.sel[d.id] = false;
    });

    try { meRun(); } catch (e) { usai('<span class=warn>gagal memulai estimasi: ' + E(e.message || e) + '</span>'); return; }

    tunggu(function () { return window.ME && ME.job; }, function (err) {
      siap.forEach(function (x) {
        var a = sebelum[x.d.id], b = runTerakhir(x.d.id), va = a && a.v || {}, vb = b && b.v || {};
        if (!b || (a && b.id === a.id)) { baris({ nama: x.d.name, lewat: 1, ket: 'tidak ada blok yang perlu dikoreksi &mdash; tidak ada bor baru yang mempengaruhi domain ini' }); return; }
        baris({
          nama: x.d.name,
          hasil: '<b>' + N(b.nEst) + '</b> blok diestimasi' + (b.nAddC ? ' (+' + N(b.nAddC) + ' tambahan)' : '') +
                 '<br><small>' + N(b.nComp) + ' komposit &middot; run #' + b.id + '</small>',
          banding: 'kadar ' + (va.mean != null ? N(va.mean, 3) : '-') + ' &rarr; <b>' + (vb.mean != null ? N(vb.mean, 3) : '-') + '</b>' +
                   '<br><small>tonase ' + N(va.ton) + ' &rarr; ' + N(vb.ton) + ' t</small>',
          ket: 'parameter ' + E(b.par || (x.P && x.P.el) || '-') + (b.parChg ? ' <span class=warn>(parameter berubah sejak run lalu)</span>' : ' (parameter tersimpan, tidak diubah autorun)')
        });
      });
      if (err) { usai('<span class=warn>estimasi ' + err + '</span>'); return; }
      lanjutWaste();
    });

    function lanjutWaste() {
      if (!AR.o.waste || !fn('wsRun')) return lanjutLaporan();
      var c = fn('wsCheck') ? wsCheck() : null;
      if (c && c.err) { baris({ nama: 'Estimasi waste', lewat: 1, ket: E(c.err) }); return lanjutLaporan(); }
      try { wsRun(); } catch (e) { baris({ nama: 'Estimasi waste', lewat: 1, ket: 'gagal: ' + E(e.message || e) }); return lanjutLaporan(); }
      tunggu(function () { return window.WS && WS.job; }, function (err) {
        baris({ nama: 'Estimasi waste', hasil: err ? '<span class=warn>' + err + '</span>' : 'selesai',
                ket: (window.WS && WS.msg ? String(WS.msg).replace(/<[^>]+>/g, '') : '') +
                     ' &middot; ditandai est_type = 3, tidak ikut pelaporan sumber daya' });
        lanjutLaporan();
      });
    }
    function lanjutLaporan() {
      if (AR.o.rep && fn('rpRun')) { try { rpRun(); baris({ nama: 'Reporting BM', hasil: 'laporan disegarkan', ket: 'grade-tonase memakai hasil run terbaru' }); } catch (e) {} }
      usai('Selesai. Parameter variogram <b>tidak</b> diubah: autorun memakai yang sudah Anda simpan per domain. ' +
           'Bandingkan kolom kadar dan tonase sebelum &rarr; sesudah; bila ada yang berubah jauh tanpa penambahan bor yang sepadan, ' +
           'telusuri run itu di menu Model Estimation &#9315; (riwayat run bisa dibatalkan).');
    }
  };

  /* ================= TAHAP 1b — AUTORUN ESTIMASI LAPISAN (LATERIT) ================= */

  window.arEstLat = function () {
    if (AR.busy) { alert('Autorun lain sedang berjalan.'); return; }
    if (!window.SL) { alert('Menu Stratified-Laterite belum siap.'); return; }
    if (!(window.BX && BX.m)) { alert('Belum ada block model GC. Import lewat menu Block Model, atau buat kerangka blok (AOI) dulu.'); return; }
    var L = SL.L || [];
    if (!L.length) { alert('Belum ada lapisan. Jalankan Autorun Lapisan dulu.'); return; }

    mulai('estimasi-lapisan', 'Autorun Estimasi Lapisan — ' + L.length + ' lapisan');
    var R = null;
    try { R = fn('slEnsure') ? slEnsure() : null; } catch (e) {}
    if (!R) { usai('<span class=warn>permukaan lapisan belum terbentuk: ' + E(SL.err || '-') + '</span>'); return; }

    var ikut = 0;
    L.forEach(function (l) {
      var e = l.est || {};
      if (!(l.codes || []).length) { baris({ nama: l.name, lewat: 1, ket: 'belum ada kode log yang dipetakan ke lapisan ini' }); return; }
      if (e.on === false) { baris({ nama: l.name, lewat: 1, ket: 'estimasi lapisan ini dimatikan di ③' }); return; }
      ikut++;
      baris({ nama: l.name, hasil: 'ikut run', banding: (l.codes || []).length + ' kode',
              ket: 'metode ' + E(e.met || 'ok') + ', ruang ' + E(e.mode === '3d' ? '3D' : 'unfold ' + (e.unf || 'prop')) +
                   ' &middot; parameter tersimpan per lapisan, tidak diubah autorun' });
    });
    if (!ikut) { usai('Tidak ada lapisan yang siap diestimasi.'); return; }

    try { slRun(); } catch (e) { usai('<span class=warn>gagal memulai: ' + E(e.message || e) + '</span>'); return; }
    tunggu(function () { return window.SL && SL.job; }, function (err) {
      baris({ nama: 'Estimasi unfold per lapisan', hasil: err ? '<span class=warn>' + err + '</span>' : 'selesai',
              ket: 'hasil per lapisan ada di ④ Laporan WMT / DMT' });
      if (!AR.o.waste || !fn('wlRun')) return usai('Selesai.');
      var c = fn('wlCheck') ? wlCheck() : null;
      if (c && c.err) { baris({ nama: 'Estimasi waste laterit', lewat: 1, ket: E(c.err) }); return usai('Selesai.'); }
      try { wlRun(); } catch (e) { baris({ nama: 'Estimasi waste laterit', lewat: 1, ket: 'gagal: ' + E(e.message || e) }); return usai('Selesai.'); }
      tunggu(function () { return window.WL && WL.job; }, function (e2) {
        baris({ nama: 'Estimasi waste laterit', hasil: e2 ? '<span class=warn>' + e2 + '</span>' : 'selesai',
                ket: (window.WL && WL.msg ? String(WL.msg).replace(/<[^>]+>/g, '') : '') +
                     ' &middot; zona bawah / atas memakai ruang unfold masing-masing' });
        usai('Selesai. Blok waste ditandai est_type = 3 dan tidak ikut pelaporan sumber daya.');
      });
    });
  };

  /* ================= PILIHAN & NODE PROJECT TREE ================= */

  AR.sel = function (grup, id) {
    AR.pil = AR.pil || {};
    var k = grup + ':' + id;
    return AR.pil[k] !== false;
  };
  window.arSel = function (grup, id, v) { AR.pil = AR.pil || {}; AR.pil[grup + ':' + id] = !!v; try { if (window.PT && PT.render) PT.render(true); } catch (e) {} };
  window.arSet = function (k, v) {
    AR.o[k] = (k === 'sp' || k === 'minHole' || k === 'minKontak') ? (+v || AR.o[k]) : !!v;
    if (window.SA && SA.dirty) SA.dirty();
    dlgAtur(); try { if (window.PT && PT.render) PT.render(true); } catch (e) {}
  };

  window.arAtur = function () { dlgAtur(); };
  function dlgAtur() {
    var d = $('arSetDlg');
    if (!d) { d = document.createElement('div'); d.id = 'arSetDlg'; d.className = 'bxdlg'; document.body.appendChild(d); }
    var o = AR.o;
    d.innerHTML = '<div class=impBox style=width:min(620px,100%)><div class=impHead><div class=impBrand><div><b>Pengaturan autorun</b>' +
      '<small>Hanya hal yang memang perlu diputuskan. Sisanya memakai parameter yang sudah tersimpan per domain / lapisan.</small>' +
      '</div></div><button class="ib ghost" onclick="arSetClose()">Tutup</button></div><div class=impBody>' +
      '<div class=imsec>Autorun Wireframe (vein)</div>' +
      '<div class="g2 f"><div><label>Spasi section (m)</label><input type=number step=any value="' + o.sp + '" onchange="arSet(\'sp\',this.value)">' +
      '<div class=hint>Jarak antar penampang saat string ditarik otomatis. Lazimnya seperempat sampai separuh spasi bor.</div></div>' +
      '<div><label>Minimal hole per kode (laterit)</label><input type=number step=1 value="' + o.minHole + '" onchange="arSet(\'minHole\',this.value)">' +
      '<div class=hint>Kode log yang ditembus lebih sedikit dari ini tidak diusulkan sebagai lapisan.</div></div></div>' +
      '<label class=sw><input type=checkbox ' + (o.ulang ? 'checked' : '') + ' onchange="arSet(\'ulang\',this.checked)">' +
      'Bangun ulang semua, termasuk string yang sudah diedit tangan</label>' +
      '<div class=hint style="margin-top:-4px">Bawaannya <b>mati</b>: string hasil edit tangan dilewati dan dilaporkan. Nyalakan hanya bila interpretasi lama memang mau dibuang (akan ada konfirmasi).</div>' +
      '<div class=imsec>Autorun Estimation</div>' +
      '<label class=sw><input type=checkbox ' + (o.waste ? 'checked' : '') + ' onchange="arSet(\'waste\',this.checked)">Lanjut ke estimasi waste sesudah domain selesai</label>' +
      '<label class=sw><input type=checkbox ' + (o.rep ? 'checked' : '') + ' onchange="arSet(\'rep\',this.checked)">Segarkan Reporting BM sesudahnya</label>' +
      '<div class=box>Autorun <b>tidak pernah</b> melakukan fitting variogram, tidak mengganti parameter yang sudah disimpan, ' +
      'dan tidak menyentuh domain yang belum punya parameter &mdash; domain seperti itu dilewati dengan alasannya tertulis di laporan.</div>' +
      '</div><div class=impFoot><div class=hint></div><button class=ib onclick="arSetClose()">Selesai</button></div></div>';
    d.style.display = 'flex';
  }
  window.arSetClose = function () { var d = $('arSetDlg'); if (d) d.style.display = 'none'; };

  function anak(grup, L, info) {
    return L.map(function (x) {
      var id = x.d ? x.d.id : x.id, nm = x.d ? x.d.name : x.name;
      return { id: 'ar.' + grup + '.' + id, t: nm, ic: 'dom',
               chk: AR.sel(grup, id), onChk: function (v) { arSel(grup, id, v); },
               dim: x.siap === false, b: x.siap === false ? 'belum siap' : '',
               hint: x.sebab || info };
    });
  }

  /* node di bawah Geomodeller Vein */
  window.arWfTree = function () {
    if (!window.GM || !fn('gmTops')) return [];
    var D = arWfDoms(); if (!D.length) return [];
    var n = D.filter(function (d) { return AR.sel('wf', d.id); }).length;
    return [{
      id: 'ar.wf', t: 'Autorun Wireframe', ic: 'gear', fold: 1, tab: 'GM',
      b: n + ' dari ' + D.length + ' domain',
      hint: 'String kontrol semua section → solid, sekali jalan. String hasil edit tangan tidak ditimpa.',
      menu: function () {
        return [
          { t: 'Jalankan untuk domain tercentang', dis: !n || AR.busy, fn: function () { arWf(); } },
          { sep: 1 },
          { t: 'Pengaturan autorun… (spasi section)', fn: function () { arAtur(); } },
          { t: 'Lihat laporan autorun terakhir', dis: !AR.log, fn: function () { arLihat(); } },
          { sep: 1 },
          { h: 'Catatan' },
          { t: 'Dari nol & melanjutkan = perintah yang sama', dis: 1 },
          { t: 'Keputusan diambil per section, bukan per domain', dis: 1 }
        ];
      },
      kids: anak('wf', D, 'Ikut autorun wireframe')
    }];
  };

  /* node di bawah Model Estimation */
  window.arEstTree = function () {
    if (!window.ME || !fn('gmTops') || !gmTops().length) return [];
    var S = arEstSiap(), n = S.filter(function (x) { return x.siap && AR.sel('est', x.d.id); }).length;
    return [{
      id: 'ar.est', t: 'Autorun Estimation (update)', ic: 'gear', fold: 1, tab: 'ME',
      b: n ? n + ' domain siap' : 'belum ada domain siap',
      dim: !n,
      hint: 'Memakai parameter tersimpan per domain — tanpa fitting ulang. Lanjut ke estimasi waste dan Reporting BM.',
      menu: function () {
        return [
          { t: 'Jalankan update sekarang', dis: !n || AR.busy, fn: function () { arEst(); } },
          { sep: 1 },
          { t: 'Pengaturan autorun…', fn: function () { arAtur(); } },
          { t: 'Lihat laporan autorun terakhir', dis: !AR.log, fn: function () { arLihat(); } }
        ];
      },
      kids: anak('est', S, 'Ikut autorun estimasi')
    }];
  };

  /* node di bawah Geomodeller Stratified-Laterite */
  window.arLatTree = function () {
    if (!window.SL) return [];
    var L = SL.L || [];
    return [{
      id: 'ar.lap', t: 'Autorun Lapisan & Estimasi', ic: 'gear', fold: 1, tab: 'SL',
      b: L.length ? L.length + ' lapisan' : 'belum ada lapisan',
      dim: !L.length,
      hint: 'Usulan lapisan dari log geologi (bila belum ada) → permukaan atap/lantai → estimasi unfold per lapisan + waste laterit',
      menu: function () {
        return [
          { t: L.length ? 'Bangun ulang permukaan lapisan' : 'Usulkan lapisan dari log geologi…', dis: AR.busy, fn: function () { arLap(); } },
          { t: 'Jalankan estimasi lapisan + waste', dis: !L.length || AR.busy, fn: function () { arEstLat(); } },
          { sep: 1 },
          { t: 'Pengaturan autorun…', fn: function () { arAtur(); } },
          { t: 'Lihat laporan autorun terakhir', dis: !AR.log, fn: function () { arLihat(); } }
        ];
      }
    }];
  };

  /* ---------- pengaturan autorun ikut tersimpan di berkas proyek ---------- */
  if (window.SA && SA.collectWork) {
    var _c = SA.collectWork;
    SA.collectWork = function () { var w = _c.apply(this, arguments); try { w.arun = { o: AR.o, pil: AR.pil || {} }; } catch (e) {} return w; };
    var _a = SA.applyWork;
    SA.applyWork = function (W) {
      try { if (W && W.arun) { if (W.arun.o) Object.keys(W.arun.o).forEach(function (k) { AR.o[k] = W.arun.o[k]; }); AR.pil = W.arun.pil || {}; } } catch (e) {}
      return _a.apply(this, arguments);
    };
  }
})();
