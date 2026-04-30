/**
 * Shared context between `KmTabs` and `KmTab`. Lives in its own module so
 * `<script setup>` blocks (which forbid ES module re-exports) can both
 * import it.
 */

import type { ComputedRef, InjectionKey } from 'vue'
import type { DsTabItem } from '../primitives/Tabs/DsTabs.vue'

export interface TabsContext {
  active: ComputedRef<string | undefined>
  registerTab: (item: DsTabItem) => void
  unregisterTab: (value: string) => void
}

export const TabsContextKey: InjectionKey<TabsContext> = Symbol('km-tabs-context')
