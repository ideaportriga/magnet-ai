/// <reference types='vitest' />
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { nxViteTsPaths } from '@nx/vite/plugins/nx-tsconfig-paths.plugin'
import { nxCopyAssetsPlugin } from '@nx/vite/plugins/nx-copy-assets.plugin'
import vueDevTools from 'vite-plugin-vue-devtools'
import { quasar, transformAssetUrls } from '@quasar/vite-plugin'
import path from 'path'
import basicSsl from '@vitejs/plugin-basic-ssl'
import { paraglideVitePlugin } from '@inlang/paraglide-js'
// import { fileURLToPath } from 'url'
// const __dirname = path.dirname(fileURLToPath(import.meta.url))
// const __buildDir = path.resolve(__dirname, '../../knowledge-magnet/panel')

export default defineConfig({
  root: __dirname,
  cacheDir: '../../../node_modules/.vite/apps/@ipr/magnet-admin',
  resolve: {
    alias: {
      '@': path.resolve(__dirname, 'src'),
    },
  },
  plugins: [
    basicSsl(),
    vue({
      template: {
        transformAssetUrls,
      },
    }),
    quasar({
      sassVariables: '@/styles/quasar-variables.sass',
    }),
    nxViteTsPaths(),
    nxCopyAssetsPlugin(['*.md']),
    vueDevTools(),
    paraglideVitePlugin({
      project: path.resolve(__dirname, '../../../project.inlang'),
      outdir: path.resolve(__dirname, 'src/paraglide'),
    }),
  ],
  build: {
    outDir: '../../../knowledge-magnet/admin/app',
    emptyOutDir: true,
    reportCompressedSize: true,
    commonjsOptions: {
      transformMixedEsModules: true,
    },
    // §C.1 — split heavy vendor libs into named async chunks. Without this the
    // main bundle bundled Vue, Quasar, TanStack and codemirror together (~800KB),
    // and every route hit had to parse the whole thing. Named chunks let the
    // browser cache each library independently across deploys.
    rollupOptions: {
      output: {
        manualChunks: {
          vue: ['vue', 'vue-router', 'pinia'],
          quasar: ['quasar', '@quasar/extras'],
          query: ['@tanstack/vue-query', '@tanstack/vue-table'],
          editor: ['vue-codemirror'],
        },
      },
    },
  },
  test: {
    watch: false,
    globals: true,
    environment: 'jsdom',
    include: ['src/**/*.{test,spec}.{js,mjs,cjs,ts,mts,cts,jsx,tsx}'],
    reporters: ['default'],
    coverage: {
      reportsDirectory: '../../../coverage/apps/@ipr/magnet-admin',
      provider: 'v8',
    },
  },
  server: {
    host: 'localhost',
    hmr: {
      host: 'localhost',
    },
    https: true,
    port: 7001,
    cors: {
      origin: ['http://localhost:7001', 'https://localhost:7001', 'http://localhost:7002'],
    },
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
      },
      '/auth': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
      },
      '/health': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
      },
      // DEBUG_MODE-only test utility endpoints (cleanup, promote, errors)
      // mounted at the app root (not under /api). Needed by Cypress.
      '/test': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
      },
      '/loki': {
        target: 'http://localhost:3100',
        changeOrigin: true,
        secure: false,
      },
    },
  },
  preview: {
    port: 7001,
    https: true,
    host: 'localhost',
  },
  base: '/admin/',
})
