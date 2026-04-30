/**
 * @ds — Magnet design system entry point.
 *
 * The CSS layers (tokens, composition, utilities, reset) ship as side-effect
 * stylesheet imports so they can be loaded individually:
 *
 *   import '@ds/tokens'
 *   import '@ds/composition'
 *   import '@ds/utilities'
 *   import '@ds/reset'
 *
 * Or all at once via `import '@ds/styles'`.
 *
 * Components, composables, hosts and the compat layer live in their own
 * sub-paths so consumers can import precisely what they need.
 */

import type { App } from 'vue'

/** Reserved for future runtime configuration (toast position, dialog z-index, …). */
export type DsPluginOptions = Record<string, never>

/**
 * Vue plugin install. Currently a no-op — the host components
 * (`DsToastHost`, `DsDialogHost`, `DsLoadingHost`) must be mounted
 * explicitly in the application root layout. Keeping `install` as a no-op
 * lets `magnet-admin` call `app.use(ds)` today without behaviour drift.
 */
export const install = (_app: App, _options: DsPluginOptions = {}): void => {
  // intentionally empty — see file header
  void _app
  void _options
}

const ds = { install }

export default ds

/* ----- Re-exports for ergonomic single-import use cases ----- */

export { useNotify, notify, type NotifyConfirmOptions, type NotifyHandle } from './composables/useNotify'
export { useDialog, type DialogConfirmOptions } from './composables/useDialog'
export { useLoading } from './composables/useLoading'
export { useScreen, type DsBreakpoint } from './composables/useScreen'
export { useDarkMode, type DsThemeMode } from './composables/useDarkMode'
export { resolveDsColor } from './utils/resolveDsColor'
