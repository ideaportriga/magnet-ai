<script setup lang="ts">
/**
 * TagsInput — token / chip input. Built on Reka UI's TagsInput.
 */
import type { TagsInputRootEmits, TagsInputRootProps } from 'reka-ui'
import { TagsInputRoot, useForwardPropsEmits } from 'reka-ui'

const props = defineProps<TagsInputRootProps>()
const emits = defineEmits<TagsInputRootEmits>()

const forwarded = useForwardPropsEmits(props, emits)
</script>

<template>
  <TagsInputRoot
    v-slot="slotProps"
    v-bind="forwarded"
    class="ds-tags-input"
    data-test="ds-tags-input"
  >
    <slot v-bind="slotProps" />
  </TagsInputRoot>
</template>

<style>
.ds-tags-input {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--ds-space-xs);
  padding-block: var(--ds-space-2xs);
  padding-inline: var(--ds-space-xs);
  font-size: var(--ds-font-size-label);
  background: var(--ds-color-background);
  color: var(--ds-color-black);
  border: 1px solid var(--ds-color-control-border);
  border-radius: var(--ds-radius-md);
  box-shadow: var(--ds-shadow-sm);
  outline: none;
  transition:
    border-color var(--ds-duration-fast) var(--ds-ease-out),
    box-shadow var(--ds-duration-fast) var(--ds-ease-out);
}
.ds-tags-input:focus-within {
  border-color: var(--ds-color-primary);
  box-shadow: 0 0 0 3px var(--ds-color-primary-transparent);
}
.ds-tags-input[aria-invalid='true'] {
  border-color: var(--ds-color-error);
}
.ds-tags-input[aria-invalid='true']:focus-within {
  box-shadow: 0 0 0 3px var(--ds-color-error-bg);
}
</style>
