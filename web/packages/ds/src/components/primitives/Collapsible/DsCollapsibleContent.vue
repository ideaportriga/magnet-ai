<script setup lang="ts">
/**
 * CollapsibleContent — animated content region revealed by the trigger.
 * Uses Reka's `--reka-collapsible-content-height` CSS variable for animation.
 */

import { CollapsibleContent, type CollapsibleContentProps } from 'reka-ui'

const props = defineProps<CollapsibleContentProps>()
</script>

<template>
  <CollapsibleContent
    v-bind="props"
    class="ds-collapsible__content"
    data-test="ds-collapsible-content"
  >
    <slot />
  </CollapsibleContent>
</template>

<style>
.ds-collapsible__content {
  overflow: hidden;
}
.ds-collapsible__content[data-state='open'] {
  animation: ds-collapse-down var(--ds-duration-base) var(--ds-ease-out);
}
.ds-collapsible__content[data-state='closed'] {
  animation: ds-collapse-up var(--ds-duration-base) var(--ds-ease-in);
}
</style>
