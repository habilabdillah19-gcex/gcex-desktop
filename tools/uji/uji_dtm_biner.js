/* Uji pembaca Surpac DTM BINER + STR biner berdeskripsi teks (13 Nov 2026, laporan pemilik: pit_z3south_r4.dtm tidak bisa
   dibaca; pembanding Reporting). Data sintetis (pit kotak 3 jenjang), bukan data proyek.
   - STR biner: rekaman 29 byte + deskripsi teks ",<n>" berpanjang bebas; pemisah string 29 byte nol.
   - DTM biner: header teks, 4 byte, titik batas 29 byte (> 4 KB, END jauh sesudah byte 4096), END, record objek 01,
     trisolasi 02 (neighbours=yes), segitiga 03 (33 byte). Indeks titik = nomor record STR termasuk pemisah (1-based).
     Satu segitiga merujuk record di luar STR -> dibuang (drop 1), DTM tetap terbaca.
   - Regresi: STR biner tanpa deskripsi (rekaman tetap 29 byte, format ekspor GC-Ex) tetap terbaca.
   Fungsi diambil dari web-src/gcex_base.html (Block Model) dan web-src-dh/gcex_dh_base.html (Drillhole).
   Jalankan: node tools/uji/uji_dtm_biner.js            (A/B: build lama -> gagal) */
