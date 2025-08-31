/// <reference types="vite/client" />

// APIs do Electron expostas via preload
interface ElectronAPI {
  isNotificationSupported: () => Promise<boolean>
  requestNotificationPermission: () => Promise<NotificationPermission>
  getNotificationPermission: () => Promise<NotificationPermission>
  sendSystemNotification: (title: string, options?: NotificationOptions) => Promise<any>
  notifyFocusLoss: (level: string) => Promise<any>
}

// API para overlay transparente sempre-no-topo
interface OverlayAPI {
  flash: (ms?: number) => Promise<boolean>
  show: () => Promise<boolean>
  hide: () => Promise<boolean>
}

declare global {
  interface Window {
    electronAPI: ElectronAPI
    overlay: OverlayAPI
    process?: {
      versions: {
        electron: string
      }
    }
  }
}

export {}
