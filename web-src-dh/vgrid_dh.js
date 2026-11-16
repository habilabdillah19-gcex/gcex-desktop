/* ================= GC-Ex Drillhole 0.24.99: KATEGORI KOLOM IMPOR + VALIDASI & EDIT TABEL (gaya MS Access) =================
   Pemilik 16 Nov 2026 ("Kerjakan ketiganya sekaligus"), diadopsi dari Ore Works 0.10.0 dan disesuaikan dengan alur Drillhole:
   1. Kategori kolom: pemetaan kolom di layar import (panel "Pemetaan kolom & unsur") DIINGAT per nama kolom
      (localStorage 'gcex_dh_colmap'); file berikutnya dengan nama kolom sama langsung terpetakan. Kolom geologi punya
      kategori (Litologi, Alterasi, Oksidasi, Mineralisasi, Vein/domain, Struktur, Deskripsi, Kode lain, Abaikan) yang ikut
      tersimpan di proyek (geoCat[i].kat) dan dipakai lebih dulu oleh Stratified (litologi), Ore Geometry (vein, alterasi).
      Nama kolom tak dikenali: From/To ditebak dari isi (dua kolom angka berurutan, To > From), Hole_ID = kolom teks pertama.
   2. Pemeriksaan tambahan di laporan validasi import: Hole_ID beda huruf besar/kecil, koordinat collar jauh dari lubang lain,
      nilai unsur bukan angka, Au > 500, Sample_ID kosong, litologi kosong, azimuth di luar 0..360.
   3. Jendela "Validasi & edit tabel": grid gaya MS Access (sel merah = galat, kuning = peringatan, ringkasan + daftar masalah,
      edit langsung / F2 / klik dua kali, tempel dari Excel, Ctrl+Z, tambah / hapus baris, urutkan, cari, hanya baris bermasalah),
      ekspor CSV per tabel / semua (header & pemisah asli) + laporan masalah.
      - Sebelum diproses (layar import): tabel yang dipilih diedit di tempat; "Terapkan" menyegarkan pratinjau import.
      - Sesudah diproses (Project Tree › Database Bor › Validasi & edit tabel): tabel dari database proyek; "Bangun ulang
        dataset" menyimpan lewat PTD.apply (backup folder proyek dulu, bisa dibatalkan lewat Batalkan perubahan database).
   Modul ini berjalan di lingkup skrip layar import (SA, H, feat, findCol, normH, numV, txt, esc, catDict, selV). */
