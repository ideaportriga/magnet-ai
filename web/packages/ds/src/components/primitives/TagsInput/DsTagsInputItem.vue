<script setup lang="ts">
/**
 * TagsInputItem — a single tag chip in a TagsInput. Wraps text + delete.
 */
import type { TagsInputItemProps } from 'reka-ui'
import { TagsInputItem, useForwardProps } from 'reka-ui'

const props = defineProps<TagsInputItemProps>()
const forwarded = useForwardProps(props)
</script>

<template>
  <TagsInputItem
    v-bind="forwarded"
    class="ds-tags-input__item"
    data-test="ds-tags-input-item"
  >
    <slot />
  </TagsInputItem>
</template>

<style>
.ds-tags-input__item {
  display: inline-flex;
  align-items: center;
  block-size: 22px;
  background: var(--ds-color-secondary-bg);
  color: var(--ds-color-secondary-text);
  border-radius: var(--ds-radius-md);
  transition: box-shadow var(--ds-duration-fast) var(--ds-ease-out);
}
.ds-tags-input__item[data-state='active'] {
  box-shadow: 0 0 0 2px var(--ds-color-background), 0 0 0 4px var(--ds-color-primary);
}
</style>
