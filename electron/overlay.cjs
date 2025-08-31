// electron/overlay.js
const { BrowserWindow, screen } = require('electron');
const { join } = require('path');

let overlayWins = [];

function createOverlays() {
  console.log('🔴 overlay: createOverlays chamado');
  destroyOverlays();
  
  const displays = screen.getAllDisplays();
  console.log(`🔴 overlay: ${displays.length} displays encontrados`);
  
  for (const display of displays) {
    const { x, y, width, height } = display.bounds;
    console.log(`🔴 overlay: criando janela para display ${width}x${height} em (${x},${y})`);
    
    const win = new BrowserWindow({
      x, y, width, height,
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
      type: 'toolbar',
      webPreferences: { contextIsolation: true, nodeIntegration: false },
    });

    // deixa passar cliques p/ apps abaixo
    win.setIgnoreMouseEvents(true, { forward: true });
    // nível forte no topo
    win.setAlwaysOnTop(true, 'screen-saver');
    win.setVisibleOnAllWorkspaces(true, { visibleOnFullScreen: true });

    win.loadFile(join(__dirname, 'overlay.html'));
    win.hide();
    overlayWins.push(win);
    console.log(`🔴 overlay: janela criada e adicionada ao array (total: ${overlayWins.length})`);
  }

  screen.on('display-added',  recreateOverlays);
  screen.on('display-removed', recreateOverlays);
  screen.on('display-metrics-changed', recreateOverlays);
}

function recreateOverlays() {
  destroyOverlays();
  createOverlays();
}

function destroyOverlays() {
  overlayWins.forEach(w => { try { w.close(); } catch {} });
  overlayWins = [];
}

function flashOverlay(durationMs = 600) {
  console.log(`🔴 overlay: flashOverlay chamado com ${overlayWins.length} janelas`);
  
  if (overlayWins.length === 0) {
    console.log('🔴 overlay: ERRO - nenhuma janela de overlay criada!');
    return;
  }
  
  overlayWins.forEach((w, i) => {
    try {
      console.log(`🔴 overlay: mostrando janela ${i}`);
      w.showInactive(); // não rouba foco
    } catch (error) {
      console.error(`🔴 overlay: erro ao mostrar janela ${i}:`, error);
    }
  });
  
  setTimeout(() => {
    console.log(`🔴 overlay: escondendo overlays após ${durationMs}ms`);
    overlayWins.forEach((w, i) => {
      try {
        w.hide();
      } catch (error) {
        console.error(`🔴 overlay: erro ao esconder janela ${i}:`, error);
      }
    });
  }, durationMs);
}

function showOverlay() {
  overlayWins.forEach(w => w.showInactive());
}

function hideOverlay() {
  overlayWins.forEach(w => w.hide());
}

module.exports = {
  createOverlays,
  destroyOverlays,
  flashOverlay,
  showOverlay,
  hideOverlay
};
