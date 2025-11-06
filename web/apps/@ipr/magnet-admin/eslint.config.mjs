import cypress from 'eslint-plugin-cypress/flat'
import vue from 'eslint-plugin-vue'
import baseConfig from '../../../eslint.config.mjs'

export default [
  cypress.configs['recommended'],
  ...baseConfig,
  ...vue.configs['flat/recommended'],
  {
    files: ['**/*.vue'],
    languageOptions: {
      parserOptions: {
        parser: await import('@typescript-eslint/parser'),
      },
    },
  },
  {
    files: ['**/*.ts', '**/*.tsx', '**/*.js', '**/*.jsx', '**/*.vue'],
    rules: {
      'vue/multi-word-component-names': 'off',
      'vue/max-attributes-per-line': 'off',
      'vue/singleline-html-element-content-newline': 'off',
      'vue/no-v-html': 'off',
      // Disable prop validation rules for legacy code
      'vue/require-prop-types': 'off',
      'vue/require-default-prop': 'off',
      'vue/prop-name-casing': 'off',
      // Disable TypeScript rules for legacy code
      '@typescript-eslint/no-unused-vars': 'off',
      '@typescript-eslint/no-explicit-any': 'off',
    },
  },
  {
    files: ['**/*.ts'],
    // Ignore all TypeScript files
    ignores: ['**/*.ts'],
  },
  {
    files: ['**/*.js'],
    // Override or add rules here
    rules: {},
  },
  {
    // Override or add rules here
    rules: {},
  },
]
