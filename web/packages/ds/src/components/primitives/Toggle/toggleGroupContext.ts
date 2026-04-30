import type { InjectionKey } from 'vue'
import type { DsToggleSize, DsToggleVariant } from './DsToggle.vue'

export interface DsToggleGroupContext {
  variant: DsToggleVariant
  size: DsToggleSize
  joined: boolean
}

export const DS_TOGGLE_GROUP_KEY: InjectionKey<DsToggleGroupContext> =
  Symbol('DsToggleGroup')
