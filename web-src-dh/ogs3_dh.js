/* ================= ORE GEOMETRY STUDIO — 15 · PETA LEVEL (GC-Ex Drillhole 0.24.77) =================
   Pemilik 12 Nov 2026: sayatan horizontal di satu RL dijadikan peta bergaya peta eksplorasi (contoh: peta anomali Au
   dengan lode, struktur, lubang, legenda di dalam peta). Keputusan:
   - kadar: interpolasi mode ANOMALI (bawaan; IDW anisotropi searah strike bidang acuan) atau DI DALAM DOMAIN saja;
   - tebal irisan bawaan +-5 m; kelas Au bawaan 0,4 / 0,5 / 1 / 3;
   - alterasi = kategori dominan (indikator IDW) sebagai ARSIR di atas warna kadar;
   - wireframe domain dipotong otomatis di RL: GARIS TENGAH (bawaan, tebal garis bisa diatur) atau dinding;
     tiap domain bisa dinyalakan / dimatikan;
   - kontur: impor string kontur (.str / .dxf); kontur dari collar hanya cadangan (collar = lantai pit saat bor);
   - label domain & Hole ID bisa digeser dengan mouse (posisi disimpan);
   - legenda, judul, panah utara dan skala DI DALAM peta (seperti contoh);
   - garis interpretasi geologist (struktur, lode baru) dengan nama sejajar garis; ekspor .str pada RL itu.
   Gambaran visual, bukan estimasi. */
(function () { var D = { rl: null, hs: 5, mode: 'anom', rat: 4, rAlong: 40, mask: 25, res: 1.5, cls: [0.4, 0.5, 1, 3], alt: true, altCi: -1, altMin: 0.5, wfOff: {}, wfMode: 'tengah', wfW: 2.5, lub: true, lubLab: true, kont: 'auto', kInt: 5, kstr: null, step: 5, lab: {}, lapRL: '', pos: {}, lay: {} };
  OGS.p.pt = Object.assign(D, OGS.p.pt || {}); })();
OGS_NAV.splice(OGS_NAV.findIndex(function (x) { return x[0] === 'luar'; }) + 1, 0, ['peta', '15 · Peta level']);
var OGS_KCOL = ['#4c5bd4', '#fde24f', '#f4a142', '#e8352a', '#e540e0'];
var OGS_HAT = [['/', 'garis miring'], ['x', 'silang'], ['.', 'titik'], ['\\', 'garis miring balik'], ['+', 'plus'], ['-', 'datar'], ['|', 'tegak']];
var OGS_LAY = [['kadar', 'Kadar'], ['alt', 'Arsir alterasi'], ['wf', 'Wireframe'], ['wfLab', 'Label domain'], ['lub', 'Lubang'], ['lubLab', 'Hole ID'], ['kont', 'Kontur'], ['ig', 'Garis interpretasi'], ['judul', 'Judul'], ['utara', 'Panah utara & skala'], ['legenda', 'Legenda'], ['grid', 'Grid koordinat']];
function ogsLy(k) { var L = OGS.p.pt.lay || (OGS.p.pt.lay = {}); if (k === 'lub') return OGS.p.pt.lub !== false && L.lub !== false; if (k === 'lubLab') return OGS.p.pt.lubLab !== false && L.lubLab !== false; return L[k] !== false; }
function ogsPt() { var P = OGS.p.pt; if (!P.kstr && OGS._kstr) P.kstr = OGS._kstr; return P; }
function ogsPtRL() { var F = OGS.F, P = ogsPt(); if (P.rl == null || !isFinite(P.rl)) { var z = ogsIn(F).map(function (i) { return F.Z[i]; }); P.rl = Math.round(ogsMed(z) / 5) * 5; } return +P.rl; }
function ogsAltCi() { var P = ogsPt(), G = ogsGeoCols(); if (P.altCi >= 0 && CAT[P.altCi]) return P.altCi; var a = G.filter(function (o) { return /alt/i.test(o.c.name); })[0]; P.altCi = a ? a.ci : -2; return P.altCi; }

