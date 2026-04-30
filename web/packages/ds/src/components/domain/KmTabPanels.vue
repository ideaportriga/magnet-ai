<script setup lang="ts">
/**
 * `<km-tab-panels v-model="activeTab">…</km-tab-panels>` — panel wrapper
 * paired with `<km-tabs>` (which only renders the trigger strip). Each
 * child must be a `<km-tab-panel name="…">`; this component provides the
 * active panel name to its descendants via `KM_TAB_PANELS_ACTIVE_KEY` so
 * the matching panel can show itself.
 *
 * Public API preserved:
 *   modelValue (v-model), keepAlive, animated.
 */
import { computed, provide } from 'vue'
import { KM_TAB_PANELS_ACTIVE_KEY } from './kmTabPanels.tokens'

const props = withDefaults(
  defineProps<{
    modelValue?: string
    keepAlive?: boolean
    animated?: boolean
  }>(),
  { modelValue: undefined, keepAlive: false, animated: false },
)

defineSlots<{
  default?: () => unknown
}>()

const active = computed(() => props.modelValue)
provide(KM_TAB_PANELS_ACTIVE_KEY, active)
</script>

<template>
  <div
    class="km-tab-panels"
    :data-animated="animated ? 'true' : undefined"
    data-test="km-tab-panels"
  >
    <slot />
  </div>
</template>

<style>
.km-tab-panels {
  inline-size: 100%;
}
.km-tab-panels[data-animated='true'] .km-tab-panel {
  animation: km-tab-panel-in var(--ds-duration-base) var(--ds-ease-out);
}
@keyframes km-tab-panel-in {
  from { opacity: 0; transform: translateY(4px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
