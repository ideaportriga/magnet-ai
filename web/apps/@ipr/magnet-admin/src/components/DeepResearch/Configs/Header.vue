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
      .q-mb-sm
        .text-secondary-text.km-button-xs-text Modified:
        .text-secondary-text.km-description {{ updated_at }}
      .q-mb-sm
        .text-secondary-text.km-button-xs-text Created by:
        .text-secondary-text.km-description {{ created_by }}
      div
        .text-secondary-text.km-button-xs-text Modified by:
        .text-secondary-text.km-description {{ updated_by }}
q-separator(vertical, color='white')
.col-auto.text-white.q-mx-md
  km-btn(label='Create Run', icon='play_arrow', iconSize='16px', @click='showRunDialog = true')
.col-auto.text-white.q-mx-md
  km-btn(label='Save', icon='far fa-save', iconSize='16px', color='primary', bg='background', @click='save', :loading='loading')
.col-auto.text-white.q-mr-md
  q-btn.q-px-xs(flat, :icon='"fas fa-ellipsis-v"', size='13px', data-test='show-more-btn')
    q-menu(anchor='bottom right', self='top right')
      q-item(clickable, @click='showNewDialog = true', dense)
        q-item-section
          .km-heading-3 Clone
      q-item(clickable, @click='showDeleteDialog = true', dense, data-test='delete-btn')
        q-item-section
          .km-heading-3 Delete

deep-research-configs-create-new(v-if='showNewDialog', :showNewDialog='showNewDialog', @cancel='showNewDialog = false', @created='onCloned', copy)
km-popup-confirm(
  :visible='showDeleteDialog',
  confirmButtonLabel='Delete Deep Research Config',
  cancelButtonLabel='Cancel',
  notificationIcon='fas fa-triangle-exclamation',
  @confirm='deleteRecord',
  @cancel='showDeleteDialog = false'
)
  .row.item-center.justify-center.km-heading-7 You are about to delete the Deep Research Config
  .row.text-center.justify-center This action will permanently delete the configuration and cannot be undone.

q-dialog(v-model='showRunDialog')
  q-card(style='min-width: 600px')
    q-card-section
      .text-h6 Create New Run
    q-card-section.q-pt-none
      .km-field.q-mb-md
        .text-secondary-text.q-pb-xs Config
        km-input(
          :model-value='activeRowName',
          height='30px',
          readonly
        )
        .km-description.text-secondary-text.q-pt-2 This run will use the current configuration
      .km-field.q-mb-md
        .text-secondary-text.q-pb-xs Input (JSON)
        q-input(
          v-model='runInput',
          type='textarea',
          outlined,
          rows='8',
          placeholder='{"query": "Research question here"}'
        )
        .km-description.text-secondary-text.q-pt-2 Provide the input data for the research run
      .km-field.q-mb-md
        .text-secondary-text.q-pb-xs Client ID (optional)
        km-input(
          v-model='runClientId',
          height='30px',
          placeholder='Optional client identifier'
        )
    q-card-actions(align='right')
      km-btn(flat, label='Cancel', @click='showRunDialog = false')
      km-btn(label='Create Run', :loading='creatingRun', @click='createRun')

q-inner-loading(:showing='loading')
</template>

<script>
import { ref } from 'vue'
import { useQuasar } from 'quasar'

