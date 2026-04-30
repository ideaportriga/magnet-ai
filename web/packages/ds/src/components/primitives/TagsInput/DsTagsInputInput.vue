<script setup lang="ts">
/**
 * TagsInputInput — the inline text input where new tags are typed.
 */
import type { TagsInputInputProps } from 'reka-ui'
import { TagsInputInput, useForwardProps } from 'reka-ui'

const props = defineProps<TagsInputInputProps>()
const forwarded = useForwardProps(props)
</script>

<template>
  <TagsInputInput
    v-bind="forwarded"
    class="ds-tags-input__input"
    data-test="ds-tags-input-input"
  />
</template>

<style>
.ds-tags-input__input {
  flex: 1 1 auto;
  min-block-size: 20px;
  padding-inline: var(--ds-space-2xs);
  font-family: var(--ds-font-default);
  font-size: var(--ds-font-size-label);
  color: var(--ds-color-black);
  background: transparent;
  border: 0;
  outline: none;
}
.ds-tags-input__input::placeholder {
  color: var(--ds-color-placeholder);
}
</style>
