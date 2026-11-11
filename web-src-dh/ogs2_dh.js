/* ================= ORE GEOMETRY STUDIO — TAHAP 2 (GC-Ex Drillhole 0.24.74) =================
   Keputusan pemilik 11 Nov 2026 (claude/KEPUTUSAN_GCEX_ORE_GEOMETRY_STUDIO.md, butir 3, 4, 7):
   9  Struktur bawah permukaan: long section struktur (collar tertinggi, dasar lubang GC, puncak ore, zona belum teruji GC,
      ore lubang eksplorasi terdalam) + tabel per segmen strike.
   10 Struktur paralel & tekukan: peta sampel >= cut (warna RL), posisi tegak lurus vs sepanjang strike, tabel segmen,
      peta deviasi strike lokal bidang acuan + GT per kelas tekukan (uji Mann-Whitney).
   11 Pertemuan vein: zona = intercept vein bernama berjarak <= sela di satu lubang; GT / tebal / Au zona gabungan vs 1 vein,
      uji per sel lokasi (Wilcoxon), peta jarak bidang ke vein lain, uji kadar sampel dekat vein lain.
   12 Target bor: usulan otomatis + klik di long section; E / N / RL, collar, azimuth & panjang lubang.
   13 Sampel >= cut di luar wireframe: dekat wireframe, di bawah dasar, lanjutan strike, koridor, struktur lain.
   14 Laporan PDF: template deck (navy / emas, Inter, 13,333 x 7,5 in); judul & kalimat ditulis geologist; dicetak lewat
      dialog cetak (Simpan sebagai PDF / Microsoft Print to PDF) atau disimpan sebagai HTML.
   GARIS INTERPRETASI (butir 7): penanda posisi, polyline, pita, poligon, teks — nama, warna, gaya, legenda; disimpan di
   proyek; usulan otomatis bertanda "usulan" sampai diterima; ekspor CSV E/N/RL dan string Surpac .str. */
OGS.ig = null; OGS.tg = null;
(function () { var P = OGS.p; var D = { eksRe: '^(PDH|MDH|DDH|EXP|EX|RC)', cutS: 0.5, winS: 40, bwS: 50, untest: '', jGap: 3, dipB: 57.5, ig: {}, tgt: [], lap: {}, usulTolak: [] }; for (var k in D) if (P[k] == null) P[k] = D[k]; })();
OGS_NAV.splice(OGS_NAV.findIndex(function (x) { return x[0] === '-' && /Tahap 2/.test(x[1]); }), 2,
  ['-', 'Struktur & target'], ['struk', '9 · Struktur bawah permukaan'], ['par', '10 · Struktur paralel & tekukan'], ['jun', '11 · Pertemuan vein'], ['tgt', '12 · Target bor'], ['luar', '13 · Di luar wireframe'], ['-', 'Laporan'], ['lap', '14 · Laporan PDF']);
function ogsEks(h) { try { return new RegExp(OGS.p.eksRe || '^$', 'i').test(h); } catch (e) { return false; } }
function ogsErf(x) { var t = 1 / (1 + 0.3275911 * Math.abs(x)), y = 1 - (((((1.061405429 * t - 1.453152027) * t) + 1.421413741) * t - 0.284496736) * t + 0.254829592) * t * Math.exp(-x * x); return x >= 0 ? y : -y; }
function ogsPz(z) { return 1 - ogsErf(Math.abs(z) / Math.SQRT2); }
function ogsMW(a, b) { var n1 = a.length, n2 = b.length; if (n1 < 3 || n2 < 3) return NaN; var all = a.concat(b), r = ogsRank(all), R1 = 0; for (var i = 0; i < n1; i++) R1 += r[i] + 1; var U = R1 - n1 * (n1 + 1) / 2, m = n1 * n2 / 2, sd = Math.sqrt(n1 * n2 * (n1 + n2 + 1) / 12); return ogsPz((U - m) / sd); }
function ogsWil(d) { d = d.filter(function (v) { return isFinite(v) && v !== 0; }); var n = d.length; if (n < 5) return NaN; var r = ogsRank(d.map(Math.abs)), W = 0; d.forEach(function (v, i) { if (v > 0) W += r[i] + 1; }); var m = n * (n + 1) / 4, sd = Math.sqrt(n * (n + 1) * (2 * n + 1) / 24); return ogsPz((W - m) / sd); }
function ogsP(p) { return !isFinite(p) ? '–' : p < 0.001 ? '&lt; 0,001' : ogsN(p, 3); }
/* titik di bidang acuan (offset w) dari (jarak sepanjang strike, RL) */
function ogsAt(fr, u, z, w) { var nh = [fr.n[0], fr.n[1], 0], hn = Math.hypot(nh[0], nh[1]) || 1; nh = [nh[0] / hn, nh[1] / hn, 0]; var dz = z - fr.c[2], a = ((w || 0) - fr.n[2] * dz) / ogsDot(fr.n, nh); return [fr.c[0] + u * fr.sv[0] + a * nh[0], fr.c[1] + u * fr.sv[1] + a * nh[1], z]; }
function ogsLsOf(p) { var F = OGS.F, r = [p[0] - F.fr.c[0], p[1] - F.fr.c[1], p[2] - F.fr.c[2]]; return [ogsDot(r, F.fr.sv), ogsDot(r, F.fr.n)]; }

/* ================= garis interpretasi ================= */
var OGS_IGC = ['#7048e8', '#1971c2', '#e8590c', '#2f9e44', '#c2255c', '#0c8599', '#495057'];
var OGS_IGT = { v: 'Penanda posisi', line: 'Polyline', band: 'Pita / zona', poly: 'Poligon', text: 'Teks' };
function ogsIgL(key) { var P = OGS.p; return P.ig[key] || (P.ig[key] = []); }
function ogsIgHtml(key, kapan) {
  var L = ogsIgL(key), d = OGS.ig && OGS.ig.key === key ? OGS.ig : null;
  var h = '<div class=ogsig><b>Garis interpretasi</b> <span class=hint>(dibuat geologist; ' + (kapan || 'klik di grafik') + ')</span><br>' +
    Object.keys(OGS_IGT).map(function (t) { return '<button class="' + (d && d.typ === t ? 'btn-pri' : '') + '" onclick="ogsIgStart(\'' + key + '\',\'' + t + '\')">+ ' + OGS_IGT[t] + '</button>'; }).join('') +
    (d ? ' <span class=warn>&#9679; ' + OGS_IGT[d.typ] + ': ' + ({ v: 'klik 1 titik', text: 'klik 1 titik', band: 'klik 2 titik (awal &amp; akhir)', line: 'klik titik-titik, lalu Selesai', poly: 'klik titik-titik, lalu Selesai' }[d.typ]) + ' (' + d.pts.length + ' titik)</span> ' + (d.typ === 'line' || d.typ === 'poly' ? '<button class=btn-pri onclick="ogsIgEnd()">Selesai</button>' : '') + '<button onclick="OGS.ig=null;ogsRender()">Batal</button>' : '') + '</div>';
  if (L.length) h += '<table class=ogst><tr><th>Nama</th><th>Jenis</th><th>Warna</th><th>Gaya</th><th>Legenda</th><th>Keterangan</th><th></th></tr>' + L.map(function (g, i) {
    return '<tr' + (g.usul ? ' style="opacity:.75"' : '') + '><td><input type=text value="' + ogsE(g.nm) + '" onchange="ogsIgSet(\'' + key + '\',' + i + ',\'nm\',this.value)">' + (g.usul ? ' <span class=tag>usulan</span>' : '') + '</td><td>' + OGS_IGT[g.typ] + '</td><td><input type=color value="' + g.col + '" onchange="ogsIgSet(\'' + key + '\',' + i + ',\'col\',this.value)"></td><td>' +
      ogsSel("ogsIgSet('" + key + "'," + i + ",'dash',this.value)", [['solid', 'garis'], ['dash', 'putus-putus'], ['dot', 'titik']], g.dash) + '</td><td><input type=checkbox ' + (g.leg !== false ? 'checked' : '') + ' onchange="ogsIgSet(\'' + key + '\',' + i + ',\'leg\',this.checked)"></td><td><input type=text value="' + ogsE(g.ket || '') + '" onchange="ogsIgSet(\'' + key + '\',' + i + ',\'ket\',this.value)"></td><td>' +
      (g.usul ? '<button class=btn-pri onclick="ogsIgSet(\'' + key + '\',' + i + ',\'usul\',false)">Terima</button>' : '') + '<button class=x onclick="ogsIgDel(\'' + key + '\',' + i + ')">&times;</button></td></tr>'; }).join('') + '</table>' +
    '<div style="margin-top:4px"><button onclick="ogsIgExp(\'' + key + '\',\'csv\')">&#8681; Garis (CSV E/N/RL)</button> <button onclick="ogsIgExp(\'' + key + '\',\'str\')">&#8681; String Surpac (.str)</button></div>';
  return h;
}
function ogsIgStart(key, typ) { OGS.ig = { key: key, typ: typ, pts: [] }; ogsRender(); }
function ogsIgSet(key, i, k, v) { var g = ogsIgL(key)[i]; if (!g) return; g[k] = v; try { if (window.SA && SA.dirty) SA.dirty(); } catch (e) {} ogsRender(); }
function ogsIgDel(key, i) { var L = ogsIgL(key), g = L[i]; if (g && g.usulId) OGS.p.usulTolak.push(g.usulId); L.splice(i, 1); ogsRender(); }
function ogsIgEnd() { var d = OGS.ig; if (!d) return; var need = { v: 1, text: 1, band: 2, line: 2, poly: 3 }[d.typ]; if (d.pts.length < need) { alert('Butuh minimal ' + need + ' titik.'); return; }
  var L = ogsIgL(d.key), def = { v: 'Penanda', line: 'Garis', band: 'Zona', poly: 'Poligon', text: 'Catatan' }[d.typ] + ' ' + (L.length + 1), nm = d.typ === 'text' ? prompt('Teks:', '') : prompt('Nama garis (masuk legenda):', def);
  if (nm == null || nm === '') { OGS.ig = null; ogsRender(); return; }
  L.push({ id: 'g' + Date.now().toString(36), nm: nm, typ: d.typ, pts: d.pts, col: OGS_IGC[L.length % OGS_IGC.length], dash: d.typ === 'v' ? 'dash' : 'solid', leg: true, ket: '' }); OGS.ig = null; try { if (window.SA && SA.dirty) SA.dirty(); } catch (e) {} ogsRender(); }
/* klik di grafik: cari subplot di bawah kursor, ubah piksel -> data */
function ogsIgBind(gdId, key) { var gd = $(gdId); if (!gd || gd._ig) return; gd._ig = 1;
  gd.addEventListener('click', function (e) { var d = OGS.ig; if (!d || d.key !== key) return; var fl = gd._fullLayout, r = gd.getBoundingClientRect(), px = e.clientX - r.left, py = e.clientY - r.top, hit = null;
    Object.keys(fl).filter(function (k) { return /^xaxis\d*$/.test(k); }).forEach(function (k) { var xa = fl[k], ya = fl['y' + k.slice(1)]; if (!ya || hit) return; if (px >= xa._offset && px <= xa._offset + xa._length && py >= ya._offset && py <= ya._offset + ya._length) hit = [xa, ya]; });
    if (!hit) return; var x = hit[0].p2l(px - hit[0]._offset), y = hit[1].p2l(py - hit[1]._offset); d.pts.push([Math.round(x * 10) / 10, Math.round(y * 10) / 10]);
    if (d.typ === 'v' || d.typ === 'text' || (d.typ === 'band' && d.pts.length === 2)) { ogsIgEnd(); return; } ogsRender(); }); }
