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

const APP_ICON = path.join(__dirname, "app-icon.png");

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
    icon: nativeImage.createFromPath(APP_ICON),
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
    backgroundColor: "#f6f6f6",
    icon: nativeImage.createFromPath(APP_ICON),
    titleBarStyle: "hidden",
    titleBarOverlay: {
      color: "#f6f6f6",
      symbolColor: "#141414",
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
  try {
    const icon = nativeImage.createFromPath(APP_ICON);
    tray = new Tray(icon.resize({ width: 16, height: 16 }));
  tray.setToolTip("Recal agent de veille actif");
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
  } catch (err) {
    // Linux sans indicateur système : pas de tray, l'icône reste en barre des tâches.
    console.warn("Tray indisponible :", err && err.message ? err.message : err);
    tray = null;
  }
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
  // Fenêtre fermée mais tray actif : l'agent continue en arrière-plan.
  // Sans tray (Linux sans indicateur) ni macOS : quitter proprement.
  if (process.platform === "darwin") return;
  if (!tray) app.quit();
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
  ipcMain.handle("recal:theme", (_event, { theme }) => {
    // Synchronise les contrôles natifs (titlebar overlay) avec le thème web.
    if (mainWindow && (theme === "light" || theme === "dark")) {
      const overlay = theme === "dark"
        ? { color: "#111317", symbolColor: "#e2e2e6", height: 36 }
        : { color: "#f6f6f6", symbolColor: "#141414", height: 36 };
      try {
        mainWindow.setTitleBarOverlay(overlay);
        return true;
      } catch {
        return false;
      }
    }
    return false;
  });
}
ipcHandlers();
