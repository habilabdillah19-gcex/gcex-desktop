/* GC-Ex Drill Hole Ultimate — KLASIFIKASI SUMBER DAYA (Measured / Indicated / Inferred) di Reporting BM
   KHUSUS Drill Hole, dan memang TIDAK dipasang di GC-Ex Block Model: Block Model dipakai untuk
   Daily Ore Mining & Grade Control oleh Junior Grade Control / Short Term Mine Planner, bukan untuk
   pelaporan sumber daya. Klasifikasi sumber daya adalah ranah pemodelan & estimasi, dan menaruhnya
   di alat harian justru mengundang angka sumber daya terbit dari tempat yang bukan tempatnya.
   ------------------------------------------------------------------------------------------------
   Dasar: atribut hasil Model Estimation yang sudah ada (est_pass, est_nsamp, est_sor, est_ke).
     - est_pass  : pass pencarian sampel (1 = radius penuh / data rapat, 2-3 = radius diperbesar)
     - est_nsamp : jumlah komposit yang dipakai blok itu
     - est_sor   : slope of regression (kemiringan regresi kadar sebenarnya vs kadar estimasi)
     - est_ke    : kriging efficiency
   Hasil ditulis sebagai atribut KATEGORI 'klasifikasi' pada block model, sehingga seluruh mesin
   Reporting yang sudah ada (grup "Per atribut kategori", tabel grade x tonase, export CSV) langsung
   bisa dipakai. Ditambah kurva grade-tonase bertumpuk per kelas keyakinan.

   CATATAN PENTING (dipajang juga di panel): ambang di sini adalah usulan geostatistik yang dapat
   diulang, BUKAN keputusan klasifikasi. Penetapan Measured / Indicated / Inferred tetap wewenang
   Competent Person sesuai KCMI / JORC, yang juga menimbang spasi bor, kemenerusan geologi,
   kualitas QAQC dan kelayakan penambangan. */
