<script setup lang="ts">
/**
 * PaginationFirst — jump to the first page.
 */

import { reactiveOmit } from '@vueuse/core'
import { PaginationFirst, type PaginationFirstProps, useForwardProps } from 'reka-ui'
import type { DsButtonSize } from '../Button/DsButton.vue'

const props = withDefaults(
  defineProps<
    PaginationFirstProps & {
      size?: DsButtonSize
    }
  >(),
  {
    size: 'md',
  },
)

const delegatedProps = reactiveOmit(props, 'size')
const forwarded = useForwardProps(delegatedProps)
</script>

<template>
  <PaginationFirst
    v-bind="forwarded"
    class="ds-pagination__nav"
    :data-size="size"
    data-test="ds-pagination-first"
  >
    <slot>
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" aria-hidden="true">
        <path
          d="M11 17l-5-5 5-5M18 17l-5-5 5-5"
          stroke="currentColor"
          stroke-width="2"
          stroke-linecap="round"
          stroke-linejoin="round"
        />
      </svg>
      <span class="ds-pagination__nav-label">First</span>
    </slot>
  </PaginationFirst>
</template>

<style>
.ds-pagination__nav {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--ds-space-xs);
  block-size: 36px;
  padding-inline: var(--ds-space-md);
  background: transparent;
  color: var(--ds-color-black);
  border: 1px solid transparent;
  border-radius: var(--ds-radius-md);
  font-family: var(--ds-font-default);
  font-size: var(--ds-font-size-label);
  font-weight: var(--ds-font-weight-medium);
  cursor: pointer;
}
.ds-pagination__nav:hover {
  background: var(--ds-color-control-hover-bg);
}
.ds-pagination__nav:focus-visible {
  outline: 2px solid var(--ds-color-primary);
  outline-offset: 2px;
}
.ds-pagination__nav[data-size='sm'] { block-size: 32px; padding-inline: var(--ds-space-sm); }
.ds-pagination__nav[data-size='lg'] { block-size: 40px; padding-inline: var(--ds-space-lg); }

.ds-pagination__nav > svg {
  inline-size: 16px;
  block-size: 16px;
  flex: none;
}
.ds-pagination__nav-label {
  display: none;
}
@media (min-width: 640px) {
  .ds-pagination__nav-label { display: inline; }
}
</style>
