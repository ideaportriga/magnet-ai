/// <reference types='vitest' />
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { nxViteTsPaths } from '@nx/vite/plugins/nx-tsconfig-paths.plugin'
import { nxCopyAssetsPlugin } from '@nx/vite/plugins/nx-copy-assets.plugin'
import vueDevTools from 'vite-plugin-vue-devtools'
import { quasar, transformAssetUrls } from '@quasar/vite-plugin'
import basicSsl from '@vitejs/plugin-basic-ssl'
import path from 'path'
import { paraglideVitePlugin } from '@inlang/paraglide-js'

export default defineConfig({
  root: __dirname,
  cacheDir: '../../../node_modules/.vite/apps/@ipr/magnet-panel',
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
    vueDevTools(),
    quasar({
      // sassVariables: '@/styles/quasar-variables.sass' // Simplified path
    }),
    nxViteTsPaths(),
    nxCopyAssetsPlugin(['*.md']),
    paraglideVitePlugin({
      project: path.resolve(__dirname, '../../../project.inlang'),
      outdir: path.resolve(__dirname, 'src/paraglide'),
    }),
  ],
  // Uncomment this if you are using workers.
  // worker: {
  //  plugins: [ nxViteTsPaths() ],
  // },
  build: {
    outDir: '../../../knowledge-magnet/panel/app',
    emptyOutDir: true,
    reportCompressedSize: true,
    commonjsOptions: {
      transformMixedEsModules: true,
    },
    // §C.1 — split vendor libs (see magnet-admin/vite.config.ts for rationale).
    rollupOptions: {
      output: {
        manualChunks: {
          vue: ['vue', 'vue-router', 'pinia'],
          quasar: ['quasar', '@quasar/extras'],
          query: ['@tanstack/vue-query'],
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
      reportsDirectory: '../../../coverage/apps/@ipr/magnet-panel',
      provider: 'v8',
    },
  },
  server: {
    hmr: {
      host: 'localhost',
    },
    https: true,
    port: 7002,
    cors: {
      origin: ['http://localhost:7002', 'https://test-ai-bridge.ambitiousisland-a233b755.westeurope.azurecontainerapps.io', 'http://localhost:7001', 'https://localhost:7001'],
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
    },
  },
  preview: {
    port: 7003,
    https: true,
    host: 'localhost',
  },
  base: '/panel/',
})
