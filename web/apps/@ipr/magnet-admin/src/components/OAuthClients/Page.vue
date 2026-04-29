<template lang="pug">
.column.no-wrap.full-height
  .collection-container.q-mx-auto.full-width.column.full-height.q-px-md.q-pt-16
    .col.ba-border.border-radius-12.bg-white.q-pa-16.column(style='min-height: 0')
      .row.q-mb-12
        .col-auto.center-flex-y
          km-input(data-test='search-input', placeholder='Search', iconBefore='search', :modelValue='globalFilter', @input='onSearchInput', clearable)
        q-space
        .col-auto.center-flex-y
          km-btn.q-mr-12(data-test='new-btn', label='Register OAuth client', @click='openNew')
      .col(style='min-height: 0')
        km-data-table(
          :table='table',
          :loading='isLoading', :fetching='isFetching',
          fill-height,
          row-key='id',
          @row-click='openDetails'
        )
  o-auth-clients-create-new(v-if='showNewDialog', :showNewDialog='showNewDialog', @cancel='closeNew')
  o-auth-clients-details(:client='selectedClient', @close='closeDetails')
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useDataTable } from '@/composables/useDataTable'
import { textColumn, dateColumn } from '@/utils/columnHelpers'
import type { OAuthClient } from '@/types'

const showNewDialog = ref(false)
const openNew = () => { showNewDialog.value = true }
const closeNew = () => { showNewDialog.value = false }

const selectedClient = ref<OAuthClient | null>(null)
const openDetails = (row: OAuthClient) => { selectedClient.value = row }
const closeDetails = () => { selectedClient.value = null }

const columns = [
  textColumn<OAuthClient>('name', 'Name'),
  textColumn<OAuthClient>('client_id', 'Client ID'),
  textColumn<OAuthClient>('enabled', 'Enabled', {
    format: (val) => (val ? 'Yes' : 'No'),
  }),
  textColumn<OAuthClient>('is_public', 'Public', {
    format: (val) => (val ? 'Yes' : 'No'),
  }),
  textColumn<OAuthClient>('redirect_uris', 'Redirect URIs', {
    format: (val) => (Array.isArray(val) ? val.join(', ') : '-'),
  }),
  dateColumn<OAuthClient>('created_at', 'Created'),
]

const { table, isLoading, isFetching, globalFilter } = useDataTable<OAuthClient>('oauth_clients', columns, {
  defaultSort: [{ id: 'updated_at', desc: true }],
})

const onSearchInput = (val: string) => { globalFilter.value = val }
</script>