const fs = require('fs'), path = require('path'), ROOT = path.resolve(__dirname, '..', '..');
function grab(src, start) {
  const L = src.split('\n'); const i = L.findIndex(l => l.startsWith(start)); if (i < 0) return '';
  const out = [L[i]]; for (let j = i + 1; j < L.length && !/^(function |async function |SA\.|\/\*|var )/.test(L[j]); j++) out.push(L[j]); return out.join('\n');
}
function load(file) {
  const src = fs.readFileSync(path.join(ROOT, file), 'utf8');
  const js = 'var RXN=/^[+-]?(\\d+\\.?\\d*|\\.\\d+)([eE][+-]?\\d+)?$/;var E=function(){return null};function bname(n){return n.replace(/\\.[^.]+$/,"")}\n' +
    ['function beDbl', 'function strSeqBin', 'async function readStr(', 'function dtmBin', 'async function readDtm('].map(s => grab(src, s)).join('\n') +
    '\nreturn {readStr:readStr,readDtm:readDtm};';
  return new Function(js)();
}
/* ---- data sintetis ---- */
function be(n) { const b = Buffer.alloc(n); return b; }
function rec(sid, x, y, z) { const b = be(29); b[0] = 0; b.writeInt32BE(sid, 1); b.writeDoubleBE(y, 5); b.writeDoubleBE(x, 13); b.writeDoubleBE(z, 21); return b; }
const rings = [[0, 100, 100], [10, 90, 90], [20, 80, 80]], strs = [];   /* [min, max, z] keliling, titik tiap 2 m */
rings.forEach(([a, b, z]) => { const p = []; for (let x = a; x < b; x += 2) p.push([x, a]); for (let y = a; y < b; y += 2) p.push([b, y]); for (let x = b; x > a; x -= 2) p.push([x, b]); for (let y = b; y > a; y -= 2) p.push([a, y]); p.push(p[0]); strs.push(p.map(q => [q[0] + 500000, q[1] + 9000000, z])); });
function strFile(desc) {
  const parts = [Buffer.from('uji_pit,13-Nov-26,,SSI_STYLES:styles.ssi\r\n0,           0.000,           0.000,           0.000,           0.000,           0.000,           0.000\r\n', 'latin1'), be(4)], recs = [];
  strs.forEach((s, k) => { s.forEach(q => { parts.push(rec(k + 1, q[0], q[1], q[2])); if (desc) parts.push(Buffer.from(',' + (k + 1), 'latin1')); recs.push(q); }); parts.push(be(29)); recs.push(null); });
  parts.push(be(29), Buffer.from('END\0', 'latin1')); return { buf: Buffer.concat(parts), recs: recs };
}
const S1 = strFile(true), S0 = strFile(false);
/* segitiga: sabuk di antara cincin bersebelahan (indeks record 1-based, pemisah ikut dihitung) */
const idx = [], base = []; let r = 0; strs.forEach((s, k) => { base.push(r + 1); r += s.length + 1; });
const tri = [];
for (let k = 0; k + 1 < strs.length; k++) { const A = strs[k], B = strs[k + 1], na = A.length - 1, nb = B.length - 1;
  let i = 0, j = 0; while (i < na || j < nb) { const ai = base[k] + (i % na), bj = base[k + 1] + (j % nb);
    if (j >= nb || (i < na && i / na <= j / nb)) { tri.push([ai, base[k] + ((i + 1) % na), bj]); i++; } else { tri.push([ai, base[k + 1] + ((j + 1) % nb), bj]); j++; } } }
{ const C = strs[2], nc = C.length - 1; for (let i = 1; i + 1 < nc; i++) tri.push([base[2], base[2] + i, base[2] + i + 1]); }
const nGood = tri.length; tri.push([base[0], base[0] + 1, r + 5]);   /* merujuk record di luar STR */
function dtmFile() {
  const parts = [Buffer.from('uji_pit.str,1234567890;algorithm=standard;fields=x,y\r\n', 'latin1'), be(4)];
  strs[0].forEach(q => parts.push(rec(1, q[0], q[1], 0))); parts.push(be(29), be(29));   /* string batas (Z diabaikan) */
  parts.push(Buffer.from('END', 'latin1'), be(4)); const o1 = be(9); o1[0] = 1; o1.writeInt32BE(1, 1); o1.writeInt32BE(1, 5); parts.push(o1);
  const t2 = be(5); t2[0] = 2; t2.writeInt32BE(1, 1); parts.push(t2, Buffer.from('neighbours=yes,validated=true,closed=no,algorithm=legacy', 'latin1'), be(4));
  tri.forEach((t, k) => { const b = be(33); b[0] = 3; b.writeInt32BE(k + 1, 1); b.writeInt32BE(t[0], 5); b.writeInt32BE(t[1], 9); b.writeInt32BE(t[2], 13); parts.push(b); });
  parts.push(Buffer.from([255, 255, 255, 255, 255])); return Buffer.concat(parts);
}
const DTM = dtmFile();
function F(name, b) { return { name: name, size: b.length, arrayBuffer: async () => b.buffer.slice(b.byteOffset, b.byteOffset + b.length), text: async () => b.toString('latin1') }; }
(async () => {
  const gagal = [];
  if (DTM.indexOf('END') < 4096) gagal.push('data uji: END harus sesudah byte 4096');
  for (const f of ['web-src/gcex_base.html', 'web-src-dh/gcex_dh_base.html']) {
    const R = load(f), app = f.indexOf('dh') >= 0 ? 'Drillhole' : 'Block Model';
    try {
      for (const [nm, S] of [['berdeskripsi', S1], ['tanpa deskripsi', S0]]) {
        const segs = await R.readStr(F('uji_pit.str', S.buf), true); let n = 0, ok = true;
        segs.forEach(g => g.forEach(p => { n++; if (!(p[0] >= 500000 && p[0] <= 500100 && p[1] >= 9000000 && p[1] <= 9000100)) ok = false; }));
        const nExp = strs.reduce((a, s) => a + s.length, 0);
        console.log(app, 'STR', nm, 'string', segs.length, 'titik', n, '/', nExp, ok ? '' : 'KOORDINAT LIAR');
        if (segs.length !== 3 || n !== nExp || !ok) gagal.push(app + ': STR biner ' + nm + ' salah terbaca');
      }
      const m = await R.readDtm(F('uji_pit.dtm', DTM), [F('uji_pit.str', S1.buf)]);
      let zOk = true; for (let t = 0; t < m.t.length; t += 3) { const z = [0, 1, 2].map(q => m.v[m.t[t + q] * 3 + 2]); if (z.some(v => [100, 90, 80].indexOf(v) < 0)) zOk = false; }
      let luas = 0; for (let t = 0; t < m.t.length; t += 3) { const a = m.t[t] * 3, b = m.t[t + 1] * 3, c = m.t[t + 2] * 3; luas += Math.abs((m.v[b] - m.v[a]) * (m.v[c + 1] - m.v[a + 1]) - (m.v[b + 1] - m.v[a + 1]) * (m.v[c] - m.v[a])) / 2; }
      console.log(app, 'DTM biner: segitiga', m.nt, '/', nGood, 'dibuang', m.drop, 'biner', m.bin, 'luas', luas.toFixed(1), 'm2 (harus 10000)');
      if (m.nt !== nGood || m.drop !== 1 || !m.bin || !zOk || Math.abs(luas - 10000) > 0.01) gagal.push(app + ': DTM biner salah terbaca');
    } catch (e) { console.log(app, 'ERROR', e.message); gagal.push(app + ': ' + e.message); }
  }
  console.log(gagal.length ? 'GAGAL\n- ' + gagal.join('\n- ') : '\nLULUS'); process.exit(gagal.length ? 1 : 0);
})();
