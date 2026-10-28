// GC-Ex Desktop - proses utama Electron
// Tugas: membuka jendela GC-Ex (app/index.html = Block Model, app-dh/index.html = Drillhole, app-core/index.html = Core Interpretation),
// menjalankan backend Python (FastAPI),
// memberi izin folder proyek tanpa dialog berulang, menu, log, dan menutup backend saat keluar.
'use strict';
const { app, BrowserWindow, Menu, dialog, shell, session, ipcMain, protocol, clipboard, net: enet } = require('electron');
const { pathToFileURL } = require('url');
const path = require('path');
const fs = require('fs');
const net = require('net');
const http = require('http');
const { spawn } = require('child_process');
const watermark = require('./watermark');

// Aplikasi mana yang dijalankan (Block Model / Drillhole) ditentukan oleh field "gcex" di package.json
// (diisi electron-builder lewat extraMetadata). Saat pengembangan: set GCEX_APP=dh untuk Drillhole, GCEX_APP=core untuk Core Interpretation.
let PKG = {};
try { PKG = require('../package.json'); } catch (e) {}
const G = Object.assign({ page: 'app/index.html', title: 'GC-Ex Block Model', icon: 'build/icon.ico', theme: 'bm' }, PKG.gcex || {});
if (process.env.GCEX_APP === 'dh' && !app.isPackaged) {
  Object.assign(G, { page: 'app-dh/index.html', title: 'GC-Ex Drillhole', icon: 'build/icon-dh.ico', theme: 'dh' });
  app.setName('GC-Ex Drillhole');
  app.setPath('userData', path.join(app.getPath('appData'), 'GC-Ex Drillhole'));
}
if (process.env.GCEX_APP === 'core' && !app.isPackaged) {
  Object.assign(G, { page: 'app-core/index.html', title: 'GC-Ex Core Interpretation', icon: 'build/icon-core.ico', theme: 'core' });
  app.setName('GC-Ex Core Interpretation');
  app.setPath('userData', path.join(app.getPath('appData'), 'GC-Ex Core Interpretation'));
}
const APP_NAME = G.title;
// lisensi (kunci terikat komputer); diwajibkan pada aplikasi terpasang. Saat pengembangan: set GCEX_LIC=1 untuk menguji.
const LIC = require('./license').create(app.getPath('appData'));
const LIC_ON = app.isPackaged || process.env.GCEX_LIC === '1';
// DevTools & lihat sumber hanya untuk pengembangan (tidak di aplikasi terpasang)
const DEVTOOLS = !app.isPackaged && process.env.GCEX_DEVTOOLS !== '0';
let mainWin = null;
let backend = { proc: null, port: 0, url: '', ok: false, err: '' };

// ---------- log sederhana di %APPDATA%/GC-Ex/logs ----------
const logDir = path.join(app.getPath('userData'), 'logs');
try { fs.mkdirSync(logDir, { recursive: true }); } catch (e) {}
const logFile = path.join(logDir, 'gcex-' + new Date().toISOString().slice(0, 10) + '.log');
function log(...a) {
  const line = new Date().toISOString() + ' ' + a.map(x => (typeof x === 'string' ? x : JSON.stringify(x))).join(' ') + '\n';
  try { fs.appendFileSync(logFile, line); } catch (e) {}
  if (!app.isPackaged) process.stdout.write(line);
}
process.on('uncaughtException', e => log('[uncaught]', e && e.stack || String(e)));

// ---------- grafis: pilih GPU berperforma tinggi pada laptop dengan 2 kartu grafis ----------
app.commandLine.appendSwitch('force_high_performance_gpu');

// ---------- file proyek .prj: dibuka dengan klik dua kali (asosiasi file dipasang installer) ----------
// .prj = arsip ZIP; entri pertama gcex_prj.json (tidak dikompresi) berisi nama aplikasi pemilik.
// .prj milik aplikasi GC-Ex lain diteruskan ke aplikasi itu; .prj non-GC-Ex (mis. file proyeksi ESRI) dibuka di Notepad.
protocol.registerSchemesAsPrivileged([{ scheme: 'gcexfile', privileges: { standard: true, secure: true, supportFetchAPI: true, stream: true, corsEnabled: true, bypassCSP: true } }]);
const PRJ = { open: {}, pend: [], tok: 0 };
function argPrj(argv) { return (argv || []).slice(1).find(a => /\.prj$/i.test(String(a)) && fs.existsSync(a)) || null; }
function prjOwner(p) {
  try {
    const fd = fs.openSync(p, 'r'), b = Buffer.alloc(65536), n = fs.readSync(fd, b, 0, 65536, 0); fs.closeSync(fd);
    if (n < 30 || b.readUInt32LE(0) !== 0x04034b50) return null;
    const meth = b.readUInt16LE(8), csz = b.readUInt32LE(18), nl = b.readUInt16LE(26), xl = b.readUInt16LE(28), nm = b.toString('utf8', 30, 30 + nl);
    if (nm !== 'gcex_prj.json' || meth !== 0 || 30 + nl + xl + csz > n) return null;
    const j = JSON.parse(b.toString('utf8', 30 + nl + xl, 30 + nl + xl + csz));
    return j && j.format === 'gcex-prj' ? (j.app || APP_NAME) : null;
  } catch (e) { return null; }
}
const sharedFile = () => path.join(app.getPath('appData'), 'GC-Ex-shared', 'apps.json');
function readShared() { try { return JSON.parse(fs.readFileSync(sharedFile(), 'utf8')); } catch (e) { return {}; } }
/* folder pemberitahuan lisensi pihak ketiga & penafian merek (resources/legal) */
function legalDir() { return app.isPackaged ? path.join(process.resourcesPath, 'legal') : path.join(__dirname, '..', 'legal'); }
function openLegal(name) { const d = legalDir(), f = path.join(d, name || 'LISENSI_PIHAK_KETIGA.txt'); shell.openPath(fs.existsSync(f) ? f : d); }

