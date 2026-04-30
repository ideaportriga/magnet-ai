import vue from 'eslint-plugin-vue';
import baseConfig from '../../eslint.config.mjs';

export default [
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
      // Optional props without defaults are common and intentional in this
      // package — most defaults come from Reka UI primitives or are
      // genuinely optional (label, id, modelValue, …).
      'vue/require-default-prop': 'off',
      // Self-closing void elements are HTML-valid and cleaner in Vue SFCs;
      // the legacy ui-comp package follows the same convention.
      'vue/html-self-closing': 'off',
    },
  },
  {
    files: ['src/components/**/*.{vue,ts,tsx,js,jsx}', 'src/composables/**/*.{ts,js}', 'src/hosts/**/*.{vue,ts}'],
    rules: {
      'no-restricted-imports': [
        'error',
        {
          paths: [
            {
              name: 'quasar',
              message: 'The @ds package must not depend on Quasar. Use Reka UI primitives, @ds tokens, or web-platform APIs directly.',
            },
          ],
          patterns: [
            {
              group: ['quasar/*'],
              message: 'Importing from quasar/* in @ds is not allowed. Use Reka UI primitives or @ds tokens.',
            },
          ],
        },
      ],
    },
  },
];
