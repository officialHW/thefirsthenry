// Henry on top of your whole desktop.
// One see-through, always-on-top window covers the screen (above the Dock / taskbar). Clicks pass
// straight through it to whatever is underneath, except on Henry himself and his chat box.
// It shows the same page as the normal window, from Henry's helper program on this computer.
//
//   Ctrl+Shift+H (Cmd+Shift+H on a Mac)   open the chat box to type to him
//   Quit: the Henry icon in the Dock / taskbar, or close the Terminal window that started him.
const { app, BrowserWindow, ipcMain, globalShortcut, screen, session } = require("electron");
const path = require("path");

const arg = process.argv.find((a) => a.startsWith("--url="));
const URL_ = new URL(arg ? arg.slice(6) : "http://127.0.0.1:4750/");
URL_.searchParams.set("overlay", "1");
if (!["127.0.0.1", "localhost"].includes(URL_.hostname)) throw new Error("Henry's overlay only opens this computer's helper.");

let win = null;
if (!app.requestSingleInstanceLock()) app.quit();          // only one Henry on the screen

function fit() {
  if (!win) return;
  win.setBounds(screen.getPrimaryDisplay().workArea);       // the screen minus the menu bar and Dock
}

function create() {
  win = new BrowserWindow({
    ...screen.getPrimaryDisplay().workArea,
    transparent: true, backgroundColor: "#00000000", frame: false, hasShadow: false,
    resizable: false, movable: false, minimizable: false, maximizable: false, fullscreenable: false,
    skipTaskbar: true, alwaysOnTop: true, title: "Henry",
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
      contextIsolation: true, sandbox: true, nodeIntegration: false,
      backgroundThrottling: false, spellcheck: false,
    },
  });
  win.setAlwaysOnTop(true, "floating");
  win.setVisibleOnAllWorkspaces(true, { visibleOnFullScreen: true });
  win.setIgnoreMouseEvents(true, { forward: true });       // see-through for clicks until you reach Henry

  // stay on Henry's own page: no other sites, no pop-up windows
  win.webContents.on("will-navigate", (e, url) => { if (new URL(url).origin !== URL_.origin) e.preventDefault(); });
  win.webContents.setWindowOpenHandler(() => ({ action: "deny" }));
  // the helper program may still be starting: try again shortly
  win.webContents.on("did-fail-load", () => setTimeout(() => win && win.loadURL(URL_.href), 1500));
  win.loadURL(URL_.href);
  win.on("closed", () => { win = null; });
}

// the page says when the pointer is over Henry or his chat box (true) or empty space (false)
ipcMain.on("henry:interactive", (e, on) => {
  if (!win || e.sender !== win.webContents) return;
  if (on) win.setIgnoreMouseEvents(false);
  else win.setIgnoreMouseEvents(true, { forward: true });
});

app.whenReady().then(() => {
  // the overlay needs no camera, microphone, location or notifications
  session.defaultSession.setPermissionRequestHandler((wc, perm, cb) => cb(false));
  create();
  screen.on("display-metrics-changed", fit);
  screen.on("display-added", fit);
  screen.on("display-removed", fit);
  globalShortcut.register("CommandOrControl+Shift+H", () => {
    if (!win) return;
    win.setIgnoreMouseEvents(false); win.focus();
    win.webContents.send("henry:focus-chat");
  });
});
app.on("second-instance", () => win && win.webContents.send("henry:focus-chat"));
app.on("will-quit", () => globalShortcut.unregisterAll());
app.on("window-all-closed", () => app.quit());
