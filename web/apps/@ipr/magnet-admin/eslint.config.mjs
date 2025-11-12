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
    },
  },
]
