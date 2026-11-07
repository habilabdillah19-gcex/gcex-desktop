/* ============ ALAT HARIAN GRADE CONTROL — GC-Ex Block Model ============
   Untuk Junior Grade Control / Short Term Mine Planner. Tiga hal yang sebelumnya dikerjakan dengan
   mata dan ingatan, sekarang dihitung:

   1. PEMERIKSAAN DIG BLOCK (qcRun) — sebelum dig plan terbit, bukan ditemukan operator di pit:
        tanpa tujuan material, lebar minimum di bawah batas selektivitas alat (mmw), luas di bawah
        ambang, tonase nol / kadar kosong, poligon tidak tertutup, garis saling memotong (self-
        intersect), dan nama ganda. Lebar minimum dihitung dengan rotating calipers pada convex hull
        poligon -- bukan perkiraan luas/keliling -- jadi angkanya bisa dipertanggungjawabkan.

   2. RINGKASAN HARIAN (dayBox) — satu halaman untuk flitch aktif: ton, kadar semua unsur terpilih,
        jumlah dig block per material dan per tujuan, ditambah as-mined flitch yang sama bila sudah
        ada, sehingga rencana vs aktual terlihat tanpa merakit beberapa tabel.

   3. PRESET KELAS KADAR & TUJUAN MATERIAL (PST) — batas kelas (dbU().rules), aturan tujuan
        (lyU().destR), lebar minimum dan ambang sulfida disimpan sebagai preset bernama di berkas
        proyek, supaya shift siang dan malam, dan antar orang, memakai batas yang sama persis.

   Semua angka memakai fungsi yang sudah ada (lyItems / flCalc / elAgg), jadi tidak pernah berbeda
   dari rekap dig block, register, maupun PDF.                                                      */
