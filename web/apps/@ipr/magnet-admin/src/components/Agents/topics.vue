<template lang="pug">
div
  agents-topic-template-section
  q-separator.q-my-lg
  .km-heading-4.q-mb-lg Agent topics
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
      km-btn.q-mr-12(label='New', @click='openNewDetails')
  .row
    km-table-new(
      @selectRow='selectRecord',
      selection='multiple',
      row-key='system_name',
      :active-record-id='activeTopic?.topic',
      v-model:selected='selected',
      :columns='columns',
      :rows='agentDetailTopics ?? []',
      :pagination='agentPagination',
      binary-state-sort,
      @cellAction='cellAction'
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
  .row.item-center.justify-center.km-heading-7 Delete Topic Records
  .row.text-center.justify-center {{ `You are going to delete ${selected?.length} selected records. Are you sure?` }}
</template>

<script>
import { columnsSettings, agentPagination } from '@/config/agents/topics'
import { ref } from 'vue'
import { useChroma } from '@shared'

export default {
  emits: ['openTest'],
  setup() {
    const { items: promptTemplateItems } = useChroma('promptTemplates')

    return {
      columns: Object.values(columnsSettings).sort((a, b) => a.columnNumber - b.columnNumber),
      showNewDialog: ref(false),
      selected: ref([]),
      showDeleteDialog: ref(false),
      searchString: ref(''),
      agentPagination,
      promptTemplateItems,
    }
  },
  computed: {
    routeParams() {
      return this.$route.params
    },
    agentDetailTopics: {
      get() {
        const topics = this.$store.getters.agentDetailVariant?.value?.topics || []
        return topics
          .filter((item) => {
            return (
              item.name.toLowerCase().includes(this.searchString.toLowerCase()) ||
              item.system_name.toLowerCase().includes(this.searchString.toLowerCase()) ||
              item.description.toLowerCase().includes(this.searchString.toLowerCase())
            )
          })
          .map((item) => ({ ...item, actions: item.actions?.length || '' }))
      },
    },
    agentDetailVariantTopics() {
      return this.$store.getters.agentDetailVariant?.value?.topics || []
    },
    promptTemplatesOptions() {
      return (this.promptTemplateItems ?? []).map((item) => ({
        label: item.name,
        value: item.id,
        system_name: item.system_name,
        category: item.category,
        id: item.id,
      }))
    },
    topicSelectionPromptTemplateId() {
      return this.promptTemplatesOptions.find((el) => el.system_name == this.topicSelectionPromptTemplate)?.id
    },

    topicProcessingPromptTemplateId() {
      return this.promptTemplatesOptions.find((el) => el.system_name == this.topicProcessingPromptTemplate)?.id
    },

    topicSelectionPromptTemplate: {
      get() {
        return this.$store.getters.agentDetailVariant?.value.prompt_templates?.classification
      },
      set(value) {
        this.$store.dispatch(
          'updateNestedAgentDetailProperty',

          { path: 'prompt_templates.classification', value }
        )
      },
    },
    activeTopic() {
      return this.$store.getters.activeTopic
    },
  },
  methods: {
    cellAction({ event, action, row }) {
      event.stopPropagation()
      this.$router.push(`/agents/${this.routeParams?.id}/topics/${row.system_name}`)
    },
    deleteSelected() {
      this.$store.commit('updateNestedAgentDetailProperty', {
        path: 'topics',
        value: this.agentDetailVariantTopics.filter((item) => !this.selected.map((el) => el?.system_name).includes(item.system_name)),
      })
      this.selected = []
      this.showDeleteDialog = false
    },
    selectRecord(row) {
      this.$store.commit('setActiveTopic', {
        topic: row?.system_name,
      })
      // this.navigate(`agents/${this.routeParams?.id}/topics/${row.system_name}`)
    },
    openNewDetails() {
      this.showNewDialog = true
    },
    navigate(path = '') {
      if (this.$route.path !== `/${path}`) {
        this.$router.push(`/${path}`)
      }
    },
  },
}
</script>