// ---------- syarat penggunaan & penafian: wajib disetujui sekali per versi syarat (juga ditampilkan di installer) ----------
const TERMS_VERSION = '2026-10-28';
function ensureTerms() {
  const s = readSet();
  if (s.termsAccepted === TERMS_VERSION) return true;
  for (;;) {
    const r = dialog.showMessageBoxSync({
      type: 'info', title: APP_NAME + ' - Syarat Penggunaan', noLink: true, defaultId: 0, cancelId: 2,
      buttons: ['Setuju', 'Baca selengkapnya', 'Tidak setuju (keluar)'],
      message: 'Syarat Penggunaan & Penafian GC-Ex',
      detail: 'Copyright \u00a9 2026 Habil Abdillah. GC-Ex dilindungi UU No. 28 Tahun 2014 tentang Hak Cipta dan dilisensikan, bukan dijual.\n\n' +
        '\u2022 Dilarang menjual, membagikan ke pihak lain, membongkar, atau menghapus tanda hak cipta tanpa izin tertulis.\n' +
        '\u2022 Disediakan "apa adanya" tanpa jaminan. Hasil pemodelan, estimasi dan nilai geoteknik dari AI adalah alat bantu / perkiraan, wajib diperiksa orang yang kompeten, dan tidak boleh menjadi satu-satunya dasar keputusan keselamatan.\n' +
        '\u2022 Data diproses di komputer ini saja; tanggung jawab atas izin pemakaian data perusahaan ada pada pengguna.\n' +
        '\u2022 Komponen open source tetap di bawah lisensinya masing-masing (menu Bantuan).\n\n' +
        'Pilih "Baca selengkapnya" untuk teks lengkap (Bahasa Indonesia & English).'
    });
    if (r === 1) { openLegal('SYARAT_PENGGUNAAN.txt'); continue; }
    if (r !== 0) { log('[syarat] tidak disetujui, keluar'); return false; }
    writeSet({ termsAccepted: TERMS_VERSION, termsAcceptedAt: new Date().toISOString() });
    log('[syarat] disetujui versi', TERMS_VERSION);
    return true;
  }
}

// watermark hak cipta di sudut jendela, dipasang ulang setiap halaman dimuat
function markWindow(wc) { try { wc.executeJavaScript(watermark.script(G.theme), true).catch(() => {}); } catch (e) {} }
function regSelf() { if (!app.isPackaged) return; try { fs.mkdirSync(path.dirname(sharedFile()), { recursive: true }); const o = readShared(); o[G.theme] = process.execPath; fs.writeFileSync(sharedFile(), JSON.stringify(o, null, 1)); } catch (e) {} }
// hasil: 'here' (dibuka di aplikasi ini), 'other' (diteruskan), 'none' (bukan proyek GC-Ex / gagal)
function routePrj(p) {
  const own = prjOwner(p);
  if (!own) {
    log('[prj] bukan proyek GC-Ex:', p);
    try { spawn('notepad.exe', [p], { detached: true, stdio: 'ignore' }).unref(); } catch (e) {}
    dialog.showMessageBox(mainWin || undefined, { type: 'info', title: APP_NAME, message: 'File ini bukan proyek GC-Ex.',
      detail: p + '\n\nEkstensi .prj juga dipakai software GIS (file proyeksi ESRI). File ini dibuka dengan Notepad.' });
    return 'none';
  }
  if (own !== APP_NAME) {
    const key = /Drillhole/i.test(own) ? 'dh' : /Core/i.test(own) ? 'core' : 'bm', exe = readShared()[key];
    log('[prj] milik', own, '->', exe || '(tidak ditemukan)');
    if (exe && fs.existsSync(exe)) { try { spawn(exe, [p], { detached: true, stdio: 'ignore' }).unref(); return 'other'; } catch (e) { log('[prj] gagal meneruskan', e.message); } }
    dialog.showMessageBox(mainWin || undefined, { type: 'warning', title: APP_NAME, message: 'Proyek ini dibuat dengan ' + own + '.',
      detail: 'Buka dengan aplikasi ' + own + ' (jalankan aplikasinya sekali agar GC-Ex mengenalinya), atau pasang aplikasi tersebut.' });
    return 'none';
  }
  const t = 'f' + (++PRJ.tok); PRJ.open[t] = p;
  const o = { url: 'gcexfile://open/' + t, name: path.basename(p), size: fs.statSync(p).size, path: p };
  if (mainWin && PRJ.ready) mainWin.webContents.send('gcex:openPrj', o); else PRJ.pend.push(o);
  if (mainWin) { if (mainWin.isMinimized()) mainWin.restore(); mainWin.focus(); }
  return 'here';
}
ipcMain.handle('gcex:prjPending', () => PRJ.pend.shift() || null);

