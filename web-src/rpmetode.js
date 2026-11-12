/* ================= REPORTING BM: BANDINGKAN METODE TONASE (Surpac vs presisi GC-Ex) =================
   Modul bersama GC-Ex Block Model dan GC-Ex Drill Hole (dipasang sesudah modul Reporting BM).

   Latar belakangnya pekerjaan nyata: pernah ada sengketa angka volume & tonase antara hitungan
   Surpac dan hitungan GC-Ex untuk block model yang SAMA. Penyebabnya bukan salah hitung, melainkan
   dua aturan yang berbeda di blok perbatasan:

     - cara Surpac  : blok dihitung UTUH berdasarkan titik pusatnya. Blok yang separuhnya di luar
                      solid tetap dihitung 100% -- ore atau waste, tidak ada di antaranya.
     - cara GC-Ex   : blok perbatasan ditimbang dengan proporsi volumenya yang benar-benar di dalam
                      solid (atribut sb_frac dari sub-blocking), jadi 0,35 blok ore dan 0,65 blok
                      waste.

   Di tab Dig block, kedua cara itu sudah bisa dipilih dan diaudit per blok. Yang belum ada: di
   Reporting BM pemakai hanya bisa MEMILIH salah satu (sakelar sb_frac), sehingga untuk
   rekonsiliasi ia harus menghitung dua kali lalu mencatat sendiri angkanya. Tab ini menghitung
   KEDUANYA sekali jalan dan menaruh selisihnya berdampingan, supaya yang diperdebatkan jelas:
   berapa ton selisihnya, dari blok perbatasan sebanyak apa, dan berapa persen dari totalnya.

   Cara kerjanya seperti rppit.js: modul ini TIDAK menyalin mesin perhitungan Reporting. Ia hanya
   menjalankan rpRun() milik aplikasi dua kali -- sekali dengan pembobotan sb_frac dimatikan, sekali
   dinyalakan -- lalu menyimpan hasilnya. Karena mesinnya sama, angkanya pasti konsisten dengan
   laporan biasa; tidak mungkin berbeda karena salah salin rumus.

   BILA BLOCK MODEL BELUM PUNYA sb_frac: kedua cara menghasilkan angka yang sama persis, dan tab ini
   mengatakannya terang-terangan, bukan menampilkan selisih 0% seolah-olah sudah dibandingkan.     */
