<template lang="pug">
.column.full-width
  div
    q-tabs.bb-border.full-width(
      v-model='tab',
      narrow-indicator,
      dense,
      align='left',
      active-color='primary',
      indicator-color='primary',
      active-bg-color='white',
      no-caps,
      content-class='km-tabs'
    )
      template(v-for='t in tabs')
        q-tab(:name='t.name')
          .row.q-px-4(style='height: 24px')
            .col.km-title {{ t.label }}
            .col-auto.q-ml-sm(v-if='getSelectedQtyByType(t.name) > 0')
              km-chip(round, size='24px', :label='getSelectedQtyByType(t.name)', color='primary-light', text-color='primary')

  .row.q-mt-16
    km-input(placeholder='Search', iconBefore='search', v-model='searchString', @input='searchString = $event', clearable)
  .column.no-wrap.q-gap-16.full-height.full-width.q-mb-md.q-mt-16.km-scroll-area-lg(
    style='height: 100% !important',
    :class='{ "overflow-auto": tab == "mcp_tool" || tab == "api" || tab == "knowledge_graph" }'
  )
    .column.full-height.full-width(v-if='tab != "mcp_tool" && tab != "api" && tab != "knowledge_graph"')
      km-data-table.full-height(
        :table='toolTable',
        fill-height,
        row-key='id',
        :activeRowId='selectedRow?.id',
        hide-pagination,
        @row-click='selectRecord'
      )
    .column.full-width(v-else)
      template(v-if='tab == "mcp_tool"')
        agents-select-section(
          v-for='(server, index) in mcp_servers',
          :key='server.id',
          :server='server',
          :selected='selected',
          @select='selectRecord',
          @selectMultiple='selectMultiple',
          :search-string='searchString',
          system-name-key='name',
          type='mcp_tool'
        )
      template(v-if='tab == "api"')
        agents-select-section(
          v-for='(server, index) in api_servers',
          :key='server.id',
          :server='server',
          :selected='selected',
          @select='selectRecord',
          @selectMultiple='selectMultiple',
          :search-string='searchString',
          system-name-key='system_name',
          :search-fields='["name", "description", "system_name"]',
          type='api'
        )
      template(v-if='tab == "knowledge_graph"')
        agents-select-section(
          v-for='(server, index) in knowledge_graphs',
          :key='server.id',
          :server='server',
          :selected='selected',
          @select='selectRecord',
          @selectMultiple='selectMultiple',
          :search-string='searchString',
          system-name-key='system_name',
          :search-fields='["name", "description", "system_name"]',
          type='knowledge_graph'
        )
</template>
<script setup>
import { fetchData } from '@shared'
import { ref, computed, onMounted, markRaw, h } from 'vue'
import { useAppStore } from '@/stores/appStore'
import { agentTopicActionsPopupColumns } from '@/config/agents/topics'
import { useEntityQueries } from '@/queries/entities'
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

const { data: apiServersData } = queries.api_servers.useList()
const api_servers = computed(() => apiServersData.value?.items ?? [])

const { data: ragToolsData } = queries.rag_tools.useList()
const rag_tools = computed(() => ragToolsData.value?.items ?? [])

const { data: promptTemplatesData } = queries.promptTemplates.useList()
const prompt_templates = computed(() => promptTemplatesData.value?.items ?? [])

const { data: mcpServersData } = queries.mcp_servers.useList()
const mcp_servers = computed(() => mcpServersData.value?.items ?? [])

const { data: retrievalData } = queries.retrieval.useList()
const retrieval_tools = computed(() => retrievalData.value?.items ?? [])

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
  { name: 'api', label: 'API Tools' },
  { name: 'mcp_tool', label: 'MCP Tools' },
  { name: 'knowledge_graph', label: 'Knowledge Graph' },
  { name: 'rag', label: 'RAG Tools' },
  { name: 'retrieval', label: 'Retrieval Tools' },
  { name: 'prompt_template', label: 'Prompt Templates' },
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
    header: 'Name & Description',
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
