<template>
  <div class="stack full-height" data-gap="0" style="min-block-size: 0">
    <div class="cluster mb-md">
      <div class="flex-none center-flex-y">
        <km-input :placeholder="m.common_search()" icon-before="search" :model-value="globalFilter" clearable @input="globalFilter = $event" />
      </div>
      <div class="km-space" />
      <div class="flex-none center-flex-y">
        <km-btn v-if="selectedRows.length &gt; 0" class="mr-md" icon="delete" :label="m.common_delete()" interaction-tone="brand" label-class="km-title" flat icon-size="16px" @click="showDeleteDialog = true" />
      </div>
      <div class="flex-none center-flex-y">
        <km-btn class="mr-md" :label="m.common_import()" disabled />
      </div>
      <div class="flex-none center-flex-y">
        <km-btn class="mr-md" :label="m.common_addRecord()" @click="openNewDetails" />
      </div>
    </div>
    <div class="flex-1" style="min-block-size: 0">
      <km-data-table fill-height :table="table" row-key="index" :active-row-id="selectedRow?.index" @row-click="selectRecord" />
    </div>
  </div>
  <evaluation-sets-create-new-record v-if="showNewDialog" :show-new-dialog="showNewDialog" @cancel="showNewDialog = false" @add-record="addRecord" />
  <km-popup-confirm :visible="showDeleteDialog" :confirm-button-label="m.common_delete()" :cancel-button-label="m.common_cancel()" notification-icon="warning" @confirm="deleteSelected" @cancel="showDeleteDialog = false">
    <div class="cluster km-heading-7" data-justify="center">{{ m.deleteConfirm_deleteEntity({ entity: m.common_testSetItems() }) }}</div>
    <div class="cluster text-center" data-justify="center">{{ m.agents_deleteConfirmMessage({ count: selectedRows?.length ?? 0 }) }}</div>
  </km-popup-confirm>
</template>

<script setup>
import { ref, computed, h, markRaw } from 'vue'
import { m } from '@/paraglide/messages'
import { useRoute } from 'vue-router'
import { useEntityQueries } from '@/queries/entities'
import { useEntityDetail } from '@/composables/useEntityDetail'
import { useEvaluationSetRecordStore } from '@/stores/entityDetailStores'
import { useLocalDataTable } from '@/composables/useLocalDataTable'
import { selectionColumn, textColumn, componentColumn } from '@/utils/columnHelpers'
import TextWrap from '@/config/evaluation_sets/component/TextWrap.vue'
import RetrievalMetadataFilterChipList from '@/components/Retrieval/MetadataFilterChipList.vue'

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
        componentColumn('metadata_filter', m.evaluationJobs_metadataFilter(), markRaw(RetrievalMetadataFilterChipList), {
          accessorKey: 'metadata_filter',
          props: (row) => ({ readonly: true, modelValue: row.metadata_filter }),
        }),
      ]
    : []),
  componentColumn('user_input', m.evaluation_input(), markRaw(TextWrap), {
    accessorKey: 'user_input',
    sortable: true,
    props: (row) => ({ name: 'user_input' }),
  }),
  componentColumn('expected_result', m.evaluation_expectedOutput(), markRaw(TextWrap), {
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
