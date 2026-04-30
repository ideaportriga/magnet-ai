<template>
  <div>
    <div class="cluster mb-md">
      <div class="flex-none center-flex-y">
        <km-input :placeholder="m.common_search()" icon-before="search" :model-value="globalFilter" clearable @input="globalFilter = $event" />
      </div>
      <div class="km-space" />
      <div class="flex-none center-flex-y">
        <km-btn v-if="selectedRows.length &gt; 0" class="mr-md" icon="delete" :label="m.common_delete()" interaction-tone="brand" label-class="km-title" flat icon-size="16px" @click="showDeleteDialog = true" />
        <div class="flex-none center-flex-y" />
      </div>
    </div>
    <div class="cluster">
      <km-data-table :table="table" row-key="id" @row-click="selectRecord" />
    </div>
  </div>
  <km-popup-confirm :visible="showDeleteDialog" :confirm-button-label="m.common_delete()" :cancel-button-label="m.common_cancel()" notification-icon="warning" @confirm="deleteSelected" @cancel="showDeleteDialog = false">
    <div class="cluster" data-justify="center">{{ m.agents_deleteTopicActionRecords() }}</div>
    <div class="cluster text-center" data-justify="center">{{ m.agents_deleteConfirmMessage({ count: selectedRows?.length }) }}</div>
  </km-popup-confirm>
</template>

<script setup>
import { ref, computed, h, markRaw } from 'vue'
import { m } from '@/paraglide/messages'
import { useRouter, useRoute } from 'vue-router'
import { useAgentEntityDetail } from '@/composables/useAgentEntityDetail'
import { useLocalDataTable } from '@/composables/useLocalDataTable'
import { selectionColumn, textColumn, componentColumn } from '@/utils/columnHelpers'
import NameDescription from '@/config/agents/component/NameDescription.vue'
import Type from '@/config/agents/component/Type.vue'

const emit = defineEmits(['openTest'])

const router = useRouter()
const route = useRoute()
const { activeVariant, updateNestedListItemBySystemName } = useAgentEntityDetail()
const showDeleteDialog = ref(false)

const data = computed(() => {
  return (
    activeVariant.value?.value?.topics?.flatMap((topic) => {
      return (topic?.actions || []).map((action) => ({
        ...action,
        topic_system_name: topic.system_name,
        topic: topic.name,
        id: topic.system_name + '_' + action.system_name,
      }))
    }) ?? []
  )
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
  textColumn('topic', 'Topic'),
]

const { table, globalFilter, selectedRows, clearSelection } = useLocalDataTable(data, columns, {
  enableRowSelection: true,
})

const routeParams = computed(() => route.params)

const agentTopics = computed(() => {
  return activeVariant.value?.value?.topics ?? []
})

const deleteSelected = () => {
  agentTopics.value.forEach((topic) => {
    updateNestedListItemBySystemName({
      arrayPath: 'topics',
      itemSystemName: topic?.system_name,
      data: {
        actions: (topic.actions || []).filter(
          (action) => !selectedRows.value.map((el) => el?.system_name).includes(action.system_name)
        ),
      },
    })
  })
  clearSelection()
  showDeleteDialog.value = false
}

const selectRecord = (row) => {
  router.push(`/agents/${routeParams.value?.id}/topics/${row.topic_system_name}/actions/${row.system_name}`)
}
</script>
