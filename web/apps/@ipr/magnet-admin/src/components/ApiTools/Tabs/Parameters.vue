<template lang="pug">
.column.full-height(style='min-height: 0')
  div(style='width: 300px')
    km-input(:placeholder='m.common_search()', iconBefore='search', :modelValue='globalFilter', @input='globalFilter = $event', clearable)
  .km-title.q-pl-16.q-pb-8.q-pt-lg.text-text-grey {{ m.common_inputs() }}
  .col(style='min-height: 0')
    km-data-table(fill-height, :table='table', row-key='name', :activeRowId='selectedRow?.name', @row-click='select')
</template>

<script setup>
import { computed, watch } from 'vue'
import { m } from '@/paraglide/messages'
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

const rows = computed(() => {
  const parameters = props.apiTool.parameters?.input?.properties
  if (!parameters) return []
  const result = []
  Object.keys(parameters).forEach((key) => {
    const properties = parameters[key].properties
    if (!properties) return
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
  textColumn('name', m.common_name(), { width: '150px' }),
  textColumn('description', m.common_description(), { width: '400px' }),
  textColumn('in', m.apiTools_in(), { width: '100px' }),
]

const { table, globalFilter } = useLocalDataTable(rows, columns)

const select = (row) => {
  emit('select', row)
}

watch(rows, (newVal) => {
  if (newVal.length && !props.selectedRow) {
    emit('select', newVal[0])
  }
}, { immediate: true })
</script>
