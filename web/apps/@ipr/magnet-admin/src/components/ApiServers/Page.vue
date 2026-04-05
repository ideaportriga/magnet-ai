<template lang="pug">
.column.no-wrap.full-height.q-page
  .collection-container.q-mx-auto.full-width.column.full-height.q-px-md.q-pt-16
    template(v-if='isLoading')
      .flex.flex-center.full-height
        q-spinner(size='40px', color='primary')
    template(v-else-if='rows.length')
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
            row-key='system_name',
            @row-click='openDetails'
          )
    template(v-else)
      .row.items-center.justify-center
        .col-auto.q-pa-xl.bg-light.border-radius-12
          .row.items-center.justify-center.q-mb-md
            q-icon(name='fa fa-arrow-right-arrow-left', size='48px', color='primary')
          .km-heading-7.text-black {{ m.apiServers_noApiServersYet() }}
          .km-description.text-black {{ m.apiServers_useApiServerManual() }}
          .row.items-center.justify-center.q-mt-lg
            km-btn(:label='m.common_addApiServer()', @click='showNewDialog = true')
  api-servers-new-server(:showNewDialog='showNewDialog', @cancel='showNewDialog = false')
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useDataTable } from '@/composables/useDataTable'
import { nameDescriptionColumn, chipCopyColumn, dateColumn } from '@/utils/columnHelpers'
import { m } from '@/paraglide/messages'
import type { ApiServer } from '@/types'

const router = useRouter()
const showNewDialog = ref(false)

const columns = [
  nameDescriptionColumn<ApiServer>(m.common_name()),
  chipCopyColumn<ApiServer>(m.common_systemName()),
  dateColumn<ApiServer>('created_at', m.common_created()),
  dateColumn<ApiServer>('updated_at', m.common_lastUpdated()),
]

const { table, rows, isLoading, isFetching, globalFilter } = useDataTable<ApiServer>('api_servers', columns, {
  defaultSort: [{ id: 'updated_at', desc: true }],
})

const openDetails = async (row: ApiServer) => {
  await router.push(`/api-servers/${row.id}`)
}
</script>
