<script setup lang="ts">
/**
 * PaginationContent — wrapper around the pager controls. Mirrors shadcn's
 * `PaginationContent` and renders a Reka `PaginationList` for accessibility.
 */

import { PaginationList, type PaginationListProps } from 'reka-ui'

const props = defineProps<PaginationListProps>()
</script>

<template>
  <PaginationList
    v-slot="slotProps"
    v-bind="props"
    class="ds-pagination__content"
    data-test="ds-pagination-content"
  >
    <slot v-bind="slotProps" />
  </PaginationList>
</template>

<style>
.ds-pagination__content {
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: var(--ds-space-2xs);
}
</style>
