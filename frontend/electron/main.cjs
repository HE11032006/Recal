const { app, BrowserWindow, shell, Notification, Tray, Menu, nativeImage } = require("electron");
const path = require("path");

const isDev = !!process.env.VITE_DEV_SERVER_URL;

let splash = null;
let mainWindow = null;
let tray = null;
let isQuiting = false;

app.on("before-quit", () => {
  isQuiting = true;
});

function createSplash() {
  splash = new BrowserWindow({
    width: 480,
    height: 320,
    frame: false,
    resizable: false,
    transparent: true,
    backgroundColor: "#00000000",
    center: true,
    show: true,
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
    },
  });
  splash.loadFile(path.join(__dirname, "splash.html"));
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1440,
    height: 900,
    minWidth: 1024,
    minHeight: 700,
    backgroundColor: "#111317",
    titleBarStyle: "hidden",
    titleBarOverlay: {
      color: "#111317",
      symbolColor: "#e2e2e6",
      height: 36,
    },
    autoHideMenuBar: true,
    show: false,
    webPreferences: {
      preload: path.join(__dirname, "preload.cjs"),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
    },
  });

  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url);
    return { action: "deny" };
  });

  // Fermer la fenêtre = réduction dans le tray, l'app continue de veiller.
  mainWindow.on("close", (event) => {
    if (!isQuiting) {
      event.preventDefault();
      mainWindow.hide();
    }
  });

  if (isDev) {
    mainWindow.loadURL(process.env.VITE_DEV_SERVER_URL);
  } else {
    mainWindow.loadFile(path.join(__dirname, "..", "dist", "index.html"));
  }

  mainWindow.once("ready-to-show", () => {
    if (splash) {
      splash.close();
      splash = null;
    }
    mainWindow.show();
  });
}

function createTray() {
  const icon = nativeImage.createFromPath(path.join(__dirname, "tray-icon.png"));
  tray = new Tray(icon);
  tray.setToolTip("Recal — agent de veille actif");
  tray.setContextMenu(
    Menu.buildFromTemplate([
      { label: "Afficher Recal", click: () => mainWindow && mainWindow.show() },
      { type: "separator" },
      {
        label: "Quitter",
        click: () => {
          isQuiting = true;
          app.quit();
        },
      },
    ])
  );
  tray.on("click", () => {
    if (!mainWindow) return;
    if (mainWindow.isVisible()) {
      mainWindow.focus();
    } else {
      mainWindow.show();
    }
  });
}

app.whenReady().then(() => {
  createSplash();
  createWindow();
  createTray();
  app.on("activate", () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on("window-all-closed", () => {
  // Ne jamais quitter : l'agent continue dans le tray.
});

function ipcHandlers() {
  const { ipcMain } = require("electron");
  ipcMain.handle("recal:notify", (_event, { title, body }) => {
    if (Notification.isSupported()) {
      new Notification({ title, body }).show();
      return true;
    }
    return false;
  });
  ipcMain.handle("recal:badge", (_event, { count }) => {
    if (tray) {
      tray.setToolTip(
        count > 0
          ? `Recal — ${count} nouvelle${count > 1 ? "s" : ""} opportunité${count > 1 ? "s" : ""}`
          : "Recal — agent de veille actif"
      );
      return true;
    }
    return false;
  });
}
ipcHandlers();
