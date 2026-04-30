import type { ComputedRef, InjectionKey } from 'vue'

export const KM_TAB_PANELS_ACTIVE_KEY: InjectionKey<ComputedRef<string | undefined>> = Symbol('km-tab-panels-active')
