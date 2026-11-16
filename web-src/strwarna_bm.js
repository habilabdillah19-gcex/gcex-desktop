/* ================= GC-Ex Block Model 0.24.94: SATU NOMOR STRING = SATU WARNA (STR & DXF) =================
   Pemilik 16 Nov 2026: "Termasuk dengan polygon asmined ya, warna harus tercermin dalam String Number. Setiap pewarnaan
   string di GC, manifestasi nya baik dxf maupun str harus bisa sesuai dengan warna dan string number yang diterapkan."
   Surpac mewarnai string menurut NOMORNYA. Karena itu di GC-Ex warna string diperlakukan sebagai milik nomor:
   - Daftar nomor -> warna (per lingkup):
       dig block / string digitasi : tabel kelas kadar + material (dbKelas), nomor flag (afRules sn/col), dbU().snc
       As-Mined                    : kelas As-Mined (cls n/c, ws), amR().snc
   - Mengedit: ganti WARNA string (popup dig block / Warna poligon As-Mined) = ganti warna NOMOR itu (semua string bernomor
     sama ikut, baris kelas yang memakai nomor itu ikut); ganti NOMOR = warnanya ikut warna nomor tersebut (bila terdaftar).
   - Ekspor STR / DXF (dig block, string digitasi, As-Mined): diperiksa dulu; bila satu nomor dipakai > 1 warna, ditawarkan
     memberi nomor baru untuk warna yang berbeda (nomor terdaftar untuk warna itu, atau nomor kosong berikutnya) supaya
     tampilan Surpac = tampilan GC-Ex. DXF: layer = nomor string, warna 62 = warna ACI terdekat (palet AutoCAD 1-255).
   - Proyek lama: warna & nomor yang tersimpan dibaca apa adanya; perubahan hanya terjadi saat diedit atau saat Anda setuju
     memberi nomor baru ketika ekspor. */
