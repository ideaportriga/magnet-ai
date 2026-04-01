<template lang="pug">
.column.no-wrap.full-height
  .collection-container.q-mx-auto.full-width.column.full-height.q-px-md.q-pt-16
    template(v-if='isLoading')
      .flex.flex-center.full-height
        q-spinner(size='40px', color='primary')
    template(v-else-if='rows.length')
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
            row-key='system_name',
            @row-click='openDetails'
          )
    template(v-else)
      .row.items-center.justify-center
        .col-auto.q-pa-xl.bg-light.border-radius-12
          .row.items-center.justify-center.q-mb-md
            q-icon(name='fa fa-arrow-right-arrow-left', size='48px', color='primary')
          .km-heading-7.text-black You have no MCP servers yet
          .km-description.text-black Add a new MCP server to get started
          .row.items-center.justify-center.q-mt-lg
            km-btn(label='Add MCP Server', @click='showNewDialog = true')
  mcp-new-server(:showNewDialog='showNewDialog', @cancel='showNewDialog = false')
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useDataTable } from '@/composables/useDataTable'
import { nameDescriptionColumn, chipCopyColumn, dateColumn } from '@/utils/columnHelpers'
import type { McpServer } from '@/types'

const router = useRouter()
const showNewDialog = ref(false)

const columns = [
  nameDescriptionColumn<McpServer>('Name'),
  chipCopyColumn<McpServer>('System name'),
  dateColumn<McpServer>('last_synced_at', 'Last Synced'),
]

const { table, rows, isLoading, globalFilter } = useDataTable<McpServer>('mcp_servers', columns, {
  defaultSort: [{ id: 'last_synced_at', desc: true }],
  manualPagination: false,
  manualSorting: false,
  manualFiltering: false,
})

const openDetails = async (row: McpServer) => {
  await router.push(`/mcp/${row.id}`)
}
</script>
