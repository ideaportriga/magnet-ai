<script setup lang="ts">
/**
 * TagsInputItemText — visible label inside a tag chip.
 */
import type { TagsInputItemTextProps } from 'reka-ui'
import { TagsInputItemText, useForwardProps } from 'reka-ui'

const props = defineProps<TagsInputItemTextProps>()
const forwarded = useForwardProps(props)
</script>

<template>
  <TagsInputItemText
    v-bind="forwarded"
    class="ds-tags-input__item-text"
    data-test="ds-tags-input-item-text"
  >
    <slot />
  </TagsInputItemText>
</template>

<style>
.ds-tags-input__item-text {
  padding-block: 2px;
  padding-inline: var(--ds-space-xs);
  font-size: var(--ds-font-size-label);
  background: transparent;
  border-radius: var(--ds-radius-sm);
}
</style>
