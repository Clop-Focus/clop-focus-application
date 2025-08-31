var __defProp = Object.defineProperty;
var __getOwnPropDesc = Object.getOwnPropertyDescriptor;
var __getOwnPropNames = Object.getOwnPropertyNames;
var __hasOwnProp = Object.prototype.hasOwnProperty;
var __copyProps = (to, from, except, desc) => {
  if (from && typeof from === "object" || typeof from === "function") {
    for (let key of __getOwnPropNames(from))
      if (!__hasOwnProp.call(to, key) && key !== except)
        __defProp(to, key, { get: () => from[key], enumerable: !(desc = __getOwnPropDesc(from, key)) || desc.enumerable });
  }
  return to;
};
var __toCommonJS = (mod) => __copyProps(__defProp({}, "__esModule", { value: true }), mod);

// electron/preload.ts
var preload_exports = {};
module.exports = __toCommonJS(preload_exports);
var import_electron = require("electron");
import_electron.contextBridge.exposeInMainWorld("electronAPI", {
  // Verificar se notificações são suportadas
  isNotificationSupported: async () => {
    console.log("\u{1F514} preload: isNotificationSupported chamado");
    try {
      const result = await import_electron.ipcRenderer.invoke("notifications:isSupported");
      console.log("\u{1F514} preload: Suporte via IPC:", result);
      return result;
    } catch (error) {
      console.error("\u{1F514} preload: Erro ao verificar suporte:", error);
      return false;
    }
  },
  // Solicitar permissão para notificações
  requestNotificationPermission: async () => {
    console.log("\u{1F514} preload: requestNotificationPermission chamado");
    try {
      const result = await import_electron.ipcRenderer.invoke("notifications:requestPermission");
      console.log("\u{1F514} preload: Permiss\xE3o solicitada via IPC:", result);
      return result;
    } catch (error) {
      console.error("\u{1F514} preload: Erro ao solicitar permiss\xE3o:", error);
      return "denied";
    }
  },
  // Verificar permissão atual
  getNotificationPermission: async () => {
    console.log("\u{1F514} preload: getNotificationPermission chamado");
    try {
      const result = await import_electron.ipcRenderer.invoke("notifications:getPermission");
      console.log("\u{1F514} preload: Permiss\xE3o atual via IPC:", result);
      return result;
    } catch (error) {
      console.error("\u{1F514} preload: Erro ao verificar permiss\xE3o:", error);
      return "denied";
    }
  },
  // Enviar notificação do sistema
  sendSystemNotification: async (title, options) => {
    try {
      const result = await import_electron.ipcRenderer.invoke("notifications:send", title, options);
      console.log("\u{1F514} preload: Notifica\xE7\xE3o enviada via IPC:", result);
      return result;
    } catch (error) {
      console.error("\u{1F514} preload: Erro ao enviar notifica\xE7\xE3o:", error);
      return null;
    }
  },
  // Notificação específica para perda de foco
  notifyFocusLoss: async (level) => {
    console.log("\u{1F514} preload: notifyFocusLoss chamado com n\xEDvel:", level);
    try {
      const result = await import_electron.ipcRenderer.invoke("notifications:notifyFocusLoss", level);
      console.log("\u{1F514} preload: Notifica\xE7\xE3o de perda de foco via IPC:", result);
      return result;
    } catch (error) {
      console.error("\u{1F514} preload: Erro ao notificar perda de foco:", error);
      return null;
    }
  }
});
import_electron.contextBridge.exposeInMainWorld("overlay", {
  flash: async (ms = 600) => {
    console.log("\u{1F534} preload: overlay.flash chamado com dura\xE7\xE3o:", ms);
    try {
      const result = await import_electron.ipcRenderer.invoke("overlay:flash", ms);
      console.log("\u{1F534} preload: Flash do overlay via IPC:", result);
      return result;
    } catch (error) {
      console.error("\u{1F534} preload: Erro ao fazer flash do overlay:", error);
      return false;
    }
  },
  show: async () => {
    console.log("\u{1F534} preload: overlay.show chamado");
    try {
      const result = await import_electron.ipcRenderer.invoke("overlay:show");
      console.log("\u{1F534} preload: Show do overlay via IPC:", result);
      return result;
    } catch (error) {
      console.error("\u{1F534} preload: Erro ao mostrar overlay:", error);
      return false;
    }
  },
  hide: async () => {
    console.log("\u{1F534} preload: overlay.hide chamado");
    try {
      const result = await import_electron.ipcRenderer.invoke("overlay:hide");
      console.log("\u{1F534} preload: Hide do overlay via IPC:", result);
      return result;
    } catch (error) {
      console.error("\u{1F534} preload: Erro ao esconder overlay:", error);
      return false;
    }
  }
});
