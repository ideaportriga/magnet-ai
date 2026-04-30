/**
 * Notification helpers — Phase 4b: this file is now a thin bridge over the
 * `@ds` Toast system (`useNotify`). Public API is identical, so the 38+
 * callers across `magnet-admin` and `magnet-panel` continue to work
 * unchanged.
 *
 * Why we kept the file (rather than removing it and updating imports
 * everywhere): the codebase reaches for `notify` from many places —
 * components, stores, plugins, even non-Vue helpers. Keeping the symbol at
 * its current location avoids one large mechanical change-set; the symbol
 * just delegates to the new implementation.
 *
 * To send a toast the host component `<DsToastHost>` must be mounted at
 * the application root (see `magnet-admin/src/App.vue` and
 * `magnet-panel/src/App.vue`). When it is not mounted the toast is queued
 * in memory and rendered as soon as the host appears.
 */

import { notify as dsNotify, type NotifyConfirmOptions as DsNotifyConfirmOptions } from '@ds/composables/useNotify'

export type NotifyConfirmOptions = DsNotifyConfirmOptions

export const notify = dsNotify
