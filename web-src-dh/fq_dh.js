/* ================= PENYUSUN FILTER AND/OR + RENTANG NILAI =================
   Filter bebas atas atribut yang SUDAH ADA di GC-Ex — bukan kolom mentah berkas Excel/CSV, jadi
   tidak ada kolom yang perlu disimpan ulang dan tidak ada biaya memori tambahan. Header pilihannya
   dinamis: ia dibentuk dari apa pun yang masuk saat import.

   Yang bisa difilter:
     unsur assay (Au, Ag, Cu, …)        angka  -> >=, <=, >, <, =, !=, ANTARA (rentang)
     kategori assay (mis. Jenis, Lab)   teks   -> =, !=, salah satu (daftar), mengandung
     atribut geologi (Lith, Alt, Ox, …) teks   -> sama seperti di atas
     kampanye & dataset aktif           teks   -> sama seperti di atas
     collar (Easting, Northing, RL, kedalaman, bench)  angka / teks
     interval (From, To, panjang)       angka
   Tiap aturan juga punya "ada" / "kosong" untuk menyaring data yang tidak terisi.

   DIGABUNG DENGAN AND ATAU OR, dan dinilai PER INTERVAL. Sebuah hole ikut tampil bila sedikitnya
   satu intervalnya lolos (hole tanpa assay dinilai dari aturan tingkat-hole saja).

   SAMBUNGAN KE MESIN YANG SUDAH ADA: filter dipasang pada domOK(), penjaga interval yang sudah
   dipakai Geostatistik, komposit dan statistik — jadi hasilnya langsung berlaku di sana tanpa
   menyentuh satu pun fungsi analisis. Pembungkusnya dipasang PALING LUAR dan ber-AND dengan filter
   domain / populasi WASTE / lapisan yang sudah ada, sehingga tidak saling meniadakan.
   Untuk tampilan, visHoles() disaring ke hole yang punya interval lolos.                          */
