<script setup lang="ts">
/**
 * HoverCardTrigger — element that opens the hover card on pointer/focus.
 */

import { HoverCardTrigger, type HoverCardTriggerProps } from 'reka-ui'

const props = defineProps<HoverCardTriggerProps>()
</script>

<template>
  <HoverCardTrigger
    v-bind="props"
    class="ds-hover-card__trigger"
    data-test="ds-hover-card-trigger"
  >
    <slot />
  </HoverCardTrigger>
</template>

<style>
.ds-hover-card__trigger {
  display: inline-flex;
  align-items: center;
}
</style>