(function () {
  if (window.GCO || typeof BX === 'undefined') return;
  var GCO = window.GCO = { qc: null, pst: null, msg: '' };
  var $ = function (i) { return document.getElementById(i); };
  function E(s) { return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) { return '&#' + c.charCodeAt(0) + ';'; }); }
  function N(v, d) { return (v == null || !isFinite(v)) ? '-' : (+v).toLocaleString('id-ID', { minimumFractionDigits: d || 0, maximumFractionDigits: d || 0 }); }
  function fn(n) { return typeof window[n] === 'function'; }

  /* ================= geometri: lebar minimum & perpotongan sendiri ================= */
  function hull(P) {
    var S = P.map(function (q) { return [q[0], q[1]]; }).sort(function (a, b) { return a[0] - b[0] || a[1] - b[1]; });
    if (S.length < 3) return S;
    var cr = function (o, a, b) { return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0]); };
    var L = [], i;
    for (i = 0; i < S.length; i++) { while (L.length >= 2 && cr(L[L.length - 2], L[L.length - 1], S[i]) <= 0) L.pop(); L.push(S[i]); }
    var U = [];
    for (i = S.length - 1; i >= 0; i--) { while (U.length >= 2 && cr(U[U.length - 2], U[U.length - 1], S[i]) <= 0) U.pop(); U.push(S[i]); }
    return L.slice(0, -1).concat(U.slice(0, -1));
  }
  /* lebar minimum = jarak terkecil antara dua garis sejajar yang mengapit poligon (rotating calipers) */
  function lebarMin(P) {
    var H = hull(P), n = H.length;
    if (n < 3) return 0;
    var best = Infinity;
    for (var i = 0; i < n; i++) {
      var a = H[i], b = H[(i + 1) % n], dx = b[0] - a[0], dy = b[1] - a[1], L = Math.hypot(dx, dy);
      if (L < 1e-9) continue;
      var mx = 0;
      for (var j = 0; j < n; j++) {
        var d = Math.abs((H[j][0] - a[0]) * dy - (H[j][1] - a[1]) * dx) / L;
        if (d > mx) mx = d;
      }
      if (mx < best) best = mx;
    }
    return isFinite(best) ? best : 0;
  }
  GCO.lebarMin = lebarMin;

  function potongSendiri(P) {
    var n = P.length;
    if (n < 4) return 0;
    var sg = function (p, q, r) { var v = (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0]); return v > 1e-9 ? 1 : v < -1e-9 ? -1 : 0; };
    var pot = function (a, b, c, d) {
      var d1 = sg(a, b, c), d2 = sg(a, b, d), d3 = sg(c, d, a), d4 = sg(c, d, b);
      return d1 !== d2 && d3 !== d4;
    };
    var c = 0;
    for (var i = 0; i < n; i++) {
      for (var j = i + 1; j < n; j++) {
        if (i === j) continue;
        if ((j + 1) % n === i || (i + 1) % n === j) continue;   /* segmen bertetangga */
        if (pot(P[i], P[(i + 1) % n], P[j], P[(j + 1) % n])) c++;
      }
    }
    return c;
  }

  /* ================= 1. PEMERIKSAAN DIG BLOCK ================= */
  GCO.qcRun = function (semua) {
    if (!(BX && BX.m)) { alert('Belum ada block model.'); return; }
    if (!fn('flGroups') || !fn('flCalc')) { alert('Modul dig block belum siap.'); return; }
    var U = fn('dbU') ? dbU() : {}, mmw = +U.mmw || 0, amin = +U.dbMin || 0;
    var B = fn('lyBench') ? lyBench() : null;
    var G = flGroups().filter(function (g) {
      if (semua) return g.db.length;
      return g.db.length && B && Math.abs(g.top - B[0]) < 1e-6 && Math.abs(g.bot - B[1]) < 1e-6;
    });
    var T = [], nama = {}, nDb = 0;
    G.forEach(function (g) {
      var c = flCalc(g); if (!c) return;
      c.it.forEach(function (o) {
        nDb++;
        var ring = (o.s && o.s.pts) ? o.s.pts.map(function (q) { return [q[0], q[1]]; }) : null;
        var add = function (lv, apa, saran) { T.push({ lv: lv, fl: 'RL ' + N(g.top, 1) + '–' + N(g.bot, 1), nama: o.name, apa: apa, saran: saran }); };
        if (!String(o.dest || '').trim()) add('CEGAH', 'tanpa tujuan material', 'isi Tujuan pada dig block, atau lengkapi aturan tujuan di Preset');
        if (!isFinite(o.t) || o.t <= 0) add('CEGAH', 'tonase nol', 'poligon tidak memuat blok model: periksa posisi / flitch / filter atribut');
        else if (!isFinite(o.g)) add('PERIKSA', 'kadar kosong', 'blok di dalamnya berkadar &minus;99 atau atribut kadar belum dipilih');
        if (ring && mmw > 0) {
          var w = lebarMin(ring);
          if (w < mmw) add('CEGAH', 'lebar minimum ' + N(w, 2) + ' m &lt; batas ' + N(mmw, 2) + ' m',
                           'tidak praktis digali: gabungkan dengan blok sebelah, atau lebarkan');
        }
        if (amin > 0 && isFinite(o.area) && o.area < amin) add('PERIKSA', 'luas ' + N(o.area, 1) + ' m² &lt; ambang ' + N(amin, 1) + ' m²', 'blok sangat kecil; pertimbangkan digabung');
        if (ring) {
          if (o.s && o.s.closed === false) add('CEGAH', 'poligon tidak tertutup', 'tutup poligonnya di Digitasi');
          var ps = potongSendiri(ring);
          if (ps) add('CEGAH', 'garis saling memotong (' + ps + ' tempat)', 'perbaiki bentuknya: luas dan tonase tidak bisa dipercaya');
        }
        var k = String(o.name || '').trim().toUpperCase();
        if (k) { nama[k] = (nama[k] || 0) + 1; }
      });
    });
    Object.keys(nama).forEach(function (k) {
      if (nama[k] > 1) T.push({ lv: 'PERIKSA', fl: '-', nama: k, apa: 'nama dipakai ' + nama[k] + ' kali', saran: 'beri nama berbeda supaya tidak tertukar di dispatch & register' });
    });
    GCO.qc = { t: T, nDb: nDb, nFl: G.length, semua: !!semua, mmw: mmw, amin: amin, tgl: new Date().toLocaleString('id-ID') };
    GCO.qcDlg();
  };

  GCO.qcDlg = function () {
    var d = $('qcDlg');
    if (!d) { d = document.createElement('div'); d.id = 'qcDlg'; d.className = 'bxdlg'; document.body.appendChild(d); }
    var Q = GCO.qc || { t: [], nDb: 0, nFl: 0 };
    var nC = Q.t.filter(function (x) { return x.lv === 'CEGAH'; }).length, nP = Q.t.length - nC;
    var rows = Q.t.length ? Q.t.map(function (x) {
      return '<tr><td><b style="color:' + (x.lv === 'CEGAH' ? '#b42318' : '#e8590c') + '">' + x.lv + '</b></td><td>' + E(x.fl) +
        '</td><td>' + E(x.nama) + '</td><td>' + x.apa + '</td><td><small>' + x.saran + '</small></td></tr>';
    }).join('') : '<tr><td colspan=5 style="color:#2b8a3e"><b>&#10003; Tidak ada temuan.</b> ' + N(Q.nDb) + ' dig block diperiksa.</td></tr>';
    d.innerHTML = '<div class=impBox style=width:min(960px,100%)><div class=impHead><div class=impBrand><div><b>Pemeriksaan dig block</b>' +
      '<small>Dijalankan sebelum dig plan terbit. <b>CEGAH</b> = jangan diterbitkan sebelum dibereskan; <b>PERIKSA</b> = perlu dilihat, belum tentu salah.</small>' +
      '</div></div><button class="ib ghost" onclick="GCO.qcClose()">Tutup</button></div><div class=impBody>' +
      '<div class=hint>' + N(Q.nDb) + ' dig block di ' + N(Q.nFl) + ' flitch' + (Q.semua ? ' (semua flitch)' : ' (flitch aktif)') +
      ' &middot; lebar minimum alat <b>' + N(Q.mmw, 2) + ' m</b> &middot; ambang luas <b>' + N(Q.amin, 1) + ' m&sup2;</b> &middot; ' +
      '<b style="color:#b42318">' + nC + ' cegah</b>, <b style="color:#e8590c">' + nP + ' periksa</b></div>' +
      '<table class=pltb><tr><th>Tingkat</th><th>Flitch</th><th>Dig block</th><th>Temuan</th><th>Saran</th></tr>' + rows + '</table>' +
      '</div><div class=impFoot><div class=hint></div>' +
      '<button class=ib onclick="GCO.qcRun(false)">Flitch aktif</button><button class=ib onclick="GCO.qcRun(true)">Semua flitch</button>' +
      '<button class=ib onclick="GCO.qcCsv()">&#8681; CSV</button><button class=ib onclick="GCO.qcClose()">Selesai</button></div></div>';
    d.style.display = 'flex';
  };
  GCO.qcClose = function () { var d = $('qcDlg'); if (d) d.style.display = 'none'; };
  GCO.qcCsv = function () {
    var Q = GCO.qc; if (!Q) return;
    var q = function (v) { v = String(v == null ? '' : v).replace(/<[^>]+>/g, '').replace(/&minus;/g, '-').replace(/&lt;/g, '<').replace(/&sup2;/g, '2'); return /[",\n]/.test(v) ? '"' + v.replace(/"/g, '""') + '"' : v; };
    var L = ['Pemeriksaan dig block,' + q(Q.tgl), 'Dig block diperiksa,' + Q.nDb, 'Lebar minimum alat (m),' + Q.mmw, '', 'Tingkat,Flitch,Dig block,Temuan,Saran']
      .concat(Q.t.map(function (x) { return [x.lv, x.fl, x.nama, x.apa, x.saran].map(q).join(','); }));
    var b = new Blob(['﻿' + L.join('\r\n')], { type: 'text/csv' });
    gxSimpan(b, 'GCEx_PemeriksaanDigBlock.csv');
  };

  /* ================= 2. RINGKASAN HARIAN (flitch aktif) ================= */
  function ring1(g) {
    var c = fn('flCalc') ? flCalc(g) : null;
    if (!c) return null;
    var EL = fn('elList') ? elList() : [], byM = {}, byD = {}, tot = fn('elAgg') ? elAgg() : null;
    c.it.forEach(function (o) {
      var t = o.ton || { t: o.t, el: o.el, elw: o.elw };
      var m = o.d || '-', dd = o.dest || '-';
      if (!byM[m]) byM[m] = { a: fn('elAgg') ? elAgg() : null, n: 0 };
      if (!byD[dd]) byD[dd] = { a: fn('elAgg') ? elAgg() : null, n: 0 };
      if (byM[m].a) byM[m].a.add(t, o.t); byM[m].n++;
      if (byD[dd].a) byD[dd].a.add(t, o.t); byD[dd].n++;
      if (tot) tot.add(t, o.t);
    });
    return { EL: EL, byM: byM, byD: byD, tot: tot, n: c.it.length, g: g };
  }
  function amFl(g) {
    try {
      var L = (fn('amAllInfo') ? amAllInfo() : []).filter(function (q) {
        return q.x && Math.abs(+q.x.top - g.top) < 1e-6 && Math.abs(+q.x.bot - g.bot) < 1e-6 && q.x.st;
      });
      if (!L.length) return null;
      var A = fn('elAgg') ? elAgg() : null;
      L.forEach(function (q) { if (A) A.add({ t: q.ton, el: (q.x.st && q.x.st.el) || {}, elw: (q.x.st && q.x.st.elw) || {} }, q.ton); });
      return { a: A, n: L.length };
    } catch (e) { return null; }
  }

  GCO.dayDlg = function () {
    if (!(BX && BX.m)) { alert('Belum ada block model.'); return; }
    var B = fn('lyBench') ? lyBench() : null;
    var G = (fn('flGroups') ? flGroups() : []).filter(function (g) { return B && Math.abs(g.top - B[0]) < 1e-6 && Math.abs(g.bot - B[1]) < 1e-6; })[0];
    var d = $('dayDlg');
    if (!d) { d = document.createElement('div'); d.id = 'dayDlg'; d.className = 'bxdlg'; document.body.appendChild(d); }
    var h;
    if (!G || !G.db.length) {
      h = '<div class=box>Belum ada dig block di flitch aktif' + (B ? ' (RL ' + N(B[0], 1) + '–' + N(B[1], 1) + ')' : '') +
          '. Buat dig block dulu di langkah <b>Dig Block</b>.</div>';
    } else {
      var S = ring1(G), A = amFl(G), EL = S.EL;
      var hd = function (lab) { return '<tr><th>' + lab + '</th><th>Blok</th><th>Ton</th>' + EL.map(function (a) { return '<th>' + E(a) + '</th>'; }).join('') + '</tr>'; };
      var row = function (lab, o) {
        return '<tr><td><b>' + E(lab) + '</b></td><td>' + N(o.n) + '</td><td>' + N(o.a ? o.a.t : 0) + '</td>' +
          EL.map(function (a) { return '<td>' + (fn('elF') && o.a ? elF(a, o.a.g(a)) : '-') + '</td>'; }).join('') + '</tr>';
      };
      h = '<div class=hint>Flitch aktif <b>RL ' + N(G.top, 1) + ' – ' + N(G.bot, 1) + '</b> &middot; ' + N(S.n) + ' dig block &middot; dibuat ' + E(new Date().toLocaleString('id-ID')) + '</div>';
      h += '<h4>Per material</h4><table class=pltb>' + hd('Material') +
        Object.keys(S.byM).sort().map(function (k) { return row(k, S.byM[k]); }).join('') +
        '<tr style="font-weight:700;background:var(--sf2,#eef2f7)"><td>TOTAL RENCANA</td><td>' + N(S.n) + '</td><td>' + N(S.tot ? S.tot.t : 0) + '</td>' +
        EL.map(function (a) { return '<td>' + (fn('elF') && S.tot ? elF(a, S.tot.g(a)) : '-') + '</td>'; }).join('') + '</tr></table>';
      h += '<h4>Per tujuan material</h4><table class=pltb>' + hd('Tujuan') +
        Object.keys(S.byD).sort().map(function (k) { return row(k, S.byD[k]); }).join('') + '</table>';
      if (A) {
        var dt = (S.tot ? S.tot.t : 0), da = A.a ? A.a.t : 0, sel = da - dt;
        h += '<h4>Rencana vs aktual (as-mined flitch ini)</h4><table class=pltb>' + hd('') +
          row('Rencana (dig block)', { n: S.n, a: S.tot }) + row('Aktual (as-mined)', { n: A.n, a: A.a }) +
          '<tr style="font-weight:700"><td>Selisih</td><td>' + N(A.n - S.n) + '</td><td>' + (sel >= 0 ? '+' : '') + N(sel) + '</td>' +
          EL.map(function () { return '<td>-</td>'; }).join('') + '</tr></table>' +
          '<div class=hint>Selisih tonase ' + (dt > 0 ? ((sel >= 0 ? '+' : '') + N(100 * sel / dt, 1) + '% dari rencana') : '-') + '.</div>';
      } else {
        h += '<div class=box>Belum ada as-mined terhitung untuk flitch ini, jadi perbandingan rencana vs aktual belum bisa ditampilkan. ' +
             'Buat poligon as-mined lalu jalankan As-Mined, atau pakai <b>Laporan periode</b> untuk rekap beberapa hari.</div>';
      }
    }
    d.innerHTML = '<div class=impBox style=width:min(900px,100%)><div class=impHead><div class=impBrand><div><b>Ringkasan harian — flitch aktif</b>' +
      '<small>Ton, kadan semua unsur terpilih, jumlah dig block per material dan per tujuan, serta rencana vs aktual bila as-mined flitch ini sudah dihitung.</small>' +
      '</div></div><button class="ib ghost" onclick="GCO.dayClose()">Tutup</button></div>' +
      '<div class=impBody>' + h + '</div>' +
      '<div class=impFoot><div class=hint></div><button class=ib onclick="GCO.dayCsv()">&#8681; CSV</button>' +
      '<button class=ib onclick="GCO.dayClose()">Selesai</button></div></div>';
    d.style.display = 'flex';
  };
  GCO.dayClose = function () { var d = $('dayDlg'); if (d) d.style.display = 'none'; };
  GCO.dayCsv = function () {
    var B = fn('lyBench') ? lyBench() : null;
    var G = (fn('flGroups') ? flGroups() : []).filter(function (g) { return B && Math.abs(g.top - B[0]) < 1e-6 && Math.abs(g.bot - B[1]) < 1e-6; })[0];
    if (!G) { alert('Belum ada dig block di flitch aktif.'); return; }
    var S = ring1(G), A = amFl(G), EL = S.EL;
    var q = function (v) { v = String(v == null ? '' : v); return /[",\n]/.test(v) ? '"' + v.replace(/"/g, '""') + '"' : v; };
    var L = ['Ringkasan harian,RL ' + G.top + ' - ' + G.bot, 'Dibuat,' + new Date().toLocaleString('id-ID'), '',
             ['Kelompok', 'Nama', 'Blok', 'Ton'].concat(EL).map(q).join(',')];
    var row = function (grp, lab, o) {
      return [grp, lab, o.n, Math.round(o.a ? o.a.t : 0)].concat(EL.map(function (a) { var v = o.a ? o.a.g(a) : NaN; return isFinite(v) ? v.toFixed(4) : ''; })).map(q).join(',');
    };
    Object.keys(S.byM).sort().forEach(function (k) { L.push(row('Material', k, S.byM[k])); });
    Object.keys(S.byD).sort().forEach(function (k) { L.push(row('Tujuan', k, S.byD[k])); });
    L.push(row('Total', 'RENCANA', { n: S.n, a: S.tot }));
    if (A) L.push(row('Total', 'AKTUAL as-mined', { n: A.n, a: A.a }));
    var b = new Blob(['﻿' + L.join('\r\n')], { type: 'text/csv' });
    gxSimpan(b, 'GCEx_RingkasanHarian_RL' + G.top + '.csv');
  };

  /* ================= 3. PRESET KELAS KADAR & TUJUAN ================= */
  function store() { var U = BX.ui || {}; if (!U.pst) U.pst = []; return U.pst; }
  function ambil() {
    var U = fn('dbU') ? dbU() : {}, L = fn('lyU') ? lyU() : {};
    return { rules: JSON.parse(JSON.stringify(U.rules || [])), rAttr: U.rAttr || '', mmw: +U.mmw || 0,
             mmwMode: U.mmwMode || 'grow', dbMin: +U.dbMin || 0, dbMat: U.dbMat || 'ORE',
             sfOn: !!U.sfOn, sfOff: +U.sfOff || 0, sxsThr: +U.sxsThr || 0,
             destR: JSON.parse(JSON.stringify(L.destR || [])), dest: L.dest || '' };
  }
  function terap(p) {
    var U = fn('dbU') ? dbU() : {}, L = fn('lyU') ? lyU() : {};
    if (p.rules) U.rules = JSON.parse(JSON.stringify(p.rules));
    ['rAttr', 'mmw', 'mmwMode', 'dbMin', 'dbMat', 'sfOn', 'sfOff', 'sxsThr'].forEach(function (k) { if (p[k] !== undefined) U[k] = p[k]; });
    if (p.destR) L.destR = JSON.parse(JSON.stringify(p.destR));
    if (p.dest !== undefined) L.dest = p.dest;
    try { if (fn('bxPanel')) bxPanel(); } catch (e) {}
    try { if (fn('lyDestUpd')) lyDestUpd(); } catch (e) {}
    try { if (fn('updatePlot')) updatePlot(); } catch (e) {}
    try { if (window.PT && PT.render) PT.render(true); } catch (e) {}
  }
  GCO.pstSimpan = function () {
    var n = prompt('Nama preset (mis. "Pit A — Nov 2026" atau "Oksida kadar rendah"):', '');
    if (n == null || !String(n).trim()) return;
    var L = store(), nm = String(n).trim();
    var o = { name: nm, tgl: new Date().toISOString().slice(0, 16).replace('T', ' '), p: ambil() };
    var i = -1; L.forEach(function (x, k) { if (x.name.toLowerCase() === nm.toLowerCase()) i = k; });
    if (i >= 0) { if (!confirm('Preset "' + nm + '" sudah ada. Ganti?')) return; L[i] = o; } else L.push(o);
    if (window.bxDirty) bxDirty(); else if (window.SA && SA.dirty) SA.dirty();
    try { if (window.PT && PT.render) PT.render(true); } catch (e) {}
    /* Permintaan pemilik: begitu preset disimpan, preset itu langsung berlaku di flitch aktif.
       Isinya memang pengaturan yang sedang dipakai, jadi menerapkannya tidak mengubah angka apa pun --
       tetapi membuat keadaannya tegas: preset yang baru dibuat itulah yang sedang aktif, bukan
       sesuatu yang masih harus dipilih lagi lewat menu. */
    try { GCO.pstTerap(nm); } catch (e) { console.error(e); }
    try { if (window.PT && PT.select) PT.select('dig.pst'); } catch (e) {}
    alert('Preset "' + nm + '" tersimpan dan langsung dipakai di flitch aktif: ' +
          (o.p.rules || []).length + ' kelas kadar, ' + (o.p.destR || []).length +
          ' aturan tujuan, lebar minimum ' + o.p.mmw + ' m.');
  };
  GCO.pstTerap = function (nm) {
    var L = store(), o = null;
    L.forEach(function (x) { if (x.name === nm) o = x; });
    if (!o) return;
    if (!confirm('Pakai preset "' + nm + '"?\n\nKelas kadar, aturan tujuan, lebar minimum dan ambang sulfida akan diganti. ' +
                 'Dig block yang sudah ada tidak dihapus, tetapi material & tujuannya dihitung ulang dengan aturan baru.')) return;
    terap(o.p);
    GCO.msg = 'Preset "' + nm + '" dipakai.';
  };
  GCO.pstHapus = function (nm) {
    if (!confirm('Hapus preset "' + nm + '"?')) return;
    var U = BX.ui || {}; U.pst = store().filter(function (x) { return x.name !== nm; });
    if (window.bxDirty) bxDirty(); else if (window.SA && SA.dirty) SA.dirty();
    try { if (window.PT && PT.render) PT.render(true); } catch (e) {}
  };

  /* ================= node Project Tree ================= */
  /* di bawah Dig Block: pemeriksaan + preset */
  window.gcoDigTree = function () {
    var L = store(), Q = GCO.qc;
    var nC = Q ? Q.t.filter(function (x) { return x.lv === 'CEGAH'; }).length : 0;
    return [
      { id: 'dig.qc', t: 'Pemeriksaan dig block', ic: 'check',
        b: Q ? (Q.t.length ? nC + ' cegah / ' + (Q.t.length - nC) + ' periksa' : 'bersih') : '',
        hint: 'Jalankan sebelum dig plan terbit: tanpa tujuan, lebar di bawah batas alat, tonase nol, poligon rusak, nama ganda',
        go: function () { GCO.qcRun(false); },
        card: { acts: [{ t: 'Periksa flitch aktif', pri: 1, fn: function () { GCO.qcRun(false); } },
                       { t: 'Periksa semua flitch', fn: function () { GCO.qcRun(true); } },
                       { t: 'Lihat hasil terakhir', fn: function () { if (GCO.qc) GCO.qcDlg(); } }] },
        menu: function () {
          return [{ t: 'Periksa flitch aktif', fn: function () { GCO.qcRun(false); } },
                  { t: 'Periksa semua flitch', fn: function () { GCO.qcRun(true); } },
                  { sep: 1 },
                  { t: 'Lihat hasil terakhir', dis: !Q, fn: function () { GCO.qcDlg(); } },
                  { t: '↓ Export CSV', dis: !Q, fn: function () { GCO.qcCsv(); } }];
        } },
      { id: 'dig.pst', t: 'Preset kelas kadar & tujuan', ic: 'gear', fold: 1,
        b: L.length ? L.length + ' preset' : '', dim: !L.length,
        hint: 'Batas kelas kadar, aturan tujuan material, lebar minimum dan ambang sulfida — supaya DS dan NS memakai batas yang sama',
        card: { kids: 1, hint: 'Simpan batas kelas kadar & aturan tujuan yang sedang dipakai sebagai preset, atau pilih preset di bawah untuk menerapkannya ke flitch aktif.',
                acts: [{ t: '\u2795 Simpan pengaturan sekarang sebagai preset\u2026', pri: 1,
                         fn: function () { GCO.pstSimpan(); } }] },
        menu: function () {
          return [{ t: 'Simpan pengaturan sekarang sebagai preset…', fn: function () { GCO.pstSimpan(); } }]
            .concat(L.length ? [{ sep: 1 }, { h: 'Pakai preset' }] : [])
            .concat(L.map(function (x) { return { t: x.name, fn: function () { GCO.pstTerap(x.name); } }; }));
        },
        kids: L.map(function (x) {
          return { id: 'dig.pst.' + x.name, t: x.name, ic: 'attr',
                   b: (x.p.rules || []).length + ' kelas · ' + (x.p.destR || []).length + ' tujuan',
                   hint: 'Disimpan ' + x.tgl + ' · lebar minimum ' + x.p.mmw + ' m',
                   menu: function () { return [{ t: 'Pakai preset ini', fn: function () { GCO.pstTerap(x.name); } },
                                               { sep: 1 },
                                               { t: 'Hapus preset ini', danger: 1, fn: function () { GCO.pstHapus(x.name); } }]; } };
        }) }
    ];
  };
  /* di bawah Laporan Grade x Tonnage: ringkasan harian */
  window.gcoRepTree = function () {
    return [{ id: 'rep.day', t: 'Ringkasan harian (flitch aktif)', ic: 'report',
      hint: 'Satu halaman: ton & kadar per material dan per tujuan, plus rencana vs aktual as-mined flitch ini',
      go: function () { GCO.dayDlg(); },
      card: { acts: [{ t: 'Buka ringkasan harian…', pri: 1, fn: function () { GCO.dayDlg(); } },
                     { t: 'Export CSV', fn: function () { GCO.dayCsv(); } }] },
      menu: function () { return [{ t: 'Buka ringkasan harian…', fn: function () { GCO.dayDlg(); } },
                                  { t: '↓ Export CSV', fn: function () { GCO.dayCsv(); } }]; } }];
  };
})();
