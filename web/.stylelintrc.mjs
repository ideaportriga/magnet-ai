/**
 * Stylelint config for the Magnet design system + apps.
 *
 * Goal: catch REAL bugs and DS-contract violations, not bikeshed formatting.
 * Stylistic noise from `stylelint-config-standard` is opted out — Prettier
 * owns whitespace.
 *
 * What we DO enforce:
 *   1. Token discipline      — no hex/rgba literals in feature CSS, no
 *                              `transition: all`, no unknown properties/units.
 *   2. Defensive patterns    — accidental :hover, list-style: none on
 *                              navigation, unsafe will-change, mixed prefixes,
 *                              missing flex-wrap on multiline rows, etc.
 *   3. Logical properties    — width/height/margin-left etc. → inline-size /
 *                              block-size / margin-inline.
 *   4. Naming                — `block__elem--mod` for component scoped CSS.
 *   5. Specificity sanity    — no IDs, no qualifying types, max specificity
 *                              0,4,0, max nesting 3.
 *
 * Per-area overrides relax the rules where they would lie:
 *   - tokens / utilities / themes / composition: hex / raw px / non-BEM allowed
 *   - apps assets/legacy global stylesheets:      raw px ok
 *   - DS components:                              softer BEM, soft hex
 *
 * Run:
 *   yarn lint:css            # full report
 *   yarn lint:css:errors     # errors only (`--quiet`)
 *   yarn lint:css:fix        # auto-fix where supported
 */

const TOKEN_CSS_FILES = [
  'packages/ds/src/tokens/**/*.css',
  'packages/ds/src/utilities/**/*.css',
  'packages/themes/**/*.css',
  'packages/ds/src/composition/**/*.css',
  'packages/ds/src/reset/**/*.css',
]

