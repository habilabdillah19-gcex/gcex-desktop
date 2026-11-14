/* Uji rumus atribut kalkulasi Surpac (SA.mdlExpr) di Block Model & Drillhole.
   Pemilik 14 Nov 2026: au1 = IIF(auok>1 AND alttype = 'PRO',auok*0.80,auok) -> dulu "karakter tidak dikenal: '".
   Teks bertanda petik tunggal maupun ganda harus terbaca. Jalankan: node tools/uji/uji_mdl_expr.js  (build lama gagal) */
const fs = require('fs'), path = require('path'), ROOT = path.resolve(__dirname, '..', '..');
const A = [{ name: 'auok' }, { name: 'alttype' }, { name: 'au1', calc: true }];
const kasus = [
  ["IIF(auok>1 AND alttype = 'PRO',auok*0.80,auok)", { auok: 2, alttype: 'PRO' }, 1.6],
  ["IIF(auok>1 AND alttype = 'PRO',auok*0.80,auok)", { auok: 2, alttype: 'OX' }, 2],
  ["IIF(auok>1 AND alttype = 'PRO',auok*0.80,auok)", { auok: 0.5, alttype: 'PRO' }, 0.5],
  ['IIF(alttype = "PRO",1,0)', { auok: 0, alttype: 'PRO' }, 1],
];
let gagal = 0;
for (const f of ['web-src/gcex_base.html', 'web-src-dh/gcex_dh_base.html']) {
  const s = fs.readFileSync(path.join(ROOT, f), 'utf8'), i = s.indexOf('SA.mdlExpr=function'), j = s.indexOf('return{vars:Object.keys(vars)', i);
  const SA = {}; new Function('SA', s.slice(i, s.indexOf('}};};', j) + 5))(SA);
  for (const [ex, r, ok] of kasus) {
    let v; try { v = SA.mdlExpr(ex, A).f(r); } catch (e) { v = 'ERROR ' + e.message; }
    const lulus = typeof v === 'number' && Math.abs(v - ok) < 1e-9; if (!lulus) gagal++;
    console.log((lulus ? '  ok   ' : '  GAGAL ') + f.split('/')[0] + ' ' + ex + ' ' + JSON.stringify(r) + ' -> ' + v + ' (harap ' + ok + ')');
  }
}
console.log(gagal ? 'GAGAL (' + gagal + ')' : 'LULUS'); process.exit(gagal ? 1 : 0);
