/* ================= GC-Ex Drillhole 0.24.24: GRAFIK ANALISIS DARI DATA PROYEK =================
   ① Geostatistik → tab PROFIL: profil kadar per pita RL / Easting / Northing — beberapa panel sekaligus:
      unsur (rata-rata tertimbang panjang), rasio dua unsur (mis. Ag/Au), jumlah dua unsur (mis. Pb+Zn),
      % panjang kode geologi (mis. tekstur colloform). Garis acuan (mis. paleo-muka air tanah). CSV & PNG.
      Dipakai untuk menentukan batas zona sebelum membuat domain estimasi.
   ② Geostatistik → tab Statistik: KURVA PEMUSATAN LOGAM (% sampel teratas → % logam), angka 1 / 5 / 10 %,
      ambang kadar tiap titik, tombol "Pakai sebagai top-cut".
   ③ Ore Geometry → Ore shoot: KIPAS VARIOGRAM GT & TEBAL INTERSEP di bidang vein (36 arah dari garis strike),
      lembah terdalam = arah paling menerus, garis pitch usulan / sumbu shoot. */
var PF = { ax: 'z', bw: 10, slab: false, ref: '', refLbl: 'garis acuan', S: null, last: null };
function pfE(s) { return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; }); }
function pfN(v, d) { return v == null || !isFinite(v) ? '-' : (+v).toLocaleString('id-ID', { maximumFractionDigits: d == null ? 2 : d, minimumFractionDigits: 0 }); }
function pfFind(re) { var E = window.elements || []; for (var i = 0; i < E.length; i++) if (re.test(E[i])) return E[i]; return ''; }
function pfDef() {
  var E = window.elements || [], au = pfFind(/^au$/i) || E[0] || '', ag = pfFind(/^ag$/i), pb = pfFind(/^pb/i), zn = pfFind(/^zn/i), S = [];
  if (au) S.push({ t: 'el', a: au });
  if (ag && au) S.push({ t: 'rat', a: ag, b: au });
  if (pb && zn) S.push({ t: 'sum', a: pb, b: zn });
  var ci = -1; (window.CAT || []).forEach(function (c, i) { if (ci < 0 && c.src === 'g' && /tekst|text/i.test(c.name)) ci = i; });
  if (ci >= 0) { var dd = CAT[ci].d || [], cc = []; dd.forEach(function (nm, k) { if (/coll|crust|band/i.test(nm)) cc.push(k); }); if (!cc.length && dd.length) cc = [0]; S.push({ t: 'cat', ci: ci, c: cc }); }
  if (!S.length && E[0]) S.push({ t: 'el', a: E[0] });
  return S;
}
function pfLbl(s) {
  if (s.t === 'el') return s.a; if (s.t === 'rat') return s.a + '/' + s.b; if (s.t === 'sum') return s.a + '+' + s.b;
  var C = CAT[s.ci]; return '% ' + (s.c && s.c.length ? s.c.map(function (k) { try { return geoName(s.ci, k); } catch (e) { return k; } }).join('+') : '?') + (C ? ' (' + C.name + ')' : '');
}
/* data: per interval assay (hole terfilter, filter domain Geologi / domain aktif Geostatistik, opsional hanya di dalam slab) */
function pfCalc() {
  var S = PF.S || (PF.S = pfDef()), ids = visHoles(), bw = Math.max(0.1, +PF.bw || 10), ax = PF.ax, K = PF.slab ? secK().K : null, B = {};
  var dc = (window.gsDomCodes && gsDomCodes()) || null, need = {};
  S.forEach(function (s) { if (s.t !== 'cat') { need[s.a] = 1; if (s.b) need[s.b] = 1; } });
  var EI = {}; Object.keys(need).forEach(function (e) { EI[e] = elements.indexOf(e); });
  var nInt = 0;
  ids.forEach(function (id) {
    (groupedAssays[id] || []).forEach(function (a) {
      if (!(a[2] > a[1]) || !domOK(id, a)) return;
      if (dc && dc[gmCodeAt(id, (a[1] + a[2]) / 2)] !== true) return;
      var p = getXYZ(id, (a[1] + a[2]) / 2); if (K && !inK(K, p)) return;
      var q = ax === 'z' ? p.z : ax === 'x' ? p.x + offX : p.y + offY, k = Math.floor(q / bw), L = a[2] - a[1], b = B[k] || (B[k] = { n: 0, v: {}, w: {}, c: S.map(function () { return [0, 0]; }) });
      b.n++; nInt++;
      Object.keys(EI).forEach(function (e) { var v = a[4][EI[e]]; if (v != null && isFinite(v)) { b.v[e] = (b.v[e] || 0) + v * L; b.w[e] = (b.w[e] || 0) + L; } });
      S.forEach(function (s, i) { if (s.t !== 'cat') return; var c = catAssay(s.ci, id, a); if (c < 0) return; b.c[i][1] += L; if ((s.c || []).indexOf(c) >= 0) b.c[i][0] += L; });
    });
  });
  var keys = Object.keys(B).map(Number).sort(function (a, b) { return a - b; }), mean = function (b, e) { return b.w[e] > 0 ? b.v[e] / b.w[e] : NaN; };
  var rows = keys.map(function (k) {
    var b = B[k]; return { q: (k + 0.5) * bw, n: b.n, v: S.map(function (s, i) {
      if (s.t === 'el') return mean(b, s.a); if (s.t === 'rat') { var x = mean(b, s.a), y = mean(b, s.b); return y > 0 ? x / y : NaN; }
      if (s.t === 'sum') return mean(b, s.a) + mean(b, s.b); return b.c[i][1] > 0 ? 100 * b.c[i][0] / b.c[i][1] : NaN; }) };
  }).filter(function (r) { return r.n >= 1; });
  PF.last = { rows: rows, S: S.slice(), ax: ax, bw: bw, nInt: nInt, dom: !!dc, slab: !!K };
  return PF.last;
}
function pfPlot() {
  var d = document.getElementById('pfPlot'); if (!d || !window.Plotly) return; var R = pfCalc(), S = R.S, n = S.length, vert = R.ax === 'z';
  var dark = document.body.classList.contains('dark'), gr = dark ? '#33414f' : '#e9ecef', tx = dark ? '#dbe3ec' : '#333', cols = ['#2f5d9e', '#c8902f', '#3f8a46', '#8e44ad', '#c0392b', '#16a085'];
  var axT = vert ? 'RL (m)' : (R.ax === 'x' ? 'Easting (m)' : 'Northing (m)'), T = [], L = { paper_bgcolor: dark ? '#16202c' : '#fff', plot_bgcolor: dark ? '#0e1621' : '#fff', font: { size: 11, color: tx }, margin: { l: 60, r: 14, t: 34, b: 46 }, showlegend: false, shapes: [], annotations: [] };
  var ref = parseFloat(PF.ref);
  S.forEach(function (s, i) {
    var xa = 'x' + (i ? i + 1 : ''), ya = 'y' + (i ? i + 1 : ''), X = R.rows.map(function (r) { return r.v[i]; }), Q = R.rows.map(function (r) { return r.q; });
    T.push({ type: 'scatter', mode: 'lines+markers', x: vert ? X : Q, y: vert ? Q : X, xaxis: xa, yaxis: ya, line: { color: cols[i % cols.length], width: 2 }, marker: { size: 6 }, connectgaps: false, name: pfLbl(s),
      text: R.rows.map(function (r) { return r.n + ' interval'; }), hovertemplate: pfE(pfLbl(s)) + ': %{' + (vert ? 'x' : 'y') + ':.3f}<br>' + axT + ' %{' + (vert ? 'y' : 'x') + ':.1f} · %{text}<extra></extra>' });
    var dom = vert ? [i / n + 0.012, (i + 1) / n - 0.012] : [1 - (i + 1) / n + 0.03, 1 - i / n - 0.01];
    if (vert) { L['xaxis' + (i ? i + 1 : '')] = { domain: dom, title: { text: pfE(pfLbl(s)) }, gridcolor: gr, zeroline: false, anchor: ya }; L['yaxis' + (i ? i + 1 : '')] = { title: i ? undefined : { text: axT }, gridcolor: gr, matches: i ? 'y' : undefined, showticklabels: !i, anchor: xa }; }
    else { L['yaxis' + (i ? i + 1 : '')] = { domain: dom, title: { text: pfE(pfLbl(s)) }, gridcolor: gr, zeroline: false, anchor: xa }; L['xaxis' + (i ? i + 1 : '')] = { title: i === n - 1 ? { text: axT } : undefined, gridcolor: gr, matches: i ? 'x' : undefined, showticklabels: i === n - 1, anchor: ya }; }
    if (isFinite(ref)) {
      L.shapes.push(vert ? { type: 'line', xref: xa + ' domain', yref: ya, x0: 0, x1: 1, y0: ref, y1: ref, line: { color: '#c0392b', width: 2, dash: 'dash' } }
                         : { type: 'line', xref: xa, yref: ya + ' domain', x0: ref, x1: ref, y0: 0, y1: 1, line: { color: '#c0392b', width: 2, dash: 'dash' } });
      if (!i) L.annotations.push(vert ? { xref: xa + ' domain', yref: ya, x: 0.02, y: ref, text: pfE(PF.refLbl || ''), showarrow: false, yanchor: 'bottom', xanchor: 'left', font: { color: '#c0392b', size: 11 } }
                                      : { xref: xa, yref: ya + ' domain', x: ref, y: 1, text: pfE(PF.refLbl || ''), showarrow: false, xanchor: 'left', yanchor: 'top', font: { color: '#c0392b', size: 11 } });
    }
  });
  L.title = { text: 'Profil ' + (vert ? 'vertikal' : 'horizontal') + ' per pita ' + pfN(R.bw, 1) + ' m' + (R.dom ? ' · domain aktif' : '') + (R.slab ? ' · dalam slab' : '') + ' · ' + pfN(R.nInt, 0) + ' interval', font: { size: 12 } };
  d.style.height = (vert ? 420 : Math.max(300, 170 * n)) + 'px';
  Plotly.react(d, T, L, { displaylogo: false, responsive: true, toImageButtonOptions: { filename: 'profil_' + (vert ? 'RL' : R.ax), scale: 2 } });
}
function pfCsv() {
  var R = PF.last || pfCalc(), h = [(R.ax === 'z' ? 'RL' : R.ax === 'x' ? 'Easting' : 'Northing') + '_tengah', 'Jumlah_interval'].concat(R.S.map(pfLbl)), r = [h.join(',')];
  R.rows.forEach(function (o) { r.push([o.q.toFixed(2), o.n].concat(o.v.map(function (v) { return isFinite(v) ? v.toFixed(4) : ''; })).join(',')); });
  gxSimpan('\ufeff' + r.join('\r\n'), 'profil_kadar.csv', 'text/csv');
}
function pfSet(k, v) { PF[k] = v; pfPanel(); }
function pfS(i, k, v) { var s = PF.S[i]; if (!s) return; s[k] = v; if (k === 't') { if (v === 'cat') { s.ci = (CAT || []).findIndex(function (c) { return c.src === 'g'; }); s.c = []; } else if (!s.a) s.a = elements[0]; if ((v === 'rat' || v === 'sum') && !s.b) s.b = elements[1] || elements[0]; }
  if (k === 'ci') s.c = []; pfPanel(); }
