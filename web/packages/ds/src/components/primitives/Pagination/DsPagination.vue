<script setup lang="ts">
/**
 * Pagination — accessible pager built on Reka UI's Pagination primitive.
 *
 *   <DsPagination v-model:page="page" :total="total" :items-per-page="20">
 *     <DsPaginationContent>
 *       <DsPaginationFirst />
 *       <DsPaginationPrevious />
 *       <DsPaginationList v-slot="{ items }">
 *         <template v-for="(item, i) in items" :key="i">
 *           <DsPaginationItem v-if="item.type === 'page'" :value="item.value">
 *             {{ item.value }}
 *           </DsPaginationItem>
 *           <DsPaginationEllipsis v-else :index="i" />
 *         </template>
 *       </DsPaginationList>
 *       <DsPaginationNext />
 *       <DsPaginationLast />
 *     </DsPaginationContent>
 *   </DsPagination>
 */

import {
  PaginationRoot,
  type PaginationRootEmits,
  type PaginationRootProps,
  useForwardPropsEmits,
} from 'reka-ui'

const props = defineProps<PaginationRootProps>()
const emits = defineEmits<PaginationRootEmits>()

const forwarded = useForwardPropsEmits(props, emits)
</script>

<template>
  <PaginationRoot
    v-slot="slotProps"
    v-bind="forwarded"
    class="ds-pagination"
    data-test="ds-pagination"
  >
    <slot v-bind="slotProps" />
  </PaginationRoot>
</template>

<style>
.ds-pagination {
  display: flex;
  inline-size: 100%;
  margin-inline: auto;
  justify-content: center;
}
</style>
