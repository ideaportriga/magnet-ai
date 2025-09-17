<template lang="pug">
div
  .km-heading-4.q-mb-md Topic Actions
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
      km-btn.q-mr-12(label='New', @click='openNewDetails')
  .row
    km-table-new(
      @selectRow='selectRecord',
      selection='multiple',
      row-key='system_name',
      :active-record-id='activeTopic?.action',
      v-model:selected='selected',
      :columns='columns',
      :rows='agentDetailTopicActions ?? []',
      :pagination='agentPagination',
      binary-state-sort
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
      columns: Object.values(agentTopicActionsColumns)
        .filter((col) => col.name != 'topic')
        .sort((a, b) => a.columnNumber - b.columnNumber),
      showNewDialog: ref(false),
      selected: ref([]),
      showDeleteDialog: ref(false),
      searchString: ref(''),
      agentPagination,
    }
  },
  computed: {
    routeParams() {
      return this.$route.params
    },
    topic() {
      return (this.$store.getters.agentDetailVariant?.value?.topics || [])?.find((topic) => topic?.system_name === this.routeParams?.topicId)
    },
    system_name: {
      get() {
        return this.topic?.system_name || ''
      },
      set(value) {
        this.$store.commit('updateNestedAgentDetailListItemBySystemName', {
          arrayPath: 'topics',
          itemSystemName: this.system_name,
          data: {
            system_name: value,
          },
        })
      },
    },
    agentDetailTopicActions: {
      get() {
        const actions = this.topic?.actions ?? []
        return actions.filter((item) => {
          return (
            item.name.toLowerCase().includes(this.searchString.toLowerCase()) ||
            item.system_name.toLowerCase().includes(this.searchString.toLowerCase())
          )
        })
      },
      // set(value) {
      //   this.$store.commit('updateAgentDetailProperty', { key: 'items', value })
      // },
    },
    activeTopic: {
      get() {
        return this.$store.getters.activeTopic
      },
      set(value) {
        this.$store.commit('setActiveTopic', value)
      },
    },
  },
  methods: {
    deleteSelected() {
      this.$store.commit('updateNestedAgentDetailListItemBySystemName', {
        arrayPath: 'topics',
        itemSystemName: this.topic?.system_name,
        data: {
          actions: (this.topic.actions || []).filter((action) => !this.selected.map((el) => el?.system_name).includes(action.system_name)),
        },
      })

      this.selected = []
      this.showDeleteDialog = false
    },
    selectRecord(row) {
      this.activeTopic = {
        ...(this.activeTopic ? this.activeTopic : {}),
        topic: this.routeParams?.topicId,
        action: row.system_name,
      }
      // this.navigate(`agents/${this.routeParams?.id}/topics/${this.routeParams.topicId}/actions/${row.system_name}`)
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