/* ---------- hitung peta ---------- */
function ogsPeta() {
  var F = OGS.F, P = ogsPt(), RL = ogsPtRL(), hs = Math.max(0.5, +P.hs || 5), au = ogsEi(ogsAu()), cls = P.cls.map(Number), fr = F.fr;
  var nh = [fr.n[0], fr.n[1]], hn = Math.hypot(nh[0], nh[1]) || 1; nh = [nh[0] / hn, nh[1] / hn];
  var rat = Math.max(1, +P.rat || 4), R = Math.max(5, +P.rAlong || 40), M = Math.max(1, +P.mask || 25);
  var rot = function (x, y) { return [x * fr.sv[0] + y * fr.sv[1], (x * nh[0] + y * nh[1]) * rat]; };
  var I = []; for (var i = 0; i < F.n; i++) if (Math.abs(F.Z[i] - RL) <= hs && isFinite(F.V[au][i])) I.push(i);
  if (!I.length) return { kosong: true, RL: RL, hs: hs };
  var O = I.filter(function (i) { return F.V[au][i] >= cls[0] && Math.abs(F.Wd[i]) <= 60; }); if (O.length < 5) O = I;
  var xs = O.map(function (i) { return F.X[i]; }), ys = O.map(function (i) { return F.Y[i]; }), mg = 60;
  var x0 = ogsQ(xs, 0.005) - mg, x1 = ogsQ(xs, 0.995) + mg, y0 = ogsQ(ys, 0.005) - mg, y1 = ogsQ(ys, 0.995) + mg, res = Math.max(0.5, +P.res || 1.5);
  while (((x1 - x0) / res) * ((y1 - y0) / res) > 250000) res *= 1.25;
  var nx = Math.ceil((x1 - x0) / res) + 1, ny = Math.ceil((y1 - y0) / res) + 1, gx = [], gy = []; for (var a = 0; a < nx; a++) gx.push(x0 + a * res); for (var b = 0; b < ny; b++) gy.push(y0 + b * res);
  /* hash sampel di ruang anisotropi */
  var A = I.map(function (i) { return rot(F.X[i], F.Y[i]); }), Hh = {}; A.forEach(function (p, k) { var key = Math.floor(p[0] / R) + ',' + Math.floor(p[1] / R); (Hh[key] = Hh[key] || []).push(k); });
  var cap = ogsQ(I.map(function (i) { return F.V[au][i]; }), 0.995), ci = P.alt ? ogsAltCi() : -2, AC = [], cats = [];
  if (ci >= 0) { I.forEach(function (i) { var a2 = F.A[i], c = catAssay(ci, a2[0], a2); AC.push(c); }); var cnt = {}; AC.forEach(function (c) { if (c >= 0) cnt[c] = (cnt[c] || 0) + 1; }); cats = Object.keys(cnt).map(Number).filter(function (c) { return cnt[c] >= 20; }).sort(function (p, q) { return cnt[q] - cnt[p]; }).slice(0, OGS_HAT.length); }
  var inDom = null; if (P.mode === 'dom') { var Wm = F.dom.map(function (d) { return P.wfOff[d.k] ? null : d.m._ogsW; }); inDom = function (x, y) { for (var q = 0; q < Wm.length; q++) if (Wm[q] && Wm[q].f(x, y, RL)) return true; return false; }; }
  var Z = [], K = [], AL = [], kk = 16, bd = new Float64Array(kk), bi = new Int32Array(kk);
  for (b = 0; b < ny; b++) { var rz = [], rk = [], ra = []; for (a = 0; a < nx; a++) { var p = rot(gx[a], gy[b]), cx = Math.floor(p[0] / R), cy = Math.floor(p[1] / R), n = 0, dmin = 1e9;
      for (var u = -1; u <= 1; u++) for (var v = -1; v <= 1; v++) { var L = Hh[(cx + u) + ',' + (cy + v)]; if (!L) continue;
        for (var j = 0; j < L.length; j++) { var q2 = A[L[j]], d = Math.hypot(p[0] - q2[0], p[1] - q2[1]); if (d > R) continue; if (d < dmin) dmin = d;
          if (n < kk) { bd[n] = d; bi[n] = L[j]; n++; } else { var w = 0; for (var t = 1; t < kk; t++) if (bd[t] > bd[w]) w = t; if (d < bd[w]) { bd[w] = d; bi[w] = L[j]; } } } }
      if (!n || dmin > M || (inDom && !inDom(gx[a], gy[b]))) { rz.push(null); rk.push(null); ra.push(null); continue; }
      var sw = 0, sv = 0, sc = {}; for (t = 0; t < n; t++) { var ww = 1 / Math.pow(Math.max(bd[t], 1), 2), val = Math.min(cap, F.V[au][I[bi[t]]]); sw += ww; sv += ww * val; if (ci >= 0) { var c2 = AC[bi[t]]; if (c2 >= 0) sc[c2] = (sc[c2] || 0) + ww; } }
      var g = sv / sw, k2 = 0; while (k2 < cls.length && g >= cls[k2]) k2++; rz.push(g); rk.push(k2);
      var best = -1, bw = 0; for (var c3 in sc) if (sc[c3] > bw) { bw = sc[c3]; best = +c3; } ra.push(best >= 0 && bw / sw >= (+P.altMin || 0.5) && cats.indexOf(best) >= 0 ? best : null); }
    Z.push(rz); K.push(rk); AL.push(ra); }
  /* potongan wireframe per domain */
  var WF = F.dom.map(function (d) { if (P.wfOff[d.k]) return null; var Ls = []; try { Ls = wfSlice(d.m, { n: [0, 0, 1], c: [0, 0, RL] }, 0); } catch (e) {} return { d: d, L: Ls.filter(function (l) { return l.p.length >= 3; }) }; }).filter(Boolean);
  WF.forEach(function (w) { w.mid = w.L.map(ogsMidline).filter(function (m) { return m.length >= 2; }); var all = []; w.L.forEach(function (l) { all = all.concat(l.p); }); w.c = all.length ? [ogsMed(all.map(function (q) { return q[0]; })), ogsMed(all.map(function (q) { return q[1]; }))] : null; });
  /* lubang yang menembus RL */
  var LB = []; Object.keys(holeData).forEach(function (h) { var hd = holeData[h], pp = hd.path.map(function (q) { return [q.x, q.y, q.z]; }), e = getXYZ(h, hd.maxD); pp.push([e.x, e.y, e.z]);
    var hit = null; for (var s = 0; s + 1 < pp.length; s++) { var p0 = pp[s], p1 = pp[s + 1]; if ((p0[2] - RL) * (p1[2] - RL) > 0 || p0[2] === p1[2]) continue; var f = (RL - p0[2]) / (p1[2] - p0[2]); hit = [p0[0] + f * (p1[0] - p0[0]), p0[1] + f * (p1[1] - p0[1]), 1]; break; }
    /* tidak menembus RL tetapi ujung lubang masuk irisan +-hs: tampil di ujung lubang (tanda kosong) */
    if (!hit) { var e2 = pp[pp.length - 1]; if (Math.abs(e2[2] - RL) <= hs) hit = [e2[0], e2[1], 0]; }
    if (!hit || hit[0] < x0 || hit[0] > x1 || hit[1] < y0 || hit[1] > y1) return; LB.push({ h: h, x: hit[0], y: hit[1], lewat: !!hit[2], eks: ogsEks(h), tr: pp }); });
  return { RL: RL, hs: hs, I: I, x0: x0, x1: x1, y0: y0, y1: y1, gx: gx, gy: gy, Z: Z, K: K, AL: AL, cats: cats, ci: ci, WF: WF, LB: LB, res: res };
}
/* garis tengah poligon vein tipis: pasangan titik terdekat antar dua sisi, dirata-rata sepanjang sumbu panjang */
function ogsMidline(l) { var p = l.p; if (p.length < 4) return p.map(function (q) { return [q[0], q[1]]; }); var mx = 0, my = 0; p.forEach(function (q) { mx += q[0]; my += q[1]; }); mx /= p.length; my /= p.length;
  var sxx = 0, syy = 0, sxy = 0; p.forEach(function (q) { var dx = q[0] - mx, dy = q[1] - my; sxx += dx * dx; syy += dy * dy; sxy += dx * dy; }); var th = 0.5 * Math.atan2(2 * sxy, sxx - syy), ax = [Math.cos(th), Math.sin(th)];
  var B = {}, st = 2; p.forEach(function (q) { var s = (q[0] - mx) * ax[0] + (q[1] - my) * ax[1], t = -(q[0] - mx) * ax[1] + (q[1] - my) * ax[0], k = Math.round(s / st); var b = B[k] || (B[k] = [1e9, -1e9, 0]); if (t < b[0]) b[0] = t; if (t > b[1]) b[1] = t; });
  return Object.keys(B).map(Number).sort(function (a, b) { return a - b; }).map(function (k) { var b = B[k], s = k * st, t = (b[0] + b[1]) / 2; return [mx + s * ax[0] - t * ax[1], my + s * ax[1] + t * ax[0]]; }); }
