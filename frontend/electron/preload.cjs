const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("recal", {
  notify: (title, body) => ipcRenderer.invoke("recal:notify", { title, body }),
  setBadge: (count) => ipcRenderer.invoke("recal:badge", { count }),
  setTheme: (theme) => ipcRenderer.invoke("recal:theme", { theme }),
  isDesktop: true,
});
