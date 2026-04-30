<script setup lang="ts">
/**
 * ToggleGroupItem — individual button inside `<DsToggleGroup>`. Inherits
 * `variant` / `size` from the surrounding group; per-item overrides win.
 */

import {
  ToggleGroupItem,
  type ToggleGroupItemProps,
  useForwardProps,
} from 'reka-ui'
import { reactiveOmit } from '@vueuse/core'
import { inject } from 'vue'
import { DS_TOGGLE_GROUP_KEY } from './toggleGroupContext'
import type { DsToggleSize, DsToggleVariant } from './DsToggle.vue'

const props = defineProps<
  ToggleGroupItemProps & {
    variant?: DsToggleVariant
    size?: DsToggleSize
  }
>()

const ctx = inject(DS_TOGGLE_GROUP_KEY, undefined)

const delegated = reactiveOmit(props, 'variant', 'size')
const forwarded = useForwardProps(delegated)
</script>

<template>
  <ToggleGroupItem
    v-slot="slotProps"
    v-bind="forwarded"
    class="ds-toggle"
    :data-variant="variant ?? ctx?.variant ?? 'default'"
    :data-size="size ?? ctx?.size ?? 'md'"
    data-test="ds-toggle-group-item"
  >
    <slot v-bind="slotProps" />
  </ToggleGroupItem>
</template>
