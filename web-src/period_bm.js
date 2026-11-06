/* ============ LAPORAN PERIODE (MINGGUAN / BULANAN) — GC-Ex Block Model ============
   Untuk Junior Grade Control / Short Term Mine Planner: menjumlahkan apa yang BENAR-BENAR tergali
   dalam satu rentang tanggal, dari register as-mined. Bukan pelaporan sumber daya.

   Sumbernya data yang sudah ada, tidak ada perhitungan baru:
     - tiap poligon as-mined menyimpan tanggal, shift (DS / NS), pit, blok, RL flitch, kode ore dan
       tujuan material (amBndAdd -> web-src/gcex_base.html, amD().bnd);
     - tonase, volume dan kadar per poligon dihitung amRun() dan tersimpan di x.st;
     - kadar multi-unsur dijumlahkan dengan elAgg() (multiel.js), sama seperti register & PDF,
       supaya angka di laporan periode TIDAK pernah berbeda dari angka di register.

   Satu hal yang harus jujur disebut: amRun() menghitung poligon pada FLITCH AKTIF saja. Poligon
   dari flitch lain yang belum pernah dihitung tidak punya x.st, jadi tonasenya belum ada. Modul ini
   menghitung berapa poligon yang begitu, MENAMPILKANNYA, dan menyediakan tombol untuk mengisinya
   (membuka tiap flitch lalu menjalankan as-mined, dan mengembalikan flitch semula). Laporan tidak
   pernah diam-diam melewatkan poligon.                                                            */