/* gambar garis ke layout (semua subplot bila multi) + entri legenda */
function ogsIgApply(key, T, Lay, ax) { ax = ax || ['']; var L = ogsIgL(key).slice(), d = OGS.ig && OGS.ig.key === key ? OGS.ig : null; Lay.shapes = Lay.shapes || []; Lay.annotations = Lay.annotations || [];
  if (d && d.pts.length) L.push({ nm: '(sedang digambar)', typ: d.typ === 'text' || d.typ === 'v' ? 'line' : d.typ === 'band' ? 'line' : d.typ, pts: d.pts, col: '#e03131', dash: 'dot', leg: false });
  L.forEach(function (g) { var dash = g.usul ? 'dot' : g.dash, col = g.usul ? '#868e96' : g.col;
    ax.forEach(function (s, k) { var xr = 'x' + s, yr = 'y' + s;
      if (g.typ === 'v') Lay.shapes.push({ type: 'line', xref: xr, yref: yr + ' domain', x0: g.pts[0][0], x1: g.pts[0][0], y0: 0, y1: 1, line: { color: col, width: 1.6, dash: dash } });
      else if (g.typ === 'band') Lay.shapes.push({ type: 'rect', xref: xr, yref: yr + ' domain', x0: g.pts[0][0], x1: g.pts[1][0], y0: 0, y1: 1, fillcolor: col, opacity: 0.13, line: { width: 0 } });
      else if (g.typ === 'line' || g.typ === 'poly') Lay.shapes.push({ type: 'path', xref: xr, yref: yr, path: 'M' + g.pts.map(function (p) { return p[0] + ',' + p[1]; }).join('L') + (g.typ === 'poly' ? 'Z' : ''), line: { color: col, width: 1.8, dash: dash }, fillcolor: g.typ === 'poly' ? col : undefined, opacity: g.typ === 'poly' ? 0.35 : 1 });
      if (g.typ === 'text' || (k === 0 && (g.typ === 'v' || g.typ === 'band'))) Lay.annotations.push({ xref: xr, yref: g.typ === 'text' ? yr : yr + ' domain', x: g.typ === 'band' ? (g.pts[0][0] + g.pts[1][0]) / 2 : g.pts[0][0], y: g.typ === 'text' ? g.pts[0][1] : 0.98, text: ogsE(g.nm) + (g.usul ? ' (usulan)' : ''), showarrow: false, font: { size: 10, color: col }, xanchor: g.typ === 'v' ? 'left' : 'center', yanchor: 'top' }); });
    if (g.leg !== false && g.typ !== 'text' && g.nm !== '(sedang digambar)') T.push({ type: 'scatter', mode: 'lines', x: [null], y: [null], name: g.nm + (g.usul ? ' (usulan)' : ''), line: { color: col, dash: dash, width: g.typ === 'band' ? 8 : 2 }, opacity: g.typ === 'band' ? 0.35 : 1, showlegend: true, xaxis: 'x' + ax[0], yaxis: 'y' + ax[0] }); }); }
/* ekspor: (u, v) grafik -> E / N / RL */
function ogsIgXYZ(key, p) { var F = OGS.F; if (key === 'struk' || key === 'tgtls') return ogsAt(F.fr, p[0], p[1], 0); if (key === 'sec') { var s = OGS.p.sec[OGS.p.secI], g = ogsSecGeom(s); return [g.c[0] + p[0] * g.d[0], g.c[1] + p[0] * g.d[1], p[1]]; }
  if (key === 'par') return ogsAt(F.fr, p[0], F.fr.c[2], p[1]); return null; }
function ogsIgExp(key, fmt) { var F = OGS.F; if (!F) return; var L = ogsIgL(key).filter(function (g) { return !g.usul && g.typ !== 'text'; }); if (!L.length) { alert('Belum ada garis yang diterima.'); return; }
  var S = L.map(function (g) { var P = g.pts; if (g.typ === 'v' || g.typ === 'band') { var xs = g.typ === 'v' ? [P[0][0]] : [P[0][0], P[1][0]], zs = [Math.min.apply(null, F.Z), Math.max.apply(null, F.Z)]; P = []; xs.forEach(function (x) { P.push([x, zs[0]], [x, zs[1]]); }); }
    return { g: g, X: P.map(function (p) { return ogsIgXYZ(key, p); }).filter(Boolean) }; });
  var nm = 'OreGeometry_interpretasi_' + key;
  if (fmt === 'csv') { var R = ['Garis,Jenis,Urut,X,Y,Z,Keterangan']; S.forEach(function (s) { s.X.forEach(function (q, i) { R.push([JSON.stringify(s.g.nm), s.g.typ, i + 1, (q[0] + offX).toFixed(3), (q[1] + offY).toFixed(3), q[2].toFixed(3), JSON.stringify(s.g.ket || '')].join(',')); }); });
    gxDl(new Blob(['﻿' + R.join('\r\n')], { type: 'text/csv' }), nm + '.csv'); return; }
  var o = [nm + ',' + new Date().toISOString().slice(0, 10) + ',,GC-Ex Ore Geometry Studio', '0, 0.000, 0.000, 0.000,'];
  S.forEach(function (s, k) { s.X.forEach(function (q) { o.push((k + 1) + ', ' + (q[1] + offY).toFixed(3) + ', ' + (q[0] + offX).toFixed(3) + ', ' + q[2].toFixed(3) + ', ' + s.g.nm.replace(/,/g, ' ')); }); o.push('0, 0.000, 0.000, 0.000,'); });
  o.push('0, 0.000, 0.000, 0.000, END'); gxDl(new Blob([o.join('\r\n')], { type: 'text/plain' }), nm + '.str'); }
/* usulan otomatis: masuk daftar bertanda usulan (sekali; yang dihapus tidak diusulkan lagi) */
function ogsUsul(key, list) { var L = ogsIgL(key), T = OGS.p.usulTolak; list.forEach(function (u) { if (T.indexOf(u.usulId) >= 0 || L.some(function (g) { return g.usulId === u.usulId; })) return; u.usul = true; u.leg = true; u.col = '#868e96'; u.dash = 'dot'; u.id = u.usulId; L.push(u); }); }

