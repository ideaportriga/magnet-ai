<template lang="pug">
.column.full-height(style='min-height: 0')
  .row.q-mb-12
    .col-auto.center-flex-y
      km-input(placeholder='Search', iconBefore='search', :modelValue='globalFilter', @input='globalFilter = $event', clearable)
    q-space
    .col-auto.center-flex-y
      km-btn.q-mr-12(
        v-if='selectedRows.length > 0',
        icon='delete',
        label='Delete',
        @click='showDeleteDialog = true',
        iconColor='icon',
        hoverColor='primary',
        labelClass='km-title',
        flat,
        iconSize='16px',
        hoverBg='primary-bg'
      )
    .col-auto.center-flex-y
      km-btn.q-mr-12(label='Import', disabled)

    .col-auto.center-flex-y
      km-btn.q-mr-12(label='Add record', @click='openNewDetails')
  .col(style='min-height: 0')
    km-data-table(
      fill-height,
      :table='table',
      row-key='index',
      :activeRowId='selectedRow?.index',
      @row-click='selectRecord'
    )

evaluation-sets-create-new-record(:showNewDialog='showNewDialog', @cancel='showNewDialog = false', @addRecord='addRecord', v-if='showNewDialog')
km-popup-confirm(
  :visible='showDeleteDialog',
  confirmButtonLabel='Delete',
  cancelButtonLabel='Cancel',
  notificationIcon='fas fa-triangle-exclamation',
  @confirm='deleteSelected',
  @cancel='showDeleteDialog = false'
)
  .row.item-center.justify-center.km-heading-7 Delete Test Set Records
  .row.text-center.justify-center {{ `You are going to delete ${selectedRows?.length} selected records. Are you sure?` }}
</template>

<script setup>
import { ref, computed, h, markRaw } from 'vue'
import { useRoute } from 'vue-router'
import { useEntityQueries } from '@/queries/entities'
import { useEntityDetail } from '@/composables/useEntityDetail'
import { useEvaluationSetRecordStore } from '@/stores/entityDetailStores'
import { useLocalDataTable } from '@/composables/useLocalDataTable'
import { selectionColumn, textColumn, componentColumn } from '@/utils/columnHelpers'
import TextWrap from '@/config/evaluation_sets/component/TextWrap.vue'
import RetrievalMetadataFilterChipList from '@ui/components/Retrieval/MetadataFilterChipList.vue'

const emit = defineEmits(['openTest', 'record:update'])

const route = useRoute()
const queries = useEntityQueries()
const { draft, updateField } = useEntityDetail('evaluation_sets')
const evalSetRecordStore = useEvaluationSetRecordStore()
const routeId = computed(() => route.params.id)
const { data: selectedEvaluationSet } = queries.evaluation_sets.useDetail(routeId)

const showNewDialog = ref(false)
const showDeleteDialog = ref(false)

const evaluationSetItems = computed({
  get() {
    return draft.value?.items?.map((item, index) => ({ ...item, index })) || []
  },
  set(value) {
    updateField('items', value)
  },
})

const selectedRow = computed(() => evalSetRecordStore.record)

const data = computed(() => evaluationSetItems.value)

const columns = [
  selectionColumn(),
  ...(selectedEvaluationSet.value?.type === 'rag_tool'
    ? [
        componentColumn('metadata_filter', 'Evaluation metadata filter', markRaw(RetrievalMetadataFilterChipList), {
          accessorKey: 'metadata_filter',
          props: (row) => ({ readonly: true, modelValue: row.metadata_filter }),
        }),
      ]
    : []),
  componentColumn('user_input', 'Evaluation input', markRaw(TextWrap), {
    accessorKey: 'user_input',
    sortable: true,
    props: (row) => ({ name: 'user_input' }),
  }),
  componentColumn('expected_result', 'Expected output', markRaw(TextWrap), {
    accessorKey: 'expected_result',
    sortable: true,
    props: (row) => ({ name: 'expected_result' }),
  }),
]

const { table, globalFilter, selectedRows, clearSelection } = useLocalDataTable(data, columns, {
  enableRowSelection: true,
})

const deleteSelected = () => {
  const indexToDelete = selectedRows.value.map((item) => item.index)
  const value = evaluationSetItems.value.filter((item, index) => !indexToDelete.includes(index))
  updateField('items', value)
  clearSelection()
  showDeleteDialog.value = false
}

const selectRecord = (row) => {
  evalSetRecordStore.setRecord(row)
}

const addRecord = (newRow) => {
  updateField('items', [newRow, ...evaluationSetItems.value])
}

const openNewDetails = () => {
  showNewDialog.value = true
}
</script>
