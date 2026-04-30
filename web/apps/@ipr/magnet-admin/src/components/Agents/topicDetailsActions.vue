<template>
  <div>
    <div class="km-heading-4 mb-md">{{ m.agents_topicActions() }}</div>
    <div class="cluster mb-md">
      <div class="flex-none center-flex-y">
        <km-input :placeholder="m.common_search()" icon-before="search" :model-value="globalFilter" clearable @input="globalFilter = $event" />
      </div>
      <div class="km-space" />
      <div class="flex-none center-flex-y">
        <km-btn v-if="selectedRows.length &gt; 0" class="mr-md" icon="delete" :label="m.common_delete()" interaction-tone="brand" label-class="km-title" flat icon-size="16px" @click="showDeleteDialog = true" />
        <km-btn class="mr-md" :label="m.common_new()" @click="openNewDetails" />
      </div>
    </div>
    <div class="cluster">
      <km-data-table :table="table" row-key="system_name" :active-row-id="activeTopic?.action" @row-click="selectRecord" />
    </div>
    <agents-create-new-action v-if="showNewDialog" :show-new-dialog="showNewDialog" @cancel="showNewDialog = false" />
  </div>
  <km-popup-confirm :visible="showDeleteDialog" :confirm-button-label="m.common_delete()" :cancel-button-label="m.common_cancel()" notification-icon="warning" @confirm="deleteSelected" @cancel="showDeleteDialog = false">
    <div class="cluster" data-justify="center">{{ m.agents_deleteTopicActionRecords() }}</div>
    <div class="cluster text-center" data-justify="center">{{ m.agents_deleteConfirmMessage({ count: selectedRows?.length }) }}</div>
  </km-popup-confirm>
</template>

<script setup>
import { ref, computed, markRaw } from 'vue'
import { m } from '@/paraglide/messages'
import { useRoute } from 'vue-router'
import { useAgentEntityDetail } from '@/composables/useAgentEntityDetail'
import { useLocalDataTable } from '@/composables/useLocalDataTable'
import { selectionColumn, textColumn, componentColumn } from '@/utils/columnHelpers'
import NameDescription from '@/config/agents/component/NameDescription.vue'
import Type from '@/config/agents/component/Type.vue'

const emit = defineEmits(['openTest'])

const route = useRoute()
const { activeVariant, activeTopic: activeTopicRef, updateNestedListItemBySystemName } = useAgentEntityDetail()
const showNewDialog = ref(false)
const showDeleteDialog = ref(false)

const routeParams = computed(() => route.params)

const topic = computed(() => {
  return (activeVariant.value?.value?.topics || [])?.find(
    (topic) => topic?.system_name === routeParams.value?.topicId
  )
})

const data = computed(() => {
  const actions = topic.value?.actions ?? []
  return actions
})

const columns = [
  selectionColumn(),
  componentColumn('nameDescription', 'Name & Description for LLM', markRaw(NameDescription), {
    accessorKey: 'name',
    sortable: true,
    props: (row) => ({
      row: {
        name: row.function_name,
        description: row.function_description,
      },
    }),
  }),
  componentColumn('type', 'Type', markRaw(Type), {
    accessorKey: 'type',
    sortable: true,
  }),
]

const { table, globalFilter, selectedRows, clearSelection } = useLocalDataTable(data, columns, {
  enableRowSelection: true,
})

const activeTopic = computed({
  get() {
    return activeTopicRef.value
  },
  set(value) {
    activeTopicRef.value = value
  },
})

const deleteSelected = () => {
  updateNestedListItemBySystemName({
    arrayPath: 'topics',
    itemSystemName: topic.value?.system_name,
    data: {
      actions: (topic.value.actions || []).filter(
        (action) => !selectedRows.value.map((el) => el?.system_name).includes(action.system_name)
      ),
    },
  })

  clearSelection()
  showDeleteDialog.value = false
}

const selectRecord = (row) => {
  activeTopic.value = {
    ...(activeTopic.value ? activeTopic.value : {}),
    topic: routeParams.value?.topicId,
    action: row.system_name,
  }
}

const openNewDetails = () => {
  showNewDialog.value = true
}
</script>
