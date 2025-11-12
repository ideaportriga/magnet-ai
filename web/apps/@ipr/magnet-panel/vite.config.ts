/// <reference types='vitest' />
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { nxViteTsPaths } from '@nx/vite/plugins/nx-tsconfig-paths.plugin'
import { nxCopyAssetsPlugin } from '@nx/vite/plugins/nx-copy-assets.plugin'
import vueDevTools from 'vite-plugin-vue-devtools'
import { quasar, transformAssetUrls } from '@quasar/vite-plugin'
import basicSsl from '@vitejs/plugin-basic-ssl'
import path from 'path'

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
      origin: ['http://localhost:7002', 'https://test-ai-bridge.ambitiousisland-a233b755.westeurope.azurecontainerapps.io', 'http://localhost:7000'],
    },
  },
  preview: {
    port: 7003,
    https: true,
    host: 'localhost',
  },
  base: "/panel/"
})
