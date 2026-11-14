// The only two things the page can ask the overlay window to do. Nothing else from the
// computer is reachable from the page.
const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("henryOverlay", {
  setInteractive: (on) => ipcRenderer.send("henry:interactive", !!on),
  onFocusChat: (cb) => ipcRenderer.on("henry:focus-chat", () => cb()),
});