// ---------- hanya satu jendela GC-Ex ----------
if (!app.requestSingleInstanceLock()) { app.quit(); }
app.on('second-instance', (e, argv) => { if (mainWin) { if (mainWin.isMinimized()) mainWin.restore(); mainWin.focus(); } const f = argPrj(argv); if (f) routePrj(f); });

// ---------- layar penuh (tombol di bilah atas, F11, menu Tampilan) ----------
ipcMain.handle('gcex:fullscreen', (e, on) => { if (!mainWin) return false; const v = on == null ? !mainWin.isFullScreen() : !!on; mainWin.setFullScreen(v); return v; });

// ---------- backend Python ----------
function freePort() {
  return new Promise((res, rej) => { const s = net.createServer(); s.unref(); s.on('error', rej); s.listen(0, '127.0.0.1', () => { const p = s.address().port; s.close(() => res(p)); }); });
}
function ping(url, ms) {
  return new Promise(res => { const r = http.get(url + '/health', { timeout: ms }, x => { res(x.statusCode === 200); x.resume(); }); r.on('error', () => res(false)); r.on('timeout', () => { r.destroy(); res(false); }); });
}
async function startBackend() {
  backend.port = await freePort();
  backend.url = 'http://127.0.0.1:' + backend.port;
  let cmd, args, cwd;
  if (app.isPackaged) {
    // backend hasil PyInstaller: resources/backend/gcex-backend.exe
    cmd = path.join(process.resourcesPath, 'backend', process.platform === 'win32' ? 'gcex-backend.exe' : 'gcex-backend');
    args = ['--port', String(backend.port)];
    cwd = path.dirname(cmd);
  } else {
    // mode pengembangan: python backend/run_backend.py
    cmd = process.env.GCEX_PYTHON || (process.platform === 'win32' ? 'python' : 'python3');
    args = [path.join(__dirname, '..', 'backend', 'run_backend.py'), '--port', String(backend.port)];
    cwd = path.join(__dirname, '..', 'backend');
  }
  if (app.isPackaged && !fs.existsSync(cmd)) { backend.err = 'backend tidak ditemukan: ' + cmd; log(backend.err); return; }
  log('[backend] start', cmd, args.join(' '));
  try {
    backend.proc = spawn(cmd, args, { cwd, windowsHide: true, env: Object.assign({}, process.env, { GCEX_LOG_DIR: logDir, GCEX_CACHE: path.join(app.getPath('userData'), 'cache') }) });
  } catch (e) { backend.err = String(e); log('[backend] gagal start', backend.err); return; }
  backend.proc.stdout.on('data', d => log('[backend]', String(d).trim()));
  backend.proc.stderr.on('data', d => log('[backend]', String(d).trim()));
  backend.proc.on('exit', c => { log('[backend] keluar, kode', c); backend.ok = false; backend.proc = null; });
  for (let i = 0; i < 60; i++) { // tunggu maks ~30 detik
    if (await ping(backend.url, 800)) { backend.ok = true; log('[backend] siap di', backend.url); return; }
    await new Promise(r => setTimeout(r, 500));
  }
  backend.err = 'backend tidak merespons dalam 30 detik'; log('[backend]', backend.err);
}
function stopBackend() {
  if (!backend.proc) return;
  try {
    if (process.platform === 'win32') spawn('taskkill', ['/pid', String(backend.proc.pid), '/T', '/F'], { windowsHide: true });
    else backend.proc.kill();
  } catch (e) {}
  backend.proc = null;
}

// ---------- jembatan ke halaman (preload) ----------
ipcMain.handle('gcex:info', () => ({ app: APP_NAME, version: app.getVersion(), backendUrl: backend.ok ? backend.url : '', backendErr: backend.err, logDir, userData: app.getPath('userData'), platform: process.platform }));
ipcMain.handle('gcex:openLogs', () => shell.openPath(logDir));
ipcMain.handle('gcex:saveFile', async (e, opt) => {
  const r = await dialog.showSaveDialog(mainWin, { defaultPath: opt && opt.name, filters: opt && opt.filters });
  if (r.canceled || !r.filePath) return null;
  fs.writeFileSync(r.filePath, Buffer.from(opt.data));
  return r.filePath;
});

