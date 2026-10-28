// jembatan aman halaman aktivasi <-> proses utama (tanpa akses Node di halaman)
'use strict';
const { contextBridge, ipcRenderer } = require('electron');
contextBridge.exposeInMainWorld('gcexLic', {
  state: () => ipcRenderer.invoke('lic:state'),
  activate: (key) => ipcRenderer.invoke('lic:activate', String(key || '')),
  openFile: () => ipcRenderer.invoke('lic:openFile'),
  copy: (t) => ipcRenderer.invoke('lic:copy', String(t || '')),
  remove: () => ipcRenderer.invoke('lic:remove'),
  done: () => ipcRenderer.send('lic:done'),
  close: () => ipcRenderer.send('lic:close')
});
