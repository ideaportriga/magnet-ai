/// <reference types='vitest' />
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { nxViteTsPaths } from '@nx/vite/plugins/nx-tsconfig-paths.plugin'
import { nxCopyAssetsPlugin } from '@nx/vite/plugins/nx-copy-assets.plugin'
import vueDevTools from 'vite-plugin-vue-devtools'
import { quasar, transformAssetUrls } from '@quasar/vite-plugin'
import path from 'path'
import basicSsl from '@vitejs/plugin-basic-ssl'
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
  ],
  build: {
    outDir: '../../../knowledge-magnet/admin/app',
    emptyOutDir: true,
    reportCompressedSize: true,
    commonjsOptions: {
      transformMixedEsModules: true,
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
    port: 7000,
    cors: {
      origin: ['http://localhost:7000', 'http://locahost:7002'],
    },
  },
  preview: {
    port: 7001,
    https: true,
    host: 'localhost',
  },
  base: './',
})
