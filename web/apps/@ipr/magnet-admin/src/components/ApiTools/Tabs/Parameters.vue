<template>
  <div class="stack full-height" data-gap="0" style="min-block-size: 0">
    <div style="inline-size: 300px">
      <km-input :placeholder="m.common_search()" icon-before="search" :model-value="globalFilter" clearable @input="globalFilter = $event" />
    </div>
    <div class="km-title pl-lg pb-sm pt-lg text-text-grey">{{ m.common_inputs() }}</div>
    <div class="flex-1" style="min-block-size: 0">
      <km-data-table fill-height :table="table" row-key="name" :active-row-id="selectedRow?.name" @row-click="select" />
    </div>
  </div>
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