/* ================= 9. struktur bawah permukaan ================= */
function ogsStruk() {
  var F = OGS.F, P = OGS.p, win = +P.winS || 40, cut = +P.cutS || 0.5, au = ogsEi(ogsAu()), H = [], bw = Math.max(10, +P.bwS || 50);
  Object.keys(holeData).forEach(function (id) { var h = holeData[id], c = ogsLsOf([h.x, h.y, h.z]), b = getXYZ(id, h.maxD), q = ogsLsOf([b.x, b.y, b.z]); if (Math.abs(c[1]) > 2 * win && Math.abs(q[1]) > 2 * win) return; H.push({ id: id, ls: c[0], z: h.z, lsb: q[0], zb: b.z, eks: ogsEks(id) }); });
  var S = []; for (var i = 0; i < F.n; i++) if (Math.abs(F.Wd[i]) <= win) S.push(i); var hi = S.filter(function (i) { return F.V[au][i] >= cut; });
  var bin = function (L, v, w2, fn) { var B = {}; L.forEach(function (o) { var k = Math.floor(v(o) / w2); (B[k] = B[k] || []).push(o); }); return Object.keys(B).map(Number).sort(function (a, b) { return a - b; }).map(function (k) { return { x: (k + 0.5) * w2, v: fn(B[k]) }; }); };
  var GC = H.filter(function (h) { return !h.eks; }), EK = H.filter(function (h) { return h.eks; });
  var topo = bin(H, function (h) { return h.ls; }, 20, function (L) { return Math.max.apply(null, L.map(function (h) { return h.z; })); });
  var dasar = bin(GC, function (h) { return h.ls; }, 25, function (L) { return ogsMed(L.map(function (h) { return h.zb; })); });
  var puncak = bin(hi, function (i) { return F.LS[i]; }, 25, function (L) { return Math.max.apply(null, L.map(function (i) { return F.Z[i]; })); });
  var zU = P.untest === '' || P.untest == null ? Math.round(Math.min.apply(null, dasar.map(function (d) { return d.v; }).concat([1e9])) - 20) : +P.untest;
  var hitH = {}; hi.forEach(function (i) { if (!ogsEks(F.A[i][0])) hitH[F.A[i][0]] = 1; });
  var l0 = Math.floor(Math.min.apply(null, S.map(function (i) { return F.LS[i]; })) / bw) * bw, l1 = Math.max.apply(null, S.map(function (i) { return F.LS[i]; })), rows = [];
  for (var a = l0; a < l1; a += bw) { var g = GC.filter(function (h) { return h.ls >= a && h.ls < a + bw; }), hb = hi.filter(function (i) { return F.LS[i] >= a && F.LS[i] < a + bw; }), he = hb.filter(function (i) { return ogsEks(F.A[i][0]); });
    rows.push({ a: a, b: a + bw, ngc: g.length, kena: g.length ? 100 * g.filter(function (h) { return hitH[h.id]; }).length / g.length : NaN, col: ogsMed(g.map(function (h) { return h.z; })), dasar: ogsMed(g.map(function (h) { return h.zb; })), top: hb.length ? Math.max.apply(null, hb.map(function (i) { return F.Z[i]; })) : NaN, deep: he.length ? Math.min.apply(null, he.map(function (i) { return F.Z[i]; })) : NaN, neks: he.length }); }
  /* usulan: segmen GC tanpa hit setelah segmen ber-hit (ujung ore), dan pergeseran posisi tegak lurus > 15 m antar segmen */
  var us = []; rows.forEach(function (r, k) { var p = rows[k - 1]; if (p && r.ngc >= 10 && r.kena === 0 && p.kena > 10) us.push({ usulId: 'ujung' + r.a, nm: 'Ujung ore? (GC ' + r.ngc + ' lubang, 0% kena)', typ: 'v', pts: [[r.a, 0]], ket: 'usulan otomatis' });
    if (p && p.ngc >= 10 && r.kena === 0 && p.kena === 0) return; });
  var wb = bin(hi, function (i) { return F.LS[i]; }, bw, function (L) { return L.length >= 10 ? ogsMed(L.map(function (i) { return F.Wd[i]; })) : NaN; });
  wb.forEach(function (b, k) { var p = wb[k - 1]; if (p && isFinite(b.v) && isFinite(p.v) && Math.abs(b.v - p.v) >= 15) us.push({ usulId: 'geser' + b.x, nm: 'Pergeseran ' + ogsN(Math.abs(b.v - p.v), 0) + ' m ke ' + ogsArah(b.v < p.v ? F.fr.ddir + 180 : F.fr.ddir), typ: 'band', pts: [[p.x, 0], [b.x, 0]], ket: 'usulan otomatis' }); });
  ogsUsul('struk', us);
  return { H: H, GC: GC, EK: EK, S: S, hi: hi, topo: topo, dasar: dasar, puncak: puncak, zU: zU, rows: rows, win: win, cut: cut };
}
function ogsPgStruk() {
  var F = OGS.F; if (!F) return '<h3 class=ogsh>Struktur bawah permukaan</h3>' + ogsNeed(); var P = OGS.p, R = ogsStruk(); OGS._st = R;
  var rows = R.rows.map(function (r) { return [(r.a > 0 ? '+' : '') + ogsN(r.a, 0) + ' s/d ' + (r.b > 0 ? '+' : '') + ogsN(r.b, 0) + ' m', ogsN(r.ngc), isFinite(r.kena) ? ogsN(r.kena, 0) + '%' : '–', ogsN(r.col, 0), ogsN(r.dasar, 0), ogsN(r.top, 0), ogsN(r.deep, 0)]; });
  return '<h3 class=ogsh>Struktur bawah permukaan: apakah ore berhenti di dasar GC?</h3><div class=hint>Long section ±' + R.win + ' m dari bidang acuan. Garis otomatis dari data: collar tertinggi (≈ topografi / pit), dasar lubang GC (median 25 m), puncak ore (sampel ' + ogsE(ogsAu()) + ' ≥ ' + ogsAuto(R.cut) + '), zona belum teruji GC (dasar GC → RL batas). Lubang eksplorasi dikenali dari pola nama. Garis interpretasi (mis. tekukan, ujung ore, sesar) dibuat geologist.</div>' +
    '<div class="g6 f"><div><label>Cut-off sampel</label>' + ogsNum('cutS', P.cutS) + '</div><div><label>Lebar ± dari bidang (m)</label>' + ogsNum('winS', P.winS) + '</div><div><label>Segmen tabel (m)</label>' + ogsNum('bwS', P.bwS) + '</div><div><label>RL batas belum teruji</label><input type=number step=any value="' + ogsE(P.untest) + '" placeholder="' + R.zU + '" onchange="ogsSet(\'untest\',this.value,\'\')"></div><div style="grid-column:span 2"><label>Pola nama lubang eksplorasi (regex)</label><input type=text value="' + ogsE(P.eksRe) + '" onchange="ogsSet(\'eksRe\',this.value,\'\')"></div></div>' +
    ogsIgHtml('struk') + ogsFig('ogsST', 460, 'struktur_long_section') + ogsCsvBtn('ogsTS', 'struktur_segmen') + ogsTab(['Sepanjang strike', 'Lubang GC', 'Kena ≥ ' + ogsAuto(R.cut), 'Collar RL', 'Dasar GC RL', 'Puncak ore RL', 'Ore eksplorasi terdalam RL'], rows, rows.map(function (r, k) { return R.rows[k].ngc >= 10 && R.rows[k].kena === 0 ? k : -1; }), 'ogsTS') +
    '<p class=ogscap>' + ogsN(R.GC.length) + ' lubang GC, ' + ogsN(R.EK.length) + ' lubang eksplorasi di koridor. Baris kuning = ≥ 10 lubang GC tanpa sampel ≥ cut-off.</p>';
}
function ogsDrStruk() {
  var F = OGS.F, R = OGS._st || ogsStruk(), gd = $('ogsST'); if (!F || !gd) return; var T = [], gc = { x: [], y: [] }, ek = { x: [], y: [] };
  R.GC.forEach(function (h) { gc.x.push(h.ls, h.lsb, null); gc.y.push(h.z, h.zb, null); }); R.EK.forEach(function (h) { ek.x.push(h.ls, h.lsb, null); ek.y.push(h.z, h.zb, null); });
  T.push({ type: 'scattergl', mode: 'lines', x: gc.x, y: gc.y, line: { color: '#ced4da', width: 0.6 }, hoverinfo: 'skip', name: 'lubang GC', showlegend: true });
  T.push({ type: 'scatter', mode: 'lines', x: ek.x, y: ek.y, line: { color: '#495057', width: 1, dash: 'dash' }, hoverinfo: 'skip', name: 'lubang eksplorasi', showlegend: true });
  var d = R.dasar; T.push({ type: 'scatter', mode: 'lines', x: d.map(function (o) { return o.x; }).concat(d.map(function (o) { return o.x; }).reverse()), y: d.map(function (o) { return Math.max(o.v, R.zU); }).concat(d.map(function () { return R.zU; }).reverse()), fill: 'toself', fillcolor: 'rgba(255,224,102,0.35)', line: { width: 0 }, hoverinfo: 'skip', name: 'belum teruji GC (dasar GC → RL ' + R.zU + ')', showlegend: true });
  T.push({ type: 'scatter', mode: 'lines', x: R.topo.map(function (o) { return o.x; }), y: R.topo.map(function (o) { return o.v; }), line: { color: '#8c4b3a', width: 1.6 }, name: 'collar tertinggi (≈ topografi / pit)', showlegend: true });
  T.push({ type: 'scatter', mode: 'lines', x: d.map(function (o) { return o.x; }), y: d.map(function (o) { return o.v; }), line: { color: '#1971c2', width: 2 }, name: 'dasar lubang GC (median 25 m)', showlegend: true });
  T.push({ type: 'scatter', mode: 'lines', x: R.puncak.map(function (o) { return o.x; }), y: R.puncak.map(function (o) { return o.v; }), line: { color: '#e03131', width: 2 }, name: 'puncak ore ≥ ' + ogsAuto(R.cut), showlegend: true });
  var au = ogsEi(ogsAu()), h = R.hi.slice().sort(function (a, b) { return F.V[au][a] - F.V[au][b]; });
  T.push({ type: 'scattergl', mode: 'markers', x: h.map(function (i) { return F.LS[i]; }), y: h.map(function (i) { return F.Z[i]; }), text: h.map(function (i) { return F.A[i][0] + ' · ' + ogsAuto(F.V[au][i]) + ' · w ' + ogsN(F.Wd[i], 0) + ' m'; }),
    marker: { size: h.map(function (i) { return Math.max(4, Math.min(16, 3 + 2.2 * F.V[au][i])); }), color: h.map(function (i) { return F.Wd[i]; }), cmin: -R.win * 0.75, cmax: R.win * 0.75, colorscale: 'RdBu', reversescale: true, line: { width: 0.4, color: '#333' }, colorbar: { title: { text: 'jarak dari bidang (m, + = ' + ogsArah(F.fr.ddir) + ')', side: 'right' }, thickness: 12 } }, name: 'sampel ≥ ' + ogsAuto(R.cut) + ' (ukuran ∝ ' + ogsAu() + ')', showlegend: true });
  var Lay = ogsLay({ title: { text: 'Long section struktur ±' + R.win + ' m dari bidang acuan (strike ' + ogsAzTxt(F.fr.az) + ')', font: { size: 12 } }, xaxis: { title: 'jarak sepanjang strike (m) → ' + ogsArah(F.fr.az) }, yaxis: { title: 'RL (m)' }, showlegend: true, legend: { orientation: 'h', y: -0.18, font: { size: 10 } }, margin: { l: 56, r: 16, t: 34, b: 90 } });
  ogsIgApply('struk', T, Lay); Plotly.newPlot(gd, T, Lay, OGS_CFG); ogsIgBind('ogsST', 'struk');
}

/* ================= 10. struktur paralel & tekukan ================= */
function ogsPgPar() {
  var F = OGS.F; if (!F) return '<h3 class=ogsh>Struktur paralel &amp; tekukan</h3>' + ogsNeed(); var P = OGS.p, cut = +P.cutS || 0.5, au = ogsEi(ogsAu()), ls = F.I.map(function (c) { return c.ls; }), a = ogsQ(ls, 0.02), b = ogsQ(ls, 0.98), st = (b - a) / 3, rows = [], neg = ogsArah(F.fr.ddir + 180), pos = ogsArah(F.fr.ddir);
  for (var k = 0; k < 3; k++) { var s0 = a + k * st, s1 = s0 + st, I = []; for (var i = 0; i < F.n; i++) if (F.LS[i] >= s0 && F.LS[i] < s1 && isFinite(F.V[au][i]) && Math.abs(F.Wd[i]) <= 60) I.push(i);
    var lab = ogsN(s0, 0) + ' s/d ' + ogsN(s1, 0) + ' m', add = function (nm, L) { if (!L.length) return; rows.push([lab, nm, ogsN(L.length), ogsN(L.filter(function (i) { return F.V[au][i] >= cut; }).length), ogsAuto(ogsWmean(F, au, L))]); };
    F.dom.forEach(function (d, q) { add(ogsE(d.nm), I.filter(function (i) { return F.D[i] === q; })); });
    add('di luar wireframe, sisi ' + neg, I.filter(function (i) { return F.D[i] < 0 && F.Wd[i] < 0; })); add('di luar wireframe, sisi ' + pos, I.filter(function (i) { return F.D[i] < 0 && F.Wd[i] >= 0; })); }
  var B = ogsBend(), bt = B ? B.cls.map(function (c) { return [c[0], ogsN(c[1]), ogsAuto(c[2]), ogsAuto(c[3])]; }) : [];
  return '<h3 class=ogsh>Struktur paralel &amp; tekukan</h3><div class=hint>Sampel ' + ogsE(ogsAu()) + ' ≥ ' + ogsAuto(cut) + ' di peta (warna = RL) dan posisinya tegak lurus bidang acuan vs sepanjang strike (warna = domain). Tabel: sampel ≤ 60 m dari bidang per sepertiga panjang strike. Garis interpretasi bisa ditarik di grafik kanan.</div>' +
    ogsIgHtml('par', 'klik di grafik posisi tegak lurus') + '<div class=ogs2 style="grid-template-columns:1fr 1.6fr"><div>' + ogsFig('ogsPA', 470, 'peta_struktur_paralel') + '</div><div>' + ogsFig('ogsPB', 470, 'posisi_tegak_lurus') + '</div></div>' +
    ogsCsvBtn('ogsTP', 'struktur_paralel') + ogsTab(['Segmen strike', 'Posisi', 'Sampel', '≥ ' + ogsAuto(cut), ogsE(ogsAu()) + ' rata-rata'], rows, [], 'ogsTP') +
    '<h4 style="margin-top:12px">Tekukan strike bidang acuan (' + ogsE(F.dom[F.ref] ? F.dom[F.ref].nm : '–') + ')</h4>' + (B ? '<div class=ogs2 style="grid-template-columns:1.8fr 1fr"><div>' + ogsFig('ogsBD', 380, 'tekukan_strike') + '</div><div>' + ogsCsvBtn('ogsTB', 'tekukan') + ogsTab(['Kelas deviasi strike', 'Intercept', 'GT median', ogsE(ogsAu()) + ' median'], bt, [], 'ogsTB') +
      '<p class=ogscap>Deviasi = sudut lokal bidang (RBF posisi tegak lurus) terhadap strike rata-rata. Tekukan &gt; 10° vs lurus ±3°: GT median ' + ogsAuto(B.gB) + ' vs ' + ogsAuto(B.gS) + ', Mann-Whitney p = ' + ogsP(B.p) + (B.p < 0.05 ? ' (signifikan)' : ' (belum signifikan)') + '.</p></div></div>' : '<p class=hint>Domain acuan butuh ≥ 5 intercept.</p>');
}
function ogsBend() { var F = OGS.F, E = ogsEnv(F.ref); if (!E) return null; var nx = E.xs.length, nz = E.zs.length, A = []; for (var r = 0; r < nz; r++) { var row = []; for (var c = 0; c < nx; c++) { var w0 = E.W[r][c - 1], w1 = E.W[r][c + 1], v = null; if (w0 != null && w1 != null) v = Math.atan((w1 - w0) / (2 * E.res)) * 180 / Math.PI; else if (E.W[r][c] != null && (w1 != null || w0 != null)) v = Math.atan(((w1 != null ? w1 : E.W[r][c]) - (w0 != null ? w0 : E.W[r][c])) / E.res) * 180 / Math.PI; row.push(v); } A.push(row); }
  var at = function (u, z) { var c = Math.round((u - E.xs[0]) / E.res), r = Math.round((z - E.zs[0]) / E.res); return r >= 0 && r < nz && c >= 0 && c < nx ? A[r][c] : null; };
  var L = E.L.map(function (c, i) { return { gt: c.gt, au: c.g[ogsEi(ogsAu())], dev: at(E.U[i], E.Zc[i]) }; }).filter(function (o) { return o.dev != null; });
  var K = [['< −10°', -90, -10], ['−10 s/d −3°', -10, -3], ['lurus ±3°', -3, 3], ['+3 s/d +10°', 3, 10], ['> +10°', 10, 90]].map(function (k) { var q = L.filter(function (o) { return o.dev >= k[1] && o.dev < k[2]; }); return [k[0], q.length, ogsMed(q.map(function (o) { return o.gt; })), ogsMed(q.map(function (o) { return o.au; }))]; });
  var bB = L.filter(function (o) { return Math.abs(o.dev) > 10; }).map(function (o) { return o.gt; }), bS = L.filter(function (o) { return Math.abs(o.dev) <= 3; }).map(function (o) { return o.gt; });
  return { E: E, A: A, cls: K, p: ogsMW(bB, bS), gB: ogsMed(bB), gS: ogsMed(bS) }; }
