/* ================= ORE GEOMETRY STUDIO (GC-Ex Drillhole 0.24.72) =================
   Keputusan pemilik 11 Nov 2026 (claude/KEPUTUSAN_GCEX_ORE_GEOMETRY_STUDIO.md):
   - Semua grafik deck "Ore Geometry Zona 2" bisa dibuat dari node Ore Geometry, jalur Mulai dari Nol maupun Lanjutkan.
   - Satu jendela pop-up lebar (POP.win) berisi seluruh menu; panel samping hanya ringkasan + tombol pembuka.
   - Studio BERDIRI SENDIRI: sayatannya tidak menggerakkan Slicer 3D; hasilnya tidak ditulis ke Geomodeller / estimasi.
   - Flag domain otomatis: titik tengah interval assay di dalam wireframe domain (solid GC-Ex dan / atau wireframe impor),
     urutan daftar = prioritas bila wireframe bertumpang.
   - Menu redundan diizinkan: alat lama (Intercept, Long section GT, Ore shoot, Grade shell), Profil Geostatistik & Slicer.
   Tahap 1 (versi ini): Data & domain, Geometri & tebal, Kadar & multi-elemen, Long section, Envelope RBF & 3D,
   Zonasi vertikal, Profil per domain, Penampang (sayatan sendiri). Tahap 2: struktur, pertemuan vein, target, laporan PDF.
   Pembersihan data TIDAK dilakukan otomatis: "Pemeriksaan data" hanya menampilkan temuan. */
var OGS = {
  p: { mesh: {}, ord: [], gap: 1, sg: 2.42, cut: 0.6, halo: 45, bw: 10, ref: '', au: '', ag: '', res: 2, maxD: 30, nearD: 25, smooth: 0.5, rmin: 0.1,
    lsEl: [], zEls: [], secEls: [], secGeo: -1, geoCols: [], pf: null, pfDom: '', sec: [], secI: 0, envDom: '' },
  F: null, E: {}, nav: 'data', msg: '', draw: null, open: false
};
function ogsE(s) { return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) { return '&#' + c.charCodeAt(0) + ';'; }); }
function ogsN(v, d) { if (v == null || !isFinite(v)) return '–'; return (+v).toLocaleString('id-ID', { minimumFractionDigits: d || 0, maximumFractionDigits: d || 0 }); }
function ogsAuto(v) { if (v == null || !isFinite(v)) return '–'; var a = Math.abs(v); return ogsN(v, a >= 100 ? 0 : a >= 10 ? 1 : a >= 1 ? 2 : 3); }
function ogsFind(re) { var E = window.elements || []; for (var i = 0; i < E.length; i++) if (re.test(E[i])) return E[i]; return ''; }
function ogsMed(a) { return ogsQ(a, 0.5); }
function ogsQ(a, q) { var b = a.filter(function (v) { return v != null && isFinite(v); }).sort(function (x, y) { return x - y; }); if (!b.length) return NaN; var p = (b.length - 1) * q, i = Math.floor(p), f = p - i; return i + 1 < b.length ? b[i] * (1 - f) + b[i + 1] * f : b[i]; }
function ogsDot(a, b) { return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]; }
function ogsDark() { return document.body.classList.contains('dark'); }
function ogsLay(o) { var d = ogsDark(), L = { paper_bgcolor: d ? '#16202c' : '#fff', plot_bgcolor: d ? '#0e1621' : '#fff', font: { size: 11, color: d ? '#dbe3ec' : '#333' }, margin: { l: 56, r: 16, t: 34, b: 44 }, showlegend: false }; for (var k in o) L[k] = o[k]; return L; }
var OGS_CFG = { displaylogo: false, responsive: true, modeBarButtonsToRemove: ['lasso2d', 'select2d'] };
var OGS_PAL = ['#e03131', '#c2255c', '#ff8787', '#f08c00', '#fab005', '#2f9e44', '#1971c2', '#7048e8', '#0c8599', '#862e9c', '#5c940d', '#495057'];
function ogsEi(e) { return (window.elements || []).indexOf(e); }
function ogsAu() { var e = OGS.p.au; if (!e || ogsEi(e) < 0) e = OGS.p.au = ogsFind(/^au/i) || (window.elements || [])[0] || ''; return e; }
function ogsAg() { var e = OGS.p.ag; if (e === '' || (e && ogsEi(e) < 0)) e = OGS.p.ag = ogsFind(/^ag/i); return e; }

/* ---------- 1. sumber domain (wireframe) & flag otomatis ---------- */
function ogsSrc() {
  var L = [];
  ((window.MD && MD.models) || []).forEach(function (m) { if (m && m.nt && m.jenis !== 'surf') L.push({ k: 'md:' + m.name, nm: String(m.name).replace(/\.[^.]+$/, ''), m: m, j: 'wireframe impor' }); });
  ((window.GM && GM.doms) || []).forEach(function (d) { var R = window.IM && IM.R[d.id]; if (R && R.mesh && R.mesh.nt) L.push({ k: 'im:' + d.id, nm: d.name, m: R.mesh, j: 'solid GC-Ex' }); });
  var P = OGS.p, adaMd = L.some(function (s) { return s.k[0] === 'm'; });
  L.forEach(function (s) { if (P.mesh[s.k] == null) P.mesh[s.k] = adaMd ? s.k[0] === 'm' : true; });
  L.sort(function (a, b) { var ia = P.ord.indexOf(a.k), ib = P.ord.indexOf(b.k); if (ia < 0) ia = 1e6 + L.indexOf(a); if (ib < 0) ib = 1e6 + L.indexOf(b); return ia - ib; });
  P.ord = L.map(function (s) { return s.k; });
  return L;
}
function ogsKunci() { return (window.assays || []).length + '|' + ogsSrc().filter(function (s) { return OGS.p.mesh[s.k]; }).map(function (s) { return s.k + ':' + s.m.nt + ':' + s.m.nv; }).join(',') + '|' + OGS.p.gap; }
function ogsMove(k, d) { var o = OGS.p.ord, i = o.indexOf(k), j = i + d; if (i < 0 || j < 0 || j >= o.length) return; o.splice(i, 1); o.splice(j, 0, k); ogsDirty(); }
function ogsDirty() { OGS.F = null; OGS.E = {}; try { if (window.SA && SA.dirty) SA.dirty(); } catch (e) {} ogsRender(); }

function ogsFlag() {
  var src = ogsSrc().filter(function (s) { return OGS.p.mesh[s.k]; });
  if (!src.length) { OGS.msg = '<span class=warn>Belum ada wireframe domain. Bangun solid di Geological Modelling (Mulai dari Nol) atau import wireframe (Lanjutkan).</span>'; return null; }
  var t0 = performance.now(), W = src.map(function (s) { var m = s.m; if (!m._ogsW || m._ogsW.nt !== m.nt) { m._ogsW = wfInside(m); m._ogsW.nt = m.nt; }
    var b = [1e18, -1e18, 1e18, -1e18, 1e18, -1e18]; for (var i = 0; i < m.nv; i++) { var x = m._x[i], y = m._y[i], z = m._z[i]; if (x < b[0]) b[0] = x; if (x > b[1]) b[1] = x; if (y < b[2]) b[2] = y; if (y > b[3]) b[3] = y; if (z < b[4]) b[4] = z; if (z > b[5]) b[5] = z; }
    return { f: m._ogsW.f, open: m._ogsW.open, ne: m._ogsW.ne, b: b }; });
  var A = (window.assays || []).filter(function (a) { return a[2] > a[1] && holeData[a[0]]; }).slice().sort(function (a, b) { return a[0] < b[0] ? -1 : a[0] > b[0] ? 1 : a[1] - b[1]; });
  var n = A.length, X = new Float64Array(n), Y = new Float64Array(n), Z = new Float64Array(n), D = new Int16Array(n), V = [], NE = (window.elements || []).length;
  for (var i = 0; i < n; i++) { var a = A[i], p = getXYZ(a[0], (a[1] + a[2]) / 2); X[i] = p.x; Y[i] = p.y; Z[i] = p.z; D[i] = -1;
    for (var q = 0; q < W.length; q++) { var b = W[q].b; if (p.x < b[0] || p.x > b[1] || p.y < b[2] || p.y > b[3] || p.z < b[4] || p.z > b[5]) continue; if (W[q].f(p.x, p.y, p.z)) { D[i] = q; break; } } }
  for (var e = 0; e < NE; e++) { var c = new Float64Array(n); for (i = 0; i < n; i++) { var v = A[i][4] && A[i][4][e]; c[i] = v == null || !isFinite(v) ? NaN : +v; } V.push(c); }
  var F = { A: A, n: n, X: X, Y: Y, Z: Z, D: D, V: V, dom: src.map(function (s, q) { return { k: s.k, nm: s.nm, j: s.j, m: s.m, open: W[q].open, ne: W[q].ne, col: OGS_PAL[q % OGS_PAL.length] }; }), key: ogsKunci(), when: Date.now() };
  ogsIcpt(F); ogsFrame(F); F.ms = performance.now() - t0; OGS.F = F; OGS.E = {};
  var nin = 0; for (i = 0; i < n; i++) if (D[i] >= 0) nin++;
  OGS.msg = '&#10003; ' + ogsN(nin) + ' interval di dalam ' + src.length + ' wireframe domain, ' + ogsN(F.I.length) + ' intercept (' + (F.ms / 1000).toFixed(1) + ' s).' +
    (F.dom.some(function (d) { return d.open; }) ? ' <span class=warn>Wireframe tidak tertutup: ' + F.dom.filter(function (d) { return d.open; }).map(function (d) { return ogsE(d.nm); }).join(', ') + ' (hasil di dekat bagian terbuka bisa tidak akurat).</span>' : '');
  return F;
}
/* intercept = interval berurutan sedomain di satu lubang, sela <= gap */
function ogsIcpt(F) {
  var I = [], gap = Math.max(0, +OGS.p.gap || 0), cur = null, A = F.A;
  for (var i = 0; i < F.n; i++) { var d = F.D[i], a = A[i];
    if (d < 0) { continue; }
    if (cur && cur.h === a[0] && cur.d === d && a[1] - cur.t <= gap + 1e-6) { cur.r.push(i); cur.t = Math.max(cur.t, a[2]); continue; }
    if (cur) I.push(cur); cur = { h: a[0], d: d, f: a[1], t: a[2], r: [i] }; }
  if (cur) I.push(cur);
  I.forEach(function (c) { var L = 0, px = 0, py = 0, pz = 0, g = (window.elements || []).map(function () { return [0, 0]; });
    c.r.forEach(function (i) { var l = A[i][2] - A[i][1]; L += l; px += F.X[i] * l; py += F.Y[i] * l; pz += F.Z[i] * l; F.V.forEach(function (col, e) { var v = col[i]; if (isFinite(v)) { g[e][0] += v * l; g[e][1] += l; } }); });
    c.L = L; c.p = [px / L, py / L, pz / L]; c.g = g.map(function (q) { return q[1] > 0 ? q[0] / q[1] : NaN; }); c.u = ogDir(c.h, (c.f + c.t) / 2); });
  F.I = I;
}
function ogsPCA(P, W) { var f = ogPlaneFit(P, W); if (!f) return null; var V = ogVec(f.dip, f.ddir); return { c: f.c, dip: f.dip, ddir: f.ddir, n: V.n, strike: (f.ddir + 270) % 360 }; }
/* bidang per domain + bidang acuan (domain dengan intercept terbanyak, atau pilihan) */
function ogsFrame(F) {
  var au = ogsEi(ogsAu());
  F.dom.forEach(function (d, q) { var L = F.I.filter(function (c) { return c.d === q; }); d.nI = L.length; d.pl = L.length >= 3 ? ogsPCA(L.map(function (c) { return c.p; }), L.map(function (c) { return c.L; })) : null; });
  F.I.forEach(function (c) { var pl = F.dom[c.d].pl, n = pl ? pl.n : [0, 0, 1]; c.T = c.L * Math.abs(ogsDot(c.u, n)); c.gt = isFinite(c.g[au]) ? c.g[au] * c.T : NaN; });
  var ref = -1; F.dom.forEach(function (d, q) { if (OGS.p.ref === d.k && d.pl) ref = q; }); if (ref < 0) { var mx = -1; F.dom.forEach(function (d, q) { if (d.pl && d.nI > mx) { mx = d.nI; ref = q; } }); }
  F.ref = ref; var pl = ref >= 0 ? F.dom[ref].pl : null;
  if (!pl) { pl = { c: [0, 0, 0], dip: 90, ddir: 90, n: [1, 0, 0], strike: 0 }; var sx = 0, sy = 0, sz = 0; for (var i = 0; i < F.n; i++) { sx += F.X[i]; sy += F.Y[i]; sz += F.Z[i]; } pl.c = [sx / F.n, sy / F.n, sz / F.n]; }
  F.fr = ogsMkFrame(pl);
  F.LS = new Float64Array(F.n); F.Wd = new Float64Array(F.n);
  for (i = 0; i < F.n; i++) { var r = [F.X[i] - F.fr.c[0], F.Y[i] - F.fr.c[1], F.Z[i] - F.fr.c[2]]; F.LS[i] = ogsDot(r, F.fr.sv); F.Wd[i] = ogsDot(r, F.fr.n); }
  F.I.forEach(function (c) { var r = [c.p[0] - F.fr.c[0], c.p[1] - F.fr.c[1], c.p[2] - F.fr.c[2]]; c.ls = ogsDot(r, F.fr.sv); c.w = ogsDot(r, F.fr.n); });
}
/* kerangka: sv = strike horizontal yang menunjuk ke selatan (az 90–270), n = normal ke atas (komponen horizontal = arah dip) */
function ogsMkFrame(pl) { var st = pl.strike, az = st; if (!(az > 90 && az <= 270)) az = (st + 180) % 360; var r = az * Math.PI / 180, sv = [Math.sin(r), Math.cos(r), 0], n = pl.n.slice(); if (n[2] < 0) n = n.map(function (v) { return -v; });
  return { c: pl.c, sv: sv, n: n, az: az, dip: pl.dip, ddir: pl.ddir }; }
