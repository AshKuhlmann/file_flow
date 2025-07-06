const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  openDirectoryDialog: () => ipcRenderer.invoke('dialog:openDirectory'),
  getTriageList: (dirPath) => ipcRenderer.invoke('files:getTriageList', dirPath),
  performFileAction: (actionDetails) => ipcRenderer.invoke('files:performAction', actionDetails),
});
