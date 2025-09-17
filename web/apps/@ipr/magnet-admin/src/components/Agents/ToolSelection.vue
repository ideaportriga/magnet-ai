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
  .column.no-wrap.q-gap-16.full-height.full-width.q-mb-md.q-mt-16(
    style='max-height: calc(100vh - 560px) !important; height: 100% !important',
    :class='{ "overflow-auto": tab == "mcp_tool" || tab == "api" }'
  )
    .column.full-height.full-width(v-if='tab != "mcp_tool" && tab != "api"')
      km-table-new.no-header.full-height(
        style='',
        @selectRow='selectRecord',
        selection='multiple',
        row-key='id',
        :active-record-id='selectedRow?.id',
        :selected='selected',
        @update:selected='emit("update:selected", $event)',
        :columns='columns',
        :rows='rows ?? []',
        binary-state-sort,
        :infinite-scroll='true'
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
</template>
<script setup>
import { useChroma } from '@shared'
import { ref, computed } from 'vue'
import { agentTopicActionsPopupColumns } from '@/config/agents/topics'

const props = defineProps({
  selected: {
    type: Array,
    required: true,
  },
})

const emit = defineEmits(['update:selected'])

const { visibleRows: api_servers } = useChroma('api_servers')
const { visibleRows: rag_tools } = useChroma('rag_tools')
const { visibleRows: prompt_templates } = useChroma('promptTemplates')
const { visibleRows: mcp_servers } = useChroma('mcp_servers')
const { visibleRows: retrieval_tools } = useChroma('retrieval')

const tab = ref('api')
const tabs = ref([
  { name: 'api', label: 'API Tools' },
  { name: 'mcp_tool', label: 'MCP Tools' },
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
const columns = computed(() => {
  return Object.values(agentTopicActionsPopupColumns)
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
  console.log('row', row.id)
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
  console.log('rows', rows)
  const newRows = [...props.selected]
  rows.forEach((row) => {
    const index = newRows.findIndex((item) => item?.id === row?.id)
    if (index === -1) {
      newRows.push(row)
    } else {
      newRows.splice(index, 1)
    }
  })
  console.log('newRows', newRows)
  emit('update:selected', newRows)
}

const selectedRow = ref(null)
</script>
