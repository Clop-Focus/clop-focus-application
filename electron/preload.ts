import { contextBridge, ipcRenderer } from 'electron'

// APIs para notificações do sistema via IPC
contextBridge.exposeInMainWorld('electronAPI', {
  // Verificar se notificações são suportadas
  isNotificationSupported: async () => {
    console.log('🔔 preload: isNotificationSupported chamado')
    try {
      const result = await ipcRenderer.invoke('notifications:isSupported')
      console.log('🔔 preload: Suporte via IPC:', result)
      return result
    } catch (error) {
      console.error('🔔 preload: Erro ao verificar suporte:', error)
      return false
    }
  },
  
  // Solicitar permissão para notificações
  requestNotificationPermission: async () => {
    console.log('🔔 preload: requestNotificationPermission chamado')
    try {
      const result = await ipcRenderer.invoke('notifications:requestPermission')
      console.log('🔔 preload: Permissão solicitada via IPC:', result)
      return result
    } catch (error) {
      console.error('🔔 preload: Erro ao solicitar permissão:', error)
      return 'denied'
    }
  },
  
  // Verificar permissão atual
  getNotificationPermission: async () => {
    console.log('🔔 preload: getNotificationPermission chamado')
    try {
      const result = await ipcRenderer.invoke('notifications:getPermission')
      console.log('🔔 preload: Permissão atual via IPC:', result)
      return result
    } catch (error) {
      console.error('🔔 preload: Erro ao verificar permissão:', error)
      return 'denied'
    }
  },
  
  // Enviar notificação do sistema
  sendSystemNotification: async (title: string, options?: NotificationOptions) => {
    try {
      const result = await ipcRenderer.invoke('notifications:send', title, options)
      console.log('🔔 preload: Notificação enviada via IPC:', result)
      return result
    } catch (error) {
      console.error('🔔 preload: Erro ao enviar notificação:', error)
      return null
    }
  },
  
  // Notificação específica para perda de foco
  notifyFocusLoss: async (level: string) => {
    console.log('🔔 preload: notifyFocusLoss chamado com nível:', level)
    try {
      const result = await ipcRenderer.invoke('notifications:notifyFocusLoss', level)
      console.log('🔔 preload: Notificação de perda de foco via IPC:', result)
      return result
    } catch (error) {
      console.error('🔔 preload: Erro ao notificar perda de foco:', error)
      return null
    }
  }
})

// API para overlay transparente sempre-no-topo
contextBridge.exposeInMainWorld('overlay', {
  flash: async (ms = 600) => {
    console.log('🔴 preload: overlay.flash chamado com duração:', ms)
    try {
      const result = await ipcRenderer.invoke('overlay:flash', ms)
      console.log('🔴 preload: Flash do overlay via IPC:', result)
      return result
    } catch (error) {
      console.error('🔴 preload: Erro ao fazer flash do overlay:', error)
      return false
    }
  },
  
  show: async () => {
    console.log('🔴 preload: overlay.show chamado')
    try {
      const result = await ipcRenderer.invoke('overlay:show')
      console.log('🔴 preload: Show do overlay via IPC:', result)
      return result
    } catch (error) {
      console.error('🔴 preload: Erro ao mostrar overlay:', error)
      return false
    }
  },
  
  hide: async () => {
    console.log('🔴 preload: overlay.hide chamado')
    try {
      const result = await ipcRenderer.invoke('overlay:hide')
      console.log('🔴 preload: Hide do overlay via IPC:', result)
      return result
    } catch (error) {
      console.error('🔴 preload: Erro ao esconder overlay:', error)
      return false
    }
  }
})

// Manter isolado; o renderer usa getUserMedia normalmente
export {}
