<template>
  <div>
    <agents-topic-template-section />
    <km-separator class="my-lg" />
    <div class="km-heading-4 mb-lg">{{ m.agents_agentTopics() }}</div>
    <div class="cluster mb-md">
      <div class="flex-none center-flex-y">
        <km-input :placeholder="m.common_search()" icon-before="search" :model-value="globalFilter" clearable @input="globalFilter = $event" />
      </div>
      <div class="km-space" />
      <div class="flex-none center-flex-y">
        <km-btn v-if="selectedRows.length &gt; 0" class="mr-md" icon="delete" :label="m.common_delete()" interaction-tone="brand" label-class="km-title" flat icon-size="16px" @click="showDeleteDialog = true" />
      </div>
      <div class="flex-none center-flex-y">
        <km-btn class="mr-md" :label="m.common_new()" @click="openNewDetails" />
      </div>
    </div>
    <div class="cluster">
      <km-data-table :table="table" row-key="system_name" :active-row-id="activeTopic?.topic" @row-click="selectRecord" />
    </div>
  </div>
  <agents-create-new-topic v-if="showNewDialog" :show-new-dialog="showNewDialog" @cancel="showNewDialog = false" />
  <km-popup-confirm :visible="showDeleteDialog" :confirm-button-label="m.common_delete()" :cancel-button-label="m.common_cancel()" notification-icon="warning" @confirm="deleteSelected" @cancel="showDeleteDialog = false">
    <div class="cluster" data-justify="center">{{ m.agents_deleteTopicRecords() }}</div>
    <div class="cluster text-center" data-justify="center">{{ m.agents_deleteConfirmMessage({ count: selectedRows?.length }) }}</div>
  </km-popup-confirm>
</template>

<script setup>
import { ref, computed, h, markRaw } from 'vue'
import { m } from '@/paraglide/messages'
import { useRouter, useRoute } from 'vue-router'
import { useEntityQueries } from '@/queries/entities'
import { useAgentEntityDetail } from '@/composables/useAgentEntityDetail'
import { useLocalDataTable } from '@/composables/useLocalDataTable'
import { selectionColumn, textColumn, componentColumn, drilldownColumn } from '@/utils/columnHelpers'
import NameSystemName from '@/config/agents/component/NameSystemName.vue'
import TextWrap from '@/config/agents/component/TextWrap.vue'

const emit = defineEmits(['openTest'])

const router = useRouter()
const route = useRoute()
const queries = useEntityQueries()
const { data: promptTemplateData } = queries.promptTemplates.useList()
const promptTemplateItems = computed(() => promptTemplateData.value?.items ?? [])

const { draft, activeVariant, updateVariantField, activeTopic: activeTopicRef } = useAgentEntityDetail()
const showNewDialog = ref(false)
const showDeleteDialog = ref(false)

const data = computed(() => {
  const topics = activeVariant.value?.value?.topics || []
  return topics.map((item) => ({ ...item, actions: item.actions?.length || '' }))
})

const columns = [
  selectionColumn(),
  componentColumn('nameSystemName', m.agents_nameAndSystemName(), markRaw(NameSystemName), {
    accessorKey: 'name',
    sortable: true,
  }),
  componentColumn('description', m.agents_llmDescription(), markRaw(TextWrap), {
    accessorKey: 'description',
    sortable: true,
    props: (row) => ({ name: 'description' }),
  }),
  textColumn('actions', m.agents_actions()),
  drilldownColumn(),
]

const { table, globalFilter, selectedRows, clearSelection } = useLocalDataTable(data, columns, {
  enableRowSelection: true,
})

const routeParams = computed(() => route.params)

const agentDetailVariantTopics = computed(() => {
  return activeVariant.value?.value?.topics || []
})

const promptTemplatesOptions = computed(() => {
  return (promptTemplateItems.value ?? []).map((item) => ({
    label: item.name,
    value: item.id,
    system_name: item.system_name,
    category: item.category,
    id: item.id,
  }))
})

const activeTopic = computed(() => activeTopicRef.value)

const cellAction = ({ event, action, row }) => {
  event.stopPropagation()
  router.push(`/agents/${routeParams.value?.id}/topics/${row.system_name}`)
}

const deleteSelected = () => {
  updateVariantField('topics',
    agentDetailVariantTopics.value.filter(
      (item) => !selectedRows.value.map((el) => el?.system_name).includes(item.system_name)
    ),
  )
  clearSelection()
  showDeleteDialog.value = false
}

const selectRecord = (row) => {
  activeTopicRef.value = {
    topic: row?.system_name,
  }
}

const openNewDetails = () => {
  showNewDialog.value = true
}
</script>
