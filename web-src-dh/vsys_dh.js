/* GC-Ex Drillhole — Vein System (0.24.71)
   Diadopsi dari review mesh "Vein System" Leapfrog Zona 2 (11 Nov 2026), tanpa mengubah algoritma solid RBF GC-Ex:
   1. Flag dari kolom kode (Geomodeller Vein > Flag): satu kolom kode interval (geologi / kategori assay, mis. Orebody,
      Vein, Lith) -> satu domain per kode; beberapa kode boleh diarahkan ke satu domain; kode kosong / "-" dilewati.
   2. Opsi semua vein (Geomodeller Vein > Solid): tabel opsi tiap domain sekaligus (snap / kehalusan, pinch-out di bor
      kosong, pinch-out dip, tebal minimum, radius strike, ujung atas, resolusi, resolusi adaptif) + PRIORITAS (urutan
      domain = urutan klaim blok di Model Estimation bila solid bertumpang).
   3. Vein system gabungan: jumlah solid, volume total vs volume gabungan (tumpang tindih dihitung sekali), dan ekspor
      semua solid dalam SATU berkas (OBJ / DXF / STR+DTM) seperti "Merge Vein" — solid tidak di-boolean-kan.
   4. Solid usang: bila "Jalankan ulang otomatis" mati, domain yang data bor / flag / string ATAU parameternya berubah
      sejak solid dibangun ditandai usang (dengan sebabnya), tampil di panel Solid dan Project Tree, dan bisa dibangun
      ulang sekaligus.
   Resolusi adaptif (butir 9) ada di imBuild (gcex_dh_base.html, P.adp / P.adpK). */
