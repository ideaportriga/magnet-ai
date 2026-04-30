<script setup lang="ts">
/**
 * PaginationItem — single numbered page button. Pass `is-active` to highlight
 * the current page.
 */

import { reactiveOmit } from '@vueuse/core'
import { PaginationListItem, type PaginationListItemProps } from 'reka-ui'
import type { DsButtonSize } from '../Button/DsButton.vue'

const props = withDefaults(
  defineProps<
    PaginationListItemProps & {
      size?: DsButtonSize
      isActive?: boolean
    }
  >(),
  {
    size: 'icon',
  },
)

const delegatedProps = reactiveOmit(props, 'size', 'isActive')
</script>

<template>
  <PaginationListItem
    v-bind="delegatedProps"
    class="ds-pagination__item"
    :data-size="size"
    :data-active="isActive ? '' : null"
    data-test="ds-pagination-item"
  >
    <slot />
  </PaginationListItem>
</template>

<style>
.ds-pagination__item {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  inline-size: 36px;
  block-size: 36px;
  background: transparent;
  color: var(--ds-color-black);
  border: 1px solid transparent;
  border-radius: var(--ds-radius-md);
  font-family: var(--ds-font-default);
  font-size: var(--ds-font-size-label);
  font-weight: var(--ds-font-weight-medium);
  cursor: pointer;
  transition:
    background-color var(--ds-duration-fast) var(--ds-ease-out),
    border-color var(--ds-duration-fast) var(--ds-ease-out);
}
.ds-pagination__item:hover {
  background: var(--ds-color-control-hover-bg);
}
.ds-pagination__item:focus-visible {
  outline: 2px solid var(--ds-color-primary);
  outline-offset: 2px;
}
.ds-pagination__item[data-active] {
  border-color: var(--ds-color-border);
  background: var(--ds-color-control-bg);
}

.ds-pagination__item[data-size='sm'] {
  inline-size: 32px;
  block-size: 32px;
}
.ds-pagination__item[data-size='lg'] {
  inline-size: 40px;
  block-size: 40px;
}
</style>
