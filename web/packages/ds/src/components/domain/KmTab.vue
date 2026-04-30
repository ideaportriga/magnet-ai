<script setup lang="ts">
/**
 * `<km-tab name="x" label="Y" />` — single trigger registration child for
 * the legacy `<km-tabs>` slot syntax. Mounted as a sibling of `<km-tabs>`'
 * trigger strip, it injects itself via `TabsContextKey` so the parent can
 * include it in the rendered DsTabs items list.
 *
 * Public API preserved (Quasar-style):
 *   name, label, disable, icon — plus the default slot, which legacy code
 *   sometimes uses to render rich label content. When the default slot is
 *   provided we still register the tab via `name` (label falls back to
 *   `name`) — DsTabs renders the registered string label; rich label
 *   markup from the slot is intentionally not surfaced because DsTabs only
 *   accepts plain-text labels.
 */

import { inject, onBeforeUnmount, onMounted, watch } from 'vue'
import { TabsContextKey } from './kmTabsContext'

const props = withDefaults(
  defineProps<{
    name: string
    label?: string
    disable?: boolean
    icon?: string
  }>(),
  {
    label: '',
    disable: false,
  },
)

defineSlots<{
  default?: () => unknown
}>()

const ctx = inject(TabsContextKey, null)

onMounted(() => {
  ctx?.registerTab({
    value: props.name,
    label: props.label || props.name,
    disabled: props.disable,
  })
})

watch(
  () => [props.label, props.disable],
  () => {
    // Re-register on prop change so DsTabs reflects the new label.
    ctx?.unregisterTab(props.name)
    ctx?.registerTab({
      value: props.name,
      label: props.label || props.name,
      disabled: props.disable,
    })
  },
)

onBeforeUnmount(() => {
  ctx?.unregisterTab(props.name)
})
</script>

<template>
  <span
    style="display: none"
    aria-hidden="true"
    :data-test="`km-tab-${name}`"
  >
    <slot />
  </span>
</template>