(function () {
  if (!window.GM || typeof gmPanel !== 'function' || typeof imPanelHtml !== 'function') return;
  var VS = window.VS = { last: '', mg: null };
  var E = function (s) { return gmE(s); };
  var N = function (v, d) { return imN(v, d); };

  /* ================= 1. Flag dari kolom kode ================= */
  var KOSONG = /^(|-+|0|NA|N\/A|NULL|NONE|NIL|\.)$/i;
  VS.kolom = function () {
    var L = [];
    (window.geoCat || []).forEach(function (c, k) { L.push({ key: 'g:' + k, src: 'g', k: k, n: c.n, t: c.n + ' (geologi)' }); });
    (window.asCat || []).forEach(function (c, k) { L.push({ key: 'a:' + k, src: 'a', k: k, n: c.n, t: c.n + ' (assay)' }); });
    return L;
  };
  VS.kolomDef = function () {
    var L = VS.kolom(), o = GM.opt.vsCol, pick = null;
    if (o && L.some(function (c) { return c.key === o; })) return o;
    ['orebody', 'vein', 'domain', 'ore_domain', 'lode'].some(function (nm) {
      return L.some(function (c) { if (c.n.toLowerCase() === nm) { pick = c.key; return true; } return false; });
    });
    return pick || (L[0] && L[0].key) || '';
  };
  /* baris interval kolom terpilih: [[hole, from, to, kode], ...] (hanya lubang yang ada di database bor aktif) */
  VS.baris = function (key) {
    var c = VS.kolom().filter(function (x) { return x.key === key; })[0]; if (!c) return [];
    var d = c.src === 'g' ? geoCat[c.k].d : asCat[c.k].d, out = [];
    if (c.src === 'g') (window.geoRows || []).forEach(function (r) { var x = r[3] && r[3][c.k]; if (x >= 0 && holeData[r[0]]) out.push([r[0], +r[1], +r[2], String(d[x])]); });
    else (window.assays || []).forEach(function (r) { var x = r[5] && r[5][c.k]; if (x >= 0 && holeData[r[0]]) out.push([r[0], +r[1], +r[2], String(d[x])]); });
    return out;
  };
  VS.scan = function (key) {
    var S = {};
    VS.baris(key).forEach(function (r) {
      var k = r[3].trim(), s = S[k] || (S[k] = { kode: k, n: 0, h: {}, l: 0 });
      s.n++; s.h[r[0]] = 1; s.l += Math.max(0, r[2] - r[1]);
    });
    return Object.keys(S).map(function (k) { var s = S[k]; s.nh = Object.keys(s.h).length; delete s.h; return s; })
      .sort(function (a, b) { return b.l - a.l; });
  };
  VS.peta = function (key) {
    GM.opt.vsMap = GM.opt.vsMap || {};
    var M = GM.opt.vsMap[key] || (GM.opt.vsMap[key] = {});
    return M;
  };
  VS.itemKode = function (key, s) {
    var M = VS.peta(key), m = M[s.kode];
    if (!m) m = M[s.kode] = { on: !KOSONG.test(s.kode), to: s.kode.replace(/[\s,;]+/g, '_') };
    return m;
  };
  VS.setKode = function (key, kode, k, v) { var m = VS.peta(key)[kode]; if (!m) return; m[k] = k === 'to' ? String(v || '').trim().replace(/[\s,;]+/g, '_') : v; if (window.SA && SA.dirty) SA.dirty(); gmPanel(); };
  VS.semua = function (key, on) { VS.scan(key).forEach(function (s) { var m = VS.itemKode(key, s); if (!KOSONG.test(s.kode)) m.on = on; }); gmPanel(); };

  VS.html = function () {
    var L = VS.kolom(), o = GM.opt;
    var h = '<details class=gmdet id=vsFlag' + (GM._openVs ? ' open' : '') + ' ontoggle="GM._openVs=this.open"><summary>Flag dari kolom kode (satu domain per kode)</summary><div style="text-align:right;margin:2px 0 -4px"><button class=lb onclick="VS.pop(\'flag\')" title="Tampilkan tabel kode di jendela lebar yang bisa digeser">&#10697; Jendela lebar</button></div>';
    if (!L.length) return h + '<div class=hint>Database bor belum punya kolom kode (atribut geologi teks atau kategori assay, mis. Orebody / Vein / Lith).</div></details>';
    var key = VS.kolomDef(), S = VS.scan(key);
    h += '<div class=hint style="margin-top:2px">Setiap kode di kolom ini menjadi satu domain vein dan intervalnya menjadi flag. Kode yang diarahkan ke nama domain yang sama digabung; kode tanpa centang dilewati.</div>';
    h += '<div class="g2 f"><div><label>Kolom kode</label><select onchange="gmOpt(\'vsCol\',this.value);gmPanel()">' +
      L.map(function (c) { return '<option value="' + c.key + '"' + (c.key === key ? ' selected' : '') + '>' + E(c.t) + '</option>'; }).join('') +
      '</select></div><div><label>Gabung run sekode bila sela &le; (m)</label><input type=number step=any min=0 value="' + (o.vsGap != null ? o.vsGap : 0) + '" onchange="gmOpt(\'vsGap\',Math.max(0,+this.value||0))" title="Interval berkode sama yang terpisah sela sependek ini dijadikan satu run (dilusi internal)"></div></div>';
    h += '<div class=gmlist style="max-height:240px"><table class=pltb id=vsTab><tr><th><input type=checkbox title="Centang / lepas semua" onchange="VS.semua(\'' + key + '\',this.checked)"></th><th>Kode</th><th>Interval</th><th>Hole</th><th>Panjang (m)</th><th>Domain tujuan</th></tr>' +
      S.slice(0, 200).map(function (s) {
        var m = VS.itemKode(key, s), kq = E(s.kode).replace(/'/g, '&#39;'), js = s.kode.replace(/\\/g, '\\\\').replace(/'/g, "\\'").replace(/"/g, '&quot;');
        return '<tr' + (m.on ? '' : ' style="opacity:.55"') + '><td><input type=checkbox ' + (m.on ? 'checked' : '') + ' onchange="VS.setKode(\'' + key + '\',\'' + js + '\',\'on\',this.checked)"></td><td><b>' + (s.kode ? kq : '<i>(kosong)</i>') + '</b></td><td>' + N(s.n) + '</td><td>' + N(s.nh) + '</td><td>' + N(s.l, 1) + '</td>' +
          '<td><input type=text value="' + E(m.to) + '" style="width:88px" onchange="VS.setKode(\'' + key + '\',\'' + js + '\',\'to\',this.value)" title="Nama domain; kode lain dengan nama yang sama digabung ke domain ini"></td></tr>';
      }).join('') + '</table>' + (S.length > 200 ? '<div class=hint>' + N(S.length - 200) + ' kode lain tidak ditampilkan (kolom ini mungkin bukan kode vein).</div>' : '') + '</div>';
    var pil = S.filter(function (s) { return VS.itemKode(key, s).on && VS.itemKode(key, s).to; }), tuj = {};
    pil.forEach(function (s) { tuj[VS.itemKode(key, s).to.toLowerCase()] = 1; });
    var nt = Object.keys(tuj).length, nb = Object.keys(tuj).filter(function (t) { return !GM.doms.some(function (d) { return d.name.toLowerCase() === t; }); }).length;
    h += '<div class="g2 f"><div><label>Flag lama domain tujuan</label><select onchange="gmOpt(\'vsMode\',this.value)"><option value=ganti' + (o.vsMode !== 'tambah' ? ' selected' : '') + '>Diganti seluruhnya (kolom = interpretasi lengkap)</option><option value=tambah' + (o.vsMode === 'tambah' ? ' selected' : '') + '>Dipertahankan, kode ditambahkan</option></select></div>' +
      '<label class=sw style="align-self:end"><input type=checkbox ' + (o.vsIm !== false ? 'checked' : '') + ' onchange="gmOpt(\'vsIm\',this.checked)">Bangun solid domain baru</label></div>';
    h += '<button class=btn-pri style="width:100%" onclick="VS.terapkan()"' + (pil.length ? '' : ' disabled') + '>Terapkan: ' + N(pil.length) + ' kode &rarr; ' + N(nt) + ' domain' + (nb ? ' (' + N(nb) + ' baru)' : '') + '</button>';
    if (VS.last) h += '<div class=hint>' + VS.last + '</div>';
    return h + '</details>';
  };

  VS.terapkan = function (tanpaTanya) {
    var key = VS.kolomDef(), gap = Math.max(0, +GM.opt.vsGap || 0), M = VS.peta(key), rows = VS.baris(key);
    var R = {};  /* tujuan(lower) -> {nama, run:{hole:[[f,t]]}} */
    rows.forEach(function (r) {
      var m = M[r[3].trim()]; if (!m || !m.on || !m.to) return;
      var t = m.to.toLowerCase(), o = R[t] || (R[t] = { nama: m.to, h: {} });
      (o.h[r[0]] = o.h[r[0]] || []).push([r[1], r[2]]);
    });
    var T = Object.keys(R); if (!T.length) { alert('Belum ada kode yang dipilih.'); return; }
    var nRun = 0;
    T.forEach(function (t) {
      var o = R[t];
      Object.keys(o.h).forEach(function (h) {
        var L = o.h[h].sort(function (a, b) { return a[0] - b[0]; }), m = [];
        L.forEach(function (x) { var p = m[m.length - 1]; if (p && x[0] - p[1] <= gap + 1e-6) p[1] = Math.max(p[1], x[1]); else m.push(x.slice()); });
        o.h[h] = m; nRun += m.length;
      });
    });
    var baru = T.filter(function (t) { return !GM.doms.some(function (d) { return d.name.toLowerCase() === t; }); });
    var ganti = GM.opt.vsMode !== 'tambah';
    if (!tanpaTanya && !confirm('Flag dari kolom ' + (VS.kolom().filter(function (c) { return c.key === key; })[0] || {}).t + ':\n\n' +
      N(nRun) + ' run interval -> ' + T.length + ' domain (' + baru.length + ' baru: ' + baru.map(function (t) { return R[t].nama; }).slice(0, 12).join(', ') + (baru.length > 12 ? ', ...' : '') + ')\n' +
      (ganti ? 'Flag lama domain tujuan DIGANTI seluruhnya.' : 'Flag lama domain tujuan dipertahankan.') + '\nFlag domain lain di interval yang sama tertimpa.\n\nLanjutkan? (bisa diurungkan)')) return;
    gmPush();
    var actP = GM.act && gmDom(GM.act) ? imPar(gmDom(GM.act)) : null, ids = [];
    T.forEach(function (t) {
      var o = R[t], d = GM.doms.filter(function (x) { return x.name.toLowerCase() === t; })[0];
      if (!d) {
        d = { id: gmNewId(), name: o.nama, col: GMPAL[GM.doms.length % GMPAL.length], vis: true }; GM.doms.push(d);
        if (GM.opt.vsIm !== false) d.im = Object.assign({}, actP || IMDEF, { on: true });
      }
      if (ganti) Object.keys(GM.flags).forEach(function (h) { GM.flags[h] = GM.flags[h].filter(function (f) { return f[2] !== d.id; }); if (!GM.flags[h].length) delete GM.flags[h]; });
      Object.keys(o.h).forEach(function (h) { o.h[h].forEach(function (x) { gmSetRange(h, x[0], x[1], d.id); }); });
      ids.push(d.id);
    });
    if (!GM.act || ids.indexOf(GM.act) < 0) GM.act = ids[0];
    VS.last = '&#10003; ' + N(nRun) + ' run dari kolom <b>' + E((VS.kolom().filter(function (c) { return c.key === key; })[0] || {}).n) + '</b> &rarr; ' + T.length + ' domain' + (baru.length ? ' (' + baru.length + ' baru' + (GM.opt.vsIm !== false ? ', solid dinyalakan' : '') + ')' : '') + '. Urutan domain = prioritas; atur di bagian Solid &rsaquo; Opsi semua vein.';
    gmDirty();
    try { if (window.PT && PT.render) PT.render(true); } catch (e) {}
    return { run: nRun, dom: T.length, baru: baru.length };
  };

  /* jendela lebar (POP.win, web-src/popout.js): isi = bagian yang sama, digambar ulang setiap panel berubah */
  VS.popOn = {};
  var POPDEF = { flag: ['vsPopFlag', 'Flag dari kolom kode', 'min(760px,calc(100vw - 440px))'], opsi: ['vsPopOpsi', 'Opsi semua vein & prioritas', 'min(1040px,calc(100vw - 440px))'] };
  var popIsi = function (k) {
    var h = k === 'flag' ? VS.html() : VS.opsiHtml();
    h = h.replace(/^<details[^>]*>/, '').replace(/<\/details>$/, '').replace(/<summary>[\s\S]*?<\/summary>/, '')
      .replace(/<div style="text-align:right;margin:2px 0 -4px">[\s\S]*?<\/div>/, '').replace(/ id=vs\w+/g, '').replace(/max-height:240px/, 'max-height:none');
    return '<div class=gmbody style="font-size:12px">' + h + '</div>';
  };
  VS.pop = function (k) {
    if (!window.POP || !POP.win) { alert('Jendela pop-up tidak tersedia.'); return; }
    var D = POPDEF[k]; VS.popOn[k] = true;
    var w = POP.win(D[0], D[1], popIsi(k));
    if (!w._pos) { w._pos = 1; w.style.left = '420px'; w.style.top = (k === 'flag' ? 70 : 100) + 'px'; w.style.width = D[2]; w.style.maxHeight = 'calc(100vh - 120px)'; }
    var x = w.querySelector('[data-x]'); if (x && !x._vs) { x._vs = 1; var f = x.onclick; x.onclick = function () { VS.popOn[k] = false; if (f) f.apply(this, arguments); }; }
    return w;
  };
  var popSegar = function () {
    Object.keys(VS.popOn).forEach(function (k) { if (!VS.popOn[k]) return; var w = document.getElementById(POPDEF[k][0]); if (!w || w.style.display === 'none') { VS.popOn[k] = false; return; }
      var b = w.querySelector('.gxpb'); if (b) b.innerHTML = popIsi(k); });
  };

  /* tempel di bagian Flag, sesudah "Usulan otomatis dari kadar" */
  var _gp = gmPanel;
  gmPanel = window.gmPanel = function () {
    var r = _gp.apply(this, arguments);
    try {
      popSegar();
      var b = $('gmBody'); if (!b || b.querySelector('#vsFlag')) return r;
      var anchor = null;
      b.querySelectorAll('details.gmdet').forEach(function (d) { var s = d.querySelector('summary'); if (s && /Usulan otomatis/.test(s.textContent)) anchor = d; });
      if (!anchor) return r;
      var w = document.createElement('div'); w.innerHTML = VS.html();
      anchor.parentNode.insertBefore(w.firstChild, anchor.nextSibling);
    } catch (e) { console.error(e); }
    return r;
  };

  /* ================= 2. Opsi semua vein + prioritas ================= */
  VS.set = function (id, k, v) { var d = gmDom(id); if (!d) return; var P = imPar(d); P[k] = v; d.im = P; gmDirty(); };
  VS.pindah = function (id, arah) {
    var T = gmTops(), i = -1; T.forEach(function (t, k) { if (t.id === id) i = k; });
    var j = i + arah; if (i < 0 || j < 0 || j >= T.length) return;
    var t = T[i]; T[i] = T[j]; T[j] = t;
    var baru = []; T.forEach(function (x) { baru.push(x); gmKids(x.id).forEach(function (k) { baru.push(k); }); });
    GM.doms.forEach(function (d) { if (baru.indexOf(d) < 0) baru.push(d); });
    GM.doms = baru; gmDirty();
    try { if (window.PT && PT.render) PT.render(true); } catch (e) {}
  };
  VS.opsiHtml = function () {
    var D = gmOrdered(), T = gmTops();
    var sel = function (id, k, v, L) { return '<select onchange="VS.set(\'' + id + '\',\'' + k + '\',' + (typeof L[0][0] === 'number' ? '+this.value' : 'this.value') + ')">' + L.map(function (o) { return '<option value="' + o[0] + '"' + (v === o[0] ? ' selected' : '') + '>' + o[1] + '</option>'; }).join('') + '</select>'; };
    var num = function (id, k, v, t) { return '<input type=number step=any min=0 value="' + v + '" style="width:52px" onchange="VS.set(\'' + id + '\',\'' + k + '\',Math.max(0,+this.value))"' + (t ? ' title="' + t + '"' : '') + '>'; };
    var cb = function (id, k, v, t) { return '<input type=checkbox ' + (v ? 'checked' : '') + ' onchange="VS.set(\'' + id + '\',\'' + k + '\',this.checked)"' + (t ? ' title="' + t + '"' : '') + '>'; };
    var h = '<details class=gmdet id=vsOpsi' + (GM._openVo ? ' open' : '') + ' ontoggle="GM._openVo=this.open"><summary>Opsi semua vein (tabel) &amp; prioritas</summary><div style="text-align:right;margin:2px 0 -4px"><button class=lb onclick="VS.pop(\'opsi\')" title="Tampilkan tabel opsi di jendela lebar yang bisa digeser">&#10697; Jendela lebar</button></div>' +
      '<div class=hint style="margin-top:2px">Satu baris per domain; perubahan langsung berlaku untuk domain itu. <b>Urutan = prioritas</b>: bila solid bertumpang, blok diklaim domain yang lebih atas saat Model Estimation.</div>' +
      '<div class=gmlist style="max-height:none;overflow-x:auto"><table class=pltb id=vsOpsiTab style="font-size:11px;white-space:nowrap"><tr><th>Prioritas</th><th>Domain</th><th title="Bangun solid">Solid</th><th title="Kehalusan permukaan; Tepat = snap ke kontak bor">Snap / halus</th><th title="Pinch-out di bor yang menembus bidang vein tanpa flag">Pinch bor kosong</th><th>Pinch-out dip (m)</th><th>Tebal min (m)</th><th>Radius strike (m)</th><th>Ujung atas</th><th>Resolusi (m)</th><th title="Resolusi adaptif: rapat di dekat data">Adaptif</th></tr>' +
      D.map(function (d) {
        var P = imPar(d), top = !gmIsKid(d), ti = -1; T.forEach(function (t, k) { if (t.id === d.id) ti = k; });
        var pr = top ? '<span style="white-space:nowrap"><b>' + (ti + 1) + '</b> <button class=lb ' + (ti > 0 ? '' : 'disabled ') + 'onclick="VS.pindah(\'' + d.id + '\',-1)" title="Naikkan prioritas">&#9650;</button><button class=lb ' + (ti < T.length - 1 ? '' : 'disabled ') + 'onclick="VS.pindah(\'' + d.id + '\',1)" title="Turunkan prioritas">&#9660;</button></span>' : '<small>cabang</small>';
        return '<tr' + (d.id === GM.act ? ' class=on' : '') + '><td>' + pr + '</td><td><span style="color:' + d.col + ';font-weight:700">' + (top ? '' : '&#8627; ') + E(d.name) + '</span></td>' +
          '<td>' + cb(d.id, 'on', P.on, 'Bangun / matikan solid') + '</td>' +
          '<td>' + sel(d.id, 'smo', P.smo != null ? +P.smo : 1, [[0, 'Tepat (snap)'], [1, 'Halus'], [2, 'Sangat halus'], [3, 'Maksimum']]) + '</td>' +
          '<td>' + cb(d.id, 'pinE', P.pinE !== false, 'Pinch-out di bor kosong') + '</td>' +
          '<td>' + num(d.id, 'pinD', P.pinD) + '</td><td>' + num(d.id, 'minT', P.minT) + '</td><td>' + num(d.id, 'aoi', P.aoi, 'Perpanjangan dari data terluar searah strike') + '</td>' +
          '<td>' + sel(d.id, 'top', P.top, [['topo', 'Potong topo'], ['pinch', 'Pinch-out']]) + '</td>' +
          '<td>' + num(d.id, 'res', P.res) + '</td><td>' + cb(d.id, 'adp', !!P.adp, 'Resolusi adaptif (x' + (P.adpK || 4) + ' di jauh data)') + '</td></tr>';
      }).join('') + '</table></div></details>';
    return h;
  };

  /* ================= 3. Vein system gabungan ================= */
  VS.solidL = function () { return GM.doms.filter(function (d) { var R = IM.R[d.id]; return d.vis && imPar(d).on && R && R.mesh; }); };
  VS.kunci = function (L) { return L.map(function (d) { return d.id + ':' + IM.R[d.id].key; }).join('|'); };
  VS.hitung = function () {
    var L = VS.solidL(); if (!L.length) { VS.mg = null; gmPanel(); return null; }
    var t0 = performance.now(), bb = function (m) { var b = [1e18, -1e18, 1e18, -1e18, 1e18, -1e18]; for (var i = 0; i < m.nv; i++) { b[0] = Math.min(b[0], m._x[i]); b[1] = Math.max(b[1], m._x[i]); b[2] = Math.min(b[2], m._y[i]); b[3] = Math.max(b[3], m._y[i]); b[4] = Math.min(b[4], m._z[i]); b[5] = Math.max(b[5], m._z[i]); } return b; };
    var O = L.map(function (d) { var R = IM.R[d.id]; return { d: d, v: R.st.vol, b: bb(R.mesh), W: R._W || (R._W = wfInside(R.mesh)) }; });
    var sum = 0, ov = 0, pairs = []; O.forEach(function (o) { sum += o.v; });
    /* volume tumpang tindih: titik grid di irisan kotak batas tiap pasangan; titik yang berada di >= 2 solid dihitung (k-1) kali lebih */
    for (var a = 0; a < O.length; a++) for (var c = a + 1; c < O.length; c++) {
      var A = O[a].b, B = O[c].b, x0 = Math.max(A[0], B[0]), x1 = Math.min(A[1], B[1]), y0 = Math.max(A[2], B[2]), y1 = Math.min(A[3], B[3]), z0 = Math.max(A[4], B[4]), z1 = Math.min(A[5], B[5]);
      if (x1 <= x0 || y1 <= y0 || z1 <= z0) continue;
      var V = (x1 - x0) * (y1 - y0) * (z1 - z0), h = Math.max(0.5, Math.min(2, Math.cbrt(V / 200000))), n = 0;
      for (var X = x0 + h / 2; X < x1; X += h) for (var Y = y0 + h / 2; Y < y1; Y += h) for (var Z = z0 + h / 2; Z < z1; Z += h) {
        if (!O[a].W.f(X, Y, Z) || !O[c].W.f(X, Y, Z)) continue;
        /* hitung sekali per titik: pasangan (a,c) hanya bila tidak ada solid lain berindeks < c selain a yang juga memuatnya */
        var dup = false; for (var q = 0; q < c && !dup; q++) if (q !== a && q < a && O[q].W.f(X, Y, Z)) dup = true;
        if (!dup) n++;
      }
      var o2 = n * h * h * h; ov += o2; if (o2 > 0) pairs.push([O[a].d.name, O[c].d.name, o2]);
    }
    pairs.sort(function (p, q) { return q[2] - p[2]; });
    VS.mg = { key: VS.kunci(L), n: L.length, sum: sum, ov: ov, vol: Math.max(0, sum - ov), pairs: pairs, ms: performance.now() - t0 };
    gmPanel(); return VS.mg;
  };
  VS.gabungHtml = function () {
    var L = VS.solidL(), sg = GM.opt.imSG || 2.6, M = VS.mg, ok = M && L.length && M.key === VS.kunci(L);
    var h = '<div class="box gmstate" id=vsGab><b>Vein system (gabungan semua solid)</b>: ' + N(L.length) + ' solid tampil';
    if (!L.length) return h + ' &mdash; bangun solid dulu.</div>';
    var sum = 0; L.forEach(function (d) { sum += IM.R[d.id].st.vol; });
    h += ' &middot; jumlah volume ' + N(sum) + ' m&sup3;';
    if (ok) h += '<br>Volume gabungan <b>' + N(M.vol) + ' m&sup3;</b> &middot; ' + N(M.vol * sg) + ' t (SG ' + sg + ')' + (M.ov > 0 ? ' &middot; tumpang tindih ' + N(M.ov) + ' m&sup3; dihitung sekali' : ' &middot; tidak ada tumpang tindih') +
      (M.pairs.length ? '<br><small>' + M.pairs.slice(0, 6).map(function (p) { return E(p[0]) + ' &cap; ' + E(p[1]) + ' ' + N(p[2]) + ' m&sup3;'; }).join('; ') + (M.pairs.length > 6 ? '; &hellip;' : '') + '</small>' : '');
    else h += '<br><span class=hint>' + (M ? 'Hasil hitung lama sudah usang (solid berubah). ' : '') + 'Volume gabungan belum dihitung.</span>';
    h += '<div class="g2 f" style="margin-top:6px"><button onclick="VS.hitung()">Hitung volume gabungan</button><span></span></div>' +
      '<div class="g3 f"><button onclick="VS.ekspor(\'obj\')" title="Semua solid dalam satu berkas OBJ (satu objek per domain)">&#8681; Gabungan OBJ</button><button onclick="VS.ekspor(\'dxf\')">&#8681; Gabungan DXF</button><button onclick="VS.ekspor(\'str\')">&#8681; Gabungan STR+DTM</button></div>' +
      '<div class=hint>Ekspor gabungan = semua solid tampil dalam SATU berkas, tiap solid tetap tertutup (tidak di-boolean-kan), seperti &quot;Merge Vein&quot; Leapfrog.</div></div>';
    return h;
  };
  VS.ekspor = function (fmt) {
    var L = VS.solidL(); if (!L.length) { alert('Belum ada solid vein yang dibangun / ditampilkan.'); return; }
    var nm = 'Vein_System_' + gxSlug(SA && SA.D && SA.D.name || 'proyek'), m = imMerge(L.map(function (d) { return IM.R[d.id].mesh; }), nm);
    var sD = GM.doms, sR = IM.R, sGrp = GM.opt.imGrp, X;
    try {
      GM.doms = [{ id: '__vs', name: nm, col: '#888', vis: true }]; IM.R = { __vs: { mesh: m } }; GM.opt.imGrp = false;
      X = imFiles(fmt, false);
    } finally { GM.doms = sD; IM.R = sR; GM.opt.imGrp = sGrp; }
    if (!X || !X.files.length) return;
    if (X.files.length === 1) { var f = X.files[0]; gxDl(new Blob([f.data], { type: fmt === 'dxf' ? 'application/dxf' : 'text/plain' }), f.name); }
    else gxDl(gxZip(X.files), nm + '_' + (fmt === 'str' ? 'Surpac' : fmt.toUpperCase()) + '_' + gxDate() + '.zip');
    IM.msg = '&#10003; Export vein system gabungan (' + L.length + ' solid, ' + (fmt === 'str' ? 'Surpac STR + DTM' : fmt.toUpperCase()) + '): ' + X.files.map(function (f) { return gmE(f.name); }).join(', ');
    gmPanel(); return X;
  };

  /* ================= 4. Solid usang ================= */
  var qk = function (L) { return L.map(function (p) { return Math.round(p[0] * 100) + ',' + Math.round(p[1] * 100) + ',' + Math.round(p[2] * 100) + ',' + p[3]; }).join(';'); };
  VS.bagian = function (d) { var P = imPar(d), X = imPts(d, P); return { kx: imHash(qk(X.H) + '|' + qk(X.W)), kp: imKey(d, P, { H: [], W: [] }) }; };
  VS.usang = function () {
    return GM.doms.filter(function (d) { var R = IM.R[d.id]; return imPar(d).on && R && R.stale; }).map(function (d) {
      var R = IM.R[d.id], s = [];
      if (R.kx && R.kp) { var B = VS.bagian(d); if (B.kx !== R.kx) s.push('data bor / flag / string'); if (B.kp !== R.kp) s.push('parameter'); }
      return { d: d, sebab: s.length ? s.join(' + ') : 'masukan' };
    });
  };
  var _sync = imSync;
  imSync = window.imSync = function (force) {
    var w0 = {}; Object.keys(IM.R).forEach(function (id) { w0[id] = IM.R[id] && IM.R[id].when; });
    var r = _sync.apply(this, arguments);
    try {
      var n0 = VS._nu || 0;
      Object.keys(IM.R).forEach(function (id) { var R = IM.R[id], d = gmDom(id); if (d && R && R.when !== w0[id] && !R.err) { var B = VS.bagian(d); R.kx = B.kx; R.kp = B.kp; } });
      var nu = GM.doms.filter(function (d) { var R = IM.R[d.id]; return imPar(d).on && R && R.stale; }).length; VS._nu = nu;
      if (nu !== n0) setTimeout(function () { try { if (window.PT && PT.render) PT.render(true); } catch (e) {} }, 0);
    } catch (e) { console.error(e); }
    return r;
  };
  VS.bangunUsang = function () {
    var L = VS.usang(); if (!L.length) return 0;
    L.forEach(function (o) { imSync(o.d.id); });
    gmDirty(); try { if (window.PT && PT.render) PT.render(true); } catch (e) {}
    return L.length;
  };
  VS.usangHtml = function () {
    if (imAuto()) return '';
    var L = VS.usang(); if (!L.length) return '';
    return '<div class="box gmstate" id=vsUsang style="border-color:#e8590c"><b class=warn>' + L.length + ' solid usang</b> &mdash; masukannya berubah sejak dibangun (Jalankan ulang otomatis mati):<br>' +
      L.map(function (o) { return '<span style="color:' + o.d.col + ';font-weight:700">' + E(o.d.name) + '</span> <small>(' + o.sebab + ')</small>'; }).join(' &middot; ') +
      '<div class="g2 f" style="margin-top:6px"><button class=btn-pri onclick="VS.bangunUsang()">&#9654; Bangun ulang yang usang (' + L.length + ')</button><span></span></div></div>';
  };

  /* panel Solid: banner usang + tabel opsi + vein system gabungan */
  var _ph = imPanelHtml;
  imPanelHtml = window.imPanelHtml = function () {
    var h = _ph.apply(this, arguments);
    try {
      if (!GM.doms.length) return h;
      var k = h.indexOf('<div class="g2 f"><button class=btn-pri onclick="imOn(GM.act)">');
      var add = VS.usangHtml() + VS.opsiHtml();
      h = k >= 0 ? h.slice(0, k) + add + h.slice(k) : h + add;
      var e = h.indexOf('<div class="g3 f"><button onclick="imExport(\'obj\')"');
      var g = VS.gabungHtml(); h = e >= 0 ? h.slice(0, e) + g + h.slice(e) : h + g;
    } catch (er) { console.error(er); }
    return h;
  };

  /* ================= Demo: satu langkah sesudah "Model vein HW / FW -> solid (RBF)" (tidak mengubah flag / domain) ================= */
  if (typeof dmSteps === 'function') {
    var _ds = dmSteps;
    dmSteps = window.dmSteps = function () {
      var S = _ds.apply(this, arguments), k = -1;
      S.forEach(function (st, i) { if (/Model vein HW/.test(st.t || '')) k = i; });
      if (k < 0) return S;
      S.splice(k + 1, 0, { s: 'Geological Modelling', t: 'Vein system: banyak vein sekaligus', el: 'rbGM', dur: 12,
        d: 'Flag dari kolom kode: setiap kode di satu kolom (mis. Vein / Orebody) menjadi satu domain vein. Tabel Opsi semua vein mengatur snap, pinch-out, tebal minimum, radius strike, resolusi adaptif dan prioritas tiap vein sekaligus; kotak Vein system menghitung volume gabungan dan mengekspor semua solid dalam satu berkas.',
        run: function (A) {
          A(0, function () { uiTab('GM'); var c = VS.kolom().filter(function (x) { return x.n === 'Vein'; })[0]; if (c) gmOpt('vsCol', c.key); GM._openVs = true; if (window.gmSec) gmSec('flag'); else gmPanel();
            var d = document.getElementById('vsFlag'); if (d) { d.open = true; d.scrollIntoView({ block: 'start' }); } dmPoint('#vsFlag summary'); });
          A(4, function () { GM._openVs = false; GM._openVo = true; if (window.gmSec) gmSec('rbf'); else gmPanel(); var d = document.getElementById('vsOpsi'); if (d) { d.open = true; d.scrollIntoView({ block: 'start' }); } dmPoint('#vsOpsiTab'); });
          A(8, function () { GM._openVo = false; VS.hitung(); var b = document.getElementById('vsGab'); if (b) b.scrollIntoView({ block: 'start' }); dmPoint('#vsGab'); });
        } });
      return S;
    };
  }

  /* simpan pengaturan bersama proyek (GM.opt sudah ikut gmPack) */
  try { gmPanel(); } catch (e) {}
})();
