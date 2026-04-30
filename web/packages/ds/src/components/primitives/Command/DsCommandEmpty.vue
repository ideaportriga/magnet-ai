<script setup lang="ts">
/**
 * CommandEmpty — content shown when the search yields zero matches.
 * Auto-hidden when there's no search or any items match.
 */
import type { PrimitiveProps } from 'reka-ui'
import { Primitive } from 'reka-ui'
import { computed } from 'vue'
import { useCommandContext } from './context'

const props = defineProps<PrimitiveProps>()

const { filterState } = useCommandContext()
const isRender = computed(
  () => !!filterState.search && filterState.filtered.count === 0,
)
</script>

<template>
  <Primitive
    v-if="isRender"
    v-bind="props"
    class="ds-command__empty"
    data-test="ds-command-empty"
  >
    <slot />
  </Primitive>
</template>

<style>
.ds-command__empty {
  padding-block: var(--ds-space-xl);
  text-align: center;
  font-size: var(--ds-font-size-label);
  color: var(--ds-color-text-grey);
}
</style>