// pengganti window.prompt(): Electron tidak menyediakannya. Halaman memanggil sendSync dan menunggu
// sampai jendela isian kecil ini ditutup (OK -> teks, Batal / tutup -> null), persis seperti prompt() di browser.
ipcMain.on('gcex:prompt', (e, o) => {
  const parent = BrowserWindow.fromWebContents(e.sender) || mainWin;
  const id = 'p' + Date.now() + Math.floor(Math.random() * 1e6);
  const win = new BrowserWindow({
    parent, modal: true, width: 480, height: 210, resizable: false, minimizable: false, maximizable: false, fullscreenable: false,
    show: false, title: 'GC-Ex', backgroundColor: '#ffffff', icon: path.join(__dirname, '..', G.icon),
    webPreferences: { preload: path.join(__dirname, 'prompt-preload.js'), contextIsolation: true, nodeIntegration: false, sandbox: true, spellcheck: false, devTools: DEVTOOLS }
  });
  win.setMenu(null);
  let done = false;
  const ch = 'gcex:prompt-result:' + id;
  const finish = (v) => { if (done) return; done = true; ipcMain.removeAllListeners(ch); e.returnValue = v; if (!win.isDestroyed()) win.close(); };
  ipcMain.once(ch, (ev, v) => finish(v));
  const onSize = (ev, h) => { if (ev.sender === win.webContents && !win.isDestroyed()) { const [w] = win.getContentSize(); win.setContentSize(w, Math.max(150, Math.min(420, h | 0))); } };
  ipcMain.on('gcex:prompt-size', onSize);
  win.on('closed', () => { ipcMain.removeListener('gcex:prompt-size', onSize); finish(null); });
  win.once('ready-to-show', () => win.show());
  win.loadFile(path.join(__dirname, 'prompt.html'), { query: { id, theme: G.theme, msg: String((o && o.msg) || ''), def: String((o && o.def) || '') } });
});

// pengganti alert() / confirm(): kotak pesan Windows asli. Menghindari cacat Electron di Windows
// (setelah alert/confirm bawaan, kolom isian kadang tidak bisa diketik sampai jendela diklik ulang).
function refocus(wc) { setTimeout(() => { try { const w = BrowserWindow.fromWebContents(wc); if (w && !w.isDestroyed()) { w.focus(); wc.focus(); } } catch (e) {} }, 0); }
function splitMsg(m) { const t = String(m == null ? '' : m); const i = t.indexOf('\n'); return i > 0 && t.length > 160 ? { message: t.slice(0, i), detail: t.slice(i + 1).trim() } : { message: t }; }
ipcMain.on('gcex:alert', (e, m) => {
  const parent = BrowserWindow.fromWebContents(e.sender) || mainWin;
  dialog.showMessageBoxSync(parent, Object.assign({ type: 'info', title: 'GC-Ex', buttons: ['OK'], noLink: true }, splitMsg(m)));
  e.returnValue = true; refocus(e.sender);
});
ipcMain.on('gcex:confirm', (e, m) => {
  const parent = BrowserWindow.fromWebContents(e.sender) || mainWin;
  const r = dialog.showMessageBoxSync(parent, Object.assign({ type: 'question', title: 'GC-Ex', buttons: ['OK', 'Batal'], defaultId: 0, cancelId: 1, noLink: true }, splitMsg(m)));
  e.returnValue = r === 0; refocus(e.sender);
});

// pilih file yang sudah ada (mis. workbook register Excel); hasil: path lengkap atau null
ipcMain.handle('gcex:openFile', async (e, opt) => {
  const r = await dialog.showOpenDialog(mainWin, { title: opt && opt.title, defaultPath: opt && opt.defaultPath, filters: opt && opt.filters, properties: ['openFile'] });
  if (r.canceled || !r.filePaths || !r.filePaths.length) return null;
  return r.filePaths[0];
});
// pilih folder (mis. folder foto core box); hasil: path lengkap atau null
ipcMain.handle('gcex:openFolder', async (e, opt) => {
  const r = await dialog.showOpenDialog(mainWin, { title: opt && opt.title, defaultPath: opt && opt.defaultPath, properties: ['openDirectory'] });
  if (r.canceled || !r.filePaths || !r.filePaths.length) return null;
  return r.filePaths[0];
});
ipcMain.handle('gcex:showFile', (e, p) => { if (p && fs.existsSync(p)) shell.showItemInFolder(p); });