function ogsDrPar() {
  var F = OGS.F; if (!F || !$('ogsPA')) return; var cut = +OGS.p.cutS || 0.5, au = ogsEi(ogsAu()), I = []; for (var i = 0; i < F.n; i++) if (F.V[au][i] >= cut && Math.abs(F.Wd[i]) <= 60) I.push(i); I.sort(function (a, b) { return F.Z[a] - F.Z[b]; });
  var T = [{ type: 'scattergl', mode: 'markers', x: I.map(function (i) { return F.X[i] + offX; }), y: I.map(function (i) { return F.Y[i] + offY; }), marker: { size: 4, color: I.map(function (i) { return F.Z[i]; }), colorscale: 'Viridis', colorbar: { title: { text: 'RL', side: 'right' }, thickness: 10 } }, hoverinfo: 'skip', showlegend: false }];
  F.dom.forEach(function (d) { if (!d.pl) return; var fr = ogsMkFrame(d.pl), L = F.I.filter(function (c) { return F.dom[c.d] === d; }).map(function (c) { return ogsDot([c.p[0] - fr.c[0], c.p[1] - fr.c[1], 0], fr.sv); }), u0 = Math.min.apply(null, L) - 30, u1 = Math.max.apply(null, L) + 30;
    T.push({ type: 'scatter', mode: 'lines', x: [fr.c[0] + u0 * fr.sv[0] + offX, fr.c[0] + u1 * fr.sv[0] + offX], y: [fr.c[1] + u0 * fr.sv[1] + offY, fr.c[1] + u1 * fr.sv[1] + offY], line: { color: d.col, width: 1.6 }, name: 'jejak ' + d.nm, showlegend: true }); });
  Plotly.newPlot('ogsPA', T, ogsLay({ title: { text: 'Peta sampel ≥ ' + ogsAuto(cut) + ' (warna = RL)', font: { size: 11 } }, showlegend: true, legend: { font: { size: 9 }, x: 0, y: 1 }, xaxis: { tickformat: 'd', tickfont: { size: 8 } }, yaxis: { tickformat: 'd', tickfont: { size: 8 }, scaleanchor: 'x' } }), OGS_CFG);
  var T2 = [{ type: 'scattergl', mode: 'markers', x: I.filter(function (i) { return F.D[i] < 0; }).map(function (i) { return F.LS[i]; }), y: I.filter(function (i) { return F.D[i] < 0; }).map(function (i) { return F.Wd[i]; }), marker: { size: 4, color: '#adb5bd' }, name: 'di luar wireframe', showlegend: true }];
  F.dom.forEach(function (d, q) { var J = I.filter(function (i) { return F.D[i] === q; }); if (J.length) T2.push({ type: 'scattergl', mode: 'markers', x: J.map(function (i) { return F.LS[i]; }), y: J.map(function (i) { return F.Wd[i]; }), marker: { size: 5, color: d.col }, name: d.nm, showlegend: true }); });
  var Lay = ogsLay({ title: { text: 'Posisi tegak lurus vs sepanjang strike, ' + ogsAu() + ' ≥ ' + ogsAuto(cut), font: { size: 11 } }, showlegend: true, legend: { orientation: 'h', y: -0.2, font: { size: 9 } }, xaxis: { title: 'jarak sepanjang strike (m) → ' + ogsArah(F.fr.az) }, yaxis: { title: 'jarak dari bidang acuan (m, + = ' + ogsArah(F.fr.ddir) + ')', zeroline: true }, margin: { l: 60, r: 10, t: 30, b: 80 } });
  ogsIgApply('par', T2, Lay); Plotly.newPlot('ogsPB', T2, Lay, OGS_CFG); ogsIgBind('ogsPB', 'par');
  var B = ogsBend(); if (B && $('ogsBD')) { var E = B.E, L = E.L.slice().sort(function (a, b) { return a.gt - b.gt; });
    Plotly.newPlot('ogsBD', [{ type: 'heatmap', x: E.xs, y: E.zs, z: B.A, zmin: -20, zmax: 20, colorscale: 'RdBu', reversescale: true, colorbar: { title: { text: 'deviasi strike (°)', side: 'right' }, thickness: 10 } },
      { type: 'scatter', mode: 'markers', x: E.L.map(function (c, i) { return E.U[i]; }), y: E.Zc, marker: { size: E.L.map(function (c) { return Math.max(4, Math.min(18, 3 + 2 * c.gt)); }), color: 'rgba(0,0,0,0)', line: { width: 0.8, color: '#000' } }, text: E.L.map(function (c) { return c.h + ' GT ' + ogsAuto(c.gt); }) }],
      ogsLay({ title: { text: 'Tekukan strike (merah = searah jarum jam) dan GT intercept (lingkaran)', font: { size: 11 } }, xaxis: { title: 'jarak sepanjang strike domain (m)' }, yaxis: { title: 'RL (m)' } }), OGS_CFG); }
}

/* ================= 11. pertemuan vein ================= */
function ogsZona() { var F = OGS.F, g = Math.max(0, +OGS.p.jGap || 3), au = ogsEi(ogsAu()), I = F.I.filter(function (c) { return isFinite(c.gt); }).slice().sort(function (a, b) { return a.h < b.h ? -1 : a.h > b.h ? 1 : a.f - b.f; }), Z = [], cur = null;
  I.forEach(function (c) { if (cur && cur.h === c.h && c.f - cur.t <= g) { cur.t = Math.max(cur.t, c.t); cur.d[c.d] = 1; cur.gt += c.gt; cur.T += c.T; cur.m += c.g[au] * c.T; cur.n++; return; } if (cur) Z.push(cur); cur = { h: c.h, f: c.f, t: c.t, d: {}, gt: c.gt, T: c.T, m: c.g[au] * c.T, n: 1, ls: c.ls, z: c.p[2] }; cur.d[c.d] = 1; });
  if (cur) Z.push(cur); Z.forEach(function (z) { z.nd = Object.keys(z.d).length; z.au = z.T > 0 ? z.m / z.T : NaN; z.pair = Object.keys(z.d).map(function (q) { return F.dom[q].nm; }).sort().join(' + '); }); return Z; }
