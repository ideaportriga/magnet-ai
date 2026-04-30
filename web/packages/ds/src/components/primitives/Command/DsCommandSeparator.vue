<script setup lang="ts">
/**
 * CommandSeparator — thin divider between Command groups / sections.
 */
import type { SeparatorProps } from 'reka-ui'
import { Separator } from 'reka-ui'

const props = defineProps<SeparatorProps>()
</script>

<template>
  <Separator
    v-bind="props"
    class="ds-command__separator"
    data-test="ds-command-separator"
  >
    <slot />
  </Separator>
</template>

<style>
.ds-command__separator {
  block-size: 1px;
  margin-inline: calc(-1 * var(--ds-space-2xs));
  background: var(--ds-color-border);
}
</style>
