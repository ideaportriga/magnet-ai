import cypress from 'eslint-plugin-cypress/flat'
import vue from 'eslint-plugin-vue'
import baseConfig from '../../../eslint.config.mjs'

export default [
  cypress.configs['recommended'],
  ...baseConfig,
  ...vue.configs['flat/recommended'],
  {
    // Ignore all TypeScript files for this app
    ignores: ['**/*.ts', '**/*.tsx'],
  },
  {
    files: ['**/*.vue'],
    languageOptions: {
      parserOptions: {
        parser: await import('@typescript-eslint/parser'),
      },
    },
  },
  {
    files: ['**/*.js', '**/*.jsx', '**/*.vue'],
    rules: {
      'vue/multi-word-component-names': 'off',
      'vue/max-attributes-per-line': 'off',
      'vue/singleline-html-element-content-newline': 'off',
      'vue/no-v-html': 'off',
      // Disable prop validation rules for legacy code
      'vue/require-prop-types': 'off',
      'vue/require-default-prop': 'off',
      'vue/prop-name-casing': 'off',
      // §E.4 — forbid <q-table>. The app has fully migrated to
      // <km-data-table> (TanStack Table). See
      // FRONTEND_FIXES_ROADMAP.md Phase E and, as a reference migration,
      // GuidedExamplesTable.vue / NoteTakerProviders.vue.
      'vue/no-restricted-syntax': [
        'error',
        {
          selector: "VElement[rawName='q-table']",
          message:
            'Use <km-data-table> with useDataTable / useLocalDataTable instead of raw <q-table>.',
        },
      ],
    },
  },
]