(function () {
  if (window.PRD || typeof BX === 'undefined') return;
  var PRD = window.PRD = { o: { kind: 'bulan', from: '', to: '', grp: 'tgl', prev: true, tgt: '', tgtG: '', tren: true }, res: null, msg: '' };
  var $ = function (i) { return document.getElementById(i); };
  function E(s) { return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) { return '&#' + c.charCodeAt(0) + ';'; }); }
  function N(v, d) { return (v == null || !isFinite(v)) ? '-' : (+v).toLocaleString('id-ID', { minimumFractionDigits: d || 0, maximumFractionDigits: d || 0 }); }
  function fn(n) { return typeof window[n] === 'function'; }

  /* ---------- rentang tanggal ---------- */
  function iso(d) { var p = function (n) { return ('0' + n).slice(-2); }; return d.getFullYear() + '-' + p(d.getMonth() + 1) + '-' + p(d.getDate()); }
  function hari(s, n) { var d = new Date(s + 'T00:00:00'); d.setDate(d.getDate() + n); return iso(d); }
  function senin(d) { var x = new Date(d.getFullYear(), d.getMonth(), d.getDate()), w = (x.getDay() + 6) % 7; x.setDate(x.getDate() - w); return x; }
  function pekan(s) {
    /* nomor pekan ISO, dipakai sebagai kunci grup "per minggu" */
    var d = new Date(s + 'T00:00:00'); var t = new Date(d.getFullYear(), d.getMonth(), d.getDate());
    t.setDate(t.getDate() + 3 - ((t.getDay() + 6) % 7));
    var w1 = new Date(t.getFullYear(), 0, 4);
    var n = 1 + Math.round(((t - w1) / 86400000 - 3 + ((w1.getDay() + 6) % 7)) / 7);
    return t.getFullYear() + '-W' + ('0' + n).slice(-2);
  }
  PRD.rentang = function (kind) {
    var now = new Date(), o = PRD.o;
    if (kind === 'minggu' || kind === 'minggu_lalu') {
      var s = senin(now); if (kind === 'minggu_lalu') s.setDate(s.getDate() - 7);
      var e = new Date(s); e.setDate(e.getDate() + 6);
      return { from: iso(s), to: iso(e), lab: (kind === 'minggu' ? 'Minggu ini' : 'Minggu lalu') + ' (' + pekan(iso(s)) + ')' };
    }
    if (kind === 'bulan' || kind === 'bulan_lalu') {
      var y = now.getFullYear(), m = now.getMonth() + (kind === 'bulan_lalu' ? -1 : 0);
      var a = new Date(y, m, 1), b = new Date(y, m + 1, 0);
      return { from: iso(a), to: iso(b), lab: (kind === 'bulan' ? 'Bulan ini' : 'Bulan lalu') + ' (' + iso(a).slice(0, 7) + ')' };
    }
    return { from: o.from || iso(now), to: o.to || iso(now), lab: 'Kustom' };
  };
  function R() { return PRD.rentang(PRD.o.kind); }

  /* ---------- poligon dalam rentang ---------- */
  function dalam(x, r) { var d = String(x.date || ''); return d >= r.from && d <= r.to; }
  function semua() { try { return (fn('amBndAll') ? amBndAll() : []).filter(function (x) { return x.on !== false; }); } catch (e) { return []; } }

  function flKunci(x) { return (+x.top).toFixed(3) + '|' + (+x.bot).toFixed(3); }
  PRD.belum = function (r) {
    var F = {}, n = 0;
    semua().forEach(function (x) { if (!dalam(x, r) || x.st) return; F[flKunci(x)] = { top: +x.top, bot: +x.bot }; n++; });
    return { fl: Object.keys(F).map(function (k) { return F[k]; }), n: n };
  };

  /* Isi tonase poligon yang belum dihitung. Memakai am3RunAll() milik aplikasi (am3d.js) -- jalur
     yang sama dengan tombol "Hitung semua flitch" di panel As-Mined, jadi hasilnya pasti identik.
     Catatan: am3RunAll menghitung SEMUA flitch yang punya poligon, bukan hanya yang di rentang ini. */
  PRD.isi = function (sesudah) {
    var r = R(), B = PRD.belum(r);
    if (!B.fl.length) { if (sesudah) sesudah(0); return; }
    if (fn('am3RunAll')) {
      PRD.msg = 'Menghitung semua flitch yang punya poligon\u2026'; panel();
      setTimeout(function () {
        try { am3RunAll(); } catch (e) { console.error(e); }
        PRD.msg = ''; PRD.run();
        if (sesudah) sesudah(B.fl.length);
      }, 60);
      return;
    }
    if (!fn('lySet') || !fn('lyApply') || !fn('amRun') || !fn('lyBench')) { alert('Fungsi flitch / as-mined belum siap.'); return; }
    var asal = null; try { asal = lyBench(); } catch (e) {}
    var buka = function (g) { lySet('fh', +(g.top - g.bot).toFixed(3)); try { lyU().bot = ''; } catch (e) {} lySet('top', +(+g.top).toFixed(3)); lyApply(); };
    PRD.msg = 'Menghitung ' + B.fl.length + ' flitch…'; panel();
    var i = 0;
    (function next() {
      if (i >= B.fl.length) {
        if (asal) { try { buka({ top: asal[0], bot: asal[1] }); } catch (e) {} }
        PRD.msg = B.fl.length + ' flitch dihitung.';
        setTimeout(function () { if (sesudah) sesudah(B.fl.length); else PRD.run(); }, 300);
        return;
      }
      var g = B.fl[i++];
      try { buka(g); } catch (e) {}
      setTimeout(function () { try { amRun(true); } catch (e) {} setTimeout(next, 120); }, 160);
    })();
  };

  /* ---------- kunci grup ---------- */
  var GRP = [['tgl', 'Per tanggal'], ['minggu', 'Per minggu'], ['shift', 'Per shift (DS / NS)'],
             ['fl', 'Per flitch (RL)'], ['dest', 'Per tujuan material'], ['ore', 'Per kode ore'], ['pit', 'Per pit'], ['none', 'Total saja']];
  function kunci(q) {
    var x = q.x, g = PRD.o.grp;
    if (g === 'tgl') return String(x.date || '(tanpa tanggal)');
    if (g === 'minggu') return x.date ? pekan(String(x.date)) : '(tanpa tanggal)';
    if (g === 'shift') return (/^N/i.test(x.shift || '') ? 'NS (malam)' : 'DS (siang)');
    if (g === 'fl') return 'RL ' + N(x.top, 1) + ' – ' + N(x.bot, 1);
    if (g === 'dest') return String(q.lok || q.dest || '(tanpa tujuan)');
    if (g === 'ore') return String(q.ore || '(tanpa kode)');
    if (g === 'pit') return String(x.pit || '(tanpa pit)');
    return 'Total';
  }

  /* ---------- hitung ---------- */
  function agg(rows) {
    var A = fn('elAgg') ? elAgg() : { t: 0, n: 0, add: function (r, t) { this.t += (+t || 0); this.n++; }, g: function () { return NaN; }, met: function () { return NaN; } };
    var bcm = 0;
    rows.forEach(function (q) {
      var st = q.x.st || {};
      A.add({ t: q.ton, el: st.el || {}, elw: st.elw || {} }, q.ton);
      bcm += (+q.bcm || 0);
    });
    A.bcm = bcm;
    return A;
  }
  function kumpul(r) {
    var L = [];
    try {
      (fn('amAllInfo') ? amAllInfo() : []).forEach(function (q) {
        if (!q || !q.x || !dalam(q.x, r)) return;
        if (!q.x.st) return;                       /* belum dihitung: dilaporkan terpisah, tidak didiamkan */
        if (!isFinite(q.ton) || q.ton <= 0) return;
        L.push(q);
      });
    } catch (e) { console.error(e); }
    return L;
  }

  PRD.run = function () {
    if (!(BX && BX.m)) { alert('Belum ada block model.'); return; }
    var r = R(), L = kumpul(r), B = PRD.belum(r);
    var G = {}, urut = [];
    L.forEach(function (q) { var k = kunci(q); if (!G[k]) { G[k] = []; urut.push(k); } G[k].push(q); });
    urut.sort();
    var baris = urut.map(function (k) { return { k: k, a: agg(G[k]), n: G[k].length }; });
    var tot = agg(L);

    /* periode sebelumnya dengan panjang yang sama, untuk pembanding */
    var band = null;
    if (PRD.o.prev) {
      var pjg = Math.round((new Date(r.to + 'T00:00:00') - new Date(r.from + 'T00:00:00')) / 86400000) + 1;
      var r2 = { from: hari(r.from, -pjg), to: hari(r.from, -1) };
      band = { r: r2, a: agg(kumpul(r2)) };
    }
    /* tren per hari (laporan mingguan) atau per minggu (bulanan): supaya laporan periode bisa
       menunjukkan POLA, bukan hanya satu angka total. */
    var TR = {}, trKey = (PRD.o.kind === 'bulan' || PRD.o.kind === 'bulan_lalu') ? pekan : function (d) { return d; };
    L.forEach(function (q) { var k = trKey(String(q.x.date || '')); TR[k] = (TR[k] || 0) + (+q.ton || 0); });
    var tren = Object.keys(TR).sort().map(function (k) { return { k: k, t: TR[k] }; });

    var tg = parseFloat(String(PRD.o.tgt).replace(',', '.')), tgG = parseFloat(String(PRD.o.tgtG).replace(',', '.'));
    var capai = null;
    if (isFinite(tg) && tg > 0) {
      capai = { t: tg, p: 100 * tot.t / tg, sel: tot.t - tg, g: isFinite(tgG) ? tgG : null,
                gAkt: (fn('amU') ? tot.g(amU().attr || '') : NaN) };
    }
    PRD.res = { r: r, baris: baris, tot: tot, band: band, belum: B, grp: PRD.o.grp, tren: tren, capai: capai,
                els: fn('elAmX') ? elAmX() : [], prim: (fn('amU') ? (amU().attr || '') : ''),
                tgl: new Date().toLocaleString('id-ID'), bm: BX.m.name };
    PRD.msg = '';
    panel();
  };

  /* ---------- tabel ---------- */
  function tabel() {
    var S = PRD.res; if (!S) return '<div class=hint>Tekan <b>Hitung</b> untuk menyusun laporan.</div>';
    var els = S.els, lab = {};
    GRP.forEach(function (g) { lab[g[0]] = g[1]; });
    var hd = '<tr><th>' + E(lab[S.grp] || 'Grup') + '</th><th>Poligon</th><th>Ton</th><th>BCM</th>' +
      (S.prim ? '<th>' + E(S.prim) + '</th>' : '') +
      els.map(function (a) { return '<th>' + E(a) + (fn('elUnit') && elUnit(a) ? ' (' + E(elUnit(a)) + ')' : '') + '</th>'; }).join('') + '</tr>';
    var sel = function (a) {
      var A = a.a;
      return '<td>' + N(a.n) + '</td><td>' + N(A.t) + '</td><td>' + N(A.bcm) + '</td>' +
        (S.prim ? '<td>' + (fn('elF') ? elF(S.prim, A.g(S.prim)) : N(A.g(S.prim), 3)) + '</td>' : '') +
        els.map(function (q) { return '<td>' + (fn('elF') ? elF(q, A.g(q)) : N(A.g(q), 3)) + '</td>'; }).join('');
    };
    var h = '<table class=pltb>' + hd +
      S.baris.map(function (b) { return '<tr><td><b>' + E(b.k) + '</b></td>' + sel(b) + '</tr>'; }).join('') +
      '<tr style="font-weight:700;background:var(--sf2,#eef2f7)"><td>TOTAL</td>' + sel({ a: S.tot, n: S.baris.reduce(function (s, b) { return s + b.n; }, 0) }) + '</tr>' +
      '</table>';
    if (S.band) {
      var d = S.tot.t - S.band.a.t, p = S.band.a.t > 0 ? 100 * d / S.band.a.t : null;
      h += '<div class=hint style="margin-top:4px">Periode sebelumnya (' + E(S.band.r.from) + ' … ' + E(S.band.r.to) + '): <b>' +
        N(S.band.a.t) + '</b> ton dari ' + N(S.band.a.n) + ' poligon &middot; sekarang <b>' + N(S.tot.t) + '</b> ton &middot; selisih <b>' +
        (d >= 0 ? '+' : '') + N(d) + ' ton' + (p === null ? '' : ' (' + (p >= 0 ? '+' : '') + N(p, 1) + '%)') + '</b></div>';
    }
    if (S.capai) {
      var C = S.capai, warna = C.p >= 100 ? '#2b8a3e' : C.p >= 90 ? '#e8590c' : '#b42318';
      h += '<div class=box><b>Target periode ' + N(C.t) + ' ton</b> &middot; aktual <b>' + N(S.tot.t) + ' ton</b> &middot; ' +
        'pencapaian <b style="color:' + warna + '">' + N(C.p, 1) + '%</b> (' + (C.sel >= 0 ? '+' : '') + N(C.sel) + ' ton)' +
        (C.g != null && isFinite(C.gAkt) ? '<br>Target kadar ' + N(C.g, 3) + ' &middot; aktual ' + N(C.gAkt, 3) + ' &middot; ' +
          (C.gAkt >= C.g ? '<b style="color:#2b8a3e">di atas target</b>' : '<b style="color:#e8590c">di bawah target</b>') : '') + '</div>';
    }
    if (PRD.o.tren && S.tren && S.tren.length > 1) {
      var mx = Math.max.apply(null, S.tren.map(function (x) { return x.t; })) || 1;
      h += '<h4>Tren ' + (String(S.r.lab || '').indexOf('Bulan') === 0 ? 'per minggu' : 'per hari') + '</h4><div class=prdtren>' +
        S.tren.map(function (x) {
          return '<div title="' + E(x.k) + ': ' + N(x.t) + ' t"><i style="height:' + Math.max(2, Math.round(60 * x.t / mx)) + 'px"></i><small>' +
                 E(String(x.k).replace(/^[0-9]{4}-/, '')) + '</small></div>';
        }).join('') + '</div><div class=hint>Tertinggi ' + N(mx) + ' t. Arahkan kursor untuk melihat angkanya.</div>';
    }
    if (S.belum.n) {
      h += '<div class=box><b>' + N(S.belum.n) + ' poligon belum punya tonase</b> (ada di ' + S.belum.fl.length +
        ' flitch yang belum pernah dihitung as-mined). Poligon itu <b>tidak</b> ikut dijumlahkan di atas. ' +
        '<button onclick="PRD.isi()">Hitung semua flitch sekarang</button></div>';
    }
    return h;
  }

  PRD.csv = function () {
    var S = PRD.res; if (!S) { alert('Hitung laporannya dulu.'); return; }
    var els = S.els, q = function (v) { v = String(v == null ? '' : v); return /[",\n]/.test(v) ? '"' + v.replace(/"/g, '""') + '"' : v; };
    var H = ['Grup', 'Poligon', 'Ton', 'BCM'].concat(S.prim ? [S.prim] : []).concat(els);
    var L = ['Laporan periode,' + q(S.r.lab), 'Rentang,' + S.r.from + ' s/d ' + S.r.to, 'Block model,' + q(S.bm),
             'Dibuat,' + q(S.tgl), 'Dikelompokkan,' + q(S.grp), ''];
    L.push(H.map(q).join(','));
    var row = function (nama, a, n) {
      return [nama, n, Math.round(a.t), Math.round(a.bcm)].concat(S.prim ? [isFinite(a.g(S.prim)) ? a.g(S.prim).toFixed(4) : ''] : '')
        .concat(els.map(function (x) { var v = a.g(x); return isFinite(v) ? v.toFixed(4) : ''; })).map(q).join(',');
    };
    S.baris.forEach(function (b) { L.push(row(b.k, b.a, b.n)); });
    L.push(row('TOTAL', S.tot, S.baris.reduce(function (s, b) { return s + b.n; }, 0)));
    if (S.band) L.push('', 'Periode sebelumnya,' + S.band.r.from + ' s/d ' + S.band.r.to, row('TOTAL sebelumnya', S.band.a, S.band.a.n));
    if (S.capai) L.push('', 'Target ton,' + Math.round(S.capai.t), 'Aktual ton,' + Math.round(S.tot.t),
                        'Pencapaian persen,' + S.capai.p.toFixed(1), 'Selisih ton,' + Math.round(S.capai.sel));
    if (S.tren && S.tren.length) { L.push('', 'Tren,Ton'); S.tren.forEach(function (x) { L.push(q(x.k) + ',' + Math.round(x.t)); }); }
    if (S.belum.n) L.push('', 'Belum dihitung,' + S.belum.n + ' poligon di ' + S.belum.fl.length + ' flitch (tidak ikut dijumlahkan)');
    var b = new Blob(['﻿' + L.join('\r\n')], { type: 'text/csv' }), a = document.createElement('a');
    a.href = URL.createObjectURL(b); a.download = 'GCEx_LaporanPeriode_' + S.r.from + '_' + S.r.to + '.csv';
    document.body.appendChild(a); a.click(); setTimeout(function () { URL.revokeObjectURL(a.href); a.remove(); }, 800);
  };

  PRD.set = function (k, v) { PRD.o[k] = v; if (k === 'kind' || k === 'from' || k === 'to' || k === 'grp') PRD.res = null; panel(); };

  /* ---------- dialog ---------- */
  function panel() {
    var d = $('prdDlg'); if (!d || d.style.display === 'none') return;
    var r = R(), o = PRD.o, B = PRD.belum(r);
    var sel = function (id, opts, cur, oc) {
      return '<select onchange="' + oc + '">' + opts.map(function (q) {
        return '<option value="' + q[0] + '"' + (String(cur) === String(q[0]) ? ' selected' : '') + '>' + E(q[1]) + '</option>';
      }).join('') + '</select>';
    };
    $('prdBody').innerHTML =
      '<div class="g2 f"><div><label>Periode</label>' +
      sel('k', [['minggu', 'Minggu ini'], ['minggu_lalu', 'Minggu lalu'], ['bulan', 'Bulan ini'], ['bulan_lalu', 'Bulan lalu'], ['kustom', 'Kustom…']], o.kind, "PRD.set('kind',this.value)") +
      '<div class=hint>' + E(r.lab) + ': <b>' + E(r.from) + '</b> s/d <b>' + E(r.to) + '</b></div></div>' +
      '<div><label>Kelompokkan</label>' + sel('g', GRP, o.grp, "PRD.set('grp',this.value)") +
      '<div class=hint>Kadar dijumlahkan ditimbang tonase, sama seperti register.</div></div></div>' +
      (o.kind === 'kustom' ? '<div class="g2 f"><div><label>Dari</label><input type=date value="' + E(o.from) + '" onchange="PRD.set(\'from\',this.value)"></div>' +
        '<div><label>Sampai</label><input type=date value="' + E(o.to) + '" onchange="PRD.set(\'to\',this.value)"></div></div>' : '') +
      '<div class="g2 f"><div><label>Target ton periode ini</label><input type=number step=any value="' + E(o.tgt) + '" placeholder="kosong = tanpa target" onchange="PRD.set(\'tgt\',this.value)"></div>' +
      '<div><label>Target kadar</label><input type=number step=any value="' + E(o.tgtG) + '" placeholder="opsional" onchange="PRD.set(\'tgtG\',this.value)"></div></div>' +
      '<label class=sw><input type=checkbox ' + (o.prev ? 'checked' : '') + ' onchange="PRD.set(\'prev\',this.checked)">Bandingkan dengan periode sebelumnya (panjang sama)</label>' +
      '<label class=sw><input type=checkbox ' + (o.tren ? 'checked' : '') + ' onchange="PRD.set(\'tren\',this.checked)">Tampilkan tren (per hari untuk mingguan, per minggu untuk bulanan)</label>' +
      (B.n ? '<div class=box><b>' + N(B.n) + ' poligon</b> dalam rentang ini belum punya tonase (' + B.fl.length +
        ' flitch belum dihitung). <button onclick="PRD.isi()">Hitung sekarang</button></div>' : '') +
      (PRD.msg ? '<div class=hint><b>' + E(PRD.msg) + '</b></div>' : '') +
      '<div style="margin-top:6px">' + tabel() + '</div>';
  }
  PRD.dlg = function () {
    var d = $('prdDlg');
    if (!d) { d = document.createElement('div'); d.id = 'prdDlg'; d.className = 'bxdlg'; document.body.appendChild(d); }
    d.innerHTML = '<div class=impBox style=width:min(960px,100%)><div class=impHead><div class=impBrand><div><b>Laporan periode (mingguan / bulanan)</b>' +
      '<small>Menjumlahkan apa yang benar-benar tergali dari register as-mined: ton, BCM dan kadar per tanggal, minggu, shift, flitch, tujuan material, kode ore atau pit.</small>' +
      '</div></div><button class="ib ghost" onclick="PRD.close()">Tutup</button></div>' +
      '<div class=impBody id=prdBody></div>' +
      '<div class=impFoot><div class=hint></div><button class=ib onclick="PRD.run()">Hitung</button>' +
      '<button class=ib onclick="PRD.csv()">&#8681; CSV</button><button class=ib onclick="PRD.close()">Selesai</button></div></div>';
    d.style.display = 'flex';
    panel();
  };
  PRD.close = function () { var d = $('prdDlg'); if (d) d.style.display = 'none'; };

  (function () {
    var st = document.createElement('style');
    st.textContent = '.prdtren{display:flex;align-items:flex-end;gap:3px;margin:4px 0 2px;min-height:76px}' +
      '.prdtren>div{display:flex;flex-direction:column;align-items:center;justify-content:flex-end;flex:1;min-width:14px}' +
      '.prdtren i{display:block;width:100%;background:var(--mj,#f0c047);border:1px solid var(--mjln,#d6a12b);border-radius:2px 2px 0 0}' +
      '.prdtren small{font-size:8.5px;color:var(--mu,#5b6478);margin-top:2px;white-space:nowrap}';
    document.head.appendChild(st);
  })();

  /* ---------- node Project Tree, di bawah Register & Laporan As-Mined ---------- */
  window.prdTree = function () {
    var r = R(), n = 0, B = { n: 0, fl: [] };
    try { n = kumpul(r).length; B = PRD.belum(r); } catch (e) {}
    return [{
      id: 'reg.prd', t: 'Laporan periode (mingguan / bulanan)', ic: 'report',
      card: { why: 'Belum ada poligon as-mined yang sudah dihitung pada periode ini.',
              acts: [{ t: 'Buka laporan periode\u2026', pri: 1, fn: function () { PRD.dlg(); } },
                     { t: 'Minggu ini', fn: function () { PRD.o.kind = 'minggu'; PRD.res = null; PRD.dlg(); PRD.run(); } },
                     { t: 'Bulan ini', fn: function () { PRD.o.kind = 'bulan'; PRD.res = null; PRD.dlg(); PRD.run(); } }] },
      b: r.lab + (n ? ' · ' + n + ' poligon' : ''),
      dim: !n,
      hint: 'Ton, BCM dan kadar per tanggal / minggu / shift / flitch / tujuan material, dari register as-mined' +
            (B.n ? ' — ' + B.n + ' poligon belum dihitung' : ''),
      go: function () { PRD.dlg(); },
      menu: function () {
        return [
          { t: 'Buka laporan periode…', fn: function () { PRD.dlg(); } },
          { sep: 1 }, { h: 'Periode cepat' },
          { t: 'Minggu ini', on: PRD.o.kind === 'minggu', fn: function () { PRD.o.kind = 'minggu'; PRD.res = null; PRD.dlg(); PRD.run(); } },
          { t: 'Minggu lalu', on: PRD.o.kind === 'minggu_lalu', fn: function () { PRD.o.kind = 'minggu_lalu'; PRD.res = null; PRD.dlg(); PRD.run(); } },
          { t: 'Bulan ini', on: PRD.o.kind === 'bulan', fn: function () { PRD.o.kind = 'bulan'; PRD.res = null; PRD.dlg(); PRD.run(); } },
          { t: 'Bulan lalu', on: PRD.o.kind === 'bulan_lalu', fn: function () { PRD.o.kind = 'bulan_lalu'; PRD.res = null; PRD.dlg(); PRD.run(); } },
          { sep: 1 },
          { t: 'Hitung flitch yang belum dihitung (' + B.fl.length + ')', dis: !B.fl.length, fn: function () { PRD.isi(); } },
          { t: '↓ Export CSV', dis: !PRD.res, fn: function () { PRD.csv(); } }
        ];
      }
    }];
  };
})();