/* kontur: string impor (.str / .dxf) atau collar */
function ogsKontParse(txt, nm) { var L = [], cur = [];
  if (/\.dxf$/i.test(nm) || /^\s*0\s*[\r\n]+\s*SECTION/i.test(txt)) { var t = txt.split(/\r?\n/).map(function (s) { return s.trim(); }), i = 0, ent = '', el = 0, pt = null;
    var flush = function () { if (cur.length > 1) L.push(cur); cur = []; };
    for (; i + 1 < t.length; i += 2) { var c = t[i], v = t[i + 1];
      if (c === '0') { if (pt) { cur.push(pt); pt = null; } if (v === 'LWPOLYLINE' || v === 'POLYLINE' || v === 'LINE') { flush(); ent = v; el = 0; } else if (v === 'VERTEX') { } else if (v === 'SEQEND' || ent === 'LWPOLYLINE' || ent === 'LINE') { if (ent !== 'POLYLINE' || v === 'SEQEND') { flush(); ent = v === 'SEQEND' ? '' : ent === 'POLYLINE' ? ent : ''; } } continue; }
      if (!ent) continue; if (c === '38') el = +v; if (c === '10' || c === '11') { if (pt) cur.push(pt); pt = [+v, 0, el]; } if ((c === '20' || c === '21') && pt) pt[1] = +v; if ((c === '30' || c === '31') && pt) pt[2] = +v || el; }
    if (pt) cur.push(pt); flush(); }
  else { txt.split(/\r?\n/).slice(2).forEach(function (s) { var f = s.split(','); if (f.length < 4) return; var id = +f[0]; if (!id) { if (cur.length > 1) L.push(cur); cur = []; return; } var y = +f[1], x = +f[2], z = +f[3]; if (isFinite(x) && isFinite(y) && isFinite(z)) cur.push([x, y, z]); }); if (cur.length > 1) L.push(cur); }
  var n = 0; L = L.map(function (l) { return l.map(function (q) { n++; return [Math.round((q[0] - offX) * 10) / 10, Math.round((q[1] - offY) * 10) / 10, Math.round(q[2] * 10) / 10]; }); });
  return { nm: nm, L: L, n: n }; }
function ogsKontImp(inp) { var f = inp.files && inp.files[0]; if (!f) return; var r = new FileReader(); r.onload = function () { try { var K = ogsKontParse(String(r.result), f.name); if (!K.L.length) { alert('Tidak ada polyline di berkas ini.'); return; } if (K.n > 300000) { alert('Kontur terlalu rapat (' + K.n + ' titik). Sederhanakan dulu.'); return; } ogsPt().kstr = K; ogsPt().kont = 'auto'; ogsRender(); } catch (e) { alert('Gagal membaca: ' + e.message); } }; r.readAsText(f); }

