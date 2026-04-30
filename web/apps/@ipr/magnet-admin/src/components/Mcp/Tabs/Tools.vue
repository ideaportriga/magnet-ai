<template>
  <div v-if="data?.length" class="stack full-height" data-gap="0" style="min-block-size: 0">
    <div class="cluster mb-md">
      <div class="flex-none center-flex-y">
        <km-input :placeholder="m.common_search()" icon-before="search" :model-value="globalFilter" clearable @input="globalFilter = $event" />
      </div>
    </div>
    <div class="flex-1" style="min-block-size: 0">
      <km-data-table :table="table" fill-height row-key="name" @row-click="handleRowClick" />
    </div>
  </div>
  <template v-else>
    <div class="flex full-width full-height" style="flex-direction: column; justify-content: center; align-items: center">
      <div class="flex-1 p-xl bg-light border-radius-12">
        <div class="cluster mb-md" data-justify="center">
          <km-glyph name="swap" size="48px" tone="brand" />
        </div>
        <div class="km-heading-7 text-black">You have no MCP tools yet</div>
        <div class="km-description text-black">Sync with the MCP Server to load tools</div>
        <div class="cluster mt-lg" data-justify="center">
          <km-btn :label="m.common_syncTools()" @click="syncTools" />
        </div>
      </div>
    </div>
  </template>
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