export default {
  extends: [
    'stylelint-config-standard',
    'stylelint-config-recommended-vue',
  ],
  plugins: [
    'stylelint-plugin-defensive-css',
    'stylelint-plugin-logical-css',
    'stylelint-selector-bem-pattern',
  ],
  ignoreFiles: [
    '**/node_modules/**',
    '**/dist/**',
    '**/.nx/**',
    '**/coverage/**',
    '**/documentation/**',
    '**/paraglide/**',
    'packages/themes/src/base/assets/css/**',  // 3rd-party fontawesome / material-icons
  ],

  rules: {
    /* ─── Defensive CSS — catches real-world layout/a11y bugs ───────────
     *
     * Curated subset:
     *   ✓  no-list-style-none, no-mixed-vendor-prefixes, no-unsafe-*,
     *      require-background-repeat, require-focus-visible,
     *      require-overscroll-behavior, require-pure-selectors —
     *      all catch real bugs without significant noise.
     *
     *   ⨯  no-accidental-hover — disabled. Wrapping every :hover in
     *      `@media (hover: hover)` is correct for touch-first apps but
     *      Magnet admin/panel are desktop-first. 366 warnings of pure noise.
     *
     *   ⨯  require-flex-wrap — disabled. The default `nowrap` is almost
     *      always intentional in our layouts (toolbars, header rows).
     *      Forcing explicit `flex-wrap: nowrap` on every flex parent is
     *      style boilerplate, not a bug catcher.
     *
     *   ⨯  no-user-select-none — disabled. Many of our 41 hits are valid
     *      (tab labels, drag handles, dropdown chevrons). Selective fixes
     *      via per-file disable comment if needed.
     *
     *   ⨯  require-system-font-fallback — disabled. Our --ds-font-default
     *      token already chains 'Geist', 'Inter', sans-serif. Plugin
     *      doesn't unwrap var() so warns on every consumer. The check
     *      belongs at the token-definition layer (one-time review).
     */
    'defensive-css/no-accidental-hover':            null,
    'defensive-css/no-list-style-none':             [true, { severity: 'warning' }],
    'defensive-css/no-mixed-vendor-prefixes':       [true, { severity: 'warning' }],
    'defensive-css/no-unsafe-clamp-font-size':      [true, { severity: 'warning' }],
    'defensive-css/no-unsafe-will-change':          [true, { severity: 'warning' }],
    'defensive-css/no-user-select-none':            null,
    'defensive-css/require-background-repeat':      [true, { severity: 'warning' }],
    'defensive-css/require-flex-wrap':              null,
    'defensive-css/require-focus-visible':          [true, { severity: 'warning' }],
    'defensive-css/require-overscroll-behavior':    [true, { severity: 'warning' }],
    // Disabled: false-positive on legit cases.
    //   1. `:deep(<element>)` in markdown/prose renderers (KmMarkdown, generated
    //      content) MUST style raw <p>/<h1>/<a>/<pre> without classes.
    //   2. The plugin misreads @keyframes step keywords (`from`, `to`, `0%`,
    //      `100%`) as element-tag selectors.
    'defensive-css/require-pure-selectors':         null,
    'defensive-css/require-system-font-fallback':   null,

    /* ─── Logical properties (already ~95% of our CSS is logical) ─────── */
    'logical-css/require-logical-properties': [true, { severity: 'warning' }],
    'logical-css/require-logical-units':      [true, { severity: 'warning' }],
    'logical-css/require-logical-keywords':   [true, {
      severity: 'warning',
      // `caption-side: block-end` is rejected by the standard rule
      // `declaration-property-value-no-unknown` (older mdn-data); keep `bottom`.
      ignore: ['caption-side'],
    }],

    /* ─── BEM pattern in scoped CSS ────────────────────────────────────── */
    'plugin/selector-bem-pattern': {
      preset: 'bem',
      componentName: '[a-z][a-z0-9]*(?:-[a-z0-9]+)*',
      componentSelectors: {
        initial: '^\\.{componentName}(?:__[a-z0-9-]+)?(?:--[a-z0-9-]+)?(?:\\[[^\\]]+\\])?$',
        combined: '^\\.[-_a-z0-9]+(?:__[a-z0-9-]+)?(?:--[a-z0-9-]+)?(?:\\[[^\\]]+\\])?$',
      },
      ignoreSelectors: ['^:.+', '^&', '^\\*', '^>'],
      severity: 'warning',
    },

    /* ─── Token discipline (banned in feature code) ────────────────────── */
    'color-no-hex':  [true, { severity: 'error' }],
    'color-named':   ['never', { severity: 'error' }],

    'declaration-property-value-disallowed-list': {
      'transition':           ['/^all\\b/'],
      'transition-property':  ['/^all$/'],
    },

    'unit-disallowed-list': [
      ['em', 'rem'],
      {
        ignoreProperties: {
          // `em` is the idiomatic unit for inline icon/spinner sizing
          // (auto-scales with font-size). Keeping it on size properties is
          // intentional, not a token-discipline violation.
          'em': [
            'line-height', 'letter-spacing', 'font-size',
            'inline-size', 'block-size', 'width', 'height',
            'min-inline-size', 'min-block-size', 'min-width', 'min-height',
            'max-inline-size', 'max-block-size', 'max-width', 'max-height',
          ],
          // `rem` is the DS-sanctioned unit for intrinsic component sizing
          // (popover/dialog/dropdown widths) where logical-properties accept
          // density-aware values that scale with the root font-size.
          'rem': [
            'line-height', 'letter-spacing', 'font-size',
            'inline-size', 'block-size', 'width', 'height',
            'min-inline-size', 'min-block-size', 'min-width', 'min-height',
            'max-inline-size', 'max-block-size', 'max-width', 'max-height',
            'flex', 'flex-basis',
            'grid-template-columns', 'grid-template-rows',
            // CSS custom property declarations (e.g. `--sidebar-side-width: 18rem`)
            // are intrinsic-size tokens and the plugin can't tell them apart,
            // so allow them via the wildcard match.
            '/^--/',
          ],
        },
        severity: 'warning',
      },
    ],

    /* ─── Real-bug catchers ────────────────────────────────────────────── */
    'declaration-property-value-no-unknown': [true, {
      // Vue scoped CSS uses `v-bind(<ref>)` which postcss-html doesn't always lift.
      ignoreProperties: { '/.*/': ['/^v-bind\\(/'] },
    }],
    'unit-no-unknown': true,
    'property-no-unknown': true,
    'function-no-unknown': [true, {
      ignoreFunctions: ['v-bind', 'theme'],            // Vue scoped CSS uses v-bind()
    }],
    'property-no-deprecated': [true, { severity: 'warning' }],

    /* ─── Specificity / nesting hygiene ────────────────────────────────── */
    'selector-max-specificity': ['0,4,0', { severity: 'warning' }],
    'selector-max-id': 0,
    'no-descending-specificity': null,
    'max-nesting-depth': [3, { severity: 'warning' }],

    /* ─── Auto-fixable hygiene worth keeping ───────────────────────────── */
    'declaration-block-no-redundant-longhand-properties': [true, { severity: 'warning' }],
    'declaration-block-no-shorthand-property-overrides':  [true, { severity: 'warning' }],
    'shorthand-property-no-redundant-values':             [true, { severity: 'warning' }],
    'no-duplicate-selectors':                             [true, { severity: 'warning' }],
    'value-no-vendor-prefix':                             [true, { severity: 'warning' }],
    'property-no-vendor-prefix':                          [true, { severity: 'warning' }],

    /* ─── Disable purely stylistic rules — Prettier owns formatting ────── */
    'alpha-value-notation':                  null,
    'color-function-notation':               null,
    'color-function-alias-notation':         null,
    'at-rule-empty-line-before':             null,
    'declaration-empty-line-before':         null,
    'rule-empty-line-before':                null,
    'comment-empty-line-before':             null,
    'comment-whitespace-inside':             null,
    'selector-not-notation':                 null,
    'selector-pseudo-element-colon-notation': null,
    'declaration-block-single-line-max-declarations': null,
    'value-keyword-case':                    null,
    'media-feature-range-notation':          null,
    'length-zero-no-unit':                   null,
    'hue-degree-notation':                   null,
    'no-empty-source':                       null,
    'no-invalid-position-at-import-rule':    null,
    'font-family-name-quotes':               null,
    'selector-attribute-quotes':             null,
    'comment-no-empty':                      null,
    'declaration-block-no-duplicate-properties': [true, { ignore: ['consecutive-duplicates-with-different-values'] }],
    'no-irregular-whitespace':               null,
    'custom-property-empty-line-before':     null,
    'color-hex-length':                      null,

    /* ─── Already-handled by other tooling ─────────────────────────────── */
    'selector-class-pattern':    null,                 // BEM plugin handles naming
    'custom-property-pattern':   null,                 // we use --ds-*, --km-*, --ds-brand-*
    'media-feature-name-no-unknown': true,
    'at-rule-no-unknown': [true, { ignoreAtRules: ['layer', 'apply'] }],
  },

  /* ─── Per-area overrides ─────────────────────────────────────────────── */
  overrides: [
    // Token / utility / theme / composition / reset — define raw values, not BEM-named.
    {
      files: TOKEN_CSS_FILES,
      rules: {
        'color-no-hex': null,
        'color-named': null,
        'unit-disallowed-list': null,
        'plugin/selector-bem-pattern': null,
        'logical-css/require-logical-properties': null,
        'logical-css/require-logical-units': null,
        'logical-css/require-logical-keywords': null,
        'declaration-property-value-disallowed-list': null,
        'defensive-css/require-pure-selectors': null,
        'selector-max-specificity': null,
        'selector-max-id': null,                          // legacy mount-point IDs (#km-app)
        'declaration-block-no-duplicate-properties': null, // browser fallbacks (tab-size, appearance)
        'declaration-property-value-keyword-no-deprecated': null, // appearance: button kept for compat
        'font-family-no-missing-generic-family-keyword': [true, { severity: 'warning' }],
      },
    },
    // App-level global CSS (assets/layout.css) — historic, raw px ok.
    {
      files: ['apps/**/assets/**/*.css', 'apps/**/src/**/*.css'],
      rules: {
        'color-no-hex': [true, { severity: 'warning' }],
        'unit-disallowed-list': null,
        'plugin/selector-bem-pattern': null,
      },
    },
    // App-level Vue SFC scoped styles — gradual hex migration; warn, don't block CI.
    {
      files: ['apps/**/*.vue'],
      rules: {
        'color-no-hex': [true, { severity: 'warning' }],
      },
    },
    // DS components — internal CSS, narrow exemptions.
    {
      files: ['packages/ds/src/components/**/*.{vue,css}', 'packages/ui-comp/**/*.{vue,css}'],
      rules: {
        'color-no-hex': [true, { severity: 'warning' }],
        'plugin/selector-bem-pattern': null,
      },
    },
    // Vue SFCs — postcss-html parser.
    {
      files: ['**/*.vue'],
      customSyntax: 'postcss-html',
    },
  ],
}