(function () {
  if (window.SWN) return;
  var SWN = window.SWN = {};
  var nc = function (c) { return String(c || '').trim().toLowerCase(); };
  var add = function (M, n, c) { n = parseInt(n); if (n > 0 && c && !(n in M)) M[n] = nc(c); };
  SWN.dig = function () {
    var M = {}; try { (window.dbKelas ? dbKelas() : []).forEach(function (q) { add(M, q.n, q.c); }); } catch (e) { }
    try { (window.afRules ? afRules() : []).forEach(function (q) { add(M, q.sn, q.col); }); } catch (e) { }
    try { var X = dbU().snc || {}; Object.keys(X).forEach(function (n) { add(M, n, X[n]); }); } catch (e) { } return M;
  };
  SWN.am = function () {
    var M = {}; try { var R = amR(); (R.cls || []).forEach(function (q) { add(M, q.n, q.c); }); if (R.ws) add(M, R.ws.n, R.ws.c); var X = R.snc || {}; Object.keys(X).forEach(function (n) { add(M, n, X[n]); }); } catch (e) { } return M;
  };
  /* ganti warna sebuah nomor di daftar lingkup itu */
  SWN.setDig = function (n, c) {
    n = parseInt(n); if (!(n > 0)) return; var U = dbU(), hit = false;
    (U.rules || []).forEach(function (q) { if (parseInt(q.n) === n) { q.c = c; hit = true; } });
    Object.keys(U.sn || {}).forEach(function (k) { if (parseInt(U.sn[k].n) === n) { U.sn[k].c = c; hit = true; } });
    try { (window.afRules ? afRules() : []).forEach(function (q) { if (parseInt(q.sn) === n) { q.col = c; hit = true; } }); } catch (e) { }
    if (!hit) { U.snc = U.snc || {}; U.snc[n] = c; } else if (U.snc && U.snc[n]) U.snc[n] = c;
  };
  SWN.setAm = function (n, c) {
    n = parseInt(n); if (!(n > 0)) return; var R = amR(), hit = false;
    (R.cls || []).forEach(function (q) { if (parseInt(q.n) === n) { q.c = c; hit = true; } }); if (R.ws && parseInt(R.ws.n) === n) { R.ws.c = c; hit = true; }
    if (!hit) { R.snc = R.snc || {}; R.snc[n] = c; } else if (R.snc && R.snc[n]) R.snc[n] = c;
  };
  /* ---- palet ACI AutoCAD (1-255) untuk warna DXF ---- */
  var ACI = (function () {
    var P = { 1: [255, 0, 0], 2: [255, 255, 0], 3: [0, 255, 0], 4: [0, 255, 255], 5: [0, 0, 255], 6: [255, 0, 255], 7: [255, 255, 255], 8: [128, 128, 128], 9: [192, 192, 192] };
    var hsv = function (h, s, v) { var c = v * s, x = c * (1 - Math.abs((h / 60) % 2 - 1)), m = v - c, r = 0, g = 0, b = 0; if (h < 60) { r = c; g = x; } else if (h < 120) { r = x; g = c; } else if (h < 180) { g = c; b = x; } else if (h < 240) { g = x; b = c; } else if (h < 300) { r = x; b = c; } else { r = c; b = x; } return [Math.round((r + m) * 255), Math.round((g + m) * 255), Math.round((b + m) * 255)]; };
    var V = [1, 1, 0.8, 0.8, 0.6, 0.6, 0.5, 0.5, 0.3, 0.3], S = [1, 0.5, 1, 0.5, 1, 0.5, 1, 0.5, 1, 0.5];
    for (var i = 10; i < 250; i++) { var hh = Math.floor((i - 10) / 10) * 15, k = i % 10; P[i] = hsv(hh, S[k], V[k]); }
    [51, 91, 132, 173, 214, 255].forEach(function (g, j) { P[250 + j] = [g, g, g]; });
    return P;
  })();
  SWN.aci = function (c) {
    var n = parseInt(String(c || '#ffffff').replace('#', '').slice(0, 6), 16); if (!isFinite(n)) return 7; var R = n >> 16 & 255, G = n >> 8 & 255, B = n & 255, best = 7, bd = 1e9;
    for (var i = 1; i < 256; i++) { if (i === 7) continue; var p = ACI[i]; var d = (p[0] - R) * (p[0] - R) * 0.3 + (p[1] - G) * (p[1] - G) * 0.59 + (p[2] - B) * (p[2] - B) * 0.11; if (d < bd) { bd = d; best = i; } }
    if (R > 235 && G > 235 && B > 235) best = 7; return best;
  };
  window.dbAci = SWN.aci;
  /* ---- pemeriksaan sebelum ekspor ---- */
  /* L = [{no, col, keep(bool), set(no)}]; reg = daftar nomor -> warna; regSet(no,col) mendaftarkan nomor baru */
  SWN.cek = function (L) { var by = {}; L.forEach(function (o) { var n = parseInt(o.no); if (!(n > 0)) return; (by[n] = by[n] || {})[nc(o.col)] = (by[n][nc(o.col)] || 0) + 1; }); var K = {}; Object.keys(by).forEach(function (n) { if (Object.keys(by[n]).length > 1) K[n] = by[n]; }); return K; };
  SWN.perbaiki = function (L, reg, regSet) {
    var K = SWN.cek(L), used = {}, rev = {}, ubah = 0; L.forEach(function (o) { used[parseInt(o.no)] = 1; }); Object.keys(reg).forEach(function (n) { used[n] = 1; if (!(reg[n] in rev)) rev[reg[n]] = +n; });
    var next = function () { var n = 1; Object.keys(used).forEach(function (k) { if (+k >= n) n = +k + 1; }); used[n] = 1; return n; }, baru = {};
    Object.keys(K).forEach(function (n) {
      var cs = Object.keys(K[n]), keep = reg[n] && cs.indexOf(reg[n]) >= 0 ? reg[n] : cs.sort(function (a, b) { return K[n][b] - K[n][a]; })[0];
      cs.forEach(function (c) { if (c === keep) return; var t = rev[c] && !K[rev[c]] ? rev[c] : (baru[c] || (baru[c] = next())); if (!(t in reg)) { regSet(t, c); reg[t] = c; } L.forEach(function (o) { if (parseInt(o.no) === +n && nc(o.col) === c && !o.keep) { o.set(t); ubah++; } }); });
    });
    return ubah;
  };
  SWN.tanya = function (L, reg, regSet, judul) {
    var K = SWN.cek(L); if (!Object.keys(K).length) return true;
    var t = Object.keys(K).map(function (n) { return 'String ' + n + ': ' + Object.keys(K[n]).map(function (c) { return c + ' (' + K[n][c] + ')'; }).join(', '); }).join('\n');
    if (!confirm(judul + ': satu nomor string dipakai lebih dari satu warna. Surpac mewarnai string menurut nomornya, jadi warnanya akan sama di sana.\n\n' + t +
      '\n\nOK = beri nomor baru untuk warna yang berbeda (nomor yang sudah terdaftar untuk warna itu, atau nomor kosong berikutnya), lalu ekspor.\nBatal = ekspor apa adanya.')) return true;
    var n = SWN.perbaiki(L, reg, regSet); SWN.msg = n + ' string diberi nomor baru agar warna = nomor string.'; return true;
  };
  /* ---- daftar string per ekspor ---- */
  var digL = function (S) { return S.map(function (s) { return { no: s.no, col: s.col, keep: !!s.fsn, set: function (n) { s.no = n; DG.S.forEach(function (q) { if (q.inner && q.parent === s.id && !q.fsn && !q.fcol) q.no = n; }); } }; }); };
  var amL = function () { return amAllInfo().filter(function (I) { return I.x.print !== false && I.x.on; }).map(function (I) { return { no: I.sid, col: I.col, keep: false, set: function (n) { I.x.sid = n; delete I.x.col; } }; }); };
  /* ---- pembungkus ---- */
  if (window.dbStrSet) {
    var _ss = dbStrSet; window.dbStrSet = dbStrSet = function (i, f, v) {
      var s = DG.S[i];
      if (s && f === 'col' && !s.inner && s.no > 0) { SWN.setDig(s.no, v); DG.S.forEach(function (q, k) { if (k !== i && !q.inner && q.no === s.no) q.col = v; if (q.inner && !q.fcol && !q.fsn && q.no === s.no) q.col = v; }); }
      var r = _ss.apply(this, arguments);
      if (s && f === 'no' && !s.inner) { var c = SWN.dig()[parseInt(s.no)]; if (c && nc(s.col) !== c) _ss(i, 'col', c); else if (!c) SWN.setDig(s.no, s.col); }
      return r;
    };
  }
  if (window.amPSet) {
    var _ap = amPSet; window.amPSet = amPSet = function (id, f, v) {
      var x = amBndAll().filter(function (q) { return q.id === id; })[0];
      if (x && f === 'col') { var I = amInfo(x); SWN.setAm(I.sid, v); amBndAll().forEach(function (q) { if (q.col && amInfo(q).sid === I.sid) delete q.col; }); amPanel(); updatePlot(); amDirty(); return; }
      if (x && f === 'sid') delete x.col;
      return _ap.apply(this, arguments);
    };
  }
  if (window.amInfo) {
    var _ai = amInfo; window.amInfo = amInfo = function (x) { var r = _ai.apply(this, arguments); if (r && !x.col) { var c = SWN.am()[parseInt(r.sid)]; if (c) r.col = c; } return r; };
  }
  if (window.dbExport) {
    var _de = dbExport; window.dbExport = dbExport = function (fmt) {
      var S = dbStrings(); if (S.length) { var reg = SWN.dig(); SWN.tanya(digL(S), reg, SWN.setDig, 'Ekspor dig block'); try { dgSave(); } catch (e) { } }
      return _de.apply(this, arguments);
    };
  }
  if (window.dgExport) {
    var _ge = dgExport; window.dgExport = dgExport = function (fmt) {
      var S = DG.S.filter(function (s) { return s.vis; }); if (S.length) { SWN.tanya(digL(S), SWN.dig(), SWN.setDig, 'Ekspor string'); try { dgSave(); } catch (e) { } }
      if (fmt === 'str' || !S.length) return _ge.apply(this, arguments);
      /* DXF: layer = nomor string, warna 62 = ACI terdekat (dulu tanpa warna, layer = material_nomor) */
      var base = 'String_' + String(ZONE).replace(/[^A-Za-z0-9_-]+/g, '_'), f3 = function (v) { return (+v).toFixed(3); }, r = ['0', 'SECTION', '2', 'HEADER', '9', '$ACADVER', '1', 'AC1009', '0', 'ENDSEC', '0', 'SECTION', '2', 'ENTITIES'];
      S.forEach(function (s) { var ly = String(s.no); r.push('0', 'POLYLINE', '8', ly, '62', String(SWN.aci(s.col)), '66', '1', '70', s.closed ? '9' : '8', '10', '0.0', '20', '0.0', '30', '0.0'); s.pts.forEach(function (q) { r.push('0', 'VERTEX', '8', ly, '10', f3(q[0] + offX), '20', f3(q[1] + offY), '30', f3(q[2]), '70', '32'); }); r.push('0', 'SEQEND', '8', ly); });
      r.push('0', 'ENDSEC', '0', 'EOF'); return dgDl(dxfLengkap(r).join('\r\n') + '\r\n', base + '.dxf', 'application/dxf');
    };
  }
  if (window.amStr) {
    var _as = amStr; window.amStr = amStr = function () { SWN.tanya(amL(), SWN.am(), SWN.setAm, 'Ekspor As-Mined'); try { amDirty(); } catch (e) { } return _as.apply(this, arguments); };
  }
  /* As-Mined DXF: layer = String ID, warna 62 = ACI warna poligon */
  window.amDxf = function () {
    SWN.tanya(amL(), SWN.am(), SWN.setAm, 'Ekspor As-Mined'); try { amDirty(); } catch (e) { }
    var R = amR(), U = amU(), L = amAllInfo().filter(function (I) { return I.x.print !== false && I.x.on; }); if (!L.length) return;
    var r = ['0', 'SECTION', '2', 'HEADER', '9', '$ACADVER', '1', 'AC1009', '0', 'ENDSEC', '0', 'SECTION', '2', 'ENTITIES'];
    L.sort(function (a, b) { return a.sid - b.sid; }).forEach(function (I) { var ly = String(I.sid), z = (+I.x.bot).toFixed(3); r.push('0', 'POLYLINE', '8', ly, '62', String(SWN.aci(I.col)), '66', '1', '70', '9', '10', '0.0', '20', '0.0', '30', z); I.x.pts.forEach(function (p) { r.push('0', 'VERTEX', '8', ly, '10', (+p[0]).toFixed(3), '20', (+p[1]).toFixed(3), '30', z, '70', '32'); }); r.push('0', 'SEQEND', '8', ly); });
    r.push('0', 'ENDSEC', '0', 'EOF'); var fn = 'AsMined_' + String(R.pit || lyZone()).replace(/[^A-Za-z0-9_-]+/g, '_') + '_' + (U.period ? String(U.period).replace(/[^A-Za-z0-9_-]+/g, '_') : amToday()) + '.dxf';
    dgDl(dxfLengkap(r).join('\r\n') + '\r\n', fn, 'application/dxf'); var e = document.getElementById('amRegMsg'); if (e) e.textContent = L.length + ' poligon → ' + fn + ' (layer = String ID, warna = warna String ID)';
  };
})();
