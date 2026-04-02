<template lang="pug">
.column.full-height(style='min-height: 0')
  .row.q-mb-12
    .col-auto.center-flex-y
      km-input(placeholder='Search', iconBefore='search', :modelValue='globalFilter', @input='globalFilter = $event', clearable)
  .col(style='min-height: 0')
    km-data-table(
      fill-height,
      :table='table',
      row-key='id',
      :activeRowId='selectedRow?.id',
      @row-click='selectRecord'
    )
</template>

<script setup>
import { ref, computed, onMounted, markRaw } from 'vue'
import { useEvaluationStore } from '@/stores/evaluationStore'
import { useLocalDataTable } from '@/composables/useLocalDataTable'
import { selectionColumn, textColumn, componentColumn } from '@/utils/columnHelpers'
import TextWrap from '@/config/evaluation_jobs/component/TextWrap.vue'

const emit = defineEmits(['openTest'])

const evalStore = useEvaluationStore()

const selectedRow = computed(() => evalStore.evaluationJobRecord)

const evaluationSetItems = computed(() => evalStore.evaluation?.results || [])

const data = computed(() => evaluationSetItems.value)

const columns = [
  selectionColumn(),
  textColumn('iteration', 'Iteration'),
  componentColumn('user_message', 'Evaluation input', markRaw(TextWrap), {
    accessorKey: 'user_message',
    sortable: true,
    props: (row) => ({ name: 'user_message' }),
  }),
  componentColumn('generated_output', 'Generated output', markRaw(TextWrap), {
    accessorKey: 'generated_output',
    sortable: true,
    props: (row) => ({ name: 'generated_output' }),
  }),
  componentColumn('expected_output', 'Expected output', markRaw(TextWrap), {
    accessorKey: 'expected_output',
    sortable: true,
    props: (row) => ({ name: 'expected_output' }),
  }),
  textColumn('score', 'Score'),
]

const { table, globalFilter, selectedRows, clearSelection } = useLocalDataTable(data, columns, {
  enableRowSelection: true,
  defaultPageSize: 5,
  defaultSort: [{ id: 'user_message', desc: false }],
})

onMounted(() => {
  if (selectedRow.value) {
    // Pre-select the current row
  }
})

const selectRecord = (row) => {
  clearSelection()
  evalStore.evaluationJobRecord = row
}
</script>
