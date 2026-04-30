import nx from '@nx/eslint-plugin';

export default [
  ...nx.configs['flat/base'],
  ...nx.configs['flat/typescript'],
  ...nx.configs['flat/javascript'],
  {
    ignores: ['**/dist', '**/documentation', '**/src/paraglide/**'],
  },
  {
    files: ['**/*.ts', '**/*.tsx', '**/*.js', '**/*.jsx', '**/*.vue'],
    rules: {
      '@nx/enforce-module-boundaries': [
        'error',
        {
          enforceBuildableLibDependency: true,
          allow: ['^.*/eslint(\\.base)?\\.config\\.[cm]?js$', '@shared', '@shared/.*'],
          depConstraints: [
            {
              sourceTag: '*',
              onlyDependOnLibsWithTags: ['*'],
            },
          ],
        },
      ],
      'no-restricted-imports': [
        'error',
        {
          paths: [
            {
              name: 'quasar',
              message: 'Quasar runtime has been removed. Use @ds/* primitives, @ds/composables, or @ds/compat/quasar for utility helpers (copyToClipboard, openURL, uid, date, colors).',
            },
          ],
          patterns: [
            {
              group: ['quasar/*'],
              message: 'Quasar runtime has been removed. Use @ds/* instead.',
            },
          ],
        },
      ],
    },
  },
  {
    files: ['**/*.ts', '**/*.tsx', '**/*.js', '**/*.jsx', '**/*.vue'],
    rules: {
      'no-restricted-imports': [
        'error',
        {
          paths: [
            {
              name: 'quasar',
              message: 'Quasar runtime has been removed. Use @ds/* primitives, @ds/composables, or @ds/compat/legacy for transitional helpers.',
            },
          ],
          patterns: [
            {
              group: ['quasar/*'],
              message: 'Quasar runtime has been removed. Use @ds/* instead.',
            },
            {
              group: ['@quasar/extras', '@quasar/extras/*'],
              message: '@quasar/extras is a legacy icon/font bridge. Do not add new imports; migrate icons/fonts through @ds/@themes assets.',
            },
          ],
        },
      ],
    },
  },
  {
    files: [
      '**/*.ts',
      '**/*.tsx',
      '**/*.cts',
      '**/*.mts',
      '**/*.js',
      '**/*.jsx',
      '**/*.cjs',
      '**/*.mjs',
    ],
    // Override or add rules here
    rules: {},
  },
];
