<template lang="pug">
.full-width
  div(style='width: 300px')
    km-input(:placeholder='m.common_search()', iconBefore='search', :modelValue='globalFilter', @input='globalFilter = $event', clearable)
  .km-title.q-pl-16.q-pb-8.q-pt-lg.text-text-grey {{ m.common_inputs() }}
  km-data-table(:table='table', row-key='name', :activeRowId='props.selectedRow?.name', @row-click='select')
</template>
<script setup>
import { computed, watch } from 'vue'
import { m } from '@/paraglide/messages'
import { useEntityQueries } from '@/queries/entities'
import { useAgentEntityDetail } from '@/composables/useAgentEntityDetail'
import { useLocalDataTable } from '@/composables/useLocalDataTable'
import { textColumn } from '@/utils/columnHelpers'

const props = defineProps({
  apiTool: {
    type: Object,
    required: true,
  },
  selectedRow: {
    type: Object,
    required: false,
  },
})

const emit = defineEmits(['select'])

const queries = useEntityQueries()
const { data: apiServersData } = queries.api_servers.useList()
const apiServers = computed(() => apiServersData.value?.items ?? [])
const { data: mcpData } = queries.mcp_servers.useList()
const mcpItems = computed(() => mcpData.value?.items ?? [])

const { activeVariant, activeTopic: activeTopicRef } = useAgentEntityDetail()

const activeTopic = computed({
  get() {
    return activeTopicRef.value
  },
  set(value) {
    activeTopicRef.value = value
  },
})

const topic = computed(() => {
  return (activeVariant.value?.value?.topics || [])?.find(
    (topic) => topic?.system_name === activeTopic.value?.topic
  )
})

const action = computed(() => {
  return topic.value?.actions?.find(
    (action) => action?.system_name == activeTopic.value?.action
  )
})

const tool_object = computed(() => {
  if (action.value?.type === 'mcp_tool') {
    const server = mcpItems.value.find((item) => item.system_name === action.value?.tool_provider)
    return server?.tools?.find((tool) => tool.name === action.value?.tool_system_name)
  }
  const server = apiServers.value.find((item) => item.system_name === action.value?.tool_provider)
  return server?.tools?.find((item) => item.system_name === action.value?.tool_system_name)
})

const toolActiveVariant = computed(() => {
  if (action.value?.type === 'mcp_tool') return tool_object.value
  if (action.value?.type === 'api') return tool_object.value
  return tool_object.value?.variants?.find(
    (variant) => variant.variant === tool_object.value?.active_variant
  )
})

const parameters = computed(() => {
  if (action.value?.type === 'mcp_tool') return tool_object.value?.inputSchema?.properties
  if (action.value?.type === 'api') return tool_object.value?.parameters?.input?.properties
  return toolActiveVariant.value?.value?.parameters.input.properties
})

const formatApiRows = (key) => {
  const properties = parameters.value[key].properties || {}
  return Object.keys(properties).map((property) => {
    return {
      description: '-',
      ...properties[property],
      name: property,
      in: key,
    }
  })
}

const formatMCPRows = (key) => {
  const properties = parameters.value[key] || {}
  return {
    description: '-',
    ...properties,
    name: key,
  }
}

const rows = computed(() => {
  if (!parameters.value) return []
  const result = []
  Object.keys(parameters.value).forEach((key) => {
    if (action.value?.type === 'mcp_tool') {
      result.push(formatMCPRows(key))
    } else {
      result.push(...formatApiRows(key))
    }
  })
  return result
})

const isApiAction = computed(() => action.value?.type === 'api')

const columns = [
  textColumn('name', m.common_name()),
  textColumn('description', m.common_description()),
]

const columnsWithIn = [
  ...columns,
  textColumn('in', 'In'),
]

// Use all columns including 'in'; for MCP tools it will show '-' (default)
const { table, globalFilter, columnVisibility } = useLocalDataTable(rows, columnsWithIn, {
  defaultColumnVisibility: {},
})

// Toggle 'in' column visibility based on action type
watch(isApiAction, (val) => {
  columnVisibility.value = val ? {} : { in: false }
}, { immediate: true })

watch(rows, (newVal) => {
  select(newVal[0])
})

const select = (row) => {
  emit('select', row)
}
</script>
