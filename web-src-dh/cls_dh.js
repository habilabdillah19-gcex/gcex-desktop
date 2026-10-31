/* GC-Ex Drill Hole Ultimate — KLASIFIKASI SUMBER DAYA (Measured / Indicated / Inferred) di Reporting BM
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
  var KLS = ['Measured', 'Indicated', 'Inferred', 'Belum terklasifikasi'];
  var COL = { Measured: '#1b7f4b', Indicated: '#2c5282', Inferred: '#c98a16', 'Belum terklasifikasi': '#8a93a0' };
  var DEF = { pM: 1, nM: 12, sM: 0.75, pI: 2, nI: 7, sI: 0.45, pX: 3, use: 'sor' };

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
    var A = window.meAN ? meAN() : { pass: 'est_pass', ns: 'est_nsamp', sor: 'est_sor', ke: 'est_ke' };
    var P = m.num[A.pass];
    if (!P) return null;
    return { P: P, N: m.num[A.ns] || null, S: m.num[A.sor] || null, E: m.num[A.ke] || null, A: A };
  }
  window.clsSrc = src;

  /* kelas satu blok: 0 Measured, 1 Indicated, 2 Inferred, 3 belum */
  function klsOf(q, o, i) {
    var p = q.P[i];
    if (!isFinite(p) || p <= 0) return 3;                       /* tidak terestimasi */
    var n = q.N ? q.N[i] : NaN, g = q.use === 'ke' ? (q.E ? q.E[i] : NaN) : (q.S ? q.S[i] : NaN);
    var okN = function (min) { return !isFinite(n) || n >= min; };     /* atribut tidak ada -> tidak menghalangi */
    var okG = function (min) { return !isFinite(g) || g >= min; };
    if (p <= o.pM && okN(o.nM) && okG(o.sM)) return 0;
    if (p <= o.pI && okN(o.nI) && okG(o.sI)) return 1;
    if (p <= o.pX) return 2;
    return 2;
  }

  /* bangun atribut kategori 'klasifikasi' pada block model aktif */
  window.clsBuild = function (quiet) {
    var m = window.BX && BX.m;
    if (!m) { if (!quiet) alert('Belum ada block model.'); return null; }
    var q = src(m);
    if (!q) { if (!quiet) alert('Block model ini belum punya atribut hasil Model Estimation (est_pass). Jalankan Model Estimation dulu.'); return null; }
    var o = clsO(); q.use = o.use;
    var n = m.n, C = new Uint16Array(n), cnt = [0, 0, 0, 0];
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
    h += '<div class=hint style="margin-top:-2px">Usulan kelas dari hasil estimasi: <b>pass</b> pencarian, <b>jumlah komposit</b> dan <b>' +
      (o.use === 'ke' ? 'kriging efficiency' : 'slope of regression') + '</b>. Blok tanpa estimasi masuk <i>Belum terklasifikasi</i>.' +
      (q.N ? '' : ' <span class=warn>est_nsamp tidak ada</span> &rarr; syarat jumlah komposit diabaikan.') +
      ((o.use === 'ke' ? q.E : q.S) ? '' : ' <span class=warn>' + (o.use === 'ke' ? 'est_ke' : 'est_sor') + ' tidak ada</span> &rarr; syaratnya diabaikan.') + '</div>';
    h += '<div class="g2 f"><div><label>Ukuran keyakinan</label><select onchange="clsO().use=this.value;clsPanelUp()">' +
      '<option value="sor"' + (o.use === 'sor' ? ' selected' : '') + '>Slope of regression</option>' +
      '<option value="ke"' + (o.use === 'ke' ? ' selected' : '') + '>Kriging efficiency</option></select></div><div></div></div>';
    h += '<div class=clsrule><b>Measured</b> bila pass &le; <span>' + o.pM + '</span>, komposit &ge; <span>' + o.nM + '</span>, ukuran &ge; <span>' + o.sM + '</span></div>' +
      '<div class="g3 f">' + num('pM', 'Pass maks', 'Measured: pass pencarian maksimum (1 = radius penuh)') + num('nM', 'Komposit min', 'Measured: jumlah komposit minimum per blok') + num('sM', 'Ukuran min', 'Measured: SoR / KE minimum', 0.05) + '</div>';
    h += '<div class=clsrule><b>Indicated</b> bila pass &le; <span>' + o.pI + '</span>, komposit &ge; <span>' + o.nI + '</span>, ukuran &ge; <span>' + o.sI + '</span></div>' +
      '<div class="g3 f">' + num('pI', 'Pass maks', 'Indicated: pass pencarian maksimum') + num('nI', 'Komposit min', 'Indicated: jumlah komposit minimum') + num('sI', 'Ukuran min', 'Indicated: SoR / KE minimum', 0.05) + '</div>';
    h += '<div class=clsrule><b>Inferred</b>: blok terestimasi lainnya (pass &le; <span>' + o.pX + '</span>)</div>';
    h += '<button class=btn-pri style="width:100%;margin-top:6px" onclick="clsRun()">&#9654; Hitung klasifikasi</button>';
    if (C) h += '<div class=clssum>' + KLS.map(function (k, j) {
      return '<span><i style="background:' + COL[k] + '"></i>' + k + ' <b>' + (window.rpN ? rpN(C.cnt[j]) : C.cnt[j]) + '</b> blok</span>';
    }).join('') + '</div><div class=hint>Tersedia sebagai atribut kategori <b>' + ATTR + '</b>: pilih grup <b>Per atribut kategori</b> di bagian &#9312; untuk laporan tonase per kelas, dan atribut ini juga bisa diwarnai di tampilan 3D.</div>';
    h += '<div class=clsnote>&#9888; Ambang di atas adalah usulan geostatistik yang dapat diulang, <b>bukan</b> keputusan klasifikasi. Penetapan Measured / Indicated / Inferred tetap wewenang <b>Competent Person</b> (KCMI / JORC) yang juga menimbang spasi bor, kemenerusan geologi, QAQC dan kelayakan penambangan.</div>';
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
