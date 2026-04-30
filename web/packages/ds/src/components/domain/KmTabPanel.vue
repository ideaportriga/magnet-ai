<script setup lang="ts">
/**
 * `<km-tab-panel name="…">` — single panel inside `<km-tab-panels>`.
 * Visible only when its `name` matches the parent's `modelValue`.
 *
 * Public API preserved: `name` prop, default slot.
 */
import { computed, inject } from 'vue'
import { KM_TAB_PANELS_ACTIVE_KEY } from './kmTabPanels.tokens'

const props = defineProps<{
  name: string
}>()

defineSlots<{
  default?: () => unknown
}>()

const active = inject(KM_TAB_PANELS_ACTIVE_KEY, computed(() => undefined))
const visible = computed(() => active?.value === props.name)
</script>

<template>
  <div
    v-show="visible"
    class="km-tab-panel"
    :data-name="name"
    :data-test="`km-tab-panel-${name}`"
    role="tabpanel"
  >
    <slot />
  </div>
</template>

<style>
.km-tab-panel {
  inline-size: 100%;
}
</style>
