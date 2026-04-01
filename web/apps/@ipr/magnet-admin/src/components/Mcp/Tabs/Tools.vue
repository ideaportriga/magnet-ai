<template lang="pug">
.column.full-height(v-if='data?.length', style='min-height: 0')
  .row.q-mb-12
    .col-auto.center-flex-y
      km-input(placeholder='Search', iconBefore='search', :modelValue='globalFilter', @input='globalFilter = $event', clearable)
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
        km-btn(label='Sync Tools', @click='syncTools')
</template>

<script setup>
import { computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useQuasar } from 'quasar'
import { useLocalDataTable } from '@/composables/useLocalDataTable'
import { nameDescriptionColumn } from '@/utils/columnHelpers'
import { useMcpServerDetailStore } from '@/stores/entityDetailStores'
import { useEntityQueries } from '@/queries/entities'

const router = useRouter()
const route = useRoute()
const mcpStore = useMcpServerDetailStore()
const q = useQuasar()
const queries = useEntityQueries()
const { mutateAsync: updateMcpServer } = queries.mcp_servers.useUpdate()
const { mutateAsync: syncMcpServer } = queries.mcp_servers.useSync()

const data = computed(() => mcpStore.entity?.tools ?? [])

const columns = [
  nameDescriptionColumn('Name'),
]

const { table, globalFilter } = useLocalDataTable(data, columns)

const handleRowClick = (row) => {
  router.push(`${route.path}/tools/${row.name}`)
}

const syncTools = async () => {
  try {
    const mcpServer = mcpStore.entity
    const data = { ...mcpServer }
    delete data.id
    delete data.created_at
    delete data.updated_at
    delete data.created_by
    delete data.updated_by
    await updateMcpServer({ id: mcpServer.id, data })
    mcpStore.setInit()
    await syncMcpServer(mcpServer.id)
    q.notify({
      position: 'top',
      message: 'MCP Tools have been synced.',
      color: 'positive',
      textColor: 'black',
      timeout: 1000,
    })
  } catch (error) {
    q.notify({
      position: 'top',
      message: 'Failed to sync MCP Tools.',
      color: 'negative',
      textColor: 'black',
      timeout: 1000,
    })
  }
}
</script>