var VG = window.VG = {};
(function () {
  var g = function (i) { return document.getElementById(i); };
  var KS = ['collar', 'survey', 'assay', 'geo'], KN = { collar: 'Collar', survey: 'Survey', assay: 'Assay', geo: 'Geologi' };
  var GK = [['lith', 'Litologi'], ['alt', 'Alterasi'], ['ox', 'Oksidasi / pelapukan'], ['min', 'Mineralisasi'], ['vein', 'Vein / domain'], ['str', 'Struktur'], ['desc', 'Deskripsi'], ['code', 'Kode lain'], ['ign', 'Abaikan']];
  var GKN = {}; GK.forEach(function (x) { GKN[x[0]] = x[1]; });
  var GRX = [['lith', /^(lith|litho|litologi|lithology|rock|batuan)/], ['alt', /^alt|alter|ubahan/], ['ox', /oks|^ox|weath|lapuk/], ['min', /miner|sulf|sulph/],
    ['vein', /vein|urat|^qv|domain|orebody|ore_?zone/], ['str', /struct|struk|fault|sesar|joint|kekar|^str$/], ['desc', /^(desc|desk|ket|remark|catatan|comment)/]];
  var KEYS = { collar: ['hole', 'e', 'n', 'rl', 'td', 'dip', 'azi'], survey: ['hole', 'dep', 'dip', 'azi'], assay: ['hole', 'fr', 'to', 'samp'], geo: ['hole', 'fr', 'to'] };
  var NOTV = /^\s*(-|–|na|n\/a|#n\/a|nd|ns|is|lnr|nr|x|null)?\s*$/i;
  var toast = function (t) { var d = g('vgToast'); if (!d) { d = document.createElement('div'); d.id = 'vgToast'; document.body.appendChild(d); } d.textContent = t; d.className = 'on'; clearTimeout(d._t); d._t = setTimeout(function () { d.className = ''; }, 3200); };

  /* ======================= 1. templat pemetaan kolom ======================= */
  var TPK = 'gcex_dh_colmap';
  var tplAll = function () { try { return JSON.parse(localStorage.getItem(TPK) || '{}') || {}; } catch (e) { return {}; } };
  var tplGet = function (role) { return tplAll()[role] || {}; };
  function colState(role, c) {
    var M = SA.map[role]; if (!M) return '';
    var ks = KEYS[role]; for (var i = 0; i < ks.length; i++) if (M[ks[i]] === c) return ks[i];
    if (role === 'assay') return (M.els || []).indexOf(c) >= 0 ? 'el' : (M.cats || []).indexOf(c) >= 0 ? 'cat' : 'ign';
    if (role === 'geo') return (M.kat && M.kat[c]) || 'ign';
    return '';
  }
  VG.tplSave = function (role) {
    var M = SA.map[role]; if (!M) return; var T = SA.T[M.t]; if (!T) return;
    try { var A = tplAll(), P = A[role] = A[role] || {}; T.h.forEach(function (h, c) { var n = normH(h), s = colState(role, c); if (n && s) P[n] = s; }); localStorage.setItem(TPK, JSON.stringify(A)); } catch (e) { }
  };
  VG.tplClear = function () { try { localStorage.removeItem(TPK); } catch (e) { } SA.roleChanged(); toast('Pemetaan kolom yang diingat sudah dihapus; kolom ditebak ulang dari namanya.'); };
  var guessKat = function (h) { var n = String(h || '').trim().toLowerCase().replace(/[\s.]+/g, '_'); for (var i = 0; i < GRX.length; i++) if (GRX[i][1].test(n)) return GRX[i][0]; return 'code'; };
  /* tebakan dari isi: dua kolom angka berurutan dengan To > From di >= 90 % baris; Hole_ID = kolom teks (kolom 1 / 2) */
  function guessFT(T, skip) {
    var smp = T.r.slice(0, 300), best = -1;
    for (var i = 0; i + 1 < T.h.length; i++) {
      if (skip.indexOf(i) >= 0 || skip.indexOf(i + 1) >= 0) continue; var n = 0, ok = 0;
      for (var j = 0; j < smp.length; j++) { var a = numV(smp[j][i]), b = numV(smp[j][i + 1]); if (a === null || b === null) continue; n++; if (b > a && a >= 0) ok++; }
      if (n >= Math.min(5, smp.length) && ok >= n * 0.9) { best = i; break; }
    }
    return best;
  }
  function guessId(T) {
    var smp = T.r.slice(0, 300); if (!smp.length) return -1;
    for (var i = 0; i < Math.min(2, T.h.length); i++) { var n = 0; for (var j = 0; j < smp.length; j++) { var v = smp[j][i]; if (v != null && String(v).trim() !== '' && numV(v) === null) n++; } if (n >= smp.length * 0.9) return i; }
    return -1;
  }
  function applyKeys(role) {
    var M = SA.map[role]; if (!M) return false; var T = SA.T[M.t]; if (!T) return false; var P = tplGet(role), ch = false, set = function (k, c) { if (c >= 0 && M[k] !== c) { M[k] = c; ch = true; } };
    if (findCol(T, H.HOLE, -1) < 0) set('hole', guessId(T));
    if ((role === 'assay' || role === 'geo') && (findCol(T, H.FROM, -1) < 0 || findCol(T, H.TO, -1) < 0)) { var f = guessFT(T, [M.hole]); if (f >= 0) { set('fr', f); set('to', f + 1); } }
    T.h.forEach(function (h, c) { var s = P[normH(h)]; if (s && KEYS[role].indexOf(s) >= 0) { KEYS[role].forEach(function (k) { if (k !== s && M[k] === c) M[k] = -1; }); set(s, c); } });
    return ch;
  }
  var _ed = SA.elDefaults; SA.elDefaults = function () {
    _ed.apply(this, arguments); var M = SA.map.assay, T = SA.T[M.t], P = tplGet('assay'), keys = [M.hole, M.fr, M.to, M.samp];
    T.h.forEach(function (h, c) {
      var s = P[normH(h)]; if (!s || keys.indexOf(c) >= 0) return; var ie = M.els.indexOf(c), ic = M.cats.indexOf(c);
      if (s === 'el') { if (ie < 0) M.els.push(c); if (ic >= 0) M.cats.splice(ic, 1); } else if (s === 'cat') { if (ic < 0) M.cats.push(c); if (ie >= 0) M.els.splice(ie, 1); } else if (s === 'ign') { if (ie >= 0) M.els.splice(ie, 1); ic = M.cats.indexOf(c); if (ic >= 0) M.cats.splice(ic, 1); }
    });
    M.els.sort(function (a, b) { return a - b; }); M.cats.sort(function (a, b) { return a - b; });
  };
  var geoCand = function (M, T) { var f = feat(T), L = []; for (var c = 0; c < T.h.length; c++) { if (!T.h[c] || c === M.hole || c === M.fr || c === M.to) continue; var s = f.st[c]; if (s[0] + s[1] > 0) L.push(c); } return L; };
  var _gd = SA.geoDefaults; SA.geoDefaults = function () {
    _gd.apply(this, arguments); var M = SA.map.geo, T = SA.T[M.t], P = tplGet('geo'), K = M.kat = {};
    geoCand(M, T).forEach(function (c) { var s = P[normH(T.h[c])]; K[c] = (s && GKN[s]) ? s : (M.cats.indexOf(c) >= 0 ? guessKat(T.h[c]) : 'ign'); });
    M.cats = Object.keys(K).map(Number).filter(function (c) { return K[c] !== 'ign'; }).sort(function (a, b) { return a - b; });
  };
  var _bm = SA.buildMap; SA.buildMap = function () {
    _bm.apply(this, arguments); var M = SA.map, any = false;
    KS.forEach(function (r) { if (M[r] && applyKeys(r)) { any = true; if (r === 'assay') SA.elDefaults(); if (r === 'geo') SA.geoDefaults(); } });
    if (any) { document.querySelectorAll('#colMap select[data-r][data-k]').forEach(function (s) { var r = s.getAttribute('data-r'), k = s.getAttribute('data-k'); if (M[r] && M[r][k] != null) s.value = String(M[r][k]); }); SA.chkBoxes(); }
    var cm = g('colMap'); if (cm && !g('vgTplBar')) cm.insertAdjacentHTML('afterbegin', '<div id="vgTplBar" class="hint" style="margin:2px 0 6px">Pilihan kolom di panel ini <b>diingat</b> per nama kolom: file berikutnya dengan nama kolom sama langsung terpetakan. <a href="#" onclick="VG.tplClear();return false">Lupakan pilihan yang diingat</a></div>');
  };
  var _mc = SA.mapChanged; SA.mapChanged = function (s) { _mc.apply(this, arguments); VG.tplSave(s.getAttribute('data-r')); };
  var _tg = SA.tog; SA.tog = function (rk) { _tg.apply(this, arguments); VG.tplSave(rk.split('.')[0]); };
  /* kotak "Atribut geologi / domain": tiap kolom memilih kategori (bukan sekadar dicentang) */
  var _cb = SA.chkBoxes; SA.chkBoxes = function () {
    _cb.apply(this, arguments); var M = SA.map.geo, el = g('gcBox'); if (!M || !el) return; var T = SA.T[M.t], K = M.kat || {}, f = feat(T);
    var ex = function (c) { var a = []; for (var i = 0; i < T.r.length && a.length < 3; i++) { var v = txt(T.r[i][c]); if (v && a.indexOf(v) < 0) a.push(v); } return a.join(' · '); };
    el.innerHTML = '<table class="vgkt"><tr><th>Kolom</th><th>Contoh isi</th><th>Kategori</th></tr>' + geoCand(M, T).map(function (c) {
      var k = K[c] || 'ign', bad = k !== 'ign' && !catDict(T, c, f.st[c][1] > 0);
      return '<tr><td>' + esc(T.h[c]) + '</td><td class="ex" title="' + esc(ex(c)) + '">' + esc(ex(c)) + '</td><td><select data-gc="' + c + '" onchange="VG.gk(' + c + ',this.value)">' + GK.map(function (x) { return '<option value="' + x[0] + '"' + (x[0] === k ? ' selected' : '') + '>' + x[1] + '</option>'; }).join('') + '</select>' +
        (bad ? '<div class="hint" style="color:#b26a00">nilai unik &gt; 60 atau kosong: tidak dipakai sebagai atribut</div>' : '') + '</td></tr>';
    }).join('') + '</table>';
  };
  VG.gk = function (c, v) { var M = SA.map.geo; if (!M) return; M.kat = M.kat || {}; M.kat[c] = v; M.cats = Object.keys(M.kat).map(Number).filter(function (x) { return M.kat[x] !== 'ign'; }).sort(function (a, b) { return a - b; }); VG.tplSave('geo'); SA.preview(); };
  /* kategori geologi ikut ke data proyek (geoCat[i].kat) */
  var _bd = SA.build; SA.build = function () {
    var D = _bd.apply(this, arguments), M = SA.map.geo;
    if (M && M.kat && D.geoCat && D.geoCat.length) { var T = SA.T[M.t], byN = {}; M.cats.forEach(function (c) { byN[T.h[c]] = M.kat[c]; }); D.geoCat.forEach(function (gc) { if (byN[gc.n]) gc.kat = byN[gc.n]; }); }
    return D;
  };

  /* ======================= 2. pemeriksaan tambahan di laporan validasi import ======================= */
  var _va = SA.validate; SA.validate = function (D) {
    var I = _va.apply(this, arguments), add = function (lv, kat, hole, ket) { I.push([lv, kat, hole, ket]); }, C = {}, L = {};
    D.collars.forEach(function (c) { C[c[0]] = 1; L[String(c[0]).toLowerCase()] = c[0]; });
    var cs = {}; [['surveys', 'Survey'], ['assays', 'Assay'], ['geoRows', 'Geologi']].forEach(function (p) { (D[p[0]] || []).forEach(function (r) { var id = r[0]; if (C[id] || cs[p[1] + id]) return; var o = L[String(id).toLowerCase()]; if (o) { cs[p[1] + id] = 1; add('PERINGATAN', 'Hole ID beda huruf besar/kecil', id, p[1] + ' "' + id + '" vs Collar "' + o + '" (dianggap lubang lain; samakan penulisannya)'); } }); });
    if (D.collars.length >= 8) [[1, 'Easting', 150], [2, 'Northing', 150], [3, 'RL', 40]].forEach(function (a) {
      var v = D.collars.map(function (c) { return c[a[0]]; }).sort(function (p, q) { return p - q; }), med = v[v.length >> 1], dv = v.map(function (x) { return Math.abs(x - med); }).sort(function (p, q) { return p - q; }), th = 8 * dv[dv.length >> 1] * 1.4826 + a[2];
      D.collars.forEach(function (c) { if (Math.abs(c[a[0]] - med) > th) add('PERINGATAN', 'Koordinat jauh dari lubang lain', c[0], a[1] + ' ' + c[a[0]] + ' (median ' + Math.round(med) + '): salah ketik?'); });
    });
    var nbA = 0; D.surveys.forEach(function (s) { if (s[3] < 0 || s[3] > 360) nbA++; }); if (nbA) add('PERINGATAN', 'Azimuth di luar 0–360', '-', nbA + ' baris survey (dipakai apa adanya)');
    var iau = -1; D.elements.forEach(function (e, k) { if (iau < 0 && /^(au|gold|emas)/i.test(e)) iau = k; });
    if (iau >= 0) { var hi = {}, nh = 0; D.assays.forEach(function (a) { var v = a[4][iau]; if (v !== null && v > 500) { nh++; hi[a[0]] = (hi[a[0]] || 0) + 1; } }); Object.keys(hi).forEach(function (h) { add('PERINGATAN', D.elements[iau] + ' > 500', h, hi[h] + ' sampel: cek satuan (ppb vs ppm) / salah ketik'); }); }
    var M = SA.map || {};
    if (M.assay && SA.T[M.assay.t]) {
      var Ta = SA.T[M.assay.t];
      M.assay.els.forEach(function (c) { var n = 0, ex = []; Ta.r.forEach(function (r) { var v = r[c]; if (v == null || typeof v === 'number') return; var s = String(v).trim(); if (NOTV.test(s) || /^[<>]\s*[\d.,]+$/.test(s)) return; if (numV(s) === null) { n++; if (ex.length < 3 && ex.indexOf(s) < 0) ex.push(s); } }); if (n) add('PERINGATAN', 'Nilai bukan angka ' + Ta.h[c], '-', n + ' sampel (mis. ' + ex.join(', ') + ') dianggap kosong'); });
      if (M.assay.samp >= 0) { var ns = 0; D.assays.forEach(function (a) { if (a[3] === 'N/A') ns++; }); if (ns) add('PERINGATAN', 'Sample ID kosong', '-', ns + ' interval assay'); }
    }
    (D.geoCat || []).forEach(function (gc, k) { if (gc.kat !== 'lith') return; var e = {}; D.geoRows.forEach(function (r) { if (!(r[3][k] >= 0)) e[r[0]] = (e[r[0]] || 0) + 1; }); Object.keys(e).forEach(function (h) { add('PERINGATAN', 'Litologi kosong', h, e[h] + ' interval (' + gc.n + ')'); }); });
    SA.VI = I; return I;
  };
  var _vh = SA.valHtml; SA.valHtml = function () { return _vh.apply(this, arguments) + '<br><button type="button" class="vgOpenB" onclick="VG.openSlot()" title="Tabel yang dipilih untuk diimport: sel bermasalah disorot, bisa diedit lalu diekspor">&#9638; Validasi &amp; edit tabel</button>'; };

  /* ======================= 3. jendela Validasi & edit tabel ======================= */
  var vnum = function (v) { if (v == null) return NaN; if (typeof v === 'number') return isFinite(v) ? v : NaN; var s = String(v).trim().replace(',', '.'); if (!s) return NaN; return /^[-+]?(\d+\.?\d*|\.\d+)([eE][-+]?\d+)?$/.test(s) ? +s : NaN; };
  var sv = function (v) { return v == null ? '' : String(v).trim(); };
  function vgCheck(T) {
    var R = {}; KS.forEach(function (k) { if (T[k]) R[k] = { iss: [], cell: new Map(), rows: new Map(), rule: new Map() }; });
    var add = function (k, r, c, lv, rule, m) {
      var o = R[k]; o.iss.push({ r: r, c: c, lv: lv, rule: rule, msg: m }); var key = r * 1024 + c, p = o.cell.get(key); if (!p) o.cell.set(key, { lv: lv, m: [m] }); else { if (lv === 'E') p.lv = 'E'; p.m.push(m); }
      if (lv === 'E' || !o.rows.has(r)) o.rows.set(r, lv === 'E' ? 'E' : (o.rows.get(r) || 'W')); var q = o.rule.get(rule) || { lv: lv, n: 0 }; q.n++; if (lv === 'E') q.lv = 'E'; o.rule.set(rule, q);
    };
    var ix = function (t, r) { return t.map.indexOf(r); }, ids = new Map(), idl = new Map(), dep = new Map(), haveC = false, prev = new Set();
    if (!T.collar) (window.collars || (SA.D && SA.D.collars) || []).forEach(function (c) { prev.add(String(c[0])); });
    var C = T.collar;
    if (C) {
      haveC = true; var tb = C.tb, iid = ix(C, 'id'), I = { x: ix(C, 'x'), y: ix(C, 'y'), z: ix(C, 'z') }, idp = ix(C, 'dep'), idi = ix(C, 'dip'), iaz = ix(C, 'az'), V = { x: [], y: [], z: [] };
      tb.rows.forEach(function (r, i) {
        var id = iid >= 0 ? sv(r[iid]) : ''; if (iid >= 0) { if (!id) add('collar', i, iid, 'E', 'Hole_ID kosong', 'Hole_ID kosong'); else if (ids.has(id)) add('collar', i, iid, 'E', 'Hole_ID ganda', 'Hole_ID ganda (juga di baris ' + (ids.get(id) + 2) + ')'); else { ids.set(id, i); idl.set(id.toLowerCase(), id); } }
        ['x', 'y', 'z'].forEach(function (a) { var c = I[a]; if (c < 0) return; var v = vnum(r[c]); if (!isFinite(v)) add('collar', i, c, 'E', 'Koordinat bukan angka', (a === 'z' ? 'RL' : a.toUpperCase()) + ' kosong / bukan angka'); else V[a].push([v, i]); });
        if (idp >= 0) { var s = sv(r[idp]); if (s === '') add('collar', i, idp, 'W', 'Kedalaman kosong', 'Kedalaman total kosong'); else { var v = vnum(s); if (!isFinite(v)) add('collar', i, idp, 'E', 'Bukan angka', 'Kedalaman bukan angka'); else if (v <= 0) add('collar', i, idp, 'W', 'Kedalaman ≤ 0', 'Kedalaman total ≤ 0'); else if (id) dep.set(id, v); } }
        if (idi >= 0 && sv(r[idi]) !== '') { var d = vnum(r[idi]); if (!isFinite(d)) add('collar', i, idi, 'E', 'Bukan angka', 'Dip bukan angka'); else if (Math.abs(d) > 90) add('collar', i, idi, 'E', 'Dip di luar −90…90', 'Dip di luar −90…90'); }
        if (iaz >= 0 && sv(r[iaz]) !== '') { var z = vnum(r[iaz]); if (!isFinite(z)) add('collar', i, iaz, 'E', 'Bukan angka', 'Azimuth bukan angka'); else if (z < 0 || z > 360) add('collar', i, iaz, 'E', 'Azimuth di luar 0…360', 'Azimuth di luar 0…360'); }
      });
      ['x', 'y', 'z'].forEach(function (a) {
        var A = V[a]; if (A.length < 8) return; var s = A.map(function (q) { return q[0]; }).sort(function (p, q) { return p - q; }), med = s[s.length >> 1], dv = s.map(function (v) { return Math.abs(v - med); }).sort(function (p, q) { return p - q; }), th = 8 * dv[dv.length >> 1] * 1.4826 + (a === 'z' ? 40 : 150);
        A.forEach(function (q) { if (Math.abs(q[0] - med) > th) add('collar', q[1], I[a], 'W', 'Koordinat jauh dari lubang lain', (a === 'z' ? 'RL' : a.toUpperCase()) + ' ' + q[0] + ' jauh dari lubang lain (median ' + Math.round(med) + '): salah ketik?'); });
      });
    }
    var chkId = function (k, i, c, id) {
      if (!id) { add(k, i, c, 'E', 'Hole_ID kosong', 'Hole_ID kosong'); return; }
      if (haveC) { if (ids.has(id)) return; var o = idl.get(id.toLowerCase()); if (o) add(k, i, c, 'E', 'Beda huruf besar/kecil dengan Collar', 'Beda huruf besar/kecil dengan Collar "' + o + '"'); else add(k, i, c, 'W', 'Hole_ID tidak ada di Collar', 'Hole_ID tidak ada di Collar (interval tidak ditampilkan)'); return; }
      if (prev.size && !prev.has(id)) add(k, i, c, 'W', 'Hole_ID belum ada di data', 'Hole_ID belum ada di Collar proyek');
    };
    var S = T.survey;
    if (S) {
      var tbs = S.tb, sid = ix(S, 'id'), isd = ix(S, 'sd'), sdi = ix(S, 'dip'), saz = ix(S, 'az'), seen = new Map();
      tbs.rows.forEach(function (r, i) {
        var id = sid >= 0 ? sv(r[sid]) : ''; if (sid >= 0) chkId('survey', i, sid, id);
        if (isd >= 0) { var v = vnum(r[isd]); if (!isFinite(v)) add('survey', i, isd, 'E', 'Bukan angka', 'Kedalaman survey kosong / bukan angka'); else if (v < 0) add('survey', i, isd, 'E', 'Kedalaman negatif', 'Kedalaman negatif'); else { var key = id + '|' + v; if (seen.has(key)) add('survey', i, isd, 'W', 'Kedalaman survey ganda', 'Kedalaman ganda (baris ' + (seen.get(key) + 2) + ')'); else seen.set(key, i); if (dep.has(id) && v > dep.get(id) + 0.5) add('survey', i, isd, 'W', 'Melebihi kedalaman Collar', 'Lebih dalam dari kedalaman Collar (' + dep.get(id) + ' m)'); } }
        if (sdi >= 0) { var d = vnum(r[sdi]); if (!isFinite(d)) add('survey', i, sdi, 'E', 'Bukan angka', 'Dip kosong / bukan angka'); else if (Math.abs(d) > 90) add('survey', i, sdi, 'E', 'Dip di luar −90…90', 'Dip di luar −90…90'); }
        if (saz >= 0) { var z = vnum(r[saz]); if (!isFinite(z)) add('survey', i, saz, 'E', 'Bukan angka', 'Azimuth kosong / bukan angka'); else if (z < 0 || z > 360) add('survey', i, saz, z < -360 || z > 720 ? 'E' : 'W', 'Azimuth di luar 0…360', 'Azimuth di luar 0…360'); }
      });
    }
    ['assay', 'geo'].forEach(function (k) {
      var t = T[k]; if (!t) return; var tb = t.tb, iid = ix(t, 'id'), ifr = ix(t, 'fr'), ito = ix(t, 'to'), HH = new Map();
      tb.rows.forEach(function (r, i) {
        var id = iid >= 0 ? sv(r[iid]) : ''; if (iid >= 0) chkId(k, i, iid, id); if (ifr < 0 || ito < 0) return;
        var a = vnum(r[ifr]), b = vnum(r[ito]), ok = true;
        if (!isFinite(a)) { add(k, i, ifr, 'E', 'Bukan angka', 'From kosong / bukan angka'); ok = false; } else if (a < 0) { add(k, i, ifr, 'E', 'From negatif', 'From negatif'); ok = false; }
        if (!isFinite(b)) { add(k, i, ito, 'E', 'Bukan angka', 'To kosong / bukan angka'); ok = false; }
        if (ok && b <= a) { add(k, i, ito, 'E', 'To ≤ From', 'To (' + b + ') ≤ From (' + a + ')'); ok = false; }
        if (ok && id) { if (!HH.has(id)) HH.set(id, []); HH.get(id).push([a, b, i]); if (dep.has(id) && b > dep.get(id) + 0.05) add(k, i, ito, 'W', 'Melebihi kedalaman Collar', 'To melebihi kedalaman Collar (' + dep.get(id) + ' m)'); }
      });
      HH.forEach(function (L) {
        L.sort(function (p, q) { return p[0] - q[0] || p[1] - q[1]; });
        for (var j = 1; j < L.length; j++) {
          var p = L[j - 1], q = L[j];
          if (Math.abs(q[0] - p[0]) < 1e-6 && Math.abs(q[1] - p[1]) < 1e-6) add(k, q[2], ifr, 'E', 'Interval ganda', 'Interval ganda dengan baris ' + (p[2] + 2));
          else if (q[0] < p[1] - 1e-6) add(k, q[2], ifr, 'E', 'Interval tumpang tindih', 'Tumpang tindih dengan baris ' + (p[2] + 2) + ' (' + p[0] + '–' + p[1] + ')');
          else if (q[0] > p[1] + 1e-6) add(k, q[2], ifr, 'W', 'Celah interval', 'Celah ' + (+(q[0] - p[1]).toFixed(3)) + ' m setelah baris ' + (p[2] + 2));
        }
      });
      if (k === 'assay') {
        var iau = ix(t, 'au'), isid = ix(t, 'sid'), EL = [], sids = new Map(); if (isid >= 0 && !tb.rows.some(function (r) { var s = sv(r[isid]); return s && s !== 'N/A'; })) isid = -1;/* kolom Sample_ID kosong seluruhnya: data memang tanpa Sample ID */ t.map.forEach(function (r, i) { if (r === 'el' || r === 'au') EL.push(i); });
        tb.rows.forEach(function (r, i) {
          EL.forEach(function (c) { var s = r[c]; if (s == null || (typeof s !== 'number' && NOTV.test(s))) return; var x = String(s).trim(); if (/^[<>]\s*[\d.,]+$/.test(x)) return; var v = vnum(x); if (!isFinite(v)) add(k, i, c, 'W', 'Nilai bukan angka', '"' + x + '" bukan angka (dianggap kosong)'); else if (c === iau && v > 500) add(k, i, c, 'W', 'Au sangat tinggi', 'Au ' + v + ' > 500: cek satuan / salah ketik'); });
          if (isid >= 0) { var s2 = sv(r[isid]); if (!s2 || s2 === 'N/A') add(k, i, isid, 'W', 'Sample_ID kosong', 'Sample_ID kosong'); else if (sids.has(s2)) add(k, i, isid, 'E', 'Sample_ID ganda', 'Sample_ID ganda (baris ' + (sids.get(s2) + 2) + ')'); else sids.set(s2, i); }
        });
      }
      if (k === 'geo') { var il = ix(t, 'lith'); if (il >= 0) tb.rows.forEach(function (r, i) { if (!sv(r[il])) add(k, i, il, 'W', 'Litologi kosong', 'Litologi kosong'); }); }
    });
    for (var k in R) R[k].iss.sort(function (p, q) { return p.r - q.r || p.c - q.c; });
    return R;
  }
  VG.check = vgCheck;
  /* ---- tabel dari layar import (SA.T, diedit di tempat) ---- */
  function slotTables() {
    var T = {}, M = SA.map || {};
    KS.forEach(function (role) {
      var i = selV(role), m = M[role]; if (i < 0 || !m || m.t !== i) return; var t = SA.T[i], map = t.h.map(function () { return 'ign'; }), put = function (c, r) { if (c != null && c >= 0) map[c] = r; };
      if (role === 'collar') { map = map.map(function () { return 'oth'; }); put(m.hole, 'id'); put(m.e, 'x'); put(m.n, 'y'); put(m.rl, 'z'); put(m.td, 'dep'); put(m.dip, 'dip'); put(m.azi, 'az'); }
      else if (role === 'survey') { map = map.map(function () { return 'oth'; }); put(m.hole, 'id'); put(m.dep, 'sd'); put(m.dip, 'dip'); put(m.azi, 'az'); }
      else if (role === 'assay') { put(m.hole, 'id'); put(m.fr, 'fr'); put(m.to, 'to'); put(m.samp, 'sid'); var au = -1; (m.els || []).forEach(function (c) { if (au < 0 && /^(au|gold|emas)/i.test(t.h[c])) au = c; put(c, c === au ? 'au' : 'el'); }); (m.cats || []).forEach(function (c) { put(c, 'oth'); }); }
      else { put(m.hole, 'id'); put(m.fr, 'fr'); put(m.to, 'to'); (m.cats || []).forEach(function (c) { put(c, (m.kat && m.kat[c]) || 'code'); }); }
      T[role] = { name: t.src || t.name, sheet: t.name, src: t, tb: { hd0: t.h, rows: t.r, sep: t.sep || ',' }, map: map };
    });
    return T;
  }
  /* ---- tabel dari database proyek (SA.D) ---- */
  function dsTables() {
    var D = SA.D || {}, T = {}, nm = (SA.pname || 'proyek'), bl = function (v) { return v == null ? '' : v; };
    if ((D.collars || []).length) {
      var bm = D.benchmap || {}, hasG = Object.keys(bm).length > 0;
      T.collar = { name: nm + '_collar', tb: { hd0: ['Hole_ID', 'X', 'Y', 'Z', 'Total_Depth'].concat(hasG ? ['Grup'] : []), rows: D.collars.map(function (c) { var r = [c[0], c[1], c[2], c[3], c[4] ? c[4] : '']; if (hasG) r.push(bl(bm[c[0]])); return r; }), sep: ',' }, map: ['id', 'x', 'y', 'z', 'dep'].concat(hasG ? ['oth'] : []) };
    }
    if ((D.surveys || []).length) T.survey = { name: nm + '_survey', tb: { hd0: ['Hole_ID', 'Depth', 'Dip', 'Azimuth'], rows: D.surveys.map(function (s) { return s.slice(0, 4); }), sep: ',' }, map: ['id', 'sd', 'dip', 'az'] };
    if ((D.assays || []).length) {
      var el = D.elements || [], ac = D.asCat || [], au = -1; el.forEach(function (e, k) { if (au < 0 && /^(au|gold|emas)/i.test(e)) au = k; });
      T.assay = { name: nm + '_assay', tb: { hd0: ['Hole_ID', 'From', 'To', 'Sample_ID'].concat(el, ac.map(function (c) { return c.n; })), rows: D.assays.map(function (a) { return [a[0], a[1], a[2], a[3] === 'N/A' ? '' : a[3]].concat(a[4].map(bl), (a[5] || []).map(function (v, k) { return v >= 0 && ac[k] ? ac[k].d[v] : ''; })); }), sep: ',' },
        map: ['id', 'fr', 'to', 'sid'].concat(el.map(function (e, k) { return k === au ? 'au' : 'el'; }), ac.map(function () { return 'oth'; })) };
    }
    if ((D.geoRows || []).length) {
      var gc = D.geoCat || [];
      T.geo = { name: nm + '_geologi', tb: { hd0: ['Hole_ID', 'From', 'To'].concat(gc.map(function (c) { return c.n; })), rows: D.geoRows.map(function (r) { return [r[0], r[1], r[2]].concat((r[3] || []).map(function (v, k) { return v >= 0 && gc[k] ? gc[k].d[v] : ''; })); }), sep: ',' },
        map: ['id', 'fr', 'to'].concat(gc.map(function (c) { return c.kat || 'code'; })) };
    }
    return T;
  }
  /* tabel hasil edit -> larik database proyek (aturan sama dengan SA.build: baris tak valid dilewati) */
  function dsRebuild(T) {
    var D = SA.D, out = {}, skip = { collar: 0, survey: 0, assay: 0, geo: 0 }, N = function (v) { return typeof v === 'number' ? (isFinite(v) ? v : null) : numV(v); };
    var dict = function (old, vals) { var d = (old || []).slice(), ix = {}; d.forEach(function (v, i) { ix[v] = i; }); return { d: d, of: function (v) { v = sv(v); if (!v) return -1; if (!(v in ix)) { ix[v] = d.length; d.push(v); } return ix[v]; } }; };
    if (T.collar) { var seen = {}, bm = {}, hasG = T.collar.tb.hd0.length > 5; out.collars = []; T.collar.tb.rows.forEach(function (r) { var id = sv(r[0]), x = N(r[1]), y = N(r[2]), z = N(r[3]), td = N(r[4]); if (!id || seen[id] || x === null || y === null || z === null) { skip.collar++; return; } seen[id] = 1; out.collars.push([id, x, y, z, td === null ? 0 : td]); if (hasG) bm[id] = sv(r[5]); }); if (hasG) out.benchmap = bm; }
    if (T.survey) { out.surveys = []; T.survey.tb.rows.forEach(function (r) { var id = sv(r[0]), a = N(r[1]), b = N(r[2]), z = N(r[3]); if (!id || a === null || b === null || z === null || a < 0 || Math.abs(b) > 90 || z < -360 || z > 720) { skip.survey++; return; } out.surveys.push([id, a, b, z]); }); }
    if (T.assay) {
      var ne = (D.elements || []).length, ac = (D.asCat || []).map(function (c) { return dict(c.d); }); out.assays = [];
      T.assay.tb.rows.forEach(function (r) { var id = sv(r[0]), f = N(r[1]), t = N(r[2]); if (!id || f === null || t === null || !(t > f) || f < 0) { skip.assay++; return; } var els = []; for (var k = 0; k < ne; k++)els.push(N(r[4 + k])); out.assays.push([id, f, t, sv(r[3]) || 'N/A', els, ac.map(function (q, k) { return q.of(r[4 + ne + k]); })]); });
      out.asCat = (D.asCat || []).map(function (c, k) { return Object.assign({}, c, { d: ac[k].d }); });
    }
    if (T.geo) {
      var gc = (D.geoCat || []).map(function (c) { return dict(c.d); }); out.geoRows = [];
      T.geo.tb.rows.forEach(function (r) { var id = sv(r[0]), f = N(r[1]), t = N(r[2]); if (!id || f === null || t === null || !(t > f) || f < 0) { skip.geo++; return; } out.geoRows.push([id, f, t, gc.map(function (q, k) { return q.of(r[3 + k]); })]); });
      out.geoCat = (D.geoCat || []).map(function (c, k) { return Object.assign({}, c, { d: gc[k].d }); });
    }
    return { out: out, skip: skip };
  }

  /* ---- CSS + jendela ---- */
  var css = document.createElement('style'); css.textContent =
    '#vgw{position:fixed;z-index:2147483000;left:3vw;top:4vh;width:94vw;height:88vh;min-width:640px;min-height:320px;resize:both;overflow:hidden;background:#fff;color:#1d2433;border:1px solid #c9ced8;border-radius:8px;box-shadow:0 10px 40px #0004;font-size:12px;display:none;flex-direction:column}#vgw.on{display:flex}' +
    '#vgh{display:flex;align-items:center;gap:8px;padding:6px 10px;background:#1b2333;color:#fff;cursor:move;flex:none;border-radius:8px 8px 0 0}#vgh b{font-size:13px}#vgh .note{color:#c8d0e0}#vgh button{background:transparent;color:#fff;border:0;font-size:15px;cursor:pointer}' +
    '#vgbar{display:flex;flex-wrap:wrap;gap:4px;align-items:center;padding:5px 8px;border-bottom:1px solid #e3e6ec;flex:none}#vgbar button{margin:0;padding:2px 8px;font-size:12px}#vgbar input[type=search]{width:140px;padding:2px 5px}#vgbar .pri{background:#1f6feb;color:#fff;border-color:#1f6feb}' +
    '#vgtabs{display:flex;gap:2px;margin-right:6px}#vgtabs button.on{background:#1f2d6b;color:#fff;border-color:#1f2d6b}#vgtabs i{font-style:normal;font-size:10px;border-radius:8px;padding:0 5px;margin-left:4px;color:#fff;background:#c62828}#vgtabs i.w{background:#e09a00}#vgtabs i.ok{background:#2e7d32}' +
    '#vgmain{flex:1;display:flex;gap:8px;padding:6px 8px;min-height:0}#vggw{flex:1;display:flex;flex-direction:column;min-width:0;border:1px solid #b9c0cc}' +
    '#vghd{overflow:hidden;flex:none;background:#eef1f6}#vggrid{flex:1;overflow:auto;position:relative;outline:none;background:#fff}' +
    '#vggw table{border-collapse:collapse;table-layout:fixed;font:12px Segoe UI,Arial,sans-serif}#vggrid table{position:absolute;left:0;top:0}' +
    '#vggw td,#vggw th{border:1px solid #d6dae1;height:22px;box-sizing:border-box;padding:0 4px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;line-height:20px;color:#1d2433}' +
    '#vghd th{font-weight:600;color:#1f2d6b;text-align:left;cursor:pointer;line-height:15px;height:36px;vertical-align:top;padding-top:2px}#vghd th small{display:block;font-weight:400;color:#667085;font-size:10px}#vghd th.srt:after{content:" \\25B2";font-size:9px}#vghd th.srt.dn:after{content:" \\25BC"}' +
    '#vggw .rn{background:#eef1f6;color:#667085;text-align:right;position:sticky;left:0;z-index:1;cursor:pointer;font-size:11px}' +
    '#vggrid td.E{background:#ffd6d6}#vggrid td.W{background:#fff0b8}#vggrid td.ed{color:#1849a9;font-weight:600}#vggrid td.sel{outline:2px solid #1f6feb;outline-offset:-2px}#vggrid tr.rs td:not(.rn){box-shadow:inset 0 0 0 999px #1f6feb1c}' +
    '#vggrid td.rn.E{background:#c62828;color:#fff}#vggrid td.rn.W{background:#e09a00;color:#fff}#vggrid td input{width:100%;height:20px;border:0;outline:none;padding:0;font:inherit;background:#fff}' +
    '#vgside{width:300px;flex:none;display:flex;flex-direction:column;min-height:0;gap:4px}#vgside .note{color:#555}#vgrules{max-height:38%;overflow:auto;border:1px solid #e3e6ec;border-radius:4px}#vgiss{flex:1;overflow:auto;border:1px solid #e3e6ec;border-radius:4px}' +
    '#vgrules div,#vgiss div{padding:2px 6px;cursor:pointer;border-bottom:1px solid #f0f2f5}#vgrules div:hover,#vgiss div:hover{background:#eef3ff}#vgrules div.on{background:#dfe8ff}' +
    '#vgrules b,#vgiss b{display:inline-block;min-width:10px;border-radius:3px;padding:0 4px;color:#fff;font-size:10px;margin-right:4px}.vgE{background:#c62828}.vgW{background:#e09a00}' +
    '#vgft{flex:none;padding:3px 8px;border-top:1px solid #e3e6ec;color:#555;display:flex;gap:10px;align-items:center}#vgft .note{flex:1}' +
    '#vgToast{position:fixed;left:50%;bottom:30px;transform:translateX(-50%);background:#1b2333;color:#fff;padding:7px 14px;border-radius:6px;z-index:2147483001;font-size:12px;opacity:0;transition:opacity .2s;pointer-events:none}#vgToast.on{opacity:1}' +
    'table.vgkt{border-collapse:collapse;width:100%}table.vgkt td,table.vgkt th{border-bottom:1px solid #e3e6ec;padding:2px 4px;text-align:left;vertical-align:middle;font-size:12px}table.vgkt td.ex{color:#667085;max-width:180px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}table.vgkt select{width:100%}' +
    '.vgsl{font-size:11px}.vgsl a{margin-right:2px}.vgOpenB{margin-top:6px}';
  document.head.appendChild(css);
  var W = null, V = { src: null, k: null, T: null, R: null, view: [], sel: { r: 0, c: 0 }, rs: new Set(), anchor: null, sort: null, rule: null, U: [], ed: new WeakMap(), dirty: false, rowH: 22, widths: [], editing: null };
  var NL = function (n) { return Number(n).toLocaleString('id-ID'); };
  function mk() {
    if (W) return; W = document.createElement('div'); W.id = 'vgw';
    W.innerHTML = '<div id="vgh"><b>Validasi &amp; edit tabel</b><span id="vgsrc" class="note"></span><span style="flex:1"></span><button id="vgx" title="Tutup">&#10005;</button></div>' +
      '<div id="vgbar"><span id="vgtabs"></span><input type="search" id="vgq" placeholder="Cari Hole_ID / nilai"><label style="margin:0;display:flex;gap:4px;align-items:center"><input type="checkbox" id="vgonly">Hanya baris bermasalah</label>' +
      '<button id="vgmap" title="Atur kategori tiap kolom di panel Pemetaan kolom (layar import)">Kolom…</button><button id="vgadd" title="Sisipkan baris di bawah sel terpilih">+ Baris</button><button id="vgdel" title="Hapus baris terpilih (klik nomor baris; Shift+klik = rentang)">Hapus baris</button><button id="vgun" title="Batalkan edit terakhir (Ctrl+Z)">&#8630; Batal</button>' +
      '<span style="flex:1"></span><button id="vgexp" title="Ekspor tabel ini ke CSV (header &amp; pemisah asli)">&#8681; CSV tabel ini</button><button id="vgexa" title="Ekspor semua tabel">&#8681; Semua tabel</button><button id="vgexi" title="Ekspor daftar masalah">&#8681; Laporan masalah</button><button id="vggo" class="pri"></button></div>' +
      '<div id="vgmain"><div id="vggw"><div id="vghd"><table id="vght"></table></div><div id="vggrid" tabindex="0"><div id="vgsp"></div><table id="vgbt"></table></div></div>' +
      '<div id="vgside"><div class="note"><b>Ringkasan</b> (klik = saring)</div><div id="vgrules"></div><div class="note"><b>Daftar masalah</b> (klik = ke sel)</div><div id="vgiss"></div></div></div>' +
      '<div id="vgft"><span class="note" id="vgst"></span><span class="note" style="flex:none">Klik dua kali / F2 / ketik = edit · Enter = simpan · Esc = batal · Ctrl+V dari Excel · Ctrl+Z = batal</span></div>';
    document.body.appendChild(W);
    /* geser jendela lewat kepala */
    var hd = g('vgh'); hd.addEventListener('mousedown', function (e) { if (e.target.tagName === 'BUTTON') return; var r = W.getBoundingClientRect(), dx = e.clientX - r.left, dy = e.clientY - r.top; var mv = function (ev) { W.style.left = Math.max(0, ev.clientX - dx) + 'px'; W.style.top = Math.max(0, ev.clientY - dy) + 'px'; }, up = function () { document.removeEventListener('mousemove', mv); document.removeEventListener('mouseup', up); }; document.addEventListener('mousemove', mv); document.addEventListener('mouseup', up); e.preventDefault(); });
    wire();
  }
  var curT = function () { return V.T && V.T[V.k]; };
  function revalidate(now) { clearTimeout(V.rvT); var run = function () { V.R = vgCheck(V.T); buildView(); tabs(); side(); draw(); }; if (now) run(); else V.rvT = setTimeout(run, 250); }
  function tabs() {
    g('vgtabs').innerHTML = KS.filter(function (k) { return V.T[k]; }).map(function (k) { var R = V.R[k], E = 0, Wn = 0; if (R) R.iss.forEach(function (q) { if (q.lv === 'E') E++; else Wn++; }); return '<button data-k="' + k + '" class="' + (k === V.k ? 'on' : '') + '">' + KN[k] + (E ? '<i>' + NL(E) + '</i>' : '') + (Wn ? '<i class="w">' + NL(Wn) + '</i>' : '') + (!E && !Wn ? '<i class="ok">&#10003;</i>' : '') + '</button>'; }).join('');
    g('vgtabs').querySelectorAll('button').forEach(function (b) { b.onclick = function () { commit(); V.k = b.getAttribute('data-k'); V.sel = { r: 0, c: 0 }; V.rs.clear(); V.sort = null; V.rule = null; layout(); buildView(); tabs(); side(); draw(); }; });
  }
  function buildView() {
    var t = curT(); if (!t) { V.view = []; return; } var R = V.R[V.k], rows = t.tb.rows, n = rows.length, q = g('vgq').value.trim().toLowerCase(), only = g('vgonly').checked, v = [];
    var ruleRows = V.rule ? new Set(R.iss.filter(function (x) { return x.rule === V.rule; }).map(function (x) { return x.r; })) : null;
    for (var i = 0; i < n; i++) { if (only && !R.rows.has(i)) continue; if (ruleRows && !ruleRows.has(i)) continue; if (q && !rows[i].some(function (x) { return x != null && String(x).toLowerCase().indexOf(q) >= 0; })) continue; v.push(i); }
    if (V.sort) {
      var c = V.sort.c, dn = V.sort.dn, num = v.every(function (i) { var x = rows[i][c]; return x == null || String(x).trim() === '' || isFinite(vnum(x)); });
      v.sort(function (a, b) { var x = rows[a][c], y = rows[b][c], r; if (num) { var p = vnum(x), q2 = vnum(y); r = (isFinite(p) ? p : -Infinity) - (isFinite(q2) ? q2 : -Infinity); } else r = String(x == null ? '' : x).localeCompare(String(y == null ? '' : y), 'id', { numeric: true }); return (dn ? -r : r) || a - b; });
    }
    V.view = v; if (V.sel.r >= v.length) V.sel.r = Math.max(0, v.length - 1); g('vgsp').style.height = (v.length * V.rowH + 2) + 'px';
  }
  var RL = { id: 'Hole_ID', x: 'Easting / X', y: 'Northing / Y', z: 'RL / Z', dep: 'Kedalaman total', dip: 'Dip', az: 'Azimuth', sd: 'Kedalaman survey', fr: 'From', to: 'To', au: 'Au (unsur utama)', el: 'Unsur', sid: 'Sample_ID', oth: 'Lainnya', ign: 'Tidak dipakai' };
  var rlab = function (r) { return RL[r] || GKN[r] || r; };
  function layout() {
    var t = curT(); if (!t) return; var tb = t.tb, smp = tb.rows.slice(0, 300);
    V.widths = tb.hd0.map(function (h, c) { var m = Math.max(String(h == null ? '' : h).length, rlab(t.map[c]).length * 0.8); smp.forEach(function (r) { var L = String(r[c] == null ? '' : r[c]).length; if (L > m) m = L; }); return Math.round(Math.min(260, Math.max(56, m * 7.2 + 14))); });
    var rnw = Math.max(46, String(tb.rows.length + 1).length * 8 + 14), cg = '<colgroup><col style="width:' + rnw + 'px">' + V.widths.map(function (w) { return '<col style="width:' + w + 'px">'; }).join('') + '</colgroup>', tw = rnw + V.widths.reduce(function (a, b) { return a + b; }, 0);
    V.cg = cg; V.tw = tw; V.rnw = rnw; g('vght').style.width = tw + 'px'; g('vgbt').style.width = tw + 'px';
    g('vght').innerHTML = cg + '<tr><th class="rn">#</th>' + tb.hd0.map(function (h, c) { var s = V.sort && V.sort.c === c; return '<th data-c="' + c + '" class="' + (s ? 'srt' + (V.sort.dn ? ' dn' : '') : '') + '" title="' + esc(String(h == null ? '' : h)) + ' — kategori: ' + esc(rlab(t.map[c])) + ' (klik = urutkan)">' + esc(String(h == null || h === '' ? '(tanpa nama)' : h)) + '<small>' + esc(rlab(t.map[c])) + '</small></th>'; }).join('') + '</tr>';
    g('vght').querySelectorAll('th[data-c]').forEach(function (th) { th.onclick = function () { commit(); var c = +th.getAttribute('data-c'); V.sort = V.sort && V.sort.c === c ? (V.sort.dn ? null : { c: c, dn: true }) : { c: c, dn: false }; layout(); buildView(); draw(); }; });
  }
  function draw() {
    var t = curT(), bt = g('vgbt'), gr = g('vggrid'); if (!t) { bt.innerHTML = ''; return; } var tb = t.tb, R = V.R[V.k], Hh = V.rowH, top = gr.scrollTop, n0 = Math.max(0, Math.floor(top / Hh) - 5), n1 = Math.min(V.view.length, Math.ceil((top + gr.clientHeight) / Hh) + 5), h = V.cg;
    for (var vi = n0; vi < n1; vi++) {
      var i = V.view[vi], row = tb.rows[i], ed = V.ed.get(row), rl = R.rows.get(i); h += '<tr data-v="' + vi + '"' + (V.rs.has(i) ? ' class="rs"' : '') + '><td class="rn' + (rl ? ' ' + rl : '') + '" data-v="' + vi + '">' + (i + 2) + '</td>';
      for (var c = 0; c < tb.hd0.length; c++) { var q = R.cell.get(i * 1024 + c), cls = ((q ? q.lv : '') + (ed && ed.has(c) ? ' ed' : '') + (vi === V.sel.r && c === V.sel.c ? ' sel' : '')).trim(), v = row[c] == null ? '' : String(row[c]); h += '<td data-c="' + c + '"' + (cls ? ' class="' + cls + '"' : '') + (q ? ' title="' + esc(q.m.join('\n')) + '"' : (v.length > 12 ? ' title="' + esc(v) + '"' : '')) + '>' + esc(v) + '</td>'; }
      h += '</tr>';
    }
    bt.innerHTML = h; bt.style.top = (n0 * Hh) + 'px'; var tr = bt.querySelector('tr'); if (tr && Math.abs(tr.offsetHeight - Hh) > 0.5 && tr.offsetHeight > 10) { V.rowH = tr.offsetHeight; g('vgsp').style.height = (V.view.length * V.rowH + 2) + 'px'; }
    status();
  }
  function status() {
    var t = curT(); if (!t) { g('vgst').textContent = ''; return; } var R = V.R[V.k], E = 0, Wn = 0; R.iss.forEach(function (q) { if (q.lv === 'E') E++; else Wn++; }); var i = V.view[V.sel.r];
    g('vgst').innerHTML = NL(t.tb.rows.length) + ' baris' + (V.view.length !== t.tb.rows.length ? ' (tampil ' + NL(V.view.length) + ')' : '') + ' · <span style="color:#c62828">' + NL(E) + ' galat</span> · <span style="color:#b26a00">' + NL(Wn) + ' peringatan</span>' + (i != null ? ' · baris ' + (i + 2) + ', kolom ' + esc(String(t.tb.hd0[V.sel.c] == null ? '' : t.tb.hd0[V.sel.c])) : '') + (V.dirty ? ' · <b style="color:#1849a9">ada perubahan belum diterapkan</b>' : '');
  }
  function side() {
    var t = curT(); if (!t) { g('vgrules').innerHTML = ''; g('vgiss').innerHTML = ''; return; } var R = V.R[V.k], rl = Array.from(R.rule.entries()).sort(function (a, b) { return (a[1].lv === 'E' ? 0 : 1) - (b[1].lv === 'E' ? 0 : 1) || b[1].n - a[1].n; });
    g('vgrules').innerHTML = rl.length ? rl.map(function (e) { return '<div data-r="' + esc(e[0]) + '" class="' + (V.rule === e[0] ? 'on' : '') + '"><b class="vg' + e[1].lv + '">' + NL(e[1].n) + '</b>' + esc(e[0]) + '</div>'; }).join('') + (V.rule ? '<div data-r="" style="color:#1f6feb">&#10005; hapus saringan</div>' : '') : '<div style="color:#2e7d32">&#10003; Tidak ada masalah di tabel ini.</div>';
    g('vgrules').querySelectorAll('div[data-r]').forEach(function (d) { d.onclick = function () { V.rule = d.getAttribute('data-r') || null; V.sel.r = 0; buildView(); side(); g('vggrid').scrollTop = 0; draw(); }; });
    var L = V.rule ? R.iss.filter(function (x) { return x.rule === V.rule; }) : R.iss, MX = 1500;
    g('vgiss').innerHTML = L.slice(0, MX).map(function (q, j) { return '<div data-j="' + j + '"><b class="vg' + q.lv + '">' + (q.lv === 'E' ? 'G' : 'P') + '</b>Baris ' + (q.r + 2) + ' · ' + esc(String(t.tb.hd0[q.c] == null ? '' : t.tb.hd0[q.c])) + ': ' + esc(q.msg) + '</div>'; }).join('') + (L.length > MX ? '<div class="note" style="cursor:default">… ' + NL(L.length - MX) + ' masalah lain (saring lewat Ringkasan)</div>' : '');
    g('vgiss').querySelectorAll('div[data-j]').forEach(function (d) { d.onclick = function () { var q = L[+d.getAttribute('data-j')]; goCell(q.r, q.c); }; });
  }
  function goCell(r, c) { var vi = V.view.indexOf(r); if (vi < 0) { g('vgonly').checked = false; V.rule = null; g('vgq').value = ''; buildView(); side(); vi = V.view.indexOf(r); } if (vi < 0) return; V.sel = { r: vi, c: c }; scrollSel(); draw(); g('vggrid').focus(); }
  function scrollSel() {
    var gr = g('vggrid'), Hh = V.rowH, y = V.sel.r * Hh; if (y < gr.scrollTop) gr.scrollTop = y; else if (y + Hh > gr.scrollTop + gr.clientHeight - 2) gr.scrollTop = y + Hh - gr.clientHeight + 2;
    var x = V.rnw; for (var c = 0; c < V.sel.c; c++) x += V.widths[c]; var w = V.widths[V.sel.c] || 60; if (x - V.rnw < gr.scrollLeft) gr.scrollLeft = Math.max(0, x - V.rnw); else if (x + w > gr.scrollLeft + gr.clientWidth) gr.scrollLeft = x + w - gr.clientWidth;
  }
  function setCell(i, c, val, batch) { var row = curT().tb.rows[i]; while (row.length <= c) row.push(''); var old = row[c] == null ? '' : String(row[c]); if (old === val) return false; batch.push({ k: V.k, row: row, c: c, old: row[c] }); row[c] = val; var s = V.ed.get(row); if (!s) V.ed.set(row, s = new Set()); s.add(c); return true; }
  function markDirty() { V.dirty = true; var t = curT(); if (t && t.src) delete t.src._f; revalidate(); }
  function startEdit(init) {
    var t = curT(); if (!t || !V.view.length) return; var i = V.view[V.sel.r], td = g('vgbt').querySelector('tr[data-v="' + V.sel.r + '"] td[data-c="' + V.sel.c + '"]'); if (!td) return;
    var inp = document.createElement('input'), cv = t.tb.rows[i][V.sel.c]; inp.value = init != null ? init : (cv == null ? '' : cv); td.textContent = ''; td.appendChild(inp); inp.focus(); if (init == null) inp.select(); V.editing = { inp: inp, i: i, c: V.sel.c };
    inp.addEventListener('keydown', function (e) { e.stopPropagation(); if (e.key === 'Enter') { e.preventDefault(); commit(); mv(e.shiftKey ? -1 : 1, 0); } else if (e.key === 'Tab') { e.preventDefault(); commit(); mv(0, e.shiftKey ? -1 : 1); } else if (e.key === 'Escape') { e.preventDefault(); V.editing = null; draw(); g('vggrid').focus(); } });
    inp.addEventListener('blur', function () { setTimeout(function () { if (V.editing && V.editing.inp === inp) commit(); }, 0); });
  }
  function commit() { var E = V.editing; if (!E) return; V.editing = null; var b = []; if (setCell(E.i, E.c, E.inp.value, b)) { V.U.push({ batch: b }); markDirty(); } draw(); g('vggrid').focus({ preventScroll: true }); }
  function mv(dr, dc) { var t = curT(); if (!t) return; V.sel.r = Math.max(0, Math.min(V.view.length - 1, V.sel.r + dr)); V.sel.c = Math.max(0, Math.min(t.tb.hd0.length - 1, V.sel.c + dc)); scrollSel(); draw(); }
  function undo() {
    var u = V.U.pop(); if (!u) { toast('Tidak ada edit untuk dibatalkan.'); return; }
    if (u.batch) { for (var j = u.batch.length - 1; j >= 0; j--) { var o = u.batch[j]; o.row[o.c] = o.old; } if (u.batch[0]) V.k = u.batch[0].k; }
    else if (u.del) { var rows = V.T[u.k].tb.rows; u.del.slice().sort(function (a, b) { return a[0] - b[0]; }).forEach(function (q) { rows.splice(q[0], 0, q[1]); }); V.k = u.k; }
    else if (u.ins != null) { V.T[u.k].tb.rows.splice(u.ins, 1); V.k = u.k; }
    layout(); markDirty(); revalidate(true);
  }
  function delRows() {
    var t = curT(); if (!t) return; var rs = Array.from(V.rs); if (!rs.length && V.view.length) rs = [V.view[V.sel.r]]; if (!rs.length) return; if (rs.length > 1 && !confirm('Hapus ' + rs.length + ' baris dari tabel ' + KN[V.k] + '?')) return;
    rs.sort(function (a, b) { return b - a; }); var del = rs.map(function (i) { return [i, t.tb.rows[i]]; }); rs.forEach(function (i) { t.tb.rows.splice(i, 1); }); V.U.push({ k: V.k, del: del }); V.rs.clear(); markDirty(); revalidate(true); toast(del.length + ' baris dihapus · Ctrl+Z untuk membatalkan');
  }
  var base = function (n) { return String(n || 'tabel').replace(/\.[^.]+$/, '').replace(/[^\w.-]+/g, '_'); };
  var toCsv = function (tb) { var sp = tb.sep || ',', q = function (v) { v = v == null ? '' : String(v); return (v.indexOf(sp) >= 0 || /["\n\r]/.test(v)) ? '"' + v.replace(/"/g, '""') + '"' : v; }; return [tb.hd0.map(q).join(sp)].concat(tb.rows.map(function (r) { var o = []; for (var c = 0; c < tb.hd0.length; c++)o.push(q(r[c])); return o.join(sp); })).join('\r\n'); };
  var dl = function (txt2, fn) { if (typeof window.dgDl === 'function') return dgDl(txt2, fn, 'text/csv'); var a = document.createElement('a'); a.href = URL.createObjectURL(new Blob(['﻿' + txt2], { type: 'text/csv' })); a.download = fn; document.body.appendChild(a); a.click(); setTimeout(function () { URL.revokeObjectURL(a.href); a.remove(); }, 1500); };
  var tname = function (t, k) { return base(t.name) + (t.sheet && t.sheet !== base(t.name) && t.sheet !== t.name.replace(/\.[^.]+$/, '') ? '_' + base(t.sheet) : '') ; };
  function wire() {
    var gr = g('vggrid');
    gr.addEventListener('scroll', function () { g('vghd').scrollLeft = gr.scrollLeft; if (V.editing) commit(); else draw(); });
    gr.addEventListener('mousedown', function (e) {
      var td = e.target.closest('td'); if (!td || td.querySelector('input')) return; var tr = td.parentNode, vi = +tr.getAttribute('data-v'); if (V.editing) commit();
      if (td.classList.contains('rn')) { var i = V.view[vi]; if (e.shiftKey && V.anchor != null) { var a = Math.min(V.anchor, vi), b = Math.max(V.anchor, vi); if (!e.ctrlKey) V.rs.clear(); for (var k = a; k <= b; k++)V.rs.add(V.view[k]); } else if (e.ctrlKey) { if (V.rs.has(i)) V.rs.delete(i); else V.rs.add(i); V.anchor = vi; } else { V.rs.clear(); V.rs.add(i); V.anchor = vi; } V.sel.r = vi; draw(); return; }
      V.rs.clear(); V.sel = { r: vi, c: +td.getAttribute('data-c') }; draw();
    });
    gr.addEventListener('dblclick', function (e) { if (e.target.closest('td[data-c]')) startEdit(); });
    gr.addEventListener('keydown', function (e) {
      if (V.editing) return; var t = curT(); if (!t) return; var k = e.key; e.stopPropagation();
      if ((e.ctrlKey || e.metaKey) && (k === 'z' || k === 'Z')) { e.preventDefault(); undo(); return; }
      if (e.ctrlKey || e.metaKey || e.altKey) return;
      if (k === 'ArrowDown') { e.preventDefault(); mv(1, 0); } else if (k === 'ArrowUp') { e.preventDefault(); mv(-1, 0); } else if (k === 'ArrowRight' || (k === 'Tab' && !e.shiftKey)) { e.preventDefault(); mv(0, 1); } else if (k === 'ArrowLeft' || (k === 'Tab' && e.shiftKey)) { e.preventDefault(); mv(0, -1); }
      else if (k === 'PageDown') { e.preventDefault(); mv(Math.floor(gr.clientHeight / V.rowH) - 1, 0); } else if (k === 'PageUp') { e.preventDefault(); mv(-Math.floor(gr.clientHeight / V.rowH) + 1, 0); }
      else if (k === 'Home') { e.preventDefault(); V.sel.c = 0; mv(0, 0); } else if (k === 'End') { e.preventDefault(); V.sel.c = t.tb.hd0.length - 1; mv(0, 0); }
      else if (k === 'Enter' || k === 'F2') { e.preventDefault(); startEdit(); }
      else if (k === 'Delete') { e.preventDefault(); if (V.rs.size) { delRows(); return; } var b = []; if (setCell(V.view[V.sel.r], V.sel.c, '', b)) { V.U.push({ batch: b }); markDirty(); } draw(); }
      else if (k === 'Backspace') { e.preventDefault(); startEdit(''); }
      else if (k.length === 1) { e.preventDefault(); startEdit(k); }
    });
    gr.addEventListener('copy', function (e) { if (V.editing) return; var t = curT(); if (!t) return; var tx; if (V.rs.size) tx = Array.from(V.rs).sort(function (a, b) { return a - b; }).map(function (i) { return t.tb.rows[i].join('\t'); }).join('\n'); else { var v = t.tb.rows[V.view[V.sel.r]]; tx = v ? String(v[V.sel.c] == null ? '' : v[V.sel.c]) : ''; } e.clipboardData.setData('text/plain', tx); e.preventDefault(); });
    gr.addEventListener('paste', function (e) {
      if (V.editing) return; var t = curT(); if (!t || !V.view.length) return; var tx = (e.clipboardData.getData('text/plain') || '').replace(/\r/g, '').replace(/\n$/, ''); if (!tx) return; e.preventDefault();
      var L = tx.split('\n').map(function (l) { return l.split('\t'); }), b = []; L.forEach(function (cells, dr) { var vi = V.sel.r + dr; if (vi >= V.view.length) return; cells.forEach(function (v, dc) { var c = V.sel.c + dc; if (c < t.tb.hd0.length) setCell(V.view[vi], c, v.trim(), b); }); });
      if (b.length) { V.U.push({ batch: b }); markDirty(); toast(b.length + ' sel ditempel.'); } draw();
    });
    g('vgdel').onclick = delRows;
    g('vgadd').onclick = function () {
      var t = curT(); if (!t) return; commit(); var cur = V.view.length ? V.view[V.sel.r] : t.tb.rows.length - 1, at = cur + 1, row = t.tb.hd0.map(function () { return ''; }), iid = t.map.indexOf('id'), src = t.tb.rows[cur]; if (iid >= 0 && src) row[iid] = src[iid];
      var ifr = t.map.indexOf('fr'), ito = t.map.indexOf('to'); if (ifr >= 0 && ito >= 0 && src && src[ito] != null) row[ifr] = src[ito];
      t.tb.rows.splice(at, 0, row); V.ed.set(row, new Set(t.tb.hd0.map(function (h, c) { return c; }))); V.U.push({ k: V.k, ins: at }); V.sort = null; V.rule = null; g('vgonly').checked = false; markDirty(); revalidate(true); goCell(at, ifr >= 0 ? ito : 0);
    };
    g('vgun').onclick = undo;
    g('vgq').addEventListener('input', function () { clearTimeout(V.qT); V.qT = setTimeout(function () { V.sel.r = 0; buildView(); gr.scrollTop = 0; draw(); }, 200); });
    g('vgonly').onchange = function () { V.sel.r = 0; buildView(); gr.scrollTop = 0; draw(); };
    g('vgx').onclick = function () { commit(); if (V.dirty && V.src === 'ds' && !confirm('Ada perubahan yang belum dibangun ulang ke database proyek. Tutup dan buang perubahan?')) return; close(); };
    g('vgmap').onclick = function () { commit(); close(); var d = g('colDet'); if (d) { d.open = true; d.scrollIntoView({ block: 'start', behavior: 'smooth' }); } };
    g('vgexp').onclick = function () { commit(); var t = curT(); if (t) dl(toCsv(t.tb), tname(t, V.k) + '_valid.csv'); };
    g('vgexa').onclick = function () { commit(); var j = 0; KS.forEach(function (k) { var t = V.T[k]; if (t) setTimeout(function () { dl(toCsv(t.tb), tname(t, k) + '_valid.csv'); }, 400 * j++); }); };
    g('vgexi').onclick = function () {
      commit(); var q = function (v) { v = v == null ? '' : String(v); return /[",\n\r]/.test(v) ? '"' + v.replace(/"/g, '""') + '"' : v; }, L = [['Tabel', 'File', 'Baris', 'Hole_ID', 'Kolom', 'Nilai', 'Tingkat', 'Aturan', 'Pesan']];
      KS.forEach(function (k) { var t = V.T[k], R = V.R[k]; if (!t || !R) return; var iid = t.map.indexOf('id'); R.iss.forEach(function (x) { var r = t.tb.rows[x.r] || []; L.push([KN[k], t.name, x.r + 2, iid >= 0 ? r[iid] : '', t.tb.hd0[x.c], r[x.c], x.lv === 'E' ? 'Galat' : 'Peringatan', x.rule, x.msg]); }); });
      dl(L.map(function (r) { return r.map(q).join(','); }).join('\r\n'), 'Laporan_validasi_' + (V.src === 'ds' ? base(SA.pname || 'proyek') : 'import') + '.csv');
    };
    g('vggo').onclick = function () {
      commit();
      if (V.src === 'slot') { close(); SA.preview(); toast(V.dirty ? 'Tabel hasil edit dipakai di pratinjau import. Klik Tampilkan viewer untuk memproses dataset.' : 'Tidak ada perubahan.'); V.dirty = false; return; }
      if (!V.dirty) { toast('Tidak ada perubahan untuk dibangun ulang.'); return; }
      if (!window.PTD || !PTD.apply) { alert('Database proyek belum dimuat.'); return; }
      var B = dsRebuild(V.T), sk = B.skip, ns = sk.collar + sk.survey + sk.assay + sk.geo, o = B.out;
      if (!confirm('Bangun ulang database bor proyek "' + SA.pname + '" dari tabel yang diedit?\n\n' + (o.collars ? o.collars.length + ' collar · ' : '') + (o.surveys ? o.surveys.length + ' survey · ' : '') + (o.assays ? o.assays.length + ' assay · ' : '') + (o.geoRows ? o.geoRows.length + ' geologi' : '') +
        (ns ? '\n\nDilewati karena tidak valid (Hole_ID kosong / ganda, koordinat atau From-To bukan angka, To ≤ From): ' + ns + ' baris.' : '') + '\n\nFolder proyek mendapat backup dulu; bisa dibatalkan lewat Database Bor › Batalkan perubahan database terakhir.')) return;
      V.dirty = false; PTD.apply('Edit tabel database bor', function (D) { Object.keys(o).forEach(function (k) { D[k] = o[k]; }); });
    };
  }
  function close() { if (W) W.classList.remove('on'); if (V.src === 'slot') slotStat(); }
  function open(src, T, k) {
    mk(); V.src = src; V.T = T; var ks = KS.filter(function (x) { return T[x]; }); if (!ks.length) { toast(src === 'slot' ? 'Pilih file Collar / Survey / Assay / Geologi dulu.' : 'Database bor proyek masih kosong.'); return; }
    var R0 = vgCheck(T); V.k = k && T[k] ? k : (ks.filter(function (x) { return R0[x].iss.some(function (q) { return q.lv === 'E'; }); })[0] || ks[0]);
    V.sel = { r: 0, c: 0 }; V.rs.clear(); V.sort = null; V.rule = null; V.U = []; V.dirty = false; g('vgq').value = ''; g('vgonly').checked = false;
    g('vgsrc').textContent = src === 'slot' ? '· tabel yang dipilih untuk diimport (belum diproses)' : '· database bor proyek "' + (SA.pname || '') + '"';
    g('vggo').textContent = src === 'slot' ? 'Terapkan & tutup' : 'Bangun ulang dataset'; g('vggo').title = src === 'slot' ? 'Tutup; pratinjau import memakai tabel yang sudah diedit' : 'Simpan tabel yang diedit ke database bor proyek (backup dulu, bisa dibatalkan), lalu 3D dimuat ulang';
    g('vgmap').style.display = src === 'slot' ? '' : 'none';
    W.classList.add('on'); layout(); V.R = R0; buildView(); tabs(); side(); g('vggrid').scrollTop = 0; g('vggrid').scrollLeft = 0; draw(); g('vggrid').focus();
  }
  VG.openSlot = function (k) { open('slot', slotTables(), k); };
  VG.openDs = function (k) { if (!SA.D || !SA.pname) { alert('Buka proyek dulu.'); return; } open('ds', dsTables(), k); };
  VG.state = function () { return V; };
  /* ---- tautan "Kolom · Periksa" + jumlah masalah di tiap slot import ---- */
  var slotStat = function () {
    clearTimeout(VG._st); VG._st = setTimeout(function () {
      var T; try { T = slotTables(); } catch (e) { return; } var nr = 0; KS.forEach(function (k) { if (T[k]) nr += T[k].tb.rows.length; }); var R = nr <= 300000 ? vgCheck(T) : {};/* tabel sangat besar: hitungan dibuat saat jendela dibuka */
      KS.forEach(function (k) {
        var el = g('sf' + k); if (!el || !el.parentNode.classList.contains('on')) return; var s = el.querySelector('.vgsl'); if (!s) { s = document.createElement('div'); s.className = 'vgsl'; el.appendChild(s); }
        var E2 = 0, W2 = 0; if (R[k]) R[k].iss.forEach(function (q) { if (q.lv === 'E') E2++; else W2++; });
        s.innerHTML = '<a href="#" onclick="VG.kolom();return false" title="Atur kategori tiap kolom">Kolom</a> · <a href="#" onclick="VG.openSlot(\'' + k + '\');return false" title="Buka tabel; sel bermasalah disorot">Periksa</a>' + (R[k] ? ' · ' + (E2 || W2 ? (E2 ? '<span style="color:#c62828">' + NL(E2) + ' galat</span>' : '') + (E2 && W2 ? ' · ' : '') + (W2 ? '<span style="color:#b26a00">' + NL(W2) + ' peringatan</span>' : '') : '<span style="color:#2e7d32">&#10003; lolos</span>') : '');
      });
    }, 250);
  };
  VG.kolom = function () { var d = g('colDet'); if (d) { d.open = true; d.scrollIntoView({ block: 'start', behavior: 'smooth' }); } };
  var _pv = SA.preview; SA.preview = function () { var r = _pv.apply(this, arguments); slotStat(); return r; };
})();
