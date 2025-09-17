<template>
  <div class="row">
    <retrieval-metadata-filter-chip
      v-for="filter in filters"
      :key="filter.field"
      :model-value="filter"
      :readonly="readonly"
      @click="emit('click', filter)"
      @remove="emit('remove', filter)"
    />
  </div>
</template>

<script setup lang="ts">
import type { Filter } from '@shared/types'

// Models & Props
const filters = defineModel<Filter[]>({ default: [] })
defineProps<{
  readonly?: boolean
}>()

const emit = defineEmits<{
  (e: 'click', filter: Filter): void
  (e: 'remove', filter: Filter): void
}>()
</script>