(function () {
  var ATTR = 'klasifikasi';
  /* kelas 4 = blok waste (est_type 3, domain_est WASTE): material di luar seluruh solid, bukan sumber daya,
     jadi tidak pernah diberi kelas keyakinan dan tidak ikut kurva grade-tonase per kelas */
  var KLS = ['Measured', 'Indicated', 'Inferred', 'Belum terklasifikasi', 'Waste (di luar solid)'];
  var WKLS = 'Waste (di luar solid)';
  var COL = { Measured: '#1b7f4b', Indicated: '#2c5282', Inferred: '#c98a16', 'Belum terklasifikasi': '#8a93a0', 'Waste (di luar solid)': '#5c6672' };
  /* Ambang bawaan. hM/hI = jumlah LUBANG BOR berbeda; kM/kI = spasi bor setempat maksimum (m).
     Dua syarat terakhir inilah yang mendekati cara Competent Person menilai: bukan banyaknya
     komposit, melainkan kerapatan dan sebaran bor di sekitar blok. */
  var DEF = { pM: 1, nM: 12, sM: 0.75, hM: 3, kM: 25,
              pI: 2, nI: 7, sI: 0.45, hI: 2, kI: 50, pX: 3, use: 'sor' };

  function clsO() {
    var o = (window.RP && RP.o) || null;
    if (!o) return Object.assign({}, DEF);
    if (!o.kls) o.kls = Object.assign({}, DEF);
    for (var k in DEF) if (o.kls[k] === undefined) o.kls[k] = DEF[k];
    return o.kls;
  }
  window.clsO = clsO;
  window.clsAttr = function () { return ATTR; };

  /* atribut sumber ada / tidak */
  function src(m) {
    if (!m || !m.num) return null;
    var A = window.meAN ? meAN() : { pass: 'est_pass', ns: 'est_nsamp', sor: 'est_sor', ke: 'est_ke',
                                     nh: 'est_nhole', spasi: 'est_spasi', dmin: 'est_dmin', type: 'est_type' };
    var P = m.num[A.pass];
    if (!P) return null;
    return { P: P, N: m.num[A.ns] || null, S: m.num[A.sor] || null, E: m.num[A.ke] || null,
             H: m.num[A.nh] || null, K: m.num[A.spasi] || null, D: m.num[A.dmin] || null,
             T: m.num[A.type] || null, A: A };
  }
  window.clsSrc = src;

  /* kelas satu blok: 0 Measured, 1 Indicated, 2 Inferred, 3 belum, 4 waste */
  function klsOf(q, o, i) {
    var p = q.P[i];
    if (q.T && q.T[i] === 3) return 4;                          /* waste: bukan sumber daya */
    if (!isFinite(p) || p <= 0) return 3;                       /* tidak terestimasi */
    var n = q.N ? q.N[i] : NaN, g = q.use === 'ke' ? (q.E ? q.E[i] : NaN) : (q.S ? q.S[i] : NaN);
    var h = q.H ? q.H[i] : NaN, k = q.K ? q.K[i] : NaN;
    /* atribut yang tidak ada / belum terisi (-99) tidak menghalangi, hanya tidak ikut menilai */
    var okN = function (min) { return !isFinite(n) || n >= min; };
    var okG = function (min) { return !isFinite(g) || g <= -90 || g >= min; };
    var okH = function (min) { return !isFinite(h) || h <= 0 || h >= min; };
    var okK = function (max) { return !isFinite(k) || k <= -90 || k <= max; };
    if (p <= o.pM && okN(o.nM) && okG(o.sM) && okH(o.hM) && okK(o.kM)) return 0;
    if (p <= o.pI && okN(o.nI) && okG(o.sI) && okH(o.hI) && okK(o.kI)) return 1;
    return 2;
  }

  /* bangun atribut kategori 'klasifikasi' pada block model aktif */
  window.clsBuild = function (quiet) {
    var m = window.BX && BX.m;
    if (!m) { if (!quiet) alert('Belum ada block model.'); return null; }
    var q = src(m);
    if (!q) { if (!quiet) alert('Block model ini belum punya atribut hasil Model Estimation (est_pass). Jalankan Model Estimation dulu.'); return null; }
    var o = clsO(); q.use = o.use;
    var n = m.n, C = new Uint16Array(n), cnt = [0, 0, 0, 0, 0];
    for (var i = 0; i < n; i++) { var k = klsOf(q, o, i); C[i] = k; cnt[k]++; }
    m.cat[ATTR] = { codes: C, dict: KLS.slice(), cnt: cnt.slice() };
    if (window.BX) { BX.sc = {}; }
    return cnt;
  };

  /* ---------- panel: editor ambang + ringkasan ---------- */
  function num(k, lab, tip, step) {
    var o = clsO();
    return '<div><label title="' + tip + '">' + lab + '</label><input type=number step="' + (step || 1) + '" value="' + o[k] +
      '" onchange="clsO()[\'' + k + '\']=+this.value;clsPanelUp()"></div>';
  }
  window.clsPanelUp = function () { if (window.rpPanel) rpPanel(); };

  window.clsBox = function () {
    var m = window.BX && BX.m; if (!m) return '';
    var q = src(m), o = clsO();
    var h = '<h4>Klasifikasi keyakinan (Measured / Indicated / Inferred)</h4>';
    if (!q) return h + '<div class=hint>Block model ini belum punya atribut <i>est_pass</i>. Jalankan <b>Model Estimation</b> dulu, lalu klasifikasi bisa dihitung di sini.</div>';
    var C = m.cat[ATTR];
    h += '<div class=hint style="margin-top:-2px">Usulan kelas dari hasil estimasi: <b>pass</b> pencarian, <b>jumlah komposit</b>, <b>' +
      (o.use === 'ke' ? 'kriging efficiency' : 'slope of regression') + '</b>, <b>jumlah lubang bor berbeda</b> dan <b>spasi bor setempat</b>. ' +
      'Blok tanpa estimasi masuk <i>Belum terklasifikasi</i>; blok <b>waste</b> (est_type 3, di luar seluruh solid) tidak diberi kelas keyakinan karena bukan sumber daya.' +
      (q.N ? '' : ' <span class=warn>est_nsamp tidak ada</span> &rarr; syarat jumlah komposit diabaikan.') +
      ((o.use === 'ke' ? q.E : q.S) ? '' : ' <span class=warn>' + (o.use === 'ke' ? 'est_ke' : 'est_sor') + ' tidak ada</span> &rarr; syaratnya diabaikan.') +
      (q.H ? '' : ' <span class=warn>est_nhole / est_spasi tidak ada</span> &rarr; block model ini diestimasi sebelum 0.24.4; jalankan ulang Model Estimation agar kerapatan bor ikut terekam.') + '</div>';
    h += '<div class="g2 f"><div><label>Ukuran keyakinan</label><select onchange="clsO().use=this.value;clsPanelUp()">' +
      '<option value="sor"' + (o.use === 'sor' ? ' selected' : '') + '>Slope of regression</option>' +
      '<option value="ke"' + (o.use === 'ke' ? ' selected' : '') + '>Kriging efficiency</option></select></div><div></div></div>';
    var gaya = function (kelas, pk, nk, sk, hk, kk) {
      return '<div class=clsrule><b>' + kelas + '</b> bila pass &le; <span>' + o[pk] + '</span>, komposit &ge; <span>' + o[nk] +
        '</span>, ukuran &ge; <span>' + o[sk] + '</span>, <b>bor berbeda &ge; <span>' + o[hk] +
        '</span></b>, <b>spasi bor &le; <span>' + o[kk] + '</span> m</b></div>' +
        '<div class="g3 f">' + num(pk, 'Pass maks', kelas + ': pass pencarian maksimum') +
        num(nk, 'Komposit min', kelas + ': jumlah komposit minimum per blok') +
        num(sk, 'Ukuran min', kelas + ': SoR / KE minimum', 0.05) + '</div>' +
        '<div class="g2 f">' + num(hk, 'Lubang bor min', kelas + ': jumlah LUBANG BOR berbeda yang komposit-nya dipakai blok ini') +
        num(kk, 'Spasi bor maks (m)', kelas + ': perkiraan spasi bor setempat, jarak rata-rata tiap bor ke bor terdekat lainnya') + '</div>';
    };
    h += gaya('Measured', 'pM', 'nM', 'sM', 'hM', 'kM');
    h += gaya('Indicated', 'pI', 'nI', 'sI', 'hI', 'kI');
    h += '<div class=clsrule><b>Inferred</b>: blok terestimasi lainnya</div>';
    h += '<button class=btn-pri style="width:100%;margin-top:6px" onclick="clsRun()">&#9654; Hitung klasifikasi</button>';
    if (C) h += '<div class=clssum>' + KLS.map(function (k, j) {
      if (k === WKLS && !C.cnt[j]) return '';
      return '<span><i style="background:' + COL[k] + '"></i>' + k + ' <b>' + (window.rpN ? rpN(C.cnt[j]) : C.cnt[j]) + '</b> blok</span>';
    }).join('') + '</div><div class=hint>Tersedia sebagai atribut kategori <b>' + ATTR + '</b>: pilih grup <b>Per atribut kategori</b> di bagian untuk laporan tonase per kelas, dan atribut ini juga bisa diwarnai di tampilan 3D.</div>';
    h += '<div class=clsnote>&#9888; Ambang di atas adalah usulan geostatistik yang dapat diulang, <b>bukan</b> keputusan klasifikasi. Penetapan Measured / Indicated / Inferred tetap wewenang <b>Competent Person</b> (KCMI / JORC), yang juga menimbang hal-hal yang tidak terbaca dari angka: kemenerusan geologi antar bor, keyakinan pada model domain, kualitas QAQC, ketersediaan data densitas, dan kelayakan penambangan.</div>';
    return h;
  };

  window.clsRun = function () {
    var c = window.clsBuild(false);
    if (!c) return;
    var o = clsO(), m = BX.m;
    /* langsung pakai sebagai grup laporan supaya hasilnya terlihat */
    if (window.RP && RP.o) { RP.o.grp = 'cat'; RP.o.catAttr = ATTR; }
    if (window.updatePlot) updatePlot();
    if (window.rpPanel) rpPanel();
  };

  /* ---------- kurva grade-tonase per kelas ---------- */
  window.clsChart = function () {
    var R = window.RP && RP.res, el = document.getElementById('clsGT');
    if (!R || !el || R.grp !== 'cat') return;
    var X = R.cuts.map(String), g = R.gr, tr = [];
    KLS.forEach(function (k) {
      if (k === WKLS) return;                                   /* waste bukan sumber daya */
      var T = [], Gd = [], any = false;
      R.rows.forEach(function (r) {
        var a = r.G[k];
        T.push(a ? a.t / 1000 : 0);
        var q = a && a.s[g];
        Gd.push(q && q.w ? q.tw / q.w : null);
        if (a) any = true;
      });
      if (!any) return;
      tr.push({ type: 'bar', x: X, y: T, name: k, marker: { color: COL[k] }, hovertemplate: k + ' &ge; %{x}: %{y:,.1f} kt<extra></extra>' });
      tr.push({ type: 'scatter', mode: 'lines+markers', x: X, y: Gd, name: 'Kadar ' + k, yaxis: 'y2', line: { color: COL[k], width: 2, dash: 'dot' }, marker: { size: 5 }, hovertemplate: k + ' &ge; %{x}: %{y:.3f}<extra></extra>' });
    });
    if (!tr.length) { el.innerHTML = ''; return; }
    var dk = document.getElementById('darkMode') && document.getElementById('darkMode').checked,
      fg = dk ? '#dbe3ec' : '#1c2733', gr = dk ? '#2a3746' : '#e3e8ee';
    Plotly.react(el, tr, {
      height: 270, margin: { l: 48, r: 46, t: 30, b: 40 }, barmode: 'stack',
      paper_bgcolor: 'rgba(0,0,0,0)', plot_bgcolor: 'rgba(0,0,0,0)', font: { size: 10, color: fg },
      xaxis: { title: { text: 'Cut-off ' + g }, type: 'category', gridcolor: gr },
      yaxis: { title: { text: 'Tonase (kt)' }, gridcolor: gr },
      yaxis2: { title: { text: 'Kadar' }, overlaying: 'y', side: 'right', showgrid: false },
      legend: { orientation: 'h', x: 0, y: 1.2, font: { size: 9 } }, showlegend: true
    }, { displaylogo: false, responsive: true, displayModeBar: false });
  };

  /* ---------- sisipkan ke panel Reporting yang sudah ada ---------- */
  function hook() {
    if (typeof window.rpPanel !== 'function') return false;
    var _p = window.rpPanel;
    window.rpPanel = function () {
      _p.apply(this, arguments);
      var b = document.getElementById('rpBody');
      if (!b || !(window.BX && BX.m)) return;
      try {
        if (RP.sec === '1') b.insertAdjacentHTML('beforeend', '<div class=clswrap>' + window.clsBox() + '</div>');
        else if (RP.sec === '2' && RP.res && RP.res.grp === 'cat') {
          b.insertAdjacentHTML('beforeend', '<h4>Grade &times; tonase per kelas keyakinan</h4><div id=clsGT class=rpchart></div>' +
            '<div class=hint>Batang bertumpuk = tonase per kelas; garis putus-putus = kadar rata-rata kelas itu.</div>');
          setTimeout(window.clsChart, 40);
        }
      } catch (e) { }
    };
    /* klasifikasi ikut terbangun ulang bila estimasi dijalankan lagi */
    if (typeof window.meRun === 'function') {
      var _m = window.meRun;
      window.meRun = function () { var r = _m.apply(this, arguments); setTimeout(function () { try { if (BX.m && BX.m.cat[ATTR]) window.clsBuild(true); } catch (e) { } }, 400); return r; };
    }
    return true;
  }
  if (!hook()) { var t = setInterval(function () { if (hook()) clearInterval(t); }, 300); setTimeout(function () { clearInterval(t); }, 15000); }
})();
