import { build } from 'esbuild'

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

console.log('Electron bundle pronto em dist-electron/')
