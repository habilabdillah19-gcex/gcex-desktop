// Tanda hak cipta (watermark) di sudut jendela semua aplikasi GC-Ex.
// Dipasang oleh proses utama setiap kali halaman selesai dimuat; dipasang ulang bila elemennya dihapus.
// Tidak menangkap klik (pointer-events: none) sehingga tidak mengganggu kontrol di bawahnya.
'use strict';

const TEXT = 'Copyright © Habil Abdillah 2026';

// posisi per aplikasi: di ujung kanan bilah status bawah. Bilah status diberi ruang kosong (reserve) selebar
// watermark supaya tidak ada teks / data yang tertutup (dicek dengan screenshot tiap aplikasi).
// Ketiga aplikasi menulis 'Copyright (c) Habil Abdillah 2026' di bilah statusnya sendiri: watermark cadangan ini
// hanya muncul bila tulisan itu hilang / dihapus / disembunyikan (existing).
const POS = {
  bm: { bottom: '6px', right: '10px', reserve: 'footer#status', existing: 'footer#status' },
  dh: { bottom: '6px', right: '10px', reserve: 'footer#status', existing: 'footer#status' },
  core: { bottom: '6px', right: '10px', reserve: '#sbar', existing: '#sbar' }
};
const RESERVE_PX = 220;

function script(theme) {
  const p = POS[theme] || POS.bm;
  const css = [
    'position:fixed', 'bottom:' + p.bottom, 'right:' + p.right, 'z-index:2147483647', 'pointer-events:none',
    'user-select:none', 'font:600 11px/1.2 "Segoe UI",system-ui,Arial,sans-serif', 'letter-spacing:.02em',
    'color:rgba(20,26,38,.62)', 'background:rgba(255,255,255,.55)', 'padding:2px 7px', 'border-radius:4px',
    'box-shadow:0 0 0 1px rgba(20,26,38,.10)', 'white-space:nowrap', 'opacity:1', 'display:block', 'visibility:visible'
  ].map(s => s + ' !important').join(';');
  const reserve = p.reserve ? p.reserve + '{padding-right:' + RESERVE_PX + 'px !important}' : '';
  return `(() => {
  const ID = 'gcex-copyright-mark', TXT = ${JSON.stringify(TEXT)}, CSS = ${JSON.stringify(css)}, RES = ${JSON.stringify(reserve)}, EX = ${JSON.stringify(p.existing || '')};
  const has = () => { if (!EX) return false; const f = document.querySelector(EX); return !!(f && /Copyright[^A-Za-z]{1,4}Habil[^A-Za-z]{1,4}Abdillah/i.test(f.textContent || '') && f.offsetParent !== null); };
  const put = () => {
    if (!document.body) return;
    if (has()) { const o = document.getElementById(ID); if (o) o.remove(); const c = document.getElementById(ID + '-css'); if (c) c.remove(); return; }
    if (RES) { let st = document.getElementById(ID + '-css'); if (!st) { st = document.createElement('style'); st.id = ID + '-css'; document.head.appendChild(st); } if (st.textContent !== RES) st.textContent = RES; }
    let el = document.getElementById(ID);
    if (!el) { el = document.createElement('div'); el.id = ID; el.setAttribute('aria-hidden', 'true'); document.body.appendChild(el); }
    if (el.textContent !== TXT) el.textContent = TXT;
    if (el.getAttribute('style') !== CSS) el.setAttribute('style', CSS);
  };
  put();
  if (!window.__gcexMarkObs) {
    let busy = false;
    window.__gcexMarkObs = new MutationObserver(() => {
      if (busy) return;
      const el = document.getElementById(ID), ok = has();
      if ((ok && el) || (!ok && (!el || el.textContent !== TXT || el.getAttribute('style') !== CSS || (RES && !document.getElementById(ID + '-css'))))) { busy = true; put(); busy = false; }
    });
    window.__gcexMarkObs.observe(document.documentElement, { childList: true, subtree: true, characterData: true, attributes: true, attributeFilter: ['style', 'class'] });
  }
  return true;
})();`;
}

module.exports = { TEXT, POS, script };
