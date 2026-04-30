<template>
  <km-inner-loading :showing="!tool" />
  <layouts-details-layout v-if="tool">
    <template #header>
      <div class="flex-1">
        <div class="cluster">
          <div class="km-heading-4 full-width text-black">{{ tool.name }}</div>
        </div>
        <div class="cluster mt-md">
          <div class="km-description text-black full-width">{{ tool.description }}</div>
        </div>
      </div>
    </template>
    <template #content>
      <km-tabs v-model="tab" class="bb-border full-width" narrow-indicator dense align="left" no-caps content-class="km-tabs">
        <template v-for="t in tabs" :key="t">
          <km-tab :name="t.name" :label="t.label" />
        </template>
      </km-tabs>
      <div class="stack overflow-auto pt-lg pb-lg" data-gap="lg">
        <template v-if="tab == &quot;parameters&quot;">
          <div class="cluster">
            <km-data-table :table="table" row-key="name" :active-row-id="selectedRow?.name" @row-click="handleRowClick" />
          </div>
        </template>
        <template v-if="tab == &quot;definition&quot;">
          <km-input class="full-width" rows="18" border-radius="8px" height="36px" type="textarea" :model-value="JSON.stringify(tool, null, 2)" readonly />
        </template>
      </div>
    </template>
    <template #drawer>
      <mcp-tool-drawer ref="drawer" :selected-row="selectedRow" />
    </template>
  </layouts-details-layout>
</template>
<script setup>
import { m } from '@/paraglide/messages'
import { ref, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useEntityDetail } from '@/composables/useEntityDetail'
import { useLocalDataTable } from '@/composables/useLocalDataTable'
import { textColumn } from '@/utils/columnHelpers'

const { draft } = useEntityDetail('mcp_servers')
const route = useRoute()
const router = useRouter()

const tab = ref('parameters')
const tabs = ref([
  {
    name: 'parameters',
    label: m.mcp_parameters(),
  },
  {
    name: 'definition',
    label: m.mcp_toolDefinition(),
  },
])

const drawer = ref(null)

const tool = computed(() => {
  return draft.value?.tools?.find((t) => t.name === route.params.name)
})

const rows = computed(() => {
  if (!tool.value?.inputSchema?.properties) return []
  return Object.keys(tool.value.inputSchema.properties).map((key) => {
    return {
      name: key,
      description: tool.value.inputSchema.properties[key].description,
    }
  })
})

const columns = [
  textColumn('name', m.common_name()),
  textColumn('description', m.common_description()),
]

const { table } = useLocalDataTable(rows, columns)

const selectedRow = ref(null)

const handleRowClick = (row) => {
  drawer.value?.setTab('details')
  selectedRow.value = {
    name: row.name,
    ...tool.value.inputSchema.properties[row.name],
  }
}

const navigate = (path) => {
  router.push(path)
}

watch(tab, (newVal) => {
  drawer.value?.regulateTabs(newVal)
})
watch(
  () => tool.value,
  (newVal) => {
    if (!newVal) return
    const key = Object.keys(newVal.inputSchema.properties)[0]
    selectedRow.value = {
      name: key,
      ...newVal.inputSchema.properties[key],
    }
  },
  { immediate: true, deep: true }
)
</script>
