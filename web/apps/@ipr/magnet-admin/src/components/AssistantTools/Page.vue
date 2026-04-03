<template lang="pug">
.column.no-wrap.full-height
  .collection-container.q-mx-auto.full-width.column.full-height.q-px-md.q-pt-16
    q-tabs.bb-border.full-width.q-mb-lg(
      v-model='tab',
      narrow-indicator,
      dense,
      align='left',
      active-color='primary',
      indicator-color='primary',
      active-bg-color='white',
      no-caps,
      content-class='km-tabs'
    )
      template(v-for='t in tabs')
        q-tab(:name='t.name', :label='t.label')
    .col.ba-border.border-radius-12.bg-white.q-pa-16.column(style='min-height: 0')
      .row.q-mb-12
        .col-auto.center-flex-y
          km-input(:placeholder='m.common_search()', iconBefore='search', :modelValue='globalFilter', @input='globalFilter = $event', clearable)
        q-space
        .col-auto.center-flex-y
          km-btn.q-mr-12(:label='m.common_new()', @click='showNewDialog = true')
      .col(style='min-height: 0')
        km-data-table(
          :table='table',
          :loading='isLoading', :fetching='isFetching',
          fill-height,
          row-key='id',
          @row-click='openDetails'
        )
    assistant-tools-create-new(:showNewDialog='showNewDialog && tab == "api"', @cancel='showNewDialog = false')
    assistant-tools-create-new-rag(:showNewDialog='showNewDialog && tab == "rag"', @cancel='showNewDialog = false')
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useDataTable } from '@/composables/useDataTable'
import { nameDescriptionColumn, chipCopyColumn, dateColumn } from '@/utils/columnHelpers'
import { m } from '@/paraglide/messages'
import type { AssistantTool } from '@/types'

const router = useRouter()
const showNewDialog = ref(false)
const tab = ref('api')
const tabs = [
  { name: 'api', label: 'API' },
  { name: 'rag', label: 'RAG' },
]

const columns = [
  nameDescriptionColumn<AssistantTool>(m.common_name()),
  chipCopyColumn<AssistantTool>(m.common_systemName()),
  dateColumn<AssistantTool>('created_at', m.common_created()),
  dateColumn<AssistantTool>('updated_at', m.common_lastUpdated()),
]

const extraParams = computed(() => ({ type: tab.value }))

const { table, rows, isLoading, isFetching, globalFilter } = useDataTable<AssistantTool>('assistant_tools', columns, {
  defaultSort: [{ id: 'updated_at', desc: true }],
  extraParams,
})

const openDetails = async (row: AssistantTool) => {
  await router.push(`/assistant-tools/${row.id}`)
}
</script>

<style lang="stylus">
.km-input:not(.q-field--readonly) .q-field__control::before
  background: var(--q-white) !important;
</style>
