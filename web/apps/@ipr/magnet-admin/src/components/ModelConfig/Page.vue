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
          km-input(data-test='search-input', :placeholder='m.common_search()', iconBefore='search', :modelValue='globalFilter', @input='globalFilter = $event', clearable)
        q-space
        .col-auto.center-flex-y
          km-btn.q-mr-12(data-test='new-btn', :label='m.common_new()', @click='showNewDialog = true')
      .col(style='min-height: 0')
        km-data-table(
          :table='table',
          :loading='isLoading', :fetching='isFetching',
          fill-height,
          row-key='id',
          @row-click='openDetails'
        )
    model-config-create-new(:showNewDialog='showNewDialog', @cancel='showNewDialog = false', :type='tab', v-if='showNewDialog')
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useDataTable } from '@/composables/useDataTable'
import { textColumn, componentColumn, dateColumn } from '@/utils/columnHelpers'
import { m } from '@/paraglide/messages'
import type { Model } from '@/types'
import Check from '@/config/model/component/Check.vue'
import Features from '@/config/model/component/Features.vue'

const router = useRouter()
const showNewDialog = ref(false)
const tab = ref('prompts')
const tabs = [
  { name: 'prompts', label: 'Chat Completion Models' },
  { name: 'embeddings', label: 'Vector Embedding Models' },
  { name: 're-ranking', label: 'Reranking Models' },
]

const allColumns = [
  textColumn<Model>('display_name', 'Display name'),
  textColumn<Model>('model', m.common_name(), { sortable: true }),
  componentColumn<Model>('features', 'Features', Features, {
    props: (row) => ({ name: 'features' }),
  }),
  componentColumn<Model>('is_default', 'Default', Check, {
    accessorKey: 'is_default',
    sortable: true,
    align: 'center',
    props: (row) => ({ name: 'is_default' }),
  }),
  dateColumn<Model>('created_at', m.common_created()),
  dateColumn<Model>('updated_at', m.common_lastUpdated()),
]

const extraParams = computed(() => ({ type: tab.value }))

const { table, rows, isLoading, isFetching, globalFilter } = useDataTable<Model>('model', allColumns, {
  defaultSort: [{ id: 'updated_at', desc: true }],
  extraParams,
  dataFilter: (items: Model[]) => {
    // Pin is_default rows to the top
    return [...items].sort((a, b) => {
      if (a.is_default && !b.is_default) return -1
      if (!a.is_default && b.is_default) return 1
      return 0
    })
  },
})

const openDetails = async (row: Model) => {
  await router.push(`/model/${row.id}`)
}
</script>

<style lang="stylus">
.km-input:not(.q-field--readonly) .q-field__control::before
  background: var(--q-white) !important;
</style>
