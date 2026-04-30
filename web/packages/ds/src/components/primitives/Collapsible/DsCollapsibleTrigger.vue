<script setup lang="ts">
/**
 * CollapsibleTrigger — the toggle control. Use `as-child` to delegate to a
 * styled button (e.g. `<DsButton>`).
 */

import { CollapsibleTrigger, type CollapsibleTriggerProps } from 'reka-ui'

const props = defineProps<CollapsibleTriggerProps>()
</script>

<template>
  <CollapsibleTrigger
    v-bind="props"
    class="ds-collapsible__trigger"
    data-test="ds-collapsible-trigger"
  >
    <slot />
  </CollapsibleTrigger>
</template>

<style>
.ds-collapsible__trigger {
  display: inline-flex;
  align-items: center;
  gap: var(--ds-space-sm);
  background: transparent;
  border: 0;
  cursor: pointer;
  font: inherit;
  color: inherit;
}
</style>
