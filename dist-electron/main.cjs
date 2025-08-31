var __create = Object.create;
var __defProp = Object.defineProperty;
var __getOwnPropDesc = Object.getOwnPropertyDescriptor;
var __getOwnPropNames = Object.getOwnPropertyNames;
var __getProtoOf = Object.getPrototypeOf;
var __hasOwnProp = Object.prototype.hasOwnProperty;
var __commonJS = (cb, mod) => function __require() {
  return mod || (0, cb[__getOwnPropNames(cb)[0]])((mod = { exports: {} }).exports, mod), mod.exports;
};
var __copyProps = (to, from, except, desc) => {
  if (from && typeof from === "object" || typeof from === "function") {
    for (let key of __getOwnPropNames(from))
      if (!__hasOwnProp.call(to, key) && key !== except)
        __defProp(to, key, { get: () => from[key], enumerable: !(desc = __getOwnPropDesc(from, key)) || desc.enumerable });
  }
  return to;
};
var __toESM = (mod, isNodeMode, target) => (target = mod != null ? __create(__getProtoOf(mod)) : {}, __copyProps(
  // If the importer is in node compatibility mode or this is not an ESM
  // file that has been converted to a CommonJS file using a Babel-
  // compatible transform (i.e. "__esModule" has not been set), then set
  // "default" to the CommonJS "module.exports" for node compatibility.
  isNodeMode || !mod || !mod.__esModule ? __defProp(target, "default", { value: mod, enumerable: true }) : target,
  mod
));

// electron/overlay.cjs
var require_overlay = __commonJS({
  "electron/overlay.cjs"(exports2, module2) {
    var { BrowserWindow: BrowserWindow2, screen } = require("electron");
    var { join: join2 } = require("path");
    var overlayWins = [];
    function createOverlays2() {
      console.log("\u{1F534} overlay: createOverlays chamado");
      destroyOverlays();
      const displays = screen.getAllDisplays();
      console.log(`\u{1F534} overlay: ${displays.length} displays encontrados`);
      for (const display of displays) {
        const { x, y, width, height } = display.bounds;
        console.log(`\u{1F534} overlay: criando janela para display ${width}x${height} em (${x},${y})`);
        const win2 = new BrowserWindow2({
          x,
          y,
          width,
          height,
          frame: false,
          transparent: true,
          resizable: false,
          movable: false,
          focusable: false,
          skipTaskbar: true,
          fullscreenable: false,
          hasShadow: false,
          alwaysOnTop: true,
          // Usar tipo compatível com macOS
          type: "toolbar",
          webPreferences: { contextIsolation: true, nodeIntegration: false }
        });
        win2.setIgnoreMouseEvents(true, { forward: true });
        win2.setAlwaysOnTop(true, "screen-saver");
        win2.setVisibleOnAllWorkspaces(true, { visibleOnFullScreen: true });
        win2.loadFile(join2(__dirname, "overlay.html"));
        win2.hide();
        overlayWins.push(win2);
        console.log(`\u{1F534} overlay: janela criada e adicionada ao array (total: ${overlayWins.length})`);
      }
      screen.on("display-added", recreateOverlays);
      screen.on("display-removed", recreateOverlays);
      screen.on("display-metrics-changed", recreateOverlays);
    }
    function recreateOverlays() {
      destroyOverlays();
      createOverlays2();
    }
    function destroyOverlays() {
      overlayWins.forEach((w) => {
        try {
          w.close();
        } catch {
        }
      });
      overlayWins = [];
    }
    function flashOverlay2(durationMs = 600) {
      console.log(`\u{1F534} overlay: flashOverlay chamado com ${overlayWins.length} janelas`);
      if (overlayWins.length === 0) {
        console.log("\u{1F534} overlay: ERRO - nenhuma janela de overlay criada!");
        return;
      }
      overlayWins.forEach((w, i) => {
        try {
          console.log(`\u{1F534} overlay: mostrando janela ${i}`);
          w.showInactive();
        } catch (error) {
          console.error(`\u{1F534} overlay: erro ao mostrar janela ${i}:`, error);
        }
      });
      setTimeout(() => {
        console.log(`\u{1F534} overlay: escondendo overlays ap\xF3s ${durationMs}ms`);
        overlayWins.forEach((w, i) => {
          try {
            w.hide();
          } catch (error) {
            console.error(`\u{1F534} overlay: erro ao esconder janela ${i}:`, error);
          }
        });
      }, durationMs);
    }
    function showOverlay2() {
      overlayWins.forEach((w) => w.showInactive());
    }
    function hideOverlay2() {
      overlayWins.forEach((w) => w.hide());
    }
    module2.exports = {
      createOverlays: createOverlays2,
      destroyOverlays,
      flashOverlay: flashOverlay2,
      showOverlay: showOverlay2,
      hideOverlay: hideOverlay2
    };
  }
});

