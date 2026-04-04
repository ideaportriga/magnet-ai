<template lang="pug">
.column.full-height(v-if='data?.length', style='min-height: 0')
  .row.q-mb-12
    .col-auto.center-flex-y
      km-input(:placeholder='m.common_search()', iconBefore='search', :modelValue='globalFilter', @input='globalFilter = $event', clearable)
  .col(style='min-height: 0')
    km-data-table(:table='table', fill-height, row-key='name', @row-click='handleRowClick')
template(v-else)
  .column.justify-center.items-center.full-width.full-height
    .col.q-pa-xl.bg-light.border-radius-12
      .row.items-center.justify-center.q-mb-md
        q-icon(name='fa fa-arrow-right-arrow-left', size='48px', color='primary')
      .km-heading-7.text-black You have no MCP tools yet
      .km-description.text-black Sync with the MCP Server to load tools
      .row.items-center.justify-center.q-mt-lg
        km-btn(:label='m.common_syncTools()', @click='syncTools')
</template>

<script setup>
import { computed } from 'vue'
import { m } from '@/paraglide/messages'
import { useRouter, useRoute } from 'vue-router'
import { notify } from '@shared/utils/notify'
import { useLocalDataTable } from '@/composables/useLocalDataTable'
import { nameDescriptionColumn } from '@/utils/columnHelpers'
import { useEntityDetail } from '@/composables/useEntityDetail'
import { useEntityQueries } from '@/queries/entities'

const router = useRouter()
const route = useRoute()
const { draft, save } = useEntityDetail('mcp_servers')

const queries = useEntityQueries()
const { mutateAsync: syncMcpServer } = queries.mcp_servers.useSync()

const data = computed(() => draft.value?.tools ?? [])

const columns = [
  nameDescriptionColumn(m.common_name()),
]

const { table, globalFilter } = useLocalDataTable(data, columns)

const handleRowClick = (row) => {
  router.push(`${route.path}/tools/${row.name}`)
}

const syncTools = async () => {
  try {
    const result = await save()
    if (!result.success) throw result.error || new Error('Failed to save')
    await syncMcpServer(draft.value.id)
    notify.success('MCP Tools have been synced.')
  } catch (error) {
    notify.error('Failed to sync MCP Tools.')
  }
}
</script>
