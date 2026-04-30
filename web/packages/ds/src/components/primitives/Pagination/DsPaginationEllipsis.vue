<script setup lang="ts">
/**
 * PaginationEllipsis — shows when pages are skipped (e.g. 1 … 5 6 7 … 20).
 */

import { PaginationEllipsis, type PaginationEllipsisProps } from 'reka-ui'

const props = defineProps<PaginationEllipsisProps>()
</script>

<template>
  <PaginationEllipsis
    v-bind="props"
    class="ds-pagination__ellipsis"
    data-test="ds-pagination-ellipsis"
  >
    <slot>
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" aria-hidden="true">
        <circle cx="5" cy="12" r="1.5" fill="currentColor" />
        <circle cx="12" cy="12" r="1.5" fill="currentColor" />
        <circle cx="19" cy="12" r="1.5" fill="currentColor" />
      </svg>
      <span class="ds-pagination__sr">More pages</span>
    </slot>
  </PaginationEllipsis>
</template>

<style>
.ds-pagination__ellipsis {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  inline-size: 36px;
  block-size: 36px;
  color: var(--ds-color-text-grey);
}
.ds-pagination__sr {
  position: absolute;
  inline-size: 1px;
  block-size: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip-path: inset(50%);
  white-space: nowrap;
  border: 0;
}
</style>