function ogsAzTxt(a) { return ('00' + Math.round(((a % 360) + 360) % 360)).slice(-3) + '°'; }
function ogsArah(a) { var L = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE', 'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW']; return L[Math.round((((a % 360) + 360) % 360) / 22.5) % 16]; }

/* ---------- statistik ---------- */
function ogsRank(a) { var idx = a.map(function (v, i) { return i; }).sort(function (x, y) { return a[x] - a[y]; }), r = new Array(a.length), i = 0; while (i < idx.length) { var j = i; while (j + 1 < idx.length && a[idx[j + 1]] === a[idx[i]]) j++; for (var k = i; k <= j; k++) r[idx[k]] = (i + j) / 2; i = j + 1; } return r; }
function ogsSpear(x, y) { var X = [], Y = []; for (var i = 0; i < x.length; i++) if (isFinite(x[i]) && isFinite(y[i])) { X.push(x[i]); Y.push(y[i]); } if (X.length < 8) return NaN; var a = ogsRank(X), b = ogsRank(Y), n = a.length, ma = 0, mb = 0; for (i = 0; i < n; i++) { ma += a[i]; mb += b[i]; } ma /= n; mb /= n; var sab = 0, saa = 0, sbb = 0; for (i = 0; i < n; i++) { sab += (a[i] - ma) * (b[i] - mb); saa += (a[i] - ma) * (a[i] - ma); sbb += (b[i] - mb) * (b[i] - mb); } return sab / Math.sqrt(saa * sbb); }
function ogsWmean(F, e, idx) { var s = 0, w = 0; idx.forEach(function (i) { var v = F.V[e][i]; if (isFinite(v)) { var l = F.A[i][2] - F.A[i][1]; s += v * l; w += l; } }); return w > 0 ? s / w : NaN; }
function ogsIn(F, q) { var o = []; for (var i = 0; i < F.n; i++) if (q == null ? F.D[i] >= 0 : F.D[i] === q) o.push(i); return o; }
function ogsOut(F) { var o = []; for (var i = 0; i < F.n; i++) if (F.D[i] < 0) o.push(i); return o; }
function ogsVals(F, e, idx) { var o = []; idx.forEach(function (i) { var v = F.V[e][i]; if (isFinite(v)) o.push(v); }); return o; }

/* ---------- RBF linear 2D + polinom derajat 1 + smoothing (setara scipy RBFInterpolator linear) ---------- */
function ogsSolve(A, b, m) { for (var c = 0; c < m; c++) { var p = c, mx = Math.abs(A[c * m + c]); for (var r = c + 1; r < m; r++) { var v = Math.abs(A[r * m + c]); if (v > mx) { mx = v; p = r; } } if (mx < 1e-12) continue;
    if (p !== c) { for (var k = 0; k < m; k++) { var t = A[c * m + k]; A[c * m + k] = A[p * m + k]; A[p * m + k] = t; } t = b[c]; b[c] = b[p]; b[p] = t; }
    var d = A[c * m + c]; for (r = c + 1; r < m; r++) { var f = A[r * m + c] / d; if (!f) continue; for (k = c; k < m; k++) A[r * m + k] -= f * A[c * m + k]; b[r] -= f * b[c]; } }
  var x = new Float64Array(m); for (c = m - 1; c >= 0; c--) { var s = b[c]; for (k = c + 1; k < m; k++) s -= A[c * m + k] * x[k]; x[c] = Math.abs(A[c * m + c]) < 1e-12 ? 0 : s / A[c * m + c]; } return x; }
function ogsRbf(U, Zc, v, sm) { var n = U.length, m = n + 3, A = new Float64Array(m * m), b = new Float64Array(m), u0 = 0, z0 = 0; for (var i = 0; i < n; i++) { u0 += U[i]; z0 += Zc[i]; } u0 /= n; z0 /= n;
  for (i = 0; i < n; i++) { for (var j = 0; j < n; j++) A[i * m + j] = i === j ? sm : -Math.hypot(U[i] - U[j], Zc[i] - Zc[j]); A[i * m + n] = A[n * m + i] = 1; A[i * m + n + 1] = A[(n + 1) * m + i] = U[i] - u0; A[i * m + n + 2] = A[(n + 2) * m + i] = Zc[i] - z0; b[i] = v[i]; }
  var x = ogsSolve(A, b, m); return function (u, z) { var s = x[n] + x[n + 1] * (u - u0) + x[n + 2] * (z - z0); for (var i = 0; i < n; i++) s -= x[i] * Math.hypot(u - U[i], z - Zc[i]); return s; }; }

/* ---------- 5. envelope GT per domain ---------- */
function ogsEnv(q) {
  var F = OGS.F; if (!F) return null; if (OGS.E[q]) return OGS.E[q]; var d = F.dom[q], pl = d.pl; if (!pl) return null;
  var L = F.I.filter(function (c) { return c.d === q && isFinite(c.gt); }); if (L.length < 5) return null; if (L.length > 900) L = L.slice().sort(function (a, b) { return b.L - a.L; }).slice(0, 900);
  var fr = ogsMkFrame(pl), U = [], Zc = [], W = [], au = ogsEi(ogsAu()), sm = Math.max(0, +OGS.p.smooth || 0);
  L.forEach(function (c) { var r = [c.p[0] - fr.c[0], c.p[1] - fr.c[1], c.p[2] - fr.c[2]]; U.push(ogsDot(r, fr.sv)); Zc.push(c.p[2]); W.push(ogsDot(r, fr.n)); });
  var lg = function (v) { return Math.log10(Math.max(0.01, v)); }, fG = ogsRbf(U, Zc, L.map(function (c) { return lg(c.gt); }), sm), fT = ogsRbf(U, Zc, L.map(function (c) { return c.T; }), sm),
    fA = ogsRbf(U, Zc, L.map(function (c) { return lg(c.g[au]); }), sm), fW = ogsRbf(U, Zc, W, sm);
  var res = Math.max(0.5, +OGS.p.res || 2), maxD = Math.max(5, +OGS.p.maxD || 30), nearD = +OGS.p.nearD || 25, u0 = Math.min.apply(null, U) - maxD / 2, u1 = Math.max.apply(null, U) + maxD / 2, z0 = Math.min.apply(null, Zc) - maxD / 2, z1 = Math.max.apply(null, Zc) + maxD / 2;
  while (((u1 - u0) / res) * ((z1 - z0) / res) > 90000) res *= 1.25;
  var nx = Math.ceil((u1 - u0) / res) + 1, nz = Math.ceil((z1 - z0) / res) + 1, xs = [], zs = [], GT = [], TT = [], AU = [], WW = [], DD = [], Win = d.m._ogsW;
  for (var i = 0; i < nx; i++) xs.push(u0 + i * res); for (var k = 0; k < nz; k++) zs.push(z0 + k * res);
  var ez = [0, 0, 1], nh = [fr.n[0], fr.n[1], 0], hn = Math.hypot(nh[0], nh[1]) || 1; nh = [nh[0] / hn, nh[1] / hn, 0];
  var at = function (u, z, w) { var dz = z - fr.c[2], a = (w - fr.n[2] * dz) / ogsDot(fr.n, nh); return [fr.c[0] + u * fr.sv[0] + a * nh[0], fr.c[1] + u * fr.sv[1] + a * nh[1], z]; };
  var vol = 0, ton = 0, sAu = 0, sT = 0, vNear = 0, nCell = 0, area = res * res / Math.max(0.5, Math.sin(Math.max(30, pl.dip) * Math.PI / 180)), sg = +OGS.p.sg || 2.42, cut = +OGS.p.cut || 0.6, Tl = [];
  for (k = 0; k < nz; k++) { var rG = [], rT = [], rA = [], rW = [], rD = []; for (i = 0; i < nx; i++) { var u = xs[i], z = zs[k], dm = 1e9;
      for (var j = 0; j < U.length; j++) { var dd = Math.hypot(u - U[j], z - Zc[j]); if (dd < dm) dm = dd; }
      if (dm > maxD) { rG.push(null); rT.push(null); rA.push(null); rW.push(null); rD.push(null); continue; }
      var w = fW(u, z); if (Win) { var hit = false; for (var o = -3; o <= 3 && !hit; o += 1.5) { var P = at(u, z, w + o); if (Win.f(P[0], P[1], P[2])) hit = true; } if (!hit) { rG.push(null); rT.push(null); rA.push(null); rW.push(null); rD.push(null); continue; } }
      var g = Math.pow(10, fG(u, z)), t = Math.max(0.1, fT(u, z)), au_ = Math.pow(10, fA(u, z)); rG.push(g); rT.push(t); rA.push(au_); rW.push(w); rD.push(dm);
      if (g >= cut) { nCell++; vol += t * area; sAu += au_ * t; sT += t; Tl.push(t); if (dm <= nearD) vNear += t * area; } }
    GT.push(rG); TT.push(rT); AU.push(rA); WW.push(rW); DD.push(rD); }
  var E = { q: q, fr: fr, xs: xs, zs: zs, GT: GT, T: TT, AU: AU, W: WW, DD: DD, U: U, Zc: Zc, L: L, res: res, at: at, vol: vol, ton: vol * sg, au: sT > 0 ? sAu / sT : NaN, Tm: ogsMed(Tl), near: vol > 0 ? 100 * vNear / vol : NaN, nCell: nCell };
  OGS.E[q] = E; return E;
}

/* ---------- jendela ---------- */
var OGS_NAV = [['data', '1 · Data & domain'], ['geo', '2 · Geometri & tebal'], ['kadar', '3 · Kadar & multi-elemen'], ['ls', '4 · Long section'], ['env', '5 · Envelope RBF & 3D'], ['zon', '6 · Zonasi vertikal'], ['prof', '7 · Profil per domain'], ['sec', '8 · Penampang (sayatan)'],
  ['-', 'Alat lain'], ['lama', 'Intercept · LS GT · Ore shoot · Grade shell'], ['red', 'Profil Geostatistik & Slicer'], ['-', 'Tahap 2 (berikutnya)'], ['t2', 'Struktur · Pertemuan vein · Target · Laporan PDF']];
/* halaman & penggambar grafik per menu (ogs2_dh.js menambah halaman tahap 2) */
var OGS_PG = { data: ogsPgData, geo: ogsPgGeo, kadar: ogsPgKadar, ls: ogsPgLS, env: ogsPgEnv, zon: ogsPgZon, prof: ogsPgProf, sec: ogsPgSec, lama: ogsPgLama, red: ogsPgRed, t2: ogsPgT2 };
var OGS_DR = { data: ogsDrData, geo: ogsDrGeo, ls: ogsDrLS, env: ogsDrEnv, zon: ogsDrZon, prof: ogsDrProf, sec: ogsDrSec, lama: function () { try { ogPanel(); } catch (e) {} } };
function ogsOpen(nav) {
  if (!window.POP || !POP.win) { alert('Jendela pop-up tidak tersedia.'); return; }
  if (nav) OGS.nav = nav; OGS.open = true;
  var w = POP.win('ogsWin', 'Ore Geometry Studio', '<div class=ogsw><div class=ogsnav id=ogsNav></div><div class=ogsc id=ogsC></div></div>');
  if (!w._ogs) { w._ogs = 1; w.style.left = '60px'; w.style.top = '56px'; w.style.width = 'min(1320px,calc(100vw - 90px))'; w.style.height = 'calc(100vh - 90px)'; w.style.maxHeight = 'none';
    var x = w.querySelector('[data-x]'); var f = x.onclick; x.onclick = function () { OGS.open = false; if (f) f.apply(this, arguments); try { ogPanel(); } catch (e) {} ogsSide(); }; }
  ogsRender(); ogsSide();
}
function ogsGo(n) { OGS.nav = n; OGS.draw = null; ogsRender(); }
function ogsRender() {
  ogsSide(); var nv = $('ogsNav'), c = $('ogsC'); if (!nv || !c) return;
  nv.innerHTML = OGS_NAV.map(function (x) { return x[0] === '-' ? '<div class=ogsnh>' + x[1] + '</div>' : '<button class="' + (OGS.nav === x[0] ? 'on' : '') + (x[0] === 't2' ? ' dim' : '') + '" onclick="ogsGo(\'' + x[0] + '\')">' + x[1] + '</button>'; }).join('');
  var F = OGS.F, stale = F && F.key !== ogsKunci();
  var h = '<div class=ogsbar><button class=btn-pri onclick="ogsRun()">&#9654; ' + (F ? 'Hitung ulang' : 'Hitung flag domain &amp; intercept') + '</button>' + (stale ? ' <span class=warn>Data / wireframe berubah sejak dihitung: hitung ulang.</span>' : '') + (OGS.msg ? ' <span class=ogsmsg>' + OGS.msg + '</span>' : '') + '</div>';
  try { h += (OGS_PG[OGS.nav] || ogsPgData)(); }
  catch (e) { console.error(e); h += '<div class=warn>Galat: ' + ogsE(e.message) + '</div>'; }
  c.innerHTML = h; var sc = c.scrollTop;
  setTimeout(function () { try { (OGS_DR[OGS.nav] || function () {})(); } catch (e) { console.error(e); } c.scrollTop = sc; }, 0);
}
function ogsRun() { OGS.msg = 'Menghitung&hellip;'; ogsRender(); setTimeout(function () { try { ogsFlag(); } catch (e) { console.error(e); OGS.msg = '<span class=warn>Gagal: ' + ogsE(e.message) + '</span>'; } ogsRender(); }, 30); }
function ogsNeed() { return OGS.F ? '' : '<div class=hint>Tekan <b>Hitung flag domain &amp; intercept</b> dulu (atas).</div>'; }
function ogsSet(k, v, ulang) { OGS.p[k] = v; if (ulang === 'F') { ogsDirty(); return; } if (ulang === 'E') OGS.E = {}; if (ulang === 'fr' && OGS.F) { ogsFrame(OGS.F); OGS.E = {}; } try { if (window.SA && SA.dirty) SA.dirty(); } catch (e) {} ogsRender(); }
function ogsSel(oc, L, cur) { return '<select onchange="' + oc + '">' + L.map(function (o) { return '<option value="' + ogsE(o[0]) + '"' + (String(o[0]) === String(cur) ? ' selected' : '') + '>' + ogsE(o[1]) + '</option>'; }).join('') + '</select>'; }
function ogsNum(k, v, ulang, t) { return '<input type=number step=any value="' + ogsE(v) + '"' + (t ? ' title="' + ogsE(t) + '"' : '') + ' onchange="ogsSet(\'' + k + '\',+this.value,\'' + (ulang || '') + '\')">'; }
function ogsTab(head, rows, hl, id) { return '<table class=ogst' + (id ? ' id=' + id : '') + '><tr>' + head.map(function (x) { return '<th>' + x + '</th>'; }).join('') + '</tr>' + rows.map(function (r, i) { return '<tr' + ((hl || []).indexOf(i) >= 0 ? ' class=hl' : '') + '>' + r.map(function (x) { return '<td>' + x + '</td>'; }).join('') + '</tr>'; }).join('') + '</table>'; }
function ogsCsvBtn(id, nm) { return '<button class=ogsx onclick="ogsCsv(\'' + id + '\',\'' + nm + '\')">&#8681; CSV</button>'; }
function ogsCsv(id, nm) { var t = $(id); if (!t) return; var L = [].map.call(t.querySelectorAll('tr'), function (r) { return [].map.call(r.children, function (c) { var s = c.textContent.replace(/ /g, ' ').trim(); return /[",;]/.test(s) ? '"' + s.replace(/"/g, '""') + '"' : s; }).join(','); });
  gxDl(new Blob(['﻿' + L.join('\r\n')], { type: 'text/csv' }), 'OreGeometry_' + nm + '.csv'); }
function ogsPng(id, nm) { try { Plotly.downloadImage(id, { format: 'png', width: 1600, height: Math.round(1600 * ($(id).offsetHeight / Math.max(1, $(id).offsetWidth))), filename: 'OreGeometry_' + nm }); } catch (e) { alert('Gagal: ' + e.message); } }
function ogsFig(id, h, nm) { return '<div class=ogsfig><button class=ogsx onclick="ogsPng(\'' + id + '\',\'' + (nm || id) + '\')">&#8681; PNG</button><div id=' + id + ' style="height:' + h + 'px"></div></div>'; }
function ogsLog(v) { return v > 0 ? Math.log10(v) : null; }
function ogsCbar(lo, hi, t) { var tv = [], tt = []; for (var e = Math.floor(lo); e <= Math.ceil(hi); e++) { tv.push(e); tt.push(String(Math.pow(10, e)).replace('.', ',')); } return { title: { text: t, side: 'right' }, tickvals: tv, ticktext: tt, thickness: 12, len: 0.9 }; }

/* ---------- halaman 1: data & domain ---------- */
function ogsPgData() {
  var S = ogsSrc(), P = OGS.p, F = OGS.F, el = window.elements || [];
  var h = '<h3 class=ogsh>Data dan domain</h3><div class=hint>Flag otomatis: titik tengah setiap interval assay di dalam wireframe domain. <b>Urutan = prioritas</b> bila wireframe bertumpang. Sumber: solid GC-Ex (Mulai dari Nol) dan / atau wireframe impor (Lanjutkan). Hasil hanya dipakai Studio; tidak menulis flag Geomodeller.</div>';
  h += S.length ? '<table class=ogst><tr><th>Pakai</th><th>Prioritas</th><th>Domain (wireframe)</th><th>Sumber</th><th>Segitiga</th><th></th></tr>' + S.map(function (s, i) { return '<tr><td><input type=checkbox ' + (P.mesh[s.k] ? 'checked' : '') + ' onchange="OGS.p.mesh[\'' + s.k + '\']=this.checked;ogsDirty()"></td><td>' + (i + 1) + '</td><td><b>' + ogsE(s.nm) + '</b></td><td>' + s.j + '</td><td>' + ogsN(s.m.nt) + '</td><td><button class=x onclick="ogsMove(\'' + s.k + '\',-1)" title="Naikkan prioritas">&#9650;</button><button class=x onclick="ogsMove(\'' + s.k + '\',1)" title="Turunkan">&#9660;</button></td></tr>'; }).join('') + '</table>'
    : '<div class=warn>Belum ada wireframe domain. Mulai dari Nol: bangun solid di Geological Modelling. Lanjutkan: import wireframe di node Import Wireframe Geologi.</div>';
  h += '<div class="g4 f"><div><label>Sela gabung intercept (m)</label>' + ogsNum('gap', P.gap, 'F', 'Interval sedomain dalam satu lubang yang berjarak <= nilai ini digabung menjadi satu intercept') + '</div><div><label>Unsur utama (GT)</label>' + ogsSel("ogsSet('au',this.value,'F')", el.map(function (e) { return [e, e]; }), ogsAu()) + '</div><div><label>Unsur Ag (rasio Ag/Au)</label>' + ogsSel("ogsSet('ag',this.value,'')", [['', '(tidak ada)']].concat(el.map(function (e) { return [e, e]; })), ogsAg()) + '</div><div><label>SG (t/m³)</label>' + ogsNum('sg', P.sg, 'E') + '</div></div>';
  if (!F) return h + ogsNeed();
  var au = ogsEi(ogsAu()), rows = F.dom.map(function (d, q) { var idx = ogsIn(F, q), hs = {}; idx.forEach(function (i) { hs[F.A[i][0]] = 1; }); return [ogsE(d.nm), ogsN(idx.length), ogsN(Object.keys(hs).length), ogsN(d.nI), ogsAuto(ogsWmean(F, au, idx)), d.open ? '<span class=warn>terbuka</span>' : 'tertutup']; });
  var all = ogsIn(F), hsA = {}; all.forEach(function (i) { hsA[F.A[i][0]] = 1; });
  rows.push(['<b>Total</b>', '<b>' + ogsN(all.length) + '</b>', '<b>' + ogsN(Object.keys(hsA).length) + '</b>', '<b>' + ogsN(F.I.length) + '</b>', '<b>' + ogsAuto(ogsWmean(F, au, all)) + '</b>', '']);
  var cak = el.map(function (e, k) { var n = 0; all.forEach(function (i) { if (isFinite(F.V[k][i])) n++; }); return ogsE(e) + ' ' + (all.length ? Math.round(100 * n / all.length) : 0) + '%'; }).join(' · ');
  var zmin = 1e9, zmax = -1e9; all.forEach(function (i) { if (F.Z[i] < zmin) zmin = F.Z[i]; if (F.Z[i] > zmax) zmax = F.Z[i]; });
  h += '<div class=ogs2><div>' + ogsFig('ogsMap', 520, 'peta_domain') + '</div><div>' + ogsCsvBtn('ogsTD', 'domain') + ogsTab(['Domain', 'Sampel', 'Lubang', 'Intercept', ogsE(ogsAu()) + ' rata-rata', 'Wireframe'], rows, [rows.length - 1], 'ogsTD') +
    '<p class=ogscap>Cakupan unsur di vein: ' + cak + '.</p><p class=ogscap>Sampel vein RL ' + ogsN(zmin, 0) + '–' + ogsN(zmax, 0) + '. Total ' + ogsN(F.n) + ' interval assay, ' + ogsN(Object.keys(holeData).length) + ' lubang.</p>' + ogsCek(F) + '</div></div>';
  return h;
}
/* pemeriksaan data: hanya temuan, tidak ada perubahan otomatis */
function ogsCek(F) {
  var el = window.elements || [], L = [];
  el.forEach(function (e, k) { var c = F.V[k], neg = 0, z = 0, n = 0, v = []; for (var i = 0; i < F.n; i++) { var x = c[i]; if (!isFinite(x)) continue; n++; if (x < 0) neg++; else if (x === 0) z++; v.push(x); }
    if (!n) return; var p50 = ogsQ(v, 0.5), p999 = ogsQ(v, 0.999), mx = Math.max.apply(null, v.length > 2e5 ? v.slice(0, 2e5) : v);
    if (neg) L.push(ogsE(e) + ': ' + ogsN(neg) + ' nilai negatif (kode di bawah deteksi?)');
    if (z > 0.2 * n) L.push(ogsE(e) + ': ' + ogsN(z) + ' nilai nol (' + Math.round(100 * z / n) + '%)');
    if (p50 > 0 && mx > 1000 * p50 && mx > 10 * p999) L.push(ogsE(e) + ': nilai maks ' + ogsAuto(mx) + ' >> P99,9 ' + ogsAuto(p999) + ' (cek satuan / salah ketik)'); });
  return '<div class="box gmstate" style="margin-top:6px"><b>Pemeriksaan data</b> (hanya temuan; tidak ada data yang diubah)<br>' + (L.length ? L.map(function (s) { return '&bull; ' + s; }).join('<br>') : 'Tidak ada temuan.') + '</div>';
}
function ogsDrData() {
  var F = OGS.F, gd = $('ogsMap'); if (!F || !gd) return; var T = [], st = 3;
  var bg = { x: [], y: [] }; for (var i = 0; i < F.n; i += st) if (F.D[i] < 0) { bg.x.push(F.X[i] + offX); bg.y.push(F.Y[i] + offY); }
  T.push({ type: 'scattergl', mode: 'markers', x: bg.x, y: bg.y, marker: { size: 2, color: '#adb5bd' }, name: 'sampel lain', hoverinfo: 'skip' });
  F.dom.forEach(function (d, q) { var x = [], y = [], t = []; F.I.forEach(function (c) { if (c.d !== q) return; x.push(c.p[0] + offX); y.push(c.p[1] + offY); t.push(c.h + ' ' + ogsAuto(c.g[ogsEi(ogsAu())])); });
    T.push({ type: 'scattergl', mode: 'markers', x: x, y: y, text: t, marker: { size: 6, color: d.col, line: { width: 0.5, color: '#fff' } }, name: d.nm + ' (' + d.nI + ')' }); });
  Plotly.newPlot(gd, T, ogsLay({ title: { text: 'Peta intercept per domain', font: { size: 12 } }, showlegend: true, legend: { font: { size: 10 } }, xaxis: { title: 'Easting', tickformat: 'd' }, yaxis: { title: 'Northing', tickformat: 'd', scaleanchor: 'x' } }), OGS_CFG);
}

/* ---------- halaman 2: geometri & tebal ---------- */
function ogsGeoRows(F) { return F.dom.map(function (d, q) { var L = F.I.filter(function (c) { return c.d === q; }), pl = d.pl; if (!pl || !L.length) return { d: d, L: L };
    var fr = ogsMkFrame(pl), u = L.map(function (c) { return ogsDot([c.p[0] - fr.c[0], c.p[1] - fr.c[1], c.p[2] - fr.c[2]], fr.sv); }), z = L.map(function (c) { return c.p[2]; }), T = L.map(function (c) { return c.T; });
    return { d: d, L: L, pl: pl, len: Math.max.apply(null, u) - Math.min.apply(null, u), z0: Math.min.apply(null, z), z1: Math.max.apply(null, z), Tm: ogsMed(T), T10: ogsQ(T, 0.1), T90: ogsQ(T, 0.9) }; }); }
function ogsPgGeo() {
  var F = OGS.F; if (!F) return '<h3 class=ogsh>Geometri dan tebal</h3>' + ogsNeed();
  var G = ogsGeoRows(F), fr = F.fr, T = F.I.map(function (c) { return c.T; });
  var rows = G.map(function (g) { if (!g.pl) return [ogsE(g.d.nm), '–', '–', '–', '–', '–', ogsN(g.L.length), '–'];
    return [ogsE(g.d.nm), ogsAzTxt(g.pl.strike), ogsN(g.pl.dip, 0) + '° → ' + ogsArah(g.pl.ddir), ogsN(g.len, 0), ogsN(g.z1 - g.z0, 0), ogsN(g.z0, 0) + '–' + ogsN(g.z1, 0), ogsN(g.L.length), ogsN(g.Tm, 1) + ' (' + ogsN(g.T10, 1) + '–' + ogsN(g.T90, 1) + ')']; });
  return '<h3 class=ogsh>Geometri dan tebal</h3><div class=hint>Bidang per domain dari PCA titik tengah intercept (bobot panjang). Tebal sebenarnya = panjang intercept × |arah bor · normal bidang|. Bidang acuan (long section, penampang): ' +
    ogsSel("ogsSet('ref',this.value,'fr')", [['', 'otomatis (intercept terbanyak)']].concat(F.dom.filter(function (d) { return d.pl; }).map(function (d) { return [d.k, d.nm]; })), OGS.p.ref) + ' → strike ' + ogsAzTxt(fr.az) + ', dip ' + ogsN(fr.dip, 0) + '° ke ' + ogsAzTxt(fr.ddir) + ' (' + ogsArah(fr.ddir) + ').</div>' +
    ogsCsvBtn('ogsTG', 'geometri') + ogsTab(['Domain', 'Strike', 'Dip', 'Panjang (m)', 'Tinggi (m)', 'RL', 'Intercept', 'Tebal median (P10–P90) m'], rows, [F.ref], 'ogsTG') +
    '<p class=ogscap>Semua intercept: tebal median ' + ogsN(ogsMed(T), 2) + ' m (P10 ' + ogsN(ogsQ(T, 0.1), 2) + ', P90 ' + ogsN(ogsQ(T, 0.9), 2) + ').</p><div class=ogs2><div>' + ogsFig('ogsTh', 330, 'distribusi_tebal') + '</div><div>' + ogsFig('ogsTl', 330, 'tebal_long_section') + '</div></div>';
}
function ogsDrGeo() {
  var F = OGS.F; if (!F || !$('ogsTh')) return; var T = [];
  F.dom.forEach(function (d, q) { var v = F.I.filter(function (c) { return c.d === q; }).map(function (c) { return c.T; }); if (!v.length) return; T.push({ type: 'histogram', x: v, name: d.nm + ' (n=' + v.length + ', med ' + ogsN(ogsMed(v), 1) + ')', opacity: 0.55, marker: { color: d.col }, xbins: { size: 0.5 } }); });
  Plotly.newPlot('ogsTh', T, ogsLay({ barmode: 'overlay', showlegend: true, legend: { font: { size: 9 } }, title: { text: 'Distribusi tebal sebenarnya per domain', font: { size: 12 } }, xaxis: { title: 'tebal sebenarnya (m)' }, yaxis: { title: 'jumlah intercept' } }), OGS_CFG);
  var I = F.I.slice().sort(function (a, b) { return a.T - b.T; });
  Plotly.newPlot('ogsTl', [{ type: 'scattergl', mode: 'markers', x: I.map(function (c) { return c.ls; }), y: I.map(function (c) { return c.p[2]; }), text: I.map(function (c) { return c.h + ' · ' + F.dom[c.d].nm + ' · ' + ogsN(c.T, 2) + ' m'; }),
    marker: { size: 6, color: I.map(function (c) { return c.T; }), cmin: 0, cmax: Math.max(1, ogsQ(I.map(function (c) { return c.T; }), 0.95)), colorscale: 'Viridis', colorbar: { title: { text: 'tebal (m)', side: 'right' }, thickness: 12 } } }],
    ogsLay({ title: { text: 'Tebal sebenarnya pada long section', font: { size: 12 } }, xaxis: { title: 'jarak sepanjang strike (m) → ' + ogsAzTxt(F.fr.az) }, yaxis: { title: 'RL (m)' } }), OGS_CFG);
}

/* ---------- halaman 3: kadar & multi-elemen ---------- */
function ogsPgKadar() {
  var F = OGS.F; if (!F) return '<h3 class=ogsh>Kadar dan multi-elemen</h3>' + ogsNeed();
  var el = window.elements || [], vin = ogsIn(F), vout = ogsOut(F), au = ogsEi(ogsAu()), ag = ogsEi(ogsAg());
  var rows = el.map(function (e, k) { var v = ogsVals(F, k, vin); return [ogsE(e), ogsN(v.length), ogsAuto(ogsWmean(F, k, vin)), ogsAuto(ogsMed(v)), ogsAuto(ogsQ(v, 0.9)), ogsAuto(ogsMed(ogsVals(F, k, vout)))]; });
  var mIn = ogsMed(ogsVals(F, au, vin)), mOut = ogsMed(ogsVals(F, au, vout)), kon = mOut > 0 ? mIn / mOut : NaN;
  var sp = [], col = el.map(function (e, k) { return vin.map(function (i) { return F.V[k][i]; }); });
  for (var a = 0; a < el.length; a++) for (var b = a + 1; b < el.length; b++) { var r = ogsSpear(col[a], col[b]); if (isFinite(r)) sp.push([el[a] + '–' + el[b], r]); }
  sp.sort(function (x, y) { return Math.abs(y[1]) - Math.abs(x[1]); });
  var hd = ['Domain', ogsE(ogsAu())].concat(ag >= 0 ? [ogsE(el[ag]), 'Ag/Au'] : []).concat(el.filter(function (e, k) { return k !== au && k !== ag; }).slice(0, 4).map(ogsE)).concat(['GT rata-rata']);
  var dr = F.dom.map(function (d, q) { var idx = ogsIn(F, q), A = ogsWmean(F, au, idx), r = [ogsE(d.nm), ogsAuto(A)];
    if (ag >= 0) { var G = ogsWmean(F, ag, idx); r.push(ogsAuto(G), ogsAuto(A > 0 ? G / A : NaN)); }
    el.forEach(function (e, k) { if (k === au || k === ag) return; if (r.length >= hd.length - 1) return; var v = ogsVals(F, k, idx); r.push(ogsAuto(ogsWmean(F, k, idx)) + (v.length && v.length < 20 ? '*' : '')); });
    var g = F.I.filter(function (c) { return c.d === q && isFinite(c.gt); }).map(function (c) { return c.gt; }); r.push(ogsAuto(g.length ? g.reduce(function (s, v) { return s + v; }, 0) / g.length : NaN)); return r; });
  var h = '<h3 class=ogsh>Kadar dan multi-elemen</h3><div class=hint>Rata-rata tertimbang panjang; median luar vein = semua interval di luar wireframe domain. * = kurang dari 20 sampel.</div>' +
    '<div class=ogs2 style="grid-template-columns:1.3fr 1fr"><div>' + ogsCsvBtn('ogsTK', 'statistik_unsur') + ogsTab(['Unsur', 'n', 'Rata-rata', 'Median', 'P90', 'Median luar vein'], rows, [au], 'ogsTK') +
    '<div style="height:8px"></div>' + ogsCsvBtn('ogsTKD', 'kadar_domain') + ogsTab(hd, dr, [F.ref], 'ogsTKD') + '</div><div>' +
    '<div class=card><h4>Kontras ' + ogsE(ogsAu()) + '</h4><p><b>' + ogsN(kon, 0) + '×</b> (median ' + ogsAuto(mIn) + ' di vein vs ' + ogsAuto(mOut) + ' di luar)</p></div>' +
    '<div class=card><h4>Korelasi Spearman (vein)</h4><p>' + (sp.length ? sp.slice(0, 10).map(function (s) { return ogsE(s[0]) + ' <b>' + ogsN(s[1], 2) + '</b>'; }).join(' · ') : '–') + '</p></div>' + ogsGeoKartu(F, vin, vout) + '</div></div>';
  return h;
}
function ogsGeoCols() { return (window.CAT || []).map(function (c, i) { return { ci: i, c: c }; }).filter(function (o) { return o.c && o.c.src === 'g'; }); }
function ogsGeoKartu(F, vin, vout) {
  var G = ogsGeoCols(); if (!G.length) return '<div class=card><h4>Geologi di dalam vein</h4><p class=hint>Tidak ada kolom geologi.</p></div>';
  var P = OGS.p; if (!P.geoCols.length) P.geoCols = G.slice(0, 2).map(function (o) { return o.ci; });
  var au = ogsEi(ogsAu()), h = '<div class=card><h4>Geologi di dalam vein</h4><div class=hint>Kolom: ' + G.map(function (o) { return '<label class=sw style="display:inline-flex;margin-right:8px"><input type=checkbox ' + (P.geoCols.indexOf(o.ci) >= 0 ? 'checked' : '') + ' onchange="ogsGeoTog(' + o.ci + ',this.checked)">' + ogsE(o.c.name) + '</label>'; }).join('') + '</div>';
  P.geoCols.forEach(function (ci) { if (!CAT[ci]) return; var pct = function (idx) { var s = {}, t = 0; idx.forEach(function (i) { var a = F.A[i], c = catAssay(ci, a[0], a), l = a[2] - a[1]; if (c < 0) return; s[c] = (s[c] || 0) + l; t += l; }); return { s: s, t: t }; };
    var A = pct(vin), B = pct(vout), K = Object.keys(A.s).sort(function (x, y) { return A.s[y] - A.s[x]; }).slice(0, 6);
    var md = {}; K.forEach(function (k) { md[k] = ogsMed(vin.filter(function (i) { var a = F.A[i]; return String(catAssay(ci, a[0], a)) === k; }).map(function (i) { return F.V[au][i]; })); });
    h += '<p><b>' + ogsE(CAT[ci].name) + '</b>: ' + K.map(function (k) { return ogsE(geoName(ci, +k)) + ' ' + Math.round(100 * A.s[k] / A.t) + '% (' + ogsE(ogsAu()) + ' med ' + ogsAuto(md[k]) + ')'; }).join(', ') +
      '<br><span class=hint>Luar vein: ' + Object.keys(B.s).sort(function (x, y) { return B.s[y] - B.s[x]; }).slice(0, 4).map(function (k) { return ogsE(geoName(ci, +k)) + ' ' + Math.round(100 * B.s[k] / B.t) + '%'; }).join(', ') + '</span></p>'; });
  return h + '</div>';
}
function ogsGeoTog(ci, on) { var L = OGS.p.geoCols.filter(function (x) { return x !== ci; }); if (on) L.push(ci); OGS.p.geoCols = L; ogsRender(); }

/* ---------- halaman 4: long section multi-panel ---------- */
function ogsLsEls() { var P = OGS.p, el = window.elements || []; if (!P.lsEl.length) { P.lsEl = ['GT', ogsAu()]; [ogsAg(), ogsFind(/^cu/i)].forEach(function (e) { if (e && P.lsEl.indexOf(e) < 0) P.lsEl.push(e); }); }
  return P.lsEl.filter(function (e) { return e === 'GT' || el.indexOf(e) >= 0; }).slice(0, 6); }
function ogsPick(k, i, v) { var L = OGS.p[k].slice(); if (v === '') L.splice(i, 1); else L[i] = v; OGS.p[k] = L; ogsRender(); }
function ogsPickers(k, L, opts, max) { return L.map(function (e, i) { return ogsSel("ogsPick('" + k + "'," + i + ",this.value)", [['', '(hapus)']].concat(opts.map(function (o) { return [o, o]; })), e); }).join(' ') + (L.length < max ? ' ' + ogsSel("ogsPick('" + k + "'," + L.length + ",this.value)", [['', '+ panel']].concat(opts.map(function (o) { return [o, o]; })), '') : ''); }
function ogsPgLS() {
  var F = OGS.F; if (!F) return '<h3 class=ogsh>Long section</h3>' + ogsNeed();
  var L = ogsLsEls();
  return '<h3 class=ogsh>Long section vertikal</h3><div class=hint>Proyeksi ke bidang acuan (strike ' + ogsAzTxt(F.fr.az) + ', kanan = ' + ogsArah(F.fr.az) + ', lihat ke ' + ogsArah(F.fr.ddir) + '). GT = intercept; unsur = sampel di dalam vein. Titik abu kosong = unsur tidak dianalisis. Panel: ' +
    ogsPickers('lsEl', L, ['GT'].concat(window.elements || []), 6) + '</div>' + ogsFig('ogsLS', Math.ceil(L.length / 2) * 300, 'long_section');
}
function ogsSub(n, cols, o) { /* tata letak subplot manual */ var rows = Math.ceil(n / cols), L = {}, gx = 0.07 / cols * 2, gy = 0.12 / rows * 2; o = o || {};
  for (var i = 0; i < n; i++) { var r = Math.floor(i / cols), c = i % cols, x0 = c / cols + (c ? gx / 2 : 0), x1 = (c + 1) / cols - (c < cols - 1 ? gx / 2 : 0) - (o.cbw || 0.06), y1 = 1 - r / rows - (r ? gy / 2 : 0), y0 = 1 - (r + 1) / rows + (r < rows - 1 ? gy / 2 : 0), s = i ? String(i + 1) : '';
    L['xaxis' + s] = { domain: [x0, x1], anchor: 'y' + s, title: r === rows - 1 && o.xt ? { text: o.xt, font: { size: 10 } } : undefined, tickfont: { size: 9 } };
    L['yaxis' + s] = { domain: [y0, y1], anchor: 'x' + s, title: c === 0 && o.yt ? { text: o.yt, font: { size: 10 } } : undefined, tickfont: { size: 9 }, matches: o.ym && i ? 'y' : undefined };
    L['_cb' + i] = [x1 + 0.005, (y0 + y1) / 2, y1 - y0]; }
  return L; }
function ogsCleanL(L) { Object.keys(L).forEach(function (k) { if (k[0] === '_') delete L[k]; }); return L; }
function ogsDrLS() {
  var F = OGS.F, gd = $('ogsLS'); if (!F || !gd) return; var L = ogsLsEls(), Lay = ogsSub(L.length, 2, { xt: 'jarak sepanjang strike (m) → ' + ogsArah(F.fr.az), yt: 'RL (m)', ym: true }), T = [], ann = [], vin = ogsIn(F);
  L.forEach(function (e, i) { var s = i ? String(i + 1) : '', cb = Lay['_cb' + i], x = [], y = [], c = [], t = [], gx = [], gy = [];
    if (e === 'GT') F.I.forEach(function (q) { if (!isFinite(q.gt)) return; x.push(q.ls); y.push(q.p[2]); c.push(ogsLog(Math.max(0.01, q.gt))); t.push(q.h + ' · ' + F.dom[q.d].nm + ' · GT ' + ogsAuto(q.gt) + ' · T ' + ogsN(q.T, 2)); });
    else { var k = ogsEi(e); vin.forEach(function (j) { var v = F.V[k][j]; if (isFinite(v) && v > 0) { x.push(F.LS[j]); y.push(F.Z[j]); c.push(Math.log10(v)); t.push(F.A[j][0] + ' ' + ogsAuto(v)); } else { gx.push(F.LS[j]); gy.push(F.Z[j]); } }); }
    if (gx.length) T.push({ type: 'scattergl', mode: 'markers', x: gx, y: gy, xaxis: 'x' + s, yaxis: 'y' + s, marker: { size: 4, color: 'rgba(0,0,0,0)', line: { width: 0.6, color: '#adb5bd' } }, hoverinfo: 'skip' });
    var lo = ogsQ(c, 0.02), hi = ogsQ(c, 0.98); var ord = c.map(function (v, j) { return j; }).sort(function (a, b) { return c[a] - c[b]; });
    T.push({ type: 'scattergl', mode: 'markers', x: ord.map(function (j) { return x[j]; }), y: ord.map(function (j) { return y[j]; }), text: ord.map(function (j) { return t[j]; }), xaxis: 'x' + s, yaxis: 'y' + s,
      marker: { size: e === 'GT' ? 6 : 4, color: ord.map(function (j) { return c[j]; }), cmin: lo, cmax: hi, colorscale: 'Jet', colorbar: Object.assign(ogsCbar(lo, hi, e === 'GT' ? 'GT (' + ogsAu() + '×m)' : e), { x: cb[0], y: cb[1], len: cb[2], thickness: 10 }) } });
    ann.push({ text: e === 'GT' ? ogsE(ogsAu()) + ' × tebal sebenarnya' : ogsE(e), xref: 'x' + s + ' domain', yref: 'y' + s + ' domain', x: 0.5, y: 1.06, showarrow: false, font: { size: 11 } }); });
  Plotly.newPlot(gd, T, ogsLay(Object.assign(ogsCleanL(Lay), { annotations: ann, margin: { l: 54, r: 10, t: 30, b: 44 } })), OGS_CFG);
}

/* ---------- halaman 5: envelope RBF & 3D ---------- */
function ogsPgEnv() {
  var F = OGS.F; if (!F) return '<h3 class=ogsh>Envelope RBF grade × tebal</h3>' + ogsNeed();
  var P = OGS.p, D = F.dom.map(function (d, q) { return [q, d]; }).filter(function (x) { return x[1].nI >= 5 && x[1].pl; }), cur = +P.envDom; if (!D.some(function (x) { return x[0] === cur; })) cur = P.envDom = D.length ? (D.some(function (x) { return x[0] === F.ref; }) ? F.ref : D[0][0]) : -1;
  var h = '<h3 class=ogsh>Envelope RBF grade × tebal sebenarnya</h3><div class=hint>RBF linear (polinom derajat 1, smoothing) di bidang tiap domain: log GT, tebal, log ' + ogsE(ogsAu()) + ' dan posisi tegak lurus bidang. Grid hanya di dalam wireframe dan ≤ jarak maks dari intercept; arsir abu = lebih dari ' + ogsN(P.nearD) + ' m dari intercept. Gambaran geometri, <b>bukan estimasi sumber daya</b>.</div>' +
    '<div class="g6 f"><div><label>Domain</label>' + ogsSel("ogsSet('envDom',+this.value,'')", D.map(function (x) { return [x[0], x[1].nm]; }), cur) + '</div><div><label>Cut-off GT</label>' + ogsNum('cut', P.cut, 'E') + '</div><div><label>Resolusi (m)</label>' + ogsNum('res', P.res, 'E') + '</div><div><label>Jarak maks (m)</label>' + ogsNum('maxD', P.maxD, 'E') + '</div><div><label>Batas arsir (m)</label>' + ogsNum('nearD', P.nearD, 'E') + '</div><div><label>Smoothing</label>' + ogsNum('smooth', P.smooth, 'E') + '</div></div>';
  if (cur < 0) return h + '<div class=warn>Tidak ada domain dengan ≥ 5 intercept.</div>';
  var rows = D.map(function (x) { var E = ogsEnv(x[0]); return E ? [ogsE(x[1].nm), ogsN(E.vol), ogsN(E.ton), ogsAuto(E.au), ogsN(E.Tm, 1), ogsN(E.near, 0) + '%', ogsN(E.L.length)] : [ogsE(x[1].nm), '–', '–', '–', '–', '–', '–']; });
  return h + ogsFig('ogsEnv', 430, 'envelope_' + F.dom[cur].nm) + '<div class=ogs2 style="grid-template-columns:1fr 1fr"><div>' + ogsFig('ogs3D', 420, 'envelope_3D') + '</div><div>' + ogsCsvBtn('ogsTE', 'envelope') + ogsTab(['Domain', 'Volume (m³)', 'Tonase (t)', ogsE(ogsAu()) + ' RBF', 'Tebal median', '≤ ' + ogsN(P.nearD) + ' m data', 'Intercept'], rows, [D.map(function (x) { return x[0]; }).indexOf(cur)], 'ogsTE') +
    '<p class=ogscap>Volume = Σ tebal RBF × luas sel di bidang (sel GT ≥ ' + ogsAuto(+P.cut) + '); tonase × SG ' + ogsAuto(+P.sg) + '. Bagian yang jauh dari intercept ditentukan sedikit data.</p></div></div>';
}
function ogsDrEnv() {
  var F = OGS.F, gd = $('ogsEnv'); if (!F || !gd) return; var q = +OGS.p.envDom, E = ogsEnv(q); if (!E) return; var lg = E.GT.map(function (r) { return r.map(function (v) { return v == null ? null : Math.log10(Math.max(0.01, v)); }); }), cut = +OGS.p.cut || 0.6;
  var all = []; lg.forEach(function (r) { r.forEach(function (v) { if (v != null) all.push(v); }); }); var lo = ogsQ(all, 0.02), hi = ogsQ(all, 0.98);
  var far = E.DD.map(function (r) { return r.map(function (v) { return v != null && v > (+OGS.p.nearD || 25) ? 1 : null; }); });
  var T = [{ type: 'heatmap', x: E.xs, y: E.zs, z: lg, zmin: lo, zmax: hi, colorscale: 'Jet', colorbar: ogsCbar(lo, hi, 'GT'), hovertemplate: 'u %{x:.0f} m · RL %{y:.0f}<extra></extra>' },
    { type: 'heatmap', x: E.xs, y: E.zs, z: far, showscale: false, colorscale: [[0, 'rgba(90,90,90,0.38)'], [1, 'rgba(90,90,90,0.38)']], hoverinfo: 'skip' },
    { type: 'contour', x: E.xs, y: E.zs, z: E.GT.map(function (r) { return r.map(function (v) { return v == null ? null : v; }); }), showscale: false, contours: { start: cut, end: cut, size: 1, coloring: 'none' }, line: { color: '#000', width: 2.2 }, hoverinfo: 'skip' },
    { type: 'scatter', mode: 'markers', x: E.U, y: E.Zc, text: E.L.map(function (c) { return c.h + ' · GT ' + ogsAuto(c.gt) + ' · T ' + ogsN(c.T, 2); }), marker: { size: 5, color: '#fff', line: { width: 1, color: '#000' } } }];
  Plotly.newPlot(gd, T, ogsLay({ title: { text: F.dom[q].nm + ' · RBF GT · garis hitam = envelope GT ' + ogsAuto(cut) + ' · titik putih = intercept · arsir = > ' + ogsN(+OGS.p.nearD || 25) + ' m dari intercept', font: { size: 11 } }, xaxis: { title: 'jarak sepanjang strike domain (m) → ' + ogsArah(E.fr.az) }, yaxis: { title: 'RL (m)' } }), OGS_CFG);
  /* 3D: semua domain, sel GT >= cut, warna = Au RBF */
  var T3 = [], aLo = 1e9, aHi = -1e9;
  F.dom.forEach(function (d, k) { var e = ogsEnv(k); if (!e) return; e.AU.forEach(function (r) { r.forEach(function (v) { if (v != null) { var l = Math.log10(Math.max(0.01, v)); if (l < aLo) aLo = l; if (l > aHi) aHi = l; } }); }); });
  F.dom.forEach(function (d, k) { var e = ogsEnv(k); if (!e) return; var X = [], Y = [], Z = [], C = [];
    e.zs.forEach(function (z, r) { var rx = [], ry = [], rz = [], rc = []; e.xs.forEach(function (u, c) { var g = e.GT[r][c]; if (g == null || g < cut) { rx.push(null); ry.push(null); rz.push(null); rc.push(null); return; } var p = e.at(u, z, e.W[r][c]); rx.push(p[0] + offX); ry.push(p[1] + offY); rz.push(p[2]); rc.push(Math.log10(Math.max(0.01, e.AU[r][c]))); }); X.push(rx); Y.push(ry); Z.push(rz); C.push(rc); });
    T3.push({ type: 'surface', x: X, y: Y, z: Z, surfacecolor: C, cmin: aLo, cmax: aHi, colorscale: 'Jet', showscale: k === q, colorbar: ogsCbar(aLo, aHi, ogsAu() + ' RBF'), name: d.nm, hoverinfo: 'name' });
    T3.push({ type: 'scatter3d', mode: 'markers', x: e.L.map(function (c) { return c.p[0] + offX; }), y: e.L.map(function (c) { return c.p[1] + offY; }), z: e.L.map(function (c) { return c.p[2]; }), marker: { size: 1.8, color: '#000' }, hoverinfo: 'skip', showlegend: false }); });
  Plotly.newPlot('ogs3D', T3, ogsLay({ title: { text: 'Envelope 3D GT ≥ ' + ogsAuto(cut) + ' (tebal = RBF, warna = ' + ogsAu() + ' RBF)', font: { size: 11 } }, margin: { l: 0, r: 0, t: 30, b: 0 }, scene: { aspectmode: 'data', xaxis: { title: 'E' }, yaxis: { title: 'N' }, zaxis: { title: 'RL' } } }), OGS_CFG);
}

/* ---------- halaman 6: zonasi vertikal (vein vs halo) ---------- */
function ogsZEls() { var P = OGS.p; if (!P.zEls.length) { P.zEls = [ogsAu()]; if (ogsAg()) P.zEls.push(ogsAg(), 'Ag/Au'); [ogsFind(/^cu/i), ogsFind(/^zn/i)].forEach(function (e) { if (e) P.zEls.push(e); }); } return P.zEls.slice(0, 6); }
function ogsRatio(F, i) { var a = F.V[ogsEi(ogsAu())][i], g = ogsAg() ? F.V[ogsEi(ogsAg())][i] : NaN; return isFinite(a) && isFinite(g) && a >= (+OGS.p.rmin || 0.1) ? g / a : NaN; }
function ogsBand(F, idx, e, bw, mn, med) { var B = {}; idx.forEach(function (i) { var v = e === 'Ag/Au' ? ogsRatio(F, i) : F.V[ogsEi(e)][i]; if (!isFinite(v)) return; var k = Math.floor(F.Z[i] / bw), b = B[k] || (B[k] = { v: [], s: 0, w: 0 }); var l = F.A[i][2] - F.A[i][1]; b.v.push(v); b.s += v * l; b.w += l; });
  return Object.keys(B).map(Number).sort(function (a, b) { return a - b; }).filter(function (k) { return B[k].v.length >= mn; }).map(function (k) { var b = B[k]; return { z: (k + 0.5) * bw, v: med ? ogsMed(b.v) : b.s / b.w, n: b.v.length }; }); }
function ogsPgZon() {
  var F = OGS.F; if (!F) return '<h3 class=ogsh>Zonasi vertikal</h3>' + ogsNeed(); var P = OGS.p, vin = ogsIn(F), nb = vin.filter(function (i) { return F.Z[i] < (ogsQ(vin.map(function (j) { return F.Z[j]; }), 0.1)); }).length;
  return '<h3 class=ogsh>Zonasi vertikal: di dalam vein vs halo</h3><div class=hint>Median per pita RL (≥ 3 sampel; angka kecil = jumlah sampel). Halo = sampel di luar wireframe, ≤ jarak halo dari bidang acuan dan dalam rentang strike vein. Ag/Au hanya bila ' + ogsE(ogsAu()) + ' ≥ ' + ogsAuto(+P.rmin) + '. Panel: ' + ogsPickers('zEls', ogsZEls(), (window.elements || []).concat(ogsAg() ? ['Ag/Au'] : []), 6) + '</div>' +
    '<div class="g4 f"><div><label>Pita RL (m)</label>' + ogsNum('bw', P.bw) + '</div><div><label>Halo (m dari bidang)</label>' + ogsNum('halo', P.halo) + '</div><div><label>Ag/Au: ' + ogsE(ogsAu()) + ' min</label>' + ogsNum('rmin', P.rmin) + '</div></div>' + ogsFig('ogsZ', 470, 'zonasi_vertikal');
}
function ogsDrZon() {
  var F = OGS.F, gd = $('ogsZ'); if (!F || !gd) return; var P = OGS.p, vin = ogsIn(F), l0 = Math.min.apply(null, vin.map(function (i) { return F.LS[i]; })), l1 = Math.max.apply(null, vin.map(function (i) { return F.LS[i]; })), halo = [];
  for (var i = 0; i < F.n; i++) if (F.D[i] < 0 && Math.abs(F.Wd[i]) <= +P.halo && F.LS[i] >= l0 && F.LS[i] <= l1) halo.push(i);
  var L = ogsZEls(), n = L.length, T = [], Lay = {}, bw = Math.max(1, +P.bw || 10);
  L.forEach(function (e, k) { var s = k ? String(k + 1) : ''; Lay['xaxis' + s] = { domain: [k / n + 0.012, (k + 1) / n - 0.012], type: 'log', title: { text: e, font: { size: 10 } }, tickfont: { size: 8 } }; Lay['yaxis' + s] = { anchor: 'x' + s, matches: k ? 'y' : undefined, showticklabels: !k, title: k ? undefined : 'RL (m), pita ' + bw + ' m' };
    [[vin, '#e03131', 'di dalam vein'], [halo, '#1971c2', '≤ ' + P.halo + ' m dari vein (di luar vein)']].forEach(function (g, j) { var B = ogsBand(F, g[0], e, bw, 3, true).filter(function (b) { return b.v > 0; });
      T.push({ type: 'scatter', mode: 'lines+markers+text', x: B.map(function (b) { return b.v; }), y: B.map(function (b) { return b.z; }), text: B.map(function (b) { return ' ' + b.n; }), textposition: 'middle right', textfont: { size: 7, color: g[1] }, xaxis: 'x' + s, yaxis: 'y' + s, line: { color: g[1], width: 1.4 }, marker: { size: 4 }, name: g[2], showlegend: !k, legendgroup: g[2] }); }); });
  Plotly.newPlot(gd, T, ogsLay(Object.assign(Lay, { showlegend: true, legend: { orientation: 'h', y: -0.12, font: { size: 10 } }, margin: { l: 56, r: 10, t: 16, b: 60 } })), OGS_CFG);
}

/* ---------- halaman 7: profil per domain (format "Analisis Geostatistik Sayatan") ---------- */
function ogsPfDef() { var S = [{ t: 'el', a: ogsAu() }]; if (ogsAg()) S.push({ t: 'rat', a: ogsAg(), b: ogsAu() }); var pb = ogsFind(/^pb/i), zn = ogsFind(/^zn/i); if (pb && zn) S.push({ t: 'sum', a: pb, b: zn }); var cu = ogsFind(/^cu/i); if (cu) S.push({ t: 'el', a: cu });
  var G = ogsGeoCols(); if (G.length) { var o = G[0], cc = []; (o.c.d || []).forEach(function (nm, k) { if (/^(q|mv|rv|v)[a-z]*n$|vein|vbx|qvn|qcx/i.test(nm)) cc.push(k); }); S.push({ t: 'cat', ci: o.ci, c: cc }); } return S; }
function ogsPfLbl(s) { if (s.t === 'el') return s.a; if (s.t === 'rat') return s.a + '/' + s.b; if (s.t === 'sum') return s.a + '+' + s.b + ' '; var C = CAT[s.ci]; return '% ' + (s.c && s.c.length ? s.c.map(function (k) { return geoName(s.ci, k); }).join('+') : '?') + (C ? ' (' + C.name + ')' : ''); }
function ogsPf(i, k, v) { var S = OGS.p.pf; if (k === 'del') S.splice(i, 1); else if (k === 'add') S.push({ t: 'el', a: ogsAu() }); else { S[i][k] = v; if (k === 't') { if (v === 'cat') { var G = ogsGeoCols(); S[i].ci = G.length ? G[0].ci : -1; S[i].c = []; } else { S[i].a = S[i].a || ogsAu(); if (v !== 'el') S[i].b = S[i].b || ogsAu(); } } } ogsRender(); }
function ogsPfCode(i, c, on) { var s = OGS.p.pf[i]; s.c = (s.c || []).filter(function (x) { return x !== c; }); if (on) s.c.push(c); ogsRender(); }
function ogsPgProf() {
  var F = OGS.F; if (!F) return '<h3 class=ogsh>Profil vertikal per domain</h3>' + ogsNeed(); var P = OGS.p; if (!P.pf) P.pf = ogsPfDef(); var el = window.elements || [], G = ogsGeoCols();
  var o = function (cur) { return el.map(function (e) { return '<option' + (e === cur ? ' selected' : '') + '>' + ogsE(e) + '</option>'; }).join(''); };
  var ed = P.pf.map(function (s, i) { var isi = s.t === 'cat' ? '<select onchange="ogsPf(' + i + ',\'ci\',+this.value)">' + G.map(function (g) { return '<option value=' + g.ci + (g.ci === s.ci ? ' selected' : '') + '>' + ogsE(g.c.name) + '</option>'; }).join('') + '</select> ' + (CAT[s.ci] ? (CAT[s.ci].d || []).slice(0, 40).map(function (nm, k) { return '<label class=sw style="display:inline-flex;margin-right:6px"><input type=checkbox ' + ((s.c || []).indexOf(k) >= 0 ? 'checked' : '') + ' onchange="ogsPfCode(' + i + ',' + k + ',this.checked)">' + ogsE(nm) + '</label>'; }).join('') : '')
      : '<select onchange="ogsPf(' + i + ',\'a\',this.value)">' + o(s.a) + '</select>' + (s.t !== 'el' ? (s.t === 'rat' ? ' / ' : ' + ') + '<select onchange="ogsPf(' + i + ',\'b\',this.value)">' + o(s.b) + '</select>' : '');
    return '<tr><td>' + (i + 1) + '</td><td>' + ogsSel('ogsPf(' + i + ',\'t\',this.value)', [['el', 'Unsur'], ['rat', 'Rasio'], ['sum', 'Jumlah'], ['cat', '% kode geologi']].filter(function (q) { return q[0] !== 'cat' || G.length; }), s.t) + '</td><td>' + isi + '</td><td><button class=x onclick="ogsPf(' + i + ',\'del\')">&times;</button></td></tr>'; }).join('');
  return '<h3 class=ogsh>Profil vertikal per domain</h3><div class=hint>Format sama dengan <b>Geostatistik › Profil</b> ("Analisis Geostatistik Sayatan"): rata-rata tertimbang panjang per pita RL, pita &lt; 2 sampel tidak digambar. Data = sampel di dalam wireframe domain terpilih.</div>' +
    '<div class="g4 f"><div><label>Domain</label>' + ogsSel("ogsSet('pfDom',this.value,'')", [['', 'Semua vein']].concat(F.dom.map(function (d, q) { return [String(q), d.nm]; })), P.pfDom) + '</div><div><label>Pita RL (m)</label>' + ogsNum('bw', P.bw) + '</div></div>' +
    '<table class=ogst><tr><th>#</th><th>Jenis</th><th>Isi</th><th></th></tr>' + ed + '</table><button onclick="ogsPf(0,\'add\')"' + (P.pf.length >= 6 ? ' disabled' : '') + '>+ Panel</button>' + ogsFig('ogsPF', 470, 'profil_domain');
}
function ogsDrProf() {
  var F = OGS.F, gd = $('ogsPF'); if (!F || !gd) return; var P = OGS.p, S = P.pf || [], idx = P.pfDom === '' ? ogsIn(F) : ogsIn(F, +P.pfDom), bw = Math.max(1, +P.bw || 10), B = {};
  idx.forEach(function (i) { var k = Math.floor(F.Z[i] / bw), b = B[k] || (B[k] = { n: 0, v: S.map(function () { return [0, 0, 0, 0]; }) }), l = F.A[i][2] - F.A[i][1], a = F.A[i]; b.n++;
    S.forEach(function (s, j) { var q = b.v[j];
      if (s.t === 'cat') { var c = catAssay(s.ci, a[0], a); if (c >= 0) { q[1] += l; if ((s.c || []).indexOf(c) >= 0) q[0] += l; } return; }
      var x = F.V[ogsEi(s.a)][i]; if (isFinite(x)) { q[0] += x * l; q[1] += l; } if (s.t !== 'el') { var y = F.V[ogsEi(s.b)][i]; if (isFinite(y)) { q[2] += y * l; q[3] += l; } } }); });
  var K = Object.keys(B).map(Number).sort(function (a, b) { return a - b; }).filter(function (k) { return B[k].n >= 2; }), n = S.length, cols = ['#2f5d9e', '#c8902f', '#3f8a46', '#c0392b', '#8e44ad', '#16a085'], T = [], Lay = {};
  S.forEach(function (s, j) { var x = [], y = [], t = []; K.forEach(function (k) { var q = B[k].v[j], v; if (s.t === 'el') v = q[1] > 0 ? q[0] / q[1] : NaN; else if (s.t === 'rat') v = q[3] > 0 && q[2] > 0 ? (q[0] / q[1]) / (q[2] / q[3]) : NaN; else if (s.t === 'sum') v = q[1] > 0 && q[3] > 0 ? q[0] / q[1] + q[2] / q[3] : NaN; else v = q[1] > 0 ? 100 * q[0] / q[1] : NaN; if (isFinite(v)) { x.push(v); y.push((k + 0.5) * bw); t.push(' ' + B[k].n); } });
    var sx = j ? String(j + 1) : ''; Lay['xaxis' + sx] = { domain: [j / n + 0.015, (j + 1) / n - 0.015], title: { text: ogsPfLbl(s), font: { size: 10 } }, tickfont: { size: 9 }, rangemode: 'tozero' }; Lay['yaxis' + sx] = { anchor: 'x' + sx, matches: j ? 'y' : undefined, showticklabels: !j, title: j ? undefined : 'RL (m)' };
    T.push({ type: 'scatter', mode: 'lines+markers+text', x: x, y: y, text: t, textposition: 'middle right', textfont: { size: 7, color: '#868e96' }, xaxis: 'x' + sx, yaxis: 'y' + sx, line: { color: cols[j % 6], width: 1.6 }, marker: { size: 5 } }); });
  var nm = P.pfDom === '' ? 'semua vein' : F.dom[+P.pfDom].nm;
  Plotly.newPlot(gd, T, ogsLay(Object.assign(Lay, { title: { text: 'Profil vertikal per pita ' + bw + ' m · domain ' + nm + ' · ' + idx.length + ' interval (angka kecil = jumlah sampel)', font: { size: 11 } }, margin: { l: 56, r: 10, t: 34, b: 50 } })), OGS_CFG);
}

/* ---------- halaman 8: penampang (sayatan Studio, berdiri sendiri) ---------- */
function ogsSecDef() { var F = OGS.F, P = OGS.p; if (P.sec.length || !F) return; var L = F.I.filter(function (c) { return c.d === F.ref; }).map(function (c) { return c.ls; }); if (L.length < 3) L = F.I.map(function (c) { return c.ls; });
  [0.2, 0.5, 0.8].forEach(function (q, i) { P.sec.push({ nm: 'ABC'[i], ls: Math.round(ogsQ(L, q) / 10) * 10, az: null, win: 6 }); }); P.secI = 0; }
function ogsSecEls() { var P = OGS.p; if (!P.secEls.length) { P.secEls = [ogsAu()]; if (ogsAg()) P.secEls.push(ogsAg(), 'Ag/Au'); [ogsFind(/^cu/i), ogsFind(/^zn/i)].forEach(function (e) { if (e) P.secEls.push(e); }); }
  if (P.secGeo === -1) { var G = ogsGeoCols(), a = G.filter(function (o) { return /alt/i.test(o.c.name); })[0] || G[0]; P.secGeo = a ? a.ci : -2; } return P.secEls.slice(0, 6); }
function ogsSecGeom(s) { var F = OGS.F, az = s.az == null || s.az === '' ? F.fr.ddir : +s.az, r = az * Math.PI / 180, d = [Math.sin(r), Math.cos(r), 0], nn = [Math.cos(r), -Math.sin(r), 0], c = [F.fr.c[0] + s.ls * F.fr.sv[0], F.fr.c[1] + s.ls * F.fr.sv[1], F.fr.c[2]];
  if (ogsDot(nn, F.fr.sv) < 0) nn = nn.map(function (v) { return -v; }); return { az: az, d: d, nn: nn, c: c }; }
function ogsSecSet(k, v) { var s = OGS.p.sec[OGS.p.secI]; if (!s) return; s[k] = v; ogsRender(); }
function ogsSecStep(dir) { var s = OGS.p.sec[OGS.p.secI]; if (!s) return; s.ls = Math.round((+s.ls + dir * 2 * (+s.win || 6)) * 10) / 10; ogsRender(); }
function ogsSecAdd() { var P = OGS.p, nm = prompt('Nama sayatan baru:', String.fromCharCode(65 + P.sec.length)); if (!nm) return; var cur = P.sec[P.secI]; P.sec.push({ nm: nm, ls: cur ? +cur.ls + 20 : 0, az: cur ? cur.az : null, win: cur ? cur.win : 6 }); P.secI = P.sec.length - 1; ogsRender(); }
function ogsSecDel() { var P = OGS.p; if (!P.sec.length) return; P.sec.splice(P.secI, 1); P.secI = Math.max(0, P.secI - 1); ogsRender(); }
function ogsSecUsul() { var F = OGS.F, P = OGS.p; if (!F) return; var B = {}; F.I.forEach(function (c) { var k = Math.round(c.ls / 20) * 20; B[k] = (B[k] || 0) + (isFinite(c.gt) ? 1 + Math.min(5, c.gt) : 1); });
  var K = Object.keys(B).map(Number).sort(function (a, b) { return B[b] - B[a]; }), pick = []; K.forEach(function (k) { if (pick.length < 3 && pick.every(function (p) { return Math.abs(p - k) >= 60; })) pick.push(k); }); pick.sort(function (a, b) { return a - b; });
  P.sec = pick.map(function (k, i) { return { nm: 'ABC'[i], ls: k, az: null, win: 6 }; }); P.secI = 0; ogsRender(); }
function ogsPgSec() {
  var F = OGS.F; if (!F) return '<h3 class=ogsh>Penampang</h3>' + ogsNeed(); ogsSecDef(); var P = OGS.p, s = P.sec[P.secI], L = ogsSecEls(), G = ogsGeoCols();
  var h = '<h3 class=ogsh>Penampang (sayatan Studio)</h3><div class=hint>Sayatan Studio berdiri sendiri (tidak menggerakkan Slicer 3D). Bawaan tegak lurus strike bidang acuan (arah ' + ogsAzTxt(F.fr.ddir) + '); posisi = jarak sepanjang strike dari pusat bidang acuan. Garis hitam = potongan wireframe domain; lingkaran berwarna = sampel vein per domain. Panel: ' +
    ogsPickers('secEls', L, (window.elements || []).concat(ogsAg() ? ['Ag/Au'] : []), 6) + ' · geologi: ' + ogsSel("ogsSet('secGeo',+this.value,'')", [[-2, '(tanpa)']].concat(G.map(function (o) { return [o.ci, o.c.name]; })), P.secGeo) + '</div>';
  h += '<div class=ogssec>' + P.sec.map(function (q, i) { return '<button class="' + (i === P.secI ? 'on' : '') + '" onclick="OGS.p.secI=' + i + ';ogsRender()">' + ogsE(q.nm) + ' · ' + (q.ls > 0 ? '+' : '') + ogsN(q.ls, 0) + ' m</button>'; }).join('') +
    '<button onclick="ogsSecAdd()">+ Sayatan</button><button onclick="ogsSecUsul()" title="3 posisi dengan intercept terbanyak / GT tertinggi, berjarak ≥ 60 m">&#9881; Usulkan sayatan</button><button class="' + (OGS.draw ? 'btn-pri' : '') + '" onclick="OGS.draw=OGS.draw?null:{a:null};ogsRender()">' + (OGS.draw ? '&#9679; Klik 2 titik di peta…' : '&#9998; Gambar di peta') + '</button>' + (P.sec.length ? '<button class=x onclick="ogsSecDel()" title="Hapus sayatan aktif">&times;</button>' : '') + '</div>';
  if (!s) return h + '<div class=hint>Belum ada sayatan.</div>';
  var g = ogsSecGeom(s);
  h += '<div class="g6 f"><div><label>Nama</label><input type=text value="' + ogsE(s.nm) + '" onchange="ogsSecSet(\'nm\',this.value)"></div><div><label>Posisi sepanjang strike (m)</label><input type=number step=any value="' + s.ls + '" onchange="ogsSecSet(\'ls\',+this.value)"></div><div><label>Azimuth sayatan (°, kosong = tegak lurus)</label><input type=number step=any value="' + (s.az == null ? '' : s.az) + '" placeholder="' + ogsN(F.fr.ddir, 0) + '" onchange="ogsSecSet(\'az\',this.value===\'\'?null:+this.value)"></div><div><label>Lebar jendela ± (m)</label><input type=number step=any value="' + s.win + '" onchange="ogsSecSet(\'win\',+this.value)"></div><div><label>&nbsp;</label><span><button onclick="ogsSecStep(-1)">&#9664; Mundur</button><button onclick="ogsSecStep(1)">Maju &#9654;</button></span></div><div class=hint style="align-self:end">pusat E ' + ogsN(g.c[0] + offX, 0) + ' N ' + ogsN(g.c[1] + offY, 0) + ' · arah ' + ogsAzTxt(g.az) + '</div></div>';
  return h + '<div class=ogs2 style="grid-template-columns:1fr 3.2fr"><div>' + ogsFig('ogsSM', 520, 'peta_sayatan') + '</div><div>' + ogsFig('ogsSP', 520, 'penampang_' + s.nm) + '</div></div><div id=ogsSecTab></div>';
}
function ogsSecData(s) { var F = OGS.F, g = ogsSecGeom(s), w = Math.max(0.5, +s.win || 6), I = [];
  for (var i = 0; i < F.n; i++) { var r = [F.X[i] - g.c[0], F.Y[i] - g.c[1], 0]; if (Math.abs(ogsDot(r, g.nn)) <= w) I.push({ i: i, x: ogsDot(r, g.d) }); } return { g: g, I: I, w: w }; }
function ogsDrSec() {
  var F = OGS.F, P = OGS.p, s = P.sec[P.secI]; if (!F || !s || !$('ogsSP')) return; var S = ogsSecData(s), g = S.g, L = ogsSecEls(), geo = P.secGeo >= 0 && CAT[P.secGeo] ? P.secGeo : -1, n = L.length + (geo >= 0 ? 1 : 0);
  /* peta */
  var M = [], bx = [], by = []; for (var i = 0; i < F.n; i += 2) { bx.push(F.X[i] + offX); by.push(F.Y[i] + offY); }
  M.push({ type: 'scattergl', mode: 'markers', x: bx, y: by, marker: { size: 2, color: '#ced4da' }, hoverinfo: 'skip' });
  F.dom.forEach(function (d, q) { var I = F.I.filter(function (c) { return c.d === q; }); M.push({ type: 'scattergl', mode: 'markers', x: I.map(function (c) { return c.p[0] + offX; }), y: I.map(function (c) { return c.p[1] + offY; }), marker: { size: 4, color: d.col }, hoverinfo: 'skip' }); });
  var ext = 80; P.sec.forEach(function (q, k) { var G = ogsSecGeom(q); M.push({ type: 'scatter', mode: 'lines+text', x: [G.c[0] - G.d[0] * ext + offX, G.c[0] + G.d[0] * ext + offX], y: [G.c[1] - G.d[1] * ext + offY, G.c[1] + G.d[1] * ext + offY], text: [q.nm, ''], textposition: 'top left', line: { color: k === P.secI ? '#e03131' : '#1f2d6b', width: k === P.secI ? 2.5 : 1.2 } }); });
  if (OGS.draw && OGS.draw.a) M.push({ type: 'scatter', mode: 'markers', x: [OGS.draw.a[0]], y: [OGS.draw.a[1]], marker: { size: 10, color: '#e03131', symbol: 'x' } });
  Plotly.newPlot('ogsSM', M, ogsLay({ title: { text: 'Peta sayatan', font: { size: 11 } }, margin: { l: 46, r: 6, t: 26, b: 30 }, xaxis: { tickformat: 'd', tickfont: { size: 8 } }, yaxis: { tickformat: 'd', tickfont: { size: 8 }, scaleanchor: 'x' }, dragmode: OGS.draw ? false : 'pan' }), OGS_CFG);
  var gm = $('ogsSM'); if (!gm._ogs) { gm._ogs = 1; gm.addEventListener('click', function (e) { if (!OGS.draw) return; var xa = gm._fullLayout.xaxis, ya = gm._fullLayout.yaxis, r = gm.getBoundingClientRect(), x = xa.p2l(e.clientX - r.left - xa._offset), y = ya.p2l(e.clientY - r.top - ya._offset);
      if (!OGS.draw.a) { OGS.draw.a = [x, y]; ogsDrSec(); return; } var a = OGS.draw.a; OGS.draw = null; var dx = x - a[0], dy = y - a[1]; if (Math.hypot(dx, dy) < 1) { ogsRender(); return; }
      var az = ((Math.atan2(dx, dy) * 180 / Math.PI) + 360) % 360, mx = (a[0] + x) / 2 - offX, my = (a[1] + y) / 2 - offY, ls = ogsDot([mx - F.fr.c[0], my - F.fr.c[1], 0], F.fr.sv);
      var t = OGS.p.sec[OGS.p.secI]; if (!t) { OGS.p.sec.push(t = { nm: 'A', win: 6 }); OGS.p.secI = 0; } t.ls = Math.round(ls); t.az = Math.round(az); ogsRender(); }); }
  /* panel penampang */
  var Lay = ogsSub(n, n, { yt: 'RL (m)', ym: true, cbw: 0 }), T = [], ann = [], hs = {};
  S.I.forEach(function (o) { hs[F.A[o.i][0]] = 1; });
  /* jejak lubang di jendela */
  var tr = { x: [], y: [] }; Object.keys(hs).forEach(function (h) { var p = holeData[h].path; for (var k = 0; k + 1 < p.length; k++) { var a = p[k], b = p[k + 1]; [a, b].forEach(function (q) { tr.x.push(ogsDot([q.x - g.c[0], q.y - g.c[1], 0], g.d)); tr.y.push(q.z); }); tr.x.push(null); tr.y.push(null); } });
  /* potongan wireframe */
  var cut = { x: [], y: [] }; F.dom.forEach(function (d) { try { wfSlice(d.m, { n: g.nn, c: g.c }, 0).forEach(function (l) { var P = l.closed ? l.p.concat([l.p[0]]) : l.p; P.forEach(function (q) { cut.x.push(ogsDot([q[0] - g.c[0], q[1] - g.c[1], 0], g.d)); cut.y.push(q[2]); }); cut.x.push(null); cut.y.push(null); }); } catch (e) {} });
  var panels = L.slice(); if (geo >= 0) panels.push('#geo');
  panels.forEach(function (e, k) { var sx = k ? String(k + 1) : '', x = [], y = [], c = [], t = [];
    T.push({ type: 'scattergl', mode: 'lines', x: tr.x, y: tr.y, xaxis: 'x' + sx, yaxis: 'y' + sx, line: { color: '#ced4da', width: 1 }, hoverinfo: 'skip', connectgaps: false });
    if (e === '#geo') { var C = {}; S.I.forEach(function (o) { var a = F.A[o.i], v = catAssay(geo, a[0], a); if (v < 0) return; (C[v] = C[v] || { x: [], y: [] }).x.push(o.x); C[v].y.push(F.Z[o.i]); });
      Object.keys(C).sort(function (a, b) { return C[b].x.length - C[a].x.length; }).forEach(function (v, j) { T.push({ type: 'scattergl', mode: 'markers', x: C[v].x, y: C[v].y, xaxis: 'x' + sx, yaxis: 'y' + sx, marker: { size: 5, color: BXCAT[j % BXCAT.length] }, name: geoName(geo, +v), showlegend: true }); }); }
    else { S.I.forEach(function (o) { var v = e === 'Ag/Au' ? ogsRatio(F, o.i) : F.V[ogsEi(e)][o.i]; if (!(v > 0)) return; x.push(o.x); y.push(F.Z[o.i]); c.push(Math.log10(v)); t.push(F.A[o.i][0] + ' ' + ogsAuto(v)); });
      var lo = ogsQ(c, 0.02), hi = ogsQ(c, 0.98), ord = c.map(function (v, j) { return j; }).sort(function (a, b) { return c[a] - c[b]; }), dm = Lay['xaxis' + sx].domain;
      T.push({ type: 'scattergl', mode: 'markers', x: ord.map(function (j) { return x[j]; }), y: ord.map(function (j) { return y[j]; }), text: ord.map(function (j) { return t[j]; }), xaxis: 'x' + sx, yaxis: 'y' + sx, marker: { size: 5, color: ord.map(function (j) { return c[j]; }), cmin: lo, cmax: hi, colorscale: 'Jet', colorbar: Object.assign(ogsCbar(lo, hi, ''), { orientation: 'h', x: (dm[0] + dm[1]) / 2, xanchor: 'center', y: -0.08, yanchor: 'top', len: dm[1] - dm[0], thickness: 8, title: { text: e, side: 'top' }, tickfont: { size: 8 } }) } }); }
    F.dom.forEach(function (d, q) { var xs = [], ys = []; S.I.forEach(function (o) { if (F.D[o.i] === q) { xs.push(o.x); ys.push(F.Z[o.i]); } }); if (xs.length) T.push({ type: 'scattergl', mode: 'markers', x: xs, y: ys, xaxis: 'x' + sx, yaxis: 'y' + sx, marker: { size: 8, color: 'rgba(0,0,0,0)', line: { width: 1.2, color: d.col } }, hoverinfo: 'skip', name: d.nm, showlegend: k === 0 }); });
    T.push({ type: 'scattergl', mode: 'lines', x: cut.x, y: cut.y, xaxis: 'x' + sx, yaxis: 'y' + sx, line: { color: '#111', width: 1 }, hoverinfo: 'skip', connectgaps: false });
    ann.push({ text: e === '#geo' ? ogsE(CAT[geo].name) : ogsE(e), xref: 'x' + sx + ' domain', yref: 'y' + sx + ' domain', x: 0.5, y: 1.04, showarrow: false, font: { size: 11 } }); });
  T.forEach(function (t) { if (t.showlegend === undefined) t.showlegend = false; });
  var xr = S.I.map(function (o) { return o.x; }), x0 = ogsQ(xr, 0.01), x1 = ogsQ(xr, 0.99); panels.forEach(function (e, k) { var sx = k ? String(k + 1) : ''; Lay['xaxis' + sx].range = isFinite(x0) ? [Math.max(x0, -80), Math.min(x1, 80)] : undefined; });
  Plotly.newPlot('ogsSP', T, ogsLay(Object.assign(ogsCleanL(Lay), { annotations: ann, title: { text: 'Penampang ' + s.nm + ' (x = jarak di sayatan, m → ' + ogsAzTxt(g.az) + '), pusat ' + (s.ls > 0 ? '+' : '') + ogsN(s.ls, 0) + ' m sepanjang strike · jendela ±' + S.w + ' m · ' + Object.keys(hs).length + ' lubang · garis hitam = wireframe domain', font: { size: 11 } }, showlegend: true, legend: { font: { size: 9 }, x: 1.005, xanchor: 'left', y: 1 }, margin: { l: 50, r: 120, t: 46, b: 70 } })), OGS_CFG);
  /* tabel: sampel terbaik & run >= cut di luar vein */
  var au = ogsEi(ogsAu()), ag = ogsEi(ogsAg()), cut0 = 0.5, best = S.I.filter(function (o) { return isFinite(F.V[au][o.i]); }).sort(function (a, b) { return F.V[au][b.i] - F.V[au][a.i]; }).slice(0, 6);
  var runs = [], byH = {}; S.I.forEach(function (o) { (byH[F.A[o.i][0]] = byH[F.A[o.i][0]] || []).push(o.i); });
  Object.keys(byH).forEach(function (h) { var cur = null; byH[h].sort(function (a, b) { return F.A[a][1] - F.A[b][1]; }).forEach(function (i) { var v = F.V[au][i]; if (F.D[i] < 0 && v >= cut0) { if (cur) cur.r.push(i); else cur = { h: h, r: [i] }; } else if (cur) { runs.push(cur); cur = null; } }); if (cur) runs.push(cur); });
  runs.forEach(function (r) { r.n = r.r.length; r.m = ogsWmean(F, au, r.r); r.z0 = Math.min.apply(null, r.r.map(function (i) { return F.Z[i]; })); r.z1 = Math.max.apply(null, r.r.map(function (i) { return F.Z[i]; })); }); runs.sort(function (a, b) { return b.n * b.m - a.n * a.m; });
  var tb = $('ogsSecTab'); if (tb) tb.innerHTML = '<div class=ogs2><div><h4>Sampel ' + ogsE(ogsAu()) + ' tertinggi di sayatan</h4>' + ogsTab(['HoleID', 'RL', ogsE(ogsAu())].concat(ag >= 0 ? [ogsE(ogsAg())] : []).concat(['Domain']), best.map(function (o) { return [ogsE(F.A[o.i][0]), ogsN(F.Z[o.i], 1), '<b>' + ogsAuto(F.V[au][o.i]) + '</b>'].concat(ag >= 0 ? [ogsAuto(F.V[ag][o.i])] : []).concat([F.D[o.i] >= 0 ? ogsE(F.dom[F.D[o.i]].nm) : '<span class=warn>di luar</span>']); })) + '</div>' +
    '<div><h4>' + ogsE(ogsAu()) + ' ≥ ' + cut0 + ' di luar wireframe domain</h4>' + (runs.length ? ogsTab(['HoleID', 'Sampel', 'Rata-rata', 'RL'], runs.slice(0, 6).map(function (r) { return [ogsE(r.h), r.n, ogsAuto(r.m), ogsN(r.z0, 0) + '–' + ogsN(r.z1, 0)]; })) : '<p class=hint>Tidak ada.</p>') + '</div></div>';
}

/* ---------- alat lain ---------- */
function ogsPgLama() { return '<h3 class=ogsh>Alat Ore Geometry sebelumnya</h3><div class=hint>Intercept &amp; GT per bor, Long section GT (tampil di viewer utama), Ore shoot (pitch / plunge), Grade shell 3D. Sama dengan isi panel samping sebelum versi 0.24.72.</div><div id=ogBody class=ogslama></div>'; }
function ogsPgRed() { return '<h3 class=ogsh>Profil Geostatistik &amp; Slicer</h3><div class=hint>Menu yang sama juga ada di tempat asalnya (menu redundan, izin pemilik). Profil Studio (halaman 7) memakai format yang sama dengan Geostatistik › Profil, tetapi datanya dibatasi ke wireframe domain.</div>' +
    '<div class="g2 f"><button onclick="ogsBukaProfil()">Buka Geostatistik › Profil</button><button onclick="ogsBukaSlicer()">Buka Slicer / Sayatan (bilah atas)</button></div><p class=hint>Slicer menggerakkan tampilan 3D / 2D utama; sayatan Studio (halaman 8) tidak.</p>'; }
function ogsBukaProfil() { try { if (window.GS && !GS.open && typeof gsToggle === 'function') gsToggle(); if (typeof gsTab === 'function') gsTab('P'); } catch (e) { console.error(e); } }
function ogsBukaSlicer() { var b = $('btnSecM'); if (b) b.click(); else alert('Tombol Slicer tidak ditemukan di bilah atas.'); }
function ogsPgT2() { return '<h3 class=ogsh>Tahap 2</h3><div class=hint>Direncanakan (keputusan pemilik 11 Nov 2026): long section struktur (collar, dasar GC, puncak ore, zona belum teruji) dengan <b>garis interpretasi</b> buatan geologist (nama, warna, legenda), struktur paralel &amp; tekukan, <b>pertemuan vein</b> (GT &amp; ' + ogsE(ogsAu()) + ' zona gabungan), target bor, sampel ≥ cut-off di luar vein, dan laporan PDF bertemplate deck.</div>'; }

/* ---------- panel samping: ringkasan + tombol pembuka ---------- */
function ogsSide() { var b = $('ogsSide'); if (!b) return; var F = OGS.F;
  b.innerHTML = '<div class=hint style="margin-top:-2px"><b>Referensi geologist</b>: geometri, kadar, zonasi dan penampang vein. Semua menu ada di jendela <b>Ore Geometry Studio</b>. Hasilnya tidak dipakai Geological Modelling maupun Model Estimation.</div>' +
    '<button class=btn-pri style="width:100%" onclick="ogsOpen()">&#10697; Buka Ore Geometry Studio</button>' +
    (F ? '<div class="box gmstate" style="margin-top:6px">' + F.dom.length + ' domain · ' + ogsN(F.I.length) + ' intercept · bidang acuan strike ' + ogsAzTxt(F.fr.az) + ', dip ' + ogsN(F.fr.dip, 0) + '° → ' + ogsArah(F.fr.ddir) + (F.key !== ogsKunci() ? '<br><span class=warn>Data / wireframe berubah: hitung ulang di Studio.</span>' : '') + '</div>' : '<div class=hint style="margin-top:6px">Belum dihitung.</div>') +
    '<div class=ogsq>' + OGS_NAV.filter(function (x) { return x[0] !== '-' && x[0] !== 't2'; }).map(function (x) { return '<a href=javascript:void(0) onclick="ogsOpen(\'' + x[0] + '\')">' + x[1] + '</a>'; }).join('') + '</div>'; }

/* ---------- pasang ---------- */
(function () {
  var st = document.createElement('style');
  st.textContent = '#ogsWin .gxpb{padding:0;overflow:hidden;display:flex}.ogsw{display:flex;width:100%;height:100%;min-height:0}.ogsnav{width:220px;flex:none;border-right:1px solid var(--bd,#dee2e6);padding:8px;overflow:auto;background:var(--sf,#f8f9fa)}' +
    '.ogsnav button{display:block;width:100%;text-align:left;margin:2px 0;padding:6px 8px;font-size:12px;border-radius:6px}.ogsnav button.on{background:#1f2d6b;color:#fff}.ogsnav button.dim{opacity:.6}.ogsnh{font-size:10.5px;text-transform:uppercase;letter-spacing:.4px;color:#8a6d00;margin:10px 4px 2px;font-weight:700}' +
    '.ogsc{flex:1;min-width:0;overflow:auto;padding:10px 14px;font-size:12px}.ogsh{margin:6px 0 4px;color:#1f2d6b;font-size:16px}.ogsbar{position:sticky;top:-10px;background:var(--bg,#fff);z-index:3;padding:4px 0 6px;border-bottom:1px solid var(--bd,#e9ecef);margin:-10px 0 6px}.ogsmsg{font-size:11.5px}' +
    '.ogs2{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-top:8px}.ogsfig{position:relative;border:1px solid var(--bd,#e9ecef);border-radius:8px;margin-top:6px}.ogsfig .ogsx{position:absolute;right:4px;top:4px;z-index:4}.ogsx{font-size:11px;padding:1px 6px;float:right}' +
    'table.ogst{border-collapse:collapse;width:100%;font-size:11.5px;margin-top:4px}table.ogst th{background:#1f2d6b;color:#fff;text-align:left;padding:4px 6px;font-weight:600}table.ogst td{padding:4px 6px;border-bottom:1px solid var(--bd,#e9ecef)}table.ogst tr.hl td{background:#fff5d6;font-weight:700}body.dark table.ogst tr.hl td{background:#3d3418}' +
    '.ogscap{font-size:11.5px;color:#5b6478;margin:6px 0}.ogsc .card{border:1px solid var(--bd,#e3e6ec);border-radius:8px;padding:8px 10px;margin-bottom:8px}.ogsc .card h4{margin:0 0 4px;color:#1f2d6b}.ogsc .card p{margin:2px 0}' +
    '.g4{display:grid;grid-template-columns:repeat(4,1fr);gap:8px}.g6{display:grid;grid-template-columns:repeat(6,1fr);gap:8px}.ogssec{display:flex;flex-wrap:wrap;gap:4px;margin:6px 0}.ogssec button.on{background:#1f2d6b;color:#fff}.ogsq a{display:block;font-size:12px;margin:3px 0}.ogsc .hint select,.ogsc table.ogst select{width:auto!important;max-width:240px;display:inline-block;margin:1px 2px;padding:1px 4px;font-size:11.5px;height:auto}.ogsc table.ogst input[type=checkbox]{width:auto}.ogslama{max-width:560px}';
  document.head.appendChild(st);
  var tunggu = function () { var p = $('pOG'); if (!p) return setTimeout(tunggu, 300); if ($('ogsSide')) return; var b = $('ogBody'); if (b) b.remove(); var s = document.createElement('div'); s.id = 'ogsSide'; p.appendChild(s); ogsSide(); };
  tunggu();
  /* ogPanel lama: hanya menggambar bila halaman "Alat lama" Studio terbuka; ringkasan samping selalu diperbarui */
  if (typeof ogPanel === 'function') { var _o = ogPanel; ogPanel = window.ogPanel = function () { var r = _o.apply(this, arguments); try { ogsSide(); } catch (e) {} return r; }; }
  var _c = SA.collectWork; SA.collectWork = function () { var w = _c.apply(this, arguments); try { w.ogs = { p: JSON.parse(JSON.stringify(OGS.p)) }; } catch (e) {} return w; };
  var _a = SA.applyWork; SA.applyWork = function (W) { try { if (W && W.ogs && W.ogs.p) { OGS.p = Object.assign({}, OGS.p, W.ogs.p); } OGS.F = null; OGS.E = {}; } catch (e) { console.error(e); } var r = _a.apply(this, arguments); setTimeout(ogsRender, 0); return r; };
  window.addEventListener('resize', function () { [].forEach.call(document.querySelectorAll('#ogsWin .js-plotly-plot'), function (g) { try { Plotly.Plots.resize(g); } catch (e) {} }); });
})();
