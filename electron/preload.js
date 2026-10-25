// Jembatan aman antara halaman GC-Ex dan Electron (tanpa memberi akses Node penuh ke halaman)
'use strict';
const { contextBridge, ipcRenderer, webUtils } = require('electron');

let backendState = null;
const waiters = [];
ipcRenderer.on('gcex:backend', (e, st) => { backendState = st; waiters.splice(0).forEach(f => f(st)); });
// bila backend sudah siap sebelum halaman selesai dimuat, pesan di atas bisa terlewat: tanyakan langsung
async function getBackend() {
  if (backendState) return backendState;
  try { const i = await ipcRenderer.invoke('gcex:info'); if (i && i.backendUrl) { backendState = { ok: true, url: i.backendUrl, err: '' }; return backendState; } if (i && i.backendErr) return { ok: false, url: '', err: i.backendErr }; } catch (e) {}
  return new Promise(r => waiters.push(r));
}

contextBridge.exposeInMainWorld('gcexDesktop', {
  isDesktop: true,
  info: () => ipcRenderer.invoke('gcex:info'),
  // menunggu backend siap; hasil: {ok, url, err}
  backend: () => getBackend(),
  openLogs: () => ipcRenderer.invoke('gcex:openLogs'),
  // simpan file lewat dialog Windows (data: ArrayBuffer / Uint8Array)
  saveFile: (name, data, filters) => ipcRenderer.invoke('gcex:saveFile', { name, data, filters }),
  // pengganti alert() / confirm(): kotak pesan Windows asli
  alert: (msg) => { ipcRenderer.sendSync('gcex:alert', String(msg == null ? '' : msg)); },
  confirm: (msg) => ipcRenderer.sendSync('gcex:confirm', String(msg == null ? '' : msg)) === true,
  // pengganti window.prompt() (dipasang oleh halaman GC-Ex bila ada): blok sampai pengguna menjawab
  prompt: (msg, def) => ipcRenderer.sendSync('gcex:prompt', { msg: String(msg == null ? '' : msg), def: String(def == null ? '' : def) }),
  // pilih file yang sudah ada lewat dialog Windows; hasil: path lengkap atau null
  openFile: (opt) => ipcRenderer.invoke('gcex:openFile', opt || {}),
  // layar penuh: on = true / false / undefined (toggle); hasil: status baru
  fullscreen: (on) => ipcRenderer.invoke('gcex:fullscreen', on),
  onFullscreen: (cb) => ipcRenderer.on('gcex:fs', (e, v) => cb(!!v)),
  // file .prj yang dibuka dengan klik dua kali: {url, name, size, path}
  prjPending: () => ipcRenderer.invoke('gcex:prjPending'),
  onPrj: (cb) => ipcRenderer.on('gcex:openPrj', (e, o) => cb(o)),
  // tampilkan file di Windows Explorer
  showFile: (p) => ipcRenderer.invoke('gcex:showFile', p),
  // path lengkap file yang dipilih lewat <input type=file> / drag-drop ('' bila tidak diketahui)
  pathOf: (file) => { try { return webUtils.getPathForFile(file) || ''; } catch (e) { return ''; } },
  // panggil backend untuk data biner (mis. potongan block model): hasil {buf: ArrayBuffer, headers}
  apiBin: async (path, body) => {
    const st = await getBackend();
    if (!st || !st.ok) throw new Error('Backend GC-Ex tidak aktif' + (st && st.err ? ': ' + st.err : '') + '.');
    const res = await fetch(st.url + path, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body || {}) });
    if (!res.ok) { let j = null; try { j = await res.json(); } catch (e) {} throw new Error((j && j.error) || ('HTTP ' + res.status)); }
    const h = {}; res.headers.forEach((v, k) => { h[k.toLowerCase()] = v; });
    return { buf: await res.arrayBuffer(), headers: h };
  },
  // panggil backend: api('/excel/register-write', {...}) -> JSON (galat dilempar sebagai Error berisi pesan backend)
  api: async (path, body) => {
    const st = await getBackend();
    if (!st || !st.ok) throw new Error('Backend GC-Ex tidak aktif' + (st && st.err ? ': ' + st.err : '') + '. Buka Bantuan > Buka folder log.');
    const res = await fetch(st.url + path, { method: body ? 'POST' : 'GET', headers: { 'Content-Type': 'application/json' }, body: body ? JSON.stringify(body) : undefined });
    let j = null; try { j = await res.json(); } catch (e) {}
    if (!res.ok || !j || j.ok === false) throw new Error((j && (j.error || (j.detail && JSON.stringify(j.detail)))) || ('HTTP ' + res.status));
    return j;
  }
});
