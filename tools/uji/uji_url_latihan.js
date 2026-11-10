/* URL data latihan di aplikasi terpasang harus sampai ke cabang 'latihan/' penangan gcexfile di electron/main.js.
   Meniru persis cara penangan membaca URL (new URL(req.url).pathname) dan membaca bentuk URL dari web-src/demodata.js.
   Pemakaian: node tools/uji/uji_url_latihan.js */
const fs = require('fs'), path = require('path'), root = path.join(__dirname, '..', '..');
const dd = fs.readFileSync(path.join(root, 'web-src', 'demodata.js'), 'utf8'), mj = fs.readFileSync(path.join(root, 'electron', 'main.js'), 'utf8');
const m = /DLAT\.src === 'desktop' \? '([^']+)' \+ nm/.exec(dd); if (!m) { console.log('GAGAL: bentuk URL tidak ditemukan di demodata.js'); process.exit(1); }
if (!/t0\.startsWith\('latihan\/'\)/.test(mj) || !/new URL\(req\.url\)\.pathname\.replace/.test(mj)) { console.log('GAGAL: penangan di main.js berubah; sesuaikan uji ini'); process.exit(1); }
let gagal = 0;
for (const nm of ['SIM_collar.csv', 'SIM_BM_GC_kadar.csv', 'QV_Lensa2_Leapfrog.obj']) {
  const u = m[1] + nm, t0 = new URL(u).pathname.replace(/^\/+/, ''), ok = t0.startsWith('latihan/') && path.basename(t0.slice(8)) === nm;
  console.log((ok ? '  ok   ' : '  GAGAL ') + u + ' -> ' + t0); if (!ok) gagal++;
}
const lama = new URL('gcexfile://latihan/SIM_collar.csv').pathname.replace(/^\/+/, '');
console.log('  (bentuk lama gcexfile://latihan/... -> ' + lama + ' : ' + (lama.startsWith('latihan/') ? 'sampai' : 'tidak sampai = 404') + ')');
console.log(gagal ? '\nGAGAL' : '\nLULUS'); process.exit(gagal ? 1 : 0);