// ---------- jendela ----------
function createWindow() {
  mainWin = new BrowserWindow({
    width: 1600, height: 950, minWidth: 1100, minHeight: 700, show: false,
    title: APP_NAME, backgroundColor: G.theme === 'dh' ? '#f0c047' : G.theme === 'core' ? '#ecebe6' : '#1f3a5f', icon: path.join(__dirname, '..', G.icon),
    webPreferences: { preload: path.join(__dirname, 'preload.js'), contextIsolation: true, nodeIntegration: false, sandbox: true, spellcheck: false, devTools: DEVTOOLS,
      // simpan otomatis & sinyal kunci proyek tetap berjalan normal walau jendela diminimalkan
      backgroundThrottling: false }
  });
  mainWin.once('ready-to-show', () => { mainWin.maximize(); mainWin.show(); });
  mainWin.webContents.on('did-finish-load', () => { try { mainWin.webContents.setZoomFactor(zoomNow()); } catch (e) {} PRJ.ready = true; markWindow(mainWin.webContents); });
  mainWin.webContents.on('dom-ready', () => markWindow(mainWin.webContents));
  mainWin.webContents.on('did-start-loading', () => { PRJ.ready = false; });
  mainWin.on('enter-full-screen', () => { try { buildMenu(); } catch (e) {} try { mainWin.webContents.send('gcex:fs', true); } catch (e) {} });
  mainWin.on('leave-full-screen', () => { try { buildMenu(); } catch (e) {} try { mainWin.webContents.send('gcex:fs', false); } catch (e) {} });
  mainWin.webContents.on('zoom-changed', (e, dir) => stepZoom(dir === 'in' ? +1 : -1));
  mainWin.loadFile(path.join(__dirname, '..', G.page));
  // tautan luar dibuka di browser biasa, bukan di jendela GC-Ex
  mainWin.webContents.setWindowOpenHandler(({ url }) => { if (/^https?:/i.test(url)) { shell.openExternal(url); return { action: 'deny' }; } return { action: 'allow' }; });
  // menutup jendela: GC-Ex menyimpan dulu (komputer + folder proyek) dan melepas kunci proyek, baru jendela ditutup.
  // Kotak pilihan hanya muncul bila penyimpanan gagal atau GC-Ex tidak merespons.
  let closeOK = false, closing = false;
  mainWin.on('close', async (e) => {
    if (closeOK) return;
    e.preventDefault();
    if (closing) return;
    closing = true;
    let r = null;
    try {
      r = await Promise.race([
        mainWin.webContents.executeJavaScript('window.gcexFlush ? window.gcexFlush() : ({ok:true})', true),
        new Promise((res) => setTimeout(() => res({ ok: false, err: 'GC-Ex tidak merespons dalam 20 detik' }), 20000))
      ]);
    } catch (err) { r = { ok: false, err: String(err && err.message || err) }; }
    closing = false;
    log('[tutup]', JSON.stringify(r));
    if (!r || !r.ok) {
      const c = dialog.showMessageBoxSync(mainWin, { type: 'warning', title: 'GC-Ex', buttons: ['Tutup tanpa menyimpan', 'Batal'], defaultId: 1, cancelId: 1, noLink: true,
        message: 'Perubahan terakhir belum bisa disimpan ke folder proyek.',
        detail: (r && r.err ? 'Penyebab: ' + r.err + '\n\n' : '') + 'Pilih Batal, lalu periksa menu Proyek (Hubungkan lagi / Simpan sekarang). Pekerjaan tetap tersimpan di penyimpanan GC-Ex di komputer ini.' });
      if (c !== 0) return;
      await bypassUnload();
    }
    closeOK = true;
    mainWin.close();
  });
  // perubahan belum tersimpan: Electron membatalkan penutupan TANPA pesan bila halaman menolak unload -> tanyakan
  mainWin.webContents.on('will-prevent-unload', (e) => {
    const r = dialog.showMessageBoxSync(mainWin, { type: 'warning', title: 'GC-Ex', buttons: ['Lanjutkan tanpa menyimpan', 'Batal'], defaultId: 1, cancelId: 1, noLink: true,
      message: 'Ada perubahan yang belum tersimpan di folder proyek. Tetap tutup / muat ulang GC-Ex?',
      detail: 'Pilih Batal, lalu Proyek > Simpan sekarang bila ingin menyimpannya dulu. Pekerjaan tetap tersimpan di penyimpanan GC-Ex di komputer ini.' });
    if (r === 0) e.preventDefault();
  });
  // jangan pernah meninggalkan halaman GC-Ex (mis. file dijatuhkan di luar kotak unggah, tautan luar)
  mainWin.webContents.on('will-navigate', (e, url) => {
    if (url === mainWin.webContents.getURL()) return;
    e.preventDefault();
    if (/^https?:/i.test(url)) shell.openExternal(url);
  });
  mainWin.webContents.on('render-process-gone', (e, d) => log('[renderer] berhenti', d));
  mainWin.webContents.on('console-message', (e, level, msg) => { const lv = typeof level === 'number' ? level : ({ warning: 2, error: 3 }[e && e.level] || 0); const m = msg !== undefined ? msg : e && e.message; if (lv >= 2) log('[halaman]', m); });
  mainWin.on('closed', () => { mainWin = null; });
}

// pengguna sudah memilih lanjut tanpa menyimpan: matikan peringatan halaman supaya tidak bertanya dua kali
async function bypassUnload() {
  try { await mainWin.webContents.executeJavaScript('try{if(window.FP){FP._noWarn=1;FP._reloading=1;}}catch(e){}', true); } catch (e) {}
}

// muat ulang dengan aman: simpan dulu (komputer + folder proyek), baru halaman dimuat ulang
async function reloadSafe() {
  if (!mainWin) return;
  let r = null;
  try {
    r = await Promise.race([
      mainWin.webContents.executeJavaScript('window.gcexFlush ? window.gcexFlush() : ({ok:true})', true),
      new Promise((res) => setTimeout(() => res({ ok: false, err: 'GC-Ex tidak merespons dalam 20 detik' }), 20000))
    ]);
  } catch (err) { r = { ok: false, err: String(err && err.message || err) }; }
  log('[muat ulang]', JSON.stringify(r));
  if (!r || !r.ok) {
    const c = dialog.showMessageBoxSync(mainWin, { type: 'warning', title: 'GC-Ex', buttons: ['Muat ulang tanpa menyimpan', 'Batal'], defaultId: 1, cancelId: 1, noLink: true,
      message: 'Perubahan terakhir belum bisa disimpan ke folder proyek.', detail: r && r.err ? 'Penyebab: ' + r.err : '' });
    if (c !== 0) return;
    await bypassUnload();
  }
  mainWin.webContents.reloadIgnoringCache();
}