function ogsJun() {
  var F = OGS.F, Z = ogsZona(), M = Z.filter(function (z) { return z.nd >= 2; }), S = Z.filter(function (z) { return z.nd === 1; }), st = function (L) { return { n: L.length, gt: ogsMed(L.map(function (z) { return z.gt; })), T: ogsMed(L.map(function (z) { return z.T; })), au: ogsMed(L.map(function (z) { return z.au; })), g2: L.length ? 100 * L.filter(function (z) { return z.gt >= 2; }).length / L.length : NaN }; };
  var C = {}; Z.forEach(function (z) { var k = Math.floor(z.ls / 50) + '_' + Math.floor(z.z / 25); (C[k] = C[k] || []).push(z); }); var sel = [];
  Object.keys(C).forEach(function (k) { var a = C[k].filter(function (z) { return z.nd >= 2; }), b = C[k].filter(function (z) { return z.nd === 1; }); if (a.length >= 3 && b.length >= 3) sel.push({ ga: ogsMed(a.map(function (z) { return z.gt; })), gb: ogsMed(b.map(function (z) { return z.gt; })), aa: ogsMed(a.map(function (z) { return z.au; })), ab: ogsMed(b.map(function (z) { return z.au; })) }); });
  var strat = { n: sel.length, gt: sel.filter(function (s) { return s.ga > s.gb; }).length, au: sel.filter(function (s) { return s.aa > s.ab; }).length, rg: ogsMed(sel.map(function (s) { return s.ga / s.gb; })), ra: ogsMed(sel.map(function (s) { return s.aa / s.ab; })), pg: ogsWil(sel.map(function (s) { return Math.log(s.ga / s.gb); })), pa: ogsWil(sel.map(function (s) { return Math.log(s.aa / s.ab); })) };
  var pr = {}; M.forEach(function (z) { pr[z.pair] = (pr[z.pair] || 0) + 1; });
  var ls = Z.map(function (z) { return z.ls; }), a = ogsQ(ls, 0.02), b = ogsQ(ls, 0.98), w = (b - a) / 3, seg = [];
  for (var k = 0; k < 3; k++) { var s0 = a + k * w, s1 = s0 + w, L = Z.filter(function (z) { return z.ls >= s0 && z.ls < s1; }), x = L.filter(function (z) { return z.nd >= 2; }), y = L.filter(function (z) { return z.nd === 1; }); seg.push([ogsN(s0, 0) + ' s/d ' + ogsN(s1, 0) + ' m', L.length, L.length ? 100 * x.length / L.length : NaN, ogsMed(x.map(function (z) { return z.gt; })), ogsMed(y.map(function (z) { return z.gt; })), ogsMed(x.map(function (z) { return z.au; })), ogsMed(y.map(function (z) { return z.au; }))]); }
  /* uji sampel: kadar sampel vein vs jarak 3D ke sampel domain lain (hash 5 m) */
  var au = ogsEi(ogsAu()), V = ogsIn(F), cs = 5, Hh = {}; V.forEach(function (i) { var k = Math.floor(F.X[i] / cs) + ',' + Math.floor(F.Y[i] / cs) + ',' + Math.floor(F.Z[i] / cs); (Hh[k] = Hh[k] || []).push(i); });
  var near = [], far = []; V.forEach(function (i) { var v = F.V[au][i]; if (!isFinite(v)) return; var gx = Math.floor(F.X[i] / cs), gy = Math.floor(F.Y[i] / cs), gz = Math.floor(F.Z[i] / cs), dm = 1e9;
    for (var a2 = -2; a2 <= 2; a2++) for (var b2 = -2; b2 <= 2; b2++) for (var c2 = -2; c2 <= 2; c2++) { var L = Hh[(gx + a2) + ',' + (gy + b2) + ',' + (gz + c2)]; if (L) L.forEach(function (j) { if (F.D[j] === F.D[i]) return; var d = Math.hypot(F.X[i] - F.X[j], F.Y[i] - F.Y[j], F.Z[i] - F.Z[j]); if (d < dm) dm = d; }); }
    if (dm <= 3) near.push(v); else if (dm > 6) far.push(v); });
  return { Z: Z, M: M, S: S, sm: st(M), ss: st(S), strat: strat, pr: pr, seg: seg, smp: { n1: near.length, n2: far.length, m1: ogsMed(near), m2: ogsMed(far), p: ogsMW(near, far) } };
}
function ogsPgJun() {
  var F = OGS.F; if (!F) return '<h3 class=ogsh>Pertemuan vein</h3>' + ogsNeed(); if (F.dom.length < 2) return '<h3 class=ogsh>Pertemuan vein</h3><div class=hint>Butuh minimal 2 domain.</div>'; var P = OGS.p, J = ogsJun(); OGS._jn = J; var a = J.sm, b = J.ss, s = J.strat;
  var hd = function (x) { return x.gt > 0 && J.ss.gt > 0 ? ogsN(x.gt / J.ss.gt, 1) + '×' : '–'; };
  var rows = [['1 vein', ogsN(b.n), ogsAuto(b.gt), ogsN(b.T, 2), ogsAuto(b.au), ogsN(b.g2, 0) + '%'], ['Pertemuan ≥ 2 vein', ogsN(a.n), ogsAuto(a.gt), ogsN(a.T, 2), ogsAuto(a.au), ogsN(a.g2, 0) + '%']];
  var seg = J.seg.map(function (r) { return [r[0], ogsN(r[1]), ogsN(r[2], 0) + '%', ogsAuto(r[3]), ogsAuto(r[4]), ogsAuto(r[5]), ogsAuto(r[6])]; }), pr = Object.keys(J.pr).sort(function (x, y) { return J.pr[y] - J.pr[x]; });
  var kes = !s.n ? 'Sel lokasi yang punya kedua jenis zona (≥ 3 masing-masing) belum ada; perbandingan belum bisa diuji per lokasi.' : 'Per sel lokasi (50 m strike × 25 m RL, ' + s.n + ' sel): GT pertemuan lebih tinggi di ' + s.gt + ' sel (rasio median ' + ogsN(s.rg, 2) + ', Wilcoxon p = ' + ogsP(s.pg) + '); ' + ogsE(ogsAu()) + ' lebih tinggi di ' + s.au + ' sel (rasio ' + ogsN(s.ra, 2) + ', p = ' + ogsP(s.pa) + ').';
  return '<h3 class=ogsh>Pertemuan vein: kadar di zona tempat dua vein atau lebih bertemu</h3><div class=hint><b>Zona</b> = intercept vein bernama di satu lubang yang berjarak ≤ sela sepanjang lubang. GT zona = jumlah GT vein di zona itu (naik juga karena dijumlah); ' + ogsE(ogsAu()) + ' zona = rata-rata tertimbang tebal (ukuran yang adil). Uji per sel lokasi menyingkirkan efek letak.</div>' +
    '<div class="g6 f"><div><label>Sela pertemuan (m)</label>' + ogsNum('jGap', P.jGap) + '</div></div>' + ogsFig('ogsJB', 330, 'pertemuan_vein') +
    '<div class=ogs2 style="grid-template-columns:1.2fr 1fr"><div>' + ogsCsvBtn('ogsTJ', 'pertemuan_vein') + ogsTab(['Zona', 'n', 'GT median', 'Tebal median', ogsE(ogsAu()) + ' median', 'GT ≥ 2'], rows, [1], 'ogsTJ') +
    '<div style="height:6px"></div>' + ogsTab(['Segmen strike', 'Zona', '% pertemuan', 'GT pertemuan', 'GT 1 vein', ogsE(ogsAu()) + ' pertemuan', ogsE(ogsAu()) + ' 1 vein'], seg) + '</div><div>' +
    '<div class=card><h4>Uji per lokasi</h4><p>' + kes + '</p></div><div class=card><h4>Pasangan yang bertemu</h4><p>' + (pr.length ? pr.slice(0, 8).map(function (k) { return ogsE(k) + ' <b>' + J.pr[k] + '</b>'; }).join(' · ') : '–') + '</p></div>' +
    '<div class=card><h4>Uji lain: kadar sampel di dekat vein lain</h4><p>Sampel vein ≤ 3 m dari vein lain: median ' + ogsAuto(J.smp.m1) + ' (n ' + J.smp.n1 + ') vs &gt; 6 m: ' + ogsAuto(J.smp.m2) + ' (n ' + J.smp.n2 + '); Mann-Whitney p = ' + ogsP(J.smp.p) + '.</p></div></div></div>' +
    '<h4 style="margin-top:10px">Jarak bidang acuan ke vein lain</h4>' + ogsFig('ogsJM', 420, 'peta_pertemuan');
}
function ogsSep() { var F = OGS.F, E = ogsEnv(F.ref); if (!E) return null; if (E._sep) return E._sep; var cs = 5, Hh = {}, R = 15;
  F.dom.forEach(function (d, q) { if (q === F.ref) return; var e = ogsEnv(q); if (!e) return; e.zs.forEach(function (z, r) { e.xs.forEach(function (u, c) { if (e.GT[r][c] == null) return; var p = e.at(u, z, e.W[r][c]), k = Math.floor(p[0] / cs) + ',' + Math.floor(p[1] / cs) + ',' + Math.floor(p[2] / cs); (Hh[k] = Hh[k] || []).push(p); }); }); });
  if (!Object.keys(Hh).length) return null; var n = Math.ceil(R / cs), st = E.res < 3 ? 2 : 1, S = E.zs.map(function (z, r) { return E.xs.map(function (u, c) { if (E.GT[r][c] == null) return null; if (r % st || c % st) return undefined; var p = E.at(u, z, E.W[r][c]), gx = Math.floor(p[0] / cs), gy = Math.floor(p[1] / cs), gz = Math.floor(p[2] / cs), dm = R;
      for (var a = -n; a <= n; a++) for (var b = -n; b <= n; b++) for (var k = -n; k <= n; k++) { var L = Hh[(gx + a) + ',' + (gy + b) + ',' + (gz + k)]; if (L) for (var j = 0; j < L.length; j++) { var d = Math.hypot(p[0] - L[j][0], p[1] - L[j][1], p[2] - L[j][2]); if (d < dm) dm = d; } } return dm; }); });
  S.forEach(function (row, r) { row.forEach(function (v, c) { if (v === undefined) { var r0 = r - r % st, c0 = c - c % st, q = S[r0] && S[r0][c0]; row[c] = q == null ? R : q; } }); });
  return (E._sep = { E: E, S: S }); }
function ogsDrJun() {
  var F = OGS.F, J = OGS._jn; if (!F || !J || !$('ogsJB')) return; var a = J.sm, b = J.ss, T = [], Lay = {}, it = [['gt', 'GT median', 'g/t·m'], ['T', 'Tebal median', 'm'], ['au', ogsAu() + ' median zona', '']];
  it.forEach(function (q, k) { var s = k ? String(k + 1) : ''; Lay['xaxis' + s] = { domain: [k * 0.13, k * 0.13 + 0.11], anchor: 'y' + s, tickfont: { size: 9 } }; Lay['yaxis' + s] = { anchor: 'x' + s, title: { text: q[2], font: { size: 9 } }, tickfont: { size: 9 } };
    T.push({ type: 'bar', x: ['1 vein', '≥ 2 vein'], y: [b[q[0]], a[q[0]]], text: [ogsAuto(b[q[0]]), ogsAuto(a[q[0]])], textposition: 'outside', marker: { color: ['#adb5bd', '#c2540a'] }, xaxis: 'x' + s, yaxis: 'y' + s, showlegend: false });
    (Lay.annotations = Lay.annotations || []).push({ text: q[1], xref: 'x' + s + ' domain', yref: 'y' + s + ' domain', x: 0.5, y: 1.1, showarrow: false, font: { size: 10 } }); });
  Lay.xaxis4 = { domain: [0.42, 1], anchor: 'y4', title: { text: 'jarak sepanjang strike (m) → ' + ogsArah(F.fr.az), font: { size: 10 } } }; Lay.yaxis4 = { anchor: 'x4', title: { text: 'RL (m)', font: { size: 10 } } };
  [[J.S, '#adb5bd', 'zona 1 vein'], [J.M, '#c2540a', 'pertemuan ≥ 2 vein']].forEach(function (g) { T.push({ type: 'scattergl', mode: 'markers', x: g[0].map(function (z) { return z.ls; }), y: g[0].map(function (z) { return z.z; }), text: g[0].map(function (z) { return z.h + ' · ' + z.pair + ' · GT ' + ogsAuto(z.gt); }), marker: { size: g[0].map(function (z) { return Math.max(4, Math.min(18, 3 + 1.5 * z.gt)); }), color: g[1], line: { width: 0.4, color: '#333' } }, name: g[2] + ' (n=' + g[0].length + ')', xaxis: 'x4', yaxis: 'y4' }); });
  Plotly.newPlot('ogsJB', T, ogsLay(Object.assign(Lay, { showlegend: true, legend: { x: 1, xanchor: 'right', y: 0, font: { size: 9 } }, margin: { l: 44, r: 10, t: 30, b: 44 } })), OGS_CFG);
  var S = ogsSep(); if (!S || !$('ogsJM')) return; var E = S.E;
  Plotly.newPlot('ogsJM', [{ type: 'heatmap', x: E.xs, y: E.zs, z: S.S, zmin: 0, zmax: 20, colorscale: [[0, '#fff3bf'], [0.15, '#f4a261'], [0.5, '#9c2c6b'], [1, '#1a0b2e']], colorbar: { title: { text: 'jarak ke vein lain (m)', side: 'right' }, thickness: 10 } },
    { type: 'contour', x: E.xs, y: E.zs, z: S.S, showscale: false, contours: { start: 3, end: 3, size: 1, coloring: 'none' }, line: { color: '#00b4d8', width: 2 }, hoverinfo: 'skip', name: 'pertemuan: < 3 m ke vein lain', showlegend: true },
    { type: 'scatter', mode: 'markers', x: E.U, y: E.Zc, marker: { size: E.L.map(function (c) { return Math.max(4, Math.min(18, 3 + 2 * c.gt)); }), color: '#2b8a3e', line: { width: 0.6, color: '#fff' } }, text: E.L.map(function (c) { return c.h + ' GT ' + ogsAuto(c.gt); }), name: 'GT intercept', showlegend: true }],
    ogsLay({ title: { text: F.dom[F.ref].nm + ' · jarak ke bidang vein lain (warna) dan GT intercept', font: { size: 11 } }, showlegend: true, legend: { orientation: 'h', y: -0.2, font: { size: 9 } }, xaxis: { title: 'jarak sepanjang strike domain (m)' }, yaxis: { title: 'RL (m)' }, margin: { l: 56, r: 10, t: 30, b: 80 } }), OGS_CFG);
}

/* ================= 12. target bor ================= */
function ogsTgtHit(t) { var F = OGS.F, P = OGS.p, au = ogsEi(ogsAu()), cut = +P.cutS || 0.5, L = []; for (var i = 0; i < F.n; i++) if (F.V[au][i] >= cut && Math.abs(F.LS[i] - t.ls) <= 30 && Math.abs(F.Wd[i]) <= 40) L.push(F.Wd[i]);
  var w = L.length ? ogsMed(L) : 0, X = ogsAt(F.fr, t.ls, t.z, w), col = -1e9; Object.keys(holeData).forEach(function (id) { var h = holeData[id], q = ogsLsOf([h.x, h.y, h.z]); if (Math.abs(q[0] - t.ls) <= 25 && Math.abs(q[1]) <= 120 && h.z > col) col = h.z; });
  if (col < -1e8) col = t.z + 60; var dip = (+P.dipB || 57.5) * Math.PI / 180, az = (F.fr.ddir + 180) % 360, dz = Math.max(1, col - t.z), back = dz / Math.tan(dip), r = (az + 180) * Math.PI / 180;
  return { w: w, X: X, col: col, az: az, len: dz / Math.sin(dip), cx: X[0] + Math.sin(r) * back, cy: X[1] + Math.cos(r) * back }; }
