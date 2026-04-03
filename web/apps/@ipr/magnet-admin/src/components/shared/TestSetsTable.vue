<template lang="pug">
.full-width.q-mb-sm
  km-select(
    height='auto',
    minHeight='36px',
    placeholder='Test Set',
    :options='setItems',
    :modelValue='selectedTestSet',
    @update:modelValue='$emit("update:selectedTestSet", $event)',
    option-value='system_name',
    option-label='name',
    emit-value,
    map-options,
    hasDropdownSearch
  )
template(v-if='selectedTestSet')
  .row.q-mb-sm
    km-input(placeholder='Search', iconBefore='search', :modelValue='globalFilter', @input='globalFilter = $event', clearable)
  .full-width
    km-data-table(
      :table='table',
      row-key='user_input',
      :activeRowId='activeRowInput',
      @row-click='$emit("selectRecord", $event)'
    )
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { m } from '@/paraglide/messages'
import { useEntityQueries } from '@/queries/entities'
import { useLocalDataTable } from '@/composables/useLocalDataTable'
import { textColumn } from '@/utils/columnHelpers'

const props = defineProps<{
  selectedTestSet: string
  activeRowInput?: string
}>()

defineEmits<{
  'update:selectedTestSet': [value: string]
  selectRecord: [row: Record<string, unknown>]
}>()

const queries = useEntityQueries()
const { data: evaluationSetsListData } = queries.evaluation_sets.useList()

const setItems = computed(() => evaluationSetsListData.value?.items ?? [])
const testSetObject = computed(() =>
  setItems.value.find(({ system_name }: any) => system_name === props.selectedTestSet),
)
const testSetItems = computed(() => (testSetObject.value as any)?.items || [])

const columns = [
  textColumn<any>('user_input', 'User Input'),
  textColumn<any>('expected_result', 'Expected Result'),
]

const { table, globalFilter } = useLocalDataTable(testSetItems, columns, {
  defaultPageSize: 10,
})
</script>
