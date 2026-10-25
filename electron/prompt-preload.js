// Jembatan kecil untuk jendela isian (pengganti prompt() yang tidak tersedia di Electron)
'use strict';
const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('gcexPrompt', {
  done: (id, value) => ipcRenderer.send('gcex:prompt-result:' + id, value === null ? null : String(value)),
  size: (h) => ipcRenderer.send('gcex:prompt-size', h)
});
