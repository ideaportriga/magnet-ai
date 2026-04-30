/// <reference types="vitest" />
import { defineConfig } from 'vitest/config'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath } from 'node:url'
import { resolve } from 'node:path'

const root = fileURLToPath(new URL('.', import.meta.url))
const webRoot = resolve(root, '../..')

export default defineConfig({
  root,
  plugins: [vue()],
  resolve: {
    alias: [
      // Order matters: more-specific aliases first.
      { find: '@ds/tokens', replacement: resolve(webRoot, 'packages/ds/src/tokens/index.ts') },
      { find: '@ds/composition', replacement: resolve(webRoot, 'packages/ds/src/composition/index.ts') },
      { find: '@ds/utilities', replacement: resolve(webRoot, 'packages/ds/src/utilities/index.ts') },
      { find: '@ds/reset', replacement: resolve(webRoot, 'packages/ds/src/reset/index.ts') },
      { find: '@ds/composables', replacement: resolve(webRoot, 'packages/ds/src/composables/index.ts') },
      { find: '@ds/hosts', replacement: resolve(webRoot, 'packages/ds/src/hosts/index.ts') },
      { find: '@ds/primitives', replacement: resolve(webRoot, 'packages/ds/src/components/primitives/index.ts') },
      { find: '@ds/domain', replacement: resolve(webRoot, 'packages/ds/src/components/domain/index.ts') },
      { find: '@ds/styles', replacement: resolve(webRoot, 'packages/ds/src/styles.ts') },
      { find: /^@ds\/(.*)$/, replacement: resolve(webRoot, 'packages/ds/src') + '/$1' },
      { find: '@ds', replacement: resolve(webRoot, 'packages/ds/src') },
      { find: /^@shared\/(.*)$/, replacement: resolve(webRoot, 'packages/shared/src/lib') + '/$1' },
      { find: '@shared', replacement: resolve(webRoot, 'packages/shared/src/index.ts') },
    ],
  },
  test: {
    name: 'ds',
    globals: true,
    environment: 'jsdom',
    include: ['src/**/*.{spec,test}.{ts,tsx}'],
    css: false,
    setupFiles: ['./vitest.setup.ts'],
  },
})
