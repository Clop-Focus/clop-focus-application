// electron/main.ts
var import_electron = require("electron");
var import_path = require("path");
var DEV_URL = process.env.VITE_DEV_SERVER_URL ?? "http://localhost:5173";
var win = null;
async function createWindow() {
  win = new import_electron.BrowserWindow({
    width: 1280,
    height: 800,
    backgroundColor: "#0b0b0c",
    webPreferences: {
      preload: (0, import_path.join)(__dirname, "preload.cjs"),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: false
    }
  });
  const allowedOrigins = /* @__PURE__ */ new Set(["file://", new URL(DEV_URL).origin]);
  import_electron.session.defaultSession.setPermissionRequestHandler((wc, permission, callback, details) => {
    if (permission === "media") {
      const origin = details.requestingUrl ? new URL(details.requestingUrl).origin : "file://";
      callback(allowedOrigins.has(origin));
    } else {
      callback(false);
    }
  });
  try {
    await win.loadURL(`${DEV_URL}/`);
    win.webContents.openDevTools({ mode: "detach" });
    console.log("Carregando servidor de desenvolvimento:", `${DEV_URL}/`);
  } catch (error) {
    console.error("Erro ao carregar servidor de desenvolvimento:", error);
    try {
      await win.loadFile((0, import_path.join)(__dirname, "../dist/index.html"));
      console.log("Carregando arquivo local como fallback");
    } catch (fallbackError) {
      console.error("Erro ao carregar arquivo local:", fallbackError);
      win.loadURL("data:text/html,<h1>Erro ao carregar aplica\xE7\xE3o</h1><p>Verifique se o servidor Vite est\xE1 rodando em " + DEV_URL + "</p>");
    }
  }
  win.webContents.on("did-fail-load", (_e, code, desc, url) => {
    console.error("did-fail-load", code, desc, url);
  });
  win.webContents.on("did-finish-load", () => {
    console.log("Renderer carregado.");
  });
  win.on("closed", () => win = null);
}
import_electron.app.whenReady().then(createWindow);
import_electron.app.on("window-all-closed", () => {
  if (process.platform !== "darwin") import_electron.app.quit();
});
import_electron.app.on("activate", () => {
  if (import_electron.BrowserWindow.getAllWindows().length === 0) createWindow();
});
