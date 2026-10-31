const { chromium } = require('playwright');
const D = __dirname;
const MID = '7K3Q-M9XT-2HDR-PV4C';
const APPS = { bm: 'GC-Ex Block Model', dh: 'GC-Ex Drillhole', core: 'DB-Ex' };
const INFO = { id: 'L-20261029-A7KD', m: MID, a: ['bm','dh','core'], n: 'Rina Wulandari', o: 'Geologi Tambang', i: '2026-10-29', e: '2027-10-29' };
const KEY = 'GCEX1.eyJ2IjoxLCJpZCI6IkwtMjAyNjEwMjktQTdLRCIsIm0iOiI3SzNRLU05WFQtMkhEUi1QVjRDIiwiYSI6WyJibSIsImRoIiwiY29yZSJdLCJuIjoiUmluYSBXdWxhbmRhcmkifQ.Qm9udG9oLXRhbmRhLXRhbmdhbi1kZW1vLXNhamEtdGlkYWstYmVybGFrdS11bnR1ay1hcGxpa2FzaQ';
async function act(browser, file, st, after) {
  const p = await browser.newPage({ viewport: { width: 624, height: 620 }, deviceScaleFactor: 2, bypassCSP: true });
  await p.addInitScript(([st, actRes]) => {
    window.gcexLic = { state: async () => st, activate: async () => actRes, openFile: async () => null, copy: async () => true, remove: async () => true, done: () => {}, close: () => {} };
  }, [st, after && after.res]);
  await p.goto('file://' + D + '/../../electron/activate.html');
  await p.waitForTimeout(300);
  if (after) { if (after.key) await p.fill('#key', after.key); if (after.click) { await p.click(after.click); await p.waitForTimeout(250); } }
  const h = await p.evaluate(() => document.querySelector('.w').getBoundingClientRect().bottom + 10);
  await p.screenshot({ path: D + '/' + file, clip: { x: 0, y: 0, width: 624, height: Math.ceil(h) } });
  await p.close();
}
(async () => {
  const b = await chromium.launch();
  const base = { theme: 'core', appName: 'DB-Ex', machineId: MID, apps: APPS, mode: 'activate', check: { ok: false, none: true, reason: 'Belum ada lisensi di komputer ini.' } };
  await act(b, 'a1_awal.png', base);
  await act(b, 'a2_sukses.png', base, { key: KEY, click: '#go', res: { ok: true, info: INFO } });
  await act(b, 'a3_galat.png', base, { key: KEY, click: '#go', res: { ok: false, reason: 'Kunci ini untuk komputer lain (ID 4FZW-81NC-QJ6T-0B2M). ID komputer ini: ' + MID + '.' } });
  await act(b, 'a4_info.png', { ...base, mode: 'info', check: { ok: true, info: INFO, daysLeft: 365 } });
  // pembuat lisensi
  const p = await b.newPage({ viewport: { width: 900, height: 900 }, deviceScaleFactor: 2, colorScheme: 'light', locale: 'id-ID' });
  await p.goto('file://' + D + '/gen_demo.html');
  await p.evaluate(() => localStorage.clear()); await p.reload();
  await p.setInputFiles('#kf', D + '/demo_priv.json'); await p.waitForTimeout(300);
  await p.fill('#lid', 'L-20261029-A7KD');
  await p.type('#mid', '7K3QM9XT2HDRPV4C');
  await p.fill('#nm', 'Rina Wulandari'); await p.fill('#org', 'Geologi Tambang');
  await p.fill('#exp', '2027-10-29');
  await p.check('.ap[value=core]');
  await p.screenshot({ path: D + '/g1_isi.png', fullPage: true });
  await p.click('#go'); await p.waitForTimeout(300);
  await p.screenshot({ path: D + '/g2_hasil.png', fullPage: true });
  // keadaan tidak cocok (alat asli + kunci demo)
  const q = await b.newPage({ viewport: { width: 900, height: 260 }, deviceScaleFactor: 2, colorScheme: 'light', locale: 'id-ID' });
  await q.goto('file://' + D + '/gen_real.html'); await q.setInputFiles('#kf', D + '/demo_priv.json'); await q.waitForTimeout(300);
  const card = (await q.$$('.card'))[0]; await card.screenshot({ path: D + '/g3_tidakcocok.png' });
  await b.close();
})();
