<script setup lang="ts">
/**
 * List of filter chips — thin wrapper.
 */

import type { Filter } from '@shared/types'
import RetrievalMetadataFilterChip from './MetadataFilterChip.vue'

const filters = defineModel<Filter[]>({ default: () => [] })
defineProps<{ readonly?: boolean }>()
const emit = defineEmits<{
  click: [filter: Filter]
  remove: [filter: Filter]
}>()
</script>

<template>
  <div class="cluster gap-xs">
    <RetrievalMetadataFilterChip
      v-for="filter in filters"
      :key="filter.field"
      :model-value="filter"
      :readonly="readonly"
      @click="emit('click', filter)"
      @remove="emit('remove', filter)"
    />
  </div>
</template>