export default {
  props: ['activeRow'],
  emits: ['update:closeDrawer'],
  setup() {
    const $q = useQuasar()
    
    return {
      $q,
      loading: ref(false),
      showNewDialog: ref(false),
      showDeleteDialog: ref(false),
      showRunDialog: ref(false),
      runInput: ref('{"query": ""}'),
      runClientId: ref(''),
      creatingRun: ref(false),
    }
  },
  computed: {
    created_at() {
      if (!this.activeRowDB?.created_at) return ''
      return `${this.formatDate(this.activeRowDB?.created_at)}`
    },
    updated_at() {
      if (!this.activeRowDB) return ''
      return `${this.formatDate(this.activeRowDB?.updated_at)}`
    },
    created_by() {
      if (!this.activeRowDB?.created_by) return 'Unknown'
      return `${this.activeRowDB?.created_by}`
    },
    updated_by() {
      if (!this.activeRowDB?.updated_by) return 'Unknown'
      return `${this.activeRowDB?.updated_by}`
    },
    currentRow() {
      return this.$store.getters.selectedConfig
    },
    route() {
      return this.$route
    },
    activeRowId() {
      return this.$route.params.id
    },
    activeRowDB() {
      return this.$store.getters.configs?.find((item) => item.id == this.activeRowId)
    },
    activeRowName() {
      return this.activeRowDB?.name
    },
  },
  methods: {
    onCloned(configId) {
      this.showNewDialog = false
      this.$router.push(`/deep-research/configs/${configId}`)
    },
    deleteRecord() {
      this.showDeleteDialog = false
      this.$store.dispatch('deleteConfig', this.activeRowId).then(() => {
        this.$emit('update:closeDrawer', null)
        this.$q.notify({
          position: 'top',
          message: 'Deep Research Config has been deleted',
          color: 'positive',
          textColor: 'black',
          timeout: 1000,
        })
        this.$router.push('/deep-research/configs')
      }).catch((error) => {
        this.$q.notify({
          position: 'top',
          message: error?.message || 'Failed to delete configuration',
          color: 'positive',
          textColor: 'black',
          timeout: 1000,
        })
      })
    },
    async save() {
      this.loading = true
      try {
        if (!this.currentRow) {
          throw new Error('No configuration loaded')
        }

        if (this.currentRow?.created_at) {
          await this.$store.dispatch('updateConfig', {
            configId: this.activeRowId,
            updates: {
              name: this.currentRow.name,
              description: this.currentRow.description,
              system_name: this.currentRow.system_name,
              config: this.currentRow.config,
            },
          })
        } else {
          await this.$store.dispatch('createConfig', this.currentRow)
        }
        
        this.$q.notify({
          position: 'top',
          message: 'Configuration saved successfully',
          color: 'positive',
          textColor: 'black',
          timeout: 1000,
        })
      } catch (error) {
        this.$q.notify({
          position: 'top',
          message: error?.message || 'Failed to save configuration',
          color: 'positive',
          textColor: 'black',
          timeout: 1000,
        })
      } finally {
        this.loading = false
      }
    },
    formatDate(date) {
      if (!date) return ''
      const dateObject = new Date(date)
      const localeDateString = dateObject.toLocaleDateString()
      const localeTimeString = dateObject.toLocaleTimeString()
      return `${localeDateString} ${localeTimeString}`
    },
    async createRun() {
      // Validate JSON
      let inputPayload
      try {
        inputPayload = JSON.parse(this.runInput)
      } catch (e) {
        this.$q.notify({
          position: 'top',
          message: 'Invalid JSON input',
          color: 'positive',
          textColor: 'black',
          timeout: 1000,
        })
        return
      }

      this.creatingRun = true
      try {
        const result = await this.$store.dispatch('createRun', {
          config: this.activeRowDB?.config || {},
          input: inputPayload,
          client_id: this.runClientId || undefined,
          config_system_name: this.activeRowDB?.system_name,
        })

        this.$q.notify({
          position: 'top',
          message: 'Run has been created',
          color: 'positive',
          textColor: 'black',
          timeout: 1000,
        })

        this.showRunDialog = false
        this.runInput = '{"query": ""}'
        this.runClientId = ''

        // Navigate to the new run
        if (result?.id) {
          this.$router.push(`/deep-research/runs/${result.id}`)
        }
      } catch (error) {
        this.$q.notify({
          position: 'top',
          message: error?.message || 'Failed to create run',
          color: 'positive',
          textColor: 'black',
          timeout: 1000,
        })
      } finally {
        this.creatingRun = false
      }
    },
  },
}
</script>
