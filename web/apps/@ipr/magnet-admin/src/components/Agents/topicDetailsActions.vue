<template lang="pug">
div
  .km-heading-4.q-mb-md {{ m.agents_topicActions() }}
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
      km-btn.q-mr-12(label='New', @click='openNewDetails')
  .row
    km-data-table(
      :table='table',
      row-key='system_name',
      :activeRowId='activeTopic?.action',
      @row-click='selectRecord'
    )
  agents-create-new-action(:showNewDialog='showNewDialog', @cancel='showNewDialog = false', v-if='showNewDialog')
km-popup-confirm(
  :visible='showDeleteDialog',
  confirmButtonLabel='Delete',
  cancelButtonLabel='Cancel',
  notificationIcon='fas fa-triangle-exclamation',
  @confirm='deleteSelected',
  @cancel='showDeleteDialog = false'
)
  .row.item-center.justify-center.km-heading-7 {{ m.agents_deleteTopicActionRecords() }}
  .row.text-center.justify-center {{ m.agents_deleteConfirmMessage({ count: selectedRows?.length }) }}
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
