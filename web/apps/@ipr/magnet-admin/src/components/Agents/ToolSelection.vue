<template>
  <div class="stack full-width" data-gap="0">
    <div>
      <km-tabs v-model="tab" class="bb-border full-width" narrow-indicator dense align="left" no-caps content-class="km-tabs">
        <template v-for="t in tabs" :key="t.name">
          <km-tab :name="t.name">
            <div class="cluster px-xs" style="block-size: 24px">
              <div class="flex-1 km-title">{{ t.label }}</div>
              <div v-if="getSelectedQtyByType(t.name) &gt; 0" class="flex-none ml-sm">
                <km-chip tone="brand" round size="24px" :label="getSelectedQtyByType(t.name)" />
              </div>
            </div>
          </km-tab>
        </template>
      </km-tabs>
    </div>
    <div class="cluster mt-lg">
      <km-input v-model="searchString" :placeholder="m.common_search()" icon-before="search" clearable @input="searchString = $event" />
    </div>
    <div class="stack full-height full-width mb-md mt-lg km-scroll-area-lg" data-gap="lg" style="block-size: 100% !important" :class="{ 'overflow-auto': tab == 'mcp_tool' || tab == 'api' || tab == 'knowledge_graph' }">
      <div v-if="tab != 'mcp_tool' && tab != 'api' && tab != 'knowledge_graph'" class="stack full-height full-width" data-gap="0">
        <km-data-table class="full-height" :table="toolTable" fill-height row-key="id" :active-row-id="selectedRow?.id" hide-pagination @row-click="selectRecord" />
      </div>
      <div v-else class="stack full-width" data-gap="0">
        <template v-if="tab == &quot;mcp_tool&quot;">
          <agents-select-section v-for="server in mcp_servers" :key="server.id" :server="server" :selected="selected" :search-string="searchString" system-name-key="name" type="mcp_tool" @select="selectRecord" @select-multiple="selectMultiple" />
        </template>
        <template v-if="tab == &quot;api&quot;">
          <agents-select-section v-for="server in api_servers" :key="server.id" :server="server" :selected="selected" :search-string="searchString" system-name-key="system_name" :search-fields="[&quot;name&quot;, &quot;description&quot;, &quot;system_name&quot;]" type="api" @select="selectRecord" @select-multiple="selectMultiple" />
        </template>
        <template v-if="tab == &quot;knowledge_graph&quot;">
          <agents-select-section v-for="server in knowledge_graphs" :key="server.id" :server="server" :selected="selected" :search-string="searchString" system-name-key="system_name" :search-fields="[&quot;name&quot;, &quot;description&quot;, &quot;system_name&quot;]" type="knowledge_graph" @select="selectRecord" @select-multiple="selectMultiple" />
        </template>
      </div>
    </div>
  </div>
</template>
<script setup>
import { fetchData } from '@shared'
import { ref, computed, onMounted, markRaw, h } from 'vue'
import { m } from '@/paraglide/messages'
import { useAppStore } from '@/stores/appStore'
import { agentTopicActionsPopupColumns } from '@/config/agents/topics'
import { useEntityQueries } from '@/queries/entities'
import { useCatalogOptions } from '@/queries/useCatalogOptions'
import { useLocalDataTable } from '@/composables/useLocalDataTable'
import NameDescription from '@/config/agents/component/NameDescription.vue'

const props = defineProps({
  selected: {
    type: Array,
    required: true,
  },
})

const emit = defineEmits(['update:selected'])

const appStore = useAppStore()
const queries = useEntityQueries()

const { options: api_servers } = useCatalogOptions('api_servers')
const { options: rag_tools } = useCatalogOptions('rag_tools')
const { options: mcp_servers } = useCatalogOptions('mcp_servers')
const { options: retrieval_tools } = useCatalogOptions('retrieval')

const { data: promptTemplatesData } = queries.promptTemplates.useList()
const prompt_templates = computed(() => promptTemplatesData.value?.items ?? [])

const knowledge_graphs = ref([])

const fetchKnowledgeGraphs = async () => {
  try {
    const endpoint = appStore.config.api.aiBridge.urlAdmin
    const response = await fetchData({
      endpoint,
      service: 'knowledge_graphs/agent_tools',
      method: 'GET',
      credentials: 'include',
    })
    if (response.ok) {
      knowledge_graphs.value = await response.json()
    }
  } catch (error) {

  }
}

onMounted(() => {
  fetchKnowledgeGraphs()
})

const tab = ref('api')
const tabs = ref([
  { name: 'api', label: m.agents_apiTools() },
  { name: 'mcp_tool', label: m.agents_mcpTools() },
  { name: 'knowledge_graph', label: m.agents_knowledgeGraph() },
  { name: 'rag', label: m.agents_ragTools() },
  { name: 'retrieval', label: m.agents_retrievalTools() },
  { name: 'prompt_template', label: m.agents_promptTemplates() },
])

const searchString = ref('')

const rows = computed(() => {
  if (tab.value === 'rag') return getList(rag_tools.value, 'rag')
  if (tab.value === 'retrieval') return getList(retrieval_tools.value, 'retrieval')
  if (tab.value === 'prompt_template')
    return getList(
      prompt_templates.value.filter((el) => el?.category === 'prompt_tool'),
      'prompt_template'
    )
  return []
})

// Tool table columns using TanStack column definitions
const toolColumns = [
  {
    id: 'nameDescription',
    accessorKey: 'name',
    header: m.agents_nameAndDescription(),
    cell: ({ row }) => h(markRaw(NameDescription), { row: row.original }),
    enableSorting: true,
    meta: {
      align: 'left',
      width: '100%',
      component: markRaw(NameDescription),
    },
  },
]

const { table: toolTable } = useLocalDataTable(rows, toolColumns, {
  defaultPageSize: 999,
})

const getList = (list, type) => {
  //  filter by searchString by all columns
  return list
    .map((item) => {
      return {
        id: item.id,
        name: item.name,
        description: item.description,
        system_name: item.system_name,
        type,
      }
    })
    .filter((item) => {
      return Object.values(item).some((value) => {
        return value.toString().toLowerCase().includes(searchString.value.toLowerCase())
      })
    })
}

const getSelectedQtyByType = (tab) => {
  return props.selected.filter((item) => item.type === tab).length
}

const selectRecord = (row) => {

  // console.log('props.selected', props.selected)
  const index = props.selected.findIndex((item) => item?.id === row?.id)
  if (index === -1) {
    emit('update:selected', [...props.selected, row])
  } else {
    emit(
      'update:selected',
      props.selected.filter((item) => item?.id !== row?.id)
    )
  }
}

const selectMultiple = (rows) => {

  const newRows = [...props.selected]
  rows.forEach((row) => {
    const index = newRows.findIndex((item) => item?.id === row?.id)
    if (index === -1) {
      newRows.push(row)
    } else {
      newRows.splice(index, 1)
    }
  })

  emit('update:selected', newRows)
}

const selectedRow = ref(null)
</script>
