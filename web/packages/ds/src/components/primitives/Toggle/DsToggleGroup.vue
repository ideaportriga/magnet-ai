<script setup lang="ts">
/**
 * ToggleGroup — set of `<DsToggleGroupItem>` controls. Wraps reka-ui
 * `<ToggleGroupRoot>`. The `variant` and `size` chosen here are inherited
 * by every child item via `provide`/`inject`.
 *
 *   <DsToggleGroup v-model="alignment" type="single">
 *     <DsToggleGroupItem value="left"><AlignLeftIcon /></DsToggleGroupItem>
 *     <DsToggleGroupItem value="center"><AlignCenterIcon /></DsToggleGroupItem>
 *   </DsToggleGroup>
 */

import {
  ToggleGroupRoot,
  type ToggleGroupRootEmits,
  type ToggleGroupRootProps,
  useForwardPropsEmits,
} from 'reka-ui'
import { reactiveOmit } from '@vueuse/core'
import { provide } from 'vue'
import type { DsToggleSize, DsToggleVariant } from './DsToggle.vue'
import { DS_TOGGLE_GROUP_KEY } from './toggleGroupContext'

const props = withDefaults(
  defineProps<
    ToggleGroupRootProps & {
      variant?: DsToggleVariant
      size?: DsToggleSize
      /** When true, items are rendered as a single segmented control. */
      joined?: boolean
    }
  >(),
  {
    variant: 'default',
    size: 'md',
    joined: false,
  },
)

const emit = defineEmits<ToggleGroupRootEmits>()

provide(DS_TOGGLE_GROUP_KEY, {
  variant: props.variant,
  size: props.size,
  joined: props.joined,
})

const delegated = reactiveOmit(props, 'variant', 'size', 'joined')
const forwarded = useForwardPropsEmits(delegated, emit)
</script>

<template>
  <ToggleGroupRoot
    v-slot="slotProps"
    v-bind="forwarded"
    class="ds-toggle-group"
    :data-variant="variant"
    :data-size="size"
    :data-joined="joined || undefined"
    data-test="ds-toggle-group"
  >
    <slot v-bind="slotProps" />
  </ToggleGroupRoot>
</template>

<style>
.ds-toggle-group {
  display: inline-flex;
  align-items: center;
  inline-size: fit-content;
  gap: var(--ds-space-2xs);
  border-radius: var(--ds-radius-md);
}

.ds-toggle-group[data-joined] { gap: 0; }
.ds-toggle-group[data-joined] .ds-toggle {
  border-radius: 0;
  border-inline-start-width: 0;
}
.ds-toggle-group[data-joined] .ds-toggle:first-child {
  border-start-start-radius: var(--ds-radius-md);
  border-end-start-radius: var(--ds-radius-md);
  border-inline-start-width: 1px;
}
.ds-toggle-group[data-joined] .ds-toggle:last-child {
  border-start-end-radius: var(--ds-radius-md);
  border-end-end-radius: var(--ds-radius-md);
}
</style>
