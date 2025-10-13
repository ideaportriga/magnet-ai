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
        .text-secondary-text.km-button-xs-text Last Synced:
        .text-secondary-text.km-description {{ modified_at }}
q-separator(vertical, color='white')
.col-auto.text-white.q-ml-md
  km-btn(label='Save', icon='far fa-save', iconSize='16px', color='primary', bg='background', @click='save')
.col-auto.text-white.q-mx-md
  km-btn(label='Save & Sync', @click='refreshCollection', iconSize='16px', icon='fa-solid fa-rotate', color='primary', bg='background')
.col-auto.text-white.q-mr-md
  q-btn.q-px-xs(flat, :icon='"fas fa-ellipsis-v"', size='13px')
    q-menu(anchor='bottom right', self='top right')
      q-item(clickable, @click='showNewDialog = true', dense)
        q-item-section
          .km-heading-3 Clone
      q-item(clickable, @click='showDeleteDialog = true', dense)
        q-item-section
          .km-heading-3 Delete

collections-create-new(v-if='showNewDialog', :showNewDialog='showNewDialog', @cancel='showNewDialog = false', copy)
q-inner-loading(:showing='loading')
km-popup-confirm(
  :visible='showDeleteDialog',
  confirmButtonLabel='Delete Knowledge Source',
  cancelButtonLabel='Cancel',
  notificationIcon='fas fa-triangle-exclamation',
  @confirm='deleteKnowledge',
  @cancel='showDeleteDialog = false'
)
  .row.item-center.justify-center.km-heading-7 You are about to delete the Knowledge Source
  .row.text-center.justify-center This action will permanently delete the Knowledge Source and disable it in all tools that are using it, e.g. RAG Tools.

km-popup-confirm(
  :visible='showSyncConfirm',
  confirmButtonLabel='Open Sync Job',
  cancelButtonLabel='Cancel',
  notificationIcon='fas fa-info-circle',
  @confirm='openJobDetails',
  @cancel='showSyncConfirm = false'
)
  .row.item-center.justify-center.km-heading-7.q-mb-md Syncing has started
  .row.text-center.justify-center A sync job {{ job_id }} has been created and started. This process will update your Knowledge Source.
</template>

<script>
import { useChroma } from '@shared'
import { ref } from 'vue'

export default {
  props: ['activeRow'],
  emits: ['update:closeDrawer'],
  setup() {
    const { items, update, create, selectedRow, ...useCollection } = useChroma('collections')

    return {
      items,
      update,
      create,
      selectedRow,
      loading: ref(false),
      useCollection,
      showNewDialog: ref(false),
      showDeleteDialog: ref(false),
      showSyncConfirm: ref(false),
      job_id: ref(null),
    }
  },
  computed: {
    isCancelAvaliable() {
      return !this.$store.getters.promptTemplate?._metadata
    },
    created_at() {
      if (!this.activeRowDB) return ''
      return `${this.formatDate(this.activeRowDB?.created)}`
    },
    modified_at() {
      if (!this.activeRowDB) return ''
      if (!this.activeRowDB?.last_synced || this.activeRowDB?.last_synced?.invalid) return '-'
      return `${this.formatDate(this.activeRowDB?.last_synced)}`
    },
    currentRow() {
      return this.$store.getters.knowledge
    },
    route() {
      return this.$route
    },
    activeRowId() {
      return this.$route.params.id
    },
    activeRowDB() {
      return this.items.find((item) => item.id == this.activeRowId)
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
    openJobDetails() {
      this.showSyncConfirm = false
      this.navigate(`/jobs/?job_id=${this.job_id}`)
    },
    deleteKnowledge() {
      this.loadingDelelete = true
      this.useCollection.delete({ id: this.selectedRow?.id })
      this.$emit('update:closeDrawer', null)
      this.$q.notify({
        position: 'top',
        message: 'Knowledge source has been deleted.',
        color: 'positive',
        textColor: 'black',
        timeout: 1000,
      })
      this.navigate('/knowledge-sources')
    },
    async refreshCollection() {
      await this.save()
      await this.createJob()
      this.showSyncConfirm = true
    },

    async createJob() {
      let jobData = {
        name: `Sync ${this.selectedRow?.name}`,
        job_type: 'one_time_immediate',
        notification_email: '',
        run_configuration: {
          type: 'sync_collection',
          params: {
            system_name: this.selectedRow?.system_name,
          },
        },
        timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
      }

      const job = await this.$store.dispatch('createAndRunJobScheduler', jobData)
      this.job_id = job.job_id

      this.$q.notify({
        position: 'top',
        message: 'Sync job has been created.',
        color: 'positive',
        textColor: 'black',
        timeout: 1000,
      })
    },

    async openDetails(row) {
      await this.$router.push(`/knowledge-sources/${row.id}`)
    },
    navigate(path = '') {
      if (this.$route.path !== `/${path}`) {
        this.$router.push(`${path}`)
      }
    },
    transformSourceFields(source) {
      // Transform Documentation source fields from comma-separated strings to arrays
      if (source?.source_type === 'Documentation') {
        const transformed = { ...source }
        
        // Convert languages from string to array
        if (transformed.languages && typeof transformed.languages === 'string') {
          transformed.languages = transformed.languages
            .split(',')
            .map(lang => lang.trim())
            .filter(lang => lang.length > 0)
        }
        
        // Convert sections from string to array
        if (transformed.sections && typeof transformed.sections === 'string') {
          transformed.sections = transformed.sections
            .split(',')
            .map(section => section.trim())
            .filter(section => section.length > 0)
        }
        
        // Convert max_depth to integer if provided
        if (transformed.max_depth) {
          transformed.max_depth = parseInt(transformed.max_depth) || 5
        }
        
        return transformed
      }
      
      return source
    },
    async save() {
      this.loading = true
      if (this.currentRow?.created_at) {
        const obj = { ...this.currentRow }
        delete obj._metadata
        delete obj.id
        
        // Transform source fields for Documentation type
        if (obj.source) {
          obj.source = this.transformSourceFields(obj.source)
        }
        
        console.log(obj)
        await this.update({ id: this.currentRow.id, data: obj })
      } else {
        await this.create(JSON.stringify(this.currentRow))
      }
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
