<template lang="pug">
.column.no-wrap.full-height
  .collection-container.q-mx-auto.full-width.column.full-height.q-px-md.q-pt-16
    .col.ba-border.border-radius-12.bg-white.q-pa-16.column(style='min-height: 0')
      .row.q-mb-12
        .col-auto.center-flex-y
          km-input(placeholder='Search', iconBefore='search', :modelValue='globalFilter', @input='globalFilter = $event', clearable)
        q-space
        .col-auto.center-flex-y
          km-btn.q-mr-12(label='New', @click='showNewDialog = true')
      .col(style='min-height: 0')
        km-data-table(
          :table='table',
          :loading='isLoading',
          fill-height,
          row-key='id',
          @row-click='openDetails'
        )

collections-create-new(v-if='showNewDialog', :showNewDialog='showNewDialog', @cancel='showNewDialog = false')
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useDataTable } from '@/composables/useDataTable'
import { nameDescriptionColumn, chipCopyColumn, dateColumn } from '@/utils/columnHelpers'
import type { Collection } from '@/types'

const router = useRouter()
const showNewDialog = ref(false)

const columns = [
  nameDescriptionColumn<Collection>('Name'),
  chipCopyColumn<Collection>('System name'),
  dateColumn<Collection>('created_at', 'Created'),
  dateColumn<Collection>('updated_at', 'Last Updated'),
]

const { table, isLoading, globalFilter } = useDataTable<Collection>('collections', columns, {
  defaultSort: [{ id: 'updated_at', desc: true }],
  manualPagination: false,
  manualSorting: false,
  manualFiltering: false,
})

const openDetails = async (row: Collection) => {
  await router.push(`/knowledge-sources/${row.id}`)
}
</script>

<style lang="stylus">
.km-input:not(.q-field--readonly) .q-field__control::before
  background: var(--q-white) !important;
</style>
