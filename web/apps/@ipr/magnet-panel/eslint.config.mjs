import vue from 'eslint-plugin-vue'
import baseConfig from '../../../eslint.config.mjs'

export default [
  ...baseConfig,
  ...vue.configs['flat/recommended'],
  {
    files: ['**/*.vue'],
    languageOptions: {
      parserOptions: {
        parser: await import('@typescript-eslint/parser')
      }
    }
  },
  {
    files: ['**/*.ts', '**/*.tsx', '**/*.js', '**/*.jsx', '**/*.vue'],
    rules: {
      'vue/multi-word-component-names': 'off',
      // §E.4 — forbid <q-table>; use <km-data-table> instead.
      'vue/no-restricted-syntax': [
        'error',
        {
          selector: "VElement[rawName='q-table']",
          message:
            'Use <km-data-table> with useDataTable / useLocalDataTable instead of raw <q-table>.',
        },
      ],
    }
  }
]