(function () {
  if (typeof CAT === 'undefined' || typeof window.visHoles !== 'function') return;

  var FQ = { on: false, mode: 'AND', R: [], ver: 0 };
  window.FQ = FQ;

  function fE(s) { return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) { return '&#' + c.charCodeAt(0) + ';'; }); }
  function num(v) { var x = parseFloat(String(v == null ? '' : v).replace(',', '.')); return isFinite(x) ? x : null; }

  /* ---------- katalog atribut, dibentuk dari data yang sudah diimport ---------- */
  function katalog() {
    var L = [];
    (window.elements || []).forEach(function (e, i) { L.push({ k: 'el:' + i, t: e + ' (assay)', n: 1 }); });
    (window.asCat || []).forEach(function (c, i) { L.push({ k: 'ac:' + i, t: c.n + ' (assay)', d: c.d || [] }); });
    (window.geoCat || []).forEach(function (c, i) { L.push({ k: 'gc:' + i, t: c.n + ' (geologi)', d: c.d || [] }); });
    if (window.KP && KP.L && KP.L.length) {
      L.push({ k: 'kp', t: 'Kampanye', d: KP.L.filter(function (x) { return x.kind !== 'mg'; }).map(function (x) { return x.name; }) });
      L.push({ k: 'ds', t: 'Dataset aktif', d: ['ikut dataset aktif', 'hanya tampil'] });
    }
    L.push({ k: 'c:e', t: 'Easting (collar)', n: 1 }, { k: 'c:n', t: 'Northing (collar)', n: 1 },
            { k: 'c:rl', t: 'RL collar', n: 1 }, { k: 'c:td', t: 'Kedalaman hole', n: 1 });
    if (window.BENCHMAP && Object.keys(window.BENCHMAP).length) L.push({ k: 'c:b', t: 'Bench', d: [] });
    L.push({ k: 'i:f', t: 'From (interval)', n: 1 }, { k: 'i:t', t: 'To (interval)', n: 1 }, { k: 'i:l', t: 'Panjang interval', n: 1 });
    L.push({ k: 'h', t: 'HoleID', d: [] });
    /* ---- posisi: dinilai dari TITIK TENGAH interval ----
       Perhatikan ruang koordinat: solid domain & topoZ memakai koordinat LOKAL (x-offX),
       sedangkan rpTinFn / rpSurfSrc / rpPoly memakai koordinat ABSOLUT. */
    if (typeof window.topoZ === 'function') L.push({ k: 'p:topo', t: 'Posisi → topografi aktif', p: 's' });
    try {
      (window.rpSurfList ? rpSurfList() : []).forEach(function (q) { L.push({ k: 'p:dtm:' + q[0], t: 'Posisi → ' + q[1], p: 's' }); });
    } catch (e) {}
    try {
      (window.gmTops ? gmTops() : []).forEach(function (d) {
        var R = window.meGrpR ? meGrpR(d) : null;
        if (R && R.mesh) L.push({ k: 'p:sol:' + d.id, t: 'Posisi → solid domain ' + d.name, p: 'v' });
      });
    } catch (e) {}
    try {
      ((window.MD && MD.models) || []).forEach(function (w, i) { L.push({ k: 'p:wf:' + i, t: 'Posisi → wireframe ' + w.name, p: 'v' }); });
    } catch (e) {}
    try {
      (window.rpPolyList ? rpPolyList() : []).forEach(function (q) { L.push({ k: 'p:pg:' + q[0], t: 'Posisi → poligon ' + q[1], p: 'v' }); });
    } catch (e) {}
    return L;
  }
  window.fqKatalog = katalog;
  function fieldOf(k) { var L = katalog(); for (var i = 0; i < L.length; i++) if (L[i].k === k) return L[i]; return null; }

  var OPN = [['ge', '≥'], ['le', '≤'], ['gt', '>'], ['lt', '<'], ['eq', '='], ['ne', '≠'],
             ['bt', 'antara (rentang)'], ['nn', 'ada isinya'], ['nl', 'kosong']];
  var OPT = [['eq', '='], ['ne', '≠'], ['in', 'salah satu (pisahkan koma)'], ['ct', 'mengandung'],
             ['nn', 'ada isinya'], ['nl', 'kosong']];
  var OPS = [['bw', 'di bawah'], ['at', 'di atas']];                 /* permukaan / DTM */
  var OPV = [['iv', 'di dalam'], ['ov', 'di luar']];                 /* solid, wireframe, poligon */
  function opsOf(F) { return !F ? OPT : F.p === 's' ? OPS : F.p === 'v' ? OPV : F.n ? OPN : OPT; }

  /* ---------- nilai satu aturan untuk satu interval ---------- */
  var _col = null, _colV = -1;
  function colMap() {
    var key = (window.collars || []).length + '|' + (window.SA && SA.Dver || 0);
    if (_col && _colV === key) return _col;
    _col = {}; (window.collars || []).forEach(function (c) { _col[c[0]] = c; });
    _colV = key; return _col;
  }

  /* titik tengah interval dalam koordinat LOKAL; null bila tidak bisa dihitung */
  function mid(id, a) {
    if (!a || typeof window.getXYZ !== 'function') return null;
    try { return getXYZ(id, (a[1] + a[2]) / 2); } catch (e) { return null; }
  }
  var _wf = {};
  function wfIn(i) {
    if (!_wf[i]) { var w = ((window.MD && MD.models) || [])[i]; _wf[i] = w ? wfInside(w) : { f: function () { return false; } }; }
    return _wf[i];
  }
  var _sol = {};
  function solIn(did) {
    var d = window.gmDom ? gmDom(did) : null, R = (d && window.meGrpR) ? meGrpR(d) : null;
    if (!R || !R.mesh) return null;
    if (!_sol[did] || _sol[did].key !== R.key) _sol[did] = { key: R.key, W: R.W || wfInside(R.mesh) };
    return _sol[did].W;
  }
  /* true / false / null (tidak bisa dinilai) */
  function posisi(r, id, a) {
    var p = r.f.split(':'), q = mid(id, a);
    if (!q) return null;
    var ax = q.x + (window.offX || 0), ay = q.y + (window.offY || 0), z = q.z;
    if (p[1] === 'topo') {
      var zt = null; try { zt = topoZ(q.x, q.y); } catch (e) {}
      if (zt == null || !isFinite(zt)) return null;
      return r.op === 'at' ? z > zt : z <= zt;
    }
    if (p[1] === 'dtm') {
      var S = window.rpSurfSrc ? rpSurfSrc(r.f.slice(6)) : null;
      if (!S || !S.fn) return null;
      var v = S.fn(ax, ay);
      if (!v) return null;
      return r.op === 'at' ? z > v[0] : z < v[1];
    }
    if (p[1] === 'sol') {
      var W = solIn(p.slice(2).join(':'));
      if (!W) return null;
      var di = W.f(q.x, q.y, z);
      return r.op === 'ov' ? !di : di;
    }
    if (p[1] === 'wf') {
      var d2 = wfIn(+p[2]).f(q.x, q.y, z);
      return r.op === 'ov' ? !d2 : d2;
    }
    if (p[1] === 'pg') {
      var PL = window.rpPoly ? rpPoly(r.f.slice(5)) : null;
      if (!PL || !PL.f) return null;
      var dp = PL.f(ax, ay);                      /* rpPoly bekerja dalam koordinat ABSOLUT */
      return r.op === 'ov' ? !dp : dp;
    }
    return null;
  }

  function nilai(r, id, a) {
    var k = r.f, p = k.split(':'), C;
    switch (p[0]) {
      case 'el': return a ? (a[4] ? a[4][+p[1]] : null) : null;
      case 'ac': var c1 = (window.asCat || [])[+p[1]], v1 = a && a[5] ? a[5][+p[1]] : -1;
                 return (c1 && v1 != null && v1 >= 0) ? c1.d[v1] : null;
      case 'gc': if (!a || typeof window.geoAt !== 'function') return null;
                 var c2 = (window.geoCat || [])[+p[1]], v2 = geoAt(+p[1], id, (a[1] + a[2]) / 2);
                 return (c2 && v2 >= 0) ? c2.d[v2] : null;
      case 'kp': var kk = window.kpById && kpById(window.kpOf ? kpOf(id) : ''); return kk ? kk.name : null;
      case 'ds': return (window.kpKerja && kpKerja(id)) ? 'ikut dataset aktif' : 'hanya tampil';
      case 'c': C = colMap()[id]; if (!C) return null;
                return p[1] === 'e' ? C[1] : p[1] === 'n' ? C[2] : p[1] === 'rl' ? C[3] :
                       p[1] === 'td' ? C[4] : (window.BENCHMAP || {})[id];
      case 'i': if (!a) return null; return p[1] === 'f' ? a[1] : p[1] === 't' ? a[2] : (a[2] - a[1]);
      case 'h': return id;
    }
    return null;
  }

  function cocok(r, id, a) {
    if (r.f.indexOf('p:') === 0) { var pr = posisi(r, id, a); return pr === null ? false : pr; }
    var v = nilai(r, id, a), ada = !(v === null || v === undefined || v === '' || (typeof v === 'number' && !isFinite(v)));
    if (r.op === 'nn') return ada;
    if (r.op === 'nl') return !ada;
    if (!ada) return false;
    var F = fieldOf(r.f);
    if (F && F.n) {
      var x = typeof v === 'number' ? v : num(v), A = num(r.a), B = num(r.b);
      if (x === null) return false;
      switch (r.op) {
        case 'ge': return A !== null && x >= A;
        case 'le': return A !== null && x <= A;
        case 'gt': return A !== null && x > A;
        case 'lt': return A !== null && x < A;
        case 'eq': return A !== null && Math.abs(x - A) < 1e-9;
        case 'ne': return A !== null && Math.abs(x - A) >= 1e-9;
        case 'bt': return A !== null && B !== null && x >= Math.min(A, B) && x <= Math.max(A, B);
      }
      return true;
    }
    var s = String(v), t = String(r.a == null ? '' : r.a);
    switch (r.op) {
      case 'eq': return s.toUpperCase() === t.trim().toUpperCase();
      case 'ne': return s.toUpperCase() !== t.trim().toUpperCase();
      case 'ct': return s.toUpperCase().indexOf(t.trim().toUpperCase()) >= 0;
      case 'in': return t.split(/[,;]+/).map(function (q) { return q.trim().toUpperCase(); })
                        .filter(Boolean).indexOf(s.toUpperCase()) >= 0;
    }
    return true;
  }

  function aktif() { return FQ.on && FQ.R.length > 0; }
  window.fqAktif = aktif;

  /* satu interval lolos filter? */
  window.fqOK = function (id, a) {
    if (!aktif()) return true;
    var and = FQ.mode !== 'OR', i;
    for (i = 0; i < FQ.R.length; i++) {
      var ok = cocok(FQ.R[i], id, a);
      if (and && !ok) return false;
      if (!and && ok) return true;
    }
    return and;
  };

  /* ---------- sambungan: domOK (interval) + visHoles (hole) ---------- */
  if (typeof window.domOK === 'function') {
    var _d = window.domOK;
    window.domOK = function (id, a) { return window.fqOK(id, a) && _d.apply(this, arguments); };
  }

  var _hv = null, _hvV = -1;
  function holeLolos() {
    var key = FQ.ver + '|' + (window.collars || []).length + '|' + (window.assays || []).length;
    if (_hv && _hvV === key) return _hv;
    var H = {};
    (window.collars || []).forEach(function (c) { H[c[0]] = false; });
    var GA = window.groupedAssays || {};
    Object.keys(H).forEach(function (id) {
      var A = GA[id] || [];
      if (!A.length) { H[id] = window.fqOK(id, null); return; }
      for (var i = 0; i < A.length; i++) if (window.fqOK(id, A[i])) { H[id] = true; return; }
    });
    _hv = H; _hvV = key;
    return H;
  }
  window.fqHoleLolos = holeLolos;

  var _vh = window.visHoles;
  window.visHoles = function () {
    var v = _vh.apply(this, arguments);
    if (!aktif()) return v;
    var H = holeLolos();
    return v.filter(function (id) { return H[id]; });
  };

  /* ---------- hitung cakupan untuk ringkasan panel ---------- */
  function hitung() {
    var nI = 0, nL = 0, nH = 0, H = holeLolos();
    (window.collars || []).forEach(function (c) { if (H[c[0]]) nH++; });
    (window.assays || []).forEach(function (a) { nI++; if (window.fqOK(a[0], a)) nL++; });
    return { nI: nI, nL: nL, nH: nH, nHt: (window.collars || []).length };
  }

  /* ---------- panel ---------- */
  function ubah(diam) {
    FQ.ver++; _hvV = -1;
    if (window.SA && SA.dirty) SA.dirty();
    try { panel(); ringkas(); } catch (e) { console.error(e); }
    try { if (window.PT && PT.render) PT.render(true); } catch (e) {}
    if (!diam) {
      try { if (window.updatePlot) updatePlot(); } catch (e) {}
      try { if (window.gsRun && window.GS && GS.open) gsRun(); } catch (e) {}
    }
  }
  window.fqUbah = ubah;

  window.fqOn = function (v) { FQ.on = !!v; ubah(); };
  window.fqMode = function (v) { FQ.mode = v === 'OR' ? 'OR' : 'AND'; ubah(); };
  window.fqAdd = function () {
    var L = katalog();
    FQ.R.push({ f: L[0] ? L[0].k : 'h', op: L[0] && L[0].n ? 'ge' : 'eq', a: '', b: '' });
    FQ.on = true; ubah();
  };
  window.fqDel = function (i) { FQ.R.splice(i, 1); if (!FQ.R.length) FQ.on = false; ubah(); };
  window.fqClr = function () { FQ.R = []; FQ.on = false; ubah(); };
  window.fqSet = function (i, k, v) {
    var r = FQ.R[i]; if (!r) return;
    if (k === 'f') {
      r.f = v;
      var F = fieldOf(v);
      var sah = opsOf(F).map(function (o) { return o[0]; });
      if (sah.indexOf(r.op) < 0) r.op = sah[0];
    } else r[k] = v;
    ubah();
  };

  /* 0.24.30: isi dialog, bukan kotak tetap di panel Data & Filter. Kotak lama membuat panel itu
     panjang dan harus digulung terus; sekarang pintunya ada di node Project Tree "Filter data bor". */
  function panel() {
    var box = document.getElementById('fqBody');
    if (!box) return;
    var L = katalog(), C = aktif() ? hitung() : null;
    var h = '<label class=sw><input type=checkbox ' + (FQ.on ? 'checked' : '') + ' onchange="fqOn(this.checked)">Filter aktif</label>';
    if (!FQ.R.length) h += '<div class=hint>Belum ada aturan. Filter menilai tiap <b>interval</b>; sebuah hole ikut tampil bila sedikitnya satu intervalnya lolos. Berlaku juga di statistik, Geostatistik dan komposit.</div>';
    else h += '<div class=f style="margin:4px 0"><label>Gabungan aturan</label><select onchange="fqMode(this.value)">' +
      '<option value=AND' + (FQ.mode !== 'OR' ? ' selected' : '') + '>Semua aturan harus terpenuhi (AND)</option>' +
      '<option value=OR' + (FQ.mode === 'OR' ? ' selected' : '') + '>Cukup salah satu (OR)</option></select></div>';

    FQ.R.forEach(function (r, i) {
      var F = fieldOf(r.f), OP = opsOf(F), dua = r.op === 'bt',
          nilaiPerlu = r.op !== 'nn' && r.op !== 'nl' && !(F && F.p);
      h += '<div class=fqrow style="display:grid;grid-template-columns:1fr 1fr auto auto auto;gap:4px;margin-bottom:4px;align-items:center">' +
        '<select onchange="fqSet(' + i + ',\'f\',this.value)">' +
          L.map(function (q) { return '<option value="' + fE(q.k) + '"' + (q.k === r.f ? ' selected' : '') + '>' + fE(q.t) + '</option>'; }).join('') + '</select>' +
        '<select onchange="fqSet(' + i + ',\'op\',this.value)">' +
          OP.map(function (o) { return '<option value="' + o[0] + '"' + (o[0] === r.op ? ' selected' : '') + '>' + o[1] + '</option>'; }).join('') + '</select>';
      if (!nilaiPerlu) h += '<span class=hint style="grid-column:span 2">&mdash;</span>';
      else if (F && F.d && F.d.length && (r.op === 'eq' || r.op === 'ne'))
        h += '<select style="grid-column:span 2" onchange="fqSet(' + i + ',\'a\',this.value)"><option value="">(pilih)</option>' +
          F.d.map(function (v) { return '<option' + (String(v) === String(r.a) ? ' selected' : '') + '>' + fE(v) + '</option>'; }).join('') + '</select>';
      else {
        h += '<input type="text" value="' + fE(r.a) + '" placeholder="' + (dua ? 'min' : 'nilai') + '" onchange="fqSet(' + i + ',\'a\',this.value)" style="width:100%">';
        h += dua ? '<input type="text" value="' + fE(r.b) + '" placeholder="maks" onchange="fqSet(' + i + ',\'b\',this.value)" style="width:100%">'
                 : '<span></span>';
      }
      h += '<button class=x title="Hapus aturan" onclick="fqDel(' + i + ')">&times;</button></div>';
    });
    h += '<div class=g2 style="margin-top:4px"><button onclick="fqAdd()">+ Aturan</button>' +
         '<button onclick="fqClr()"' + (FQ.R.length ? '' : ' disabled') + '>Hapus semua &amp; matikan</button></div>';
    if (typeof window.topoZ === 'function') h +=
      '<div class=lab style="margin-top:6px">Tombol cepat</div><div class=g2>' +
      '<button onclick="fqTopo(\'bw\')">Hanya di bawah topografi</button>' +
      '<button onclick="fqTopo(\'at\')">Hanya di atas topografi</button></div>';
    h += '<div class=g2 style="margin-top:4px"><button onclick="fqExport(\'xlsx\')"' + (aktif() ? '' : ' disabled') + '>Export terfilter (.xlsx)</button>' +
         '<button onclick="fqExport(\'csv\')"' + (aktif() ? '' : ' disabled') + '>Export terfilter (CSV)</button></div>';
    if (C) h += '<div class=hint style="margin-top:4px"><b>' + C.nL.toLocaleString('id-ID') + '</b> dari ' +
      C.nI.toLocaleString('id-ID') + ' interval assay lolos &middot; <b>' + C.nH + '</b> dari ' + C.nHt + ' hole ikut tampil</div>';
    box.innerHTML = h;
  }
  window.fqPanel = panel;

  function ringkas() {
    var m = document.getElementById('fqMsg'); if (!m) return;
    var C = aktif() ? hitung() : null;
    m.innerHTML = C ? ('<b>' + C.nL.toLocaleString('id-ID') + '</b> dari ' + C.nI.toLocaleString('id-ID') +
                       ' interval &middot; <b>' + C.nH + '</b> dari ' + C.nHt + ' hole lolos')
                    : (FQ.R.length ? 'Aturan tersimpan, tetapi filter sedang mati.' : 'Belum ada aturan.');
  }

  /* ---------- dialog ---------- */
  window.fqDlg = function () {
    var d = document.getElementById('fqDlg');
    if (!d) { d = document.createElement('div'); d.id = 'fqDlg'; d.className = 'bxdlg'; document.body.appendChild(d); }
    d.innerHTML = '<div class=impBox style=width:min(840px,100%)><div class=impHead><div class=impBrand><div><b>Filter data bor</b>' +
      '<small>Aturan AND / OR atas atribut yang sudah ada di GC-Ex &mdash; unsur, kategori assay, atribut geologi, kampanye, data collar, interval, dan posisi terhadap topografi / DTM / solid / wireframe / poligon. Dinilai per interval.</small>' +
      '</div></div><button class="ib ghost" onclick="fqClose()">Tutup</button></div>' +
      '<div class=impBody id=fqBody></div>' +
      '<div class=impFoot><div id=fqMsg class=hint></div><button class=ib onclick="fqClose()">Selesai</button></div></div>';
    d.style.display = 'flex';
    panel(); ringkas();
  };
  window.fqClose = function () {
    var d = document.getElementById('fqDlg'); if (d) d.style.display = 'none';
    try { if (window.PT && PT.render) PT.render(true); } catch (e) {}
  };

  /* ---------- node Project Tree ---------- */
  window.fqTree = function () {
    var n = FQ.R.length, C = aktif() ? hitung() : null, aTopo = typeof window.topoZ !== 'function';
    var kids = FQ.R.map(function (r, i) {
      var F = fieldOf(r.f), OP = opsOf(F), on = r.op;
      OP.forEach(function (o) { if (o[0] === r.op) on = o[1]; });
      var v = (r.op === 'nn' || r.op === 'nl' || (F && F.p)) ? ''
            : r.op === 'bt' ? ' ' + (r.a === '' ? '?' : r.a) + ' \u2026 ' + (r.b === '' ? '?' : r.b)
            : ' ' + (r.a === '' || r.a == null ? '(kosong)' : r.a);
      return { id: 'fq.r' + i, t: (F ? F.t : r.f) + ' ' + on + v, ic: 'attr', dim: !FQ.on,
               menu: function () {
                 return [{ t: 'Atur filter\u2026', fn: function () { fqDlg(); } }, { sep: 1 },
                         { t: 'Hapus aturan ini', danger: 1, fn: function () { fqDel(i); } }];
               } };
    });
    return [{
      id: 'db.fq', t: 'Filter data bor', ic: 'gear', fold: 1, tab: 'Data',
      b: n ? (FQ.on ? FQ.mode + ' \u00b7 ' + n + ' aturan' + (C ? ' \u00b7 ' + C.nH + ' hole' : '') : n + ' aturan (mati)') : '',
      dim: !aktif(),
      chk: n ? FQ.on : undefined, onChk: function (v) { fqOn(v); },
      hint: aktif() ? 'Aktif \u2014 berlaku di tampilan, statistik, komposit, Geostatistik dan estimasi'
                    : 'Tidak aktif \u2014 seluruh data dipakai',
      menu: function () {
        return [
          { t: 'Atur filter\u2026 (aturan AND / OR)', fn: function () { fqDlg(); } },
          { sep: 1 }, { h: 'Tombol cepat' },
          { t: 'Hanya di bawah topografi', dis: aTopo, fn: function () { fqTopo('bw'); } },
          { t: 'Hanya di atas topografi', dis: aTopo, fn: function () { fqTopo('at'); } },
          { sep: 1 },
          { t: 'Export data terfilter (.xlsx)\u2026', dis: !aktif(), fn: function () { fqExport('xlsx'); } },
          { t: 'Export data terfilter (CSV)\u2026', dis: !aktif(), fn: function () { fqExport('csv'); } },
          { sep: 1 },
          { t: FQ.on ? 'Matikan filter (aturan disimpan)' : 'Aktifkan filter', dis: !n, fn: function () { fqOn(!FQ.on); } },
          { t: 'Hapus semua aturan', danger: 1, dis: !n, fn: function () { fqClr(); } }
        ];
      },
      kids: kids
    }];
  };

  /* ---------- tombol cepat topografi ---------- */
  window.fqTopo = function (arah) {
    var ada = -1;
    FQ.R.forEach(function (r, i) { if (r.f === 'p:topo') ada = i; });
    if (ada >= 0) FQ.R[ada].op = arah; else FQ.R.push({ f: 'p:topo', op: arah, a: '', b: '' });
    FQ.on = true; ubah();
  };

  /* ================= EXPORT DATA BOR TERFILTER =================
     Collar / Survey / Assay / Geologi hanya untuk yang lolos filter.

     PEMOTONGAN DI PERMUKAAN: bila ada aturan posisi terhadap sebuah permukaan (topografi aktif atau
     DTM lain), interval yang MEMOTONG permukaan itu tidak dibuang dan tidak diambil utuh, melainkan
     dipotong tepat di permukaannya. Kedalaman potongnya dicari dengan bagi-dua pada lintasan bor
     (30 langkah, ketelitian jauh di bawah 1 mm untuk interval sepanjang apa pun yang wajar), jadi
     tonase di bawah topografi tidak dilebihkan oleh separuh interval yang sebenarnya di udara.    */
  function surfRules() { return FQ.R.filter(function (r) { return r.f === 'p:topo' || r.f.indexOf('p:dtm:') === 0; }); }

  function zSurf(r, id, d) {
    var q; try { q = getXYZ(id, d); } catch (e) { return null; }
    if (!q) return null;
    if (r.f === 'p:topo') { var z = null; try { z = topoZ(q.x, q.y); } catch (e) {} return (z == null || !isFinite(z)) ? null : { z: q.z, s: z }; }
    var S = window.rpSurfSrc ? rpSurfSrc(r.f.slice(6)) : null;
    if (!S || !S.fn) return null;
    var v = S.fn(q.x + (window.offX || 0), q.y + (window.offY || 0));
    return v ? { z: q.z, s: r.op === 'at' ? v[0] : v[1] } : null;
  }
  function lolosDi(r, id, d) {
    var o = zSurf(r, id, d);
    if (!o) return null;
    return r.op === 'at' ? o.z > o.s : o.z <= o.s;
  }
  /* kedalaman tempat lintasan bor memotong permukaan, antara d0 (lolos) dan d1 (tidak) */
  function potong(r, id, d0, d1) {
    for (var i = 0; i < 30; i++) {
      var m = (d0 + d1) / 2, ok = lolosDi(r, id, m);
      if (ok === null) return null;
      if (ok) d0 = m; else d1 = m;
    }
    return (d0 + d1) / 2;
  }
  /* [from,to] hasil pemotongan, atau null bila seluruhnya di luar */
  function klip(id, f, t) {
    var R = surfRules();
    if (!R.length) return [f, t];
    for (var i = 0; i < R.length; i++) {
      var r = R[i], a0 = lolosDi(r, id, f + 1e-6), a1 = lolosDi(r, id, t - 1e-6);
      if (a0 === null || a1 === null) continue;
      if (a0 && a1) continue;
      if (!a0 && !a1) return null;
      if (a0 && !a1) { var c1 = potong(r, id, f + 1e-6, t - 1e-6); if (c1 != null) t = c1; }
      else { var c2 = potong(r, id, t - 1e-6, f + 1e-6); if (c2 != null) f = c2; }
      if (!(t > f)) return null;
    }
    return [f, t];
  }
  window.fqKlip = klip;

  window.fqTabel = function () {
    var H = holeLolos(), ok = {}, nH = 0, nPot = 0;
    (window.collars || []).forEach(function (c) { if (H[c[0]]) { ok[c[0]] = 1; nH++; } });
    var kp = function (id) { var k = window.kpById && window.kpOf ? kpById(kpOf(id)) : null; return k ? k.name : ''; };
    var r3 = function (v) { return typeof v === 'number' && isFinite(v) ? Math.round(v * 1000) / 1000 : v; };
    var col = [['HoleID', 'East', 'North', 'RL', 'Depth', 'Kampanye']];
    (window.collars || []).forEach(function (c) { if (ok[c[0]]) col.push([c[0], c[1], c[2], c[3], c[4], kp(c[0])]); });
    var sv = [['HoleID', 'Depth', 'Dip', 'Azimuth']];
    (window.surveys || []).forEach(function (r) { if (ok[r[0]]) sv.push([r[0], r[1], r[2], r[3]]); });
    var E = window.elements || [], AC = (window.asCat || []).map(function (c) { return c.n; });
    var as = [['HoleID', 'From', 'To', 'SampleID'].concat(E, AC, ['Kampanye'])];
    (window.assays || []).forEach(function (a) {
      if (!ok[a[0]] || !window.fqOK(a[0], a)) return;
      var kk = klip(a[0], a[1], a[2]);
      if (!kk) return;
      if (Math.abs(kk[0] - a[1]) > 1e-6 || Math.abs(kk[1] - a[2]) > 1e-6) nPot++;
      var row = [a[0], r3(kk[0]), r3(kk[1]), a[3]];
      E.forEach(function (_, i) { row.push(a[4] && a[4][i] != null ? a[4][i] : ''); });
      AC.forEach(function (_, i) { var c = (window.asCat || [])[i], v = a[5] && a[5][i]; row.push(c && v != null && v >= 0 ? c.d[v] : ''); });
      row.push(kp(a[0]));
      as.push(row);
    });
    var GC = (window.geoCat || []).map(function (c) { return c.n; });
    var ge = [['HoleID', 'From', 'To'].concat(GC, ['Kampanye'])];
    (window.geoRows || []).forEach(function (g) {
      if (!ok[g[0]]) return;
      var kk = klip(g[0], g[1], g[2]);
      if (!kk) return;
      var row = [g[0], r3(kk[0]), r3(kk[1])];
      GC.forEach(function (_, i) { var c = (window.geoCat || [])[i], v = g[3] && g[3][i]; row.push(c && v != null && v >= 0 ? c.d[v] : ''); });
      row.push(kp(g[0]));
      ge.push(row);
    });
    return { nH: nH, nPot: nPot, sheets: [{ name: 'Collar', rows: col }, { name: 'Survey', rows: sv },
                                          { name: 'Assay', rows: as }, { name: 'Geologi', rows: ge }] };
  };

  function unduh(blob, nama) {
    gxSimpan(blob, nama);
    setTimeout(function () { URL.revokeObjectURL(a.href); a.remove(); }, 2000);
  }
  function csvTeks(rows) {
    return rows.map(function (r) {
      return r.map(function (v) {
        var s2 = v == null ? '' : String(v);
        return /[",;\n]/.test(s2) ? '"' + s2.replace(/"/g, '""') + '"' : s2;
      }).join(',');
    }).join('\r\n');
  }

  window.fqExport = function (fmt) {
    try {
      if (!aktif()) { alert('Filter belum aktif: tidak ada yang disaring.'); return; }
      var T = window.fqTabel();
      if (!T.nH) { alert('Tidak ada hole yang lolos filter.'); return; }
      var cap = new Date().toISOString().slice(0, 10).replace(/-/g, '');
      if (fmt === 'csv') {
        T.sheets.forEach(function (s2) {
          unduh(new Blob(['﻿' + csvTeks(s2.rows)], { type: 'text/csv;charset=utf-8' }),
                'GCEx_terfilter_' + cap + '_' + s2.name.toLowerCase() + '.csv');
        });
      } else {
        if (typeof window.kpXlsx !== 'function') { alert('Penulis .xlsx tidak tersedia.'); return; }
        unduh(new Blob([kpXlsx(T.sheets)], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' }),
              'GCEx_terfilter_' + cap + '.xlsx');
      }
      alert('Export data bor terfilter: ' + T.nH + ' hole.\n\n' +
            T.sheets.map(function (s2) { return s2.name + ' ' + (s2.rows.length - 1) + ' baris'; }).join(' · ') +
            (T.nPot ? '\n\n' + T.nPot + ' interval dipotong tepat di permukaan (topografi / DTM) sesuai aturan posisi.' : ''));
    } catch (e) { console.error(e); alert('Export gagal: ' + (e.message || e)); }
  };

  /* ---------- simpan / muat bersama proyek ---------- */
  if (window.SA && typeof SA.collectWork === 'function') {
    var _c = SA.collectWork;
    SA.collectWork = function () {
      var w = _c.apply(this, arguments);
      try { w.fq = { on: FQ.on, mode: FQ.mode, R: FQ.R }; } catch (e) {}
      return w;
    };
    var _a = SA.applyWork;
    SA.applyWork = function (W) {
      try { var o = W && W.fq; FQ.on = !!(o && o.on); FQ.mode = (o && o.mode) || 'AND'; FQ.R = (o && o.R) || []; FQ.ver++; _hvV = -1; } catch (e) {}
      var r = _a.apply(this, arguments);
      try { panel(); } catch (e) {}
      return r;
    };
  }

  /* tidak ada lagi kotak tetap di panel Data & Filter: pintunya ada di node Project Tree */
})();