function ogsTgtUsul() { var F = OGS.F, P = OGS.p, R = ogsStruk(), base = function (ls) { var b = R.dasar.filter(function (d) { return Math.abs(d.x - ls) <= 25; }); return b.length ? ogsMed(b.map(function (d) { return d.v; })) : 1e9; };
  var E = F.I.filter(function (c) { return ogsEks(c.h) && isFinite(c.gt) && c.p[2] < base(c.ls); }).sort(function (a, b) { return b.gt - a.gt; }), out = [];
  if (!E.length) { /* tanpa lubang eksplorasi: intercept terdalam tiap segmen 50 m yang GT-nya >= median (mineralisasi terbuka ke bawah) */
    var B = {}, md = ogsMed(F.I.map(function (c) { return c.gt; })); F.I.forEach(function (c) { if (!isFinite(c.gt)) return; var k = Math.floor(c.ls / 50); if (!B[k] || c.p[2] < B[k].p[2]) B[k] = c; });
    E = Object.keys(B).map(function (k) { return B[k]; }).filter(function (c) { return c.gt >= md; }).sort(function (a, b) { return b.gt - a.gt; }); }
  E.forEach(function (c) { if (out.length < 4 && out.every(function (t) { return Math.abs(t.ls - c.ls) >= 40; })) out.push({ nm: 'T' + (out.length + 1) + ' · bawah ' + c.h, ls: Math.round(c.ls), z: Math.round(c.p[2] - 25), ket: 'GT ' + ogsAuto(c.gt) + ' di RL ' + ogsN(c.p[2], 0) }); });
  var I = F.I.map(function (c) { return c.ls; }).sort(function (a, b) { return a - b; }), gap = null; for (var k = 1; k < I.length; k++) { var g = I[k] - I[k - 1]; if (g > 40 && (!gap || g > gap.g)) gap = { g: g, ls: (I[k] + I[k - 1]) / 2 }; }
  if (gap) out.push({ nm: 'T' + (out.length + 1) + ' · celah data', ls: Math.round(gap.ls), z: Math.round(ogsMed(F.I.map(function (c) { return c.p[2]; }))), ket: 'celah ' + ogsN(gap.g, 0) + ' m tanpa intercept' });
  P.tgt = out; ogsRender(); }
function ogsPgTgt() {
  var F = OGS.F; if (!F) return '<h3 class=ogsh>Target bor</h3>' + ogsNeed(); var P = OGS.p, d = OGS.ig && OGS.ig.key === 'tgt';
  var rows = P.tgt.map(function (t, i) { var q = ogsTgtHit(t); return ['<input type=text value="' + ogsE(t.nm) + '" onchange="OGS.p.tgt[' + i + '].nm=this.value">', ogsN(t.ls, 0), ogsN(q.X[0] + offX, 0) + ' / ' + ogsN(q.X[1] + offY, 0) + ' / ' + ogsN(t.z, 0), ogsN(q.cx + offX, 0) + ' / ' + ogsN(q.cy + offY, 0) + ' / ' + ogsN(q.col, 0), ogsAzTxt(q.az) + ' / ' + ogsN(+P.dipB, 1) + '°', '±' + ogsN(q.len, 0) + ' m', '<input type=text value="' + ogsE(t.ket || '') + '" onchange="OGS.p.tgt[' + i + '].ket=this.value">', '<button class=x onclick="OGS.p.tgt.splice(' + i + ',1);ogsRender()">&times;</button>']; });
  return '<h3 class=ogsh>Target bor</h3><div class=hint>Target di bidang acuan (posisi tegak lurus = median sampel ≥ cut-off di sekitarnya). Lubang dibor dari sisi ' + ogsArah(F.fr.ddir) + ' (azimuth ' + ogsAzTxt((F.fr.ddir + 180) % 360) + ') menembus vein; collar = collar tertinggi ±25 m sepanjang strike (dari lantai pit lebih pendek). Usulan: di bawah intercept eksplorasi GT tertinggi yang berada di bawah dasar GC, dan celah data terbesar.</div>' +
    '<div class="g6 f"><div><label>Dip lubang (°)</label>' + ogsNum('dipB', P.dipB) + '</div><div><label>&nbsp;</label><button onclick="ogsTgtUsul()">&#9881; Usulkan target</button></div><div><label>&nbsp;</label><button class="' + (d ? 'btn-pri' : '') + '" onclick="OGS.ig=OGS.ig&&OGS.ig.key===\'tgt\'?null:{key:\'tgt\',typ:\'tgt\',pts:[]};ogsRender()">' + (d ? '&#9679; Klik di long section…' : '&#9998; Klik target di long section') + '</button></div></div>' +
    ogsFig('ogsTL', 400, 'target_bor') + ogsCsvBtn('ogsTT', 'target_bor') + ogsTab(['Target', 'Sepanjang strike', 'Target E / N / RL', 'Collar E / N / RL', 'Azimuth / dip', 'Panjang', 'Keterangan', ''], rows, [], 'ogsTT');
}
function ogsDrTgt() {
  var F = OGS.F, gd = $('ogsTL'); if (!F || !gd) return; var R = OGS._st || ogsStruk(), I = F.I.filter(function (c) { return isFinite(c.gt); }).sort(function (a, b) { return a.gt - b.gt; });
  var T = [{ type: 'scattergl', mode: 'markers', x: I.map(function (c) { return c.ls; }), y: I.map(function (c) { return c.p[2]; }), text: I.map(function (c) { return c.h + ' GT ' + ogsAuto(c.gt); }), marker: { size: I.map(function (c) { return Math.max(4, Math.min(16, 3 + 1.8 * c.gt)); }), color: I.map(function (c) { return ogsEks(c.h) ? '#c2540a' : '#1f2d6b'; }), opacity: 0.8 }, name: 'intercept (oranye = eksplorasi)' },
    { type: 'scatter', mode: 'lines', x: R.dasar.map(function (o) { return o.x; }), y: R.dasar.map(function (o) { return o.v; }), line: { color: '#1971c2', width: 2 }, name: 'dasar lubang GC' },
    { type: 'scatter', mode: 'lines', x: R.topo.map(function (o) { return o.x; }), y: R.topo.map(function (o) { return o.v; }), line: { color: '#8c4b3a', width: 1.4 }, name: 'collar tertinggi' },
    { type: 'scatter', mode: 'markers+text', x: OGS.p.tgt.map(function (t) { return t.ls; }), y: OGS.p.tgt.map(function (t) { return t.z; }), text: OGS.p.tgt.map(function (t) { return t.nm.split(' ')[0]; }), textposition: 'top center', marker: { size: 14, symbol: 'star', color: '#e03131', line: { width: 1, color: '#000' } }, name: 'target' }];
  OGS.p.tgt.forEach(function (t) { var q = ogsTgtHit(t), u = ogsLsOf([q.cx, q.cy, q.col])[0]; T.push({ type: 'scatter', mode: 'lines', x: [u, t.ls], y: [q.col, t.z], line: { color: '#e03131', width: 1, dash: 'dot' }, hoverinfo: 'skip', showlegend: false }); });
  Plotly.newPlot(gd, T, ogsLay({ title: { text: 'Target bor pada long section (proyeksi lubang usulan putus-putus)', font: { size: 11 } }, showlegend: true, legend: { orientation: 'h', y: -0.2, font: { size: 9 } }, xaxis: { title: 'jarak sepanjang strike (m) → ' + ogsArah(F.fr.az) }, yaxis: { title: 'RL (m)' }, margin: { l: 56, r: 10, t: 30, b: 80 } }), OGS_CFG);
  if (!gd._tg) { gd._tg = 1; gd.addEventListener('click', function (e) { var d = OGS.ig; if (!d || d.key !== 'tgt') return; var xa = gd._fullLayout.xaxis, ya = gd._fullLayout.yaxis, r = gd.getBoundingClientRect(), x = xa.p2l(e.clientX - r.left - xa._offset), y = ya.p2l(e.clientY - r.top - ya._offset);
    OGS.ig = null; var nm = prompt('Nama target:', 'T' + (OGS.p.tgt.length + 1)); if (!nm) { ogsRender(); return; } OGS.p.tgt.push({ nm: nm, ls: Math.round(x), z: Math.round(y), ket: '' }); ogsRender(); }); }
}

/* ================= 13. sampel >= cut di luar wireframe ================= */
function ogsLuar() { var F = OGS.F, P = OGS.p, cut = +P.cutS || 0.5, au = ogsEi(ogsAu()), cs = 5, Hh = {}, zmin = {}, lsR = [1e9, -1e9];
  F.dom.forEach(function (d) { var m = d.m; for (var i = 0; i < m.nv; i++) { var x = m._x[i], y = m._y[i], z = m._z[i], k = Math.floor(x / cs) + ',' + Math.floor(y / cs) + ',' + Math.floor(z / cs); (Hh[k] = Hh[k] || []).push(i, d); var q = ogsLsOf([x, y, z]); if (Math.abs(q[1]) <= 40) { var b = Math.floor(q[0] / 25); if (zmin[b] == null || z < zmin[b]) zmin[b] = z; } } });
  F.I.forEach(function (c) { if (c.ls < lsR[0]) lsR[0] = c.ls; if (c.ls > lsR[1]) lsR[1] = c.ls; });
  var dist = function (i) { var gx = Math.floor(F.X[i] / cs), gy = Math.floor(F.Y[i] / cs), gz = Math.floor(F.Z[i] / cs), dm = 1e9; for (var a = -2; a <= 2; a++) for (var b = -2; b <= 2; b++) for (var c = -2; c <= 2; c++) { var L = Hh[(gx + a) + ',' + (gy + b) + ',' + (gz + c)]; if (!L) continue; for (var j = 0; j < L.length; j += 2) { var m = L[j + 1].m, v = L[j], d = Math.hypot(F.X[i] - m._x[v], F.Y[i] - m._y[v], F.Z[i] - m._z[v]); if (d < dm) dm = d; } } return dm; };
  var K = ['Dekat wireframe (≤ 10 m)', 'Di bawah dasar wireframe', 'Lanjutan strike', 'Koridor vein, > 10 m dari wireframe', 'Struktur lain (> 60 m dari bidang)'], O = K.map(function () { return []; });
  for (var i = 0; i < F.n; i++) { if (F.D[i] >= 0 || !(F.V[au][i] >= cut)) continue; var w = Math.abs(F.Wd[i]), ls = F.LS[i], k;
    if (dist(i) <= 10) k = 0; else if (w > 60) k = 4; else if (ls < lsR[0] - 10 || ls > lsR[1] + 10) k = 2; else { var zb = zmin[Math.floor(ls / 25)]; k = zb != null && F.Z[i] < zb && w <= 40 ? 1 : 3; } O[k].push(i); }
  return K.map(function (nm, k) { var L = O[k], hs = {}; L.forEach(function (i) { hs[F.A[i][0]] = (hs[F.A[i][0]] || 0) + 1; }); return { nm: nm, L: L, nh: Object.keys(hs).length, au: ogsWmean(F, au, L), eks: L.filter(function (i) { return ogsEks(F.A[i][0]); }).length, ex: Object.keys(hs).sort(function (a, b) { return hs[b] - hs[a]; }).slice(0, 4).join(', ') }; }); }
