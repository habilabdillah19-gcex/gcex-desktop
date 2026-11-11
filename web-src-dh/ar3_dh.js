/* ============ AUTORUN ESTIMASI DARI NOL (Tahap 3) ============
   Berbeda tajam dari Autorun Estimation (update). Yang update memakai parameter yang SUDAH Anda
   setujui; yang ini belum punya apa-apa, jadi ia harus MENGUSULKAN parameter statistik. Karena itu
   seluruh rancangannya berputar pada satu hal: usulan boleh salah, dan kesalahannya harus kelihatan.

   Tidak ada algoritme baru. Yang dipanggil adalah fungsi yang sudah dipakai manual:
     gsRun()      -> komposit + variogram eksperimental domain aktif
     gsrAuto()    -> rekomendasi otomatis (lag, transform, top-cut)      [asinkron: GSR.busy]
     gsFitAuto()  -> fitting model variogram
     knaRun() + knaApply() -> pindai lingkungan kriging, terapkan yang terbaik
     meFromGs(d)  -> simpan parameter ke domain
     AOI.go()     -> kerangka blok bila belum ada block model            [asinkron: AOI.busy]
     SB (sub-blocking) -> pecah blok di batas solid

   GERBANG MUTU per domain, dan inilah bedanya dengan "pokoknya jalan":
     komposit < ambang            -> DILEWATI (tidak ada yang disimpan)
     nugget % > ambang            -> disimpan tetapi ditandai PERLU DITINJAU
     range mayor tidak masuk akal -> disimpan tetapi ditandai PERLU DITINJAU
   Parameter yang ditandai tetap harus dilihat mata Anda di Geostatistik sebelum dipakai produksi.
   Autorun ini sengaja TIDAK langsung mengestimasi; itu pilihan terpisah yang bawaannya mati.      */
