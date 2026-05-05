<template>
  <km-list-page>
    <template #toolbar>
      <km-input
        data-test="search-input"
        placeholder="Search"
        icon-before="search"
        :model-value="globalFilter"
        clearable
        @input="onSearchInput"
      />
      <div class="km-space" />
      <km-btn data-test="new-btn" label="Register OAuth client" @click="showNewDialog = true" />
    </template>

    <km-data-table
      :table="table"
      :loading="isLoading"
      :fetching="isFetching"
      fill-height
      row-key="id"
      @row-click="openDetails"
    />

    <template #overlays>
      <o-auth-clients-create-new v-model="showNewDialog" />
    </template>
  </km-list-page>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useDataTable } from '@/composables/useDataTable'
import { textColumn, dateColumn } from '@/utils/columnHelpers'
import type { OAuthClient } from '@/types'

const router = useRouter()
const showNewDialog = ref(false)

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
const openDetails = (row: OAuthClient) => router.push(`/oauth-clients/${row.id}`)
</script>
