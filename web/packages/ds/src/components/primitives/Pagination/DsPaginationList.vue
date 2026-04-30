<script setup lang="ts">
/**
 * PaginationList — alias for the Reka pagination list primitive. Useful when
 * you want to render numeric items separately from the prev/next controls.
 */

import { PaginationList, type PaginationListProps } from 'reka-ui'

const props = defineProps<PaginationListProps>()
</script>

<template>
  <PaginationList
    v-slot="slotProps"
    v-bind="props"
    class="ds-pagination__list"
    data-test="ds-pagination-list"
  >
    <slot v-bind="slotProps" />
  </PaginationList>
</template>

<style>
.ds-pagination__list {
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: var(--ds-space-2xs);
}
</style>
