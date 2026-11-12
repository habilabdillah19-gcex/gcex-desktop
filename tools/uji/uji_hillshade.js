/* Hillshade topo & pit (web-src/tinhr.js, BM 0.24.69 / DH 0.24.82): rumus warna per segitiga.
   Bidang menghadap cahaya (azimut 315, elevasi 45) = warna penuh; bidang datar = ambient + (1-ambient) sin 45;
   lereng membelakangi cahaya = ambient saja; lampu Plotly dimatikan supaya warna yang dipanggang tidak diubah lagi.
   Pemakaian: node tools/uji/uji_hillshade.js */
const fs = require('fs'), path = require('path');
global.window = {}; global.document = { getElementById: () => null }; global.performance = { now: () => 0 };
new Function(fs.readFileSync(path.join(__dirname, '..', '..', 'web-src', 'tinhr.js'), 'utf8'))();
const T = window.TIN; let gagal = 0;
const cek = (ok, m) => { console.log((ok ? '  ok    ' : '  GAGAL ') + m); if (!ok) gagal++; };
/* tiga segitiga: datar; lereng yang naik ke barat laut (menghadap tenggara); lereng yang naik ke tenggara (menghadap barat laut) */
const s = Math.SQRT1_2;
const tin = { x: [0, 1, 0, 0, 1, 0, 0, 1, 0], y: [0, 0, 1, 0, 0, 1, 0, 0, 1],
  z: [0, 0, 0, 0, -s * 1 * s, s * 1 * s, 0, s * s, -s * s], i: [0, 3, 6], j: [1, 4, 7], k: [2, 5, 8] };
/* normal miring: n ~ (-a,a,1) dengan a = 0,5 -> bukan persis arah cahaya; hitung harapan dengan rumus yang sama */
const L = [-0.5, 0.5, s], amb = 0.32;
const harap = (q) => { const a = tin.i[q], b = tin.j[q], c = tin.k[q], X = tin.x, Y = tin.y, Z = tin.z;
  const u = [X[b] - X[a], Y[b] - Y[a], Z[b] - Z[a]], v = [X[c] - X[a], Y[c] - Y[a], Z[c] - Z[a]];
  let n = [u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0]]; if (n[2] < 0) n = n.map(t => -t);
  const ln = Math.hypot(...n), d = (n[0] * L[0] + n[1] * L[1] + n[2] * L[2]) / ln; return amb + (1 - amb) * Math.max(0, d); };
const t = {}; cek(T.hillshade(t, tin, { color: '#c8c8c8' }, 'kuat') === true, 'hillshade terpasang');
const g = (q) => +/rgb\((\d+)/.exec(t.facecolor[q])[1] / 200;
cek(Math.abs(g(0) - (amb + (1 - amb) * s)) < 0.01, 'bidang datar = ambient + (1-ambient) sin 45: ' + g(0).toFixed(3));
cek(Math.abs(g(1) - harap(1)) < 0.01 && g(1) < g(0), 'lereng menghadap tenggara (naik ke barat laut) lebih gelap dari datar: ' + g(1).toFixed(3));
cek(Math.abs(g(2) - harap(2)) < 0.01 && g(2) > g(0), 'lereng menghadap barat laut lebih terang dari datar: ' + g(2).toFixed(3));
cek(t.lighting.diffuse === 0 && t.lighting.ambient === 1 && !t.color && !t.intensity, 'lampu Plotly dimatikan, warna dari facecolor');
const t2 = {}; T.hillshade(t2, tin, { grad: true }, 'kuat'); cek(t2.facecolor.length === 3, 'mode gradasi elevasi ikut ber-hillshade');
console.log(gagal ? '\nGAGAL' : '\nLULUS'); process.exit(gagal ? 1 : 0);
