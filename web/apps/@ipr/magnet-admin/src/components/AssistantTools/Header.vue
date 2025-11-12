<template lang="pug">
.col-auto.q-py-auto
  .km-heading-4 {{ activeAssistantToolName }}
.col
.col-auto.q-mr-sm
  km-btn(label='Record info', icon='info', iconSize='16px') 
  q-tooltip.bg-white.block-shadow
    .q-pa-sm
      .q-mb-sm
        .text-secondary-text.km-button-xs-text Created:
        .text-secondary-text.km-description {{ created_at }}
      div
        .text-secondary-text.km-button-xs-text Modified:
        .text-secondary-text.km-description {{ modified_at }}
q-separator(vertical, color='white')
.col-auto.text-white.q-mx-md
  km-btn(label='Save', icon='far fa-save', color='primary', bg='background', iconSize='16px', @click='save')
.col-auto.text-white.q-mr-md
  q-btn.q-px-xs(flat, :icon='"fas fa-ellipsis-v"', size='13px')
    q-menu(anchor='bottom right', self='top right')
      q-item(clickable, @click='showNewDialog = true', dense)
        q-item-section
          .km-heading-3 Clone
      q-item(clickable, @click='deleteAssistantTool', dense)
        q-item-section
          .km-heading-3 Delete

assistant-tool-create-new(v-if='showNewDialog', :showNewDialog='showNewDialog', @cancel='showNewDialog = false', copy)
q-inner-loading(:showing='loading')
</template>

<script>
import { useChroma } from '@shared'
import { ref } from 'vue'

export default {
  props: ['activeAssistantToolTool'],
  emits: ['update:closeDrawer'],
  setup() {
    const { items, update, create, selectedRow, ...useCollection } = useChroma('assistant_tools')

    return {
      items,
      update,
      create,
      selectedRow,
      useCollection,
      loading: ref(false),
      showNewDialog: ref(false),
    }
  },
  computed: {
    created_at() {
      if (!this.activeAssistantToolDB?.created_at) return ''
      return `${this.formatDate(this.activeAssistantToolDB.created_at)}`
    },
    modified_at() {
      if (!this.activeAssistantToolDB?.updated_at) return ''
      return `${this.formatDate(this.activeAssistantToolDB.updated_at)}`
    },
    currentAssistantTool() {
      return this.$store.getters.assistant_tool
    },
    route() {
      return this.$route
    },
    activeAssistantToolId() {
      return this.$route.params.id
    },
    activeAssistantToolDB() {
      return this.items.find((item) => item.id == this.activeAssistantToolId)
    },
    activeAssistantToolName: {
      get() {
        return this.activeAssistantToolDB?.name
      },
      set(val) {
        this.openDetails(val.value)
      },
    },
    options() {
      return this.items.map((item) => ({ label: item.name, value: item }))
    },
  },
  watch: {},
  created() {},

  methods: {
    deleteAssistantTool() {
      this.$q.notify({
        message: `Are you sure you want to delete ${this.selectedRow?.name}?`,
        color: 'error-text',
        position: 'top',
        timeout: 0,
        actions: [
          {
            label: 'Cancel',
            color: 'yellow',
            handler: () => {
              /* ... */
            },
          },
          {
            label: 'Delete',
            color: 'white',
            handler: () => {
              this.loadingDelelete = true
              this.useCollection.delete({ id: this.selectedRow?.id })
              this.$emit('update:closeDrawer', null)
              this.$q.notify({
                position: 'top',
                message: 'RAG Tool has been deleted.',
                color: 'positive',
                textColor: 'black',
                timeout: 1000,
              })
              this.navigate('/assistant-tools')
            },
          },
        ],
      })
    },
    async openDetails(row) {
      await this.$router.push(`/assistant-tools/${row.id}`)
    },
    navigate(path = '') {
      if (this.$route.path !== `/${path}`) {
        this.$router.push(`${path}`)
      }
    },
    async save() {
      this.loading = true
      if (this.currentAssistantTool?.created_at) {
        await this.update({ id: this.currentAssistantTool.id, data: JSON.stringify(this.currentAssistantTool) })
      } else {
        await this.create(JSON.stringify(this.currentAssistantTool))
      }
      this.$store.commit('setInitAssistantTool')
      this.loading = false
    },
    formatDate(date) {
      const dateObject = new Date(date)
      const localeDateString = dateObject.toLocaleDateString()
      const localeTimeString = dateObject.toLocaleTimeString()
      return `${localeDateString} ${localeTimeString}`
    },
  },
}
</script>
