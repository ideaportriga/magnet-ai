<script setup lang="ts">
/**
 * TagsInputItemDelete — small "x" inside a tag chip that removes that tag.
 */
import type { TagsInputItemDeleteProps } from 'reka-ui'
import { TagsInputItemDelete, useForwardProps } from 'reka-ui'

const props = defineProps<TagsInputItemDeleteProps>()
const forwarded = useForwardProps(props)
</script>

<template>
  <TagsInputItemDelete
    v-bind="forwarded"
    class="ds-tags-input__item-delete"
    data-test="ds-tags-input-item-delete"
  >
    <slot>
      <svg width="14" height="14" viewBox="0 0 14 14" aria-hidden="true">
        <path
          d="M2 2 L12 12 M12 2 L2 12"
          stroke="currentColor"
          stroke-width="1.6"
          stroke-linecap="round"
        />
      </svg>
    </slot>
  </TagsInputItemDelete>
</template>

<style>
.ds-tags-input__item-delete {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  inline-size: 16px;
  block-size: 16px;
  margin-inline-end: var(--ds-space-2xs);
  background: transparent;
  color: currentColor;
  border: 0;
  border-radius: var(--ds-radius-sm);
  cursor: pointer;
  opacity: 0.7;
  transition: opacity var(--ds-duration-fast) var(--ds-ease-out);
}
.ds-tags-input__item-delete:hover { opacity: 1; }
</style>