(function () {
  if (window.AR3) return;
  var AR3 = window.AR3 = {
    o: { bx: 0, by: 0, bz: 0, aoi: 'auto', sb: false, sbN: 10, minKomp: 30, maxNug: 80, simpan: true, lanjut: false, bidang: true },
    pil: {}, log: null, busy: false
  };

  function E(s) { return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; }); }
  function N(v, d) { return (v == null || !isFinite(v)) ? '-' : (+v).toLocaleString('id-ID', { maximumFractionDigits: d == null ? 0 : d }); }
  function $(i) { return document.getElementById(i); }
  function fn(n) { return typeof window[n] === 'function'; }
  function tunggu(ada, cb, batas) {
    var t0 = Date.now(), lim = batas || 1800000;
    (function p() {
      var m; try { m = ada(); } catch (e) { m = false; }
      if (!m) return cb(null);
      if (Date.now() - t0 > lim) return cb('melewati batas waktu');
      setTimeout(p, 250);
    })();
  }

  /* ---------- usulan ukuran blok: dari spasi bor, bukan dari angka hafalan ---------- */
  function spasiBor() {
    var C = (window.collars || []).map(function (c) { return [c[1], c[2]]; });
    if (C.length < 3) return null;
    var D = [], n = Math.min(C.length, 400);
    for (var i = 0; i < n; i++) {
      var best = 1e18;
      for (var j = 0; j < C.length; j++) {
        if (i === j) continue;
        var dx = C[i][0] - C[j][0], dy = C[i][1] - C[j][1], d = dx * dx + dy * dy;
        if (d < best) best = d;
      }
      if (best < 1e17) D.push(Math.sqrt(best));
    }
    if (!D.length) return null;
    D.sort(function (a, b) { return a - b; });
    return { med: D[D.length >> 1], n: D.length };
  }
  function tebalVein() {
    if (fn('wfTebal')) { try { return wfTebal(window.GM && GM.act); } catch (e) {} }
    if (!fn('gmContacts') || !window.GM) return null;
    var T = [];
    (fn('gmTops') ? gmTops() : []).forEach(function (d) {
      var C = gmContacts(d.id);
      if (C && C.L) C.L.forEach(function (c) {
        var v = Math.hypot(c.hw.x - c.fw.x, c.hw.y - c.fw.y, c.hw.z - c.fw.z);
        if (isFinite(v) && v > 0) T.push(v);
      });
    });
    if (!T.length) return null;
    T.sort(function (a, b) { return a - b; });
    return { n: T.length, med: T[T.length >> 1], min: T[0], max: T[T.length - 1] };
  }
  function usulBlok() {
    var sp = spasiBor(), tb = tebalVein(), o = { sp: sp, tb: tb };
    if (!sp) return o;
    var b = Math.max(1, Math.round(sp.med / 3));
    o.bx = b; o.by = b;
    o.bz = tb ? Math.max(1, Math.min(b, Math.round(tb.med))) : b;
    o.alasan = 'spasi bor (median jarak ke bor terdekat) <b>' + N(sp.med, 1) + ' m</b> &rarr; blok X/Y &asymp; ' +
               'sepertiganya = <b>' + N(o.bx) + ' m</b>' +
               (tb ? '; tebal vein median <b>' + N(tb.med, 2) + ' m</b> &rarr; blok Z <b>' + N(o.bz) + ' m</b>' : '');
    o.sbPerlu = !!(tb && o.bz > 0 && tb.med / o.bz < 3);
    if (o.sbPerlu) o.sbAlasan = 'tebal vein median ' + N(tb.med, 2) + ' m hanya ' + N(tb.med / o.bz, 1) +
      '&times; tinggi blok &mdash; batas solid akan kasar, <b>sub-blocking disarankan</b>';
    return o;
  }
  window.ar3Usul = usulBlok;

  /* ---------- laporan ---------- */
  function mulai(judul) { AR3.busy = true; AR3.log = { judul: judul, t0: Date.now(), baris: [], pesan: '', selesai: false }; kotak(); }
  function baris(o) { AR3.log.baris.push(o); kotak(); }
  function usai(p) { AR3.log.pesan = p || ''; AR3.log.ms = Date.now() - AR3.log.t0; AR3.log.selesai = true; AR3.busy = false; kotak(); try { if (window.PT && PT.render) PT.render(true); } catch (e) {} }

  var WARNA = { simpan: '#2b8a3e', tinjau: '#e8590c', lewat: '#b42318' };
  function kotak() {
    var d = $('ar3Dlg');
    if (!d) { d = document.createElement('div'); d.id = 'ar3Dlg'; d.className = 'bxdlg'; document.body.appendChild(d); }
    var L = AR3.log || { judul: '', baris: [] };
    var rows = L.baris.map(function (b) {
      var v = b.verdikt || '';
      return '<tr><td><b>' + E(b.nama) + '</b>' + (v ? '<br><small style="color:' + (WARNA[v] || '') + ';font-weight:700">' +
        (v === 'simpan' ? '✓ tersimpan' : v === 'tinjau' ? '⚠ perlu ditinjau' : '✖ dilewati') + '</small>' : '') +
        '</td><td>' + (b.hasil || '') + '</td><td>' + (b.par || '') + '</td><td><small>' + (b.ket || '') + '</small></td></tr>';
    }).join('') || '<tr><td colspan=4 class=hint>&hellip;</td></tr>';
    d.innerHTML = '<div class=impBox style=width:min(960px,100%)><div class=impHead><div class=impBrand><div><b>' + E(L.judul) + '</b>' +
      '<small>Autorun ini <b>mengusulkan</b> parameter statistik. Usulan boleh salah &mdash; karena itu tiap domain diberi putusan: tersimpan, perlu ditinjau, atau dilewati.</small>' +
      '</div></div><button class="ib ghost" onclick="ar3Close()">Tutup</button></div><div class=impBody>' +
      '<table class=pltb><tr><th>Domain / langkah</th><th>Data</th><th>Parameter usulan</th><th>Catatan</th></tr>' + rows + '</table>' +
      (L.pesan ? '<div class=box>' + L.pesan + '</div>' : (L.selesai ? '' : '<div class=hint>Sedang berjalan&hellip;</div>')) +
      '</div><div class=impFoot><div class=hint>' + (L.ms ? (L.ms / 1000).toFixed(1) + ' detik' : '') + '</div>' +
      (L.selesai ? '<button class=ib onclick="ar3Csv()">&#8681; Laporan CSV</button>' : '') +
      '<button class=ib onclick="ar3Close()">Selesai</button></div></div>';
    d.style.display = 'flex';
  }
  window.ar3Close = function () { var d = $('ar3Dlg'); if (d) d.style.display = 'none'; };
  window.ar3Lihat = function () { if (AR3.log) kotak(); else alert('Belum ada autorun dari nol di sesi ini.'); };
  window.ar3Csv = function () {
    var L = AR3.log; if (!L) return;
    var q = function (v) { v = String(v == null ? '' : v).replace(/<[^>]+>/g, '').replace(/&middot;/g, '·').replace(/&rarr;/g, '->'); return /[",\n]/.test(v) ? '"' + v.replace(/"/g, '""') + '"' : v; };
    var t = ['Autorun dari nol,' + q(L.judul), 'Nama,Putusan,Data,Parameter,Catatan'].concat(
      L.baris.map(function (b) { return [b.nama, b.verdikt || '', b.hasil, b.par, b.ket].map(q).join(','); })).join('\r\n');
    var a = document.createElement('a');
    gxSimpan(t, 'Autorun_dari_nol.csv', 'text/csv');
  };

  /* ---------- pilihan ---------- */
  AR3.sel = function (id) { return AR3.pil[id] !== false; };
  window.ar3Sel = function (id, v) { AR3.pil[id] = !!v; try { if (window.PT && PT.render) PT.render(true); } catch (e) {} };
  window.ar3Set = function (k, v) {
    AR3.o[k] = (k === 'aoi') ? v : (typeof AR3.o[k] === 'boolean' ? !!v : (+v || 0));
    if (window.SA && SA.dirty) SA.dirty();
    ar3Dlg();
  };

  window.ar3Dlg = function () {
    var d = $('ar3SetDlg');
    if (!d) { d = document.createElement('div'); d.id = 'ar3SetDlg'; d.className = 'bxdlg'; document.body.appendChild(d); }
    var o = AR3.o, U = usulBlok(), ada = !!(window.BX && BX.m);
    if (!o.bx && U.bx) { o.bx = U.bx; o.by = U.by; o.bz = U.bz; }
    if (!ada && o.aoi === 'auto') o.aoi = 'baru';
    var D = fn('gmTops') ? gmTops() : [];
    d.innerHTML = '<div class=impBox style=width:min(720px,100%)><div class=impHead><div class=impBrand><div><b>Autorun Estimasi dari Nol</b>' +
      '<small>Untuk domain yang <b>belum punya parameter</b>. Mengusulkan variogram, lingkungan kriging dan ukuran blok, lalu memberi putusan per domain.</small>' +
      '</div></div><button class="ib ghost" onclick="ar3SetClose()">Tutup</button></div><div class=impBody>' +

      '<div class=imsec>Block model</div>' +
      '<div class="g2 f"><div><label>Sumber blok</label><select onchange="ar3Set(\'aoi\',this.value)">' +
      '<option value=pakai' + (o.aoi === 'pakai' ? ' selected' : '') + (ada ? '' : ' disabled') + '>Pakai block model aktif' + (ada ? ' (' + N(BX.m.n) + ' blok)' : ' — belum ada') + '</option>' +
      '<option value=baru' + (o.aoi === 'baru' ? ' selected' : '') + '>Buat kerangka blok (AOI) baru</option>' +
      '</select><div class=hint>' + (ada ? 'Block model dari Surpac / AOI yang sedang aktif dipakai apa adanya.' : 'Belum ada block model, jadi kerangka AOI dibuat lebih dulu.') + '</div></div>' +
      '<div><label>Sub-blocking di batas solid</label><select onchange="ar3Set(\'sb\',this.value===\'1\')">' +
      '<option value=0' + (!o.sb ? ' selected' : '') + '>Tidak</option><option value=1' + (o.sb ? ' selected' : '') + '>Ya</option></select>' +
      '<div class=hint>' + (U.sbPerlu ? '<span class=warn>Disarankan:</span> ' + U.sbAlasan : 'Blok dipecah di batas solid supaya dilusi batas terukur.') + '</div></div></div>' +

      '<div class="g3 f"><div><label>Blok X (m)</label><input type=number step=any value="' + (o.bx || '') + '" onchange="ar3Set(\'bx\',this.value)"></div>' +
      '<div><label>Blok Y (m)</label><input type=number step=any value="' + (o.by || '') + '" onchange="ar3Set(\'by\',this.value)"></div>' +
      '<div><label>Blok Z (m)</label><input type=number step=any value="' + (o.bz || '') + '" onchange="ar3Set(\'bz\',this.value)"></div></div>' +
      (U.alasan ? '<div class=hint style="margin-top:-6px">Usulan dari data: ' + U.alasan + '. Angka ini <b>usulan</b>, bukan keharusan &mdash; ubah bila tinggi bench atau selektivitas alat gali Anda menentukan lain.</div>' : '') +
      (o.sb ? '<div class="g2 f"><div><label>Pembagi sub-blok (N)</label><input type=number step=1 min=2 value="' + o.sbN + '" onchange="ar3Set(\'sbN\',this.value)">' +
        '<div class=hint>N³ titik uji per blok untuk proporsi volume. 10 memberi volume tepat pada uji; makin besar makin lambat.</div></div><div></div></div>' : '') +

      '<div class=imsec>Gerbang mutu</div>' +
      '<div class="g2 f"><div><label>Minimal komposit per domain</label><input type=number step=1 value="' + o.minKomp + '" onchange="ar3Set(\'minKomp\',this.value)">' +
      '<div class=hint>Di bawah ini domain <b>dilewati</b> &mdash; variogram dari sampel sesedikit itu tidak bermakna.</div></div>' +
      '<div><label>Nugget maksimal (%)</label><input type=number step=1 value="' + o.maxNug + '" onchange="ar3Set(\'maxNug\',this.value)">' +
      '<div class=hint>Di atas ini parameter tetap disimpan tetapi ditandai <b>perlu ditinjau</b>.</div></div></div>' +

      '<label class=sw><input type=checkbox ' + (o.bidang !== false ? 'checked' : '') + ' onchange="ar3Set(\'bidang\',this.checked)">Variogram dari sayatan di bidang tiap domain</label>' +
      '<div class=hint>Seperti tombol <b>Sayatan di bidang domain</b> di Geostatistik: semua komposit domain masuk. Dimatikan = memakai sayatan yang sedang aktif. Sayatan Anda dikembalikan sesudah autorun.</div>' +

      '<div class=imsec>Sesudah parameter diusulkan</div>' +
      '<label class=sw><input type=checkbox ' + (o.simpan ? 'checked' : '') + ' onchange="ar3Set(\'simpan\',this.checked)">Simpan parameter ke domain</label>' +
      '<label class=sw><input type=checkbox ' + (o.lanjut ? 'checked' : '') + ' onchange="ar3Set(\'lanjut\',this.checked)">Langsung lanjut mengestimasi sesudahnya</label>' +
      '<div class=box>Bawaannya <b>tidak langsung mengestimasi</b>. Lihat dulu putusan tiap domain di laporan, periksa yang bertanda <b>perlu ditinjau</b> di Geostatistik, baru jalankan <b>Autorun Estimation (update)</b>.</div>' +
      '<div class=hint>Domain yang ikut dipilih di anak node <b>Autorun Estimasi dari Nol</b> (' + D.length + ' domain tersedia).</div>' +
      '</div><div class=impFoot><div class=hint></div>' +
      '<button class=ib onclick="ar3SetClose();ar3Run()">Jalankan →</button></div></div>';
    d.style.display = 'flex';
  };
  window.ar3SetClose = function () { var d = $('ar3SetDlg'); if (d) d.style.display = 'none'; };

  /* ---------- domain yang perlu "dari nol" ---------- */
  window.ar3Doms = function () {
    return (fn('gmTops') ? gmTops() : []).map(function (d) {
      var P = fn('meParOf') ? meParOf(d) : null;
      var R = fn('meGrpR') ? meGrpR(d) : null;
      var on = fn('imPar') ? imPar(d).on : false;
      return { d: d, adaPar: !!P, solid: !!(on && R && R.mesh) };
    });
  };

  /* ---------- jalankan ---------- */
  window.ar3Run = function () {
    if (AR3.busy || (window.AR && AR.busy)) { alert('Autorun lain sedang berjalan.'); return; }
    var S = ar3Doms().filter(function (x) { return AR3.sel(x.d.id); });
    if (!S.length) { alert('Centang dulu domain di anak node Autorun Estimasi dari Nol.'); return; }
    var o = AR3.o;
    mulai('Autorun Estimasi dari Nol — ' + S.length + ' domain');

    if (!window.GS || !GS.open) { try { gsToggle(); } catch (e) {} }

    var SEC_ID = ['sMode', 'p1e', 'p1n', 'p2e', 'p2n', 'dipS', 'dipN', 'pos', 'thick'], secAwal = null;
    if (o.bidang !== false) secSimpan();
    langkahBlok(function () {
      var i = 0;
      (function next() {
        if (i >= S.length) return tutup();
        var x = S[i++];
        setTimeout(function () { domain(x, next); }, 30);
      })();
    });

    /* ---- 1. kerangka blok + sub-blocking ---- */
    function langkahBlok(lanjut) {
      if (o.aoi !== 'baru') {
        baris({ nama: 'Block model', hasil: (window.BX && BX.m) ? N(BX.m.n) + ' blok' : '<span class=warn>belum ada</span>',
                par: 'dipakai apa adanya', ket: 'tidak ada kerangka baru yang dibuat' });
        return sub(lanjut);
      }
      if (!window.AOI || !AOI.go) {
        baris({ nama: 'Kerangka blok (AOI)', verdikt: 'lewat', ket: 'menu kerangka blok belum siap' });
        return sub(lanjut);
      }
      try {
        AOI.cfg = AOI.cfg || (fn('aoiDef') ? aoiDef() : {});
        if (o.bx) AOI.cfg.bx = o.bx; if (o.by) AOI.cfg.by = o.by; if (o.bz) AOI.cfg.bz = o.bz;
        AOI.cfg.mode = (window.BX && BX.m) ? 'isi' : 'baru';
        AOI.go();
      } catch (e) {
        baris({ nama: 'Kerangka blok (AOI)', verdikt: 'lewat', ket: 'gagal: ' + E(e.message || e) });
        return sub(lanjut);
      }
      tunggu(function () { return window.AOI && AOI.busy; }, function (err) {
        var m = window.BX && BX.m;
        baris({ nama: 'Kerangka blok (AOI)', verdikt: m ? 'simpan' : 'lewat',
                hasil: m ? '<b>' + N(m.n) + '</b> blok' : '<span class=warn>gagal</span>',
                par: N(o.bx) + ' × ' + N(o.by) + ' × ' + N(o.bz) + ' m',
                ket: err ? E(err) : (AOI.msg ? E(String(AOI.msg).replace(/<[^>]+>/g, '')) : 'dipotong topografi / pit sesuai pengaturan kerangka blok') });
        sub(lanjut);
      });
    }
    function sub(lanjut) {
      if (!o.sb) return lanjut();
      if (!window.SB) { baris({ nama: 'Sub-blocking', verdikt: 'lewat', ket: 'modul sub-blocking belum siap' }); return lanjut(); }
      baris({ nama: 'Sub-blocking', hasil: 'pengaturan disiapkan', par: 'N = ' + N(o.sbN),
              ket: 'pecah blok di batas solid dijalankan dari menu Block Model; proporsi volume (sb_frac) dipakai Reporting BM' });
      lanjut();
    }

    /* ---- sayatan di bidang domain (0.24.75, disetujui pemilik 11 Nov 2026) ----
       Variogram Geostatistik dihitung dari komposit di dalam SAYATAN AKTIF. Dulu autorun memakai sayatan apa pun
       yang sedang terpasang: pada Zona 3 sayatan horizontal bawaan hanya memuat 13 dari 489 komposit QV3, sehingga
       domain dilewati. Sekarang tiap domain dipasangi sayatan di bidangnya sendiri (strike & dip dari kontak bor,
       tebal = sebaran kontak) -- sama dengan tombol "Sayatan di bidang domain" di Geostatistik. Sayatan Anda
       dikembalikan sesudah autorun selesai. */
    function secSimpan() { secAwal = {}; SEC_ID.forEach(function (k) { var e = $(k); if (e) secAwal[k] = e.value; }); var l = $('limSeg'); if (l) secAwal._lim = l.checked; }
    function secPulih() {
      if (!secAwal) return;
      SEC_ID.forEach(function (k) { var e = $(k); if (e && secAwal[k] != null) e.value = secAwal[k]; });
      var l = $('limSeg'); if (l && secAwal._lim != null) l.checked = secAwal._lim;
      try { modeChanged(); } catch (e) {} try { updatePlot(); } catch (e) {}
      secAwal = null;
    }
    function bidang(d) {
      if (!(window.NY && NY.planeSec)) return '';
      var al = window.alert, pesan = '';
      window.alert = function (m) { pesan = String(m || ''); };
      try { NY.lastPlane = null; NY.planeSec(); } catch (e) { pesan = e.message || String(e); } finally { window.alert = al; }
      var L = NY.lastPlane;
      if (!L) return '<span class=warn>sayatan di bidang domain tidak bisa dipasang' + (pesan ? ' (' + E(pesan) + ')' : '') + '; dipakai sayatan aktif.</span> ';
      return '<small>Sayatan di bidang domain: strike ' + N(L.az, 0) + '&deg;, dip ' + N(L.dip, 0) + '&deg;, tebal ' + N(L.thick) + ' m.</small><br>';
    }

    /* ---- 2. per domain: variogram -> KNA -> simpan ---- */
    function domain(x, next) {
      var d = x.d, nm = d.name;
      if (x.adaPar) {
        baris({ nama: nm, verdikt: 'lewat', ket: 'domain ini <b>sudah punya parameter tersimpan</b> &mdash; autorun dari nol tidak menimpanya. Pakai Autorun Estimation (update), atau hapus parameternya dulu bila memang mau diulang dari nol.' });
        return next();
      }
      if (!x.solid) {
        baris({ nama: nm, verdikt: 'lewat', ket: 'solid domain belum terbentuk &mdash; jalankan <b>Autorun Wireframe</b> dulu' });
        return next();
      }
      try { gxDomAct(d.id, 'gs'); } catch (e) {}
      var bid = o.bidang !== false ? bidang(d) : '';
      try { gsRun(); } catch (e) {
        baris({ nama: nm, verdikt: 'lewat', ket: 'gagal menghitung variogram: ' + E(e.message || e) });
        return next();
      }
      var R = window.GS && GS.R;
      var nK = R && R.C ? R.C.length : 0;
      if (!R || nK < Math.max(5, +o.minKomp || 30)) {
        baris({ nama: nm, verdikt: 'lewat', hasil: N(nK) + ' komposit',
                ket: bid + 'di bawah ambang ' + N(o.minKomp) + ' &mdash; variogram dari sampel sesedikit ini tidak bermakna. Tambah bor, atau gabungkan domain sejenis lebih dulu.' });
        return next();
      }
      /* rekomendasi otomatis (asinkron), lalu fitting */
      var pakaiAuto = fn('gsrAuto') && window.GSR;
      if (pakaiAuto) { try { gsrAuto(); } catch (e) { pakaiAuto = false; } }
      tunggu(function () { return pakaiAuto && window.GSR && GSR.busy; }, function () {
        try { if (fn('gsFitAuto')) gsFitAuto(true); } catch (e) {}
        var R2 = window.GS && GS.R, M = R2 && R2.M;
        if (!M) {
          baris({ nama: nm, verdikt: 'lewat', hasil: N(nK) + ' komposit',
                  ket: 'fitting model variogram gagal &mdash; kerjakan manual di Geostatistik tab Model' });
          return next();
        }
        var ns = M.c[1] > 0, sill = M.c0 + M.c[0] + (ns ? M.c[1] : 0);
        var nug = sill > 0 ? 100 * M.c0 / sill : 100;
        var ra = ns ? Math.max(M.a[0], M.a[1]) : M.a[0];
        var rb = ns ? Math.max(M.b[0], M.b[1]) : M.b[0];
        var rd = ns ? Math.max(M.d[0], M.d[1]) : M.d[0];
        var ext = R2.ext || 0, L = R2.L || 0;
        /* KNA: pindai lingkungan kriging lalu terapkan yang terbaik */
        var kna = '';
        try {
          if (fn('knaRun')) {
            knaRun();
            if (window.KNA && KNA.rec) {
              if (fn('knaApply')) knaApply();
              kna = 'radius ×' + N(KNA.rec.rf, 2) + ', maks ' + N(KNA.rec.nmax) + ' sampel';
            } else kna = '<span class=warn>KNA tidak memberi rekomendasi</span>';
          }
        } catch (e) { kna = '<span class=warn>KNA gagal: ' + E(e.message || e) + '</span>'; }

        /* ---- putusan ---- */
        var alasan = [];
        if (nug > (+o.maxNug || 80)) alasan.push('nugget <b>' + N(nug, 0) + '%</b> di atas ambang ' + N(o.maxNug) + '% &mdash; estimasi akan sangat merata (efek nugget tinggi khas emas kasar)');
        /* nugget MENDEKATI NOL sama mencurigakannya dengan nugget tinggi: pada kadar logam, nugget
           nol praktis tidak pernah terjadi. Biasanya berarti variogram belum terbentuk, atau tidak
           ada pasangan sampel berjarak pendek (downhole) yang cukup untuk melihatnya. */
        if (nug < 5) alasan.push('nugget <b>' + N(nug, 1) + '%</b> mendekati nol &mdash; pada kadar logam itu praktis tidak pernah terjadi. Biasanya berarti variogram belum terbentuk atau pasangan sampel berjarak pendek terlalu sedikit; periksa lag dan variogram downhole di Geostatistik');
        /* elipsoid bulat = anisotropi tidak terselesaikan. Untuk vein ini hampir pasti salah:
           kemenerusan searah strike / dip jauh berbeda dari arah lainnya. */
        if (ra > 0 && rb > 0 && ra / rb < 1.05) alasan.push('range mayor dan semi hampir sama (' + N(ra, 1) + ' m vs ' + N(rb, 1) + ' m) &mdash; <b>anisotropi tidak terselesaikan</b>, elipsoidnya bulat. Untuk vein hampir selalu keliru; periksa arah di kipas variogram lalu pasang orientasi manual');
        if (nK < 50) alasan.push('hanya <b>' + N(nK) + '</b> komposit &mdash; variogram masih rapuh (lazimnya &ge; 50 untuk dipakai produksi)');
        if (!(ra > 0)) alasan.push('range mayor tidak terhitung');
        else if (L > 0 && ra < 2 * L) alasan.push('range mayor (' + N(ra, 1) + ' m) kurang dari 2× panjang komposit &mdash; kemungkinan variogram belum terbentuk');
        else if (ext > 0 && ra > 3 * ext) alasan.push('range mayor (' + N(ra, 1) + ' m) melebihi 3× bentang data &mdash; model kemungkinan tidak terkekang');
        var verdikt = alasan.length ? 'tinjau' : 'simpan';

        var tersimpan = false;
        if (o.simpan && fn('meFromGs')) {
          try { tersimpan = !!meFromGs(d.id); } catch (e) {}
        }
        baris({
          nama: nm, verdikt: verdikt,
          hasil: '<b>' + N(nK) + '</b> komposit' + (R2.st ? '<br><small>mean ' + N(R2.st.mean, 3) + ', CV ' + N(R2.st.cv, 2) + '</small>' : '') +
                 (R2.tc ? '<br><small>top-cut ' + N(R2.tc, 2) + '</small>' : ''),
          par: 'nugget <b>' + N(nug, 0) + '%</b><br><small>range mayor ' + N(ra, 1) + ' m · semi ' + N(rb, 1) + ' m · downhole ' + N(rd, 1) + ' m</small>' +
               (kna ? '<br><small>KNA: ' + kna + '</small>' : ''),
          ket: bid + (alasan.length ? '<span class=warn>Perlu ditinjau:</span> ' + alasan.join('; ') + '. ' : '') +
               (o.simpan ? (tersimpan ? 'Parameter tersimpan ke domain.' : '<span class=warn>Gagal menyimpan ke domain.</span>')
                         : 'Tidak disimpan (pilihan "Simpan parameter ke domain" dimatikan).')
        });
        next();
      });
    }

    /* ---- 3. penutup ---- */
    function tutup() {
      secPulih();
      var B = AR3.log.baris, sim = B.filter(function (b) { return b.verdikt === 'simpan'; }).length;
      var tj = B.filter(function (b) { return b.verdikt === 'tinjau'; }).length;
      var lw = B.filter(function (b) { return b.verdikt === 'lewat'; }).length;
      var p = '<b>' + sim + '</b> tersimpan, <b>' + tj + '</b> perlu ditinjau, <b>' + lw + '</b> dilewati. ';
      if (tj) p += 'Yang bertanda <b>perlu ditinjau</b> parameternya sudah tersimpan tetapi <b>belum layak produksi</b>: buka Geostatistik, periksa variogramnya, perbaiki, lalu simpan ulang. ';
      p += 'Autorun dari nol hanya <b>mengusulkan</b>; angka sumber daya tidak boleh dilaporkan dari usulan yang belum dilihat mata Anda.';
      if (o.lanjut && fn('arEst')) {
        p += '<br><br>Melanjutkan ke estimasi&hellip;';
        usai(p);
        setTimeout(function () { try { arEst(); } catch (e) {} }, 500);
        return;
      }
      p += '<br><br>Langkah berikutnya: node <b>Autorun Estimation (update)</b> untuk menjalankan estimasinya.';
      usai(p);
    }
  };

  /* ---------- node Project Tree ---------- */
  window.ar3Tree = function () {
    if (!window.ME || !fn('gmTops') || !gmTops().length) return [];
    var S = ar3Doms(), perlu = S.filter(function (x) { return !x.adaPar; });
    var n = perlu.filter(function (x) { return AR3.sel(x.d.id); }).length;
    return [{
      id: 'ar3', t: 'Autorun Estimasi dari Nol', ic: 'gear', fold: 1, tab: 'ME',
      b: perlu.length ? (n + ' dari ' + perlu.length + ' domain belum berparameter') : 'semua domain sudah berparameter',
      dim: !perlu.length,
      hint: 'Untuk domain baru: usulkan variogram + KNA + ukuran blok, dengan putusan per domain (tersimpan / perlu ditinjau / dilewati)',
      menu: function () {
        return [
          { t: 'Atur & jalankan… (ukuran blok, sub-blok, gerbang mutu)', dis: !perlu.length || AR3.busy, fn: function () { ar3Dlg(); } },
          { t: 'Lihat laporan terakhir', dis: !AR3.log, fn: function () { ar3Lihat(); } },
          { sep: 1 },
          { h: 'Catatan' },
          { t: 'Domain yang sudah berparameter tidak ditimpa', dis: 1 },
          { t: 'Usulan tetap harus ditinjau sebelum dilaporkan', dis: 1 }
        ];
      },
      kids: S.map(function (x) {
        return { id: 'ar3.' + x.d.id, t: x.d.name, ic: 'dom',
                 chk: !x.adaPar && AR3.sel(x.d.id), onChk: function (v) { ar3Sel(x.d.id, v); },
                 dim: x.adaPar, b: x.adaPar ? 'sudah berparameter' : (x.solid ? '' : 'solid belum ada'),
                 hint: x.adaPar ? 'Sudah punya parameter tersimpan — pakai Autorun Estimation (update)'
                                : (x.solid ? 'Siap diusulkan parameternya' : 'Jalankan Autorun Wireframe dulu') };
      })
    }];
  };

  if (window.SA && SA.collectWork) {
    var _c = SA.collectWork;
    SA.collectWork = function () { var w = _c.apply(this, arguments); try { w.ar3 = { o: AR3.o, pil: AR3.pil }; } catch (e) {} return w; };
    var _a = SA.applyWork;
    SA.applyWork = function (W) {
      try { if (W && W.ar3) { if (W.ar3.o) Object.keys(W.ar3.o).forEach(function (k) { AR3.o[k] = W.ar3.o[k]; }); AR3.pil = W.ar3.pil || {}; } } catch (e) {}
      return _a.apply(this, arguments);
    };
  }
})();
