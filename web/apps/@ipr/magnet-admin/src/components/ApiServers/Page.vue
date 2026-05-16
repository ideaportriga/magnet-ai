<template>
  <div class="stack full-height km-page" data-gap="0">
    <div class="collection-container mx-auto full-width stack full-height px-md pt-lg" data-gap="0">
      <template v-if="isLoading">
        <div class="flex flex-center full-height">
          <km-loader size="40px" />
        </div>
      </template>
      <template v-else-if="rows.length">
        <div class="flex-1 ba-border border-radius-12 bg-white p-lg stack" data-gap="0" style="min-block-size: 0">
          <div class="cluster mb-md">
            <div class="flex-none center-flex-y">
              <km-input data-test="search-input" :placeholder="m.common_search()" icon-before="search" :model-value="globalFilter" clearable @input="globalFilter = $event" />
            </div>
            <div class="km-space" />
            <div class="flex-none center-flex-y">
              <km-btn v-if="canCreate" class="mr-md" data-test="new-btn" :label="m.common_new()" @click="showNewDialog = true" />
            </div>
          </div>
          <div class="flex-1" style="min-block-size: 0">
            <km-data-table :table="table" :loading="isLoading" :fetching="isFetching" fill-height row-key="system_name" @row-click="openDetails" />
          </div>
        </div>
      </template>
      <template v-else>
        <div class="cluster" data-justify="center">
          <div class="flex-none p-xl bg-light border-radius-12">
            <div class="cluster mb-md" data-justify="center">
              <km-glyph name="swap" size="48px" tone="brand" />
            </div>
            <div class="km-heading-7 text-black">{{ m.apiServers_noApiServersYet() }}</div>
            <div class="km-description text-black">{{ m.apiServers_useApiServerManual() }}</div>
            <div class="cluster mt-lg" data-justify="center">
              <km-btn v-if="canCreate" data-test="new-btn" :label="m.common_addApiServer()" @click="showNewDialog = true" />
            </div>
          </div>
        </div>
      </template>
    </div>
    <api-servers-new-server :show-new-dialog="showNewDialog" @cancel="showNewDialog = false" />
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { usePermissions } from '@shared'
import { useDataTable } from '@/composables/useDataTable'
import { nameDescriptionColumn, chipCopyColumn, dateColumn } from '@/utils/columnHelpers'
import { m } from '@/paraglide/messages'
import type { ApiServer } from '@/types'

const router = useRouter()
const showNewDialog = ref(false)

const { can } = usePermissions()
const canCreate = computed(() => can('write:api_servers'))

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
