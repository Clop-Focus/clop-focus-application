import { app, BrowserWindow, session } from 'electron'
import { join } from 'path'
import { ipcMain } from 'electron'
import { createOverlays, flashOverlay, showOverlay, hideOverlay } from './overlay.cjs'

const DEV_URL = process.env.VITE_DEV_SERVER_URL ?? 'http://localhost:5173'

let win: BrowserWindow | null = null

async function createWindow() {
  win = new BrowserWindow({
    width: 1280,
    height: 800,
    backgroundColor: '#0b0b0c',
    webPreferences: {
      preload: join(__dirname, 'preload.cjs'),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: false,
    },
  })

  const allowedOrigins = new Set(['file://', new URL(DEV_URL).origin])
  session.defaultSession.setPermissionRequestHandler((wc, permission, callback, details) => {
    if (permission === 'media') {
      const origin = details.requestingUrl ? new URL(details.requestingUrl).origin : 'file://'
      callback(allowedOrigins.has(origin))
    } else {
      callback(false)
    }
  })

  // Em desenvolvimento, sempre carrega o servidor Vite
  try {
    await win.loadURL(`${DEV_URL}/`)
    win.webContents.openDevTools({ mode: 'detach' })
    console.log('Carregando servidor de desenvolvimento:', `${DEV_URL}/`)
  } catch (error) {
    console.error('Erro ao carregar servidor de desenvolvimento:', error)
    // Fallback para arquivo local se o servidor falhar
    try {
      await win.loadFile(join(__dirname, '../dist/index.html'))
      console.log('Carregando arquivo local como fallback')
    } catch (fallbackError) {
      console.error('Erro ao carregar arquivo local:', fallbackError)
      // Mostra página de erro
      win.loadURL('data:text/html,<h1>Erro ao carregar aplicação</h1><p>Verifique se o servidor Vite está rodando em ' + DEV_URL + '</p>')
    }
  }

  // Adicionar logs úteis
  win.webContents.on('did-fail-load', (_e, code, desc, url) => {
    console.error('did-fail-load', code, desc, url)
  })
  win.webContents.on('did-finish-load', () => {
    console.log('Renderer carregado.')
  })

  win.on('closed', () => (win = null))
}

app.whenReady().then(async () => {
  // Criar overlays antes da janela principal
  createOverlays()
  
  // Criar janela principal
  await createWindow()
  
  // Expor função para testes no DevTools
  if (win) {
    win.webContents.executeJavaScript(`
      window.flashFocusAlert = () => {
        console.log('🔴 Testando overlay de foco...');
        return true;
      };
    `)
  }
})
app.on('window-all-closed', () => { if (process.platform !== 'darwin') app.quit() })
app.on('activate', () => { if (BrowserWindow.getAllWindows().length === 0) createWindow() })

// Handlers IPC para notificações
ipcMain.handle('notifications:isSupported', () => {
  // No Electron, sempre suportamos notificações
  console.log('🔔 main: notifications:isSupported - sempre retorna true')
  return true
})

ipcMain.handle('notifications:getPermission', () => {
  // No Electron, assumimos que temos permissão
  console.log('🔔 main: getPermission - sempre retorna granted')
  return 'granted'
})

ipcMain.handle('notifications:requestPermission', async () => {
  // No Electron, sempre concedemos permissão
  console.log('🔔 main: requestPermission - sempre retorna granted')
  return 'granted'
})

ipcMain.handle('notifications:send', async (event, title: string, options: any) => {
  console.log('🔔 main: send - criando notificação:', title)
  
  try {
    // Usar a API nativa do sistema operacional
    const notification = new (require('electron').Notification)({
      title,
      body: options?.body || '',
      icon: options?.icon || join(__dirname, '../public/favicon.ico'),
      silent: options?.silent || false
    })
    
    // Focar a janela quando clicar na notificação
    notification.on('click', () => {
      console.log('🔔 main: notificação clicada, focando janela')
      if (win) {
        win.focus()
      }
    })
    
    notification.show()
    console.log('🔔 main: notificação criada e exibida com sucesso')
    
    return { success: true, id: options?.tag || 'default' }
  } catch (error) {
    console.error('🔔 main: erro ao criar notificação:', error)
    return { success: false, error: error.message }
  }
})

// Handlers IPC para overlay
ipcMain.handle('overlay:flash', async (_e, ms = 600) => {
  console.log('🔴 main: overlay:flash - duração:', ms)
  try {
    flashOverlay(ms)
    return true
  } catch (error) {
    console.error('🔴 main: erro ao fazer flash do overlay:', error)
    return false
  }
})

ipcMain.handle('overlay:show', async () => {
  console.log('🔴 main: overlay:show')
  try {
    showOverlay()
    return true
  } catch (error) {
    console.error('🔴 main: erro ao mostrar overlay:', error)
    return false
  }
})

ipcMain.handle('overlay:hide', async () => {
  console.log('🔴 main: overlay:hide')
  try {
    hideOverlay()
    return true
  } catch (error) {
    console.error('🔴 main: erro ao esconder overlay:', error)
    return false
  }
})

ipcMain.handle('notifications:notifyFocusLoss', async (event, level: string) => {
  console.log('🔔 main: notifyFocusLoss - nível:', level)
  
  try {
    const title = '🚨 Perda de Foco Detectada!'
    const body = `Você perdeu o foco na sessão ${level}. Volte para a tela do ClopFocus!`
    
    // Usar a API nativa do Electron para notificações
    const notification = new (require('electron').Notification)({
      title,
      body,
      icon: join(__dirname, '../public/favicon.ico'),
      silent: false
    })
    
    // Focar a janela quando clicar na notificação
    notification.on('click', () => {
      console.log('🔔 main: notificação de perda de foco clicada, focando janela')
      if (win) {
        win.focus()
      }
    })
    
    notification.show()
    console.log('🔔 main: notificação de perda de foco criada e exibida com sucesso')
    
    return { success: true, id: 'focus-loss' }
  } catch (error) {
    console.error('🔔 main: erro ao criar notificação de perda de foco:', error)
    return { success: false, error: error.message }
  }
})

// Handlers IPC para modo de foco
let isFocusModeEnabled = false

ipcMain.handle('focusMode:toggle', async () => {
  console.log('🔒 main: focusMode:toggle - estado atual:', isFocusModeEnabled)
  
  try {
    isFocusModeEnabled = !isFocusModeEnabled
    
    if (isFocusModeEnabled) {
      console.log('🔒 main: Modo foco ATIVADO - bloqueando notificações externas')
      // Aqui implementaríamos a lógica para bloquear notificações externas
      // Por enquanto, apenas logamos o status
    } else {
      console.log('🔒 main: Modo foco DESATIVADO - permitindo notificações externas')
      // Aqui implementaríamos a lógica para permitir notificações externas
    }
    
    return isFocusModeEnabled
  } catch (error) {
    console.error('🔒 main: erro ao alternar modo foco:', error)
    return false
  }
})

ipcMain.handle('focusMode:getStatus', async () => {
  console.log('🔒 main: focusMode:getStatus - retornando:', isFocusModeEnabled)
  return isFocusModeEnabled
})