function ogsPgLuar() {
  var F = OGS.F; if (!F) return '<h3 class=ogsh>Sampel di luar wireframe</h3>' + ogsNeed(); var R = ogsLuar(); OGS._lu = R; var cut = +OGS.p.cutS || 0.5, tot = R.reduce(function (s, r) { return s + r.L.length; }, 0);
  return '<h3 class=ogsh>Sampel ' + ogsE(ogsAu()) + ' ≥ ' + ogsAuto(cut) + ' di luar wireframe domain</h3><div class=hint>' + ogsN(tot) + ' sampel. Jarak ke wireframe = jarak ke verteks wireframe terdekat. "Di bawah dasar" = lebih dalam dari verteks wireframe terendah di segmen strike yang sama (±40 m dari bidang). "Lanjutan strike" = di luar rentang strike intercept. Kandidat revisi wireframe atau struktur baru.</div>' +
    '<div class=ogs2 style="grid-template-columns:1.25fr 1fr"><div>' + ogsCsvBtn('ogsTLu', 'di_luar_wireframe') + ogsTab(['Kategori', 'Sampel', 'Lubang', ogsE(ogsAu()) + ' rata-rata', 'Eksplorasi', 'Contoh lubang'], R.map(function (r) { return [r.nm, ogsN(r.L.length), ogsN(r.nh), ogsAuto(r.au), ogsN(r.eks), ogsE(r.ex)]; }), [], 'ogsTLu') + '</div><div>' + ogsFig('ogsLU', 420, 'di_luar_wireframe') + '</div></div>';
}
function ogsDrLuar() { var F = OGS.F, R = OGS._lu; if (!F || !R || !$('ogsLU')) return; var cl = ['#e8590c', '#7048e8', '#2f9e44', '#1971c2', '#868e96'], T = [{ type: 'scattergl', mode: 'markers', x: F.I.map(function (c) { return c.p[0] + offX; }), y: F.I.map(function (c) { return c.p[1] + offY; }), marker: { size: 3, color: '#dee2e6' }, name: 'intercept vein', hoverinfo: 'skip' }];
  R.forEach(function (r, k) { if (r.L.length) T.push({ type: 'scattergl', mode: 'markers', x: r.L.map(function (i) { return F.X[i] + offX; }), y: r.L.map(function (i) { return F.Y[i] + offY; }), text: r.L.map(function (i) { return F.A[i][0] + ' RL ' + ogsN(F.Z[i], 0); }), marker: { size: 5, color: cl[k] }, name: r.nm }); });
  Plotly.newPlot('ogsLU', T, ogsLay({ title: { text: 'Peta sampel ≥ cut-off di luar wireframe', font: { size: 11 } }, showlegend: true, legend: { orientation: 'h', y: -0.15, font: { size: 9 } }, xaxis: { tickformat: 'd', tickfont: { size: 8 } }, yaxis: { tickformat: 'd', tickfont: { size: 8 }, scaleanchor: 'x' }, margin: { l: 50, r: 6, t: 26, b: 70 } }), OGS_CFG); }

/* ================= 14. laporan PDF (template deck) ================= */
function ogsLapDef() { var F = OGS.F, L = [['cover', 'Sampul', ''], ['ring', 'Ringkasan', ''], ['data', 'Data dan domain', ''], ['geo', 'Geometri', ''], ['kadar', 'Kadar dan multi-elemen', ''], ['ls', 'Long section', ''], ['env', 'Envelope RBF GT', ''], ['zon', 'Zonasi vertikal', '']];
  if (F) F.dom.forEach(function (d, q) { if (d.nI >= 10) L.push(['prof:' + q, 'Profil vertikal · ' + d.nm, '']); }); (OGS.p.sec || []).forEach(function (s, i) { L.push(['sec:' + i, 'Penampang ' + s.nm, '']); });
  L.push(['struk', 'Struktur bawah permukaan', ''], ['par', 'Struktur paralel & tekukan', ''], ['jun', 'Pertemuan vein', ''], ['tgt', 'Target bor', ''], ['luar', 'Di luar wireframe', ''], ['rek', 'Rekomendasi', '']); return L; }
function ogsLapAuto(k) { var F = OGS.F; if (!F) return ''; var au = ogsAu(), d = F.dom[F.ref] || F.dom[0];
  try { if (k === 'data') return ogsN(ogsIn(F).length) + ' sampel vein dari ' + ogsN(F.I.length) + ' intercept';
    if (k === 'geo') return (d ? d.nm + ' strike ' + ogsAzTxt(d.pl.strike) + ', dip ' + ogsN(d.pl.dip, 0) + '° ke ' + ogsArah(d.pl.ddir) : '') + '; tebal median ' + ogsN(ogsMed(F.I.map(function (c) { return c.T; })), 1) + ' m';
    if (k === 'kadar') { var e = ogsEi(au), a = ogsMed(ogsVals(F, e, ogsIn(F))), b = ogsMed(ogsVals(F, e, ogsOut(F))); return 'Kontras ' + au + ' ' + ogsN(a / b, 0) + '× terhadap batuan samping'; }
    if (k === 'jun' && F.dom.length > 1) { var J = ogsJun(); return 'Di pertemuan ≥ 2 vein (' + J.sm.n + ' zona): GT ' + ogsN(J.sm.gt / J.ss.gt, 1) + '× dan ' + au + ' ' + ogsN(J.sm.au / J.ss.au, 1) + '× zona 1 vein'; } } catch (e) {} return ''; }
function ogsPgLap() {
  var F = OGS.F; if (!F) return '<h3 class=ogsh>Laporan PDF</h3>' + ogsNeed(); var P = OGS.p, Lp = P.lap; Lp.cov = Lp.cov || { k: 'MEETING INTERNAL GEOLOGY TEAM · ' + new Date().toLocaleDateString('id-ID', { day: 'numeric', month: 'long', year: 'numeric' }).toUpperCase(), j: 'Geometri Bijih Vein: bentuk, ketebalan, zonasi multi-elemen dan target lanjutan', s: '', foot: 'GC-Ex · Ore Geometry' }; Lp.s = Lp.s || {}; var D = ogsLapDef();
  var rows = D.map(function (x) { var s = Lp.s[x[0]] || (Lp.s[x[0]] = { on: true, h: '', t: '' }); return '<tr><td><input type=checkbox ' + (s.on ? 'checked' : '') + ' onchange="OGS.p.lap.s[\'' + x[0] + '\'].on=this.checked"></td><td>' + ogsE(x[1]) + '</td><td>' + (x[0] === 'cover' ? '<i>lihat isian sampul</i>' : '<input type=text style="width:100%" value="' + ogsE(s.h) + '" placeholder="' + ogsE(ogsLapAuto(x[0]) || 'judul kalimat (ditulis geologist)') + '" onchange="OGS.p.lap.s[\'' + x[0] + '\'].h=this.value">') + '</td><td>' + (x[0] === 'cover' ? '' : '<textarea rows=1 style="width:100%" placeholder="catatan / poin (satu per baris)" onchange="OGS.p.lap.s[\'' + x[0] + '\'].t=this.value">' + ogsE(s.t) + '</textarea>') + '</td></tr>'; }).join('');
  return '<h3 class=ogsh>Laporan PDF (template deck)</h3><div class=hint>Template sama dengan deck Ore Geometry (navy / emas, Inter, 13,333 × 7,5 in). Grafik dan tabel diambil dari halaman Studio dengan parameter saat ini. <b>Judul kalimat dan catatan ditulis geologist</b>; teks abu-abu hanya usulan angka (dipakai bila kolom dikosongkan). Garis interpretasi yang belum diterima tidak dicetak.</div>' +
    '<div class="g6 f"><div style="grid-column:span 2"><label>Label sampul</label><input type=text value="' + ogsE(Lp.cov.k) + '" onchange="OGS.p.lap.cov.k=this.value"></div><div style="grid-column:span 4"><label>Judul</label><input type=text value="' + ogsE(Lp.cov.j) + '" onchange="OGS.p.lap.cov.j=this.value"></div></div>' +
    '<div class="g6 f"><div style="grid-column:span 4"><label>Subjudul / sumber data</label><input type=text value="' + ogsE(Lp.cov.s) + '" placeholder="mis. Data GC 261109 + lubang eksplorasi PDH" onchange="OGS.p.lap.cov.s=this.value"></div><div style="grid-column:span 2"><label>Kaki halaman</label><input type=text value="' + ogsE(Lp.cov.foot) + '" onchange="OGS.p.lap.cov.foot=this.value"></div></div>' +
    '<table class=ogst><tr><th>Cetak</th><th>Slide</th><th>Judul kalimat</th><th>Catatan</th></tr>' + rows + '</table>' +
    '<div class="g2 f" style="margin-top:8px"><button class=btn-pri onclick="ogsLapBuat(\'pdf\')">&#128438; Buat laporan &amp; cetak ke PDF</button><button onclick="ogsLapBuat(\'html\')">&#8681; Simpan laporan (HTML)</button></div><div id=ogsLapMsg class=hint></div>';
}
var OGS_LAPCSS = '@page{size:13.333in 7.5in;margin:0}*{box-sizing:border-box}body{margin:0;font-family:"Inter","Segoe UI",Arial,sans-serif;color:#1d2433}' +
  '.s{width:13.333in;height:7.5in;padding:.5in .7in .45in;position:relative;page-break-after:always;overflow:hidden;background:#fff}.s:last-child{page-break-after:auto}' +
  'h1{font-size:30px;margin:0 0 8px;color:#1f2d6b;line-height:1.15}h2{font-size:14px;margin:0 0 6px;color:#8a6d00;font-weight:600;letter-spacing:.3px;text-transform:uppercase}' +
  '.foot{position:absolute;left:.7in;right:.7in;bottom:.22in;font-size:10.5px;color:#7b8394;display:flex;justify-content:space-between;border-top:1px solid #e3e6ec;padding-top:6px}.bar{position:absolute;left:0;top:0;width:.18in;height:100%;background:#1f2d6b}' +
  '.cover{background:#1f2d6b;color:#fff}.cover h1{color:#fff;font-size:42px}.cover .lead{font-size:19px;color:#dfe4f2;max-width:9.5in}.cover .amber{height:6px;width:2.2in;background:#f2c200;margin:22px 0}' +
  'table{border-collapse:collapse;width:100%;font-size:12.5px}th{background:#1f2d6b;color:#fff;text-align:left;padding:5px 7px;font-weight:600}td{padding:5px 7px;border-bottom:1px solid #e3e6ec}tr.hl td{background:#fff5d6;font-weight:700}' +
  '.grid{display:flex;gap:16px;align-items:flex-start}.grid>div{flex:1;min-width:0}img{max-width:100%;display:block;margin:0 auto}.cap{font-size:13px;color:#5b6478;margin:6px 0 0}ul{margin:6px 0 0;padding-left:20px}li{font-size:15px;line-height:1.45}' +
  '.cards{display:grid;grid-template-columns:repeat(4,1fr);gap:14px}.card{border:1px solid #e3e6ec;border-radius:10px;padding:12px 14px;background:#fafbfd}.big{font-size:32px;font-weight:800;color:#1f2d6b;line-height:1}.sub{font-size:13px;color:#5b6478;margin-top:6px}' +
  '.tsm td,.tsm th{padding:1px 5px;font-size:9.5px;line-height:1.25}.key{border-left:6px solid #f2c200;background:#fffbe6;padding:8px 12px;border-radius:6px;font-size:15px;margin-top:10px}';
function ogsLapAmbil(nav, setup) { return new Promise(function (ok) { try { if (setup) setup(); } catch (e) {} ogsGo(nav);
  setTimeout(async function () { var c = $('ogsC'), F = [], T = []; var G = c.querySelectorAll('.ogsfig > div[id]');
    for (var i = 0; i < G.length; i++) { var g = G[i]; if (!g.data) continue; try { F.push({ id: g.id, src: await Plotly.toImage(g, { format: 'png', width: Math.max(900, g.offsetWidth), height: Math.max(380, g.offsetHeight), scale: 2 }), w: g.offsetWidth, h: g.offsetHeight }); } catch (e) { console.error(e); } }
    c.querySelectorAll('table.ogst[id]').forEach(function (t) { var x = t.cloneNode(true); x.querySelectorAll('input,select,button,textarea').forEach(function (e) { var s = document.createElement('span'); s.textContent = e.type === 'checkbox' ? '' : (e.value || ''); e.replaceWith(s); }); T.push({ id: t.id, html: x.outerHTML }); });
    ok({ F: F, T: T }); }, nav === 'env' || nav === 'jun' || nav === 'par' ? 3200 : 1600); }); }