/* ---------- halaman ---------- */
function ogsPgPeta() {
  var F = OGS.F; if (!F) return '<h3 class=ogsh>Peta level</h3>' + ogsNeed(); var P = ogsPt(), RL = ogsPtRL(), G = ogsGeoCols(), ks = P.kstr;
  var h = '<h3 class=ogsh>Peta level (sayatan horizontal)</h3><div class=hint>Irisan horizontal di satu RL dijadikan peta: interpolasi kadar, arsir alterasi, potongan wireframe domain, lubang yang menembus RL, kontur, garis interpretasi, legenda di dalam peta. Label domain dan Hole ID bisa <b>digeser dengan mouse</b>. Gambaran visual, bukan estimasi.</div>' +
    '<div class="g6 f"><div><label>RL (m)</label><span style="display:flex;gap:2px"><button onclick="ogsPtSet(\'rl\',' + (RL - (+P.step || 5)) + ')">&#9660;</button><input type=number step=any value="' + RL + '" onchange="ogsPtSet(\'rl\',+this.value)"><button onclick="ogsPtSet(\'rl\',' + (RL + (+P.step || 5)) + ')">&#9650;</button></span></div>' +
    '<div><label>Tebal irisan ± (m)</label><input type=number step=any value="' + P.hs + '" onchange="ogsPtSet(\'hs\',+this.value)"></div><div><label>Langkah ▲▼ (m)</label><input type=number step=any value="' + P.step + '" onchange="ogsPtSet(\'step\',+this.value)"></div>' +
    '<div><label>Mode kadar</label>' + ogsSel("ogsPtSet('mode',this.value)", [['anom', 'Anomali (interpolasi)'], ['dom', 'Di dalam domain saja']], P.mode) + '</div>' +
    '<div><label>Kelas ' + ogsE(ogsAu()) + ' (4 batas)</label><input type=text value="' + P.cls.join('; ') + '" onchange="ogsPtCls(this.value)"></div><div><label>Anisotropi strike : tegak lurus</label><input type=number step=any value="' + P.rat + '" onchange="ogsPtSet(\'rat\',+this.value)"></div></div>' +
    '<div class="g6 f"><div><label>Jangkauan searah strike (m)</label><input type=number step=any value="' + P.rAlong + '" onchange="ogsPtSet(\'rAlong\',+this.value)"></div><div><label>Batas warna dari data (m)</label><input type=number step=any value="' + P.mask + '" onchange="ogsPtSet(\'mask\',+this.value)"></div>' +
    '<div><label>Alterasi (arsir)</label>' + ogsSel("ogsPtSet('altCi',+this.value)", [[-2, '(tanpa)']].concat(G.map(function (o) { return [o.ci, o.c.name]; })), P.alt ? ogsAltCi() : -2) + '</div><div><label>Dominan min (%)</label><input type=number step=any value="' + Math.round(100 * P.altMin) + '" onchange="ogsPtSet(\'altMin\',this.value/100)"></div>' +
    '<div><label>Wireframe</label>' + ogsSel("ogsPtSet('wfMode',this.value)", [['tengah', 'Garis tengah'], ['dinding', 'Dinding (outline)']], P.wfMode) + '</div><div><label>Tebal garis wireframe (px)</label><input type=number step=0.5 value="' + P.wfW + '" onchange="ogsPtSet(\'wfW\',+this.value)"></div></div>' +
    '<div class=hint>Domain: ' + F.dom.map(function (d) { return '<label class=sw style="display:inline-flex;margin-right:8px"><input type=checkbox ' + (P.wfOff[d.k] ? '' : 'checked') + ' onchange="OGS.p.pt.wfOff[\'' + d.k + '\']=!this.checked;ogsRender()"><span style="color:' + d.col + '">&#9632;</span>&nbsp;' + ogsE(d.nm) + '</label>'; }).join('') +
    '</div><div class=hint><b>Lapisan:</b> ' + OGS_LAY.map(function (l) { return '<label class=sw style="display:inline-flex;margin-right:8px"><input type=checkbox ' + (ogsLy(l[0]) ? 'checked' : '') + ' onchange="ogsLySet(\'' + l[0] + '\',this.checked)">' + l[1] + '</label>'; }).join('') +
    ' <button class=x title="Kembalikan posisi judul, panah utara, skala, legenda dan label ke otomatis" onclick="ogsPt().pos={};ogsPt().lab={};ogsRender()">&#8634; posisi otomatis</button></div>' +
    '<div class=hint>Kontur: ' + (ks ? '<b>' + ogsE(ks.nm) + '</b> (' + ks.L.length + ' string) <button class=x onclick="OGS.p.pt.kstr=null;ogsRender()" title="Lepas">&times;</button>' : '<i>belum ada string kontur</i>') + ' <label class=btn style="display:inline-block;cursor:pointer;border:1px solid #ccd;padding:1px 8px;border-radius:5px">&#8679; Impor string kontur (.str / .dxf)<input type=file accept=".str,.dxf,.txt,.csv" style="display:none" onchange="ogsKontImp(this)"></label> ' +
    ogsSel("ogsPtSet('kont',this.value)", [['auto', ks ? 'pakai string kontur' : 'dari collar (cadangan)'], ['collar', 'dari collar (cadangan)'], ['off', 'tanpa kontur']], P.kont) + ' interval ' + '<input type=number step=any style="width:60px" value="' + P.kInt + '" onchange="ogsPtSet(\'kInt\',+this.value)"> m</div>' +
    ogsIgHtml('peta', 'klik di peta; nama garis ikut tampil sejajar garis') + ogsFig('ogsPT', 820, 'peta_level') +
    '<div class=hint>Laporan: RL peta yang dicetak <input type=text value="' + ogsE(P.lapRL) + '" placeholder="mis. 280; 300; 320 (kosong = RL saat ini)" onchange="OGS.p.pt.lapRL=this.value" style="width:240px"></div>';
  return h;
}
function ogsLySet(k, v) { var P = ogsPt(); P.lay[k] = v; if (k === 'lub') P.lub = v; if (k === 'lubLab') P.lubLab = v; try { if (window.SA && SA.dirty) SA.dirty(); } catch (e) {} ogsDrPeta(); }
function ogsPtSet(k, v) { var P = ogsPt(); P[k] = v; if (k === 'altCi') { P.alt = v >= 0; } try { if (window.SA && SA.dirty) SA.dirty(); } catch (e) {} ogsRender(); }
function ogsPtCls(s) { var v = String(s).split(/[;\s]+/).map(function (x) { return +String(x).replace(',', '.'); }).filter(function (x) { return isFinite(x) && x > 0; }).sort(function (a, b) { return a - b; }); if (v.length !== 4) { alert('Isi 4 batas kelas, mis. 0,4; 0,5; 1; 3'); ogsRender(); return; } ogsPt().cls = v; ogsRender(); }
function ogsFmtN(v) { return Math.round(v).toLocaleString('id-ID'); }
function ogsDrPeta() {
  var F = OGS.F, gd = $('ogsPT'); if (!F || !gd) return; var P = ogsPt(), M = ogsPeta(); OGS._pt = M;
  if (M.kosong) { gd.innerHTML = '<div class=hint style="padding:20px">Tidak ada sampel di RL ' + M.RL + ' ± ' + M.hs + ' m.</div>'; return; }
  var T = [], sh = [], ann = [], key = [], cls = P.cls, ox = offX, oy = offY, X = M.gx.map(function (x) { return x + ox; }), Y = M.gy.map(function (y) { return y + oy; });
  var W = (M.x1 - M.x0), H = (M.y1 - M.y0), lab = P.lab || (P.lab = {}), LK = 'RL' + M.RL;
  /* kontur */
  var ks = P.kstr, kmode = !ogsLy('kont') ? 'off' : P.kont === 'auto' ? (ks ? 'str' : 'collar') : P.kont, ki = Math.max(0.5, +P.kInt || 5);
  if (kmode === 'str' && ks) { var kx = [], ky = []; ks.L.forEach(function (l) { var inb = l.some(function (q) { return q[0] > M.x0 && q[0] < M.x1 && q[1] > M.y0 && q[1] < M.y1; }); if (!inb) return; l.forEach(function (q) { kx.push(q[0] + ox); ky.push(q[1] + oy); }); kx.push(null); ky.push(null);
      var z = l[0][2]; if (Math.abs(z / (2 * ki) - Math.round(z / (2 * ki))) < 1e-6) { var m = l[Math.floor(l.length / 2)]; if (m[0] > M.x0 && m[0] < M.x1 && m[1] > M.y0 && m[1] < M.y1) ann.push({ x: m[0] + ox, y: m[1] + oy, text: String(Math.round(z)), showarrow: false, font: { size: 9, color: '#868e96' }, bgcolor: 'rgba(241,243,245,.85)' }), key.push(null); } });
    T.push({ type: 'scattergl', mode: 'lines', x: kx, y: ky, line: { color: '#a5abb2', width: 0.7 }, hoverinfo: 'skip', name: 'Kontur ' + ki + ' m (' + ks.nm + ')', showlegend: true, connectgaps: false }); }
  else if (kmode === 'collar') { var cg = [], cs = 10; M.gy.forEach(function (y, b) { if (b % 3) return; var r = []; M.gx.forEach(function (x, a) { if (a % 3) { return; } var s = 0, w = 0; Object.keys(holeData).forEach(function (h) { var hd = holeData[h], d = Math.hypot(hd.x - x, hd.y - y); if (d < 40) { var ww = 1 / Math.max(d, 2) / Math.max(d, 2); s += ww * hd.z; w += ww; } }); r.push(w ? s / w : null); }); cg.push(r); });
    T.push({ type: 'contour', x: X.filter(function (v, a) { return !(a % 3); }), y: Y.filter(function (v, b) { return !(b % 3); }), z: cg, showscale: false, contours: { coloring: 'none', showlabels: true, size: ki, labelfont: { size: 9, color: '#868e96' } }, line: { color: '#a5abb2', width: 0.7 }, hoverinfo: 'skip', name: 'Kontur collar ' + ki + ' m (bukan topografi)', showlegend: true }); }
  /* kadar */
  var cs2 = [[0, OGS_KCOL[0]], [0.1999, OGS_KCOL[0]], [0.2, OGS_KCOL[1]], [0.3999, OGS_KCOL[1]], [0.4, OGS_KCOL[2]], [0.5999, OGS_KCOL[2]], [0.6, OGS_KCOL[3]], [0.7999, OGS_KCOL[3]], [0.8, OGS_KCOL[4]], [1, OGS_KCOL[4]]];
  /* kadar halus: nilai dipetakan ke ruang kelas (batas kelas = bilangan bulat 1..4) lalu dikontur terisi */
  var BB = [0, +cls[0], +cls[1], +cls[2], +cls[3], 3 * cls[3]], U = M.Z.map(function (r) { return r.map(function (g) { if (g == null) return null; var k = 0; while (k < 4 && g >= BB[k + 1]) k++; return Math.min(4.999, k + (g - BB[k]) / (BB[k + 1] - BB[k])); }); });
  if (ogsLy('kadar')) { var U2 = U.map(function (r) { return r.map(function (v) { return v == null ? -1 : v; }); }), q6 = function (v) { return (v + 1) / 6; }, cs3 = [[0, 'rgba(0,0,0,0)'], [q6(-0.001), 'rgba(0,0,0,0)']];
    OGS_KCOL.forEach(function (c, k) { cs3.push([q6(k), c], [q6(k + 1) - 1e-4, c]); }); cs3[cs3.length - 1][0] = 1;
    T.push({ type: 'heatmap', x: X, y: Y, z: U2, zmin: -1, zmax: 5, colorscale: cs3, showscale: false, opacity: 0.9, zsmooth: 'best', hoverinfo: 'skip', showlegend: false });
    T.push({ type: 'heatmap', x: X, y: Y, z: M.Z, opacity: 0, showscale: false, hovertemplate: ogsAu() + ' %{z:.2f} g/t<extra></extra>', showlegend: false }); }
  var fm = function (v) { return String(+(+v).toPrecision(4)).replace('.', ','); }, lbl = ['< ' + fm(cls[0]), fm(cls[0]) + ' – ' + fm(cls[1]), fm(cls[1]) + ' – ' + fm(cls[2]), fm(cls[2]) + ' – ' + fm(cls[3]), '≥ ' + fm(cls[3])];
  if (ogsLy('kadar')) for (var k = 4; k >= 0; k--) T.push({ type: 'scatter', mode: 'markers', x: [null], y: [null], marker: { symbol: 'square', size: 13, color: OGS_KCOL[k] }, name: ogsE(ogsAu()) + ' ' + lbl[k] + (k === 4 ? ' g/t' : ''), legendgroup: 'au', legendgrouptitle: k === 4 ? { text: ogsAu() + ' g/t (interpolasi)' } : undefined, showlegend: true });
  /* arsir alterasi: run per baris sel -> persegi dengan fillpattern */
  if (ogsLy('alt')) M.cats.forEach(function (c, j) { var px = [], py = [], h2 = M.res / 2; M.AL.forEach(function (row, b) { var a = 0; while (a < row.length) { if (row[a] !== c) { a++; continue; } var s = a; while (a < row.length && row[a] === c) a++; var xa = M.gx[s] - h2 + ox, xb = M.gx[a - 1] + h2 + ox, ya = M.gy[b] - h2 + oy, yb = M.gy[b] + h2 + oy; px.push(xa, xb, xb, xa, xa, null); py.push(ya, ya, yb, yb, ya, null); } });
    if (px.length) T.push({ type: 'scatter', mode: 'none', x: px, y: py, fill: 'toself', fillcolor: 'rgba(0,0,0,0)', fillpattern: { shape: OGS_HAT[j][0], fgcolor: '#2b2b2b', bgcolor: 'rgba(0,0,0,0)', size: 7, solidity: 0.12 }, hoverinfo: 'skip', name: 'Alterasi ' + geoName(M.ci, c), legendgroup: 'alt', showlegend: true }); });
  /* wireframe */
  M.WF.forEach(function (w) { var px = [], py = []; (P.wfMode === 'dinding' ? w.L.map(function (l) { return l.closed ? l.p.concat([l.p[0]]) : l.p; }) : w.mid).forEach(function (l) { l.forEach(function (q) { px.push(q[0] + ox); py.push(q[1] + oy); }); px.push(null); py.push(null); });
    if (px.length && ogsLy('wf')) T.push({ type: 'scatter', mode: 'lines', x: px, y: py, line: { color: '#c00000', width: +P.wfW || 2.5 }, hoverinfo: 'name', name: w.d.nm, legendgroup: 'wf', showlegend: false, connectgaps: false });
    if (w.c && ogsLy('wfLab')) { var kk = LK + ':d:' + w.d.k, sv = lab[kk] || {}; ann.push({ x: w.c[0] + ox, y: w.c[1] + oy, ax: sv.ax != null ? sv.ax : -70, ay: sv.ay != null ? sv.ay : 0, text: '<b>' + ogsE(w.d.nm) + '</b>', font: { color: '#fff', size: 11 }, bgcolor: '#1d1d1d', borderpad: 4, showarrow: true, arrowhead: 0, arrowwidth: 1, arrowcolor: '#1d1d1d' }); key.push(kk); } });
  if (M.WF.length && ogsLy('wf')) T.push({ type: 'scatter', mode: 'lines', x: [null], y: [null], line: { color: '#c00000', width: 3 }, name: 'Wireframe domain di RL ' + M.RL + (P.wfMode === 'dinding' ? '' : ' (garis tengah)'), showlegend: true });
  /* lubang */
  if (ogsLy('lub')) { var gx2 = [], gy2 = [], ux = [], uy = [], ex = [], ey = [], tx = [], ty = [], placed = [];
    M.LB.forEach(function (l) { if (l.eks) { ex.push(l.x + ox); ey.push(l.y + oy); l.tr.forEach(function (q) { tx.push(q[0] + ox); ty.push(q[1] + oy); }); tx.push(null); ty.push(null);
        if (ogsLy('lubLab') && placed.every(function (p) { return Math.hypot(p[0] - l.x, p[1] - l.y) > W / 25; })) { placed.push([l.x, l.y]); var kh = LK + ':h:' + l.h, s2 = lab[kh] || {}; ann.push({ x: l.x + ox, y: l.y + oy, ax: s2.ax != null ? s2.ax : -28, ay: s2.ay != null ? s2.ay : -16, text: '<b>' + ogsE(l.h) + '</b>', font: { color: '#fff', size: 10 }, bgcolor: '#8b1a1a', borderpad: 3, showarrow: true, arrowhead: 0, arrowwidth: 0.8, arrowcolor: '#8b1a1a' }); key.push(kh); } }
      else if (l.lewat) { gx2.push(l.x + ox); gy2.push(l.y + oy); } else { ux.push(l.x + ox); uy.push(l.y + oy); } });
    T.push({ type: 'scatter', mode: 'lines', x: tx, y: ty, line: { color: '#ffffff', width: 2.2 }, hoverinfo: 'skip', showlegend: false, connectgaps: false });
    T.push({ type: 'scatter', mode: 'lines', x: tx, y: ty, line: { color: '#adb5bd', width: 0.8 }, hoverinfo: 'skip', name: 'Jejak lubang eksplorasi', showlegend: !!tx.length, connectgaps: false });
    T.push({ type: 'scattergl', mode: 'markers', x: gx2, y: gy2, marker: { size: 3.5, color: '#495057' }, name: 'Lubang GC (tembus RL)', showlegend: !!gx2.length, hoverinfo: 'skip' });
    T.push({ type: 'scattergl', mode: 'markers', x: ux, y: uy, marker: { size: 4, color: 'rgba(0,0,0,0)', line: { width: 1, color: '#495057' } }, name: 'Lubang GC berakhir di irisan', showlegend: !!ux.length, hoverinfo: 'skip' });
    T.push({ type: 'scatter', mode: 'markers', x: ex, y: ey, marker: { size: 9, color: '#868e96', line: { width: 1, color: '#343a40' } }, name: 'Lubang eksplorasi (tembus RL)', showlegend: !!ex.length, hoverinfo: 'skip' }); }
  /* garis interpretasi + nama sejajar garis */
  var Lay = { xaxis: { range: [M.x0 + ox, M.x1 + ox], tickformat: ',d', ticksuffix: ' mE', showgrid: ogsLy('grid'), gridcolor: 'rgba(0,0,0,.08)', zeroline: false, ticks: 'inside', mirror: true, linewidth: 1.5, linecolor: '#222', tickfont: { size: 10 } },
    yaxis: { range: [M.y0 + oy, M.y1 + oy], tickformat: ',d', ticksuffix: ' mN', scaleanchor: 'x', showgrid: ogsLy('grid'), gridcolor: 'rgba(0,0,0,.08)', zeroline: false, ticks: 'inside', mirror: true, linewidth: 1.5, linecolor: '#222', tickangle: -90, tickfont: { size: 10 } },
    xaxis2: { overlaying: 'x', matches: 'x', side: 'top', tickformat: ',d', ticksuffix: ' mE', showgrid: false, ticks: 'inside', tickfont: { size: 10 } }, yaxis2: { overlaying: 'y', matches: 'y', side: 'right', tickformat: ',d', ticksuffix: ' mN', showgrid: false, ticks: 'inside', tickangle: 90, tickfont: { size: 10 } } };
  T.push({ type: 'scatter', x: [null], y: [null], xaxis: 'x2', yaxis: 'y2', showlegend: false, hoverinfo: 'skip' });
  var T2 = []; if (ogsLy('ig')) ogsIgApply('peta', T2, Lay); else { Lay.shapes = []; Lay.annotations = []; } T = T.concat(T2.map(function (t) { t.legendgroup = 'ig'; return t; }));
  if (ogsLy('ig')) ogsIgL('peta').forEach(function (g) { if (g.typ !== 'line' || g.pts.length < 2) return; var a = g.pts[Math.floor((g.pts.length - 1) / 2)], b = g.pts[Math.floor((g.pts.length - 1) / 2) + 1], ang = Math.atan2(b[1] - a[1], b[0] - a[0]) * 180 / Math.PI; if (ang > 90) ang -= 180; if (ang < -90) ang += 180;
    Lay.annotations.push({ x: (a[0] + b[0]) / 2, y: (a[1] + b[1]) / 2, text: '<b>' + ogsE(g.nm) + '</b>', textangle: -ang, showarrow: false, font: { size: 11, color: g.usul ? '#868e96' : g.col }, bgcolor: 'rgba(255,255,255,.7)', yshift: 9 }); });
  ann.forEach(function (a) { a.xref = 'x'; a.yref = 'y'; }); var nIg = Lay.annotations.length; Lay.annotations = Lay.annotations.concat(ann); key = new Array(nIg).fill(null).concat(key); OGS._ptKey = key;
  /* judul, panah utara + skala, legenda: di dalam peta, bisa digeser; posisi awal = sudut paling kosong */
  var pos = P.pos || (P.pos = {}), cnt = [[0.02, 0.98], [0.98, 0.98], [0.02, 0.02], [0.98, 0.02]].map(function (c) { var n = 0, nx = M.gx.length, ny = M.gy.length; for (var b = 0; b < ny; b++) { var fy = b / ny; if (c[1] > 0.5 ? fy < 0.68 : fy > 0.32) continue; for (var a = 0; a < nx; a++) { var fx = a / nx; if (c[0] > 0.5 ? fx < 0.7 : fx > 0.3) continue; if (M.K[b][a] != null) n++; } } return { c: c, n: n }; }).sort(function (p, q) { return p.n - q.n; });
  var dUt = cnt[0].c, dLg = cnt[1].c, dJd = cnt[2].c, pU = pos.utara || { x: dUt[0] > 0.5 ? 0.9 : 0.1, y: dUt[1] > 0.5 ? 0.97 : 0.2 }, pJ = pos.judul || { x: dJd[0], y: dJd[1] }, pL = pos.legenda || { x: dLg[0], y: dLg[1] };
  var sc = [10, 20, 25, 50, 100, 200, 250, 500, 1000].filter(function (v) { return v <= W / 5; }).pop() || 10, fr2 = sc / W, fix = {};
  if (ogsLy('judul')) { fix[Lay.annotations.length] = 'judul'; Lay.annotations.push({ xref: 'x domain', yref: 'y domain', x: pJ.x, y: pJ.y, xanchor: pJ.x > 0.5 ? 'right' : 'left', yanchor: pJ.y > 0.5 ? 'top' : 'bottom', align: 'left', showarrow: false, bgcolor: 'rgba(255,255,255,.95)', bordercolor: '#1f2d6b', borderwidth: 1.2, borderpad: 7,
    text: '<b style="font-size:16px;color:#1f2d6b">Peta level RL ' + M.RL + ' · irisan ±' + M.hs + ' m</b><br><span style="font-size:10px;color:#495057">' + ogsFmtN(M.I.length) + ' interval · ' + (P.mode === 'dom' ? 'kadar di dalam domain' : 'interpolasi anomali, anisotropi ' + P.rat + ':1 searah strike ' + ogsAzTxt(F.fr.az)) + '</span>' }); }
  if (ogsLy('utara')) { var yb = pU.y - 0.085, xb0 = pU.x - fr2 / 2;
    Lay.shapes = (Lay.shapes || []).concat([{ type: 'rect', xref: 'x domain', yref: 'y domain', x0: Math.min(pU.x - 0.035, xb0 - 0.02), x1: Math.max(pU.x + 0.035, xb0 + fr2 + 0.035), y0: yb - 0.035, y1: pU.y + 0.008, fillcolor: 'rgba(255,255,255,.92)', line: { color: '#888', width: 1 } }])
      .concat([0, 1, 2, 3].map(function (i) { return { type: 'rect', xref: 'x domain', yref: 'y domain', x0: xb0 + i * fr2 / 4, x1: xb0 + (i + 1) * fr2 / 4, y0: yb, y1: yb + 0.006, fillcolor: i % 2 ? '#fff' : '#111', line: { color: '#111', width: 0.8 } }; }));
    fix[Lay.annotations.length] = 'utara'; Lay.annotations.push({ xref: 'x domain', yref: 'y domain', x: pU.x, y: pU.y, xanchor: 'center', yanchor: 'top', showarrow: false, text: '<b><span style="font-size:24px">&#x2B06;</span><br>N</b>', font: { size: 14, color: '#111' }, hovertext: 'tarik untuk memindah panah utara & skala' });
    [[0, '0'], [fr2 / 2, String(sc / 2)], [fr2, sc + ' m']].forEach(function (q) { Lay.annotations.push({ xref: 'x domain', yref: 'y domain', x: xb0 + q[1 - 1 + 0 * 0] * 0 + q[0], y: yb - 0.004, text: q[1], showarrow: false, yanchor: 'top', font: { size: 10 } }); }); }
  OGS._ptFix = fix;
  Lay = ogsLay(Object.assign(Lay, { showlegend: ogsLy('legenda'), legend: { x: pL.x, y: pL.y, xanchor: pL.x > 0.5 ? 'right' : 'left', yanchor: pL.y > 0.5 ? 'top' : 'bottom', bgcolor: 'rgba(255,255,255,.95)', bordercolor: '#888', borderwidth: 1, font: { size: 10 }, tracegroupgap: 4, groupclick: 'toggleitem' }, plot_bgcolor: '#f1f3f5', margin: { l: 70, r: 70, t: 46, b: 46 }, dragmode: OGS.ig && OGS.ig.key === 'peta' ? false : 'pan', separators: ',.' }));
  var asp = H / W, w0 = gd.offsetWidth || 900; gd.style.height = Math.max(520, Math.min(1500, Math.round((w0 - 140) * asp + 92))) + 'px';
  Plotly.newPlot(gd, T, Lay, Object.assign({}, OGS_CFG, { edits: { annotationTail: true, annotationPosition: true, legendPosition: true } }));
  ogsIgBind('ogsPT', 'peta');
  if (!gd._lab) { gd._lab = 1; gd.on('plotly_relayout', function (e) { var K = OGS._ptKey || [], FX = OGS._ptFix || {}, ch = false, ulang = false, ps = ogsPt().pos;
    Object.keys(e || {}).forEach(function (k) { var m = /^annotations\[(\d+)\]\.(ax|ay|x|y)$/.exec(k);
      if (m) { var i = +m[1]; if (FX[i] && (m[2] === 'x' || m[2] === 'y')) { var o2 = ps[FX[i]] || (ps[FX[i]] = Object.assign({}, gd.layout.annotations[i] ? { x: gd.layout.annotations[i].x, y: gd.layout.annotations[i].y } : {})); o2[m[2]] = +(+e[k]).toFixed(4); ch = true; if (FX[i] === 'utara') ulang = true; return; }
        var kk = K[i]; if (!kk || (m[2] !== 'ax' && m[2] !== 'ay')) return; var o = ogsPt().lab[kk] || (ogsPt().lab[kk] = {}); o[m[2]] = Math.round(e[k]); ch = true; return; }
      var g = /^legend\.(x|y)$/.exec(k); if (g) { var o3 = ps.legenda || (ps.legenda = { x: gd.layout.legend.x, y: gd.layout.legend.y }); o3[g[1]] = +(+e[k]).toFixed(4); ch = true; } });
    if (ch) try { if (window.SA && SA.dirty) SA.dirty(); } catch (x) {} if (ulang) setTimeout(ogsDrPeta, 0); }); }
}
/* ekspor garis interpretasi peta = di RL itu */
(function () { var _x = ogsIgXYZ; ogsIgXYZ = function (key, p) { if (key === 'peta') return [p[0] - offX, p[1] - offY, ogsPtRL()]; return _x.apply(this, arguments); }; })();
Object.assign(OGS_PG, { peta: ogsPgPeta }); Object.assign(OGS_DR, { peta: ogsDrPeta });
