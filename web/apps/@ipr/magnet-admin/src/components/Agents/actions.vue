<template lang="pug">
div
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
  .row
    km-data-table(
      :table='table',
      row-key='id',
      @row-click='selectRecord'
    )
km-popup-confirm(
  :visible='showDeleteDialog',
  confirmButtonLabel='Delete',
  cancelButtonLabel='Cancel',
  notificationIcon='fas fa-triangle-exclamation',
  @confirm='deleteSelected',
  @cancel='showDeleteDialog = false'
)
  .row.item-center.justify-center.km-heading-7 Delete Topic Action Records
  .row.text-center.justify-center {{ `You are going to delete ${selectedRows?.length} selected records. Are you sure?` }}
</template>

<script setup>
import { ref, computed, h, markRaw } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAgentDetailStore } from '@/stores/agentDetailStore'
import { useLocalDataTable } from '@/composables/useLocalDataTable'
import { selectionColumn, textColumn, componentColumn } from '@/utils/columnHelpers'
import NameDescription from '@/config/agents/component/NameDescription.vue'
import Type from '@/config/agents/component/Type.vue'

const emit = defineEmits(['openTest'])

const router = useRouter()
const route = useRoute()
const agentStore = useAgentDetailStore()
const showDeleteDialog = ref(false)

const data = computed(() => {
  return (
    agentStore.activeVariant?.value?.topics?.flatMap((topic) => {
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
  return agentStore.activeVariant?.value?.topics ?? []
})

const deleteSelected = () => {
  agentTopics.value.forEach((topic) => {
    agentStore.updateNestedListItemBySystemName({
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
