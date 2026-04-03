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
import { useRoute } from 'vue-router'
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

const route = useRoute()
const queries = useEntityQueries()
const { data: apiServersData } = queries.api_servers.useList()
const apiServers = computed(() => apiServersData.value?.items ?? [])

const { activeVariant: agentActiveVariant } = useAgentEntityDetail()

const routeParams = computed(() => route.params)

const topic = computed(() => {
  return (agentActiveVariant.value?.value?.topics || [])?.find(
    (topic) => topic?.system_name === routeParams.value?.topicId
  )
})

const action = computed(() => {
  return topic.value?.actions?.find((action) => action?.system_name == routeParams.value?.actionId)
})

const tool_object = computed(() => {
  const server = apiServers.value.find((item) => item.system_name === action.value?.tool_provider)
  return server?.tools?.find((item) => item.system_name === action.value?.tool_system_name)
})

const toolActiveVariant = computed(() => {
  return tool_object.value?.variants?.find(
    (variant) => variant.variant === tool_object.value?.active_variant
  )
})

const parameters = computed(() => {
  if (action.value?.type === 'api') return tool_object.value?.parameters?.input?.properties
  return toolActiveVariant.value?.value?.parameters.input.properties
})

const rows = computed(() => {
  if (!parameters.value) return []
  const result = []
  Object.keys(parameters.value).forEach((key) => {
    const properties = parameters.value[key].properties || {}
    Object.keys(properties).forEach((property) => {
      result.push({
        description: '-',
        ...properties[property],
        name: property,
        in: key,
      })
    })
  })
  return result
})

const columns = [
  textColumn('name', m.common_name()),
  textColumn('description', m.common_description()),
  textColumn('in', 'In'),
]

const { table, globalFilter } = useLocalDataTable(rows, columns)

watch(rows, (newVal) => {
  select(newVal[0])
})

const select = (row) => {
  emit('select', row)
}
</script>
