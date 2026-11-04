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
    return L;
  }
  window.fqKatalog = katalog;
  function fieldOf(k) { var L = katalog(); for (var i = 0; i < L.length; i++) if (L[i].k === k) return L[i]; return null; }

  var OPN = [['ge', '≥'], ['le', '≤'], ['gt', '>'], ['lt', '<'], ['eq', '='], ['ne', '≠'],
             ['bt', 'antara (rentang)'], ['nn', 'ada isinya'], ['nl', 'kosong']];
  var OPT = [['eq', '='], ['ne', '≠'], ['in', 'salah satu (pisahkan koma)'], ['ct', 'mengandung'],
             ['nn', 'ada isinya'], ['nl', 'kosong']];

  /* ---------- nilai satu aturan untuk satu interval ---------- */
  var _col = null, _colV = -1;
  function colMap() {
    var key = (window.collars || []).length + '|' + (window.SA && SA.Dver || 0);
    if (_col && _colV === key) return _col;
    _col = {}; (window.collars || []).forEach(function (c) { _col[c[0]] = c; });
    _colV = key; return _col;
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
    panel();
    if (!diam) {
      try { if (window.updatePlot) updatePlot(); } catch (e) {}
      try { if (window.gsRun && window.GS && GS.open) gsRun(); } catch (e) {}
      try { if (window.PT && PT.render) PT.render(true); } catch (e) {}
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
      var sah = (F && F.n ? OPN : OPT).map(function (o) { return o[0]; });
      if (sah.indexOf(r.op) < 0) r.op = F && F.n ? 'ge' : 'eq';
    } else r[k] = v;
    ubah();
  };

  function panel() {
    var box = document.getElementById('fqBox');
    if (!box) {
      var host = document.getElementById('pData');
      if (!host) return;
      box = document.createElement('div');
      box.id = 'fqBox'; box.className = 'box';
      box.style.marginTop = '8px';
      host.appendChild(box);
    }
    var L = katalog(), C = aktif() ? hitung() : null;
    var h = '<div class=cmh>Filter data bor (AND / OR)</div>' +
      '<label class=sw><input type=checkbox ' + (FQ.on ? 'checked' : '') + ' onchange="fqOn(this.checked)">Filter aktif</label>';
    if (!FQ.R.length) h += '<div class=hint>Belum ada aturan. Filter menilai tiap <b>interval</b>; sebuah hole ikut tampil bila sedikitnya satu intervalnya lolos. Berlaku juga di statistik, Geostatistik dan komposit.</div>';
    else h += '<div class=f style="margin:4px 0"><label>Gabungan aturan</label><select onchange="fqMode(this.value)">' +
      '<option value=AND' + (FQ.mode !== 'OR' ? ' selected' : '') + '>Semua aturan harus terpenuhi (AND)</option>' +
      '<option value=OR' + (FQ.mode === 'OR' ? ' selected' : '') + '>Cukup salah satu (OR)</option></select></div>';

    FQ.R.forEach(function (r, i) {
      var F = fieldOf(r.f), OPS = (F && F.n) ? OPN : OPT, dua = r.op === 'bt', nilaiPerlu = r.op !== 'nn' && r.op !== 'nl';
      h += '<div class=fqrow style="display:grid;grid-template-columns:1fr 1fr auto auto auto;gap:4px;margin-bottom:4px;align-items:center">' +
        '<select onchange="fqSet(' + i + ',\'f\',this.value)">' +
          L.map(function (q) { return '<option value="' + fE(q.k) + '"' + (q.k === r.f ? ' selected' : '') + '>' + fE(q.t) + '</option>'; }).join('') + '</select>' +
        '<select onchange="fqSet(' + i + ',\'op\',this.value)">' +
          OPS.map(function (o) { return '<option value="' + o[0] + '"' + (o[0] === r.op ? ' selected' : '') + '>' + o[1] + '</option>'; }).join('') + '</select>';
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
         '<button onclick="fqClr()"' + (FQ.R.length ? '' : ' disabled') + '>Hapus semua</button></div>';
    if (C) h += '<div class=hint style="margin-top:4px"><b>' + C.nL.toLocaleString('id-ID') + '</b> dari ' +
      C.nI.toLocaleString('id-ID') + ' interval assay lolos &middot; <b>' + C.nH + '</b> dari ' + C.nHt + ' hole ikut tampil</div>';
    box.innerHTML = h;
  }
  window.fqPanel = panel;

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

  setTimeout(panel, 700);
})();
