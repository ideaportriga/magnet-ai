<script setup lang="ts">
/**
 * CommandList — scrollable region that holds groups, items, separators.
 */
import type { ListboxContentProps } from 'reka-ui'
import { ListboxContent, useForwardProps } from 'reka-ui'

const props = defineProps<ListboxContentProps>()
const forwarded = useForwardProps(props)
</script>

<template>
  <ListboxContent
    v-bind="forwarded"
    class="ds-command__list"
    data-test="ds-command-list"
  >
    <div role="presentation">
      <slot />
    </div>
  </ListboxContent>
</template>

<style>
.ds-command__list {
  max-block-size: 300px;
  scroll-padding-block: var(--ds-space-2xs);
  overflow-inline: hidden;
  overflow-block: auto;
}
</style>
