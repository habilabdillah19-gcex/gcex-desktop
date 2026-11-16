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
      cs.forEach(function (c) { if (c === keep) return; var t = rev[c] && !K[rev[c]] ? rev[c] : (baru[c] || (baru[c] = (SWN.dekat && SWN.dekat(c, +n, used)) || next())); if (!(t in reg)) { regSet(t, c); reg[t] = c; } L.forEach(function (o) { if (parseInt(o.no) === +n && nc(o.col) === c && !o.keep) { o.set(t); ubah++; } }); });
    });
    return ubah;
  };
  SWN.tanya = function (L, reg, regSet, judul) {
    var K = SWN.cek(L); if (!Object.keys(K).length) return true;
    var t = Object.keys(K).map(function (n) { return 'String ' + n + ': ' + Object.keys(K[n]).map(function (c) { return c + ' (' + K[n][c] + ')'; }).join(', '); }).join('\n');
    if (!confirm(judul + ': satu nomor string dipakai lebih dari satu warna. Surpac mewarnai string menurut nomornya, jadi warnanya akan sama di sana.\n\n' + t +
      '\n\nOK = beri nomor baru untuk warna yang berbeda (nomor yang sudah terdaftar untuk warna itu; bila belum ada, nomor yang warnanya paling mirip di gaya Surpac situs, mis. oranye -> 16), lalu ekspor.\nBatal = ekspor apa adanya.')) return true;
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
/* ================= BM 0.24.96: GAYA SURPAC (.ssi) =================
   Pemilik 16 Nov 2026 mengirim berkas .ssi situs. Dua format teks:
   1. Gaya string (styles): "STRINGS:" lalu baris "<kunci>=ssi_label=...,HGS_color=lines=text=edges=markers=<warna>,...";
      kunci = "default", satu nomor ("17"), atau rentang "awal, akhir, langkah" ("14, 99, 10" = 14, 24, ..., 94).
      Surpac menyimpan .ssi BERNAMA SAMA di samping .str -> GC-Ex menulis <nama>.ssi saat ekspor STR, sehingga Surpac
      menampilkan warna yang sama dengan GC-Ex (nomor yang dipakai ditulis satu per satu di awal bagian STRINGS).
   2. Skema warna rentang (mis. grade_ore.ssi): "pink~default face colour", "0;0.4;1;3;999~range", "grey~0.00 -> 0.40", ...
      -> diimpor sebagai kelas warna block model (Warna & kelas kadar).
   Warna: "r=0.349 g=1.0 b=0.349" (0..1) atau nama warna Surpac (tabel di bawah; nama tak dikenal dilewati). */
(function () {
  if (!window.SWN || SWN.ssi) return;
  var NM = { 'white': '#ffffff', 'black': '#000000', 'red': '#ff0000', 'green': '#00ff00', 'blue': '#0000ff', 'yellow': '#ffff00', 'cyan': '#00ffff', 'magenta': '#ff00ff', 'fuchsia': '#ff00ff',
    'grey': '#808080', 'gray': '#808080', 'light grey': '#d3d3d3', 'light gray': '#d3d3d3', 'dark grey': '#555555', 'dark gray': '#555555', 'silver': '#c0c0c0', 'light silver': '#d8d8d8',
    'orange': '#ffa500', 'red orange': '#ff5349', 'orange yellow': '#f8d568', 'yellow orange': '#ffae42', 'gold': '#ffd700', 'peach': '#ffcba4', 'apricot': '#fbceb1', 'brown': '#a52a2a',
    'burnt sienna': '#e97451', 'raw sienna': '#d68a59', 'forest green': '#228b22', 'light green': '#90ee90', 'dark green': '#006400', 'aquamarine': '#7fffd4', 'blue green': '#0d98ba',
    'pink': '#ffc0cb', 'purple': '#800080', 'violet': '#ee82ee', 'navy': '#000080', 'navy blue': '#000080', 'maroon': '#800000', 'olive': '#808000', 'teal': '#008080', 'lime': '#00ff00',
    'tan': '#d2b48c', 'khaki': '#f0e68c', 'salmon': '#fa8072', 'coral': '#ff7f50', 'turquoise': '#40e0d0', 'sky blue': '#87ceeb', 'light blue': '#add8e6', 'dark blue': '#00008b',
    'indigo': '#4b0082', 'lavender': '#e6e6fa', 'chocolate': '#d2691e', 'crimson': '#dc143c', 'sea green': '#2e8b57', 'spring green': '#00ff7f', 'yellow green': '#9acd32', 'orchid': '#da70d6' };
  var h2 = function (v) { return ('0' + Math.max(0, Math.min(255, Math.round(v * 255))).toString(16)).slice(-2); };
  var warna = function (s) {
    s = String(s || '').trim().toLowerCase(); var m = s.match(/^r\s*=\s*([\d.]+)\s+g\s*=\s*([\d.]+)\s+b\s*=\s*([\d.]+)/);
    if (m) return '#' + h2(+m[1]) + h2(+m[2]) + h2(+m[3]); return NM[s] || null;
  };
  var keSsi = function (hex) { var n = parseInt(String(hex).replace('#', '').slice(0, 6), 16); if (!isFinite(n)) return 'yellow'; var f = function (v) { return +(v / 255).toFixed(3); }; return 'r=' + f(n >> 16 & 255) + ' g=' + f(n >> 8 & 255) + ' b=' + f(n & 255); };
  /* gaya string */
  var parse = function (t) {
    t = String(t || ''); var L = t.split(/\r?\n/);
    if (/~range\s*$/m.test(t)) { /* skema rentang */
      var R = { kind: 'range', cuts: [], cols: [] }; L.forEach(function (l) { var p = l.split('~'); if (p.length < 2) return; var a = p[0].trim(), b = p.slice(1).join('~').trim();
        if (/^range$/i.test(b)) R.cuts = a.split(';').map(Number).filter(isFinite); else if (/->/.test(b)) R.cols.push(warna(a) || '#999999'); });
      return R.cuts.length >= 2 ? R : null;
    }
    var S = { kind: 'styles', def: null, ex: {}, rg: [], lines: L }, sec = '';
    L.forEach(function (l) {
      if (/^[A-Z]+:\s*$/.test(l)) { sec = l.trim(); return; } if (sec !== 'STRINGS:') return; var i = l.indexOf('='); if (i < 0) return; var k = l.slice(0, i).trim(), rest = l.slice(i + 1);
      var m = rest.match(/HGS_color=lines=text=edges=markers=([^,]+)/), c = m ? warna(m[1]) : null; if (!c) return;
      if (k === 'default') S.def = c; else if (/^\d+$/.test(k)) S.ex[+k] = c; else { var q = k.split(',').map(function (x) { return parseInt(x); }); if (q.length === 3 && q.every(isFinite) && q[2] > 0) S.rg.push({ a: q[0], b: q[1], s: q[2], c: c }); }
    });
    return Object.keys(S.ex).length || S.rg.length || S.def ? S : null;
  };
  var colorOf = function (S, n) { n = parseInt(n); if (!S || !(n > 0)) return null; if (S.ex[n]) return S.ex[n]; for (var i = 0; i < S.rg.length; i++) { var r = S.rg[i]; if (n >= r.a && n <= r.b && (n - r.a) % r.s === 0) return r.c; } return S.def; };
  var TAIL = ',HGS_line_pattern=|--->,HGS_color=faces=(diffuse=%C,specular=white,gloss=5,transmission=black),HGS_edge_pattern=---,HGS_face_pattern=solid,HGS_line_weight=1,HGS_edge_weight=1,HGS_marker_symbol=+,HGS_marker_size=0.5,HGS_text_font=name=Default|size=0.02 sru|slant=0,HGS_text_path=1 0 0';
  /* ---- gaya string BAWAAN Surpac situs (legend Surpac pemilik, 17 Nov 2026): 1-9 lalu berulang tiap 10 sampai 99
     (14, 24, ... hijau; 16, 26, ... oranye; 17, 27, ... merah; 18, 28, ... ungu). Dipakai bila belum ada .ssi situs yang diimpor:
     memilih nomor baru yang warnanya cocok, dan mengisi .ssi yang ikut diekspor (nomor lain tetap tampil seperti biasa di Surpac). */
  var BW = ['white', 'blue', 'r=0.0 g=0.6 b=0.8', 'r=0.478 g=0.819 b=0.478', 'r=0.349 g=1.0 b=0.349', 'yellow', 'r=1.0 g=0.6 b=0.2', 'red', 'r=1.0 g=0.4 b=1.0'];
  var BW_LAB = ['white line', 'blue line', 'blue green line', 'light green line', 'green line', 'yellow line', 'orange line', 'red line', 'pink line'];
  SWN.BAWAAN = ['STRINGS:', 'default=ssi_label=yellow line,HGS_color=lines=text=edges=markers=yellow' + TAIL.replace('%C', 'yellow')].concat(
    BW.map(function (c, i) { return (i + 1) + '=ssi_label=' + BW_LAB[i] + ',HGS_color=lines=text=edges=markers=' + c + TAIL.replace('%C', c); }),
    ['white'].concat(BW.slice(1, 8)).concat([BW[8]]).map(function (c, i) { return (10 + i) + ', 99, 10=ssi_label=,HGS_color=lines=text=edges=markers=' + c + TAIL.replace('%C', c); })).join('\r\n');
  var bawaanS = null, gaya = function () { var t = dbU().ssiTxt; var S = t ? parse(t) : null; if (S && S.kind === 'styles') return S; return bawaanS || (bawaanS = parse(SWN.BAWAAN)); };
  var jarak = function (a, b) { var p = function (h) { var n = parseInt(String(h).replace('#', '').slice(0, 6), 16); return [n >> 16 & 255, n >> 8 & 255, n & 255]; }, x = p(a), y = p(b); return Math.sqrt((x[0] - y[0]) * (x[0] - y[0]) * 0.3 + (x[1] - y[1]) * (x[1] - y[1]) * 0.59 + (x[2] - y[2]) * (x[2] - y[2]) * 0.11); };
  /* nomor kosong (1-99) yang warnanya di Surpac paling mirip warna c; seri sama -> yang paling dekat dengan nomor asal */
  SWN.dekat = function (c, asal, used) {
    var S = gaya(), best = 0, bd = 60; for (var n = 1; n <= 99; n++) { if (used[n]) continue; var w = colorOf(S, n); if (!w) continue; var d = jarak(c, w) + Math.abs(n - asal) * 0.01; if (d < bd) { bd = d; best = n; } }
    if (best) used[best] = 1; return best;
  };
  SWN.gaya = gaya;
  /* tulis .ssi: nomor yang dipakai ditulis satu per satu paling atas di STRINGS (sesudah default); sisa gaya situs (bila diimpor) dipertahankan */
  var TRI = 'default=ssi_label=,HGS_color=lines=text=edges=markers=blue,HGS_line_pattern=|-->,HGS_color=faces=(diffuse=light green,specular=white,gloss=5),HGS_edge_pattern=---,HGS_face_pattern=solid,HGS_line_weight=1,HGS_edge_weight=1,HGS_marker_symbol=+,HGS_marker_size=0.5';
  var baris = function (k, hex, lab) { var c = keSsi(hex); return k + '=ssi_label=' + (lab || '').replace(/[,=]/g, ' ') + ',HGS_color=lines=text=edges=markers=' + c + TAIL.replace('%C', c); };
  var tulis = function (M, lab) {
    var site = gaya(), ns = Object.keys(M).map(Number).sort(function (a, b) { return a - b; }), mine = ns.map(function (n) { return baris(n, M[n], lab && lab[n]); });
    if (site && site.kind === 'styles') {
      var out = [], sec = '', done = false; site.lines.forEach(function (l) {
        if (/^[A-Z]+:\s*$/.test(l)) { sec = l.trim(); out.push(l); return; }
        var k = l.slice(0, Math.max(0, l.indexOf('='))).trim();
        if (sec === 'STRINGS:' && /^\d+$/.test(k) && M[+k]) return; /* nomor kita menggantikan baris situs yang sama */
        out.push(l); if (sec === 'STRINGS:' && k === 'default' && !done) { out.push.apply(out, mine); done = true; }
      });
      if (!done) { var j = out.indexOf('STRINGS:'); if (j >= 0) out.splice.apply(out, [j + 1, 0].concat(mine)); }
      if (out.indexOf('TRIOBJECTS:') < 0) out.push('TRIOBJECTS:', TRI);
      return out.join('\r\n').replace(/(\r\n)+$/, '') + '\r\n';
    }
    return ['STRINGS:', baris('default', '#ffff00', 'yellow line')].concat(mine, ['TRIOBJECTS:', TRI]).join('\r\n') + '\r\n';
  };
  SWN.ssi = { parse: parse, colorOf: colorOf, write: tulis, warna: warna };
  /* ---- daftar nomor -> warna ikut gaya situs (nomor yang tak ada di tabel GC-Ex) ---- */
  var _dig = SWN.dig, _am = SWN.am, siteS = function () { try { var t = dbU().ssiTxt; if (!t) return null; if (!siteS.c || siteS.t !== t) { siteS.t = t; siteS.c = parse(t); } return siteS.c && siteS.c.kind === 'styles' ? siteS.c : null; } catch (e) { return null; } };
  var plus = function (M) { var S = siteS(); if (!S) return M; Object.keys(S.ex).forEach(function (n) { if (!(n in M)) M[n] = S.ex[n]; }); return M; };
  SWN.dig = function () { return plus(_dig()); }; SWN.am = function () { return plus(_am()); };
  SWN.situs = function (n) { return colorOf(siteS(), n); };
  /* ---- impor gaya situs: warna kelas GC-Ex (dig block, flag, As-Mined) ikut warna nomor di .ssi ---- */
  var pilih = function (cb) { var i = document.createElement('input'); i.type = 'file'; i.accept = '.ssi,.txt'; i.onchange = function () { var f = i.files && i.files[0]; if (!f) return; var r = new FileReader(); r.onload = function () { cb(String(r.result || ''), f.name); }; r.readAsText(f); }; i.click(); };
  SWN.imporSitus = function (txt, nama) {
    var S = parse(txt); if (!S || S.kind !== 'styles') { alert('Berkas ini bukan gaya string Surpac (bagian STRINGS: tidak ditemukan).' + (S && S.kind === 'range' ? '\nIni skema warna rentang kadar: impor lewat Block Model › Warna & kelas kadar › Import .ssi.' : '')); return 0; }
    var U = dbU(), n = 0, set = function (o, kn, kc) { var c = colorOf(S, o[kn]); if (c && String(o[kc]).toLowerCase() !== c) { o[kc] = c; n++; } };
    U.ssiTxt = txt; U.ssiNama = nama || 'styles.ssi';
    (U.rules || []).forEach(function (q) { set(q, 'n', 'c'); }); Object.keys(U.sn || {}).forEach(function (k) { set(U.sn[k], 'n', 'c'); });
    try { (window.afRules ? afRules() : []).forEach(function (q) { if (parseInt(q.sn) > 0) set(q, 'sn', 'col'); }); } catch (e) { }
    try { var R = amR(); (R.cls || []).forEach(function (q) { set(q, 'n', 'c'); }); if (R.ws) set(R.ws, 'n', 'c'); } catch (e) { }
    (window.DG ? DG.S : []).forEach(function (s) { if (s.no > 0) { var c = colorOf(S, s.no); if (c && !(s.inner && s.fcol && !s.fsn) && String(s.col).toLowerCase() !== c) { s.col = c; n++; } } });
    try { amBndAll().forEach(function (x) { delete x.col; }); } catch (e) { }
    try { dgSave(); } catch (e) { } try { if (window.SA && SA.dirty) SA.dirty(); } catch (e) { } try { amDirty(); } catch (e) { }
    try { BX.mc = null; dbPanel(); dgList(); updatePlot(); } catch (e) { }
    return n;
  };
  SWN.imporSitusUI = function () { pilih(function (t, nm) { var n = SWN.imporSitus(t, nm); if (n || dbU().ssiTxt) alert('Gaya Surpac "' + nm + '" dipakai: ' + n + ' warna kelas / string disamakan dengan warna nomornya di Surpac. Ekspor STR berikutnya juga menyertakan .ssi berisi gaya situs ini.'); }); };
  SWN.lupaSitus = function () { var U = dbU(); delete U.ssiTxt; delete U.ssiNama; try { dbPanel(); } catch (e) { } };
  /* ---- skema rentang -> kelas warna block model ---- */
  SWN.imporRentang = function (txt) {
    var R = parse(txt); if (!R || R.kind !== 'range') { alert('Berkas ini bukan skema warna rentang (baris "...~range" tidak ditemukan).'); return false; }
    var a = BX.ui.attr, c = R.cuts, L = []; for (var i = 0; i + 1 < c.length; i++) L.push({ lo: i === 0 && c[0] <= 0 ? null : c[i], hi: i === c.length - 2 && c[i + 1] >= 999 ? null : c[i + 1], col: R.cols[i] || '#999999' });
    BX.ui.cls = BX.ui.cls || {}; BX.ui.cls[a] = L; BX.sc = {}; try { LY.fst = null; } catch (e) { } try { bxPanel(); updatePlot(); if (window.SA && SA.dirty) SA.dirty(); } catch (e) { } return L.length;
  };
  SWN.imporRentangUI = function () { pilih(function (t, nm) { var n = SWN.imporRentang(t); if (n) alert(n + ' kelas warna dari "' + nm + '" dipakai untuk atribut ' + BX.ui.attr + '.'); }); };
  /* ---- ekspor: tulis <nama>.ssi di samping <nama>.str ---- */
  var denganSsi = function (fn, L) {
    var U = dbU(); if (U.ssiOut === false) return fn();
    /* header STR menunjuk .ssi pasangannya (bukan styles.ssi umum) agar Surpac memakai warna yang sama */
    var nm = null, o = window.dgDl, r; window.dgDl = function (t, f) { if (/\.str$/i.test(f)) { nm = f; var sn = String(f).split(/[\\\/]/).pop().replace(/\.str$/i, '.ssi'); if (typeof t === 'string') { var e = t.search(/\r?\n/), h = e < 0 ? t : t.slice(0, e); h = /ssi_styles:/i.test(h) ? h.replace(/ssi_styles:[^,]*/i, 'SSI_STYLES:' + sn) : (h.split(',').length === 4 && !h.split(',')[3].trim() ? h.replace(/,\s*$/, ',SSI_STYLES:' + sn) : h); arguments[0] = h + (e < 0 ? '' : t.slice(e)); } } return o.apply(this, arguments); };
    try { r = fn(); } finally { window.dgDl = o; }
    if (nm) { var M = {}; L().forEach(function (q) { var n = parseInt(q.no); if (n > 0 && q.col && !(n in M)) M[n] = String(q.col).toLowerCase(); }); if (Object.keys(M).length) setTimeout(function () { dgDl(tulis(M), nm.replace(/\.str$/i, '.ssi'), 'text/plain'); }, 300); }
    return r;
  };
  var digS = function (S) { return function () { return S().map(function (s) { return { no: s.no, col: s.col }; }); }; };
  if (window.dbExport) { var _de = dbExport; window.dbExport = dbExport = function (fmt) { var a = arguments, t = this; if (fmt === 'dxf') return _de.apply(t, a); return denganSsi(function () { return _de.apply(t, a); }, digS(dbStrings)); }; }
  if (window.dgExport) { var _ge = dgExport; window.dgExport = dgExport = function (fmt) { var a = arguments, t = this; if (fmt !== 'str') return _ge.apply(t, a); return denganSsi(function () { return _ge.apply(t, a); }, digS(function () { return DG.S.filter(function (s) { return s.vis; }); })); }; }
  if (window.amStr) { var _as = amStr; window.amStr = amStr = function () { var a = arguments, t = this; return denganSsi(function () { return _as.apply(t, a); }, function () { return amAllInfo().filter(function (I) { return I.x.print !== false && I.x.on; }).map(function (I) { return { no: I.sid, col: I.col }; }); }); }; }
  /* ---- UI: kotak "Warna Surpac (.ssi)" di Dig Block › Otomatis (satu pintu untuk dig block, flag & As-Mined) ---- */
  if (window.dbPanel) {
    var _dp = dbPanel; window.dbPanel = dbPanel = function () {
      var r = _dp.apply(this, arguments), el = document.getElementById('dbBody'); if (!el) return r; var t = el.querySelector('.dbrt'); if (!t || el.querySelector('#swSsi')) return r;
      var U = dbU(), d = document.createElement('div'); d.id = 'swSsi'; d.style.cssText = 'margin-top:8px;padding:6px;border:1px solid var(--bd,#d0d5dd);border-radius:6px';
      d.innerHTML = '<b>Warna Surpac (.ssi)</b><div class=hint style="margin:2px 0 4px">Surpac mewarnai string menurut nomornya lewat berkas .ssi bernama sama dengan .str. ' + (U.ssiTxt ? 'Gaya situs terpasang: <b>' + String(U.ssiNama || 'styles.ssi').replace(/[<>&]/g, '') + '</b>.' : 'Belum ada .ssi situs: dipakai gaya bawaan Surpac (1–9, lalu berulang tiap 10: 14 hijau, 16 oranye, 17 merah, 18 ungu). Impor .ssi situs bila standar situs berbeda.') + '</div>' +
        '<div class=g2><button onclick="SWN.imporSitusUI()" title="Pilih berkas .ssi dari Surpac (mis. styles situs atau .ssi sebuah string)">Import .ssi Surpac</button>' + (U.ssiTxt ? '<button onclick="SWN.lupaSitus()">Lepas gaya situs</button>' : '<span></span>') + '</div>' +
        '<label class=sw style="margin-top:4px"><input type=checkbox ' + (U.ssiOut === false ? '' : 'checked') + ' onchange="dbU().ssiOut=this.checked"> Sertakan berkas .ssi saat ekspor STR</label>';
      var hs = Array.prototype.slice.call(el.querySelectorAll('.hint')).filter(function (h) { return /Tiap baris = satu tombol/.test(h.textContent); })[0];
      if (hs) hs.parentNode.insertBefore(d, hs.nextSibling); else t.parentNode.insertBefore(d, t.nextSibling); return r;
    };
  }
  /* ---- tombol impor skema rentang di Warna & kelas kadar ---- */
  if (window.bxPanel) {
    var _bp = bxPanel; window.bxPanel = bxPanel = function () {
      var r = _bp.apply(this, arguments); try { var b = Array.prototype.slice.call(document.querySelectorAll('button')).filter(function (x) { return x.getAttribute('onclick') === 'bxClsCut()'; })[0];
        if (b && !b.parentNode.parentNode.querySelector('.swRg')) { var x = document.createElement('button'); x.className = 'swRg'; x.style.cssText = 'width:100%;margin:-4px 0 8px'; x.title = 'Skema warna rentang kadar Surpac (mis. grade_ore.ssi: 0;0.4;1;3;999~range)'; x.textContent = 'Import .ssi Surpac (skema warna kadar)'; x.onclick = SWN.imporRentangUI; b.parentNode.parentNode.insertBefore(x, b.parentNode.nextSibling); } } catch (e) { }
      return r;
    };
  }
})();