// menu klik kanan Potong / Salin / Tempel (Electron tidak menyediakannya sendiri)
function editMenu(wc) {
  wc.on('context-menu', (e, p) => {
    const items = [];
    if (p.isEditable) {
      items.push({ label: 'Potong', role: 'cut', enabled: p.editFlags.canCut }, { label: 'Salin', role: 'copy', enabled: p.editFlags.canCopy },
        { label: 'Tempel', role: 'paste', enabled: p.editFlags.canPaste }, { type: 'separator' }, { label: 'Pilih semua', role: 'selectAll' });
    } else if (p.selectionText && p.selectionText.trim()) {
      items.push({ label: 'Salin', role: 'copy' });
    }
    if (items.length) Menu.buildFromTemplate(items).popup({ window: BrowserWindow.fromWebContents(wc) || undefined });
  });
}
app.on('web-contents-created', (e, wc) => { editMenu(wc); lockDown(wc); });
// aplikasi terpasang: tidak ada jalan melihat kode sumber (DevTools, view-source, navigasi ke file lain)
function lockDown(wc) {
  if (DEVTOOLS) return;
  wc.on('before-input-event', (ev, i) => {
    const k = String(i.key || '').toLowerCase(), c = i.control || i.meta;
    if (k === 'f12' || (c && i.shift && ['i', 'j', 'c'].includes(k)) || (c && k === 'u')) ev.preventDefault();
  });
  wc.on('devtools-opened', () => { try { wc.closeDevTools(); } catch (er) {} });
  wc.on('will-navigate', (ev, url) => { if (/^view-source:/i.test(url)) ev.preventDefault(); });
}

// ---------- lisensi: jendela aktivasi / info ----------
let licWin = null, licResolve = null, licMode = 'activate', licBusy = false;
function showLicense(mode) {
  return new Promise((res) => {
    licMode = mode || 'activate';
    if (licWin) { licWin.focus(); const pr = licResolve; licResolve = (v) => { if (pr) pr(v); res(v); }; return; }
    licResolve = res;
    const info = licMode === 'info' && mainWin;
    licWin = new BrowserWindow({ width: 640, height: 660, resizable: false, minimizable: !info, maximizable: false, fullscreenable: false, show: false,
      parent: info ? mainWin : undefined, modal: !!info, title: (info ? 'Lisensi ' : 'Aktivasi ') + APP_NAME, icon: path.join(__dirname, '..', G.icon), backgroundColor: '#e7e4dd',
      webPreferences: { preload: path.join(__dirname, 'activate-preload.js'), contextIsolation: true, nodeIntegration: false, sandbox: true, spellcheck: false, devTools: DEVTOOLS } });
    licWin.setMenu(null);
    licWin.once('ready-to-show', () => licWin.show());
    licWin.loadFile(path.join(__dirname, 'activate.html'));
    licWin.on('closed', () => { licWin = null; const r = licResolve; licResolve = null; if (r) r(LIC.check(G.theme).ok); });
  });
}
ipcMain.handle('lic:state', () => ({ theme: G.theme, appName: APP_NAME, machineId: LIC.machineId(), apps: LIC.apps, check: LIC.check(G.theme), mode: licMode }));
ipcMain.handle('lic:activate', (e, key) => { const r = LIC.activate(key, G.theme); log('[lisensi] aktivasi', r.ok ? 'OK ' + (r.info && r.info.id) : 'gagal: ' + r.reason); return r; });
ipcMain.handle('lic:copy', (e, t) => { clipboard.writeText(String(t || '')); return true; });
ipcMain.handle('lic:openFile', async () => {
  const r = await dialog.showOpenDialog(licWin || mainWin, { title: 'Buka file lisensi GC-Ex', filters: [{ name: 'Lisensi GC-Ex', extensions: ['gcexlic', 'txt'] }], properties: ['openFile'] });
  if (r.canceled || !r.filePaths || !r.filePaths.length) return null;
  try { return fs.readFileSync(r.filePaths[0], 'utf8').slice(0, 20000); } catch (e) { return null; }
});
ipcMain.handle('lic:remove', () => {
  const c = dialog.showMessageBoxSync(licWin || mainWin, { type: 'warning', title: 'Lisensi GC-Ex', buttons: ['Hapus lisensi', 'Batal'], defaultId: 1, cancelId: 1, noLink: true,
    message: 'Hapus lisensi dari komputer ini?', detail: 'Semua aplikasi GC-Ex di komputer ini akan meminta kunci lisensi lagi saat dibuka berikutnya.' });
  if (c !== 0) return false;
  LIC.remove(); log('[lisensi] dihapus'); return true;
});
ipcMain.on('lic:done', () => { const r = licResolve; licResolve = null; if (r) r(true); if (licMode === 'info' && licWin) licWin.close(); });
ipcMain.on('lic:close', () => { if (licWin) licWin.close(); });

