import { app, BrowserWindow, session } from 'electron'
import { join } from 'path'

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

app.whenReady().then(createWindow)
app.on('window-all-closed', () => { if (process.platform !== 'darwin') app.quit() })
app.on('activate', () => { if (BrowserWindow.getAllWindows().length === 0) createWindow() })
