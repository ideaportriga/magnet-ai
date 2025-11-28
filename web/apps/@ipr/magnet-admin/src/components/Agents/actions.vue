<template lang="pug">
div
  .row.q-mb-12
    .col-auto.center-flex-y
      km-input(placeholder='Search', iconBefore='search', v-model='searchString', @input='searchString = $event', clearable) 
    q-space
    .col-auto.center-flex-y
      km-btn.q-mr-12(
        v-if='selected.length > 0',
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
    km-table-new(
      @selectRow='selectRecord',
      selection='multiple',
      row-key='id',
      :active-record-id='selectedRow?.id',
      v-model:selected='selected',
      :columns='columns',
      :rows='agentDetailTopicActions ?? []',
      :pagination='agentPagination',
      binary-state-sort
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
  .row.text-center.justify-center {{ `You are going to delete ${selected?.length} selected records. Are you sure?` }}
</template>

<script>
import { agentTopicActionsColumns, agentPagination } from '@/config/agents/topics'
import { ref } from 'vue'

export default {
  emits: ['openTest'],
  setup() {
    return {
      columns: Object.values(agentTopicActionsColumns).sort((a, b) => a.columnNumber - b.columnNumber),
      showNewDialog: ref(false),
      selected: ref([]),
      showDeleteDialog: ref(false),
      agentPagination,
    }
  },
  computed: {
    routeParams() {
      return this.$route.params
    },
    topic() {
      return this.agentTopics?.find((topic) => topic?.system_name === this.routeParams?.topicId)
    },
    agentTopics() {
      return this.$store.getters.agentDetailVariant?.value?.topics ?? []
    },
    agentDetailTopicActions: {
      get() {
        return (
          this.$store.getters.agentDetailVariant?.value?.topics?.flatMap((topic) => {
            return (topic?.actions || []).map((action) => ({
              ...action,
              topic_system_name: topic.system_name,
              topic: topic.name,
              id: topic.system_name + '_' + action.system_name,
            }))
          }) ?? []
        )
      },
    },
  },
  methods: {
    deleteSelected() {
      this.agentTopics.forEach((topic) => {
        this.$store.commit('updateNestedAgentDetailListItemBySystemName', {
          arrayPath: 'topics',
          itemSystemName: topic?.system_name,
          data: {
            actions: (topic.actions || []).filter((action) => !this.selected.map((el) => el?.system_name).includes(action.system_name)),
          },
        })
      })

      this.selected = []
      this.showDeleteDialog = false
    },
    selectRecord(row) {
      this.navigate(`agents/${this.routeParams?.id}/topics/${row.topic_system_name}/actions/${row.system_name}`)
    },
    openNewDetails() {
      this.showNewDialog = true
    },
    navigate(path = '') {
      if (this.$route.path !== `/${path}`) {
        this.$router.push(`/${path}`)
      }
    },
    openDetails() {
      this.navigate('evaluation-sets/details')
    },
  },
}
</script>