// ---------- ukuran tampilan: bawaan 85% (layar laptop dengan skala Windows 125-150% terasa sempit), diingat ----------
const ZOOMS = [0.75, 0.8, 0.85, 0.9, 1.0, 1.1, 1.25];
const ZOOM_DEF = 0.85;
const setFile = path.join(app.getPath('userData'), 'settings.json');
function readSet() { try { return JSON.parse(fs.readFileSync(setFile, 'utf8')); } catch (e) { return {}; } }
function writeSet(o) { try { fs.writeFileSync(setFile, JSON.stringify(Object.assign(readSet(), o), null, 1)); } catch (e) {} }
function zoomNow() { const z = +readSet().zoom; return z >= 0.5 && z <= 2 ? z : ZOOM_DEF; }
function setZoom(z) {
  z = Math.max(0.6, Math.min(1.6, Math.round(z * 100) / 100));
  writeSet({ zoom: z });
  if (mainWin) mainWin.webContents.setZoomFactor(z);
  buildMenu();
}
function stepZoom(d) { const L = ZOOMS, z = zoomNow(); let i = L.findIndex(v => Math.abs(v - z) < 0.001); if (i < 0) i = L.findIndex(v => v > z) - (d > 0 ? 1 : 0); setZoom(L[Math.max(0, Math.min(L.length - 1, i + d))]); }

function buildMenu() {
  const tpl = [
    { label: 'File', submenu: [
      { label: 'Muat ulang GC-Ex', accelerator: 'F5', click: () => reloadSafe() },
      { type: 'separator' },
      { label: 'Keluar', role: 'quit' }
    ] },
    { label: 'Tampilan', submenu: [
      { label: 'Ukuran tampilan', submenu: ZOOMS.map(z => ({ label: Math.round(z * 100) + '%' + (z === ZOOM_DEF ? ' (bawaan)' : ''), type: 'radio', checked: Math.abs(z - zoomNow()) < 0.001, click: () => setZoom(z) })) },
      { label: 'Perbesar', accelerator: 'CmdOrCtrl+=', click: () => stepZoom(+1) },
      { label: 'Perbesar', accelerator: 'CmdOrCtrl+Plus', visible: false, click: () => stepZoom(+1) },
      { label: 'Perkecil', accelerator: 'CmdOrCtrl+-', click: () => stepZoom(-1) },
      { label: 'Ukuran bawaan (' + Math.round(ZOOM_DEF * 100) + '%)', accelerator: 'CmdOrCtrl+0', click: () => setZoom(ZOOM_DEF) },
      { type: 'separator' }, { label: 'Layar penuh', accelerator: 'F11', type: 'checkbox', checked: !!(mainWin && mainWin.isFullScreen()), click: () => { if (mainWin) mainWin.setFullScreen(!mainWin.isFullScreen()); } }
    ] },
    { label: 'Bantuan', submenu: [
      { label: 'Buka folder log', click: () => shell.openPath(logDir) },
      { label: 'Panduan AI lokal (Ollama)', visible: G.theme === 'core', click: () => { const f = path.join(legalDir(), '..', 'docs', 'PANDUAN_CORE.html'); shell.openPath(fs.existsSync(f) ? f : legalDir()); } },
      { label: 'Hapus cache block model besar', visible: G.theme !== 'core', click: async () => {
          const r = await dialog.showMessageBox(mainWin, { type: 'question', buttons: ['Hapus', 'Batal'], defaultId: 1, title: 'Cache block model',
            message: 'Hapus cache block model .mdl besar?', detail: 'Cache dibuat ulang otomatis saat model dibuka lagi (pembacaan pertama lebih lama). Folder: ' + path.join(app.getPath('userData'), 'cache') });
          if (r.response !== 0) return;
          try { const res = await fetch(backend.url + '/mdl/cache/clear', { method: 'POST' }); const j = await res.json(); dialog.showMessageBox(mainWin, { type: 'info', message: (j.removed || 0) + ' cache dihapus.' }); }
          catch (e) { dialog.showMessageBox(mainWin, { type: 'error', message: 'Gagal menghapus cache: ' + e.message }); }
        } },
      { type: 'separator' },
      { label: 'Syarat penggunaan & penafian', click: () => openLegal('SYARAT_PENGGUNAAN.txt') },
      { label: 'Lisensi pihak ketiga (open source) & merek dagang', click: () => openLegal() },
      { label: 'Lisensi GC-Ex…', visible: LIC_ON, click: () => showLicense('info') },
      { label: 'Tentang GC-Ex', click: async () => {
          const c = LIC_ON ? LIC.check(G.theme) : null, I = c && c.info;
          const r = await dialog.showMessageBox(mainWin, { type: 'info', title: 'Tentang GC-Ex', buttons: ['OK', 'Lisensi open source & merek', 'Syarat penggunaan'], defaultId: 0, noLink: true, message: APP_NAME + ' - Grade Control Excellence',
            detail: 'Versi ' + app.getVersion() + '\nCopyright © 2026 Habil Abdillah. Hak cipta dilindungi undang-undang.' +
              (I && c.ok ? '\n\nDilisensikan kepada: ' + I.n + (I.o ? ' (' + I.o + ')' : '') + '\nBerlaku sampai: ' + (I.e || 'tanpa batas waktu') : '') +
              '\n\nMemakai komponen open source: ' + (G.theme === 'core' ? '' : 'Plotly.js (MIT), ') + 'Electron / Chromium (MIT, BSD), Python (PSF), FastAPI, Uvicorn, Pydantic, NumPy, Pillow (MIT-CMU), lxml, openpyxl, pyodbc (MIT / BSD)' + (G.theme === 'core' ? ', font Playfair Display & Courier Prime (SIL OFL 1.1).\nAI lokal memakai Ollama (MIT, dipasang terpisah); model AI mengikuti lisensi masing-masing.' : '.') +
              '\nLeapfrog, Surpac, GEOVIA, Micromine, AutoCAD, Microsoft Excel / Access, Ollama dan nama produk lain adalah merek dagang milik pemiliknya; GC-Ex tidak berafiliasi dengan mereka.' });
          if (r.response === 1) openLegal();
          if (r.response === 2) openLegal('SYARAT_PENGGUNAAN.txt');
        } }
    ] }
  ];
  Menu.setApplicationMenu(Menu.buildFromTemplate(tpl));
}