async function ogsLapBuat(fmt) {
  var F = OGS.F, P = OGS.p, Lp = P.lap, D = ogsLapDef(), msg = function (t) { var e = $('ogsLapMsg'); if (e) e.innerHTML = t; }, pg = 0, out = [], ft = Lp.cov.foot || 'GC-Ex · Ore Geometry', back = OGS.nav, secI = P.secI, pfD = P.pfDom, ig = OGS.ig; OGS.ig = null;
  var S = function (lab, h, isi, cat) { pg++; return '<section class=s><div class=bar></div><h2>' + ogsE(lab) + '</h2><h1>' + ogsE(h) + '</h1>' + isi + '<div class=foot><span>' + ogsE(ft) + (cat ? ' · ' + ogsE(cat) : '') + '</span><span>' + pg + '</span></div></section>'; };
  var poin = function (t) { var L = String(t || '').split(/\n+/).map(function (x) { return x.trim(); }).filter(Boolean); return L.length ? '<ul>' + L.map(function (x) { return '<li>' + ogsE(x) + '</li>'; }).join('') + '</ul>' : ''; };
  var img = function (f, h) { return f ? '<img src="' + f.src + '" style="max-height:' + h + 'in">' : ''; };
  var MAP = { data: ['data', 'Data dan domain'], geo: ['geo', 'Geometri'], kadar: ['kadar', 'Kadar dan multi-elemen'], ls: ['ls', 'Long section'], env: ['env', 'Envelope RBF grade × tebal'], zon: ['zon', 'Zonasi vertikal'], struk: ['struk', 'Struktur bawah permukaan'], par: ['par', 'Struktur paralel & tekukan'], jun: ['jun', 'Pertemuan vein'], tgt: ['tgt', 'Target bor'], luar: ['luar', 'Di luar wireframe'] };
  try {
    for (var i = 0; i < D.length; i++) { var k = D[i][0], s = Lp.s[k] || { on: true }; if (!s.on) continue; msg('Menyusun slide ' + (out.length + 1) + ': ' + ogsE(D[i][1]) + '…'); var h = s.h || ogsLapAuto(k) || D[i][1];
      if (k === 'cover') { pg++; out.push('<section class="s cover"><div style="margin-top:1in"><div style="font-size:15px;letter-spacing:2px;color:#f2c200;font-weight:700">' + ogsE(Lp.cov.k) + '</div><h1 style="margin-top:14px">' + ogsE(Lp.cov.j) + '</h1><div class=amber></div><p class=lead>' + ogsE(Lp.cov.s || (ogsN(Object.keys(holeData).length) + ' lubang, ' + ogsN(F.n) + ' interval assay; domain: ' + F.dom.map(function (d) { return d.nm; }).join(', '))) + '</p></div><div class=foot style="color:#b9c2dc;border-color:#3a4785"><span>' + ogsE(ft) + '</span><span>' + pg + '</span></div></section>'); continue; }
      if (k === 'ring') { var d = F.dom[F.ref], T = F.I.map(function (c) { return c.T; }), e = ogsEi(ogsAu()), V = ogsIn(F);
        out.push(S('Ringkasan', s.h || (d ? 'Vein ' + ogsArah(d.pl.strike) + '–' + ogsArah(d.pl.strike + 180) + ', dip ' + ogsN(d.pl.dip, 0) + '° ke ' + ogsArah(d.pl.ddir) : 'Ringkasan'), '<div class=cards><div class=card><div class=big>' + (d ? ogsAzTxt(d.pl.strike) : '–') + '</div><div class=sub>Strike bidang acuan; dip ' + (d ? ogsN(d.pl.dip, 0) + '° ke ' + ogsArah(d.pl.ddir) : '–') + '</div></div><div class=card><div class=big>' + F.dom.length + '</div><div class=sub>Domain, ' + ogsN(F.I.length) + ' intercept</div></div><div class=card><div class=big>' + ogsN(ogsMed(T), 1) + ' m</div><div class=sub>Tebal sebenarnya median (P10–P90 ' + ogsN(ogsQ(T, 0.1), 1) + '–' + ogsN(ogsQ(T, 0.9), 1) + ' m)</div></div><div class=card><div class=big>' + ogsAuto(ogsWmean(F, e, V)) + '</div><div class=sub>' + ogsE(ogsAu()) + ' rata-rata di vein (median ' + ogsAuto(ogsMed(ogsVals(F, e, V))) + ')</div></div></div>' + poin(s.t))); continue; }
      if (k === 'rek') { out.push(S('Rekomendasi', s.h || 'Rekomendasi untuk tim', poin(s.t) || '<p class=cap>(isi catatan rekomendasi di Studio › Laporan PDF)</p>')); continue; }
      if (/^prof:/.test(k)) { var q = +k.split(':')[1], R0 = await ogsLapAmbil('prof', function () { P.pfDom = String(q); }); out.push(S('Profil vertikal per domain', s.h || ('Profil ' + F.dom[q].nm), img(R0.F[0], 4.9) + poin(s.t))); continue; }
      if (/^sec:/.test(k)) { var j = +k.split(':')[1], R1 = await ogsLapAmbil('sec', function () { P.secI = j; }); out.push(S('Penampang ' + (P.sec[j] ? P.sec[j].nm + ' · ' + (P.sec[j].ls > 0 ? '+' : '') + ogsN(P.sec[j].ls, 0) + ' m' : ''), s.h || 'Penampang ' + (P.sec[j] || {}).nm, img(R1.F.filter(function (f) { return f.id === 'ogsSP'; })[0], 4.7) + poin(s.t))); continue; }
      var m = MAP[k]; if (!m) continue; var R = await ogsLapAmbil(m[0]), Tb = function (id) { var t = R.T.filter(function (x) { return x.id === id; })[0]; return t ? t.html : ''; }, Fi = function (id) { return R.F.filter(function (f) { return f.id === id; })[0]; }, isi = '';
      if (k === 'data') isi = '<div class=grid><div style="flex:.9">' + img(Fi('ogsMap'), 5) + '</div><div>' + Tb('ogsTD') + poin(s.t) + '</div></div>';
      else if (k === 'geo') isi = Tb('ogsTG') + '<div class=grid style="margin-top:8px"><div>' + img(Fi('ogsTh'), 2.4) + '</div><div>' + img(Fi('ogsTl'), 2.4) + '</div></div>' + poin(s.t);
      else if (k === 'kadar') isi = '<div class=grid><div>' + Tb('ogsTK') + '<div style="height:8px"></div>' + Tb('ogsTKD') + '</div><div style="flex:.8">' + poin(s.t) + '</div></div>';
      else if (k === 'env') isi = img(Fi('ogsEnv'), 3.4) + '<div style="height:6px"></div>' + Tb('ogsTE') + poin(s.t);
      else if (k === 'struk') isi = '<div class=grid><div style="flex:1.5">' + img(Fi('ogsST'), 4.4) + poin(s.t) + '</div><div>' + Tb('ogsTS').replace('<table', '<table class=tsm') + '</div></div>';
      else if (k === 'par') isi = '<div class=grid><div style="flex:1.3">' + img(Fi('ogsPB'), 4.3) + poin(s.t) + '</div><div>' + Tb('ogsTP').replace('<table', '<table class=tsm') + '</div></div>';
      else if (k === 'jun') isi = img(Fi('ogsJB'), 2.6) + '<div class=grid style="margin-top:6px"><div>' + Tb('ogsTJ') + '</div><div>' + img(Fi('ogsJM'), 2.3) + '</div></div>' + poin(s.t);
      else if (k === 'tgt') isi = img(Fi('ogsTL'), 3.2) + Tb('ogsTT') + poin(s.t);
      else if (k === 'luar') isi = '<div class=grid><div>' + Tb('ogsTLu') + poin(s.t) + '</div><div>' + img(Fi('ogsLU'), 4.6) + '</div></div>';
      else isi = (R.F.map(function (f) { return img(f, 4.9 / Math.max(1, R.F.length)); }).join('')) + poin(s.t);
      out.push(S(m[1], h, isi)); }
  } catch (e) { console.error(e); msg('<span class=warn>Gagal: ' + ogsE(e.message) + '</span>'); }
  P.secI = secI; P.pfDom = pfD; OGS.ig = ig; ogsGo('lap');
  var html = '<!DOCTYPE html><html lang=id><head><meta charset=utf-8><title>' + ogsE(Lp.cov.j) + '</title><style>' + OGS_LAPCSS + '</style></he' + 'ad><bo' + 'dy>' + out.join('\n') + '</bo' + 'dy></ht' + 'ml>';
  OGS._lapHtml = html; var nm = 'OreGeometry_Laporan_' + new Date().toISOString().slice(0, 10);
  if (fmt === 'html') { gxDl(new Blob([html], { type: 'text/html' }), nm + '.html'); setTimeout(function () { var e = $('ogsLapMsg'); if (e) e.innerHTML = '&#10003; ' + pg + ' slide disimpan sebagai HTML (buka di browser, Cetak → Simpan sebagai PDF, ukuran 13,333 × 7,5 in).'; }, 200); return pg; }
  var fr = $('ogsLapFr'); if (fr) fr.remove(); fr = document.createElement('iframe'); fr.id = 'ogsLapFr'; fr.style.cssText = 'position:fixed;right:0;bottom:0;width:13.333in;height:7.5in;border:0;opacity:0;pointer-events:none;z-index:-1'; document.body.appendChild(fr);
  fr.srcdoc = html; fr.onload = function () { setTimeout(function () { var e = $('ogsLapMsg'); if (e) e.innerHTML = '&#10003; ' + pg + ' slide. Di dialog cetak pilih <b>Simpan sebagai PDF</b> / <b>Microsoft Print to PDF</b>; ukuran halaman sudah 13,333 × 7,5 in, margin 0, centang <b>Grafik latar belakang</b>.'; if (!OGS.noPrint) try { fr.contentWindow.focus(); fr.contentWindow.print(); } catch (x) { console.error(x); } }, 400); };
  return pg;
}

/* ---------- daftarkan halaman ---------- */
Object.assign(OGS_PG, { struk: ogsPgStruk, par: ogsPgPar, jun: ogsPgJun, tgt: ogsPgTgt, luar: ogsPgLuar, lap: ogsPgLap });
Object.assign(OGS_DR, { struk: ogsDrStruk, par: ogsDrPar, jun: ogsDrJun, tgt: ogsDrTgt, luar: ogsDrLuar });
/* garis interpretasi di penampang (semua panel) */
(function () { var _p = ogsPgSec, _d = ogsDrSec;
  OGS_PG.sec = ogsPgSec = function () { var h = _p.apply(this, arguments); if (!OGS.F || !OGS.p.sec.length) return h; return h.replace('<div class=ogs2 style="grid-template-columns:1fr 3.2fr">', ogsIgHtml('sec', 'klik di panel mana saja; garis tampil di semua panel') + '<div class=ogs2 style="grid-template-columns:1fr 3.2fr">'); };
  OGS_DR.sec = ogsDrSec = function () { var r = _d.apply(this, arguments); var gd = $('ogsSP'); if (gd && gd.data) { var T = [], Lay = {}, ax = Object.keys(gd._fullLayout).filter(function (k) { return /^xaxis\d*$/.test(k); }).map(function (k) { return k.slice(5); }).sort(); ogsIgApply('sec', T, Lay, ax); if (T.length || Lay.shapes.length) { Plotly.relayout(gd, { shapes: Lay.shapes, annotations: (gd.layout.annotations || []).concat(Lay.annotations) }); if (T.length) Plotly.addTraces(gd, T); } ogsIgBind('ogsSP', 'sec'); } return r; }; })();
(function () { var st = document.createElement('style'); st.textContent = '.ogsig{border:1px dashed #b9c2dc;border-radius:8px;padding:6px 8px;margin:6px 0;background:rgba(31,45,107,.03)}.ogsig button{font-size:11.5px;margin:2px 2px 0 0}.ogsig+table.ogst input[type=text]{width:100%}.ogsc .tag{display:inline-block;background:#fff5d6;color:#8a6d00;border-radius:4px;padding:0 6px;font-size:10.5px;font-weight:700}'; document.head.appendChild(st); })();
