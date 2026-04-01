<template lang="pug">
km-inner-loading(:showing='loading')
layouts-details-layout(v-if='!loading')
  template(#header)
    km-input-flat.km-heading-4.full-width.text-black(placeholder='Name', :modelValue='name', @change='name = $event')
    km-input-flat.km-description.full-width.text-black(placeholder='Description', :modelValue='description', @change='description = $event')
    .row.items-center.q-pl-6
      q-icon.col-auto(name='o_info', color='text-secondary')
        q-tooltip.bg-white.block-shadow.text-secondary-text.km-description(self='top middle', :offset='[-50, -50]') System name serves as unique record id
      km-input-flat.col.km-description.text-black.full-width(
        placeholder='Enter system name',
        :modelValue='system_name',
        @change='system_name = $event',
        @focus='showInfo = true',
        @blur='showInfo = false',
        :rules='[validSystemName()]'
      )
    .km-description.text-secondary.q-pl-6(v-if='showInfo') It is highly recommended to fill in system name only once and not change it later.
  template(#header-actions)
    km-btn(label='Record info', flat, icon='info', iconSize='16px')
      q-tooltip.bg-white.block-shadow
        .q-pa-sm
          .q-mb-sm
            .text-secondary-text.km-button-xs-text Created:
            .text-secondary-text.km-description {{ created_at }}
          .q-mb-sm
            .text-secondary-text.km-button-xs-text Last Synced:
            .text-secondary-text.km-description {{ modified_at }}
          .q-mb-sm
            .text-secondary-text.km-button-xs-text Created by:
            .text-secondary-text.km-description {{ created_by }}
          div
            .text-secondary-text.km-button-xs-text Modified by:
            .text-secondary-text.km-description {{ updated_by }}
    km-btn(label='Revert', icon='fas fa-undo', iconSize='16px', flat, @click='collectionStore.revert()', v-if='collectionStore.isChanged')
    km-btn(label='Save', flat, icon='far fa-save', iconSize='16px', @click='save', :loading='saving', :disable='saving || !collectionStore.isChanged')
    km-btn(label='Save & Sync', flat, @click='refreshCollection', iconSize='16px', icon='fa-solid fa-rotate')
    q-btn.q-px-xs(flat, :icon='"fas fa-ellipsis-v"', size='13px')
      q-menu(anchor='bottom right', self='top right')
        q-item(clickable, @click='showNewDialog = true', dense)
          q-item-section
            .km-heading-3 Clone
        q-item(clickable, @click='showDeleteDialog = true', dense)
          q-item-section
            .km-heading-3 Delete
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
  template(#content)
    km-tabs(v-model='tab')
      template(v-for='t in tabs')
        q-tab(:name='t.name', :label='t.label')
    .column.no-wrap.q-gap-16.full-height.full-width.overflow-auto.q-mb-md.q-mt-lg(style='min-height: 0')
      .row.q-gap-16.full-height.full-width
        .col.full-height.full-width
          .column.full-height.full-width.q-gap-16.overflow-auto.no-wrap
            collections-generalinfo(v-if='tab == "settings"')
            collections-metadata-page(v-if='tab == "metadata"')
            collections-chunks(v-if='tab == "chunks"', :selectedRow='selectedChunk', @selectRow='selectedChunk = $event')
            collections-scheduler(v-if='tab == "scheduler"')
  template(#drawer)
    collections-metadata-drawer(v-if='tab == "metadata" && activeMetadataConfig')
    collection-items-drawer(v-else-if='tab == "chunks" && selectedChunk', :selectedRow='selectedChunk', @close='selectedChunk = null')
    collections-drawer(v-else)
collections-create-new(v-if='showNewDialog', :showNewDialog='showNewDialog', @cancel='showNewDialog = false', copy)
</template>

<script>
import { ref, computed } from 'vue'
import { useRoute } from 'vue-router'
import { useEntityQueries } from '@/queries/entities'
import { validSystemName } from '@shared/utils/validationRules'
import { fetchData } from '@shared'
import { useCollectionDetailStore, useCollectionMetadataStore } from '@/stores/entityDetailStores'
import { useSearchStore } from '@/stores/searchStore'
import { useAppStore } from '@/stores/appStore'
import { storeToRefs } from 'pinia'

export default {
  emits: ['update:closeDrawer'],
  setup() {
    const route = useRoute()
    const queries = useEntityQueries()
    const collectionStore = useCollectionDetailStore()
    const collectionMetadataStore = useCollectionMetadataStore()
    const searchStore = useSearchStore()
    const appStore = useAppStore()
    const { semanticSearchAnswers } = storeToRefs(searchStore)
    const id = ref(route.params.id)
    const { data: selectedRow } = queries.collections.useDetail(id)
    const { data: listData } = queries.collections.useList()
    const { mutateAsync: updateCollection } = queries.collections.useUpdate()
    const { mutateAsync: createCollection } = queries.collections.useCreate()
    const { mutateAsync: removeCollection } = queries.collections.useRemove()

    function clearSemanticSearchAnswers() {
      semanticSearchAnswers.value = []
    }

    const tabs = ref([
      { name: 'chunks', label: 'Chunks' },
      { name: 'metadata', label: 'Metadata' },
      { name: 'settings', label: 'Settings' },
      { name: 'scheduler', label: 'Schedule & Runs' },
    ])
    const tab = ref('chunks')
    return {
      activeKnowledge: ref({}),
      prompt: ref(null),
      openTest: ref(true),
      showInfo: ref(false),
      showNewDialog: ref(false),
      showDeleteDialog: ref(false),
      showSyncConfirm: ref(false),
      saving: ref(false),
      job_id: ref(null),
      id,
      selectedRow,
      listData,
      updateCollection,
      createCollection,
      removeCollection,
      tabs,
      tab,
      selectedChunk: ref(null),
      validSystemName,
      collectionStore,
      collectionMetadataStore,
      appStore,
      clearSemanticSearchAnswers,
    }
  },
  computed: {
    items() {
      return this.listData?.items || []
    },
    name: {
      get() {
        return this.collectionStore.entity?.name || ''
      },
      set(value) {
        this.collectionStore.updateProperty({ key: 'name', value })
      },
    },
    description: {
      get() {
        return this.collectionStore.entity?.description || ''
      },
      set(value) {
        this.collectionStore.updateProperty({ key: 'description', value })
      },
    },
    system_name: {
      get() {
        return this.collectionStore.entity?.system_name || ''
      },
      set(value) {
        this.collectionStore.updateProperty({ key: 'system_name', value })
      },
    },
    currentRow() {
      return this.collectionStore.entity
    },
    activeKnowledgeId() {
      return this.$route.params?.id
    },
    activeRowId() {
      return this.$route.params.id
    },
    activeRowDB() {
      return this.items.find((item) => item.id == this.activeRowId)
    },
    activeKnowledgeName() {
      return this.listData?.items?.find((item) => item?.id == this.activeKnowledgeId)?.name
    },
    activeMetadataConfig() {
      return this.collectionMetadataStore.activeMetadataConfig
    },
    options() {
      return this.listData?.items?.map((item) => item?.name)
    },
    loading() {
      return !this.collectionStore.entity?.id
    },
    created_by() {
      if (!this.activeRowDB?.created_by) return 'Unknown'
      return `${this.activeRowDB?.created_by}`
    },
    updated_by() {
      if (!this.activeRowDB?.updated_by) return 'Unknown'
      return `${this.activeRowDB?.updated_by}`
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
  },

  watch: {
    selectedRow(newVal, oldVal) {
      if (newVal?.id !== oldVal?.id) {
        // Merge selectedRow with existing knowledge state to preserve job_id and other runtime data
        const existingKnowledge = this.collectionStore.entity
        if (existingKnowledge?.id === newVal?.id) {
          // Preserve existing state but update with fresh data from selectedRow
          this.collectionStore.setEntity({ ...newVal, job_id: existingKnowledge?.job_id || newVal?.job_id })
        } else {
          this.collectionStore.setEntity(newVal)
        }
        this.clearSemanticSearchAnswers()
      }
    },
  },
  mounted() {
    const existingKnowledge = this.collectionStore.entity
    // If the knowledge state already has the correct id (e.g., from CreateNew navigation), don't overwrite it
    if (existingKnowledge?.id === this.activeKnowledgeId) {
      // Knowledge is already set correctly, just clear semantic search answers
      this.clearSemanticSearchAnswers()
    } else if (this.activeKnowledgeId != existingKnowledge?.id) {
      this.collectionStore.setEntity(this.selectedRow)
      this.clearSemanticSearchAnswers()
    }
  },
  activated() {
    this.id = this.$route.params.id
    // Re-sync Pinia state when KeepAlive reactivates this component (multi-tab support)
    if (this.selectedRow && this.activeKnowledgeId !== this.collectionStore.entity?.id) {
      this.collectionStore.setEntity(this.selectedRow)
      this.clearSemanticSearchAnswers()
    }
  },
  methods: {
    navigate(path = '') {
      if (this.$route.path !== `/${path}`) {
        this.$router.push(`${path}`)
      }
    },
    openJobDetails() {
      this.showSyncConfirm = false
      window.open(this.$router.resolve({ path: `/jobs/?job_id=${this.job_id}` }).href, '_blank')
    },
    async deleteKnowledge() {
      this.saving = true
      try {
        await this.removeCollection(this.activeRowDB?.id)
        this.$emit('update:closeDrawer', null)
        this.$q.notify({
          color: 'green-9', textColor: 'white',
          icon: 'check_circle',
          group: 'success',
          message: 'Knowledge source has been deleted.',
          timeout: 1000,
        })
        this.navigate('/knowledge-sources')
      } catch (error) {
        const errorMessage = error?.message || 'Failed to delete Knowledge Source.'
        this.$q.notify({
          color: 'red-9', textColor: 'white',
          icon: 'error',
          group: 'error',
          message: errorMessage,
          timeout: 3000,
        })
      } finally {
        this.saving = false
      }
    },
    async refreshCollection() {
      await this.save()
      await this.createJob()
      this.showSyncConfirm = true
    },
    async createJob() {
      let jobData = {
        name: `Sync ${this.activeRowDB?.name}`,
        job_type: 'one_time_immediate',
        notification_email: '',
        run_configuration: {
          type: 'sync_collection',
          params: {
            system_name: this.activeRowDB?.system_name,
          },
        },
        timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
      }

      const endpoint = this.appStore.config?.scheduler?.endpoint
      const service = this.appStore.config?.scheduler?.service
      const credentials = this.appStore.config?.scheduler?.credentials
      const response = await fetchData({
        endpoint,
        service: `${service}/create-job`,
        method: 'POST',
        body: JSON.stringify(jobData),
        credentials,
        headers: { 'Content-Type': 'application/json' },
      })
      const job = await response.json()
      this.job_id = job.job_id

      this.$q.notify({
        color: 'green-9', textColor: 'white',
        icon: 'check_circle',
        group: 'success',
        message: 'Sync job has been created.',
        timeout: 1000,
      })
    },
    transformSourceFields(source) {
      // Transform Documentation source fields from comma-separated strings to arrays
      if (source?.source_type === 'Documentation') {
        const transformed = { ...source }

        // Convert languages from string to array
        if (transformed.languages && typeof transformed.languages === 'string') {
          transformed.languages = transformed.languages
            .split(',')
            .map((lang) => lang.trim())
            .filter((lang) => lang.length > 0)
        }

        // Convert sections from string to array
        if (transformed.sections && typeof transformed.sections === 'string') {
          transformed.sections = transformed.sections
            .split(',')
            .map((section) => section.trim())
            .filter((section) => section.length > 0)
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
      // Validate system_name before saving
      const systemNameValidation = validSystemName()(this.currentRow?.system_name)
      if (systemNameValidation !== true) {
        this.$q.notify({
          color: 'red-9', textColor: 'white',
          icon: 'error',
          group: 'error',
          message: systemNameValidation,
          timeout: 3000,
        })
        return
      }

      this.saving = true
      try {
        if (this.currentRow?.created_at) {
          const obj = this.collectionStore.buildPayload()

          // Ensure provider_system_name is preserved
          if (this.activeRowDB?.provider_system_name) {
            obj.provider_system_name = this.activeRowDB.provider_system_name
          }

          // Transform source fields for Documentation type
          if (obj.source) {
            obj.source = this.transformSourceFields(obj.source)
          }

          await this.updateCollection({ id: this.currentRow.id, data: obj })
        } else {
          await this.createCollection(this.currentRow)
        }
        this.$q.notify({
          color: 'green-9', textColor: 'white',
          icon: 'check_circle',
          group: 'success',
          message: 'Saved successfully',
          timeout: 2000,
        })
      } catch (error) {
        this.$q.notify({
          color: 'red-9', textColor: 'white',
          icon: 'error',
          group: 'error',
          message: error.message || 'Failed to save',
          timeout: 3000,
        })
      } finally {
        this.saving = false
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

<style lang="stylus">

@keyframes wobble {
    0% { transform: rotate(-5deg); }
    50% { transform: rotate(5deg); }
    100% { transform: rotate(-5deg); }
}

.wobble {
    animation: wobble 2s infinite;
}
</style>