function pfCode(i, c, on) { var s = PF.S[i]; if (!s) return; s.c = (s.c || []).filter(function (x) { return x !== c; }); if (on) s.c.push(c); pfPanel(); }
function pfPanel() {
  var b = document.getElementById('pfBody'); if (!b) return; if (!PF.S) PF.S = pfDef(); var E = window.elements || [];
  var opt = function (L, cur) { return L.map(function (e) { return '<option' + (e === cur ? ' selected' : '') + '>' + pfE(e) + '</option>'; }).join(''); };
  var h = '<div class=note>Rata-rata kadar per pita (tertimbang panjang sampel) dari semua hole terfilter dan filter domain aktif. Rasio = rasio rata-rata; % kode = persen panjang interval berkode itu. Pakai untuk menemukan <b>batas zona</b> (mis. zona didih, base-metal, tudung tercuci) sebelum membuat domain estimasi.</div>' +
    '<div class=g3><div><label>Sumbu</label><select onchange="pfSet(\'ax\',this.value)"><option value=z' + (PF.ax === 'z' ? ' selected' : '') + '>RL (vertikal)</option><option value=x' + (PF.ax === 'x' ? ' selected' : '') + '>Easting</option><option value=y' + (PF.ax === 'y' ? ' selected' : '') + '>Northing</option></select></div>' +
    '<div><label>Lebar pita (m)</label><input type=number step=any value="' + PF.bw + '" onchange="pfSet(\'bw\',+this.value)"></div>' +
    '<div><label>Garis acuan (RL / koordinat)</label><input type=number step=any value="' + pfE(PF.ref) + '" placeholder="mis. 250" onchange="pfSet(\'ref\',this.value)"></div></div>' +
    '<div class=g2><div><label>Label garis acuan</label><input type=text value="' + pfE(PF.refLbl) + '" onchange="pfSet(\'refLbl\',this.value)"></div><label class=sw style="margin-top:18px"><input type=checkbox ' + (PF.slab ? 'checked' : '') + ' onchange="pfSet(\'slab\',this.checked)">Hanya di dalam slab sayatan</label></div>';
  h += '<table class=pftb><tr><th>Panel</th><th>Jenis</th><th>Isi</th><th></th></tr>' + PF.S.map(function (s, i) {
    var isi;
    if (s.t === 'cat') { var cs = (CAT || []).map(function (c, k) { return c.src === 'g' || c.src === 'a' ? '<option value=' + k + (k === s.ci ? ' selected' : '') + '>' + pfE(c.name) + '</option>' : ''; }).join(''), C = CAT[s.ci];
      isi = '<select onchange="pfS(' + i + ',\'ci\',+this.value)">' + cs + '</select><div class=pfcodes>' + (C && C.d ? C.d.map(function (nm, k) { return '<label><input type=checkbox ' + ((s.c || []).indexOf(k) >= 0 ? 'checked' : '') + ' onchange="pfCode(' + i + ',' + k + ',this.checked)">' + pfE(nm) + '</label>'; }).join('') : '') + '</div>'; }
    else isi = '<select onchange="pfS(' + i + ',\'a\',this.value)">' + opt(E, s.a) + '</select>' + (s.t === 'rat' ? ' / ' : s.t === 'sum' ? ' + ' : '') + (s.t === 'rat' || s.t === 'sum' ? '<select onchange="pfS(' + i + ',\'b\',this.value)">' + opt(E, s.b) + '</select>' : '');
    return '<tr><td>' + (i + 1) + '</td><td><select onchange="pfS(' + i + ',\'t\',this.value)">' + [['el', 'Unsur'], ['rat', 'Rasio'], ['sum', 'Jumlah'], ['cat', '% kode geologi']].map(function (q) { return '<option value=' + q[0] + (q[0] === s.t ? ' selected' : '') + '>' + q[1] + '</option>'; }).join('') + '</select></td><td>' + isi + '</td><td><button class=x onclick="PF.S.splice(' + i + ',1);pfPanel()">&times;</button></td></tr>';
  }).join('') + '</table>' +
    '<div class=row><button onclick="PF.S.push({t:\'el\',a:elements[0]});pfPanel()"' + (PF.S.length >= 6 ? ' disabled' : '') + '>+ Panel</button> <button onclick="PF.S=pfDef();pfPanel()">Bawaan</button> <button onclick="pfCsv()">&#8681; CSV</button> <button onclick="Plotly.downloadImage(\'pfPlot\',{format:\'png\',filename:\'profil_kadar\',scale:2})">&#8681; PNG</button></div>' +
    '<div id=pfPlot class=chart style="height:420px"></div>';
  b.innerHTML = h; try { pfPlot(); } catch (e) { console.error(e); }
}
/* ---------- ② kurva pemusatan logam ---------- */
function mcCalc(R) {
  var C = R.C, n = C.length; if (n < 5) return null; var A = C.map(function (c) { return [c.v, c.len || 1]; }).filter(function (a) { return isFinite(a[0]) && a[0] >= 0; }).sort(function (a, b) { return b[0] - a[0]; });
  var tot = A.reduce(function (s, a) { return s + a[0] * a[1]; }, 0); if (!(tot > 0)) return null; var X = [0], Y = [0], cum = 0;
  A.forEach(function (a, i) { cum += a[0] * a[1]; X.push(100 * (i + 1) / A.length); Y.push(100 * cum / tot); });
  var at = function (p) { var k = Math.max(1, Math.round(p / 100 * A.length)); return { p: p, k: k, thr: A[k - 1][0], m: Y[k] }; };
  return { X: X, Y: Y, n: A.length, pts: [1, 2.5, 5, 10].map(at), max: A[0][0] };
}
function mcDraw() {
  var R = GS.R, host = document.getElementById('gsTS'); if (!host || !R || !R.C) return; var d = document.getElementById('gMetal');
  if (!d) { d = document.createElement('div'); d.id = 'gMetalBox'; d.innerHTML = '<div id=gMetal class=chart style="height:300px"></div><div id=gMetalTbl></div>'; var tt = document.getElementById('gsTopTbl'); host.insertBefore(d, tt); d = document.getElementById('gMetal'); }
  var M = mcCalc(R), tb = document.getElementById('gMetalTbl'); if (!M) { d.innerHTML = ''; tb.innerHTML = ''; return; }
  var dark = document.body.classList.contains('dark'), gr = dark ? '#33414f' : '#e9ecef', tx = dark ? '#dbe3ec' : '#333', P = M.pts.filter(function (q) { return q.p !== 2.5; });
  var T = [{ type: 'scatter', mode: 'lines', x: M.X, y: M.Y, line: { color: '#c8902f', width: 2.5 }, hovertemplate: '%{x:.1f}% sampel teratas = %{y:.1f}% logam<extra></extra>' },
           { type: 'scatter', mode: 'markers+text', x: P.map(function (q) { return q.p; }), y: P.map(function (q) { return q.m; }), marker: { size: 9, color: '#1d2b3a' },
             text: P.map(function (q) { return q.p + '% sampel = ' + q.m.toFixed(0) + '% logam'; }), textposition: 'middle right', textfont: { size: 11, color: tx }, hoverinfo: 'skip' }];
  Plotly.react(d, T, { paper_bgcolor: dark ? '#16202c' : '#fff', plot_bgcolor: dark ? '#0e1621' : '#fff', font: { size: 11, color: tx }, margin: { l: 56, r: 14, t: 30, b: 44 }, showlegend: false,
    title: { text: 'Pemusatan logam ' + pfE(R.el) + ' (' + M.n + ' komposit)', font: { size: 12 } }, xaxis: { title: { text: '% sampel teratas' }, range: [0, 30], gridcolor: gr }, yaxis: { title: { text: '% logam terkumpul' }, range: [0, 100], gridcolor: gr } },
    { displaylogo: false, responsive: true, toImageButtonOptions: { filename: 'pemusatan_logam_' + R.el, scale: 2 } });
  tb.innerHTML = '<table><tr><th>Sampel teratas</th><th>Ambang kadar (&ge;)</th><th>% logam</th><th></th></tr>' + M.pts.map(function (q) {
      return '<tr><td>' + q.p + '% (' + q.k + ')</td><td>' + fx(q.thr) + '</td><td>' + q.m.toFixed(1) + '%</td><td><button onclick="$(\'gTop\').value=' + (+q.thr).toPrecision(4) + ';gsRun()">Pakai sebagai top-cut</button></td></tr>'; }).join('') +
    '</table><div class=note>Bila 1% sampel teratas memuat &gt; 10% logam, kadar ekstrem terlalu berpengaruh: top-cut perlu dipertimbangkan (cocokkan dengan titik patah kurva log-probability &amp; tabel top-cut di bawah). Nilai maksimum ' + fx(M.max) + '.</div>';
}
/* ---------- ③ kipas variogram GT & tebal di Ore Geometry ---------- */
function ogFan(val) {
  var R = OG.R; if (!R) return null; var V = R.pl, H = R.H.filter(function (h) { return isFinite(val(h)); }); if (H.filter(function (h) { return val(h) > 0; }).length < 5) return null;
  var P = H.map(function (h) { var e = [h.p[0] - V.c[0], h.p[1] - V.c[1], h.p[2] - V.c[2]]; return [ogDot(e, V.s), ogDot(e, V.dd), Math.log(val(h) + 1)]; }), n = P.length;
  if (n > 1500) { var st = n / 1500, Q = []; for (var q = 0; q < 1500; q++)Q.push(P[Math.floor(q * st)]); P = Q; n = P.length; }
  var mu = 0; P.forEach(function (p) { mu += p[2]; }); mu /= n; var va = 0; P.forEach(function (p) { va += (p[2] - mu) * (p[2] - mu); }); va /= Math.max(1, n - 1); if (!(va > 0)) return null;
  var nn = []; for (var i = 0; i < n; i += Math.max(1, Math.floor(n / 300))) { var m = 1e18; for (var j = 0; j < n; j++) { if (j === i) continue; var d = Math.hypot(P[i][0] - P[j][0], P[i][1] - P[j][1]); if (d > 0.01 && d < m) m = d; } if (m < 1e18) nn.push(m); }
  nn.sort(function (a, b) { return a - b; }); var med = nn.length ? nn[Math.floor(nn.length / 2)] : 10, h1 = 0.5 * med, h2 = 4.5 * med, NB = 36, S = new Float64Array(NB), C = new Float64Array(NB);
  for (i = 0; i < n; i++)for (j = i + 1; j < n; j++) { var du = P[j][0] - P[i][0], dv = P[j][1] - P[i][1], dd = Math.hypot(du, dv); if (dd < h1 || dd > h2) continue; var a = Math.atan2(dv, du) / OGR; a = ((a % 180) + 180) % 180; var g = 0.5 * (P[i][2] - P[j][2]) * (P[i][2] - P[j][2]);
    for (var b = 0; b < NB; b++) { var df = Math.abs(a - b * 5); df = Math.min(df, 180 - df); if (df <= 12.5) { S[b] += g; C[b]++; } } }
  var G = []; for (b = 0; b < NB; b++)G.push(C[b] >= 20 ? S[b] / C[b] / va : null);
  var Gs = G.map(function (v, b) { var L = [G[(b + NB - 1) % NB], v, G[(b + 1) % NB]].filter(function (x) { return x != null; }); return L.length ? L.reduce(function (s, x) { return s + x; }, 0) / L.length : null; });
  var bi = -1; Gs.forEach(function (v, b) { if (v != null && (bi < 0 || v < Gs[bi])) bi = b; }); return { G: Gs, best: bi * 5, n: n, lag: [h1, h2] };
}
function ogFanDraw() {
  var body = document.getElementById('ogBody'); if (!body || !OG.R) return; var h4 = [].slice.call(body.querySelectorAll('h4')).filter(function (x) { return /Ore shoot/.test(x.textContent); })[0]; if (!h4) return;
  var box = document.getElementById('ogFanBox'); if (!box) { box = document.createElement('div'); box.id = 'ogFanBox'; var nx = h4.nextElementSibling; while (nx && nx.tagName !== 'H4') { if (nx.matches && nx.matches('button') && /Export sumbu/.test(nx.textContent)) break; nx = nx.nextElementSibling; } h4.parentNode.insertBefore(box, nx && nx.tagName !== 'H4' ? nx.nextSibling : nx); }
  var A = ogFan(function (h) { return h.gt; }), B = ogFan(function (h) { return h.tt > 0 ? h.tt : h.len; });
  if (!A) { box.innerHTML = '<div class=hint>Kipas variogram perlu minimal 5 bor ber-intercept.</div>'; return; }
  box.innerHTML = '<div id=ogFanPlot style="height:280px;margin-top:6px"></div><div class=hint id=ogFanTx></div>';
  var X = []; for (var b = 0; b < 36; b++)X.push(b * 5); var dark = document.body.classList.contains('dark'), gr = dark ? '#33414f' : '#e9ecef', tx = dark ? '#dbe3ec' : '#333', R = OG.R;
  var T = [{ type: 'scatter', mode: 'lines+markers', x: X, y: A.G, name: 'GT (kadar × tebal)', line: { color: '#2f5d9e', width: 2 }, marker: { size: 5 }, connectgaps: true }];
  if (B) T.push({ type: 'scatter', mode: 'lines+markers', x: X, y: B.G, name: 'tebal intersep', line: { color: '#c8902f', width: 2 }, marker: { size: 5 }, connectgaps: true });
  var sh = [], an = [], line = function (p, c, lbl, dash) { sh.push({ type: 'line', xref: 'x', yref: 'paper', x0: p, x1: p, y0: 0, y1: 1, line: { color: c, width: 2, dash: dash } }); an.push({ xref: 'x', yref: 'paper', x: p, y: 1, text: lbl, showarrow: false, xanchor: 'left', yanchor: 'top', font: { size: 10, color: c } }); };
  line(A.best, '#c0392b', 'GT paling menerus ' + A.best + '°', 'dash');
  (OG.axes || []).filter(function (a) { return !a.auto && isFinite(a.pitch); }).forEach(function (a) { var p = ((a.pitch % 180) + 180) % 180; line(p, '#5b6478', pfE(a.name) + ' ' + Math.round(p) + '°', 'dot'); });
  Plotly.react('ogFanPlot', T, { paper_bgcolor: dark ? '#16202c' : '#fff', plot_bgcolor: dark ? '#0e1621' : '#fff', font: { size: 11, color: tx }, margin: { l: 52, r: 10, t: 28, b: 42 }, title: { text: 'Kipas variogram di bidang vein (' + pfE(R.el) + ')', font: { size: 12 } },
    xaxis: { title: { text: 'arah di dalam bidang vein (° dari garis strike)' }, dtick: 15, range: [-3, 178], gridcolor: gr }, yaxis: { title: { text: 'γ ternormalisasi (kecil = lebih menerus)' }, gridcolor: gr }, legend: { orientation: 'h', y: 1.12, x: 0 }, shapes: sh, annotations: an },
    { displaylogo: false, responsive: true, toImageButtonOptions: { filename: 'kipas_variogram_GT', scale: 2 } });
  document.getElementById('ogFanTx').innerHTML = 'Lembah terdalam = arah paling menerus. GT: ' + A.best + '&deg;' + (B ? ', tebal intersep: ' + B.best + '&deg;' : '') + ' dari garis strike (' + A.n + ' bor termasuk GT 0, jarak pasangan ' + pfN(A.lag[0], 0) + '&ndash;' + pfN(A.lag[1], 0) + ' m, nilai log). Bila GT dan tebal sejalan, sumbu ore shoot dikontrol geometri vein; bila berbeda, oleh kadar.';
}
/* ---------- pasang ---------- */
(function () {
  var tabs = document.querySelector('#gsBS') && document.querySelector('#gsBS').parentNode, ts = document.getElementById('gsTS');
  if (tabs && ts && !document.getElementById('gsBP')) {
    var bt = document.createElement('button'); bt.id = 'gsBP'; bt.textContent = 'Profil'; bt.onclick = function () { gsTab('P'); }; tabs.appendChild(bt);
    var dv = document.createElement('div'); dv.id = 'gsTP'; dv.style.display = 'none'; dv.innerHTML = '<div id=pfBody></div>'; ts.parentNode.insertBefore(dv, ts);
    var st = document.createElement('style'); st.textContent = '.pftb{width:100%;border-collapse:collapse;margin:6px 0}.pftb td,.pftb th{padding:3px 4px;border-bottom:1px solid var(--bd,#e3e7ee);font-size:12px;text-align:left;vertical-align:top}.pftb select{max-width:150px}.pfcodes{display:flex;flex-wrap:wrap;gap:2px 10px;margin-top:3px;max-height:90px;overflow:auto}.pfcodes label{display:flex;align-items:center;gap:3px;font-size:11.5px;font-weight:400}';
    document.head.appendChild(st);
  }
  if (typeof gsTab === 'function') { var _t = gsTab; gsTab = function (t) { var r = _t.apply(this, arguments); var p = document.getElementById('gsTP'), b = document.getElementById('gsBP'); if (p) p.style.display = t === 'P' ? 'block' : 'none'; if (b) b.className = t === 'P' ? 'on' : ''; if (t === 'P') { try { pfPanel(); } catch (e) { console.error(e); } } return r; }; window.gsTab = gsTab; }
  if (typeof gsDraw === 'function') { var _d = gsDraw; gsDraw = function () { var r = _d.apply(this, arguments); try { if (GS.tab === 'S') mcDraw(); if (GS.tab === 'P') pfPanel(); } catch (e) { console.error(e); } return r; }; window.gsDraw = gsDraw; }
  if (typeof ogPanel === 'function') { var _o = ogPanel; ogPanel = function () { var r = _o.apply(this, arguments); try { ogFanDraw(); } catch (e) { console.error(e); } return r; }; window.ogPanel = ogPanel; }
})();