// electron/main.ts
var import_electron = require("electron");
var import_path = require("path");
var import_electron2 = require("electron");
var import_overlay = __toESM(require_overlay(), 1);
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
import_electron.app.whenReady().then(async () => {
  (0, import_overlay.createOverlays)();
  await createWindow();
  if (win) {
    win.webContents.executeJavaScript(`
      window.flashFocusAlert = () => {
        console.log('\u{1F534} Testando overlay de foco...');
        return true;
      };
    `);
  }
});
import_electron.app.on("window-all-closed", () => {
  if (process.platform !== "darwin") import_electron.app.quit();
});
import_electron.app.on("activate", () => {
  if (import_electron.BrowserWindow.getAllWindows().length === 0) createWindow();
});
import_electron2.ipcMain.handle("notifications:isSupported", () => {
  console.log("\u{1F514} main: notifications:isSupported - sempre retorna true");
  return true;
});
import_electron2.ipcMain.handle("notifications:getPermission", () => {
  console.log("\u{1F514} main: getPermission - sempre retorna granted");
  return "granted";
});
import_electron2.ipcMain.handle("notifications:requestPermission", async () => {
  console.log("\u{1F514} main: requestPermission - sempre retorna granted");
  return "granted";
});
import_electron2.ipcMain.handle("notifications:send", async (event, title, options) => {
  console.log("\u{1F514} main: send - criando notifica\xE7\xE3o:", title);
  try {
    const notification = new (require("electron")).Notification({
      title,
      body: options?.body || "",
      icon: options?.icon || (0, import_path.join)(__dirname, "../public/favicon.ico"),
      silent: options?.silent || false
    });
    notification.on("click", () => {
      console.log("\u{1F514} main: notifica\xE7\xE3o clicada, focando janela");
      if (win) {
        win.focus();
      }
    });
    notification.show();
    console.log("\u{1F514} main: notifica\xE7\xE3o criada e exibida com sucesso");
    return { success: true, id: options?.tag || "default" };
  } catch (error) {
    console.error("\u{1F514} main: erro ao criar notifica\xE7\xE3o:", error);
    return { success: false, error: error.message };
  }
});
import_electron2.ipcMain.handle("overlay:flash", async (_e, ms = 600) => {
  console.log("\u{1F534} main: overlay:flash - dura\xE7\xE3o:", ms);
  try {
    (0, import_overlay.flashOverlay)(ms);
    return true;
  } catch (error) {
    console.error("\u{1F534} main: erro ao fazer flash do overlay:", error);
    return false;
  }
});
import_electron2.ipcMain.handle("overlay:show", async () => {
  console.log("\u{1F534} main: overlay:show");
  try {
    (0, import_overlay.showOverlay)();
    return true;
  } catch (error) {
    console.error("\u{1F534} main: erro ao mostrar overlay:", error);
    return false;
  }
});
import_electron2.ipcMain.handle("overlay:hide", async () => {
  console.log("\u{1F534} main: overlay:hide");
  try {
    (0, import_overlay.hideOverlay)();
    return true;
  } catch (error) {
    console.error("\u{1F534} main: erro ao esconder overlay:", error);
    return false;
  }
});
import_electron2.ipcMain.handle("notifications:notifyFocusLoss", async (event, level) => {
  console.log("\u{1F514} main: notifyFocusLoss - n\xEDvel:", level);
  try {
    const title = "\u{1F6A8} Perda de Foco Detectada!";
    const body = `Voc\xEA perdeu o foco na sess\xE3o ${level}. Volte para a tela do ClopFocus!`;
    const notification = new (require("electron")).Notification({
      title,
      body,
      icon: (0, import_path.join)(__dirname, "../public/favicon.ico"),
      silent: false
    });
    notification.on("click", () => {
      console.log("\u{1F514} main: notifica\xE7\xE3o de perda de foco clicada, focando janela");
      if (win) {
        win.focus();
      }
    });
    notification.show();
    console.log("\u{1F514} main: notifica\xE7\xE3o de perda de foco criada e exibida com sucesso");
    return { success: true, id: "focus-loss" };
  } catch (error) {
    console.error("\u{1F514} main: erro ao criar notifica\xE7\xE3o de perda de foco:", error);
    return { success: false, error: error.message };
  }
});
var isFocusModeEnabled = false;
import_electron2.ipcMain.handle("focusMode:toggle", async () => {
  console.log("\u{1F512} main: focusMode:toggle - estado atual:", isFocusModeEnabled);
  try {
    isFocusModeEnabled = !isFocusModeEnabled;
    if (isFocusModeEnabled) {
      console.log("\u{1F512} main: Modo foco ATIVADO - bloqueando notifica\xE7\xF5es externas");
    } else {
      console.log("\u{1F512} main: Modo foco DESATIVADO - permitindo notifica\xE7\xF5es externas");
    }
    return isFocusModeEnabled;
  } catch (error) {
    console.error("\u{1F512} main: erro ao alternar modo foco:", error);
    return false;
  }
});
import_electron2.ipcMain.handle("focusMode:getStatus", async () => {
  console.log("\u{1F512} main: focusMode:getStatus - retornando:", isFocusModeEnabled);
  return isFocusModeEnabled;
});
