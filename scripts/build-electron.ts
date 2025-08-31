import { build } from 'esbuild'
import { copyFile, mkdir } from 'fs/promises'
import { join } from 'path'

// Build dos arquivos TypeScript
await build({
  entryPoints: {
    main: 'electron/main.ts',
    preload: 'electron/preload.ts',
  },
  outdir: 'dist-electron',
  platform: 'node',
  format: 'cjs',
  target: 'node18',
  bundle: true,
  sourcemap: false,
  external: ['electron'],
  outExtension: { '.js': '.cjs' },
})

// Copiar arquivos estáticos necessários
try {
  await copyFile('electron/overlay.html', 'dist-electron/overlay.html')
  console.log('✅ overlay.html copiado para dist-electron/')
} catch (error) {
  console.error('❌ Erro ao copiar overlay.html:', error)
}

console.log('Electron bundle pronto em dist-electron/')