// izin folder proyek (File System Access API) diberikan otomatis: tidak ada bilah "Izinkan" berulang
function grantFilePermissions() {
  const ses = session.defaultSession;
  ses.setPermissionRequestHandler((wc, perm, cb) => cb(['fileSystem', 'clipboard-read', 'clipboard-sanitized-write', 'media', 'display-capture'].includes(perm)));
  ses.setPermissionCheckHandler((wc, perm) => ['fileSystem', 'clipboard-read', 'clipboard-sanitized-write'].includes(perm));
  // folder yang dilindungi Chromium (mis. langsung folder profil pengguna, Program Files): tanya, jangan tolak diam-diam
  ses.on('file-system-access-restricted', async (e, details, callback) => {
    const r = await dialog.showMessageBox(mainWin, {
      type: 'warning', buttons: ['Pilih folder lain', 'Tetap pakai folder ini', 'Batal'], defaultId: 0, cancelId: 2, title: 'Folder proyek',
      message: 'Folder ini termasuk folder sistem / folder induk yang dilindungi.',
      detail: (details && details.path ? details.path + '\n\n' : '') + 'Sebaiknya buat subfolder khusus proyek, mis. Documents\\GC-Ex\\Proyek_A.'
    });
    callback(r.response === 0 ? 'tryAgain' : r.response === 1 ? 'allow' : 'deny');
  });
}

app.whenReady().then(async () => {
  log('=== GC-Ex', app.getVersion(), 'mulai ===');
  regSelf();
  protocol.handle('gcexfile', async (req) => {
    const t = new URL(req.url).pathname.replace(/^\/+/, ''), p = PRJ.open[t];
    if (!p || !fs.existsSync(p)) return new Response('tidak ditemukan', { status: 404 });
    const r = await enet.fetch(pathToFileURL(p).toString());
    return new Response(r.body, { status: 200, headers: { 'content-type': 'application/octet-stream', 'access-control-allow-origin': '*' } });
  });
  // dibuka dengan klik dua kali .prj milik aplikasi GC-Ex lain: teruskan & selesai tanpa membuka jendela
  const f0 = argPrj(process.argv);
  let f0done = false;
  if (f0) {
    const own = prjOwner(f0);
    if (!own) { log('[prj] bukan proyek GC-Ex, dibuka di Notepad:', f0); try { spawn('notepad.exe', [f0], { detached: true, stdio: 'ignore' }).unref(); } catch (e) {} app.quit(); return; }
    if (own !== APP_NAME) { if (routePrj(f0) === 'other') { app.quit(); return; } f0done = true; }
  }
  // syarat penggunaan dulu, baru aktivasi lisensi
  if (!ensureTerms()) { app.quit(); return; }
  if (LIC_ON) {
    const c = LIC.check(G.theme);
    if (!c.ok) {
      licBusy = true;
      log('[lisensi] belum aktif:', c.reason);
      const ok = await showLicense('activate');
      if (!ok) { licBusy = false; log('[lisensi] aplikasi ditutup tanpa lisensi'); app.quit(); return; }
    } else if (c.daysLeft != null && c.daysLeft <= 14) {
      setTimeout(() => { if (mainWin) dialog.showMessageBox(mainWin, { type: 'warning', title: 'Lisensi GC-Ex', message: 'Lisensi GC-Ex berakhir dalam ' + c.daysLeft + ' hari (' + c.info.e + ').', detail: 'Minta kunci perpanjangan ke penerbit GC-Ex, lalu masukkan lewat Bantuan > Lisensi GC-Ex.' }); }, 4000);
    }
  }
  grantFilePermissions();
  buildMenu();
  createWindow();
  if (licWin) { const w = licWin; setTimeout(() => { try { if (!w.isDestroyed()) w.close(); } catch (e) {} licBusy = false; }, 600); } else licBusy = false;
  if (f0 && !f0done) routePrj(f0);
  startBackend().then(() => { if (mainWin) mainWin.webContents.send('gcex:backend', { ok: backend.ok, url: backend.url, err: backend.err }); });
});
app.on('window-all-closed', () => { if (licBusy) return; stopBackend(); app.quit(); });
app.on('will-quit', stopBackend);
