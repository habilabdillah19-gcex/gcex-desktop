// GC-Ex Desktop - lisensi aplikasi (kunci lisensi terikat komputer)
// - ID Komputer = hash MachineGuid Windows (fallback: nama komputer + CPU + MAC), ditampilkan sebagai XXXX-XXXX-XXXX-XXXX.
// - Kunci lisensi = "GCEX1.<payload base64url>.<tanda tangan Ed25519 base64url>". Payload JSON:
//     { v:1, id, m:<ID Komputer>, a:['bm','dh','core'] | ['*'], n:<pemegang>, o:<organisasi>, i:<tgl terbit>, e:<tgl kedaluwarsa | ''> }
// - Aplikasi hanya memegang KUNCI PUBLIK; kunci privat penerbit disimpan pemilik GC-Ex (alat: tools/lisensi/GCEx_Pembuat_Lisensi.html).
// - Satu file lisensi dipakai bersama ketiga aplikasi: %APPDATA%\GC-Ex Lisensi\lisensi.json
'use strict';
const crypto = require('crypto');
const fs = require('fs');
const os = require('os');
const path = require('path');
const { execFileSync } = require('child_process');

const PUBKEY = '-----BEGIN PUBLIC KEY-----\nMCowBQYDK2VwAyEA9r0X96ABXcPSrjl0edVsTn836jFZxwBDmFvX4aie0ug=\n-----END PUBLIC KEY-----\n';
const APPS = { bm: 'GC-Ex Block Model', dh: 'GC-Ex Drillhole', core: 'Core-Ex' };
const B32 = '0123456789ABCDEFGHJKMNPQRSTVWXYZ';

let _mid = null;
function rawMachine() {
  if (process.platform === 'win32') {
    try {
      const out = execFileSync('reg', ['query', 'HKLM\\SOFTWARE\\Microsoft\\Cryptography', '/v', 'MachineGuid'], { encoding: 'utf8', windowsHide: true, timeout: 5000 });
      const m = /MachineGuid\s+REG_SZ\s+([0-9a-fA-F-]{20,})/.exec(out);
      if (m) return 'guid:' + m[1].toLowerCase();
    } catch (e) { /* lanjut ke cadangan */ }
  }
  const nets = os.networkInterfaces(), macs = [];
  Object.keys(nets).forEach(k => (nets[k] || []).forEach(n => { if (!n.internal && n.mac && n.mac !== '00:00:00:00:00:00') macs.push(n.mac); }));
  macs.sort();
  return 'host:' + os.hostname().toLowerCase() + '|' + ((os.cpus()[0] || {}).model || '') + '|' + (macs[0] || '');
}
function machineId() {
  if (_mid) return _mid;
  const h = crypto.createHash('sha256').update('GC-Ex|' + rawMachine()).digest();
  let bits = 0, val = 0, s = '';
  for (let i = 0; i < h.length && s.length < 16; i++) { val = (val << 8) | h[i]; bits += 8; while (bits >= 5 && s.length < 16) { s += B32[(val >>> (bits - 5)) & 31]; bits -= 5; } }
  _mid = s.match(/.{4}/g).join('-');
  return _mid;
}
function b64u(buf) { return Buffer.from(buf).toString('base64').replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, ''); }
function unb64u(s) { s = String(s).replace(/-/g, '+').replace(/_/g, '/'); while (s.length % 4) s += '='; return Buffer.from(s, 'base64'); }
function today() { return new Date().toISOString().slice(0, 10); }

function parseKey(key) {
  const k = String(key || '').replace(/\s+/g, '');
  const p = k.split('.');
  if (p.length !== 3 || p[0] !== 'GCEX1') return { ok: false, reason: 'Format kunci tidak dikenal. Kunci GC-Ex diawali "GCEX1."' };
  let data;
  try { data = JSON.parse(unb64u(p[1]).toString('utf8')); } catch (e) { return { ok: false, reason: 'Isi kunci rusak (salah salin?).' }; }
  let good = false;
  try { good = crypto.verify(null, Buffer.from(p[0] + '.' + p[1], 'utf8'), crypto.createPublicKey(PUBKEY), unb64u(p[2])); } catch (e) { good = false; }
  if (!good) return { ok: false, reason: 'Tanda tangan kunci tidak sah (kunci diubah, terpotong, atau bukan dari penerbit GC-Ex).' };
  return { ok: true, key: k, data };
}

function verify(key, appKey, lastSeen) {
  const r = parseKey(key);
  if (!r.ok) return r;
  const d = r.data, mid = machineId();
  const info = { id: d.id || '', n: d.n || '', o: d.o || '', e: d.e || '', i: d.i || '', a: Array.isArray(d.a) ? d.a : [], m: d.m || '' };
  if (String(d.m || '').toUpperCase() !== mid) return { ok: false, reason: 'Kunci ini untuk komputer lain (ID ' + (d.m || '?') + '). ID komputer ini: ' + mid + '.', info };
  if (!(info.a.indexOf('*') >= 0 || info.a.indexOf(appKey) >= 0)) return { ok: false, reason: 'Kunci ini tidak berlaku untuk ' + (APPS[appKey] || appKey) + ' (berlaku: ' + info.a.map(x => x === '*' ? 'semua aplikasi' : (APPS[x] || x)).join(', ') + ').', info };
  const t = today();
  if (info.e) {
    if (lastSeen && lastSeen > info.e && t < lastSeen) return { ok: false, expired: true, reason: 'Lisensi kedaluwarsa (' + info.e + '); tanggal komputer lebih awal dari pemakaian terakhir (' + lastSeen + '). Minta kunci baru ke penerbit GC-Ex.', info };
    if (t > info.e) return { ok: false, expired: true, reason: 'Lisensi kedaluwarsa sejak ' + info.e + '. Minta kunci baru ke penerbit GC-Ex.', info };
  }
  const left = info.e ? Math.round((Date.parse(info.e) - Date.parse(t)) / 864e5) : null;
  return { ok: true, key: r.key, info, daysLeft: left };
}

function create(appDataDir) {
  const dir = path.join(appDataDir, 'GC-Ex Lisensi'), file = path.join(dir, 'lisensi.json');
  const read = () => { try { return JSON.parse(fs.readFileSync(file, 'utf8')); } catch (e) { return {}; } };
  const write = (o) => { fs.mkdirSync(dir, { recursive: true }); fs.writeFileSync(file, JSON.stringify(o, null, 1)); };
  return {
    file, machineId, apps: APPS,
    check(appKey) {
      const st = read();
      if (!st.key) return { ok: false, none: true, reason: 'Belum ada lisensi di komputer ini.' };
      const prev = st.last, t = today();
      /* tanggal terbesar yang pernah terlihat dicatat (juga saat gagal) -> memundurkan jam tidak menghidupkan lisensi kedaluwarsa */
      if (!st.last || t > st.last) { st.last = t; try { write(st); } catch (e) {} }
      return verify(st.key, appKey, st.last > t ? st.last : prev);
    },
    activate(key, appKey) {
      const st = read(), r = verify(key, appKey, st.last);
      if (!r.ok) return r;
      write({ key: r.key, at: new Date().toISOString(), last: today() });
      return r;
    },
    remove() { try { fs.unlinkSync(file); } catch (e) {} }
  };
}
module.exports = { create, machineId, parseKey, verify, APPS };
