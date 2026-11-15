// The only things the page can ask the overlay window to do. Nothing else from the
// computer is reachable from the page.
const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("henryOverlay", {
  setInteractive: (on) => ipcRenderer.send("henry:interactive", !!on),
  onFocusChat: (cb) => ipcRenderer.on("henry:focus-chat", () => cb()),
  cross: (side) => ipcRenderer.send("henry:cross", side > 0 ? 1 : -1),          // he walked off that side
  onExits: (cb) => ipcRenderer.on("henry:exits", (e, x) => cb(!!x.left, !!x.right)),
  onArrived: (cb) => ipcRenderer.on("henry:arrived", (e, side) => cb(side > 0 ? 1 : -1)),
});
