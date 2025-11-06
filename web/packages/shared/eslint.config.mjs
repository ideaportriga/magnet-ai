import baseConfig from '../../eslint.config.mjs'

export default [
  ...baseConfig,
  {
    files: ['**/*.js', '**/*.ts'],
    rules: {
      '@nx/enforce-module-boundaries': 'off',
    },
  },
]