(function () {
  if (typeof RP === 'undefined' || typeof rpRun !== 'function') return;
  if (window.RPM) return;
  var RPM = window.RPM = { res: null, busy: false, msg: '', ci: 0 };
  var $ = function (id) { return document.getElementById(id); };
  function E(s) { return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) { return '&#' + c.charCodeAt(0) + ';'; }); }
  function N(v, d) { return v == null || !isFinite(v) ? '-' : (+v).toLocaleString('id-ID', { minimumFractionDigits: d || 0, maximumFractionDigits: d || 0 }); }

  /* Dua aplikasi memakai cara yang BERBEDA untuk sakelar pembobotan ini, dan itu harus dihormati
     apa adanya daripada menyeragamkan kode aplikasi yang sudah jalan:
       - GC-Ex Block Model : RP.o.frac bertipe boolean (tak diisi = menimbang bila sb_frac ada,
                             false = blok dihitung utuh)
       - GC-Ex Drill Hole  : RP.o.frac berisi NAMA atribut proporsinya ('' = tanpa pembobotan)
     Bentuknya ditentukan dari BAWAAN aplikasi (rpDef), bukan dari isi RP.o.frac saat itu: isi
     RP.o bisa saja sudah diubah modul lain atau sesi sebelumnya, dan menebak dari nilai yang
     sudah berubah pernah membuat pembobotan tidak kena sama sekali -- tonase "presisi" keluar
     sama persis dengan tonase "Surpac" tanpa tanda apa pun bahwa ada yang salah. Angka yang
     diam-diam salah lebih berbahaya daripada galat yang terlihat. */
  function pakaiNama() {
    try {
      if (typeof rpDef === 'function') return typeof rpDef().frac === 'string';
    } catch (e) {}
    return (window.GCEX_APP || '') === 'dh';      /* cadangan: Drill Hole memakai nama atribut */
  }

  function fracAttr() {
    var m = window.BX && BX.m;
    if (!m || !m.num) return '';
    if (m.num['sb_frac']) return 'sb_frac';
    var k = Object.keys(m.num).filter(function (n) { return /frac|prop/i.test(n); });
    return k.length ? k[0] : '';
  }

  function adaFrac() { return !!fracAttr(); }
  /* 0.24.68 / 0.24.81: cara GC-Ex juga menimbang blok di batas topografi / desain pit / DTM (web-src/rpsfrac.js) */
  function adaPermukaan() { var o = window.rpO && rpO(); return !!(o && ((o.surf && o.surf !== 'none') || (o.sx && o.sx.length))); }
  function adaGcex() { return adaFrac() || adaPermukaan(); }

  /* Jumlahkan seluruh grup satu baris cut-off. Dihitung di sini, bukan memakai fungsi penjumlah
     milik Reporting: fungsi itu global di GC-Ex Drill Hole tetapi LOKAL di dalam IIFE Reporting
     GC-Ex Block Model, sehingga memanggilnya membuat tab ini mati di Block Model -- ditangkap
     uji tools/uji/uji_metode_tonase.py. Rumusnya sama: tonase dijumlahkan, kadar ditimbang tonase. */
  function total(G) {
    var r = { n: 0, v: 0, t: 0, s: {} };
    Object.keys(G || {}).forEach(function (k) {
      var a = G[k];
      r.n += a.n; r.v += a.v; r.t += a.t;
      Object.keys(a.s || {}).forEach(function (at) {
        var q = r.s[at] || (r.s[at] = { tw: 0, w: 0 });
        q.tw += a.s[at].tw; q.w += a.s[at].w;
      });
    });
    return r;
  }

  /* Rincian proporsi di SELURUH block model: dihitung sendiri, tidak mengandalkan ringkasan
     aplikasi, karena kedua aplikasi melaporkannya dengan nama field yang berbeda. */
  function rincian() {
    var m = window.BX && BX.m, a = fracAttr();
    if (!m || !a) return null;
    var F = m.num[a], nol = 0, tepi = 0, penuh = 0, lain = 0, i, v;
    for (i = 0; i < m.n; i++) {
      v = F[i];
      if (!isFinite(v) || v < 0) { lain++; continue; }
      if (v <= 0) nol++; else if (v >= 0.999) penuh++; else tepi++;
    }
    return { attr: a, nol: nol, tepi: tepi, penuh: penuh, lain: lain, n: m.n };
  }

  /* ---------- satu kali hitung dengan pembobotan sb_frac dimatikan / dinyalakan ---------- */
  function sekali(pakaiFrac) {
    var o = rpO(); if (!o) throw new Error('Block model belum ada.');
    /* rpRun() memindahkan tab ke "Hasil" dan menggambar panelnya; simpan lalu pulihkan supaya
       tab ini tetap yang tampil (sama seperti yang dilakukan rppit.js). */
    var f0 = o.frac, sf0 = o.sfrac, sh0 = o.show, sec0 = RP.sec;
    o.frac = pakaiNama() ? (pakaiFrac ? fracAttr() : '') : !!pakaiFrac;
    o.sfrac = !!pakaiFrac;
    o.show = false;
    try { rpRun(); } finally { o.frac = f0; o.sfrac = sf0; o.show = sh0; RP.sec = sec0; }
    var R = RP.res;
    if (!R) throw new Error('Reporting tidak menghasilkan apa pun. Periksa tab Atribut dan Constraint.');
    /* hanya yang diperlukan yang disalin, supaya hasil lama tidak ikut berubah saat dihitung ulang */
    return {
      rows: R.rows.map(function (r) { var T = total(r.G); return { c: r.c, n: T.n, v: T.v, t: T.t, s: T.s }; }),
      cuts: R.cuts.slice(), atts: R.atts.slice(), unit: Object.assign({}, R.unit),
      nb: R.nb, nPart: R.nPart || 0, nSf: R.nSf || 0, lab: R.lab, sg: R.sg, gr: R.gr, frac: R.frac || ''
    };
  }

  RPM.run = function () {
    if (RPM.busy) return;
    RPM.busy = true; RPM.msg = ''; RPM.panel();
    setTimeout(function () {
      try {
        var surpac = sekali(false);           /* blok utuh menurut titik pusat */
        var presisi = adaGcex() ? sekali(true) : null;   /* ditimbang proporsi sb_frac dan / atau proporsi terhadap permukaan */
        RPM.res = {
          surpac: surpac, presisi: presisi, adaFrac: adaFrac(), adaPerm: adaPermukaan(), sfN: (rpO() && +rpO().sfN) || 4,
          attr: fracAttr(), rinci: rincian(),
          date: new Date().toLocaleString('id-ID'),
          bm: (window.BX && BX.m && BX.m.name) || ''
        };
        RPM.ci = Math.min(RPM.ci, surpac.rows.length - 1);
      } catch (e) {
        console.error(e); RPM.msg = '<span class=warn>' + E(e.message || e) + '</span>'; RPM.res = null;
      } finally { RPM.busy = false; RPM.panel(); }
    }, 10);
  };

  /* ---------- tabel perbandingan ---------- */
  function kadar(q) { return q && q.w ? q.tw / q.w : NaN; }

  function caraGcex(X) {
    return [X.adaFrac ? 'timbang ' + (X.attr || 'sb_frac') : '', X.adaPerm ? 'proporsi permukaan ' + X.sfN + '×' + X.sfN : ''].filter(Boolean).join(' + ');
  }

  function tabel() {
    var X = RPM.res; if (!X) return '';
    var S = X.surpac, P = X.presisi, at = S.atts, u = S.unit;
    var h = '<div class=rpwrap><table class="pltb rptb"><tr><th>Cut-off<br><small>' + E(S.gr) + '</small></th><th>Metode</th><th>Blok</th>' +
      '<th>Volume<br><small>m&sup3;</small></th><th>Tonase<br><small>t</small></th>' +
      at.map(function (a) { return '<th>' + E(a) + '<br><small>' + E(u[a] || 'g/t') + '</small></th>'; }).join('') + '</tr>';
    S.rows.forEach(function (rs, i) {
      var rp = P ? P.rows[i] : null;
      var baris = function (nama, r, tebal) {
        return '<tr><td>' + (tebal ? '&ge; ' + rs.c : '') + '</td><td>' + nama + '</td><td>' + N(r.n) + '</td><td>' + N(r.v) + '</td><td>' + (tebal ? '<b>' + N(r.t) + '</b>' : N(r.t)) + '</td>' +
          at.map(function (a) { return '<td>' + N(kadar(r.s[a]), 3) + '</td>'; }).join('') + '</tr>';
      };
      h += baris('Cara Surpac <small>(blok utuh, bawaan)</small>', rs, true);
      if (rp) {
          h += baris('Cara GC-Ex <small>(' + E(caraGcex(X)) + ')</small>', rp, false);
        var dv = rp.v - rs.v, dt = rp.t - rs.t;
        h += '<tr class=tot><td></td><td>Selisih</td><td>' + (rp.n - rs.n) + '</td><td>' + N(dv) +
          ' <small>(' + (rs.v ? (dv / rs.v * 100).toFixed(1) : '0') + '%)</small></td><td><b>' + N(dt) +
          ' <small>(' + (rs.t ? (dt / rs.t * 100).toFixed(1) : '0') + '%)</small></b></td>' +
          at.map(function (a) {
            var a1 = kadar(rs.s[a]), a2 = kadar(rp.s[a]);
            return '<td>' + (isFinite(a1) && isFinite(a2) ? N(a2 - a1, 3) : '-') + '</td>';
          }).join('') + '</tr>';
      }
    });
    return h + '</table></div>';
  }

  RPM.csv = function () {
    var X = RPM.res; if (!X) return;
    var S = X.surpac, P = X.presisi, at = S.atts, u = S.unit;
    var L = ['# Reporting BM - perbandingan metode tonase (Surpac vs presisi GC-Ex)',
             '# Block model: ' + X.bm, '# Constraint: ' + [S.lab, S.sg].filter(Boolean).join(' · '),
             '# Tanggal: ' + X.date,
             '# Cara Surpac (bawaan, audit) = blok dihitung utuh menurut titik pusatnya',
             '# Cara GC-Ex = blok perbatasan ditimbang proporsi volume: ' + caraGcex(X)];
    if (!X.presisi) L.push('# CATATAN: tidak ada sb_frac maupun batas permukaan, jadi kedua metode identik.');
    L.push(['CUTOFF', 'METODE', 'BLOK', 'VOLUME_M3', 'TONASE_T'].concat(
      at.map(function (a) { return a + '_' + String(u[a] || 'g/t').replace('/', '_'); })).join(','));
    var tulis = function (c, nama, r) {
      L.push([c, '"' + nama + '"', r.n, r.v.toFixed(1), r.t.toFixed(1)].concat(
        at.map(function (a) { var g = kadar(r.s[a]); return isFinite(g) ? g.toFixed(4) : ''; })).join(','));
    };
    S.rows.forEach(function (rs, i) {
      tulis(rs.c, 'Cara Surpac', rs);
      if (P) {
        tulis(rs.c, 'Cara GC-Ex', P.rows[i]);
        var rp = P.rows[i];
        L.push([rs.c, '"Selisih (GC-Ex - Surpac)"', rp.n - rs.n, (rp.v - rs.v).toFixed(1),
                (rp.t - rs.t).toFixed(1)].concat(at.map(function () { return ''; })).join(','));
      }
    });
    if (window.dgDl) dgDl(L.join('\r\n') + '\r\n', 'Reporting_BM_metode_tonase_' +
      String(X.bm).replace(/[^A-Za-z0-9_-]+/g, '_') + '.csv', 'text/csv');
  };

  /* ---------- panel ---------- */
  RPM.open = function () { RP.sec = 'm'; if (window.uiTab) uiTab('Rep'); RPM.panel(); };
  RPM.panel = function () {
    if (!window.RP || RP.sec !== 'm') { if (window.rpPanel) rpPanel(); return; }
    var b = $('rpBody'); if (!b) return;
    var m = window.BX && BX.m;
    if (!m) { b.innerHTML = '<div class="box gmstate">Belum ada block model.</div>'; return; }
    var h = '<i id=rpmBody hidden></i><div class="uitabs rptabs">' +
      '<button onclick="RP.sec=\'1\';rpPanel()">Atribut</button>' +
      '<button onclick="RP.sec=\'c\';rpPanel()">Constraint</button>' +
      '<button onclick="RP.sec=\'2\';rpPanel()">Hasil</button>' +
      (window.RPX ? '<button class=rpxtab onclick="RPX.open()">Pit &amp; progres</button>' : '') +
      '<button class=on>Metode tonase</button></div>';
    h += '<div class=hint style="margin:4px 0 8px">Memakai <b>atribut, cut-off, pengelompokan, domain, poligon, permukaan dan SG</b> yang sudah diatur di tab <b>Atribut</b> dan <b>Constraint</b>. ' +
      'Yang dibandingkan di sini hanya <b>aturan blok perbatasan</b>.</div>';
    h += '<div class="box gmstate"><b>Cara Surpac</b> (bawaan, untuk audit) &mdash; blok dihitung <b>utuh</b> berdasarkan titik pusatnya (Surpac <i>Keep partial = False</i>).<br>' +
      '<b>Cara GC-Ex</b> &mdash; blok perbatasan ditimbang <b>proporsi volumenya</b>: ' +
      [adaFrac() ? 'di dalam solid (atribut <code>' + E(fracAttr()) + '</code>)' : '',
       adaPermukaan() ? 'terhadap topografi / desain pit / batas DTM (kolom ' + ((rpO() && +rpO().sfN) || 4) + '&times;' + ((rpO() && +rpO().sfN) || 4) + ', atur di tab <b>Constraint</b>)' : ''].filter(Boolean).join(' dan ') +
      (adaGcex() ? '' : 'tidak ada yang bisa ditimbang') + '.</div>';
    if (!adaGcex()) {
      h += '<div class="box gmstate"><span class=warn>Block model ini belum punya atribut <code>sb_frac</code>.</span> ' +
        'Tidak ada pula batas permukaan (topografi / pit / DTM) di tab <b>Constraint</b>, jadi kedua metode menghasilkan angka yang <b>sama persis</b>. ' +
        'Hitung proporsi volume lebih dulu di <b>GC-Ex Drill Hole &rsaquo; Block Model &rsaquo; Hitung proporsi volume ore per blok (sb_frac)</b>, ' +
        'simpan block model-nya, lalu kembali ke sini.</div>';
    }
    if (RPM.msg) h += '<div class="box gmstate">' + RPM.msg + '</div>';
    h += '<button class=btn-pri style="width:100%;height:32px;margin-top:8px" onclick="RPM.run()" ' + (RPM.busy ? 'disabled' : '') +
      '>&#9654; ' + (RPM.busy ? 'Menghitung…' : 'Hitung kedua metode') + '</button>';
    var X = RPM.res;
    if (X) {
      var S = X.surpac;
      h += '<h4 style="margin-top:10px">Hasil</h4><div class="box gmstate rpsum"><small>' +
        E([S.lab, S.sg].filter(Boolean).join(' · ')) + '<br>' + E(X.date) + '</small></div>';
      if (X.presisi && X.adaPerm) h += '<div class="box gmstate"><b>Blok di batas permukaan</b>: ' + N(X.presisi.nSf) + ' blok dihitung sebagian pada cara GC-Ex. ' +
        'Blok yang titik pusatnya di luar batas tetapi sebagian volumenya di dalam ikut terhitung sebagian, sehingga jumlah blok bisa bertambah.</div>';
      if (X.presisi && X.rinci) {
        var R = X.rinci;
        h += '<div class="box gmstate"><b>Dari mana selisihnya</b><br>Atribut <code>' + E(R.attr) + '</code> di ' +
          N(R.n) + ' blok: <b>' + N(R.penuh) + '</b> seluruhnya di dalam solid (proporsi 1), <b>' + N(R.tepi) +
          '</b> di perbatasan (0&ndash;1), <b>' + N(R.nol) + '</b> seluruhnya di luar (proporsi 0)' +
          (R.lain ? ', ' + N(R.lain) + ' tanpa nilai' : '') + '.' +
          '<br><span class=warn>Blok berproporsi 0 tidak dilaporkan sama sekali</span> pada cara GC-Ex. ' +
          'Jadi bila <code>' + E(R.attr) + '</code> hanya mencakup solid vein, baris <b>Cara GC-Ex</b> ' +
          'melaporkan material <b>di dalam solid saja</b>, sedangkan baris <b>Cara Surpac</b> melaporkan ' +
          'semua blok yang lolos constraint &mdash; termasuk waste di luar solid. Selisih sebesar itu wajar ' +
          'dan bukan tanda salah hitung; bandingkan keduanya hanya sesudah constraint domainnya disamakan ' +
          '(tab <b>Constraint</b>).</div>';
      }
      h += tabel();
      h += '<div class="g2 f" style="margin-top:8px"><button class=btn-pri onclick="RPM.csv()">&#8681; Export CSV</button>' +
        '<button onclick="RP.sec=\'2\';rpPanel()">Laporan rinci terakhir</button></div>';
      h += '<div class=hint style="margin-top:6px">Untuk audit dan rekonsiliasi dengan report Surpac: pakai baris <b>Cara Surpac</b>. ' +
        'Untuk dig plan dan perhitungan dilusi / ore loss: pakai <b>Cara GC-Ex</b>, karena di situlah blok perbatasan dihitung seadanya. ' +
        'Perbandingan yang paling berarti: batasi domain ke solid yang sama di tab <b>Constraint</b>, lalu lihat selisihnya &mdash; ' +
        'yang tersisa barulah pengaruh aturan blok perbatasan.</div>';
    }
    b.innerHTML = h;
  };

  /* Tab tambahan disisipkan ke bilah tab Reporting tanpa mengubah rpPanel-nya. Dipasang lewat
     pengamat DOM, bukan pembungkus window.rpPanel: di Block Model, rpPanel dipanggil lewat ikatan
     LOKAL di dalam IIFE-nya sehingga pembungkus window saja tidak kena (pelajaran dari rppit.js). */
  (function () {
    function pasangTab() {
      var bar = document.querySelector('#rpBody .rptabs');
      if (!bar || bar.querySelector('.rpmtab')) return;
      if (document.getElementById('rpmBody')) return;    /* panel milik tab ini sendiri */
      var b2 = document.createElement('button');
      b2.className = 'rpmtab'; b2.innerHTML = 'Metode tonase';
      b2.title = 'Bandingkan tonase cara Surpac (blok utuh, bawaan) dengan cara GC-Ex (proporsi volume blok perbatasan)';
      b2.onclick = function () { RPM.open(); };
      bar.appendChild(b2);
    }
    var mo = new MutationObserver(pasangTab);
    function mulai() {
      var b = document.getElementById('rpBody');
      if (!b) { setTimeout(mulai, 400); return; }
      mo.observe(b, { childList: true, subtree: true });
      pasangTab();
    }
    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', mulai);
    else mulai();
  })();
})();
