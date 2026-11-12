/* Pembaca header .mdl (SA.mdlParseHead) harus tahan terhadap lebar nilai bawaan atribut yang tidak biasa
   (laporan pemilik 10-11-2026: 'Tipe atribut "" (24940) belum didukung'). Header SINTETIS (nama & nilai fiktif)
   dengan tata letak Surpac Version 4.0 yang dipelajari dari model pemilik; tiap varian menyisipkan satu atribut
   dengan lebar lain, lalu memeriksa semua atribut sesudahnya tetap terbaca benar.
   Pemakaian: node tools/uji/uji_mdl_header.js [berkas.mdl ...]   (berkas nyata opsional, tidak masuk repo) */
const fs = require('fs'), path = require('path'), root = path.join(__dirname, '..', '..');
const src = fs.readFileSync(path.join(root, 'web-src', 'gcex_base.html'), 'utf8');
const a = src.indexOf('SA.mdlParseHead=function'), b = src.indexOf('/* atribut yang dibutuhkan atribut kalkulasi */');
const SA = {}; const MA = fs.readFileSync(path.join(root, 'web-src', 'mdlattr.js'), 'utf8');
new Function('SA', 'TextDecoder', MA + '\n' + src.slice(a, b))(SA, TextDecoder);
const enc = s => Buffer.from(s, 'latin1');
const i32 = v => { const x = Buffer.alloc(4); x.writeInt32BE(v); return x; }, f64 = v => { const x = Buffer.alloc(8); x.writeDoubleBE(v); return x; };
function header(attrs) {
  const P = [enc('### Block Model ###\nVersion 4.0\n'), Buffer.from([0]), enc('uji_sintetis.mdl'), Buffer.from([0]), Buffer.from([0]), Buffer.alloc(12)];
  [500000, 9000000, 100, 12, 12, 6, 1200, 1200, 300].forEach(v => P.push(f64(v)));
  P.push(i32(0), i32(attrs.length));
  attrs.forEach(t => { P.push(enc(t.name), Buffer.from([0]));
    if (t.expr) { P.push(i32(1), i32(2), enc(t.expr), Buffer.from([0])); return; }
    P.push(i32(0), i32(2), i32(t.type), t.body); });
  P.push(i32(0)); const key = Buffer.alloc(8); key.writeUInt32BE(3); P.push(key, Buffer.alloc(64)); return Buffer.concat(P);
}
const real = (name, v) => ({ name, type: 2, body: Buffer.concat([f64(v), Buffer.from([0])]) });
const tail = [real('au_x', 0), { name: 'kelas_x', expr: 'IIF(au_x<0.3,"WASTE","ORE")' }, real('sg_x', 2.5)];
const varian = {
  'baku (real, char, int)': [real('ag_x', 0), { name: 'rock_x', type: 3, body: Buffer.concat([enc('unknown'), Buffer.from([0, 0])]) }, { name: 'n_x', type: 1, body: Buffer.concat([i32(-99), Buffer.from([0])]) }],
  'integer 8+1 byte': [{ name: 'n_x', type: 1, body: Buffer.concat([f64(-99), Buffer.from([0])]) }],
  'karakter + 5 byte': [{ name: 'rock_x', type: 3, body: Buffer.concat([enc('waste'), Buffer.from([0]), Buffer.alloc(5)]) }],
  'karakter tanpa byte ekor': [{ name: 'rock_x', type: 3, body: Buffer.concat([enc('waste'), Buffer.from([0])]) }],
  'tipe tak dikenal (6) 8+1': [{ name: 'dens_x', type: 6, body: Buffer.concat([f64(2.6), Buffer.from([0])]) }],
  'real 13 byte': [{ name: 'cu_x', type: 2, body: Buffer.concat([f64(0), Buffer.alloc(5)]) }],
  /* 12-11-2026: kolom Description Surpac terisi -> teks deskripsi sesudah nilai bawaan ('Atribut ke-5 sesudah "ensity"') */
  'real berdeskripsi': [real('ag_x', 0), { name: 'sg_d', type: 2, body: Buffer.concat([f64(0), enc('density'), Buffer.from([0])]) }, real('sxs_x', 0)],
  'karakter & integer berdeskripsi': [{ name: 'rock_x', type: 3, body: Buffer.concat([enc('BLANK'), Buffer.from([0]), enc('rock type'), Buffer.from([0])]) }, { name: 'n_x', type: 1, body: Buffer.concat([i32(-99), enc('nomor'), Buffer.from([0])]) }],
};
let gagal = 0;
for (const [nm, pre] of Object.entries(varian)) {
  const A = pre.concat(tail), u = new Uint8Array(header(A));
  try { const H = SA.mdlParseHead(u, u.length, 'uji.mdl'), got = H.attrs.map(x => x.name), want = A.map(x => x.name);
    const ok = JSON.stringify(got) === JSON.stringify(want) && H.attrs.find(x => x.name === 'kelas_x').calc && H.attrs.find(x => x.name === 'sg_x').def === 2.5;
    console.log((ok ? '  ok   ' : '  GAGAL ') + nm + ' -> ' + got.join(', ') + ' | tipe: ' + H.attrs.map(x => x.calc ? 'calc' : x.type + (x.rawType ? '(' + x.rawType + ')' : '')).join(','));
    if (!ok) gagal++;
  } catch (e) { console.log('  GAGAL ' + nm + ': ' + e.message); gagal++; }
}
for (const f of process.argv.slice(2)) { const u = new Uint8Array(fs.readFileSync(f).subarray(0, 1 << 20));
  try { const H = SA.mdlParseHead(u, fs.statSync(f).size, path.basename(f)); console.log('  ok   ' + path.basename(f) + ': ' + H.attrs.length + ' atribut: ' + H.attrs.map(x => x.name + (x.calc ? '=calc' : ':' + x.type)).join(', ')); }
  catch (e) { console.log('  GAGAL ' + path.basename(f) + ': ' + e.message); gagal++; } }
console.log(gagal ? '\nGAGAL' : '\nLULUS'); process.exit(gagal ? 1 : 0);
