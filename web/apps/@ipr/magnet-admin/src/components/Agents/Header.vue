<template lang="pug">
.col-auto.q-py-auto
  .km-heading-4 {{ activeRowName }}
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
  km-btn(label='Save', icon='far fa-save', iconSize='16px', color='primary', bg='background', @click='save', :loading='loading', :disable='loading')
.col-auto.text-white.q-mr-md
  q-btn.q-px-xs(flat, :icon='"fas fa-ellipsis-v"', size='13px')
    q-menu(anchor='bottom right', self='top right')
      q-item(clickable, @click='showNewDialog = true', dense)
        q-item-section
          .km-heading-3 Clone
      q-item(clickable, @click='showDeleteDialog = true', dense)
        q-item-section
          .km-heading-3 Delete

agents-create-new(v-if='showNewDialog', :showNewDialog='showNewDialog', @cancel='showNewDialog = false', copy)
km-popup-confirm(
  :visible='showDeleteDialog',
  confirmButtonLabel='Delete Agent',
  cancelButtonLabel='Cancel',
  notificationIcon='fas fa-triangle-exclamation',
  @confirm='deleteRecord',
  @cancel='showDeleteDialog = false'
)
  .row.item-center.justify-center.km-heading-7 You are about to delete the Agent
  .row.text-center.justify-center Deleting the Agent will also permanently delete its Topics with their interactions.
q-inner-loading(:showing='loading')
</template>

<script>
import { useChroma } from '@shared'
import { validSystemName } from '@shared/utils/validationRules'
import { ref } from 'vue'

export default {
  props: ['activeRow'],
  emits: ['update:closeDrawer'],
  setup() {
    const { items, update, create, selectedRow, ...useCollection } = useChroma('agents')

    return {
      items,
      update,
      create,
      selectedRow,
      loading: ref(false),
      useCollection,
      showNewDialog: ref(false),
      showDeleteDialog: ref(false),
    }
  },
  computed: {
    isCancelAvaliable() {
      return !this.$store.getters.promptTemplate?._metadata
    },
    created_at() {
      if (!this.activeRowDB?.created_at) return ''
      return `${this.formatDate(this.activeRowDB?.created_at)}`
    },
    modified_at() {
      if (!this.activeRowDB?.updated_at) return ''
      return `${this.formatDate(this.activeRowDB?.updated_at)}`
    },
    currentRow() {
      return this.$store.getters.agent_detail
    },
    route() {
      return this.$route
    },
    activeRowId() {
      return this.$route.params.id
    },
    activeTopicId() {
      return this.$route.params?.topicId || ''
    },
    activeActionId() {
      return this.$route.params?.actionId || ''
    },
    activeAgent() {
      return this.items.find((item) => item.id == this.activeRowId)
    },
    activeTopic: {
      get() {
        return this.activeAgent?.variants
          ?.find((el) => (this.activeAgent.active_variant = el?.variant))
          ?.value?.topics?.find((el) => el.system_name == this.activeTopicId)
      },
    },
    activeAction() {
      return this.activeTopic?.actions?.find((el) => el.system_name == this.activeActionId)
    },

    activeRowDB() {
      // if (this.activeAction) return this.activeAction
      // if (this.activeTopicId) return this.activeTopic
      return this.activeAgent
    },

    activeRowName: {
      get() {
        return this.activeRowDB?.name
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
    deleteRecord() {
      this.useCollection.delete({ id: this.selectedRow?.id })
      this.$emit('update:closeDrawer', null)
      this.$q.notify({
        position: 'top',
        message: 'Agent deleted successfully',
        color: 'positive',
        textColor: 'black',
        timeout: 1000,
      })
      this.navigate('/agents')
    },
    async openDetails(row) {
      await this.$router.push(`/agents/${row.id}`)
    },
    navigate(path = '') {
      if (this.$route.path !== `/${path}`) {
        this.$router.push(`${path}`)
      }
    },
    async save() {
      // Validate system_name before saving
      const systemNameValidation = validSystemName()(this.currentRow?.system_name)
      if (systemNameValidation !== true) {
        this.$q.notify({
          position: 'top',
          color: 'negative',
          message: systemNameValidation,
          timeout: 3000,
        })
        return
      }

      this.loading = true
      try {
        if (this.currentRow?.created_at) {
          const obj = { ...this.currentRow }
          delete obj.created_at
          delete obj.updated_at
          await this.update({ id: obj.id, data: obj })
        } else {
          await this.create(this.currentRow)
        }
        this.$store.dispatch('setAgentDetailById', this.currentRow.id)
        this.$q.notify({
          position: 'top',
          type: 'positive',
          message: 'Saved successfully',
          timeout: 2000,
        })
      } catch (error) {
        this.$q.notify({
          position: 'top',
          color: 'negative',
          message: error.message || 'Failed to save',
          timeout: 3000,
        })
      } finally {
        this.loading = false
      }
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
