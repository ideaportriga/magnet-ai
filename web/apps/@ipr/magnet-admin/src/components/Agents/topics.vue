<template lang="pug">
div
  agents-topic-template-section
  q-separator.q-my-lg
  .km-heading-4.q-mb-lg {{ m.agents_agentTopics() }}
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
      km-btn.q-mr-12(label='New', @click='openNewDetails')
  .row
    km-data-table(
      :table='table',
      row-key='system_name',
      :activeRowId='activeTopic?.topic',
      @row-click='selectRecord'
    )

agents-create-new-topic(:showNewDialog='showNewDialog', @cancel='showNewDialog = false', v-if='showNewDialog')
km-popup-confirm(
  :visible='showDeleteDialog',
  confirmButtonLabel='Delete',
  cancelButtonLabel='Cancel',
  notificationIcon='fas fa-triangle-exclamation',
  @confirm='deleteSelected',
  @cancel='showDeleteDialog = false'
)
  .row.item-center.justify-center.km-heading-7 {{ m.agents_deleteTopicRecords() }}
  .row.text-center.justify-center {{ m.agents_deleteConfirmMessage({ count: selectedRows?.length }) }}
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
  componentColumn('nameSystemName', 'Name & system name', markRaw(NameSystemName), {
    accessorKey: 'name',
    sortable: true,
  }),
  componentColumn('description', 'LLM description', markRaw(TextWrap), {
    accessorKey: 'description',
    sortable: true,
    props: (row) => ({ name: 'description' }),
  }),
  textColumn('actions', 'Actions'),
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
